"""Deduplication service for near-duplicate chunk detection.

Compares incoming chunk embeddings against existing chunks for the same
repository using cosine similarity (retrieved directly from the vector
store's scored search results). When two chunks are near-duplicates
(cosine > 0.95), the lower-authority chunk is marked as the duplicate.

Authority ranking (higher wins):
    confluence: 3, steering/product/structure/tech: 2, jira: 1

On tied authority the chunk with the alphabetically-larger ``chunk_id``
is the duplicate (deterministic tiebreak ensuring symmetry regardless of
processing order — Property 8).

Requirements: 5.1, 5.2, 5.3, 5.4, 5.6.
Design: §6 "Deduplication service".
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from config.settings import get_settings

if TYPE_CHECKING:
    from storage.graph.graph_store import GraphStore
    from storage.vector.vector_store import VectorStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Authority ranking
# ---------------------------------------------------------------------------

#: Higher value means higher authority. "product", "structure", and "tech"
#: are steering subtypes and share the same rank as "steering".
AUTHORITY_RANK: dict[str, int] = {
    "confluence": 3,
    "steering": 2,
    "product": 2,
    "structure": 2,
    "tech": 2,
    "jira": 1,
}

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DedupDecision:
    """Result of a duplicate check.

    Attributes:
        is_duplicate: Whether a near-duplicate was found.
        canonical_chunk_id: The ``chunk_id`` of the winning (canonical)
            chunk, or ``None`` when no duplicate is detected.
        duplicate_chunk_id: The ``chunk_id`` of the losing (duplicate)
            chunk, or ``None`` when no duplicate is detected.
    """

    is_duplicate: bool
    canonical_chunk_id: str | None
    duplicate_chunk_id: str | None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class DeduplicationService:
    """Near-duplicate chunk detection and marking.

    Parameters:
        vector_store: Used to search for existing chunk vectors by
            ``repo_name``.
        graph_store: Optional. When provided, ``mark_duplicate`` writes
            a ``DUPLICATE_OF`` edge between the duplicate and canonical
            chunks in the graph. When ``None``, the edge write is
            skipped with a warning.
    """

    def __init__(
        self,
        vector_store: "VectorStore",
        graph_store: "GraphStore | None" = None,
    ) -> None:
        self._vector_store = vector_store
        self._graph_store = graph_store

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def check_duplicate(
        self,
        new_chunk_id: str,
        new_vector: list[float],
        new_doc_type: str,
        repo_name: str,
    ) -> DedupDecision:
        """Check whether ``new_chunk_id`` is a near-duplicate of an existing chunk.

        Steps:
            1. Search the vector store for existing chunks in the same
               ``repo_name`` using ``new_vector`` as the query (cosine
               similarity is returned as ``hit.score``).
            2. If the best score exceeds the configured threshold
               (``settings.dedup_cosine_threshold``, default 0.95),
               determine which chunk is the duplicate via authority +
               tiebreak.
            3. Return a :class:`DedupDecision`.

        On vector-store failure, logs a warning and returns a
        non-duplicate decision (canonical by default).
        """

        settings = get_settings()

        try:
            hits = await self._vector_store.search(
                query_vector=new_vector,
                filters={"repo_name": repo_name},
                entity_type="Chunk",
                limit=10,
                exclude_duplicates=False,
            )
        except Exception:
            logger.warning(
                "Vector store search failed during dedup check for chunk %s; "
                "treating as canonical (not duplicate).",
                new_chunk_id,
                exc_info=True,
            )
            return DedupDecision(
                is_duplicate=False,
                canonical_chunk_id=None,
                duplicate_chunk_id=None,
            )

        if not hits:
            return DedupDecision(
                is_duplicate=False,
                canonical_chunk_id=None,
                duplicate_chunk_id=None,
            )

        # Find the best scoring hit (cosine similarity from the vector
        # store search). Exclude self-matches (new_chunk_id already
        # indexed from a prior run).
        best_score: float = 0.0
        best_hit_id: str | None = None
        best_hit_doc_type: str | None = None

        for hit in hits:
            if hit.source_id == new_chunk_id:
                continue
            if hit.score > best_score:
                best_score = hit.score
                best_hit_id = hit.source_id
                best_hit_doc_type = hit.doc_type

        if best_hit_id is None or best_score <= settings.dedup_cosine_threshold:
            return DedupDecision(
                is_duplicate=False,
                canonical_chunk_id=None,
                duplicate_chunk_id=None,
            )

        # Determine canonical vs duplicate based on authority + tiebreak.
        canonical_id, duplicate_id = self._resolve_canonical(
            chunk_a_id=new_chunk_id,
            chunk_a_doc_type=new_doc_type,
            chunk_b_id=best_hit_id,
            chunk_b_doc_type=best_hit_doc_type or "",
        )

        return DedupDecision(
            is_duplicate=True,
            canonical_chunk_id=canonical_id,
            duplicate_chunk_id=duplicate_id,
        )

    async def mark_duplicate(
        self,
        duplicate_chunk_id: str,
        canonical_chunk_id: str,
    ) -> None:
        """Record the duplicate relationship.

        Writes a ``DUPLICATE_OF`` edge from the duplicate chunk to the
        canonical chunk in the graph store (if available). Also attempts
        to mark the duplicate's vector record with ``is_duplicate=True``
        — currently logged as a placeholder since the vector store ABC
        doesn't expose a single-field update method.

        If no graph store was injected, the edge write is skipped and a
        warning is logged.
        """

        # Write DUPLICATE_OF edge in the graph.
        if self._graph_store is not None:
            try:
                await self._graph_store.upsert_relationship(
                    source_id=duplicate_chunk_id,
                    source_label="Chunk",
                    target_id=canonical_chunk_id,
                    target_label="Chunk",
                    rel_type="DUPLICATE_OF",
                )
            except Exception:
                logger.warning(
                    "Failed to write DUPLICATE_OF edge: %s -> %s",
                    duplicate_chunk_id,
                    canonical_chunk_id,
                    exc_info=True,
                )
        else:
            logger.warning(
                "No graph store injected; skipping DUPLICATE_OF edge write "
                "for %s -> %s.",
                duplicate_chunk_id,
                canonical_chunk_id,
            )

        # Mark the duplicate vector record. The VectorStore ABC does not
        # expose a targeted metadata update, so we log the intent for now.
        # During ingestion the caller should upsert the VectorRecord with
        # is_duplicate=True set before writing.
        logger.info(
            "Duplicate chunk %s should be stored with is_duplicate=True "
            "(canonical: %s).",
            duplicate_chunk_id,
            canonical_chunk_id,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_canonical(
        chunk_a_id: str,
        chunk_a_doc_type: str,
        chunk_b_id: str,
        chunk_b_doc_type: str,
    ) -> tuple[str, str]:
        """Return ``(canonical_id, duplicate_id)``.

        The chunk with HIGHER authority wins (is canonical). On tied
        authority, the chunk with the alphabetically-smaller
        ``chunk_id`` wins (the larger id becomes the duplicate).

        This logic is symmetric: calling with (A, B) or (B, A) always
        yields the same canonical/duplicate assignment (Property 8).
        """

        rank_a = AUTHORITY_RANK.get(chunk_a_doc_type, 0)
        rank_b = AUTHORITY_RANK.get(chunk_b_doc_type, 0)

        if rank_a > rank_b:
            return chunk_a_id, chunk_b_id
        elif rank_b > rank_a:
            return chunk_b_id, chunk_a_id
        else:
            # Tied authority — alphabetically smaller chunk_id is canonical.
            if chunk_a_id <= chunk_b_id:
                return chunk_a_id, chunk_b_id
            else:
                return chunk_b_id, chunk_a_id


__all__ = [
    "AUTHORITY_RANK",
    "DedupDecision",
    "DeduplicationService",
]
