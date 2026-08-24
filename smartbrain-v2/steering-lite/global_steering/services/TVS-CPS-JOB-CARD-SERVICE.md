# TVS-CPS-JOB-CARD-SERVICE


## Product Context


# Product Context — TVS CPS Job Card Service

## What This Service Does

This is the **Job Card Management Service** for TVS Motor's Connected Parts & Service (CPS) platform, specifically serving Norton Motorcycles dealerships. A "job card" represents a service or repair work order for a motorcycle at a dealership — tracking the full lifecycle from creation through completion and billing.

The service handles CRUD operations on job cards, manages associated parts/labor/complaints/files, performs warranty checks, provides analytics dashboards, supports bulk upload of job cards from Excel, and publishes domain events to downstream systems.

## Domain Entities

### Core Entities

| Entity | Purpose |
|--------|---------|
| **Jobcard** | Central work order: links customer, vehicle, dealer, job/service type, status, billing, and all associated mappings |
| **Billing** | Financial summary for a job card (estimated cost, total payable, tax, discount) |
| **BillingLineItem** | Individual line-item pricing (net price, tax, OEM/dealer split) attached to parts or labor |
| **JobcardPartMapping** | Parts consumed in a job card (catalog SKU, quantity, issue mode, billing) |
| **JobcardLaborMapping** | Labor charges (type, rate, effort, billing) |
| **JobcardComplaintMapping** | Customer complaints (code, group, remarks, recording URL) |
| **JobcardFileMapping** | Attached documents/photos (URL, name, size, type) |
| **BulkUpload** | Tracks bulk job card creation from uploaded Excel files |
| **BulkUploadError** | Per-row error details for failed bulk upload operations |

### Key Enums

| Enum | Values |
|------|--------|
| **JobcardStatus** | CREATED, WORK_IN_PROGRESS, COMPLETED, CANCELLED, CLOSED, ON_HOLD |
| **JobType** | PDI, MILEAGE_SERVICE, ANNUAL_SERVICE, ACCIDENT_REPAIR, OPEN_TIME |
| **ServiceType** | ROAD_SIDE_ASSIST, DEALERSHIP_COLLECT_AND_RETURN, WHILE_YOU_WAIT_SERVICE, REGULAR_SERVICE |
| **IssueModeType** | GOODWILL, WARRANTY, TSB, RECALL, SERVICE, REPAIR |
| **Channel** | CPS |
| **ModeType** | MANUAL, BULK_UPLOAD |

### Status Lifecycle

```
CREATED → WORK_IN_PROGRESS → COMPLETED → CLOSED
                ↓                              
            ON_HOLD                           
                ↓                              
           CANCELLED                          
```

- `COMPLETED` sets `completionDateTime`
- `CLOSED` sets `closeDateTime`

## Integrations

| System | Protocol | Purpose |
|--------|----------|---------|
| **Customer Service** | REST (POST) | Search customers by VIN to resolve `customerId` and `customerVehicleId` during bulk upload |
| **Azure Event Hub** | Kafka (SASL_SSL) | Publish `JOBCARD_CREATED` and `JOBCARD_UPDATED` events to topic `dev.cp.job_card` |
| **tvsm-be-core** | Library | Shared JWT security, multi-tenant datasource routing, TenantContext, BaseController, APIException, validation framework |

## Business Rules

### Billing & Warranty

- Parts with issue mode WARRANTY, RECALL, or TSB that are standard parts are **excluded from billing totals**
- When warranty parts exist on a job card, only **non-standard labor** costs are included in billing
- When all parts are non-warranty, all labor costs are included
- Billing amounts are always rounded to 2 decimal places
- Net price and tax are multiplied by quantity for parts

### Warranty Check Logic

1. Check vehicle warranty first (sale date + warranty period)
2. If vehicle warranty expired, check part warranty (last part sale date + part warranty period)
3. Warranty periods support YEARS, MONTHS, or DAYS units

### File Upload Validation

- File attachment is **mandatory** for standard parts with WARRANTY, RECALL, TSB, or GOODWILL issue mode
- Validation runs before any part operations are processed

### Access Control

