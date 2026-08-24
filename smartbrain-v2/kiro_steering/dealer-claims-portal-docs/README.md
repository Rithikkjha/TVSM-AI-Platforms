README — Dealer Claims Portal

Purpose: Developer onboarding and setup guide for the Dealer Claims Portal repositories.
Version: 1.0 | Author: Samyucktha S

_______________________________________________________________________________________


1. Application Overview

The Dealer Claims Portal is a full-stack web application for TVS Motor Company that manages dealer reimbursement claims and Test Ride Vehicle (TRV) norm processing. The system comprises:

    Frontend: React 17 SPA with MobX state management and Ant Design UI (repository: dealer-dashboard)
    Backend: ASP.NET Core 7 Web API with Entity Framework Core (repository: BS2.0Backend_Integration)

The portal supports Dealer login with OTP, booking claim management across 5 workflow tabs, TRV norm approval with Area Manager email workflows, vehicle document upload with AI compliance validation, and SAP-based financial settlement.

_______________________________________________________________________________________


2. Setup Instructions

Prerequisites:

Component       Requirement
Node.js         v16+ (for frontend)
.NET SDK        7.0
SQL Server      2019+ (or Azure SQL)
IDE             VS Code (frontend) + Visual Studio 2022 (backend)
Git             2.30+

Repository Clone:

    git clone <frontend-repo-url>
    cd dealer-dashboard

    git clone <backend-repo-url>
    cd BS2.0Backend_Integration

_______________________________________________________________________________________


3. Local Development Steps

Frontend:

    cd dealer-dashboard
    npm install
    npm start
    # Runs on http://localhost:3000

Backend:

    cd BS2.0Backend_Integration
    dotnet restore
    dotnet run
    # Runs on http://localhost:5201

Database:
    The application uses EF Core with existing database schema (database-first).
    Ensure all required tables exist: BookingClaim, PaymentDetail, VehicleDetail,
    DealerTRNorms, TRV_Norms, ExistingTRVDetails, Tb1008UserDetails,
    tb_1002_SAP_Details, BookingTopicLog.

_______________________________________________________________________________________


4. Environment Variables

Frontend (src/components/stores/APIEndpoints.js):

Variable        Description                 Example
backendHost     Backend API base URL        http://localhost:5201/api/

Toggle environment by commenting/uncommenting the appropriate line in APIEndpoints.js.

Backend (appsettings.json):

Section             Key                                 Description
ConnectionStrings   DbConn                              Primary SQL Server connection
ConnectionStrings   TravelNew                           Secondary database for AM/TM emails
AppSettings         BRIDGE_AUTH_TOKEN                    JWT signing secret
ServiceBusSettings  ServiceBusEndpoint                  Azure Service Bus connection
ServiceBusSettings  TopicName                           Topic (dev.booking / uat.booking / prod.booking)
SAP                 TokenUrl, ClientId, ClientSecret     SAP CPI integration
DataScience         Url, BearerToken                    Databricks OCR endpoint
SMTP                SMTP_HOST, EmailFrom, SMTP_PASSWORD Email delivery (SendGrid)
DMS                 BaseUrl                             Dealer Management System API
Airtel              AirtelBaseURL, OA, DLT IDs          SMS OTP gateway

_______________________________________________________________________________________


5. Build Instructions

Frontend:

    npm start               # Development (hot reload)
    npm run build           # Production build → output: build/
    npm run deploy          # Deploy to S3 (if configured)

Backend:

    dotnet build                                # Debug build
    dotnet publish --configuration Release      # Release → bin/Release/net7.0/publish/

_______________________________________________________________________________________


6. Deployment Steps

The project uses Azure DevOps CI/CD pipelines:

CI Pipeline (dealerportal-api-uat-ci.yaml):
    Trigger: Push to branch
    Agent: windows-latest
    Steps: dotnet restore → dotnet publish → Publish artifact (drop)

