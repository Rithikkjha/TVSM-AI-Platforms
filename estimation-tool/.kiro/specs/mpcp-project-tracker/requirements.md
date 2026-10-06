# Requirements Document

## Introduction

The MPCP Project Tracker is a new module within TVS PlanIQ that provides hierarchical project tracking with drill-down navigation across Managing Points (MPs), Check Points (CPs), and Projects. Each project is tracked along two axes: a Process/SOP Track (8 lifecycle stages from BRD through to Production) and an Engineering Execution Track (sprint/milestone-level planned vs actual dates). The module uses a universal RAG (Red/Amber/Green) status system that propagates upward through the hierarchy using worst-child-wins logic, and provides an auto-derived Overview Dashboard aggregating health indicators across the portfolio. The tracker handles Fixed-bid projects, Special projects (Website 2.0, SPD, Ikarus, ICE Booking), Bugs, and Enhancements — all under the same MPCP hierarchy.

## Glossary

- **Tracker_Service**: The backend service responsible for managing the MPCP hierarchy, RAG status computation, and data persistence for project tracking operations.
- **MP (Managing_Point)**: A mid-level organizational unit in the hierarchy (e.g., A3, B1, C2) that belongs to an MP Theme and contains one or more Check Points. Uses alphanumeric codes like A1, A2, B1, B2, etc.
- **MP_Theme**: A top-level category tag on each MP for filtering/grouping. Fixed set: A - Customer Satisfaction, B - Profit & Profitability, C - Business Growth, D - New Product Development, E - Effectiveness of People & System, F - Digitalization & AI.
- **CP (Check_Point)**: A granular grouping under a Managing Point (e.g., A3.1, B1.4, C2.6) that contains one or more Projects.
- **Project**: A tracked work item under a Check Point, classified as one of: Fixed-bid, Special, Bug, or Enhancement.
- **Process_Track**: The 8-stage lifecycle track for a project consisting of: BRD, PRD, RFP, PO, Kickoff, Execution_Start, Rolled_Out_To_Prod, Success_Failure.
- **Execution_Track**: The sprint/milestone-level tracking of Planned Date vs Actual Date for engineering execution, typically vendor-driven.
- **RAG_Status**: A universal health indicator applied at every level of the hierarchy with values: Green (on track), Yellow (delayed/off track/pending clarity), or Red (blocked).
- **RAG_Context**: The mandatory supplemental information required when RAG status is Yellow or Red, using 3W1H format: What (the issue), Why (root cause), Who (person responsible/blocking), and How (action plan + ETA to resolve).
- **Overview_Dashboard**: The auto-derived top-level view showing aggregated counts by status, by PO, by vendor, and health indicators computed from the underlying tracker data.
- **Drill_Down_Navigator**: The frontend navigation component that enables hierarchical traversal from MP → CP → Project → Process Track / Execution Track.
- **SharePoint_Client**: The existing persistence service that manages read/write operations to SharePoint Excel files.
- **Audit_Service**: The existing audit logging service that tracks creation and modification events.
- **Product_Owner**: A designated person responsible for a set of projects. Known POs: Ashish Thakur, Akshay Bhosle, Prakash Bharati, Avinash Kumar, Bibin, Sumitra Rathod.
- **Vendor**: An external delivery partner executing project work. Known vendors: Exathought, Deloitte, TVSD, Evontech, Autovyn.
- **Line_of_Business (LoB)**: A business division tag applied to projects. Known LoBs: IND-2W, CMB, IB.

## Requirements

### Requirement 1: Managing Point (MP) Management

**User Story:** As a program manager, I want to create and manage Managing Points as top-level containers, so that I can organize the project portfolio into logical management groupings.

#### Acceptance Criteria

