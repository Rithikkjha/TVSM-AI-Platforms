"""Service aliases: deterministic nicknames per service_id -> ``registry/aliases.yaml``.

Sources (each alias keeps where it came from):
- ``name``      GitHub repo name / service_id and their spaced form            (high)
- ``readme``    README H1 title / first bold product name                        (high / medium)
- ``artifact``  package.json name, pom artifactId, csproj/nupkg name            (high)
- ``caller_config`` config key / env var holding the base URL in a CALLER repo  (medium)
- ``caller_client`` client class (``BookingServiceClient``) / Feign/Refit name  (medium; ``*Service`` low)
- ``host`` / ``base_path``  hostname label / dominant inbound path prefix       (medium)
- ``infra``     compose/k8s service names (medium), pipeline file names (low)
- ``derived``   suffix-stripped / singular variants of the above                (low)

``config/aliases.manual.yaml`` (user-owned) is merged with top priority: an alias listed there
maps ONLY to the services given there. Only key NAMES and hostnames are used, never values.
Output is deterministic (sorted, no timestamps).
"""
from __future__ import annotations

import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml

from . import paths
from .config import OrgConfig
from .state import StateStore

log = logging.getLogger("repo_docs.aliases")

SCHEMA_VERSION = 1
CONF_RANK = {"manual": 0, "high": 1, "medium": 2, "low": 3}
MAX_SOURCES = 8

GENERIC = {"service", "services", "api", "apis", "backend", "app", "apps", "application", "portal",
           "common", "core", "main", "server", "test", "tests", "frontend", "web", "ui", "admin",
           "bff", "microservice", "microservices", "micro", "layer", "client", "base", "instance",
           "readme", "development", "description", "svc", "fe", "be", "crud", "the", "for", "and",
           "of", "src", "lib", "library", "shared", "framework", "url", "host", "v1", "v2",
           "generate", "inbound", "outbound", "docker", "validation", "health", "parent"}
ORG_PREFIX = {"tvs", "tvsm", "tvsmbe", "tvsmotor"}
# trailing tokens stripped to build name variants (spec: -service(s) -svc -api -backend ... crud)
SUFFIX = {"service", "services", "svc", "api", "backend", "frontend", "fe", "be", "bff",
          "microservice", "microservices", "micro", "crud"}
URLISH = {"url", "uri", "urls", "host", "hostname", "endpoint", "endpoints", "baseurl", "address"}
KEY_TRAIL = URLISH | {"base", "client", "api", "path", "config"}
KEY_LEAD = {"react", "app", "next", "public", "vite", "vue", "nuxt", "ng", "bff", "env"}
CLIENT_TRAIL = {"client", "gateway", "service", "impl", "rest", "http", "feign", "proxy"}
GENERIC_CLASS = re.compile(r"(?i)(okhttp|httpservice|restcall|passthrough|util|helper|http$|"
                           r"^api|^rest|^web|^base)")
PIPE_NOISE = {"ast", "ci", "cd", "prod", "uat", "dev", "qa", "sit", "stage", "staging", "pipeline",
              "pipelines", "image", "scan", "sonar", "pr", "release", "azure", "yml", "yaml",
              "templates", "deploy", "build", "check", "scheduled", "nightly", "main", "master"}
INFRA_IMAGES = {"mongodb", "mongo", "redis", "postgres", "postgresql", "mysql", "mssql", "sqlserver",
                "rabbitmq", "kafka", "zookeeper", "nginx", "elasticsearch", "opensearch", "db",
                "database", "cache", "azurite", "localstack", "minio"}
README_JUNK = re.compile(r"(?i)^(readme|development|description|introduction|overview|"
                         r"getting started.*|react \+ .*|nodejs[- ]starter ?kit|project title|"
                         r"table of contents|installation)$")
JUNK_PHRASES = {"nodejs starterkit", "nodejs starter kit", "starterkit", "page type"}
PATH_SKIP = re.compile(r"(?i)^(api|apis|v\d+|system|rest|public|internal|\{.*\}|health)$")


# --------------------------------------------------------------------------- text helpers

