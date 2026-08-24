# High Level Code Document — `tvsmbe-mdp-bff`

## 1. Application Overview

`tvsmbe-mdp-bff` is the Backend-For-Frontend (BFF) layer for the MDP (Master Data Platform) ecosystem at TVS Motor. It mediates traffic between callers (web/mobile clients, internal services, daemons, webhooks) and the MDP system, and propagates dealer-master data changes from MDP outward to a set of external partner systems.

The repository is organized as **two independently deployable Spring Boot 3 / Java 17 services** that share design conventions but have distinct responsibilities:

| Service | Module | Role | Trigger |
|---|---|---|---|
| **Inbound BFF** | `inbound/` (`com.tvsmotor.bff`) | Synchronous REST API for read-style dealer queries; receives incoming webhooks from external clients | HTTP requests |
| **Outbound BFF** | `outbound/` (`com.tvsmotor.mdp_bff.outbound`) | Asynchronous consumer that fans MDP dealer-data change events out to external partner systems | Azure Service Bus topic messages |

Both services share patterns: REST controllers, OkHttp-based outbound HTTP, JPA on MySQL, audit logging, retryable calls, and Azure B2C OAuth2 token retrieval.

## 2. Major Modules / Components

### Inbound (`com.tvsmotor.bff`)
- **REST Controllers** — `MdpController`, `WebHookController`, `TestController`
- **Service layer** — `MdpDealerOperationsService`, `WebHookService`, `SingleInterfaceWebhookHandlerService`, `AzureB2CTokenGenerationService`, `OkHttpService`, `AuditLogService`, `JsonHelperService`, `CronService`, `TestService`
- **Persistence** — `AuditLog` entity + `AuditLogRepo` (JPA) + `BaseEntity` (audit fields, Hibernate Envers)
- **Cross-cutting** — `RestExceptionHandler` (`@ControllerAdvice`), `CacheService` (Spring caching abstraction), `Context` (ThreadLocal request context), `Constants`, `GeneralUtils`
- **Domain enums** — `DealerType`, `DealerEmployeeType`, `DmsStatus`, `MdpModule`, `WebHookEventType`, `ExternalClient`, `AuditLogType`, `CacheName`
- **DTOs/models** — `request/mdp/*` (filter/search request bodies), `response/*` (MDP & Azure responses), shared `GeneralResponse` envelope

### Outbound (`com.tvsmotor.mdp_bff.outbound`)
- **Service Bus Listener** — `BffServiceBusConfig` (creates the `ServiceBusProcessorClient` bean), `MdpDealerDataConsumerService`
- **Dispatcher** — `DealerDataPasserService` (fan-out), `DealerDataProcessorFactory`, `DealerDataProcessor` interface
- **External-client processors** (one per partner system):
  - `knowlarity/` — `KnowlarityDealerDataProcessorService`, `KnowlarityApiCallerService`
  - `single_interface/` — `SingleInterfaceDealerDataProcessorService`, `SingleInterfaceApiCallerService`, `SingleInterfaceOperationService`
  - `lat_long/` — `LatLongDealerDataProcessorService`, `LatLongApiCallerService`
  - `daksha/` — `DakshaDealerDataProcessorService`, `DakshaApiCallerService`
  - `gmb_common/GmbCommonService` — shared dealer-data eligibility + address-merge helpers
- **Failure handling & alerting** — `FailedMessageExceptionHandlerService`, `FailureEventTypeInfoService`, `NotificationSenderService`
- **Async execution** — `AsyncJobService` (fixed `ThreadPoolExecutor` of 20 threads)
- **MDP write APIs** — `MdpDealerOperationsService` (mapDealerWithKNumber, unassignKNumber)
- **Persistence** — `AuditLog`, `FailedMdpMessageExceptionEntity`, `FailureEventTypeInfo` entities + matching repositories
- **Test endpoint** — `TestController` (`/v1/test/health`, `/v1/test/hello`)

