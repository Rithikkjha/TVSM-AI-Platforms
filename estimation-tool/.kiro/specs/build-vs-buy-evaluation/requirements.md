# Requirements Document

## Introduction

The Build vs Buy Evaluation feature adds a structured digital investment decision platform to TVS PlanIQ. It enables teams to make evidence-based software investment decisions by comparing options (Build, Buy, Extend, Do Nothing) using a weighted Gartner-style scoring matrix and detailed Total Cost of Ownership (TCO) analysis. The tool produces objective, auditable recommendations with executive-friendly dashboards and exportable reports, leveraging the existing SLM (Ollama gemma3:4b) for AI-assisted vendor proposal analysis.

## Glossary

- **Evaluation_Engine**: The backend service responsible for orchestrating the Build vs Buy evaluation workflow including opportunity intake, option scoring, TCO calculation, and recommendation generation.
- **Scoring_Matrix**: The weighted scoring component that calculates composite scores across 8 dimensions for each evaluation option.
- **TCO_Calculator**: The component that computes 3-Year and 5-Year Total Cost of Ownership from structured cost inputs per option.
- **Option**: A candidate investment approach being evaluated (e.g., "Do Nothing", "Build In-House", "Buy Vendor A", "Buy Vendor B", "Extend Existing System").
- **Opportunity**: A business problem or need that requires a software investment decision, serving as the container for the entire evaluation.
- **Dimension**: One of the 8 scoring categories in the weighted matrix (Business Value, Technology Fit, Functional Fit, Financial, Operational Sustainability, Business Agility, Vendor Risk, AI Readiness).
- **SLM_Engine**: The inference service (`app/services/slm_engine.py`) that calls Ollama or OpenRouter for language model completions.
- **SharePoint_Client**: The persistence service (`app/services/sharepoint_client.py`) that manages read/write operations to SharePoint Excel files in the BuildVsBuy/ folder.
- **Dashboard_UI**: The frontend executive dashboard view that displays radar charts, ranked options, and the overall recommendation.
- **Report_Generator**: The component that produces PDF exports containing the evaluation comparison summary.
- **Audit_Service**: The existing audit logging service that tracks creation and modification events.

## Requirements

### Requirement 1: Opportunity Intake

**User Story:** As an evaluation user, I want to capture the business context for a software investment decision, so that the evaluation is grounded in a clearly defined problem, budget, and timeline.

#### Acceptance Criteria

1. THE Evaluation_Engine SHALL accept an opportunity intake containing: opportunity name, problem statement, business unit, budget range (min and max in INR), target decision date, and evaluation owner.
2. WHEN an opportunity intake is submitted, THE Evaluation_Engine SHALL validate that the opportunity name is non-empty and the budget max is greater than or equal to budget min.
3. WHEN an opportunity intake is submitted with valid data, THE Evaluation_Engine SHALL create a new evaluation record and return a unique evaluation ID.
4. IF an opportunity intake is submitted with invalid or missing required fields, THEN THE Evaluation_Engine SHALL return descriptive validation errors identifying each invalid field.
5. THE Evaluation_Engine SHALL store the opportunity intake metadata alongside the evaluation for audit and reporting purposes.

### Requirement 2: Option Management

**User Story:** As an evaluation user, I want to define 2 to 5 options for comparison, so that I can evaluate multiple investment approaches side by side.

#### Acceptance Criteria

1. THE Evaluation_Engine SHALL support defining between 2 and 5 options per evaluation.
2. WHEN an option is added to an evaluation, THE Evaluation_Engine SHALL accept: option name, option type (one of: Do_Nothing, Build, Buy, Extend), vendor name (required for Buy type), and a brief description.
3. IF a user attempts to add more than 5 options to an evaluation, THEN THE Evaluation_Engine SHALL reject the request with an error indicating the maximum has been reached.
4. IF a user attempts to proceed to scoring with fewer than 2 options defined, THEN THE Evaluation_Engine SHALL reject the request with an error indicating the minimum has not been met.
5. WHEN an option is removed from an evaluation, THE Evaluation_Engine SHALL also remove all associated scores and TCO data for that option.
6. THE Evaluation_Engine SHALL allow editing of option details (name, description, vendor name) after creation without affecting existing scores.

