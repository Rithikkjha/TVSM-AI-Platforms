"""LLM-backed extraction for unstructured text.

Deterministic extraction (``src/extraction/deterministic.py``) covers
structured source data — PR fields, ticket fields, repository
metadata, CODEOWNERS — where each graph entity is a direct mapping
from a JSON field. But plenty of knowledge lives in *free-form*
text: Confluence architecture pages, long PR descriptions, incident
write-ups. That's what this module handles.

Each public extractor method asks an Azure OpenAI ``gpt-4o``
deployment to read a chunk of free text and emit a small, strict
JSON object describing which services are mentioned and which
``DEPENDS_ON`` claims the text makes. The result is mapped to the
same :class:`~src.extraction.deterministic.ExtractedEntity` /
:class:`~src.extraction.deterministic.ExtractedRelationship` types
the deterministic extractor uses, so the write coordinator treats
both paths uniformly.

Key design choices
------------------

* **Known-services whitelist** — callers pass the list of services
  that actually exist in the graph. Anything the model invents
  outside that list is discarded. This is the primary guard against
  hallucination (Requirement 1.2 + 1.9).
* **JSON mode + temperature 0** — we rely on the model's
  ``response_format={"type": "json_object"}`` mode and zero
  temperature for deterministic, parseable outputs.
* **Graceful JSON failures** — if the model returns invalid JSON,
  we log and return an empty :class:`ExtractionResult`. The graph
  simply misses this one extraction; the next sync will retry.
* **Hard errors surface** — network timeouts, rate limiting, and
  API errors raise :class:`LLMExtractionError` so the caller can
  decide whether to retry. Exposing these lets the orchestrator
  apply its own backoff policy (Requirement 1.7).
* **Confidence scoring** — every emitted entity/relationship carries
  a ``"high" | "medium" | "low"`` confidence propagated from the
  model's self-assessment (Requirement 1.9).
"""

from __future__ import annotations

import json
import logging
from types import TracebackType
from typing import Any, Self

import openai
from openai import AsyncAzureOpenAI

from config.settings import Settings
from processing.extraction.deterministic import (
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionResult,
    compute_text_hash,
)
from storage.graph.schema import EntityType, RelationshipType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Hard wall on how long we're willing to wait for a single LLM call
#: before surfacing a timeout. The design doc calls out 30 s explicitly
#: — anything longer and the webhook/sync loop starts to back up.
LLM_REQUEST_TIMEOUT_SECONDS: float = 30.0

#: Upper bound on the response size. Structured outputs are tiny (a
#: few service names + a handful of edges), so 2000 tokens is plenty.
LLM_MAX_OUTPUT_TOKENS: int = 2000

#: Deterministic sampling — LLM extraction must be reproducible to
#: play nicely with the idempotency machinery in the write
#: coordinator.
LLM_TEMPERATURE: float = 0.0

#: Confidence values accepted on the wire. Anything else is
#: downgraded to ``"low"``.
_ALLOWED_CONFIDENCES: frozenset[str] = frozenset({"high", "medium", "low"})


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LLMExtractionError(RuntimeError):
    """Raised when an LLM-backed extraction call fails irrecoverably.

    Wraps transport-level failures (timeouts, network errors) and
    API-level failures (rate limiting, server errors, invalid
    requests) coming from :mod:`openai`. The original exception is
    available via :attr:`__cause__`, and the caller decides whether
    to retry.

    Note: *invalid JSON* from the model does **not** raise this —
    see the docstring on :class:`LLMExtractor` for the
    graceful-degradation policy.
    """


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


_SYSTEM_PROMPT: str = (
    "You extract service dependencies from engineering documents.\n\n"
    "Output a JSON object with exactly these keys:\n"
    "  - services_mentioned: array of {name, confidence}\n"
    "  - dependencies_claimed: array of {from, to, confidence}\n"
    "  - documents_service: boolean (true if the doc documents its own service)\n"
    "  - ticket_concerns: array of {name, confidence} (for Jira tickets only)\n"
    "Where `confidence` is one of: \"high\", \"medium\", \"low\".\n\n"
    "CRITICAL RULES:\n"
    "1. You are given a known_services list. These are the ONLY valid "
    "output values for service names. You must NEVER output a name not "
    "in this list.\n"
    "2. Documents may use informal names like \"Booking Service\" or "
    "\"BookingService\". You must fuzzy-match to the closest canonical "
    "name in known_services. Example: \"BookingService\" in a doc likely "
    "maps to \"booking-crud-services\" because both contain \"booking\".\n"
    "3. Only emit a dependency if the text explicitly states one service "
    "calls, forwards to, routes to, uses, depends on, or consumes "
    "another.\n"
    "4. If you cannot confidently map a mentioned service to a "
    "known_services entry, OMIT it entirely.\n"
    "5. Use confidence `high` for obvious matches, `medium` for "
    "interpretive fuzzy matches, `low` for uncertain.\n"
    "6. If nothing relevant is found, return empty arrays. Do not guess.\n"
    "7. The `from` field in dependencies is always the service being "
    "analyzed (use its canonical known_services name). The `to` field "
    "must be a DIFFERENT service from known_services."
)


