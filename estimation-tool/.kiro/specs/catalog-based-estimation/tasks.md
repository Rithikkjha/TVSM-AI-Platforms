# Implementation Tasks

## Task 1: Create Config Files (Catalog + Dependencies + Blueprint)
- [x] Create `config/estimation_catalog.json` with full effort tables (81 units × 3 tiers), system multipliers, overhead factors, integration pattern costs, hub surcharges, AI multiplier, sanity checks, discipline mapping
- [x] Create `config/system_dependencies.json` with system registry (37 systems), hub identification, integration links (59 edges), cross-domain overhead rules, critical path chains
- [x] Create `config/estimation_blueprint.md` containing Part A (§1-§5) from bottom-up blueprint v3 — estimation principles, work unit catalog (names/descriptions only), system registry, trigger phrases, LLM output schema
- [x] Validate JSON files parse correctly and all unit IDs in catalog match those referenced in blueprint

## Task 2: Create Data Models (schemas.py additions)
- [x] Add `WorkItem` model (unitId, complexity, quantity, system, reason, calculatedEffort)
- [x] Add `OverheadFlags` model (teamSize, crossDomain, crossDomainSystems, techFamiliarityRisk, dataVolumeEstimate, multiRegion, regionCount, securityCritical, legacyTechDebt)
- [x] Add `ClassificationResult` model (requirementTitle, targetSystems, scopeType, workItems, integrationPatterns, overheadFlags, assumptions, risks)
- [x] Add `CalculationResult` model (pointEstimate, confidenceLevel, rangeLow, rangeHigh, baseEffort, patternSurcharge, hubSurcharge, overheadMultiplier, aiMultiplier, workItems, disciplineBreakdown, sanityWarnings, assumptions, risks)
- [x] Add `CatalogBreakdown` model for frontend display (workItems, overheadDetail, integrationPatterns, hubSurcharges, aiMultiplierApplied, sanityWarnings)
- [x] Add `catalogBreakdown` optional field to existing `EstimationResult` model

## Task 3: Create Catalog Loader Service
- [x] Create `app/services/catalog_loader.py` with `CatalogLoader` class
- [x] Implement `load_catalog()` — reads `config/estimation_catalog.json` with 5-minute TTL cache
- [x] Implement `load_dependencies()` — reads `config/system_dependencies.json` with 5-minute TTL cache
- [x] Implement `load_blueprint_section(section: str)` — parses markdown headings and returns content for §1, §2, §3, §4, §5
- [x] Implement `invalidate_cache()` for admin reload
- [x] Add fallback to hardcoded defaults if JSON files missing/corrupt
- [x] Add structural validation on load (check required keys, value ranges)

## Task 4: Create Catalog Classifier Service (3-Call Chunked SLM)
- [x] Create `app/services/catalog_classifier.py` with `CatalogClassifier` class
- [x] Implement `_build_call1_prompt()` — system identification prompt using §3 registry (~2K tokens)
- [x] Implement `_call1_identify_systems()` — call SLM, parse JSON response → targetSystems, scopeType, overheadFlags
- [x] Implement `_build_call2_prompt()` — work item classification prompt using §1 principles + §2 catalog + §4 triggers (~6K tokens)
- [x] Implement `_call2_classify_work_items()` — handle PRD chunking (split at 8K chars, ~6K per chunk), call SLM per chunk, merge results
- [x] Implement `_build_call3_prompt()` — integration/risk analysis prompt (~2K tokens)
- [x] Implement `_call3_integration_risks()` — call SLM, parse integration patterns + assumptions + risks
- [x] Implement `_merge_chunked_results()` — deduplicate work items with same unitId+system (sum quantities)
- [x] Implement `classify()` orchestrator — runs all 3 calls sequentially, merges into ClassificationResult
- [x] Add retry logic — each call retried once on failure before falling through
- [x] Add JSON parsing with graceful handling (extract JSON from markdown code blocks, handle malformed responses)
- [x] Add validation — check unitIds exist in catalog, complexity values valid, systems in registry

## Task 5: Create Catalog Calculator Service (Deterministic Math)
- [x] Create `app/services/catalog_calculator.py` with `CatalogCalculator` class
- [x] Implement `_calculate_base_effort()` — Σ(effort[unitId][complexity] × quantity × systemMultiplier[system])
- [x] Implement `_calculate_pattern_surcharges()` — sum pattern costs from integrationPatternCosts table
- [x] Implement `_calculate_hub_surcharges()` — sum hub surcharges for hub systems in targetSystems
- [x] Implement `_calculate_overhead_multiplier()` — compound: teamSize × crossDomain × techFamiliarity × dataVolume × deployment × security × legacy
- [x] Implement `_apply_ai_multiplier()` — apply global multiplier (or per-category if set) as final step
- [x] Implement `_calculate_confidence_band()` — HIGH/MEDIUM/LOW based on assumption+risk count, return range
- [x] Implement `_run_sanity_checks()` — min/max guards + consistency checks (hub without INT, payment without QA-02, etc.)
- [x] Implement `_map_to_disciplines()` — FE/BE/INT → Digital Engineering, QA → QA/Testing, DO → DevOps
- [x] Implement `calculate()` orchestrator — runs full pipeline, returns CalculationResult
- [x] Ensure fully deterministic — same input always produces same output (no random, no async, no external calls)

