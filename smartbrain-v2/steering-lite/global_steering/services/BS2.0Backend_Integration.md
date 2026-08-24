# BS2.0Backend_Integration


## Product Context


# Product: CustomerBay — TVS Motor Booking Reimbursement Service (BS2.0)

## What This Service Does

CustomerBay is the backend API for TVS Motor Company's online vehicle booking reimbursement and dealer settlement system. It manages the full lifecycle of online bookings from creation through payment settlement, document verification, and SAP financial posting.

The system handles two vehicle categories:
- **BSVI / ICE** — Internal combustion engine two-wheelers
- **EV / iQube** — Electric vehicles (TVS iQube)

## Core Business Processes

1. **Booking Ingestion** — Receives real-time booking events from an upstream booking service via Azure Service Bus Topics (session-based, ordered per UUID).
2. **Document Upload & Verification** — Dealers upload invoice and insurance documents; area accountants approve or reject them.
3. **SAP Financial Posting** — Generates journal entry data for dealer reimbursement and exchanges document numbers with SAP ERP.
4. **Payment Settlement Tracking** — Tracks CCAvenue payment gateway settlements, fees, taxes, and payout IDs.
5. **Dealer Dashboard** — Provides booking lists, status counts, filtering, and export capabilities for dealer users.
6. **Area Accountant Portal** — Booking review, document approval/rejection, transaction reports, and TDR details.

## Domain Entities

| Entity | Purpose |
|--------|---------|
| **BookingClaim** | Central entity (PK: UUID). Holds customer, dealer, invoice, insurance, and document status. |
| **PaymentDetail** | Payment transactions per booking (partial, full). Tracks settlement amounts, fees, gateway info. |
| **VehicleDetail** | Vehicle info per booking (model, variant, color, type ICE/EV). |
| **BookingStatus** | Legacy denormalized view combining booking + payment + document data (composite PK: Id + BookingDate). |
| **Tb1002SapDetail** | SAP journal entry records — accounts, amounts, reference numbers. |
| **Tb1002SapDetailsLog** | Audit log of SAP document posting attempts and responses. |
| **Tb1010SettlementDetail** | CCAvenue settlement records (UTR, bank, amounts). |
| **Tb1011CcavenueStatusApiDetail** | Full CCAvenue transaction status details. |
| **Tb1012SettlementBreakup** | Per-transaction settlement breakdown (fees, tax, payable amount). |
| **Tb1007PolicyDetail** | Insurance policy details (insurer, coverage, vehicle info). |
| **Tb1008UserDetail** | System users (dealers, area accountants) with credentials. |
| **AdAmdMapping** | Maps dealer codes (AD) to area manager dealer codes (AMD) for SAP account routing. |
| **BsviExportDocument** | Export job tracking (file name, status, timestamps). |
| **DocumentRejectLog** | Audit trail of document rejections with reasons. |
| **BookingTopicLog** | Audit log of all Service Bus messages received (request, response, event type). |

## External Integrations

