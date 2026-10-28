"""Neo4j constraints and indexes for the Phase 8 graph (idempotent)."""

from __future__ import annotations

from typing import Any

from ingestion.repo_docs_ingest.common import REPO_DOCS_LABELS, run_cypher

#: Labels that get ``source_id IS UNIQUE``: everything repo_docs writes plus the
#: pre-existing Jira/Confluence/chunk labels (so labelled source_id lookups are indexed).
CONSTRAINT_LABELS: tuple[str, ...] = (*REPO_DOCS_LABELS, "Chunk", "Ticket", "ConfluencePage")

#: Extra lookup indexes ``(label, property)``.
EXTRA_INDEXES: tuple[tuple[str, str], ...] = (
    ("Service", "name"),
    ("Topic", "name"),
    ("Endpoint", "path"),
)


def constraint_statements() -> list[str]:
    stmts = [
        f"CREATE CONSTRAINT {label.lower()}_source_id_unique IF NOT EXISTS "
        f"FOR (n:{label}) REQUIRE n.source_id IS UNIQUE"
        for label in CONSTRAINT_LABELS
    ]
    stmts += [
        f"CREATE INDEX {label.lower()}_{prop}_idx IF NOT EXISTS FOR (n:{label}) ON (n.{prop})"
        for label, prop in EXTRA_INDEXES
    ]
    return stmts


async def ensure_schema(driver: Any) -> list[dict[str, Any]]:
    """Create all constraints/indexes, wait for them, return ``SHOW CONSTRAINTS``."""

    async with driver.session() as session:
        for stmt in constraint_statements():
            await run_cypher(session, stmt)
        await run_cypher(session, "CALL db.awaitIndexes(300)")
        return await run_cypher(
            session,
            "SHOW CONSTRAINTS YIELD name, labelsOrTypes, properties "
            "RETURN name, labelsOrTypes, properties ORDER BY name",
        )
