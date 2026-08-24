# TVS-CPS-INVENTORY


## Product Context


# TVS CPS Inventory Service — Product Context

## What This Service Does

This is the **Inventory Management microservice** for TVS Motor Company's Channel Partner System (CPS). It manages dealer-level inventory for a multi-tenant network of vehicle dealerships, tracking vehicles (two-wheelers), spare parts, accessories, and merchandise through their full lifecycle — from goods receipt to customer sale.

## Domain Entities

### Vehicle
The core asset tracked by the system. Represents a physical two-wheeler identified by VIN and engine number, linked to a product catalog entry.
- Fields: vehicleId (UUID), productCatalogId, vin (unique), engineNumber (unique), manufactureYear, manufactureMonth, warrantyExpiryDate, additionalInfo (JSONB)

### VehicleDealerMapping
Links a Vehicle to a specific dealer (channel partner) and tracks its lifecycle state at that dealer.
- Fields: vehicleId, tenantId, entityType, entityId (dealer), stockType, status, inwardedAt, isDamaged, isPDIDone, inwardType, deliveryDate, invoiceDate, locationId, isActive, additionalInfo (JSONB)
- StockType enum: DEMO, DISPLAY, RETAIL_STOCK, ALLOCATED, STOCK
- Status values: IN_STOCK, ALLOCATED, INVOICED, SOLD

### Inventory
Generic stock record for all product categories. Tracks quantity at a specific storage location.
- Fields: tenantId, entityType, entityId, productCatalogId, productCategoryType, stockQuantity, locationId, rackId, binId, vehicleId, receiveType, unitOfMeasurement, additionalInfo (JSONB)

### InventoryAudit
Immutable audit trail for every stock movement (inward or outward).
- Fields: entityId, entityType, productCatalogId, stockQuantity, type (STOCK_IN/STOCK_OUT/PDI_COMPLETED), locationId, rackId, binId, additionalInfo (JSONB)

### Location / Rack / Bin
Three-level warehouse hierarchy for physical storage management. Each level has name, code, isDefault flag, and parent reference.

## Product Categories

| Category | Description |
|----------|-------------|
| VEHICLE | Two-wheelers (tracked individually by VIN) |
| PARTS | Spare parts (tracked by quantity) |
| ACCESSORIES | Vehicle accessories (tracked by quantity) |
| MERCHANDISE | Branded merchandise (tracked by quantity) |

## Inward Types (how stock enters the system)

| Type | Description |
|------|-------------|
| GRN | Goods Receipt Note — standard vehicle receipt from factory |
| WARRANTY_REGISTRATION | Vehicle received for warranty registration |
| SERVICE | Vehicle received for service |
| DEALLOCATE | Return a previously allocated vehicle back to stock |

## Issue Types (how stock leaves the system)

| Type | Description |
|------|-------------|
| CUSTOMER_SALE | Vehicle sold to end customer |
| ALLOCATE | Vehicle allocated to a booking |
| WR_ALLOCATE | Warranty registration allocation |
| JOB_CARD | Parts issued against a service job card |

## Receive Types (for parts/accessories)

| Type | Description |
|------|-------------|
| JOB_CARD_RETURN | Parts returned from a service job card |

## Business Rules

### Stock Type Transitions
- **DEMO** — terminal state, cannot be changed
- **DISPLAY** → can change to DEMO or STOCK only
- **STOCK** → can change to DISPLAY or DEMO only

### Allocation Constraints
- Vehicles with stockType DEMO or DISPLAY **cannot** be allocated
- Allocation requires a valid vehicleId and VEHICLE product category

### Issue Constraints
- JOB_CARD issue type is **invalid** for VEHICLE product category (parts only)
- CUSTOMER_SALE for vehicles requires a VIN
- Stock decrement is atomic — fails if insufficient stock

### PDI (Pre-Delivery Inspection)
- Can only be completed once per vehicle (isPDIDone flag)
- Creates an audit record of type PDI_COMPLETED
- Records checklist and comments in additionalInfo

### Warranty Expiry
- Auto-calculated when delivery date is set: deliveryDate + warranty duration (months from additionalInfo)

### Auto-Creation of Storage Hierarchy
- When receiving inventory, if Location/Rack/Bin don't exist or are invalid, the system auto-creates default ones for the dealer

