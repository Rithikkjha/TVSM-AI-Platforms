---
service_id: tvsm-securesigner-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvsm-securesigner-service — High-Level Code

## Application Overview
tvsm-securesigner-service (`tvsm-securesigner-service`) is a `backend-api` codebase; stacks java; head `01113ba63ca68d0f24c4f555313d9ecfb526f334`.
Entry points: `src/main/java/com/tvsm/urlsigner/URLSignerApplication.java`.

## Module Summary
tvsm-securesigner-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 6 endpoints, 0 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
tvsm-securesigner-service top-level folders (3 levels):

```
tvsm-securesigner-service/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
```

## Core Workflows in Code
tvsm-securesigner-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### SignerController
1. `src/main/java/com/tvsm/urlsigner/controller/SignerController.java` receives 5 route(s), e.g. `GET /generate/bcrypt-hash` → `SignerController.generateBCryptHash`.

### TestController
1. `src/main/java/com/tvsm/urlsigner/controller/TestController.java` receives 1 route(s), e.g. `GET /test/test` → `TestController.healthTest`.

## Integration Clients
tvsm-securesigner-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| N/A | | |

## Cross-Cutting Concerns
tvsm-securesigner-service cross-cutting code:
- Auth: `src/main/java/com/tvsm/urlsigner/service/SignerService.java:12` (jsonwebtoken)
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `org.springframework.boot:spring-boot-starter-cache`

## Build and Test
tvsm-securesigner-service build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `AST_Image_Scan_secure_signer_Pipeline.yml:1`, `AST_secure_signer_UAT_Pipeline.yml:1`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`
