"""Direct Cypher query functions for the Query API read path.

This module provides async functions that run Cypher queries directly
against the Neo4j async driver. It bypasses the write-focused GraphStore
to keep the read path simple and fast (Requirement 3.5: P95 < 500ms).

All queries exclude soft-deleted entities (WHERE n.deleted_at IS NULL).
"""

from __future__ import annotations

from typing import Any

from neo4j import AsyncDriver


async def get_service_by_name(driver: AsyncDriver, name: str) -> dict[str, Any] | None:
    """Find a Service node by its name property.

    Args:
        driver: The Neo4j async driver instance.
        name: The service name to look up.

    Returns:
        A dict of the service node's properties, or None if not found.
    """
    cypher = (
        "MATCH (n:Service {name: $name}) "
        "WHERE n.deleted_at IS NULL "
        "RETURN properties(n) AS props"
    )
    async with driver.session() as session:
        result = await session.run(cypher, name=name)
        record = await result.single()

    if record is None:
        return None
    return dict(record["props"])


async def get_service_owners(driver: AsyncDriver, service_source_id: str) -> list[dict[str, Any]]:
    """Fetch teams that own a service via OWNED_BY relationship.

    Args:
        driver: The Neo4j async driver instance.
        service_source_id: The source_id of the service.

    Returns:
        A list of dicts with team properties.
    """
    cypher = (
        "MATCH (s:Service {source_id: $sid})-[:OWNED_BY]->(t:Team) "
        "WHERE t.deleted_at IS NULL AND s.deleted_at IS NULL "
        "RETURN properties(t) AS props"
    )
    async with driver.session() as session:
        result = await session.run(cypher, sid=service_source_id)
        records = [record async for record in result]

    return [dict(record["props"]) for record in records]


async def get_service_dependencies(
    driver: AsyncDriver, service_source_id: str, direction: str
) -> list[dict[str, Any]]:
    """Fetch services connected via DEPENDS_ON relationships.

    Args:
        driver: The Neo4j async driver instance.
        service_source_id: The source_id of the service.
        direction: "upstream" for outgoing DEPENDS_ON (services this depends on),
                   "downstream" for incoming DEPENDS_ON (services that depend on this).

    Returns:
        A list of dicts with neighbor service properties and relationship properties.
    """
    if direction == "upstream":
        cypher = (
            "MATCH (s:Service {source_id: $sid})-[r:DEPENDS_ON]->(t:Service) "
            "WHERE t.deleted_at IS NULL AND s.deleted_at IS NULL "
            "RETURN properties(t) AS props, properties(r) AS rel_props"
        )
    else:
        cypher = (
            "MATCH (t:Service)-[r:DEPENDS_ON]->(s:Service {source_id: $sid}) "
            "WHERE t.deleted_at IS NULL AND s.deleted_at IS NULL "
            "RETURN properties(t) AS props, properties(r) AS rel_props"
        )

    async with driver.session() as session:
        result = await session.run(cypher, sid=service_source_id)
        records = [record async for record in result]

    return [
        {**dict(record["props"]), "rel_props": dict(record["rel_props"])}
        for record in records
    ]


async def get_service_tickets(
    driver: AsyncDriver, service_source_id: str
) -> list[dict[str, Any]]:
    """Fetch tickets linked to a service via LINKED_TO (incoming from Ticket).

    Args:
        driver: The Neo4j async driver instance.
        service_source_id: The source_id of the service.

    Returns:
        A list of dicts with ticket properties.
    """
    cypher = (
        "MATCH (t:Ticket)-[:LINKED_TO]->(s:Service {source_id: $sid}) "
        "WHERE t.deleted_at IS NULL AND s.deleted_at IS NULL "
        "RETURN properties(t) AS props"
    )
    async with driver.session() as session:
        result = await session.run(cypher, sid=service_source_id)
        records = [record async for record in result]

    return [dict(record["props"]) for record in records]


async def get_service_documents(
    driver: AsyncDriver, service_source_id: str
) -> list[dict[str, Any]]:
    """Fetch Confluence pages linked via DOCUMENTED_IN (outgoing from Service).

    Args:
        driver: The Neo4j async driver instance.
        service_source_id: The source_id of the service.

    Returns:
        A list of dicts with ConfluencePage properties.
    """
    cypher = (
        "MATCH (s:Service {source_id: $sid})-[:DOCUMENTED_IN]->(d:ConfluencePage) "
        "WHERE d.deleted_at IS NULL AND s.deleted_at IS NULL "
        "RETURN properties(d) AS props"
    )
    async with driver.session() as session:
        result = await session.run(cypher, sid=service_source_id)
        records = [record async for record in result]

    return [dict(record["props"]) for record in records]


