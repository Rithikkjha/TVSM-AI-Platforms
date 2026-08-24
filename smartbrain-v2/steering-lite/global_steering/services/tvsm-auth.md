# tvsm-auth


## Product Context


# Product: TVSM Authentication & User Management Service (auth-ninja)

## What This Service Does

Centralized Authentication, Authorization, and User Management Service (UMS) for TVS Motor's dealer network ecosystem. It provides:

- **Multi-tenant application authentication** via Azure AD B2C (OAuth2 authorization code flow)
- **User lifecycle management** for dealer employees, dealers, distributors, HO users, and support staff
- **Face recognition login** with liveness detection via Azure Face API
- **eKYC verification** (PAN, Driving License, Bank Account) via Karza API
- **Role-based access control** with hierarchical roles, permissions, and reporting structures
- **Dealership and branch management** integrated with MDP (Master Data Platform)
- **Event-driven architecture** publishing user lifecycle events via Azure Service Bus

## Domain Entities

### Core Authentication
- **Application** — Registered client apps with client credentials, login policies, auth methods (FID/OTP/UID/TVSM), redirect URIs, and branding (title, logo)
- **LoginPolicies** — B2C user flow policies per country code per application, with default fallback
- **AuthenticationMethod** — Enum: FACE_ID, PHONE_OTP, USERID_PWD, TVSM_LOGIN

### User Management
- **UserDetails** (abstract, single-table inheritance via `db_user_type`) — Core user entity with subtypes:
  - `Dealer` — Dealership owner/partner
  - `DealerEmployees` — Staff working at dealerships
  - `HOUser` — Head Office users
  - `SupportUser` — Support staff
  - `Distributor` — Distribution partners
  - `TvsmUser` — Internal TVSM users
- **UserFaceDetails** — Azure Face API person/group/face IDs for biometric login
- **UserLoginAudit** — Login history with auth method and app context
- **ConflictedUsers** — Tracks conflicts when phone/face/eKYC matches existing users across dealers

### Organizational Hierarchy
- **Role** — Functional roles with permissions, designations, reporting role mappings, application mappings, and flags (multipleBranchAccess, canBePassiveUser, bankDetailsMandatory, specializationMultiMandatory)
- **Permission** — Granular permissions mapped to roles (many-to-many)
- **Department** → **Group** → **Role** → **Type** / **Specialization** — Hierarchical organizational structure
- **Designation** — Job titles within roles (with default designation support)
- **RoleHierarchy** — Parent-child role relationships
- **UserBaseRoleMapping** — User-to-role assignment with department, group, type, specializations, and reporting user
- **UserReportingRoleMapping** — Reporting manager assignment per role

### Dealership & Branch
- **Dealership** — Dealer organizations (name, address, dealer code, GST, type: IB/EV/etc.)
- **UserDealershipMapping** / **UserBranchMapping** — User-to-dealership and branch assignments

### eKYC & Consent
- **UserEkycDetails** — Verification records (PAN/DL/BANK) with status and vendor response
- **UserConsentDetails** — Consent acceptance/rejection records
- **EkycType** — Enum: PAN, DL, BANK

### Profile Details
- **BankDetails** — Account number, IFSC, beneficiary, UPI, PAN, consent/passbook references
- **ProfessionalDetails** — Employee ID, joining date, last working date, driving license
- **EducationDetails**, **LastEmployeeDetails**, **TrainingCertification** — Extended profile data
- **Address** — Multi-line address with city, state, country, zip

### Dynamic Forms
- **FormSegment** / **FormSubsegment** / **FormAttribute** / **FormMapping** — Configurable form definitions per role

## External Integrations

