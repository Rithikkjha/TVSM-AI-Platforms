High Level Design — Dealer Claims Portal

Purpose: Architecture-level documentation for external engineering partners covering system design, deployment, integrations, and resiliency considerations.
Version: 1.0 | Author: Samyucktha S | Status: CURRENT


_______________________________________________________________________________________


1. System Architecture

The Dealer Claims Portal follows a layered monolithic architecture with event-driven processing capabilities. The system is structured into distinct tiers deployed on Azure infrastructure.

┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
│  ┌──────────────┐ ┌────────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ Dealer Portal│ │Area Accountant │ │ Area Manager │ │  DMS Web Portal  │ │
│  │ (React SPA)  │ │  (SSO Portal)  │ │(Email Links) │ │   (Upstream)     │ │
│  └──────────────┘ └────────────────┘ └──────────────┘ └──────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
         │                    │                  │                │
         ▼                    ▼                  ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│         Dealer Claims Portal (ASP.NET Core 7 / IIS / Azure VM)              │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                    API Layer (Controllers)                          │     │
│  │ ┌────────────┐ ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ │     │
│  │ │DealerDash- │ │  TRV    │ │   SAP    │ │SSO Auth│ │ Bookings │ │     │
│  │ │board Ctrl  │ │  Ctrl   │ │   Ctrl   │ │  Ctrl  │ │   Ctrl   │ │     │
│  │ └────────────┘ └─────────┘ └──────────┘ └────────┘ └──────────┘ │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                Application Layer (Services)                         │     │
│  │ ┌────────────┐ ┌──────────────┐ ┌──────────┐ ┌─────────┐         │     │
│  │ │TRVServices │ │BookingsServic│ │LLMService│ │ Manager │         │     │
│  │ └────────────┘ └──────────────┘ └──────────┘ └─────────┘         │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │           Domain Layer (Entities, Enumerations, Constants)          │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │     Infrastructure Layer (EF Core 7.0, Repositories, DbContext)     │     │
│  │ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │     │
│  │ │CustomerBayDBContext│  │TravelNewDbContext │  │  TRVRepository   │  │     │
│  │ │   (Primary DB)    │  │ (Email Lookups)  │  │                  │  │     │
│  │ └──────────────────┘  └──────────────────┘  └──────────────────┘  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────────┐     ┌──────────────────────┐
│   CustomerBay DB     │     │    TravelNew DB       │
│    (SQL Server)      │     │    (SQL Server)       │
│ Bookings, Claims,    │     │  AM/TM Email Lookups  │
│ TRV, Users, SAP      │     │                      │
└──────────────────────┘     └──────────────────────┘


                                                     ┌────────────────────────┐
                                                     │   External Services    │
                                                     │                        │
                                                     │  DMS REST API          │
                                                     │  (Branches, Frame No)  │
                                                     │                        │
                                                     │  SAP CPI               │
                                                     │  (OAuth2 — Claims)     │
                                                     │                        │
                                                     │  Azure Databricks      │
                                                     │  (OCR Compliance)      │
                                                     │                        │
                                                     │  Azure Service Bus     │
                                                     │  (Booking Events)      │
                                                     │                        │
                                                     │  Azure AD              │
                                                     │  (SSO — OpenID)        │
                                                     │                        │
                                                     │  Airtel SMS (OTP)      │
                                                     │                        │
                                                     │  SendGrid (Emails)     │
                                                     │                        │
                                                     │  Azure DevOps (CI/CD)  │
                                                     └────────────────────────┘

Architecture Description:

Presentation Layer:
    React 17 SPA with MobX state management, Ant Design UI components, and AG Grid for data tables. Served as static assets from IIS. Three client types: Dealer Portal, Area Accountant Portal (SSO), and Area Manager (Email Links).

API Layer:
    ASP.NET Core 7 Web API hosted on IIS behind Kestrel. Six controllers handling dealer operations, TRV management, SAP integration, area accountant workflows, SSO authentication, and data export.

Service Layer:
    Business logic orchestration including TRVServices (norm/vehicle/claim management), BookingsServices (data retrieval), LLMService (AI compliance), Manager (event routing), and SaveFileService (file I/O).