## 3. Folder Structure Explanation

```
.
├── README.md                                    # Service overview + env var template
├── 20241004_docker_manual_builder_and_pusher_*  # Manual local Docker build helper
├── AST_Image_Scan_*.yml                         # AST/security image scan pipeline definitions
│
├── inbound/                                     # Inbound BFF service (Spring Boot)
│   ├── Dockerfile                               # Multi-stage Maven → Corretto 17 runtime
│   ├── pom.xml                                  # Maven dependencies (Spring Boot 3.5.x)
│   ├── ci-pipeline.yaml / cd-pipeline.yaml      # Build & deploy pipelines
│   ├── sonar_ci_pr_pipelines.yml                # SonarQube quality gate
│   ├── AST_MDP_BFF_*_Pipeline.yml               # AST scan pipelines (UAT/PROD)
│   └── src/
│       ├── main/java/com/tvsmotor/bff/
│       │   ├── BffApplication.java              # Spring Boot entry point
│       │   ├── cache/                           # CacheService wrapper around Spring CacheManager
│       │   ├── config/                          # CustomConfig, PostConstructThings
│       │   ├── controller/                      # REST controllers (MDP, Webhook, Test)
│       │   ├── entity/                          # JPA entities (AuditLog, BaseEntity)
│       │   ├── enums/                           # Domain enums
│       │   ├── exceptions/ + handlers/          # Custom exceptions + @ControllerAdvice
│       │   ├── model/request|response/          # Request/response DTOs
│       │   ├── repository/                      # Spring Data JPA repositories
│       │   ├── service/                         # Business + integration services
│       │   └── utils/                           # Constants, Context (ThreadLocal), GeneralUtils
│       ├── main/resources/
│       │   ├── application*.properties          # Per-profile config (local/dev/uat/prod)
│       │   ├── banner.txt
│       │   └── db/migrations/*.sql              # Manual DB migration scripts
│       └── test/                                # JUnit / Mockito unit tests, H2 used in tests
│
└── outbound/                                    # Outbound BFF service (Spring Boot)
    ├── Dockerfile, pom.xml, *-pipeline.*        # Same conventions as inbound
    └── src/main/java/com/tvsmotor/mdp_bff/outbound/
        ├── OutboundApplication.java             # Spring Boot entry point
        ├── cache/, config/, controller/, entity/
        ├── enums/                               # Adds FailureEventType, MdpStatus, ApiRetryPriority, SapStatus
        ├── exceptions/                          # Adds FailedMdpMessageException, ServiceException
        ├── model/                               # Marker types per client (KNOWLARITY, SINGLE_INTERFACE, LAT_LONG, DAKSHA)
        │   ├── request/{daksha, mdp, single_interface}/
        │   └── response/{azure, knowlarity, service_bus}/
        ├── repository/                          # AuditLogRepo, FailedMdpMessageExceptionRepo, FailureEventTypeInfoRepo
        ├── service/
        │   ├── service_bus/mdp/                 # MdpDealerDataConsumerService
        │   ├── knowlarity/, single_interface/, lat_long/, daksha/, gmb_common/
        │   └── (shared) AsyncJobService, FailedMessageExceptionHandlerService, NotificationSenderService, ...
        └── utils/                               # Constants, Context, GeneralUtils
```

## 4. Core Business Workflows

### A. Inbound: Read dealer data (synchronous)
1. Client calls one of the MDP read endpoints on `/mdp-bff/v1/mdp/...`.
2. `MdpController` delegates to `MdpDealerOperationsService`.
3. Inputs are validated & sanitized (`GeneralUtils`, `Validateable`/`Sanitizeable` interfaces).
4. `AzureB2CTokenGenerationService` obtains a Bearer token (with retry) from Azure AD B2C.
5. `OkHttpService` calls the MDP backend; response codes 4xx/5xx map to `BAD_REQUEST` / `UNAUTHORIZED` / `INTERNAL_SERVER_ERROR` via `handleValidationAndNoSuchElementException`.
6. The MDP `data` node is deserialized into `MdpDealerData` (or a list) and wrapped in a `GeneralResponse` envelope.
7. Failures or non-2xx responses are persisted via `AuditLogService`. The call is annotated `@Retryable` (max 5 attempts, exponential backoff 1s → 10s).

