# DMS Domestic — High Level Code (HLC)

> Reference document for the DMS Domestic Angular system, generated against `.kiro/steering/HLC.md`.
>
> **Source repos**
> - Angular Frontend: `D:\DMS_DOMESTIC\ANGULAR_DMS`
> - .NET Web API: `D:\DMS_DOMESTIC\MICRO_DMS\MicroDMS\OnlineDMS_WebAPI`
>
> **Companion diagrams**
> - [Module Map](../diagrams/hlc-module-map.md)
> - [Runtime Flow](../diagrams/hlc-runtime-flow.md)
> - [Dependency Graph](../diagrams/hlc-dependency-graph.md)

---

## 1. Application Overview

DMS Domestic is the Dealer Management System used by TVS Motor channel partners (dealers / ASCs) for the Indian domestic market. It is delivered as a single product across two repos:

| Tier | Repo | Tech | Role |
|---|---|---|---|
| Client | `ANGULAR_DMS` | Angular 6 (TypeScript), PrimeNG, Bootstrap, Electron (optional desktop) | Dealer-facing SPA for Sales, Service, Parts, Accounts, Master, HO, Reports |
| Server | `MICRO_DMS / OnlineDMS_WebAPI` | ASP.NET Web API on .NET Framework 4.7.2, OWIN, Unity DI | REST API + integration hub for SAP, Oracle, UMS, Redis, Azure Blob, Service Bus, SendGrid, OTP/SMS providers |

The Angular SPA bootstraps from `src/main.ts` and routes through `AppRoutes`. Lazy-loaded feature modules (`sales`, `service`, `parts`, `accounts`, `master`, `ho`, `homedashboard`, `dmsreports`, `uvd-reports`, `UVD`) talk to the Web API through `app/api-services/*`. The Web API uses Unity-resolved dependencies, JWT/UMS auth filters, OpenTelemetry, and a Service Bus Function App for async work.

> See [Module Map](../diagrams/hlc-module-map.md) for the visual summary.

---

## 2. Major Modules / Components

### 2.1 Angular feature modules (lazy-loaded)

| Route | Module file | Responsibility |
|---|---|---|
| `/session` | `app/session/session.module.ts` | Login (UMS), idle handling, 404 |
| `/sales` | `app/sales/sales.module.ts` | Enquiry, Booking, Invoicing, Sales GRN, Stock Transfer, RTO, PSF, Returns, Quick Invoice |
| `/service` | `app/service/service.module.ts` | Job Card, Appointment, Service Reminder, Warranty, ASC Warranty, FSC Claim, AMC, Care Camp |
| `/parts` | `app/parts/parts.module.ts` | Parts master, GRN (vendor / other), Direct Invoice, Inventory check |
| `/accounts` | `app/accounts/accounts.module.ts` | Vouchers, Sub-ledger, Reconciliation, AdminID reports |
| `/master` | `app/master/master.module.ts` | Customer, Vehicle, Bank, Area, RTO, Insurance, Vendor, Labour masters |
| `/ho` | `app/ho/ho.module.ts` | HO admin operations |
| `/homedashboard` | `app/homedashboard/homedashboard.module.ts` | Dealer landing dashboard |
| `/dmsreports`, `/uvd-reports`, `/uvd` | `dmsreports.module.ts`, `uvd-reports.module.ts`, `UVD/uvd.module.ts` | Reports + UVD (Used Vehicle Division) |

Cross-cutting Angular modules:

- `app/shared/shared.module.ts` — shared components, pipes, directives
- `app/layout/master/master.component.ts` + `auth.component.ts` — shells (authed vs unauthed)
- `app/api-services/*` — HTTP client services (~50 services)
- `app/azure-storage/blob-storage.service.ts` — direct browser → Azure Blob uploads
- `app/Conviva-Service/conviva.service.ts` — analytics
- `app/session/session.service.ts` — HTTP interceptor for token / session

### 2.2 Backend solution projects (`MicroDMS.sln`)

