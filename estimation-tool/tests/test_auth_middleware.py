"""Unit tests for auth middleware (app/middleware/auth.py).

Tests cover:
- Bearer token extraction from Authorization header
- SSO token (JWT) decoding and validation
- Identity extraction from JWT claims
- Allowlist lookup against Users.xlsx via SharePoint client
- Role-based access (Admin vs User)
- Access denial for non-allowlisted users
- require_admin dependency enforcement
"""

import time
from unittest.mock import AsyncMock, patch

import jwt
import pytest
import pytest_asyncio

from app.middleware.auth import (
    AuthenticatedUser,
    _check_allowlist,
    _decode_sso_token,
    _extract_bearer_token,
    _extract_identity_from_claims,
    get_current_user,
    require_admin,
)
from app.models.schemas import UserIdentity, UserRole
from app.services.sharepoint_client import SharePointClient, SharePointUnavailableError
from fastapi import HTTPException


# --- Test Fixtures ---

TEST_SECRET = "test-secret-key-for-unit-tests"

SAMPLE_USERS_XLSX_ROWS = [
    ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"],
    ["EMP001", "alice@corp.com", "Alice Smith", "Admin", "system", "2024-01-01", "true"],
    ["EMP002", "bob@corp.com", "Bob Jones", "User", "alice@corp.com", "2024-01-15", "true"],
    ["EMP003", "charlie@corp.com", "Charlie Brown", "User", "alice@corp.com", "2024-02-01", "false"],
]


def _make_token(claims: dict, secret: str = TEST_SECRET, exp_offset: int = 3600) -> str:
    """Create a JWT token with the given claims."""
    payload = {**claims, "exp": int(time.time()) + exp_offset}
    return jwt.encode(payload, secret, algorithm="HS256")


# --- Tests for _extract_bearer_token ---


class TestExtractBearerToken:
    def test_valid_bearer_token(self):
        token = _extract_bearer_token("Bearer my-token-value")
        assert token == "my-token-value"

    def test_bearer_case_insensitive(self):
        token = _extract_bearer_token("bearer my-token-value")
        assert token == "my-token-value"

    def test_missing_header_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            _extract_bearer_token(None)
        assert exc_info.value.status_code == 401
        assert "Missing Authorization header" in exc_info.value.detail

    def test_empty_header_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            _extract_bearer_token("")
        assert exc_info.value.status_code == 401

    def test_no_bearer_prefix_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            _extract_bearer_token("Basic some-credentials")
        assert exc_info.value.status_code == 401
        assert "Invalid Authorization header format" in exc_info.value.detail

    def test_only_bearer_no_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            _extract_bearer_token("Bearer")
        assert exc_info.value.status_code == 401


# --- Tests for _decode_sso_token ---


class TestDecodeSsoToken:
    @patch.dict(
        "os.environ",
        {"SSO_SECRET": TEST_SECRET, "SSO_ISSUER": "", "SSO_AUDIENCE": "", "SSO_JWKS_URL": ""},
    )
    def test_valid_token_decodes_successfully(self):
        token = _make_token({"sub": "user123", "email": "user@corp.com"})
        claims = _decode_sso_token(token)
        assert claims["sub"] == "user123"
        assert claims["email"] == "user@corp.com"

    @patch.dict(
        "os.environ",
        {"SSO_SECRET": TEST_SECRET, "SSO_ISSUER": "", "SSO_AUDIENCE": "", "SSO_JWKS_URL": ""},
    )
    def test_expired_token_raises_401(self):
        token = _make_token({"sub": "user123"}, exp_offset=-3600)
        with pytest.raises(HTTPException) as exc_info:
            _decode_sso_token(token)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    @patch.dict(
        "os.environ",
        {"SSO_SECRET": TEST_SECRET, "SSO_ISSUER": "", "SSO_AUDIENCE": "", "SSO_JWKS_URL": ""},
    )
    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            _decode_sso_token("not-a-valid-jwt")
        assert exc_info.value.status_code == 401
        assert "Invalid authentication token" in exc_info.value.detail

    @patch.dict(
        "os.environ",
        {"SSO_SECRET": "wrong-secret", "SSO_ISSUER": "", "SSO_AUDIENCE": "", "SSO_JWKS_URL": ""},
    )
    def test_wrong_secret_raises_401(self):
        token = _make_token({"sub": "user123"}, secret="correct-secret")
        with pytest.raises(HTTPException) as exc_info:
            _decode_sso_token(token)
        assert exc_info.value.status_code == 401


# --- Tests for _extract_identity_from_claims ---


class TestExtractIdentityFromClaims:
    def test_azure_ad_claims(self):
        claims = {"oid": "obj-123", "email": "user@corp.com", "name": "Test User"}
        identity = _extract_identity_from_claims(claims)
        assert identity.corporateId == "obj-123"
        assert identity.email == "user@corp.com"
        assert identity.displayName == "Test User"

    def test_standard_jwt_claims(self):
        claims = {"sub": "sub-456", "preferred_username": "user@corp.com", "name": "Another User"}
        identity = _extract_identity_from_claims(claims)
        assert identity.corporateId == "sub-456"
        assert identity.email == "user@corp.com"
        assert identity.displayName == "Another User"

    def test_upn_fallback(self):
        claims = {"sub": "sub-789", "upn": "user@corp.com"}
        identity = _extract_identity_from_claims(claims)
        assert identity.email == "user@corp.com"

    def test_missing_both_email_and_id_raises_401(self):
        claims = {"name": "No ID User"}
        with pytest.raises(HTTPException) as exc_info:
            _extract_identity_from_claims(claims)
        assert exc_info.value.status_code == 401
        assert "missing required identity claims" in exc_info.value.detail.lower()

    def test_corporate_id_claim(self):
        claims = {"corporate_id": "CORP-001", "email": "emp@corp.com"}
        identity = _extract_identity_from_claims(claims)
        assert identity.corporateId == "CORP-001"


