"""Embedding generation for the Engineering Memory Graph.

Thin async wrapper around Azure OpenAI's ``text-embedding-3-large``
deployment that is used to produce the 3072-dimension vectors stored
in the vector store (see :mod:`src.models.vector_store`).

Responsibilities:

* Construct and own the :class:`openai.AsyncAzureOpenAI` client (or
  accept an injected one for testing).
* Offer single- and batch-embedding methods returning
  ``list[float]`` / ``list[list[float]]``.
* Keep inputs under the model's 8192-token limit by truncating with
  :mod:`tiktoken`; fall back to a simple character-based heuristic if
  tiktoken is unavailable or raises.
* Translate all :mod:`openai` errors to a single :class:`EmbeddingError`
  so callers don't need to import the SDK's exception hierarchy.

The design maps to Requirement 2.7 (vector embedding for text-bearing
entities) and the tech stack constraint that V1 uses Azure OpenAI
``text-embedding-3-large``.
"""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Self

import openai
from openai import AsyncAzureOpenAI

from config.settings import Settings
from storage.vector.vector_store import EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Model ID used for tokenizer selection. The Azure *deployment name*
#: may be anything the operator chooses (e.g. ``"embeddings-prod"``),
#: but the underlying model is always ``text-embedding-3-large`` for
#: V1, which uses the ``cl100k_base`` encoding in :mod:`tiktoken`.
_TOKENIZER_MODEL: str = "text-embedding-3-large"

#: Hard upper bound on input tokens imposed by ``text-embedding-3-large``.
#: Anything beyond this is rejected by the API.
MAX_INPUT_TOKENS: int = 8192

#: Default safe budget used by :func:`truncate_to_token_limit`. Slightly
#: below :data:`MAX_INPUT_TOKENS` to leave headroom for any control
#: tokens the tokenizer might account for differently than the service.
DEFAULT_TRUNCATION_TOKENS: int = 8000

#: Approximate character-to-token ratio used when tiktoken is
#: unavailable. 4 chars per token is the commonly cited heuristic for
#: English text with OpenAI BPE tokenizers.
_CHARS_PER_TOKEN_FALLBACK: int = 4


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class EmbeddingError(RuntimeError):
    """Raised when embedding generation fails.

    Wraps both transport-level failures (network errors, timeouts) and
    API-level failures (rate limiting, invalid requests) coming from
    :mod:`openai`. The original exception is available via
    :attr:`__cause__`.
    """


# ---------------------------------------------------------------------------
# Token-aware truncation
# ---------------------------------------------------------------------------


def truncate_to_token_limit(
    text: str,
    max_tokens: int = DEFAULT_TRUNCATION_TOKENS,
) -> str:
    """Return ``text`` shortened to at most ``max_tokens`` tokens.

    The preferred strategy uses :mod:`tiktoken` with the encoding for
    ``text-embedding-3-large`` so the token count matches what the API
    sees. If :mod:`tiktoken` isn't installed or raises during
    encoding/decoding, the function falls back to a character-based
    heuristic (``max_tokens * 4`` characters) and logs a warning.

    ``max_tokens`` must be positive. ``text`` that is already short
    enough is returned unchanged.

    Args:
        text: Input to truncate. May be empty.
        max_tokens: Maximum number of tokens allowed in the result.

    Returns:
        Either the original string (when already within budget) or a
        truncated copy. The return value is always a ``str``.

    Raises:
        ValueError: If ``max_tokens`` is not positive.
    """

    if max_tokens <= 0:
        raise ValueError("max_tokens must be a positive integer")
    if not text:
        return text

    try:
        import tiktoken  # local import to keep startup cost low
    except ImportError:
        return _truncate_by_chars(text, max_tokens)

    try:
        try:
            encoding = tiktoken.encoding_for_model(_TOKENIZER_MODEL)
        except KeyError:
            # Newer/older model names might not be registered yet;
            # cl100k_base is what text-embedding-3-large actually uses.
            encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated = encoding.decode(tokens[:max_tokens])
        logger.warning(
            "Embedding input truncated from %d to %d tokens (max=%d)",
            len(tokens),
            max_tokens,
            max_tokens,
        )
        return truncated
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning(
            "tiktoken truncation failed (%s); falling back to char-based truncation",
            exc,
        )
        return _truncate_by_chars(text, max_tokens)


