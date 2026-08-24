"""MCP orchestrator — coordinates source pulls and routes to extraction + writer.

The orchestrator is the top-level driver of the V1 ingestion pipeline. It
sits between the **MCP client layer** (which knows how to talk to
GitHub/Jira/Confluence servers over JSON-RPC) and the
**Graph_Extraction_Engine** (which turns payloads into graph writes).

V1 design notes
---------------

* **Pluggable clients** — this module does *not* spawn real MCP
  subprocesses or speak JSON-RPC. It depends on three
  :class:`typing.Protocol`-typed client interfaces —
  :class:`GitHubMCPClient`, :class:`JiraMCPClient`, and
  :class:`ConfluenceMCPClient` — that can be backed by real
  ``mcp`` SDK clients (later) or by in-process fakes for tests.
* **Stateless** — the orchestrator holds no sync state between calls.
  Freshness is tracked on the entities themselves via ``updated_at``
  (Requirement 4.1). Each invocation of :meth:`MCPOrchestrator.full_sync_all`
  performs a complete pass over every registered client.
* **Per-client error isolation** — failures in one client (timeout,
  auth error, malformed payload) are logged and the orchestrator
  moves on to the next client. This keeps a single broken source
  from halting the whole graph refresh.
* **Known-services tracking** — after each GitHub sync, the
  orchestrator gathers the set of ``Service`` names that were just
  materialized. That set is handed to :class:`LLMExtractor` when it
  processes Confluence pages, so the LLM cannot invent service
  names outside of what actually exists in the graph
  (Requirement 1.9 / Property: hallucination guard).
* **Configuration-driven scope** — Jira project keys and Confluence
  space keys come from the injected :class:`MCPRegistry`. GitHub
  repositories are driven by the client's own
  :meth:`GitHubMCPClient.list_repositories` (typical MCP GitHub
  servers already filter to a configured org/repo set, so the
  orchestrator trusts the client).
* **Extraction, then write** — extraction is pure and independent
  per entity; the writer is invoked once per client with the
  fully-merged :class:`ExtractionResult`. Ordering inside the result
  matters for referential integrity: entities emitted by
  extractors come first, relationships later (the writer itself
  also enforces this — entities before relationships — so the
  orchestrator doesn't need to interleave).

V1 simplifications
~~~~~~~~~~~~~~~~~~

* :meth:`full_sync_all` runs clients *sequentially* (GitHub → Jira →
  Confluence) rather than in parallel. That's deliberate: the
  Confluence LLM step depends on the ``known_services`` set produced
  by the GitHub sync, so parallel fan-out would either race on that
  set or require a pre-warm step. Parallelism is deferred to V2 when
  scale demands it (the pilot volume is 10–20 repos, 1–2 projects,
  1–2 spaces).
* ``get_pull_requests`` / ``get_issues`` / ``get_pages`` take no
  ``since`` filter yet. The clients are free to internally scope
  their output. Incremental sync lives in the webhook path.
"""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any, Protocol, Self, runtime_checkable

from config.mcp_registry import MCPRegistry
from processing.extraction.deterministic import (
    ExtractionResult,
    extract_codeowners,
    extract_confluence_page_metadata,
    extract_pr,
    extract_repository,
    extract_ticket,
)
from processing.extraction.llm_extractor import LLMExtractionError, LLMExtractor
from processing.extraction.writer import GraphWriter, WriteResult
from ingestion.retry import RetryConfig, with_retry
from storage.graph.schema import EntityType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MCP client protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class GitHubMCPClient(Protocol):
    """Pull-side interface for a GitHub MCP server.

    Concrete implementations wrap the ``mcp`` SDK's JSON-RPC client;
    test doubles implement the same attributes/methods directly. The
    orchestrator never constructs these — they are registered via
    :meth:`MCPOrchestrator.register_github_client` so callers control
    lifecycle and configuration.
    """

    name: str
    source_type: str  # always "github"

    async def list_repositories(self) -> list[dict[str, Any]]:
        """Return the list of repository payloads the client is scoped to."""
        ...

    async def get_pull_requests(self, repo_name: str) -> list[dict[str, Any]]:
        """Return PR payloads for the given repository name."""
        ...

    async def get_codeowners(self, repo_name: str) -> str | None:
        """Return the raw CODEOWNERS file contents or ``None`` if absent."""
        ...

    async def close(self) -> None:
        """Release any transport resources held by the client."""
        ...


