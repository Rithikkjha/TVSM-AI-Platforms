---
service_id: master-data-platform
doc_type: hlc
last_reviewed: 2026-10-11
---

# master-data-platform — High-Level Code

## Application Overview
master-data-platform is a Spring Boot 3 web app, entry `com.tvsmotor.mdp.MdpApplication` (`src/main/java/com/tvsmotor/mdp/MdpApplication.java`, `@EnableRetry`), with springdoc OpenAPI at `/v3/api-docs` and context path `/mdp`. Artifact `com.tvsmotor:mdp` 1.0.0 (jar).

## Module Summary
master-data-platform modules:

| Module | Path | Responsibility |
|---|---|---|
| Controllers | `src/main/java/com/tvsmotor/mdp/controller` | Dealer, flags, pipeline trigger, test & migration endpoints |
| Dealer | `src/main/java/com/tvsmotor/mdp/dealer` | Dealer models incl. DMS service-bus payloads |
| Product | `src/main/java/com/tvsmotor/mdp/product` | Vehicle product endpoints/services |
| Product part | `src/main/java/com/tvsmotor/mdp/product_part` | Part data + Service Bus sender |
| Product MNA | `src/main/java/com/tvsmotor/mdp/product_mna` | MNA data |
| Price | `src/main/java/com/tvsmotor/mdp/price` | Vehicle price data + sender |
| Part price | `src/main/java/com/tvsmotor/mdp/part_price` | Part price data + sender |
| Services | `src/main/java/com/tvsmotor/mdp/service` | Business services, batch processing, service_bus, notification_service |
| Common | `src/main/java/com/tvsmotor/mdp/common` | Cache, exceptions, request models, cron |
| Config | `src/main/java/com/tvsmotor/mdp/config` | Filter, Service Bus, DB, OkHttp config |
| Entities/Repos | `src/main/java/com/tvsmotor/mdp/entity` | JPA entities; `repository/` Spring Data repos |

## Folder Structure
master-data-platform repository layout (top levels):

```
master-data-platform/
├── Dockerfile, pom.xml, *.yml pipelines
├── azure-pipelines/ (prod.ci, prod.cd, uat.ci)
├── archive/sql/
├── master-data-platform-docs/
├── script/ (bash/aks, java/service_bus)
└── src/main/java/com/tvsmotor/mdp/
    ├── controller/ (+ migration/)
    ├── dealer/ product/ product_part/ product_mna/ price/ part_price/
    ├── service/ (batch_processing/, service_bus/, notification_service/, migration/)
    ├── common/ config/ entity/ repository/ enums/ model/ aop/ utils/
```

## Core Workflows in Code
### Get dealer
1. `DealerController.getDealerData` (`controller/DealerController.java:20`) handles `GET /mdp/v1/dealer/{sapDealerCode}` (`skipCache` query).
2. Dealer services (`service/DealerService.java`, `service/DealerCacheService.java`) read from Redis cache or MySQL via repositories.

### Batch ingestion
1. `DE_PipelineController.startProcessing` (`controller/DE_PipelineController.java:20`) takes a `batchProcessingType` (SAP_DATA, SHAREPOINT_DATA, PRODUCT_VEHICLE_SAP_DATA, PRICE_VEHICLE_SAP_DATA, PART_SAP_DATA, …).
2. Processors in `service/batch_processing/` (e.g. `AdfSapDealerDataProcessorService.java`) load staged SAP/SharePoint tables and update master tables.
3. Changes are pushed to Service Bus topics by `*DataSenderService` classes; unexpected events notify via `UnexpectedEventsNotificationSenderService` → `notification-service`.

