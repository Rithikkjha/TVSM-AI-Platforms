# Implementation Plan: Phase-wise Estimation

## Overview

This plan implements phase-aware estimation by introducing a Phase Detector module, constraining discipline names via an enum, modifying the estimation engine for phase-aware prompting, extending the response schema, and adding a tabbed frontend view. Each task builds incrementally, ensuring no orphaned code.

## Tasks

- [x] 1. Add Discipline enum and PhaseEstimation schema to data models
  - [x] 1.1 Add `Discipline` enum to `app/models/schemas.py`
    - Define `Discipline(str, Enum)` with values: "Digital Engineering", "Data Engineering", "Data Science", "DevOps", "QA/Testing", "Tech COE", "Product/Design"
    - Place it alongside the existing `Domain` and `Stream` enums
    - _Requirements: 3.1_

  - [x] 1.2 Add `PhaseEstimation` model to `app/models/schemas.py`
    - Define `PhaseEstimation(BaseModel)` with fields: `phaseName` (str), `effortBreakdown` (list[DisciplineEffort]), `totalPersonDays` (float), `totalPersonMonths` (float), `teamComposition` (list[TeamMember], default_factory=list), `calendarDuration` (Optional[float]), `costProjection` (Optional[CostProjection]), `assumptions` (list[str], default_factory=list)
    - _Requirements: 4.1_

  - [x] 1.3 Add optional `phases` field to `EstimationResult`
    - Add `phases: Optional[list[PhaseEstimation]] = Field(default=None, description="Per-phase estimation breakdown. Null if document is not phased.")`
    - Ensure all existing fields remain unchanged for backward compatibility
    - _Requirements: 4.2, 6.1, 6.3_

- [x] 2. Implement Phase Detector module
  - [x] 2.1 Create `app/services/phase_detector.py` with data classes and main entry point
    - Define `PhaseInfo` dataclass with `name: str` and `use_cases: list[str]`
    - Define `PhaseDetectionResult` dataclass with `phases: list[PhaseInfo]`, `detection_method: Optional[str]`, `warning: Optional[str]`
    - Implement `detect_phases(text: str) -> PhaseDetectionResult` that orchestrates the four detection strategies in priority order
    - _Requirements: 1.1, 1.3, 1.5_

  - [x] 2.2 Implement heading-based phase detection
    - Implement `_detect_heading_phases(text: str) -> list[PhaseInfo]` using regex to match patterns like "## Phase 1: ...", "### Release 2 - ...", numbered phase headings
    - Extract use cases listed under each heading until the next phase heading
    - _Requirements: 1.4, 7.1_

  - [x] 2.3 Implement table-based phase detection
    - Implement `_detect_table_phases(text: str) -> list[PhaseInfo]` to detect tabular use case assignments
    - Parse rows with a "Phase" or "Release" column and group use case IDs by phase
    - _Requirements: 1.4, 7.2_

  - [x] 2.4 Implement inline annotation and milestone-based detection
    - Implement `_detect_inline_phases(text: str) -> list[PhaseInfo]` for patterns like "UC#1 [Phase 1]", "[Sprint 1-3]"
    - Implement `_detect_milestone_phases(text: str) -> list[PhaseInfo]` for "Milestone 1 - MVP" style groupings
    - _Requirements: 1.4, 7.3, 7.4_

  - [x] 2.5 Implement single-phase collapsing and ambiguity handling
    - If only one phase is detected, return empty phases list (treat as non-phased)
    - If ambiguous/conflicting phase structures detected, return empty phases with a warning
    - _Requirements: 1.5, 7.5_

  - [x] 2.6 Add `DISCIPLINE_ALIASES` mapping and `normalize_discipline` function
    - Define `DISCIPLINE_ALIASES: dict[str, Discipline]` mapping common alternative names to the enum
    - Implement `normalize_discipline(raw_name: str) -> Optional[Discipline]` with: exact match → alias lookup → substring match → None
    - _Requirements: 3.2_

  - [ ]* 2.7 Write property tests for phase detection (Property 1, 2, 8, 9)
    - **Property 1: Phase detection extracts correct structure** — generate documents with known phase indicators, verify extracted phases match
    - **Property 2: Non-phased documents produce empty phase list** — generate documents without phase keywords, verify empty result
    - **Property 8: Multi-format phase detection** — generate documents with each format type, verify non-empty result
    - **Property 9: Single phase treated as non-phased** — generate documents with one phase, verify empty result
    - **Validates: Requirements 1.1, 1.2, 1.3, 7.1, 7.2, 7.3, 7.4, 7.5**

  - [ ]* 2.8 Write property tests for discipline normalization (Property 4, 5)
    - **Property 4: Discipline normalization correctness** — for any string matching an enum value (case-insensitive), verify correct enum returned; for random strings, verify result is Discipline or None
    - **Property 5: Discipline validation filters invalid entries** — generate lists with valid/invalid discipline names, verify only valid entries remain
    - **Validates: Requirements 3.1, 3.2, 3.4**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Modify Estimation Engine for phase-aware prompting
  - [x] 4.1 Add `_build_phase_estimation_prompt` function to `app/services/estimation_engine.py`
    - Build a prompt that includes each phase name, its assigned use cases, and instructions for the SLM to produce per-phase effort breakdown using only the 7 fixed Discipline names
    - Include instructions for per-phase timeline and team composition
    - _Requirements: 2.1, 2.3, 2.4, 3.3_

  - [x] 4.2 Add `_parse_phase_estimation_response` function
    - Parse JSON response expecting `{"phases": [{"phaseName": ..., "effortBreakdown": [...], "assumptions": [...]}, ...], "documentDetailScore": ..., "requirementClarityScore": ...}`
    - Validate structure and return parsed dict or None on failure
    - _Requirements: 4.1_

  - [x] 4.3 Add `_validate_disciplines` function
    - Accept list of effort breakdown dicts, normalize each discipline name using `normalize_discipline`
    - Discard entries with unmappable names (log warning), merge duplicates by summing person-days
    - Return list of validated `DisciplineEffort` objects
    - _Requirements: 3.2, 3.4_

  - [x] 4.4 Modify `generate_estimation` to integrate phase detection
    - Import and call `detect_phases` on PRD text (fallback to BRD if no phases in PRD)
    - Route to `_build_phase_estimation_prompt` if phases detected, else use existing `_build_estimation_prompt`
    - Parse phase response with `_parse_phase_estimation_response`, validate disciplines, assemble `PhaseEstimation` objects
    - Populate the `phases` field on `EstimationResult`; set to None if non-phased
    - Ensure backward compatibility: non-phased documents produce identical results to current behavior
    - _Requirements: 2.1, 2.2, 4.1, 4.2, 4.3, 4.4, 6.1_

  - [x] 4.5 Update existing `_build_estimation_prompt` to include fixed discipline list
    - Replace the current discipline list in the prompt with the 7-value `Discipline` enum names
    - Add explicit instruction: "Use ONLY these discipline names exactly as written"
    - _Requirements: 3.3_

  - [ ]* 4.6 Write property test for phase-aware prompt (Property 3)
    - **Property 3: Phase-aware prompt contains all phase context** — generate PhaseDetectionResult with N phases, verify prompt contains every phase name and every use case string
    - **Validates: Requirements 2.1, 2.3, 2.4**

  - [ ]* 4.7 Write property tests for consistency invariants (Property 6, 7)
    - **Property 6: Phase effort sums to total** — generate EstimationResult with phases, verify sum of phase totalPersonDays equals top-level totalEffortPersonDays within 5%
    - **Property 7: Per-discipline round-trip consistency** — generate EstimationResult with phases, verify per-discipline sums across phases match top-level effortBreakdown within 5%
    - **Validates: Requirements 4.3, 4.4**

