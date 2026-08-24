"""Steering auto-updater — detects meaningful PR changes and patches steering files.

This module handles the full pipeline:
1. FILTER — Is this PR meaningful enough to update knowledge?
2. CLASSIFY — Which steering file(s) are affected? (product/structure/tech)
3. PATCH — Update only the affected parts of existing steering
4. SAVE — Write updated file to kiro_steering/{repo}/
5. INGEST — Re-ingest that one file into Neo4j + Qdrant

Run manually:
    python -m src.ingestion.steering_updater --repo booking-crud-services --pr-number 42

Or triggered via webhook:
    POST /webhooks/steering-update
    Body: {"repo": "booking-crud-services", "pr_number": 42}

How it works:
    ┌─────────────────────────────────────────────────────────┐
    │  GitHub (PR merged)                                      │
    │       │                                                  │
    │       ▼                                                  │
    │  Fetch PR diff from GitHub API                           │
    │       │                                                  │
    │       ▼                                                  │
    │  Step 1: FILTER — ask LLM "is this meaningful?"          │
    │       │                                                  │
    │       ▼ (YES)                                            │
    │  Step 2: CLASSIFY — which steering file(s) affected?     │
    │       │                                                  │
    │       ▼                                                  │
    │  Step 3: PATCH — LLM updates existing steering with diff │
    │       │                                                  │
    │       ▼                                                  │
    │  Step 4: SAVE — write to kiro_steering/{repo}/*.md       │
    │       │                                                  │
    │       ▼                                                  │
    │  Step 5: INGEST — update Neo4j node + Qdrant embedding   │
    └─────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

import httpx
from openai import AsyncAzureOpenAI

from config.settings import get_settings
from processing.extraction.deterministic import (
    ExtractionResult,
    ExtractedEntity,
    ExtractedRelationship,
    compute_text_hash,
)
from processing.embeddings.service import get_embedding_service
from processing.extraction.writer import GraphWriter
from storage.graph.graph_store import GraphStore
from storage.graph.schema import EntityType, RelationshipType
from storage.vector.vector_store import get_vector_store

logger = logging.getLogger(__name__)

KIRO_STEERING_DIR = Path("kiro_steering")

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

FILTER_PROMPT = """You are evaluating whether a code change affects developer knowledge about a service.

A change is MEANINGFUL if it:
- Adds/removes/changes an API endpoint
- Adds/removes a dependency or integration with another service
- Changes the tech stack (new framework, database, message queue)
- Adds a new module or significantly restructures code
- Changes authentication/authorization flow
- Adds new environment variables or config requirements
- Changes how the service communicates (HTTP, Service Bus, events)
- Adds/removes a database or changes schema significantly

A change is NOT MEANINGFUL if it:
- Fixes a typo, formatting, or comment
- Refactors without changing external behavior
- Updates tests only
- Bumps a patch version of a dependency (1.2.3 → 1.2.4)
- Changes logging messages
- Fixes a bug without changing the API contract
- Updates CI/CD pipeline config only

Given this PR diff, respond with ONLY one of:
- "SKIP" if not meaningful
- "UPDATE: tech" if it affects tech stack, endpoints, dependencies, config
- "UPDATE: product" if it affects business logic, features, domain
- "UPDATE: structure" if it affects code organization, modules, architecture
- "UPDATE: tech,product" (or any combo) if multiple are affected

PR Title: {pr_title}
PR Diff (truncated):
{diff}
"""

PATCH_PROMPT = """You are updating an existing steering documentation file for a microservice.

RULES:
1. You are given the CURRENT steering file content and a PR diff showing what changed in the code.
2. UPDATE ONLY the parts that are affected by the change. Do NOT rewrite the entire file.
3. PRESERVE all existing content that is not affected by this change.
4. ADD new information where appropriate (new endpoint → add to endpoints list, new dep → add to deps).
5. REMOVE information only if the code change explicitly removes that capability.
6. Keep the same markdown format and structure as the original.
7. If the change is minor, the update should be minor too — maybe just one new bullet point or table row.

Current {file_type}.md content:
---
{current_content}
---

