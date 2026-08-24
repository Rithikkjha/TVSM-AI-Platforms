# TVS-CPS-JOBS


## Product Context


# TVS-CPS-JOBS — Product Context

## What This Service Does

TVS-CPS-JOBS is a **stateless scheduled batch processing microservice** for the Norton Motorcycles Channel Partner System (CPS). It orchestrates periodic background tasks that synchronize data between the CPS backend application and external systems (SAP ERP via Azure Data Lake).

The service does NOT own a database. It acts purely as a job runner — fetching data from one system and pushing it to another on a schedule.

**Domain**: Automotive dealer management for Norton Motorcycles (a TVS Motor subsidiary) across European markets (GB, IT, FR, DE, ES). Covers vehicle/parts orders, invoices, service appointments, warranty claims, and dealer analytics dashboards.

---

## Domain Entities

| Entity | DTO Class | Description |
|--------|-----------|-------------|
| ERP Order | `ERPOrderUpdateDto` | SAP sales order with line-item details: quantities, delivery/picking/invoice status, outbound delivery info |
| Order Invoice | `OrderInvoiceDto` | Invoice from SAP for an order: value, line items, vehicle identifiers (engine/frame/battery), part details |
| Analytics Request | `AnalyticsRequestDTO` | KPI calculation trigger with indicator keys for Claims, Appointments, Job Cards |
| Sales Order Request | `SalesOrderNoRequestDto` | Tenant-scoped request to fetch SAP order numbers |
| Sync ERP Status | `SyncERPStatusRequestDto` | Wrapper for a batch of ERP order updates |
| Insert Invoice | `InsertInvoiceRequestDto` | Wrapper for a batch of invoices to insert |

**Key relationships**: Orders → have line items → get delivered → get invoiced. Appointments and Claims are separate service domains with their own KPI indicators.

---

## External Integrations

| System | Purpose | Auth |
|--------|---------|------|
| **TVS-CPS-Backend** (`norton-cps-app`) | Main CPS application — order sync, invoice insert, appointment close, claim sync, L1 dashboard, analytics | OAuth2 bearer token + X-Tenant-ID header |
| **Azure Data Lake** (Azure Function) | Source of ERP order status and invoice data from SAP | Function code query param |
| **Azure AD** | OAuth2 token generation for service-to-service auth | Client credentials grant |

---

## Business Rules

### Order Status Sync (9 AM & 9 PM daily)
1. Fetch all SAP sales order numbers from CPS backend (multi-tenant: GB, IT, FR, DE, ES)
2. Query Azure Data Lake for current ERP status (batched by 10)
3. Push updated statuses back to CPS backend (batched by 20, grouped by CPS reference number)
4. Orders with null `CPSSalesOrderRefNo` are **skipped**

### Invoice Processing (2 AM daily)
1. Fetch invoices from Azure Data Lake for last N days (default: 2 days)
2. Filter by invoice type "M" and date range
3. Group by invoice number, batch by 20, send to CPS backend

### Appointment Auto-Close (2 PM daily)
- Triggers backend API to close appointments older than a configured threshold

### Claim SAP Sync (every 30 minutes)
- Triggers backend API to sync approved claims with SAP invoice details

### L1 Dashboard KPI Calculation (every hour)
- Triggers calculation of ALL claim, appointment, and job card indicators

### Analytics Indicators (25+ schedulers, staggered 3-min intervals starting midnight)
- Each triggers a specific KPI: bookings, enquiries, test rides, stock levels, orders, GRN, retail, PDI, TAT, etc.

---

## Multi-Tenancy

- Tenant IDs are configured externally (`TENANT_IDS` env var, default: `GB,IT,FR,DE,ES`)
- Default tenant for headers: `GB`
- All backend calls include `X-Tenant-ID` header



## Code Structure


# TVS-CPS-JOBS — Project Structure

## Directory Layout