### B. Inbound: Webhook intake
1. External client `POST`s to `/mdp-bff/webhook/v1/{mdpModule}/{externalClient}/{webHookEventType}`.
2. `WebHookController` → `WebHookService.handleWebhookRequest(...)`.
3. Payload is serialized, an `INCOMING_WEBHOOK` audit log is written, then routed via a `switch` on `MdpModule`/`ExternalClient`.
4. For `DEALER` + `SINGLE_INTERFACE`, `SingleInterfaceWebhookHandlerService.processWebhookRequest` is invoked; per-event-type processing is gated by `ExternalClient.shouldProcessFor(...)`.

### C. Outbound: Fan-out of MDP dealer changes (asynchronous)
1. MDP publishes a dealer-change event onto an Azure Service Bus topic.
2. `BffServiceBusConfig` creates a `ServiceBusProcessorClient` (session-aware, PEEK_LOCK, max 10 concurrent sessions, manual completion).
3. `MdpDealerDataConsumerService.consumeMessage` deserializes the body into `MdpServiceBusIncomingMessagePayloadBody`, sets `Context` (transactionId), and writes a `SAVED_SERVICE_BUS_MESSAGE` audit log.
4. `DealerDataPasserService.sendDealerDataToExternalClients` parallelStream-iterates over the configured `MDP_BFF_EXTERNAL_CLIENTS`, submitting each client's processing as a job to `AsyncJobService`'s 20-thread pool.
5. `DealerDataProcessorFactory.getProcessor(client)` returns the right `DealerDataProcessor` strategy:
   - **Knowlarity** — handles virtual-number assignment / update / un-assignment for AMD, AD, BRANCH dealers based on `MdpStatus`, `K_NUMBER_NEEDED` flag, and Knowlarity pricing tier. Three-step assign flow: `callPoolApi` → `mapDealerWithKNumber` (back to MDP) → `callDealerUpdateApi`.
   - **Single Interface** — `createOutlet` for ACTIVE dealers (with full address/lat-long/showroom-manager checks), `closeOutlet` for INACTIVE.
   - **LatLong** — forwards the entire MDP payload to the LatLong dealer-data API.
   - **Daksha** — wraps the payload in a `DakshaUpdateRequest` and posts to the Daksha dealer-update API.
6. Each client API call is wrapped in `@Retryable` (5 attempts, exponential backoff). On non-retryable failure, a `FailedMdpMessageException` is thrown carrying `FailureEventType`, `ApiRetryPriority`, response, and the original message.

### D. Outbound: Failure handling & alerting
1. `FailedMessageExceptionHandlerService.exceptionHandler` is invoked from the dispatcher's catch block.
2. The exception is persisted into `failed_mdp_message_exception` (with truncated `apiResponse`) for later replay/inspection.
3. `FailureEventTypeInfoService.shouldTriggerMailFor` enforces a per-`FailureEventType` email backoff window (`nextEmailBackoffTimeInHrs`, currently 1h per event type).
4. If due, `NotificationSenderService.sendEmailNotification` calls the internal Notification API (Azure B2C-authenticated) using a configurable template + recipient list and writes audit logs. The "last notified" timestamp is then updated in `failure_event_type_info`.

### E. Periodic metrics
- Both services run `CronService.logMetricsPeriodically()` on a 60-second `@Scheduled` timer.
- Metrics include JVM memory snapshot and (outbound) the `ThreadPoolExecutor`'s queue/active/completed counts. Each tick is persisted as a `JVM_MEMORY_DATA_*` audit log.

