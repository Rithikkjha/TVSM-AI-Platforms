# master-data-platform


## Product Context


# Master Data Platform (MDP) — Product Context

## What This Service Does

MDP is the **single source of truth** for TVS Motor's dealer and product master data. It ingests data from multiple upstream systems (SAP, DMS, SharePoint), normalizes it, caches it in Redis, and exposes it via REST APIs to downstream consumers. It also publishes change events to Azure Service Bus topics so subscribers stay in sync.

## Domain Modules

| Module | Responsibility |
|--------|---------------|
| **dealer** (root-level) | Dealer lifecycle: onboarding, status management, flags, branches, contacts, locations, employees, test-ride vehicles |
| **product** | Vehicle model catalog — models, parts, part specifications |
| **product_mna** | Product MNA (Model Name Alias / Marketing Name) data — maps SAP model IDs to marketing-friendly names |
| **price** | Vehicle pricing by location — ex-showroom prices per model per state/city |
| **product_part** | Spare parts master — part catalog with market-level availability |
| **part_price** | Spare part pricing data |

## Core Domain Entities

### Dealer Domain
- **Dealer** — Central entity identified by `sapDealerCode`. Tracks DMS status, SAP status, MDP status, dealer type (AMD/SPD/BRANCH), and parent relationships.
- **DealerDetails** — Name, branch name, DMS branch sequence, K-number.
- **DealerLocation** — Address, lat/long, pincode, state. Types: MAIN, WORKSHOP, WAREHOUSE.
- **DealerContact** — Phone, email. Types: MAIN, SECONDARY.
- **DealerEmployee** — Staff attached to a dealer. Types: DEALER_PRINCIPAL, SERVICE_MANAGER, etc.
- **DealerFlag** / **DealerFlagNew** — Feature flags per dealer (SALES, SERVICE, DIGITAL_LEADS, IQUBE, RONIN, etc.).
- **DealerTestRideVehicle** — Test ride vehicle inventory per dealer.

### Product Domain
- **VehicleModel** — Identified by `sapModelId` + market. Attributes: brand, engine type, industry, category, availability status.
- **VehiclePart** — Parts linked to vehicle models.
- **VehiclePartSpecifications** — Technical specs for parts.
- **ProductMna** / **ProductMnaNew** — Marketing name aliases for SAP model IDs.

### Pricing Domain
- **PriceVehicleModel** — Vehicle price per location.
- **PriceLocationDetail** — Location-level pricing metadata.
- **PartPrice** — Spare part pricing.

### Supporting Entities
- **AuthClientUser** — API client registry for authentication.
- **IndianStates** / **IndianStateDetail** — Reference data for Indian geography.
- **AuditLog** — Internal audit trail for all operations.

## Dealer Hierarchy

```
APS (Area Parts Supervisor)
 └── AMD (Authorized Main Dealer) or SPD
      └── BRANCH (child branches, official or unofficial)
```

- Branches inherit certain properties from their parent AMD (2W/3W flags, MDP status, SAP first billing status).
- Unofficial branches get `SAP_STATUS = NOT_PRESENT_IN_SAP`.

## Dealer Status Model

A dealer has three independent statuses:
1. **DMS Status** — from the Dealer Management System: `ACTIVE`, `INACTIVE`, `PRE_ACTIVE`
2. **SAP Status** — from SAP: `ACTIVE`, `PERMANENTLY_BLOCKED`, `NOT_PRESENT_IN_SAP`
3. **MDP Status** — computed/derived: `ACTIVE`, `INACTIVE`, `PRE_ACTIVE`

MDP status is derived from the combination of DMS + SAP statuses and is synced to child branches when the parent AMD changes.

## External Integrations

| System | Direction | Mechanism |
|--------|-----------|-----------|
| **SAP** | Inbound | Batch data ingestion (via Azure Data Factory / Data Lake), service bus messages |
| **DMS (OnlineDMS)** | Inbound | Direct SQL Server read (read-only), service bus topic for dealer data |
| **SharePoint** | Inbound | Data migration/sync for dealer flags and details |
| **Azure Service Bus** | Both | Consumes dealer/DMS/product/price topics; publishes dealer change events |
| **Redis** | Internal | Read-through cache for dealer and product data |
| **Notification Service** | Outbound | Email notifications for failures and new dealer onboarding |
| **Azure B2C** | Inbound | Token validation for API authentication |
| **Lat/Long API** | Outbound | Geocoding dealer addresses (brand-specific credentials) |
| **APIM** | Outbound | Azure API Management gateway calls |