1. THE Tracker_Service SHALL allow creation of a Managing Point with: MP code (e.g., A3, B1, C2), MP name, MP Theme (one of: A - Customer Satisfaction, B - Profit & Profitability, C - Business Growth, D - New Product Development, E - Effectiveness of People & System, F - Digitalization & AI), MP owner, and Line of Business.
2. WHEN a Managing Point is created, THE Tracker_Service SHALL assign a unique MP identifier and set the initial RAG_Status to Green.
3. THE Tracker_Service SHALL pre-configure the following MP Themes as the fixed category list for tagging: A - Customer Satisfaction, B - Profit & Profitability, C - Business Growth, D - New Product Development, E - Effectiveness of People & System, F - Digitalization & AI.
4. THE Tracker_Service SHALL allow filtering/grouping all MPs by their MP Theme category.
5. THE Tracker_Service SHALL allow editing of MP code, MP name, MP Theme, MP owner, and Line of Business after creation.
6. THE Tracker_Service SHALL allow deletion of a Managing Point only when it contains zero Check Points.
7. IF a user attempts to delete a Managing Point that contains one or more Check Points, THEN THE Tracker_Service SHALL reject the request with an error indicating the MP must be emptied first.
8. THE Tracker_Service SHALL support listing all Managing Points with their current RAG_Status, MP Theme, Check Point count, and Project count (aggregated).

### Requirement 2: Check Point (CP) Management

**User Story:** As a program manager, I want to create and manage Check Points under Managing Points, so that I can group related projects within a management area.

#### Acceptance Criteria

1. THE Tracker_Service SHALL allow creation of a Check Point under a specified Managing Point with: CP code (e.g., A3.1, B1.4, C2.6), CP name, CP owner, and optional description.
2. WHEN a Check Point is created, THE Tracker_Service SHALL assign a unique CP identifier and set the initial RAG_Status to Green.
3. THE Tracker_Service SHALL validate that the CP code follows the pattern of parent MP code + decimal suffix (e.g., if parent MP is A3, valid CPs are A3.1, A3.2, etc.).
3. THE Tracker_Service SHALL allow editing of CP name, CP owner, and description after creation.
4. THE Tracker_Service SHALL allow deletion of a Check Point only when it contains zero Projects.
5. IF a user attempts to delete a Check Point that contains one or more Projects, THEN THE Tracker_Service SHALL reject the request with an error indicating the CP must be emptied first.
6. THE Tracker_Service SHALL support listing all Check Points under a given Managing Point with their current RAG_Status and Project count.

### Requirement 3: Project Management

**User Story:** As a project owner, I want to create and manage Projects under Check Points with classification metadata, so that all work items are tracked uniformly regardless of type.

#### Acceptance Criteria

1. THE Tracker_Service SHALL allow creation of a Project under a specified Check Point with: project name, project type (one of: Fixed_Bid, Special, Bug, Enhancement), assigned vendor, assigned Product Owner, Line of Business, and optional description.
2. WHEN a Project is created, THE Tracker_Service SHALL assign a unique Project identifier and set the initial RAG_Status to Green.
3. THE Tracker_Service SHALL validate that the assigned vendor is one of the configured vendor list (Exathought, Deloitte, TVSD, Evontech, Autovyn).
4. THE Tracker_Service SHALL validate that the assigned Product Owner is one of the configured PO list (Ashish Thakur, Akshay Bhosle, Prakash Bharati, Avinash Kumar, Bibin, Sumitra Rathod).
5. THE Tracker_Service SHALL allow editing of all project metadata fields after creation.
6. THE Tracker_Service SHALL allow deletion of a Project, removing all associated Process Track and Execution Track data.
7. THE Tracker_Service SHALL support listing all Projects under a given Check Point with their current RAG_Status, project type, vendor, and Product Owner.

### Requirement 4: Process/SOP Track Management

**User Story:** As a project owner, I want to track each project through 8 lifecycle stages with dates and status, so that I can monitor progress from BRD through to production rollout.

#### Acceptance Criteria

