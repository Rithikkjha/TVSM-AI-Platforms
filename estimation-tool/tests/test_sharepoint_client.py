"""Unit tests for SharePoint client service.

Tests authentication flow, read/write operations, monthly file creation,
retry logic, and write queue behavior using mocked Graph API responses.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from app.services.sharepoint_client import (
    FileLockError,
    SharePointClient,
    SharePointError,
    SharePointUnavailableError,
    SharePointWriteError,
)


@pytest_asyncio.fixture
async def client():
    """Create a SharePoint client with test credentials."""
    sp_client = SharePointClient(
        tenant_id="test-tenant-id",
        client_id="test-client-id",
        client_secret="test-secret",
        site_url="https://test.sharepoint.com/sites/test",
        drive_id="test-drive-id",
    )
    yield sp_client
    await sp_client.close()


class TestAuthentication:
    """Tests for MSAL authentication flow."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self, client: SharePointClient):
        """Successful authentication acquires access token."""
        mock_msal_app = MagicMock()
        mock_msal_app.acquire_token_silent.return_value = None
        mock_msal_app.acquire_token_for_client.return_value = {
            "access_token": "test-token-123",
            "expires_in": 3600,
        }

        with patch.object(client, "_get_msal_app", return_value=mock_msal_app):
            await client.authenticate()

        assert client._access_token == "test-token-123"

    @pytest.mark.asyncio
    async def test_authenticate_uses_cached_token(self, client: SharePointClient):
        """Authentication uses cached token from MSAL when available."""
        mock_msal_app = MagicMock()
        mock_msal_app.acquire_token_silent.return_value = {
            "access_token": "cached-token-456",
            "expires_in": 3600,
        }

        with patch.object(client, "_get_msal_app", return_value=mock_msal_app):
            await client.authenticate()

        assert client._access_token == "cached-token-456"
        mock_msal_app.acquire_token_for_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_authenticate_failure_raises_error(self, client: SharePointClient):
        """Failed authentication raises SharePointError."""
        mock_msal_app = MagicMock()
        mock_msal_app.acquire_token_silent.return_value = None
        mock_msal_app.acquire_token_for_client.return_value = {
            "error": "invalid_client",
            "error_description": "Client secret is invalid",
        }

        with patch.object(client, "_get_msal_app", return_value=mock_msal_app):
            with pytest.raises(SharePointError, match="Authentication failed"):
                await client.authenticate()


