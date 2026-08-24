# Low Level Design — TVSM Marketplace Service

> Audience: New engineering vendors onboarding to the `tvsm-marketplace-service` codebase.
> Companion to `docs/HIGH_LEVEL_DESIGN.md` and `docs/HIGH_LEVEL_CODE_DOCUMENT.md`.
> Excludes credentials, tenant URLs, exact webhook secrets, and proprietary commercial rules (price thresholds, dealer ranking heuristics).

## Overview

This document describes the implementation-level design of the Marketplace Service: how requests flow from controllers to repositories, how the order state machine is structured, how external API integrations are wrapped, what validation and error handling rules apply, and how configuration is plugged in. The goal is to allow a new engineer to confidently add a feature, fix a bug, or onboard a new marketplace.

## High Level Design — Quick Recap

- See `docs/HIGH_LEVEL_DESIGN.md` for system-level architecture, deployment, and external dependencies.
- Stack: Spring Boot 3.5.7 (Java 17) on AKS; MySQL 8 via JPA/Hibernate; Azure Service Bus (sessions); OkHttp 4.12 for outbound HTTP; Spring Retry; Hibernate Envers for audit history.
- Two top-level workflows: **price update** (CCP → Marketplace) and **order lifecycle** (Marketplace → TVS internal services, driven by a state machine).

## Assumptions

- All inbound and outbound traffic to internal TVS services flows through APIM; therefore the service does not implement its own user-level authn/authz beyond webhook hash validation.
- Azure AD B2C is the identity provider for service-to-service tokens (client_credentials grant).
- Service Bus topics are pre-created with sessions enabled; the producer side (CCP, Booking) is owned by other teams and contracts are stable.
- DB schema migrations are applied by the deployment pipeline (Flyway/Liquibase) before app start; the application itself does not run migrations on boot.
- Each pod gets a unique `HOSTNAME` from Kubernetes which is used as `k8sPodName`; a 4-char `serverInstanceId` is generated at startup for log/audit correlation.
- All persisted strings respect the column-length validation rules in service-layer `validate(...)` methods; values longer than the configured cap are rejected before reaching the DB.
- Time zone for runtime + container is `Asia/Kolkata`.
- Rate-limiting on Flipkart is approximated by inter-batch sleeps (1–2s) and parallelism caps (10 concurrent tasks per batch).

## Components

### C1. Inbound HTTP layer (`controller/`)

| Controller | Path prefix | Notes |
|---|---|---|
| `OrderController` | `/v1/order` | CRUD-ish on orders, async batch triggers. Has `@CrossOrigin` for `localhost:3000` and an internal GH Pages origin (dev tooling only). |
| `ProductsController` | `/v1/products` | Bulk upsert TVS products and per-marketplace SKU codes. |
| `DealerRefreshTokenController` | `/v1/dealer-refresh-token` | Bulk upsert dealer refresh tokens (Dealer-as-a-Seller). |
| `FlipkartWebhookController` | `/webhook/flipkart/order-management` | Receives Flipkart shipment webhooks. |
| `FlipkartHelperController` | `/test/flipkart` | Pre-warm dealer access tokens. |
| `TestController` | `/v1/test` | Diagnostics / replay endpoints. |
| `TestServiceBusController` | `/v1/test/service-bus` | Start/stop/list Service Bus processor clients. |

Every request passes through `MarketplaceOncePerRequestFilter` (Spring `OncePerRequestFilter`), which:
1. Records start time via `StopWatch`.
2. Builds a per-request `transactionId` (UUID) and stores it in `Context` (a ThreadLocal holder) along with `serverId`.
3. If root logging level ≤ DEBUG, dumps headers and parameters.
4. Forwards to the controller chain.
5. On any exception, audits an `EXCEPTION` log entry then rethrows.
6. In `finally`, audits an `INCOMING_API_CALL` entry with method, path, query string, total time taken; clears the `Context`.

### C2. Service / orchestration layer (`service/`)

Organised into sub-packages by domain (`order_management`, `flipkart`, `dealer_as_a_seller`, `booking_service`, `mdp`, `atp`, `lead`/`booking_service`, `notification_service`, `apim_token_management`, `service_bus`, `price_update`).

Cross-cutting helpers:

- `OkHttpService` — single GET/POST/PUT helper backed by the singleton `OkHttpClient`. Wraps each call in `StopWatch`, builds an `ApiCallResponse(responseCode, responseData, isSuccessful, metrics)`, and writes an `OUTGOING_API_CALL` audit row.
- `JsonHelperService` — ObjectMapper wrapper (`fromJson`, `toJson`, `fromJsonToNode`, `fromJsonString` for double-encoded payloads).
- `AuditLogService` — async writer; trims metadata to 4000 chars; uses `Context.transactionId` and an incremented `logOrder`.
- `AsyncJobService` — fixed thread pool of 20; supports `waitForTransactionCompletion` to dispatch only after the current Spring transaction commits; copies the current `Context.transactionId` into the worker thread.
- `ParallelTaskExecutorService` — runs Runnables/Callables in batches of N (typically 10) with an inter-batch delay (typically 1–2s).
- `GeneralUtils` (in `service/` and `utils/`) — null/empty/length validators, date/time helpers, partitioning, UUID generation, Bearer prefixing.

### C3. State machine (`service/order_management/flipkart/ProductOrderProcessingStateMachine`)

The class is intentionally a switch on `OrderStatus`. `processOrder(orderId)` calls `moveOrderForwardOneStep(orderId)` in a loop, capping iterations at `2 × |OrderStatus|` to avoid infinite loops. Each iteration:
- Re-reads the `Order` from DB (idempotent and resumable).
- Delegates to a per-status `*_OrderProcessService` bean.
- Catches any `Exception`, persists `lastFailureReason` (truncated to 255 chars) and `lastFailureAt`, then rethrows so the async runner records the failure too.
- Returns `shouldContinue=false` for terminal/await states (`APPROVED`, `SHIPPED`, `DELIVERED`, `CANCELLED`, `INVOICE_DATA_PUSHED_TO_3P_MARKETPLACE`, `PUSHED_TO_LS_AND_BS`, `CANCELLATION_REQUESTED`).

