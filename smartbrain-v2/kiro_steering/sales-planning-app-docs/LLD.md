Low Level Design — DRS Sales Planning Application

Purpose: Implementation-level documentation for new engineering vendors to understand, maintain, and extend the system.
Version: 1.0 | Author: Samyucktha S | Status: CURRENT

_______________________________________________________________________________________


1. Overview

The DRS (Dealer Retail Sales) Sales Planning Application is a Laravel 7.24 monolithic web application that manages monthly retail sales plan allocation across TVS Motor Company's dealer network. The system accepts area-level retail plans via Excel upload, generates dealer-level plans using historical sales contribution ratios, and orchestrates a multi-level confirmation workflow (Sales Planner → AMD → AD → Branch). This LLD documents the implementation details including controller responsibilities, data access patterns, plan generation algorithms, validation logic, middleware chains, error handling, telemetry integration, and configuration.

_______________________________________________________________________________________


2. HLD Quick Recap

Reference doc: HLD — DRS Sales Planning Application

Architecture: Controllers → DB Facade (raw SQL) + Eloquent → SQL Server (4 connections)
Technology: Laravel 7.24, PHP 7.2.5+, Blade + Vue.js, ag-Grid, Maatwebsite Excel
Authentication: Azure AD SSO (production) + email login (dev/test)
Database: SQL Server via PDO sqlsrv driver (connections: sqlsrv, sqlsrv2, sqlsrv4, sqlsrv5)
Observability: Custom OtelTracer → OTLP HTTP → otel-gw-logs.tvsmotor.com (Loki + Tempo)
Email: Laravel Mail (SMTP) for plan upload/confirmation reminders

_______________________________________________________________________________________


3. Assumptions

    Laravel 7.24 with PHP 7.2.5+ running under IIS (Windows / Azure App Service)
    All business logic resides in Controllers (no separate Service layer)
    Data access via DB facade (raw SQL) for complex queries; Eloquent for simple CRUD (User, Dealer)
    All routes are web routes (session-based), no API/token routes
    No background job queue — all processing is synchronous within request lifecycle
    Plan generation runs in post-processing middleware (after response is prepared)
    ag-Grid operates client-side; server provides JSON data via GET endpoints
    Excel files are temporarily stored in storage/app/ during validation, not persisted long-term
    No unit/integration test suite exists in the repository
    Telemetry (OtelTracer) is non-blocking with 2-second timeout on OTLP exports
    Single-tenant deployment — one instance serves all zones/areas
    config_CFG table acts as runtime configuration store (cutoff days, flags)

_______________________________________________________________________________________


4. Components

Sales Plan Upload Module:

Layer           Class/File                              Responsibility
Controller      SalesPlannerController                  Excel validation, retail/institution plan upload, weekly % upload (~3950 lines)
Middleware      afterProcessSalesPlan                   Post-upload dealer plan generation from area plans using historical ratios
Import          ExcelImport (Maatwebsite)               Excel file parsing and row extraction
Model           Models (model_MDL)                      Active model master data

AMD Plan Module:

Layer           Class/File                              Responsibility
Controller      AmdController                           Plan month config, plan status, dealer grid data, save/confirm, week/day data
Middleware      afterProcessAMD                         Post-confirm AD plan derivation, status update to AMD Confirmed (2)
View            _amdretailplan.blade.php                ag-Grid based dealer×model plan editing interface

AD Plan Module:

Layer           Class/File                              Responsibility
Controller      AdController                            AD data, L3M ratios, MBO targets, save/confirm, bulk upload/download
Middleware      afterProcessAD                          Post-confirm status progression
View            _adretailplan.blade.php                 AD plan review interface with L3M contribution display

Branch Plan Module:

Layer           Class/File                              Responsibility
Controller      BranchController                        Branch data, counter totals, L3M, save/confirm, bulk upload/download
Middleware      afterProcessBranch                      Post-confirm final status (All Confirmed = 4)
View            _branchretailplan.blade.php             Branch plan confirmation interface