class TestReadWorkbook:
    """Tests for read_workbook() method."""

    @pytest.mark.asyncio
    async def test_read_workbook_default_sheet(self, client: SharePointClient):
        """read_workbook() reads Sheet1 by default."""
        import io
        from openpyxl import Workbook

        # Create a real in-memory Excel file
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["Header1", "Header2"])
        ws.append(["Value1", "Value2"])
        buffer = io.BytesIO()
        wb.save(buffer)
        excel_bytes = buffer.getvalue()

        with patch.object(client, "_download_file", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = excel_bytes
            result = await client.read_workbook("Config.xlsx")

        assert result == [["Header1", "Header2"], ["Value1", "Value2"]]
        mock_download.assert_called_once_with("Config.xlsx")

    @pytest.mark.asyncio
    async def test_read_workbook_specific_sheet(self, client: SharePointClient):
        """read_workbook() uses specified sheet name."""
        import io
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "AllUsers"
        ws.append(["data"])
        buffer = io.BytesIO()
        wb.save(buffer)
        excel_bytes = buffer.getvalue()

        with patch.object(client, "_download_file", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = excel_bytes
            result = await client.read_workbook("Users.xlsx", sheet="AllUsers")

        assert result == [["data"]]

    @pytest.mark.asyncio
    async def test_read_workbook_empty_result(self, client: SharePointClient):
        """read_workbook() returns empty list when no data."""
        import io
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        # No rows added — empty sheet
        buffer = io.BytesIO()
        wb.save(buffer)
        excel_bytes = buffer.getvalue()

        with patch.object(client, "_download_file", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = excel_bytes
            result = await client.read_workbook("Empty.xlsx")

        assert result == []


class TestWriteRows:
    """Tests for write_rows() method."""

    @pytest.mark.asyncio
    async def test_write_rows_with_start_row(self, client: SharePointClient):
        """write_rows() downloads, modifies, and uploads the file."""
        import io
        from openpyxl import Workbook

        # Create a source Excel file
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["Col1", "Col2"])
        buffer = io.BytesIO()
        wb.save(buffer)
        excel_bytes = buffer.getvalue()

        with patch.object(client, "_download_file", new_callable=AsyncMock) as mock_download, \
             patch.object(client, "_upload_file", new_callable=AsyncMock) as mock_upload:
            mock_download.return_value = excel_bytes
            await client.write_rows(
                "Test.xlsx", "Sheet1",
                rows=[["a", "b"], ["c", "d"]],
                start_row=2,
            )

        mock_download.assert_called_once_with("Test.xlsx")
        mock_upload.assert_called_once()
        # Verify uploaded content is valid Excel
        upload_args = mock_upload.call_args
        assert upload_args[0][0] == "Test.xlsx"

    @pytest.mark.asyncio
    async def test_write_rows_queues_on_write_error(self, client: SharePointClient):
        """write_rows() queues operation when write fails."""
        client._access_token = "test-token"

        with patch.object(client, "_download_file", new_callable=AsyncMock) as mock_download:
            mock_download.side_effect = SharePointWriteError("Write failed")
            with pytest.raises(SharePointWriteError):
                await client.write_rows("Test.xlsx", "Sheet1", rows=[["data"]])

        assert client.pending_writes == 1


class TestAppendRow:
    """Tests for append_row() method."""

    @pytest.mark.asyncio
    async def test_append_row_uses_table_endpoint(self, client: SharePointClient):
        """append_row() downloads, appends, and uploads the file."""
        import io
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["Col1", "Col2"])
        buffer = io.BytesIO()
        wb.save(buffer)
        excel_bytes = buffer.getvalue()

        with patch.object(client, "_download_file", new_callable=AsyncMock) as mock_download, \
             patch.object(client, "_upload_file", new_callable=AsyncMock) as mock_upload:
            mock_download.return_value = excel_bytes
            await client.append_row("Test.xlsx", "Sheet1", row=["val1", "val2"])

        mock_download.assert_called_once_with("Test.xlsx")
        mock_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_append_row_queues_on_lock_error(self, client: SharePointClient):
        """append_row() queues operation when file is locked."""
        client._access_token = "test-token"

        with patch.object(client, "_download_file", new_callable=AsyncMock) as mock_download:
            mock_download.side_effect = FileLockError("Locked")
            with pytest.raises(FileLockError):
                await client.append_row("Test.xlsx", "Sheet1", row=["data"])

        assert client.pending_writes == 1


class TestRetryLogic:
    """Tests for exponential backoff retry logic."""

    @pytest.mark.asyncio
    async def test_retry_on_file_lock_with_backoff(self, client: SharePointClient):
        """Retries with exponential backoff on HTTP 423 (file lock)."""
        client._access_token = "test-token"

        locked_response = MagicMock()
        locked_response.status_code = 423

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"values": []}

        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.request = AsyncMock(
            side_effect=[locked_response, success_response]
        )

        client._http_client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await client._request_with_retry("GET", "https://example.com/test")

        assert result.status_code == 200
        # First backoff: 1.0 * 2^0 = 1.0 second
        mock_sleep.assert_called_once_with(1.0)

    @pytest.mark.asyncio
    async def test_raises_file_lock_error_after_max_retries(self, client: SharePointClient):
        """Raises FileLockError after MAX_RETRIES exhausted."""
        client._access_token = "test-token"

        locked_response = MagicMock()
        locked_response.status_code = 423

        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.request = AsyncMock(return_value=locked_response)

        client._http_client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(FileLockError, match="File currently locked"):
                await client._request_with_retry("PATCH", "https://example.com/test")

        # Should have been called MAX_RETRIES times
        assert mock_client.request.call_count == client.MAX_RETRIES

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self, client: SharePointClient):
        """Retries on network connection errors."""
        client._access_token = "test-token"

        success_response = MagicMock()
        success_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.request = AsyncMock(
            side_effect=[httpx.ConnectError("Connection refused"), success_response]
        )

        client._http_client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await client._request_with_retry("GET", "https://example.com/test")

        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_raises_unavailable_after_network_retries_exhausted(self, client: SharePointClient):
        """Raises SharePointUnavailableError after all network retries fail."""
        client._access_token = "test-token"

        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.request = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        client._http_client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(SharePointUnavailableError):
                await client._request_with_retry("GET", "https://example.com/test")

    @pytest.mark.asyncio
    async def test_raises_write_error_for_5xx_on_write(self, client: SharePointClient):
        """Raises SharePointWriteError for 5xx on write operations."""
        client._access_token = "test-token"

        error_response = MagicMock()
        error_response.status_code = 503
        error_response.text = "Service Unavailable"

        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.request = AsyncMock(return_value=error_response)

        client._http_client = mock_client

        with pytest.raises(SharePointWriteError):
            await client._request_with_retry(
                "POST", "https://example.com/test", is_write=True
            )


