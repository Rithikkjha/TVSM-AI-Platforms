"""Standalone Phase 3 runner — LLM enrichment only.

Skips Phase 1 (embedding + chunking) entirely. Reads the Known_Entity_Set
from Neo4j (services + tickets already materialized), loads steering file
texts from disk, fetches Jira tickets from the API (limited to most recent
N per project), and runs GPT-4o extraction to create DEPENDS_ON / LINKED_TO
edges in the graph.

Usage:
    python -m ingestion.run_phase3                    # default: 100 tickets/project
    python -m ingestion.run_phase3 --limit 50        # 50 tickets/project
    python -m ingestion.run_phase3 --limit 0         # steering only, skip jira
    python -m ingestion.run_phase3 --verbose         # show debug logs
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any

from config.settings import get_settings
from config.mcp_registry import load_mcp_registry
from processing.extraction.deterministic import ExtractionResult, ExtractedRelationship
from processing.extraction.llm_extractor import LLMExtractionError, get_llm_extractor
from processing.extraction.writer import GraphWriter
from processing.embeddings.service import get_embedding_service
from storage.graph.graph_store import GraphStore
from storage.vector.vector_store import get_vector_store
from ingestion.clients.jira_client import JiraHTTPClient

logger = logging.getLogger(__name__)

# Steering file types
_STEERING_FILE_TYPES = ("product", "structure", "tech")


async def run_phase3(ticket_limit: int = 100, verbose: bool = False) -> None:
    """Run Phase 3 LLM enrichment standalone."""

    settings = get_settings()

    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    else:
        logging.basicConfig(level=logging.CRITICAL)
        for noisy in ("httpx", "httpcore", "neo4j", "neo4j.notifications",
                      "processing", "storage", "ingestion", "config"):
            logging.getLogger(noisy).setLevel(logging.CRITICAL)

    # Connect to graph
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
    llm_extractor = get_llm_extractor(settings)

    # --- Build Known_Entity_Set from Neo4j ---
    print("📋 Loading Known_Entity_Set from Neo4j...", flush=True)

    # Get all service names
    async with graph_store._active_driver.session() as session:
        result = await session.run("MATCH (s:Service) WHERE s.deleted_at IS NULL RETURN s.name AS name")
        service_records = await result.data()

    known_services = sorted(set(
        r["name"] for r in service_records if r.get("name")
    ))

    # Get all ticket keys
    async with graph_store._active_driver.session() as session:
        result = await session.run("MATCH (t:Ticket) WHERE t.deleted_at IS NULL RETURN t.key AS key")
        ticket_records = await result.data()

    known_tickets = sorted(set(
        r["key"] for r in ticket_records if r.get("key")
    ))

    print(
        f"   Found {len(known_services)} services, {len(known_tickets)} tickets in graph",
        flush=True,
    )

    # --- Load steering docs from disk ---
    steering_dir = Path("kiro_steering")
    steering_docs: list[dict[str, Any]] = []

    if steering_dir.exists():
        repo_dirs = sorted(
            d for d in steering_dir.iterdir()
            if d.is_dir() and any(d.glob("*.md"))
        )
        for repo_dir in repo_dirs:
            repo_name = repo_dir.name
            for file_type in _STEERING_FILE_TYPES:
                md_file = repo_dir / f"{file_type}.md"
                if not md_file.exists():
                    continue
                content = md_file.read_text(encoding="utf-8")
                if not content.strip():
                    continue
                steering_docs.append({
                    "service_name": repo_name,
                    "service_source_id": f"service:{repo_name}",
                    "page_source_id": f"steering:{repo_name}:{file_type}",
                    "steering_text": content,
                })

    print(f"   Loaded {len(steering_docs)} steering docs from disk", flush=True)

    # --- Fetch Jira tickets (limited) ---
    jira_tickets: list[dict[str, Any]] = []

    if ticket_limit > 0:
        registry = load_mcp_registry(settings.mcp_servers_config_path)
        jira_config = next(
            (s for s in registry.servers if s.name == "jira"), None
        )
        if jira_config:
            token = os.environ.get(jira_config.config.get("token_env", ""), "")
            if not token:
                token = settings.jira_token
            if token and settings.jira_url:
                jira_client = JiraHTTPClient(
                    url=settings.jira_url,
                    email=settings.jira_email,
                    token=token,
                    projects=jira_config.config.get("projects", []),
                )
                projects = jira_config.config.get("projects", [])
                print(
                    f"   Fetching last {ticket_limit} tickets from {len(projects)} projects...",
                    flush=True,
                )
                for project_key in projects:
                    try:
                        issues = await jira_client.get_issues(project_key)
                        # Take only the most recent N (they come sorted by created desc)
                        issues = issues[:ticket_limit]
                        for issue in issues:
                            ticket_key = issue.get("key", "")
                            if not ticket_key:
                                continue
                            fields = issue.get("fields", {})
                            summary = fields.get("summary", "")
                            description = fields.get("description") or ""
                            if isinstance(description, dict):
                                # ADF format — extract text
                                description = _extract_adf_text(description)

                            ticket_text_parts = [f"[{ticket_key}] {summary}"]
                            if description:
                                ticket_text_parts.append(f"Description: {description}")

                            status_obj = fields.get("status")
                            if isinstance(status_obj, dict) and status_obj.get("name"):
                                ticket_text_parts.append(f"Status: {status_obj['name']}")

                            jira_tickets.append({
                                "ticket_source_id": f"jira:ticket:{ticket_key}",
                                "ticket_key": ticket_key,
                                "ticket_text": "\n".join(ticket_text_parts),
                            })
                    except Exception as exc:
                        print(f"   ⚠ Failed to fetch {project_key}: {exc}", flush=True)

        print(f"   Loaded {len(jira_tickets)} jira tickets (limited to {ticket_limit}/project)", flush=True)

    # --- Run Phase 3 ---
    total_items = len(steering_docs) + len(jira_tickets)
    print(
        f"\n🧠 Phase 3: LLM enrichment — {total_items} items "
        f"({len(steering_docs)} steering + {len(jira_tickets)} jira)\n",
        flush=True,
    )

    start = time.time()
    llm_idx = 0
    total_edges = 0

    # Steering extraction
    for doc_info in steering_docs:
        llm_idx += 1
        pct = llm_idx / total_items * 100 if total_items > 0 else 0
        try:
            result = await llm_extractor.extract_from_steering(
                service_source_id=doc_info["service_source_id"],
                service_name=doc_info["service_name"],
                steering_text=doc_info["steering_text"],
                page_source_id=doc_info["page_source_id"],
                known_services=known_services,
            )
            edges = len(result.relationships) if result.relationships else 0
            if result.relationships:
                await writer.write(result)
            total_edges += edges
            print(
                f"[{llm_idx:>{len(str(total_items))}}/{total_items}] "
                f"{pct:5.1f}%  llm/steering: {doc_info['service_name']} — {edges} edges",
                flush=True,
            )
        except LLMExtractionError as exc:
            print(
                f"[{llm_idx:>{len(str(total_items))}}/{total_items}] "
                f"{pct:5.1f}%  llm/steering: {doc_info['service_name']} — ⚠ failed: {exc}",
                flush=True,
            )
        except Exception as exc:
            print(
                f"[{llm_idx:>{len(str(total_items))}}/{total_items}] "
                f"{pct:5.1f}%  llm/steering: {doc_info['service_name']} — ⚠ error: {exc}",
                flush=True,
            )

    # Jira extraction
    for ticket_info in jira_tickets:
        llm_idx += 1
        pct = llm_idx / total_items * 100 if total_items > 0 else 0
        try:
            result = await llm_extractor.extract_from_jira_ticket(
                ticket_source_id=ticket_info["ticket_source_id"],
                ticket_key=ticket_info["ticket_key"],
                ticket_text=ticket_info["ticket_text"],
                known_services=known_services,
                known_tickets=known_tickets,
            )
            edges = len(result.relationships) if result.relationships else 0
            if result.relationships:
                await writer.write(result)
            total_edges += edges
            print(
                f"[{llm_idx:>{len(str(total_items))}}/{total_items}] "
                f"{pct:5.1f}%  llm/jira: {ticket_info['ticket_key']} — {edges} edges",
                flush=True,
            )
        except LLMExtractionError as exc:
            print(
                f"[{llm_idx:>{len(str(total_items))}}/{total_items}] "
                f"{pct:5.1f}%  llm/jira: {ticket_info['ticket_key']} — ⚠ failed: {exc}",
                flush=True,
            )
        except Exception as exc:
            print(
                f"[{llm_idx:>{len(str(total_items))}}/{total_items}] "
                f"{pct:5.1f}%  llm/jira: {ticket_info['ticket_key']} — ⚠ error: {exc}",
                flush=True,
            )

    elapsed = time.time() - start
    print(f"\n✅ Phase 3 complete: {llm_idx} items processed, {total_edges} edges created in {elapsed:.1f}s", flush=True)


def _extract_adf_text(adf: dict[str, Any]) -> str:
    """Recursively extract plain text from Atlassian Document Format."""
    parts: list[str] = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text":
                parts.append(node.get("text", ""))
            for child in node.get("content", []):
                _walk(child)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(adf)
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Phase 3 (LLM enrichment) standalone — skips Phase 1 entirely",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max tickets per Jira project to send through LLM (default: 100, 0 = skip jira)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show debug logs",
    )
    args = parser.parse_args()

    asyncio.run(run_phase3(ticket_limit=args.limit, verbose=args.verbose))


if __name__ == "__main__":
    main()
