"""MPCP Project Tracker API router.

Provides endpoints for the full MPCP hierarchy lifecycle:
- Managing Points, Check Points, Projects CRUD
- Process Track stage management
- Execution Track milestone management
- RAG status and context management
- Dependencies CRUD
- Budget management
- Dashboard and search
- Export and weekly report

Requirements: 13, 14
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, UploadFile, File, status

from app.middleware.auth import (
    AuthenticatedUser,
    get_current_user,
    require_budget_access,
)
from app.models.mpcp_schemas import (
    BudgetData,
    BudgetTransactionCreateRequest,
    BudgetUpdateRequest,
    BusinessUnit,
    CPCreateRequest,
    CPUpdateRequest,
    DashboardMetrics,
    Dependency,
    DependencyCreateRequest,
    DependencyUpdateRequest,
    ExecutionMilestone,
    ExecutionTrackResponse,
    ManagingPoint,
    MilestoneCreateRequest,
    MilestoneTask,
    MilestoneTaskCreateRequest,
    MilestoneTaskUpdateRequest,
    MilestoneUpdateRequest,
    MPCreateRequest,
    MPTheme,
    MPUpdateRequest,
    ProcessStage,
    ProcessTrackResponse,
    ProcessTrackStage,
    Project,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    RAGContext,
    RAGContextUpdateRequest,
    RAGHistoryEntry,
    RAGStatus,
    RAGUpdateRequest,
    StageUpdateRequest,
)
from app.services.sharepoint_client import SharePointClient, SharePointError
from app.services import mpcp_tracker_service as tracker
from app.services.execution_track_engine import (
    compute_cumulative_slippage,
    compute_fast_track_days,
    compute_time_axis,
    compute_total_actual_days,
    compute_total_planned_days,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mpcp-tracker", tags=["MPCP Tracker"])


def _get_sp() -> SharePointClient:
    return SharePointClient()


# ==========================================================================
# MANAGING POINTS
# ==========================================================================


@router.get("/mps", response_model=List[ManagingPoint])
async def list_managing_points(
    theme: Optional[MPTheme] = None,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """List all Managing Points, optionally filtered by theme."""
    sp = _get_sp()
    try:
        return await tracker.list_mps(sp, theme_filter=theme)
    except SharePointError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Storage unavailable")


@router.post("/mps", status_code=status.HTTP_201_CREATED, response_model=ManagingPoint)
async def create_managing_point(
    request: MPCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Create a new Managing Point. Any authenticated user may create."""
    sp = _get_sp()
    try:
        return await tracker.create_mp(request, user.identity.displayName, sp)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except SharePointError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Storage unavailable")


