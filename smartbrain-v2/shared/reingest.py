"""Shared re-ingestion utility for the Automated Steering Pipeline.

Both the webhook pipeline and the metadata scanner call this module to
re-ingest specific steering files into the Engineering Memory Graph after
they've been written to disk.

The utility is idempotent: files whose ``text_hash`` matches the existing
graph record are skipped by the underlying :class:`GraphWriter`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from config.settings import get_settings
from ingestion.steering.kiro_steering_ingest import _build_kiro_steering_entity
from processing.embeddings.service import get_embedding_service
from processing.extraction.writer import GraphWriter
from storage.graph.graph_store import GraphStore
from storage.vector.vector_store import get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class ReingestResult:
    """Summary of a re-ingestion run for a single repository."""

    repo_name: str
    files_processed: int = 0
    files_skipped: int = 0
    chunks_created: int = 0
    error: str | None = None


async def _create_writer() -> GraphWriter:
    """Construct a :class:`GraphWriter` from application settings."""
    settings = get_settings()
    graph_store = GraphStore(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await graph_store.connect()
    vector_store = get_vector_store(settings)
    await vector_store.ensure_index()
    embedding_service = get_embedding_service(settings)
    return GraphWriter(graph_store, vector_store, embedding_service)


async def trigger_reingest(
    repo_name: str,
    file_types: list[str],
    steering_dir: Path | None = None,
) -> ReingestResult:
    """Re-ingest specific steering files for a repo into the knowledge graph.

    Idempotent: skips files whose text_hash matches the existing graph hash.
    Calls into the V2 clean-ingest infrastructure (GraphWriter + embeddings).

    Args:
        repo_name: Name of the repository (e.g., "booking-crud-services").
        file_types: List of file types to re-ingest (e.g., ["product", "tech"]).
        steering_dir: Override for the kiro_steering directory path.

    Returns:
        A :class:`ReingestResult` summarizing the operation.
    """
    settings = get_settings()
    base_dir = steering_dir or Path(settings.kiro_steering_dir)
    repo_dir = base_dir / repo_name

    writer = await _create_writer()

    files_processed = 0
    files_skipped = 0
    chunks_created = 0

    try:
        for file_type in file_types:
            md_file = repo_dir / f"{file_type}.md"
            if not md_file.exists():
                files_skipped += 1
                continue

            content = md_file.read_text(encoding="utf-8")
            if not content.strip():
                files_skipped += 1
                continue

            # Build entity + relationship extraction result
            result = _build_kiro_steering_entity(repo_name, file_type, content)

            # Write via GraphWriter (handles text_hash dedup internally)
            write_result = await writer.write(result)
            if write_result.updated_count == 0 and write_result.created_count == 0:
                files_skipped += 1
            else:
                files_processed += 1
                chunks_created += write_result.created_count

        return ReingestResult(
            repo_name=repo_name,
            files_processed=files_processed,
            files_skipped=files_skipped,
            chunks_created=chunks_created,
        )
    except Exception as exc:
        logger.exception("Re-ingestion failed for %s", repo_name)
        return ReingestResult(
            repo_name=repo_name,
            files_processed=files_processed,
            files_skipped=files_skipped,
            chunks_created=chunks_created,
            error=str(exc),
        )
    finally:
        await writer.close()


__all__ = [
    "ReingestResult",
    "trigger_reingest",
]
