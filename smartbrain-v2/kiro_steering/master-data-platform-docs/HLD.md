# MDP — High Level Design (SmartBrain AI Format)

> **Service:** Master Data Platform (MDP)
> **Version:** 2.0
> **Last Updated:** July 2026
> **Source of truth:** Code in `src/main/java/com/tvsmotor/mdp/`

---

## System Purpose

The Master Data Platform (MDP) consolidates fragmented, point-to-point master-data integrations (dealer, vehicle product, vehicle pricing, parts, part-pricing, MnA) behind one domain model, one API contract, and one event contract — with a single audit trail. It replaces direct integrations between upstream enterprise systems (SAP, DMS, SharePoint) and downstream consumer channels (D2C web, mobile, reporting, partner channels).

**Problem it solves:** Each consumer channel previously integrated point-to-point with source systems, leading to inconsistent data representations, tight coupling to proprietary schemas, duplicated batch transformations, and no shared audit trail.

**Tier:** Tier 1 — Mission Critical. MDP is the source of truth for dealer, product, and pricing data consumed by customer-facing channels.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              UPSTREAM SOURCES                                │
│   SAP (ECC/S4) ─┐                                                          │
│   SharePoint ────┼──► Azure Data Lake ──► Azure Data Factory ──┐            │
│   DMS (MSSQL) ───────────────────────────────────────────────┐ │            │
└──────────────────────────────────────────────────────────────┼─┼────────────┘
                                                               │ │
┌──────────────────────────────────────────────────────────────▼─▼────────────┐
│                           APIM GATEWAY (EDGE)                                │
│   TLS termination · OAuth2 B2C enforcement · Rate limit (1000/min/appid)    │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                     AKS — MDP SERVICE (Spring Boot 3.5.16 / Java 17)         │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ REST Layer  │  │  SB Listeners│  │ Scheduled/   │  │  Cross-cutting  │   │
│  │ (Tomcat     │  │ (2 consumers │  │ Migration    │  │  AOP (Auth,     │   │
│  │  10.1.56)   │  │  dealer+dms) │  │ Jobs         │  │  Disable, Timed)│   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘   │
│         └────────────────┼─────────────────┘                   │            │
│                          ▼                                     │            │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │            SERVICE LAYER (Domain Modules)                     │           │
│  │  dealer · product · price · product_mna · product_part ·     │           │
│  │  part_price · batch_processing · migration · notification    │           │
│  └──────────────────────────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────────────────────┘
         │              │              │              │
    ┌────▼────┐    ┌───▼────┐    ┌───▼─────┐   ┌───▼──────────┐
    │ MySQL 8 │    │ Redis  │    │ Azure   │   │ DMS/MSSQL    │
    │ (JPA,   │    │ (Jedis │    │ Service │   │ (OnlineDMS,  │
    │ Envers) │    │ 5.2.0) │    │ Bus     │   │  read-only)  │
    └─────────┘    └────────┘    └─────────┘   └──────────────┘
                                       │
                    ┌──────────────────▼───────────────────────┐
                    │        DOWNSTREAM CONSUMERS               │
                    │  D2C Web · Mobile · Reporting · Partners  │
                    └──────────────────────────────────────────┘
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Modular Monolith** (not microservices) | Team/ops capacity doesn't justify micro-service overhead; clean module boundaries (dealer, product, price, product_mna, product_part, part_price) allow later extraction |
| **Redis as derived cache** (not source of truth) | All 10 cache regions rebuildable from MySQL; simplifies consistency model |
| **Event-driven + REST** (not event-only) | D2C journeys need synchronous reads; events used for change propagation alongside REST |
| **Soft-delete only** | Audit trail preserved; no physical DELETE SQL; Hibernate Envers 6.6.13 for full history |
| **Azure AD B2C OAuth2** | Centralized identity; client-credentials for app-to-app; 3 client types (SYSTEM, ADF, MDP_BFF) |
| **Forward-only migrations** | Schema always moves forward (v1.1 → v1.44+); expand-then-contract for non-breaking changes |
| **APIM at edge** | Offloads TLS, rate limiting (1000/min/appid), JWT signature verification from the service |
| **Session-based FIFO on Service Bus** | Dealer topic uses sessionId = `DEALER_{sapDealerCode}` to ensure ordered processing per dealer |
| **App-generated timestamps** | `createdAt`/`updatedAt` generated in application (CommonBaseEntity @PrePersist/@PreUpdate), not by DB |

---

## Scalability Approach

- **Stateless service** — all state externalized to MySQL, Redis, Service Bus → pods scale horizontally on AKS via HPA (CPU/memory)
- **Cache-first reads** — Redis (10 cache regions) absorbs read-heavy traffic; event-driven invalidation bounds staleness
- **Connection pooling** — HikariCP sized (min 20 / max 50) per pod; grows with pod count
- **Background processing** — ADF batch (9 batch types) & DMS migration run as async background jobs via `AsyncJobService` / `ParallelJobExecutor`
- **DMS read replicas** — `applicationIntent=ReadOnly` routes scans to secondary
- **Per-environment isolation** — separate ACR, AKS namespace, MySQL, Redis, SB per env; blast radius contained
- **Spring Retry** — `@Retryable` on cache operations (3-5 attempts) absorbs transient Redis hiccups
- **Service Bus concurrency** — dealer topic: 1 concurrent session (strict ordering); DMS topic: 250 concurrent sessions (throughput)

---

## Error Handling Strategy