| Project | Role |
|---|---|
| `OnlineDMS_WebAPI` | **Primary REST surface** — ~67 controllers, OWIN startup (`Global.asax.cs`), Unity DI, OpenTelemetry, auth filters |
| `MicroDMS.BusinessLayer` (~166 classes) | Business orchestration per domain (BookingBL, JobCardBL, ASCWarrantyClaimBL, AccountsFun, etc.) |
| `MicroDMS.BusinessEntities` (~297 DTOs) | Domain DTOs grouped by feature (ATP, ATW, Booking, Accessory, Banks, ATWs, etc.) |
| `MicroDMS.DataLayer` | ADO.NET data access; SQL stored-procedure callers |
| `MicroDMS.EntityObjects` | EF entities / typed DataSets |
| `MicroDMS.ServiceLayer` | Outbound service contracts (SOAP/REST) |
| `MicroDMS.CacheLibrary` | Redis cache helpers (used by `RedisCacheLayer.cs`) |
| `MicroDMS.ConfigHelper` | Strongly-typed config readers |
| `MicroDMS.ExceptionManager` | `LogGeneration` static + delegates wired to OpenTelemetry from Web API |
| `MicroDMS.Utilities` | Cross-cutting helpers (date, validation, file, string) |
| `MicroDMS.Tests` | Unit tests |
| `DMSFunctionApp` | Azure Function — Service Bus topic worker for async work |
| `MicroDMS.Web`, `MicroDMS` | Legacy Web Forms surface (kept for transition) |

### 2.3 Web API sub-areas

- `App_Start/` — `WebApiConfig`, `RouteConfig`, `FilterConfig`, `BundleConfig`, `IdentityConfig`, `UnityResolver`
- `Controllers/` — feature-aligned (Booking, JobCard, Sales, Parts, Accounts, OTP, UMS, External, Webhook…)
- `ExternalAPIs/Interfaces` + `ExternalAPIs/Implementations` — outbound HTTP clients (EMS, EvDmsBookingApi, NGD, Atp, BookingEngine, AzureBlob, TvsmEmsApi)
- `Webhook/` — inbound webhooks: ATP, AzureBlobService, BookingEngine 2.0, BookingService, CWIService, EnquiryService, NotificationService
- `Service References/` — SOAP refs (SAP, Oracle, ZMC, Insurance Policy Upload)
- `EmailServices/`, `OtpServices/`, `SmsServices/`, `SMSHelper/` — provider-specific clients (SendGrid, Infobip, TinySMS, Mahale, Otp.NET)
- `Security/`, `Providers/`, `RSAKeys/` — auth helpers and signing keys
- Top-level cross-cutting: `Authentication.cs`, `JwtAuthorizationFilterAttribute.cs`, `UMSAuthenticationAttribute.cs`, `HarithaAuthenticationAttribute.cs`, `BasicAuthenticationAttribute.cs`, `ApimTokenAcquisition.cs`, `TokenManager*.cs`, `RedisCacheLayer.cs`, `LogGenerationOTel.cs`, `OtelActivityModule.cs`, `TraceContextLogProcessor.cs`, `HtmlToPdfConverter.cs`, `ProjectConstants.cs`

---

## 3. Folder Structure Explanation

```
DMS_DOMESTIC/
├── ANGULAR_DMS/AngularDMS/
│   ├── .github/workflows/AngularDMS.yml       # Frontend CI
│   ├── package.json                             # root proxy
│   └── Work_In_Progress/Source_Code/AngularDMS/
│       ├── angular.json                         # CLI workspace
│       ├── package.json                         # actual deps + scripts
│       ├── main.js                              # Electron entry
│       └── src/
│           ├── main.ts                          # Angular bootstrap
│           ├── environments/                    # env-specific config
│           ├── assets/                          # static + azure-storage shim
│           └── app/
│               ├── app.module.ts                # root module + interceptors
│               ├── app.routing.ts               # lazy-loaded routes
│               ├── api-services/                # HTTP service layer (~50 services)
│               ├── azure-storage/               # browser-side blob uploads
│               ├── Conviva-Service/             # analytics
│               ├── shared/, layout/, pipes/, directive/, service/, session/
│               ├── sales/, service/, parts/, accounts/, master/
│               ├── ho/, homedashboard/
│               └── dmsreports/, uvd-reports/, UVD/
│
└── MICRO_DMS/MicroDMS/
    ├── MicroDMS.sln
    ├── .github/workflows/main.yml              # Backend CI
    ├── DMSFunctionApp/                          # Service Bus worker
    ├── MicroDMS.BusinessLayer/                  # BL classes per domain
    ├── MicroDMS.BusinessEntities/               # DTOs
    ├── MicroDMS.DataLayer/, EntityObjects/, ServiceLayer/
    ├── MicroDMS.CacheLibrary/, ConfigHelper/, ExceptionManager/, Utilities/
    └── OnlineDMS_WebAPI/                        # PRIMARY API SURFACE
        ├── App_Start/                           # WebApiConfig, RouteConfig, UnityResolver, FilterConfig
        ├── Controllers/                         # ~67 REST controllers
        ├── ExternalAPIs/Interfaces+Implementations
        ├── Webhook/                             # ATP, BookingEngine2.0, BookingService, NotificationService, etc.
        ├── EmailServices/, OtpServices/, SmsServices/, SMSHelper/
        ├── Service References/                  # SAP, Oracle, ZMC, Insurance
        ├── RSAKeys/                             # JWT keys (do NOT commit real values)
        ├── Web.config / Web.Release.config      # appSettings + connectionStrings
        ├── Global.asax(.cs)                     # OWIN startup, OpenTelemetry init
        └── ApplicationInsights.config
```

