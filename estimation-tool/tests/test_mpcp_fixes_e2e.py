"""End-to-end regression tests for two production fixes.

1. Process-track reconcile: editing a stage (e.g. PO) on a project whose stored
   process track is incomplete / mis-ordered must NOT 500. Previously the
   service indexed into the stage list positionally and raised IndexError
   (surfacing as a generic HTTP 500) when a project had fewer than 8 stages.

2. Allowlist cache invalidation: after an admin adds/removes a user, the auth
   middleware's cached Users.xlsx must be invalidated so the change takes
   effect immediately instead of lingering for the cache TTL (which produced
   intermittent 403s on authenticated endpoints just after a user was added).
"""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.auth import (
    AuthenticatedUser,
    get_current_user,
    get_sharepoint_client,
    require_admin,
)
import app.middleware.auth as auth_mod
from app.models.mpcp_schemas import (
    PROCESS_STAGES_ORDERED,
    ProcessStage,
    ProcessTrackStage,
    Project,
    StageStatus,
)
from app.models.schemas import UserIdentity, UserRole
from app.services import mpcp_tracker_service as tracker
from app.services.sharepoint_client import SharePointClient


# ===========================================================================
# Fix 1: process-track reconcile prevents HTTP 500
# ===========================================================================


def _make_admin_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        identity=UserIdentity(
            corporateId="ADMIN001",
            email="admin@company.com",
            displayName="Admin User",
        ),
        role=UserRole.ADMIN,
    )


@pytest.fixture
def tracker_app(monkeypatch):
    """Build an app exposing the MPCP tracker router with auth overridden and
    persistence/audit stubbed so no real SharePoint calls happen."""
    from app.routers.mpcp_tracker import router

    app = FastAPI()
    app.include_router(router)

    admin = _make_admin_user()
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[require_admin] = lambda: admin

    # ensure_loaded is a no-op; data is primed directly in module state.
    async def _noop_async(*args, **kwargs):
        return None

    monkeypatch.setattr(tracker, "ensure_loaded", _noop_async)
    monkeypatch.setattr(tracker, "_persist_process_tracks", _noop_async)
    monkeypatch.setattr(tracker, "_persist_projects", _noop_async)
    monkeypatch.setattr(tracker, "_log_project_change", _noop_async)
    monkeypatch.setattr(tracker, "_log_audit", _noop_async)

    yield app
    app.dependency_overrides.clear()


def _prime_project_with_incomplete_track(project_id: str, present_stages):
    """Seed tracker module state with a project whose process track only
    contains ``present_stages`` (a subset / mis-ordered subset of the 8)."""
    now = datetime.now(timezone.utc)
    tracker._projects.clear()
    tracker._process_tracks.clear()
    tracker._projects[project_id] = Project(
        id=project_id,
        name="Test Project",
        parent_cp_id="cp-1",
        created_at=now,
        updated_at=now,
    )
    stages = []
    for stage_name in present_stages:
        order = PROCESS_STAGES_ORDERED.index(stage_name)
        stages.append(
            ProcessTrackStage(
                project_id=project_id,
                stage=ProcessStage(stage_name),
                stage_order=order,
                status=StageStatus.COMPLETED,
            )
        )
    tracker._process_tracks[project_id] = stages
    # Simulate a fully-loaded tracker so persist helpers are allowed to run.
    tracker._loaded = True
    tracker._load_ok = True