1. WHEN a Project is created, THE Tracker_Service SHALL initialize a Process Track with 8 stages in fixed order: BRD, PRD, RFP, PO, Kickoff, Execution_Start, Rolled_Out_To_Prod, Success_Failure.
2. THE Tracker_Service SHALL store for each Process Track stage: stage status (Not_Started, In_Progress, Completed, Skipped), planned completion date (optional), actual completion date (optional), and remarks (optional).
3. WHEN a stage status is updated to Completed, THE Tracker_Service SHALL require an actual completion date.
4. THE Tracker_Service SHALL enforce sequential stage progression: a stage cannot be marked In_Progress unless all preceding stages are either Completed or Skipped.
5. IF a user attempts to mark a stage In_Progress while a preceding stage is still Not_Started or In_Progress, THEN THE Tracker_Service SHALL reject the request with an error identifying the blocking stage.
6. THE Tracker_Service SHALL allow marking a stage as Skipped with a mandatory reason, and treat Skipped stages as non-blocking for subsequent stages.
7. THE Tracker_Service SHALL compute a current stage indicator showing which stage the project is currently at in the Process Track.

### Requirement 5: Engineering Execution Track Management

**User Story:** As a project owner, I want to track planned vs actual dates for each engineering milestone/sprint, so that I can monitor vendor delivery performance and identify slippage.

#### Acceptance Criteria

1. THE Tracker_Service SHALL allow adding milestones to a Project's Execution Track with: milestone name, planned start date, planned end date, and assigned vendor.
2. THE Tracker_Service SHALL allow updating milestone actual dates: actual start date and actual end date.
3. THE Tracker_Service SHALL compute slippage for each milestone as the difference in days between planned end date and actual end date (positive value indicates delay).
4. WHEN a milestone actual end date exceeds the planned end date, THE Tracker_Service SHALL flag the milestone as delayed.
5. THE Tracker_Service SHALL allow adding, editing, and removing milestones from the Execution Track without affecting other milestones.
6. THE Tracker_Service SHALL support listing all milestones for a given Project in chronological order by planned start date, showing planned dates, actual dates, slippage, and delay status.
7. THE Tracker_Service SHALL allow associating remarks with each milestone update for context on delays or changes.
8. THE Tracker_Service SHALL support bulk import of milestones from an uploaded Excel/CSV file with columns: Milestone Name, Vendor, Planned Start Date, Planned End Date.
9. WHEN a bulk import is submitted, THE Tracker_Service SHALL validate all rows (non-empty name, valid dates, planned end >= planned start) and reject the entire upload if any row is invalid, returning specific row-level errors.
10. THE Tracker_Service SHALL allow both ingestion methods: manual add (one milestone at a time via form) and bulk upload (multiple milestones via Excel/CSV file).

### Requirement 6: RAG Status Assignment and Context

**User Story:** As a project owner, I want to assign RAG status at every level with mandatory context for non-Green statuses, so that stakeholders always understand root causes and remediation plans for at-risk items.

#### Acceptance Criteria

1. THE Tracker_Service SHALL accept RAG_Status updates at MP, CP, Project, and Milestone levels with values: Green, Yellow, or Red.
2. WHEN RAG_Status is set to Yellow or Red, THE Tracker_Service SHALL require mandatory RAG_Context fields using the 3W1H format: What (description of the issue), Why (root cause), Who (person or team responsible/blocking), and How (action plan to resolve, including ETA).
3. IF a user attempts to set RAG_Status to Yellow or Red without providing all four 3W1H fields (What, Why, Who, How with ETA), THEN THE Tracker_Service SHALL reject the request with an error indicating which context fields are missing.
4. WHEN RAG_Status is set to Green, THE Tracker_Service SHALL clear any previously stored RAG_Context for that entity.
5. THE Tracker_Service SHALL store a history of RAG_Status changes for each entity including: previous status, new status, RAG_Context (if applicable), changed by (user identity), and timestamp.
6. THE Tracker_Service SHALL allow updating RAG_Context fields (Why, Path_to_Green, Owner, ETA) independently without changing the RAG_Status value.

### Requirement 7: RAG Status Propagation (Worst-Child-Wins)

**User Story:** As a program manager, I want RAG status to automatically propagate upward through the hierarchy using worst-child-wins logic, so that I can see aggregated health at any level without manual roll-up.

#### Acceptance Criteria