Data Layer:
    Entity Framework Core 7.0.2 with two Azure SQL databases (CustomerBay for primary data, TravelNew for email lookups). IIS local file storage for uploaded documents.

Integration Layer:
    Outbound connections to DMS (REST/SOAP), SAP CPI (OAuth2+REST), Azure Databricks (REST), Airtel SMS, and SendGrid. Inbound event consumption from Azure Service Bus (AMQP).


_______________________________________________________________________________________


2. Major Components/Services

Component                       Technology                                  Responsibility
Frontend (dealer-dashboard)     React 17 + MobX 6 + Ant Design + AG Grid   SPA for dealers — booking management, TRV workflows, document upload
Backend API (CustomerBay)       ASP.NET Core 7 Web API                      REST endpoints, business logic, event processing, file management
Database (Primary)              Azure SQL Server (CustomerBayDBContext)      Bookings, claims, TRV norms, vehicles, users, SAP records
Database (Secondary)            Azure SQL Server (TravelNewDbContext)        AM/TM email lookups via stored procedure
Service Bus Topic Listener      Azure Service Bus (AMQP)                    Consumes booking lifecycle events (Created, Cancelled, Invoiced, FullPayment)
Export Queue Processor          Azure Service Bus Queue                     Async Excel/CSV export generation
File Storage                    IIS Local Disk (wwwroot)                    Invoice, Insurance, RC, HSRP, Declaration document storage

Layer Interaction Pattern:

Frontend (React SPA)
  │ REST API (JSON + JWT Token header)
  ▼
Backend Controllers (6)
  ├── DealerDashboardController (/api/)
  ├── TRVController (/api/TRV/)
  ├── SAPController (/api/sap/)
  ├── BookingsController (/api/areaAccountant/)
  ├── SsoAuthController (/auth/sso/)
  └── BookingExport (/api/areaAccountant/)
  │
  ▼
Services Layer
  ├── TRVServices (TRV orchestration)
  ├── BookingsServices (booking queries)
  ├── LLMService (AI name matching)
  ├── SaveFileService (file I/O)
  ├── Manager (event routing)
  └── Email helpers (SMTP/SendGrid)
  │
  ▼
Repository Layer (EF Core)
  ├── TRVRepository
  ├── DealerBookingsRepository
  ├── LoginRepository
  └── TrvDealerClaimPortalRepository
  │
  ▼
Azure SQL Server (2 databases)


_______________________________________________________________________________________


3. Deployment Architecture

┌───────────┐     ┌────────────────────────┐     ┌──────────────────────────┐
│ Developer │────▶│  CI Pipeline           │────▶│  CD Pipeline             │
│ (Git Push)│     │  (Azure DevOps)        │     │  (deploy-template)       │
└───────────┘     │  • dotnet restore      │     │  • Download artifact     │
                  │  • dotnet publish       │     │  • Deploy to IIS         │
                  │  • Publish artifact     │     │  • TakeAppOffline        │
                  └────────────────────────┘     └────────────┬─────────────┘
                                                              │
                  ┌───────────┬───────────────┬───────────────┘
                  ▼           ▼               ▼
            ┌──────────┐ ┌──────────┐ ┌────────────┐
            │   DEV    │ │   UAT    │ │    PROD    │
            │  (Auto)  │ │ (Manual) │ │  (Manual)  │
            └──────────┘ └──────────┘ └────────────┘

 ╔══════════════════════════════════════════════════════════════════════╗
 ║              Azure Virtual Machine (IIS — Windows Server)            ║
 ║                                                                      ║
 ║  ┌─────────────────────────────┐  ┌─────────────────────────────┐  ║
 ║  │ Backend API (.NET 7)         │  │ Frontend (React Build)       │  ║
 ║  │ Virtual App: /BS             │  │ Virtual App: /bsvi           │  ║
 ║  │ AppPool: BsBackendAppPool    │  │ (Static files)              │  ║
 ║  │ Port: 443 (HTTPS)           │  │ React 17 + MobX + Ant Design│  ║
 ║  └─────────────────────────────┘  └─────────────────────────────┘  ║
 ║                                                                      ║
 ║  ┌─────────────────────────────────────────────────────────────────┐║
 ║  │  File Storage (Local Disk)                                       │║
 ║  │  C:\inetpub\wwwroot\TVS-BSIV\ (Invoice, Insurance, Ack)         │║
 ║  │  C:\inetpub\wwwroot\TVS-TRV\  (RC, Insurance, HSRP, Declaration)│║
 ║  └─────────────────────────────────────────────────────────────────┘║
 ╚══════════════════════════════════════════════════════════════════════╝
                    │                              │
     ┌──────────────┴──────────────┐  ┌───────────┴───────────────┐
     ▼                             ▼  ▼                           ▼