def _build_confluence_user_prompt(
    page_title: str,
    page_content: str,
    known_services: list[str],
) -> str:
    """Render the per-call user message for Confluence extraction."""

    known = json.dumps(sorted(set(known_services)))
    return (
        "Analyze the following Confluence page and extract service "
        "mentions and dependency claims.\n\n"
        f"known_services: {known}\n\n"
        f"page_title: {page_title}\n\n"
        "page_content:\n---\n"
        f"{page_content}\n---"
    )


def _build_pr_user_prompt(
    pr_title: str,
    pr_body: str,
    known_services: list[str],
) -> str:
    """Render the per-call user message for PR-description extraction."""

    known = json.dumps(sorted(set(known_services)))
    return (
        "Analyze the following pull request description and extract "
        "service mentions and dependency claims.\n\n"
        f"known_services: {known}\n\n"
        f"pr_title: {pr_title}\n\n"
        "pr_body:\n---\n"
        f"{pr_body}\n---"
    )


def _build_steering_user_prompt(
    service_name: str,
    steering_text: str,
    known_services: list[str],
) -> str:
    """Render the per-call user message for steering-file extraction.

    Steering files are the auto-generated per-service knowledge docs
    (product / structure / tech). They describe one service in depth
    and frequently spell out that service's runtime dependencies. The
    wire schema keeps the existing ``services_mentioned`` /
    ``dependencies_claimed`` keys — so ``_filter_known_services`` and
    ``_filter_known_dependencies`` apply verbatim — and ADDS a single
    ``documents_service`` boolean: whether this steering doc documents
    its own service (``service_name``). That boolean drives the
    optional ``DOCUMENTED_IN`` edge in :meth:`LLMExtractor._build_steering_result`.
    """

    known = json.dumps(sorted(set(known_services)))
    return (
        "Analyze the following steering document and extract service "
        "dependency claims.\n\n"
        "In addition to the standard keys, include a boolean "
        "`documents_service`: set it to true when this document "
        "describes/documents the service named below, false "
        "otherwise.\n\n"
        "CRITICAL MATCHING RULE: The document uses human-readable names "
        "like 'BookingService', 'Booking Service', 'TVSConnectEV', "
        "'notification service', etc. The known_services list uses "
        "repo-slug names like 'booking-crud-services', "
        "'tvs-connect-android-app-docs', 'async-communication-service'. "
        "You MUST fuzzy-match these. Examples:\n"
        "  - 'BookingService' or 'Booking Service' → 'booking-crud-services'\n"
        "  - 'TVSConnectEV' → 'tvs-connect-android-app-docs'\n"
        "  - 'auth service' or 'tvsm auth' → 'tvsm-auth'\n"
        "  - 'OTP service' → 'tvsm-otp-service'\n"
        "  - 'notification' → 'async-communication-service'\n"
        "Output ONLY canonical names from the known_services list.\n\n"
        f"known_services: {known}\n\n"
        f"service_name: {service_name}\n\n"
        "steering_text:\n---\n"
        f"{steering_text}\n---"
    )


def _build_jira_user_prompt(
    ticket_key: str,
    ticket_text: str,
    known_services: list[str],
) -> str:
    """Render the per-call user message for Jira-ticket extraction.

    Jira tickets describe work against one or more services. Beyond the
    standard ``services_mentioned`` / ``dependencies_claimed`` keys —
    which keep ``_filter_known_services`` and
    ``_filter_known_dependencies`` applicable verbatim — the wire schema
    ADDS a single ``ticket_concerns`` array of service names: the
    services this ticket concerns/affects. Those names drive the
    ``Ticket LINKED_TO Service`` edges in
    :meth:`LLMExtractor._build_jira_result` (Req 10.1).
    """

    known = json.dumps(sorted(set(known_services)))
    return (
        "Analyze the following Jira ticket and extract service mentions "
        "and dependency claims.\n\n"
        "In addition to the standard keys, include a `ticket_concerns` "
        "array of {name, confidence} objects naming the services this "
        "ticket concerns, affects, or is about. Only use names that "
        "appear verbatim (case-insensitive) in known_services.\n\n"
        f"known_services: {known}\n\n"
        f"ticket_key: {ticket_key}\n\n"
        "ticket_text:\n---\n"
        f"{ticket_text}\n---"
    )


