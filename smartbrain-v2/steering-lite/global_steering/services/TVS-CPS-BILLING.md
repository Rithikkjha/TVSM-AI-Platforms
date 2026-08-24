# TVS-CPS-BILLING


## Product Context


# TVS CPS Billing Service — Product Context

## What This Service Does

TVS CPS Billing is a multi-tenant invoicing microservice for the TVS Motor Channel Partner System (CPS). It manages the full invoice lifecycle for vehicle and parts sales conducted through dealer channel partners. The service handles invoice creation, modification, finalization, discarding, retrieval, and reporting.

## Domain Entities

### Invoice
The central entity representing a billing document issued to a customer through a channel partner (dealer).

| Field | Purpose |
|-------|---------|
| invoiceId (UUID) | Primary key |
| tenantId | Tenant isolation identifier |
| invoiceNumber | Human-readable ID, format: `NINV-{yyMMdd}-{sequence}` |
| invoiceDate | Set when invoice is finalized (posted) |
| entityId / entityType | The business entity this invoice relates to (e.g., ORDER, VEHICLE_ORDER) |
| channelPartnerId / channelPartnerType | The dealer issuing the invoice |
| invoiceType | Category (SALES, VEHICLE_SALES, etc.) |
| invoiceStatus | Lifecycle state: DRAFT, FINAL, DISCARD |
| currencyCode | e.g., INR |
| paymentStatus | e.g., PENDING, PARTIAL, COMPLETED |
| totalLineitemlevelDiscountAmount | Sum of all line-item discounts |
| invoicelevelDiscountType / Amount / Context | Invoice-wide discount |
| totalInvoiceTaxAmount | Sum of all line-item taxes |
| totalInvoiceAmount | Grand total |
| paymentTerms (JSONB) | Flexible payment terms |
| additionalNotes (JSONB) | Extensible metadata (vehicle info, delivery date, discard reason) |

### InvoiceLineItem
Individual items on an invoice (parts or vehicles).

| Field | Purpose |
|-------|---------|
| invoiceLineItemId (UUID) | Primary key |
| invoiceId | FK to parent invoice |
| itemType | PARTS or VEHICLE |
| productCatalogId | Reference to product catalog |
| quantity / unitOfMeasure / unitPrice | Pricing inputs |
| lineitemDiscountType / Percentage / Amount / Context | Per-item discount |
| lineitemAggrTaxPercentage / lineitemTotalTaxAmount | Tax details |
| totalLineitemAmount | Computed total for this line |
| taxType | e.g., GST |
| taxInformation (JSONB) | Breakdown (CGST, SGST, IGST) |
| additionalInfo (JSONB) | Extensible metadata |

### Payment
Payment records associated with an invoice.

| Field | Purpose |
|-------|---------|
| paymentReceiptId (UUID) | Primary key |
| invoiceId | FK to invoice |
| entityId / entityType | Business entity reference |
| paymentMethod | CASH, UPI, etc. |
| paymentAmount / paymentCurrency | Amount details |
| paymentDate | When payment was made |
| paymentType | ADVANCE, FULL, etc. |
| paymentReference / paymentStatus | Tracking |
| additionalInfo (JSONB) | Extensible (e.g., UPI reference) |

## Invoice Statuses

```
DRAFT → FINAL   (via post-invoice)
DRAFT → DISCARD (via discard, with reason)
```

- Invoices are created in DRAFT status
- Only DRAFT invoices can be discarded
- Posting moves an invoice to FINAL and stamps the invoice date

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/v1/billing/create | Create a new invoice with line items and optional payments |
| POST | /api/v1/billing/update | Update invoice (add/update/delete line items, update dealer exec) |
| GET | /api/v1/billing/get/{invoiceNumber} | Retrieve full invoice by number |
| POST | /api/v1/billing/discard | Discard a DRAFT invoice with reason |
| POST | /api/v1/billing/post-invoice | Finalize invoice (DRAFT → FINAL) |
| POST | /api/v1/billing/report/invoice-list | Paginated report (PARTS or VEHICLE) |
| GET | /api/health | Health check |

## Business Rules