Per-status services delegate to marketplace-specific implementations via `switch(order.getMarketplace())`. For Flipkart, the chain is:

```
Captured_OrderProcessService          → Flipkart_Captured_OrderProcessorService
Accepted_OrderProcessService          → Flipkart_Accepted_OrderProcessorService
DealerAssigned_OrderProcessService    (marketplace-agnostic)
PushedToLSAndBS_OrderProcessService   (marketplace-agnostic)
InvoiceGenerated_OrderProcessService  → Flipkart_InvoiceGenerated_OrderProcessorService
InvoiceDataPushed3P..._OrderProcessService → Flipkart_InvoiceDataPushed3PMarketplace_OrderProcessorService
GatePassGenerated_OrderProcessService → Flipkart_GatePassGenerated_OrderProcessService
CancellationRequested_OrderProcessService (marketplace-agnostic; cancels in Booking)
```

### C4. External API caller services

Each external integration has one caller service. They follow a uniform shape:
- `@Value` injects base URL.
- `OkHttpService` performs the call.
- `@Retryable(maxAttempts = …, backoff = @Backoff(delay = 2_000, multiplier = 1.5, random = true))` annotates the method.
- `JsonHelperService` deserialises to a typed response.
- A `ValidationException` or `RuntimeException` is thrown on non-2xx.

| Caller | Notable paths |
|---|---|
| `FlipkartApiCallerService` | `/oauth-service/oauth/token`, `/sellers/listings/v3/search`, `/sellers/listings/v3/update/price`, `/sellers/listings/v3/{skuIds}`, `/sellers/v3/shipments/{shipmentId}`, `/sellers/v3/shipments?orderItemIds=…`, `/sellers/v3/shipments/selfShip/dispatch`, `/sellers/v3/shipments/selfShip/delivery` |
| `BookingApiCallerService` | `/bookings`, `/bookings/search`, `/bookings/cancel` |
| `LeadApiCallerService` | `/lead-service/api/lead`, `/lead-service/api/leads/getDetails` |
| `MdpApiCallerService` | `/v1/dealer/{sapDealerCode}`, `/v1/dealers/listOfDealerDetails/basedOnProximity` |
| `LocationMasterApiCallerService` | `/location/latlong/{pinCode}` |
| `NotificationApiCallerService` | `/api/v1/notification/email` |
| `AzureB2CTokenGenerationService` | client-credentials POST to `${b2c.token.url}` |

### C5. Service Bus consumers (`service/service_bus/`)

`ECommerceServiceBusConfig` builds two beans:
- `VehiclePriceData_ServiceBusProcessorClient` — session-aware, `PEEK_LOCK`, `disableAutoComplete`, `maxConcurrentSessions=50`.
- `BookingUpdates_ServiceBusProcessorClient` — same shape, `maxConcurrentSessions=10`.

Each `onMessage` callback delegates to `VehiclePriceDataConsumerService` or `BookingUpdatesConsumerService`. After successful processing the message is `complete()`-d. Exceptions are logged but the session lock is released (no explicit abandon), so the broker redelivers per its lock-renewal/timeout config.

### C6. Caches (`cache/`)

- `CacheConfig` registers a Spring `SimpleCacheManager` with one `ConcurrentMapCache` per `CacheName` enum value (currently `AZURE_B2C_TOKEN`).
- `CacheManagerImpl` provides `put` / `putIfAbsent` / `remove` / `getStringFromCache` / `getObjectFromCache`.
- `CacheService` is a parallel facade with `@Retryable` and `CacheName` enum signatures.
- `TokenCacheManager` adapts to `AuthB2cToken { accessToken, validTillInSec }` and only returns the cached value if `validTillInSec > now` (with a 60s safety buffer).
- `AzureB2CTokenManager` performs a double-checked-locking re-fetch on cache miss.

Per-dealer Flipkart access tokens are persisted in `dealer_refresh_tokens` (not in the in-memory cache) — the DB row is the cache.

### C7. Repositories (`repository/`)

Spring Data JPA interfaces named after entities, e.g. `OrderRepo`, `OrderDetailsRepo`, `CustomerAddressDetailsRepo`, `CustomerPaymentDetailsRepo`, `TvsProductDetailsRepo`, `VehicleMarketplaceCodeRepo`, `VehiclePriceRepo`, `SellerAccessCredsRepo`, `IndianStateRepo`, `AuditLogRepo`, `DealerProductMarketplaceMappingRepo`, `DealerRefreshTokenRepo`. Custom queries appear on `OrderRepo` for status sync / cancellation discrepancies. A projection interface (`OrderIdSapDealerCodeProjection`) keeps row scans light during sync.

## API Design

> Context-path: `/marketplace`. All examples use `http://localhost:8080` for clarity. All bodies/responses use `application/json`. `GeneralResponse` is the standard envelope: `{ "data": <any>, "errorMessage": <string|null> }`. Idempotency is handled at the resource level (see notes below).

### Standard error envelope

```
HTTP 400  ValidationException
{ "errorMessage": "<violation message>", "data": null }

HTTP 500  any other Exception
{ "errorMessage": "Internal Error occurred",
  "data": { "ex.getClass": "...", "ex.getMessage": "...", "ex.getStackTrace": "..." }   // present only when SHOW_HTTP_500_ERROR_DETAILS=true
}
```

### Order APIs

#### `GET /v1/order/list?pageNo=<int>&size=<int>`

Returns paginated `Order` rows ordered by `id ASC`.

- 200 → `{ "data": [Order, ...] }`
- 400 → invalid pagination

#### `GET /v1/order/{orderId}`

