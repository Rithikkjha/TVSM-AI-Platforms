"""Sparse (keyword / BM25) index abstraction for the Engineering Memory Graph.

The dense :class:`~storage.vector.vector_store.VectorStore` captures semantic
similarity, but queries that hinge on *exact* tokens — service names, error
codes, config keys — are better served by a term-frequency index. This module
defines the backend-agnostic :class:`SparseIndex` interface used by the
V2 ``HybridRetriever`` and a local ``rank_bm25``-backed implementation for the
dev / Qdrant path.

Two backends sit behind the one interface (see design.md
"Components and Interfaces > 3. Vector store + sparse index"):

* :class:`LocalBM25Index` — wraps :class:`rank_bm25.BM25Okapi` over an
  in-memory corpus, persisted to the ``data/`` directory so it survives
  process restarts. Serves the Qdrant/local path (this file).
* ``AzureSearchSparseIndex`` — delegates to Azure AI Search's native BM25
  (``search_text=query``) on the shared index. Added in a later task; this
  file is structured so it can be appended cleanly without touching the ABC.

Graceful degradation is a first-class concern: if ``rank_bm25`` is not
installed, or the persisted corpus fails to load/build, :meth:`is_available`
returns ``False`` and the caller falls back to dense-only retrieval and logs a
warning (Req 3.5). The ``rank_bm25`` import is therefore deferred to method
call time and wrapped in ``try``/``except`` so importing this module never
crashes on a missing optional dependency.

Requirements: 3.1 (index every chunk in the BM25 index alongside the dense
store), 3.5 (unavailable index → dense-only fallback).
"""

from __future__ import annotations

import logging
import pickle
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "SparseHit",
    "SparseIndex",
    "LocalBM25Index",
    "AzureSearchSparseIndex",
    "DEFAULT_BM25_INDEX_PATH",
    "DEFAULT_SPARSE_TEXT_FIELD",
    "tokenize",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared constants + helpers
# ---------------------------------------------------------------------------

#: Default on-disk location for the persisted local BM25 corpus. Resolved
#: relative to the ``smartbrain-v2`` project root (``storage/vector/`` is two
#: directories below it) so the path is stable regardless of the process CWD.
DEFAULT_BM25_INDEX_PATH: Path = (
    Path(__file__).resolve().parents[2] / "data" / "bm25_index.pkl"
)

#: Token grammar: runs of word characters (letters, digits, underscore),
#: lowercased. Simple and deterministic — good enough for BM25 keyword recall
#: and identical across the index/query paths so scoring stays consistent.
_TOKEN_RE = re.compile(r"\w+")


def tokenize(text: str) -> list[str]:
    """Tokenize ``text`` into lowercase word tokens.

    A single simple tokenizer is used for both indexing and querying so the
    two sides always agree on term boundaries. Returns an empty list for
    empty/whitespace-only input.
    """

    if not text:
        return []
    return _TOKEN_RE.findall(text.lower())


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SparseHit:
    """A scored result returned from :meth:`SparseIndex.search`.

    Attributes:
        chunk_id: The ``chunk_id`` of the matching chunk. Joins back to the
            dense vector record and graph ``Chunk`` node by id.
        score: The backend's relevance score (BM25 term-frequency score for
            :class:`LocalBM25Index`). Higher is more relevant. Scores are only
            meaningfully comparable within a single ranked list — RRF fusion
            downstream consumes the *rank*, not the raw score.
        metadata: Optional exact-match metadata stored with the chunk at
            index time (e.g. ``repo_name``, ``doc_type``, ``section_title``).
            Used to apply ``filters`` at search time.
    """

    chunk_id: str
    score: float
    metadata: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class SparseIndex(ABC):
    """Async interface implemented by every concrete sparse-index backend.

    All methods are async so backends can use non-blocking I/O (e.g. the
    Azure backend issues network calls). Implementations must be safe to
    reuse across concurrent calls. The interface is intentionally minimal and
    backend-neutral so a second implementation (Azure AI Search native BM25)
    can be added without changing this contract.
    """

    @abstractmethod
    async def index_chunk(
        self, chunk_id: str, text: str, metadata: dict[str, str]
    ) -> None:
        """Index one chunk's text under ``chunk_id`` (Req 3.1).

        Re-indexing an existing ``chunk_id`` replaces its stored text and
        metadata so the operation is idempotent.
        """

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 30,
        filters: dict[str, str] | None = None,
    ) -> list[SparseHit]:
        """Return the top-``limit`` keyword matches for ``query``.

        If ``filters`` is provided, only chunks whose stored metadata matches
        every ``field == value`` pair (exact match) are considered.
        """

    @abstractmethod
    async def delete(self, chunk_id: str) -> None:
        """Remove ``chunk_id`` from the index if present. No-op if absent."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Return whether the index is usable.

        When ``False``, the :class:`HybridRetriever` falls back to dense-only
        retrieval and logs a warning (Req 3.5).
        """


