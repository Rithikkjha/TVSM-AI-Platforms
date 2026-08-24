High Level Code Document — Dealer Claims Portal

_______________________________________________________________________________________


1. Application Overview

The Dealer Claims Portal is a full-stack web application developed for TVS Motor Company to manage the end-to-end dealer reimbursement lifecycle. The system handles online booking claim processing, document management (invoice/insurance), SAP financial document generation, and Test Ride Vehicle (TRV) norm management with multi-level approval workflows.

The application comprises two main codebases:

Frontend: A React 17 single-page application using MobX for state management, Ant Design for UI components, and AG Grid for data-intensive tables.

Backend: An ASP.NET Core 7 Web API (project name: CustomerBay) using Entity Framework Core 7, Azure Service Bus for event-driven processing, and integrations with SAP CPI, Azure Databricks, DMS, and Azure AD.

The portal serves four primary user roles: Super Admin, Dealers (AMD/AD/SPD), Area Accountants, and Area Managers, each with distinct capabilities and access restrictions.

_______________________________________________________________________________________


2. Major Modules/Components

Frontend Modules:

Module                                  Path                                        Purpose
Dealer Dashboard (Booking Claims)       src/components/dealerConsole/                Manages booking claim lifecycle across 5 tabs: Booking Update, Ready for Payment, Return Cases, Payment Status, One View
TRV Dashboard                           src/components/dealerDashboardTRV/           Test Ride Vehicle norm approval, vehicle details capture, document upload, claim submission
Authentication                          src/components/SignIn.js,                    Username/password login + OTP-based two-factor authentication
                                        TwoFactorAuthentication.js,
                                        OtpVerification.js
Modals                                  src/components/Modals/                      Document upload, view more details, invoice/insurance forms
Stores                                  src/components/stores/                      MobX state management (AppStore, LoginStore, DealerListStore, TRVStore)
Export                                  src/components/dealerConsole/exportFile/     Export document request and download

Backend Modules:

Module                          Path                                                Purpose
Dealer Dashboard Controller     Controllers/DealerDashboardController.cs             Login, booking data retrieval, document upload, OTP, export
TRV Controller                  Controllers/TRVController.cs                         TRV branches, summary, norms, vehicle save, declaration upload, compliance
SAP Controller                  Controllers/SAPController.cs                         SAP document generation, SAP response processing, Area Accountant claim approval
Bookings Controller             Controllers/BookingsController.cs                    Area Accountant booking views, approve/reject documents
SSO Auth Controller             Controllers/SsoAuthController.cs                     Azure AD OpenID Connect SSO flow
Booking Export                  Controllers/BookingExport.cs                         Async export via queue, CSV download
Topic Listener                  TopicListener/BookingServiceTopicListener.cs         Azure Service Bus topic consumer for booking events
Queue Listener                  QueueListeners/ExportQueue.cs                        Background export file generation
TRV Services                    Services/TRVServices.cs                              Business logic orchestration for TRV operations
LLM Service                     Services/LLMService.cs                               AI-based name matching (phonetic + fuzzy) for document compliance

_______________________________________________________________________________________


3. Folder Structure Explanation

Frontend (dealer-dashboard/):