| Integration | Purpose | Client |
|---|---|---|
| **Azure AD B2C** | OAuth2 auth flows, token validation (JWKS), session management | WebClient + java-jwt |
| **Microsoft Graph API** | B2C user CRUD (create, delete, patch, query by identity) | GraphServiceClient (SDK) |
| **Azure Face API** | Face detect, identify, train, liveness verification, person group management | OkHttpClient + Azure Face SDK |
| **Azure Blob Storage** | Profile photos, consent docs, passbooks, logo images | Azure Blob SDK |
| **Azure Service Bus** | Publish UmsUserActivated/UmsUserUpdated events | ServiceBusSenderClient |
| **Karza API** | eKYC: PAN validation, DL validation, bank account verification, name matching | OkHttpClient |
| **MDP (Master Data Platform)** | Dealer info, branch listings | OkHttpClient |
| **Notification Service** | SMS notifications (consent links, face login reminders) | OkHttpClient |

## Business Rules

### Authentication & Login
- Applications define allowed auth methods (comma-separated: FID, OTP, UID, TVSM)
- Login policies are resolved by country code with a default fallback
- Token validation uses RSA public key from B2C JWKS endpoint (keys are cached)
- Client credentials flow available for inter-service token generation
- Employee confirmation: periodic face login required for certain roles/apps (configurable days threshold)

### User Lifecycle (Status Machine)
```
PENDING_ACTIVE → ACTIVE → PASSIVE → INACTIVE
                    ↑         |
                    └─────────┘ (re-activation)
```
- **Registration**: User created in PENDING_ACTIVE. Face + phone uniqueness checked. Conflicts tracked if match found in different dealer.
- **Activation**: Requires consent + eKYC (if app has eKYC enabled). Generates employee ID and password. Registers in B2C. Publishes UmsUserActivatedEvent.
- **Passive**: Auto-transition after configurable unused days. B2C account disabled. Can be re-activated.
- **Inactive**: B2C user deleted. Triggered by admin action, cron job, or conflict resolution.
- **Conflict Resolution**: When phone/face/eKYC matches across dealers, conflicts are tracked and resolved by the existing user's dealer.

### Face Recognition
- Face validation on registration: checks position, blur, noise, exposure, occlusion (mask/hat), head pose, eye openness, face area ratio
- Face identification uses Azure Large Person Groups with configurable confidence threshold
- Liveness verification via Azure Face SDK session-based flow
- One face per active user enforced; duplicate face detection across dealers

### eKYC
- Consent must be accepted before verification
- PAN/DL/BANK verified via Karza API with name matching
- If verified document matches another user, conflict is created
- Each type can only be verified once per user

### Auto-Generated Credentials
- Employee ID format: `{dealerCode}{sequence}` (5-digit zero-padded)
- Password format: `{firstName}@{lastFourDigitsOfPhone}#66`
- Passwords encrypted with AES-GCM before storage

### Scheduled Jobs
- Deactivate PENDING_ACTIVE users after configurable days
- Deactivate PASSIVE users after configurable days
- Move unused ACTIVE users to PASSIVE after configurable days
- Send SMS reminders for face login at configurable intervals



## Code Structure


# Structure: Annotated Directory Layout & Architecture

## Project Root

```
tvsm-auth/
├── pom.xml                          # Maven build (Spring Boot 3.5.7, Java 17)
├── Dockerfile                       # Multi-stage: Maven build → Amazon Corretto 17 Alpine
├── api-specs.yml                    # OpenAPI 3.0 spec for public-facing auth endpoints
├── README.md                        # Setup instructions (MySQL, env vars, mvn spring-boot:run)
├── ci-pipeline.yaml                 # Azure DevOps CI (triggered after SonarQube scan)
├── cd-pipeline.yaml                 # Azure DevOps CD (dev → UAT → prod with approvals)
├── cd-norton-pipeline.yaml          # Norton-specific CD pipeline
├── auth-ninja-sonar-scan.yaml       # SonarQube analysis pipeline
├── sonar_ci_pr_pipeline.yml         # PR-level sonar scan
├── AST_*.yml                        # AST image security scan pipelines
├── script/python/                   # Utility scripts (token generation, bulk user create/update)
└── src/
    ├── main/
    │   ├── java/com/tvsmotor/tvsmauth/
    │   └── resources/
    │       └── application.properties   # Externalized config (env vars for all secrets)
    └── test/
        ├── java/com/tvsmotor/tvsmauth/  # Unit tests mirroring main structure
        └── resources/
            └── application-test.properties
```

