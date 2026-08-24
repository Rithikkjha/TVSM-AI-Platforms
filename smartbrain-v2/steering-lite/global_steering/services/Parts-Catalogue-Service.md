# Parts-Catalogue-Service


## Product Context


# Parts Catalogue Service — Product Context

## What This Service Does

The Parts Catalogue Service is a read-oriented microservice that serves a **two-wheeler (motorcycle) parts catalogue** for TVS Motor Company. It exposes REST APIs to navigate, search, and retrieve parts information across a complex product hierarchy stored in a graph database (NebulaGraph) and a search engine (OpenSearch).

The service is multi-tenant — pricing and access are scoped by a `x-tenant-id` header (e.g., "GB"). Tenant validation is enforced via `TenantUtils.isTenantAllowed()`.

---

## Domain Hierarchy

The core domain is a **many-to-many hierarchy** of automotive entities:

```
Product → Vehicle → Model → Variant → Catalogue → Kit → Assembly → Part
```

Each level connects to the next via directed edges in NebulaGraph (`HAS_VEHICLE`, `HAS_MODEL`, etc.). A Part can belong to multiple Assemblies, an Assembly to multiple Kits, and so on up the chain.

---

## Domain Entities

| Entity | Description | Key Properties |
|--------|-------------|----------------|
| **Product** | Top-level brand/product line (e.g., "TVS 2W", "Norton") | name, sku_id, is_active |
| **Vehicle** | Specific vehicle type within a product | name, sku_id, is_active |
| **Model** | Vehicle model | name, sku_id, is_active |
| **Variant** | Model variant | name, sku_id, variant_part_id, is_active |
| **Catalogue** | Parts catalogue for a variant | name, sku_id, is_active |
| **Kit** | Group of assemblies within a catalogue | name, sku_id, is_active |
| **Assembly** | Group of parts within a kit | name, sku_id, is_active |
| **Part** | Individual spare part | part_number, sku_id, name, description, serviceable, has_associated_parts, has_supplementary, is_accessory, is_active |
| **Price** | Tenant-specific pricing for a part | part_number, price_type (RETAIL/DEALER), region, currency, amount, discount_percentage, tax_rate, tenant_id, effective_from/to |
| **Warranty** | Warranty terms for a part | part_number, warranty_type (MANUFACTURER/EXTENDED), duration_months, transferable, available_from/to |

All entities carry `created_at`, `last_updated_at`, and `is_active` (soft-delete) fields.

---

## Integrations

### NebulaGraph (Graph Database)
- **Role**: Source of truth for the product hierarchy and graph relationships.
- **Usage**: Graph traversals for chart data, reverse hierarchy lookups, entity-by-parent queries, and as a **fallback** when OpenSearch is unavailable.
- **Connection**: Pooled sessions via `NebulaPool` with configurable min/max connections, idle time, and timeouts.
- **Space**: `parts_catalogue_graph`

### OpenSearch (Search Engine)
- **Role**: Primary read source for paginated search, part details, prices, warranties, and hierarchy data.
- **Indices**: `parts_catalogue` (parts), `parts_prices`, `parts_warranties`, `parts_hierarchies`
- **Usage**: Full-text search with boosting, fuzzy matching, scroll API for large result sets, batch multi-get operations.
- **Connection**: Apache HC5 async client with SSL, connection pooling, and `SafeResponseConsumer` to protect the I/O reactor.

### Azure Blob Storage
- Dependency present (`azure-storage-blob`) but not actively used in current read-path code. Likely used by a companion ingestion service.

---

## Business Rules

1. **Soft Delete**: All entities use `is_active` flag. Queries always filter for `is_active = true`.
2. **Multi-Tenancy**: Prices are tenant-scoped. The `x-tenant-id` header is mandatory for search and traversal endpoints. Invalid tenants are rejected.
3. **Serviceability Filter**: Parts can be filtered by `serviceable` (true/false) and `is_accessory` flags.
4. **Hierarchy Paths**: A single part can have multiple hierarchy paths (e.g., same part used in different assemblies/kits). The `totalPaths` field indicates how many paths exist.
5. **Data Freshness**: OpenSearch is the primary source; NebulaGraph is the fallback. A "fresh" endpoint bypasses cache for real-time data.
6. **Product-Specific Logic**: Strategy pattern (`KitAssemblyServiceStrategy`) handles product-specific business rules (e.g., TVS 2W vs Norton have different kit/assembly retrieval logic).
7. **Input Sanitization**: All user-provided IDs and names pass through `StringSanitizer.isSafeEntity()` before use in queries.
8. **Pagination**: Search results are paginated (default page=0, size=50, max page=500, max size=500).
9. **Pricing Rules**: Prices have effective date ranges, minimum quantities, tax rates, and discount percentages. Multiple price types (RETAIL, DEALER) can exist per part per tenant.