## Business Rules

1. **Cache-first reads** — Dealer data is served from Redis. On cache miss, data is loaded from MySQL and cached.
2. **Event-driven sync** — Any dealer mutation triggers: cache refresh → service bus publish.
3. **Flag inheritance** — 2W and 3W flags propagate from parent AMD to all child branches.
4. **MDP status inheritance** — Child branch MDP status is synced when parent AMD status changes.
5. **SAP first billing inheritance** — Propagates from AMD to branches.
6. **Validation-first** — All mutations validate input and throw `ValidationException` for bad data (returns 400).
7. **Audit logging** — All API calls, exceptions, and service bus messages are logged to the `audit_log` table.
8. **Retry on failure** — Redis and DMS database operations use `@Retryable` (3–5 attempts).
9. **DMS migration** — Periodic cron jobs import dealer data from the DMS SQL Server database.
10. **K-number mapping** — Dealers can be mapped to SAP K-numbers (unique constraint enforced).



## Code Structure


# Master Data Platform (MDP) — Project Structure

## Top-Level Layout

```
master-data-platform/
├── src/main/java/com/tvsmotor/mdp/   # Application source code
├── src/main/resources/                # Config, migrations, logging
├── src/test/                          # Unit and integration tests
├── script/                            # Operational scripts (bash, java, python, node, sql)
├── azure-pipelines/                   # CI/CD pipeline definitions
├── archive/                           # Deprecated/historical files
├── pom.xml                            # Maven build config
├── Dockerfile                         # Multi-stage Docker build
└── .env                               # Local environment variables (not committed)
```

## Source Code Structure (`src/main/java/com/tvsmotor/mdp/`)

### Root-Level Packages (Dealer Domain + Shared)