src/
    App.js                          Root component, creates AppStore, renders layout
    App.css                         Global styles (AG Grid alternating rows, buttons)
    components/
        SignIn.js                    Login form (username/password)
        LoginUI.js                  Login page wrapper with background
        TwoFactorAuthentication.js  Phone number entry for OTP
        OtpVerification.js          4-digit OTP verification
        ToolBar.js                  Navigation header with menus and user dropdown
        SelectedComponent.js        Router-equivalent component switcher
        dealerConsole/              Booking claim management
            DealerDashboardUI.js    Main dashboard with tabbed interface
            CriteriaForm.js         Search filters (customer, dealer, date range)
            BookingUpdate.js        AG Grid: bookings needing doc upload
            ReadyForPaymentList.js  AG Grid: ready for SAP processing
            PaymentStatus.js        AG Grid: SAP document received
            ReturnCases.js          AG Grid: rejected documents for re-upload
            OneView.js              AG Grid: comprehensive all-bookings view
            DealerListStore.js      MobX store for booking data and pagination
            exportFile/             Export document management
        dealerDashboardTRV/         Test Ride Vehicle module
            TRVDashboardUI.js       Main TRV dashboard orchestrator
            NormApprovalModal.js    Brand/variant selection for norm approval
            VehicleDetailsModal.js  Frame number entry + document upload
            TRVNormsTable.js        Norms status table (approval/claim/capitalization)
            ClaimSubmissionForm.js  Declaration PDF upload for claim
            UploadDeclarationModal.js   Declaration upload modal
            TRVDocumentModal.js     Individual document upload modal
        Modals/                     Shared modal components
            DocumentModal.js        Invoice/insurance document modal
            UploadForm.js           Invoice/insurance data entry + file upload
            ViewMoreModal.js        Detailed booking record view
            ModalStore.js           MobX observable for modal state
        stores/                     Global state management
            AppStore.js             Central store: auth, session, navigation
            LoginStore.js           Authentication API calls
            APIProxy.js             HTTP client (fetch-based) with token auth
            APIEndpoints.js         Backend URL configuration
            TRVStore.js             TRV module state (approximately 1800 lines)
            Util.js                 Utility functions (CSV export, validation)
            menus/                  Menu configuration JSON
        util/                       Shared utilities
            Style.js                Shared style constants
            Util.js                 Date formatting, input type detection
            NotificationConfig.js   Global notification configuration
    images/                         Static assets (brand logo, backgrounds)
    public/                         Static HTML, favicon, manifest

Backend (BS2.0Backend_Integration/):

    Program.cs                      Application startup, DI, middleware pipeline
    Registry.cs                     Service/repository DI registration
    Encrypt.cs                      Password encryption utility
    Controllers/                    API endpoints
        DealerDashboardController.cs    Dealer portal APIs (login, bookings, uploads)
        TRVController.cs                TRV APIs (norms, vehicles, declarations)
        SAPController.cs                SAP integration APIs
        BookingsController.cs           Area Accountant APIs
        SsoAuthController.cs            Azure AD SSO endpoints
        BookingExport.cs                Export queue and download APIs
    Services/                       Business logic layer
        TRVServices.cs              TRV orchestration
        BookingsServices.cs         Booking data retrieval delegation
        LLMService.cs               Name matching (phonetic + fuzzy)
        SaveFileService.cs          File upload to IIS paths
        Manager.cs                  Event routing (Strategy pattern)
        EmailServices.cs            SendGrid email
        Event Handlers (6 files)    Booking lifecycle event processors
    Repository/                     Data access layer (30+ files)
        TRVRepository.cs            TRV database operations
        BookingsRepository.cs       Booking queries with filtering
        LoginRepository.cs          Credential validation
        TrvDealerClaimPortalRepository.cs   TRV norms save with deduplication
    Entities/                       EF Core entity classes (28 files)
    Model/                          Request/Response DTOs (55+ files)
    CustomerBayAppContext/          EF Core DbContext definitions
    Helpers/                        Utility classes (Email, Validation, Fuzzy)
    Const/                          Constants and Enums
    AutoMapper/                     Object mapping profiles
    TopicListener/                  Azure Service Bus topic consumer
    QueueDispatcher/                Azure Service Bus queue sender
    QueueListeners/                 Background queue processors
    Properties/                     Launch settings

_______________________________________________________________________________________


4. Core Business Workflows

4.1 Booking Claim Workflow (Dealer Dashboard)

Step 1 - Event Ingestion: Booking events (BOOKING_CREATED, FULL_PAYMENT_UPDATED, INVOICED, BOOKING_CANCELLED) arrive via Azure Service Bus Topic.

Step 2 - Data Population: Events are processed by Manager service which routes them to specific handlers. The handlers update the BookingClaim table accordingly.

Step 3 - Dealer Document Upload: Dealer searches bookings using criteria form, then uploads invoice PDF and insurance PDF. Metadata is saved to the database and files are stored on the IIS file system.

