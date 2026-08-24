"""Cross-encoder re-ranking of hybrid-retrieval candidates.

The :class:`HybridRetriever` returns a broad top-30 set fused via RRF; those
candidates are ranked by *fusion* score, which is a proxy for relevance rather
than a direct measurement of it. A **cross-encoder** re-ranker (design.md §5)
refines that set: it jointly encodes each ``(query, chunk.display_text)`` pair
and emits a single relevance logit, which is far more accurate than the
bi-encoder cosine that produced the dense leg. Because a cross-encoder is too
expensive to run over the whole corpus, it is applied only to the retrieved
top-30, then narrowed to the top-5 sent to the LLM (the classic
retrieve-then-rerank pattern).

This module provides:

* :class:`Reranker` — the async protocol every re-ranker satisfies.
* :class:`CrossEncoderReranker` — the default local implementation backed by
  ``sentence_transformers.CrossEncoder`` (default model
  ``cross-encoder/ms-marco-MiniLM-L-6-v2``). The blocking model call is run in
  a thread executor under a timeout (``settings.rerank_timeout_ms``).
* :class:`HostedRerankAdapter` — an optional adapter that routes re-ranking to
  a hosted rerank API (e.g. Cohere Rerank) behind the same protocol.

Graceful degradation is the central contract (Req 4.4): the ``sentence
-transformers`` dependency is optional and imported lazily/guarded, and *any*
failure mode — the package missing, a model load error, a scoring exception,
or a timeout — resolves to returning ``candidates[:top_k]`` **unchanged**
(preserving the upstream hybrid RRF order) and logging the failure once. The
re-ranker never raises to the caller.

Determinism (Property 7): given candidates with assigned scores, the re-ranker
returns exactly the ``min(top_k, n)`` highest-scoring candidates ordered by
descending model score, with ``chunk_id`` ascending as a deterministic
tiebreak, and never returns a candidate absent from the input.

Requirements: 4.1, 4.2, 4.3, 4.4. Design §5.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Protocol, runtime_checkable

from config.settings import Settings, get_settings
from retrieval.search.hybrid_retriever import ScoredChunk

__all__ = ["Reranker", "CrossEncoderReranker", "HostedRerankAdapter"]

logger = logging.getLogger(__name__)

#: Default number of candidates to keep after re-ranking (Req 4.2).
DEFAULT_TOP_K: int = 5


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class Reranker(Protocol):
    """Re-score and narrow a candidate set for a single query.

    Implementations MUST be non-raising: on any internal failure they fall
    back to the input order and return ``candidates[:top_k]`` (Req 4.4).
    """

    async def rerank(
        self,
        query: str,
        candidates: list[ScoredChunk],
        top_k: int = DEFAULT_TOP_K,
    ) -> list[ScoredChunk]:
        """Return the ``min(top_k, len(candidates))`` most relevant candidates."""
        ...


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fallback(candidates: list[ScoredChunk], top_k: int) -> list[ScoredChunk]:
    """Return the upstream top-``top_k`` unchanged (hybrid RRF order preserved).

    ``top_k`` is clamped to non-negative so a nonsensical ``top_k`` can never
    raise; slicing then naturally yields ``min(top_k, n)`` items.
    """

    return candidates[: max(top_k, 0)]


def _select_top_k(
    candidates: list[ScoredChunk],
    scores: list[float],
    top_k: int,
) -> list[ScoredChunk]:
    """Order ``candidates`` by descending ``scores`` and keep the top ``top_k``.

    Ties on score are broken deterministically by ``chunk_id`` ascending so the
    result is stable across runs and backends (Property 7). The returned
    objects are exactly the input objects (with their fused ``score`` field
    left intact) — no candidate outside the input can appear.
    """

    order = sorted(
        range(len(candidates)),
        key=lambda i: (-scores[i], candidates[i].chunk_id),
    )
    return [candidates[i] for i in order[: max(top_k, 0)]]


# ---------------------------------------------------------------------------
# Local cross-encoder
# ---------------------------------------------------------------------------


class CrossEncoderReranker:
    """Local ``sentence-transformers`` cross-encoder re-ranker.

    The model (default ``cross-encoder/ms-marco-MiniLM-L-6-v2``, from
    ``settings.rerank_model``) is loaded lazily on first use: constructing the
    re-ranker is cheap and never imports ``sentence_transformers``, so a
    deployment without the optional ``rerank`` extra installed can still import
    this module and construct the object. The blocking ``predict`` call is
    offloaded to a thread and bounded by ``settings.rerank_timeout_ms``.

    Any failure — missing dependency, model load error, scoring exception, or
    timeout — is caught, logged once, and resolved by returning the upstream
    ``candidates[:top_k]`` unchanged (Req 4.4). The re-ranker never raises.

    Args:
        settings: Optional settings override. Defaults to :func:`get_settings`.
        model_name: Optional explicit model name overriding
            ``settings.rerank_model``.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        model_name: str | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._model_name = model_name or self._settings.rerank_model
        self._timeout_s = max(self._settings.rerank_timeout_ms, 0) / 1000.0
        # Loaded lazily; sentinel `False` means "not yet attempted", `None`
        # means "load attempted and failed" so we don't retry-spam the log.
        self._model: object | None | bool = False
        self._load_failed = False
        self._logged_failure = False

    # -- model loading --------------------------------------------------

    def _ensure_model(self) -> object | None:
        """Return the loaded CrossEncoder, or ``None`` if unavailable.

        Guards the optional import so a missing ``sentence-transformers`` never
        breaks module import or construction — only the first scoring attempt
        discovers the dependency is absent and trips the fallback.
        """

        if self._model is not False:
            # Either a loaded model (object) or a prior failure (None).
            return self._model if self._model is not None else None
        if self._load_failed:
            return None

        try:
            # Lazy, guarded import: absence must degrade to fallback, not crash.
            from sentence_transformers import CrossEncoder
        except ImportError as exc:  # pragma: no cover - depends on env
            self._load_failed = True
            self._model = None
            self._log_once(
                "sentence-transformers not installed (%s); re-ranking disabled, "
                "falling back to hybrid order. Install the 'rerank' extra to enable.",
                exc,
            )
            return None

        try:
            model = CrossEncoder(self._model_name)
        except Exception as exc:  # noqa: BLE001 - any load error must fall back
            self._load_failed = True
            self._model = None
            self._log_once(
                "Failed to load cross-encoder model %r (%s); falling back to "
                "hybrid order.",
                self._model_name,
                exc,
            )
            return None

        self._model = model
        return model

    # -- scoring --------------------------------------------------------

    def _score(self, model: object, query: str, candidates: list[ScoredChunk]) -> list[float]:
        """Score every ``(query, display_text)`` pair with the model (blocking).

        Runs inside a worker thread via :func:`asyncio.to_thread`. Returns one
        float per candidate, in candidate order.
        """

        pairs = [[query, candidate.display_text] for candidate in candidates]
        # `predict` returns a numpy array (or list) of floats, one per pair.
        raw_scores = model.predict(pairs)  # type: ignore[attr-defined]
        return [float(score) for score in raw_scores]

    async def rerank(
        self,
        query: str,
        candidates: list[ScoredChunk],
        top_k: int = DEFAULT_TOP_K,
    ) -> list[ScoredChunk]:
        """Re-rank ``candidates`` for ``query`` and return the top ``top_k``.

        On success, returns the ``min(top_k, n)`` candidates with the highest
        model relevance scores (ties broken by ``chunk_id`` ascending). On any
        failure or timeout, returns ``candidates[:top_k]`` unchanged and logs
        once (Req 4.4). Never raises.
        """

        if not candidates:
            return []

        model = self._ensure_model()
        if model is None:
            return _fallback(candidates, top_k)

        try:
            scores = await asyncio.wait_for(
                asyncio.to_thread(self._score, model, query, candidates),
                timeout=self._timeout_s if self._timeout_s > 0 else None,
            )
        except TimeoutError:
            self._log_once(
                "Cross-encoder re-ranking exceeded %d ms for %d candidates; "
                "falling back to hybrid order.",
                self._settings.rerank_timeout_ms,
                len(candidates),
            )
            return _fallback(candidates, top_k)
        except Exception as exc:  # noqa: BLE001 - any scoring error must fall back
            self._log_once(
                "Cross-encoder re-ranking failed (%s); falling back to hybrid order.",
                exc,
            )
            return _fallback(candidates, top_k)

        # Defensive: a well-behaved model returns one score per pair, but if the
        # shapes disagree we cannot trust the ranking — fall back.
        if len(scores) != len(candidates):
            self._log_once(
                "Cross-encoder returned %d scores for %d candidates; "
                "falling back to hybrid order.",
                len(scores),
                len(candidates),
            )
            return _fallback(candidates, top_k)

        return _select_top_k(candidates, scores, top_k)

    # -- logging --------------------------------------------------------

    def _log_once(self, msg: str, *args: object) -> None:
        """Log a re-ranker failure a single time to avoid per-request spam."""

        if self._logged_failure:
            logger.debug(msg, *args)
            return
        self._logged_failure = True
        logger.warning(msg, *args)


