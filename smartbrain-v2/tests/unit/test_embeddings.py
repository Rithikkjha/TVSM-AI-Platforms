"""Unit tests for :mod:`src.extraction.embeddings`.

These tests exercise the :class:`EmbeddingService` contract without
calling the real Azure OpenAI service. The strategy mirrors
``tests/unit/test_vector_store.py``: inject a mock client for
``openai.AsyncAzureOpenAI`` so we can assert on the requests the
service makes and control the responses it sees.

Coverage:

* :func:`truncate_to_token_limit` — tiktoken path, character-based
  fallback, edge cases (empty input, non-positive budget).
* :class:`EmbeddingService` — constructor validation, single/batch
  embedding, context manager, error translation, dimension checks.
* :func:`get_embedding_service` — factory wires settings correctly.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import openai
import pytest
from config.settings import Settings
from processing.embeddings.service import (
    DEFAULT_TRUNCATION_TOKENS,
    EmbeddingError,
    EmbeddingService,
    get_embedding_service,
    truncate_to_token_limit,
)
from storage.vector.vector_store import EMBEDDING_DIMENSION

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_vector(fill: float = 0.0) -> list[float]:
    """Return a 3072-long vector for use in fake API responses."""

    return [fill] * EMBEDDING_DIMENSION


def _make_response(*vectors: list[float]) -> MagicMock:
    """Build a shape-compatible stand-in for ``CreateEmbeddingResponse``.

    The service only reads ``response.data[i].embedding``, so we mimic
    exactly that structure.
    """

    response = MagicMock(name="CreateEmbeddingResponse")
    response.data = [MagicMock(embedding=list(v)) for v in vectors]
    return response


def _make_service(
    *,
    deployment_name: str = "text-embedding-3-large",
) -> tuple[EmbeddingService, MagicMock]:
    """Build a service with an ``AsyncAzureOpenAI`` mock attached."""

    client = MagicMock(name="AsyncAzureOpenAI")
    client.embeddings = MagicMock()
    client.embeddings.create = AsyncMock()
    client.close = AsyncMock()

    service = EmbeddingService(
        endpoint="https://openai.example.net",
        api_key="k",
        deployment_name=deployment_name,
        api_version="2024-06-01",
        client=client,
    )
    return service, client


# ---------------------------------------------------------------------------
# truncate_to_token_limit
# ---------------------------------------------------------------------------


class TestTruncateToTokenLimit:
    def test_returns_short_text_unchanged(self) -> None:
        text = "hello world"
        assert truncate_to_token_limit(text, max_tokens=100) == text

    def test_empty_string_is_returned_as_is(self) -> None:
        assert truncate_to_token_limit("", max_tokens=100) == ""

    def test_rejects_non_positive_budget(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            truncate_to_token_limit("abc", max_tokens=0)
        with pytest.raises(ValueError, match="positive"):
            truncate_to_token_limit("abc", max_tokens=-5)

    def test_truncates_long_input_to_token_budget(self) -> None:
        """Using tiktoken, re-encoding the output yields ≤ budget tokens."""

        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")
        # 1000 tokens' worth of distinct, non-whitespace tokens.
        long_text = " ".join(f"word{i}" for i in range(1000))
        original_token_count = len(encoding.encode(long_text))
        assert original_token_count > 50  # sanity: truncation will trigger

        truncated = truncate_to_token_limit(long_text, max_tokens=50)

        assert truncated != long_text
        assert len(truncated) < len(long_text)
        assert len(encoding.encode(truncated)) <= 50

    def test_char_fallback_when_tiktoken_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If importing :mod:`tiktoken` fails, fall back to char slicing."""

        import builtins

        original_import = builtins.__import__

        def fake_import(
            name: str,
            globals: Any = None,
            locals: Any = None,
            fromlist: Any = (),
            level: int = 0,
        ) -> Any:
            if name == "tiktoken":
                raise ImportError("tiktoken unavailable for test")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        text = "a" * 10_000
        out = truncate_to_token_limit(text, max_tokens=100)
        # 100 tokens * 4 chars/token heuristic
        assert out == "a" * 400


# ---------------------------------------------------------------------------
# EmbeddingService constructor
# ---------------------------------------------------------------------------


class TestEmbeddingServiceConstructor:
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
            EmbeddingService(**kwargs)


# ---------------------------------------------------------------------------
# EmbeddingService.generate_embedding / generate_embeddings
# ---------------------------------------------------------------------------


