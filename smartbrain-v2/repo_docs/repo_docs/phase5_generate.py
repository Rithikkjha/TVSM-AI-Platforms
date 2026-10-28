"""Phase 5 generate: deterministic service.yaml per repo from inventory.json + phase-4 registry.

Maps 1:1 onto ``templates/service-docs/service.yaml`` (schema v1, read-only). Anything not
determinable from inventory/registry stays ``null`` (never invented). Config is names only.
Output: ``output/<org>/<service_id>/service.yaml`` via ``<service_id>.partial/`` + atomic rename;
existing narrative ``*.md`` files in the output dir are carried over untouched.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from . import aliases as aliasmod, flows as flowmod, paths
from .config import OrgConfig
from .config_classify import canonical_key
from .state import StateStore

log = logging.getLogger("repo_docs.generate")

PHASE_VERSION = "0.1.0"
ALIAS_CAP = 15
MD_FILES = ("OVERVIEW.md", "API_SPEC.md", "DATA_FLOWS.md", "HLD.md", "HLC.md", "LLD.md")
CALLER_KINDS = {"http", "grpc", "soap"}
ACCESS = {"read": "read", "write": "write", "both": "read-write"}


def _src(s: str | None) -> str:
    """Template enum is code|manual|inferred; phase-2 ``contract`` is written as ``code``."""
    return s if s in ("manual", "inferred") else "code"


def slug(s: str) -> str:
    s = re.sub(r"\{[^}]*\}", "", s or "")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "root"


def _uniq(seq) -> list:
    return sorted({x for x in seq if x})


class Registry:
    """Phase-4 registry indexes used by the mapping."""

    def __init__(self, edges: list[dict], services: dict[str, dict],
                 flows: list[dict] | None = None, aliases: dict[str, dict] | None = None,
                 summaries: dict[str, dict] | None = None):
        self.edges = edges
        self.services = services
        self.aliases = aliases or {}      # registry/aliases.yaml services
        self.summaries = summaries or {}  # config/service_summaries.yaml
        self.flows = flows  # registry/flows.json; None -> legacy per-topic event flows
        self.by_to_item: dict[tuple, list[dict]] = defaultdict(list)
        self.by_from_item: dict[tuple, list[dict]] = defaultdict(list)
        for e in edges:
            if e.get("to_item"):
                self.by_to_item[(e["to"], e["to_item"])].append(e)
            for fi in e.get("from_items") or [e.get("from_item")]:
                if fi:
                    self.by_from_item[(e["from"], fi)].append(e)

    @classmethod
    def load(cls, org: str) -> "Registry":
        reg = paths.registry_dir()
        edges = (paths.read_json(reg / "edges.json", {}) or {}).get("edges", [])
        services = (paths.read_json(reg / org / "services.json", {}) or {}).get("services", {})
        return cls(edges, services, flowmod.load_flows(org), aliasmod.load_registry(),
                   load_summaries())

    def inbound_edges(self, sid, item_id):
        return [e for e in self.by_to_item.get((sid, item_id), []) if e["kind"] in CALLER_KINDS]

    def outbound_edges(self, sid, item_id, kinds):
        return [e for e in self.by_from_item.get((sid, item_id), []) if e["kind"] in kinds]

    def event_edges(self, via: str) -> list[dict]:
        return sorted((e for e in self.edges if e["kind"] == "event" and e.get("via") == via),
                      key=lambda e: (e["from"], e["to"]))


def summaries_path() -> Path:
    return paths.root() / "config" / "service_summaries.yaml"


def load_summaries() -> dict[str, dict]:
    """config/service_summaries.yaml {service_id: {summary, domain, source, based_on}}."""
    try:
        doc = yaml.safe_load(summaries_path().read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return {k: v for k, v in doc.items() if isinstance(v, dict)}


def refresh_overview(text: str, aliases: list[str], summary: str | None) -> str:
    """Idempotently set front-matter ``aliases:`` and the ``Summary:`` / ``Also known as:``
    lines right under ``## Purpose``; everything else (headings, other keys) is untouched."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is not None:
            fm, i = [], 1
            while i < end:
                if lines[i].startswith("aliases:"):
                    i += 1
                    while i < end and re.match(r"^\s+-\s", lines[i]):
                        i += 1
                    continue
                fm.append(lines[i])
                i += 1
            fm.append("aliases: " + json.dumps(aliases, ensure_ascii=False))
            lines = [lines[0]] + fm + lines[end:]
    try:
        h = next(i for i, ln in enumerate(lines) if ln.strip() == "## Purpose")
    except StopIteration:
        return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    j = h + 1
    while j < len(lines) and (lines[j].startswith("Summary:") or
                              lines[j].startswith("Also known as:")):
        j += 1
    ins = []
    if summary:
        ins.append(f"Summary: {summary}")
    ins.append("Also known as: " + (", ".join(aliases) if aliases else "none recorded"))
    lines = lines[:h + 1] + ins + lines[j:]
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _entity(a: dict) -> str | None:
    if a.get("entity"):
        return a["entity"]
    vals = sorted(set((a.get("resolved_values") or {}).values()))
    return vals[0] if len(vals) == 1 else None


