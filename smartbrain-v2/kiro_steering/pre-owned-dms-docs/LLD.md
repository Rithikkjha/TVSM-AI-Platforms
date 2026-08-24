# Low Level Design (LLD) — PreOwnedDMS (UVD)

> Restored from Confluence: https://tvsmotorcompany.atlassian.net/wiki/pages/viewpage.action?pageId=5268897897

**Audience:** New engineering vendors / implementation partners. **Scope:** the `PreOwnedDMS` solution (`UVD.sln`) — the Used-Vehicle Dealership (UVD) platform. **Template:** follows the D&AI Low Level Design Template. **Confidentiality:** no secrets/credentials reproduced; integration auth described by config key name only.

## Overview

This LLD describes the **implementation-level** design of PreOwnedDMS — the used-vehicle dealer-management Web API. It lets a new vendor understand how a request travels through the layers, how classes are arranged, and how data access, validation, and error handling work, using concrete examples (Purchase Order / Procurement). It complements the HLD with class, method, and flow detail.

## High Level Design — Quick Recap

Stateless **ASP.NET Web API 2 (OWIN)** in an N-tier layout: `UVD` (controllers) → `UVD.BLL` (business services) → `UVD.DAL` (ADO.NET + stored procedures) → **SQL Server**, with `UVD.VM` (contracts), `UVD.Helper` (cross-cutting), and the shared `MicroDMS.*` core. See the HLD page in this space (`HLD-PreOwnedDMS-UVD.md`).

## Assumptions

- All transactional data access is via **stored procedures**; no ORM on transactional paths (EntityFramework only backs ASP.NET Identity).
- APIs sit behind a TLS-terminating load balancer; clients send an OAuth2 **bearer** token on every call.
- SQL Server runs as an **AlwaysOn AG** (primary + read-only replica); connection strings are environment-provided.
- Multi-tenancy is enforced per request by `dealerId`/`branchId`/`userId` scope checks.

## 1. Detailed Module Breakdown

![Module / Class Design](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5268897897/child/attachment/att5273714769/download)

| Project | Type | Responsibility | Representative members |
| --- | --- | --- | --- |
| `UVD` | ASP.NET Web API 2 | HTTP endpoints, routing, auth, OWIN startup | `*Controller : ApiController`, `App_Start/*`, `Startup.Auth` |
| `UVD.BLL` | Class library | Business logic + integration orchestration | `PurchaseOrderBusinessService`, `ProcurementBusinessService`, `SalesOne/TwoBusinessService`, `IDPService`, `SAPAccessoriesService`, `EmailService` |
| `UVD.DAL` | Class library | ADO.NET data access (stored procedures) | `*DataAccess`, `DbConnector`, `DataAccessLayerBaseClass`, `DataAccessLayerFactory` |
| `UVD.VM` | Class library | Request/response contracts | `RequestVM*`, `ResponseVM*`, `CodeMessage`, `OutputResult` |
| `UVD.Helper` | Class library | Cross-cutting helpers | `Validator`, `ExceptionLogging`, `Encryptor`, `ReUsableEnum` |
| `MicroDMS.*` | Shared core | Domain entities, shared BL/DAL, tax processors | `*DO`, `*BL`, `*DAL`, `DeadLockRetryHelper` |

## 2. Class / Service Responsibilities

**Controller (e.g. `PurchaseOrderController`):** `[RoutePrefix("PurchaseOrder")]`; actions use `[HttpGet]`/`[HttpPost]`, `[Route]`, `[Authorize]`, `[SwaggerResponse]`. Holds `CodeMessage`, `ExceptionLogging`, `Validator`, the relevant `*BusinessService`, and `SettingController` (for `ValidateToken`). Per action: authorize → validate input → `await` business service → `Request.CreateResponse(...)`.

**Business service (methods prefixed `BLL…`):** business rules + orchestration; calls `*DataAccess` and integration services (`IDPService`, `SAPAccessoriesService`, `EmailService`).

**Data access (methods prefixed `DAL…`):** executes stored procedures, returns `DataSet`/`DataTable` or mapped objects.

**Helpers:** `Validator` (per-request boolean validation), `ExceptionLogging` (file logger), `ReUsableEnum` (status enums).

## 3. API Design & Flow Details

REST/JSON over Web API 2. Example endpoints on `PurchaseOrderController`:

| Method | Route | Input | Output (Swagger type) |
| --- | --- | --- | --- |
| GET | `PurchaseOrder/purchaseOrderTypeList` | `dealerId`, `countryCode` | `ResponseVMPurchaseOrderMasterDetails` |
| POST | `PurchaseOrder/getVendorList` | `dealerId`, `orderType`, `countryCode` | `ResponseVMPOVendorList` |
| POST | `PurchaseOrder/getPurchaseOrderList` | `RequestVMListOfPurchaseOrder` | `ResponseVMPuchaseOrderList` |
| GET | `PurchaseOrder/getViewPurchaseOrder` | `dealerId`, `branchId`, `SparePOId` | `ResponseVMPOView` |
| POST | `PurchaseOrder/cancelPO` | `dealerId`, `branchId`, `vendorId`, `sparePOId`, `orderType` | `ResponseVMCancelPO` |
| POST | `PurchaseOrder/confirmPO` | `RequestVMSparePOConfirm` | `CodeMessage` |