def _truncate_by_chars(text: str, max_tokens: int) -> str:
    """Character-based fallback when tiktoken isn't usable.

    Uses a rough ``_CHARS_PER_TOKEN_FALLBACK`` chars-per-token ratio.
    Logs a warning when truncation actually happens so callers know
    the fallback path was exercised.
    """

    char_budget = max_tokens * _CHARS_PER_TOKEN_FALLBACK
    if len(text) <= char_budget:
        return text
    logger.warning(
        "Embedding input truncated by char-heuristic from %d to %d chars "
        "(max_tokens=%d, ratio=%d)",
        len(text),
        char_budget,
        max_tokens,
        _CHARS_PER_TOKEN_FALLBACK,
    )
    return text[:char_budget]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class EmbeddingService:
    """Async client for Azure OpenAI embedding generation.

    The service is designed to be long-lived: create one per process,
    reuse it across requests, and :meth:`close` it on shutdown. It can
    also be used as an async context manager::

        async with EmbeddingService(...) as svc:
            vec = await svc.generate_embedding("hello")

    When an :class:`openai.AsyncAzureOpenAI` is injected via ``client``
    the service will not close it on :meth:`close` — the caller
    retains ownership. This matches :mod:`src.models.vector_store`'s
    pattern for injected HTTP clients.
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
            raise ValueError("EmbeddingService requires a non-empty endpoint")
        if not api_key:
            raise ValueError("EmbeddingService requires a non-empty api_key")
        if not deployment_name:
            raise ValueError("EmbeddingService requires a non-empty deployment_name")
        if not api_version:
            raise ValueError("EmbeddingService requires a non-empty api_version")

        self._endpoint = endpoint
        self._deployment_name = deployment_name
        self._api_version = api_version
        # Track ownership so injected clients aren't closed out from
        # under the caller.
        self._owns_client = client is None
        if client is None:
            # Use a custom httpx client with SSL verification disabled
            # to handle corporate proxies with self-signed certificates.
            import httpx as _httpx
            custom_http_client = _httpx.AsyncClient(verify=False)
            self._client: AsyncAzureOpenAI = AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
                http_client=custom_http_client,
            )
        else:
            self._client = client

    # -- public API ------------------------------------------------------

    async def generate_embedding(self, text: str) -> list[float]:
        """Return the embedding vector for ``text``.

        The input is truncated to :data:`DEFAULT_TRUNCATION_TOKENS`
        before the API call to avoid server-side rejection of
        over-long inputs. The returned vector is always exactly
        :data:`EMBEDDING_DIMENSION` floats long; a mismatch raises
        :class:`EmbeddingError`.
        """

        vectors = await self.generate_embeddings([text])
        return vectors[0]

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding per entry in ``texts``.

        Inputs are truncated individually. An empty ``texts`` list
        short-circuits to an empty result (no API call made). Order is
        preserved: ``result[i]`` corresponds to ``texts[i]``.
        """

        if not texts:
            return []

        prepared = [truncate_to_token_limit(t) for t in texts]
        try:
            response = await self._client.embeddings.create(
                model=self._deployment_name,
                input=prepared,
            )
        except openai.RateLimitError as exc:
            # Caller decides whether/when to retry; we just surface the
            # failure with context.
            logger.warning("Azure OpenAI rate limit hit during embedding: %s", exc)
            raise EmbeddingError("Azure OpenAI rate limit exceeded") from exc
        except openai.APIError as exc:
            logger.error("Azure OpenAI API error during embedding: %s", exc)
            raise EmbeddingError(f"Azure OpenAI API error: {exc}") from exc
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Unexpected error during embedding: %s", exc)
            raise EmbeddingError(f"Unexpected embedding failure: {exc}") from exc

        vectors: list[list[float]] = []
        for item in response.data:
            vec = list(item.embedding)
            if len(vec) != EMBEDDING_DIMENSION:
                raise EmbeddingError(
                    f"Embedding dimension mismatch: expected "
                    f"{EMBEDDING_DIMENSION}, got {len(vec)}"
                )
            vectors.append(vec)

        if len(vectors) != len(texts):
            raise EmbeddingError(
                f"Embedding count mismatch: expected {len(texts)}, got "
                f"{len(vectors)}"
            )
        return vectors

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


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_embedding_service(settings: Settings) -> EmbeddingService:
    """Construct an :class:`EmbeddingService` from application settings.

    Pulls the endpoint, API key, embedding deployment name, and API
    version out of :class:`~src.config.settings.Settings`. Raises
    :class:`ValueError` if any of those required fields are empty —
    embedding generation cannot proceed without live Azure OpenAI
    credentials.
    """

    return EmbeddingService(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        deployment_name=settings.azure_openai_deployment_embedding,
        api_version=settings.azure_openai_api_version,
    )


__all__ = [
    "DEFAULT_TRUNCATION_TOKENS",
    "EmbeddingError",
    "EmbeddingService",
    "MAX_INPUT_TOKENS",
    "get_embedding_service",
    "truncate_to_token_limit",
]
