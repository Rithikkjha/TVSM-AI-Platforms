"""Layered query caches built on the :mod:`backends` byte store.

This module implements the two query-facing caches described in the design
("Components and Interfaces > 8. Caching"):

- :class:`EmbeddingCache` — memoizes the embedding *vector* for an exact query
  text, so a repeated question skips the Azure OpenAI embedding call. Keyed by
  ``"emb:" + sha256(query_text)`` with a 24-hour default TTL (Req 7.3, 7.5).
- :class:`ResultCache` — memoizes the full answer + citations payload for a
  ``(query_text, filters)`` pair, so an identical request skips the entire
  retrieval + LLM pipeline. Keyed by ``"res:" + sha256(query_text + canonical
  filters)`` with a 1-hour default TTL (Req 7.1, 7.6).

Both caches are thin, deterministic wrappers over a
:class:`~retrieval.cache.backends.CacheBackend`: they own key derivation and
(de)serialization only; storage, TTL enforcement, and prefix invalidation live
in the backend. Backend and TTL are injected via the constructor; the
:func:`build_query_caches` factory wires them from ``settings`` for the common
case.

Determinism (design Property 12): key derivation is pure SHA-256 over a
canonical string, so equal inputs always map to the same key, and distinct
``(query, filters)`` inputs map to distinct result-cache keys. Filter dicts are
serialized with sorted keys so semantically equal filters (regardless of insert
order) collapse to one key.

Requirements: 7.1, 7.3, 7.5, 7.6, 7.7.
"""

from __future__ import annotations

import hashlib
import json
import logging

from retrieval.cache.backends import CacheBackend, get_cache_backend

logger = logging.getLogger(__name__)

__all__ = [
    "EMBEDDING_KEY_PREFIX",
    "RESULT_KEY_PREFIX",
    "EmbeddingCache",
    "ResultCache",
    "build_query_caches",
]

# Stable key namespaces. Kept as module constants so invalidation callers and
# the caches agree on exactly one prefix per cache (and so prefix-based
# `delete_prefix` invalidation is unambiguous).
EMBEDDING_KEY_PREFIX = "emb:"
RESULT_KEY_PREFIX = "res:"

# UTF-8 is used for all hashing so the same query text hashes identically
# across processes and platforms.
_ENCODING = "utf-8"


def _sha256_hex(text: str) -> str:
    """Return the SHA-256 hex digest of ``text`` (deterministic, pure)."""
    return hashlib.sha256(text.encode(_ENCODING)).hexdigest()


def _canonical_filters(filters: dict | None) -> str:
    """Serialize ``filters`` to a canonical string for stable keying.

    ``json.dumps(..., sort_keys=True)`` guarantees that two filter dicts with
    the same key/value pairs but different insertion order produce the same
    string — and therefore the same cache key (design Property 12). ``None`` is
    normalized to an empty object so "no filters" is a single, stable key.
    """
    return json.dumps(filters or {}, sort_keys=True, separators=(",", ":"))


class EmbeddingCache:
    """Cache of query-text → embedding vector, backed by a ``CacheBackend``.

    The key is ``"emb:" + sha256(query_text)`` (Req 7.3), and values are the
    embedding vector serialized as a JSON array of floats. The default TTL is
    24 hours (Req 7.5), supplied here via constructor injection so the same
    class serves both the in-memory dev backend and Redis in prod.
    """

    def __init__(self, backend: CacheBackend, ttl_seconds: int = 86_400) -> None:
        self._backend = backend
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def _key(query: str) -> str:
        """Derive the namespaced cache key for ``query`` (pure/deterministic)."""
        return f"{EMBEDDING_KEY_PREFIX}{_sha256_hex(query)}"

    async def get(self, query: str) -> list[float] | None:
        """Return the cached vector for ``query``, or ``None`` on a miss.

        A corrupt/undecodable cached value is treated as a miss (and logged)
        rather than raised, so a bad entry degrades to a recompute instead of
        breaking the query path.
        """
        raw = await self._backend.get(self._key(query))
        if raw is None:
            return None
        try:
            vector = json.loads(raw.decode(_ENCODING))
        except (ValueError, UnicodeDecodeError) as exc:
            logger.warning("Discarding corrupt embedding-cache entry: %s", exc)
            return None
        if not isinstance(vector, list):
            logger.warning(
                "Discarding embedding-cache entry of unexpected type: %s",
                type(vector).__name__,
            )
            return None
        return [float(component) for component in vector]

    async def set(self, query: str, vector: list[float]) -> None:
        """Store ``vector`` for ``query`` with the configured TTL (Req 7.5)."""
        payload = json.dumps(vector, separators=(",", ":")).encode(_ENCODING)
        await self._backend.set(self._key(query), payload, self._ttl_seconds)

    async def invalidate_prefix(self, prefix: str = EMBEDDING_KEY_PREFIX) -> None:
        """Invalidate cached embeddings under ``prefix`` (Req 7.7).

        With no argument this clears the entire embedding namespace. Callers on
        the re-ingest path pass a more specific prefix when they maintain one.
        """
        await self._backend.delete_prefix(prefix)