| System | Direction | Purpose |
|--------|-----------|---------|
| **SAP ERP** | Bidirectional | Provides booking data for journal entry creation (GET); receives document numbers back (POST). Company code: TSL. |
| **Azure Service Bus (Topic)** | Inbound | Subscribes to `prod.booking` topic for real-time events. Session-based processing ensures ordering per UUID. |
| **Azure Service Bus (Queue)** | Internal | `export_queue` for async Excel report generation. |
| **CCAvenue** | Data sync | Payment settlement and transaction status tracking (data arrives via DB triggers/external sync). |
| **DMS (Dealer Management System)** | Referenced | Booking push status, internet enquiry IDs, booking numbers. |
| **SendGrid** | Outbound | Email notifications (package referenced, service registered). |
| **IIS File System** | Local | Document storage at `C:\inetpub\wwwroot\TVS-BSIV\TVS-BSIV\` (Invoice, Insurance, Acknowledgement, Export folders). |

## Business Rules

### SAP Document Posting
- Only processes bookings where: DocumentStatus = 1, settlement data exists, invoice AND insurance uploaded, booking not cancelled, payment is online.
- Reference number derived from TransactionId (for CPG/JUSPAY channels) or PaymentId.
- RefNumber must be 12–16 characters, alphanumeric with optional hyphens.
- Company code is always "TSL"; CCA is "ZEVC" for EV, "ZTS1" for ICE.
- Account routing: ACCOUNT_1 = AMD mapping (if dealer code 50000–70000) or dealer code; ACCOUNT_2 = "450160"; ACCOUNT_3 = "572106".
- Retry mechanism: max 3 attempts. After 3 failures, DocumentStatus set to 5.
- Duplicate SAP responses with a DOC_NO are treated as success ("Document Posted Successfully").

### Brand Discounts (SAP Amount Adjustment)
- Applied only for specific merchant IDs (394306, 2115695, 2908324) and payment > ₹5000.
- Apache RTR 160/200: ₹1800 discount
- NTorq 125 / Raider: ₹1000 discount
- Star City / Scooty Pep / Zest 110: ₹500 discount
- EV vehicles: no brand discount adjustment on amount.

### Document Status Flow
- 1 = Approved (pending SAP posting)
- 3 = SAP document posted successfully
- 5 = SAP retry mechanism exhausted

### Payment Types
- `partial` — Booking amount (token payment)
- `full Payment` — Full vehicle payment
- Both partial and full must have SAP documents posted for DocumentStatus = 3.

### Booking Events (Service Bus)
- `BOOKING_CREATED` — Creates BookingClaim, VehicleDetails, PaymentDetails
- `BOOKING_CANCELLED` — Sets cancellation date
- `FULL_PAYMENT_UPDATED` — Adds full payment record
- `DEALER_UPDATED` — Updates dealer assignment
- `INVOICED` — Updates invoice details
- `INVOICE_CANCEL` — Handles invoice cancellation

### Document Upload Rules
- Differentiated by `ComeFrom` field: "BSVI" vs iQube paths.
- Files stored as PDF with naming: `{PaymentId}_{ticks}.pdf`.
- Acknowledgment uploads differentiated by `isiQube` boolean flag.

### Authentication
- JWT tokens with 120-minute expiry, HMAC-SHA256 signing.
- Token passed in custom `Token` header (not standard `Authorization`).
- Two roles referenced: dealer users and area accountants.
- SAP endpoint uses a separate static auth key.



## Code Structure


# Structure: CustomerBay Project Layout

## Annotated Directory Layout

```
BS2.0Backend_Integration/
├── Program.cs                      # App entry point: DI, middleware, CORS, JWT config, Service Bus listener startup
├── Registry.cs                     # Centralized DI registration (all services, repositories, event handlers)
├── Encrypt.cs                      # AES-256 encryption utility (password hashing for login)
├── CustomerBay.csproj              # Project file (.NET 7, package references)
├── appsettings.json                # Config: DB connection, JWT secret, Service Bus endpoints (prod/uat/dev)
│
├── Controllers/                    # API layer — thin controllers, delegate to services/repositories
│   ├── DealerDashboardController.cs    # Dealer-facing: login, bookings, counts, uploads, exports (route: api/)
│   ├── BookingsController.cs           # Area accountant: booking lists, approve/reject, TDR, reports (route: api/areaAccountant/)
│   ├── BookingExport.cs                # Export job creation and retrieval (route: api/areaAccountant/)
│   └── SAPController.cs               # SAP integration: GET pending docs, POST doc responses (route: api/sap)
│
├── Services/                       # Business logic layer
│   ├── Manager.cs                      # Event dispatcher — routes event types to handlers (strategy pattern)
│   ├── IManager.cs                     # Manager interface
│   ├── IEventHandler.cs                # Common interface for all event handlers
│   ├── BookingCreatedHandler.cs        # Handles BOOKING_CREATED: creates BookingClaim, Vehicles, Payments
│   ├── BookingCancelledHandler.cs      # Handles BOOKING_CANCELLED
│   ├── FullPaymentUpdatedHandler.cs    # Handles FULL_PAYMENT_UPDATED
│   ├── DealerUpdatedHandler.cs         # Handles DEALER_UPDATED
│   ├── InvoicedHandler.cs              # Handles INVOICED
│   ├── InvoiceCancelledHandler.cs      # Handles INVOICE_CANCEL
│   ├── BookingStatusService.cs         # Area accountant booking queries (IBookingStatusService)
│   ├── IBookingStatusService.cs        # Interface
│   ├── BookingsServices.cs             # Dealer dashboard booking queries (IBookingsServices)
│   ├── IBookingsServices.cs            # Interface
│   ├── SaveFileService.cs              # File upload to IIS local disk (ISaveFileService)
│   ├── ISaveFileService.cs             # Interface
│   ├── ExcelService.cs                 # EPPlus Excel package creation (IExcelService)
│   ├── IExcelService.cs                # Interface
│   └── EmailServices.cs                # SendGrid email sending
│
├── Repository/                     # Data access layer — EF Core queries, raw SQL where needed
│   ├── LoginRepository.cs / ILoginRepository.cs           # User credential validation
│   ├── BookingsRepository.cs / IBookingsRepository.cs     # Dealer booking data queries
│   ├── DealerBookingRepository.cs / IDealerBookingRepository.cs  # Dealer-specific booking queries
│   ├── FilterRepository.cs / IFilterRepository.cs         # Shared filtering logic
│   ├── ApprovedRepository.cs / IApprovedRepository.cs     # Document approval updates
│   ├── RejectRequestRepository.cs / IRejectRequestRepository.cs  # Document rejection updates
│   ├── DocumentExportRepository.cs / IDocumentExportRepository.cs # Export job CRUD
│   ├── ExportRepository.cs / IExportRepository.cs         # Export data retrieval
│   ├── InvoiceUploadRepository.cs / IInvoiceUploadRepository.cs   # Invoice upload logging
│   ├── InvoiceDetailRepository.cs / IInvoiceDetailRepository.cs   # Invoice detail updates
│   ├── InsuranceUploadRepository.cs / IInsuranceUploadRepository.cs # Insurance upload logging
│   ├── InsuranceDetailRepository.cs / IInsuranceDetailRepository.cs # Insurance detail updates
│   ├── TdrDetailsRepository.cs / ITdrDetailsRepository.cs # TDR (Transaction Dispute Resolution) queries
│   └── LoginLogger.cs / ILoginLogger.cs                   # Login attempt audit logging
│
├── Entities/                       # EF Core entity classes (database-first, data annotations)
│   ├── BookingClaim.cs                 # Central booking entity (PK: UUID), has nav props to Payment/Vehicle
│   ├── PaymentDetail.cs                # Payment records (FK: UUID → BookingClaim)
│   ├── VehicleDetail.cs                # Vehicle records (FK: UUID → BookingClaim)
│   ├── BookingStatus.cs                # Legacy denormalized booking view (composite PK)
│   ├── Tb1002SapDetail.cs              # SAP journal entries (keyless)
│   ├── Tb1002SapDetailsLog.cs          # SAP posting audit log
│   ├── Tb1007PolicyDetail.cs           # Insurance policy details
│   ├── Tb1008UserDetail.cs             # System users (login credentials)
│   ├── Tb1010SettlementDetail.cs       # CCAvenue settlement records
│   ├── Tb1011CcavenueStatusApiDetail.cs # CCAvenue transaction details
│   ├── Tb1012SettlementBreakup.cs      # Settlement breakdowns
│   ├── Tb1000BookingDetail.cs          # Legacy iQube booking details
│   ├── Tb102BookingDetail.cs           # Legacy BSVI booking details
│   ├── Tb105UserStatus.cs              # Legacy user status (iQube)
│   ├── Tb1002UserStatus.cs             # Legacy user status (BSVI)
│   ├── AdAmdMapping.cs                 # Dealer-to-AMD code mapping
│   ├── BookingTopicLog.cs              # Service Bus message audit log
│   ├── BsviExportDocument.cs           # Export job records
│   ├── BsviInsuranceUploadLog.cs       # Insurance upload audit
│   ├── BsviInvoiceUploadLog.cs         # Invoice upload audit
│   ├── DocumentRejectLog.cs            # Rejection audit trail
│   ├── InvoiceUploadLog.cs             # Invoice upload audit (iQube)
│   ├── SapapprovedLog.cs               # SAP approval audit
│   └── UserLoginLog.cs                 # Login attempt records
│
├── Model/                          # DTOs, request/response models, filters
│   ├── BookingDetails.cs               # Main booking DTO for API responses
│   ├── BookingFilter.cs                # Query filter (dates, dealer, mobile, pagination)
│   ├── BookingResult.cs                # Paginated result wrapper
│   ├── SAPModel.cs                     # SAP request/response DTOs (SAP, SAPDetails, SAPRequestDetails)
│   ├── LoginModel.cs                   # Login request DTO
│   ├── ApprovedModel.cs                # Document approval request
│   ├── RejectRequestModel.cs           # Document rejection request
│   ├── ExportRequestModel.cs           # Export job creation request
│   ├── ExportReturnModel.cs            # Export data with filename
│   ├── InvoiceUploadRequestModel.cs    # Invoice file upload request
│   ├── InsuranceDetailRequestModel.cs  # Insurance detail update request
│   ├── AcknowledgmentModel.cs          # Acknowledgment upload request
│   ├── InvalidTokenException.cs        # Custom exception for auth failures
│   ├── AllCountModel.cs                # Dashboard count aggregates
│   ├── TransactionModel.cs             # Transaction report counts
│   ├── TDRDetails.cs                   # Transaction dispute resolution model
│   └── ... (additional log/DTO models)
│
├── CustomerBayAppContext/          # EF Core DbContext
│   └── CustomerBayDBContext.cs         # All DbSets, OnModelCreating with keys/triggers/relationships
│
├── AutoMapper/                     # Object mapping profiles
│   └── AutoMapping.cs                  # Maps: approval→log, reject→log, export→log, policy, invoice, insurance
│
├── Const/                          # Application constants
│   └── Constants.cs                    # Service Bus connection string, queue names
│
├── TopicListener/                  # Azure Service Bus Topic subscription
│   ├── BookingServiceTopicListener.cs  # Session processor: receives messages, logs, dispatches to Manager
│   └── ITopicListener.cs              # Interface
│
├── QueueDispatcher/                # Azure Service Bus Queue sender
│   ├── Dispatcher.cs                   # Sends messages to named queues
│   └── IDispatcher.cs                  # Interface
│
├── QueueListeners/                 # Background queue consumers
│   └── ExportQueue.cs                  # BackgroundService: processes export jobs, generates Excel, uploads file
│
└── Properties/
    ├── launchSettings.json             # Dev server URLs and profiles
    └── PublishProfiles/                # Deployment publish profiles
