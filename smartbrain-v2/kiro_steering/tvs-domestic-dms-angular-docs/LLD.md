# DMS Domestic — Low Level Design (LLD)

> Authored against `.kiro/steering/LLD.md` and the [TVS LLD Template](https://tvsmotorcompany.atlassian.net/wiki/spaces/DE2/pages/4209606912/Low+Level+Design+Template).
>
> **Source repos**
> - Angular Frontend: `D:\DMS_DOMESTIC\ANGULAR_DMS`
> - .NET Web API: `D:\DMS_DOMESTIC\MICRO_DMS\MicroDMS\OnlineDMS_WebAPI`
>
> **Companion documents:** [HLD](./HLD.md) · [HLC](./HLC.md)
>
> **Companion diagrams**
> - [Class Diagram](../diagrams/lld-class-diagram.md)
> - [Request / Response Lifecycle](../diagrams/lld-request-response-lifecycle.md)
> - [Database Schema](../diagrams/lld-database-schema.md)
> - [Validation & Error Flow](../diagrams/lld-validation-error-flow.md)
> - [Component Interaction](../diagrams/lld-component-interaction.md)
>
> **Audience:** External engineering vendors onboarding to DMS Domestic. This document focuses on *implementation detail* — how the layers are wired, what each class does, how a request is processed end to end, and where the business rules live. It deliberately avoids secrets, connection strings, tokens and credentials.

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Detailed Module Breakdown](#2-detailed-module-breakdown)
3. [Class / Service Responsibilities](#3-class--service-responsibilities)
4. [API Flow Details](#4-api-flow-details)
5. [Internal Component Interactions](#5-internal-component-interactions)
6. [Database Schema Usage](#6-database-schema-usage)
7. [Request / Response Lifecycle](#7-request--response-lifecycle)
8. [Validation Logic](#8-validation-logic)
9. [Error Handling](#9-error-handling)
10. [Key Algorithms / Business Rules](#10-key-algorithms--business-rules)
11. [Configuration Handling](#11-configuration-handling)
12. [TVS LLD Template Sections](#12-tvs-lld-template-sections)
13. [Appendix](#appendix)

---

## 1. Purpose & Scope

DMS Domestic is the Dealer Management System for TVS Motor channel partners (dealers / ASCs) in the Indian domestic market. It is built as two tiers:

| Tier | Repo / Project | Technology |
|---|---|---|
| Client | `ANGULAR_DMS` (`Work_In_Progress/Source_Code/AngularDMS`) | Angular 6 SPA + optional Electron desktop |
| Server | `MICRO_DMS/MicroDMS/OnlineDMS_WebAPI` + class libraries | ASP.NET Web API on .NET Framework 4.7.2, OWIN, Unity DI |

This LLD documents the **server-side implementation** in depth (controllers → Business Layer → Data Layer → SQL/Oracle) and the **client-side service layer** that drives it. The intent is that a new vendor can read this document plus the five companion diagrams and be productive without reverse-engineering the codebase.

**Out of scope / not exposed:** real connection strings, JWT signing keys (`RSAKeys/`), APIM subscription keys, SAP/Oracle credentials, SendGrid/SMS provider secrets. All such values are referenced by *config key name only*.

---

## 2. Detailed Module Breakdown

The solution (`MicroDMS.sln`) is layered. Each layer is a separate .NET project; the Angular app is a separate CLI workspace.

### 2.1 Layering overview

```
Angular SPA (api-services/*)
      │  HTTPS + Bearer JWT
      ▼
APIM (validate-jwt)
      ▼
OnlineDMS_WebAPI            ← Presentation / API tier (controllers, filters, DI, OTel)
      ▼
MicroDMS.BusinessLayer     ← Business orchestration + rules (~166 *BL / *Fun classes)
      ▼
MicroDMS.DataLayer         ← ADO.NET stored-procedure callers (~190 *DAL / *DH classes)
      ▼
SQL Server (primary) · Oracle (legacy reads)
```

Supporting libraries sit beside the layers:

| Project | Responsibility |
|---|---|
| `MicroDMS.BusinessEntities` | ~297 DTO/DO classes (`*DO`, `*DataObjects`) — the contract objects passed between layers and serialized to JSON. |
| `MicroDMS.EntityObjects` | Typed DataSets / EF entities used by some legacy flows. |
| `MicroDMS.ServiceLayer` | Outbound service contracts (SOAP / REST wrappers). |
| `MicroDMS.CacheLibrary` | Redis cache helpers consumed by `RedisCacheLayer`. |
| `MicroDMS.ConfigHelper` | Strongly-typed configuration readers. |
| `MicroDMS.ExceptionManager` | `LogGeneration` — central logging with OTel delegate hooks. |
| `MicroDMS.Utilities` | Cross-cutting helpers (date, string, file, validation). |
| `DMSFunctionApp` | Azure Function — Service Bus topic worker for async fan-out. |
| `MicroDMS.Web`, `MicroDMS` | Legacy Web Forms surface (transitional). |

> The layer wiring is visualized in [Component Interaction](../diagrams/lld-component-interaction.md).

### 2.2 OnlineDMS_WebAPI sub-modules

| Folder | Contents | Notes |
|---|---|---|
| `App_Start/` | `WebApiConfig`, `RouteConfig`, `FilterConfig`, `BundleConfig`, `IdentityConfig`, `UnityResolver` | Startup wiring; DI graph in `UnityResolver.cs`. |
| `Controllers/` | ~67 `ApiController` classes (e.g. `JobCardController`, `SalesProcessController`, `MultiVehicleInvoiceController`, `AccountController`, `MasterController`, `OTPController`). | Feature-aligned; many are very large (e.g. `JobCardController` ≈ 17k lines). |
| `Controllers/StockTransfer/` | Stock transfer / receipt controllers. | DI-injected via interfaces. |
| `ExternalAPIs/Interfaces` + `Implementations` | `IEvDmsBookingApi`/`EvDmsBookingApi`, `INGDApi`/`NGDApi`, `ITvsmEmsApi`/`TvsmEmsApi`. | Outbound partner REST clients. |
| `Webhook/` | Inbound + integration clients: `ATP`, `BookingEngine2.0`, `BookingService`, `CWIService`, `EnquiryService`, `NotificationService`, `AzureBlobService`, `EMSClient`. | Each has an `I*` interface for DI. |
| `Service References/` | SOAP proxies: SAP (`OnlineDmsSapServices`), Oracle (`OnlineDmsOracleService`), `ZMC_Service`, `InsurancePolicyUpload`, `CentralCustVehicleDetails`, `CRMAvailablePoints`. | Generated WCF clients. |
| `EmailServices/`, `OtpServices/`, `SmsServices/`, `SMSHelper/` | Provider-specific messaging clients (SendGrid, Infobip, TinySMS, Mahale, Otp.NET). | Wrapped by `Email.cs`, `SMS.cs`, `OTPGenerationCls.cs`. |
| `Security/`, `Providers/`, `RSAKeys/` | Auth helpers + JWT signing keys. | **Keys must come from KeyVault / encrypted config — never committed.** |
| `Models/` | API-level models incl. the `Output` response envelope. | |
| `Enums/`, `DTOs/` | API enums (e.g. `IssueMode`, `JobType`) and request/response DTOs. | |
| Cross-cutting root files | `Global.asax.cs`, `JwtAuthorizationFilterAttribute.cs`, `UMSAuthenticationAttribute.cs`, `HarithaAuthenticationAttribute.cs`, `BasicAuthenticationAttribute.cs`, `ApimTokenAcquisition.cs`, `TokenManager*.cs`, `RedisCacheLayer.cs`, `LogGenerationOTel.cs`, `OtelActivityModule.cs`, `TraceContextLogProcessor.cs`, `HtmlToPdfConverter.cs`, `ProjectConstants.cs`, `ConfigSettings.cs`. | |

### 2.3 Angular feature modules

| Route | Module | Key services (`app/api-services/`) |
|---|---|---|
| `/session` | `session.module.ts` | `login.service.ts`, `session.service.ts` |
| `/sales` | `sales.module.ts` | `sales-process.ts`, `multi-vehicle-invoice.service.ts`, `quick-invoice.service.ts`, `master.sales.ts` |
| `/service` | `service.module.ts` | `job-card.service.ts`, `job-card-invoice.service.ts`, `service-appoitment.service.ts`, `service-reminder.service.ts`, `service-amc.service.ts`, `outwork-process.service.ts`, `warranty-claim.ts`, `asc-warranty-claim.ts`, `asc-fsc-claim.ts`, `dealer-fsc-claim.ts`, `transit-claim.ts` |
| `/parts` | `parts.module.ts` | parts-related services |
| `/accounts` | `accounts.module.ts` | `account-recon.service.ts`, `account-bankData.ts`, `approvals.service.ts` |
| `/master` | `master.module.ts` | `master.service.ts`, `master-data.service.ts`, `non-individual-customer-search.service.ts` |
| `/ho` | `ho.module.ts` | `ho-login-service.service.ts` |
| `/homedashboard` | `homedashboard.module.ts` | `nav-data.service.ts`, `menu.service.ts` |
| `/dmsreports`, `/uvd-reports`, `/uvd` | reports + UVD modules | `reports.service.ts`, `adfcs-claim-report.ts`, `refurbishment.service.ts` |

Cross-cutting Angular services: `request.service.ts` (HTTP wrapper), `common.service.ts`, `data-share.service.ts`, `session.service.ts` (interceptor + idle), `export-excel.service.ts`, `Timeapi.service.ts`, `map.service.ts`, `scroll.service.ts`.

> See [Class Diagram](../diagrams/lld-class-diagram.md) for the key types across both tiers.

---

## 3. Class / Service Responsibilities

This section documents the concrete responsibilities of the most important classes a vendor will touch. Where a class is representative of a pattern, the pattern is called out so the same understanding applies to its siblings.

### 3.1 Presentation tier — startup & cross-cutting

| Class | File | Responsibility |
|---|---|---|
| `WebApiApplication` | `Global.asax.cs` | OWIN/ASP.NET entry. `Application_Start()` forces TLS 1.2, calls `InitializeOpenTelemetry()`, wires `LogGeneration.OTelWrite*` delegates to `LogGenerationOTel`, registers areas + `WebApiConfig` + `FilterConfig` + `RouteConfig` + `BundleConfig`. `Application_BeginRequest` handles CORS preflight (OPTIONS short-circuit). Honours the `OTEL_ENABLED` kill switch. |
| `WebApiConfig` | `App_Start/WebApiConfig.cs` | Configures the JSON formatter (`DefaultContractResolver`, ignores `[Serializable]`), calls `RegisterUnityContainer.RegisterContainer(config)`, enables attribute routing, registers the default route `api/{controller}/{id}`, sets `IncludeErrorDetailPolicy = Always`. |
| `RegisterUnityContainer` | `App_Start/UnityResolver.cs` | Builds the Unity DI graph (interface → implementation registrations) and installs the `UnityResolver` dependency resolver. `BeginScope()` returns a per-request child container. |
| `UnityResolver` | `App_Start/UnityResolver.cs` | `IDependencyResolver` implementation; resolves controllers and their injected services per request. |
| `FilterConfig` / `RouteConfig` / `BundleConfig` / `IdentityConfig` | `App_Start/*` | MVC-side filters, routes, bundles and identity scaffolding for the legacy MVC surface. |

### 3.2 Presentation tier — authentication filters

| Class | File | Responsibility |
|---|---|---|
| `UMSAuthentication` (`AuthorizationFilterAttribute`) | `UMSAuthenticationAttribute.cs` | Primary gate for UMS-authenticated endpoints. Requires `Authorization: Bearer <token>`; rejects missing/blank tokens with `401`; calls `TokenManager.GetPrincipal(token)` and rejects expired/invalid tokens with `401`. |
| `JwtAuthorizeAttribute` (`AuthorizeAttribute`) | `JwtAuthorizationFilterAttribute.cs` | Specialized JWT validation (e.g. invoice-cancel flow). Builds `TokenValidationParameters` (validate issuer/audience/lifetime/signing key) from app settings and validates with `JwtSecurityTokenHandler`. On failure returns the standard `Output` envelope with `statusCode = 401`. |
| `HarithaAuthentication` | `HarithaAuthenticationAttribute.cs` | Auth for the Haritha partner integration endpoints. |
| `BasicAuthentication` | `BasicAuthenticationAttribute.cs` | Basic-auth gate for specific service-to-service / webhook endpoints. |
| `TokenManager` / `TokenManager1` / `TokenManager2` | `TokenManager*.cs` | Token parsing/validation helpers; `GetPrincipal` returns a `ClaimsPrincipal` from a token. |
| `ApimTokenAcquisition` | `ApimTokenAcquisition.cs` | Acquires B2C/APIM bearer tokens for outbound calls; results cached in Redis. |
| `RedisCacheLayer` | `RedisCacheLayer.cs` | StackExchange.Redis wrapper for token + master/hot-lookup caching; logs via `LogGeneration.WriteToFileRedisLog`. |

### 3.3 Presentation tier — controllers (pattern)

Controllers derive from `System.Web.Http.ApiController`. The dominant pattern (seen in `JobCardController`, `BankMasterController`, etc.):

1. Accept a typed request DO (e.g. `StaticIssueModeDO`) or primitive parameters.
2. Construct an `Output` envelope (`statusCode`, `message`, `data`, `OTP_Count`).
3. Apply guard/validation checks inline, returning `Output` with `statusCode = 500` and a human-readable `message` on rule violations.
4. Call into the Business Layer (`*BL`) or directly into `DataAccessLayer` for read helpers.
5. Wrap the body in `try/catch`; on exception log via `LogGeneration` and return a failure `Output`.

Representative controllers:

| Controller | Domain | Notable BL/DAL collaborators |
|---|---|---|
| `LoginController`, `UMSIntegrationController` | Auth / session | `UMSIntegrationDAL`, `TokenManager`, `ApimTokenAcquisition` |
| `SalesController`, `SalesProcessController`, `SalesInvoiceProcessController`, `MultiVehicleInvoiceController` | Vehicle sales | `BookingBL`, `SalesProcessBL`, `MultiVehicleInvoiceBL`, `SalesVehicleInvoiceDAL` |
| `JobCardController`, `ServiceProcessController`, `ServiceClaimProcessController` | Service / job card | `JobCardBL`, `JobCardDAL`, `ServiceClaimProcessBL` |
| `PartsController`, `OtherVendorGRNController`, `SIBPartsController`, `ReportPartsController` | Parts | `PartsBL`, `OtherVendorGRNDAL`, `SparesGRNDAL`, `PartStockDAL` |
| `AccountController`, `AccountModuleController`, `VoucherController`, `SubLedgerController` | Accounts | `AccountsFun`, `AccountsFundsBL`, `VouchersDAL`, `SubLedgerDAL` |
| `MasterController`, `CustomerMasterController`, `VehicleMasterController`, `BankMasterController`, `RTOMasterController`, `LabourMasterController`, `VendorMasterController` | Masters | `CustomerMasterBL`, `VehicleMasterBL`, `BankMasterDAL`, `RTOMasterDAL` |
| `OTPController`, `NotificationsController`, `TinySmsController`, `MahaleController` | Messaging | `OTPGenerationCls`, `SMS`, `Email`, `InfobipAdditionalSms` |
| `ExternalAPIController`, `DigiSignerController`, `HarithaController`, `AzureController` | Integrations | `EvDmsBookingApi`, `NGDApi`, `TvsmEmsApi`, `AzureBlobService` |
| `CacheController` | Ops | `RedisCacheLayer` (cache warm/clear) |

### 3.4 Business tier — BL classes (pattern)

`*BL` (and `*Fun`) classes in `MicroDMS.BusinessLayer` orchestrate a use case: they validate cross-entity rules, compute derived values (tax, schemes, eligibility), call one or more `*DAL` methods, and assemble the result DO. They are mostly stateless and instantiated per call (some are DI-registered behind interfaces — e.g. `IVehicleStockTransferServiceBL`).

| BL class | Domain responsibility |
|---|---|
| `BookingBL`, `AngBookingBL` | Enquiry → Booking lifecycle, booking validations, scheme attachment. |
| `SalesProcessBL`, `MultiVehicleInvoiceBL`, `SalesInvoiceProcessBL` | Sales invoicing — price/tax computation, multi-vehicle invoice assembly. |
| `JobCardBL`, `ServiceProcessBL`, `ServiceClaimProcessBL` | Job card lifecycle, spare issue-mode eligibility, service claims. |
| `ASCFSCClaimBL`, `ASCWarrantyClaimBL`, `CounterWarrantyClaimBL` | Warranty / FSC / ASC claim validation and posting. |
| `PartsBL`, `OtherVendorGRNBL`, `SIBPartsBL` | Parts inventory — GRN, issue, returns, stock checks. |
| `AccountsFun`, `AccountsFundsBL`, `AccountUtilities`, `AdminIDReportsBL` | Voucher posting, fund management, reconciliation, reports. |
| `CustomerMasterBL`, `VehicleMasterBL`, `BankMasterBL`, `LabourMasterBL`, `RTOMasterBL`, `BranchMasterBL` | Master CRUD + validation. |
| `AMCBL`, `CareCampSchemeBL`, `ATWBL`, `ATWSchemesBL` | After-sales programs and scheme rules. |
| `CentralTaxProcessor` | Centralized GST/tax computation (CGST/SGST/IGST/UTGST). |

### 3.5 Data tier — DAL classes (pattern)

`*DAL` classes in `MicroDMS.DataLayer` are the *only* place SQL is executed. The canonical pattern (see `BankMasterDAL.cs`):

```csharp
public static List<BankMasterDO> getBankMasters()
{
    var list = new List<BankMasterDO>();
    try
    {
        DataAccessLayer.DataAccessLayerBaseClass dataAccess =
            DataAccessLayer.DataAccessLayerFactory.GetDataAccessLayer();
        dataAccess.StoredProcedureName = "Pr_Get_BanksMaster";          // stored proc, never inline SQL
        dataAccess.AddParameterToSQLCommand("@DEALER_ID", SqlDbType.Int, dealerId); // typed params
        return dataAccess.RetrieveDataIntoCollection(list, typeof(BankMasterDO)); // reflection map → DO
    }
    catch (Exception ex) { throw ex; }
}
```

Key data-tier helpers:

| Class | File | Responsibility |
|---|---|---|
| `DALHelper` | `DALHelper.cs` | Lower-level SQL helper: holds `SqlConnection`/`SqlCommand`, `CommandTimeout = 40000`, picks the connection string (`DMSConnection` or `OracleSQLPortal`) by `SQLConnectionType`. Exposes `ExecDataSet`, `ExecDataTable`, `ExecDML`, `ExecScalar`, `ExecReader`, generic `RetrieveDataIntoCollection<T>` / `ReturnSingleDataObject<T>`, and transaction methods (`BeginTransaction` with `IsolationLevel.Serializable`, `Commit`, `RollBack`). |
| `SqlDataAccessLayer` | `SqlDataAccess.cs` | Concrete SQL Server provider over the `DataAccessLayerBaseClass` abstraction (factory-created via `DataAccessLayerFactory`). |
| `DeadlockRetryHelper` | `DeadLockRetryHelper.cs` | Retries an action up to 3× on SQL error `1205` (deadlock) with incremental back-off; logs each attempt via `LogGeneration.WriteToFile`. |
| `OracleHelper` | `OracleHelper.cs` | Oracle equivalent for legacy reads (`OracleSQLPortal`). |
| `DataTableToList` / `PivotExtension` | `DeadLockRetryHelper.cs` | Generic `DataTable → List<T>` mapper and invoice tax pivot helper. |
| `*DH` classes (`JobCardDH`, `BookingDH`, `VehicleGRNDH`, …) | various | "Data Helper" companions that build XML payloads / parameter sets for complex stored procs. |

### 3.6 Angular service layer

| Service | Responsibility |
|---|---|
| `SessionService` | Registered as an `HTTP_INTERCEPTOR`. Reads the UMS JWT from `localStorage` (`UMStoken` / `UMSUser`), decodes it, checks `exp`, forces logout on expiry, and drives the `@ng-idle` idle/timeout watcher. |
| `LoginService` | UMS sign-in / sign-out handshake (`logout1()`), token storage. |
| `RequestService` / `CommonService` | Thin HTTP wrappers and shared helpers (language, headers, base URL from `environment.*`). |
| Feature services (`JobCardService`, `SalesProcess`, `MultiVehicleInvoiceService`, `WarrantyClaim`, `MasterService`, …) | One service per feature area; expose typed methods that POST/GET DTOs to APIM-fronted endpoints and return `Observable`s consumed by components. |
| `BlobStorageService` (`azure-storage/`) | Direct browser → Azure Blob uploads via SAS. |
| `ConvivaService` (`Conviva-Service/`) | Frontend analytics. |

> The full set of types and their relationships is in [Class Diagram](../diagrams/lld-class-diagram.md).

---

## 4. API Flow Details

### 4.1 Routing & conventions

- **Base path:** all traffic enters via APIM, which applies a `validate-jwt` policy and forwards to the Web API.
- **Routing:** attribute routing (`config.MapHttpAttributeRoutes()`) plus the convention route `api/{controller}/{id}`. Many controllers expose action methods reached as `api/{controller}/{action}` via `[Route]`/`[HttpPost]` attributes.
- **Verbs:** read endpoints are `GET`; create/update/posting endpoints are `POST` with a JSON body bound to a request DO. A few search endpoints use `POST` because they carry a filter DO.
- **Content type:** `application/json` (Newtonsoft.Json). The serializer ignores `[Serializable]` and uses `DefaultContractResolver`.

### 4.2 Standard response envelope

Every API action returns the `Output` envelope (`OnlineDMS_WebAPI.Models.Output`):

```csharp
public class Output
{
    public Int32  statusCode { get; set; } // 200 success, 401 unauthorized, 500 business/technical failure
    public string message    { get; set; } // human-readable status / validation message
    public object data       { get; set; } // payload (DO, list, scalar, or null)
    public int    OTP_Count  { get; set; } // used by OTP flows
}
```

Convention observed across controllers:
- **Success:** `statusCode = 200`, `message = "success"`, `data = <payload>`.
- **Business rule violation:** `statusCode = 500`, `message = "<reason>"`, `data = 0` (or empty).
- **Auth failure:** `statusCode = 401` (from filters), `message = "Unauthorized request"` / `"Token Expired or Invalid"`.

> Note: the envelope frequently returns HTTP `200 OK` at the transport level while signalling business failure via `statusCode = 500` inside the body. Vendors must inspect `body.statusCode`, not just the HTTP status.

### 4.3 Representative flows

**A. Master read — `BankMasterController` → `BankMasterDAL`**
```
GET api/BankMaster/getBankMasters
  → UMSAuthentication validates Bearer token
  → controller calls BankMasterDAL.getBankMasters()
  → DAL runs stored proc Pr_Get_BanksMaster, maps rows → List<BankMasterDO>
  → Output { 200, "success", data = [BankMasterDO...] }
```

**B. Service eligibility — `JobCardController.CheckPartClaim(StaticIssueModeDO)`**
```
POST api/JobCard/CheckPartClaim   (body: StaticIssueModeDO)
  → guard: if BRANCH_ID & DEALER_ID & FRAME_NO all empty → Output{200,"success"}
  → DataAccessLayer.GetSparePartForIssueMode(...) enriches the DO (warranty flags, KM bands)
  → warranty/issue-mode eligibility rules evaluated (see §10)
  → on violation → Output{500,"<reason>", data=0}; on success continues to posting
```

**C. Sales invoice create — `MultiVehicleInvoiceController` → `MultiVehicleInvoiceBL`**
```
POST api/MultiVehicleInvoice/...   (body: invoice DO)
  → BL computes tax (CentralTaxProcessor) + schemes (ATWSchemesBL)
  → DAL writes inside a serializable transaction (DALHelper.BeginTransaction/Commit)
  → on success: domain event published to Service Bus → DMSFunctionApp consumes
  → Output{200,"success", data = invoice result}
```

> The end-to-end sequence (incl. OTel spans and the async leg) is in [Request / Response Lifecycle](../diagrams/lld-request-response-lifecycle.md).

### 4.4 Authentication requirements per endpoint family

| Endpoint family | Filter | Token source |
|---|---|---|
| Dealer app endpoints (sales/service/parts/accounts/master) | `UMSAuthentication` | UMS / Azure AD B2C JWT |
| Invoice-cancel & specific secure flows | `JwtAuthorizeAttribute` | symmetric-key JWT (config-driven issuer/audience/key) |
| Haritha partner endpoints | `HarithaAuthentication` | partner token |
| Service-to-service / webhooks | `BasicAuthentication` | basic credentials |
| Outbound partner calls (EMS/NGD/ATP/BookingEngine) | n/a (client side) | APIM token via `ApimTokenAcquisition` (Redis-cached) |

---

## 5. Internal Component Interactions

### 5.1 Per-request collaboration

1. **APIM → Controller** — APIM validates the JWT and forwards. ASP.NET routing resolves the controller; `UnityResolver.BeginScope()` creates a per-request child container and injects dependencies (for DI-registered controllers/services).
2. **Auth filter** — the controller/action's auth attribute runs (`UMSAuthentication` etc.). On failure the pipeline short-circuits with `401` and the controller body never executes.
3. **Controller → BL** — the controller validates inputs, then calls a `*BL` method (or a DAL read helper for simple lookups).
4. **BL → DAL** — the BL applies business rules, then calls one or more `*DAL` methods. Multi-statement writes are wrapped in a `DALHelper` serializable transaction; deadlock-prone writes go through `DeadlockRetryHelper`.
5. **DAL → DB** — the DAL sets `StoredProcedureName`, adds typed `SqlParameter`s, executes, and maps the reader/`DataTable` into DOs via reflection (`RetrieveDataIntoCollection<T>` / `DataTableToList`).
6. **Side effects** — BL may call SOAP service references (SAP/Oracle/ZMC/Insurance), outbound REST (`ExternalAPIs/*`, `Webhook/*` clients), messaging (`Email`/`SMS`/`OTPGenerationCls`), or publish to Service Bus.
7. **Response** — BL returns a DO → controller wraps it in `Output` → Newtonsoft serializes → APIM forwards to the SPA.
8. **Observability** — throughout, OpenTelemetry instrumentations (ASP.NET, HttpClient, SqlClient) emit spans; `LogGeneration` calls are routed to `LogGenerationOTel` (OTLP) and Application Insights.

### 5.2 DI registrations (selected, from `UnityResolver.cs`)

| Interface | Implementation |
|---|---|
| `IEMSClient` | `EMSClient` |
| `IBookingStatusService` | `BookingStatusService` |
| `IEnquiryService` | `EnquiryService` |
| `ITvsmEmsApi` | `TvsmEmsApi` |
| `IEvDmsBookingApi` | `EvDmsBookingApi` |
| `INGDApi` | `NGDApi` |
| `IAtpService` | `AtpService` |
| `IBookingEngineService` / `IBookingEngineToken` | `BookingEngineService` / `BookingEngineToken` |
| `IAzureBlobService` | `AzureBlobService` |
| `IVehicleStockTransferServiceBL` / `IVehicleStockReceiptServiceBL` | `VehicleStockTransferServiceBL` / `VehicleStockReceiptServiceBL` (+ matching DAL) |

### 5.3 Async fan-out

`DMSFunctionApp/ServiceBusTopicFunction.cs` is a Service Bus topic-triggered Azure Function. The Web API publishes domain events (e.g. invoice created, booking confirmed); the function consumes them and performs downstream side-effects (partner sync, notifications). The subscription's native dead-lettering + retry provides at-least-once delivery semantics.

> Wiring is visualized in [Component Interaction](../diagrams/lld-component-interaction.md).

---

## 6. Database Schema Usage

DMS Domestic does **not** use an ORM-mapped schema for its core flows. All persistence goes through **stored procedures** invoked by `*DAL` classes; result sets are mapped to `*DO` objects by column-name reflection. Consequently the "schema" the application code knows about is the *stored-procedure contract* plus the result-set column names, not EF migrations.

### 6.1 Access model

| Aspect | Implementation |
|---|---|
| Primary store | SQL Server — connection string key `DMSConnection`. |
| Secondary store | Oracle (legacy reads) — connection string key `OracleSQLPortal` (via `OracleHelper`). |
| Invocation | `DataAccessLayerFactory.GetDataAccessLayer()` → `SqlDataAccessLayer`; `StoredProcedureName = "Pr_..."`; typed `AddParameterToSQLCommand`. |
| Mapping | `RetrieveDataIntoCollection<T>` / `ReturnSingleDataObject<T>` / `DataTableToList<T>` map columns → DO properties by name (case-insensitive), null-safe. |
| Transactions | `DALHelper.BeginTransaction(IsolationLevel.Serializable)` → `Commit()` / `RollBack()`. |
| Command timeout | 40000 (set on the `SqlCommand`). |
| Bulk / complex writes | XML payloads built by `*DH` helpers and passed to procs (e.g. `pr_Save_ASCWarranty` takes `@IN_ASC_WAR_HEADER_DATA` / `@IN_ASC_WAR_DETAIL_DATA` XML). |

### 6.2 Logical entity groups (inferred from DAL + DO names)

These are the principal logical tables/entities the procedures operate on. Exact physical table names live in the database; the application references them only through procs.

| Domain | Representative entities | Representative DAL / procs |
|---|---|---|
| **Sales / Booking** | Enquiry, Booking, Vehicle Invoice, Vehicle Stock, GRN, Stock Transfer | `BookingDAL`, `SalesVehicleInvoiceDAL`, `VehicleGRNDAL`, `VehicleInvoiceDAL`, `StockTransferDAL`, `VehiclePODAL` |
| **Service / Job Card** | Job Card, Job Card Invoice, Outwork, Spare Issue, Appointment, Service Reminder | `JobCardDAL`, `JobCardInvoiceDAL`, `JobCardOutWorkDAL`, `SpareIssueDAL`, `ServiceAppointmentDAL`, `ServiceReminderDAL` |
| **Warranty / Claims** | ASC Warranty, Counter Warranty, FSC Claim, Transit Claim, Spare Part Claim | `ASCWarrantyClaimDAL` (`pr_Save_ASCWarranty`, `pr_Modify_ASCWarranty`, `pr_UpdateASCWarrantyClaimStatus`), `CounterWarrantyClaimDAL`, `FSCClaimDAL`, `ASCFSCClaimDAL`, `TransitClaimDAL`, `SparePartClaimDAL` |
| **Parts / Inventory** | Part Master, Part Stock, Rack/Bin, GRN, Purchase Order, Returns | `PartMasterDAL`, `PartStockDAL`, `SparesGRNDAL`, `SparesPODAL`, `OtherVendorGRNDAL`, `SparesPurchaseReturnDAL`, `PhysicalInventoryCheckDAL`, `RackMasterDAL` |
| **Accounts** | Voucher, Sub-ledger, Credit/Debit, Balance, Reconciliation | `VouchersDAL`, `SubLedgerDAL`, `CreditManagerDAL`, `BalanceManagerDAL`, `AccountReconDAL`, `AccountsFunsDAL`, `CustomerBalanceDAL` |
| **Masters** | Customer, Vehicle, Bank, Area, RTO, State, Vendor, Dealer, Branch, Employee, Labour, Tax | `CustomerMasterDAL`, `VehicleDAL`/`VehicleModelDAL`, `BankMasterDAL`, `AreaMasterDAL`, `RTOMasterDAL`, `StateMasterDAL`, `VendorMasterDAL`, `DealerMasterDAL`, `BranchMasterDAL`, `EmployeeMasterDAL`, `LabourPriceDAL`, `TaxMasterDAL` |
| **Schemes / Programs** | AMC, Care Camp, ATW Schemes, HP Scheme, Coupons | `AMCDAL`, `CareCampSchemeDAL`, `ATWSchemesDAL`, `HPSchemeDAL`, `CouponMasterDAL` |
| **Auth / Session** | UMS integration, User, Menu | `UMSIntegrationDAL`, `UserDAL`, `MenuDAL` |
| **Reports** | Service / parts / accounts / dashboard reports | `ServiceReportDAL`, `PartsReportDAL`, `AccountsReportDAL`, `DashBoardRptDAL`, `GeneralRptDAL`, `S401RptDAL` |

> Naming suffix convention: `_MDP_DMS_DAL` variants target the MDP (master-data-platform) schema; the plain `*DAL` variants target the core DMS schema.

### 6.3 Stored-procedure & parameter conventions

- Proc names are prefixed `Pr_` / `pr_` (e.g. `Pr_Get_BanksMaster`, `pr_Save_ASCWarranty`, `pr_SearchASCWarrantyClaim`).
- Parameter names are `@UPPER_SNAKE` (e.g. `@DEALER_ID`, `@BRANCH_ID`, `@CLAIM_ID`, `@FROM_DATE`).
- Constant proc/param/XML-node names are centralized in `DALConstants` (`DeadLockRetryHelper.cs`) so the data tier shares a single source of truth for proc names.
- Output parameters (e.g. `@RESULT`, `@totalRows`) are read after execution for status and paging totals (`ExecDataSetPagewise`).

> The entity-relationship view and proc-contract examples are in [Database Schema](../diagrams/lld-database-schema.md).

---

## 7. Request / Response Lifecycle

End-to-end, a typical authenticated write request travels:

```
1. SPA component → feature service (api-services/*) builds a request DO
2. Angular HttpClient issues the request
   • SessionService interceptor checks the UMS JWT expiry (localStorage)
        – expired → toastr error + deferred logout1()
        – valid   → forwards request; resets @ng-idle watcher
   • Authorization: Bearer <jwt> header attached
3. APIM receives request → validate-jwt policy
   • invalid/expired/missing → 401 short-circuit at the gateway
   • valid → forward to OnlineDMS_WebAPI
4. ASP.NET pipeline
   • Application_BeginRequest handles CORS preflight (OPTIONS short-circuit)
   • routing resolves controller/action
   • UnityResolver.BeginScope() → per-request child container
   • auth filter (UMSAuthentication / JwtAuthorize / Haritha / Basic) validates token
        – fail → Output{401,...}
5. Controller action
   • binds JSON body → request DO
   • inline guard/validation → on fail Output{500,"<reason>"}
   • calls *BL
6. Business Layer
   • applies business rules / computes tax & schemes
   • calls *DAL (read or transactional write)
7. Data Layer
   • DALHelper opens SqlConnection (DMSConnection)
   • sets StoredProcedureName + typed params
   • write: BeginTransaction(Serializable) → ExecDML → Commit (RollBack on error)
   • read: ExecReader/ExecDataTable → reflection map → DO list
   • deadlock (SQL 1205) → DeadlockRetryHelper retries ≤3×
8. Side effects (optional)
   • SOAP (SAP/Oracle/ZMC/Insurance), REST (EMS/NGD/ATP/BookingEngine)
   • Email/SMS/OTP
   • publish domain event → Service Bus topic → DMSFunctionApp (async)
9. Response assembly
   • BL returns DO → controller wraps in Output{200,"success",data}
   • Newtonsoft serializes → APIM → SPA
10. SPA updates the component view model from body.data (after checking body.statusCode)
11. Observability runs in parallel: OTel spans (ASP.NET/HttpClient/SqlClient) + LogGenerationOTel logs + App Insights
```

Key timing/ownership notes for vendors:
- The **business outcome is in `body.statusCode`**, not the HTTP status — a failed rule still returns HTTP 200 with `statusCode = 500`.
- The **transaction boundary is in the DAL** (`DALHelper`), not the controller — keep multi-statement writes inside a single `BeginTransaction/Commit` block.
- The **idle/session timeout is client-driven** (`SessionService` + `@ng-idle`), independent of server token lifetime; both must agree for a smooth UX.

> Full sequence diagram: [Request / Response Lifecycle](../diagrams/lld-request-response-lifecycle.md).

---

## 8. Validation Logic

Validation is layered; there is no single framework — it is explicit, defensive code at each tier.

### 8.1 Client tier (Angular)
- **Template/reactive form validation** in feature components (required fields, formats) before a request is sent.
- **Token/session validation** in `SessionService.intercept` — decodes the UMS JWT, compares `exp * 1000` to `Date.now()`, forces logout on expiry.
- **Idle validation** — `@ng-idle` (`setIdle(10)`, `setTimeout(3000)`) logs the user out on inactivity.
- **Sanitization** — `dompurify` is available for HTML sanitization; `crypto-js` / `md5-typescript` for client-side hashing where required.

### 8.2 Gateway tier (APIM)
- `validate-jwt` enforces issuer, audience, signature and expiry before the request reaches the API. Rate-limit/quota policies (where configured) protect the backend.

### 8.3 API tier (filters + controllers)
- **Auth filters** validate the bearer token (`UMSAuthentication`, `JwtAuthorizeAttribute` with `TokenValidationParameters`).
- **Inline guards** in controller actions check presence/shape of inputs and return `Output{500,"<message>"}` on violation. Example from `JobCardController.CheckPartClaim`:
  - If `BRANCH_ID`, `DEALER_ID`, `FRAME_NO` are all empty → early `Output{200,"success"}` (nothing to validate).
  - `FRAME_NO` must be 17 chars for warranty issue mode, else *"Issue Mode -Warranty cannot be selected…"*.
  - Old-vehicle guard blocks Warranty/SupplierWarranty/Transit/RecallRefit modes.
  - MCS mode requires the vehicle/part to be ZMC-eligible.

### 8.4 Business tier (BL)
- Cross-entity rules (eligibility windows, KM/age bands, scheme applicability, tax correctness) live in the `*BL` classes and are the authoritative business validation (see §10).

### 8.5 Data tier (DAL / DB)
- Typed `SqlParameter`s (`AddParameterToSQLCommand` with `SqlDbType`) prevent type-mismatch and provide a parameterization boundary.
- Stored procedures perform set-based integrity checks and return status via output params (e.g. `@RESULT`) or sentinel rows; DAL surfaces these to the BL.

> The validation + error decision paths are visualized in [Validation & Error Flow](../diagrams/lld-validation-error-flow.md).

---

## 9. Error Handling

### 9.1 Tier-by-tier behaviour

| Tier | Mechanism |
|---|---|
| Angular | RxJS `tap`/error callbacks; `ToastrService` surfaces messages; HTTP/token errors trigger `loginService.logout1()`. Components branch on `body.statusCode`. |
| APIM | `validate-jwt` failures → `401` at the edge before the backend is hit. |
| Auth filters | Return the `Output` envelope (or `HttpResponseMessage`) with `statusCode = 401` and a clear message; pipeline short-circuits. |
| Controllers | `try/catch` around the action body; on exception, log via `LogGeneration` and return `Output{500, message}`. Business rule failures return `Output{500, "<reason>"}` without throwing. |
| Business Layer | Catches and rethrows or converts to result codes; logs context via `LogGeneration`. |
| Data Layer | `DALHelper` wraps every operation; SQL errors are rethrown as `ApplicationException("Error occured while calling DataAccess:...", ex)` preserving the inner exception. Transactions roll back on error. |
| Deadlocks | `DeadlockRetryHelper.Execute(action)` retries SQL error `1205` up to 3× with `Thread.Sleep(100 * retries)` back-off; non-deadlock exceptions are logged and rethrown. |

### 9.2 Logging — `MicroDMS.ExceptionManager.LogGeneration`

`LogGeneration` is the single logging entry point used across BL/DAL. It exposes:

- **OTel delegate hooks** — `OTelWriteInfo/Warning/Error/Debug/Exception` static `Action`s wired at startup (`Global.asax`) to `LogGenerationOTel`. `LogInfo/LogWarning/LogError/LogDebug` route through these delegates when set, otherwise fall back to file logging.
- **File logging** — `WriteToFile(string|Exception)` writes to a per-session file (name from session key configured by `LogFileNameSession`), stamped with `DealerID`, `BranchID`, `UserID`, `CountryCode`, `LoginId`, timestamp.
- **Specialized log files** — dedicated writers for high-signal flows: `WriteToFileJC` (job card), `WriteToFileDI` (direct invoice), `WriteToFileCWI`/`WriteToFileCWIAMC`/`WriteToFileCWIATW`, `WriteToFileEMSWebhook`, `WriteToFileRedisLog`, `WriteToFileJCCancelled`, `WriteToFileJCStatus`, `WriteToFileDIF`, `WriteToFileWebServiceLog`. These write date-stamped files under `~/LogFiles`.

### 9.3 Observability pipeline
- `LogGenerationOTel`, `OtelActivityModule`, `TraceContextLogProcessor` export structured logs and traces over OTLP; the `traceparent` is attached so logs correlate to spans.
- Application Insights runs in parallel (`ApplicationInsights.config`).
- A telemetry **kill switch** (`OTEL_ENABLED=false`) disables OTel exports without code change.

### 9.4 Error surfacing to clients
- The API returns errors **inside the `Output` body** (`statusCode` 401/500 + `message`), usually with HTTP 200. With `IncludeErrorDetailPolicy = Always`, unhandled exceptions include diagnostic detail — useful in non-prod, but vendors should confirm this is restricted/scrubbed in production hardening.

> Error/validation paths are mapped in [Validation & Error Flow](../diagrams/lld-validation-error-flow.md).

---

## 10. Key Algorithms / Business Rules

The business logic is concentrated in controllers' inline guards and `*BL` classes. The most intricate rules are in the service/warranty domain.

### 10.1 Spare-part warranty / issue-mode eligibility (`JobCardController.CheckPartClaim`)

Determines whether a spare can be issued under a given **issue mode** (Warranty, ExtendedWarranty, MCS, SupplierWarranty, Transit, RecallRefit, Paid, etc.). Inputs are enriched from `GetSparePartForIssueMode` (warranty flags, KM bands, wear-and-tear config). Core rules:

- **Frame number** must be exactly 17 chars for warranty modes.
- **Old vehicle** → Warranty/SupplierWarranty/Transit/RecallRefit are blocked.
- **MCS (ZMC)** → only allowed when the vehicle and part are ZMC-eligible (`MCS_TYPE_ID > 0`, `IS_ZMC`).
- **Warranty window by category** (motorcycle `00001`, scooter `00003`/`00004`, moped `00002`), keyed on **days since sale** and **kilometers**:
  - Motorcycle: standard warranty < 1095 days & < 30,001 km; extended-warranty band 30,001–60,000 km / up to 1825 days.
  - Scooter: standard < 1095 days & < 24,001 km; extended band 24,001–50,000 km.
  - Moped: standard < 730 days & < 12,001 km; extended band 12,001–36,000 km.
  - **Wear-and-tear parts** (`IS_WEAR_TEAR`) use part-specific `FROM_KM`/`TO_KM`/`NO_OF_VALID_DAYS` instead of the category band.
- **Model-specific overrides** — specific `MODEL_ID`s (e.g. Max/Scooty variants) get 365-day vs 730-day TVS warranty end dates, adjusted by config `IssueSpareOneYrExtraDays` / `IssueSpareTwoYrExtraDays`.
- **3W (`COUNTRY_CODE == "3W"`)** uses a distinct rule set (model-specific day/KM ceilings, e.g. 540 days/72,000 km or 730 days/100,000 km) and a post-2024-01-01 branch.
- **CWI extended warranty** (`IS_CWI_EXT_WARRANTY`) can override expiry blocks.

On any failed rule the method returns `Output{500, "<specific reason>", data = 0}`.

### 10.2 Tax computation (`CentralTaxProcessor`)
Centralizes GST split (CGST/SGST/IGST/UTGST) for invoices and claims. The invoice tax pivot (`ListToPivotConverter` + `PivotExtension.PivotTable`) transforms line-item tax rows into a per-rate pivot used in invoice printing (`A110JcInvoiceDO` by `INVOICE_NO` × `TAX_RATE`).

### 10.3 Claim posting (ASC Warranty example)
`ASCWarrantyClaimDAL` builds a header+detail **XML payload** (`<ASCWARRANTY><HEADER>…</HEADER><DETAILS>…</DETAILS></ASCWARRANTY>`) using the node-name constants in `DALConstants`, and passes it to `pr_Save_ASCWarranty` / `pr_Modify_ASCWarranty`. Status transitions go through `pr_UpdateASCWarrantyClaimStatus`. Stock for issue-to-ASC is updated via `pr_UpdateStockForIssueToASC` (fails with sentinel when free stock is 0).

### 10.4 Deadlock-safe posting
High-contention writes (stock/inventory updates) are wrapped in `DeadlockRetryHelper.Execute(...)` — retry SQL `1205` up to 3× with incremental back-off, otherwise log and rethrow.

### 10.5 Paging
List/search procs accept paging params and an output `@totalRows`; `DALHelper.ExecDataSetPagewise` fills the dataset and returns the total count for client-side pagination.

---

## 11. Configuration Handling

### 11.1 Backend configuration

| Source | Contents |
|---|---|
| `Web.config` / `Web.Release.config` / `Web.Debug.config` | `appSettings` (feature flags, OTel settings, warranty day adjustments, log-file session keys, JWT issuer/audience/signing-key *names*), `connectionStrings` (`DMSConnection`, `OracleSQLPortal`). Release/Debug transforms apply per environment. |
| `ConfigSettings.cs` / `ProjectConstants.cs` | Strongly-typed access to settings and shared constants (e.g. `sCountryCode3W`). |
| `MicroDMS.ConfigHelper` | Reusable typed config readers shared across projects. |
| `ApplicationInsights.config` | App Insights instrumentation. |
| `DALConstants` (`DeadLockRetryHelper.cs`) | Stored-proc names, param names, XML node names, default values. |
| `DMSFunctionApp/host.json` + `local.settings.json` | Function host + Service Bus connection (local settings not committed). |

Representative app-setting keys referenced by code (values are environment-specific and **not** shown here):
- `IssueSpareOneYrExtraDays`, `IssueSpareTwoYrExtraDays` — warranty window adjustments.
- `InvoiceCancelValidIssuer`, `InvoiceCancelValidAudience`, `InvoiceCancelIssuerSigningKey` — JWT validation for invoice-cancel flow.
- `LogFileNameSession` — session key holding the per-session log file path.
- `OTEL_ENABLED`, `OTEL_BSP_*` — OpenTelemetry enable/kill-switch and batch-processor tuning.

### 11.2 Connection string selection
`DALHelper` chooses the connection string by `SQLConnectionType` enum: `SqlOnlineDMS → DMSConnection` (default, SQL Server) or `SqlOraclePortal → OracleSQLPortal` (Oracle bridge). `SqlCommand.CommandTimeout` is `40000`.

### 11.3 Secret hygiene (mandatory)
- JWT signing keys (`RSAKeys/`), SAP/Oracle credentials, APIM subscription keys, SendGrid/SMS provider keys, and connection strings **must** be sourced from KeyVault / encrypted config (`aspnet_regiis -pe` for config sections) and **never committed**.
- This document references all such values by **key name only**.

### 11.4 Frontend configuration

| Source | Contents |
|---|---|
| `src/environments/environment.ts` + `environment.<env>.ts` | API base URLs (APIM), UMS URLs (`umsLogin`, `umsLogin_WebApi`, `umsLogout`), feature flags, analytics keys. |
| `angular.json` `fileReplacements` | Per-environment env file swap at build time. |
| `package.json` scripts | `build`, env-specific builds, `ele-build` (Electron packaging). |

---

## 12. TVS LLD Template Sections

> Mapped to the [TVS LLD Template](https://tvsmotorcompany.atlassian.net/wiki/spaces/DE2/pages/4209606912/Low+Level+Design+Template). Sections above provide the implementation detail; this section provides the template-aligned summary.

### 12.1 Document Control
| Field | Value |
|---|---|
| Document | DMS Domestic — Low Level Design |
| Version | 1.0 |
| Status | Draft for vendor onboarding |
| Source | `ANGULAR_DMS` + `OnlineDMS_WebAPI` |
| Related | [HLD](./HLD.md), [HLC](./HLC.md) |

### 12.2 Introduction & Scope
Implementation-level design of the DMS Domestic Angular SPA and `OnlineDMS_WebAPI`. Covers module breakdown, class responsibilities, API flows, DB usage, request lifecycle, validation, error handling, business rules and configuration. Excludes secrets and the legacy Web Forms internals (referenced only).

### 12.3 Design Overview
Layered architecture: Angular SPA → APIM (`validate-jwt`) → Web API (controllers + filters + Unity DI) → BusinessLayer → DataLayer → SQL Server / Oracle, with an async leg via Service Bus → `DMSFunctionApp`. See [Component Interaction](../diagrams/lld-component-interaction.md).

### 12.4 Detailed Component Design
See §2–§3 (module breakdown, class responsibilities) and [Class Diagram](../diagrams/lld-class-diagram.md).

### 12.5 Interface / API Design
See §4 (routing, `Output` envelope, representative flows, auth per endpoint family). API specification is maintained per `.kiro/steering/API_SPEC.md`.

### 12.6 Data Design
See §6 — stored-procedure-based access, logical entity groups, proc/param conventions. See [Database Schema](../diagrams/lld-database-schema.md).

### 12.7 Process / Sequence Design
See §7 and [Request / Response Lifecycle](../diagrams/lld-request-response-lifecycle.md).

### 12.8 Validation & Error Handling
See §8–§9 and [Validation & Error Flow](../diagrams/lld-validation-error-flow.md).

### 12.9 Business Rules
See §10 (warranty/issue-mode eligibility, tax, claims, deadlock-safe posting, paging).

### 12.10 Configuration & Environment
See §11.

### 12.11 Assumptions, Risks & Constraints
- .NET Framework 4.7.2 + Angular 6 — modernization pending; ecosystem in maintenance mode.
- Business outcomes encoded in `body.statusCode` (not HTTP status) — clients must branch on it.
- `IncludeErrorDetailPolicy = Always` should be reviewed for production hardening.
- Dual-store (SQL + Oracle) introduces cross-store consistency edge cases.
- Very large controllers (e.g. `JobCardController`) concentrate logic that belongs in BL — refactor candidate.

---

## Appendix

### Glossary
- **DO / DTO** — Data Object / Data Transfer Object (`*DO` in `BusinessEntities`).
- **BL** — Business Layer class (`*BL`, `*Fun`).
- **DAL / DH** — Data Access Layer class / Data Helper.
- **MDP** — Master Data Platform schema (`*_MDP_DMS_DAL`).
- **APIM** — Azure API Management. **UMS** — User Management System (Azure AD B2C). **ASC** — Authorized Service Centre. **GRN** — Goods Receipt Note. **FSC** — Free Service Coupon. **AMC** — Annual Maintenance Contract. **ATW/ATP/NGD/EMS/CWI** — partner integrations. **ZMC/MCS** — manufacturing/service campaign eligibility. **3W** — three-wheeler country code.

### Diagram index
| Diagram | File | Referenced from |
|---|---|---|
| Class Diagram | [`diagrams/lld-class-diagram.md`](../diagrams/lld-class-diagram.md) | §2.3, §3 |
| Request / Response Lifecycle | [`diagrams/lld-request-response-lifecycle.md`](../diagrams/lld-request-response-lifecycle.md) | §4.3, §7 |
| Database Schema | [`diagrams/lld-database-schema.md`](../diagrams/lld-database-schema.md) | §6 |
| Validation & Error Flow | [`diagrams/lld-validation-error-flow.md`](../diagrams/lld-validation-error-flow.md) | §8, §9 |
| Component Interaction | [`diagrams/lld-component-interaction.md`](../diagrams/lld-component-interaction.md) | §2.1, §5 |

### References
- [TVS LLD Template](https://tvsmotorcompany.atlassian.net/wiki/spaces/DE2/pages/4209606912/Low+Level+Design+Template)
- Source repos: `D:\DMS_DOMESTIC\ANGULAR_DMS`, `D:\DMS_DOMESTIC\MICRO_DMS\MicroDMS\OnlineDMS_WebAPI`

---

_Source: ANGULAR_DMS + OnlineDMS_WebAPI_