# --- Tests for _check_allowlist ---


class TestCheckAllowlist:
    @pytest.mark.asyncio
    async def test_user_found_by_email(self):
        client = AsyncMock(spec=SharePointClient)
        client.read_workbook = AsyncMock(return_value=SAMPLE_USERS_XLSX_ROWS)

        identity = UserIdentity(corporateId="", email="alice@corp.com", displayName="Alice")
        entry = await _check_allowlist(identity, client)

        assert entry.email == "alice@corp.com"
        assert entry.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_user_found_by_corporate_id(self):
        client = AsyncMock(spec=SharePointClient)
        client.read_workbook = AsyncMock(return_value=SAMPLE_USERS_XLSX_ROWS)

        identity = UserIdentity(corporateId="EMP002", email="", displayName="Bob")
        entry = await _check_allowlist(identity, client)

        assert entry.corporateId == "EMP002"
        assert entry.role == UserRole.USER

    @pytest.mark.asyncio
    async def test_user_not_in_allowlist_raises_403(self):
        client = AsyncMock(spec=SharePointClient)
        client.read_workbook = AsyncMock(return_value=SAMPLE_USERS_XLSX_ROWS)

        identity = UserIdentity(corporateId="EMP999", email="unknown@corp.com", displayName="Unknown")

        with pytest.raises(HTTPException) as exc_info:
            await _check_allowlist(identity, client)
        assert exc_info.value.status_code == 403
        assert "Access Denied" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_inactive_user_raises_403(self):
        client = AsyncMock(spec=SharePointClient)
        client.read_workbook = AsyncMock(return_value=SAMPLE_USERS_XLSX_ROWS)

        identity = UserIdentity(corporateId="EMP003", email="charlie@corp.com", displayName="Charlie")

        with pytest.raises(HTTPException) as exc_info:
            await _check_allowlist(identity, client)
        assert exc_info.value.status_code == 403
        assert "Access Denied" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_sharepoint_unavailable_raises_503(self):
        client = AsyncMock(spec=SharePointClient)
        client.read_workbook = AsyncMock(side_effect=SharePointUnavailableError("unavailable"))

        identity = UserIdentity(corporateId="EMP001", email="alice@corp.com", displayName="Alice")

        with pytest.raises(HTTPException) as exc_info:
            await _check_allowlist(identity, client)
        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_empty_allowlist_raises_403(self):
        client = AsyncMock(spec=SharePointClient)
        client.read_workbook = AsyncMock(return_value=[])

        identity = UserIdentity(corporateId="EMP001", email="alice@corp.com", displayName="Alice")

        with pytest.raises(HTTPException) as exc_info:
            await _check_allowlist(identity, client)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_case_insensitive_email_matching(self):
        client = AsyncMock(spec=SharePointClient)
        client.read_workbook = AsyncMock(return_value=SAMPLE_USERS_XLSX_ROWS)

        identity = UserIdentity(corporateId="", email="ALICE@CORP.COM", displayName="Alice")
        entry = await _check_allowlist(identity, client)

        assert entry.role == UserRole.ADMIN


# --- Tests for get_current_user (integration) ---


class TestGetCurrentUser:
    @pytest.mark.asyncio
    @patch.dict(
        "os.environ",
        {"SSO_SECRET": TEST_SECRET, "SSO_ISSUER": "", "SSO_AUDIENCE": "", "SSO_JWKS_URL": ""},
    )
    async def test_full_auth_flow_success(self):
        token = _make_token({"sub": "EMP001", "email": "alice@corp.com", "name": "Alice Smith"})

        client = AsyncMock(spec=SharePointClient)
        client.read_workbook = AsyncMock(return_value=SAMPLE_USERS_XLSX_ROWS)

        user = await get_current_user(
            authorization=f"Bearer {token}",
            sharepoint_client=client,
        )

        assert isinstance(user, AuthenticatedUser)
        assert user.email == "alice@corp.com"
        assert user.role == UserRole.ADMIN
        assert user.is_admin is True

    @pytest.mark.asyncio
    @patch.dict(
        "os.environ",
        {"SSO_SECRET": TEST_SECRET, "SSO_ISSUER": "", "SSO_AUDIENCE": "", "SSO_JWKS_URL": ""},
    )
    async def test_non_allowlisted_user_gets_403(self):
        token = _make_token({"sub": "EMP999", "email": "hacker@external.com", "name": "Hacker"})

        client = AsyncMock(spec=SharePointClient)
        client.read_workbook = AsyncMock(return_value=SAMPLE_USERS_XLSX_ROWS)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                authorization=f"Bearer {token}",
                sharepoint_client=client,
            )
        assert exc_info.value.status_code == 403
        assert "Access Denied" in exc_info.value.detail


# --- Tests for require_admin ---


class TestRequireAdmin:
    @pytest.mark.asyncio
    async def test_admin_user_passes(self):
        admin_user = AuthenticatedUser(
            identity=UserIdentity(corporateId="EMP001", email="alice@corp.com", displayName="Alice"),
            role=UserRole.ADMIN,
        )
        result = await require_admin(user=admin_user)
        assert result is admin_user

    @pytest.mark.asyncio
    async def test_non_admin_user_raises_403(self):
        regular_user = AuthenticatedUser(
            identity=UserIdentity(corporateId="EMP002", email="bob@corp.com", displayName="Bob"),
            role=UserRole.USER,
        )
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(user=regular_user)
        assert exc_info.value.status_code == 403
        assert "Admin role required" in exc_info.value.detail