class TestGenerateEmbedding:
    @pytest.mark.asyncio
    async def test_single_returns_vector_of_correct_length(self) -> None:
        service, client = _make_service()
        client.embeddings.create.return_value = _make_response(_make_vector(0.1))

        vec = await service.generate_embedding("hello")

        assert len(vec) == EMBEDDING_DIMENSION
        assert vec[0] == pytest.approx(0.1)
        # The deployment name is used as the ``model`` arg.
        _args, kwargs = client.embeddings.create.call_args
        assert kwargs["model"] == "text-embedding-3-large"
        assert kwargs["input"] == ["hello"]

    @pytest.mark.asyncio
    async def test_batch_returns_one_vector_per_input(self) -> None:
        service, client = _make_service()
        client.embeddings.create.return_value = _make_response(
            _make_vector(0.1),
            _make_vector(0.2),
            _make_vector(0.3),
        )

        vectors = await service.generate_embeddings(["a", "b", "c"])

        assert len(vectors) == 3
        assert all(len(v) == EMBEDDING_DIMENSION for v in vectors)
        assert vectors[0][0] == pytest.approx(0.1)
        assert vectors[1][0] == pytest.approx(0.2)
        assert vectors[2][0] == pytest.approx(0.3)
        _args, kwargs = client.embeddings.create.call_args
        assert kwargs["input"] == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_batch_empty_is_noop(self) -> None:
        service, client = _make_service()
        result = await service.generate_embeddings([])
        assert result == []
        client.embeddings.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_long_input_is_truncated_before_api_call(self) -> None:
        """Inputs over the token budget are shortened before dispatch."""

        service, client = _make_service()
        client.embeddings.create.return_value = _make_response(_make_vector())
        long_text = "token " * 20_000  # far more than 8k tokens

        await service.generate_embedding(long_text)

        _args, kwargs = client.embeddings.create.call_args
        sent = kwargs["input"][0]
        assert len(sent) < len(long_text)

        # And the truncated input is well under the model's hard limit.
        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")
        assert len(encoding.encode(sent)) <= DEFAULT_TRUNCATION_TOKENS

    @pytest.mark.asyncio
    async def test_rate_limit_raised_as_embedding_error(self) -> None:
        service, client = _make_service()
        # RateLimitError requires (message, response, body); we build a
        # minimal stub that passes the constructor.
        response = MagicMock()
        response.request = MagicMock()
        client.embeddings.create.side_effect = openai.RateLimitError(
            message="429 Too Many Requests",
            response=response,
            body=None,
        )

        with pytest.raises(EmbeddingError, match="rate limit"):
            await service.generate_embedding("x")

    @pytest.mark.asyncio
    async def test_api_error_raised_as_embedding_error(self) -> None:
        service, client = _make_service()
        request = MagicMock()
        client.embeddings.create.side_effect = openai.APIError(
            message="upstream failure",
            request=request,
            body=None,
        )

        with pytest.raises(EmbeddingError, match="Azure OpenAI API error"):
            await service.generate_embedding("x")

    @pytest.mark.asyncio
    async def test_dimension_mismatch_raises_embedding_error(self) -> None:
        service, client = _make_service()
        # Return a vector with the wrong length; the service must
        # reject it rather than silently propagate bad data.
        client.embeddings.create.return_value = _make_response([0.1, 0.2, 0.3])

        with pytest.raises(EmbeddingError, match="dimension mismatch"):
            await service.generate_embedding("x")


# ---------------------------------------------------------------------------
# Context manager / close semantics
# ---------------------------------------------------------------------------


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_close_does_not_close_injected_client(self) -> None:
        """Injected clients remain owned by the caller."""

        service, client = _make_service()
        await service.close()
        client.close.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_async_context_manager_calls_close(self) -> None:
        service, client = _make_service()
        client.embeddings.create.return_value = _make_response(_make_vector())

        async with service as svc:
            await svc.generate_embedding("hi")

        # Injected client, so close is still a no-op (ownership stays
        # with the caller) — but the CM path shouldn't raise.
        client.close.assert_not_awaited()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestGetEmbeddingService:
    def test_constructs_service_from_settings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The factory wires each settings field onto the service."""

        captured: dict[str, Any] = {}

        def fake_init(
            self: EmbeddingService,
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

        monkeypatch.setattr(EmbeddingService, "__init__", fake_init)

        settings = Settings(
            azure_openai_endpoint="https://openai.example.net",
            azure_openai_key="secret-key",
            azure_openai_deployment_embedding="emb-deploy",
            azure_openai_api_version="2024-06-01",
        )
        svc = get_embedding_service(settings)

        assert isinstance(svc, EmbeddingService)
        assert captured == {
            "endpoint": "https://openai.example.net",
            "api_key": "secret-key",
            "deployment_name": "emb-deploy",
            "api_version": "2024-06-01",
        }