@runtime_checkable
class JiraMCPClient(Protocol):
    """Pull-side interface for a Jira MCP server."""

    name: str
    source_type: str  # always "jira"

    async def get_issues(self, project_key: str) -> list[dict[str, Any]]:
        """Return issue payloads (tickets + epics) for the given project."""
        ...

    async def close(self) -> None:
        """Release any transport resources held by the client."""
        ...


@runtime_checkable
class ConfluenceMCPClient(Protocol):
    """Pull-side interface for a Confluence MCP server."""

    name: str
    source_type: str  # always "confluence"

    async def get_pages(self, space_key: str) -> list[dict[str, Any]]:
        """Return page payloads (with bodies) for the given space key."""
        ...

    async def close(self) -> None:
        """Release any transport resources held by the client."""
        ...


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _collect_service_names(result: ExtractionResult) -> set[str]:
    """Return the set of :class:`Service` names present in ``result``.

    Used to keep ``MCPOrchestrator._known_services`` current after each
    GitHub sync so that subsequent Confluence LLM extractions can
    reject invented service names.
    """

    names: set[str] = set()
    for entity in result.entities:
        if entity.label != EntityType.SERVICE.value:
            continue
        name = entity.properties.get("name")
        if isinstance(name, str) and name:
            names.add(name)
    return names


def _find_repo_source_id(result: ExtractionResult) -> str | None:
    """Return the ``Repository.source_id`` emitted by a GitHub repo extraction, if any."""

    for entity in result.entities:
        if entity.label == EntityType.REPOSITORY.value:
            sid = entity.properties.get("source_id")
            if isinstance(sid, str) and sid:
                return sid
    return None


def _find_confluence_source_id(result: ExtractionResult) -> str | None:
    """Return the ``ConfluencePage.source_id`` emitted by a page extraction, if any."""

    for entity in result.entities:
        if entity.label == EntityType.CONFLUENCE_PAGE.value:
            sid = entity.properties.get("source_id")
            if isinstance(sid, str) and sid:
                return sid
    return None


