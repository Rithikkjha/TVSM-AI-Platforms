README — DRS Sales Planning Application

Purpose: Developer onboarding and setup guide for the DRS Sales Planning Application repository.
Version: 1.0 | Author: Samyucktha S

_______________________________________________________________________________________


1. Application Overview

The DRS (Dealer Retail Sales) Sales Planning Application is a web application for TVS Motor Company that manages the monthly retail sales planning lifecycle across all zones, areas, territories, and dealers. The system comprises:

    Backend: Laravel 7.24 (PHP 7.2.5+) with Blade templates for server-side rendering
    Frontend: Vue.js components + ag-Grid embedded within Blade templates
    Database: SQL Server (4 connections for primary, historical, and auxiliary data)

The application supports Sales Planner Excel uploads (area×model retail plans), automatic dealer-level plan generation using historical sales ratios, Area Manager plan review/edit/confirm via ag-Grid, AD and Branch plan confirmation workflows, zone-wide status dashboards, and admin user/area management.

_______________________________________________________________________________________


2. Setup Instructions

Prerequisites:

Component           Requirement
PHP                 7.2.5+ (with extensions: sqlsrv, pdo_sqlsrv, curl, openssl, mbstring, xml, zip, gd)
Composer            2.x
SQL Server          2016+ (or Azure SQL)
SQL Server Driver   Microsoft ODBC Driver 17+ for SQL Server
IIS                 Windows Server (production) or php artisan serve (local dev)
Node.js             12+ (for frontend asset compilation, optional)
IDE                 VS Code with PHP Intelephense extension
Git                 2.30+

Repository Clone:

    git clone <repository-url>
    cd tvsm-salesplanning-app-repo

_______________________________________________________________________________________


3. Local Development Steps

Backend Setup:

    cd tvsm-salesplanning-app-repo
    composer install
    cp .env.example .env
    php artisan key:generate

    # Configure .env with database credentials (see section 4)

    php artisan serve
    # Runs on http://localhost:8000

Database Setup:

    Ensure SQL Server is running and accessible
    Create the required databases
    Import the database schema (no migrations — schema is managed externally)
    Ensure all tables exist (see Key Tables below)

    Key Tables Required:
        user_USR, role_RLE, user_area_UAR, area_ARE, territory_TRY,
        dealer_DLR, dealer_link_DLK, model_MDL, config_CFG,
        dealer_model_plan_DPN, dealer_model_sales_DMS,
        area_model_plan_APN, area_model_sales_AMS,
        active_dealers_for_month_IDM, plan_status_PST,
        institution_model_plan_IPN, week_WEK, week_days_WDY,
        weekly_percentage_plan_WPP, daily_percentage_plan_DPP,
        dealer_other_plan_DOP, dealer_mode_plan_DMP,
        day_model_plan_DYM, day_mode_plan_DYO, mode_MDE

Authentication Setup (Local):

    Leave AZURE_CLIENT_ID empty in .env to use email-based login
    Add a test user to user_USR table with USR_Status=1 and desired role
    Login with that email address at http://localhost:8000

_______________________________________________________________________________________


4. Environment Variables

Primary Configuration (.env):

Variable                    Description                                 Example
APP_NAME                    Application name                            "DRS Sales Planning"
APP_ENV                     Environment                                 local / production
APP_KEY                     Laravel encryption key                      base64:xxxxx (auto-generated)
APP_DEBUG                   Debug mode                                  true (local) / false (prod)
APP_URL                     Application base URL                        http://localhost:8000

DB_CONNECTION               Default database driver                     sqlsrv
DB_HOST                     Primary SQL Server host                     localhost
DB_PORT                     Primary SQL Server port                     1433
DB_DATABASE                 Primary database name                       drs_salesplanning
DB_USERNAME                 Primary DB username                         (configured per environment)
DB_PASSWORD                 Primary DB password                         (configured per environment)

DB_HOST2                    Secondary SQL Server host                   localhost
DB_PORT2                    Secondary SQL Server port                   1433
DB_DATABASE2                Secondary database name                     drs_historical
DB_USERNAME2                Secondary DB username                        (configured)
DB_PASSWORD2                Secondary DB password                        (configured)

