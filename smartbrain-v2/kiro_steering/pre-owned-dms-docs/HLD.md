# High Level Design (HLD) — PreOwnedDMS (UVD)

> Restored from Confluence: https://tvsmotorcompany.atlassian.net/wiki/pages/viewpage.action?pageId=5269356573

**Audience:** External engineering partners. **Scope:** the `PreOwnedDMS` solution (`UVD.sln`) — the Used-Vehicle Dealership (UVD) platform. **Template:** follows the D&AI High Level Design Template. **Confidentiality:** no secrets or business-sensitive logic; integration auth is described by config key name/pattern only.

## Overview

PreOwnedDMS (internally **UVD**) is a multi-tier Dealer Management System for the **pre-owned two- and three-wheeler** business of TVS Motor dealerships. It manages the full used-vehicle lifecycle — procurement, valuation, refurbishment, resale, after-sales service, spare parts, accessories, and accounting — exposed as a stateless REST API consumed by a mobile app and a dealer web portal. The platform is multi-tenant by **dealer** and **branch**.

## Tier Classification

**Tier 2 — Business Critical.** Core to dealer operations but not life-critical; short scheduled downtime is tolerable. Data integrity for financial postings is paramount.

## Background

PreOwnedDMS reuses the proven core MicroDMS libraries (`MicroDMS.BusinessEntities/BusinessLayer/DataLayer`) and extends them with UVD-specific layers (`UVD`, `UVD.BLL`, `UVD.DAL`, `UVD.VM`, `UVD.Helper`). It standardizes on ASP.NET Web API 2 + OWIN OAuth bearer auth, with stored-procedure-based access to SQL Server. OpenTelemetry hooks were recently added for observability.

## Requirements

**Functional:** used-vehicle procurement (enquiry → valuation → checklist/documents → procurement); refurbishment; resale (enquiry, block, sale order, invoice, self-HP); spare parts (master, stock, PO, GRN, pick-slip, returns); accessories; accounting; masters; dealer-portal feeds.

**Non-Functional:** stateless horizontally-scalable API behind a load balancer; OAuth2 bearer auth with per-request dealer/branch/user scope checks; resilient SQL connectivity (AlwaysOn AG, MultiSubnetFailover, pooling); observability via OTel + structured logging; secrets externalized (target state).

## 1. System Architecture

![System Architecture](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5269356573/child/attachment/att5268471916/download)

**Architecture Diagram Description.** PreOwnedDMS is a classic **N-tier** application. Clients (UVD mobile app, dealer web portal, Swagger UI) call the **UVD Web API** over HTTPS with an OAuth2 bearer token. The API tier (IIS + OWIN, ASP.NET Web API 2) authenticates the request, runs a dealer/branch/user scope check, and delegates to the **business tier** (`UVD.BLL`). Business services apply rules and orchestrate integrations, then call the **data-access tier** (`UVD.DAL`), which executes **stored procedures** on **SQL Server**. Shared libraries (`UVD.VM`, `UVD.Helper`, `MicroDMS.*`) are referenced across tiers. **Dependency services** (SAP, POMS/IDP, Orange Book Value, Azure, Extentia, SMTP, SMS) are shown in a distinct colour and invoked from the business tier. Flow is strictly downward: Controller → BLL → DAL → SQL Server.

**Pros:** clear separation of concerns; reuse of hardened core; stateless tier scales out; SP-based access centralizes data logic. **Cons:** .NET Framework (Windows/IIS) limits portability; raw ADO.NET + SPs add boilerplate; shared libraries couple UVD to the core release cycle.

## 2. Major Components / Services

| Component | Tier | Responsibility |
| --- | --- | --- |
| `UVD` (Web API) | App | Controllers, OWIN OAuth, Swagger, filters, CORS, OTel init |
| `UVD.BLL` | Business | `*BusinessService` classes; rules, tax/pricing, integration orchestration |
| `UVD.DAL` | Data | ADO.NET + stored procedures; `DbConnector`, `DataAccessLayerFactory` |
| `UVD.VM` | Shared | `RequestVM*`/`ResponseVM*` DTOs, `OutputResult`, `CodeMessage` |
| `UVD.Helper` | Shared | `ExceptionLogging`, `Validator`, `Encryptor`, status enums |
| `MicroDMS.*` | Shared | Core entities, business logic, data access reused from DMS |

**Functional services:** Procurement & Valuation, Refurbishment, Sales, Service & Warranty, Spare Parts (PO/GRN/pick-slip/returns), Accessories, Accounts, Masters & Settings, Portal & Web Order.

![Service Interaction](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5269356573/child/attachment/att5268701285/download)

