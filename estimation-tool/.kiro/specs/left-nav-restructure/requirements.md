# Requirements Document

## Introduction

This feature restructures the Project Estimation Tool's navigation from a single top navigation bar to a two-tier layout: a persistent left sidebar for primary sections and a contextual top navigation bar for sub-pages within each section. The restructure introduces a clearer information hierarchy, groups related functionality under distinct sections, and accommodates future feature additions (PRD Completeness, Build vs Buy) via placeholder pages. All existing functionality must be preserved with backward-compatible URL routing.

## Glossary

- **Left_Sidebar**: The persistent vertical navigation panel on the left side of the viewport containing primary section links with icons and labels.
- **Top_Nav**: The horizontal bar at the top of the viewport displaying the application logo, contextual sub-navigation links for the active section, and user information.
- **Section**: A primary grouping in the Left_Sidebar (Estimate Project, PRD Completeness, Compare Vendors, Build vs Buy, Settings).
- **Sub_Page**: A page accessible from the Top_Nav that belongs to a specific Section.
- **Router**: The client-side hash-based routing system that maps URL fragments to page views.
- **Collapsed_Mode**: The Left_Sidebar display mode on mobile viewports where only icons are shown (60px width).
- **Expanded_Mode**: The Left_Sidebar display mode on desktop viewports where icons and labels are shown (200px width).
- **Placeholder_Page**: A minimal page with a title and "Coming Soon" message for features not yet implemented.

## Requirements

### Requirement 1: Left Sidebar Layout

**User Story:** As a user, I want a persistent left sidebar navigation, so that I can quickly switch between primary tool sections without losing context.

#### Acceptance Criteria

1. THE Left_Sidebar SHALL display five navigation items in this order: Estimate Project (📊), PRD Completeness (📋), Compare Vendors (🔄), Build vs Buy (⚖️), Settings (⚙️).
2. THE Left_Sidebar SHALL be visible on all pages of the application.
3. THE Left_Sidebar SHALL have a width of 200px in Expanded_Mode.
4. THE Left_Sidebar SHALL occupy the full height of the viewport.
5. THE Left_Sidebar SHALL have a background color of #1a237e with white icon and label text.
6. WHEN a user clicks a Section item in the Left_Sidebar, THE Router SHALL navigate to the default Sub_Page of that Section.
7. WHILE a Section is active, THE Left_Sidebar SHALL highlight the active Section item with a lighter background (rgba(255,255,255,0.15)).

### Requirement 2: Contextual Top Navigation

**User Story:** As a user, I want the top navigation to show sub-pages relevant to the section I'm in, so that I can navigate within a section without confusion.

#### Acceptance Criteria

1. WHEN the Estimate Project section is active, THE Top_Nav SHALL display sub-navigation links: Dashboard, New Estimation, Audit Log.
2. WHEN the PRD Completeness section is active, THE Top_Nav SHALL display a sub-navigation link: Check Document.
3. WHEN the Compare Vendors section is active, THE Top_Nav SHALL display sub-navigation links: Compare, History.
4. WHEN the Build vs Buy section is active, THE Top_Nav SHALL display sub-navigation links: Evaluate, History.
5. WHEN the Settings section is active, THE Top_Nav SHALL display sub-navigation links: Users, Config, Templates.
6. THE Top_Nav SHALL display the application logo on the left side and user information on the right side.
7. WHILE a Sub_Page is active, THE Top_Nav SHALL highlight the active sub-navigation link.

### Requirement 3: Responsive Left Sidebar (Mobile)

**User Story:** As a mobile user, I want the sidebar to collapse to icons only, so that I have more screen space for content while retaining navigation access.

#### Acceptance Criteria

1. WHEN the viewport width is 768px or less, THE Left_Sidebar SHALL display in Collapsed_Mode with a width of 60px.
2. WHILE in Collapsed_Mode, THE Left_Sidebar SHALL display only icons without text labels.
3. WHEN the viewport width exceeds 768px, THE Left_Sidebar SHALL display in Expanded_Mode with icons and text labels.
4. THE Left_Sidebar SHALL transition between Collapsed_Mode and Expanded_Mode with a smooth CSS transition.

### Requirement 4: Hash-Based URL Routing Extension

**User Story:** As a user, I want clean URL routes that reflect the navigation hierarchy, so that I can bookmark and share links to specific pages.

#### Acceptance Criteria