- **Multi-tenant**: All queries scoped by `tenantId`
- **Dealer-scoped**: Non-OEM users see only their dealer's job cards (filtered by `channelPartnerId`)
- **Role-based**: Users with roles "Service Advisor", "Workshop Controller", "After Sales Advisor" see only job cards they created
- **Service history**: Cross-dealer access allowed when `isServiceHistory=true` (bypasses dealer filter)

### Job Card Number Generation

- Format: `NJC-{yyMMdd}-{sequence}` (e.g., `NJC-240601-42`)
- Sequence from PostgreSQL `job_card_sequence`

### Bulk Upload

- Excel files parsed and grouped by composite key (VIN + job type + service type + mileage + dates + cost)
- Each VIN group creates one job card with multiple complaints
- Processing is asynchronous (thread pool: 5 core, 10 max)
- Status tracking: PENDING → PROCESSING → COMPLETED / COMPLETED_WITH_ERRORS / FAILED
- Customer/vehicle data resolved via REST call to Customer Service



## Code Structure


# Project Structure — TVS CPS Job Card Service

## Directory Layout

```
TVS-CPS-JOB-CARD-SERVICE/
├── .kiro/steering/              # Kiro steering files (this documentation)
├── azure-pipelines/             # CI/CD pipeline definitions
│   └── templates/
│       ├── ci-pipeline.yaml     # Build pipeline (triggers Sonar → build)
│       ├── cd-pipeline.yaml     # Deploy to dev AKS (norton-cps-job-card helm chart)
│       ├── sonar.yaml           # SonarQube analysis
│       ├── ast-*.yaml           # Security scanning (image scan, UAT, prod)
│       ├── uk-cd-pipeline.yaml  # UK region deployment
│       └── pr-build-validation.yaml
├── src/
│   ├── main/
│   │   ├── java/com/tvsm/jobcard/
│   │   │   ├── Application.java          # Spring Boot entry point
│   │   │   ├── config/                   # Spring configuration beans
│   │   │   │   ├── AppConfig.java        # RestTemplate bean
│   │   │   │   ├── AsyncConfig.java      # Thread pool executors (bulk upload, analytics)
│   │   │   │   └── EventHubConfig.java   # Kafka producer factory (Azure Event Hub)
│   │   │   ├── constant/                 # Constants and endpoint paths
│   │   │   │   ├── ApiConstants.java     # API-level constants (event types, Kafka config keys)
│   │   │   │   ├── JobCardConstants.java # Domain constants (prefixes, field names, pool sizes)
│   │   │   │   ├── JobcardServiceEndpoints.java  # REST endpoint path constants
│   │   │   │   ├── StringConstants.java  # Response message strings
│   │   │   │   ├── AnalyticsKeyIndicator.java    # Enum of analytics KPIs
│   │   │   │   └── BulkUploadStatus.java # Bulk upload status enum
│   │   │   ├── controller/               # REST API layer
│   │   │   │   ├── JobcardController.java         # Main CRUD + bulk upload + download
│   │   │   │   ├── JobCardAnalyticsController.java # Analytics BFF endpoint
│   │   │   │   └── HealthController.java          # Health check
│   │   │   ├── dto/                      # Request/Response DTOs (~40 classes)
│   │   │   │   ├── JobcardCreateRequestDTO.java   # Create input (validated)
│   │   │   │   ├── JobcardUpdateRequestDTO.java   # Update input (nested operations)
│   │   │   │   ├── JobcardResponseDTO.java        # List response
│   │   │   │   ├── JobcardMappingsResponseDTO.java # Detail response (parts, labor, etc.)
│   │   │   │   ├── SearchRequestDTO.java          # Generic search/filter/sort/page
│   │   │   │   ├── PageResponseDTO.java           # Paginated response wrapper
│   │   │   │   └── ...                            # Billing, analytics, bulk upload DTOs
│   │   │   ├── entity/                   # JPA entities (PostgreSQL)
│   │   │   │   ├── BaseEntity.java       # Audit fields (createdAt, updatedAt, createdBy, active)
│   │   │   │   ├── Jobcard.java          # Core entity with all relationships
│   │   │   │   ├── Billing.java          # One-to-one with Jobcard
│   │   │   │   ├── BillingLineItem.java  # Many-to-one with Billing
│   │   │   │   ├── JobcardPartMapping.java
│   │   │   │   ├── JobcardLaborMapping.java
│   │   │   │   ├── JobcardComplaintMapping.java
│   │   │   │   ├── JobcardFileMapping.java
│   │   │   │   ├── BulkUpload.java       # Bulk upload tracking
│   │   │   │   └── BulkUploadError.java  # Bulk upload error records
│   │   │   ├── enums/                    # Domain enumerations
│   │   │   │   ├── JobcardStatus.java
│   │   │   │   ├── JobType.java
│   │   │   │   ├── ServiceType.java
│   │   │   │   ├── IssueModeType.java
│   │   │   │   ├── Channel.java
│   │   │   │   ├── ModeType.java
│   │   │   │   ├── CatalogType.java
│   │   │   │   ├── ClaimType.java
│   │   │   │   └── EntityType.java
│   │   │   ├── mapper/                   # MapStruct mappers
│   │   │   │   └── JobcardMapper.java    # Entity ↔ DTO conversions + row export logic
│   │   │   ├── repository/              # Spring Data JPA repositories
│   │   │   │   ├── JobcardRepository.java          # Main repo + custom interface
│   │   │   │   ├── JobcardRepositoryCustom.java    # Custom query interface (projections)
│   │   │   │   ├── JobcardRepositoryCustomImpl.java # Custom impl with CriteriaBuilder
│   │   │   │   ├── JobCardL1DashboardRepository.java # Analytics queries
│   │   │   │   ├── JobcardPartMappingRepository.java
│   │   │   │   ├── JobcardLaborMappingRepository.java
│   │   │   │   ├── JobcardComplaintMappingRepository.java
│   │   │   │   ├── JobcardFileMappingRepository.java
│   │   │   │   ├── BulkUploadRepository.java
│   │   │   │   └── BulkUploadErrorsRepository.java
│   │   │   ├── service/                  # Business logic layer
│   │   │   │   ├── JobcardService.java             # Core CRUD, dashboard, download
│   │   │   │   ├── PartOperationService.java       # Part add with billing calculation
│   │   │   │   ├── WarrantyCheckService.java       # Vehicle/part warranty validation
│   │   │   │   ├── JobCardProducerService.java     # Kafka event publishing
│   │   │   │   ├── JobcardBulkUploadService.java   # Async bulk upload processing
│   │   │   │   ├── JobcardExcelParserService.java  # Excel/CSV parsing
│   │   │   │   ├── JobCardAnalyticsService.java    # Analytics orchestration
│   │   │   │   └── JobCardMasterDataService.java   # Master data retrieval
│   │   │   ├── strategy/                 # Strategy pattern for analytics
│   │   │   │   ├── AnalyticsStrategy.java          # Interface (getIndicator, process)
│   │   │   │   ├── JobCardAnalyticsStrategyFactory.java # Factory (indicator → strategy)
│   │   │   │   ├── TotalJobCardIndicator.java
│   │   │   │   ├── NoShowAppointmentsIndicator.java
│   │   │   │   ├── NotClosedJobCardsIndicator.java
│   │   │   │   └── JobByJobType*.java              # Per-job-type indicators (5 classes)
│   │   │   └── utils/                    # Utility classes
│   │   │       ├── SearchSpecificationBuilder.java # Dynamic JPA Specification builder
│   │   │       ├── CommonUtils.java                # Tenant/user helpers, findJobCardOrThrow
│   │   │       ├── DateUtils.java                  # Date formatting and conversion
│   │   │       ├── ConversionUtils.java            # Rounding, UUID parsing
│   │   │       └── Searchable.java                 # Custom annotation for full-text fields
│   │   └── resources/
│   │       ├── application.yml           # Main config (DB, Kafka, cache, security)
│   │       └── jobcard-validation.yml    # Custom validation rules
│   └── test/java/com/tvsm/jobcard/      # Unit tests (mirrors main structure)
│       ├── config/
│       ├── constant/
│       ├── controller/
│       ├── entity/
│       ├── enums/
│       ├── mapper/
│       ├── repository/
│       ├── service/
│       ├── strategy/
│       └── utils/
├── Dockerfile                    # Multi-stage build (Maven → Corretto 21 Alpine)
├── pom.xml                       # Maven build config
└── README.md
```

