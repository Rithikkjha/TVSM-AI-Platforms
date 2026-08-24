"""Tests for the audit service."""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.schemas import AuditGenerationEntry, AuditRevisionEntry, Domain, Stream
from app.services.audit_service import (
    AuditRevisionError,
    AuditServiceError,
    _extract_month_from_timestamp,
    _values_differ,
    get_project_history,
    record_generation,
    record_generation_with_estimation_id,
    record_revision,
)


class TestValuesDiffer:
    """Tests for the _values_differ helper."""

    def test_identical_dicts_return_false(self):
        d = {"a": 1, "b": 2}
        assert _values_differ(d, d.copy()) is False

    def test_different_values_return_true(self):
        prev = {"effort": 100, "cost": 5000}
        new = {"effort": 120, "cost": 5000}
        assert _values_differ(prev, new) is True

    def test_different_keys_return_true(self):
        prev = {"effort": 100}
        new = {"effort": 100, "cost": 5000}
        assert _values_differ(prev, new) is True

    def test_empty_dicts_return_false(self):
        assert _values_differ({}, {}) is False

    def test_nested_dicts_with_difference(self):
        prev = {"data": {"x": 1}}
        new = {"data": {"x": 2}}
        assert _values_differ(prev, new) is True


class TestExtractMonth:
    """Tests for _extract_month_from_timestamp."""

    def test_iso_format(self):
        assert _extract_month_from_timestamp("2026-03-15T10:30:00+00:00") == "2026-03"

    def test_iso_format_z_suffix(self):
        assert _extract_month_from_timestamp("2026-01-01T00:00:00Z") == "2026-01"

    def test_invalid_timestamp_returns_current_month(self):
        result = _extract_month_from_timestamp("not-a-date")
        expected = datetime.now(timezone.utc).strftime("%Y-%m")
        assert result == expected


class TestRecordGeneration:
    """Tests for record_generation."""

    @pytest.mark.asyncio
    async def test_record_generation_success(self):
        mock_client = AsyncMock()
        mock_client.ensure_monthly_files = AsyncMock()
        mock_client.append_row = AsyncMock()

        entry = AuditGenerationEntry(
            userId="user@example.com",
            projectName="Test Project",
            domain=Domain.SHOP,
            stream=Stream.D2C,
            inputTier=1,
            estimationValues={"totalEffortDays": 100},
            slmModelName="qwen3:4b",
            timestamp="2026-01-15T10:00:00+00:00",
        )

        audit_id = await record_generation(entry, mock_client)

        assert audit_id  # Non-empty UUID
        mock_client.ensure_monthly_files.assert_called_once_with("2026-01")
        mock_client.append_row.assert_called_once()

        # Verify the row content
        call_args = mock_client.append_row.call_args
        row = call_args[0][2]  # Third positional arg is the row
        assert row[1] == "generation"
        assert row[2] == "user@example.com"
        assert row[3] == "Test Project"
        assert row[4] == "Shop"
        assert row[5] == "D2C"

    @pytest.mark.asyncio
    async def test_record_generation_with_estimation_id(self):
        mock_client = AsyncMock()
        mock_client.ensure_monthly_files = AsyncMock()
        mock_client.append_row = AsyncMock()

        entry = AuditGenerationEntry(
            userId="user@example.com",
            projectName="Test Project",
            domain=Domain.BUY,
            stream=Stream.CHANNEL_PARTNER,
            inputTier=2,
            estimationValues={"totalEffortDays": 200},
            slmModelName="qwen3:4b",
            timestamp="2026-02-10T10:00:00+00:00",
        )

        audit_id = await record_generation_with_estimation_id(
            entry, "est-123", mock_client
        )

        assert audit_id
        call_args = mock_client.append_row.call_args
        row = call_args[0][2]
        assert row[11] == "est-123"  # EstimationId

    @pytest.mark.asyncio
    async def test_record_generation_sharepoint_error(self):
        mock_client = AsyncMock()
        mock_client.ensure_monthly_files = AsyncMock()
        mock_client.append_row = AsyncMock(side_effect=Exception("Write failed"))

        entry = AuditGenerationEntry(
            userId="user@example.com",
            projectName="Test Project",
            domain=Domain.SHOP,
            stream=Stream.D2C,
            inputTier=1,
            estimationValues={},
            slmModelName="qwen3:4b",
            timestamp="2026-01-15T10:00:00+00:00",
        )

        with pytest.raises(AuditServiceError):
            await record_generation(entry, mock_client)


