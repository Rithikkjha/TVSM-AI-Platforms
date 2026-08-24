# High Level Design — TVSM Marketplace Service

> Audience: External engineering partners working with TVS Motor on marketplace integrations.
> Scope: `tvsm-marketplace-service` (Maven artifact `com.tvsmotor:marketplace`, version 1.0.1).
> Confidential commercial logic, credentials, tenant URLs, and pricing rules are intentionally excluded.

---

## Overview

The Marketplace Service is the integration backbone between TVS Motor's internal commerce platforms and external e-commerce marketplaces (Flipkart today; placeholders for Amazon, IndiaMART, Paytm). It synchronises vehicle prices outbound to marketplaces, ingests marketplace orders inbound, and orchestrates the order fulfilment lifecycle by coordinating Lead, Booking, MDP (dealer master), ATP (inventory) and Notification services.

Built on Spring Boot 3.5 (Java 17), it runs as a stateless container on Azure Kubernetes Service, backed by MySQL and Azure Service Bus, with Azure AD B2C providing service-to-service tokens for internal APIs.

## Tier Classification

**Tier 2 — Business Critical, not Life-or-Death.**

Rationale:
- Direct revenue impact from marketplace orders, but failures degrade rather than halt vehicle sales (offline / dealer channels remain available).
- Outages stall price synchronisation and order ingestion; recovery via replays from Service Bus and idempotent retries is supported.
- No safety-of-life or regulatory real-time obligations.

## Background

TVS Motor sells vehicles and accessories on third-party marketplaces under two commercial models:
- **OEM-as-a-Seller**: TVS is the seller of record; one seller account per state.
- **Dealer-as-a-Seller**: each dealer holds its own seller account.

Earlier point-to-point integrations entangled marketplace-specific logic across multiple internal systems (CCP for prices, Lead, Booking, DMS for invoicing) and lacked a single owner for marketplace lifecycle, retries, audit, and reconciliation. The Marketplace Service centralises that responsibility behind a single contract per marketplace, with state-machine-driven order processing and bulk reconciliation jobs.

## Requirements

### Functional

- Receive vehicle price events from CCP and propagate state-specific marketplace prices.
- Support OEM-as-a-Seller and Dealer-as-a-Seller price update flows.
- Receive Flipkart shipment-created and shipment-cancelled webhooks; persist orders.
- Drive each order through a fulfilment state machine: capture → dealer assignment → lead/booking creation → invoicing → dispatch → gate-pass → delivery, with cancellation as a parallel terminal path.
- Assign a dealer to an order using proximity (lat/long from pincode), dealer eligibility (MDP), and positive inventory (ATP).
- Push invoice-dispatch and delivery confirmations to Flipkart self-ship APIs.
- Reconcile prices across all dealer SKUs in bulk on demand or on schedule.
- Detect and notify cancellation discrepancies between marketplace and internal status.
- Provide ops endpoints to manage caches, replay orders, start/stop Service Bus receivers, and pre-warm dealer tokens.

### Non-Functional

| Attribute | Target / Approach |
|---|---|
| Availability | ≥ 99.5% during business hours; AKS rolling deploys; multi-replica |
| Latency | Webhook acknowledgement < 2s P99; outbound API calls protected by 30s read timeout |
| Throughput | Webhook + price events handled at marketplace volume; up to 50 concurrent Service Bus sessions for price topic, 10 for booking topic |
| Resilience | Spring Retry with exponential jittered backoff on outbound calls; peek-lock + manual complete on Service Bus; Hibernate transactions; idempotent state machine |
| Observability | Per-request `transactionId` propagated across threads; structured audit log (`audit_logs` table); standard Spring Boot logs via Logback |
| Security | OAuth2 client_credentials (Azure AD B2C) for internal APIs; per-dealer Flipkart access tokens with refresh rotation; SHA-1 hash validation on Flipkart webhooks |
| Auditability | Hibernate Envers on all critical entities; per-event audit log entries with type, level, transaction id |
| Configurability | All endpoints, secrets, topic names, enabled marketplaces and flows externalised via env vars |

## Current Architecture (HLD)

Prior state was a set of point-to-point integrations across CCP, Lead, Booking, DMS, MDP and ATP, with marketplace-specific glue code embedded in each consumer. There was no single owner for marketplace lifecycle, retries, or reconciliation. (Detailed prior-state diagrams remain with the platform team.)