1. **Invoice number generation**: Format `NINV-{yyMMdd}-{sequence}` using a PostgreSQL sequence (`invoice_sequence`) for uniqueness.
2. **Line items required**: Invoice creation fails if no line items are provided.
3. **Vehicle invoice enrichment**: When a line item has `itemType=VEHICLE`, the invoice's `additionalNotes` is enriched with `isVehicleInvoice`, `bookingReference`, `vin`, and `productDescription`.
4. **Discard guard**: Only invoices in DRAFT state can be discarded. Attempting to discard a FINAL invoice throws an error.
5. **Post-invoice**: Sets status to FINAL, stamps `invoiceDate` to now, and optionally records `deliveryDate` in `additionalNotes`.
6. **Line item calculations**:
   - `lineSubtotal = unitPrice × quantity`
   - `lineDiscount = discountAmount × quantity`
   - `lineTax = (unitPrice - discountAmount) × taxPercentage/100 × quantity`
   - `lineAmount = subtotal - discount + tax`
7. **Invoice totals**:
   - `invoiceAmount = subtotal - totalLineDiscount + totalTax - invoiceDiscount`
8. **Tenant isolation**: All queries filter by `tenantId` from the JWT/request context.
9. **Audit fields**: All entities track `createdAt`, `createdBy`, `updatedAt`, `updatedBy`.

## Integrations

- **tvsm-be-core library**: Provides BaseController, TenantContext, APIResponse/APIException, JWT security, logging aspects, JsonUtil, and multi-tenant datasource routing.
- **PostgreSQL**: Primary data store with JSONB columns for flexible metadata.
- **Azure Blob Storage**: Configured (cloud-storage provider) but not actively used in billing logic.
- **RestTemplate**: Configured for outbound HTTP calls (ApiPassthroughUtil), though not currently used in billing flows.

## Multi-Tenancy

Tenant context is extracted from JWT headers and made available via `TenantContext`:
- `tenantId` — data isolation key
- `channelPartnerId` / `channelPartnerType` — dealer identity
- `currentUser` — audit trail



## Code Structure


# TVS CPS Billing Service — Project Structure

## Directory Layout