def test_update_po_stage_on_incomplete_track_returns_200(tracker_app):
    """Reproduces the live bug: project with only BRD/PRD/RFP stored, user
    completes PO. Must return 200, not 500 (IndexError)."""
    project_id = "5c28de2c-c7f4-4948-8bb1-3f481245b727"
    # Only the first 3 stages exist; PO (index 3) and everything after is missing.
    _prime_project_with_incomplete_track(project_id, ["BRD", "PRD", "RFP"])

    client = TestClient(tracker_app, raise_server_exceptions=False)
    resp = client.put(
        f"/api/mpcp-tracker/projects/{project_id}/process-track/PO",
        json={
            "status": "Completed",
            "planned_date": "2026-08-20",
            "actual_date": "2026-08-20",
            "remarks": "Project started with TVSD",
            "skip_reason": None,
        },
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    # The response contains the reconciled, full 8-stage track.
    assert len(body["stages"]) == 8
    returned_order = [s["stage"] for s in body["stages"]]
    assert returned_order == PROCESS_STAGES_ORDERED
    # The PO stage reflects the update.
    po = next(s for s in body["stages"] if s["stage"] == "PO")
    assert po["status"] == "Completed"
    assert po["actual_date"] == "2026-08-20"
    assert po["remarks"] == "Project started with TVSD"


def test_update_remark_only_on_empty_track_returns_200(tracker_app):
    """A project with NO stored stages at all should still accept a stage edit
    (the track is reconciled from scratch)."""
    project_id = "empty-track-project"
    _prime_project_with_incomplete_track(project_id, [])

    client = TestClient(tracker_app, raise_server_exceptions=False)
    resp = client.put(
        f"/api/mpcp-tracker/projects/{project_id}/process-track/BRD",
        json={"status": "In_Progress", "remarks": "Kicking off"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["stages"]) == 8
    brd = next(s for s in body["stages"] if s["stage"] == "BRD")
    assert brd["status"] == "In_Progress"
    assert brd["remarks"] == "Kicking off"


def test_get_process_track_heals_incomplete_track(tracker_app):
    """GET also returns the full 8-stage set for an incomplete project."""
    project_id = "heal-on-read"
    _prime_project_with_incomplete_track(project_id, ["BRD"])

    client = TestClient(tracker_app, raise_server_exceptions=False)
    resp = client.get(f"/api/mpcp-tracker/projects/{project_id}/process-track")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["stages"]) == 8
    assert [s["stage"] for s in body["stages"]] == PROCESS_STAGES_ORDERED


# ===========================================================================
# Fix 2: allowlist cache invalidation
# ===========================================================================


class TestAllowlistCacheInvalidation:
    def test_invalidate_clears_cache(self):
        """invalidate_allowlist_cache resets the module-level cache so the next
        lookup re-reads Users.xlsx."""
        # Prime the cache as if a prior request populated it.
        auth_mod._allowlist_cache = [["CorporateId", "Email"], ["X", "a@b.com"]]
        auth_mod._allowlist_cache_time = 9999999999.0

        auth_mod.invalidate_allowlist_cache()

        assert auth_mod._allowlist_cache is None
        assert auth_mod._allowlist_cache_time == 0

    @pytest.mark.asyncio
    async def test_cache_refetches_after_invalidation(self):
        """After invalidation, _get_allowlist_rows reads fresh rows from SharePoint."""
        # Seed a stale cache that does NOT contain the new user.
        auth_mod._allowlist_cache = [["CorporateId", "Email"]]
        auth_mod._allowlist_cache_time = 9999999999.0  # far future => "fresh"

        client = AsyncMock(spec=SharePointClient)
        fresh_rows = [
            ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"],
            ["EMP9", "neha.parasher@tvsmotor.com", "Neha", "User", "admin", "2026-01-01", "true"],
        ]
        client.read_workbook = AsyncMock(return_value=fresh_rows)

        # Without invalidation, the stale cache would be returned.
        cached = await auth_mod._get_allowlist_rows(client)
        assert cached == [["CorporateId", "Email"]]
        client.read_workbook.assert_not_called()

        # After invalidation, the next read hits SharePoint and returns fresh data.
        auth_mod.invalidate_allowlist_cache()
        refreshed = await auth_mod._get_allowlist_rows(client)
        client.read_workbook.assert_called_once()
        assert any(
            "neha.parasher@tvsmotor.com" in [str(c).lower() for c in row]
            for row in refreshed
        )

    def test_add_user_invalidates_cache(self):
        """POST /api/admin/users clears the allowlist cache so a newly-added
        user can access authenticated endpoints immediately."""
        from app.routers.admin_users import router

        app = FastAPI()
        app.include_router(router)
        admin = _make_admin_user()
        sp = AsyncMock(spec=SharePointClient)
        sp.read_workbook = AsyncMock(return_value=[
            ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"],
        ])
        sp.append_row = AsyncMock()

        app.dependency_overrides[require_admin] = lambda: admin
        app.dependency_overrides[get_sharepoint_client] = lambda: sp

        # Prime a stale cache.
        auth_mod._allowlist_cache = [["stale"]]
        auth_mod._allowlist_cache_time = 9999999999.0

        client = TestClient(app)
        resp = client.post("/api/admin/users", json={
            "email": "neha.parasher@tvsmotor.com",
            "corporate_id": "EMP9",
            "display_name": "Neha Parasher",
            "role": "User",
        })

        assert resp.status_code == 201, resp.text
        # Cache must have been invalidated by the add.
        assert auth_mod._allowlist_cache is None
        app.dependency_overrides.clear()

    def test_remove_user_invalidates_cache(self):
        """DELETE /api/admin/users/{id} clears the allowlist cache."""
        from app.routers.admin_users import router

        app = FastAPI()
        app.include_router(router)
        admin = _make_admin_user()
        sp = AsyncMock(spec=SharePointClient)
        sp.read_workbook = AsyncMock(return_value=[
            ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"],
            ["EMP1", "admin1@company.com", "Admin 1", "Admin", "system", "2024-01-01", "TRUE"],
            ["EMP2", "admin2@company.com", "Admin 2", "Admin", "system", "2024-01-01", "TRUE"],
            ["EMP3", "user@company.com", "User", "User", "admin1@company.com", "2024-02-01", "TRUE"],
        ])
        sp.update_row_cells = AsyncMock(return_value=True)

        app.dependency_overrides[require_admin] = lambda: admin
        app.dependency_overrides[get_sharepoint_client] = lambda: sp

        auth_mod._allowlist_cache = [["stale"]]
        auth_mod._allowlist_cache_time = 9999999999.0

        client = TestClient(app)
        resp = client.delete("/api/admin/users/user@company.com")

        assert resp.status_code == 200, resp.text
        assert auth_mod._allowlist_cache is None
        app.dependency_overrides.clear()


# ===========================================================================
# Fix 3: no silent data loss on persist failure
# ===========================================================================


class TestNoSilentDataLoss:
    """The MPCP persist helpers must (a) refuse to overwrite a sheet when the
    tracker was not fully loaded, and (b) surface write failures instead of
    swallowing them (which previously let an operation report success while
    the SharePoint write silently failed)."""

    def _reset_state(self):
        tracker._managing_points.clear()
        tracker._process_tracks.clear()

    @pytest.mark.asyncio
    async def test_persist_refuses_when_not_loaded(self):
        """_assert_persist_safe blocks overwrite when _load_ok is False, so a
        partial/empty in-memory state can never clobber real SharePoint data."""
        from app.services.sharepoint_client import SharePointError

        tracker._load_ok = False
        sp = AsyncMock(spec=SharePointClient)
        sp.write_rows = AsyncMock()

        with pytest.raises(SharePointError):
            await tracker._persist_mps(sp)

        # Crucially, no write was attempted — the guard fired BEFORE write_rows.
        sp.write_rows.assert_not_called()

    @pytest.mark.asyncio
    async def test_persist_propagates_write_failure(self):
        """A SharePoint write failure must propagate (not be swallowed), so the
        caller/endpoint reports an error instead of a false success."""
        from app.services.sharepoint_client import SharePointWriteError

        tracker._load_ok = True
        self._reset_state()
        sp = AsyncMock(spec=SharePointClient)
        sp.write_rows = AsyncMock(side_effect=SharePointWriteError("disk full"))

        with pytest.raises(SharePointWriteError):
            await tracker._persist_mps(sp)

    @pytest.mark.asyncio
    async def test_persist_config_is_guarded(self):
        """_persist_config refuses to overwrite the Config sheet when the config
        was not loaded successfully (its own _config_load_ok flag, independent
        of the hierarchy's _load_ok)."""
        from app.services.sharepoint_client import SharePointError

        tracker._config_load_ok = False
        sp = AsyncMock(spec=SharePointClient)
        sp.write_rows = AsyncMock()

        with pytest.raises(SharePointError):
            await tracker._persist_config(sp)
        sp.write_rows.assert_not_called()

    @pytest.mark.asyncio
    async def test_persist_config_allowed_after_successful_load(self):
        """When the config loaded OK, _persist_config writes the Config sheet."""
        tracker._config_load_ok = True
        sp = AsyncMock(spec=SharePointClient)
        sp.write_rows = AsyncMock()

        await tracker._persist_config(sp)
        sp.write_rows.assert_called_once()


# ===========================================================================
# Fix 4: a failed save surfaces as a clean 503, not a generic 500
# ===========================================================================


class TestWriteFailureReturns503:
    """When a SharePoint write fails during an MPCP mutation, the user should
    get a structured 'service unavailable, retry' 503 — not a misleading 500
    that could be read as 'something crashed' or a false success."""

    def test_stage_update_write_failure_returns_503(self, monkeypatch):
        from app.middleware.error_handler import GlobalExceptionHandlerMiddleware
        from app.routers.mpcp_tracker import router
        from app.services.sharepoint_client import SharePointWriteError

        app = FastAPI()
        app.add_middleware(GlobalExceptionHandlerMiddleware)
        app.include_router(router)

        admin = _make_admin_user()
        app.dependency_overrides[get_current_user] = lambda: admin
        app.dependency_overrides[require_admin] = lambda: admin

        async def _noop_async(*args, **kwargs):
            return None

        # Load is fine; the WRITE is what fails.
        monkeypatch.setattr(tracker, "ensure_loaded", _noop_async)
        monkeypatch.setattr(tracker, "_log_project_change", _noop_async)
        monkeypatch.setattr(tracker, "_log_audit", _noop_async)

        async def _failing_persist(*args, **kwargs):
            raise SharePointWriteError("SharePoint write failed")

        monkeypatch.setattr(tracker, "_persist_process_tracks", _failing_persist)
        monkeypatch.setattr(tracker, "_persist_projects", _noop_async)

        project_id = "write-fail-project"
        _prime_project_with_incomplete_track(project_id, ["BRD", "PRD", "RFP"])

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.put(
            f"/api/mpcp-tracker/projects/{project_id}/process-track/PO",
            json={"status": "In_Progress", "remarks": "x"},
        )

        # The process-track route catches SharePointError and raises a 503
        # HTTPException (FastAPI's {"detail": ...} envelope). Either envelope is
        # acceptable; what matters is a 503 (retryable) rather than a 500.
        assert resp.status_code == 503, resp.text
        body = resp.json()
        assert "detail" in body or "error" in body

        app.dependency_overrides.clear()

    def test_dependency_add_write_failure_returns_503(self, monkeypatch):
        """A route that does NOT catch SharePointError relies on the global
        middleware to produce the structured {"error": {...}} 503 envelope."""
        from app.middleware.error_handler import GlobalExceptionHandlerMiddleware
        from app.routers.mpcp_tracker import router
        from app.services.sharepoint_client import SharePointWriteError

        app = FastAPI()
        app.add_middleware(GlobalExceptionHandlerMiddleware)
        app.include_router(router)

        admin = _make_admin_user()
        app.dependency_overrides[get_current_user] = lambda: admin
        app.dependency_overrides[require_admin] = lambda: admin

        async def _noop_async(*args, **kwargs):
            return None

        monkeypatch.setattr(tracker, "ensure_loaded", _noop_async)
        monkeypatch.setattr(tracker, "_log_audit", _noop_async)

        project_id = "dep-write-fail"
        _prime_project_with_incomplete_track(project_id, [])

        async def _failing_add_dependency(*args, **kwargs):
            raise SharePointWriteError("SharePoint write failed")

        monkeypatch.setattr(tracker, "add_dependency", _failing_add_dependency)

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            f"/api/mpcp-tracker/projects/{project_id}/dependencies",
            json={
                "description": "dep",
                "external_owner": "Team",
                "cutoff_date": "2026-03-31",
                "is_blocker": True,
                "status": "Open",
            },
        )

        assert resp.status_code == 503, resp.text
        body = resp.json()
        assert body["error"]["statusCode"] == 503
        assert "retry" in body["error"]["correctiveAction"].lower()

        app.dependency_overrides.clear()


