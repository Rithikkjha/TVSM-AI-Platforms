---
service_id: tvsmbe-qrcode
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvsmbe-qrcode — High-Level Code

## Application Overview
tvsmbe-qrcode (`tvsmbe-qrcode`) is a `backend-api` codebase; stacks java; head `20cbc22dd9800f72d5914902f2e7045b584dd797`.
Entry points: `src/main/java/com/tvsmotor/qrcode/QRCodeApplication.java`.

## Module Summary
tvsmbe-qrcode modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 21 endpoints, 0 outbound calls, 0 messaging, 1 data-access |

## Folder Structure
tvsmbe-qrcode top-level folders (3 levels):

```
tvsmbe-qrcode/
├── gradle/
│   ├── wrapper/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
```

## Core Workflows in Code
tvsmbe-qrcode workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### AuthController
1. `src/main/java/com/tvsmotor/qrcode/controller/AuthController.java` receives 6 route(s), e.g. `GET /api/auth/config` → `AuthController.getConfig`.
3. Module `.` data access via `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:45`.

### AnalyticsController
1. `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java` receives 4 route(s), e.g. `GET /api/analytics/scans/{shortCode}` → `AnalyticsController.scansByShortCode`.
3. Module `.` data access via `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:45`.

### QrLibraryController
1. `src/main/java/com/tvsmotor/qrcode/controller/QrLibraryController.java` receives 4 route(s), e.g. `GET /api/qr-library` → `QrLibraryController.list`.
3. Module `.` data access via `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:45`.

### LogosController
1. `src/main/java/com/tvsmotor/qrcode/controller/LogosController.java` receives 2 route(s), e.g. `GET /api/v1/logos` → `LogosController.list`.
3. Module `.` data access via `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:45`.

### QrCreateController
1. `src/main/java/com/tvsmotor/qrcode/controller/QrCreateController.java` receives 2 route(s), e.g. `POST /api/qr-create/preview` → `QrCreateController.preview`.
3. Module `.` data access via `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:45`.

### QrComposeController
1. `src/main/java/com/tvsmotor/qrcode/controller/QrComposeController.java` receives 2 route(s), e.g. `POST /api/qr/generate` → `QrComposeController.generateOnly`.
3. Module `.` data access via `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:45`.

### RedirectController
1. `src/main/java/com/tvsmotor/qrcode/controller/RedirectController.java` receives 1 route(s), e.g. `GET /{shortCode}` → `RedirectController.resolve`.
3. Module `.` data access via `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:45`.

## Integration Clients
tvsmbe-qrcode outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| data store (tvs_qr) | `src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:45` | Unknown |

## Cross-Cutting Concerns
tvsmbe-qrcode cross-cutting code:
- Auth: `src/main/java/com/tvsmotor/qrcode/auth/JwtService.java:4` (jsonwebtoken), `src/main/java/com/tvsmotor/qrcode/auth/TvsmAuthFilter.java:5` (jsonwebtoken)
- Error handling: `src/main/java/com/tvsmotor/qrcode/exceptions/GlobalExceptionHandler.java:7` (@RestControllerAdvice)
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
tvsmbe-qrcode build/test commands from manifests:
- Gradle: `./gradlew build` / `./gradlew test`
- CI pipelines: none found
