# tvsm-marketplace-service


## Product Context


# TVS Motor Marketplace Service — Product Context

## What This Service Does

This is a backend microservice for TVS Motor Company that integrates with e-commerce marketplaces to sell two-wheeler vehicles (motorcycles and scooters) online. It handles the full lifecycle of marketplace operations: receiving orders via webhooks, processing them through a state machine, managing vehicle pricing across marketplaces, and coordinating with internal TVS systems (dealer management, booking, lead generation, inventory).

The primary operating model is **dealer-as-a-seller** — TVS dealers are registered as sellers on Flipkart, and this service orchestrates order fulfillment and price synchronization on their behalf.

## Supported Marketplaces

| Marketplace | Status | Notes |
|-------------|--------|-------|
| Flipkart | Fully implemented | Dealer-as-a-seller + OEM-as-a-seller (partial) |
| Amazon | Stub only | Price pusher interface exists, no real implementation |
| IndiaMart | Enum only | No implementation |
| Paytm | Enum only | No implementation |

## Domain Entities

### Order Management

- **Order** — A marketplace order tied to a Flipkart shipment. Tracks marketplace IDs (orderId, orderItemId, shipmentId), internal status, marketplace status, and failure info.
- **OrderDetails** — Product details for an order: assigned dealer (SAP code), TVS product reference, quantity, lead/booking IDs, invoice/delivery dates, cancellation reasons.
- **CustomerAddressDetails** — Delivery and billing addresses captured from Flipkart shipment details.
- **CustomerPaymentDetails** — Payment breakdown: paid amount, selling price, shipping charges, discounts, payment mode (COD/PREPAID).

### Product & Pricing

- **TvsProductDetails** — TVS product catalog: part ID, model ID/name, vehicle type (ICE/EV), MDP dealer flag, lead service brand code.
- **VehiclePrice** — Ex-showroom price per part ID per state code. Source of truth for marketplace pricing.
- **VehicleMarketplaceCode** — Maps TVS part IDs to marketplace-specific codes (e.g., Flipkart FSN).

### Seller & Authentication

- **SellerAccessCredentials** — OEM seller OAuth credentials (client ID/secret) per marketplace per state.
- **DealerRefreshToken** — Dealer-specific Flipkart OAuth refresh tokens with expiry tracking. Also caches access tokens.

### Infrastructure

- **AuditLog** — Comprehensive audit trail for all operations, exceptions, and API interactions.
- **IndianState** — Reference table for Indian states (name ↔ code mapping).
- **BaseEntity** — Common fields: id, createdBy, updatedBy, createdAt, updatedAt, version (optimistic locking).

## Order Processing Flow

Orders follow a state machine pattern (`ProductOrderProcessingStateMachine`):

```
CAPTURED → ACCEPTED → DEALER_ASSIGNED → PUSHED_TO_LS_AND_BS → APPROVED
    → INVOICE_GENERATED → INVOICE_DATA_PUSHED_TO_3P_MARKETPLACE → SHIPPED
    → GATE_PASS_GENERATED → DELIVERED
```

Cancellation branch: `CANCELLATION_REQUESTED → CANCELLED`

### State Transitions

| State | What Happens |
|-------|-------------|
| CAPTURED | Fetch shipment details from Flipkart, save customer addresses, move to ACCEPTED |
| ACCEPTED | Assign nearest dealer with positive inventory (location → MDP → ATP check) |
| DEALER_ASSIGNED | Push lead + booking to Lead Service and Booking Service |
| PUSHED_TO_LS_AND_BS | Terminal pause — waits for external booking confirmation |
| INVOICE_GENERATED | Push invoice/dispatch details to Flipkart self-ship API |
| INVOICE_DATA_PUSHED_TO_3P_MARKETPLACE | Terminal pause — waits for gate pass |
| GATE_PASS_GENERATED | Push delivery details to Flipkart self-ship delivery API |
| CANCELLATION_REQUESTED | Process cancellation with Flipkart |

## Price Management

