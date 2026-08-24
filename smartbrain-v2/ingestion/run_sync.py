"""One-shot manual sync CLI.

Run with:
    python -m src.ingestion.run_sync          # normal per-source fan-out
    python -m src.ingestion.run_sync --clean  # V2 three-phase clean ingest

Triggers a full sync across all configured MCP servers (GitHub, Jira,
Confluence) and prints a summary of what was ingested.

When ``--clean`` is passed, runs the V2 :class:`CleanIngestOrchestrator`
instead — a strict three-phase pipeline that populates fresh Neo4j and
Qdrant stores from steering files, Confluence, and Jira (Req 12.1, 12.4).

This is the quickest way to populate the graph for local testing
without waiting for the periodic scheduler.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from config.mcp_registry import load_mcp_registry
from config.settings import get_settings
from processing.embeddings.service import get_embedding_service
from processing.extraction.llm_extractor import get_llm_extractor
from processing.extraction.writer import GraphWriter
from ingestion.clients.confluence_client import ConfluenceHTTPClient
from ingestion.clients.github_client import GitHubHTTPClient
from ingestion.clients.jira_client import JiraHTTPClient
from ingestion.orchestrator import MCPOrchestrator
from storage.graph.graph_store import GraphStore
from storage.vector.vector_store import get_vector_store

logger = logging.getLogger(__name__)


async def run() -> None:
    """Execute a one-shot full sync."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    logger.info("=" * 60)
    logger.info("Engineering Memory Graph — Manual Full Sync")
    logger.info("=" * 60)

    # Load MCP registry
    registry = load_mcp_registry(settings.mcp_servers_config_path)
    logger.info("Loaded %d MCP server(s) from config", len(registry.servers))

    # Build the write pipeline
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

    # Build the orchestrator
    orchestrator = MCPOrchestrator(registry, writer, llm_extractor=llm_extractor)

    # Build and register clients from config
    github_config = next((s for s in registry.servers if s.name == "github"), None)
    if github_config:
        token = os.environ.get(github_config.config.get("token_env", ""), "")
        if not token:
            token = settings.github_token
        github_client = GitHubHTTPClient(
            token=token,
            org=github_config.config.get("org", ""),
            repos=github_config.config.get("repos", []),
        )
        orchestrator.register_github_client("github", github_client)
        logger.info(
            "Registered GitHub client: org=%s, repos=%d",
            github_config.config.get("org", ""),
            len(github_config.config.get("repos", [])),
        )

    jira_config = next((s for s in registry.servers if s.name == "jira"), None)
    if jira_config:
        token = os.environ.get(jira_config.config.get("token_env", ""), "")
        if not token:
            token = settings.jira_token
        jira_client = JiraHTTPClient(
            url=settings.jira_url,
            email=settings.jira_email,
            token=token,
            projects=jira_config.config.get("projects", []),
        )
        orchestrator.register_jira_client("jira", jira_client)
        logger.info(
            "Registered Jira client: projects=%s",
            jira_config.config.get("projects", []),
        )

    confluence_config = next((s for s in registry.servers if s.name == "confluence"), None)
    if confluence_config:
        token = os.environ.get(confluence_config.config.get("token_env", ""), "")
        if not token:
            token = settings.confluence_token
        confluence_client = ConfluenceHTTPClient(
            url=settings.confluence_url,
            email=settings.jira_email,  # same Atlassian account
            token=token,
            spaces=confluence_config.config.get("spaces", []),
            restricted_spaces=confluence_config.config.get("restricted_spaces"),
        )
        orchestrator.register_confluence_client("confluence", confluence_client)
        logger.info(
            "Registered Confluence client: spaces=%s, restricted_spaces=%d",
            confluence_config.config.get("spaces", []),
            len(confluence_config.config.get("restricted_spaces", []) or []),
        )

    # Run full sync — all sources in PARALLEL
    logger.info("")
    logger.info("Starting full sync (parallel across sources)...")
    start = time.time()

    # Run GitHub, Jira, and Confluence concurrently
    tasks = []
    task_names = []

    if "github" in [c for c in orchestrator._github_clients]:
        tasks.append(orchestrator.full_sync_github("github"))
        task_names.append("github:github")

    if "jira" in [c for c in orchestrator._jira_clients]:
        tasks.append(orchestrator.full_sync_jira("jira"))
        task_names.append("jira:jira")

    if "confluence" in [c for c in orchestrator._confluence_clients]:
        tasks.append(orchestrator.full_sync_confluence("confluence"))
        task_names.append("confluence:confluence")

    # Run all in parallel
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    results: dict[str, Any] = {}
    for name, result in zip(task_names, raw_results):
        if isinstance(result, Exception):
            logger.error("  %s FAILED: %s", name, result)
        else:
            results[name] = result

    elapsed = time.time() - start

    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Sync Results:")
    logger.info("-" * 60)
    for key, result in results.items():
        logger.info(
            "  %s: created=%d updated=%d skipped=%d",
            key,
            result.created_count,
            result.updated_count,
            result.skipped_count,
        )
    logger.info("-" * 60)
    logger.info("Full sync completed in %.1fs", elapsed)
    logger.info("=" * 60)

    await orchestrator.close()


