# TVS-CPS-BACKEND


## Product Context


# TVS CPS Backend — Product Context

## What This Service Does

TVS Channel Partner System (CPS) Backend is the server-side platform for managing Norton Motorcycles dealership operations. It serves as the central system for dealers (channel partners) to manage their day-to-day business: ordering vehicles and parts, handling warranty claims, scheduling service appointments, tracking enquiries and bookings, and running analytics dashboards.

The system is multi-tenant — each dealer operates in an isolated data context identified by a tenant ID. OEM (Original Equipment Manufacturer) users have cross-dealer visibility for oversight and approvals.

## Domain Entities

### Orders
- **Order**: Vehicle, parts, merchandise, or accessories purchase orders placed by dealers to OEM
- **OrderLine**: Individual line items within an order (SKU, quantity, price)
- **OrderStateHistory**: Audit trail of order status transitions
- **ERPOrderInfo**: SAP ERP integration data (sales order numbers, sync status)
- **Cart**: Draft order workspace before submission (one active cart per user per category)
- **GRN (Goods Received Note)**: Delivery confirmation that triggers order status reconciliation

### Claims
- **Claim**: Warranty, transit damage, shortage, or goodwill claims submitted by dealers
- **ClaimCatalogMapping**: Links claims to specific catalog items (parts/labour)
- **ClaimTimeline**: Approval/rejection history per claim line
- **BulkUpload**: Batch processing of claim approvals via Excel

### Appointments
- **Appointment**: Service scheduling for customer vehicles
- **AppointmentFollowUp**: Follow-up tracking with auto-close after configurable days
- **AppointmentEvent**: Published to Azure Event Hubs for downstream consumers

### Workflow
- **WorkflowInstance**: Approval workflow instances (order approval, claim approval)
- **WorkflowAction**: Actions performed on workflows (approve, reject, appeal)
- **WorkflowRule**: Drools-based rules determining approval routing

### Enquiries & Bookings
- **Enquiry/Lead**: Sales pipeline entries from potential customers
- **Booking**: Vehicle reservations with status tracking (Confirmed → Allocated → Delivered)
- **TestRide**: Test ride scheduling linked to enquiries

### Announcements & Training
- **Announcement**: OEM-to-dealer communications with target audience filtering
- **AnnouncementReadLog**: Read receipt tracking
- **Training**: Training modules and completion tracking for dealer staff

### Inventory & Catalog
- **CatalogItem**: Cached product catalog (vehicles, parts, merchandise, accessories)
- **VehicleStock**: VIN-level stock tracking with age buckets and PDI status
- **StockCache**: In-memory stock availability for order validation

### Other Entities
- **NPQR**: New Product Quality Reports from dealers
- **Collateral**: Marketing materials distribution
- **Billing/Invoice**: Customer invoicing for vehicle and parts sales
- **Document**: File attachments stored in Azure Blob Storage

## Integrations

| System | Protocol | Purpose |
|--------|----------|---------|
| SAP ERP (CPI) | REST + OAuth2 | Order creation, claim submission, invoice sync |
| Azure Event Hubs | Kafka (SASL_SSL) | Appointment event publishing |
| Azure Blob Storage | SDK | Document/file storage |
| Norton MDP | REST + OAuth2 | Dealer master data sync (every 2h) |
| Norton UMS | REST | User management, role resolution |
| Norton Catalog Service | REST | Product catalog sync (every 2h) |
| Norton Customer Service | REST | Customer data lookup |
| Norton Inventory Service | REST | Stock availability |
| Norton Job Card Service | REST | Service job card management |
| Norton Lead Service | REST + OAuth2 | Enquiry/lead management |
| Norton Booking Service | REST + OAuth2 | Vehicle booking management |
| OneTrust | REST + OAuth2 | Consent management (GDPR) |
| Data Lake (Azure Functions) | REST | Analytics data push for claims, stock |
| OTP Service | REST | One-time password for customer verification |
| Notification Service | REST | Push notifications to dealers |

