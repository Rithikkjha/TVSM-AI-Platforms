"""MPCP Tracker Service for the MPCP Project Tracker.

Handles:
- CRUD for Managing Points, Check Points, Projects
- Load/save hierarchy from SharePoint
- Process Track initialization and stage validation
- Vendor and PO validation
- Delete guards (cascading logic)
- RAG propagation orchestration

Requirements: 1, 2, 3, 4, 5
"""

import json
import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.models.mpcp_schemas import (
    BudgetData,
    BusinessUnit,
    CheckPoint,
    CPCreateRequest,
    CPUpdateRequest,
    Dependency,
    DependencyCreateRequest,
    DependencyStatus,
    DependencyUpdateRequest,
    ExecutionMilestone,
    ManagingPoint,
    MilestoneCreateRequest,
    MilestoneTask,
    MilestoneTaskCreateRequest,
    MilestoneTaskUpdateRequest,
    MilestoneUpdateRequest,
    MPCreateRequest,
    MPUpdateRequest,
    MPTheme,
    PROCESS_STAGES_ORDERED,
    ProcessStage,
    ProcessTrackStage,
    Project,
    ProjectCreateRequest,
    ProjectType,
    ProjectUpdateRequest,
    RAGContext,
    RAGHistoryEntry,
    RAGSeverity,
    RAGStatus,
    StageStatus,
    StageUpdateRequest,
    VALID_PRODUCT_OWNERS,
    VALID_VENDORS,
)
from app.services.sharepoint_client import (
    SharePointClient,
    SharePointError,
    SharePointUnavailableError,
    get_mpcp_tracker_file,
    get_mpcp_audit_folder,
)
from app.services.rag_engine import (
    compute_propagated_rag,
    create_rag_history_entry,
    validate_rag_context,
)
from app.services.execution_track_engine import (
    compute_slippage,
    is_delayed,
    update_milestone_computed_fields,
)
from app.services.mpcp_dependencies_service import (
    create_dependency as _create_dep,
    update_dependency as _update_dep,
)
from app.services.mpcp_budget_service import (
    create_default_budget,
)

logger = logging.getLogger(__name__)


# =============================================================================
# AUDIT LOGGING HELPER
# =============================================================================


async def _log_audit(
    event_type: str,
    entity_type: str,
    entity_id: str,
    user_name: str,
    details: str,
    sp: SharePointClient,
) -> None:
    """Append an audit row to the monthly MPCPAudit file.

    Writes to {get_mpcp_audit_folder()}/MPCPAudit_{YYYY-MM}.xlsx using sp.append_row().
    Silently logs errors without raising to avoid breaking CRUD operations.
    """
    try:
        now = datetime.now(timezone.utc)
        audit_file = f"{get_mpcp_audit_folder()}/MPCPAudit_{now.strftime('%Y-%m')}.xlsx"
        row = [
            now.isoformat(),
            event_type,
            entity_type,
            entity_id,
            user_name,
            details,
        ]
        await sp.append_row(filename=audit_file, sheet="Sheet1", row=row)
    except Exception as e:
        logger.warning(f"Audit log failed: {e}")


async def _log_project_change(
    project_id: str,
    field: str,
    old_value: str,
    new_value: str,
    changed_by: str,
    context: str,
    sp: SharePointClient,
) -> None:
    """Log a detailed project-level change to the ProjectChangeLog sheet.

    Records who changed what, old vs new value, with timestamp.
    Stored in-memory and persisted to the ProjectChangeLog sheet in MPCPTracker.xlsx.
    """
    try:
        now = datetime.now(timezone.utc)
        project_name = _projects.get(project_id, None)
        proj_name_str = project_name.name if project_name else project_id
        entry = {
            "timestamp": now.isoformat(),
            "project_id": project_id,
            "project_name": proj_name_str,
            "field": field,
            "old_value": old_value or "",
            "new_value": new_value or "",
            "changed_by": changed_by,
            "context": context,
        }
        # Store in memory — skip only if old_value is empty AND it's a date/status field (not budget/transaction)
        if not old_value and "budget" not in field and "transaction" not in field:
            return  # Skip logging first-time entries for non-financial fields
        if project_id not in _project_changelog:
            _project_changelog[project_id] = []
        _project_changelog[project_id].append(entry)
        # Persist to SharePoint
        tracker_file = get_mpcp_tracker_file()
        row = [
            entry["timestamp"],
            entry["project_id"],
            entry["project_name"],
            entry["field"],
            entry["old_value"],
            entry["new_value"],
            entry["changed_by"],
            entry["context"],
        ]
        await sp.append_row(filename=tracker_file, sheet=SHEET_PROJECT_CHANGELOG, row=row)
    except Exception as e:
        logger.warning(f"Project change log failed: {e}")


# Sheet names in MPCPTracker.xlsx (each sheet = one "table")
SHEET_MPS = "ManagingPoints"
SHEET_CPS = "CheckPoints"
SHEET_PROJECTS = "Projects"
SHEET_PROCESS_TRACKS = "ProcessTracks"
SHEET_MILESTONES = "ExecutionMilestones"
SHEET_MILESTONE_TASKS = "MilestoneTasks"
SHEET_RAG_CONTEXT_ENTRIES = "RAGContextEntries"
SHEET_DEPENDENCIES = "Dependencies"
SHEET_BUDGET = "Budget"
SHEET_RAG_HISTORY = "RAGHistory"
SHEET_PROJECT_CHANGELOG = "ProjectChangeLog"


# Predefined SDLC milestones auto-created when a project is created
DEFAULT_MILESTONES = [
    "Design & Architecture",
    "Environment & Pipeline Setup",
    "Development - Sprint(s)",
    "Integration & API Testing",
    "QA / Functional Testing",
    "Regression Testing",
    "Performance & Load Testing",
    "Security & Compliance Review",
    "UAT & Demo",
    "Deployment to Production",
    "Hypercare & Stabilization",
]


_active_fy_override: Optional[str] = None


def _tracker_file() -> str:
    """Get the MPCPTracker.xlsx path, respecting FY override."""
    if _active_fy_override:
        return f"ProjectTracker/{_active_fy_override}/MPCPTracker.xlsx"
    return get_mpcp_tracker_file()


def _audit_folder() -> str:
    """Get the current FY audit folder path."""
    return get_mpcp_audit_folder()


class MPCPTrackerError(Exception):
    """Base exception for tracker operations."""
    pass


class EntityNotFoundError(MPCPTrackerError):
    """Raised when an entity is not found."""
    pass


class DeleteGuardError(MPCPTrackerError):
    """Raised when delete is blocked by children."""
    pass


class StageValidationError(MPCPTrackerError):
    """Raised when stage transition is invalid."""
    pass


import re

