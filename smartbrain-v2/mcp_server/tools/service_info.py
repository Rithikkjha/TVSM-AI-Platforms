"""get_service_info tool — detailed service information from the knowledge graph.

Fetches a service node by name and returns all related entities:
owners, dependencies (upstream/downstream), linked tickets, and documents.

Use cases:
- "Tell me about booking-crud-services"
- "Who owns the notification-service?"
- "What are the dependencies of tvsm-auth?"
"""

from __future__ import annotations

from typing import Any

from neo4j import AsyncGraphDatabase

from config.settings import get_settings
from retrieval.search import graph_queries
from retrieval.search.freshness import check_staleness


async def get_service_info(name: str) -> dict[str, Any]:
    """Get detailed information about a service from the knowledge graph.

    Args:
        name: Service name (e.g. "booking-crud-services", "tvsm-auth").

    Returns:
        Dict with service properties, owners, dependencies, tickets, and documents.
        Returns error dict if service not found.
    """
    if not name or not name.strip():
        return {"error": "Service name must not be empty"}

    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    try:
        service = await graph_queries.get_service_by_name(driver, name)

        if service is None:
            return {
                "error": "not_found",
                "message": f"Service '{name}' not found in graph",
            }

        source_id = service.get("source_id", "")

        # Fetch all related entities
        owners_raw = await graph_queries.get_service_owners(driver, source_id)
        upstream_raw = await graph_queries.get_service_dependencies(driver, source_id, "upstream")
        downstream_raw = await graph_queries.get_service_dependencies(driver, source_id, "downstream")
        tickets_raw = await graph_queries.get_service_tickets(driver, source_id)
        documents_raw = await graph_queries.get_service_documents(driver, source_id)

        # Build response
        owners = [{"source_id": o.get("source_id", ""), "name": o.get("name")} for o in owners_raw]

        upstream = [
            {
                "source_id": d.get("source_id", ""),
                "name": d.get("name"),
                "dependency_type": d.get("rel_props", {}).get("dependency_type"),
            }
            for d in upstream_raw
        ]

        downstream = [
            {
                "source_id": d.get("source_id", ""),
                "name": d.get("name"),
                "dependency_type": d.get("rel_props", {}).get("dependency_type"),
            }
            for d in downstream_raw
        ]

        tickets = [
            {
                "source_id": t.get("source_id", ""),
                "key": t.get("key"),
                "title": t.get("title"),
                "status": t.get("status"),
                "priority": t.get("priority"),
            }
            for t in tickets_raw
        ]

        documents = [
            {
                "source_id": d.get("source_id", ""),
                "title": d.get("title"),
                "url": d.get("url"),
            }
            for d in documents_raw
        ]

        staleness = check_staleness(service.get("updated_at"))

        return {
            "service": service,
            "owners": owners,
            "upstream_dependencies": upstream,
            "downstream_dependents": downstream,
            "linked_tickets": tickets,
            "documents": documents,
            "staleness": staleness,
        }

    finally:
        await driver.close()
