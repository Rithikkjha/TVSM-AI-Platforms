High Level Code Document — DRS Sales Planning Application

_______________________________________________________________________________________


1. Application Overview

The DRS (Dealer Retail Sales) Sales Planning Application is a full-stack web application developed for TVS Motor Company to manage the monthly retail sales planning lifecycle across all zones, areas, territories, and dealers. The system handles area-level plan uploads via Excel, automatic dealer-level plan generation using historical sales ratios, multi-level plan confirmation workflows (AMD → AD → Branch), weekly/daily plan breakdowns, and real-time status tracking across all zones.

The application is built as a monolithic Laravel 7.24 application with:

Backend: Laravel 7.24 (PHP 7.2.5+) with Blade templates for server-side rendering, raw SQL queries via DB facade for complex business logic, and Maatwebsite Excel for spreadsheet processing.

Frontend: Vue.js components embedded within Blade templates, ag-Grid for interactive plan editing tables, and Excel file upload/download capabilities.

The portal serves four primary user roles: Sales Planner (zone-level plan upload), Area Manager (dealer-level plan review/confirmation), Status Viewer (read-only dashboard), and Admin (user/area management).

_______________________________________________________________________________________


2. Major Modules/Components

Backend Modules:

Module                          Controller                      Purpose
Authentication                  LoginController                 Email-based login (dev/test) + Azure AD SSO (production)
Sales Plan Upload               SalesPlannerController          Excel validation, retail/institution plan upload, weekly percentage upload
AMD Retail Plan                 AmdController                   Area Manager dealer-level plan view, edit, confirm
AD Retail Plan                  AdController                    Associate Dealer plan derivation, edit, confirm (L3M ratios)
Branch Retail Plan              BranchController                Branch-level plan confirmation workflow
Status Dashboard                StatusController                Zone-wide plan confirmation status view
Plan Viewer                     PlanController                  Historical plan data with configurable columns
Admin Panel                     AdminController                 User CRUD, role assignment, area mapping, plan status reset
Email Notifications             EmailController                 SMTP-based email triggers for plan upload reminders
Mail Trigger (CLI)              MailTriggerController            Scheduled reminder emails via CLI/cron
Miscellaneous                   MiscController                  Utility/maintenance operations

Frontend Views (Blade + Vue.js):

View                            Template                        Purpose
Login                           login.blade.php                 Email login form (dev) / Azure AD redirect (prod)
Retail Plan Upload              _retailplanupload.blade.php     Excel upload interface for retail + weekly plans
AMD Retail Plan                 _amdretailplan.blade.php        ag-Grid based dealer plan editing
AD Retail Plan                  _adretailplan.blade.php         AD plan review with L3M contribution data
Branch Retail Plan              _branchretailplan.blade.php     Branch plan confirmation interface
Status Dashboard                _status.blade.php               Zone-wide confirmation progress
Plans Viewer                    _plans.blade.php                Historical plan data table
Admin Panel                     _admin.blade.php                User management interface

_______________________________________________________________________________________


3. Folder Structure Explanation

