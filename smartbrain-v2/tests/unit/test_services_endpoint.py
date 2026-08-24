"""Unit tests for GET /v1/services/{name} endpoint.

Tests cover:
- Service found → 200 with correct response shape
- Service not found → 404 with helpful message
- Staleness indicator appears when entity is old
- Staleness indicator absent when entity is fresh
- Owners, dependencies, tickets, documents populated correctly
- API key required (401 without)

Since we don't have a real Neo4j instance in tests, the graph_queries
functions are mocked.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from config.settings import Settings, get_settings
from api.app import app

# Use a known API key for testing
TEST_API_KEY = "test-secret-key-services"


@pytest.fixture(autouse=True)
def _override_settings() -> None:  # type: ignore[misc]
    """Override settings to use a known API key and staleness threshold."""
    get_settings.cache_clear()
    with patch(
        "src.query.app.get_settings",
        return_value=Settings(api_key=TEST_API_KEY, staleness_threshold_hours=24),
    ), patch(
        "src.query.services.get_settings",
        return_value=Settings(api_key=TEST_API_KEY, staleness_threshold_hours=24),
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

FRESH_TIMESTAMP = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
STALE_TIMESTAMP = (datetime.now(UTC) - timedelta(hours=48)).isoformat()

SAMPLE_SERVICE = {
    "source_id": "github:repo:payments-service",
    "name": "payments-service",
    "description": "Handles payment processing and billing",
    "updated_at": FRESH_TIMESTAMP,
    "created_at": "2024-01-01T00:00:00+00:00",
}

SAMPLE_OWNERS = [
    {"source_id": "jira:team:payments", "name": "Payments Team"},
]

SAMPLE_UPSTREAM = [
    {
        "source_id": "github:repo:auth-service",
        "name": "auth-service",
        "rel_props": {"dependency_type": "runtime"},
    },
]

SAMPLE_DOWNSTREAM = [
    {
        "source_id": "github:repo:checkout-service",
        "name": "checkout-service",
        "rel_props": {"dependency_type": "runtime"},
    },
]

SAMPLE_TICKETS = [
    {
        "source_id": "jira:ticket:ENG-1234",
        "key": "ENG-1234",
        "title": "Fix timeout on payment retry",
        "status": "In Progress",
        "priority": "High",
    },
]

SAMPLE_DOCUMENTS = [
    {
        "source_id": "confluence:page:12345",
        "title": "Payments Architecture",
        "url": "https://confluence.example.com/pages/12345",
    },
]


# ---------------------------------------------------------------------------
# Helper to mock all graph queries
# ---------------------------------------------------------------------------


def _mock_graph_queries(
    service: dict | None = None,
    owners: list | None = None,
    upstream: list | None = None,
    downstream: list | None = None,
    tickets: list | None = None,
    documents: list | None = None,
):
    """Return a context manager that patches all graph_queries functions."""
    if service is None:
        service_mock = AsyncMock(return_value=None)
    else:
        service_mock = AsyncMock(return_value=service)

    owners_mock = AsyncMock(return_value=owners or [])
    deps_mock = AsyncMock(
        side_effect=lambda driver, sid, direction: (upstream or [])
        if direction == "upstream"
        else (downstream or [])
    )
    tickets_mock = AsyncMock(return_value=tickets or [])
    documents_mock = AsyncMock(return_value=documents or [])

    return (
        patch("src.query.services.graph_queries.get_service_by_name", service_mock),
        patch("src.query.services.graph_queries.get_service_owners", owners_mock),
        patch("src.query.services.graph_queries.get_service_dependencies", deps_mock),
        patch("src.query.services.graph_queries.get_service_tickets", tickets_mock),
        patch("src.query.services.graph_queries.get_service_documents", documents_mock),
        patch("src.query.services._get_neo4j_driver", return_value=AsyncMock()),
    )


# ---------------------------------------------------------------------------
# Tests: API key authentication
# ---------------------------------------------------------------------------


class TestServiceEndpointAuth:
    """Tests for API key requirement on the services endpoint."""

    def test_returns_401_without_api_key(self, client: TestClient) -> None:
        """Should reject requests without an API key."""
        response = client.get("/v1/services/payments-service")
        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["error"] == "unauthorized"

    def test_returns_401_with_wrong_api_key(self, client: TestClient) -> None:
        """Should reject requests with an incorrect API key."""
        response = client.get(
            "/v1/services/payments-service",
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Tests: Service found (200)
# ---------------------------------------------------------------------------


class TestServiceFound:
    """Tests for successful service lookup (200 response)."""

    def test_returns_200_with_correct_shape(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 200 with the full service response shape."""
        patches = _mock_graph_queries(
            service=SAMPLE_SERVICE,
            owners=SAMPLE_OWNERS,
            upstream=SAMPLE_UPSTREAM,
            downstream=SAMPLE_DOWNSTREAM,
            tickets=SAMPLE_TICKETS,
            documents=SAMPLE_DOCUMENTS,
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            response = client.get("/v1/services/payments-service", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()

        # Verify top-level keys
        assert "service" in body
        assert "owners" in body
        assert "upstream_dependencies" in body
        assert "downstream_dependents" in body
        assert "linked_tickets" in body
        assert "documents" in body
        assert "staleness" in body

    def test_service_properties_returned(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return the full service properties dict."""
        patches = _mock_graph_queries(service=SAMPLE_SERVICE)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            response = client.get("/v1/services/payments-service", headers=auth_headers)

        body = response.json()
        assert body["service"]["name"] == "payments-service"
        assert body["service"]["source_id"] == "github:repo:payments-service"
        assert body["service"]["description"] == "Handles payment processing and billing"

    def test_owners_populated(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should populate owners from OWNED_BY relationships."""
        patches = _mock_graph_queries(service=SAMPLE_SERVICE, owners=SAMPLE_OWNERS)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            response = client.get("/v1/services/payments-service", headers=auth_headers)

        body = response.json()
        assert len(body["owners"]) == 1
        assert body["owners"][0]["source_id"] == "jira:team:payments"
        assert body["owners"][0]["name"] == "Payments Team"

    def test_upstream_dependencies_populated(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should populate upstream dependencies (outgoing DEPENDS_ON)."""
        patches = _mock_graph_queries(service=SAMPLE_SERVICE, upstream=SAMPLE_UPSTREAM)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            response = client.get("/v1/services/payments-service", headers=auth_headers)

        body = response.json()
        assert len(body["upstream_dependencies"]) == 1
        assert body["upstream_dependencies"][0]["name"] == "auth-service"
        assert body["upstream_dependencies"][0]["dependency_type"] == "runtime"

    def test_downstream_dependents_populated(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should populate downstream dependents (incoming DEPENDS_ON)."""
        patches = _mock_graph_queries(service=SAMPLE_SERVICE, downstream=SAMPLE_DOWNSTREAM)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            response = client.get("/v1/services/payments-service", headers=auth_headers)

        body = response.json()
        assert len(body["downstream_dependents"]) == 1
        assert body["downstream_dependents"][0]["name"] == "checkout-service"
        assert body["downstream_dependents"][0]["dependency_type"] == "runtime"

    def test_linked_tickets_populated(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should populate linked tickets from LINKED_TO relationships."""
        patches = _mock_graph_queries(service=SAMPLE_SERVICE, tickets=SAMPLE_TICKETS)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            response = client.get("/v1/services/payments-service", headers=auth_headers)

        body = response.json()
        assert len(body["linked_tickets"]) == 1
        assert body["linked_tickets"][0]["key"] == "ENG-1234"
        assert body["linked_tickets"][0]["title"] == "Fix timeout on payment retry"
        assert body["linked_tickets"][0]["status"] == "In Progress"

    def test_documents_populated(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should populate documents from DOCUMENTED_IN relationships."""
        patches = _mock_graph_queries(service=SAMPLE_SERVICE, documents=SAMPLE_DOCUMENTS)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            response = client.get("/v1/services/payments-service", headers=auth_headers)

        body = response.json()
        assert len(body["documents"]) == 1
        assert body["documents"][0]["title"] == "Payments Architecture"
        assert body["documents"][0]["url"] == "https://confluence.example.com/pages/12345"
        assert body["documents"][0]["source_id"] == "confluence:page:12345"


# ---------------------------------------------------------------------------
# Tests: Service not found (404)
# ---------------------------------------------------------------------------


class TestServiceNotFound:
    """Tests for service not found (404 response)."""

    def test_returns_404_with_helpful_message(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 404 with a message including the service name."""
        patches = _mock_graph_queries(service=None)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            response = client.get("/v1/services/unknown-service", headers=auth_headers)

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "not_found"
        assert "unknown-service" in body["message"]
        assert "not found" in body["message"].lower()


# ---------------------------------------------------------------------------
# Tests: Staleness indicator
# ---------------------------------------------------------------------------


class TestStalenessIndicator:
    """Tests for the staleness indicator in service responses."""

    def test_staleness_absent_when_fresh(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should not include staleness when entity is recently updated."""
        fresh_service = {**SAMPLE_SERVICE, "updated_at": FRESH_TIMESTAMP}
        patches = _mock_graph_queries(service=fresh_service)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            response = client.get("/v1/services/payments-service", headers=auth_headers)

        body = response.json()
        assert body["staleness"] is None

    def test_staleness_present_when_old(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should include staleness='stale' when entity exceeds threshold."""
        stale_service = {**SAMPLE_SERVICE, "updated_at": STALE_TIMESTAMP}
        patches = _mock_graph_queries(service=stale_service)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            response = client.get("/v1/services/payments-service", headers=auth_headers)

        body = response.json()
        assert body["staleness"] == "stale"

    def test_staleness_when_updated_at_missing(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should mark as stale when updated_at is missing."""
        service_no_timestamp = {
            "source_id": "github:repo:old-service",
            "name": "old-service",
        }
        patches = _mock_graph_queries(service=service_no_timestamp)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            response = client.get("/v1/services/old-service", headers=auth_headers)

        body = response.json()
        assert body["staleness"] == "stale"
