API Specification — DRS Sales Planning Application

Purpose: Complete API specification document for external engineering partners and integration teams.
Version: 1.0 | Author: Samyucktha S | Status: CURRENT

_______________________________________________________________________________________


0. Service Identity

| Field | Value |
|-------|-------|
| Service Name | drs-salesplanning |
| Repo | github.com/TVSM-DMS/tvsm-salesplanning-app-repo |
| Team | D&AI / Electronic City |
| Tech Lead | @Samyucktha.S |
| Deployment | Azure App Service (IIS) |
| Base URL (prod) | https://drs.tvsmotor.com/sps |
| Base URL (dev) | https://tvsmazoogappdev01-drs.azurewebsites.net |

Ownership & Contacts:

| Role | Person / Team | Contact |
|------|---------------|---------|
| Product Owner | Business / Sales Team | Vidit Singh |
| Tech Lead | Samyucktha S | Samyucktha.S@tvsmotor.com |
| Dev Team | D&AI / Electronic City | |
| L2 Support | Vineetha B, Ashok Kumar K | Vineetha.B@tvsmotor.com, AshokKumar.K@tvsmotor.com |
| DE Pipeline | Geetapriya | DE Team |
| PowerBI / Parts | Gowthaman S | PowerBI Team |

_______________________________________________________________________________________


Inbound Summary (Who Calls This Service)

| Caller | Endpoints Called | Auth Method |
|--------|----------------|-------------|
| Web Browser (Area Managers) | All AMD/AD/Branch/Status endpoints | Session cookie (Azure AD SSO) |
| Web Browser (Sales Planner) | Upload/Validate endpoints | Session cookie (Azure AD SSO) |
| Web Browser (Admin) | Admin/User management endpoints | Session cookie (Azure AD SSO) |
| Cron/Scheduler | /mailtrigger | No auth (internal trigger) |
| Azure AD callback | /login/azurecallback | OAuth2 auth code |

Note: This is a monolithic web application. There are no service-to-service API consumers. All endpoints are consumed by the web browser via AJAX or form submissions.

_______________________________________________________________________________________


1. API Endpoint List

Authentication APIs (No auth middleware):

#   Method  Endpoint                    Purpose
1   GET     /                           Application entry — login page or redirect to home
2   POST    /login/email                Email-based authentication (dev/test environments)
3   GET     /login/azure                Azure AD SSO initiation (production)
4   GET     /login/azurecallback        Azure AD OAuth callback handler
5   GET     /logout/email               Session destroy and logout
6   GET     /logout/azure               Azure AD logout

Sales Planner APIs (auth required):

#   Method  Endpoint                    Purpose
7   GET     /getlastdate                Get last upload date/status for given month and type
8   POST    /validatesalesplan          Validate sales plan Excel file against master data
9   POST    /validateretailplan         Validate retail plan Excel file against master data
10  POST    /uploadretailplan           Persist validated retail plan data to database
11  POST    /uploadsalesplan            Persist sales plan + trigger dealer plan generation
12  POST    /validateweeklyplan         Validate weekly percentage distribution Excel
13  POST    /uploadweeklyplan           Persist weekly percentage data

AMD (Area Manager) APIs (auth required):

#   Method  Endpoint                    Purpose
14  GET     /getplanmonthconfig         Get plan month configuration (cutoff day, AM cutoff)
15  GET     /getplanstatus              Get plan confirmation status for current area
16  GET     /getareas                   Get areas assigned to logged-in Area Manager
17  GET     /getmodels                  Get active vehicle models list
18  GET     /getamddata                 Get dealer×model plan grid data for editing
19  GET     /getweekwisedata            Get week-wise plan breakdown
20  GET     /getdaywisedata             Get day-wise plan breakdown
21  GET     /getretailplandata          Get retail plan summary/totals
22  GET     /getinstitutionplandata     Get institution plan data for area
23  GET     /getareaadretailplandata    Get area AD retail plan data
24  POST    /saveamdretailplan          Save AMD edits and confirm plan
25  POST    /resetamdplan               Reset AMD plan to editable state
26  POST    /uploadamdretailplan        Bulk upload AMD plan via Excel

