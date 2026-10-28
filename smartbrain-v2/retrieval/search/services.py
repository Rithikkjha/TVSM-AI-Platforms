"""FastAPI router for service-related query endpoints.

Implements GET /v1/services/{name} which returns a service node with
its ownership, dependencies, linked tickets, and documents.

Requirements: 3.1, 3.5, 3.9, 4.2
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from config.settings import get_settings
from retrieval.search import graph_queries
from retrieval.search.freshness import check_staleness
from api.schemas import AffectedService, EntityRef, ImpactResponse, ServiceResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _json_safe(obj: Any) -> Any:
    """Recursively convert values that aren't natively JSON-serializable.

    Neo4j returns temporal properties (created_at/updated_at) as neo4j.time
    DateTime/Date objects which the stdlib json encoder can't serialize,
    causing a 500 on service detail. We convert any object exposing
    ``iso_format()`` (neo4j temporals) or ``isoformat()`` (datetime/date) to
    its ISO string, and recurse through dicts/lists.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    # neo4j.time types expose iso_format(); datetime/date expose isoformat()
    for attr in ("iso_format", "isoformat"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:  # noqa: BLE001
                break
    return str(obj)


def _get_neo4j_driver() -> Any:
    """Get the Neo4j driver from the app state.

    In production, this would be initialized at startup. For V1, we
    import it lazily to allow mocking in tests.
    """
    from neo4j import AsyncGraphDatabase

    settings = get_settings()
    return AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )





@router.get("/services")
async def list_services(
    q: str | None = Query(default=None, description="Optional filter on name + aliases"),
) -> JSONResponse:
    """Return all services with their display name, domain, summary and aliases.

    Powers the UI Search tab. Clients filter locally against name + aliases,
    but an optional ``?q=`` performs the same case-insensitive substring
    filter server-side. Each service's ``name`` is the identifier that
    GET /v1/services/{name} resolves against.
    """
    driver = _get_neo4j_driver()
    try:
        services = await graph_queries.list_services(driver)

        if q and q.strip():
            needle = q.strip().lower()
            services = [
                s
                for s in services
                if needle in (s.get("name") or "").lower()
                or needle in (s.get("display_name") or "").lower()
                or any(needle in (a or "").lower() for a in s.get("aliases", []))
            ]

        return JSONResponse(
            status_code=200,
            content=_json_safe({"services": services, "total": len(services)}),
        )
    finally:
        await driver.close()


@router.get("/services/{name}")
async def get_service(name: str) -> JSONResponse:
    """Return a service node with all related entities.

    Fetches the service by name, then retrieves owners, upstream/downstream
    dependencies, linked tickets, and documents via graph traversal.

    Returns 404 with a helpful message if the service is not found.
    """
    driver = _get_neo4j_driver()
    try:
        # Look up service by name
        service = await graph_queries.get_service_by_name(driver, name)

        if service is None:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "not_found",
                    "message": f"Service '{name}' not found in graph",
                },
            )

        source_id = service.get("source_id", "")

        # Fetch all related entities
        owners_raw = await graph_queries.get_service_owners(driver, source_id)
        upstream_raw = await graph_queries.get_service_dependencies(
            driver, source_id, "upstream"
        )
        downstream_raw = await graph_queries.get_service_dependencies(
            driver, source_id, "downstream"
        )
        tickets_raw = await graph_queries.get_service_tickets(driver, source_id)
        documents_raw = await graph_queries.get_service_documents(driver, source_id)

        # Build response
        owners = [
            EntityRef(
                source_id=o.get("source_id", ""),
                name=o.get("name"),
            )
            for o in owners_raw
        ]

        upstream_dependencies = [
            EntityRef(
                source_id=d.get("source_id", ""),
                name=d.get("name"),
                dependency_type=d.get("rel_props", {}).get("dependency_type"),
            )
            for d in upstream_raw
        ]

        downstream_dependents = [
            EntityRef(
                source_id=d.get("source_id", ""),
                name=d.get("name"),
                dependency_type=d.get("rel_props", {}).get("dependency_type"),
            )
            for d in downstream_raw
        ]

        linked_tickets = [
            EntityRef(
                source_id=t.get("source_id", ""),
                key=t.get("key"),
                title=t.get("title"),
                status=t.get("status"),
                priority=t.get("priority"),
            )
            for t in tickets_raw
        ]

        documents = [
            EntityRef(
                source_id=d.get("source_id", ""),
                title=d.get("title"),
                url=d.get("url"),
            )
            for d in documents_raw
        ]

        # Check staleness
        staleness = check_staleness(service.get("updated_at"))

        response = ServiceResponse(
            service=service,
            owners=owners,
            upstream_dependencies=upstream_dependencies,
            downstream_dependents=downstream_dependents,
            linked_tickets=linked_tickets,
            documents=documents,
            staleness=staleness,
        )

        return JSONResponse(status_code=200, content=_json_safe(response.model_dump()))

    finally:
        await driver.close()


@router.get("/services/{name}/impact")
async def get_service_impact(name: str) -> JSONResponse:
    """Return the transitive dependency set (up to 2 hops) with linked epics and tickets.

    Finds all services that depend on the queried service (incoming DEPENDS_ON)
    up to 2 hops, along with any epics and tickets linked to those affected services.

    Returns 404 with a helpful message if the service is not found.
    """
    driver = _get_neo4j_driver()
    try:
        # Look up service by name
        service = await graph_queries.get_service_by_name(driver, name)

        if service is None:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "not_found",
                    "message": f"Service '{name}' not found in graph",
                },
            )

        source_id = service.get("source_id", "")

        # Get impact graph (BFS traversal of incoming DEPENDS_ON up to 2 hops)
        impact_data = await graph_queries.get_impact_graph(driver, source_id, max_hops=2)

        # Build response
        affected_services = [
            AffectedService(
                source_id=s["source_id"],
                name=s["name"],
                hops=s["hops"],
            )
            for s in impact_data["affected_services"]
        ]

        linked_epics = [
            EntityRef(
                source_id=e.get("source_id", ""),
                key=e.get("key"),
                title=e.get("title"),
                status=e.get("status"),
            )
            for e in impact_data["linked_epics"]
        ]

        linked_tickets = [
            EntityRef(
                source_id=t.get("source_id", ""),
                key=t.get("key"),
                title=t.get("title"),
                status=t.get("status"),
                priority=t.get("priority"),
            )
            for t in impact_data["linked_tickets"]
        ]

        response = ImpactResponse(
            service=name,
            max_hops=2,
            affected_services=affected_services,
            linked_epics=linked_epics,
            linked_tickets=linked_tickets,
        )

        return JSONResponse(status_code=200, content=_json_safe(response.model_dump()))

    finally:
        await driver.close()