## Business Rules

### Order Management
- Orders go through workflow approval (configurable per tenant)
- Vehicle orders: one vehicle per order (cart splits into individual orders)
- Parts/Accessories/Merchandise: multiple lines per order
- Bulk upload via Excel with all-or-none validation
- ERP sync pushes orders to SAP; status reconciliation pulls back delivery info
- OEM stock validation prevents ordering out-of-stock items
- Order statuses: DRAFT → SUBMITTED → APPROVED/REJECTED → COMPLETED/CANCELLED

### Claims
- Warranty claims require valid VIN with active warranty period
- Appeal limit is configurable (default: 2 appeals per claim)
- Claims sync to SAP on closure with approved values
- Bulk approval via Excel upload with async processing
- Claim types: warranty, transit, shortage, goodwill

### Appointments
- Auto-close after configurable days of inactivity (default: 2 days)
- Follow-up reminders at configurable intervals (default: 45 days)
- Events published to Event Hub for downstream job card creation

### RBAC & Access Control
- 30+ roles (Dealer Owner, Sales Manager, Service Advisor, Technician, OEM roles, etc.)
- 100+ granular permissions mapped to API endpoints
- Some roles have "self-only" access (see only their own records)
- OEM roles have cross-dealer visibility
- API permission mapping enforced at request filter level

### Multi-Tenancy
- Tenant isolation via `x-tenant-id` header (extracted from JWT)
- Each tenant has independent data in shared PostgreSQL database
- Configurable per-tenant: timezone, currency, locale
- Supported tenants: UK, FR, DE, IT, ES, IN (and Test_Tenant for dev)

### Catalog & Pricing
- Catalog cached in-memory, refreshed every 2 hours from external catalog service
- Vehicle filtering by `availableForSale` flag
- Pricing: RRP, standard discount, additional discount, VAT, freight charges
- Merchandise ordered by size (XXS → 3XL)



## Code Structure


# TVS CPS Backend — Project Structure

## Architecture Overview

Monolithic multi-module Spring Boot application deployed as a single JAR. All service modules compile into `tvs-cps-app` which is the only runnable artifact. The BFF (Backend-for-Frontend) module aggregates calls to both internal modules (same JVM) and external microservices (HTTP).

```
┌─────────────────────────────────────────────────────────┐
│                    tvs-cps-app (JAR)                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │              bff-service (API Gateway)           │    │
│  │   Aggregates internal + external service calls   │    │
│  └──────────┬──────────────────────┬───────────────┘    │
│             │ direct calls         │ HTTP/WebClient      │
│  ┌──────────▼──────────┐   ┌──────▼───────────────┐    │
│  │   Internal Modules   │   │  External Services   │    │
│  │  order-service       │   │  Catalog Service     │    │
│  │  claim-service       │   │  Customer Service    │    │
│  │  appointment-service │   │  Inventory Service   │    │
│  │  workflow-service    │   │  Job Card Service    │    │
│  │  announcement-service│   │  Lead/Booking Svc    │    │
│  │  training-service    │   │  SAP ERP             │    │
│  │  collateral-service  │   │  MDP, UMS, OTP       │    │
│  │  npqr-service        │   └──────────────────────┘    │
│  └──────────┬──────────┘                                │
│             │                                           │
│  ┌──────────▼──────────┐                                │
│  │   common-service     │  Shared caches, DTOs, utils   │
│  └──────────┬──────────┘                                │
│             │                                           │
│  ┌──────────▼──────────┐                                │
│  │   tvsm-be-core       │  Framework (external JAR)     │
│  │   BaseController, APIResponse, TenantContext,        │
│  │   RBAC, Validation, Security, Cloud Storage          │
│  └─────────────────────┘                                │
└─────────────────────────────────────────────────────────┘
```

