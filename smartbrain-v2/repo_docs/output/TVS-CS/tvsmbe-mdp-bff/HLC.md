---
service_id: tvsmbe-mdp-bff
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvsmbe-mdp-bff — High-Level Code

## Application Overview
tvsmbe-mdp-bff (`tvsmbe-mdp-bff`) is a `bff` codebase; stacks java; head `53bd2ac505ed791d4865d4dcd925317716c8357d`.
Entry points: `inbound/src/main/java/com/tvsmotor/bff/BffApplication.java`, `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/OutboundApplication.java`.

## Module Summary
tvsmbe-mdp-bff modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| inbound | `inbound` | service: 5 endpoints, 6 outbound calls, 0 messaging, 2 data-access |
| outbound | `outbound` | service: 2 endpoints, 8 outbound calls, 1 messaging, 1 data-access |

## Folder Structure
tvsmbe-mdp-bff top-level folders (3 levels):

```
tvsmbe-mdp-bff/
├── inbound/
│   ├── src/
│   │   ├── main/
│   │   ├── test/
├── outbound/
│   ├── src/
│   │   ├── main/
│   │   ├── test/
```

## Core Workflows in Code
tvsmbe-mdp-bff workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### MdpController
1. `inbound/src/main/java/com/tvsmotor/bff/controller/MdpController.java` receives 3 route(s), e.g. `GET /mdp-bff/v1/mdp/dealer/{sapDealerCode}` → `MdpController.getDealerData`.
2. Module `inbound` makes outbound calls to: `Unknown(config:azure.b2c.token.url)`, `Unknown(config:mdp.get-dealer-data.api-url)`, `Unknown(literal)`, `master-data-platform`.
3. Module `inbound` data access via `inbound/src/main/resources/db/migrations/v1.1_audit_log_table_20240523.sql:1`, `inbound/src/main/java/com/tvsmotor/bff/entity/AuditLog.java:10`.

### TestController
1. `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/controller/TestController.java` receives 2 route(s), e.g. `GET /mdp-bff-outbound/v1/test/health` → `TestController.healthTest`.
2. Module `outbound` makes outbound calls to: `Unknown(config:azure.b2c.token.url)`, `Unknown(config:si.outletApi.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`.
3. Module `outbound` data access via `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/entity/AuditLog.java:11`.

### TestController
1. `inbound/src/main/java/com/tvsmotor/bff/controller/TestController.java` receives 1 route(s), e.g. `GET /mdp-bff/v1/test/hello` → `TestController.helloCode`.
2. Module `inbound` makes outbound calls to: `Unknown(config:azure.b2c.token.url)`, `Unknown(config:mdp.get-dealer-data.api-url)`, `Unknown(literal)`, `master-data-platform`.
3. Module `inbound` data access via `inbound/src/main/resources/db/migrations/v1.1_audit_log_table_20240523.sql:1`, `inbound/src/main/java/com/tvsmotor/bff/entity/AuditLog.java:10`.

### WebHookController
1. `inbound/src/main/java/com/tvsmotor/bff/controller/WebHookController.java` receives 1 route(s), e.g. `POST /mdp-bff/webhook/v1/{mdpModule}/{externalClient}/{webHookEventType}` → `WebHookController.handleWebhook`.
2. Module `inbound` makes outbound calls to: `Unknown(config:azure.b2c.token.url)`, `Unknown(config:mdp.get-dealer-data.api-url)`, `Unknown(literal)`, `master-data-platform`.
3. Module `inbound` data access via `inbound/src/main/resources/db/migrations/v1.1_audit_log_table_20240523.sql:1`, `inbound/src/main/java/com/tvsmotor/bff/entity/AuditLog.java:10`.

### Job CronService.logMetricsPeriodically
1. `inbound/src/main/java/com/tvsmotor/bff/service/CronService.java:23` runs on fixed-rate `60000`.

### Job CronService.logMetricsPeriodically
1. `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/CronService.java:24` runs on fixed-rate `60000`.

### Consumer dev.mdp.dealer_data
1. `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/config/BffServiceBusConfig.java:26` handles messages (azure-service-bus, trigger processor).

## Integration Clients
tvsmbe-mdp-bff outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `inbound/src/main/java/com/tvsmotor/bff/service/AzureB2CTokenGenerationService.java`, `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/AzureB2CTokenGenerationService.java` | config:azure.b2c.token.url |
| Unknown | `inbound/src/main/java/com/tvsmotor/bff/service/MdpDealerOperationsService.java` | config:mdp.get-dealer-data.api-url |
| Unknown | `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/OkHttpService.java` | config:si.outletApi.baseUrl |
| Unknown | `inbound/src/test/java/com/tvsmotor/bff/service/AzureB2CTokenGenerationServiceTest.java`, `inbound/src/test/java/com/tvsmotor/bff/service/OkHttpServiceTest.java`, `outbound/src/test/java/com/tvsmotor/mdp_bff/outbound/service/AzureB2CTokenGenerationServiceTest.java` …+1 | literal |
| `master-data-platform` | `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/MdpDealerOperationsService.java` | config:mdp.api.dealer.mapDealerWithKNumber |
| `master-data-platform` | `inbound/src/main/java/com/tvsmotor/bff/service/MdpDealerOperationsService.java` | config:mdp.get-dealer-data.based-on-filters.api-url |
| `notification-service` | `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/NotificationSenderService.java` | config:notification.base-url |
| azure-service-bus subscribe dev.mdp.dealer_data | `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/config/BffServiceBusConfig.java:26` | spring.jms.servicebus.topic.mdpDealerData.name |
| data store (db) | `inbound/src/main/resources/db/migrations/v1.1_audit_log_table_20240523.sql:1` | Unknown |
| data store (tvsmazebffsdbdev01) | `inbound/src/main/java/com/tvsmotor/bff/entity/AuditLog.java:10` | Unknown |
| data store (tvsmazebffsdbdev01) | `outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/entity/AuditLog.java:11` | Unknown |

## Cross-Cutting Concerns
tvsmbe-mdp-bff cross-cutting code:
- Auth: none found
- Error handling: `inbound/src/main/java/com/tvsmotor/bff/exceptions/handlers/RestExceptionHandler.java:18` (@ControllerAdvice)
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
tvsmbe-mdp-bff build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`, 2 module poms)
- CI pipelines: `AST_Image_Scan_MDP_BFF_Inbound_tvsmbe_mdp_bff_UAT_Pipeline.yml:1`, `AST_Image_Scan_MDP_BFF_Outbound_tvsmbe_mdp_bff_UAT_Pipeline.yml:1`, `inbound/AST_MDP_BFF_tvsmbe_mdp_bff_PROD_Pipeline.yml:1`, `inbound/AST_MDP_BFF_tvsmbe_mdp_bff_UAT_Pipeline.yml:1`, `inbound/cd-pipeline.yaml:1`, `inbound/ci-pipeline.yaml:1`, `inbound/sonar_ci_pr_pipelines.yml:1`, `outbound/cd-pipeline.yaml:1`, `outbound/ci-pipeline.yaml:1`, `outbound/sonar_ci_pr_pipelines.yml:1`