```
TVS-CPS-JOBS/
├── pom.xml                          # Maven build config; parent: tvsm-be-starter-parent
├── Dockerfile                       # Multi-stage: custom base builder → Temurin 21 runtime
├── ci-pipeline.yaml                 # Azure DevOps CI (build-template from shared repo)
├── cd-pipeline.yaml                 # Azure DevOps CD (Helm deploy to dev-cp namespace)
├── pr-build-validation.yaml         # PR validation pipeline
├── sonar.yaml                       # SonarQube analysis pipeline
├── ast-image-scan.yaml              # Container image security scan
├── AST_cps_jobs_prod_Pipeline.yml   # Production pipeline
├── ast_cps_jobs_uat_Pipeline.yml    # UAT pipeline
│
└── src/
    ├── main/
    │   ├── java/com/tvsm/jobs/
    │   │   ├── TVSCPSJobsApplication.java      # Spring Boot entry point
    │   │   │
    │   │   ├── config/
    │   │   │   └── JobConfiguration.java       # @EnableScheduling, RestTemplate bean
    │   │   │
    │   │   ├── constants/
    │   │   │   ├── ApiConstants.java           # Backend API endpoint paths
    │   │   │   ├── AppointmentAnalyticsKeyIndicator.java  # Enum: appointment KPIs
    │   │   │   ├── ClaimAnalyticsKeyIndicator.java        # Enum: claim KPIs
    │   │   │   └── JobCardAnalyticsKeyIndicator.java      # Enum: job card KPIs
    │   │   │
    │   │   ├── controller/
    │   │   │   ├── CronJobsController.java     # Manual trigger endpoints (fetch-invoices, sync-status)
    │   │   │   └── HealthController.java       # /api/health endpoint
    │   │   │
    │   │   ├── dto/
    │   │   │   ├── ERPOrderUpdateDto.java      # SAP order status fields (Jackson mapped)
    │   │   │   ├── OrderInvoiceDto.java        # SAP invoice fields (Jackson mapped)
    │   │   │   ├── AnalyticsRequestDTO.java    # KPI calculation request
    │   │   │   ├── SalesOrderNoRequestDto.java # Tenant-scoped order ID fetch
    │   │   │   ├── SyncERPStatusRequestDto.java # Batch order update wrapper
    │   │   │   └── InsertInvoiceRequestDto.java # Batch invoice insert wrapper
    │   │   │
    │   │   ├── scheduler/
    │   │   │   └── CronJobScheduler.java       # All @Scheduled methods (30+ cron jobs)
    │   │   │
    │   │   ├── service/
    │   │   │   ├── CronJobService.java         # Orchestrator — delegates to domain services
    │   │   │   ├── OrderService.java           # Fetch order IDs, sync ERP status
    │   │   │   ├── DataLakeService.java        # Azure Data Lake: order status queries
    │   │   │   ├── InvoiceDataLakeService.java # Azure Data Lake: invoice queries
    │   │   │   ├── InvoiceProcessingService.java # Invoice pull + batch insert
    │   │   │   ├── AppointmentService.java     # Auto-close appointments
    │   │   │   ├── ClaimService.java           # Claim SAP sync
    │   │   │   ├── L1DashboardService.java     # L1 dashboard KPI calculation
    │   │   │   ├── AnalyticsService.java       # Analytics indicator API calls
    │   │   │   ├── RestCallService.java        # Centralized HTTP client (auth, headers)
    │   │   │   └── ServiceOAuthTokenService.java # OAuth2 token generation
    │   │   │
    │   │   └── util/
    │   │       └── Constants.java              # Data Lake field name constants
    │   │
    │   └── resources/
    │       └── application.yml                 # All config: scheduling, URLs, auth, tenants
    │
    └── test/java/com/tvsm/jobs/               # Unit tests (JUnit 5 + Mockito)
```

---

## Module Dependencies

```
CronJobScheduler
    └── CronJobService (orchestrator)
            ├── OrderService
            │       └── RestCallService
            ├── DataLakeService
            │       └── RestCallService
            ├── InvoiceProcessingService
            │       ├── InvoiceDataLakeService
            │       │       └── RestCallService
            │       └── RestCallService
            ├── AppointmentService
            │       └── RestCallService
            ├── ClaimService
            │       └── RestCallService
            ├── L1DashboardService
            │       └── RestCallService
            └── AnalyticsService
                    └── RestCallService

RestCallService
    └── ServiceOAuthTokenService
            └── OAuthGenerationTokenUtil (from tvsm-be-core)
```

---

## Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **No database** | DataSource autoconfiguration excluded; all persistence delegated to CPS backend |
| **Single scheduler class** | All 30+ `@Scheduled` methods in one `CronJobScheduler` — simple to find, but large file |
| **CronJobService as facade** | Thin orchestration layer between scheduler and domain services; keeps scheduling concerns separate from business logic |
| **RestCallService as single HTTP gateway** | Centralizes auth token injection, tenant headers, and error handling for all outbound calls |
| **Batch processing with configurable sizes** | Data Lake queries batched by 10, backend updates batched by 20; prevents payload/timeout issues |
| **Externalized cron expressions** | All schedules in `application.yml` — deployable to different environments without code changes |
| **Manual trigger endpoints** | `CronJobsController` allows on-demand execution with a shared secret header (`valid`) for ops use |
| **Shared parent POM** | Inherits from `tvsm-be-starter-parent` for consistent dependency versions across CPS services |
| **Custom base Docker image** | Builder stage uses pre-built framework image from ACR to speed up CI builds |
| **Staggered analytics schedulers** | 25+ analytics jobs run 3 minutes apart (midnight–1:20 AM) to avoid overwhelming the backend |



## Tech Stack & Dependencies


# TVS-CPS-JOBS — Technical Guide

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 21 |
| Framework | Spring Boot | Managed by `tvsm-be-starter-parent` 1.0.0 |
| Build | Maven | With JaCoCo coverage plugin |
| HTTP Client | Spring RestTemplate | (via `JobConfiguration` bean) |
| Scheduling | Spring `@Scheduled` + `@EnableScheduling` | — |
| Serialization | Jackson (`ObjectMapper`) | — |
| Code Gen | Lombok + MapStruct | With `lombok-mapstruct-binding` |
| API Docs | SpringDoc OpenAPI / Swagger UI | `springdoc-openapi-starter-webmvc-ui` |
| Auth | OAuth2 client credentials (Azure AD) | Via `tvsm-be-core` utilities |
| Monitoring | Spring Actuator | health, info, metrics |
| Database | None (DataSource excluded) | PostgreSQL driver present for core lib |
| Container | Docker multi-stage | Eclipse Temurin 21.0.10 JDK UBI10 minimal |
| Registry | Azure Container Registry | `tvsmazcmnsvcacrdev01.azurecr.io` |
| CI/CD | Azure DevOps Pipelines | YAML templates from shared DevOps repo |
| Deployment | Helm charts → Kubernetes (AKS) | `dev-cp` namespace |
| Testing | JUnit 5 + Mockito | `spring-boot-starter-test` |

---

## Coding Conventions

### General
- **Lombok everywhere**: `@Data`, `@Builder`, `@RequiredArgsConstructor`, `@Slf4j`, `@NoArgsConstructor`, `@AllArgsConstructor`
- **Constructor injection** via `@RequiredArgsConstructor` — never use `@Autowired`
- **`@Value` for config injection** — all external config via Spring property binding
- **No field injection** — all dependencies are `private final` fields

### Naming
- DTOs: `*Dto` or `*DTO` suffix (inconsistent — prefer `*Dto` for new classes)
- Services: `*Service` suffix
- Constants: `UPPER_SNAKE_CASE` static finals
- Jackson field mapping: `@JsonProperty("UPPER_SNAKE_CASE")` matching SAP field names
- Packages: lowercase, single-word (`config`, `constants`, `controller`, `dto`, `scheduler`, `service`, `util`)

### Class Structure
- Controllers extend `BaseController` from `tvsm-be-core`
- Constants classes have private constructors to prevent instantiation
- Enums used for KPI indicator types
- `@Loggable` annotation (from `tvsm-be-core`) on service classes for method-level logging/performance tracking

### Logging
- SLF4J via Lombok `@Slf4j`
- Step-numbered logs in multi-step workflows (`Step 1a:`, `Step 2b:`, etc.)
- Trace ID included in log pattern: `[%X{traceId:-}]`
- Log sanitization: `%replace(%msg){ "[<>|\n\r\t]", "" }` to strip injection characters
- Log levels: `INFO` for flow milestones, `DEBUG` for payloads/details, `ERROR` for failures, `WARN` for empty/skipped data

---

## Patterns

### Scheduler → Service Delegation
```
@Scheduled → CronJobScheduler → CronJobService → DomainService → RestCallService
```
The scheduler catches all exceptions. `CronJobService` orchestrates steps. Domain services handle business logic. `RestCallService` handles HTTP concerns.

### Batch Processing
- Data is grouped (by CPS ref no or invoice number) then chunked into configurable batch sizes
- Each batch is processed independently — a failed batch does not stop subsequent batches
- Pattern: collect into `currentBatch`, process when count reaches `dataProcessBatchSize`, clear and continue