# ---------------------------------------------------------------------------
# Response parsing helpers
# ---------------------------------------------------------------------------


def _normalize_confidence(raw: Any) -> str:
    """Return one of ``"high" | "medium" | "low"``.

    Values outside the allowed set — including ``None``, numbers, or
    typos like ``"HIGH"`` — are normalized to ``"low"`` so callers
    never have to guard against surprise strings. The case-insensitive
    match keeps the parser forgiving without loosening the schema.
    """

    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered in _ALLOWED_CONFIDENCES:
            return lowered
    return "low"


def _filter_known_services(
    services: list[dict[str, Any]],
    known_services: set[str],
) -> list[tuple[str, str]]:
    """Drop entries whose ``name`` isn't in ``known_services``.

    The match is case-insensitive (the model may echo capitalization
    from prose) but the returned canonical name is the spelling from
    the known-services list so downstream ``source_id`` values stay
    stable.

    Returns a list of ``(canonical_name, confidence)`` tuples,
    deduplicated by canonical name (first occurrence wins — if the
    model emits the same service twice we keep the first
    confidence).
    """

    canonical_lookup = {s.lower(): s for s in known_services}
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for item in services:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        canonical = canonical_lookup.get(name.strip().lower())
        if canonical is None or canonical in seen:
            continue
        seen.add(canonical)
        result.append((canonical, _normalize_confidence(item.get("confidence"))))
    return result


def _filter_known_dependencies(
    deps: list[dict[str, Any]],
    known_services: set[str],
) -> list[tuple[str, str, str]]:
    """Keep only dependency claims between two known services.

    Self-loops (``from == to``) are dropped because the schema
    doesn't allow a service to depend on itself and they're almost
    always a hallucination artifact. Duplicate ``(from, to)`` pairs
    collapse — the first-seen confidence wins.
    """

    canonical_lookup = {s.lower(): s for s in known_services}
    seen: set[tuple[str, str]] = set()
    result: list[tuple[str, str, str]] = []
    for item in deps:
        if not isinstance(item, dict):
            continue
        src = item.get("from")
        dst = item.get("to")
        if not isinstance(src, str) or not isinstance(dst, str):
            continue
        src_canonical = canonical_lookup.get(src.strip().lower())
        dst_canonical = canonical_lookup.get(dst.strip().lower())
        if src_canonical is None or dst_canonical is None:
            continue
        if src_canonical == dst_canonical:
            continue
        key = (src_canonical, dst_canonical)
        if key in seen:
            continue
        seen.add(key)
        result.append(
            (src_canonical, dst_canonical, _normalize_confidence(item.get("confidence")))
        )
    return result


def _parse_llm_json(raw_text: str) -> dict[str, Any] | None:
    """Parse the model's JSON response, or return ``None`` on failure.

    Returning ``None`` (rather than raising) is the contract we hand
    to callers: graceful degradation when the model misbehaves, hard
    errors only when the transport fails. Callers log context and
    substitute an empty :class:`ExtractionResult`.
    """

    try:
        parsed = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("LLM returned invalid JSON: %s; payload=%r", exc, raw_text)
        return None
    if not isinstance(parsed, dict):
        logger.error("LLM JSON root was not an object: type=%s", type(parsed).__name__)
        return None
    return parsed


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------