## Module Dependencies (Data Flow)

```
Controller (REST API)
    │
    ▼
Service (Business Logic)
    │
    ├──► Repository (Data Access / JPA)
    │        │
    │        ▼
    │    PostgreSQL (jobcard schema)
    │
    ├──► Mapper (MapStruct: Entity ↔ DTO)
    │
    ├──► Strategy (Analytics computation)
    │        │
    │        ▼
    │    L1DashboardRepository (analytics queries)
    │
    ├──► ProducerService (Event publishing)
    │        │
    │        ▼
    │    Azure Event Hub (Kafka)
    │
    └──► RestTemplate (External service calls)
             │
             ▼
         Customer Service (VIN → customer lookup)
```

## Architectural Decisions

### Layered Architecture
Standard Spring Boot layers: Controller → Service → Repository. Controllers are thin (delegate to services, wrap in `APIResponse`). Services contain all business logic.

### Strategy Pattern for Analytics
Each analytics KPI (total job cards, no-show appointments, pending closures, per-job-type counts) is a separate `AnalyticsStrategy` implementation. The factory auto-discovers strategies via Spring DI. Each strategy runs asynchronously with a 10-second timeout.

### Specification Pattern for Dynamic Queries
`SearchSpecificationBuilder` converts `SearchRequestDTO` (with AND/OR filters, operators, sort, search text) into JPA `Specification<T>`. Supports operators: eq, ne, lt, lte, gt, gte, in, between. Fields annotated with `@Searchable` are included in full-text search.

