"""Dashboard Calculator for the MPCP Project Tracker.

Handles:
- Aggregate metrics (RAG counts, by vendor/PO/type/LoB)
- Domain × BU × Stream summary table
- Critical items list
- Open dependencies list
- Budget summary
- BU filtering and multi-filter AND logic

Requirements: 9, 19, 22
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.mpcp_schemas import (
    BudgetData,
    BusinessUnit,
    DashboardMetrics,
    Dependency,
    DependencyStatus,
    Project,
    RAGStatus,
)
from app.services.mpcp_budget_service import is_over_budget
from app.services.mpcp_dependencies_service import compute_days_overdue

logger = logging.getLogger(__name__)


def compute_dashboard_metrics(
    projects: List[Project],
    dependencies: List[Dependency],
    budgets: List[BudgetData],
    bu_filter: Optional[BusinessUnit] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> DashboardMetrics:
    """Compute aggregated dashboard metrics.

    Applies BU filter first, then additional filters before aggregation.
    """
    # Apply BU filter
    if bu_filter:
        projects = [p for p in projects if p.bu == bu_filter]

    # Apply additional AND-logic filters
    if filters:
        projects = apply_filters(projects, filters)

    # Filter dependencies and budgets to matched project IDs
    project_ids = {p.id for p in projects}
    filtered_deps = [d for d in dependencies if d.project_id in project_ids]
    filtered_budgets = [b for b in budgets if b.project_id in project_ids]

    # RAG counts
    green = sum(1 for p in projects if p.rag_status == RAGStatus.GREEN)
    yellow = sum(1 for p in projects if p.rag_status == RAGStatus.YELLOW)
    red = sum(1 for p in projects if p.rag_status == RAGStatus.RED)

    # By vendor
    by_vendor: Dict[str, Dict[str, int]] = {}
    for p in projects:
        v = p.vendor or "Unassigned"
        if v not in by_vendor:
            by_vendor[v] = {"total": 0, "Green": 0, "Yellow": 0, "Red": 0}
        by_vendor[v]["total"] += 1
        by_vendor[v][p.rag_status.value] += 1

    # By PO
    by_po: Dict[str, Dict[str, int]] = {}
    for p in projects:
        po = p.product_owner or "Unassigned"
        if po not in by_po:
            by_po[po] = {"total": 0, "Green": 0, "Yellow": 0, "Red": 0}
        by_po[po]["total"] += 1
        by_po[po][p.rag_status.value] += 1

    # By type
    by_type: Dict[str, int] = {}
    for p in projects:
        t = p.project_type.value if p.project_type else "Unassigned"
        by_type[t] = by_type.get(t, 0) + 1

    # By LoB
    by_lob: Dict[str, Dict[str, int]] = {}
    for p in projects:
        lob = p.lob.value if p.lob else "Unassigned"
        if lob not in by_lob:
            by_lob[lob] = {"total": 0, "Green": 0, "Yellow": 0, "Red": 0}
        by_lob[lob]["total"] += 1
        by_lob[lob][p.rag_status.value] += 1

    # Domain × BU × Stream summary
    domain_bu_stream: Dict[str, Dict[str, int]] = {}
    for p in projects:
        key = f"{p.domain.value if p.domain else 'N/A'}|{p.bu.value if p.bu else 'N/A'}|{p.stream.value if p.stream else 'N/A'}"
        if key not in domain_bu_stream:
            domain_bu_stream[key] = {"total": 0, "Green": 0, "Yellow": 0, "Red": 0}
        domain_bu_stream[key]["total"] += 1
        domain_bu_stream[key][p.rag_status.value] += 1

    by_domain_bu_stream = []
    for key, counts in domain_bu_stream.items():
        parts = key.split("|")
        by_domain_bu_stream.append({
            "domain": parts[0],
            "bu": parts[1],
            "stream": parts[2],
            **counts,
        })

    # Critical items (all Red projects with RAG context)
    critical_items = []
    for p in projects:
        if p.rag_status == RAGStatus.RED:
            item = {
                "project_id": p.id,
                "project_name": p.name,
                "vendor": p.vendor,
                "product_owner": p.product_owner,
            }
            if p.rag_context:
                item["why"] = p.rag_context.why
                item["who"] = p.rag_context.who
                item["eta"] = str(p.rag_context.eta) if p.rag_context.eta else None
            critical_items.append(item)

    # Open dependencies sorted by urgency
    open_deps = [d for d in filtered_deps if d.status != DependencyStatus.RESOLVED]
    open_deps.sort(key=lambda d: d.cutoff_date)
    open_deps_list = []
    for d in open_deps:
        open_deps_list.append({
            "dependency_id": d.id,
            "project_id": d.project_id,
            "description": d.description,
            "external_owner": d.external_owner,
            "cutoff_date": str(d.cutoff_date),
            "days_overdue": compute_days_overdue(d),
            "status": d.status.value,
        })

    # Budget summary
    total_approved = sum(b.approved_budget for b in filtered_budgets)
    total_exhausted = sum(b.total_spent for b in filtered_budgets)
    total_remaining = sum(b.remaining for b in filtered_budgets)
    over_budget_count = sum(1 for b in filtered_budgets if is_over_budget(b))

    return DashboardMetrics(
        total_projects=len(projects),
        green_count=green,
        yellow_count=yellow,
        red_count=red,
        open_dependencies=len(open_deps),
        budget_total_approved=total_approved,
        budget_total_exhausted=total_exhausted,
        budget_total_remaining=total_remaining,
        budget_over_count=over_budget_count,
        by_vendor=by_vendor,
        by_po=by_po,
        by_type=by_type,
        by_lob=by_lob,
        by_domain_bu_stream=by_domain_bu_stream,
        critical_items=critical_items,
        open_dependencies_list=open_deps_list,
    )


def apply_filters(projects: List[Project], filters: Dict[str, Any]) -> List[Project]:
    """Apply AND-logic filtering on projects.

    Supported filter keys:
    - rag: RAGStatus value
    - vendor: vendor name
    - po: product owner name
    - type: ProjectType value
    - lob: BusinessUnit value
    - domain: TrackerDomain value
    - stream: TrackerStream value
    - q: text search on project name (case-insensitive)
    """
    filtered = projects

    if "rag" in filters and filters["rag"]:
        filtered = [p for p in filtered if p.rag_status.value == filters["rag"]]
    if "vendor" in filters and filters["vendor"]:
        filtered = [p for p in filtered if p.vendor == filters["vendor"]]
    if "po" in filters and filters["po"]:
        filtered = [p for p in filtered if p.product_owner == filters["po"]]
    if "type" in filters and filters["type"]:
        filtered = [p for p in filtered if p.project_type and p.project_type.value == filters["type"]]
    if "lob" in filters and filters["lob"]:
        filtered = [p for p in filtered if p.lob and p.lob.value == filters["lob"]]
    if "domain" in filters and filters["domain"]:
        filtered = [p for p in filtered if p.domain and p.domain.value == filters["domain"]]
    if "stream" in filters and filters["stream"]:
        filtered = [p for p in filtered if p.stream and p.stream.value == filters["stream"]]
    if "q" in filters and filters["q"]:
        q = filters["q"].lower()
        filtered = [p for p in filtered if q in p.name.lower()]

    return filtered
