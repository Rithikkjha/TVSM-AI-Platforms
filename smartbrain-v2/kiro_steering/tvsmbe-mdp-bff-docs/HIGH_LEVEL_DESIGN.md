# High Level Design — `tvsmbe-mdp-bff`

> Architecture document for external engineering partners.
> Follows the [TVS Motor D&AI HLD Template](https://tvsmotorcompany.atlassian.net/wiki/spaces/DE2/pages/4209508450/High+Level+Design+Template).
> No production secrets, credentials, or confidential business logic are included. Configuration values are referenced by environment-variable name only.

| Field | Value |
|---|---|
| Service name | `tvsmbe-mdp-bff` |
| Repository layout | Two Spring Boot services in one repo: `inbound/`, `outbound/` |
| Runtime | Java 17, Spring Boot 3.5.x, Tomcat (embedded), MySQL, Azure Service Bus |
| Audience | External engineering partners |
| Owner | TVS Motor — D&AI / D2C Engineering |

---

## Overview

`tvsmbe-mdp-bff` is the Backend-For-Frontend layer for the **MDP (Master Data Platform) — Dealer module**. It abstracts MDP from a) front-end and partner clients that need to read dealer data, and b) downstream partner systems that need to react to dealer changes.

It exists for two reasons:

1. To centralize **read access to MDP dealer data** for clients (web, mobile, internal services), with consistent auth, validation, and error semantics.
2. To **fan out MDP dealer-data change events** to multiple external partner systems (Knowlarity, Single Interface, LatLong, Daksha) reliably, asynchronously, and with audit/alerting.

## Tier Classification

**Tier 2 — Business Critical but not Life-or-Death.**

Rationale: The service is on the critical path for dealer-onboarding journeys (dealer outlets visible on partner platforms, dealer virtual numbers provisioned for customer calls), but a temporary outage degrades dealer-side capabilities (call masking, locator listing, partner sync) rather than blocking end-customer transactions on the primary platform. Failures are recoverable — events queued in Azure Service Bus are durable, and failed events are persisted in `failed_mdp_message_exception` for replay.

## Background

- The MDP dealer module is the source of truth for dealer master data inside TVS Motor.
- Several partner systems (telephony, locator, listing, internal CRM-style platforms) need a consistent view of that data, but pulling from MDP directly would couple every partner to MDP's API and auth model and produce N×M integration sprawl.
- Front-end and partner clients also need to read dealer data, but should not be given MDP credentials directly.
- The BFF pattern lets us:
  - keep client/partner contracts decoupled from MDP's internal contract,
  - implement cross-cutting concerns (Azure B2C auth, retries, audit, validation) in one place,
  - introduce per-partner orchestration (e.g., Knowlarity virtual-number assignment is a 3-step workflow) without polluting MDP.
- The split into **inbound** (synchronous reads + webhooks) and **outbound** (async fan-out from MDP events) was chosen to keep the request-serving path independent of long-running, retry-heavy outbound work and to let the two scale independently.

## Requirements

### Functional
- Expose REST APIs to:
  - fetch a dealer by SAP dealer code,
  - fetch dealers by pincode,
  - fetch dealers by filter (type, statuses, flags, search term).
- Accept inbound webhooks from external partners on a path-typed URL (`/{module}/{client}/{event}`).
- Consume MDP dealer change events from an Azure Service Bus topic and propagate them to the configured set of external clients.
- Per partner, implement the partner-specific workflow:
  - **Knowlarity**: assign / update / un-assign virtual numbers based on dealer status, type, and configured flags.
  - **Single Interface**: create or close outlet listings.
  - **LatLong**: forward dealer payload to the dealer-locator API.
  - **Daksha**: forward dealer payload to the Daksha dealer-update API.
- Persist an append-only audit trail for every external interaction (request/response, timing, status).
- Persist failed events so they can be retried or analyzed.
- Send email alerts (with cooldown) when a partner integration fails repeatedly.

### Non-functional
- **Availability**: target 99.5% (Tier 2) — service is horizontally scalable and stateless.
- **Latency**: read APIs P95 < 1s under nominal load (driven by MDP latency + 1 hop). Outbound fan-out is async; per-event end-to-end SLA is best-effort within minutes, bounded by retry backoff (5 attempts, exponential 1s → 10s).
- **Durability**: no message loss on outbound — Azure Service Bus PEEK_LOCK + manual `complete()`; failed messages persisted in DB.
- **Observability**: every external API call is timed (StopWatch), logged, and audit-rowed; periodic JVM/executor metrics emitted every 60s.
- **Security**: all calls to MDP and to the internal Notification API use Azure AD B2C OAuth2 client-credentials Bearer tokens; partner systems use partner-issued static tokens passed via configured env vars.
- **Configurability**: every URL, token, and behavior toggle is externalized as an environment variable; per-environment property files for `local`, `dev`, `uat`, `prod`.
- **Idempotency**: outbound integrations are designed so a retried message produces the same end state (e.g., assign-or-update for Knowlarity, create-or-close for Single Interface).

