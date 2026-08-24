# Design Document

## Overview

This design replaces the current "LLM invents numbers" estimation engine with a catalog-based architecture where the SLM only classifies work items and the application performs deterministic math. The system uses two config files (`estimation_catalog.json` + `system_dependencies.json`) as the single source of truth for all calculations, and a markdown file (`estimation_blueprint.md`) as the LLM prompt context.

The chunked 3-call SLM strategy ensures gemma3:4b produces reliable classifications by keeping each prompt focused and under 8K tokens.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ESTIMATION PIPELINE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌─────────────────────┐    ┌───────────────────┐  │
│  │ PRD Text │───▶│ CHUNKED CLASSIFIER  │───▶│ CATALOG CALCULATOR│  │
│  │ (Upload) │    │ (3 SLM Calls)       │    │ (Pure Math)       │  │
│  └──────────┘    └─────────┬───────────┘    └────────┬──────────┘  │
│                            │                          │              │
│                   ┌────────▼────────┐       ┌────────▼────────┐    │
│                   │ config/         │       │ config/          │    │
│                   │ estimation_     │       │ estimation_      │    │
│                   │ blueprint.md    │       │ catalog.json     │    │
│                   │ (LLM context)   │       │ (effort values)  │    │
│                   └─────────────────┘       └─────────────────┘    │
│                                                      │              │
│                                             ┌────────▼────────┐    │
│                                             │ config/          │    │
│                                             │ system_          │    │
│                                             │ dependencies.json│    │
│                                             │ (graph + hubs)   │    │
│                                             └─────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Config Files (`config/`)

#### 1.1 `config/estimation_catalog.json`

Structure:

```json
{
  "version": "3.0",
  "lastUpdated": "2026-07-03T00:00:00Z",
  "effortTable": {
    "FE-01": {"simple": 0.5, "medium": 1.0, "complex": 2.0},
    "FE-02": {"simple": 1.0, "medium": 2.0, "complex": 3.5},
    "...": "all 81 units from §6 of blueprint v3"
  },
  "systemMultipliers": {
    "DMS": 1.5,
    "DigiApp": 1.3,
    "POMS": 1.4,
    "TruChamp": 1.2,
    "IDP": 1.6,
    "CPS": 1.1,
    "...": "all systems from §7"
  },
  "overheadFactors": {
    "teamSize": {"1-2": 1.0, "3-5": 1.1, "6-10": 1.2, "11+": 1.35},
    "crossDomain": 1.2,
    "multiVendor": 1.25,
    "distributedTeam": 1.15,
    "techFamiliarity": {"proficient": 1.0, "learning": 1.25, "unfamiliar": 1.5},
    "dataVolume": {"<1K": 1.0, "1K-10K": 1.05, "10K-100K": 1.15, "100K-1M": 1.3, ">1M": 1.5},
    "deploymentTopology": {"single_region": 1.0, "multi_region_2_3": 1.2, "multi_country_4_10": 1.35, "multi_country_10+": 1.5, "hybrid": 1.3, "on_prem": 1.15},
    "security": {"standard": 1.0, "pii": 1.15, "payment": 1.2, "pii_and_payment": 1.3},
    "legacyDebt": {"modern": 1.0, "moderate": 1.15, "heavy": 1.3}
  },
  "integrationPatternCosts": {
    "REST_EXISTING": 0,
    "REST_NEW": 0,
    "SERVICE_BUS_NEW_TOPIC": 1.5,
    "SERVICE_BUS_NEW_SUBSCRIBER": 1.0,
    "SAP_RFC": 2.0,
    "SAP_IDOC": 2.5,
    "BATCH_FILE": 1.0,
    "WEBHOOK": 0.5,
    "GRPC": 1.5,
    "GRAPHQL": 1.0
  },
  "hubSurcharges": {
    "MDP": 3.0,
    "IDP": 2.5,
    "UMS": 2.5,
    "CNS": 2.0,
    "Booking Service": 2.0
  },
  "documentationOverhead": 0.05,
  "aiProductivity": {
    "globalMultiplier": 1.0,
    "perCategory": {
      "frontend": null,
      "backendCrud": null,
      "backendLogic": null,
      "integration": null,
      "qa": null,
      "devops": null,
      "sap": null
    }
  },
  "sanityChecks": {
    "minEffort": {"New Feature": 10, "Enhancement": 3, "Bug Fix": 0.5, "Integration": 5, "Migration": 15},
    "maxEffort": {"Enhancement": 60, "Bug Fix": 20}
  },
  "disciplineMapping": {
    "FE": "Digital Engineering",
    "BE": "Digital Engineering",
    "INT": "Digital Engineering",
    "QA": "QA/Testing",
    "DO": "DevOps"
  }
}
```

