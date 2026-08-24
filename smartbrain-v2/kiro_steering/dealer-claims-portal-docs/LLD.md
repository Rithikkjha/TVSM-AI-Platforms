Low Level Design — Dealer Claims Portal

Purpose: Implementation-level documentation for new engineering vendors to understand, maintain, and extend the system.
Version: 1.0 | Author: Samyucktha S | Status: CURRENT

_______________________________________________________________________________________


Overview

The Dealer Claims Portal is a full-stack system comprising a React 17 frontend and ASP.NET Core 7 backend that manages dealer reimbursement claims and Test Ride Vehicle (TRV) norm processing for TVS Motor Company. This LLD documents the implementation details including module breakdown, class responsibilities, API flows, data schemas, validation logic, error handling, business rules, and configuration.

_______________________________________________________________________________________


High Level Design — Quick Recap

Reference doc: HLD — Dealer Claims Portal (Confluence page ID: 5281251344)

Architecture: Controller → Services → Repository → EF Core → Azure SQL Server
Technology: ASP.NET Core 7, React 17, MobX 6, Entity Framework Core 7.0.2
Authentication: JWT Bearer (HMAC SHA256) + Azure AD OpenID Connect + OTP (Airtel SMS)
Database: 2 Azure SQL instances (CustomerBay + TravelNew) via EF Core
Messaging: Azure Service Bus (Topic for booking events, Queue for export)
External Services: DMS REST/SOAP, SAP CPI (OAuth2), Databricks OCR, Airtel SMS, SendGrid

_______________________________________________________________________________________


Assumptions

    Entity Framework Core 7.0.2 for all data access (no raw ADO.NET except SAP module)
    IIS-hosted ASP.NET Core 7 Web API with Kestrel behind reverse proxy
    All business logic in Services layer; Controllers are thin (validation + delegation only)
    JWT tokens validated per-request from custom Token header (not standard Authorization header)
    File uploads stored on local IIS disk (not Azure Blob Storage)
    Azure Service Bus session processor with MaxConcurrentSessions=1 (sequential processing)
    No caching layer (Redis/MemoryCache) currently implemented
    Frontend uses MobX observable stores with localStorage persistence for session
    No unit/integration test projects exist in either repository

_______________________________________________________________________________________


Components

Dealer Dashboard Module:

Layer           Class                           File                                            Responsibility
Controller      DealerDashboardController       Controllers/DealerDashboardController.cs        Login, OTP, bookings, document upload, export
Service         BookingsServices                Services/BookingsServices.cs                    Delegates to repository for tab-based queries
Repository      DealerBookingsRepository        Repository/DealerBookingsRepository.cs          EF Core queries with pagination
Repository      FilterRepository                Repository/FilterRepository.cs                  Optimized booking queries with dealer type filtering
Repository      LoginRepository                 Repository/LoginRepository.cs                   Credential validation, OTP save/verify
Service         SaveFileService                 Services/SaveFileService.cs                    File I/O to IIS paths

TRV (Test Ride Vehicle) Module:

Layer           Class                           File                                            Responsibility
Controller      TRVController                   Controllers/TRVController.cs                   Branches, summary, norms, vehicles, declarations, compliance, downloads
Service         TRVServices                     Services/TRVServices.cs                        Orchestrates all TRV operations
Service         LLMService                      Services/LLMService.cs                         AI name matching (Double Metaphone + FuzzySharp)
Repository      TRVRepository                   Repository/TRVRepository.cs                    TRVNorms CRUD, vehicle save (transactional), declarations
Repository      TrvDealerClaimPortalRepository  Repository/TrvDealerClaimPortalRepository.cs   Norm deduplication, TrvNormId generation

SAP Integration Module:

Layer           Class                           File                                            Responsibility
Controller      SAPController                   Controllers/SAPController.cs                   SAP document generation, response processing, claim approval
Service         TRVServices                     Services/TRVServices.cs                        SapRequestUpdate (claim status after SAP response)

Event Processing Module:

Layer           Class                           File                                            Responsibility
Listener        BookingServiceTopicListener     TopicListener/BookingServiceTopicListener.cs    Service Bus session processor, deduplication
Router          Manager                         Services/Manager.cs                            Routes events by EventType (Strategy pattern)
Handler         BookingCreatedHandler           Services/BookingCreatedHandler.cs               Upserts BookingClaim + PaymentDetail + VehicleDetail
Handler         FullPaymentUpdatedHandler       Services/FullPaymentUpdatedHandler.cs           Updates full payment info
Handler         InvoicedHandler                 Services/InvoicedHandler.cs                    Updates invoice status
Handler         BookingCancelledHandler         Services/BookingCancelledHandler.cs             Marks booking as cancelled

_______________________________________________________________________________________


API Design

Dealer Dashboard APIs (Route: /api/):

Method  Route                   Purpose                         Key Parameters
POST    /api/login              Authenticate dealer             username, password
POST    /api/SendOtp            Send OTP to phone               phoneNumber, dealerId, role, id
POST    /api/VerifyOtp          Verify OTP and issue JWT        otp, dealerId, role, id
POST    /api/bookings           Get all bookings (paginated)    BookingFilter
POST    /api/AllCount           Get tab counts                  BookingFilter
POST    /api/BookingUpdate      Bookings needing docs           BookingFilter
POST    /api/ReadyForPayment    Ready for SAP                   BookingFilter
POST    /api/PaymentStatus      SAP settled                     BookingFilter
POST    /api/ReturnCases        Rejected docs                   BookingFilter
POST    /api/InvoiceUpload      Upload invoice PDF              FormData: File, PartialPaymentId, Uuid
POST    /api/InsuranceUpload    Upload insurance PDF            FormData: File, PartialPaymentId, Uuid
POST    /api/InvoiceDetail      Update invoice metadata         InvoiceId, Value, Date, VIN
POST    /api/InsuranceDetail    Update insurance metadata       Insurer, PolicyNumber, ValidityFrom/To

TRV APIs (Route: /api/TRV/):

Method  Route                               Purpose                     Key Parameters
POST    /api/TRV/branches                   Get branches from DMS       dealerId
POST    /api/TRV/summary                    Get dealer classification   dealerId, branchId
POST    /api/TRV/norm-approval-form         Get models + variants       dealerId, branchId
POST    /api/TRV/SubmitNormsApproval        Submit for approval         List of TrvNormRequestModel
POST    /api/TRV/GetTRVNorms                Get norms status            dealerId, branchId
POST    /api/TRV/SaveExistingTrvVehicles    Save vehicle + docs         FormData (all fields + files)
POST    /api/TRV/GetExistingTrvVehicles     Get existing vehicles       dealerId, branchId
GET     /api/TRV/get-frame-details          Validate via DMS            dealerId, branchId, frameNo
GET     /api/TRV/download-file/{id}/{type}  Download document           existingTrvVehicleId, fileType
POST    /api/TRV/upload-declaration-file    Upload declaration          FormData: DEALER_ID, BRANCH_ID, IDs, PDF

Standard Response Format:
    { "status": 200, "data": { ... }, "message": "Success" }

Status Codes:
    200: Success
    400: Bad request (validation failure)
    401: Unauthorized (invalid JWT, dealer mismatch)
    404: Record not found
    409: Conflict (duplicate frame/engine)
    500: Internal server error

_______________________________________________________________________________________


Data Model / Schema Changes

Key Entities:

Entity              Table               PK                                  Key Fields
BookingClaim        BookingClaim        UUID (string)                       DealerCode, CustomerName, BookingDate, DocumentStatus, InvoiceFileName, InsuranceFileName
TRVNorms            TRV_Norms           Id (long)                           DealerId, BranchId, Brand_Name, Variant_Name, Is_Norm_Approved, Claim_Status
ExistingTRVDetail   ExistingTRVDetails  TRVDetailId (int)                   DealerId, BranchId, FrameNo, EngineNo, NORM_ID, IsCompliant, Documents
DealerTRNorms       DealerTRNorms       Id (Unique: DealerCode+SapBranchId) DealerClassification, TRVCount, SupportPercentage, ModelJson
PaymentDetail       PaymentDetails      Id (int)                            UUID(FK), PaymentId, PaymentAmount, PaymentType, ClaimAmount, IsOnline

Status Code Enums:

