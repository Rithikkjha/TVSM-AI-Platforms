"""Execution Track Engine for the MPCP Project Tracker.

Handles:
- Milestone CRUD operations
- Slippage auto-calculation
- Total slippage computation
- Revised Target Date / fast-track calculation
- Milestone sorting and time axis computation

Requirements: 5, 20
"""

import logging
from datetime import date
from typing import Dict, List, Optional, Tuple

from app.models.mpcp_schemas import ExecutionMilestone

logger = logging.getLogger(__name__)


def compute_slippage(planned_end: Optional[date], actual_end: Optional[date]) -> Optional[int]:
    """Compute slippage in days: (actual_end - planned_end).

    Positive = delayed, negative = ahead of schedule, None = not completed.
    """
    if actual_end is None or planned_end is None:
        return None
    return (actual_end - planned_end).days


def is_delayed(planned_end: Optional[date], actual_end: Optional[date]) -> bool:
    """True if actual_end exceeds planned_end."""
    if actual_end is None or planned_end is None:
        return False
    return actual_end > planned_end


def sort_milestones(milestones: List[Dict]) -> List[Dict]:
    """Sort milestones by planned_start ascending."""
    return sorted(milestones, key=lambda m: m.get("planned_start", date.max))


def sort_milestone_models(milestones: List[ExecutionMilestone]) -> List[ExecutionMilestone]:
    """Sort ExecutionMilestone models by planned_start ascending."""
    return sorted(milestones, key=lambda m: m.planned_start if m.planned_start else date.max)


def compute_time_axis(milestones: List[ExecutionMilestone]) -> Tuple[Optional[date], Optional[date]]:
    """Compute time axis bounds for Gantt scaling.

    Returns (min_planned_start, max_planned_end). None if no milestones with dates.
    """
    dated = [m for m in milestones if m.planned_start and m.planned_end]
    if not dated:
        return None, None
    min_start = min(m.planned_start for m in dated)
    max_end = max(m.planned_end for m in dated)
    return min_start, max_end


def compute_total_planned_days(milestones: List[ExecutionMilestone]) -> int:
    """Total planned duration: last planned_end - first planned_start."""
    dated = [m for m in milestones if m.planned_start and m.planned_end]
    if not dated:
        return 0
    sorted_ms = sort_milestone_models(dated)
    first_start = sorted_ms[0].planned_start
    last_end = max(m.planned_end for m in sorted_ms)
    return (last_end - first_start).days


def compute_total_actual_days(milestones: List[ExecutionMilestone]) -> int:
    """Total actual duration so far from completed milestones."""
    completed = [m for m in milestones if m.actual_start and m.actual_end]
    if not completed:
        return 0
    first_actual = min(m.actual_start for m in completed)
    last_actual = max(m.actual_end for m in completed)
    return (last_actual - first_actual).days


def compute_cumulative_slippage(milestones: List[ExecutionMilestone]) -> int:
    """Sum of slippage days from completed milestones."""
    total = 0
    for m in milestones:
        if m.slippage_days is not None:
            total += m.slippage_days
    return total


def compute_fast_track_days(
    milestones: List[ExecutionMilestone],
    revised_target_date: Optional[date],
) -> Optional[int]:
    """Calculate fast-track recovery days.

    If revised_target_date is earlier than last milestone's planned_end,
    returns the number of days recovered.
    """
    dated = [m for m in milestones if m.planned_end]
    if not dated or revised_target_date is None:
        return None
    last_planned_end = max(m.planned_end for m in dated)
    if revised_target_date < last_planned_end:
        return (last_planned_end - revised_target_date).days
    return None


def update_milestone_computed_fields(milestone: ExecutionMilestone) -> ExecutionMilestone:
    """Recompute slippage_days and is_delayed on a milestone."""
    if milestone.planned_end:
        milestone.slippage_days = compute_slippage(milestone.planned_end, milestone.actual_end)
        milestone.is_delayed = is_delayed(milestone.planned_end, milestone.actual_end)
    else:
        milestone.slippage_days = None
        milestone.is_delayed = False
    return milestone
