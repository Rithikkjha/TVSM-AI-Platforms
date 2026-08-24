High Level Design — DRS Sales Planning Application

Purpose: Architecture-level documentation for external engineering partners covering system design, deployment, integrations, and resiliency considerations.
Version: 1.0 | Author: Samyucktha S | Status: CURRENT


_______________________________________________________________________________________


1. Overview

The DRS (Dealer Retail Sales) Sales Planning Application is a web-based system that manages the monthly retail sales planning lifecycle for TVS Motor Company's dealer network. The system enables zone-level sales planners to upload area×model retail plans via Excel, automatically generates dealer-level plans using historical sales contribution ratios, and provides a multi-level confirmation workflow (AMD → AD → Branch) with real-time status tracking.

The application is built as a Laravel 7.24 monolith deployed on IIS (Windows/Azure App Service) with SQL Server as the primary data store, Azure AD for production authentication, and OpenTelemetry for observability.

_______________________________________________________________________________________


2. Tier Classification

Tier        Component                   Technology                              Responsibility
Tier 1      Web Browser (Client)        Blade + Vue.js + ag-Grid               Plan upload, editing, status viewing
Tier 2      Application Server          Laravel 7.24 / PHP 7.2.5+ / IIS        Business logic, authentication, Excel processing
Tier 3      Database (Primary)          SQL Server (sqlsrv)                     Users, areas, dealers, plans, status
Tier 3      Database (Secondary)        SQL Server (sqlsrv2)                    Historical sales data, cross-references
Tier 3      Database (Tertiary)         SQL Server (sqlsrv4, sqlsrv5)           Additional data sources

_______________________________________________________________________________________


3. Background

The DRS Sales Planning system was developed to digitize TVS Motor Company's monthly retail plan allocation process. Previously, plan distribution from zone level down to individual dealers was managed manually via spreadsheets exchanged over email. This system automates:

    Area-level plan intake via structured Excel uploads
    Dealer-level plan generation using mathematical models (historical contribution ratios)
    Multi-level review and confirmation workflow
    Weekly and daily plan breakdowns for operational tracking
    Status visibility across all zones for management oversight

The system replaced manual processes that were error-prone, time-consuming, and lacked audit trails.

_______________________________________________________________________________________


4. Requirements

Functional Requirements:

ID      Requirement                                                     Priority
FR-01   Sales Planner uploads area×model retail plan via Excel          Critical
FR-02   System validates Excel against master data (areas, models)      Critical
FR-03   System generates dealer-level plans using L3M/L6M ratios        Critical
FR-04   Area Manager views/edits dealer-level plans via grid UI         Critical
FR-05   Area Manager confirms dealer plans (status → AMD Confirmed)     Critical
FR-06   System derives AD plans from AMD confirmed values               High
FR-07   AD plan confirmation workflow                                   High
FR-08   Branch-level plan confirmation                                  High
FR-09   Zone-wide status dashboard shows confirmation progress          High
FR-10   Weekly percentage plan upload and breakdown                     Medium
FR-11   Daily plan derivation from weekly breakdowns                    Medium
FR-12   Admin manages users, roles, area assignments                   Medium
FR-13   Email reminders for pending plan actions                        Medium
FR-14   Plan status reset by Admin for re-processing                   Medium
FR-15   Institution-level plan upload (separate from retail)           Low

Non-Functional Requirements:

ID      Requirement                                                     Target
NFR-01  Authentication via Azure AD SSO (production)                    100% production users
NFR-02  Concurrent plan editing by multiple Area Managers               Up to 50 AMs simultaneously
NFR-03  Excel upload processing time                                    < 30 seconds for standard file
NFR-04  Plan generation (dealer-level) time                             < 60 seconds per area
NFR-05  Page load time for plan grid                                    < 5 seconds
NFR-06  Observability via OpenTelemetry                                 All controller methods traced
NFR-07  Session timeout                                                 Configurable (default: Laravel session lifetime)
NFR-08  Support for 30+ vehicle models in plan matrix                   No upper limit on model count
NFR-09  Support for 50+ areas across all zones                          All active areas

_______________________________________________________________________________________


5. Current Architecture (HLD)

┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
│  ┌──────────────┐ ┌────────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │Sales Planner │ │ Area Manager   │ │Status Viewer │ │     Admin        │ │
│  │(Excel Upload)│ │(ag-Grid Edit)  │ │ (Dashboard)  │ │ (User Mgmt)      │ │
│  └──────────────┘ └────────────────┘ └──────────────┘ └──────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
         │                    │                  │                │
         ▼                    ▼                  ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│       DRS Sales Planning Application (Laravel 7.24 / IIS / Windows)         │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                    Route Layer (web.php)                            │     │
│  │  auth middleware group ──▶ All authenticated routes                 │     │
│  │  preventBackHistory ──▶ Session protection                         │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                    Controller Layer                                 │     │
│  │ ┌────────────┐ ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ │     │
│  │ │SalesPlanner│ │   Amd   │ │    Ad    │ │ Branch │ │  Status  │ │     │
│  │ │ Controller │ │Controller│ │Controller│ │  Ctrl  │ │   Ctrl   │ │     │
│  │ └────────────┘ └─────────┘ └──────────┘ └────────┘ └──────────┘ │     │
│  │ ┌────────────┐ ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ │     │
│  │ │   Admin    │ │  Login  │ │  Email   │ │  Plan  │ │   Misc   │ │     │
│  │ │ Controller │ │  Ctrl   │ │   Ctrl   │ │  Ctrl  │ │   Ctrl   │ │     │
│  │ └────────────┘ └─────────┘ └──────────┘ └────────┘ └──────────┘ │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │              Middleware Layer (Post-Processing)                     │     │
│  │ ┌──────────────────┐ ┌──────────────┐ ┌─────────────────────────┐ │     │
│  │ │afterProcessSales-│ │afterProcess- │ │afterProcessAD/Branch    │ │     │
│  │ │Plan (Dealer Gen) │ │AMD (AD Gen)  │ │(Status Update)          │ │     │
│  │ └──────────────────┘ └──────────────┘ └─────────────────────────┘ │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │           Data Access Layer (DB Facade + Eloquent)                  │     │
│  │ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │     │
│  │ │  DB::SELECT/     │  │  Eloquent Models │  │  Maatwebsite     │  │     │
│  │ │  INSERT/UPDATE   │  │  (User, Dealer)  │  │  Excel Import    │  │     │
│  │ └──────────────────┘  └──────────────────┘  └──────────────────┘  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │           Observability Layer (OtelTracer)                          │     │
│  │  Traces → /v1/traces │ Logs → /v1/logs │ Gateway: otel-gw-logs    │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
         │              │                │                │
         ▼              ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  SQL Server  │ │  SQL Server  │ │  SQL Server  │ │  SQL Server  │
│  (sqlsrv)    │ │  (sqlsrv2)   │ │  (sqlsrv4)   │ │  (sqlsrv5)   │
│  Primary DB  │ │  Secondary   │ │  Tertiary    │ │  Quaternary  │
│  Plans,Users │ │  Sales Hist  │ │              │ │              │
│  Areas,Dlrs  │ │              │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘


                                              ┌────────────────────────┐
                                              │   External Services    │
                                              │                        │
                                              │  Azure AD (Entra ID)   │
                                              │  (SSO — OpenID Connect)│
                                              │                        │
                                              │  SMTP Server           │
                                              │  (Email Notifications) │
                                              │                        │
                                              │  OTLP Gateway          │
                                              │  otel-gw-logs          │
                                              │  (Loki + Tempo)        │
                                              │                        │
                                              └────────────────────────┘

_______________________________________________________________________________________


6. Data Flow / Sequence Diagram

Plan Upload and Generation Sequence:

Sales Planner          Laravel App              SQL Server           OTLP Gateway
     │                      │                       │                     │
     │──POST /validateretailplan──▶│                │                     │
     │   (Excel file)       │                       │                     │
     │                      │──SELECT model_MDL────▶│                     │
     │                      │◀──model list─────────│                     │
     │                      │──SELECT active_dealers_for_month_IDM──▶    │
     │                      │◀──area list──────────│                     │
     │                      │                       │                     │
     │                      │ [Validates: models,   │                     │
     │                      │  areas, integers,     │                     │
     │                      │  no duplicates]       │                     │
     │                      │                       │                     │
     │◀──validation result──│                       │                     │
     │                      │                       │                     │
     │──POST /uploadretailplan──▶│                  │                     │
     │                      │──INSERT area_model_plan_APN──▶             │
     │                      │                       │                     │
     │                      │ [afterProcessSalesPlan middleware]         │
     │                      │──SELECT dealer_model_sales_DMS──▶          │
     │                      │◀──L3M/L6M ratios─────│                     │
     │                      │──INSERT dealer_model_plan_DPN──▶           │
     │                      │──UPDATE plan_status_PST (status=0)──▶     │
     │                      │                       │                     │
     │                      │──POST /v1/traces─────────────────────────▶│
     │                      │──POST /v1/logs───────────────────────────▶│
     │                      │                       │                     │
     │◀──success response───│                       │                     │

