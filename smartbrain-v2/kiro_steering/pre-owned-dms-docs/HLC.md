# PreOwnedDMS (UVD) — High Level Code Document (HLCD)

> Restored from Confluence: https://tvsmotorcompany.atlassian.net/wiki/pages/viewpage.action?pageId=5282398269

**Audience:** Vendor onboarding / new engineering partners. **Scope:** the `PreOwnedDMS` solution (`UVD.sln`) — the Used-Vehicle Dealership (UVD) platform within the TVS Motor DMS ecosystem. Architecture diagrams are generated from `docs/diagrams/gen_diagrams.py`.

## 1. Application Overview

PreOwnedDMS (internally **UVD** — Used Vehicle Dealership) is the dealer-management platform for **pre-owned / used two- and three-wheeler vehicles**. It supports the full second-hand vehicle lifecycle for TVS Motor dealerships:

- **Procurement** of used vehicles (enquiry, valuation, checklist, documents, follow-up).
- **Refurbishment** of acquired vehicles (job allocation and completion).
- **Resale** of refurbished vehicles to customers (enquiry, blocking, sale order, invoice, self-financing/HP).
- **After-sales service, spare parts, accessories, and accounting** surrounding the used-vehicle business.

It is delivered as a **stateless ASP.NET Web API 2** backend consumed by mobile applications and a dealer web portal. The platform is multi-tenant by **dealer** and **branch**, with most operations scoped by `dealerId` / `branchId` and authorized via OAuth bearer tokens.

| Attribute | Detail |
| --- | --- |
| Solution | `UVD.sln` (Visual Studio 2019, format 16) |
| Application type | RESTful Web API (HTTP/JSON) |
| Platform | .NET Framework (4.5.2 / 4.6.1), ASP.NET Web API 2, OWIN |
| Primary datastore | Microsoft SQL Server (stored-procedure driven) |
| Auth | OWIN OAuth 2.0 bearer tokens (`/Token`), ASP.NET Identity |
| API docs | Swagger / Swashbuckle |
| Observability | File-based exception logging + OpenTelemetry (OTel) hooks |

**Architecture at a glance**

![Layered Architecture](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5282398269/child/attachment/att5282398293/download)

## 2. Module Summary

The solution is organized as a classic **N-tier** set of projects plus shared libraries reused from the core MicroDMS product.

| Project | Role | Notes |
| --- | --- | --- |
| **UVD** | Web API host (entry layer) | Controllers, OWIN startup, OAuth, Swagger, filters, request logging |
| **UVD.BLL** | Business logic | `*BusinessService` classes; orchestration, integrations, tax/pricing rules |
| **UVD.DAL** | Data access | ADO.NET + stored procedures; `DbConnector`, `DataAccessLayerFactory` |
| **UVD.VM** | View models | `Request/` and `Response/` DTOs, plus `Common` (`CodeMessage`, `OutputResult`) |
| **UVD.Helper** | Cross-cutting helpers | `ExceptionLogging`, `Validator`, `Encryptor`, reusable enums |
| **MicroDMS.BusinessEntities** | Shared domain entities | `*DO` data objects shared with the core DMS |
| **MicroDMS.BusinessLayer** | Shared business logic | Reused masters, tax processors, account posting |
| **MicroDMS.DataLayer** | Shared data access | Shared stored-procedure access + `DataAccessLayerFactory` |

**Functional modules (vertical slices)**

![Module Map](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5282398269/child/attachment/att5282398290/download)