## 5. Key Services / Classes

### Inbound
| Class | Responsibility |
|---|---|
| `BffApplication` | Spring Boot bootstrap; enables `@EnableCaching`, `@EnableRetry`, `@EnableScheduling` |
| `MdpController` | REST endpoints under `/v1/mdp` |
| `WebHookController` | Webhook intake at `/webhook/v1/{module}/{client}/{event}` |
| `MdpDealerOperationsService` | Calls MDP read APIs, retry + auth, response normalization |
| `WebHookService` | Routes webhook events to per-client handlers; audit-logs every incoming hook |
| `AzureB2CTokenGenerationService` | OAuth2 client-credentials Bearer token fetch (with retry) |
| `OkHttpService` | Generic GET/POST helpers wrapping OkHttp + StopWatch metrics |
| `AuditLogService` | Persists audit rows (auto-truncated to 4000 chars) |
| `RestExceptionHandler` | Global `@ControllerAdvice` mapping `ValidationException`, `HttpMessageNotReadableException`, etc. |
| `CacheService` | Typed wrapper around Spring `CacheManager` keyed by `CacheName` enum |
| `Context` | ThreadLocal carrier for `userId`, `userToken`, `uuid` |

### Outbound
| Class | Responsibility |
|---|---|
| `OutboundApplication` | Spring Boot bootstrap (cache + retry + scheduling) |
| `BffServiceBusConfig` | Builds the `ServiceBusProcessorClient` bean for the MDP topic |
| `MdpDealerDataConsumerService` | Topic message deserializer + entry to fan-out |
| `DealerDataPasserService` | Parallel fan-out + per-client async submission |
| `DealerDataProcessor` (interface) + `DealerDataProcessorFactory` | Strategy pattern for per-client processing |
| `Knowlarity*Service`, `SingleInterface*Service`, `LatLong*Service`, `Daksha*Service` | Per-partner orchestration + HTTP integration |
| `MdpDealerOperationsService` (outbound variant) | Calls MDP write APIs (`mapDealerWithKNumber`, `unassignKNumber`) |
| `AsyncJobService` | 20-thread fixed pool used to isolate per-client work |
| `FailedMessageExceptionHandlerService` | Persists failures + decides whether to alert |
| `FailureEventTypeInfoService` | Per-event-type alert-cooldown bookkeeping |
| `NotificationSenderService` | Calls internal Notification email API |
| `GmbCommonService` | Shared dealer eligibility + address-merge utilities |

## 6. External Integrations

| System | Direction | Channel | Auth | Configured via |
|---|---|---|---|---|
| **MDP** (read) | Inbound BFF → MDP | HTTPS REST (OkHttp) | Azure B2C Bearer token | `MDP_BASE_URL`, `mdp.get-dealer-data.*` |
| **MDP** (write) | Outbound BFF → MDP | HTTPS REST (OkHttp) | Azure B2C Bearer token | `mdp.api.dealer.*` |
| **Azure AD B2C** | Both → Microsoft | OAuth2 client-credentials | Client ID + Secret | `AZURE_B2C_*` |
| **Azure Service Bus** (MDP topic) | MDP → Outbound BFF | AMQP (azure-messaging-servicebus) | Connection string | `MDP_DEALER_DATA_TOPIC_*` |
| **Knowlarity** (virtual-number provider) | Outbound BFF → Knowlarity | HTTPS GET with query params | Static `auth` header token | `KNOWLARITY_K_NUMBER_API_*` |
| **Single Interface** (outlet/listing platform) | Outbound BFF → SI | HTTPS POST JSON | Static `auth` header token | `SI_OUTLET_API_*` |
| **LatLong** (dealer-locator) | Outbound BFF → LatLong | HTTPS POST JSON + access_token query param | Token | `LATLONG_DEALER_DATA_API_*` |
| **Daksha** | Outbound BFF → Daksha | HTTPS POST JSON | `token` header | `DAKSHA_DEALER_UPDATE_API_*` |
| **Internal Notification API** | Outbound BFF → Notification | HTTPS POST JSON | Azure B2C Bearer token | `NOTIFICATION_*` |
| **Single Interface webhook** | SI → Inbound BFF | Inbound HTTPS POST | n/a (path-typed) | `/webhook/v1/{module}/{client}/{event}` |
| **MySQL** (Azure DB for MySQL) | Both ↔ DB | JDBC | Username + password | `DATABASE_*` |

