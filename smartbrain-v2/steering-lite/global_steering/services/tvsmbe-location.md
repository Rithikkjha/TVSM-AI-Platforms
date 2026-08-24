# tvsmbe-location


## Product Context


# Product: TVS Motor Location Master Service

## What This Service Does

Location Master is the central microservice for all dealer location-related data at TVS Motor. It manages:

1. **Dealer Location Verification** — An SMS-driven workflow where admins initiate location capture, dealers submit GPS coordinates + photos via mobile, and admins verify submissions by comparing distances between SAP address, submitted address, and image GPS metadata.
2. **Dealer Proximity Search** — Public API for finding nearest dealers by latitude/longitude, filtered by dealer type (AMD/APS) and service flags (SALES/SERVICE).
3. **Administrative Location Data** — Hierarchical India location data (Country → State → District → SubDistrict → Pincode → Area) with geocoding support.
4. **International Business (IB) Dealer Management** — CRUD for dealership locations outside India with GeoJSON-based storage.
5. **Geocoding** — Forward and reverse geocoding via Google Maps API.

---

## Domain Entities

### Core Dealer Entities
- **DealerInfoDetails** — Tracks a dealer's location verification lifecycle: status, submitted coordinates, image-captured coordinates, photo URL, admin comments, SMS details. Keyed by `sapDealerCode` + `locationType`.
- **DealerSecretKey** — Time-limited secret keys sent via SMS to authenticate dealer location submissions. Expires after configurable days.
- **VerifiedDealerLocation** — Immutable history of verified dealer locations with timestamps per location type.
- **DealershipLocation** — IB dealer locations with GeoJSON points, status flags, and contact info.
- **DealerLocationData** — Dealer geo-coordinates for proximity queries.

### Administrative Location Entities
- **Country**, **State**, **District**, **SubDistrict**, **Division**, **Area**, **City** — Hierarchical location reference data.
- **Location** — Pincode-level location with lat/long (compound unique index on state+district+pincode+area).
- **Pincode**, **PincodeCentroidEntity** — Pincode reference and centroid coordinates.

### User & System Entities
- **UserX** — Admin and Territory Manager users with role-based ownership matrix (territories, dealers, location types).
- **AuditLog** — Audit trail for all significant operations and external API failures.
- **RejectionComment** — Predefined rejection reasons for admin verification flow.

---

## External Integrations

| System | Purpose | Protocol |
|--------|---------|----------|
| **MDP (Master Data Platform)** | Dealer master data, active status checks, branch lists, proximity search | REST + Azure B2C OAuth2 |
| **UMS (User Management Service)** | JWT token validation, dealer/branch manager contact lookup | REST + Azure B2C OAuth2 |
| **Notification Service** | SMS dispatch for location update requests, delivery status tracking | REST + Azure B2C + APIM key |
| **Google Maps Geocoding API** | Forward geocoding (address → lat/long), reverse geocoding | REST + API key |
| **Azure Blob Storage** | Dealer photo upload/download, presigned URL generation, regulatory documents | Azure SDK |
| **MongoDB Atlas** | Primary data store for all entities | Spring Data MongoDB |

---

## Business Rules

### Dealer Location Verification State Machine

```
VERIFICATION_TO_BE_INITIATED
    ↓ (admin sends SMS)
VERIFICATION_INITIATED
    ↓ (dealer submits location + photo)
VERIFICATION_PENDING
    ↓ (admin approves)         ↓ (admin rejects)
VERIFIED                     REJECTED
                                ↓ (admin re-sends SMS)
                             RE_VERIFICATION_INITIATED
                                ↓ (dealer re-submits)
                             RE_VERIFICATION_PENDING
                                ↓ (admin approves)    ↓ (admin rejects)
                             VERIFIED               REJECTED
```

### Access Control Rules
- **ADMIN** role: Full access to all dealers and location types.
- **TERRITORY_MANAGER** role: Access restricted to dealers within assigned territories OR explicitly assigned dealer codes, filtered by allowed location types.
- **Dealer Owner/Partner** and **Branch Manager**: Access only to their own dealership data (validated via JWT `dealerId` claim).

### Validation Rules
- Submitted location accuracy must be ≤ 500 meters (configurable).
- Image-captured location accuracy must be ≤ 20 meters (configurable).
- Secret keys expire after 2 days (configurable via `LOCATION_UPDATE_SECRET_EXPIRY_DAYS`).
- SAP dealer code max length: 20 characters.
- Address fields max length: 200 characters.
- Latitude: -90 to 90 degrees. Longitude: -180 to 180 degrees.

