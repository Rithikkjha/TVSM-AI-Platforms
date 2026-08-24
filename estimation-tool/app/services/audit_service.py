"""Audit service for the Project Estimation Tool.

Records immutable audit entries for estimation generation and revision events.
All entries are append-only — no update or delete operations.

Implements:
- record_generation(): write audit entry to AuditLog_YYYY-MM.xlsx
- record_revision(): write revision entry with previous and new values
- get_project_history(): return chronological list of all events for a project

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 6.4
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.models.schemas import (
    AuditEntry,
    AuditGenerationEntry,
    AuditRevisionEntry,
)
from app.services.sharepoint_client import SharePointClient, FOLDER_ESTIMATIONS_AUDIT

logger = logging.getLogger(__name__)

# AuditLog sheet name
AUDIT_SHEET = "Sheet1"


class AuditServiceError(Exception):
    """Base exception for audit service errors."""
    pass


class AuditRevisionError(AuditServiceError):
    """Raised when a revision entry has no difference between previous and new values."""
    pass


async def record_generation(
    entry: AuditGenerationEntry,
    sharepoint_client: SharePointClient,
) -> str:
    """Record a new estimation generation event in the audit log.

    Writes an append-only entry to AuditLog_YYYY-MM.xlsx. The entry captures
    user identity, project metadata, estimation values, and the SLM model used.

    Args:
        entry: The generation audit entry containing all required fields.
        sharepoint_client: SharePoint client for writing to the audit log file.

    Returns:
        The generated audit ID for the new entry.

    Raises:
        AuditServiceError: If the write operation fails.

    Requirements: 9.1, 9.5, 6.4
    """
    audit_id = str(uuid.uuid4())
    timestamp = entry.timestamp or datetime.now(timezone.utc).isoformat()

    # Determine the monthly file from the timestamp
    month = _extract_month_from_timestamp(timestamp)
    filename = f"{FOLDER_ESTIMATIONS_AUDIT}/AuditLog_{month}.xlsx"

    # Ensure the monthly file exists
    await sharepoint_client.ensure_monthly_files(month)

    # Build the row for the audit log
    row = [
        audit_id,
        "generation",
        entry.userId,
        entry.projectName,
        entry.domain.value,
        entry.stream.value,
        entry.inputTier,
        "",  # PreviousValues (empty for generation events)
        json.dumps(entry.estimationValues),  # NewValues
        entry.slmModelName,
        timestamp,
        "",  # EstimationId will be set by caller if needed
    ]

    try:
        await sharepoint_client.append_row(filename, AUDIT_SHEET, row)
        logger.info(
            f"Recorded generation audit entry {audit_id} for project "
            f"'{entry.projectName}' by user '{entry.userId}'."
        )
        return audit_id
    except Exception as exc:
        logger.error(f"Failed to record generation audit entry: {exc}")
        raise AuditServiceError(f"Failed to record audit entry: {exc}")


async def record_generation_with_estimation_id(
    entry: AuditGenerationEntry,
    estimation_id: str,
    sharepoint_client: SharePointClient,
) -> str:
    """Record a generation event linked to a specific estimation ID.

    Args:
        entry: The generation audit entry.
        estimation_id: The estimation ID to associate with this audit entry.
        sharepoint_client: SharePoint client for writing.

    Returns:
        The generated audit ID.

    Requirements: 9.1, 6.4
    """
    audit_id = str(uuid.uuid4())
    timestamp = entry.timestamp or datetime.now(timezone.utc).isoformat()

    month = _extract_month_from_timestamp(timestamp)
    filename = f"{FOLDER_ESTIMATIONS_AUDIT}/AuditLog_{month}.xlsx"

    await sharepoint_client.ensure_monthly_files(month)

    row = [
        audit_id,
        "generation",
        entry.userId,
        entry.projectName,
        entry.domain.value,
        entry.stream.value,
        entry.inputTier,
        "",  # PreviousValues
        json.dumps(entry.estimationValues),
        entry.slmModelName,
        timestamp,
        estimation_id,
    ]

    try:
        await sharepoint_client.append_row(filename, AUDIT_SHEET, row)
        logger.info(
            f"Recorded generation audit entry {audit_id} for estimation "
            f"'{estimation_id}' by user '{entry.userId}'."
        )
        return audit_id
    except Exception as exc:
        logger.error(f"Failed to record generation audit entry: {exc}")
        raise AuditServiceError(f"Failed to record audit entry: {exc}")


async def record_revision(
    entry: AuditRevisionEntry,
    sharepoint_client: SharePointClient,
) -> str:
    """Record a revision event in the audit log.

    A revision entry must have previousValues and newValues that differ in at
    least one field. This ensures audit integrity — no-op revisions are rejected.

    Args:
        entry: The revision audit entry with previous and new values.
        sharepoint_client: SharePoint client for writing.

    Returns:
        The generated audit ID for the revision entry.

    Raises:
        AuditRevisionError: If previousValues and newValues are identical.
        AuditServiceError: If the write operation fails.

    Requirements: 9.2, 9.3, 9.5
    """
    # Validate that previous and new values differ in at least one field
    if not _values_differ(entry.previousValues, entry.newValues):
        raise AuditRevisionError(
            "Revision entry rejected: previousValues and newValues must differ "
            "in at least one field. No-op revisions are not permitted."
        )

    audit_id = str(uuid.uuid4())
    timestamp = entry.timestamp or datetime.now(timezone.utc).isoformat()

    month = _extract_month_from_timestamp(timestamp)
    filename = f"{FOLDER_ESTIMATIONS_AUDIT}/AuditLog_{month}.xlsx"

    await sharepoint_client.ensure_monthly_files(month)

    row = [
        audit_id,
        "revision",
        entry.userId,
        entry.projectName,
        entry.domain.value,
        entry.stream.value,
        entry.inputTier,
        json.dumps(entry.previousValues),
        json.dumps(entry.newValues),
        entry.slmModelName,
        timestamp,
        entry.estimationId,
    ]

    try:
        await sharepoint_client.append_row(filename, AUDIT_SHEET, row)
        logger.info(
            f"Recorded revision audit entry {audit_id} for estimation "
            f"'{entry.estimationId}' by user '{entry.userId}'."
        )
        return audit_id
    except Exception as exc:
        logger.error(f"Failed to record revision audit entry: {exc}")
        raise AuditServiceError(f"Failed to record audit entry: {exc}")


async def get_project_history(
    project_name: str,
    sharepoint_client: SharePointClient,
    estimation_id: Optional[str] = None,
) -> list[AuditEntry]:
    """Return a chronological list of all audit events for a project.

    Searches through audit log files to find all entries matching the given
    project name or estimation ID, returned in chronological order.

    Args:
        project_name: The project name to search for.
        sharepoint_client: SharePoint client for reading audit logs.
        estimation_id: Optional estimation ID to narrow the search.

    Returns:
        Chronologically ordered list of AuditEntry objects.

    Requirements: 9.4
    """
    entries: list[AuditEntry] = []

    # Get the current month's audit log
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    filename = f"{FOLDER_ESTIMATIONS_AUDIT}/AuditLog_{current_month}.xlsx"

    try:
        rows = await sharepoint_client.read_workbook(filename, sheet=AUDIT_SHEET)
        entries.extend(_parse_audit_rows(rows, project_name, estimation_id))
    except Exception as exc:
        logger.warning(f"Could not read audit log for {current_month}: {exc}")

    # Sort chronologically by timestamp
    entries.sort(key=lambda e: e.timestamp)

    return entries


async def get_project_history_all_months(
    project_name: str,
    sharepoint_client: SharePointClient,
    estimation_id: Optional[str] = None,
    months_back: int = 12,
) -> list[AuditEntry]:
    """Search multiple months of audit logs for a project's history.

    Searches the current month and up to `months_back` prior months.

    Args:
        project_name: The project name to search for.
        sharepoint_client: SharePoint client for reading.
        estimation_id: Optional estimation ID to filter by.
        months_back: Number of prior months to search (default 12).

    Returns:
        Chronologically ordered list of AuditEntry objects.

    Requirements: 9.3, 9.4
    """
    entries: list[AuditEntry] = []
    now = datetime.now(timezone.utc)

    for i in range(months_back + 1):
        # Calculate the month offset
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        month_str = f"{year:04d}-{month:02d}"
        filename = f"{FOLDER_ESTIMATIONS_AUDIT}/AuditLog_{month_str}.xlsx"

        try:
            if not await sharepoint_client.file_exists(filename):
                continue
            rows = await sharepoint_client.read_workbook(filename, sheet=AUDIT_SHEET)
            entries.extend(_parse_audit_rows(rows, project_name, estimation_id))
        except Exception as exc:
            logger.debug(f"Could not read audit log for {month_str}: {exc}")
            continue

    # Sort chronologically
    entries.sort(key=lambda e: e.timestamp)

    return entries


def _parse_audit_rows(
    rows: list[list],
    project_name: str,
    estimation_id: Optional[str] = None,
) -> list[AuditEntry]:
    """Parse raw audit log rows and filter by project name or estimation ID.

    Args:
        rows: Raw rows from the workbook (first row is headers).
        project_name: Project name to filter by.
        estimation_id: Optional estimation ID to filter by.

    Returns:
        List of matching AuditEntry objects.
    """
    if not rows or len(rows) < 2:
        return []

    entries: list[AuditEntry] = []
    headers = rows[0]

    # Build column index map
    col_map = {str(h).strip().lower(): i for i, h in enumerate(headers)}

    audit_id_idx = col_map.get("auditid", 0)
    event_type_idx = col_map.get("eventtype", 1)
    user_id_idx = col_map.get("userid", 2)
    project_name_idx = col_map.get("projectname", 3)
    domain_idx = col_map.get("domain", 4)
    stream_idx = col_map.get("stream", 5)
    input_tier_idx = col_map.get("inputtier", 6)
    prev_values_idx = col_map.get("previousvalues", 7)
    new_values_idx = col_map.get("newvalues", 8)
    slm_model_idx = col_map.get("slmmodelname", 9)
    timestamp_idx = col_map.get("timestamp", 10)
    estimation_id_idx = col_map.get("estimationid", 11)

    for row in rows[1:]:
        if not row or len(row) <= project_name_idx:
            continue

        row_project = str(row[project_name_idx]).strip() if row[project_name_idx] else ""
        row_estimation_id = (
            str(row[estimation_id_idx]).strip()
            if len(row) > estimation_id_idx and row[estimation_id_idx]
            else ""
        )

        # Filter by project name or estimation ID
        match = False
        if project_name and row_project.lower() == project_name.lower():
            match = True
        if estimation_id and row_estimation_id == estimation_id:
            match = True

        if not match:
            continue

        # Parse the row into an AuditEntry
        try:
            prev_values = None
            new_values = None

            prev_raw = str(row[prev_values_idx]).strip() if len(row) > prev_values_idx and row[prev_values_idx] else ""
            new_raw = str(row[new_values_idx]).strip() if len(row) > new_values_idx and row[new_values_idx] else ""

            if prev_raw:
                try:
                    prev_values = json.loads(prev_raw)
                except json.JSONDecodeError:
                    prev_values = {"raw": prev_raw}

            if new_raw:
                try:
                    new_values = json.loads(new_raw)
                except json.JSONDecodeError:
                    new_values = {"raw": new_raw}

            input_tier_val = row[input_tier_idx] if len(row) > input_tier_idx else 1
            try:
                input_tier = int(input_tier_val)
                if input_tier not in (1, 2, 3):
                    input_tier = 1
            except (ValueError, TypeError):
                input_tier = 1

            entry = AuditEntry(
                auditId=str(row[audit_id_idx]).strip() if row[audit_id_idx] else "",
                eventType=str(row[event_type_idx]).strip() if len(row) > event_type_idx and row[event_type_idx] else "generation",
                userId=str(row[user_id_idx]).strip() if len(row) > user_id_idx and row[user_id_idx] else "",
                projectName=row_project,
                domain=str(row[domain_idx]).strip() if len(row) > domain_idx and row[domain_idx] else "Others",
                stream=str(row[stream_idx]).strip() if len(row) > stream_idx and row[stream_idx] else "D2C",
                inputTier=input_tier,
                previousValues=prev_values,
                newValues=new_values,
                slmModelName=str(row[slm_model_idx]).strip() if len(row) > slm_model_idx and row[slm_model_idx] else "",
                timestamp=str(row[timestamp_idx]).strip() if len(row) > timestamp_idx and row[timestamp_idx] else "",
                estimationId=row_estimation_id,
            )
            entries.append(entry)
        except Exception as exc:
            logger.warning(f"Failed to parse audit row: {exc}")
            continue

    return entries


def _values_differ(previous: dict, new: dict) -> bool:
    """Check if two value dictionaries differ in at least one field.

    Args:
        previous: The previous estimation values.
        new: The new estimation values.

    Returns:
        True if the values differ in at least one field, False otherwise.
    """
    if previous == new:
        return False

    # Check all keys from both dicts
    all_keys = set(previous.keys()) | set(new.keys())
    for key in all_keys:
        if previous.get(key) != new.get(key):
            return True

    return False


def _extract_month_from_timestamp(timestamp: str) -> str:
    """Extract YYYY-MM from an ISO timestamp string.

    Args:
        timestamp: ISO format timestamp string.

    Returns:
        Month string in YYYY-MM format.
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m")
    except (ValueError, AttributeError):
        # Fallback to current month
        return datetime.now(timezone.utc).strftime("%Y-%m")