| Failure Scenario | Behavior |
|-----------------|----------|
| Redis unavailable | Reads fall back to DB after Spring Retry (3-5 attempts); writes still persist to MySQL; cache repopulates on next read |
| DMS unreachable | Synchronous API path unaffected (migration-only); migration jobs retry |
| Service Bus unreachable | API responses still succeed; outbound publish fails → SB client-level retry; consumers resume on recovery |
| Notification Service unreachable | Dealer operations continue; email retry via OkHttp + Spring Retry |
| Invalid/expired token | 401 response with clear error message (`"Invalid token"`, `"Token expired"`, `"Access Denied"`); audit logged |
| Upstream schema drift (SAP/DMS) | Strict validation in batch processors (`Validateable`/`Sanitizeable`); per-row errors recorded in ADF digest; failure-alert email sent |
| Batch processing row failure | Per-row try/catch; failures recorded in digest table; batch continues; email on threshold |

**Global exception handling:** `RestExceptionHandler` (@ControllerAdvice) maps all exceptions to typed HTTP responses (400/401/405/500). Stack traces gated by `SHOW_HTTP_500_DETAILS` flag (always false in prod).

---

## Deployment Topology

| Component | Technology | Version/Details |
|-----------|-----------|-----------------|
| Compute | Azure Kubernetes Service (AKS) | HPA, liveness/readiness via Actuator |
| Container | Multi-stage Docker | Maven 3.9.x build → Amazon Corretto 17 runtime, `-XX:MaxRAMPercentage=75`, TZ=Asia/Kolkata |
| Registry | Azure Container Registry (per env) | Image built once, promoted across environments |
| Gateway | Azure API Management (APIM) | TLS, rate limiting, JWT enforcement |
| Database | Azure Database for MySQL 8 | Primary OLTP store, HikariCP 20-50 |
| Cache | Azure Cache for Redis | Jedis 5.2.0, standalone mode |
| Messaging | Azure Service Bus | 7 topics, PEEK_LOCK, 30-min idle timeout |
| CI/CD | Azure DevOps | Build → test → SonarQube → AST scan → push → deploy (manual approval UAT/Prod) |
| Security scan | AST Image Scan + SonarQube | Deploy/PR gates |
| Logging | Logback (logback-spring.xml) | Structured JSON logs, per-request transactionId |

**Environments:** `local` → `dev` → `uat` → `prod` (fully isolated stack each)

**Pipelines:** `ci-pipeline.yaml`, `cd-pipeline.yaml`, `azure-pipelines/{uat,prod}.ci.yml`, `azure-pipelines/{uat_cd_yaml, prod.cd.yml}`, `AST_Image_Scan_MDP_Pipeline.yml`, `sonar_ci_pr_pipelines.yml`

---

## Data Flow Summary

1. **SAP/SharePoint** → files land in **Azure Data Lake**
2. **Azure Data Factory** orchestrates transfer and triggers `GET /v1/de-pipeline/trigger/{type}`
3. **MDP batch processor** (`BatchJobProcessorFactory` selects from 9 processor types) validates, sanitizes, upserts into MySQL canonical tables
4. **Service Bus** events published to 7 topics for downstream consumers
5. **Redis cache** invalidated/repopulated (10 cache regions)
6. **Downstream consumers** (web/mobile/reporting/partners) read via REST or subscribe to SB events
7. **DMS migration** runs as async background job (`/v1/dms-import/trigger`) reading from MSSQL OnlineDMS (read-only)
8. **Inbound SB events** — dealer topic (1 concurrent session, strict FIFO) and DMS topic (250 concurrent sessions) processed by `DealerDataConsumerService` and `DmsDataConsumerService`

---

## Service Bus Architecture Detail

| Topic | Direction | Subscription | Max Concurrent Sessions | Consumer Class |
|-------|-----------|-------------|------------------------|----------------|
| `dealerData` | Bi-directional | `mdp` | 1 (strict FIFO per dealer) | `DealerDataConsumerService` |
| `dmsDealerData` | Bi-directional | `mdp` | 250 (high throughput) | `DmsDataConsumerService` |
| `productVehicleData` | Outbound only | — | — | Product SB sender |
| `priceVehicleData` | Outbound only | — | — | Price SB sender |
| `productMnaData` | Outbound only | — | — | MnA SB sender |
| `partData` | Outbound only | — | — | Part SB sender |
| `partPriceData` | Outbound only | — | — | PartPrice SB sender |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| MySQL bottleneck during batch ingestion (9 batch types) | HikariCP pool tuning (20-50), batch chunking, ParallelJobExecutor |
| Service Bus consumer lag during bursts | Horizontal pod scaling; DMS topic sized at 250 concurrent sessions |
| Cache stampede on cold start | Cache warming after deploy; jittered TTLs; @Retryable (5 attempts) |
| Upstream schema drift | Strict validation via `Validateable`/`Sanitizeable` + per-row error recording + failure-alert emails |
| Token misconfiguration | Required role claim (`mdp.api`); alarms on auth-failure spikes |
| DMS read pressure | `applicationIntent=ReadOnly`; async migration triggered by `/trigger` endpoint |
| Modular-monolith blast radius | Strong module boundaries; service-to-service calls only (never cross-module repository access) |
| Unofficial branch data pollution | `isDealerDataPushAllowed()` filters out unofficial branches and branches with tempDmsBranchSequence=1 |

---

*For detailed implementation specifics, see `LLD.md`. For full API contract, see `API_SPEC.md`. For comprehensive architecture with Mermaid diagrams, see `HIGH_LEVEL_DESIGN.md`.*
