"""PR diff extraction from GitHub webhook payloads.

Fetches changed files and unified diffs from the GitHub REST API so the
LLM analyzer can determine whether steering files need updating.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ChangedFile:
    """A single file changed in a pull request."""

    path: str
    status: str  # "added", "modified", "removed", "renamed"
    patch: str = ""


@dataclass
class DiffResult:
    """Aggregated diff information for a single PR event."""

    repo_name: str
    pr_number: int
    action: str  # "closed", "opened", "synchronize"
    merged: bool
    changed_files: list[ChangedFile] = field(default_factory=list)
    error: str | None = None


async def extract_pr_diff(payload: dict, github_token: str) -> DiffResult:
    """Extract PR diff from a GitHub webhook payload.

    For ``action == "closed"`` with ``merged == False``, returns an empty
    result (nothing to analyze). Otherwise fetches the file list from the
    GitHub API.

    Args:
        payload: Parsed JSON body of the webhook event.
        github_token: GitHub personal access token for API calls.

    Returns:
        A populated :class:`DiffResult`.
    """
    action = payload.get("action", "")
    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})
    repo_name = repo.get("name", "")
    full_name = repo.get("full_name", "")
    pr_number = pr.get("number", 0)
    merged = pr.get("merged", False)

    # Closed without merge — nothing to analyze
    if action == "closed" and not merged:
        return DiffResult(
            repo_name=repo_name,
            pr_number=pr_number,
            action=action,
            merged=False,
            changed_files=[],
        )

    # Fetch changed files from GitHub API
    try:
        changed_files = await _fetch_pr_files(full_name, pr_number, github_token)
        return DiffResult(
            repo_name=repo_name,
            pr_number=pr_number,
            action=action,
            merged=merged,
            changed_files=changed_files,
        )
    except Exception as exc:
        logger.exception("Failed to fetch PR diff for %s#%d", full_name, pr_number)
        return DiffResult(
            repo_name=repo_name,
            pr_number=pr_number,
            action=action,
            merged=merged,
            changed_files=[],
            error=f"Failed to fetch PR diff: {exc}",
        )


async def _fetch_pr_files(
    full_name: str, pr_number: int, github_token: str
) -> list[ChangedFile]:
    """Fetch the list of changed files for a PR via GitHub REST API."""
    url = f"https://api.github.com/repos/{full_name}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

    files_data = response.json()
    changed_files: list[ChangedFile] = []
    for item in files_data:
        changed_files.append(
            ChangedFile(
                path=item.get("filename", ""),
                status=item.get("status", "modified"),
                patch=item.get("patch", ""),
            )
        )
    return changed_files


__all__ = [
    "ChangedFile",
    "DiffResult",
    "extract_pr_diff",
]