### Distance Matrix
When admin reviews a submission, the system calculates Haversine distances between three points:
1. SAP address (geocoded via Google Maps)
2. Dealer-submitted address coordinates
3. Image GPS metadata coordinates

### Beta Release
- Feature flag `BETA_RELEASE_ENABLED` gates the system to a whitelist of SAP dealer codes.
- When enabled, only dealers in `BETA_RELEASE_SAP_DEALER_CODES` are visible.

### Dealer Location Types
- **SALES** — Sales showroom location.
- **SERVICE** — Service center location.
- A dealer can have both types active independently (controlled by MDP flags).



## Code Structure


# Structure: Location Master Service

## Project Root

```
tvsmbe-location/
├── .env                          # Local environment variables (not committed)
├── .gitignore
├── pom.xml                       # Maven build config (Spring Boot 3.5.13, Java 17)
├── Dockerfile                    # Multi-stage build (Maven + Amazon Corretto 17 Alpine)
├── README.md                     # Setup instructions, env vars, useful commands
│
├── azure-pipelines/              # Azure DevOps CI/CD
│   ├── uat.ci.yml                # CI: Docker build + push to ACR
│   └── uat.cd.yml                # CD: Deploy to Azure Web App Container
│
├── scripts/python/               # One-off data scripts (geocoding, analysis)
│
└── src/
    ├── main/
    │   ├── java/com/tvsmotor/location_master/
    │   │   ├── LocationMasterApplication.java   # Spring Boot entry point
    │   │   ├── ENUM/                            # Business enumerations
    │   │   ├── config/                          # Spring configuration beans
    │   │   ├── controller/                      # REST API controllers
    │   │   ├── entity/                          # MongoDB document entities
    │   │   ├── exception/                       # Global exception handling
    │   │   ├── model/                           # DTOs (request/response/cache)
    │   │   ├── repository/                      # Spring Data MongoDB repositories
    │   │   ├── security/                        # Auth filter, security config
    │   │   ├── service/                         # Business logic layer
    │   │   └── utils/                           # Shared utilities
    │   └── resources/
    │       └── application.properties           # Externalized config (env vars)
    │
    └── test/java/com/tvsmotor/location_master/  # Mirrors main structure
```

---

## Package Breakdown

### `ENUM/` — Business Enumerations
| File | Purpose |
|------|---------|
| `DealerLocationStatus` | Verification state machine (7 states with admin/dealer display names) |
| `DealerLocationType` | SALES, SERVICE, PARTS (only SALES and SERVICE are active) |
| `DealerType` | AMD (Authorized Main Dealer), APS, etc. |
| `UserRole` | ADMIN, DEALER, TERRITORY_MANAGER |
| `ServiceType` | External service identifiers for token management (MDP, UMS, NOTIFICATION) |
| `CacheType` | Cache key namespaces |
| `CoordinateDistanceCalculatorFormula` | HAVERSINE formula selection |
| `DealerFilterType` | Proximity search filter categories |
| `MdpDealerFlagType` | MDP flag types for dealer capabilities |
| `AuditLogType` | Categorized audit event types |
| `RejectionCommentType` | Types of static rejection data |

### `config/` — Spring Configuration
| File | Purpose |
|------|---------|
| `AzureBlobConfig` | BlobContainerClient bean from connection string |
| `CacheConfig` | SimpleCacheManager with ConcurrentMapCache per CacheType |
| `OkHttpClientConfig` | OkHttpClient bean configuration |
| `PostConstructThings` | Application startup initialization |
| `TransactionManagerConfig` | MongoDB transaction manager setup |

### `controller/` — REST API Layer
| File | API Prefix | Access | Purpose |
|------|-----------|--------|---------|
| `AdminFlowController` | `/api/v1/admin-flow` | Admin/TM roles | Verification workflow, dealer lists, SMS trigger |
| `DealerFlowController` | `/api/v1/dealer-flow` | Dealer roles | Dealer self-service (view own locations) |
| `MobileFlowController` | `/v1/dealer-location` | Open (secret key auth) | Mobile app submission endpoint |
| `DealerProximityController` | `/api/v1/finder` | Open | Nearest dealer search |
| `DealershipLocationController` | `/api/v1/dealer-search` | Open | IB dealer text search |
| `IBDealerController` | `/api/v1/dealer` | Admin | IB dealer CRUD |
| `LocationController` | `/api/v1/location` | Open | Administrative location lookups |
| `CountryController` | `/api/v1/country` | Open | Country and province data |
| `GeoCodeController` | `/api/v1/geo` | Authenticated | Geocoding proxy |

