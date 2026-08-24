"""Excel Export Service for the MPCP Project Tracker.

Handles:
- Portfolio report (Overview, Hierarchy, Projects, Execution, Budget sheets)
- 3W1H report (Yellow/Red projects with context)
- Per-project milestone plan download
- Conditional RAG cell formatting

Requirements: 16, 20
"""

import logging
from datetime import date, datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from app.models.mpcp_schemas import (
    BudgetData,
    CheckPoint,
    Dependency,
    ExecutionMilestone,
    ManagingPoint,
    Project,
    RAGStatus,
)

logger = logging.getLogger(__name__)

RAG_FILLS = {
    "Green": PatternFill(start_color="92D050", end_color="92D050", fill_type="solid"),
    "Yellow": PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid"),
    "Red": PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid"),
}

HEADER_FONT = Font(bold=True, size=11)
HEADER_FILL = PatternFill(start_color="1A237E", end_color="1A237E", fill_type="solid")
HEADER_FONT_WHITE = Font(bold=True, size=11, color="FFFFFF")


def _write_headers(ws, headers):
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = HEADER_FONT_WHITE
        cell.fill = HEADER_FILL


def _apply_rag_fill(cell, rag_value: str):
    if rag_value in RAG_FILLS:
        cell.fill = RAG_FILLS[rag_value]
        if rag_value == "Red":
            cell.font = Font(bold=True, color="FFFFFF")