Aggregated detail view; performs best-effort calls to Lead, Booking, and the marketplace shipment API. Per-call failures are caught and reported in an `exceptions` array within the response so partial data is still returned.

- 200 → `{ "data": { "order", "orderDetails", "tvsProductDetails", "customerAddressDetails", "customerPaymentDetails", "leadDetails", "bookingDetails", "shipmentDetailsFromMarketplace", "exceptions": [...] } }`
- 400 → `orderId` not found.

#### `GET /v1/order/process/{marketplace}`

Submits an async batch that advances every order in `TRANSIENT_ORDER_STATUSES` for the given marketplace. Returns immediately with 200 and a confirmation message.

#### `PUT /v1/order/{marketplace}/marketplace-status?action=refresh`

Async sync of marketplace order status against the marketplace API. `action` must equal `refresh` (case-insensitive); anything else → 400.

#### `GET /v1/order/{marketplace}/cancellation-discrepancies?action=notify`

Async notification of orders flagged CANCELLED by the marketplace but not internally. `action` must equal `notify`.

### Product / Master-Data APIs

#### `POST /v1/products/upsert`

Body: `List<TvsProductDetailsDto>`. Bulk upsert into `tvs_product_details`. Idempotent on `(part_id, model_id)` per repository semantics.

#### `POST /v1/products/{marketplace}/upsert`

Body: `List<VehicleMarketplaceCodeDto>`. Bulk upsert per `(part_id, marketplace)` into `vehicle_marketplace_codes`. Marketplace path-var is parsed as `EcommerceMarketplace`.

#### `POST /v1/dealer-refresh-token/upsert`

Body: `List<DealerRefreshTokenDto>`. Bulk upsert per `sap_dealer_code` into `dealer_refresh_tokens`.

### Flipkart Webhook

#### `POST /webhook/flipkart/order-management/notifications-receiver/dealer/common`

Required headers: `X-Date`, `X-Authorization` (prefixed `FKLOGIN <signature>`).
Body: Flipkart `FlipkartShipmentWebhookRequest` payload.

Behaviour:
1. Strip `FKLOGIN ` from `X-Authorization`.
2. Compute SHA-1 of `epochSeconds + flipkartWebhookNotificationURL + httpMethod + OAuth_ApplicationSecret`, base64-encode `<OAuth_ApplicationID>:<sha1Hash>`, compare to incoming.
3. On mismatch → throw `ValidationException("Invalid hash")` → HTTP 400.
4. On match, parse the body and dispatch by `eventType`:
   - `SHIPMENT_CREATED` → idempotent: skip if `marketplaceShipmentId` already exists; else create `Order(status=CAPTURED) + OrderDetails + CustomerPaymentDetails` per `orderItem` and trigger `startOrderProcessingAsync`.
   - `SHIPMENT_CANCELLED` → reject if any `orderItem` is in `NON_CANCELABLE_STATUSES (INVOICE_GENERATED, SHIPPED, GATE_PASS_GENERATED, DELIVERED, CANCELLED)`; otherwise mark as `CANCELLATION_REQUESTED` and trigger async processing.
   - Any other event → log warning and ignore.
5. Always returns `200 { "data": "Shipment data successfully received" }` on accepted events.

#### Idempotency rules

| Resource | Idempotency key |
|---|---|
| `Order` create from webhook | `marketplaceShipmentId` (existing rows → ignore) |
| Booking creation | `OrderDetails.bookingId` (skip if already set) |
| Marketplace price update | Compares `currentPriceOnFlipkart == updatedPrice`; equal → no-op |
| State transitions | Re-reading `Order` and dispatching by current `status` makes replays idempotent |
| Service Bus messages | `complete()` only on success → broker redelivers on failure |

### Operational APIs

| Endpoint | Body / Params | Behaviour |
|---|---|---|
| `GET /v1/test/health?sapDealerCode&property` | — | Returns active profile + diagnostic map. |
| `GET /v1/test/hello?sapDealerCode&threadSleepTimeInMs` | — | APIM passthrough echo (IPs, headers, JVM metrics). |
| `POST /v1/test/sendVehiclePriceDataToEcommerceClients?isParallel=<bool>` | `List<PriceData>` | Manual fan-out (legacy/test path). |
| `GET /v1/test/start-bulk-price-update-flipkart` | — | Trigger async bulk price reconciliation. |
| `GET /v1/test/processOrderAsync?orderId` | — | Replay an order through the state machine asynchronously. |
| `GET /v1/test/moveOrderForwardOneStep?orderId` | — | Single transition (synchronous) — for debugging. |
| `DELETE /v1/test/cache/{cacheName}/{key}` | — | Evict a cache entry (e.g. `AZURE_B2C_TOKEN/AZURE_B2C_TOKEN`). |
| `GET /v1/test/service-bus/status` | — | Returns booleans for each processor client's `isRunning()`. |
| `GET /v1/test/service-bus/start-receiver?receiverId` | `1` or `2` | Starts a stopped receiver. |
| `GET /v1/test/service-bus/stop-receiver?receiverId` | `1` or `2` | Stops + closes a receiver. |
| `GET /test/flipkart/token/generate` | — | Async warmup of dealer access tokens for all dealers. |

### Status / Error codes summary

| Source | Code | Meaning |
|---|---|---|
| Controller | 200 | Successful response (sync or async-accepted). |
| `RestExceptionHandler.handleValidationException` | 400 | `ValidationException` from the service or input layer. |
| `RestExceptionHandler.handleException` | 500 | Any other uncaught `RuntimeException`. Stack-trace included only when `SHOW_HTTP_500_ERROR_DETAILS=true`. |
| Webhook | 400 | Invalid SHA-1 hash. |
| Outbound (Spring Retry) | retried up to N (3–6) times with exponential jittered backoff before bubbling up. |

## Data Model / Schema Changes