## Source Layout (Feature-Based Modules)

```
src/main/java/com/tvsmotor/tvsmauth/
├── AuthApplication.java                 # @SpringBootApplication entry point
│
├── aop/                                 # Cross-cutting concerns
│   ├── annotations/
│   │   └── Authenticate.java           # Custom annotation for token validation
│   └── AuthenticateAspect.java         # AOP aspect: validates Authorization + x-client-id headers
│
├── applications/                        # Authentication & Application module
│   ├── ApplicationService.java          # Service interface
│   ├── ApplicationServiceImpl.java      # OAuth2 flows, token validation, B2C integration
│   ├── controller/
│   │   ├── ApplicationController.java   # Public auth endpoints (/token, /callback, /logout, /face-login)
│   │   ├── ApplicationExceptionHandler.java  # @ControllerAdvice global exception handler
│   │   └── ValidationHandler.java       # Bean validation error formatting
│   ├── dto/                             # Auth request/response DTOs
│   ├── entity/
│   │   ├── Application.java            # Client app registration
│   │   ├── LoginPolicies.java          # Country-specific B2C policies
│   │   ├── AuthenticationMethod.java   # FID/OTP/UID/TVSM enum
│   │   ├── BaseEntity.java            # Auditing fields (createdAt, updatedAt, createdBy, updatedBy)
│   │   └── CountryCodeEnum.java       # Country → phone code mapping
│   ├── exception/                       # Domain exceptions
│   │   ├── CustomException.java        # General business exception (with HTTP status)
│   │   ├── TokenException.java         # JWT validation failures
│   │   ├── ApplicationNotFoundException.java
│   │   ├── LoginRedirectException.java # Employee confirmation redirect
│   │   ├── EKycVerificationException.java
│   │   └── UserFaceNotLiveException.java
│   ├── gateway/
│   │   ├── AzureB2CGateway.java        # Token validation (JWKS), token generation (client_credentials)
│   │   └── representation/             # OpenID config, key beans for JWKS
│   └── repository/
│       └── ApplicationRepository.java   # JPA repository
│
├── config/                              # Spring configuration
│   ├── SecurityConfig.java             # SecurityFilterChain: stateless, JWT filter, URL authorization
│   ├── JwtTokenFilter.java            # OncePerRequestFilter: extracts B2C user, sets SecurityContext
│   ├── AccessDeniedHandler.java       # Custom 403 handler
│   ├── GraphServiceClientConfig.java  # Microsoft Graph SDK client bean
│   ├── AzureServiceBusConfig.java     # ServiceBusSenderClient bean (managed identity)
│   ├── AzureBlobStorageConfig.java    # BlobContainerClient bean
│   ├── WebClientConfiguration.java    # WebClient for B2C token endpoint
│   ├── OkHttpClientConfig.java        # OkHttpClient for Face API, MDP, Notification
│   ├── AppCacheManager.java           # In-memory cache (JWT keys)
│   ├── CacheClearScheduler.java       # Periodic cache eviction
│   ├── SwaggerConfig.java            # OpenAPI/Swagger UI config
│   ├── AsyncConfig.java              # @EnableAsync thread pool
│   ├── AuthenticationDto.java        # Security context DTO (extends AbstractAuthenticationToken)
│   └── BranchInfoConverter.java      # JPA AttributeConverter for JSON column
│
├── support/                             # Shared utilities
│   ├── AppConstants.java              # URL mappings, regex patterns, format strings, file paths
│   ├── AppUtils.java                  # Token parsing, logged-in user helpers, string utils
│   ├── BlobStorageUtil.java           # Upload, download, pre-signed URL generation
│   ├── EncryptUtil.java              # AES-GCM encryption/decryption for passwords
│   ├── PasswordUtil.java            # Password generation from name + phone
│   ├── JsonUtil.java                # Jackson serialize/deserialize helpers
│   ├── MessageUtil.java             # i18n message resolution
│   ├── SanitizeUtil.java            # Input sanitization
│   ├── ValidationUtil.java          # Multipart file validation (type, size)
│   ├── AsyncJobService.java         # Async job submission with delay
│   └── DownloadFileDto.java         # File download response wrapper
│
└── user/                                # User management domain (largest module)
    ├── profile/                         # Core user profile management
    │   ├── api/                         # REST controllers
    │   │   ├── UserProfileController.java    # CRUD, registration, status changes, face/phone verification
    │   │   ├── AdminController.java          # Admin onboarding (TVSM users, distributors)
    │   │   ├── DealerController.java         # Dealer/branch operations
    │   │   ├── ConsentController.java        # eKYC consent endpoints
    │   │   └── UserApplicationController.java # App-to-user assignment
    │   ├── dto/                         # ~60+ request/response DTOs
    │   ├── entity/                      # JPA entities
    │   │   ├── UserDetails.java         # Abstract base (single-table inheritance)
    │   │   ├── DealerEmployees.java     # Dealer staff subtype
    │   │   ├── Dealer.java              # Dealer owner subtype
    │   │   ├── UserBaseRoleMapping.java # Role assignment join entity
    │   │   ├── UserDealershipMapping.java / UserBranchMapping.java
    │   │   ├── UserFaceDetails.java     # Face recognition data
    │   │   ├── UserLoginAudit.java      # Login audit trail
    │   │   ├── ConflictedUsers.java     # Cross-dealer conflict tracking
    │   │   ├── BankDetails.java, ProfessionalDetails.java, Address.java
    │   │   └── UserApplicationMapping.java
    │   ├── enums/                       # Status, UserType, Gender, MaritialStatus
    │   ├── ekyc/                        # eKYC sub-module
    │   │   ├── api/EkycController.java
    │   │   ├── dto/                     # ValidationRequest/Response, ConsentRequest/Response
    │   │   ├── entity/                  # UserEkycDetails, UserConsentDetails, EkycType
    │   │   ├── factory/EkycValidationServiceFactory.java  # Strategy pattern for vendors
    │   │   ├── repository/
    │   │   └── service/
    │   │       ├── EkycService.java     # Orchestrates verification flow
    │   │       ├── EkycValidationService.java  # Interface for vendor implementations
    │   │       ├── KarzaEkycValidationService.java  # Karza API integration
    │   │       ├── ConsentService.java  # Consent management
    │   │       └── AsyncService.java    # Async consent SMS
    │   ├── factory/UserTypeServiceFactory.java  # Factory for user-type-specific logic
    │   ├── repository/                  # 20+ JPA repositories
    │   ├── scheduler/                   # Cron jobs
    │   │   ├── PendingActiveConversion.java   # Auto-deactivation (currently disabled)
    │   │   └── NotificationReminder.java      # Face login SMS reminders
    │   └── service/
    │       ├── UserProfileService.java        # Core service (~1500 lines): registration, activation, deactivation, conflict resolution
    │       ├── AdminService.java              # Admin user onboarding
    │       ├── DealerEmployeeProfileService.java  # Listing/pagination for dealer employees
    │       ├── DealerProfileService.java      # Branch/dealer queries
    │       ├── UserOnboardFlxService.java     # Bulk onboarding via CSV
    │       ├── UserApplicationMappingService.java
    │       └── EmployeeIdGeneratorService.java # Sequential ID generation
    │
    ├── gateway/                         # External service clients
    │   ├── AzureGatewayB2C.java        # MS Graph: user create/delete/patch/query
    │   ├── FaceRecognitionService.java  # Azure Face API: detect, identify, train, validate, liveness
    │   ├── MDPServiceClient.java       # MDP: dealer info, branch listings
    │   ├── NotificationGateway.java    # Notification service: SMS
    │   ├── UMSServiceClient.java       # Inter-service token generation
    │   ├── AzureServiceBusPublisher.java # Event publishing to Service Bus topic
    │   ├── event/                       # Event DTOs
    │   │   ├── UmsUserActivatedEvent.java
    │   │   └── UmsUserUpdatedEvent.java
    │   └── models/                      # Gateway request/response models
    │
    ├── dealership/                      # Dealership management
    │   ├── dto/, entity/, enums/, repository/, service/
    │
    ├── department/                      # Department CRUD
    │   ├── api/, dto/, entity/, repository/, service/
    │
    ├── group/                           # Group CRUD (under departments)
    │   ├── api/, dto/, entity/, repository/, service/
    │
    ├── role/                            # Role management
    │   ├── api/RoleController.java     # Create, update, fetch types/specializations/designations
    │   ├── dto/, entity/, enums/, repository/, service/
    │
    ├── permission/                      # Permission entity & repository
    ├── designation/                     # Designation management
    ├── specialization/                  # Specialization management
    ├── type/                            # Type management
    └── dynamicforms/                    # Dynamic form configuration
        ├── api/, dto/, entity/, repository/, service/, util/
```

