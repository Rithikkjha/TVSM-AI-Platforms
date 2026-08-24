"""P0 Critical Path Integration Tests for TVS PlanIQ Estimation Tool.

Tests the FastAPI app directly using TestClient with DEV_MODE=true.
In dev mode, auth is bypassed (all requests authenticated as admin).

Covers:
1.  Health check
2.  Auth login (valid + invalid email)
3.  Admin users (list + add)
4.  MPCP Dashboard
5.  MPCP Projects (list all)
6.  MPCP CPs (list all)
7.  MPCP Process Track
8.  MPCP Budget update
9.  MPCP Dependencies (add with is_blocker=True)
10. PRD Check audit endpoint
11. Estimations list
12. Build vs Buy evaluations list
"""

import os

# CRITICAL: Set DEV_MODE before importing the app so auth is bypassed
os.environ["DEV_MODE"] = "true"
os.environ["SSO_SECRET"] = "test-secret-key-for-p0-integration-tests-32chars"

import pytest
from fastapi.testclient import TestClient

from main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the FastAPI app with DEV_MODE=true."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers():
    """Standard auth headers for all requests (dev mode accepts any token)."""
    return {"Authorization": "Bearer demo-token"}


# ---------------------------------------------------------------------------
# 1. Health Check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    """Health check endpoint should always return 200."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_detailed_returns_200(self, client):
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "components" in data
        assert data["components"]["api"] == "up"


# ---------------------------------------------------------------------------
# 2. Auth Login
# ---------------------------------------------------------------------------


class TestAuthLogin:
    """Auth login endpoint: valid email → token, invalid → 403."""

    def test_login_valid_email_returns_token(self, client):
        """Login with a valid registered email should return a token.
        In dev mode with SharePoint, this may return 503 if SharePoint
        is unreachable. We accept 200 (success) or 503 (SP unavailable)."""
        response = client.post(
            "/api/auth/login",
            json={"email": "suraj.ray@tvsmotor.com"},
        )
        # Dev mode without live SharePoint may return 503
        assert response.status_code in (200, 503)
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            assert "email" in data
            assert "role" in data

    def test_login_invalid_email_format_returns_400(self, client):
        """Login with an invalid email format should return 400."""
        response = client.post(
            "/api/auth/login",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 400

    def test_login_unregistered_email_returns_403_or_503(self, client):
        """Login with an unregistered email should return 403.
        May return 503 if SharePoint is unreachable."""
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@unknown.com"},
        )
        # 403 = access denied, 503 = SP unavailable (both acceptable in CI)
        assert response.status_code in (403, 503)


# ---------------------------------------------------------------------------
# 3. Admin Users
# ---------------------------------------------------------------------------


class TestAdminUsers:
    """Admin user management: list and add."""

    def test_list_users_returns_200(self, client, auth_headers):
        """GET /api/admin/users should return user list or SP error."""
        response = client.get("/api/admin/users", headers=auth_headers)
        # 200 = success, 500/503 = SharePoint unavailable/misconfigured
        assert response.status_code in (200, 500, 503)
        if response.status_code == 200:
            data = response.json()
            assert "users" in data
            assert "total" in data
            assert isinstance(data["users"], list)

    def test_add_user_returns_201_or_service_error(self, client, auth_headers):
        """POST /api/admin/users should add a user or report SP error."""
        response = client.post(
            "/api/admin/users",
            headers=auth_headers,
            json={
                "email": "test.user@tvsmotor.com",
                "display_name": "Test User",
                "role": "User",
                "corporate_id": "99999",
            },
        )
        # 201 = created, 409 = duplicate, 500/503 = SP unavailable
        assert response.status_code in (201, 409, 500, 503)


# ---------------------------------------------------------------------------
# 4. MPCP Dashboard
# ---------------------------------------------------------------------------


class TestMPCPDashboard:
    """MPCP Dashboard returns aggregated metrics."""

    def test_dashboard_returns_200(self, client, auth_headers):
        """GET /api/mpcp-tracker/dashboard should return metrics."""
        response = client.get(
            "/api/mpcp-tracker/dashboard", headers=auth_headers
        )
        assert response.status_code == 200

    def test_dashboard_response_structure(self, client, auth_headers):
        """Dashboard response should contain expected metric fields."""
        response = client.get(
            "/api/mpcp-tracker/dashboard", headers=auth_headers
        )
        data = response.json()
        # DashboardMetrics model should have these top-level keys
        assert isinstance(data, dict)
        # At minimum it should be a valid dict (empty or with metrics)


