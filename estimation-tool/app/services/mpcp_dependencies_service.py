"""Dependencies Service for the MPCP Project Tracker.

Handles:
- Dependency CRUD (project-level and milestone-level linking)
- Overdue detection
- Escalation marking
- Resolved date tracking

Requirements: 18
"""

import logging
import uuid
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from app.models.mpcp_schemas import (
    Dependency,
    DependencyCreateRequest,
    DependencyStatus,
    DependencyUpdateRequest,
)

logger = logging.getLogger(__name__)


def create_dependency(
    project_id: str,
    request: DependencyCreateRequest,
) -> Dependency:
    """Create a new Dependency from a request."""
    now = datetime.now(timezone.utc)
    return Dependency(
        id=str(uuid.uuid4()),
        project_id=project_id,
        milestone_id=request.milestone_id,
        description=request.description,
        external_owner=request.external_owner,
        cutoff_date=request.cutoff_date,
        raised_date=date.today(),
        status=request.status,
        is_overdue=_check_overdue(request.cutoff_date, request.status),
        is_blocker=request.is_blocker,
    )


def update_dependency(
    dependency: Dependency,
    request: DependencyUpdateRequest,
) -> Dependency:
    """Apply updates to an existing Dependency."""
    if request.description is not None:
        dependency.description = request.description
    if request.external_owner is not None:
        dependency.external_owner = request.external_owner
    if request.cutoff_date is not None:
        dependency.cutoff_date = request.cutoff_date
    if request.milestone_id is not None:
        dependency.milestone_id = request.milestone_id
    if request.status is not None:
        # Auto-set resolved_date when marking as Resolved
        if request.status == DependencyStatus.RESOLVED and dependency.status != DependencyStatus.RESOLVED:
            dependency.resolved_date = date.today()
        dependency.status = request.status
    if request.escalation_note is not None:
        dependency.escalation_note = request.escalation_note
        if dependency.status != DependencyStatus.ESCALATED:
            dependency.status = DependencyStatus.ESCALATED
    if request.is_blocker is not None:
        dependency.is_blocker = request.is_blocker

    # Recompute overdue
    dependency.is_overdue = _check_overdue(dependency.cutoff_date, dependency.status)
    return dependency


def compute_days_overdue(dep: Dependency) -> int:
    """Compute days overdue for a dependency. 0 if not overdue."""
    if not dep.is_overdue:
        return 0
    return (date.today() - dep.cutoff_date).days


def _check_overdue(cutoff_date: date, status: DependencyStatus) -> bool:
    """A dependency is overdue if cutoff passed and not Resolved."""
    if status == DependencyStatus.RESOLVED:
        return False
    return date.today() > cutoff_date


def get_open_dependencies_sorted(dependencies: List[Dependency]) -> List[Dependency]:
    """Return unresolved dependencies sorted by cutoff date (most urgent first)."""
    open_deps = [d for d in dependencies if d.status != DependencyStatus.RESOLVED]
    return sorted(open_deps, key=lambda d: d.cutoff_date)
