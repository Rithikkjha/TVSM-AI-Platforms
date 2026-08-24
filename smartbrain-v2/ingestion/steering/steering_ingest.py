"""Ingest generated steering files + Level 1 key files into the graph.

Run with:
    python -m src.ingestion.steering_ingest

This script:
1. Reads all .md files from generated_steering/
2. For each, creates/updates a Document entity linked to the Service via DOCUMENTED_IN
3. Fetches Level 1 key files (README, package.json, Dockerfile) for each repo
4. Embeds the steering file + key files content for rich semantic search
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path

from config.mcp_registry import load_mcp_registry
from config.settings import get_settings
from processing.extraction.deterministic import (
    ExtractionResult,
    ExtractedEntity,
    ExtractedRelationship,
    compute_text_hash,
)
from processing.embeddings.service import get_embedding_service
from processing.extraction.writer import GraphWriter
from ingestion.clients.github_client import GitHubHTTPClient
from storage.graph.graph_store import GraphStore
from storage.graph.schema import EntityType, RelationshipType
from storage.vector.vector_store import get_vector_store

logger = logging.getLogger(__name__)

STEERING_DIR = Path("generated_steering")


def _build_steering_entity(repo_name: str, content: str) -> ExtractionResult:
    """Build a Document entity from a steering file and link it to the Service."""
    source_id = f"steering:{repo_name}"
    service_source_id = f"service:{repo_name}"
    text_hash = compute_text_hash(content)

    from datetime import UTC, datetime
    now = datetime.now(UTC).isoformat()

    entity = ExtractedEntity(
        label=EntityType.CONFLUENCE_PAGE.value,  # Reuse ConfluencePage for docs
        properties={
            "source_id": source_id,
            "title": f"Steering: {repo_name}",
            "space_key": "STEERING",
            "url": f"generated_steering/{repo_name}.md",
            # Store FULL steering content so GraphRAG can surface the rich
            # tech-stack / API / dependency sections to the LLM. Previous
            # impl truncated to 500 chars which chopped everything after
            # the "Service Overview" heading.
            "content_summary": content,
            "created_at": now,
            "updated_at": now,
            "text_hash": text_hash,
        },
    )

    # Link Service -> DOCUMENTED_IN -> this steering doc
    relationship = ExtractedRelationship(
        source_label=EntityType.SERVICE.value,
        source_id=service_source_id,
        target_label=EntityType.CONFLUENCE_PAGE.value,
        target_id=source_id,
        rel_type=RelationshipType.DOCUMENTED_IN.value,
        properties={"created_at": now},
    )

    return ExtractionResult(entities=[entity], relationships=[relationship])


def _build_key_files_entity(repo_name: str, key_files: dict[str, str]) -> ExtractionResult:
    """Build a Document entity from Level 1 key files content."""
    if not key_files:
        return ExtractionResult()

    # Combine all key files into one document
    combined = "\n\n".join(
        f"## {path}\n```\n{content}\n```"
        for path, content in key_files.items()
    )

    source_id = f"keyfiles:{repo_name}"
    service_source_id = f"service:{repo_name}"
    text_hash = compute_text_hash(combined)

    from datetime import UTC, datetime
    now = datetime.now(UTC).isoformat()

    entity = ExtractedEntity(
        label=EntityType.CONFLUENCE_PAGE.value,
        properties={
            "source_id": source_id,
            "title": f"Key Files: {repo_name}",
            "space_key": "KEY_FILES",
            "url": f"https://github.com/TVSM-CS/{repo_name}",
            # Store FULL key-files content (README / package.json / Dockerfile
            # etc.). A 500-char truncation silently discarded everything
            # after the first README header, neutering search relevance.
            "content_summary": combined,
            "created_at": now,
            "updated_at": now,
            "text_hash": text_hash,
        },
    )

    relationship = ExtractedRelationship(
        source_label=EntityType.SERVICE.value,
        source_id=service_source_id,
        target_label=EntityType.CONFLUENCE_PAGE.value,
        target_id=source_id,
        rel_type=RelationshipType.DOCUMENTED_IN.value,
        properties={"created_at": now},
    )

    return ExtractionResult(entities=[entity], relationships=[relationship])


async def run() -> None:
    """Ingest steering files + Level 1 key files."""
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    logger.info("=" * 60)
    logger.info("Engineering Memory Graph — Steering + Level 1 Ingestion")
    logger.info("=" * 60)

    # Load config
    registry = load_mcp_registry(settings.mcp_servers_config_path)
    github_config = next((s for s in registry.servers if s.name == "github"), None)

    # Build write pipeline
    graph_store = GraphStore(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await graph_store.connect()
    vector_store = get_vector_store(settings)
    await vector_store.ensure_index()
    embedding_service = get_embedding_service(settings)
    writer = GraphWriter(graph_store, vector_store, embedding_service)

    start = time.time()
    total_created = 0
    total_updated = 0

    # Step 1: Ingest steering files
    logger.info("")
    logger.info("--- Step 1: Ingesting steering files from %s ---", STEERING_DIR)
    steering_files = sorted(STEERING_DIR.glob("*.md"))
    logger.info("Found %d steering files", len(steering_files))

    for idx, filepath in enumerate(steering_files, 1):
        repo_name = filepath.stem
        content = filepath.read_text(encoding="utf-8")
        logger.info("[%d/%d] Ingesting steering: %s", idx, len(steering_files), repo_name)

        result = _build_steering_entity(repo_name, content)
        write_result = await writer.write(result)
        total_created += write_result.created_count
        total_updated += write_result.updated_count

    # Step 2: Fetch and ingest Level 1 key files
    if github_config:
        logger.info("")
        logger.info("--- Step 2: Fetching Level 1 key files from GitHub ---")
        token = settings.github_token
        org = github_config.config.get("org", "")
        repos = github_config.config.get("repos", [])

        github_client = GitHubHTTPClient(token=token, org=org, repos=repos)

        for idx, repo_name in enumerate(repos, 1):
            logger.info("[%d/%d] Fetching key files: %s", idx, len(repos), repo_name)
            try:
                key_files = await github_client.get_key_files(repo_name)
                if key_files:
                    result = _build_key_files_entity(repo_name, key_files)
                    write_result = await writer.write(result)
                    total_created += write_result.created_count
                    total_updated += write_result.updated_count
                    logger.info("  Found %d key files", len(key_files))
                else:
                    logger.info("  No key files found")
            except Exception as exc:
                logger.warning("  Failed: %s", exc)

        await github_client.close()

    elapsed = time.time() - start

    logger.info("")
    logger.info("=" * 60)
    logger.info("Steering + Level 1 Ingestion Complete!")
    logger.info("  Created: %d entities", total_created)
    logger.info("  Updated: %d entities", total_updated)
    logger.info("  Time: %.1fs", elapsed)
    logger.info("=" * 60)

    await writer.close()


def main() -> None:
    """CLI entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
