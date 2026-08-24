"""Unit tests for admin user management endpoints (app/routers/admin_users.py).

Tests POST /api/admin/users, DELETE /api/admin/users/{user_id}, and
GET /api/admin/users endpoints including:
- Admin-only access enforcement (403 for non-admin users)
- Adding users to the allowlist with role assignment
- Removing users with last-admin protection
- Listing allowlisted users
- Email validation and duplicate detection

Requirements: 18.3, 18.4, 18.13, 18.14, 18.15
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.auth import AuthenticatedUser, get_sharepoint_client, require_admin
from app.models.schemas import UserIdentity, UserRole
from app.routers.admin_users import router
from app.services.sharepoint_client import (
    SharePointClient,
    SharePointError,
    SharePointUnavailableError,
)

# --- Test Setup ---

app = FastAPI()
app.include_router(router)


def _make_admin_user() -> AuthenticatedUser:
    """Create a mock admin user for testing."""
    identity = UserIdentity(
        corporateId="ADMIN001",
        email="admin@company.com",
        displayName="Admin User",
    )
    return AuthenticatedUser(identity=identity, role=UserRole.ADMIN)


def _make_regular_user() -> AuthenticatedUser:
    """Create a mock regular user for testing."""
    identity = UserIdentity(
        corporateId="USER001",
        email="user@company.com",
        displayName="Regular User",
    )
    return AuthenticatedUser(identity=identity, role=UserRole.USER)


def _make_users_rows(users: list[dict]) -> list[list]:
    """Build Users.xlsx rows from user dicts.

    Args:
        users: List of dicts with keys: corporate_id, email, display_name, role, added_by, added_at, active.

    Returns:
        List of rows (first row is headers).
    """
    headers = ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"]
    rows = [headers]
    for u in users:
        rows.append([
            u.get("corporate_id", ""),
            u.get("email", ""),
            u.get("display_name", ""),
            u.get("role", "User"),
            u.get("added_by", ""),
            u.get("added_at", ""),
            u.get("active", "TRUE"),
        ])
    return rows


# --- Fixtures ---


@pytest.fixture
def mock_sharepoint():
    """Create a mock SharePoint client."""
    client = AsyncMock(spec=SharePointClient)
    return client


@pytest.fixture
def admin_client(mock_sharepoint):
    """Create a test client with admin auth override."""
    admin_user = _make_admin_user()

    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_sharepoint_client] = lambda: mock_sharepoint

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


# --- GET /api/admin/users Tests ---


class TestListUsers:
    """Tests for GET /api/admin/users endpoint."""

    def test_list_users_returns_active_users(self, admin_client, mock_sharepoint):
        """Admin can list all active users."""
        mock_sharepoint.read_workbook = AsyncMock(return_value=_make_users_rows([
            {"corporate_id": "EMP001", "email": "alice@company.com", "display_name": "Alice", "role": "Admin", "added_by": "system", "added_at": "2024-01-01", "active": "TRUE"},
            {"corporate_id": "EMP002", "email": "bob@company.com", "display_name": "Bob", "role": "User", "added_by": "admin@company.com", "added_at": "2024-02-01", "active": "TRUE"},
            {"corporate_id": "EMP003", "email": "charlie@company.com", "display_name": "Charlie", "role": "User", "added_by": "admin@company.com", "added_at": "2024-03-01", "active": "FALSE"},
        ]))

        response = admin_client.get("/api/admin/users")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Only active users
        assert len(data["users"]) == 2
        assert data["users"][0]["email"] == "alice@company.com"
        assert data["users"][0]["role"] == "Admin"
        assert data["users"][1]["email"] == "bob@company.com"
        assert data["users"][1]["role"] == "User"

    def test_list_users_empty_allowlist(self, admin_client, mock_sharepoint):
        """Returns empty list when no users exist."""
        mock_sharepoint.read_workbook = AsyncMock(return_value=[
            ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"]
        ])

        response = admin_client.get("/api/admin/users")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["users"] == []

    def test_list_users_sharepoint_unavailable(self, admin_client, mock_sharepoint):
        """Returns 503 when SharePoint is unavailable."""
        mock_sharepoint.read_workbook = AsyncMock(
            side_effect=SharePointUnavailableError("Unavailable")
        )

        response = admin_client.get("/api/admin/users")
        assert response.status_code == 503

    def test_list_users_requires_admin_role(self, mock_sharepoint):
        """Non-admin users get 403 when trying to list users."""
        from fastapi import HTTPException

        def deny_non_admin():
            raise HTTPException(status_code=403, detail="Insufficient permissions. Admin role required.")

        app.dependency_overrides[require_admin] = deny_non_admin
        app.dependency_overrides[get_sharepoint_client] = lambda: mock_sharepoint

        client = TestClient(app)
        response = client.get("/api/admin/users")
        assert response.status_code == 403

        app.dependency_overrides.clear()


# --- POST /api/admin/users Tests ---


class TestAddUser:
    """Tests for POST /api/admin/users endpoint."""

    def test_add_user_success(self, admin_client, mock_sharepoint):
        """Admin can add a new user to the allowlist."""
        mock_sharepoint.read_workbook = AsyncMock(return_value=_make_users_rows([
            {"corporate_id": "EMP001", "email": "admin@company.com", "display_name": "Admin", "role": "Admin", "added_by": "system", "added_at": "2024-01-01", "active": "TRUE"},
        ]))
        mock_sharepoint.append_row = AsyncMock()

        response = admin_client.post("/api/admin/users", json={
            "email": "newuser@company.com",
            "corporate_id": "EMP002",
            "display_name": "New User",
            "role": "User",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@company.com"
        assert data["display_name"] == "New User"
        assert data["role"] == "User"
        assert data["active"] is True
        mock_sharepoint.append_row.assert_called_once()

    def test_add_user_with_admin_role(self, admin_client, mock_sharepoint):
        """Admin can add a new user with Admin role."""
        mock_sharepoint.read_workbook = AsyncMock(return_value=_make_users_rows([]))
        mock_sharepoint.append_row = AsyncMock()

        response = admin_client.post("/api/admin/users", json={
            "email": "newadmin@company.com",
            "corporate_id": "EMP003",
            "display_name": "New Admin",
            "role": "Admin",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "Admin"

    def test_add_user_duplicate_email_rejected(self, admin_client, mock_sharepoint):
        """Adding a user with an already-existing active email returns 409."""
        mock_sharepoint.read_workbook = AsyncMock(return_value=_make_users_rows([
            {"corporate_id": "EMP001", "email": "existing@company.com", "display_name": "Existing", "role": "User", "added_by": "admin@company.com", "added_at": "2024-01-01", "active": "TRUE"},
        ]))

        response = admin_client.post("/api/admin/users", json={
            "email": "existing@company.com",
            "corporate_id": "EMP002",
            "display_name": "Duplicate",
            "role": "User",
        })

        assert response.status_code == 409

    def test_add_user_invalid_email_rejected(self, admin_client, mock_sharepoint):
        """Adding a user with an invalid email format returns 400."""
        response = admin_client.post("/api/admin/users", json={
            "email": "not-an-email",
            "corporate_id": "EMP002",
            "display_name": "Bad Email",
            "role": "User",
        })

        assert response.status_code == 400

    def test_add_user_sharepoint_write_failure(self, admin_client, mock_sharepoint):
        """Returns 500 when SharePoint write fails."""
        mock_sharepoint.read_workbook = AsyncMock(return_value=_make_users_rows([]))
        mock_sharepoint.append_row = AsyncMock(
            side_effect=SharePointError("Write failed")
        )

        response = admin_client.post("/api/admin/users", json={
            "email": "newuser@company.com",
            "corporate_id": "EMP002",
            "display_name": "New User",
            "role": "User",
        })

        assert response.status_code == 500

    def test_add_user_requires_admin_role(self, mock_sharepoint):
        """Non-admin users get 403 when trying to add users."""
        from fastapi import HTTPException

        def deny_non_admin():
            raise HTTPException(status_code=403, detail="Insufficient permissions. Admin role required.")

        app.dependency_overrides[require_admin] = deny_non_admin
        app.dependency_overrides[get_sharepoint_client] = lambda: mock_sharepoint

        client = TestClient(app)
        response = client.post("/api/admin/users", json={
            "email": "newuser@company.com",
            "corporate_id": "EMP002",
            "display_name": "New User",
            "role": "User",
        })
        assert response.status_code == 403

        app.dependency_overrides.clear()


# --- DELETE /api/admin/users/{user_id} Tests ---


class TestRemoveUser:
    """Tests for DELETE /api/admin/users/{user_id} endpoint."""

    def test_remove_user_success(self, admin_client, mock_sharepoint):
        """Admin can remove a user from the allowlist."""
        mock_sharepoint.read_workbook = AsyncMock(return_value=_make_users_rows([
            {"corporate_id": "EMP001", "email": "admin1@company.com", "display_name": "Admin 1", "role": "Admin", "added_by": "system", "added_at": "2024-01-01", "active": "TRUE"},
            {"corporate_id": "EMP002", "email": "admin2@company.com", "display_name": "Admin 2", "role": "Admin", "added_by": "system", "added_at": "2024-01-01", "active": "TRUE"},
            {"corporate_id": "EMP003", "email": "user@company.com", "display_name": "User", "role": "User", "added_by": "admin1@company.com", "added_at": "2024-02-01", "active": "TRUE"},
        ]))
        mock_sharepoint.write_rows = AsyncMock()

        response = admin_client.delete("/api/admin/users/user@company.com")
        assert response.status_code == 200
        data = response.json()
        assert "removed" in data["message"].lower() or "user@company.com" in data["message"]
        mock_sharepoint.write_rows.assert_called_once()

    def test_remove_user_by_corporate_id(self, admin_client, mock_sharepoint):
        """Admin can remove a user by corporate ID."""
        mock_sharepoint.read_workbook = AsyncMock(return_value=_make_users_rows([
            {"corporate_id": "EMP001", "email": "admin@company.com", "display_name": "Admin", "role": "Admin", "added_by": "system", "added_at": "2024-01-01", "active": "TRUE"},
            {"corporate_id": "EMP002", "email": "user@company.com", "display_name": "User", "role": "User", "added_by": "admin@company.com", "added_at": "2024-02-01", "active": "TRUE"},
        ]))
        mock_sharepoint.write_rows = AsyncMock()

        response = admin_client.delete("/api/admin/users/EMP002")
        assert response.status_code == 200

    def test_remove_user_not_found(self, admin_client, mock_sharepoint):
        """Returns 404 when user is not found in allowlist."""
        mock_sharepoint.read_workbook = AsyncMock(return_value=_make_users_rows([
            {"corporate_id": "EMP001", "email": "admin@company.com", "display_name": "Admin", "role": "Admin", "added_by": "system", "added_at": "2024-01-01", "active": "TRUE"},
        ]))

        response = admin_client.delete("/api/admin/users/nonexistent@company.com")
        assert response.status_code == 404

    def test_remove_last_admin_rejected(self, admin_client, mock_sharepoint):
        """Removing the last admin is rejected with 400 error.

        Requirements: 18.13 - Last admin protection
        """
        mock_sharepoint.read_workbook = AsyncMock(return_value=_make_users_rows([
            {"corporate_id": "EMP001", "email": "onlyadmin@company.com", "display_name": "Only Admin", "role": "Admin", "added_by": "system", "added_at": "2024-01-01", "active": "TRUE"},
            {"corporate_id": "EMP002", "email": "user@company.com", "display_name": "User", "role": "User", "added_by": "admin@company.com", "added_at": "2024-02-01", "active": "TRUE"},
        ]))

        response = admin_client.delete("/api/admin/users/onlyadmin@company.com")
        assert response.status_code == 400
        assert "last Admin" in response.json()["detail"] or "at least one Admin" in response.json()["detail"]

    def test_remove_admin_when_multiple_admins_succeeds(self, admin_client, mock_sharepoint):
        """Removing an admin succeeds when multiple admins exist.

        Requirements: 18.13 - Last admin protection allows removal if 2+ admins
        """
        mock_sharepoint.read_workbook = AsyncMock(return_value=_make_users_rows([
            {"corporate_id": "EMP001", "email": "admin1@company.com", "display_name": "Admin 1", "role": "Admin", "added_by": "system", "added_at": "2024-01-01", "active": "TRUE"},
            {"corporate_id": "EMP002", "email": "admin2@company.com", "display_name": "Admin 2", "role": "Admin", "added_by": "system", "added_at": "2024-01-01", "active": "TRUE"},
        ]))
        mock_sharepoint.write_rows = AsyncMock()

        response = admin_client.delete("/api/admin/users/admin1@company.com")
        assert response.status_code == 200

    def test_remove_user_sharepoint_unavailable(self, admin_client, mock_sharepoint):
        """Returns 503 when SharePoint is unavailable."""
        mock_sharepoint.read_workbook = AsyncMock(
            side_effect=SharePointUnavailableError("Unavailable")
        )

        response = admin_client.delete("/api/admin/users/user@company.com")
        assert response.status_code == 503

    def test_remove_user_requires_admin_role(self, mock_sharepoint):
        """Non-admin users get 403 when trying to remove users.

        Requirements: 18.15
        """
        from fastapi import HTTPException

        def deny_non_admin():
            raise HTTPException(status_code=403, detail="Insufficient permissions. Admin role required.")

        app.dependency_overrides[require_admin] = deny_non_admin
        app.dependency_overrides[get_sharepoint_client] = lambda: mock_sharepoint

        client = TestClient(app)
        response = client.delete("/api/admin/users/user@company.com")
        assert response.status_code == 403

        app.dependency_overrides.clear()