### Requirement 3: Weighted Scoring Matrix Configuration

**User Story:** As an evaluation user, I want to score options across 8 weighted dimensions using a Gartner-style matrix, so that the comparison is multi-dimensional and reflects organizational priorities.

#### Acceptance Criteria

1. THE Scoring_Matrix SHALL use the following default dimension weights: Business Value 20%, Technology Fit 15%, Functional Fit 15%, Financial 20%, Operational Sustainability 15%, Business Agility 5%, Vendor Risk 5%, AI Readiness 5%.
2. THE Scoring_Matrix SHALL validate that dimension weights sum to exactly 100%.
3. THE Scoring_Matrix SHALL accept scores on a 1-to-5 integer scale for each dimension per option, where 1 represents the lowest fit and 5 represents the highest fit.
4. WHEN all dimensions are scored for an option, THE Scoring_Matrix SHALL calculate the weighted total score as the sum of (score × weight) across all 8 dimensions.
5. FOR ALL valid scoring inputs, THE Scoring_Matrix SHALL produce weighted totals in the range 1.00 to 5.00 inclusive.
6. IF a score outside the 1-to-5 range is submitted, THEN THE Scoring_Matrix SHALL reject the input with a validation error.

### Requirement 4: Per-Option Scoring Workflow

**User Story:** As an evaluation user, I want to rate each option across all dimensions and see the calculated totals, so that I can identify the highest-scoring option objectively.

#### Acceptance Criteria

1. WHEN a user submits scores for an option, THE Evaluation_Engine SHALL store the individual dimension scores and compute the weighted total for that option.
2. THE Evaluation_Engine SHALL allow partial scoring (some dimensions scored, others pending) and indicate which dimensions remain unscored.
3. WHEN all options have complete scores across all dimensions, THE Evaluation_Engine SHALL rank options by weighted total in descending order.
4. THE Evaluation_Engine SHALL recalculate weighted totals immediately when any individual score is updated.
5. FOR ALL valid score submissions, storing scores then retrieving them SHALL return the identical dimension scores and computed weighted total (round-trip property).

### Requirement 5: TCO Cost Input Structure

**User Story:** As an evaluation user, I want to enter detailed cost breakdowns per option covering Year 0 through Year 5, so that the tool can calculate accurate multi-year TCO projections.

#### Acceptance Criteria

1. THE TCO_Calculator SHALL accept Year 0 (initial) costs per option including: license cost, implementation cost, migration cost, infrastructure cost, training cost, and consulting/professional services cost.
2. THE TCO_Calculator SHALL accept Year 1 through Year 5 recurring costs per option including: license renewal, cloud cost, infrastructure cost, storage cost, KTLO/people cost, vendor AMC (Annual Maintenance Contract), change request cost, upgrade cost, and support cost.
3. WHEN cost inputs are submitted, THE TCO_Calculator SHALL validate that all cost values are non-negative numbers.
4. IF a cost value is submitted as negative, THEN THE TCO_Calculator SHALL reject the input with a validation error identifying the invalid field.
5. THE TCO_Calculator SHALL allow partial cost entry (some fields populated, others defaulting to zero) to accommodate options where certain cost categories are not applicable.

### Requirement 6: TCO Calculation and Comparison

**User Story:** As an evaluation user, I want the tool to calculate 3-Year TCO, 5-Year TCO, Annual Run Cost, and Cost per User for each option, so that I can compare the financial impact across investment approaches.

#### Acceptance Criteria