1. WHEN any Project's RAG_Status changes, THE Tracker_Service SHALL recompute the parent Check Point's propagated RAG_Status as the worst (highest severity) RAG_Status among all Projects under that Check Point.
2. WHEN any Check Point's propagated RAG_Status changes, THE Tracker_Service SHALL recompute the parent Managing Point's propagated RAG_Status as the worst (highest severity) RAG_Status among all Check Points under that Managing Point.
3. THE Tracker_Service SHALL define RAG severity ordering as: Green (lowest) < Yellow (middle) < Red (highest).
4. WHEN a CP or MP has no children, THE Tracker_Service SHALL retain the manually set RAG_Status without propagation override.
5. THE Tracker_Service SHALL distinguish between manually set RAG_Status and propagated RAG_Status, displaying both when they differ.
6. FOR ALL hierarchy configurations, propagating RAG_Status from the bottom level upward SHALL produce the same result regardless of the order in which child status changes are processed (confluence property).
7. WHEN any Milestone's RAG_Status changes, THE Tracker_Service SHALL recompute the parent Project's propagated RAG_Status as the worst RAG_Status among all Milestones in that Project's Execution Track.

### Requirement 8: Drill-Down Navigation

**User Story:** As a user, I want to navigate the hierarchy with drill-down and roll-up capability, so that I can view details at any level and traverse the structure intuitively.

#### Acceptance Criteria

1. THE Drill_Down_Navigator SHALL present the top-level view as a list of all Managing Points with their RAG_Status and summary metrics.
2. WHEN a user selects a Managing Point, THE Drill_Down_Navigator SHALL display all Check Points under that MP with their RAG_Status and project counts.
3. WHEN a user selects a Check Point, THE Drill_Down_Navigator SHALL display all Projects under that CP with their RAG_Status, project type, vendor, PO, and current Process Track stage.
4. WHEN a user selects a Project, THE Drill_Down_Navigator SHALL display the Project detail view with both Process Track and Execution Track accessible as tabs or sections.
5. THE Drill_Down_Navigator SHALL provide breadcrumb navigation showing the current position in the hierarchy (e.g., MP > CP > Project) with clickable links to parent levels.
6. THE Drill_Down_Navigator SHALL support keyboard navigation and maintain focus management for accessibility compliance.
7. THE Drill_Down_Navigator SHALL provide a flat "All Projects" view accessible directly from the dashboard or sidebar, listing all projects across the hierarchy with search and filters, allowing users to jump directly to any project without navigating through MP and CP levels.
8. THE flat project list SHALL display the full hierarchy path (MP > CP) as context for each project so the user knows where it sits.

### Requirement 9: Overview Dashboard

**User Story:** As a program manager, I want an auto-derived dashboard showing portfolio health at a glance, so that I can quickly identify problem areas and track overall delivery status.

#### Acceptance Criteria

1. THE Overview_Dashboard SHALL display total project counts grouped by RAG_Status (Green count, Yellow count, Red count).
2. THE Overview_Dashboard SHALL display project counts grouped by Product Owner, showing each PO's total projects and RAG breakdown.
3. THE Overview_Dashboard SHALL display project counts grouped by Vendor, showing each vendor's total projects and RAG breakdown.
4. THE Overview_Dashboard SHALL display project counts grouped by project type (Fixed_Bid, Special, Bug, Enhancement).
5. THE Overview_Dashboard SHALL display a Line of Business breakdown showing project count and RAG distribution per LoB.
6. THE Overview_Dashboard SHALL auto-derive all metrics from the current tracker data without requiring manual data entry for the dashboard.
7. WHEN any project's status or metadata changes, THE Overview_Dashboard SHALL reflect the updated metrics upon page refresh or data reload.
8. THE Overview_Dashboard SHALL highlight critical items: all Projects and CPs currently in Red status with their RAG_Context (Why, Owner, ETA) visible in a summary list.

### Requirement 10: Filtering and Search

**User Story:** As a user, I want to filter and search across the tracker hierarchy, so that I can quickly find specific projects or view subsets of data by vendor, PO, status, or type.

#### Acceptance Criteria

