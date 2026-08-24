# TVS Motor — Marketplace Service: High-Level Code Document

> Vendor onboarding reference for the `tvsm-marketplace-service` (Maven artifact `com.tvsmotor:marketplace`, version 1.0.1). All credentials, endpoint URLs, and tenant-specific values are externalised through environment variables and are intentionally omitted here.

## 1. Application Overview

The `marketplace` service is a Spring Boot 3.5 (Java 17) backend that acts as TVS Motor's integration hub between internal commerce platforms (CCP, MDP, ATP, Booking, Lead, Notification, Location-Master) and external e-commerce marketplaces (currently Flipkart; placeholders exist for Amazon, IndiaMART, Paytm).

Core responsibilities:
- Synchronise vehicle prices from internal sources to marketplace listings (OEM-as-a-seller and Dealer-as-a-seller flows).
- Receive marketplace order webhooks, persist orders, and drive them through a state-machine-based fulfilment pipeline.
- Push order, invoice, dispatch, and delivery events back to marketplaces.
- Coordinate dealer assignment (proximity + inventory based) and propagate updates to Lead Service and Booking Service.
- Provide operational APIs for cache management, async job triggering, and bulk reconciliation tasks.

Runtime form factor: a single containerised Spring Boot JAR deployed on Azure Kubernetes Service (AKS), backed by MySQL, Azure Service Bus (topics/subscriptions), and Azure AD B2C for service-to-service auth.

## 2. Major Modules / Components

| Module | Package | Purpose |
|---|---|---|
| Bootstrap | `marketplace` (root) | Spring Boot main class, enables retry, caching, scheduling |
| Configuration | `marketplace.config` | Beans for OkHttp, ObjectMapper, cache, Service Bus processors, request filter |
| Controllers (REST) | `marketplace.controller` | HTTP endpoints for orders, products, dealer tokens, Flipkart webhooks, test/ops |
| Service: Order Management | `marketplace.service.order_management` (+ `flipkart` subpkg) | State machine + per-status processors driving order lifecycle |
| Service: Price Update | `marketplace.service.flipkart`, `marketplace.service.dealer_as_a_seller.flipkart`, `marketplace.service.price_update.*` | OEM and Dealer price-update flows, bulk reconciliation |
| Service: External Integrations | `marketplace.service.{mdp, atp, booking_service, location_master, notification_service, apim_token_management, flipkart}` | Outbound API callers |
| Service: Service Bus consumers | `marketplace.service.service_bus` | Async consumers for vehicle price + booking update topics |
| Domain Entities | `marketplace.entity` (+ `order_management`, `price_update.dealer_as_a_seller`) | JPA entities with Hibernate Envers auditing |
| Repositories | `marketplace.repository.*` | Spring Data JPA repositories |
| Models / DTOs | `marketplace.model.{request, response, booking, notification, cache, interfaces}` | API request/response payloads, internal DTOs |
| Enums | `marketplace.enums.*` | Marketplace, OrderStatus, AuditLogType, CacheName, PriceUpdateFlowType, etc. |
| Cache | `marketplace.cache` | Spring `ConcurrentMapCache` plus a token cache manager |
| Cross-cutting | `marketplace.utils`, `marketplace.exceptions` | `Context` (ThreadLocal), `Constants`, exception types & global handler |
| Operational scripts | `scripts/` (bash, python, java) | AKS cron-job triggers and one-off utilities |
| CI/CD | `*-pipeline.yml`, `Dockerfile` | Build/scan/deploy pipelines and runtime image definition |

## 3. Folder Structure

