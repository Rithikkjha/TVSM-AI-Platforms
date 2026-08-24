# tvsm-otp-service


## Product Context


# Product: TVSM OTP Service

## Overview

A multi-tenant OTP (One-Time Password) microservice that generates and verifies 6-digit OTPs delivered via configurable channels (EMAIL, MOBILE, WHATSAPP). OTPs are stored in Redis with TTL-based expiry, and the service enforces rate limiting and brute-force protection per entity.

> **Note:** OTP delivery (SMS/email sending) is not yet integrated. The OTP value is currently returned directly in the API response.

## Domain Entities

| Entity | Description |
|--------|-------------|
| `OtpRequest` | Incoming generation request containing a list of channels, country code, and optional client configs. Includes validation logic for email and mobile. |
| `OtpResponse` | Per-channel generation result: channelType, entity, message, HTTP status. |
| `OtpVerify` | Verification request: channel type, entity, and 6-digit OTP. |
| `OtpVerificationResponse` | Verification result: success flag, result message, error code. |
| `Channel` | Individual channel entry: channel type + entity + client reference. |
| `ChannelConfig` | Per-channel validation rules: minLength, maxLength, regex, countryCodes. |
| `ClientConfig` | Per-client business rules: otpExpiryMinutes, maxOtpRequestsPerHour, blockDurationMinutes, requestCount, channel map. |
| `ApiResponseWrapper<T>` | Generic API envelope: timestamp, code, message, data payload. |
| `OtpChannelType` | Enum: MOBILE, EMAIL, WHATSAPP |
| `OtpEntityType` | Enum: EMAIL, MOBILE |

## Integrations

| System | Purpose |
|--------|---------|
| **Redis** (Lettuce + SSL) | OTP storage, rate-limiting counters, block flags, attempt tracking |
| **Azure Key Vault** | RSA-OAEP encryption/decryption of entity values (phone/email) before storing as Redis keys |
| **JWT (Bearer token)** | Authentication — extracts `roles` claim from payload. Requires `otp.api` role. No signature verification (Base64 decode only). |
| **Spring Actuator** | Health and info endpoints (`/actuator/health`, `/actuator/info`) |

## Business Rules

### OTP Generation
- OTP is 6 digits, generated via `SecureRandom`
- OTP expiry is configurable per client (e.g., 2 min for `otp.api`, 5 min for `LMS`)
- Entity values are encrypted via Azure Key Vault before use as Redis keys

### Rate Limiting
- Max N OTP requests per hour per entity per channel (configurable per client)
- After exceeding the rate limit, the entity is blocked for a configurable duration (30–60 min)

### OTP Verification
- Max 3 verification attempts before the entity is blocked
- On successful verification, OTP and attempt keys are cleaned up from Redis
- On block, OTP and attempt keys are deleted and a block key is set with TTL

### Entity Validation
- **Email:** validated via configurable regex
- **Mobile:** validated via regex + libphonenumber + country code whitelist (per client)

### Redis Key Structure
- `OTP:{client}:{channel}:{encryptedEntity}` — stores the OTP value
- `OTP:{client}:{channel}:{encryptedEntity}:attempts` — verification attempt counter
- `REQ_COUNT:{client}:{channel}:{encryptedEntity}` — generation request counter
- `BLOCKED:{client}:{channel}:{encryptedEntity}` — block flag

## Configured Clients (otp-config.json)