```

## Module Dependencies

```
Controllers ──→ Services ──→ Repository ──→ CustomerBayDBContext ──→ Entities
     │              │              │
     │              │              └──→ AutoMapper (for log creation)
     │              │
     │              └──→ QueueDispatcher (export jobs)
     │
     └──→ Repository (some controllers call repos directly)

TopicListener ──→ Manager ──→ EventHandlers ──→ CustomerBayDBContext
                                    │
                                    └──→ Entities (direct creation)

QueueListeners ──→ Services (SaveFileService, ExcelService)
               ──→ Repository (DocumentExportRepository)
```

## Architectural Decisions

1. **Database-first EF Core** — Entities generated from existing SQL Server schema with data annotations. Some tables are keyless (Tb1002SapDetail) requiring raw SQL for inserts.

2. **Mixed data access** — Most queries use EF Core LINQ. SAP controller uses raw ADO.NET (`SqlConnection`/`SqlCommand`) for inserts and updates to keyless tables and for performance-critical batch operations.

3. **Event-driven ingestion** — Booking data arrives via Azure Service Bus Topics with session-based processing (ensures per-UUID ordering). The Manager class dispatches to typed handlers using a switch expression (strategy pattern).

4. **Async export via queue** — Export requests are queued to Azure Service Bus; a BackgroundService (`ExportQueue`) processes them, generates Excel files, and saves to disk.

5. **No strict layering enforcement** — Controllers sometimes call repositories directly (bypassing services). Some business logic lives in controllers (SAPController has significant logic).

6. **Dual-system support** — Most operations branch on "BSVI" vs "iQube" (via `ComeFrom` field or `isiQube` flag), with separate repository methods for each path.

7. **Legacy + new entities coexist** — `BookingStatus` is the legacy denormalized table; `BookingClaim` + `PaymentDetail` + `VehicleDetail` is the normalized new schema. Both are maintained.

8. **File storage on IIS** — Documents stored directly on the Windows server filesystem under IIS wwwroot. No cloud blob storage.

9. **Centralized DI in Registry.cs** — All service and repository registrations in a single extension method, keeping Program.cs clean.

10. **No unit tests** — No test project exists in the solution.



## Tech Stack & Dependencies


# Tech: CustomerBay Development Guide

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | .NET | 7.0 |
| Web Framework | ASP.NET Core Web API | 7.0 |
| ORM | Entity Framework Core (SQL Server) | 7.0.2 |
| Database | Azure SQL Server | — |
| Messaging | Azure Service Bus (Topics + Queues) | 7.6.0 (new) / 5.2.0 (legacy) |
| Auth | JWT Bearer (System.IdentityModel.Tokens.Jwt) | 6.36.0 |
| Object Mapping | AutoMapper | 11.0.0 |
| Excel Generation | EPPlus 6.1.2, ClosedXML 0.104.2 |
| Email | SendGrid | 9.29.3 |
| JSON | Newtonsoft.Json 13.0.2, System.Text.Json (built-in) |
| API Docs | Swashbuckle (Swagger) | 6.4.0 |
| Hosting | IIS on Windows Server | — |

## Build & Run

```bash
# Restore and build
dotnet restore
dotnet build