## Directory Layout

```
TVS-CPS-BACKEND/
├── pom.xml                          # Parent POM (multi-module, inherits tvsm-be-starter-parent)
├── Dockerfile                       # Multi-stage: Maven build → Amazon Corretto runtime
├── ci-pipeline.yaml                 # Azure DevOps CI (triggers on main)
├── cd-pipeline.yaml                 # Azure DevOps CD (deploy to environments)
├── uk-cd-pipeline.yaml              # UK-specific deployment pipeline
├── sonar.yaml                       # SonarQube analysis pipeline
├── AST_cps_app_uat_Pipeline.yml     # UAT security scanning pipeline
├── AST_cps_app_prod_Pipeline.yml    # Prod security scanning pipeline
├── ast-image-scan.yaml              # Container image security scan
│
├── tvs-cps-app/                     # Main application module (deployable)
│   ├── pom.xml                      # Aggregates all service modules as dependencies
│   └── src/main/
│       ├── java/.../TVSCPSBackendApplication.java  # @SpringBootApplication entry point
│       └── resources/config/
│           ├── application.yml      # All configuration (single file, env-var driven)
│           ├── roles.json           # RBAC role definitions
│           ├── permissions.json     # Granular permission codes
│           ├── permission-groups.json # Permission groupings
│           └── api-permission-mapping.json # Endpoint → permission mapping
│
├── bff-service/                     # Backend-for-Frontend (API aggregation layer)
│   └── src/main/java/com/tvsm/bff/
│       ├── auth/                    # OAuth2 token management (Azure AD, OneTrust)
│       ├── client/                  # HTTP clients for external services (WebClient)
│       ├── config/                  # BFF-specific config, exception handlers
│       ├── constants/               # Endpoint path constants per external service
│       ├── controller/              # Aggregated API endpoints (dashboard, analytics, reports)
│       ├── dto/                     # Request/response DTOs (organized by service)
│       ├── entity/                  # BFF-specific entities (user preferences, etc.)
│       ├── enums/                   # BFF enums
│       ├── exception/               # Custom exceptions (BulkUploadValidationException)
│       ├── mapper/                  # MapStruct mappers
│       ├── repository/              # JPA repositories
│       ├── scheduler/               # Cron jobs (catalog sync, dealer sync, stock sync)
│       ├── service/                 # Business logic, report generation
│       ├── strategy/                # Strategy pattern (analytics indicator calculations)
│       ├── util/                    # Utilities (API passthrough, caching, header forwarding)
│       └── validator/               # Request validators
│
├── order-service/                   # Order management domain
│   └── src/main/java/com/tvsm/order/
│       ├── config/                  # OrderStatusConfigProperties
│       ├── constants/               # ApiConstants, OrderStatus, OrderLineOperation
│       ├── controller/              # OrderController (CRUD, search, bulk upload, workflow)
│       ├── dto/                     # Order DTOs (request, response, search, pagination)
│       ├── entity/                  # Order, OrderLine, OrderStateHistory, ERPOrderInfo, Cart
│       ├── enums/                   # OrderCategory, StockType
│       ├── mapper/                  # OrderMapper (MapStruct)
│       ├── repository/              # JPA repositories with custom queries
│       ├── service/                 # OrderService, ERPService, ExcelParserService, GrnDetailService
│       └── utils/                   # ChannelPartnerUtil, WorkflowIntegrationUtil
│
├── claim-service/                   # Warranty claims domain
│   └── src/main/java/com/tvsm/claim/
│       ├── config/                  # Claim-specific configuration
│       ├── constants/               # ClaimConstants, ClaimServiceEndpoints
│       ├── controller/              # ClaimController
│       ├── dto/                     # Claim DTOs (create, update, response, dashboard, bulk)
│       ├── entity/                  # Claim, ClaimCatalogMapping, BulkUpload entities
│       ├── enums/                   # ClaimStatus, ClaimType
│       ├── mapper/                  # ClaimMapper
│       ├── repository/              # Claim repositories
│       └── service/                 # ClaimService, ClaimCatalogService, ClaimBulkUploadService
│
├── workflow-service/                # Approval workflow engine
│   └── src/main/java/com/tvsm/workflow/
│       ├── constants/               # ApiConstants
│       ├── controller/              # WorkflowController (init, action, items, status)
│       ├── dto/                     # WorkflowInitRequest, WorkflowActionRequest, WorkflowResponse
│       ├── entity/                  # WorkflowInstance, WorkflowAction
│       ├── repository/              # Workflow repositories
│       └── service/                 # WorkflowService (Drools rules integration)
│
├── appointment-service/             # Service appointment scheduling
│   └── src/main/java/com/tvsm/appointment/
│       ├── controller/              # AppointmentController
│       ├── dto/                     # Appointment DTOs
│       ├── entity/                  # Appointment, AppointmentFollowUp
│       ├── repository/              # Appointment repositories
│       └── service/                 # AppointmentService (Event Hub publishing)
│
├── announcement-service/            # OEM-to-dealer communications
│   └── src/main/java/com/tvsm/announcement/
│       ├── constants/               # AnnouncementConstants
│       ├── controller/              # AnnouncementController
│       ├── dto/                     # Announcement DTOs
│       ├── entity/                  # Announcement, AnnouncementMedia, AnnouncementTarget
│       ├── mapper/                  # AnnouncementMapper, MediaMapper
│       ├── repository/              # Announcement repositories
│       ├── service/                 # AnnouncementService, MediaService
│       └── util/                    # JSON converters (ActionButton, ExternalLinks)
│
├── training-service/                # Dealer staff training modules
├── collateral-service/              # Marketing materials management
├── npqr-service/                    # New Product Quality Reports
│
└── common-service/                  # Shared module (no controllers)
    └── src/main/java/com/tvsm/common/
        ├── config/                  # BrandConfig
        ├── dto/                     # CatalogItemDto, VehicleVariantDto, MerchandiseCatalogItemDto
        ├── service/                 # CatalogCacheService, StockCacheService
        └── util/                    # CacheUtils
```