```
TVS-CPS-BILLING/
├── .kiro/steering/              # Kiro steering files (this documentation)
├── src/
│   ├── main/
│   │   ├── java/com/tvsm/billing/
│   │   │   ├── TVSCPSBillingApplication.java   # Spring Boot entry point
│   │   │   ├── config/
│   │   │   │   ├── Config.java                 # RestTemplate bean with timeouts
│   │   │   │   └── CorsConfig.java             # CORS filter (all origins, all methods)
│   │   │   ├── constants/
│   │   │   │   └── ApiConstants.java           # URL paths and success message keys
│   │   │   ├── controller/
│   │   │   │   ├── BillingController.java      # Invoice CRUD endpoints
│   │   │   │   ├── BillingReportController.java # Report endpoints (parts/vehicle)
│   │   │   │   └── HealthController.java       # /api/health
│   │   │   ├── dto/
│   │   │   │   ├── CreateInvoiceRequestDto.java # Create/update request (nested LineItemsDto, PaymentDto)
│   │   │   │   ├── GetInvoiceResponseDto.java  # Full invoice response (nested TotalsDto, LineItemsSummaryDto, StatusInfoDto)
│   │   │   │   ├── PostInvoiceRequestDto.java  # Finalize invoice request
│   │   │   │   ├── PostInvoiceResponseDto.java # Finalize invoice response
│   │   │   │   ├── InvoiceDiscardRequestDto.java # Discard request (invoiceNumber + reason)
│   │   │   │   ├── InvoiceDiscardResponseDto.java # Discard response
│   │   │   │   ├── PaginatedResponse.java      # Generic paginated wrapper
│   │   │   │   └── SearchRequestDto.java       # Generic search/filter DTO (and/or filters, sort, pagination)
│   │   │   ├── entity/
│   │   │   │   ├── Invoice.java                # JPA entity → "invoices" table
│   │   │   │   ├── InvoiceLineItem.java        # JPA entity → "invoice_line_item" table
│   │   │   │   └── Payment.java                # JPA entity → "payment" table
│   │   │   ├── enums/
│   │   │   │   └── InvoiceStatus.java          # DRAFT, FINAL, DISCARD
│   │   │   ├── exception/
│   │   │   │   └── ErrorResponse.java          # Structured error DTO (timestamp, status, message, validationErrors)
│   │   │   ├── mapper/
│   │   │   │   └── InvoiceMapper.java          # MapStruct interface (Entity ↔ DTO)
│   │   │   ├── repository/
│   │   │   │   ├── InvoiceRepository.java      # JPA repo with custom JPQL queries + sequence call
│   │   │   │   ├── InvoiceLineItemRepository.java # findByInvoiceId, findByInvoiceIdAndItemType
│   │   │   │   └── PaymentRepository.java      # Basic CRUD
│   │   │   ├── service/
│   │   │   │   ├── BillingService.java         # Core invoice logic (create, update, get, discard, post)
│   │   │   │   └── BillingReportService.java   # Report generation (parts/vehicle invoice lists)
│   │   │   └── util/
│   │   │       ├── ApiPassthroughUtil.java     # RestTemplate helper for outbound calls
│   │   │       ├── HelperService.java          # Invoice number generation (sequence-based)
│   │   │       └── TenantContextUtil.java      # Validates tenant context presence
│   │   └── resources/
│   │       └── application.yml                 # App config (DB, security, logging, actuator)
│   └── test/
│       └── java/com/tvsm/billing/
│           ├── controller/
│           │   ├── BillingControllerTest.java
│           │   └── BillingReportControllerTest.java
│           ├── service/
│           │   ├── BillingServiceTest.java
│           │   └── BillingReportServiceTest.java
│           └── util/
│               └── HelperServiceTest.java
├── pom.xml                          # Maven build (parent: tvsm-be-starter-parent)
├── Dockerfile                       # Multi-stage build (builder + Corretto 21 runtime)
├── ci-pipeline.yaml                 # Azure DevOps CI (triggers SonarQube, then build template)
├── sonar_ci.yml                     # SonarQube analysis pipeline
├── AST_cps_billing_uat_Pipeline.yml # UAT security scans (SAST, SCA, DAST, Dockerfile scan)
├── AST_cps_billing_prod_Pipeline.yml # Prod DAST scan
├── ast-image-scan.yaml              # Docker image vulnerability scan
└── README.md                        # Project overview
```

## Module Dependencies

```
Controller layer
  └── extends BaseController (from tvsm-be-core)
  └── depends on → Service layer
  └── uses → DTOs, ApiConstants

Service layer
  └── depends on → Repository layer
  └── depends on → Mapper (InvoiceMapper)
  └── depends on → HelperService (invoice number generation)
  └── uses → TenantContext (from tvsm-be-core)
  └── uses → JsonUtil (from tvsm-be-core)
  └── throws → APIException (from tvsm-be-core)

Repository layer
  └── extends JpaRepository
  └── uses → Entity classes
  └── custom JPQL queries for report filtering

Mapper layer
  └── MapStruct interface (compile-time code generation)
  └── maps Entity ↔ Response DTO
  └── handles JsonNode → String/Map conversions
```

## Architectural Decisions

1. **Layered architecture**: Standard Controller → Service → Repository pattern. No domain-driven design; business logic lives in service classes.

2. **Shared core library (`tvsm-be-core`)**: Cross-cutting concerns (security, multi-tenancy, logging, exception handling, base controller) are centralized. This service inherits JWT validation, tenant routing, and standardized API responses.

3. **JSONB for extensibility**: `additionalNotes`, `paymentTerms`, `taxInformation`, and `additionalInfo` columns use PostgreSQL JSONB. This avoids schema migrations for new metadata fields.

4. **MapStruct for mapping**: Compile-time DTO mapping with custom `default` methods for JsonNode conversions. Lombok-MapStruct binding ensures builder compatibility.

5. **Single request DTO for create and update**: `CreateInvoiceRequestDto` serves both operations. The `LineItemsDto` nested class has `add`, `update`, and `delete` lists to support partial updates in a single call.

