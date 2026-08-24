"""Ingest Kiro-generated steering files (3 per repo) into the graph.

Run with:
    python -m src.ingestion.kiro_steering_ingest
    python -m src.ingestion.kiro_steering_ingest --input kiro_steering
    python -m src.ingestion.kiro_steering_ingest --input kiro_steering --skip-key-files

This script:
1. Reads kiro_steering/{repo-name}/product.md, structure.md, tech.md
2. For each file, creates a Document entity linked to the Service via DOCUMENTED_IN
3. Each file gets its own vector embedding for precise semantic search
4. Optionally fetches Level 1 key files from GitHub (same as old steering_ingest)

Folder structure expected:
    kiro_steering/
    ├── booking-crud-services/
    │   ├── product.md
    │   ├── structure.md
    │   └── tech.md
    ├── tvsm-auth/
    │   ├── product.md
    │   ├── structure.md
    │   └── tech.md
    └── ...
"""

from __future__ import annotations

import asyncio
import logging
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

KIRO_STEERING_DIR = Path("kiro_steering")

# The 3 steering file types Kiro generates
STEERING_FILE_TYPES = ["product", "structure", "tech"]


def _build_kiro_steering_entity(
    repo_name: str,
    file_type: str,
    content: str,
) -> ExtractionResult:
    """Build a Document entity from a single Kiro steering file.

    Creates a node with source_id like "steering:booking-crud-services:product"
    and links it to the Service node via DOCUMENTED_IN.
    """
    source_id = f"steering:{repo_name}:{file_type}"
    service_source_id = f"service:{repo_name}"
    text_hash = compute_text_hash(content)

    from datetime import UTC, datetime
    now = datetime.now(UTC).isoformat()

    # Human-friendly titles
    title_map = {
        "product": f"Product Context: {repo_name}",
        "structure": f"Code Structure: {repo_name}",
        "tech": f"Tech Stack: {repo_name}",
    }
    title = title_map.get(file_type, f"Steering ({file_type}): {repo_name}")

    entity = ExtractedEntity(
        label=EntityType.CONFLUENCE_PAGE.value,
        properties={
            "source_id": source_id,
            "title": title,
            "space_key": "STEERING",
            "url": f"kiro_steering/{repo_name}/{file_type}.md",
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
    """Ingest Kiro steering files (3 per repo) + optional Level 1 key files."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest Kiro-generated steering files")
    parser.add_argument(
        "--input",
        default=str(KIRO_STEERING_DIR),
        help="Directory containing repo folders with steering files (default: kiro_steering/)",
    )
    parser.add_argument(
        "--skip-key-files",
        action="store_true",
        help="Skip fetching Level 1 key files from GitHub",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    input_dir = Path(args.input)

    logger.info("=" * 60)
    logger.info("Engineering Memory Graph — Kiro Steering Ingestion (3-file)")
    logger.info("=" * 60)

    if not input_dir.exists():
        logger.error("Input directory does not exist: %s", input_dir)
        return

    # Find all repo folders (folders that contain at least one .md file)
    repo_dirs = sorted([
        d for d in input_dir.iterdir()
        if d.is_dir() and any(d.glob("*.md"))
    ])

    if not repo_dirs:
        logger.error("No repo folders with .md files found in %s", input_dir)
        return

    logger.info("Found %d repos with steering files in %s", len(repo_dirs), input_dir)

    # Load config for key files
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
    total_skipped = 0
    files_ingested = 0

    # Step 1: Ingest Kiro steering files (3 per repo)
    logger.info("")
    logger.info("--- Step 1: Ingesting Kiro steering files ---")

    for idx, repo_dir in enumerate(repo_dirs, 1):
        repo_name = repo_dir.name
        logger.info("[%d/%d] Processing: %s", idx, len(repo_dirs), repo_name)

        md_files = sorted(repo_dir.glob("*.md"))
        for md_file in md_files:
            file_type = md_file.stem  # "product", "structure", "tech", or other
            content = md_file.read_text(encoding="utf-8")

            if not content.strip():
                logger.info("  ⏭️  %s.md — empty, skipping", file_type)
                total_skipped += 1
                continue

            result = _build_kiro_steering_entity(repo_name, file_type, content)
            write_result = await writer.write(result)
            total_created += write_result.created_count
            total_updated += write_result.updated_count
            files_ingested += 1
            logger.info("  ✅ %s.md — ingested", file_type)

    # Step 2: Fetch and ingest Level 1 key files (optional)
    if not args.skip_key_files and github_config:
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
    elif args.skip_key_files:
        logger.info("")
        logger.info("--- Step 2: Skipped (--skip-key-files) ---")

    elapsed = time.time() - start

    logger.info("")
    logger.info("=" * 60)
    logger.info("Kiro Steering Ingestion Complete!")
    logger.info("  Repos processed: %d", len(repo_dirs))
    logger.info("  Files ingested: %d", files_ingested)
    logger.info("  Nodes created: %d", total_created)
    logger.info("  Nodes updated: %d", total_updated)
    logger.info("  Files skipped (empty): %d", total_skipped)
    logger.info("  Time: %.1fs", elapsed)
    logger.info("=" * 60)

    await writer.close()


def main() -> None:
    """CLI entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