## Module Dependencies

```
tvs-cps-app
├── bff-service → order-service, common-service, tvsm-be-core
├── order-service → common-service, tvsm-be-core
├── claim-service → common-service, tvsm-be-core
├── appointment-service → tvsm-be-core
├── workflow-service → tvsm-be-core
├── announcement-service → tvsm-be-core
├── training-service → tvsm-be-core
├── collateral-service → tvsm-be-core
├── npqr-service → tvsm-be-core
└── common-service → tvsm-be-core
```

All modules depend on `tvsm-be-core` (external framework JAR providing BaseController, APIResponse, TenantContext, security filters, RBAC, validation framework, cloud storage abstraction, multi-tenant datasource, logging aspects, etc.).

## Key Architectural Decisions

1. **Single deployable JAR** — All modules compile into one artifact. Simplifies deployment but means all services scale together.

2. **BFF pattern** — The `bff-service` module acts as an API gateway for the frontend. It aggregates data from internal modules (direct method calls) and external services (WebClient HTTP calls). This keeps frontend API contracts stable while backend services evolve.

3. **Multi-tenancy via header** — Tenant isolation is achieved through `x-tenant-id` header (set from JWT claims). The `TenantContext` thread-local holds tenant/user/dealer info for the request lifecycle. Database queries filter by `tenant_id` column.

4. **In-memory catalog cache** — Product catalog is cached in `CatalogCacheService` (ConcurrentHashMap) and refreshed via cron every 2 hours. This avoids repeated HTTP calls to the external catalog service during order creation.

5. **Workflow as a service** — Approval workflows are managed by the `workflow-service` module using Drools rules. Other modules (order, claim) integrate via REST callbacks — they initiate workflows and receive status updates via webhook callbacks.