### `entity/` — MongoDB Documents
All extend `MongoBaseEntity` (id, createdAt, updatedAt).

| Entity | Collection | Key Fields |
|--------|-----------|------------|
| `DealerInfoDetails` | `dealer_data` | sapDealerCode, locationType, status, locations, photo |
| `DealerSecretKey` | `dealer_secret_key` | sapDealerCode, locationType, secretKey |
| `VerifiedDealerLocation` | `verified_dealer_locations` | sapDealerCode (unique), verifiedLocationDetails[] |
| `DealershipLocation` | `dealership_location` | dealerCode, GeoJsonPoint, status, flags |
| `DealerLocationData` | — | sapDealerCode, lat/long for proximity |
| `UserX` | `user_x` | userId, role, owningMatrix |
| `Location` | `location_data` | pincode, state, district, area (compound unique) |
| `Country`, `State`, `District`, `SubDistrict`, `Division`, `Area`, `City`, `Pincode` | respective collections | Hierarchical location reference |
| `AuditLog` | — | type, message, timestamp |
| `RejectionComment` | — | code, description |

### `model/` — Data Transfer Objects
```
model/
├── request/           # Inbound API payloads (implement ApiRequest<T> for validate/sanitize)
│   └── mdp/           # MDP-specific request models
├── response/          # Outbound API payloads
│   └── google_geocode/  # Google Maps API response models
├── cache/             # In-memory cache value objects
├── mongo_projections/ # MongoDB aggregation projections
└── mongo_repo_supporter/  # Custom query result types
```

### `repository/` — Data Access
Spring Data MongoDB repositories. One per entity. No custom query implementations visible — uses derived queries and projections.

### `security/` — Authentication & Authorization
| File | Purpose |
|------|---------|
| `SecurityConfig` | Filter chain: open APIs, admin APIs (role-gated), dealer APIs (role-gated), stateless sessions |
| `RequestFilter` | JWT extraction from `Authorization` header, builds `AuthenticationDto` with authorities from UMS roles |
| `AccessDeniedHandler` | Custom 403 response |
| `DealerValidatorUtil` | Validates dealer's JWT `dealerId` matches requested sapDealerCode |

### `service/` — Business Logic
| Service | Responsibility |
|---------|---------------|
| `AdminFlowService` | Admin verification workflow, dealer lists, SMS dispatch, distance matrix |
| `DealerService` | Dealer self-service: view own info, branches, location details |
| `MobileFlowOperationalService` | Process dealer location submissions (validate, upload photo, update status) |
| `DealerProximityService` | Find nearest dealers via MDP proximity API |
| `MDPDealerService` | All MDP API interactions (dealer data, branches, filters, proximity) |
| `UMSService` | UMS token validation and contact lookup |
| `NotificationSmsDispatcherService` | SMS send and status check via Notification Service |
| `GeocodingService` | Google Maps geocoding wrapper |
| `AzureBlobOperationService` | Photo upload, presigned URL generation, file download |
| `DealerInfoDetailsService` | CRUD for DealerInfoDetails with validation |
| `DealerLocationStatusManager` | State machine transitions (no DB, pure logic) |
| `IBDealerManagementService` | IB dealer CRUD operations |
| `LocationService` | Administrative location hierarchy queries |
| `CountryService`, `StateService`, `DistrictService`, etc. | Individual location entity services |
| `AuditLogService` | Persist audit trail entries |
| `AzureB2CTokenManager` / `AzureB2CTokenGenerationService` | OAuth2 token lifecycle with caching |
| `SecretKeyManager` | Generate, validate, and expire dealer secret keys |
| `JsonHelperService` | Jackson serialization/deserialization helper |
| `CoordinateDistanceCalculatorUtilService` | Haversine distance calculation |
| `UserXService` | User lookup and ownership matrix extraction |

**Sub-packages:**
- `service/external_api_caller/` — Dedicated external API caller classes (e.g., GoogleMapsApiCallerService)
- `service/interfaces/` — Service interfaces
- `service/one_time_things/` — One-time migration/setup scripts