class ResultCache:
    """Cache of ``(query, filters)`` → answer payload, backed by a backend.

    The key is ``"res:" + sha256(query_text + canonical_filters)`` (Req 7.1,
    7.6). Values are the full answer + citations payload serialized as JSON.
    The default TTL is 1 hour (Req 7.6). Distinct ``(query, filters)`` pairs
    produce distinct keys (design Property 12), while filter dicts that differ
    only in key order collapse to the same key via canonical serialization.
    """

    def __init__(self, backend: CacheBackend, ttl_seconds: int = 3_600) -> None:
        self._backend = backend
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def _key(query: str, filters: dict | None) -> str:
        """Derive the namespaced cache key for ``(query, filters)``.

        The query text and canonical filter serialization are joined with a
        NUL separator that cannot appear in the JSON filter string, so no
        ``(query, filters)`` pair can collide with another by concatenation
        ambiguity (e.g. query ``"a"`` + filters vs query ``"a{...}"``).
        """
        material = f"{query}\x00{_canonical_filters(filters)}"
        return f"{RESULT_KEY_PREFIX}{_sha256_hex(material)}"

    async def get(self, query: str, filters: dict | None = None) -> dict | None:
        """Return the cached answer payload, or ``None`` on a miss.

        A corrupt/undecodable entry is treated as a miss (and logged) so the
        pipeline recomputes rather than raising.
        """
        raw = await self._backend.get(self._key(query, filters))
        if raw is None:
            return None
        try:
            payload = json.loads(raw.decode(_ENCODING))
        except (ValueError, UnicodeDecodeError) as exc:
            logger.warning("Discarding corrupt result-cache entry: %s", exc)
            return None
        if not isinstance(payload, dict):
            logger.warning(
                "Discarding result-cache entry of unexpected type: %s",
                type(payload).__name__,
            )
            return None
        return payload

    async def set(
        self, query: str, filters: dict | None, payload: dict
    ) -> None:
        """Store ``payload`` for ``(query, filters)`` with the TTL (Req 7.6)."""
        blob = json.dumps(payload, separators=(",", ":")).encode(_ENCODING)
        await self._backend.set(self._key(query, filters), blob, self._ttl_seconds)

    async def invalidate_prefix(self, prefix: str = RESULT_KEY_PREFIX) -> None:
        """Invalidate cached results under ``prefix`` (Req 7.7).

        With no argument this clears the entire result namespace. Because
        result keys are opaque hashes, whole-namespace invalidation is the
        conservative default on re-ingest.
        """
        await self._backend.delete_prefix(prefix)


def build_query_caches(settings: object) -> tuple[EmbeddingCache, ResultCache]:
    """Construct both query caches from ``settings`` over a shared backend.

    Reads the backend selection (via :func:`get_cache_backend`) and the two
    TTLs (``embedding_cache_ttl_seconds`` default 24h, ``result_cache_ttl_seconds``
    default 1h) from ``settings``, returning a ready-to-use
    ``(EmbeddingCache, ResultCache)`` pair. Both caches share one backend so a
    single Redis connection (or one in-memory store) serves both namespaces,
    which are kept disjoint by their ``emb:`` / ``res:`` prefixes.
    """
    backend = get_cache_backend(settings)
    embedding_ttl = getattr(settings, "embedding_cache_ttl_seconds", 86_400)
    result_ttl = getattr(settings, "result_cache_ttl_seconds", 3_600)
    return (
        EmbeddingCache(backend, ttl_seconds=embedding_ttl),
        ResultCache(backend, ttl_seconds=result_ttl),
    )