### Event-Driven Communication
Job card create/update events are published to Azure Event Hub (Kafka protocol). Events include full job card state plus operation details. Fire-and-forget with async completion logging.

### Multi-Tenancy
Tenant isolation via `TenantContext` (from tvsm-be-core). Every query includes `tenantId` filter. Datasource routing handled by the core library.

### Async Bulk Processing
Bulk uploads are processed asynchronously using a dedicated thread pool (`jobcardBulkExecutor`). Tenant context is captured before async execution and restored in the worker thread.

### Custom Repository for Projections
`JobcardRepositoryCustomImpl` uses CriteriaBuilder to fetch `JobcardProjection` (interface-based projection) for optimized list queries that avoid loading full entity graphs.

### Soft Deletes
All entities extend `BaseEntity` with an `active` boolean. Records are never physically deleted — they are marked `active=false`. Queries filter by active status where appropriate.

### JSONB for Flexible Data
Both `Jobcard` and `JobcardPartMapping` use PostgreSQL JSONB columns (`additional_info`) for semi-structured data like customer vehicle details, assigned-to names, and part metadata.



## Tech Stack & Dependencies


# Tech Stack & Conventions — TVS CPS Job Card Service

## Tech Stack

| Layer | Technology | Version/Notes |
|-------|-----------|---------------|
| Language | Java | 21 (Amazon Corretto) |
| Framework | Spring Boot | 3.x (via `tvsm-be-starter-parent` 1.0.0) |
| Build | Maven | Multi-module with parent POM |
| Database | PostgreSQL | Azure-hosted, schema `jobcard`, SSL required |
| ORM | Spring Data JPA + Hibernate | `ddl-auto: none` (schema managed externally) |
| Messaging | Spring Kafka | Azure Event Hub (Kafka protocol, SASL_SSL) |
| Mapping | MapStruct | 1.x with Lombok binding |
| Boilerplate | Lombok | `@Data`, `@Builder`, `@RequiredArgsConstructor` |
| Validation | Jakarta Bean Validation | + custom YAML-based validation (tvsm-core) |
| API Docs | Springdoc OpenAPI | Swagger UI at `/swagger-ui.html` |
| Caching | Caffeine | 500 max entries, 5-min TTL |
| File Parsing | Apache POI + Commons CSV | Excel (`.xlsx`) and CSV bulk upload |
| Testing | JUnit 5 + Mockito + AssertJ | Unit tests only (no integration test infra) |
| Coverage | JaCoCo | Report generated during `test` phase |
| Container | Docker | Multi-stage: Maven build → Corretto 21 Alpine |
| CI/CD | Azure Pipelines | Sonar → Build → Deploy to AKS via Helm |
| Security | JWT (RS256) | Via tvsm-be-core library |
| Shared Library | `tvsm-be-core` 1.0.0-SNAPSHOT | Multi-tenancy, security, BaseController, APIException |