### `utils/` — Shared Utilities
| File | Purpose |
|------|---------|
| `Constants` | All constants: API paths, roles, URL templates, magic numbers |
| `GeneralUtils` | Validation helpers, string utils, epoch calculations, collection ops |
| `OkHttpUtil` | OkHttp GET/POST wrapper |
| `JWTUtil` | JWT payload extraction (no signature verification — trusts API-M) |
| `SecretKeyManager` | Secret key generation and validation |
| `AzureB2CTokenManager` | Token cache with expiry management |
| `ValidationException` | Custom 400-level exception |
| `RetryableException` | Triggers Spring Retry |
| `FlagUtils` | MDP flag value interpretation |
| `CsvFileParser`, `XlsxFileParser` | File import utilities |

---

## Module Dependencies (Simplified)

```
Controllers
    ↓ (inject)
Services (business logic)
    ↓ (inject)                    ↓ (inject)
Repositories (MongoDB)      External API Callers (OkHttp)
    ↓                              ↓
MongoDB Atlas               MDP / UMS / Notification / Google Maps
```

Cross-cutting:
- `AuditLogService` — injected into most services for audit trail
- `AzureB2CTokenManager` — shared by MDPDealerService, UMSService, NotificationSmsDispatcherService
- `JsonHelperService` — shared serialization across all external API callers
- `GeneralUtils` — static validation methods used everywhere

---

## Architectural Decisions

1. **No ORM, MongoDB-native** — All entities are MongoDB documents. No JPA despite initial project setup mentioning MySQL. Spring Data MongoDB handles persistence.

2. **JWT trust model** — The `RequestFilter` extracts JWT payload without signature verification, trusting that Azure API Management (APIM) has already validated the token upstream.

3. **External master data** — Dealer master data lives in MDP, not locally. This service only stores verification state and submitted locations. Every dealer operation requires an MDP API call to confirm active status.

4. **In-memory caching** — Uses `ConcurrentMapCache` (no Redis/distributed cache). Suitable for single-instance deployment but won't scale horizontally without change.

5. **Manual validation over annotations** — Uses `GeneralUtils` static methods and `ApiRequest<T>` interface instead of Jakarta Bean Validation (`@Valid`, `@NotNull`). This is a deliberate pattern throughout.

6. **OkHttp over WebClient/RestTemplate** — All external HTTP calls use OkHttp3 with a custom `OkHttpUtil` wrapper, combined with Spring Retry for resilience.

7. **Stateless security** — No sessions. JWT-based auth with role extraction from UMS token payload. Open APIs bypass the filter entirely.

8. **Decorator pattern for response filtering** — `DealerLocationDetailsResponseDecorator` / `DealerLocationDetailsResponseForDealer` hides admin-only fields when serving dealer-facing APIs.



## Tech Stack & Dependencies


# Tech: Location Master Service

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 17 |
| Framework | Spring Boot | 3.5.13 |
| Build Tool | Maven | 3.9.14 |
| Database | MongoDB Atlas | — |
| HTTP Client | OkHttp3 | 4.12.0 |
| Object Storage | Azure Blob Storage SDK | 12.32.0 |
| Caching | Spring Cache (ConcurrentMapCache) | — |
| Resilience | Spring Retry + AOP | — |
| Security | Spring Security (stateless JWT) | — |
| Serialization | Jackson + Gson 2.11.0 | — |
| Boilerplate | Lombok | — |
| API Docs | SpringDoc OpenAPI (Swagger UI) | 1.8.0 |
| Error Monitoring | Sentry (prod only) | 7.16.0 |
| Code Coverage | JaCoCo | 0.8.11 |
| Static Analysis | SonarQube | — |
| Testing | JUnit 5 + Mockito (mockito-inline 5.2.0) | — |
| File Parsing | OpenCSV 5.12.0, Apache POI 5.5.0 | — |
| Geo Utilities | pointlocation6709 4.2.1 | — |
| Utilities | Google Guava 33.5.0, Commons IO 2.16.1 | — |
| Container Runtime | Amazon Corretto 17 Alpine | 17.0.18 |

---

## Coding Conventions

### Naming
- **Packages**: lowercase, underscore-separated (`location_master`, `external_api_caller`)
- **Classes**: PascalCase. Services suffixed with `Service`, controllers with `Controller`, entities match domain name
- **Constants**: `UPPER_SNAKE_CASE`, defined in `Constants` interface as `public final` fields
- **ENUMs**: PascalCase class name, `UPPER_SNAKE_CASE` values
- **Test classes**: Mirror main class name + `Test` suffix (e.g., `AdminFlowServiceTest`)