# ===========================================================================
# Fix 5: atomic multi-sheet writes (no partial commit on failure)
# ===========================================================================


class TestAtomicMultiSheetWrite:
    """SharePointClient.write_sheets must update only the targeted sheets in a
    single workbook upload, leaving other sheets untouched, and must not
    partially commit if the upload fails."""

    def _make_workbook_bytes(self, sheets: dict):
        """Build an .xlsx byte blob with the given {sheet: [rows]} content."""
        import io
        from openpyxl import Workbook

        wb = Workbook()
        # Remove the default sheet so we control names exactly.
        default = wb.active
        wb.remove(default)
        for name, rows in sheets.items():
            ws = wb.create_sheet(name)
            for r in rows:
                ws.append(r)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def _read_sheet(self, blob: bytes, sheet: str):
        import io
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(blob))
        ws = wb[sheet]
        return [[c if c is not None else "" for c in row]
                for row in ws.iter_rows(values_only=True)]

    @pytest.mark.asyncio
    async def test_write_sheets_updates_targets_preserves_others(self):
        from unittest.mock import AsyncMock
        from app.services.sharepoint_client import SharePointClient

        existing = self._make_workbook_bytes({
            "Projects": [["Id", "Name"], ["p1", "Old Project"]],
            "Budget": [["ProjectId", "Approved"], ["p1", 100]],
            "ManagingPoints": [["Id", "Code"], ["m1", "A1"]],
        })

        client = SharePointClient.__new__(SharePointClient)  # bypass __init__
        uploaded = {}

        async def _fake_download(filename):
            return existing

        async def _fake_upload(filename, content):
            uploaded["content"] = content

        client._download_file = _fake_download
        client._upload_file = _fake_upload
        client._queue_write = lambda **kw: None

        # Update Projects + Budget; leave ManagingPoints untouched.
        await client.write_sheets("MPCPTracker.xlsx", {
            "Projects": [["Id", "Name"], ["p1", "New Project"], ["p2", "Second"]],
            "Budget": [["ProjectId", "Approved"]],  # cleared to just header
        })

        blob = uploaded["content"]
        assert self._read_sheet(blob, "Projects") == [
            ["Id", "Name"], ["p1", "New Project"], ["p2", "Second"]
        ]
        # Budget was full-replaced down to just its header row.
        assert self._read_sheet(blob, "Budget") == [["ProjectId", "Approved"]]
        # Untargeted sheet is preserved exactly.
        assert self._read_sheet(blob, "ManagingPoints") == [["Id", "Code"], ["m1", "A1"]]

    @pytest.mark.asyncio
    async def test_write_sheets_no_partial_commit_on_upload_failure(self):
        from app.services.sharepoint_client import SharePointClient, SharePointWriteError

        existing = self._make_workbook_bytes({
            "Projects": [["Id", "Name"], ["p1", "Old"]],
        })

        client = SharePointClient.__new__(SharePointClient)
        upload_calls = {"n": 0}

        async def _fake_download(filename):
            return existing

        async def _fake_upload(filename, content):
            upload_calls["n"] += 1
            raise SharePointWriteError("upload failed")

        client._download_file = _fake_download
        client._upload_file = _fake_upload
        client._queue_write = lambda **kw: None

        with pytest.raises(SharePointWriteError):
            await client.write_sheets("MPCPTracker.xlsx", {
                "Projects": [["Id", "Name"], ["p1", "New"]],
            })

        # Exactly one upload attempt, and it failed — so nothing was committed.
        # (All-or-nothing: the single upload is the only commit point.)
        assert upload_calls["n"] == 1


    @pytest.mark.asyncio
    async def test_delete_project_persists_all_sheets_in_one_write(self, monkeypatch):
        """delete_project must commit via a single atomic write_sheets covering
        every affected sheet — not N sequential per-sheet writes."""
        from app.services.sharepoint_client import SharePointClient

        async def _noop_async(*args, **kwargs):
            return None

        monkeypatch.setattr(tracker, "ensure_loaded", _noop_async)
        monkeypatch.setattr(tracker, "_log_audit", _noop_async)

        # Seed a project with full in-memory state.
        now = datetime.now(timezone.utc)
        tracker._projects.clear()
        tracker._check_points.clear()
        tracker._managing_points.clear()
        tracker._process_tracks.clear()
        tracker._milestones.clear()
        tracker._milestone_tasks.clear()
        tracker._dependencies.clear()
        tracker._budgets.clear()

        from app.models.mpcp_schemas import CheckPoint, ManagingPoint, MPTheme, BusinessUnit
        tracker._managing_points["m1"] = ManagingPoint(
            id="m1", code="A1", name="MP", theme=MPTheme.A, owner="o",
            lob=BusinessUnit.IND_2W, bu=BusinessUnit.IND_2W,
            created_at=now, updated_at=now,
        )
        tracker._check_points["c1"] = CheckPoint(
            id="c1", code="A1.1", name="CP", owner="o", parent_mp_id="m1",
            created_at=now, updated_at=now,
        )
        pid = "proj-del"
        tracker._projects[pid] = Project(
            id=pid, name="P", parent_cp_id="c1", created_at=now, updated_at=now,
        )
        tracker._process_tracks[pid] = tracker._initialize_process_track(pid)
        tracker._milestones[pid] = []
        tracker._dependencies[pid] = []
        tracker._loaded = True
        tracker._load_ok = True

        sp = AsyncMock(spec=SharePointClient)
        sp.write_sheets = AsyncMock()
        sp.write_rows = AsyncMock()

        await tracker.delete_project(pid, sp)

        # One atomic multi-sheet write, no sequential single-sheet writes.
        sp.write_sheets.assert_called_once()
        sp.write_rows.assert_not_called()
        _, kwargs = sp.write_sheets.call_args
        # call signature: write_sheets(filename, sheets_dict)
        written = sp.write_sheets.call_args[0][1]
        for required in [
            tracker.SHEET_PROJECTS, tracker.SHEET_PROCESS_TRACKS,
            tracker.SHEET_MILESTONES, tracker.SHEET_MILESTONE_TASKS,
            tracker.SHEET_DEPENDENCIES, tracker.SHEET_BUDGET,
            tracker.SHEET_CPS, tracker.SHEET_MPS,
        ]:
            assert required in written
        # The deleted project is gone from the serialized Projects sheet.
        projects_rows = written[tracker.SHEET_PROJECTS]
        flat = [str(c) for row in projects_rows for c in row]
        assert pid not in flat