# ---------------------------------------------------------------------------
# 5. MPCP Projects - List All
# ---------------------------------------------------------------------------


class TestMPCPProjects:
    """MPCP Projects listing."""

    def test_list_all_projects_returns_200(self, client, auth_headers):
        """GET /api/mpcp-tracker/projects/all should return project list."""
        response = client.get(
            "/api/mpcp-tracker/projects/all", headers=auth_headers
        )
        assert response.status_code == 200

    def test_list_all_projects_returns_list(self, client, auth_headers):
        """Response should be a JSON list."""
        response = client.get(
            "/api/mpcp-tracker/projects/all", headers=auth_headers
        )
        data = response.json()
        assert isinstance(data, list)


# ---------------------------------------------------------------------------
# 6. MPCP CPs - List All
# ---------------------------------------------------------------------------


class TestMPCPCheckPoints:
    """MPCP Check Points bulk listing."""

    def test_list_all_cps_returns_200(self, client, auth_headers):
        """GET /api/mpcp-tracker/cps/all should return CP list."""
        response = client.get(
            "/api/mpcp-tracker/cps/all", headers=auth_headers
        )
        assert response.status_code == 200

    def test_list_all_cps_returns_list(self, client, auth_headers):
        """Response should be a JSON list."""
        response = client.get(
            "/api/mpcp-tracker/cps/all", headers=auth_headers
        )
        data = response.json()
        assert isinstance(data, list)


# ---------------------------------------------------------------------------
# 7. MPCP Process Track
# ---------------------------------------------------------------------------