def split_ident(s: str) -> list[str]:
    """Identifier -> lowercase words (camel/Pascal/snake/kebab/dotted; ``2.0`` stays one token)."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s or "")
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    toks = re.split(r"[^A-Za-z0-9.]+|(?<!\d)\.|\.(?!\d)", s)
    return [t.lower() for t in toks if t and t != "."]


def norm(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip().lower())
    return s.strip(" .,:;!?\"'`*#()[]")


def is_junk(alias: str) -> bool:
    a = norm(alias)
    if len(a) < 3 or "xxx" in a or "$" in a or "{" in a or "/" in a or a in JUNK_PHRASES:
        return True
    toks = split_ident(a) if " " not in a else a.split()
    if not toks:
        return True
    return all(t in GENERIC or t in ORG_PREFIX or t in PIPE_NOISE or t.isdigit() for t in toks)


def _singular(w: str) -> str:
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def name_variants(words: list[str]) -> list[str]:
    """Spaced / singular / suffix-stripped / org-prefix-stripped phrases for a word list
    (``booking crud services`` -> booking crud service, booking services, booking service, booking)."""
    words = [w for w in words if w]
    if not words:
        return []
    bases = [words]
    joined = " ".join(words)
    bff = re.sub(r"\bbackend for frontend( layer)?\b", "bff", joined)
    if bff != joined:
        bases.append(bff.split())
    for b in list(bases):
        if "crud" in b and len(b) > 1:
            bases.append([w for w in b if w != "crud"])
    for b in list(bases):
        if len(b) > 1 and b[0] in ORG_PREFIX:
            bases.append(b[1:])
            if len(b) > 2 and b[1] == "cps":  # tvs-cps-billing -> billing
                bases.append(b[2:])
    out: list[str] = []
    for b in bases:
        cur = list(b)
        while cur:
            if cur[-1] not in SUFFIX or cur[-1] in ("service", "services"):
                out.append(" ".join(cur))
                sing = cur[:-1] + [_singular(cur[-1])]
                out.append(" ".join(sing))
            if len(cur) > 1 and cur[-1] in SUFFIX:
                cur = cur[:-1]
            else:
                break
    seen, res = set(), []
    for p in out:
        p = norm(p)
        if p and p not in seen:
            seen.add(p)
            res.append(p)
    return res


def key_words(name: str) -> list[str]:
    """Config key / env var holding a base URL -> service words, or [] when the key is not
    URL-shaped (``BOOKING_SERVICE_URL`` -> booking service; ``bff.booking-service.base-url``
    -> booking service)."""
    toks = split_ident(name)
    if not toks or not any(t in URLISH or t == "base" for t in toks[-3:]):
        return []
    while toks and toks[-1] in KEY_TRAIL:
        toks = toks[:-1]
    while toks and toks[0] in KEY_LEAD:
        toks = toks[1:]
    return toks if len(toks) <= 4 else []


def class_words(stem: str) -> tuple[list[str], str] | None:
    """Client class/file stem -> (words, confidence) for ``*Client``/``*Gateway`` (medium) or
    PascalCase ``*Service`` (low); generic transport helpers are ignored."""
    if not re.match(r"^[A-Z][A-Za-z0-9]+$", stem or "") or GENERIC_CLASS.search(stem):
        return None
    if re.search(r"(Client|Gateway|Proxy)$", stem):
        conf = "medium"
    elif stem.endswith("Service"):
        conf = "low"
    else:
        return None
    toks = split_ident(stem)
    while toks and toks[-1] in CLIENT_TRAIL:
        toks = toks[:-1]
    return (toks, conf) if toks else None


def host_words(host: str) -> list[str]:
    h = (host or "").lower().split(":")[0]
    if not h or h in ("localhost",) or re.match(r"^[\d.]+$", h):
        return []
    label = h.split(".")[0]
    return [t for t in re.split(r"[-_]", label) if t and not re.search(r"\d", t)]


def pipeline_words(name: str) -> list[str]:
    stem = os.path.basename(name or "")
    stem = re.sub(r"\.(ya?ml)$", "", stem, flags=re.I)
    out = []
    for t in split_ident(stem):
        if t not in PIPE_NOISE and t not in out:
            out.append(t)
    return out if len(out) <= 4 else []


def readme_titles(path: Path) -> list[tuple[str, int, str]]:
    """[(title, line, kind)] from the README: first meaningful H1 (``kind=h1``, the part
    before `` — ``/`` - `` and any ``(parenthesised)`` alt name) + first bold name (``bold``)."""
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []
    out, start = [], 0
    if lines and lines[0].strip() == "---":  # skip YAML front-matter
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break
    h1_done = bold_done = False
    for i in range(start, min(len(lines), start + 60)):
        raw = lines[i].strip().strip('"').strip()
        if not h1_done and re.match(r"^#\s+\S", raw):
            title = re.sub(r"\s*#+\s*$", "", raw[1:]).strip()
            title = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", title)
            head = re.split(r"\s+[—–-]\s+", title)[0]
            alts = re.findall(r"\(([^)]+)\)", head)
            head = re.sub(r"\([^)]*\)", "", head).strip()
            for t in [head] + alts:
                if t and not README_JUNK.match(t.strip()):
                    out.append((t.strip(), i + 1, "h1"))
            h1_done = True
        if not bold_done and i < start + 40:
            m = re.search(r"\*\*([^*]{3,60})\*\*", raw)
            if m:
                b = m.group(1).strip()
                if (not b.endswith(":") and 1 <= len(b.split()) <= 5
                        and re.match(r"^[A-Za-z][A-Za-z0-9 .&+-]*$", b)
                        and not README_JUNK.match(b)):
                    out.append((b, i + 1, "bold"))
                bold_done = True
    return out


def find_readme(clone: Path) -> Path | None:
    try:
        for p in sorted(clone.iterdir()):
            if p.is_file() and p.name.lower() in ("readme.md", "readme.markdown", "readme"):
                return p
    except OSError:
        return None
    return None


# --------------------------------------------------------------------------- collection

class Collector:
    def __init__(self) -> None:
        self.data: dict[str, dict[str, dict]] = defaultdict(dict)

    def add(self, sid: str, alias: str, conf: str, src: dict) -> None:
        a = norm(alias)
        if not a or is_junk(a):
            return
        e = self.data[sid].setdefault(a, {"confidence": conf, "sources": []})
        if CONF_RANK[conf] < CONF_RANK[e["confidence"]]:
            e["confidence"] = conf
        s = {k: src.get(k) for k in ("type", "repo", "file", "line")}
        if src.get("from"):
            s["from"] = src["from"]
        if s not in e["sources"]:
            e["sources"].append(s)

    def add_words(self, sid: str, words: list[str], conf: str, src: dict) -> None:
        """Add the phrase itself at ``conf`` and its derived variants at ``low``."""
        if not words:
            return
        variants = name_variants(words)
        phrase = norm(" ".join(words))
        self.add(sid, phrase, conf, src)
        for v in variants:
            if v != phrase:
                self.add(sid, v, "low", {**src, "type": "derived", "from": phrase})


def _ev(it: dict) -> tuple[str | None, int | None]:
    ev = (it.get("evidence") or [{}])[0]
    return ev.get("file"), ev.get("line")


def _artifact_names(name: str) -> list[str]:
    if not name or "${" in name:
        return []
    n = name.split(":")[-1]          # maven group:artifact
    n = n.split("/")[-1]             # npm @scope/name
    return [n] if n else []


def collect(org: str, invs: dict[str, dict], edges: list[dict], services: dict[str, dict],
            clones: dict[str, Path | None]) -> Collector:
    """invs: {service_id: inventory}; clones: {service_id: clone dir or None}."""
    c = Collector()
    items_by_sid = {sid: {i["id"]: i for i in inv.get("items") or []} for sid, inv in invs.items()}
    for sid, inv in sorted(invs.items()):
        repo = inv.get("repo") or sid
        # name variants
        c.add(sid, sid, "high", {"type": "name", "repo": repo})
        c.add(sid, repo.lower(), "high", {"type": "name", "repo": repo})
        c.add_words(sid, split_ident(repo), "high", {"type": "name", "repo": repo})
        # README + artifacts first: their tokens are the anchors that README bold names and
        # pipeline file names must share (filters "First time setup", "uk-training-cd-pipeline")
        clone = clones.get(sid)
        rp = find_readme(clone) if clone else None
        titles = readme_titles(rp) if rp else []
        items = sorted(inv.get("items") or [], key=lambda i: i["id"])
        anchors = set(split_ident(repo))
        for title, line, kind in titles:
            if kind == "h1":
                anchors.update(split_ident(title))
                c.add_words(sid, split_ident(title), "high",
                            {"type": "readme_h1", "repo": repo, "file": rp.name, "line": line})
        for it in items:
            a = it.get("attributes") or {}
            if it["kind"] != "artifact":
                continue
            f, ln = _ev(it)
            root = bool(f) and "/" not in f  # root manifest = the service; sub-module = medium
            for n in _artifact_names(a.get("name") or ""):
                if root:
                    anchors.update(split_ident(n))
                c.add_words(sid, split_ident(n), "high" if root else "medium",
                            {"type": "artifact", "repo": repo, "file": f, "line": ln})
        anchors -= GENERIC | ORG_PREFIX | PIPE_NOISE
        for title, line, kind in titles:
            bw = split_ident(title)
            if "-".join(bw) in invs and "-".join(bw) != sid:
                continue  # bold text naming ANOTHER repo (e.g. a sibling in a README table)
            if kind == "bold" and anchors & set(bw):
                c.add_words(sid, split_ident(title), "medium",
                            {"type": "readme_bold", "repo": repo, "file": rp.name, "line": line})
        for it in items:
            a, k = it.get("attributes") or {}, it["kind"]
            f, ln = _ev(it)
            if k == "infra":
                ik = a.get("infra_kind")
                if ik in ("compose-service", "k8s-service", "k8s-deployment", "kubernetes",
                          "helm", "app-service"):
                    n = a.get("name") or ""
                    if n.lower() not in INFRA_IMAGES:
                        c.add_words(sid, split_ident(n), "medium",
                                    {"type": "infra", "repo": repo, "file": f, "line": ln})
                elif ik == "azure-pipeline":
                    pw = pipeline_words(a.get("name") or "")
                    if pw and anchors & set(pw):
                        c.add_words(sid, pw, "low",
                                    {"type": "pipeline", "repo": repo, "file": f, "line": ln})
        # dominant inbound base path (e.g. /location-master/..., /mdp/v1/...)
        firsts = []
        for it in items:
            if it["kind"] != "inbound_http":
                continue
            segs = [s for s in (it["attributes"].get("path") or "").split("/") if s]
            seg = next((s for s in segs if not PATH_SKIP.match(s)), None)
            if seg:
                firsts.append((seg, it))
        if len(firsts) >= 2:
            cnt: dict[str, list] = defaultdict(list)
            for seg, it in firsts:
                cnt[seg].append(it)
            seg, its = sorted(cnt.items(), key=lambda kv: (-len(kv[1]), kv[0]))[0]
            if len(its) >= 2 and len(its) * 2 >= len(firsts):
                f, ln = _ev(sorted(its, key=lambda i: i["id"])[0])
                c.add_words(sid, split_ident(seg), "medium",
                            {"type": "base_path", "repo": repo, "file": f, "line": ln})
        for h in (services.get(sid) or {}).get("hosts") or []:
            if h.get("from") == "compose-service":
                continue  # compose names handled as infra above
            c.add_words(sid, host_words(h.get("host") or ""), "medium",
                        {"type": "host", "repo": repo, "file": None, "line": None})

    # caller-side names from OTHER repos, via resolved http edges
    class_targets: dict[tuple, set] = defaultdict(set)
    calls = []
    for e in sorted(edges, key=lambda e: e.get("id") or ""):
        if e.get("kind") not in ("http", "grpc", "soap"):
            continue
        to, frm = e.get("to"), e.get("from")
        if not to or to.startswith("external:") or to == frm or to not in invs or frm not in invs:
            continue
        if e.get("caller_type") not in (None, "service", "frontend"):
            continue
        for fi in e.get("from_items") or [e.get("from_item")]:
            it = items_by_sid.get(frm, {}).get(fi)
            if it:
                calls.append((frm, to, it))
                f, _ = _ev(it)
                if f:
                    class_targets[(frm, f)].add(to)
    for frm, to, it in calls:
        a = it.get("attributes") or {}
        crepo = invs[frm].get("repo") or frm
        f, ln = _ev(it)
        bus = a.get("base_url_source") or ""
        if ":" in bus and bus.split(":", 1)[0] in ("config", "env"):
            key = bus.split(":", 1)[1]
            c.add_words(to, key_words(key), "medium",
                        {"type": "caller_config", "repo": crepo, "file": f, "line": ln,
                         "from": key})
        if a.get("client") in ("feign", "refit", "openfeign") and a.get("client_name"):
            c.add_words(to, split_ident(a["client_name"]), "medium",
                        {"type": "caller_client", "repo": crepo, "file": f, "line": ln})
        if f and len(class_targets[(frm, f)]) == 1:
            stem = os.path.splitext(os.path.basename(f))[0]
            cw = class_words(stem)
            if cw:
                c.add_words(to, cw[0], cw[1], {"type": "caller_client", "repo": crepo,
                                               "file": f, "line": ln, "from": stem})
        hint = a.get("target_hint")
        if hint:
            c.add_words(to, host_words(hint), "medium",
                        {"type": "host", "repo": crepo, "file": f, "line": ln})
    return c


# --------------------------------------------------------------------------- merge + output

def manual_path() -> Path:
    return paths.root() / "config" / "aliases.manual.yaml"


def aliases_path() -> Path:
    return paths.registry_dir() / "aliases.yaml"


def load_manual(path: Path | None = None) -> dict[str, list[str]]:
    path = path or manual_path()
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    if isinstance(doc.get("aliases"), dict):
        doc = doc["aliases"]
    out = {}
    for k, v in (doc or {}).items():
        if k is None:
            continue
        vals = [v] if isinstance(v, str) else list(v or [])
        out[norm(str(k))] = [str(x) for x in vals if x]
    return out


def merge(derived: dict[str, dict[str, dict]], manual: dict[str, list[str]],
          known: Iterable[str]) -> dict[str, dict[str, dict]]:
    """manual + derived. A manual alias maps ONLY to its listed services (derived hits of the
    same alias on other services are dropped); unknown service ids are ignored with a warning."""
    known = set(known)
    out = {sid: {a: {"confidence": e["confidence"], "sources": list(e["sources"])}
                 for a, e in m.items()} for sid, m in derived.items()}
    for alias, sids in sorted(manual.items()):
        if not alias:
            continue
        good = [s for s in sids if s in known]
        for s in sorted(set(sids) - known):
            log.warning("aliases.manual: %r -> unknown service_id %r ignored", alias, s)
        if not good:
            continue
        for sid, m in out.items():
            if sid not in good:
                m.pop(alias, None)
        for sid in good:
            e = out.setdefault(sid, {}).setdefault(alias, {"confidence": "manual", "sources": []})
            e["confidence"] = "manual"
            src = {"type": "manual", "repo": None, "file": "config/aliases.manual.yaml",
                   "line": None}
            if src not in e["sources"]:
                e["sources"].insert(0, src)
    return out


def ambiguous_map(merged: dict[str, dict[str, dict]]) -> dict[str, list[str]]:
    idx: dict[str, set] = defaultdict(set)
    for sid, m in merged.items():
        for a in m:
            idx[a].add(sid)
    return {a: sorted(s) for a, s in sorted(idx.items()) if len(s) > 1}


def _src_key(s: dict):
    return (s.get("type") or "", s.get("repo") or "", s.get("file") or "", s.get("line") or 0,
            s.get("from") or "")


def build_doc(org: str, merged: dict[str, dict[str, dict]], repos: dict[str, str]) -> dict:
    amb = ambiguous_map(merged)
    services = {}
    for sid in sorted(merged):
        rows = []
        for a, e in merged[sid].items():
            srcs = sorted(e["sources"], key=lambda s: (s.get("type") != "manual", _src_key(s)))
            rows.append({"alias": a, "confidence": e["confidence"],
                         "sources": srcs[:MAX_SOURCES], "source_count": len(srcs)})
        rows.sort(key=lambda r: (CONF_RANK[r["confidence"]], r["alias"] in amb,
                                 -r["source_count"], r["alias"]))
        services[sid] = {"canonical": sid, "repo": repos.get(sid), "aliases": rows}
    return {"schema_version": SCHEMA_VERSION, "org": org,
            "generated_by": "repo_docs aliases (deterministic; manual overrides: "
                            "config/aliases.manual.yaml)",
            "services": services, "ambiguous": amb}


def ranked(entry: dict | None, cap: int = 15, exclude: Iterable[str] = ()) -> list[str]:
    """Alias strings for service.yaml/OVERVIEW: manual, high, medium first (rows are already
    ranked in aliases.yaml), the canonical id itself excluded."""
    ex = {norm(x) for x in exclude}
    out = []
    for r in (entry or {}).get("aliases") or []:
        if r["alias"] not in ex and r["alias"] not in out:
            out.append(r["alias"])
        if len(out) >= cap:
            break
    return out


def load_registry() -> dict[str, dict]:
    try:
        doc = yaml.safe_load(aliases_path().read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return doc.get("services") or {}


MANUAL_TEMPLATE = """\
# User-owned service nicknames. Merged into registry/aliases.yaml at the HIGHEST priority by
# `python -m repo_docs aliases --org <ORG>`; this file is never overwritten by the pipeline.
#
# Format: <alias>: [<service_id>, ...]   (alias is matched case-insensitively)
# An alias listed here maps ONLY to the services you list (derived hits on other services are
# dropped), so use it to settle ambiguous names too. Unknown service_ids are ignored (warning).
#
# Examples:
#   bs: [booking-crud-services]
#   booking service: [booking-crud-services]
#   mdp: [master-data-platform]
#   auth ninja: [tvsm-auth]
"""


def ensure_manual_template() -> Path:
    p = manual_path()
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(MANUAL_TEMPLATE, encoding="utf-8")
    return p


def dump(doc: dict) -> str:
    head = ("# Service aliases — generated by `repo_docs aliases` (deterministic; manual entries "
            "from config/aliases.manual.yaml win).\n# Do not edit; add nicknames to "
            "config/aliases.manual.yaml instead.\n")
    return head + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)


def run(org: OrgConfig | str, store: StateStore | None = None) -> dict[str, Any]:
    name = org if isinstance(org, str) else org.name
    store = store or StateStore()
    invs, clones, repos = {}, {}, {}
    for repo in sorted(store.repos(name)):
        inv = paths.read_json(paths.runs_dir(name, repo) / "inventory.json")
        if not inv:
            continue
        sid = inv["service_id"]
        invs[sid] = inv
        repos[sid] = inv.get("repo") or repo
        cd = paths.clone_dir(name, repo)
        clones[sid] = cd if cd.is_dir() else None
    reg = paths.registry_dir()
    edges = (paths.read_json(reg / "edges.json", {}) or {}).get("edges", [])
    services = (paths.read_json(reg / name / "services.json", {}) or {}).get("services", {})
    col = collect(name, invs, edges, services, clones)
    ensure_manual_template()
    merged = merge(col.data, load_manual(), invs.keys())
    for sid in invs:
        merged.setdefault(sid, {})
    doc = build_doc(name, merged, repos)
    out = aliases_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(dump(doc), encoding="utf-8")
    os.replace(tmp, out)
    return {"services": len(doc["services"]),
            "aliases": sum(len(s["aliases"]) for s in doc["services"].values()),
            "ambiguous": len(doc["ambiguous"]), "output": str(out.relative_to(paths.root()))}