```
.
├── Dockerfile                     # Multi-stage build: maven:3.9 → amazoncorretto:17 alpine
├── pom.xml                        # Maven build, Spring Boot parent 3.5.7
├── ci-pipeline.yaml / cd-pipeline.yaml
├── AST_*_Pipeline.yml             # Static analysis / image-scan pipelines
├── sonar_ci_pipeline.yml          # Sonar pipeline
├── 20250327_docker_manual_builder_and_pusher_marketplace.sh
├── HELP.md / README.md
├── LOGS_IS_UNDEFINED/             # Local log artefacts (runtime output)
├── scripts/
│   ├── bash/aks/cronjob/          # Shell triggers for AKS CronJobs (process orders, bulk price update, status sync, cancellation discrepancies)
│   ├── java/                      # Standalone helper Java files
│   └── python/                    # Ops scripts (CSV/JSON helpers, retry runners, refresh-token utilities)
└── src/main/
    ├── java/com/tvsmotor/marketplace/
    │   ├── MarketplaceApplication.java
    │   ├── cache/                 # CacheService, CacheManagerImpl, TokenCacheManager
    │   ├── config/                # CustomConfiguration, OkHttpClientConfig, ObjectMapperConfig,
    │   │                            CacheConfig, ECommerceServiceBusConfig,
    │   │                            MarketplaceOncePerRequestFilter, PostConstructThings
    │   ├── controller/            # 7 REST controllers
    │   ├── entity/                # JPA entities + order_management/, price_update/
    │   ├── enums/                 # Domain enums (+ mdp/, order_management/, price_update/)
    │   ├── exceptions/            # Validation + Retryable exceptions, global handler
    │   ├── model/                 # DTOs and value objects (request/, response/, booking/, notification/, cache/, interfaces/)
    │   ├── projection/            # Spring Data projections
    │   ├── repository/            # JPA repositories
    │   ├── service/               # Business services (sub-packages by domain)
    │   └── utils/                 # Constants, Context (thread-local), AzureB2CTokenManager, GeneralUtils
    └── resources/
        ├── application.properties # Externalised config (no secrets in repo)
        ├── banner.txt
        ├── logback-spring.xml
        └── db/migration/          # Versioned SQL migrations v1.1 … v1.10
```

## 4. Core Business Workflows

### 4.1 Vehicle Price Update (CCP → Marketplace)

1. CCP publishes a price-data message to the **Vehicle Price Data** Service Bus topic.
2. `VehiclePriceDataConsumerService` consumes the message via `ServiceBusProcessorClient` (session-based, peek-lock), persists the marketplace-adjusted price into `vehicle_prices`.
3. (Legacy/test path) `VehiclePriceDataPusherService` can be invoked to fan-out a price update to all `enabled.ecommerce-marketplaces` via `VehiclePriceDataPusherFactory` → `IVehiclePriceDataPusher` implementations.
4. `FlipkartVehiclePriceDataPusher` selects the active flow(s) (`OEM_AS_A_SELLER` and/or `DEALER_AS_A_SELLER`):
   - **OEM flow:** resolve state-specific seller credentials → generate Flipkart token → resolve SKU from FSN → compare current vs. updated price → call Flipkart price-update API.
   - **Dealer flow:** `FlipkartPushDealerSpecificPriceUpdateService` per-dealer: fetch access token (refreshing via stored refresh token), look up SKU, and update price via Flipkart API.
5. `FlipkartVehiclePriceUpdatorService` enforces Flipkart's ≤30% delta rule by stepping prices in increments (`loopedPriceUpdate`) when needed.

### 4.2 Bulk Price Reconciliation (Flipkart, Dealer-as-a-Seller)

Triggered manually (`/v1/test/start-bulk-price-update-flipkart`) or via AKS CronJob.
1. `BulkPriceUpdateService` pulls every dealer's refresh token, fetches the SKU listing per dealer (parallel batches of 10), retrieves current Flipkart prices, and computes deltas against the latest CCP price snapshot.
2. SKUs with |delta| ≤ 30% are pushed via the bulk price-update API; SKUs with |delta| > 30% go through the looped step-update flow.
3. Email summaries (start/finish/discrepancies) are sent via `EmailNotificationService` → Notification API.

### 4.3 Order Lifecycle (Flipkart, Dealer-as-a-Seller)

Webhook-driven, then state-machine-driven:

```
[Flipkart Webhook] → FlipkartWebhookController → FlipkartOrderWebhookService
   │
   ├── shipment-created → create Order/OrderDetails/CustomerPaymentDetails → status=CAPTURED
   ├── shipment-cancelled → status=CANCELLATION_REQUESTED (after non-cancelable check)
   │
   └── async ProductOrderProcessingStateMachine.processOrder(orderId)
         loops moveOrderForwardOneStep() through OrderStatus:
            CAPTURED → ACCEPTED → DEALER_ASSIGNED → PUSHED_TO_LS_AND_BS → APPROVED
            (waits for Booking Service event) → INVOICE_GENERATED
            → INVOICE_DATA_PUSHED_TO_3P_MARKETPLACE → SHIPPED
            (waits for gate-pass event)        → GATE_PASS_GENERATED → DELIVERED
            CANCELLATION_REQUESTED → CANCELLED
```

