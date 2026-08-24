# tvsmbe-mdp-bff


## Product Context


# Product: MDP BFF (Master Data Platform - Backend For Frontend)

## What This Service Does

MDP BFF is a Backend-For-Frontend layer for TVS Motor's Master Data Platform (MDP), specifically the **dealer management** domain. It serves two roles:

1. **Inbound** — Receives HTTP requests from external clients and proxies them to the MDP core service (dealer data queries, webhook ingestion).
2. **Outbound** — Consumes dealer data change events from Azure Service Bus and pushes updates to multiple external third-party services.

### Core Flow

```
[External Clients] → [MDP-BFF Inbound] → [MDP Core Service]
[MDP Core Service] → [Azure Service Bus] → [MDP-BFF Outbound] → [External Services]
```

---

## Domain Entities

### Dealer (core aggregate)
- `sapDealerCode` — unique identifier (SAP system code)
- `type` — AMD, AD, BRANCH
- `dmsStatus` — DMS system status
- `mdpStatus` — ACTIVE or INACTIVE
- `parentAmdSapDealerCode`, `parentApsSapDealerCode` — hierarchy references

### DealerDetails
- Name, branch name, operating hours, GST number
- Knowlarity virtual number, routing CLI, fallback number
- Test ride configuration (DTR/HTR start dates, caps per day)
- Offline booking caps (iQube, TVSX)

### Location
- Type (MAIN, etc.), full address (line1/2/3), pincode, city, state
- Latitude, longitude, Google Maps URL, Google Plus Code
- Territory, area, zone

### Contact
- Type-based: primary/secondary phone, email

### Employee
- Type: SHOWROOM_MANAGER, etc.
- Name, phone, email, managerId, active/deleted status

### Flag
- Named feature flags per dealer (e.g., `K_NUMBER_NEEDED`)
- `isEnabled` (integer: 0/1)

### AuditLog
- Tag (enum-based type), metadata (JSON text), transactionId
- Tracks every significant operation for traceability

### FailedMdpMessageExceptionEntity (outbound only)
- Persists failed external API calls with full dealer data payload
- Includes: client, failureEventType, apiResponse, responseCode, priority

---

## External Integrations

| Integration | Direction | Purpose |
|---|---|---|
| **MDP Core Service** | Inbound calls MDP | Fetch dealer data by SAP code, pincode, or filters |
| **Azure Service Bus** | Outbound consumes | Receives dealer data change events (topic: `mdp.dealer_data`) |
| **Knowlarity** | Outbound pushes | Virtual phone number (K-number) pool, assignment, update, removal |
| **Single Interface** | Outbound pushes | Outlet creation/closure (Google My Business related) |
| **LatLong** | Outbound pushes | Dealer geolocation data sync |
| **Daksha (Stratbeans)** | Outbound pushes | Dealer update notifications to training platform |
| **Azure B2C** | Both modules | OAuth2 token generation for inter-service authentication |
| **Notification Service** | Outbound sends | Email alerts for external API failures |

---

## API Endpoints (Inbound)

| Method | Path | Description |
|---|---|---|
| GET | `/mdp-bff/v1/mdp/dealer/{sapDealerCode}` | Get dealer data by SAP dealer code |
| POST | `/mdp-bff/v1/mdp/dealer/basedOnFilters` | Query dealers by type, status, flags with search |
| GET | `/mdp-bff/v1/mdp/dealers?pincode={pincode}` | Get dealers by pincode |
| POST | `/mdp-bff/webhook/v1/{mdpModule}/{externalClient}/{webHookEventType}` | Generic webhook receiver |
| GET | `/mdp-bff/v1/test/hello` | Health check |

---

## Business Rules

### Knowlarity K-Number Assignment
- Only ACTIVE dealers receive virtual numbers
- INACTIVE dealers with existing K-numbers get them unassigned
- K-number assignment is enabled per dealer type via config (`KNOWLARITY_K_NUM_ASSIGNMENT_ENABLED_DEALER_TYPES`)
- AMD and BRANCH dealers always qualify if enabled
- AD dealers require the `K_NUMBER_NEEDED` flag to be enabled
- Pricing tier mapping: AMD → AMD tier; AD and BRANCH → AD tier
- Assignment is a 3-step synchronized process: (1) pick from Knowlarity pool, (2) assign in MDP, (3) update Knowlarity dealer API

### Single Interface Outlet Management
- Only processes dealer types listed in `SI_ENABLED_DEALER_TYPES`
- ACTIVE dealers → create outlet; INACTIVE dealers → close outlet
- Outlet creation requires: pincode, lat/long, city, showroom manager (name, email, phone), and at least one address line

