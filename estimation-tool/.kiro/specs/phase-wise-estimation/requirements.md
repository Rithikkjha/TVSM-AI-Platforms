# Requirements Document

## Introduction

The Phase-wise Estimation feature extends the Project Estimation Tool to detect phased delivery plans within uploaded PRD/BRD documents and produce separate effort breakdowns per phase. Currently, the tool generates a single consolidated estimation regardless of whether the source document defines phases, releases, sprints, or milestones. This feature enables phase-aware estimation while maintaining backward compatibility for documents without phase information.

Additionally, this feature constrains discipline names to a fixed enumeration, preventing the SLM from inventing arbitrary discipline labels.

## Glossary

- **Estimation_Engine**: The backend service (`app/services/estimation_engine.py`) that orchestrates the full estimation pipeline including SLM prompt construction, response parsing, and result assembly.
- **Phase_Detector**: A new component responsible for identifying phase-related structures (phases, releases, sprints, milestones) within document text content.
- **SLM_Engine**: The inference service (`app/services/slm_engine.py`) that calls Ollama or OpenRouter for language model completions.
- **Results_UI**: The frontend results display section in `static/index.html` that renders estimation outputs to the user.
- **Phase**: A named delivery increment within a project (e.g., "Phase 1", "Release 2", "Sprint 3", "Milestone Alpha") that groups a subset of use cases or requirements.
- **Discipline**: One of the fixed engineering practice areas: Digital Engineering, Data Engineering, Data Science, DevOps, QA/Testing, Tech COE, Product/Design.
- **Consolidated_View**: The existing single-estimation display showing one effort breakdown across all use cases.
- **Phase_View**: A new display mode showing per-phase effort breakdowns with individual timelines and costs.

## Requirements

### Requirement 1: Phase Detection from Document Content

**User Story:** As an estimation user, I want the system to automatically detect whether my uploaded document contains phased delivery plans, so that the estimation output matches the project's delivery structure.

#### Acceptance Criteria

1. WHEN a document is uploaded for estimation, THE Phase_Detector SHALL scan the extracted text content for phase indicators including: "Phase N", "Release N", "Sprint N", "Milestone" labels, and tabular phase-assignment columns.
2. WHEN phase indicators are found, THE Phase_Detector SHALL extract a list of phase names and the use cases or requirements assigned to each phase.
3. WHEN no phase indicators are found in the document, THE Phase_Detector SHALL return an empty phase list indicating a non-phased document.
4. THE Phase_Detector SHALL recognize phase assignments in varied formats including numbered headings (e.g., "## Phase 1"), table columns (e.g., a "Phase" column mapping use case IDs to phases), and inline annotations (e.g., "UC#1 [Phase 1]").
5. IF the document contains ambiguous phase references that cannot be reliably parsed, THEN THE Phase_Detector SHALL fall back to treating the document as non-phased and include a warning in the response.

### Requirement 2: Phase-wise SLM Prompt Construction

**User Story:** As an estimation user, I want the SLM to produce effort estimates per phase, so that I can understand the cost and effort of each delivery increment separately.

#### Acceptance Criteria

1. WHEN phases are detected in the document, THE Estimation_Engine SHALL construct a prompt instructing the SLM to produce a separate effort breakdown for each detected phase.
2. WHEN no phases are detected, THE Estimation_Engine SHALL construct the existing single consolidated prompt (backward compatible behavior).
3. THE Estimation_Engine SHALL include the phase name and its assigned use cases in the prompt context for each phase.
4. THE Estimation_Engine SHALL instruct the SLM to produce per-phase timeline estimates and team composition recommendations.

### Requirement 3: Constrained Discipline Names

**User Story:** As an estimation user, I want discipline names to be consistent across all estimations, so that I can compare results reliably without encountering invented or inconsistent labels.

#### Acceptance Criteria