Step 4 - Claim Categorization: The system categorizes bookings into 5 tabs based on document status:
    Booking Update: Missing invoice or insurance, no rejection reason, DocumentStatus is not 3
    Ready for Payment: Both documents uploaded, no SAP document yet, no rejection
    Payment Status: SAP document received (DocumentStatus = 3)
    Return Cases: Documents rejected (has DocumentRejectReason)
    One View: All bookings regardless of status

Step 5 - SAP Processing: Approved claims are pushed to SAP CPI for document number generation. Once SAP responds with a document number, the status is updated to settled.

4.2 TRV Claim Workflow

Step 1 - Branch Selection: Dealer selects a branch. The system calls DMS API to provide branch list.

Step 2 - Summary Load: Backend calculates dealer classification, TRV required count, and capitalized vehicle count from the DealerTRNorms table.

Step 3 - Norm Approval: Dealer selects brands and variants from the available models list. On submission, records are inserted into TRV_Norms table and an approval email is sent to the Area Manager with approve/reject links.

Step 4 - AM Action: Area Manager clicks the email link. Azure AD authenticates the AM. The approve or reject action is stored in the database, updating Is_Norm_Approved to 1 (approved) or 2 (rejected).

Step 5 - Vehicle Details: Dealer enters frame number (17 characters). The system calls DMS API to validate and auto-fill vehicle data (customer name, invoice details, engine number).

Step 6 - Document Upload: RC, Insurance, and HSRP files are uploaded. These are mandatory for norm-based saves (SaveRequest = 0) and optional for existing TRV saves (SaveRequest = 1).

Step 7 - Compliance Check: A background task encodes the uploaded documents to base64 and sends them to Azure Databricks OCR endpoint. The AI validates that the customer name and chassis number on the RC document match the submitted data.

Step 8 - Declaration Submission: Dealer uploads a declaration PDF. The claim status moves from DocUploaded (4) to ClaimSubmitted (1).

Step 9 - Area Accountant Review: The Area Accountant reviews the claim in the ACM Portal. They can approve (which triggers a SAP API call) or reject (with a remark).

Step 10 - SAP Settlement: SAP returns a success response. Capitalization Status is updated to Capitalized (2) and Claim Status is updated to ClaimApprovedAO (2).

_______________________________________________________________________________________


5. Key Services/Classes

Frontend Key Classes:

AppStore (stores/AppStore.js)
    Central authentication, session management, menu resolution, navigation. Persists credentials to localStorage. Decodes JWT for session timeout.

DealerListStore (dealerConsole/DealerListStore.js)
    Booking data fetching, server-side pagination, CSV export, file upload management. Maintains SuperAdminData object with categorized booking arrays.

TRVStore (stores/TRVStore.js)
    TRV state management: branches, norms, vehicles, modals, submissions. Approximately 60 observables and 40 actions. Includes frame number caching to avoid repeated API calls.

APIProxy (stores/APIProxy.js)
    HTTP client using native fetch API. Methods: get, getBlob, post, asyncPost, postFile. Attaches JWT as Token header. Handles FormData uploads without Content-Type header.

LoginStore (stores/LoginStore.js)
    Login, SendOtp, VerifyOtp API calls. Tracks loading/error/done states via MobX observables.

ModalStore (Modals/ModalStore.js)
    Observable state for modal visibility, data, field type, and document links.

Backend Key Services:

TRVServices (Services/TRVServices.cs)
    Orchestrates all TRV operations: norms, vehicles, declarations, emails. Loads variants from DMS API. Triggers AM approval email via SMTP. Manages transactional vehicle save with file upload.

LLMService (Services/LLMService.cs)
    Document compliance name matching using Double Metaphone for phonetic similarity and FuzzySharp for character-level fuzzy matching. Applies surname gate check for multi-part names. Returns match result with confidence level.

SaveFileService (Services/SaveFileService.cs)
    File upload management to structured IIS paths. Handles four document types: Invoice, Insurance, TRV vehicle documents (RC/Insurance/HSRP), and Declaration. Validates file extensions and generates unique filenames.