### Data Isolation
- All queries are scoped by tenantId + entityType + entityId
- External API endpoints filter additionalInfo to expose only safe keys (vin, color, model, etc.) when the requester is not the owning dealer

## Integrations

### Internal (from tvsm-be-core)
- **TenantContext** — provides tenantId, currentUser, channelPartnerType, channelPartnerId from JWT
- **Validation Framework** — config-driven request validation via `@ConfigValidated`
- **Logging/Performance** — AOP-based method logging via `@Loggable`
- **Report Models** — shared VehicleStockModel and ReportRequest for cross-service reporting

### External
- **Azure Blob Storage** — file storage (configured but usage is minimal in this service)
- **Product Catalog Service** — referenced by productCatalogId (external system of record for product details)

## Analytics KPIs (Dashboard)

| Indicator | Description |
|-----------|-------------|
| AVAILABLE_STOCK | Total stock quantity per dealer per product catalog |
| STOCK_90_DAYS | Count of vehicles in stock for more than 90 days |
| RETAIL_COUNT | Count of invoiced vehicles per dealer |
| VEHICLES_PENDING_PDI | Vehicles with GRN inward, in STOCK status, PDI not done |
| AVERAGE_STOCK_DAYS | Average days vehicles have been in stock, grouped by dealer and product |



## Code Structure


# TVS CPS Inventory Service — Project Structure

## Directory Layout