---

## 4. Core Business Workflows

| # | Flow | Key Angular module | Key controllers / BL |
|---|---|---|---|
| 1 | **Login → home dashboard** | `session`, `homedashboard` | `LoginController`, `UMSIntegrationController`, `JwtAuthorizationFilterAttribute` |
| 2 | **Vehicle Sales (Enquiry → Booking → Invoice)** | `sales` | `SalesController`, `SalesProcessController`, `MultiVehicleInvoiceController`, `SalesInvoiceProcessController`, `BookingBL` |
| 3 | **Job Card lifecycle** (create → service → complete → invoice) | `service` | `JobCardController`, `ServiceProcessController`, `ServiceClaimProcessController` |
| 4 | **Warranty / FSC / ASC claims** | `service` | `ASCFSCClaimBL`, `ASCWarrantyClaimBL`, `CounterWarrantyClaimBL`, `ServiceClaimProcessController` |
| 5 | **Parts inventory** (GRN, issue, returns) | `parts` | `PartsController`, `OtherVendorGRNController`, `SIBPartsController`, `ReportPartsController` |
| 6 | **Accounting** (vouchers, reconciliation, sub-ledger) | `accounts` | `AccountController`, `AccountModuleController`, `VoucherController`, `SubLedgerController` |
| 7 | **Masters** | `master` | `MasterController`, `CustomerMasterController`, `VehicleMasterController`, `BankMasterController`, `RTOMasterController`, `LabourMasterController` |
| 8 | **OTP / Notifications** | shared | `OTPController`, `NotificationsController`, `Webhook/NotificationService` |
| 9 | **Webhook ingest** (booking, enquiry, ATP, EV, CWI) | n/a | `Webhook/*` (consumed by external systems) |
| 10 | **Async fan-out** (events) | n/a | `DMSFunctionApp` Service Bus worker |

> See [Runtime Flow](../diagrams/hlc-runtime-flow.md) for a request-level sequence.

---

## 5. Key Services / Classes

### 5.1 Angular — selected services (under `app/api-services/`)

| Service | Purpose |
|---|---|
| `login.service.ts` | Login + UMS handshake |
| `session.service.ts` | HTTP interceptor (auth header, errors, idle) |
| `master.service.ts`, `master-data.service.ts` | Master data fetches |
| `job-card.service.ts`, `job-card-invoice.service.ts` | Service workflow |
| `sales-process.ts`, `multi-vehicle-invoice.service.ts`, `quick-invoice.service.ts` | Sales workflows |
| `dealer-fsc-claim.ts`, `asc-fsc-claim.ts`, `warranty-claim.ts`, `asc-warranty-claim.ts`, `transit-claim.ts` | Claims |
| `account-recon.service.ts`, `approvals.service.ts` | Accounting |
| `service-amc.service.ts`, `service-appoitment.service.ts`, `service-reminder.service.ts` | Service module |
| `psf.service.ts`, `vehicle-service-history.service.ts`, `vehicle-return.service.ts` | After-sales |
| `crm-welcom-kit.service.ts`, `care-camp.service.ts`, `atw.service.ts` | CRM / promo |
| `request.service.ts`, `common.service.ts`, `data-share.service.ts`, `nav-data.service.ts`, `menu.service.ts` | Cross-cutting |
| `export-excel.service.ts`, `Timeapi.service.ts`, `map.service.ts`, `scroll.service.ts` | Utilities |

