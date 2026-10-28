"""Fixed-Cypher queries over the repo_docs graph (Phase 8 MCP graph tools).

Every function takes a neo4j async driver and an already-resolved service_id /
topic name. Direction convention: ``(a)-[:DEPENDS_ON]->(b)`` means a calls b.
Config keys are returned by NAME only (no values exist in the graph).
"""

from __future__ import annotations

import json
from typing import Any

_HOPS_MAX = 4


def _hops(h: int) -> int:
    return max(1, min(int(h or 1), _HOPS_MAX))


async def _rows(driver: Any, cypher: str, **params: Any) -> list[dict[str, Any]]:
    async with driver.session() as s:
        result = await s.run(cypher, **params)
        return [dict(r) for r in await result.data()]


def _ev(raw: Any, limit: int = 3) -> list[Any]:
    try:
        return (json.loads(raw) if isinstance(raw, str) else raw or [])[:limit]
    except (TypeError, ValueError):
        return []


#: Bound on linked doc text attached to graph results (~1,500 tokens).
DOCS_MAX_CHARS = 6000
DOCS_PER_ENTITY = 2


async def describing_chunks(
    driver: Any, entity_ids: list[str], per_entity: int = DOCS_PER_ENTITY, max_chars: int = DOCS_MAX_CHARS
) -> dict[str, list[dict[str, Any]]]:
    """``entity source_id -> [{chunk_id, section_title, text}]`` via ``(Chunk)-[:DESCRIBES]->``.

    Primary (heading) chunks first; at most ``per_entity`` per entity and
    ``max_chars`` of text in total, in ``entity_ids`` order. A chunk already
    attached to an earlier entity is not repeated.
    """

    if not entity_ids:
        return {}
    rows = await _rows(
        driver,
        "UNWIND $ids AS id MATCH (c:Chunk)-[r:DESCRIBES]->(e:Endpoint|Topic|Flow {source_id: id}) "
        "RETURN id, c.source_id AS chunk_id, c.section_title AS section_title, c.text AS text, "
        "CASE r.role WHEN 'primary' THEN 0 WHEN 'events' THEN 1 WHEN 'index' THEN 2 ELSE 3 END AS rank "
        "ORDER BY rank, size(c.text)",
        ids=list(dict.fromkeys(entity_ids)),
    )
    by_id: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_id.setdefault(r["id"], []).append(r)
    out: dict[str, list[dict[str, Any]]] = {}
    used, seen = 0, set()
    for eid in dict.fromkeys(entity_ids):
        for r in by_id.get(eid, []):
            if len(out.get(eid, [])) >= per_entity or used >= max_chars:
                break
            if r["chunk_id"] in seen:
                continue
            text = (r["text"] or "")[: max_chars - used]
            seen.add(r["chunk_id"])
            used += len(text)
            out.setdefault(eid, []).append(
                {"chunk_id": r["chunk_id"], "section_title": r["section_title"], "text": text}
            )
    return out


