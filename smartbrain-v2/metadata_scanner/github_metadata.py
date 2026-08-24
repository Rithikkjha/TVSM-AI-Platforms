"""Repository metadata fetching from the GitHub REST API.

Fetches languages, contributors, recent commits, CODEOWNERS, README,
build manifests, and file tree for steering file generation.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)


@dataclass
class RepoMetadata:
    """All metadata about a repository needed for steering generation."""

    name: str
    languages: dict[str, int] = field(default_factory=dict)
    contributors: list[dict] = field(default_factory=list)
    recent_commits: list[dict] = field(default_factory=list)
    codeowners: str | None = None
    readme: str | None = None
    build_manifest: dict[str, str] = field(default_factory=dict)
    file_tree: list[str] = field(default_factory=list)
    default_branch: str = "main"


class MetadataFetcher:
    """Fetches repository metadata from the GitHub REST API.

    Makes parallel API calls where possible, then sequential calls for
    files that depend on the tree response.
    """

    def __init__(self, token: str, org: str = "TVSM-CS") -> None:
        self._org = org
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=httpx.Timeout(30.0),
        )

    async def fetch(self, repo_name: str) -> RepoMetadata:
        """Fetch all metadata for a single repository.

        Makes parallel API calls for: repo info, languages, contributors,
        commits, file tree. Then sequential for CODEOWNERS, README, manifests.
        """
        full_name = f"{self._org}/{repo_name}"

        # Parallel fetch of independent API calls
        repo_info, languages, contributors, commits, tree = await asyncio.gather(
            self._get_repo_info(full_name),
            self._get_languages(full_name),
            self._get_contributors(full_name),
            self._get_commits(full_name),
            self._get_tree(full_name),
            return_exceptions=True,
        )

        # Handle exceptions from gather
        if isinstance(repo_info, Exception):
            logger.warning("Failed to fetch repo info for %s: %s", repo_name, repo_info)
            repo_info = {}
        if isinstance(languages, Exception):
            logger.warning("Failed to fetch languages for %s: %s", repo_name, languages)
            languages = {}
        if isinstance(contributors, Exception):
            logger.warning("Failed to fetch contributors for %s: %s", repo_name, contributors)
            contributors = []
        if isinstance(commits, Exception):
            logger.warning("Failed to fetch commits for %s: %s", repo_name, commits)
            commits = []
        if isinstance(tree, Exception):
            logger.warning("Failed to fetch tree for %s: %s", repo_name, tree)
            tree = []

        default_branch = repo_info.get("default_branch", "main") if isinstance(repo_info, dict) else "main"

        # Sequential fetches
        codeowners = await self._get_file_content(full_name, "CODEOWNERS", default_branch)
        readme = await self._get_file_content(full_name, "README.md", default_branch)
        build_manifest = await self._get_build_manifests(full_name, tree, default_branch)

        file_paths = [item.get("path", "") for item in tree] if isinstance(tree, list) else []

        return RepoMetadata(
            name=repo_name,
            languages=languages if isinstance(languages, dict) else {},
            contributors=contributors if isinstance(contributors, list) else [],
            recent_commits=commits if isinstance(commits, list) else [],
            codeowners=codeowners,
            readme=readme,
            build_manifest=build_manifest,
            file_tree=file_paths,
            default_branch=default_branch,
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    # -- Private API methods -----------------------------------------------

    async def _get_repo_info(self, full_name: str) -> dict:
        resp = await self._client.get(f"/repos/{full_name}")
        resp.raise_for_status()
        return resp.json()

    async def _get_languages(self, full_name: str) -> dict[str, int]:
        resp = await self._client.get(f"/repos/{full_name}/languages")
        resp.raise_for_status()
        return resp.json()

    async def _get_contributors(self, full_name: str) -> list[dict]:
        resp = await self._client.get(
            f"/repos/{full_name}/contributors", params={"per_page": 10}
        )
        resp.raise_for_status()
        return resp.json()

    async def _get_commits(self, full_name: str) -> list[dict]:
        resp = await self._client.get(
            f"/repos/{full_name}/commits", params={"per_page": 20}
        )
        resp.raise_for_status()
        return resp.json()

    async def _get_tree(self, full_name: str) -> list[dict]:
        """Fetch the file tree (recursive, truncated)."""
        resp = await self._client.get(
            f"/repos/{full_name}/git/trees/HEAD",
            params={"recursive": "1"},
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return data.get("tree", [])

    async def _get_file_content(
        self, full_name: str, path: str, branch: str
    ) -> str | None:
        """Fetch a single file's content via the contents API."""
        resp = await self._client.get(
            f"/repos/{full_name}/contents/{path}",
            params={"ref": branch},
            headers={"Accept": "application/vnd.github.raw+json"},
        )
        if resp.status_code == 200:
            return resp.text
        return None

    async def _get_build_manifests(
        self, full_name: str, tree: list[dict], branch: str
    ) -> dict[str, str]:
        """Fetch build manifests (package.json, pom.xml, *.csproj) from root."""
        manifest_names = {"package.json", "pom.xml"}
        manifests: dict[str, str] = {}

        # Check tree for root-level manifests and .csproj files
        target_paths: list[str] = []
        for item in tree if isinstance(tree, list) else []:
            path = item.get("path", "")
            # Root-level manifest files
            if path in manifest_names:
                target_paths.append(path)
            # Root-level .csproj files
            elif path.endswith(".csproj") and "/" not in path:
                target_paths.append(path)

        for path in target_paths:
            content = await self._get_file_content(full_name, path, branch)
            if content:
                manifests[path] = content

        return manifests


__all__ = [
    "MetadataFetcher",
    "RepoMetadata",
]