PR Title: {pr_title}
PR Diff:
---
{diff}
---

Return the COMPLETE updated {file_type}.md file (with your changes incorporated). Keep everything that wasn't affected unchanged.
"""


# ---------------------------------------------------------------------------
# GitHub API helper
# ---------------------------------------------------------------------------


async def fetch_pr_diff(org: str, repo: str, pr_number: int, token: str) -> dict[str, Any]:
    """Fetch PR title and diff from GitHub API."""
    async with httpx.AsyncClient(
        base_url="https://api.github.com",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        },
        timeout=30.0,
    ) as client:
        # Get PR metadata
        pr_resp = await client.get(f"/repos/{org}/{repo}/pulls/{pr_number}")
        pr_resp.raise_for_status()
        pr_data = pr_resp.json()
        pr_title = pr_data.get("title", "")

        # Get PR diff
        diff_resp = await client.get(
            f"/repos/{org}/{repo}/pulls/{pr_number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        diff_resp.raise_for_status()
        diff_text = diff_resp.text

        # Truncate diff if too large (keep under 8K chars for LLM context)
        if len(diff_text) > 8000:
            diff_text = diff_text[:8000] + "\n\n... [diff truncated]"

        return {"title": pr_title, "diff": diff_text}


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------


async def step_filter(llm_client: AsyncAzureOpenAI, deployment: str, pr_title: str, diff: str) -> str | None:
    """Step 1: Determine if the PR is meaningful enough to update steering.

    Returns None if SKIP, or comma-separated file types ("tech", "product,structure", etc.)
    """
    prompt = FILTER_PROMPT.format(pr_title=pr_title, diff=diff)

    response = await llm_client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=50,
    )
    result = (response.choices[0].message.content or "").strip()

    if result.upper().startswith("SKIP"):
        return None

    # Parse "UPDATE: tech,product" → "tech,product"
    if result.upper().startswith("UPDATE:"):
        files = result.split(":", 1)[1].strip().lower()
        return files

    # Fallback — if LLM gives unexpected format, skip
    logger.warning("Unexpected filter response: %r — skipping", result)
    return None


async def step_patch(
    llm_client: AsyncAzureOpenAI,
    deployment: str,
    file_type: str,
    current_content: str,
    pr_title: str,
    diff: str,
) -> str:
    """Step 3: Patch the existing steering file with changes from the PR."""
    prompt = PATCH_PROMPT.format(
        file_type=file_type,
        current_content=current_content,
        pr_title=pr_title,
        diff=diff,
    )

    response = await llm_client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4000,
    )
    result = response.choices[0].message.content or ""
    return result.strip()


def step_save(repo_name: str, file_type: str, content: str) -> Path:
    """Step 4: Write updated steering file to kiro_steering/{repo}/."""
    repo_dir = KIRO_STEERING_DIR / repo_name
    repo_dir.mkdir(parents=True, exist_ok=True)
    filepath = repo_dir / f"{file_type}.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath


async def step_ingest(repo_name: str, file_type: str, content: str) -> None:
    """Step 5: Re-ingest the updated steering file into Neo4j + Qdrant."""
    settings = get_settings()

    source_id = f"steering:{repo_name}:{file_type}"
    service_source_id = f"service:{repo_name}"
    text_hash = compute_text_hash(content)

    from datetime import UTC, datetime
    now = datetime.now(UTC).isoformat()

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

    relationship = ExtractedRelationship(
        source_label=EntityType.SERVICE.value,
        source_id=service_source_id,
        target_label=EntityType.CONFLUENCE_PAGE.value,
        target_id=source_id,
        rel_type=RelationshipType.DOCUMENTED_IN.value,
        properties={"created_at": now},
    )

    result = ExtractionResult(entities=[entity], relationships=[relationship])

    # Write to graph + vector store
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

    write_result = await writer.write(result)
    logger.info(
        "Ingested %s/%s.md — created=%d updated=%d",
        repo_name, file_type, write_result.created_count, write_result.updated_count,
    )
    await writer.close()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


async def update_steering_from_pr(org: str, repo: str, pr_number: int) -> dict[str, Any]:
    """Run the full steering update pipeline for a merged PR.

    Returns a summary dict with what happened.
    """
    settings = get_settings()
    start = time.time()

    # Create audit log for this webhook call (named after the repo)
    from ingestion.steering.steering_batch_update import _get_audit_filepath, _write_audit_log
    audit_file = _get_audit_filepath(repo)

    logger.info("=" * 60)
    logger.info("Steering Updater: %s/%s PR #%d", org, repo, pr_number)
    logger.info("=" * 60)

    # Fetch PR diff
    logger.info("Fetching PR diff...")
    pr_data = await fetch_pr_diff(org, repo, pr_number, settings.github_token)
    pr_title = pr_data["title"]
    diff = pr_data["diff"]
    logger.info("PR: %s", pr_title)

    # Create LLM client
    custom_http_client = httpx.AsyncClient(verify=False)
    llm_client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        http_client=custom_http_client,
    )
    deployment = settings.azure_openai_deployment_gpt4o

    try:
        # Step 1: Filter
        logger.info("Step 1: Filtering...")
        affected_files = await step_filter(llm_client, deployment, pr_title, diff)

        if affected_files is None:
            logger.info("  → SKIP (not meaningful)")
            _write_audit_log(audit_file, {
                "repo": repo,
                "pr_number": pr_number,
                "pr_title": pr_title,
                "decision": "skipped",
                "reason": "LLM determined change is not meaningful for developer knowledge",
                "duration_seconds": round(time.time() - start, 1),
            })
            return {
                "repo": repo,
                "pr_number": pr_number,
                "action": "skipped",
                "reason": "Change not meaningful for developer knowledge",
                "time": round(time.time() - start, 1),
                "audit_log": str(audit_file),
            }

        # Step 2: Classify (already done in filter response)
        file_types = [f.strip() for f in affected_files.split(",")]
        logger.info("  → UPDATE: %s", file_types)

        # Steps 3-5 for each affected file
        updated_files = []
        for file_type in file_types:
            if file_type not in ("product", "structure", "tech"):
                logger.warning("  Unknown file type: %s — skipping", file_type)
                continue

            # Read existing steering
            existing_path = KIRO_STEERING_DIR / repo / f"{file_type}.md"
            if existing_path.exists():
                current_content = existing_path.read_text(encoding="utf-8")
            else:
                current_content = f"# {file_type.title()}\n\nNo existing content."
                logger.warning("  No existing %s.md for %s — creating new", file_type, repo)

            # Step 3: Patch
            logger.info("  Patching %s.md...", file_type)
            patched_content = await step_patch(
                llm_client, deployment, file_type, current_content, pr_title, diff
            )

            # Step 4: Save
            saved_path = step_save(repo, file_type, patched_content)
            logger.info("  Saved: %s", saved_path)

            # Step 5: Ingest
            logger.info("  Ingesting into graph + embeddings...")
            await step_ingest(repo, file_type, patched_content)

            updated_files.append(file_type)

        elapsed = round(time.time() - start, 1)
        logger.info("")
        logger.info("Done! Updated %s in %.1fs", updated_files, elapsed)

        _write_audit_log(audit_file, {
            "repo": repo,
            "pr_number": pr_number,
            "pr_title": pr_title,
            "decision": "updated",
            "reason": "Meaningful change detected, updated steering",
            "files_updated": updated_files,
            "duration_seconds": elapsed,
        })

        return {
            "repo": repo,
            "pr_number": pr_number,
            "action": "updated",
            "files_updated": updated_files,
            "time": elapsed,
            "audit_log": str(audit_file),
        }

    finally:
        await llm_client.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Update steering from a merged PR")
    parser.add_argument("--org", default="TVSM-CS", help="GitHub org (default: TVSM-CS)")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--pr-number", type=int, required=True, help="PR number")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from dotenv import load_dotenv
    load_dotenv()

    result = asyncio.run(update_steering_from_pr(args.org, args.repo, args.pr_number))
    print()
    print("Result:", result)


if __name__ == "__main__":
    main()