### Real-Time Flow (Service Bus)
1. CCP (Central Configuration Platform) publishes price changes to Azure Service Bus topic
2. Service consumes message, calculates marketplace price (ICE vs EV formula), upserts to `vehicle_prices`
3. Pushes updated price to all enabled marketplaces for affected dealers/states

### Price Calculation
- **ICE vehicles**: `ex_showroom_price`
- **EV vehicles**: `(ex_showroom_price - famesubsidy) + softwareupgrade`

### Bulk Price Update (Scheduled)
1. Fetch all current CCP prices from DB
2. For each dealer: fetch their Flipkart SKU listings, get current Flipkart prices
3. Compare and identify deltas
4. Updates with delta >30% → individual API calls; delta ≤30% → bulk batch API calls

### Price Threshold
A configurable minimum price threshold (`priceUpdate.priceThresholdInInr`) exists but is currently commented out.

## External Integrations

| System | Purpose | Protocol |
|--------|---------|----------|
| Flipkart Seller API | Orders, listings, pricing, shipments | REST (OkHttp) |
| Azure Service Bus | Vehicle price data, booking updates | Topic/Subscription (sessions) |
| MDP (Master Data Platform) | Dealer data, proximity search | REST |
| Location Master | Pincode → lat/long conversion | REST |
| ATP Service | Dealer inventory availability check | REST |
| Lead Service | Create leads for marketplace orders | REST |
| Booking Service | Create/query bookings | REST |
| Notification Service | Email notifications | REST |
| Azure AD B2C | Service-to-service authentication | OAuth2 client credentials |

## Business Rules

- Orders cannot be cancelled once in: INVOICE_GENERATED, SHIPPED, GATE_PASS_GENERATED, DELIVERED, or CANCELLED status.
- Dealer assignment uses proximity-based selection: pincode → geo-coordinates → nearest dealers (limit 50) → first with positive ATP inventory.
- Flipkart webhook authentication uses SHA-1 hash verification with timing-attack prevention (random sleep).
- Tentative delivery date = invoice date + 15 days (configurable).
- Bulk price updates skip deltas of 0 (no change needed).
- Refresh tokens have expiry tracking; expired tokens trigger email notifications.
- Service Bus receivers are disabled in `local` and `test` environments.



## Code Structure


# TVS Motor Marketplace Service — Project Structure

## Directory Layout

