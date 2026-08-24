# TVS-CPS-BE-BASE-FRAMEWORK


## Product Context


# Product Context — TVSM Backend Base Framework

## What This Is

This is NOT a standalone application. It is an **enterprise base framework** (shared library + Maven archetype) that bootstraps all TVSM (TVS Motor) backend microservices for the Connected Parts & Services (CPS) / Dealer Management System (DMS) platform.

Downstream services (order-service, appointment-service, claim-service, etc.) depend on `tvsm-be-core` as a library and are scaffolded using `tvsm-be-archetype`.

## Domain Context

TVS Motor's dealer and channel partner ecosystem. The platform manages:

- Orders, Bookings, Enquiries
- Vehicle Stock and Vehicle Invoices
- Part Purchases and Part Invoices
- Warranty Registrations
- Dealer/Channel Partner operations

### Key Domain Concepts

| Concept | Description |
|---------|-------------|
| Tenant | A logical isolation boundary — typically a dealer group or business unit. Each tenant may have its own database. |
| Channel Partner | A dealer or distributor. Identified by `channelPartnerId` and `channelPartnerType` (e.g., DEALER). |
| User Types | OEM (TVS corporate) vs Dealer users. Determines data visibility and permissions. |
| Roles & Permissions | JSON-configured RBAC. Roles contain permission groups; permission groups contain permissions; API endpoints map to required permissions. |

## Integrations

| System | Mechanism | Purpose |
|--------|-----------|---------|
| PostgreSQL | Spring Data JPA + HikariCP | Primary data store (per-tenant routing) |
| Azure Blob Storage | Azure SDK (spring-cloud-azure) | File upload/download/streaming |
| Azure AD (OAuth) | Client credentials flow via `OAuthGenerationTokenUtil` | Service-to-service auth tokens |
| Downstream microservices | RestTemplate / WebClient with trace propagation | Inter-service communication |
| WireMock | Standalone mock server module | API mocking for development/testing |

## Business Rules Encoded in the Framework

1. **Tenant isolation is mandatory** — Every request must resolve a `tenantId` (from JWT claim or X-Tenant-ID header). Unknown tenants fall back to the default datasource.
2. **JWT authentication on all non-excluded paths** — Bearer token required. Token must contain `sub`, `tenantId`, and role claims.
3. **RBAC enforcement** — API endpoints are mapped to permissions via JSON config. Access is denied if the user's roles don't grant the required permission.
4. **Request sanitization** — All incoming requests (URL params, headers, body) are scanned for SQL injection, XSS, template injection, path traversal, and null bytes.
5. **Soft delete by default** — `BaseEntity` includes an `active` flag; entities are never hard-deleted.
6. **Audit trail** — `createdAt`, `updatedAt`, `createdBy`, `updatedBy` are auto-populated on all entities.
7. **Validation is config-driven** — Validation rules live in YAML files, keyed by POJO class name and tenant. The `@ConfigValidated` annotation triggers validation automatically on controller parameters.
8. **Unmapped API behavior is configurable** — RBAC can be set to ALLOW or DENY requests to endpoints without explicit permission mappings.

## API Response Contract

All APIs return a standardized envelope:

```json
{
  "status": "SUCCESS | ERROR",
  "statusCode": "OK | BAD_REQUEST | UNAUTHORIZED | FORBIDDEN | NOTFOUND | INTERNAL_ERROR",
  "message": "Human-readable message",
  "messageKey": "I18N_KEY",
  "data": { ... },
  "errors": [{ "field": "...", "errorCode": "...", "messageKey": "..." }],
  "errorCode": "...",
  "params": { ... }
}
```

## Configuration Properties (prefix: `tvsm.core`)

| Property Path | Purpose |
|---------------|---------|
| `tvsm.core.security.excludedPaths` | Paths bypassing JWT validation |
| `tvsm.core.security.jwt.publicKey.*` | RSA public keys for JWT verification |
| `tvsm.core.security.defaultTenant` | Fallback tenant when JWT lacks claim |
| `tvsm.core.multitenant.datasource.*` | Per-tenant database connection config |
| `tvsm.core.cloud-storage.enabled/provider` | Cloud storage toggle and provider selection |
| `tvsm.core.logging.methodLevel.enabled` | AOP method-level logging |
| `tvsm.core.logging.performance.thresholdMs` | Slow-method alerting threshold |
| `rbac.enabled` | RBAC enforcement toggle |
| `rbac.config.*.path` | Paths to RBAC JSON config files |