6. **External framework dependency** — `tvsm-be-core` is a shared framework across multiple TVSM applications. It provides cross-cutting concerns (security, validation, logging, error handling). Changes to core require coordinating across teams.

7. **Configuration-driven validation** — Request validation rules are defined in YAML files (e.g., `order-validation.yml`) and applied via `@ConfigValidated` annotation. This allows changing validation rules without code changes.

8. **Strategy pattern for analytics** — Dashboard/analytics calculations use the Strategy pattern to support different indicator types (KPIs, counts, aggregations) without modifying the core analytics engine.



## Tech Stack & Dependencies


# TVS CPS Backend — Technical Reference

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 21 |
| Framework | Spring Boot | Managed by `tvsm-be-starter-parent:1.0.0` |
| Build | Maven | Multi-module POM |
| Database | PostgreSQL | Via Spring Data JPA + Hibernate |
| ORM | Hibernate | `ddl-auto: none` (schema managed externally) |
| Mapping | MapStruct | `${mapstruct.version}` from parent |
| Boilerplate | Lombok | `${lombok.version}` from parent |
| HTTP Client | Spring WebClient | Reactive, non-blocking (used in BFF clients) |
| HTTP Client | RestTemplate | Legacy usage in some services |
| API Docs | SpringDoc OpenAPI | `springdoc-openapi-starter-webmvc-ui` |
| Testing | JUnit 5 + Mockito | Standard Spring Boot test stack |
| Coverage | JaCoCo | 0.8.14 |
| Messaging | Azure Event Hubs | Kafka protocol (SASL_SSL) |
| Storage | Azure Blob Storage | Via tvsm-be-core cloud-storage abstraction |
| Runtime | Amazon Corretto | 26.0.0-alpine3.22 (Docker) |
| CI/CD | Azure DevOps | YAML pipelines |
| Code Quality | SonarQube | Separate pipeline |
| Security Scan | Tenable/DAST | AST pipelines for UAT and prod |

## Coding Conventions

### Naming
- **Packages**: `com.tvsm.{module}.{layer}` (e.g., `com.tvsm.order.service`)
- **Controllers**: `{Domain}Controller` extending `BaseController`
- **Services**: `{Domain}Service` annotated with `@Service`
- **Repositories**: `{Domain}Repository` extending JpaRepository
- **DTOs**: `{Domain}{Purpose}Dto` (e.g., `OrderRequestDto`, `ClaimResponseDTO`)
  - Note: inconsistent casing exists (`Dto` vs `DTO`) — follow the module's existing convention
- **Entities**: Domain name directly (e.g., `Order`, `Claim`, `Appointment`)
- **Mappers**: `{Domain}Mapper` with `@Mapper(componentModel = "spring")`
- **Constants**: `{Domain}Constants` or `ApiConstants` with `public static final`

### Class Structure
```java
@RestController
@RequestMapping(ApiConstants.BASE_PATH)
@RequiredArgsConstructor  // Constructor injection via Lombok
@Slf4j                    // Logging
@Tag(name = "...", description = "...")  // OpenAPI
public class ExampleController extends BaseController {

    private final ExampleService exampleService;

    @PostMapping(path = ApiConstants.ENDPOINT)
    @Operation(summary = "...", description = "...")
    @ApiResponses(value = { ... })
    public ResponseEntity<APIResponse<ResponseDto>> doSomething(
            @RequestBody @ConfigValidated RequestDto request) {
        ResponseDto result = exampleService.process(request);
        return success(result, APIResponse.Status.SUCCESS, 
            Constants.MESSAGE, Constants.MESSAGE_KEY);
    }
}
```

### Dependency Injection
- Always use **constructor injection** via `@RequiredArgsConstructor`
- Never use `@Autowired` on fields (except in rare legacy cases)
- `@Value` for configuration properties on private fields