## 7. Major Dependencies

Both modules use the same Spring Boot 3 / Java 17 base. Key Maven dependencies:

- `org.springframework.boot:spring-boot-starter-web` — REST + embedded Tomcat (port 8080)
- `org.springframework.boot:spring-boot-starter-data-jpa` — JPA / Hibernate
- `org.springframework.boot:spring-boot-starter-actuator` — health, metrics
- `org.springframework.retry:spring-retry` (+ `@EnableRetry`) — `@Retryable` annotations across HTTP services
- `com.mysql:mysql-connector-j` — MySQL driver
- `org.hibernate:hibernate-envers` — entity audit history (via `@Audited` on `BaseEntity`)
- `com.azure:azure-messaging-servicebus` — Azure Service Bus consumer (outbound only listens; inbound has the lib but no consumer)
- `com.squareup.okhttp3:okhttp` — outbound HTTP client
- `com.google.guava:guava` — `ImmutableMap`, etc.
- `com.fasterxml.jackson.*` (transitive) + `JavaTimeModule` — JSON serialization
- `org.springdoc:springdoc-openapi-starter-webmvc-ui` — Swagger UI at `/<context>/swagger-ui/index.html`
- `org.projectlombok:lombok` — boilerplate reduction
- `com.h2database:h2` (test scope) — in-memory DB for unit tests
- `org.jacoco:jacoco-maven-plugin` — coverage report (entities, models, exceptions excluded)

Build: `mvn clean install` (multi-stage Dockerfiles use `maven:3.9.14-amazoncorretto-17` for build, `amazoncorretto:17.0.18` for runtime).

## 8. Runtime Architecture

```
                          ┌─────────────────────────────────────────┐
                          │            Azure AD B2C                 │
                          │       (OAuth2 client-credentials)       │
                          └───────────────▲─────────────────────────┘
                                          │ Bearer token
                                          │
  Clients / Webhooks                      │
        │                                 │
        ▼                                 │
  ┌────────────────────────┐              │           ┌────────────────────────┐
  │   INBOUND BFF (8080)   │──────────────┼──────────▶│         MDP            │
  │ context: /mdp-bff      │   read APIs  │  read     │  (master data store)   │
  │                        │              │           └──────────▲─────────────┘
  │  REST controllers      │              │                      │ write APIs
  │  + Webhook intake      │              │                      │
  └─────────┬──────────────┘              │           ┌──────────┴─────────────┐
            │                             │           │   OUTBOUND BFF (8080)  │
            │  audit_log                  │           │ context: /mdp-bff-     │
            ▼                             │           │           outbound     │
  ┌────────────────────┐                  │           │                        │
  │     MySQL DB       │◀─────────────────┴───────────┤  Service Bus consumer  │
  │  audit_log         │                              │  + DealerDataProcessor │
  │  failed_mdp_msg_*  │                              │    factory + 20-thread │
  │  failure_event_*   │                              │    async pool          │
  └────────────────────┘                              └──┬──────┬──────┬───────┘
                                                        │      │      │
                                                        ▼      ▼      ▼
                                  ┌─────────────────────────┐ ┌────────────────┐
                                  │ Azure Service Bus topic │ │  External      │
                                  │  (MDP_DEALER_DATA_*)    │ │  partners:     │
                                  │     ▲                   │ │  Knowlarity,   │
                                  │     │ produced by MDP   │ │  Single        │
                                  └─────┘                   │ │  Interface,    │
                                                            │ │  LatLong,      │
                                                            │ │  Daksha        │
                                                            │ └────────────────┘
                                                            │
                                                            ▼
                                                  ┌────────────────────┐
                                                  │ Notification API   │
                                                  │ (failure email)    │
                                                  └────────────────────┘
```