def _natural_sort_key(text: str):
    """Natural sort: A1 < A2 < A10 < B1 (numbers sorted numerically within text)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]


# =============================================================================
# IN-MEMORY STORAGE (loaded from/persisted to SharePoint)
# =============================================================================

# These are module-level caches populated by load_hierarchy()
_managing_points: Dict[str, ManagingPoint] = {}
_check_points: Dict[str, CheckPoint] = {}
_projects: Dict[str, Project] = {}
_process_tracks: Dict[str, List[ProcessTrackStage]] = {}  # project_id → stages
_milestones: Dict[str, List[ExecutionMilestone]] = {}  # project_id → milestones
_milestone_tasks: Dict[str, List[MilestoneTask]] = {}  # milestone_id → tasks
_rag_context_entries: Dict[str, List[RAGContext]] = {}  # entity_id → list of 3W1H entries
_dependencies: Dict[str, List[Dependency]] = {}  # project_id → deps
_budgets: Dict[str, BudgetData] = {}  # project_id → budget
_rag_history: List[RAGHistoryEntry] = []
_project_changelog: Dict[str, List[dict]] = {}  # project_id → list of change entries
_loaded: bool = False
# True only after a load that fully succeeded (no SharePoint read failures).
# Persist helpers refuse to overwrite sheets when this is False, so a failed
# load can never cause the in-memory (possibly empty) state to clobber the
# real data in MPCPTracker.xlsx.
_load_ok: bool = False


async def ensure_loaded(sp: SharePointClient) -> None:
    """Ensure hierarchy is loaded from SharePoint. Loads once per process.

    If a prior load failed (SharePoint unavailable), ``_loaded`` stays False so
    the next request retries the load rather than serving (and later persisting)
    an empty in-memory state.
    """
    global _loaded
    if not _loaded:
        await load_hierarchy(sp)
        _loaded = True


async def load_hierarchy(sp: SharePointClient) -> None:
    """Load all data from SharePoint into memory.

    IMPORTANT — data-loss guard: a SharePoint read *failure* (connectivity /
    service unavailable) must NEVER be silently treated as "the sheet is
    empty". If it were, the empty in-memory state would later be persisted
    with a full-sheet overwrite and wipe the real data in MPCPTracker.xlsx.

    So on any ``SharePointError`` we abort the whole load and re-raise, leaving
    ``_load_ok`` False (persist helpers then refuse to overwrite). A missing
    sheet or a parse error on an otherwise-reachable file is a genuine "empty"
    case (e.g. first run) and is handled per-sheet.
    """
    global _managing_points, _check_points, _projects
    global _process_tracks, _milestones, _milestone_tasks, _rag_context_entries, _dependencies, _budgets, _rag_history
    global _load_ok

    _load_ok = False

    async def _read_sheet(sheet: str) -> list:
        """Read a sheet's rows. Re-raise on SharePoint failure (so the load
        aborts); return [] only when the file/sheet is genuinely reachable but
        absent/empty."""
        try:
            return await sp.read_workbook(_tracker_file(), sheet=sheet)
        except SharePointError:
            # Connectivity / service failure — do NOT treat as empty.
            raise
        except Exception as e:
            # Missing sheet, parse issue, etc. — safe to treat as empty.
            logger.warning(f"Sheet '{sheet}' unavailable, treating as empty: {e}")
            return []

    try:
        _managing_points = _parse_mps(await _read_sheet(SHEET_MPS))
        _check_points = _parse_cps(await _read_sheet(SHEET_CPS))
        _projects = _parse_projects(await _read_sheet(SHEET_PROJECTS))
        _process_tracks = _parse_process_tracks(await _read_sheet(SHEET_PROCESS_TRACKS))
        _milestones = _parse_milestones(await _read_sheet(SHEET_MILESTONES))
        _milestone_tasks = _parse_milestone_tasks(await _read_sheet(SHEET_MILESTONE_TASKS))
        _rag_context_entries = _parse_rag_context_entries(await _read_sheet(SHEET_RAG_CONTEXT_ENTRIES))
    except SharePointError as e:
        logger.error(
            f"MPCP tracker load aborted — SharePoint read failed: {e}. "
            f"In-memory state left untouched; persists are disabled until a "
            f"successful reload."
        )
        raise

    # Attach RAG context entries to milestones and tasks
    for ms_list in _milestones.values():
        for m in ms_list:
            m.rag_context = _rag_context_entries.get(m.id, [])
    for tasks in _milestone_tasks.values():
        for t in tasks:
            t.rag_context = _rag_context_entries.get(t.id, [])

    try:
        _dependencies = _parse_dependencies(await _read_sheet(SHEET_DEPENDENCIES))

        _budgets = _parse_budgets(await _read_sheet(SHEET_BUDGET))
        # Recompute budget fields to ensure correct formula
        from app.services.mpcp_budget_service import _recompute
        for b in _budgets.values():
            _recompute(b)

        _rag_history = _parse_rag_history(await _read_sheet(SHEET_RAG_HISTORY))
    except SharePointError as e:
        logger.error(
            f"MPCP tracker load aborted — SharePoint read failed: {e}. "
            f"In-memory state left untouched; persists are disabled until a "
            f"successful reload."
        )
        raise

    # Load project changelog
    try:
        rows = await sp.read_workbook(_tracker_file(), sheet=SHEET_PROJECT_CHANGELOG)
        _project_changelog.clear()
        if rows and len(rows) > 1:
            for row in rows[1:]:
                if not row or len(row) < 7:
                    continue
                pid = str(row[1]).strip()
                entry = {
                    "timestamp": str(row[0]).strip(),
                    "project_id": pid,
                    "project_name": str(row[2]).strip(),
                    "field": str(row[3]).strip(),
                    "old_value": str(row[4]).strip(),
                    "new_value": str(row[5]).strip(),
                    "changed_by": str(row[6]).strip(),
                    "context": str(row[7]).strip() if len(row) > 7 else "",
                }
                if pid not in _project_changelog:
                    _project_changelog[pid] = []
                _project_changelog[pid].append(entry)
    except Exception:
        pass  # Sheet may not exist yet

    # Seed the "Others (Non-MPCP)" theme Z hierarchy if missing
    await _seed_others_theme(sp)

    # Recompute counts and propagated RAG
    _recompute_counts()
    _recompute_all_propagation()

    # Load fully succeeded (all SharePoint reads returned without a transport
    # failure). Only now is it safe for persist helpers to overwrite sheets.
    _load_ok = True

    logger.info(
        f"Loaded MPCP hierarchy: {len(_managing_points)} MPs, "
        f"{len(_check_points)} CPs, {len(_projects)} Projects"
    )


async def _seed_others_theme(sp: SharePointClient) -> None:
    """Auto-create the Theme Z 'Others (Non-MPCP)' hierarchy if it doesn't exist.

    Creates 3 MPs (Z1/Z2/Z3) each with one CP, to hold non-MPCP initiatives:
      Z1 NPI/CFT              → Z1.1 New Product Launches      (SOP Type 2)
      Z2 Business-led 3P–D&AI → Z2.1 3P Solutions             (SOP Type 4)
      Z3 Unplanned Initiative → Z3.1 Others                   (SOP Type 5)

    Idempotent: keyed by MP/CP code, so restarts won't duplicate.
    Uses deterministic IDs so references stay stable.
    Owner and LoB/BU are placeholders ('TBD' / IND-2W) to be edited later.
    """
    global _managing_points, _check_points

    seed_spec = [
        # (mp_code, mp_name, cp_code, cp_name)
        ("Z1", "NPI/CFT", "Z1.1", "New Product Launches"),
        ("Z2", "Business-led 3P — D&AI", "Z2.1", "3P Solutions"),
        ("Z3", "Unplanned Initiative", "Z3.1", "Others"),
    ]

    existing_mp_codes = {mp.code for mp in _managing_points.values()}
    existing_cp_codes = {cp.code for cp in _check_points.values()}
    now = datetime.now(timezone.utc)
    changed = False

    for mp_code, mp_name, cp_code, cp_name in seed_spec:
        mp_id = f"mp-seed-{mp_code.lower()}"
        cp_id = f"cp-seed-{cp_code.lower().replace('.', '-')}"

        if mp_code not in existing_mp_codes:
            _managing_points[mp_id] = ManagingPoint(
                id=mp_id,
                code=mp_code,
                name=mp_name,
                theme=MPTheme.Z,
                owner="TBD",
                lob=BusinessUnit.IND_2W,
                bu=BusinessUnit.IND_2W,
                rag_status=RAGStatus.GREEN,
                created_at=now,
                updated_at=now,
                created_by="system-seed",
            )
            changed = True

        # Resolve the MP id in case it already existed under a different id
        parent_mp_id = mp_id
        for mp in _managing_points.values():
            if mp.code == mp_code:
                parent_mp_id = mp.id
                break

        if cp_code not in existing_cp_codes:
            _check_points[cp_id] = CheckPoint(
                id=cp_id,
                code=cp_code,
                name=cp_name,
                owner="TBD",
                description="Auto-created bucket for Non-MPCP initiatives.",
                parent_mp_id=parent_mp_id,
                rag_status=RAGStatus.GREEN,
                created_at=now,
                updated_at=now,
                created_by="system-seed",
            )
            changed = True

    if changed:
        try:
            await _persist_mps(sp)
            await _persist_cps(sp)
            logger.info("Seeded Theme Z (Others / Non-MPCP) hierarchy.")
        except Exception as e:
            logger.warning(f"Failed to persist seeded Theme Z hierarchy: {e}")


# =============================================================================
# MANAGING POINT CRUD
# =============================================================================


async def create_mp(
    request: MPCreateRequest,
    user_name: str,
    sp: SharePointClient,
) -> ManagingPoint:
    """Create a new Managing Point."""
    await ensure_loaded(sp)
    now = datetime.now(timezone.utc)
    mp = ManagingPoint(
        id=str(uuid.uuid4()),
        code=request.code,
        name=request.name,
        theme=request.theme,
        owner=request.owner,
        lob=request.lob,
        bu=request.bu,
        uom=request.uom,
        target_from=request.target_from,
        target_to=request.target_to,
        rag_status=RAGStatus.GREEN,
        created_at=now,
        updated_at=now,
        created_by=user_name,
    )
    _managing_points[mp.id] = mp
    await _persist_mps(sp)
    await _log_audit("created", "MP", mp.id, user_name, f"Created MP {mp.code} - {mp.name}", sp)
    return mp


async def get_mp(mp_id: str, sp: SharePointClient) -> ManagingPoint:
    """Get a Managing Point by ID."""
    await ensure_loaded(sp)
    if mp_id not in _managing_points:
        raise EntityNotFoundError(f"Managing Point {mp_id} not found")
    return _managing_points[mp_id]


async def list_mps(
    sp: SharePointClient,
    theme_filter: Optional[MPTheme] = None,
) -> List[ManagingPoint]:
    """List all Managing Points, optionally filtered by theme. Natural sort by code."""
    await ensure_loaded(sp)
    mps = list(_managing_points.values())
    if theme_filter:
        mps = [m for m in mps if m.theme == theme_filter]
    mps.sort(key=lambda m: _natural_sort_key(m.code))
    return mps


async def update_mp(
    mp_id: str,
    request: MPUpdateRequest,
    sp: SharePointClient,
) -> ManagingPoint:
    """Update a Managing Point."""
    await ensure_loaded(sp)
    mp = await get_mp(mp_id, sp)
    if request.code is not None:
        mp.code = request.code
    if request.name is not None:
        mp.name = request.name
    if request.theme is not None:
        mp.theme = request.theme
    if request.owner is not None:
        mp.owner = request.owner
    if request.lob is not None:
        mp.lob = request.lob
    if request.bu is not None:
        mp.bu = request.bu
    if request.uom is not None:
        mp.uom = request.uom
    if request.target_from is not None:
        mp.target_from = request.target_from
    if request.target_to is not None:
        mp.target_to = request.target_to
    mp.updated_at = datetime.now(timezone.utc)
    _managing_points[mp_id] = mp
    await _persist_mps(sp)
    await _log_audit("updated", "MP", mp_id, mp.owner, f"Updated MP {mp.code}", sp)
    return mp


async def delete_mp(mp_id: str, sp: SharePointClient) -> None:
    """Delete a Managing Point. Must have 0 CPs."""
    await ensure_loaded(sp)
    if mp_id not in _managing_points:
        raise EntityNotFoundError(f"Managing Point {mp_id} not found")
    child_cps = [c for c in _check_points.values() if c.parent_mp_id == mp_id]
    if child_cps:
        raise DeleteGuardError(
            f"Cannot delete MP: it has {len(child_cps)} Check Points. Remove them first."
        )
    del _managing_points[mp_id]
    await _persist_mps(sp)
    await _log_audit("deleted", "MP", mp_id, "", f"Deleted MP", sp)


# =============================================================================
# CHECK POINT CRUD
# =============================================================================


async def create_cp(
    mp_id: str,
    request: CPCreateRequest,
    user_name: str,
    sp: SharePointClient,
) -> CheckPoint:
    """Create a Check Point under an MP."""
    await ensure_loaded(sp)
    if mp_id not in _managing_points:
        raise EntityNotFoundError(f"Managing Point {mp_id} not found")
    now = datetime.now(timezone.utc)
    cp = CheckPoint(
        id=str(uuid.uuid4()),
        code=request.code,
        name=request.name,
        owner=request.owner,
        description=request.description,
        domain=request.domain,
        stream=request.stream,
        uom=request.uom,
        target_from=request.target_from,
        target_to=request.target_to,
        target_quarter=request.target_quarter,
        parent_mp_id=mp_id,
        rag_status=RAGStatus.GREEN,
        created_at=now,
        updated_at=now,
        created_by=user_name,
    )
    _check_points[cp.id] = cp
    _recompute_counts()
    _propagate_for_cp(cp.id)
    await _persist_sheets(sp, [SHEET_CPS, SHEET_MPS])
    await _log_audit("created", "CP", cp.id, user_name, f"Created CP {cp.code} - {cp.name} under MP {mp_id}", sp)
    return cp


async def get_cp(cp_id: str, sp: SharePointClient) -> CheckPoint:
    """Get a Check Point by ID."""
    await ensure_loaded(sp)
    if cp_id not in _check_points:
        raise EntityNotFoundError(f"Check Point {cp_id} not found")
    return _check_points[cp_id]


async def list_cps(
    mp_id: str,
    sp: SharePointClient,
) -> List[CheckPoint]:
    """List all Check Points under an MP, natural sorted by code."""
    await ensure_loaded(sp)
    cps = [c for c in _check_points.values() if c.parent_mp_id == mp_id]
    cps.sort(key=lambda c: _natural_sort_key(c.code))
    return cps


async def update_cp(
    cp_id: str,
    request: CPUpdateRequest,
    sp: SharePointClient,
) -> CheckPoint:
    """Update a Check Point."""
    await ensure_loaded(sp)
    cp = await get_cp(cp_id, sp)
    if request.code is not None:
        cp.code = request.code
    if request.name is not None:
        cp.name = request.name
    if request.owner is not None:
        cp.owner = request.owner
    if request.description is not None:
        cp.description = request.description
    if request.domain is not None:
        cp.domain = request.domain
    if request.stream is not None:
        cp.stream = request.stream
    if request.uom is not None:
        cp.uom = request.uom
    if request.target_from is not None:
        cp.target_from = request.target_from
    if request.target_to is not None:
        cp.target_to = request.target_to
    if request.target_quarter is not None:
        cp.target_quarter = request.target_quarter
    cp.updated_at = datetime.now(timezone.utc)
    _check_points[cp_id] = cp
    await _persist_cps(sp)
    await _log_audit("updated", "CP", cp_id, cp.owner, f"Updated CP {cp.code}", sp)
    return cp


async def delete_cp(cp_id: str, sp: SharePointClient) -> None:
    """Delete a Check Point. Must have 0 Projects."""
    await ensure_loaded(sp)
    if cp_id not in _check_points:
        raise EntityNotFoundError(f"Check Point {cp_id} not found")
    child_projects = [p for p in _projects.values() if p.parent_cp_id == cp_id]
    if child_projects:
        raise DeleteGuardError(
            f"Cannot delete CP: it has {len(child_projects)} Projects. Remove them first."
        )
    mp_id = _check_points[cp_id].parent_mp_id
    del _check_points[cp_id]
    _recompute_counts()
    _propagate_for_mp(mp_id)
    await _persist_sheets(sp, [SHEET_CPS, SHEET_MPS])
    await _log_audit("deleted", "CP", cp_id, "", f"Deleted CP", sp)


# =============================================================================
# PROJECT CRUD
# =============================================================================


async def create_project(
    cp_id: str,
    request: ProjectCreateRequest,
    user_name: str,
    sp: SharePointClient,
) -> Project:
    """Create a Project under a CP."""
    await ensure_loaded(sp)
    if cp_id not in _check_points:
        raise EntityNotFoundError(f"Check Point {cp_id} not found")
    now = datetime.now(timezone.utc)
    project = Project(
        id=str(uuid.uuid4()),
        name=request.name,
        project_type=request.project_type,
        vendor=request.vendor,
        product_owner=request.product_owner,
        engg_poc=request.engg_poc,
        lob=request.lob,
        bu=request.bu,
        domain=request.domain,
        stream=request.stream,
        description=request.description,
        parent_cp_id=cp_id,
        rag_status=RAGStatus.GREEN,
        current_stage=ProcessStage.BRD,
        created_at=now,
        updated_at=now,
        created_by=user_name,
    )
    _projects[project.id] = project

    # Initialize process track (8 stages)
    _process_tracks[project.id] = _initialize_process_track(project.id)

    # Initialize empty milestone list and budget
    _milestones[project.id] = []
    _dependencies[project.id] = []
    _budgets[project.id] = create_default_budget(project.id)

    # Auto-create 11 default SDLC milestones
    for ms_name in DEFAULT_MILESTONES:
        milestone = ExecutionMilestone(
            id=str(uuid.uuid4()),
            project_id=project.id,
            name=ms_name,
            vendor="",
        )
        _milestones[project.id].append(milestone)

    _recompute_counts()
    _propagate_for_project(project.id)
    # Atomic: all five affected sheets commit in one workbook write.
    await _persist_sheets(sp, [
        SHEET_PROJECTS, SHEET_MILESTONES, SHEET_PROCESS_TRACKS,
        SHEET_CPS, SHEET_MPS,
    ])
    await _log_audit("created", "Project", project.id, user_name, f"Created Project {project.name} under CP {cp_id}", sp)
    return project


async def get_project(project_id: str, sp: SharePointClient) -> Project:
    """Get a Project by ID."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    return _projects[project_id]


async def list_projects(
    cp_id: str,
    sp: SharePointClient,
) -> List[Project]:
    """List all Projects under a CP."""
    await ensure_loaded(sp)
    return [p for p in _projects.values() if p.parent_cp_id == cp_id]


async def list_all_projects(sp: SharePointClient) -> List[Project]:
    """List all projects across the hierarchy."""
    await ensure_loaded(sp)
    return list(_projects.values())


async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    sp: SharePointClient,
) -> Project:
    """Update a Project."""
    await ensure_loaded(sp)
    project = await get_project(project_id, sp)
    if request.name is not None:
        project.name = request.name
    if request.project_type is not None:
        project.project_type = request.project_type
    if request.vendor is not None:
        project.vendor = request.vendor
    if request.product_owner is not None:
        project.product_owner = request.product_owner
    if request.engg_poc is not None:
        project.engg_poc = request.engg_poc
    if request.lob is not None:
        project.lob = request.lob
    if request.bu is not None:
        project.bu = request.bu
    if request.domain is not None:
        project.domain = request.domain
    if request.stream is not None:
        project.stream = request.stream
    if request.description is not None:
        project.description = request.description
    if request.revised_target_date is not None:
        project.revised_target_date = request.revised_target_date
    project.updated_at = datetime.now(timezone.utc)
    _projects[project_id] = project
    await _persist_projects(sp)
    # Log key project field changes to changelog
    user = project.product_owner or ""
    if request.name is not None:
        await _log_project_change(project_id, "project.name", "", request.name, user, "Project updated", sp)
    if request.vendor is not None:
        await _log_project_change(project_id, "project.vendor", "", request.vendor, user, "Project updated", sp)
    if request.revised_target_date is not None:
        await _log_project_change(project_id, "project.revised_target_date", "", str(request.revised_target_date), user, "Target date revised", sp)
    await _log_audit("updated", "Project", project_id, user, f"Updated Project {project.name}", sp)
    return project