## Proposed Architecture (HLD)

```
                         Flipkart Seller          Flipkart Webhook
                              APIs                    (HTTPS)
                                ▲                         │
                                │                         ▼
                          ┌─────────────────────────────────────────┐
                          │         Marketplace Service             │
                          │  (Spring Boot 3.5, Java 17, AKS pod)    │
                          │                                         │
                          │  ┌────────────┐    ┌────────────────┐   │
                          │  │ REST API   │    │ Service Bus    │   │
                          │  │ + Webhook  │    │ Processors x2  │   │
                          │  └─────┬──────┘    └─────┬──────────┘   │
                          │        ▼                  ▼             │
                          │  ┌────────────────────────────────────┐ │
                          │  │  Order State Machine + Services    │ │
                          │  │  Price Update Orchestrators        │ │
                          │  │  Async Job Pool, Audit Logger      │ │
                          │  └─┬───────────────┬────────────┬─────┘ │
                          │    │               │            │       │
                          │  ┌─▼──┐ ┌──────────▼─┐ ┌────────▼────┐  │
                          │  │JPA │ │OkHttp Caller│ │In-mem Cache │  │
                          │  └─┬──┘ └─────┬───────┘ └─────────────┘  │
                          └────┼──────────┼──────────────────────────┘
                               │          │
                               ▼          ▼
                        ┌──────────┐  ┌─────────────────────────────┐
                        │ MySQL 8  │  │ Internal APIs (via APIM)    │
                        │ HikariCP │  │  - MDP, ATP, Location-Master│
                        └──────────┘  │  - Lead, Booking, Notifn.   │
                                      │  - Azure AD B2C (token IdP) │
                                      └─────────────────────────────┘
                               ▲
                               │ AMQP (peek-lock, sessions)
                       ┌───────┴───────────────────────────┐
                       │ Azure Service Bus topics          │
                       │  - vehiclePriceData (CCP producer)│
                       │  - bookingUpdates (Booking prod.) │
                       └───────────────────────────────────┘
```

> Coloring guide for dependency services/blocks (per template): in the live Confluence page, MDP, ATP, Booking, Lead, Notification, Location-Master and Azure AD B2C should be highlighted in a distinct colour to call out external dependencies. Flipkart Seller APIs and Webhooks should be highlighted as a separate external-system colour.

### Component summary

| Component | Responsibility |
|---|---|
| REST controllers (`controller/`) | Inbound HTTP for orders, products, dealer tokens, Flipkart webhooks, ops APIs |
| Once-per-request filter | Sets per-request `Context` (transaction id, server id), records timing, audits inbound calls |
| Service Bus processors (`config/ECommerceServiceBusConfig`) | Two session-aware processor clients (price events, booking events) with peek-lock and manual complete |
| Order state machine (`ProductOrderProcessingStateMachine`) | Single dispatch loop over `OrderStatus`; idempotent, bounded |
| Order processors (`order_management/*_OrderProcessService`) | One per `OrderStatus`; marketplace-specific via factory pattern |
| Price update services (`flipkart/`, `dealer_as_a_seller/`) | OEM and dealer flows; bulk reconciliation; ≤30% delta stepping |
| Outbound API callers | One per external system, all using shared `OkHttpService`, `JsonHelperService`, Spring Retry |
| Async job pool (`AsyncJobService`) | Fixed pool of 20 threads; transaction-aware; propagates `Context` |
| Parallel batched executor (`ParallelTaskExecutorService`) | Batched parallel runs with inter-batch delay for upstream rate limits |
| Audit logger (`AuditLogService`) | Async write of typed audit entries with transaction id |
| Caches | In-memory `ConcurrentMapCache` for B2C token; per-dealer Flipkart token persisted in DB |

### Pros

- Clear separation of marketplace lifecycle from upstream/downstream systems.
- Idempotent state machine; safe to replay any order from any status.
- Horizontal scalability — stateless app, sessioned consumers prevent message reordering per session.
- Backed by retries + audit log; failures localised and observable.
- Externalised configuration; each environment is fully parameterisable.

### Cons / Trade-offs