## Code Structure


# Project Structure — TVSM Backend Base Framework

## Repository Layout

```
TVS-CPS-BE-BASE-FRAMEWORK/
├── pom.xml                          # Parent POM (tvsm-be-starter-parent) — dependency management, plugin config
├── Dockerfile                       # Multi-stage build: builds framework, publishes to .m2 for downstream use
├── ci-pipeline.yaml                 # Azure DevOps CI — triggers shared build template from Devops_ISSM_pipelines repo
├── README.md                        # Usage guide, archetype generation commands, WireMock docs
│
├── tvsm-be-core/                    # ★ Core framework library JAR — consumed by all downstream services
│   ├── pom.xml                      # Dependencies: Spring Boot starters, Azure SDK, Commons, Lombok, test libs
│   └── src/main/java/com/tvsm/core/
│       ├── aspect/                  # AOP cross-cutting concerns
│       │   ├── Loggable.java        #   @Loggable annotation for method-level logging
│       │   ├── LoggingAspect.java   #   Logs method entry/exit with args and return values
│       │   └── PerformanceAspect.java #  Logs slow methods exceeding configurable threshold
│       ├── async/                   # Thread pool utilities
│       │   └── TenantAwareMDCTaskDecorator.java  # Propagates TenantContext + MDC to async threads
│       ├── autoconfigure/           # Spring Boot auto-configuration classes
│       │   ├── TvsCoreAutoConfiguration.java      # Core beans: GlobalExceptionHandler, RestTemplate interceptor, MDC executor
│       │   ├── MultiTenantAutoConfiguration.java  # HikariCP datasources per tenant, routing datasource
│       │   ├── CloudStorageAutoConfiguration.java # Azure Blob client + provider (conditional on property)
│       │   └── ValidationAutoConfiguration.java   # Validation engine + config loader beans
│       ├── bean/                    # Shared DTOs and response models
│       │   ├── APIResponse.java     #   Standard response envelope (Status, StatusCode, data, errors, messageKey)
│       │   ├── SearchRequestDTO.java #  Generic search/filter/sort request (AND/OR filters, pagination)
│       │   ├── PageResponseDTO.java #   Paginated response wrapper
│       │   ├── Error.java           #   Error detail (field, errorCode, messageKey)
│       │   ├── ParamDTO.java        #   Dynamic parameters for error messages
│       │   └── APIMTokenRequestDTO.java # OAuth token request model
│       ├── cloudstorage/            # Cloud storage abstraction layer
│       │   ├── config/              #   CloudStorageProperties (@ConfigurationProperties)
│       │   ├── model/               #   StorageFile, UploadRequest DTOs
│       │   ├── provider/            #   CloudStorageProvider interface + AzureStorageProvider impl
│       │   └── service/             #   CloudStorageService interface + CloudStorageServiceImpl
│       ├── constants/               # Shared constants
│       │   └── BaseConstants.java   #   USER_TYPE_OEM, common string constants
│       ├── controller/              # Base controller
│       │   └── BaseController.java  #   success()/error()/badRequest()/forbidden() response helpers
│       ├── exception/               # Exception hierarchy and global handler
│       │   ├── APIException.java    #   General API error (maps to 500)
│       │   ├── NotFoundException.java #  Resource not found (maps to 404)
│       │   ├── ValidationException.java # Validation failure (maps to 400)
│       │   ├── GlobalExceptionHandler.java # @RestControllerAdvice — catches all exceptions
│       │   └── SanitizedException.java    # Strips dangerous chars from exception messages for logging
│       ├── http/                    # HTTP client interceptors
│       │   ├── RestTemplateInterceptor.java # Propagates traceId, tenantId, token to outgoing RestTemplate calls
│       │   └── WebClientInterceptor.java    # Same for reactive WebClient calls
│       ├── model/                   # Base entity classes
│       │   ├── BaseEntity.java      #   Audit fields (createdAt/By, updatedAt/By), soft delete (active), @PrePersist/@PreUpdate
│       │   └── reports/             #   Report-specific models (Booking, Order, Enquiry, VehicleStock, etc.)
│       ├── repository/              # Base repository
│       │   └── BaseRepository.java  #   Abstract repository with common query methods
│       ├── security/                # Security filter chain
│       │   ├── AuthenticationFilter.java     # Order=1: JWT validation, tenant extraction, RBAC check
│       │   ├── RequestValidationFilter.java  # Order=2: Input sanitization (XSS, SQLi, path traversal)
│       │   ├── MaliciousContentDetector.java # Pattern-based threat detection engine
│       │   ├── CachedBodyHttpServletRequest.java # Allows re-reading request body for validation
│       │   ├── SecurityProperties.java       # @ConfigurationProperties for security config
│       │   ├── ValidationResult.java         # Result object for request validation
│       │   ├── jwt/                 # JWT utilities
│       │   │   ├── JWTUtil.java     #   Token parsing, claim extraction
│       │   │   ├── KeyManager.java  #   RSA public key management
│       │   │   ├── Base64Util.java  #   Base64 encoding/decoding
│       │   │   └── CryptoUtil.java  #   Cryptographic operations
│       │   └── rbac/                # Role-Based Access Control
│       │       ├── RBACService.java #   Loads JSON configs, caches role→permission mappings, checks access
│       │       ├── RBACProperties.java #  RBAC configuration properties
│       │       ├── Role.java / Permission.java / PermissionGroup.java  # Domain models
│       │       └── *Config.java     #   JSON deserialization models for RBAC config files
│       ├── service/                 # Base service
│       │   └── BaseService.java     #   Abstract service with common patterns
│       ├── tenant/                  # Multi-tenancy infrastructure
│       │   ├── TenantContext.java   #   ThreadLocal holder for tenantId, user, token, roles, channelPartner
│       │   ├── MultiTenantRoutingDataSource.java # AbstractRoutingDataSource — routes by TenantContext
│       │   └── MultiTenantProperties.java        # @ConfigurationProperties for datasource config
│       ├── util/                    # Utility classes
│       │   ├── JsonUtil.java        #   Jackson ObjectMapper wrapper (Optional-based API)
│       │   ├── DateTimeUtil.java    #   Date/time formatting and parsing
│       │   ├── StringUtil.java      #   String manipulation helpers
│       │   ├── MapUtil.java         #   Map transformation utilities
│       │   ├── MDCUtil.java         #   MDC (Mapped Diagnostic Context) management
│       │   ├── OAuthGenerationTokenUtil.java # Azure AD client credentials token generation
│       │   ├── SearchSpecificationBuilder.java # Dynamic JPA Specification builder from SearchRequestDTO
│       │   └── Searchable.java      #   @Searchable annotation for full-text search field discovery
│       └── validations/             # Config-driven validation engine
│           ├── CustomValidationEngine.java   # Core engine — loads rules, orchestrates validation
│           ├── ValidationRulesConfig.java    # YAML config model (per-class, per-tenant rules)
│           ├── ValidationConfigLoader.java   # Loads validation YAML files
│           ├── NestedValidationUtils.java    # Path conversion utilities for nested field validation
│           ├── aspect/              # AOP integration
│           │   ├── ConfigValidated.java      # @ConfigValidated annotation for controller params
│           │   └── ConfigValidationAspect.java # Intercepts controller methods, triggers validation
│           ├── strategy/            # Strategy pattern for field type handling
│           │   ├── ValidationTypeOrchestrator.java # Routes to correct strategy by field type
│           │   └── impl/            # SimpleField, NestedField, CollectionField, MapField, TupleField strategies
│           └── validators/          # Custom validator implementations
│               └── CustomGenericValidator.java # mandatory, minLength, maxLength, pattern, email, numericRange, futureDate
│
├── tvsm-be-archetype/              # ★ Maven archetype for scaffolding new microservices
│   ├── pom.xml                     # Archetype packaging config
│   └── src/main/resources/
│       ├── META-INF/maven/archetype-metadata.xml  # Archetype descriptor (required properties, file sets)
│       └── archetype-resources/    # Template project
│           ├── pom.xml             #   Generated service POM (depends on tvsm-be-core)
│           ├── .gitignore          #   Standard Java gitignore
│           ├── README.md           #   Generated project readme
│           └── src/main/
│               ├── java/__packageInPathFormat__/
│               │   ├── Application.java       # Spring Boot main class
│               │   ├── controller/            # Sample OrderController extending BaseController
│               │   ├── dto/                   # OrderRequestDto, OrderResponseDto
│               │   ├── entity/                # Order entity extending BaseEntity
│               │   ├── mapper/                # OrderMapper (MapStruct)
│               │   ├── repository/            # OrderRepository (Spring Data JPA)
│               │   └── service/               # OrderService with TenantContext usage
│               └── resources/
│                   └── application.yml        # Template config with all tvsm.core properties
│
└── tvsm-be-wiremock/               # ★ WireMock mock server for API simulation
    ├── pom.xml
    └── src/                        # WireMock mappings and Handlebars response templates
```