class TestRecordRevision:
    """Tests for record_revision."""

    @pytest.mark.asyncio
    async def test_record_revision_success(self):
        mock_client = AsyncMock()
        mock_client.ensure_monthly_files = AsyncMock()
        mock_client.append_row = AsyncMock()

        entry = AuditRevisionEntry(
            userId="user@example.com",
            projectName="Test Project",
            domain=Domain.SHOP,
            stream=Stream.D2C,
            inputTier=2,
            previousValues={"effort": 100},
            newValues={"effort": 120},
            slmModelName="qwen3:4b",
            timestamp="2026-01-20T10:00:00+00:00",
            estimationId="est-456",
        )

        audit_id = await record_revision(entry, mock_client)

        assert audit_id
        mock_client.append_row.assert_called_once()
        call_args = mock_client.append_row.call_args
        row = call_args[0][2]
        assert row[1] == "revision"
        assert row[11] == "est-456"

    @pytest.mark.asyncio
    async def test_record_revision_identical_values_rejected(self):
        mock_client = AsyncMock()

        entry = AuditRevisionEntry(
            userId="user@example.com",
            projectName="Test Project",
            domain=Domain.SHOP,
            stream=Stream.D2C,
            inputTier=1,
            previousValues={"effort": 100, "cost": 5000},
            newValues={"effort": 100, "cost": 5000},
            slmModelName="qwen3:4b",
            timestamp="2026-01-20T10:00:00+00:00",
            estimationId="est-789",
        )

        with pytest.raises(AuditRevisionError, match="must differ"):
            await record_revision(entry, mock_client)

    @pytest.mark.asyncio
    async def test_record_revision_empty_dicts_rejected(self):
        mock_client = AsyncMock()

        entry = AuditRevisionEntry(
            userId="user@example.com",
            projectName="Test Project",
            domain=Domain.SHOP,
            stream=Stream.D2C,
            inputTier=1,
            previousValues={},
            newValues={},
            slmModelName="qwen3:4b",
            timestamp="2026-01-20T10:00:00+00:00",
            estimationId="est-789",
        )

        with pytest.raises(AuditRevisionError):
            await record_revision(entry, mock_client)


class TestGetProjectHistory:
    """Tests for get_project_history."""

    @pytest.mark.asyncio
    async def test_get_project_history_returns_matching_entries(self):
        mock_client = AsyncMock()

        # Simulate audit log rows
        rows = [
            ["AuditId", "EventType", "UserId", "ProjectName", "Domain",
             "Stream", "InputTier", "PreviousValues", "NewValues",
             "SLMModelName", "Timestamp", "EstimationId"],
            ["a1", "generation", "user1", "My Project", "Shop",
             "D2C", 1, "", '{"effort": 100}',
             "qwen3:4b", "2026-01-15T10:00:00+00:00", "est-1"],
            ["a2", "revision", "user2", "My Project", "Shop",
             "D2C", 2, '{"effort": 100}', '{"effort": 120}',
             "qwen3:4b", "2026-01-20T10:00:00+00:00", "est-2"],
            ["a3", "generation", "user1", "Other Project", "Buy",
             "D2C", 1, "", '{"effort": 50}',
             "qwen3:4b", "2026-01-16T10:00:00+00:00", "est-3"],
        ]
        mock_client.read_workbook = AsyncMock(return_value=rows)

        entries = await get_project_history("My Project", mock_client)

        assert len(entries) == 2
        assert entries[0].projectName == "My Project"
        assert entries[1].projectName == "My Project"
        # Verify chronological order
        assert entries[0].timestamp <= entries[1].timestamp

    @pytest.mark.asyncio
    async def test_get_project_history_empty_log(self):
        mock_client = AsyncMock()
        mock_client.read_workbook = AsyncMock(return_value=[])

        entries = await get_project_history("Nonexistent", mock_client)
        assert entries == []

    @pytest.mark.asyncio
    async def test_get_project_history_by_estimation_id(self):
        mock_client = AsyncMock()

        rows = [
            ["AuditId", "EventType", "UserId", "ProjectName", "Domain",
             "Stream", "InputTier", "PreviousValues", "NewValues",
             "SLMModelName", "Timestamp", "EstimationId"],
            ["a1", "generation", "user1", "Project A", "Shop",
             "D2C", 1, "", '{"effort": 100}',
             "qwen3:4b", "2026-01-15T10:00:00+00:00", "target-est"],
            ["a2", "generation", "user1", "Project B", "Buy",
             "D2C", 1, "", '{"effort": 50}',
             "qwen3:4b", "2026-01-16T10:00:00+00:00", "other-est"],
        ]
        mock_client.read_workbook = AsyncMock(return_value=rows)

        entries = await get_project_history(
            "Project A", mock_client, estimation_id="target-est"
        )

        assert len(entries) == 1
        assert entries[0].estimationId == "target-est"
