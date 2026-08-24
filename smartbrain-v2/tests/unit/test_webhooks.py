"""Unit tests for :mod:`src.webhooks.adapter`.

The adapter sits between the source-system webhook transports and
:class:`MCPOrchestrator.write_extraction_result`. Rather than stand up
real Neo4j / vector stores, these tests use a hand-rolled orchestrator
double that records the :class:`ExtractionResult` objects it was
handed, and then assert against those records.

All HTTP calls go through FastAPI's :class:`TestClient` so signature
verification, header handling, and body parsing are exercised the same
way a real request would hit the endpoint.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from processing.extraction.deterministic import ExtractionResult
from processing.extraction.writer import WriteResult
from storage.graph.schema import EntityType
from ingestion.webhook_adapter import (
    WebhookAdapter,
    verify_atlassian_signature,
    verify_github_signature,
)

GITHUB_SECRET = "github-secret-xyz"
ATLASSIAN_SECRET = "atlassian-secret-xyz"


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _RecordingOrchestrator:
    """Minimal orchestrator stand-in that records write calls.

    Only :meth:`write_extraction_result` is exercised by the adapter;
    we duck-type the rest to avoid dragging in the full orchestrator
    constructor (which needs an MCP registry and a graph writer).
    """

    def __init__(
        self, raise_on_write: BaseException | None = None
    ) -> None:
        self.writes: list[ExtractionResult] = []
        self.raise_on_write = raise_on_write

    async def write_extraction_result(
        self, result: ExtractionResult
    ) -> WriteResult:
        if self.raise_on_write is not None:
            raise self.raise_on_write
        self.writes.append(result)
        return WriteResult()


def _sign_github(body: bytes, secret: str = GITHUB_SECRET) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _sign_atlassian(body: bytes, secret: str = ATLASSIAN_SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _make_client(
    orchestrator: _RecordingOrchestrator | None = None,
    github_secret: str | None = GITHUB_SECRET,
    atlassian_secret: str | None = ATLASSIAN_SECRET,
) -> tuple[TestClient, _RecordingOrchestrator]:
    orch = orchestrator or _RecordingOrchestrator()
    adapter = WebhookAdapter(
        orchestrator=orch,  # type: ignore[arg-type]
        github_webhook_secret=github_secret,
        atlassian_webhook_secret=atlassian_secret,
    )
    app = FastAPI()
    app.include_router(adapter.create_router())
    return TestClient(app), orch


# ---------------------------------------------------------------------------
# Payload factories
# ---------------------------------------------------------------------------


def _github_pr_payload() -> dict[str, Any]:
    return {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "title": "Add retries to payments",
            "state": "open",
            "body": "Adds exponential backoff.",
            "html_url": "https://github.com/test-org/payments/pull/42",
            "user": {"login": "alice", "name": "Alice"},
            "created_at": "2024-11-01T00:00:00Z",
            "updated_at": "2024-12-01T00:00:00Z",
        },
        "repository": {
            "id": 12345,
            "name": "payments",
            "full_name": "test-org/payments",
        },
    }


def _github_push_payload() -> dict[str, Any]:
    return {
        "ref": "refs/heads/main",
        "repository": {
            "id": 12345,
            "name": "payments",
            "full_name": "test-org/payments",
        },
        "commits": [],
    }


def _jira_issue_updated_payload() -> dict[str, Any]:
    return {
        "webhookEvent": "jira:issue_updated",
        "issue": {
            "key": "ENG-1234",
            "fields": {
                "summary": "Fix payment timeout",
                "status": {"name": "In Progress"},
                "priority": {"name": "High"},
                "description": "Retry path times out after 30s.",
                "created": "2024-11-01T00:00:00.000+0000",
                "updated": "2024-12-01T00:00:00.000+0000",
            },
        },
    }


def _confluence_page_updated_payload() -> dict[str, Any]:
    return {
        "event": "page_updated",
        "page": {
            "id": "98765",
            "title": "Payments Architecture",
            "space": {"key": "ENG"},
            "_links": {"webui": "/spaces/ENG/pages/98765"},
            "version": {"when": "2024-12-01T00:00:00.000Z"},
            "body": {
                "storage": {"value": "<p>Architecture overview.</p>"}
            },
        },
    }


# ---------------------------------------------------------------------------
# Signature helper tests
# ---------------------------------------------------------------------------


class TestVerifyGithubSignature:
    def test_valid_signature_returns_true(self) -> None:
        body = b'{"hello": "world"}'
        assert (
            verify_github_signature(body, _sign_github(body), GITHUB_SECRET)
            is True
        )

    def test_mismatched_signature_returns_false(self) -> None:
        body = b'{"hello": "world"}'
        assert (
            verify_github_signature(body, "sha256=deadbeef", GITHUB_SECRET)
            is False
        )

    def test_missing_header_returns_false(self) -> None:
        assert verify_github_signature(b"{}", None, GITHUB_SECRET) is False

    def test_missing_prefix_returns_false(self) -> None:
        body = b"{}"
        digest = hmac.new(
            GITHUB_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        # Valid digest, but without the "sha256=" prefix.
        assert verify_github_signature(body, digest, GITHUB_SECRET) is False

    def test_empty_secret_returns_false(self) -> None:
        body = b"{}"
        assert verify_github_signature(body, _sign_github(body), "") is False


class TestVerifyAtlassianSignature:
    def test_valid_signature_returns_true(self) -> None:
        body = b'{"webhookEvent": "jira:issue_updated"}'
        assert (
            verify_atlassian_signature(
                body, _sign_atlassian(body), ATLASSIAN_SECRET
            )
            is True
        )

    def test_valid_signature_with_prefix_returns_true(self) -> None:
        body = b"{}"
        digest = hmac.new(
            ATLASSIAN_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        assert (
            verify_atlassian_signature(
                body, f"sha256={digest}", ATLASSIAN_SECRET
            )
            is True
        )

    def test_missing_signature_returns_false(self) -> None:
        assert (
            verify_atlassian_signature(b"{}", None, ATLASSIAN_SECRET) is False
        )

    def test_empty_secret_returns_false(self) -> None:
        body = b"{}"
        assert (
            verify_atlassian_signature(body, _sign_atlassian(body), "")
            is False
        )


# ---------------------------------------------------------------------------
# GitHub webhook endpoint
# ---------------------------------------------------------------------------


class TestGithubWebhook:
    def test_pr_opened_extracts_and_writes(self) -> None:
        client, orch = _make_client()
        body = json.dumps(_github_pr_payload()).encode()

        response = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-Hub-Signature-256": _sign_github(body),
                "X-GitHub-Event": "pull_request",
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200
        assert len(orch.writes) == 1
        result = orch.writes[0]
        pr_entities = [
            e for e in result.entities if e.label == EntityType.PR.value
        ]
        assert len(pr_entities) == 1
        assert pr_entities[0].properties["number"] == 42
        assert pr_entities[0].properties["title"] == "Add retries to payments"

    def test_push_event_is_acknowledged_without_write(self) -> None:
        client, orch = _make_client()
        body = json.dumps(_github_push_payload()).encode()

        response = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-Hub-Signature-256": _sign_github(body),
                "X-GitHub-Event": "push",
            },
        )

        assert response.status_code == 200
        # V1 doesn't persist commit-level entities; push is a no-op
        # on the graph and relies on the scheduler.
        assert orch.writes == []

    def test_invalid_signature_returns_401(self) -> None:
        client, orch = _make_client()
        body = json.dumps(_github_pr_payload()).encode()

        response = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-Hub-Signature-256": "sha256=wrong",
                "X-GitHub-Event": "pull_request",
            },
        )

        assert response.status_code == 401
        assert orch.writes == []

    def test_missing_signature_returns_401(self) -> None:
        client, orch = _make_client()
        body = json.dumps(_github_pr_payload()).encode()

        response = client.post(
            "/webhooks/github",
            content=body,
            headers={"X-GitHub-Event": "pull_request"},
        )

        assert response.status_code == 401
        assert orch.writes == []

    def test_malformed_body_returns_400(self) -> None:
        client, orch = _make_client()
        body = b"not-valid-json{"

        response = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-Hub-Signature-256": _sign_github(body),
                "X-GitHub-Event": "pull_request",
            },
        )

        assert response.status_code == 400
        assert orch.writes == []

    def test_ping_event_returns_200_without_write(self) -> None:
        client, orch = _make_client()
        body = json.dumps({"zen": "Keep it simple."}).encode()

        response = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-Hub-Signature-256": _sign_github(body),
                "X-GitHub-Event": "ping",
            },
        )

        assert response.status_code == 200
        assert orch.writes == []

    def test_unknown_event_type_logs_and_returns_200(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        client, orch = _make_client()
        body = json.dumps({"action": "starred"}).encode()

        with caplog.at_level(logging.INFO, logger="src.webhooks.adapter"):
            response = client.post(
                "/webhooks/github",
                content=body,
                headers={
                    "X-Hub-Signature-256": _sign_github(body),
                    "X-GitHub-Event": "star",
                },
            )

        assert response.status_code == 200
        assert orch.writes == []
        assert any("ignoring unknown event" in r.message for r in caplog.records)

    def test_processing_error_returns_200_without_retry(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        orch = _RecordingOrchestrator(
            raise_on_write=RuntimeError("Neo4j down")
        )
        client, _ = _make_client(orchestrator=orch)
        body = json.dumps(_github_pr_payload()).encode()

        with caplog.at_level(logging.ERROR, logger="src.webhooks.adapter"):
            response = client.post(
                "/webhooks/github",
                content=body,
                headers={
                    "X-Hub-Signature-256": _sign_github(body),
                    "X-GitHub-Event": "pull_request",
                },
            )

        # Validation passed, so we return 200 to stop GitHub from
        # retrying; the error is logged and the full sync will recover.
        assert response.status_code == 200
        assert any(
            "processing error" in r.message for r in caplog.records
        )


# ---------------------------------------------------------------------------
# Jira webhook endpoint
# ---------------------------------------------------------------------------


class TestJiraWebhook:
    def test_issue_updated_extracts_and_writes(self) -> None:
        client, orch = _make_client()
        body = json.dumps(_jira_issue_updated_payload()).encode()

        response = client.post(
            "/webhooks/jira",
            content=body,
            headers={
                "X-Hub-Signature-256": _sign_atlassian(body),
            },
        )

        assert response.status_code == 200
        assert len(orch.writes) == 1
        ticket_entities = [
            e
            for e in orch.writes[0].entities
            if e.label == EntityType.TICKET.value
        ]
        assert len(ticket_entities) == 1
        assert ticket_entities[0].properties["key"] == "ENG-1234"

    def test_invalid_signature_returns_401(self) -> None:
        client, orch = _make_client()
        body = json.dumps(_jira_issue_updated_payload()).encode()

        response = client.post(
            "/webhooks/jira",
            content=body,
            headers={"X-Hub-Signature-256": "deadbeef"},
        )

        assert response.status_code == 401
        assert orch.writes == []

    def test_unknown_event_type_is_ignored(self) -> None:
        client, orch = _make_client()
        payload = {
            "webhookEvent": "jira:issue_deleted",
            "issue": {"key": "X-1"},
        }
        body = json.dumps(payload).encode()

        response = client.post(
            "/webhooks/jira",
            content=body,
            headers={"X-Hub-Signature-256": _sign_atlassian(body)},
        )

        assert response.status_code == 200
        assert orch.writes == []


# ---------------------------------------------------------------------------
# Confluence webhook endpoint
# ---------------------------------------------------------------------------


class TestConfluenceWebhook:
    def test_page_updated_extracts_and_writes(self) -> None:
        client, orch = _make_client()
        body = json.dumps(_confluence_page_updated_payload()).encode()

        response = client.post(
            "/webhooks/confluence",
            content=body,
            headers={"X-Hub-Signature-256": _sign_atlassian(body)},
        )

        assert response.status_code == 200
        assert len(orch.writes) == 1
        page_entities = [
            e
            for e in orch.writes[0].entities
            if e.label == EntityType.CONFLUENCE_PAGE.value
        ]
        assert len(page_entities) == 1
        assert page_entities[0].properties["title"] == "Payments Architecture"

    def test_invalid_signature_returns_401(self) -> None:
        client, orch = _make_client()
        body = json.dumps(_confluence_page_updated_payload()).encode()

        response = client.post(
            "/webhooks/confluence",
            content=body,
            headers={"X-Hub-Signature-256": "nope"},
        )

        assert response.status_code == 401
        assert orch.writes == []

    def test_malformed_body_returns_400(self) -> None:
        client, orch = _make_client()
        body = b"[]"  # JSON but not an object

        response = client.post(
            "/webhooks/confluence",
            content=body,
            headers={"X-Hub-Signature-256": _sign_atlassian(body)},
        )

        assert response.status_code == 400
        assert orch.writes == []
