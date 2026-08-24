# MicroDMS.Web (DMS Domestic Web) — High Level Design (HLD)

> Architecture document for external engineering partners, authored against the [TVS HLD Template](https://tvsmotorcompany.atlassian.net/wiki/spaces/DE2/pages/4209508450/High+Level+Design+Template).
> Scope: the **MicroDMS.Web** project (assembly `MicroDMS.UI`) — the ASP.NET Web Forms UI tier of the TVS Motor Dealer Management System (DMS Domestic) — and its referenced class libraries in `MicroDMS.sln`.
> Source: `MICRO_DMS/MicroDMS/MicroDMS.Web` and sibling projects.
>
> **Companion diagrams** (draw.io under `diagram web/`)
> - [System Architecture](../diagram%20web/hld-system-architecture.md)
> - [Service Interaction](../diagram%20web/hld-service-interaction.md)
> - [Deployment Topology](../diagram%20web/hld-deployment-topology.md)
> - [Auth Flow](../diagram%20web/hld-auth-flow.md)
> - [External Integrations](../diagram%20web/hld-external-integrations.md)

---

## Overview

MicroDMS.Web is the **server-rendered ASP.NET Web Forms tier** of DMS Domestic, used by TVS Motor channel partners (dealers / ASCs) in the Indian domestic market. It renders the operational screens for Sales, Service, Parts, Accounts, Masters, HO operations, Dashboards and Reports using the Telerik RadControls suite, and executes business logic through a layered set of class libraries (`BusinessLayer` → `DataLayer`) over SQL Server and Oracle.

The application authenticates dealers through **UMS (Azure AD B2C / OAuth2)** with a legacy session-login fallback, holds per-user context in **in-process session**, and integrates with **SAP web portals, SMS/OTP providers, SendGrid, and a Booking Engine API**.

This HLD captures the architecture, deployment shape, primary flows, integrations, and resiliency posture of the Web Forms tier for external engineering partners. Business-sensitive details and all secrets are deliberately excluded; configuration is referenced by key name only.

---

## Tier Classification

**Tier 1 — Mission Critical.** MicroDMS.Web is a primary dealer-facing surface for day-to-day operations (sales, job cards, parts, accounting). Downtime halts dealer transactions and after-sales service. Standard Tier 1 expectations apply: high-availability hosting, monitored app pools, and a paged on-call path.

---

## Background

DMS Domestic began as a Web Forms application (`MicroDMS.Web` / `MicroDMS`) and has since been complemented by a modern Angular SPA + `OnlineDMS_WebAPI`. The Web Forms tier documented here remains in active use for a broad range of transactional and master-data screens. It is built on:

- **ASP.NET Web Forms** on **.NET Framework 4.5.2**, assembly `MicroDMS.UI`.
- A layered class-library set: `BusinessLayer` (~166 `*BL`), `BusinessEntities` (~297 `*DO` DTOs), `DataLayer` (~140 `*DAL`/`*DH` over a `DataAccessLayer` provider), plus `EntityObjects`, `CacheLibrary`, `ConfigHelper`, `ExceptionManager`, `Utilities`, `RadMessageBox`.
- **Telerik RadControls** for grids/combos/upload, with `RadCompression` and `RadUpload` HTTP modules.
- A wide integration footprint reached directly from the web/BL tier (UMS, SAP portals, SMS, Email, Booking Engine).

---

## Requirements

### Functional

- Authenticated dealer access via UMS (Azure AD B2C) with a legacy session-login fallback.
- Sales lifecycle — Enquiry → Quotation → Booking → Vehicle Invoice → Return / Stock Transfer.
- Service lifecycle — Job Card → Service → Invoice; Warranty / FSC / ASC claims; PSF.
- Parts inventory — GRN (vendor / AD / TVS), Direct Invoice, Issue, Purchase Return, Schemes, Physical Inventory.
- Accounting — vouchers, receipts, ledgers, commission/registration payments, Tally extract.
- Master data CRUD — Customer, Vehicle, Employee, Dealer/Branch, RTO, Tax, Rack, Vendor.
- HO operations, dashboards and Telerik reports.
- Excel-based data migration / bulk uploads.
- Outbound notifications — SMS (Airtel IQMS / Infobip) and Email (SendGrid).
- AJAX type-ahead lookups via ASMX web services.

### Non-Functional

| Concern | Target / Note |
|---|---|
| Availability | Tier 1 — high availability per environment (active-passive minimum) |
| Session | In-process session (`InProc`, 90-minute timeout) — sticky sessions required behind any load balancer |
| Request limits | Large uploads supported (`maxRequestLength` configured high for Excel/document upload) |
| Security | UMS (Azure AD B2C) + JWT acquisition; TLS 1.2 enforced for outbound integration; secrets externalized (no secrets in source) |
| Observability | Centralized logging via `ExceptionManager` / Enterprise Library; `Global.asax` `Application_Error` |
| Scalability | Horizontal scale of IIS app pool with sticky sessions; master/lookup caching via `CacheLibrary` |
| Resiliency | Deadlock-retry in DAL (`DeadLockRetryHelper`); ADO.NET transactions for writes; read-only reporting replica |
| Compliance | PII handled per TVS policy; business-sensitive data excluded from this document |

---

## System Architecture (Current)

MicroDMS.Web follows a classic **n-tier architecture**:

<!-- ╔════════════════════════════════════════════════════════════════════════════╗
     ║  📸 CONFLUENCE IMAGE PLACEHOLDER                                           ║
     ║                                                                            ║
     ║  Paste image here: hld-system-architecture.png                            ║
     ║  Location: diagram web/hld-system-architecture.png                        ║
     ╚════════════════════════════════════════════════════════════════════════════╝ -->

![System Architecture](../diagram%20web/hld-system-architecture.png)

```
Dealer Browser (Telerik RadControls / AjaxControlToolkit)
        │  HTTPS (page postbacks + ASMX AJAX)
        ▼
IIS  ──►  MicroDMS.UI  (ASP.NET Web Forms, .NET 4.5.2)
        │   BasePage → SessionLayer / ApplicationLayer / ConfigSettings
        ▼
MicroDMS.BusinessLayer (*BL)   ── GST/posting/validation rules
        ▼
MicroDMS.DataLayer (*DAL/*DH) + DataAccessLayer provider
        ▼
SQL Server (OnlineDMS / Report / Portal DBs)   +   Oracle
        ▲
        └── External: UMS (REST/JWT) · SAP portals · SMS · Email · Booking Engine API
```

The hot path is a browser postback (or ASMX AJAX call) into a Web Forms page derived from `BasePage`, which builds a `*DO` DTO, calls a `*BL` method, which delegates to a `*DAL` method that executes a stored procedure / SQL through the `DataAccessLayer` provider. Cross-cutting concerns: `ConfigHelper` (session/config), `CacheLibrary` (master/lookup cache), `ExceptionManager` (logging).

> Visualized in [System Architecture](../diagram%20web/hld-system-architecture.md).

---

## Major Components / Services

<!-- ╔════════════════════════════════════════════════════════════════════════════╗
     ║  📸 CONFLUENCE IMAGE PLACEHOLDER                                           ║
     ║                                                                            ║
     ║  Paste image here: hld-service-interaction.png                            ║
     ║  Location: diagram web/hld-service-interaction.png                        ║
     ╚════════════════════════════════════════════════════════════════════════════╝ -->

![Service Interaction](../diagram%20web/hld-service-interaction.png)

| Component | Tier | Role |
|---|---|---|
| **MicroDMS.Web (`MicroDMS.UI`)** | Presentation | ASP.NET Web Forms pages (`.aspx`), user controls (`.ascx`), `MainMaster.master`; `BasePage`/`BasePageAdmin` base classes; `Global.asax` lifecycle/error events |
| **WebServices/ (ASMX)** | Presentation | AJAX lookups (`CustomerSearch`, `PartSearch`, `PartrSearch`, `LabourSearch`, `ComplaintSearch`, `FrameNoCheck`, `FramenoAvailability`, `JobCarddetails`, `GetCustVehByVehInvDate`, `GetCustVehByVehModifyDate`) |
| **MicroDMS.BusinessLayer** | Application | ~166 `*BL` classes — business rules, GST (`TaxProcessor`/`GSTTaxProcessor`), accounting posting (`*AccountPosting`), orchestration |
| **MicroDMS.BusinessEntities** | Application | ~297 `*DO` DTOs exchanged between layers |
| **MicroDMS.DataLayer** | Data access | ~140 `*DAL`/`*DH` classes + `DataAccessLayer` provider abstraction (`DBFactoryHelper`, `SqlDataAccessLayer`, `OracleHelper`, `DeadLockRetryHelper`) |
| **MicroDMS.ConfigHelper** | Cross-cutting | `SessionLayer`, `ApplicationLayer`, `ConfigSettings` typed accessors |
| **MicroDMS.CacheLibrary** | Cross-cutting | Master/lookup caching |
| **MicroDMS.ExceptionManager** | Cross-cutting | Centralized logging / exception policy (Enterprise Library) |
| **MicroDMS.Utilities / EntityObjects / RadMessageBox** | Cross-cutting | Helpers, entity definitions, Telerik message-box helper (VB) |

> Visualized in [Service Interaction](../diagram%20web/hld-service-interaction.md).

---

## Deployment Architecture

<!-- ╔════════════════════════════════════════════════════════════════════════════╗
     ║  📸 CONFLUENCE IMAGE PLACEHOLDER                                           ║
     ║                                                                            ║
     ║  Paste image here: hld-deployment-topology.png                            ║
     ║  Location: diagram web/hld-deployment-topology.png                        ║
     ╚════════════════════════════════════════════════════════════════════════════╝ -->

![Deployment Topology](../diagram%20web/hld-deployment-topology.png)

| Layer | Hosting |
|---|---|
| MicroDMS.Web (`MicroDMS.UI`) | IIS app pool (Integrated pipeline) on Windows — Azure App Service (Windows) or Windows VM/IIS; .NET Framework 4.x runtime |
| Session state | In-process (`InProc`) — requires **sticky sessions** (session affinity) behind a load balancer |
| SQL Server | Azure SQL or on-prem SQL Server (primary `DMSConnection`; read replica `DMSSecConnReport`) |
| Oracle | On-prem / hosted Oracle (legacy reads) |
| Static assets | Served from the IIS site (`App_Themes`, `images`, `js`) |
| Config | `Web.config` + `Web.Debug.config`/`Web.Release.config` XDT transforms; sensitive sections encrypted with `aspnet_regiis -pe` per environment |

CI workflow: `MICRO_DMS/MicroDMS/.github/workflows/main.yml`.

**Deployment flow:** merge to integration branch → CI builds the solution → produce a Web Deploy package for `MicroDMS.Web` → deploy to the target IIS app pool → apply the correct `Web.<Env>.config` transform → encrypt sensitive config sections → smoke-test (UMS login → `Home.aspx` → one master lookup → one transactional screen). Roll back by redeploying the previous Web Deploy package.

> Visualized in [Deployment Topology](../diagram%20web/hld-deployment-topology.md).

---

## Database Interactions

- **Provider abstraction:** `DataLayer` uses a `DataAccessLayer` provider (`DBFactoryHelper`, `SqlDataAccessLayer`, `OracleHelper`) selecting connections via a `SQLConnectionType` enum (OnlineDMS, OnlineDMS Report, Central Portal, Retail, FSC Claim, Oracle SQL Portal, etc.).
- **Access style:** primarily **stored procedures** and parameterized SQL executed through ADO.NET, returning `DataSet`/DTO collections for grid binding.
- **Connections (names only, redacted values):** `DMSConnection` (primary), `DMSConnReport` / `DMSSecConnReport` (read/reporting), `OracleConnection` / `OracleConnectionClient`, `FSCOTPConnection`, `CENTRALPORTALCONN`, `RETAILSCONN`, `OracleSQLPortal`, `OnlineDMS2`, `OfflineDMS2`, `SqlPortalCon`.
- **Resiliency:** `DeadLockRetryHelper` for transient deadlocks; ADO.NET transactions for multi-statement writes; read-only reporting replica (`ApplicationIntent=ReadOnly`) for report queries.
- **Caching:** hot master/lookup reads cached via `CacheLibrary` to reduce DB round-trips.

> Visualized in [Service Interaction](../diagram%20web/hld-service-interaction.md).

---

## API Integrations

The Web Forms tier integrates outbound directly from page/BL code:

| Integration | Mechanism | Touchpoints |
|---|---|---|
| **UMS (Azure AD B2C / OAuth2)** | Browser redirect to UMS auth UI; token acquisition via RestSharp (`UMSIntegration/UMSUserGetToken`) | `UMSDMSLogin.aspx.cs`, `UMSIntegrationBL`/`UMSIntegrationDAL`, `UMS_*` settings |
| **SAP portals** | Web Dynpro deep links (HTTPS) + SOAP service references | SAP `*Link` settings, `Service References/`, `SAP_Operations` |
| **SMS / OTP** | HTTP to Airtel IQMS / Infobip | `SMS.cs`, `SMShelper/`, `SMSTemplateBL` |
| **Email** | SendGrid SMTP | `EmailBL` (`SMTP*` settings) |
| **Booking Engine / BS API** | OAuth2 client-credentials REST | `BE*` settings, `BookingEngineApiBaseUrl` |
| **Internal ASMX (AJAX)** | `ScriptService` JSON over HTTP, `EnableSession` | `WebServices/*.asmx` |

> Visualized in [External Integrations](../diagram%20web/hld-external-integrations.md).

---

## Authentication / Authorization Flow

<!-- ╔════════════════════════════════════════════════════════════════════════════╗
     ║  📸 CONFLUENCE IMAGE PLACEHOLDER                                           ║
     ║                                                                            ║
     ║  Paste image here: hld-auth-flow.png                                      ║
     ║  Location: diagram web/hld-auth-flow.png                                  ║
     ╚════════════════════════════════════════════════════════════════════════════╝ -->

![Auth Flow](../diagram%20web/hld-auth-flow.png)

1. **Entry** — unauthenticated requests land on `UMSDMSLogin.aspx` (UMS) or `Login.aspx` (legacy session login). `LoginURL`/`UMSDMSLogin` settings drive routing.
2. **UMS sign-in** — `UMSDMSLogin.aspx` redirects the browser to the UMS Auth base URL (`UMS_Auth_Base_URL`) with `UMS_AppId` and `ums_callback_URL`. UMS authenticates the dealer and returns to the callback.
3. **Token acquisition** — server-side, `UMSDMSLogin.aspx.cs` uses RestSharp to call `UMS_token_auth` (`/UMSIntegration/UMSUserGetToken`) with client credentials (`ClientID_UMS` / `ClientSecret_UMS`), receiving an access key stored in session.
4. **Session establishment** — `SessionLayer` populates dealer/user context (`DEALERID`, `DEALERNAME`, `UMS_USER_ID`, etc.) in **in-process session**.
5. **Per-request enforcement** — every page derives from `BasePage`, whose `OnInit`/`OnPreInit` verifies an authenticated session and redirects to login if absent.
6. **Logout** — `Logout.aspx` clears session and redirects to UMS logout (`UMS_logout` / `UMS_logout_AppId`).

> Note: `Web.config` sets `authentication mode="Windows"` at the IIS level, but effective dealer authentication is handled by the UMS/session flow above. Visualized in [Auth Flow](../diagram%20web/hld-auth-flow.md).

---

## External Systems

<!-- ╔════════════════════════════════════════════════════════════════════════════╗
     ║  📸 CONFLUENCE IMAGE PLACEHOLDER                                           ║
     ║                                                                            ║
     ║  Paste image here: hld-external-integrations.png                          ║
     ║  Location: diagram web/hld-external-integrations.png                      ║
     ╚════════════════════════════════════════════════════════════════════════════╝ -->

![External Integrations](../diagram%20web/hld-external-integrations.png)

- **Identity:** UMS / Azure AD B2C
- **ERP / portals:** SAP Web Dynpro portals (dealer ledger, warranty, credit note, packing list, e-Sugam, etc.)
- **Databases:** SQL Server (primary + reporting replica + portal DBs), Oracle (legacy)
- **Messaging:** SMS via Airtel IQMS / Infobip; Email via SendGrid
- **Partner API:** Booking Engine / BS API (OAuth2)
- **Reporting:** Telerik Reporting / ReportViewer
- **Document generation:** PDFsharp / MigraDoc (PDF); DocumentFormat.OpenXml (Excel)

---

## Infrastructure Dependencies

| Dependency | Purpose |
|---|---|
| IIS / Windows | Hosts the Web Forms application (`MicroDMS.UI.dll` + `.aspx`) |
| .NET Framework 4.x runtime | Execution runtime (project targets 4.5.2) |
| SQL Server | Primary datastore + reporting replica + portal DBs |
| Oracle | Legacy reads for specific flows |
| Telerik Web UI / Reporting | UI controls, AJAX modules (`RadCompression`, `RadUpload`), reports |
| Microsoft Enterprise Library 4.1 | Logging / exception handling / caching configuration |
| Local `bin/` reference DLLs | Telerik, AjaxControlToolkit, MessagingToolkit.QRCode, EntLib (restored from artifact storage) |
| Network reachability | To UMS, SAP portals, SMS/Email providers, Booking Engine API |

---

## High-Level Sequence Flows

### 1. Login → Home
Dealer → `UMSDMSLogin.aspx` → UMS sign-in → callback → server token acquisition (RestSharp) → session populated → redirect to `Home.aspx` (`DealerHomePage`).

### 2. Authenticated read (master fetch / list)
`BasePage` (auth check) → page event → `*BL` → `*DAL` → `DataAccessLayer` → SQL stored proc → `DataSet`/DTO → RadGrid binding.

### 3. AJAX type-ahead lookup
RadComboBox keystroke → `WebServices/<X>.asmx` (`ScriptService`, `EnableSession`) → `*BL` → `*DAL` → SQL → JSON → combo populated.

### 4. Authenticated write (e.g. Job Card / Sales Invoice)
Page builds `*DO` → `*BL` applies GST (`TaxProcessor`) and posting rules (`*AccountPosting`) → `*DAL` executes a SQL transaction → result DTO → confirmation message (`RadMessageBox`).

### 5. Outbound notification
Business event → `EmailBL` (SendGrid) / `SMS.cs` (Airtel/Infobip) → external provider over HTTPS/SMTP.

> Visualized in [Service Interaction](../diagram%20web/hld-service-interaction.md) and [Auth Flow](../diagram%20web/hld-auth-flow.md).

---

## Scalability & Resiliency Considerations

**Scalability**
- Horizontal scale of the IIS app pool; because session is `InProc`, a load balancer must use **session affinity (sticky sessions)**, or session state should be externalized (SQL/State Server) as a modernization step.
- `CacheLibrary` reduces repeated master/lookup DB hits.
- Read/reporting traffic offloaded to `DMSSecConnReport` (read-only replica).

**Resiliency**
- `DeadLockRetryHelper` retries transient SQL deadlocks; writes wrapped in ADO.NET transactions.
- Centralized error logging via `Global.asax` `Application_Error` → `ExceptionManager`; user-facing errors routed via `Errors/`.
- Outbound integration calls enforce TLS 1.2; failures are caught and surfaced as friendly messages.
- Multiple connection targets allow failover/segregation (primary vs reporting vs portal DBs).

**Risks / modernization notes**
- **Legacy framework:** .NET Framework 4.5.2 + Web Forms + Telerik — modernization (to .NET 8 / modern UI) is a multi-quarter effort.
- **InProc session:** limits seamless horizontal scaling; externalizing session is recommended for true scale-out.
- **Synchronous SAP/Oracle calls:** can elevate tail latency under partner slowdown.
- **Secret hygiene:** DB passwords, SendGrid key, SMS tokens, UMS client secret and `APIKEY` must be sourced from encrypted config / secret store and never committed.

---

## Expected Outputs (per steering)

### Architecture Diagram Description
A four-lane architecture: **Client (Dealer browser, Telerik RadControls)** → **Web Tier (IIS · MicroDMS.UI Web Forms · BasePage · ASMX lookups)** → **Application (BusinessLayer + DataLayer + ConfigHelper/Cache/ExceptionManager)** → **Data & External (SQL Server · Oracle · UMS · SAP portals · SMS · Email · Booking Engine)**. The hot path is HTTPS postback/AJAX → page → BL → DAL → SQL; side legs cover caching, logging, and outbound integrations.

### Service Interaction
Pages and ASMX services call `*BL`, which composes `*DAL` calls (ADO.NET stored procs via the `DataAccessLayer` provider against SQL Server / Oracle), GST computation (`TaxProcessor`/`GSTTaxProcessor`), and accounting posting (`*AccountPosting` → `PostManagerDAL`). Session/config flow through `ConfigHelper`; caching via `CacheLibrary`; logging via `ExceptionManager`.

### Infra Topology
Per environment (DEV/QA/PROD): IIS app pool hosts `MicroDMS.UI`; SQL Server (primary + read replica) and Oracle provide data; outbound to UMS, SAP portals, SMS/Email providers, and Booking Engine API. Session is in-process (sticky sessions required). Config via `Web.config` + XDT transforms with encrypted sensitive sections.

### Deployment Flow
CI (`main.yml`) builds the solution → Web Deploy package for `MicroDMS.Web` → deploy to IIS app pool → apply `Web.<Env>.config` transform → encrypt sensitive sections (`aspnet_regiis -pe`) → smoke test → phased rollout. Rollback redeploys the previous package.

### External Integrations
- **Identity:** UMS / Azure AD B2C
- **ERP / portals:** SAP Web Dynpro portals (SOAP + deep links)
- **Data:** SQL Server, Oracle
- **Notifications:** SendGrid (Email), Airtel IQMS / Infobip (SMS)
- **Partner REST:** Booking Engine / BS API
- **Reporting / docs:** Telerik Reporting, PDFsharp/MigraDoc, OpenXml

---

## Appendix

### Glossary
- **AMC** — Annual Maintenance Contract · **ASC** — Authorized Service Centre · **BL** — Business Layer · **DAL** — Data Access Layer · **DMS** — Dealer Management System · **FSC** — Free Service Coupon · **GRN** — Goods Receipt Note · **HO** — Head Office · **JC** — Job Card · **PSF** — Post-Sales Follow-up · **RTO** — Regional Transport Office · **SPA** — Single Page Application · **UMS** — User Management System (Azure AD B2C-based)

### References
- [TVS HLD Template](https://tvsmotorcompany.atlassian.net/wiki/spaces/DE2/pages/4209508450/High+Level+Design+Template)
- Source: `MICRO_DMS/MicroDMS/MicroDMS.Web` (`MicroDMS.UI`) and referenced libraries

---

_Source: MICRO_DMS / MicroDMS / MicroDMS.Web (MicroDMS.UI). Secrets redacted; business-sensitive details excluded; counts approximate._