tvsm-salesplanning-app-repo/
    app/
        Http/
            Controllers/
                LoginController.php             Authentication (email + Azure AD)
                SalesPlannerController.php      Excel upload validation and processing (~3950 lines)
                AmdController.php               Area Manager plan operations
                AdController.php                Associate Dealer plan operations
                BranchController.php            Branch-level plan operations
                StatusController.php            Zone status aggregation
                PlanController.php              Plan data retrieval
                AdminController.php             User/area/status management
                EmailController.php             Email notification triggers
                MailTriggerController.php        CLI-triggered email reminders
                MiscController.php              Utility operations
            Middleware/
                AppAzure.php                    Custom Azure AD middleware (non-AD fallback)
                Authenticate.php                Laravel auth middleware
                afterProcessSalesPlan.php       Post-upload plan generation middleware
                afterProcessAMD.php             Post-AMD-confirm middleware
                afterProcessAD.php              Post-AD-confirm middleware
                afterProcessBranch.php          Post-Branch-confirm middleware
        Imports/
            ExcelImport.php                     Maatwebsite Excel import handler
        Models.php                              Eloquent model for model_MDL
        User.php                                Eloquent model for user_USR
        Dealer.php                              Eloquent model for dealer_DLR
        Telemetry/
            OtelTracer.php                      OpenTelemetry OTLP tracer (Loki + Tempo)
        constants.php                           Application constants
    config/
        database.php                            Multi-connection SQL Server config (sqlsrv, sqlsrv2, sqlsrv4, sqlsrv5)
        azure.php                               Azure AD tenant/client configuration
        app.php                                 Laravel application config
        mail.php                                SMTP email configuration
    resources/
        views/
            login.blade.php                     Login page
            _retailplanupload.blade.php         Plan upload view
            _amdretailplan.blade.php            AMD plan editing view
            _adretailplan.blade.php             AD plan view
            _branchretailplan.blade.php         Branch plan view
            _status.blade.php                   Status dashboard
            _plans.blade.php                    Plans viewer
            _admin.blade.php                    Admin panel
        js/                                     Vue.js components
    routes/
        web.php                                 All application routes (session-based)
    composer.json                               PHP dependencies
    .env                                        Environment variables (not committed)

_______________________________________________________________________________________


4. Core Business Workflows

4.1 Retail Plan Upload (Sales Planner)

Step 1 - Plan Month Resolution: System reads config_CFG table for CFG_Plan_month_start_day (cutoff day). If current date >= cutoff day, plan month advances to next month.

Step 2 - Excel Upload: Sales Planner uploads an Excel file with area-level retail plan. File contains models as columns, areas as rows, with integer plan values.

Step 3 - Validation: SalesPlannerController.checkRetailPlanData() validates:
    - All models in header exist in model_MDL table
    - All areas in rows exist in active_dealers_for_month_IDM for the plan month
    - All plan values are non-negative integers
    - No duplicate areas or models, no missing areas

Step 4 - Model Status Update: On successful validation, model_MDL.MDL_Model_status is set to 1 for models present in the upload, 0 for others.

Step 5 - Data Persistence: Validated data is inserted into area_model_plan_APN table (area × model plan values).

Step 6 - Dealer Plan Generation (afterProcessSalesPlan middleware): System generates dealer-level plans in dealer_model_plan_DPN using historical sales ratios from dealer_model_sales_DMS (last 3-6 months contribution percentages).

Step 7 - Plan Status Init: plan_status_PST is set to 0 (Generated) for each area.

4.2 AMD Plan Confirmation

Step 1 - Area Manager Login: AM logs in and is directed to /amdretailplan.

Step 2 - Plan Load: System loads dealer-level plan data from dealer_model_plan_DPN for the AM's assigned area(s).

Step 3 - Edit: AM can edit individual dealer×model plan values via ag-Grid interface.

Step 4 - Confirm: AM confirms the plan → afterProcessAMD middleware fires → plan_status_PST updated to 2 (AMD Confirmed).

Step 5 - AD Plan Derivation: System auto-generates AD (Associate Dealer) plans using L3M (Last 3 Month) contribution ratios.

4.3 AD and Branch Plan Confirmation

Step 1 - AD Plan Review: Area team reviews derived AD plans, can edit via upload or ag-Grid.

Step 2 - AD Confirm: On confirmation → afterProcessAD middleware → plan_status_PST progresses.

Step 3 - Branch Plan: Branch-level aggregated plans are reviewed and confirmed.

Step 4 - Final Status: plan_status_PST updated to 4 (All Confirmed).

4.4 Weekly/Daily Plan Breakdown

Step 1 - Weekly % Upload: Sales Planner uploads weekly percentage distribution (4-5 weeks per month).

Step 2 - Storage: weekly_percentage_plan_WPP and daily_percentage_plan_DPP tables populated.

