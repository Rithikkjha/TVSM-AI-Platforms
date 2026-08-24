"""Batch steering updater — scans all repos for recent merged PRs and updates steering.

This is the API/CLI approach (no webhooks needed). Run it on-demand or via cron.
It checks all configured repos for merged PRs in the last N days, filters for
meaningful changes, and patches the steering files + graph + embeddings.

Usage:
    # Default: last 7 days, max 2 PRs per repo
    python -m src.ingestion.steering_batch_update

    # Custom: last 3 days, max 5 PRs per repo
    python -m src.ingestion.steering_batch_update --days 3 --max-prs 5

    # Single repo
    python -m src.ingestion.steering_batch_update --repo booking-crud-services

    # Dry run (filter only, no patching)
    python -m src.ingestion.steering_batch_update --dry-run

Configuration:
    All config comes from environment variables and mcp_servers.yaml:
    - Repos list: from mcp_servers.yaml (github.config.repos)
    - GITHUB_TOKEN: for fetching PRs
    - AZURE_OPENAI_*: for LLM filter/patch
    - NEO4J_*, QDRANT_URL: for ingestion

    CLI overrides:
    --days N        Look back N days (default: 7)
    --max-prs N    Max PRs to process per repo (default: 2)
    --repo NAME    Process only this repo
    --dry-run      Only filter, don't patch or ingest
    --verbose      Debug logging

Audit Log:
    All decisions are logged to `logs/steering_update_audit.jsonl`
    Each line is a JSON object with:
    - timestamp, repo, pr_number, pr_title
    - decision: "skipped" | "updated" | "error"
    - reason: why it was skipped or what was updated
    - files_updated: which steering files were patched
    - duration_seconds: how long it took

After completion:
    Updated steering files are in kiro_steering/{repo}/*.md
    Neo4j + Qdrant are updated immediately
    MCP tools serve the new data on next call (no restart needed)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from config.mcp_registry import load_mcp_registry
from config.settings import get_settings
from ingestion.steering.steering_updater import (
    fetch_pr_diff,
    step_filter,
    step_ingest,
    step_patch,
    step_save,
)

logger = logging.getLogger(__name__)

AUDIT_LOG_DIR = Path("logs/steering_audits")


# ---------------------------------------------------------------------------
# Audit logger
# ---------------------------------------------------------------------------


def _get_audit_filepath(source: str = "batch") -> Path:
    """Get the audit log filepath for this run.

    Batch/API runs: logs/steering_audits/batch_2026-05-21T12-00-00.jsonl
        (one file for the entire run, all repos logged in it)
    Webhook runs: logs/steering_audits/booking-crud-services_2026-05-21T12-00-00.jsonl
        (one file per service that triggered the webhook)
    """
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{source}_{timestamp}.jsonl"
    return AUDIT_LOG_DIR / filename


def _write_audit_log(filepath: Path, entry: dict[str, Any]) -> None:
    """Append a JSON line to the audit log file."""
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = datetime.now(UTC).isoformat()
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


# ---------------------------------------------------------------------------
# GitHub API: fetch recent merged PRs
# ---------------------------------------------------------------------------


async def fetch_recent_merged_prs(
    org: str,
    repo: str,
    token: str,
    days: int = 7,
    max_prs: int = 2,
) -> list[dict[str, Any]]:
    """Fetch recently merged PRs for a repo (merged to default branch in last N days).

    Returns list of {number, title, merged_at, user} dicts, newest first.
    """
    since = (datetime.now(UTC) - timedelta(days=days)).isoformat()

    async with httpx.AsyncClient(
        base_url="https://api.github.com",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        },
        timeout=30.0,
    ) as client:
        # Fetch closed PRs sorted by updated date
        resp = await client.get(
            f"/repos/{org}/{repo}/pulls",
            params={
                "state": "closed",
                "sort": "updated",
                "direction": "desc",
                "per_page": 20,  # fetch more, filter to merged
                "base": "main",  # only PRs targeting main branch
            },
        )

        if resp.status_code == 404:
            # Try 'master' branch if 'main' doesn't exist
            resp = await client.get(
                f"/repos/{org}/{repo}/pulls",
                params={
                    "state": "closed",
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": 20,
                    "base": "master",
                },
            )

        if resp.status_code != 200:
            logger.warning("Failed to fetch PRs for %s/%s: %d", org, repo, resp.status_code)
            return [{"_error": True, "status_code": resp.status_code}]

        prs = resp.json()

        # Filter: only merged PRs within the time window
        merged_prs = []
        for pr in prs:
            if not pr.get("merged_at"):
                continue
            merged_at = pr["merged_at"]
            if merged_at >= since:
                merged_prs.append({
                    "number": pr["number"],
                    "title": pr["title"],
                    "merged_at": merged_at,
                    "user": pr.get("user", {}).get("login", "unknown"),
                })

        # Return newest first, capped at max_prs
        return merged_prs[:max_prs]


# ---------------------------------------------------------------------------
# Main batch pipeline
# ---------------------------------------------------------------------------


async def run_batch_update(
    days: int = 7,
    max_prs: int = 2,
    repo_filter: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run the batch steering update across all configured repos.

    Args:
        days: Look back N days for merged PRs.
        max_prs: Max PRs to process per repo.
        repo_filter: If set, only process this one repo.
        dry_run: If True, only filter (don't patch or ingest).

    Returns:
        Summary dict with counts and details.
    """
    settings = get_settings()
    registry = load_mcp_registry(settings.mcp_servers_config_path)
    github_config = next((s for s in registry.servers if s.name == "github"), None)

    if not github_config:
        return {"error": "No GitHub config found in mcp_servers.yaml"}

    org = github_config.config.get("org", "TVSM-CS")
    all_repos = github_config.config.get("repos", [])
    token = settings.github_token

    if not token:
        return {"error": "GITHUB_TOKEN not set"}

    # Filter to single repo if specified
    if repo_filter:
        if repo_filter not in all_repos:
            return {"error": f"Repo '{repo_filter}' not in configured repos list"}
        repos = [repo_filter]
    else:
        repos = all_repos

    start = time.time()
    logger.info("=" * 60)
    logger.info("Steering Batch Update")
    logger.info("  Repos: %d | Days: %d | Max PRs/repo: %d | Dry run: %s",
                len(repos), days, max_prs, dry_run)
    logger.info("=" * 60)

    # Create LLM client for filter/patch
    custom_http_client = httpx.AsyncClient(verify=False)
    from openai import AsyncAzureOpenAI
    llm_client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        http_client=custom_http_client,
    )
    deployment = settings.azure_openai_deployment_gpt4o

    # Stats
    total_prs_found = 0
    total_skipped = 0
    total_updated = 0
    total_errors = 0
    results: list[dict[str, Any]] = []

    # Create audit log file for this run
    audit_file = _get_audit_filepath("batch")
    logger.info("  Audit log: %s", audit_file)

    try:
        for idx, repo in enumerate(repos, 1):
            logger.info("")
            logger.info("[%d/%d] %s", idx, len(repos), repo)

            # Fetch recent merged PRs
            try:
                prs = await fetch_recent_merged_prs(org, repo, token, days=days, max_prs=max_prs)
            except Exception as exc:
                logger.warning("  Failed to fetch PRs: %s", exc)
                total_errors += 1
                _write_audit_log(audit_file, {
                    "repo": repo,
                    "decision": "error",
                    "reason": f"Failed to fetch PRs: {exc}",
                })
                continue

            if not prs:
                logger.info("  No merged PRs in last %d days", days)
                _write_audit_log(audit_file, {
                    "repo": repo,
                    "decision": "no_prs",
                    "reason": f"No merged PRs to main in last {days} days",
                })
                continue

            # Check if fetch returned an error marker
            if prs and prs[0].get("_error"):
                status_code = prs[0].get("status_code", "unknown")
                logger.warning("  GitHub API error: %s", status_code)
                total_errors += 1
                _write_audit_log(audit_file, {
                    "repo": repo,
                    "decision": "error",
                    "reason": f"GitHub API returned {status_code} (unauthorized or not found)",
                })
                continue

            total_prs_found += len(prs)
            logger.info("  Found %d merged PR(s)", len(prs))

            for pr in prs:
                pr_number = pr["number"]
                pr_title = pr["title"]
                logger.info("  PR #%d: %s", pr_number, pr_title)

                pr_start = time.time()

                try:
                    # Fetch diff
                    pr_data = await fetch_pr_diff(org, repo, pr_number, token)
                    diff = pr_data["diff"]

                    # Step 1: Filter
                    affected_files = await step_filter(llm_client, deployment, pr_title, diff)

                    if affected_files is None:
                        logger.info("    → SKIP (not meaningful)")
                        total_skipped += 1
                        _write_audit_log(audit_file, {
                            "repo": repo,
                            "pr_number": pr_number,
                            "pr_title": pr_title,
                            "decision": "skipped",
                            "reason": "LLM determined change is not meaningful for developer knowledge",
                            "duration_seconds": round(time.time() - pr_start, 1),
                        })
                        continue

                    file_types = [f.strip() for f in affected_files.split(",")]
                    logger.info("    → MEANINGFUL: affects %s", file_types)

                    if dry_run:
                        logger.info("    → DRY RUN: would update %s", file_types)
                        _write_audit_log(audit_file, {
                            "repo": repo,
                            "pr_number": pr_number,
                            "pr_title": pr_title,
                            "decision": "would_update",
                            "reason": f"Dry run — would update: {file_types}",
                            "files_affected": file_types,
                            "duration_seconds": round(time.time() - pr_start, 1),
                        })
                        total_updated += 1
                        continue

                    # Steps 3-5: Patch, Save, Ingest
                    updated_files = []
                    for file_type in file_types:
                        if file_type not in ("product", "structure", "tech"):
                            continue

                        # Read existing
                        from ingestion.steering.steering_updater import KIRO_STEERING_DIR
                        existing_path = KIRO_STEERING_DIR / repo / f"{file_type}.md"
                        if existing_path.exists():
                            current_content = existing_path.read_text(encoding="utf-8")
                        else:
                            current_content = f"# {file_type.title()}\n\nNo existing content."

                        # Patch
                        patched = await step_patch(
                            llm_client, deployment, file_type, current_content, pr_title, diff
                        )

                        # Save
                        step_save(repo, file_type, patched)

                        # Ingest
                        await step_ingest(repo, file_type, patched)

                        updated_files.append(file_type)
                        logger.info("    ✅ %s.md updated + ingested", file_type)

                    total_updated += 1
                    _write_audit_log(audit_file, {
                        "repo": repo,
                        "pr_number": pr_number,
                        "pr_title": pr_title,
                        "decision": "updated",
                        "reason": f"Meaningful change detected, updated steering",
                        "files_updated": updated_files,
                        "duration_seconds": round(time.time() - pr_start, 1),
                    })

                    results.append({
                        "repo": repo,
                        "pr_number": pr_number,
                        "pr_title": pr_title,
                        "files_updated": updated_files,
                    })

                except Exception as exc:
                    logger.error("    ❌ Error processing PR #%d: %s", pr_number, exc)
                    total_errors += 1
                    _write_audit_log(audit_file, {
                        "repo": repo,
                        "pr_number": pr_number,
                        "pr_title": pr_title,
                        "decision": "error",
                        "reason": str(exc),
                        "duration_seconds": round(time.time() - pr_start, 1),
                    })

    finally:
        await llm_client.close()

    elapsed = round(time.time() - start, 1)

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Batch Update Complete!")
    logger.info("  Repos scanned: %d", len(repos))
    logger.info("  PRs found: %d", total_prs_found)
    logger.info("  PRs skipped (not meaningful): %d", total_skipped)
    logger.info("  PRs updated (steering patched): %d", total_updated)
    logger.info("  Errors: %d", total_errors)
    logger.info("  Time: %.1fs", elapsed)
    logger.info("  Audit log: %s", audit_file)
    logger.info("=" * 60)

    return {
        "repos_scanned": len(repos),
        "prs_found": total_prs_found,
        "prs_skipped": total_skipped,
        "prs_updated": total_updated,
        "errors": total_errors,
        "time_seconds": elapsed,
        "updates": results,
        "audit_log": str(audit_file),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Batch update steering from recent merged PRs across all repos"
    )
    parser.add_argument("--days", type=int, default=7, help="Look back N days (default: 7)")
    parser.add_argument("--max-prs", type=int, default=2, help="Max PRs per repo (default: 2)")
    parser.add_argument("--repo", type=str, default=None, help="Process only this repo")
    parser.add_argument("--dry-run", action="store_true", help="Filter only, don't patch")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    from dotenv import load_dotenv
    load_dotenv()

    result = asyncio.run(run_batch_update(
        days=args.days,
        max_prs=args.max_prs,
        repo_filter=args.repo,
        dry_run=args.dry_run,
    ))

    print()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