## Code Structure


# Parts Catalogue Service — Project Structure

## Directory Layout

```
Parts-Catalogue-Service/
├── .kiro/steering/              # Kiro steering files (this documentation)
├── azure-pipelines/             # Security scanning pipeline definitions
│   ├── ast-image-scan.yaml      # Docker image vulnerability scanning
│   ├── ast-prod.yaml            # Checkmarx AST scan for production
│   └── ast-uat.yaml             # Checkmarx AST scan for UAT
├── src/
│   ├── main/
│   │   ├── java/org/com/graph/
│   │   │   ├── ProductCatalogue.java        # Spring Boot application entry point
│   │   │   ├── config/                      # Configuration & bean definitions
│   │   │   │   ├── BatchProperties.java     # Batch operation timeout config
│   │   │   │   ├── CacheConfig.java         # Caffeine cache manager (3 caches)
│   │   │   │   ├── CacheProperties.java     # Cache TTL and size config
│   │   │   │   ├── NebulaGraphConfig.java   # NebulaPool bean with host parsing
│   │   │   │   ├── NebulaGraphProperties.java # Nebula connection properties
│   │   │   │   ├── OpenSearchConfig.java    # OpenSearch client bean with SSL/auth
│   │   │   │   ├── OpenSearchProperties.java # OpenSearch connection properties
│   │   │   │   ├── ResilienceEventConfig.java # Retry/CB event logging
│   │   │   │   ├── SafeResponseConsumer.java # HC5 I/O reactor crash protection
│   │   │   │   └── SwaggerConfig.java       # OpenAPI/Swagger configuration
│   │   │   ├── constants/                   # Static constants
│   │   │   │   ├── ApiConstants.java        # Product name constants (TVS_2W, etc.)
│   │   │   │   └── NebulaGraphConstants.java # Tag names, edge types, property names
│   │   │   ├── controller/                  # REST API layer (5 controllers)
│   │   │   │   ├── ChartController.java     # /api/chart/* — hierarchy chart data
│   │   │   │   ├── EntitiesController.java  # /api/* — CRUD-like entity fetching
│   │   │   │   ├── ProductDetailsController.java # /api/products/* — product-level queries
│   │   │   │   ├── SearchController.java    # /api/search — paginated part search
│   │   │   │   └── TraversalController.java # /api/reverseHierarchy/* — bottom-up traversal
│   │   │   ├── dto/                         # Data Transfer Objects (request/response)
│   │   │   │   ├── ApiResponseWrapper.java  # Unified API response envelope
│   │   │   │   ├── CustomProblemDetail.java # RFC 7807 error response
│   │   │   │   ├── PartDetailsResponseDto.java # Main part details response (nested hierarchy)
│   │   │   │   ├── PartDetailsSearchRequestDto.java # Search request with filters
│   │   │   │   ├── SearchRequestDto.java    # Generic OpenSearch search request
│   │   │   │   ├── SearchResponseDto.java   # Generic OpenSearch search response
│   │   │   │   └── ...                      # Entity-specific response DTOs
│   │   │   ├── exception/                   # Exception handling
│   │   │   │   ├── GlobalExceptionHandler.java # @RestControllerAdvice (RFC 7807)
│   │   │   │   ├── GraphException.java      # NebulaGraph operation failures
│   │   │   │   └── SearchException.java     # OpenSearch operation failures
│   │   │   ├── mapper/                      # Entity → DTO mappers (static methods)
│   │   │   │   ├── HierarchyMapper.java     # HierarchyData → HierarchyResponseDto
│   │   │   │   ├── PriceMapper.java         # List<Price> → PriceResponseDto
│   │   │   │   └── WarrantyMapper.java      # List<Warranty> → List<WarrantyResponseDto>
│   │   │   ├── model/                       # Domain entities / data models
│   │   │   │   ├── BaseModel.java           # Base for OpenSearch documents
│   │   │   │   ├── BaseEntity.java          # Base for NebulaGraph entities
│   │   │   │   ├── Part.java                # Part entity (both sources)
│   │   │   │   ├── Price.java               # Price entity with PriceType enum
│   │   │   │   ├── Warranty.java            # Warranty entity with WarrantyType enum
│   │   │   │   ├── HierarchyData.java       # Flattened hierarchy path record
│   │   │   │   ├── EdgeRelationship.java    # Graph edge representation
│   │   │   │   └── ...                      # Vehicle, Model, Variant, etc.
│   │   │   ├── repository/                  # Data access layer (dual-source)
│   │   │   │   ├── nebula/                  # NebulaGraph repositories
│   │   │   │   │   ├── NebulaGraphRepository.java # Abstract base (session mgmt, query execution)
│   │   │   │   │   ├── ChartRepository.java # Full hierarchy traversal for charts
│   │   │   │   │   ├── PartRepository.java  # Part lookups, hierarchy data by part number
│   │   │   │   │   ├── PriceRepository.java # Price lookups from graph
│   │   │   │   │   ├── WarrantyRepository.java # Warranty lookups from graph
│   │   │   │   │   └── ...                  # Entity-specific repos (Vehicle, Model, etc.)
│   │   │   │   └── opensearch/              # OpenSearch repositories
│   │   │   │       ├── OpenSearchRepository.java # Abstract base (search, scroll, circuit breaker)
│   │   │   │       ├── PartRepository.java  # Part search, batch fetch by part numbers
│   │   │   │       ├── PriceRepository.java # Price search by part number(s) + tenant
│   │   │   │       ├── WarrantyRepository.java # Warranty search by part number(s)
│   │   │   │       └── HierarchyDataRepository.java # Hierarchy search with scroll
│   │   │   ├── service/                     # Business logic layer
│   │   │   │   ├── HierarchyService.java    # Core service: search, part details, batch ops
│   │   │   │   ├── ChartService.java        # Chart data orchestration
│   │   │   │   ├── ProductService.java      # Product-level operations
│   │   │   │   ├── PartService.java         # Part entity operations
│   │   │   │   └── ...                      # Vehicle, Model, Variant, etc. services
│   │   │   │   └── strategy/               # Strategy pattern implementations
│   │   │   │       ├── HierarchyStrategy.java # Interface for chart hierarchy building
│   │   │   │       ├── HierarchyBuilder.java # Recursive hierarchy tree construction
│   │   │   │       ├── ProductHierarchyStrategy.java # Build from Product level down
│   │   │   │       ├── VehicleHierarchyStrategy.java # Build from Vehicle level down
│   │   │   │       ├── ModelHierarchyStrategy.java   # Build from Model level down
│   │   │   │       ├── VariantHierarchyStrategy.java # Build from Variant level down
│   │   │   │       ├── KitAssemblyServiceStrategy.java # Interface for product-specific kit logic
│   │   │   │       ├── KitAssemblyStrategyResolver.java # Resolves strategy by product name
│   │   │   │       └── TvsKitAssemblyStrategy.java # TVS 2W-specific implementation
│   │   │   └── util/                        # Utility classes
│   │   │       ├── ResponseUtils.java       # Standardized response builders
│   │   │       ├── StringSanitizer.java     # Input validation and injection prevention
│   │   │       └── TenantUtils.java         # Tenant allowlist validation
│   │   └── resources/
│   │       ├── application.properties       # Main config (env-var driven)
│   │       └── schema/
│   │           └── nebula-schema.ngql        # NebulaGraph DDL (tags, edges, indexes)
│   └── test/
│       └── java/org/com/graph/
│           └── service/
│               └── HierarchyServiceTest.java # Comprehensive unit tests for core service
├── pom.xml                      # Maven build config (Spring Boot 3.5.14, Java 21)
├── Dockerfile                   # Multi-stage build (Maven → Eclipse Temurin JRE 25)
├── ci-pipeline.yaml             # Azure DevOps CI pipeline definition
├── cd-pipeline.yaml             # Azure DevOps CD pipeline (dev → uat → prod)
├── sonar.yml                    # SonarQube analysis + quality gate pipeline
└── README.md                    # Project documentation
```