**Service Interaction.** A controller resolves to one module's business service; cross-module needs (e.g. vouchers during a sales invoice) are met by calling sibling business services. Integration services (`SAPAccessoriesService`, `IDPService`, `AzureBusinessService`, `ExtentiaBusinessService`, `EmailService`) are invoked from business services (dependency colour). All persistence funnels through `UVD.DAL` → stored procedures → SQL Server.

## 3. Deployment Architecture

![Infra Topology](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5269356573/child/attachment/att5269487651/download)

**Infra Topology.** Four logical zones — **Clients** (mobile/portal over HTTPS); **Edge** (TLS termination + load balancer); **Application Zone** (Windows Server + IIS hosting multiple stateless UVD Web API nodes, OTel collector at OTLP :4317, local logs at `D:\LogFiles`); and **Data Zone** (SQL Server AlwaysOn AG — read/write primary + read-only reporting replica with `ApplicationIntent=ReadOnly`, `MultiSubnetFailover=True`). Dependency services are reached over the internet / TVS network.

**Deployment Flow.** (1) Build with MSBuild / Visual Studio from `UVD.sln` (classic `packages.config` restore). (2) Produce a web-deploy package for the `UVD` Web API. (3) Deploy node-by-node behind the load balancer (rolling) to preserve availability. (4) Apply per-environment config; warm up and health-check each node before re-adding to the pool. **Rollback:** redeploy the previous package and revert config; stateless nodes make replacement safe.

## 4. Database Interactions

- **Engine:** SQL Server, accessed via **stored procedures** (EntityFramework only for the Identity store).
- **Connections (key names only):** `UVDDbConnection` (primary), `DMSConnection`, `DMSConnReport` (reporting) — sourced from `Web.config` at runtime.
- **Access pattern:** `DbConnector`/`DataAccessLayerFactory` open a connection per request; `*DataAccess` classes set an SP name, add typed parameters, execute, and map `DataSet`/`DataTable` into `ResponseVM*`/`*DO` objects.
- **Resiliency:** `Pooling=True`, `Max Pool Size=2500`, tuned timeouts, `ApplicationIntent=ReadOnly` for reports, `MultiSubnetFailover=True` for AG failover; `DeadLockRetryHelper` for deadlock-prone operations.

## 5. API Integrations

RESTful JSON API (Web API 2) with attribute routing (`[RoutePrefix]` + `[Route]`), `[HttpPost]`/`[HttpGet]`, `[Authorize]`, and `[SwaggerResponse]`. Standard envelopes: `OutputResult`/`CodeMessage`/`ResponseVM*` with `statusCode`, message, and `data`. Outbound integrations are encapsulated in dedicated business services using `HttpClient`/`RestSharp`.

## 6. Authentication / Authorization Flow

![Auth Flow](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5269356573/child/attachment/att5270372367/download)

1. Client authenticates at **`POST /Token`** (OWIN OAuth Authorization Server).
2. A **bearer token** (1-day expiry) is returned.
3. Each API call carries `Authorization: Bearer <token>`.
4. OWIN validates the bearer token (`SuppressDefaultHostAuthentication` + `HostAuthenticationFilter`).
5. The controller calls `ValidateToken((ClaimsIdentity)User.Identity)` to enforce dealer/branch/user scope.
6. On success, control passes to business/data layers.
7. Responses are JSON; failures return **401**, **400**, or **500** (logged via `ExceptionLogging`).

Identity is backed by ASP.NET Identity (EntityFramework). `AllowInsecureHttp` is enabled in the inspected config and should be **false** in production (TLS enforced at the edge).

## 7. External Systems & Integrations