```
mdp/
├── MdpApplication.java              # Spring Boot entry point
├── aop/                             # Cross-cutting concerns (aspects)
│   ├── annotations/                 # Custom annotations: @Timed, @Authorization, @DisableOnProd
│   ├── AuthenticateAspect.java      # JWT authentication enforcement
│   ├── AuthorizationAspect.java     # Role-based access control
│   ├── DisableOnProdAspect.java     # Disables test/debug endpoints in production
│   └── TimedAspect.java            # Request timing instrumentation
├── config/                          # App-level Spring configuration
│   ├── CustomConfiguration.java     # General beans (server ID, etc.)
│   ├── DealerMasterServiceBusConfig.java  # Service Bus sender/processor clients for dealer topics
│   ├── DmsDatabaseConfig.java       # Secondary datasource (SQL Server, read-only)
│   ├── LatLongBrandCreds.java       # Geocoding API credentials per brand
│   ├── MdpOncePerRequestFilter.java # Request filter: context setup, auth, audit logging
│   ├── OkHttpClientConfig.java      # HTTP client for outbound calls
│   └── PostConstructThings.java     # Startup initialization
├── controller/                      # REST controllers (dealer domain)
│   ├── DealerController.java        # Core dealer CRUD + query APIs
│   ├── DealerFlagsController.java   # Flag management APIs
│   ├── DealerFlagsNewController.java
│   ├── DealerFlagsTypeNewController.java
│   ├── DealerKnowlarityDataController.java
│   ├── DealerStatusController.java  # Status update APIs
│   ├── DE_PipelineController.java   # Data Engineering pipeline triggers
│   ├── LatLongDetailsController.java # Geocoding operations
│   ├── TestController.java          # Debug/test endpoints (@DisableOnProd)
│   ├── TestServiceBusController.java
│   └── migration/                   # One-time migration endpoints
├── entity/                          # JPA entities (dealer domain)
│   ├── Dealer.java                  # Core dealer entity
│   ├── DealerDetails.java
│   ├── DealerContact.java
│   ├── DealerLocation.java
│   ├── DealerEmployee.java
│   ├── DealerFlag.java / DealerFlagNew.java / DealerFlagTypeNew.java
│   ├── DealerTestRideVehicle.java
│   ├── BaseEntityWithId.java        # Base class with auto-generated ID
│   ├── CommonBaseEntity.java        # Base with audit fields (createdAt, updatedAt)
│   ├── DealerDependentEntity.java   # Base for entities with dealerId FK
│   ├── AuthClientUser.java
│   └── batch_processing/            # Batch job tracking entities
├── enums/                           # Enumerations (dealer domain)
│   ├── DealerType.java              # AMD, SPD, BRANCH
│   ├── DmsStatus.java               # ACTIVE, INACTIVE, PRE_ACTIVE
│   ├── SapStatus.java               # ACTIVE, PERMANENTLY_BLOCKED, NOT_PRESENT_IN_SAP
│   ├── MdpDealerStatus.java         # ACTIVE, INACTIVE, PRE_ACTIVE
│   ├── DealerFlagType.java          # SALES, SERVICE, IQUBE, RONIN, etc.
│   ├── MdpClient.java, MdpDealerDataSource.java
│   ├── batch_processing/
│   └── service_bus/
├── model/                           # DTOs and response objects
│   ├── GeneralResponse.java         # Standard API response wrapper
│   ├── redis/                       # Redis cache data models (DealerData, etc.)
│   ├── request/                     # Request DTOs
│   ├── response/                    # Response DTOs
│   └── migration/
├── repository/                      # Spring Data JPA repositories (dealer domain)
├── service/                         # Business logic (dealer domain)
│   ├── DealerOperationsService.java # Main orchestrator for dealer mutations
│   ├── DealerCacheService.java      # Redis cache management
│   ├── DealerService.java           # CRUD operations
│   ├── DealerFlagService.java       # Flag CRUD
│   ├── Dealer*Service.java          # Per-entity services
│   ├── SapDealerDataService.java    # SAP data ingestion
│   ├── DmsDealerOperationalService.java # DMS data operations
│   ├── LatLongService.java          # Geocoding
│   ├── OkHttpService.java           # HTTP client wrapper
│   ├── AsyncJobService.java         # Async task execution
│   ├── ParallelJobExecutor.java     # Parallel processing utility
│   ├── service_bus/                 # Service Bus producers/consumers
│   │   ├── DealerDataSenderService.java    # Publishes dealer events
│   │   ├── DealerDataConsumerService.java  # Consumes own messages (audit)
│   │   ├── DealerDataGeneratorService.java # Constructs dealer data payloads
│   │   └── DmsDataConsumerService.java     # Consumes DMS topic messages
│   ├── migration/                   # Data migration services
│   │   ├── DmsDealerDataMigrator.java
│   │   ├── DmsBranchDataMigrator.java
│   │   ├── LatLongDealerDataMigrator.java
│   │   └── ...
│   ├── notification_service/        # Email notification integration
│   └── batch_processing/
└── utils/                           # Utility classes
    ├── FlagUtils.java
    ├── JWTUtil.java
    └── ValidationUtilityService.java
```

### Domain Modules (Self-Contained)

Each domain module follows the same internal structure:

```
{module}/
├── cache/          # Redis cache service for this domain
├── config/         # Service Bus config (sender/processor clients)
├── controller/     # REST endpoints
├── entity/         # JPA entities
│   └── batch_processing/   # Batch job entities
├── enums/          # Domain-specific enums
├── model/ or redis/ # DTOs, Redis data models
├── repository/     # Spring Data JPA repos
│   └── batch_processing/
├── service/        # Business logic
│   ├── service_bus/        # Service Bus consumer/sender
│   └── batch_processing/   # Batch data processors
└── utils/          # Domain-specific utilities
```

Modules: `product/`, `product_mna/`, `price/`, `product_part/`, `part_price/`

### Common Package (`common/`)

Shared infrastructure used across all domain modules:

```
common/
├── batch_processing/    # BatchProcessingService, BatchJobProcessorFactory
├── cache/               # CacheService (Redis abstraction)
├── config/              # RedisCacheConfig, ObjectMapperConfig
├── entity/              # AuditLog, IndianStates, IndianStateDetail
├── enums/               # AuditLogType, CacheName, PipelineSource
├── exceptions/          # ValidationException, NotFoundException, AccessDeniedException
│   └── handlers/        # RestExceptionHandler (@ControllerAdvice)
├── model/               # Shared DTOs (request, response, redis, service_bus)
├── repository/          # AuditLogRepo
├── service/             # AuditLogService, CronService, JsonHelperService, ServiceBusMessageConsumer
└── utils/               # Constants, Context (ThreadLocal), GeneralUtils
```

## Resources

```
src/main/resources/
├── application.properties          # Shared config (env-var placeholders)
├── application-local.properties    # Local dev overrides
├── application-dev.properties      # Dev environment
├── application-uat.properties      # UAT environment
├── application-prod.properties     # Production
├── logback-spring.xml              # Logging configuration
├── banner.txt                      # Startup banner
└── db/migration/                   # Flyway SQL migrations (v1.1 through v1.44)
```

## Test Structure

```
src/test/
├── java/com/tvsmotor/mdp/
│   ├── MdpBasicTests.java          # Basic Spring context tests
│   ├── MdpIntegrationTest.java     # Integration test base
│   ├── service/                    # Service layer unit tests
│   ├── controller/                 # Controller tests
│   ├── product/                    # Product module tests
│   ├── price/                      # Price module tests
│   ├── product_mna/                # Product MNA tests
│   ├── product_part/               # Part tests
│   ├── part_price/                 # Part price tests
│   └── ...
└── resources/
    ├── application.properties      # Test config (H2 in-memory DB)
    ├── db.migration/               # Test-specific migrations
    ├── files/                      # Test fixture files
    └── mockito-extensions/         # Mockito config (mock final classes)
```

## Module Dependencies

```
common ←── dealer (root-level packages)
common ←── product
common ←── product_mna
common ←── price
common ←── product_part
common ←── part_price
```

- All domain modules depend on `common/` for caching, exceptions, audit logging, and utilities.
- Domain modules are independent of each other (no cross-module imports).
- The root-level dealer packages (`controller/`, `service/`, `entity/`, etc.) are the original module; newer modules are properly namespaced.

## Architectural Decisions

1. **Modular monolith** — Single deployable Spring Boot app with domain-separated packages. Not microservices, but logically isolated.
2. **Cache-aside pattern** — Redis is populated on write and on cache miss. No TTL-based expiry; cache is explicitly refreshed.
3. **Event sourcing (light)** — All mutations publish to Azure Service Bus. Consumers (including MDP itself) can replay events.
4. **Flyway migrations** — Schema changes are versioned SQL scripts. No JPA auto-DDL in production.
5. **Hibernate Envers** — Entity auditing via `@Audited` annotation. Tracks all changes to dealer and product entities.
6. **Multi-datasource** — Primary: MySQL (JPA/Hikari). Secondary: SQL Server/DMS (raw JDBC, read-only).
7. **AOP for cross-cutting** — Authentication, authorization, timing, and prod-disabling handled via aspects.
8. **Factory pattern for batch jobs** — `BatchJobProcessorFactory` routes batch processing types to the correct processor implementation.



## Tech Stack & Dependencies


# Master Data Platform (MDP) — Tech Stack & Conventions

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 17 |
| Framework | Spring Boot | 3.5.12 |
| Build | Maven | 3.9.x |
| ORM | Spring Data JPA + Hibernate | 6.x |
| Auditing | Hibernate Envers | 6.6.13 |
| Database (primary) | MySQL | 8.x |
| Database (secondary) | SQL Server (DMS, read-only) | via mssql-jdbc 12.x |
| Cache | Redis (Jedis client) | 5.2.0 |
| Messaging | Azure Service Bus | 7.17.17 |
| HTTP Client | OkHttp | 4.12.0 |
| API Docs | SpringDoc OpenAPI (Swagger UI) | 2.8.9 |
| CSV Parsing | OpenCSV | 5.8 |
| Utilities | Guava, Commons BeanUtils, Lombok | |
| Retry | Spring Retry | 1.3.4 |
| Schema Migration | Flyway (via versioned SQL scripts) | |
| Containerization | Docker (multi-stage: Maven build → Amazon Corretto 17) | |
| CI/CD | Azure Pipelines (GitHub-hosted) | |
| Code Coverage | JaCoCo | 0.8.11 |
| Testing | JUnit 4 + Spring Boot Test + Mockito (inline) + H2 | |

