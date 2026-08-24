"""Email-based login endpoint.

Simple auth flow: user enters corporate email → if found in Users.xlsx → issue JWT.
No password required (relies on internal network access + allowlist).
"""

import logging
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.sharepoint_client import SharePointClient, FOLDER_ADMIN

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

USERS_FILENAME = f"{FOLDER_ADMIN}/Users.xlsx"


class LoginRequest(BaseModel):
    """Login request - just email."""
    email: str = Field(..., min_length=3, description="Corporate email address")


class LoginResponse(BaseModel):
    """Login response with JWT token and user info."""
    token: str
    email: str
    display_name: str
    role: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user by email against Users.xlsx allowlist.

    If email is found and active, issues a JWT token with user identity.
    """
    email = request.email.strip().lower()

    if not email or "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid email address.",
        )

    # Read Users.xlsx from SharePoint
    sp = SharePointClient()
    try:
        rows = await sp.read_workbook(USERS_FILENAME, sheet="Sheet1")
    except Exception as e:
        logger.error(f"Login failed - cannot read Users.xlsx: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable. Please try again.",
        )

    if not rows or len(rows) < 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied. No users configured. Please contact suraj.ray@tvsmotor.com for access.",
        )

    # Parse headers
    headers = rows[0]
    col_map = {str(h).strip().lower(): i for i, h in enumerate(headers)}
    email_idx = col_map.get("email", 1)
    display_name_idx = col_map.get("displayname", 2)
    role_idx = col_map.get("role", 3)
    corp_id_idx = col_map.get("corporateid", 0)
    active_idx = col_map.get("active", 6)

    # Search for user
    for row in rows[1:]:
        if not row or len(row) <= email_idx:
            continue

        row_email = str(row[email_idx]).strip().lower() if row[email_idx] else ""
        if row_email != email:
            continue

        # Found — check if active
        is_active = True
        if len(row) > active_idx:
            active_val = str(row[active_idx]).strip().lower()
            if active_val in ("false", "0", "no"):
                is_active = False

        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact suraj.ray@tvsmotor.com for access.",
            )

        # Extract user info
        display_name = str(row[display_name_idx]).strip() if len(row) > display_name_idx and row[display_name_idx] else email.split("@")[0]
        role = str(row[role_idx]).strip() if len(row) > role_idx and row[role_idx] else "User"
        corp_id = str(row[corp_id_idx]).strip() if len(row) > corp_id_idx and row[corp_id_idx] else ""

        # Generate JWT token (valid for 24 hours)
        secret = os.getenv("SSO_SECRET", "dev-secret-key-at-least-32-characters-long")
        payload = {
            "sub": corp_id or email,
            "email": row_email,
            "name": display_name,
            "corporate_id": corp_id,
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            "iat": datetime.now(timezone.utc),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        logger.info(f"Login successful: {row_email} ({display_name}, {role})")

        return LoginResponse(
            token=token,
            email=row_email,
            display_name=display_name,
            role=role,
        )

    # Not found
    logger.info(f"Login denied: {email} not in allowlist")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access Denied. Your email is not registered. Please contact suraj.ray@tvsmotor.com to request access.",
    )


@router.post("/bootstrap")
async def bootstrap_admin():
    """One-time bootstrap: create first admin user if Users.xlsx is empty.

    Only works when no users exist. After first admin is created, this endpoint
    becomes a no-op.
    """
    sp = SharePointClient()

    # Check if users already exist (with valid email data)
    sp = SharePointClient()
    try:
        rows = await sp.read_workbook(USERS_FILENAME, sheet="Sheet1")
        if rows and len(rows) > 1:
            headers_row = [str(h).strip().lower() for h in rows[0]]
            email_col = headers_row.index("email") if "email" in headers_row else 0
            for row in rows[1:]:
                if len(row) > email_col and "@" in str(row[email_col]):
                    return {"message": "Bootstrap not needed — users already exist.", "status": "skipped"}
    except Exception:
        pass

    # Create Users.xlsx with first admin
    from datetime import datetime as dt
    now = dt.now(timezone.utc).isoformat()
    # Match the actual SharePoint file header order
    # Read existing headers to match column order
    try:
        rows = await sp.read_workbook(USERS_FILENAME, sheet="Sheet1")
        if rows:
            headers = [str(h).strip() for h in rows[0]]
        else:
            headers = ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"]
    except Exception:
        headers = ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"]

    # Build row matching header order
    field_values = {
        "CorporateId": "17293",
        "Email": "suraj.ray@tvsmotor.com",
        "DisplayName": "Suraj Ray",
        "Role": "Admin",
        "AddedBy": "Bootstrap",
        "AddedAt": now,
        "Active": "True",
    }
    admin_row = [field_values.get(h, "") for h in headers]

    try:
        # Overwrite entire file with headers + admin row (removes any malformed data)
        await sp.write_rows(USERS_FILENAME, "Sheet1", [headers, admin_row])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bootstrap failed: {e}",
        )

    logger.info("Bootstrap: Created first admin user suraj.ray@tvsmotor.com")
    return {"message": "Admin user created: suraj.ray@tvsmotor.com", "status": "success"}