## Current Architecture (HLD)

This service is the current implementation; there is no separate "current vs proposed". A summary of the live architecture is below; the full diagram is in **Proposed Architecture**.

- Two Spring Boot 3 services packaged as separate Docker images.
- Shared MySQL schema for audit + failure tracking.
- Azure Service Bus topic as the integration pipe from MDP.
- Azure AD B2C as identity provider for service-to-service auth with MDP and Notification.

## Proposed Architecture (HLD)

### System architecture (1)

```
                     ┌────────────────────────────────────────┐
                     │             Azure AD B2C               │ ◀── (dependency)
                     │     (OAuth2 client-credentials)        │
                     └───────────────────▲────────────────────┘
                                         │ Bearer
   ┌──────────────────────┐              │              ┌──────────────────────┐
   │  Clients / Webhooks  │              │              │       MDP API        │ ◀── (dependency)
   │ (web, mobile, SI hk) │              │              │  (master data)       │
   └──────────┬───────────┘              │              └──────────▲───────────┘
              │ HTTPS                    │   read APIs              │ write APIs
              ▼                          │                          │
    ┌──────────────────────┐             │             ┌────────────┴─────────────┐
    │   INBOUND BFF        │─────────────┴────────────▶│      OUTBOUND BFF        │
    │  (Spring Boot)       │                           │     (Spring Boot)        │
    │  /mdp-bff            │                           │  /mdp-bff-outbound       │
    │                      │                           │                          │
    │  REST controllers    │                           │  Service Bus consumer    │
    │  Webhook intake      │                           │  + DealerDataProcessor   │
    │  MDP read calls      │                           │    factory               │
    │  Audit logging       │                           │  + 20-thread async pool  │
    └──────────┬───────────┘                           │  + Failure handler       │
               │                                       │  + Notification sender   │
               │       ┌────────────────────────┐      └──┬──────┬──────┬──────┬──┘
               └──────▶│       MySQL DB         │◀────────┘      │      │      │
                       │  audit_log             │                ▼      ▼      ▼
                       │  failed_mdp_message_*  │ ┌──────────┐ ┌────┐ ┌────────┐ ┌──────┐
                       │  failure_event_type_*  │ │Knowlarity│ │ SI │ │LatLong │ │Daksha│ ◀── (dependencies)
                       └────────────────────────┘ └──────────┘ └────┘ └────────┘ └──────┘
                                                            ▲
                                       ┌────────────────────┘
                                       │ produces events
                                ┌──────┴──────────────┐
                                │ Azure Service Bus   │ ◀── (dependency)
                                │  topic: dealer_data │
                                │  sub:   mdp_bff     │
                                └─────────▲───────────┘
                                          │
                                  ┌───────┴────────┐
                                  │  MDP (source)  │ ◀── (dependency)
                                  └────────────────┘
```

Boundaries:
- **Inbound BFF** owns synchronous HTTP traffic and webhook intake.
- **Outbound BFF** owns asynchronous, retry-heavy partner fan-out.
- Both share the MySQL schema for audit + failure tracking. They do not call each other.

Pros:
- Clear read/write split → independent scaling, blast-radius isolation.
- Strategy-pattern fan-out makes adding a partner localized (one processor + one caller class + one enum entry).
- Externalized config + per-profile properties make environment promotion mechanical.

Cons / known limitations:
- Inbound and outbound share a database — schema changes need to be coordinated.
- Service Bus listener is configured with a single subscription `mdp_bff`; horizontal scaling of outbound shares load via session-aware processing (max 10 concurrent sessions per pod).
- Schema migrations are applied manually from `inbound/src/main/resources/db/migrations/v*.sql` (no Flyway/Liquibase wiring).
- Cache configuration uses Spring's default `CacheManager` (`ConcurrentMapCacheManager`) — not distributed; B2C tokens are effectively per-pod.

### Major components / services (2)