async def linked_context(
    driver: Any,
    topic_ids: list[str],
    endpoints: list[dict[str, Any]],
    chunk_ids: list[str],
    max_notes: int = 8,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Ask-pipeline glue for the DESCRIBES links (both directions).

    * entity -> chunks: topics / endpoints resolved in the question -> their
      describing chunks (bounded by :func:`describing_chunks`), minus ``chunk_ids``.
    * chunk -> entity: retrieved repo_docs ``chunk_ids`` -> one-line notes on the
      Endpoint / Topic / Flow they describe (primary/events links only).
    """

    from retrieval.search.entity_linker import normalize_path

    ep_ids: list[str] = []
    if endpoints:
        ep_rows = await _rows(
            driver,
            "UNWIND $eps AS ep MATCH (e:Endpoint {service_id: ep.service, method: ep.method}) "
            "WHERE e.path_normalized = ep.norm RETURN e.source_id AS id",
            eps=[{"service": e["service"], "method": e["method"], "norm": normalize_path(e["path"])}
                 for e in endpoints[:3]],
        )
        ep_ids = [r["id"] for r in ep_rows]
    docs = await describing_chunks(driver, ep_ids + list(topic_ids[:3]))
    skip = set(chunk_ids)
    linked = [c for eid in docs for c in docs[eid] if c["chunk_id"] not in skip]

    notes: list[str] = []
    if chunk_ids:
        rows = await _rows(
            driver,
            "UNWIND $ids AS cid MATCH (c:Chunk {source_id: cid})-[r:DESCRIBES]->(e) "
            "WHERE r.role IN ['primary', 'events'] "
            "OPTIONAL MATCH (p:Service)-[:PUBLISHES]->(e) OPTIONAL MATCH (sb:Service)-[:SUBSCRIBES]->(e) "
            "RETURN DISTINCT e.source_id AS id, labels(e)[0] AS label, e.method AS method, e.path AS path, "
            "e.service_id AS service, e.request AS request, e.callers AS callers, e.name AS name, "
            "e.services AS flow_services, collect(DISTINCT p.name) AS pubs, collect(DISTINCT sb.name) AS subs",
            ids=list(dict.fromkeys(chunk_ids)),
        )
        for r in rows[:max_notes]:
            if r["label"] == "Endpoint":
                notes.append(
                    f"Endpoint {r['method'] or ''} {r['path']} ({r['service']}): request {r['request'] or 'none'}; "
                    f"callers {', '.join(r['callers'] or []) or 'unknown'}."
                )
            elif r["label"] == "Topic":
                notes.append(
                    f"Topic {r['name']}: publishers {', '.join(r['pubs']) or 'none'}; "
                    f"subscribers {', '.join(r['subs']) or 'none'}."
                )
            elif r["label"] == "Flow":
                notes.append(f"Flow {r['name']}: services {' -> '.join(r['flow_services'] or [])}.")
    return linked, notes


async def get_dependencies(driver: Any, service_id: str, hops: int = 1) -> list[dict[str, Any]]:
    """What ``service_id`` depends on (calls), up to ``hops``, plus external calls."""

    rows = await _rows(
        driver,
        f"MATCH p = (s:Service {{name: $sid}})-[:DEPENDS_ON*1..{_hops(hops)}]->(t:Service) "
        "WITH t, min(length(p)) AS hop, collect(last(relationships(p))) AS rs "
        "WITH t, hop, rs[0] AS r "
        "RETURN t.name AS service, hop, r.kinds AS kinds, r.confidence AS confidence, "
        "r.vias AS vias, r.evidence AS evidence ORDER BY hop, service",
        sid=service_id,
    )
    ext = await _rows(
        driver,
        "MATCH (s:Service {name: $sid})-[r:CALLS|DEPENDS_ON_LIBRARY]->(x:ExternalSystem) "
        "RETURN x.name AS external, type(r) AS rel, r.via AS via, r.confidence AS confidence, r.evidence AS evidence",
        sid=service_id,
    )
    out = [{**r, "evidence": _ev(r["evidence"])} for r in rows]
    out += [{**r, "evidence": _ev(r["evidence"]), "hop": 1} for r in ext]
    return out


async def get_dependents(driver: Any, service_id: str, hops: int = 2) -> list[dict[str, Any]]:
    """Blast radius: services that (transitively) depend on ``service_id``."""

    rows = await _rows(
        driver,
        f"MATCH p = (t:Service)-[:DEPENDS_ON*1..{_hops(hops)}]->(s:Service {{name: $sid}}) "
        "WITH t, min(length(p)) AS hop, collect(head(relationships(p))) AS rs "
        "WITH t, hop, rs[0] AS r "
        "RETURN t.name AS service, hop, r.kinds AS kinds, r.confidence AS confidence, "
        "r.vias AS vias, r.evidence AS evidence ORDER BY hop, service",
        sid=service_id,
    )
    return [{**r, "evidence": _ev(r["evidence"])} for r in rows]


async def topic_members(driver: Any, topic: str, rel: str) -> list[dict[str, Any]]:
    assert rel in ("PUBLISHES", "SUBSCRIBES")
    return await _rows(
        driver,
        f"MATCH (s:Service)-[r:{rel}]->(t:Topic) "
        "WHERE toLower(t.name) = toLower($topic) OR any(n IN t.raw_names WHERE toLower(n) = toLower($topic)) "
        "RETURN t.source_id AS topic_id, t.name AS topic, t.broker AS broker, t.entity_type AS entity_type, s.name AS service, "
        "r.subscription AS subscription, r.namespace AS namespace ORDER BY topic, service",
        topic=topic,
    )


async def get_flows(driver: Any, service_id: str, limit: int = 20) -> list[dict[str, Any]]:
    rows = await _rows(
        driver,
        "MATCH (s:Service {name: $sid})-[r:PART_OF_FLOW]->(f:Flow) "
        "RETURN f.source_id AS fid, f.flow_id AS flow_id, f.name AS name, r.role AS role, f.entry AS entry, "
        "f.terminal AS terminal, f.length AS length, f.confidence AS confidence, f.steps AS steps "
        "ORDER BY CASE r.role WHEN 'entry' THEN 0 ELSE 1 END, f.length DESC, f.flow_id LIMIT $limit",
        sid=service_id,
        limit=limit,
    )
    for r in rows:
        steps = _ev(r.pop("steps"), limit=50)
        r["steps"] = [
            {k: st.get(k) for k in ("n", "from", "to", "kind", "mode", "via", "data", "confidence")}
            for st in steps
        ]
    docs = await describing_chunks(driver, [r["fid"] for r in rows])
    for r in rows:
        r["docs"] = docs.get(r.pop("fid"), [])
    return rows


async def get_endpoint(
    driver: Any, method: str | None, path: str, service_id: str | None = None
) -> list[dict[str, Any]]:
    """Endpoint params / request / responses with schema fields."""

    from retrieval.search.entity_linker import normalize_path

    rows = await _rows(
        driver,
        "MATCH (s:Service)-[:EXPOSES]->(e:Endpoint) "
        "WHERE ($sid IS NULL OR s.name = $sid) AND ($method IS NULL OR e.method = $method) "
        "AND (e.path = $path OR e.path_normalized = $norm) "
        "OPTIONAL MATCH (e)-[:REQUEST]->(rq:Schema) "
        "OPTIONAL MATCH (e)-[rr:RESPONDS]->(rs:Schema) "
        "WITH s, e, rq, collect(CASE WHEN rs IS NULL THEN NULL ELSE "
        "{status: rr.status, schema: rs.name, fields: rs.fields} END) AS resp_schemas "
        "RETURN e.source_id AS endpoint_id, s.name AS service, e.method AS method, e.path AS path, e.auth AS auth, "
        "e.handler AS handler, e.params AS params, e.request AS request, rq.fields AS request_fields, "
        "e.responses AS responses, resp_schemas, e.callers AS callers ORDER BY service",
        sid=service_id,
        method=method.upper() if method else None,
        path=path,
        norm=normalize_path(path),
    )
    for r in rows:
        r["params"] = _ev(r["params"], 100)
        r["responses"] = _ev(r["responses"], 100)
        r["request_fields"] = _ev(r["request_fields"], 200)
        r["response_schemas"] = [
            {**x, "fields": _ev(x.get("fields"), 200)} for x in r.pop("resp_schemas") or []
        ]
    docs = await describing_chunks(driver, [r["endpoint_id"] for r in rows])
    for r in rows:
        r["docs"] = docs.get(r["endpoint_id"], [])
    return rows


async def list_service_endpoints(driver: Any, service: str) -> list[dict[str, Any]]:
    """All HTTP endpoints a service EXPOSES: method + path, sorted.

    ``service`` may be a service name, source_id, or an alias. Resolution
    matches the Service by name/source_id directly, or via a linked Alias
    node (case-insensitive), mirroring get_service_by_name's alias handling.
    Returns [] if the service isn't found or exposes nothing. Deterministic,
    no LLM, no similarity cutoff — this is the authoritative list.
    """
    rows = await _rows(
        driver,
        "MATCH (s:Service) "
        "WHERE s.deleted_at IS NULL AND ("
        "  toLower(s.name) = toLower($svc) "
        "  OR s.source_id = $svc "
        "  OR s.source_id = 'service:' + toLower($svc) "
        "  OR EXISTS { MATCH (a:Alias)-[:ALSO_KNOWN_AS]->(s) WHERE toLower(a.name) = toLower($svc) } "
        ") "
        "WITH s LIMIT 1 "
        "MATCH (s)-[:EXPOSES]->(e:Endpoint) "
        "WHERE e.deleted_at IS NULL "
        "RETURN s.name AS service, e.method AS method, e.path AS path, "
        "e.auth AS auth, e.handler AS handler "
        "ORDER BY e.path, e.method",
        svc=service,
    )
    return rows


async def get_config_keys(driver: Any, service_id: str) -> list[dict[str, Any]]:
    """Config key NAMES (plus secret/required flags). Never values."""

    return await _rows(
        driver,
        "MATCH (s:Service {name: $sid})-[:USES_CONFIG]->(c:ConfigKey) "
        "RETURN c.name AS name, c.secret AS secret, c.required AS required, "
        "c.provided_by AS provided_by ORDER BY name",
        sid=service_id,
    )


_CONF_ORDER = "CASE r.confidence WHEN 'high' THEN 0 WHEN 'medium' THEN 1 WHEN 'low' THEN 2 ELSE 3 END"


async def get_service_tickets(
    driver: Any, service_id: str, min_confidence: str = "low", limit: int = 50
) -> list[dict[str, Any]]:
    """Jira tickets ``LINKED_TO`` the service, with link confidence / matched terms / hits."""

    allowed = {"high": ["high"], "medium": ["high", "medium"]}.get(min_confidence, ["high", "medium", "low"])
    return await _rows(
        driver,
        "MATCH (t:Ticket)-[r:LINKED_TO]->(s:Service {name: $sid}) WHERE r.confidence IN $allowed "
        "RETURN t.key AS key, t.title AS title, t.source_id AS source_id, t.updated_at AS updated_at, "
        "r.confidence AS confidence, r.matched AS matched, r.hits AS hits, r.source AS link_source "
        f"ORDER BY {_CONF_ORDER}, r.hits DESC, t.updated_at DESC LIMIT $limit",
        sid=service_id,
        allowed=allowed,
        limit=max(1, min(int(limit or 50), 200)),
    )


async def service_context(driver: Any, service_id: str) -> str:
    """Compact text block seeded from ``service:<id>`` for the ask pipeline."""

    rows = await _rows(
        driver,
        "MATCH (s:Service {name: $sid}) "
        "OPTIONAL MATCH (s)-[:DEPENDS_ON]->(d:Service) "
        "WITH s, collect(DISTINCT d.name) AS deps "
        "OPTIONAL MATCH (u:Service)-[:DEPENDS_ON]->(s) "
        "WITH s, deps, collect(DISTINCT u.name) AS dependents "
        "OPTIONAL MATCH (s)-[:PUBLISHES]->(tp:Topic) "
        "WITH s, deps, dependents, collect(DISTINCT tp.name) AS pubs "
        "OPTIONAL MATCH (s)-[:SUBSCRIBES]->(ts:Topic) "
        "WITH s, deps, dependents, pubs, collect(DISTINCT ts.name) AS subs "
        "OPTIONAL MATCH (s)-[:CALLS]->(x:ExternalSystem) "
        "RETURN s.name AS name, s.summary AS summary, s.type AS type, s.domain AS domain, "
        "s.aliases AS aliases, deps, dependents, pubs, subs, collect(DISTINCT x.name) AS externals",
        sid=service_id,
    )
    if not rows:
        return ""
    r = rows[0]

    def j(v: list[str] | None) -> str:
        return ", ".join(v or []) or "none"

    return (
        f"- {r['name']} ({r['type'] or 'unknown type'}, domain {r['domain'] or 'unknown'}): {r['summary'] or ''}\n"
        f"  aka: {j(r['aliases'])}\n"
        f"  depends on (calls): {j(r['deps'])}; external: {j(r['externals'])}\n"
        f"  depended on by: {j(r['dependents'])}\n"
        f"  publishes: {j(r['pubs'])}; subscribes: {j(r['subs'])}"
    )