## Module Dependencies

```
tvsm-be-starter-parent (parent POM)
       │
       ├── tvsm-be-core ──────────── Published as JAR to Maven repo
       │        │                     Consumed by ALL downstream services
       │        └── Dependencies: Spring Boot Web, JPA, AOP, Actuator, WebFlux,
       │                          Azure Storage, Commons Validator, Lombok, SpringDoc
       │
       ├── tvsm-be-archetype ─────── Published as Maven archetype
       │        │                     Generates new service projects
       │        └── Generated projects depend on tvsm-be-core
       │
       └── tvsm-be-wiremock ──────── Standalone mock server
                                      No dependency on tvsm-be-core
```

## Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Multi-module Maven project | Separates reusable library (core) from project scaffolding (archetype) and testing tools (wiremock) |
| Spring Boot auto-configuration | Downstream services get all framework features by adding a single dependency — zero boilerplate |
| `AbstractRoutingDataSource` for multi-tenancy | Database-per-tenant isolation without requiring separate service instances |
| ThreadLocal-based `TenantContext` | Propagates tenant/user context through the request lifecycle without passing parameters |
| Servlet filter chain (not Spring Security) | Lightweight JWT + RBAC without the complexity of full Spring Security filter chain |
| Strategy pattern for validation | Supports simple fields, nested objects, collections, maps, and tuples with a single engine |
| JSON-file RBAC configuration | Permissions can be updated without code changes or redeployment (loaded at startup) |
| `@Searchable` annotation + `SearchSpecificationBuilder` | Declarative full-text search across entity fields including JSONB columns |
| `BeanPostProcessor` for interceptor injection | Automatically decorates all RestTemplate and ThreadPoolTaskExecutor beans without manual wiring |
| Conditional auto-configuration (`@ConditionalOnProperty`) | Cloud storage, RBAC, and validation are opt-in — services only pay for what they use |