#### 1.2 `config/system_dependencies.json`

Structure:

```json
{
  "version": "1.0",
  "lastUpdated": "2026-07-03T00:00:00Z",
  "systems": {
    "DMS": {
      "domain": "CP",
      "domainTag": "cp.dealer.sales-service-parts",
      "techStack": ".NET, Angular, SQL Server",
      "deploymentModel": "Azure (IB countrywise)",
      "isHub": false,
      "integrationDensity": "High"
    },
    "MDP": {
      "domain": "D2C",
      "domainTag": "d2c.platform.master-data",
      "techStack": "Java/Spring Boot",
      "deploymentModel": "Azure",
      "isHub": true,
      "integrationDensity": "Critical"
    }
  },
  "hubSystems": ["MDP", "IDP", "UMS", "CNS", "Booking Service"],
  "integrationLinks": [
    {"source": "Lead Service", "target": "EMS", "pattern": "REST_API", "criticality": "critical", "domain": "D2C_to_CP"},
    {"source": "Booking Service", "target": "DMS", "pattern": "SERVICE_BUS", "criticality": "critical", "domain": "D2C_to_CP"},
    {"source": "MDP", "target": "DMS", "pattern": "SERVICE_BUS_BATCH", "criticality": "critical", "domain": "D2C_to_CP"}
  ],
  "crossDomainOverhead": {
    "D2C_to_CP": 0.20,
    "any_to_SAP": 0.30,
    "any_to_notification": 0.10,
    "any_to_MDP": 0.25,
    "any_to_UMS": 0.15,
    "any_to_IDP": 0.20,
    "any_to_thirdParty": 0.25
  },
  "criticalPathChains": [
    {"name": "Full Purchase", "hops": 8, "systems": ["tvsmotor.com", "Catalog", "MDP", "Lead Service", "EMS", "DMS", "SAP", "DWR", "TVS Connect"]},
    {"name": "Parts Fulfillment", "hops": 6, "systems": ["DigiApp", "POMS", "SAP", "IDP", "DMS", "TruChamp", "CNS"]},
    {"name": "Dealer Onboarding", "hops": 7, "systems": ["KYC Dealer", "Verifier", "KYC Auditor", "SAP", "MDP", "UMS", "DMS", "Dealer Locator"]}
  ]
}
```

#### 1.3 `config/estimation_blueprint.md`

Contains Part A (§1 through §5) of the bottom-up blueprint v3 — the content that goes into LLM prompts. This is the human-readable source that admin can edit. The engine reads specific sections from it to construct prompts.

### 2. Chunked Classifier Service (`app/services/catalog_classifier.py`)

New service replacing the old prompt-based estimation. Handles the 3-call SLM strategy.