DB_HOST4                    Tertiary SQL Server host                    (configured)
DB_DATABASE4                Tertiary database name                      (configured)
DB_HOST5                    Quaternary SQL Server host                  (configured)
DB_DATABASE5                Quaternary database name                    (configured)

AZURE_TENANT_ID             Azure AD tenant ID                          (leave empty for email login)
AZURE_CLIENT_ID             Azure AD client ID                          (leave empty for email login)
AZURE_CLIENT_SECRET         Azure AD client secret                      (leave empty for email login)
AZURE_RESOURCE              Azure AD resource/object ID                 (optional)
AZURE_SCOPE                 Azure AD permission scope                   User.Read

MAIL_MAILER                 Mail driver                                 smtp
MAIL_HOST                   SMTP server                                 smtp.office365.com
MAIL_PORT                   SMTP port                                   587
MAIL_USERNAME               SMTP username                               (configured)
MAIL_PASSWORD               SMTP password                               (configured)
MAIL_ENCRYPTION             SMTP encryption                             tls

OTEL_ENABLED                Enable telemetry export                     true / false
OTEL_SERVICE_NAME           Service name for telemetry                  drs-salesplanning
OTEL_EXPORTER_OTLP_ENDPOINT OTLP gateway endpoint                      http://otel-gw-logs.tvsmotor.com
SERVICE_VERSION             Application version                         1.0.0
DEPLOYMENT_ENVIRONMENT      Deployment environment tag                  dev / uat / prod

_______________________________________________________________________________________


5. Build Instructions

Local Development:

    composer install                 # Install PHP dependencies
    php artisan serve                # Start development server (port 8000)
    php artisan config:clear         # Clear config cache (after .env changes)
    php artisan route:clear          # Clear route cache
    php artisan view:clear           # Clear compiled views

Production Build:

    composer install --no-dev --optimize-autoloader
    php artisan config:cache         # Cache configuration
    php artisan route:cache          # Cache routes
    php artisan view:clear           # Clear view cache

Frontend Assets (if applicable):

    npm install                      # Install Node dependencies (optional)
    npm run dev                      # Compile assets for development
    npm run production               # Compile assets for production

Note: Frontend assets (Vue.js, ag-Grid) may be loaded via CDN in Blade templates rather than compiled locally. Check resources/views/ for script tags.

_______________________________________________________________________________________


6. Deployment Steps

The project is deployed on IIS (Windows Server / Azure App Service):

Deployment Process:

    1. Pull latest code to deployment folder
    2. Run: composer install --no-dev --optimize-autoloader
    3. Ensure .env file has production configuration
    4. Run: php artisan config:cache
    5. Run: php artisan route:cache
    6. Run: php artisan view:clear
    7. Set IIS document root to /public folder
    8. Ensure IIS URL Rewrite module is installed
    9. Verify web.config exists in /public for URL rewriting
    10. Restart IIS application pool
    11. Smoke test: Access application, verify login works

IIS Configuration:

    Document Root: {app_path}/public
    PHP Handler: PHP 7.2.5+ via FastCGI
    URL Rewrite: All requests to index.php (Laravel routing)
    HTTPS: Required (TLS certificate configured in IIS)

Environment Promotion:

    DEV: Auto-deploy on push (email login enabled)
    UAT: Manual deployment (Azure AD enabled, test data)
    PROD: Manual deployment with approval (Azure AD enabled, production data)

Rollback Strategy:

    Keep previous deployment folder as backup
    Rollback: Point IIS to previous folder, restart app pool
    Database: No automated rollback — schema changes are manual and backward-compatible

_______________________________________________________________________________________


7. Testing Instructions

No automated test suite is currently active. Manual testing approach:

Backend Testing:

    Start application: php artisan serve
    Login with test email (dev mode)
    Verify role-based routing:
        Role 1 → /retailplanupload
        Role 2 → /amdretailplan
        Role 3 → /status
        Role 4 → /retailplanupload (with admin access)

Plan Upload Testing:

    Prepare Excel file matching template format (Area column + Model columns)
    Navigate to /retailplanupload
    Upload via "Validate" button → verify validation response
    If valid, click "Upload" → verify data in area_model_plan_APN
    Verify dealer plans generated in dealer_model_plan_DPN