# ---------------------------------------------------------------------------
# Hosted rerank adapter (optional)
# ---------------------------------------------------------------------------


class HostedRerankAdapter:
    """Route re-ranking to a hosted rerank API (e.g. Cohere Rerank).

    This adapter satisfies the same :class:`Reranker` protocol as the local
    cross-encoder so callers can swap implementations via a settings flag. It
    reads an API key from ``settings.rerank_api_key`` (falling back to
    ``getattr`` so the setting is optional); when unconfigured — or on any
    transport/scoring failure — it behaves exactly like the fallback path,
    returning ``candidates[:top_k]`` unchanged and logging once (Req 4.4). It
    never raises to the caller.

    The hosted call itself is intentionally left as a minimal, clearly-marked
    integration point: wiring in a concrete provider SDK (Cohere, Voyage, etc.)
    only needs to fill in :meth:`_hosted_scores` without touching the
    surrounding fallback contract.

    Args:
        settings: Optional settings override. Defaults to :func:`get_settings`.
        model_name: Optional hosted model/endpoint identifier.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        model_name: str | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        # These settings are optional; the adapter degrades to fallback when
        # they are absent so an unconfigured deployment stays functional.
        self._api_key: str = getattr(self._settings, "rerank_api_key", "") or ""
        self._model_name = model_name or getattr(
            self._settings, "rerank_hosted_model", "rerank-english-v3.0"
        )
        self._logged_failure = False

    async def rerank(
        self,
        query: str,
        candidates: list[ScoredChunk],
        top_k: int = DEFAULT_TOP_K,
    ) -> list[ScoredChunk]:
        """Re-rank via the hosted API; fall back on missing config or failure."""

        if not candidates:
            return []

        if not self._api_key:
            self._log_once(
                "Hosted rerank API key not configured; falling back to hybrid order."
            )
            return _fallback(candidates, top_k)

        try:
            scores = await self._hosted_scores(query, candidates)
        except Exception as exc:  # noqa: BLE001 - any API error must fall back
            self._log_once(
                "Hosted rerank call failed (%s); falling back to hybrid order.",
                exc,
            )
            return _fallback(candidates, top_k)

        if len(scores) != len(candidates):
            self._log_once(
                "Hosted rerank returned %d scores for %d candidates; "
                "falling back to hybrid order.",
                len(scores),
                len(candidates),
            )
            return _fallback(candidates, top_k)

        return _select_top_k(candidates, scores, top_k)

    async def _hosted_scores(
        self,
        query: str,
        candidates: list[ScoredChunk],
    ) -> list[float]:
        """Return one relevance score per candidate from the hosted provider.

        Integration point: a concrete deployment fills this in with a real HTTP
        call (e.g. Cohere Rerank) using ``self._api_key`` and
        ``self._model_name``. Until wired, it raises :class:`NotImplementedError`
        so :meth:`rerank` transparently falls back to the hybrid order rather
        than silently returning a bogus ranking.
        """

        raise NotImplementedError(
            "HostedRerankAdapter._hosted_scores is a stub; wire in a hosted "
            "rerank provider (e.g. Cohere Rerank) to enable hosted re-ranking."
        )

    def _log_once(self, msg: str, *args: object) -> None:
        """Log a hosted-rerank failure a single time to avoid per-request spam."""

        if self._logged_failure:
            logger.debug(msg, *args)
            return
        self._logged_failure = True
        logger.warning(msg, *args)