- **Procurement & Valuation** — `ProcurementController` → `ProcurementBusinessService` → `ProcurementDataAccess`; valuation via `VehicleValuationController` and Orange Book Value pricing.
- **Refurbishment** — `RefurbishmentController` → `RefurbishBusinessService` → `RefurbishDataAccess`.
- **Sales** — `SalesController` → `SalesOneBusinessService` / `SalesTwoBusinessService`.
- **Service & Warranty** — `ServiceController`, `JobCardController`, `ReminderAndAppointmentController`.
- **Spare Parts** — part master/help, stock, GRN, purchase orders, pick-slip invoice, sale order, returns.
- **Accessories** — `AccessoryGRNController`, `SparePartAMDController`, SAP accessory ordering.
- **Accounts** — vouchers, ledger, bank & CN/DN reconciliation, tracking payments.
- **Masters & Settings** — DMS masters, vendor, employee, labour, themes, menu/RBAC.
- **Portal & Web Order** — `PortalController`, `WebOrderController`, `ReferralVehicleController`, `ExtentiaController`.

## 3. Folder Structure

```text
PreOwnedDMS/
├── UVD.sln                        # Solution entry point
├── UVD/                           # ASP.NET Web API host (entry layer)
│   ├── App_Start/                 # WebApiConfig, Startup.Auth, FilterConfig, RouteConfig, SwaggerConfig
│   ├── Controllers/                # ~40 API controllers (one per functional area)
│   ├── Models/ Providers/ Results/ # Identity/OAuth models, providers, custom results
│   ├── Document/ Content/ Scripts/ # Uploaded docs + static assets
│   ├── Global.asax.cs             # App bootstrap + OTel init
│   ├── Startup.cs                 # OWIN entry point
│   └── Web.config                 # Connection strings + appSettings (integration endpoints)
├── UVD.BLL/                       # Business services (*BusinessService.cs)
├── UVD.DAL/                       # Data access (*DataAccess.cs, DbConnector, SqlDataAccess)
├── UVD.VM/                        # Request/ + Response/ view models + Common/
├── UVD.Helper/                    # ExceptionLogging, Validator, Encryptor, ReUsableEnum
├── MicroDMS.BusinessEntities/     # Shared domain data objects (*DO.cs)
├── MicroDMS.BusinessLayer/        # Shared business logic (*BL.cs, tax processors)
├── MicroDMS.DataLayer/            # Shared data access (*DAL.cs)
├── packages/                      # NuGet packages (packages.config style)
└── docs/diagrams/                 # Architecture diagram source + generated PNGs
```

**Naming conventions:** Controllers `XxxController.cs`; business services `XxxBusinessService.cs` (methods prefixed `BLL…`); data access `XxxDataAccess.cs` (methods prefixed `DAL…`/`DLL…`); view models `RequestVMXxx` / `ResponseVMXxx`; shared entities `XxxDO`.

## 4. Core Business Workflows

### 4.1 Procurement → Refurbishment → Resale

1. Procurement enquiry captured (`ProcurementController.CreateProcurement`).
2. Valuation performed — base price by city/age plus system-suggested price from the **Orange Book Value** API (`getOBVPrice`).
3. Checklist & documents recorded; follow-ups scheduled.
4. Vehicle procured (status tracked via `UVDProcurementStatus`).
5. Refurbishment job cards allocated and completed (`UVDRefurbishmentStatus`).
6. Vehicle enters stock (`vehicleStatus.InStock`) and becomes available for sales.
7. Sales: enquiry → block → sale order → sales invoice; optional self-HP. Status via `SalesStatus` (Opened → Blocked → Sold → Delivered).

### 4.2 Spare-parts procurement (PO → GRN → Stock)

1. Spare Purchase Order created and confirmed (`PurchaseOrderController`).
2. PO data published to POMS/IDP for stock orders (`IDPService.SendPODataToPOMS`).
3. GRN received against the PO (`SparePartGRNController`).
4. Stock updated; parts available for pick-slip invoice / sale order / returns.
5. PO confirmation triggers email notifications to dealers (`EmailService.PushPOGenerationEmail`).

### 4.3 Status model (representative enums)

