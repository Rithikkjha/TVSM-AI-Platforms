# Requirements Document

## Introduction

The Catalog-Based Estimation Engine is a complete rewrite of the effort estimation pipeline in TVS PlanIQ. The current approach asks the LLM to invent effort numbers (person-days) directly from PRD text, resulting in wildly inconsistent estimates (e.g., ₹69L vs ₹420L for the same PRD depending on model and run). The new approach separates concerns: the SLM only classifies work items from a fixed catalog, and the application performs all math deterministically using pre-defined effort tables, system multipliers, and overhead factors.

This is powered by two reference documents:
1. **Bottom-Up Estimation Blueprint v3** (`config/estimation_blueprint.md`) — 81 atomic work units across 5 categories (FE/BE/INT/QA/DO) with Simple/Medium/Complex effort tiers, system multipliers, overhead tables, and aggregation formula.
2. **System Dependency Diagram** (`config/system_dependencies.json`) — 39 systems, 55+ integration links, hub multipliers, cross-domain overhead, and cascade chains.

The SLM's role is reduced to pattern matching and classification — tasks that small models (gemma3:4b) handle reliably. The estimation accuracy is then determined by catalog quality (which is admin-editable and improves over time) rather than LLM mood.

## Glossary

- **Work_Unit**: An atomic unit of engineering work from the catalog (e.g., FE-04 = "List/table with CRUD", BE-17 = "SAP integration service"). Each has an ID, name, description, and effort values per complexity tier.
- **Complexity_Tier**: One of three levels (simple, medium, complex) assigned to each work item by the LLM based on scope inference from the PRD.
- **System_Multiplier**: A numeric factor (e.g., DMS = ×1.5, CPS = ×1.1) that adjusts base effort for a specific system's inherent complexity (tech debt, deployment model, codebase size).
- **Overhead_Factor**: A multiplier applied to subtotal effort based on contextual conditions (team size, cross-domain work, tech familiarity, data volume, deployment topology, security criticality, legacy tech debt).
- **Hub_Surcharge**: A flat effort add-on (in person-days) when a hub system (MDP, IDP, UMS, CNS, Booking Service) is directly modified — accounts for ripple-effect coordination and regression testing.
- **Integration_Pattern**: A recognized pattern of system-to-system communication (REST_EXISTING, SERVICE_BUS_NEW_TOPIC, SAP_RFC, etc.) that carries additional effort cost beyond the base work unit.
- **AI_Productivity_Multiplier**: A global admin-configurable factor (e.g., ×0.70 for teams using Kiro) applied as the final step to account for AI-assisted development speed.
- **Estimation_Catalog**: The JSON file (`config/estimation_catalog.json`) containing all effort values, multipliers, and overhead tables — the single source of truth for deterministic calculation.
- **System_Dependencies**: The JSON file (`config/system_dependencies.json`) containing the system graph, hub identification, integration patterns, and cross-domain overhead data.
- **Chunked_Classification**: The multi-call SLM approach where the PRD is processed in 3 focused calls (system identification → work item classification → integration/risk analysis) to stay within gemma3:4b's reliable accuracy window.
- **Confidence_Band**: The range around the point estimate (±10% for HIGH, ±25% for MEDIUM, ±40% for LOW) determined by the number of assumptions and risks flagged by the LLM.
- **Sanity_Check**: Post-calculation validation rules that flag estimates falling outside expected ranges for the given scope type.

## Requirements

### Requirement 1: SLM Classification-Only Prompt Architecture

**User Story:** As a user running estimations, I want the SLM to only classify work items from a fixed catalog (never invent effort numbers), so that estimates are consistent and reproducible regardless of model run or temperature.

#### Acceptance Criteria

1. WHEN an estimation is triggered, THE Estimation_Engine SHALL send the PRD text to the SLM with ONLY the catalog unit names, descriptions, system registry, trigger phrases, and estimation principles — never effort values.
2. THE SLM prompt SHALL explicitly instruct the model to "NEVER output effort numbers (days/hours). Only output unit IDs, complexity tier, and quantity."
3. THE SLM response SHALL conform to the LLM Output Schema (§5 of the blueprint) returning: `targetSystems`, `scopeType`, `workItems[]` (with unitId, complexity, quantity, system, reason), `integrationPatterns`, `overheadFlags`, `assumptions`, and `risks`.
4. IF the SLM returns a unitId not present in the catalog, THE Estimation_Engine SHALL discard that work item and log a warning.
5. IF the SLM returns a complexity value other than "simple", "medium", or "complex", THE Estimation_Engine SHALL default to "medium" and log a warning.
6. IF the SLM returns an empty workItems array, THE Estimation_Engine SHALL retry once with a simplified prompt, and if still empty, raise an estimation error.

### Requirement 2: Chunked Multi-Call SLM Strategy

