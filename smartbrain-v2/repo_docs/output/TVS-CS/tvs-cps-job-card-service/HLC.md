---
service_id: tvs-cps-job-card-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvs-cps-job-card-service — High-Level Code

## Application Overview
tvs-cps-job-card-service (`TVS-CPS-JOB-CARD-SERVICE`) is a `backend-api` codebase; stacks java; head `bf6538ecab8ffbfc749d441215b403cf3a47b5dd`.
Entry points: `src/main/java/com/tvsm/jobcard/Application.java`.

## Module Summary
tvs-cps-job-card-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 16 endpoints, 1 outbound calls, 1 messaging, 1 data-access |

## Folder Structure
tvs-cps-job-card-service top-level folders (3 levels):

```
TVS-CPS-JOB-CARD-SERVICE/
├── azure-pipelines/
│   ├── templates/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
```

## Core Workflows in Code
tvs-cps-job-card-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### JobcardController
1. `src/main/java/com/tvsm/jobcard/controller/JobcardController.java` receives 13 route(s), e.g. `GET /api/v1/jobcards/bulk-upload/{bulkUploadId}/error` → `JobcardController.getBulkUploadErrors`.
2. Module `.` makes outbound calls to: `Unknown(config:customer.search-url)`.
3. Module `.` data access via `src/main/java/com/tvsm/jobcard/entity/Billing.java:12`.

### HealthController
1. `src/main/java/com/tvsm/jobcard/controller/HealthController.java` receives 1 route(s), e.g. `GET /api/health` → `HealthController.health`.
2. Module `.` makes outbound calls to: `Unknown(config:customer.search-url)`.
3. Module `.` data access via `src/main/java/com/tvsm/jobcard/entity/Billing.java:12`.

### JobCardAnalyticsController
1. `src/main/java/com/tvsm/jobcard/controller/JobCardAnalyticsController.java` receives 1 route(s), e.g. `POST /api/v1/jobcards/analytics/stats` → `JobCardAnalyticsController.retrieveJobCardIndicators`.
2. Module `.` makes outbound calls to: `Unknown(config:customer.search-url)`.
3. Module `.` data access via `src/main/java/com/tvsm/jobcard/entity/Billing.java:12`.

### ExternalJobcardController
1. `src/main/java/com/tvsm/jobcard/controller/ExternalJobcardController.java` receives 1 route(s), e.g. `POST /api/v1/jobcards/external/details` → `ExternalJobcardController.getJobcardsByVinAndStatus`.
2. Module `.` makes outbound calls to: `Unknown(config:customer.search-url)`.
3. Module `.` data access via `src/main/java/com/tvsm/jobcard/entity/Billing.java:12`.

## Integration Clients
tvs-cps-job-card-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/main/java/com/tvsm/jobcard/service/JobcardBulkUploadService.java` | config:customer.search-url |
| kafka publish dev.cp.job_card | `src/main/java/com/tvsm/jobcard/service/JobCardProducerService.java:29` | azure.eventhub.jobcard.hub-name |
| data store (nmazcpsdbdev01-jobcard) | `src/main/java/com/tvsm/jobcard/entity/Billing.java:12` | Unknown |

## Cross-Cutting Concerns
tvs-cps-job-card-service cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 27 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
tvs-cps-job-card-service build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `azure-pipelines/templates/ast-image-scan.yaml:1`, `azure-pipelines/templates/ast-prod.yaml:1`, `azure-pipelines/templates/ast-uat.yaml:1`, `azure-pipelines/templates/cd-pipeline.yaml:1`, `azure-pipelines/templates/ci-pipeline.yaml:1`, `azure-pipelines/templates/pr-build-validation.yaml:1`, `azure-pipelines/templates/sonar.yaml:1`, `azure-pipelines/templates/uk-cd-pipeline.yaml:1`, `azure-pipelines/templates/uk-training-cd-pipeline.yaml:1`