### BRANCH Dealer Processing (GMB Common)
- BRANCH dealers are only processed if `tempDmsBranchSequence != 1` AND `parentAmdSapDealerCode` is present
- This shared logic (`GmbCommonService.shouldProcessDealerData`) applies to Knowlarity and Single Interface

### Failure Handling
- Failed external API calls are persisted to DB with full dealer data for retry
- Email notifications are sent to configured recipients with rate limiting (via `FailureEventTypeInfoService`)
- Separate failure event types: `KNOWLARITY_API_FAILURE_RESPONSE`, `KNOWLARITY_CALL_POOL_API_EMPTY`, etc.

### External Client Configuration
- Which external clients are active is controlled by `MDP_BFF_EXTERNAL_CLIENTS` env var
- Dealer data is sent to all enabled clients in parallel



## Code Structure


# Project Structure

This is a multi-module Java Spring Boot monorepo with two independently deployable services: **inbound** and **outbound**. Each has its own `pom.xml`, `Dockerfile`, and CI/CD pipelines.

## Repository Layout

```
tvsmbe-mdp-bff/
├── inbound/          # HTTP API service (receives requests, proxies to MDP core)
├── outbound/         # Event consumer service (Azure Service Bus → external clients)
├── .kiro/            # Kiro steering and config
├── .env              # Shared environment variables
└── *.yml             # Root-level Azure DevOps pipeline definitions
```

## Module: Inbound

- **Base package:** `com.tvsmotor.bff`
- **Spring Boot entry:** `BffApplication.java`
- **Build:** `inbound/pom.xml` (Maven)
- **Profiles:** `local`, `dev`, `uat`, `prod` (via `application-{profile}.properties`)

### Package Layout

| Package | Purpose |
|---|---|
| `controller` | REST endpoints (`MdpController`, `WebHookController`, `TestController`) |
| `service` | Business logic, HTTP client calls, webhook handling |
| `service.interfaces` | Service interfaces |
| `model.request.mdp` | Inbound request DTOs |
| `model.response` | Response DTOs (includes `azure/` for B2C token models) |
| `entity` | JPA entities (`AuditLog`, `BaseEntity`) |
| `repository` | Spring Data JPA repos (`AuditLogRepo`) |
| `enums` | Domain enums (`DealerType`, `DmsStatus`, `ExternalClient`, etc.) |
| `exceptions` | Custom exceptions + `handlers/RestExceptionHandler` |
| `config` | Spring config (`CustomConfig`, `PostConstructThings`) |
| `cache` | Cache service layer |
| `utils` | Utility classes |

## Module: Outbound

- **Base package:** `com.tvsmotor.mdp_bff.outbound`
- **Spring Boot entry:** `OutboundApplication.java`
- **Build:** `outbound/pom.xml` (Maven)
- **Profiles:** `local`, `dev`, `uat`, `prod`

### Package Layout

| Package | Purpose |
|---|---|
| `controller` | Minimal (only `TestController` for health check) |
| `service` | Core orchestration (`DealerDataPasserService`, `DealerDataProcessor`, `DealerDataProcessorFactory`, `AsyncJobService`) |
| `service.service_bus.mdp` | Azure Service Bus consumer (`MdpDealerDataConsumerService`) |
| `service.knowlarity` | Knowlarity K-number API caller + processor |
| `service.single_interface` | Single Interface outlet API caller + processor + operations |
| `service.lat_long` | LatLong geolocation API caller + processor |
| `service.daksha` | Daksha/Stratbeans API caller + processor |
| `service.gmb_common` | Shared logic for GMB-related clients (branch dealer filtering) |
| `model` | Client abstraction (`BffClient`, `DealerDataClient`, per-client classes: `KNOWLARITY`, `SINGLE_INTERFACE`, `LAT_LONG`, `DAKSHA`) |
| `model.request` | Outbound request DTOs (per-client subpackages + `EmailNotificationRequest`) |
| `model.response` | Response DTOs (per-client subpackages: `azure/`, `knowlarity/`, `service_bus/`) |
| `entity` | JPA entities (`AuditLog`, `FailedMdpMessageExceptionEntity`, `FailureEventTypeInfo`) |
| `repository` | Spring Data JPA repos (`AuditLogRepo`, `FailedMdpMessageExceptionRepo`, `FailureEventTypeInfoRepo`) |
| `enums` | Domain enums (`ExternalClient`, `FailureEventType`, `ApiRetryPriority`, `MdpStatus`, `SapStatus`, etc.) |
| `exceptions` | Custom exceptions |
| `config` | Spring config (`CustomConfig`, `BffServiceBusConfig`, `PostConstructThings`) |
| `cache` | Cache service layer |
| `utils` | Utility classes |