AD (Associate Dealer) APIs (auth required):

#   Method  Endpoint                    Purpose
27  GET     /getamds                    Get AMD dealers list for area
28  GET     /getaddata                  Get AD plan grid data
29  GET     /getamdtotal                Get AMD plan totals for comparison
30  GET     /getadl3m                   Get Last 3 Month contribution ratios
31  GET     /getamdmbo                  Get AMD MBO (Management By Objectives) targets
32  GET     /getamdcounter              Get AMD counter/outlet data
33  GET     /getareaadplan              Get area-level AD plan summary
34  POST    /saveadretailplan           Save and confirm AD retail plan
35  GET     /validateadretailplan       Validate AD plan before confirmation
36  GET     /getdlrname                 Get dealer name by ID
37  GET     /getadplanconfirmedstatus   Check if AD plan is already confirmed
38  POST    /resetadplan                Reset AD plan for re-editing
39  POST    /downloadalladplan          Download all AD plans as Excel
40  POST    /uploadalladretailplan      Bulk upload all AD retail plans via Excel

Branch APIs (auth required):

#   Method  Endpoint                        Purpose
41  GET     /getbranchplanconfirmedstatus    Check if branch plan is confirmed
42  GET     /getbranchdata                  Get branch plan grid data
43  GET     /getcountertotal                Get counter/outlet totals
44  GET     /getbranchl3m                   Get branch L3M contribution data
45  GET     /getareabranchplan              Get area branch plan summary
46  POST    /savebranchretailplan           Save and confirm branch plan
47  GET     /validatebranchretailplan       Validate branch plan before confirmation
48  POST    /resetbranchplan                Reset branch plan for re-editing
49  POST    /downloadallbranchplan          Download all branch plans as Excel
50  POST    /uploadallbranchretailplan      Bulk upload branch plans via Excel

Status & Plan APIs (auth required):

#   Method  Endpoint                        Purpose
51  GET     /getallzonestatus               Get confirmation status across all zones
52  GET     /downloadallareasmonthplan      Download all areas plan data as Excel
53  GET     /getrowtypes                    Get row type configuration for plan viewer
54  GET     /getplancolumns                 Get column configuration for plan viewer
55  GET     /getplandata                    Get historical plan data

Admin APIs (auth required):

#   Method  Endpoint                        Purpose
56  GET     /getroles                       Get all user roles
57  GET     /getusers                       Get paginated user list with area mappings
58  GET     /getareasadm                    Get all areas for admin dropdown
59  GET     /getuseredit                    Get single user data for editing
60  GET     /checkemail                     Check email uniqueness
61  GET     /deleteuser                     Delete user and area mappings
62  POST    /saveuser                       Create or update user record
63  GET     /getallplanstatus               Get plan status for all areas (current month)
64  GET     /getareaplanstatus              Get plan status for specific area
65  POST    /resetareaplanstatus            Admin reset area plan status

Email APIs (No auth — CLI triggered):

#   Method  Endpoint                    Purpose
66  GET     /mailsp                     Trigger Sales Planner reminder email
67  GET     /mailamd                    Trigger AMD plan reminder email
68  GET     /mailad                     Trigger AD plan reminder email
69  GET     /mailtrigger                CLI-triggered scheduled mail reminders

_______________________________________________________________________________________


2. Request Methods

GET:    Data retrieval (plan data, status, config, user info, validation checks)
POST:   Data mutations (plan uploads, saves, confirmations, user CRUD, status resets)
POST:   File uploads (Excel files via multipart/form-data)

Note: All routes are web routes using Laravel session-based authentication. No REST API versioning or content negotiation is implemented. All data endpoints return JSON; page routes return Blade views.

_______________________________________________________________________________________


3. Authentication Requirements

