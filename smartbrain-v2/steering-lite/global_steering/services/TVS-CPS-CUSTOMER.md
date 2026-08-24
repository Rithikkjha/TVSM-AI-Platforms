# TVS-CPS-CUSTOMER


## Product Context


# Product: TVS CPS Customer Service

## Overview

This is the **Customer Management microservice** for TVS Motor's Channel Partner System (CPS). It manages the full lifecycle of customer records in a dealer/vehicle sales context, specifically for the Norton motorcycle brand targeting the UK market.

The service is a backend data-owner for customer profiles. It does **not** perform vehicle enrichment (VIN lookups, warranty data) — that responsibility belongs to the BFF (Backend-for-Frontend) layer upstream.

## Domain Entities

### Customer
Core entity representing an individual customer.
- Fields: firstName, lastName, email, mobileNumber, alternateMobileNumber, dateOfBirth, gender, age, preferredLanguage, customerType, modeOfCommunication (JSON), additionalInfo
- Multi-tenant via `tenantId`
- Soft-deletable via `isActive` flag

### CustomerAddress
Multiple addresses per customer (HOME, OFFICE, etc.).
- Fields: addressType, addressLine1/2, city, state, postalCode (UK format), countryCode, isPrimary
- Linked to Customer via `customerId` (no JPA relationship annotation)
- UK postal code format enforced: `^[A-Z]{1,2}[0-9R][0-9A-Z]?\s?[0-9][A-Z]{2}$`

### CustomerVehicle
Vehicle-customer associations linking to an external Vehicle Master service.
- Fields: entityId (Vehicle Master FK), entityType, registrationNumber, cherishedNumber, saleInvoiceNumber, saleDate, deliveryDate, relationshipType, additionalInfo
- Relationship types: OWNER (default), SERVICE, USER

### CustomerDealerMapping
Links customers to channel partners (dealers).
- Fields: dealerId, vehicleRelationshipType (SALE, SERVICE)
- Created automatically during customer creation

### CustomerAudit
Full audit trail tracking field-level changes across all entities.
- Tracks CREATE, UPDATE, DELETE operations
- Stores old/new values per field for updates
- Records change source (API endpoint) and user

## API Endpoints

All endpoints use POST method with JSON request bodies.

### Internal APIs (`/api/v1/customer/`)
- `POST /search` — Search customers with AND/OR criteria, pagination, sorting
- `POST /create` — Create customer with addresses, vehicles, dealer mapping
- `POST /update` — Partial update of customer fields, addresses (add/update/delete), vehicles (add/update)
- `POST /add-vehicle` — Add vehicles to existing customer
- `POST /delete` — Soft delete customer and all related entities

### External APIs (`/api/v1/customer/external/`)
- `POST /create` — Create customer (requires `channelPartnerId` in request body, no JWT)
- `POST /update` — Update customer (no JWT, uses fixed user `external-system-user-request`)
- `POST /search` — Search customers (no JWT)

### Vehicle Search (`/api/v1/`)
- `POST /vehiclesearch` — Search customers by vehicle criteria (VIN, engine number, sale date)

## Business Rules

### Uniqueness
- Mobile number must be unique across all customers
- Email must be unique across all customers

### Soft Delete
- Never physically removes data; sets `isActive = false`
- Cascades to all related entities: addresses, vehicles, dealer mappings
- Cannot delete an already-inactive customer (throws CUSTOMER_ALREADY_DELETED)

### Ownership Validation
- Cannot update/delete an address that belongs to a different customer
- Cannot update a vehicle that belongs to a different customer

### Data Normalization
- Emails stored in lowercase
- Postal codes stored in uppercase
- Default customerType: "INDIVIDUAL"
- Default preferredLanguage: "en"
- Default vehicle entityType: "VEHICLE"
- Default vehicle relationshipType: "OWNER"

### Validation
- firstName/lastName: 1-30 chars, pattern `^[\p{L}][\p{L}'\-\s]*$`
- mobileNumber: mandatory, E.164 format `^\+[1-9]\d{1,14}$`, max 15 chars
- email: mandatory, valid format, max 100 chars
- age: 18-130 range
- address fields: addressLine1 (mandatory, max 50), city (mandatory, max 30), state (mandatory, max 50), postalCode (mandatory, UK format, max 10)
- vehicleData: entityId mandatory

### External API Rules
- `channelPartnerId` is required for external customer creation (throws CHANNEL_PARNER_ID_REQUIRED if missing)
- External requests use a fixed user identity: `external-system-user-request`
- External endpoints bypass JWT authentication

## Integrations