---

## Module Dependencies

```
Controller → Service → Repository (nebula/ + opensearch/)
     ↓           ↓           ↓
    DTO        Model       Config (properties, pools, clients)
     ↓           ↓
   Mapper     Exception
     ↓
   Util (ResponseUtils, StringSanitizer, TenantUtils)
```

- **Controllers** depend on Services and DTOs. They validate input via `StringSanitizer` and build responses via `ResponseUtils`.
- **Services** orchestrate between Nebula and OpenSearch repositories. `HierarchyService` is the central service handling search, part details, and batch operations.
- **Repositories** are split by data source. Each source has an abstract base class (`NebulaGraphRepository`, `OpenSearchRepository`) providing session/client management, circuit breakers, and retries.
- **Mappers** are stateless static utility classes converting between model entities and DTOs.
- **Config** classes are self-contained — each external system has its own `*Properties` + `*Config` pair.

---

## Architectural Decisions

### Dual Data Source with Fallback
OpenSearch is the primary read source for performance (pagination, full-text search, batch queries). NebulaGraph serves as the source of truth and fallback when OpenSearch is unavailable or returns empty results. This is implemented in `HierarchyService` via `fetchHierarchyWithFallback()`, `fetchPricesWithFallback()`, and `fetchWarrantiesWithFallback()`.