1. THE TCO_Calculator SHALL compute 3-Year TCO as: Year 0 total + Year 1 costs + Year 2 costs + Year 3 costs (where Year 2 and Year 3 default to Year 1 values if not separately specified).
2. THE TCO_Calculator SHALL compute 5-Year TCO as: Year 0 total + sum of Year 1 through Year 5 costs (where unspecified years default to the last specified year's values).
3. THE TCO_Calculator SHALL compute Annual Run Cost as: average of Year 1 through Year 5 recurring costs (excluding Year 0 initial costs).
4. WHEN user count is provided for an option, THE TCO_Calculator SHALL compute Cost per User as: 5-Year TCO divided by user count.
5. FOR ALL valid TCO inputs, computing 3-Year TCO SHALL produce a value less than or equal to the 5-Year TCO for the same option.
6. THE TCO_Calculator SHALL present a side-by-side comparison of all options showing 3-Year TCO, 5-Year TCO, Annual Run Cost, and Cost per User.

### Requirement 7: Executive Dashboard and Recommendation

**User Story:** As a decision-maker, I want to see an executive dashboard with a clear recommendation, radar chart, and ranked options, so that I can make an informed investment decision quickly.

#### Acceptance Criteria

1. WHEN all options are fully scored and TCO is calculated, THE Dashboard_UI SHALL display a radar chart comparing all options across the 8 scoring dimensions.
2. THE Dashboard_UI SHALL display a ranked list of options sorted by weighted total score in descending order.
3. THE Dashboard_UI SHALL highlight the top-ranked option as the recommended choice.
4. THE Dashboard_UI SHALL display per-option summary cards showing: option name, type, weighted total score, 3-Year TCO, 5-Year TCO, and a visual score bar.
5. WHEN an option has incomplete scoring or TCO data, THE Dashboard_UI SHALL indicate the incomplete status and exclude that option from the recommendation ranking.
6. THE Dashboard_UI SHALL display the evaluation metadata (opportunity name, owner, budget range, decision date) in a header section.

### Requirement 8: SLM-Assisted Vendor Proposal Analysis

**User Story:** As an evaluation user, I want to upload vendor proposals and have the SLM extract key data points and flag risks, so that I can populate scoring dimensions with evidence-based data rather than subjective estimates.

#### Acceptance Criteria

1. WHEN a vendor proposal document is uploaded for an option, THE SLM_Engine SHALL extract key data points including: proposed cost, implementation timeline, team size, technology stack, support model, and SLA commitments.
2. WHEN vendor data points are extracted, THE Evaluation_Engine SHALL map extracted values to relevant scoring dimensions as suggested scores that the user can accept or override.
3. THE SLM_Engine SHALL identify and flag risks found in vendor proposals including: vendor lock-in indicators, hidden costs, unclear SLA terms, and technology deprecation risks.
4. IF the SLM_Engine fails to process a vendor document, THEN THE Evaluation_Engine SHALL return a graceful error message and allow the user to proceed with manual scoring.
5. THE SLM_Engine SHALL support PDF and DOCX document formats for vendor proposal upload.

### Requirement 9: Report Generation

**User Story:** As an evaluation user, I want to export a PDF report containing the complete evaluation comparison summary, so that I can share the analysis with stakeholders who do not have access to the tool.

#### Acceptance Criteria

1. WHEN a user requests a report export, THE Report_Generator SHALL produce a PDF document containing: opportunity metadata, options summary, scoring matrix with weighted totals, TCO comparison table, radar chart visualization, ranked recommendation, and risk flags.
2. THE Report_Generator SHALL include the evaluation date, owner name, and a unique report identifier in the document header.
3. THE Report_Generator SHALL format financial figures in INR with appropriate lakhs/crores notation.
4. IF an evaluation has incomplete data (missing scores or TCO for some options), THEN THE Report_Generator SHALL include a "Data Completeness" section noting which options have incomplete data.
5. WHEN a report is generated, THE Report_Generator SHALL store the generated report in SharePoint under the BuildVsBuy/ folder with a filename pattern: `{evaluation_id}_Report_{YYYY-MM-DD}.pdf`.

### Requirement 10: Persistence to SharePoint

**User Story:** As an evaluation user, I want evaluations to be saved to SharePoint, so that evaluation data is durable, shareable, and accessible for future reference.

#### Acceptance Criteria

1. THE SharePoint_Client SHALL persist evaluation data to the BuildVsBuy/ folder in SharePoint using Excel file format.
2. WHEN an evaluation is created, THE SharePoint_Client SHALL store opportunity metadata, options, scores, and TCO data in a structured Excel workbook with separate sheets for each data category.
3. WHEN an evaluation is updated (scores modified, options added/removed), THE SharePoint_Client SHALL update the corresponding Excel file in SharePoint.
4. THE SharePoint_Client SHALL support listing all evaluations from the BuildVsBuy/ folder with summary metadata (evaluation ID, opportunity name, status, last modified date).
5. THE SharePoint_Client SHALL support loading a complete evaluation by ID from SharePoint for viewing or continued editing.
6. IF SharePoint is unavailable during a write operation, THEN THE SharePoint_Client SHALL queue the write and retry upon reconnection (consistent with existing retry behavior).
7. FOR ALL valid evaluations, saving to SharePoint then loading by ID SHALL return data equivalent to the original evaluation state (round-trip property).

### Requirement 11: Audit Logging

**User Story:** As an administrator, I want all evaluation creation and modification events logged, so that I can track who made changes and when for governance purposes.

#### Acceptance Criteria

1. WHEN an evaluation is created, THE Audit_Service SHALL log an entry with: event type "evaluation_created", evaluation ID, user identity (corporate ID and display name), and timestamp.
2. WHEN an evaluation is modified (scores updated, options changed, TCO data entered), THE Audit_Service SHALL log an entry with: event type "evaluation_modified", evaluation ID, modification summary, user identity, and timestamp.
3. WHEN a report is generated, THE Audit_Service SHALL log an entry with: event type "report_generated", evaluation ID, report filename, user identity, and timestamp.
4. THE Audit_Service SHALL write audit log entries to the existing monthly AuditLog Excel file in the BuildVsBuy/ folder.

### Requirement 12: Evaluation Lifecycle and Status

**User Story:** As an evaluation user, I want evaluations to have a clear lifecycle status, so that I can track progress and distinguish between in-progress and completed evaluations.

#### Acceptance Criteria

1. THE Evaluation_Engine SHALL assign one of the following statuses to each evaluation: Draft, In_Progress, Scoring_Complete, Recommended, Archived.
2. WHEN an evaluation is first created, THE Evaluation_Engine SHALL set its status to Draft.
3. WHEN options are added and scoring begins, THE Evaluation_Engine SHALL transition the status to In_Progress.
4. WHEN all options have complete scores and TCO data, THE Evaluation_Engine SHALL transition the status to Scoring_Complete.
5. WHEN the user confirms the recommendation, THE Evaluation_Engine SHALL transition the status to Recommended.
6. THE Evaluation_Engine SHALL allow manual transition to Archived status from any other status.

### Requirement 13: Frontend Evaluation Workflow

**User Story:** As an evaluation user, I want a step-by-step guided workflow in the UI, so that I can complete the evaluation process without confusion about what to do next.

#### Acceptance Criteria

1. THE Dashboard_UI SHALL present the evaluation workflow as a multi-step process with clear progress indication: Step 1 Opportunity Intake, Step 2 Define Options, Step 3 Score Options, Step 4 Enter TCO, Step 5 Review Dashboard.
2. THE Dashboard_UI SHALL allow navigation between completed steps for editing while preventing forward navigation past incomplete steps.
3. WHEN an evaluation is loaded from SharePoint, THE Dashboard_UI SHALL restore the user to the appropriate step based on evaluation completeness.
4. THE Dashboard_UI SHALL provide inline validation feedback on each step before allowing progression to the next step.
5. THE Dashboard_UI SHALL render within the existing PlanIQ SPA layout (vanilla HTML/JS/CSS in static/index.html) consistent with other tool modules.

### Requirement 14: Access Control

**User Story:** As an administrator, I want evaluation access controlled by the existing SSO role system, so that only authorized users can create and modify evaluations.

#### Acceptance Criteria

1. THE Evaluation_Engine SHALL require authenticated SSO users for all evaluation operations (create, read, update, export).
2. WHILE a user has the Admin role, THE Evaluation_Engine SHALL allow that user to view, edit, and delete any evaluation.
3. WHILE a user has the User role, THE Evaluation_Engine SHALL allow that user to create new evaluations and edit only evaluations they own.
4. WHILE a user has the User role, THE Evaluation_Engine SHALL allow that user to view (read-only) evaluations created by others.
5. IF an unauthenticated request is received, THEN THE Evaluation_Engine SHALL return a 401 Unauthorized response.