┌────────────────────────────┐  ┌────────────────────────────┐
│ Azure SQL (CustomerBay DB) │  │ Azure Service Bus           │
│ • BookingClaim             │  │ • Topic: uat.booking        │
│ • TRV_Norms               │  │ • Queue: export_queue       │
│ • ExistingTRVDetails       │  └────────────────────────────┘
│ • Tb1008UserDetails        │
│ • tb_1002_SAP_Details      │  ┌────────────────────────────┐
└────────────────────────────┘  │ Azure AD (Entra ID)        │
                                │ • SSO (OpenID Connect)     │
┌────────────────────────────┐  └────────────────────────────┘
│ Azure SQL (TravelNew DB)   │
│ • sp_GetDealerAMTMMails    │  ┌────────────────────────────┐
└────────────────────────────┘  │ Serilog (Observability)    │
                                │ • Logs/log-yyyyMMdd.txt    │
                                └────────────────────────────┘

Current Deployment Model:

Aspect                  Details
Hosting                 IIS on Azure Virtual Machine (Windows Server)
Backend Virtual App     /BS (AppPool: BsBackendAppPool, No Managed Code)
Frontend Virtual App    /bsvi (static React build)
Port                    443 (HTTPS via IIS)
Framework               .NET 7
CI/CD                   Azure DevOps (ci-pipeline.yaml + cd-pipeline.yaml)
Environments            Dev → UAT → Production
Rollback Strategy       Re-deploy previous artifact from Azure DevOps drop

CI/CD Pipeline Flow:

CI Pipeline (dealerportal-api-uat-ci.yaml):
  1. Trigger: Push to branch
  2. Agent: windows-latest
  3. dotnet restore
  4. dotnet publish (WebDeploy package)
  5. Publish artifact as "drop"

CD Pipeline (dealerportal-api-cd.yaml):
  1. Trigger: CI pipeline completion
  2. Download artifact from CI
  3. Create/Update IIS Application (/BS, AppPool: BsBackendAppPool)
  4. Deploy WebApp.zip to C:\inetpub\wwwroot\Bs2.0Backend
  5. TakeAppOffline during deployment

Environment Promotion:
  DEV (Auto deploy) → UAT (Manual approval) → PROD (Manual approval)


_______________________________________________________________________________________


4. Database Interactions

Connection                      Database            Purpose                                                     Type
ConnectionStrings.DbConn        CustomerBay DB      Primary transactional data (BookingClaim, PaymentDetail,     Azure SQL
                                                    VehicleDetail, TRVNorms, ExistingTRVDetail, Users, SAP)
ConnectionStrings.TravelNew     TravelNew DB        AM/TM email lookups via sp_GetDealerAMTMMails               Azure SQL

Data Access Patterns:
    Entity Framework Core 7.0.2 with Code-First approach
    Repository pattern with explicit transactions for TRV vehicle save + file upload
    Raw SQL (SqlCommand) used for SAP document insertion where EF tracking is not suitable
    DbContext registered as Scoped (per-request lifetime)
    UnitOfWork pattern via EF SaveChangesAsync within transactions