#### Inbound BFF (`com.tvsmotor.bff`)
| Component | Type | Responsibility |
|---|---|---|
| `BffApplication` | Bootstrap | Enables `@EnableCaching`, `@EnableRetry`, `@EnableScheduling` |
| `MdpController` | REST | Read endpoints under `/v1/mdp` |
| `WebHookController` | REST | Webhook intake at `/webhook/v1/{module}/{client}/{event}` |
| `TestController` | REST | Health/diagnostics |
| `MdpDealerOperationsService` | Service | MDP read calls (auth + retry + response normalization) |
| `WebHookService` + `SingleInterfaceWebhookHandlerService` | Service | Webhook routing per `MdpModule` × `ExternalClient` × `WebHookEventType` |
| `AzureB2CTokenGenerationService` | Service | OAuth2 client-credentials token fetch |
| `OkHttpService` | Service | Generic OkHttp wrapper with timing |
| `AuditLogService` | Service | Persist audit rows (4000-char cap) |
| `CacheService` | Service | Typed wrapper over Spring `CacheManager` |
| `RestExceptionHandler` | `@ControllerAdvice` | Global error mapping |
| `Context` | ThreadLocal | Per-request `userId`, `userToken`, `uuid` |
| `CronService` | `@Scheduled` | 60s JVM-metric emission |

#### Outbound BFF (`com.tvsmotor.mdp_bff.outbound`)
| Component | Type | Responsibility |
|---|---|---|
| `OutboundApplication` | Bootstrap | Enables `@EnableCaching`, `@EnableRetry`, `@EnableScheduling` |
| `BffServiceBusConfig` | Config | Builds the `ServiceBusProcessorClient` bean (PEEK_LOCK, sessions) |
| `MdpDealerDataConsumerService` | Service | Deserializes incoming Service Bus messages; enters fan-out |
| `DealerDataPasserService` | Service | Parallel fan-out across configured external clients |
| `DealerDataProcessor` (interface) + `DealerDataProcessorFactory` | Strategy | Resolves per-client processor |
| `KnowlarityDealerDataProcessorService` + `KnowlarityApiCallerService` | Service | Knowlarity assign/update/remove flows |
| `SingleInterfaceDealerDataProcessorService` + `SingleInterfaceApiCallerService` + `SingleInterfaceOperationService` | Service | Single Interface create-outlet / close-outlet |
| `LatLongDealerDataProcessorService` + `LatLongApiCallerService` | Service | LatLong dealer-data forwarding |
| `DakshaDealerDataProcessorService` + `DakshaApiCallerService` | Service | Daksha dealer-update forwarding |
| `MdpDealerOperationsService` | Service | MDP write calls (`mapDealerWithKNumber`, `unassignKNumber`) |
| `AsyncJobService` | Service | Fixed `ThreadPoolExecutor` (size=20) for client-isolated work |
| `FailedMessageExceptionHandlerService` | Service | Persists failures + decides whether to alert |
| `FailureEventTypeInfoService` | Service | Per-event-type alert cooldown bookkeeping |
| `NotificationSenderService` | Service | Posts to internal Notification email API |
| `GmbCommonService` | Service | Dealer-eligibility + address-merge utilities shared across processors |
| `CronService` | `@Scheduled` | 60s JVM + executor metric emission |

#### Shared persistence model
- `audit_log` — append-only audit trail (`tag` enum, `metadata` ≤ 4000 chars, `transaction_id`).
- `failed_mdp_message_exception` — DLQ-style replay store for outbound failures.
- `failure_event_type_info` — per-failure-type alert cooldown timestamps.
- All entities extend `BaseEntity` with Hibernate Envers `@Audited` (history tables auto-managed).

### Deployment architecture (3)

- Each service is built into its own Docker image via a multi-stage Dockerfile (Maven 3.9 + Amazon Corretto 17 build → Corretto 17.0.18 runtime). Containers run with `-XX:MaxRAMPercentage=75`, timezone `Asia/Kolkata`, exposing port `8080`.
- CI/CD: per-module pipelines in `inbound/ci-pipeline.yaml`, `inbound/cd-pipeline.yaml`, and the equivalents under `outbound/`, plus SonarQube (`sonar_ci_pr_pipelines.yml`) and AST image scans (`AST_*_Pipeline.yml`).
- Deployment target is a Kubernetes-style container platform (typical for TVS Motor BFFs); each service is deployed as a separate workload behind an HTTPS ingress (`/mdp-bff` and `/mdp-bff-outbound` context paths).
- Profile selection via the `ACTIVE_ENVIRONMENT` env var (`local|dev|uat|prod`) which Spring resolves into the matching `application-<env>.properties`.
- Both services run with `spring.main.web-application-type` defaulted (web). The outbound test endpoints are useful as readiness/liveness signals.
- Stateless replicas: scaling is done by adding pods. Outbound shares load across replicas via the single Service Bus subscription `mdp_bff` (Azure handles fan-out across consumers).

### Database interactions (4)

