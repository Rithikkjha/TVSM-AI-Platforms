# Requirements: Graph Augmentation & Platform Enhancements

## 1. Graph-Augmented Classification

### REQ-GA-1: Post-SLM Graph Augmentation Layer
The system shall apply a deterministic graph augmentation layer after SLM classification to enrich the estimation with dependency graph knowledge.

### REQ-GA-2: Cross-Domain Detection from Graph
The system shall detect cross-domain scope (CP ↔ D2C) from the system dependency graph topology, not from SLM inference.

### REQ-GA-3: Missing System Detection
The system shall auto-detect and add dependent systems that the SLM missed, based on:
- Architecture invariant rules (e.g., "DMS always involves IDP")
- Hub system detection (if 3+ systems are involved, add connecting hubs)
- Critical path chain analysis (add intermediate systems on known chains)

### REQ-GA-4: Integration Work Item Auto-Addition
The system shall automatically add integration work items (INT-*) for known integration links between target systems, capped at 8 items per estimation.

### REQ-GA-5: Cross-Domain Overhead Calculation
The system shall calculate graduated cross-domain overhead from the graph's crossDomainOverhead table, capped at 60%.

### REQ-GA-6: Single-System Protection
The system shall NOT apply aggressive augmentation for single-system simple changes (Bug Fix, Enhancement with 1 system).

## 2. Cloud Cost Estimation

### REQ-CC-1: Azure Resource Mapping
The system shall estimate monthly Azure cloud infrastructure costs by mapping work item categories and target systems to Azure resource types.

### REQ-CC-2: System-Specific Resources
The system shall add system-specific Azure resources (e.g., IoT Hub for TVS Connect, Cosmos DB for P360, Service Bus Premium for CNS).

### REQ-CC-3: Deployment Multiplier
The system shall apply deployment topology multipliers (multi-region, IB countrywise) to cloud costs based on system deployment models.

### REQ-CC-4: Dual Scenario Display
The system shall display cloud costs in two scenarios: "If New Provisioning" (full cost) and "If Using Existing Infra" (incremental only).

## 3. Distribution Auto-Correction

### REQ-DC-1: Top-Down Distribution Validation
The system shall validate discipline proportions against expected ranges defined per scope type (New Application, New Feature, Enhancement, etc.).

### REQ-DC-2: Auto-Correction
When a discipline is below the minimum expected percentage, the system shall automatically bump it to the expected level and add the gap to the total estimate.

### REQ-DC-3: Correction Transparency
The system shall display distribution corrections in Sanity Warnings with the exact adjustment details.

## 4. Multi-Discipline Rate Card

### REQ-RC-1: System Discipline Overrides
The system shall map work items from specific systems to specialized disciplines (e.g., TVS Connect → P360 Telematics, MDP → Data Engineering) for accurate rate card application.

### REQ-RC-2: QA/DevOps Non-Override
QA and DevOps work items shall always stay in their own discipline regardless of target system.

## 5. In-Progress Jobs Dashboard

### REQ-JP-1: Active Jobs API
The system shall provide GET /api/estimations/jobs endpoint listing all active/recent estimation jobs.

### REQ-JP-2: Dashboard Banner
The dashboard shall display an auto-refreshing banner showing all in-progress estimations with project name and elapsed time.

### REQ-JP-3: Auto-Polling
The dashboard shall poll for active jobs every 10 seconds when visible.

## 6. Async Enrichment (Scope + Doc Quality)

### REQ-AE-1: Background Processing
Scope analysis and document readiness shall run as background tasks after the main estimation completes.

### REQ-AE-2: Enrichment Polling
The frontend shall poll GET /api/estimations/{id}/enrichment every 5 seconds until enrichment completes or times out.

### REQ-AE-3: In-Place Update
When enrichment completes, the Scope Coverage and Doc Quality tabs shall update in-place without resetting the current tab.

## 7. UI Enhancements

### REQ-UI-1: Pagination
Dashboard and Audit Log tables shall paginate at 10 rows per page with Prev/Next navigation.

### REQ-UI-2: Sort Order
Dashboard shall default to newest-first sorting.

### REQ-UI-3: Month Filter Fix
Month filter shall parse dates robustly (handles ISO, locale strings, etc.).

### REQ-UI-4: Scenario Modeling (Live Sliders)
Timeline sliders shall update duration and timeline bars in real-time without API calls.

### REQ-UI-5: Cost Without AI
Total Cost card shall show "(without AI: ₹XXL)" alongside the AI-adjusted cost.

### REQ-UI-6: Tab Reset on Navigation
Navigating to a new estimation result shall always reset to the Overview tab.

### REQ-UI-7: Filename Labels
Result pills shall display uploaded BRD/PRD filenames when available.

## 8. Data Persistence

### REQ-DP-1: Extended SharePoint Storage
Monthly estimation files shall store CatalogBreakdownJSON, InfraCostJSON, and DocumentReadinessJSON as additional columns.

### REQ-DP-2: Backward-Compatible Loading
The load function shall use positional fallback for new columns when headers are missing (pre-existing monthly files).

### REQ-DP-3: Discipline Scaling
The discipline breakdown shall be proportionally scaled to match the pointEstimate total (includes all multipliers and surcharges).

## 9. Performance & Reliability

### REQ-PR-1: Ollama Parallel Inference
Production deployment shall use OLLAMA_NUM_PARALLEL=2 for concurrent request handling.

### REQ-PR-2: Rate Limiter Exclusions
Polling endpoints (/jobs, /enrichment) shall be excluded from rate limiting.

### REQ-PR-3: Frontend Polling Timeout
Frontend shall poll job status for up to 15 minutes before timing out.
