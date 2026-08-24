# Implementation Plan: Build vs Buy Evaluation

## Overview

This plan implements the Build vs Buy Evaluation feature following a bottom-up approach: pure-logic services first (scoring matrix, TCO calculator), then the orchestration/persistence layer, API router, SLM integration, frontend wizard/dashboard, and finally report generation. Each task builds on the previous, ensuring no orphaned code.

## Tasks

- [x] 1. Create data models and enums for Build vs Buy
  - [x] 1.1 Add BvB enums and Pydantic models to `app/models/schemas.py`
    - Define `OptionType(str, Enum)` with values: Do_Nothing, Build, Buy, Extend
    - Define `EvaluationStatus(str, Enum)` with values: Draft, In_Progress, Scoring_Complete, Recommended, Archived
    - Define `EvaluationCreateRequest`, `OptionCreateRequest`, `OptionUpdateRequest`, `ScoreSubmitRequest`, `TCOSubmitRequest`, `StatusUpdateRequest` request models
    - Define `EvaluationResponse`, `EvaluationListResponse`, `EvaluationDetailResponse`, `OptionResponse`, `ScoreResponse`, `TCOResponse`, `ProposalAnalysisResponse`, `ReportResponse`, `RecommendationResponse`, `DimensionScoreResponse`, `TCOResultResponse` response models
    - Define `Year0CostsInput` and `RecurringCostsInput` models with field validations (ge=0 for costs)
    - _Requirements: 1.1, 2.2, 3.3, 5.1, 5.2, 12.1_

- [x] 2. Implement Scoring Matrix Calculator
  - [x] 2.1 Create `app/services/scoring_matrix.py` with constants and core logic
    - Define `DEFAULT_WEIGHTS` dict with 8 dimensions matching Gartner weights (business_value=0.20, technology_fit=0.15, functional_fit=0.15, financial=0.20, operational_sustainability=0.15, business_agility=0.05, vendor_risk=0.05, ai_readiness=0.05)
    - Define `DIMENSIONS` list, `SCORE_MIN=1`, `SCORE_MAX=5`
    - Define `DimensionScore` and `WeightedResult` dataclasses
    - Implement `validate_weights(weights)` — returns True if sum is 1.0 within ±0.001 tolerance
    - Implement `validate_score(score)` — returns True if 1 ≤ score ≤ 5
    - Implement `calculate_weighted_total(scores, weights)` — returns float in [1.0, 5.0]
    - Implement `rank_options(results)` — sorts complete options by weighted_total descending
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.3_

  - [ ]* 2.2 Write property tests for scoring matrix
    - **Property 6: Weight sum validation**
    - **Property 7: Score range validation**
    - **Property 8: Weighted total calculation correctness**
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6**

  - [ ]* 2.3 Write property tests for ranking and partial scoring
    - **Property 10: Partial scoring reports correct unscored dimensions**
    - **Property 11: Ranking correctness with completeness filtering**
    - **Validates: Requirements 4.2, 4.3, 7.5**

- [x] 3. Implement TCO Calculator
  - [x] 3.1 Create `app/services/tco_calculator.py` with dataclasses and calculation logic
    - Define `Year0Costs` dataclass with fields: license, implementation, migration, infrastructure, training, professional_services (all float, default 0.0) and `total` property
    - Define `RecurringCosts` dataclass with fields: license_renewal, cloud, infrastructure, storage, ktlo_people, vendor_amc, change_requests, upgrades, support (all float, default 0.0) and `total` property
    - Define `TCOInput` dataclass with option_id, year_0, yearly_costs list, and optional user_count
    - Define `TCOResult` dataclass with option_id, year_0_total, three_year_tco, five_year_tco, annual_run_cost, cost_per_user, yearly_totals
    - Implement `validate_costs(costs)` — returns list of field names with negative values
    - Implement `get_year_costs(tco_input, year)` — returns RecurringCosts for a year, defaulting to last specified
    - Implement `calculate_tco(tco_input)` — computes 3Y TCO, 5Y TCO, Annual Run Cost, Cost per User
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 3.2 Write property tests for TCO calculator
    - **Property 12: Cost validation rejects negative values**
    - **Property 13: TCO calculation correctness**
    - **Property 14: 3-Year TCO never exceeds 5-Year TCO**
    - **Validates: Requirements 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 6.5**