Key runtime characteristics:
- **Stateless services**, scaled horizontally (each pod listens to the same Service Bus subscription `mdp_bff`; subscription handles fan-in).
- **Concurrency** in Outbound: 10 concurrent Service Bus sessions × 20-thread executor for per-client work.
- **Resilience**: every external HTTP call is `@Retryable` (5 attempts, 1s → 10s exponential, multiplier 2.0); Service Bus uses `PEEK_LOCK` with manual `complete()`.
- **Profiles** selected via `ACTIVE_ENVIRONMENT` (`local`, `dev`, `uat`, `prod`).
- **Observability**: Spring Boot Actuator + per-call StopWatch metrics + database-backed audit log + periodic JVM/executor snapshots.
- **JVM tuning**: containers run with `-XX:MaxRAMPercentage=75` and timezone `Asia/Kolkata`.

## 9. Important Entry Points

### HTTP (Inbound, context path `/mdp-bff`)
| Method | Path | Handler | Purpose |
|---|---|---|---|
| GET | `/v1/mdp/dealer/{sapDealerCode}` | `MdpController#getDealerData` | Single-dealer lookup |
| POST | `/v1/mdp/dealer/basedOnFilters` | `MdpController#getDealerDataBasedOnFilters` | Filter by type/statuses/flags/search |
| GET | `/v1/mdp/dealers?pincode={pincode}` | `MdpController#getDealersBasedOnPincode` | Dealers by pincode |
| POST | `/webhook/v1/{mdpModule}/{externalClient}/{webHookEventType}` | `WebHookController#handleWebhook` | Generic webhook intake |
| GET | `/v1/test/hello` | `TestController#helloCode` | Health/diagnostic |
| Various | `/swagger-ui/index.html`, `/v3/api-docs` | springdoc | API docs (toggleable) |

### HTTP (Outbound, context path `/mdp-bff-outbound`)
| Method | Path | Handler |
|---|---|---|
| GET | `/v1/test/health` | `TestController#healthTest` (env + property introspection) |
| GET | `/v1/test/hello` | `TestController#helloWorldApi` (incl. executor stats) |

### Message-driven (Outbound)
- **Azure Service Bus topic**: `${MDP_DEALER_DATA_TOPIC_NAME}` / subscription `mdp_bff` — handled by the lambda registered in `BffServiceBusConfig.createServiceBusMdpDataProcessorClient`, dispatched to `MdpDealerDataConsumerService.consumeMessage`.

### Application bootstrap
- `inbound`: `com.tvsmotor.bff.BffApplication#main`
- `outbound`: `com.tvsmotor.mdp_bff.outbound.OutboundApplication#main`

### Scheduled
- `CronService.logMetricsPeriodically` — `@Scheduled(fixedRate = 60_000)` in both services.

## 10. High-Level Data Flow

### Read flow (Inbound)
```
Client
  │ HTTP request (sapDealerCode | filter body | pincode)
  ▼
MdpController
  │ delegate
  ▼
MdpDealerOperationsService
  │ validate + sanitize          ──▶ AzureB2CTokenGenerationService ─▶ Azure B2C (token)
  │ build URL + headers (Bearer)
  ▼
OkHttpService ─────────────────── HTTPS ──────────────────────────▶ MDP API
  │                                                                       │
  │ ApiCallResponse {code, body, timeTakenInMs}                            │
  ▼                                                                       │
MdpDealerOperationsService                                                 │
  │ if !successful  → AuditLogService.saveLog(...) → MySQL audit_log       │
  │ else            → JsonHelperService.fromJson → MdpDealerData           │
  ▼                                                                       │
GeneralResponse envelope ◀──────────────────────────────────────────── (response)
  │
  ▼
Client
```