### 5.2 Web API — startup, security, observability

- `WebApiApplication.Application_Start()` (`Global.asax.cs`)
  - Forces TLS 1.2.
  - Calls `InitializeOpenTelemetry()` — sets up `TracerProvider` (ASP.NET / HttpClient / SqlClient instrumentation, OTLP exporter, batch processor) and `LoggerFactory` (OTLP logs + `TraceContextLogProcessor`).
  - Wires `MicroDMS.ExceptionManager.LogGeneration.OTelWrite*` delegates to `OnlineDMS_WebAPI.Logging.LogGenerationOTel.*` — so BL/DAL log calls are exported through OTel.
  - Registers areas, `WebApiConfig`, `FilterConfig`, `RouteConfig`, `BundleConfig`.
  - Has a **kill switch** via `OTEL_ENABLED` appSetting and configurable BSP batch options (`OTEL_BSP_*`).
- `Application_BeginRequest` — handles CORS preflight (OPTIONS) by emitting allow-headers/methods/origin and short-circuiting.
- `RegisterUnityContainer.RegisterContainer(config)` (`UnityResolver.cs`) — DI graph; sample registrations:
  - `IEMSClient → EMSClient`
  - `IBookingStatusService → BookingStatusService`
  - `IEnquiryService → EnquiryService`
  - `ITvsmEmsApi → TvsmEmsApi`
  - `IVehicleStockTransferServiceBL → VehicleStockTransferServiceBL` (+ DAL)
  - `IVehicleStockReceiptServiceBL → VehicleStockReceiptServiceBL` (+ DAL)
  - `IEvDmsBookingApi → EvDmsBookingApi`
  - `INGDApi → NGDApi`
  - `IAtpService → AtpService`
  - `IBookingEngineService → BookingEngineService`, `IBookingEngineToken → BookingEngineToken`
  - `IAzureBlobService → AzureBlobService`
- `WebApiConfig.Register` — `application/json` formatter, attribute routing, `IncludeErrorDetailPolicy = Always`, default route `api/{controller}/{id}`.
- Auth attributes — `JwtAuthorizationFilterAttribute`, `UMSAuthenticationAttribute`, `HarithaAuthenticationAttribute`, `BasicAuthenticationAttribute`.
- `ApimTokenAcquisition` + `TokenManager*` — fetch B2C / APIM bearer tokens; `RedisCacheLayer` caches them.
- `LogGenerationOTel` / `OtelActivityModule` / `TraceContextLogProcessor` — OpenTelemetry plumbing.

### 5.3 Backend BL — selected classes (high-traffic flows)

| BL class (in `MicroDMS.BusinessLayer`) | Domain |
|---|---|
| `BookingBL`, `AngBookingBL` | Booking |
| `SalesProcessBL`, `MultiVehicleInvoiceBL`, `SalesInvoiceProcessBL` | Sales |
| `JobCardBL`, `ServiceProcessBL`, `ServiceClaimProcessBL` | Service / Job Card |
| `ASCFSCClaimBL`, `ASCWarrantyClaimBL`, `CounterWarrantyClaimBL` | Warranty / FSC |
| `PartsBL`, `OtherVendorGRNBL`, `SIBPartsBL` | Parts |
| `AccountsFun`, `AccountsFundsBL`, `AccountUtilities`, `AdminIDReportsBL` | Accounts |
| `CustomerMasterBL`, `VehicleMasterBL`, `BankMasterBL`, `LabourMasterBL`, `RTOMasterBL`, `BranchMasterBL` | Masters |
| `AMCBL`, `CareCampSchemeBL`, `ATWBL`, `ATWSchemesBL` | After-sales programs |
| `CICInfoBL`, `CommonMasterBL`, `CompanyMasterBL` | Cross-cutting masters |
| `CentralTaxProcessor` | Tax computation |