## Key Patterns

- **External client abstraction:** Each external client (Knowlarity, Single Interface, LatLong, Daksha) follows a consistent pattern with an `*ApiCallerService` (HTTP calls) and `*DealerDataProcessorService` (business logic). The `DealerDataProcessorFactory` routes to the correct processor.
- **HTTP client:** Both modules use OkHttp (`OkHttpService` + `OkHttpConfig`) for outbound HTTP calls.
- **Auth:** Azure B2C OAuth2 token generation (`AzureB2CTokenGenerationService`) for inter-service auth.
- **Audit logging:** Both modules persist audit logs via `AuditLogService` → `AuditLogRepo`.
- **Failure persistence:** Outbound persists failed API calls to `FailedMdpMessageExceptionEntity` for retry.
- **Configuration:** Environment-specific properties in `src/main/resources/application-{profile}.properties`. Runtime config via `CustomConfig` class reading `@Value` properties.

## Build & Run

```bash
# Build inbound
cd inbound && mvn clean package

# Build outbound
cd outbound && mvn clean package

# Run locally (requires appropriate profile)
cd inbound && mvn spring-boot:run -Dspring-boot.run.profiles=local
cd outbound && mvn spring-boot:run -Dspring-boot.run.profiles=local
```

## CI/CD

- Azure DevOps pipelines (YAML) for UAT and PROD
- Separate pipelines per module: `ci-pipeline.yaml` (build/test), `cd-pipeline.yaml` (deploy)
- Docker-based deployment (`Dockerfile` per module)
- SonarQube integration (`sonar_ci_pr_pipelines.yml`)
- AST image scanning pipelines at root level



## Tech Stack & Dependencies


# Tech Stack & Conventions

## Core Technology

| Layer | Technology | Version |
|---|---|---|
| Language | Java | 17 |
| Framework | Spring Boot | 3.5.12 |
| Build | Maven | 3.9.14 |
| ORM | Spring Data JPA + Hibernate | 6.6.13 |
| Audit | Hibernate Envers | 6.6.13 |
| Database | MySQL | 8.x (connector 8.4.0) |
| HTTP Client | OkHttp | 4.12.0 |
| Messaging | Azure Service Bus SDK | 7.17.8 (outbound), 7.14.7 (inbound) |
| API Docs | SpringDoc OpenAPI (Swagger UI) | 2.8.9 |
| Retry | Spring Retry | 1.3.4 |
| Monitoring | Spring Boot Actuator | (managed) |
| Utilities | Lombok, Google Guava | 1.18.26, 32.1.1-jre |
| Test DB | H2 | 2.3.232 |
| Code Coverage | JaCoCo | 0.8.11 |
| Container | Amazon Corretto 17 (Docker) | 17.0.18 |

## Coding Conventions

### Annotations & DI
- Use `@RequiredArgsConstructor` (Lombok) for constructor injection — no `@Autowired` on fields.
- Use `@Slf4j` (Lombok) for logging in every service/controller.
- Use `@Service`, `@Configuration`, `@ControllerAdvice` as appropriate Spring stereotypes.

### Naming
- Packages: lowercase with underscores for multi-word (`mdp_bff`, `single_interface`, `lat_long`).
- Classes: PascalCase. Services end with `Service`, controllers with `Controller`, repos with `Repo`.
- External client services follow the pattern: `{Client}ApiCallerService` (HTTP calls) + `{Client}DealerDataProcessorService` (business logic).
- Enums: UPPER_SNAKE_CASE values.

### Logging
- Log at method entry/exit for key operations with method name prefix: `log.info("methodName() : ...")`.
- Log level: INFO for normal flow, ERROR for exceptions (with full stack trace).
- Azure SDK logs suppressed to ERROR level.

### Configuration
- All environment-specific values use `${ENV_VAR}` placeholders in `application.properties`.
- Profile-specific overrides in `application-{local|dev|uat|prod}.properties`.
- Runtime config injected via `@Value` annotations into config classes or services.
- Feature toggles (which clients are active, which dealer types are enabled) are comma-separated env vars parsed at runtime.

## Architectural Patterns