### Upstream (consumers of this service)
- **BFF Layer** — Calls this service for customer CRUD, enriches vehicle data with VIN/engine/warranty from Vehicle Master
- **External Systems** — Use `/external/` endpoints for cross-system customer management

### Shared Library: tvsm-be-core
Provides:
- Multi-tenant datasource routing (TenantContext ThreadLocal)
- JWT authentication and security filters
- Base controller with standardized APIResponse wrapper
- Custom exceptions (APIException, NotFoundException)
- Validation framework (@ConfigValidated + YAML rules)
- JsonUtil for serialization

### External References
- **Vehicle Master Service** — Referenced via `entityId` in CustomerVehicle; this service stores the association but does not call Vehicle Master directly



## Code Structure


# Structure: TVS CPS Customer Service

## Architecture

Layered architecture with a Facade pattern at the service layer. No JPA entity relationships — all associations use UUID foreign keys to avoid MultipleBagFetchException.

```
Controllers (3)
    ↓
CustomerService (Facade)
    ↓
Specialized Services (7)
    ↓
Repositories (5) ← JPA Specifications (dynamic queries)
    ↓
PostgreSQL (multi-tenant datasource routing via tvsm-be-core)

Audit: JPA EntityListeners → Spring ApplicationEvents → TransactionalEventListener (AFTER_COMMIT)
```

## Directory Layout

```
src/main/java/com/tvsm/customer/
├── CustomerServiceApplication.java        # Spring Boot entry point
├── audit/                                 # Event-driven audit subsystem
│   ├── AuditConstants.java                #   Entity types (CUSTOMER, CUSTOMER_ADDRESS, CUSTOMER_VEHICLE)
│   ├── AuditContext.java                  #   ThreadLocal storage for current endpoint
│   ├── AuditContextFilter.java            #   Servlet filter capturing request URI into AuditContext
│   ├── AuditEventHandler.java             #   @TransactionalEventListener — saves audit records AFTER_COMMIT
│   ├── CustomerAuditListener.java         #   JPA @EntityListener — publishes Spring events on persist/update
│   ├── CustomerAuditService.java          #   Query interface for audit records
│   ├── SpringContextHolder.java           #   Static access to ApplicationEventPublisher for JPA listeners
│   └── event/                             #   Event records (Java records)
│       ├── EntityCreatedEvent.java
│       ├── EntityDeletedEvent.java
│       └── EntityUpdatedEvent.java
├── config/
│   └── Config.java                        # RestTemplate bean with timeout configuration
├── constants/
│   ├── CustomerConstants.java             # Error codes, status values, API paths, field names
│   └── VehicleRelationshipType.java       # Enum: SALE, SERVICE
├── controller/
│   ├── CustomerController.java            # Internal CRUD + search APIs (/api/v1/customer/)
│   ├── ExternalCustomerController.java    # External APIs bypassing JWT (/api/v1/customer/external/)
│   └── VehicleSearchController.java       # Vehicle-based search (/api/v1/vehiclesearch)
├── dto/                                   # Request/response DTOs (19 classes)
│   ├── CustomerCreateRequest.java
│   ├── CustomerCreateResponse.java
│   ├── CustomerUpdateRequest.java         #   Contains nested AddressOperations, VehicleDataOperations
│   ├── CustomerUpdateResponse.java
│   ├── CustomerDeleteRequest.java
│   ├── CustomerDeleteResponse.java
│   ├── CustomerSearchRequest.java         #   AND/OR criteria, pagination, sort
│   ├── CustomerSearchResponse.java        #   Paginated results with metadata
│   ├── CustomerResponse.java              #   Full customer view with addresses + vehicles
│   ├── SearchCriteria.java                #   field + operator + values
│   ├── SortCriteria.java                  #   field + orderBy + priority
│   ├── AddressDto.java
│   ├── AddressOperationResult.java        #   Counts: updated, added, deleted
│   ├── AddVehicleRequest.java
│   ├── VehicleAddResponse.java
│   ├── VehicleDataDto.java                #   Includes enrichment fields (vin, engineNumber) set by BFF
│   ├── VehicleResponse.java
│   ├── VehicleSearchCriteria.java
│   └── CommunicationModeDto.java
├── entity/                                # JPA entities (no relationship annotations)
│   ├── Customer.java                      #   @EntityListeners(CustomerAuditListener.class)
│   ├── CustomerAddress.java               #   Linked via customerId UUID
│   ├── CustomerVehicle.java               #   Linked via customerId UUID, entityId → Vehicle Master
│   ├── CustomerDealerMapping.java         #   Linked via customerId UUID
│   └── CustomerAudit.java                 #   Audit trail storage
├── repository/                            # Spring Data JPA repositories
│   ├── CustomerRepository.java            #   Extends JpaSpecificationExecutor for dynamic queries
│   ├── CustomerAddressRepository.java
│   ├── CustomerVehicleRepository.java
│   ├── CustomerDealerMappingRepository.java
│   └── CustomerAuditRepository.java
├── service/                               # Business logic layer
│   ├── CustomerService.java               #   FACADE — delegates to specialized services
│   ├── CustomerCrudTransactionalService.java  # Extracts tenant context, delegates to CrudService
│   ├── CustomerCrudService.java           #   Core create/update logic with @Transactional
│   ├── CustomerSearchService.java         #   Search with JPA Specifications, pagination
│   ├── CustomerAddressService.java        #   Address CRUD with ownership validation
│   ├── CustomerVehicleService.java        #   Vehicle association management
│   ├── CustomerDeletionService.java       #   Soft delete orchestration (cascading)
│   └── ExternalCustomerService.java       #   External API variant (no JWT context)
├── specification/
│   └── CustomerSearchSpecification.java   # Dynamic JPA Specification builder (AND/OR, subqueries)
└── utils/
    ├── CustomerServiceUtils.java          # Entity↔DTO conversions, search response builder
    ├── CustomerResponseMapper.java        # Unified Customer→CustomerResponse mapping
    └── PaginationUtil.java                # Pageable creation, manual pagination, sort mapping

src/main/resources/
├── application.yml                        # Spring config, multi-tenant datasource, security paths
└── customer-validation.yml                # YAML-based validation rules (used by @ConfigValidated)

src/test/java/com/tvsm/customer/
├── CustomerServiceApplicationTest.java
├── audit/                                 # 6 test classes covering full audit subsystem
├── config/                                # ConfigTest
├── controller/                            # 3 controller tests
├── dto/                                   # DTO-specific tests
├── entity/                                # Entity lifecycle callback tests
├── repository/                            # 5 repository tests
├── service/                               # 8 service tests (one per service class)
├── specification/                         # Specification builder tests
├── util/
│   └── TestDataBuilder.java              # Shared test data factory
└── utils/                                 # 5 utility class tests
```