## Tech Stack & Dependencies


# Tech Stack & Conventions — TVSM Backend Base Framework

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 21 |
| Framework | Spring Boot | 3.5.6 |
| Spring Core | Spring Framework | 6.2.11 |
| ORM | Spring Data JPA + Hibernate | (managed by Spring Boot BOM) |
| Database | PostgreSQL | Driver 42.7.3 |
| Connection Pool | HikariCP | (managed by Spring Boot) |
| Reactive HTTP | Spring WebFlux (WebClient) | 3.5.6 |
| AOP | Spring AOP + AspectJ | 1.9.24 |
| Monitoring | Spring Boot Actuator | 3.5.12 |
| API Docs | SpringDoc OpenAPI (Swagger UI) | 2.8.9 |
| Cloud Storage | Azure Blob Storage (spring-cloud-azure) | 5.23.0 |
| JSON | Jackson | 2.21.1 |
| Mapping | MapStruct | 1.6.3 |
| Boilerplate | Lombok | 1.18.38 |
| Validation | Apache Commons Validator | 1.10.0 |
| Utilities | Apache Commons Lang3 | 3.17.0 |
| Logging | SLF4J 2.0.17 + Logback 1.5.18 | |
| Testing | JUnit 5 (5.13.4) + Mockito (5.18.0) + H2 | |
| Coverage | JaCoCo | 0.8.14 |
| Build | Maven 3.9.6 | |
| Container | Amazon Corretto 21 (Docker) | |
| CI/CD | Azure DevOps Pipelines | |

## Coding Conventions

### General Style