6. **Sequence-based invoice numbers**: Uses a PostgreSQL sequence (`invoice_sequence`) via native query for globally unique, monotonically increasing invoice numbers.

7. **No explicit transaction management**: Relies on Spring's default transactional behavior. `HelperService.generateInvoiceNumber` is annotated `@Transactional` to ensure sequence reads are consistent.

8. **Report queries use JPQL JOINs**: Invoice reports join `Invoice` with `InvoiceLineItem` to filter by item type, avoiding N+1 at the query level (though line items are fetched separately per invoice for mapping).

9. **Controllers extend BaseController**: Provides a `success()` helper that wraps responses in a standardized `APIResponse` envelope with status codes and messages.

10. **No pagination on core CRUD**: Pagination is only implemented on report endpoints. Core invoice operations work on single entities.



## Tech Stack & Dependencies


# TVS CPS Billing Service — Tech Stack & Conventions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Java 21 |
| Framework | Spring Boot (via `tvsm-be-starter-parent` 1.0.0) |
| Web | Spring Boot Starter Web |
| Persistence | Spring Data JPA + Hibernate (PostgreSQL dialect) |
| Database | PostgreSQL with JSONB columns |
| Validation | Spring Boot Starter Validation |
| Mapping | MapStruct (with Lombok binding) |
| Boilerplate | Lombok (@Data, @Builder, @RequiredArgsConstructor, @Slf4j) |
| API Docs | SpringDoc OpenAPI (Swagger UI) |
| Monitoring | Spring Boot Actuator (health, info, metrics) |
| Testing | JUnit 5 + Mockito + Spring Boot Test |
| Coverage | JaCoCo |
| Build | Maven (with Surefire 3.2.2) |
| Container | Docker multi-stage (builder with custom base image → Amazon Corretto 21 runtime) |
| CI/CD | Azure DevOps Pipelines |
| Security Scanning | Checkmarx (SAST), SCA/SBOM, DAST, Dockerfile scan, Tenable (container) |
| Code Quality | SonarQube |

## Coding Conventions

### Naming
- **Packages**: `com.tvsm.billing.{layer}` (controller, service, repository, dto, entity, mapper, util, config, constants, enums, exception)
- **Classes**: PascalCase. DTOs suffixed with `Dto`, entities are plain nouns, services suffixed with `Service`
- **Fields**: camelCase in Java, snake_case in JSON (via `@JsonProperty`)
- **Constants**: UPPER_SNAKE_CASE as `public static final` in dedicated constants classes
- **Database columns**: snake_case matching entity field annotations

### Lombok Usage
- `@Data` on entities and DTOs (generates getters, setters, equals, hashCode, toString)
- `@Builder` on entities and some DTOs for fluent construction
- `@NoArgsConstructor` + `@AllArgsConstructor` on all entities and DTOs (required for JPA and Jackson)
- `@RequiredArgsConstructor` on services and controllers for constructor injection
- `@Slf4j` on services and config classes for logging

### Dependency Injection
- Constructor injection via `@RequiredArgsConstructor` (no `@Autowired` annotations)
- All dependencies are `private final` fields

### JSON Serialization
- `@JsonProperty("snake_case")` on DTO fields for API contract
- `@JsonInclude(JsonInclude.Include.NON_NULL)` on error responses
- JSONB columns use `@JdbcTypeCode(SqlTypes.JSON)` with `JsonNode` type

### Entity Conventions
- `@DynamicUpdate` on all entities (only changed columns in UPDATE statements)
- UUID primary keys with `@GeneratedValue`
- `@Column(name = "...")` explicit mapping on all fields
- Audit fields: `createdAt`, `createdBy`, `updatedAt`, `updatedBy` (Instant + String)

## Patterns

### API Response Envelope
All endpoints return `ResponseEntity<APIResponse<T>>` using `BaseController.success()`:
```java
return success(data, APIResponse.Status.SUCCESS, "message", "SUCCESS_CODE");
```

### Error Handling
- Business errors throw `APIException` (from tvsm-be-core) with status code, message, and optional params
- `APIException` includes: message, statusCode name, error details, API error constant, and ParamDTO for context
- `ErrorResponse` DTO provides structured error output (timestamp, status, error, message, path, validationErrors)
- No explicit `@ControllerAdvice` in this service — handled by the core library