# Run locally (uses launchSettings.json profiles)
dotnet run

# Publish for deployment
dotnet publish -c Release
```

The app starts a Service Bus topic listener on startup (`BookingServiceTopicListener.Register()` in Program.cs) and a background queue listener (`ExportQueue` as `IHostedService`).

## Coding Conventions

### Naming
- **Namespaces**: `CustomerBay`, `CustomerBay.Controllers`, `CustomerBay.Services`, `CustomerBay.Repositories`, `CustomerBay.Entities`, `CustomerBay.Model`, `CustomerBay.Models` (note: both `Model` and `Models` namespaces exist).
- **Entities**: Match database table names. Prefixed tables use `Tb` prefix (e.g., `Tb1002SapDetail` for `tb_1002_SAP_Details`).
- **Interfaces**: `I` prefix (e.g., `IBookingStatusService`, `ILoginRepository`).
- **DTOs/Models**: Suffix with `Model`, `Filter`, `Details`, or `Request` (e.g., `BookingFilter`, `ExportRequestModel`, `SAPRequestDetails`).
- **Repository methods**: Verb-first (e.g., `ValidateLoginCredentials`, `InsertDownloadDetails`, `UpdateBSVI`).
- **Controller methods**: Action-named, matching route (e.g., `GetBooking`, `ApprovedDocuments`, `RejectDocuments`).

### File Organization
- One class per file (entities, models, repositories).
- Interface and implementation in the same folder (Repository/).
- Services folder contains both interfaces and implementations.
- No sub-folders within Services/ for event handlers — they sit alongside other services.

### Property Naming
- Entity properties use PascalCase with EF Core `[Column]` attributes mapping to database column names.
- Model/DTO properties use a mix of PascalCase and camelCase (inconsistent — follow existing pattern in each file).
- Filter models use camelCase properties (e.g., `startDate`, `endDate`, `dealerId`).

## Patterns

### Repository Pattern
Every data access operation goes through an interface + implementation pair:
```csharp
// Interface
public interface ILoginRepository
{
    public Task<dynamic> ValidateLoginCredentials(LoginModel request);
}