The data model lives in MySQL 8 and is evolved via versioned SQL migrations under `src/main/resources/db/migration/v1.1 … v1.10`. Hibernate Envers maintains `*_aud` shadow tables and a shared `revinfo` table for change history.

### Core tables

| Table | Key columns | Notable constraints / indexes |
|---|---|---|
| `seller_access_credentials` | `marketplace`, `state_code`, `client_id`, `client_secret` | UK `(marketplace, state_code)` |
| `vehicle_marketplace_codes` | `part_id`, `marketplace`, `marketplace_code` | UK `(part_id, marketplace)`, UK `(marketplace, marketplace_code)` |
| `audit_log` | `transaction_id`, `type`, `tag`, `metadata`, `log_order` | metadata up to 4000 chars |
| `dealer_state_marketplace_mappings` | `sap_dealer_code`, `state_code`, `marketplace`, `marketplace_location_id` | UK `(sap_dealer_code, state_code, marketplace)` |
| `dealer_refresh_tokens` | `sap_dealer_code`, `refresh_token`, `refresh_token_expiry_time_in_sec`, `access_token`, `access_token_expiry_time_in_sec` | UK on `sap_dealer_code` and `refresh_token` |
| `indian_states` | `name`, `code` | UK on each |
| `orders` | `marketplace_*`, `status`, `marketplace_order_status`, `last_failure_reason`, `last_failure_at` | UK `(marketplace_order_item_id, marketplace)`, idx on `status` |
| `tvs_product_details` | `part_id`, `model_id`, `vehicle_type`, `lead_service_brand_code` | — |
| `order_details` | FK `order_id` (UK), FK `tvs_product_id`, `assigned_dealer_sap_code`, `lead_id`, `booking_id`, `dms_invoice_*`, `delivery_date` | UK `booking_id`, FKs to `orders` and `tvs_product_details` |
| `customer_address_details` | FK `order_id`, `type` (DELIVERY/BILLING), FK `state_id` | UK `(order_id, type)` |
| `customer_payment_details` | FK `order_id`, `marketplace_payment_id`, `paid_amount_in_inr`, `payment_mode`, marketplace breakdowns | UK on `order_id` |
| `vehicle_prices` | `part_id`, `state_code`, `exshowroom_price_in_inr` | UK `(part_id, state_code)` |
| Envers shadow tables | `*_aud` + `revinfo` | created in v1.5 / v1.7 |

### ER diagram (simplified)

```
indian_states (1) ────────────┐
                              │
orders (1) ──┬── (1) order_details ── (1) tvs_product_details
             ├── (1..N) customer_address_details ──► indian_states
             └── (1) customer_payment_details

dealer_refresh_tokens (per sapDealerCode)
dealer_state_marketplace_mappings (sapDealerCode, stateCode, marketplace, marketplace_location_id)
seller_access_credentials (marketplace, state)
vehicle_marketplace_codes (partId, marketplace) ──► tvs_product_details (by partId)
vehicle_prices (partId, stateCode)
audit_log  ◄── async writes from any component
```

### Data model flexibility

- All entities extend `BaseEntity` (id, createdAt, createdBy, updatedAt, updatedBy, version). `@PrePersist` / `@PreUpdate` set audit fields from `Context.userId` (fallback `"System"`). `@Version` enables optimistic locking on row updates.
- Adding a new field requires: (a) a migration in `src/main/resources/db/migration/`, (b) a column annotation on the entity, (c) updates to the corresponding `validate(...)` and `sanitizeIncomingData(...)` if it is user-input, (d) Envers picks up the new field automatically when re-running the audit table generation if applicable.

## Class & Interface Design

### Service contracts (`service/interfaces/`)

```
Validateable<E>                  void validate(E e)
Sanitizeable<E>                  void sanitizeIncomingData(E e)
Saveable<E>                      E save(E e)
SaveableWithValidateAndSanitize  E saveWithValidateAndSanitize(E e)  // typically validate → sanitize → save
OrderProcessor                   Order process(Order order)          // marketplace dispatch
IVehiclePriceDataPusher          void pushVehiclePriceData(NaturalizedPartPriceData data)
```

Most entity-bound services implement all four CRUD-ish interfaces (e.g. `OrderService`, `OrderDetailsService`, `AuditLogService`, `TvsProductDetailsService`).

### Class arrangement (key clusters)

```
controller.*                                ← inbound HTTP
   ↓ (calls)
service/order_management/
   OrderOperationalService                  ← top-level orchestrator
       ↓
   service/order_management/flipkart/
      ProductOrderProcessingStateMachine    ← state-machine loop
         ↓ (per status)
      *_OrderProcessService                 ← marketplace-agnostic dispatch
         ↓
      Flipkart_*_OrderProcessorService      ← marketplace-specific behavior
         ↓ (calls)
      FlipkartOperationalService            ← Flipkart business operations
         ↓
      FlipkartApiCallerService              ← raw HTTP to Flipkart Seller API
         ↓
      OkHttpService                         ← single OkHttpClient

service/service_bus/
   VehiclePriceDataConsumerService          ← inbound CCP price events
   BookingUpdatesConsumerService → BookingOperationalService.consumeMessage
                                          ↓
                                       OrderInvoicedHandlerService / OrderGatePassUpdateHandlerService
                                          ↓ (loops back to state machine)

service/flipkart/
   FlipkartTokenGeneratorService            ← per-dealer token lifecycle
   FlipkartVehiclePriceDataPusher           ← OEM vs Dealer flow chooser
   FlipkartPushDealerSpecificPriceUpdateService
   FlipkartVehiclePriceUpdatorService       ← ≤30% delta + looped step update
   BulkPriceUpdateService                   ← reconciliation entry
   FlipkartSellerSkuService                 ← listing search + SKU lookup helpers

cache/
   CacheManagerImpl ◄── TokenCacheManager ◄── AzureB2CTokenManager
                                                  ▲
                                                  │
                                    AzureB2CTokenGenerationService

config/
   MarketplaceOncePerRequestFilter
   ECommerceServiceBusConfig (×2 ProcessorClients)
   PostConstructThings (gates Service Bus startup)
   OkHttpClientConfig, ObjectMapperConfig, CacheConfig, CustomConfiguration
```