1. THE Tracker_Service SHALL support filtering projects by: RAG_Status, project type, vendor, Product Owner, and Line of Business.
2. THE Tracker_Service SHALL support combining multiple filter criteria with AND logic (e.g., Red status AND vendor Exathought).
3. THE Tracker_Service SHALL support text search by project name across the entire hierarchy, returning matching projects with their full hierarchy path (MP > CP > Project).
4. WHEN filters are applied, THE Overview_Dashboard SHALL recalculate all aggregated metrics to reflect only the filtered subset.
5. THE Drill_Down_Navigator SHALL maintain active filters when navigating between hierarchy levels.

### Requirement 11: Persistence to SharePoint

**User Story:** As a user, I want all tracker data persisted to SharePoint, so that project tracking information is durable, shareable, and consistent with the existing PlanIQ data architecture.

#### Acceptance Criteria

1. THE SharePoint_Client SHALL persist MPCP tracker data to a ProjectTracker/ folder in SharePoint using Excel file format.
2. THE SharePoint_Client SHALL store the hierarchy structure (MPs, CPs, Projects) in a master workbook with separate sheets for: MPs, CPs, Projects, ProcessTracks, ExecutionTracks, and RAGHistory.
3. WHEN any entity is created or updated, THE SharePoint_Client SHALL write the change to the corresponding SharePoint Excel file.
4. THE SharePoint_Client SHALL support loading the complete hierarchy from SharePoint for display in the frontend.
5. IF SharePoint is unavailable during a write operation, THEN THE SharePoint_Client SHALL queue the write and retry upon reconnection (consistent with existing retry behavior).
6. FOR ALL valid tracker data, saving to SharePoint then loading from SharePoint SHALL return data equivalent to the original state (round-trip property).

### Requirement 12: Audit Logging

**User Story:** As an administrator, I want all tracker modifications logged, so that I can track who made changes and when for governance and accountability.

#### Acceptance Criteria

1. WHEN any entity (MP, CP, Project) is created, THE Audit_Service SHALL log an entry with: event type, entity type, entity ID, user identity, and timestamp.
2. WHEN any entity is modified (metadata changed, RAG status updated, track data edited), THE Audit_Service SHALL log an entry with: event type, entity type, entity ID, modification summary, user identity, and timestamp.
3. WHEN any entity is deleted, THE Audit_Service SHALL log an entry with: event type "deleted", entity type, entity ID, user identity, and timestamp.
4. THE Audit_Service SHALL write audit log entries to the existing monthly AuditLog Excel file in the ProjectTracker/ folder.

### Requirement 13: Frontend Integration with PlanIQ

**User Story:** As a user, I want the MPCP Project Tracker accessible from the PlanIQ sidebar alongside existing modules, so that the tracking experience is integrated with the broader toolset.

#### Acceptance Criteria

1. THE Drill_Down_Navigator SHALL render within the existing PlanIQ SPA layout (vanilla HTML/JS/CSS in static/index.html) consistent with other tool modules.
2. THE Drill_Down_Navigator SHALL be accessible via a new "MPCP Tracker" entry in the existing left sidebar navigation.
3. THE Overview_Dashboard SHALL use the existing PlanIQ design patterns: metric cards, data tables, filters, and modals.
4. THE Drill_Down_Navigator SHALL support responsive layout for standard desktop viewport widths (1280px and above).
5. THE Tracker_Service SHALL expose RESTful API endpoints under `/api/mpcp-tracker/` following the existing FastAPI router pattern.

### Requirement 14: Access Control

**User Story:** As an administrator, I want tracker access controlled by the existing SSO role system, so that only authorized users can create and modify project tracking data.

#### Acceptance Criteria