```
tvsm-marketplace-service/
├── .kiro/steering/              # Kiro steering files (this documentation)
├── scripts/
│   ├── bash/aks/cronjob/        # AKS CronJob scripts (scheduled tasks triggered via curl)
│   ├── java/                    # One-off Java scripts for testing/ops
│   └── python/                  # Utility scripts (CSV/JSON conversion, token generation, retries)
├── src/
│   ├── main/
│   │   ├── java/com/tvsmotor/marketplace/
│   │   │   ├── cache/           # In-memory cache (Azure B2C token)
│   │   │   ├── config/          # Spring configuration beans
│   │   │   ├── controller/      # REST API endpoints
│   │   │   ├── entity/          # JPA entities (DB tables)
│   │   │   │   ├── order_management/   # Order, OrderDetails, CustomerAddress/Payment
│   │   │   │   └── price_update/       # DealerRefreshToken, DealerProductMarketplaceMapping
│   │   │   ├── enums/           # Enumerations (OrderStatus, EcommerceMarketplace, etc.)
│   │   │   │   ├── order_management/   # AddressType, DealerOrderAssignmentCriteria
│   │   │   │   └── price_update/       # PriceUpdateFlowType
│   │   │   ├── exceptions/      # Custom exceptions + global handler
│   │   │   │   └── handlers/    # @ControllerAdvice RestExceptionHandler
│   │   │   ├── model/           # DTOs, request/response models
│   │   │   │   ├── booking/     # Booking service models
│   │   │   │   ├── cache/       # Cache value objects (AuthB2cToken)
│   │   │   │   ├── interfaces/  # OrderProcessor interface
│   │   │   │   ├── notification/# Email notification models
│   │   │   │   ├── request/     # Inbound DTOs + Flipkart API request models
│   │   │   │   └── response/    # API response wrappers + Flipkart/MDP response models
│   │   │   ├── projection/      # JPA projections (OrderIdSapDealerCodeProjection)
│   │   │   ├── repository/      # Spring Data JPA repositories
│   │   │   │   ├── order_management/
│   │   │   │   └── price_update/
│   │   │   ├── service/         # Business logic layer
│   │   │   │   ├── amazon/      # Amazon price pusher (stub)
│   │   │   │   ├── apim_token_management/  # Azure B2C token management
│   │   │   │   ├── atp/         # ATP (Available-to-Promise) inventory check
│   │   │   │   ├── booking_service/  # Booking service integration
│   │   │   │   ├── dealer_as_a_seller/    # Dealer-specific Flipkart operations
│   │   │   │   ├── flipkart/    # Core Flipkart integration (API calls, tokens, pricing)
│   │   │   │   ├── interfaces/  # Service interfaces (Validateable, Sanitizeable, Saveable)
│   │   │   │   ├── location_master/  # Pincode → geo-coordinates
│   │   │   │   ├── mdp/         # Master Data Platform (dealer data)
│   │   │   │   ├── notification_service/  # Email notification caller
│   │   │   │   ├── order_management/      # Order state machine + processors
│   │   │   │   │   └── flipkart/          # Flipkart-specific order processors
│   │   │   │   ├── price_update/          # Price update orchestration
│   │   │   │   │   └── dealer_as_a_seller/
│   │   │   │   └── service_bus/           # Azure Service Bus consumers
│   │   │   └── utils/           # ThreadLocal context, constants, general utilities
│   │   └── resources/
│   │       └── application.properties     # All config (env-var driven)
│   └── test/java/               # Test sources (minimal coverage currently)
├── pom.xml                      # Maven build (Spring Boot 3.5.7, Java 17)
├── Dockerfile                   # Multi-stage build (Maven → Corretto 17 Alpine)
├── ci-pipeline.yaml             # Azure DevOps CI (triggers from sonar scan)
├── cd-pipeline.yaml             # Azure DevOps CD (dev → UAT → prod with approvals)
└── sonar_ci_pipeline.yml        # SonarQube analysis pipeline
```

## Module Dependencies

### Controller Layer
Controllers are thin — they validate input, delegate to services, and wrap responses in `GeneralResponse`.

- `FlipkartWebhookController` → `FlipkartOrderWebhookService`
- `OrderController` → `OrderOperationalService`, `FlipkartOperationalService`, `LeadApiCallerService`, `BookingApiCallerService`
- `ProductsController` → `TvsProductDetailsService`, `VehicleMarketplaceCodeProviderService`
- `DealerRefreshTokenController` → `DealerRefreshTokenService`
- `FlipkartHelperController` → `FlipkartTokenGeneratorService`
- `TestServiceBusController` → Direct `ServiceBusProcessorClient` management

### Service Layer — Key Dependency Chains

**Order Processing:**
```
OrderOperationalService
  → AsyncJobService (thread pool)
  → ProductOrderProcessingStateMachine
    → Captured_OrderProcessService → FlipkartApiCallerService
    → Accepted_OrderProcessService → LocationMasterService, MdpDealerService, AtpService
    → DealerAssigned_OrderProcessService → LeadApiCallerService, BookingApiCallerService
    → InvoiceGenerated_OrderProcessService → FlipkartOperationalService
    → GatePassGenerated_OrderProcessService → FlipkartOperationalService
```

**Price Updates:**
```
VehiclePriceDataConsumerService (Service Bus)
  → VehiclePriceService (upsert to DB)
  → VehiclePriceDataPusherService
    → VehiclePriceDataPusherFactory
      → FlipkartVehiclePriceDataPusher (OEM + Dealer flows)
        → FlipkartTokenGeneratorService
        → FlipkartApiCallerService
        → FlipkartPushDealerSpecificPriceUpdateService
```

**Bulk Price Update:**
```
BulkPriceUpdateService
  → DealerRefreshTokenService (all dealers)
  → FlipkartSellerSkuService (fetch listings)
  → FlipkartApiCallerService (fetch prices, update prices)
  → ParallelTaskExecutorService (batch execution)
  → EmailNotificationService (summary notification)
```