- Process-local in-memory caches (`ConcurrentMapCache`) — every pod warms its own cache; acceptable for low-cardinality items (B2C token), but not suitable for shared mutable state.
- `AsyncJobService` uses an unbounded queue under a fixed thread pool (size 20); back-pressure must be considered for very large bulk jobs.
- Looped price stepping for >30% deltas serialises updates per SKU; latency proportional to delta magnitude.
- Flipkart-specific code paths leak into shared services in places; refactor needed before adding a second marketplace.
- DB migrations are versioned SQL files but not wired to an in-app migrator (Flyway/Liquibase); migration tooling is the deployment pipeline's responsibility.

## Database Interactions

### Persistence

- MySQL 8 via Spring Data JPA / Hibernate 6, HikariCP pool (min 20, max 50). Pool sizing assumes per-pod limits multiplied by replica count stay within DB server capacity.
- Hibernate Envers audits critical entities (orders, order details, products, vehicle prices, dealer tokens).
- Migration scripts: `src/main/resources/db/migration/v1.1 … v1.10`. Pipeline runs them via Flyway/Liquibase (deployment owner).

### Core tables (illustrative)

| Table | Purpose |
|---|---|
| `orders` | Marketplace order header (status, marketplace order/item/shipment ids, last failure) |
| `order_details` | Lead id, booking id, assigned dealer, invoice + delivery dates |
| `customer_address_details` | Delivery / billing addresses by `AddressType` |
| `customer_payment_details` | Payment id, mode, amount |
| `tvs_product_details` | Internal product master (part id, model id, vehicle type, lead-service brand code) |
| `vehicle_marketplace_codes` | Per-marketplace external codes (e.g. Flipkart FSN) |
| `vehicle_prices` | Latest state-wise marketplace price per `partId` |
| `seller_access_credentials` | OEM-flow seller credentials per marketplace + state |
| `dealer_refresh_tokens` | Per-dealer Flipkart refresh + access tokens with expiry epochs |
| `indian_states` | State code/name reference data |
| `audit_logs` | Async typed audit trail with transaction id and `logOrder` |

### Read/write characteristics

- High write volume on `audit_logs` (async writer, 4KB metadata cap).
- `orders` and `order_details` are updated on each state transition; concurrency mitigated by single-threaded per-order processing through `processOrder(orderId)`.
- Price reconciliation is read-heavy across `vehicle_prices` and `dealer_refresh_tokens`.

## API Integrations

### Inbound HTTP

| Endpoint | Auth | Caller |
|---|---|---|
| `POST /webhook/flipkart/order-management/notifications-receiver/dealer/common` | SHA-1 hash of `X-Date` + `X-Authorization` (FKLOGIN prefix stripped) | Flipkart |
| `POST /v1/products/upsert`, `POST /v1/products/{marketplace}/upsert` | Internal (via APIM) | Internal admin tooling |
| `POST /v1/dealer-refresh-token/upsert` | Internal (via APIM) | Dealer onboarding tooling |
| `GET /v1/order/list`, `GET /v1/order/{id}` | Internal (via APIM) | Internal back-office |
| `GET /v1/order/process/{marketplace}` | Internal (via APIM) | AKS CronJob trigger |
| `PUT /v1/order/{marketplace}/marketplace-status?action=refresh` | Internal (via APIM) | AKS CronJob trigger |
| `GET /v1/order/{marketplace}/cancellation-discrepancies?action=notify` | Internal (via APIM) | AKS CronJob trigger |
| `GET /test/flipkart/token/generate` | Internal (via APIM) | Ops |
| `GET /v1/test/*`, `GET /v1/test/service-bus/*` | Internal (via APIM) | Diagnostics / ops |

### Outbound HTTP

| Target | Operations | Retry policy |
|---|---|---|
| Flipkart Seller API | Token (client-credentials & refresh-token), listing search, SKU lookup, price update single & bulk, shipment retrieval, self-ship dispatch, self-ship delivery | `@Retryable` max 6, exponential jittered (delay 2s, multiplier 1.5) |
| Azure AD B2C `/token` | Client-credentials grant | `@Retryable` max 5 on `RetryableException` |
| MDP service | Dealer master, eligibility, proximity-based dealers | `@Retryable` max 5, exponential jittered |
| Location-Master | Pincode → lat/long | (No explicit retry; bearer-protected) |
| ATP service | Positive-inventory check | (Skeleton in repo; future build-out) |
| Lead service | Push lead, get lead details | `@Retryable` max 6 |
| Booking service | Create booking, update payment, cancel booking, get booking details | `@Retryable` max 5 |
| Notification service | Send templated email | `@Retryable` max 3 |

