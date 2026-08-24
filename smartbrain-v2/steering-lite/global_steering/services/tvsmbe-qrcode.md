# tvsmbe-qrcode


## Product Context


# Product Context — TVS Motor QR Code Service

## What This Service Does

A QR code generation and management platform for TVS Motor Company. Internal users create branded, customizable QR codes for marketing campaigns, products, and regional initiatives. The system supports two QR modes:

- **Dynamic (trackable) QR codes** — encode a short URL (`https://qr.tvsmotor.com/{shortCode}`) that 302-redirects to the actual destination. Enables scan analytics and post-creation URL changes without regenerating the QR image.
- **Static QR codes** — encode the target URL directly into the QR. No redirect tracking, no URL editing after creation.

---

## Domain Entities

### QrCode (`qr_codes`)
The central entity. Each record represents one generated QR code.

| Field | Purpose |
|-------|---------|
| `shortCode` | Unique Base62-encoded identifier used in short URLs |
| `subjectType` | What the QR is about: `BRAND`, `CAMPAIGN`, `PRODUCT`, `MODEL`, `OTHER` |
| `subjectKey` | Slug/ID of the subject (e.g. "apache", "diwali-2025") |
| `region` / `country` | Geographic scope — used for access control and blob path organization |
| `redirectUrl` | The actual destination URL (editable post-creation for dynamic QRs) |
| `status` | Lifecycle: `ACTIVE`, `INACTIVE`, `SCHEDULED`, `EXPIRED` |
| `svgBlobPath` | URL/path to the stored SVG in Azure Blob Storage |
| `metadata` | Arbitrary JSON for campaign-specific data |
| `isRedirect` | `true` = dynamic/trackable, `false` = static |
| `createdByUserId` | Owner — drives USER-role access control |
| `validFrom` / `validTo` | Optional scheduling window |

### QrUser (`qr_users`)
Internal user accounts with role-based access.

| Field | Purpose |
|-------|---------|
| `userId` | Integer ID (auto-incremented on signup) |
| `username` | Lowercase, unique login identifier |
| `passwordHash` | BCrypt hash of (pepper + password) |
| `role` | `SUPER_ADMIN`, `ADMIN`, `USER` |
| `regionGroup` | For ADMIN scoping — matches `QrCode.region` |
| `accessToken` / `refreshToken` | Stored tokens — enables single-session enforcement |

### QrRedirectEvent (`qr_redirect_events`)
Scan tracking for dynamic QR codes.

| Field | Purpose |
|-------|---------|
| `shortCode` | Which QR was scanned |
| `scanTime` | When the scan occurred |
| `userAgent` / `ipAddress` / `referer` | Client context for analytics |

### QrAuditLog (`qr_audit_logs`)
Change history for QR codes.

| Field | Purpose |
|-------|---------|
| `action` | `CREATED`, `UPDATED`, `STATUS_CHANGED`, `DELETED` |
| `performedByUserId` | Who made the change |
| `details` | JSON snapshot of what changed |

---

## Integrations

| System | Purpose | Status |
|--------|---------|--------|
| **MongoDB** (Mongo 7) | Primary data store for all entities | Active |
| **Azure Blob Storage** | SVG/PNG file storage | Disabled (SDK calls commented out; returns placeholder URLs) |
| **ZXing** | QR code matrix generation | Active |
| **Apache Batik** | SVG → PNG transcoding | Active |

---

## Business Rules

### QR Creation
- Short codes are generated via an atomic MongoDB counter + Base62 encoding (offset 100,000 for readable codes).
- Dynamic QRs encode the short URL into the QR image; static QRs encode the target URL directly.
- Preview endpoints return SVG without persisting. Save endpoints persist to DB and upload to blob storage.
- A `shortCode` generated at preview time can be reused at save time to produce an identical QR.
- Blob paths follow a hierarchical convention: `{folderRoot}/{scope}/{region|tag}/print/{subjectType}/{subjectKey}/{filename}_{timestamp}.svg`

### Authentication & Authorization
- Auth is toggleable via `tvsm.auth.enabled`. When disabled, all endpoints are open (dev mode).
- Passwords are peppered before BCrypt hashing. The pepper is a required config value.
- JWT access tokens expire in 24 hours; refresh tokens in 7 days.
- Tokens are stored in the user record — logging in invalidates any previous session.
- Public paths (signup, login, refresh, config, logos, short-code redirects) skip auth.