### Cross-Cutting Services

| Service | Role |
|---------|------|
| `AsyncJobService` | Fixed thread pool (20 threads), transaction-aware job submission |
| `ParallelTaskExecutorService` | Batch execution with configurable batch size and inter-batch delay |
| `AuditLogService` | Persists all operations/exceptions to `audit_log` table |
| `JsonHelperService` | Jackson ObjectMapper wrapper for serialization |
| `OkHttpService` | HTTP client wrapper (GET/POST with headers) |
| `Context` (ThreadLocal) | Request-scoped transaction ID, user ID, server ID |

## Architectural Decisions

### State Machine Pattern
Order processing uses a loop-based state machine rather than a framework (Spring State Machine). The `ProductOrderProcessingStateMachine.processOrder()` method loops calling `moveOrderForwardOneStep()` until a terminal state or exception. This keeps the flow simple and debuggable, with each state having a dedicated processor class implementing `OrderProcessor`.

### Async Processing with Transaction Awareness
`AsyncJobService` supports waiting for the current transaction to commit before executing async work. This prevents race conditions where async tasks read uncommitted data.

### Factory Pattern for Marketplace Abstraction
`VehiclePriceDataPusherFactory` returns marketplace-specific `IVehiclePriceDataPusher` implementations. This allows adding new marketplaces without modifying orchestration code.

### ThreadLocal Context
`Context` class carries request metadata (transactionId, userId, serverId) across the call stack without passing parameters. Cleaned up in `finally` blocks and the request filter.

### Optimistic Locking
All entities extend `BaseEntity` which includes a `@Version` field for optimistic concurrency control.

### Hibernate Envers Auditing
All core entities are annotated with `@Audited` for full change history tracking at the database level.

### Session-Based Service Bus
Azure Service Bus processors use session mode with PEEK_LOCK for ordered, at-least-once message processing. Max concurrent sessions: 50 for price data, 10 for booking updates.

### Retry Strategy
All Flipkart API calls use `@Retryable(maxAttempts = 6, backoff = @Backoff(delay = 2_000, multiplier = 1.5, random = true))` — exponential backoff with jitter.

### Rate Limiting Awareness
Price update flows include deliberate `Thread.sleep()` calls (1.5–2 seconds) between batches to avoid Flipkart API rate limits.

### No Security Framework
The service does not use Spring Security. Authentication is handled at the API gateway level (Azure AD B2C tokens validated externally). The `MarketplaceOncePerRequestFilter` handles request context setup only.



## Tech Stack & Dependencies


# TVS Motor Marketplace Service — Tech Stack & Conventions

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 17 |
| Framework | Spring Boot | 3.5.7 |
| Build Tool | Maven | 3.9.x (wrapper included) |
| ORM | Spring Data JPA + Hibernate | 6.6.x |
| Audit History | Hibernate Envers | 6.6.41 |
| HTTP Client | OkHttp | 4.12.0 |
| Messaging | Azure Service Bus SDK | 7.17.17 |
| Database | MySQL 8 | Connector 9.6.0 |
| Retry | Spring Retry | 2.0.11 |
| JSON | Jackson (Joda + JSR-310 modules) | 2.21.1 |
| Utilities | Google Guava | 33.4.0-jre |
| Crypto | Apache Commons Codec | 1.19.0 |
| API Docs | SpringDoc OpenAPI (Swagger UI) | 2.8.11 |
| Code Gen | Lombok | 1.18.26 |
| Testing | JUnit 5 + Mockito (via spring-boot-starter-test) | — |
| Coverage | JaCoCo | 0.8.11 |
| Code Quality | SonarQube | — |
| Container | Amazon Corretto 17 Alpine | 17.0.18 |

## Build & Run

```bash
# Local build (skip tests)
./mvnw clean install -DskipTests

# Run locally
java -jar target/marketplace.jar

# Docker build (multi-stage)
docker build -t marketplace .
```