Key Tables:
    BookingClaim (PK: UUID) — Core booking/claim data
    PaymentDetail (FK: UUID) — Payment transactions (partial/full)
    VehicleDetail (FK: UUID) — Vehicle model/variant info
    DealerTRNorms (PK: Id, Unique: DealerCode+SapBranchId) — TRV norm definitions
    TRV_Norms (PK: Id) — Individual norm records with approval/claim status
    ExistingTRVDetails (PK: TRVDetailId) — Vehicle details with document upload tracking
    TrvDeclarationFile — Declaration documents per norm
    Tb1008UserDetails — User accounts (dealers, admins, AM/AA)
    tb_1002_SAP_Details — SAP document records
    BookingTopicLog — Service Bus message processing audit


_______________________________________________________________________________________


5. API Integrations

┌────────────────────┐                    ┌─────────────────────────────────────┐
│  Dealer Browser    │─── REST (JWT) ────▶│  Dealer Claims Portal Backend       │
│  (React SPA)       │                    │  (ASP.NET Core 7 / IIS)             │
└────────────────────┘                    └──────────────────┬──────────────────┘
                                                             │
                          Backend calls the following services:
                                                             │
     ┌──────────────┬──────────────┬──────────────┬──────────┴───────┬───────────────┐
     ▼              ▼              ▼              ▼                  ▼               ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌───────────────┐ ┌────────────┐
│ DMS API  │ │ SAP CPI  │ │Azure Service │ │ Azure AD │ │  Databricks   │ │Airtel SMS +│
│  (REST)  │ │(OAuth2+  │ │    Bus       │ │  (OIDC)  │ │   (OCR/AI)    │ │  SendGrid  │
│          │ │  REST)   │ │  (AMQP)      │ │          │ │               │ │            │
│Branches  │ │Claims    │ │Booking Events│ │SSO for   │ │Document       │ │OTP +       │
│Frame No  │ │Settlement│ │Export Queue  │ │AM / AA   │ │Compliance     │ │Email Notif │
│Variants  │ │          │ │              │ │          │ │               │ │            │
└──────────┘ └──────────┘ └──────────────┘ └──────────┘ └───────────────┘ └────────────┘
 Outbound    Outbound      Inbound         Bidirectional  Outbound         Outbound
 (REST)      (OAuth2)      (AMQP)          (OIDC)         (REST/Bearer)    (REST/SMTP)

Internal APIs (Frontend → Backend):

Route Prefix                Controller                      Auth
/api/                       DealerDashboardController       JWT Token header
/api/TRV/                   TRVController                   JWT Token header
/api/sap/                   SAPController                   JWT Token header
/api/areaAccountant/        BookingsController              JWT Token header
/auth/sso/                  SsoAuthController               Cookie + OIDC

External API Integrations:

External System     Endpoint Pattern                                    Auth                Timeout
DMS Branches        {DMS_BASE}/OnlineMasterAPI/Master.asmx/LoadBranch2  None                Default
DMS Frame Details   {DMS_BASE}/OnlineSalesAPI/Sales/TrvFrameNumberDetails None              Default
DMS Variants        {DMS_BASE}/OnlineSalesAPI/load-variants-by-series   None                Default
SAP Token           {SAP_TOKEN_URL} (client_credentials)                Basic Auth          Default
SAP Claim API       {SAP_API_URL}                                       Bearer (OAuth2)     30 seconds
Databricks OCR      {DS_URL}/invocations                                Bearer token        60 seconds
Airtel SMS          digimate.airtel.in:44111/BulkPush/InstantJsonPush   Payload-based       Default
DMS Employee        SOAP WebService                                     Username/Password   Default


_______________________________________________________________________________________


6. Authentication/Authorization Flow

Dealer Authentication (JWT + OTP):
1. Dealer enters username + password → POST /api/login
2. Backend validates against Tb1008UserDetail (encrypted password)
3. For Role 10 (Dealer): returns credentials, no JWT yet
4. Dealer enters phone number → POST /api/SendOtp
5. Backend verifies employee active status via DMS SOAP Web Service
6. Generates 4-digit OTP → stores in DB → sends via Airtel SMS
7. Dealer enters OTP → POST /api/VerifyOtp
8. Backend validates OTP + 10-minute expiry
9. Issues JWT (HMAC SHA256, 120-min expiry, claims: Name=DealerId, Role=RoleId)
10. Frontend stores in localStorage, passes as "Token" header on all API calls
11. For Role 1 (SuperAdmin): JWT issued directly at step 2 (no OTP required)