## Module Dependencies

```
CustomerController ──→ CustomerService (facade)
ExternalCustomerController ──→ CustomerService + ExternalCustomerService
VehicleSearchController ──→ CustomerService

CustomerService ──→ CustomerSearchService
                ──→ CustomerCrudTransactionalService
                ──→ CustomerDeletionService
                ──→ CustomerVehicleService

CustomerCrudTransactionalService ──→ CustomerCrudService (+ TenantContext)
ExternalCustomerService ──→ CustomerCrudTransactionalService

CustomerCrudService ──→ CustomerRepository
                    ──→ CustomerVehicleRepository
                    ──→ CustomerDealerMappingRepository
                    ──→ CustomerAddressService

CustomerSearchService ──→ CustomerRepository (with Specifications)
                      ──→ CustomerAddressRepository
                      ──→ CustomerVehicleRepository
                      ──→ CustomerDealerMappingRepository

CustomerDeletionService ──→ All 4 repositories (cascading soft delete)

CustomerAuditListener ──→ SpringContextHolder ──→ ApplicationEventPublisher
AuditEventHandler ──→ CustomerAuditRepository
```

## Key Architectural Decisions

### No JPA Relationships
Entities use UUID foreign keys (`customerId`) instead of `@OneToMany`/`@ManyToOne`. This avoids MultipleBagFetchException and N+1 query issues. Related data is fetched explicitly in service methods.

### Facade Pattern (CustomerService)
Controllers depend only on `CustomerService`, which delegates to specialized services. This maintains backward compatibility while allowing internal refactoring.

### Event-Driven Audit
JPA `@EntityListeners` cannot safely write to the database during lifecycle callbacks (causes ConcurrentModificationException). Instead:
1. `CustomerAuditListener` captures entity state changes and publishes Spring `ApplicationEvent`s
2. `AuditEventHandler` listens with `@TransactionalEventListener(phase = AFTER_COMMIT)` and saves audit records in a `REQUIRES_NEW` transaction

### Multi-Tenancy via Shared Library
Tenant resolution, datasource routing, and user context are handled by `tvsm-be-core`. Services access context via `TenantContext.getCurrentUser()`, `TenantContext.getTenantId()`, `TenantContext.getChannelPartnerId()`.

### All-POST API Design
Every endpoint uses POST, even for search and delete operations. This provides consistent request body handling and avoids URL length limits for complex search criteria.