AMD Plan Confirmation Sequence:

Area Manager           Laravel App              SQL Server
     │                      │                       │
     │──GET /getamddata────▶│                       │
     │                      │──SELECT dealer_model_plan_DPN──▶
     │                      │◀──dealer plan grid───│
     │◀──JSON grid data─────│                       │
     │                      │                       │
     │  [AM edits values in ag-Grid]                │
     │                      │                       │
     │──POST /saveamdretailplan──▶│                 │
     │                      │──UPDATE dealer_model_plan_DPN──▶
     │                      │                       │
     │                      │ [afterProcessAMD middleware]
     │                      │──UPDATE plan_status_PST (status=2)──▶
     │                      │──Generate AD plans using L3M ratios──▶
     │                      │                       │
     │◀──confirm success────│                       │

_______________________________________________________________________________________


7. Dependencies

Internal Dependencies:

Component                   Depends On                  Purpose
SalesPlannerController      model_MDL, area_ARE         Master data validation
SalesPlannerController      active_dealers_for_month    Active dealer resolution for plan month
afterProcessSalesPlan       dealer_model_sales_DMS      Historical ratios for plan generation
AmdController               user_area_UAR               Area assignment for current user
AmdController               dealer_model_plan_DPN       Dealer plan data
AdController                dealer_model_sales_DMS      L3M contribution for AD derivation
StatusController            plan_status_PST             Confirmation status aggregation
LoginController             config_CFG                  Cutoff day configuration

External Dependencies:

Dependency                  Purpose                         Criticality     Fallback
Azure AD (Entra ID)         Production SSO authentication   High            Email login fallback (dev mode)
SMTP Server                 Email notifications             Medium          Emails fail silently; plans still work
OTLP Gateway (Loki+Tempo)  Observability                   Low             Telemetry fails silently (2s timeout)
SQL Server (Primary)        All application data            Critical        No fallback — system unavailable

_______________________________________________________________________________________


8. Deployment & Rollout Plan

┌───────────┐     ┌────────────────────────────┐     ┌──────────────────────┐
│ Developer │────▶│  Build                     │────▶│  Deploy              │
│ (Git Push)│     │  • composer install        │     │  • Copy to IIS       │
└───────────┘     │  • php artisan config:cache│     │  • Restart app pool  │
                  │  • npm run prod (assets)   │     │  • Verify health     │
                  └────────────────────────────┘     └──────────┬───────────┘
                                                                │
                  ┌───────────┬─────────────────┬───────────────┘
                  ▼           ▼                 ▼
            ┌──────────┐ ┌──────────┐ ┌────────────┐
            │   DEV    │ │   UAT    │ │    PROD    │
            │  (Auto)  │ │ (Manual) │ │  (Manual)  │
            └──────────┘ └──────────┘ └────────────┘

 ╔══════════════════════════════════════════════════════════════════════╗
 ║         Windows Server / Azure App Service (IIS)                     ║
 ║                                                                      ║
 ║  ┌─────────────────────────────────────────────────────────────┐    ║
 ║  │  DRS Sales Planning Application (Laravel 7.24)               │    ║
 ║  │  PHP 7.2.5+ | IIS with PHP-CGI/FastCGI                      │    ║
 ║  │  Port: 443 (HTTPS)                                          │    ║
 ║  │                                                              │    ║
 ║  │  Routes: web.php (session-based, all authenticated)          │    ║
 ║  │  Views: Blade templates + Vue.js + ag-Grid                   │    ║
 ║  │  Storage: storage/app/ (uploaded Excel files — temporary)    │    ║
 ║  └─────────────────────────────────────────────────────────────┘    ║
 ╚══════════════════════════════════════════════════════════════════════╝
                    │                              │
     ┌──────────────┴──────────────┐  ┌───────────┴───────────────┐
     ▼                             ▼  ▼                           ▼