def _inbound(items, sid, reg) -> list[dict]:
    out, seen = [], set()
    for it in items:
        a = it["attributes"]
        if it["kind"] == "inbound_http":
            base = slug(f"{a.get('method')}-{a.get('path')}")
            entry = {"id": None, "kind": "http", "method": a.get("method"), "path": a.get("path"),
                     "auth": a.get("auth"),
                     "callers": _uniq(e["from"] for e in reg.inbound_edges(sid, it["id"])),
                     "params": [{"name": p.get("name"), "in": p.get("in"), "type": p.get("type"),
                                 "required": p.get("required")} for p in a.get("params") or []],
                     "request": a.get("request"),
                     "responses": [{"status": r.get("status"), "schema": r.get("schema"),
                                    "when": r.get("when")} for r in a.get("responses") or []],
                     "handler": a.get("handler"), "source": _src(it.get("source"))}
        elif it["kind"] == "scheduled_job":
            base = slug(f"scheduled-{a.get('name')}")
            entry = {"id": None, "kind": "scheduled", "name": a.get("name"),
                     "schedule": a.get("expression"), "trigger": a.get("trigger_type"),
                     "handler": a.get("handler"), "callers": [], "source": _src(it.get("source"))}
        else:
            continue
        iid, n = base, 2
        while iid in seen:
            iid, n = f"{base}-{n}", n + 1
        seen.add(iid)
        entry["id"] = iid
        out.append(entry)
    return out


def _outbound(items, sid, reg) -> tuple[list[dict], dict[str, str]]:
    """Outbound entries + {canonical config key: target} for config.points_to."""
    out, points = [], {}
    ext_done = set()
    for it in items:
        a = it["attributes"]
        if it["kind"] in ("outbound_http", "frontend_api_call"):
            if a.get("role") == "tests_target":
                continue
            edges = reg.outbound_edges(sid, it["id"], CALLER_KINDS)
            base = {"target": None, "kind": "http", "method": a.get("method"),
                    "path": a.get("path_template"), "purpose": None,
                    "request": a.get("request"), "response": a.get("response"),
                    "criticality": None, "on_failure": None,
                    "base_url_source": a.get("base_url_source"), "source": _src(it.get("source"))}
            if not edges:
                out.append(base)
            for e in sorted(edges, key=lambda e: e["to"]):
                out.append({**base, "target": e["to"], "criticality": e.get("criticality"),
                            "source": _src(e.get("source"))})
                bus = a.get("base_url_source") or ""
                if ":" in bus and bus.split(":", 1)[0] in ("config", "env"):
                    points.setdefault(canonical_key(bus.split(":", 1)[1])[0], e["to"])
        elif it["kind"] == "external_system":
            tgt = f"external:{a.get('name')}"
            edges = reg.outbound_edges(sid, it["id"], CALLER_KINDS)
            if tgt in ext_done:
                continue
            ext_done.add(tgt)
            crit = edges[0].get("criticality") if edges else None
            out.append({"target": tgt, "kind": "http", "purpose": None, "criticality": crit,
                        "category": a.get("category"),
                        "source": _src(edges[0].get("source") if edges else it.get("source"))})
    # external targets reached through literal hosts already appear via outbound_http edges
    return out, points


def _events(items, sid, reg):
    pubs, subs, vias = [], [], set()
    for it in items:
        if it["kind"] != "messaging":
            continue
        a = it["attributes"]
        if a.get("role") == "tests_target":
            continue
        out_e = [e for e in reg.by_from_item.get((sid, it["id"]), []) if e["kind"] == "event"]
        in_e = [e for e in reg.by_to_item.get((sid, it["id"]), []) if e["kind"] == "event"]
        ev_edges = out_e + in_e
        common = {"entity": _entity(a), "entity_type": a.get("entity_type"),
                  "broker": a.get("broker"), "namespace": a.get("namespace"),
                  "name_from": a.get("name_from"), "message_types": a.get("message_types") or [],
                  "payload": a.get("payload"), "properties": a.get("properties") or {}}
        for e in ev_edges:
            vias.add(e["via"])
        if a.get("direction") == "publish":
            pubs.append({**common, "published_by": a.get("published_by"),
                         "consumers": _uniq(e["to"] for e in out_e),
                         "source": _src(it.get("source"))})
        else:
            subs.append({**common, "subscription": a.get("subscription"),
                         "filter": a.get("filter"), "handler": a.get("handler"),
                         "trigger": a.get("trigger"), "action": None,
                         "error_handling": a.get("error_handling") or {},
                         "producers": _uniq(e["from"] for e in in_e),
                         "source": _src(it.get("source"))})
    return {"publishes": pubs, "subscribes": subs}, vias