### Validation via YAML Configuration
Field validation rules are defined in `customer-validation.yml` and applied via `@ConfigValidated` annotation from `tvsm-be-core`. This allows validation rules to change without code deployment.

### Internal vs External API Separation
- Internal APIs (`/api/v1/customer/`) require JWT; user/tenant context comes from the token
- External APIs (`/api/v1/customer/external/`) bypass JWT; `channelPartnerId` must be in the request body; a fixed system user identity is used



## Tech Stack & Dependencies


# Tech: TVS CPS Customer Service

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Java 21 |
| Framework | Spring Boot (parent: `tvsm-be-starter-parent:1.0.0`) |
| ORM | Spring Data JPA + Hibernate |
| Database | PostgreSQL (dialect: `org.hibernate.dialect.PostgreSQLDialect`) |
| Shared Library | `tvsm-be-core:1.0.0-SNAPSHOT` (multi-tenancy, auth, validation, exceptions) |
| API Docs | SpringDoc OpenAPI (Swagger UI at `/swagger-ui.html`) |
| Code Gen | Lombok (`@Data`, `@RequiredArgsConstructor`, `@Slf4j`, `@Builder`) |
| Mapping | MapStruct (declared in POM, manual mapping used in practice via utility classes) |
| JSON | Jackson with JavaTimeModule |
| Build | Maven with wrapper (`mvnw`) |
| Runtime | Amazon Corretto 21 (Docker) |
| CI/CD | Azure DevOps Pipelines |
| Container Registry | Azure ACR (`tvsmazcmnsvcacrdev01.azurecr.io`) |
| Deployment | Kubernetes via Helm charts (`norton-cps-customer`) |

## Coding Conventions

### Dependency Injection
- Always use constructor injection via `@RequiredArgsConstructor` + `private final` fields
- Never use `@Autowired` on fields

### Logging
- Every class annotated with `@Slf4j`
- Use structured log messages with `{}` placeholders
- DEBUG for internal flow, INFO for entry/exit points, WARN for recoverable issues, ERROR for failures
- Search service uses `[CUSTOMER-SEARCH]` log prefix for traceability

### Utility Classes
- Private constructor to prevent instantiation
- All methods are `static`
- Named with `Utils` or `Util` suffix

### DTOs
- Annotated with `@Data` (Lombok)
- Swagger annotations (`@Schema`) on every field
- Request DTOs use `@ConfigValidated` (YAML-based validation from core library)
- No business logic in DTOs

### Entities
- Annotated with `@Data`, `@EqualsAndHashCode`, `@ToString`
- UUID primary keys with `@GeneratedValue(strategy = GenerationType.UUID)`
- `@PreUpdate` callback sets `updatedAt = Instant.now()`
- `@EntityListeners(CustomerAuditListener.class)` on audited entities
- No JPA relationship annotations — use UUID foreign keys

### Naming
- Entity fields: camelCase Java, snake_case `@Column(name = "...")`
- Constants: UPPER_SNAKE_CASE in dedicated constants classes
- Services: `Customer<Domain>Service` (e.g., `CustomerAddressService`, `CustomerDeletionService`)
- Repositories: `<Entity>Repository`

### Null Safety
- Partial updates: only set fields that are non-null in the request
- Use `Optional.ofNullable(...).map(...)` for safe transformations
- Default values set at entity level (`isActive = true`, `preferredLanguage = "en"`)

## Patterns

### Facade Pattern
`CustomerService` is the single entry point for controllers. It delegates to specialized services without containing business logic itself.

### Specification Pattern
`CustomerSearchSpecification` builds dynamic JPA `Specification<Customer>` from AND/OR search criteria. Vehicle-related searches use subqueries against `CustomerVehicle`.

### Soft Delete
All delete operations set `isActive = false` via `@Modifying` `@Query` UPDATE statements. Never use `DELETE FROM` in production code.

### Event-Driven Audit
```
Entity change → @PostPersist/@PostUpdate (CustomerAuditListener)
    → publishes ApplicationEvent
    → @TransactionalEventListener(AFTER_COMMIT) in AuditEventHandler
    → saves CustomerAudit in REQUIRES_NEW transaction
```

### Multi-Tenancy
- `TenantContext` (ThreadLocal) provides `getCurrentUser()`, `getTenantId()`, `getChannelPartnerId()`
- Datasource routing handled by `tvsm-be-core`
- External APIs use fixed values instead of JWT-derived context

### Response Wrapper
All API responses use `APIResponse<T>` from `tvsm-be-core`:
```java
return success(data, APIResponse.Status.SUCCESS, "message", "SUCCESS_KEY");
```

## Error Handling

