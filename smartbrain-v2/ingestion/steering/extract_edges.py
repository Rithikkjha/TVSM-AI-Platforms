"""Extract DEPENDS_ON edges from Kiro steering files and create them in Neo4j.

Reads the product.md and tech.md files for each service, uses LLM to extract
integration/dependency relationships, and creates DEPENDS_ON edges in the graph.

Usage:
    python -m src.ingestion.extract_edges_from_steering
    python -m src.ingestion.extract_edges_from_steering --repo booking-crud-services
    python -m src.ingestion.extract_edges_from_steering --dry-run

This fills the gap where get_service_info shows empty dependencies.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx
from openai import AsyncAzureOpenAI

from config.settings import get_settings
from storage.graph.graph_store import GraphStore
from storage.graph.schema import EntityType, RelationshipType

logger = logging.getLogger(__name__)

KIRO_STEERING_DIR = Path("kiro_steering")

EXTRACT_PROMPT = """You are extracting service dependencies from a microservice's steering documentation.

Given the service name and its product/tech documentation, identify ALL services it depends on (calls or sends events to) and ALL services that depend on it (call it or send events to it).

RULES:
- Only extract dependencies to OTHER SERVICES in our org (not external APIs like Azure Key Vault, Azure Service Bus itself, or databases)
- Service Bus topics are INDIRECT dependencies — if service A publishes to a topic that service B subscribes to, that's A → B
- HTTP calls are DIRECT dependencies
- Use the exact service name if mentioned, otherwise use the target system name as-is

Respond in this EXACT JSON format (no other text):
{{
  "depends_on": [
    {{"target": "service-name", "type": "http|service_bus|build", "detail": "short description"}}
  ],
  "depended_by": [
    {{"source": "service-name", "type": "http|service_bus|build", "detail": "short description"}}
  ]
}}

If no dependencies found, return empty arrays.
"""


async def extract_edges_for_repo(
    repo_name: str,
    product_content: str,
    tech_content: str,
    llm_client: AsyncAzureOpenAI,
    deployment: str,
) -> dict[str, list[dict[str, str]]]:
    """Use LLM to extract dependency edges from steering content."""

    content = f"Service: {repo_name}\n\n"
    if product_content:
        content += f"## Product Context (integrations section):\n{product_content[:4000]}\n\n"
    if tech_content:
        content += f"## Tech Stack (dependencies section):\n{tech_content[:4000]}\n"

    try:
        response = await llm_client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": EXTRACT_PROMPT},
                {"role": "user", "content": content},
            ],
            temperature=0.0,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content or ""

        # Parse JSON from response
        # Handle markdown code blocks
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]

        result = json.loads(raw.strip())
        return result
    except Exception as exc:
        logger.warning("  LLM extraction failed for %s: %s", repo_name, exc)
        return {"depends_on": [], "depended_by": []}


async def create_edges_in_neo4j(
    graph_store: GraphStore,
    repo_name: str,
    edges: dict[str, list[dict[str, str]]],
    dry_run: bool = False,
) -> int:
    """Create DEPENDS_ON edges in Neo4j from extracted dependencies."""
    created = 0
    source_id = f"service:{repo_name}"

    # Outgoing: this service depends on target
    for dep in edges.get("depends_on", []):
        target_name = dep.get("target", "").strip()
        if not target_name:
            continue

        target_id = f"service:{target_name}"
        dep_type = dep.get("type", "unknown")
        detail = dep.get("detail", "")

        if dry_run:
            logger.info("    [DRY] %s → %s (%s: %s)", repo_name, target_name, dep_type, detail)
            created += 1
            continue

        try:
            await graph_store.upsert_relationship(
                source_id=source_id,
                source_label=EntityType.SERVICE.value,
                target_id=target_id,
                target_label=EntityType.SERVICE.value,
                rel_type=RelationshipType.DEPENDS_ON.value,
                properties={
                    "dependency_type": dep_type,
                    "detail": detail,
                    "source": "steering_extraction",
                },
            )
            created += 1
        except Exception as exc:
            logger.debug("    Edge %s → %s failed: %s", repo_name, target_name, exc)

    # Incoming: source depends on this service
    for dep in edges.get("depended_by", []):
        source_name = dep.get("source", "").strip()
        if not source_name:
            continue

        dep_source_id = f"service:{source_name}"
        dep_type = dep.get("type", "unknown")
        detail = dep.get("detail", "")

        if dry_run:
            logger.info("    [DRY] %s → %s (%s: %s)", source_name, repo_name, dep_type, detail)
            created += 1
            continue

        try:
            await graph_store.upsert_relationship(
                source_id=dep_source_id,
                source_label=EntityType.SERVICE.value,
                target_id=source_id,
                target_label=EntityType.SERVICE.value,
                rel_type=RelationshipType.DEPENDS_ON.value,
                properties={
                    "dependency_type": dep_type,
                    "detail": detail,
                    "source": "steering_extraction",
                },
            )
            created += 1
        except Exception as exc:
            logger.debug("    Edge %s → %s failed: %s", source_name, repo_name, exc)

    return created


async def run(repo_filter: str | None = None, dry_run: bool = False) -> None:
    """Extract edges from all steering files and create in Neo4j."""
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    logger.info("=" * 60)
    logger.info("Extract DEPENDS_ON edges from Kiro steering files")
    logger.info("  Dry run: %s", dry_run)
    logger.info("=" * 60)

    # Find repos
    repos = sorted([
        d for d in KIRO_STEERING_DIR.iterdir()
        if d.is_dir() and any(d.glob("*.md"))
    ])

    if repo_filter:
        repos = [r for r in repos if r.name == repo_filter]
        if not repos:
            logger.error("Repo '%s' not found in kiro_steering/", repo_filter)
            return

    # Setup
    custom_http_client = httpx.AsyncClient(verify=False)
    llm_client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        http_client=custom_http_client,
    )
    deployment = settings.azure_openai_deployment_gpt4o

    graph_store = None
    if not dry_run:
        graph_store = GraphStore(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )
        await graph_store.connect()

    start = time.time()
    total_edges = 0

    try:
        for idx, repo_dir in enumerate(repos, 1):
            repo_name = repo_dir.name
            logger.info("[%d/%d] %s", idx, len(repos), repo_name)

            # Read steering files
            product_path = repo_dir / "product.md"
            tech_path = repo_dir / "tech.md"
            product = product_path.read_text(encoding="utf-8") if product_path.exists() else ""
            tech = tech_path.read_text(encoding="utf-8") if tech_path.exists() else ""

            if not product and not tech:
                logger.info("  No content, skipping")
                continue

            # Extract edges using LLM
            edges = await extract_edges_for_repo(repo_name, product, tech, llm_client, deployment)
            num_deps = len(edges.get("depends_on", [])) + len(edges.get("depended_by", []))

            if num_deps == 0:
                logger.info("  No dependencies found")
                continue

            logger.info("  Found %d edges", num_deps)

            # Create in Neo4j
            created = await create_edges_in_neo4j(graph_store, repo_name, edges, dry_run=dry_run)
            total_edges += created

            # Rate limit
            await asyncio.sleep(1)

    finally:
        await llm_client.close()
        if graph_store:
            await graph_store.close()

    elapsed = round(time.time() - start, 1)
    logger.info("")
    logger.info("=" * 60)
    logger.info("Done! Edges created: %d | Time: %.1fs", total_edges, elapsed)
    logger.info("=" * 60)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Extract DEPENDS_ON edges from steering files")
    parser.add_argument("--repo", type=str, help="Process only this repo")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without writing")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    asyncio.run(run(repo_filter=args.repo, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
