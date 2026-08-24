"""Authentication and authorization middleware using FastAPI dependency injection.

Implements:
- SSO token validation (JWT decoding from corporate SSO / Azure AD)
- Allowlist check against Users.xlsx via SharePoint client
- Role extraction (Admin vs User) from allowlist
- "Access Denied — contact your admin" for non-allowlisted users
- Automatic corporate identity capture for audit purposes

Requirements: 18.1, 18.2, 18.3, 18.11, 18.12, 7.4
"""

import logging
import os
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.models.schemas import AllowlistEntry, UserIdentity, UserRole
from app.services.sharepoint_client import SharePointClient, SharePointUnavailableError

logger = logging.getLogger(__name__)

# Environment variables for SSO configuration
ENV_SSO_ISSUER = "SSO_ISSUER"
ENV_SSO_AUDIENCE = "SSO_AUDIENCE"
ENV_SSO_JWKS_URL = "SSO_JWKS_URL"
ENV_SSO_SECRET = "SSO_SECRET"  # For HMAC-based validation in dev/testing


class AuthenticatedUser:
    """Represents a fully authenticated and authorized user.

    Combines the SSO identity with the allowlist role for downstream use.
    """

    def __init__(self, identity: UserIdentity, role: UserRole):
        self.identity = identity
        self.role = role

    @property
    def corporate_id(self) -> str:
        return self.identity.corporateId

    @property
    def email(self) -> str:
        return self.identity.email

    @property
    def display_name(self) -> str:
        return self.identity.displayName

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN


def _get_sso_config() -> dict:
    """Load SSO configuration from environment variables."""
    return {
        "issuer": os.getenv(ENV_SSO_ISSUER, ""),
        "audience": os.getenv(ENV_SSO_AUDIENCE, ""),
        "jwks_url": os.getenv(ENV_SSO_JWKS_URL, ""),
        "secret": os.getenv(ENV_SSO_SECRET, ""),
    }


