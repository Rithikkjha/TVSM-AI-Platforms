"""SharePoint client service for Microsoft Graph API operations.

Handles all read/write operations to SharePoint Excel files using
service account authentication (MSAL client credentials flow).

Requirements: 18.6, 18.7, 18.16, 21.1, 21.2, 21.4, 21.9, 21.10
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
import msal

# Suppress SSL warnings for corporate proxy environments
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
# Set env for requests (used by MSAL internally)
os.environ.setdefault("CURL_CA_BUNDLE", "")

logger = logging.getLogger(__name__)

# Environment variable names for configuration
ENV_TENANT_ID = "SHAREPOINT_TENANT_ID"
ENV_CLIENT_ID = "SHAREPOINT_CLIENT_ID"
ENV_CLIENT_SECRET = "SHAREPOINT_CLIENT_SECRET"
ENV_SITE_URL = "SHAREPOINT_SITE_URL"
ENV_DRIVE_ID = "SHAREPOINT_DRIVE_ID"

# SharePoint folder structure (module-based)
FOLDER_ESTIMATIONS = "Estimations"
FOLDER_ESTIMATIONS_DATA = "Estimations/Estimations"
FOLDER_ESTIMATIONS_AUDIT = "Estimations/Audit"
FOLDER_PRD_CHECK = "PrdCheck"
FOLDER_PRD_CHECK_AUDIT = "PrdCheck/Audit"
FOLDER_PRD_CHECK_TEMPLATES = "PrdCheck/Templates"
FOLDER_VENDORS = "Vendors"
FOLDER_VENDORS_RESULTS = "Vendors/ComparisonResults"
FOLDER_BUILD_VS_BUY = "BuildVsBuy"
FOLDER_BUILD_VS_BUY_EVALUATIONS = "BuildVsBuy/Evaluations"
FOLDER_BUILD_VS_BUY_AUDIT = "BuildVsBuy/Audit"
FOLDER_ADMIN = "Admin"
FOLDER_PROJECT_TRACKER = "ProjectTracker"


def get_financial_year_label(ref_date=None) -> str:
    """Get Indian financial year label (Apr-Mar). E.g. '2026_27' for Apr 2026 - Mar 2027.

    If ref_date is None, uses current UTC date.
    """
    from datetime import datetime, timezone as _tz
    d = ref_date or datetime.now(_tz.utc)
    # Indian FY starts April 1. If month >= April, FY starts this calendar year.
    if d.month >= 4:
        start_year = d.year
    else:
        start_year = d.year - 1
    end_year_short = (start_year + 1) % 100
    return f"{start_year}_{end_year_short:02d}"


def get_mpcp_fy_folder(ref_date=None) -> str:
    """Get the financial year subfolder path. E.g. 'ProjectTracker/2026_27'."""
    return f"{FOLDER_PROJECT_TRACKER}/{get_financial_year_label(ref_date)}"


def get_mpcp_tracker_file(ref_date=None) -> str:
    """Get the MPCPTracker.xlsx path for the current FY."""
    return f"{get_mpcp_fy_folder(ref_date)}/MPCPTracker.xlsx"


def get_mpcp_audit_folder(ref_date=None) -> str:
    """Get the Audit folder path for the current FY."""
    return f"{get_mpcp_fy_folder(ref_date)}/Audit"


def get_mpcp_exports_folder(ref_date=None) -> str:
    """Get the Exports folder path for the current FY."""
    return f"{get_mpcp_fy_folder(ref_date)}/Exports"


class SharePointError(Exception):
    """Base exception for SharePoint operations."""

    pass


class SharePointUnavailableError(SharePointError):
    """Raised when SharePoint is unavailable for read operations."""

    pass


class SharePointWriteError(SharePointError):
    """Raised when SharePoint write operations fail."""

    pass


class FileLockError(SharePointError):
    """Raised when a file is locked by another process after all retries."""

    pass


class FileCorruptionError(SharePointError):
    """Raised when a SharePoint Excel file is detected as corrupted."""

    pass


class SharePointClient:
    """Client for SharePoint Excel file operations via Microsoft Graph API.

    Uses MSAL client credentials flow (service account) for authentication.
    Implements exponential backoff retry for file lock conflicts (max 3 retries).
    Queues writes on SharePoint unavailability, retries on reconnection.
    Auto-creates monthly files (Estimations_YYYY-MM.xlsx, AuditLog_YYYY-MM.xlsx)
    on first event of a new month.
    """

    # Graph API base URL
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

    # Retry configuration for file lock conflicts
    MAX_RETRIES = 3
    BASE_BACKOFF_SECONDS = 1.0  # Initial backoff: 1s, 2s, 4s

    # Network retry configuration
    NETWORK_RETRY_INTERVALS = [5, 15, 30]  # seconds
    NETWORK_TIMEOUT_SECONDS = 60

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        site_url: Optional[str] = None,
        drive_id: Optional[str] = None,
    ):
        """Initialize the SharePoint client.

        Args:
            tenant_id: Azure AD tenant ID. Falls back to SHAREPOINT_TENANT_ID env var.
            client_id: Azure AD application (client) ID. Falls back to SHAREPOINT_CLIENT_ID env var.
            client_secret: Azure AD client secret. Falls back to SHAREPOINT_CLIENT_SECRET env var.
            site_url: SharePoint site URL. Falls back to SHAREPOINT_SITE_URL env var.
            drive_id: SharePoint drive ID. Falls back to SHAREPOINT_DRIVE_ID env var.
        """
        self.tenant_id = tenant_id or os.getenv(ENV_TENANT_ID, "")
        self.client_id = client_id or os.getenv(ENV_CLIENT_ID, "")
        self.client_secret = client_secret or os.getenv(ENV_CLIENT_SECRET, "")
        self.site_url = site_url or os.getenv(ENV_SITE_URL, "")
        self.drive_id = drive_id or os.getenv(ENV_DRIVE_ID, "")

        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._msal_app: Optional[msal.ConfidentialClientApplication] = None
        self._http_client: Optional[httpx.AsyncClient] = None

        # Write queue for pending writes during SharePoint unavailability
        self._write_queue: list[dict[str, Any]] = []

    @property
    def _authority(self) -> str:
        """MSAL authority URL."""
        return f"https://login.microsoftonline.com/{self.tenant_id}"

    @property
    def _scopes(self) -> list[str]:
        """Microsoft Graph API scopes for client credentials flow."""
        return ["https://graph.microsoft.com/.default"]

    def _get_msal_app(self) -> msal.ConfidentialClientApplication:
        """Get or create the MSAL confidential client application."""
        if self._msal_app is None:
            import requests
            session = requests.Session()
            session.verify = False
            self._msal_app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self._authority,
                http_client=session,
            )
        return self._msal_app

    async def authenticate(self) -> None:
        """Authenticate using MSAL client credentials flow.

        Acquires an access token for Microsoft Graph API using the service account
        (app-only / client credentials). Tokens are cached and refreshed automatically.

        Raises:
            SharePointError: If authentication fails.
        """
        msal_app = self._get_msal_app()

        # Try to get token from cache first
        result = msal_app.acquire_token_silent(self._scopes, account=None)

        if not result:
            # No cached token; acquire a new one
            result = msal_app.acquire_token_for_client(scopes=self._scopes)

        if "access_token" in result:
            self._access_token = result["access_token"]
            # MSAL tokens typically expire in 3600 seconds
            expires_in = result.get("expires_in", 3600)
            self._token_expiry = datetime.now(timezone.utc)
            logger.info("SharePoint authentication successful.")
        else:
            error = result.get("error", "unknown_error")
            error_description = result.get("error_description", "No description")
            raise SharePointError(
                f"Authentication failed: {error} - {error_description}"
            )

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid access token, refreshing if needed."""
        if self._access_token is None:
            await self.authenticate()

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False)
        return self._http_client

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authorization."""
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def _build_item_path(self, filename: str) -> str:
        """Build the Graph API path to a file in the drive.

        Args:
            filename: The Excel file name (e.g., 'Config.xlsx').

        Returns:
            Full Graph API URL path for the file.
        """
        return (
            f"{self.GRAPH_API_BASE}/drives/{self.drive_id}"
            f"/root:/{filename}"
        )

    def _build_workbook_path(self, filename: str) -> str:
        """Build the Graph API path to a workbook's content.

        Args:
            filename: The Excel file name.

        Returns:
            Full Graph API URL for workbook operations.
        """
        return (
            f"{self.GRAPH_API_BASE}/drives/{self.drive_id}"
            f"/root:/{filename}:/workbook"
        )

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        is_write: bool = False,
        **kwargs: Any,
    ) -> httpx.Response:
        """Execute an HTTP request with exponential backoff for lock conflicts.

        Implements:
        - Exponential backoff retry for file lock conflicts (HTTP 423, max 3 retries)
        - Network retry with increasing intervals (timeout at 60s)
        - Write queueing on persistent failure

        Args:
            method: HTTP method (GET, POST, PATCH, PUT).
            url: Full request URL.
            is_write: Whether this is a write operation (for queue logic).
            **kwargs: Additional httpx request arguments.

        Returns:
            The HTTP response.

        Raises:
            SharePointUnavailableError: If read operations fail.
            FileLockError: If file is locked after all retries.
            SharePointWriteError: If write operations fail after retries.
        """
        await self._ensure_authenticated()
        client = await self._get_http_client()
        headers = self._get_headers()

        last_exception: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await client.request(
                    method, url, headers=headers, **kwargs
                )

                # Success
                if response.status_code < 400:
                    return response

                # File lock conflict (HTTP 423 Locked)
                if response.status_code == 423:
                    backoff = self.BASE_BACKOFF_SECONDS * (2**attempt)
                    logger.warning(
                        f"File lock conflict (attempt {attempt + 1}/{self.MAX_RETRIES}). "
                        f"Retrying in {backoff}s..."
                    )
                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        raise FileLockError(
                            "File currently locked by another process. "
                            "Please try again later."
                        )

                # SharePoint unavailable (5xx errors)
                if response.status_code >= 500:
                    if is_write:
                        raise SharePointWriteError(
                            f"SharePoint write failed with status {response.status_code}"
                        )
                    else:
                        raise SharePointUnavailableError(
                            "Data source temporarily unavailable. Please retry shortly."
                        )

                # File corruption detection (specific error codes)
                if response.status_code == 422:
                    raise FileCorruptionError(
                        f"SharePoint file may be corrupted. Status: {response.status_code}"
                    )

                # Other client errors
                error_body = response.text
                raise SharePointError(
                    f"Graph API error ({response.status_code}): {error_body}"
                )

            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_exception = exc
                backoff = self.BASE_BACKOFF_SECONDS * (2**attempt)
                logger.warning(
                    f"Network error (attempt {attempt + 1}/{self.MAX_RETRIES}): {exc}. "
                    f"Retrying in {backoff}s..."
                )
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(backoff)
                    continue

        # All retries exhausted
        if is_write:
            raise SharePointWriteError(
                f"SharePoint write failed after {self.MAX_RETRIES} retries: "
                f"{last_exception}"
            )
        raise SharePointUnavailableError(
            f"SharePoint unavailable after {self.MAX_RETRIES} retries: "
            f"{last_exception}"
        )

    async def _download_file(self, filename: str) -> bytes:
        """Download a file's content from SharePoint.

        Args:
            filename: The file name to download.

        Returns:
            Raw file bytes.

        Raises:
            SharePointUnavailableError: If download fails.
        """
        await self._ensure_authenticated()
        client = await self._get_http_client()
        headers = {
            "Authorization": f"Bearer {self._access_token}",
        }

        url = (
            f"{self.GRAPH_API_BASE}/drives/{self.drive_id}"
            f"/root:/{filename}:/content"
        )

        # Graph API returns a 302 redirect to the actual file download URL
        response = await client.get(url, headers=headers, follow_redirects=True)

        if response.status_code == 404:
            raise SharePointError(
                f"File '{filename}' not found in SharePoint."
            )

        if response.status_code >= 400:
            raise SharePointUnavailableError(
                f"Failed to download '{filename}': {response.status_code} - {response.text[:200]}"
            )

        # Validate we got an actual Excel file (starts with PK zip magic bytes)
        if not response.content[:2] == b'PK':
            raise SharePointUnavailableError(
                f"Downloaded content for '{filename}' is not a valid Excel file. "
                f"Got {len(response.content)} bytes starting with: {response.content[:50]}"
            )

        return response.content

    async def _upload_file(self, filename: str, content: bytes) -> None:
        """Upload file content to SharePoint (overwrite).

        Args:
            filename: The file name to upload.
            content: Raw file bytes.

        Raises:
            SharePointWriteError: If upload fails.
        """
        await self._ensure_authenticated()
        client = await self._get_http_client()
        url = (
            f"{self.GRAPH_API_BASE}/drives/{self.drive_id}"
            f"/root:/{filename}:/content"
        )
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        response = await client.put(url, headers=headers, content=content)
        if response.status_code not in (200, 201):
            raise SharePointWriteError(
                f"Failed to upload '{filename}': {response.status_code} - {response.text}"
            )

    async def read_workbook(
        self,
        filename: str,
        sheet: Optional[str] = None,
    ) -> list[list[Any]]:
        """Read all rows from a SharePoint Excel workbook.

        Downloads the file and parses it locally with openpyxl.

        Args:
            filename: Excel file name (e.g., 'Config.xlsx').
            sheet: Optional worksheet name. If None, reads the first sheet.

        Returns:
            List of rows, where each row is a list of cell values.

        Raises:
            SharePointUnavailableError: If SharePoint is unavailable for reads.
        """
        import io
        from openpyxl import load_workbook

        file_bytes = await self._download_file(filename)
        wb = load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)

        if sheet:
            ws = wb[sheet]
        else:
            ws = wb.active

        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append([cell if cell is not None else "" for cell in row])

        wb.close()
        return rows

    async def write_rows(
        self,
        filename: str,
        sheet: str,
        rows: list[list[Any]],
        start_row: Optional[int] = None,
    ) -> None:
        """Write rows to a SharePoint Excel workbook.

        Downloads the file, modifies it locally with openpyxl, and re-uploads.

        Args:
            filename: Excel file name.
            sheet: Worksheet name.
            rows: List of rows to write, where each row is a list of cell values.
            start_row: Optional 1-based row number to start writing at.
                       If None, overwrites starting from row 2 (after headers).

        Raises:
            FileLockError: If the file is locked after all retries.
            SharePointWriteError: If the write operation fails.
        """
        import io
        from openpyxl import load_workbook

        try:
            file_bytes = await self._download_file(filename)
            wb = load_workbook(io.BytesIO(file_bytes))

            if sheet in wb.sheetnames:
                ws = wb[sheet]
                # Physically delete all existing rows so no phantom empty rows remain.
                # (Clearing cell values alone leaves blank rows that read back as empty.)
                if ws.max_row and ws.max_row > 0:
                    ws.delete_rows(1, ws.max_row)
            else:
                ws = wb.create_sheet(sheet)

            actual_start = start_row if start_row is not None else 1

            for row_idx, row_data in enumerate(rows):
                for col_idx, value in enumerate(row_data):
                    ws.cell(row=actual_start + row_idx, column=col_idx + 1, value=value)

            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            await self._upload_file(filename, buffer.getvalue())
            wb.close()

        except (SharePointWriteError, FileLockError):
            self._queue_write(
                operation="write_rows",
                filename=filename,
                sheet=sheet,
                rows=rows,
                start_row=start_row,
            )
            raise

    async def append_row(
        self,
        filename: str,
        sheet: str,
        row: list[Any],
    ) -> None:
        """Append a single row to the end of a SharePoint Excel worksheet.

        Downloads the file, appends the row with openpyxl, and re-uploads.

        Args:
            filename: Excel file name.
            sheet: Worksheet name.
            row: List of cell values for the new row.

        Raises:
            FileLockError: If the file is locked after all retries.
            SharePointWriteError: If the write operation fails.
        """
        import io
        from openpyxl import load_workbook

        try:
            file_bytes = await self._download_file(filename)
            wb = load_workbook(io.BytesIO(file_bytes))

            if sheet in wb.sheetnames:
                ws = wb[sheet]
            else:
                ws = wb.create_sheet(sheet)

            ws.append(row)

            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            await self._upload_file(filename, buffer.getvalue())
            wb.close()

        except (SharePointWriteError, FileLockError):
            self._queue_write(
                operation="append_row",
                filename=filename,
                sheet=sheet,
                row=row,
            )
            raise

    async def update_row_cells(
        self,
        filename: str,
        sheet: str,
        match_column: int,
        match_value: str,
        updates: dict[int, Any],
    ) -> bool:
        """Update specific cells in a row matched by a column value.

        Downloads the file, finds the row where match_column == match_value,
        updates the specified columns, and re-uploads.

        Args:
            filename: Excel file name.
            sheet: Worksheet name.
            match_column: 1-based column index to match on (e.g., 1 for column A).
            match_value: Value to match in the match_column.
            updates: Dict of {1-based column index: new value} to set.

        Returns:
            True if a matching row was found and updated, False otherwise.

        Raises:
            FileLockError: If the file is locked after all retries.
            SharePointWriteError: If the write operation fails.
        """
        import io
        from openpyxl import load_workbook

        try:
            file_bytes = await self._download_file(filename)
            wb = load_workbook(io.BytesIO(file_bytes))

            if sheet not in wb.sheetnames:
                wb.close()
                return False

            ws = wb[sheet]
            found = False

            for row in ws.iter_rows(min_row=2):  # Skip header
                cell_value = str(row[match_column - 1].value or "").strip()
                if cell_value == match_value:
                    for col_idx, value in updates.items():
                        ws.cell(row=row[0].row, column=col_idx, value=value)
                    found = True
                    break

            if found:
                buffer = io.BytesIO()
                wb.save(buffer)
                buffer.seek(0)
                await self._upload_file(filename, buffer.getvalue())

            wb.close()
            return found

        except (SharePointWriteError, FileLockError):
            self._queue_write(
                operation="update_row_cells",
                filename=filename,
                sheet=sheet,
                match_column=match_column,
                match_value=match_value,
                updates=updates,
            )
            raise

    async def create_monthly_file(
        self,
        template: str,
        month: str,
    ) -> None:
        """Create a new monthly file from a template.

        Auto-creates monthly files (Estimations/Estimations_YYYY-MM.xlsx,
        Estimations/AuditLog_YYYY-MM.xlsx) on first event of a new month.

        Args:
            template: Template identifier ('estimations' or 'auditlog').
            month: Month in YYYY-MM format (e.g., '2026-01').

        Raises:
            SharePointWriteError: If file creation fails.
        """
        if template == "estimations":
            filename = f"{FOLDER_ESTIMATIONS_DATA}/Estimations_{month}.xlsx"
            headers_row = [
                "EstimationId", "ProjectName", "ProjectDescription", "Domain",
                "Stream", "InputTier", "EffortBreakdownJSON", "TotalEffortDays",
                "TotalEffortMonths", "CalendarDuration", "TeamCompositionJSON",
                "ScopeCoverageJSON", "ConfidenceJSON", "CostProjectionJSON",
                "AssumptionsJSON", "SLMModelName", "GeneratedBy", "GeneratedAt",
                "Version", "PreviousVersionId", "VendorComparisonJSON", "PhasesJSON",
                "CatalogBreakdownJSON", "InfraCostJSON", "DocumentReadinessJSON",
            ]
        elif template == "auditlog":
            filename = f"{FOLDER_ESTIMATIONS_AUDIT}/AuditLog_{month}.xlsx"
            headers_row = [
                "AuditId", "EventType", "UserId", "ProjectName", "Domain",
                "Stream", "InputTier", "PreviousValues", "NewValues",
                "SLMModelName", "Timestamp", "EstimationId",
            ]
        else:
            raise SharePointError(f"Unknown template type: {template}")

        # Check if file already exists before creating
        if await self.file_exists(filename):
            logger.info(f"Monthly file '{filename}' already exists. Skipping creation.")
            return

        # Create the file with headers using Graph API upload
        await self._create_excel_file(filename, headers_row)
        logger.info(f"Created monthly file: {filename}")

    async def _create_excel_file(
        self,
        filename: str,
        headers: list[str],
    ) -> None:
        """Create a new Excel file in SharePoint with column headers.

        Uses Graph API to create an empty workbook session and write headers.

        Args:
            filename: File name to create.
            headers: Column header names for the first row.
        """
        await self._ensure_authenticated()
        client = await self._get_http_client()
        auth_headers = self._get_headers()

        # Step 1: Create an empty file via upload
        upload_url = (
            f"{self.GRAPH_API_BASE}/drives/{self.drive_id}"
            f"/root:/{filename}:/content"
        )

        # Create a minimal Excel file using openpyxl in memory
        import io

        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(headers)

        # Also create a table for structured data
        from openpyxl.worksheet.table import Table, TableStyleInfo

        if headers:
            end_col = chr(ord("A") + len(headers) - 1)
            table_ref = f"A1:{end_col}1"
            table = Table(displayName="Table1", ref=table_ref)
            style = TableStyleInfo(
                name="TableStyleMedium2",
                showFirstColumn=False,
                showLastColumn=False,
                showRowStripes=True,
                showColumnStripes=False,
            )
            table.tableStyleInfo = style
            ws.add_table(table)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        file_content = buffer.getvalue()

        # Upload the file
        upload_headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

        response = await client.put(
            upload_url, headers=upload_headers, content=file_content
        )

        if response.status_code not in (200, 201):
            raise SharePointWriteError(
                f"Failed to create file '{filename}': {response.status_code} - {response.text}"
            )

    async def file_exists(self, filename: str) -> bool:
        """Check if a file exists in the SharePoint drive.

        Args:
            filename: File name to check.

        Returns:
            True if the file exists, False otherwise.
        """
        await self._ensure_authenticated()
        client = await self._get_http_client()
        headers = self._get_headers()

        url = f"{self._build_item_path(filename)}"

        try:
            response = await client.get(url, headers=headers)
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            # If we can't reach SharePoint, we can't confirm existence
            raise SharePointUnavailableError(
                "Cannot verify file existence: SharePoint is unavailable."
            )

    async def ensure_monthly_files(self, month: Optional[str] = None) -> None:
        """Ensure monthly files exist for the given month, creating if needed.

        Implements the monthly file rotation logic: on first event of a new month,
        automatically create Estimations/Estimations_YYYY-MM.xlsx and
        Estimations/AuditLog_YYYY-MM.xlsx.

        Args:
            month: Month in YYYY-MM format. Defaults to current month.
        """
        if month is None:
            month = datetime.now(timezone.utc).strftime("%Y-%m")

        estimations_file = f"{FOLDER_ESTIMATIONS_DATA}/Estimations_{month}.xlsx"
        auditlog_file = f"{FOLDER_ESTIMATIONS_AUDIT}/AuditLog_{month}.xlsx"

        # Create estimation file if it doesn't exist
        if not await self.file_exists(estimations_file):
            await self.create_monthly_file("estimations", month)

        # Create audit log file if it doesn't exist
        if not await self.file_exists(auditlog_file):
            await self.create_monthly_file("auditlog", month)

    async def ensure_estimation_index(self) -> None:
        """Ensure EstimationIndex.xlsx exists with proper headers, creating if needed."""
        index_file = f"{FOLDER_ESTIMATIONS}/EstimationIndex.xlsx"
        if not await self.file_exists(index_file):
            headers = [
                "EstimationId", "ProjectName", "Domain", "Stream", "InputTier",
                "TotalEffortDays", "CalendarDuration", "ConfidenceLevel", "TotalCost",
                "GeneratedBy", "GeneratedAt", "MonthlyFileRef", "Version", "Status",
                "DocumentNames",
            ]
            await self._create_excel_file(index_file, headers)
            logger.info(f"Created EstimationIndex file: {index_file}")

    async def initialize_sharepoint_structure(self) -> None:
        """Ensure all required SharePoint files/folders exist on first boot.

        Idempotent — safe to call on every startup. Only creates files that
        don't already exist. Never overwrites or deletes existing data.
        """
        from datetime import datetime, timezone as tz

        logger.info("Initializing SharePoint file structure...")
        month = datetime.now(tz.utc).strftime("%Y-%m")

        # ── Estimations module ──
        # EstimationIndex.xlsx
        await self.ensure_estimation_index()
        # Monthly estimation + audit files
        await self.ensure_monthly_files(month)
        # Config.xlsx (rate card, settings)
        config_file = f"{FOLDER_ESTIMATIONS}/Config.xlsx"
        if not await self.file_exists(config_file):
            await self._create_excel_file(config_file, ["key", "value"])
            logger.info(f"Created: {config_file}")

        # ── Admin module ──
        users_file = f"{FOLDER_ADMIN}/Users.xlsx"
        if not await self.file_exists(users_file):
            await self._create_excel_file(users_file, [
                "Email", "DisplayName", "CorporateId", "Role", "Active", "AddedAt",
            ])
            logger.info(f"Created: {users_file}")

        # ── Vendor Compare module ──
        vendor_index = f"{FOLDER_VENDORS}/ComparisonIndex.xlsx"
        if not await self.file_exists(vendor_index):
            await self._create_excel_file(vendor_index, [
                "ComparisonId", "Name", "VendorCount", "Winner", "OwnerName", "CreatedAt",
            ])
            logger.info(f"Created: {vendor_index}")

        # ── Build vs Buy module ──
        eval_index = f"{FOLDER_BUILD_VS_BUY}/EvalIndex.xlsx"
        if not await self.file_exists(eval_index):
            await self._create_excel_file(eval_index, [
                "EvaluationId", "OpportunityName", "BusinessUnit",
                "Status", "OwnerName", "CreatedAt", "UpdatedAt", "FileName",
            ])
            logger.info(f"Created: {eval_index}")

        bvb_audit = f"{FOLDER_BUILD_VS_BUY_AUDIT}/BvBAudit_{month}.xlsx"
        if not await self.file_exists(bvb_audit):
            await self._create_excel_file(bvb_audit, [
                "AuditId", "Timestamp", "EventType", "EvaluationId", "UserEmail", "Details",
            ])
            logger.info(f"Created: {bvb_audit}")

        # ── PRD Checker module ──
        prd_audit = f"{FOLDER_PRD_CHECK_AUDIT}/PrdCheckAudit_{month}.xlsx"
        if not await self.file_exists(prd_audit):
            await self._create_excel_file(prd_audit, [
                "AuditId", "Timestamp", "UserEmail", "UserName", "DocType",
                "Filename", "ReadinessPercent", "FilledSections", "PlaceholderSections",
                "MissingSections", "TotalSections", "MissingSectionNames", "ResultJSON",
            ])
            logger.info(f"Created: {prd_audit}")

        # ── MPCP Project Tracker module (financial year-based folders) ──
        fy_folder = get_mpcp_fy_folder()
        fy_audit_folder = get_mpcp_audit_folder()
        fy_exports_folder = get_mpcp_exports_folder()
        mpcp_tracker_file = get_mpcp_tracker_file()

        # Create MPCPTracker.xlsx with proper named sheets (no default Sheet1)
        if not await self.file_exists(mpcp_tracker_file):
            import io as _io
            from openpyxl import Workbook as _Wb
            _wb = _Wb()
            # Rename default sheet to ManagingPoints
            _ws = _wb.active
            _ws.title = "ManagingPoints"
            # Create all other sheets
            _wb.create_sheet("CheckPoints")
            _wb.create_sheet("Projects")
            _wb.create_sheet("ProcessTracks")
            _wb.create_sheet("ExecutionMilestones")
            _wb.create_sheet("Dependencies")
            _wb.create_sheet("Budget")
            _wb.create_sheet("RAGHistory")
            _wb.create_sheet("ProjectChangeLog")
            _buf = _io.BytesIO()
            _wb.save(_buf)
            await self._upload_file(mpcp_tracker_file, _buf.getvalue())
            logger.info(f"Created: {mpcp_tracker_file} with all sheets (FY: {get_financial_year_label()})")

        mpcp_audit_file = f"{fy_audit_folder}/MPCPAudit_{month}.xlsx"
        if not await self.file_exists(mpcp_audit_file):
            await self._create_excel_file(mpcp_audit_file, [
                "AuditId", "Timestamp", "EventType", "EntityType",
                "EntityId", "UserEmail", "UserName", "Details",
            ])
            logger.info(f"Created: {mpcp_audit_file}")

        logger.info("SharePoint structure initialization complete.")

    def _queue_write(self, **operation_data: Any) -> None:
        """Queue a write operation for later retry.

        Called when SharePoint is unavailable for writes. Queued operations
        are retried when connectivity is restored.

        Args:
            **operation_data: Operation details (operation type, filename, data).
        """
        operation_data["queued_at"] = datetime.now(timezone.utc).isoformat()
        self._write_queue.append(operation_data)
        logger.warning(
            f"Write operation queued (queue size: {len(self._write_queue)}). "
            f"Will retry on reconnection."
        )

    async def flush_write_queue(self) -> list[dict[str, Any]]:
        """Attempt to flush all queued write operations.

        Called when SharePoint connectivity is restored. Processes queued writes
        in order, removing successful ones from the queue.

        Returns:
            List of operations that failed to flush (still in queue).
        """
        if not self._write_queue:
            return []

        logger.info(f"Flushing write queue ({len(self._write_queue)} operations)...")
        failed_operations: list[dict[str, Any]] = []

        while self._write_queue:
            operation = self._write_queue.pop(0)
            op_type = operation.get("operation")

            try:
                if op_type == "write_rows":
                    await self.write_rows(
                        filename=operation["filename"],
                        sheet=operation["sheet"],
                        rows=operation["rows"],
                        start_row=operation.get("start_row"),
                    )
                elif op_type == "append_row":
                    await self.append_row(
                        filename=operation["filename"],
                        sheet=operation["sheet"],
                        row=operation["row"],
                    )
                else:
                    logger.error(f"Unknown queued operation type: {op_type}")
                    failed_operations.append(operation)
            except (SharePointWriteError, FileLockError) as exc:
                logger.warning(f"Queued write still failing: {exc}")
                failed_operations.append(operation)

        self._write_queue = failed_operations
        if failed_operations:
            logger.warning(
                f"{len(failed_operations)} write(s) still pending in queue."
            )
        else:
            logger.info("Write queue flushed successfully.")

        return failed_operations

    @property
    def pending_writes(self) -> int:
        """Number of pending write operations in the queue."""
        return len(self._write_queue)

    async def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    def get_monthly_filename(self, template: str, month: Optional[str] = None) -> str:
        """Get the filename for a monthly file.

        Args:
            template: 'estimations' or 'auditlog'.
            month: Month in YYYY-MM format. Defaults to current month.

        Returns:
            Filename string (e.g., 'Estimations/Estimations_2026-01.xlsx').
        """
        if month is None:
            month = datetime.now(timezone.utc).strftime("%Y-%m")

        if template == "estimations":
            return f"{FOLDER_ESTIMATIONS_DATA}/Estimations_{month}.xlsx"
        elif template == "auditlog":
            return f"{FOLDER_ESTIMATIONS_AUDIT}/AuditLog_{month}.xlsx"
        else:
            raise ValueError(f"Unknown template type: {template}")

    # ---- Template Storage Methods ----

    async def upload_template(self, doc_type: str, file_bytes: bytes, file_ext: str) -> None:
        """Upload a document template to SharePoint (Templates/ folder).

        Args:
            doc_type: Template type ('prd', 'brd', 'hld').
            file_bytes: Raw file content.
            file_ext: File extension ('docx' or 'pdf').

        Raises:
            SharePointWriteError: If upload fails.
        """
        await self._ensure_authenticated()
        client = await self._get_http_client()

        filename = f"{FOLDER_PRD_CHECK_TEMPLATES}/{doc_type}_template.{file_ext}"
        url = (
            f"{self.GRAPH_API_BASE}/drives/{self.drive_id}"
            f"/root:/{filename}:/content"
        )

        content_type_map = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pdf": "application/pdf",
            "json": "application/json",
        }
        content_type = content_type_map.get(file_ext, "application/octet-stream")

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": content_type,
        }
        response = await client.put(url, headers=headers, content=file_bytes)
        if response.status_code not in (200, 201):
            raise SharePointWriteError(
                f"Failed to upload template '{filename}': {response.status_code} - {response.text[:200]}"
            )
        logger.info(f"Uploaded template to SharePoint: {filename}")

    async def upload_template_sections(self, doc_type: str, sections_json: bytes) -> None:
        """Upload extracted template sections JSON to SharePoint.

        Args:
            doc_type: Template type ('prd', 'brd', 'hld').
            sections_json: JSON bytes of extracted sections.

        Raises:
            SharePointWriteError: If upload fails.
        """
        await self._ensure_authenticated()
        client = await self._get_http_client()

        filename = f"{FOLDER_PRD_CHECK_TEMPLATES}/{doc_type}_sections.json"
        url = (
            f"{self.GRAPH_API_BASE}/drives/{self.drive_id}"
            f"/root:/{filename}:/content"
        )
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        response = await client.put(url, headers=headers, content=sections_json)
        if response.status_code not in (200, 201):
            raise SharePointWriteError(
                f"Failed to upload template sections '{filename}': {response.status_code} - {response.text[:200]}"
            )
        logger.info(f"Uploaded template sections to SharePoint: {filename}")

    async def download_template_sections(self, doc_type: str) -> Optional[bytes]:
        """Download template sections JSON from SharePoint.

        Args:
            doc_type: Template type ('prd', 'brd', 'hld').

        Returns:
            JSON bytes if found, None if not found.
        """
        await self._ensure_authenticated()
        client = await self._get_http_client()

        filename = f"{FOLDER_PRD_CHECK_TEMPLATES}/{doc_type}_sections.json"
        url = (
            f"{self.GRAPH_API_BASE}/drives/{self.drive_id}"
            f"/root:/{filename}:/content"
        )
        headers = {
            "Authorization": f"Bearer {self._access_token}",
        }

        response = await client.get(url, headers=headers, follow_redirects=True)

        if response.status_code == 404:
            return None

        if response.status_code >= 400:
            logger.warning(
                f"Failed to download template sections '{filename}': "
                f"{response.status_code} - {response.text[:200]}"
            )
            return None

        return response.content

    async def delete_template(self, doc_type: str) -> None:
        """Delete template files from SharePoint (Templates/ folder).

        Attempts to delete both the template file and sections JSON.
        Silently ignores 404 (file not found).

        Args:
            doc_type: Template type ('prd', 'brd', 'hld').
        """
        await self._ensure_authenticated()
        client = await self._get_http_client()
        headers = {
            "Authorization": f"Bearer {self._access_token}",
        }

        # Try to delete both possible template files and the sections JSON
        filenames = [
            f"{FOLDER_PRD_CHECK_TEMPLATES}/{doc_type}_template.docx",
            f"{FOLDER_PRD_CHECK_TEMPLATES}/{doc_type}_template.pdf",
            f"{FOLDER_PRD_CHECK_TEMPLATES}/{doc_type}_sections.json",
        ]

        for filename in filenames:
            url = (
                f"{self.GRAPH_API_BASE}/drives/{self.drive_id}"
                f"/root:/{filename}"
            )
            response = await client.delete(url, headers=headers)
            if response.status_code == 404:
                continue  # File doesn't exist, that's fine
            if response.status_code >= 400 and response.status_code != 204:
                logger.warning(
                    f"Failed to delete '{filename}' from SharePoint: "
                    f"{response.status_code} - {response.text[:200]}"
                )
            else:
                logger.info(f"Deleted template from SharePoint: {filename}")
