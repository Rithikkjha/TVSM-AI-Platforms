"""get_impact tool — blast radius / dependency impact analysis.

Finds all services that depend on the queried service (incoming DEPENDS_ON)
up to 2 hops, along with any epics and tickets linked to those affected services.

Use cases:
- "What breaks if tvsm-auth goes down?"
- "What's the blast radius of notification-service?"
- "Show me the impact of changing Payment-Service"
"""

from __future__ import annotations

from typing import Any

from neo4j import AsyncGraphDatabase

from config.settings import get_settings
from retrieval.search import graph_queries


async def get_impact(name: str) -> dict[str, Any]:
    """Get the blast radius / impact analysis for a service.

    Traverses incoming DEPENDS_ON edges up to 2 hops to find all
    services that would be affected if this service goes down or changes.

    Args:
        name: Service name (e.g. "tvsm-auth", "Payment-Service").

    Returns:
        Dict with affected services (with hop distance), linked epics, and tickets.
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

        # BFS traversal of incoming DEPENDS_ON up to 2 hops
        impact_data = await graph_queries.get_impact_graph(driver, source_id, max_hops=2)

        affected_services = [
            {
                "source_id": s["source_id"],
                "name": s["name"],
                "hops": s["hops"],
            }
            for s in impact_data["affected_services"]
        ]

        linked_epics = [
            {
                "source_id": e.get("source_id", ""),
                "key": e.get("key"),
                "title": e.get("title"),
                "status": e.get("status"),
            }
            for e in impact_data["linked_epics"]
        ]

        linked_tickets = [
            {
                "source_id": t.get("source_id", ""),
                "key": t.get("key"),
                "title": t.get("title"),
                "status": t.get("status"),
                "priority": t.get("priority"),
            }
            for t in impact_data["linked_tickets"]
        ]

        return {
            "service": name,
            "max_hops": 2,
            "affected_services": affected_services,
            "linked_epics": linked_epics,
            "linked_tickets": linked_tickets,
        }

    finally:
        await driver.close()