### State machine schematic

```
moveOrderForwardOneStep(orderId):
  switch (order.getStatus()) {
    CAPTURED                            → captured.process();          shouldContinue=true
    ACCEPTED                            → accepted.process();          shouldContinue=true
    DEALER_ASSIGNED                     → dealerAssigned.process();    shouldContinue=true
    PUSHED_TO_LS_AND_BS                 → pushedToLSandBS.process();   shouldContinue=false  (→APPROVED)
    APPROVED                            → no-op;                       shouldContinue=false
    INVOICE_GENERATED                   → invoiceGenerated.process();  shouldContinue=true
    INVOICE_DATA_PUSHED_TO_3P_MARKETPLACE→ pushed3P.process();         shouldContinue=false  (→SHIPPED)
    SHIPPED                             → no-op;                       shouldContinue=false
    GATE_PASS_GENERATED                 → gatePass.process();          shouldContinue=true   (→DELIVERED)
    CANCELLATION_REQUESTED              → cancellationRequested.process(); shouldContinue=false
    CANCELLED / DELIVERED               → no-op;                       shouldContinue=false
    default                             → no-op;                       shouldContinue=false
  }
```

## UI Changes

Not applicable — this is a backend service with no UI.

## Error Handling & Retries

### Error taxonomy

| Layer | Class | Used for | HTTP mapping (when raised in a controller call) |
|---|---|---|---|
| Service | `ValidationException extends RuntimeException` | invariant / input violations, missing entities, non-cancelable order states, unsupported marketplaces, hash mismatch | 400 |
| Service | `RetryableException extends RuntimeException` | transient external failures (e.g. B2C token generation) | retried by Spring Retry; on exhaustion bubbles as 500 |
| Service | `RuntimeException` | unhandled / unknown failure | 500 |

`RestExceptionHandler` (a `@ControllerAdvice`):
- `ValidationException` → 400 with `errorMessage = ex.getMessage()`; audited as `EXCEPTION`.
- All other `Exception` → 500 with `errorMessage = "Internal Error occurred"`. If `SHOW_HTTP_500_ERROR_DETAILS=true`, the response includes `ex.getClass`, `ex.getMessage`, and `ex.getStackTrace`. Audited as `EXCEPTION`.
- Two TODOs noted in code: handlers for Hibernate `NotFoundException` and `HttpMessageNotReadableException` (today these fall through to the generic 500 handler).

### Retry / backoff matrix

| Caller | maxAttempts | delay | multiplier | random |
|---|---|---|---|---|
| Flipkart API (most methods) | 6 | 2000ms | 1.5 | yes |
| Flipkart token-via-refresh | (annotation present but disabled at the alternate overload — see source comment) |
| Booking API methods | 5 | 2000ms | 1.5 | yes |
| Lead API methods | 6 | 2000ms | 1.5 | yes |
| MDP API methods | 5 | 2000ms | 1.5 | yes |
| Notification email | 3 | 1000ms | 2.0 | (default) |
| Azure B2C token | 5 | (default backoff); only retries on `RetryableException` |
| Booking SB consumer (`BookingOperationalService.consumeMessage`) | 3 | 2000ms | 1.5 | yes |

### Timeout thresholds

- OkHttp read timeout: 30s (`OkHttpClientConfig`).
- OkHttp connect/write timeouts default to OkHttp library defaults.
- DB connection timeout / max lifetime governed by Hikari defaults; pool sized 20–50.

### Fallback mechanism

- Per-call fallbacks are minimal — failures propagate to the audit log + `Order.lastFailureReason`. The state machine itself is the recovery mechanism: rerun on schedule (`/v1/order/process/{marketplace}` cron) advances any orders stuck in transient states.
- For aggregated GET endpoints (e.g. `GET /v1/order/{orderId}`), per-source failures are caught and surfaced as a parallel `exceptions` list rather than aborting the whole response.
- For Service Bus, refusing to `complete()` triggers redelivery; sustained failures land in the dead-letter queue (queue-side configuration).

## Security and Compliance

### Encryption

- In transit: All external/internal HTTP traffic is TLS-terminated at APIM / load balancer. Outbound HTTP uses HTTPS URLs (configured via env var). AMQP to Azure Service Bus uses TLS by default through `azure-messaging-servicebus`.
- At rest: MySQL encryption-at-rest is a platform concern; refresh/access tokens are stored in plaintext in DB columns (`VARCHAR(100)`); short-lived access tokens are also persisted. Future iteration: column-level encryption.

### Authentication / Authorisation

- **Service-to-service (TVS internal)**: APIM gates the inbound side; the Marketplace Service obtains an Azure AD B2C bearer token via `client_credentials` grant for outbound calls. See §"Authentication / Authorization Flow" in HLD for the sequence.
- **Marketplace integration (Flipkart)**: Two flows.
  - **OEM-as-Seller**: `client_credentials` grant per state's `seller_access_credentials` row. Token is generated on demand; not cached at app level today (per-call generation).
  - **Dealer-as-Seller**: long-lived `refresh_token` per dealer in DB; short-lived `access_token` derived on demand and cached in the same DB row with `access_token_expiry_time_in_sec`.
- **Webhook validation**: Flipkart `X-Authorization` header is verified against a recomputed SHA-1 hash. Includes a 0–8ms random sleep (`sleepRandom(8)`) prior to comparison to mitigate trivial timing attacks.
- **Authorisation**: no in-app role/permission model. APIM is the perimeter for internal callers; webhook relies on the cryptographic check. Operational ("test") endpoints are protected by APIM access policy.

### PII handling

