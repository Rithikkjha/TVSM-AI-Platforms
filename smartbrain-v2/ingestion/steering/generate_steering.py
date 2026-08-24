"""Auto-generate steering files for all configured repos.

Run with:
    python -m src.ingestion.generate_steering

For each repo, this script:
1. Fetches key files (README.md, package.json, Dockerfile, etc.) via GitHub API
2. Fetches the directory tree (top 2 levels)
3. Sends everything to GPT-4o-mini to produce a structured steering file
4. Saves the output to generated_steering/{repo_name}.md

The generated steering files are then ingested by the memory graph
alongside the normal metadata.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from pathlib import Path

import httpx
from openai import AsyncAzureOpenAI

from config.mcp_registry import load_mcp_registry
from config.settings import get_settings

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("generated_steering")

STEERING_PROMPT = """You are analyzing a software repository to produce a structured steering file.
Based on the repository structure and file contents provided below, produce a comprehensive summary in Markdown format with these sections:

## Service Overview
- What this service/application does (purpose, domain)
- Key responsibilities

## Tech Stack
- Language and version
- Framework
- Database (if any)
- Message queue / event bus (if any)
- Key libraries/dependencies

## API Endpoints / Routes
- List all API endpoints you can identify (method, path, description)
- If you can't find explicit routes, note what the service exposes

## Architecture
- How the code is organized (layers, modules)
- Key design patterns used
- Entry point(s)

## Dependencies (External Services)
- What other services/APIs does this call?
- What databases/caches does it connect to?

## Configuration
- Key environment variables
- Configuration files

## Deployment
- How it's deployed (Docker, K8s, etc.)
- Ports exposed
- Health check endpoints

If you cannot determine something from the provided files, say "Not determinable from available files" rather than guessing.
Be concise but thorough. Focus on facts from the code, not speculation."""

KEY_FILES = [
    "README.md",
    "readme.md",
    "package.json",
    "pom.xml",
    "build.gradle",
    "pyproject.toml",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".env.example",
    "src/main.ts",
    "src/index.ts",
    "src/app.ts",
    "src/main.py",
    "src/app.py",
    "app.py",
    "main.py",
    "src/main/java",
    "application.yml",
    "application.properties",
    "src/main/resources/application.yml",
    "src/main/resources/application.properties",
    "swagger.json",
    "openapi.yaml",
    "openapi.json",
]


async def fetch_file_content(
    client: httpx.AsyncClient, org: str, repo: str, path: str
) -> str | None:
    """Fetch a single file's content from GitHub API."""
    try:
        resp = await client.get(f"/repos/{org}/{repo}/contents/{path}")
        if resp.status_code == 404:
            return None
        if resp.status_code == 429:
            logger.warning("Rate limited fetching %s/%s/%s", org, repo, path)
            return None
        resp.raise_for_status()
        data = resp.json()
        if data.get("type") != "file":
            return None
        content_b64 = data.get("content", "")
        if content_b64:
            content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
            # Truncate very large files
            if len(content) > 10000:
                content = content[:10000] + "\n... [truncated]"
            return content
        return None
    except Exception:
        return None


async def fetch_tree(
    client: httpx.AsyncClient, org: str, repo: str
) -> str:
    """Fetch the repo's file tree (top 2 levels) for context."""
    try:
        resp = await client.get(
            f"/repos/{org}/{repo}/git/trees/HEAD",
            params={"recursive": "1"},
        )
        if resp.status_code != 200:
            return "Directory tree not available."
        data = resp.json()
        tree = data.get("tree", [])
        # Filter to top 3 levels and limit to 100 entries
        lines = []
        for item in tree[:200]:
            path = item.get("path", "")
            depth = path.count("/")
            if depth <= 2:
                prefix = "📁 " if item.get("type") == "tree" else "📄 "
                lines.append(f"{prefix}{path}")
        return "\n".join(lines[:100])
    except Exception:
        return "Directory tree not available."


async def generate_steering_for_repo(
    github_client: httpx.AsyncClient,
    llm_client: AsyncAzureOpenAI,
    org: str,
    repo: str,
    deployment_name: str,
) -> str:
    """Generate a steering file for a single repo."""
    # Fetch directory tree
    tree = await fetch_tree(github_client, org, repo)

    # Fetch key files
    file_contents: dict[str, str] = {}
    for path in KEY_FILES:
        content = await fetch_file_content(github_client, org, repo, path)
        if content:
            file_contents[path] = content

    if not file_contents and tree == "Directory tree not available.":
        return f"# {repo}\n\nNo files accessible for analysis.\n"

    # Build context for LLM
    context_parts = [f"# Repository: {org}/{repo}\n"]
    context_parts.append(f"## Directory Structure\n```\n{tree}\n```\n")

    for path, content in file_contents.items():
        context_parts.append(f"## File: {path}\n```\n{content}\n```\n")

    context = "\n".join(context_parts)

    # Truncate if too long (stay under 15K tokens ~ 60K chars for gpt-4o-mini)
    if len(context) > 50000:
        context = context[:50000] + "\n... [context truncated]"

    # Call LLM
    try:
        response = await llm_client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": STEERING_PROMPT},
                {"role": "user", "content": f"Analyze this repository:\n\n{context}"},
            ],
            temperature=0.1,
            max_tokens=3000,
            timeout=60.0,
        )
        return response.choices[0].message.content or f"# {repo}\n\nAnalysis failed.\n"
    except Exception as exc:
        logger.error("LLM failed for %s: %s", repo, exc)
        return f"# {repo}\n\nAnalysis failed: {exc}\n"


async def run() -> None:
    """Generate steering files for all configured repos."""
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Load config
    registry = load_mcp_registry(settings.mcp_servers_config_path)
    github_config = next((s for s in registry.servers if s.name == "github"), None)
    if not github_config:
        logger.error("No GitHub config found in mcp_servers.yaml")
        return

    org = github_config.config.get("org", "")
    repos = github_config.config.get("repos", [])
    token = settings.github_token

    logger.info("Generating steering files for %d repos in org %s", len(repos), org)

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Build clients
    github_client = httpx.AsyncClient(
        base_url="https://api.github.com",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=httpx.Timeout(15.0, connect=5.0),
    )

    llm_client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        timeout=60.0,  # 60 second timeout per LLM call
    )

    deployment = settings.azure_openai_deployment_gpt4o
    total_repos = len(repos)
    generated = 0
    skipped = 0

    try:
        for idx, repo in enumerate(repos, 1):
            output_path = OUTPUT_DIR / f"{repo}.md"

            # Skip if already generated
            if output_path.exists():
                logger.info("[%d/%d] %s — already exists, skipping", idx, total_repos, repo)
                skipped += 1
                continue

            logger.info("[%d/%d] Generating steering for: %s", idx, total_repos, repo)

            steering_content = await generate_steering_for_repo(
                github_client, llm_client, org, repo, deployment
            )

            # Save to file
            output_path.write_text(
                f"# Steering File: {repo}\n\n"
                f"*Auto-generated from repository analysis*\n\n"
                f"{steering_content}\n",
                encoding="utf-8",
            )
            generated += 1
            logger.info("[%d/%d] ✅ Saved: %s", idx, total_repos, output_path)

    finally:
        await github_client.aclose()
        await llm_client.close()

    logger.info("")
    logger.info("=" * 50)
    logger.info("Steering generation complete!")
    logger.info("  Generated: %d", generated)
    logger.info("  Skipped (already exist): %d", skipped)
    logger.info("  Output directory: %s", OUTPUT_DIR.resolve())
    logger.info("=" * 50)


def main() -> None:
    """CLI entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
