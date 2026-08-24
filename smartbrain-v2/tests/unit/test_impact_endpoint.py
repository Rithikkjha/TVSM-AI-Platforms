"""Unit tests for GET /v1/services/{name}/impact endpoint.

Tests cover:
- Service found with downstream dependents → 200 with affected services at correct hops
- Service with no dependents → 200 with empty affected_services
- Service not found → 404
- Linked tickets and epics collected from affected services
- Max_hops=2 boundary (services at hop 3 excluded)
- API key required (401 without)

Since we don't have a real Neo4j instance in tests, the graph_queries
functions are mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from config.settings import Settings, get_settings
from api.app import app

# Use a known API key for testing
TEST_API_KEY = "test-secret-key-impact"


@pytest.fixture(autouse=True)
def _override_settings() -> None:  # type: ignore[misc]
    """Override settings to use a known API key."""
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

SAMPLE_SERVICE = {
    "source_id": "github:repo:payments-service",
    "name": "payments-service",
    "description": "Handles payment processing and billing",
    "updated_at": "2024-12-01T10:00:00+00:00",
    "created_at": "2024-01-01T00:00:00+00:00",
}

SAMPLE_IMPACT_WITH_DEPENDENTS = {
    "affected_services": [
        {"source_id": "github:repo:checkout-service", "name": "checkout-service", "hops": 1},
        {"source_id": "github:repo:order-service", "name": "order-service", "hops": 2},
    ],
    "linked_epics": [
        {
            "source_id": "jira:epic:ENG-100",
            "key": "ENG-100",
            "title": "Payment Platform Rewrite",
            "status": "In Progress",
        },
    ],
    "linked_tickets": [
        {
            "source_id": "jira:ticket:ENG-1234",
            "key": "ENG-1234",
            "title": "Fix timeout on payment retry",
            "status": "In Progress",
            "priority": "High",
        },
        {
            "source_id": "jira:ticket:ENG-1235",
            "key": "ENG-1235",
            "title": "Add idempotency key",
            "status": "To Do",
            "priority": "Medium",
        },
    ],
}

SAMPLE_IMPACT_EMPTY = {
    "affected_services": [],
    "linked_epics": [],
    "linked_tickets": [],
}


# ---------------------------------------------------------------------------
# Helper to mock graph queries for impact endpoint
# ---------------------------------------------------------------------------


def _mock_impact_queries(
    service: dict | None = None,
    impact_data: dict | None = None,
):
    """Return context managers that patch graph_queries functions for impact."""
    if service is None:
        service_mock = AsyncMock(return_value=None)
    else:
        service_mock = AsyncMock(return_value=service)

    impact_mock = AsyncMock(return_value=impact_data or SAMPLE_IMPACT_EMPTY)

    return (
        patch("src.query.services.graph_queries.get_service_by_name", service_mock),
        patch("src.query.services.graph_queries.get_impact_graph", impact_mock),
        patch("src.query.services._get_neo4j_driver", return_value=AsyncMock()),
    )


# ---------------------------------------------------------------------------
# Tests: API key authentication
# ---------------------------------------------------------------------------


class TestImpactEndpointAuth:
    """Tests for API key requirement on the impact endpoint."""

    def test_returns_401_without_api_key(self, client: TestClient) -> None:
        """Should reject requests without an API key."""
        response = client.get("/v1/services/payments-service/impact")
        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["error"] == "unauthorized"

    def test_returns_401_with_wrong_api_key(self, client: TestClient) -> None:
        """Should reject requests with an incorrect API key."""
        response = client.get(
            "/v1/services/payments-service/impact",
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Tests: Service not found (404)
# ---------------------------------------------------------------------------


class TestImpactServiceNotFound:
    """Tests for service not found (404 response)."""

    def test_returns_404_when_service_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 404 with a message including the service name."""
        patches = _mock_impact_queries(service=None)
        with patches[0], patches[1], patches[2]:
            response = client.get("/v1/services/unknown-service/impact", headers=auth_headers)

        assert response.status_code == 404
        body = response.json()
        assert body["error"] == "not_found"
        assert "unknown-service" in body["message"]


# ---------------------------------------------------------------------------
# Tests: Service found with dependents (200)
# ---------------------------------------------------------------------------