1. THE Tracker_Service SHALL require authenticated SSO users for all tracker operations (create, read, update, delete).
2. WHILE a user has any authenticated role (Admin, User, or Partner), THE Tracker_Service SHALL allow that user to create, edit, and delete MPs, Check Points, and Projects, and to update RAG_Status, Process Track, Execution Track (milestones/tasks), and Dependencies across the hierarchy ("full contributor" model).
3. WHILE a user has the Partner role, THE Tracker_Service SHALL deny access to all Budget data (view and edit) and return 403 Forbidden; Admin and User roles retain full Budget access.
4. THE Tracker_Service SHALL allow all authenticated roles to view (read) all non-budget tracker data across the hierarchy.
5. IF an unauthenticated request is received, THEN THE Tracker_Service SHALL return a 401 Unauthorized response.

> **Note (updated):** The access model was changed from "Admin-only create/edit/delete" to a full-contributor model — any authenticated user (Admin, User, Partner) can create, edit, and delete hierarchy entities. The only role-based restriction remaining is that **Partner** users cannot see or modify Budget data (enforced by `require_budget_access`). This is implemented via `get_current_user` on all hierarchy/track endpoints and `require_budget_access` on budget endpoints in `app/routers/mpcp_tracker.py`.


### Requirement 15: Execution Tracker Visualization

**User Story:** As a project owner, I want to see a horizontal timeline bar visualization alongside the milestone table, so that I can visually assess project progress and overlaps at a glance.

#### Acceptance Criteria

1. THE Drill_Down_Navigator SHALL render a horizontal timeline bar chart above the milestone table in the Execution Track view, showing each milestone as a proportional bar on a time axis.
2. THE timeline visualization SHALL display planned dates as blue bars and actual dates as overlaid green (on-track) or red (delayed) bars.
3. THE timeline visualization SHALL auto-scale the time axis based on the earliest planned start and latest planned end across all milestones in the project.
4. WHEN a milestone has no actual dates, THE timeline visualization SHALL show only the planned bar in blue.
5. THE timeline visualization SHALL be rendered using pure CSS (proportional widths based on date ranges) without external charting libraries.
6. THE timeline visualization SHALL be responsive and horizontally scrollable on narrower viewports.

### Requirement 16: Export and Download

**User Story:** As a program manager, I want to download the tracker data as a formatted Excel file, so that I can share status with stakeholders who don't have tool access.

#### Acceptance Criteria

1. THE Tracker_Service SHALL provide an export endpoint that generates a formatted Excel workbook containing: Overview sheet (RAG summary, counts by vendor/PO/type), MP-CP hierarchy sheet, Projects sheet (all projects with current process stage and RAG), and Execution sheet (all milestones with planned vs actual).
2. THE export SHALL support filtering — if filters are active in the UI, the export SHALL include only the filtered subset.
3. THE export SHALL apply conditional formatting: Green/Yellow/Red cell colors for RAG status columns.
4. THE Drill_Down_Navigator SHALL provide a "Download Report" button that triggers the export and downloads the Excel file to the user's browser.
5. THE export filename SHALL include the current date (e.g., MPCP_Tracker_Report_2026-07-06.xlsx).
6. THE Tracker_Service SHALL provide a "Download 3W1H Report" option that exports all projects with Yellow or Red RAG status as an Excel file containing: Project Name, MP, CP, RAG Status, What, Why, Who, How, ETA — filterable by RAG (Yellow only, Red only, or both).

### Requirement 17: Weekly Email Report

**User Story:** As a program manager, I want an automated weekly email summarizing portfolio health, so that stakeholders receive regular updates without needing to log into the tool.

#### Acceptance Criteria

1. THE Tracker_Service SHALL provide a `/api/mpcp-tracker/weekly-report` endpoint that generates and sends an HTML email report via Microsoft Graph API (using existing SharePoint service account credentials).
2. THE weekly report email SHALL contain: overall RAG breakdown (count of Green/Yellow/Red projects), a list of all Red items with Why + Owner + ETA, a list of all Yellow items with Why + Owner + ETA, and top 5 milestone slippages of the week.
3. THE weekly report email SHALL include a direct link back to TVS PlanIQ MPCP Tracker for detailed view.
4. THE Tracker_Service SHALL support configuring email recipients (to, cc) via the admin settings.
5. THE weekly report SHALL be triggerable on-demand via a "Send Report Now" button in the UI, and schedulable via an external cron/scheduler calling the endpoint.
6. IF no Red or Yellow items exist, THE weekly report SHALL indicate "All projects on track" with the Green count.