All outbound HTTP uses a single `OkHttpClient` (30s read timeout). All JSON marshalling goes through one `ObjectMapper` (Joda + JSR-310 modules).

### Inbound AMQP (Azure Service Bus)

| Topic / Subscription | Producer | Mode | Concurrency |
|---|---|---|---|
| `vehiclePriceData` / `marketplace` | CCP | Session-aware, peek-lock, manual complete | 50 sessions |
| `bookingUpdates` / `market-place-booking-subscription` | Booking service | Session-aware, peek-lock, manual complete | 10 sessions |

Receivers are gated by `servicebus.receivers.enabled` and disabled in `local`/`test` profiles.

## Authentication / Authorization Flow

### Internal API → Internal API (APIM-fronted)

```
Caller ──► APIM ──► Marketplace Service
                ▲
   AzureB2CTokenManager:
   1. Cache hit? return token
   2. Cache miss → AzureB2CTokenGenerationService
       POST <B2C_TOKEN_URL>
         grant_type=client_credentials
         client_id=<B2C_CLIENT_ID>
         client_secret=<B2C_CLIENT_SECRET>
         scope=<B2C_SCOPE>
   3. Cache token (TTL = expires_in)
   4. All outbound calls add: Authorization: Bearer <token>
      Booking service additionally adds: Ocp-Apim-Subscription-Key: <key>
```

Cache miss is guarded by double-checked locking inside `AzureB2CTokenManager`.

### Marketplace Service → Flipkart

Two flows, depending on commercial model:

| Flow | Auth source | Where stored |
|---|---|---|
| OEM-as-a-Seller (per state) | Client credentials (state-specific seller `clientId` + `clientSecret`) | `seller_access_credentials` table; tokens generated on demand |
| Dealer-as-a-Seller | Per-dealer refresh token (180 days), exchanged for access token (60 days) | `dealer_refresh_tokens` table; access token cached + persisted |

`FlipkartTokenGeneratorService.getAccessToken(sapDealerCode)`:
1. Read dealer's row from DB.
2. If access token present and `accessTokenExpiryTimeInSec > now`, return it.
3. Otherwise call Flipkart `/oauth-service/oauth/token?grant_type=refresh_token`, persist new token + expiry.

A scheduled / manual job (`/test/flipkart/token/generate`) pre-warms tokens for all dealers.

### Inbound Flipkart Webhook

`FlipkartWebhookController` extracts `X-Date` and `X-Authorization`, strips `FKLOGIN` prefix, then `FlipkartOrderWebhookOperationalService.validHash(...)` re-computes the SHA-1 hash with the configured webhook secret and compares.

### Authorization

There is no in-app role/permission model. APIM is the perimeter; controllers trust authenticated callers. Webhook endpoints validate cryptographic hash. Operational ("test") endpoints rely on APIM access policy.

## External Systems

| System | Direction | Why it matters |
|---|---|---|
| Flipkart Seller API + Webhook | Bidirectional | Marketplace transactions, price updates |
| Azure AD B2C | Outbound | OAuth2 token issuer for internal APIs |
| Azure Service Bus | Inbound (consumer) | Price events from CCP, booking lifecycle from Booking |
| MDP (TVS Master Data Platform) | Outbound | Dealer master and proximity search |
| Location-Master | Outbound | Pincode geocoding |
| ATP | Outbound | Inventory availability |
| Lead service | Outbound | Lead create/get for marketplace order |
| Booking service | Outbound + inbound (via SB) | Booking create/update/cancel; lifecycle events back |
| Notification service | Outbound | Email templates, recipients, priority |
| MySQL 8 | Outbound | Primary OLTP store |

## Infrastructure Dependencies