### Class Structure
- Use `@RequiredArgsConstructor` (Lombok) for constructor injection — no `@Autowired` on fields
- Use `@Slf4j` for logging on all services and controllers
- Use `@Value` for injecting externalized config from `application.properties`
- Constants live in `Constants` interface (implemented as `public interface` with static fields)
- Utility methods live in `GeneralUtils` interface as `static` methods

### Response Envelope
All API responses are wrapped in `GeneralResponse`:
```java
GeneralResponse.builder()
    .data(payload)        // Object — the actual response data
    .errorMessage(msg)    // String — only on errors
    .time(timestamp)      // String — auto-set
    .timeTakenInMs(ms)    // Long — optional
    .serverId(id)         // String — optional
    .build();
```

### Request Validation Pattern
Request DTOs implement `ApiRequest<T>` which extends both `Sanitizeable<T>` and `Validateable<T>`:
```java
public class SomeRequest implements ApiRequest<SomeRequest> {
    @Override
    public void validate(SomeRequest request) { /* manual checks */ }

    @Override
    public void sanitizeIncomingData(SomeRequest request) { /* trim, normalize */ }
}
```
Validation is invoked manually in the service layer — no Jakarta Bean Validation annotations.

### Validation Utilities
All validation uses static methods from `GeneralUtils`:
- `notNullOrElseThrow(obj, name)` — null check
- `notNullAndNotEmptyOrElseThrow(str, name)` — string null + empty check
- `notNullAndNotEmptyAndMaxLengthCheckOrElseThrow(str, max, name)` — with length limit
- `validateLatitudeOrElseThrow(lat, name)` / `validateLongitudeOrElseThrow(lng, name)`
- `validatePincodeOrElseThrow(pincode, name)` — 6-digit Indian pincode
- `validateNoSpecialCharactersOrElseThrow(input, name)` — alphanumeric + spaces only

All throw `ValidationException` (unchecked) which maps to HTTP 400.

---

## Patterns

### Dependency Injection
- Constructor injection via Lombok `@RequiredArgsConstructor` (all dependencies are `private final`)
- `@Value` for config properties
- No field injection (`@Autowired` on fields) except one legacy case in `RequestFilter`

### External API Calls
- All external HTTP calls go through `OkHttpUtil` (wraps OkHttp3 client)
- External services use `@Retryable(value = {RetryableException.class}, maxAttempts = 3)`
- Token management via `AzureB2CTokenManager` with in-memory caching and expiry buffer (60s)
- Pattern: Service → OkHttpUtil → parse response → throw `RetryableException` on failure

### Caching
- `ConcurrentMapCache` per `CacheType` enum value (in-memory, single-instance only)
- Token cache managed manually via epoch-based expiry (`GeneralUtils.isTokenValid()`)
- No distributed cache (Redis) — designed for single-instance deployment

### Security
- Stateless JWT — no sessions (`SessionCreationPolicy.STATELESS`)
- `RequestFilter` extracts JWT payload without signature verification (trusts Azure API Management)
- Role-based access: `ADMIN_APIS` require HR Manager or Territory Manager roles; `DEALER_APIS` require Dealer Owner/Partner or Branch Manager
- Open APIs bypass the filter entirely (matched by path pattern)
- Additional ownership validation in service layer (`isUserAllowedAccessToOrElseThrow`)

### Transaction Management
- MongoDB transactions via `@Transactional` on service methods
- `TransactionManagerConfig` provides `MongoTransactionManager` bean

### Logging
- SLF4J via Lombok `@Slf4j`
- `log.info()` at method entry with parameters
- `log.error()` for exceptions
- ANSI color-coded console output (`spring.output.ansi.enabled=ALWAYS`)
- Root level: `INFO`

### Audit Trail
- `AuditLogService.saveLog()` called after significant operations
- Stores type, message, and timestamp in MongoDB

---

## Error Handling

### Exception Hierarchy
| Exception | HTTP Status | Purpose |
|-----------|-------------|---------|
| `ValidationException` | 400 | Input validation failures, business rule violations, access denied |
| `RetryableException` | (triggers retry) | External API call failures — retried up to 3–5 times |
| `HttpMessageNotReadableException` | 400 | Malformed JSON / invalid enum values |
| `Exception` (catch-all) | 500 | Unexpected errors |

### Global Exception Handler (`RestExceptionHandler`)
- `@ControllerAdvice` with `@ExceptionHandler` methods
- `ValidationException` → 400 with `GeneralResponse.errorMessage`
- Generic `Exception` → 500 with optional stack trace (controlled by `SHOW_HTTP_500_DETAILS` env var)
- Enum deserialization errors → 400 with allowed values listed