**Status codes:** `200`, `400`, `401`, `406` (uploads), `500`. **Idempotency:** GETs are idempotent; writes (e.g. `confirmPO`) are guarded by server-side PO status checks + an outbox/correlation pattern for POMS publishing so retries don't double-publish. No client-supplied idempotency key.

## 4. Internal Component Interactions & Request/Response Lifecycle

![Request Lifecycle](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5268897897/child/attachment/att5273976838/download)

1. Client sends HTTPS request with `Authorization: Bearer <token>` and a `RequestVM*` body.
2. OWIN validates the bearer token; controller calls `ValidateToken((ClaimsIdentity)User.Identity)` for dealer/branch/user scope.
3. Controller runs input validation (`validate.<Rule>(reqObj)` or inline guards).
4. On success it `await`s the business service (`pobs.BLL…`).
5. Business service calls `*DataAccess`, which executes a stored procedure.
6. Results return as `DataSet`/`DataTable`, mapped to `ResponseVM*`/`*DO`, and bubble back up.
7. Controller returns `Request.CreateResponse(HttpStatusCode.OK, result)` as JSON.

**Envelopes:** `CodeMessage` (`statusCode`, `statusMessage`, `documentId`, `documentNo`), `OutputResult` (`statusCode`, `message`, `data`), and typed `ResponseVM*`.

## 5. Database Schema Usage

![Data Access](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5268897897/child/attachment/att5273583755/download)

- **Two data-access styles coexist** in `UVD.DAL`: **Style A** (`DbConnector` + `SqlCommand`/`SqlDataAdapter.Fill`, connections closed in `finally`) and **Style B** (`DataAccessLayerFactory.GetDataAccessLayer()` → `AddParameterToSQLCommand` → `RetrieveDataIntoCollection`/`ReturnSingleDataObject`/`ExecScalar`).
- **Stored procedures only** for transactional paths. Examples: `UVD_GetBusinessTypeSettings`, `pr_getSparePartforPO`, `pr_getSpareCostDetailsForSparesPO`, `UVD_GetMonthlyAverageConsumptionForPart`.
- **Connections (key names only):** `UVDDbConnection` (primary), `DMSConnection`, `DMSConnReport` (reporting).
- **Result mapping:** `DataTable.AsEnumerable().Select(row => new ResponseVM*/DO { COL = row.Field<T>("COL") })`.
- **Resiliency:** `Pooling=True`, `Max Pool Size=2500`, tuned timeout, `ApplicationIntent=ReadOnly` for reports, `MultiSubnetFailover=True`; `DeadLockRetryHelper` for deadlock-prone operations.

Table/column names are owned by the database (stored procedures); the app binds to result-set column names. No schema DDL is managed in this repository.

## 6. Validation Logic

`UVD.Helper.Validator` exposes one boolean method per request type; the controller returns `400` when it returns `false`. Pattern: explicit field guards (`== 0`, `== null`, `string.IsNullOrEmpty`, allowed-value checks).

- `CreateProcurement` — requires dealer/branch/company/enquiry keys, non-empty customer name/city/mobile/address/state, `areaId`, `brandId`, `modelId`, `manu_year`, `partId`, `runningKMS`, `hpEndorsement`.
- `validateConfirmPO` — requires dealer/branch, non-empty country code, PO id/no, company, vendor, order type, `modifiedBy`, non-empty `SparesPODetails`, and per-line `spare_PO_DET_Id` unless the row is newly created (`RowState.Created`).
- `ValCreateSalesInvoice` — validates header keys, `TOT_AMT > 0`, single-unit part (`QTY == 1`), and at least one GST component + percentage present.

Some controllers use **inline guards** instead of `Validator` (e.g. `dealerId > 0 && countryCode != ""`).

## 7. Error Handling & Retries

![Error / Validation Flow](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5268897897/child/attachment/att5273550952/download)

- **Pattern:** every action body is wrapped in `try/catch`. On exception: set `MethodName`, `ErrLog.ErrorLogging(ex, MethodName)`, `500` `CodeMessage`.
- **Client errors:** `400` (validation), `401` (auth/scope), `406` (unsupported upload type).
- **Logging:** `ExceptionLogging` writes to `~/LogFiles/UVD-App-Error.txt` (method, message, inner, stack, timestamp); `DataLogger` gated by `EnableLogging`.
- **Retries / failover:** SQL AG failover via `MultiSubnetFailover`; `DeadLockRetryHelper`; TLS 1.2 for integrations; non-critical notifications isolated from the primary transaction; **POMS publish** paginates (size 250) with a per-page `try/catch` calling `BLLUpdatePOStatus` on failure.

