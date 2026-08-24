"""Hybrid dense + sparse retrieval with Reciprocal Rank Fusion (RRF).

The :class:`HybridRetriever` combines two complementary rankings for one query:

* a **dense** semantic ranking from the
  :class:`~storage.vector.vector_store.VectorStore` (cosine similarity over the
  query embedding), and
* a **sparse** keyword ranking from the
  :class:`~storage.vector.sparse_index.SparseIndex` (BM25 term-frequency).

The two ranked lists of ``chunk_id`` values are fused into a single ranking via
:func:`~retrieval.search.rrf.reciprocal_rank_fusion` (``k=60``), which needs no
score normalization and is therefore robust across the incomparable dense and
sparse score scales. The fused top-``top_n`` ids are hydrated into
:class:`ScoredChunk` objects carrying the chunk text and metadata needed by the
downstream re-ranker (task 8.1) and citation engine.

Design decisions (design.md §4 "Hybrid retriever + RRF"):

* Dense and sparse searches run **concurrently** via :func:`asyncio.gather`
  (Req 3.2).
* If the sparse index reports itself unavailable
  (``await sparse_index.is_available()`` is ``False``), the sparse leg is
  skipped, only the dense ranked list is fused, and a warning is logged
  (Req 3.5). RRF over a single list is order-preserving, so the retriever
  degrades cleanly to dense-only.
* Fusion is delegated to the pure, deterministic RRF function (Req 3.4).

Requirements: 3.2, 3.4, 3.5.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from retrieval.search.rrf import reciprocal_rank_fusion
from storage.vector.sparse_index import SparseHit, SparseIndex
from storage.vector.vector_store import VectorSearchHit, VectorStore

__all__ = ["ScoredChunk", "HybridRetriever"]

logger = logging.getLogger(__name__)

#: Default RRF constant (Req 3.3) and retrieval breadth (design.md §4).
DEFAULT_RRF_K: int = 60
DEFAULT_TOP_N: int = 30

#: Entity type used for chunk vectors in the shared vector store (design.md §3).
_CHUNK_ENTITY_TYPE: str = "Chunk"


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScoredChunk:
    """A fused, hydrated retrieval result consumed downstream.

    This type is intentionally self-contained and importable so the
    cross-encoder re-ranker (task 8.1) and the citation engine can depend on it
    without reaching back into the vector/sparse hit shapes.

    Attributes:
        chunk_id: The chunk's id (``== source_id`` of the chunk vector record).
        score: The fused RRF score (higher is more relevant). This is the
            fusion score, not a raw dense/sparse score.
        text: The chunk's raw text. The dense :class:`VectorSearchHit` does not
            store text, so this is hydrated from the sparse hit's metadata when
            available and is otherwise an empty string (the re-ranker/citation
            engine may hydrate it from another source). See ``display_text``.
        display_text: The context-prepended text used for re-ranking and
            citation context (design.md §5). Defaults to ``text``.
        section_title: Nearest preceding heading / structured field name the
            chunk was derived from; ``None`` when unknown.
        repo_name: Repository the chunk belongs to; ``None`` when unknown.
        doc_type: One of ``product|structure|tech|confluence|jira``; ``None``
            when unknown.
        parent_source_id: ``source_id`` of the full document entity this chunk
            was split from; ``None`` when unknown.
        chunk_index: 0-based order within the parent document; ``None`` when
            unknown.
        source_ref: File path / page URL / ticket key locating the chunk's
            origin content; ``None`` when unknown.
        metadata: Free-form metadata dict carried from the sparse hit (kept for
            downstream consumers that prefer a dict view).
    """

    chunk_id: str
    score: float
    text: str = ""
    display_text: str = ""
    section_title: str | None = None
    repo_name: str | None = None
    doc_type: str | None = None
    parent_source_id: str | None = None
    chunk_index: int | None = None
    source_ref: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Hybrid retriever
# ---------------------------------------------------------------------------


class HybridRetriever:
    """Fuse dense vector search and sparse BM25 search via RRF.

    The vector store and sparse index are injected so the retriever is
    backend-agnostic (Azure AI Search / Qdrant for dense, Azure native BM25 /
    local ``rank_bm25`` for sparse) and easy to test.

    Args:
        vector_store: Dense backend implementing
            :class:`~storage.vector.vector_store.VectorStore`.
        sparse_index: Sparse backend implementing
            :class:`~storage.vector.sparse_index.SparseIndex`.
        rrf_k: RRF constant passed to
            :func:`~retrieval.search.rrf.reciprocal_rank_fusion`. Defaults to
            :data:`DEFAULT_RRF_K` (60, Req 3.3).
        top_n: Default number of fused results to return. Defaults to
            :data:`DEFAULT_TOP_N` (30).
    """

    def __init__(
        self,
        vector_store: VectorStore,
        sparse_index: SparseIndex,
        *,
        rrf_k: int = DEFAULT_RRF_K,
        top_n: int = DEFAULT_TOP_N,
    ) -> None:
        self._vector_store = vector_store
        self._sparse_index = sparse_index
        self._rrf_k = rrf_k
        self._default_top_n = top_n

    async def retrieve(
        self,
        query: str,
        query_vector: list[float],
        filters: dict | None = None,
        top_n: int = DEFAULT_TOP_N,
    ) -> list[ScoredChunk]:
        """Retrieve the fused top-``top_n`` chunks for ``query``.

        Args:
            query: The raw query text (used by the sparse/BM25 leg).
            query_vector: The dense query embedding (used by the vector leg).
            filters: Optional exact-match metadata filters (e.g.
                ``{"repo_name": "svc", "doc_type": "confluence"}``) applied to
                both legs. Chunks marked ``is_duplicate=True`` are always
                excluded from the dense leg.
            top_n: Maximum number of fused results to return.

        Returns:
            A list of :class:`ScoredChunk` ordered by descending fused RRF
            score (ties broken by ``chunk_id`` ascending, per the RRF
            contract), of length ``min(top_n, unique fused ids)``.
        """

        # Determine sparse availability first so we only launch the sparse
        # search when it can actually serve results (Req 3.5).
        sparse_available = await self._sparse_index.is_available()

        if sparse_available:
            dense_hits, sparse_hits = await asyncio.gather(
                self._dense_search(query_vector, filters, top_n),
                self._sparse_search(query, filters, top_n),
            )
        else:
            logger.warning(
                "Sparse index unavailable; falling back to dense-only retrieval."
            )
            dense_hits = await self._dense_search(query_vector, filters, top_n)
            sparse_hits = []

        # Build the ranked id lists for fusion (best first).
        dense_ids = [hit.source_id for hit in dense_hits]
        ranked_lists: list[list[str]] = [dense_ids]
        if sparse_available:
            ranked_lists.append([hit.chunk_id for hit in sparse_hits])

        fused = reciprocal_rank_fusion(ranked_lists, k=self._rrf_k, limit=top_n)

        # Hydration lookups keyed by chunk_id; dense metadata is preferred.
        dense_by_id = {hit.source_id: hit for hit in dense_hits}
        sparse_by_id = {hit.chunk_id: hit for hit in sparse_hits}

        return [
            self._hydrate(chunk_id, score, dense_by_id.get(chunk_id), sparse_by_id.get(chunk_id))
            for chunk_id, score in fused
        ]

    # -- internal search helpers ----------------------------------------

    async def _dense_search(
        self,
        query_vector: list[float],
        filters: dict | None,
        top_n: int,
    ) -> list[VectorSearchHit]:
        """Run the dense vector search for chunk vectors only."""

        return await self._vector_store.search(
            query_vector,
            entity_type=_CHUNK_ENTITY_TYPE,
            limit=top_n,
            filters=filters,
            exclude_duplicates=True,
        )

    async def _sparse_search(
        self,
        query: str,
        filters: dict | None,
        top_n: int,
    ) -> list[SparseHit]:
        """Run the sparse BM25 search."""

        return await self._sparse_index.search(query, limit=top_n, filters=filters)

    # -- hydration ------------------------------------------------------

    @staticmethod
    def _hydrate(
        chunk_id: str,
        score: float,
        dense: VectorSearchHit | None,
        sparse: SparseHit | None,
    ) -> ScoredChunk:
        """Build a :class:`ScoredChunk`, preferring dense metadata.

        The dense hit carries the authoritative chunk metadata fields but no
        text; the sparse hit may carry the chunk text in its ``metadata`` dict.
        We prefer dense metadata for the structured fields and fall back to the
        sparse hit's metadata for anything the dense hit lacks (including the
        text, which the dense hit never stores).
        """

        sparse_meta: dict[str, str] = dict(sparse.metadata) if sparse else {}

        # Text is not stored on the dense hit; recover it from the sparse hit's
        # metadata when present, otherwise leave empty for later hydration.
        text = sparse_meta.get("text", "")
        display_text = sparse_meta.get("display_text", text)

        if dense is not None:
            section_title = dense.section_title
            repo_name = dense.repo_name
            doc_type = dense.doc_type
            parent_source_id = dense.parent_source_id
            chunk_index = dense.chunk_index
            source_ref = dense.source_ref
        else:
            # Sparse-only hit: pull whatever structured fields the sparse
            # metadata carried at index time.
            section_title = sparse_meta.get("section_title")
            repo_name = sparse_meta.get("repo_name")
            doc_type = sparse_meta.get("doc_type")
            parent_source_id = sparse_meta.get("parent_source_id")
            raw_index = sparse_meta.get("chunk_index")
            chunk_index = int(raw_index) if raw_index is not None else None
            source_ref = sparse_meta.get("source_ref")

        return ScoredChunk(
            chunk_id=chunk_id,
            score=score,
            text=text,
            display_text=display_text,
            section_title=section_title,
            repo_name=repo_name,
            doc_type=doc_type,
            parent_source_id=parent_source_id,
            chunk_index=chunk_index,
            source_ref=source_ref,
            metadata=sparse_meta,
        )
