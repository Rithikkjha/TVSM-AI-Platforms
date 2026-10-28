"""Phase 6 verify (lightweight coverage gate) for the generated doc set of one repo.

Checks (any failure -> fail):
1. service.yaml present, parseable, schema_version 1, service_id matches.
2. All 6 template .md files present; front-matter has service_id (== repo's), doc_type (== the
   template's), last_reviewed (YYYY-MM-DD); every template ``##`` heading present in order
   (DATA_FLOWS: ``## Flow Index`` + one ``## Flow: <id>`` per front-matter flow id).
3. Every inventory endpoint / scheduled job / topic / outbound target / data store is mentioned.
4. No secret value anywhere in the output dir (token forms + secret shapes + secret-key values).
Writes runs/<org>/<repo>/coverage-report.md and coverage.json. Ledger/symmetry checks of the full
Phase 6 design are not part of this lightweight gate.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yaml

from . import paths
from .config import OrgConfig
from . import config_classify as cc
from .phase5_generate import MD_FILES, _entity
from .state import StateStore

log = logging.getLogger("repo_docs.verify")

PHASE_VERSION = "0.1.0"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HOLE = re.compile(r"\{[^}]*\}")
BENIGN_VAL = re.compile(r"^(?:true|false|null|none|yes|no|~|unknown|string)$", re.I)
# unquoted values only; quoted ones are handled by the _KV_QUOTED key check
CONN_VALUE = re.compile(r"(?i)\b(?:password|pwd|accountkey|sharedaccesskey)\s*=\s*"
                        r"(?![*$<{%;\s\"'`]|$)")
SHAPES = [cc._JWT, cc._PEM, cc._AKIA, cc._GHP, cc._USERINFO, CONN_VALUE,
          re.compile(r"(?i)[?&;]sig=(?![*$<{%])[^&\s;]+")]


def template_dir() -> Path:
    """smartbrain-v2/templates/service-docs (read-only spec), independent of the runs root."""
    return paths.DEFAULT_ROOT.parent / "templates" / "service-docs"


def split_front_matter(text: str) -> tuple[dict | None, str]:
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    try:
        fm = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return None, text
    return (fm if isinstance(fm, dict) else None), text[end + 4:]


def headings(body: str) -> list[str]:
    out, fence = [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
        elif not fence and line.startswith("## "):
            out.append(line[3:].strip())
    return out


def template_spec(tdir: Path | None = None) -> dict[str, dict]:
    """{file: {doc_type, headings}} from the read-only template (``Flow: x`` headings dropped)."""
    tdir = tdir or template_dir()
    spec = {}
    for name in MD_FILES:
        fm, body = split_front_matter((tdir / name).read_text(encoding="utf-8"))
        spec[name] = {"doc_type": (fm or {}).get("doc_type"),
                      "headings": [h for h in headings(body) if not h.startswith("Flow:")]}
    return spec


def _in_order(required: list[str], found: list[str]) -> list[str]:
    """Required headings missing or out of order (subsequence check)."""
    missing, pos = [], 0
    for h in required:
        try:
            pos = found.index(h, pos) + 1
        except ValueError:
            missing.append(h)
    return missing


def _norm(s: str) -> str:
    return HOLE.sub("{}", s or "").lower()


def required_mentions(inv: dict, sy: dict) -> list[tuple[str, str, list[str]]]:
    """(item label, scope, [alternative needles]) — scope ``api`` = API_SPEC.md, ``all`` = any doc."""
    out = []
    for it in inv.get("items") or []:
        a, k = it["attributes"], it["kind"]
        if k == "inbound_http":
            out.append((it["id"], "api", [a.get("path") or ""]))
        elif k == "scheduled_job":
            # unnamed jobs (e.g. node-cron callbacks): accept the cron expression or the handler file
            alts = [a.get("name") or "", a.get("expression") or "",
                    (a.get("handler") or "").rsplit(":", 1)[0]]
            out.append((it["id"], "all", [x for x in alts if x]))
        elif k == "messaging" and a.get("role") != "tests_target":
            needles = [_entity(a), a.get("name_key")]
            nf = a.get("name_from") or ""
            if ":" in nf:
                needles.append(nf.split(":", 1)[1])
            loc = a.get("published_by") or a.get("handler")
            # published_by/handler may be a single "file:line" or a list of them (merged items)
            for one in (loc if isinstance(loc, list) else [loc] if loc else []):
                if isinstance(one, str) and one:
                    needles.append(one.rsplit(":", 1)[0])
            out.append((it["id"], "all", [n for n in needles if n]))
    for o in sy.get("outbound") or []:
        if o.get("target"):
            out.append((f"outbound target {o['target']}", "all", [o["target"]]))
        elif o.get("path"):
            out.append((f"outbound {o.get('method')} {o['path']}", "api", [o["path"]]))
    for d in sy.get("data_stores") or []:
        out.append((f"data store {d.get('name')}", "all",
                    [n for n in [d.get("name")] + list(d.get("key_entities") or [])[:1] if n]))
    return out


def scan_secrets(files: list[Path], token_forms: list[str]) -> list[str]:
    hits = []
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if any(t and t in text for t in token_forms):
            hits.append(f"{p.name}: token")
        for n, line in enumerate(text.splitlines(), 1):
            if line_has_secret(line):
                hits.append(f"{p.name}:{n}")
    return hits


def line_has_secret(line: str) -> bool:
    """Secret *values* only. Config key names (e.g. ``AppSettings:AUTH_TOKEN``) and flags
    (``secret: true``) are expected in docs, so the entropy/key-name heuristics of
    ``redact_line`` are not used here: secret shapes + quoted/assigned values of secret keys."""
    if any(rx.search(line) for rx in SHAPES):
        return True
    pairs = [(m.group(1), m.group(2)) for m in cc._KV_JSON.finditer(line)]
    pairs += [(m.group(1), m.group(3)) for m in cc._KV_QUOTED.finditer(line)]
    for key, val in pairs:
        if cc.key_is_secret(key.rsplit(".", 1)[-1].rsplit(":", 1)[-1]) and val and not (
                BENIGN_VAL.match(val) or val.startswith(("***", "$", "{", "<", "%", "#{"))):
            return True
    return False


def verify_repo(org: str, repo: str, token_forms: list[str] | None = None,
                spec: dict | None = None) -> dict[str, Any]:
    rd = paths.runs_dir(org, repo)
    inv = paths.read_json(rd / "inventory.json") or {}
    sid = inv.get("service_id") or repo
    out = paths.output_dir(org, sid)
    spec = spec or template_spec()
    gaps: dict[str, list] = {"missing_files": [], "template_violations": [],
                             "items_missing_in_docs": [], "secret_hits": []}
    sy = {}
    syp = out / "service.yaml"
    if not syp.exists():
        gaps["missing_files"].append("service.yaml")
    else:
        try:
            sy = yaml.safe_load(syp.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            gaps["template_violations"].append(f"service.yaml: invalid yaml ({e.__class__.__name__})")
        if sy and (sy.get("schema_version") != 1 or sy.get("service_id") != sid):
            gaps["template_violations"].append("service.yaml: schema_version/service_id mismatch")
    texts: dict[str, str] = {}
    for name in MD_FILES:
        p = out / name
        if not p.exists():
            gaps["missing_files"].append(name)
            continue
        text = p.read_text(encoding="utf-8")
        texts[name] = text
        fm, body = split_front_matter(text)
        if fm is None:
            gaps["template_violations"].append(f"{name}: missing/invalid front-matter")
            continue
        if fm.get("service_id") != sid:
            gaps["template_violations"].append(f"{name}: front-matter service_id != {sid}")
        if fm.get("doc_type") != spec[name]["doc_type"]:
            gaps["template_violations"].append(f"{name}: doc_type != {spec[name]['doc_type']}")
        if not DATE.match(str(fm.get("last_reviewed") or "")):
            gaps["template_violations"].append(f"{name}: last_reviewed not YYYY-MM-DD")
        found = headings(body)
        for h in _in_order(spec[name]["headings"], found):
            gaps["template_violations"].append(f"{name}: heading '## {h}' missing or out of order")
        if name == "DATA_FLOWS.md":
            for fid in fm.get("flows") or []:
                if f"Flow: {fid}" not in found:
                    gaps["template_violations"].append(f"{name}: '## Flow: {fid}' missing")
    if texts:
        api = _norm(texts.get("API_SPEC.md", ""))
        alltxt = _norm("\n".join(texts.values()))
        for label, scope, needles in required_mentions(inv, sy):
            hay = api if scope == "api" else alltxt
            if not any(_norm(n) in hay for n in needles if n):
                gaps["items_missing_in_docs"].append(label)
    files = sorted(p for p in out.iterdir() if p.is_file()) if out.is_dir() else []
    gaps["secret_hits"] = scan_secrets(files, token_forms or [])
    result = "pass" if not any(gaps.values()) else "fail"
    cov = {"schema_version": 1, "repo": repo, "service_id": sid, "result": result,
           "checked_at": paths.utcnow(), "gaps": gaps}
    paths.atomic_write_json(rd / "coverage.json", cov)
    (rd / "coverage-report.md").write_text(render_report(cov), encoding="utf-8")
    return cov


def render_report(cov: dict) -> str:
    g = cov["gaps"]
    lines = [f"# Coverage report — {cov['repo']} ({cov['service_id']})", "",
             f"Result: **{cov['result'].upper()}** (checked {cov['checked_at']})", ""]
    for key, title in (("missing_files", "Missing files"),
                       ("template_violations", "Template violations"),
                       ("items_missing_in_docs", "Inventory items not mentioned in docs"),
                       ("secret_hits", "Secret hits (file:line, values never shown)")):
        lines.append(f"## {title} ({len(g[key])})")
        lines += [f"- {x}" for x in g[key]] or ["- none"]
        lines.append("")
    return "\n".join(lines)


def run(org: OrgConfig, store: StateStore, repos: list[str] | None = None,
        token_forms: list[str] | None = None) -> dict[str, Any]:
    spec = template_spec()
    res: dict[str, Any] = {"pass": [], "fail": {}}
    for repo in sorted(store.repos(org.name)):
        if repos and repo not in repos:
            continue
        if not (paths.runs_dir(org.name, repo) / "inventory.json").exists():
            continue
        cov = verify_repo(org.name, repo, token_forms, spec)
        n = sum(len(v) for v in cov["gaps"].values())
        store.set_phase(org.name, repo, "verify", status="done" if cov["result"] == "pass" else "failed",
                        version=PHASE_VERSION, finished_at=cov["checked_at"],
                        error=None if cov["result"] == "pass" else f"coverage fail: {n} gaps")
        if cov["result"] == "pass":
            res["pass"].append(repo)
        else:
            res["fail"][repo] = {k: len(v) for k, v in cov["gaps"].items() if v}
    return res
