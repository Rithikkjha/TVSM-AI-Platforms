"""GitHub-based dependency extractor — fetches config files and uses GPT-4o.

Standalone module that:
1. Fetches key config files from a GitHub repo via API
2. Sends them to GPT-4o with a focused extraction prompt
3. Returns structured dependencies ready for Neo4j edges

No regex, no language-specific parsing, no cloning.
GPT-4o reads package.json, csproj, appsettings, docker-compose natively.

Usage:
    python -m processing.extraction.github_deps_extractor --repo PaymentService
    python -m processing.extraction.github_deps_extractor --all
    python -m processing.extraction.github_deps_extractor --repo booking-crud-services --dry-run

Output: JSON with inbound/outbound/service_bus/databases for each repo.
Can be piped into Phase 2 later when you're ready to integrate.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from openai import AsyncAzureOpenAI

logger = logging.getLogger(__name__)

# Files to fetch from each repo (covers .NET, Node, Java, Python)
_CONFIG_FILES_TO_FETCH = [
    # .NET
    "appsettings.json",
    "appsettings.Development.json",
    "appsettings.Production.json",
    "host.json",  # Azure Functions
    # Node
    "package.json",
    # Java
    "pom.xml",
    "build.gradle",
    "src/main/resources/application.yml",
    "src/main/resources/application.properties",
    # Python
    "pyproject.toml",
    "requirements.txt",
    # Docker / Infra
    "docker-compose.yml",
    "docker-compose.yaml",
    "Dockerfile",
    # General
    ".env.example",
    "README.md",
]

_GITHUB_API_BASE = "https://api.github.com"

# GPT-4o prompt for dependency extraction from config files
_SYSTEM_PROMPT = """You extract service dependencies from configuration files of a microservice.

Output a JSON object with these keys:
{
  "service_name": "string — the repo/service name",
  "outbound_http": [{"target": "service name or URL", "purpose": "why it calls this"}],
  "inbound_endpoints": [{"method": "GET/POST/etc", "path": "/api/...", "purpose": "what it does"}],
  "service_bus": {
    "publishes_to": [{"topic": "topic-name", "events": ["EVENT_1", "EVENT_2"]}],
    "subscribes_to": [{"topic": "topic-name", "events": ["EVENT_1"]}]
  },
  "databases": [{"type": "MSSQL/Redis/MongoDB/etc", "purpose": "what data"}],
  "external_integrations": [{"name": "JusPay/SendGrid/etc", "type": "payment/email/etc"}],
  "build_dependencies": ["list of key packages/libraries (top 10 most important)"]
}

RULES:
1. Extract ONLY what's explicitly in the config files. Don't infer or guess.
2. For outbound_http: look for base URLs, HttpClient configs, API endpoints in settings.
3. For service_bus: look for queue/topic names in connection strings or config.
4. For databases: look for connection strings, DB names.
5. For inbound_endpoints: look at controller routes, function triggers, API definitions.
6. If a file doesn't contain relevant info, skip it. Don't make things up.
7. Return empty arrays for sections with no data found.
8. For build_dependencies: only list the most significant packages (skip testing/tooling).
"""


@dataclass
class RepoDeps:
    """Structured dependencies extracted from a repo's config files."""

    service_name: str = ""
    outbound_http: list[dict[str, str]] = field(default_factory=list)
    inbound_endpoints: list[dict[str, str]] = field(default_factory=list)
    service_bus: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {"publishes_to": [], "subscribes_to": []})
    databases: list[dict[str, str]] = field(default_factory=list)
    external_integrations: list[dict[str, str]] = field(default_factory=list)
    build_dependencies: list[str] = field(default_factory=list)
    files_fetched: int = 0
    error: str | None = None


