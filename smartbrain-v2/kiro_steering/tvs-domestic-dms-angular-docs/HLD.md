# DMS Domestic — High Level Design (HLD)

> Authored against `.kiro/steering/HLD.md` and the [TVS HLD Template](https://tvsmotorcompany.atlassian.net/wiki/spaces/DE2/pages/4209508450/High+Level+Design+Template).
>
> **Source repos**
> - Angular Frontend: `D:\DMS_DOMESTIC\ANGULAR_DMS`
> - .NET Web API: `D:\DMS_DOMESTIC\MICRO_DMS\MicroDMS\OnlineDMS_WebAPI`
>
> **Companion diagrams**
> - [System Architecture](../diagrams/hld-system-architecture.md)
> - [Deployment Topology](../diagrams/hld-deployment-topology.md)
> - [Service Interaction](../diagrams/hld-service-interaction.md)
> - [Auth Flow](../diagrams/hld-auth-flow.md)
> - [External Integrations](../diagrams/hld-external-integrations.md)

---

## Overview

DMS Domestic is the Dealer Management System used by TVS Motor channel partners (dealers, ASCs) for the Indian domestic market. It is delivered as a single product with two co-deployed tiers — an Angular 6 SPA (with optional Electron desktop build) and an ASP.NET Web API (`OnlineDMS_WebAPI`) on .NET Framework 4.7.2 — wired through Azure API Management and protected by UMS (Azure AD B2C). The platform supports Sales, Service, Parts, Accounts, Master, HO and Reports flows, integrating with SAP, Oracle, Service Bus, Azure Blob, Redis, SendGrid, SMS / OTP providers and partner APIs (DigiSigner, EMS, NGD, ATP, BookingEngine).

This HLD captures the current production architecture, deployment shape, primary flows, and resiliency posture for external engineering partners.

---

## Tier Classification

**Tier 1 — Mission Critical**.

DMS Domestic is the system of record for dealer operations across India: it powers vehicle sales, job cards, warranty claims, parts inventory, accounting and HO operations. Downtime stops dealer revenue activity and disrupts after-sales service. Standard Tier 1 SLOs apply (high-availability deployment, multi-region failover where infra permits, instrumented with Application Insights + OpenTelemetry, paged on-call rotation).

---

## Background

The platform evolved from a legacy Web Forms application (`MicroDMS.Web`, `MicroDMS`) into a modern Angular SPA backed by a Web API (`OnlineDMS_WebAPI`). The legacy surface is retained for transitional flows but new development happens in the SPA + Web API tiers. Over time the system has accumulated:

- A large business catalogue (~166 BL classes, ~297 DTOs across `MicroDMS.BusinessLayer` and `MicroDMS.BusinessEntities`).
- A wide integration footprint (SAP, Oracle, ZMC, Insurance, EMS, NGD, ATP, DigiSigner, multiple SMS providers, SendGrid).
- Cross-cutting infra: Redis caching, Service Bus async fan-out (`DMSFunctionApp`), OpenTelemetry, Application Insights, JWT/UMS auth.

Recent investments include OpenTelemetry traces+logs (with kill switch via `OTEL_ENABLED`), the DIGI ↔ DMS Notification service integration via APIM, and progressive migration of features from legacy Web Forms to the Angular SPA.

---

## Requirements

### Functional

- Authenticated dealer access with UMS (Azure AD B2C) sign-in and JWT-based authorization across the API surface.
- End-to-end Sales lifecycle — Enquiry → Booking → Invoice → Stock Transfer / RTO / PSF / Returns.
- End-to-end Service lifecycle — Job Card → Service → Complete → Invoice; Warranty / FSC / ASC claims.
- Parts inventory — GRN (vendor / other), Direct Invoice, Issue, Returns, Inventory checks.
- Accounting — Vouchers, Sub-ledger, Reconciliation, Admin reports.
- Master data CRUD — Customer, Vehicle, Bank, Area, RTO, Vendor, Labour.
- HO operations and dashboards.
- Outbound notifications — SMS, Email, OTP via abstracted provider clients.
- Inbound webhooks — ATP, BookingEngine 2.0, BookingService, EnquiryService, CWIService, NotificationService.
- Document generation — invoices and reports as PDF (via `Select.HtmlToPdf` / `PdfSharp`).

### Non-Functional

| Concern | Target |
|---|---|
| Availability | Tier 1 — high availability per environment (active-passive minimum) |
| Latency (P95, hot read) | < 600 ms at API edge |
| Latency (P95, hot write) | < 1.5 s at API edge |
| Throughput | Burst-tolerant; batch invoicing peaks during business hours |
| Security | JWT (UMS / Azure AD B2C), TLS 1.2+, JWT keys held in `RSAKeys/` and KeyVault (target), no secrets in source |
| Observability | OpenTelemetry traces + logs (OTLP), Application Insights, structured logs via `LogGenerationOTel` |
| Scalability | Horizontal scale of WebAPI app pool, Redis-cached tokens, async fan-out via Service Bus |
| Resiliency | TLS 1.2 enforced, batch export with retry-friendly buffers, kill switch on telemetry, idempotent writes for known flows |
| Compliance | PII handled per TVS policy; audit logs via OTel |

---

## Current Architecture (HLD)

The current production architecture is an Angular SPA → APIM → ASP.NET Web API → BL → DAL → SQL/Oracle, with a parallel async leg via Azure Service Bus that is consumed by `DMSFunctionApp`. Auth is via UMS / Azure AD B2C, with APIM enforcing `validate-jwt`. Cross-cutting infra: Redis (StackExchange.Redis) caches tokens and master data; SAP / ZMC / Insurance Policy Upload reached via SOAP service references; SendGrid / Infobip / TinySMS / Mahale handle messaging; PDF generation in-process; observability via OpenTelemetry (OTLP) and Application Insights running in parallel.

> Visualized in [System Architecture](../diagrams/hld-system-architecture.md).

The system is deployed on Azure-hosted IIS (or compatible Windows app service) for the Web API; the Angular bundle is distributed as static assets (Azure Storage / IIS virtual dir / CDN) and additionally as an Electron desktop app for offline-friendly use cases.

---

## Proposed Architecture (HLD)

The "proposed" view in this document is the **current production architecture**, presented in the TVS HLD style for external engineering partners. Components are colour-coded in the companion diagrams to highlight third-party / managed dependencies (orange) versus first-party services (green/blue).

### Key components

| Component | Tier | Role |
|---|---|---|
| **Angular SPA (`AngularDMS`)** | Client | Dealer-facing UI; lazy-loaded feature modules (`session`, `sales`, `service`, `parts`, `accounts`, `master`, `ho`, `homedashboard`, `dmsreports`, `uvd-reports`, `UVD`); HTTP via `app/api-services/*`; JWT injected by `SessionService` interceptor; optional Electron desktop entry (`main.js`). |
| **Azure AD B2C / UMS** | Identity | Issues JWT for dealers / service principals; URL set: `umsLogin`, `umsLogin_WebApi`, `umsLogout`. |
| **Azure API Management** | Gateway | `validate-jwt` policy (issuer, audience, signature, expiry); routes to OnlineDMS_WebAPI; subscription keys per consumer. |
| **OnlineDMS_WebAPI** | Application | ASP.NET Web API on .NET 4.7.2 hosted in IIS; OWIN startup (`Global.asax`); Unity DI (`UnityResolver`); per-request auth filters; ~67 controllers. |
| **MicroDMS class libraries** | Application | `BusinessLayer` (~166), `BusinessEntities` (~297), `DataLayer`, `EntityObjects`, `ServiceLayer`, `CacheLibrary`, `ConfigHelper`, `ExceptionManager`, `Utilities`. |
| **DMSFunctionApp** | Application | Azure Function (Service Bus topic worker) for async fan-out — see `ServiceBusTopicFunction.cs`. |
| **SQL Server** | Data | Primary datastore — invoked via ADO.NET stored procedures from DataLayer. |
| **Oracle DB** | Data | Legacy datastore for specific reads (Service References → Oracle service). |
| **Redis** | Cache | Token + master cache via `RedisCacheLayer.cs`. |
| **Azure Blob Storage** | Storage | Direct browser uploads via `azure-storage/blob-storage.service.ts` (SAS); server-side via `Webhook/AzureBlobService`. |
| **Azure Service Bus** | Messaging | Topic for domain events; consumed by `DMSFunctionApp`. |
| **SAP / ZMC / Insurance Policy Upload** | External | SOAP integrations via `Service References/`. |
| **SendGrid / Infobip / TinySMS / Mahale / Otp.NET** | External | Notifications (Email / SMS / OTP). |
| **DigiSigner / EMS / NGD / ATP / BookingEngine 2.0** | External | Partner APIs via `ExternalAPIs/Implementations/*`; some inbound webhooks under `Webhook/`. |
| **Application Insights + OTLP collector** | Observability | Traces, logs and metrics (parallel pipelines). |

### Pros

- Clear tier separation (SPA / API / DB) with a hard auth boundary at APIM.
- Externalized identity (UMS / B2C) — multi-app SSO, central session control.
- Centralized BL + DTO catalogue makes feature growth predictable.
- OpenTelemetry + Application Insights give end-to-end traceability.
- Async fan-out (Service Bus) decouples slow side-effects from the hot request path.
- Redis caching shields hot lookups and reduces token-fetch fan-out.

### Cons

- .NET Framework 4.7.2 — modernization work required to move to .NET 8/.NET Core for cross-platform hosting and faster dependency uptake.
- Angular 6 frontend — major version upgrade required for security and ecosystem support.
- Some legacy Web Forms code paths (`MicroDMS.Web`) still active.
- A few high-traffic flows depend on synchronous SOAP calls to SAP / Oracle, increasing tail latency under partner slowdowns.
- DI graph relies on Unity (in maintenance mode upstream).

> Dependency services (B2C / APIM / SAP / Oracle / SendGrid / SMS / Service Bus / Blob / Redis / Insurance / DigiSigner / NGD / ATP / EMS / BookingEngine / OTLP / Application Insights) are highlighted in a distinct colour in [System Architecture](../diagrams/hld-system-architecture.md).

---

## Data Flow / Sequence Diagram

### Main user flows

1. **Login → Home dashboard** — Angular `session` module → UMS sign-in → JWT in browser; `SessionService` interceptor attaches `Authorization: Bearer <jwt>` to every API call.
2. **Authenticated read (e.g. master fetch / job-card list)** — SPA → APIM (`validate-jwt`) → controller → BL → DAL → SQL stored proc → JSON response → SPA render.
3. **Authenticated write (e.g. Job Card create)** — same hot path; BL applies rules, writes via DAL, optionally publishes a Service Bus event.
4. **Async fan-out** — `DMSFunctionApp` consumes the topic message and performs side-effects (downstream notifications, partner sync).
5. **Inbound webhooks** — Partner systems POST to `Webhook/*` endpoints (ATP, BookingEngine 2.0, BookingService, EnquiryService, CWIService, NotificationService). Filters validate signature / token and route into BL.

### Retry, error handling, failover

- **APIM** — `validate-jwt` failure → 401 short-circuited at the gateway; rate-limit / quota policies (where configured) protect the WebAPI from bursts.
- **Auth filters** — `JwtAuthorizationFilterAttribute` validates JWT (issuer, audience, signature, expiry); failures map to 401.
- **CORS preflight** — handled by `Application_BeginRequest` (allow-headers/methods, OPTIONS short-circuit).
- **Telemetry kill switch** — `OTEL_ENABLED=false` disables OpenTelemetry exports without code changes; OTLP endpoint is connectivity-tested at startup.
- **Database** — stored proc errors propagate through `MicroDMS.ExceptionManager.LogGeneration` → OTel logs; transactional writes use ADO.NET transactions.
- **Outbound integrations** — SAP / SOAP failures are caught and surfaced as 5xx with diagnostic info (`IncludeErrorDetailPolicy = Always`); RestSharp / HttpClient calls to partners rely on TLS 1.2.
- **Redis** — token cache miss falls back to a fresh `ApimTokenAcquisition` call.
- **Service Bus** — message handler in `DMSFunctionApp` benefits from native dead-lettering and retry on the topic subscription.

> Visualized in [Service Interaction](../diagrams/hld-service-interaction.md) and [Auth Flow](../diagrams/hld-auth-flow.md).

### Worked example — Sales Invoice creation

1. Dealer fills the Sales Invoice form in `sales` Angular module.
2. SPA calls `multi-vehicle-invoice.service.ts` → APIM `/OnlineSalesAPI/...`.
3. APIM `validate-jwt` passes → routes to `MultiVehicleInvoiceController`.
4. Controller resolves `MultiVehicleInvoiceBL` via Unity (`UnityResolver.BeginScope`).
5. BL applies tax + scheme rules (`CentralTaxProcessor`, `ATWSchemesBL`), calls DAL stored procs.
6. DAL executes a SQL transaction; on success, BL publishes a "Sales Invoice Created" event to Service Bus.
7. `DMSFunctionApp` consumes the event → triggers downstream syncs (e.g. SAP, partner notifications via `Webhook/NotificationService`).
8. BL returns a result DTO → controller serializes → APIM forwards → SPA updates UI.
9. Throughout the call, OpenTelemetry instrumentations (ASP.NET, HttpClient, SqlClient) emit spans; `LogGenerationOTel` emits structured logs.

---

## Deployment & Rollout Plan

> Visualized in [Deployment Topology](../diagrams/hld-deployment-topology.md).

### Topology

| Layer | Environment options |
|---|---|
| Angular SPA | Static hosting on Azure Storage static site / IIS virtual directory / CDN; QA + Prod use `--base-href ./` |
| Electron desktop | Built via `electron-packager` from the Angular bundle (`ele-build` script) |
| Web API | IIS app pool on Windows (Azure App Service Windows or Windows VM); .NET Framework 4.7.2 |
| DMSFunctionApp | Azure Functions runtime — Service Bus topic trigger |
| SQL Server | Managed Azure SQL or on-prem SQL (via secured network) |
| Redis | Managed Azure Cache for Redis |
| Service Bus | Azure Service Bus (Standard / Premium) |
| Azure Blob | General-purpose v2 |
| Application Insights | Azure resource per environment |
| OTLP collector | Customer-managed collector forwarding to APM backend |

### Promotion / rollout

1. Merge to integration branch → CI builds (`AngularDMS.yml`, `main.yml`).
2. Frontend bundle deployed to env target (dev / qa / prod) with the matching `environment.<env>.ts` file replacement (`fileReplacements` in `angular.json`).
3. Backend Web Deploy package deployed to target IIS app pool; `aspnet_regiis -pe` encrypts sensitive config sections.
4. Smoke tests: UMS sign-in, master fetch, Job Card list, Sales Invoice list, OTP send.
5. Production cut-over uses a phased ring (HO pilot dealers → tier-1 dealers → all dealers).
6. Roll back via redeploy of previous Web Deploy package; SPA roll back via swap of static bundle or pinned base href.

### Hotfix strategy

- Hotfix branch from current production tag.
- CI builds artefact; deploy to a staging slot; smoke test.
- Promote with no DB schema change where possible. For DB changes, ship migration script and gate with feature flag.

---

## Metrics to be Tracked

| Metric | Source | Threshold (proposed) |
|---|---|---|
| API request rate (req/s) | App Insights / OTel | environment-specific baseline |
| API P95 latency (read / write) | App Insights / OTel | 600 ms / 1.5 s |
| API error rate (5xx) | App Insights / OTel | < 0.5% over 5 min |
| Auth failure rate (401) | App Insights / OTel | < 1% over 5 min (excluding bot scans) |
| SQL P95 query time | OTel SqlClient instrumentation | < 250 ms |
| Redis hit ratio | App Insights / OTel | > 80% on token + master keys |
| Service Bus topic backlog | Azure Service Bus metrics | < 1000 messages |
| DMSFunctionApp invocation failures | App Insights | < 1% over 1 hour |
| OTLP export failures | Debug logs | non-zero triggers investigation |
| App Insights live metrics | App Insights | active alerts on rate / latency |
| SendGrid bounce / failure rate | SendGrid + App Insights | < 2% |
| SMS / OTP delivery failure | Provider + App Insights | < 2% |

---

## Data Analytics / Data Engineering metrics / tables

OpenTelemetry traces + logs (OTLP) and Application Insights are the canonical sources for operational analytics. Where business analytics is required (sales, service KPIs), data is exported from SQL Server to the central data lake by an existing ETL out of scope for this document. Any new flows added to the BL should ensure transactional logs include the `traceparent` (OTel) so that data engineering pipelines can correlate.

---

## Alternatives Considered

### Option A — Move OnlineDMS_WebAPI to .NET 8 / .NET Core today

- **Pros:** cross-platform hosting (Linux containers), faster dependency uptake, modern DI, native `IHostedService`, lower memory footprint.
- **Cons:** large surface area (~67 controllers, hundreds of BL/DTO types), legacy `System.Web.Http` references, SOAP service references rebuild, full QA cycle. Out of scope for this iteration; tracked as a multi-quarter migration.

### Option B — Replace Unity with the built-in DI

- **Pros:** removes Unity dependency, aligns with .NET 8 future state.
- **Cons:** requires .NET Core/.NET 8 migration; not viable on .NET Framework 4.7.2 without intermediate shim.

### Option C — Move all SOAP partner calls to async via Service Bus

- **Pros:** smooths tail latency, decouples partner slowness from user flows.
- **Cons:** loses synchronous validation semantics for some flows; requires per-flow feasibility analysis.

---

## Risks (If Any)

- **Legacy framework risk** — .NET 4.7.2 + Angular 6 are supported but lag current ecosystem. Security patches require careful tracking (libraries like `node-sass`, `protractor`, `jasmine` are in maintenance mode).
- **Partner dependency tail latency** — synchronous SAP / Oracle / Insurance calls in some flows can blow the API SLO if a partner slows down.
- **Secret hygiene** — `RSAKeys/`, SAP credentials, APIM subscription keys, SendGrid API key, SMS provider credentials must be sourced from KeyVault / encrypted config (`aspnet_regiis -pe`), never committed.
- **OpenTelemetry overhead** — high-volume flows can exhaust the BSP queue if `OTEL_BSP_*` settings are mis-tuned. Kill switch (`OTEL_ENABLED=false`) is the safety valve.
- **Dual-DB shape** — split between SQL Server and Oracle introduces consistency edge cases for cross-DB reads.
- **Token cache invalidation** — bad Redis state can cause stale APIM tokens; fall back path (re-acquire) is in place but should be alarmed.

---

## Appendix

### Glossary / Acronyms

- **AMC** — Annual Maintenance Contract
- **APIM** — Azure API Management
- **ASC** — Authorized Service Centre
- **ATP** — partner integration (Available-to-Promise)
- **ATW** — After-sales workflow / scheme
- **B2C** — Azure AD B2C
- **BL** — Business Layer
- **CWI** — Customer Wins Incentive (partner integration)
- **DAL** — Data Access Layer
- **DMS** — Dealer Management System
- **EMS** — Employee Management System (TVSM EMS API)
- **FSC** — Free Service Coupon
- **GRN** — Goods Receipt Note
- **HO** — Head Office
- **HLD** — High Level Design
- **JC** — Job Card
- **NGD** — partner integration
- **OTEL** — OpenTelemetry
- **OTLP** — OpenTelemetry Protocol
- **PSF** — Post-Sales Follow-up
- **RTO** — Regional Transport Office (vehicle registration)
- **SLA / SLO** — Service Level Agreement / Objective
- **SOAP** — Simple Object Access Protocol
- **SPA** — Single Page Application
- **TLS** — Transport Layer Security
- **UMS** — User Management System (Azure AD B2C-based)
- **UVD** — Used Vehicle Division

### References

- [TVS HLD Template](https://tvsmotorcompany.atlassian.net/wiki/spaces/DE2/pages/4209508450/High+Level+Design+Template)
- [Notification service integration with DIGI and DMS](https://tvsmotorcompany.atlassian.net/wiki/spaces/CPA/pages/4776755322)
- Source repos: `D:\DMS_DOMESTIC\ANGULAR_DMS`, `D:\DMS_DOMESTIC\MICRO_DMS\MicroDMS\OnlineDMS_WebAPI`

---

## 📌 Expected Outputs (per `.kiro/steering/HLD.md`)

### Architecture Diagram Description

A four-lane architecture: **Client (Angular SPA)** → **Edge / Auth (UMS · APIM)** → **Application (OnlineDMS_WebAPI + MicroDMS class libraries + DMSFunctionApp)** → **Data & External (SQL · Oracle · Redis · Blob · Service Bus · SAP · ZMC · Insurance · SendGrid · SMS · OTP · DigiSigner · EMS · NGD · ATP · BookingEngine · OTLP · Application Insights)**. The hot path is HTTPS + Bearer JWT from SPA through APIM (`validate-jwt`) into Web API → BL → DAL → SQL. Side legs: Redis caches tokens / hot lookups, Azure Blob handles file artifacts, Service Bus drives async fan-out into `DMSFunctionApp`. Telemetry is emitted via OpenTelemetry (ASP.NET / HttpClient / SqlClient instrumentations) plus Application Insights. Dependency services are highlighted in a distinct colour to identify third-party / managed boundaries.

### Service Interaction

Controllers in `OnlineDMS_WebAPI/Controllers` resolve dependencies via Unity (`UnityResolver`). Auth filters (`JwtAuthorizationFilterAttribute`, `UMSAuthenticationAttribute`, `HarithaAuthenticationAttribute`, `BasicAuthenticationAttribute`) run per request. The BL composes DAL calls (ADO.NET stored procs against SQL Server / Oracle), SOAP calls via Service References (SAP / ZMC / Insurance Policy Upload), and outbound REST via `ExternalAPIs/Implementations/*` (EMS / NGD / ATP / BookingEngine / TvsmEmsApi / EvDmsBookingApi). Inbound webhooks (`Webhook/*`) are handled by feature-specific controllers under the same auth chain. Async events flow through Azure Service Bus to `DMSFunctionApp`. Token acquisition (`ApimTokenAcquisition`) is cached in Redis (`RedisCacheLayer`).

### Infra Topology

Per environment (DEV / QA / PROD): IIS app pool hosts `OnlineDMS_WebAPI`; Azure Storage / IIS hosts the Angular bundle; Azure Functions runs `DMSFunctionApp`; Azure Service Bus carries topic events; Azure Cache for Redis backs token + master cache; SQL Server (Azure SQL or on-prem) is the primary datastore; Oracle covers legacy reads; Azure Blob Storage holds documents and uploaded artefacts; Application Insights is provisioned per environment; OTLP collector is customer-managed. APIM front-doors all API traffic and applies `validate-jwt`; UMS (Azure AD B2C) issues JWTs.

### Deployment Flow

CI workflows (`AngularDMS.yml`, `main.yml`) produce the SPA bundle (`dist/`) and the WebAPI Web Deploy package. Frontend deploys per env with the matching `environment.<env>.ts` file replacement (configured in `angular.json`); QA / Prod use `--base-href ./`. Backend deploys to the IIS target; encrypted appSettings via `aspnet_regiis -pe`. Smoke tests validate UMS sign-in, master fetch, Job Card / Sales Invoice flows. Rollout is phased through pilot dealers → tier-1 → all dealers. Rollback redeploys the previous Web Deploy package; SPA rollback swaps the static bundle. Hotfixes branch from the current production tag.

### External Integrations

- **Identity:** UMS / Azure AD B2C
- **Gateway:** Azure API Management (`validate-jwt`)
- **Data:** SQL Server, Oracle DB
- **Cache:** Redis (StackExchange.Redis)
- **Storage:** Azure Blob Storage
- **Messaging:** Azure Service Bus topic + `DMSFunctionApp`
- **Partner ERP / SOAP:** SAP, ZMC, Insurance Policy Upload (Service References)
- **Notifications:** SendGrid (Email), Infobip / TinySMS / Mahale (SMS), Otp.NET (OTP)
- **Partner REST:** DigiSigner, EMS / TVSM EMS API, EV DMS, NGD, ATP, BookingEngine 2.0, Notification Service (DIGI ↔ DMS)
- **Analytics:** Conviva (frontend), Time API (`timeapi.io`)
- **Observability:** Application Insights, OTLP collector

> See [External Integrations](../diagrams/hld-external-integrations.md).

---

_Source: ANGULAR_DMS + OnlineDMS_WebAPI_