- [x] 5. Integrate phase detection in the upload router
  - [x] 5.1 Verify router integration works end-to-end
    - Confirm that `app/routers/estimations.py` calls `generate_estimation` which now internally handles phase detection
    - No router changes should be needed since phase detection is internal to the engine; verify this assumption by checking the data flow
    - If any wiring is needed (e.g., passing extra context), add it here
    - _Requirements: 6.3_

  - [ ]* 5.2 Write unit tests for non-phased backward compatibility (Property 10)
    - **Property 10: Non-phased backward compatibility** — verify non-phased documents produce EstimationResult with phases=None and all existing fields valid
    - **Validates: Requirements 6.1**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement frontend tabbed phase display
  - [x] 7.1 Add tab bar rendering logic to `static/index.html`
    - Implement `buildTabBar(tabNames)` function that renders horizontal tab buttons
    - Add click handler to switch active tab and show/hide corresponding content panels
    - Style tabs consistently with existing card-based layout
    - _Requirements: 5.1, 5.5_

  - [x] 7.2 Add phase panel rendering
    - Implement `buildPhasePanel(phase)` that renders effort breakdown table, totals (person-days, person-months), team composition, calendar duration, and cost projection for a single phase
    - _Requirements: 5.3_

  - [x] 7.3 Add `renderPhaseResults(result)` orchestration function
    - If `result.phases` is null/empty, delegate to existing consolidated rendering (no changes)
    - If phases present, build tab bar with "Consolidated" + phase names, render consolidated panel and per-phase panels
    - Default to "Consolidated" tab active
    - Wire into the existing results display logic
    - _Requirements: 5.1, 5.2, 5.4, 5.5, 6.2_

  - [ ]* 7.4 Write unit tests for frontend rendering logic
    - Test that tabbed UI renders when phases array is non-empty
    - Test that existing consolidated view renders unchanged when phases is null
    - _Requirements: 5.1, 5.2, 6.2_

- [x] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties defined in the design document using `hypothesis`
- The implementation language is Python (backend) and JavaScript (frontend), matching the existing codebase
- Phase detection is fully automatic — no new user input required