async def run_clean(verbose: bool = False, start_phase: int | None = None, max_phase: int = 3, llm_ticket_limit: int = 100, source_filter: str | None = None) -> None:
    """Execute a V2 three-phase clean ingest (Req 12.1, 12.4).

    Constructs the full :class:`CleanIngestOrchestrator` with steering dir,
    available live clients, embedding/dedup/vector/BM25/graph pipeline, and
    runs the three-phase ingest. Logs the final report on completion.

    When ``verbose`` is False (default), all library logging is suppressed
    and only the progress bar is shown. Pass ``--verbose`` to see full logs.

    ``start_phase`` allows skipping completed phases (e.g., --phase 3 to
    only run LLM enrichment after Phase 1+2 already completed).

    ``llm_ticket_limit`` caps how many Jira tickets per project are sent
    through GPT-4o in Phase 3 (default 100). All tickets are still ingested.

    ``source_filter`` limits ingestion to a single source (steering, confluence,
    or jira). If None, all sources are processed.
    """

    from ingestion.clean_ingest import CleanIngestOrchestrator
    from ingestion.report import IngestionReport
    from processing.deduplication.dedup_service import DeduplicationService
    from storage.vector.sparse_index import LocalBM25Index

    settings = get_settings()

    if verbose:
        # Full logging — show everything
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    else:
        # Quiet mode — suppress all library logs, only progress bar prints
        logging.basicConfig(level=logging.CRITICAL)
        # Silence all noisy loggers
        for noisy in (
            "httpx", "httpcore", "neo4j", "neo4j.notifications",
            "processing", "storage", "ingestion", "config",
        ):
            logging.getLogger(noisy).setLevel(logging.CRITICAL)

    logger.info("=" * 60)
    logger.info("Engineering Memory Graph — V2 Clean Ingest")
    logger.info("=" * 60)

    # Build the write pipeline
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
    dedup_service = DeduplicationService(vector_store, graph_store)
    sparse_index = LocalBM25Index()

    # Steering directory — defaults to "kiro_steering" relative to CWD
    steering_dir = Path("kiro_steering")

    # Build live clients if credentials are available
    confluence_client: Any = None
    jira_client: Any = None

    registry = load_mcp_registry(settings.mcp_servers_config_path)

    confluence_config = next(
        (s for s in registry.servers if s.name == "confluence"), None
    )
    if confluence_config:
        token = os.environ.get(confluence_config.config.get("token_env", ""), "")
        if not token:
            token = settings.confluence_token
        if token and settings.confluence_url:
            confluence_client = ConfluenceHTTPClient(
                url=settings.confluence_url,
                email=settings.jira_email,
                token=token,
                spaces=confluence_config.config.get("spaces", []),
                restricted_spaces=confluence_config.config.get("restricted_spaces"),
            )

    jira_config = next((s for s in registry.servers if s.name == "jira"), None)
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

    # Build and run the orchestrator
    report = IngestionReport()
    orchestrator = CleanIngestOrchestrator(
        steering_dir=steering_dir,
        confluence_client=confluence_client,
        jira_client=jira_client,
        writer=writer,
        dedup_service=dedup_service,
        llm_extractor=llm_extractor,
        embedding_service=embedding_service,
        vector_store=vector_store,
        sparse_index=sparse_index,
        report=report,
        llm_ticket_limit=llm_ticket_limit,
        source_filter=source_filter,
    )

    start = time.time()
    start_dt = datetime.now()
    report = await orchestrator.run(start_phase=start_phase, max_phase=max_phase)
    elapsed = time.time() - start
    end_dt = datetime.now()

    # Always print the final summary (visible even in quiet mode)
    print("")
    print("=" * 60)
    print("Clean Ingest Results:")
    print("-" * 60)
    print(report.render())
    print("-" * 60)
    print(f"⏱  Start time:  {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱  End time:    {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱  Total:       {elapsed:.1f}s ({elapsed/60:.1f} min)")
    # Per-phase timings
    if hasattr(orchestrator, '_phase_timings') and orchestrator._phase_timings:
        print("")
        print("Phase Timings:")
        for phase_name, phase_elapsed in orchestrator._phase_timings.items():
            print(f"  {phase_name}: {phase_elapsed:.1f}s ({phase_elapsed/60:.1f} min)")
    print("=" * 60)


