"""Unit tests for :mod:`src.query.app`.

Tests cover the FastAPI application setup including:
- Health endpoint (unauthenticated)
- API key authentication (missing, wrong, correct)
- CORS headers
- Global exception handler (structured 500 response)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from config.settings import Settings, get_settings
from api.app import app

# Use a known API key for testing
TEST_API_KEY = "test-secret-key-12345"


@pytest.fixture(autouse=True)
def _override_settings() -> None:  # type: ignore[misc]
    """Override settings to use a known API key for all tests."""
    get_settings.cache_clear()
    with patch(
        "src.query.app.get_settings",
        return_value=Settings(api_key=TEST_API_KEY),
    ):
        yield
    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    """Create a TestClient for the FastAPI app."""
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Tests for GET /v1/health (unauthenticated)."""

    def test_health_returns_200_without_api_key(self, client: TestClient) -> None:
        """Health endpoint should be accessible without authentication."""
        response = client.get("/v1/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        # Expanded response includes these keys
        assert "neo4j" in body
        assert "vector_store" in body
        assert "last_sync" in body
        assert "freshness" in body

    def test_health_returns_200_with_api_key(self, client: TestClient) -> None:
        """Health endpoint should also work if an API key is provided."""
        response = client.get("/v1/health", headers={"X-API-Key": TEST_API_KEY})
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "neo4j" in body


# ---------------------------------------------------------------------------
# API key authentication
# ---------------------------------------------------------------------------


class TestApiKeyAuthentication:
    """Tests for API key authentication on protected endpoints."""

    def test_returns_401_without_api_key(self, client: TestClient) -> None:
        """Authenticated endpoints should reject requests without an API key."""
        response = client.get("/v1/services")
        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["error"] == "unauthorized"
        assert "Invalid or missing API key" in body["detail"]["message"]

    def test_returns_401_with_wrong_api_key(self, client: TestClient) -> None:
        """Authenticated endpoints should reject requests with an incorrect key."""
        response = client.get("/v1/services", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401
        body = response.json()
        assert body["detail"]["error"] == "unauthorized"

    def test_returns_200_with_correct_api_key(self, client: TestClient) -> None:
        """Authenticated endpoints should accept requests with the correct key."""
        response = client.get("/v1/services", headers={"X-API-Key": TEST_API_KEY})
        assert response.status_code == 200
        assert "services" in response.json()


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


class TestCorsHeaders:
    """Tests for CORS middleware configuration."""

    def test_cors_headers_present_on_preflight(self, client: TestClient) -> None:
        """CORS preflight (OPTIONS) should return appropriate headers."""
        response = client.options(
            "/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        # With allow_origins=["*"] and allow_credentials=True, Starlette
        # echoes the request origin rather than a literal "*".
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_cors_headers_present_on_response(self, client: TestClient) -> None:
        """Regular responses should include CORS headers when Origin is sent."""
        response = client.get(
            "/v1/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------


class TestExceptionHandler:
    """Tests for the global unhandled exception handler."""

    def test_unhandled_exception_returns_500_structured_error(
        self, client: TestClient
    ) -> None:
        """Unhandled exceptions should return a structured 500 JSON response."""
        # Add a temporary route that raises an unhandled exception
        error_router = APIRouter()

        @error_router.get("/v1/explode")
        async def explode() -> None:
            raise RuntimeError("Something went terribly wrong")

        app.include_router(error_router)
        try:
            response = client.get("/v1/explode")
            assert response.status_code == 500
            body = response.json()
            assert body["error"] == "internal_error"
            assert body["message"] == "An unexpected error occurred"
        finally:
            # Clean up the temporary route
            app.routes[:] = [r for r in app.routes if getattr(r, "path", "") != "/v1/explode"]


# ---------------------------------------------------------------------------
# Static UI serving
# ---------------------------------------------------------------------------


class TestStaticUiServing:
    """Tests for static file serving of the Web UI at /ui/."""

    def test_ui_index_returns_200(self, client: TestClient) -> None:
        """GET /ui/ should serve the index.html file."""
        response = client.get("/ui/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Engineering Memory Graph" in response.text

    def test_ui_style_css_returns_200(self, client: TestClient) -> None:
        """GET /ui/style.css should serve the stylesheet."""
        response = client.get("/ui/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers.get("content-type", "")

    def test_ui_api_js_returns_200(self, client: TestClient) -> None:
        """GET /ui/api.js should serve the API client module."""
        response = client.get("/ui/api.js")
        assert response.status_code == 200
        assert "javascript" in response.headers.get("content-type", "")

    def test_ui_app_js_returns_200(self, client: TestClient) -> None:
        """GET /ui/app.js should serve the main app script."""
        response = client.get("/ui/app.js")
        assert response.status_code == 200
        assert "javascript" in response.headers.get("content-type", "")