// Implementation — injected via DI
public class LoginRepository : ILoginRepository
{
    private readonly CustomerBayDBContext dbContext;
    public LoginRepository(CustomerBayDBContext dbContext) { ... }
}
```

### Event Handler Pattern (Strategy)
Service Bus events are dispatched by `Manager` to typed handlers:
```csharp
public interface IEventHandler
{
    Task HandleAsync(JsonElement payload, int LogId);
}

// Manager dispatches:
IEventHandler handler = eventType switch
{
    "BOOKING_CREATED" => _bookCreatedHandler,
    "BOOKING_CANCELLED" => _bookCancelledHandler,
    // ...
};
await handler.HandleAsync(payload, LogId);
```

### DI Registration
All registrations in `Registry.cs` using the extension method pattern:
```csharp
public static class Registry
{
    public static void Register(this IServiceCollection services)
    {
        services.AddScoped<IBookingStatusService, BookingStatusService>();
        services.AddHostedService<ExportQueue>();
        services.AddSingleton<BookingServiceTopicListener>();
        // ...
    }
}
```
- Repositories and services: `AddScoped`
- Background services: `AddHostedService`
- Topic listener: `AddSingleton`

### Controller Response Pattern
All endpoints return anonymous objects with a `Status` field:
```csharp
result = new { Status = 200, data = bookingData, message = "Successfull" };
return Ok(result);

