# TVS PlanIQ — Architecture & Design Document

## 1. Product Overview

TVS PlanIQ is an AI-powered effort estimation tool that uses a Small Language Model (SLM) + deterministic graph-based calculation to produce accurate project effort, cost, and timeline estimates from BRD/PRD documents.

### Key Capabilities
- **Catalog-Based Estimation** — SLM classifies work items from a fixed catalog; app does all math
- **Graph Augmentation** — System dependency graph auto-detects cross-domain scope, missing integrations
- **Cloud Cost Estimation** — Maps systems to Azure resources with monthly cost breakdown
- **Phase-Wise Estimation** — Detects phases from PRD and estimates each independently
- **Build vs Buy Evaluation** — Multi-criteria scoring for build/buy/partner decisions
- **PRD Completeness Checker** — Validates document readiness against org templates
- **Vendor Comparison** — Compares vendor proposals against internal estimates
- **Multi-Discipline Rate Card** — Per-discipline costing with system-specific overrides

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (static/index.html)               │
│   Dashboard │ New Estimation │ Results │ BvB │ Vendor │ Admin    │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API
┌─────────────────────────────▼───────────────────────────────────┐
│                     FastAPI Backend (main.py)                     │
│  Routers: estimations │ admin_config │ build_vs_buy │ prd_check  │
│  Middleware: auth │ rate_limiter │ error_handler                  │
└──────┬──────────┬──────────┬──────────┬─────────────────────────┘
       │          │          │          │
┌──────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼──────────┐
│ SLM      │ │ Graph  │ │ Cloud  │ │ SharePoint   │
│ (Ollama) │ │ Engine │ │ Cost   │ │ (Data Store) │
│ gemma3:4b│ │        │ │ Calc   │ │              │
└──────────┘ └────────┘ └────────┘ └──────────────┘
```

## 3. Estimation Pipeline

```
Upload BRD/PRD
    → Text Extraction (DOCX/PDF/MD)
    → Tier Classification (0=BRD only, 1=+PRD, 2=+HLD, 3=+Deps)
    → Phase Detection (regex-based from PRD headings)
    → SLM Classification (3 calls):
        Call 1: System Identification (targetSystems, scopeType, overheadFlags)
        Call 2: Work Item Classification (chunked for long PRDs)
        Call 3: Integration & Risk Analysis
    → Graph Augmentation:
        - Add missing dependent systems (ALWAYS_INVOLVED_RULES + hub detection)
        - Detect cross-domain (CP ↔ D2C) from graph topology
        - Add missing integration work items (capped at 8)
    → Catalog Calculator (deterministic math):
        1. Base effort (unit × complexity × quantity × system_multiplier)
        2. Integration pattern surcharges
        3. Hub system surcharges
        4. Overhead multiplier (team, cross-domain, tech familiarity, data volume, security, legacy)
        5. Scope factor (New Application ×2.5, New Module ×1.8, etc.)
        6. Documentation overhead (+5%)
        7. AI productivity multiplier (×0.8 global, per-category overrides)
        8. Distribution auto-correction (bump under-represented disciplines)
        9. Confidence band (HIGH ±10%, MEDIUM ±25%, LOW ±40%)
        10. Sanity checks
    → Cloud Cost Calculation (Azure resource mapping)
    → Discipline Scaling (breakdown matches total)
    → Cost Calculation (per-discipline rates from Config.xlsx)
    → Timeline Calculation
    → Result Assembly + SharePoint Write
    → Background: Scope Analysis + Doc Readiness (async enrichment)