### Parallel Data Fetching
Part details require data from 3 sources (hierarchy, prices, warranties). These are fetched concurrently using `CompletableFuture` with a fixed thread pool (4 threads) and a 5-second timeout. Partial results are returned if some futures fail.

### Strategy Pattern for Extensibility
Two strategy hierarchies exist:
1. **HierarchyStrategy** — determines how to build chart data starting from different hierarchy levels (Product, Vehicle, Model, Variant).
2. **KitAssemblyServiceStrategy** — handles product-specific business logic (TVS 2W vs Norton). New products are added by implementing the interface and registering via Spring DI.

### Abstract Repository Base Classes
Both `NebulaGraphRepository` and `OpenSearchRepository` are abstract classes (not interfaces) providing:
- Connection/session lifecycle management
- Common query execution with error handling
- Circuit breaker and retry annotations
- Helper methods for type-safe value extraction

### Unified Response Envelope
All API responses use `ApiResponseWrapper<T>` for consistency. Errors use `CustomProblemDetail` (RFC 7807). `ResponseUtils` provides factory methods for success, error, paged, and empty responses.

### Configuration via Environment Variables
All sensitive and environment-specific values (hosts, ports, credentials, index names) are injected via environment variables in `application.properties`. No profile-specific property files are committed — environment differences are handled at deployment time.



## Tech Stack & Dependencies


# Parts Catalogue Service — Technical Guide

## Tech Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Language | Java | 21 |
| Framework | Spring Boot | 3.5.14 |
| Build Tool | Maven | 3.9+ |
| Graph Database | NebulaGraph (client) | 3.8.4 |
| Search Engine | OpenSearch (Java client) | 3.8.0 |
| Caching | Caffeine | 3.2.3 |
| Resilience | Resilience4j (Spring Cloud) | 3.3.2 |
| API Docs | SpringDoc OpenAPI | 2.8.14 |
| JSON | Jackson (with JSR-310) | 2.21.3 |
| Boilerplate | Lombok | 1.18.42 |
| HTTP Client | Apache HC5 (async) | via OpenSearch client |
| Cloud Storage | Azure Blob Storage | 12.33.3 |
| Container | Docker (Eclipse Temurin JRE 25) | Multi-stage |
| CI/CD | Azure DevOps Pipelines | — |
| Code Quality | SonarQube | — |
| Security Scan | Checkmarx AST | — |
| Testing | JUnit 5 + Mockito + Testcontainers | — |

---

## Coding Conventions

### General Style
- **Lombok everywhere**: `@Data`, `@Builder`, `@RequiredArgsConstructor`, `@Slf4j` on nearly all classes. Avoid writing getters/setters/constructors manually.
- **Constructor injection**: All dependencies are `final` fields injected via `@RequiredArgsConstructor`. No `@Autowired` on fields.
- **Immutable where possible**: DTOs use `@Builder` pattern. Service fields are `final`.
- **Package-by-layer**: Code is organized by technical layer (controller, service, repository, dto, model, etc.), not by feature.