- **Lombok everywhere** — Use `@Data`, `@Builder`, `@Slf4j`, `@RequiredArgsConstructor`, `@AllArgsConstructor` on all classes. Avoid writing getters/setters/constructors manually.
- **`@UtilityClass`** for static-only utility classes (e.g., `JsonUtil`, `DateTimeUtil`, `StringUtil`).
- **Private constructors** on constants classes to prevent instantiation.
- **`Optional<T>` return types** for methods that may return null (see `JsonUtil.fromJson()`).
- **Builder pattern** for DTOs and response objects (`APIResponse.builder()...build()`).
- **Comprehensive Javadoc** on all public methods and classes in the core module.

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Packages | `com.tvsm.core.<module>` or `com.tvsm.<service>.<layer>` | `com.tvsm.core.security.rbac` |
| Classes | PascalCase, suffix by role | `OrderService`, `BaseController`, `APIResponse` |
| Interfaces | PascalCase, no `I` prefix | `CloudStorageProvider`, `CloudStorageService` |
| DTOs | Suffix with `Dto` or `DTO` | `OrderRequestDto`, `SearchRequestDTO` |
| Entities | Plain domain name | `Order`, `BaseEntity` |
| Constants | UPPER_SNAKE_CASE in dedicated class | `BaseConstants.USER_TYPE_OEM` |
| Config properties | kebab-case in YAML | `tvsm.core.cloud-storage.enabled` |
| Annotations | PascalCase | `@Loggable`, `@ConfigValidated`, `@Searchable` |

### Package Structure for Downstream Services

```
com.tvsm.<service>/
├── controller/     # REST controllers extending BaseController
├── dto/            # Request/Response DTOs
├── entity/         # JPA entities extending BaseEntity
├── mapper/         # MapStruct mappers
├── repository/     # Spring Data JPA repositories
└── service/        # Business logic services
```

### Controller Conventions

- Extend `BaseController` for standardized response helpers.
- Use `@Tag`, `@Operation`, `@ApiResponses` from SpringDoc for API documentation.
- Return `ResponseEntity<APIResponse<T>>` — never raw objects.
- Use `success(data)` and `error(message, statusCode)` helper methods.
- Annotate validated parameters with `@ConfigValidated` for config-driven validation.

### Service Conventions

- Annotate with `@Service`, `@RequiredArgsConstructor`, `@Slf4j`, `@Transactional`.
- Use `TenantContext.getTenantId()` to scope data operations to the current tenant.
- Read-only operations use `@Transactional(readOnly = true)`.

### Entity Conventions

- Extend `BaseEntity` to inherit audit fields and soft delete.
- Use `@Searchable` on fields that should be included in full-text search.
- Use `@Searchable(keys = {"key1", "key2"})` for JSONB column search.
- Never hard-delete — set `active = false` instead.

## Patterns

### Multi-Tenancy Flow

```
Request → AuthenticationFilter → extracts tenantId from JWT/header
        → TenantContext.setCurrentTenantId(tenantId)
        → MultiTenantRoutingDataSource.determineCurrentLookupKey()
        → Routes to tenant-specific or default HikariCP pool
```

### Request Processing Pipeline

```
1. AuthenticationFilter (Order=1)
   - Extract & validate JWT
   - Populate TenantContext (tenantId, user, roles, token, channelPartner)
   - RBAC permission check
   
2. RequestValidationFilter (Order=2)
   - Validate URL path parameters
   - Validate query parameters
   - Validate headers (skip safe headers)
   - Validate JSON body (recursive node traversal)
   - Block if malicious content detected

3. ConfigValidationAspect (AOP)
   - Intercepts all com.tvsm..controller..* methods
   - Validates @ConfigValidated parameters against YAML rules

4. Controller → Service → Repository
```

### Search & Filter Pattern

```java
// In service:
SearchSpecificationBuilder<MyEntity> builder = new SearchSpecificationBuilder<>(MyEntity.class);
Specification<MyEntity> spec = Specification.where(SearchSpecificationBuilder.tenantSpec(tenantId))
    .and(builder.toSpecification(searchRequest));
Sort sort = builder.toSort(searchRequest.getSortOrders());
Page<MyEntity> results = repository.findAll(spec, PageRequest.of(page, size, sort));
```

### Cloud Storage Pattern

```java
// Upload
cloudStorageService.upload(UploadRequest.builder()
    .path("folder/file.pdf")
    .content(bytes)
    .contentType("application/pdf")
    .build());

// Download with range (streaming)
InputStream stream = cloudStorageService.downloadRange(path, rangeStart, rangeEnd);
```

### Config-Driven Validation

Validation rules in YAML (`validation-rules.yml`):
```yaml
validations:
  com_tvsm_order_dto_OrderRequestDto:
    moduleName: ORDER
    common:
      customerName:
        - rule: mandatory
        - rule: maxLength
          value: "100"
    tenants:
      tenant1:
        amount:
          - rule: numericRange
            value:
              min: "0"
              max: "999999"
```