### Logging
- Use `@Slf4j` (Lombok) for logger
- Log at method entry with request context: `log.info("Creating order: {}", JsonUtil.toJson(request))`
- Log errors with exception: `log.error("Error: {}", ex.getMessage(), ex)`
- Pattern includes traceId from MDC: `%d %-5level [%X{traceId:-}] %logger{36} - %msg%n`

## Patterns

### API Response Pattern
All endpoints return `ResponseEntity<APIResponse<T>>` using the `success()` helper from `BaseController`:
```java
return success(data, APIResponse.Status.SUCCESS, "Human message", "MESSAGE_KEY");
```

Error responses follow the same structure with `APIResponse.Status.ERROR` and error arrays.

### Multi-Tenancy Pattern
```java
// Tenant context is set by security filter from JWT/headers
String tenantId = TenantContext.getTenantId();
String userId = TenantContext.getUserId();
String dealerId = TenantContext.getChannelPartnerId();
```
All database queries must filter by `tenantId` for data isolation.

### Validation Pattern
- Use `@ConfigValidated` annotation on request DTOs in controller methods
- Validation rules defined in YAML files: `src/main/resources/{module}-validation.yml`
- Standard Jakarta validation (`@Valid`, `@NotNull`, etc.) also used
- Skip validation for specific API paths configured in `request.validation.skip-api-path`

### BFF Client Pattern
```java
@Component
@RequiredArgsConstructor
public class ExternalServiceClient {
    private final AuthService authService;
    
    @Value("${bff.service.base-url}")
    private String baseUrl;

    public ResponseType callService(RequestType request) {
        String token = authService.getToken();  // OAuth2 client credentials
        return buildClient(token, null)
            .post()
            .uri("/endpoint")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(ResponseType.class)
            .block();
    }
}
```

### Workflow Integration Pattern
1. Service initiates workflow: POST to workflow-service `/init`
2. Workflow processes rules (Drools) and determines routing
3. Approver performs action: POST to workflow-service `/action`
4. Workflow calls back to originating service via configured callback URL
5. Originating service handles callback in `handleWorkflowCallback(Map<String, Object>)`

### Scheduled Jobs Pattern
```java
@Scheduled(cron = "${catalog.cron.schedule}")  // Externalized cron expression
public void syncCatalog() { ... }
```
Key schedules: catalog sync (2h), dealer sync (2h), OEM stock (1h), claim SAP sync (30min).

### Strategy Pattern (Analytics)
Used in BFF for dashboard indicator calculations. Each indicator type has a strategy implementation, selected at runtime based on the indicator key.

## Error Handling

### Exception Hierarchy (from tvsm-be-core)
- `APIException` — General API errors with status code and message key
- `ValidationException` — Request validation failures
- `NotFoundException` — Resource not found (404)

### BFF-Specific Exceptions
- `BulkUploadValidationException` — Excel upload row-level validation errors

### Error Response Format
```json
{
  "status": "ERROR",
  "statusCode": "BAD_REQUEST",
  "message": "Human-readable message",
  "messageKey": "MACHINE_KEY",
  "data": null,
  "errors": [
    {
      "field": "fieldName",
      "errorCode": "ERROR_CODE",
      "messageKey": "Detailed message",
      "params": null
    }
  ]
}
```

### Exception Handler Ordering
- `BFFExceptionHandler` (`@Order(Ordered.HIGHEST_PRECEDENCE)`) — BFF-specific exceptions
- Core framework handler (from tvsm-be-core) — catches remaining exceptions

## Testing

### Framework
- **JUnit 5** (`junit-jupiter`) for test lifecycle
- **Mockito** (`mockito-core`, `mockito-junit-jupiter`) for mocking
- **Spring Boot Test** (`spring-boot-starter-test`) for integration tests
- **MockMvc** for controller layer testing
- **AssertJ** for fluent assertions