1. THE Estimation_Engine SHALL constrain discipline names to the following fixed set: "Digital Engineering", "Data Engineering", "Data Science", "DevOps", "QA/Testing", "Tech COE", "Product/Design".
2. WHEN the SLM returns a discipline name not in the fixed set, THE Estimation_Engine SHALL map the returned name to the closest matching discipline from the fixed set or discard the entry with a logged warning.
3. THE Estimation_Engine SHALL include the fixed discipline list in the SLM prompt with explicit instructions to use only these names.
4. THE Estimation_Engine SHALL validate parsed SLM output to reject discipline entries that do not match the fixed set before assembling the result.

### Requirement 4: Phase-wise Response Schema

**User Story:** As a developer integrating with this API, I want the response schema to include a structured phases array, so that downstream consumers can programmatically access per-phase estimation data.

#### Acceptance Criteria

1. WHEN phases are detected, THE Estimation_Engine SHALL return an EstimationResult containing a `phases` array where each entry includes: phase name, effort breakdown (list of DisciplineEffort), total person-days, total person-months, team composition, timeline, and cost projection for that phase.
2. WHEN no phases are detected, THE Estimation_Engine SHALL return an EstimationResult with a null or empty `phases` array, preserving the existing top-level consolidated fields unchanged.
3. THE Estimation_Engine SHALL ensure that the sum of per-phase total person-days equals the top-level totalEffortPersonDays (within a 5% tolerance for rounding).
4. FOR ALL valid phase-wise estimation results, parsing the phases array then summing effort per discipline SHALL produce values consistent with the top-level effort breakdown (round-trip property).

### Requirement 5: Phase-wise Frontend Display

**User Story:** As an estimation user, I want to see per-phase results in a tabbed or accordion view, so that I can review effort, cost, and timeline for each delivery phase independently.

#### Acceptance Criteria

1. WHEN the estimation result contains a non-empty phases array, THE Results_UI SHALL render a tabbed interface with one tab per phase plus a "Consolidated" summary tab.
2. WHEN the estimation result has no phases (null or empty array), THE Results_UI SHALL render the existing Consolidated_View with no changes to the current layout.
3. THE Results_UI SHALL display for each phase tab: effort breakdown table, total person-days, total person-months, team composition, calendar duration, and cost projection.
4. THE Results_UI SHALL display the "Consolidated" tab with the aggregated totals across all phases.
5. THE Results_UI SHALL default to showing the "Consolidated" tab as the initially active tab when phase data is present.

### Requirement 6: Backward Compatibility

**User Story:** As an existing user of the tool, I want non-phased documents to continue producing the same estimation output and UI experience as before, so that the new feature does not disrupt my current workflow.

#### Acceptance Criteria

1. WHEN a document without phase information is processed, THE Estimation_Engine SHALL produce an EstimationResult identical in structure to the current output (with phases field set to null or empty).
2. WHEN a document without phase information is processed, THE Results_UI SHALL render the Consolidated_View exactly as it does in the current implementation.
3. THE Estimation_Engine SHALL not require any additional mandatory input fields from the user to support phase detection — detection is fully automatic from document content.

### Requirement 7: Phase Detection Robustness

**User Story:** As an estimation user uploading diverse document formats, I want phase detection to work reliably across different PRD structures, so that I get phase-wise output regardless of how the author formatted their phase plan.

#### Acceptance Criteria

1. THE Phase_Detector SHALL detect phases from documents using numbered phase headings (e.g., "Phase 1: Identity & Rides").
2. THE Phase_Detector SHALL detect phases from documents using tabular use case assignments (e.g., a table with a "Phase" or "Release" column).
3. THE Phase_Detector SHALL detect phases from documents using milestone-based groupings (e.g., "Milestone 1 - MVP").
4. THE Phase_Detector SHALL detect phases from documents using sprint-based groupings (e.g., "Sprint 1-3: Core Features").
5. IF a document contains only a single phase (all use cases assigned to one phase), THEN THE Phase_Detector SHALL treat it as non-phased to avoid a redundant single-phase breakdown.
