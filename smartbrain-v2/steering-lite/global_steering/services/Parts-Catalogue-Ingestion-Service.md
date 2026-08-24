# Parts-Catalogue-Ingestion-Service


## Product Context


# Parts Catalogue Ingestion Service — Product Context

## What This Service Does

This microservice ingests parts catalogue data from external APIs (Norton Motorcycles, TVS Motor) and persists it into a dual-database architecture:
- **Nebula Graph** for hierarchical relationships and graph traversal
- **OpenSearch** for full-text search and filtering

It supports both manual (API-triggered) and scheduled (cron-based) ingestion workflows, with region-aware configuration for multi-geography deployments.

## Domain Entities

The catalogue follows an 8-level hierarchy with many-to-many relationships at every level:

```
Product → Vehicle → Model → Variant → Catalogue → Kit → Assembly → Part
```

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **Product** | Top-level brand (e.g., "Norton") | name, sku_id |
| **Vehicle** | Vehicle line under a product | name, sku_id |
| **Model** | Specific model (e.g., "Commando 961") | name, sku_id |
| **Variant** | Model variant (e.g., "Sport", "Cafe Racer") | name, sku_id, variant_part_id |
| **Catalogue** | Parts catalogue section | name, sku_id |
| **Kit** | Group of assemblies within a catalogue | name, sku_id |
| **Assembly** | Mechanical assembly containing parts | name, sku_id, is_accessory_assembly |
| **Part** | Individual spare part (leaf node) | part_number, name, description, is_accessory, serviceable |

Additional entities attached to Parts:
- **Price** — pricing with type (RETAIL, DEALER, WHOLESALE), currency, region, effective dates, tax, discounts
- **Warranty** — warranty coverage with type, duration, transferability, availability dates

### Many-to-Many Relationships

Every level supports many-to-many: a Part can belong to multiple Assemblies, an Assembly to multiple Kits, etc. Relationships are stored as graph edges, not embedded arrays.

### Entity Identity

All entity IDs are deterministic SHA-256 hex hashes derived from the hierarchy path or part number. SKU IDs follow the pattern `PREFIX-<16-char-hex>` (e.g., `PART-9F3C2B817A44C3`).

## External Integrations

| System | Protocol | Purpose |
|--------|----------|---------|
| **Norton Catalogue API** | REST (PTC ServiceCenter) | Fetch Norton motorcycle parts hierarchy |
| **TVS Catalogue API** | REST (PTC ServiceCenter) | Fetch TVS motor parts hierarchy |
| **Price API** | REST (Azure Function) | Fetch pricing data (Domestic, Norton, IB) |
| **Nebula Graph** | Native client (port 9669) | Store graph vertices and edges |
| **OpenSearch** | REST (port 9200) | Index documents for search |

### API Authentication
- Norton/TVS APIs: Basic auth via `Authorization` header
- Price API: API key via `code` query parameter

## Business Rules

### Ingestion Workflow
1. Catalogue ingestion runs first (Norton and/or TVS in parallel per region config)
2. Warranty ingestion follows (creates default warranties for all parts)
3. Price ingestion runs last (fetches prices for all part numbers in the graph)

### Region Configuration
- **UK region**: Ingests NORTON only, cron at 3 AM
- **IND region**: Ingests NORTON + TVS, cron at 2 AM
- Region is set via `INGESTION_REGION` environment variable

### Accessory Classification
- An Assembly is an accessory if its name contains "accessories" (case-insensitive)
- A Part is an accessory if ANY of its parent assemblies is an accessory assembly (OR semantics)
- Accessory status is recomputed when a part gains a new parent assembly

### Pricing Rules
- Domestic prices default to INR currency
- Norton prices default to GBP currency
- International Business (IB) prices default to USD currency
- Price IDs include region + type to prevent collisions (e.g., DOMESTIC_MRP vs NORTON_MRP)
- Prices are fetched in batches of 100 part numbers

### Warranty Rules
- Default warranty: 24 months, DURATION type, non-transferable
- Created by "system" user for all parts in the catalogue
- Warranty availability has no end date by default

### Locking & Concurrency
- Only one ingestion per datasource can run at a time (ConcurrentHashMap-based lock)
- Lock acquisition is all-or-nothing for a region's datasources
- Manual ingestion returns 409 CONFLICT if a datasource is already locked
- Locks are released in a finally block after ingestion completes