- **Engine**: Azure Database for MySQL (8.x, JDBC URL `jdbc:mysql://${DATABASE_HOST_URL}:3306/${DATABASE_NAME}`).
- **ORM**: Spring Data JPA + Hibernate 6 with Envers auditing.
- **Connection pool**: HikariCP defaults (Spring Boot starter).
- **Schema migrations**: SQL files under `inbound/src/main/resources/db/migrations/v*.sql` applied manually as part of release.
- **Tables**:
  | Table | Owner | Purpose |
  |---|---|---|
  | `audit_log` | both | Append-only audit, indexed by `tag` |
  | `failed_mdp_message_exception` | outbound | Failed message replay store; `mdp_dealer_data` LONGTEXT contains the raw MDP payload |
  | `failure_event_type_info` | outbound | Cooldown timestamps for per-failure-type email alerts; UNIQUE on `failure_event_type` |
  | `*_AUD` (envers) | both | Auto-generated history tables |
- **Access patterns**:
  - Audit writes are fire-and-forget (saved within the request thread but failures are logged, not propagated).
  - Failure persistence and notification are wrapped in `@Transactional`.
  - Reads on `failure_event_type_info` happen on every failure (one row per `FailureEventType`); volume is small.
- **Tests** use H2 in-memory DB with `application.properties` from `src/test/resources/`.

### API integrations (5)

#### Provided REST APIs (Inbound, context `/mdp-bff`)
| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/mdp/dealer/{sapDealerCode}` | Single dealer lookup |
| POST | `/v1/mdp/dealer/basedOnFilters` | Filter by type, statuses, flags, search |
| GET | `/v1/mdp/dealers?pincode={pincode}` | Dealers for a pincode |
| POST | `/webhook/v1/{mdpModule}/{externalClient}/{webHookEventType}` | Generic webhook intake |
| GET | `/v1/test/hello` | Diagnostics |
| GET | `/swagger-ui/index.html`, `/v3/api-docs` | API documentation (springdoc) |

#### Provided REST APIs (Outbound, context `/mdp-bff-outbound`)
| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/test/health` | Diagnostics + property/env introspection |
| GET | `/v1/test/hello` | Diagnostics + executor stats |

#### Consumed APIs
| System | Endpoint(s) | Method | Auth |
|---|---|---|---|
| MDP — read | `/mdp/v1/dealer/{code}`, `/mdp/v1/dealers/basedOnFilters`, `/mdp/v1/dealers` | GET / POST | Azure B2C Bearer |
| MDP — write | `/mdp/v1/dealer/mapDealerWithKNumber`, `/mdp/v1/dealer/{code}/unassignKNumber` | POST | Azure B2C Bearer |
| Azure AD B2C | `${AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL}` | POST (form-urlencoded) | Client ID + Secret |
| Knowlarity | `${KNOWLARITY_K_NUMBER_API_URL}` | GET (`query_type=fetch|update|delete`) | Static `auth` header token |
| Single Interface | `${SI_OUTLET_API_BASE_URL}/v1/Outlets/Add`, `/v1/Outlets/Close` | POST JSON | Static `auth` header token |
| LatLong | `${LATLONG_DEALER_DATA_API_URL}` | POST JSON + `access_token` query | Token |
| Daksha | `${DAKSHA_DEALER_UPDATE_API_URL}?r=client_api/dealerCreationAPI/JxGetDealerCreationData` | POST JSON | `token` header |
| Internal Notification | `${NOTIFICATION_BASE_URL}/api/v1/notification/email` | POST JSON | Azure B2C Bearer |

All outbound HTTP uses OkHttp 4.12, all calls are wrapped in Spring `@Retryable` (5 attempts, 1s → 10s exponential, multiplier 2.0), and every call writes an `audit_log` row tagged with the call type.

### Authentication / authorization flow (6)

This service does **not** authenticate the end user. Its role is service-to-service.

- **Outgoing — to MDP and Notification**: OAuth2 **client-credentials** against Azure AD B2C.
  1. `AzureB2CTokenGenerationService` posts `grant_type=client_credentials`, `client_id`, `client_secret`, `scope` (form-urlencoded) to `${AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL}`.
  2. The returned access token is wrapped as `Bearer %s` and sent in the `Authorization` header on each MDP / Notification call.
  3. The token call itself is `@Retryable` (5 attempts) on `ExternalServiceException`. There is currently **no positive caching** of the token — every call generates a fresh one. (`CacheName.MDP_AUTH_B2C_TOKEN` exists but is not wired into the token generator at the time of writing.)

- **Outgoing — to Knowlarity / Single Interface / LatLong / Daksha**: partner-issued **static tokens** stored as env vars and sent in the partner's expected header (`auth`, `token`) or as a query parameter (`access_token`).