def _flows(sid, vias: set, reg) -> list[dict]:
    """One flow per broker entity this service takes part in; flow_id is derived from the
    registry ``via`` only, so every participant emits the same flow_id and steps."""
    flows = []
    for via in sorted(vias):
        edges = reg.event_edges(via)
        if not edges:
            continue
        parts = via.split(":", 2)  # <broker>:<entity_type>:<name>
        etype, name = (parts[1], parts[2]) if len(parts) == 3 else ("topic", via)
        producers = {e["from"] for e in edges}
        role = "participant" if sid in producers else "consumer"
        flows.append({"flow_id": f"event-{slug(name)}",
                      "name": f"{name} event propagation", "role": role,
                      "steps": [{"from": e["from"], "to": e["to"], "via": f"{etype}:{name}",
                                 "data": None, "source": _src(e.get("source"))}
                                for e in edges]})
    return flows


def _schemas(items) -> dict:
    out = {}
    for it in sorted((i for i in items if i["kind"] == "schema"), key=lambda i: i["id"]):
        a = it["attributes"]
        name = a.get("name") or it["id"].rsplit(":", 1)[-1]
        if name in out:
            continue
        entry = {"defined_in": a.get("defined_in"),
                 "fields": [{"name": f.get("json_name") or f.get("name"), "type": f.get("type"),
                             "required": f.get("required"), "validation": f.get("validation")}
                            for f in a.get("fields") or []]}
        if a.get("enum_values"):
            entry["type"] = f"enum[{','.join(str(v) for v in a['enum_values'])}]"
        entry["source"] = _src(it.get("source"))
        out[name] = entry
    return out


def _data_stores(items, sid, reg) -> list[dict]:
    out = []
    for it in items:
        if it["kind"] != "data_access":
            continue
        a = it["attributes"]
        shared = [e for e in reg.by_from_item.get((sid, it["id"]), []) if e["kind"] == "shared_db"]
        owned = True if a.get("owns_schema") else (False if shared else None)
        out.append({"name": (a.get("database") if a.get("database") not in (None, "_") else None)
                    or a.get("name_from") or it["id"].split(":", 3)[-1],
                    "type": a.get("store_type"), "access": ACCESS.get(a.get("operation")),
                    "owned": owned, "owner_service": shared[0]["to"] if shared else None,
                    "key_entities": _uniq(e.get("name") for e in a.get("entities") or []),
                    "source": _src(it.get("source"))})
    return out


def _config(items, points) -> list[dict]:
    out = []
    for it in sorted((i for i in items if i["kind"] == "config_key"),
                     key=lambda i: (str(i["attributes"].get("name") or ""), i["id"])):
        a = it["attributes"]
        canon = a.get("canonical") or canonical_key(a.get("name") or "")[0]
        names = a.get("name") if isinstance(a.get("name"), list) else [a.get("name")]
        entry = {"name": names[0]}
        if len(names) > 1:  # same key read under several spellings (e.g. ENV_STYLE + dotted)
            entry["aliases"] = names[1:]
        out.append({**entry, "purpose": None, "required": a.get("required"),
                    "secret": bool(a.get("secret")),
                    "provided_by": None if a.get("provided_by") in (None, "unknown") else a["provided_by"],
                    "points_to": points.get(canon)})
    return out