Enum                    Values
ClaimStatus             0=DocPending, 1=ClaimSubmitted, 2=ClaimApprovedAO, 3=ClaimRejectedAO, 4=DocUploaded, 5=ClaimRejectedAM
CapitalizationStatus    0=DocPending, 1=AreaAccountantApproved, 2=Capitalized(SAP), 3=Rejected
RequestType             0=Reject, 1=Approve
TRVDocumentType         1=RC, 2=Insurance, 3=HSRP, 4=Declaration
TrvRequestType          0=TrvNormSaveRequest (mandatory docs), 1=ExistingTrvSaveRequest (optional docs)

_______________________________________________________________________________________


Class and Interface Design

Backend Service Layer Pattern:

    Controller (thin):
        Validates JWT → checks authorization → calls service → wraps response

    Service (orchestration):
        Applies business rules → coordinates repositories + external APIs → manages transactions

    Repository (data access):
        EF Core LINQ queries → SaveChangesAsync → returns entities/DTOs

Frontend Store Pattern (MobX):

    Store class with @observable state, @action methods, @computed properties
    APIProxy.post/get for HTTP calls
    runInAction() for state mutations after async calls
    localStorage persistence for credentials

_______________________________________________________________________________________


Error Handling and Retries

Scenario                                    Handling
Invalid/expired JWT                         Return 401 "Invalid or expired token"
Dealer ID mismatch                          Return 401 "Access to dealer(X) not allowed"
SQL unique constraint (2601/2627)           Catch DbUpdateException → 409 "Duplicate FrameNo or EngineNo"
SAP API timeout (30s)                       Catch TaskCanceledException → 408 "Request timeout"
SAP HTTP error                              Catch HttpRequestException → 503 "Service unavailable"
SAP retry logic                             Up to 3 retries in Tb1002SapDetailsLog; after 3: DocumentStatus=5
Service Bus failure                         Log error, abandon message (Service Bus retries automatically)
Databricks OCR failure                      Fire-and-forget: error logged, vehicle save NOT rolled back
File upload failure in transaction          DB transaction rolled back completely
DMS API failure                             Return BadRequest with DMS error message

_______________________________________________________________________________________


Security and Compliance

Authentication:
    JWT Bearer (HMAC SHA256) with 120-minute expiry
    Token passed via custom "Token" header
    Azure AD OpenID Connect for SSO (AM/AA)
    OTP via Airtel SMS with 10-minute expiry (DLT compliant)

Authorization:
    Every API validates JWT, extracts Role and DealerId from claims
    Non-SuperAdmin can only access own dealer data
    Area Accountants verified by region overlap

Input Validation (DealerDashboardController):
    dealerId: numeric only (regex ^\d+$)
    mobileNumber: exactly 10 digits
    customerEmail: valid MailAddress
    customerName: letters, digits, spaces, .'- only
    dates: yyyyMMdd, start <= end
    pageSize: max 200, default 50
    Unknown fields rejected

_______________________________________________________________________________________


RBAC (Role-Based Access Control)

Role                    ID      Permissions                                             Auth Method
Super Admin             1       All dealer data, no OTP, search any dealer              JWT (direct)
Dealer (AMD/AD/SPD)    10      Own dealer only, requires OTP                           JWT + OTP
Area Accountant         3       Region-based, claim approve/reject, SAP trigger         Azure AD SSO
Area Manager            2/13    Norm approve/reject only (via email)                    Azure AD SSO

_______________________________________________________________________________________


Configuration Rules and Feature Flags

Key (appsettings.json)              Purpose                             Type
AppSettings:BRIDGE_AUTH_TOKEN       JWT signing secret key              String
AppSettings:SuperAdminRoleId        Role ID for super admin ("1")       String
AppSettings:DealerRoleId            Role ID for dealer ("10")           String
AppSettings:AreaAccountantRoleId    Role ID for AA ("3")                String
AppSettings:SendOtpBypassForTesting Bypass OTP in testing               Boolean
SMTP:Is_Production                  Toggle prod vs test email recipients String
SMTP:TestRideVehicleEmailId         CC email for TRV notifications      String
ServiceBusSettings:TopicName        Topic name per environment          String
SAP:COMPANY_CODE                    SAP company code ("TSL")            String
SAP:EXPENSE_GL_ACCOUNT              SAP GL account for TRV claims       String

Configuration Source: All in appsettings.json. No database-driven flags. Environment switching by commenting/uncommenting URLs.

