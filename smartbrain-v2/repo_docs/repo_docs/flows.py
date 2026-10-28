"""End-to-end data flows: deterministic simple paths over the phase-4 HTTP/event edges.

Inputs: ``registry/edges.json``, ``registry/<org>/services.json``, ``runs/<org>/*/inventory.json``.
Outputs: ``registry/flows.json`` (sorted, no timestamps -> byte-identical re-runs) and
``output/<org>/<service_id>/DATA_FLOWS.md`` for every generated service. No LLM content.

Graph: one hop per ``(from, to, kind)`` aggregating every edge between that pair (all vias, schema
names, evidence). Excluded: self-loops, test edges (``caller_type`` test-suite, ``kind`` tests),
``library_dependency``/``owns_schema``/``shared_db``, edges whose caller items are all ``script`` /
``tests_target``, and test-suite/library services. ``external:<name>`` targets are terminal nodes.
Entries: frontends, services with scheduled jobs, services without an inbound edge from another
service, every event publisher (flows starting with its event hop) and, last, any node still not
covered (cycle-only components). From each entry: all maximal simple paths, at most MAX_DEPTH hops.
Only maximal paths are kept, so strict prefixes (which add no hop) never appear; identical step
sequences from several entry reasons are merged (triggers unioned).
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from . import paths
from .config import OrgConfig

log = logging.getLogger("repo_docs.flows")

FLOWS_VERSION = "0.1.0"
MAX_DEPTH = 5
SERVICE_CAP = 25
FLOW_KINDS = {"http": "sync", "event": "async"}
SKIP_ROLES = {"script", "tests_target"}
SKIP_SERVICE_TYPES = {"test-suite", "library"}
CONF_RANK = {"low": 0, "medium": 1, "high": 2}
GENERIC = re.compile(r"^(?:map<.*>|object|string|integer|number|boolean|binary|any|uuid|T|void)"
                     r"(?:\[\])?$", re.I)
EVIDENCE_CAP = 10
ENTRY_ORDER = ("frontend", "scheduled", "event_publisher", "no_inbound", "uncovered")


def _min_conf(confs: Iterable[str]) -> str:
    return min(confs, key=lambda c: CONF_RANK.get(c, -1))


def _max_conf(confs: Iterable[str]) -> str:
    return max(confs, key=lambda c: CONF_RANK.get(c, -1))


def _names(v) -> list[str]:
    vals = v if isinstance(v, list) else [v]
    out = []
    for x in vals:
        if isinstance(x, str):
            for part in x.split("|"):
                part = part.strip()
                if part and not GENERIC.match(part):
                    out.append(part)
    return out


def topic_of(via: str) -> str:
    """``<broker>:<entity_type>:<name>`` -> ``<name>`` (normalized topic/queue name)."""
    parts = via.split(":", 2)
    return parts[2] if len(parts) == 3 else via


def display_via(kind: str, via: str) -> str:
    if kind == "event":
        parts = via.split(":", 2)
        etype = parts[1] if len(parts) == 3 else "topic"
        return f"{etype}:{topic_of(via)}"
    return via


def _edge_ok(e: dict, items: dict[str, dict[str, dict]], svc_types: dict[str, str]) -> bool:
    if e.get("kind") not in FLOW_KINDS or e.get("from") == e.get("to"):
        return False
    if e.get("caller_type") in ("test", "test-suite"):
        return False
    for sid in (e["from"], e["to"]):
        if svc_types.get(sid) in SKIP_SERVICE_TYPES:
            return False
    fis = [f for f in (e.get("from_items") or [e.get("from_item")]) if f]
    inv = items.get(e["from"], {})
    roles = [((inv.get(f) or {}).get("attributes") or {}).get("role") for f in fis]
    if roles and all(r in SKIP_ROLES for r in roles):
        return False
    ti = (items.get(e["to"], {}).get(e.get("to_item")) or {}).get("attributes") or {}
    return ti.get("role") not in SKIP_ROLES


def _edge_data(e: dict, items: dict[str, dict[str, dict]]) -> list[str]:
    """Schema names for one edge: callee contract first, caller DTOs as fallback."""
    out: list[str] = []
    ta = (items.get(e["to"], {}).get(e.get("to_item")) or {}).get("attributes") or {}
    fas = [(items.get(e["from"], {}).get(f) or {}).get("attributes") or {}
           for f in (e.get("from_items") or [e.get("from_item")]) if f]
    if e["kind"] == "event":
        for a in [ta] + fas:
            out += _names(a.get("payload"))
        return out
    out += _names(ta.get("request"))
    for r in ta.get("responses") or []:
        out += _names(r.get("schema"))
    if not out:
        for a in fas:
            out += _names(a.get("request")) + _names(a.get("response"))
    return out


def build_hops(edges: list[dict], items: dict[str, dict[str, dict]],
               svc_types: dict[str, str]) -> dict[tuple, dict]:
    """{(from, to, kind): hop} aggregating every eligible edge of that pair."""
    acc: dict[tuple, list[dict]] = defaultdict(list)
    for e in edges:
        if _edge_ok(e, items, svc_types):
            acc[(e["from"], e["to"], e["kind"])].append(e)
    hops = {}
    for key, es in acc.items():
        es = sorted(es, key=lambda e: (e.get("via") or "", e.get("id") or ""))
        vias = sorted({display_via(e["kind"], e.get("via") or "") for e in es})
        data = sorted({n for e in es for n in _edge_data(e, items)})
        ev, seen = [], set()
        for e in es:
            for x in e.get("evidence") or []:
                ref = (x.get("repo"), x.get("file"), x.get("line"))
                if ref not in seen:
                    seen.add(ref)
                    ev.append({"repo": ref[0], "file": ref[1], "line": ref[2]})
        hop = {"from": key[0], "to": key[1], "kind": key[2], "mode": FLOW_KINDS[key[2]],
               "via": vias[0], "vias": vias, "data": data,
               "confidence": _max_conf(e.get("confidence") or "low" for e in es),
               "criticality": sorted({e.get("criticality") for e in es if e.get("criticality")}),
               "edges": sorted(e["id"] for e in es if e.get("id")),
               "evidence": ev[:EVIDENCE_CAP], "evidence_total": len(ev)}
        if key[2] == "event":
            hop["topics"] = sorted({topic_of(e.get("via") or "") for e in es})
        hops[key] = hop
    return hops


def _entries(hops: dict[tuple, dict], svc_types: dict[str, str],
             scheduled: dict[str, list[str]]) -> list[tuple[str, str, str]]:
    """[(service_id, entry_type, trigger)] sorted; event entries are handled separately."""
    nodes = sorted({k[0] for k in hops})
    inbound = {k[1] for k in hops}
    out = []
    for n in nodes:
        if svc_types.get(n) == "frontend":
            out.append((n, "frontend", f"user action in {n} (frontend)"))
        if scheduled.get(n):
            jobs = scheduled[n]
            more = f" (+{len(jobs) - 3} more)" if len(jobs) > 3 else ""
            out.append((n, "scheduled", f"scheduled job(s) in {n} (job-to-call link not resolved): "
                                        f"{', '.join(jobs[:3])}{more}"))
        if n not in inbound and svc_types.get(n) != "frontend":
            out.append((n, "no_inbound", f"request to {n} from outside the registry (no internal caller)"))
    return out


def _walk(start: str, first: list[tuple] | None, adj: dict[str, list[tuple]],
          max_depth: int) -> list[list[tuple]]:
    """All maximal simple paths (lists of hop keys) from ``start``; ``first`` restricts hop 1."""
    out: list[list[tuple]] = []

    def dfs(node: str, path: list[tuple], visited: set[str]) -> None:
        nxt = [] if len(path) >= max_depth else [
            k for k in (first if not path and first is not None else adj.get(node, []))
            if k[1] not in visited]
        if not nxt:
            if path:
                out.append(list(path))
            return
        for k in nxt:
            path.append(k)
            visited.add(k[1])
            dfs(k[1], path, visited)
            visited.discard(k[1])
            path.pop()

    dfs(start, [], {start})
    return out


def _short_hash(keys: list[tuple]) -> str:
    sig = "|".join(f"{a}>{b}:{k}" for a, b, k in keys)
    return hashlib.sha1(sig.encode()).hexdigest()[:6]


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def build_flows(edges: list[dict], items: dict[str, dict[str, dict]], svc_types: dict[str, str],
                scheduled: dict[str, list[str]] | None = None,
                max_depth: int = MAX_DEPTH) -> list[dict]:
    """Pure core: deterministic list of flows sorted by flow_id."""
    scheduled = scheduled or {}
    hops = build_hops(edges, items, svc_types)
    adj: dict[str, list[tuple]] = defaultdict(list)
    for k in sorted(hops):
        adj[k[0]].append(k)
    paths_: dict[tuple, dict] = {}  # step-key sequence -> {entry, entry_types, triggers}

    def add(start: str, etype: str, trigger: str, first=None) -> None:
        for p in _walk(start, first, adj, max_depth):
            rec = paths_.setdefault(tuple(p), {"entry": start, "triggers": {}})
            rec["triggers"].setdefault(etype, set()).add(trigger)

    for n, etype, trig in _entries(hops, svc_types, scheduled):
        add(n, etype, trig)
    for k in sorted(k for k in hops if k[2] == "event"):
        add(k[0], "event_publisher", f"{k[0]} publishes {', '.join(hops[k]['topics'])}", [k])
    covered = {n for p in paths_ for k in p for n in k[:2]}
    for n in sorted(set(adj) - covered):  # cycle-only components
        if n not in covered:
            add(n, "uncovered", f"request to {n} (only reachable inside a cycle)")
            covered |= {x for p in paths_ for k in p for x in k[:2]}

    by_id: dict[str, list[tuple]] = defaultdict(list)
    for p, rec in paths_.items():
        by_id[f"{_slug(rec['entry'])}--{_slug(p[-1][1])}"].append(p)
    flows = []
    for base, ps in by_id.items():
        for p in ps:
            fid = base if len(ps) == 1 else f"{base}-{_short_hash(list(p))}"
            rec = paths_[p]
            steps = [dict(hops[k], n=i) for i, k in enumerate(p, 1)]
            nodes = [p[0][0]] + [k[1] for k in p]
            flows.append({
                "flow_id": fid, "name": f"{nodes[0]} → {nodes[-1]} ({len(p)} hop{'s' * (len(p) > 1)})",
                "entry": nodes[0], "terminal": nodes[-1], "services": nodes,
                "entry_types": [t for t in ENTRY_ORDER if t in rec["triggers"]],
                "triggers": [x for t in ENTRY_ORDER for x in sorted(rec["triggers"].get(t, ()))],
                "length": len(p), "truncated": len(p) >= max_depth and bool(
                    [k for k in adj.get(nodes[-1], []) if k[1] not in nodes]),
                "confidence": _min_conf(s["confidence"] for s in steps), "steps": steps})
    return sorted(flows, key=lambda f: f["flow_id"])


def load_inputs(org: str) -> tuple[list[dict], dict, dict, dict]:
    reg = paths.registry_dir()
    edges = (paths.read_json(reg / "edges.json", {}) or {}).get("edges", [])
    services = (paths.read_json(reg / org / "services.json", {}) or {}).get("services", {})
    svc_types = {sid: s.get("repo_type") for sid, s in services.items()}
    items: dict[str, dict[str, dict]] = {}
    scheduled: dict[str, list[str]] = {}
    base = paths.runs_dir(org)
    for inv_p in sorted(base.glob("*/inventory.json")) if base.is_dir() else []:
        inv = paths.read_json(inv_p) or {}
        sid = inv.get("service_id")
        if not sid:
            continue
        items[sid] = {it["id"]: it for it in inv.get("items") or []}
        jobs = sorted({(it["attributes"].get("name") or it["attributes"].get("expression") or "unnamed")
                       for it in inv.get("items") or [] if it["kind"] == "scheduled_job"})
        if jobs:
            scheduled[sid] = jobs
    return edges, items, svc_types, scheduled


def stats(flows: list[dict], all_services: Iterable[str]) -> dict:
    by_len: dict[str, int] = defaultdict(int)
    for f in flows:
        by_len[str(f["length"])] += 1
    covered = sorted({s for f in flows for s in f["services"] if not s.startswith("external:")})
    return {"flows": len(flows), "by_length": dict(sorted(by_len.items())),
            "services_covered": len(covered),
            "services_without_flow": sorted(set(all_services) - set(covered))}


def build_registry(org: str) -> dict:
    edges, items, svc_types, scheduled = load_inputs(org)
    flows = build_flows(edges, items, svc_types, scheduled)
    return {"schema_version": 1, "org": org, "version": FLOWS_VERSION, "max_depth": MAX_DEPTH,
            "stats": stats(flows, svc_types), "flows": flows}


def load_flows(org: str | None = None) -> list[dict] | None:
    """flows.json flows (None when not built yet); ``org`` filter when given."""
    doc = paths.read_json(paths.registry_dir() / "flows.json")
    if doc is None:
        return None
    if org and doc.get("org") not in (None, org):
        return []
    return doc.get("flows") or []


def role_of(flow: dict, sid: str) -> str:
    if flow["entry"] == sid:
        return "entry"
    if flow["terminal"] == sid:
        return "terminal"
    return "participant"


def select_for_service(flows: list[dict], sid: str, cap: int = SERVICE_CAP) -> tuple[list[dict], int]:
    """Top ``cap`` flows of ``sid`` by confidence, then length (longer first), then flow_id."""
    mine = [f for f in flows if sid in f["services"]]
    mine.sort(key=lambda f: (-CONF_RANK.get(f["confidence"], -1), -f["length"], f["flow_id"]))
    return sorted(mine[:cap], key=lambda f: f["flow_id"]), len(mine)


YAML_ROLE = {"entry": "orchestrator", "participant": "participant", "terminal": "consumer"}


def _cap_list(xs: list[str], n: int) -> str:
    if not xs:
        return ""
    return ", ".join(xs[:n]) + (f" (+{len(xs) - n} more)" if len(xs) > n else "")


def service_yaml_flows(flows: list[dict], sid: str) -> list[dict]:
    """service.yaml ``flows`` (template enum role orchestrator|participant|consumer)."""
    sel, _ = select_for_service(flows, sid)
    return [{"flow_id": f["flow_id"], "name": f["name"], "role": YAML_ROLE[role_of(f, sid)],
             "steps": [{"from": s["from"], "to": s["to"], "via": _cap_list(s["vias"], 1),
                        "data": _cap_list(s["data"], 5) or None, "source": "code"}
                       for s in f["steps"]]} for f in sel]


# ---------------------------------------------------------------- DATA_FLOWS.md rendering

def _cell(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def _alias(sid: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "_", sid)


def _mermaid_text(s: str) -> str:
    return re.sub(r"[;#]", " ", s)


def _store_label(key: str) -> str:
    parts = [p for p in key.split(":") if p and p != "_"]
    return ":".join(parts) or key


def render_flow(f: dict, sid: str, data_stores: dict[str, list[str]]) -> list[str]:
    svcs = f["services"]
    mids = svcs[1:-1]
    n_sync = sum(1 for s in f["steps"] if s["mode"] == "sync")
    n_async = len(f["steps"]) - n_sync
    through = (f" passes through {', '.join(f'`{m}`' for m in mids)} and" if mids else "")
    lines = [f"## Flow: {f['flow_id']}",
             f"Summary: Starting at `{svcs[0]}` ({'; '.join(f['triggers'])}), the flow{through} ends at "
             f"`{svcs[-1]}`, using {n_sync} sync HTTP hop(s) and {n_async} async event hop(s); "
             f"{sid} role: {role_of(f, sid)}; confidence {f['confidence']}"
             + ("; truncated at the depth cap." if f.get("truncated") else "."),
             "", "```mermaid", "sequenceDiagram"]
    for s in dict.fromkeys(svcs):
        lines.append(f"  participant {_alias(s)} as {s}")
    for s in f["steps"]:
        arrow = "->>" if s["mode"] == "sync" else "--)"
        more = f" (+{len(s['vias']) - 1} more)" if len(s["vias"]) > 1 else ""
        lines.append(f"  {_alias(s['from'])}{arrow}{_alias(s['to'])}: {_mermaid_text(s['via'])}{more}")
    lines += ["```", "", "Steps:",
              "| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |",
              "|---|---|---|---|---|---|---|"]
    for s in f["steps"]:
        lines.append(f"| {s['n']} | {s['from']} | {s['to']} | {_cell(_cap_list(s['vias'], 3))} | "
                     f"{_cell(_cap_list(s['data'], 5)) or 'Unknown'} | {s['mode']} | {s['confidence']} |")
    touched = [f"{x}: {', '.join(data_stores[x])}" for x in dict.fromkeys(svcs) if data_stores.get(x)]
    lines += ["", "Data touched: " + ("; ".join(touched) if touched else "Unknown (no data stores in registry)"),
              "", "Failure points: " + "; ".join(
                  f"hop {s['n']} {s['from']} → {s['to']}: criticality {'/'.join(s['criticality']) or 'unknown'}"
                  for s in f["steps"]), "", "Evidence:"]
    for s in f["steps"]:
        refs = [f"`{x['repo']}/{x['file']}:{x['line']}`" for x in s["evidence"][:3]]
        more = f" (+{s['evidence_total'] - len(refs)} more)" if s["evidence_total"] > len(refs) else ""
        lines.append(f"- hop {s['n']} ({s['from']} → {s['to']}): {', '.join(refs) or 'none'}{more}")
    lines.append("")
    return lines


def _split_sections(body: str) -> list[tuple[str, str]]:
    """[(heading, text incl. heading line)] for ``## `` sections outside code fences."""
    out, cur, buf, fence = [], None, [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
        if not fence and line.startswith("## "):
            if cur is not None:
                out.append((cur, "\n".join(buf)))
            cur, buf = line[3:].strip(), [line]
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out.append((cur, "\n".join(buf)))
    return out


def _neighbours(sid: str, edges: list[dict]) -> list[str]:
    out = set()
    for e in edges:
        if e.get("from") == e.get("to"):
            continue
        if e.get("from") == sid:
            out.add(f"outbound → {e['to']} ({e['kind']})")
        elif e.get("to") == sid:
            out.add(f"inbound ← {e['from']} ({e['kind']})")
    return sorted(out)


def render_data_flows(sid: str, flows: list[dict], edges: list[dict],
                      data_stores: dict[str, list[str]], existing: str | None) -> str:
    from .phase6_verify import split_front_matter  # local: phase6 imports phase5 imports this
    fm_old, body_old = split_front_matter(existing) if existing else (None, "")
    last = str((fm_old or {}).get("last_reviewed") or paths.utcnow()[:10])
    sel, total = select_for_service(flows, sid)
    ids = [f["flow_id"] for f in sel]
    lines = ["---", f"service_id: {sid}", "doc_type: data_flows", f"last_reviewed: {last}",
             f"flows: [{', '.join(ids)}]   # flow_ids, must match service.yaml `flows`", "---", "",
             f"# {sid} — Data Flows", "", "## Flow Index"]
    if sel:
        shown = (f"; showing the top {len(sel)} by confidence, then length" if total > len(sel) else "")
        lines.append(f"{sid} takes part in {total} end-to-end flow(s) in registry/flows.json{shown}.")
    lines += ["", f"| flow_id | Name | Role of {sid} | Trigger |", "|---|---|---|---|"]
    for f in sel:
        lines.append(f"| {f['flow_id']} | {_cell(f['name'])} | {role_of(f, sid)} | "
                     f"{_cell('; '.join(f['triggers']))} |")
    if not sel:
        nb = _neighbours(sid, edges)
        lines += ["| N/A | no end-to-end flow | N/A | N/A |", "",
                  f"N/A — {sid} takes part in no end-to-end flow in registry/flows.json "
                  "(no HTTP/event edge to or from another service).", ""]
        lines += (["Direct neighbours in registry/edges.json:"] + [f"- {x}" for x in nb[:20]]
                  + ([f"- (+{len(nb) - 20} more)"] if len(nb) > 20 else [])
                  if nb else ["Direct neighbours in registry/edges.json: none."])
    lines.append("")
    for f in sel:
        lines += render_flow(f, sid, data_stores)
    for head, text in _split_sections(body_old):  # keep sections the generator does not own
        if head != "Flow Index" and not head.startswith("Flow:"):
            lines += [text.rstrip(), ""]
    return "\n".join(lines).rstrip() + "\n"


def _write_text(p: Path, text: str) -> None:
    tmp = p.with_name(f"{p.name}.tmp.{os.getpid()}")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, p)


def run(org: OrgConfig) -> dict[str, Any]:
    doc = build_registry(org.name)
    paths.atomic_write_json(paths.registry_dir() / "flows.json", doc, sort_keys=True)
    edges = (paths.read_json(paths.registry_dir() / "edges.json", {}) or {}).get("edges", [])
    services = (paths.read_json(paths.registry_dir() / org.name / "services.json", {}) or {}).get(
        "services", {})
    stores = {sid: [_store_label(k) for k in s.get("data_stores") or []] for sid, s in services.items()}
    written = []
    for sid in sorted(services):
        out = paths.output_dir(org.name, sid)
        if not out.is_dir():
            continue
        p = out / "DATA_FLOWS.md"
        existing = p.read_text(encoding="utf-8") if p.exists() else None
        _write_text(p, render_data_flows(sid, doc["flows"], edges, stores, existing))
        written.append(sid)
    st = doc["stats"]
    return {**st, "data_flows_written": len(written)}
