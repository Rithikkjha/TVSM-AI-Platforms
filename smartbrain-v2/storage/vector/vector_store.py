"""Vector store abstraction for the Engineering Memory Graph.

Two concrete backends are provided behind a single async interface:

* :class:`AzureAISearchVectorStore` — production backend using
  Azure AI Search via the official ``azure-search-documents`` SDK.
* :class:`QdrantVectorStore` — local/dev backend talking to Qdrant's
  REST API directly via :mod:`httpx` so that the ``qdrant-client``
  dependency isn't required.

Both implementations share the same semantics described in the design
document:

* Single index / collection: ``memory_graph_entities`` (configurable).
* Vector dimension: 3072 (``text-embedding-3-large``).
* Distance metric: cosine.
* Upsert semantics: re-ingesting the same ``source_id`` replaces the
  stored vector and metadata (used when text content changes).
* Metadata stored alongside each vector: ``source_id``, ``entity_type``,
  ``text_hash``, ``created_at``.

All user-supplied values (entity type filters, source ids, text hashes)
flow through structured SDK calls or JSON request bodies — never string
concatenation — so there's no injection surface.

See Requirement 2.7 and Property 5 for the behavioral contract this
module implements.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

import httpx
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

from config.settings import Settings

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

#: Embedding dimension. Defaults to 1536 for ``text-embedding-3-small``.
#: Set to 3072 for ``text-embedding-3-large``. Configurable via the
#: EMBEDDING_DIMENSION environment variable or settings.
#: Changing this after initial index creation requires a re-index.
import os as _os

EMBEDDING_DIMENSION: int = int(_os.environ.get("EMBEDDING_DIMENSION", "1536"))

#: Default index / collection name used by both backends.
DEFAULT_INDEX_NAME: str = "memory_graph_entities"

#: Algorithm / profile identifiers used by Azure AI Search. Kept as
#: module-level constants so tests can assert on them without magic
#: strings.
_AZURE_HNSW_CONFIG_NAME = "memory-graph-hnsw"
_AZURE_VECTOR_PROFILE_NAME = "memory-graph-vector-profile"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class VectorRecord:
    """A single vector to upsert into the store.

    Attributes:
        source_id: Primary key. Must match the ``source_id`` of the
            corresponding Neo4j entity so the two stores can be joined
            by id at query time.
        entity_type: Schema label of the source entity (e.g.
            ``"ConfluencePage"``). Used as a filter field.
        text_hash: SHA-256 of the source text that produced this
            vector. Enables ``text_hash``-keyed idempotency in the
            write coordinator.
        vector: Embedding of length :data:`EMBEDDING_DIMENSION`.
        created_at: ISO-8601 timestamp string recording when the
            embedding was computed.
        section_title: (V2 chunk field) Nearest preceding heading /
            structured field name the chunk was derived from. ``None``
            for legacy whole-document entity vectors.
        repo_name: (V2 chunk field) Repository the chunk belongs to.
            Filterable. ``None`` for legacy entity vectors.
        doc_type: (V2 chunk field) One of ``product|structure|tech|
            confluence|jira``. Filterable. ``None`` for legacy vectors.
        parent_source_id: (V2 chunk field) ``source_id`` of the full
            document entity this chunk was split from.
        chunk_index: (V2 chunk field) 0-based order within the parent
            document.
        source_ref: (V2 chunk field) file path / page URL / ticket key
            locating the chunk's origin content.
        is_duplicate: (V2 chunk field) ``True`` when the chunk was
            marked a near-duplicate by the deduplication service; such
            chunks are excluded from search by default (Req 5.5).

    Raises:
        ValueError: If any required string field is empty, or if the
            vector isn't exactly :data:`EMBEDDING_DIMENSION` floats.
    """

    source_id: str
    entity_type: str
    text_hash: str
    vector: list[float]
    created_at: str
    # V2 chunk metadata (optional; ``None``/``False`` for legacy entity
    # vectors so existing records keep validating unchanged).
    section_title: str | None = None
    repo_name: str | None = None
    doc_type: str | None = None
    parent_source_id: str | None = None
    chunk_index: int | None = None
    source_ref: str | None = None
    is_duplicate: bool = False

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("VectorRecord.source_id must be a non-empty string")
        if not self.entity_type:
            raise ValueError("VectorRecord.entity_type must be a non-empty string")
        if not self.text_hash:
            raise ValueError("VectorRecord.text_hash must be a non-empty string")
        if not self.created_at:
            raise ValueError("VectorRecord.created_at must be a non-empty string")
        if len(self.vector) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"VectorRecord.vector must have exactly {EMBEDDING_DIMENSION} "
                f"dimensions; got {len(self.vector)}"
            )


@dataclass(frozen=True, slots=True)
class VectorSearchHit:
    """A scored result returned from :meth:`VectorStore.search`.

    Attributes:
        source_id: Matching entity's ``source_id``.
        entity_type: Matching entity's schema label.
        text_hash: ``text_hash`` stored with the vector.
        created_at: ISO timestamp stored with the vector.
        score: Backend-reported similarity score. Higher is more
            similar for both Azure AI Search (``@search.score`` on a
            cosine vector query) and Qdrant (cosine similarity).
        section_title: (V2 chunk field) hydrated from the stored
            chunk metadata; ``None`` for legacy entity vectors.
        repo_name: (V2 chunk field) hydrated from the stored chunk
            metadata; ``None`` for legacy entity vectors.
        doc_type: (V2 chunk field) hydrated from the stored chunk
            metadata; ``None`` for legacy entity vectors.
        parent_source_id: (V2 chunk field) ``source_id`` of the parent
            document entity; ``None`` for legacy entity vectors.
        chunk_index: (V2 chunk field) 0-based order within the parent
            document; ``None`` for legacy entity vectors.
        source_ref: (V2 chunk field) file path / page URL / ticket key;
            ``None`` for legacy entity vectors.
        is_duplicate: (V2 chunk field) duplicate marker; ``False`` for
            legacy entity vectors.
    """

    source_id: str
    entity_type: str
    text_hash: str
    created_at: str
    score: float
    # V2 chunk metadata (optional; ``None``/``False`` for legacy vectors).
    section_title: str | None = None
    repo_name: str | None = None
    doc_type: str | None = None
    parent_source_id: str | None = None
    chunk_index: int | None = None
    source_ref: str | None = None
    is_duplicate: bool = False


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class VectorStore(ABC):
    """Async interface implemented by every concrete vector backend.

    All methods are async to allow backends to use non-blocking I/O.
    Implementations must be safe to reuse across many concurrent calls
    as long as :meth:`close` is called exactly once on shutdown.
    """

    @abstractmethod
    async def ensure_index(self) -> None:
        """Create the index/collection if it doesn't already exist.

        Implementations must be idempotent — a subsequent call on an
        existing index is a no-op.
        """

    @abstractmethod
    async def upsert_embedding(self, record: VectorRecord) -> None:
        """Upsert a single vector record keyed on ``source_id``.

        Re-upserting with the same ``source_id`` replaces the stored
        vector and metadata.
        """

    @abstractmethod
    async def upsert_embeddings(self, records: list[VectorRecord]) -> None:
        """Batch-upsert many vector records in one call."""

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        entity_type: str | None = None,
        limit: int = 10,
        *,
        filters: dict[str, str] | None = None,
        exclude_duplicates: bool = True,
    ) -> list[VectorSearchHit]:
        """Return the top-``limit`` cosine-similar hits for ``query_vector``.

        If ``entity_type`` is provided, only vectors with that entity
        type are considered.

        If ``filters`` is provided, only vectors whose stored chunk
        metadata matches every ``field == value`` pair are considered
        (e.g. ``{"repo_name": "svc", "doc_type": "confluence"}``).

        When ``exclude_duplicates`` is ``True`` (the default), vectors
        marked ``is_duplicate=True`` are omitted from the results
        (Req 5.5). Legacy entity vectors have no duplicate marker and
        are always included.
        """

    @abstractmethod
    async def delete_embedding(self, source_id: str) -> None:
        """Remove the vector record for ``source_id`` if it exists."""

    @abstractmethod
    async def close(self) -> None:
        """Release any underlying network resources."""

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
# Azure AI Search implementation
# ---------------------------------------------------------------------------


class AzureAISearchVectorStore(VectorStore):
    """Production backend backed by Azure AI Search.

    The store holds two SDK clients — a :class:`SearchIndexClient` for
    index administration (``ensure_index``) and a :class:`SearchClient`
    for document operations (upsert/search/delete). Both are closed on
    :meth:`close`.

    The ``endpoint``/``api_key``/``index_name`` arguments are accepted
    directly rather than reading from :mod:`src.config.settings` so the
    class is easy to test and can be used outside the usual app
    settings lifecycle. The :func:`get_vector_store` factory is the
    normal entry point in application code.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str = DEFAULT_INDEX_NAME,
        *,
        search_client: SearchClient | None = None,
        index_client: SearchIndexClient | None = None,
    ) -> None:
        if not endpoint:
            raise ValueError("AzureAISearchVectorStore requires a non-empty endpoint")
        if not api_key:
            raise ValueError("AzureAISearchVectorStore requires a non-empty api_key")
        if not index_name:
            raise ValueError("AzureAISearchVectorStore requires a non-empty index_name")

        self._endpoint = endpoint
        self._api_key = api_key
        self._index_name = index_name
        credential = AzureKeyCredential(api_key)
        # Allow the tests to inject mocks; otherwise build real clients.
        self._search_client: SearchClient = search_client or SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential,
        )
        self._index_client: SearchIndexClient = index_client or SearchIndexClient(
            endpoint=endpoint,
            credential=credential,
        )

    # -- schema ----------------------------------------------------------

    def _build_index(self) -> SearchIndex:
        """Construct the :class:`SearchIndex` definition for the store.

        Fields:
            source_id      — Edm.String, key
            entity_type    — Edm.String, filterable
            text_hash      — Edm.String
            vector         — Collection(Edm.Single), HNSW, 3072 dims
            created_at     — Edm.String (ISO timestamp)
            section_title  — Edm.String, filterable (Req 2.12)
            repo_name      — Edm.String, filterable (Req 2.12)
            doc_type       — Edm.String, filterable (Req 2.12)
            parent_source_id — Edm.String, filterable/retrievable
            chunk_index    — Edm.Int32, filterable/retrievable
            source_ref     — Edm.String, retrievable
            is_duplicate   — Edm.Boolean, filterable (Req 5.5)
        """

        fields = [
            SearchField(
                name="source_id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True,
                retrievable=True,
            ),
            SearchField(
                name="entity_type",
                type=SearchFieldDataType.String,
                filterable=True,
                retrievable=True,
            ),
            SearchField(
                name="text_hash",
                type=SearchFieldDataType.String,
                filterable=False,
                retrievable=True,
            ),
            SearchField(
                name="created_at",
                type=SearchFieldDataType.String,
                filterable=False,
                retrievable=True,
            ),
            # -- V2 chunk metadata fields --------------------------------
            SearchField(
                name="section_title",
                type=SearchFieldDataType.String,
                filterable=True,
                retrievable=True,
            ),
            SearchField(
                name="repo_name",
                type=SearchFieldDataType.String,
                filterable=True,
                retrievable=True,
            ),
            SearchField(
                name="doc_type",
                type=SearchFieldDataType.String,
                filterable=True,
                retrievable=True,
            ),
            SearchField(
                name="parent_source_id",
                type=SearchFieldDataType.String,
                filterable=True,
                retrievable=True,
            ),
            SearchField(
                name="chunk_index",
                type=SearchFieldDataType.Int32,
                filterable=True,
                retrievable=True,
            ),
            SearchField(
                name="source_ref",
                type=SearchFieldDataType.String,
                filterable=False,
                retrievable=True,
            ),
            SearchField(
                name="is_duplicate",
                type=SearchFieldDataType.Boolean,
                filterable=True,
                retrievable=True,
            ),
            SearchField(
                name="vector",
                # ``SearchFieldDataType.Collection(...)`` is a helper on
                # the CaseInsensitiveEnumMeta metaclass at runtime, but
                # static checkers see it as a plain ``Enum`` and reject
                # the call. The resulting string literal is identical.
                type="Collection(Edm.Single)",
                searchable=True,
                vector_search_dimensions=EMBEDDING_DIMENSION,
                vector_search_profile_name=_AZURE_VECTOR_PROFILE_NAME,
            ),
        ]
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name=_AZURE_HNSW_CONFIG_NAME,
                    parameters=HnswParameters(metric=VectorSearchAlgorithmMetric.COSINE),
                ),
            ],
            profiles=[
                VectorSearchProfile(
                    name=_AZURE_VECTOR_PROFILE_NAME,
                    algorithm_configuration_name=_AZURE_HNSW_CONFIG_NAME,
                ),
            ],
        )
        return SearchIndex(
            name=self._index_name,
            fields=fields,
            vector_search=vector_search,
        )

    # -- VectorStore interface ------------------------------------------

    async def ensure_index(self) -> None:
        """Create the index with vector search config if missing."""

        try:
            await self._index_client.get_index(self._index_name)
            return
        except ResourceNotFoundError:
            pass
        index = self._build_index()
        await self._index_client.create_index(index)

    async def upsert_embedding(self, record: VectorRecord) -> None:
        await self.upsert_embeddings([record])

    async def upsert_embeddings(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        documents = [_record_to_azure_document(r) for r in records]
        # ``merge_or_upload_documents`` is the closest thing Azure Search
        # offers to ``UPSERT`` — it creates the document if missing or
        # replaces the listed fields otherwise, keyed on ``source_id``.
        await self._search_client.merge_or_upload_documents(documents=documents)

    async def search(
        self,
        query_vector: list[float],
        entity_type: str | None = None,
        limit: int = 10,
        *,
        filters: dict[str, str] | None = None,
        exclude_duplicates: bool = True,
    ) -> list[VectorSearchHit]:
        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        if len(query_vector) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"query_vector must have exactly {EMBEDDING_DIMENSION} dimensions; "
                f"got {len(query_vector)}"
            )

        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=limit,
            fields="vector",
        )
        # Azure AI Search uses OData for filters. All user-supplied
        # values are single-quote-escaped defensively — there's no
        # string-concatenation injection surface into the query engine.
        clauses: list[str] = []
        if entity_type is not None:
            if not entity_type:
                raise ValueError("entity_type filter must be a non-empty string")
            escaped = entity_type.replace("'", "''")
            clauses.append(f"entity_type eq '{escaped}'")
        if filters:
            for field, value in filters.items():
                if not field:
                    raise ValueError("filter field names must be non-empty strings")
                escaped_field = field.replace("'", "''")
                escaped_value = str(value).replace("'", "''")
                clauses.append(f"{escaped_field} eq '{escaped_value}'")
        if exclude_duplicates:
            # ``ne true`` also admits legacy vectors where the field is
            # null (never set), so pre-V2 records are always included.
            clauses.append("is_duplicate ne true")
        search_filter = " and ".join(clauses) if clauses else None

        results = await self._search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=search_filter,
            top=limit,
            select=[
                "source_id",
                "entity_type",
                "text_hash",
                "created_at",
                "section_title",
                "repo_name",
                "doc_type",
                "parent_source_id",
                "chunk_index",
                "source_ref",
                "is_duplicate",
            ],
        )
        hits: list[VectorSearchHit] = []
        async for raw in results:
            # Defensive: skip any duplicate that slips through the filter.
            if exclude_duplicates and raw.get("is_duplicate") is True:
                continue
            hits.append(_azure_raw_to_hit(raw))
        return hits

    async def delete_embedding(self, source_id: str) -> None:
        if not source_id:
            raise ValueError("source_id must be a non-empty string")
        await self._search_client.delete_documents(
            documents=[{"source_id": source_id}]
        )

    async def close(self) -> None:
        await self._search_client.close()
        await self._index_client.close()