## Module Dependencies

```
ApplicationController
    └── ApplicationServiceImpl
        ├── ApplicationRepository
        ├── AzureB2CGateway (token validation/generation)
        ├── UserProfileService (employee confirmation check)
        ├── BlobStorageUtil (logo images)
        └── WebClient (B2C token endpoint)

UserProfileController
    └── UserProfileService
        ├── DealerEmployeeRepository / DealerRepository / UserDetailsRepository
        ├── AzureGatewayB2C (B2C user CRUD via Graph API)
        ├── FaceRecognitionService (face detect/identify/train)
        ├── AzureServiceBusPublisher (event publishing)
        ├── BlobStorageUtil (profile photos)
        ├── MDPServiceClient (dealer/branch info)
        ├── RoleService, DepartmentService, GroupService, TypeService, SpecializationService
        ├── EmployeeIdGeneratorService
        └── DealershipService

EkycController
    └── EkycService
        ├── EkycValidationServiceFactory → KarzaEkycValidationService
        ├── UserProfileService (user lookup, conflict detection)
        └── UserEkycDetailsRepository

JwtTokenFilter (SecurityFilterChain)
    └── UserProfileService.fetchUserDetailsFromB2CId()
        → Sets AuthenticationDto in SecurityContext

AuthenticateAspect (@Authenticate annotation)
    └── ApplicationService.validateToken()
```

