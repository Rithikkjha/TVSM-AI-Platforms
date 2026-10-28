"""MCP wrappers for the repo_docs graph tools (resolve argument -> fixed Cypher -> JSON)."""

from __future__ import annotations

import json
from typing import Any

from neo4j import AsyncGraphDatabase

from config.settings import get_settings
from retrieval.search import repo_graph
from retrieval.search.entity_linker import get_index, resolve_name


def _driver():  # type: ignore[no-untyped-def]
    s = get_settings()
    return AsyncGraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password))


def _dump(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


def _resolve(service: str) -> tuple[str | None, dict[str, Any] | None]:
    sid, cands = resolve_name(service)
    if sid:
        return sid, None
    if len(cands) > 1:
        return None, {"error": "ambiguous", "message": f"'{service}' could refer to: {', '.join(cands)}",
                      "candidates": cands}
    return None, {"error": "not_found", "message": f"Service '{service}' not found"}


async def _with_service(service: str, fn, key: str, **kw: Any) -> str:  # type: ignore[no-untyped-def]
    sid, err = _resolve(service)
    if err:
        return _dump(err)
    driver = _driver()
    try:
        rows = await fn(driver, sid, **kw)
    finally:
        await driver.close()
    return _dump({"service": sid, "query": service, key: rows, "count": len(rows)})


async def dependencies(service: str, hops: int = 1) -> str:
    return await _with_service(service, repo_graph.get_dependencies, "dependencies", hops=hops)


async def dependents(service: str, hops: int = 2) -> str:
    return await _with_service(service, repo_graph.get_dependents, "dependents", hops=hops)


async def flows(service: str) -> str:
    return await _with_service(service, repo_graph.get_flows, "flows")


async def config_keys(service: str) -> str:
    return await _with_service(service, repo_graph.get_config_keys, "config_keys")


async def service_tickets(service: str, min_confidence: str = "low", limit: int = 50) -> str:
    return await _with_service(service, repo_graph.get_service_tickets, "tickets",
                               min_confidence=(min_confidence or "low").strip().lower(), limit=limit)


def _topic_name(topic: str) -> str:
    q = topic.strip()
    info = get_index().topics.get(q.lower())
    return info["name"] if info else q


async def _members(topic: str, rel: str, key: str) -> str:
    name = _topic_name(topic)
    driver = _driver()
    try:
        rows = await repo_graph.topic_members(driver, name, rel)
        docs = await repo_graph.describing_chunks(driver, [r["topic_id"] for r in rows])
    finally:
        await driver.close()
    linked = [c for chunks in docs.values() for c in chunks]
    return _dump({"topic": name, key: rows, "count": len(rows), "docs": linked})


async def publishers(topic: str) -> str:
    return await _members(topic, "PUBLISHES", "publishers")


async def subscribers(topic: str) -> str:
    return await _members(topic, "SUBSCRIBES", "subscribers")


async def endpoint(path: str, method: str = "", service: str = "") -> str:
    sid = None
    if service.strip():
        sid, err = _resolve(service)
        if err:
            return _dump(err)
    driver = _driver()
    try:
        rows = await repo_graph.get_endpoint(driver, method.strip() or None, path.strip(), sid)
    finally:
        await driver.close()
    return _dump({"path": path, "method": method or None, "service": sid, "endpoints": rows, "count": len(rows)})