@router.get("/mps/{mp_id}", response_model=ManagingPoint)
async def get_managing_point(
    mp_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get a Managing Point by ID."""
    sp = _get_sp()
    try:
        return await tracker.get_mp(mp_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"MP {mp_id} not found")


@router.put("/mps/{mp_id}", response_model=ManagingPoint)
async def update_managing_point(
    mp_id: str,
    request: MPUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update a Managing Point."""
    sp = _get_sp()
    try:
        return await tracker.update_mp(mp_id, request, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"MP {mp_id} not found")
    except SharePointError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Storage unavailable")


@router.delete("/mps/{mp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_managing_point(
    mp_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete a Managing Point (must have 0 CPs)."""
    sp = _get_sp()
    try:
        await tracker.delete_mp(mp_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"MP {mp_id} not found")
    except tracker.DeleteGuardError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))


# ==========================================================================
# CHECK POINTS
# ==========================================================================


@router.get("/mps/{mp_id}/cps")
async def list_check_points(
    mp_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """List all Check Points under an MP."""
    sp = _get_sp()
    try:
        return await tracker.list_cps(mp_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"MP {mp_id} not found")


@router.get("/cps/all")
async def list_all_check_points(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """List ALL Check Points across all MPs in one call (avoids N+1 queries)."""
    sp = _get_sp()
    await tracker.ensure_loaded(sp)
    from app.services.mpcp_tracker_service import _check_points
    return list(_check_points.values())


@router.post("/mps/{mp_id}/cps", status_code=status.HTTP_201_CREATED)
async def create_check_point(
    mp_id: str,
    request: CPCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Create a Check Point under an MP. Any authenticated user may create."""
    sp = _get_sp()
    try:
        return await tracker.create_cp(mp_id, request, user.identity.displayName, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"MP {mp_id} not found")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.get("/cps/{cp_id}")
async def get_check_point(
    cp_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get a Check Point by ID."""
    sp = _get_sp()
    try:
        return await tracker.get_cp(cp_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"CP {cp_id} not found")


@router.put("/cps/{cp_id}")
async def update_check_point(
    cp_id: str,
    request: CPUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update a Check Point."""
    sp = _get_sp()
    try:
        return await tracker.update_cp(cp_id, request, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"CP {cp_id} not found")


@router.delete("/cps/{cp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_check_point(
    cp_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete a Check Point (must have 0 projects)."""
    sp = _get_sp()
    try:
        await tracker.delete_cp(cp_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"CP {cp_id} not found")
    except tracker.DeleteGuardError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))


# ==========================================================================
# PROJECTS
# ==========================================================================


@router.get("/cps/{cp_id}/projects", response_model=List[Project])
async def list_projects(
    cp_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """List all Projects under a CP."""
    sp = _get_sp()
    try:
        return await tracker.list_projects(cp_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"CP {cp_id} not found")


@router.get("/projects/all", response_model=List[Project])
async def list_all_projects(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """List all projects across the hierarchy."""
    sp = _get_sp()
    return await tracker.list_all_projects(sp)


@router.post("/cps/{cp_id}/projects", status_code=status.HTTP_201_CREATED)
async def create_project(
    cp_id: str,
    request: ProjectCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Create a Project under a CP. Any authenticated user may create."""
    sp = _get_sp()
    try:
        return await tracker.create_project(cp_id, request, user.identity.displayName, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"CP {cp_id} not found")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get a Project by ID."""
    sp = _get_sp()
    try:
        return await tracker.get_project(project_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")


@router.put("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update a Project."""
    sp = _get_sp()
    try:
        return await tracker.update_project(project_id, request, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.put("/projects/{project_id}/move", response_model=Project)
async def move_project(
    project_id: str,
    body: dict = Body(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Move a Project to a different Check Point (reassign its parent MP/CP)."""
    sp = _get_sp()
    target_cp_id = (body or {}).get("target_cp_id", "").strip()
    if not target_cp_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "target_cp_id is required")
    user_name = user.identity.displayName if user.identity else (user.email or "")
    try:
        return await tracker.move_project(project_id, target_cp_id, user_name, sp)
    except tracker.EntityNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete a Project and all associated data."""
    sp = _get_sp()
    try:
        await tracker.delete_project(project_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")


# ==========================================================================
# PROCESS TRACK
# ==========================================================================


@router.get("/projects/{project_id}/process-track", response_model=ProcessTrackResponse)
async def get_process_track(
    project_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get all 8 process track stages for a project."""
    sp = _get_sp()
    try:
        stages = await tracker.get_process_track(project_id, sp)
        project = await tracker.get_project(project_id, sp)
        return ProcessTrackResponse(
            project_id=project_id,
            stages=stages,
            current_stage=project.current_stage,
        )
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")


@router.put("/projects/{project_id}/process-track/{stage}")
async def update_process_track_stage(
    project_id: str,
    stage: ProcessStage,
    request: StageUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update a process track stage status/dates."""
    sp = _get_sp()
    try:
        user_name = user.identity.displayName if user.identity else (user.email or "")
        stages = await tracker.update_stage(project_id, stage, request, user_name, sp)
        project = await tracker.get_project(project_id, sp)
        return ProcessTrackResponse(
            project_id=project_id,
            stages=stages,
            current_stage=project.current_stage,
        )
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")
    except tracker.StageValidationError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except SharePointError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))


# ==========================================================================
# EXECUTION TRACK (MILESTONES)
# ==========================================================================


@router.get("/projects/{project_id}/execution-track", response_model=ExecutionTrackResponse)
async def get_execution_track(
    project_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get full execution track with milestones and computed metrics."""
    sp = _get_sp()
    try:
        milestones = await tracker.get_milestones(project_id, sp)
        project = await tracker.get_project(project_id, sp)
        time_start, time_end = compute_time_axis(milestones)
        return ExecutionTrackResponse(
            project_id=project_id,
            milestones=milestones,
            total_planned_days=compute_total_planned_days(milestones),
            total_actual_days=compute_total_actual_days(milestones),
            cumulative_slippage=compute_cumulative_slippage(milestones),
            revised_target_date=project.revised_target_date,
            fast_track_days=compute_fast_track_days(milestones, project.revised_target_date),
            time_axis_start=time_start,
            time_axis_end=time_end,
        )
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")


@router.post("/projects/{project_id}/milestones", status_code=status.HTTP_201_CREATED)
async def add_milestone(
    project_id: str,
    request: MilestoneCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Add a milestone to a project's execution track."""
    sp = _get_sp()
    try:
        return await tracker.add_milestone(project_id, request, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.put("/projects/{project_id}/milestones/{milestone_id}")
async def update_milestone(
    project_id: str,
    milestone_id: str,
    request: MilestoneUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update a milestone (actuals, dates, etc.)."""
    sp = _get_sp()
    try:
        user_name = user.identity.displayName if user.identity else (user.email or "")
        # Capture old milestone state for changelog
        old_milestones = await tracker.get_milestones(project_id, sp)
        old_ms = next((m for m in old_milestones if m.id == milestone_id), None)

        result = await tracker.update_milestone(project_id, milestone_id, request, sp)

        # Log key field changes
        if old_ms:
            if request.actual_start is not None and str(request.actual_start) != str(old_ms.actual_start or ""):
                await tracker._log_project_change(project_id, f"milestone.{old_ms.name}.actual_start", str(old_ms.actual_start or ""), str(request.actual_start), user_name, "Milestone actual start updated", sp)
            if request.actual_end is not None and str(request.actual_end) != str(old_ms.actual_end or ""):
                await tracker._log_project_change(project_id, f"milestone.{old_ms.name}.actual_end", str(old_ms.actual_end or ""), str(request.actual_end), user_name, "Milestone actual end updated", sp)
            if request.planned_start is not None and str(request.planned_start) != str(old_ms.planned_start or ""):
                await tracker._log_project_change(project_id, f"milestone.{old_ms.name}.planned_start", str(old_ms.planned_start or ""), str(request.planned_start), user_name, "Milestone planned start updated", sp)
            if request.planned_end is not None and str(request.planned_end) != str(old_ms.planned_end or ""):
                await tracker._log_project_change(project_id, f"milestone.{old_ms.name}.planned_end", str(old_ms.planned_end or ""), str(request.planned_end), user_name, "Milestone planned end updated", sp)
        return result
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Milestone not found")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.delete("/projects/{project_id}/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone(
    project_id: str,
    milestone_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Remove a milestone from a project."""
    sp = _get_sp()
    await tracker.delete_milestone(project_id, milestone_id, sp)


# ==========================================================================
# MILESTONE TASKS (Sub-tasks under milestones)
# ==========================================================================


@router.get("/projects/{project_id}/all-tasks")
async def get_all_tasks_for_project(
    project_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get all tasks for all milestones of a project, grouped by milestone_id."""
    sp = _get_sp()
    try:
        milestones = await tracker.get_milestones(project_id, sp)
        result = {}
        for m in milestones:
            tasks = await tracker.get_milestone_tasks(project_id, m.id, sp)
            result[m.id] = [t.model_dump(mode="json") for t in tasks]
        return result
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")


@router.get("/projects/{project_id}/milestones/{milestone_id}/tasks", response_model=List[MilestoneTask])
async def get_milestone_tasks(
    project_id: str,
    milestone_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get all tasks under a milestone."""
    sp = _get_sp()
    try:
        return await tracker.get_milestone_tasks(project_id, milestone_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Milestone {milestone_id} not found")


@router.post("/projects/{project_id}/milestones/{milestone_id}/tasks", status_code=status.HTTP_201_CREATED, response_model=MilestoneTask)
async def add_milestone_task(
    project_id: str,
    milestone_id: str,
    request: MilestoneTaskCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Add a task under a milestone."""
    sp = _get_sp()
    try:
        return await tracker.add_milestone_task(project_id, milestone_id, request, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Milestone {milestone_id} not found in Project {project_id}")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.put("/projects/{project_id}/milestones/{milestone_id}/tasks/{task_id}", response_model=MilestoneTask)
async def update_milestone_task(
    project_id: str,
    milestone_id: str,
    task_id: str,
    request: MilestoneTaskUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update a milestone task."""
    sp = _get_sp()
    try:
        return await tracker.update_milestone_task(project_id, milestone_id, task_id, request, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Task {task_id} not found")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.delete("/projects/{project_id}/milestones/{milestone_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone_task(
    project_id: str,
    milestone_id: str,
    task_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Remove a task from a milestone."""
    sp = _get_sp()
    try:
        await tracker.delete_milestone_task(project_id, milestone_id, task_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Task {task_id} not found")


# ==========================================================================
# RAG STATUS
# ==========================================================================


@router.put("/rag/{entity_type}/{entity_id}")
async def update_rag_status(
    entity_type: str,
    entity_id: str,
    request: RAGUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update RAG status with 3W1H context (required for Yellow/Red)."""
    sp = _get_sp()
    if entity_type not in ("MP", "CP", "Project"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "entity_type must be MP, CP, or Project")
    context = None
    if request.status in (RAGStatus.YELLOW, RAGStatus.RED):
        context = RAGContext(
            what=request.what, why=request.why, who=request.who,
            owner_team=request.owner_team, how=request.how, eta=request.eta,
        )
    try:
        return await tracker.update_rag(
            entity_type, entity_id, request.status, context,
            user.identity.displayName, sp,
        )
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{entity_type} {entity_id} not found")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.put("/rag/{entity_type}/{entity_id}/context")
async def update_rag_context(
    entity_type: str,
    entity_id: str,
    request: RAGContextUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update RAG context without changing status."""
    sp = _get_sp()
    if entity_type not in ("MP", "CP", "Project"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "entity_type must be MP, CP, or Project")
    context = RAGContext(
        what=request.what, why=request.why, who=request.who,
        owner_team=request.owner_team, how=request.how, eta=request.eta,
    )
    try:
        return await tracker.update_rag_context_only(entity_type, entity_id, context, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{entity_type} {entity_id} not found")


@router.get("/rag/{entity_type}/{entity_id}/history")
async def get_rag_history(
    entity_type: str,
    entity_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get RAG change history for an entity."""
    sp = _get_sp()
    if entity_type not in ("MP", "CP", "Project"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "entity_type must be MP, CP, or Project")
    try:
        history = await tracker.get_rag_history(entity_type, entity_id, sp)
        return [h.model_dump() for h in history]
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{entity_type} {entity_id} not found")


# ==========================================================================
# DEPENDENCIES
# ==========================================================================


@router.get("/projects/{project_id}/dependencies", response_model=List[Dependency])
async def get_dependencies(
    project_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get all dependencies for a project."""
    sp = _get_sp()
    try:
        return await tracker.get_dependencies(project_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")


@router.post("/projects/{project_id}/dependencies", status_code=status.HTTP_201_CREATED)
async def add_dependency(
    project_id: str,
    request: DependencyCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Add a dependency to a project."""
    sp = _get_sp()
    try:
        return await tracker.add_dependency(project_id, request, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")


@router.put("/projects/{project_id}/dependencies/{dep_id}")
async def update_dependency(
    project_id: str,
    dep_id: str,
    request: DependencyUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update a dependency."""
    sp = _get_sp()
    try:
        return await tracker.update_dependency(project_id, dep_id, request, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dependency not found")


@router.delete("/projects/{project_id}/dependencies/{dep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(
    project_id: str,
    dep_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Remove a dependency."""
    sp = _get_sp()
    await tracker.delete_dependency(project_id, dep_id, sp)


# ==========================================================================
# BUDGET
# ==========================================================================


@router.get("/projects/{project_id}/budget", response_model=BudgetData)
async def get_budget(
    project_id: str,
    user: AuthenticatedUser = Depends(require_budget_access),
):
    """Get budget data for a project. Not available to Partner role."""
    sp = _get_sp()
    try:
        return await tracker.get_budget(project_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")


@router.put("/projects/{project_id}/budget", response_model=BudgetData)
async def update_budget(
    project_id: str,
    request: BudgetUpdateRequest,
    user: AuthenticatedUser = Depends(require_budget_access),
):
    """Update budget data for a project. Not available to Partner role."""
    sp = _get_sp()
    try:
        user_name = user.identity.displayName if user.identity else (user.email or "")
        # Capture old values for changelog
        old_budget = await tracker.get_budget(project_id, sp)
        old_approved = old_budget.approved_budget
        old_internal = old_budget.internal_estimate

        result = await tracker.update_budget(project_id, request, sp)

        # Log changes to changelog
        if request.approved_budget is not None and abs((request.approved_budget or 0) - (old_approved or 0)) > 0.01:
            await tracker._log_project_change(project_id, "budget.approved_budget", f"₹{old_approved:,.0f}", f"₹{request.approved_budget:,.0f}", user_name, "Budget updated", sp)
        if request.internal_estimate is not None and abs((request.internal_estimate or 0) - (old_internal or 0)) > 0.01:
            await tracker._log_project_change(project_id, "budget.internal_estimate", f"₹{old_internal:,.0f}", f"₹{request.internal_estimate:,.0f}", user_name, "Budget updated", sp)
        if request.quarterly_plan is not None:
            await tracker._log_project_change(project_id, "budget.quarterly_plan", "", str(request.quarterly_plan), user_name, "Quarterly plan updated", sp)
        if request.remarks is not None:
            await tracker._log_project_change(project_id, "budget.remarks", "", request.remarks or "", user_name, "Budget remarks updated", sp)
        return result
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")


@router.post("/projects/{project_id}/budget/transactions", status_code=status.HTTP_201_CREATED)
async def add_budget_transaction(
    project_id: str,
    request: BudgetTransactionCreateRequest,
    user: AuthenticatedUser = Depends(require_budget_access),
):
    """Add a transaction (PO, CR, Spend, Refund) to the project budget.

    Not available to Partner role.
    """
    sp = _get_sp()
    try:
        user_name = user.identity.displayName if user.identity else (user.email or "")
        budget = await tracker.get_budget(project_id, sp)
        from app.services.mpcp_budget_service import add_transaction
        txn = add_transaction(budget, request)
        # Persist
        from app.services.mpcp_tracker_service import _budgets, _persist_budgets
        _budgets[project_id] = budget
        await _persist_budgets(sp)
        # Log transaction to changelog
        txn_desc = f"{request.transaction_type.value}: ₹{request.amount:,.0f}"
        if request.vendor:
            txn_desc += f" ({request.vendor})"
        if request.po_number:
            txn_desc += f" [PO: {request.po_number}]"
        await tracker._log_project_change(project_id, f"budget.transaction", "", txn_desc, user_name, f"Transaction added: {request.transaction_type.value}", sp)
        return txn
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")


@router.get("/projects/{project_id}/changelog")
async def get_project_changelog(
    project_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=5, le=100, description="Items per page"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get the change history for a project (who changed what, when). Paginated."""
    sp = _get_sp()
    try:
        all_entries = await tracker.get_project_changelog(project_id, sp)
        total = len(all_entries)
        total_pages = max(1, (total + page_size - 1) // page_size)
        start = (page - 1) * page_size
        end = start + page_size
        entries = all_entries[start:end]
        return {
            "project_id": project_id,
            "entries": entries,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")


# ==========================================================================
# DASHBOARD & SEARCH
# ==========================================================================


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard(
    bu: Optional[BusinessUnit] = None,
    rag: Optional[str] = None,
    vendor: Optional[str] = None,
    po: Optional[str] = None,
    type: Optional[str] = None,
    lob: Optional[str] = None,
    domain: Optional[str] = None,
    stream: Optional[str] = None,
    q: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get aggregated dashboard metrics with optional BU filter and filters."""
    sp = _get_sp()
    filters = {}
    if rag:
        filters["rag"] = rag
    if vendor:
        filters["vendor"] = vendor
    if po:
        filters["po"] = po
    if type:
        filters["type"] = type
    if lob:
        filters["lob"] = lob
    if domain:
        filters["domain"] = domain
    if stream:
        filters["stream"] = stream
    if q:
        filters["q"] = q

    metrics = await tracker.get_dashboard(sp, bu_filter=bu, filters=filters or None)

    # Partner role must not see budget figures — zero out budget totals so
    # they never leak through the dashboard aggregate.
    if not user.can_view_budget:
        metrics.budget_total_approved = 0.0
        metrics.budget_total_exhausted = 0.0
        metrics.budget_total_remaining = 0.0
        metrics.budget_over_count = 0

    return metrics


@router.get("/search")
async def search_projects(
    q: Optional[str] = None,
    rag: Optional[str] = None,
    vendor: Optional[str] = None,
    po: Optional[str] = None,
    type: Optional[str] = None,
    lob: Optional[str] = None,
    domain: Optional[str] = None,
    stream: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Search/filter projects with full hierarchy path."""
    sp = _get_sp()
    filters = {}
    if q:
        filters["q"] = q
    if rag:
        filters["rag"] = rag
    if vendor:
        filters["vendor"] = vendor
    if po:
        filters["po"] = po
    if type:
        filters["type"] = type
    if lob:
        filters["lob"] = lob
    if domain:
        filters["domain"] = domain
    if stream:
        filters["stream"] = stream

    return await tracker.search_projects(sp, filters)

# ==========================================================================
# BULK UPLOAD (MP + CP + Projects from Excel)
# ==========================================================================


@router.post("/bulk-upload")
async def bulk_upload_hierarchy(
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Bulk upload MPs, CPs, and Projects from an Excel file.

    Expected sheets:
    - 'MPs': Code, Name, Theme, Owner, LoB, BU
    - 'CPs': Code, Name, Owner, Description, Domain, Stream, ParentMPCode
    - 'Projects': Name, Type, Vendor, ProductOwner, LoB, BU, Domain, Stream, Description, ParentCPCode

    Returns summary of created entities and any row-level errors.
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only .xlsx/.xls files accepted")

    sp = _get_sp()
    try:
        content = await file.read()
        result = await tracker.bulk_upload_hierarchy(
            content, user.identity.displayName, sp
        )
        return result
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception as e:
        logger.exception(f"Bulk upload error: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Upload failed: {str(e)}")


@router.get("/templates/hierarchy-upload")
async def download_hierarchy_template(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Download an Excel template for bulk hierarchy upload."""
    from fastapi.responses import Response
    content = tracker.generate_hierarchy_template()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=MPCP_Hierarchy_Upload_Template.xlsx"},
    )


# ==========================================================================
# EXPORT & REPORTS
# ==========================================================================


@router.get("/export")
async def export_portfolio_report(
    rag: Optional[str] = None,
    vendor: Optional[str] = None,
    bu: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Download formatted Excel portfolio report."""
    from fastapi.responses import Response
    from app.services.mpcp_export_service import generate_portfolio_report, get_export_filename

    sp = _get_sp()
    await tracker.ensure_loaded(sp)

    # Access internal data
    from app.services.mpcp_tracker_service import (
        _managing_points, _check_points, _projects, _milestones, _budgets, _dependencies
    )

    projects = list(_projects.values())
    if bu:
        projects = [p for p in projects if p.bu.value == bu]
    if rag:
        projects = [p for p in projects if p.rag_status.value == rag]
    if vendor:
        projects = [p for p in projects if p.vendor == vendor]

    content = generate_portfolio_report(
        mps=list(_managing_points.values()),
        cps=list(_check_points.values()),
        projects=projects,
        milestones=_milestones,
        budgets=_budgets,
        dependencies=_dependencies,
    )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={get_export_filename()}"},
    )


@router.get("/export/3w1h")
async def export_3w1h_report(
    rag: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Download 3W1H report (Yellow/Red projects with context)."""
    from fastapi.responses import Response
    from app.services.mpcp_export_service import generate_3w1h_report, get_3w1h_filename

    sp = _get_sp()
    await tracker.ensure_loaded(sp)

    from app.services.mpcp_tracker_service import _managing_points, _check_points, _projects

    content = generate_3w1h_report(
        projects=list(_projects.values()),
        cps=list(_check_points.values()),
        mps=list(_managing_points.values()),
        rag_filter=rag,
    )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={get_3w1h_filename()}"},
    )


@router.post("/weekly-report")
async def send_weekly_report(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Generate and send the weekly email report."""
    from app.services.mpcp_report_service import (
        generate_weekly_report_html, get_report_config, send_report_email,
    )

    sp = _get_sp()
    await tracker.ensure_loaded(sp)

    from app.services.mpcp_tracker_service import (
        _managing_points, _check_points, _projects, _milestones, _dependencies
    )

    html = generate_weekly_report_html(
        projects=list(_projects.values()),
        milestones=_milestones,
        dependencies=_dependencies,
        mps=list(_managing_points.values()),
        cps=list(_check_points.values()),
    )

    config = get_report_config()
    success = await send_report_email(html, config, sp)

    return {
        "success": success,
        "recipients": config.to,
        "cc": config.cc,
        "message": "Report sent" if success else "Failed to send (check Graph API credentials)",
    }


@router.get("/weekly-report/config")
async def get_weekly_report_config(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get weekly report email recipients."""
    from app.services.mpcp_report_service import get_report_config
    return get_report_config()


@router.put("/weekly-report/config")
async def update_weekly_report_config(
    config: "WeeklyReportConfig",
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update weekly report email recipients."""
    from app.models.mpcp_schemas import WeeklyReportConfig
    from app.services.mpcp_report_service import update_report_config
    return update_report_config(config)


@router.post("/projects/{project_id}/milestones/bulk-upload")
async def bulk_upload_milestones(
    project_id: str,
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Bulk upload milestones from Excel/CSV for a project."""
    sp = _get_sp()
    try:
        content = await file.read()
        result = await tracker.bulk_upload_milestones(project_id, content, sp)
        return result
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


# ==========================================================================
# MPCP SETTINGS (configurable Vendors, POs, EMs)
# ==========================================================================


@router.get("/config")
async def get_mpcp_config(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get MPCP configurable lists (vendors, POs, EMs).

    Returned with no-cache headers: a stale cached config would cause the
    settings UI to PUT outdated lists and silently drop items.
    """
    from fastapi.responses import JSONResponse
    sp = _get_sp()
    config = await tracker.get_mpcp_config(sp)
    return JSONResponse(
        content=config,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.put("/config")
async def update_mpcp_config(
    config: dict,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update MPCP configurable lists."""
    sp = _get_sp()
    return await tracker.update_mpcp_config(config, sp)


@router.get("/projects/{project_id}/execution-track/export")
async def export_execution_track(
    project_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Download execution track as Excel (milestones + tasks with plan vs actual)."""
    from fastapi.responses import Response
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from io import BytesIO

    sp = _get_sp()
    try:
        milestones = await tracker.get_milestones(project_id, sp)
        project = await tracker.get_project(project_id, sp)
    except tracker.EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project {project_id} not found")

    wb = Workbook()
    ws = wb.active
    ws.title = "Execution Plan"

    # Header styling
    hfont = Font(bold=True, size=11, color="FFFFFF")
    hfill = PatternFill(start_color="1A237E", end_color="1A237E", fill_type="solid")
    delay_fill = PatternFill(start_color="FFCDD2", end_color="FFCDD2", fill_type="solid")

    # Title
    ws.cell(row=1, column=1, value=f"Execution Plan: {project.name}")
    ws.cell(row=1, column=1).font = Font(bold=True, size=14)

    # Headers
    headers = ["Milestone / Task", "Owner", "Planned Start", "Planned End", "Actual Start", "Actual End", "Delay (days)", "RAG", "Remarks"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.font = hfont
        cell.fill = hfill

    row = 4
    from app.services.mpcp_tracker_service import _milestone_tasks
    delay_items = []  # collect for Delay Report sheet

    for m in milestones:
        # Milestone row (bold)
        ws.cell(row=row, column=1, value=f"📌 {m.name}").font = Font(bold=True)
        ws.cell(row=row, column=3, value=str(m.planned_start) if m.planned_start else "")
        ws.cell(row=row, column=4, value=str(m.planned_end) if m.planned_end else "")
        ws.cell(row=row, column=5, value=str(m.actual_start) if m.actual_start else "")
        ws.cell(row=row, column=6, value=str(m.actual_end) if m.actual_end else "")
        if m.slippage_days:
            ws.cell(row=row, column=7, value=m.slippage_days)
            if m.slippage_days > 0:
                for c in range(1, 10):
                    ws.cell(row=row, column=c).fill = delay_fill
        ws.cell(row=row, column=8, value=m.rag_status.value if m.rag_status else "Green")
        ws.cell(row=row, column=9, value=m.remarks or "")
        rc_list = m.rag_context or []
        if m.is_delayed:
            for rc_entry in rc_list:
                delay_items.append({"type": "Milestone", "name": m.name, "delay": m.slippage_days, "rag_context": rc_entry})
        row += 1

        # Tasks under this milestone
        tasks = _milestone_tasks.get(m.id, [])
        for t in tasks:
            ws.cell(row=row, column=1, value=f"    ↳ {t.name}")
            ws.cell(row=row, column=2, value=t.owner or "")
            ws.cell(row=row, column=3, value=str(t.planned_start) if t.planned_start else "")
            ws.cell(row=row, column=4, value=str(t.planned_end) if t.planned_end else "")
            ws.cell(row=row, column=5, value=str(t.actual_start) if t.actual_start else "")
            ws.cell(row=row, column=6, value=str(t.actual_end) if t.actual_end else "")
            if t.slippage_days:
                ws.cell(row=row, column=7, value=t.slippage_days)
                if t.slippage_days > 0:
                    for c in range(1, 10):
                        ws.cell(row=row, column=c).fill = delay_fill
            ws.cell(row=row, column=8, value=t.rag_status.value if t.rag_status else "Green")
            ws.cell(row=row, column=9, value=t.remarks or "")
            trc_list = t.rag_context or []
            if t.is_delayed:
                for trc_entry in trc_list:
                    delay_items.append({"type": "Task", "name": f"{m.name} → {t.name}", "delay": t.slippage_days, "rag_context": trc_entry})
            row += 1

    # Auto-width
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)

    # ============ DELAY REPORT SHEET ============
    if delay_items:
        ws_d = wb.create_sheet("Delay Report")
        ws_d.cell(row=1, column=1, value=f"Delay Report: {project.name}").font = Font(bold=True, size=14)
        delay_headers = ["Type", "Milestone / Task", "Delay (days)", "What", "Why", "Who (blocking)", "Owner/Team (action)", "How (recovery)", "ETA"]
        for col, h in enumerate(delay_headers, 1):
            cell = ws_d.cell(row=3, column=col, value=h)
            cell.font = hfont
            cell.fill = PatternFill(start_color="C62828", end_color="C62828", fill_type="solid")
        for i, item in enumerate(delay_items, 4):
            ws_d.cell(row=i, column=1, value=item["type"])
            ws_d.cell(row=i, column=2, value=item["name"])
            ws_d.cell(row=i, column=3, value=item["delay"])
            rc = item.get("rag_context")
            if rc:
                ws_d.cell(row=i, column=4, value=rc.what or "")
                ws_d.cell(row=i, column=5, value=rc.why or "")
                ws_d.cell(row=i, column=6, value=rc.who or "")
                ws_d.cell(row=i, column=7, value=rc.owner_team or "")
                ws_d.cell(row=i, column=8, value=rc.how or "")
                ws_d.cell(row=i, column=9, value=str(rc.eta) if rc.eta else "")
        for col in ws_d.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws_d.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)

    # ============ GANTT SHEET (cell-colored horizontal timeline) ============
    from datetime import timedelta
    ws_g = wb.create_sheet("Gantt")
    planned_fill = PatternFill(start_color="90CAF9", end_color="90CAF9", fill_type="solid")
    actual_ok_fill = PatternFill(start_color="A5D6A7", end_color="A5D6A7", fill_type="solid")
    actual_delay_fill = PatternFill(start_color="EF9A9A", end_color="EF9A9A", fill_type="solid")
    week_border_fill = PatternFill(start_color="EEEEEE", end_color="EEEEEE", fill_type="solid")

    # Compute date range
    all_dates = []
    for m in milestones:
        if m.planned_start: all_dates.append(m.planned_start)
        if m.planned_end: all_dates.append(m.planned_end)
        if m.actual_start: all_dates.append(m.actual_start)
        if m.actual_end: all_dates.append(m.actual_end)
        for t in _milestone_tasks.get(m.id, []):
            if t.planned_start: all_dates.append(t.planned_start)
            if t.planned_end: all_dates.append(t.planned_end)
            if t.actual_start: all_dates.append(t.actual_start)
            if t.actual_end: all_dates.append(t.actual_end)

    if all_dates:
        from datetime import date as _date
        min_date = min(all_dates)
        max_date = max(all_dates)
        # Pad by 2 days
        min_date = min_date - timedelta(days=2)
        max_date = max_date + timedelta(days=2)
        total_days = (max_date - min_date).days + 1
        day_count = min(total_days, 120)

        # Row 1: Month headers (merged per month span)
        ws_g.cell(row=1, column=1, value="Milestone / Task").font = Font(bold=True, size=10)
        ws_g.cell(row=1, column=2, value="").font = Font(bold=True, size=9)
        ws_g.column_dimensions['A'].width = 32
        ws_g.column_dimensions['B'].width = 7

        # Row 2: Day-of-month numbers
        ws_g.cell(row=2, column=1, value="").font = Font(size=9)
        ws_g.cell(row=2, column=2, value="P/A").font = Font(bold=True, size=8)

        current_month = None
        month_start_col = 3
        for d in range(day_count):
            col = d + 3
            dt = min_date + timedelta(days=d)
            month_label = dt.strftime("%b %Y")

            # Day number in row 2
            day_cell = ws_g.cell(row=2, column=col, value=dt.day)
            day_cell.font = Font(size=7)
            day_cell.alignment = Alignment(horizontal="center")
            ws_g.column_dimensions[day_cell.column_letter].width = 2.8

            # Month header in row 1
            if month_label != current_month:
                if current_month is not None:
                    pass  # already wrote previous month
                ws_g.cell(row=1, column=col, value=month_label).font = Font(bold=True, size=9, color="1A237E")
                current_month = month_label

            # Light background on Monday columns for week boundary
            if dt.weekday() == 0:
                for rr in range(1, 100):
                    ws_g.cell(row=rr, column=col).fill = week_border_fill

        # Data rows: each milestone gets Plan row + Actual row, tasks same
        grow = 3
        for m in milestones:
            tasks = _milestone_tasks.get(m.id, [])
            # Milestone planned row
            ws_g.cell(row=grow, column=1, value=m.name).font = Font(bold=True, size=10)
            ws_g.cell(row=grow, column=2, value="Plan").font = Font(size=8, color="1565C0")
            if m.planned_start and m.planned_end:
                for d in range((m.planned_end - min_date).days - (m.planned_start - min_date).days + 1):
                    col = (m.planned_start - min_date).days + d + 3
                    if 3 <= col < day_count + 3:
                        ws_g.cell(row=grow, column=col).fill = planned_fill
            grow += 1
            # Milestone actual row
            ws_g.cell(row=grow, column=1, value="")
            ws_g.cell(row=grow, column=2, value="Actual").font = Font(size=8, color="2E7D32")
            if m.actual_start:
                a_end = m.actual_end or max_date
                is_late = m.is_delayed
                fill = actual_delay_fill if is_late else actual_ok_fill
                for d in range((a_end - m.actual_start).days + 1):
                    col = (m.actual_start - min_date).days + d + 3
                    if 3 <= col < day_count + 3:
                        ws_g.cell(row=grow, column=col).fill = fill
            grow += 1

            # Tasks
            for t in tasks:
                ws_g.cell(row=grow, column=1, value=f"  ↳ {t.name}").font = Font(size=9)
                ws_g.cell(row=grow, column=2, value="Plan").font = Font(size=8, color="1565C0")
                if t.planned_start and t.planned_end:
                    for d in range((t.planned_end - t.planned_start).days + 1):
                        col = (t.planned_start - min_date).days + d + 3
                        if 3 <= col < day_count + 3:
                            ws_g.cell(row=grow, column=col).fill = planned_fill
                grow += 1
                ws_g.cell(row=grow, column=1, value="")
                ws_g.cell(row=grow, column=2, value="Actual").font = Font(size=8, color="2E7D32")
                if t.actual_start:
                    a_end = t.actual_end or max_date
                    is_late = (t.actual_end and t.planned_end and t.actual_end > t.planned_end)
                    fill = actual_delay_fill if is_late else actual_ok_fill
                    for d in range((a_end - t.actual_start).days + 1):
                        col = (t.actual_start - min_date).days + d + 3
                        if 3 <= col < day_count + 3:
                            ws_g.cell(row=grow, column=col).fill = fill
                grow += 1

        # Freeze panes so names stay visible when scrolling
        ws_g.freeze_panes = "C3"

    # ============ DEPENDENCIES SHEET ============
    from app.services.mpcp_tracker_service import _dependencies
    deps = _dependencies.get(project_id, [])
    if deps:
        ws_dep = wb.create_sheet("Dependencies")
        ws_dep.cell(row=1, column=1, value=f"Dependencies: {project.name}").font = Font(bold=True, size=14)
        dep_headers = ["Description", "Owner", "Cutoff Date", "Raised Date", "Linked To", "Status", "Overdue", "Escalation Note"]
        for col, h in enumerate(dep_headers, 1):
            cell = ws_dep.cell(row=3, column=col, value=h)
            cell.font = hfont
            cell.fill = hfill
        for i, d in enumerate(deps, 4):
            linked = "Project level"
            if d.milestone_id:
                linked_ms = next((m.name for m in milestones if m.id == d.milestone_id), "Milestone")
                linked = linked_ms
            ws_dep.cell(row=i, column=1, value=d.description)
            ws_dep.cell(row=i, column=2, value=d.external_owner)
            ws_dep.cell(row=i, column=3, value=str(d.cutoff_date))
            ws_dep.cell(row=i, column=4, value=str(d.raised_date))
            ws_dep.cell(row=i, column=5, value=linked)
            ws_dep.cell(row=i, column=6, value=d.status.value)
            ws_dep.cell(row=i, column=7, value="Yes" if d.is_overdue else "No")
            ws_dep.cell(row=i, column=8, value=d.escalation_note or "")
            if d.is_overdue:
                for c in range(1, 9):
                    ws_dep.cell(row=i, column=c).fill = delay_fill
        for col in ws_dep.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws_dep.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)

    # Make Gantt the active sheet when file opens
    wb.active = wb.sheetnames.index("Gantt")

    buf = BytesIO()
    wb.save(buf)
    filename = f"{project.name.replace(' ', '_')}_Execution_Plan.xlsx"
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ==========================================================================
# FINANCIAL YEAR SWITCHING
# ==========================================================================


@router.get("/fy")
async def get_current_fy(user: AuthenticatedUser = Depends(get_current_user)):
    """Get the current active FY and list of available FYs."""
    from app.services.sharepoint_client import get_financial_year_label
    from app.services.mpcp_tracker_service import _active_fy_override
    current = _active_fy_override or get_financial_year_label()
    return {"current_fy": current, "available_fys": ["2024_25", "2025_26", "2026_27"]}


@router.post("/fy/{fy_label}")
async def switch_fy(
    fy_label: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Switch to a different FY. Reloads data from that FY's SharePoint folder."""
    from app.services.mpcp_tracker_service import switch_financial_year
    sp = _get_sp()
    await switch_financial_year(fy_label, sp)
    return {"active_fy": fy_label}