### Multi-Tenancy
- `TenantContext` (thread-local from core library) provides tenant ID, channel partner info, and current user
- All repository queries include `tenantId` filter
- `TenantContextUtil` validates presence of required context fields

### Logging
- `@Loggable` aspect annotation on controllers (from tvsm-be-core) for automatic request/response logging
- `@Slf4j` for manual logging in services
- Log pattern includes traceId for distributed tracing
- Levels: DEBUG for service logic, INFO for Spring Web, DEBUG for Hibernate SQL

### Pagination
- Report endpoints accept `page` (1-based) and `size` query params
- Controller converts to 0-based page index: `Math.max(0, page - 1)`
- Size clamped between 1 and 1000
- Returns `PaginatedResponse<T>` with content, totalRecords, currentPage, pageLimit

### MapStruct Mapping
- Interface with `@Mapper(componentModel = "spring")`
- `@Mapping` annotations for field name differences between entity and DTO
- Custom `default` methods for `JsonNode → String` and `JsonNode → Map<String, Object>` conversions
- Null value strategy: `NullValuePropertyMappingStrategy.IGNORE`

## Testing

### Framework
- JUnit 5 (`@ExtendWith(MockitoExtension.class)`)
- Mockito for mocking dependencies
- No integration tests or testcontainers — all tests are unit tests with mocked repositories

### Test Structure
- `@Nested` classes group related test scenarios (e.g., CreateInvoiceTests, UpdateInvoiceTests)
- `@DisplayName` for readable test descriptions
- `@BeforeEach` for common setup
- `MockedStatic<TenantContext>` for tenant context in service tests (closed in `@AfterEach`)

### Test Coverage
- Controllers: verify correct service delegation and response wrapping
- Services: verify business logic, exception paths, entity construction, and repository interactions
- Utils: verify invoice number format and sequence behavior
- JaCoCo plugin generates coverage reports

### Running Tests
```bash
mvn test                    # Run all tests
mvn test -pl .              # Run tests for this module only
mvn jacoco:report           # Generate coverage report (target/site/jacoco/)
```

## Build & Deployment

### Local Development
```bash
mvn spring-boot:run         # Start on port 8081
# Requires PostgreSQL and environment variables for DB credentials and JWT keys
```

### Docker Build
Multi-stage Dockerfile:
1. **Builder stage**: Uses custom base image (`tvsm-cs/tvs-cps-be-base-framework`) with pre-installed framework dependencies. Runs `mvn clean install -DskipTests`.
2. **Runtime stage**: Amazon Corretto 21 (headless). Copies JAR, runs with `-Xms256m -Xmx384m -XX:+UseContainerSupport`.

### CI/CD Pipeline (Azure DevOps)
1. **SonarQube** (`sonar_ci.yml`): Triggered after UAT pipeline, runs code quality analysis
2. **CI Build** (`ci-pipeline.yaml`): Triggered on `main` branch push, uses shared build template from `Devops_ISSM_pipelines` repo
3. **UAT Security** (`AST_cps_billing_uat_Pipeline.yml`): Secret detection, SCA/SBOM, SAST (Checkmarx), API security, Dockerfile scan, container security, DAST
4. **Prod Security** (`AST_cps_billing_prod_Pipeline.yml`): DAST scan only (triggered after prod deployment)
5. **Image Scan** (`ast-image-scan.yaml`): Docker image vulnerability scanning

### Environment Variables
| Variable | Purpose |
|----------|---------|
| BIL_JWT_PUBLIC_KEY_1 | RSA public key for JWT validation |
| BIL_DB_USERNAME | PostgreSQL username |
| BIL_DB_PASSWORD | PostgreSQL password |
| INV_AZURE_STORAGE_CONNECTION_STRING | Azure Blob Storage connection |

### Key Configuration (application.yml)
- Server port: 8081
- Context path: /
- Hibernate DDL: none (schema managed externally)
- Actuator: health, info, metrics exposed
- Security excluded paths: /actuator/**, /error, /api/health/**
- REST timeouts: connect 5s, read 10s