def build_service_yaml(inv: dict, meta: dict, reg: Registry) -> dict:
    sid = inv["service_id"]
    items = sorted(inv.get("items") or [], key=lambda i: i["id"])
    svc = reg.services.get(sid, {})
    by_kind = defaultdict(list)
    for it in items:
        by_kind[it["kind"]].append(it)
    rt = meta.get("repo_type") or {}
    inbound = _inbound(items, sid, reg)
    outbound, points = _outbound(items, sid, reg)
    events, vias = _events(items, sid, reg)
    frameworks = _uniq([i["attributes"].get("framework") for i in by_kind["inbound_http"]]
                       + [i["attributes"].get("ui_framework") for i in by_kind["frontend_api_call"]])
    infra_kinds = {i["attributes"].get("infra_kind") for i in by_kind["infra"]}
    libs = _uniq(i["attributes"].get("name") for i in by_kind["dependency"]
                 if not i["attributes"].get("internal") and i["attributes"].get("scope") != "test")
    ent = reg.aliases.get(sid)
    aliases = (aliasmod.ranked(ent, ALIAS_CAP, exclude=[sid]) if ent
               else svc.get("aliases") or [])
    summ = reg.summaries.get(sid) or {}
    envs = [{"name": h.get("env"), "base_url": h.get("host") + (h.get("path_prefix") or "")}
            for h in svc.get("hosts") or [] if h.get("host")]
    return {
        "schema_version": 1, "service_id": sid, "name": inv.get("repo"),
        "aliases": aliases, "type": rt.get("template_type"), "domain": summ.get("domain"),
        "status": "deprecated" if meta.get("archived") else None, "summary": summ.get("summary"),
        "repo": {"url": meta.get("html_url"), "default_branch": meta.get("default_branch")},
        "ownership": {"team": None, "tech_lead": None, "product_owner": None, "vendor": None,
                      "oncall": None},
        "tech_stack": {"languages": _uniq([meta.get("language")]), "frameworks": frameworks,
                       "runtime": None, "key_libraries": libs,
                       "build": ",".join(meta.get("stack_ids") or []) or None,
                       "container": "docker" if "dockerfile" in infra_kinds else None},
        "deployment": {"platform": None, "regions": None,
                       "environments": sorted(envs, key=lambda e: (e["name"] or "", e["base_url"]))},
        "inbound": inbound, "outbound": outbound, "events": events,
        "schemas": _schemas(items), "data_stores": _data_stores(items, sid, reg),
        "config": _config(items, points),
        "flows": (flowmod.service_yaml_flows(reg.flows, sid) if reg.flows is not None
                  else _flows(sid, vias, reg)),
        "links": {"jira_projects": None, "confluence_pages": None, "dashboards": None},
    }


def dump_yaml(doc: dict) -> str:
    head = ("# SmartBrain service manifest — schema v1 (generated by repo_docs generate; "
            "deterministic from inventory + registry. null = not determinable from code)\n")
    return head + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)


def write_output(org: str, sid: str, text: str,
                 overview: tuple[list[str], str | None] | None = None) -> Path:
    """``overview=(aliases, summary)`` refreshes OVERVIEW.md (front-matter + Purpose lines)."""
    final = paths.output_dir(org, sid)
    partial = final.with_name(f"{sid}.partial")
    old = final.with_name(f"{sid}.old")
    for d in (partial, old):
        if d.exists():
            shutil.rmtree(d)
    partial.mkdir(parents=True)
    if final.is_dir():  # keep narrative docs written by the per-repo agent
        for p in final.iterdir():
            if p.is_file() and p.name != "service.yaml":
                shutil.copy2(p, partial / p.name)
    ov = partial / "OVERVIEW.md"
    if overview is not None and ov.is_file():
        old_text = ov.read_text(encoding="utf-8")
        new_text = refresh_overview(old_text, *overview)
        if new_text != old_text:
            ov.write_text(new_text, encoding="utf-8")
    with open(partial / "service.yaml", "w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    if final.exists():
        os.replace(final, old)
    os.replace(partial, final)
    if old.exists():
        shutil.rmtree(old)
    return final


def run(org: OrgConfig, store: StateStore, repos: list[str] | None = None) -> dict[str, Any]:
    reg = Registry.load(org.name)
    done, failed = [], {}
    for repo in sorted(store.repos(org.name)):
        if repos and repo not in repos:
            continue
        rd = paths.runs_dir(org.name, repo)
        inv = paths.read_json(rd / "inventory.json")
        if not inv:
            continue
        try:
            meta = paths.read_json(rd / "meta.json", {}) or {}
            notes = paths.read_json(rd / "llm_notes.json")
            if notes:  # same merge as phase 4, so service.yaml events match the registry
                from .phase4_resolve import merge_llm_items
                inv = {**inv, "items": merge_llm_items(list(inv.get("items") or []), notes)}
            doc = build_service_yaml(inv, meta, reg)
            write_output(org.name, inv["service_id"], dump_yaml(doc),
                         overview=(doc["aliases"], doc["summary"]))
            store.set_phase(org.name, repo, "generate", status="done", version=PHASE_VERSION,
                            input_sha=inv.get("head_sha"), finished_at=paths.utcnow(), error=None)
            done.append(repo)
        except Exception as e:  # per-repo failure, previous output kept
            log.exception("generate %s failed", repo)
            failed[repo] = f"{type(e).__name__}: {e}"
            store.set_phase(org.name, repo, "generate", status="failed", version=PHASE_VERSION,
                            error=failed[repo], finished_at=paths.utcnow())
    return {"generated": len(done), "failed": failed}