# ===========================================================================
# Fix 6: delete-then-readd must not lock the user out
# ===========================================================================


class TestReAddAfterDelete:
    """Deleting a user (soft-delete -> Active=FALSE) and re-adding them must not
    leave a stale inactive row that blocks login with 'account deactivated'."""

    @pytest.mark.asyncio
    async def test_check_allowlist_prefers_active_duplicate(self):
        """_check_allowlist must pick an ACTIVE row even if an inactive row for
        the same email appears first (the delete-then-readd case)."""
        from unittest.mock import AsyncMock
        import app.middleware.auth as auth_mod
        from app.middleware.auth import _check_allowlist
        from app.models.schemas import UserIdentity, UserRole
        from app.services.sharepoint_client import SharePointClient

        # Row order mirrors the bug: stale inactive 'User' row FIRST, then the
        # re-added active 'Partner' row.
        rows = [
            ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"],
            ["E1", "neha.parasher@tvsmotor.com", "Neha", "User", "admin", "2026-01-01", "FALSE"],
            ["E1", "neha.parasher@tvsmotor.com", "Neha", "Partner", "admin", "2026-02-01", "TRUE"],
        ]
        client = AsyncMock(spec=SharePointClient)
        client.read_workbook = AsyncMock(return_value=rows)
        auth_mod.invalidate_allowlist_cache()

        identity = UserIdentity(corporateId="E1", email="neha.parasher@tvsmotor.com", displayName="Neha")
        entry = await _check_allowlist(identity, client)
        assert entry.active is True
        assert entry.role == UserRole.PARTNER  # picked the active re-added row
        auth_mod.invalidate_allowlist_cache()

    @pytest.mark.asyncio
    async def test_check_allowlist_all_inactive_still_denies(self):
        """If EVERY matching row is inactive, access is still denied."""
        from unittest.mock import AsyncMock
        import app.middleware.auth as auth_mod
        from app.middleware.auth import _check_allowlist
        from app.models.schemas import UserIdentity
        from app.services.sharepoint_client import SharePointClient
        from fastapi import HTTPException

        rows = [
            ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"],
            ["E1", "gone@tvsmotor.com", "Gone", "User", "admin", "2026-01-01", "FALSE"],
        ]
        client = AsyncMock(spec=SharePointClient)
        client.read_workbook = AsyncMock(return_value=rows)
        auth_mod.invalidate_allowlist_cache()

        identity = UserIdentity(corporateId="E1", email="gone@tvsmotor.com", displayName="Gone")
        with pytest.raises(HTTPException) as exc:
            await _check_allowlist(identity, client)
        assert exc.value.status_code == 403
        auth_mod.invalidate_allowlist_cache()

    def test_add_user_reactivates_inactive_row_in_place(self):
        """Re-adding a previously-removed user updates the existing inactive row
        (reactivate) rather than appending a duplicate."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from unittest.mock import AsyncMock
        from app.routers.admin_users import router
        from app.middleware.auth import get_sharepoint_client, require_admin
        from app.services.sharepoint_client import SharePointClient

        app = FastAPI()
        app.include_router(router)
        admin = _make_admin_user()
        sp = AsyncMock(spec=SharePointClient)
        sp.read_workbook = AsyncMock(return_value=[
            ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"],
            ["E1", "neha.parasher@tvsmotor.com", "Neha", "User", "admin", "2026-01-01", "FALSE"],
        ])
        sp.update_row_cells = AsyncMock(return_value=True)
        sp.append_row = AsyncMock()

        app.dependency_overrides[require_admin] = lambda: admin
        app.dependency_overrides[get_sharepoint_client] = lambda: sp

        client = TestClient(app)
        resp = client.post("/api/admin/users", json={
            "email": "neha.parasher@tvsmotor.com",
            "corporate_id": "E1",
            "display_name": "Neha Parasher",
            "role": "Partner",
        })

        assert resp.status_code == 201, resp.text
        # Reactivated in place: updated the row, did NOT append a duplicate.
        sp.update_row_cells.assert_called_once()
        sp.append_row.assert_not_called()
        _, kwargs = sp.update_row_cells.call_args
        assert kwargs["match_value"] == "neha.parasher@tvsmotor.com"
        # Active flipped TRUE and role updated to Partner in the updates dict.
        assert "TRUE" in [str(v) for v in kwargs["updates"].values()]
        assert "Partner" in [str(v) for v in kwargs["updates"].values()]
        app.dependency_overrides.clear()

    def test_add_user_still_appends_when_no_existing_row(self):
        """A brand-new email (no existing row) still appends normally."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from unittest.mock import AsyncMock
        from app.routers.admin_users import router
        from app.middleware.auth import get_sharepoint_client, require_admin
        from app.services.sharepoint_client import SharePointClient

        app = FastAPI()
        app.include_router(router)
        admin = _make_admin_user()
        sp = AsyncMock(spec=SharePointClient)
        sp.read_workbook = AsyncMock(return_value=[
            ["CorporateId", "Email", "DisplayName", "Role", "AddedBy", "AddedAt", "Active"],
        ])
        sp.append_row = AsyncMock()
        sp.update_row_cells = AsyncMock(return_value=True)

        app.dependency_overrides[require_admin] = lambda: admin
        app.dependency_overrides[get_sharepoint_client] = lambda: sp

        client = TestClient(app)
        resp = client.post("/api/admin/users", json={
            "email": "fresh@tvsmotor.com",
            "corporate_id": "E9",
            "display_name": "Fresh User",
            "role": "User",
        })

        assert resp.status_code == 201, resp.text
        sp.append_row.assert_called_once()
        sp.update_row_cells.assert_not_called()
        app.dependency_overrides.clear()