**Security finding (to fix):** in `PurchaseOrderController.ConfirmPO`, the POMS failure branch appends POMS endpoint/ID/password app-setting values into the `500` message, leaking credentials to the client/logs. Remove secret values from error messages and move them to a secret store. (Values are not reproduced here.)

## 8. Key Algorithms / Business Rules

![Confirm PO Flow](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5268897897/child/attachment/att5273813037/download)

**ConfirmPO routing:** (1) validate via `validateConfirmPO` → `400` if invalid. (2) `pobs.btnConfirm(regObj)`; proceed only if `statusCode == 200`. (3) branch by vendor/order type — **SRICHAKRA** calls external vendor Sale Order API (message depends on DBR-code mapping); **StockOrder + IS_POMS_ENABLED** computes `pageCount = ceil(lineItems / 250)`, saves IDP header, then loops pages saving line items, inserting an outbox correlation id, and calling `IDPService.BLLPublishDatatoPOMSAsync`; **other** vendors do standard confirmation. (4) return `200` with a status message.

**Status enums** (`ReUsableEnum`): Procurement, Refurbishment, JobCard, Sales (Opened/Blocked/Sold/Delivered), Vehicle (InStock/Blocked/Sold). **Valuation:** combines configured city/age base price with the Orange Book Value system-suggested price.

## 9. Configuration Handling

- Read at runtime via `ConfigurationManager` (`AppSettings` / `ConnectionStrings`).
- **Connection strings (key names):** `UVDDbConnection`, `DMSConnection`, `DMSConnReport`.
- **Integration keys (names only):** `OBVPriceUrl`/`OBVToken`, `POMSTokenEndPoint`/`POMSID`/`POMSPassword`, `sap_token_url`/`sap_client_id`/`sap_client_secret`, `AzureTokenGenURL`/`AzureTokenGenCode`, `SMTPHost`/`SMTPPort`/`SMTPUserID`, `SMS1`/`SMS2`/`SMS3`, `WebUri`.
- **Flags:** `OTEL_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, `EnableLogging`, `IS_POMS_ENABLED`, `isAutomationRequest`.
- **Tax/business config:** `GSTDate`, `TCS*`, `CentralTaxDate`, `KFCDate`.

**Configuration risk:** the inspected `Web.config` contains live connection strings, an OBV token, an SMS gateway password, and AG endpoints in source control. Externalize to a secret store (e.g. Azure Key Vault) and rotate exposed values.

## 10. Security & Compliance

- **In transit:** HTTPS/TLS at the edge; integrations force TLS 1.2.
- **AuthN/Z:** OWIN OAuth2 bearer tokens (`/Token`, 1-day expiry) + per-request `ValidateToken` scope checks. `AllowInsecureHttp=true` in the inspected config should be `false` in production.
- **PII:** customer name/contact/address in procurement/sales — keep out of logs/responses where not required.
- **Token management:** integration tokens fetched on demand per call/session; never persist or log token values.

## RBAC

Endpoints require an authenticated bearer principal; `roleId` is read from claims (e.g. `getPrintPO`). Fine-grained menu/permission data is served by the masters/menu module — confirm the role→permission matrix with the product owner before onboarding.

## Configuration Rules & Feature Flags

| Flag / key | Effect |
| --- | --- |
| `IS_POMS_ENABLED` | Enables POMS publishing branch on PO confirm |
| `isAutomationRequest` | Bypasses interactive token check for automation callers |
| `OTEL_ENABLED` | Toggles OpenTelemetry logger initialization |
| `EnableLogging` | Toggles verbose `DataLogger` output |

## Dependencies

**Internal:** shared `MicroDMS.*` libraries. **External:** SAP, POMS/IDP, Orange Book Value, Azure, Extentia, SMTP, SMS, dealer portal. **Runtime:** ASP.NET Web API 2, OWIN, ASP.NET Identity, Newtonsoft.Json, RestSharp, Swashbuckle, EPPlus/OpenXml, PdfSharp, EntityFramework (Identity only).

## Trade-offs & Alternatives Considered

- **Two DAL styles** (DbConnector vs DataAccessLayerFactory) coexist; recommend standardizing on one.
- **Stored procedures vs ORM:** SPs chosen for performance/consistency; trade-off is more boilerplate and DB-owned logic.
- **Bearer token vs session:** bearer chosen for stateless scale-out.

## Open Questions

- Should the two DAL styles be unified, and on which one?
- Confirm the canonical RBAC role→permission matrix for external partners.
- Timeline for secret externalization and removal of secrets from error messages/config.