**User Story:** As a user with gemma3:4b (limited context), I want the classification to be split across focused SLM calls, so that each call stays within the model's reliable accuracy window and produces better results than one massive prompt.

#### Acceptance Criteria

1. THE Estimation_Engine SHALL split classification into 3 sequential SLM calls:
   - Call 1 (System Identification): PRD summary + System Registry → returns `targetSystems`, `scopeType`, `overheadFlags`
   - Call 2 (Work Item Classification): PRD text (chunked if >8K chars) + Estimation Principles + Work Unit Catalog + Trigger Phrases → returns `workItems[]`
   - Call 3 (Integration & Risk Analysis): PRD summary + identified systems + integration pattern list → returns `integrationPatterns`, `assumptions`, `risks`
2. WHEN the PRD text exceeds 8000 characters, Call 2 SHALL be split into multiple sub-calls (one per ~6000 char chunk of the PRD), and results SHALL be merged by deduplicating work items with the same unitId + system combination (summing quantities).
3. THE Estimation_Engine SHALL merge outputs from all 3 calls into a single unified classification JSON before passing to the calculation engine.
4. IF any individual call fails (timeout, parse error), THE Estimation_Engine SHALL retry that specific call once before falling back to a single consolidated prompt.

### Requirement 3: Deterministic Effort Calculation from Catalog

**User Story:** As a user, I want effort calculations to be purely mathematical (no LLM involvement), so that given the same classification input, the same estimate is always produced.

#### Acceptance Criteria

1. THE Estimation_Engine SHALL calculate base effort as: `Σ(effort_table[unitId][complexity] × quantity × system_multiplier[system])` for each work item.
2. THE Estimation_Engine SHALL add integration pattern surcharges from the pattern cost table for each identified pattern.
3. THE Estimation_Engine SHALL add hub system surcharges (flat person-days) when any hub system (MDP, IDP, UMS, CNS, Booking Service) appears in targetSystems.
4. THE Estimation_Engine SHALL compound overhead multipliers in this order: team_size × cross_domain × tech_familiarity × data_volume × deployment_topology × security × legacy_debt.
5. THE Estimation_Engine SHALL add +5% documentation overhead to the subtotal.
6. THE Estimation_Engine SHALL apply the AI productivity multiplier as the final step.
7. THE Estimation_Engine SHALL produce a confidence band based on assumption/risk count: HIGH (±10%) if ≤2 assumptions and ≤1 risk, MEDIUM (±25%) if ≤4 assumptions and ≤3 risks, LOW (±40%) otherwise.
8. GIVEN identical classification JSON input, THE calculation function SHALL always produce the exact same output (deterministic, no randomness).

### Requirement 4: Estimation Catalog as Editable JSON Configuration

**User Story:** As an admin, I want to edit effort values, system multipliers, and overhead factors through the Settings UI or by directly modifying a JSON file, so that the estimation model can be calibrated over time without code changes.

#### Acceptance Criteria

1. THE Estimation_Engine SHALL load all effort values, system multipliers, overhead tables, integration pattern costs, hub surcharges, and AI multipliers from `config/estimation_catalog.json`.
2. THE Estimation_Engine SHALL load system dependency data (graph, hub identification) from `config/system_dependencies.json`.
3. WHEN `config/estimation_catalog.json` is modified, THE Estimation_Engine SHALL pick up changes on the next estimation run (no server restart required — use TTL cache with 5-minute expiry).
4. THE Settings UI SHALL provide a Catalog Editor page allowing admins to:
   - View and edit effort values (Simple/Medium/Complex) per work unit
   - View and edit system multipliers
   - View and edit overhead factor tables
   - View and edit AI productivity multiplier
   - Add new work units to the catalog
5. THE Settings UI SHALL validate catalog edits before saving (no negative values, multipliers between 0.5 and 3.0, effort values between 0.1 and 20.0 person-days).

### Requirement 5: System Dependencies JSON for Integration Scoring

**User Story:** As a user estimating integration-heavy projects, I want the system to automatically apply hub surcharges and cross-domain overhead based on which systems are touched, so that integration complexity is consistently accounted for.

#### Acceptance Criteria

1. THE `config/system_dependencies.json` SHALL contain: system registry (name, domain, multiplier, hub flag), integration links (source → target, pattern, criticality), hub surcharge values, and cross-domain overhead rules.
2. WHEN the LLM identifies targetSystems, THE Estimation_Engine SHALL automatically look up hub surcharges and apply them without LLM involvement.
3. WHEN the LLM flags `crossDomain: true`, THE Estimation_Engine SHALL apply the cross-domain multiplier from the overhead table.
4. THE dependency data SHALL be used to validate LLM output: if a hub system is in targetSystems but no INT-* work item references it, the engine SHALL log a warning (consistency check from §12 of the blueprint).

