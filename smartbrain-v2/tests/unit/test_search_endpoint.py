"""Unit tests for GET /v1/search endpoint.

Tests cover:
- Search with valid query → 200 with results
- Search with type filter
- Search with custom limit
- Empty query → 400
- Limit > 50 capped at 50
- Embedding failure → 200 with empty results + logged warning
- API key required (401 without)

EmbeddingService and VectorStore are mocked since we don't have real
infrastructure in unit tests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from config.settings import Settings, get_settings
from processing.embeddings.service import EmbeddingError
from storage.vector.vector_store import VectorSearchHit
from api.app import app

# Use a known API key for testing
TEST_API_KEY = "test-secret-key-search"


@pytest.fixture(autouse=True)
def _override_settings() -> None:  # type: ignore[misc]
    """Override settings to use a known API key."""
    get_settings.cache_clear()
    with patch(
        "src.query.app.get_settings",
        return_value=Settings(api_key=TEST_API_KEY),
    ), patch(
        "src.query.search.get_settings",
        return_value=Settings(api_key=TEST_API_KEY),
    ):
        yield
    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    """Create a TestClient for the FastAPI app."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Return headers with a valid API key."""
    return {"X-API-Key": TEST_API_KEY}


# ---------------------------------------------------------------------------
# Sample data for mocking
# ---------------------------------------------------------------------------

SAMPLE_VECTOR = [0.1] * 3072

SAMPLE_HITS = [
    VectorSearchHit(
        source_id="confluence:page:456",
        entity_type="ConfluencePage",
        text_hash="abc123",
        created_at="2024-01-01T00:00:00Z",
        score=0.92,
    ),
    VectorSearchHit(
        source_id="github:repo:payments-service",
        entity_type="Service",
        text_hash="def456",
        created_at="2024-01-02T00:00:00Z",
        score=0.87,
    ),
]


# ---------------------------------------------------------------------------
# Helper to mock embedding service and vector store
# ---------------------------------------------------------------------------


def _mock_search_dependencies(
    embedding_result: list[float] | None = None,
    embedding_error: Exception | None = None,
    search_results: list[VectorSearchHit] | None = None,
):
    """Return patch context managers for embedding service and vector store."""
    # Build embedding service mock
    embedding_svc = AsyncMock()
    if embedding_error:
        embedding_svc.generate_embedding = AsyncMock(side_effect=embedding_error)
    else:
        embedding_svc.generate_embedding = AsyncMock(
            return_value=embedding_result or SAMPLE_VECTOR
        )
    embedding_svc.close = AsyncMock()

    # Build vector store mock
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=search_results or [])
    vector_store.close = AsyncMock()

    return (
        patch("src.query.search._get_embedding_service", return_value=embedding_svc),
        patch("src.query.search._get_vector_store", return_value=vector_store),
    )


# ---------------------------------------------------------------------------
# Tests: API key authentication
# ---------------------------------------------------------------------------