```
TVS-CPS-INVENTORY/
├── .kiro/steering/              # Kiro steering files (project context)
├── src/
│   ├── main/
│   │   ├── java/com/tvsm/inventory/
│   │   │   ├── TVSCPSInventoryApplication.java   # Spring Boot entry point
│   │   │   ├── analytics/                         # Strategy pattern for dashboard KPIs
│   │   │   │   ├── AnalyticsStrategy.java         # Strategy interface
│   │   │   │   ├── AnalyticsStrategyFactory.java  # Factory dispatches by indicator key
│   │   │   │   ├── AvailableStockStrategy.java
│   │   │   │   ├── AverageStockDaysStrategy.java
│   │   │   │   ├── RetailCountStrategy.java
│   │   │   │   ├── Stock90DaysStrategy.java
│   │   │   │   └── VehiclesPendingPDIStrategy.java
│   │   │   ├── config/                            # Spring configuration beans
│   │   │   │   ├── Config.java                    # RestTemplate bean
│   │   │   │   └── CorsConfig.java                # CORS (allow all origins)
│   │   │   ├── constants/                         # Enums and static constants
│   │   │   │   ├── AnalyticsKeyIndicator.java     # KPI enum
│   │   │   │   ├── ApiConstants.java              # URL paths and success codes
│   │   │   │   ├── InwardType.java                # GRN, WARRANTY_REGISTRATION, SERVICE, DEALLOCATE
│   │   │   │   ├── IssueType.java                 # CUSTOMER_SALE, ALLOCATE, WR_ALLOCATE, JOB_CARD
│   │   │   │   ├── ProductCategoryType.java       # PARTS, VEHICLE, MERCHANDISE, ACCESSORIES
│   │   │   │   └── ReceiveType.java               # JOB_CARD_RETURN
│   │   │   ├── controller/                        # REST API layer (9 controllers)
│   │   │   │   ├── BinController.java
│   │   │   │   ├── ExternalVehicleController.java # Unauthenticated vehicle lookup
│   │   │   │   ├── HealthController.java
│   │   │   │   ├── InventoryController.java       # Core CRUD: receive, issue, search
│   │   │   │   ├── InventoryDashboardController.java  # Analytics endpoints (system prefix)
│   │   │   │   ├── LocationController.java
│   │   │   │   ├── RackController.java
│   │   │   │   ├── VehicleController.java         # Vehicle lifecycle operations
│   │   │   │   └── VehicleReportController.java   # Reporting endpoints
│   │   │   ├── dto/                               # Request/Response data transfer objects
│   │   │   │   ├── *RequestDto.java               # Inbound payloads
│   │   │   │   ├── *ResponseDto.java              # Outbound payloads
│   │   │   │   ├── PaginatedResponse.java         # Generic paginated wrapper
│   │   │   │   ├── SearchRequestDto.java          # Dynamic filter/sort search model
│   │   │   │   └── InventoryAuditEntityType.java  # Audit entity type enum
│   │   │   ├── entity/                            # JPA entities (7 entities)
│   │   │   │   ├── Bin.java
│   │   │   │   ├── Inventory.java
│   │   │   │   ├── InventoryAudit.java
│   │   │   │   ├── Location.java
│   │   │   │   ├── Rack.java
│   │   │   │   ├── Vehicle.java
│   │   │   │   └── VehicleDealerMapping.java
│   │   │   ├── exception/                         # Error response model
│   │   │   ├── mapper/                            # MapStruct mappers (6 mappers)
│   │   │   │   ├── BinMapper.java
│   │   │   │   ├── InventoryAuditMapper.java
│   │   │   │   ├── LocationMapper.java
│   │   │   │   ├── RackMapper.java
│   │   │   │   ├── VehicleDealerMappingMapper.java
│   │   │   │   └── VehicleMapper.java
│   │   │   ├── repository/                        # Spring Data JPA repositories (7 repos)
│   │   │   │   ├── BinRepository.java
│   │   │   │   ├── InventoryAuditRepository.java
│   │   │   │   ├── InventoryRepository.java       # Complex native queries for stock ops
│   │   │   │   ├── LocationRepository.java
│   │   │   │   ├── RackRepository.java
│   │   │   │   ├── VehicleDealerMappingRepository.java  # Analytics queries
│   │   │   │   └── VehicleRepository.java
│   │   │   ├── service/                           # Business logic (13 services)
│   │   │   │   ├── AvailableStockService.java
│   │   │   │   ├── AverageStockDaysService.java
│   │   │   │   ├── BinService.java
│   │   │   │   ├── InventoryAuditService.java
│   │   │   │   ├── InventoryService.java          # Core: receive, issue, search
│   │   │   │   ├── LocationService.java
│   │   │   │   ├── ProductCatalogService.java     # Product catalog count aggregation
│   │   │   │   ├── RackService.java
│   │   │   │   ├── RetailCountService.java
│   │   │   │   ├── Stock90DaysService.java
│   │   │   │   ├── VehicleReportService.java
│   │   │   │   ├── VehicleService.java            # Vehicle lifecycle, PDI, stock type
│   │   │   │   └── VehiclesPendingPDIService.java
│   │   │   └── util/                              # Utility classes
│   │   │       ├── AnalyticsMappingUtils.java
│   │   │       ├── ApiPassthroughUtil.java
│   │   │       └── TenantContextUtil.java         # Tenant context extraction helpers
│   │   └── resources/
│   │       └── application.yml                    # Spring Boot configuration
│   └── test/java/com/tvsm/inventory/             # Unit tests (mirrors main structure)
│       ├── analytics/                             # Strategy tests
│       ├── config/                                # Config tests
│       ├── constants/                             # Enum tests
│       ├── controller/                            # Controller tests (all 9)
│       ├── dto/                                   # DTO tests
│       ├── mapper/                                # Mapper tests (all 6)
│       ├── service/                               # Service tests (all services)
│       └── util/                                  # Utility tests + TestDataBuilder
├── pom.xml                                        # Maven build (parent: tvsm-be-starter-parent)
├── Dockerfile                                     # Multi-stage build (builder + Corretto 21)
├── ci-pipeline.yaml                               # Azure DevOps CI pipeline
├── cd-pipeline.yaml                               # Azure DevOps CD pipeline (Helm deploy)
├── AST_cps_inventory_prod_Pipeline.yml            # Production pipeline
├── AST_cps_inventory_uat_Pipeline.yml             # UAT pipeline
├── ast-image-scan.yaml                            # Container image security scan
└── sonar_ci.yml                                   # SonarQube quality gate

```

## Module Dependencies

### External Dependencies (from parent POM)
- `spring-boot-starter-web` — REST API framework
- `spring-boot-starter-data-jpa` — ORM and repository layer
- `spring-boot-starter-validation` — Bean validation
- `spring-boot-starter-actuator` — Health/metrics endpoints
- `postgresql` — Database driver
- `lombok` — Boilerplate reduction
- `mapstruct` + `mapstruct-processor` — Object mapping
- `springdoc-openapi-starter-webmvc-ui` — Swagger/OpenAPI docs
- `spring-boot-starter-test` + `junit-jupiter` + `mockito-core` — Testing