### Requirement 18: Project Dependencies Tracking

**User Story:** As a project owner, I want to track external dependencies with their owners, cutoff dates, and resolution status, so that leadership can see what's blocked and escalate where needed.

#### Acceptance Criteria

1. THE Tracker_Service SHALL allow adding dependencies to a Project or to a specific Milestone within a Project, with: dependency description, external owner (person or team responsible), cutoff date (date by which it must be resolved), raised date, and status (Open, WIP, Resolved, Escalated).
2. WHEN a dependency is linked to a specific milestone, THE Tracker_Service SHALL display it in the context of that milestone in the Execution Track view.
3. THE Execution Track milestone table SHALL show a visual indicator (link icon with count) next to any milestone that has linked dependencies, color-coded red if any linked dependency is overdue, blue otherwise.
4. THE indicator SHALL display the linked dependency names and statuses on hover/click, providing bidirectional visibility (dependency → milestone from the Dependencies tab, and milestone → dependency from the Execution Track tab).
2. THE Tracker_Service SHALL allow updating dependency status and adding a resolved date when marked as Resolved.
3. WHEN a dependency's cutoff date passes and status is not Resolved, THE Tracker_Service SHALL flag it as overdue with a visual indicator.
4. THE Tracker_Service SHALL display overdue dependencies prominently in the project detail view and roll them up to the Overview Dashboard critical items section.
5. THE Tracker_Service SHALL allow marking a dependency as "Escalated" with an escalation note, indicating leadership intervention is needed.
6. THE Overview_Dashboard SHALL include an "Open Dependencies" section listing all unresolved dependencies across all projects, sorted by cutoff date (most urgent first), showing: project name, dependency, owner, cutoff date, days overdue (if any).
7. THE weekly email report SHALL include overdue and escalated dependencies with their owners and cutoff dates.
8. THE Tracker_Service SHALL allow adding, editing, and removing dependencies without affecting milestones or process track data.


### Requirement 19: Domain Grouping (Shop/Buy/Own/D2C)

**User Story:** As a program manager, I want to tag and group projects by business domain (Shop, Buy, Own) and stream (D2C, Channel Partner), so that I can view portfolio health from a domain perspective alongside the MPCP hierarchy.

#### Acceptance Criteria

1. THE Tracker_Service SHALL allow assigning a Domain tag (Shop, Buy, Own, Parts) and a Stream tag (D2C, Channel Partner, Platform Services) to each Project and Check Point.
2. THE Overview_Dashboard SHALL support grouping/filtering by Domain (Shop, Buy, Own, Parts) and Stream (D2C, Channel Partner, Platform Services) in addition to existing filters (RAG, Vendor, PO, Type).
3. THE Overview_Dashboard SHALL display a quick-filter bar directly below the metric cards with dropdowns for: Stream (CP/D2C/Platform), Domain (Shop/Buy/Own/Parts), RAG status, and a text search field — allowing users to filter the entire dashboard view without navigating away.
3. THE Drill_Down_Navigator SHALL display Domain and Stream tags visually on project rows in all list views.
4. THE weekly report SHALL include a domain-wise breakdown showing project counts and RAG distribution per domain.
5. THE Overview_Dashboard SHALL display a "By Domain" summary table showing Domain × BU × Stream (D2C/CP) combinations with project count, Green/Yellow/Red breakdown, and overall health RAG per row.

### Requirement 20: Slippage Auto-Calculation, Totals, and Fast-Track Override

**User Story:** As a project owner, I want the system to auto-calculate per-milestone slippage and project total slippage, with the ability to manually override the final date to commit to fast-tracking, so that I can see cumulative delay impact and set revised delivery targets.

#### Acceptance Criteria