class TestMonthlyFiles:
    """Tests for monthly file rotation logic."""

    @pytest.mark.asyncio
    async def test_create_monthly_estimations_file(self, client: SharePointClient):
        """create_monthly_file() creates estimations file with correct headers."""
        client._access_token = "test-token"

        with patch.object(client, "file_exists", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = False
            with patch.object(client, "_create_excel_file", new_callable=AsyncMock) as mock_create:
                await client.create_monthly_file("estimations", "2026-01")

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[0][0] == "Estimations_2026-01.xlsx"
        headers = call_args[0][1]
        assert "EstimationId" in headers
        assert "ProjectName" in headers

    @pytest.mark.asyncio
    async def test_create_monthly_auditlog_file(self, client: SharePointClient):
        """create_monthly_file() creates audit log file with correct headers."""
        client._access_token = "test-token"

        with patch.object(client, "file_exists", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = False
            with patch.object(client, "_create_excel_file", new_callable=AsyncMock) as mock_create:
                await client.create_monthly_file("auditlog", "2026-01")

        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[0][0] == "AuditLog_2026-01.xlsx"
        headers = call_args[0][1]
        assert "AuditId" in headers
        assert "EventType" in headers

    @pytest.mark.asyncio
    async def test_create_monthly_file_skips_if_exists(self, client: SharePointClient):
        """create_monthly_file() skips creation if file already exists."""
        client._access_token = "test-token"

        with patch.object(client, "file_exists", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = True
            with patch.object(client, "_create_excel_file", new_callable=AsyncMock) as mock_create:
                await client.create_monthly_file("estimations", "2026-01")

        mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_monthly_files_creates_both(self, client: SharePointClient):
        """ensure_monthly_files() creates both estimations and audit log files."""
        client._access_token = "test-token"

        with patch.object(client, "file_exists", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = False
            with patch.object(client, "create_monthly_file", new_callable=AsyncMock) as mock_create:
                await client.ensure_monthly_files("2026-02")

        assert mock_create.call_count == 2

    @pytest.mark.asyncio
    async def test_create_monthly_file_unknown_template_raises(self, client: SharePointClient):
        """create_monthly_file() raises error for unknown template type."""
        with pytest.raises(SharePointError, match="Unknown template type"):
            await client.create_monthly_file("unknown", "2026-01")

    def test_get_monthly_filename_estimations(self, client: SharePointClient):
        """get_monthly_filename() returns correct estimations filename."""
        result = client.get_monthly_filename("estimations", "2026-03")
        assert result == "Estimations_2026-03.xlsx"

    def test_get_monthly_filename_auditlog(self, client: SharePointClient):
        """get_monthly_filename() returns correct audit log filename."""
        result = client.get_monthly_filename("auditlog", "2026-03")
        assert result == "AuditLog_2026-03.xlsx"

    def test_get_monthly_filename_defaults_to_current_month(self, client: SharePointClient):
        """get_monthly_filename() uses current month when none specified."""
        result = client.get_monthly_filename("estimations")
        expected_month = datetime.now(timezone.utc).strftime("%Y-%m")
        assert result == f"Estimations_{expected_month}.xlsx"


class TestFileExists:
    """Tests for file_exists() method."""

    @pytest.mark.asyncio
    async def test_file_exists_returns_true(self, client: SharePointClient):
        """file_exists() returns True for HTTP 200."""
        client._access_token = "test-token"

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.get = AsyncMock(return_value=mock_response)

        client._http_client = mock_client

        result = await client.file_exists("Config.xlsx")
        assert result is True

    @pytest.mark.asyncio
    async def test_file_exists_returns_false_for_404(self, client: SharePointClient):
        """file_exists() returns False for non-200 response."""
        client._access_token = "test-token"

        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.get = AsyncMock(return_value=mock_response)

        client._http_client = mock_client

        result = await client.file_exists("NonExistent.xlsx")
        assert result is False

    @pytest.mark.asyncio
    async def test_file_exists_raises_on_network_error(self, client: SharePointClient):
        """file_exists() raises SharePointUnavailableError on network failure."""
        client._access_token = "test-token"

        mock_client = AsyncMock()
        mock_client.is_closed = False
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("No connection"))

        client._http_client = mock_client

        with pytest.raises(SharePointUnavailableError):
            await client.file_exists("Config.xlsx")


class TestWriteQueue:
    """Tests for write queue behavior."""

    @pytest.mark.asyncio
    async def test_pending_writes_count(self, client: SharePointClient):
        """pending_writes reflects queue size."""
        assert client.pending_writes == 0
        client._queue_write(operation="test", filename="test.xlsx")
        assert client.pending_writes == 1

    @pytest.mark.asyncio
    async def test_flush_write_queue_empty(self, client: SharePointClient):
        """flush_write_queue() returns empty list when queue is empty."""
        result = await client.flush_write_queue()
        assert result == []

    @pytest.mark.asyncio
    async def test_flush_write_queue_processes_operations(self, client: SharePointClient):
        """flush_write_queue() processes queued operations successfully."""
        client._access_token = "test-token"

        # Queue a write operation
        client._queue_write(
            operation="append_row",
            filename="Test.xlsx",
            sheet="Sheet1",
            row=["data"],
        )

        with patch.object(client, "append_row", new_callable=AsyncMock) as mock_append:
            result = await client.flush_write_queue()

        assert result == []
        assert client.pending_writes == 0
        mock_append.assert_called_once()