### Naming Conventions
- **Classes**: PascalCase. Suffix indicates role: `*Controller`, `*Service`, `*Repository`, `*Properties`, `*Config`, `*Dto`, `*Exception`.
- **Constants**: `UPPER_SNAKE_CASE` in dedicated `*Constants` classes.
- **Methods**: camelCase. Repository methods use descriptive names like `getPartsByAssemblyIdFromNebula()`, `getPricesByPartNumber()`.
- **Properties**: kebab-case in `application.properties` (e.g., `nebula.graph.max-conn-size`), mapped to camelCase Java fields via `@ConfigurationProperties`.

### Configuration Pattern
Each external system follows the same pattern:
1. `*Properties.java` — `@ConfigurationProperties` with `@Validated` and JSR-303 annotations
2. `*Config.java` — `@Configuration` class that creates the client/pool bean using the properties

### Response Pattern
All controllers return `ResponseEntity<ApiResponseWrapper<T>>` using `ResponseUtils`:
```java
return ResponseUtils.buildSuccessResponse("Message", data);
return ResponseUtils.buildPagedSuccessResponse("Message", pagedResult);
return ResponseUtils.buildPagedBadRequestResponse("Error", emptyPage);
```

### Input Validation
- All user-provided IDs/names are validated via `StringSanitizer.isSafeEntity()` before use.
- Request DTOs use Jakarta Validation annotations (`@Min`, `@Max`, `@NotBlank`).
- The `x-tenant-id` header is validated via `TenantUtils.isTenantAllowed()`.

---

## Design Patterns

### Strategy Pattern
- **HierarchyStrategy**: Interface with `getTag()` and `build()`. Implementations: `ProductHierarchyStrategy`, `VehicleHierarchyStrategy`, `ModelHierarchyStrategy`, `VariantHierarchyStrategy`. Used by `ChartController` to build chart data from different starting points.
- **KitAssemblyServiceStrategy**: Interface with `supports(productName)` and `getKitsAndAssemblies(tenantId)`. Resolved via `KitAssemblyStrategyResolver` which iterates registered strategies.

### Template Method (Abstract Base Repositories)
- `NebulaGraphRepository`: Provides `execute(query)`, `executeQuery(query, mapper)`, and type-safe value extraction helpers. Subclasses implement domain-specific queries.
- `OpenSearchRepository`: Provides multiple `execute()` overloads with pagination, sorting, source filtering, and scroll support. Annotated with `@Retry` and `@CircuitBreaker`.

### Parallel Composition
`HierarchyService` uses `CompletableFuture.supplyAsync()` with a fixed thread pool to fetch hierarchy, prices, and warranties concurrently. Results are collected with `CompletableFuture.allOf()` and a configurable timeout.

### Fallback Chain
For each data type (hierarchy, prices, warranties):
1. Try OpenSearch (primary)
2. If empty or exception → try NebulaGraph (fallback)
3. If both fail → return empty collection (graceful degradation)

---

## Error Handling

### Exception Hierarchy
```
RuntimeException
├── GraphException        — NebulaGraph failures (query, errorCode, isRetryable())
├── SearchException       — OpenSearch failures (operation, index, isRetryable())
├── IllegalArgumentException — Input validation failures
└── NoSuchElementException   — Entity not found
```

### Global Exception Handler (`GlobalExceptionHandler`)
Maps exceptions to RFC 7807 `CustomProblemDetail` responses:

| Exception | HTTP Status | Response |
|-----------|-------------|----------|
| `BindException`, `MethodArgumentNotValidException` | 400 | Field-level validation errors map |
| `ConstraintViolationException` | 400 | Constraint violation details |
| `IllegalArgumentException`, `MissingRequestHeaderException` | 400 | Error message |
| `EntityNotFoundException`, `NoSuchElementException` | 404 | "Resource Not Found" |
| `HttpRequestMethodNotSupportedException` | 405 | Method not allowed |
| `Exception` (catch-all) | 500 | "Unexpected error occurred" |

### Resilience4j Configuration

**Circuit Breakers** (separate instances for Nebula and OpenSearch):
- Sliding window: 10 calls (COUNT_BASED)
- Failure threshold: 50%
- Open state duration: 30 seconds
- Half-open calls: 3
- Slow call threshold: >10s duration, >80% rate
- Auto transition: open → half-open

**Retries** (separate instances for Nebula and OpenSearch):
- Max attempts: 3
- Wait duration: 1 second
- Exponential backoff: multiplier 2
- Retry on: `IOException`, `SocketTimeoutException`, `GraphException`/`SearchException`