- [x] 4. Checkpoint - Core calculators complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement BvB Evaluation Service (orchestration + persistence)
  - [x] 5.1 Create `app/services/bvb_evaluation_service.py` with evaluation lifecycle logic
    - Implement `create_evaluation(request, user, sp)` — validates intake (name non-empty, budget_max >= budget_min), generates UUID, sets status=Draft, persists to SharePoint `BuildVsBuy/{id}.xlsx` + updates `BuildVsBuy/EvalIndex.xlsx`, logs audit event, returns EvaluationResponse
    - Implement `load_evaluation(evaluation_id, sp)` — reads evaluation workbook from SharePoint, deserializes all sheets (Metadata, Options, Scores, TCO, Recommendation) into EvaluationDetail
    - Implement `save_evaluation(evaluation, sp)` — serializes full evaluation state to Excel workbook with separate sheets per data category
    - Implement `list_evaluations(sp)` — reads EvalIndex.xlsx for summary metadata
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 10.1, 10.2, 10.3, 10.4, 10.5, 12.2_

  - [x] 5.2 Implement option management in the evaluation service
    - Implement `add_option(evaluation_id, option, sp)` — validates 2-5 constraint (rejects 6th), appends to Options sheet, returns Option
    - Implement `update_option(evaluation_id, option_id, update, sp)` — updates name/description/vendor without affecting scores
    - Implement `remove_option(evaluation_id, option_id, sp)` — removes option and all associated scores + TCO data
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6_

  - [x] 5.3 Implement scoring and TCO submission in the evaluation service
    - Implement `submit_scores(evaluation_id, option_id, scores, sp)` — validates scores via scoring_matrix, stores dimension scores, computes weighted total, reports unscored dimensions
    - Implement `submit_tco(evaluation_id, option_id, tco_input, sp)` — validates costs via tco_calculator, stores TCO data, computes metrics
    - Implement `get_recommendation(evaluation_id, sp)` — ranks complete options, returns recommendation with top option highlighted
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.6_

  - [x] 5.4 Implement status determination and transition logic
    - Implement `determine_status(evaluation)` — returns Draft (no options), In_Progress (options but incomplete scoring/TCO), Scoring_Complete (all complete)
    - Implement `update_status(evaluation_id, new_status, sp)` — validates transitions, allows Archived from any status, allows Recommended from Scoring_Complete
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ]* 5.5 Write property tests for evaluation service
    - **Property 1: Intake validation accepts valid and rejects invalid inputs**
    - **Property 2: Created evaluations have unique IDs**
    - **Property 3: Option count constraint enforced**
    - **Property 4: Cascading option removal**
    - **Property 5: Editing option metadata preserves scores**
    - **Property 9: Score storage round-trip**
    - **Property 16: Evaluation persistence round-trip**
    - **Property 17: Status determination reflects evaluation completeness**
    - **Validates: Requirements 1.2, 1.3, 1.4, 2.1, 2.3, 2.4, 2.5, 2.6, 4.5, 10.7, 12.3, 12.4, 12.6**