async def move_project(
    project_id: str,
    target_cp_id: str,
    user_name: str,
    sp: SharePointClient,
) -> Project:
    """Move a Project to a different Check Point (reassign parent_cp_id).

    Recomputes counts and RAG propagation for both the old and new CPs.
    All project track data (process, milestones, dependencies, budget) stays
    with the project since they are keyed by project_id, not CP.
    """
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    if target_cp_id not in _check_points:
        raise EntityNotFoundError(f"Check Point {target_cp_id} not found")

    project = _projects[project_id]
    old_cp_id = project.parent_cp_id
    if old_cp_id == target_cp_id:
        return project  # no-op

    old_cp = _check_points.get(old_cp_id)
    new_cp = _check_points.get(target_cp_id)
    old_label = old_cp.code if old_cp else old_cp_id
    new_label = new_cp.code if new_cp else target_cp_id

    project.parent_cp_id = target_cp_id
    project.updated_at = datetime.now(timezone.utc)
    _projects[project_id] = project

    _recompute_counts()
    # Re-propagate RAG for both old and new parent CPs
    if old_cp_id:
        _propagate_for_cp(old_cp_id)
    _propagate_for_cp(target_cp_id)

    await _persist_sheets(sp, [SHEET_PROJECTS, SHEET_CPS, SHEET_MPS])
    await _log_project_change(
        project_id, "project.parent_cp", old_label, new_label,
        user_name, "Project moved to a different Check Point", sp,
    )
    await _log_audit("moved", "Project", project_id, user_name,
                     f"Moved Project {project.name} from {old_label} to {new_label}", sp)
    return project


async def delete_project(project_id: str, sp: SharePointClient) -> None:
    """Delete a Project and all associated track data."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    cp_id = _projects[project_id].parent_cp_id
    # Clean up milestone tasks for all milestones in this project
    for m in _milestones.get(project_id, []):
        _milestone_tasks.pop(m.id, None)
    del _projects[project_id]
    _process_tracks.pop(project_id, None)
    _milestones.pop(project_id, None)
    _dependencies.pop(project_id, None)
    _budgets.pop(project_id, None)
    _recompute_counts()
    _propagate_for_cp(cp_id)
    # Atomic: all eight affected sheets commit in one workbook write, so a
    # delete can never leave orphaned child rows (process track, milestones,
    # tasks, dependencies, budget) behind a removed project.
    await _persist_sheets(sp, [
        SHEET_PROJECTS, SHEET_PROCESS_TRACKS, SHEET_MILESTONES,
        SHEET_MILESTONE_TASKS, SHEET_DEPENDENCIES, SHEET_BUDGET,
        SHEET_CPS, SHEET_MPS,
    ])
    await _log_audit("deleted", "Project", project_id, "", f"Deleted Project and all track data", sp)


# =============================================================================
# PROCESS TRACK
# =============================================================================


async def get_process_track(
    project_id: str,
    sp: SharePointClient,
) -> List[ProcessTrackStage]:
    """Get all 8 process track stages for a project."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    # Always return the canonical, fully-ordered 8-stage set. Projects whose
    # stored track is incomplete/mis-ordered are healed in memory so the UI
    # renders all stages and later edits index safely.
    stages = _reconcile_process_track(project_id, _process_tracks.get(project_id, []))
    _process_tracks[project_id] = stages
    return stages


async def update_stage(
    project_id: str,
    stage: ProcessStage,
    request: StageUpdateRequest,
    user_name: str,
    sp: SharePointClient,
) -> List[ProcessTrackStage]:
    """Update a process track stage with sequential validation."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")

    # Reconcile the project's process track against the canonical 8-stage set.
    # Historical/partial data (or a row that failed to parse) can leave a
    # project with missing or mis-ordered stages. Operating on such a list by
    # positional index raises IndexError and surfaces as a generic HTTP 500.
    # Rebuild the full ordered set here, preserving any existing stage data,
    # so the lookup below is always safe and the data self-heals on save.
    stages = _reconcile_process_track(project_id, _process_tracks.get(project_id, []))
    target_idx = PROCESS_STAGES_ORDERED.index(stage.value)

    # Sequential validation: Can't advance a stage unless all preceding are Completed/Skipped
    if request.status in (StageStatus.IN_PROGRESS, StageStatus.COMPLETED, StageStatus.SKIPPED):
        for i in range(target_idx):
            if stages[i].status not in (StageStatus.COMPLETED, StageStatus.SKIPPED):
                raise StageValidationError(
                    f"Cannot update {stage.value}: preceding stage "
                    f"'{PROCESS_STAGES_ORDERED[i]}' is {stages[i].status.value}. "
                    f"All preceding stages must be Completed or Skipped first."
                )

    # Capture old values for change log
    old_stage = stages[target_idx]
    old_status = old_stage.status.value if old_stage.status else "Not_Started"
    old_planned = str(old_stage.planned_date) if old_stage.planned_date else ""
    old_actual = str(old_stage.actual_date) if old_stage.actual_date else ""
    old_remarks = old_stage.remarks or ""

    # Apply update — only update fields that are explicitly provided
    stages[target_idx].status = request.status
    if request.planned_date is not None:
        stages[target_idx].planned_date = request.planned_date
    if request.actual_date is not None:
        stages[target_idx].actual_date = request.actual_date
    if request.remarks is not None:
        stages[target_idx].remarks = request.remarks
    if request.skip_reason is not None:
        stages[target_idx].skip_reason = request.skip_reason

    # Update project's current_stage
    _projects[project_id].current_stage = _compute_current_stage(stages)
    _projects[project_id].updated_at = datetime.now(timezone.utc)

    _process_tracks[project_id] = stages
    await _persist_process_tracks(sp)
    await _persist_projects(sp)

    # Log detailed changes to ProjectChangeLog
    new_status = request.status.value
    new_planned = str(request.planned_date) if request.planned_date else old_planned
    new_actual = str(request.actual_date) if request.actual_date else old_actual
    new_remarks = request.remarks if request.remarks is not None else old_remarks

    if old_status != new_status:
        await _log_project_change(project_id, f"{stage.value}.status", old_status, new_status, user_name, f"Stage status changed", sp)
    if request.planned_date is not None and old_planned != new_planned:
        await _log_project_change(project_id, f"{stage.value}.planned_date", old_planned, new_planned, user_name, f"Planned date updated", sp)
    if request.actual_date is not None and old_actual != new_actual:
        await _log_project_change(project_id, f"{stage.value}.actual_date", old_actual, new_actual, user_name, f"Actual date updated", sp)
    if request.remarks is not None and old_remarks != new_remarks:
        await _log_project_change(project_id, f"{stage.value}.remarks", old_remarks, new_remarks, user_name, f"Remarks updated", sp)

    await _log_audit("stage_updated", "Project", project_id, user_name, f"Stage {stage.value} set to {request.status.value}", sp)
    return stages


# =============================================================================
# PROJECT CHANGE LOG
# =============================================================================


async def get_project_changelog(
    project_id: str,
    sp: SharePointClient,
) -> list[dict]:
    """Read the ProjectChangeLog for a specific project (in-memory + SharePoint fallback)."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")

    # Return from in-memory store (most recent first)
    entries = list(_project_changelog.get(project_id, []))
    entries.reverse()
    return entries


# =============================================================================
# EXECUTION TRACK (MILESTONES)
# =============================================================================


async def get_milestones(
    project_id: str,
    sp: SharePointClient,
) -> List[ExecutionMilestone]:
    """Get milestones for a project, sorted by planned_start (None last).
    
    Infers milestone dates from tasks when not explicitly set.
    """
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    ms = _milestones.get(project_id, [])
    
    # Infer dates from tasks for milestones without explicit dates
    for m in ms:
        if not m.planned_start or not m.planned_end:
            tasks = _milestone_tasks.get(m.id, [])
            if tasks:
                task_starts = [t.planned_start for t in tasks if t.planned_start]
                task_ends = [t.planned_end for t in tasks if t.planned_end]
                if task_starts and not m.planned_start:
                    m.planned_start = min(task_starts)
                if task_ends and not m.planned_end:
                    m.planned_end = max(task_ends)
        if not m.actual_start or not m.actual_end:
            tasks = _milestone_tasks.get(m.id, [])
            if tasks:
                actual_starts = [t.actual_start for t in tasks if t.actual_start]
                actual_ends = [t.actual_end for t in tasks if t.actual_end]
                if actual_starts and not m.actual_start:
                    m.actual_start = min(actual_starts)
                if actual_ends and not m.actual_end:
                    m.actual_end = max(actual_ends)
        # Recompute is_delayed from inferred/explicit dates
        if m.planned_end and m.actual_end:
            m.is_delayed = m.actual_end > m.planned_end
            m.slippage_days = (m.actual_end - m.planned_end).days
        elif not m.actual_end:
            # Check if any task is delayed
            tasks = _milestone_tasks.get(m.id, [])
            m.is_delayed = any(t.is_delayed for t in tasks)
    
    return ms  # Keep original creation order (SDLC sequence)


async def add_milestone(
    project_id: str,
    request: MilestoneCreateRequest,
    sp: SharePointClient,
) -> ExecutionMilestone:
    """Add a milestone to a project's execution track."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")

    milestone = ExecutionMilestone(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=request.name,
        vendor=request.vendor or "",
        planned_start=request.planned_start,
        planned_end=request.planned_end,
        remarks=request.remarks,
    )
    if project_id not in _milestones:
        _milestones[project_id] = []
    _milestones[project_id].append(milestone)
    await _persist_milestones(sp)
    await _log_audit("created", "Milestone", milestone.id, "", f"Added milestone '{milestone.name}' to Project {project_id}", sp)
    return milestone


async def update_milestone(
    project_id: str,
    milestone_id: str,
    request: MilestoneUpdateRequest,
    sp: SharePointClient,
) -> ExecutionMilestone:
    """Update a milestone (actuals, name, dates). Auto-detects delay and requires 3W1H."""
    await ensure_loaded(sp)
    ms_list = _milestones.get(project_id, [])
    milestone = next((m for m in ms_list if m.id == milestone_id), None)
    if not milestone:
        raise EntityNotFoundError(f"Milestone {milestone_id} not found")

    if request.name is not None:
        milestone.name = request.name
    if request.vendor is not None:
        milestone.vendor = request.vendor
    if request.planned_start is not None:
        milestone.planned_start = request.planned_start
    if request.planned_end is not None:
        milestone.planned_end = request.planned_end
    if request.actual_start is not None:
        milestone.actual_start = request.actual_start
    if request.actual_end is not None:
        milestone.actual_end = request.actual_end
    if request.remarks is not None:
        milestone.remarks = request.remarks

    # Recompute slippage
    update_milestone_computed_fields(milestone)

    # Auto-detect RAG from delay (actual_end > planned_end)
    if milestone.is_delayed and milestone.actual_end and milestone.planned_end:
        # Delay detected — require 3W1H
        missing = []
        if not request.delay_what:
            missing.append("delay_what")
        if not request.delay_why:
            missing.append("delay_why")
        if not request.delay_who:
            missing.append("delay_who")
        if not request.delay_owner_team:
            missing.append("delay_owner_team")
        if not request.delay_how:
            missing.append("delay_how")
        if not request.delay_eta:
            missing.append("delay_eta")
        if missing and len(milestone.rag_context) == 0:
            raise ValueError(
                f"Milestone is delayed by {milestone.slippage_days} days. "
                f"3W1H context is mandatory: {', '.join(missing)}"
            )
        milestone.rag_status = RAGStatus.RED
        if request.delay_what:
            new_entry = RAGContext(
                id=str(uuid.uuid4()),
                what=request.delay_what,
                why=request.delay_why,
                who=request.delay_who,
                owner_team=request.delay_owner_team,
                how=request.delay_how,
                eta=request.delay_eta,
                created_at=datetime.now(timezone.utc).isoformat(),
                status="Open",
            )
            milestone.rag_context.append(new_entry)
            if milestone.id not in _rag_context_entries:
                _rag_context_entries[milestone.id] = []
            _rag_context_entries[milestone.id].append(new_entry)
    elif not milestone.is_delayed and milestone.actual_end:
        milestone.rag_status = RAGStatus.GREEN

    # Propagate: Milestone → Project (worst-case)
    _propagate_rag_from_milestones(project_id)

    await _persist_milestones(sp)
    await _persist_projects(sp)
    await _persist_rag_context_entries(sp)
    # Log milestone 3W1H context if added
    if milestone.is_delayed and request.delay_what:
        await _log_project_change(project_id, f"milestone.{milestone.name}.3W1H", "", f"What: {request.delay_what}, Why: {request.delay_why}, Who: {request.delay_who}, ETA: {request.delay_eta}", "", "Milestone delay 3W1H added", sp)
    await _log_audit("updated", "Milestone", milestone_id, "", f"Updated milestone '{milestone.name}' in Project {project_id}", sp)
    return milestone


async def delete_milestone(
    project_id: str,
    milestone_id: str,
    sp: SharePointClient,
) -> None:
    """Remove a milestone from a project."""
    await ensure_loaded(sp)
    ms_list = _milestones.get(project_id, [])
    _milestones[project_id] = [m for m in ms_list if m.id != milestone_id]
    # Also remove tasks associated with this milestone
    _milestone_tasks.pop(milestone_id, None)
    await _persist_milestones(sp)
    await _persist_milestone_tasks(sp)
    await _log_audit("deleted", "Milestone", milestone_id, "", f"Deleted milestone from Project {project_id}", sp)


# =============================================================================
# MILESTONE TASKS (Sub-tasks under milestones)
# =============================================================================


async def get_milestone_tasks(
    project_id: str,
    milestone_id: str,
    sp: SharePointClient,
) -> List[MilestoneTask]:
    """Get all tasks under a milestone."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    # Verify milestone belongs to project
    ms_list = _milestones.get(project_id, [])
    if not any(m.id == milestone_id for m in ms_list):
        raise EntityNotFoundError(f"Milestone {milestone_id} not found in Project {project_id}")
    return _milestone_tasks.get(milestone_id, [])


