# Implementation Plan: Left Nav Restructure

## Overview

Restructure the Project Estimation Tool's navigation in `static/index.html` from a single top nav bar to a two-tier layout: a persistent left sidebar for primary sections and a contextual top nav for sub-pages. All changes are within the single `static/index.html` file (CSS, HTML, and JS). Each task is incremental and testable independently.

## Tasks

- [-] 1. Add left sidebar CSS styles and layout adjustments
  - [x] 1.1 Add `.left-sidebar` CSS rules (fixed position, 200px width, full height, #1a237e background, z-index: 101, flex column, transition)
    - Add `.sidebar-nav`, `.sidebar-item` styles (flex row, gap, padding, color rgba(255,255,255,0.75), cursor pointer)
    - Add `.sidebar-item:hover` (background rgba(255,255,255,0.1), color white)
    - Add `.sidebar-item.active` (background rgba(255,255,255,0.15), color white)
    - Add `.sidebar-icon` and `.sidebar-label` styles
    - _Requirements: 1.3, 1.4, 1.5, 7.1, 7.5, 7.6_

  - [x] 1.2 Adjust existing `.header` CSS to sit right of sidebar
    - Add `margin-left: 200px` to `.header`
    - Verify existing gradient background (linear-gradient(135deg, #1a237e, #3949ab)) is preserved
    - _Requirements: 7.2, 7.4_

  - [x] 1.3 Adjust `.container` / main content area CSS
    - Add `margin-left: 200px` to the container/body content area
    - Ensure main content occupies space right of sidebar and below top nav
    - _Requirements: 7.3_

  - [x] 1.4 Add responsive CSS for sidebar collapse at ≤768px
    - Add `@media (max-width: 768px)` rule: `.left-sidebar { width: 60px }`
    - Hide `.sidebar-label` in collapsed mode (`display: none` or `opacity: 0`)
    - Adjust `.header` and content `margin-left` to `60px` in media query
    - Add smooth CSS transition for width change (transition: width 0.3s ease)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 1.5 Add placeholder page CSS
    - Add `.placeholder-card` styles (centered content, appropriate spacing)
    - Add `.coming-soon` indicator styles (visible badge or label)
    - _Requirements: 6.7_

- [ ] 2. Add HTML structure for left sidebar and placeholder pages
  - [x] 2.1 Add left sidebar HTML structure
    - Insert `<nav class="left-sidebar" id="left-sidebar">` with `.sidebar-nav` container
    - Add 5 `<a class="sidebar-item">` elements with `data-section` attributes: estimate, prd, vendors, build-vs-buy, settings
    - Each item has `.sidebar-icon` span (📊, 📋, 🔄, ⚖️, ⚙️) and `.sidebar-label` span
    - Each item has `onclick="navigateTo('...')"` pointing to section default route
    - _Requirements: 1.1, 1.2, 1.6, 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 2.2 Modify existing header HTML for contextual sub-nav
    - Ensure `<div class="nav-links" id="sub-nav-links">` exists in header for dynamic population
    - Keep logo/title on left and user info on right
    - _Requirements: 2.6_

  - [x] 2.3 Add placeholder page divs for new sections
    - Add `<div class="page" id="page-prd-check">` with title "PRD Completeness", description, and "Coming Soon" indicator
    - Add `<div class="page" id="page-build-vs-buy">` with title "Build vs Buy", description, and "Coming Soon" indicator
    - Add `<div class="page" id="page-vendors-history">` with title "Comparison History" and "Coming Soon" indicator
    - Add `<div class="page" id="page-build-vs-buy-history">` with title "Evaluation History" and "Coming Soon" indicator
    - Add `<div class="page" id="page-settings-config">` with title "Configuration" and "Coming Soon" indicator
    - Add `<div class="page" id="page-settings-templates">` with title "Templates" and "Coming Soon" indicator
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [ ] 3. Checkpoint - Verify CSS and HTML structure
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement JS routing logic and nav state management
  - [x] 4.1 Add SECTION_CONFIG and LEGACY_ROUTES constants
    - Define `SECTION_CONFIG` object with keys: estimate, prd, vendors, build-vs-buy, settings
    - Each section has: label, icon, defaultRoute, subNav array of {label, route}
    - Define `LEGACY_ROUTES` map for exact-match legacy redirects (dashboard → #estimate/dashboard, new-estimation → #estimate/new, audit-log → #estimate/audit-log, admin → #settings/users)
    - Define `LEGACY_PATTERNS` array for pattern-based redirects (results/:id, re-estimate/:id, vendor-compare, vendor-compare/:id)
    - _Requirements: 4.6, 4.7, 4.8, 4.9, 4.10, 4.11, 4.12, 4.13_

  - [x] 4.2 Implement `getActiveSection(hash)` function
    - Return section key based on hash prefix: estimate/* → 'estimate', prd-check → 'prd', vendors/* → 'vendors', build-vs-buy/* → 'build-vs-buy', settings/* → 'settings'
    - Default to 'estimate' for unknown routes
    - _Requirements: 1.7, 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 4.3 Implement `getSubNavItems(section)` and `updateNavState(section, hash)` functions
    - `getSubNavItems` returns the subNav array from SECTION_CONFIG for the given section
    - `updateNavState` updates: sidebar active highlight (add/remove .active class based on data-section), top nav sub-links (populate #sub-nav-links), active sub-nav link highlight
    - _Requirements: 1.7, 2.7_

  - [x] 4.4 Implement `resolveLegacyRoute(hash)` function
    - Check exact matches against LEGACY_ROUTES
    - Check regex patterns in LEGACY_PATTERNS, preserving :id parameters
    - Return new route string or null if not a legacy route
    - _Requirements: 4.6, 4.7, 4.8, 4.9, 4.10, 4.11, 4.12, 4.13_

  - [x] 4.5 Extend the `router()` function with new route resolution
    - Strip '#' from hash, check for legacy redirect first (call resolveLegacyRoute)
    - If legacy route found, call `navigateTo(newRoute)` and return
    - Match hash against new route patterns to determine page ID
    - Show correct page div (add .active, hide others)
    - Call `updateNavState()` to sync sidebar and top nav
    - Handle empty hash / root → redirect to #estimate/dashboard
    - Preserve existing admin role guard for settings routes
    - Handle unknown routes → default to #estimate/dashboard
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 8.6_

  - [ ]* 4.6 Write property test: Route-to-UI-state consistency (Property 1)
    - **Property 1: Route-to-UI-state consistency**
    - For any valid hash route, verify getActiveSection returns correct section AND getSubNavItems returns correct sub-nav for that section
    - Use fast-check to generate valid route strings from all defined routes
    - **Validates: Requirements 1.7, 2.1, 2.2, 2.3, 2.4, 2.5, 2.7**

  - [ ]* 4.7 Write property test: Route resolution correctness (Property 2)
    - **Property 2: Route resolution correctness**
    - For any valid new-format hash route (including random IDs for parameterized routes), verify the router resolves to exactly one page ID
    - Use fast-check to generate arbitrary ID strings for parameterized routes
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

  - [ ]* 4.8 Write property test: Legacy route redirect preservation (Property 3)
    - **Property 3: Legacy route redirect preservation**
    - For any legacy-format hash (including those with arbitrary IDs), verify resolveLegacyRoute returns the correct new-format route with ID preserved
    - Use fast-check to generate random ID strings for parameterized legacy routes
    - **Validates: Requirements 4.6, 4.7, 4.8, 4.9, 4.10, 4.11, 4.12, 4.13**

- [ ] 5. Checkpoint - Verify routing logic
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Integration and wiring
  - [ ] 6.1 Wire sidebar clicks to router and verify section defaults
    - Confirm each sidebar item navigateTo call triggers correct default route
    - Confirm root/empty hash redirects to #estimate/dashboard
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ] 6.2 Wire existing pages to new routes and verify preservation
    - Map existing page IDs to new route patterns (page-dashboard → estimate/dashboard, page-new-estimation → estimate/new, etc.)
    - Ensure all existing page functionality (form submissions, data loading, interactive elements) is preserved
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

  - [ ] 6.3 Verify legacy route redirects work end-to-end
    - Test all legacy routes redirect correctly: #dashboard, #new-estimation, #results/:id, #re-estimate/:id, #vendor-compare, #vendor-compare/:id, #audit-log, #admin
    - _Requirements: 4.6, 4.7, 4.8, 4.9, 4.10, 4.11, 4.12, 4.13_

  - [ ]* 6.4 Write integration tests for full navigation flow
    - Test sidebar click → hash change → page shown → nav state updated
    - Test legacy route entry → redirect → correct page shown
    - Test back/forward navigation maintains correct state
    - _Requirements: 5.8, 4.6–4.13_

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All changes are within `static/index.html` — no backend modifications
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties of routing functions
- The existing ~2100+ line file requires careful insertion points to avoid breaking current functionality
- Existing admin role guard must be preserved for settings routes