| Client | Expiry | Max Requests/Hour | Block Duration | Channels |
|--------|--------|-------------------|----------------|----------|
| `otp.api` | 2 min | 5 | 30 min | MOBILE (+1, +91, +44), EMAIL |
| `LMS` | 5 min | 3 | 60 min | MOBILE (+49, +33), EMAIL |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/otp/api/generate` | Generate OTP for one or more channels |
| POST | `/otp/api/verify` | Verify an OTP for a given entity |

Both endpoints require a `Bearer` token in the `Authorization` header with the `otp.api` role.



## Code Structure


# Structure: TVSM OTP Service

## Directory Layout

```
tvsm-otp-service/
├── .kiro/steering/              # Kiro steering files (this documentation)
├── azure-pipelines/             # Azure DevOps pipeline definitions
│   ├── ast-image-scan-otp-pipeline.yaml   # Container image security scanning
│   ├── ast-otp-prod-pipeline.yaml         # Production deployment
│   ├── ast-otp-uat-pipeline.yaml          # UAT deployment
│   ├── cd-pipeline.yaml                   # Continuous delivery
│   ├── ci-pipeline.yaml                   # Continuous integration
│   └── sonar.yaml                         # SonarQube analysis
├── src/
│   ├── main/
│   │   ├── java/com/otp/
│   │   │   ├── OTPService.java            # Spring Boot application entry point
│   │   │   ├── controller/
│   │   │   │   └── OtpController.java     # REST endpoints: /api/generate, /api/verify
│   │   │   ├── service/
│   │   │   │   └── OtpService.java        # Core business logic (generation, verification, rate limiting)
│   │   │   ├── config/
│   │   │   │   ├── ConfigLoader.java      # (Commented out) Azure Blob → Redis config loader
│   │   │   │   ├── JwtConfig.java         # (Empty) JWT config placeholder
│   │   │   │   ├── RedisConfig.java       # Redis connection factory + template (Lettuce, SSL)
│   │   │   │   └── SwaggerConfig.java     # SpringDoc OpenAPI grouped API config
│   │   │   ├── model/                     # DTOs, enums, request/response objects
│   │   │   │   ├── ApiResponseWrapper.java
│   │   │   │   ├── Channel.java
│   │   │   │   ├── ChannelConfig.java
│   │   │   │   ├── ClientConfig.java
│   │   │   │   ├── OtpChannelType.java
│   │   │   │   ├── OtpEntityType.java
│   │   │   │   ├── OtpRequest.java
│   │   │   │   ├── OtpResponse.java
│   │   │   │   ├── OtpResponseDetails.java
│   │   │   │   ├── OtpVerificationResponse.java
│   │   │   │   └── OtpVerify.java
│   │   │   ├── exception/
│   │   │   │   ├── ConfigurationException.java   # RuntimeException for config load failures
│   │   │   │   └── GlobalExceptionHandler.java   # @RestControllerAdvice — centralized error handling
│   │   │   └── util/
│   │   │       ├── AzureKeyVaultUtil.java  # RSA-OAEP encrypt/decrypt via Azure Key Vault
│   │   │       └── JwtUtil.java            # Static JWT parsing (role extraction, token verification)
│   │   └── resources/
│   │       ├── application.properties      # App config (env var placeholders for Redis, Azure, port)
│   │       └── otp-config.json             # Per-client OTP rules (expiry, rate limits, channels)
│   └── test/java/com/otp/                  # Unit tests (JUnit 5 + Mockito)
│       ├── config/
│       ├── controller/
│       ├── exception/
│       ├── model/
│       ├── service/
│       └── util/
├── Dockerfile                   # Multi-stage production build (Maven → Temurin JRE)
├── Dockerfile.build             # Standalone build image (Temurin 21 + Maven)
├── Jenkinsfile                  # Jenkins pipeline (checkout, docker build, archive)
├── Jenkinsfile-sun              # Alternate Jenkins pipeline
├── build.sh                     # Docker build + metadata JSON generation
├── pom.xml                      # Maven project descriptor
├── cd-pipeline.yaml             # Root-level CD pipeline
└── ci-otp-pipeline.yaml         # Root-level CI pipeline
```

## Module Dependencies

```
OtpController
  ├── OtpService          (injected via constructor)
  └── JwtUtil             (static utility calls)

OtpService
  ├── RedisTemplate       (injected — OTP storage, rate limiting)
  ├── AzureKeyVaultUtil   (injected — entity encryption/decryption)
  └── otp-config.json     (loaded at startup from classpath)

AzureKeyVaultUtil
  └── Azure Key Vault SDK (CryptographyClient via Managed Identity)

RedisConfig
  └── application.properties (host, port, password, database from env vars)