class LLMExtractor:
    """Async client that wraps Azure OpenAI for unstructured extraction.

    The extractor is designed to be long-lived: construct one per
    process, reuse it across many extractions, and :meth:`close` it on
    shutdown. It can also be used as an async context manager::

        async with LLMExtractor(...) as ext:
            result = await ext.extract_from_confluence_page(...)

    When an :class:`openai.AsyncAzureOpenAI` is injected via
    ``client`` the extractor will not close it on :meth:`close` — the
    caller retains ownership. This matches the pattern used in
    :class:`~src.extraction.embeddings.EmbeddingService` and
    :class:`~src.models.vector_store.AzureAISearchVectorStore`.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment_name: str,
        api_version: str,
        *,
        client: AsyncAzureOpenAI | None = None,
    ) -> None:
        if not endpoint:
            raise ValueError("LLMExtractor requires a non-empty endpoint")
        if not api_key:
            raise ValueError("LLMExtractor requires a non-empty api_key")
        if not deployment_name:
            raise ValueError("LLMExtractor requires a non-empty deployment_name")
        if not api_version:
            raise ValueError("LLMExtractor requires a non-empty api_version")

        self._endpoint = endpoint
        self._deployment_name = deployment_name
        self._api_version = api_version
        self._owns_client = client is None
        import httpx as _httpx
        _http_client = _httpx.AsyncClient(verify=False, timeout=LLM_REQUEST_TIMEOUT_SECONDS)
        self._client: AsyncAzureOpenAI = client or AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            timeout=LLM_REQUEST_TIMEOUT_SECONDS,
            http_client=_http_client,
        )

    # -- public API ------------------------------------------------------

    async def extract_from_confluence_page(
        self,
        page_source_id: str,
        page_title: str,
        page_content: str,
        known_services: list[str],
    ) -> ExtractionResult:
        """Extract service mentions and dependency claims from a page.

        The ``page_source_id`` must be the canonical Neo4j id of the
        :class:`ConfluencePage` node (as produced by the deterministic
        extractor's :func:`extract_confluence_page_metadata`). Each
        service mention produces a ``DOCUMENTED_IN`` edge from the
        mentioned :class:`Service` to this page — matching the V1
        schema direction ``(Service)-[:DOCUMENTED_IN]->(ConfluencePage)``.

        Dependency claims produce ``DEPENDS_ON`` edges between
        services. Both endpoints must be in ``known_services`` or the
        claim is dropped (hallucination guard).

        An empty ``page_content`` short-circuits to an empty result
        without calling the API (no tokens spent on noise).
        """

        if not page_source_id:
            raise ValueError("extract_from_confluence_page requires page_source_id")
        if not page_content.strip():
            return ExtractionResult()

        user_prompt = _build_confluence_user_prompt(
            page_title=page_title,
            page_content=page_content,
            known_services=known_services,
        )
        parsed = await self._invoke_llm(user_prompt)
        if parsed is None:
            return ExtractionResult()

        return self._build_confluence_result(
            parsed=parsed,
            page_source_id=page_source_id,
            known_services=set(known_services),
        )

    async def extract_from_pr_description(
        self,
        pr_source_id: str,
        pr_title: str,
        pr_body: str,
        repo_source_id: str,
        known_services: list[str],
    ) -> ExtractionResult:
        """Extract service mentions and dependency claims from a PR.

        ``pr_source_id`` is informational (used for logging only) —
        the PR node itself is always produced deterministically. The
        LLM's job here is strictly to surface *additional*
        ``DEPENDS_ON`` edges when a PR description says something
        like "this PR wires service-a up to service-b."

        ``repo_source_id`` is currently unused in the returned graph
        writes but is captured so that future versions can attribute
        extracted dependencies to the originating repo without
        breaking the method signature.
        """

        if not pr_source_id:
            raise ValueError("extract_from_pr_description requires pr_source_id")
        if not repo_source_id:
            raise ValueError("extract_from_pr_description requires repo_source_id")
        if not pr_body.strip():
            return ExtractionResult()

        user_prompt = _build_pr_user_prompt(
            pr_title=pr_title,
            pr_body=pr_body,
            known_services=known_services,
        )
        parsed = await self._invoke_llm(user_prompt)
        if parsed is None:
            return ExtractionResult()

        return self._build_pr_result(
            parsed=parsed,
            known_services=set(known_services),
        )

    async def extract_from_steering(
        self,
        service_source_id: str,
        service_name: str,
        steering_text: str,
        page_source_id: str | None,
        known_services: list[str],
    ) -> ExtractionResult:
        """Extract dependency + documentation edges from steering prose.

        Steering files are per-service knowledge docs. This method
        surfaces two kinds of edges (Req 9.1):

        * ``Service DEPENDS_ON Service`` — dependency claims the doc
          makes between two known services.
        * ``(Service)-[:DOCUMENTED_IN]->(ConfluencePage)`` — emitted
          only when ``page_source_id`` is provided (the steering doc
          has a backing ConfluencePage node) *and* the model asserts
          the doc documents its own service.

        ``service_source_id`` is the canonical :class:`Service` node id
        used as the ``DOCUMENTED_IN`` source, grounding that edge to the
        service the steering file belongs to. ``service_name`` is passed
        to the prompt for context only.

        Empty ``steering_text`` short-circuits to an empty result
        without spending tokens. A malformed / unparseable LLM
        response degrades gracefully to an empty result (Req 9.6) —
        the next sync retries. This method emits **edges only**; no
        Service or ConfluencePage node is ever created here (Req 9.5).
        """

        if not service_source_id:
            raise ValueError("extract_from_steering requires service_source_id")
        if not steering_text.strip():
            return ExtractionResult()

        user_prompt = _build_steering_user_prompt(
            service_name=service_name,
            steering_text=steering_text,
            known_services=known_services,
        )
        parsed = await self._invoke_llm(user_prompt)
        if parsed is None:
            return ExtractionResult()

        return self._build_steering_result(
            parsed=parsed,
            service_source_id=service_source_id,
            page_source_id=page_source_id,
            known_services=set(known_services),
        )

    async def extract_from_jira_ticket(
        self,
        ticket_source_id: str,
        ticket_key: str,
        ticket_text: str,
        known_services: list[str],
        known_tickets: list[str],
    ) -> ExtractionResult:
        """Extract dependency + linkage edges from Jira-ticket text.

        Jira tickets are free-form work descriptions (summary +
        description + acceptance criteria + comments). This method
        surfaces two kinds of edges (Req 10.1):

        * ``Service DEPENDS_ON Service`` — dependency claims the ticket
          text makes between two known services.
        * ``(Ticket)-[:LINKED_TO]->(Service)`` — for every service the
          ticket concerns, but only when ``ticket_key`` is itself a
          member of ``known_tickets`` (Req 10.2). This grounds the edge
          to a ticket node that actually exists in the graph.

        ``ticket_source_id`` is the canonical :class:`Ticket` node id
        used as the ``LINKED_TO`` source. ``ticket_key`` is passed to
        the prompt for context and gates the ``LINKED_TO`` edges.

        Empty ``ticket_text`` short-circuits to an empty result without
        spending tokens. A malformed / unparseable LLM response degrades
        gracefully to an empty result (Req 10.6) — the next sync
        retries. This method emits **edges only**; no Service or Ticket
        node is ever created here (Req 10.5).
        """

        if not ticket_source_id:
            raise ValueError("extract_from_jira_ticket requires ticket_source_id")
        if not ticket_text.strip():
            return ExtractionResult()

        user_prompt = _build_jira_user_prompt(
            ticket_key=ticket_key,
            ticket_text=ticket_text,
            known_services=known_services,
        )
        parsed = await self._invoke_llm(user_prompt)
        if parsed is None:
            return ExtractionResult()

        return self._build_jira_result(
            parsed=parsed,
            ticket_source_id=ticket_source_id,
            ticket_key=ticket_key,
            known_services=set(known_services),
            known_tickets=set(known_tickets),
        )

    async def close(self) -> None:
        """Close the underlying Azure OpenAI client if we own it."""

        if self._owns_client:
            await self._client.close()

    # -- context manager -------------------------------------------------

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

    async def _invoke_llm(self, user_prompt: str) -> dict[str, Any] | None:
        """Call Azure OpenAI and return the parsed JSON body.

        Returns ``None`` when the API responded successfully but with
        unparseable content — the caller treats this as an empty
        extraction and moves on. Transport / API failures, including
        timeouts, are raised as :class:`LLMExtractionError` so the
        orchestrator can retry with backoff.
        """

        try:
            response = await self._client.chat.completions.create(
                model=self._deployment_name,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_OUTPUT_TOKENS,
                timeout=LLM_REQUEST_TIMEOUT_SECONDS,
            )
        except openai.APITimeoutError as exc:
            logger.warning("LLM extraction timed out after %ss", LLM_REQUEST_TIMEOUT_SECONDS)
            raise LLMExtractionError(
                f"LLM extraction timed out after {LLM_REQUEST_TIMEOUT_SECONDS}s"
            ) from exc
        except openai.RateLimitError as exc:
            logger.warning("Azure OpenAI rate limit hit during LLM extraction: %s", exc)
            raise LLMExtractionError("Azure OpenAI rate limit exceeded") from exc
        except openai.APIError as exc:
            logger.error("Azure OpenAI API error during LLM extraction: %s", exc)
            raise LLMExtractionError(f"Azure OpenAI API error: {exc}") from exc
        except Exception as exc:  # pragma: no cover - defensive catch-all
            logger.error("Unexpected error during LLM extraction: %s", exc)
            raise LLMExtractionError(f"Unexpected LLM failure: {exc}") from exc

        self._log_token_usage(response)

        if not response.choices:
            logger.error("LLM returned no choices")
            return None
        content = response.choices[0].message.content
        if not content:
            logger.error("LLM returned empty content")
            return None

        return _parse_llm_json(content)

    @staticmethod
    def _log_token_usage(response: Any) -> None:
        """Emit a single info log line with prompt/completion/total tokens.

        Token accounting is the main cost-tracking signal for LLM
        extraction; logging it per call lets us aggregate usage in
        the log pipeline without standing up a dedicated metrics
        path in V1.
        """

        usage = getattr(response, "usage", None)
        if usage is None:
            return
        logger.info(
            "LLM token usage: prompt=%s completion=%s total=%s",
            getattr(usage, "prompt_tokens", None),
            getattr(usage, "completion_tokens", None),
            getattr(usage, "total_tokens", None),
        )

    def _build_confluence_result(
        self,
        parsed: dict[str, Any],
        page_source_id: str,
        known_services: set[str],
    ) -> ExtractionResult:
        """Translate a parsed LLM response into graph writes for a page.

        The caller guarantees ``parsed`` is a dict. Individual fields
        are defensively typed: missing or malformed arrays collapse
        to empty lists rather than raising, because partial extraction
        is better than no extraction.
        """

        services_raw = parsed.get("services_mentioned") or []
        deps_raw = parsed.get("dependencies_claimed") or []
        if not isinstance(services_raw, list):
            services_raw = []
        if not isinstance(deps_raw, list):
            deps_raw = []

        service_hits = _filter_known_services(services_raw, known_services)
        dep_hits = _filter_known_dependencies(deps_raw, known_services)

        relationships: list[ExtractedRelationship] = []

        # DOCUMENTED_IN edges from each mentioned Service to the page.
        for name, confidence in service_hits:
            service_source_id = f"service:{name}"
            relationships.append(
                ExtractedRelationship(
                    source_label=EntityType.SERVICE.value,
                    source_id=service_source_id,
                    target_label=EntityType.CONFLUENCE_PAGE.value,
                    target_id=page_source_id,
                    rel_type=RelationshipType.DOCUMENTED_IN.value,
                    properties={
                        "created_at": "",
                        "source": "llm:confluence",
                        "text_hash": compute_text_hash(
                            {
                                "edge": "DOCUMENTED_IN",
                                "service": name,
                                "page": page_source_id,
                            }
                        ),
                    },
                    confidence=confidence,
                )
            )

        # DEPENDS_ON edges claimed by the page.
        for src, dst, confidence in dep_hits:
            relationships.append(
                ExtractedRelationship(
                    source_label=EntityType.SERVICE.value,
                    source_id=f"service:{src}",
                    target_label=EntityType.SERVICE.value,
                    target_id=f"service:{dst}",
                    rel_type=RelationshipType.DEPENDS_ON.value,
                    properties={
                        "created_at": "",
                        "dependency_type": "runtime",
                        "source": "llm:confluence",
                        "text_hash": compute_text_hash(
                            {
                                "edge": "DEPENDS_ON",
                                "from": src,
                                "to": dst,
                                "evidence": page_source_id,
                            }
                        ),
                    },
                    confidence=confidence,
                )
            )

        # No ExtractedEntity objects are emitted here: Service nodes
        # are already materialized by the repository extractor, and
        # the ConfluencePage is materialized by
        # extract_confluence_page_metadata. The LLM only contributes
        # edges.
        return ExtractionResult(entities=[], relationships=relationships)

    def _build_steering_result(
        self,
        parsed: dict[str, Any],
        service_source_id: str,
        page_source_id: str | None,
        known_services: set[str],
    ) -> ExtractionResult:
        """Translate a parsed LLM response into graph writes for a steering doc.

        Mirrors :meth:`_build_confluence_result`: individual fields are
        defensively typed so malformed arrays collapse to empty lists
        rather than raising (partial extraction beats none). Emits
        edges only (Req 9.5):

        * ``Service DEPENDS_ON Service`` for every claim whose endpoints
          both survive :func:`_filter_known_dependencies` (grounding +
          canonical spelling + self-loop/dupe drop — Req 9.2/9.7/9.8).
        * ``(Service)-[:DOCUMENTED_IN]->(ConfluencePage)`` when a backing
          ``page_source_id`` exists and the model flagged
          ``documents_service`` truthy.

        Every relationship is tagged ``properties["source"] =
        "llm:steering"`` (provenance, Req 9.4) and carries the
        propagated confidence (Req 9.3).
        """

        deps_raw = parsed.get("dependencies_claimed") or []
        if not isinstance(deps_raw, list):
            deps_raw = []

        dep_hits = _filter_known_dependencies(deps_raw, known_services)

        relationships: list[ExtractedRelationship] = []

        # DEPENDS_ON edges claimed by the steering doc.
        for src, dst, confidence in dep_hits:
            relationships.append(
                ExtractedRelationship(
                    source_label=EntityType.SERVICE.value,
                    source_id=f"service:{src}",
                    target_label=EntityType.SERVICE.value,
                    target_id=f"service:{dst}",
                    rel_type=RelationshipType.DEPENDS_ON.value,
                    properties={
                        "created_at": "",
                        "dependency_type": "runtime",
                        "source": "llm:steering",
                        "text_hash": compute_text_hash(
                            {
                                "edge": "DEPENDS_ON",
                                "from": src,
                                "to": dst,
                                "evidence": service_source_id,
                            }
                        ),
                    },
                    confidence=confidence,
                )
            )

        # DOCUMENTED_IN edge: only when the steering doc has a backing
        # ConfluencePage node AND the model asserts it documents its
        # own service. Confidence isn't self-assessed for this edge, so
        # it defaults to the ExtractedRelationship default.
        if page_source_id is not None and parsed.get("documents_service"):
            relationships.append(
                ExtractedRelationship(
                    source_label=EntityType.SERVICE.value,
                    source_id=service_source_id,
                    target_label=EntityType.CONFLUENCE_PAGE.value,
                    target_id=page_source_id,
                    rel_type=RelationshipType.DOCUMENTED_IN.value,
                    properties={
                        "created_at": "",
                        "source": "llm:steering",
                        "text_hash": compute_text_hash(
                            {
                                "edge": "DOCUMENTED_IN",
                                "service": service_source_id,
                                "page": page_source_id,
                            }
                        ),
                    },
                )
            )

        # Edges only — Service and ConfluencePage nodes are materialized
        # by the deterministic extractors, never by LLM extraction.
        return ExtractionResult(entities=[], relationships=relationships)

    def _build_pr_result(
        self,
        parsed: dict[str, Any],
        known_services: set[str],
    ) -> ExtractionResult:
        """Translate a parsed LLM response into graph writes for a PR.

        PR descriptions only contribute ``DEPENDS_ON`` claims today
        — the PR node, its author, and its MODIFIES edge come from
        deterministic extraction. Service *mentions* without an
        explicit dependency claim aren't actionable in the current
        schema (there's no ``MENTIONS`` edge in V1), so they're
        logged but not materialized.
        """

        services_raw = parsed.get("services_mentioned") or []
        deps_raw = parsed.get("dependencies_claimed") or []
        if not isinstance(services_raw, list):
            services_raw = []
        if not isinstance(deps_raw, list):
            deps_raw = []

        service_hits = _filter_known_services(services_raw, known_services)
        dep_hits = _filter_known_dependencies(deps_raw, known_services)

        if service_hits:
            logger.debug(
                "PR mentions %d known services without explicit deps: %s",
                len(service_hits),
                [name for name, _ in service_hits],
            )

        relationships: list[ExtractedRelationship] = [
            ExtractedRelationship(
                source_label=EntityType.SERVICE.value,
                source_id=f"service:{src}",
                target_label=EntityType.SERVICE.value,
                target_id=f"service:{dst}",
                rel_type=RelationshipType.DEPENDS_ON.value,
                properties={
                    "created_at": "",
                    "dependency_type": "runtime",
                    "source": "llm:pr",
                    "text_hash": compute_text_hash(
                        {"edge": "DEPENDS_ON", "from": src, "to": dst}
                    ),
                },
                confidence=confidence,
            )
            for src, dst, confidence in dep_hits
        ]

        return ExtractionResult(entities=[], relationships=relationships)

    def _build_jira_result(
        self,
        parsed: dict[str, Any],
        ticket_source_id: str,
        ticket_key: str,
        known_services: set[str],
        known_tickets: set[str],
    ) -> ExtractionResult:
        """Translate a parsed LLM response into graph writes for a ticket.

        Mirrors :meth:`_build_confluence_result` /
        :meth:`_build_steering_result`: individual fields are defensively
        typed so malformed arrays collapse to empty lists rather than
        raising (partial extraction beats none). Emits edges only
        (Req 10.5):

        * ``Service DEPENDS_ON Service`` for every claim whose endpoints
          both survive :func:`_filter_known_dependencies` (grounding +
          canonical spelling + self-loop/dupe drop — Req 10.7).
        * ``(Ticket)-[:LINKED_TO]->(Service)`` for every service the
          ticket concerns that survives :func:`_filter_known_services`,
          retained **only** when ``ticket_key`` is a member of
          ``known_tickets`` (Req 10.2) — grounding the edge's ticket
          endpoint.

        Every relationship is tagged ``properties["source"] =
        "llm:jira"`` (provenance, Req 10.4) and carries the propagated
        confidence (Req 10.3).
        """

        deps_raw = parsed.get("dependencies_claimed") or []
        concerns_raw = parsed.get("ticket_concerns") or []
        if not isinstance(deps_raw, list):
            deps_raw = []
        if not isinstance(concerns_raw, list):
            concerns_raw = []

        dep_hits = _filter_known_dependencies(deps_raw, known_services)
        concern_hits = _filter_known_services(concerns_raw, known_services)

        relationships: list[ExtractedRelationship] = []

        # DEPENDS_ON edges claimed by the ticket text.
        for src, dst, confidence in dep_hits:
            relationships.append(
                ExtractedRelationship(
                    source_label=EntityType.SERVICE.value,
                    source_id=f"service:{src}",
                    target_label=EntityType.SERVICE.value,
                    target_id=f"service:{dst}",
                    rel_type=RelationshipType.DEPENDS_ON.value,
                    properties={
                        "created_at": "",
                        "dependency_type": "runtime",
                        "source": "llm:jira",
                        "text_hash": compute_text_hash(
                            {
                                "edge": "DEPENDS_ON",
                                "from": src,
                                "to": dst,
                                "evidence": ticket_source_id,
                            }
                        ),
                    },
                    confidence=confidence,
                )
            )

        # LINKED_TO edges from the Ticket to each concerned Service —
        # retained only when the ticket itself is a known node (Req 10.2).
        if ticket_key in known_tickets:
            for name, confidence in concern_hits:
                relationships.append(
                    ExtractedRelationship(
                        source_label=EntityType.TICKET.value,
                        source_id=ticket_source_id,
                        target_label=EntityType.SERVICE.value,
                        target_id=f"service:{name}",
                        rel_type=RelationshipType.LINKED_TO.value,
                        properties={
                            "created_at": "",
                            "source": "llm:jira",
                            "text_hash": compute_text_hash(
                                {
                                    "edge": "LINKED_TO",
                                    "ticket": ticket_source_id,
                                    "service": name,
                                }
                            ),
                        },
                        confidence=confidence,
                    )
                )

        # Edges only — Service and Ticket nodes are materialized by the
        # deterministic extractors, never by LLM extraction.
        return ExtractionResult(entities=[], relationships=relationships)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_llm_extractor(settings: Settings) -> LLMExtractor:
    """Construct an :class:`LLMExtractor` from application settings.

    Pulls the endpoint, API key, GPT-4o deployment name, and API
    version out of :class:`~src.config.settings.Settings`. Raises
    :class:`ValueError` if any required field is empty — LLM
    extraction cannot proceed without live Azure OpenAI credentials.
    """

    return LLMExtractor(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        deployment_name=settings.azure_openai_deployment_gpt4o,
        api_version=settings.azure_openai_api_version,
    )


# ---------------------------------------------------------------------------
# Silence unused-import warnings from tools that can't see
# conditional usage (e.g. the `ExtractedEntity` re-export for
# downstream callers who import it alongside the extractor).
# ---------------------------------------------------------------------------

_ = ExtractedEntity  # re-export target

__all__ = [
    "LLMExtractionError",
    "LLMExtractor",
    "LLM_MAX_OUTPUT_TOKENS",
    "LLM_REQUEST_TIMEOUT_SECONDS",
    "LLM_TEMPERATURE",
    "get_llm_extractor",
]
