---
service_id: tvsm-otp-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvsm-otp-service — High-Level Code

## Application Overview
tvsm-otp-service (`tvsm-otp-service`) is a `backend-api` codebase; stacks java; head `c2e3ad84f21c97ab024d77021e95d4eb5a3232ab`.
Entry points: Unknown.

## Module Summary
tvsm-otp-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 2 endpoints, 0 outbound calls, 0 messaging, 1 data-access |

## Folder Structure
tvsm-otp-service top-level folders (3 levels):

```
tvsm-otp-service/
├── azure-pipelines/
├── jmeter/
│   ├── test-plans/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
```

## Core Workflows in Code
tvsm-otp-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### OtpController
1. `src/main/java/com/otp/controller/OtpController.java` receives 2 route(s), e.g. `POST /otp/api/generate` → `OtpController.generateOtp`.
3. Module `.` data access via `src/main/java/com/otp/config/OtpServiceHealthIndicator.java:26`.

## Integration Clients
tvsm-otp-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| data store (db) | `src/main/java/com/otp/config/OtpServiceHealthIndicator.java:26` | Unknown |

## Cross-Cutting Concerns
tvsm-otp-service cross-cutting code:
- Auth: none found
- Error handling: `src/main/java/com/otp/exception/GlobalExceptionHandler.java:15` (@RestControllerAdvice)
- Validation: 1 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `org.springframework.boot:spring-boot-starter-data-redis`, `org.springframework.boot:spring-boot-starter-log4j2`

## Build and Test
tvsm-otp-service build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `azure-pipelines/ast-image-scan-otp-pipeline.yaml:1`, `azure-pipelines/ast-otp-prod-pipeline.yaml:1`, `azure-pipelines/ast-otp-uat-pipeline.yaml:1`, `azure-pipelines/cd-pipeline.yaml:1`, `azure-pipelines/ci-pipeline.yaml:1`, `azure-pipelines/sonar.yaml:13`, `cd-pipeline.yaml:1`, `ci-otp-pipeline.yaml:1`, `uk-cd-pipeline.yaml:1`, `uk-cd-training-pipeline.yaml:1`