Key transition handlers:
- `Captured_OrderProcessService` → marketplace-specific (e.g. `Flipkart_Captured_OrderProcessorService`) to mark order ACCEPTED.
- `DealerAssigned_OrderProcessService` calls Lead Service (`pushLead`), Booking Service (`createBooking` + `updatePayment`), persists IDs, and advances to `PUSHED_TO_LS_AND_BS` → `APPROVED`.
- `OrderInvoicedHandlerService` reacts to Booking Service `INVOICED` events from the bookingUpdates topic and moves the order to `INVOICE_GENERATED`.
- `Flipkart_InvoiceGenerated_OrderProcessorService` + `FlipkartOperationalService.pushInvoiceDetails` pushes invoice to Flipkart self-ship dispatch API.
- `OrderGatePassUpdateHandlerService` processes `DELIVERED` booking events; `Flipkart_GatePassGenerated_OrderProcessService` calls `FlipkartOperationalService.pushDeliveryDetails`.
- `CancellationRequested_OrderProcessService` cancels in Booking Service if a `bookingId` exists, then sets the order to `CANCELLED`.

### 4.4 Dealer Assignment

`OrderOperationalService.getTopValidDealer` orchestrates:
1. `LocationMasterService.getLatLongFromPincode` → lat/long for the customer pincode.
2. `MdpDealerService.getListOfValidDealersBy(...)` → proximity-sorted candidate dealers (filtered by eligibility).
3. `AtpService.isPositiveInventory(sapDealerCode, partId)` → first dealer with positive ATP inventory wins.

### 4.5 Order Status Sync & Cancellation Discrepancies

- `PUT /v1/order/{marketplace}/marketplace-status?action=refresh` triggers `syncMarketplaceOrderStatus`, which polls each non-terminal order's status from the marketplace (Flipkart shipment API) and persists drift.
- `GET /v1/order/{marketplace}/cancellation-discrepancies?action=notify` finds orders flagged as `CANCELLED` by the marketplace but not internally, and emails a discrepancy report.

### 4.6 Token Generation

- **Azure AD B2C client_credentials token** for internal APIs is generated on demand by `AzureB2CTokenGenerationService`, cached in-memory by `TokenCacheManager`, and accessed via `AzureB2CTokenManager.getAzureB2CToken()` (double-checked locking on cache miss).
- **Flipkart access token (per dealer)** is fetched/refreshed on demand by `FlipkartTokenGeneratorService`. Tokens and expiry are persisted in `dealer_refresh_tokens`. A bulk warmup job is exposed at `/test/flipkart/token/generate`.

## 5. Key Services / Classes