### Write/fan-out flow (Outbound)
```
MDP ─publish─▶ Azure Service Bus topic
                 │
                 ▼
BffServiceBusConfig.processMessage (PEEK_LOCK)
                 │ session-aware, max 10 concurrent
                 ▼
MdpDealerDataConsumerService.consumeMessage
   │ Context.setValues(transactionId)
   │ JsonHelperService → MdpServiceBusIncomingMessagePayloadBody
   │ AuditLogService(SAVED_SERVICE_BUS_MESSAGE)
   ▼
DealerDataPasserService.sendDealerDataToExternalClients
   │ for each ExternalClient ∈ MDP_BFF_EXTERNAL_CLIENTS (parallel)
   │   AsyncJobService.submitJob(() -> {
   │     DealerDataProcessorFactory.getProcessor(client).processData(payload);
   │   })
   ▼
┌──────────────────────────────────────────────────────────────────────┐
│   Per-client processor                                               │
│   eligibility check (GmbCommonService, dealer-type allow-list)       │
│   build request → OkHttpService → external API (with @Retryable)     │
│   AuditLogService(<event-specific tag>)                              │
│                                                                      │
│   on non-retryable failure:                                          │
│     throw FailedMdpMessageException(client, payload, code, ...)      │
│                                          │                           │
│                                          ▼                           │
│   FailedMessageExceptionHandlerService.exceptionHandler              │
│     ├─▶ failed_mdp_message_exception (DB)                            │
│     └─▶ FailureEventTypeInfoService.shouldTriggerMailFor?            │
│            yes ─▶ NotificationSenderService.sendEmailNotification    │
│                   (Azure B2C Bearer → Notification API)              │
│                   updates failure_event_type_info.last_notified_time │
└──────────────────────────────────────────────────────────────────────┘
   │
   ▼
context.complete() → Service Bus message ACK'd
```

### Persistent data
- `audit_log` (`tag` enum, `metadata` ≤ 4000 chars, `transaction_id`, audit fields, version) — write-mostly trail used for forensic analysis.
- `failed_mdp_message_exception` (full incoming MDP payload as `longtext`, truncated `api_response`, `client`, `priority`, `failure_event_type`) — replay/dead-letter store.
- `failure_event_type_info` (`failure_event_type` UNIQUE, `last_notified_time`) — alert backoff bookkeeping.
- All entities extend `BaseEntity` (`@Audited` via Hibernate Envers ⇒ `*_AUD` history tables auto-managed).

---

## Notes for vendor onboarding

- **Configuration is fully externalized** through environment variables consumed in `application.properties`. The full list (with placeholder values) is in `README.md`. No production secret values are stored in this repo.
- **Local run**: set `ACTIVE_ENVIRONMENT=local`, populate the env vars, then `mvn -f inbound/pom.xml spring-boot:run` and `mvn -f outbound/pom.xml spring-boot:run` (in separate shells). Default port for both is 8080 (run on different hosts/ports if started locally side-by-side; the manual-build helper script uses 9999 for outbound).
- **Adding a new external client (outbound)** requires: adding an enum value to `ExternalClient`, a marker class under `model/`, an entry in `DealerDataProcessorFactory#getProcessor`, a new `*DealerDataProcessorService` implementing `DealerDataProcessor`, plus an `*ApiCallerService` for the HTTP integration and corresponding `FailureEventType` + handling in `FailedMessageExceptionHandlerService.exceptionHandler`.
- **Schema migrations** are tracked manually in `inbound/src/main/resources/db/migrations/v*.sql`; there is no Flyway/Liquibase wiring — apply scripts as part of release.
- **Tests**: unit tests live under `src/test/java/...` for both modules; `H2` is used as the in-memory DB. Run with `mvn test`. JaCoCo coverage runs in the `prepare-package` phase.