## Coding Conventions

### Naming

- **Packages**: lowercase, singular (`controller`, `service`, `entity`, `dto`, `enums`, `mapper`, `repository`, `strategy`, `utils`, `config`, `constant`)
- **Classes**: PascalCase. Entities use `Jobcard` prefix (e.g., `JobcardPartMapping`). DTOs suffixed with `DTO`. Services suffixed with `Service`.
- **Constants**: `UPPER_SNAKE_CASE` in dedicated constant classes
- **Endpoints**: kebab-case paths (e.g., `/bulk-upload`, `/warranty-check`)
- **Database columns**: `snake_case` (e.g., `job_card_id`, `channel_partner_id`)

### Class Structure

- **Entities**: Extend `BaseEntity`, use `@Builder`, `@Getter/@Setter`, `@NoArgsConstructor/@AllArgsConstructor`. UUID primary keys with `GenerationType.AUTO`.
- **DTOs**: Use `@Data`, `@Builder`, `@NoArgsConstructor/@AllArgsConstructor`. Validation annotations on fields. Swagger `@Schema` annotations for documentation.
- **Services**: `@Service`, `@RequiredArgsConstructor`, `@Slf4j`. Constructor injection via Lombok.
- **Controllers**: `@RestController`, extend `BaseController` (from core). Use `success()` helper for responses.
- **Repositories**: Extend `JpaRepository<Entity, UUID>` + `JpaSpecificationExecutor<Entity>`. Custom queries via `@Query` (JPQL or native).

### Response Format

All API responses wrapped in `APIResponse<T>`:
```java
{
  "status": "SUCCESS",
  "statusCode": "OK",
  "message": "descriptive message",
  "data": { ... }
}
```

Paginated responses use `PageResponseDTO<T>`:
```java
{
  "content": [...],
  "total": 100,
  "page": 1,
  "size": 10
}
```

### Dependency Injection

- Constructor injection exclusively (via `@RequiredArgsConstructor`)
- No field injection (`@Autowired` on fields)
- `@Value` for configuration properties on constructor parameters or fields

### Logging

- SLF4J via Lombok `@Slf4j`
- Log level: DEBUG for `com.tvsm.jobcard`, INFO for Spring Web
- Log entry/exit of key operations with relevant IDs
- Sensitive data (tokens, passwords) never logged

## Patterns

### Search & Filtering

Generic `SearchRequestDTO` supports:
- `and`: List of filters combined with AND
- `or`: List of filters combined with OR
- `searchText`: Full-text search across `@Searchable` fields
- `sort`: List of `{field, orderBy, priority}` objects
- `page` / `size`: Pagination (1-indexed pages)

Filter operators: `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `between`

### Audit Trail

`BaseEntity` provides automatic audit via JPA lifecycle callbacks:
- `@PrePersist`: Sets `createdAt` and `updatedAt`
- `@PreUpdate`: Updates `updatedAt`
- `createdBy` / `updatedBy`: Set manually from `TenantContext.getCurrentUser()`

### Soft Delete

- `active` field (default `true`) on all entities
- Deactivation sets `active = false` (never physical delete)
- List queries filter active records where appropriate

### Event Publishing

Events follow a standard envelope:
```java
{
  "eventId": "uuid",
  "eventType": "JOBCARD_CREATED" | "JOBCARD_UPDATED",
  "source": "JOBCARD_SERVICE",
  "topic": "dev.cp.job_card",
  "timestamp": "ISO-8601",
  "payload": { ... }
}
```

Kafka producer configured with idempotence enabled and `acks=all` for delivery guarantees.

### Multi-Tenancy

- `TenantContext` (ThreadLocal) holds: tenantId, userId, dealerId, userName, channelPartnerId, userType, token
- Every repository query includes `.and(tenantSpec(tenantId))`
- For async operations: capture context before, restore in worker thread, clear in finally block

## Error Handling

### Exception Strategy

- `APIException` (from tvsm-be-core) with status code enum: `BAD_REQUEST`, `FORBIDDEN`, `NOTFOUND`, `INTERNAL_SERVER_ERROR`
- Thrown from service layer, handled by global exception handler (in core library)
- Validation errors return 400 with field-level messages (from `@NotBlank`, `@Min`, etc.)

### Common Error Patterns

```java
// Not found
throw new APIException("Jobcard not found", APIResponse.StatusCode.NOTFOUND.name());

