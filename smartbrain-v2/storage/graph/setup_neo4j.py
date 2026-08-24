"""Apply the V1 Neo4j schema (constraints + indexes) to a running database.

Run as a CLI script:

.. code-block:: bash

    python -m src.models.setup_neo4j

The script is **idempotent**: every DDL statement uses ``IF NOT EXISTS``
so re-running it against a fully migrated database is a no-op. Each
operation is logged to stdout.

Configuration (Neo4j URI / credentials) is read from
:func:`src.config.settings.get_settings`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Final

from neo4j import AsyncGraphDatabase

from config.settings import get_settings
from storage.graph.schema import UNIQUE_CONSTRAINT_NAMES, EntityType

logger = logging.getLogger(__name__)


def _build_constraint_statements() -> list[tuple[str, str]]:
    """Return ``(name, cypher)`` pairs for every ``source_id`` uniqueness
    constraint (one per entity label)."""

    statements: list[tuple[str, str]] = []
    for label in EntityType:
        name = UNIQUE_CONSTRAINT_NAMES[label]
        cypher = (
            f"CREATE CONSTRAINT {name} IF NOT EXISTS "
            f"FOR (n:{label.value}) REQUIRE n.source_id IS UNIQUE"
        )
        statements.append((name, cypher))
    return statements


#: Standard single-property indexes required by the design doc.
INDEX_STATEMENTS: Final[list[tuple[str, str]]] = [
    (
        "service_name_idx",
        "CREATE INDEX service_name_idx IF NOT EXISTS FOR (n:Service) ON (n.name)",
    ),
    (
        "person_email_idx",
        "CREATE INDEX person_email_idx IF NOT EXISTS FOR (n:Person) ON (n.email)",
    ),
    (
        "ticket_status_idx",
        "CREATE INDEX ticket_status_idx IF NOT EXISTS FOR (n:Ticket) ON (n.status)",
    ),
]

#: Cross-label full-text index used by the search endpoint.
FULLTEXT_INDEX_NAME: Final[str] = "entity_search"
FULLTEXT_INDEX_STATEMENT: Final[str] = (
    f"CREATE FULLTEXT INDEX {FULLTEXT_INDEX_NAME} IF NOT EXISTS "
    "FOR (n:Service|Ticket|Epic|ConfluencePage) "
    "ON EACH [n.name, n.title, n.description, n.content_summary]"
)


async def apply_schema() -> None:
    """Connect to Neo4j using the configured settings and apply the schema.

    Runs every constraint and index creation exactly once per invocation.
    Each statement uses ``IF NOT EXISTS`` so the operation is safe to
    re-run against an already-migrated database.
    """

    settings = get_settings()
    logger.info("Connecting to Neo4j at %s as %s", settings.neo4j_uri, settings.neo4j_user)
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        async with driver.session() as session:
            for name, cypher in _build_constraint_statements():
                logger.info("Applying uniqueness constraint %s", name)
                await session.run(cypher)
            for name, cypher in INDEX_STATEMENTS:
                logger.info("Applying index %s", name)
                await session.run(cypher)
            logger.info("Applying full-text index %s", FULLTEXT_INDEX_NAME)
            await session.run(FULLTEXT_INDEX_STATEMENT)
        logger.info("Schema applied successfully")
    finally:
        await driver.close()


def main() -> None:
    """CLI entry point. Configures logging and runs :func:`apply_schema`."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(apply_schema())


if __name__ == "__main__":
    main()