| Layer | Dependency |
|---|---|
| Compute | Azure Kubernetes Service; pod injects `HOSTNAME`; container exposes 8080 |
| Container image | Two-stage build: `maven:3.9.14-amazoncorretto-17-alpine` → `amazoncorretto:17.0.18-alpine3.23`; entrypoint `java -XX:MaxRAMPercentage=75 -jar /usr/local/lib/marketplace.jar`; TZ `Asia/Kolkata` |
| Datastore | MySQL 8 (managed) |
| Messaging | Azure Service Bus topics: `vehiclePriceData`, `bookingUpdates` |
| Identity | Azure AD B2C |
| API gateway | APIM (provides Ocp-Apim-Subscription-Key for Booking service) |
| CronJobs | AKS CronJobs invoking shell scripts under `scripts/bash/aks/cronjob/` (process orders, sync status, bulk price update, cancellation-discrepancy notify) |
| CI/CD | Pipelines: `ci-pipeline.yaml`, `cd-pipeline.yaml`, `sonar_ci_pipeline.yml`, `AST_Image_Scan_marketplace_Pipeline.yml`, `AST_MDP_marketplace_PROD_Pipeline.yml`, `AST_MDP_marketplace_UAT_Pipeline.yml`; manual rebuild script `20250327_docker_manual_builder_and_pusher_marketplace.sh` |
| Observability | Logback (with Spring Boot ANSI), `audit_logs` table (queryable per-transaction trail) |

### Required environment variables (names only)

`ACTIVE_ENVIRONMENT`, `DATABASE_HOST_URL`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `VEHICLE_PRICE_DATA_TOPIC_NAME`, `VEHICLE_PRICE_DATA_TOPIC_CONNECTION_STRING`, `SERVICE_BUS_BOOKING_UPDATES_TOPIC_NAME`, `SERVICE_BUS_BOOKING_UPDATES_CONNECTION_STRING`, `SERVICEBUS_RECEIVERS_ENABLED`, `ENABLED_ECOMMERCE_MARKETPLACES`, `FLIPKART_SELLER_API_BASE_URL`, `FLIPKART_OAUTH_APPLICATION_ID`, `FLIPKART_OAUTH_APPLICATION_SECRET`, `FLIPKART_WEBHOOK_NOTIFICATION_URL`, `B2C_TOKEN_URL`, `B2C_CLIENT_ID`, `B2C_CLIENT_SECRET`, `B2C_SCOPE`, `MDP_API_BASE_URL`, `LOCATION_MASTER_BASE_URL`, `LEAD_SERVICE_BASE_URL`, `BOOKING_SERVICE_API_BASE_URL`, `BOOKING_SERVICE_OCP_APIM_SUBSCRIPTION_KEY`, `NOTIFICATION_SERVICE_BASE_URL`, `NOTIFICATION_EMAIL_PRICE_UPDATE_PRIORITY`, `NOTIFICATION_EMAIL_PRICE_UPDATE_TEMPLATE_ID`, `NOTIFICATION_EMAIL_PRICE_UPDATE_RECIPIENTS`, `PRICE_UPDATE_PRICE_THRESHOLD_IN_INR`, `PRICE_UPDATE_FLIPKART_ENABLED_FLOWS`, `PRICE_UPDATE_FLIPKART_DEALER_AS_A_SELLER_TVS_CLIENT_ID`, `PRICE_UPDATE_FLIPKART_DEALER_AS_A_SELLER_TVS_CLIENT_SECRET`, `SHOW_HTTP_500_ERROR_DETAILS`, `HOSTNAME` (auto, k8s).

## Data Flow / Sequence Diagrams

### S1. Vehicle price ingestion (CCP → DB)

```
CCP ─► ServiceBus.vehiclePriceData ─► VehiclePriceDataConsumerService.consumeMessage
                                       │
                                       ├── audit log SAVED_SERVICE_BUS_MESSAGE
                                       ├── jsonHelperService.fromJson(PriceData)
                                       ├── compute marketplace price (ICE vs EV rule)
                                       └── vehiclePriceService.upsertVehiclePrice ─► MySQL.vehicle_prices
```

Failure path: any exception is caught and audited as `EXCEPTION`; the Service Bus message is `complete()`-d only after successful processing.

### S2. Order received (Flipkart shipment-created)

```
Flipkart ─► POST /webhook/.../dealer/common
            │
            ├── validate SHA-1 hash (xDate + xAuthorization)
            ├── parse FlipkartShipmentWebhookRequest
            └── for each orderItem:
                  ├── orderService.buildAndSaveOrderEntity (status=CAPTURED)
                  ├── orderDetailsService.buildAndSaveOrderDetailsEntity
                  ├── customerPaymentDetailsService.buildAndSaveCustomerPaymentDetailsEntity
                  └── orderOperationalService.startOrderProcessingAsync(orderId)
                        └── AsyncJobService submits ProductOrderProcessingStateMachine.processOrder(orderId)
```