Authentication Module:

Layer           Class/File                              Responsibility
Controller      LoginController                         Email login (dev), Azure AD redirect, session creation, role-based redirect
Middleware      AppAzure                                Custom Azure middleware for non-AD environments
Config          config/azure.php                        Azure AD tenant/client/scope configuration

Admin Module:

Layer           Class/File                              Responsibility
Controller      AdminController                         User CRUD, role assignment, area mapping, plan status list, status reset
View            _admin.blade.php                        User management and plan status admin interface

Status & Plan View Module:

Layer           Class/File                              Responsibility
Controller      StatusController                        Zone-wide plan confirmation status aggregation, Excel download
Controller      PlanController                          Historical plan data with configurable columns and row types
View            _status.blade.php                       Status dashboard
View            _plans.blade.php                        Plan data viewer

Observability Module:

Layer           Class/File                              Responsibility
Singleton       OtelTracer (App\Telemetry)              Distributed tracing + structured logging via OTLP HTTP

Email Module:

Layer           Class/File                              Responsibility
Controller      EmailController                         Trigger email notifications for SP/AMD/AD actions
Controller      MailTriggerController                   CLI-triggered scheduled reminders

_______________________________________________________________________________________


5. API Design

Authentication Routes (No middleware):

Method  Route                       Controller                  Purpose
GET     /                           LoginController@init_login  Entry point — login page or redirect
POST    /login/email                LoginController@email_login Email authentication (dev/test)
GET     /login/azure                Azure middleware            Azure AD SSO initiation
GET     /login/azurecallback        Azure middleware            Azure AD callback handler
GET     /logout/email               LoginController@email_logout Session destroy + redirect
GET     /logout/azure               Azure middleware            Azure AD logout

Sales Planner Routes (auth middleware):

Method  Route                       Controller                          Purpose
GET     /retailplanupload           Blade view                          Plan upload page
GET     /getlastdate                SalesPlannerController@getLastUploadDate     Last upload status
POST    /validatesalesplan          SalesPlannerController@validateSalesUploads   Validate sales Excel
POST    /validateretailplan         SalesPlannerController@validateRetailUploads  Validate retail Excel
POST    /uploadretailplan           SalesPlannerController@saveRetailUpload       Persist retail plan
POST    /uploadsalesplan            SalesPlannerController@saveSalesUpload        Persist sales plan + trigger generation
POST    /validateweeklyplan         SalesPlannerController@validateWeeklyPercentUploads  Validate weekly %
POST    /uploadweeklyplan           SalesPlannerController@saveWeeklyPercentUpload       Persist weekly %

AMD Routes (auth middleware):

Method  Route                       Controller                          Purpose
GET     /amdretailplan              Blade view                          AMD plan editing page
GET     /getplanmonthconfig         AmdController@get_plan_month_config Plan month + cutoff config
GET     /getplanstatus              AmdController@get_plan_status       Area plan confirmation status
GET     /getareas                   AmdController@get_areas             Areas assigned to current AM
GET     /getmodels                  AmdController@get_models            Active models list
GET     /getamddata                 AmdController@get_amd_data          Dealer×model plan grid data
GET     /getweekwisedata            AmdController@get_weekwise_data     Weekly breakdown data
GET     /getdaywisedata             AmdController@get_daywise_data      Daily breakdown data
GET     /getretailplandata          AmdController@get_retail_plan_data  Retail plan totals
GET     /getinstitutionplandata     AmdController@get_institution_plan_data  Institution plan data
GET     /getareaadretailplandata    AmdController@get_area_ad_retail_plan_data   Area AD plan data
POST    /saveamdretailplan          AmdController@save_amd_retail_plan  Save + confirm AMD plan
POST    /resetamdplan               AmdController@reset_amd_plan        Reset plan for re-editing
POST    /uploadamdretailplan        AmdController@upload_amd_retail_plan    Bulk AMD plan upload

AD Routes (auth middleware):