### HTTP Client (OkHttpService)
- Centralized `OkHttpService` wraps all outbound HTTP calls.
- Returns `ApiCallResponse` with: `responseCode`, `responseData` (String), `isSuccessful`, and `metrics` (timing).
- Uses `StopWatch` for call duration tracking.
- Supports GET, POST (JSON body, form-encoded, query params, headers).
- Uses `@SneakyThrows` for checked exception handling.

### Factory Pattern (Outbound)
- `DealerDataProcessorFactory` routes to the correct `DealerDataProcessor` implementation based on `ExternalClient` enum.
- Each external client has its own sub-package under `service/` with an API caller and a data processor.

### Entity Auditing (BaseEntity)
- All JPA entities extend `BaseEntity` which provides: `id` (auto-generated), `createdBy`, `updatedBy`, `createdAt`, `updatedAt`, `version` (optimistic locking).
- `@PrePersist` and `@PreUpdate` lifecycle hooks auto-populate audit fields.
- `createdBy`/`updatedBy` resolved from `Context.getUserId()` or defaults to `"System"`.
- Hibernate Envers (`@Audited`) tracks entity revision history.

### Error Handling
- Global `@ControllerAdvice` (`RestExceptionHandler`) catches exceptions and returns `GeneralResponse`.
- `ValidationException` → 400 BAD_REQUEST with error message.
- Generic `Exception` → 500 INTERNAL_SERVER_ERROR.
- `HttpMessageNotReadableException` / `TypeMismatchException` → 400 with descriptive message.
- Response shape: `GeneralResponse { data: Object, errorMessage: String }`.

### Failure Persistence (Outbound)
- Failed external API calls are saved to `FailedMdpMessageExceptionEntity` with full dealer data payload.
- `FailureEventTypeInfoService` tracks failure counts and controls email notification rate limiting.
- `NotificationSenderService` sends failure alert emails via the Notification Service.

### Async Processing (Outbound)
- `AsyncJobService` handles parallel dispatch to multiple external clients.
- `DealerDataPasserService` orchestrates the flow from Service Bus message → processor factory → client-specific logic.

## API Response Format

```java
// Success
GeneralResponse.builder().data(payload).build();

// Error
GeneralResponse.builder().errorMessage("description").build();
```

## Testing

- **Framework:** JUnit 5 + Spring Boot Test (`spring-boot-starter-test`).
- **Test DB:** H2 in-memory database (test scope).
- **Coverage:** JaCoCo with package-level line coverage checks.
- **Exclusions from coverage:** `model/**`, `entity/**`, `exceptions/**` packages.
- **Run tests:** `mvn test` (per module).

## Deployment

### Docker
- Multi-stage build: Maven build stage → Amazon Corretto 17 runtime.
- JVM tuning: `-XX:MaxRAMPercentage=75` (container-aware memory).
- Timezone: `Asia/Kolkata`.
- Port: 8080.

### CI/CD (Azure DevOps)
- `ci-pipeline.yaml` — build, test, SonarQube analysis.
- `cd-pipeline.yaml` — Docker build, push to registry, deploy.
- `sonar_ci_pr_pipelines.yml` — PR-triggered quality gate.
- AST image scanning pipelines for security.
- Environments: UAT and PROD with separate pipeline definitions.

### Profiles
- `local` — local development (likely points to local/dev DB).
- `dev` — development environment.
- `uat` — user acceptance testing.
- `prod` — production.

Activated via `ACTIVE_ENVIRONMENT` env var → `spring.profiles.active`.

## Key Environment Variables

| Variable | Purpose |
|---|---|
| `ACTIVE_ENVIRONMENT` | Spring profile (local/dev/uat/prod) |
| `DATABASE_HOST_URL`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD` | MySQL connection |
| `MDP_BASE_URL` | MDP core service base URL |
| `AZURE_B2C_*` | Azure B2C OAuth2 credentials |
| `MDP_BFF_EXTERNAL_CLIENTS` | Comma-separated list of active external clients |
| `MDP_DEALER_DATA_TOPIC_*` | Azure Service Bus topic config |
| `SI_OUTLET_API_*` | Single Interface API credentials |
| `KNOWLARITY_K_NUMBER_API_*` | Knowlarity API credentials |
| `LATLONG_DEALER_DATA_API_*` | LatLong API credentials |
| `DAKSHA_DEALER_UPDATE_API_*` | Daksha API credentials |
| `NOTIFICATION_BASE_URL` | Notification service for failure emails |
| `SI_ENABLED_DEALER_TYPES` | Dealer types enabled for Single Interface |
| `KNOWLARITY_K_NUM_ASSIGNMENT_ENABLED_DEALER_TYPES` | Dealer types enabled for K-number assignment |