SSO Authentication (Azure AD OpenID Connect):
1. AM/AA navigates to /auth/sso/login
2. Backend issues OpenID Connect Challenge → redirects to Microsoft login
3. User authenticates with corporate Microsoft account
4. Microsoft redirects to /signin-oidc with authorization code
5. Backend exchanges code for tokens
6. OnTokenValidated: extracts email, validates in DB (role 2/3/13), adds PortalRole claim
7. Cookie-based session established
8. Frontend calls /auth/sso/token → receives JWT for subsequent API calls

Authorization Matrix:

Role                    ID      Booking Data        TRV Norms               Claim Approval      SAP Posting
Super Admin             1       All dealers         All dealers             View only           No
Dealer (AMD/AD/SPD)    10      Own dealer only     Own dealer only         No                  No
Area Accountant         3       Region-based        Region-based            Approve/Reject      Triggers SAP
Area Manager            2/13    No direct access    Approve/Reject norms    No                  No


_______________________________________________________________________________________


7. External Systems

                         ┌──────────────────────────────────────┐
                         │  Dealer Claims Portal Backend        │
                         │  (ASP.NET Core 7 — IIS)              │
                         └──────────────────┬───────────────────┘
                                            │
     ┌──────────┬──────────┬───────────┬────┴────┬──────────┬──────────┐
     │          │          │           │         │          │          │
     ▼          ▼          ▼           ▼         ▼          ▼          ▼
┌─────────┐┌────────┐┌──────────┐┌─────────┐┌────────┐┌────────┐┌────────┐
│DMS REST ││SAP CPI ││ Azure    ││Azure AD ││Databr- ││Airtel  ││Send-   │
│API      ││(OAuth2)││ Service  ││(OIDC)   ││icks    ││SMS     ││Grid    │
│         ││        ││ Bus      ││         ││(OCR)   ││        ││(SMTP)  │
│Outbound ││Outbound││Inbound   ││Bidir.   ││Outbound││Outbound││Outbound│
│REST     ││REST    ││AMQP     ││OIDC     ││REST    ││REST    ││SMTP    │
└─────────┘└────────┘└──────────┘└─────────┘└────────┘└────────┘└────────┘
 Branches   Claims    Booking     SSO for    Document   OTP       Email
 Frame No   Settle-   Events      AM / AA    Compliance Delivery  Notifi-
 Variants   ment      Export Q                                    cations

Service                         Provider                Protocol            Purpose                                     Status
DMS (Dealer Management System)  TVS Internal            REST + SOAP         Branch lookup, frame validation, variants   ACTIVE
SAP CPI                         SAP BTP                 OAuth2 + REST       Financial document posting                  ACTIVE
Azure Service Bus               Microsoft Azure         AMQP WebSockets     Booking events + export queue               ACTIVE
Azure AD (Entra ID)             Microsoft Azure         OpenID Connect      SSO for AM/AA                               ACTIVE
Azure Databricks                Microsoft Azure         REST (Bearer)       OCR document compliance                     ACTIVE
Airtel SMS Gateway              Airtel (Third-party)    REST                OTP delivery (DLT registered)               ACTIVE
SendGrid / SMTP                 Twilio                  SMTP                Email notifications                         ACTIVE
DMS Web Service                 TVS Internal            SOAP                Employee active status verification         ACTIVE


_______________________________________________________________________________________


8. Infrastructure Dependencies

Component       Technology                              Purpose                         Criticality
Compute         Azure VM (Windows Server + IIS)         Application hosting             Critical
Database        Azure SQL Database (managed)            Primary + secondary stores      Critical
Messaging       Azure Service Bus (Standard tier)       Event processing + export       High
Identity        Azure Active Directory (Entra ID)       SSO for AM/AA                   Medium
File Storage    IIS Local Disk (C:\inetpub\wwwroot\)    Document storage                High
CI/CD           Azure DevOps Pipelines                  Build + deploy automation       Medium
DNS / Proxy     IIS (reverse proxy to Kestrel)          Request routing, TLS            Critical