### S3. Order fulfilment state machine

```
processOrder(orderId)  loops moveOrderForwardOneStep until shouldContinue=false or exception:

CAPTURED              → Captured_OrderProcessService                → ACCEPTED
ACCEPTED              → Accepted_OrderProcessService                → DEALER_ASSIGNED
DEALER_ASSIGNED       → DealerAssigned_OrderProcessService          → PUSHED_TO_LS_AND_BS
                        ├── Lead.push  (LeadApiCallerService)
                        ├── Booking.create + updatePayment (BookingApiCallerService)
                        └── persist leadId, bookingId
PUSHED_TO_LS_AND_BS   → PushedToLSAndBS_OrderProcessService         → APPROVED  (loop stops)

Booking SB event INVOICED → OrderInvoicedHandlerService            → INVOICE_GENERATED
INVOICE_GENERATED     → Flipkart_InvoiceGenerated_OrderProcessor   → INVOICE_DATA_PUSHED_TO_3P_MARKETPLACE
                        └── FlipkartOperationalService.pushInvoiceDetails (self-ship dispatch API)
INVOICE_DATA_PUSHED.. → Flipkart_InvoiceDataPushed3PMarketplace... → SHIPPED  (loop stops)

Booking SB event DELIVERED → OrderGatePassUpdateHandlerService     → GATE_PASS_GENERATED
GATE_PASS_GENERATED   → Flipkart_GatePassGenerated_OrderProcess    → DELIVERED (loop stops)
                        └── FlipkartOperationalService.pushDeliveryDetails (self-ship delivery API)

Webhook shipment-cancelled → CANCELLATION_REQUESTED
CANCELLATION_REQUESTED → CancellationRequested_OrderProcessService → CANCELLED (loop stops)
                        └── BookingOperationalService.cancelBooking (if bookingId present)
```

Failure handling: any exception during a step is caught at `moveOrderForwardOneStep`; `Order.lastFailureReason` (truncated to 255 chars) and `Order.lastFailureAt` are persisted; the exception bubbles up so the async job records it. The state machine bounds iterations to `2 × |OrderStatus|` to prevent infinite loops.

### S4. Bulk price update (Flipkart, Dealer-as-a-Seller)

```
Trigger: GET /v1/test/start-bulk-price-update-flipkart  OR  AKS CronJob
   │
   └── BulkPriceUpdateService.bulkPriceUpdate (async)
         ├── EmailNotificationService.bulkPriceUpdateInitiate (start email)
         ├── vehiclePriceService.fetchAllMarketPlaceProductIdExShowroomPriceMap(FLIPKART)
         ├── for each dealer (parallel batches of 10, 1s delay):
         │     ├── flipkartSellerSkuService.fetchAllFlipkartSellerSkuListing
         │     ├── flipkartSellerSkuService.getSkusData (current prices)
         │     ├── compute SkuPriceChangeData (delta filter)
         │     ├── delta ≤ 30 → flipkartApiCallerService.callUpdateListingPriceApiBulk (batched)
         │     │      └── failed SKUs retried via single-update path
         │     └── delta > 30 → FlipkartVehiclePriceUpdatorService.loopedPriceUpdate (≤30% steps)
         └── EmailNotificationService.bulkPriceUpdateSummary (completion email)
```

### S5. Dealer assignment

```
OrderOperationalService.getTopValidDealer
   ├── LocationMasterService.getLatLongFromPincode(pinCode)
   ├── MdpDealerService.getListOfValidDealersBy(point, stateCode, partId, marketplace)
   └── for each candidate (already proximity-sorted):
         AtpService.isPositiveInventory(sapDealerCode, partId)
         → first match wins → return sapDealerCode
```

## Deployment & Rollout Plan