## Integration Clients
master-data-platform integration wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | Unknown | literal |
| Unknown | Unknown | literal |
| Unknown | Unknown | config:azure.b2c.token.url |
| notification-service | Unknown | config:notification.base-url |
| (call `GET /v2/brands/{}/stores.json`) | okhttp `src/main/java/com/tvsmotor/mdp/service/LatLongService.java:66` | literal |
| (call `POST /oauth/token`) | okhttp `src/main/java/com/tvsmotor/mdp/service/LatLongService.java:129` | literal |
| (call `POST /`) | okhttp `src/main/java/com/tvsmotor/mdp/service/AzureB2CTokenGenerationService.java:47` | config:azure.b2c.token.url |
| (call `POST /api/v1/notification/email`) | okhttp `src/main/java/com/tvsmotor/mdp/service/OkHttpService.java:24` | config:notification.base-url |
| topic `local.mdp.dealer_data` (azure-service-bus) | `src/main/java/com/tvsmotor/mdp/service/service_bus/DealerDataSenderService.java:87` | config:spring.jms.servicebus.topic.dealerData.name |
| topic `local.dms.dealer_data` (azure-service-bus) | `src/main/java/com/tvsmotor/mdp/service/service_bus/DealerDataSenderService.java:176` | config:spring.jms.servicebus.topic.dmsDealerData.name |
| topic `local.mdp.part_data` (azure-service-bus) | `src/main/java/com/tvsmotor/mdp/product_part/service/service_bus/PartDataSenderService.java:45` | config:spring.jms.servicebus.topic.partData.name |
| topic `local.mdp.part.price` (azure-service-bus) | `src/main/java/com/tvsmotor/mdp/part_price/service/service_bus/PartPriceDataSenderService.java:45` | config:spring.jms.servicebus.topic.partPriceData.name |
| topic `local.mdp.price.vehicle` (azure-service-bus) | `src/main/java/com/tvsmotor/mdp/price/service/service_bus/PriceVehicleDataSenderService.java:52` | config:spring.jms.servicebus.topic.priceVehicleData.name |
| topic `local.mdp.product.mna` (azure-service-bus) | `src/main/java/com/tvsmotor/mdp/product_mna/service/service_bus/ProductMnaDataSenderService.java:50` | config:spring.jms.servicebus.topic.productMnaData.name |
| topic `local.mdp.product.vehicle` (azure-service-bus) | `src/main/java/com/tvsmotor/mdp/product/service/service_bus/ProductVehicleDataSenderService.java:50` | config:spring.jms.servicebus.topic.productVehicleData.name |
| consume `local.mdp.dealer_data` (azure-service-bus) | `src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:50` | config:spring.jms.servicebus.topic.dealerData.name |
| consume `local.dms.dealer_data` (azure-service-bus) | `src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:91` | config:spring.jms.servicebus.topic.dmsDealerData.name |
| consume `dev.mdp.dealer_data` (azure-service-bus) | `script/java/service_bus/DealerDataConsumer.java:17` | literal |
| consume `local.mdp.part` (azure-service-bus) | `script/java/service_bus/ProductPartDataConsumer.java:17` | literal |
| consume `local.mdp.price.vehicle` (azure-service-bus) | `script/java/service_bus/PriceVehicleDataConsumer.java:17` | literal |
| consume `mdp.product.vehicle` (azure-service-bus) | `script/java/service_bus/ProductVehicleDataConsumer.java:17` | literal |
| store `mdp_20230904` (mysql) | `src/main/java/com/tvsmotor/mdp/common/entity/AuditLog.java:11` | Unknown |
| store `_` (other) | `archive/sql/20230519_microsoft_SQL-DDLs.sql:17` | Unknown |
| store `_` (redis) | `src/main/java/com/tvsmotor/mdp/common/cache/CacheService.java:25` | Unknown |

## Cross-Cutting Concerns
master-data-platform: auth + request logging filter (`config/MdpOncePerRequestFilter.java`), global `RestExceptionHandler` (`common/exceptions/handlers/RestExceptionHandler.java:32`), Spring Retry, Redis cache (`common/cache/CacheService.java`), AOP package (`aop/`), Lombok.

## Build and Test
master-data-platform: `mvn -f pom.xml clean install` (`Dockerfile`); tests under `src/test/java`; Sonar PR pipeline `sonar_ci_pr_pipelines.yml`.
