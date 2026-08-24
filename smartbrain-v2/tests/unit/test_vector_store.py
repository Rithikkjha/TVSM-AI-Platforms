"""Unit tests for :mod:`src.models.vector_store`.

The tests exercise the public interface of every concrete backend
without touching a real Azure AI Search instance or a real Qdrant
server:

* The Azure backend is tested by injecting stub ``SearchClient`` /
  ``SearchIndexClient`` instances.
* The Qdrant backend is tested by wiring an :class:`httpx.AsyncClient`
  onto an :class:`httpx.MockTransport` that asserts on the request
  shape and returns canned JSON responses.
* :class:`VectorRecord` validation is tested directly.
* The :func:`get_vector_store` factory is tested for both branches.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from config.settings import Settings
from storage.vector.vector_store import (
    DEFAULT_INDEX_NAME,
    EMBEDDING_DIMENSION,
    AzureAISearchVectorStore,
    QdrantVectorStore,
    VectorRecord,
    VectorSearchHit,
    get_vector_store,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_vector(fill: float = 0.0) -> list[float]:
    """Return a 3072-long list suitable for :class:`VectorRecord`."""

    return [fill] * EMBEDDING_DIMENSION


def _make_record(source_id: str = "svc-1", entity_type: str = "Service") -> VectorRecord:
    return VectorRecord(
        source_id=source_id,
        entity_type=entity_type,
        text_hash="abc123",
        vector=_make_vector(0.1),
        created_at="2024-01-01T00:00:00Z",
    )


class _AsyncListIterator:
    """Minimal async iterator wrapping a list of dicts.

    Mimics what the real Azure ``AsyncSearchItemPaged`` yields: plain
    dict-like rows that the store reads from via ``row.get(...)``.
    """

    def __init__(self, items: list[dict[str, Any]]) -> None:
        self._items = items

    def __aiter__(self) -> _AsyncListIterator:
        return self

    async def __anext__(self) -> dict[str, Any]:
        if not self._items:
            raise StopAsyncIteration
        return self._items.pop(0)


# ---------------------------------------------------------------------------
# VectorRecord validation
# ---------------------------------------------------------------------------


class TestVectorRecord:
    def test_accepts_valid_payload(self) -> None:
        rec = _make_record()
        assert rec.source_id == "svc-1"
        assert rec.entity_type == "Service"
        assert len(rec.vector) == EMBEDDING_DIMENSION

    def test_rejects_wrong_vector_dimension(self) -> None:
        with pytest.raises(ValueError, match="3072"):
            VectorRecord(
                source_id="s",
                entity_type="Service",
                text_hash="h",
                vector=[0.0] * 100,
                created_at="t",
            )

    @pytest.mark.parametrize(
        "field",
        ["source_id", "entity_type", "text_hash", "created_at"],
    )
    def test_rejects_empty_required_fields(self, field: str) -> None:
        kwargs: dict[str, Any] = {
            "source_id": "s",
            "entity_type": "Service",
            "text_hash": "h",
            "vector": _make_vector(),
            "created_at": "t",
        }
        kwargs[field] = ""
        with pytest.raises(ValueError, match=field):
            VectorRecord(**kwargs)

    def test_frozen(self) -> None:
        """``VectorRecord`` is immutable (catch accidental mutation)."""

        rec = _make_record()
        with pytest.raises((AttributeError, TypeError)):
            rec.source_id = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestGetVectorStore:
    def test_returns_azure_when_endpoint_and_key_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Avoid constructing the real Azure SDK clients (which would
        # require aiohttp and attempt DNS) by patching them at the
        # module level.
        monkeypatch.setattr(
            "src.models.vector_store.SearchClient",
            MagicMock(return_value=MagicMock()),
        )
        monkeypatch.setattr(
            "src.models.vector_store.SearchIndexClient",
            MagicMock(return_value=MagicMock()),
        )

        settings = Settings(
            azure_search_endpoint="https://search.example.net",
            azure_search_key="top-secret",
            qdrant_url="http://qdrant:6333",
        )
        store = get_vector_store(settings)
        assert isinstance(store, AzureAISearchVectorStore)
        assert store._index_name == DEFAULT_INDEX_NAME

    def test_returns_qdrant_when_endpoint_missing(self) -> None:
        settings = Settings(
            azure_search_endpoint=None,
            azure_search_key=None,
            qdrant_url="http://qdrant.local:6333",
        )
        store = get_vector_store(settings)
        assert isinstance(store, QdrantVectorStore)
        assert store._collection_name == DEFAULT_INDEX_NAME
        assert store._base_url == "http://qdrant.local:6333"

    def test_returns_qdrant_when_only_endpoint_set(self) -> None:
        """Both endpoint AND key are required to pick Azure."""

        settings = Settings(
            azure_search_endpoint="https://search.example.net",
            azure_search_key=None,
            qdrant_url="http://qdrant:6333",
        )
        store = get_vector_store(settings)
        assert isinstance(store, QdrantVectorStore)


# ---------------------------------------------------------------------------
# Azure AI Search backend
# ---------------------------------------------------------------------------


def _make_azure_store(
    search_client: Any | None = None,
    index_client: Any | None = None,
) -> tuple[AzureAISearchVectorStore, Any, Any]:
    """Build an Azure-backed store with mocked SDK clients."""

    sc = search_client or MagicMock()
    sc.merge_or_upload_documents = AsyncMock()
    sc.delete_documents = AsyncMock()
    # Azure's SearchClient.search is async and resolves to an async
    # iterable of result rows, so we use AsyncMock whose return_value
    # gets set per-test via ``sc.search.return_value = <async iterable>``.
    sc.search = AsyncMock()
    sc.close = AsyncMock()

    ic = index_client or MagicMock()
    ic.get_index = AsyncMock()
    ic.create_index = AsyncMock()
    ic.close = AsyncMock()

    store = AzureAISearchVectorStore(
        endpoint="https://search.example.net",
        api_key="k",
        index_name="test-index",
        search_client=sc,
        index_client=ic,
    )
    return store, sc, ic


class TestAzureAISearchVectorStore:
    def test_validates_constructor_args(self) -> None:
        with pytest.raises(ValueError, match="endpoint"):
            AzureAISearchVectorStore(endpoint="", api_key="k")
        with pytest.raises(ValueError, match="api_key"):
            AzureAISearchVectorStore(endpoint="https://x", api_key="")

    def test_build_index_shape(self) -> None:
        store, _, _ = _make_azure_store()
        index = store._build_index()

        assert index.name == "test-index"
        assert index.vector_search is not None
        field_names = {f.name for f in index.fields}
        assert field_names == {
            "source_id",
            "entity_type",
            "text_hash",
            "vector",
            "created_at",
        }
        key_field = next(f for f in index.fields if f.name == "source_id")
        assert key_field.key is True
        vector_field = next(f for f in index.fields if f.name == "vector")
        assert vector_field.vector_search_dimensions == EMBEDDING_DIMENSION

    @pytest.mark.asyncio
    async def test_ensure_index_skips_when_present(self) -> None:
        store, _, ic = _make_azure_store()
        ic.get_index.return_value = MagicMock(name="existing-index")

        await store.ensure_index()

        ic.get_index.assert_awaited_once_with("test-index")
        ic.create_index.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ensure_index_creates_when_missing(self) -> None:
        from azure.core.exceptions import ResourceNotFoundError

        store, _, ic = _make_azure_store()
        ic.get_index.side_effect = ResourceNotFoundError("no such index")

        await store.ensure_index()

        ic.create_index.assert_awaited_once()
        (sent_index,), _kwargs = ic.create_index.call_args
        assert sent_index.name == "test-index"

    @pytest.mark.asyncio
    async def test_upsert_embedding_calls_merge_or_upload(self) -> None:
        store, sc, _ = _make_azure_store()
        rec = _make_record()

        await store.upsert_embedding(rec)

        sc.merge_or_upload_documents.assert_awaited_once()
        _args, kwargs = sc.merge_or_upload_documents.call_args
        documents = kwargs["documents"]
        assert len(documents) == 1
        doc = documents[0]
        assert doc["source_id"] == rec.source_id
        assert doc["entity_type"] == rec.entity_type
        assert doc["text_hash"] == rec.text_hash
        assert doc["created_at"] == rec.created_at
        assert doc["vector"] == rec.vector

    @pytest.mark.asyncio
    async def test_upsert_embeddings_empty_is_noop(self) -> None:
        store, sc, _ = _make_azure_store()
        await store.upsert_embeddings([])
        sc.merge_or_upload_documents.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_search_issues_vector_query_with_filter(self) -> None:
        store, sc, _ = _make_azure_store()
        sc.search.return_value = _AsyncListIterator(
            [
                {
                    "source_id": "svc-1",
                    "entity_type": "Service",
                    "text_hash": "h1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "@search.score": 0.95,
                },
            ]
        )
        query_vec = _make_vector(0.2)

        hits = await store.search(query_vec, entity_type="Service", limit=5)

        assert hits == [
            VectorSearchHit(
                source_id="svc-1",
                entity_type="Service",
                text_hash="h1",
                created_at="2024-01-01T00:00:00Z",
                score=0.95,
            )
        ]
        _args, kwargs = sc.search.call_args
        assert kwargs["search_text"] is None
        assert kwargs["top"] == 5
        assert kwargs["filter"] == "entity_type eq 'Service'"
        vector_queries = kwargs["vector_queries"]
        assert len(vector_queries) == 1
        assert vector_queries[0].vector == query_vec
        assert vector_queries[0].k_nearest_neighbors == 5

    @pytest.mark.asyncio
    async def test_search_without_entity_type_filter(self) -> None:
        store, sc, _ = _make_azure_store()
        sc.search.return_value = _AsyncListIterator([])
        await store.search(_make_vector(), limit=3)
        _args, kwargs = sc.search.call_args
        assert kwargs["filter"] is None

    @pytest.mark.asyncio
    async def test_search_rejects_bad_dimension(self) -> None:
        store, _, _ = _make_azure_store()
        with pytest.raises(ValueError, match="3072"):
            await store.search([0.0] * 10)

    @pytest.mark.asyncio
    async def test_search_rejects_nonpositive_limit(self) -> None:
        store, _, _ = _make_azure_store()
        with pytest.raises(ValueError, match="positive"):
            await store.search(_make_vector(), limit=0)

    @pytest.mark.asyncio
    async def test_delete_embedding(self) -> None:
        store, sc, _ = _make_azure_store()

        await store.delete_embedding("svc-1")

        sc.delete_documents.assert_awaited_once()
        _args, kwargs = sc.delete_documents.call_args
        assert kwargs["documents"] == [{"source_id": "svc-1"}]

    @pytest.mark.asyncio
    async def test_delete_embedding_rejects_empty(self) -> None:
        store, _, _ = _make_azure_store()
        with pytest.raises(ValueError, match="source_id"):
            await store.delete_embedding("")

    @pytest.mark.asyncio
    async def test_close_closes_both_clients(self) -> None:
        store, sc, ic = _make_azure_store()
        await store.close()
        sc.close.assert_awaited_once()
        ic.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_search_escapes_single_quotes_in_filter(self) -> None:
        store, sc, _ = _make_azure_store()
        sc.search.return_value = _AsyncListIterator([])
        await store.search(_make_vector(), entity_type="Odd'Type")
        _args, kwargs = sc.search.call_args
        assert kwargs["filter"] == "entity_type eq 'Odd''Type'"


# ---------------------------------------------------------------------------
# Qdrant backend
# ---------------------------------------------------------------------------


class _QdrantRecorder:
    """Collects HTTP requests made via :class:`httpx.MockTransport`.

    Each ``record`` tuple is ``(method, path, body)``, making tests
    straightforward to write with direct structural assertions rather
    than inspecting raw ``httpx.Request`` objects.
    """

    def __init__(self, responder: Any) -> None:
        self._responder = responder
        self.records: list[tuple[str, str, dict[str, Any] | None]] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        body: dict[str, Any] | None = None
        if request.content:
            try:
                body = json.loads(request.content.decode("utf-8"))
            except json.JSONDecodeError:
                body = None
        self.records.append((request.method, request.url.path, body))
        return self._responder(request, body)


def _make_qdrant_store(
    responder: Any,
) -> tuple[QdrantVectorStore, _QdrantRecorder]:
    """Build a Qdrant store whose ``httpx.AsyncClient`` talks to a mock.

    The ``responder(request, body)`` callable returns an
    :class:`httpx.Response` per call, so tests control responses per
    endpoint.
    """

    recorder = _QdrantRecorder(responder)
    transport = httpx.MockTransport(recorder.handler)
    client = httpx.AsyncClient(
        base_url="http://qdrant.test",
        transport=transport,
    )
    store = QdrantVectorStore(
        url="http://qdrant.test",
        collection_name="test-collection",
        client=client,
    )
    return store, recorder


class TestQdrantVectorStore:
    def test_validates_constructor_args(self) -> None:
        with pytest.raises(ValueError, match="url"):
            QdrantVectorStore(url="")
        with pytest.raises(ValueError, match="collection_name"):
            QdrantVectorStore(url="http://x", collection_name="")

    def test_point_id_deterministic(self) -> None:
        a = QdrantVectorStore._point_id_for("github:repo:abc")
        b = QdrantVectorStore._point_id_for("github:repo:abc")
        c = QdrantVectorStore._point_id_for("github:repo:xyz")
        assert a == b
        assert a != c
        # UUID-shaped: 5 groups separated by hyphens
        assert a.count("-") == 4

    @pytest.mark.asyncio
    async def test_ensure_index_skips_when_exists(self) -> None:
        def responder(request: httpx.Request, body: Any) -> httpx.Response:
            if request.method == "GET" and request.url.path.endswith("/exists"):
                return httpx.Response(
                    200, json={"result": {"exists": True}, "status": "ok"}
                )
            raise AssertionError(f"Unexpected request: {request.method} {request.url.path}")

        store, recorder = _make_qdrant_store(responder)
        try:
            await store.ensure_index()
        finally:
            await store.close()

        methods = [r[0] for r in recorder.records]
        paths = [r[1] for r in recorder.records]
        assert methods == ["GET"]
        assert paths == ["/collections/test-collection/exists"]

    @pytest.mark.asyncio
    async def test_ensure_index_creates_when_missing(self) -> None:
        def responder(request: httpx.Request, body: Any) -> httpx.Response:
            if request.method == "GET" and request.url.path.endswith("/exists"):
                return httpx.Response(
                    200, json={"result": {"exists": False}, "status": "ok"}
                )
            if request.method == "PUT":
                return httpx.Response(200, json={"result": True, "status": "ok"})
            raise AssertionError("Unexpected request")

        store, recorder = _make_qdrant_store(responder)
        try:
            await store.ensure_index()
        finally:
            await store.close()

        assert len(recorder.records) == 2
        _, create_path, create_body = recorder.records[1]
        assert create_path == "/collections/test-collection"
        assert create_body == {
            "vectors": {
                "size": EMBEDDING_DIMENSION,
                "distance": "Cosine",
            }
        }

    @pytest.mark.asyncio
    async def test_upsert_embedding_sends_expected_point(self) -> None:
        def responder(request: httpx.Request, body: Any) -> httpx.Response:
            return httpx.Response(200, json={"result": {}, "status": "ok"})

        store, recorder = _make_qdrant_store(responder)
        try:
            rec = _make_record(source_id="github:repo:42")
            await store.upsert_embedding(rec)
        finally:
            await store.close()

        assert len(recorder.records) == 1
        method, path, body = recorder.records[0]
        assert method == "PUT"
        assert path == "/collections/test-collection/points"
        assert body is not None
        points = body["points"]
        assert len(points) == 1
        point = points[0]
        assert point["id"] == QdrantVectorStore._point_id_for("github:repo:42")
        assert point["vector"] == rec.vector
        assert point["payload"] == {
            "source_id": "github:repo:42",
            "entity_type": "Service",
            "text_hash": "abc123",
            "created_at": "2024-01-01T00:00:00Z",
        }

    @pytest.mark.asyncio
    async def test_upsert_embeddings_empty_is_noop(self) -> None:
        def responder(request: httpx.Request, body: Any) -> httpx.Response:
            raise AssertionError("Should not be called")

        store, recorder = _make_qdrant_store(responder)
        try:
            await store.upsert_embeddings([])
        finally:
            await store.close()
        assert recorder.records == []

    @pytest.mark.asyncio
    async def test_search_sends_filter_and_parses_hits(self) -> None:
        def responder(request: httpx.Request, body: Any) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "result": [
                        {
                            "id": "doesnt-matter",
                            "score": 0.87,
                            "payload": {
                                "source_id": "svc-1",
                                "entity_type": "Service",
                                "text_hash": "h1",
                                "created_at": "2024-01-01T00:00:00Z",
                            },
                        }
                    ],
                    "status": "ok",
                },
            )

        store, recorder = _make_qdrant_store(responder)
        try:
            query_vec = _make_vector(0.3)
            hits = await store.search(query_vec, entity_type="Service", limit=5)
        finally:
            await store.close()

        assert hits == [
            VectorSearchHit(
                source_id="svc-1",
                entity_type="Service",
                text_hash="h1",
                created_at="2024-01-01T00:00:00Z",
                score=0.87,
            )
        ]
        method, path, body = recorder.records[0]
        assert method == "POST"
        assert path == "/collections/test-collection/points/search"
        assert body is not None
        assert body["vector"] == query_vec
        assert body["limit"] == 5
        assert body["with_payload"] is True
        assert body["filter"] == {
            "must": [{"key": "entity_type", "match": {"value": "Service"}}]
        }

    @pytest.mark.asyncio
    async def test_search_without_filter(self) -> None:
        def responder(request: httpx.Request, body: Any) -> httpx.Response:
            return httpx.Response(200, json={"result": [], "status": "ok"})

        store, recorder = _make_qdrant_store(responder)
        try:
            await store.search(_make_vector(), limit=3)
        finally:
            await store.close()
        _method, _path, body = recorder.records[0]
        assert body is not None
        assert "filter" not in body

    @pytest.mark.asyncio
    async def test_search_rejects_bad_dimension(self) -> None:
        def responder(request: httpx.Request, body: Any) -> httpx.Response:
            raise AssertionError("Should not be called")

        store, _ = _make_qdrant_store(responder)
        try:
            with pytest.raises(ValueError, match="3072"):
                await store.search([0.0] * 5)
        finally:
            await store.close()

    @pytest.mark.asyncio
    async def test_delete_embedding_sends_point_id(self) -> None:
        def responder(request: httpx.Request, body: Any) -> httpx.Response:
            return httpx.Response(200, json={"result": {}, "status": "ok"})

        store, recorder = _make_qdrant_store(responder)
        try:
            await store.delete_embedding("github:repo:42")
        finally:
            await store.close()

        method, path, body = recorder.records[0]
        assert method == "POST"
        assert path == "/collections/test-collection/points/delete"
        assert body == {
            "points": [QdrantVectorStore._point_id_for("github:repo:42")],
        }

    @pytest.mark.asyncio
    async def test_delete_embedding_rejects_empty(self) -> None:
        def responder(request: httpx.Request, body: Any) -> httpx.Response:
            raise AssertionError("Should not be called")

        store, _ = _make_qdrant_store(responder)
        try:
            with pytest.raises(ValueError, match="source_id"):
                await store.delete_embedding("")
        finally:
            await store.close()

    @pytest.mark.asyncio
    async def test_upsert_raises_on_http_error(self) -> None:
        """Transport errors surface as ``httpx.HTTPStatusError``."""

        def responder(request: httpx.Request, body: Any) -> httpx.Response:
            return httpx.Response(500, json={"status": {"error": "boom"}})

        store, _ = _make_qdrant_store(responder)
        try:
            with pytest.raises(httpx.HTTPStatusError):
                await store.upsert_embedding(_make_record())
        finally:
            await store.close()