// Access denied
throw new APIException("Access denied for this jobcard", APIResponse.StatusCode.FORBIDDEN.name());

// Invalid input
throw new APIException("Invalid query parameters: " + e.getMessage(), APIResponse.StatusCode.BAD_REQUEST.name());
```

### Bulk Upload Error Handling

- Per-row error tracking with `BulkUploadError` entity
- Error types: `VALIDATION_ERROR`, `CREATION_ERROR`, `CUSTOMER_VEHICLE_ERROR`
- Failed VIN groups: all rows (including successful ones) saved to error table with context
- Overall status: `COMPLETED_WITH_ERRORS` if any failures, `FAILED` if unrecoverable exception

### Kafka Error Handling

- Fire-and-forget with completion callback logging
- Exceptions caught and logged (not retried): `"Event send failed and will not be retried"`
- No dead-letter queue configured

## Testing

### Framework

- **JUnit 5** for test lifecycle
- **Mockito** for mocking dependencies
- **AssertJ** for fluent assertions
- **Spring Boot Test** for context loading (where needed)

### Test Structure

Tests mirror the main source tree:
```
src/test/java/com/tvsm/jobcard/
├── config/       # Config bean tests
├── constant/     # Constant value tests
├── controller/   # Controller unit tests (MockMvc)
├── entity/       # Entity construction/equality tests
├── enums/        # Enum value tests
├── mapper/       # MapStruct mapping tests
├── repository/   # Repository query tests
├── service/      # Service logic tests (mocked repos)
├── strategy/     # Analytics strategy tests
└── utils/        # Utility method tests
```

### Conventions

- Test class named `{ClassUnderTest}Test`
- Use `@ExtendWith(MockitoExtension.class)` for unit tests
- Mock all dependencies with `@Mock`, inject with `@InjectMocks`
- No integration tests with real database (no Testcontainers, no H2)
- JaCoCo for coverage reporting

## Deployment

### Docker

Multi-stage Dockerfile:
1. **Build stage**: Uses `tvs-cps-be-base-framework` image (includes Maven + JDK), runs `mvn clean install -DskipTests`
2. **Runtime stage**: Amazon Corretto 21 Alpine, non-root user (`norton`), exposes port 8080

### CI/CD Pipeline (Azure DevOps)

1. **PR Validation**: Build + Sonar analysis on pull requests
2. **CI Pipeline**: Triggered after Sonar passes on `main` branch. Builds Docker image.
3. **CD Pipeline**: Triggered by successful CI build. Deploys to AKS using Helm chart `norton-cps-job-card`.
4. **Environments**: dev → UAT (manual approval) → prod (manual approval)
5. **Security**: AST image scanning before UAT and prod deployments

### Infrastructure

- **AKS** (Azure Kubernetes Service): Namespace `dev-cp`
- **Azure Container Registry**: `tvsmazcmnsvcacrdev01.azurecr.io`
- **PostgreSQL**: Azure Database for PostgreSQL (SSL required)
- **Azure Event Hub**: Kafka-compatible messaging
- **Helm**: Chart name `norton-cps-job-card`

### Configuration

- Environment-specific config via Spring profiles (not visible in repo — likely injected via Helm values)
- Secrets via environment variables: `DB_USERNAME`, `DB_PASSWORD`, `KAFKA_SSL_JC_PWD`
- Server port: 8080, context path: `/`
- Actuator endpoints exposed: health, info, metrics

## Build Commands

```bash
# Build (skip tests)
mvn clean install -DskipTests

# Build with tests
mvn clean install

# Run locally
mvn spring-boot:run

# Run tests only
mvn test

# Generate coverage report
mvn test jacoco:report
```