---

## 6. External Integrations

| Integration | Direction | Where it lives |
|---|---|---|
| **UMS / Azure AD B2C** | Outbound (auth) | `UMSAuthenticationAttribute`, `UMSIntegrationController`, `ApimTokenAcquisition`, `TokenManager*` |
| **APIM (Azure API Management)** | Outbound (gateway) | `ApimTokenAcquisition`, `ApimTokenDo` |
| **SAP** | Outbound | `Service References/OnlineDmsSapServices` (SOAP) |
| **Oracle** | Outbound | `Service References/OnlineDmsOracleService` |
| **ZMC** | Outbound | `Service References/ZMC_Service` |
| **Insurance Policy Upload** | Outbound | `Service References/InsurancePolicyUpload` |
| **Azure Blob Storage** | Both | Angular: `azure-storage/blob-storage.service.ts`; Web API: `Webhook/AzureBlobService/AzureBlobService.cs` |
| **Azure Service Bus topic** | Both | `DMSFunctionApp/ServiceBusTopicFunction.cs` (consumer) + WebAPI publishers |
| **SendGrid (Email)** | Outbound | `EmailServices/`, `Email.cs` |
| **Infobip / TinySMS / Mahale (SMS)** | Outbound | `SmsServices/`, `SMSHelper/`, `SMS.cs`, `InfobipAdditionalSms.cs`, `TinySmsController.cs`, `MahaleController.cs` |
| **OTP** | Outbound | `OtpServices/`, `OTPGenerationCls.cs`, `OTPController.cs` |
| **DigiSigner** | Outbound | `DigiSignerController.cs` |
| **EMS / TVSM EMS API** | Outbound | `ExternalAPIs/Implementations/EMSClient`, `TvsmEmsApi` |
| **EV DMS / NGD / ATP / BookingEngine 2.0** | Outbound + inbound webhooks | `Webhook/ATP`, `Webhook/BookingEngine2.0`, `Webhook/BookingService`, `Webhook/EnquiryService`, `Webhook/CWIService`, `ExternalAPIs/EvDmsBookingApi`, `NGDApi` |
| **Notification Service (DIGI ↔ DMS)** | Outbound | `Webhook/NotificationService/` (per the [DIGI-DMS Notification](https://tvsmotorcompany.atlassian.net/wiki/spaces/CPA/pages/4776755322) integration) |
| **Conviva analytics** | Outbound | Angular `Conviva-Service/conviva.service.ts` |
| **Time API** | Outbound | Angular `Timeapi.service.ts` |
| **Application Insights / OpenTelemetry / OTLP collector** | Outbound | `LogGenerationOTel.cs`, `OtelActivityModule.cs`, `TraceContextLogProcessor.cs`, `ApplicationInsights.config` |

---

## 7. Major Dependencies

### 7.1 Angular (`Work_In_Progress/Source_Code/AngularDMS/package.json`)

- **Framework:** `@angular/* 6.1.0`, `rxjs 6.0.0`, `zone.js 0.8.27`, `core-js 2.5.4`
- **UI:** `@angular/material 6.4.2`, `@angular/cdk 6.4.2`, `primeng 6.1.4`, `primeicons`, `bootstrap 3.3.7`, `font-awesome 4.7.0`, `ngx-bootstrap 2.0.2`, `ngx-datatable 13.0.1`, `ngx-toastr 8.10.0`, `ng-image-slider`, `ng2-charts 2.2.3`, `chart.js`, `ngx-color-picker`, `ngx-masonry`, `ngx-slick-carousel`, `slick-carousel`, `ngx-chips`, `ngx-infinite-scroll`
- **Forms / utility:** `crypto-js 4.2.0`, `dompurify 3.1.6`, `file-saver`, `md5-typescript`, `moment` + `moment-timezone`, `underscore`, `xlsx`, `xlsx-js-style`, `ng2-pdf-viewer`, `ng-idle/core` + `ng-idle/keepalive`, `angular-user-idle`, `hammerjs`
- **Analytics:** `@convivainc/conviva-js-appanalytics`
- **Build / dev:** `@angular/cli 6.1.1`, `@angular-devkit/build-angular 0.7.0`, `typescript 2.7.2`, `karma 1.7.1`, `jasmine-core 2.99.1`, `protractor 5.3.0`, `tslint`, `codelyzer`, `node-sass 4.12.0`, `node-gyp 8.4.1`

### 7.2 Web API (`OnlineDMS_WebAPI.csproj` references)

- **Runtime / framework:** .NET Framework 4.7.2, ASP.NET Web API 5.2.3, OWIN, Unity (DI), Newtonsoft.Json 13.0.3
- **Auth / tokens:** Microsoft.IdentityModel.Tokens 6.11.1, System.IdentityModel.Tokens.Jwt 6.11.1, Microsoft.IdentityModel.JsonWebTokens 6.11.1, Microsoft.Owin.Security 4.2.2
- **Cloud SDK:** Azure.Core 1.22, Azure.Storage.Blobs 12.11, Azure.Storage.Common 12.10
- **Cache:** StackExchange.Redis 2.6.122, Pipelines.Sockets.Unofficial 2.2.8
- **Telemetry:** Microsoft.ApplicationInsights 2.0.0 (+ Web/DependencyCollector/PerfCounter/ServerTelemetryChannel), OpenTelemetry 1.15, OpenTelemetry.Api, OpenTelemetry.Exporter.OpenTelemetryProtocol, OpenTelemetry.Instrumentation.AspNet / Http / SqlClient, OpenTelemetry.Extensions.Hosting, Microsoft.Extensions.Logging 10.0
- **Documents / barcodes:** PDFsharp 1.32, HtmlRenderer.Core 1.5, HtmlRenderer.PdfSharp, Select.HtmlToPdf, DocumentFormat.OpenXml, BarcodeStandard 3.1.4, MessagingToolkit.QRCode, SkiaSharp 2.88.8
- **HTTP / messaging:** RestSharp 105.0, SendGrid 9.29.3, Otp.NET 1.3
- **Crypto:** Portable.BouncyCastle 1.8.9, starkbank-ecdsa 1.3.3, System.Security.Cryptography.* (compat)
- **API docs:** Swashbuckle.Core 5.6.0
- **System (compat):** System.Buffers, System.Memory, System.Memory.Data, System.Text.Json 6.0.11, System.Text.Encodings.Web 6.0.1, System.Threading.Channels 5.0.0, System.IO.Pipelines 5.0.1, System.IO.Hashing 6.0.0

> See [Dependency Graph](../diagrams/hlc-dependency-graph.md) for a condensed visual.

---

## 8. Runtime Architecture

```
┌──────────────────────────┐    HTTPS + Bearer JWT     ┌────────────────────────────────────┐
│ Angular SPA (browser)    │ ─────────────────────────▶│ Azure API Management (validate-jwt)│
│ optional Electron host   │                           └─────────────────┬──────────────────┘
└────────────┬─────────────┘                                             │
             │ UMS sign-in (OAuth2)                                       ▼
             ▼                                          ┌──────────────────────────────────┐
   ┌────────────────────┐    issues JWT                 │ OnlineDMS_WebAPI (IIS, .NET 4.7.2)│
   │ Azure AD B2C / UMS │ ────────────────────────────▶│ OWIN startup • Unity DI            │
   └────────────────────┘                               │ Auth filters (JWT/UMS/Haritha/Basic)│
                                                       │ Controllers → BusinessLayer → DAL  │
                                                       └─────┬───────────┬───────────┬──────┘
                                                             │           │           │
                                                             ▼           ▼           ▼
                                                          SQL Server   Oracle      SAP / ZMC / Insurance
                                                          (primary)    (legacy)    (SOAP)
                                                             │
                                                             ├─▶ Redis (StackExchange) — token + cache
                                                             ├─▶ Azure Blob — uploads / docs
                                                             ├─▶ Service Bus topic ─▶ DMSFunctionApp
                                                             ├─▶ SendGrid (email)
                                                             ├─▶ Infobip / TinySMS / Mahale (SMS)
                                                             ├─▶ Otp.NET / OTP providers
                                                             ├─▶ Application Insights + OTLP collector
                                                             └─▶ DigiSigner / EMS / NGD / ATP / BookingEngine
```

- **Process model:** ASP.NET on IIS, OWIN startup, Unity-resolved per-request DI scope (`UnityResolver.BeginScope()` returns child container).
- **Hot paths:** Login → JWT issued → cached in Redis. Subsequent requests validated by `JwtAuthorizationFilterAttribute` and forwarded to BL → DAL → SQL stored procs.
- **Async path:** WebAPI publishes domain events to Azure Service Bus topic → `DMSFunctionApp/ServiceBusTopicFunction.cs` consumes them.
- **Telemetry:** OpenTelemetry traces (ASP.NET, HttpClient, SqlClient) and logs are exported via OTLP/HttpProtobuf with batch processor; Application Insights also active.

---

## 9. Important Entry Points

| Side | Entry point | Purpose |
|---|---|---|
| Angular | `src/main.ts` | Bootstraps `AppModule` via `platformBrowserDynamic` |
| Angular | `src/app/app.module.ts` | Root NgModule — registers `SessionService` HTTP interceptor, `BlobStorageService`, `ConvivaService`, `UserIdleModule`, toastr |
| Angular | `src/app/app.routing.ts` | Lazy routes for `session`, `sales`, `service`, `parts`, `accounts`, `master`, `ho`, `homedashboard`, `dmsreports`, `uvd*`, `UVD` |
| Angular | `main.js` | Electron desktop entry — loads `dist/index.html` |
| Web API | `Global.asax.cs → Application_Start` | OWIN startup, OTel init, areas, route/filter/bundle config |
| Web API | `App_Start/WebApiConfig.Register` | Routing + JSON formatter |
| Web API | `App_Start/UnityResolver.RegisterContainer` | DI graph |
| Web API | `App_Start/FilterConfig`, `RouteConfig`, `BundleConfig`, `IdentityConfig` | Cross-cutting setup |
| Web API | `Authentication.cs`, `JwtAuthorizationFilterAttribute.cs`, `UMSAuthenticationAttribute.cs`, etc. | Per-request auth |
| Service Bus worker | `DMSFunctionApp/Program.cs` + `ServiceBusTopicFunction.cs` | Async event consumer |
| CI | `.github/workflows/AngularDMS.yml`, `.github/workflows/main.yml` | Build & deploy pipelines |

---

## 10. High-Level Data Flow

1. **Authentication**
   - Angular `LoginComponent` calls `login.service.ts` → UMS endpoints (`umsLogin*`).
   - UMS issues JWT; Angular stores it; `SessionService` (HTTP interceptor) attaches `Authorization: Bearer <jwt>` to every outbound request.
2. **Read flow (e.g. fetch master / list)**
   - Angular component → `*.service.ts` → HTTPS to APIM → `validate-jwt` → Web API controller.
   - Controller resolves BL via Unity → BL calls DAL → DAL executes stored procs against SQL Server (or Oracle for specific flows).
   - Response serialized via Newtonsoft.Json → Angular updates view model.
3. **Write flow (e.g. create Job Card / Sales Invoice)**
   - Angular form posts payload → controller validates → BL applies rules and calls DAL → SQL transaction commits.
   - For events (booking confirmed, invoice created), publishers push messages to Azure Service Bus topic → `DMSFunctionApp` consumes.
4. **External integrations**
   - SAP / Oracle / ZMC / Insurance — synchronous SOAP via Service References (used inside BL).
   - SendGrid / Infobip / OTP — fire-and-await from BL via `EmailServices` / `SmsServices` / `OtpServices`.
   - DigiSigner / EMS / NGD / ATP / BookingEngine — through `ExternalAPIs/Implementations/*`, often token-protected via APIM.
5. **Caching**
   - APIM tokens, master data, hot lookups — cached via `RedisCacheLayer` (StackExchange.Redis).
6. **File / image flows**
   - Browser uploads directly to Azure Blob via `azure-storage/blob-storage.service.ts` (SAS-based).
   - Web API also reads/writes blobs via `Webhook/AzureBlobService`.
7. **Observability**
   - OpenTelemetry: ASP.NET / HttpClient / SqlClient instrumentations → batch OTLP exporter → collector.
   - `MicroDMS.ExceptionManager.LogGeneration` delegates → `LogGenerationOTel` → ILogger → OTLP logs.
   - Application Insights running in parallel (`ApplicationInsights.config`).

> See [Runtime Flow](../diagrams/hlc-runtime-flow.md) for the swim-lane visual.

---

## 📌 Expected Outputs (per `.kiro/steering/HLC.md`)

### Application Overview
DMS Domestic = Angular 6 SPA (with optional Electron desktop) + ASP.NET Web API on .NET Framework 4.7.2, used by TVS dealers for Sales, Service, Parts, Accounts, Master and HO operations across India.

### Module Summary
- **Frontend modules:** `session`, `sales`, `service`, `parts`, `accounts`, `master`, `ho`, `homedashboard`, `dmsreports`, `uvd-reports`, `UVD`, `shared`.
- **Backend solution projects:** `OnlineDMS_WebAPI` (REST), `BusinessLayer` (~166 classes), `BusinessEntities` (~297 DTOs), `DataLayer`, `EntityObjects`, `ServiceLayer`, `CacheLibrary`, `ConfigHelper`, `ExceptionManager`, `Utilities`, `Tests`, `DMSFunctionApp` (Service Bus worker), legacy `MicroDMS.Web` / `MicroDMS`.
- **Web API sub-areas:** `App_Start/`, `Controllers/` (~67), `ExternalAPIs/`, `Webhook/`, `EmailServices/`, `OtpServices/`, `SmsServices/`, `Service References/` (SAP / Oracle / ZMC / Insurance), `Security/`, `Providers/`, `RSAKeys/`.

### Dependency Overview
- **Frontend:** Angular 6 + RxJS 6 + Zone.js, PrimeNG 6, Bootstrap 3, Material 6, NGX ecosystem (datatable, toastr, charts, color-picker, masonry), CryptoJS, DOMPurify, Moment, Underscore, XLSX, Conviva analytics, Karma + Jasmine + Protractor for tests.
- **Backend:** ASP.NET Web API 5.2.3, OWIN, Unity DI, Newtonsoft.Json 13, IdentityModel JWT 6.11, Azure.Storage.Blobs 12.11, StackExchange.Redis 2.6, OpenTelemetry 1.15 (+ASP.NET/Http/Sql instrumentation, OTLP exporter), Application Insights 2.0, SendGrid 9.29, Otp.NET 1.3, PDFsharp + HtmlRenderer + Select.HtmlToPdf, DocumentFormat.OpenXml, BarcodeStandard, SkiaSharp, Swashbuckle, RestSharp, BouncyCastle.

### Runtime Flow
Browser SPA → APIM (`validate-jwt`) → OnlineDMS_WebAPI controllers → BusinessLayer → DataLayer → SQL Server / Oracle. Side flows hit SAP / ZMC / Insurance via SOAP, Azure Blob for files, Service Bus for async events (consumed by `DMSFunctionApp`), SendGrid / SMS providers / OTP for messaging. Tokens cached in Redis. Telemetry via OpenTelemetry + Application Insights.

### Key Services
- **Frontend:** `SessionService` (interceptor), `LoginService`, `MasterService`, `JobCardService`, `SalesProcess`, `MultiVehicleInvoiceService`, `WarrantyClaim`, `BlobStorageService`, `ConvivaService`.
- **Backend:** `WebApiApplication` (OWIN/OTel startup), `RegisterUnityContainer`, auth filters (`JwtAuthorizationFilterAttribute`, `UMSAuthenticationAttribute`, `HarithaAuthenticationAttribute`, `BasicAuthenticationAttribute`), `ApimTokenAcquisition`, `TokenManager*`, `RedisCacheLayer`, `LogGenerationOTel`, BL classes (`BookingBL`, `JobCardBL`, `ASCWarrantyClaimBL`, `AccountsFun`, `SalesProcessBL`).

### Integration Summary
UMS / Azure AD B2C, Azure API Management, SAP, Oracle, ZMC, Insurance Policy Upload, Azure Blob Storage, Azure Service Bus, SendGrid, Infobip, TinySMS, Mahale, Otp.NET, DigiSigner, EMS / TVSM EMS API, EV DMS, NGD, ATP, BookingEngine 2.0, Notification Service (DIGI-DMS), Conviva, Application Insights + OpenTelemetry collector.

---

_Source: ANGULAR_DMS + OnlineDMS_WebAPI_