### Error Response Format
```json
{
  "data": null,
  "errorMessage": "sapDealerCode is NULL",
  "time": "Wed Jan 15 10:30:00 IST 2025"
}
```

---

## Testing

### Framework
- **JUnit 5** (`@ExtendWith(MockitoExtension.class)`)
- **Mockito** with `mockito-inline` for mocking final classes/static methods
- `@MockitoSettings(strictness = Strictness.LENIENT)` used broadly

### Patterns
- Unit tests only — no integration tests or embedded MongoDB
- `@Mock` for dependencies, `@InjectMocks` for the class under test
- `ReflectionTestUtils.setField()` for `@Value`-injected properties
- `ReflectionTestUtils.invokeMethod()` for testing private methods
- `SecurityContextHolder` mocked manually in tests requiring auth context
- Test constants in `GeoCoordinatesRelatedTestConstants`

### Coverage
- JaCoCo configured with `PACKAGE`-level line coverage check (currently minimum: `0.00` — no enforcement)
- SonarQube excludes: `entity/`, `model/`, `ENUM/`, `repository/`

### Running Tests
```bash
mvn test                    # Run all tests
mvn verify                  # Run tests + JaCoCo report
mvn test -pl .              # Single module
```

---

## Deployment

### Container
- **Multi-stage Dockerfile**:
  1. Build stage: `maven:3.9.14-amazoncorretto-17-alpine` — runs `mvn clean install`
  2. Runtime stage: `amazoncorretto:17.0.18-alpine3.23` — runs the fat JAR
- JVM flags: `-XX:MaxRAMPercentage=75`
- Timezone: `Asia/Kolkata`
- Exposed port: `8080`

### CI/CD (Azure DevOps)
- **CI Pipeline** (`uat.ci.yml`): Docker build + push to Azure Container Registry (ACR)
- **CD Pipeline** (`uat.cd.yml`): Deploy to Azure Web App Container (triggered by CI success on `uat` branch)
- **Security Pipeline** (`AST_Image_Scan_Location_Master_Pipeline.yml`): Container image scanning
- **SonarQube Pipeline** (`sonar_ci_pr_pipeline.yml`): Static analysis on PRs
- Agent pool: `self-hosted-agent-mdp`

### Environments
| Environment | Profile | Notes |
|-------------|---------|-------|
| Local | `local` | `.env` file, `SHOW_HTTP_500_DETAILS=true` |
| Dev | `dev` | — |
| UAT | `uat` | ACR: `tvsmazcmnsvcacrdev01location`, App: `tvsmazcmnsvcappuat01-location-api` |
| Prod | `prod` | Sentry enabled, Swagger disabled, detailed errors hidden |

### Configuration
- All secrets and URLs externalized via environment variables
- Spring profiles activate environment-specific `application-{profile}.properties`
- Key env vars: `MONGODB_URI`, `MDP_BASE_URL`, `GOOGLE_MAPS_GEOCODE_API_KEY`, `NOTIFICATION_*`, `UMS_*`

---

## Build Commands

```bash
# Local development
mvn spring-boot:run         # Start with .env loaded externally

# Build JAR
mvn clean install           # Compile + test + package

# Build Docker image
docker build -t location-master .

# Run Docker container
docker run -p 8080:8080 --env-file .env location-master

# Skip tests during build
mvn clean install -DskipTests
```

---

## Key Technical Decisions

1. **OkHttp over WebClient/RestTemplate** — Synchronous HTTP calls with manual retry via Spring Retry. Simpler debugging, explicit control over request/response lifecycle.

2. **Manual validation over Bean Validation** — `GeneralUtils` static methods + `ApiRequest<T>` interface instead of `@Valid`/`@NotNull`. Provides explicit control and custom error messages.

3. **Interface-based constants and utilities** — `Constants` and `GeneralUtils` are interfaces with static members, used via static import throughout the codebase.

4. **No signature verification on JWT** — Trusts Azure API Management (APIM) gateway to validate tokens upstream. The service only extracts payload claims.

5. **In-memory caching** — `ConcurrentMapCache` for simplicity. Acceptable for single-instance deployment; would need Redis for horizontal scaling.

6. **Lombok everywhere** — `@Data`, `@Builder`, `@RequiredArgsConstructor`, `@Slf4j`, `@SneakyThrows` used extensively to reduce boilerplate.

7. **Fat JAR deployment** — Single executable JAR via Spring Boot Maven plugin, deployed as a Docker container on Azure Web App.

