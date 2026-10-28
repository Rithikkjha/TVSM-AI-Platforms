---
service_id: parts-catalogue-ingestion-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# parts-catalogue-ingestion-service — High-Level Code

## Application Overview
parts-catalogue-ingestion-service (`Parts-Catalogue-Ingestion-Service`) is a `Unknown` codebase; stacks java; head `cfd36cbc0ab8d334a872c056a32e895ccee80b4b`.
Entry points: `src/main/java/org/com/graph/IngestionServiceApplication.java`.

## Module Summary
parts-catalogue-ingestion-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | unknown: 0 endpoints, 4 outbound calls, 0 messaging, 2 data-access |

## Folder Structure
parts-catalogue-ingestion-service top-level folders (3 levels):

```
Parts-Catalogue-Ingestion-Service/
├── azure_pipelines/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
```

## Core Workflows in Code
parts-catalogue-ingestion-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.
N/A — no server-side entry handlers; see Integration Clients for UI → API calls.

## Integration Clients
parts-catalogue-ingestion-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/main/java/org/com/graph/config/ApiClientConfig.java` | config:catalogue.api.mdp.baseUrl |
| Unknown | `src/main/java/org/com/graph/config/ApiClientConfig.java` | config:catalogue.api.mdp.tokenUrl |
| Unknown | `src/main/java/org/com/graph/config/ApiClientConfig.java` | config:catalogue.api.norton.baseUrl |
| Unknown | `src/main/java/org/com/graph/config/ApiClientConfig.java` | config:catalogue.api.price.baseUrl |
| data store (db) | `src/main/java/org/com/graph/config/NebulaGraphConfig.java:63` | Unknown |
| data store (db) | `src/main/java/org/com/graph/config/OpenSearchConfig.java:59` | Unknown |

## Cross-Cutting Concerns
parts-catalogue-ingestion-service cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `ch.qos.logback:logback-classic`, `ch.qos.logback:logback-core`

## Build and Test
parts-catalogue-ingestion-service build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `azure_pipelines/ast-image-scan-parts-catalogue-ingestion-pipeline.yaml:1`, `azure_pipelines/ast-parts-catalogue-ingestion-service-prod.yaml:1`, `azure_pipelines/ast-parts-catalogue-ingestion-uat-pipeline.yaml:1`, `azure_pipelines/sonar-pr-pipeline.yaml:7`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`, `sonar-cipipeline.yml:3`, `uk-cd-pipeline.yaml:1`, `uk-cd-training-pipeline.yaml:1`
