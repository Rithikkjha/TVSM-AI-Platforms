"""RAG Engine for the MPCP Project Tracker.

Handles:
- 3W1H validation for Yellow/Red statuses
- Worst-child-wins propagation (Milestone→Project→CP→MP)
- RAG history logging
- Manual vs propagated RAG distinction

Requirements: 6, 7
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models.mpcp_schemas import (
    RAGContext,
    RAGHistoryEntry,
    RAGSeverity,
    RAGStatus,
)

logger = logging.getLogger(__name__)

# Map RAGStatus to numeric severity for comparison
_SEVERITY_MAP = {
    RAGStatus.GREEN: RAGSeverity.GREEN,
    RAGStatus.YELLOW: RAGSeverity.YELLOW,
    RAGStatus.RED: RAGSeverity.RED,
}


def compute_propagated_rag(children_statuses: List[RAGStatus]) -> Optional[RAGStatus]:
    """Compute propagated RAG using worst-child-wins logic.

    Returns the highest severity RAG from children.
    Returns None if no children (no propagation override).
    Commutative — order doesn't affect result.
    """
    if not children_statuses:
        return None
    worst = max(children_statuses, key=lambda s: _SEVERITY_MAP[s])
    return worst


def validate_rag_context(status: RAGStatus, context: Optional[RAGContext]) -> List[str]:
    """Validate that 3W1H fields are provided for Yellow/Red.

    Returns list of missing field names. Empty list means valid.
    """
    if status == RAGStatus.GREEN:
        return []

    if context is None:
        return ["what", "why", "who", "how", "eta"]

    missing = []
    if not context.what:
        missing.append("what")
    if not context.why:
        missing.append("why")
    if not context.who:
        missing.append("who")
    if not context.how:
        missing.append("how")
    if not context.eta:
        missing.append("eta")
    return missing


def create_rag_history_entry(
    entity_type: str,
    entity_id: str,
    previous_status: RAGStatus,
    new_status: RAGStatus,
    context: Optional[RAGContext],
    changed_by: str,
) -> RAGHistoryEntry:
    """Create a RAG history entry for logging."""
    return RAGHistoryEntry(
        entity_type=entity_type,
        entity_id=entity_id,
        previous_status=previous_status,
        new_status=new_status,
        rag_context=context,
        changed_by=changed_by,
        timestamp=datetime.now(timezone.utc),
    )


def get_effective_rag(
    manual_rag: RAGStatus,
    propagated_rag: Optional[RAGStatus],
) -> RAGStatus:
    """Get the effective RAG for display.

    If propagated exists, returns the worst of manual and propagated.
    Otherwise returns manual.
    """
    if propagated_rag is None:
        return manual_rag
    return max(
        [manual_rag, propagated_rag],
        key=lambda s: _SEVERITY_MAP[s],
    )
