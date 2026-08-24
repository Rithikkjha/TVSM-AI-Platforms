"""Backfill missing vector embeddings for steering nodes.

Run with:
    python -m src.ingestion.backfill_embeddings

This script finds all ConfluencePage nodes with space_key='STEERING' in Neo4j,
checks if they have a corresponding vector in Qdrant, and generates embeddings
for any that are missing.

Use this after a failed embedding run (e.g., Azure OpenAI was unreachable).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time

from config.settings import get_settings
from processing.embeddings.service import EmbeddingError, get_embedding_service
from storage.graph.graph_store import GraphStore
from storage.vector.vector_store import QdrantVectorStore, VectorRecord, get_vector_store

logger = logging.getLogger(__name__)


async def run() -> None:
    """Find steering nodes missing embeddings and generate them."""
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    logger.info("=" * 60)
    logger.info("Backfill: Generating missing embeddings for steering nodes")
    logger.info("=" * 60)

    # Connect
    graph_store = GraphStore(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await graph_store.connect()
    vector_store = get_vector_store(settings)
    await vector_store.ensure_index()
    embedding_service = get_embedding_service(settings)

    start = time.time()

    # Step 1: Get all steering nodes from Neo4j
    logger.info("")
    logger.info("--- Step 1: Finding steering nodes in Neo4j ---")

    query = """
    MATCH (p:ConfluencePage)
    WHERE p.space_key = 'STEERING'
    RETURN p.source_id AS source_id, p.title AS title, 
           p.content_summary AS content, p.text_hash AS text_hash,
           p.updated_at AS updated_at
    """
    async with graph_store._driver.session() as session:
        result = await session.run(query)
        nodes = await result.data()

    logger.info("Found %d steering nodes in Neo4j", len(nodes))

    # Step 2: Check which ones are missing from Qdrant
    logger.info("")
    logger.info("--- Step 2: Checking for missing embeddings ---")

    missing = []
    for node in nodes:
        source_id = node["source_id"]
        # Check if vector exists by trying to look it up
        # We'll use the point ID derivation from QdrantVectorStore
        point_id = QdrantVectorStore._point_id_for(source_id)

        # Try to retrieve the point
        if isinstance(vector_store, QdrantVectorStore):
            import httpx
            try:
                resp = await vector_store._client.request(
                    "POST",
                    f"/collections/{vector_store._collection_name}/points",
                    json={"ids": [point_id], "with_payload": True, "with_vector": False},
                )
                data = resp.json()
                points = data.get("result", [])
                if not points:
                    missing.append(node)
            except Exception:
                missing.append(node)
        else:
            # For Azure AI Search, just try to embed everything
            missing.append(node)

    logger.info("Missing embeddings: %d / %d", len(missing), len(nodes))

    if not missing:
        logger.info("All embeddings are present! Nothing to do.")
        await graph_store.close()
        await vector_store.close()
        await embedding_service.close()
        return

    # Step 3: Generate and store embeddings
    logger.info("")
    logger.info("--- Step 3: Generating embeddings ---")

    success_count = 0
    fail_count = 0

    for idx, node in enumerate(missing, 1):
        source_id = node["source_id"]
        title = node["title"]
        content = node.get("content", "") or ""
        text_hash = node.get("text_hash", "")
        updated_at = node.get("updated_at", "") or ""

        # Build text for embedding (same logic as writer._extract_text_for_embedding)
        text = f"{title} STEERING {content}".strip()

        logger.info("[%d/%d] Embedding: %s", idx, len(missing), source_id)

        try:
            vector = await embedding_service.generate_embedding(text)

            # Convert updated_at to string if it's a Neo4j DateTime object
            created_at_str = str(updated_at) if updated_at else "2026-05-20T00:00:00Z"

            record = VectorRecord(
                source_id=source_id,
                entity_type="ConfluencePage",
                text_hash=text_hash,
                vector=vector,
                created_at=created_at_str,
            )
            await vector_store.upsert_embedding(record)
            success_count += 1

        except EmbeddingError as exc:
            logger.warning("  Failed: %s", exc)
            fail_count += 1
        except Exception as exc:
            logger.warning("  Failed: %s", exc)
            fail_count += 1

    elapsed = time.time() - start

    logger.info("")
    logger.info("=" * 60)
    logger.info("Backfill Complete!")
    logger.info("  Total missing: %d", len(missing))
    logger.info("  Successfully embedded: %d", success_count)
    logger.info("  Failed: %d", fail_count)
    logger.info("  Time: %.1fs", elapsed)
    logger.info("=" * 60)

    await graph_store.close()
    await vector_store.close()
    await embedding_service.close()


def main() -> None:
    """CLI entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
