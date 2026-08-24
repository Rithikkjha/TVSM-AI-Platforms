"""Unit tests for POST /v1/ask endpoint (GraphRAG pipeline).

Tests cover:
- Valid question → 200 with answer and citations
- Empty question → 400
- No vector results → 200 with null answer and "insufficient context" message
- Embedding failure → 503
- LLM failure → 503 with fallback
- Citations extracted from LLM response
- Context assembly respects token budget
- API key required (401 without)

EmbeddingService, VectorStore, Neo4j driver, and OpenAI chat completion
are mocked since we don't have real infrastructure in unit tests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from config.settings import Settings, get_settings
from processing.embeddings.service import EmbeddingError
from storage.vector.vector_store import VectorSearchHit
from api.app import app
from retrieval.search.ask_pipeline import _assemble_context, _extract_citations

# Use a known API key for testing
TEST_API_KEY = "test-secret-key-ask"


@pytest.fixture(autouse=True)
def _override_settings():  # type: ignore[misc]
    """Override settings to use a known API key."""
    get_settings.cache_clear()
    with patch(
        "src.query.app.get_settings",
        return_value=Settings(api_key=TEST_API_KEY),
    ), patch(
        "src.query.ask.get_settings",
        return_value=Settings(
            api_key=TEST_API_KEY,
            azure_openai_endpoint="https://test.openai.azure.com",
            azure_openai_key="test-key",
            vector_search_top_k=10,
            graph_expansion_hops=2,
            llm_context_token_budget=8000,
        ),
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
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_VECTOR = [0.1] * 3072

SAMPLE_HITS = [
    VectorSearchHit(
        source_id="github:repo:payments-service",
        entity_type="Service",
        text_hash="abc123",
        created_at="2024-01-01T00:00:00Z",
        score=0.92,
    ),
    VectorSearchHit(
        source_id="jira:ticket:ENG-1234",
        entity_type="Ticket",
        text_hash="def456",
        created_at="2024-01-02T00:00:00Z",
        score=0.85,
    ),
]

SAMPLE_ENTITY_SERVICE = {
    "source_id": "github:repo:payments-service",
    "name": "payments-service",
    "description": "Handles payment processing and billing",
    "updated_at": "2024-12-01T10:00:00Z",
}

SAMPLE_ENTITY_TICKET = {
    "source_id": "jira:ticket:ENG-1234",
    "key": "ENG-1234",
    "title": "Fix timeout on payment retry",
    "status": "In Progress",
    "priority": "High",
    "updated_at": "2024-12-01T10:00:00Z",
}

SAMPLE_NEIGHBOR = {
    "source_id": "jira:team:payments",
    "name": "Payments Team",
    "updated_at": "2024-11-01T10:00:00Z",
}

LLM_ANSWER_WITH_CITATIONS = (
    "The payments-service (github:repo:payments-service) handles payment processing. "
    "There is an open ticket ENG-1234 (jira:ticket:ENG-1234) about fixing timeout on payment retry."
)


# ---------------------------------------------------------------------------
# Tests: API key authentication
# ---------------------------------------------------------------------------


class TestAskEndpointAuth:
    """Tests for API key requirement on the ask endpoint."""

    def test_returns_401_without_api_key(self, client: TestClient) -> None:
        """Should reject requests without an API key."""
        response = client.post("/v1/ask", json={"question": "test"})
        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["error"] == "unauthorized"

    def test_returns_401_with_wrong_api_key(self, client: TestClient) -> None:
        """Should reject requests with an incorrect API key."""
        response = client.post(
            "/v1/ask",
            json={"question": "test"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Tests: Empty question (400)
# ---------------------------------------------------------------------------


class TestAskEmptyQuestion:
    """Tests for empty question validation."""

    def test_empty_question_returns_400(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 400 when question is empty string."""
        response = client.post("/v1/ask", json={"question": ""}, headers=auth_headers)
        assert response.status_code == 400
        body = response.json()
        assert body["error"] == "bad_request"

    def test_whitespace_only_question_returns_400(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 400 when question is only whitespace."""
        response = client.post("/v1/ask", json={"question": "   "}, headers=auth_headers)
        assert response.status_code == 400
        body = response.json()
        assert body["error"] == "bad_request"


# ---------------------------------------------------------------------------
# Tests: No vector results (insufficient context)
# ---------------------------------------------------------------------------


class TestAskNoVectorResults:
    """Tests for insufficient context when vector search returns no results."""

    def test_no_vector_results_returns_200_with_null_answer(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 200 with null answer and message when no vector results."""
        embedding_svc = AsyncMock()
        embedding_svc.generate_embedding = AsyncMock(return_value=SAMPLE_VECTOR)
        embedding_svc.close = AsyncMock()

        vector_store = AsyncMock()
        vector_store.search = AsyncMock(return_value=[])
        vector_store.close = AsyncMock()

        with patch("src.query.ask._get_embedding_service", return_value=embedding_svc), \
             patch("src.query.ask._get_vector_store", return_value=vector_store):
            response = client.post(
                "/v1/ask",
                json={"question": "What is the meaning of life?"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        body = response.json()
        assert body["answer"] is None
        assert body["message"] is not None
        assert "enough information" in body["message"].lower() or "don't have" in body["message"].lower()
        assert body["citations"] == []


# ---------------------------------------------------------------------------
# Tests: Embedding failure (503)
# ---------------------------------------------------------------------------


class TestAskEmbeddingFailure:
    """Tests for embedding service failure."""

    def test_embedding_failure_returns_503(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 503 when embedding service fails."""
        embedding_svc = AsyncMock()
        embedding_svc.generate_embedding = AsyncMock(
            side_effect=EmbeddingError("Azure OpenAI rate limit exceeded")
        )
        embedding_svc.close = AsyncMock()

        with patch("src.query.ask._get_embedding_service", return_value=embedding_svc):
            response = client.post(
                "/v1/ask",
                json={"question": "What services exist?"},
                headers=auth_headers,
            )

        assert response.status_code == 503
        body = response.json()
        assert body["error"] == "service_unavailable"
        assert "temporarily unavailable" in body["message"].lower()


# ---------------------------------------------------------------------------
# Tests: LLM failure (503 with fallback)
# ---------------------------------------------------------------------------


class TestAskLLMFailure:
    """Tests for LLM service failure with fallback to raw results."""

    def test_llm_failure_returns_503_with_fallback_citations(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 503 with fallback citations when LLM fails."""
        embedding_svc = AsyncMock()
        embedding_svc.generate_embedding = AsyncMock(return_value=SAMPLE_VECTOR)
        embedding_svc.close = AsyncMock()

        vector_store = AsyncMock()
        vector_store.search = AsyncMock(return_value=SAMPLE_HITS)
        vector_store.close = AsyncMock()

        # Mock the graph functions directly
        async def mock_get_entity(driver, source_id):
            if source_id == "github:repo:payments-service":
                return SAMPLE_ENTITY_SERVICE
            elif source_id == "jira:ticket:ENG-1234":
                return SAMPLE_ENTITY_TICKET
            return None

        async def mock_get_neighborhood(driver, source_id, hops=2):
            return []

        driver = AsyncMock()
        driver.close = AsyncMock()

        # Mock LLM client that raises
        llm_client = AsyncMock()
        llm_client.chat.completions.create = AsyncMock(
            side_effect=Exception("LLM service unavailable")
        )
        llm_client.close = AsyncMock()

        with patch("src.query.ask._get_embedding_service", return_value=embedding_svc), \
             patch("src.query.ask._get_vector_store", return_value=vector_store), \
             patch("src.query.ask._get_neo4j_driver", return_value=driver), \
             patch("src.query.ask._get_llm_client", return_value=llm_client), \
             patch("src.query.ask._get_entity_by_source_id", side_effect=mock_get_entity), \
             patch("src.query.ask.graph_queries.get_entity_neighborhood", side_effect=mock_get_neighborhood):
            response = client.post(
                "/v1/ask",
                json={"question": "What depends on payments?"},
                headers=auth_headers,
            )

        assert response.status_code == 503
        body = response.json()
        assert body["error"] == "service_unavailable"
        assert "citations" in body
        assert len(body["citations"]) > 0


# ---------------------------------------------------------------------------
# Tests: Valid question with answer and citations (200)
# ---------------------------------------------------------------------------


class TestAskValidQuestion:
    """Tests for successful question answering."""

    def test_valid_question_returns_200_with_answer_and_citations(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 200 with answer and citations for a valid question."""
        embedding_svc = AsyncMock()
        embedding_svc.generate_embedding = AsyncMock(return_value=SAMPLE_VECTOR)
        embedding_svc.close = AsyncMock()

        vector_store = AsyncMock()
        vector_store.search = AsyncMock(return_value=SAMPLE_HITS)
        vector_store.close = AsyncMock()

        # Mock the graph functions directly
        async def mock_get_entity(driver, source_id):
            if source_id == "github:repo:payments-service":
                return SAMPLE_ENTITY_SERVICE
            elif source_id == "jira:ticket:ENG-1234":
                return SAMPLE_ENTITY_TICKET
            return None

        async def mock_get_neighborhood(driver, source_id, hops=2):
            if source_id == "github:repo:payments-service":
                return [SAMPLE_NEIGHBOR]
            return []

        driver = AsyncMock()
        driver.close = AsyncMock()

        # Mock LLM client
        llm_client = AsyncMock()
        completion_mock = MagicMock()
        choice_mock = MagicMock()
        choice_mock.message.content = LLM_ANSWER_WITH_CITATIONS
        completion_mock.choices = [choice_mock]
        llm_client.chat.completions.create = AsyncMock(return_value=completion_mock)
        llm_client.close = AsyncMock()

        with patch("src.query.ask._get_embedding_service", return_value=embedding_svc), \
             patch("src.query.ask._get_vector_store", return_value=vector_store), \
             patch("src.query.ask._get_neo4j_driver", return_value=driver), \
             patch("src.query.ask._get_llm_client", return_value=llm_client), \
             patch("src.query.ask._get_entity_by_source_id", side_effect=mock_get_entity), \
             patch("src.query.ask.graph_queries.get_entity_neighborhood", side_effect=mock_get_neighborhood):
            response = client.post(
                "/v1/ask",
                json={"question": "What services depend on payments?"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        body = response.json()
        assert body["answer"] is not None
        assert "payments-service" in body["answer"]
        assert len(body["citations"]) >= 1

        # Verify citations contain expected source_ids
        citation_ids = [c["source_id"] for c in body["citations"]]
        assert "github:repo:payments-service" in citation_ids


# ---------------------------------------------------------------------------
# Tests: Citation extraction
# ---------------------------------------------------------------------------


class TestCitationExtraction:
    """Tests for citation extraction from LLM response."""

    def test_citations_extracted_from_llm_response(self) -> None:
        """Should extract citations for source_ids mentioned in LLM response."""
        llm_response = (
            "The payments-service (github:repo:payments-service) has a ticket "
            "jira:ticket:ENG-1234 about fixing timeouts."
        )
        entities = [SAMPLE_ENTITY_SERVICE, SAMPLE_ENTITY_TICKET, SAMPLE_NEIGHBOR]

        citations = _extract_citations(llm_response, entities)

        assert len(citations) == 2
        citation_ids = [c.source_id for c in citations]
        assert "github:repo:payments-service" in citation_ids
        assert "jira:ticket:ENG-1234" in citation_ids

    def test_no_citations_when_no_source_ids_in_response(self) -> None:
        """Should return empty citations when no source_ids are mentioned."""
        llm_response = "I don't have enough information to answer this question."
        entities = [SAMPLE_ENTITY_SERVICE, SAMPLE_ENTITY_TICKET]

        citations = _extract_citations(llm_response, entities)

        assert citations == []


# ---------------------------------------------------------------------------
# Tests: Context assembly token budget
# ---------------------------------------------------------------------------


class TestContextAssembly:
    """Tests for context assembly respecting token budget."""

    def test_context_assembly_respects_token_budget(self) -> None:
        """Should truncate context when it exceeds the token budget."""
        # Create entities with long descriptions
        entities = [
            {
                "source_id": f"test:entity:{i}",
                "name": f"Entity {i}",
                "description": "A" * 500,
            }
            for i in range(20)
        ]
        neighbors = [
            {
                "source_id": f"test:neighbor:{i}",
                "name": f"Neighbor {i}",
                "description": "B" * 500,
            }
            for i in range(20)
        ]

        # Very small budget: 100 tokens = 400 chars
        context = _assemble_context(entities, neighbors, token_budget=100)

        # Context should be within budget
        assert len(context) <= 400

    def test_context_assembly_prioritizes_matched_entities(self) -> None:
        """Should include vector-matched entities before neighbors."""
        entities = [
            {"source_id": "matched:1", "name": "Matched Entity"},
        ]
        neighbors = [
            {"source_id": "neighbor:1", "name": "Neighbor Entity"},
        ]

        context = _assemble_context(entities, neighbors, token_budget=8000)

        # Matched entity should appear before neighbor
        matched_pos = context.find("matched:1")
        neighbor_pos = context.find("neighbor:1")
        assert matched_pos < neighbor_pos