def generate_portfolio_report(
    mps: List[ManagingPoint],
    cps: List[CheckPoint],
    projects: List[Project],
    milestones: Dict[str, List[ExecutionMilestone]],
    budgets: Dict[str, BudgetData],
    dependencies: Dict[str, List[Dependency]],
) -> bytes:
    """Generate full portfolio Excel report with multiple sheets."""
    wb = Workbook()

    # --- Overview sheet ---
    ws = wb.active
    ws.title = "Overview"
    _write_headers(ws, ["Metric", "Value"])
    total = len(projects)
    green = sum(1 for p in projects if p.rag_status == RAGStatus.GREEN)
    yellow = sum(1 for p in projects if p.rag_status == RAGStatus.YELLOW)
    red = sum(1 for p in projects if p.rag_status == RAGStatus.RED)
    ws.append(["Total Projects", total])
    ws.append(["Green", green])
    ws.append(["Yellow", yellow])
    ws.append(["Red", red])
    ws.append([""])
    ws.append(["By Vendor", ""])
    vendors = {}
    for p in projects:
        vendors.setdefault(p.vendor, {"total": 0, "G": 0, "Y": 0, "R": 0})
        vendors[p.vendor]["total"] += 1
        vendors[p.vendor][{"Green": "G", "Yellow": "Y", "Red": "R"}[p.rag_status.value]] += 1
    for v, c in vendors.items():
        ws.append([v, f"Total:{c['total']} G:{c['G']} Y:{c['Y']} R:{c['R']}"])
    # Apply RAG fills to overview cells
    for row in ws.iter_rows(min_row=2, max_row=5, min_col=2, max_col=2):
        for cell in row:
            if cell.row == 3:
                _apply_rag_fill(cell, "Green")
            elif cell.row == 4:
                _apply_rag_fill(cell, "Yellow")
            elif cell.row == 5:
                _apply_rag_fill(cell, "Red")

    # --- Hierarchy sheet ---
    ws_h = wb.create_sheet("Hierarchy")
    _write_headers(ws_h, ["MP Code", "MP Name", "Theme", "MP Owner", "CP Code", "CP Name", "CP Owner", "RAG"])
    cp_map = {cp.id: cp for cp in cps}
    mp_map = {mp.id: mp for mp in mps}
    for cp in cps:
        mp = mp_map.get(cp.parent_mp_id)
        row_idx = ws_h.max_row + 1
        ws_h.append([
            mp.code if mp else "", mp.name if mp else "", mp.theme.value if mp else "",
            mp.owner if mp else "", cp.code, cp.name, cp.owner,
            (cp.propagated_rag or cp.rag_status).value,
        ])
        _apply_rag_fill(ws_h.cell(row=row_idx, column=8), (cp.propagated_rag or cp.rag_status).value)

    # --- Projects sheet ---
    ws_p = wb.create_sheet("Projects")
    _write_headers(ws_p, [
        "Project Name", "Type", "Vendor", "PO", "LoB", "BU",
        "Domain", "Stream", "Current Stage", "RAG", "CP Code", "MP Code",
    ])
    for p in projects:
        cp = cp_map.get(p.parent_cp_id)
        mp = mp_map.get(cp.parent_mp_id) if cp else None
        row_idx = ws_p.max_row + 1
        ws_p.append([
            p.name, p.project_type.value if p.project_type else "", p.vendor or "", p.product_owner or "",
            p.lob.value if p.lob else "", p.bu.value if p.bu else "", p.domain.value if p.domain else "",
            p.stream.value if p.stream else "",
            p.current_stage.value if p.current_stage else "",
            p.rag_status.value, cp.code if cp else "", mp.code if mp else "",
        ])
        _apply_rag_fill(ws_p.cell(row=row_idx, column=10), p.rag_status.value)

    # --- Execution sheet ---
    ws_e = wb.create_sheet("Execution")
    _write_headers(ws_e, [
        "Project", "Milestone", "Vendor", "Planned Start", "Planned End",
        "Actual Start", "Actual End", "Slippage (days)", "Delayed", "RAG",
    ])
    for p in projects:
        ms_list = milestones.get(p.id, [])
        for m in ms_list:
            row_idx = ws_e.max_row + 1
            ws_e.append([
                p.name, m.name, m.vendor or "",
                str(m.planned_start) if m.planned_start else "",
                str(m.planned_end) if m.planned_end else "",
                str(m.actual_start) if m.actual_start else "",
                str(m.actual_end) if m.actual_end else "",
                m.slippage_days if m.slippage_days is not None else "",
                "Yes" if m.is_delayed else "No",
                m.rag_status.value,
            ])
            _apply_rag_fill(ws_e.cell(row=row_idx, column=10), m.rag_status.value)

    # --- Budget sheet ---
    ws_b = wb.create_sheet("Budget")
    _write_headers(ws_b, [
        "Project", "Internal Estimate", "Approved Budget", "Total Committed",
        "Total Spent", "Remaining", "Remarks",
    ])
    for p in projects:
        b = budgets.get(p.id)
        if b:
            ws_b.append([
                p.name, b.internal_estimate, b.approved_budget, b.total_committed,
                b.total_spent, b.remaining, b.remarks or "",
            ])

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def generate_3w1h_report(
    projects: List[Project],
    cps: List[CheckPoint],
    mps: List[ManagingPoint],
    rag_filter: Optional[str] = None,
) -> bytes:
    """Generate 3W1H report: All delayed items with context (project + milestone + task level)."""
    from app.services.mpcp_tracker_service import _milestones, _milestone_tasks, _rag_context_entries

    wb = Workbook()
    ws = wb.active
    ws.title = "3W1H Report"
    _write_headers(ws, [
        "Level", "Project", "MP / CP", "Item", "Delay (days)", "RAG",
        "What", "Why", "Who", "Owner/Team", "How", "ETA", "Status",
    ])

    cp_map = {cp.id: cp for cp in cps}
    mp_map = {mp.id: mp for mp in mps}

    for p in projects:
        if rag_filter == "Yellow" and p.rag_status != RAGStatus.YELLOW:
            continue
        if rag_filter == "Red" and p.rag_status != RAGStatus.RED:
            continue

        cp = cp_map.get(p.parent_cp_id)
        mp = mp_map.get(cp.parent_mp_id) if cp else None
        mp_cp_label = f"{mp.code} › {cp.code}" if mp and cp else (cp.code if cp else "")

        # Project-level RAG context (old format - single object)
        if p.rag_status in (RAGStatus.YELLOW, RAGStatus.RED) and p.rag_context:
            ctx = p.rag_context
            row_idx = ws.max_row + 1
            ws.append([
                "Project", p.name, mp_cp_label, "-", "-",
                p.rag_status.value,
                ctx.what or "", ctx.why or "", ctx.who or "",
                ctx.owner_team or "", ctx.how or "",
                str(ctx.eta) if ctx.eta else "", "Open",
            ])
            _apply_rag_fill(ws.cell(row=row_idx, column=6), p.rag_status.value)

        # Milestone-level 3W1H entries
        ms_list = _milestones.get(p.id, [])
        for m in ms_list:
            entries = _rag_context_entries.get(m.id, [])
            for entry in entries:
                row_idx = ws.max_row + 1
                ws.append([
                    "Milestone", p.name, mp_cp_label, m.name,
                    m.slippage_days or "-", m.rag_status.value,
                    entry.what or "", entry.why or "", entry.who or "",
                    entry.owner_team or "", entry.how or "",
                    str(entry.eta) if entry.eta else "", entry.status or "Open",
                ])
                _apply_rag_fill(ws.cell(row=row_idx, column=6), m.rag_status.value)

            # Task-level 3W1H entries
            tasks = _milestone_tasks.get(m.id, [])
            for t in tasks:
                t_entries = _rag_context_entries.get(t.id, [])
                for entry in t_entries:
                    row_idx = ws.max_row + 1
                    ws.append([
                        "Task", p.name, mp_cp_label, f"{m.name} → {t.name}",
                        t.slippage_days or "-", t.rag_status.value,
                        entry.what or "", entry.why or "", entry.who or "",
                        entry.owner_team or "", entry.how or "",
                        str(entry.eta) if entry.eta else "", entry.status or "Open",
                    ])
                    _apply_rag_fill(ws.cell(row=row_idx, column=6), t.rag_status.value)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def get_export_filename() -> str:
    """Generate filename with current date."""
    return f"MPCP_Tracker_Report_{date.today().isoformat()}.xlsx"


def get_3w1h_filename() -> str:
    """Generate 3W1H report filename."""
    return f"MPCP_3W1H_Report_{date.today().isoformat()}.xlsx"