## Architectural Decisions

1. **Feature-based package structure** — Each domain concept (role, department, dealership, etc.) is a self-contained module with its own api/dto/entity/repository/service layers. The `user/profile` module is the largest and most complex.

2. **Single Table Inheritance for users** — All user types share one `user_details` table with a `db_user_type` discriminator. Simplifies queries but results in wide table with nullable columns.

3. **Stateless JWT security** — No server-side sessions. JwtTokenFilter extracts B2C user ID from token, loads user from DB, and populates Spring SecurityContext with roles/authorities.

4. **Dual HTTP clients** — WebClient (reactive) for B2C token operations; OkHttpClient (blocking) for Face API, MDP, and Notification calls. This is a pragmatic split, not a design inconsistency.

5. **Event-driven downstream communication** — User lifecycle changes publish events to Azure Service Bus topic. Downstream services consume asynchronously. Events carry full user snapshot (not just deltas).

6. **AOP-based authentication for public endpoints** — The `@Authenticate` annotation validates tokens on specific endpoints that bypass the main security filter (e.g., endpoints behind APIM).

7. **Factory pattern for extensibility** — `EkycValidationServiceFactory` allows swapping eKYC vendors. `UserTypeServiceFactory` handles user-type-specific registration logic.

8. **Conflict detection as first-class concept** — Cross-dealer conflicts (same phone/face/eKYC) are tracked in a dedicated table with resolution workflows rather than simply rejecting duplicates.

9. **Externalized configuration** — All secrets and environment-specific values are injected via environment variables. No hardcoded credentials. Spring profiles control environment selection.

10. **Shared base entity** — `BaseEntity` provides `createdAt`, `updatedAt`, `createdBy`, `updatedBy` audit fields inherited by all entities.



## Tech Stack & Dependencies