_______________________________________________________________________________________


9. High-Level Sequence Flows

TRV Claim Settlement (End-to-End):

1. Dealer selects branch → Backend calls DMS API → returns branch list
2. Dealer searches → Backend returns classification, TRV count, capitalized count
3. Dealer submits norm approval → Backend inserts TRV_Norms → Email sent to AM
4. AM clicks approve link in email → Azure AD authenticates → Backend updates Is_Norm_Approved=1
5. Dealer enters 17-char frame number → DMS validates → auto-fills vehicle data
6. Dealer uploads RC, Insurance, HSRP → Backend saves transactionally (rollback on failure)
7. Background: Databricks OCR validates customer name + chassis match → compliance status saved
8. Dealer uploads declaration PDF → Claim_Status = ClaimSubmitted(1)
9. Email notification sent to Area Accountant
10. Area Accountant approves → Backend fetches SAP OAuth2 token → calls SAP CPI API
11. SAP returns success (TYPE="S") → Capitalization=2 (Capitalized), Claim=2 (Approved)
12. Notification email sent to dealer confirming settlement
13. If SAP returns error → SapResponse stored, claim stays pending for retry

Booking Claim Lifecycle:

1. Booking event arrives via Azure Service Bus topic (BOOKING_CREATED)
2. BookingServiceTopicListener deserializes, checks UUID+version for duplicates
3. Manager routes to BookingCreatedHandler → upserts BookingClaim + PaymentDetail + VehicleDetail
4. Dealer logs in (username/password + OTP) → searches bookings
5. System categorizes: Booking Update / Ready for Payment / Payment Status / Return Cases / One View
6. Dealer uploads invoice PDF + insurance PDF
7. Area Accountant approves documents (DocumentStatus = 1)
8. SAP document number generated → status updated to 3 (settled)


_______________________________________________________________________________________


10. Scalability and Resiliency Considerations

Current State:

Aspect                      Current Implementation
Compute                     Single Azure VM (IIS)
Database pooling            Disabled (Pooling=False)
Service Bus concurrency     MaxConcurrentSessions = 1
Caching                     No caching layer
File storage                Local IIS disk (not distributed)
Load balancing              None (single instance)

Resiliency Patterns Implemented:

Pattern                     Implementation
Retry                       SAP calls retry up to 3 times (tracked in Tb1002SapDetailsLog)
Dead Letter                 Service Bus messages abandoned on failure → DLQ after max delivery
Idempotency                 Messages checked by UUID + version before processing
Graceful Degradation        Databricks OCR is fire-and-forget; failure doesn't block vehicle save
Transactional Integrity     TRV vehicle save + file upload uses explicit DB transaction with rollback
Session Timeout             JWT expires after 120 min; frontend auto-logouts

Risks and Recommendations:

Risk                                        Impact      Likelihood  Mitigation
Single VM as single point of failure        Critical    Medium      Add Azure Load Balancer + multiple VMs
Database connection pooling disabled        High        High        Enable pooling with pool size 50+
Local file storage not distributed          High        Medium      Migrate to Azure Blob Storage
No caching for frequently accessed data     Medium      Medium      Add Redis for dealer branch data
Service Bus single session processing      Medium      Low         Increase MaxConcurrentSessions to 5-10
No circuit breaker for DMS calls            Medium      Low         Add Polly resilience policies

Metrics to Track:

Metric                      Source                  Alert Threshold     Priority
API Response Time (P95)     Serilog logs            > 3 seconds         P1
Error Rate (5xx)            Serilog logs            > 1%                P1
SAP Timeout Rate            Tb1002SapDetailsLog     > 5 retries/hour    P2
Service Bus DLQ depth       Azure Monitor           > 10 messages       P2
File Storage disk usage     OS monitoring           > 80%               P2


_______________________________________________________________________________________


Technology Stack Summary