class GitHubDepsExtractor:
    """Fetches config files from GitHub and sends to GPT-4o for dep extraction."""

    def __init__(
        self,
        github_token: str,
        org: str,
        openai_endpoint: str,
        openai_key: str,
        openai_deployment: str,
        openai_api_version: str = "2025-01-01-preview",
    ) -> None:
        self._org = org
        self._github = httpx.AsyncClient(
            base_url=_GITHUB_API_BASE,
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=httpx.Timeout(15.0, connect=5.0),
        )
        self._openai = AsyncAzureOpenAI(
            azure_endpoint=openai_endpoint,
            api_key=openai_key,
            api_version=openai_api_version,
        )
        self._deployment = openai_deployment

    async def extract_repo(self, repo_name: str) -> RepoDeps:
        """Fetch config files from a repo and extract dependencies via GPT-4o."""

        result = RepoDeps(service_name=repo_name)

        # Step 1: Fetch config files
        files = await self._fetch_config_files(repo_name)
        result.files_fetched = len(files)

        if not files:
            result.error = "No config files found"
            return result

        # Step 2: Build content blob for GPT-4o
        content_parts = [f"# Config files for repo: {repo_name}\n"]
        for path, content in files.items():
            # Truncate very large files
            if len(content) > 5000:
                content = content[:5000] + "\n... [truncated]"
            content_parts.append(f"\n## File: {path}\n```\n{content}\n```\n")

        full_content = "\n".join(content_parts)

        # Step 3: Send to GPT-4o
        try:
            response = await self._openai.chat.completions.create(
                model=self._deployment,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": full_content},
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=2000,
            )

            raw = response.choices[0].message.content
            if raw:
                parsed = json.loads(raw)
                result.outbound_http = parsed.get("outbound_http", [])
                result.inbound_endpoints = parsed.get("inbound_endpoints", [])
                result.service_bus = parsed.get("service_bus", {"publishes_to": [], "subscribes_to": []})
                result.databases = parsed.get("databases", [])
                result.external_integrations = parsed.get("external_integrations", [])
                result.build_dependencies = parsed.get("build_dependencies", [])

        except Exception as exc:
            result.error = str(exc)
            logger.error("GPT-4o extraction failed for %s: %s", repo_name, exc)

        return result

    async def extract_all(self, repos: list[str]) -> list[RepoDeps]:
        """Extract dependencies for multiple repos sequentially."""
        results = []
        for i, repo in enumerate(repos, 1):
            print(f"[{i}/{len(repos)}] Extracting: {repo}...", flush=True)
            result = await self.extract_repo(repo)
            results.append(result)
            if result.error:
                print(f"  ⚠ {result.error}")
            else:
                print(
                    f"  ✓ {result.files_fetched} files → "
                    f"{len(result.outbound_http)} outbound, "
                    f"{len(result.inbound_endpoints)} endpoints, "
                    f"{len(result.databases)} DBs"
                )
        return results

    async def _fetch_config_files(self, repo_name: str) -> dict[str, str]:
        """Fetch config files from GitHub API. Returns {path: content}."""
        files: dict[str, str] = {}

        for path in _CONFIG_FILES_TO_FETCH:
            try:
                resp = await self._github.get(
                    f"/repos/{self._org}/{repo_name}/contents/{path}"
                )
                if resp.status_code == 404:
                    continue
                if resp.status_code == 429:
                    logger.warning("Rate limited fetching %s/%s", repo_name, path)
                    break
                resp.raise_for_status()
                data = resp.json()
                if data.get("type") != "file":
                    continue
                content_b64 = data.get("content", "")
                if content_b64:
                    content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
                    files[path] = content
            except httpx.TimeoutException:
                continue
            except httpx.HTTPError:
                continue

        return files

    async def close(self) -> None:
        await self._github.aclose()
        await self._openai.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


async def run(repo: str | None, all_repos: bool, dry_run: bool) -> None:
    """CLI entry point."""
    from dotenv import load_dotenv
    load_dotenv()

    from config.settings import get_settings
    from config.mcp_registry import load_mcp_registry

    settings = get_settings()
    registry = load_mcp_registry(settings.mcp_servers_config_path)

    github_config = next((s for s in registry.servers if s.name == "github"), None)
    if not github_config:
        print("ERROR: No GitHub server configured in mcp_servers.yaml")
        return

    org = github_config.config.get("org", "")
    repos_list = github_config.config.get("repos", [])
    token = os.environ.get(github_config.config.get("token_env", ""), "") or settings.github_token

    if not token:
        print("ERROR: No GitHub token found")
        return

    extractor = GitHubDepsExtractor(
        github_token=token,
        org=org,
        openai_endpoint=settings.azure_openai_endpoint,
        openai_key=settings.azure_openai_key,
        openai_deployment=settings.azure_openai_deployment_gpt4o,
        openai_api_version=settings.azure_openai_api_version,
    )

    if repo:
        targets = [repo]
    elif all_repos:
        targets = repos_list
    else:
        print("ERROR: Specify --repo NAME or --all")
        return

    print(f"\n🔍 Extracting dependencies from {len(targets)} repo(s) via GitHub API + GPT-4o\n")
    start = time.time()

    results = await extractor.extract_all(targets)
    await extractor.close()

    elapsed = time.time() - start

    # Output results
    output = []
    for r in results:
        entry = {
            "service_name": r.service_name,
            "files_fetched": r.files_fetched,
            "outbound_http": r.outbound_http,
            "inbound_endpoints": r.inbound_endpoints,
            "service_bus": r.service_bus,
            "databases": r.databases,
            "external_integrations": r.external_integrations,
            "build_dependencies": r.build_dependencies,
        }
        if r.error:
            entry["error"] = r.error
        output.append(entry)

    if dry_run:
        print(f"\n{'='*60}")
        print(json.dumps(output, indent=2))
        print(f"{'='*60}")
    else:
        # Save to file
        out_path = f"data/github_deps_{'_'.join(targets[:3])}.json"
        os.makedirs("data", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n✅ Results saved to {out_path}")

    print(f"Completed in {elapsed:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract service dependencies from GitHub repos via GPT-4o"
    )
    parser.add_argument("--repo", type=str, help="Single repo name to extract")
    parser.add_argument("--all", action="store_true", dest="all_repos", help="Extract all configured repos")
    parser.add_argument("--dry-run", action="store_true", help="Print results to stdout instead of saving")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
    asyncio.run(run(repo=args.repo, all_repos=args.all_repos, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