// Error:
result = new { Status = 400, message = ex.Message };
return BadRequest(result);
```

### Authentication Pattern
Token extracted from custom header, validated manually:
```csharp
string? token = Request.Headers["Token"];
if (string.IsNullOrEmpty(token))
    return BadRequest(new { Status = 400, Message = "Token is missing." });

var claimsPrincipal = ValidateToken(token, this.AuthToken);
if (claimsPrincipal == null)
    return Unauthorized(new { Status = 401, Message = "Invalid or expired token." });
```

Some older endpoints use simple token comparison:
```csharp
private void Authenticate(string? token)
{
    if (string.IsNullOrEmpty(token)) throw new InvalidTokenException();
    if (!token.Equals(this.AuthToken)) throw new InvalidTokenException();
}
```

### Dual-Path Operations (BSVI vs iQube)
Most upload/update operations branch based on source system:
```csharp
if (request.ComeFrom == "BSVI")
    await repository.BSVIInvoiceUpload(request, fileName);
else
    await repository.IqubeInvoiceUpload(request, fileName);
```

## Error Handling

### Controller Level
- All controller actions wrapped in try/catch.
- `InvalidTokenException` caught separately → 400 with token message.
- Generic `Exception` caught → 400 with `ex.Message` (no 500s returned).
- No global exception middleware or filters.

### Service Bus Listener
- Errors logged via `ILogger`.
- Failed messages: log entry updated with error, message abandoned (will retry via Service Bus).
- Special case: "From DMS" errors complete the message (no retry).

### SAP Controller
- Uses `BadRequestException` (from SendGrid.Helpers) for domain validation errors.
- Retry mechanism: max 3 SAP posting attempts per RefNumber before marking as failed (DocumentStatus = 5).

### Event Handlers
- Use `BadRequestException` for validation failures (missing required fields).
- Helper methods (`GetRequiredString`, `GetRequiredDateTime`) throw on missing data.

## Data Access Patterns

### EF Core (primary)
```csharp
var result = await _context.BookingClaims
    .Where(obj => obj.Uuid == uuid)
    .FirstOrDefaultAsync();
