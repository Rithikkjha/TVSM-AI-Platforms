"""Fetch repository files via GitHub API for static analysis.

Uses the GitHub REST API to:
1. Get the file tree (all paths in the repo)
2. Fetch specific file contents (decoded from base64)
3. Get git commit history (for activity stats)

This avoids cloning repos locally — works with just API access.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GITHUB_API_BASE = "https://api.github.com"


class GitHubFetcher:
    """Fetches repo content via GitHub REST API for static analysis."""

    def __init__(self, token: str, org: str) -> None:
        self._token = token
        self._org = org
        self._client = httpx.AsyncClient(
            base_url=_GITHUB_API_BASE,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    async def get_default_branch(self, repo: str) -> str:
        """Get the default branch name for a repo."""
        try:
            resp = await self._client.get(f"/repos/{self._org}/{repo}")
            resp.raise_for_status()
            return resp.json().get("default_branch", "main")
        except Exception as exc:
            logger.warning("Failed to get default branch for %s: %s", repo, exc)
            return "main"

    async def get_tree(self, repo: str, branch: str | None = None) -> list[dict[str, Any]]:
        """Get the full file tree of a repo (recursive).

        Returns a list of dicts with keys: path, type (blob/tree), size.
        """
        if branch is None:
            branch = await self.get_default_branch(repo)

        try:
            resp = await self._client.get(
                f"/repos/{self._org}/{repo}/git/trees/{branch}",
                params={"recursive": "1"},
            )
            if resp.status_code == 404:
                logger.warning("Tree not found for %s/%s (branch: %s)", self._org, repo, branch)
                return []
            resp.raise_for_status()
            return resp.json().get("tree", [])
        except Exception as exc:
            logger.error("Failed to get tree for %s: %s", repo, exc)
            return []

    async def get_file_content(self, repo: str, path: str) -> str | None:
        """Fetch a single file's content (decoded from base64).

        Returns None if file doesn't exist or is too large.
        """
        try:
            resp = await self._client.get(f"/repos/{self._org}/{repo}/contents/{path}")
            if resp.status_code == 404:
                return None
            if resp.status_code == 429:
                logger.warning("Rate limited fetching %s/%s/%s", self._org, repo, path)
                return None
            resp.raise_for_status()
            data = resp.json()

            # Skip directories and files too large for API (>1MB)
            if data.get("type") != "file":
                return None
            if data.get("size", 0) > 1_000_000:
                logger.info("Skipping large file %s/%s (%d bytes)", repo, path, data["size"])
                return None

            content_b64 = data.get("content", "")
            if content_b64:
                return base64.b64decode(content_b64).decode("utf-8", errors="replace")
            return None
        except Exception as exc:
            logger.debug("Failed to fetch %s/%s: %s", repo, path, exc)
            return None

    async def get_file_batch(self, repo: str, paths: list[str]) -> dict[str, str]:
        """Fetch multiple files. Returns {path: content} for files that exist."""
        results: dict[str, str] = {}
        for path in paths:
            content = await self.get_file_content(repo, path)
            if content is not None:
                results[path] = content
        return results

    async def get_commits(self, repo: str, per_page: int = 100) -> list[dict[str, Any]]:
        """Get recent commits for activity stats."""
        try:
            resp = await self._client.get(
                f"/repos/{self._org}/{repo}/commits",
                params={"per_page": str(per_page)},
            )
            if resp.status_code != 200:
                return []
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("Failed to get commits for %s: %s", repo, exc)
            return []

    async def get_contributors(self, repo: str) -> list[dict[str, Any]]:
        """Get contributor stats for ownership detection."""
        try:
            resp = await self._client.get(
                f"/repos/{self._org}/{repo}/contributors",
                params={"per_page": "20"},
            )
            if resp.status_code != 200:
                return []
            return resp.json()
        except Exception as exc:
            logger.warning("Failed to get contributors for %s: %s", repo, exc)
            return []

    def get_directory_tree_display(self, tree: list[dict[str, Any]], max_depth: int = 2) -> str:
        """Format the file tree into a readable display (src/ focused)."""
        lines: list[str] = []

        # Skip noise files/folders
        skip_patterns = {
            ".vscode", ".github", ".husky", "node_modules", "dist", "build",
            "coverage", ".nyc_output", "target", "bin", "obj",
            "azure-pipelines", ".dockerignore", ".eslintrc", ".prettierrc",
            ".gitignore", "package-lock.json", "yarn.lock", ".editorconfig",
            "tsconfig.build.tsbuildinfo", ".env",
        }

        for item in tree:
            path = item.get("path", "")
            depth = path.count("/")
            if depth > max_depth:
                continue

            # Skip noise
            first_segment = path.split("/")[0]
            if first_segment.lower() in skip_patterns or any(s in path.lower() for s in skip_patterns):
                continue

            item_type = item.get("type", "")
            if item_type == "tree":
                lines.append(f"📁 {path}/")
            else:
                lines.append(f"📄 {path}")

        # Limit output
        if len(lines) > 50:
            lines = lines[:50] + [f"... and {len(lines) - 50} more"]
        return "\n".join(lines)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