```python
class CatalogClassifier:
    """Orchestrates chunked SLM classification of PRD into catalog work items."""
    
    async def classify(self, prd_text: str, request: EstimationRequest) -> ClassificationResult:
        """Run 3-call classification pipeline."""
        
    async def _call1_identify_systems(self, prd_summary: str) -> SystemIdentification:
        """Call 1: Identify target systems, scope type, overhead flags."""
        
    async def _call2_classify_work_items(self, prd_text: str, systems: list[str]) -> list[WorkItem]:
        """Call 2: Classify PRD into atomic work units. Chunks if >8K chars."""
        
    async def _call3_integration_risks(self, prd_summary: str, systems: list[str]) -> IntegrationAnalysis:
        """Call 3: Identify integration patterns, assumptions, risks."""
        
    def _merge_chunked_results(self, chunks: list[list[WorkItem]]) -> list[WorkItem]:
        """Merge work items from multiple chunks, dedup by unitId+system."""
        
    def _build_call1_prompt(self, prd_summary: str) -> str:
        """Build prompt for system identification (includes §3 registry)."""
        
    def _build_call2_prompt(self, prd_chunk: str, systems: list[str]) -> str:
        """Build prompt for work item classification (includes §1, §2, §4)."""
        
    def _build_call3_prompt(self, prd_summary: str, systems: list[str]) -> str:
        """Build prompt for integration/risk analysis."""
```

#### Call 1 Prompt Template (~2K tokens):

```
You are a system analyst for TVS Motor Company.
Read this requirement and identify which systems are impacted.

[System Registry from §3 — names and domain tags only]

PRD Summary:
{first 4000 chars of PRD}

Return JSON:
{"targetSystems": [...], "scopeType": "...", "overheadFlags": {...}}
```

#### Call 2 Prompt Template (~6K tokens):

```
You are a software effort classifier.
{§1 Estimation Principles}

Work Unit Catalog:
{§2 — unit IDs, names, descriptions only}

Trigger Phrases:
{§4 — mapping table}

PRD Section:
{6000 char chunk}

Target Systems (already identified): {systems from Call 1}

Return JSON:
{"workItems": [{"unitId": "...", "complexity": "...", "quantity": N, "system": "...", "reason": "..."}]}
```

#### Call 3 Prompt Template (~2K tokens):

```
You are an integration analyst for TVS Motor Company.
Systems identified: {targetSystems}
Integration patterns available: REST_EXISTING, REST_NEW, SERVICE_BUS_NEW_TOPIC, SERVICE_BUS_NEW_SUBSCRIBER, SAP_RFC, SAP_IDOC, BATCH_FILE, WEBHOOK, GRPC, GRAPHQL

PRD Summary:
{first 3000 chars}

Return JSON:
{"integrationPatterns": [...], "assumptions": [...], "risks": [...]}
```

### 3. Catalog Calculator Service (`app/services/catalog_calculator.py`)

Pure math — no SLM, no async, fully deterministic.

```python
class CatalogCalculator:
    """Deterministic effort calculation from classification + catalog data."""
    
    def __init__(self, catalog: EstimationCatalog, dependencies: SystemDependencies):
        self.catalog = catalog
        self.dependencies = dependencies
    
    def calculate(self, classification: ClassificationResult) -> CalculationResult:
        """Run full calculation pipeline. Same input → same output always."""
        
    def _calculate_base_effort(self, work_items: list[WorkItem]) -> float:
        """Sum(effort[unitId][complexity] * quantity * systemMultiplier)."""
        
    def _calculate_pattern_surcharges(self, patterns: list[str]) -> float:
        """Sum pattern costs from catalog."""
        
    def _calculate_hub_surcharges(self, systems: list[str]) -> float:
        """Sum hub surcharges for hub systems in target list."""
        
    def _calculate_overhead_multiplier(self, flags: OverheadFlags) -> float:
        """Compound all overhead factors."""
        
    def _apply_ai_multiplier(self, effort: float, work_items: list[WorkItem]) -> float:
        """Apply global or per-category AI multiplier."""
        
    def _calculate_confidence_band(self, effort: float, assumptions: list, risks: list) -> ConfidenceBand:
        """Determine HIGH/MEDIUM/LOW and calculate range."""
        
    def _run_sanity_checks(self, effort: float, scope_type: str, classification: ClassificationResult) -> list[str]:
        """Return list of warning messages if sanity checks fail."""
        
    def _map_to_disciplines(self, work_items: list[WorkItem]) -> list[DisciplineEffort]:
        """Map FE/BE/INT → Digital Engineering, QA → QA/Testing, DO → DevOps."""
```