The service stores customer name, mobile, address, pincode, payment id, and amount on the order entities. Considerations:
- Name + contact + address tuples are PII. Logging is audit-tagged but raw payloads can include them at DEBUG (Flipkart webhook body is logged at INFO). Production logging should remain at INFO and avoid header/body dumps.
- Audit log metadata is truncated to 4000 chars but is unredacted; treat `audit_log` as PII-bearing.
- No GDPR-specific erasure flow exists in code today; if required, a deletion job per `(orderId)` deleting from `customer_address_details`, `customer_payment_details`, and the corresponding `*_aud` rows would be the implementation point.

### Token management

- B2C token: cached in-memory per pod; eviction via `DELETE /v1/test/cache/AZURE_B2C_TOKEN/AZURE_B2C_TOKEN`.
- Flipkart dealer access token: persisted; refreshed on demand when `expiry < now`. A buffer constant (`TOKEN_EXPIRY_BUFFER_IN_SEC = 60s`) is defined for safety windows.
- Flipkart OEM token: not cached; regenerated per call. (Performance optimisation candidate.)
- Refresh tokens are not rotated by the service; lifecycle is owned by Flipkart's seller console and onboarding.

## RBAC (Role-Based Access Control)

Not applicable inside the service. APIM-side policy controls who can call internal endpoints. The webhook endpoint trusts only valid Flipkart-signed payloads.

## Configuration Rules & Feature Flags

All configuration is externalised via env vars; properties are referenced from `src/main/resources/application.properties`.

### Feature flags / behavioural toggles

| Property / env | Effect |
|---|---|
| `SERVICEBUS_RECEIVERS_ENABLED` | Master switch; `PostConstructThings` skips Service Bus startup when `false` or profile is `local`/`test`. |
| `ENABLED_ECOMMERCE_MARKETPLACES` | Comma-separated list; controls which `IVehiclePriceDataPusher` implementations the legacy fan-out invokes. |
| `PRICE_UPDATE_FLIPKART_ENABLED_FLOWS` | `OEM_AS_A_SELLER`, `DEALER_AS_A_SELLER`, or both. Read by `FlipkartVehiclePriceDataPusher`. |
| `PRICE_UPDATE_PRICE_THRESHOLD_IN_INR` | Threshold value (currently referenced but the `<` check is commented out in `VehiclePriceDataPusherService`). |
| `SHOW_HTTP_500_ERROR_DETAILS` | When `true`, `RestExceptionHandler` includes class/message/stack-trace in 500 responses. Off in PROD by default. |
| `flipkart.tentativeDeliveryDaysFromInvoiceDate` | Days added to invoice date for `FlipkartSelfshipDispatch` request. Default 15. |
| `logging.level.root` | INFO by default. The request filter only dumps headers/params at DEBUG or below. |
| `notification.email.priceUpdate.priority` / `templateId` / `recipients` | Email dispatch parameters for bulk-price-update + cancellation-discrepancy emails. |

### Profile-specific behaviour

- `local` / `test`: Service Bus consumers are not started by `PostConstructThings` regardless of `SERVICEBUS_RECEIVERS_ENABLED`.
- Each environment has its own `ACTIVE_ENVIRONMENT` value used as `spring.profiles.active`.

### Configuration handling pattern

- Inject single values with `@Value("${some.property}")`.
- Inject typed lists with `@Value` + Spring's built-in conversion (`List<EcommerceMarketplace>`, `List<PriceUpdateFlowType>`, `List<String>`).
- Bean definitions for runtime metadata (`serverInstanceId`, `k8sPodName`) live in `CustomConfiguration`.
- Per-pod startup wiring lives in `PostConstructThings` (`@PostConstruct`).

## Dependencies

### Internal (TVS) services

| Dependency | Guarantees / Assumptions |
|---|---|
| MDP service | Available 24×7; returns proximity-sorted dealer list and dealer master. |
| Location-Master | Pincode → lat/long resolution; bearer-token protected. |
| ATP service | Inventory check API. (Implementation skeleton in repo; fully wired upstream.) |
| Lead service | `pushLead` is idempotent on its side; returns a stable `leadId`. |
| Booking service | Create/update/cancel APIs; emits `INVOICED` and `DELIVERED` events on the bookingUpdates topic; requires an APIM subscription key in addition to bearer token. |
| Notification service | Accepts an `EmailNotificationRequest` with template id, priority, recipients, body. |
| Azure AD B2C | Token endpoint (client_credentials), available 24×7. |
| Azure Service Bus | Two pre-created topics with sessions enabled; subscriptions named `marketplace` and `market-place-booking-subscription`. |
| MySQL 8 | Primary store with HikariCP pool; ALTERS run by deployment pipeline before app start. |

### External services

| Dependency | Guarantees / Assumptions |
|---|---|
| Flipkart Seller API | `@Retryable` mitigates transient failures; rate-limits are respected via inter-batch sleeps. |
| Flipkart Webhook | Sends `SHIPMENT_CREATED` / `SHIPMENT_CANCELLED` events with SHA-1 hash + base64 signature. |

### Library dependencies (selected, see `pom.xml`)

`spring-boot-starter-web 3.5.7`, `spring-boot-starter-data-jpa 3.5.7`, `spring-retry 2.0.11`, `azure-messaging-servicebus 7.17.17`, `okhttp 4.12.0`, `mysql-connector-j 9.6.0`, `commons-codec 1.19.0`, `hibernate-envers 6.6.41.Final`, `springdoc-openapi-starter-webmvc-ui 2.8.11`, `jackson-datatype-{joda,jsr310} 2.21.1`, `guava 33.4.0-jre`, `lombok 1.18.26`.

## Validation Logic

Each entity-bound service implements `Validateable<E>` and `Sanitizeable<E>` with a `saveWithValidateAndSanitize(...)` method that runs validate → sanitize → save in order. Examples:

- `OrderService.validate`:
  - `marketplaceShipmentId`, `marketplaceOrderId`, `marketplaceOrderItemId` non-null, non-empty, ≤100 chars.
  - `status`, `marketplace`, `marketplaceOrderDate` non-null.
  - `lastFailureReason` ≤255 chars (when present).
  - `marketplaceOrderStatus` ≤50 chars (when present).
- `OrderService.sanitizeIncomingData`:
  - Trims string fields, uppercases `marketplaceOrderStatus`.
- `OrderDetailsService.validate`:
  - `orderId`, `tvsProductId` non-null; `quantity` positive.
  - `leadId` ≤50 chars; `bookingId` ≤50 chars; `dmsInvoiceNumber` ≤100; `dmsInvoiceDate` ≤100; `assignedDealerSapCode` ≤25; `deliveryDate` ≤30; reasons/sub-reasons ≤255.
- `AuditLogService.validate`:
  - `transactionId` ≤100; `metadata` ≤4000; `logOrder` positive.
- `BookingEventPayload`-driven services:
  - `OrderInvoicedHandlerService` rejects null `InvoiceDetails`, missing `OrderDetails`, and non-`APPROVED` order status.
  - `OrderGatePassUpdateHandlerService` rejects null `GatePassDetails` or empty `vehicleDeliveryDate`, and non-`SHIPPED` order status.

Webhook payload validation (`FlipkartShipmentWebhookRequest.validateAndSanitize()`) is invoked before dispatch.

## Key Algorithms / Business Rules

### A1. Vehicle price normalisation (CCP → marketplace price)

```
if engineType == ICE:
   marketplacePrice = ex_showroom_price
else if engineType == EV:
   marketplacePrice = ex_showroom_price - famesubsidy + softwareupgrade
else:
   throw ValidationException("Invalid engine type")
```

State name from CCP is mapped to `state_code` via `IndianStatesService.getStateCodeByStateNameOrElseThrow`.

### A2. Flipkart price update with ≤30% delta rule

`FlipkartVehiclePriceUpdatorService.updatePriceData`:
1. Reject if either price < 4 (Flipkart minimum) or both equal.
2. Compute `deltaPercentAbsolute = |100 × (updated - current) / current|`.
3. If `deltaPercentAbsolute ≤ 30` → single PATCH via `callUpdateListingPriceApi`.
4. If `> 30` → step-wise loop:
   - Increase: each step `newPrice = floor(currentInFK × 1.30)`; final step jumps to `updatedExShowRoomPrice` once `newPrice ≥ target`.
   - Decrease: each step `newPrice = ceil(currentInFK × 0.70)`; final step jumps to `updatedExShowRoomPrice` once `newPrice ≤ target`.
   - 2s sleep between steps.
   - Hard cap at 100 iterations (`LOOP_COUNT_MAX_LIMIT`) for safety.

### A3. Bulk price update batching

```
for each dealer (parallel batches of 10, 1s delay):
  fetch SKU listing
  fetch current Flipkart prices in batches of 10
  compute SkuPriceChangeData = (skuId, productId, currentPrice, updatedPrice, absoluteDelta%)
   filter:
     - currentPrice not null
     - CCP has price for (productId, stateCode)
     - currentPrice != CCP price
   partition by absoluteDelta:
     - ≤ 30 → callUpdateListingPriceApiBulk in batches of 10
              if any SKU fails → retry one-by-one via FlipkartVehiclePriceUpdatorService
     - >  30 → updateSinglePriceDataParallely (looped step update per SKU, parallel)
```

Email notifications: `bulkPriceUpdateInitiate` at start, `bulkPriceUpdateSummary` at end (with elapsed time and dealer count).

### A4. Dealer assignment

```
PointLocation = LocationMasterService.getLatLongFromPincode(pincode)
candidates    = MdpDealerService.getListOfValidDealersBy(point, stateCode, partId, marketplace)   # already proximity-sorted
for c in candidates:
   if AtpService.isPositiveInventory(c.sapDealerCode, partId):
      return c.sapDealerCode
return null   # caller decides fallback
```

### A5. Webhook hash validation (Flipkart)

```
timestamp        = epoch_seconds(parse(xDate, "EEE, dd MMM yyyy HH:mm:ss 'GMT'XXX"))
combinedString   = timestamp + flipkart.webhook.notification.url + "POST" + OAuth_ApplicationSecret
sha1Hash         = SHA1Hex(combinedString)
expected         = base64(OAuth_ApplicationID + ":" + sha1Hash)
sleepRandom(8)                          # timing-attack mitigation
return expected.equals(xAuthorization)  # mismatch → ValidationException("Invalid hash") → 400
```

### A6. Token refresh (Dealer-as-Seller)

```
row = dealer_refresh_tokens by sapDealerCode
if row.access_token != null AND row.access_token_expiry_time_in_sec > now/1000:
   return row.access_token
else:
   resp = Flipkart /oauth-service/oauth/token?grant_type=refresh_token&refresh_token=row.refresh_token
   row.access_token = resp.access_token
   row.access_token_expiry_time_in_sec = now/1000 + resp.expires_in
   save(row)
   return resp.access_token
```

### A7. State-machine bounded loop

```
i = 0
while shouldContinue && i < OrderStatus.values().length × 2:
   shouldContinue = moveOrderForwardOneStep(orderId)
   i += 1
```

The `2×` factor prevents infinite loops in case of misconfigured transitions while still allowing for status progress through the entire state set plus a buffer.

### A8. Cancellation discrepancy detection

`OrderRepo.findOrdersWithCancellationDiscrepancies(marketplace)` returns orders where `marketplace_order_status` (synced from Flipkart) is `CANCELLED` while internal `status` is anything else. The result is emailed via `EmailNotificationService.sendEmailNotificationCancellationDiscrepancies`.

## Trade-offs & Alternatives Considered