Manager (Services/Manager.cs)
    Event dispatcher using Strategy pattern. Routes Service Bus events (BOOKING_CREATED, FULL_PAYMENT_UPDATED, DEALER_UPDATED, BOOKING_CANCELLED, INVOICED, INVOICE_CANCEL) to specific handler classes.

BookingsServices (Services/BookingsServices.cs)
    Delegates booking queries to DealerBookingsRepository for paginated data retrieval across different tab categories.

BookingServiceTopicListener (TopicListener/BookingServiceTopicListener.cs)
    Azure Service Bus session processor. Deserializes messages, extracts event type and payload, logs to BookingTopicLog, routes to Manager for processing.

_______________________________________________________________________________________


6. External Integrations

Integration                     Protocol            Direction       Purpose
DMS (Dealer Management System)  REST                Outbound        Branch lookup, frame number validation, variant loading
SAP CPI (Cloud Platform)        OAuth2 + REST       Outbound        Financial document posting for claim settlement
Azure Service Bus               AMQP WebSockets     Inbound         Event-driven booking lifecycle updates
Azure AD (Entra ID)             OpenID Connect      Bidirectional   SSO for Area Managers and Area Accountants
Azure Databricks                REST (Bearer token) Outbound        OCR-based document compliance validation
Airtel SMS Gateway              REST                Outbound        OTP delivery for dealer two-factor authentication
SendGrid / SMTP                 REST / SMTP         Outbound        Email notifications (norm approvals, claim actions)
DMS Web Service                 SOAP                Outbound        Employee active status verification before OTP

_______________________________________________________________________________________


7. Major Dependencies

Frontend (package.json):

Package             Version     Purpose
react               17.0.2      UI framework (class components)
mobx                6.4.1       Observable state management
mobx-react          7.3.0       React bindings for MobX
antd                4.18.8      UI component library
ag-grid-react       27.0.1      High-performance data tables
moment              latest      Date manipulation
dayjs               latest      Lightweight date library
jwt-decode          4.0.0       JWT token decoding for session expiry
papaparse           5.4.1       CSV parsing for export
file-saver          2.0.5       Client-side file download
react-app-rewired   2.2.1       Build customization without ejecting
customize-cra       1.0.0       Webpack override utilities

Backend (CustomerBay.csproj):

Package                                             Version     Purpose
Microsoft.EntityFrameworkCore.SqlServer             7.0.2       SQL Server ORM
Microsoft.Azure.ServiceBus                          5.2.0       Service Bus topic/queue operations
Microsoft.AspNetCore.Authentication.JwtBearer       7.0.0       JWT authentication
Microsoft.AspNetCore.Authentication.OpenIdConnect   7.0.20      Azure AD SSO
FuzzySharp                                          2.0.2       Fuzzy string matching for compliance
EPPlus                                              6.1.2       Excel file generation
Newtonsoft.Json                                     13.0.2      JSON serialization
Serilog.AspNetCore                                  7.0.0       Structured logging
SendGrid                                            9.29.3      Email delivery
AutoMapper.Extensions.Microsoft.DependencyInjection 11.0.0      Object-to-object mapping
ClosedXML                                           0.104.2     Excel file manipulation
Azure.Messaging.ServiceBus                          7.6.0       Modern Service Bus client

_______________________________________________________________________________________


8. Runtime Architecture

Frontend Runtime:

Build Tool: react-app-rewired with customize-cra. Legacy decorators enabled, ESLint disabled via config-overrides.js.

Deployment: Static build output deployed to IIS wwwroot (or AWS S3 as configured in package.json deploy script).

State Management: MobX observables with localStorage persistence for credentials and current component.

Session Management: JWT decoded client-side using jwt-decode library. Auto-logout triggered via setInterval when token expiry time is reached.

API Communication: Native fetch API used throughout. No axios in active use despite being listed in dependencies. All requests include Token header with JWT value.

Navigation: Custom component-based routing via SelectedComponent.js. No react-router. Navigation driven by appStore.currentComponent.key changes.

Backend Runtime:

Framework: ASP.NET Core 7 running on Kestrel behind IIS reverse proxy.

Threading: Single-threaded request processing with async/await pattern throughout.

Background Processing:
    BookingServiceTopicListener (Singleton): Consumes Service Bus topic messages with session processing. MaxConcurrentSessions = 1.
    ExportQueue (HostedService): Processes export queue messages to generate Excel files.

Database Contexts:
    CustomerBayDBContext: Primary database containing bookings, claims, TRV data, and user accounts.
    TravelNewDbContext: Secondary database used for AM/TM email lookups via stored procedure.

File System: Direct IIS file system writes to structured paths under C:\inetpub\wwwroot\TVS-BSIV\ and C:\inetpub\wwwroot\TVS-TRV\.

Concurrency: Service Bus session processor configured with MaxConcurrentSessions = 1 and SessionIdleTimeout of 5 seconds.

_______________________________________________________________________________________


9. Important Entry Points

Frontend Entry Points:

Entry Point             File                                    Description
Application Root        src/App.js                              Creates AppStore, renders ToolBar and SelectedComponent
Component Router        src/components/SelectedComponent.js     Switches components based on appStore.currentComponent.key
API Base URL            src/components/stores/APIEndpoints.js   Backend host configuration (toggle by commenting/uncommenting)

Backend Entry Points:

Entry Point             Route                                   Description
Dealer Login            POST /api/login                         Username/password authentication
Send OTP                POST /api/SendOtp                       OTP generation and SMS delivery
Verify OTP              POST /api/VerifyOtp                     OTP validation and JWT issuance
Booking Data            POST /api/bookings                      Paginated booking retrieval
TRV Branches            POST /api/TRV/branches                  Dealer branch listing from DMS
TRV Summary             POST /api/TRV/summary                   Dealer TR classification and counts
Norm Approval           POST /api/TRV/SubmitNormsApproval       Submit norm approval request
Vehicle Save            POST /api/TRV/SaveExistingTrvVehicles   Save vehicle with document upload
SAP Posting             POST /api/sap/claim-request             Area Accountant SAP claim request
SSO Login               GET /auth/sso/login                     Azure AD OpenID Connect initiation

_______________________________________________________________________________________


10. High-Level Data Flow

The data flows through the system as follows:

Dealer (Browser) communicates with Frontend (React/MobX) which communicates with Backend (.NET 7 API).

The Backend connects to:
    Azure SQL Database for all application data persistence
    Azure Service Bus for receiving booking lifecycle events
    DMS (REST) for dealer branch data and vehicle frame number details

Azure Service Bus delivers booking events which include:
    BOOKING_CREATED
    BOOKING_CANCELLED
    FULL_PAYMENT_UPDATED
    INVOICED
    INVOICE_CANCEL
    DEALER_UPDATED

SAP CPI connects to the Backend (SAP Controller) via OAuth2 + REST for financial document posting.

Azure AD connects to the Backend (SSO Controller) via OpenID Connect for Area Manager and Area Accountant authentication.

Azure Databricks connects to the Backend (TRV Controller) via REST with Bearer token for OCR-based document compliance validation.

Airtel SMS Gateway connects to the Backend (Dealer Dashboard Controller) via REST for OTP delivery.

Integration Summary:

Source System           Target System           Integration Type        Data Exchanged
Frontend                Backend                 REST (JWT)              Bookings, uploads, TRV operations
Azure Service Bus       Backend                 AMQP Topic              Booking lifecycle events
Backend                 DMS                     REST                    Branch data, frame details, variants
Backend                 SAP CPI                 OAuth2 REST             Claim documents, settlement amounts
Backend                 Azure AD                OIDC                    SSO authentication for AM/AA
Backend                 Databricks              REST                    Document images for OCR compliance
Backend                 Airtel                  REST                    OTP SMS messages
Backend                 SendGrid/SMTP           SMTP                    Notification emails
Backend                 Azure SQL               EF Core                 All application data
Frontend                IIS/S3                  Static                  Built SPA assets

_______________________________________________________________________________________