## Error Handling

### Exception Hierarchy

| Exception | HTTP Status | When to Use |
|-----------|-------------|-------------|
| `APIException` | 500 | Unexpected server errors, integration failures |
| `NotFoundException` | 404 | Entity not found by ID |
| `ValidationException` | 400 | Business rule or input validation failures |
| `MethodArgumentNotValidException` | 400 | `@Valid` annotation failures (Spring) |

### Throwing Exceptions

```java
// Not found
throw new NotFoundException("Order not found", "ORDER_NOT_FOUND", "ORDER_NOT_FOUND_KEY", params);

// Validation failure (field-level)
Map<String, String> fieldErrors = Map.of("email", "INVALID_EMAIL");
throw new ValidationException(fieldErrors, "VALIDATION_ERROR_ORDER");

// General API error
throw new APIException("Payment gateway timeout", "PAYMENT_TIMEOUT", params, "PAYMENT_TIMEOUT_KEY", null);
```

### Log Sanitization

All exceptions logged through `GlobalExceptionHandler` are wrapped in `SanitizedException` which strips dangerous characters (`<`, `>`, `|`, `\n`, `\r`, `\t`) from stack traces to prevent log injection.

## Testing

### Stack

- **JUnit 5** — Test framework
- **Mockito** — Mocking
- **Spring Boot Test** — Integration testing with `@SpringBootTest`
- **H2** — In-memory database for repository tests
- **JaCoCo** — Code coverage reporting

### Conventions

- Test classes in `src/test/java` mirroring main package structure.
- Unit tests: `@ExtendWith(MockitoExtension.class)`, mock dependencies with `@Mock` / `@InjectMocks`.
- Integration tests: `@SpringBootTest` with H2 datasource.
- Coverage reports generated during `mvn test` phase via JaCoCo.
- Surefire HTML reports generated automatically.

### Running Tests

```bash
mvn test                    # Run all tests + generate coverage report
mvn verify                  # Run tests + verify coverage thresholds
```

## Deployment

### Docker Build (Multi-Stage)

```
Stage 1 (framework-builder): Amazon Corretto 21 + Maven 3.9.6
  → mvn clean install -DskipTests
  → Produces .m2 repository with framework artifacts

Stage 2 (framework-image): Amazon Corretto 21 + Maven 3.9.6
  → Copies .m2 from builder
  → Used as base image for downstream service builds
```

### CI/CD

- **Azure DevOps Pipelines** with shared template from `Devops_ISSM_pipelines` repo.
- Pipeline defined in `ci-pipeline.yaml` — references `pipelines/build-template.yml@devopsRepo`.
- Triggers: manual (no branch trigger, no PR trigger configured).

### Environment Variables (Secrets)

| Variable | Purpose |
|----------|---------|
| `BFW_JWT_PUBLIC_KEY_1` | RSA public key for JWT verification |
| `BFW_DB_USERNAME` | Default database username |
| `BFW_DB_PASSWORD` | Default database password |
| `BFW_AZURE_STORAGE_CONNECTION_STRING` | Azure Blob Storage connection string |

### Building & Installing Locally

```bash
# Install framework to local .m2
mvn clean install

# Generate a new service from archetype
mvn archetype:generate \
  -DgroupId=com.tvsm \
  -DartifactId=my-service \
  -DarchetypeGroupId=com.tvsm \
  -DarchetypeArtifactId=tvsm-be-archetype \
  -DarchetypeVersion=1.0.0 \
  -Dpackage=com.tvsm.myservice \
  -DinteractiveMode=false
```

## Logging

### Log Pattern

```
%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level [%X{traceId:-}] [%X{userId:-}] [%X{tenantId:-}] [%X{requestId:-}] %logger{36} - %msg%n
```

### MDC Fields

| Field | Source |
|-------|--------|
| `traceId` | `X-Trace-ID` header (auto-generated if missing) |
| `requestId` | `X-Request-ID` header |
| `tenantId` | JWT claim or `X-Tenant-ID` header |
| `userId` | JWT `sub` claim |

### Trace Propagation

- `RestTemplateInterceptor` and `WebClientInterceptor` automatically forward `traceId`, `tenantId`, and `Authorization` token to all outgoing HTTP calls.
- `TenantAwareMDCTaskDecorator` propagates MDC and TenantContext to `@Async` threads.