```

## Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **Controller → Service (no repository layer)** | Redis is accessed directly via `RedisTemplate` in the service. No JPA entities or database tables. |
| **JSON file-based client configuration** | Per-client OTP rules loaded from `otp-config.json` at startup. Allows multi-tenant behavior without a database. |
| **Manual JWT parsing (no Spring Security)** | Lightweight auth — Base64 decodes the payload to extract roles. No signature verification. Keeps the service stateless and simple. |
| **Entity encryption before Redis storage** | Privacy protection — phone numbers and emails are RSA-OAEP encrypted via Azure Key Vault before being used as Redis key components. |
| **Global exception handler** | `@RestControllerAdvice` ensures all errors return a consistent `ApiResponseWrapper` envelope. |
| **DataSource excluded** | `@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})` — JPA starter is present but no relational DB is used. |
| **Redis key pattern scanning for verification** | Uses `KEYS` command to find matching OTP entries, then decrypts each entity to match. Trade-off: simple but O(N) scan. |
| **Multi-stage Docker build** | Separates build (Maven + full JDK) from runtime (minimal JRE) for smaller production images. |
| **Log4j2 over Logback** | Default Spring Boot logging excluded in favor of `spring-boot-starter-log4j2`. |



## Tech Stack & Dependencies


# Tech: TVSM OTP Service

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 17 |
| Framework | Spring Boot | 3.5.7 |
| Build | Maven | 3.9.x |
| Cache/Store | Redis (Lettuce client, SSL) | — |
| Secrets | Azure Key Vault (RSA-OAEP) | azure-identity 1.16.0, keyvault-keys 4.6.4 |
| JWT | jjwt 0.12.6, nimbus-jose-jwt 10.4 (manual Base64 parsing used) | — |
| Validation | Jakarta Bean Validation + libphonenumber 3.5 | — |
| API Docs | SpringDoc OpenAPI (springdoc-openapi-starter-webmvc-ui 2.8.13) | — |
| Logging | Log4j2 (via spring-boot-starter-log4j2) | — |
| HTTP Client | Apache HttpClient 4.5.14 | — |
| Code Gen | Lombok | — |
| Testing | JUnit 5 + Mockito | — |
| Container | Docker (multi-stage: Maven build → Eclipse Temurin 25 JRE) | — |
| CI/CD | Jenkins + Azure Pipelines | — |

## Coding Conventions

### General
- Package structure: `com.otp.{layer}` (controller, service, config, model, exception, util)
- One controller, one service — flat structure, no sub-packages per feature
- Lombok annotations for boilerplate: `@Data`, `@Builder`, `@RequiredArgsConstructor`, `@Slf4j`, `@NoArgsConstructor`, `@AllArgsConstructor`
- Jakarta validation annotations on request DTOs (`@NotNull`, `@NotBlank`, `@Pattern`)
- Enums for fixed value sets (`OtpChannelType`, `OtpEntityType`)

### Naming
- Classes: PascalCase (`OtpService`, `ApiResponseWrapper`)
- Methods: camelCase (`generateOtp`, `verifyOtp`)
- Constants: UPPER_SNAKE_CASE (`OTP_EXPIRED_OR_INVALID`, `SECURE_RANDOM`)
- Redis keys: colon-separated uppercase (`OTP:client:channel:entity`)

### API Design
- All responses wrapped in `ApiResponseWrapper<T>` with `timestamp`, `code`, `message`, `data`
- HTTP status in response body (`code` field) may differ from the actual HTTP status code
- Controller returns `ResponseEntity<ApiResponseWrapper<T>>`
- Swagger/OpenAPI annotations on controller methods (`@Operation`, `@ApiResponse`, `@Tag`)

### Dependency Injection
- Constructor injection via `@RequiredArgsConstructor` (controller) or explicit constructor (service)
- `@Component` for utilities, `@Configuration` + `@Bean` for infrastructure
- Static utility methods in `JwtUtil` (not injected as a bean despite `@Component`)

## Patterns

### Request Flow
```
Client → Authorization Header (JWT) → OtpController
  → JwtUtil.verifyToken() → JwtUtil.extractRoleFromJwt()
  → OtpService.generateOtp() / verifyOtp()
  → AzureKeyVaultUtil.encrypt/decrypt()
  → RedisTemplate operations
  → ApiResponseWrapper response
