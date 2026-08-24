"""Byte-oriented cache backends for the V2 query cache layer.

This module defines the low-level storage abstraction used by the layered
query cache (embedding cache + result cache). It intentionally knows nothing
about queries, embeddings, or citations — it only stores and retrieves opaque
``bytes`` values under string keys, with per-key TTLs and prefix-based
invalidation. Higher-level caches (``query_cache.py``) build on top of it.

Two backends are provided:

- :class:`InMemoryTTLBackend` — the development default. A process-local
  dict with per-key expiry timestamps and lazy eviction. Thread-safe via a
  simple lock so it is usable from ``asyncio`` code that offloads to threads.
- :class:`RedisBackend` — an optional production backend selected via the
  ``cache_backend`` setting. The ``redis`` package is imported lazily so a
  deployment without it installed can still import this module and fall back
  to the in-memory backend.

The :func:`get_cache_backend` factory picks a backend from settings and, per
the design ("Components and Interfaces > 8. Caching"), falls back to the
in-memory backend when Redis is requested but unreachable.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7.
"""

from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

__all__ = [
    "CacheBackend",
    "InMemoryTTLBackend",
    "RedisBackend",
    "RedisConnectionError",
    "get_cache_backend",
]


class CacheBackend(ABC):
    """Abstract byte store with TTL and prefix invalidation.

    Implementations store opaque ``bytes`` values keyed by ``str``. All
    methods are asynchronous so backends that perform network I/O (Redis)
    share the same interface as the in-memory backend.
    """

    @abstractmethod
    async def get(self, key: str) -> bytes | None:
        """Return the stored value for ``key``, or ``None`` if missing/expired."""
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, value: bytes, ttl_seconds: int) -> None:
        """Store ``value`` under ``key``, expiring after ``ttl_seconds``."""
        raise NotImplementedError

    @abstractmethod
    async def delete_prefix(self, prefix: str) -> None:
        """Delete every key that begins with ``prefix`` (cache invalidation)."""
        raise NotImplementedError


class InMemoryTTLBackend(CacheBackend):
    """Process-local dict cache with per-key expiry and lazy eviction.

    This is the development default (Req 7.x). Expired entries are evicted
    lazily on access; a full sweep also runs opportunistically on ``set`` so
    a write-heavy workload does not accumulate dead keys unbounded.

    Thread-safety is provided by a single lock guarding the underlying dict,
    which is sufficient because every operation is a short, in-memory update.
    """

    def __init__(self) -> None:
        # key -> (value, expires_at_monotonic)
        self._store: dict[str, tuple[bytes, float]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _now() -> float:
        # Monotonic clock so TTLs are unaffected by wall-clock adjustments.
        return time.monotonic()

    async def get(self, key: str) -> bytes | None:
        now = self._now()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at <= now:
                # Lazily evict the expired entry.
                self._store.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: bytes, ttl_seconds: int) -> None:
        now = self._now()
        expires_at = now + max(ttl_seconds, 0)
        with self._lock:
            self._store[key] = (value, expires_at)
            # Opportunistic sweep of expired entries to bound memory growth.
            if len(self._store) > 1:
                expired = [k for k, (_, exp) in self._store.items() if exp <= now]
                for k in expired:
                    self._store.pop(k, None)

    async def delete_prefix(self, prefix: str) -> None:
        with self._lock:
            to_delete = [k for k in self._store if k.startswith(prefix)]
            for k in to_delete:
                self._store.pop(k, None)


class RedisConnectionError(RuntimeError):
    """Raised when a :class:`RedisBackend` cannot be constructed/connected.

    Callers (notably :func:`get_cache_backend`) catch this to fall back to the
    in-memory backend rather than crashing at startup.
    """


class RedisBackend(CacheBackend):
    """Redis-backed cache using ``redis.asyncio`` (optional production backend).

    The ``redis`` package is imported lazily inside ``__init__`` so this module
    imports cleanly on systems where Redis is not installed. If the package is
    missing or the client cannot be constructed, a :class:`RedisConnectionError`
    is raised so the caller can fall back to :class:`InMemoryTTLBackend`.

    Note: constructing the async client does not itself open a socket, so a
    dead server is typically surfaced on the first command rather than here.
    The factory logs and falls back on either failure mode.
    """

    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        try:
            # Lazy, guarded import: a missing `redis` package must not break
            # module import for the in-memory path.
            from redis import asyncio as redis_asyncio
        except ImportError as exc:  # pragma: no cover - depends on env
            raise RedisConnectionError(
                "The 'redis' package is not installed; install the optional "
                "'redis' extra to use the Redis cache backend."
            ) from exc

        try:
            self._client = redis_asyncio.from_url(url)
        except Exception as exc:  # noqa: BLE001 - normalize any client error
            raise RedisConnectionError(
                f"Failed to construct Redis client for URL {url!r}: {exc}"
            ) from exc

        self._url = url

    async def get(self, key: str) -> bytes | None:
        value = await self._client.get(key)
        if value is None:
            return None
        # redis-py returns bytes when decode_responses is not set (the default).
        return value if isinstance(value, bytes) else bytes(value)

    async def set(self, key: str, value: bytes, ttl_seconds: int) -> None:
        # `ex` sets an expiry in seconds; must be a positive integer.
        ttl = max(int(ttl_seconds), 1)
        await self._client.set(key, value, ex=ttl)

    async def delete_prefix(self, prefix: str) -> None:
        # SCAN avoids blocking the server the way KEYS would on large datasets.
        pattern = f"{prefix}*"
        keys_to_delete: list[bytes | str] = []
        async for key in self._client.scan_iter(match=pattern):
            keys_to_delete.append(key)
        if keys_to_delete:
            await self._client.delete(*keys_to_delete)


def get_cache_backend(settings: object) -> CacheBackend:
    """Return a cache backend selected from ``settings``.

    Selects :class:`RedisBackend` when ``settings.cache_backend == "redis"``,
    falling back to :class:`InMemoryTTLBackend` (with a logged warning) if the
    Redis client cannot be constructed or its package is missing. For any other
    value of ``cache_backend`` (including the default ``"memory"``), the
    in-memory backend is returned.

    The design specifies that startup falls back to the in-memory backend on a
    Redis connection error, so this factory never raises for a misconfigured or
    unreachable Redis instance.
    """
    backend_name = getattr(settings, "cache_backend", "memory")

    if backend_name == "redis":
        redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
        try:
            backend = RedisBackend(url=redis_url)
            logger.info("Using Redis cache backend at %s", redis_url)
            return backend
        except RedisConnectionError as exc:
            logger.warning(
                "Redis cache backend unavailable (%s); falling back to "
                "in-memory TTL cache.",
                exc,
            )
            return InMemoryTTLBackend()

    return InMemoryTTLBackend()