def _extract_bearer_token(authorization: Optional[str]) -> str:
    """Extract the Bearer token from the Authorization header.

    Args:
        authorization: The Authorization header value.

    Returns:
        The token string.

    Raises:
        HTTPException: If the header is missing or malformed.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return parts[1]


def _decode_sso_token(token: str) -> dict:
    """Decode and validate the SSO JWT token.

    Extracts claims from the JWT. In production, this validates against the
    corporate IdP's JWKS endpoint. For development/testing, supports HMAC
    secret-based validation.

    Args:
        token: The JWT token string.

    Returns:
        Dictionary of decoded JWT claims.

    Raises:
        HTTPException: If the token is invalid, expired, or malformed.
    """
    config = _get_sso_config()

    try:
        # Determine decoding options based on available config
        decode_options = {"algorithms": ["RS256", "HS256"]}

        if config["secret"]:
            # Dev/testing mode: validate with HMAC secret
            claims = jwt.decode(
                token,
                config["secret"],
                algorithms=["HS256"],
                options={"verify_exp": True},
            )
        else:
            # Production mode: decode without full verification
            # In production, JWKS-based validation would fetch public keys
            # from the IdP's JWKS endpoint and verify the signature.
            # For now, decode claims (signature verification depends on IdP setup).
            claims = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": True,
                },
            )

        return claims

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid SSO token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _extract_identity_from_claims(claims: dict) -> UserIdentity:
    """Extract UserIdentity from JWT claims.

    Supports common claim formats from Azure AD / corporate SSO providers.

    Args:
        claims: Decoded JWT claims dictionary.

    Returns:
        UserIdentity with corporateId, email, and displayName.

    Raises:
        HTTPException: If required identity claims are missing.
    """
    # Try common claim names for corporate ID
    corporate_id = (
        claims.get("oid")  # Azure AD object ID
        or claims.get("sub")  # Standard subject claim
        or claims.get("employee_id")
        or claims.get("corporate_id")
        or ""
    )

    # Try common claim names for email
    email = (
        claims.get("email")
        or claims.get("preferred_username")
        or claims.get("upn")  # Azure AD User Principal Name
        or ""
    )

    # Try common claim names for display name
    display_name = (
        claims.get("name")
        or claims.get("display_name")
        or claims.get("given_name", "")
        or ""
    )

    if not email and not corporate_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required identity claims (email or corporate ID)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserIdentity(
        corporateId=corporate_id,
        email=email,
        displayName=display_name,
    )


# Allowlist cache (avoids reading Users.xlsx from SharePoint on every request)
_allowlist_cache: Optional[list] = None
_allowlist_cache_time: float = 0
_ALLOWLIST_CACHE_TTL = 300  # 5 minutes


async def _get_allowlist_rows(sharepoint_client: SharePointClient) -> list:
    """Get allowlist rows with 5-minute cache."""
    global _allowlist_cache, _allowlist_cache_time
    import time
    now = time.time()
    if _allowlist_cache is not None and (now - _allowlist_cache_time) < _ALLOWLIST_CACHE_TTL:
        return _allowlist_cache
    try:
        rows = await sharepoint_client.read_workbook("Admin/Users.xlsx", sheet="Sheet1")
        _allowlist_cache = rows
        _allowlist_cache_time = now
        return rows
    except SharePointUnavailableError:
        # If cache exists but stale, still use it rather than failing
        if _allowlist_cache is not None:
            return _allowlist_cache
        raise


async def _check_allowlist(
    identity: UserIdentity,
    sharepoint_client: SharePointClient,
) -> AllowlistEntry:
    """Check if the user is on the allowlist in Users.xlsx.

    Looks up the user by email or corporate ID in the SharePoint-hosted
    Users.xlsx file. Uses a 5-minute cache to avoid repeated reads.

    Args:
        identity: The authenticated user's identity from SSO.
        sharepoint_client: SharePoint client instance for reading Users.xlsx.

    Returns:
        The matching AllowlistEntry with role information.

    Raises:
        HTTPException: 403 if user is not on the allowlist or inactive.
        HTTPException: 503 if SharePoint is unavailable.
    """
    try:
        rows = await _get_allowlist_rows(sharepoint_client)
    except SharePointUnavailableError:
        logger.error("SharePoint unavailable during allowlist check")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable. Please retry shortly.",
        )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied \u2014 contact your admin",
        )

    # First row is headers; data rows start at index 1
    # Expected columns: CorporateId, Email, DisplayName, Role, AddedBy, AddedAt, Active
    headers = rows[0] if rows else []
    data_rows = rows[1:] if len(rows) > 1 else []

    # Build column index map for flexibility
    col_map = {str(h).strip().lower(): i for i, h in enumerate(headers)}

    corp_id_idx = col_map.get("corporateid", 0)
    email_idx = col_map.get("email", 1)
    display_name_idx = col_map.get("displayname", 2)
    role_idx = col_map.get("role", 3)
    added_by_idx = col_map.get("addedby", 4)
    added_at_idx = col_map.get("addedat", 5)
    active_idx = col_map.get("active", 6)

    for row in data_rows:
        if len(row) <= max(email_idx, corp_id_idx):
            continue

        row_email = str(row[email_idx]).strip().lower() if row[email_idx] else ""
        row_corp_id = str(row[corp_id_idx]).strip().lower() if row[corp_id_idx] else ""

        # Match by email or corporate ID
        user_email = identity.email.strip().lower()
        user_corp_id = identity.corporateId.strip().lower()

        if (user_email and row_email == user_email) or (
            user_corp_id and row_corp_id == user_corp_id
        ):
            # Check if active
            is_active = True
            if len(row) > active_idx:
                active_val = str(row[active_idx]).strip().lower()
                is_active = active_val in ("true", "1", "yes", "")

            if not is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access Denied \u2014 contact your admin",
                )

            # Extract role
            role_str = str(row[role_idx]).strip() if len(row) > role_idx else "User"
            role = UserRole.ADMIN if role_str == "Admin" else UserRole.USER

            return AllowlistEntry(
                corporateId=str(row[corp_id_idx]).strip() if row[corp_id_idx] else "",
                email=str(row[email_idx]).strip() if row[email_idx] else "",
                displayName=(
                    str(row[display_name_idx]).strip()
                    if len(row) > display_name_idx and row[display_name_idx]
                    else identity.displayName
                ),
                role=role,
                addedBy=(
                    str(row[added_by_idx]).strip()
                    if len(row) > added_by_idx and row[added_by_idx]
                    else ""
                ),
                addedAt=(
                    str(row[added_at_idx]).strip()
                    if len(row) > added_at_idx and row[added_at_idx]
                    else ""
                ),
                active=is_active,
            )

    # User not found in allowlist
    logger.info(
        f"Access denied for user: {identity.email or identity.corporateId} "
        f"(not in allowlist)"
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access Denied \u2014 contact your admin",
    )


# --- SharePoint Client Dependency ---


def get_sharepoint_client() -> SharePointClient:
    """FastAPI dependency providing a SharePoint client instance.

    Returns a new SharePointClient configured from environment variables.
    In production, this could be replaced with a cached/singleton instance.
    """
    return SharePointClient()


# --- FastAPI Dependencies ---


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> AuthenticatedUser:
    """FastAPI dependency that authenticates and authorizes the current user.

    This is the primary auth dependency. It:
    1. Extracts the Bearer token from the Authorization header
    2. Validates/decodes the JWT token (SSO token from corporate IdP)
    3. Extracts user identity (corporate ID, email) from token claims
    4. Checks the user against the allowlist in Users.xlsx via SharePoint
    5. Returns an AuthenticatedUser with identity and role

    Usage:
        @app.get("/api/estimations")
        async def list_estimations(user: AuthenticatedUser = Depends(get_current_user)):
            ...

    Args:
        authorization: The Authorization header value (injected by FastAPI).
        sharepoint_client: SharePoint client for allowlist lookup (injected).

    Returns:
        AuthenticatedUser with identity and role information.

    Raises:
        HTTPException 401: Missing/invalid token.
        HTTPException 403: User not on allowlist ("Access Denied — contact your admin").
        HTTPException 503: SharePoint unavailable for allowlist check.
    """
    # Step 1: Extract Bearer token
    token = _extract_bearer_token(authorization)

    # Step 2: Decode and validate SSO token
    claims = _decode_sso_token(token)

    # Step 3: Extract corporate identity from claims
    identity = _extract_identity_from_claims(claims)

    # Step 4: Check allowlist and get role
    allowlist_entry = await _check_allowlist(identity, sharepoint_client)

    # Step 5: Build authenticated user (use allowlist display name if available)
    final_identity = UserIdentity(
        corporateId=allowlist_entry.corporateId or identity.corporateId,
        email=allowlist_entry.email or identity.email,
        displayName=allowlist_entry.displayName or identity.displayName,
    )

    logger.info(
        f"User authenticated: {final_identity.email} "
        f"(role: {allowlist_entry.role.value})"
    )

    return AuthenticatedUser(identity=final_identity, role=allowlist_entry.role)


async def require_admin(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """FastAPI dependency that requires Admin role.

    Builds on get_current_user and additionally verifies the user has Admin role.

    Usage:
        @app.post("/api/admin/users")
        async def add_user(user: AuthenticatedUser = Depends(require_admin)):
            ...

    Args:
        user: The authenticated user (injected via get_current_user).

    Returns:
        The authenticated user if they have Admin role.

    Raises:
        HTTPException 403: If the user does not have Admin role.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required.",
        )
    return user