## Coding Conventions

### Naming

- **Packages**: lowercase, underscore-separated for multi-word modules (`product_mna`, `part_price`)
- **Classes**: PascalCase. Services suffixed with `Service`, controllers with `Controller`, repositories with `Repository`
- **Operations services**: `{Domain}OperationsService` for orchestration logic (e.g., `DealerOperationsService`)
- **Entity tables**: plural snake_case (`dealers`, `vehicle_models`, `dealer_flags`)
- **Enum values**: UPPER_SNAKE_CASE
- **REST paths**: `/v1/{resource}` pattern, kebab-case for multi-word paths
- **Config beans**: named with `@Bean(name = "...")` for disambiguation

### Class Patterns

- **Lombok everywhere**: `@Data`, `@Builder`, `@RequiredArgsConstructor`, `@Slf4j` on nearly all classes
- **Constructor injection**: via `@RequiredArgsConstructor` (no `@Autowired` field injection)
- **Final fields**: all injected dependencies are `private final`
- **Builder pattern**: DTOs and response objects use `@Builder`

### Controller Conventions

```java
@Slf4j
@RequiredArgsConstructor
@RestController
@RequestMapping("/v1")
public class ExampleController {

    @Timed  // custom AOP annotation for timing
    @GetMapping("/resource/{id}")
    public ResponseEntity<GeneralResponse> getResource(@PathVariable final String id) {
        log.info("getResource() : id = {}", id);
        GeneralResponse response = GeneralResponse.builder()
                .data(service.doSomething(id))
                .build();
        return ResponseEntity.ok(response);
    }
}
```

- All endpoints return `ResponseEntity<GeneralResponse>`
- `GeneralResponse` wraps: `data`, `errorMessage`, `time`, `uuid`, `timeTakenInMs`, `serverId`
- Log method entry with parameters at INFO level
- Use `@Timed` annotation for performance tracking
- Use `@DisableOnProd` on test/debug endpoints

### Service Conventions

- **Validate first, then act**: Input validation at the top of methods using utility methods (`validateAndSanitize`, `notNullOrElseThrow`)
- **Transactional boundaries**: `@Transactional` on methods that perform multiple writes
- **Parallel streams**: Used for bulk operations (with `Collections.synchronizedList` for thread safety)
- **Copy-before-modify**: `GeneralUtils.generateCopy(entity)` before mutation to detect actual changes
- **Side effects after mutation**: Cache refresh → Service Bus publish (always in this order)

### Entity Conventions

```java
@Data
@Entity
@Audited           // Hibernate Envers auditing
@DynamicInsert     // Only include non-null columns in INSERT
@DynamicUpdate     // Only include changed columns in UPDATE
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "table_name")
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class MyEntity extends BaseEntityWithId { ... }
```

- All entities extend `BaseEntityWithId` or `CommonBaseEntity`
- Use `@Enumerated(EnumType.STRING)` for enum columns (never ordinal)
- Mark computed/non-persisted fields with `@Transient`

### Repository Conventions

- Extend `JpaRepository<Entity, Long>`
- Custom queries via method naming or `@Query`
- No native queries unless absolutely necessary

## Error Handling

### Exception Hierarchy

| Exception | HTTP Status | Use Case |
|-----------|-------------|----------|
| `ValidationException` | 400 | Invalid input, business rule violations, entity not found |
| `NotFoundException` | 400 | Entity lookup failures (treated same as validation) |
| `AccessDeniedException` | 401 | Authentication/authorization failures |
| `NoSuchElementException` | 400 | Caught alongside ValidationException |
| Generic `Exception` | 500 | Unexpected errors |

### Global Handler (`RestExceptionHandler`)

- `@ControllerAdvice` extending `ResponseEntityExceptionHandler`
- All responses wrapped in `GeneralResponse` with `errorMessage` field
- 500 errors optionally include stack trace (controlled by `show.http_500_error_details` property)
- All exceptions are logged and persisted to `audit_log` table
- HTTP 405, 400 (type mismatch, missing params, unreadable body) all handled explicitly