- [x] 6. Implement Build vs Buy API Router
  - [x] 6.1 Create `app/routers/build_vs_buy.py` with evaluation CRUD endpoints
    - Implement `POST /api/build-vs-buy/evaluations` — create_evaluation with auth dependency
    - Implement `GET /api/build-vs-buy/evaluations` — list_evaluations with auth
    - Implement `GET /api/build-vs-buy/evaluations/{evaluation_id}` — get full evaluation detail
    - Implement `PATCH /api/build-vs-buy/evaluations/{evaluation_id}/status` — update lifecycle status
    - Apply `get_current_user` dependency to all endpoints
    - Apply role-based access control: Admin can view/edit/delete any; User can edit own, read-only others
    - _Requirements: 1.1, 1.3, 10.4, 10.5, 12.5, 14.1, 14.2, 14.3, 14.4, 14.5_

  - [x] 6.2 Add option management and scoring/TCO endpoints to the router
    - Implement `POST /api/build-vs-buy/evaluations/{evaluation_id}/options` — add option
    - Implement `PUT /api/build-vs-buy/evaluations/{evaluation_id}/options/{option_id}` — update option
    - Implement `DELETE /api/build-vs-buy/evaluations/{evaluation_id}/options/{option_id}` — remove option
    - Implement `PUT /api/build-vs-buy/evaluations/{evaluation_id}/options/{option_id}/scores` — submit scores
    - Implement `PUT /api/build-vs-buy/evaluations/{evaluation_id}/options/{option_id}/tco` — submit TCO
    - Validate minimum 2 options before allowing scoring progression
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 6.3 Register the router in `main.py`
    - Import `router as build_vs_buy_router` from `app.routers.build_vs_buy`
    - Add `app.include_router(build_vs_buy_router)` alongside existing routers
    - _Requirements: 14.1_

  - [ ]* 6.4 Write property tests for access control
    - **Property 18: Role-based access control enforcement**
    - **Validates: Requirements 14.2, 14.3, 14.4**

- [x] 7. Checkpoint - Backend core API functional
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement SLM-Assisted Vendor Proposal Analyzer
  - [x] 8.1 Create `app/services/proposal_analyzer.py` with SLM integration
    - Define `ProposalExtractionResult` dataclass with: proposed_costs, timeline_months, team_size, technology_stack, support_model, sla_commitments, risk_flags, suggested_scores, confidence
    - Define `ANALYSIS_PROMPT_TEMPLATE` with structured extraction instructions and JSON schema
    - Implement `analyze_proposal(file_content, filename, slm_engine)` — extracts text from PDF/DOCX via existing `document_processor`, sends to SLM with analysis prompt, parses JSON response into result
    - Handle SLM failures gracefully — return empty result with error flag, allowing manual scoring to proceed
    - Validate supported formats (PDF, DOCX) — return 415 for unsupported
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 8.2 Add proposal analysis endpoint to the router
    - Implement `POST /api/build-vs-buy/evaluations/{evaluation_id}/options/{option_id}/analyze-proposal` — accepts file upload, calls proposal_analyzer, maps suggested scores to option
    - Store SLM-suggested scores with source="slm_suggested" alongside manual scores
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ]* 8.3 Write unit tests for proposal analyzer
    - Test SLM failure returns graceful error with `error` field populated
    - Test PDF and DOCX format validation
    - Test suggested scores are within 1-5 range
    - _Requirements: 8.4, 8.5_

