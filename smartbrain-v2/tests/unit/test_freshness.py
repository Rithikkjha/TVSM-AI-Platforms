"""Unit tests for :mod:`src.query.freshness` and the expanded health endpoint.

Tests cover:
- check_staleness with fresh, stale, None, and invalid inputs
- Health endpoint expanded response shape
- Health endpoint graceful handling of Neo4j disconnection

Requirements: 4.1, 4.2, 4.3, 4.4
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from config.settings import Settings, get_settings
from api.app import app
from retrieval.search.freshness import check_staleness, get_freshness_summary

TEST_API_KEY = "test-secret-key-12345"


@pytest.fixture(autouse=True)
def _override_settings() -> None:  # type: ignore[misc]
    """Override settings to use known values for all tests."""
    get_settings.cache_clear()
    with patch(
        "src.query.app.get_settings",
        return_value=Settings(
            api_key=TEST_API_KEY,
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="test",
            qdrant_url="http://localhost:6333",
        ),
    ):
        yield
    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    """Create a TestClient for the FastAPI app."""
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# check_staleness tests
# ---------------------------------------------------------------------------


class TestCheckStaleness:
    """Tests for the check_staleness function."""

    def test_fresh_timestamp_returns_none(self) -> None:
        """A timestamp within the threshold should return None (not stale)."""
        recent = datetime.now(UTC) - timedelta(hours=1)
        result = check_staleness(recent.isoformat(), threshold_hours=24)
        assert result is None

    def test_stale_timestamp_returns_stale(self) -> None:
        """A timestamp older than the threshold should return 'stale'."""
        old = datetime.now(UTC) - timedelta(hours=48)
        result = check_staleness(old.isoformat(), threshold_hours=24)
        assert result == "stale"

    def test_none_returns_stale(self) -> None:
        """None updated_at should return 'stale'."""
        result = check_staleness(None, threshold_hours=24)
        assert result == "stale"

    def test_invalid_string_returns_stale(self) -> None:
        """An unparseable string should return 'stale'."""
        result = check_staleness("not-a-date", threshold_hours=24)
        assert result == "stale"

    def test_datetime_object_fresh(self) -> None:
        """A fresh datetime object should return None."""
        recent = datetime.now(UTC) - timedelta(hours=2)
        result = check_staleness(recent, threshold_hours=24)
        assert result is None

    def test_datetime_object_stale(self) -> None:
        """A stale datetime object should return 'stale'."""
        old = datetime.now(UTC) - timedelta(hours=30)
        result = check_staleness(old, threshold_hours=24)
        assert result == "stale"

    def test_iso_string_with_z_suffix(self) -> None:
        """ISO string with Z suffix should be parsed correctly."""
        recent = datetime.now(UTC) - timedelta(hours=1)
        iso_str = recent.strftime("%Y-%m-%dT%H:%M:%SZ")
        result = check_staleness(iso_str, threshold_hours=24)
        assert result is None

    def test_naive_datetime_treated_as_utc(self) -> None:
        """A naive datetime (no tzinfo) should be treated as UTC."""
        # Use a recent naive datetime
        recent = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
        result = check_staleness(recent, threshold_hours=24)
        assert result is None

    def test_uses_default_threshold_from_settings(self) -> None:
        """When threshold_hours is not provided, uses settings default."""
        with patch(
            "src.query.freshness.get_settings",
            return_value=Settings(staleness_threshold_hours=12),
        ):
            # 15 hours old — stale with 12h threshold
            old = datetime.now(UTC) - timedelta(hours=15)
            result = check_staleness(old.isoformat())
            assert result == "stale"

            # 5 hours old — fresh with 12h threshold
            recent = datetime.now(UTC) - timedelta(hours=5)
            result = check_staleness(recent.isoformat())
            assert result is None


# ---------------------------------------------------------------------------
# get_freshness_summary tests
# ---------------------------------------------------------------------------


class TestGetFreshnessSummary:
    """Tests for the get_freshness_summary function."""

    @pytest.mark.asyncio
    async def test_returns_correct_percentages(self) -> None:
        """Should compute correct percentages from Neo4j bucket counts."""
        mock_records = [
            {"bucket": "within_1h", "cnt": 10},
            {"bucket": "within_24h", "cnt": 40},
            {"bucket": "old", "cnt": 50},
        ]

        mock_result = AsyncMock()
        mock_result.data = AsyncMock(return_value=mock_records)

        mock_session = AsyncMock()
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver = MagicMock()
        mock_driver.session = MagicMock(return_value=mock_session)

        result = await get_freshness_summary(mock_driver)

        assert result["total_entities"] == 100
        assert result["updated_within_1h"] == 10  # 10/100 = 10%
        assert result["updated_within_24h"] == 50  # (10+40)/100 = 50%
        assert result["older_than_24h"] == 50  # 50/100 = 50%

    @pytest.mark.asyncio
    async def test_empty_graph_returns_zeros(self) -> None:
        """An empty graph should return all zeros."""
        mock_result = AsyncMock()
        mock_result.data = AsyncMock(return_value=[])

        mock_session = AsyncMock()
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver = MagicMock()
        mock_driver.session = MagicMock(return_value=mock_session)

        result = await get_freshness_summary(mock_driver)

        assert result["total_entities"] == 0
        assert result["updated_within_1h"] == 0
        assert result["updated_within_24h"] == 0
        assert result["older_than_24h"] == 0


# ---------------------------------------------------------------------------
# Health endpoint tests
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Tests for the expanded GET /v1/health endpoint."""

    def test_health_returns_expanded_response_shape(self, client: TestClient) -> None:
        """Health endpoint should return the expanded response with all fields."""
        mock_freshness = {
            "updated_within_1h": 45,
            "updated_within_24h": 85,
            "older_than_24h": 15,
            "total_entities": 200,
        }

        mock_result = AsyncMock()
        mock_result.data = AsyncMock(return_value=[])

        mock_session = AsyncMock()
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver = AsyncMock()
        mock_driver.session = MagicMock(return_value=mock_session)
        mock_driver.close = AsyncMock()

        mock_get_freshness = AsyncMock(return_value=mock_freshness)

        with (
            patch("neo4j.AsyncGraphDatabase") as mock_agd,
            patch(
                "src.query.app.get_freshness_summary",
                mock_get_freshness,
            ),
        ):
            mock_agd.driver = MagicMock(return_value=mock_driver)

            response = client.get("/v1/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["neo4j"] == "connected"
        assert body["vector_store"] == "connected"
        assert body["last_sync"] is None
        assert body["freshness"] == mock_freshness

    def test_health_handles_neo4j_disconnection(self, client: TestClient) -> None:
        """Health endpoint should return partial response when Neo4j is down."""
        with patch(
            "neo4j.AsyncGraphDatabase",
        ) as mock_agd:
            mock_agd.driver = MagicMock(side_effect=Exception("Connection refused"))
            response = client.get("/v1/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["neo4j"] == "disconnected"
        assert body["freshness"] is None
        # Vector store should still be checked
        assert body["vector_store"] == "connected"

    def test_health_unauthenticated(self, client: TestClient) -> None:
        """Health endpoint should not require API key."""
        with patch(
            "neo4j.AsyncGraphDatabase",
        ) as mock_agd:
            mock_agd.driver = MagicMock(side_effect=Exception("Connection refused"))
            response = client.get("/v1/health")

        assert response.status_code == 200