The Dockerfile uses a two-stage build:
1. `maven:3.9.14-amazoncorretto-17-alpine` — compiles the JAR
2. `amazoncorretto:17.0.18-alpine3.23` — runtime image with curl (for CronJob health checks)

JVM flag: `-XX:MaxRAMPercentage=75` (container-aware memory sizing).

Timezone is hardcoded to `Asia/Kolkata` in the container.

## Deployment

| Environment | Trigger | Approval |
|-------------|---------|----------|
| dev | Automatic (after CI) | None |
| UAT | After dev deploy | Manual approval required |
| prod | After UAT deploy | Manual approval required |

Pipeline chain: `sonar_ci_pipeline` → `ci-pipeline` (Docker build + push) → `cd-pipeline` (Helm deploy to AKS).

Infrastructure: Azure Kubernetes Service (AKS) with Helm charts. CronJobs run as Kubernetes CronJob resources that curl internal endpoints.

## Configuration

All configuration is externalized via environment variables injected at runtime (Kubernetes ConfigMaps/Secrets). The `application.properties` file uses `${ENV_VAR}` placeholders exclusively — no hardcoded secrets.

Active profile is set via `ACTIVE_ENVIRONMENT` (values: `local`, `dev`, `uat`, `prod`, `test`).

Connection pool: HikariCP with `minimumIdle=20`, `maximumPoolSize=50`.

## Coding Conventions

### Naming
- Packages: `snake_case` for multi-word domain packages (e.g., `order_management`, `price_update`, `dealer_as_a_seller`)
- Classes: `PascalCase`, suffixed by role (`*Service`, `*Controller`, `*Repo`, `*Config`)
- Methods: `camelCase`, prefixed with verb (e.g., `findByIdOrElseThrow`, `saveWithValidateAndSanitize`)
- Constants: `UPPER_SNAKE_CASE`, defined in a `Constants` interface (static imports)
- Enums: `UPPER_SNAKE_CASE` values

### Class Structure
- Lombok annotations for boilerplate: `@Data`, `@Builder`, `@RequiredArgsConstructor`, `@Slf4j`
- Constructor injection via `@RequiredArgsConstructor` (no field injection)
- `@Qualifier` used for disambiguating multiple beans of the same type
- `@Lazy` used to break circular dependencies (e.g., `AuditLogService` ↔ `AsyncJobService`)

### Service Layer Patterns
- Services implement granular interfaces: `Validateable<E>`, `Sanitizeable<E>`, `Saveable<E>`
- Composite method pattern: `saveWithValidateAndSanitize(entity)` chains validate → sanitize → save
- Static utility methods in `GeneralUtils` (two classes: `com.tvsmotor.marketplace.service.GeneralUtils` for general utils, `com.tvsmotor.marketplace.utils.GeneralUtils` for domain-specific utils)
- `GeneralUtils` in `service` package is an `interface` with static methods (allows static import)
- `GeneralUtils` in `utils` package is a `class` with static methods

### Controller Conventions
- Thin controllers: validate input, delegate to service, wrap in `GeneralResponse`
- All responses wrapped in `GeneralResponse` (contains: `data`, `errorMessage`, `time`, `uuid`, `timeTakenInMs`, `serverId`)
- `@CrossOrigin` on controllers that serve the admin UI
- Path pattern: `/v1/{domain}/{action}` (e.g., `/v1/order/list`, `/v1/order/process/FLIPKART`)

### Entity Conventions
- All entities extend `BaseEntity` (provides `id`, `createdBy`, `updatedBy`, `createdAt`, `updatedAt`, `version`)
- `@Audited` (Hibernate Envers) on all core entities for change history
- `@Version` for optimistic locking
- `@PrePersist` / `@PreUpdate` lifecycle callbacks for audit fields
- Auto-generated IDs (`GenerationType.IDENTITY`)

### Logging
- SLF4J via Lombok `@Slf4j`
- Method entry/exit logging: `log.info("methodName() :START : param = {}", param)` / `log.info("methodName() : END")`
- Exception logging: `log.error("methodName() : Exception occurred : ", exception)` (full stack trace)
- Azure SDK logs suppressed to ERROR level

## Error Handling

