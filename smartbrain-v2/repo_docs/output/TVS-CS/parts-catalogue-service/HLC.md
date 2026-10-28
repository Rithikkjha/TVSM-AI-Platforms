---
service_id: parts-catalogue-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# parts-catalogue-service — High-Level Code

## Application Overview
parts-catalogue-service (`Parts-Catalogue-Service`) is a `backend-api` codebase; stacks java; head `e7872a1a3c0d2d4598f741baf051c5bb7a4c9d21`.
Entry points: Unknown.

## Module Summary
parts-catalogue-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 19 endpoints, 0 outbound calls, 0 messaging, 2 data-access |

## Folder Structure
parts-catalogue-service top-level folders (3 levels):

```
Parts-Catalogue-Service/
├── azure-pipelines/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
```

## Core Workflows in Code
parts-catalogue-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### EntitiesController
1. `src/main/java/org/com/graph/controller/EntitiesController.java` receives 6 route(s), e.g. `GET /api/assemblies` → `EntitiesController.getAssemblies`.
3. Module `.` data access via `src/main/java/org/com/graph/config/NebulaGraphConfig.java:38`, `src/main/java/org/com/graph/config/OpenSearchConfig.java:60`.

### ChartController
1. `src/main/java/org/com/graph/controller/ChartController.java` receives 4 route(s), e.g. `GET /api/chart/model` → `ChartController.getChartModel`.
3. Module `.` data access via `src/main/java/org/com/graph/config/NebulaGraphConfig.java:38`, `src/main/java/org/com/graph/config/OpenSearchConfig.java:60`.

### ProductDetailsController
1. `src/main/java/org/com/graph/controller/ProductDetailsController.java` receives 2 route(s), e.g. `GET /api/products/kits-with-assemblies` → `ProductDetailsController.getAssembliesByProduct`.
3. Module `.` data access via `src/main/java/org/com/graph/config/NebulaGraphConfig.java:38`, `src/main/java/org/com/graph/config/OpenSearchConfig.java:60`.

### EpcController
1. `src/main/java/org/com/graph/controller/EpcController.java` receives 2 route(s), e.g. `GET /api/v1/epc/image` → `EpcController.getImage`.
3. Module `.` data access via `src/main/java/org/com/graph/config/NebulaGraphConfig.java:38`, `src/main/java/org/com/graph/config/OpenSearchConfig.java:60`.

### TraversalController
1. `src/main/java/org/com/graph/controller/TraversalController.java` receives 1 route(s), e.g. `GET /api/reverseHierarchy/part` → `TraversalController.getReverseHierarchyByPartNumberOrCatalogSkuId`.
3. Module `.` data access via `src/main/java/org/com/graph/config/NebulaGraphConfig.java:38`, `src/main/java/org/com/graph/config/OpenSearchConfig.java:60`.

### SearchController
1. `src/main/java/org/com/graph/controller/SearchController.java` receives 1 route(s), e.g. `GET /api/search` → `SearchController.search`.
3. Module `.` data access via `src/main/java/org/com/graph/config/NebulaGraphConfig.java:38`, `src/main/java/org/com/graph/config/OpenSearchConfig.java:60`.

### ProductDetailsControllerV2
1. `src/main/java/org/com/graph/controller/ProductDetailsControllerV2.java` receives 1 route(s), e.g. `GET /api/v2/products/kits-with-assemblies/details` → `ProductDetailsControllerV2.getAssembliesWithDetails`.
3. Module `.` data access via `src/main/java/org/com/graph/config/NebulaGraphConfig.java:38`, `src/main/java/org/com/graph/config/OpenSearchConfig.java:60`.

### TraversalControllerV2
1. `src/main/java/org/com/graph/controller/TraversalControllerV2.java` receives 1 route(s), e.g. `GET /api/v2/reverseHierarchy/part` → `TraversalControllerV2.getReverseHierarchy`.
3. Module `.` data access via `src/main/java/org/com/graph/config/NebulaGraphConfig.java:38`, `src/main/java/org/com/graph/config/OpenSearchConfig.java:60`.

### SearchControllerV2
1. `src/main/java/org/com/graph/controller/SearchControllerV2.java` receives 1 route(s), e.g. `GET /api/v2/search` → `SearchControllerV2.search`.
3. Module `.` data access via `src/main/java/org/com/graph/config/NebulaGraphConfig.java:38`, `src/main/java/org/com/graph/config/OpenSearchConfig.java:60`.

## Integration Clients
parts-catalogue-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| data store (parts_catalogue_graph) | `src/main/java/org/com/graph/config/NebulaGraphConfig.java:38` | Unknown |
| data store (db) | `src/main/java/org/com/graph/config/OpenSearchConfig.java:60` | Unknown |

## Cross-Cutting Concerns
parts-catalogue-service cross-cutting code:
- Auth: none found
- Error handling: `src/main/java/org/com/graph/exception/GlobalExceptionHandler.java:24` (@RestControllerAdvice)
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `ch.qos.logback:logback-classic`, `ch.qos.logback:logback-core`, `com.github.ben-manes.caffeine:caffeine`, `org.springframework.boot:spring-boot-starter-cache`

## Build and Test
parts-catalogue-service build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `azure-pipelines/ast-image-scan.yaml:1`, `azure-pipelines/ast-prod.yaml:1`, `azure-pipelines/ast-uat.yaml:1`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`, `sonar.yml:1`, `uk-cd-pipeline.yaml:1`, `uk-training-cd-pipeline.yaml:1`