## Task 6: Refactor Estimation Engine to Use Catalog Pipeline
- [x] Modify `generate_estimation()` in `app/services/estimation_engine.py` to use CatalogClassifier + CatalogCalculator as primary path
- [x] Keep old `_build_estimation_prompt()` / `_chunked_estimation()` as fallback (triggered when catalog engine fails entirely)
- [x] Add `engine` config check — if `estimation_catalog.json` has `"engine": "legacy"`, use old path
- [x] Wire phase detection: if phases detected, run classifier per phase, calculate per phase, aggregate
- [x] Map CatalogCalculator output → existing EstimationResult fields (effortBreakdown by discipline, totalEffortPersonDays, etc.)
- [x] Populate new `catalogBreakdown` field in EstimationResult
- [x] Keep existing cost_calculator, timeline_calculator, confidence_calculator integration (feed them the discipline breakdown from catalog)
- [x] Add logging: log classification JSON, calculation breakdown, and any warnings
- [x] Add timing: log duration of each SLM call and total pipeline time

## Task 7: Admin API Endpoints for Catalog Management
- [x] Add `GET /api/admin/catalog` — return current estimation_catalog.json content
- [x] Add `PUT /api/admin/catalog` — validate structure, save to config/, invalidate cache
- [x] Add `GET /api/admin/system-dependencies` — return current system_dependencies.json
- [x] Add `PUT /api/admin/system-dependencies` — validate structure, save, invalidate cache
- [x] Add `GET /api/admin/catalog/ai-multiplier` — return AI multiplier section
- [x] Add `PUT /api/admin/catalog/ai-multiplier` — update AI multiplier only, save, invalidate cache
- [x] Add `POST /api/admin/catalog/reset` — copy shipped defaults back to config/, invalidate cache
- [x] Add validation on PUT: effort values 0.1-20.0, multipliers 0.5-3.0, no missing required keys
- [x] Store backup of previous version in config/ on each PUT

## Task 8: Frontend — Detailed Decomposition View in Results
- [x] Add expandable "Detailed Decomposition" section below existing estimation results summary
- [x] Show work items table: # | Unit ID | Description | System | Complexity | Qty | Effort (pd)
- [x] Show multipliers summary: system avg, overhead compound, AI multiplier, documentation %
- [x] Show integration patterns identified as tags/pills
- [x] Show hub surcharges applied (which hubs + how many days each)
- [x] Show sanity warnings in a yellow alert box (if any)
- [x] Show assumptions and risks in separate collapsible sections
- [x] Show confidence band visualization (bar with LOW/MED/HIGH marker + range)
- [x] Maintain backward compatibility — existing summary cards, discipline breakdown, cost/timeline all unchanged

## Task 9: Frontend — Catalog Editor in Admin Settings
- [ ] Add "Estimation Catalog" tab/section under Admin Settings page
- [ ] Create effort table editor: editable grid with unitId | name | simple | medium | complex columns
- [ ] Create system multipliers editor: list with system name | multiplier, editable inline
- [ ] Create overhead factors editor: form with dropdowns/inputs for each factor category
- [ ] Create AI productivity section: global slider (0.65-1.0) + per-category override toggles
- [ ] Add Import JSON button (file upload → validates → replaces catalog)
- [ ] Add Export JSON button (downloads current catalog as file)
- [ ] Add "Reset to Defaults" button with confirmation modal
- [ ] Add Save button that calls PUT /api/admin/catalog with validation feedback
- [ ] Add input validation: no negative values, multipliers 0.5-3.0, effort 0.1-20.0

## Task 10: Integration Testing & Fallback Verification
- [ ] Test full pipeline: upload a sample PRD → verify 3 SLM calls execute → verify calculation matches expected output
- [ ] Test chunking: upload a >8K char PRD → verify Call 2 splits and merges correctly
- [ ] Test fallback: simulate SLM failure → verify system falls back to legacy engine with degradation warning
- [ ] Test catalog edit: modify effort value via API → verify next estimation uses new value
- [ ] Test sanity checks: craft a classification that triggers min/max guards → verify warnings appear
- [ ] Test phase-wise: upload a phased PRD → verify per-phase classification and separate calculations
- [ ] Test AI multiplier: set to 0.70 → verify final estimate is 70% of pre-AI subtotal
- [ ] Test determinism: run same classification through calculator 10 times → verify identical output
- [ ] Test unknown unitId handling: inject invalid unitId in mock LLM response → verify discarded with warning
- [ ] Test engine switch: set `"engine": "legacy"` in catalog → verify old path used