Method  Route                       Controller                          Purpose
GET     /adretailplan               Blade view                          AD plan page
GET     /getamds                    AdController@get_amds               AMD dealers list
GET     /getaddata                  AdController@get_ad_data            AD plan grid data
GET     /getamdtotal                AdController@get_amd_total          AMD plan totals
GET     /getadl3m                   AdController@get_ad_l3m             L3M contribution ratios
GET     /getamdmbo                  AdController@get_amd_mbo            AMD MBO targets
GET     /getamdcounter              AdController@get_amd_counter        AMD counter data
GET     /getareaadplan              AdController@get_area_ad_plan       Area AD plan summary
POST    /saveadretailplan           AdController@save_ad_retail_plan    Save + confirm AD plan
GET     /validateadretailplan       AdController@validate_ad_retail_plan    Pre-confirm validation
GET     /getdlrname                 AdController@get_dlr_name           Dealer name lookup
GET     /getadplanconfirmedstatus   AdController@get_ad_plan_confirmed_status    Confirm check
POST    /resetadplan                AdController@reset_ad_plan          Reset AD plan
POST    /downloadalladplan          AdController@download_all_ad_plan   Excel download
POST    /uploadalladretailplan      AdController@upload_all_ad_retail_plan   Bulk upload

Branch Routes (auth middleware):

Method  Route                       Controller                              Purpose
GET     /branchretailplan           Blade view                              Branch plan page
GET     /getbranchplanconfirmedstatus   BranchController@get_branch_plan_confirmed_status   Confirm check
GET     /getbranchdata              BranchController@get_branch_data         Branch plan grid
GET     /getcountertotal            BranchController@get_counter_total       Counter totals
GET     /getbranchl3m               BranchController@get_branch_l3m         L3M data
GET     /getareabranchplan          BranchController@get_area_branch_plan    Area branch summary
POST    /savebranchretailplan       BranchController@save_branch_retail_plan Save + confirm
GET     /validatebranchretailplan   BranchController@validate_branch_retail_plan    Pre-confirm
POST    /resetbranchplan            BranchController@reset_branch_plan       Reset plan
POST    /downloadallbranchplan      BranchController@download_all_branch_plan   Excel download
POST    /uploadallbranchretailplan  BranchController@upload_all_branch_retail_plan   Bulk upload

Admin Routes (auth middleware):

Method  Route                       Controller                          Purpose
GET     /admin                      Blade view                          Admin panel
GET     /getroles                   AdminController@get_user_roles      All roles list
GET     /getusers                   AdminController@get_users           Paginated user list
GET     /getareasadm                AdminController@get_areas           All areas list
GET     /getuseredit                AdminController@get_user_data       Single user for edit
GET     /checkemail                 AdminController@check_unique_email  Email uniqueness check
GET     /deleteuser                 AdminController@delete_user         Delete user + area mapping
POST    /saveuser                   AdminController@save_user_data      Create/update user
GET     /getallplanstatus           AdminController@get_planstatus_list Plan status for all areas
GET     /getareaplanstatus          AdminController@get_area_status_data    Single area status
POST    /resetareaplanstatus        AdminController@reset_planstatus    Admin reset plan status

Standard Response Patterns:

    Success (JSON array/object): Direct data return from DB queries
    Success (paginated): LengthAwarePaginator with { data, total, per_page, current_page }
    Error: { "error": "An error occurred" } with HTTP 500
    Validation Error: { "error": [...], "warning": [...], "final_arr": [...] }
    Redirect: Laravel redirect() for auth flows

_______________________________________________________________________________________


6. Data Model / Schema Changes

Core Tables (Primary Connection — sqlsrv):