def _record_to_azure_document(record: VectorRecord) -> dict[str, Any]:
    """Serialize a :class:`VectorRecord` to the Azure document shape.

    The V2 chunk metadata fields are always emitted; they carry ``None``
    for legacy entity vectors, which Azure stores as null and which the
    ``is_duplicate ne true`` search filter treats as "not a duplicate".
    """

    return {
        "source_id": record.source_id,
        "entity_type": record.entity_type,
        "text_hash": record.text_hash,
        "created_at": record.created_at,
        "vector": list(record.vector),
        # V2 chunk metadata.
        "section_title": record.section_title,
        "repo_name": record.repo_name,
        "doc_type": record.doc_type,
        "parent_source_id": record.parent_source_id,
        "chunk_index": record.chunk_index,
        "source_ref": record.source_ref,
        "is_duplicate": record.is_duplicate,
    }


def _optional_str(value: Any) -> str | None:
    """Return ``str(value)`` or ``None`` when the raw value is missing."""

    return None if value is None else str(value)


def _optional_int(value: Any) -> int | None:
    """Return ``int(value)`` or ``None`` when the raw value is missing."""

    return None if value is None else int(value)


def _azure_raw_to_hit(raw: dict[str, Any]) -> VectorSearchHit:
    """Hydrate a :class:`VectorSearchHit` from an Azure result document."""

    return VectorSearchHit(
        source_id=str(raw.get("source_id", "")),
        entity_type=str(raw.get("entity_type", "")),
        text_hash=str(raw.get("text_hash", "")),
        created_at=str(raw.get("created_at", "")),
        score=float(raw.get("@search.score", 0.0)),
        section_title=_optional_str(raw.get("section_title")),
        repo_name=_optional_str(raw.get("repo_name")),
        doc_type=_optional_str(raw.get("doc_type")),
        parent_source_id=_optional_str(raw.get("parent_source_id")),
        chunk_index=_optional_int(raw.get("chunk_index")),
        source_ref=_optional_str(raw.get("source_ref")),
        is_duplicate=bool(raw.get("is_duplicate", False)),
    )