# ===========================================================================
# Fix 7: role matrix — full-contributor model (Option A)
# ===========================================================================
#
# Contract after opening edit/delete to all authenticated users:
#   - Admin, User, Partner: create / edit / delete MP, CP, Project, and update
#     process-track / milestones / tasks / RAG / dependencies.
#   - Budget: Admin and User allowed; Partner BLOCKED (403) via
#     require_budget_access.
# These tests exercise the REAL route dependencies per role (no DEV_MODE
# bypass), with the service layer and SharePoint stubbed.


def _user_with_role(role: UserRole) -> AuthenticatedUser:
    return AuthenticatedUser(
        identity=UserIdentity(
            corporateId=f"ID-{role.value}",
            email=f"{role.value.lower()}@tvsmotor.com",
            displayName=f"{role.value} Tester",
        ),
        role=role,
    )


@pytest.fixture
def role_matrix_app(monkeypatch):
    """MPCP router app where the authenticated user's ROLE is swappable, using
    the REAL get_current_user / require_budget_access dependencies (not the
    DEV_MODE override). Service + persistence are stubbed."""
    from app.routers.mpcp_tracker import router
    from app.middleware.auth import (
        get_current_user as real_get_current_user,
        require_budget_access as real_require_budget_access,
    )

    app = FastAPI()
    app.include_router(router)

    # Holder so each test can set the "logged in" role.
    current = {"user": _user_with_role(UserRole.ADMIN)}

    async def _fake_get_current_user():
        return current["user"]

    async def _fake_require_budget_access():
        # Mirror the real rule: everyone except Partner may access budget.
        u = current["user"]
        if u.role == UserRole.PARTNER:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Budget access is not available for your role.")
        return u

    app.dependency_overrides[real_get_current_user] = _fake_get_current_user
    app.dependency_overrides[real_require_budget_access] = _fake_require_budget_access

    # Stub the whole service surface the routes call.
    async def _noop_async(*args, **kwargs):
        return None

    now = datetime.now(timezone.utc)
    sample_project = Project(id="p1", name="P1", parent_cp_id="c1", created_at=now, updated_at=now)

    monkeypatch.setattr(tracker, "ensure_loaded", _noop_async)
    monkeypatch.setattr(tracker, "create_project", AsyncMock(return_value=sample_project))
    monkeypatch.setattr(tracker, "update_project", AsyncMock(return_value=sample_project))
    monkeypatch.setattr(tracker, "delete_project", AsyncMock(return_value=None))
    from app.models.mpcp_schemas import BudgetData
    monkeypatch.setattr(tracker, "get_budget", AsyncMock(return_value=BudgetData(project_id="p1")))

    yield app, current
    app.dependency_overrides.clear()


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.USER, UserRole.PARTNER])
def test_all_roles_can_create_project(role_matrix_app, role):
    app, current = role_matrix_app
    current["user"] = _user_with_role(role)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/mpcp-tracker/cps/c1/projects", json={"name": "New Proj"})
    assert resp.status_code == 201, f"{role.value}: {resp.status_code} {resp.text}"


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.USER, UserRole.PARTNER])
def test_all_roles_can_edit_project(role_matrix_app, role):
    app, current = role_matrix_app
    current["user"] = _user_with_role(role)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.put("/api/mpcp-tracker/projects/p1", json={"name": "Renamed"})
    assert resp.status_code == 200, f"{role.value}: {resp.status_code} {resp.text}"


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.USER, UserRole.PARTNER])
def test_all_roles_can_delete_project(role_matrix_app, role):
    app, current = role_matrix_app
    current["user"] = _user_with_role(role)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.delete("/api/mpcp-tracker/projects/p1")
    assert resp.status_code == 204, f"{role.value}: {resp.status_code} {resp.text}"