### Test Structure
```
src/test/java/com/tvsm/{module}/
├── controller/     # @WebMvcTest with MockMvc
├── service/        # Unit tests with @MockitoBean
├── repository/     # (Minimal — rely on integration tests)
├── mapper/         # MapStruct mapper tests
├── strategy/       # Strategy implementation tests
└── util/           # TestDataBuilder helpers
```

### Controller Test Pattern
```java
@WebMvcTest(OrderController.class)
@ContextConfiguration(classes = {OrderController.class})
public class OrderControllerTest {
    @Autowired private MockMvc mockMvc;
    @MockitoBean private OrderService orderService;

    @Test
    void testCreateOrder() throws Exception {
        when(orderService.createOrder(any())).thenReturn(expectedResponse);
        mockMvc.perform(post("/api/v1/order/create")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{...}"))
                .andExpect(status().isOk());
    }
}
```

### Running Tests
```bash
mvn test                          # Run all tests
mvn test -pl order-service        # Run tests for specific module
mvn verify                        # Run tests + generate JaCoCo report
```

## Build & Deployment

### Local Development
```bash
mvn clean install -DskipTests     # Build all modules
mvn spring-boot:run -pl tvs-cps-app  # Run the application
```
Application starts on port 8080 with context path `/`.

### Docker Build
```dockerfile
# Stage 1: Build with Maven (base image includes tvsm-be-core framework)
FROM tvsmazcmnsvcacrdev01.azurecr.io/tvsm-cs/tvs-cps-be-base-framework:33222-d9fde9e AS builder
RUN mvn clean install -DskipTests

# Stage 2: Runtime
FROM amazoncorretto:26.0.0-alpine3.22
COPY --from=builder /workspace/tvs-cps-app/target/tvs-cps-app-1.0.0-SNAPSHOT.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### CI/CD Pipeline (Azure DevOps)
1. **CI** (`ci-pipeline.yaml`): Triggers on `main` branch → builds Docker image
2. **Sonar** (`sonar.yaml`): Code quality analysis
3. **CD** (`cd-pipeline.yaml`): Deploys to environments (dev → UAT → prod)
4. **Security** (`AST_*.yml`): DAST/Tenable scanning on UAT and prod
5. **Image Scan** (`ast-image-scan.yaml`): Container vulnerability scanning

### Environment Configuration
All configuration is in `application.yml` with environment variable overrides:
- `DB_USERNAME`, `DB_PASSWORD` — Database credentials
- `PUBLIC_KEY` — JWT validation key
- `CLOUD_STORAGE_CONNECTION_STRING` — Azure Blob Storage
- `SAP_OAUTH_CLIENT_SECRET` — SAP ERP integration
- `AZURE_CLIENT_SECRET` — Azure AD OAuth
- `CPS_APIM_CLIENT_ID/SECRET/SCOPE` — API Management gateway
- `KAKFA_SSL_PWD` — Event Hub connection

### Kubernetes
Deployed via Helm chart (`norton-cps-app`) to AKS. Environments:
- `dev` — Development (auto-deploy from main)
- `UAT` — User acceptance testing
- `prod` — Production (manual approval gate)

## Key Configuration Properties

| Property | Purpose |
|----------|---------|
| `server.port` | 8080 |
| `spring.servlet.multipart.max-file-size` | 50MB |
| `spring.mvc.async.request-timeout` | 600000ms (10min for reports) |
| `webclient.max-in-memory-size` | 16MB buffer |
| `tvsm.core.security.excludedPaths` | Paths skipped by JWT filter |
| `rbac.enabled` | false (RBAC enforcement toggle) |
| `rbac.default-unmapped-api-behavior` | ALLOW (for unmapped endpoints) |
| `validation.files` | Comma-separated validation YAML file names |
| `catalog.cron.schedule` | Catalog refresh interval |
| `order.statuses.tracked` | Configurable order statuses for dashboard |