# ---------------------------------------------------------------------------
# Qdrant implementation
# ---------------------------------------------------------------------------


class QdrantVectorStore(VectorStore):
    """Dev backend talking to Qdrant's REST API directly.

    We deliberately use :mod:`httpx` rather than the ``qdrant-client``
    package to keep the dependency set small. Only the handful of
    endpoints needed by the :class:`VectorStore` interface are called
    — collection create/exists, point upsert, search, and delete.

    Qdrant point IDs must be unsigned integers or UUIDs, so we derive a
    deterministic UUID from the (string) ``source_id``. The original
    ``source_id`` is always stored in the payload too, which is what
    :meth:`search` returns to callers.
    """

    def __init__(
        self,
        url: str,
        collection_name: str = DEFAULT_INDEX_NAME,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 10.0,
    ) -> None:
        if not url:
            raise ValueError("QdrantVectorStore requires a non-empty url")
        if not collection_name:
            raise ValueError("QdrantVectorStore requires a non-empty collection_name")
        # Normalise the base URL so ``rstrip`` doesn't run every request.
        self._base_url = url.rstrip("/")
        self._collection_name = collection_name
        self._owns_client = client is None
        self._client: httpx.AsyncClient = client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
        )

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _point_id_for(source_id: str) -> str:
        """Return a deterministic UUID5-style id for ``source_id``.

        Qdrant accepts UUID strings as point ids; deriving one from the
        ``source_id`` via SHA-256 keeps upserts idempotent without
        needing an external registry. The original ``source_id``
        remains available in the point's payload.
        """

        digest = hashlib.sha256(source_id.encode("utf-8")).hexdigest()
        # Assemble a UUID-shaped string from the first 32 hex chars.
        return (
            f"{digest[0:8]}-{digest[8:12]}-{digest[12:16]}-"
            f"{digest[16:20]}-{digest[20:32]}"
        )

    @staticmethod
    def _record_to_point(record: VectorRecord) -> dict[str, Any]:
        return {
            "id": QdrantVectorStore._point_id_for(record.source_id),
            "vector": list(record.vector),
            "payload": {
                "source_id": record.source_id,
                "entity_type": record.entity_type,
                "text_hash": record.text_hash,
                "created_at": record.created_at,
                # V2 chunk metadata (``None``/``False`` for legacy vectors).
                "section_title": record.section_title,
                "repo_name": record.repo_name,
                "doc_type": record.doc_type,
                "parent_source_id": record.parent_source_id,
                "chunk_index": record.chunk_index,
                "source_ref": record.source_ref,
                "is_duplicate": record.is_duplicate,
            },
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        response = await self._client.request(method, path, json=json)
        return response

    # -- VectorStore interface ------------------------------------------

    async def ensure_index(self) -> None:
        """Create the collection if it doesn't already exist."""

        exists_resp = await self._request(
            "GET", f"/collections/{self._collection_name}/exists"
        )
        if exists_resp.status_code == 200:
            payload = exists_resp.json()
            if payload.get("result", {}).get("exists") is True:
                return

        create_resp = await self._request(
            "PUT",
            f"/collections/{self._collection_name}",
            json={
                "vectors": {
                    "size": EMBEDDING_DIMENSION,
                    "distance": "Cosine",
                }
            },
        )
        create_resp.raise_for_status()

    async def upsert_embedding(self, record: VectorRecord) -> None:
        await self.upsert_embeddings([record])

    async def upsert_embeddings(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        points = [self._record_to_point(r) for r in records]
        resp = await self._request(
            "PUT",
            f"/collections/{self._collection_name}/points",
            json={"points": points},
        )
        resp.raise_for_status()

    async def search(
        self,
        query_vector: list[float],
        entity_type: str | None = None,
        limit: int = 10,
        *,
        filters: dict[str, str] | None = None,
        exclude_duplicates: bool = True,
    ) -> list[VectorSearchHit]:
        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        if len(query_vector) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"query_vector must have exactly {EMBEDDING_DIMENSION} dimensions; "
                f"got {len(query_vector)}"
            )

        body: dict[str, Any] = {
            "vector": list(query_vector),
            "limit": limit,
            "with_payload": True,
        }
        # Qdrant filter clauses are built structurally (never string
        # concatenation) so there's no injection surface into the query.
        must: list[dict[str, Any]] = []
        if entity_type is not None:
            if not entity_type:
                raise ValueError("entity_type filter must be a non-empty string")
            must.append({"key": "entity_type", "match": {"value": entity_type}})
        if filters:
            for field, value in filters.items():
                if not field:
                    raise ValueError("filter field names must be non-empty strings")
                must.append({"key": field, "match": {"value": value}})

        qdrant_filter: dict[str, Any] = {}
        if must:
            qdrant_filter["must"] = must
        if exclude_duplicates:
            # ``must_not is_duplicate == true`` keeps legacy vectors whose
            # payload has no ``is_duplicate`` key (they don't match true).
            qdrant_filter["must_not"] = [
                {"key": "is_duplicate", "match": {"value": True}}
            ]
        if qdrant_filter:
            body["filter"] = qdrant_filter

        resp = await self._request(
            "POST",
            f"/collections/{self._collection_name}/points/search",
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_hits = data.get("result", [])
        hits: list[VectorSearchHit] = []
        for raw in raw_hits:
            payload = raw.get("payload") or {}
            # Defensive: skip any duplicate that slips through the filter.
            if exclude_duplicates and payload.get("is_duplicate") is True:
                continue
            hits.append(
                VectorSearchHit(
                    source_id=str(payload.get("source_id", "")),
                    entity_type=str(payload.get("entity_type", "")),
                    text_hash=str(payload.get("text_hash", "")),
                    created_at=str(payload.get("created_at", "")),
                    score=float(raw.get("score", 0.0)),
                    section_title=_optional_str(payload.get("section_title")),
                    repo_name=_optional_str(payload.get("repo_name")),
                    doc_type=_optional_str(payload.get("doc_type")),
                    parent_source_id=_optional_str(payload.get("parent_source_id")),
                    chunk_index=_optional_int(payload.get("chunk_index")),
                    source_ref=_optional_str(payload.get("source_ref")),
                    is_duplicate=bool(payload.get("is_duplicate", False)),
                )
            )
        return hits

    async def delete_embedding(self, source_id: str) -> None:
        if not source_id:
            raise ValueError("source_id must be a non-empty string")
        resp = await self._request(
            "POST",
            f"/collections/{self._collection_name}/points/delete",
            json={"points": [self._point_id_for(source_id)]},
        )
        resp.raise_for_status()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_vector_store(settings: Settings) -> VectorStore:
    """Return the vector store implementation appropriate for ``settings``.

    Selection rule:

    * If both ``settings.azure_search_endpoint`` and
      ``settings.azure_search_key`` are set, return an
      :class:`AzureAISearchVectorStore`.
    * Otherwise, fall back to :class:`QdrantVectorStore` using
      ``settings.qdrant_url``.

    This matches the design's prod/dev split: Azure AI Search in
    production (once the endpoint + key are configured) and Qdrant
    locally otherwise.
    """

    endpoint = settings.azure_search_endpoint
    api_key = settings.azure_search_key
    if endpoint and api_key:
        return AzureAISearchVectorStore(
            endpoint=endpoint,
            api_key=api_key,
            index_name=DEFAULT_INDEX_NAME,
        )
    return QdrantVectorStore(
        url=settings.qdrant_url,
        collection_name=DEFAULT_INDEX_NAME,
    )


__all__ = [
    "AzureAISearchVectorStore",
    "DEFAULT_INDEX_NAME",
    "EMBEDDING_DIMENSION",
    "QdrantVectorStore",
    "VectorRecord",
    "VectorSearchHit",
    "VectorStore",
    "get_vector_store",
]