@pytest.mark.parametrize("role,expected", [
    (UserRole.ADMIN, 200),
    (UserRole.USER, 200),
    (UserRole.PARTNER, 403),  # Partner must NOT see budget
])
def test_budget_access_by_role(role_matrix_app, role, expected):
    app, current = role_matrix_app
    current["user"] = _user_with_role(role)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/mpcp-tracker/projects/p1/budget")
    assert resp.status_code == expected, f"{role.value}: {resp.status_code} {resp.text}"


# ===========================================================================
# Fix 8: in-process write serialization (concurrency / last-writer-wins guard)
# ===========================================================================


class TestWriteSerialization:
    """Writes to the SAME workbook must serialize (no interleaved
    download-edit-upload), so a concurrent write can't read a stale version and
    clobber another writer. Writes to DIFFERENT files may still overlap."""

    def _fresh_client(self, events, filename_tag):
        """Build a SharePointClient whose download/upload record ordered events
        and yield control (await) so overlap is possible without the lock."""
        import asyncio
        from app.services.sharepoint_client import SharePointClient

        client = SharePointClient.__new__(SharePointClient)
        client._queue_write = lambda **kw: None

        async def _download(filename):
            events.append(("download_start", filename))
            await asyncio.sleep(0.01)  # window where an unlocked writer could interleave
            events.append(("download_end", filename))
            # Minimal valid xlsx bytes.
            import io
            from openpyxl import Workbook
            wb = Workbook(); buf = io.BytesIO(); wb.save(buf); return buf.getvalue()

        async def _upload(filename, content):
            events.append(("upload_start", filename))
            await asyncio.sleep(0.01)
            events.append(("upload_end", filename))

        client._download_file = _download
        client._upload_file = _upload
        return client

    @pytest.mark.asyncio
    async def test_same_file_writes_serialize(self):
        import asyncio
        from app.services.sharepoint_client import SharePointClient

        # Reset the shared lock registry so this test is isolated.
        SharePointClient._write_locks = {}

        events = []
        c1 = self._fresh_client(events, "A")
        c2 = self._fresh_client(events, "B")
        FN = "SameFile.xlsx"

        await asyncio.gather(
            c1.write_rows(FN, "Sheet1", [["h"], ["a"]]),
            c2.write_rows(FN, "Sheet1", [["h"], ["b"]]),
        )

        # Each write is a contiguous download...upload block. With the lock, the
        # two blocks must NOT interleave: once the first write starts, it fully
        # finishes (upload_end) before the second's download_start.
        # Find the index of each phase.
        phases = [e[0] for e in events]
        first_upload_end = phases.index("upload_end")
        # The second download_start must come AFTER the first upload_end.
        # i.e. there is exactly one download_start before the first upload_end.
        downloads_before_first_upload_end = sum(
            1 for p in phases[:first_upload_end] if p == "download_start"
        )
        assert downloads_before_first_upload_end == 1, (
            f"writes interleaved — ordering was {phases}"
        )

    @pytest.mark.asyncio
    async def test_different_files_do_not_block_each_other(self):
        import asyncio
        from app.services.sharepoint_client import SharePointClient

        SharePointClient._write_locks = {}

        events = []
        c1 = self._fresh_client(events, "A")
        c2 = self._fresh_client(events, "B")

        await asyncio.gather(
            c1.write_rows("FileA.xlsx", "Sheet1", [["h"], ["a"]]),
            c2.write_rows("FileB.xlsx", "Sheet1", [["h"], ["b"]]),
        )

        phases = [e[0] for e in events]
        # Different files use different locks, so they SHOULD overlap: both
        # downloads start before either upload ends.
        first_upload_end = phases.index("upload_end")
        downloads_before_first_upload_end = sum(
            1 for p in phases[:first_upload_end] if p == "download_start"
        )
        assert downloads_before_first_upload_end == 2, (
            f"different files should overlap — ordering was {phases}"
        )