### Validation Pattern

```java
sapDealerCode = validateAndSanitize(sapDealerCode, "sapDealerCode");
notNullOrElseThrow(updatedDmsStatus, "updatedDmsStatus");
// throws ValidationException with formatted message
throw new ValidationException("sapDealerCode = %s NOT present in the DB", sapDealerCode);
```

## Caching Strategy

- **Redis** as the cache layer, accessed via Spring `CacheManager` + `StringRedisTemplate`
- **Cache names** defined in `CacheName` enum: `DEALER_DATA`, `DEALER_EMPLOYEE_DATA`, plus per-module caches
- **Serialization**: JSON strings stored in Redis (via `JsonHelperService`)
- **Batch reads**: `multiGet` with partitioned keys (batch size constant)
- **Retry**: All cache operations annotated with `@Retryable(maxAttempts = 3-5)`
- **No TTL**: Cache entries are explicitly refreshed on data mutation

## Service Bus Patterns

### Consumer Setup

- `ServiceBusProcessorClient` beans configured per topic in `*ServiceBusConfig` classes
- Session-based processing with `PEEK_LOCK` receive mode and manual `context.complete()`
- `maxConcurrentSessions` tuned per topic (1 for dealer, 250 for DMS)
- Error handling logs full context (namespace, entity path, error source, reason)

### Producer Pattern

- `ServiceBusSenderClient` beans for publishing
- Events include: `DEALER_CREATED`, `DEALER_UPDATED`, and domain-specific event types
- Messages published after successful DB write + cache refresh

## Authentication & Authorization

- **Request filter** (`MdpOncePerRequestFilter`): Extracts JWT from `Authorization` header, validates via Azure B2C, resolves client ID to user type
- **ThreadLocal context** (`Context`): Stores `userType`, `authToken`, `serverId`, `clientId`, `transactionId` per request
- **AOP aspects**: `@Authorization` annotation for role-based access; `@DisableOnProd` to block test endpoints in production
- **Client registry**: `AuthClientUser` table maps Azure B2C client IDs to user types

## Testing

### Framework

- **JUnit 4** (legacy) + Spring Boot Test
- **Mockito** with `mockito-inline` for mocking final classes (Azure Service Bus SDK)
- **H2** in-memory database for integration tests
- **Test migrations** in `src/test/resources/db.migration/`

### Coverage

- **JaCoCo** with package-level line coverage checks
- Excluded from coverage: enums, entities, repositories, specific config classes, and certain service bus consumers
- Minimum coverage threshold: 0% (effectively disabled, but reporting is active)

### Test Organization

- Mirror the main source structure under `src/test/java/com/tvsmotor/mdp/`
- Service tests focus on business logic with mocked dependencies
- Controller tests verify HTTP layer behavior

## Deployment

### Docker

- Multi-stage build: Maven 3.9 + Corretto 17 (build) → Corretto 17 (runtime)
- JVM tuning: `-XX:MaxRAMPercentage=75`
- Timezone: `Asia/Kolkata`
- Exposes port 8080
- Includes AKS cron job scripts in the image

### CI/CD (Azure Pipelines)

- **CI**: Triggered by Sonar PR validation pipeline completion on `main`
- **CD**: Separate pipelines for UAT and PROD
- Uses shared templates from `TVSM-DMS/Devops_ISSM_pipelines` repo
- Image scanning via separate AST pipeline

### Environments

- Profiles: `local`, `dev`, `uat`, `prod`
- All secrets via environment variables (never hardcoded)
- Context path: `/mdp`
- Swagger UI enabled in all environments (consider disabling in prod)

### Infrastructure

- Runs on **Azure Kubernetes Service (AKS)**
- Cron jobs triggered via bash scripts in AKS CronJob resources
- Connection pooling: HikariCP with min 20, max 50 connections
- Pod name exposed via `HOSTNAME` env var for tracing

## Logging

- **Logback** with Spring profile-aware configuration
- ANSI color coding enabled
- Log levels: INFO for application, ERROR for Azure SDK, WARN for Hibernate Envers
- Structured log pattern: `methodName() : key = value` format
- All API calls logged with timing via the request filter
- Audit log table for persistent operational logging