async def get_entity_neighborhood(
    driver: AsyncDriver, source_id: str, hops: int = 2
) -> list[dict[str, Any]]:
    """Get all entities within N hops of the given entity.

    Uses variable-length path matching to find all connected entities
    within the specified hop distance. Excludes soft-deleted entities.

    Args:
        driver: The Neo4j async driver instance.
        source_id: The source_id of the starting entity.
        hops: Maximum number of hops to traverse (default 2).

    Returns:
        A list of dicts with entity properties for each neighbor found.
    """
    cypher = (
        "MATCH (n {source_id: $sid})-[*1.."
        + str(hops)
        + "]-(m) "
        "WHERE m.deleted_at IS NULL AND n.deleted_at IS NULL "
        "RETURN DISTINCT properties(m) AS props"
    )
    async with driver.session() as session:
        result = await session.run(cypher, sid=source_id)
        records = [record async for record in result]

    return [dict(record["props"]) for record in records]


async def get_impact_graph(
    driver: AsyncDriver, service_source_id: str, max_hops: int = 2
) -> dict[str, Any]:
    """BFS traversal of incoming DEPENDS_ON up to max_hops.

    Finds all services that transitively depend on the given service
    (i.e., services that would be affected by changes to this service).

    Args:
        driver: The Neo4j async driver instance.
        service_source_id: The source_id of the root service.
        max_hops: Maximum traversal depth (default 2).

    Returns:
        {
            "affected_services": [{"source_id": ..., "name": ..., "hops": 1}, ...],
            "linked_epics": [{"source_id": ..., "key": ..., "title": ..., "status": ...}, ...],
            "linked_tickets": [{"source_id": ..., "key": ..., "title": ..., "status": ...}, ...]
        }
    """
    # Query 1: Get all affected services with their hop distance
    affected_cypher = (
        "MATCH path = (s:Service {source_id: $sid})<-[:DEPENDS_ON*1.."
        + str(max_hops)
        + "]-(t:Service) "
        "WHERE t.deleted_at IS NULL AND s.deleted_at IS NULL "
        "WITH t, min(length(path)) AS hops "
        "RETURN properties(t) AS props, hops"
    )

    async with driver.session() as session:
        result = await session.run(affected_cypher, sid=service_source_id)
        affected_records = [record async for record in result]

    affected_services = [
        {
            "source_id": dict(record["props"]).get("source_id", ""),
            "name": dict(record["props"]).get("name", ""),
            "hops": record["hops"],
        }
        for record in affected_records
    ]

    # Collect source_ids of affected services for linked entity lookup
    affected_sids = [s["source_id"] for s in affected_services]

    if not affected_sids:
        return {
            "affected_services": [],
            "linked_epics": [],
            "linked_tickets": [],
        }

    # Query 2: Get epics linked to any affected service
    epics_cypher = (
        "MATCH (e:Epic)-[:LINKED_TO]->(s:Service) "
        "WHERE s.source_id IN $sids AND e.deleted_at IS NULL AND s.deleted_at IS NULL "
        "RETURN DISTINCT properties(e) AS props"
    )

    # Query 3: Get tickets linked to any affected service
    tickets_cypher = (
        "MATCH (t:Ticket)-[:LINKED_TO]->(s:Service) "
        "WHERE s.source_id IN $sids AND t.deleted_at IS NULL AND s.deleted_at IS NULL "
        "RETURN DISTINCT properties(t) AS props"
    )

    async with driver.session() as session:
        epics_result = await session.run(epics_cypher, sids=affected_sids)
        epic_records = [record async for record in epics_result]

    async with driver.session() as session:
        tickets_result = await session.run(tickets_cypher, sids=affected_sids)
        ticket_records = [record async for record in tickets_result]

    linked_epics = [dict(record["props"]) for record in epic_records]
    linked_tickets = [dict(record["props"]) for record in ticket_records]

    return {
        "affected_services": affected_services,
        "linked_epics": linked_epics,
        "linked_tickets": linked_tickets,
    }


async def find_confluence_pages_by_keyword(
    driver: AsyncDriver, keyword: str, limit: int = 5
) -> list[dict[str, Any]]:
    """Find Confluence pages whose title contains the keyword.

    This is a fallback for when no formal DOCUMENTED_IN edge exists
    between a service and its documentation. It uses the full-text
    index to find pages that mention the service name.

    Args:
        driver: The Neo4j async driver instance.
        keyword: The search term (typically a service name).
        limit: Maximum number of pages to return.

    Returns:
        A list of dicts with ConfluencePage properties.
    """
    # Use full-text index for fuzzy matching
    cypher = (
        "CALL db.index.fulltext.queryNodes('entity_search', $keyword) "
        "YIELD node, score "
        "WHERE 'ConfluencePage' IN labels(node) AND node.deleted_at IS NULL "
        "RETURN properties(node) AS props, score "
        "ORDER BY score DESC "
        "LIMIT $limit"
    )
    async with driver.session() as session:
        result = await session.run(cypher, keyword=keyword, limit=limit)
        records = [record async for record in result]

    return [dict(record["props"]) for record in records]