- **Build**: Maven inside Docker (`mvn clean install -DskipTests`); JaCoCo report attached to `prepare-package`; coverage gate currently 0.00 (informational).
- **Image scan**: `AST_Image_Scan_marketplace_Pipeline.yml` runs against the built image before promotion.
- **Static analysis**: `sonar_ci_pipeline.yml`.
- **Deploy**: `cd-pipeline.yaml` (UAT and PROD pipelines wired via `AST_MDP_marketplace_UAT_Pipeline.yml` and `AST_MDP_marketplace_PROD_Pipeline.yml`).
- **Rollout strategy**:
  1. Deploy to UAT, validate with synthetic Flipkart payloads and price events.
  2. PROD rollout via standard rolling update; new pods pick up Service Bus sessions only after readiness.
  3. Toggle large-scope changes via env-var feature gates: `SERVICEBUS_RECEIVERS_ENABLED`, `PRICE_UPDATE_FLIPKART_ENABLED_FLOWS`, `ENABLED_ECOMMERCE_MARKETPLACES`.
- **Rollback**:
  - Standard image rollback to previous tag; safe because the service is stateless.
  - Service Bus messages remain in subscription until processed → re-processing on rollback is supported via peek-lock + idempotent state machine.
  - For schema changes, follow expand-contract: deploy app first that tolerates both old and new schema, then run migration, then remove old paths.
- **Hotfix**: cherry-picked fix to release branch → image build → fast-track scan + deploy.

## Metrics to be Tracked

(Targets to wire post-launch; today the service surfaces these via logs / `audit_logs`.)

| Category | Metric |
|---|---|
| Webhook | `flipkart_webhook_count`, `flipkart_webhook_invalid_hash_count`, latency P50/P95 |
| Order pipeline | Orders by status; transitions/sec; `order_failure_count` (`Order.lastFailureReason` not null); time-in-status distribution |
| Service Bus | Messages consumed/sec per topic; abandon/dead-letter counts; processor `isRunning` status |
| Outbound APIs | Per-target success/failure rates; retry counts; P95 latency (Flipkart, MDP, Booking, Lead, Notification, B2C) |
| Price update | Bulk-job duration; SKUs updated; `>30% delta` step counts; failed SKU IDs |
| JVM | Heap, GC, thread pool active count (`AsyncJobService.getExecutorData`) |
| Infrastructure | DB pool active vs idle; HTTP 5xx rate; pod restarts |

Recommended alerts: Service Bus processor down; sustained 5xx on Flipkart endpoints; surge in `order_failure_count`; B2C token generation failures; cancellation discrepancy email surge.

## Data Analytics / Data Engineering Metrics & Tables

- `audit_logs` is the canonical operational fact table for transaction-level analysis (transactionId, type, tag, log_order, metadata, timestamps).
- `orders` + Hibernate Envers `orders_AUD` enable point-in-time order state reconstruction.
- `vehicle_prices` is the source-of-truth for per-state marketplace price history (audited).
- `dealer_refresh_tokens` + audit captures token rotation cadence for dealer-as-a-seller flow.
- Data-lake ingestion (CDC or batch) of these tables is recommended; specific lake-side tables are owned by the DE team and out of scope here.

## Alternatives Considered

### Option A — Embed marketplace logic in each consuming system (status quo before this service)

- Pros: no new service to operate; faster initial delivery for first marketplace.
- Cons: scattered ownership, inconsistent retry/audit, duplicate token management, hard to add a second marketplace; was the trigger for this rewrite.

### Option B — Event-driven micro-orchestrator (per-status microservices + workflow engine, e.g. Camunda / Temporal)

- Pros: visual workflow, durable execution, native retries.
- Cons: heavier ops footprint, additional infra dependency, learning curve, cost; the linear, bounded fulfilment pipeline doesn't (yet) justify it.

### Option C — Saga over messaging (each step a message)

- Pros: maximum decoupling between steps.
- Cons: harder reasoning about a single order's lineage; needs richer monitoring; chosen state-machine-in-service approach gives strong consistency per order with simpler operations.

## Risks (If Any)

