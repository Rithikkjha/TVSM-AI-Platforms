"""Admin user management endpoints for the Project Estimation Tool.

Provides endpoints for managing the user allowlist (Users.xlsx):
- POST /api/admin/users — add user to allowlist (Admin only, assign role)
- DELETE /api/admin/users/{user_id} — remove user from allowlist (Admin only)
- GET /api/admin/users — list allowlisted users (Admin only)

Enforces last-admin protection: rejects removal if only one Admin remains.
Denies operations from User-role accounts with insufficient permissions error.

Requirements: 18.3, 18.4, 18.13, 18.14, 18.15
"""

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.middleware.auth import (
    AuthenticatedUser,
    get_sharepoint_client,
    invalidate_allowlist_cache,
    require_admin,
)
from app.models.schemas import AllowlistEntry, UserRole
from app.services.sharepoint_client import (
    FOLDER_ADMIN,
    SharePointClient,
    SharePointError,
    SharePointUnavailableError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/users", tags=["Admin Users"])

# Users.xlsx column layout
USERS_FILENAME = f"{FOLDER_ADMIN}/Users.xlsx"
USERS_SHEET = "Sheet1"
USERS_HEADERS = [
    "CorporateId",
    "Email",
    "DisplayName",
    "Role",
    "AddedBy",
    "AddedAt",
    "Active",
]


# --- Request/Response Models ---


class AddUserRequest(BaseModel):
    """Request body for adding a user to the allowlist."""

    email: str = Field(..., min_length=1, description="User's corporate email")
    corporate_id: Optional[str] = Field(
        default="", description="User's corporate ID (optional)"
    )
    display_name: str = Field(..., min_length=1, description="User's display name")
    role: UserRole = Field(..., description="Role to assign: 'Admin' or 'User'")


class UserResponse(BaseModel):
    """Response model for a single allowlist user."""

    corporate_id: str
    email: str
    display_name: str
    role: UserRole
    added_by: str
    added_at: str
    active: bool


class UserListResponse(BaseModel):
    """Response model for listing all allowlisted users."""

    users: list[UserResponse]
    total: int


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


# --- Helper Functions ---


def _validate_email(email: str) -> bool:
    """Validate email format using a basic regex pattern."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def _parse_users_rows(rows: list[list]) -> list[dict]:
    """Parse Users.xlsx rows into a list of user dictionaries.

    Args:
        rows: Raw rows from the workbook (first row is headers).

    Returns:
        List of user dicts with standardized keys.
    """
    if not rows or len(rows) < 1:
        return []

    headers = rows[0]
    col_map = {str(h).strip().lower(): i for i, h in enumerate(headers)}

    corp_id_idx = col_map.get("corporateid", 0)
    email_idx = col_map.get("email", 1)
    display_name_idx = col_map.get("displayname", 2)
    role_idx = col_map.get("role", 3)
    added_by_idx = col_map.get("addedby", 4)
    added_at_idx = col_map.get("addedat", 5)
    active_idx = col_map.get("active", 6)

    users = []
    for row in rows[1:]:
        if not row or len(row) <= email_idx:
            continue

        # Check if active
        is_active = True
        if len(row) > active_idx:
            active_val = str(row[active_idx]).strip().lower()
            is_active = active_val in ("true", "1", "yes", "")

        users.append(
            {
                "corporate_id": str(row[corp_id_idx]).strip() if len(row) > corp_id_idx and row[corp_id_idx] else "",
                "email": str(row[email_idx]).strip() if len(row) > email_idx and row[email_idx] else "",
                "display_name": str(row[display_name_idx]).strip() if len(row) > display_name_idx and row[display_name_idx] else "",
                "role": str(row[role_idx]).strip() if len(row) > role_idx and row[role_idx] else "User",
                "added_by": str(row[added_by_idx]).strip() if len(row) > added_by_idx and row[added_by_idx] else "",
                "added_at": str(row[added_at_idx]).strip() if len(row) > added_at_idx and row[added_at_idx] else "",
                "active": is_active,
                "row_index": rows.index(row) if row in rows else -1,
            }
        )

    return users


# --- Endpoints ---


@router.get("", response_model=UserListResponse)
async def list_users(
    admin: AuthenticatedUser = Depends(require_admin),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> UserListResponse:
    """List all allowlisted users.

    Only accessible by Admin-role users.

    Requirements: 18.14
    """
    try:
        rows = await sharepoint_client.read_workbook(USERS_FILENAME, sheet=USERS_SHEET)
    except SharePointUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SharePoint is temporarily unavailable. Please retry shortly.",
        )

    users_data = _parse_users_rows(rows)

    users = [
        UserResponse(
            corporate_id=u["corporate_id"],
            email=u["email"],
            display_name=u["display_name"],
            role=UserRole.from_str(u["role"]),
            added_by=u["added_by"],
            added_at=u["added_at"],
            active=u["active"],
        )
        for u in users_data
        if u["active"] and u["email"]
    ]

    return UserListResponse(users=users, total=len(users))


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def add_user(
    request: AddUserRequest,
    admin: AuthenticatedUser = Depends(require_admin),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> UserResponse:
    """Add a user to the allowlist.

    Only accessible by Admin-role users. Validates email format and
    assigns the specified role.

    Requirements: 18.3, 18.14
    """
    # Validate email format
    if not _validate_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email format: {request.email}",
        )

    # Check if user already exists
    try:
        rows = await sharepoint_client.read_workbook(USERS_FILENAME, sheet=USERS_SHEET)
    except SharePointUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SharePoint is temporarily unavailable. Please retry shortly.",
        )

    users_data = _parse_users_rows(rows)
    email_lower = request.email.strip().lower()

    # A currently-active row for this email is a genuine duplicate.
    for user in users_data:
        if user["email"].lower() == email_lower and user["active"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{request.email}' already exists in the allowlist.",
            )

    now = datetime.now(timezone.utc).isoformat()

    # Read current headers to match column order
    try:
        existing = await sharepoint_client.read_workbook(USERS_FILENAME, USERS_SHEET)
        headers = [str(h).strip() for h in existing[0]] if existing else USERS_HEADERS
    except Exception:
        headers = USERS_HEADERS

    # If an INACTIVE row already exists for this email (e.g. the person was
    # removed earlier via soft-delete), REACTIVATE that row in place instead of
    # appending a new one. Appending would leave two rows for the same email —
    # and login/allowlist scanning could then hit the stale inactive row first
    # and wrongly report "account deactivated". Reactivating keeps exactly one
    # row per person and updates their role/details to the new values.
    inactive_exists = any(
        u["email"].lower() == email_lower and not u["active"] for u in users_data
    )
    if inactive_exists:
        header_map = {str(h).strip().lower(): i + 1 for i, h in enumerate(headers)}  # 1-based
        updates = {}
        if "corporateid" in header_map:
            updates[header_map["corporateid"]] = request.corporate_id or ""
        if "displayname" in header_map:
            updates[header_map["displayname"]] = request.display_name.strip()
        if "role" in header_map:
            updates[header_map["role"]] = request.role.value
        if "addedby" in header_map:
            updates[header_map["addedby"]] = admin.email
        if "addedat" in header_map:
            updates[header_map["addedat"]] = now
        if "active" in header_map:
            updates[header_map["active"]] = "TRUE"
        email_col = header_map.get("email", 2)

        try:
            updated = await sharepoint_client.update_row_cells(
                USERS_FILENAME,
                USERS_SHEET,
                match_column=email_col,
                match_value=request.email.strip(),
                updates=updates,
            )
        except SharePointError as exc:
            logger.error(f"Failed to reactivate user in allowlist: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add user. Please retry.",
            )
        if not updated:
            # Row vanished between read and write (rare race) — fall through to append.
            inactive_exists = False

    if not inactive_exists:
        field_values = {
            "CorporateId": request.corporate_id or "",
            "Email": request.email.strip(),
            "DisplayName": request.display_name.strip(),
            "Role": request.role.value,
            "AddedBy": admin.email,
            "AddedAt": now,
            "Active": "TRUE",
        }
        new_row = [field_values.get(h, "") for h in headers]

        # Append to Users.xlsx
        try:
            await sharepoint_client.append_row(USERS_FILENAME, USERS_SHEET, new_row)
        except SharePointError as exc:
            logger.error(f"Failed to add user to allowlist: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add user. Please retry.",
            )

    # Invalidate the auth allowlist cache so the new user can access
    # authenticated endpoints immediately rather than after the TTL expires.
    invalidate_allowlist_cache()

    logger.info(
        f"Admin '{admin.email}' added user '{request.email}' "
        f"with role '{request.role.value}' to allowlist."
    )

    return UserResponse(
        corporate_id=request.corporate_id or "",
        email=request.email.strip(),
        display_name=request.display_name.strip(),
        role=request.role,
        added_by=admin.email,
        added_at=now,
        active=True,
    )


@router.delete("/{user_id}", response_model=MessageResponse)
async def remove_user(
    user_id: str,
    admin: AuthenticatedUser = Depends(require_admin),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> MessageResponse:
    """Remove a user from the allowlist.

    Only accessible by Admin-role users. Enforces last-admin protection:
    if the target user is the only Admin, the removal is rejected.

    The user_id parameter matches against the user's email or corporate ID.

    Requirements: 18.4, 18.13, 18.14
    """
    try:
        rows = await sharepoint_client.read_workbook(USERS_FILENAME, sheet=USERS_SHEET)
    except SharePointUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SharePoint is temporarily unavailable. Please retry shortly.",
        )

    users_data = _parse_users_rows(rows)
    user_id_lower = user_id.strip().lower()

    # Find the user to remove
    target_user = None

    for user in users_data:
        if (
            user["email"].lower() == user_id_lower
            or user["corporate_id"].lower() == user_id_lower
        ) and user["active"]:
            target_user = user
            break

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found in the allowlist.",
        )

    # Last-admin protection: check if this is the only Admin
    if target_user["role"] == "Admin":
        admin_count = sum(
            1
            for u in users_data
            if u["role"] == "Admin" and u["active"]
        )
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last Admin. At least one Admin must remain on the allowlist.",
            )

    # Soft-delete the user by flipping only their Active cell to FALSE.
    # We match the row by email and update just the Active column, so no
    # other rows are touched. (Previously this used write_rows with a single
    # row + start_row, but write_rows clears the ENTIRE sheet first and then
    # writes only the passed rows — which wiped all other users.)
    #
    # Column indices are resolved from the actual file headers rather than
    # hardcoded, since the on-disk column order may differ from USERS_HEADERS.
    headers = [str(h).strip().lower() for h in rows[0]] if rows else []
    try:
        email_col = headers.index("email") + 1  # 1-based
    except ValueError:
        email_col = 2  # default: Email is the 2nd column
    try:
        active_col = headers.index("active") + 1  # 1-based
    except ValueError:
        active_col = 7  # default: Active is the 7th column

    try:
        updated = await sharepoint_client.update_row_cells(
            USERS_FILENAME,
            USERS_SHEET,
            match_column=email_col,
            match_value=target_user["email"],
            updates={active_col: "FALSE"},
        )
    except SharePointError as exc:
        logger.error(f"Failed to remove user from allowlist: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove user. Please retry.",
        )

    if not updated:
        # Row disappeared between read and write (rare race / stale data).
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found in the allowlist.",
        )

    # Invalidate the auth allowlist cache so the removed user loses access
    # immediately rather than lingering until the TTL expires.
    invalidate_allowlist_cache()

    logger.info(
        f"Admin '{admin.email}' removed user '{user_id}' from allowlist."
    )

    return MessageResponse(
        message=f"User '{user_id}' has been removed from the allowlist."
    )