```

### Configuration Loading
- `otp-config.json` loaded from classpath at `OtpService` construction time
- Parsed as Jackson `JsonNode` tree (not mapped to POJOs in the service layer)
- Client config accessed via `configData.path("clients").path(clientName)`

### Rate Limiting (in-service, Redis-backed)
- Request counter incremented per generation call
- Block key set when counter exceeds threshold
- Block key has TTL matching `blockDurationMinutes`

### Entity Encryption
- All entity values (phone/email) encrypted via Azure Key Vault before use in Redis keys
- Verification resolves keys by scanning `OTP:{client}:{channel}:*` and decrypting each match

## Error Handling

### Strategy
- `@RestControllerAdvice` (`GlobalExceptionHandler`) catches all exceptions
- Every error response uses `ApiResponseWrapper<String>` with appropriate HTTP status

### Exception Hierarchy
| Exception | HTTP Status | When |
|-----------|-------------|------|
| `MethodArgumentNotValidException` | 400 | Bean validation failure on request body |
| `ConstraintViolationException` | 400 | Constraint violation |
| `IllegalArgumentException` | 400 | Invalid token, invalid input |
| `RuntimeException` | 500 | General runtime errors |
| `ConfigurationException` | (startup failure) | OTP config file cannot be loaded |
| `Exception` (catch-all) | 500 | Unexpected errors |

### Error Response Format
```json
{
  "timestamp": "2025-01-01T00:00:00Z",
  "code": 400,
  "message": "Validation Error: Entity cannot be empty",
  "data": null
}
```

## Testing

### Framework
- JUnit 5 (`@ExtendWith(MockitoExtension.class)`)
- Mockito for mocking dependencies (`@Mock`, `@InjectMocks`)
- No integration tests or testcontainers currently

### Coverage Areas
- Controller tests: mock service, verify response structure, auth flows
- Service tests: OTP generation/verification logic
- Config tests: Redis, Swagger, JWT configuration beans
- Exception tests: handler behavior for each exception type
- Model tests: DTO getters/setters/builders

### Test Conventions
- Test class naming: `{ClassName}Test.java`
- `@BeforeEach` for common setup (valid tokens, request objects)
- Assertions: JUnit 5 `assertEquals`, `assertNotNull`, `assertThrows`, `assertTrue`
- Verification: Mockito `verify(mock, times(n))`

## Deployment

### Docker
- **Production image** (`Dockerfile`): Multi-stage — Maven 3.9.11 (Corretto 24) builds the JAR, Eclipse Temurin 25 JRE runs it
- **Build image** (`Dockerfile.build`): Temurin 21 + Maven for CI pre-build step
- Exposed port: **7001**
- JVM options: `-XX:+UnlockExperimentalVMOptions -XX:+UseContainerSupport -XX:+PrintFlagsFinal`

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `EXPOSED_PORT` | Server port |
| `REDIS_HOST_URL` | Redis hostname |
| `REDIS_PORT` | Redis port |
| `REDIS_TOKEN` | Redis password |
| `REDIS_DATABASE` | Redis database index |
| `AZURE_KEY_URL` | Azure Key Vault URI |
| `AZURE_KEY_NAME` | Key name in vault |
| `AZURE_KEY_CLIENT` | Managed Identity client ID |

### CI/CD
- **Jenkins**: Shared library `deploy-conf`, stages: checkout → docker pre-build → build → archive artifacts
- **Azure Pipelines**: Separate pipelines for CI, CD, UAT deploy, Prod deploy, image scanning, SonarQube
- **build.sh**: Builds Docker image with commit hash label, outputs `metadata.json`

### Endpoints
- Application context path: `/otp`
- Actuator: `/otp/actuator/health`, `/otp/actuator/info`
- Swagger UI: `/otp/swagger-ui/index.html`