┌────────────────────────────┐  ┌────────────────────────────┐
│ SQL Server (Primary)       │  │ External Services           │
│ • user_USR                 │  │ • Azure AD (SSO)           │
│ • area_ARE                 │  │ • SMTP (Email)             │
│ • dealer_DLR               │  │ • OTLP Gateway             │
│ • model_MDL                │  │   (otel-gw-logs.tvsmotor)  │
│ • dealer_model_plan_DPN    │  └────────────────────────────┘
│ • area_model_plan_APN      │
│ • plan_status_PST          │
│ • config_CFG               │
│ • dealer_model_sales_DMS   │
└────────────────────────────┘

Deployment Steps:

1. Pull latest code from repository
2. Run: composer install --no-dev --optimize-autoloader
3. Run: php artisan config:cache
4. Run: php artisan route:cache
5. Run: php artisan view:clear
6. Copy application files to IIS document root
7. Ensure .env file has correct environment variables
8. Restart IIS application pool
9. Verify: Access / and confirm login page loads
10. Smoke test: Login → upload plan → verify plan generation

Rollback Strategy:
    Keep previous deployment folder as backup
    Rollback: Point IIS to previous folder, restart app pool
    Database: No automated migrations; schema changes are manual

_______________________________________________________________________________________


9. Metrics to be Tracked

Metric                          Source                      Alert Threshold     Priority
Plan Upload Processing Time     OtelTracer spans            > 60 seconds        P1
Controller Error Rate (5xx)     OtelTracer logs             > 1%                P1
Login Success Rate              OtelTracer spans            < 95%               P1
AMD Confirmation Latency        OtelTracer spans            > 10 seconds        P2
Excel Validation Time           OtelTracer spans            > 30 seconds        P2
Database Query Time (P95)       OtelTracer spans            > 5 seconds         P2
Plan Status Completion Rate     plan_status_PST             < 80% by cutoff     P2
Email Delivery Success          SMTP logs                   Failure rate > 5%   P3
OTLP Export Failures            Laravel error logs          > 10/hour           P3
Active Sessions Count           Session store               > 100 concurrent    P3

Business Metrics:

Metric                          Query Source                Frequency
Areas with plans uploaded       area_model_plan_APN         Daily
Areas confirmed (AMD)           plan_status_PST (status=2)  Daily
Areas fully confirmed           plan_status_PST (status=4)  Daily
Average plans per area          dealer_model_plan_DPN       Monthly
Plan revision count             area_model_plan_APN audit   Monthly

_______________________________________________________________________________________


10. Alternatives Considered

Decision                    Chosen                          Alternative                         Rationale
Framework                   Laravel 7 (PHP)                 Node.js / Spring Boot               Existing PHP expertise in team; rapid development
Frontend                    Blade + Vue.js + ag-Grid        React SPA                           Simpler deployment; server-rendered; ag-Grid for Excel-like editing
Database                    SQL Server                      PostgreSQL / MySQL                  Enterprise standard at TVS; existing infrastructure
Authentication              Azure AD SSO + email fallback   Custom OAuth2                       Corporate directory integration; email for dev simplicity
Plan Generation             Mathematical ratios (L3M/L6M)  ML-based forecasting                Deterministic, auditable, matches existing business process
Excel Processing            Maatwebsite Excel               PhpSpreadsheet direct               Higher-level API, batch import support, Laravel integration
Observability               Custom OtelTracer (OTLP)        Serilog / Laravel Telescope          Unified with D2C observability stack (Loki + Tempo)
Hosting                     IIS on Windows                  Linux + Nginx                       Azure App Service Windows compatibility; SQL Server drivers
Session Management          Server-side sessions            JWT stateless                       Simpler for Blade-rendered pages; no API-first requirement


Risks:

Risk                                        Impact      Likelihood  Mitigation
Single SQL Server instance failure          Critical    Low         Azure SQL managed service with backups
Plan generation logic error (ratios)        High        Medium      Validation warnings, AM review step, admin reset
Excel upload with corrupt/wrong format      Medium      High        Comprehensive validation before persistence
Concurrent AM edits on same area            Medium      Medium      Session-based area assignment prevents overlap
Azure AD outage blocks production login     High        Low         Email login fallback (can be enabled quickly)
OTLP gateway down loses telemetry           Low         Medium      Graceful timeout (2s); local Laravel logs remain
Large Excel files causing PHP timeout       Medium      Medium      max_execution_time config; file size validation
Session hijacking / fixation                High        Low         Laravel CSRF, session regeneration, preventBackHistory


_______________________________________________________________________________________


Appendix

Technology Stack Summary:

Layer                   Technology                          Version
Backend Runtime         Laravel (PHP)                       7.24
PHP Version             PHP                                 7.2.5+
Frontend Rendering      Blade Templates + Vue.js            Laravel 7 / Vue 2
Data Grid               ag-Grid                             Community Edition
Database                SQL Server                          Multiple connections
ORM                     Eloquent + DB Facade                Laravel 7
Excel Processing        Maatwebsite Excel + Fast Excel      3.1 / 1.7
Auth (Production)       Azure AD via OpenID Connect         0.9.6
Auth (Dev/Test)         Laravel Auth (email-based)          Built-in
Observability           Custom OtelTracer (OTLP HTTP)       1.0.0
Email                   Laravel Mail (SMTP)                 Built-in
Hosting                 IIS on Windows                      Azure App Service
HTTP Client             Guzzle                              6.3

Database Connection Map:

Connection      Purpose                                     Key Tables
sqlsrv          Primary application data                    user_USR, area_ARE, dealer_DLR, model_MDL, dealer_model_plan_DPN, area_model_plan_APN, plan_status_PST, config_CFG
sqlsrv2         Historical sales and cross-reference data   dealer_model_sales_DMS, area_model_sales_AMS
sqlsrv4         Additional data source                      (Context-specific queries)
sqlsrv5         Additional data source                      (Context-specific queries)

User Role Matrix:

Role ID     Role Name           Home Page               Capabilities
1           Sales Planner       /retailplanupload       Upload retail/weekly plans, view status
2           Area Manager        /amdretailplan          View/edit/confirm dealer plans, AD plans, branch plans
3           Status Viewer       /status                 View confirmation status across zones
4           Admin               /retailplanupload       All Sales Planner capabilities + user/area/status management

_______________________________________________________________________________________


_______________________________________________________________________________________


11. Error Handling Strategy

Layer               Pattern                                     Implementation
Controller          Try-catch with OtelTracer                   Every public method wrapped; errors logged with TraceId/SpanId
Middleware          Terminable post-processing                  Plan generation runs after response; failures don't block user
Exception Handler   Global catch via App\Exceptions\Handler     Unhandled exceptions logged with trace context to OTEL gateway
Validation          Array-based error collection                Excel upload validates all rows before returning; no partial saves
Database            Lock timeout + retry                        SP execution uses SET LOCK_TIMEOUT -1 (infinite wait)
Concurrent access   In-progress flags                           PST_Confirm_in_progress prevents duplicate confirmations
Telemetry           Silent failure                              OtelTracer export has 2s timeout; never breaks application flow

Error Response Patterns:

Scenario                        Response
Session expired                 Redirect to / with error flash
Excel validation fails          JSON: {"error": [...], "warning": [...]}
DB query exception              JSON: {"error": "An error occurred"} (500)
Plan not yet generated          NULL response (frontend shows empty grid)
Concurrent confirmation         Plan stuck in "processing" state; admin can reset via /resetareaplanstatus

_______________________________________________________________________________________


12. Scalability Approach

Current State:

Aspect              Implementation              Limitation
Horizontal scaling  Not supported               File-based sessions, single-instance deployment
Vertical scaling    Azure App Service tier      Scale up plan tier for more CPU/memory
Plan generation     Synchronous (terminable MW) Long-running for large areas (~30s)
Concurrent users    ~50 simultaneous            Limited by PHP-FPM worker pool + DB connections
Data volume         ~44 tables, ~8000 lines     Performance depends on SQL Server tier

Potential Improvements (not implemented):

    Redis sessions for horizontal scaling
    Queue-based plan generation (Laravel Jobs)
    Caching of static reference data (models, areas, dealers)
    Read replicas for reporting queries
    API rate limiting for AJAX endpoints