### Internal Dependency
- **`tvsm-be-core:1.0.0-SNAPSHOT`** — Shared company framework providing:
  - `BaseController` — standardized `APIResponse` wrapping (`success()`, `error()`)
  - `TenantContext` — thread-local multi-tenant context (tenantId, currentUser, dealerId, channelPartnerType)
  - `APIException` — standardized exception with status code and parameter context
  - `@Loggable` — AOP method-level logging and performance tracking
  - `@ConfigValidated` — config-driven request validation (rules in external files)
  - `JsonUtil`, `StringUtil` — shared utilities
  - `VehicleStockModel`, `ReportRequest` — shared report DTOs
  - `ParamDTO` — error context parameters

## Architectural Decisions

### Layered Architecture
Standard Controller → Service → Repository layering. Controllers are thin (delegate immediately to services). Services contain all business logic and transaction management.

### Strategy Pattern for Analytics
Dashboard KPIs use a Strategy pattern: each indicator has its own `AnalyticsStrategy` implementation. The `AnalyticsStrategyFactory` auto-discovers all strategies via Spring DI and dispatches by indicator key string. Adding a new KPI requires only a new strategy class — no factory changes needed.

### Multi-Tenancy via Context
Tenant isolation is enforced at the query level, not the database level. Every repository query includes `tenantId`, `entityType`, and `entityId` parameters extracted from `TenantContext` (populated from JWT by the core framework).

### Dual Vehicle Tracking
Vehicles are tracked in two ways simultaneously:
1. **Inventory table** — quantity-based (like parts), for stock count aggregation
2. **VehicleDealerMapping table** — individual vehicle lifecycle tracking (status, PDI, dates)

This allows the same analytics/reporting infrastructure to work across all product categories while preserving vehicle-specific lifecycle data.

### Atomic Stock Operations
Stock increment/decrement uses `@Modifying` JPQL queries with WHERE clauses (e.g., `WHERE stockQuantity >= :quantity`) to prevent race conditions without pessimistic locking.

### Auto-Provisioning Storage Hierarchy
The system auto-creates default Location → Rack → Bin hierarchy when receiving inventory if the dealer doesn't have one. This reduces onboarding friction for new dealers.

### External vs Internal APIs
- Internal APIs (`/api/v1/...`) require JWT authentication and use tenant context
- External APIs (`/api/v1/external/...`) are excluded from JWT validation and filter sensitive data from responses
- System APIs (`/system/...`) are also excluded from JWT — used for internal service-to-service calls (analytics dashboard)

### Config-Driven Validation
Request validation rules are externalized in config files (`bin-validation`, `rack-validation`, etc.) rather than hardcoded annotations. The `@ConfigValidated` aspect loads rules at runtime, allowing validation changes without code deployment.



## Tech Stack & Dependencies


# TVS CPS Inventory Service — Tech Stack & Conventions

## Tech Stack

| Layer | Technology | Version/Notes |
|-------|-----------|---------------|
| Language | Java | 21 (Amazon Corretto runtime) |
| Framework | Spring Boot | Via parent POM `tvsm-be-starter-parent:1.0.0` |
| Web | Spring MVC | REST controllers with `@RestController` |
| ORM | Spring Data JPA + Hibernate | PostgreSQL dialect, DDL managed externally |
| Database | PostgreSQL | With JSONB columns for flexible metadata |
| Mapping | MapStruct | Component model "spring", with Lombok binding |
| Boilerplate | Lombok | `@Data`, `@Builder`, `@RequiredArgsConstructor` |
| API Docs | SpringDoc OpenAPI | Swagger UI at `/swagger-ui.html` |
| Validation | Spring Validation + Custom | `@ConfigValidated` for config-driven rules |
| Testing | JUnit 5 + Mockito | JaCoCo for coverage |
| Build | Maven | Surefire 3.2.2, JaCoCo plugin |
| Container | Docker | Multi-stage: Maven builder → Corretto 21 headless |
| CI/CD | Azure DevOps | YAML pipelines, Helm chart deployment |
| Registry | Azure Container Registry | `tvsmazcmnsvcacrdev01.azurecr.io` |
| Storage | Azure Blob Storage | Container: `cpsfiles` |
| Quality | SonarQube | Integrated quality gate pipeline |

## Coding Conventions