Layer                   Technology                          Version
Frontend Runtime        React (Class Components)            17.0.2
State Management        MobX                                6.4.1
UI Framework            Ant Design + AG Grid                4.18.8 / 27.0.1
Backend Runtime         ASP.NET Core Web API                .NET 7
ORM                     Entity Framework Core               7.0.2
Database                Azure SQL Server                    Managed
Messaging               Azure Service Bus                   5.2.0
Auth (Dealer)           JWT Bearer (HMAC SHA256)            —
Auth (SSO)              Azure AD OpenID Connect             7.0.20
AI/ML                   FuzzySharp + Double Metaphone       2.0.2
Logging                 Serilog                             7.0.0
Email                   SendGrid / SMTP                     9.29.3
Hosting                 IIS on Azure VM                     —
CI/CD                   Azure DevOps Pipelines              YAML
Cloud                   Azure (SQL, Service Bus, AD, VM)    —


_______________________________________________________________________________________


Diagrams

All architecture diagrams are stored as draw.io files in:
    docs/diagrams/

Diagram Files and Confluence Placement:

File                                Insert Under This Section                           Content
system-architecture.drawio          Current Architecture (HLD)                          Full layered architecture: Clients → Controllers → Services → Domain → Infra → DBs + External Services sidebar
layer-interaction.drawio            Current Architecture → Layer Interaction Pattern     Detailed layer boxes with responsibilities list and dependency direction arrow
auth-flow.drawio                    Authentication and Authorization Flow                Dealer JWT+OTP sequence + SSO (Azure AD) sequence with all participants and error paths
deployment-infrastructure.drawio    Deployment and Rollout Plan                         CI/CD pipeline (Dev→UAT→Prod) + Azure VM with IIS apps + connected Azure services
sequence-flows.drawio (Tab 1)       Data Flow / Sequence Diagram → before TRV           Dealer Login + OTP (10 steps with DMS, Airtel, DB participants)
sequence-flows.drawio (Tab 2)       Data Flow / Sequence Diagram → Booking              Booking Claim Lifecycle: Event ingestion → Document upload → SAP settlement (3 phases)
sequence-trv-claim.drawio           Data Flow / Sequence Diagram → TRV                  TRV Claim: Norm approval → Vehicle details → Declaration → SAP (full end-to-end with 8 participants)

To insert into Confluence:
    1. Get attachment permissions on the D2W space
    2. Edit HLD page → place cursor at the relevant section
    3. Type /draw → select "draw.io Diagram" → Import → upload the .drawio file
    4. Each file renders inline as an interactive diagram

_______________________________________________________________________________________


_______________________________________________________________________________________


Database and Storage

Store                       Type            Purpose
CustomerBay DB              Azure SQL       Primary data (BookingClaim, PaymentDetail, VehicleDetail, TRVNorms, ExistingTRVDetail, Users, SAP records)
TravelNew DB                Azure SQL       AM/TM email lookups via stored procedure
IIS Local Disk (TVS-BSIV)  File System     Invoice, Insurance, Acknowledgement documents
IIS Local Disk (TVS-TRV)   File System     RC, Insurance, HSRP, Declaration documents
Redis                       None            Not implemented (recommended for caching)

_______________________________________________________________________________________


Events and Messaging

Topics Subscribed To:

Topic/Queue                 Events                                                  Action
uat.booking (Topic)         BOOKING_CREATED, BOOKING_CANCELLED, FULL_PAYMENT_UPDATED, INVOICED, DEALER_UPDATED   Upsert booking data
export_queue (Queue)        Export request (logId)                                  Generate Excel file

This service does not publish events to any topic.

_______________________________________________________________________________________


Error Handling Strategy

Pattern                 Implementation
Try-Catch per endpoint  Controllers wrap all logic in try-catch, return structured { Status, Message }
Transaction rollback    TRV vehicle save + file upload uses explicit DB transaction (rollback on file failure)
Fire-and-forget         Databricks OCR compliance check — failure does not block vehicle save
Retry (SAP)             Up to 3 retries tracked in Tb1002SapDetailsLog
Dead Letter Queue       Service Bus messages abandoned on failure → DLQ after max delivery
Idempotency             Messages checked by UUID + version before processing
Graceful degradation    DMS/Databricks failures return error but don't crash the application

_______________________________________________________________________________________
