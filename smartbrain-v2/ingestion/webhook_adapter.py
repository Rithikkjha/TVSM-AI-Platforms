"""Webhook adapter for GitHub, Jira, and Confluence.

The :class:`WebhookAdapter` exposes three FastAPI endpoints — one per
source system — that receive push-style events, validate the sender
with a signature / shared-secret check, extract just the resource
that changed, and forward the result to the injected
:class:`~src.ingestion.orchestrator.MCPOrchestrator` via the public
:meth:`MCPOrchestrator.write_extraction_result` fast path.

Design notes (V1)
-----------------

* **No message queue.** The design explicitly calls out that V1 sits
  below the scale where Service Bus is worth the operational cost.
  Invoking the orchestrator directly is simpler and meets the 10-minute
  freshness SLO at pilot volume.
* **No DLQ.** Post-validation processing errors are logged and the
  endpoint still returns ``200`` — we rely on the 6-hour full-sync
  scheduler as the backstop so a lost webhook never leaves the graph
  permanently out of date. Returning ``200`` also stops the source
  system from retrying a pathologically bad event forever.
* **Per-webhook extraction, not per-repo.** A GitHub PR webhook carries
  the single PR payload the repo owner updated; we extract just that
  one PR rather than refetching the whole repo. Ditto Jira issues and
  Confluence pages.
* **Signature verification is timing-safe.** Both helpers use
  :func:`hmac.compare_digest` so a byte-by-byte compare can't leak the
  secret through timing.
* **No LLM on Confluence webhooks.** LLM extraction runs during the
  nightly full sync (``MCPOrchestrator.full_sync_confluence``). The
  webhook path only writes the page *metadata* so the endpoint stays
  well under any freshness SLO.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse

from processing.extraction.deterministic import (
    ExtractionResult,
    extract_confluence_page_metadata,
    extract_pr,
    extract_ticket,
)
from ingestion.orchestrator import MCPOrchestrator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Signature helpers
# ---------------------------------------------------------------------------


def verify_github_signature(
    raw_body: bytes,
    signature_header: str | None,
    secret: str,
) -> bool:
    """Verify a GitHub ``X-Hub-Signature-256`` header.

    GitHub signs each webhook body with HMAC-SHA256 keyed on the
    repository's (or app's) webhook secret. The resulting hex digest
    is placed in the ``X-Hub-Signature-256`` header prefixed with
    ``sha256=``. A missing header, an unexpected prefix, or a digest
    mismatch all return ``False`` — callers should translate that into
    a ``401 Unauthorized`` response.

    The comparison uses :func:`hmac.compare_digest` so the wall-clock
    time to reject an invalid signature is independent of how many
    leading bytes matched (prevents timing attacks).

    Args:
        raw_body: The exact body bytes that GitHub signed. Any
            re-serialization (pretty-printing, reordering) breaks the
            signature.
        signature_header: The full value of ``X-Hub-Signature-256`` or
            ``None`` if the header was absent.
        secret: The shared secret configured on the GitHub webhook.

    Returns:
        ``True`` if the signature is well-formed and matches, else
        ``False``.
    """

    if not signature_header or not signature_header.startswith("sha256="):
        return False
    if not secret:
        # Misconfiguration: the adapter was wired up without a secret.
        # Fail closed rather than accepting every request.
        return False

    provided = signature_header.removeprefix("sha256=")
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(provided, expected)


def verify_atlassian_signature(
    raw_body: bytes,
    signature: str | None,
    secret: str,
) -> bool:
    """Verify an Atlassian-provided signature or shared secret.

    Atlassian's webhook auth story is less uniform than GitHub's — some
    instances sign the body with HMAC-SHA256, others drop a shared
    secret straight into a header or query parameter. For V1 we
    standardize on HMAC-SHA256 and document that callers must configure
    their Atlassian webhook to send the hex digest in the
    ``X-Hub-Signature-256`` header (Jira/Confluence Cloud both support
    this via webhook templates).

    The provided signature may optionally carry the ``sha256=`` prefix
    so operators can reuse a GitHub-style signing proxy if they have
    one.

    Returns:
        ``True`` if the signature matches, else ``False``.
    """

    if not signature or not secret:
        return False

    provided = signature.removeprefix("sha256=")
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(provided, expected)


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


def _client_host(request: Request) -> str:
    """Best-effort client IP for log attribution."""

    client = request.client
    if client is None:
        return "unknown"
    return client.host or "unknown"


def _payload_hash(raw_body: bytes) -> str:
    """Short SHA-256 digest for use in malformed-payload logs."""

    return hashlib.sha256(raw_body).hexdigest()[:16]


class WebhookAdapter:
    """FastAPI route group receiving source-system webhooks.

    The adapter is stateless — it only holds references to the
    orchestrator and the two webhook secrets. A single instance can be
    shared across all FastAPI workers.

    Wiring looks like::

        adapter = WebhookAdapter(
            orchestrator=orchestrator,
            github_webhook_secret=settings.github_webhook_secret,
            atlassian_webhook_secret=settings.atlassian_webhook_secret,
        )
        app.include_router(adapter.create_router())
    """

    # GitHub event types this adapter knows how to process. Events
    # outside this set are accepted (200) and logged but don't mutate
    # the graph — keeps noisy repos from filling the error logs.
    _GITHUB_KNOWN_EVENTS: frozenset[str] = frozenset(
        {"push", "pull_request", "pull_request_review", "ping"}
    )
    # Jira event types we process. The "jira:" prefix is Atlassian's
    # own naming convention in webhook payloads.
    _JIRA_KNOWN_EVENTS: frozenset[str] = frozenset(
        {"jira:issue_created", "jira:issue_updated"}
    )
    _CONFLUENCE_KNOWN_EVENTS: frozenset[str] = frozenset(
        {"page_created", "page_updated"}
    )

    def __init__(
        self,
        orchestrator: MCPOrchestrator,
        github_webhook_secret: str | None,
        atlassian_webhook_secret: str | None,
    ) -> None:
        self._orchestrator = orchestrator
        self._github_secret = github_webhook_secret or ""
        self._atlassian_secret = atlassian_webhook_secret or ""

    # -- router ---------------------------------------------------------

    def create_router(self) -> APIRouter:
        """Return a FastAPI router with the three webhook endpoints."""

        router = APIRouter(prefix="/webhooks", tags=["webhooks"])

        @router.post("/github")
        async def github_webhook(  # pyright: ignore[reportUnusedFunction]
            request: Request,
            x_hub_signature_256: str | None = Header(default=None),
            x_github_event: str | None = Header(default=None),
        ) -> JSONResponse:
            return await self._handle_github(
                request, x_hub_signature_256, x_github_event
            )

        @router.post("/jira")
        async def jira_webhook(  # pyright: ignore[reportUnusedFunction]
            request: Request,
            x_hub_signature_256: str | None = Header(default=None),
        ) -> JSONResponse:
            return await self._handle_jira(request, x_hub_signature_256)

        @router.post("/confluence")
        async def confluence_webhook(  # pyright: ignore[reportUnusedFunction]
            request: Request,
            x_hub_signature_256: str | None = Header(default=None),
        ) -> JSONResponse:
            return await self._handle_confluence(request, x_hub_signature_256)

        return router

    # -- handlers -------------------------------------------------------

    async def _handle_github(
        self,
        request: Request,
        signature_header: str | None,
        event_type: str | None,
    ) -> JSONResponse:
        """Process a GitHub webhook request end-to-end."""

        raw_body = await request.body()

        if not verify_github_signature(
            raw_body, signature_header, self._github_secret
        ):
            logger.warning(
                "github webhook: invalid signature from %s (payload_hash=%s)",
                _client_host(request),
                _payload_hash(raw_body),
            )
            return JSONResponse(
                {"error": "invalid_signature"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        payload = _parse_json(raw_body)
        if payload is None:
            logger.warning(
                "github webhook: malformed payload from %s (payload_hash=%s)",
                _client_host(request),
                _payload_hash(raw_body),
            )
            return JSONResponse(
                {"error": "malformed_payload"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        event = (event_type or "").strip()
        logger.info(
            "github webhook received: event=%s payload_hash=%s",
            event or "<missing>",
            _payload_hash(raw_body),
        )

        # "ping" is GitHub's hello-world event; ack and move on.
        if event == "ping":
            return JSONResponse({"status": "ok"})

        if event not in self._GITHUB_KNOWN_EVENTS:
            logger.info("github webhook: ignoring unknown event %r", event)
            return JSONResponse({"status": "ignored", "event": event})

        try:
            if event in {"pull_request", "pull_request_review"}:
                await self._process_github_pr_event(payload)
            elif event == "push":
                # V1 doesn't materialize commit-level entities; log for
                # observability and rely on the nightly sync to refresh
                # repository metadata.
                repo = payload.get("repository") or {}
                repo_name = (
                    repo.get("full_name") or repo.get("name") or "<unknown>"
                )
                logger.info(
                    "github push event for %s acknowledged (handled by full sync)",
                    repo_name,
                )
        except Exception as exc:
            # Post-validation failures: log but still return 200 so the
            # source system doesn't retry. The next full sync will pick
            # up whatever we missed.
            logger.error(
                "github webhook: processing error for event %s: %s",
                event,
                exc,
                exc_info=True,
            )

        return JSONResponse({"status": "ok"})

    async def _handle_jira(
        self,
        request: Request,
        signature_header: str | None,
    ) -> JSONResponse:
        raw_body = await request.body()

        if not verify_atlassian_signature(
            raw_body, signature_header, self._atlassian_secret
        ):
            logger.warning(
                "jira webhook: invalid signature from %s (payload_hash=%s)",
                _client_host(request),
                _payload_hash(raw_body),
            )
            return JSONResponse(
                {"error": "invalid_signature"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        payload = _parse_json(raw_body)
        if payload is None:
            logger.warning(
                "jira webhook: malformed payload from %s (payload_hash=%s)",
                _client_host(request),
                _payload_hash(raw_body),
            )
            return JSONResponse(
                {"error": "malformed_payload"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        event = str(payload.get("webhookEvent", "")).strip()
        logger.info(
            "jira webhook received: event=%s payload_hash=%s",
            event or "<missing>",
            _payload_hash(raw_body),
        )

        if event not in self._JIRA_KNOWN_EVENTS:
            logger.info("jira webhook: ignoring unknown event %r", event)
            return JSONResponse({"status": "ignored", "event": event})

        try:
            await self._process_jira_issue_event(payload)
        except Exception as exc:
            logger.error(
                "jira webhook: processing error for event %s: %s",
                event,
                exc,
                exc_info=True,
            )

        return JSONResponse({"status": "ok"})

    async def _handle_confluence(
        self,
        request: Request,
        signature_header: str | None,
    ) -> JSONResponse:
        raw_body = await request.body()

        if not verify_atlassian_signature(
            raw_body, signature_header, self._atlassian_secret
        ):
            logger.warning(
                "confluence webhook: invalid signature from %s (payload_hash=%s)",
                _client_host(request),
                _payload_hash(raw_body),
            )
            return JSONResponse(
                {"error": "invalid_signature"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        payload = _parse_json(raw_body)
        if payload is None:
            logger.warning(
                "confluence webhook: malformed payload from %s (payload_hash=%s)",
                _client_host(request),
                _payload_hash(raw_body),
            )
            return JSONResponse(
                {"error": "malformed_payload"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Confluence Cloud webhooks put the event type either at the
        # top level as ``event`` or inside a ``webhookEvent`` field
        # depending on the connector flavour. Tolerate both.
        event = str(
            payload.get("event") or payload.get("webhookEvent") or ""
        ).strip()
        logger.info(
            "confluence webhook received: event=%s payload_hash=%s",
            event or "<missing>",
            _payload_hash(raw_body),
        )

        if event not in self._CONFLUENCE_KNOWN_EVENTS:
            logger.info("confluence webhook: ignoring unknown event %r", event)
            return JSONResponse({"status": "ignored", "event": event})

        try:
            await self._process_confluence_page_event(payload)
        except Exception as exc:
            logger.error(
                "confluence webhook: processing error for event %s: %s",
                event,
                exc,
                exc_info=True,
            )

        return JSONResponse({"status": "ok"})

    # -- processing helpers ---------------------------------------------

    async def _process_github_pr_event(self, payload: dict[str, Any]) -> None:
        """Extract a single PR from a GitHub webhook and write it."""

        pr = payload.get("pull_request")
        repo = payload.get("repository") or {}
        if not isinstance(pr, dict) or not isinstance(repo, dict):
            logger.warning(
                "github PR webhook: missing pull_request or repository payload"
            )
            return

        repo_id = repo.get("id")
        if repo_id is None:
            logger.warning("github PR webhook: repository.id missing in payload")
            return

        repo_source_id = f"github:repo:{repo_id}"
        pr_result = extract_pr(pr, repo_source_id=repo_source_id)
        await self._orchestrator.write_extraction_result(pr_result)

    async def _process_jira_issue_event(self, payload: dict[str, Any]) -> None:
        """Extract a single Jira ticket from a webhook and write it."""

        issue = payload.get("issue")
        if not isinstance(issue, dict):
            logger.warning("jira webhook: missing issue payload")
            return

        ticket_result = extract_ticket(issue)
        await self._orchestrator.write_extraction_result(ticket_result)

    async def _process_confluence_page_event(
        self, payload: dict[str, Any]
    ) -> None:
        """Extract a single Confluence page's metadata and write it.

        The LLM extraction step is intentionally skipped here to keep
        the webhook latency low. The next nightly full sync picks up
        any service/dependency mentions in the page body.
        """

        page = payload.get("page")
        if not isinstance(page, dict):
            logger.warning("confluence webhook: missing page payload")
            return

        page_result = extract_confluence_page_metadata(page)
        # Skip LLM extraction on the hot path — kept as empty merge so
        # the shape stays identical to the full-sync path if we ever
        # want to add it back.
        await self._orchestrator.write_extraction_result(
            page_result.merge(ExtractionResult())
        )


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _parse_json(raw_body: bytes) -> dict[str, Any] | None:
    """Decode ``raw_body`` as a JSON object, else return ``None``.

    Webhooks must be JSON objects — lists, scalars, or malformed bytes
    are all rejected so the caller can respond with ``400``.
    """

    if not raw_body:
        return None
    try:
        parsed = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


__all__ = [
    "WebhookAdapter",
    "verify_atlassian_signature",
    "verify_github_signature",
]