Step 3 - Calculation: Week-wise and day-wise plan values derived from confirmed monthly plans.

_______________________________________________________________________________________


5. Key Services/Classes

Backend Key Classes:

SalesPlannerController (app/Http/Controllers/SalesPlannerController.php)
    Core controller (~3950 lines) handling all plan upload logic. Key methods:
    - getLastUploadDate(): Checks last upload status for given month/type
    - validateRetailUploads(): Validates retail plan Excel against DB master data
    - validateSalesUploads(): Validates sales data Excel
    - saveRetailUpload(): Persists validated retail plan data
    - saveSalesUpload(): Persists sales data + triggers dealer plan generation
    - validateWeeklyPercentUploads(): Validates weekly % distribution
    - saveWeeklyPercentUpload(): Persists weekly percentage data
    - checkRetailPlanData(): Internal validation engine for retail plan Excel
    - checkInstitutionPlanData(): Validates institution-level plan uploads
    - getMonthDate(): Resolves plan month based on cutoff day configuration

AmdController (app/Http/Controllers/AmdController.php)
    Manages Area Manager operations:
    - get_plan_month_config(): Returns cutoff day and plan month
    - get_plan_status(): Returns area plan confirmation status
    - get_amd_data(): Loads dealer-model plan grid data
    - get_weekwise_data(): Returns week-wise breakdowns
    - get_daywise_data(): Returns day-wise breakdowns
    - save_amd_retail_plan(): Saves AM-edited dealer plans + triggers confirm
    - reset_amd_plan(): Resets plan status back for re-editing

AdController (app/Http/Controllers/AdController.php)
    Manages Associate Dealer plan operations:
    - get_ad_data(): Loads AD plan data
    - get_ad_l3m(): Returns L3M (Last 3 Month) contribution ratios
    - get_amd_mbo(): Returns AMD MBO targets
    - save_ad_retail_plan(): Confirms AD plans
    - validate_ad_retail_plan(): Validates before confirmation
    - download_all_ad_plan(): Excel download of all AD plans
    - upload_all_ad_retail_plan(): Bulk AD plan upload

AdminController (app/Http/Controllers/AdminController.php)
    User and plan status management:
    - get_users(): Paginated user list with area mappings
    - save_user_data(): Create/update user with role and area assignment
    - delete_user(): Removes user and area mappings
    - get_planstatus_list(): Current month plan status for all areas
    - reset_planstatus(): Admin override to reset area plan status

OtelTracer (app/Telemetry/OtelTracer.php)
    OpenTelemetry instrumentation singleton:
    - Exports traces to Tempo via OTLP HTTP (/v1/traces)
    - Exports logs to Loki via OTLP HTTP (/v1/logs)
    - Provides startSpan/endSpan for distributed tracing
    - logWithTrace for correlated log entries
    - 2-second timeout on telemetry calls (non-blocking)

User (app/User.php)
    Eloquent model for user_USR table. PK: USR_User_id. Custom remember token name.

Dealer (app/Dealer.php)
    Eloquent model for dealer_DLR table. PK: DLR_Dealer_id. Fields: dealer code, name, AMD ID, territory ID.

_______________________________________________________________________________________


6. External Integrations

Integration                     Protocol            Direction       Purpose
Azure AD (Entra ID)             OpenID Connect      Bidirectional   SSO authentication for production environment
SMTP (Email)                    SMTP                Outbound        Plan upload/confirmation reminder emails
OpenTelemetry Gateway           OTLP HTTP           Outbound        Logs to Loki, traces to Tempo (otel-gw-logs.tvsmotor.com)
Excel File Processing           Local               Internal        Maatwebsite Excel for plan upload/download (xlsx)

_______________________________________________________________________________________


7. Major Dependencies

Backend (composer.json):