### 4. Catalog Loader (`app/services/catalog_loader.py`)

Handles loading and caching of config files.

```python
class CatalogLoader:
    """Loads and caches estimation catalog and system dependencies."""
    
    CACHE_TTL = 300  # 5 minutes
    
    def load_catalog(self) -> EstimationCatalog:
        """Load config/estimation_catalog.json with TTL cache."""
        
    def load_dependencies(self) -> SystemDependencies:
        """Load config/system_dependencies.json with TTL cache."""
        
    def load_blueprint_section(self, section: str) -> str:
        """Load specific section from config/estimation_blueprint.md."""
        
    def invalidate_cache(self):
        """Force reload on next access."""
```

### 5. Updated Estimation Engine (`app/services/estimation_engine.py`)

The existing `generate_estimation()` function is refactored to use the new components:

```python
async def generate_estimation(request, input_tier, slm_engine, sharepoint_client):
    # Step 1: Validate (unchanged)
    await validate_request(request)
    
    # Step 2: Load catalog + dependencies
    loader = CatalogLoader()
    catalog = loader.load_catalog()
    dependencies = loader.load_dependencies()
    
    # Step 3: Phase detection (unchanged)
    phase_result = detect_phases(request.documents.prd.textContent)
    
    # Step 4: Classification via chunked SLM calls
    classifier = CatalogClassifier(slm_engine, loader)
    
    if phase_result.phases:
        # Per-phase classification
        phase_classifications = []
        for phase in phase_result.phases:
            phase_text = _extract_phase_text(request, phase)
            classification = await classifier.classify(phase_text, request)
            phase_classifications.append((phase, classification))
    else:
        # Single classification for entire PRD
        prd_text = request.documents.prd.textContent
        if request.documents.brd:
            prd_text = request.documents.brd.textContent + "\n\n" + prd_text
        classification = await classifier.classify(prd_text, request)
    
    # Step 5: Deterministic calculation
    calculator = CatalogCalculator(catalog, dependencies)
    
    if phase_result.phases:
        # Per-phase calculation
        phases_list = []
        for phase, cls in phase_classifications:
            result = calculator.calculate(cls)
            phases_list.append(_build_phase_estimation(phase, result))
        # Aggregate top-level from phases
        total_result = _aggregate_phase_results(phases_list)
    else:
        total_result = calculator.calculate(classification)
    
    # Step 6: Cost, timeline, confidence (reuse existing calculators)
    # ... (existing logic adapted to use catalog result)
    
    # Step 7: Assemble EstimationResult (backward compatible)
    return _build_estimation_result(request, total_result, phases_list, ...)
```

### 6. Data Models (`app/models/schemas.py` additions)