_______________________________________________________________________________________


Dependencies

Backend NuGet Packages:

Package                                             Version     Purpose
Microsoft.EntityFrameworkCore.SqlServer             7.0.2       SQL Server ORM
Microsoft.Azure.ServiceBus                          5.2.0       Service Bus operations
Microsoft.AspNetCore.Authentication.JwtBearer       7.0.0       JWT auth
Microsoft.AspNetCore.Authentication.OpenIdConnect   7.0.20      Azure AD SSO
FuzzySharp                                          2.0.2       Fuzzy matching (compliance)
EPPlus                                              6.1.2       Excel generation
Serilog.AspNetCore                                  7.0.0       Logging
SendGrid                                            9.29.3      Email
Newtonsoft.Json                                     13.0.2      JSON
AutoMapper                                          11.0.0      Object mapping

External Service Dependencies:

Service             Class                               Protocol        Purpose
DMS                 HttpClient (inline)                 REST + SOAP     Branches, frame, variants, employee status
SAP CPI             HttpClient (inline)                 OAuth2 + REST   Claim settlement (30s timeout)
Azure Databricks    IHttpClientFactory ("DataScience")  REST            OCR compliance (60s timeout)
Airtel SMS          HttpClient (inline)                 REST            OTP delivery
SendGrid/SMTP       Email helper (static)               SMTP            Email notifications
Azure AD            OpenIdConnect middleware             OIDC            SSO authentication

_______________________________________________________________________________________


Trade-offs and Alternatives Considered

Decision            Choice                      Alternative                 Reason
Architecture        Layered Monolith            Microservices               Small team, simpler deployment; Service Bus for event decoupling
Data Access         EF Core 7                   Dapper / ADO.NET            EF Core for CRUD; raw SQL only for SAP batch
File Storage        IIS Local Disk              Azure Blob Storage          Simpler for current scale; accepted single-node risk
Frontend State      MobX (Class components)     Redux / React Query         Existing codebase; MobX simpler for observable patterns
Auth Token Header   Custom "Token" header       Standard Authorization      Legacy design; works but non-standard
Compliance Check    Fire-and-forget (bg)        Synchronous validation      Non-blocking UX; 60s timeout would block user
SAP Integration     Direct HTTP in controller   Queue-based async           Immediate response needed; retry via log table
Session Mgmt        JWT (stateless)             Server sessions             Scalable, no server-side state needed

_______________________________________________________________________________________


Open Questions

    Connection pooling disabled (Pooling=False). Should be enabled for production.
    Secrets in appsettings.json. Should migrate to Azure Key Vault.
    No unit/integration tests. Should add xUnit test project.
    Service Bus MaxConcurrentSessions=1 limits throughput. Evaluate increasing.
    Custom "Token" header is non-standard. Consider migrating to Authorization: Bearer.
    TRVController is 800+ lines. Consider splitting into smaller controllers.
    Frontend uses class components. Consider migration path to hooks + functional components.
    No database migration strategy documented. EF Core migrations not in use.

_______________________________________________________________________________________


_______________________________________________________________________________________


Database Schema (Key Tables and Relationships)

BookingClaim (PK: UUID)
    → PaymentDetail (FK: UUID) — 1:N (partial + full payments)
    → VehicleDetail (FK: UUID) — 1:N (vehicle info)

DealerTRNorms (PK: Id, Unique: DealerCode+SapBranchId)
    → TRVNorms / TRV_Norms (FK: DealerTR_NORM_Id)
        → ExistingTRVDetail (FK: NORM_ID)
            → TrvDeclarationFile (Index: DealerId+BranchId+TrvNormId)

Tb1008UserDetail (PK: Id) — User accounts for all roles
tb_1002_SAP_Details — SAP document records
Tb1002SapDetailsLog — SAP response audit trail
BookingTopicLog — Service Bus message processing audit

_______________________________________________________________________________________


Testing Strategy

No automated test projects currently exist in either repository.
Manual testing approach:
    Backend: Swagger UI at /swagger (Development environment only)
    Frontend: npm test (React testing library — limited coverage)
    Integration: Start backend → start frontend → login → verify flows manually
Recommendation: Add xUnit test project for backend, Jest tests for frontend stores.

_______________________________________________________________________________________
