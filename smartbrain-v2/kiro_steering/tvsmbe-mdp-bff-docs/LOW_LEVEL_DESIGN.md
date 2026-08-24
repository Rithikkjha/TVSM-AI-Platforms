# Low Level Design — `tvsmbe-mdp-bff`

> Implementation-level design for engineering vendors.
> Follows the [TVS Motor D&AI LLD Template](https://tvsmotorcompany.atlassian.net/wiki/spaces/DE2/pages/4209606912/Low+Level+Design+Template).
> Companion to the HLD at `docs/HLD_tvsmbe-mdp-bff.md`. No production credentials, tokens, or URLs are included; configuration is referenced by env-var name only.

| Field | Value |
|---|---|
| Service name | `tvsmbe-mdp-bff` |
| Modules | `inbound/` (`com.tvsmotor.bff`), `outbound/` (`com.tvsmotor.mdp_bff.outbound`) |
| Runtime | Java 17, Spring Boot 3.5.x, Tomcat (embedded), MySQL 8, Azure Service Bus, OkHttp 4.12 |
| Audience | New engineering vendors / partners onboarding the codebase |

---

## Overview

`tvsmbe-mdp-bff` is the BFF for the MDP Dealer module. The repository ships **two Spring Boot services**:

- **Inbound** — synchronous REST APIs to read dealer data from MDP, plus a generic webhook intake.
- **Outbound** — asynchronous consumer of MDP dealer-change events from Azure Service Bus that fans out to external partner systems (Knowlarity, Single Interface, LatLong, Daksha) and an internal Notification API.

This document is the implementation-level companion to the HLD — class-by-class structure, API request/response shapes, validation rules, error handling, business rules (especially Knowlarity and Single Interface), and configuration.

## High Level Design — Quick Recap

Reference doc: [`docs/HLD_tvsmbe-mdp-bff.md`](./HLD_tvsmbe-mdp-bff.md)

Two services, single shared MySQL schema, single Service Bus topic from MDP, four partner integrations, one internal Notification dependency, Azure AD B2C as IdP for service-to-service auth.

## Assumptions

- The platform is **Kubernetes-style** (or equivalent) container orchestrator with HTTPS ingress; pods are stateless and horizontally scalable.
- Network egress to MDP, Azure Service Bus, Azure AD B2C, Knowlarity, Single Interface, LatLong, Daksha, and the Notification API is open from the cluster.
- The Service Bus topic and subscription `mdp_bff` exist before outbound starts.
- MDP is the system of record for dealer master data; this service does not own dealer state, only audit + failure replay state.
- Partner endpoints are accessible via static tokens issued out-of-band by each partner.
- A single Spring `CacheManager` (default `ConcurrentMapCacheManager`) is used. **No distributed cache** today.
- Schema migrations are applied **manually** from `inbound/src/main/resources/db/migrations/v*.sql` as part of release.
- Inbound REST and webhook endpoints are protected by **network-level trust** (private VNet / API gateway). Application-level authentication is not implemented on controllers.

## Components

### Module 1 — Inbound (`com.tvsmotor.bff`, port 8080, context `/mdp-bff`)

```
com.tvsmotor.bff
├── BffApplication                          // @SpringBootApplication entry point
├── cache/CacheService                      // Typed wrapper over Spring CacheManager
├── config/
│   ├── CustomConfig                        // exposes @Bean("serverInstanceId") UUID fragment
│   └── PostConstructThings                 // empty hook; logs on startup
├── controller/
│   ├── MdpController                       // /v1/mdp/*
│   ├── WebHookController                   // /webhook/v1/*
│   └── TestController                      // /v1/test/*
├── entity/
│   ├── BaseEntity                          // id, createdAt/by, updatedAt/by, version, @Audited
│   └── AuditLog                            // table audit_log
├── enums/                                  // domain enums (see §5.4)
├── exceptions/
│   ├── ValidationException                 // RuntimeException for input failures
│   ├── ExternalServiceException            // RuntimeException for upstream failures
│   └── handlers/RestExceptionHandler       // global @ControllerAdvice
├── model/
│   ├── request/mdp/{...}                   // typed request DTOs implementing MdpDealerRequestData
│   └── response/{...}                      // GeneralResponse, ApiCallResponse, MdpDealerData, ...
├── repository/AuditLogRepo                 // JpaRepository<AuditLog, Long>
├── service/
│   ├── interfaces/{Validateable, Sanitizeable}
│   ├── MdpDealerOperationsService          // MDP read calls
│   ├── WebHookService                      // Webhook routing
│   ├── SingleInterfaceWebhookHandlerService
│   ├── AzureB2CTokenGenerationService      // OAuth2 client-credentials
│   ├── OkHttpService + OkHttpConfig        // OkHttp client + helpers
│   ├── AuditLogService                     // persists audit_log rows
│   ├── JsonHelperService                   // Jackson wrapper
│   ├── CronService                         // 60s metric ticks
│   └── TestService                         // /v1/test diagnostics
└── utils/{Constants, Context, GeneralUtils}
```

### Module 2 — Outbound (`com.tvsmotor.mdp_bff.outbound`, port 8080, context `/mdp-bff-outbound`)

```
com.tvsmotor.mdp_bff.outbound
├── OutboundApplication                     // @SpringBootApplication entry point
├── config/
│   ├── BffServiceBusConfig                 // builds ServiceBusProcessorClient bean
│   ├── CustomConfig                        // @Bean("serverInstanceId")
│   └── PostConstructThings
├── controller/TestController               // /v1/test/health, /v1/test/hello
├── entity/{BaseEntity, AuditLog,
│         FailedMdpMessageExceptionEntity,
│         FailureEventTypeInfo}
├── enums/                                  // adds MdpStatus, FailureEventType, ApiRetryPriority, SapStatus
├── exceptions/                             // adds FailedMdpMessageException, ServiceException
├── model/
│   ├── (marker) KNOWLARITY, SINGLE_INTERFACE, LAT_LONG, DAKSHA  // implements DealerDataClient
│   ├── request/{daksha, mdp, single_interface}/...
│   └── response/{azure, knowlarity, service_bus}/...
├── repository/{AuditLogRepo, FailedMdpMessageExceptionRepo, FailureEventTypeInfoRepo}
├── service/
│   ├── service_bus/mdp/MdpDealerDataConsumerService
│   ├── DealerDataPasserService
│   ├── DealerDataProcessor (interface)
│   ├── DealerDataProcessorFactory
│   ├── knowlarity/{KnowlarityDealerDataProcessorService, KnowlarityApiCallerService}
│   ├── single_interface/{...DataProcessor, ...ApiCaller, SingleInterfaceOperationService}
│   ├── lat_long/{...DataProcessor, ...ApiCaller}
│   ├── daksha/{...DataProcessor, ...ApiCaller}
│   ├── gmb_common/GmbCommonService
│   ├── MdpDealerOperationsService          // MDP write calls
│   ├── AsyncJobService                     // 20-thread fixed pool
│   ├── FailedMessageExceptionHandlerService
│   ├── FailureEventTypeInfoService
│   ├── NotificationSenderService
│   ├── AzureB2CTokenGenerationService
│   ├── OkHttpService + OkHttpConfig
│   ├── AuditLogService, JsonHelperService, CronService
└── utils/{Constants, Context, GeneralUtils}
```

## API Design

All inbound REST APIs return `application/json` as `GeneralResponse`:

```json
{
  "data": <payload | null>,
  "errorMessage": "<string | null>"
}
```

### 1. `GET /mdp-bff/v1/mdp/dealer/{sapDealerCode}`
- **Handler**: `MdpController.getDealerData`
- **Path params**: `sapDealerCode` (string, non-empty)
- **Headers**: none required at the BFF (network-trusted)
- **Validation**: `GeneralUtils.validateAndSanitize(sapDealerCode, "sapDealerCode")` → trims and rejects null/empty.
- **Business behavior**: fetches a Bearer token from Azure B2C, GETs `${MDP_BASE_URL}/mdp/v1/dealer/{code}`, deserializes the `data` node into `MdpDealerData`.
- **Status codes**:
  - `200 OK` — success (`data: MdpDealerData`).
  - `400 Bad Request` — MDP returned 400 (relayed errorMessage), or `ValidationException` on input.
  - `401 Unauthorized` — MDP returned 401.
  - `500 Internal Server Error` — MDP returned other non-2xx, or `ExternalServiceException`/unexpected.
- **Idempotency**: GET is naturally idempotent.
- **Retry**: `@Retryable(maxAttempts=5, backoff=@Backoff(delay=1000, maxDelay=10000, multiplier=2.0))` on the service method.

### 2. `POST /mdp-bff/v1/mdp/dealer/basedOnFilters`
- **Handler**: `MdpController.getDealerDataBasedOnFilters`
- **Body**: `DealerTypeStatusFlagsFilterRequest`
  ```json
  {
    "type": "AMD|APS|BRANCH|AD",
    "sapStatus": "<string optional>",
    "dmsStatus": "<string optional>",
    "mdpStatus": "<string optional>",
    "flags": ["<string>", ...],
    "search": {
      "searchTerm": "<min length 3>",
      "searchParams": ["<string>", ...]
    }
  }
  ```
- **Validation** (in `DealerTypeStatusFlagsFilterRequest.validate`):
  - At least one of `type`, `sapStatus`, `dmsStatus`, `mdpStatus`, `flags`, `search` must be provided.
  - String fields: nullable but if present must not be blank (`nullableButNotEmptyOrElseThrow`).
  - `flags`: if present, must be non-empty and contain no null/empty strings.
  - `search.searchTerm` ≥ 3 characters; `search.searchParams` non-empty list of non-empty strings.
- **Sanitization** (`sanitizeIncomingData`): trims `sapStatus`, `dmsStatus`, every `flag`, `search.searchTerm`, every `search.searchParams[i]`.
- **Status codes**: `200`, `400` (validation), `500` (MDP failure / `ExternalServiceException`).
- **Idempotency**: idempotent (read-only).

### 3. `GET /mdp-bff/v1/mdp/dealers?pincode={pincode}`
- **Handler**: `MdpController.getDealersBasedOnPincode`
- **Query params**: `pincode` (string, non-empty)
- **Validation**: `GeneralUtils.validateAndSanitize(pincode, "pincode")`.
- **Status codes**: `200`, `400`, `500`.

### 4. `POST /mdp-bff/webhook/v1/{mdpModule}/{externalClient}/{webHookEventType}`
- **Handler**: `WebHookController.handleWebhook`
- **Path enums** (binding will 400 on unknown values):
  - `mdpModule`: `DEALER`
  - `externalClient`: `KNOWLARITY | SINGLE_INTERFACE | LAT_LONG`
  - `webHookEventType`: `DEALER_UNPROCESSABLE | DEALER_PROCESSED_SUCCESSFULLY`
- **Body**: `Map<String, Object>` (free-form JSON)
- **Behavior**:
  1. `GeneralUtils.notNullOrElseThrow(payload, "payload")`.
  2. `WebHookService.logWebhookEvent` writes an `INCOMING_WEBHOOK` audit row.
  3. `switch(mdpModule)` → `DEALER`. `switch(externalClient)` → `SINGLE_INTERFACE` → `SingleInterfaceWebhookHandlerService.processWebhookRequest`. Other clients throw `ValidationException`.
  4. `ExternalClient.shouldProcessFor(webHookEventType)` decides whether the handler runs business logic. Today the `SINGLE_INTERFACE` value declares `[DEALER_UNPROCESSABLE]` as processable; the handler body is currently a TODO placeholder.
- **Response**:
  ```json
  { "data": "Webhook data received successfully", "errorMessage": null }
  ```
- **Status codes**: `200`, `400` (invalid module/client/event or null payload), `500`.

### 5. `GET /mdp-bff/v1/test/hello`
- **Handler**: `TestController.helloCode` → `TestService.helloFromService`
- Returns a small map with timestamp, version banner, request IPs, and headers.

### 6. Outbound diagnostics (context `/mdp-bff-outbound`)
- `GET /v1/test/health?sapDealerCode=&property=` — returns active profile + a snapshot map; if `property` is set, returns `applicationContext.getEnvironment().getProperty(sapDealerCode)`. *(Diagnostic only.)*
- `GET /v1/test/hello?sapDealerCode=&threadSleepTimeInMs=` — returns runtime metrics + `AsyncJobService.getExecutorData()`.

### Springdoc / Swagger
- `GET /<context>/swagger-ui/index.html`, `GET /<context>/v3/api-docs` (controlled by `springdoc.swagger-ui.enabled`).

### Outbound — Service Bus contract (incoming)
- Topic: `${MDP_DEALER_DATA_TOPIC_NAME}`, subscription: `mdp_bff`.
- Message body (JSON) is parsed into `MdpServiceBusIncomingMessagePayloadBody`:
  ```
  dealer:        { sapDealerCode, dmsStatus, sapStatus, sapRawStatus, mdpStatus,
                   type (AMD|AD|BRANCH|APS), oldSapDealerCode,
                   parentApsSapDealerCode, parentAmdSapDealerCode }
  dealerDetails: { name, branchName, ..., tempDmsBranchSequence,
                   knowlarityVirtualNumber, knowlarityRoutingCli, knowlarityFallbackNumber, ... }
  locations[]:   { type, addressLine1..3, pincode, city, state, country, ...
                   latitude, longitude, googleMapsUrl, ... }
  contacts[]:    { type, primaryPhoneNumber, secondaryPhoneNumber, emailAddress }
  flags[]:       { name, isEnabled (0|1) }
  employees[]:   { fullName, type (MANAGER|DSE|SHOWROOM_MANAGER|OTHER),
                   managerId, phoneNumber, emailAddress, isActive, isDeleted }
  ```
- Application property `event` (string) on the Service Bus message is read by `MdpDealerDataConsumerService` (currently logged; not used to branch).

## Data Model / Schema Changes

### Tables (MySQL 8)

#### `audit_log` (created in `v1.1_audit_log_table_20240523.sql`, altered in `v1.3_audit_log_changes_20250203.sql`)
| Column | Type | Notes |
|---|---|---|
| `id` | BIGINT PK AUTO_INCREMENT | |
| `created_at`, `updated_at` | DATETIME NOT NULL DEFAULT now() | |
| `created_by`, `updated_by` | VARCHAR(50) NOT NULL | filled from `Context.getUserId()` or `"System"` |
| `version` | BIGINT DEFAULT 0 | optimistic lock |
| `tag` | VARCHAR(200) NOT NULL | enum `AuditLogType` stored as string |
| `metadata` | VARCHAR(4000) NOT NULL | trimmed at 4000 chars by `AuditLogService` |
| `transaction_id` | VARCHAR(100) | added in v1.3; populated by outbound `Context` |
| Index | `audit_log_idx_tag (tag)` | |

#### `failed_mdp_message_exception` (created in `v1.2_failed_mdp_message_entity_20241128.sql`)
| Column | Type | Notes |
|---|---|---|
| `id` | BIGINT PK AUTO_INCREMENT | |
| audit columns | (same as `audit_log`) | |
| `mdp_dealer_data` | LONGTEXT | full incoming MDP payload, JSON-serialized |
| `client` | VARCHAR(20) | `ExternalClient` enum |
| `api_response` | VARCHAR(200) | truncated to 200 chars by `FailedMessageExceptionHandlerService.trimApiJsonResponse` |
| `response_code` | INT | upstream HTTP code |
| `priority` | VARCHAR(20) | `ApiRetryPriority` enum (`HIGH | MEDIUM | LOW`) |
| `failure_event_type` | VARCHAR(50) | `FailureEventType` enum |

#### `failure_event_type_info` (created in `v1.2_*.sql`)
| Column | Type | Notes |
|---|---|---|
| `id` | BIGINT PK AUTO_INCREMENT | |
| audit columns | | |
| `failure_event_type` | VARCHAR(100) | UNIQUE (`unique_failure_event_type`) |
| `last_notified_time` | VARCHAR(50) | written by `FailureEventTypeInfoService.saveAndUpdateLastNotifiedTime` |

#### Hibernate Envers
- `BaseEntity` is `@Audited` (revisions stored in `*_AUD` tables created by Envers; managed automatically by Hibernate).

### ER (textual)
```
BaseEntity (mapped superclass)
   ├── AuditLog                            (1:N revisions in audit_log_AUD)
   ├── FailedMdpMessageExceptionEntity     (1:N revisions in failed_mdp_message_exception_AUD)
   └── FailureEventTypeInfo                (1:N revisions in failure_event_type_info_AUD)
```

There are no foreign keys between the three tables — they are independent operational stores keyed by `id` only.

## Class & Interface Design

### Inbound — high-level wiring
```
HTTP request
   │
   ▼
MdpController / WebHookController / TestController
   │   uses
   ▼
MdpDealerOperationsService / WebHookService / TestService
   │   uses
   ▼
OkHttpService          AzureB2CTokenGenerationService
   │                       │
   │                       ▼
   │                   OkHttpService → Azure B2C (token URL)
   ▼
External API (MDP)
   │
   ▼
JsonHelperService → DTO  →  GeneralResponse → HTTP response
                                  │
                                  ▼
                          (on failure path) AuditLogService → AuditLogRepo → MySQL
```

### Outbound — high-level wiring
```
ServiceBusProcessorClient (BffServiceBusConfig)
   │   processMessage(...)
   ▼
MdpDealerDataConsumerService
   │   uses JsonHelperService, AuditLogService, Context
   ▼
DealerDataPasserService
   │   parallelStream over MDP_BFF_EXTERNAL_CLIENTS
   │   AsyncJobService.submitJob(Runnable)
   ▼
DealerDataProcessorFactory.getProcessor(client)
   │   returns one of:
   ▼
KnowlarityDealerDataProcessorService → KnowlarityApiCallerService → Knowlarity API
SingleInterfaceDealerDataProcessorService → SingleInterfaceApiCallerService (+ SingleInterfaceOperationService) → SI API
LatLongDealerDataProcessorService → LatLongApiCallerService → LatLong API
DakshaDealerDataProcessorService → DakshaApiCallerService → Daksha API
   │
   ▼
(failure)  FailedMessageExceptionHandlerService
   ├── FailedMdpMessageExceptionRepo (DB row)
   ├── FailureEventTypeInfoService.shouldTriggerMailFor (cooldown check)
   └── NotificationSenderService → Notification API
```

### Class responsibilities (highlights)

| Class | Stereotype | Responsibility |
|---|---|---|
| `BffApplication` / `OutboundApplication` | `@SpringBootApplication` | Entry points; enable `@EnableCaching`, `@EnableRetry`, `@EnableScheduling` |
| `MdpController` | `@RestController` | Thin controller; delegates to `MdpDealerOperationsService` |
| `WebHookController` | `@RestController` | Path-typed binding; delegates to `WebHookService` |
| `MdpDealerOperationsService` (inbound) | `@Service` | Validate → fetch B2C token → call MDP → translate response. `@Retryable` on each public method. |
| `WebHookService` | `@Service` | Audit + route by `(MdpModule, ExternalClient)` switch |
| `SingleInterfaceWebhookHandlerService` | `@Service` | Per-event-type handler skeleton (`processWebhookRequest`) |
| `AzureB2CTokenGenerationService` | `@Service` | Form-urlencoded POST for OAuth2 token; wraps as `Bearer <token>` |
| `OkHttpService` | `@Service` | Generic `getRequest`, `postRequest`, `getRequestUrlEncoded`, `postRequestWithParam`; returns `ApiCallResponse` with `responseCode`, `responseData`, `isSuccessful`, `metrics.timeTakenInMs` |
| `OkHttpConfig` | `@Configuration` | Builds the `OkHttpClient` bean: trust-all `X509TrustManager`, `readTimeout(0)`, hostname verifier accepts all |
| `JsonHelperService` | `@Service` | Jackson `ObjectMapper` with `JavaTimeModule`; `fromJson`, `fromJsonToList`, `fromJsonToNode`, `toJson` |
| `AuditLogService` | `@Service` | `saveLog(tag, metadata)` / `(metadata)` / `(tag, metadata, ex)`; trims at 4000 chars |
| `CacheService` | `@Service` | `put`, `putIfAbsent`, `getStringFromCache`, `remove` keyed by `CacheName` enum |
| `RestExceptionHandler` | `@ControllerAdvice` | Maps `ValidationException`→400, `Exception`→500, `HttpMessageNotReadableException`→400, `TypeMismatchException`→400 |
| `Context` | utility (ThreadLocal) | `userId`, `userToken`, `uuid`/`transactionId`. Cleared in `MdpDealerDataConsumerService.consumeMessage` `finally` block |
| `GeneralUtils` | utility | Null/empty checks, `validateAndSanitize`, `generateSomeUuid`, list validators (see §7) |
| `BffServiceBusConfig` | `@Configuration` | Builds `ServiceBusProcessorClient` bean: session-aware, `PEEK_LOCK`, `disableAutoComplete`, `maxConcurrentSessions=10`, `processMessage` lambda calls `MdpDealerDataConsumerService.consumeMessage` then `context.complete()` |
| `MdpDealerDataConsumerService` | `@Service` | Deserialize `MdpServiceBusIncomingMessagePayloadBody`, set `Context`, audit `SAVED_SERVICE_BUS_MESSAGE`, call `DealerDataPasserService.sendDealerDataToExternalClients` |
| `DealerDataPasserService` | `@Service` | parallelStream fan-out + `AsyncJobService.submitJob`; catches `FailedMdpMessageException` → `FailedMessageExceptionHandlerService.exceptionHandler` |
| `DealerDataProcessor<T extends DealerDataClient>` | interface | `void processData(MdpServiceBusIncomingMessagePayloadBody mdpDealerData)` |
| `DealerDataProcessorFactory` | `@Service` | `switch(ExternalClient)` returns the matching processor; throws `ValidationException` for unknown |
| `KnowlarityDealerDataProcessorService` | `@Service` | Implements assign/update/un-assign workflow (see §9.1) |
| `KnowlarityApiCallerService` | `@Service` | `callPoolApi`, `callDealerUpdateApi`, `callDealerRemovalApi`; builds the partner-specific query-param map |
| `SingleInterfaceDealerDataProcessorService` | `@Service` | `createOutlet` / `closeOutlet` per `MdpStatus` |
| `SingleInterfaceApiCallerService` | `@Service` | Builds `OutletCreateRequest` / `OutletCloseRequest`, calls `/v1/Outlets/Add` / `/v1/Outlets/Close` |
| `SingleInterfaceOperationService` | `@Service` | Address splitting, lat/long formatting, derived dealer IDs, contact-person email selection, dealer-name prefixing |
| `LatLongDealerDataProcessorService` + `LatLongApiCallerService` | `@Service` | Forward MDP payload as JSON to LatLong API |
| `DakshaDealerDataProcessorService` + `DakshaApiCallerService` | `@Service` | Wrap payload in `DakshaUpdateRequest` and POST |
| `MdpDealerOperationsService` (outbound) | `@Service` | `mapDealerWithKNumber`, `unassignKNumber`; `@Retryable` |
| `AsyncJobService` | `@Service` | `Executors.newFixedThreadPool(20)`; per-job try/catch logs to `audit_log` |
| `FailedMessageExceptionHandlerService` | `@Service` | `createFailedMdpMessageException` factory; `exceptionHandler` `@Transactional`: per-`(client, failureEventType)` switch decides email subject/body, persists DB row, calls cooldown check |
| `FailureEventTypeInfoService` | `@Service` | `shouldTriggerMailFor(FailureEventType)`: true if `last_notified_time` is null OR more than `nextEmailBackoffTimeInHrs` (currently 1) ago |
| `NotificationSenderService` | `@Service` | `@Retryable(maxAttempts=3)` POST to Notification API; throws `ServiceException` on 401 / non-2xx |
| `GmbCommonService` | `@Service` | `shouldProcessDealerData(payload)` and `getMergedDealerAddress(location)` shared eligibility/format helpers |
| `CronService` | `@Service`, `@Scheduled` | `fixedRate=60_000`; logs JVM (and outbound: executor) data to `audit_log` |

### Interfaces and marker types
- `Validateable<E>` — `void validate(E e) throws ValidationException`.
- `Sanitizeable<E>` — `void sanitizeIncomingData(E e)`.
- `RequestData<E> extends Validateable<E>, Sanitizeable<E>` — combined contract for inbound REST DTOs.
- `MdpDealerRequestData<E> extends RequestData<E>` — semantic marker for MDP-bound DTOs.
- `DealerDataClient` (outbound) — base type; per-client marker classes `KNOWLARITY`, `SINGLE_INTERFACE`, `LAT_LONG`, `DAKSHA` are used purely as type parameters of `DealerDataProcessor<T extends DealerDataClient>` for compile-time documentation.

## UI Changes

Not applicable. This service has no front-end. Swagger UI is auto-generated by `springdoc` for API exploration only.

## Error Handling & Retries

### Error taxonomy
| Exception | Where thrown | Mapped to |
|---|---|---|
| `ValidationException` (inbound) | `GeneralUtils.*OrElseThrow`, DTO `validate()`, factory `getProcessor` for unknown clients | `400 Bad Request` via `RestExceptionHandler` |
| `HttpMessageNotReadableException` | Spring (malformed JSON) | `400 Bad Request` ("Un-processable request received") |
| `TypeMismatchException` | Spring (bad path / query types, e.g., unknown `MdpModule`) | `400 Bad Request` (raw exception message) |
| `ExternalServiceException` (inbound) | `MdpDealerOperationsService` on non-2xx for filter/pincode endpoints; `AzureB2CTokenGenerationService` on token failure | `500` via the generic handler |
| `Exception` (anything else) | runtime | `500 Internal Server Error` ("Internal Error occurred : <ex.message>") |
| `FailedMdpMessageException` (outbound) | partner caller services on non-2xx | Caught in `DealerDataPasserService` → `FailedMessageExceptionHandlerService.exceptionHandler` (DB + email) |
| `ServiceException` (outbound) | `NotificationSenderService` on 401 / non-2xx | propagated; logged; not surfaced to caller (consumer is the Service Bus listener) |

### Inbound MDP read response mapping
`MdpDealerOperationsService.handleValidationAndNoSuchElementException`:
- 400 → `400 BAD_REQUEST` with `errorMessage` from MDP's `errorMessage` field.
- 401 → `401 UNAUTHORIZED` with same.
- otherwise → `500 INTERNAL_SERVER_ERROR` with same.

### Retries
| Caller | Annotation | Behavior |
|---|---|---|
| `MdpDealerOperationsService.findDealerDataBySapDealerCode` / `getDealersDataBasedOnPincode` / `getDealerDataBasedOnFilters` (inbound) | `@Retryable(maxAttempts=5, backoff=@Backoff(delay=1000L, maxDelay=10000, multiplier=2.0))` | exponential backoff |
| `MdpDealerOperationsService.mapDealerWithKNumber` / `unassignKNumber` (outbound) | same `@Retryable` | |
| `KnowlarityApiCallerService.callPoolApi` / `callDealerUpdateApi` / `callDealerRemovalApi` | same | |
| `LatLongDealerDataProcessorService.sendDataToLatLong` | same | |
| `DakshaDealerDataProcessorService.sendDataToDaksha` | same | |
| `SingleInterfaceDealerDataProcessorService.createOutlet` / `closeOutlet` | same | **Note**: these methods are `private`; Spring Retry uses proxy-based AOP and does not intercept private-method calls — the `@Retryable` is effectively a no-op here. (Tracked as a risk; verify before relying on it.) |
| `AzureB2CTokenGenerationService.getAzureB2CBearerToken` | `@Retryable(value = ExternalServiceException.class, maxAttempts = 5)` | |
| `NotificationSenderService.callNotificationSendEmailNotificationApi` | `@Retryable(maxAttempts=3, backoff=...)` | |

### Timeouts
- OkHttp client (`OkHttpConfig`): `readTimeout(0, TimeUnit.SECONDS)` — i.e., **no read timeout**. Connect/write timeouts use OkHttp defaults (10s).
- This is a known risk area; see Risks in the HLD.

### Service Bus error handling
- `BffServiceBusConfig.processError` logs the error context. Messages remain locked until `complete()` is called by `processMessage`. If `consumeMessage` throws, `complete()` is **not** called, so the message returns to the queue for redelivery; after the configured Service Bus delivery-count limit, Azure routes it to the topic's DLQ.

### Failure persistence and alert cooldown
1. `FailedMdpMessageException` → `FailedMessageExceptionHandlerService.exceptionHandler` (`@Transactional`).
2. Persist row in `failed_mdp_message_exception` with `apiResponse` truncated to 200 chars.
3. `FailureEventTypeInfoService.shouldTriggerMailFor(failureEventType)`:
   ```
   info = repo.findByFailureEventType(failureEventType).orElseCreate();
   return info.lastNotifiedTime == null
          || ChronoUnit.HOURS.between(info.lastNotifiedTime, now()) > failureEventType.nextEmailBackoffTimeInHrs;
   ```
4. If true → `NotificationSenderService.sendEmailNotification(recipients, "[<env>]<subject>", body)` and update `last_notified_time`.

### Fallback behaviour
- No business fallback exists. If a partner is unreachable, the message is recorded for replay; the platform is not designed to silently drop or mock partner calls.

## Security and Compliance

### Transport
- All outbound HTTP is `https://...` (URLs come from env vars). The OkHttp client is currently configured to trust all certificates; this is acceptable for internal Azure-hosted endpoints but should be tightened for prod where possible (HLD risk).

### Service-to-service auth
- **Azure AD B2C, OAuth2 client-credentials**:
  - Token URL: `${AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL}`.
  - Body: `grant_type=client_credentials`, `client_id=${AZURE_B2C_CLIENT_ID}`, `client_secret=${AZURE_B2C_CLIENT_SECRET}`, `scope=${AZURE_B2C_SCOPE}`.
  - Token wrapped as `Bearer %s` in `Authorization` header for MDP and Notification calls.
  - Currently **not cached**; every external call generates a fresh token.

### Partner auth
- **Knowlarity** — `Authorization: ${KNOWLARITY_K_NUMBER_API_TOKEN}` (note: header name is the constant `Authorization` per `Constants.AUTH_HEADER_KEY`; partner spec is the source of truth).
- **Single Interface** — `auth: ${SI_OUTLET_API_TOKEN}` (header `auth` per `Constants.AUTH_HEADER_KEY_SI`).
- **LatLong** — `?access_token=${LATLONG_DEALER_DATA_API_TOKEN}` query param.
- **Daksha** — `token: ${DAKSHA_DEALER_UPDATE_API_TOKEN}` header.

### PII / data classification
- The Service Bus message and `failed_mdp_message_exception.mdp_dealer_data` may contain dealer-employee names, phone numbers, and email addresses (PII).
- Audit log `metadata` truncates at 4000 chars; failure DB row truncates `apiResponse` at 200 chars.
- Logs use Lombok `@Slf4j` → SLF4J → console; rely on log-aggregation retention policy. Tokens are logged at `info` level on successful B2C token acquisition (see `AzureB2CTokenGenerationService.generateAzureB2CToken`) — **flag this for production review**; recommend reducing to debug or removing entirely.

### Compliance
- No GDPR-specific handling implemented in code. Data minimization should be enforced upstream (MDP) and via log redaction policies.

## RBAC

Not implemented at the application layer. Network-level trust is the only enforcement today. Webhook endpoints in particular have no application-layer authentication; introducing a shared-secret header check (per partner) is recommended.

## Configuration Rules & Feature Flag

All configuration is via environment variables resolved into per-profile property files. Profile is selected by `ACTIVE_ENVIRONMENT` (`local | dev | uat | prod`). The complete env-var inventory is in `README.md`; below is the role each plays.

### Common
| Env var | Used by | Purpose |
|---|---|---|
| `ACTIVE_ENVIRONMENT` | both | Selects `application-<env>.properties` |
| `DATABASE_HOST_URL`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD` | both | MySQL JDBC |
| `MDP_BASE_URL` | both | Base URL for MDP APIs |
| `AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL` | both | OAuth2 token endpoint |
| `AZURE_B2C_CLIENT_ID`, `AZURE_B2C_CLIENT_SECRET`, `AZURE_B2C_SCOPE` | both | client-credentials inputs |

### Inbound-specific
| Env var | Purpose |
|---|---|
| (no extra at runtime; uses the common set) | |

### Outbound-specific
| Env var | Purpose |
|---|---|
| `MDP_DEALER_DATA_TOPIC_NAME` | Service Bus topic name |
| `MDP_DEALER_DATA_TOPIC_CONNECTION_STRING` | Service Bus auth |
| `MDP_BFF_EXTERNAL_CLIENTS` | **Feature toggle**: comma-separated `ExternalClient` values; only those listed receive the fan-out |
| `SI_OUTLET_API_BASE_URL`, `SI_OUTLET_API_TOKEN`, `SI_ENABLED_DEALER_TYPES` | Single Interface integration + per-`DealerType` enablement |
| `KNOWLARITY_K_NUMBER_API_URL`, `KNOWLARITY_K_NUMBER_API_TOKEN`, `KNOWLARITY_K_NUM_ASSIGNMENT_ENABLED_DEALER_TYPES` | Knowlarity integration + per-`DealerType` enablement |
| `LATLONG_DEALER_DATA_API_URL`, `LATLONG_DEALER_DATA_API_TOKEN` | LatLong integration |
| `DAKSHA_DEALER_UPDATE_API_URL`, `DAKSHA_DEALER_UPDATE_API_TOKEN` | Daksha integration |
| `NOTIFICATION_BASE_URL`, `NOTIFICATION_FAILURE_EMAIL_TEMPLATE_ID`, `NOTIFICATION_EMAIL_FAILURE_PRIORITY` | Notification API + email template |
| `EXTERNAL_CLIENTS_FAILURE_EMAIL_ALERT_RECIPIENTS` | Comma-separated email recipients for failure alerts |

### Spring properties of note
| Property | Default in code | Notes |
|---|---|---|
| `server.port` | `8080` | Both services |
| `server.servlet.context-path` | `/${spring.application.name}` | `/mdp-bff` and `/mdp-bff-outbound` |
| `springdoc.swagger-ui.enabled` | `true` | Toggle for API docs UI |
| `logging.level.com.azure.*` | `ERROR` | Suppresses Azure SDK noise |

### Feature toggles (operational)
- **Per-partner enablement (outbound)**: include/exclude an `ExternalClient` value in `MDP_BFF_EXTERNAL_CLIENTS`.
- **Per-dealer-type enablement** (per partner): `SI_ENABLED_DEALER_TYPES`, `KNOWLARITY_K_NUM_ASSIGNMENT_ENABLED_DEALER_TYPES`. Bound via Spring's comma-separated → `List<DealerType>` conversion.
- **Webhook event processing (inbound)**: `ExternalClient.SINGLE_INTERFACE` declares `[DEALER_UNPROCESSABLE]` as processable in code (not env-driven).

## Dependencies

### Internal (within TVS)
- **MDP** — read and write APIs (master data).
- **Notification API** — failure-alert emails.
- **Azure AD B2C** — OAuth2 IdP.
- **Azure Service Bus** — event channel from MDP.
- **Azure Database for MySQL** — operational store.

### External (third-party)
- **Knowlarity** — virtual-number/telephony provider.
- **Single Interface** — outlet/listing platform.
- **LatLong** — dealer-locator service.
- **Daksha** — internal dealer-data consumer.

### Library dependencies (key, full list in `pom.xml`)
| Library | Version | Used for |
|---|---|---|
| `spring-boot-starter-web`, `-data-jpa`, `-actuator`, `-test` | 3.5.x | Web, ORM, ops, tests |
| `spring-retry` | 1.3.4 | `@Retryable` |
| `mysql-connector-j` | 8.4.0 | JDBC |
| `hibernate-envers` | 6.6.13.Final | Entity history |
| `okhttp` | 4.12.0 | Outbound HTTP |
| `azure-messaging-servicebus` | 7.14.7 (inbound), 7.17.8 (outbound) | Service Bus client |
| `springdoc-openapi-starter-webmvc-ui` | 2.8.9 | Swagger UI |
| `guava` | 32.1.1-jre | `ImmutableMap` |
| `lombok` | 1.18.26 | Boilerplate |
| `h2` | 2.3.232 | Test DB |
| `jacoco-maven-plugin` | 0.8.11 | Coverage |

## Trade-offs & Alternatives Considered

| Decision | Choice | Alternative considered | Rationale |
|---|---|---|---|
| Repo layout | Two Spring Boot services in one repo | Single service | Inbound (sync) and outbound (async/retry-heavy) have different scaling and failure modes; isolating them reduces blast radius. Cost: shared schema. |
| HTTP client | OkHttp 4.12 with thin wrapper | Spring `WebClient` / `RestTemplate` | OkHttp's blocking model fits the synchronous, retry-friendly pattern used everywhere; predates reactive adoption in this repo. |
| Fan-out concurrency | `parallelStream` + per-task `AsyncJobService` (fixed pool of 20) | Reactive pipeline / Project Reactor | Simpler to reason about; failures on one partner do not affect others on the same message. |
| Partner dispatch | Strategy pattern + factory + enum switch | Spring `@Qualifier` map injection | Explicit `switch` is grep-friendly for vendors; small partner set means low maintenance cost. |
| DB migrations | Manual SQL files in `db/migrations/` | Flyway / Liquibase | Historical choice; risk of drift across environments (called out in Risks). Flyway is recommended for the future. |
| B2C token caching | None | Cache keyed by scope/clientId with TTL | `CacheName.MDP_AUTH_B2C_TOKEN` exists but is not wired; recommended improvement. |
| Audit storage | Same MySQL DB as runtime state | Dedicated audit DB / log aggregator only | Operationally simple; size managed by 4000-char trim. |
| TLS verification | Trust-all in OkHttp | Standard truststore | Matches internal Azure-hosted endpoints; tighten for prod. |
| `@Retryable` placement | Currently on some private methods (SI processor) | Public methods only | Spring Retry uses proxy-based AOP and won't intercept self-invocation; current placement is partially ineffective and should be moved or made package-private with a separate bean. |

## Open Questions

1. Should the B2C token be cached (per `client_id`/`scope`) with a TTL aligned to `expires_in`? Today every external call refetches.
2. Is webhook authentication needed at the application layer (shared secret per partner), or is ingress-level auth sufficient?
3. Should `OkHttpConfig` enable proper TLS verification in `prod`? (Today it trusts all certificates.)
4. Should `SI_ENABLED_DEALER_TYPES` and `KNOWLARITY_K_NUM_ASSIGNMENT_ENABLED_DEALER_TYPES` be runtime-tunable (DB- or feature-flag-backed) instead of pod-restart-only?
5. Is there a desired auto-replay strategy for `failed_mdp_message_exception` rows (today they are inspected manually)?
6. Should `event` from Service Bus `ApplicationProperties` drive routing (today it's logged but unused)?
7. Should `springdoc.swagger-ui.enabled` be `false` in `prod`?

---

## Appendix A — Validation Logic Reference (`GeneralUtils`)

| Method | Behavior |
|---|---|
| `neitherNullNorEmpty(String s)` | `s != null && !s.trim().isEmpty()` |
| `isNullOrEmpty(String s)` | inverse of above |
| `isFlagEnabled(Integer)` | `value != null && value == 1` |
| `trimNullable(String)` | returns null if null/empty, else trimmed |
| `notNullOrElseThrow(Object, name)` | throws `ValidationException("<name> is NULL")` if null |
| `notNullAndNotEmptyOrElseThrow(String, name)` | not-null + non-blank-after-trim |
| `nullableButNotEmptyOrElseThrow(String, name)` | allows null; rejects non-null blank |
| `notNullNotEmptyAndAllElementsNotNullOrElseThrow(List<String>, name)` | non-null + non-empty list with no null/blank items |
| `validateAndSanitize(String, name)` | not-null + non-blank, returns trimmed value |
| `generateSomeUuid()` | `<thread-name>_<UUID>_<epoch-ms>` (used as `transactionId`) |

## Appendix B — Knowlarity Business Rules (algorithm)

`KnowlarityDealerDataProcessorService.processData(MdpServiceBusIncomingMessagePayloadBody)`:

```
1. If GmbCommonService.shouldProcessDealerData(payload) is false → skip.
   (BRANCH: requires tempDmsBranchSequence != null && != 1, parentAmdSapDealerCode set;
    AMD/AD: pass; everything else: skip)
2. pricingTier = getKnowlarityPricingTier(dealer.type)
   (AMD → AMD; BRANCH | AD → AD; else ValidationException)
3. If dealer.mdpStatus == ACTIVE:
       if dealerDetails.knowlarityVirtualNumber is set:
           updateKnowlarityApiWithDealerData()
              → KnowlarityApiCallerService.callDealerUpdateApi(payload, pricingTier, Optional.empty())
       else if shouldAssignKnowlarityVirtualNumberForDealer():
              dealerType ∈ KNOWLARITY_K_NUM_ASSIGNMENT_ENABLED_DEALER_TYPES, AND
              switch(dealerType):
                  AMD, BRANCH → true
                  AD          → true if flags.K_NUMBER_NEEDED.isEnabled == 1
                  else        → ValidationException
           pickAndAssignVirtualNumberToDealer():  (synchronized)
              Step 1: callPoolApi(panel_type=pricingTier, query_type="fetch")
                      if data is empty → throw FailedMdpMessageException(KNOWLARITY_CALL_POOL_API_EMPTY)
                      else pick data[0] {k_number, routing_cli}
              Step 2: MdpDealerOperationsService.mapDealerWithKNumber({sapDealerCode, k_number, routing_cli})
                      → returns MapDealerWithKNumberResponse (which carries knowlarityFallbackNumber)
              Step 3: callDealerUpdateApi(payload, pricingTier, Optional.of(mapResponse))
4. Else if dealer.mdpStatus == INACTIVE && knowlarityVirtualNumber is set:
       unassignVirtualNumber():
          mdpDealerOperationsService.unassignKNumber(payload)  (POST to MDP)
          knowlarityApiCallerService.callDealerRemovalApi(payload)  (query_type="delete")
5. Otherwise → no-op.
```

`KnowlarityApiCallerService.isSuccessful` treats two cases as "success":
- `200 OK` and `status == "success"`.
- `200 OK` and `status == "failure"` AND `message == "Dealer not updated"` (no-op update). Reference: JIRA `CBS02-669`.

Query parameter assembly (`generateQueryParams`) maps:
- `agent_list` → fixed `18002587555` (TVS contact number).
- `dealer_id`, `store_id` → `getKnowlarityCompliantDealerCode` (BRANCH uses `parentAmdSapDealerCode`; AMD/AD use own `sapDealerCode`).
- `branch_id` → `1` for AMD/AD; `tempDmsBranchSequence` for BRANCH.
- `fallback_number` → from `MapDealerWithKNumberResponse` (assign flow) else `dealerDetails.knowlarityFallbackNumber` (update flow).
- `panel_type` → pricingTier; `query_type` → `update | delete`.

## Appendix C — Single Interface Business Rules (algorithm)

`SingleInterfaceDealerDataProcessorService.processData`:

```
1. If dealerType not in SI_ENABLED_DEALER_TYPES → skip.
2. If GmbCommonService.shouldProcessDealerData(payload) is false → skip.
3. If mdpStatus == ACTIVE → createOutlet().
4. If mdpStatus == INACTIVE → closeOutlet().
5. Else → skip.
```

`createOutlet` calls `shouldCallCreateOutletApi` first:
```
mainLocation must exist (locations[].type == "MAIN");
showroomManager must exist (employees[].type == SHOWROOM_MANAGER);
mainLocation.pincode, latitude, longitude, city must be non-empty;
showroomManager.fullName, emailAddress, phoneNumber must be non-empty;
isAddressPresent(mainLocation): at least one of addressLine1/2/3 non-empty.
```

Field derivations (in `SingleInterfaceOperationService` and `SingleInterfaceApiCallerService`):
- `apiDealerId` / `enterpriseActualClientStoreId` rules:
  | DealerType | API_DEALER_ID | ENTERPRISE_ACTUAL_CLIENT_STORE_ID |
  |---|---|---|
  | `AMD` | `sapDealerCode` | `sapDealerCode + "1"` |
  | `AD`  | `sapDealerCode` | `sapDealerCode` |
  | `BRANCH` (requires `tempDmsBranchSequence != null && != 1`) | `parentAmdSapDealerCode` | `parentAmdSapDealerCode + tempDmsBranchSequence` |
- `businessName` = `String.format("TVS - %s", trimmed dealerName)` (`SI_DEALERSHIP_NAME_FORMAT`).
- `phone` = `knowlarityVirtualNumber` if set else `showroomManager.phoneNumber`.
- `contactPersonEmail` = `showroomManager.emailAddress` unless null/blank or equal to the placeholder `AUTOMATICALLY_CREATED@nx.tvsmotor.com` — fallback to `mainContact.emailAddress`.
- `address`/`address2`/`location`:
  - Merge `addressLine1..3` (separator " ") → strip `-` → space.
  - If length ≤ 51 → `address` = full string, `location` = `mainLocation.city`.
  - Else split into segments of ≤ 51 chars; `address` = seg[0]; `address2` = seg[1] if present; `location` = seg[2] truncated to fit `address2.length + location.length ≤ 61`. On split failure → fallback `location` = `city` with `.` → space.
- `latitude`/`longitude` formatted via `BigDecimal.setScale(13, RoundingMode.DOWN)`, trailing zeros trimmed.
- `isActiveOnDealer` = `1` if `mdpStatus == ACTIVE` else `0` (PRE_ACTIVE/INACTIVE both 0).
- `categoryOrderTypes` = comma-joined `flag.name` for flags whose name is `SALES`/`SERVICE` and `isEnabled == 1`.

`closeOutlet` posts a minimal `OutletCloseRequest { actualStoreCode = sapDealerCode }` to `/v1/Outlets/Close`.

## Appendix D — Audit `tag` taxonomy (selected)

Inbound: `INCOMING_WEBHOOK`, `MDP_GET_DEALER_DATA_BASED_ON_FILTERS_RESPONSE`, `MDP_GET_DEALER_DATA_BASED_ON_PINCODE_RESPONSE`, `MDP_AUTH_API_RESPONSE`, `JVM_MEMORY_DATA_INBOUND`, `GENERIC`.

Outbound: `SAVED_SERVICE_BUS_MESSAGE`, `KNOWLARITY_POOL_API`, `KNOWLARITY_POOL_API_EMPTY`, `KNOWLARITY_VIRTUAL_NUMBER_PICKED`, `KNOWLARITY_DEALER_UPDATE_API`, `KNOWLARITY_DEALER_UPDATE_API_SUCCESS`, `KNOWLARITY_DEALER_REMOVAL_API`, `KNOWLARITY_DEALER_REMOVAL_API_SUCCESS`, `KNOWLARITY_NUMBER_ASSIGNED_IN_MDP`, `SI_CREATE_OUTLET_API_RESPONSE`, `SI_CLOSE_OUTLET_API_RESPONSE`, `MDP_MAP_DEALER_KNUMBER_API_RESPONSE`, `MDP_UNASSIGN_KNUMBER_API_RESPONSE`, `LAT_LONG_API`, `LAT_LONG_API_RESPONSE`, `DAKSHA_DEALER_UPDATE_API`, `DAKSHA_DEALER_UPDATE_API_RESPONSE`, `NOTIFICATION_API_FAILED`, `EXCEPTION`, `JVM_MEMORY_DATA_OUTBOUND`, `GENERIC`.

## Appendix E — Glossary

- **BFF** — Backend-For-Frontend.
- **MDP** — Master Data Platform (dealer master).
- **SAP dealer code** — Primary dealer identifier.
- **Pricing tier (Knowlarity)** — `AMD` or `AD`; computed from dealer type.
- **K-number / virtual number** — Knowlarity-issued masking number.
- **DSE** — Dealer's Sales Executive.
- **PEEK_LOCK** — Service Bus receive mode where messages are locked until `complete()`.
- **DLQ** — Dead-letter queue (Service Bus or `failed_mdp_message_exception` table, contextually).
- **B2C** — Azure AD Business-to-Customer (used here as service-to-service IdP).