1. THE Tracker_Service SHALL auto-compute slippage for each milestone as: (actual_end_date - planned_end_date) in days. Positive = delayed, negative = ahead of schedule, null = not yet completed.
2. THE Execution Track view SHALL display a summary row at the bottom showing: total planned duration, total actual duration (so far), and cumulative slippage (sum of completed milestone slippages).
3. THE Tracker_Service SHALL allow the Project Owner to set a "Revised Target Date" at the project level, which overrides the last milestone's planned end date to indicate a fast-track commitment.
4. WHEN a Revised Target Date is set that is earlier than the original last milestone planned end, THE Tracker_Service SHALL display the difference as "Fast-track: X days recovered" alongside the cumulative slippage.
5. THE Execution Track view SHALL visually distinguish planned dates (displayed in blue/gray) from actual dates (displayed in green if on time, red if delayed) using color-coding in both the milestone table and the Gantt timeline.
6. THE milestone table SHALL display planned dates in a neutral color and actual dates in bold with green (#2e7d32) for on-time or red (#c62828) for delayed, making them immediately distinguishable at a glance.
7. THE Execution Track view SHALL provide a "Download Plan" button that exports the project's milestone data (planned dates, actual dates, slippage, RAG, dependencies) as an Excel file for sharing with vendors or stakeholders offline.


### Requirement 21: Project Budget Tracking

**User Story:** As a program manager, I want to track budget allocation and consumption for each project, so that I can monitor financial health and identify cost overruns early.

#### Acceptance Criteria

1. THE Tracker_Service SHALL allow recording budget data for each project with the following fields: Internal Estimate (₹, the initial estimate by TVS internal team), Approved Budget (₹, the amount allotted/sanctioned), Vendor Proposal (₹, the cost from the vendor's proposal/SOW), Amount Exhausted (₹, spent so far), and Remarks.
2. THE Tracker_Service SHALL auto-compute: Remaining Budget (Approved Budget - Amount Exhausted) and Variance (Vendor Proposal - Internal Estimate).
3. WHEN Amount Exhausted exceeds Approved Budget, THE Tracker_Service SHALL flag the project as "Over Budget" with a visual indicator (red).
4. WHEN Amount Exhausted exceeds 80% of Approved Budget but is below 100%, THE Tracker_Service SHALL flag the project as "Budget At Risk" with a visual indicator (yellow).
5. THE Project Detail view SHALL display a "Budget" tab or section showing: Internal Estimate, Approved Budget, Vendor Proposal, Amount Exhausted, Remaining, and a progress bar indicating % utilized.
6. THE Overview_Dashboard SHALL include a budget summary card showing: Total Approved Budget (sum across all projects), Total Exhausted, Total Remaining, and count of over-budget projects.
7. THE export report SHALL include a Budget sheet with per-project financial data (Internal Estimate, Approved, Vendor Proposal, Exhausted, Remaining, % Utilized, Status).
8. THE Tracker_Service SHALL allow updating Amount Exhausted incrementally (adding spend entries) or by overwriting the total, with audit trail of changes.


### Requirement 22: Business Unit (BU) Switcher

**User Story:** As a program manager, I want to switch between Business Units (IND-2W, 3W/CMB, IB) at the top level, so that I can view MPCP data scoped to a specific BU or across all BUs.

#### Acceptance Criteria

1. THE Drill_Down_Navigator SHALL display a persistent BU switcher bar at the top of the tracker (above dashboard/content) with options: All, IND-2W, 3W/CMB, IB.
2. WHEN a BU is selected, THE entire tracker view (Dashboard, MP list, CP list, Project list, All Projects) SHALL filter to show only data belonging to that BU.
3. WHEN "All" is selected, THE tracker SHALL show the combined portfolio across all BUs.
4. THE BU selection SHALL persist across navigation within the tracker (drilling from MP → CP → Project retains the BU context).
5. THE Overview_Dashboard metrics SHALL recalculate based on the active BU filter (total projects, RAG counts, vendor/PO breakdowns, budget, dependencies — all scoped to the selected BU).
6. THE weekly email report SHALL support BU-specific reports (one per BU) or a consolidated "All" report, configurable by admin.
7. THE BU switcher SHALL be visually prominent (pill-style toggle or tab bar) and indicate the currently active BU clearly.
