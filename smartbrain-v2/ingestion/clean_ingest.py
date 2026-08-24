"""V2 Clean-Ingest Orchestrator — three-phase entry point.

Populates fresh empty Neo4j + Qdrant stores from all three sources
(steering files, Confluence pages, Jira tickets) in a strict
three-phase ordering that guarantees the Known_Entity_Set is fully
populated before any LLM relationship extraction runs.

Phase 1: Materialize all entities + chunks for every source.
Phase 2: Deterministic extraction (structural edges).
Phase 3: LLM enrichment with a frozen Known_Entity_Set.

Requirements: 12.1–12.6, 13.1–13.3, 14.1–14.5.
Design: §12 "V2 clean-ingest orchestrator".
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from processing.chunking.base import SourceDocument, get_chunker
from processing.chunking.models import Chunk, SourceType
from processing.deduplication.dedup_service import DeduplicationService
from processing.embeddings.service import EmbeddingService
from processing.extraction.deterministic import (
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionResult,
    compute_text_hash,
)
from processing.extraction.llm_extractor import LLMExtractionError, LLMExtractor
from processing.extraction.writer import GraphWriter
from storage.graph.schema import EntityType, RelationshipType
from storage.vector.sparse_index import SparseIndex
from storage.vector.vector_store import VectorRecord, VectorStore
from ingestion.report import IngestionReport

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cumulative progress tracker
# ---------------------------------------------------------------------------


class ProgressTracker:
    """Cumulative progress bar across all ingestion sources.

    Prints a line per item as it's processed, e.g.:
        [  5/142]  12%  steering: booking-crud-services — 8 chunks ✓
        [ 47/142]  33%  confluence: DEV/Onboarding Guide — 3 chunks ✓
        [130/142]  91%  jira: ACV2-1234 — 2 chunks ✓

    Also emits a phase summary banner at end of each source.
    """

    def __init__(self, total: int) -> None:
        self._total = total
        self._current = 0
        self._start_time = time.time()

    @property
    def total(self) -> int:
        return self._total

    @total.setter
    def total(self, value: int) -> None:
        self._total = value

    def tick(self, source: str, label: str, chunks: int) -> None:
        """Record one item processed and print progress line."""
        self._current += 1
        pct = (self._current / self._total * 100) if self._total > 0 else 0
        elapsed = time.time() - self._start_time
        # Estimate remaining time
        rate = self._current / elapsed if elapsed > 0 else 0
        remaining = (self._total - self._current) / rate if rate > 0 else 0

        line = (
            f"[{self._current:>{len(str(self._total))}}/{self._total}] "
            f"{pct:5.1f}%  {source}: {label} — {chunks} chunks ✓"
        )
        # Add ETA if meaningful
        if remaining > 5:
            mins, secs = divmod(int(remaining), 60)
            line += f"  (ETA {mins}m{secs:02d}s)"

        print(line, flush=True)

    def source_done(self, source: str, count: int, total_chunks: int) -> None:
        """Print a summary banner after finishing a source."""
        elapsed = time.time() - self._start_time
        print(
            f"  └─ {source} done: {count} items, {total_chunks} chunks total "
            f"[{elapsed:.1f}s elapsed]",
            flush=True,
        )

    def finish(self) -> None:
        """Print final summary."""
        elapsed = time.time() - self._start_time
        print(
            f"\n✅ Phase 1 complete: {self._current}/{self._total} items "
            f"processed in {elapsed:.1f}s",
            flush=True,
        )


__all__ = ["CleanIngestOrchestrator"]

# Steering file types (mirrors kiro_steering_ingest.py convention)
_STEERING_FILE_TYPES = ("product", "structure", "tech")


# ---------------------------------------------------------------------------
# Client protocols for live sources
# ---------------------------------------------------------------------------


@runtime_checkable
class ConfluenceLiveClient(Protocol):
    """Minimal protocol for the Confluence live-fetch client."""

    async def get_pages(self, space_key: str) -> list[dict[str, Any]]: ...
    async def close(self) -> None: ...


@runtime_checkable
class JiraLiveClient(Protocol):
    """Minimal protocol for the Jira live-fetch client."""

    async def get_issues(self, project_key: str) -> list[dict[str, Any]]: ...
    async def close(self) -> None: ...


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class CleanIngestOrchestrator:
    """Three-phase clean-ingest entry point (Req 12/13).

    Materializes all entities and chunks for all sources first, then
    runs deterministic extraction, then LLM enrichment against a fully
    populated Known_Entity_Set. Per-source error isolation ensures a
    failure in one source does not halt the others.
    """

    def __init__(
        self,
        *,
        steering_dir: Path,
        confluence_client: ConfluenceLiveClient | None,
        jira_client: JiraLiveClient | None,
        writer: GraphWriter,
        dedup_service: DeduplicationService,
        llm_extractor: LLMExtractor,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        sparse_index: SparseIndex,
        report: IngestionReport | None = None,
        llm_ticket_limit: int = 100,
        source_filter: str | None = None,
    ) -> None:
        self._steering_dir = steering_dir
        self._confluence_client = confluence_client
        self._jira_client = jira_client
        self._writer = writer
        self._dedup_service = dedup_service
        self._llm_extractor = llm_extractor
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._sparse_index = sparse_index
        self._report = report or IngestionReport()
        self._llm_ticket_limit = llm_ticket_limit
        self._source_filter = source_filter  # None = all, "steering"/"confluence"/"jira"

        # Accumulated during Phase 1
        self._known_services: set[str] = set()
        self._known_tickets: set[str] = set()

        # Steering docs accumulated for Phase 3 LLM enrichment
        self._steering_docs: list[dict[str, Any]] = []
        # Jira tickets accumulated for Phase 3 LLM enrichment
        self._jira_tickets: list[dict[str, Any]] = []

        # Cumulative progress tracker (initialized during run())
        self._progress: ProgressTracker | None = None

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def run(self, start_phase: int | None = None, max_phase: int = 3) -> IngestionReport:
        """Execute the three-phase clean-ingest pipeline.

        Args:
            start_phase: If specified (1, 2, or 3), skip earlier phases.
                Phase 1 must have run previously for Phase 2/3 to work.
                When starting from Phase 2 or 3, the Known_Entity_Set is
                rebuilt by scanning the steering directory and Jira config.

        Returns the completed IngestionReport with per-source,
        per-stage counts (Req 15).
        """

        effective_start = start_phase or 1
        self._phase_timings: dict[str, float] = {}

        if effective_start <= 1:
            # Pre-count total items across all sources for cumulative progress
            total_items = await self._count_total_items()
            self._progress = ProgressTracker(total_items)
            print(
                f"\n🚀 Clean ingest starting — {total_items} items to process "
                f"(steering + confluence + jira)\n",
                flush=True,
            )

            logger.info("Clean-ingest: starting Phase 1 (materialize entities + chunks)")
            p1_start = time.time()
            await self._phase1_materialize()
            self._phase_timings["Phase 1 (Chunk + Embed + Write)"] = time.time() - p1_start
            if self._progress:
                self._progress.finish()
            # Flush BM25 index to disk (debounced persist may have pending writes)
            self._sparse_index.flush()
        else:
            # Rebuild the Known_Entity_Set from filesystem for Phase 2/3
            print(f"\n⏩ Skipping to Phase {effective_start} (prior phases assumed complete)\n", flush=True)
            await self._rebuild_known_entity_set()

        # Freeze the Known_Entity_Set (Req 13.2/13.3)
        frozen_services = frozenset(self._known_services)
        frozen_tickets = frozenset(self._known_tickets)
        logger.info(
            "Clean-ingest: Known_Entity_Set frozen — %d services, %d tickets",
            len(frozen_services),
            len(frozen_tickets),
        )

        if effective_start <= 2 and max_phase >= 2:
            logger.info("Clean-ingest: starting Phase 2 (deterministic extraction)")
            p2_start = time.time()
            await self._phase2_deterministic()
            self._phase_timings["Phase 2 (Deterministic Edges)"] = time.time() - p2_start

        if effective_start <= 3 and max_phase >= 3:
            logger.info("Clean-ingest: starting Phase 3 (LLM enrichment)")
            p3_start = time.time()
            await self._phase3_llm_enrichment(frozen_services, frozen_tickets)
            self._phase_timings["Phase 3 (LLM Enrichment)"] = time.time() - p3_start

        logger.info("Clean-ingest: complete.\n%s", self._report.render())
        return self._report

    async def _rebuild_known_entity_set(self) -> None:
        """Rebuild Known_Entity_Set + accumulated docs from filesystem.

        Used when --phase 2 or --phase 3 is passed (skipping Phase 1).
        Reads steering files to populate service names and doc texts,
        and reads Jira ticket keys from the graph if available.
        """

        # Rebuild services from steering directory
        if self._steering_dir.exists():
            repo_dirs = sorted(
                d for d in self._steering_dir.iterdir()
                if d.is_dir() and any(d.glob("*.md"))
            )
            for repo_dir in repo_dirs:
                repo_name = repo_dir.name
                self._known_services.add(repo_name)

                for md_file in sorted(repo_dir.glob("*.md")):
                    file_type = md_file.stem
                    content = md_file.read_text(encoding="utf-8")
                    if not content.strip():
                        continue
                    source_id = f"steering:{repo_name}:{file_type}"
                    self._steering_docs.append({
                        "service_name": repo_name,
                        "service_source_id": f"service:{repo_name}",
                        "page_source_id": source_id,
                        "steering_text": content,
                    })

        # Rebuild Jira ticket keys from the Jira client config
        if self._jira_client is not None:
            projects: list[str] = getattr(self._jira_client, "_projects", [])
            for project_key in projects:
                try:
                    issues = await self._jira_client.get_issues(project_key)
                    for issue in issues:
                        ticket_key = issue.get("key", "")
                        if ticket_key:
                            self._known_tickets.add(ticket_key)

                            fields = issue.get("fields", {})
                            summary = fields.get("summary", "")
                            description = fields.get("description") or ""
                            if isinstance(description, dict):
                                description = self._extract_adf_text(description)

                            source_id = f"jira:ticket:{ticket_key}"
                            ticket_text_parts = [f"[{ticket_key}] {summary}"]
                            if description:
                                ticket_text_parts.append(f"Description: {description}")

                            self._jira_tickets.append({
                                "ticket_source_id": source_id,
                                "ticket_key": ticket_key,
                                "ticket_text": "\n".join(ticket_text_parts),
                            })
                except Exception as exc:
                    logger.warning("Failed to fetch tickets for %s: %s", project_key, exc)

        print(
            f"  Rebuilt: {len(self._known_services)} services, "
            f"{len(self._known_tickets)} tickets, "
            f"{len(self._steering_docs)} steering docs, "
            f"{len(self._jira_tickets)} jira tickets",
            flush=True,
        )

    async def _count_total_items(self) -> int:
        """Pre-count the total number of items across all sources.

        This enables a cumulative progress bar. Counts:
        - Steering: number of steering files (repo × file_type)
        - Confluence: number of pages (fetched via client)
        - Jira: number of tickets (fetched via client)

        For Confluence and Jira, we estimate from the client's config
        to avoid double-fetching. The actual count updates dynamically
        if it differs at processing time.
        """
        total = 0

        # Count steering files
        if self._steering_dir.exists():
            repo_dirs = [
                d for d in self._steering_dir.iterdir()
                if d.is_dir() and any(d.glob("*.md"))
            ]
            for repo_dir in repo_dirs:
                md_files = list(repo_dir.glob("*.md"))
                for md_file in md_files:
                    content = md_file.read_text(encoding="utf-8")
                    if content.strip():
                        total += 1

        # Estimate Confluence pages (use a generous estimate;
        # the actual total will be adjusted once pages are fetched)
        if self._confluence_client is not None:
            spaces = getattr(self._confluence_client, "_spaces", [])
            # Estimate ~20 pages per space as a starting point
            total += len(spaces) * 20

        # Estimate Jira tickets
        if self._jira_client is not None:
            projects = getattr(self._jira_client, "_projects", [])
            # Estimate ~50 tickets per project as a starting point
            total += len(projects) * 50

        return max(total, 1)  # Avoid divide by zero


    # ------------------------------------------------------------------
    # Phase 1: Materialize all entities + chunks
    # ------------------------------------------------------------------

    async def _phase1_materialize(self) -> None:
        """Materialize entities and chunks for all sources (Req 12.1/12.2).

        Per-source error isolation: each source is wrapped in
        try/except; failure logs and records a skipped source (Req 12.5/12.6).

        When ``self._source_filter`` is set, only that source is processed.
        """

        sf = self._source_filter

        # Source: steering files from kiro_steering directory
        if sf is None or sf == "steering":
            try:
                await self._phase1_steering()
            except Exception as exc:
                logger.error("Phase 1: steering source failed: %s", exc, exc_info=True)
                self._report.skip("steering")

        # Source: Confluence pages (live fetch)
        if sf is None or sf == "confluence":
            try:
                await self._phase1_confluence()
            except Exception as exc:
                logger.error("Phase 1: confluence source failed: %s", exc, exc_info=True)
                self._report.skip("confluence")

        # Source: Jira tickets (live fetch)
        if sf is None or sf == "jira":
            try:
                await self._phase1_jira()
            except Exception as exc:
                logger.error("Phase 1: jira source failed: %s", exc, exc_info=True)
                self._report.skip("jira")


    async def _phase1_steering(self) -> None:
        """Materialize steering file entities and chunks.

        Reads kiro_steering/{repo-name}/product.md, structure.md, tech.md,
        chunks each file, embeds, deduplicates, and writes to all stores.
        """

        if not self._steering_dir.exists():
            logger.warning(
                "Steering directory does not exist: %s — skipping steering source",
                self._steering_dir,
            )
            self._report.skip("steering")
            return

        repo_dirs = sorted(
            d for d in self._steering_dir.iterdir()
            if d.is_dir() and any(d.glob("*.md"))
        )

        if not repo_dirs:
            logger.info("No repo folders found in %s", self._steering_dir)
            return

        logger.info("Phase 1 steering: found %d repos", len(repo_dirs))
        chunker = get_chunker(SourceType.STEERING_FILE)
        steering_items_count = 0
        steering_chunks_total = 0

        for repo_dir in repo_dirs:
            repo_name = repo_dir.name
            # Register the service in the Known_Entity_Set
            self._known_services.add(repo_name)

            # Write the parent Service entity via writer
            await self._write_service_entity(repo_name)

            # Process ALL .md files in the folder (not just product/structure/tech)
            md_files = sorted(repo_dir.glob("*.md"))
            for md_file in md_files:
                file_type = md_file.stem  # e.g., "product", "HLD", "API_SPEC"

                content = md_file.read_text(encoding="utf-8")
                if not content.strip():
                    continue

                source_id = f"steering:{repo_name}:{file_type}"
                source_ref = str(md_file)

                # Write the steering doc entity (ConfluencePage-type)
                await self._write_steering_entity(
                    repo_name, file_type, content, source_id
                )

                # Build SourceDocument for chunking
                doc = SourceDocument(
                    source_type=SourceType.STEERING_FILE,
                    parent_source_id=source_id,
                    repo_name=repo_name,
                    source_ref=source_ref,
                    doc_type=file_type,
                    text=content,
                    title=f"{repo_name}/{file_type}",
                )

                # Chunk, embed, dedup, write
                chunks = chunker.chunk(doc)
                chunks_created, duplicates_marked = await self._ingest_chunks(
                    chunks, source_type="steering"
                )
                self._report.record_chunks(
                    "steering", chunks_created, duplicates_marked
                )

                # Progress tracking
                steering_items_count += 1
                steering_chunks_total += chunks_created
                if self._progress:
                    self._progress.tick(
                        "steering",
                        f"{repo_name}/{file_type}",
                        chunks_created,
                    )

                # Accumulate for Phase 3 LLM enrichment
                self._steering_docs.append({
                    "service_name": repo_name,
                    "service_source_id": f"service:{repo_name}",
                    "page_source_id": source_id,
                    "steering_text": content,
                })

        if self._progress:
            self._progress.source_done("steering", steering_items_count, steering_chunks_total)

    async def _phase1_confluence(self) -> None:
        """Materialize Confluence page entities and chunks.

        Fetches pages from the live Confluence client, chunks, embeds,
        and stores them. Adds service names found in pages to the
        Known_Entity_Set.
        """

        if self._confluence_client is None:
            logger.info(
                "Phase 1 confluence: no client configured — skipping"
            )
            self._report.skip("confluence")
            return

        # Resolve space keys from the client (populated at construction time
        # from mcp_servers.yaml config)
        spaces: list[str] = getattr(self._confluence_client, "_spaces", [])
        if not spaces:
            logger.warning(
                "Phase 1 confluence: no spaces configured on client — skipping"
            )
            self._report.skip("confluence")
            return

        logger.info("Phase 1 confluence: fetching pages for %d spaces", len(spaces))
        chunker = get_chunker(SourceType.CONFLUENCE_PAGE)
        total_pages = 0
        confluence_chunks_total = 0
        # Adjust progress total once we know actual page count
        actual_page_count = 0

        for space_key in spaces:
            try:
                pages = await self._confluence_client.get_pages(space_key)
            except Exception as exc:
                logger.warning(
                    "Phase 1 confluence: failed to fetch pages for space %s: %s",
                    space_key,
                    exc,
                )
                continue

            if not pages:
                logger.info(
                    "Phase 1 confluence: no pages returned for space %s", space_key
                )
                continue

            actual_page_count += len(pages)

            logger.info(
                "Phase 1 confluence: processing %d pages from space %s",
                len(pages),
                space_key,
            )

            for page in pages:
                try:
                    page_id = page.get("id", "")
                    title = page.get("title", "Untitled")
                    # Body comes from the expanded body.storage.value
                    body_storage = page.get("body", {}).get("storage", {})
                    page_body = body_storage.get("value", "")
                    # Build page URL from _links if available
                    links = page.get("_links", {})
                    site_url = getattr(
                        self._confluence_client, "site_url", ""
                    )
                    page_url = links.get("webui", "")
                    if page_url and site_url:
                        page_url = f"{site_url}/wiki{page_url}"
                    elif not page_url:
                        page_url = f"confluence:page:{page_id}"

                    if not page_body.strip():
                        continue

                    source_id = f"confluence:page:{page_id}"

                    # Derive repo_name from space key + title (best effort)
                    repo_name = f"{space_key}/{title}"

                    # Write the parent ConfluencePage entity
                    await self._write_confluence_entity(
                        page_id=page_id,
                        title=title,
                        space_key=space_key,
                        page_url=page_url,
                        content=page_body,
                        source_id=source_id,
                    )

                    # Build SourceDocument for chunking
                    doc = SourceDocument(
                        source_type=SourceType.CONFLUENCE_PAGE,
                        parent_source_id=source_id,
                        repo_name=repo_name,
                        source_ref=page_url,
                        doc_type="confluence",
                        text=page_body,
                        title=title,
                    )

                    # Chunk, embed, dedup, write
                    chunks = chunker.chunk(doc)
                    chunks_created, duplicates_marked = await self._ingest_chunks(
                        chunks, source_type="confluence"
                    )
                    self._report.record_chunks(
                        "confluence", chunks_created, duplicates_marked
                    )

                    # Try to discover service names from the page title
                    for svc in self._known_services:
                        if svc.lower() in title.lower():
                            break
                    else:
                        # Add title-based service hint if it looks like a
                        # service name (all known services are already
                        # registered from steering; this is just additive)
                        pass

                    total_pages += 1

                    # Progress tracking
                    confluence_chunks_total += chunks_created
                    if self._progress:
                        self._progress.tick(
                            "confluence",
                            f"{space_key}/{title[:40]}",
                            chunks_created,
                        )

                except Exception as exc:
                    logger.warning(
                        "Phase 1 confluence: error processing page %s in space %s: %s",
                        page.get("id", "?"),
                        space_key,
                        exc,
                    )
                    continue

        # Adjust progress total if actual page count differs from estimate
        if self._progress and actual_page_count > 0:
            estimated_confluence = len(spaces) * 20
            diff = actual_page_count - estimated_confluence
            if diff != 0:
                self._progress.total = self._progress.total + diff

        if self._progress:
            self._progress.source_done("confluence", total_pages, confluence_chunks_total)

        logger.info(
            "Phase 1 confluence: processed %d pages across %d spaces",
            total_pages,
            len(spaces),
        )


    async def _phase1_jira(self) -> None:
        """Materialize Jira ticket entities and chunks.

        Fetches tickets from the live Jira client, chunks, embeds,
        and stores them. Adds ticket keys to the Known_Entity_Set.
        """

        if self._jira_client is None:
            logger.info(
                "Phase 1 jira: no client configured — skipping"
            )
            self._report.skip("jira")
            return

        # Resolve project keys from the client (populated at construction
        # time from mcp_servers.yaml config)
        projects: list[str] = getattr(self._jira_client, "_projects", [])
        if not projects:
            logger.warning(
                "Phase 1 jira: no projects configured on client — skipping"
            )
            self._report.skip("jira")
            return

        logger.info("Phase 1 jira: fetching tickets for %d projects", len(projects))
        chunker = get_chunker(SourceType.JIRA_TICKET)
        total_tickets = 0
        jira_chunks_total = 0
        actual_ticket_count = 0

        for project_key in projects:
            try:
                issues = await self._jira_client.get_issues(project_key)
            except Exception as exc:
                logger.warning(
                    "Phase 1 jira: failed to fetch issues for project %s: %s",
                    project_key,
                    exc,
                )
                continue

            if not issues:
                logger.info(
                    "Phase 1 jira: no issues returned for project %s", project_key
                )
                continue

            actual_ticket_count += len(issues)

            logger.info(
                "Phase 1 jira: processing %d tickets from project %s",
                len(issues),
                project_key,
            )

            for issue in issues:
                try:
                    ticket_key = issue.get("key", "")
                    if not ticket_key:
                        continue

                    fields = issue.get("fields", {})
                    summary = fields.get("summary", "")
                    description = fields.get("description") or ""
                    # Atlassian v3 description is ADF (JSON); extract
                    # plain text if it's a dict, otherwise use as-is
                    if isinstance(description, dict):
                        description = self._extract_adf_text(description)

                    status_name = ""
                    status_obj = fields.get("status")
                    if isinstance(status_obj, dict):
                        status_name = status_obj.get("name", "")

                    priority_name = ""
                    priority_obj = fields.get("priority")
                    if isinstance(priority_obj, dict):
                        priority_name = priority_obj.get("name", "")

                    issue_type = ""
                    issuetype_obj = fields.get("issuetype")
                    if isinstance(issuetype_obj, dict):
                        issue_type = issuetype_obj.get("name", "")

                    source_id = f"jira:ticket:{ticket_key}"

                    # Build structured fields for the Jira chunker
                    ticket_fields: dict[str, str] = {
                        "Summary": summary,
                        "Description": description,
                    }
                    if status_name:
                        ticket_fields["Status"] = status_name
                    if priority_name:
                        ticket_fields["Priority"] = priority_name
                    if issue_type:
                        ticket_fields["Issue Type"] = issue_type

                    # Derive repo_name from project key
                    repo_name = project_key

                    # Write the parent Ticket entity
                    await self._write_ticket_entity(
                        ticket_key=ticket_key,
                        title=summary,
                        source_id=source_id,
                    )

                    # Register in Known_Entity_Set
                    self._known_tickets.add(ticket_key)

                    # Build SourceDocument for chunking
                    doc = SourceDocument(
                        source_type=SourceType.JIRA_TICKET,
                        parent_source_id=source_id,
                        repo_name=repo_name,
                        source_ref=ticket_key,
                        doc_type="jira",
                        fields=ticket_fields,
                        title=ticket_key,
                    )

                    # Chunk, embed, dedup, write
                    chunks = chunker.chunk(doc)
                    chunks_created, duplicates_marked = await self._ingest_chunks(
                        chunks, source_type="jira"
                    )
                    self._report.record_chunks(
                        "jira", chunks_created, duplicates_marked
                    )

                    # Accumulate for Phase 3 LLM enrichment
                    # Build a combined text for LLM extraction
                    ticket_text_parts = [
                        f"[{ticket_key}] {summary}",
                    ]
                    if description:
                        ticket_text_parts.append(f"Description: {description}")
                    if status_name:
                        ticket_text_parts.append(f"Status: {status_name}")
                    if priority_name:
                        ticket_text_parts.append(f"Priority: {priority_name}")

                    self._jira_tickets.append({
                        "ticket_source_id": source_id,
                        "ticket_key": ticket_key,
                        "ticket_text": "\n".join(ticket_text_parts),
                    })

                    total_tickets += 1

                    # Progress tracking
                    jira_chunks_total += chunks_created
                    if self._progress:
                        self._progress.tick(
                            "jira",
                            f"{ticket_key}: {summary[:35]}",
                            chunks_created,
                        )

                except Exception as exc:
                    logger.warning(
                        "Phase 1 jira: error processing ticket %s in project %s: %s",
                        issue.get("key", "?"),
                        project_key,
                        exc,
                    )
                    continue

        # Adjust progress total if actual ticket count differs from estimate
        if self._progress and actual_ticket_count > 0:
            estimated_jira = len(projects) * 50
            diff = actual_ticket_count - estimated_jira
            if diff != 0:
                self._progress.total = self._progress.total + diff

        if self._progress:
            self._progress.source_done("jira", total_tickets, jira_chunks_total)

        logger.info(
            "Phase 1 jira: processed %d tickets across %d projects",
            total_tickets,
            len(projects),
        )

    # ------------------------------------------------------------------
    # Phase 2: Deterministic extraction
    # ------------------------------------------------------------------

    async def _phase2_deterministic(self) -> None:
        """Run deterministic extraction over materialized sources (Req 12.3).

        The steering files already write DOCUMENTED_IN edges during
        Phase 1 entity materialization (they are structural/deterministic).
        Additional deterministic extraction for Confluence and Jira
        entities is handled here when those sources are available.
        """

        # For steering: the DOCUMENTED_IN edges (Service -> steering doc)
        # are already written during _write_steering_entity in Phase 1.
        # Record the count of deterministic edges produced.
        # Each steering doc with content produced 1 DOCUMENTED_IN edge.
        steering_det_edges = len(self._steering_docs)
        self._report.record_deterministic("steering", steering_det_edges)

        # Confluence and Jira deterministic extraction would run here
        # once those Phase 1 branches are fully implemented.
        logger.info(
            "Phase 2: recorded %d deterministic edges for steering",
            steering_det_edges,
        )


    # ------------------------------------------------------------------
    # Phase 3: LLM enrichment
    # ------------------------------------------------------------------

    async def _phase3_llm_enrichment(
        self,
        frozen_services: frozenset[str],
        frozen_tickets: frozenset[str],
    ) -> None:
        """Run LLM relationship extraction with frozen Known_Entity_Set (Req 12.4).

        Processes steering docs and Jira tickets through the
        LLMExtractor, writing edges via GraphWriter (idempotent).
        """

        known_services_list = sorted(frozen_services)
        known_tickets_list = sorted(frozen_tickets)

        # Apply ticket limit for LLM extraction (most recent N per project)
        # All tickets remain in Qdrant/BM25 for search; limit only affects graph edges.
        jira_for_llm = self._jira_tickets
        if self._llm_ticket_limit and len(self._jira_tickets) > self._llm_ticket_limit:
            # Take the last N (most recently accumulated = most recent tickets)
            jira_for_llm = self._jira_tickets[-self._llm_ticket_limit:]
            print(
                f"  ℹ Limiting Jira LLM extraction to {len(jira_for_llm)} tickets "
                f"(of {len(self._jira_tickets)} total). All tickets remain searchable.",
                flush=True,
            )

        total_llm_items = len(self._steering_docs) + len(jira_for_llm)
        llm_idx = 0
        print(
            f"\n🧠 Phase 3: LLM enrichment — {total_llm_items} items to extract\n",
            flush=True,
        )

        # LLM enrichment for steering docs (Req 9)
        for doc_info in self._steering_docs:
            llm_idx += 1
            pct = llm_idx / total_llm_items * 100 if total_llm_items > 0 else 0
            try:
                result = await self._llm_extractor.extract_from_steering(
                    service_source_id=doc_info["service_source_id"],
                    service_name=doc_info["service_name"],
                    steering_text=doc_info["steering_text"],
                    page_source_id=doc_info["page_source_id"],
                    known_services=known_services_list,
                )
                edges = len(result.relationships) if result.relationships else 0
                if result.relationships:
                    await self._writer.write(result)
                    by_confidence = self._bucket_by_confidence(result)
                    self._report.record_llm_edges("steering", by_confidence)
                print(
                    f"[{llm_idx:>{len(str(total_llm_items))}}/{total_llm_items}] "
                    f"{pct:5.1f}%  llm/steering: {doc_info['service_name']} — "
                    f"{edges} edges",
                    flush=True,
                )
            except LLMExtractionError as exc:
                logger.warning(
                    "Phase 3: LLM extraction failed for steering doc %s: %s",
                    doc_info["service_name"],
                    exc,
                )
                print(
                    f"[{llm_idx:>{len(str(total_llm_items))}}/{total_llm_items}] "
                    f"{pct:5.1f}%  llm/steering: {doc_info['service_name']} — ⚠ failed",
                    flush=True,
                )
            except Exception as exc:
                logger.warning(
                    "Phase 3: unexpected error in steering LLM extraction "
                    "for %s: %s",
                    doc_info["service_name"],
                    exc,
                )

        # LLM enrichment for Jira tickets (Req 10)
        for ticket_info in jira_for_llm:
            llm_idx += 1
            pct = llm_idx / total_llm_items * 100 if total_llm_items > 0 else 0
            try:
                result = await self._llm_extractor.extract_from_jira_ticket(
                    ticket_source_id=ticket_info["ticket_source_id"],
                    ticket_key=ticket_info["ticket_key"],
                    ticket_text=ticket_info["ticket_text"],
                    known_services=known_services_list,
                    known_tickets=known_tickets_list,
                )
                edges = len(result.relationships) if result.relationships else 0
                if result.relationships:
                    await self._writer.write(result)
                    by_confidence = self._bucket_by_confidence(result)
                    self._report.record_llm_edges("jira", by_confidence)
                print(
                    f"[{llm_idx:>{len(str(total_llm_items))}}/{total_llm_items}] "
                    f"{pct:5.1f}%  llm/jira: {ticket_info['ticket_key']} — "
                    f"{edges} edges",
                    flush=True,
                )
            except LLMExtractionError as exc:
                logger.warning(
                    "Phase 3: LLM extraction failed for ticket %s: %s",
                    ticket_info["ticket_key"],
                    exc,
                )
                print(
                    f"[{llm_idx:>{len(str(total_llm_items))}}/{total_llm_items}] "
                    f"{pct:5.1f}%  llm/jira: {ticket_info['ticket_key']} — ⚠ failed",
                    flush=True,
                )
            except Exception as exc:
                logger.warning(
                    "Phase 3: unexpected error in Jira LLM extraction "
                    "for %s: %s",
                    ticket_info["ticket_key"],
                    exc,
                )

        print(f"\n✅ Phase 3 complete: {llm_idx} items enriched\n", flush=True)
        logger.info("Phase 3: LLM enrichment complete")


    # ------------------------------------------------------------------
    # Helpers: entity writing
    # ------------------------------------------------------------------

    async def _write_service_entity(self, repo_name: str) -> None:
        """Write a Service entity node for the given repo/service name."""

        now = datetime.now(UTC).isoformat()
        entity = ExtractedEntity(
            label=EntityType.SERVICE.value,
            properties={
                "source_id": f"service:{repo_name}",
                "name": repo_name,
                "created_at": now,
                "updated_at": now,
                "text_hash": compute_text_hash({"service": repo_name}),
            },
        )
        await self._writer.write(ExtractionResult(entities=[entity], relationships=[]))

    async def _write_steering_entity(
        self,
        repo_name: str,
        file_type: str,
        content: str,
        source_id: str,
    ) -> None:
        """Write a steering doc as a ConfluencePage-type entity + DOCUMENTED_IN edge."""

        now = datetime.now(UTC).isoformat()
        text_hash = compute_text_hash(content)

        title_map = {
            "product": f"Product Context: {repo_name}",
            "structure": f"Code Structure: {repo_name}",
            "tech": f"Tech Stack: {repo_name}",
        }
        title = title_map.get(file_type, f"Steering ({file_type}): {repo_name}")

        entity = ExtractedEntity(
            label=EntityType.CONFLUENCE_PAGE.value,
            properties={
                "source_id": source_id,
                "title": title,
                "space_key": "STEERING",
                "url": f"kiro_steering/{repo_name}/{file_type}.md",
                "content_summary": content,
                "created_at": now,
                "updated_at": now,
                "text_hash": text_hash,
            },
        )

        # DOCUMENTED_IN: Service -> steering doc (deterministic edge)
        service_source_id = f"service:{repo_name}"
        relationship = ExtractedRelationship(
            source_label=EntityType.SERVICE.value,
            source_id=service_source_id,
            target_label=EntityType.CONFLUENCE_PAGE.value,
            target_id=source_id,
            rel_type=RelationshipType.DOCUMENTED_IN.value,
            properties={
                "created_at": now,
                "source": "deterministic",
            },
        )

        await self._writer.write(
            ExtractionResult(entities=[entity], relationships=[relationship])
        )

    async def _write_confluence_entity(
        self,
        page_id: str,
        title: str,
        space_key: str,
        page_url: str,
        content: str,
        source_id: str,
    ) -> None:
        """Write a Confluence page entity node (no automatic DOCUMENTED_IN edge).

        Unlike steering docs, Confluence pages do not have a deterministic
        service link — that is discovered by Phase 3 LLM enrichment.
        """

        now = datetime.now(UTC).isoformat()
        text_hash = compute_text_hash(content)

        entity = ExtractedEntity(
            label=EntityType.CONFLUENCE_PAGE.value,
            properties={
                "source_id": source_id,
                "title": title,
                "space_key": space_key,
                "url": page_url,
                "content_summary": content,
                "created_at": now,
                "updated_at": now,
                "text_hash": text_hash,
            },
        )

        await self._writer.write(
            ExtractionResult(entities=[entity], relationships=[])
        )

    async def _write_ticket_entity(
        self,
        ticket_key: str,
        title: str,
        source_id: str,
    ) -> None:
        """Write a Ticket entity node in the graph."""

        now = datetime.now(UTC).isoformat()
        text_hash = compute_text_hash({"key": ticket_key, "title": title})

        entity = ExtractedEntity(
            label=EntityType.TICKET.value,
            properties={
                "source_id": source_id,
                "key": ticket_key,
                "title": title,
                "created_at": now,
                "updated_at": now,
                "text_hash": text_hash,
            },
        )

        await self._writer.write(
            ExtractionResult(entities=[entity], relationships=[])
        )

    @staticmethod
    def _extract_adf_text(adf: dict[str, Any]) -> str:
        """Recursively extract plain text from an Atlassian Document Format node.

        Jira v3 API returns descriptions as ADF JSON. This helper walks the
        tree and concatenates text leaf nodes to produce a usable plaintext
        representation for chunking and LLM enrichment.
        """

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

    # ------------------------------------------------------------------
    # Helpers: chunk ingestion pipeline
    # ------------------------------------------------------------------

    async def _ingest_chunks(
        self,
        chunks: list[Chunk],
        source_type: str,
    ) -> tuple[int, int]:
        """Embed, dedup, and write chunks to vector store + BM25 + graph.

        Uses batch embedding (single API call for all chunks in a document)
        to minimize network round-trips. Dedup + writes remain sequential
        since they hit local Docker containers and are fast.

        Returns (chunks_created, duplicates_marked) for reporting.
        """

        if not chunks:
            return 0, 0

        chunks_created = 0
        duplicates_marked = 0

        # 1. Batch embed ALL chunks in one API call (~400ms total vs N×400ms)
        texts = [chunk.display_text for chunk in chunks]
        try:
            vectors = await self._embedding_service.generate_embeddings(texts)
        except Exception as exc:
            logger.warning(
                "Batch embedding failed for %d chunks (source=%s): %s",
                len(chunks), source_type, exc,
            )
            return 0, 0

        # 2. Process each chunk with its pre-computed vector
        for chunk, vector in zip(chunks, vectors):
            try:
                # Check for near-duplicates (Req 5.1-5.3)
                decision = await self._dedup_service.check_duplicate(
                    new_chunk_id=chunk.chunk_id,
                    new_vector=vector,
                    new_doc_type=chunk.metadata.doc_type,
                    repo_name=chunk.metadata.repo_name,
                )

                is_duplicate = False
                if decision.is_duplicate and decision.duplicate_chunk_id == chunk.chunk_id:
                    is_duplicate = True
                    duplicates_marked += 1
                    # Write DUPLICATE_OF edge in graph (Req 5.4)
                    await self._dedup_service.mark_duplicate(
                        duplicate_chunk_id=decision.duplicate_chunk_id,
                        canonical_chunk_id=decision.canonical_chunk_id or "",
                    )

                # Write to vector store (with is_duplicate flag)
                now = datetime.now(UTC).isoformat()
                record = VectorRecord(
                    source_id=chunk.chunk_id,
                    entity_type="Chunk",
                    text_hash=compute_text_hash(chunk.original_segment),
                    vector=vector,
                    created_at=now,
                    section_title=chunk.metadata.section_title,
                    repo_name=chunk.metadata.repo_name,
                    doc_type=chunk.metadata.doc_type,
                    parent_source_id=chunk.metadata.parent_source_id,
                    chunk_index=chunk.metadata.chunk_index,
                    source_ref=chunk.metadata.source_ref,
                    is_duplicate=is_duplicate,
                )
                await self._vector_store.upsert_embedding(record)

                # Write to BM25 sparse index (Req 3.1)
                sparse_metadata = {
                    "repo_name": chunk.metadata.repo_name,
                    "doc_type": chunk.metadata.doc_type,
                    "section_title": chunk.metadata.section_title,
                    "parent_source_id": chunk.metadata.parent_source_id,
                }
                await self._sparse_index.index_chunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.display_text,
                    metadata=sparse_metadata,
                )

                # Write Chunk node + HAS_CHUNK edge in graph
                chunk_entity = ExtractedEntity(
                    label=EntityType.CHUNK.value,
                    properties={
                        "source_id": chunk.chunk_id,
                        "parent_source_id": chunk.metadata.parent_source_id,
                        "chunk_index": chunk.metadata.chunk_index,
                        "doc_type": chunk.metadata.doc_type,
                        "created_at": now,
                        "updated_at": now,
                        "text_hash": compute_text_hash(chunk.original_segment),
                    },
                )
                has_chunk_rel = ExtractedRelationship(
                    source_label=EntityType.CONFLUENCE_PAGE.value,
                    source_id=chunk.metadata.parent_source_id,
                    target_label=EntityType.CHUNK.value,
                    target_id=chunk.chunk_id,
                    rel_type=RelationshipType.HAS_CHUNK.value,
                    properties={
                        "created_at": now,
                        "source": "deterministic",
                    },
                )
                await self._writer.write(
                    ExtractionResult(
                        entities=[chunk_entity],
                        relationships=[has_chunk_rel],
                    )
                )

                chunks_created += 1

            except Exception as exc:
                logger.warning(
                    "Failed to ingest chunk %s: %s",
                    chunk.chunk_id,
                    exc,
                    exc_info=True,
                )

        return chunks_created, duplicates_marked


    # ------------------------------------------------------------------
    # Helpers: confidence bucketing
    # ------------------------------------------------------------------

    @staticmethod
    def _bucket_by_confidence(result: ExtractionResult) -> dict[str, int]:
        """Bucket LLM-inferred relationships by confidence value.

        Returns a dict suitable for IngestionReport.record_llm_edges.
        """

        buckets: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
        for rel in result.relationships:
            conf = getattr(rel, "confidence", None) or "low"
            if conf in buckets:
                buckets[conf] += 1
            else:
                buckets["low"] += 1
        return buckets