### Deduplication
- Entities are cached in ConcurrentHashMaps during ingestion
- If an entity already exists, only a new edge relationship is created (no duplicate vertices)
- Graph uses UPSERT semantics (insert if not exists, update if exists)



## Code Structure


# Parts Catalogue Ingestion Service — Project Structure

## Directory Layout

```
src/main/java/org/com/graph/
├── IngestionServiceApplication.java        # Spring Boot entry point
│
├── config/                                 # Spring @Configuration and @ConfigurationProperties
│   ├── ApiClientConfig.java                # RestClient beans for Norton, TVS, Price APIs (SSL, timeouts)
│   ├── CatalogueApiProperties.java         # Base class for catalogue API config
│   ├── NortonCatalogueApiProperties.java   # Norton-specific API properties
│   ├── TvsCatalogueApiProperties.java      # TVS-specific API properties
│   ├── PriceApiProperties.java             # Price API connection properties
│   ├── ExecutorConfig.java                 # Virtual thread executor + TaskScheduler beans
│   ├── NebulaGraphConfig.java              # NebulaPool bean (connection pool, IPv4/IPv6 parsing)
│   ├── NebulaGraphProperties.java          # Nebula connection properties
│   ├── OpenSearchConfig.java               # OpenSearchClient bean
│   ├── OpenSearchProperties.java           # OpenSearch connection + index properties
│   ├── RegionConfiguration.java            # Region config model (YAML-based)
│   ├── RegionSchedulerProperties.java      # @ConfigurationProperties for ingestion.region.*
│   ├── ResilienceConfig.java               # CircuitBreaker + Retry beans (catalogue, nebula, opensearch)
│   └── SwaggerConfig.java                  # OpenAPI/Springdoc configuration
│
├── constants/
│   └── NebulaGraphConstants.java           # All tag names, property names, edge types as constants
│
├── controller/                             # REST API layer
│   ├── IngestionController.java            # POST /trigger, /trigger/prices, /trigger/warranties, GET /status, /locks/status
│   └── RegionConfigurationController.java  # GET/PUT region config endpoints
│
├── dto/                                    # Data Transfer Objects (API responses)
│   ├── AcdApiHierarchyNodeResponseDto.java # Hierarchy node from Norton/TVS API
│   ├── ApiResponseDto.java                 # Generic paginated API response wrapper
│   ├── ApiResponseWrapper.java             # Simple response wrapper
│   └── PriceApiResponseDto.java            # Price API response with nested PricePartDto
│
├── event/
│   └── RegionConfigurationChangedEvent.java # Spring ApplicationEvent for config changes
│
├── exception/                              # Custom exception hierarchy
│   ├── ApiException.java                   # External API errors (status code, URL, retryable logic)
│   ├── GraphException.java                 # Nebula Graph errors (query, error code, retryable logic)
│   ├── IngestionException.java             # Workflow errors (phase, entity type/id, retryable logic)
│   └── SearchException.java               # OpenSearch errors (operation, index, retryable logic)
│
├── model/                                  # Domain entities
│   ├── BaseModel.java                      # Root: id, isActive, lastUpdatedAt, createdAt
│   ├── BaseEntity.java                     # Adds: name, skuId, abstract getEntityType/getChildEntityType/getParentEntityType
│   ├── Product.java                        # Root of hierarchy
│   ├── Vehicle.java                        # productIds (Set<String>)
│   ├── Model.java                          # vehicleIds (Set<String>)
│   ├── Variant.java                        # modelIds (Set<String>), variantPartId
│   ├── Catalogue.java                      # variantIds (Set<String>)
│   ├── Kit.java                            # catalogueIds (Set<String>)
│   ├── Assembly.java                       # kitIds (Set<String>), isAccessoryAssembly
│   ├── Part.java                           # assemblyIds (Set<String>), partNumber, isAccessory
│   ├── Price.java                          # partNumber, priceType, amount, currency, region, tax
│   ├── Warranty.java                       # partNumber, warrantyType, durationMonths, transferable
│   ├── EdgeRelationship.java              # sourceId, targetId, edgeType (enum with forHierarchy())
│   └── searchdocument/
│       └── HierarchySearchDocument.java    # Flattened hierarchy for OpenSearch indexing
│
├── repository/                             # Data access layer
│   ├── NebulaGraphRepository.java          # Low-level nGQL execution with retry (session pool management)
│   ├── CatalogueGraphRepository.java       # Entity-specific upsert/batch operations, edge creation
│   └── OpenSearchRepository.java           # Index CRUD, bulk indexing, index lifecycle management
│
├── scheduler/
│   └── RegionAwareIngestionScheduler.java  # @PostConstruct cron scheduling via TaskScheduler
│
├── service/                                # Business logic
│   ├── IngestionService.java               # Interface: executeFullIngestion(), getStatistics(), isApiHealthy()
│   ├── NortonIngestionService.java         # Norton-specific: recursive hierarchy traversal with caching
│   ├── TvsIngestionService.java            # TVS-specific: same pattern, different API client
│   ├── IngestionOrchestrator.java          # Coordinates: catalogue → warranty → price ingestion
│   ├── IngestionApiClientService.java      # Generic API client with circuit breaker + retry
│   ├── TransformationService.java          # DTO → domain entity conversion (switch on type)
│   ├── GraphPersistenceService.java        # Entity persistence + edge creation (delegates to repository)
│   ├── SearchService.java                  # OpenSearch indexing, hierarchy document creation
│   ├── PriceApiService.java                # Price API client (batched fetching, response transformation)
│   ├── PriceIngestionService.java          # Chunked parallel ingestion to graph + search with DLQ
│   ├── WarrantyIngestionService.java       # Default warranty creation + parallel ingestion
│   ├── DatasourceIngestionLockManager.java # ConcurrentHashMap-based lock for single-instance
│   └── strategy/
│       ├── IClientStrategy.java            # Strategy interface for datasource-specific behavior
│       ├── NortonClientStrategy.java       # Norton URL extraction logic
│       └── TvsClientStrategy.java          # TVS URL extraction logic
│
└── util/                                   # Stateless utilities
    ├── NebulaIdGenerator.java              # SHA-256 hex ID generation, SKU ID generation
    ├── NebulaQueryBuilder.java             # Fluent nGQL query construction (UPSERT, INSERT, DELETE)
    ├── AccessoryClassifier.java            # Assembly/Part accessory classification logic
    └── StringSanitizer.java                # Input sanitization for graph-safe strings

src/main/resources/
├── application.properties                  # Main config (all values from env vars)
├── application-dev.properties              # Dev profile overrides (localhost, scheduler disabled)
└── schema/
    └── nebula-schema.ngql                  # Full Nebula Graph DDL (tags, edges, indexes)

src/test/java/org/com/graph/               # Mirrors main structure
├── config/                                 # Config bean tests
├── controller/                             # Controller tests (MockMvc)
├── dto/                                    # DTO serialization tests
├── event/                                  # Event tests
├── exception/                              # Exception behavior tests
├── model/                                  # Entity tests (builders, methods)
├── repository/                             # Repository tests (mocked clients)
├── scheduler/                              # Scheduler tests
├── service/                                # Service tests (mocked dependencies)
└── util/                                   # Utility tests (pure functions)
```