# ---------------------------------------------------------------------------
# Local rank_bm25 implementation
# ---------------------------------------------------------------------------


class LocalBM25Index(SparseIndex):
    """Local BM25 sparse index backed by :class:`rank_bm25.BM25Okapi`.

    The corpus is held in memory as a mapping ``chunk_id -> (tokens, text,
    metadata)`` and the :class:`~rank_bm25.BM25Okapi` model is (re)built
    lazily from the current corpus whenever it is dirty. The corpus is
    persisted to :data:`DEFAULT_BM25_INDEX_PATH` (a pickle in ``data/``) after
    every mutation so it survives process restarts.

    Availability (Req 3.5): if ``rank_bm25`` cannot be imported, or the
    persisted corpus cannot be loaded, the index marks itself unavailable and
    :meth:`is_available` returns ``False`` — callers then degrade to
    dense-only retrieval. Individual operations also fail soft (log + no-op /
    empty result) rather than raising into the retrieval path.
    """

    def __init__(self, index_path: Path | str | None = None) -> None:
        self._index_path: Path = (
            Path(index_path) if index_path is not None else DEFAULT_BM25_INDEX_PATH
        )
        # Ensure the parent directory exists at init time (avoids race on first persist)
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        # chunk_id -> {"tokens": list[str], "text": str, "metadata": dict}
        self._corpus: dict[str, dict[str, Any]] = {}
        # Cached BM25 model + the id order it was built over. ``None`` until
        # (re)built. ``_dirty`` forces a rebuild on the next search.
        self._bm25: Any | None = None
        self._doc_ids: list[str] = []
        self._dirty: bool = True
        # Set to False if rank_bm25 is missing or persistence load fails.
        self._available: bool = True
        # Persist debounce: only write to disk every N chunks to avoid rapid-fire IO
        self._persist_counter: int = 0
        self._persist_interval: int = 50  # persist every 50 chunks

        self._load()

    # -- rank_bm25 import guard -----------------------------------------

    @staticmethod
    def _import_bm25() -> Any | None:
        """Import :class:`rank_bm25.BM25Okapi`, or ``None`` if unavailable.

        Deferred to call time so a missing optional dependency never breaks
        module import (Req 3.5 graceful degradation).
        """

        try:
            from rank_bm25 import BM25Okapi
        except Exception:  # pragma: no cover - exercised when dep absent
            return None
        return BM25Okapi

    # -- persistence -----------------------------------------------------

    def _load(self) -> None:
        """Load the persisted corpus from disk, if any.

        A missing file is a clean empty index (still available). A corrupt /
        unreadable file marks the index unavailable so retrieval falls back to
        dense-only rather than serving a broken corpus.
        """

        if self._import_bm25() is None:
            logger.warning(
                "rank_bm25 is not installed; LocalBM25Index is unavailable and "
                "hybrid retrieval will fall back to dense-only."
            )
            self._available = False
            return

        if not self._index_path.exists():
            self._available = True
            return

        try:
            with self._index_path.open("rb") as fh:
                data = pickle.load(fh)
            if not isinstance(data, dict):
                raise ValueError("persisted BM25 corpus has unexpected shape")
            self._corpus = data
            self._dirty = True
            self._available = True
        except Exception:
            logger.exception(
                "Failed to load persisted BM25 corpus from %s; marking "
                "LocalBM25Index unavailable.",
                self._index_path,
            )
            self._corpus = {}
            self._available = False

    def _persist(self) -> None:
        """Write the in-memory corpus to disk. Failures are logged, not raised."""

        try:
            self._index_path.parent.mkdir(parents=True, exist_ok=True)
            # Write to a temp file then atomically replace to avoid leaving a
            # half-written pickle behind on crash.
            tmp_path = self._index_path.with_suffix(self._index_path.suffix + ".tmp")
            with tmp_path.open("wb") as fh:
                pickle.dump(self._corpus, fh, protocol=pickle.HIGHEST_PROTOCOL)
            tmp_path.replace(self._index_path)
        except Exception:
            logger.exception(
                "Failed to persist BM25 corpus to %s; in-memory index is still "
                "usable for this process.",
                self._index_path,
            )

    def flush(self) -> None:
        """Force persist the current in-memory index to disk.

        Call this at the end of ingestion to ensure all chunks are saved,
        since index_chunk uses debounced persistence.
        """
        if self._corpus:
            self._persist()

    # -- model build -----------------------------------------------------

    def _rebuild(self) -> None:
        """Rebuild the BM25 model from the current corpus if dirty."""

        if not self._dirty:
            return
        bm25_cls = self._import_bm25()
        if bm25_cls is None:
            self._available = False
            self._bm25 = None
            self._doc_ids = []
            return

        self._doc_ids = list(self._corpus.keys())
        token_lists = [self._corpus[cid]["tokens"] for cid in self._doc_ids]
        if not token_lists:
            # BM25Okapi rejects an empty corpus; treat as "no model, no hits".
            self._bm25 = None
        else:
            try:
                self._bm25 = bm25_cls(token_lists)
            except Exception:
                logger.exception("Failed to build BM25 model; index unavailable.")
                self._available = False
                self._bm25 = None
                self._doc_ids = []
                return
        self._dirty = False
        self._available = True

    # -- SparseIndex interface ------------------------------------------

    async def index_chunk(
        self, chunk_id: str, text: str, metadata: dict[str, str]
    ) -> None:
        if not chunk_id:
            raise ValueError("chunk_id must be a non-empty string")
        self._corpus[chunk_id] = {
            "tokens": tokenize(text),
            "text": text,
            "metadata": dict(metadata or {}),
        }
        self._dirty = True
        # Debounced persist: only write to disk every N chunks to avoid
        # rapid-fire IO and race conditions on the tmp file.
        self._persist_counter += 1
        if self._persist_counter >= self._persist_interval:
            self._persist_counter = 0
            self._persist()

    async def search(
        self,
        query: str,
        limit: int = 30,
        filters: dict[str, str] | None = None,
    ) -> list[SparseHit]:
        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        if not self._available:
            return []

        self._rebuild()
        if self._bm25 is None or not self._doc_ids:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        query_set = set(query_tokens)

        try:
            scores = self._bm25.get_scores(query_tokens)
        except Exception:
            logger.exception("BM25 scoring failed; returning no sparse hits.")
            return []

        hits: list[SparseHit] = []
        for chunk_id, score in zip(self._doc_ids, scores, strict=False):
            entry = self._corpus.get(chunk_id)
            if entry is None:
                continue
            # Require at least one shared token so only genuine keyword
            # matches enter the ranking. BM25Okapi can assign zero/negative
            # IDF scores to real matches in small corpora (a term appearing
            # in ~half the docs), so token overlap — not the raw score — is
            # the reliable match signal. Non-matching docs (no shared token)
            # are excluded so they don't pollute the fused ranking.
            if query_set.isdisjoint(entry["tokens"]):
                continue
            meta: dict[str, str] = entry.get("metadata", {})
            if filters and not self._matches_filters(meta, filters):
                continue
            hits.append(
                SparseHit(chunk_id=chunk_id, score=float(score), metadata=dict(meta))
            )

        # Rank by score desc; break ties on chunk_id asc for determinism.
        hits.sort(key=lambda h: (-h.score, h.chunk_id))
        return hits[:limit]

    async def delete(self, chunk_id: str) -> None:
        if chunk_id in self._corpus:
            del self._corpus[chunk_id]
            self._dirty = True
            self._persist()

    async def is_available(self) -> bool:
        return self._available

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _matches_filters(
        metadata: dict[str, str], filters: dict[str, str]
    ) -> bool:
        """Return ``True`` iff every filter pair exactly matches ``metadata``."""

        return all(metadata.get(field_name) == value for field_name, value in filters.items())