### Dependency Injection
- Always use **constructor injection** via `@RequiredArgsConstructor` (Lombok)
- Never use `@Autowired` on fields
- Services and repositories are declared as `private final` fields

### Entity Conventions
- `@Data @Entity @DynamicUpdate @Builder @NoArgsConstructor @AllArgsConstructor`
- UUID primary keys with `@GeneratedValue`
- `Instant` for all timestamp fields (createdAt, updatedAt, inwardedAt, etc.)
- JSONB columns use `@JdbcTypeCode(SqlTypes.JSON)` with `JsonNode` type
- Table names are snake_case, matching entity class names

### DTO Conventions
- `@Data @NoArgsConstructor @AllArgsConstructor`
- `@JsonProperty` annotations on all fields for explicit JSON mapping
- Request DTOs suffixed with `RequestDto`, response with `ResponseDto`
- Builder pattern (`@Builder`) on response DTOs where construction is complex

### Controller Conventions
- Extend `BaseController` from `tvsm-be-core`
- Annotate with `@Loggable` for AOP logging
- Use `@Tag` for Swagger grouping
- Use `@Operation` and `@ApiResponses` for endpoint documentation
- Return `ResponseEntity<APIResponse<T>>` using `success()` helper
- Request validation via `@ConfigValidated` annotation on `@RequestBody`
- URL constants defined in `ApiConstants` class — never hardcode paths

### Service Conventions
- Annotate with `@Service @RequiredArgsConstructor @Slf4j`
- `@Transactional` on methods that modify data
- `@Loggable` on service classes for performance tracking
- Extract tenant context at the start of each method:
  ```java
  String entityType = TenantContextUtil.getCurrentChannelPartnerType();
  String entityId = TenantContextUtil.getCurrentChannelPartnerId();
  String tenantId = TenantContext.getTenantId();
  ```

### Repository Conventions
- Extend `JpaRepository<Entity, UUID>` and optionally `JpaSpecificationExecutor`
- Use JPQL for simple queries, native SQL for complex joins or PostgreSQL-specific features
- `@Modifying` + `@Query` for atomic update operations
- Method naming follows Spring Data conventions where possible

### Mapper Conventions
- MapStruct interfaces with `@Mapper(componentModel = "spring")`
- One mapper per entity (VehicleMapper, LocationMapper, etc.)
- Custom mapping logic in default methods when needed

### Naming Conventions
- Packages: `com.tvsm.inventory.<layer>`
- Classes: PascalCase (e.g., `VehicleDealerMapping`, `InventoryService`)
- Constants: UPPER_SNAKE_CASE as `public static final String`
- API paths: kebab-case (e.g., `/delivery-date/add`, `/vehicle-stock-report-list`)
- Database columns: snake_case
- JSON fields: camelCase

## Patterns

### Strategy Pattern (Analytics)
```java
// Interface
public interface AnalyticsStrategy {
    String getIndicator();
    Map<String, Number> getAnalytics(InventoryAnalyticsRequestDto request);
}

// Factory auto-discovers via Spring DI
@Component
public class AnalyticsStrategyFactory {
    public AnalyticsStrategyFactory(List<AnalyticsStrategy> strategies) { ... }
    public AnalyticsStrategy getStrategy(String indicatorKey) { ... }
}
```
To add a new KPI: create a new class implementing `AnalyticsStrategy`, annotate with `@Component`. The factory picks it up automatically.

### Standardized API Response
All endpoints return:
```java
return success(data, APIResponse.Status.SUCCESS, "Human message", "MACHINE_CODE");
```
Machine codes are defined in `ApiConstants` (e.g., `SUCCESS_INVENTORY_RETRIEVED`).

### Search/Filter Pattern
The `SearchRequestDto` provides a generic filter model:
```json
{
  "and": [{"field": "status", "operation": "IN", "value": ["IN_STOCK"]}],
  "or": [],
  "page": 1,
  "limit": 20,
  "sort": [{"field": "createdAt", "sortOrder": "DESC", "priority": 1}]
}
```
Services extract filter values via `request.getAndFilterValue("fieldName")`.

### Pagination
Uses `PaginatedResponse<T>` wrapper with `totalRecords`, `currentPage`, `pageLimit`, `content`. Pages are 1-indexed in the API but converted to 0-indexed for Spring Data internally.