### Exception Hierarchy
- `ValidationException` (extends `RuntimeException`) → HTTP 400 Bad Request
- `RetryableException` (extends `RuntimeException`) → triggers Spring Retry
- All other `RuntimeException` → HTTP 500 Internal Server Error

### Global Exception Handler (`RestExceptionHandler`)
- `@ControllerAdvice` with `@ExceptionHandler` methods
- `ValidationException` → 400 with error message in `GeneralResponse.errorMessage`
- Generic `Exception` → 500 with optional stack trace (controlled by `show.http_500_error_details` property)
- All exceptions are persisted to `audit_log` table via `AuditLogService`

### Validation Pattern
- Imperative validation using static utility methods (`notNullOrElseThrow`, `notNullAndNotEmptyOrElseThrow`, etc.)
- No Bean Validation annotations (`@Valid`, `@NotNull`) — all validation is manual in service layer
- Validation happens before any business logic or persistence

### Retry Strategy
- `@Retryable(maxAttempts = 6, backoff = @Backoff(delay = 2_000, multiplier = 1.5, random = true))`
- Applied to Flipkart API caller methods
- `RetryableException` is the trigger exception class
- Exponential backoff with jitter to avoid thundering herd

## Async & Concurrency

- `AsyncJobService`: Fixed thread pool (20 threads) for background work
- `ParallelTaskExecutorService`: Batch execution with configurable batch size and inter-batch delay (rate limiting)
- Transaction-aware async: jobs can wait for current transaction to commit before executing
- `Context` (ThreadLocal): carries `transactionId`, `userId`, `serverId`, `clientId`, `startTimeInMs`, `auditLogOrder` across the call stack
- Context is propagated to async threads manually and cleaned in `finally` blocks

## Testing

### Framework
- JUnit 5 (`@ExtendWith(MockitoExtension.class)`)
- Mockito for mocking (`@Mock`, `@InjectMocks`, `MockedStatic`)
- AssertJ available (version 3.27.7 in properties, though JUnit assertions are used in practice)
- No integration tests or testcontainers — tests are pure unit tests with mocked dependencies

### Test Structure
- Mirror of main source tree: `src/test/java/com/tvsmotor/marketplace/{package}/{ClassNameTest}.java`
- Tests exist for most service classes, controllers, configs, and utilities
- `@BeforeEach` for context cleanup (`Context.clean()`)
- `timeout(1000)` used in async test verification

### Coverage
- JaCoCo configured with minimum 0% line coverage (effectively no enforcement)
- SonarQube excludes: entities, models, enums, repositories, projections (DTO/data classes)

## Security

- No Spring Security — authentication handled at Azure API Gateway (AD B2C)
- Service-to-service auth: Azure AD B2C client credentials flow (cached token with expiry buffer)
- Flipkart webhook auth: SHA-1 hash verification with timing-attack prevention (`sleepRandom()`)
- No CSRF, no session management — stateless REST API
- Secrets injected via Kubernetes Secrets (never in code or properties files)

## Observability

- `AuditLog` table: comprehensive audit trail for all operations, exceptions, and API interactions
- Each request gets a unique `transactionId` (format: `ThreadName_UUID_timestamp`)
- `auditLogOrder` field provides ordering within a single transaction
- `ServerMetricsService`: exposes thread pool stats and pod metadata
- Structured logging with correlation via `transactionId`

## Key Libraries & Their Roles

| Library | Usage |
|---------|-------|
| OkHttp | All outbound HTTP calls (Flipkart, MDP, ATP, Lead, Booking, Notification) |
| Guava | `ImmutableSet`, `Lists.partition()` for batch processing |
| Jackson + Joda/JSR-310 | JSON serialization with Java 8 time and Joda time support |
| Commons Codec | SHA-1 hashing for Flipkart webhook signature verification |
| SpringDoc OpenAPI | Auto-generated Swagger UI at `/marketplace/swagger-ui.html` |
| Hibernate Envers | Automatic entity change history (audit tables with `_AUD` suffix) |
| Spring Retry | Declarative retry with exponential backoff on Flipkart API calls |