| Class | Role |
|---|---|
| `MarketplaceApplication` | Spring Boot entry point. Enables `@EnableRetry`, `@EnableCaching`, `@EnableScheduling`. |
| `MarketplaceOncePerRequestFilter` | Tags every inbound request with a `transactionId` (ThreadLocal `Context`), records timing, persists incoming-API audit log. |
| `ECommerceServiceBusConfig` | Builds two session-based `ServiceBusProcessorClient` beans (vehicle price data, booking updates) with peek-lock + manual complete. |
| `PostConstructThings` | Starts Service Bus processor clients on app startup unless profile is `local`/`test` or receivers are disabled. |
| `OkHttpClientConfig` | Singleton `OkHttpClient` (30s read timeout). |
| `OkHttpService` | Thin wrapper used by every outbound caller. |
| `JsonHelperService` | Jackson-based serialise/deserialise helper (registers JodaModule, JavaTimeModule). |
| `AsyncJobService` | Bounded fixed-thread-pool (size 20) executor; integrates with Spring `TransactionSynchronization` for after-commit dispatch; copies `Context.transactionId` across threads. |
| `ParallelTaskExecutorService` | Batched parallel executor used by bulk flows (10-task batches with inter-batch delay). |
| `AuditLogService` | Persists structured audit log entries asynchronously into `audit_logs` (Hibernate Envers + JPA). |
| `Context` (ThreadLocal) | Carries `userId`, `serverId`, `clientId`, `transactionId`, request start time, audit log order across threads. |
| `ProductOrderProcessingStateMachine` | The order-fulfilment state machine — single dispatch loop over `OrderStatus`. |
| `OrderOperationalService` | High-level orchestrator: async order processing, transient-state batch processing, status sync, cancellation discrepancy detection. |
| `FlipkartOrderWebhookService` / `FlipkartOrderWebhookOperationalService` | Validates Flipkart webhook signature (SHA-1 hash of `xDate`+`xAuthorization`), parses payload, and routes events. |
| `FlipkartApiCallerService` | All outbound Flipkart Seller-API calls (`@Retryable` with exponential backoff, max 6 attempts). |
| `FlipkartTokenGeneratorService` | Per-dealer access-token lifecycle backed by `DealerRefreshTokenService`. |
| `BulkPriceUpdateService` | Reconciliation entry point; partitions work and dispatches to bulk vs. single price update. |
| `FlipkartVehiclePriceUpdatorService` | Implements the ≤30% delta rule and looped price stepping. |
| `FlipkartOperationalService` | Self-ship dispatch and delivery push, current-status fetch from Flipkart. |
| `BookingOperationalService` / `BookingApiCallerService` | Inbound (Service Bus) and outbound (REST) Booking integration; handles `INVOICED` and `DELIVERED` events. |
| `LeadApiCallerService` | Lead-service create/get APIs. |
| `MdpDealerService` / `MdpApiCallerService` | Dealer master-data lookups (eligibility, proximity). |
| `AtpService` / `AtpApiCallerService` | Inventory/ATP checks (skeleton in repo). |
| `LocationMasterService` / `LocationMasterApiCallerService` | Pincode → lat/long resolution. |
| `EmailNotificationService` / `NotificationApiCallerService` | Outbound email notifications via internal Notification Service. |
| `AzureB2CTokenManager` / `AzureB2CTokenGenerationService` / `TokenCacheManager` | OAuth2 client_credentials with in-memory cache. |
| `RestExceptionHandler` | `@ControllerAdvice` for global error responses. |

## 6. External Integrations

| Direction | System | Purpose | Auth |
|---|---|---|---|
| Inbound (HTTP) | Flipkart Seller webhook | Shipment created / cancelled events | `X-Date` + `X-Authorization` SHA-1 hash validation |
| Outbound (HTTP) | Flipkart Seller API | Token generation (client-credentials & refresh-token), listing search, SKU lookup, price update (single & bulk), shipment retrieval, self-ship dispatch & delivery | OAuth2 (Basic for token endpoint, Bearer thereafter) |
| Outbound (HTTP) | TVS MDP service | Dealer master, dealer eligibility, proximity-based dealer list | Azure AD B2C bearer token |
| Outbound (HTTP) | TVS Location Master | Pincode geocoding | Azure AD B2C bearer token |
| Outbound (HTTP) | TVS ATP service | Inventory check | Azure AD B2C bearer token |
| Outbound (HTTP) | TVS Lead Service | Create lead, fetch lead details | Azure AD B2C bearer token |
| Outbound (HTTP) | TVS Booking Service | Create booking, update payment, cancel booking, fetch booking details | Azure AD B2C bearer + OCP-APIM subscription key |
| Outbound (HTTP) | TVS Notification Service | Email notifications | Azure AD B2C bearer token |
| Outbound (HTTP) | Azure AD B2C | OAuth2 client_credentials token endpoint | Client ID + Secret (env-injected) |
| Inbound (AMQP) | Azure Service Bus topic — Vehicle Price Data | CCP price events; subscription `marketplace`; session-aware, peek-lock, max 50 concurrent sessions | SAS connection string |
| Inbound (AMQP) | Azure Service Bus topic — Booking Updates | Booking lifecycle events; subscription `market-place-booking-subscription`; max 10 concurrent sessions | SAS connection string |
| Outbound (DB) | MySQL 8 | Primary OLTP store; HikariCP pool (min 20, max 50) | Username/password (env-injected) |

## 7. Major Dependencies (`pom.xml`)

