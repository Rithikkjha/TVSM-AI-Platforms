"""In-memory LRU cache for frequently accessed entity embedding vectors.

The ``HotEmbeddingsCache`` accelerates per-entity vector lookups (for example,
graph-expansion hydration) by keeping the most recently used embeddings in
process memory, eliminating vector store round-trips for hot keys. It is
independent of the query/result caches.

Backed by :class:`collections.OrderedDict`: reads move the accessed key to the
most-recently-used end, and once the cache reaches ``capacity`` the least
recently used entry is evicted via ``popitem(last=False)``. All operations are
O(1) and in-memory, meeting the sub-millisecond lookup target.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Awaitable, Callable

__all__ = ["HotEmbeddingsCache"]


class HotEmbeddingsCache:
    """LRU cache of entity embedding vectors keyed by ``source_id``.

    Args:
        capacity: Maximum number of embedding vectors to retain. Once exceeded,
            the least recently used entry is evicted. Defaults to 500 (Req 8.1).
    """

    def __init__(self, capacity: int = 500) -> None:
        if capacity < 1:
            raise ValueError("capacity must be a positive integer")
        self._capacity = capacity
        self._store: OrderedDict[str, list[float]] = OrderedDict()

    @property
    def capacity(self) -> int:
        """The maximum number of entries the cache will hold."""
        return self._capacity

    def get(self, source_id: str) -> list[float] | None:
        """Return the cached vector for ``source_id``, or ``None`` on a miss.

        On a hit, the entry is marked as most recently used.
        """
        if source_id not in self._store:
            return None
        self._store.move_to_end(source_id)
        return self._store[source_id]

    def put(self, source_id: str, vector: list[float]) -> None:
        """Insert or update ``source_id`` with ``vector`` as most recently used.

        Evicts the least recently used entry if the insertion pushes the cache
        over capacity (Req 8.4).
        """
        if source_id in self._store:
            self._store.move_to_end(source_id)
        self._store[source_id] = vector
        if len(self._store) > self._capacity:
            self._store.popitem(last=False)

    async def get_or_fetch(
        self,
        source_id: str,
        fetch: Callable[[str], Awaitable[list[float]]],
    ) -> list[float]:
        """Return the cached vector for ``source_id`` or fetch and cache it.

        On a cache hit, the entry is moved to the most-recently-used end and
        returned without invoking ``fetch`` (Req 8.2). On a miss, ``fetch`` is
        awaited, the resulting vector is inserted, the LRU entry is evicted if
        the cache is over capacity, and the vector is returned (Req 8.3, 8.4).

        Args:
            source_id: The entity identifier to look up.
            fetch: Async callable that resolves ``source_id`` to its vector when
                the value is not already cached.

        Returns:
            The embedding vector for ``source_id``.
        """
        cached = self.get(source_id)
        if cached is not None:
            return cached

        vector = await fetch(source_id)
        self.put(source_id, vector)
        return vector

    def invalidate(self, source_id: str) -> None:
        """Remove the cached entry for ``source_id`` if present (Req 8.5)."""
        self._store.pop(source_id, None)

    def __len__(self) -> int:
        """Return the number of entries currently cached."""
        return len(self._store)

    def __contains__(self, source_id: object) -> bool:
        """Return whether ``source_id`` is currently cached (no LRU update)."""
        return source_id in self._store