async def add_milestone_task(
    project_id: str,
    milestone_id: str,
    request: MilestoneTaskCreateRequest,
    sp: SharePointClient,
) -> MilestoneTask:
    """Add a task under a milestone."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    ms_list = _milestones.get(project_id, [])
    if not any(m.id == milestone_id for m in ms_list):
        raise EntityNotFoundError(f"Milestone {milestone_id} not found in Project {project_id}")

    task = MilestoneTask(
        id=str(uuid.uuid4()),
        milestone_id=milestone_id,
        name=request.name,
        owner=request.owner,
        planned_start=request.planned_start,
        planned_end=request.planned_end,
        remarks=request.remarks,
    )
    if milestone_id not in _milestone_tasks:
        _milestone_tasks[milestone_id] = []
    _milestone_tasks[milestone_id].append(task)
    await _persist_milestone_tasks(sp)
    await _log_audit("created", "MilestoneTask", task.id, "", f"Added task '{task.name}' to Milestone {milestone_id}", sp)
    return task


async def update_milestone_task(
    project_id: str,
    milestone_id: str,
    task_id: str,
    request: MilestoneTaskUpdateRequest,
    sp: SharePointClient,
) -> MilestoneTask:
    """Update a milestone task. Auto-detects delay and requires 3W1H if actual_end > planned_end."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    tasks = _milestone_tasks.get(milestone_id, [])
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        raise EntityNotFoundError(f"Task {task_id} not found")

    if request.name is not None:
        task.name = request.name
    if request.owner is not None:
        task.owner = request.owner
    if request.planned_start is not None:
        task.planned_start = request.planned_start
    if request.planned_end is not None:
        task.planned_end = request.planned_end
    if request.actual_start is not None:
        task.actual_start = request.actual_start
    if request.actual_end is not None:
        task.actual_end = request.actual_end
    if request.remarks is not None:
        task.remarks = request.remarks

    # Compute slippage
    if task.actual_end and task.planned_end:
        task.slippage_days = (task.actual_end - task.planned_end).days
        task.is_delayed = task.slippage_days > 0
    else:
        task.slippage_days = None
        task.is_delayed = False

    # Auto-detect RAG from delay
    if task.is_delayed:
        # Delay detected — require 3W1H only if no existing entries
        if len(task.rag_context) == 0:
            missing = []
            if not request.delay_what:
                missing.append("delay_what")
            if not request.delay_why:
                missing.append("delay_why")
            if not request.delay_who:
                missing.append("delay_who")
            if not request.delay_owner_team:
                missing.append("delay_owner_team")
            if not request.delay_how:
                missing.append("delay_how")
            if not request.delay_eta:
                missing.append("delay_eta")
            if missing:
                raise ValueError(
                    f"Task is delayed by {task.slippage_days} days. "
                    f"3W1H context is mandatory: {', '.join(missing)}"
                )
        # Set RAG to Red
        task.rag_status = RAGStatus.RED
        # Only add new entry if all 3W1H fields are provided (explicit add)
        if request.delay_what and request.delay_why and request.delay_who and request.delay_owner_team and request.delay_how and request.delay_eta:
            new_entry = RAGContext(
                id=str(uuid.uuid4()),
                what=request.delay_what,
                why=request.delay_why,
                who=request.delay_who,
                owner_team=request.delay_owner_team,
                how=request.delay_how,
                eta=request.delay_eta,
                created_at=datetime.now(timezone.utc).isoformat(),
                status="Open",
            )
            task.rag_context.append(new_entry)
            # Update in-memory store
            if task.id not in _rag_context_entries:
                _rag_context_entries[task.id] = []
            _rag_context_entries[task.id].append(new_entry)
    elif not task.is_delayed and task.actual_end:
        # Completed on time — auto-Green
        task.rag_status = RAGStatus.GREEN

    # Propagate RAG: Task → Milestone → Project
    _propagate_rag_from_tasks(milestone_id, project_id)

    # Infer milestone dates from tasks (min planned_start, max planned_end, min actual_start, max actual_end)
    _infer_milestone_dates_from_tasks(milestone_id, project_id)

    await _persist_milestone_tasks(sp)
    await _persist_milestones(sp)
    await _persist_projects(sp)
    await _persist_rag_context_entries(sp)
    # Log key task changes to project changelog
    if request.actual_start is not None or request.actual_end is not None:
        change_desc = []
        if request.actual_start is not None:
            change_desc.append(f"actual_start={request.actual_start}")
        if request.actual_end is not None:
            change_desc.append(f"actual_end={request.actual_end}")
        await _log_project_change(project_id, f"task.{task.name}.actuals", "", ", ".join(change_desc), "", "Task actuals updated", sp)
    if task.is_delayed and request.delay_what:
        await _log_project_change(project_id, f"task.{task.name}.3W1H", "", f"What: {request.delay_what}, Why: {request.delay_why}, ETA: {request.delay_eta}", "", "Delay 3W1H added", sp)
    await _log_audit("updated", "MilestoneTask", task_id, "", f"Updated task '{task.name}' in Milestone {milestone_id}", sp)
    return task


async def delete_milestone_task(
    project_id: str,
    milestone_id: str,
    task_id: str,
    sp: SharePointClient,
) -> None:
    """Remove a task from a milestone."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    tasks = _milestone_tasks.get(milestone_id, [])
    _milestone_tasks[milestone_id] = [t for t in tasks if t.id != task_id]
    await _persist_milestone_tasks(sp)
    await _log_audit("deleted", "MilestoneTask", task_id, "", f"Deleted task from Milestone {milestone_id}", sp)


# =============================================================================
# RAG STATUS
# =============================================================================


async def update_rag(
    entity_type: str,
    entity_id: str,
    status: RAGStatus,
    context: Optional[RAGContext],
    user_name: str,
    sp: SharePointClient,
) -> Dict[str, Any]:
    """Update RAG status for an entity with validation and propagation."""
    await ensure_loaded(sp)

    # Get current status
    entity = _get_entity(entity_type, entity_id)
    if entity is None:
        raise EntityNotFoundError(f"{entity_type} {entity_id} not found")

    previous_status = entity.rag_status

    # Validate context for Yellow/Red
    if status in (RAGStatus.YELLOW, RAGStatus.RED):
        missing = validate_rag_context(status, context)
        if missing:
            raise ValueError(f"Missing 3W1H fields for {status.value}: {', '.join(missing)}")

    # Apply RAG change
    entity.rag_status = status
    if status == RAGStatus.GREEN:
        entity.rag_context = None
    else:
        entity.rag_context = context
    entity.updated_at = datetime.now(timezone.utc)

    # Log history
    history_entry = create_rag_history_entry(
        entity_type, entity_id, previous_status, status, context, user_name
    )
    _rag_history.append(history_entry)

    # Propagate upward
    if entity_type == "Project":
        _propagate_for_project(entity_id)
    elif entity_type == "CP":
        _propagate_for_cp(entity_id)

    # Persist atomically: the affected entity sheet(s) and the RAG history
    # commit together, so a RAG change can't leave the status updated without
    # its history entry (or vice versa).
    if entity_type == "MP":
        _rag_sheets = [SHEET_MPS]
    elif entity_type == "CP":
        _rag_sheets = [SHEET_CPS, SHEET_MPS]
    else:
        _rag_sheets = [SHEET_PROJECTS, SHEET_CPS, SHEET_MPS]
    _rag_sheets.append(SHEET_RAG_HISTORY)
    await _persist_sheets(sp, _rag_sheets)

    await _log_audit("rag_changed", entity_type, entity_id, user_name, f"RAG changed from {previous_status.value} to {status.value}", sp)

    # Log to project changelog if entity is a Project
    if entity_type == "Project":
        await _log_project_change(entity_id, "rag_status", previous_status.value, status.value, user_name, "RAG status changed", sp)

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "previous_status": previous_status.value,
        "new_status": status.value,
        "rag_context": context.model_dump() if context else None,
    }


async def update_rag_context_only(
    entity_type: str,
    entity_id: str,
    context: RAGContext,
    sp: SharePointClient,
) -> Dict[str, Any]:
    """Update RAG context without changing the status."""
    await ensure_loaded(sp)
    entity = _get_entity(entity_type, entity_id)
    if entity is None:
        raise EntityNotFoundError(f"{entity_type} {entity_id} not found")
    entity.rag_context = context
    entity.updated_at = datetime.now(timezone.utc)

    if entity_type == "MP":
        await _persist_mps(sp)
    elif entity_type == "CP":
        await _persist_cps(sp)
    else:
        await _persist_projects(sp)

    return {"entity_type": entity_type, "entity_id": entity_id, "context": context.model_dump()}


async def get_rag_history(
    entity_type: str,
    entity_id: str,
    sp: SharePointClient,
) -> List[RAGHistoryEntry]:
    """Get RAG change history for an entity."""
    await ensure_loaded(sp)
    return [
        h for h in _rag_history
        if h.entity_type == entity_type and h.entity_id == entity_id
    ]


# =============================================================================
# DEPENDENCIES
# =============================================================================


async def get_dependencies(
    project_id: str,
    sp: SharePointClient,
) -> List[Dependency]:
    """Get all dependencies for a project."""
    await ensure_loaded(sp)
    return _dependencies.get(project_id, [])


async def add_dependency(
    project_id: str,
    request: DependencyCreateRequest,
    sp: SharePointClient,
) -> Dependency:
    """Add a dependency to a project."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    dep = _create_dep(project_id, request)
    if project_id not in _dependencies:
        _dependencies[project_id] = []
    _dependencies[project_id].append(dep)
    await _persist_dependencies(sp)
    await _log_project_change(project_id, "dependency.added", "", f"{request.description} (due: {request.cutoff_date})", "", f"New dependency{' [BLOCKER]' if request.is_blocker else ''}", sp)
    await _log_audit("created", "Dependency", dep.id, "", f"Added dependency to Project {project_id}: {request.description}", sp)
    return dep


async def update_dependency(
    project_id: str,
    dep_id: str,
    request: DependencyUpdateRequest,
    sp: SharePointClient,
) -> Dependency:
    """Update a dependency."""
    await ensure_loaded(sp)
    deps = _dependencies.get(project_id, [])
    dep = next((d for d in deps if d.id == dep_id), None)
    if not dep:
        raise EntityNotFoundError(f"Dependency {dep_id} not found")
    dep = _update_dep(dep, request)
    await _persist_dependencies(sp)
    # Log resolution/status changes to changelog
    if request.status is not None:
        await _log_project_change(project_id, f"dependency.{dep.description[:40]}.status", "", request.status.value if hasattr(request.status, 'value') else str(request.status), "", "Dependency updated", sp)
    if dep.resolved_date is not None and request.status and str(request.status.value) == "Resolved":
        await _log_project_change(project_id, f"dependency.{dep.description[:40]}.resolved", "", str(dep.resolved_date), "", "Dependency resolved", sp)
    await _log_audit("updated", "Dependency", dep_id, "", f"Updated dependency in Project {project_id}", sp)
    return dep


async def delete_dependency(
    project_id: str,
    dep_id: str,
    sp: SharePointClient,
) -> None:
    """Remove a dependency."""
    await ensure_loaded(sp)
    deps = _dependencies.get(project_id, [])
    _dependencies[project_id] = [d for d in deps if d.id != dep_id]
    await _persist_dependencies(sp)
    await _log_audit("deleted", "Dependency", dep_id, "", f"Deleted dependency from Project {project_id}", sp)


# =============================================================================
# BUDGET
# =============================================================================


async def get_budget(project_id: str, sp: SharePointClient) -> BudgetData:
    """Get budget data for a project."""
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    return _budgets.get(project_id, create_default_budget(project_id))


async def update_budget(
    project_id: str,
    request: "BudgetUpdateRequest",
    sp: SharePointClient,
) -> BudgetData:
    """Update budget data for a project."""
    from app.models.mpcp_schemas import BudgetUpdateRequest
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")
    budget = _budgets.get(project_id, create_default_budget(project_id))
    from app.services.mpcp_budget_service import update_budget_metadata
    budget = update_budget_metadata(budget, request)
    _budgets[project_id] = budget
    await _persist_budgets(sp)
    await _log_audit("updated", "Budget", project_id, "", f"Updated budget for Project {project_id}", sp)
    return budget