| Dependency | Version | Use |
|---|---|---|
| `spring-boot-starter-web` | 3.5.7 | REST API surface |
| `spring-boot-starter-data-jpa` | 3.5.7 | Persistence, repositories |
| `spring-retry` | 2.0.11 | `@Retryable` on outbound API callers |
| `azure-messaging-servicebus` | 7.17.17 | Topic consumers (sessions, peek-lock) |
| `okhttp` | 4.12.0 | HTTP client for outbound calls |
| `jackson-datatype-joda`, `jackson-datatype-jsr310` | 2.21.1 | Joda-Time and Java 8 Date/Time JSON support |
| `mysql-connector-j` | 9.6.0 | MySQL JDBC driver |
| `commons-codec` | 1.19.0 | Encoding helpers (Base64, hashing) |
| `springdoc-openapi-starter-webmvc-ui` | 2.8.11 | OpenAPI/Swagger UI |
| `hibernate-envers` | 6.6.41.Final | Entity audit history |
| `guava` | 33.4.0-jre | `Lists.partition`, `ImmutableSet`, etc. |
| `lombok` | 1.18.26 | Boilerplate reduction |
| `jacoco-maven-plugin` | 0.8.11 | Coverage reports |

## 8. Runtime Architecture

```
                       ┌────────────────────────────────────┐
                       │          AKS Pod (HOSTNAME)        │
                       │  ┌──────────────────────────────┐  │
   HTTPS (8080) ──────►│  │ Spring Boot (marketplace.jar)│  │
   /marketplace/**     │  │  - Tomcat (server.port 8080) │  │
                       │  │  - Once-Per-Request Filter   │  │
                       │  │  - REST Controllers          │  │
                       │  │  - State machine + services  │  │
                       │  │  - In-process caches         │  │
                       │  │  - Async ThreadPool (20)     │  │
                       │  │  - Service Bus session       │  │
                       │  │    processor clients (2)     │  │
                       │  └──────┬───────────────────────┘  │
                       └─────────┼──────────────────────────┘
                                 │ JDBC (Hikari)
                                 ▼
                          ┌──────────────┐
                          │   MySQL 8    │
                          └──────────────┘
        ▲                                              ▲
        │ AMQP (peek-lock)                             │ HTTPS
        │                                              │
┌──────────────────────┐                ┌──────────────┴──────────────┐
│ Azure Service Bus    │                │ Internal APIs               │
│  - vehiclePriceData  │                │ MDP / Location-Master / ATP │
│  - bookingUpdates    │                │ Lead / Booking / Notif.     │
└──────────────────────┘                │ Azure AD B2C (token)        │
        ▲                                └─────────────────────────────┘
        │ producers (CCP, Booking)                      ▲
                                                        │
                              External: Flipkart Seller API + Webhooks
```

Key runtime traits:
- Single deployable container; horizontal scaling via Kubernetes (each pod registers a `serverInstanceId` UUID and consumes its `HOSTNAME` as `k8sPodName`).
- Service Bus receivers are gated by `servicebus.receivers.enabled` and are skipped in `local`/`test` profiles to avoid contention during local runs.
- Retries (Spring-Retry) and idempotency-aware audit logging across the order pipeline; failures are recorded against `Order.lastFailureReason` / `lastFailureAt`.
- A separate `AsyncJobService` thread pool keeps long-running tasks off the request thread, with `Context` propagation for trace continuity.
- AKS CronJobs (`scripts/bash/aks/cronjob/`) schedule periodic operational triggers (process orders, sync status, bulk price update, cancellation discrepancy notification).

## 9. Important Entry Points

### REST endpoints (context-path: `/marketplace`)

