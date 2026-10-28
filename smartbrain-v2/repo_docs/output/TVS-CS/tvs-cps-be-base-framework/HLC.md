---
service_id: tvs-cps-be-base-framework
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvs-cps-be-base-framework — High-Level Code

## Application Overview
tvs-cps-be-base-framework (`TVS-CPS-BE-BASE-FRAMEWORK`) is a `library` codebase; stacks java; head `37744a7285d0835695d43c01b1baf1ed43e9f299`.
Entry points: `tvsm-be-archetype/src/main/resources/archetype-resources/src/main/java/__packageInPathFormat__/Application.java`.

## Module Summary
tvs-cps-be-base-framework modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | unknown: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| tvsm-be-archetype | `tvsm-be-archetype` | library: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| tvsm-be-archetype/src/main/resources/archetype-resources | `tvsm-be-archetype/src/main/resources/archetype-resources` | service: 3 endpoints, 0 outbound calls, 0 messaging, 1 data-access |
| tvsm-be-core | `tvsm-be-core` | library: 0 endpoints, 1 outbound calls, 1 messaging, 0 data-access |
| tvsm-be-wiremock | `tvsm-be-wiremock` | library: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
tvs-cps-be-base-framework top-level folders (3 levels):

```
TVS-CPS-BE-BASE-FRAMEWORK/
├── tvsm-be-archetype/
│   ├── src/
│   │   ├── main/
├── tvsm-be-core/
│   ├── src/
│   │   ├── main/
│   │   ├── test/
├── tvsm-be-wiremock/
│   ├── src/
│   │   ├── main/
│   │   ├── test/
```

## Core Workflows in Code
tvs-cps-be-base-framework workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### OrderController
1. `tvsm-be-archetype/src/main/resources/archetype-resources/src/main/java/__packageInPathFormat__/controller/OrderController.java` receives 2 route(s), e.g. `GET /api/orders` → `OrderController.getOrders`.
3. Module `tvsm-be-archetype/src/main/resources/archetype-resources` data access via `tvsm-be-archetype/src/main/resources/archetype-resources/src/main/java/__packageInPathFormat__/entity/Order.java:11`.

### HealthController
1. `tvsm-be-archetype/src/main/resources/archetype-resources/src/main/java/__packageInPathFormat__/controller/HealthController.java` receives 1 route(s), e.g. `GET /api/health` → `HealthController.health`.
3. Module `tvsm-be-archetype/src/main/resources/archetype-resources` data access via `tvsm-be-archetype/src/main/resources/archetype-resources/src/main/java/__packageInPathFormat__/entity/Order.java:11`.

## Integration Clients
tvs-cps-be-base-framework outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `tvsm-be-core/src/main/java/com/tvsm/core/util/OAuthGenerationTokenUtil.java` | literal |
| kafka publish Unknown (`unresolved`) | `tvsm-be-core/src/main/java/com/tvsm/core/messaging/kafka/config/KafkaPublisherService.java:91` | unknown |
| data store (order_db) | `tvsm-be-archetype/src/main/resources/archetype-resources/src/main/java/__packageInPathFormat__/entity/Order.java:11` | Unknown |

## Cross-Cutting Concerns
tvs-cps-be-base-framework cross-cutting code:
- Auth: `tvsm-be-core/src/main/java/com/tvsm/core/security/RequestValidationFilter.java:12` (OncePerRequestFilter), `tvsm-be-core/src/main/java/com/tvsm/core/security/AuthenticationFilter.java:25` (OncePerRequestFilter)
- Error handling: `tvsm-be-core/src/main/java/com/tvsm/core/exception/GlobalExceptionHandler.java:25` (@RestControllerAdvice)
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
tvs-cps-be-base-framework build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`, 3 module poms)
- CI pipelines: `ci-pipeline.yaml:1`