# Tech: Stack, Conventions, Patterns & Operations

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Java | 17 |
| Framework | Spring Boot | 3.5.7 |
| Security | Spring Security | (managed by Boot) |
| ORM | Spring Data JPA + Hibernate | (managed by Boot) |
| Database | MySQL | Production |
| Database (test) | H2 | In-memory |
| HTTP (reactive) | Spring WebFlux (WebClient) | (managed by Boot) |
| HTTP (blocking) | OkHttp | (managed transitively) |
| Validation | Jakarta Bean Validation | (managed by Boot) |
| Auth Library | MSAL4J | 1.20.1 |
| Graph SDK | Microsoft Graph | 5.79.0 |
| Azure Identity | azure-identity | 1.18.1 |
| Service Bus | azure-messaging-servicebus | 7.17.4 |
| Blob Storage | azure-storage-blob | 12.25.2 |
| Face API | azure-ai-vision-face | 1.0.0-beta.2 |
| JWT | java-jwt (Auth0) | 4.4.0 |
| Retry | Spring Retry | (managed by Boot) |
| CSV | OpenCSV | 5.12.0 |
| API Docs | springdoc-openapi | 2.8.13 |
| Boilerplate | Lombok | (managed by Boot) |
| Build | Maven | 3.9.12 |
| Container | Docker (Amazon Corretto 17 Alpine) | — |
| CI/CD | Azure DevOps Pipelines | — |
| Code Quality | SonarQube + JaCoCo | 0.8.11 |
| Monitoring | Sentry | — |

## Coding Conventions

### General Style
- **Lombok everywhere**: `@Data`, `@Builder`, `@RequiredArgsConstructor`, `@Slf4j`, `@SneakyThrows` on nearly all classes
- **Constructor injection** via `@RequiredArgsConstructor` (no `@Autowired` on fields except in config classes)
- **Static imports** used heavily for constants and utility methods
- **Slf4j logging** with structured messages: `log.info("Action description: [{}]", value)`

### Naming Conventions
- **Packages**: lowercase, feature-based (`user.profile`, `user.gateway`, `applications`)
- **Controllers**: `{Feature}Controller.java` with `@RequestMapping(value = CONSTANT_PATH)`
- **Services**: Interface + Impl for `ApplicationService`; direct `@Service` classes elsewhere
- **Repositories**: `{Entity}Repository.java` extending `JpaRepository`
- **DTOs**: `{Name}Dto.java`, `{Name}Request.java`, `{Name}Response.java`
- **Entities**: Plain domain names (`Role`, `Application`, `UserDetails`)
- **Constants**: `UPPER_SNAKE_CASE` in `AppConstants.java`
- **Enums**: PascalCase values (`PENDING_ACTIVE`, `DEALER_EMPLOYEE`)

### Controller Patterns
```java
@RestController
@RequiredArgsConstructor
@RequestMapping(value = CONSTANT_URL)
@Slf4j
public class XxxController {
    
    @GetMapping("/endpoint")
    public ResponseEntity<ResponseDto> method(@RequestParam String param) {
        log.info("GET: /api/v1/xxx/endpoint, method: method()");
        return ResponseEntity.ok(service.doWork(param));
    }
}
```
- Always log the HTTP method, path, and method name at entry
- Return `ResponseEntity<T>` with explicit status codes
- Use `@Valid` for request body validation
- Multipart uploads validated via `ValidationUtil.validateAndSanitizeMultipart()`

### Service Patterns
- Business logic concentrated in service classes (not controllers)
- `@Transactional` used selectively (not blanket)
- `@Retryable` for operations with transient failures (e.g., user activation)
- Static factory methods on DTOs: `fromDto()`, `toDto()`, `toEvent()`
- Null checks via `Objects.isNull()` / `Objects.nonNull()` and custom `isNullOrEmptyString()`

### Entity Patterns
- `BaseEntity` superclass with audit fields (`createdAt`, `updatedAt`, `createdBy`, `updatedBy`)
- `@DynamicInsert` / `@DynamicUpdate` on entities to avoid null column updates
- `@SuperBuilder` for inheritance hierarchies
- JSON columns via `@Convert(converter = BranchInfoConverter.class)`
- `@EqualsAndHashCode(callSuper = true)` on entities extending BaseEntity