1. THE Router SHALL support the following hash routes for Estimate Project: #estimate/dashboard, #estimate/new, #estimate/results/:id, #estimate/re-estimate/:id, #estimate/audit-log.
2. THE Router SHALL support the following hash route for PRD Completeness: #prd-check.
3. THE Router SHALL support the following hash routes for Compare Vendors: #vendors, #vendors/history.
4. THE Router SHALL support the following hash routes for Build vs Buy: #build-vs-buy, #build-vs-buy/history.
5. THE Router SHALL support the following hash routes for Settings: #settings/users, #settings/config, #settings/templates.
6. WHEN a user navigates to the legacy route #dashboard, THE Router SHALL redirect to #estimate/dashboard.
7. WHEN a user navigates to the legacy route #new-estimation, THE Router SHALL redirect to #estimate/new.
8. WHEN a user navigates to the legacy route #results/:id, THE Router SHALL redirect to #estimate/results/:id.
9. WHEN a user navigates to the legacy route #vendor-compare, THE Router SHALL redirect to #vendors.
10. WHEN a user navigates to the legacy route #vendor-compare/:id, THE Router SHALL redirect to #vendors.
11. WHEN a user navigates to the legacy route #audit-log, THE Router SHALL redirect to #estimate/audit-log.
12. WHEN a user navigates to the legacy route #admin, THE Router SHALL redirect to #settings/users.
13. WHEN a user navigates to the legacy route #re-estimate/:id, THE Router SHALL redirect to #estimate/re-estimate/:id.

### Requirement 5: Existing Functionality Preservation

**User Story:** As a user, I want all existing estimation features to work exactly as before, so that the navigation restructure does not break my workflow.

#### Acceptance Criteria

1. THE Router SHALL render the existing Dashboard page content when navigating to #estimate/dashboard.
2. THE Router SHALL render the existing New Estimation wizard when navigating to #estimate/new.
3. THE Router SHALL render the existing Results detail page when navigating to #estimate/results/:id.
4. THE Router SHALL render the existing Re-Estimate page when navigating to #estimate/re-estimate/:id.
5. THE Router SHALL render the existing Vendor Compare page when navigating to #vendors.
6. THE Router SHALL render the existing Audit Log page when navigating to #estimate/audit-log.
7. THE Router SHALL render the existing Admin page content when navigating to #settings/users.
8. THE Router SHALL preserve all existing page functionality including form submissions, data loading, and interactive elements.

### Requirement 6: Placeholder Pages for New Sections

**User Story:** As a product owner, I want placeholder pages for upcoming features, so that the navigation structure is ready for future development.

#### Acceptance Criteria

1. WHEN a user navigates to #prd-check, THE Router SHALL display a Placeholder_Page with the title "PRD Completeness" and a description of the feature.
2. WHEN a user navigates to #build-vs-buy, THE Router SHALL display a Placeholder_Page with the title "Build vs Buy" and a description of the feature.
3. WHEN a user navigates to #vendors/history, THE Router SHALL display a Placeholder_Page with the title "Comparison History".
4. WHEN a user navigates to #build-vs-buy/history, THE Router SHALL display a Placeholder_Page with the title "Evaluation History".
5. WHEN a user navigates to #settings/config, THE Router SHALL display a Placeholder_Page with the title "Configuration".
6. WHEN a user navigates to #settings/templates, THE Router SHALL display a Placeholder_Page with the title "Templates".
7. THE Placeholder_Page SHALL display a "Coming Soon" indicator and a brief description of the planned functionality.

### Requirement 7: Layout Structure

**User Story:** As a user, I want a well-organized layout with clear content areas, so that I can focus on the task at hand.

#### Acceptance Criteria

1. THE Left_Sidebar SHALL be positioned fixed on the left side of the viewport.
2. THE Top_Nav SHALL be positioned to the right of the Left_Sidebar and at the top of the remaining viewport.
3. THE main content area SHALL occupy the space to the right of the Left_Sidebar and below the Top_Nav.
4. THE Top_Nav SHALL retain the existing gradient background (linear-gradient(135deg, #1a237e, #3949ab)).
5. THE Left_Sidebar SHALL have smooth hover transitions on navigation items (transition duration of 0.2s).
6. WHEN a user hovers over a Left_Sidebar navigation item, THE Left_Sidebar SHALL display the item with a subtle background highlight (rgba(255,255,255,0.1)).

### Requirement 8: Section Default Routes

**User Story:** As a user, I want clicking a section in the left nav to take me to a sensible default page, so that I don't land on an empty view.

#### Acceptance Criteria

1. WHEN a user clicks the Estimate Project item in the Left_Sidebar, THE Router SHALL navigate to #estimate/dashboard.
2. WHEN a user clicks the PRD Completeness item in the Left_Sidebar, THE Router SHALL navigate to #prd-check.
3. WHEN a user clicks the Compare Vendors item in the Left_Sidebar, THE Router SHALL navigate to #vendors.
4. WHEN a user clicks the Build vs Buy item in the Left_Sidebar, THE Router SHALL navigate to #build-vs-buy.
5. WHEN a user clicks the Settings item in the Left_Sidebar, THE Router SHALL navigate to #settings/users.
6. WHEN a user navigates to the application root (empty hash or #), THE Router SHALL navigate to #estimate/dashboard.