# =============================================================================
# SEARCH
# =============================================================================


async def search_projects(
    sp: SharePointClient,
    filters: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Search/filter projects with full hierarchy path."""
    await ensure_loaded(sp)
    from app.services.mpcp_dashboard_calculator import apply_filters
    projects = list(_projects.values())
    filtered = apply_filters(projects, filters)

    results = []
    for p in filtered:
        cp = _check_points.get(p.parent_cp_id)
        mp = _managing_points.get(cp.parent_mp_id) if cp else None
        results.append({
            "project": p.model_dump(),
            "cp_code": cp.code if cp else None,
            "cp_name": cp.name if cp else None,
            "mp_code": mp.code if mp else None,
            "mp_name": mp.name if mp else None,
            "hierarchy_path": f"{mp.code if mp else '?'} > {cp.code if cp else '?'} > {p.name}",
        })
    return results


# =============================================================================
# DASHBOARD
# =============================================================================


async def get_dashboard(
    sp: SharePointClient,
    bu_filter: Optional[BusinessUnit] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> "DashboardMetrics":
    """Get dashboard metrics."""
    from app.models.mpcp_schemas import DashboardMetrics
    from app.services.mpcp_dashboard_calculator import compute_dashboard_metrics
    await ensure_loaded(sp)

    all_projects = list(_projects.values())
    all_deps = []
    for deps in _dependencies.values():
        all_deps.extend(deps)
    all_budgets = list(_budgets.values())

    return compute_dashboard_metrics(
        projects=all_projects,
        dependencies=all_deps,
        budgets=all_budgets,
        bu_filter=bu_filter,
        filters=filters,
    )


# =============================================================================
# INTERNAL HELPERS
# =============================================================================


def _initialize_process_track(project_id: str) -> List[ProcessTrackStage]:
    """Create 8 stages in order, all Not_Started."""
    stages = []
    for i, stage_name in enumerate(PROCESS_STAGES_ORDERED):
        stages.append(ProcessTrackStage(
            project_id=project_id,
            stage=ProcessStage(stage_name),
            stage_order=i,
            status=StageStatus.NOT_STARTED,
        ))
    return stages


def _reconcile_process_track(
    project_id: str, existing: List[ProcessTrackStage]
) -> List[ProcessTrackStage]:
    """Return the canonical, fully-ordered 8-stage track for a project.

    Guarantees exactly one entry per stage in ``PROCESS_STAGES_ORDERED`` order.
    Any stage already present (keyed by its ``stage`` value) is preserved as-is;
    missing stages are created as Not_Started. This heals projects whose stored
    process track is incomplete or mis-ordered — the previous code indexed into
    the stage list positionally and raised IndexError (surfacing as HTTP 500)
    when a project had fewer than 8 stages.
    """
    by_stage = {}
    for s in existing or []:
        # Keep the first occurrence of each stage; ignore duplicates.
        if s.stage.value not in by_stage:
            by_stage[s.stage.value] = s

    reconciled: List[ProcessTrackStage] = []
    for i, stage_name in enumerate(PROCESS_STAGES_ORDERED):
        s = by_stage.get(stage_name)
        if s is None:
            s = ProcessTrackStage(
                project_id=project_id,
                stage=ProcessStage(stage_name),
                stage_order=i,
                status=StageStatus.NOT_STARTED,
            )
        else:
            # Normalise the order so positional access stays consistent.
            s.stage_order = i
        reconciled.append(s)
    return reconciled


def _compute_current_stage(stages: List[ProcessTrackStage]) -> Optional[ProcessStage]:
    """First In_Progress stage, or first Not_Started if none In_Progress."""
    for s in stages:
        if s.status == StageStatus.IN_PROGRESS:
            return s.stage
    for s in stages:
        if s.status == StageStatus.NOT_STARTED:
            return s.stage
    return stages[-1].stage if stages else None


def _get_entity(entity_type: str, entity_id: str):
    """Get entity by type and ID from in-memory stores."""
    if entity_type == "MP":
        return _managing_points.get(entity_id)
    elif entity_type == "CP":
        return _check_points.get(entity_id)
    elif entity_type == "Project":
        return _projects.get(entity_id)
    return None


def _recompute_counts() -> None:
    """Recompute cp_count and project_count on MPs and CPs."""
    for mp in _managing_points.values():
        cps = [c for c in _check_points.values() if c.parent_mp_id == mp.id]
        mp.cp_count = len(cps)
        mp.project_count = sum(
            1 for p in _projects.values()
            if p.parent_cp_id in {c.id for c in cps}
        )
    for cp in _check_points.values():
        cp.project_count = sum(
            1 for p in _projects.values() if p.parent_cp_id == cp.id
        )


def _recompute_all_propagation() -> None:
    """Recompute propagated RAG for all CPs and MPs."""
    for cp in _check_points.values():
        child_projects = [p for p in _projects.values() if p.parent_cp_id == cp.id]
        if child_projects:
            cp.propagated_rag = compute_propagated_rag(
                [p.rag_status for p in child_projects]
            )
        else:
            cp.propagated_rag = None

    for mp in _managing_points.values():
        child_cps = [c for c in _check_points.values() if c.parent_mp_id == mp.id]
        if child_cps:
            effective = [c.propagated_rag or c.rag_status for c in child_cps]
            mp.propagated_rag = compute_propagated_rag(effective)
        else:
            mp.propagated_rag = None


def _propagate_for_project(project_id: str) -> None:
    """Propagate RAG upward from a project change."""
    project = _projects.get(project_id)
    if not project:
        return
    cp_id = project.parent_cp_id
    _propagate_for_cp(cp_id)


def _propagate_for_cp(cp_id: str) -> None:
    """Recompute CP propagated RAG and propagate to parent MP."""
    cp = _check_points.get(cp_id)
    if not cp:
        return
    child_projects = [p for p in _projects.values() if p.parent_cp_id == cp_id]
    if child_projects:
        cp.propagated_rag = compute_propagated_rag([p.rag_status for p in child_projects])
    else:
        cp.propagated_rag = None
    _propagate_for_mp(cp.parent_mp_id)


def _propagate_for_mp(mp_id: str) -> None:
    """Recompute MP propagated RAG from child CPs."""
    mp = _managing_points.get(mp_id)
    if not mp:
        return
    child_cps = [c for c in _check_points.values() if c.parent_mp_id == mp_id]
    if child_cps:
        effective = [c.propagated_rag or c.rag_status for c in child_cps]
        mp.propagated_rag = compute_propagated_rag(effective)
    else:
        mp.propagated_rag = None


def _propagate_rag_from_tasks(milestone_id: str, project_id: str) -> None:
    """Propagate worst-case RAG from tasks → milestone → project → CP → MP."""
    # Task → Milestone
    tasks = _milestone_tasks.get(milestone_id, [])
    ms_list = _milestones.get(project_id, [])
    milestone = next((m for m in ms_list if m.id == milestone_id), None)
    if milestone:
        if tasks:
            task_rags = [t.rag_status for t in tasks]
            worst = compute_propagated_rag(task_rags)
            # Only override milestone RAG if tasks show worse status
            if worst and RAGSeverity[worst.name] > RAGSeverity[milestone.rag_status.name]:
                milestone.rag_status = worst
        # Then propagate milestone → project
        _propagate_rag_from_milestones(project_id)


def _propagate_rag_from_milestones(project_id: str) -> None:
    """Propagate worst-case RAG from milestones → project → CP → MP."""
    ms_list = _milestones.get(project_id, [])
    project = _projects.get(project_id)
    if not project:
        return
    if ms_list:
        milestone_rags = [m.rag_status for m in ms_list]
        worst = compute_propagated_rag(milestone_rags)
        if worst and RAGSeverity[worst.name] > RAGSeverity[project.rag_status.name]:
            project.rag_status = worst
    # Continue propagation upward
    _propagate_for_project(project_id)


def _infer_milestone_dates_from_tasks(milestone_id: str, project_id: str) -> None:
    """Infer milestone planned/actual dates from its tasks (min start, max end)."""
    tasks = _milestone_tasks.get(milestone_id, [])
    if not tasks:
        return
    ms_list = _milestones.get(project_id, [])
    milestone = next((m for m in ms_list if m.id == milestone_id), None)
    if not milestone:
        return

    # Infer planned dates from tasks
    planned_starts = [t.planned_start for t in tasks if t.planned_start]
    planned_ends = [t.planned_end for t in tasks if t.planned_end]
    if planned_starts:
        milestone.planned_start = min(planned_starts)
    if planned_ends:
        milestone.planned_end = max(planned_ends)

    # Infer actual dates from tasks
    actual_starts = [t.actual_start for t in tasks if t.actual_start]
    actual_ends = [t.actual_end for t in tasks if t.actual_end]
    if actual_starts:
        milestone.actual_start = min(actual_starts)
    if actual_ends:
        milestone.actual_end = max(actual_ends)

    # Recompute slippage on milestone
    update_milestone_computed_fields(milestone)


# =============================================================================
# PERSISTENCE HELPERS (SharePoint read/write)
# =============================================================================


def _assert_persist_safe() -> None:
    """Guard against overwriting SharePoint sheets from an unverified state.

    Every ``_persist_*`` helper does a FULL-SHEET overwrite from the in-memory
    store. If the last load did not fully succeed (``_load_ok`` is False), the
    in-memory store may be empty or partial, and overwriting would wipe the
    real data in MPCPTracker.xlsx. In that case we refuse to persist and raise,
    so the mutation fails loudly instead of silently destroying data.
    """
    if not _load_ok:
        raise SharePointError(
            "Refusing to persist MPCP data: the tracker was not loaded "
            "successfully (SharePoint read failed). Retry once storage is "
            "reachable so the full dataset is in memory before any write."
        )


def _rows_for_sheet(sheet: str) -> List[List[Any]]:
    """Build the full ``[header, *data]`` row set for a tracker sheet from the
    current in-memory state.

    This is the single source of truth for sheet serialization: both the
    single-sheet ``_persist_*`` helpers and the atomic ``_persist_sheets``
    multi-sheet writer build their rows here, so the two paths can never
    diverge in format.
    """
    if sheet == SHEET_MPS:
        headers = [
            "Id", "Code", "Name", "Theme", "Owner", "LoB", "BU",
            "UOM", "TargetFrom", "TargetTo",
            "RAGStatus", "RAGContext", "PropagatedRAG",
            "CpCount", "ProjectCount", "CreatedAt", "UpdatedAt", "CreatedBy",
        ]
        return [headers] + [_mp_to_row(mp) for mp in _managing_points.values()]

    if sheet == SHEET_CPS:
        headers = [
            "Id", "Code", "Name", "Owner", "Description", "Domain", "Stream",
            "UOM", "TargetFrom", "TargetTo", "TargetQuarter",
            "ParentMpId", "RAGStatus", "RAGContext", "PropagatedRAG",
            "ProjectCount", "CreatedAt", "UpdatedAt", "CreatedBy",
        ]
        return [headers] + [_cp_to_row(cp) for cp in _check_points.values()]

    if sheet == SHEET_PROJECTS:
        headers = [
            "Id", "Name", "ProjectType", "Vendor", "ProductOwner", "LoB", "BU",
            "Domain", "Stream", "Description", "ParentCpId", "RAGStatus",
            "RAGContext", "CurrentStage", "RevisedTargetDate",
            "CreatedAt", "UpdatedAt", "CreatedBy", "EnggPOC",
        ]
        return [headers] + [_project_to_row(p) for p in _projects.values()]

    if sheet == SHEET_PROCESS_TRACKS:
        headers = [
            "ProjectId", "Stage", "StageOrder", "Status",
            "PlannedDate", "ActualDate", "Remarks", "SkipReason",
        ]
        rows = []
        for stages in _process_tracks.values():
            for s in stages:
                rows.append([
                    s.project_id, s.stage.value, s.stage_order, s.status.value,
                    str(s.planned_date) if s.planned_date else "",
                    str(s.actual_date) if s.actual_date else "",
                    s.remarks or "", s.skip_reason or "",
                ])
        return [headers] + rows

    if sheet == SHEET_MILESTONES:
        headers = [
            "Id", "ProjectId", "Name", "Vendor",
            "PlannedStart", "PlannedEnd", "ActualStart", "ActualEnd",
            "SlippageDays", "IsDelayed", "RAGStatus", "Remarks",
        ]
        rows = []
        for ms_list in _milestones.values():
            for m in ms_list:
                rows.append([
                    m.id, m.project_id, m.name, m.vendor or "",
                    str(m.planned_start) if m.planned_start else "",
                    str(m.planned_end) if m.planned_end else "",
                    str(m.actual_start) if m.actual_start else "",
                    str(m.actual_end) if m.actual_end else "",
                    m.slippage_days if m.slippage_days is not None else "",
                    str(m.is_delayed), m.rag_status.value,
                    m.remarks or "",
                ])
        return [headers] + rows

    if sheet == SHEET_MILESTONE_TASKS:
        headers = [
            "Id", "MilestoneId", "Name", "Owner",
            "PlannedStart", "PlannedEnd", "ActualStart", "ActualEnd",
            "SlippageDays", "IsDelayed", "RAGStatus", "Remarks",
        ]
        rows = []
        for tasks in _milestone_tasks.values():
            for t in tasks:
                rows.append([
                    t.id, t.milestone_id, t.name, t.owner or "",
                    str(t.planned_start) if t.planned_start else "",
                    str(t.planned_end) if t.planned_end else "",
                    str(t.actual_start) if t.actual_start else "",
                    str(t.actual_end) if t.actual_end else "",
                    t.slippage_days if t.slippage_days is not None else "",
                    str(t.is_delayed), t.rag_status.value,
                    t.remarks or "",
                ])
        return [headers] + rows

    if sheet == SHEET_RAG_CONTEXT_ENTRIES:
        headers = [
            "Id", "EntityId", "What", "Why", "Who",
            "OwnerTeam", "How", "ETA", "CreatedAt", "Status",
        ]
        rows = []
        for entity_id, entries in _rag_context_entries.items():
            for rc in entries:
                rows.append([
                    rc.id or "", entity_id,
                    rc.what or "", rc.why or "", rc.who or "",
                    rc.owner_team or "", rc.how or "",
                    str(rc.eta) if rc.eta else "",
                    rc.created_at or "", rc.status or "Open",
                ])
        return [headers] + rows

    if sheet == SHEET_DEPENDENCIES:
        headers = [
            "Id", "ProjectId", "MilestoneId", "Description",
            "ExternalOwner", "CutoffDate", "RaisedDate",
            "Status", "ResolvedDate", "EscalationNote", "IsOverdue", "IsBlocker",
        ]
        rows = []
        for deps in _dependencies.values():
            for d in deps:
                rows.append([
                    d.id, d.project_id, d.milestone_id or "", d.description,
                    d.external_owner, str(d.cutoff_date), str(d.raised_date),
                    d.status.value, str(d.resolved_date) if d.resolved_date else "",
                    d.escalation_note or "", str(d.is_overdue), str(d.is_blocker),
                ])
        return [headers] + rows

    if sheet == SHEET_BUDGET:
        import json as _json
        headers = [
            "ProjectId", "ApprovedBudget", "InternalEstimate",
            "Transactions", "TotalCommitted", "TotalSpent",
            "Remaining", "Remarks",
        ]
        rows = []
        for b in _budgets.values():
            txns_json = _json.dumps([t.model_dump(mode="json") for t in b.transactions]) if b.transactions else ""
            rows.append([
                b.project_id, b.approved_budget, b.internal_estimate,
                txns_json, b.total_committed, b.total_spent,
                b.remaining, b.remarks or "",
            ])
        return [headers] + rows

    if sheet == SHEET_RAG_HISTORY:
        headers = [
            "EntityType", "EntityId", "PreviousStatus",
            "NewStatus", "RAGContext", "ChangedBy", "Timestamp",
        ]
        rows = []
        for h in _rag_history:
            ctx_json = json.dumps(h.rag_context.model_dump()) if h.rag_context else ""
            rows.append([
                h.entity_type, h.entity_id, h.previous_status.value,
                h.new_status.value, ctx_json, h.changed_by,
                h.timestamp.isoformat(),
            ])
        return [headers] + rows

    raise ValueError(f"Unknown tracker sheet: {sheet}")


async def _persist_sheets(sp: SharePointClient, sheet_names: List[str]) -> None:
    """Atomically persist several tracker sheets in a single workbook write.

    Builds every requested sheet from the current in-memory state and commits
    them with one ``write_sheets`` call, so a multi-sheet operation (create /
    move / delete / RAG change) is all-or-nothing: either every affected sheet
    is written or none are. This removes the partial-write window that
    sequential per-sheet persists had.

    Guarded by ``_assert_persist_safe`` so a partial/unverified in-memory state
    can never overwrite real data.
    """
    _assert_persist_safe()
    # De-duplicate while preserving order.
    seen = set()
    ordered = [s for s in sheet_names if not (s in seen or seen.add(s))]
    sheets = {name: _rows_for_sheet(name) for name in ordered}
    try:
        await sp.write_sheets(_tracker_file(), sheets)
    except Exception as e:
        logger.error(f"Failed to persist sheets {ordered}: {e}")
        raise


async def _persist_mps(sp: SharePointClient) -> None:
    """Write all MPs to SharePoint."""
    _assert_persist_safe()
    try:
        await sp.write_rows(_tracker_file(), SHEET_MPS, _rows_for_sheet(SHEET_MPS))
    except Exception as e:
        logger.error(f"Failed to persist MPs: {e}")
        raise


async def _persist_cps(sp: SharePointClient) -> None:
    """Write all CPs to SharePoint."""
    _assert_persist_safe()
    try:
        await sp.write_rows(_tracker_file(), SHEET_CPS, _rows_for_sheet(SHEET_CPS))
    except Exception as e:
        logger.error(f"Failed to persist CPs: {e}")
        raise


async def _persist_projects(sp: SharePointClient) -> None:
    """Write all Projects to SharePoint."""
    _assert_persist_safe()
    try:
        await sp.write_rows(_tracker_file(), SHEET_PROJECTS, _rows_for_sheet(SHEET_PROJECTS))
    except Exception as e:
        logger.error(f"Failed to persist Projects: {e}")
        raise


async def _persist_process_tracks(sp: SharePointClient) -> None:
    """Write all process tracks to SharePoint."""
    _assert_persist_safe()
    try:
        await sp.write_rows(_tracker_file(), SHEET_PROCESS_TRACKS, _rows_for_sheet(SHEET_PROCESS_TRACKS))
    except Exception as e:
        logger.error(f"Failed to persist ProcessTracks: {e}")
        raise


async def _persist_milestones(sp: SharePointClient) -> None:
    """Write all milestones to SharePoint. Guarded against unverified loads."""
    _assert_persist_safe()
    try:
        await sp.write_rows(_tracker_file(), SHEET_MILESTONES, _rows_for_sheet(SHEET_MILESTONES))
    except Exception as e:
        logger.error(f"Failed to persist Milestones: {e}")
        raise


async def _persist_milestone_tasks(sp: SharePointClient) -> None:
    """Write all milestone tasks to SharePoint."""
    _assert_persist_safe()
    try:
        await sp.write_rows(_tracker_file(), SHEET_MILESTONE_TASKS, _rows_for_sheet(SHEET_MILESTONE_TASKS))
    except Exception as e:
        logger.error(f"Failed to persist MilestoneTasks: {e}")
        raise


async def _persist_rag_context_entries(sp: SharePointClient) -> None:
    """Write all RAG context entries to SharePoint (separate sheet)."""
    _assert_persist_safe()
    try:
        await sp.write_rows(_tracker_file(), SHEET_RAG_CONTEXT_ENTRIES, _rows_for_sheet(SHEET_RAG_CONTEXT_ENTRIES))
    except Exception as e:
        logger.error(f"Failed to persist RAGContextEntries: {e}")
        raise


async def _persist_dependencies(sp: SharePointClient) -> None:
    """Write all dependencies to SharePoint."""
    _assert_persist_safe()
    try:
        await sp.write_rows(_tracker_file(), SHEET_DEPENDENCIES, _rows_for_sheet(SHEET_DEPENDENCIES))
    except Exception as e:
        logger.error(f"Failed to persist Dependencies: {e}")
        raise


async def _persist_budgets(sp: SharePointClient) -> None:
    """Write all budgets to SharePoint."""
    _assert_persist_safe()
    try:
        await sp.write_rows(_tracker_file(), SHEET_BUDGET, _rows_for_sheet(SHEET_BUDGET))
    except Exception as e:
        logger.error(f"Failed to persist Budgets: {e}")
        raise


async def _persist_rag_history(sp: SharePointClient) -> None:
    """Write RAG history to SharePoint."""
    _assert_persist_safe()
    try:
        await sp.write_rows(_tracker_file(), SHEET_RAG_HISTORY, _rows_for_sheet(SHEET_RAG_HISTORY))
    except Exception as e:
        logger.error(f"Failed to persist RAG History: {e}")
        raise


# =============================================================================
# ROW SERIALIZATION HELPERS
# =============================================================================


def _mp_to_row(mp: ManagingPoint) -> List[Any]:
    ctx = json.dumps(mp.rag_context.model_dump()) if mp.rag_context else ""
    return [
        mp.id, mp.code, mp.name, mp.theme.value, mp.owner,
        mp.lob.value, mp.bu.value,
        mp.uom or "", mp.target_from or "", mp.target_to or "",
        mp.rag_status.value, ctx,
        mp.propagated_rag.value if mp.propagated_rag else "",
        mp.cp_count, mp.project_count,
        mp.created_at.isoformat(), mp.updated_at.isoformat(),
        mp.created_by or "",
    ]


def _cp_to_row(cp: CheckPoint) -> List[Any]:
    ctx = json.dumps(cp.rag_context.model_dump()) if cp.rag_context else ""
    return [
        cp.id, cp.code, cp.name, cp.owner, cp.description or "",
        cp.domain.value if cp.domain else "",
        cp.stream.value if cp.stream else "",
        cp.uom or "", cp.target_from or "", cp.target_to or "",
        cp.target_quarter.value if cp.target_quarter else "",
        cp.parent_mp_id, cp.rag_status.value, ctx,
        cp.propagated_rag.value if cp.propagated_rag else "",
        cp.project_count,
        cp.created_at.isoformat(), cp.updated_at.isoformat(),
        cp.created_by or "",
    ]


def _project_to_row(p: Project) -> List[Any]:
    ctx = json.dumps(p.rag_context.model_dump()) if p.rag_context else ""
    return [
        p.id, p.name,
        p.project_type.value if p.project_type else "",
        p.vendor or "", p.product_owner or "",
        p.lob.value if p.lob else "",
        p.bu.value if p.bu else "",
        p.domain.value if p.domain else "",
        p.stream.value if p.stream else "",
        p.description or "", p.parent_cp_id, p.rag_status.value, ctx,
        p.current_stage.value if p.current_stage else "",
        str(p.revised_target_date) if p.revised_target_date else "",
        p.created_at.isoformat(), p.updated_at.isoformat(),
        p.created_by or "",
        p.engg_poc or "",
    ]


# =============================================================================
# ROW PARSING HELPERS (SharePoint → Models)
# =============================================================================


def _parse_mps(rows: List[List]) -> Dict[str, ManagingPoint]:
    """Parse MP rows from SharePoint. First row = headers.
    
    Header order: Id, Code, Name, Theme, Owner, LoB, BU, UOM, TargetFrom, TargetTo,
                  RAGStatus, RAGContext, PropagatedRAG, CpCount, ProjectCount, CreatedAt, UpdatedAt, CreatedBy
    """
    result = {}
    if not rows or len(rows) < 2:
        return result
    for row in rows[1:]:
        if not row or len(row) < 16:
            continue
        try:
            ctx = None
            if row[11]:
                ctx = RAGContext(**json.loads(row[11]))
            mp = ManagingPoint(
                id=str(row[0]),
                code=str(row[1]),
                name=str(row[2]),
                theme=MPTheme(str(row[3])),
                owner=str(row[4]),
                lob=BusinessUnit(str(row[5])),
                bu=BusinessUnit(str(row[6])),
                uom=str(row[7]) if row[7] else None,
                target_from=str(row[8]) if row[8] else None,
                target_to=str(row[9]) if row[9] else None,
                rag_status=RAGStatus(str(row[10])),
                rag_context=ctx,
                propagated_rag=RAGStatus(str(row[12])) if row[12] else None,
                cp_count=int(row[13]) if len(row) > 13 and row[13] else 0,
                project_count=int(row[14]) if len(row) > 14 and row[14] else 0,
                created_at=datetime.fromisoformat(str(row[15])),
                updated_at=datetime.fromisoformat(str(row[16])),
                created_by=str(row[17]) if len(row) > 17 and row[17] else None,
            )
            result[mp.id] = mp
        except Exception as e:
            logger.warning(f"Failed to parse MP row: {e}")
    return result


def _parse_cps(rows: List[List]) -> Dict[str, CheckPoint]:
    """Parse CP rows from SharePoint.
    
    Header order: Id, Code, Name, Owner, Description, Domain, Stream,
                  UOM, TargetFrom, TargetTo, TargetQuarter, ParentMpId,
                  RAGStatus, RAGContext, PropagatedRAG, ProjectCount, CreatedAt, UpdatedAt, CreatedBy
    """
    result = {}
    if not rows or len(rows) < 2:
        return result
    for row in rows[1:]:
        if not row or len(row) < 17:
            continue
        try:
            ctx = None
            if row[13]:
                ctx = RAGContext(**json.loads(row[13]))
            from app.models.mpcp_schemas import TrackerDomain, TrackerStream, TargetQuarter
            cp = CheckPoint(
                id=str(row[0]),
                code=str(row[1]),
                name=str(row[2]),
                owner=str(row[3]),
                description=str(row[4]) if row[4] else None,
                domain=TrackerDomain(str(row[5])) if row[5] else None,
                stream=TrackerStream(str(row[6])) if row[6] else None,
                uom=str(row[7]) if row[7] else None,
                target_from=str(row[8]) if row[8] else None,
                target_to=str(row[9]) if row[9] else None,
                target_quarter=TargetQuarter(str(row[10])) if row[10] else None,
                parent_mp_id=str(row[11]),
                rag_status=RAGStatus(str(row[12])),
                rag_context=ctx,
                propagated_rag=RAGStatus(str(row[14])) if row[14] else None,
                project_count=int(row[15]) if len(row) > 15 and row[15] else 0,
                created_at=datetime.fromisoformat(str(row[16])),
                updated_at=datetime.fromisoformat(str(row[17])),
                created_by=str(row[18]) if len(row) > 18 and row[18] else None,
            )
            result[cp.id] = cp
        except Exception as e:
            logger.warning(f"Failed to parse CP row: {e}")
    return result


def _parse_projects(rows: List[List]) -> Dict[str, Project]:
    """Parse Project rows from SharePoint."""
    result = {}
    if not rows or len(rows) < 2:
        return result
    for row in rows[1:]:
        if not row or len(row) < 16:
            continue
        try:
            ctx = None
            if row[12]:
                ctx = RAGContext(**json.loads(row[12]))
            from app.models.mpcp_schemas import TrackerDomain, TrackerStream
            p = Project(
                id=str(row[0]),
                name=str(row[1]),
                project_type=ProjectType(str(row[2])) if row[2] else None,
                vendor=str(row[3]) if row[3] else None,
                product_owner=str(row[4]) if row[4] else None,
                lob=BusinessUnit(str(row[5])) if row[5] else None,
                bu=BusinessUnit(str(row[6])) if row[6] else None,
                domain=TrackerDomain(str(row[7])) if row[7] else None,
                stream=TrackerStream(str(row[8])) if row[8] else None,
                description=str(row[9]) if row[9] else None,
                parent_cp_id=str(row[10]),
                rag_status=RAGStatus(str(row[11])),
                rag_context=ctx,
                current_stage=ProcessStage(str(row[13])) if row[13] else None,
                revised_target_date=date.fromisoformat(str(row[14])) if row[14] else None,
                created_at=datetime.fromisoformat(str(row[15])),
                updated_at=datetime.fromisoformat(str(row[16])),
                created_by=str(row[17]) if len(row) > 17 and row[17] else None,
                engg_poc=str(row[18]) if len(row) > 18 and row[18] else None,
            )
            result[p.id] = p
        except Exception as e:
            logger.warning(f"Failed to parse Project row: {e}")
    return result


def _parse_process_tracks(rows: List[List]) -> Dict[str, List[ProcessTrackStage]]:
    """Parse process track rows grouped by project_id."""
    result: Dict[str, List[ProcessTrackStage]] = {}
    if not rows or len(rows) < 2:
        return result
    for row in rows[1:]:
        if not row or len(row) < 4:
            continue
        try:
            stage = ProcessTrackStage(
                project_id=str(row[0]),
                stage=ProcessStage(str(row[1])),
                stage_order=int(row[2]),
                status=StageStatus(str(row[3])),
                planned_date=date.fromisoformat(str(row[4])) if row[4] else None,
                actual_date=date.fromisoformat(str(row[5])) if row[5] else None,
                remarks=str(row[6]) if row[6] else None,
                skip_reason=str(row[7]) if row[7] else None,
            )
            if stage.project_id not in result:
                result[stage.project_id] = []
            result[stage.project_id].append(stage)
        except Exception as e:
            logger.warning(f"Failed to parse ProcessTrack row: {e}")
    # Sort stages by order
    for pid in result:
        result[pid].sort(key=lambda s: s.stage_order)
    return result


def _parse_milestones(rows: List[List]) -> Dict[str, List[ExecutionMilestone]]:
    """Parse milestone rows grouped by project_id."""
    result: Dict[str, List[ExecutionMilestone]] = {}
    if not rows or len(rows) < 2:
        return result
    for row in rows[1:]:
        if not row or len(row) < 4:
            continue
        try:
            m = ExecutionMilestone(
                id=str(row[0]),
                project_id=str(row[1]),
                name=str(row[2]),
                vendor=str(row[3]) if len(row) > 3 and row[3] else "",
                planned_start=date.fromisoformat(str(row[4])) if len(row) > 4 and row[4] else None,
                planned_end=date.fromisoformat(str(row[5])) if len(row) > 5 and row[5] else None,
                actual_start=date.fromisoformat(str(row[6])) if len(row) > 6 and row[6] else None,
                actual_end=date.fromisoformat(str(row[7])) if len(row) > 7 and row[7] else None,
                slippage_days=int(row[8]) if len(row) > 8 and row[8] != "" and row[8] is not None else None,
                is_delayed=str(row[9]).lower() == "true" if len(row) > 9 and row[9] else False,
                rag_status=RAGStatus(str(row[10])) if len(row) > 10 and row[10] else RAGStatus.GREEN,
                rag_context=[],  # Loaded separately from RAGContextEntries sheet
                remarks=str(row[11]) if len(row) > 11 and row[11] else None,
            )
            if m.project_id not in result:
                result[m.project_id] = []
            result[m.project_id].append(m)
        except Exception as e:
            logger.warning(f"Failed to parse Milestone row: {e}")
    return result


def _parse_milestone_tasks(rows: List[List]) -> Dict[str, List[MilestoneTask]]:
    """Parse milestone task rows grouped by milestone_id."""
    result: Dict[str, List[MilestoneTask]] = {}
    if not rows or len(rows) < 2:
        return result
    for row in rows[1:]:
        if not row or len(row) < 3:
            continue
        try:
            t = MilestoneTask(
                id=str(row[0]),
                milestone_id=str(row[1]),
                name=str(row[2]),
                owner=str(row[3]) if len(row) > 3 and row[3] else None,
                planned_start=date.fromisoformat(str(row[4])) if len(row) > 4 and row[4] else None,
                planned_end=date.fromisoformat(str(row[5])) if len(row) > 5 and row[5] else None,
                actual_start=date.fromisoformat(str(row[6])) if len(row) > 6 and row[6] else None,
                actual_end=date.fromisoformat(str(row[7])) if len(row) > 7 and row[7] else None,
                slippage_days=int(row[8]) if len(row) > 8 and row[8] != "" and row[8] is not None else None,
                is_delayed=str(row[9]).lower() == "true" if len(row) > 9 and row[9] else False,
                rag_status=RAGStatus(str(row[10])) if len(row) > 10 and row[10] else RAGStatus.GREEN,
                rag_context=[],  # Loaded separately from RAGContextEntries sheet
                remarks=str(row[11]) if len(row) > 11 and row[11] else None,
            )
            if t.milestone_id not in result:
                result[t.milestone_id] = []
            result[t.milestone_id].append(t)
        except Exception as e:
            logger.warning(f"Failed to parse MilestoneTask row: {e}")
    return result


def _parse_rag_context_entries(rows: List[List]) -> Dict[str, List[RAGContext]]:
    """Parse RAG context entries grouped by entity_id."""
    result: Dict[str, List[RAGContext]] = {}
    if not rows or len(rows) < 2:
        return result
    for row in rows[1:]:
        if not row or len(row) < 3:
            continue
        try:
            entry = RAGContext(
                id=str(row[0]) if row[0] else None,
                what=str(row[2]) if len(row) > 2 and row[2] else None,
                why=str(row[3]) if len(row) > 3 and row[3] else None,
                who=str(row[4]) if len(row) > 4 and row[4] else None,
                owner_team=str(row[5]) if len(row) > 5 and row[5] else None,
                how=str(row[6]) if len(row) > 6 and row[6] else None,
                eta=date.fromisoformat(str(row[7])) if len(row) > 7 and row[7] else None,
                created_at=str(row[8]) if len(row) > 8 and row[8] else None,
                status=str(row[9]) if len(row) > 9 and row[9] else "Open",
            )
            entity_id = str(row[1])
            if entity_id not in result:
                result[entity_id] = []
            result[entity_id].append(entry)
        except Exception as e:
            logger.warning(f"Failed to parse RAGContextEntry row: {e}")
    return result


def _parse_dependencies(rows: List[List]) -> Dict[str, List[Dependency]]:
    """Parse dependency rows grouped by project_id."""
    result: Dict[str, List[Dependency]] = {}
    if not rows or len(rows) < 2:
        return result
    for row in rows[1:]:
        if not row or len(row) < 7:
            continue
        try:
            d = Dependency(
                id=str(row[0]),
                project_id=str(row[1]),
                milestone_id=str(row[2]) if row[2] else None,
                description=str(row[3]),
                external_owner=str(row[4]),
                cutoff_date=date.fromisoformat(str(row[5])),
                raised_date=date.fromisoformat(str(row[6])),
                status=DependencyStatus(str(row[7])),
                resolved_date=date.fromisoformat(str(row[8])) if row[8] else None,
                escalation_note=str(row[9]) if len(row) > 9 and row[9] else None,
                is_overdue=str(row[10]).lower() == "true" if len(row) > 10 and row[10] else False,
                is_blocker=str(row[11]).lower() == "true" if len(row) > 11 and row[11] else False,
            )
            if d.project_id not in result:
                result[d.project_id] = []
            result[d.project_id].append(d)
        except Exception as e:
            logger.warning(f"Failed to parse Dependency row: {e}")
    return result


def _parse_budgets(rows: List[List]) -> Dict[str, BudgetData]:
    """Parse budget rows keyed by project_id."""
    result: Dict[str, BudgetData] = {}
    if not rows or len(rows) < 2:
        return result
    for row in rows[1:]:
        if not row or len(row) < 7:
            continue
        try:
            from app.models.mpcp_schemas import BudgetTransaction
            transactions = []
            if len(row) > 3 and row[3]:
                try:
                    txns_data = json.loads(row[3])
                    transactions = [BudgetTransaction(**t) for t in txns_data]
                except Exception:
                    transactions = []
            b = BudgetData(
                project_id=str(row[0]),
                approved_budget=float(row[1]) if row[1] else 0.0,
                internal_estimate=float(row[2]) if row[2] else 0.0,
                transactions=transactions,
                total_committed=float(row[4]) if len(row) > 4 and row[4] else 0.0,
                total_spent=float(row[5]) if len(row) > 5 and row[5] else 0.0,
                remaining=float(row[6]) if len(row) > 6 and row[6] else 0.0,
                remarks=str(row[7]) if len(row) > 7 and row[7] else None,
            )
            result[b.project_id] = b
        except Exception as e:
            logger.warning(f"Failed to parse Budget row: {e}")
    return result


def _parse_rag_history(rows: List[List]) -> List[RAGHistoryEntry]:
    """Parse RAG history rows."""
    result: List[RAGHistoryEntry] = []
    if not rows or len(rows) < 2:
        return result
    for row in rows[1:]:
        if not row or len(row) < 7:
            continue
        try:
            ctx = None
            if row[4]:
                ctx = RAGContext(**json.loads(row[4]))
            entry = RAGHistoryEntry(
                entity_type=str(row[0]),
                entity_id=str(row[1]),
                previous_status=RAGStatus(str(row[2])),
                new_status=RAGStatus(str(row[3])),
                rag_context=ctx,
                changed_by=str(row[5]),
                timestamp=datetime.fromisoformat(str(row[6])),
            )
            result.append(entry)
        except Exception as e:
            logger.warning(f"Failed to parse RAG History row: {e}")
    return result


# =============================================================================
# BULK UPLOAD (MP + CP + Projects from Excel)
# =============================================================================


def generate_hierarchy_template() -> bytes:
    """Generate an Excel template for bulk hierarchy upload."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    header_font = Font(bold=True, size=11)
    header_fill = PatternFill(start_color="E8EAF6", end_color="E8EAF6", fill_type="solid")

    # MPs sheet
    ws_mp = wb.active
    ws_mp.title = "MPs"
    mp_headers = ["Code", "Name", "Theme", "Owner", "LoB", "BU", "UOM", "From", "To"]
    for col, h in enumerate(mp_headers, 1):
        cell = ws_mp.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
    # Sample rows
    ws_mp.append(["A1", "Increase Service NPS by improving usage of current Digital & AI tools", "A", "Ashok", "IND-2W", "IND-2W", "Service NPS Score", "-", "+0.5"])
    ws_mp.append(["B1", "Increasing retail by improving usage of current Digital & AI tools in sales process", "B", "UBP", "IND-2W", "IND-2W", "# Retail 000s MA", "21", "29"])

    # CPs sheet
    ws_cp = wb.create_sheet("CPs")
    cp_headers = ["Code", "Name", "Owner", "Description", "Domain", "Stream", "ParentMPCode", "UOM", "From", "To"]
    for col, h in enumerate(cp_headers, 1):
        cell = ws_cp.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
    ws_cp.append(["A1.1", "Job Card Voice Of Customer fill rate (AMD + AD)", "Prithviraj, Ankit M", "", "Shop", "D2C", "A1", "JC Fill rate% (exit)", "60", "100"])
    ws_cp.append(["B1.1", "2 hour follow-up of digital leads", "Raman", "", "Buy", "D2C", "B1", "% (exit)", "77", "90"])

    # Projects sheet
    ws_proj = wb.create_sheet("Projects")
    proj_headers = ["Name", "Type", "Vendor", "ProductOwner", "LoB", "BU", "Domain", "Stream", "Description", "ParentCPCode"]
    for col, h in enumerate(proj_headers, 1):
        cell = ws_proj.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
    ws_proj.append(["App Redesign Phase 1", "Fixed_Bid", "Exathought", "Ashish Thakur", "IND-2W", "IND-2W", "Shop", "D2C", "Phase 1 of mobile app redesign", "A1.1"])
    ws_proj.append(["Vendor Portal", "Enhancement", "Deloitte", "Akshay Bhosle", "3W/CMB", "3W/CMB", "Buy", "Channel Partner", "", "B1.1"])

    # Instructions sheet
    ws_info = wb.create_sheet("Instructions")
    ws_info.append(["Column", "Valid Values"])
    ws_info.append(["Theme", "A, B, C, D, E, F"])
    ws_info.append(["LoB / BU", "IND-2W, 3W/CMB, IB"])
    ws_info.append(["Type", "Fixed_Bid, Special, Bug, Enhancement"])
    ws_info.append(["Vendor", "Exathought, Deloitte, TVSD, Evontech, Autovyn"])
    ws_info.append(["ProductOwner", "Ashish Thakur, Akshay Bhosle, Prakash Bharati, Avinash Kumar, Bibin, Sumitra Rathod"])
    ws_info.append(["Domain", "Shop, Buy, Own, Parts"])
    ws_info.append(["Stream", "D2C, Channel Partner, Platform Services"])
    ws_info.append([""])
    ws_info.append(["NOTES:"])
    ws_info.append(["- ParentMPCode in CPs sheet must match a Code in MPs sheet"])
    ws_info.append(["- ParentCPCode in Projects sheet must match a Code in CPs sheet"])
    ws_info.append(["- All rows are validated. Upload fails if any row has errors."])

    from io import BytesIO
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


async def bulk_upload_hierarchy(
    file_content: bytes,
    user_name: str,
    sp: SharePointClient,
) -> Dict[str, Any]:
    """Parse Excel and bulk-create MPs, CPs, Projects.

    Returns summary with counts and any errors.
    """
    from openpyxl import load_workbook
    from io import BytesIO

    await ensure_loaded(sp)

    wb = load_workbook(BytesIO(file_content), read_only=True, data_only=True)
    errors = []
    created_mps = 0
    created_cps = 0
    created_projects = 0

    # --- Parse and create MPs ---
    mp_code_to_id: Dict[str, str] = {}
    # Include existing MPs by code
    for mp in _managing_points.values():
        mp_code_to_id[mp.code] = mp.id

    if "MPs" in wb.sheetnames:
        ws = wb["MPs"]
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        for i, row in enumerate(rows, start=2):
            if not row or not row[0]:
                continue
            try:
                code = str(row[0]).strip()
                if code in mp_code_to_id:
                    continue  # Skip existing
                name = str(row[1]).strip() if row[1] else ""
                theme_val = str(row[2]).strip() if row[2] else ""
                owner = str(row[3]).strip() if row[3] else ""
                lob_val = str(row[4]).strip() if row[4] else ""
                bu_val = str(row[5]).strip() if len(row) > 5 and row[5] else lob_val

                if not name:
                    errors.append({"sheet": "MPs", "row": i, "error": "Name is required"})
                    continue

                request = MPCreateRequest(
                    code=code, name=name, theme=MPTheme(theme_val),
                    owner=owner, lob=BusinessUnit(lob_val), bu=BusinessUnit(bu_val),
                    uom=str(row[6]).strip() if len(row) > 6 and row[6] else None,
                    target_from=str(row[7]).strip() if len(row) > 7 and row[7] else None,
                    target_to=str(row[8]).strip() if len(row) > 8 and row[8] else None,
                )
                mp = await create_mp(request, user_name, sp)
                mp_code_to_id[code] = mp.id
                created_mps += 1
            except Exception as e:
                errors.append({"sheet": "MPs", "row": i, "error": str(e)})

    # --- Parse and create CPs ---
    cp_code_to_id: Dict[str, str] = {}
    for cp in _check_points.values():
        cp_code_to_id[cp.code] = cp.id

    if "CPs" in wb.sheetnames:
        ws = wb["CPs"]
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        for i, row in enumerate(rows, start=2):
            if not row or not row[0]:
                continue
            try:
                code = str(row[0]).strip()
                if code in cp_code_to_id:
                    continue  # Skip existing
                name = str(row[1]).strip() if row[1] else ""
                owner = str(row[2]).strip() if row[2] else ""
                desc = str(row[3]).strip() if len(row) > 3 and row[3] else None
                domain_val = str(row[4]).strip() if len(row) > 4 and row[4] else None
                stream_val = str(row[5]).strip() if len(row) > 5 and row[5] else None
                parent_mp_code = str(row[6]).strip() if len(row) > 6 and row[6] else ""

                if not name:
                    errors.append({"sheet": "CPs", "row": i, "error": "Name is required"})
                    continue
                if parent_mp_code not in mp_code_to_id:
                    errors.append({"sheet": "CPs", "row": i, "error": f"ParentMPCode '{parent_mp_code}' not found"})
                    continue

                from app.models.mpcp_schemas import TrackerDomain, TrackerStream
                request = CPCreateRequest(
                    code=code, name=name, owner=owner, description=desc,
                    domain=TrackerDomain(domain_val) if domain_val else None,
                    stream=TrackerStream(stream_val) if stream_val else None,
                    uom=str(row[7]).strip() if len(row) > 7 and row[7] else None,
                    target_from=str(row[8]).strip() if len(row) > 8 and row[8] else None,
                    target_to=str(row[9]).strip() if len(row) > 9 and row[9] else None,
                )
                cp = await create_cp(mp_code_to_id[parent_mp_code], request, user_name, sp)
                cp_code_to_id[code] = cp.id
                created_cps += 1
            except Exception as e:
                errors.append({"sheet": "CPs", "row": i, "error": str(e)})

    # --- Parse and create Projects ---
    if "Projects" in wb.sheetnames:
        ws = wb["Projects"]
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        for i, row in enumerate(rows, start=2):
            if not row or not row[0]:
                continue
            try:
                name = str(row[0]).strip()
                type_val = str(row[1]).strip() if row[1] else ""
                vendor = str(row[2]).strip() if row[2] else ""
                po = str(row[3]).strip() if row[3] else ""
                lob_val = str(row[4]).strip() if row[4] else ""
                bu_val = str(row[5]).strip() if len(row) > 5 and row[5] else lob_val
                domain_val = str(row[6]).strip() if len(row) > 6 and row[6] else None
                stream_val = str(row[7]).strip() if len(row) > 7 and row[7] else None
                desc = str(row[8]).strip() if len(row) > 8 and row[8] else None
                parent_cp_code = str(row[9]).strip() if len(row) > 9 and row[9] else ""

                if not name:
                    errors.append({"sheet": "Projects", "row": i, "error": "Name is required"})
                    continue
                if parent_cp_code not in cp_code_to_id:
                    errors.append({"sheet": "Projects", "row": i, "error": f"ParentCPCode '{parent_cp_code}' not found"})
                    continue

                from app.models.mpcp_schemas import TrackerDomain, TrackerStream
                request = ProjectCreateRequest(
                    name=name, project_type=ProjectType(type_val),
                    vendor=vendor, product_owner=po,
                    lob=BusinessUnit(lob_val), bu=BusinessUnit(bu_val),
                    domain=TrackerDomain(domain_val) if domain_val else None,
                    stream=TrackerStream(stream_val) if stream_val else None,
                    description=desc,
                )
                await create_project(cp_code_to_id[parent_cp_code], request, user_name, sp)
                created_projects += 1
            except Exception as e:
                errors.append({"sheet": "Projects", "row": i, "error": str(e)})

    wb.close()

    return {
        "success": len(errors) == 0,
        "created_mps": created_mps,
        "created_cps": created_cps,
        "created_projects": created_projects,
        "errors": errors,
    }


async def bulk_upload_milestones(
    project_id: str,
    file_content: bytes,
    sp: SharePointClient,
) -> Dict[str, Any]:
    """Bulk upload milestones from Excel/CSV for a project.

    Expected columns: Milestone Name, Vendor, Planned Start Date, Planned End Date
    """
    await ensure_loaded(sp)
    if project_id not in _projects:
        raise EntityNotFoundError(f"Project {project_id} not found")

    from openpyxl import load_workbook
    from io import BytesIO

    wb = load_workbook(BytesIO(file_content), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))

    errors = []
    added = 0

    for i, row in enumerate(rows, start=2):
        if not row or not row[0]:
            continue
        try:
            name = str(row[0]).strip()
            vendor = str(row[1]).strip() if row[1] else ""
            planned_start_raw = row[2]
            planned_end_raw = row[3]

            if not name:
                errors.append({"row": i, "error": "Milestone Name is required"})
                continue
            if vendor not in VALID_VENDORS:
                errors.append({"row": i, "error": f"Invalid vendor '{vendor}'"})
                continue

            # Parse dates
            if isinstance(planned_start_raw, datetime):
                ps = planned_start_raw.date()
            elif isinstance(planned_start_raw, date):
                ps = planned_start_raw
            else:
                ps = date.fromisoformat(str(planned_start_raw).strip())

            if isinstance(planned_end_raw, datetime):
                pe = planned_end_raw.date()
            elif isinstance(planned_end_raw, date):
                pe = planned_end_raw
            else:
                pe = date.fromisoformat(str(planned_end_raw).strip())

            if pe < ps:
                errors.append({"row": i, "error": "Planned End must be >= Planned Start"})
                continue

            request = MilestoneCreateRequest(
                name=name, vendor=vendor, planned_start=ps, planned_end=pe,
            )
            await add_milestone(project_id, request, sp)
            added += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    wb.close()

    if errors and added == 0:
        raise ValueError(f"All rows failed validation: {errors}")

    return {
        "success": len(errors) == 0,
        "milestones_added": added,
        "errors": errors,
    }


