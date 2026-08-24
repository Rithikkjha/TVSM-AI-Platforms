"""Unit tests for :mod:`src.ingestion.orchestrator`.

The orchestrator composes three things that already have their own
tests: the deterministic extractors, the :class:`LLMExtractor`, and the
:class:`GraphWriter`. These tests focus on the orchestration slice
specifically — client dispatch, registry lookup, error isolation, and
the known-services propagation — with every dependency mocked.

No real Neo4j, no real MCP transport, no real Azure OpenAI calls.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from config.mcp_registry import MCPRegistry, MCPServerConfig
from processing.extraction.deterministic import ExtractionResult
from processing.extraction.llm_extractor import LLMExtractionError
from processing.extraction.writer import WriteResult
from ingestion.orchestrator import (
    ConfluenceMCPClient,
    GitHubMCPClient,
    JiraMCPClient,
    MCPOrchestrator,
)
from ingestion.retry import RetryConfig
from storage.graph.schema import EntityType, RelationshipType

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeGitHubClient:
    """In-process stand-in for a GitHub MCP client."""

    source_type = "github"

    def __init__(
        self,
        name: str,
        repos: list[dict[str, Any]] | None = None,
        prs: dict[str, list[dict[str, Any]]] | None = None,
        codeowners: dict[str, str | None] | None = None,
    ) -> None:
        self.name = name
        self._repos = repos or []
        self._prs = prs or {}
        self._codeowners = codeowners or {}
        self.closed = False
        self.list_repos_exc: BaseException | None = None
        self.prs_exc_for: set[str] = set()
        self.codeowners_exc_for: set[str] = set()

    async def list_repositories(self) -> list[dict[str, Any]]:
        if self.list_repos_exc is not None:
            raise self.list_repos_exc
        return list(self._repos)

    async def get_pull_requests(self, repo_name: str) -> list[dict[str, Any]]:
        if repo_name in self.prs_exc_for:
            raise RuntimeError(f"simulated PR fetch failure for {repo_name}")
        return list(self._prs.get(repo_name, []))

    async def get_codeowners(self, repo_name: str) -> str | None:
        if repo_name in self.codeowners_exc_for:
            raise RuntimeError(f"simulated CODEOWNERS failure for {repo_name}")
        return self._codeowners.get(repo_name)

    async def close(self) -> None:
        self.closed = True


class FakeJiraClient:
    source_type = "jira"

    def __init__(
        self,
        name: str,
        issues: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.name = name
        self._issues = issues or {}
        self.closed = False
        self.issues_exc_for: set[str] = set()

    async def get_issues(self, project_key: str) -> list[dict[str, Any]]:
        if project_key in self.issues_exc_for:
            raise RuntimeError(f"simulated Jira failure for {project_key}")
        return list(self._issues.get(project_key, []))

    async def close(self) -> None:
        self.closed = True


class FakeConfluenceClient:
    source_type = "confluence"

    def __init__(
        self,
        name: str,
        pages: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.name = name
        self._pages = pages or {}
        self.closed = False
        self.pages_exc_for: set[str] = set()

    async def get_pages(self, space_key: str) -> list[dict[str, Any]]:
        if space_key in self.pages_exc_for:
            raise RuntimeError(f"simulated Confluence failure for {space_key}")
        return list(self._pages.get(space_key, []))

    async def close(self) -> None:
        self.closed = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_writer_mock() -> MagicMock:
    """Return a :class:`GraphWriter`-shaped mock returning empty results."""

    writer = MagicMock(name="GraphWriter")
    writer.write = AsyncMock(return_value=WriteResult())
    writer.close = AsyncMock()
    return writer


def _make_registry() -> MCPRegistry:
    """Return a registry matching the client names used in these tests."""

    return MCPRegistry(
        servers=[
            MCPServerConfig(
                name="github",
                type="@modelcontextprotocol/server-github",
                config={
                    "org": "test-org",
                    "repos": ["repo-a", "repo-b"],
                    "token_env": "GITHUB_TOKEN",
                },
            ),
            MCPServerConfig(
                name="jira",
                type="mcp-atlassian",
                config={
                    "instance": "test.atlassian.net",
                    "projects": ["ENG", "PLAT"],
                    "token_env": "JIRA_TOKEN",
                },
            ),
            MCPServerConfig(
                name="confluence",
                type="mcp-atlassian",
                config={
                    "instance": "test.atlassian.net",
                    "spaces": ["ENG", "ARCH"],
                    "token_env": "CONFLUENCE_TOKEN",
                },
            ),
        ]
    )


def _repo_payload(repo_id: int, name: str) -> dict[str, Any]:
    return {
        "id": repo_id,
        "name": name,
        "html_url": f"https://github.com/test-org/{name}",
        "default_branch": "main",
        "language": "Python",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-12-01T00:00:00Z",
    }


def _pr_payload(number: int, title: str = "Fix bug") -> dict[str, Any]:
    return {
        "number": number,
        "title": title,
        "state": "open",
        "body": "This fixes the bug.",
        "html_url": "https://github.com/test-org/repo/pull/1",
        "user": {"login": "alice", "name": "Alice"},
        "created_at": "2024-11-01T00:00:00Z",
        "updated_at": "2024-12-01T00:00:00Z",
    }


def _jira_issue_payload(key: str, title: str = "Example") -> dict[str, Any]:
    return {
        "key": key,
        "fields": {
            "summary": title,
            "status": {"name": "In Progress"},
            "priority": {"name": "High"},
            "description": "Details here.",
            "created": "2024-11-01T00:00:00.000+0000",
            "updated": "2024-12-01T00:00:00.000+0000",
        },
    }


def _confluence_page_payload(
    page_id: str,
    title: str = "Payments Architecture",
    space_key: str = "ENG",
    body: str = "The payments service depends on the auth service.",
) -> dict[str, Any]:
    return {
        "id": page_id,
        "title": title,
        "space": {"key": space_key},
        "_links": {"webui": f"/spaces/{space_key}/pages/{page_id}"},
        "version": {"when": "2024-12-01T00:00:00.000Z"},
        "body": {"storage": {"value": body}},
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_register_github_client_stores_under_name(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)
        client = FakeGitHubClient("github")
        orch.register_github_client("github", client)
        assert orch._github_clients["github"] is client  # noqa: SLF001

    def test_register_jira_client_stores_under_name(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)
        client = FakeJiraClient("jira")
        orch.register_jira_client("jira", client)
        assert orch._jira_clients["jira"] is client  # noqa: SLF001

    def test_register_confluence_client_stores_under_name(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)
        client = FakeConfluenceClient("confluence")
        orch.register_confluence_client("confluence", client)
        assert orch._confluence_clients["confluence"] is client  # noqa: SLF001


# ---------------------------------------------------------------------------
# full_sync_github
# ---------------------------------------------------------------------------


class TestFullSyncGitHub:
    async def test_extracts_repos_prs_and_codeowners(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)

        client = FakeGitHubClient(
            "github",
            repos=[_repo_payload(1, "repo-a"), _repo_payload(2, "repo-b")],
            prs={
                "repo-a": [_pr_payload(1), _pr_payload(2)],
                "repo-b": [_pr_payload(3)],
            },
            codeowners={
                "repo-a": "* @platform-team\n*.md @docs\n",
                "repo-b": None,
            },
        )
        orch.register_github_client("github", client)

        result = await orch.full_sync_github("github")

        # Writer was invoked with a single merged ExtractionResult.
        assert isinstance(result, WriteResult)
        writer.write.assert_awaited_once()
        (aggregate,), _ = writer.write.call_args
        assert isinstance(aggregate, ExtractionResult)

        labels = [e.label for e in aggregate.entities]
        # Both repos produced Repository + Service entities.
        assert labels.count(EntityType.REPOSITORY.value) == 2
        assert labels.count(EntityType.SERVICE.value) == 2
        # Three PRs total across the two repos, each with its Person.
        assert labels.count(EntityType.PR.value) == 3
        assert labels.count(EntityType.PERSON.value) == 3
        # CODEOWNERS for repo-a produced 2 teams.
        assert labels.count(EntityType.TEAM.value) == 2

        rel_types = [r.rel_type for r in aggregate.relationships]
        assert rel_types.count(RelationshipType.CONTAINS.value) == 2
        assert rel_types.count(RelationshipType.MODIFIES.value) == 3
        assert rel_types.count(RelationshipType.OWNED_BY.value) == 2

    async def test_populates_known_services(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)

        client = FakeGitHubClient(
            "github",
            repos=[
                _repo_payload(1, "payments"),
                _repo_payload(2, "auth"),
            ],
        )
        orch.register_github_client("github", client)

        assert orch.known_services == frozenset()
        await orch.full_sync_github("github")
        assert orch.known_services == frozenset({"payments", "auth"})

    async def test_list_repositories_failure_returns_empty_without_writing(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)

        client = FakeGitHubClient("github")
        client.list_repos_exc = RuntimeError("auth failed")
        orch.register_github_client("github", client)

        with caplog.at_level(logging.ERROR, logger="src.ingestion.orchestrator"):
            result = await orch.full_sync_github("github")

        assert isinstance(result, WriteResult)
        writer.write.assert_not_awaited()
        assert any("list_repositories failed" in rec.message for rec in caplog.records)

    async def test_pr_fetch_failure_is_isolated_to_that_repo(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)

        client = FakeGitHubClient(
            "github",
            repos=[_repo_payload(1, "repo-a"), _repo_payload(2, "repo-b")],
            prs={"repo-b": [_pr_payload(9)]},
        )
        client.prs_exc_for = {"repo-a"}
        orch.register_github_client("github", client)

        await orch.full_sync_github("github")

        (aggregate,), _ = writer.write.call_args
        pr_numbers = [
            e.properties["number"]
            for e in aggregate.entities
            if e.label == EntityType.PR.value
        ]
        # repo-a's PRs dropped, repo-b's survived.
        assert pr_numbers == [9]
        # Both repos still extracted into Repository + Service entities.
        labels = [e.label for e in aggregate.entities]
        assert labels.count(EntityType.REPOSITORY.value) == 2

    async def test_missing_client_raises(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)
        with pytest.raises(KeyError):
            await orch.full_sync_github("missing")


# ---------------------------------------------------------------------------
# full_sync_jira
# ---------------------------------------------------------------------------


class TestFullSyncJira:
    async def test_extracts_issues_for_each_project_in_registry(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)

        client = FakeJiraClient(
            "jira",
            issues={
                "ENG": [_jira_issue_payload("ENG-1"), _jira_issue_payload("ENG-2")],
                "PLAT": [_jira_issue_payload("PLAT-42")],
            },
        )
        orch.register_jira_client("jira", client)

        await orch.full_sync_jira("jira")

        writer.write.assert_awaited_once()
        (aggregate,), _ = writer.write.call_args
        keys = [
            e.properties["key"]
            for e in aggregate.entities
            if e.label == EntityType.TICKET.value
        ]
        assert keys == ["ENG-1", "ENG-2", "PLAT-42"]

    async def test_no_projects_configured_returns_empty(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        writer = _make_writer_mock()
        registry = MCPRegistry(
            servers=[MCPServerConfig(name="jira", type="mcp-atlassian", config={})]
        )
        orch = MCPOrchestrator(registry, writer)
        client = FakeJiraClient("jira")
        orch.register_jira_client("jira", client)

        with caplog.at_level(logging.WARNING, logger="src.ingestion.orchestrator"):
            result = await orch.full_sync_jira("jira")

        assert isinstance(result, WriteResult)
        writer.write.assert_not_awaited()
        assert any("no projects configured" in rec.message for rec in caplog.records)

    async def test_project_failure_is_isolated(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)

        client = FakeJiraClient(
            "jira",
            issues={"PLAT": [_jira_issue_payload("PLAT-1")]},
        )
        client.issues_exc_for = {"ENG"}
        orch.register_jira_client("jira", client)

        await orch.full_sync_jira("jira")

        (aggregate,), _ = writer.write.call_args
        keys = [
            e.properties["key"]
            for e in aggregate.entities
            if e.label == EntityType.TICKET.value
        ]
        assert keys == ["PLAT-1"]

    async def test_missing_client_raises(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)
        with pytest.raises(KeyError):
            await orch.full_sync_jira("missing")


# ---------------------------------------------------------------------------
# full_sync_confluence
# ---------------------------------------------------------------------------


class TestFullSyncConfluence:
    async def test_extracts_pages_without_llm_extractor(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)

        client = FakeConfluenceClient(
            "confluence",
            pages={
                "ENG": [_confluence_page_payload("1"), _confluence_page_payload("2")],
                "ARCH": [_confluence_page_payload("3", space_key="ARCH")],
            },
        )
        orch.register_confluence_client("confluence", client)

        await orch.full_sync_confluence("confluence")

        (aggregate,), _ = writer.write.call_args
        page_labels = [
            e.label
            for e in aggregate.entities
            if e.label == EntityType.CONFLUENCE_PAGE.value
        ]
        assert len(page_labels) == 3

    async def test_invokes_llm_extractor_with_known_services(self) -> None:
        writer = _make_writer_mock()
        registry = _make_registry()

        llm = MagicMock(name="LLMExtractor")
        llm.extract_from_confluence_page = AsyncMock(return_value=ExtractionResult())
        llm.close = AsyncMock()

        orch = MCPOrchestrator(registry, writer, llm_extractor=llm)
        # Seed known services as if a prior github sync ran.
        orch._known_services = {"payments", "auth"}  # noqa: SLF001

        client = FakeConfluenceClient(
            "confluence",
            pages={
                "ENG": [
                    _confluence_page_payload(
                        "1",
                        title="Payments Architecture",
                        body="Payments depends on auth.",
                    )
                ],
                "ARCH": [],
            },
        )
        orch.register_confluence_client("confluence", client)

        await orch.full_sync_confluence("confluence")

        llm.extract_from_confluence_page.assert_awaited_once()
        _args, kwargs = llm.extract_from_confluence_page.call_args
        assert kwargs["page_source_id"] == "confluence:page:1"
        assert kwargs["page_title"] == "Payments Architecture"
        assert "Payments depends on auth" in kwargs["page_content"]
        assert kwargs["known_services"] == ["auth", "payments"]  # sorted

    async def test_llm_extraction_error_does_not_abort_sync(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        writer = _make_writer_mock()
        registry = _make_registry()

        llm = MagicMock(name="LLMExtractor")
        llm.extract_from_confluence_page = AsyncMock(
            side_effect=LLMExtractionError("rate limited")
        )
        llm.close = AsyncMock()

        orch = MCPOrchestrator(registry, writer, llm_extractor=llm)

        client = FakeConfluenceClient(
            "confluence",
            pages={
                "ENG": [_confluence_page_payload("1"), _confluence_page_payload("2")],
                "ARCH": [],
            },
        )
        orch.register_confluence_client("confluence", client)

        with caplog.at_level(logging.WARNING, logger="src.ingestion.orchestrator"):
            await orch.full_sync_confluence("confluence")

        # Both pages still had their metadata recorded.
        (aggregate,), _ = writer.write.call_args
        assert (
            sum(
                1
                for e in aggregate.entities
                if e.label == EntityType.CONFLUENCE_PAGE.value
            )
            == 2
        )
        # LLM was invoked for both pages and errored for both.
        assert llm.extract_from_confluence_page.await_count == 2
        assert any(
            "LLM extraction failed" in rec.message for rec in caplog.records
        )

    async def test_skips_llm_for_empty_body(self) -> None:
        writer = _make_writer_mock()
        registry = _make_registry()
        llm = MagicMock(name="LLMExtractor")
        llm.extract_from_confluence_page = AsyncMock(return_value=ExtractionResult())
        llm.close = AsyncMock()

        orch = MCPOrchestrator(registry, writer, llm_extractor=llm)

        client = FakeConfluenceClient(
            "confluence",
            pages={
                "ENG": [_confluence_page_payload("1", body="")],
                "ARCH": [],
            },
        )
        orch.register_confluence_client("confluence", client)

        await orch.full_sync_confluence("confluence")
        llm.extract_from_confluence_page.assert_not_awaited()

    async def test_no_spaces_configured_returns_empty(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        writer = _make_writer_mock()
        registry = MCPRegistry(
            servers=[
                MCPServerConfig(name="confluence", type="mcp-atlassian", config={})
            ]
        )
        orch = MCPOrchestrator(registry, writer)
        client = FakeConfluenceClient("confluence")
        orch.register_confluence_client("confluence", client)

        with caplog.at_level(logging.WARNING, logger="src.ingestion.orchestrator"):
            result = await orch.full_sync_confluence("confluence")

        assert isinstance(result, WriteResult)
        writer.write.assert_not_awaited()
        assert any("no spaces configured" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# full_sync_all
# ---------------------------------------------------------------------------


class TestFullSyncAll:
    async def test_aggregates_across_all_clients(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)

        orch.register_github_client(
            "github",
            FakeGitHubClient(
                "github",
                repos=[_repo_payload(1, "repo-a")],
            ),
        )
        orch.register_jira_client(
            "jira",
            FakeJiraClient("jira", issues={"ENG": [_jira_issue_payload("ENG-1")]}),
        )
        orch.register_confluence_client(
            "confluence",
            FakeConfluenceClient(
                "confluence",
                pages={"ENG": [_confluence_page_payload("1")]},
            ),
        )

        results = await orch.full_sync_all()

        assert set(results) == {"github:github", "jira:jira", "confluence:confluence"}
        # The writer was called exactly three times (once per client).
        assert writer.write.await_count == 3

    async def test_failure_in_one_client_does_not_stop_others(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)

        gh_client = FakeGitHubClient("github")
        gh_client.list_repos_exc = RuntimeError("boom")
        orch.register_github_client("github", gh_client)

        orch.register_jira_client(
            "jira",
            FakeJiraClient("jira", issues={"ENG": [_jira_issue_payload("ENG-1")]}),
        )
        orch.register_confluence_client(
            "confluence",
            FakeConfluenceClient(
                "confluence",
                pages={"ENG": [_confluence_page_payload("1")]},
            ),
        )

        with caplog.at_level(logging.ERROR, logger="src.ingestion.orchestrator"):
            results = await orch.full_sync_all()

        # GitHub still recorded an (empty) result because
        # full_sync_github swallowed list_repositories failure.
        assert "github:github" in results
        assert "jira:jira" in results
        assert "confluence:confluence" in results

    async def test_empty_when_no_clients_registered(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)
        results = await orch.full_sync_all()
        assert results == {}


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


class TestLifecycle:
    async def test_close_closes_every_client_and_writer(self) -> None:
        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)

        gh = FakeGitHubClient("github")
        jira = FakeJiraClient("jira")
        conf = FakeConfluenceClient("confluence")
        orch.register_github_client("github", gh)
        orch.register_jira_client("jira", jira)
        orch.register_confluence_client("confluence", conf)

        await orch.close()

        assert gh.closed is True
        assert jira.closed is True
        assert conf.closed is True
        writer.close.assert_awaited_once()

    async def test_async_context_manager_closes_on_exit(self) -> None:
        writer = _make_writer_mock()
        gh = FakeGitHubClient("github")
        async with MCPOrchestrator(_make_registry(), writer) as orch:
            orch.register_github_client("github", gh)
        assert gh.closed is True
        writer.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# Protocol structural conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    """The fakes should satisfy the runtime-checkable Protocols.

    This exercise is mostly a guard against drift — if the Protocol
    signatures change without updating the concrete MCP-backed
    implementations, these isinstance checks will fail and point at
    the mismatch.
    """

    def test_fake_github_client_matches_protocol(self) -> None:
        assert isinstance(FakeGitHubClient("github"), GitHubMCPClient)

    def test_fake_jira_client_matches_protocol(self) -> None:
        assert isinstance(FakeJiraClient("jira"), JiraMCPClient)

    def test_fake_confluence_client_matches_protocol(self) -> None:
        assert isinstance(FakeConfluenceClient("confluence"), ConfluenceMCPClient)


# ---------------------------------------------------------------------------
# Retry integration
# ---------------------------------------------------------------------------


class _FlakyGitHubClient:
    """Fails a configurable number of times per method, then succeeds.

    Used to prove the orchestrator wraps MCP calls in :func:`with_retry`
    when a :class:`RetryConfig` is supplied. Each attempt counter is
    exposed so the assertion can verify the total number of invocations.
    """

    source_type = "github"

    def __init__(
        self,
        name: str,
        repos: list[dict[str, Any]],
        list_repos_failures: int = 0,
        pr_failures: int = 0,
        codeowners_failures: int = 0,
    ) -> None:
        self.name = name
        self._repos = repos
        self._list_repos_remaining = list_repos_failures
        self._pr_remaining = pr_failures
        self._codeowners_remaining = codeowners_failures
        self.list_repos_calls = 0
        self.pr_calls = 0
        self.codeowners_calls = 0
        self.closed = False

    async def list_repositories(self) -> list[dict[str, Any]]:
        self.list_repos_calls += 1
        if self._list_repos_remaining > 0:
            self._list_repos_remaining -= 1
            raise RuntimeError("transient list_repositories failure")
        return list(self._repos)

    async def get_pull_requests(self, repo_name: str) -> list[dict[str, Any]]:
        self.pr_calls += 1
        if self._pr_remaining > 0:
            self._pr_remaining -= 1
            raise RuntimeError(f"transient PR failure for {repo_name}")
        return []

    async def get_codeowners(self, repo_name: str) -> str | None:
        self.codeowners_calls += 1
        if self._codeowners_remaining > 0:
            self._codeowners_remaining -= 1
            raise RuntimeError(f"transient CODEOWNERS failure for {repo_name}")
        return None

    async def close(self) -> None:
        self.closed = True


class TestRetryIntegration:
    """Verify MCPOrchestrator honours an injected RetryConfig."""

    async def test_transient_list_repositories_failure_is_retried(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_mock = AsyncMock()
        monkeypatch.setattr("src.ingestion.retry.asyncio.sleep", sleep_mock)

        writer = _make_writer_mock()
        retry_config = RetryConfig(
            max_attempts=3, base_delay=0.1, max_delay=1.0
        )
        orch = MCPOrchestrator(_make_registry(), writer, retry_config=retry_config)

        client = _FlakyGitHubClient(
            "github",
            repos=[_repo_payload(1, "repo-a")],
            list_repos_failures=2,  # fails twice, succeeds on 3rd attempt
        )
        orch.register_github_client("github", client)

        await orch.full_sync_github("github")

        assert client.list_repos_calls == 3  # 1 initial + 2 retries
        assert sleep_mock.await_count == 2

    async def test_retries_exhausted_falls_back_to_error_swallow(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Final fallback: orchestrator still logs + returns WriteResult."""

        monkeypatch.setattr(
            "src.ingestion.retry.asyncio.sleep", AsyncMock()
        )

        writer = _make_writer_mock()
        retry_config = RetryConfig(
            max_attempts=3, base_delay=0.1, max_delay=1.0
        )
        orch = MCPOrchestrator(_make_registry(), writer, retry_config=retry_config)

        client = _FlakyGitHubClient(
            "github",
            repos=[],
            list_repos_failures=10,  # never recovers within max_attempts
        )
        orch.register_github_client("github", client)

        with caplog.at_level(logging.ERROR, logger="src.ingestion.orchestrator"):
            result = await orch.full_sync_github("github")

        # Three attempts were made, then orchestrator caught the
        # exception and returned an empty result (Requirement 1.7
        # "retry, then log and continue").
        assert client.list_repos_calls == 3
        assert isinstance(result, WriteResult)
        writer.write.assert_not_awaited()
        assert any(
            "list_repositories failed" in rec.message for rec in caplog.records
        )

    async def test_pr_fetch_retry_per_repo(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "src.ingestion.retry.asyncio.sleep", AsyncMock()
        )

        writer = _make_writer_mock()
        retry_config = RetryConfig(
            max_attempts=3, base_delay=0.1, max_delay=1.0
        )
        orch = MCPOrchestrator(_make_registry(), writer, retry_config=retry_config)

        client = _FlakyGitHubClient(
            "github",
            repos=[_repo_payload(1, "repo-a")],
            pr_failures=1,  # one transient failure, then succeeds
        )
        orch.register_github_client("github", client)

        await orch.full_sync_github("github")
        assert client.pr_calls == 2  # initial + 1 retry

    async def test_without_retry_config_calls_are_not_wrapped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Baseline: no retry config == no retries, no sleeps."""

        sleep_mock = AsyncMock()
        monkeypatch.setattr("src.ingestion.retry.asyncio.sleep", sleep_mock)

        writer = _make_writer_mock()
        orch = MCPOrchestrator(_make_registry(), writer)  # no retry_config

        client = _FlakyGitHubClient(
            "github",
            repos=[_repo_payload(1, "repo-a")],
            list_repos_failures=1,
        )
        orch.register_github_client("github", client)

        result = await orch.full_sync_github("github")

        # Single attempt, failure swallowed via existing try/except.
        assert client.list_repos_calls == 1
        assert isinstance(result, WriteResult)
        sleep_mock.assert_not_awaited()