# ---------------------------------------------------------------------------
# Azure AI Search native BM25 implementation
# ---------------------------------------------------------------------------

#: Name of the searchable text field the sparse index writes chunk text into
#: on the shared Azure AI Search index. BM25 keyword search (``search_text``)
#: only works against an *analyzed/searchable* field, so this field MUST exist
#: on the index schema (see the SCHEMA REQUIREMENT note on
#: :class:`AzureSearchSparseIndex`).
DEFAULT_SPARSE_TEXT_FIELD: str = "chunk_text"

#: Chunk metadata keys that are known columns on the shared vector index
#: (mirrors the filterable/retrievable fields defined by
#: ``AzureAISearchVectorStore._build_index``). Only these keys are merged /
#: selected so a merge never fails on an unknown field, and they double as the
#: OData-filterable field set for :meth:`AzureSearchSparseIndex.search`.
_AZURE_SPARSE_METADATA_FIELDS: tuple[str, ...] = (
    "entity_type",
    "section_title",
    "repo_name",
    "doc_type",
    "parent_source_id",
    "chunk_index",
    "source_ref",
    "is_duplicate",
)


def _default_azure_index_name() -> str:
    """Return the shared index name, imported lazily from the vector store.

    Deferred so importing :mod:`storage.vector.sparse_index` never pulls in the
    heavy ``azure-search-documents`` SDK (imported at module scope by
    ``vector_store``) on the pure-local ``LocalBM25Index`` path. Falls back to
    the well-known literal if the import is unavailable for any reason.
    """

    try:
        from storage.vector.vector_store import DEFAULT_INDEX_NAME

        return DEFAULT_INDEX_NAME
    except Exception:  # pragma: no cover - defensive; literal matches source
        return "memory_graph_entities"


