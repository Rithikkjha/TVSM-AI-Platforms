"""Link repo_docs Chunk nodes to the graph entities they describe.

Writes ``(Chunk)-[:DESCRIBES {role, match}]->(Endpoint|Topic|Flow)``. Deterministic
(no LLM, no re-embedding), idempotent: every DESCRIBES edge from a repo_docs chunk
is deleted, then the current set is MERGEd.

* API_SPEC ``### METHOD path`` headings (chunk text or ``section_title``) -> the
  same service's Endpoint by method + normalized path (``role='primary'``);
  ``### None path`` -> path-only endpoints.
* Endpoint Index rows / scheduled-job handlers -> ``role='index'``; Outbound Calls
  rows -> the target service's Endpoint (``role='outbound'``). Capped per chunk.
* Events Published / Consumed -> Topics the service PUBLISHES / SUBSCRIBES
  (``match='name'`` when the topic name appears in the chunk, else ``'service_rel'``).
* DATA_FLOWS ``## Flow: <id>`` -> Flow (``primary``); Flow Index rows -> ``index``.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from ingestion.repo_docs_ingest.common import ORIGIN, run_cypher, unwind_write
from ingestion.repo_docs_ingest.graph_loader import normalize_path

MULTI_CAP = 20
_METHODS = "GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|None"
_H3_EP_RE = re.compile(rf"^### ({_METHODS}) (\S+)\s*$", re.M)
_TITLE_EP_RE = re.compile(rf"^({_METHODS}) (\S+)$")
_ROW_EP_RE = re.compile(rf"^\|\s*(?:`?([^|`]*?)`?\s*\|\s*)?({_METHODS})\s*\|\s*`([^`]+)`", re.M)
_FLOW_ROW_RE = re.compile(r"^\|\s*([A-Za-z0-9][^|\s]*)\s*\|", re.M)


def _key(method: str | None, path: str) -> tuple[str | None, str]:
    m = None if not method or method == "None" else method.upper()
    return m, normalize_path(path).lower()


def _title_headings(section_title: str) -> list[str]:
    """H3 names from ``"H2 › a, b, c …"``."""

    if " › " not in section_title:
        return []
    tail = section_title.split(" › ", 1)[1].replace(" …", "")
    return [h.strip() for h in tail.split(", ") if h.strip()]


async def _load(session: Any) -> dict[str, Any]:
    chunks = await run_cypher(
        session,
        "MATCH (c:Chunk {origin: $o}) RETURN c.source_id AS id, c.service_id AS sid, c.doc_type AS dt, "
        "c.section_title AS title, c.text AS text",
        o=ORIGIN,
    )
    eps = await run_cypher(
        session,
        "MATCH (s:Service)-[:EXPOSES]->(e:Endpoint) RETURN e.source_id AS id, s.name AS sid, e.kind AS kind, "
        "e.method AS method, e.path AS path, e.handler AS handler",
    )
    topics = await run_cypher(
        session,
        "MATCH (s:Service)-[r:PUBLISHES|SUBSCRIBES]->(t:Topic) RETURN DISTINCT s.name AS sid, type(r) AS rel, "
        "t.source_id AS id, t.name AS name, t.raw_names AS raw",
    )
    flows = await run_cypher(session, "MATCH (f:Flow) RETURN f.source_id AS id, f.flow_id AS fid")
    all_topics = await run_cypher(session, "MATCH (t:Topic) RETURN t.source_id AS id")
    return {"chunks": chunks, "eps": eps, "topics": topics, "flows": flows, "n_topics": len(all_topics)}


def compute(data: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_key: dict[str, dict[tuple[str | None, str], list[str]]] = defaultdict(lambda: defaultdict(list))
    by_path: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    handlers: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for e in data["eps"]:
        if e["path"]:
            by_key[e["sid"]][_key(e["method"], e["path"])].append(e["id"])
            by_path[e["sid"]][normalize_path(e["path"]).lower()].append(e["id"])
        if e["kind"] != "http" and e["handler"]:
            handlers[e["sid"]].append((e["handler"], e["id"]))
    svc_topics: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for t in data["topics"]:
        svc_topics[(t["sid"], t["rel"])].append(t)
    flow_ids = {f["fid"]: f["id"] for f in data["flows"] if f["fid"]}

    links: dict[tuple[str, str], dict[str, Any]] = {}
    unmatched: list[str] = []

    def add(cid: str, eid: str, role: str, match: str) -> None:
        links.setdefault((cid, eid), {"chunk": cid, "entity": eid, "role": role, "match": match})

    def find_ep(sid: str, method: str, path: str) -> list[str]:
        hit = by_key.get(sid, {}).get(_key(method, path))
        if hit:
            return hit
        if method == "None":
            return by_path.get(sid, {}).get(normalize_path(path).lower(), [])
        return []

    for c in data["chunks"]:
        cid, sid, dt, text = c["id"], c["sid"], c["dt"], c["text"] or ""
        title = c["title"] or ""
        h2 = title.split(" › ", 1)[0]
        if dt == "API_SPEC" and h2 == "Endpoints":
            heads = [(m.group(1), m.group(2)) for m in _H3_EP_RE.finditer(text)]
            for h in _title_headings(title):
                m = _TITLE_EP_RE.match(h)
                if m and (m.group(1), m.group(2)) not in heads:
                    heads.append((m.group(1), m.group(2)))
            for method, path in heads:
                found = find_ep(sid, method, path)
                if not found:
                    unmatched.append(f"{sid}: {method} {path}")
                for eid in found:
                    add(cid, eid, "primary", "heading")
        elif dt == "API_SPEC" and h2 in ("Endpoint Index", "Outbound Calls"):
            n = 0
            for m in _ROW_EP_RE.finditer(text):
                if n >= MULTI_CAP:
                    break
                if h2 == "Outbound Calls":
                    target = (m.group(1) or "").strip()
                    found = find_ep(target, m.group(2), m.group(3)) if target else []
                    role = "outbound"
                else:
                    found = find_ep(sid, m.group(2), m.group(3))
                    role = "index"
                for eid in found[: MULTI_CAP - n]:
                    add(cid, eid, role, "table_row")
                    n += 1
            if h2 == "Endpoint Index":
                for handler, eid in handlers.get(sid, []):
                    if n < MULTI_CAP and handler in text:
                        add(cid, eid, "index", "handler")
                        n += 1
        elif dt == "API_SPEC" and h2 in ("Events Published", "Events Consumed"):
            rel = "PUBLISHES" if h2 == "Events Published" else "SUBSCRIBES"
            low = text.lower()
            for t in svc_topics.get((sid, rel), [])[:MULTI_CAP]:
                names = [t["name"], *(t["raw"] or [])]
                hit = any(re.search(rf"(?<![\w.-]){re.escape(n.lower())}(?![\w-])", low) for n in names if n)
                add(cid, t["id"], "events", "name" if hit else "service_rel")
        elif dt == "DATA_FLOWS" and h2.startswith("Flow: "):
            fid = h2[len("Flow: ") :].strip()
            if fid in flow_ids:
                add(cid, flow_ids[fid], "primary", "heading")
            else:
                unmatched.append(f"{sid}: Flow {fid}")
        elif dt == "DATA_FLOWS" and h2 == "Flow Index":
            n = 0
            for m in _FLOW_ROW_RE.finditer(text):
                if n >= MULTI_CAP:
                    break
                if m.group(1) in flow_ids:
                    add(cid, flow_ids[m.group(1)], "index", "table_row")
                    n += 1

    rows = list(links.values())
    ep_ids = {e["id"] for e in data["eps"]}
    covered = Counter()
    seen: set[str] = set()
    for r in rows:
        if r["entity"] in seen:
            continue
        seen.add(r["entity"])
        covered["Endpoint" if r["entity"] in ep_ids else r["entity"].split(":", 1)[0]] += 1
    primary_eps = {r["entity"] for r in rows if r["entity"] in ep_ids and r["role"] == "primary"}
    n_eps, n_flows = len(ep_ids), len(flow_ids)
    report = {
        "describes_rels": len(rows),
        "by_role": dict(Counter(r["role"] for r in rows)),
        "endpoints_covered": f"{covered['Endpoint']}/{n_eps} ({100 * covered['Endpoint'] / max(n_eps, 1):.1f}%)",
        "endpoints_with_primary_chunk": f"{len(primary_eps)}/{n_eps} ({100 * len(primary_eps) / max(n_eps, 1):.1f}%)",
        "topics_covered": f"{covered['topic']}/{data['n_topics']} ({100 * covered['topic'] / max(data['n_topics'], 1):.1f}%)",
        "flows_covered": f"{covered['flow']}/{n_flows} ({100 * covered['flow'] / max(n_flows, 1):.1f}%)",
        "unmatched_headings": len(unmatched),
        "unmatched_samples": unmatched[:10],
    }
    return rows, report


async def link_chunks(driver: Any, run_id: str, dry_run: bool = False) -> dict[str, Any]:
    async with driver.session() as s:
        rows, report = compute(await _load(s))
        if dry_run:
            return report
        deleted = (await run_cypher(
            s, "MATCH (c:Chunk {origin: $o})-[r:DESCRIBES]->() DELETE r RETURN count(r) AS n", o=ORIGIN))[0]["n"]
        for prefix, label in (("endpoint:", "Endpoint"), ("topic:", "Topic"), ("flow:", "Flow")):
            await unwind_write(
                s,
                f"MATCH (c:Chunk {{source_id: row.chunk}}) MATCH (e:{label} {{source_id: row.entity}}) "
                "MERGE (c)-[r:DESCRIBES]->(e) SET r.role = row.role, r.match = row.match, "
                f"r.source = 'deterministic', r.origin = '{ORIGIN}', r.ingest_run = '{run_id}'",
                [r for r in rows if r["entity"].startswith(prefix)],
            )
        written = (await run_cypher(
            s, "MATCH (c:Chunk {origin: $o})-[r:DESCRIBES]->() RETURN count(r) AS n", o=ORIGIN))[0]["n"]
    return {**report, "deleted_old": deleted, "written": written}