class TestSearchEndpointAuth:
    """Tests for API key requirement on the search endpoint."""

    def test_returns_401_without_api_key(self, client: TestClient) -> None:
        """Should reject requests without an API key."""
        response = client.get("/v1/search?q=test")
        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["error"] == "unauthorized"

    def test_returns_401_with_wrong_api_key(self, client: TestClient) -> None:
        """Should reject requests with an incorrect API key."""
        response = client.get(
            "/v1/search?q=test",
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Tests: Valid search (200)
# ---------------------------------------------------------------------------


class TestSearchValid:
    """Tests for successful search queries."""

    def test_search_with_valid_query_returns_200(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 200 with results for a valid query."""
        patches = _mock_search_dependencies(
            embedding_result=SAMPLE_VECTOR,
            search_results=SAMPLE_HITS,
        )
        with patches[0], patches[1]:
            response = client.get("/v1/search?q=payment+retry+logic", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["query"] == "payment retry logic"
        assert body["total"] == 2
        assert len(body["results"]) == 2

        # Check first result
        assert body["results"][0]["source_id"] == "confluence:page:456"
        assert body["results"][0]["entity_type"] == "ConfluencePage"
        assert body["results"][0]["score"] == 0.92

        # Check second result
        assert body["results"][1]["source_id"] == "github:repo:payments-service"
        assert body["results"][1]["entity_type"] == "Service"
        assert body["results"][1]["score"] == 0.87

    def test_search_with_type_filter(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should pass entity_type filter to vector store search."""
        embedding_svc = AsyncMock()
        embedding_svc.generate_embedding = AsyncMock(return_value=SAMPLE_VECTOR)
        embedding_svc.close = AsyncMock()

        vector_store = AsyncMock()
        vector_store.search = AsyncMock(return_value=[SAMPLE_HITS[1]])
        vector_store.close = AsyncMock()

        with patch("src.query.search._get_embedding_service", return_value=embedding_svc), \
             patch("src.query.search._get_vector_store", return_value=vector_store):
            response = client.get(
                "/v1/search?q=payments&type=Service", headers=auth_headers
            )

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["results"][0]["entity_type"] == "Service"

        # Verify the type filter was passed to vector store
        vector_store.search.assert_called_once_with(
            query_vector=SAMPLE_VECTOR,
            entity_type="Service",
            limit=10,
        )

    def test_search_with_custom_limit(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should pass custom limit to vector store search."""
        embedding_svc = AsyncMock()
        embedding_svc.generate_embedding = AsyncMock(return_value=SAMPLE_VECTOR)
        embedding_svc.close = AsyncMock()

        vector_store = AsyncMock()
        vector_store.search = AsyncMock(return_value=[])
        vector_store.close = AsyncMock()

        with patch("src.query.search._get_embedding_service", return_value=embedding_svc), \
             patch("src.query.search._get_vector_store", return_value=vector_store):
            response = client.get(
                "/v1/search?q=test&limit=25", headers=auth_headers
            )

        assert response.status_code == 200

        # Verify the limit was passed to vector store
        vector_store.search.assert_called_once_with(
            query_vector=SAMPLE_VECTOR,
            entity_type=None,
            limit=25,
        )

    def test_search_limit_capped_at_50(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should cap limit at 50 even if a higher value is requested."""
        embedding_svc = AsyncMock()
        embedding_svc.generate_embedding = AsyncMock(return_value=SAMPLE_VECTOR)
        embedding_svc.close = AsyncMock()

        vector_store = AsyncMock()
        vector_store.search = AsyncMock(return_value=[])
        vector_store.close = AsyncMock()

        with patch("src.query.search._get_embedding_service", return_value=embedding_svc), \
             patch("src.query.search._get_vector_store", return_value=vector_store):
            response = client.get(
                "/v1/search?q=test&limit=100", headers=auth_headers
            )

        assert response.status_code == 200

        # Verify the limit was capped at 50
        vector_store.search.assert_called_once_with(
            query_vector=SAMPLE_VECTOR,
            entity_type=None,
            limit=50,
        )


# ---------------------------------------------------------------------------
# Tests: Empty query (400)
# ---------------------------------------------------------------------------


class TestSearchEmptyQuery:
    """Tests for empty query validation."""

    def test_empty_query_returns_400(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 400 when query is empty string."""
        response = client.get("/v1/search?q=", headers=auth_headers)
        assert response.status_code == 400
        body = response.json()
        assert body["error"] == "bad_request"
        assert "q" in body["message"].lower() or "query" in body["message"].lower()

    def test_whitespace_only_query_returns_400(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 400 when query is only whitespace."""
        response = client.get("/v1/search?q=   ", headers=auth_headers)
        assert response.status_code == 400
        body = response.json()
        assert body["error"] == "bad_request"


# ---------------------------------------------------------------------------
# Tests: Embedding failure (graceful degradation)
# ---------------------------------------------------------------------------


class TestSearchEmbeddingFailure:
    """Tests for graceful handling of embedding failures."""

    def test_embedding_failure_returns_200_with_empty_results(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 200 with empty results when embedding fails."""
        patches = _mock_search_dependencies(
            embedding_error=EmbeddingError("Azure OpenAI rate limit exceeded"),
        )
        with patches[0], patches[1]:
            response = client.get("/v1/search?q=test+query", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["query"] == "test query"
        assert body["results"] == []
        assert body["total"] == 0

    def test_embedding_failure_logs_warning(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should log a warning when embedding generation fails."""
        patches = _mock_search_dependencies(
            embedding_error=EmbeddingError("API error"),
        )
        with patches[0], patches[1], patch("src.query.search.logger") as mock_logger:
            response = client.get("/v1/search?q=test+query", headers=auth_headers)

        assert response.status_code == 200
        mock_logger.warning.assert_called_once()
        warning_args = mock_logger.warning.call_args[0]
        assert "test query" in warning_args[1]