| Domain | States |
| --- | --- |
| Procurement | Closed, Opened, ValuationDone, Procured, PartialPayment, FullPayment |
| Refurbishment | UnAllocated, Allocated, Completed, Closed, YetToStart |
| Job Card | UnAllocated, Allocated, Suspended, Cancelled, Invoiced, JobComplete, Closed |
| Sales | Opened, Blocked, Sold, Delivered |
| Vehicle | InStock, Blocked, Sold |

*Detailed tax, pricing, and financial-posting rules are intentionally summarized and not reproduced in this onboarding document.*

## 5. Key Services / Classes

| Layer | Class | Responsibility |
| --- | --- | --- |
| Entry | `Startup` / `Startup.Auth` | OWIN bootstrap; OAuth bearer flow (`/Token`) |
| Entry | `WebApiConfig` | Routing, JSON formatting, host-auth filter |
| Entry | `Global.asax` | App start, registration, OTel init, CORS preflight |
| BLL | `ProcurementBusinessService` | Procurement, valuation, follow-up orchestration |
| BLL | `SalesOne/TwoBusinessService` | Sales enquiry → invoice lifecycle |
| BLL | `SparePart*` / `PurchaseOrder*` | Parts master, stock, GRN, purchase orders |
| Integration | `SAPAccessoriesService` | OAuth client-credentials call to SAP |
| Integration | `IDPService` | POMS/IDP token + spare-PO publish |
| Integration | `AzureBusinessService` | Azure token generation |
| Integration | `ExtentiaBusinessService` | Master-data sync (SHA-512 hash-token auth) |
| Integration | `EmailService` | SMTP email (PO notifications) |
| Cross-cutting | `ExceptionLogging`, `Validator`, `DbConnector` | Logging, validation, DB connection + ADO.NET |

## 6. Integration Summary

![Integration Context](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5282398269/child/attachment/att5282398284/download)

| Integration | Direction | Purpose | Auth pattern (key names only) |
| --- | --- | --- | --- |
| **SAP** | Outbound | Accessory order creation / posting | OAuth client-credentials (`sap_token_url`, `sap_client_id`, `sap_client_secret`) |
| **POMS / IDP** | Outbound | Publish spare purchase orders | Login token (`POMSTokenEndPoint`, `POMSID`, `POMSPassword`) + `X-Client-Id` |
| **Orange Book Value** | Outbound | Used-vehicle valuation pricing | API token (`OBVToken`, `OBVPriceUrl`) |
| **Azure Services** | Outbound | Token generation + storage | Function code header (`AzureTokenGenURL`, `AzureTokenGenCode`) |
| **Extentia** | Inbound | Master-data sync | SHA-512 daily hash token |
| **SMTP Email** | Outbound | PO / notification emails | `SMTPHost`, `SMTPPort`, `SMTPUserID`, `EmailFrom` |
| **SMS Gateway** | Outbound | OTP / transactional alerts | URL-keyed gateway (`SMS1`/`SMS2`/`SMS3`) |
| **Dealer Web Portal** | In/Out | Parts-order feeds, referral vehicles | Bearer token |

**Security note:** All endpoints, credentials, and keys are sourced from `Web.config` at runtime. This document references **configuration key names only** — no secret values. Several keys currently hold environment-specific values in source control; treat these as tech debt and migrate to a secret store (e.g. Azure Key Vault) during onboarding.

## 7. Dependency Overview

| Category | Library | Used for |
| --- | --- | --- |
| Web framework | ASP.NET Web API 2 (5.2.x) | REST endpoints |
| Hosting / auth | OWIN 3.0.1, ASP.NET Identity 2.2.1, OAuth bearer | Token auth |
| Serialization | Newtonsoft.Json 12.x | JSON (de)serialization |
| HTTP clients | HttpClient, RestSharp 106.x | Outbound integrations |
| API docs | Swashbuckle 5.6.0 | Swagger UI |
| Excel | EPPlus 4.1.0, DocumentFormat.OpenXml 2.16 | Excel import/export |
| PDF | PdfSharp + HtmlRenderer.PdfSharp | Document/print generation |
| ORM (secondary) | EntityFramework 6.1.3 | Identity store; most data access is raw ADO.NET |
| Tokens | System.IdentityModel.Tokens.Jwt 6.23.1 | JWT handling |
| Observability | Microsoft.Extensions.Logging 3.1.x + OpenTelemetry | Logging/tracing |