![External Integrations](https://tvsmotorcompany.atlassian.net/wiki/rest/api/content/5269356573/child/attachment/att5269225530/download)

| System | Direction | Purpose | Auth pattern (key names only) |
| --- | --- | --- | --- |
| **SAP** | Outbound | Accessory orders / invoice posting | OAuth client-credentials (`sap_token_url`, `sap_client_id`, `sap_client_secret`) |
| **POMS / IDP** | Outbound | Publish spare purchase orders | Login token (`POMSTokenEndPoint`, `POMSID`, `POMSPassword`) + `X-Client-Id` |
| **Orange Book Value** | Outbound | Used-vehicle valuation pricing | API token (`OBVToken`, `OBVPriceUrl`) |
| **Azure Services** | Outbound | Token generation + storage | Function code header (`AzureTokenGenURL`, `AzureTokenGenCode`) |
| **Extentia** | Inbound | Master-data sync | SHA-512 daily hash token |
| **SMTP Email** | Outbound | PO / notification emails | `SMTPHost`, `SMTPPort`, `SMTPUserID`, `EmailFrom` |
| **SMS Gateway** | Outbound | OTP / transactional alerts | URL-keyed gateway (`SMS1`/`SMS2`/`SMS3`) |
| **Dealer Web Portal** | In/Out | Parts-order feeds, referral vehicles | Bearer token |

## 8. Infrastructure Dependencies

- **Compute:** Windows Server + IIS (OWIN-hosted Web API), multiple stateless nodes.
- **Database:** SQL Server AlwaysOn AG (primary + read replica).
- **Edge:** Load balancer / reverse proxy with TLS termination.
- **Observability:** OpenTelemetry collector (OTLP :4317), local file logs (`D:\LogFiles`).
- **Runtime libs:** ASP.NET Web API 2 (5.2.x), OWIN 3.0.1, ASP.NET Identity 2.2.1, Newtonsoft.Json 12.x, RestSharp 106.x, Swashbuckle 5.6.0, EPPlus/OpenXml, PdfSharp, EntityFramework 6.1.3, JWT/IdentityModel 6.23.1.
- **Build:** MSBuild / Visual Studio 2019; NuGet `packages.config`.

## 9. High-Level Sequence Flows

**Create Procurement (example):** App → `POST /Procurement/createProcurement` (bearer + `RequestVMCreateProcurement`) → OWIN token validation → controller `ValidateToken` + `Validator.CreateProcurement` → `ProcurementBusinessService.BLLCreateProcurement` (may call OBV pricing) → `ProcurementDataAccess` executes stored procedure(s) → result mapped to `CodeMessage`/`ResponseVM*` returned as JSON.

**Spare PO publish (dependency + error handling):** PO confirmed → `IDPService.GetPOMSToken()` → `SendPODataToPOMS` publishes paginated payload → on success status updated; on failure exception logged and surfaced; dealer email via `EmailService.PushPOGenerationEmail`.

**Retry / failover / error paths:** SQL AG failover via `MultiSubnetFailover`; deadlock retry via `DeadLockRetryHelper`; TLS 1.2 enforced for integrations; failures caught, logged, and mapped to safe HTTP responses; non-critical notification failures are isolated from the primary transaction.

## 10. Scalability & Resiliency Considerations

**Scalability:** stateless API scales out behind the load balancer; read/reporting traffic offloaded to the AG read-only replica; connection pooling sized for concurrency; heavy operations (Excel/PDF, integrations) run `async`.

**Resiliency:** SQL AlwaysOn AG with multi-subnet failover; deadlock retry helper; centralized exception logging + OTel traces; graceful degradation isolating notification/integration failures from core transactions.

**Improvement opportunities:** externalize secrets to a vault (e.g. Azure Key Vault) and rotate any currently in `Web.config`; enforce `AllowInsecureHttp=false` and HTTPS end-to-end; move per-node document storage to shared/blob storage; add a distributed cache for hot master data; complete the OTel exporter wiring (currently scaffolded).

## Deployment & Rollout Plan

Rolling deployment per IIS node behind the load balancer with health-check gating; rollback by redeploying the previous package and reverting config.

## Metrics to be Tracked

- API: request rate, p95/p99 latency, 4xx/5xx per controller.
- SQL: pool usage, query duration, deadlock count, AG failover events.
- Integrations: SAP/POMS/OBV success rate and latency; email/SMS delivery failures.
- Host: CPU/memory per IIS node, thread-pool saturation.

## Risks

- Secrets currently present in `Web.config` (config + source) — security risk until externalized/rotated.
- .NET Framework / Windows-only runtime limits portability.
- Tight coupling to shared MicroDMS libraries ties releases to the core product.
- Per-node local file storage for documents/logs complicates scale-out.

## Alternatives Considered

**Option A — Re-platform to .NET (Core) + containers/K8s.** Pros: portability, autoscale, modern observability. Cons: large migration effort; deferred in favour of incremental hardening.

**Option B — Direct ORM (EF) for transactional paths.** Pros: less boilerplate. Cons: diverges from the SP-centric DMS standard and risks performance regressions; rejected.

## Appendix — Glossary

| Term | Meaning |
| --- | --- |
| UVD | Used Vehicle Dealership (this platform) |
| DMS | Dealer Management System |
| BLL / DAL / VM | Business Logic Layer / Data Access Layer / View Model |
| GRN / PO | Goods Receipt Note / Purchase Order |
| POMS / IDP | TVS Integration Platform for order publishing |
| OBV | Orange Book Value (vehicle valuation) |
| AG | (SQL Server) AlwaysOn Availability Group |
| OTel | OpenTelemetry |
| HP | Hire Purchase (financing) |