def main() -> None:
    """CLI entry point with --clean flag support."""
    parser = argparse.ArgumentParser(
        description="Engineering Memory Graph — one-shot sync CLI",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help=(
            "Run the V2 three-phase CleanIngestOrchestrator instead of the "
            "normal per-source fan-out. Populates fresh Neo4j + Qdrant stores "
            "from steering files, Confluence, and Jira."
        ),
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help=(
            "Show full debug logs alongside the progress bar. "
            "Without this flag, only the progress bar is displayed."
        ),
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help=(
            "Start from a specific phase (1=ingest, 2=deterministic, 3=LLM). "
            "Requires that prior phases have already completed. "
            "If not specified, runs all phases sequentially."
        ),
    )
    parser.add_argument(
        "--llm-ticket-limit",
        type=int,
        default=100,
        help=(
            "Max Jira tickets per project to send through LLM extraction "
            "in Phase 3. All tickets are still ingested in Phase 1. "
            "Default: 100 (most recent per project)."
        ),
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["steering", "confluence", "jira"],
        default=None,
        help=(
            "Only ingest a specific source. Useful when you only updated "
            "steering files and don't want to re-fetch confluence/jira. "
            "If not specified, all sources are processed."
        ),
    )
    parser.add_argument(
        "--max-phase",
        type=int,
        choices=[1, 2, 3],
        default=3,
        help=(
            "Stop after this phase. Use --max-phase 1 to only run "
            "Phase 1 (chunk + embed + write) without LLM enrichment."
        ),
    )
    args = parser.parse_args()

    if args.clean:
        asyncio.run(run_clean(
            verbose=args.verbose,
            start_phase=args.phase,
            max_phase=args.max_phase,
            llm_ticket_limit=args.llm_ticket_limit,
            source_filter=args.source,
        ))
    else:
        # Default: V2 pipeline (same as --clean)
        asyncio.run(run_clean(
            verbose=args.verbose,
            start_phase=args.phase,
            max_phase=args.max_phase,
            llm_ticket_limit=args.llm_ticket_limit,
            source_filter=args.source,
        ))


if __name__ == "__main__":
    main()