- [x] 9. Implement Audit Logging for BvB
  - [x] 9.1 Integrate audit logging into evaluation service
    - Log "evaluation_created" on create_evaluation with evaluation_id, user identity, timestamp
    - Log "evaluation_modified" on score/TCO/option changes with modification summary
    - Log "report_generated" on report export with report filename
    - Write audit entries to `BuildVsBuy/BvBAudit_YYYY-MM.xlsx` using existing audit_service patterns
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 10. Implement Frontend Evaluation Wizard and Dashboard
  - [x] 10.1 Add Build vs Buy navigation and wizard skeleton to `static/index.html`
    - Add "Build vs Buy" section to existing left-nav with sub-tabs: "New Evaluation" and "History"
    - Implement `BVB_STEPS` constant with 5 steps (Opportunity Intake, Define Options, Score Options, Enter TCO, Review Dashboard)
    - Implement `renderBvBWizard(step, evaluationData)` with progress indicator showing current step
    - Implement step navigation logic — allow backward navigation to completed steps, block forward past incomplete steps
    - _Requirements: 13.1, 13.2, 13.4, 13.5_

  - [x] 10.2 Implement Step 1: Opportunity Intake form
    - Render form with fields: opportunity_name, problem_statement, business_unit, budget_min, budget_max, target_decision_date
    - Add inline validation (name non-empty, budget_max >= budget_min, date required)
    - On submit call `POST /api/build-vs-buy/evaluations` and store returned evaluation_id
    - _Requirements: 1.1, 1.2, 13.4_

  - [x] 10.3 Implement Step 2: Define Options
    - Render option cards with add/edit/remove capability
    - Form fields: name, type (dropdown: Do_Nothing/Build/Buy/Extend), vendor_name (shown when type=Buy), description
    - Display option count indicator (min 2, max 5)
    - Block progression to Step 3 until at least 2 options defined
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 13.2_

  - [x] 10.4 Implement Step 3: Score Options
    - Render scoring grid: rows=dimensions (8), columns=options
    - Each cell is a 1-5 rating input (buttons or dropdown)
    - Display weighted total per option as scores are entered
    - Show completion indicator per option (scored vs unscored dimensions)
    - If SLM-suggested scores exist, display them as pre-filled suggestions with "accept/override" UX
    - Include "Upload Proposal" button per Buy-type option that triggers SLM analysis
    - _Requirements: 3.1, 3.3, 4.1, 4.2, 4.4, 8.2, 13.4_

  - [x] 10.5 Implement Step 4: Enter TCO
    - Render TCO input form per option with Year 0 costs (6 fields) and Year 1-5 recurring costs (9 fields each)
    - Allow partial entry (default unset fields to 0)
    - Display computed 3-Year TCO, 5-Year TCO, Annual Run Cost live as values are entered
    - Add optional user_count input per option for Cost per User calculation
    - _Requirements: 5.1, 5.2, 5.5, 6.1, 6.2, 6.3, 6.4, 13.4_

  - [x] 10.6 Implement Step 5: Executive Dashboard
    - Render radar chart comparing all options across 8 dimensions using Chart.js
    - Render ranked options table sorted by weighted total (descending)
    - Highlight top-ranked option as recommended choice
    - Render per-option summary cards with: name, type, weighted total, 3Y TCO, 5Y TCO, visual score bar
    - Show evaluation metadata header (opportunity name, owner, budget range, decision date)
    - Mark incomplete options with "Incomplete" badge, exclude from recommendation
    - Add "Export PDF Report" button triggering report generation
    - Add "Confirm Recommendation" button to transition status to Recommended
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 12.5_

  - [x] 10.7 Implement History view and evaluation restore
    - Render list of all evaluations from `GET /api/build-vs-buy/evaluations` with: name, status, owner, last modified
    - Clicking an evaluation loads it and restores wizard to appropriate step based on completeness
    - _Requirements: 10.4, 13.3_

- [x] 11. Checkpoint - Frontend wizard and dashboard functional
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implement Report Generator
  - [ ] 12.1 Create `app/services/bvb_report_generator.py` with PDF generation
    - Implement `generate_bvb_report(evaluation)` using reportlab — produces PDF with: header (date, owner, report ID), opportunity metadata, options summary table, scoring matrix with weighted totals, TCO comparison table, ranked recommendation, risk flags
    - Implement `_format_inr(amount)` — formats amounts in INR with lakhs/crores notation
    - Implement `_render_radar_chart_image(evaluation)` — renders radar chart as PNG for PDF embedding
    - Include "Data Completeness" section for evaluations with missing data
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 12.2 Add report endpoint and SharePoint storage
    - Implement `POST /api/build-vs-buy/evaluations/{evaluation_id}/report` in router — generates PDF, stores to SharePoint `BuildVsBuy/Reports/{id}_Report_{YYYY-MM-DD}.pdf`, logs audit event, returns report filename and URL
    - _Requirements: 9.5, 11.3_

  - [ ]* 12.3 Write property tests for report generation
    - **Property 15: INR formatting correctness**
    - **Validates: Requirements 9.3**

- [x] 13. Final checkpoint - Full feature integration
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- The design uses Python (FastAPI + reportlab + hypothesis) — all implementations follow existing project patterns
- The `FOLDER_BUILD_VS_BUY` constant already exists in the SharePoint client
- Existing services (`slm_engine.py`, `sharepoint_client.py`, `audit_service.py`, `document_processor.py`) are reused without modification
