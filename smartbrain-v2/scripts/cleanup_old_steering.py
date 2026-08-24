"""Clean up old steering nodes from Neo4j and Qdrant.

Run with:
    python -m src.ingestion.cleanup_old_steering

This script removes the old single-file steering nodes (source_id pattern: "steering:{repo}")
and their vector embeddings, making way for the new 3-file-per-repo Kiro steering ingestion.

It does NOT touch:
- Confluence pages (space_key != "STEERING")
- Key files nodes (source_id pattern: "keyfiles:{repo}")
- Jira / GitHub data
"""

from __future__ import annotations

import asyncio
import logging
import time

from config.settings import get_settings
from storage.graph.graph_store import GraphStore
from storage.vector.vector_store import get_vector_store

logger = logging.getLogger(__name__)


async def run() -> None:
    """Remove old steering nodes from Neo4j and Qdrant."""
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    logger.info("=" * 60)
    logger.info("Cleanup: Removing old single-file steering nodes")
    logger.info("=" * 60)

    # Connect to stores
    graph_store = GraphStore(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await graph_store.connect()
    vector_store = get_vector_store(settings)

    start = time.time()

    # Step 1: Find all old steering nodes in Neo4j
    logger.info("")
    logger.info("--- Step 1: Finding old steering nodes in Neo4j ---")

    query = """
    MATCH (p:ConfluencePage)
    WHERE p.space_key = 'STEERING'
    RETURN p.source_id AS source_id, p.title AS title
    """
    async with graph_store._driver.session() as session:
        result = await session.run(query)
        old_nodes = await result.data()

    logger.info("Found %d old steering nodes", len(old_nodes))

    if not old_nodes:
        logger.info("Nothing to clean up!")
        await graph_store.close()
        await vector_store.close()
        return

    # Step 2: Delete from Neo4j (hard delete — these are being replaced)
    logger.info("")
    logger.info("--- Step 2: Deleting from Neo4j ---")

    delete_query = """
    MATCH (p:ConfluencePage)
    WHERE p.space_key = 'STEERING'
    DETACH DELETE p
    """
    async with graph_store._driver.session() as session:
        result = await session.run(delete_query)
        summary = await result.consume()
        logger.info("Deleted %d nodes from Neo4j", summary.counters.nodes_deleted)

    # Step 3: Delete from Qdrant
    logger.info("")
    logger.info("--- Step 3: Deleting vectors from Qdrant ---")

    deleted_vectors = 0
    for node in old_nodes:
        source_id = node["source_id"]
        try:
            await vector_store.delete_embedding(source_id)
            deleted_vectors += 1
            logger.debug("  Deleted vector: %s", source_id)
        except Exception as exc:
            logger.warning("  Failed to delete vector %s: %s", source_id, exc)

    elapsed = time.time() - start

    logger.info("")
    logger.info("=" * 60)
    logger.info("Cleanup Complete!")
    logger.info("  Neo4j nodes deleted: %d", len(old_nodes))
    logger.info("  Qdrant vectors deleted: %d", deleted_vectors)
    logger.info("  Time: %.1fs", elapsed)
    logger.info("=" * 60)

    await graph_store.close()
    await vector_store.close()


def main() -> None:
    """CLI entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