Table                           PK                      Key Columns                                         Purpose
user_USR                        USR_User_id             USR_User_name, USR_User_email, USR_User_role        User accounts
role_RLE                        RLE_Role_id             RLE_Role_name                                       Role definitions (1=SP, 2=AM, 3=SV, 4=Admin)
user_area_UAR                   UAR_id                  UAR_User_id, UAR_Area_id                            User-to-area assignment
area_ARE                        ARE_Area_id             ARE_Area_name, ARE_Status                           Area master
territory_TRY                   TRY_Territory_id        TRY_Territory_name, TRY_Area_id                     Territory master
dealer_DLR                      DLR_Dealer_id           DLR_Dealer_code, DLR_Dealer_name, DLR_AMD_id, DLR_Territory_id    Dealer master
dealer_link_DLK                 DLK_id                  DLK_AMD_id, DLK_AD_id                               AMD-AD dealer linkage
model_MDL                       MDL_Model_id            MDL_Model_name, MDL_Model_status                    Vehicle model master
config_CFG                      CFG_id                  CFG_Plan_month_start_day, CFG_AM_cutoff_day          Runtime config

Plan Tables:

Table                           PK                      Key Columns                                         Purpose
area_model_plan_APN             APN_id                  APN_Date, APN_Area_id, APN_Model_id, APN_Retail_plan_value     Area-level retail plan
area_model_sales_AMS            AMS_id                  AMS_Date, AMS_Area_id, AMS_Model_id, AMS_Sales_value           Area-level actual sales
dealer_model_plan_DPN           DPN_id                  DPN_Date, DPN_Dealer_id, DPN_Model_id, DPN_Plan_value          Dealer-level retail plan
dealer_model_sales_DMS          DMS_id                  DMS_Date, DMS_Dealer_id, DMS_Model_id, DMS_Sales_value         Dealer-level actual sales
institution_model_plan_IPN      IPN_id                  IPN_Date, IPN_Institution_id, IPN_Model_id, IPN_Retail_plan_value   Institution plan
active_dealers_for_month_IDM    IDM_id                  IDM_Dealer_id, IDM_Date                             Active dealers per month
plan_status_PST                 PST_id                  PST_Area_id, PST_Date, PST_Status, PST_Updated_by   Plan confirmation status

Weekly/Daily Breakdown Tables:

Table                           PK                      Key Columns                                         Purpose
week_WEK                        WEK_id                  WEK_Week_number, WEK_Month, WEK_Year                Week definitions
week_days_WDY                   WDY_id                  WDY_Week_id, WDY_Day_date                           Days within weeks
weekly_percentage_plan_WPP      WPP_id                  WPP_Date, WPP_Area_id, WPP_Week_id, WPP_Percentage  Weekly % distribution
daily_percentage_plan_DPP       DPP_id                  DPP_Date, DPP_Area_id, DPP_Day_id, DPP_Percentage   Daily % distribution

Derived Plan Tables:

Table                           PK                      Key Columns                                         Purpose
dealer_other_plan_DOP           DOP_id                  DOP_Date, DOP_Dealer_id, DOP_Plan_type              Other plan types
dealer_mode_plan_DMP            DMP_id                  DMP_Date, DMP_Dealer_id, DMP_Mode_id                Mode-wise plan
day_model_plan_DYM              DYM_id                  DYM_Date, DYM_Dealer_id, DYM_Model_id, DYM_Day      Day×model plan
day_mode_plan_DYO               DYO_id                  DYO_Date, DYO_Dealer_id, DYO_Mode_id, DYO_Day       Day×mode plan
mode_MDE                        MDE_Mode_id             MDE_Mode_name                                       Sales mode master

Plan Status Lifecycle:

Status      Value       Meaning                     Transition From     Transition To
Generated   0           Plans generated from upload  N/A                1 (AM Edit)
AM Edit     1           AM is editing plans          0                  2 (AMD Confirmed)
AMD Conf.   2           AM has confirmed             1                  4 (All Confirmed)
All Conf.   4           AD + Branch confirmed        2                  0 (Reset by Admin)

Entity Relationships:

area_ARE ──1:N──▶ territory_TRY ──1:N──▶ dealer_DLR
user_USR ──N:M──▶ area_ARE (via user_area_UAR)
dealer_DLR ──1:N──▶ dealer_model_plan_DPN
area_ARE ──1:N──▶ area_model_plan_APN
area_ARE ──1:1──▶ plan_status_PST (per month)
model_MDL ──1:N──▶ dealer_model_plan_DPN
model_MDL ──1:N──▶ area_model_plan_APN

_______________________________________________________________________________________


7. Class & Interface Design

OtelTracer (Singleton):

Class: App\Telemetry\OtelTracer
Pattern: Singleton (getInstance())
State: serviceName, serviceVersion, deploymentEnvironment, otlpEndpoint, currentTraceId, currentSpanId, enabled

Methods:
    startSpan(operationName, attributes=[]) → span array
    endSpan(&span, statusCode='OK', statusMessage='') → void (exports trace)
    setSpanError(&span, errorMessage) → void
    logWithTrace(level, message, attributes=[]) → void (exports log)
    info/error/warning/debug(message, attributes=[]) → void
    getTraceId() → string (32 hex chars)
    getSpanId() → string (16 hex chars)
    newTrace() → void (resets trace context per request)

User (Eloquent Model):

Class: App\User extends Authenticatable
Table: user_USR
PK: USR_User_id
Fillable: USR_User_name, USR_User_email, USR_User_role, USR_Status
Hidden: USR_Remember_token, USR_Updated_by, USR_Updated_datetime

Dealer (Eloquent Model):

Class: App\Dealer extends Model
Table: dealer_DLR
PK: DLR_Dealer_id
Fillable: DLR_Dealer_code, DLR_Dealer_name, DLR_AMD_id, DLR_Territory_id, DLR_Updated_by
Hidden: DLR_Updated_datetime

Controller Method Pattern (AdminController example):

    public static function method_name(Request $request) {
        $tracer = OtelTracer::getInstance();
        $span = $tracer->startSpan('ControllerName.method_name');
        try {
            // Business logic with DB facade calls
            $result = DB::SELECT("...");
            $tracer->endSpan($span);
            return $result;
        } catch (\Exception $e) {
            $tracer->setSpanError($span, $e->getMessage());
            $tracer->error("ControllerName.method_name failed: " . $e->getMessage(), [
                'exception.type' => get_class($e),
                'exception.file' => $e->getFile(),
                'exception.line' => (string)$e->getLine(),
            ]);
            $tracer->endSpan($span, 'ERROR', $e->getMessage());
            Log::error("ControllerName.method_name: " . $e->getMessage());
            return response()->json(['error' => 'An error occurred'], 500);
        }
    }

_______________________________________________________________________________________


8. Error Handling & Retries

Error Handling Strategy:

Layer               Pattern                                     Behavior
Controller          try/catch (Exception)                       Catch all exceptions, log via OtelTracer + Laravel Log, return HTTP 500
Telemetry           Silent failure (OTLP export)                2-second timeout, curl errors suppressed — telemetry never breaks the app
Excel Validation    Error accumulation pattern                  All errors collected into array, returned to user for correction
Session Timeout     Session::get() null check                  Returns "Session FAILED: NOT LOGGED IN" error if session expired
Database            DB facade exceptions                         Caught at controller level, logged, generic error returned

Error Response Patterns:

Scenario                            Response
Controller exception                {"error": "An error occurred"} — HTTP 500
Session expired                     {"error": [{error: "Session FAILED : NOT LOGGED IN or SESSION EXPIRED"}]}
Excel validation failure            {"error": ["Model X: unknown", "Area Y: missing"], "warning": [], "final_arr": []}
Invalid login                       Redirect to / with flash error "Incorrect email address"
Invalid user role                   Redirect to / with flash error "Invalid user role"

Retry Behavior:

    No automatic retry logic implemented in the application
    OTLP telemetry exports: Fire-and-forget, no retry on failure
    Database queries: No retry, exception propagates to controller catch
    Email sends: No retry, failure logged

_______________________________________________________________________________________


9. Security and Compliance

Authentication:

Mechanism                   Environment         Implementation
Azure AD OpenID Connect     Production          rootinc/laravel-azure-middleware; validates against user_USR
Email-based login           Dev/Test            LoginController.email_login; validates USR_User_email + USR_Status=1
Session management          All                 Laravel session with CSRF protection

Authorization:

    Role-based access control via USR_User_role stored in session
    Area-based data filtering via user_area_UAR mapping (AM sees only assigned areas)
    Route protection via auth middleware group (all plan routes)
    preventBackHistory middleware prevents cached page access after logout

Security Considerations:

Concern                     Current State                                   Recommendation
SQL Injection               Mix of parameterized (?) and string concat      Migrate all queries to parameterized
CSRF Protection             Laravel CSRF token on all POST forms             Adequate
Session Fixation            Session regenerated on login                     Adequate
XSS                         Blade {{ }} auto-escaping                       Adequate for Blade; review Vue bindings
Input Validation            Excel validation thorough; API input minimal     Add request validation for all endpoints
Password Storage            No passwords stored (Azure AD / email lookup)    N/A
Sensitive Data              .env for secrets, not committed                  Adequate

_______________________________________________________________________________________


10. RBAC (Role-Based Access Control)

Role Definitions:

Role ID     Name                Home Route              Capabilities
1           Sales Planner       /retailplanupload       Upload retail/weekly plans; view upload status
2           Area Manager        /amdretailplan          View/edit/confirm AMD plans; manage AD plans; branch plans
3           Status Viewer       /status                 Read-only status dashboard
4           Admin               /retailplanupload       All SP capabilities + user management + plan status reset

Permission Matrix:

Feature                     Sales Planner (1)   Area Manager (2)    Status Viewer (3)   Admin (4)
Upload Retail Plan          ✓                   ✗                   ✗                   ✓
Upload Weekly Plan          ✓                   ✗                   ✗                   ✓
View/Edit AMD Plan          ✗                   ✓ (own areas)       ✗                   ✗
Confirm AMD Plan            ✗                   ✓ (own areas)       ✗                   ✗
View/Confirm AD Plan        ✗                   ✓ (own areas)       ✗                   ✗
View/Confirm Branch Plan    ✗                   ✓ (own areas)       ✗                   ✗
View Zone Status            ✗                   ✗                   ✓                   ✗
Admin Users                 ✗                   ✗                   ✗                   ✓
Reset Plan Status           ✗                   ✗                   ✗                   ✓
Download Plans              ✗                   ✓                   ✓                   ✓

Area-Based Data Isolation:

    Area Manager (role=2) can only see data for areas mapped in user_area_UAR
    Session stores 'area' and 'areaid' from UAR assignment at login
    All data queries filter by session area ID
    Admin (role=4) can see all areas in plan status management

_______________________________________________________________________________________


11. Configuration Rules & Feature Flags

Runtime Configuration (config_CFG table):

Parameter                   Column                      Purpose                             Default
Plan Month Start Day        CFG_Plan_month_start_day    Day of month when plan advances     25
AM Cutoff Day               CFG_AM_cutoff_day           Deadline for AM confirmation        (configurable)

Plan Month Resolution Logic:

    if (current_day >= CFG_Plan_month_start_day):
        plan_month = next_month
    else:
        plan_month = current_month

Environment-Based Feature Flags (.env):

Variable                    Purpose                                     Values
AZURE_CLIENT_ID             Enables/disables Azure AD SSO               Set = SSO enabled; Empty = email login
OTEL_ENABLED                Enables/disables telemetry export           true/false
OTEL_SERVICE_NAME           Service name in telemetry                   drs-salesplanning
OTEL_EXPORTER_OTLP_ENDPOINT OTLP gateway URL                            http://otel-gw-logs.tvsmotor.com
SERVICE_VERSION             Application version tag                     1.0.0
DEPLOYMENT_ENVIRONMENT      Environment name in telemetry               dev/uat/prod

