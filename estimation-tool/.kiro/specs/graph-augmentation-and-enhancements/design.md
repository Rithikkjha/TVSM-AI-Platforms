# Design: Graph Augmentation & Platform Enhancements

## Architecture Overview

```
PRD Upload → SLM Classification (3 calls) → Graph Augmentation → Catalog Calculator → Cloud Cost → Result
                                                    ↓
                                          Background: Scope + Doc Readiness → Enrichment Store → Frontend Poll
```

## 1. Graph Augmentation Layer

**File:** `app/services/graph_augmentation.py`

**Class:** `GraphAugmenter`

**Input:** `CatalogClassificationResult` (from SLM)
**Output:** `(augmented_classification, GraphAugmentationResult)`

### Detection Strategies (ordered):
1. **ALWAYS_INVOLVED_RULES** — 9 hard-coded architectural invariants (only for multi-system scope)
2. **Hub Detection** — if 3+ target systems, check if hub connects ≥2 of them
3. **Critical Path Chain** — if 3+ systems on a chain are present, add intermediates

### Cross-Domain Detection:
- Reads `domain` field from each system in `system_dependencies.json`
- CP + D2C present = cross-domain
- Overrides SLM's `crossDomain` flag

### Integration Item Auto-Addition:
- Finds `integrationLinks` where BOTH source and target are in scope
- Maps pattern → catalog unit (PATTERN_TO_UNIT dict, 18 patterns)
- Caps at 8 auto-added items
- Skips items where coverage already exists

## 2. Cloud Cost Calculator

**File:** `app/services/cloud_cost_calculator.py`

**Function:** `estimate_cloud_cost(work_items, target_systems, dependencies, catalog)`

### Mapping Layers:
1. `CATEGORY_RESOURCE_MAP` — work item category → Azure resources
2. `SYSTEM_RESOURCE_MAP` — target system → system-specific resources
3. `prd_azure_hints` — keyword detection in work item reasons
4. Baseline resources (App Insights, Key Vault, Load Balancer)

### Pricing:
- Azure India (Central India) Pay-As-You-Go rates in INR
- Deployment multiplier from system_dependencies.json deployment models
- "Existing Infra" = 30% of new (shared services already running)

## 3. Distribution Auto-Correction

**Location:** `CatalogCalculator._check_distribution()` (in catalog_calculator.py)

### Flow:
1. After `_map_to_disciplines()` produces base breakdown
2. Compare each discipline % against `distributionRules[scopeType]`
3. If below `min`, bump to `expected` level
4. Modify `discipline_breakdown` in-place
5. Recalculate `final_effort` from adjusted breakdown
6. Add warning with correction details

### Rules (from estimation_catalog.json):
```json
"New Feature": {
  "Digital Engineering": {"min": 0.50, "expected": 0.60, "max": 0.75},
  "QA/Testing": {"min": 0.08, "expected": 0.12, "max": 0.18},
  "DevOps": {"min": 0.02, "expected": 0.05, "max": 0.10}
}
```

## 4. Async Enrichment

### Backend:
- `_backfill_scope_and_readiness()` — async task fired after estimation result built
- Stores results in `_enrichment_store[estimation_id]`
- Status: "processing" → "complete" / "failed"

### API:
- `GET /api/estimations/{id}/enrichment` — returns enrichment status + data

### Frontend:
- `_pollEnrichment(estimationId, section)` — polls every 5s, max 60 attempts
- Updates scope/doc quality sections in-place (no tab reset)

## 5. Discipline Scaling

**Problem:** `pointEstimate` includes overhead × scope factor × AI multiplier × hub surcharges, but `disciplineBreakdown` only has base work item mapping.

**Fix:** After calculating both, scale discipline breakdown proportionally:
```python
scale_factor = total_effort_days / raw_sum
effort_breakdown = [DisciplineEffort(d.discipline, d.personDays * scale_factor, ...) for d in breakdown]
```

## 6. Data Flow (SharePoint)

### Save (25 columns):
```
[0-21] Original fields (EstimationId through PhasesJSON)
[22]   CatalogBreakdownJSON
[23]   InfraCostJSON  
[24]   DocumentReadinessJSON
```

### Load:
- Uses `col_map` for named headers (new monthly files)
- Falls back to positional index (22, 23, 24) for pre-existing files

## 7. System Aliases

**File:** `catalog_classifier.py` → `SYSTEM_NAME_ALIASES`

### Categories:
- Vehicle names (iQube S, Apache, etc.) → TVS Connect
- Azure services → `_CLOUD_HINT_` (filtered from targetSystems, fed to cloud cost)
- Common abbreviations (BS → Booking Service, etc.)

## 8. Integration Patterns

**File:** `estimation_catalog.json` → `integrationPatternCosts`

28 patterns mapped with cost surcharges (0–2.5 pd each):
- REST_API, SERVICE_BUS, SSO_JWT, BLE, MQTT, GRAPHQL_WEBSOCKET, etc.