Endpoint Group              Auth Method                     Session Variables
/login/*, /logout/*         None (public)                   N/A
All other routes            Laravel session (auth middleware) user_id, user_name, user_email, user_role, area, areaid
/mailtrigger, /mail*        None (CLI triggered)            N/A

Authentication Flow (Production — Azure AD):

    1. User navigates to /
    2. LoginController checks session; if empty, renders login view
    3. User clicks "Login with Azure AD" → GET /login/azure
    4. Azure AD middleware redirects to Microsoft login
    5. User authenticates with corporate credentials
    6. Callback to /login/azurecallback → validates user exists in user_USR
    7. Session created with user_id, user_role, area assignments
    8. Redirected to role-based home page

Authentication Flow (Dev/Test — Email):

    1. User navigates to /
    2. Enters email address in login form
    3. POST /login/email with email parameter
    4. Controller checks: USR_User_email match + USR_Status = 1
    5. On success: Auth::login(), session variables set, redirect to home
    6. On failure: Redirect back with error flash message

Session Variables Set at Login:

Variable        Source                      Purpose
user_id         user_USR.USR_User_id        Current user identifier
user_name       user_USR.USR_User_name      Display name
user_email      user_USR.USR_User_email     Email address
user_role       user_USR.USR_User_role      Role ID (1-4)
area            user_area_UAR.UAR_Area_id   Primary area (for AM)
areaid          user_area_UAR.UAR_Area_id   Area ID (for AM)
user_home       (derived from role)         Home route for redirects
cutoffday       config_CFG                  Plan month cutoff day
amcutoffday     config_CFG                  AM cutoff day

_______________________________________________________________________________________


4. Request Payloads

POST /login/email:
    Content-Type: application/x-www-form-urlencoded
    Parameters: email=user@tvsmotor.com

GET /getlastdate:
    Query: ?month=01-25&type=retail
    (month format: MM-YY, type: retail|weekly)

POST /validateretailplan (multipart/form-data):
    file: [Excel .xlsx file]
    month: 01-25

POST /uploadretailplan:
    Content-Type: application/json
    Body: (validated data from session/previous validation step)

POST /validateweeklyplan (multipart/form-data):
    file: [Excel .xlsx file with weekly percentages]
    month: 01-25

GET /getamddata:
    Query: ?area={areaId}&month={YYYY-MM-DD}

POST /saveamdretailplan:
    Content-Type: application/json
    Body: {
        "data": [
            {"dealer_id": 123, "model_id": 45, "plan_value": 10},
            {"dealer_id": 123, "model_id": 46, "plan_value": 15}
        ],
        "area": 5,
        "month": "2025-02-01"
    }

POST /saveadretailplan:
    Content-Type: application/json
    Body: {
        "data": [...],
        "area": 5,
        "amd_id": 123,
        "month": "2025-02-01"
    }

GET /getusers:
    Query: ?per_page=10&page=1&sort=USR_User_id|asc&filter=searchterm

POST /saveuser:
    Content-Type: application/x-www-form-urlencoded
    Parameters: edit=0|1, name=John, user_email=john@tvs.com, role=2, area=5, upid=123

GET /getallplanstatus:
    Query: ?per_page=10&page=1&sort=&filter=searchterm

POST /resetareaplanstatus:
    Content-Type: application/x-www-form-urlencoded
    Parameters: ad_amd=1|2, areaid=5

_______________________________________________________________________________________


5. Response Payloads

GET /getlastdate:
    [{"maxdate": "2025-02-01", "disabled": 0, "dt": {"processdate": "2025-03-01", "cutoffday": 25, ...}}]

POST /validateretailplan (Success):
    {"error": [], "warning": [], "final_arr": [...validated data...]}

POST /validateretailplan (Validation Errors):
    {"error": ["Model jupiter: unknown", "Area Chennai: Is repeated", "Area Bangalore: missing"], "warning": [], "final_arr": []}

GET /getamddata (Dealer×Model Grid):
    [
        {"dealer_id": 123, "dealer_name": "ABC Motors", "model_1": 10, "model_2": 15, "total": 25},
        {"dealer_id": 124, "dealer_name": "XYZ Motors", "model_1": 8, "model_2": 12, "total": 20}
    ]

GET /getplanstatus:
    {"status": 2, "status_text": "AMD Confirmed", "area": "Chennai", "date": "2025-02-01"}

GET /getroles:
    [{"id": 1, "role": "Sales Planner"}, {"id": 2, "role": "Area Manager"}, {"id": 3, "role": "Status Viewer"}, {"id": 4, "role": "Admin"}]

GET /getusers (Paginated):
    {
        "current_page": 1,
        "data": [
            {"id": 1, "name": "John", "email": "john@tvs.com", "roleId": 2, "role": "Area Manager", "areaid": "5", "areaname": "Chennai", "created_at": "15-Jan-2025"}
        ],
        "total": 42,
        "per_page": 10,
        "last_page": 5
    }

GET /getallplanstatus (Paginated):
    {
        "current_page": 1,
        "data": [
            {"id": 5, "areaname": "Chennai", "status": "AMD Confirmed", "statusid": 2, "manager": "Area Mgr Name", "dt": "2025-02-01"}
        ],
        "total": 50,
        "per_page": 10
    }

GET /getallzonestatus:
    [
        {"zone": "South", "total_areas": 12, "confirmed": 8, "pending": 4},
        {"zone": "North", "total_areas": 10, "confirmed": 6, "pending": 4}
    ]

POST /saveuser (Success):
    {"messege": "User Saved Successfully"}

POST /saveamdretailplan (Success):
    {"messege": "Plan saved and confirmed successfully"}

GET /checkemail:
    0 (unique) | 1 (duplicate)

_______________________________________________________________________________________


6. Error Responses

Standard Error Format:
    {"error": "An error occurred"} — HTTP 500

Validation Error Format:
    {"error": ["error message 1", "error message 2"], "warning": ["warning 1"], "final_arr": []}

Session Expired Format:
    {"error": [{"error": "Session FAILED : NOT LOGGED IN or SESSION EXPIRED"}]}

Common Error Scenarios:

Scenario                            Response                                            HTTP Code
Controller exception                {"error": "An error occurred"}                      500
Session expired (AJAX)              {"error": [...session expired message...]}           200 (with error payload)
Session expired (page load)         Redirect to / (login page)                          302
Invalid email login                 Redirect to / with flash: "Incorrect email address" 302
Invalid user role                   Redirect to / with flash: "Invalid user role"       302
Excel validation failure            {"error": [...list of errors...]}                   200
Duplicate email (check)             1                                                   200
Plan already confirmed              {"error": "Plan already confirmed for this area"}   200

_______________________________________________________________________________________


7. Validation Rules

Excel Retail Plan Validation (SalesPlannerController.checkRetailPlanData):

Rule                                    Error Message Pattern
Model not in model_MDL                  "Model {name} : unknown"
Model repeated in header                "Model {name} : Is repeated"
Area not in active_dealers_for_month    "Area {name} : unknown(0)"
Area repeated in data rows              "Area {name} : Is repeated"
Area missing from data                  "Area {name} : missing"
Plan value not non-negative integer     "Area {name} at row ({n}): invalid plan-number for model :{model}"
Empty model columns between values      "Model has empty columns"
Empty area rows between values          "Area before row ({n}) : EMPTY VALUES"
No valid models found                   "No valid Models were found"
Header unreadable                       "Unable to get the header, please use template and re-upload"

User Management Validation (AdminController):

Field           Rule                            Error
email           Must be unique in user_USR      check_unique_email returns 1 (duplicate)
role            Must be valid role ID (1-4)     No explicit validation (trusted admin input)
area            Required if role = 2 (AM)       Area mapping created only for AM role

Plan Month Resolution Rules:

    Current day >= CFG_Plan_month_start_day → plan month = next month
    Current day < CFG_Plan_month_start_day → plan month = current month
    Historical period: Last 6 months for L3M/L6M ratio calculation
    Plan upload disabled for past months (disabled flag = 1)

Pagination Parameters:

Parameter       Type        Default     Range       Purpose
per_page        integer     10          1-100       Records per page
page            integer     1           1-N         Current page number
sort            string      ""          col|dir     Sort column and direction
filter          string      ""          any         Text filter on name/area columns

_______________________________________________________________________________________


8. Rate Limits

No explicit application-level rate limiting is implemented. The system relies on:

Protection Layer            Mechanism                                   Limit
IIS                         Request queue and connection limits          Server-configured
Laravel                     Session-based (one user per session)        Implicit
SQL Server                  Connection pool limits                      Per database config
PHP                         max_execution_time                          60-120 seconds
PHP                         upload_max_filesize                         Configured in php.ini
PHP                         post_max_size                               Configured in php.ini
OTLP Export                 Timeout per request                         2 seconds (non-blocking)

Implicit Rate Controls:

    One session per browser (cookie-based)
    Plan upload requires complete validation before persistence
    Plan confirmation is idempotent (re-confirm doesn't duplicate)
    Admin operations restricted to role 4 users only

_______________________________________________________________________________________


9. External API Dependencies

External API                    Called By               Auth                    Timeout     Purpose
Azure AD (login.microsoftonline.com)    LoginController (prod)  OAuth2/OIDC             Default     SSO authentication
Azure AD (graph.microsoft.com)          Azure middleware         Bearer token            Default     User profile (scope: User.Read)
SMTP Server                             EmailController         SMTP credentials        Default     Plan reminder notifications
OTLP Gateway (otel-gw-logs.tvsmotor.com/v1/logs)    OtelTracer    None (internal)    2000ms      Log export to Loki
OTLP Gateway (otel-gw-logs.tvsmotor.com/v1/traces)  OtelTracer    None (internal)    2000ms      Trace export to Tempo

Azure AD Configuration (config/azure.php):

Parameter               Environment Variable        Purpose
tenant_id               AZURE_TENANT_ID             Azure AD directory ID
client.id               AZURE_CLIENT_ID             Application (client) ID
client.secret           AZURE_CLIENT_SECRET         Client secret for OAuth
resource                AZURE_RESOURCE              Object ID
domain_hint             AZURE_DOMAIN_HINT           Login domain helper
scope                   AZURE_SCOPE                 Permission scope (User.Read)

OTLP Gateway Payload Structure:

Traces (POST /v1/traces):
    Content-Type: application/json
    Body: { "resourceSpans": [{ "resource": { "attributes": [...] }, "scopeSpans": [...] }] }

Logs (POST /v1/logs):
    Content-Type: application/json
    Body: { "resourceLogs": [{ "resource": { "attributes": [...] }, "scopeLogs": [...] }] }

Resource Attributes (both traces and logs):
    service.name: "drs-salesplanning"
    service.version: "1.0.0"
    deployment.environment: "dev" | "uat" | "prod"

_______________________________________________________________________________________


10. Sample Requests/Responses

Complete Login Flow (Dev Environment):

    Step 1: GET /
    Response: HTML login page (Blade rendered)

    Step 2: POST /login/email
    Content-Type: application/x-www-form-urlencoded
    Body: email=planner@tvsmotor.com&_token={csrf_token}
    Response (role=1): 302 Redirect → /retailplanupload
    Response (role=2): 302 Redirect → /amdretailplan
    Response (role=3): 302 Redirect → /status
    Response (invalid): 302 Redirect → / (with error flash)

Plan Upload Flow:

    Step 1: GET /getlastdate?month=02-25&type=retail
    Response: [{"maxdate":"2025-02-01","disabled":0,"dt":{"processdate":"2025-03-01","cutoffday":25}}]

    Step 2: POST /validateretailplan
    Content-Type: multipart/form-data
    Body: file=[retail_plan.xlsx]

    Success Response:
    {"error":[],"warning":[],"final_arr":[{"APN_Date":"2025-03-01","APN_Area_id":5,"APN_Model_id":12,"APN_Retail_plan_value":150},...]}

    Failure Response:
    {"error":["Model scooterx : unknown","Area InvalidCity : unknown(1)","Area Chennai : missing"],"warning":[],"final_arr":[]}

    Step 3: POST /uploadretailplan
    Response: {"status":"success","message":"Retail plan uploaded successfully"}

AMD Plan Operations:

    GET /getplanmonthconfig
    Response: {"cutoffday":25,"amcutoffday":28,"processdate":"2025-03-01"}

    GET /getamddata?area=5&month=2025-03-01
    Response: [
        {"dealer_id":101,"dealer_code":"CHN001","dealer_name":"Chennai Motors","Jupiter":10,"Apache":5,"Ntorq":8,"total":23},
        {"dealer_id":102,"dealer_code":"CHN002","dealer_name":"TVS Showroom","Jupiter":12,"Apache":7,"Ntorq":6,"total":25}
    ]

    POST /saveamdretailplan
    Content-Type: application/json
    Body: {"data":[{"dealer_id":101,"model_id":12,"plan_value":11},{"dealer_id":101,"model_id":13,"plan_value":6}],"area":5}
    Response: {"messege":"Plan saved and confirmed successfully"}

Admin Operations:

    GET /getroles
    Response: [{"id":1,"role":"Sales Planner"},{"id":2,"role":"Area Manager"},{"id":3,"role":"Status Viewer"},{"id":4,"role":"Admin"}]

    GET /getusers?per_page=10&page=1&filter=Chennai
    Response: {
        "current_page":1,
        "data":[{"id":5,"name":"Raj Kumar","email":"raj@tvsmotor.com","roleId":2,"role":"Area Manager","areaid":"5, 6","areaname":"Chennai, Coimbatore","created_at":"15-Jan-2025"}],
        "total":3,"per_page":10,"last_page":1
    }

    POST /saveuser
    Body: edit=0&name=New+User&user_email=newuser@tvsmotor.com&role=2&area=5
    Response: {"messege":"User Saved Successfully"}

    POST /resetareaplanstatus
    Body: ad_amd=1&areaid=5
    Response: {"messege":"Area status updated Successfully"}

_______________________________________________________________________________________


_______________________________________________________________________________________


Outbound (Who This Service Calls)

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| Azure Active Directory | GET | /oauth2/v2.0/authorize | OAuth2 SSO authentication |
| Microsoft Graph API | GET | /v1.0/me | Fetch user email after Azure AD auth |
| SendGrid | SMTP | smtp.sendgrid.net:587 | Plan status email notifications |
| OTEL Gateway | POST | http://otel-gw-logs.tvsmotor.com/v1/logs | Send structured logs to Loki |
| OTEL Gateway | POST | http://otel-gw-logs.tvsmotor.com/v1/traces | Send distributed traces to Tempo |

_______________________________________________________________________________________


External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| Azure Active Directory | Identity Provider | OAuth2 SSO for production login | Client credentials (tenant + client_id + secret) |
| Microsoft Graph API | REST API | Fetch authenticated user's email address | Bearer token from Azure AD |
| SendGrid | Email Gateway (SMTP) | Plan upload notifications, AMD/AD/Branch confirmations | API key |
| OTEL Gateway | Observability | Logs (Loki) and Traces (Tempo) export via OTLP HTTP | None (internal network) |

_______________________________________________________________________________________


Database & Storage

| Store | Type | Purpose |
|-------|------|---------|
| tvsmazoogsdbprd01-sp (sqlsrv) | Azure SQL Server | Primary — users, dealers, plans, status, models |
| tvsmazoogsdbprd01-townwise (sqlsrv2) | Azure SQL Server | Historical town-wise reference data |
| tvsmazoogsdbprd01-townwise (sqlsrv4) | Azure SQL Server | DMS (Dealer Management System) data |
| tvsmazoogsdbprd01-townwise (sqlsrv5) | Azure SQL Server | Power Automate pilot data |
| storage/app/ (local filesystem) | File Storage | Temporary Excel file storage during upload validation |
| storage/logs/ (local filesystem) | Log Files | Laravel application logs with trace context |

_______________________________________________________________________________________


Events & Messaging

This service does NOT use any message queue or event bus. All processing is synchronous within the HTTP request lifecycle. Post-confirmation plan generation runs via terminable middleware (after HTTP response is sent to client).