**Build & runtime:** NuGet uses the classic `packages.config` style with a shared `packages/` folder. Build via MSBuild / Visual Studio (`UVD.sln`); requires Windows + .NET Framework. Runs under IIS as an OWIN-hosted Web API.

## 8. Runtime Architecture & Flow

![Runtime Flow](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5282398269/child/attachment/att5282398287/download)

- **Stateless Web API** hosted in IIS via OWIN. Clients authenticate at `/Token` and pass a bearer token on each request.
- `Application_Start` registers areas, Web API config, filters, bundles, and initializes OTel logging (toggled by `OTEL_ENABLED`).
- `Application_BeginRequest` handles CORS preflight (OPTIONS) responses.
- Each controller action: (1) `ValidateToken` authorization, (2) input validation → `400` on failure, (3) delegate to a BusinessService, (4) DataAccess executes stored procedures, (5) result mapped to a ResponseVM/OutputResult and serialized to JSON, (6) exceptions logged via `ExceptionLogging` and returned as `500`.
- Connections are obtained per request via `DbConnector` / `DataAccessLayerFactory` using named connection strings (`UVDDbConnection`, plus reporting/offline DBs).

## 9. Important Entry Points

| Entry point | File | Purpose |
| --- | --- | --- |
| OWIN startup | `UVD/Startup.cs` → `Startup.Auth.cs` | Configures OAuth bearer authentication |
| App bootstrap | `UVD/Global.asax.cs` | Route/filter/bundle registration, OTel init, CORS |
| Web API config | `UVD/App_Start/WebApiConfig.cs` | Attribute routing, JSON formatter, host-auth filter |
| Token endpoint | `POST /Token` | Issues OAuth bearer tokens |
| API routes | `Controllers/*` with `[RoutePrefix]`+`[Route]` | Functional REST endpoints |
| API docs | `App_Start/SwaggerConfig.cs` | Swagger UI |
| Configuration | `UVD/Web.config` | Connection strings + integration appSettings |

## 10. High-Level Data Flow

```text
[ Mobile App / Dealer Portal ]
        | HTTPS + Bearer token (JSON)
        v
[ UVD Web API - Controller ]
   - OAuth bearer validation (OWIN)
   - ValidateToken + input validation
        v
[ UVD.BLL - BusinessService ]
   - Business rules, tax/pricing, orchestration
   - External integration calls (SAP, POMS, OBV, Azure, Extentia, SMTP, SMS)
        v
[ UVD.DAL - DataAccess ]
   - DbConnector / DataAccessLayerFactory
   - ADO.NET -> Stored Procedures
        v
[ SQL Server ] (UVD DB - DMS DB - Reporting DB)
        v
DataSet/DataTable -> mapped to ResponseVM*/DO
        ^
(response bubbles back up the same layers, serialized to JSON)
```

- **Request shape:** `RequestVMXxx` DTOs (UVD.VM/Request).
- **Response shape:** `ResponseVMXxx` / `OutputResult` / `CodeMessage` with `statusCode` + message + `data`.
- **Persistence:** stored-procedure-centric; results returned as `DataSet`/`DataTable` and projected to typed objects in the BLL.
- **Side effects:** integration calls and file uploads (`~/Document/`) occur in the business layer.

---

## Appendix — Diagram Regeneration

All PNG diagrams are generated programmatically and attached to this page.

```bash
cd PreOwnedDMS
python -m pip install --user matplotlib
python docs\diagrams\gen_diagrams.py
```

Output: `01_layered_architecture.png`, `02_module_map.png`, `03_runtime_flow.png`, `04_integration_context.png`.