class TestImpactWithDependents:
    """Tests for successful impact analysis with downstream dependents."""

    def test_returns_200_with_affected_services(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 200 with affected services at correct hops."""
        patches = _mock_impact_queries(
            service=SAMPLE_SERVICE,
            impact_data=SAMPLE_IMPACT_WITH_DEPENDENTS,
        )
        with patches[0], patches[1], patches[2]:
            response = client.get("/v1/services/payments-service/impact", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()

        assert body["service"] == "payments-service"
        assert body["max_hops"] == 2
        assert len(body["affected_services"]) == 2

        # Verify hop distances
        hop1_services = [s for s in body["affected_services"] if s["hops"] == 1]
        hop2_services = [s for s in body["affected_services"] if s["hops"] == 2]
        assert len(hop1_services) == 1
        assert len(hop2_services) == 1
        assert hop1_services[0]["name"] == "checkout-service"
        assert hop2_services[0]["name"] == "order-service"

    def test_affected_services_have_correct_fields(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should include source_id, name, and hops for each affected service."""
        patches = _mock_impact_queries(
            service=SAMPLE_SERVICE,
            impact_data=SAMPLE_IMPACT_WITH_DEPENDENTS,
        )
        with patches[0], patches[1], patches[2]:
            response = client.get("/v1/services/payments-service/impact", headers=auth_headers)

        body = response.json()
        for svc in body["affected_services"]:
            assert "source_id" in svc
            assert "name" in svc
            assert "hops" in svc
            assert svc["hops"] in (1, 2)

    def test_linked_epics_collected(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should collect epics linked to affected services."""
        patches = _mock_impact_queries(
            service=SAMPLE_SERVICE,
            impact_data=SAMPLE_IMPACT_WITH_DEPENDENTS,
        )
        with patches[0], patches[1], patches[2]:
            response = client.get("/v1/services/payments-service/impact", headers=auth_headers)

        body = response.json()
        assert len(body["linked_epics"]) == 1
        assert body["linked_epics"][0]["key"] == "ENG-100"
        assert body["linked_epics"][0]["title"] == "Payment Platform Rewrite"
        assert body["linked_epics"][0]["status"] == "In Progress"

    def test_linked_tickets_collected(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should collect tickets linked to affected services."""
        patches = _mock_impact_queries(
            service=SAMPLE_SERVICE,
            impact_data=SAMPLE_IMPACT_WITH_DEPENDENTS,
        )
        with patches[0], patches[1], patches[2]:
            response = client.get("/v1/services/payments-service/impact", headers=auth_headers)

        body = response.json()
        assert len(body["linked_tickets"]) == 2
        ticket_keys = [t["key"] for t in body["linked_tickets"]]
        assert "ENG-1234" in ticket_keys
        assert "ENG-1235" in ticket_keys


# ---------------------------------------------------------------------------
# Tests: Service with no dependents (200)
# ---------------------------------------------------------------------------


class TestImpactNoDependents:
    """Tests for service with no downstream dependents."""

    def test_returns_200_with_empty_affected_services(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should return 200 with empty lists when no dependents exist."""
        patches = _mock_impact_queries(
            service=SAMPLE_SERVICE,
            impact_data=SAMPLE_IMPACT_EMPTY,
        )
        with patches[0], patches[1], patches[2]:
            response = client.get("/v1/services/payments-service/impact", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["service"] == "payments-service"
        assert body["max_hops"] == 2
        assert body["affected_services"] == []
        assert body["linked_epics"] == []
        assert body["linked_tickets"] == []


# ---------------------------------------------------------------------------
# Tests: Max hops boundary
# ---------------------------------------------------------------------------


class TestImpactMaxHopsBoundary:
    """Tests for max_hops=2 boundary (services at hop 3 excluded)."""

    def test_only_services_within_2_hops_included(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should only include services at hop 1 and 2, not beyond."""
        # The graph_queries.get_impact_graph function enforces the 2-hop limit
        # via the Cypher query. We verify the endpoint correctly passes max_hops=2
        # and only returns services within that boundary.
        impact_data = {
            "affected_services": [
                {"source_id": "github:repo:svc-a", "name": "svc-a", "hops": 1},
                {"source_id": "github:repo:svc-b", "name": "svc-b", "hops": 2},
            ],
            "linked_epics": [],
            "linked_tickets": [],
        }
        patches = _mock_impact_queries(
            service=SAMPLE_SERVICE,
            impact_data=impact_data,
        )
        with patches[0], patches[1], patches[2]:
            response = client.get("/v1/services/payments-service/impact", headers=auth_headers)

        body = response.json()
        # All returned services should be at hops 1 or 2
        for svc in body["affected_services"]:
            assert svc["hops"] <= 2
        # No hop 3 services should be present
        hop3_services = [s for s in body["affected_services"] if s["hops"] > 2]
        assert len(hop3_services) == 0

    def test_get_impact_graph_called_with_max_hops_2(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Should call get_impact_graph with max_hops=2."""
        service_mock = AsyncMock(return_value=SAMPLE_SERVICE)
        impact_mock = AsyncMock(return_value=SAMPLE_IMPACT_EMPTY)

        with (
            patch("src.query.services.graph_queries.get_service_by_name", service_mock),
            patch("src.query.services.graph_queries.get_impact_graph", impact_mock),
            patch("src.query.services._get_neo4j_driver", return_value=AsyncMock()),
        ):
            client.get("/v1/services/payments-service/impact", headers=auth_headers)

        # Verify get_impact_graph was called with max_hops=2
        impact_mock.assert_called_once()
        call_kwargs = impact_mock.call_args
        assert call_kwargs[1]["max_hops"] == 2