# =============================================================================
# MPCP CONFIG (configurable lists for Vendors, POs, EMs)
# =============================================================================

_mpcp_config: Dict[str, List[str]] = {
    "vendors": list(VALID_VENDORS),
    "product_owners": list(VALID_PRODUCT_OWNERS),
    "engineering_managers": [],
}
_config_loaded: bool = False
# Whether the Config sheet was last read successfully (independent of the
# hierarchy's _load_ok). Guards _persist_config against overwriting the real
# Config sheet with in-memory defaults after a failed read.
_config_load_ok: bool = False


async def get_mpcp_config(sp: SharePointClient) -> Dict[str, List[str]]:
    """Get the MPCP config (vendors, POs, EMs)."""
    global _config_loaded
    if not _config_loaded:
        await _load_config(sp)
        _config_loaded = True
    return _mpcp_config


async def update_mpcp_config(
    config: Dict[str, List[str]],
    sp: SharePointClient,
) -> Dict[str, List[str]]:
    """Update MPCP config and persist."""
    global _mpcp_config, _config_loaded
    # Ensure the current config is loaded from SharePoint before mutating, so a
    # partial/default in-memory state can't overwrite the real Config sheet, and
    # so the persist guard (_config_loaded) is satisfied.
    if not _config_loaded:
        await _load_config(sp)
        _config_loaded = True
    if "vendors" in config:
        _mpcp_config["vendors"] = config["vendors"]
    if "product_owners" in config:
        _mpcp_config["product_owners"] = config["product_owners"]
    if "engineering_managers" in config:
        _mpcp_config["engineering_managers"] = config["engineering_managers"]
    await _persist_config(sp)
    return _mpcp_config