### Requirement 6: Sanity Checks and Validation Guards

**User Story:** As a user, I want the system to flag estimates that seem unreasonably high or low, so that obvious classification errors or catalog misconfigurations are caught before presenting results.

#### Acceptance Criteria

1. AFTER calculation, THE Estimation_Engine SHALL check the total estimate against minimum/maximum guards per scope type:
   - New Feature: min 10 days, max per system count
   - Enhancement: min 3 days, max 60 days
   - Bug Fix: min 0.5 days, max 20 days
   - Integration: min 5 days
   - Migration: min 15 days
2. THE Estimation_Engine SHALL run consistency checks (hub system without integration unit, payment without integration test, multi-system without QA-02, SAP in targets without BE-17, security-critical without QA-06) and include warnings in the result.
3. WHEN a sanity check fails, THE result SHALL include a `warnings[]` array with human-readable messages — but the estimate SHALL still be returned (warnings don't block output).

### Requirement 7: Backward-Compatible Result Format

**User Story:** As an existing user of TVS PlanIQ, I want the estimation results UI to continue showing the same information (effort breakdown by discipline, cost, timeline, confidence) while additionally showing the new work-item-level decomposition.

#### Acceptance Criteria

1. THE Estimation_Engine SHALL produce an EstimationResult that includes all existing fields (totalEffortPersonDays, totalEffortPersonMonths, effortBreakdown by discipline, costProjection, compositeConfidence, calendarDuration, teamComposition).
2. THE Estimation_Engine SHALL additionally include: `catalogBreakdown` (the full work-item-level detail with unitId, description, system, complexity, quantity, calculatedEffort per item), `overheadDetail` (which multipliers were applied and their values), and `sanityWarnings[]`.
3. THE existing discipline-level breakdown (Digital Engineering, QA/Testing, DevOps, etc.) SHALL be derived by mapping work unit categories (FE+BE+INT → Digital Engineering, QA → QA/Testing, DO → DevOps) for backward compatibility.
4. THE Results UI SHALL show the catalog-level breakdown in an expandable "Detailed Decomposition" section below the existing summary view.

### Requirement 8: Phase-Wise Compatibility

**User Story:** As a user uploading a phased PRD, I want catalog-based estimation to work per-phase, so that each phase gets its own work-item decomposition and effort calculation.

#### Acceptance Criteria

1. WHEN the Phase_Detector identifies multiple phases in the document, THE Estimation_Engine SHALL run the chunked classification (Calls 1-3) separately for each phase's scope/use cases.
2. EACH phase SHALL get its own `workItems[]`, `integrationPatterns`, and `overheadFlags` — phases are estimated independently.
3. THE top-level estimate SHALL be the sum of all phase estimates.
4. THE existing PhaseEstimation schema (phaseName, effortBreakdown, totalPersonDays, teamComposition, calendarDuration) SHALL be populated from the per-phase catalog calculations.

### Requirement 9: Estimation Blueprint Files Management

**User Story:** As an admin, I want to upload/update the estimation blueprint and dependency files through the Settings UI, so that the estimation model evolves without requiring deployments.

#### Acceptance Criteria

1. THE Settings UI SHALL provide a "Estimation Catalog" section under Admin Settings with:
   - Upload/replace `config/estimation_catalog.json`
   - Upload/replace `config/system_dependencies.json`
   - Download current versions of both files
   - A "Reset to Defaults" button that restores the shipped default catalog
2. WHEN a new catalog file is uploaded, THE system SHALL validate its structure (all required keys present, values within valid ranges) before accepting.
3. THE system SHALL maintain a version history of catalog changes (stored in SharePoint `Admin/CatalogHistory/`) for audit purposes.
4. THE estimation blueprint markdown (Part A — LLM prompt context) SHALL be stored as `config/estimation_blueprint.md` and used as the source for prompt construction.

### Requirement 10: AI Productivity Multiplier Configuration

**User Story:** As an admin, I want to set the AI productivity multiplier globally (and optionally per work-unit category), so that estimates reflect actual team velocity with AI tools.

#### Acceptance Criteria

1. THE Settings UI SHALL expose an "AI Productivity" setting with a global multiplier dropdown (1.0 / 0.85 / 0.75 / 0.70 / 0.65) with descriptions matching the AI adoption levels from the blueprint.
2. THE global AI multiplier SHALL be applied as the final step in calculation (after all other multipliers).
3. OPTIONALLY, the admin SHALL be able to set per-category multipliers (Frontend, Backend CRUD, Backend Logic, Integration, QA, DevOps, SAP) that override the global when set.
4. THE AI multiplier setting SHALL be stored in `config/estimation_catalog.json` under an `aiProductivity` key and take effect immediately (no restart).