### DTO Patterns
- Static factory methods: `ApplicationResponseDto.fromDto(entity, extraData)`
- Event DTOs with `toEvent(userDetails, applications, dealershipDetails)` builders
- Request DTOs with `fromDto()` converting to entity

## Error Handling

### Exception Hierarchy
```
RuntimeException
├── CustomException              # General business errors (message + optional HTTP status)
├── TokenException               # JWT validation failures (401)
├── ApplicationNotFoundException # App not found (400/404)
├── LoginRedirectException       # Employee confirmation redirect (carries appId + redirect URL)
├── EKycVerificationException    # eKYC vendor errors
└── UserFaceNotLiveException     # Face liveness check failure
```

### Global Exception Handler (`ApplicationExceptionHandler`)
- `@ControllerAdvice` catches all exceptions
- Returns `ErrorResponse` DTO with timestamp, HTTP status, and message
- `ValidationHandler` formats bean validation errors into readable messages

### Error Response Format
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "status": 400,
  "message": "User is already existing with the phone number."
}
```

### Conventions
- Throw `CustomException` for business rule violations with descriptive messages
- Use `MessageUtil` for i18n message resolution (keys like `profile.user-not-exists-id`)
- Log warnings before throwing exceptions
- Gateway errors wrapped in `CustomException` with original message
- B2C user creation failures trigger rollback (delete created B2C user)

## Patterns In Use

| Pattern | Where | Purpose |
|---|---|---|
| **Layered Architecture** | All modules | Controller → Service → Repository/Gateway |
| **Single Table Inheritance** | `UserDetails` hierarchy | All user types in one table |
| **Factory** | `EkycValidationServiceFactory`, `UserTypeServiceFactory` | Vendor/type-specific logic |
| **Strategy** | `EkycValidationService` interface | Swappable eKYC vendors |
| **AOP** | `AuthenticateAspect` | Cross-cutting token validation |
| **Event Publishing** | `AzureServiceBusPublisher` | Async downstream notification |
| **Builder** | All DTOs and entities (Lombok) | Immutable construction |
| **Repository** | Spring Data JPA | Data access abstraction |
| **Filter Chain** | `JwtTokenFilter` | Request-level authentication |
| **Retry** | `@Retryable` on activation | Transient failure recovery |
| **Async** | `@Async`, `AsyncJobService` | Non-blocking operations |
| **Caching** | `AppCacheManager` | JWT key caching |
| **Scheduler** | `@Scheduled` cron jobs | Periodic user lifecycle transitions |

## Testing

### Framework & Tools
- **JUnit 5** (via `spring-boot-starter-test`)
- **Mockito** (mockito-inline 5.2.0) for mocking
- **H2** in-memory database for repository/integration tests
- **Test profile**: `application-test.properties`

### Test Structure
- Tests mirror the main source tree under `src/test/java/com/tvsmotor/tvsmauth/`
- Test factories exist for creating test data (ApplicationFactory, ProfileFactory, GroupFactory, etc.)
- Service tests mock repositories and gateway clients
- Controller tests use MockMvc or direct service mocking

### Coverage Requirements
- **JaCoCo** enforces minimum **40% line coverage** per package
- Excluded from coverage: `com/tvsmotor/tvsmauth/config/**`, `AuthApplication.java`
- Coverage report generated during `prepare-package` phase

### Running Tests
```bash
mvn test                    # Run all tests
mvn verify                  # Run tests + JaCoCo coverage check
mvn jacoco:report           # Generate coverage report
```

## Build & Deployment

### Local Development
```bash
# Required environment variables
export ACTIVE_ENVIRONMENT=local
export DB_URI=jdbc:mysql://localhost:3306/tvs_auth
export DB_USERNAME=<username>
export DB_PASSWORD=<password>
export B2C_TENANT_NAME=<tenant>
export B2C_TENANT_ID=<tenant-id>
# ... (see application.properties for full list)

# Run
mvn spring-boot:run
```

### Docker Build
```dockerfile
# Stage 1: Maven build (amazoncorretto-17-alpine)
# Stage 2: Runtime (amazoncorretto:17.0.17-alpine3.19)
# JVM: -Xms512m -XX:MaxRAMPercentage=75.0
# Timezone: Asia/Kolkata
# Port: 8080
```

```bash
docker build -t tvsm-auth .
docker run -p 8080:8080 --env-file .env tvsm-auth
```

### CI/CD Pipeline (Azure DevOps)

```
Code Push → SonarQube Scan → CI Build (Docker image) → AST Security Scan
    → Deploy to Dev (auto)
    → Manual Approval → Deploy to UAT
    → Manual Approval → Deploy to Prod
```

- **CI** (`ci-pipeline.yaml`): Triggered after SonarQube scan passes on `develop`/`main_IB` branches. Uses shared `build-template.yml` from DevOps repo.
- **CD** (`cd-pipeline.yaml`): Deploys via Helm charts to Kubernetes. Manual approval gates for UAT and prod.
- **Security**: AST image scan pipelines run on Docker images before deployment.
- **Helm chart name**: `auth-ninja` (matches service name in pipelines)

### Environment Configuration
All configuration is externalized via environment variables. Key categories:

| Category | Variables |
|---|---|
| Database | `DB_URI`, `DB_USERNAME`, `DB_PASSWORD`, `SHOW_SQL` |
| Azure B2C | `B2C_TENANT_NAME`, `B2C_TENANT_ID`, `B2C_ISSUER`, `UMS_CLIENT_ID`, `UMS_CLIENT_SECRET` |
| Azure Face | `AZURE_FACE_URL`, `AZURE_FACE_SUBSCRIPTION` |
| Azure Blob | `AZURE_BLOB_CONNECTION`, `PRE_SIGNED_URL_EXPIRY_HOURS` |
| Azure Service Bus | `AZURE_SERVICE_BUS_NAMESPACE`, `AZURE_SERVICE_BUS_TOPIC_NAME`, `AZURE_CLIENT_ID` |
| MDP | `MDP_BASE_URL`, `MDP_CLIENT_ID`, `MDP_CLIENT_SECRET` |
| Karza (eKYC) | `KARZA_API_BASE_URL`, `KARZA_API_KEY` |
| Notification | `NOTIFICATION_BASE_URL`, `NOTIFICATION_CONSENT_TEMPLATE` |
| User Lifecycle | `MAX_PENDING_DAYS`, `MAX_PASSIVE_DAYS`, `MAX_UNUSED_DAYS`, `MAX_FACE_LOGIN_DAYS` |
| Security | `FACE_CONFIDENCE_THRESHOLD`, `USER_ONBOARD_AUTHORITIES`, `EMPLOYEE_CONFIRMATION` |

### Database
- **MySQL** with HikariCP connection pool (max 50 connections, min 10 idle)
- Schema managed by Hibernate (DDL auto mode configured per environment)
- No Flyway/Liquibase migrations visible — schema likely managed externally or via `update` mode

### Monitoring & Observability
- **Sentry** for error tracking (DSN configured, 100% trace sample rate in non-prod)
- **Health endpoint**: `GET /v1/app/test/health` returns beacon, profile, version, timestamp
- **Structured logging** via Slf4j with contextual parameters

## Security Considerations

- All secrets externalized as environment variables (never in source)
- Passwords encrypted with AES-GCM before database storage
- JWT tokens validated against B2C JWKS public keys (RSA256)
- File uploads validated for type and size (`ALLOWED_FILE_TYPES_IMAGE`, `ALLOWED_FILE_TYPES_DOCUMENT`)
- Input sanitization via `SanitizeUtil`
- HTTPS enforced for token endpoints (`SecurityException` if not HTTPS)
- CORS and CSRF disabled (API-only service behind APIM)
- Stateless sessions (no server-side session state)
- B2C user creation rolled back on activation failure
- Swagger UI commented out for production security (available for dev only)