- **Flipkart API changes / rate-limit changes**: heavy reliance on stable contracts; mitigated by retry+backoff and bulk APIs.
- **Token expiry storms** (180-day refresh tokens for dealers): a coordinated re-auth window is required; mitigated by warmup endpoint and `DEALER_REFRESH_TOKEN_EXPIRED` audit event.
- **Looped price stepping**: large deltas drive multiple sequential API calls; failure mid-loop leaves SKU at intermediate price until next reconciliation.
- **Service Bus session affinity**: with sessions, throughput per pod is bounded by configured concurrency (`maxConcurrentSessions`); scale-out beyond that requires more pods.
- **In-process caches**: per-pod caches mean transient inconsistencies right after deploys; tolerated by short B2C token TTLs and re-fetch on miss.
- **Schema change discipline**: migrations are loose (versioned SQL only); coordination between PR + pipeline migration step is enforced by convention, not tooling.
- **Single MySQL**: a primary outage stops the service; HA / read-replica strategy lives at the DB platform layer.

## Scalability and Resiliency Considerations

### Scalability

- **Stateless app**: any pod can serve any HTTP request; horizontal scaling via AKS replica count.
- **Service Bus consumers**: scale with replicas; sessions guarantee per-session ordering, multiple sessions per pod increase throughput. Tunable via `maxConcurrentSessions` (50 / 10 today).
- **Async job pool**: bounded at 20 threads per pod to protect downstream APIs; bulk operations are partitioned into batches of 10 with inter-batch sleeps to stay within Flipkart and internal-API rate budgets.
- **DB pool**: Hikari max 50 per pod — sized so that replica-count × 50 ≤ DB connection ceiling.
- **Caches**: in-process today; if multi-pod consistency becomes a concern, swap `ConcurrentMapCache` for a distributed cache (Redis) without changing call-sites.

### Resiliency

- **Spring Retry** on every outbound caller with exponential, jittered backoff; retry counts (3–6) reflect criticality vs. blast-radius trade-offs.
- **Service Bus**: peek-lock + manual `complete()`; failed processing leaves the message for redelivery; dead-letter destination configured at topic level.
- **State machine idempotency**: `moveOrderForwardOneStep` always re-reads the order from DB and dispatches by current `OrderStatus`; replays of the same orderId converge to the same terminal state.
- **Bounded loops**: state-machine iterations capped at `2 × |OrderStatus|`; price stepping capped at 100 iterations.
- **Audit logging on failure**: every catch-block writes an `EXCEPTION` audit row including class + message; per-order failures persisted on the order row.
- **Webhook safety**: hash validation rejects forged calls; create-event idempotent on `marketplaceShipmentId`; cancel-event refuses non-cancelable statuses.
- **Token caching with double-checked locking** prevents thundering-herd on B2C token generation.

## Appendix

### Glossary

| Term | Meaning |
|---|---|
| AKS | Azure Kubernetes Service |
| APIM | Azure API Management |
| ATP | Available-to-Promise (inventory service) |
| B2C | Azure AD B2C (token issuer used here for service-to-service tokens) |
| BS | Booking Service |
| CCP | Central Commerce / Pricing platform (price-data producer) |
| DMS | Dealer Management System |
| FSN | Flipkart's product code |
| LS | Lead Service |
| MDP | Master Data Platform (dealer master) |
| OEM | Original Equipment Manufacturer |
| SAP Dealer Code | Dealer identifier shared with SAP / DMS |
| SKU | Stock Keeping Unit |

### Key file references

- Entry point: `src/main/java/com/tvsmotor/marketplace/MarketplaceApplication.java`
- Config: `src/main/java/com/tvsmotor/marketplace/config/`
- Order state machine: `service/order_management/flipkart/ProductOrderProcessingStateMachine.java`
- Order orchestrator: `service/order_management/OrderOperationalService.java`
- Webhook entry: `controller/FlipkartWebhookController.java` + `service/order_management/flipkart/FlipkartOrderWebhookService.java`
- Price update: `service/flipkart/FlipkartVehiclePriceDataPusher.java`, `FlipkartVehiclePriceUpdatorService.java`, `BulkPriceUpdateService.java`
- Token mgmt: `utils/AzureB2CTokenManager.java`, `service/flipkart/FlipkartTokenGeneratorService.java`
- Migrations: `src/main/resources/db/migration/v1.1 … v1.10`
- Container: `Dockerfile`
- Properties: `src/main/resources/application.properties`

### Status of this document

Written for external engineering partners; suppresses credentials, tenant URLs, and proprietary commercial logic (specific pricing thresholds, dealer-ranking heuristics beyond proximity + inventory, exact webhook secret format, tax / margin rules). For deeper internal detail, see the corresponding Confluence space.