class AzureSearchSparseIndex(SparseIndex):
    """Sparse backend delegating to Azure AI Search's native BM25.

    Unlike :class:`LocalBM25Index`, this backend owns no separate corpus. It
    reuses the **same** Azure AI Search index that
    :class:`~storage.vector.vector_store.AzureAISearchVectorStore` writes vector
    records into (``DEFAULT_INDEX_NAME = "memory_graph_entities"``) and lets the
    search service score keyword relevance with its built-in BM25 similarity via
    ``search_text=query``. There is no second store to keep in sync — dense
    vectors and the sparse-searchable text live on one document keyed by
    ``source_id`` (== ``chunk_id``).

    .. important:: SCHEMA REQUIREMENT

        BM25 ``search_text`` only matches against **searchable** (analyzed)
        fields. The shared index built by
        ``AzureAISearchVectorStore._build_index`` does **not** currently define a
        searchable text field — its ``String`` fields are ``filterable`` /
        ``retrievable`` only. For this backend to return any hits, a searchable
        ``Edm.String`` field named :data:`DEFAULT_SPARSE_TEXT_FIELD`
        (``"chunk_text"``, or whatever ``text_field`` is passed here) must be
        added to that index definition (``searchable=True``). Until the vector
        index schema task adds it, :meth:`index_chunk` will merge the text
        successfully but :meth:`search` will find nothing to score. **This is a
        dependency a later index-schema task must satisfy.**

    Construction mirrors :class:`AzureAISearchVectorStore`: pass
    ``endpoint``/``api_key``/``index_name`` for a real client, or inject a
    ready-made async ``SearchClient`` via ``search_client`` for testing. When
    neither a client nor endpoint+key are supplied the backend is simply
    unavailable (:meth:`is_available` → ``False``) and hybrid retrieval falls
    back to dense-only (Req 3.5). The ``azure-search-documents`` import is
    deferred to construction time so the module still imports on the local path
    without the SDK present.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        index_name: str | None = None,
        *,
        search_client: Any | None = None,
        text_field: str = DEFAULT_SPARSE_TEXT_FIELD,
    ) -> None:
        if not text_field:
            raise ValueError("text_field must be a non-empty string")
        self._index_name: str = index_name or _default_azure_index_name()
        self._text_field: str = text_field
        # ``None`` marks the backend unavailable (missing config / SDK).
        self._search_client: Any | None = search_client

        if self._search_client is None and endpoint and api_key:
            azure = self._import_azure()
            if azure is not None:
                search_client_cls, azure_key_credential_cls = azure
                self._search_client = search_client_cls(
                    endpoint=endpoint,
                    index_name=self._index_name,
                    credential=azure_key_credential_cls(api_key),
                )
            else:
                logger.warning(
                    "azure-search-documents is not installed; "
                    "AzureSearchSparseIndex is unavailable and hybrid retrieval "
                    "will fall back to dense-only."
                )

    # -- azure SDK import guard -----------------------------------------

    @staticmethod
    def _import_azure() -> tuple[Any, Any] | None:
        """Import the async ``SearchClient`` + ``AzureKeyCredential``.

        Returns ``None`` (rather than raising) when the SDK is absent so a
        missing optional dependency degrades to an unavailable index instead of
        crashing module import (Req 3.5).
        """

        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents.aio import SearchClient
        except Exception:  # pragma: no cover - exercised when dep absent
            return None
        return SearchClient, AzureKeyCredential

    # -- OData filter construction --------------------------------------

    @staticmethod
    def _escape_odata(value: str) -> str:
        """Single-quote-escape a value for an OData string literal.

        Mirrors ``AzureAISearchVectorStore``: every user-supplied value flows
        through this so there's no string-concatenation injection surface into
        the query engine.
        """

        return str(value).replace("'", "''")

    def _build_filter(self, filters: dict[str, str] | None) -> str | None:
        """Build the OData ``$filter`` clause for a sparse search.

        Combines caller-provided exact-match ``filters`` with an implicit
        ``is_duplicate ne true`` exclusion (matching the dense store's
        ``exclude_duplicates`` default, Req 5.5). ``ne true`` also admits legacy
        documents where the field is null, so pre-V2 records are never dropped.
        """

        clauses: list[str] = []
        if filters:
            for field_name, value in filters.items():
                if not field_name:
                    raise ValueError("filter field names must be non-empty strings")
                clauses.append(
                    f"{self._escape_odata(field_name)} eq "
                    f"'{self._escape_odata(value)}'"
                )
        clauses.append("is_duplicate ne true")
        return " and ".join(clauses) if clauses else None

    # -- SparseIndex interface ------------------------------------------

    async def index_chunk(
        self, chunk_id: str, text: str, metadata: dict[str, str]
    ) -> None:
        """Merge the chunk's searchable text + metadata into the shared index.

        The vector store owns the index and the document lifecycle, so this uses
        ``merge_or_upload_documents`` (Azure's closest thing to UPSERT) keyed on
        ``source_id`` (== ``chunk_id``): it creates the document if the vector
        record hasn't landed yet, or merges the searchable ``chunk_text`` field
        (and any known metadata columns) into the existing document otherwise.
        Re-indexing the same ``chunk_id`` replaces the stored text, so the
        operation is idempotent.

        No-op when the backend is unavailable so ingestion never hard-fails on a
        missing sparse index (Req 3.5).
        """

        if not chunk_id:
            raise ValueError("chunk_id must be a non-empty string")
        if self._search_client is None:
            return

        document: dict[str, Any] = {
            "source_id": chunk_id,
            self._text_field: text,
        }
        # Only merge metadata keys that are real columns on the shared index so
        # the merge never fails on an unknown field.
        for key in _AZURE_SPARSE_METADATA_FIELDS:
            if metadata and key in metadata:
                document[key] = metadata[key]

        try:
            await self._search_client.merge_or_upload_documents(documents=[document])
        except Exception:
            logger.exception(
                "Failed to merge chunk %s into the Azure sparse index.", chunk_id
            )

    async def search(
        self,
        query: str,
        limit: int = 30,
        filters: dict[str, str] | None = None,
    ) -> list[SparseHit]:
        """Return the top-``limit`` BM25 keyword matches for ``query``.

        Delegates to ``SearchClient.search(search_text=query, ...)``; Azure AI
        Search scores results with native BM25 over the searchable text field.
        Results map to :class:`SparseHit` with ``chunk_id`` = ``source_id`` and
        ``score`` = ``@search.score``. Returns an empty list when the backend is
        unavailable so callers degrade to dense-only (Req 3.5).
        """

        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        if self._search_client is None:
            return []

        query_text = query.strip()
        if not query_text:
            return []

        search_filter = self._build_filter(filters)
        select_fields = ["source_id", *_AZURE_SPARSE_METADATA_FIELDS]

        try:
            results = await self._search_client.search(
                search_text=query_text,
                search_fields=[self._text_field],
                filter=search_filter,
                top=limit,
                select=select_fields,
            )
        except Exception:
            logger.exception("Azure BM25 search failed; returning no sparse hits.")
            return []

        hits: list[SparseHit] = []
        try:
            async for raw in results:
                # Defensive: skip any duplicate that slips through the filter.
                if raw.get("is_duplicate") is True:
                    continue
                source_id = str(raw.get("source_id", ""))
                if not source_id:
                    continue
                hits.append(
                    SparseHit(
                        chunk_id=source_id,
                        score=float(raw.get("@search.score", 0.0)),
                        metadata=self._extract_metadata(raw),
                    )
                )
        except Exception:
            logger.exception("Failed reading Azure BM25 results; truncating hits.")
        return hits

    async def delete(self, chunk_id: str) -> None:
        """Clear the chunk's searchable text from the shared document.

        The vector store owns document creation/deletion, so rather than
        deleting the whole document (which would drop the dense vector too) this
        merges ``chunk_text = None`` to clear the searchable field — mirroring
        ``AzureAISearchVectorStore.delete_embedding`` semantics for the sparse
        concern only. No-op when unavailable or ``chunk_id`` is falsy.
        """

        if not chunk_id or self._search_client is None:
            return
        try:
            await self._search_client.merge_or_upload_documents(
                documents=[{"source_id": chunk_id, self._text_field: None}]
            )
        except Exception:
            logger.exception(
                "Failed to clear sparse text for chunk %s on the Azure index.",
                chunk_id,
            )

    async def is_available(self) -> bool:
        """Return ``True`` when an Azure ``SearchClient`` is configured."""

        return self._search_client is not None

    async def close(self) -> None:
        """Release the underlying ``SearchClient`` if this instance owns one."""

        if self._search_client is not None:
            close = getattr(self._search_client, "close", None)
            if close is not None:
                await close()

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _extract_metadata(raw: dict[str, Any]) -> dict[str, str]:
        """Pull the known metadata columns off an Azure result document.

        Values are coerced to ``str`` (and ``None``/missing keys skipped) so the
        returned mapping matches :attr:`SparseHit.metadata`'s ``dict[str, str]``
        contract.
        """

        metadata: dict[str, str] = {}
        for key in _AZURE_SPARSE_METADATA_FIELDS:
            value = raw.get(key)
            if value is not None:
                metadata[key] = str(value)
        return metadata