| Method & Path | Controller | Purpose |
|---|---|---|
| `POST /v1/products/upsert` | `ProductsController` | Bulk upsert TVS product master |
| `POST /v1/products/{marketplace}/upsert` | `ProductsController` | Bulk upsert marketplace SKU codes (e.g. Flipkart FSN) |
| `POST /v1/dealer-refresh-token/upsert` | `DealerRefreshTokenController` | Onboard dealer Flipkart refresh tokens |
| `GET /v1/order/list?pageNo&size` | `OrderController` | Paginated order listing |
| `GET /v1/order/{orderId}` | `OrderController` | Aggregated order detail (joins Lead, Booking, Marketplace shipment) |
| `GET /v1/order/process/{marketplace}` | `OrderController` | Trigger async batch advancement of orders in transient states |
| `PUT /v1/order/{marketplace}/marketplace-status?action=refresh` | `OrderController` | Async sync of marketplace order status |
| `GET /v1/order/{marketplace}/cancellation-discrepancies?action=notify` | `OrderController` | Async cancellation discrepancy email |
| `POST /webhook/flipkart/order-management/notifications-receiver/dealer/common` | `FlipkartWebhookController` | Flipkart shipment webhook (dealer-as-seller) |
| `GET /test/flipkart/token/generate` | `FlipkartHelperController` | Pre-warm Flipkart access tokens for all dealers |
| `GET /v1/test/health` | `TestController` | Health/diagnostic info |
| `GET /v1/test/hello` | `TestController` | Echo IPs/headers for APIM debugging |
| `POST /v1/test/sendVehiclePriceDataToEcommerceClients` | `TestController` | Manual price-data fan-out |
| `GET /v1/test/start-bulk-price-update-flipkart` | `TestController` | Trigger bulk price reconciliation |
| `GET /v1/test/processOrderAsync?orderId` | `TestController` | Replay order through state machine |
| `GET /v1/test/moveOrderForwardOneStep?orderId` | `TestController` | Single-step state transition |
| `DELETE /v1/test/cache/{cacheName}/{key}` | `TestController` | Evict a cache entry |
| `GET /v1/test/service-bus/status` | `TestServiceBusController` | Show Service Bus processor status |
| `GET /v1/test/service-bus/start-receiver?receiverId` | `TestServiceBusController` | Start a receiver (1=price, 2=booking) |
| `GET /v1/test/service-bus/stop-receiver?receiverId` | `TestServiceBusController` | Stop a receiver |

### Asynchronous entry points

- `VehiclePriceData_ServiceBusProcessorClient` → `VehiclePriceDataConsumerService.consumeMessage(...)` (CCP price events).
- `BookingUpdates_ServiceBusProcessorClient` → `BookingUpdatesConsumerService.consumeMessage(...)` → `BookingOperationalService.consumeMessage(...)` (booking lifecycle events).

### Process-level entry point

- `MarketplaceApplication.main(...)` boots Spring; `PostConstructThings#startServiceBusProcessorClients` then opens AMQP receivers for non-local profiles.

## 10. High-Level Data Flow

```
                    ┌────────────────────────────────────────────────────────────┐
                    │                   Inbound channels                         │
                    └────────────────────────────────────────────────────────────┘
                       REST  ──────────────► OncePerRequestFilter ──┐
                       Webhook (Flipkart) ──────────────────────────┤
                       Service Bus (CCP price) ───────────────┐     │
                       Service Bus (Booking updates) ─┐       │     │
                                                      ▼       ▼     ▼
                                              ┌─────────────────────────┐
                                              │  Service / Orchestration│
                                              │  layer                  │
                                              │  - Validation           │
                                              │  - Audit logging        │
                                              │  - State machine        │
                                              └────────────┬────────────┘
                                                           │
              ┌───────────────────────┬────────────────────┼─────────────────────┬──────────────────────┐
              ▼                       ▼                    ▼                     ▼                      ▼
   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────┐  ┌──────────────────┐  ┌───────────────────┐
   │  MySQL (orders,    │  │ Outbound REST      │  │ In-memory      │  │ AsyncJobService  │  │ Email Notification│
   │  order_details,    │  │ - Flipkart         │  │ caches         │  │ ThreadPool (20)  │  │ (templates +      │
   │  audit_logs,       │  │ - MDP/ATP/Location │  │ (B2C token,    │  │ + ParallelTask   │  │ recipients via    │
   │  vehicle_prices,   │  │ - Lead/Booking     │  │ etc.)          │  │ ExecutorService  │  │ env vars)         │
   │  dealer_refresh_   │  │ - Notification     │  │                │  │                  │  │                   │
   │  tokens, …)        │  │ - Azure AD B2C     │  │                │  │                  │  │                   │
   └────────────────────┘  └────────────────────┘  └────────────────┘  └──────────────────┘  └───────────────────┘
```

Representative end-to-end traces:

- **Price update (CCP → Flipkart):** Service Bus message → `VehiclePriceDataConsumerService` → `VehiclePriceService.upsertVehiclePrice` → (manual or scheduled) `BulkPriceUpdateService.bulkPriceUpdate` → `FlipkartApiCallerService.callUpdateListingPriceApiBulk` (or single via `FlipkartVehiclePriceUpdatorService`) → audit log + summary email.

- **Order received (Flipkart → TVS):** Webhook hits `FlipkartWebhookController` → `FlipkartOrderWebhookService` validates hash, persists `Order`/`OrderDetails`/`CustomerPaymentDetails` → `OrderOperationalService.startOrderProcessingAsync` → `ProductOrderProcessingStateMachine` walks status → at `DEALER_ASSIGNED`, `LeadApiCallerService` + `BookingApiCallerService` are called; status advances to `APPROVED`.

- **Invoice → Marketplace:** Booking Service publishes `INVOICED` to bookingUpdates topic → `BookingUpdatesConsumerService` → `OrderInvoicedHandlerService` updates Order to `INVOICE_GENERATED` → state machine → `Flipkart_InvoiceGenerated_OrderProcessorService` → `FlipkartOperationalService.pushInvoiceDetails` (self-ship dispatch API).

- **Delivery confirmation:** Booking Service `DELIVERED` event → `OrderGatePassUpdateHandlerService` → `GATE_PASS_GENERATED` → `Flipkart_GatePassGenerated_OrderProcessService` → `FlipkartOperationalService.pushDeliveryDetails` → status `DELIVERED`.

## Operational Notes for Vendor Onboarding

- **Required env vars** (names only; values are environment-managed): `ACTIVE_ENVIRONMENT`, `DATABASE_HOST_URL`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `VEHICLE_PRICE_DATA_TOPIC_NAME`, `VEHICLE_PRICE_DATA_TOPIC_CONNECTION_STRING`, `SERVICE_BUS_BOOKING_UPDATES_TOPIC_NAME`, `SERVICE_BUS_BOOKING_UPDATES_CONNECTION_STRING`, `SERVICEBUS_RECEIVERS_ENABLED`, `ENABLED_ECOMMERCE_MARKETPLACES`, `FLIPKART_SELLER_API_BASE_URL`, `FLIPKART_OAUTH_APPLICATION_ID`, `FLIPKART_OAUTH_APPLICATION_SECRET`, `FLIPKART_WEBHOOK_NOTIFICATION_URL`, `B2C_TOKEN_URL`, `B2C_CLIENT_ID`, `B2C_CLIENT_SECRET`, `B2C_SCOPE`, `MDP_API_BASE_URL`, `LOCATION_MASTER_BASE_URL`, `LEAD_SERVICE_BASE_URL`, `BOOKING_SERVICE_API_BASE_URL`, `BOOKING_SERVICE_OCP_APIM_SUBSCRIPTION_KEY`, `NOTIFICATION_SERVICE_BASE_URL`, `NOTIFICATION_EMAIL_PRICE_UPDATE_*`, `PRICE_UPDATE_PRICE_THRESHOLD_IN_INR`, `PRICE_UPDATE_FLIPKART_ENABLED_FLOWS`, `PRICE_UPDATE_FLIPKART_DEALER_AS_A_SELLER_TVS_CLIENT_ID`/`_SECRET`, `SHOW_HTTP_500_ERROR_DETAILS`, `HOSTNAME` (auto by k8s).
- **Database migrations:** Versioned SQL files in `src/main/resources/db/migration/` (v1.1 through v1.10). The build does not bundle a migration tool; ensure a tool like Flyway/Liquibase is run as part of deployment (or that schemas are pre-applied).
- **Profiles:** `local`, `test`, plus environment-specific profiles selected via `ACTIVE_ENVIRONMENT`. Service Bus consumers do not start in `local`/`test`.
- **Observability:** Audit logs in `audit_logs` table (typed via `AuditLogType`), enriched with `transactionId`. Standard Spring Boot logs route through Logback.
- **Resilience:** Spring Retry (`@Retryable` with exponential, jittered backoff) on most outbound callers; bulk operations split into batches with inter-batch sleep to respect upstream rate limits.

This document captures the externally visible architecture and integration footprint without exposing credentials or proprietary marketplace pricing logic. For a deeper dive into specific flows (e.g. price-step algorithm, exact webhook signature scheme, dealer ranking), see the linked services in §5.