## Module Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                        Controller Layer                          │
│  IngestionController, RegionConfigurationController             │
└──────────────────────────────┬──────────────────────────────────┘
                               │ depends on
┌──────────────────────────────▼──────────────────────────────────┐
│                         Service Layer                            │
│  IngestionOrchestrator ──→ IngestionService (Norton/TVS)        │
│       │                     ├── IngestionApiClientService        │
│       │                     ├── TransformationService            │
│       │                     ├── GraphPersistenceService          │
│       │                     └── SearchService                    │
│       ├──→ PriceIngestionService ──→ PriceApiService            │
│       ├──→ WarrantyIngestionService                             │
│       └──→ DatasourceIngestionLockManager                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │ depends on
┌──────────────────────────────▼──────────────────────────────────┐
│                       Repository Layer                           │
│  CatalogueGraphRepository ──→ NebulaGraphRepository (NebulaPool)│
│  OpenSearchRepository (OpenSearchClient)                        │
└─────────────────────────────────────────────────────────────────┘
```

## Architectural Decisions

### Dual-Database Architecture
- **Nebula Graph** stores the hierarchy and relationships (graph traversal queries)
- **OpenSearch** stores flattened documents for search (full-text, filters, aggregations)
- Both are written in parallel during ingestion for consistency

### Virtual Threads (Java 21)
- `Executors.newVirtualThreadPerTaskExecutor()` for all ingestion work
- Ideal for I/O-bound operations (API calls, database writes)
- No manual pool sizing needed — JVM scales automatically
- Manual `Thread.ofVirtual()` for fire-and-forget async triggers in controller

### Recursive Hierarchy Traversal
- Each `IngestionService` (Norton/TVS) recursively walks the API hierarchy
- Uses in-memory `ConcurrentHashMap` caches per entity type for deduplication
- `BlockingQueue` buffers for batched OpenSearch indexing (flush at bulk-size threshold)

### Resilience Strategy
- Three independent circuit breaker instances: catalogueApi, nebulaGraph, openSearch
- Three independent retry instances with exponential backoff
- Circuit breakers auto-transition from OPEN → HALF_OPEN
- Failed prices go to an in-memory Dead Letter Queue for later retry

### Region-Based Configuration
- Properties-driven (`ingestion.region.*`) — no external config service
- Immutable at runtime — requires restart to change region
- Scheduler reads region config at startup via `@PostConstruct`

### ID Generation Strategy
- Deterministic: same input always produces same ID (SHA-256 hex)
- Hierarchy path is used as input for hierarchy entities
- Part number is used as input for Part entities
- Prevents duplicates across ingestion runs without needing existence checks



## Tech Stack & Dependencies


# Parts Catalogue Ingestion Service — Tech Stack & Conventions

## Tech Stack

| Category | Technology | Version | Notes |
|----------|-----------|---------|-------|
| Language | Java | 21 | Virtual threads, pattern matching, records, sealed classes |
| Framework | Spring Boot | 3.5.11 | Web, Actuator, Validation, Configuration Processor |
| Build | Maven | 3.x | Spring Boot parent POM, Lombok annotation processor |
| Graph DB | Nebula Graph | 3.8.4 (client) | Native Java client with connection pooling |
| Search | OpenSearch | 3.7.0 (client) | opensearch-java + opensearch-rest-client |
| Resilience | Resilience4j | via Spring Cloud 3.3.1 | Circuit breakers + retry with exponential backoff |
| API Docs | Springdoc OpenAPI | 2.8.14 | Swagger UI at /swagger-ui.html |
| HTTP Client | Spring RestClient | (Boot managed) | Replaces RestTemplate; per-API bean instances |
| JSON | Jackson | 2.21.1 | jackson-datatype-jsr310 for Java time types |
| Boilerplate | Lombok | 1.18.42 | @Data, @SuperBuilder, @RequiredArgsConstructor, @Slf4j |
| Metrics | Micrometer | (Boot managed) | Counters, Timers; exposed via /actuator/prometheus |
| Testing | JUnit 5 + Mockito + Awaitility | (Boot managed) | No integration test containers |
| Container | Docker | Multi-stage | Maven build → Eclipse Temurin 25 JRE |
| CI/CD | Azure DevOps Pipelines | — | SonarQube PR checks, UAT, Prod pipelines |

## Coding Conventions

### Class Structure
- **Entities**: Use `@SuperBuilder` + `@Data` + `@NoArgsConstructor` + `@AllArgsConstructor` + `@EqualsAndHashCode(callSuper = true)`
- **Services**: Use `@RequiredArgsConstructor` for constructor injection (no `@Autowired`)
- **Config**: Use `@ConfigurationProperties` with prefix binding, validated via Spring Validation
- **Controllers**: Use `@RestController` + `@RequestMapping` with record-based response types
- **Utilities**: Private constructor, static methods only, `final` class where possible
- **Constants**: Dedicated `NebulaGraphConstants` class with `public static final` fields

### Naming Conventions
- Packages: `org.com.graph.<layer>` (config, controller, service, repository, model, dto, exception, util, scheduler, event, constants)
- Service beans: Named by datasource (e.g., `@Service(value = "norton")`)
- Config properties: Kebab-case in properties files, camelCase in Java (Spring binding)
- RestClient beans: Named by purpose (e.g., `nortonRestClient`, `tvsRestClient`, `priceRestClient`)
- Executor beans: Named with `@Qualifier` (e.g., `"ingestionExecutor"`)

### Java 21 Features Used
- **Virtual threads**: `Executors.newVirtualThreadPerTaskExecutor()`, `Thread.ofVirtual().name(...).start(...)`
- **Records**: `TriggerResponse`, `HealthResponse`, `IngestionResult`, `ChunkResult`, `IngestionExecution`, `IngestionStatus`
- **Pattern matching switch**: `switch (entity) { case Model model -> ... }` in repositories and transformation
- **Sealed/enhanced switch**: `return switch (type) { case "model" -> ...; }` for type dispatch

### Dependency Injection Patterns
- Constructor injection via Lombok `@RequiredArgsConstructor` (preferred)
- `@Qualifier` for disambiguating multiple beans of same type (circuit breakers, retry, rest clients)
- `@Value` for simple scalar config values in services
- `@Bean` methods in `@Configuration` classes for infrastructure beans
- `Map<String, IngestionService>` auto-wired by Spring (bean name → instance)

### Logging
- SLF4J via Lombok `@Slf4j`
- Pattern: `%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n`
- DEBUG for individual operations, INFO for batch summaries, WARN for skipped items, ERROR for failures
- Query truncation at 200 chars for log safety

## Patterns

### Resilience Pattern (Circuit Breaker + Retry)
```java
Retry.decorateSupplier(retry,
    CircuitBreaker.decorateSupplier(circuitBreaker,
        () -> executeRequest(url)
    )
).get();
```
- Retry wraps circuit breaker (retry is outer, CB is inner)
- Three independent instances: `catalogueApi`, `nebulaGraph`, `openSearch`
- Exponential backoff: initial 2s, multiplier 2.0, max 3 attempts
- Circuit breaker: sliding window 10, failure threshold 50%, wait 30s in open state

### Chunked Parallel Ingestion Pattern
Used by `PriceIngestionService` and `WarrantyIngestionService`:
1. Partition data into chunks (default 50 items)
2. Submit each chunk as `CompletableFuture.supplyAsync(..., ingestionExecutor)`
3. Within each chunk, persist to Graph and Search in parallel
4. Retry failed chunks up to 3 times
5. Failed records go to Dead Letter Queue
6. Merge all chunk results into final `IngestionResult`

### Entity Persistence Pattern
```java
// Upsert vertex (idempotent)
catalogueGraphRepository.upsertPart(part);
// Create edge (IF NOT EXISTS)
persistenceService.createRelationship(parentId, parentType, childId, childType);
```
- Always UPSERT for vertices (safe for re-runs)
- INSERT IF NOT EXISTS for edges
- Batch operations use `executeBatch(String... queries)` with chunking

### Deduplication via In-Memory Cache
```java
Part existingPart = partCache.get(partId);
if (existingPart != null) {
    // Just add new relationship edge
    existingPart.addAssemblyId(assemblyId);
    persistenceService.persistPart(existingPart, assemblyId);
} else {
    // Transform, persist, cache
    Part part = transformationService.transform(node);
    partCache.put(part.getId(), part);
}
```

### Buffered Search Indexing
- `BlockingQueue<Part>` with capacity 1000
- Non-blocking `offer()` with 100ms timeout
- Flush when buffer reaches `opensearch.bulk-size` (default 100)
- Final flush after hierarchy traversal completes

## Error Handling

### Exception Hierarchy
```
RuntimeException
├── ApiException          — HTTP errors from external APIs
│   └── isRetryable()    — true for 5xx and timeouts, false for 4xx
├── GraphException        — Nebula Graph query failures
│   └── isRetryable()    — true for connection errors, false for syntax errors
├── IngestionException    — Workflow-level failures
│   ├── phase            — FETCH, TRANSFORM, VALIDATE, PERSIST, LINK, COMPLETE
│   ├── entityType/Id    — context about what failed
│   └── isRetryable()    — true for FETCH/PERSIST phases
└── SearchException       — OpenSearch operation failures
    └── isRetryable()    — true for IOExceptions and connection errors