**Event Logging** (`ResilienceEventConfig`):
- Logs every retry attempt, success after retry, and final failure
- Logs circuit breaker state transitions and threshold breaches

### SafeResponseConsumer
Wraps the Apache HC5 `AsyncResponseConsumer` to catch `Error` (e.g., `OutOfMemoryError`) and convert to `RuntimeException`, preventing permanent I/O reactor shutdown.

---

## Caching

Three Caffeine caches managed by `CacheConfig`:

| Cache Name | TTL | Max Size | Purpose |
|-----------|-----|----------|---------|
| `hierarchyCache` | 30 min | 1000 | Hierarchy traversal results |
| `nodeCache` | 60 min | 5000 | Individual part details (`@Cacheable` on `getPartDetailsByPartNumber`) |
| `searchCache` | 15 min | 500 | Search query results |

All caches have `recordStats()` enabled for monitoring. The "fresh" endpoint (`getPartDetailsByPartNumberFresh`) bypasses cache intentionally.

---

## Testing

### Framework & Tools
- **JUnit 5** with `@ExtendWith(MockitoExtension.class)`
- **Mockito** for mocking (lenient strictness where needed)
- **Testcontainers** for OpenSearch integration tests
- **Spring Boot Test** for context-loading tests

### Test Organization
- Nested `@Nested` classes group related tests by method/scenario
- `@DisplayName` on every test for readable output
- Test data setup in `@BeforeEach` methods

### Coverage Areas
- Happy path and error cases for all service methods
- Fallback behavior (OpenSearch down → Nebula fallback)
- Parallel fetch failures and timeouts
- Batch operations with partial failures
- Pagination edge cases
- Cache annotation verification (reflection-based)
- Input validation (null, blank, invalid)

### Running Tests
```bash
mvn test                          # Run all tests
mvn test -Dtest=HierarchyServiceTest  # Run specific test class
mvn clean test jacoco:report      # Run with coverage report
```

---

## Deployment

### Docker Build
Multi-stage Dockerfile:
1. **Build stage**: `maven:3-amazoncorretto-25-alpine` — compiles and packages the JAR
2. **Runtime stage**: `eclipse-temurin:25-jre-ubi10-minimal` — runs the application

JVM flags in the entrypoint:
- `G1GC` garbage collector
- `UseContainerSupport` + `MaxRAMPercentage=75%` for container-aware memory
- `ExitOnOutOfMemoryError` + heap dump on OOM
- GC logging to `/parts-catalogue-service/logs/gc.log`

### CI/CD Pipeline (Azure DevOps)

**CI Pipeline** (`ci-pipeline.yaml`):
- Triggered by Sonar pipeline completion on `main`
- Uses shared build template from `Devops_ISSM_pipelines` repo
- Produces Docker image

**CD Pipeline** (`cd-pipeline.yaml`):
- Triggered by CI pipeline completion
- Deploys via Helm charts to: dev → (manual approval) → uat → (manual approval) → prod
- Configurable approval emails and timeouts (default 24h)

**Quality Gates** (`sonar.yml`):
- SonarQube analysis with Maven + Java 21
- Quality gate enforcement (build breaker on failure)
- Runs on `ubuntu-latest`

**Security Scanning** (`azure-pipelines/`):
- Checkmarx AST scans for UAT and production
- Docker image vulnerability scanning

### Environment Configuration
All runtime config is injected via environment variables:
- `EXPOSED_PORT`, `NEBULA_HOSTS`, `NEBULA_PORT`, `NEBULA_SPACE`, `NEBULA_USERNAME`, `NEBULA_PASSWORD`
- `OPENSEARCH_HOST`, `OPENSEARCH_PORT`, `OPENSEARCH_USERNAME`, `OPENSEARCH_PASSWORD`
- `OPENSEARCH_PARTS_INDEX`, `OPENSEARCH_PRICES_INDEX`, `OPENSEARCH_WARRANTIES_INDEX`, `OPENSEARCH_HIERARCHIES_INDEX`

### Health & Monitoring
- **Actuator endpoints**: `/actuator/health`, `/actuator/metrics`, `/actuator/prometheus`
- **Health indicators**: Circuit breaker status included in health check
- **Logging**: Structured console output with timestamp, thread, level, logger, message