```

## 4. Data Architecture

### Config Files (local, shipped with app)
| File | Purpose |
|------|---------|
| `config/estimation_catalog.json` | 81 work units, multipliers, overheads, AI factors, distribution rules |
| `config/system_dependencies.json` | 44 systems, 74 integration links, 6 hubs, critical paths |
| `config/estimation_blueprint.md` | SLM prompt context (principles, registry, triggers) |
| `config/doc_templates.json` | BRD/PRD section templates for readiness scoring |

### SharePoint (runtime data)
| File | Purpose |
|------|---------|
| `EstimationIndex.xlsx` | Lightweight index of all estimations (dashboard listing) |
| `Estimations_YYYY-MM.xlsx` | Monthly detailed estimation data (25 columns) |
| `AuditLog_YYYY-MM.xlsx` | Monthly audit trail |
| `Config.xlsx` | Admin-editable config (rate card, SLM settings) |

### In-Memory (ephemeral)
| Store | Purpose |
|-------|---------|
| `_job_store` | Background estimation jobs (30-min TTL) |
| `_enrichment_store` | Async scope/doc readiness results |
| Config/catalog caches | 5-min TTL for hot config |

## 5. Key Services

| Service | File | Responsibility |
|---------|------|----------------|
| Estimation Engine | `estimation_engine.py` | Orchestrates full pipeline |
| Catalog Classifier | `catalog_classifier.py` | 3-call SLM classification |
| Catalog Calculator | `catalog_calculator.py` | Deterministic math (all effort calculation) |
| Graph Augmenter | `graph_augmentation.py` | Post-SLM graph enrichment |
| Cloud Cost Calculator | `cloud_cost_calculator.py` | Azure resource cost estimation |
| Catalog Loader | `catalog_loader.py` | Config loading with TTL cache |
| Scope Analyzer | `scope_analyzer.py` | PRD scope item extraction |
| Document Readiness | `document_readiness.py` | BRD/PRD completeness scoring |
| Cost Calculator | `cost_calculator.py` | Per-discipline cost from rate card |
| Timeline Calculator | `timeline_calculator.py` | Duration + scenario modeling |
| Phase Detector | `phase_detector.py` | Regex-based phase extraction |
| SLM Engine | `slm_engine.py` | Ollama/OpenRouter inference abstraction |
| SharePoint Client | `sharepoint_client.py` | Graph API for Excel read/write |
| BvB Evaluation | `bvb_evaluation_service.py` | Build vs Buy scoring |

## 6. API Endpoints

### Estimation
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/estimations/upload` | Submit BRD/PRD for estimation (background job) |
| GET | `/api/estimations/jobs` | List active/recent jobs |
| GET | `/api/estimations/jobs/{id}` | Poll job status |
| GET | `/api/estimations` | Dashboard listing |
| GET | `/api/estimations/{id}` | Full estimation detail |
| GET | `/api/estimations/{id}/enrichment` | Poll async scope/doc readiness |
| GET | `/api/estimations/{id}/audit` | Audit history |
| POST | `/api/estimations/{id}/re-estimate` | Re-estimate with changes |
| POST | `/api/estimations/{id}/scenarios` | Scenario modeling |
| GET/POST | `/api/estimations/{id}/export/*` | PDF/JSON export |

### Admin
| Method | Path | Description |
|--------|------|-------------|
| GET/PUT | `/api/admin/config` | Read/update Config.xlsx |
| GET/POST/DELETE | `/api/admin/templates` | Manage base templates |