### Audit Trail
Every stock movement creates an `InventoryAudit` record with:
- Entity reference (inventoryId or vehicleId)
- Entity type (PARTS_INVENTORY, VEHICLE_INVENTORY, MERCHANDISE_INVENTORY, ACCESSORY_INVENTORY)
- Type: STOCK_IN, STOCK_OUT, or PDI_COMPLETED
- Additional context merged into JSONB additionalInfo

## Error Handling

### Exception Strategy
- Throw `APIException` from `tvsm-be-core` with:
  - Human-readable message
  - Status code string (e.g., `BAD_REQUEST`, `INTERNAL_ERROR`)
  - Optional `ParamDTO` for context (productCatalogId, vin, vehicleId, etc.)
  - Machine-readable error code (e.g., `API_ERROR_BAD_REQUEST`)

### Common Pattern
```java
throw new APIException(
    "Inventory not found for SKU: " + productCatalogId,
    APIResponse.StatusCode.BAD_REQUEST.name(),
    null,
    BaseConstants.API_ERROR + APIResponse.StatusCode.BAD_REQUEST.name(),
    ParamDTO.builder().productCatalogId(productCatalogId).build()
);
```

### Service-Level Try-Catch
Complex operations wrap in try-catch and re-throw as `APIException` with `INTERNAL_ERROR`:
```java
try {
    // business logic
} catch (Exception e) {
    log.error("Error processing: ", e);
    throw new APIException("Failed to process: " + e.getMessage(),
        APIResponse.StatusCode.INTERNAL_ERROR.name(), ...);
}
```

### Validation Errors
- `TenantContextUtil` throws `ValidationException` (from core) if tenant context is missing
- `@ConfigValidated` triggers validation errors before reaching service layer
- Business rule violations throw `APIException` with `BAD_REQUEST`

## Testing

### Framework
- JUnit 5 (`@Test`, `@ExtendWith(MockitoExtension.class)`)
- Mockito for mocking dependencies (`@Mock`, `@InjectMocks`)
- No integration tests or testcontainers — pure unit tests

### Structure
Tests mirror the main source structure exactly:
- `controller/` — test each endpoint with mocked services
- `service/` — test business logic with mocked repositories
- `mapper/` — test MapStruct mapping correctness
- `analytics/` — test each strategy independently
- `util/` — test utility methods

### Test Data
- `TestDataBuilder` utility class provides factory methods for creating test fixtures
- Located at `src/test/java/com/tvsm/inventory/util/TestDataBuilder.java`

### Running Tests
```bash
mvn test                    # Run all tests
mvn test -pl .              # Run tests for this module only
mvn verify                  # Run tests + JaCoCo coverage report
```

### Coverage
- JaCoCo plugin generates coverage reports during `test` phase
- Reports available at `target/site/jacoco/index.html`

## Deployment

### Docker Build
Multi-stage Dockerfile:
1. **Builder stage**: Uses custom base image (`tvs-cps-be-base-framework`) with pre-installed Maven dependencies. Runs `mvn clean install -DskipTests`.
2. **Runtime stage**: `amazoncorretto:21-al2023-headless` with JVM tuning: `-Xms256m -Xmx384m -XX:+UseContainerSupport`

### CI Pipeline
- Triggered by SonarQube pipeline completion on `main` branch
- Uses shared build template from `TVSM-DMS/Devops_ISSM_pipelines` repo
- Produces Docker image tagged with build ID

### CD Pipeline
- Triggered automatically by CI pipeline completion
- Deploys via Helm chart (`norton-cps-inventory`) to Kubernetes
- Current active environment: `dev-cp` namespace
- UAT and prod stages defined but commented out (manual approval gates)

### Environment Configuration
Secrets injected via environment variables:
- `INV_JWT_PUBLIC_KEY_1` — JWT validation key
- `INV_DB_USERNAME` / `INV_DB_PASSWORD` — Database credentials
- `INV_AZURE_STORAGE_CONNECTION_STRING` — Azure Blob Storage

### Server Configuration
- Port: 8099
- Context path: `/`
- Actuator endpoints exposed: health, info, metrics
- Hibernate DDL: `none` (schema managed by migrations external to this service)

## Build Commands

```bash
# Local build (skip tests)
mvn clean install -DskipTests

# Full build with tests
mvn clean install

# Run locally
mvn spring-boot:run

# Docker build
docker build -t tvs-cps-inventory .
```

