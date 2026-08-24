"""Concrete GitHub HTTP client implementing the GitHubMCPClient protocol.

Calls the GitHub REST API (api.github.com) using httpx with a personal
access token for authentication. Designed to satisfy the
:class:`~src.ingestion.orchestrator.GitHubMCPClient` protocol so the
orchestrator can use it interchangeably with any future MCP-transport
implementation.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GITHUB_API_BASE = "https://api.github.com"


class GitHubHTTPClient:
    """Concrete GitHub client using httpx to call api.github.com."""

    name: str = "github"
    source_type: str = "github"

    def __init__(self, token: str, org: str, repos: list[str]) -> None:
        self._token = token
        self._org = org
        self._repos = repos
        self._client = httpx.AsyncClient(
            base_url=_GITHUB_API_BASE,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=httpx.Timeout(10.0, connect=5.0),  # 10s read, 5s connect
        )

    async def list_repositories(self) -> list[dict[str, Any]]:
        """Fetch metadata for each configured repo via GET /repos/{org}/{repo}."""
        results: list[dict[str, Any]] = []
        total = len(self._repos)

        for idx, repo_name in enumerate(self._repos, 1):
            logger.info("Fetching repo %d/%d: %s", idx, total, repo_name)
            try:
                resp = await self._client.get(f"/repos/{self._org}/{repo_name}")
                if resp.status_code == 404:
                    logger.warning("Repo not found: %s/%s", self._org, repo_name)
                    continue
                if resp.status_code == 429:
                    logger.warning("Rate limited fetching repo %s", repo_name)
                    continue
                resp.raise_for_status()
                results.append(resp.json())
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Failed to fetch repo %s/%s: %s %s",
                    self._org,
                    repo_name,
                    exc.response.status_code,
                    exc.response.reason_phrase,
                )
            except httpx.TimeoutException:
                logger.warning("Timeout fetching repo %s/%s — skipping", self._org, repo_name)
            except httpx.HTTPError as exc:
                logger.error("HTTP error fetching repo %s/%s: %s", self._org, repo_name, exc)

        logger.info("Fetched %d/%d repositories", len(results), total)
        return results

    async def get_pull_requests(self, repo_name: str) -> list[dict[str, Any]]:
        """Fetch the most recent 30 PRs for a repo."""
        try:
            resp = await self._client.get(
                f"/repos/{self._org}/{repo_name}/pulls",
                params={"state": "all", "per_page": "30", "sort": "updated"},
            )
            if resp.status_code == 429:
                logger.warning("Rate limited fetching PRs for %s", repo_name)
                return []
            resp.raise_for_status()
            prs: list[dict[str, Any]] = resp.json()
            return prs
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Failed to fetch PRs for %s: %s %s",
                repo_name,
                exc.response.status_code,
                exc.response.reason_phrase,
            )
            return []
        except httpx.HTTPError as exc:
            logger.error("HTTP error fetching PRs for %s: %s", repo_name, exc)
            return []

    async def get_codeowners(self, repo_name: str) -> str | None:
        """Fetch CODEOWNERS file content, trying root then .github/ path."""
        paths_to_try = ["CODEOWNERS", ".github/CODEOWNERS"]

        for path in paths_to_try:
            try:
                resp = await self._client.get(f"/repos/{self._org}/{repo_name}/contents/{path}")
                if resp.status_code == 404:
                    continue
                if resp.status_code == 429:
                    logger.warning("Rate limited fetching CODEOWNERS for %s", repo_name)
                    return None
                resp.raise_for_status()
                data = resp.json()
                # Content comes base64 encoded in the API response
                content_b64 = data.get("content", "")
                if content_b64:
                    return base64.b64decode(content_b64).decode("utf-8")
                return None
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    continue
                logger.warning(
                    "Failed to fetch CODEOWNERS at %s for %s: %s",
                    path,
                    repo_name,
                    exc.response.status_code,
                )
            except httpx.HTTPError as exc:
                logger.warning("HTTP error fetching CODEOWNERS for %s: %s", repo_name, exc)

        return None

    async def get_key_files(self, repo_name: str) -> dict[str, str]:
        """Fetch Level 1 key files (README, package.json, Dockerfile, etc.).

        Returns a dict of {filename: content} for files that exist.
        """
        paths_to_try = [
            "README.md", "readme.md",
            "package.json", "pom.xml", "build.gradle", "pyproject.toml",
            "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            ".env.example",
            "src/main/resources/application.yml",
            "src/main/resources/application.properties",
        ]
        results: dict[str, str] = {}

        for path in paths_to_try:
            try:
                resp = await self._client.get(f"/repos/{self._org}/{repo_name}/contents/{path}")
                if resp.status_code == 404:
                    continue
                if resp.status_code == 429:
                    break  # Stop on rate limit
                resp.raise_for_status()
                data = resp.json()
                if data.get("type") != "file":
                    continue
                content_b64 = data.get("content", "")
                if content_b64:
                    content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
                    # Truncate very large files
                    if len(content) > 8000:
                        content = content[:8000] + "\n... [truncated]"
                    results[path] = content
            except httpx.TimeoutException:
                continue
            except httpx.HTTPError:
                continue

        return results

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()