- **Incoming — REST**: there is no application-level authn/authz on the controllers themselves. Trust is established at the network/ingress layer (private VNet / API gateway). Path-typed validation is used on webhooks (the path enums `MdpModule`, `ExternalClient`, `WebHookEventType` are validated by Spring's path-variable type binding; an unknown value yields HTTP 400).

- **Inputs are validated and sanitized** in service code via `GeneralUtils` and per-DTO `Validateable.validate(...)` / `Sanitizeable.sanitizeIncomingData(...)` implementations.

### External systems (7)

| System | Type | Direction | Criticality |
|---|---|---|---|
| MDP | Internal master-data API | bi-directional | Critical |
| Azure AD B2C | Identity provider | dependency | Critical (hard auth gate) |
| Azure Service Bus | Message broker | inbound to outbound BFF | Critical (only event source) |
| Azure Database for MySQL | Datastore | bi-directional | Important (audit + replay) |
| Knowlarity | Telephony / virtual-number provider | outbound | Important |
| Single Interface | Outlet / listing platform | outbound | Important |
| LatLong | Dealer-locator | outbound | Important |
| Daksha | Internal dealer-data consumer | outbound | Important |
| Internal Notification API | Email-sending platform | outbound | Best-effort |

### Infrastructure dependencies (8)

- Container orchestration platform (Kubernetes-style) with HTTPS ingress.
- Azure Database for MySQL — connectivity from both pods.
- Azure Service Bus namespace and topic; subscription `mdp_bff` must exist before outbound starts.
- Azure AD B2C tenant/app registration with the configured `client_id`/`client_secret`/`scope`.
- Outbound network egress to Knowlarity, Single Interface, LatLong, Daksha, MDP, and Notification endpoints.
- Container registry for built images.
- Log aggregation (Spring Boot writes to stdout in the configured format).
- Maven repository proxy (build time only).

Configuration is driven entirely by environment variables resolved into `application-<env>.properties`. The README lists all expected env vars without real values.

### High-level sequence flows (9)

#### Sequence 1 — Read dealer by SAP code (Inbound, sync)
```
Client                    Inbound BFF                Azure B2C            MDP API              MySQL
  │  GET /v1/mdp/dealer/{code} │                       │                    │                     │
  │──────────────────────────▶ │                       │                    │                     │
  │                            │ validate + sanitize   │                    │                     │
  │                            │ getAzureB2CBearerToken│                    │                     │
  │                            │──────────────────────▶│                    │                     │
  │                            │◀──────────────────────│  access_token      │                     │
  │                            │ GET /mdp/v1/dealer/{code} (Bearer)         │                     │
  │                            │───────────────────────────────────────────▶│                     │
  │                            │◀───────────────────── 2xx + payload ──────│                     │
  │                            │ deserialize → MdpDealerData                                      │
  │                            │ (on non-2xx)  → AuditLogService.saveLog ─────────────────────── ▶│
  │  200 OK GeneralResponse   ◀│                                                                   │
  │◀───────────────────────────│                                                                   │

Failure paths:
- 4xx from MDP → mapped 400/401 GeneralResponse.errorMessage
- 5xx / IOException → @Retryable up to 5 attempts; final failure → ExternalServiceException → 500 via RestExceptionHandler
- ValidationException on input → 400 via RestExceptionHandler
```

#### Sequence 2 — Webhook intake (Inbound, sync)
```
SI/Partner                Inbound BFF                MySQL
  │ POST /webhook/v1/DEALER/SINGLE_INTERFACE/{event} │
  │─────────────────────────────────────▶ │
  │                                       │ JsonHelperService.toJson(payload)
  │                                       │ AuditLogService.saveLog(INCOMING_WEBHOOK) ─▶│
  │                                       │ switch(MdpModule, ExternalClient)            │
  │                                       │   → SingleInterfaceWebhookHandlerService     │
  │                                       │   → ExternalClient.shouldProcessFor(event)?  │
  │                                       │       yes → process; no → log+skip           │
  │ 200 OK                               ◀│
```

#### Sequence 3 — MDP event fan-out (Outbound, async)
```
MDP        ServiceBus           Outbound BFF                            Partner APIs / MDP write             MySQL
 │ publish  │                     │                                                  │                          │
 │────────▶ │                     │                                                  │                          │
 │          │ deliver (PEEK_LOCK) │                                                  │                          │
 │          │────────────────────▶│ MdpDealerDataConsumerService.consumeMessage      │                          │
 │          │                     │ Context.setValues(transactionId)                 │                          │
 │          │                     │ AuditLog(SAVED_SERVICE_BUS_MESSAGE) ─────────────────────────────────────── ▶│
 │          │                     │ DealerDataPasserService.sendDealerDataToExternalClients                      │
 │          │                     │ for each client in MDP_BFF_EXTERNAL_CLIENTS (parallel):                      │
 │          │                     │   AsyncJobService.submitJob(() -> processor.processData(payload))            │
 │          │                     │     ┌───────────────────────────────────────────┐                            │
 │          │                     │     │ Per-client processor                      │                            │
 │          │                     │     │  GmbCommonService.shouldProcessDealerData?│                            │
 │          │                     │     │  build request → @Retryable HTTP call ──▶ │ partner / MDP write API    │
 │          │                     │     │  AuditLog(<call-specific tag>) ──────────────────────────────────────── ▶│
 │          │                     │     │  on failure (non-retryable):              │                            │
 │          │                     │     │    throw FailedMdpMessageException        │                            │
 │          │                     │     │    FailedMessageExceptionHandlerService:  │                            │
 │          │                     │     │      save → failed_mdp_message_exception ────────────────────────────── ▶│
 │          │                     │     │      shouldTriggerMailFor? yes →          │                            │
 │          │                     │     │        NotificationSenderService.send ──▶ │ Notification API           │
 │          │                     │     │        update failure_event_type_info ───────────────────────────────── ▶│
 │          │                     │     └───────────────────────────────────────────┘                            │
 │          │                     │ context.complete() ── ACK ───┐                                               │
 │          │◀───────────────────────────────────────────────────┘                                               │
```

#### Sequence 4 — Knowlarity virtual-number assignment (3-step, inside Sequence 3)
```
Outbound BFF              Knowlarity              MDP API
  │ callPoolApi(panel_type, fetch) ─▶│
  │◀── pool list ────────────────────│
  │ pick top number, audit
  │ mapDealerWithKNumber ─────────────────────────────▶│
  │◀── 2xx + KnowlarityFallbackNumber ─────────────────│
  │ callDealerUpdateApi(update, fallbackNumber) ─▶│
  │◀── 2xx ───────────────────────────────────────│
```
If the pool is empty: `KNOWLARITY_CALL_POOL_API_EMPTY` failure → DB row + alert email (with cooldown).

### Scalability and resiliency considerations (10)

#### Scalability
- **Stateless pods** — both services can be scaled horizontally without coordination.
- **Inbound** scales linearly with HTTP load. The bottleneck is MDP's response time and Azure B2C token issuance (no caching today; see Risks).
- **Outbound** scales by adding replicas. Service Bus distributes messages across consumers; per pod, concurrency is bounded by:
  - `maxConcurrentSessions = 10` on the `ServiceBusProcessorClient`,
  - `AsyncJobService` thread pool of 20 (per-pod).
- The **per-partner fan-out** is `parallelStream` over `MDP_BFF_EXTERNAL_CLIENTS`, so adding a partner does not slow other partners on the same message.

#### Resiliency
- **Retries** — every external HTTP call is `@Retryable(maxAttempts=5, backoff=@Backoff(delay=1000, maxDelay=10000, multiplier=2.0))`. Notification has 3 attempts.
- **Message durability** — Service Bus PEEK_LOCK + manual `complete()`. If processing throws, the message is redelivered; if all retries are exhausted at the message level, Service Bus moves it to its DLQ (per topic configuration).
- **Application-level DLQ** — non-retryable failures are persisted to `failed_mdp_message_exception` with the original MDP payload, the partner client, the response code and a priority, enabling offline replay.
- **Alert cooldown** — `FailureEventTypeInfoService` ensures only one email per `FailureEventType` per `nextEmailBackoffTimeInHrs` (currently 1h), preventing alert storms.
- **Bulkhead** — outbound work runs in a fixed 20-thread pool; spikes are queued, not amplified.
- **Timeouts** — OkHttp client is configured with `readTimeout(0)` (no read timeout). Connect / write timeouts use OkHttp defaults. *(Tracked as a risk.)*
- **Circuit breaking** — not implemented. Retries + alert backoff are the only failure-control today.
- **Idempotency** — partner workflows are designed so a retry produces the same end state (assign-or-update for Knowlarity, create-or-close for SI).
- **Audit trail** — every external interaction creates a row in `audit_log`, supporting forensic analysis.

## Data Flow / Sequence diagram

See the four sequences in **High-level sequence flows (9)** above. Worked example:

> An MDP dealer transitions from `PRE_ACTIVE` to `ACTIVE` for a BRANCH dealer. MDP publishes the change.
> 1. Outbound BFF picks the message off the `mdp_bff` subscription.
> 2. `DealerDataPasserService` fans out to Knowlarity, Single Interface, LatLong, Daksha (whichever are configured in `MDP_BFF_EXTERNAL_CLIENTS`).
> 3. Knowlarity processor: dealer has no virtual number yet → `K_NUMBER_NEEDED` flag check → pool API call → number picked → MDP `mapDealerWithKNumber` → Knowlarity `dealer-update`. Audit rows logged after each step.
> 4. Single Interface processor: BRANCH eligibility passes (`tempDmsBranchSequence > 1`, parent AMD code present, address + showroom manager present) → POST `/v1/Outlets/Add`.
> 5. LatLong + Daksha processors: forward the payload as-is.
> 6. Service Bus message ACK'd. If any partner call exhausted retries, a row is persisted in `failed_mdp_message_exception` and (subject to cooldown) an email is sent via the Notification API.

## Deployment & Rollout Plan

- **Branching/CI**: `ci-pipeline.yaml` builds the module; `cd-pipeline.yaml` deploys; `sonar_ci_pr_pipelines.yml` runs static analysis on PRs; `AST_*_Pipeline.yml` runs container/image security scans for UAT/PROD.
- **Environments**: `local` → `dev` → `uat` → `prod`. Profile is selected by `ACTIVE_ENVIRONMENT`.
- **Image build**: multi-stage Dockerfile in each module; output JAR is `inbound.jar` / `outbound.jar`.
- **Rollout strategy**: standard rolling deployment of the container workload; Spring Boot Actuator health endpoint is the readiness probe target. Outbound's `ServiceBusProcessorClient` connects on startup; readiness should be gated until the bean is up.
- **Rollback**: redeploy the previous image tag. No schema-breaking change should be released without a backward-compatible migration step (DB scripts are manual, so out-of-band rollback of schema must be planned per release).
- **Feature toggling**: per-partner enablement is via `MDP_BFF_EXTERNAL_CLIENTS`. Disabling a partner requires a config change and pod restart (no live reload).

## Metrics to be Tracked

- **Per-call latency** — `OkHttpService` already records `timeTakenInMs` in every audit row. Recommended: export to Micrometer / Actuator metrics.
- **Per-`AuditLogType` counts** — derive from `audit_log.tag` (e.g., counts of `KNOWLARITY_POOL_API_EMPTY`, `*_API_RESPONSE` failures).
- **Failure backlog** — count of rows in `failed_mdp_message_exception` per `client` × `failure_event_type` × time window.
- **Async pool health** — `AsyncJobService.getExecutorData()` (active, queue size, completed) is logged every 60s; recommend exposing as gauges.
- **JVM** — emitted every 60s via `CronService` (max/free/total memory).
- **Service Bus metrics** — message age, abandon count, DLQ count (Azure portal / monitor).
- **Recommended alarms**:
  - `failed_mdp_message_exception` row count for a single dealer trending up.
  - Knowlarity pool empty events.
  - Notification API failure rate.
  - JVM heap pressure.

## Data Analytics / Data Engineering metrics/tables

No data lake export is configured in this repo. The `audit_log` table is the de-facto operational metric source today. Long-term, recommended sinks:

- `audit_log` → BI table (slowly changing, append-only), partitioned by date and `tag`.
- `failed_mdp_message_exception` → operational dashboard for replay + SRE triage.

## Alternatives Considered

This service is in production and the formal alternative-selection is not captured in the repo. Notable design choices and the trade-off they imply:

- **Two services (inbound + outbound) vs. one** — chosen for blast-radius isolation and independent scaling. Cost: shared schema, two deploy units.
- **Strategy pattern with `@Service` beans (current) vs. plugin/SPI loader** — current approach is straightforward and IDE-friendly; adding a partner is N small files and one factory branch. Plugin/SPI was not adopted because the partner set is small and changes infrequently.
- **OkHttp vs. Spring `WebClient`** — OkHttp was chosen and is used directly via a thin wrapper; predates Spring Boot 3 reactive adoption in this repo. Trade-off: blocking I/O, but matches the synchronous, retry-friendly call style.
- **Manual SQL migrations vs. Flyway/Liquibase** — manual today (in `db/migrations/`). Risk of drift; adoption of a migration tool is recommended (see Risks).
- **No B2C token caching today** — recommended improvement. The `MDP_AUTH_B2C_TOKEN` cache name is defined but unused.

## Risks (If Any)

- **Token caching** — every external call refetches a B2C token; high volume of tokens issued and increased latency under load. Wiring `CacheService` + `CacheName.MDP_AUTH_B2C_TOKEN` (with token-expiry-aware TTL) is recommended.
- **OkHttp `readTimeout(0)`** — no read timeout. A hung partner can occupy threads in the pool. Recommend explicit connect/read/write timeouts.
- **Manual schema migration** — DB scripts in `db/migrations/` are applied out-of-band. Risk of environment drift; recommend Flyway/Liquibase.
- **No circuit breaker** — repeated retries against an unhealthy partner can saturate threads despite the bulkhead. Resilience4j or similar is recommended.
- **Schema sharing** — both services use the same `audit_log` table. Coordinated schema changes are required to avoid breaking either side.
- **`@Retryable` on private methods** — Spring Retry uses proxies; some `@Retryable` annotations on private methods (e.g., outlet-create / close in `SingleInterfaceDealerDataProcessorService`) may not behave as expected. Verify before depending on those retries.
- **No application-level authn on controllers** — relies entirely on network-level trust. Adoption of mTLS or token-based ingress auth is recommended for partner webhook endpoints.
- **TLS trust-all in `OkHttpConfig`** — the OkHttp client is configured to trust all certificates. Acceptable for internal trusted networks, risky if traffic ever traverses untrusted paths. Recommend tightening for prod.

## Appendix

### Glossary
- **BFF** — Backend-For-Frontend.
- **MDP** — Master Data Platform; source of truth for dealer master data.
- **SAP dealer code** — Primary identifier for a dealer.
- **AMD / AD / BRANCH / APS** — `DealerType` values (sourced from MDP).
- **k_number / virtual number** — Knowlarity-issued number used for call masking between customers and dealers.
- **DSE** — Dealer's Sales Executive.
- **DLQ** — Dead-letter queue.
- **PEEK_LOCK** — Azure Service Bus receive mode where a message is locked but not removed until `complete()`.
- **B2C** — Azure AD Business-to-Customer; here used as an OAuth2 IdP for service-to-service auth.

### Acronyms / enums of note
- `ExternalClient` — `KNOWLARITY`, `SINGLE_INTERFACE`, `LAT_LONG`, `DAKSHA`, `INTERNAL_SYSTEM`.
- `FailureEventType` — `KNOWLARITY_CALL_POOL_API_EMPTY`, `KNOWLARITY_API_FAILURE_RESPONSE`, `SINGLE_INTERFACE_API_FAILURE_RESPONSE`, `LAT_LONG_API_FAILURE_RESPONSE`, `INTERNAL_SYSTEM_FAILURE_RESPONSE`, `DAKSHA_API_FAILURE_RESPONSE`.
- `MdpStatus` — `PRE_ACTIVE`, `ACTIVE`, `INACTIVE`.
- `MdpModule` — `DEALER` (currently the only module).
- `WebHookEventType` — `DEALER_UNPROCESSABLE`, `DEALER_PROCESSED_SUCCESSFULLY`.

### Repository pointers
- Spring Boot entry points: `inbound/src/main/java/com/tvsmotor/bff/BffApplication.java`, `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/OutboundApplication.java`.
- Service Bus configuration: `outbound/.../config/BffServiceBusConfig.java`.
- Strategy / factory: `outbound/.../service/DealerDataProcessor.java`, `DealerDataProcessorFactory.java`.
- Failure handler: `outbound/.../service/FailedMessageExceptionHandlerService.java`.
- Migration scripts: `inbound/src/main/resources/db/migrations/`.
- Env-var reference: `README.md`.

### Configuration reference (env-var names only — no values)
`ACTIVE_ENVIRONMENT`, `DATABASE_HOST_URL`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `MDP_BASE_URL`, `MDP_BFF_EXTERNAL_CLIENTS`, `MDP_DEALER_DATA_TOPIC_NAME`, `MDP_DEALER_DATA_TOPIC_CONNECTION_STRING`, `KNOWLARITY_K_NUMBER_API_URL`, `KNOWLARITY_K_NUMBER_API_TOKEN`, `KNOWLARITY_K_NUM_ASSIGNMENT_ENABLED_DEALER_TYPES`, `KNOWLARITY_K_NUM_POOL_API_EMPTY_NOTIFICATION_RECIPIENTS`, `SI_OUTLET_API_BASE_URL`, `SI_OUTLET_API_TOKEN`, `SI_ENABLED_DEALER_TYPES`, `LATLONG_DEALER_DATA_API_URL`, `LATLONG_DEALER_DATA_API_TOKEN`, `DAKSHA_DEALER_UPDATE_API_URL`, `DAKSHA_DEALER_UPDATE_API_TOKEN`, `NOTIFICATION_BASE_URL`, `NOTIFICATION_FAILURE_EMAIL_TEMPLATE_ID`, `NOTIFICATION_EMAIL_FAILURE_PRIORITY`, `EXTERNAL_CLIENTS_FAILURE_EMAIL_ALERT_RECIPIENTS`, `AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL`, `AZURE_B2C_CLIENT_ID`, `AZURE_B2C_CLIENT_SECRET`, `AZURE_B2C_SCOPE`.