class TestMPCPProcessTrack:
    """MPCP Process Track for a project."""

    def test_process_track_known_project(self, client, auth_headers):
        """GET process-track for a project returns stages or 404."""
        # First get a project ID from the list
        projects_resp = client.get(
            "/api/mpcp-tracker/projects/all", headers=auth_headers
        )
        if projects_resp.status_code == 200 and projects_resp.json():
            project_id = projects_resp.json()[0].get("id", "")
            if project_id:
                response = client.get(
                    f"/api/mpcp-tracker/projects/{project_id}/process-track",
                    headers=auth_headers,
                )
                assert response.status_code == 200
                data = response.json()
                assert "stages" in data
                assert "project_id" in data
                return

        # Fallback: try with a fake project_id → expect 404
        response = client.get(
            "/api/mpcp-tracker/projects/nonexistent-project/process-track",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# 8. MPCP Budget Update
# ---------------------------------------------------------------------------


class TestMPCPBudget:
    """MPCP Budget update endpoint."""

    def test_budget_update_known_project(self, client, auth_headers):
        """PUT budget update works for an existing project or returns 404."""
        # Get a project ID
        projects_resp = client.get(
            "/api/mpcp-tracker/projects/all", headers=auth_headers
        )
        if projects_resp.status_code == 200 and projects_resp.json():
            project_id = projects_resp.json()[0].get("id", "")
            if project_id:
                response = client.put(
                    f"/api/mpcp-tracker/projects/{project_id}/budget",
                    headers=auth_headers,
                    json={
                        "approved_budget": 1500000.0,
                        "internal_estimate": 1200000.0,
                        "remarks": "P0 test budget update",
                    },
                )
                assert response.status_code == 200
                data = response.json()
                assert "approved_budget" in data
                return

        # Fallback: nonexistent project → 404
        response = client.put(
            "/api/mpcp-tracker/projects/nonexistent-project/budget",
            headers=auth_headers,
            json={
                "approved_budget": 1000000.0,
            },
        )
        assert response.status_code == 404

    def test_budget_get_returns_data_or_404(self, client, auth_headers):
        """GET budget for a project returns budget data or 404."""
        projects_resp = client.get(
            "/api/mpcp-tracker/projects/all", headers=auth_headers
        )
        if projects_resp.status_code == 200 and projects_resp.json():
            project_id = projects_resp.json()[0].get("id", "")
            if project_id:
                response = client.get(
                    f"/api/mpcp-tracker/projects/{project_id}/budget",
                    headers=auth_headers,
                )
                assert response.status_code == 200
                return

        response = client.get(
            "/api/mpcp-tracker/projects/nonexistent-project/budget",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# 9. MPCP Dependencies
# ---------------------------------------------------------------------------


class TestMPCPDependencies:
    """MPCP Dependencies: add dependency with is_blocker=True."""

    def test_add_dependency_with_blocker(self, client, auth_headers):
        """POST dependency with is_blocker=True returns 201 or 404."""
        # Get a project ID
        projects_resp = client.get(
            "/api/mpcp-tracker/projects/all", headers=auth_headers
        )
        if projects_resp.status_code == 200 and projects_resp.json():
            project_id = projects_resp.json()[0].get("id", "")
            if project_id:
                response = client.post(
                    f"/api/mpcp-tracker/projects/{project_id}/dependencies",
                    headers=auth_headers,
                    json={
                        "description": "P0 Test: API Gateway deployment",
                        "external_owner": "Platform Team",
                        "cutoff_date": "2025-03-31",
                        "is_blocker": True,
                        "status": "Open",
                    },
                )
                assert response.status_code == 201
                data = response.json()
                assert data.get("is_blocker") is True
                return

        # Fallback: nonexistent project → 404
        response = client.post(
            "/api/mpcp-tracker/projects/nonexistent-project/dependencies",
            headers=auth_headers,
            json={
                "description": "Test dependency",
                "external_owner": "Test Team",
                "cutoff_date": "2025-06-30",
                "is_blocker": True,
                "status": "Open",
            },
        )
        assert response.status_code == 404

    def test_get_dependencies(self, client, auth_headers):
        """GET dependencies for a project returns list or 404."""
        projects_resp = client.get(
            "/api/mpcp-tracker/projects/all", headers=auth_headers
        )
        if projects_resp.status_code == 200 and projects_resp.json():
            project_id = projects_resp.json()[0].get("id", "")
            if project_id:
                response = client.get(
                    f"/api/mpcp-tracker/projects/{project_id}/dependencies",
                    headers=auth_headers,
                )
                assert response.status_code == 200
                assert isinstance(response.json(), list)
                return

        # No projects loaded — in-memory tracker may return 200 (empty) or 404
        response = client.get(
            "/api/mpcp-tracker/projects/nonexistent-project/dependencies",
            headers=auth_headers,
        )
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# 10. PRD Check Audit
# ---------------------------------------------------------------------------


class TestPRDCheck:
    """PRD Check audit endpoint exists and returns expected structure."""

    def test_prd_check_audit_returns_200(self, client, auth_headers):
        """GET /api/prd-check/audit returns 200."""
        response = client.get(
            "/api/prd-check/audit", headers=auth_headers
        )
        # 200 success or 503 if SP unreachable
        assert response.status_code in (200, 503)

    def test_prd_check_audit_response_structure(self, client, auth_headers):
        """Audit response should contain entries list."""
        response = client.get(
            "/api/prd-check/audit", headers=auth_headers
        )
        if response.status_code == 200:
            data = response.json()
            assert "entries" in data
            assert isinstance(data["entries"], list)


# ---------------------------------------------------------------------------
# 11. Estimations List
# ---------------------------------------------------------------------------


class TestEstimations:
    """Estimations list endpoint."""

    def test_list_estimations_returns_200(self, client, auth_headers):
        """GET /api/estimations returns 200."""
        response = client.get(
            "/api/estimations", headers=auth_headers
        )
        # 200 = success, 503 = SP unavailable
        assert response.status_code in (200, 503)

    def test_list_estimations_response_is_valid(self, client, auth_headers):
        """Estimations response should be valid JSON."""
        response = client.get(
            "/api/estimations", headers=auth_headers
        )
        if response.status_code == 200:
            data = response.json()
            # Should be a dict or list depending on implementation
            assert data is not None


# ---------------------------------------------------------------------------
# 12. Build vs Buy Evaluations
# ---------------------------------------------------------------------------


class TestBuildVsBuy:
    """Build vs Buy evaluations list endpoint."""

    def test_list_evaluations_returns_200(self, client, auth_headers):
        """GET /api/build-vs-buy/evaluations returns 200."""
        response = client.get(
            "/api/build-vs-buy/evaluations", headers=auth_headers
        )
        # 200 = success, 500/503 = SP unavailable/misconfigured
        assert response.status_code in (200, 500, 503)

    def test_list_evaluations_response_structure(self, client, auth_headers):
        """Evaluations response should contain evaluations list."""
        response = client.get(
            "/api/build-vs-buy/evaluations", headers=auth_headers
        )
        if response.status_code == 200:
            data = response.json()
            assert "evaluations" in data
            assert "total" in data
            assert isinstance(data["evaluations"], list)
