"""Backfill chunk vectors for existing steering document entities.

Iterates ConfluencePage entities in Neo4j whose source_id starts with
"steering:", re-chunks them through the V2 source-type-aware chunker,
embeds each chunk, runs dedup checks, writes VectorRecords (with
is_duplicate flag), indexes in BM25, and writes Chunk graph nodes +
HAS_CHUNK edges.

Honors the ``retrieval_mode`` setting:
  - "chunk" (default): backfill runs normally.
  - "document": logs and exits without processing.

Run with:
    python -m scripts.backfill_chunks [--steering-dir kiro_steering] [--verbose]

Requirements: 2.10, 2.11, 3.1, 5.4.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

from config.settings import get_settings
from processing.chunking.base import SourceDocument, get_chunker
from processing.chunking.models import SourceType
from processing.deduplication.dedup_service import DeduplicationService
from processing.embeddings.service import EmbeddingError, get_embedding_service
from processing.extraction.deterministic import (
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionResult,
    compute_text_hash,
)
from processing.extraction.writer import GraphWriter
from storage.graph.graph_store import GraphStore
from storage.graph.schema import EntityType, RelationshipType
from storage.vector.sparse_index import LocalBM25Index
from storage.vector.vector_store import VectorRecord, get_vector_store

logger = logging.getLogger(__name__)

# Steering file types (product, structure, tech)
_STEERING_FILE_TYPES = ("product", "structure", "tech")


async def run(steering_dir: Path, verbose: bool = False) -> None:
    """Backfill chunk vectors for existing steering entities."""

    settings = get_settings()
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Honor retrieval_mode: when "document", skip backfill.
    if settings.retrieval_mode != "chunk":
        logger.info(
            "retrieval_mode=%r (not 'chunk') — chunk backfill is disabled. "
            "Set RETRIEVAL_MODE=chunk to enable.",
            settings.retrieval_mode,
        )
        return

    logger.info("=" * 60)
    logger.info("Backfill Chunks: generating chunk vectors for steering docs")
    logger.info("=" * 60)
    logger.info("Steering directory: %s", steering_dir)

    # Connect to stores
    graph_store = GraphStore(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await graph_store.connect()

    vector_store = get_vector_store(settings)
    await vector_store.ensure_index()

    embedding_service = get_embedding_service(settings)
    dedup_service = DeduplicationService(
        vector_store=vector_store,
        graph_store=graph_store,
    )
    sparse_index = LocalBM25Index()

    start = time.time()

    # Step 1: Fetch existing steering entities from Neo4j
    logger.info("")
    logger.info("--- Step 1: Finding steering entities in Neo4j ---")

    query = """
    MATCH (p:ConfluencePage)
    WHERE p.source_id STARTS WITH 'steering:'
    RETURN p.source_id AS source_id, p.title AS title
    """
    async with graph_store._driver.session() as session:
        result = await session.run(query)
        nodes = await result.data()

    logger.info("Found %d steering entities in Neo4j", len(nodes))

    if not nodes:
        logger.info("No steering entities found. Nothing to do.")
        await _cleanup(graph_store, vector_store, embedding_service)
        return

    # Step 2: Process each entity — read file, chunk, embed, dedup, write
    logger.info("")
    logger.info("--- Step 2: Chunking + embedding + writing ---")

    chunker = get_chunker(SourceType.STEERING_FILE)
    total_chunks_created = 0
    total_duplicates = 0
    entities_processed = 0
    entities_skipped = 0

    for idx, node in enumerate(nodes, 1):
        source_id = node["source_id"]
        title = node.get("title", "")

        # Parse source_id: "steering:{repo_name}:{file_type}"
        parts = source_id.split(":")
        if len(parts) != 3:
            logger.warning(
                "[%d/%d] Skipping %s — unexpected source_id format",
                idx, len(nodes), source_id,
            )
            entities_skipped += 1
            continue

        _, repo_name, file_type = parts

        # Read the corresponding file from the steering directory
        md_file = steering_dir / repo_name / f"{file_type}.md"
        if not md_file.exists():
            logger.warning(
                "[%d/%d] Skipping %s — file not found: %s",
                idx, len(nodes), source_id, md_file,
            )
            entities_skipped += 1
            continue

        content = md_file.read_text(encoding="utf-8")
        if not content.strip():
            logger.debug(
                "[%d/%d] Skipping %s — file is empty",
                idx, len(nodes), source_id,
            )
            entities_skipped += 1
            continue

        logger.info("[%d/%d] Processing: %s", idx, len(nodes), source_id)

        # Build SourceDocument for chunking
        doc = SourceDocument(
            source_type=SourceType.STEERING_FILE,
            parent_source_id=source_id,
            repo_name=repo_name,
            source_ref=str(md_file),
            doc_type=file_type,
            text=content,
            title=f"{repo_name}/{file_type}",
        )

        # Chunk the document
        chunks = chunker.chunk(doc)
        logger.info("  Produced %d chunks", len(chunks))

        # Process each chunk: embed, dedup, write
        for chunk in chunks:
            try:
                # 1. Embed
                vector = await embedding_service.generate_embedding(
                    chunk.display_text
                )

                # 2. Dedup check
                decision = await dedup_service.check_duplicate(
                    new_chunk_id=chunk.chunk_id,
                    new_vector=vector,
                    new_doc_type=chunk.metadata.doc_type,
                    repo_name=chunk.metadata.repo_name,
                )

                is_duplicate = False
                if decision.is_duplicate and decision.duplicate_chunk_id == chunk.chunk_id:
                    is_duplicate = True
                    total_duplicates += 1
                    # Write DUPLICATE_OF edge (Req 5.4)
                    await dedup_service.mark_duplicate(
                        duplicate_chunk_id=decision.duplicate_chunk_id,
                        canonical_chunk_id=decision.canonical_chunk_id or "",
                    )

                # 3. Write to vector store (with is_duplicate flag)
                now = datetime.now(UTC).isoformat()
                record = VectorRecord(
                    source_id=chunk.chunk_id,
                    entity_type="Chunk",
                    text_hash=compute_text_hash(chunk.original_segment),
                    vector=vector,
                    created_at=now,
                    section_title=chunk.metadata.section_title,
                    repo_name=chunk.metadata.repo_name,
                    doc_type=chunk.metadata.doc_type,
                    parent_source_id=chunk.metadata.parent_source_id,
                    chunk_index=chunk.metadata.chunk_index,
                    source_ref=chunk.metadata.source_ref,
                    is_duplicate=is_duplicate,
                )
                await vector_store.upsert_embedding(record)

                # 4. Index in BM25 (Req 3.1)
                sparse_metadata = {
                    "repo_name": chunk.metadata.repo_name,
                    "doc_type": chunk.metadata.doc_type,
                    "section_title": chunk.metadata.section_title,
                    "parent_source_id": chunk.metadata.parent_source_id,
                }
                await sparse_index.index_chunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.display_text,
                    metadata=sparse_metadata,
                )

                # 5. Write Chunk node + HAS_CHUNK edge in graph
                chunk_entity = ExtractedEntity(
                    label=EntityType.CHUNK.value,
                    properties={
                        "source_id": chunk.chunk_id,
                        "parent_source_id": chunk.metadata.parent_source_id,
                        "chunk_index": chunk.metadata.chunk_index,
                        "doc_type": chunk.metadata.doc_type,
                        "created_at": now,
                        "updated_at": now,
                        "text_hash": compute_text_hash(chunk.original_segment),
                    },
                )
                has_chunk_rel = ExtractedRelationship(
                    source_label=EntityType.CONFLUENCE_PAGE.value,
                    source_id=chunk.metadata.parent_source_id,
                    target_label=EntityType.CHUNK.value,
                    target_id=chunk.chunk_id,
                    rel_type=RelationshipType.HAS_CHUNK.value,
                    properties={
                        "created_at": now,
                        "source": "deterministic",
                    },
                )
                # Write directly to graph store (bypass GraphWriter's
                # embedding logic since we already have the vector)
                await graph_store.upsert_entity(
                    label=chunk_entity.label,
                    source_id=chunk_entity.properties["source_id"],
                    properties=chunk_entity.properties,
                )
                try:
                    await graph_store.upsert_relationship(
                        source_id=has_chunk_rel.source_id,
                        source_label=has_chunk_rel.source_label,
                        target_id=has_chunk_rel.target_id,
                        target_label=has_chunk_rel.target_label,
                        rel_type=has_chunk_rel.rel_type,
                    )
                except Exception as rel_exc:
                    logger.debug(
                        "  Could not write HAS_CHUNK edge for %s: %s",
                        chunk.chunk_id, rel_exc,
                    )

                total_chunks_created += 1

            except EmbeddingError as exc:
                logger.warning("  Embedding failed for chunk %s: %s", chunk.chunk_id, exc)
            except Exception as exc:
                logger.warning(
                    "  Failed to process chunk %s: %s", chunk.chunk_id, exc
                )

        entities_processed += 1

    elapsed = time.time() - start

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Backfill Chunks Complete!")
    logger.info("  Steering entities found: %d", len(nodes))
    logger.info("  Entities processed: %d", entities_processed)
    logger.info("  Entities skipped: %d", entities_skipped)
    logger.info("  Total chunks created: %d", total_chunks_created)
    logger.info("  Duplicates marked: %d", total_duplicates)
    logger.info("  Time: %.1fs", elapsed)
    logger.info("=" * 60)

    await _cleanup(graph_store, vector_store, embedding_service)


async def _cleanup(graph_store: GraphStore, vector_store, embedding_service) -> None:
    """Close all store connections."""
    await graph_store.close()
    await vector_store.close()
    await embedding_service.close()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill chunk vectors for existing steering doc entities."
    )
    parser.add_argument(
        "--steering-dir",
        type=Path,
        default=Path("kiro_steering"),
        help="Path to the kiro_steering directory (default: kiro_steering)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    args = parser.parse_args()
    asyncio.run(run(steering_dir=args.steering_dir, verbose=args.verbose))


if __name__ == "__main__":
    main()