### Other Modules
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/prd-check` | PRD completeness check |
| POST | `/api/build-vs-buy/*` | Build vs Buy evaluation |
| POST | `/api/estimations/{id}/vendor-compare` | Vendor comparison |

## 7. Deployment

### Local Development
```bash
set -a && source .env.dev && set +a
OLLAMA_NUM_PARALLEL=2 ollama serve  # In separate terminal
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Production (Docker + Azure)
```bash
docker build -t planiq:latest .
docker run --env-file .env.prod -p 8000:8000 planiq:latest
```

Secrets via Azure Key Vault references in App Service config.

## 8. Key Design Decisions

1. **SLM classifies, app calculates** — Removes LLM randomness from effort numbers
2. **Graph augments, never removes** — SLM output preserved, graph only adds missing items
3. **Distribution auto-correction** — Top-down validation catches systematic SLM blind spots
4. **Async enrichment** — Scope/doc quality don't block main estimation (background task)
5. **Positional fallback for SharePoint columns** — Backward-compatible with pre-existing files
6. **System discipline overrides** — Accurate rate card application per target system
7. **Cloud cost from topology** — No SLM call needed; purely deterministic from graph + categories


## 9. MPCP Project Tracker Module

### Overview
Full-lifecycle project tracking for Managing Points (MP) → Check Points (CP) → Projects hierarchy. Tracks execution milestones, tasks, budget, dependencies, process stages, and RAG status with 3W1H accountability.

### Data Model (Hierarchy)
```
MP (Managing Point)
 └── CP (Check Point)
      └── Project
           ├── Process Track (8 SOP stages: BRD → PRD → RFP → PO → Kickoff → Execution → Prod → Success)
           ├── Execution Track
           │    └── Milestones (11 auto-created SDLC phases)
           │         └── Tasks (user-defined work items)
           ├── Dependencies (project-level or milestone-linked)
           ├── Budget (ledger: PO_Issued, Change_Request, Spend, Refund)
           └── RAG Status (auto-propagates upward: Task → Milestone → Project → CP → MP)
```

### RAG & 3W1H System
- **Auto-detection**: When `actual_end > planned_end` → RAG = Red, 3W1H mandatory
- **Multiple entries**: Each task/milestone can have multiple parallel 3W1H issues (stored in RAGContextEntries sheet)
- **Propagation chain**: Task → Milestone → Project → CP → MP (worst-case bubbles up)
- **3W1H fields**: What, Why, Who, Owner/Team, How, ETA, Status (Open/Resolved)
- **Enforcement**: Cannot save a delayed task without providing 3W1H on first detection

### Milestone Date Inference
When tasks are updated under a milestone, the system auto-infers milestone dates:
- `milestone.planned_start` = min(tasks.planned_start)
- `milestone.planned_end` = max(tasks.planned_end)
- `milestone.actual_start` = min(tasks.actual_start)
- `milestone.actual_end` = max(tasks.actual_end)

### SharePoint Storage
All data in `ProjectTracker/{FY}/MPCPTracker.xlsx` with sheets:

| Sheet | Purpose |
|-------|---------|
| ManagingPoints | MPs with theme, owner, BU, RAG |
| CheckPoints | CPs linked to parent MP |
| Projects | Projects linked to parent CP |
| ProcessTracks | 8-stage SOP lifecycle per project |
| ExecutionMilestones | SDLC milestones with plan/actual dates |
| MilestoneTasks | Tasks under milestones with plan/actual dates |
| RAGContextEntries | 3W1H entries (multiple per entity) |
| Dependencies | Project/milestone dependencies with owner, ETA, status |
| Budget | Transaction ledger (PO_Issued, CR, Spend, Refund) |
| RAGHistory | RAG change audit trail |
| Config | Configurable vendors, POs, EMs |

### Financial Year
- Indian FY: April to March (e.g., "2026_27" = Apr 2026 - Mar 2027)
- Auto-detected from current date
- Separate workbook per FY
- FY switcher in UI for historical access

### Budget Lifecycle
```
Approved Budget (sanctioned amount)
  → PO_Issued transactions (committed to vendors)
  → Change_Request (additional commitment)
  → Remaining = Approved - Total Committed
  → Utilization % = Total Committed / Approved × 100
```

### Export Reports (Excel)
Per-project download with 4 sheets:
1. **Execution Plan** — Milestones + tasks with dates, delay, RAG, remarks
2. **Delay Report** — All 3W1H entries for delayed items
3. **Dependencies** — All dependencies with owner, ETA, status, overdue flag
4. **Gantt** — Horizontal cell-colored timeline (Plan row + Actual row per item)

Dashboard-level reports:
- **Portfolio Report** — All projects across MPs/CPs with RAG summary
- **3W1H Report** — Consolidated delay report across all projects (Task/Milestone/Project level)

### Key API Endpoints (48+)
| Group | Endpoints |
|-------|-----------|
| MPs | CRUD, list |
| CPs | CRUD under MP |
| Projects | CRUD under CP, list all |
| Process Track | Get/update stages (sequential validation) |
| Execution Track | Get milestones, CRUD tasks |
| Dependencies | CRUD (project or milestone level) |
| Budget | Get/update, add transactions |
| RAG | Update status, get history |
| Export | Portfolio report, 3W1H report, execution plan, Gantt |
| Config | Get/update vendors, POs, EMs |
| FY | Switch financial year |

### Frontend (SPA)
Single-page app in `static/mpcp-tracker.js`:
- Dashboard with RAG summary cards + BU filter
- MP → CP → Project drill-down
- Execution Track with collapsible milestones, task tables
- CSS Gantt chart (dual-row: Planned + Actual per item)
- Process Track stepper (sequential validation)
- Dependencies tab with milestone linking
- Budget tab with transaction ledger + utilization bar
- Settings page (configurable vendors, POs, EMs)

## 10. Infrastructure Requirements

### Minimum (CPU-only, no GPU)
| Resource | Spec |
|----------|------|
| CPU | 8 vCPUs |
| RAM | 16 GB |
| Disk | 40 GB SSD |
| OS | Ubuntu 22.04 LTS |
| External | SharePoint API access, Ollama (local) |

### With GPU (faster AI estimation)
| Resource | Spec |
|----------|------|
| CPU | 4 vCPUs |
| RAM | 16 GB |
| GPU | NVIDIA T4 (16 GB VRAM) |
| Disk | 50 GB SSD |

### Without Local SLM (API-only mode)
| Resource | Spec |
|----------|------|
| CPU | 2 vCPUs |
| RAM | 4 GB |
| Disk | 20 GB SSD |
| External | OpenRouter/Azure OpenAI API key |