Package                             Version     Purpose
laravel/framework                   ^7.24       Core PHP framework
php                                 ^7.2.5      Runtime requirement
maatwebsite/excel                   ^3.1        Excel import/export (plan uploads)
rap2hpoutre/fast-excel              ^1.7        Fast Excel processing for large files
rootinc/laravel-azure-middleware    ^0.9.6      Azure AD SSO middleware
guzzlehttp/guzzle                   ^6.3        HTTP client (outbound API calls)
laravel/ui                          ^2.2        Authentication scaffolding
laravelcollective/html              ^6.2        HTML/Form helpers for Blade templates
fideloper/proxy                     ^4.2        Trusted proxy handling (IIS/Azure)
fruitcake/laravel-cors              ^2.0        CORS middleware
laravel/tinker                      ^2.0        REPL for debugging

Dev Dependencies:

Package                             Version     Purpose
barryvdh/laravel-debugbar           ^3.4        Debug toolbar (local development)
phpunit/phpunit                     ^8.5        Unit testing framework
fzaninotto/faker                    ^1.9.1      Test data generation
mockery/mockery                     ^1.3.1      Mocking library for tests

Frontend Dependencies (loaded via CDN/npm in Blade templates):

Library         Purpose
Vue.js          Reactive UI components within Blade templates
ag-Grid         High-performance data grid for plan editing
Bootstrap       CSS framework for layout/styling

_______________________________________________________________________________________


8. Runtime Architecture

Backend Runtime:

Framework: Laravel 7.24 running on PHP 7.2.5+ with IIS as the web server (Windows/Azure App Service).

Database: Multiple SQL Server connections via PDO sqlsrv driver:
    sqlsrv (primary): Main application data (users, areas, dealers, plans)
    sqlsrv2: Secondary data source (historical sales, cross-references)
    sqlsrv4: Additional data connection
    sqlsrv5: Additional data connection

Session: Laravel session with database/file driver. Session stores user_id, user_name, user_email, user_role, area, areaid, cutoffday, amcutoffday.

Authentication Flow:
    Production: Azure AD SSO via rootinc/laravel-azure-middleware → callback validates user in user_USR → session created
    Dev/Test: Email-based login → validates against user_USR table → Auth::login() → session created

Middleware Pipeline:
    preventBackHistory: Prevents browser back-button to cached pages after logout
    auth: Laravel authentication guard
    afterProcessSalesPlan: Post-upload dealer plan generation
    afterProcessAMD: Post-AMD-confirm processing
    afterProcessAD: Post-AD-confirm processing
    afterProcessBranch: Post-Branch-confirm processing

Telemetry: OtelTracer singleton exports structured logs and traces via OTLP HTTP to otel-gw-logs.tvsmotor.com with 2-second non-blocking timeout.

Frontend Runtime:

Rendering: Server-side Blade templates with embedded Vue.js components.

Data Grid: ag-Grid used for interactive editing of dealer×model plan matrices.

File Operations: Excel upload via multipart form POST, download via server-generated xlsx responses.

Navigation: Traditional page-based navigation (full page reloads) via Laravel routes.

_______________________________________________________________________________________


9. Important Entry Points

Authentication Entry Points:

Entry Point                 Route                           Description
Application Root            GET /                           Redirects to login or home based on session
Email Login                 POST /login/email               Validates email, creates session, redirects by role
Azure AD Login              GET /login/azure                Initiates Azure AD OAuth flow
Azure AD Callback           GET /login/azurecallback        Processes Azure AD response, creates session
Logout                      GET /logout/email               Destroys session, redirects to login

Sales Planner Entry Points:

Entry Point                 Route                           Description
Plan Upload Page            GET /retailplanupload           Blade view for plan upload interface
Get Last Upload Date        GET /getlastdate                Returns last upload status for month/type
Validate Retail Plan        POST /validateretailplan        Validates Excel file against master data
Upload Retail Plan          POST /uploadretailplan          Persists validated retail plan data
Validate Weekly Plan        POST /validateweeklyplan        Validates weekly percentage Excel
Upload Weekly Plan          POST /uploadweeklyplan          Persists weekly percentage data

AMD Entry Points:

Entry Point                 Route                           Description
AMD Plan Page               GET /amdretailplan              Blade view for AM plan editing
Get AMD Data                GET /getamddata                 Returns dealer×model plan grid data
Save AMD Plan               POST /saveamdretailplan         Saves edits + triggers confirmation
Reset AMD Plan              POST /resetamdplan              Resets plan back to editable state

Admin Entry Points:

Entry Point                 Route                           Description
Admin Panel                 GET /admin                      Blade view for user management
Get Users                   GET /getusers                   Paginated user list
Save User                   POST /saveuser                  Create/update user record
Get Plan Status List        GET /getallplanstatus           All areas plan confirmation status
Reset Plan Status           POST /resetareaplanstatus       Admin override plan status reset

_______________________________________________________________________________________


10. High-Level Data Flow

The data flows through the system as follows:

Sales Planner (Browser) uploads Excel → Laravel validates → persists to area_model_plan_APN → triggers dealer plan generation → populates dealer_model_plan_DPN.

Area Manager (Browser) views ag-Grid → edits dealer plans → saves to dealer_model_plan_DPN → confirms → triggers AD plan derivation using L3M ratios from dealer_model_sales_DMS.

AD plans are derived → stored in dealer_model_plan_DPN → reviewed/confirmed → Branch plans generated and confirmed.

Status Dashboard reads plan_status_PST → aggregates confirmation progress across all zones/areas.

Data Flow Summary:

Source                  Target                          Integration Type        Data Exchanged
Sales Planner           SalesPlannerController          HTTP POST (Excel)       Area×Model retail plan values
SalesPlannerController  area_model_plan_APN             SQL INSERT              Validated area-level plans
afterProcessSalesPlan   dealer_model_plan_DPN           SQL INSERT              Generated dealer-level plans (historical ratios)
Area Manager            AmdController                   HTTP GET/POST (JSON)    Dealer×Model plan edits
AmdController           dealer_model_plan_DPN           SQL UPDATE              Edited plan values
afterProcessAMD         plan_status_PST                 SQL UPDATE              Status = 2 (AMD Confirmed)
afterProcessAD          plan_status_PST                 SQL UPDATE              Status progression
afterProcessBranch      plan_status_PST                 SQL UPDATE              Status = 4 (All Confirmed)
StatusController        plan_status_PST + area_ARE      SQL SELECT              Zone-wide status aggregation
EmailController         SMTP Server                     SMTP                    Reminder notifications
OtelTracer              otel-gw-logs.tvsmotor.com       OTLP HTTP               Traces (/v1/traces), Logs (/v1/logs)
LoginController         Azure AD                        OpenID Connect          SSO authentication (production)

Integration Summary:

┌────────────────────┐       ┌─────────────────────────────────────────┐
│  Sales Planner     │──────▶│  DRS Sales Planning (Laravel 7 / IIS)   │
│  (Excel Upload)    │       │                                         │
├────────────────────┤       │  Controllers → DB Facade → SQL Server   │
│  Area Manager      │──────▶│  Middleware → Plan Generation Logic     │
│  (ag-Grid Edit)    │       │  OtelTracer → OTLP Gateway              │
├────────────────────┤       │                                         │
│  Status Viewer     │──────▶│                                         │
│  (Read-only)       │       └──────────────┬──────────────────────────┘
├────────────────────┤                      │
│  Admin             │──────▶               │
│  (User Mgmt)       │                      │
└────────────────────┘                      │
                              ┌─────────────┴─────────────────────┐
                              ▼                                   ▼
                   ┌─────────────────────┐          ┌─────────────────────────┐
                   │ SQL Server (4 DBs)  │          │  External Services       │
                   │ Plans, Users, Areas │          │  Azure AD (SSO)          │
                   │ Dealers, Models,    │          │  SMTP (Email)            │
                   │ Sales History       │          │  OTLP Gateway (Telemetry)│
                   └─────────────────────┘          └─────────────────────────┘

_______________________________________________________________________________________