### Role-Based Access Control
- **SUPER_ADMIN**: Full access to all QR codes and analytics.
- **ADMIN**: Scoped to QR codes matching their `regionGroup`. Can filter to "mine" only.
- **USER**: Can only see and manage QR codes they created.

### Redirect Behavior
- `/{shortCode}` resolves to a 302 redirect with no-cache headers.
- If the QR is not `ACTIVE`, returns 410 Gone.
- Scan events are logged asynchronously (failure doesn't block the redirect).

### QR Visual Customization
- Foreground, background, and corner (finder pattern) colors are configurable.
- Two styles: `classic` (solid modules) and `squared` (rounded, spaced modules).
- Logo overlay: classpath PNG, uploaded file, or default TVS logo. Pass `"none"` to skip logo.
- Optional label text rendered below the QR in the SVG.
- Error correction level H (30% redundancy) to tolerate logo overlay.



## Code Structure


# Project Structure — TVS Motor QR Code Service

## Annotated Directory Layout

```
tvsmbe-qrcode/
├── build.gradle                    # Gradle build config (Spring Boot 3.3.3, Java 21)
├── settings.gradle                 # Project name: qr_code_genv2
├── gradlew / gradlew.bat           # Gradle wrapper scripts
├── gradle/wrapper/                 # Gradle wrapper properties (8.x)
├── Dockerfile                      # Multi-stage build: Temurin 21 JDK → JRE
├── docker-compose.yml              # MongoDB + two backend profiles (public + admin)
├── .dockerignore / .gitignore
│
└── src/main/
    ├── java/com/tvsmotor/qrcode/
    │   ├── QRCodeApplication.java          # Entry point, CORS config bean
    │   │
    │   ├── auth/                           # Authentication & authorization
    │   │   ├── AuthContext.java            # ThreadLocal holder for current user
    │   │   ├── AuthenticatedUser.java      # Immutable DTO: userId, name, role, regionGroup
    │   │   ├── JwtService.java             # JWT signing/validation (HMAC-SHA)
    │   │   ├── PepperedPasswordEncoder.java # BCrypt with server-side pepper
    │   │   └── TvsmAuthFilter.java         # Servlet Filter — token validation, AuthContext population
    │   │
    │   ├── controller/                     # REST API layer
    │   │   ├── AuthController.java         # /api/auth — signup, login, refresh, logout, me
    │   │   ├── QrCreateController.java     # /api/qr-create — dynamic QR preview + save
    │   │   ├── QrComposeController.java    # /api/qr — static QR generate + save
    │   │   ├── QrLibraryController.java    # /api/qr-library — CRUD, list, status/redirect updates
    │   │   ├── RedirectController.java     # /{shortCode} — public 302 redirect + scan logging
    │   │   ├── AnalyticsController.java    # /api/analytics — summary, top, timeline, scans
    │   │   └── LogosController.java        # /api/v1/logos — list/serve classpath PNG logos
    │   │
    │   ├── db/
    │   │   ├── MongoInitializer.java       # Creates collections with JSON Schema validation
    │   │   ├── entities/                   # MongoDB document models (Lombok @Data @Builder)
    │   │   │   ├── QrCode.java
    │   │   │   ├── QrUser.java
    │   │   │   ├── QrRedirectEvent.java
    │   │   │   └── QrAuditLog.java
    │   │   └── repositories/              # Spring Data MongoDB repositories
    │   │       ├── QrCodeRepository.java
    │   │       ├── QrUserRepository.java
    │   │       ├── QrRedirectEventRepository.java
    │   │       └── QrAuditLogRepository.java
    │   │
    │   ├── exceptions/
    │   │   ├── GlobalExceptionHandler.java         # @RestControllerAdvice — conflict, bad request
    │   │   └── QrCodeAlreadyExistsException.java   # 409 with existing document payload
    │   │
    │   ├── services/
    │   │   ├── QrService.java              # QR image generation (PNG + SVG, logo overlay, styles)
    │   │   └── SequenceService.java        # Atomic counter + Base62 short code generation
    │   │
    │   ├── storage/
    │   │   └── AzureBlobStorageService.java # Azure Blob upload/download (currently disabled)
    │   │
    │   └── util/
    │       ├── Json.java                   # Jackson serialize/deserialize helpers
    │       └── SvgPngConverter.java        # Batik-based SVG → PNG conversion
    │
    └── resources/
        ├── application.yml                 # Config: MongoDB, server port, Azure, auth, app settings
        ├── TVS_Logo.svg                    # Default SVG logo for QR overlay
        ├── tvs_motor.png / ntorg150.png    # Additional logo assets
        └── logos/                          # Classpath logo library (served via LogosController)
            ├── TVS Logo.png
            ├── TVS logo black.png
            └── ntorg150.png
```

---

## Module Dependencies

```
Controller Layer
  ├── auth (AuthContext, AuthenticatedUser)
  ├── services (QrService, SequenceService)
  ├── storage (AzureBlobStorageService)
  └── db/repositories

Services Layer
  ├── QrService → ZXing, java.awt, Batik (image generation, no DB access)
  └── SequenceService → MongoTemplate (atomic counter)

Auth Layer
  ├── TvsmAuthFilter → JwtService, QrUserRepository, AuthContext
  ├── JwtService → JJWT library
  └── PepperedPasswordEncoder → Spring Security Crypto (BCrypt)

Storage Layer
  └── AzureBlobStorageService → Azure SDK (disabled)

DB Layer
  ├── entities (POJOs with Lombok + Spring Data annotations)
  └── repositories (Spring Data MongoRepository interfaces)
```

---

## Architectural Decisions

### Dual-Profile Deployment
The same codebase deploys as two separate containers:
- **`public` profile** (port 8085): Only `RedirectController` is active. No auth, minimal attack surface.
- **`admin` profile** (port 8084): All management controllers active, auth enforced.

Controllers use `@Profile({"admin", "default"})` or `@Profile({"public", "default"})` to control activation. The `default` profile enables both for local development.

### Custom Auth (No Spring Security Filter Chain)
Auth is implemented as a raw `jakarta.servlet.Filter` rather than Spring Security's filter chain. This keeps the dependency footprint small (only `spring-security-crypto` for BCrypt) and gives full control over token validation logic.

### Token-in-DB Pattern
Access and refresh tokens are stored in the `QrUser` document. This enables:
- Single-session enforcement (new login overwrites old token)
- Immediate token invalidation on logout
- Token-to-user verification (prevents use of valid-signature tokens after logout)

### MongoDB Schema Validation
`MongoInitializer` applies a `$jsonSchema` validator to the `qr_codes` collection at startup. This enforces required fields (`shortCode`, `redirectUrl`, `status`) and type constraints at the database level.

### Short Code Generation
Uses an atomic `findAndModify` counter in a `sequences` collection, offset by 100,000, then Base62-encoded. This produces short, URL-safe codes without collision risk.

### SVG-First QR Output
QR codes are generated as SVG (not PNG) for scalability. SVG includes embedded base64 logos or inline SVG logo content. PNG conversion is available via `SvgPngConverter` (Batik) but not exposed as an endpoint currently.



## Tech Stack & Dependencies


# Tech Stack & Conventions — TVS Motor QR Code Service

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 21 |
| Framework | Spring Boot | 3.3.3 |
| Build | Gradle (Groovy DSL) | 8.x (wrapper) |
| Database | MongoDB | 7 (via Docker) |
| QR Generation | ZXing (core + javase) | 3.5.3 |
| SVG → PNG | Apache Batik | 1.17 |
| JWT | JJWT (api + impl + jackson) | 0.12.6 |
| Password Hashing | Spring Security Crypto (BCrypt) | 6.3.0 |
| Object Storage | Azure Blob Storage SDK | 12.27.0 |
| Object Mapping | ModelMapper | 3.1.1 |
| Boilerplate | Lombok | (managed by Spring BOM) |
| Container | Eclipse Temurin | 21 (JDK build, JRE runtime) |

---

## Coding Conventions

### General
- **Lombok everywhere**: `@Data`, `@Builder`, `@NoArgsConstructor`, `@AllArgsConstructor` on entities. `@RequiredArgsConstructor` on some controllers.
- **Constructor injection** preferred (no `@Autowired` annotations).
- **No interfaces for services** — concrete classes directly (`QrService`, `SequenceService`, `AzureBlobStorageService`).
- **Map-based JSON responses** — controllers return `Map<String, Object>` or `ResponseEntity<Map<...>>` rather than dedicated response DTOs.
- **Request bodies as `Map<String, String>`** for auth endpoints; `@RequestParam` / `@RequestPart` for multipart QR endpoints.

### Naming
- Package: `com.tvsmotor.qrcode.{module}` (auth, controller, db, db.entities, db.repositories, exceptions, services, storage, util)
- Entity classes: `QrCode`, `QrUser`, `QrAuditLog`, `QrRedirectEvent`
- Repository interfaces: `{Entity}Repository`
- Controllers: `{Feature}Controller`
- MongoDB collections: snake_case (`qr_codes`, `qr_users`, `qr_audit_logs`, `qr_redirect_events`)

### Configuration
- All config in `application.yml` with environment variable overrides (`${ENV_VAR:default}`)
- Secrets (JWT secret, password pepper, Azure connection string) are env vars with dev-only defaults
- Feature flags: `azure.storage.enabled`, `tvsm.auth.enabled`
- App-specific config under `app.qr.*` and `app.domain.*`

---

## Patterns

### Thread-Local Auth Context
```java
AuthContext.set(new AuthenticatedUser(...));  // set in TvsmAuthFilter
AuthenticatedUser user = AuthContext.get();   // read in controllers/services
AuthContext.clear();                          // cleared in filter's finally block
```
Controllers check `AuthContext.get()` — if null, auth is disabled (dev mode) and access is unrestricted.

### Profile-Based Controller Activation
```java
@Profile({"admin", "default"})   // active in admin and local dev
@Profile({"public", "default"})  // active in public-facing and local dev
```

### Audit Logging
Changes to QR codes (create, update redirect, change status) are logged to `qr_audit_logs` with a try-catch that swallows failures — audit logging never blocks the primary operation.

### Blob Path Convention
```
{folderRoot}/{scope}/{region-or-tag}/print/{subjectType}/{subjectKey}/{subjectKey}_{timestamp}.svg
```
Example: `tvs-qrcodes-ib/global/ib/print/campaign/diwali-2025/diwali-2025_20250115_143022.svg`

### Short Code Flow (Dynamic QR)
1. `SequenceService.nextShortCode()` → atomic increment → Base62
2. Build short URL: `{domain.base}/{shortCode}`
3. Encode short URL into QR matrix
4. On scan: `RedirectController` resolves shortCode → 302 to `redirectUrl`

---

## Error Handling

### Global Exception Handler (`@RestControllerAdvice`)
- `QrCodeAlreadyExistsException` → 409 Conflict with existing document in body
- `IllegalArgumentException` → 400 Bad Request with message

### Controller-Level Handling
- Not-found cases return `404` with `{"error": "..."}` body
- Access denied returns `403` with `{"error": "Access denied"}`
- Auth failures return `401` with `{"error": "..."}` (from both filter and controller)
- Validation errors in signup return `400` with `{"error": "Validation failed", "details": [...]}`

### Resilient Patterns
- Redirect event logging wrapped in try-catch — scan tracking failure never blocks the redirect
- Audit log writes wrapped in try-catch — audit failure never blocks the primary operation
- Blob storage disabled gracefully — returns placeholder URLs, app continues to function

---

## Testing

- Test framework: JUnit 5 (via `spring-boot-starter-test`, JUnit Vintage excluded)
- Run tests: `./gradlew test`
- No test files currently exist in the repository

---

## Deployment

### Docker Build (Multi-Stage)
```dockerfile
# Stage 1: Build with JDK 21
FROM eclipse-temurin:21-jdk AS build
# Downloads dependencies first (layer caching), then builds bootJar

# Stage 2: Runtime with JRE 21
FROM eclipse-temurin:21-jre
COPY --from=build /app/build/libs/*.jar app.jar
EXPOSE 8084
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### Docker Compose Services
| Service | Profile | Port | Auth |
|---------|---------|------|------|
| `backend-admin` | `admin` | 8084 | Enabled |
| `backend-public` | `public` | 8085 | Disabled |
| `mongodb` | — | 27017 | Root: qradmin/qradmin123 |

### Environment Variables
| Variable | Purpose | Default |
|----------|---------|---------|
| `SPRING_PROFILES_ACTIVE` | Profile selection | — |
| `SERVER_PORT` | HTTP port | 8084 |
| `MONGO_URI` | MongoDB connection string | localhost Docker URI |
| `TVSM_AUTH_ENABLED` | Enable/disable auth | true |
| `TVSM_AUTH_JWT_SECRET` | JWT signing key (≥32 chars) | dev-only default |
| `TVSM_AUTH_PASSWORD_PEPPER` | Password pepper | dev-only default |
| `AZURE_STORAGE_ENABLED` | Enable blob uploads | false |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure connection | empty |
| `AZURE_STORAGE_CONTAINER` | Blob container name | qrcodes-uat |
| `APP_DOMAIN_BASE` | Base URL for short links | https://qr.tvsmotor.com/ |

### Local Development
```bash
# Start MongoDB
docker compose up mongodb -d

# Run the app (default profile = both admin + public controllers active)
./gradlew bootRun

# Or run both profiles separately
docker compose up
```