AMD Plan Testing:

    Login as Area Manager (role=2) with area assignment in user_area_UAR
    Navigate to /amdretailplan
    Verify dealer×model grid loads with generated plan values
    Edit values in ag-Grid → Save → Verify plan_status_PST = 2

Utility Commands (via browser for quick testing):

    /clear-cache       — Clear application cache
    /clear-config      — Rebuild config cache
    /clear-view        — Clear compiled views
    /clear-route       — Clear route cache
    /clear-compiled    — Clear compiled classes
    /clear-optimize    — Clear all optimizations

_______________________________________________________________________________________


8. Folder Structure

tvsm-salesplanning-app-repo/
    app/
        Http/
            Controllers/                    11 controllers (business logic)
            Middleware/                      Auth, session, post-processing middlewares
        Imports/                             Maatwebsite Excel import classes
        Telemetry/
            OtelTracer.php                  OpenTelemetry OTLP integration
        User.php                            Eloquent model (user_USR)
        Dealer.php                          Eloquent model (dealer_DLR)
        Models.php                          Eloquent model (model_MDL)
        constants.php                       Application constants
    config/
        app.php                             Application configuration
        database.php                        4 SQL Server connections
        azure.php                           Azure AD configuration
        mail.php                            SMTP email configuration
    resources/
        views/                              Blade templates (8 views + login)
        js/                                 Vue.js components
    routes/
        web.php                             All application routes (~160 route definitions)
    storage/
        app/                                Temporary file storage (Excel uploads)
        logs/                               Laravel log files
    public/
        index.php                           Application entry point
        .htaccess / web.config              URL rewriting rules
    composer.json                           PHP dependency definitions
    .env.example                            Environment variable template
    docs/                                   Generated documentation (this folder)

_______________________________________________________________________________________


9. Common Troubleshooting

Issue                                   Cause                                       Solution
Login redirects back to /               User email not in user_USR or USR_Status≠1  Add user to user_USR with Status=1
"Session FAILED" error on AJAX          Session expired (idle timeout)              Re-login; check session lifetime in .env
Excel upload "No valid Models found"    Model names in Excel don't match model_MDL  Ensure Excel header matches MDL_Model_name exactly (case-insensitive)
Excel upload "Area X : unknown"         Area not in active_dealers_for_month_IDM    Ensure IDM table has entries for plan month
"An error occurred" on any endpoint     PHP exception in controller                 Check storage/logs/laravel.log for stack trace
AMD plan page shows no data             No plans generated for area/month           Run plan upload first (Sales Planner role)
Azure AD login fails                    AZURE_CLIENT_ID misconfigured               Verify Azure AD config in .env; check tenant/client IDs
Blank page after login                  .env APP_DEBUG=false hides errors            Set APP_DEBUG=true temporarily; check logs
Plan status stuck at 0                  afterProcessSalesPlan middleware failed      Check logs for middleware exceptions
Database connection error               SQL Server driver not installed              Install Microsoft ODBC Driver 17+ and php_sqlsrv extension
Email notifications not sending         SMTP credentials incorrect                  Verify MAIL_* variables in .env; test with php artisan tinker
OTLP telemetry not reaching gateway     Network/firewall blocking outbound          Check connectivity to otel-gw-logs.tvsmotor.com; OTEL_ENABLED=false to disable

_______________________________________________________________________________________


10. Maintainer/Contact

Role                    Contact
Application Team        TVS Motor Company — D2C Digital Engineering
Ticket System           Internal JIRA / ServiceNow
UAT Environment         (Internal UAT URL — configured per deployment)
Production Environment  (Internal Production URL — configured per deployment)

Related Documentation:

    High Level Code Document — DRS Sales Planning Application (docs/HLC.md)
    High Level Design — DRS Sales Planning Application (docs/HLD.md)
    Low Level Design — DRS Sales Planning Application (docs/LLD.md)
    API Specification — DRS Sales Planning Application (docs/API_SPEC.md)

Key Contacts:

    For plan upload issues: Sales Planning team (zone-level coordinators)
    For user access issues: Admin users (role=4) can manage via /admin panel
    For infrastructure issues: DevOps / Azure App Service team
    For telemetry/observability: D2C Observability team (Loki + Tempo dashboards)

_______________________________________________________________________________________