Authentication Toggle Logic (routes/web.php):

    if (env('AZURE_CLIENT_ID', "") != ""):
        Use RootInc\LaravelAzureMiddleware (production SSO)
    else:
        Use App\Http\Middleware\AppAzure (local fallback)

_______________________________________________________________________________________


12. Dependencies

PHP Package Dependencies (composer.json):

Package                             Version     Purpose                         Criticality
laravel/framework                   ^7.24       Core application framework      Critical
maatwebsite/excel                   ^3.1        Excel import/export             Critical (plan upload)
rap2hpoutre/fast-excel              ^1.7        Fast Excel processing           High (large files)
rootinc/laravel-azure-middleware    ^0.9.6      Azure AD SSO                    Critical (production)
guzzlehttp/guzzle                   ^6.3        HTTP client                     Medium
laravel/ui                          ^2.2        Auth scaffolding                Low
laravelcollective/html              ^6.2        Blade HTML helpers              Low
fideloper/proxy                     ^4.2        Trusted proxy (IIS)             Medium
fruitcake/laravel-cors              ^2.0        CORS headers                    Low

Infrastructure Dependencies:

Dependency                  Version/Type        Purpose                     Criticality
PHP                         7.2.5+              Runtime                     Critical
SQL Server                  Any (via PDO)       Data persistence            Critical
IIS                         Windows Server      Web server                  Critical
PHP sqlsrv extension        PDO driver          SQL Server connectivity     Critical
cURL extension              PHP built-in        OTLP telemetry export       Low
OpenSSL extension           PHP built-in        Azure AD token handling     High (production)

_______________________________________________________________________________________


13. Trade-offs & Alternatives Considered

Decision                        Chosen Approach                     Alternative                     Rationale
Data Access                     DB facade (raw SQL)                 Eloquent ORM throughout         Complex join/aggregation queries better expressed in SQL
Controller Design               Fat controllers (all logic)         Service layer pattern           Rapid development; single developer initially
Plan Generation                 Synchronous middleware              Background queue (Redis)        Simpler deployment; acceptable latency for batch
Frontend                        Blade + Vue + ag-Grid               Full SPA (React/Vue)            Simpler deployment; server-rendered; ag-Grid Excel-like
Auth Fallback                   Email login for dev                 Mock Azure AD locally           Simpler; no local AD setup needed
Telemetry                       Custom OtelTracer (OTLP)            Laravel Telescope               Aligns with D2C observability platform (Loki/Tempo)
Pagination                      Manual array_slice                  Laravel paginate()              Raw SQL results require manual pagination
Excel Library                   Maatwebsite + Fast Excel            PhpSpreadsheet direct           Higher-level API, Laravel integration, chunk support
Session Store                   Default (file/database)             Redis                           No Redis infrastructure; adequate for concurrent load

Known Technical Debt:

    SQL injection risk in some string-concatenated queries (filter parameters)
    Static controller methods prevent proper DI and testability
    3950-line SalesPlannerController needs decomposition
    No input validation middleware (relies on Excel validation logic only)
    Mixed use of parameterized queries and string interpolation
    No database transactions wrapping multi-table plan inserts

_______________________________________________________________________________________


14. Open Questions

#       Question                                                        Status      Decision
OQ-1    Should plan generation be moved to background queue?            Open        Current sync approach works but limits scalability
OQ-2    Is there a plan to add proper request validation?               Open        Currently relies on Excel validation; API inputs unchecked
OQ-3    Should old plan data be archived/purged periodically?           Open        Tables grow indefinitely per monthly cycle
OQ-4    Will the system need multi-language support?                    Open        Currently English only
OQ-5    Should SQL queries be migrated to parameterized format?         Open        Security concern; requires significant refactor
OQ-6    Is Redis/caching needed for frequently-accessed master data?    Open        model_MDL, area_ARE queried on every upload
OQ-7    Should the SalesPlannerController be decomposed?                Open        Single 3950-line file is maintenance risk
OQ-8    Will there be API consumers (mobile/BI) needing token auth?     Open        Current web-only routes use session auth

_______________________________________________________________________________________