CD Pipeline (dealerportal-api-cd.yaml):
    Trigger: CI completion
    Steps: Download artifact → Create IIS App (/BS) → Deploy WebApp.zip
    Target: C:\inetpub\wwwroot\Bs2.0Backend
    AppPool: BsBackendAppPool

Environments: DEV (auto) → UAT (manual approval) → PROD (manual approval)

_______________________________________________________________________________________


7. Testing Instructions

No automated test projects currently exist. Manual testing:

    Backend: Use Swagger UI at http://localhost:5201/swagger (Development only)
    Frontend: npm test (React testing library, limited coverage)
    Integration: Start backend → start frontend → login with test credentials → verify flows

_______________________________________________________________________________________


8. Folder Structure

dealer-dashboard/                       Frontend
    src/components/dealerConsole/        Booking claim management (5 tabs)
    src/components/dealerDashboardTRV/   TRV module
    src/components/stores/              MobX stores (AppStore, TRVStore)
    src/components/Modals/              Shared modals
    docs/                               Generated documentation
    package.json

BS2.0Backend_Integration/               Backend
    Controllers/                        6 API controllers
    Services/                           Business logic
    Repository/                         Data access (30+ files)
    Entities/                           EF Core entities (28 files)
    TopicListener/                      Service Bus consumer
    appsettings.json                    Configuration
    CustomerBay.csproj                  Project file (.NET 7)

_______________________________________________________________________________________


9. Common Troubleshooting

Issue                               Cause                                   Solution
CORS error in browser               Backend not allowing frontend origin    Add frontend URL to CORS policy in Program.cs
"Token is missing" error            JWT not sent in headers                 Verify Token header is set in APIProxy.js
OTP not received                    Airtel gateway or phone not active      Check DMS employee status API response
Service Bus not processing          Connection string or topic mismatch     Verify ServiceBusSettings in appsettings.json
File upload fails (413)             File exceeds IIS limit                  Check RequestSizeLimit (100MB)
"Duplicate FrameNo" error           Vehicle already exists for norm         Check ExistingTRVDetails for existing record
SAP timeout                         SAP CPI slow response                   Retry tracked in logs (max 3)
Swagger not loading                 Non-development environment             Swagger only enabled in Development
DB connection timeout               Connection pooling disabled             Remove Pooling=False from connection string
JWT expired                         120-minute session timeout              Frontend auto-logouts; user re-authenticates

_______________________________________________________________________________________


10. Maintainer/Contact

Role                    Contact
Support Email           dealersupport@tvsmotor.com
Ticket System           tvsmotor.bolddesk.com/support
UAT Frontend            https://uat-bookingapi.tvsmotor.net/dealers
UAT Backend             https://uat-bookingapi.tvsmotor.net/BS/api/
Production Frontend     https://iqubeprod.tvsmotor.com/dealers/
Production Backend      https://iqubeprod.tvsmotor.com/DealerDashboardApi/api/
Confluence Space        tvsmotorcompany.atlassian.net/wiki/spaces/D2W

_______________________________________________________________________________________


Related Documentation

    High Level Code Document — Dealer Claims Portal
    High Level Design — Dealer Claims Portal
    Low Level Design — Dealer Claims Portal
    API Specification — Dealer Claims Portal

_______________________________________________________________________________________


_______________________________________________________________________________________


Service Identity

Field               Value
Service Name        dealer-claims-portal
Repo (Frontend)     dealer-dashboard
Repo (Backend)      BS2.0Backend_Integration
Team                Dealer Portal Team
Deployment          IIS on Azure VM
Base URL (prod)     https://iqubeprod.tvsmotor.com/DealerDashboardApi/api/
Base URL (UAT)      https://uat-bookingapi.tvsmotor.net/BS/api/

Ownership and Contacts

Role                Contact
Support Email       dealersupport@tvsmotor.com
Ticket System       tvsmotor.bolddesk.com/support
Confluence          tvsmotorcompany.atlassian.net/wiki/spaces/D2W

_______________________________________________________________________________________