def _extract_confluence_body(page: dict[str, Any]) -> str:
    """Return the best-effort body text of a Confluence page payload.

    Confluence's REST API nests the body under ``body.storage.value``
    (or ``body.view.value`` / ``body.atlas_doc_format.value`` depending
    on the requested representation). Some MCP servers flatten it to a
    top-level ``content`` or ``body_text`` field. This helper tolerates
    all of those shapes so the orchestrator doesn't need to know which
    server flavour produced the payload.
    """

    body = page.get("body")
    if isinstance(body, dict):
        for key in ("storage", "view", "atlas_doc_format"):
            sub = body.get(key)
            if isinstance(sub, dict):
                value = sub.get("value")
                if isinstance(value, str):
                    return value
    for key in ("content", "text", "body_text"):
        val = page.get(key)
        if isinstance(val, str):
            return val
    return ""


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class MCPOrchestrator:
    """Coordinates MCP client calls and feeds the Graph_Extraction_Engine.

    Instances are long-lived (one per process). The typical wiring is::

        orchestrator = MCPOrchestrator(
            mcp_registry=registry,
            graph_writer=writer,
            llm_extractor=llm,
        )
        orchestrator.register_github_client("github", github_client)
        orchestrator.register_jira_client("jira", jira_client)
        orchestrator.register_confluence_client("confluence", confluence_client)
        await orchestrator.full_sync_all()

    The orchestrator does not own the registered clients — callers
    construct them and pass them in. :meth:`close` best-effort-closes
    every registered client plus the injected writer, so shutdown is a
    single call.
    """

    def __init__(
        self,
        mcp_registry: MCPRegistry,
        graph_writer: GraphWriter,
        llm_extractor: LLMExtractor | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._registry = mcp_registry
        self._writer = graph_writer
        self._llm_extractor = llm_extractor
        self._retry_config = retry_config
        self._github_clients: dict[str, GitHubMCPClient] = {}
        self._jira_clients: dict[str, JiraMCPClient] = {}
        self._confluence_clients: dict[str, ConfluenceMCPClient] = {}
        self._known_services: set[str] = set()

    async def _call(
        self,
        func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Invoke ``func(*args, **kwargs)`` via :func:`with_retry` when configured.

        When the orchestrator was constructed without a
        :class:`RetryConfig`, the call is forwarded directly — preserving
        the zero-overhead behaviour used by tests and by in-process fakes
        that never fail. When a config is present, transient failures are
        retried with exponential backoff before the call's own
        per-site ``except`` block takes over as the final fallback
        (Requirement 1.7).
        """

        if self._retry_config is None:
            return await func(*args, **kwargs)
        return await with_retry(func, *args, config=self._retry_config, **kwargs)

    # -- client registration --------------------------------------------

    def register_github_client(self, name: str, client: GitHubMCPClient) -> None:
        """Register a :class:`GitHubMCPClient` under ``name``.

        Duplicate names overwrite silently; the caller is expected to
        hold a single identity per source. ``name`` is also how the
        client is identified in :class:`WriteResult` keys returned by
        :meth:`full_sync_all`.
        """

        self._github_clients[name] = client

    def register_jira_client(self, name: str, client: JiraMCPClient) -> None:
        """Register a :class:`JiraMCPClient` under ``name``."""

        self._jira_clients[name] = client

    def register_confluence_client(self, name: str, client: ConfluenceMCPClient) -> None:
        """Register a :class:`ConfluenceMCPClient` under ``name``."""

        self._confluence_clients[name] = client

    # -- introspection ---------------------------------------------------

    @property
    def known_services(self) -> frozenset[str]:
        """Snapshot of the service names discovered so far this session.

        Populated by GitHub syncs (see :meth:`full_sync_github`) and
        consumed by Confluence syncs (see :meth:`full_sync_confluence`)
        to guard LLM extraction against hallucinated service names.
        Exposed as a property for observability and for testing; the
        returned set is immutable.
        """

        return frozenset(self._known_services)

    # -- full syncs ------------------------------------------------------

    async def full_sync_github(self, client_name: str) -> WriteResult:
        """Pull every repo / PR / CODEOWNERS from a GitHub MCP client.

        The flow per repo is:

        1. :func:`extract_repository` → ``Repository`` + ``Service`` +
           ``CONTAINS``.
        2. :meth:`GitHubMCPClient.get_pull_requests` →
           :func:`extract_pr` per PR → ``PR`` + ``MODIFIES`` + optional
           ``Person`` (author).
        3. :meth:`GitHubMCPClient.get_codeowners` →
           :func:`extract_codeowners` → ``Team`` + ``OWNED_BY`` edges.

        All produced entities and relationships are merged into one
        :class:`ExtractionResult` and written in a single
        :meth:`GraphWriter.write` call so that the writer can apply its
        "entities before relationships" ordering in one pass. Errors
        on individual PRs or CODEOWNERS files are logged and skipped;
        they don't halt the sync for the rest of the repo.

        Raises:
            KeyError: If no GitHub client is registered under
                ``client_name``.
        """

        client = self._github_clients.get(client_name)
        if client is None:
            raise KeyError(f"No GitHub client registered under {client_name!r}")

        try:
            repos = await self._call(client.list_repositories)
        except Exception as exc:
            logger.error(
                "github client %s: list_repositories failed: %s", client_name, exc
            )
            return WriteResult()

        aggregate = ExtractionResult()

        for repo in repos:
            repo_name = repo.get("name") if isinstance(repo, dict) else None
            if not isinstance(repo_name, str) or not repo_name:
                logger.warning(
                    "github client %s: skipping repo payload with no name", client_name
                )
                continue

            try:
                repo_result = extract_repository(repo)
            except Exception as exc:
                logger.warning(
                    "github client %s: extract_repository failed for %r: %s",
                    client_name,
                    repo_name,
                    exc,
                )
                continue

            aggregate = aggregate.merge(repo_result)
            self._known_services |= _collect_service_names(repo_result)

            repo_source_id = _find_repo_source_id(repo_result)
            if repo_source_id is None:
                # Shouldn't happen, but without a repo source id the
                # downstream PR and CODEOWNERS extractions can't link
                # back.
                logger.warning(
                    "github client %s: no Repository entity produced for %r",
                    client_name,
                    repo_name,
                )
                continue

            # PRs --------------------------------------------------------
            try:
                prs = await self._call(client.get_pull_requests, repo_name)
            except Exception as exc:
                logger.warning(
                    "github client %s: get_pull_requests(%r) failed: %s",
                    client_name,
                    repo_name,
                    exc,
                )
                prs = []

            for pr in prs:
                try:
                    pr_result = extract_pr(pr, repo_source_id=repo_source_id)
                    aggregate = aggregate.merge(pr_result)
                except Exception as exc:
                    logger.warning(
                        "github client %s: extract_pr failed for %r: %s",
                        client_name,
                        repo_name,
                        exc,
                    )

            # CODEOWNERS -------------------------------------------------
            try:
                codeowners_text = await self._call(client.get_codeowners, repo_name)
            except Exception as exc:
                logger.warning(
                    "github client %s: get_codeowners(%r) failed: %s",
                    client_name,
                    repo_name,
                    exc,
                )
                codeowners_text = None

            if codeowners_text:
                try:
                    co_result = extract_codeowners(
                        codeowners_text, repo_source_id=repo_source_id
                    )
                    aggregate = aggregate.merge(co_result)
                except Exception as exc:
                    logger.warning(
                        "github client %s: extract_codeowners failed for %r: %s",
                        client_name,
                        repo_name,
                        exc,
                    )

        return await self._writer.write(aggregate)

    async def full_sync_jira(self, client_name: str) -> WriteResult:
        """Pull every configured Jira project's issues and extract them.

        The list of project keys comes from the MCP registry entry
        whose ``name`` matches ``client_name`` (the ``config.projects``
        field). If the registry has no matching entry — or the entry
        declares no ``projects`` — the orchestrator logs a warning
        and returns an empty :class:`WriteResult`.

        Every Jira issue is extracted as a :class:`Ticket` via
        :func:`extract_ticket`. V1 does not distinguish epics from
        other issue types here; epic-specific extraction can be
        layered in later by switching on the ``fields.issuetype.name``
        field.

        Raises:
            KeyError: If no Jira client is registered under
                ``client_name``.
        """

        client = self._jira_clients.get(client_name)
        if client is None:
            raise KeyError(f"No Jira client registered under {client_name!r}")

        projects = self._config_list_for(client_name, "projects")
        if not projects:
            logger.warning(
                "jira client %s: no projects configured in MCP registry", client_name
            )
            return WriteResult()

        aggregate = ExtractionResult()

        for project_key in projects:
            try:
                issues = await self._call(client.get_issues, project_key)
            except Exception as exc:
                logger.warning(
                    "jira client %s: get_issues(%r) failed: %s",
                    client_name,
                    project_key,
                    exc,
                )
                continue

            for issue in issues:
                try:
                    issue_result = extract_ticket(issue)
                    aggregate = aggregate.merge(issue_result)
                except Exception as exc:
                    issue_key = (
                        issue.get("key") if isinstance(issue, dict) else None
                    )
                    logger.warning(
                        "jira client %s: extract_ticket failed for %r: %s",
                        client_name,
                        issue_key,
                        exc,
                    )

        return await self._writer.write(aggregate)

    async def full_sync_confluence(self, client_name: str) -> WriteResult:
        """Pull every configured Confluence space's pages and extract them.

        Each page produces a :class:`ConfluencePage` entity via
        :func:`extract_confluence_page_metadata`. If an
        :class:`LLMExtractor` is wired in, the page body is *also*
        handed to :meth:`LLMExtractor.extract_from_confluence_page`
        with the current :attr:`known_services` set as a
        hallucination guard — producing ``DOCUMENTED_IN`` and
        ``DEPENDS_ON`` edges for services explicitly mentioned in the
        prose.

        :class:`LLMExtractionError` is caught per page so a transient
        LLM outage only drops the semantic edges for that page; the
        page metadata is still written. All structural errors
        (malformed payload, missing fields) are logged and skipped.

        Raises:
            KeyError: If no Confluence client is registered under
                ``client_name``.
        """

        client = self._confluence_clients.get(client_name)
        if client is None:
            raise KeyError(f"No Confluence client registered under {client_name!r}")

        spaces = self._config_list_for(client_name, "spaces")
        restricted = self._config_restricted_spaces_for(client_name)
        restricted_keys = [r.get("space_key", "") for r in restricted if r.get("space_key")]
        all_space_keys = list(dict.fromkeys([*spaces, *restricted_keys]))  # dedupe, preserve order

        if not all_space_keys:
            logger.warning(
                "confluence client %s: no spaces configured in MCP registry",
                client_name,
            )
            return WriteResult()

        aggregate = ExtractionResult()

        for space_key in all_space_keys:
            try:
                pages = await self._call(client.get_pages, space_key)
            except Exception as exc:
                logger.warning(
                    "confluence client %s: get_pages(%r) failed: %s",
                    client_name,
                    space_key,
                    exc,
                )
                continue

            for page in pages:
                try:
                    base_url = getattr(client, "site_url", None)
                    page_result = extract_confluence_page_metadata(page, base_url=base_url)
                except Exception as exc:
                    logger.warning(
                        "confluence client %s: extract_confluence_page_metadata "
                        "failed: %s",
                        client_name,
                        exc,
                    )
                    continue

                aggregate = aggregate.merge(page_result)

                if self._llm_extractor is None:
                    continue

                page_source_id = _find_confluence_source_id(page_result)
                body = _extract_confluence_body(page)
                if page_source_id is None or not body.strip():
                    continue

                try:
                    llm_result = await self._llm_extractor.extract_from_confluence_page(
                        page_source_id=page_source_id,
                        page_title=str(page.get("title", "")),
                        page_content=body,
                        known_services=sorted(self._known_services),
                    )
                    aggregate = aggregate.merge(llm_result)
                except LLMExtractionError as exc:
                    logger.warning(
                        "confluence client %s: LLM extraction failed for %s: %s",
                        client_name,
                        page_source_id,
                        exc,
                    )

        return await self._writer.write(aggregate)

    async def write_extraction_result(self, result: ExtractionResult) -> WriteResult:
        """Write an already-extracted result, bypassing the full-sync loop.

        This is the fast-path for webhook-driven ingestion. When a
        source system sends an event (PR opened, ticket updated,
        page edited), the :class:`~src.webhooks.adapter.WebhookAdapter`
        pulls just that single resource, hands it to the matching
        deterministic extractor, and passes the resulting
        :class:`ExtractionResult` here — avoiding a full
        per-source fan-out.

        The method is a thin pass-through to :meth:`GraphWriter.write`
        rather than inlining the call so the writer stays the single
        point of entry for graph mutations (which keeps the
        idempotency + embedding logic in one place).
        """

        return await self._writer.write(result)

    async def full_sync_all(self) -> dict[str, WriteResult]:
        """Run a full sync across every registered client.

        Order is fixed: GitHub first (so :attr:`known_services` is
        populated), then Jira, then Confluence. Failures in one client
        don't stop the others — the result dict simply won't contain
        a key for the failed client (an error is logged).

        Returns:
            Mapping from ``"{source_type}:{client_name}"`` to the
            corresponding :class:`WriteResult`.
        """

        results: dict[str, WriteResult] = {}

        for name in list(self._github_clients):
            try:
                results[f"github:{name}"] = await self.full_sync_github(name)
            except Exception as exc:
                logger.error(
                    "full_sync_github(%s) raised an unexpected error: %s", name, exc
                )

        for name in list(self._jira_clients):
            try:
                results[f"jira:{name}"] = await self.full_sync_jira(name)
            except Exception as exc:
                logger.error(
                    "full_sync_jira(%s) raised an unexpected error: %s", name, exc
                )

        for name in list(self._confluence_clients):
            try:
                results[f"confluence:{name}"] = await self.full_sync_confluence(name)
            except Exception as exc:
                logger.error(
                    "full_sync_confluence(%s) raised an unexpected error: %s",
                    name,
                    exc,
                )

        return results

    # -- lifecycle -------------------------------------------------------

    async def close(self) -> None:
        """Best-effort close of every registered client and the writer.

        Errors from individual client ``close`` calls are logged and
        swallowed so a flaky transport can't leak an exception on
        shutdown. The :class:`GraphWriter` is closed last because it
        owns the stores shared by all other components.
        """

        clients: list[Any] = [
            *self._github_clients.values(),
            *self._jira_clients.values(),
            *self._confluence_clients.values(),
        ]
        for client in clients:
            try:
                await client.close()
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("error closing MCP client: %s", exc)

        try:
            await self._writer.close()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("error closing GraphWriter: %s", exc)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    # -- internals -------------------------------------------------------

    def _config_list_for(self, client_name: str, key: str) -> list[str]:
        """Return ``config[key]`` as a list of strings from the matching registry entry.

        Non-matching entries, missing keys, and malformed list values
        all return ``[]`` so callers don't have to re-check each
        layer.
        """

        for server in self._registry.servers:
            if server.name != client_name:
                continue
            value = server.config.get(key)
            if isinstance(value, list):
                return [str(item) for item in value if isinstance(item, str) and item]
            return []
        return []

    def _config_restricted_spaces_for(self, client_name: str) -> list[dict[str, Any]]:
        """Return the ``restricted_spaces`` config block for the given client, or ``[]``.

        Each entry is a dict like ``{"space_key": "DA", "parent_page_id": "..."}``.
        """

        for server in self._registry.servers:
            if server.name != client_name:
                continue
            value = server.config.get("restricted_spaces")
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            return []
        return []


__all__ = [
    "ConfluenceMCPClient",
    "GitHubMCPClient",
    "JiraMCPClient",
    "MCPOrchestrator",
]