```

### Error Isolation Strategy
- Individual entity failures don't stop the ingestion run
- Errors are counted (`errorsEncountered.incrementAndGet()`) and logged
- Chunk-level failures are isolated — other chunks continue
- Circuit breakers prevent cascading failures to downstream systems
- Dead Letter Queue captures failed records for later retry

### HTTP Error Responses
- `202 ACCEPTED` — ingestion triggered successfully
- `400 BAD REQUEST` — no datasources configured
- `409 CONFLICT` — ingestion already running (lock held)
- `500 INTERNAL SERVER ERROR` — unexpected failure during trigger

## Testing

### Framework
- **JUnit 5** with Spring Boot Test (`@SpringBootTest`, `@WebMvcTest`)
- **Mockito** for mocking dependencies (`@Mock`, `@InjectMocks`, `@MockBean`)
- **Awaitility** for testing async operations with timeouts
- **No test containers** — all external dependencies are mocked

### Test Organization
- Mirrors main source structure (same package names)
- One test class per production class
- Test class naming: `<ClassName>Test.java`

### What to Test
- Config classes: Bean creation, property binding, validation
- Controllers: HTTP status codes, request/response mapping, error cases
- Services: Business logic, orchestration flow, error handling paths
- Repositories: Query construction, response parsing (mocked clients)
- Utilities: Pure function behavior, edge cases, null handling
- Exceptions: Constructor variants, `isRetryable()` logic, `toString()`

### Test Conventions
- Use `@ExtendWith(MockitoExtension.class)` for unit tests
- Use `@WebMvcTest` for controller slice tests
- Verify interactions with `verify(mock, times(n))`
- Assert exceptions with `assertThrows()`
- Use `@BeforeEach` for common setup

## Deployment

### Docker
- Multi-stage build: Maven 3.9 + Corretto 25 (build) → Temurin 25 JRE (runtime)
- Exposed port: 2001
- JVM flags: `-XX:+UnlockExperimentalVMOptions -XX:+UseContainerSupport`
- Dependencies cached via `mvn dependency:go-offline` layer

### Environment Variables (Required)
| Variable | Purpose |
|----------|---------|
| `EXPOSED_PORT` | Server port (default 2001) |
| `NEBULA_HOSTS` | Comma-separated Nebula Graph hosts |
| `NEBULA_PORT` | Nebula Graph port |
| `NEBULA_SPACE` | Graph space name |
| `NEBULA_USERNAME` / `NEBULA_PASSWORD` | Nebula credentials |
| `OPENSEARCH_HOST` / `OPENSEARCH_PORT` | OpenSearch connection |
| `OPENSEARCH_USERNAME` / `OPENSEARCH_PASSWORD` | OpenSearch credentials |
| `OPENSEARCH_PARTS_INDEX` | Parts index name |
| `OPENSEARCH_PRICES_INDEX` | Prices index name |
| `OPENSEARCH_WARRANTIES_INDEX` | Warranties index name |
| `OPENSEARCH_HIERARCHIES_INDEX` | Hierarchies index name |
| `ACD_TVS_URL` / `ACD_TVS_ENDPOINT` / `ACD_TVS_API_KEY` | TVS API config |
| `ACD_NORTON_URL` / `ACD_NORTON_ENDPOINT` / `ACD_NORTON_API_KEY` | Norton API config |
| `PRICE_API_URL` / `PRICE_API_ENDPOINT` / `PRICE_API_KEY` | Price API config |
| `INGESTION_REGION` | Active region (default: IND) |
| `AZURE_ACCOUNT` / `AZURE_ACCOUNT_KEY` / `AZURE_ACCOUNT_URL` | Azure Blob Storage |

### CI/CD (Azure DevOps)
- **CI pipeline**: Triggered by SonarQube PR pipeline completion on `main`
- **CD pipeline**: Separate YAML for UAT and Prod deployments
- **Image scanning**: Dedicated pipeline for container security
- Template-based: Extends from shared `Devops_ISSM_pipelines` repo

### Profiles
- **default** (production): Port 2001, scheduler enabled, full thread pools
- **dev**: Port 8080, scheduler disabled, reduced pool sizes, verbose logging

### Health & Monitoring
- `/actuator/health` — overall health with circuit breaker details
- `/actuator/metrics` — Micrometer metrics
- `/actuator/prometheus` — Prometheus-compatible metrics export
- Custom metrics: `price.ingestion.*`, `warranty.ingestion.*` (total, success, failed, duration)

## Build Commands

```bash
# Build (skip tests)
mvn clean package -DskipTests

# Build with tests
mvn clean install

# Run locally (dev profile)
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# Run tests
mvn test

# Run specific test
mvn test -Dtest=NortonIngestionServiceTest

# Generate test coverage
mvn clean test jacoco:report
```