```python
class WorkItem(BaseModel):
    unitId: str           # e.g., "BE-05"
    complexity: str       # "simple" | "medium" | "complex"
    quantity: int         # ≥ 1
    system: str           # System name from registry
    reason: str           # 1-line explanation
    calculatedEffort: Optional[float] = None  # Filled by calculator

class ClassificationResult(BaseModel):
    requirementTitle: str
    targetSystems: list[str]
    scopeType: str
    workItems: list[WorkItem]
    integrationPatterns: list[str]
    overheadFlags: OverheadFlags
    assumptions: list[str]
    risks: list[str]

class OverheadFlags(BaseModel):
    teamSize: int = 3
    crossDomain: bool = False
    crossDomainSystems: list[str] = []
    techFamiliarityRisk: str = "proficient"
    dataVolumeEstimate: str = "<1K"
    multiRegion: bool = False
    regionCount: int = 0
    securityCritical: bool = False
    legacyTechDebt: bool = False

class CalculationResult(BaseModel):
    pointEstimate: float
    confidenceLevel: str  # HIGH / MEDIUM / LOW
    rangeLow: float
    rangeHigh: float
    baseEffort: float
    patternSurcharge: float
    hubSurcharge: float
    overheadMultiplier: float
    aiMultiplier: float
    workItems: list[WorkItem]  # With calculatedEffort filled
    disciplineBreakdown: list[DisciplineEffort]
    sanityWarnings: list[str]
    assumptions: list[str]
    risks: list[str]

class CatalogBreakdown(BaseModel):
    """Detailed work-item-level breakdown for UI display."""
    workItems: list[WorkItem]
    overheadDetail: dict[str, float]
    integrationPatterns: list[str]
    hubSurcharges: dict[str, float]
    aiMultiplierApplied: float
    sanityWarnings: list[str]
```

### 7. Admin Settings API (`app/routers/admin_config.py` additions)

New endpoints:

```
GET  /api/admin/catalog                    → Return current estimation_catalog.json
PUT  /api/admin/catalog                    → Replace catalog (validates structure)
GET  /api/admin/system-dependencies        → Return current system_dependencies.json
PUT  /api/admin/system-dependencies        → Replace dependencies (validates)
GET  /api/admin/catalog/ai-multiplier      → Get current AI multiplier settings
PUT  /api/admin/catalog/ai-multiplier      → Update AI multiplier
POST /api/admin/catalog/reset              → Reset catalog to shipped defaults
GET  /api/admin/catalog/history            → List catalog version history
```

### 8. UI Changes (`static/index.html`)

#### 8.1 Results View Enhancement

Below the existing summary cards, add an expandable "Detailed Decomposition" section:

