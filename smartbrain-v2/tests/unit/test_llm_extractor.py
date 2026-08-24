"""Unit tests for :mod:`src.extraction.llm_extractor`.

These tests exercise the :class:`LLMExtractor` contract without
calling a real Azure OpenAI endpoint. The strategy mirrors
``tests/unit/test_embeddings.py``: inject a mock
``openai.AsyncAzureOpenAI`` so we can assert on the outgoing
request shape and control the fake response body.

Coverage:

* Constructor validation (empty required fields).
* Confluence extraction — valid JSON response produces the expected
  ``DOCUMENTED_IN`` and ``DEPENDS_ON`` edges.
* Hallucination guard — services / dependencies referencing names
  outside ``known_services`` are filtered out.
* Graceful degradation on invalid JSON (empty result, error logged).
* Transport failures — timeouts, rate limiting, and generic API
  errors surface as :class:`LLMExtractionError`.
* PR extraction — only claimed dependencies become edges; plain
  service mentions do not.
* Empty content short-circuits to an empty result without calling
  the API.
* Context manager / ownership semantics.
* :func:`get_llm_extractor` wires settings correctly.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import openai
import pytest
from config.settings import Settings
from processing.extraction.deterministic import ExtractionResult
from processing.extraction.llm_extractor import (
    LLMExtractionError,
    LLMExtractor,
    get_llm_extractor,
)
from storage.graph.schema import EntityType, RelationshipType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_completion(
    content: str,
    *,
    prompt_tokens: int = 120,
    completion_tokens: int = 40,
    total_tokens: int = 160,
) -> MagicMock:
    """Build a minimal stand-in for ``ChatCompletion``.

    The extractor only reads ``response.choices[0].message.content``
    and ``response.usage.*``, so we mimic exactly that shape.
    """

    response = MagicMock(name="ChatCompletion")
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response.choices = [choice]
    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = total_tokens
    response.usage = usage
    return response


def _make_extractor(
    *,
    deployment_name: str = "gpt-4o",
) -> tuple[LLMExtractor, MagicMock]:
    """Build an extractor with an ``AsyncAzureOpenAI`` mock attached."""

    client = MagicMock(name="AsyncAzureOpenAI")
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock()
    client.close = AsyncMock()

    extractor = LLMExtractor(
        endpoint="https://openai.example.net",
        api_key="k",
        deployment_name=deployment_name,
        api_version="2024-06-01",
        client=client,
    )
    return extractor, client


def _json_body(payload: dict[str, Any]) -> str:
    return json.dumps(payload)


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


class TestLLMExtractorConstructor:
    @pytest.mark.parametrize(
        "field",
        ["endpoint", "api_key", "deployment_name", "api_version"],
    )
    def test_rejects_empty_required_args(self, field: str) -> None:
        kwargs: dict[str, Any] = {
            "endpoint": "https://x",
            "api_key": "k",
            "deployment_name": "d",
            "api_version": "2024-06-01",
            "client": MagicMock(),
        }
        kwargs[field] = ""
        with pytest.raises(ValueError, match=field):
            LLMExtractor(**kwargs)


# ---------------------------------------------------------------------------
# Confluence extraction
# ---------------------------------------------------------------------------


class TestExtractFromConfluencePage:
    @pytest.mark.asyncio
    async def test_documented_in_edges_created_for_known_services(self) -> None:
        extractor, client = _make_extractor()
        body = _json_body(
            {
                "services_mentioned": [
                    {"name": "payments-service", "confidence": "high"},
                    {"name": "auth-service", "confidence": "medium"},
                ],
                "dependencies_claimed": [],
            }
        )
        client.chat.completions.create.return_value = _make_completion(body)

        result = await extractor.extract_from_confluence_page(
            page_source_id="confluence:page:42",
            page_title="Payments Architecture",
            page_content="payments-service talks to auth-service.",
            known_services=["payments-service", "auth-service", "other-service"],
        )

        assert isinstance(result, ExtractionResult)
        # LLM only contributes edges; Service + ConfluencePage nodes
        # are already produced by deterministic extractors.
        assert result.entities == []
        # One DOCUMENTED_IN edge per mentioned known service.
        documented = [
            r for r in result.relationships
            if r.rel_type == RelationshipType.DOCUMENTED_IN.value
        ]
        assert len(documented) == 2

        by_source = {r.source_id: r for r in documented}
        assert by_source["service:payments-service"].target_id == "confluence:page:42"
        assert by_source["service:payments-service"].source_label == EntityType.SERVICE.value
        assert (
            by_source["service:payments-service"].target_label
            == EntityType.CONFLUENCE_PAGE.value
        )
        assert by_source["service:payments-service"].confidence == "high"
        assert by_source["service:auth-service"].confidence == "medium"

    @pytest.mark.asyncio
    async def test_unknown_services_filtered_out(self) -> None:
        extractor, client = _make_extractor()
        body = _json_body(
            {
                "services_mentioned": [
                    {"name": "payments-service", "confidence": "high"},
                    {"name": "imaginary-service", "confidence": "high"},
                ],
                "dependencies_claimed": [],
            }
        )
        client.chat.completions.create.return_value = _make_completion(body)

        result = await extractor.extract_from_confluence_page(
            page_source_id="confluence:page:42",
            page_title="Doc",
            page_content="content with two service names",
            known_services=["payments-service"],
        )

        # Only the known service produces an edge; the hallucinated
        # one is dropped entirely.
        sources = {r.source_id for r in result.relationships}
        assert sources == {"service:payments-service"}

    @pytest.mark.asyncio
    async def test_depends_on_edge_when_both_endpoints_known(self) -> None:
        extractor, client = _make_extractor()
        body = _json_body(
            {
                "services_mentioned": [],
                "dependencies_claimed": [
                    {
                        "from": "payments-service",
                        "to": "auth-service",
                        "confidence": "high",
                    }
                ],
            }
        )
        client.chat.completions.create.return_value = _make_completion(body)

        result = await extractor.extract_from_confluence_page(
            page_source_id="confluence:page:1",
            page_title="t",
            page_content="payments-service depends on auth-service",
            known_services=["payments-service", "auth-service"],
        )

        depends = [
            r for r in result.relationships
            if r.rel_type == RelationshipType.DEPENDS_ON.value
        ]
        assert len(depends) == 1
        edge = depends[0]
        assert edge.source_id == "service:payments-service"
        assert edge.target_id == "service:auth-service"
        assert edge.source_label == EntityType.SERVICE.value
        assert edge.target_label == EntityType.SERVICE.value
        assert edge.confidence == "high"

    @pytest.mark.asyncio
    async def test_depends_on_filtered_when_endpoint_unknown(self) -> None:
        extractor, client = _make_extractor()
        body = _json_body(
            {
                "services_mentioned": [],
                "dependencies_claimed": [
                    {
                        "from": "payments-service",
                        "to": "mystery-service",
                        "confidence": "medium",
                    },
                    {
                        "from": "ghost-service",
                        "to": "auth-service",
                        "confidence": "medium",
                    },
                ],
            }
        )
        client.chat.completions.create.return_value = _make_completion(body)

        result = await extractor.extract_from_confluence_page(
            page_source_id="confluence:page:1",
            page_title="t",
            page_content="some body",
            known_services=["payments-service", "auth-service"],
        )

        # Neither endpoint pair is fully covered by known_services,
        # so no DEPENDS_ON edges are emitted.
        assert not any(
            r.rel_type == RelationshipType.DEPENDS_ON.value for r in result.relationships
        )

    @pytest.mark.asyncio
    async def test_invalid_json_returns_empty_result_and_logs(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        extractor, client = _make_extractor()
        client.chat.completions.create.return_value = _make_completion(
            "this is not json{"
        )

        with caplog.at_level(logging.ERROR, logger="src.extraction.llm_extractor"):
            result = await extractor.extract_from_confluence_page(
                page_source_id="confluence:page:1",
                page_title="t",
                page_content="body",
                known_services=["payments-service"],
            )

        assert result.entities == []
        assert result.relationships == []
        assert any("invalid JSON" in rec.getMessage() for rec in caplog.records)

    @pytest.mark.asyncio
    async def test_empty_content_short_circuits_without_api_call(self) -> None:
        extractor, client = _make_extractor()

        result = await extractor.extract_from_confluence_page(
            page_source_id="confluence:page:1",
            page_title="t",
            page_content="   ",
            known_services=["payments-service"],
        )

        assert result == ExtractionResult()
        client.chat.completions.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_missing_page_source_id_raises(self) -> None:
        extractor, _client = _make_extractor()
        with pytest.raises(ValueError, match="page_source_id"):
            await extractor.extract_from_confluence_page(
                page_source_id="",
                page_title="t",
                page_content="body",
                known_services=["payments-service"],
            )

    @pytest.mark.asyncio
    async def test_uses_json_mode_zero_temperature_and_max_tokens(self) -> None:
        extractor, client = _make_extractor()
        body = _json_body({"services_mentioned": [], "dependencies_claimed": []})
        client.chat.completions.create.return_value = _make_completion(body)

        await extractor.extract_from_confluence_page(
            page_source_id="confluence:page:1",
            page_title="t",
            page_content="body",
            known_services=["payments-service"],
        )

        _args, kwargs = client.chat.completions.create.call_args
        assert kwargs["model"] == "gpt-4o"
        assert kwargs["response_format"] == {"type": "json_object"}
        assert kwargs["temperature"] == 0.0
        assert kwargs["max_tokens"] == 2000
        messages = kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_case_insensitive_service_matching_uses_canonical_spelling(
        self,
    ) -> None:
        """The model may echo prose capitalization; we normalize back."""

        extractor, client = _make_extractor()
        body = _json_body(
            {
                "services_mentioned": [
                    {"name": "Payments-Service", "confidence": "high"},
                ],
                "dependencies_claimed": [],
            }
        )
        client.chat.completions.create.return_value = _make_completion(body)

        result = await extractor.extract_from_confluence_page(
            page_source_id="confluence:page:1",
            page_title="t",
            page_content="body",
            known_services=["payments-service"],
        )

        sources = [r.source_id for r in result.relationships]
        # Canonical spelling (lowercase) from known_services wins.
        assert sources == ["service:payments-service"]

    @pytest.mark.asyncio
    async def test_self_loop_dependencies_are_dropped(self) -> None:
        extractor, client = _make_extractor()
        body = _json_body(
            {
                "services_mentioned": [],
                "dependencies_claimed": [
                    {
                        "from": "payments-service",
                        "to": "payments-service",
                        "confidence": "high",
                    }
                ],
            }
        )
        client.chat.completions.create.return_value = _make_completion(body)

        result = await extractor.extract_from_confluence_page(
            page_source_id="confluence:page:1",
            page_title="t",
            page_content="body",
            known_services=["payments-service"],
        )

        assert not any(
            r.rel_type == RelationshipType.DEPENDS_ON.value for r in result.relationships
        )

    @pytest.mark.asyncio
    async def test_logs_token_usage(self, caplog: pytest.LogCaptureFixture) -> None:
        extractor, client = _make_extractor()
        body = _json_body({"services_mentioned": [], "dependencies_claimed": []})
        client.chat.completions.create.return_value = _make_completion(
            body, prompt_tokens=321, completion_tokens=17, total_tokens=338
        )

        with caplog.at_level(logging.INFO, logger="src.extraction.llm_extractor"):
            await extractor.extract_from_confluence_page(
                page_source_id="confluence:page:1",
                page_title="t",
                page_content="body",
                known_services=["payments-service"],
            )

        assert any("321" in rec.getMessage() for rec in caplog.records)


# ---------------------------------------------------------------------------
# PR description extraction
# ---------------------------------------------------------------------------


class TestExtractFromPRDescription:
    @pytest.mark.asyncio
    async def test_depends_on_edges_from_pr_body(self) -> None:
        extractor, client = _make_extractor()
        body = _json_body(
            {
                "services_mentioned": [
                    {"name": "payments-service", "confidence": "high"},
                ],
                "dependencies_claimed": [
                    {
                        "from": "payments-service",
                        "to": "auth-service",
                        "confidence": "medium",
                    }
                ],
            }
        )
        client.chat.completions.create.return_value = _make_completion(body)

        result = await extractor.extract_from_pr_description(
            pr_source_id="github:pr:payments-service/42",
            pr_title="Wire up auth",
            pr_body="This wires payments-service up to auth-service",
            repo_source_id="github:repo:123",
            known_services=["payments-service", "auth-service"],
        )

        # PR extraction only emits DEPENDS_ON; plain mentions don't
        # become edges (there's no MENTIONS type in V1).
        assert all(
            r.rel_type == RelationshipType.DEPENDS_ON.value for r in result.relationships
        )
        assert len(result.relationships) == 1
        edge = result.relationships[0]
        assert edge.source_id == "service:payments-service"
        assert edge.target_id == "service:auth-service"
        assert edge.confidence == "medium"

    @pytest.mark.asyncio
    async def test_unknown_services_in_pr_are_filtered(self) -> None:
        extractor, client = _make_extractor()
        body = _json_body(
            {
                "services_mentioned": [],
                "dependencies_claimed": [
                    {
                        "from": "payments-service",
                        "to": "nonexistent",
                        "confidence": "high",
                    }
                ],
            }
        )
        client.chat.completions.create.return_value = _make_completion(body)

        result = await extractor.extract_from_pr_description(
            pr_source_id="github:pr:payments-service/42",
            pr_title="t",
            pr_body="body",
            repo_source_id="github:repo:123",
            known_services=["payments-service"],
        )

        assert result.relationships == []

    @pytest.mark.asyncio
    async def test_empty_body_short_circuits(self) -> None:
        extractor, client = _make_extractor()

        result = await extractor.extract_from_pr_description(
            pr_source_id="github:pr:payments-service/42",
            pr_title="t",
            pr_body="",
            repo_source_id="github:repo:123",
            known_services=["payments-service"],
        )

        assert result == ExtractionResult()
        client.chat.completions.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_missing_pr_source_id_raises(self) -> None:
        extractor, _client = _make_extractor()
        with pytest.raises(ValueError, match="pr_source_id"):
            await extractor.extract_from_pr_description(
                pr_source_id="",
                pr_title="t",
                pr_body="body",
                repo_source_id="github:repo:123",
                known_services=["payments-service"],
            )

    @pytest.mark.asyncio
    async def test_missing_repo_source_id_raises(self) -> None:
        extractor, _client = _make_extractor()
        with pytest.raises(ValueError, match="repo_source_id"):
            await extractor.extract_from_pr_description(
                pr_source_id="github:pr:x/1",
                pr_title="t",
                pr_body="body",
                repo_source_id="",
                known_services=["payments-service"],
            )


# ---------------------------------------------------------------------------
# Transport / API error handling
# ---------------------------------------------------------------------------


class TestAPIErrorHandling:
    @pytest.mark.asyncio
    async def test_api_error_raised_as_llm_extraction_error(self) -> None:
        extractor, client = _make_extractor()
        request = MagicMock()
        client.chat.completions.create.side_effect = openai.APIError(
            message="upstream failure",
            request=request,
            body=None,
        )

        with pytest.raises(LLMExtractionError, match="Azure OpenAI API error"):
            await extractor.extract_from_confluence_page(
                page_source_id="confluence:page:1",
                page_title="t",
                page_content="body",
                known_services=["payments-service"],
            )

    @pytest.mark.asyncio
    async def test_rate_limit_raised_as_llm_extraction_error(self) -> None:
        extractor, client = _make_extractor()
        response = MagicMock()
        response.request = MagicMock()
        client.chat.completions.create.side_effect = openai.RateLimitError(
            message="429 Too Many Requests",
            response=response,
            body=None,
        )

        with pytest.raises(LLMExtractionError, match="rate limit"):
            await extractor.extract_from_confluence_page(
                page_source_id="confluence:page:1",
                page_title="t",
                page_content="body",
                known_services=["payments-service"],
            )

    @pytest.mark.asyncio
    async def test_timeout_raised_as_llm_extraction_error(self) -> None:
        extractor, client = _make_extractor()
        request = MagicMock()
        client.chat.completions.create.side_effect = openai.APITimeoutError(
            request=request,
        )

        with pytest.raises(LLMExtractionError, match="timed out"):
            await extractor.extract_from_confluence_page(
                page_source_id="confluence:page:1",
                page_title="t",
                page_content="body",
                known_services=["payments-service"],
            )


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_close_does_not_close_injected_client(self) -> None:
        extractor, client = _make_extractor()
        await extractor.close()
        client.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        extractor, client = _make_extractor()
        body = _json_body({"services_mentioned": [], "dependencies_claimed": []})
        client.chat.completions.create.return_value = _make_completion(body)

        async with extractor as ext:
            await ext.extract_from_confluence_page(
                page_source_id="confluence:page:1",
                page_title="t",
                page_content="body",
                known_services=["payments-service"],
            )

        client.close.assert_not_awaited()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestGetLLMExtractor:
    def test_constructs_extractor_from_settings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The factory wires each settings field onto the extractor."""

        captured: dict[str, Any] = {}

        def fake_init(
            self: LLMExtractor,
            endpoint: str,
            api_key: str,
            deployment_name: str,
            api_version: str,
            *,
            client: Any = None,
        ) -> None:
            captured["endpoint"] = endpoint
            captured["api_key"] = api_key
            captured["deployment_name"] = deployment_name
            captured["api_version"] = api_version
            # Avoid building the real AsyncAzureOpenAI client in tests.
            self._endpoint = endpoint
            self._deployment_name = deployment_name
            self._api_version = api_version
            self._owns_client = False
            self._client = MagicMock()

        monkeypatch.setattr(LLMExtractor, "__init__", fake_init)

        settings = Settings(
            azure_openai_endpoint="https://openai.example.net",
            azure_openai_key="secret-key",
            azure_openai_deployment_gpt4o="gpt4o-deploy",
            azure_openai_api_version="2024-06-01",
        )
        ext = get_llm_extractor(settings)

        assert isinstance(ext, LLMExtractor)
        assert captured == {
            "endpoint": "https://openai.example.net",
            "api_key": "secret-key",
            "deployment_name": "gpt4o-deploy",
            "api_version": "2024-06-01",
        }