async def _load_config(sp: SharePointClient) -> None:
    """Load config from SharePoint Config sheet.

    Sets ``_config_load_ok`` True only when the Config sheet was read without a
    transport failure (a missing sheet is a valid "first run" and still counts
    as a successful load that may be persisted). On a genuine SharePoint read
    failure we leave it False so ``_persist_config`` refuses to overwrite the
    real Config sheet with in-memory defaults.
    """
    global _mpcp_config, _config_load_ok
    _config_load_ok = False
    try:
        rows = await sp.read_workbook(_tracker_file(), sheet="Config")
        if rows and len(rows) >= 2:
            # Config format: Key, Values (comma-separated)
            for row in rows[1:]:
                if row and len(row) >= 2 and row[0]:
                    key = str(row[0]).strip()
                    values = [v.strip() for v in str(row[1]).split(",") if v.strip()]
                    if key in _mpcp_config:
                        _mpcp_config[key] = values
        # Reached here without a transport error → safe to persist later.
        _config_load_ok = True
    except SharePointError as e:
        # Connectivity/service failure — do NOT mark load ok, so we won't
        # overwrite the real Config sheet with defaults.
        logger.warning(f"Config read failed (SharePoint unavailable): {e}")
    except Exception as e:
        # Missing sheet / parse issue on a reachable file — genuine empty case.
        logger.debug(f"Config not found, using defaults: {e}")
        _config_load_ok = True


async def _persist_config(sp: SharePointClient) -> None:
    """Write config to SharePoint Config sheet.

    Guarded by ``_config_load_ok`` (NOT the hierarchy's ``_load_ok``): the
    config lists are independent of the hierarchy data, so config writes must
    not depend on whether the hierarchy loaded. We only refuse when the Config
    sheet itself could not be read, to avoid clobbering it with defaults.
    """
    if not _config_load_ok:
        raise SharePointError(
            "Refusing to persist MPCP config: the Config sheet was not loaded "
            "successfully. Retry once storage is reachable."
        )
    rows = [["Key", "Values"]]
    for key, values in _mpcp_config.items():
        rows.append([key, ", ".join(values)])
    await sp.write_rows(_tracker_file(), "Config", rows)


# =============================================================================
# FINANCIAL YEAR SWITCHING
# =============================================================================


async def switch_financial_year(fy_label: str, sp: SharePointClient) -> None:
    """Switch to a different FY by reloading all data from that FY's workbook."""
    global _active_fy_override, _loaded
    _active_fy_override = fy_label
    _loaded = False  # Force reload
    await ensure_loaded(sp)