```
┌─────────────────────────────────────────────────────────┐
│ ESTIMATION RESULTS                                       │
├─────────────────────────────────────────────────────────┤
│ Total Effort: 40.7 person-days (30.5 – 50.9)           │
│ Confidence: MEDIUM | Cost: ₹24.4L | Duration: 2.5 mo   │
├─────────────────────────────────────────────────────────┤
│ [Effort by Discipline]  [Cost Breakdown]  [Timeline]    │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Digital Engineering: 32.1 pd                        │ │
│ │ QA/Testing: 6.6 pd                                 │ │
│ │ DevOps: 2.0 pd                                     │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ ▶ Detailed Decomposition (click to expand)              │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ # │ Unit │ Description │ System │ Cmplx │ Effort   │ │
│ │ 1 │ FE-10│ Mobile screen│TruChamp│ Med   │ 8.4 pd  │ │
│ │ 2 │ FE-04│ List/table   │TruChamp│ Med   │ 3.6 pd  │ │
│ │ 3 │ BE-02│ Biz logic    │TruChamp│ Cmplx │ 7.2 pd  │ │
│ │ ...│      │             │        │       │         │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Multipliers Applied:                                │ │
│ │   System avg: ×1.32 | Overhead: ×1.265             │ │
│ │   AI productivity: ×0.70 | Docs: +5%              │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ⚠ Warnings:                                        │ │
│ │   • Payment flow without integration test           │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### 8.2 Admin Settings — Catalog Editor

Under Admin Settings, a new "Estimation Catalog" tab with:

- **Effort Table**: Editable grid (unitId | simple | medium | complex) with save button
- **System Multipliers**: Editable list (system | multiplier) with validation
- **Overhead Factors**: Form with dropdowns/inputs for each factor
- **AI Productivity**: Global slider (0.65 – 1.0) + per-category overrides
- **Import/Export**: Upload JSON / Download JSON buttons
- **Reset**: "Reset to Defaults" with confirmation modal

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `config/estimation_catalog.json` | CREATE | All effort values, multipliers, overheads |
| `config/system_dependencies.json` | CREATE | System graph, hubs, integration links |
| `config/estimation_blueprint.md` | CREATE | Part A of blueprint v3 (LLM prompt content) |
| `app/services/catalog_classifier.py` | CREATE | 3-call chunked SLM classification |
| `app/services/catalog_calculator.py` | CREATE | Deterministic math engine |
| `app/services/catalog_loader.py` | CREATE | Config loading with TTL cache |
| `app/services/estimation_engine.py` | MODIFY | Refactor to use classifier + calculator |
| `app/models/schemas.py` | MODIFY | Add WorkItem, ClassificationResult, etc. |
| `app/routers/admin_config.py` | MODIFY | Add catalog CRUD endpoints |
| `app/routers/estimations.py` | MODIFY | Minor — result now includes catalogBreakdown |
| `static/index.html` | MODIFY | Add detailed decomposition view + catalog editor |

## Sequence Diagram — Estimation Flow

```
User            Frontend         API              Classifier        Calculator       Config
 │                │               │                  │                 │               │
 │ Upload PRD     │               │                  │                 │               │
 │───────────────▶│               │                  │                 │               │
 │                │ POST /estimate│                  │                 │               │
 │                │──────────────▶│                  │                 │               │
 │                │               │ load_catalog()   │                 │               │
 │                │               │─────────────────────────────────────────────────▶│
 │                │               │◀────────────────────────────────────────────────── │
 │                │               │                  │                 │               │
 │                │               │ classify(prd)    │                 │               │
 │                │               │─────────────────▶│                 │               │
 │                │               │                  │ Call 1: Systems │               │
 │                │               │                  │───▶ SLM ───▶   │               │
 │                │               │                  │ Call 2: Items   │               │
 │                │               │                  │───▶ SLM ───▶   │               │
 │                │               │                  │ Call 3: Integr. │               │
 │                │               │                  │───▶ SLM ───▶   │               │
 │                │               │                  │                 │               │
 │                │               │◀─────────────────│ ClassificationResult           │
 │                │               │                  │                 │               │
 │                │               │ calculate(cls)   │                 │               │
 │                │               │────────────────────────────────▶│               │
 │                │               │                  │              │ pure math      │
 │                │               │◀───────────────────────────────── │               │
 │                │               │                  │  CalculationResult              │
 │                │               │                  │                 │               │
 │                │◀──────────────│ EstimationResult │                 │               │
 │◀───────────────│               │                  │                 │               │
 │ Show results   │               │                  │                 │               │
```

## Error Handling Strategy

| Failure | Recovery |
|---------|----------|
| Call 1 (systems) fails | Retry once → if still fails, use all systems mentioned as text in PRD |
| Call 2 (work items) fails | Retry once → if still fails, use default decomposition from §4 based on scopeType |
| Call 3 (integration) fails | Retry once → if still fails, infer patterns from targetSystems using dependency graph |
| Catalog JSON missing/corrupt | Fall back to hardcoded defaults embedded in code |
| Unknown unitId in LLM output | Discard that work item, log warning |
| Unknown system in LLM output | Apply ×1.2 default multiplier, log warning |
| Estimate below minimum guard | Add warning, still return result |
| Estimate above maximum guard | Add warning, still return result |

## Migration Strategy

The old estimation engine code (`_build_estimation_prompt`, `_chunked_estimation`, `_parse_estimation_response`) remains as a fallback. The new catalog-based path is the primary path. If the entire catalog pipeline fails (all retries exhausted), the engine falls back to the old single-shot prompt approach with a degradation warning.

Configuration switch in `config/estimation_catalog.json`:
```json
{
  "engine": "catalog",  // "catalog" | "legacy"
  ...
}
```

This allows switching back to the old engine without code deployment if the catalog approach produces issues in early usage.
