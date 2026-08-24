# Implementation Plan

## Overview

MPCP Project Tracker module for TVS PlanIQ — hierarchical project tracking with MP → CP → Project drill-down, process/execution tracks, RAG status, dependencies, budget, and reporting.

## Tasks

- [x] 1. Pydantic models (`app/models/mpcp_schemas.py`) — All enums, core models, request/response schemas, UOM/target fields
- [x] 2. SharePoint storage (`app/services/sharepoint_client.py`) — FY-based folders (`ProjectTracker/2026_27/`), auto-init on startup
- [x] 3. MPCP tracker service (`app/services/mpcp_tracker_service.py`) — Full CRUD, process track, stage validation, delete guards
- [x] 4. RAG engine (`app/services/rag_engine.py`) — 3W1H validation, worst-child-wins propagation, history logging
- [x] 5. Execution track engine (`app/services/execution_track_engine.py`) — Slippage calc, totals, fast-track, Gantt time axis
- [x] 6. Dependencies service (`app/services/mpcp_dependencies_service.py`) — CRUD, overdue detection, escalation
- [x] 7. Budget service (`app/services/mpcp_budget_service.py`) — Auto-compute remaining/variance, over-budget flagging
- [x] 8. Dashboard calculator (`app/services/mpcp_dashboard_calculator.py`) — Aggregation, filters, critical items, open deps
- [x] 9. FastAPI router (`app/routers/mpcp_tracker.py`) — 41 REST endpoints registered
- [x] 10. Router registration (`main.py`) — Included in app, SharePoint init updated
- [x] 11. Sidebar + routing (`static/index.html`) — MPCP Tracker sidebar entry, hash routing, page container
- [x] 12. Dashboard view (`static/mpcp-tracker.js`) — Metrics, BU switcher, by-vendor/PO tables, download buttons
- [x] 13. MP List + CP List views — Tables with RAG, edit buttons, + Add MP/CP modals
- [x] 14. All Projects view — Flat view with search/filter, + Add Project with CP picker
- [x] 15. Process Track tab — 8-stage stepper (clickable), stage update modal
- [x] 16. Execution Track tab — CSS Gantt, milestone table, slippage summary, + Add Milestone
- [x] 17. Dependencies tab — Table with overdue indicators, + Add Dependency modal
- [x] 18. Budget tab — Metric cards, utilization bar, Edit Budget modal
- [x] 19. RAG Update modal (3W1H) — Radio + conditional fields for project/milestone
- [x] 20. CRUD modals — Create/Edit MP, CP, Project with Delete confirmation
- [x] 21. Excel export (`app/services/mpcp_export_service.py`) — Portfolio report (5 sheets), 3W1H report
- [x] 22. Milestone bulk upload — Excel parsing, row validation, error reporting
- [x] 23. Hierarchy bulk upload + template — Download template, upload to create MPs/CPs/Projects
- [x] 24. Weekly email report (`app/services/mpcp_report_service.py`) — HTML template, Graph API sendMail
- [x] 25. Wire audit logging into every CRUD operation
- [x] 26. Access control enforcement (Admin vs User role)
- [x] 27. CP to Projects navigation fix
- [x] 28. Milestone edit/delete UI buttons in execution track rows

## Task Dependency Graph

```json
{
  "waves": [
    {
      "name": "Phase 1: Backend Foundation",
      "tasks": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    },
    {
      "name": "Phase 2: Frontend",
      "tasks": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    },
    {
      "name": "Phase 3: Export and Reports",
      "tasks": [21, 22, 23, 24]
    },
    {
      "name": "Phase 4: Polish",
      "tasks": [25, 26, 27, 28]
    }
  ]
}
```

## Notes

- 41 API endpoints under `/api/mpcp-tracker/`
- Financial year folders: `ProjectTracker/2026_27/MPCPTracker.xlsx` auto-creates on April 1
- In-memory caching: Hierarchy loaded once from SharePoint, mutations persist back immediately
- UOM/Target fields added to MP and CP models after business MPCP deck review
- Pre-built data file: `~/Downloads/MPCP_Hierarchy_2W_CMB_FY27.xlsx` with 17 MPs + 41 CPs