| Decision | Picked | Alternatives | Why |
|---|---|---|---|
| Order orchestration | In-process state machine | Workflow engine (Camunda/Temporal); Saga over messaging | Linear, bounded pipeline; lower ops overhead; idempotent design covers replays. |
| HTTP client | OkHttp 4 | Spring `RestTemplate`/`WebClient` | Simple, battle-tested; project already standardised on it. |
| Cache | `ConcurrentMapCache` (process-local) | Redis | Low-cardinality cached items (B2C token, with short TTL); avoids extra infra. |
| Message lock mode | PEEK_LOCK + manual complete | RECEIVE_AND_DELETE | At-least-once with retry/DLQ semantics is required for financial flows. |
| Async dispatch | `ExecutorService` (size 20) + `ParallelTaskExecutorService` | Spring `@Async` / Reactor | Explicit control over batch size, sleep, and `Context` propagation. |
| Token storage (dealer) | DB column | External vault | Volume (1 row per dealer) and simple lifecycle; vault adoption is a future iteration. |
| Retry strategy | `@Retryable` per-method | Resilience4j circuit breaker | Spring Retry already pulled in; backoff + jitter satisfies the current resilience needs. |
| Migration tooling | Versioned SQL files (no in-app runner) | Flyway/Liquibase as Spring dependency | Pipeline owns migrations to avoid coupling app readiness to schema state. |
| Webhook idempotency | Skip if existing `marketplaceShipmentId` | Unique constraint + conflict handler | Skip-on-exists is safer for Flipkart's at-least-once delivery and produces a single `INFO` audit log on duplicates. |
| Validation surface | Service-layer `validate(...)` | Bean Validation (`@Valid`/`@NotNull`) annotations | Centralises business-rule validation alongside save logic and supports composite max-length checks. |

## Open Questions

- **Order replay scope when a downstream PUT fails mid-flow** (e.g., Lead succeeds, Booking fails): today the order remains at `DEALER_ASSIGNED` until the next replay; should we explicitly mark a sub-status to disambiguate "lead exists, no booking yet"?
- **Token rotation policy for dealer refresh tokens** (Flipkart limits to 180 days). What is the operational SOP for proactive rotation? Should the service expose a job to alert at e.g. T-30 days?
- **Multi-pod handling of single-order processing**: two pods can pick up the same `processOrder(orderId)` if the same trigger lands on different pods (e.g. webhook + cron at the same time). State-machine reads protect from divergence, but we do not hold a per-order pessimistic lock today.
- **OEM token caching**: every OEM-flow update generates a fresh client-credentials token; should we cache per `(marketplace, stateCode)` similar to the B2C token to reduce token-endpoint load?
- **`AsyncJobService` queue back-pressure**: queue is unbounded; under pathological load, memory could grow. Should we switch to a bounded queue + caller-runs policy?
- **`Validateable` adoption**: not every entity-bound service implements it (some services skip sanitisation when fields are server-set only). Worth a refactor pass for consistency?
- **Hibernate `NotFoundException` and `HttpMessageNotReadableException` handlers** are TODO in `RestExceptionHandler` — add 404 / 400 mappings respectively.
- **Privacy / PII redaction** in `audit_log.metadata`: do we need a redaction step for stored payload snippets (names, contact, address)?
- **OpenAPI publication**: `springdoc-openapi-starter-webmvc-ui` is on the classpath but Swagger UI access policy / publication is not documented; do we expose it externally?

## Appendix

### File index for new joiners

| Topic | Path |
|---|---|
| Bootstrapping | `src/main/java/com/tvsmotor/marketplace/MarketplaceApplication.java` |
| Request filter | `…/config/MarketplaceOncePerRequestFilter.java` |
| Service Bus wiring | `…/config/ECommerceServiceBusConfig.java`, `…/config/PostConstructThings.java` |
| State machine | `…/service/order_management/flipkart/ProductOrderProcessingStateMachine.java` |
| Order orchestration | `…/service/order_management/OrderOperationalService.java` |
| Webhook signature | `…/service/order_management/flipkart/FlipkartOrderWebhookOperationalService.java` |
| Flipkart APIs | `…/service/flipkart/FlipkartApiCallerService.java` |
| Bulk reconcile | `…/service/flipkart/BulkPriceUpdateService.java` |
| Token mgmt | `…/utils/AzureB2CTokenManager.java`, `…/service/flipkart/FlipkartTokenGeneratorService.java` |
| Audit | `…/service/AuditLogService.java`, `…/entity/AuditLog.java` |
| Migrations | `src/main/resources/db/migration/v1.1 … v1.10` |
| Properties | `src/main/resources/application.properties` |
| Container | `Dockerfile` |
| Pipelines | `ci-pipeline.yaml`, `cd-pipeline.yaml`, `sonar_ci_pipeline.yml`, `AST_Image_Scan_marketplace_Pipeline.yml`, `AST_MDP_marketplace_UAT_Pipeline.yml`, `AST_MDP_marketplace_PROD_Pipeline.yml` |
| AKS CronJobs | `scripts/bash/aks/cronjob/` |

### Glossary

| Term | Meaning |
|---|---|
| AKS | Azure Kubernetes Service |
| APIM | Azure API Management |
| ATP | Available-to-Promise (inventory service) |
| B2C | Azure AD B2C (token IdP for service-to-service) |
| BS | Booking Service |
| CCP | Central Commerce / Pricing platform (price-data producer) |
| DMS | Dealer Management System |
| FSN | Flipkart's product code |
| LS | Lead Service |
| MDP | Master Data Platform (dealer master) |
| OEM | Original Equipment Manufacturer |
| SAP Dealer Code | Dealer identifier shared with SAP / DMS |
| SKU | Stock Keeping Unit |

### Status of this document

Authored from the source tree at the current commit. Excludes credentials, tenant URLs, exact webhook secrets, proprietary pricing thresholds, and detailed ranking heuristics. Intended for internal teams and external partners onboarding to development/maintenance work on the Marketplace Service.