```

### Raw ADO.NET (SAP operations on keyless tables)
```csharp
using (var connection = new SqlConnection(connectionString))
using (var command = new SqlCommand(sql, connection))
{
    command.Parameters.AddWithValue("@Param", value);
    await connection.OpenAsync();
    await command.ExecuteNonQueryAsync();
}
```

### AutoMapper (audit log creation)
```csharp
CreateMap<SapApprovalModel, SapapprovedLog>();
CreateMap<RejectLogModel, DocumentRejectLog>();
```

## Configuration

### appsettings.json Structure
```json
{
  "ConnectionStrings": { "DbConn": "..." },
  "AppSettings": { "BRIDGE_AUTH_TOKEN": "..." },
  "ServiceBusSettings": {
    "ServiceBusEndpoint": "...",
    "TopicName": "prod.booking",
    "Subscription": "reimbursement-booking-subscription"
  }
}
```

### Environment Switching
- Prod/UAT/Dev configs are commented in/out in appsettings.json (no per-environment files used in practice).
- `appsettings.Development.json` exists for local development overrides.

### CORS
Allowed origins configured in Program.cs:
- `http://localhost:3001` (local dev)
- `https://iqubeprod.tvsmotor.com`
- `https://tvsmonline.tvsmotor.com`
- `https://uat-bookingapi.tvsmotor.net`

## Testing

- **No test project exists.** No unit tests, integration tests, or test infrastructure.
- Manual testing via Swagger UI (enabled in Development environment).
- When adding tests, use xUnit (standard for .NET) with Moq for mocking repositories/services.

## Deployment

- **Hosting**: IIS on Windows Server (evidenced by `C:\inetpub\wwwroot\` file paths).
- **Database**: Azure SQL Server (`*.database.windows.net`).
- **Messaging**: Azure Service Bus (separate namespaces for prod/uat/dev).
- **Publish profiles** exist in `Properties/PublishProfiles/`.
- **No containerization** — no Dockerfile or docker-compose present.
- **No CI/CD pipeline files** visible in the repository.

## Known Technical Debt

1. **Hardcoded secrets** — Connection strings, Service Bus keys, and auth tokens in `Constants.cs` and `appsettings.json`. Should use Azure Key Vault or environment variables.
2. **Deprecated crypto** — `Encrypt.cs` uses `RijndaelManaged` (obsolete) with hardcoded passphrase/salt/IV.
3. **Mixed auth patterns** — JWT validation, static token comparison, and commented-out auth checks coexist.
4. **No input validation** — Controllers accept input without model validation attributes or FluentValidation.
5. **Inconsistent response format** — `Status`/`status`, `Message`/`message`, `data`/`Data` casing varies across endpoints.
6. **`throw ex`** in Dispatcher.cs — Loses stack trace. Should be `throw;`.
7. **No async consistency** — Some repository calls are synchronous within async methods (e.g., `FirstOrDefault()` instead of `FirstOrDefaultAsync()`).
8. **Windows-only file paths** — `SaveFileService` uses hardcoded Windows paths, preventing cross-platform development.
9. **Two Service Bus client libraries** — Both `Azure.Messaging.ServiceBus` (new) and `Microsoft.Azure.ServiceBus` (legacy, deprecated) are used simultaneously.
10. **Dynamic return types** — Several repository methods return `dynamic`, losing type safety.