### Exception Types (from tvsm-be-core)
- `NotFoundException` — Entity not found (HTTP 404)
- `APIException` — Business rule violation (HTTP 400)
- Both accept: message, errorCode, params, apiError, paramDTO

### Error Codes (defined in CustomerConstants)
| Code | Meaning |
|------|---------|
| `CUSTOMER_NOT_FOUND` | Customer ID doesn't exist |
| `CUSTOMER_EXISTS` | Duplicate mobile or email |
| `CUSTOMER_ALREADY_DELETED` | Attempting to delete inactive customer |
| `ADDRESS_NOT_FOUND` | Address ID doesn't exist |
| `VEHICLE_NOT_FOUND` | Vehicle ID doesn't exist |
| `ADDRESS_OWNERSHIP_VIOLATION` | Address belongs to different customer |
| `VEHICLE_OWNERSHIP_VIOLATION` | Vehicle belongs to different customer |
| `DEALER_REQUIRED` | No dealer ID provided |
| `CHANNEL_PARNER_ID_REQUIRED` | External API missing channelPartnerId |

### Error Handling Strategy
- Exceptions bubble up from services; global exception handler in `tvsm-be-core` converts them to `APIResponse` with appropriate HTTP status
- Audit failures are caught and logged (never propagate to caller)
- Validation errors are handled by the `@ConfigValidated` framework before reaching service layer

## Testing

### Framework
- JUnit 5 (`@ExtendWith(MockitoExtension.class)`)
- Mockito for mocking dependencies
- H2 in-memory database for repository integration tests

### Coverage Requirements
- **85% line coverage minimum** (enforced by JaCoCo)
- **85% branch coverage minimum** (enforced by JaCoCo)
- Build fails if coverage drops below thresholds

### Test Structure
- Mirrors main source structure: one test class per production class
- `TestDataBuilder` utility in `src/test/java/com/tvsm/customer/util/` for consistent test data
- Controller tests mock the service layer
- Service tests mock repositories
- Repository tests use H2 with JPA auto-configuration

### Test Naming
Follow the pattern: `methodName_scenario_expectedResult` or descriptive method names.

### What to Test
- Happy path for all public methods
- Error/exception paths (not found, already exists, ownership violations)
- Edge cases (null inputs, empty lists, boundary values)
- Audit event publishing and handling
- Specification builder with various criteria combinations

## Build & Deployment

### Local Development
```bash
./mvnw spring-boot:run          # Run locally (needs PostgreSQL on localhost:5432)
./mvnw clean test               # Run tests with coverage
./mvnw clean package -DskipTests  # Build JAR without tests
```

### Docker Build
Multi-stage build:
1. **Builder stage**: Uses custom base image from Azure ACR (`tvs-cps-be-base-framework`), runs `mvnw clean package -DskipTests`
2. **Runtime stage**: `amazoncorretto:21-al2023-headless`, copies JAR, exposes port 8080

### CI/CD Pipeline (Azure DevOps)
1. **Sonar Pipeline** (`sonar_ci.yml`) — Code quality analysis
2. **CI Pipeline** (`ci-pipeline.yaml`) — Triggered after Sonar passes on `main`; builds Docker image
3. **AST Image Scan** (`ast-image-scan.yaml`) — Security scanning of container image
4. **CD Pipeline** (`cd-pipeline.yaml`) — Deploys to environments via Helm:
   - `dev` (auto-deploy)
   - `uat` (manual approval gate)
   - `prod` (manual approval gate + DAST scan)

### Configuration
- `application.yml` contains local dev defaults
- Production config injected via environment variables / Kubernetes ConfigMaps
- Flyway disabled (`flyway.enabled: false`) — migrations handled separately
- DDL validation mode (`ddl-auto: validate`) — schema must match entities

### Health & Monitoring
- Actuator endpoints exposed: `/actuator/health`, `/actuator/info`, `/actuator/metrics`
- Health details always shown (`show-details: always`)
- Log pattern includes traceId for distributed tracing: `%d %-5level [%X{traceId:-}] - %msg%n`

## Security

### Authentication
- JWT validation handled by `tvsm-be-core` security filters
- Excluded paths (no auth required):
  - `/actuator/**`
  - `/swagger-ui/**`, `/api-docs/**`
  - `/api/v1/customer/external/**`

### Input Sanitization
- Log pattern strips `<>|\n\r\t` characters to prevent log injection
- Validation rules enforce max lengths and patterns on all user inputs
- Parameterized JPA queries prevent SQL injection

### Sensitive Data
- Database credentials in `application.yml` are for local dev only
- Production credentials injected via environment/secrets management
- No secrets committed to repository (`.gitignore` covers standard patterns)