### Centralized HTTP Client (`RestCallService`)
- Single generic `post()` method using `ParameterizedTypeReference<T>` for type-safe responses
- Automatically injects: `Content-Type: application/json`, `Accept: */*`, `X-Tenant-ID`, Bearer token (if enabled)
- Returns `ResponseEntity` with `503 SERVICE_UNAVAILABLE` on any exception — never throws

### OAuth2 Service Token
- `ServiceOAuthTokenService` generates tokens via `OAuthGenerationTokenUtil` from core library
- Token is injected into headers by `RestCallService.getHeaders()` when `service.auth-token.enable=true`

### Manual Trigger Endpoints
- `CronJobsController` exposes POST endpoints for ops to trigger jobs on-demand
- Protected by a shared secret header (`valid`) compared against config value — not JWT-protected

---

## Error Handling

| Pattern | Where Used |
|---------|-----------|
| **Catch-all try/catch** | Every service method and every scheduler method |
| **Never propagate exceptions** | All exceptions are logged and swallowed; methods return empty/false/null |
| **Empty collection on failure** | `Collections.emptyList()` returned instead of null |
| **Boolean success tracking** | `allSuccessful` flag across batch iterations |
| **String-based error detection** | Response body checked for "Exception", "failed", "Failed" strings |
| **Null-safe response checks** | Always check `response != null && response.getBody() != null` before use |
| **Graceful degradation** | Failed batches don't stop remaining batches from processing |
| **RestCallService 503 fallback** | On any HTTP exception, returns a `ResponseEntity` with 503 status and empty body |

---

## Testing

- **Framework**: JUnit 5 + Mockito (via `spring-boot-starter-test`)
- **Coverage**: JaCoCo plugin configured in Maven; reports generated during `test` phase
- **Test location**: `src/test/java/com/tvsm/jobs/` mirrors main source structure
- **Style**: Unit tests with mocked dependencies (no integration/container tests observed)
- **Naming**: `*Test` suffix on test classes

### Running Tests
```bash
mvn test                    # Run all tests with coverage
mvn verify                  # Full build + test + coverage report
```

---

## Build & Deployment

### Local Build
```bash
mvn clean install -DskipTests   # Build without tests
mvn clean install               # Build with tests + JaCoCo report
```

### Docker Build
```dockerfile
# Stage 1: Build using custom base framework image (has parent POM pre-installed)
FROM tvsmazcmnsvcacrdev01.azurecr.io/tvsm-cs/tvs-cps-be-base-framework:<tag> AS builder
# Stage 2: Runtime on Eclipse Temurin 21 minimal
FROM eclipse-temurin:21.0.10_7-jdk-ubi10-minimal
```

### JVM Configuration
- `-Xms256m -Xmx384m` — lightweight memory footprint for a job runner
- `-XX:+UseContainerSupport` — respects container memory limits

### CI/CD Pipeline Flow
1. **Sonar pipeline** runs on `main` branch push
2. **CI pipeline** (`ci-pipeline.yaml`) triggered by Sonar completion → builds Docker image
3. **CD pipeline** (`cd-pipeline.yaml`) triggered by CI completion → Helm deploy to `dev-cp`
4. UAT/Prod stages available (currently commented out) with manual approval gates

### Environment Configuration
All environment-specific values are injected via environment variables:
- `AZURE_DATALAKE_API_URL`, `AZURE_DATALAKE_FUNCTION_CODE`
- `SERVICE_AUTH_TOKEN_CLIENT_ID`, `SERVICE_AUTH_TOKEN_CLIENT_SECRET`, `SERVICE_AUTH_TOKEN_SCOPE`, `SERVICE_AUTH_TOKEN_TENANT_ID`
- `TENANT_IDS`, `VALID_TENANT_ID`
- `JWT_PUBLIC_KEY_1`
- `AZURE_STORAGE_CONNECTION_STRING`

### Key Endpoints
| Path | Purpose |
|------|---------|
| `/api/health` | Health check (excluded from JWT) |
| `/api/v1/cron-jobs/fetch-invoices` | Manual invoice fetch trigger |
| `/api/v1/cron-jobs/sync-status` | Manual order sync trigger |
| `/actuator/health` | Spring Actuator health |
| `/swagger-ui.html` | API documentation |

