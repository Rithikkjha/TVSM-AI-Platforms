---
service_id: tvsm-marketplace-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvsm-marketplace-service — High-Level Code

## Application Overview
tvsm-marketplace-service (`tvsm-marketplace-service`) is a `backend-api` codebase; stacks java; head `d7d6c5fde5afad1fff0a78fede8d20f220e5f453`.
Entry points: `src/main/java/com/tvsmotor/marketplace/MarketplaceApplication.java`.

## Module Summary
tvsm-marketplace-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 35 endpoints, 46 outbound calls, 4 messaging, 2 data-access |

## Folder Structure
tvsm-marketplace-service top-level folders (3 levels):

```
tvsm-marketplace-service/
├── scripts/
│   ├── bash/
│   │   ├── aks/
│   ├── java/
│   ├── python/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
├── tvsm-marketplace-service-docs/
```

## Core Workflows in Code
tvsm-marketplace-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### TestController
1. `src/main/java/com/tvsmotor/marketplace/controller/TestController.java` receives 9 route(s), e.g. `DELETE /marketplace/v1/test/cache/{cacheName}/{key}` → `TestController.clearCache`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### OrderController
1. `src/main/java/com/tvsmotor/marketplace/controller/OrderController.java` receives 7 route(s), e.g. `GET /marketplace/v1/order/enums` → `OrderController.getEnums`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### FlipkartHelperController
1. `src/main/java/com/tvsmotor/marketplace/controller/FlipkartHelperController.java` receives 4 route(s), e.g. `GET /marketplace/test/flipkart/token/generate` → `FlipkartHelperController.generateAccessTokensForDealers`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### TestServiceBusController
1. `src/main/java/com/tvsmotor/marketplace/controller/TestServiceBusController.java` receives 3 route(s), e.g. `GET /marketplace/v1/test/service-bus/start-receiver` → `TestServiceBusController.startTheReceiver`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### ProductsController
1. `src/main/java/com/tvsmotor/marketplace/controller/ProductsController.java` receives 2 route(s), e.g. `POST /marketplace/v1/products/upsert` → `ProductsController.upsertTvsProductDetails`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### AmazonListingSyncController
1. `src/main/java/com/tvsmotor/marketplace/controller/AmazonListingSyncController.java` receives 2 route(s), e.g. `PUT /marketplace/v1/amazon/listing` → `AmazonListingSyncController.triggerListingSync`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### DealerInventoryController
1. `src/main/java/com/tvsmotor/marketplace/controller/DealerInventoryController.java` receives 1 route(s), e.g. `POST /marketplace/v1/dealer-inventory/sync` → `DealerInventoryController.syncDealerInventory`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### DealerMarketplaceMappingController
1. `src/main/java/com/tvsmotor/marketplace/controller/DealerMarketplaceMappingController.java` receives 1 route(s), e.g. `POST /marketplace/v1/dealer-marketplace-mapping/{marketplace}/upsert` → `DealerMarketplaceMappingController.upsertDealerMarketplaceMappings`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### DealerRefreshTokenController
1. `src/main/java/com/tvsmotor/marketplace/controller/DealerRefreshTokenController.java` receives 1 route(s), e.g. `POST /marketplace/v1/dealer-refresh-token/upsert` → `DealerRefreshTokenController.upsertDealerRefreshTokens`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### PartIdModelIdTransitionController
1. `src/main/java/com/tvsmotor/marketplace/controller/PartIdModelIdTransitionController.java` receives 1 route(s), e.g. `POST /marketplace/v1/part-id-model-id-transitions/upload` → `PartIdModelIdTransitionController.uploadTransitions`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### DealerVehicleMappingController
1. `src/main/java/com/tvsmotor/marketplace/controller/DealerVehicleMappingController.java` receives 1 route(s), e.g. `POST /marketplace/v1/{marketplace}/dealer-vehicle-map` → `DealerVehicleMappingController.ingestExcel`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### FlipkartWebhookController
1. `src/main/java/com/tvsmotor/marketplace/controller/FlipkartWebhookController.java` receives 1 route(s), e.g. `POST /marketplace/webhook/flipkart/order-management/notifications-receiver/dealer/common` → `FlipkartWebhookController.orderNotificationsReceiver_DealerAsASellerModel`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### FlipkartSaltKeyMetadataController
1. `src/main/java/com/tvsmotor/marketplace/controller/FlipkartSaltKeyMetadataController.java` receives 1 route(s), e.g. `PUT /marketplace/flipkart-salt-key-metadata/salt-key` → `FlipkartSaltKeyMetadataController.updateSaltKey`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### DealerController
1. `src/main/java/com/tvsmotor/marketplace/controller/DealerController.java` receives 1 route(s), e.g. `PUT /marketplace/v1/dealer/sync` → `DealerController.syncDealers`.
2. Module `.` makes outbound calls to: `Unknown(config:amazon.lwa.api.base-url)`, `Unknown(config:amazon.sp.api.base-url)`, `Unknown(config:b2c.token.url)`, `Unknown(config:dms.api.base-url)`, `Unknown(config:flipkart.partner.api.base.url)`, `Unknown(config:flipkart.seller.api.base-url)`, `Unknown(config:lead.service.api.base.url)`, `Unknown(config:location-master.base.url)`, `Unknown(config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId)`, `Unknown(literal)`, `booking-crud-services`, `master-data-platform`.
3. Module `.` data access via `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1`, `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12`.

### Job ServerMetricsService.scheduledLogServerMetrics
1. `src/main/java/com/tvsmotor/marketplace/service/ServerMetricsService.java:31` runs on cron `0 * * * * ?`.

### Job AmazonPriceUpdateExecutorService.scheduledDrain
1. `src/main/java/com/tvsmotor/marketplace/service/price_update/AmazonPriceUpdateExecutorService.java:104` runs on fixed-delay `None`.

### Job FlipkartPriceUpdateExecutorService.scheduledDrain
1. `src/main/java/com/tvsmotor/marketplace/service/price_update/FlipkartPriceUpdateExecutorService.java:83` runs on fixed-delay `None`.

### Job MarketplacePriceUpdateTaskService.recoverStaleLocks
1. `src/main/java/com/tvsmotor/marketplace/service/price_update/MarketplacePriceUpdateTaskService.java:162` runs on fixed-delay `None`.

### Job MarketplacePriceUpdateTaskService.cleanupDoneTasks
1. `src/main/java/com/tvsmotor/marketplace/service/price_update/MarketplacePriceUpdateTaskService.java:174` runs on cron `None`.

### Consumer uat.booking
1. `src/main/java/com/tvsmotor/marketplace/config/ECommerceServiceBusConfig.java:74` handles messages (azure-service-bus, trigger processor).

### Consumer xxxx
1. `src/main/java/com/tvsmotor/marketplace/config/ECommerceServiceBusConfig.java:156` handles messages (azure-service-bus, trigger processor).

### Consumer xxx
1. `src/main/java/com/tvsmotor/marketplace/config/ECommerceServiceBusConfig.java:112` handles messages (azure-service-bus, trigger processor).

### Consumer dev.catalog.price_updates
1. `src/main/java/com/tvsmotor/marketplace/config/ECommerceServiceBusConfig.java:32` handles messages (azure-service-bus, trigger processor).

## Integration Clients
tvsm-marketplace-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java` | config:amazon.lwa.api.base-url |
| Unknown | `src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java` | config:amazon.sp.api.base-url |
| Unknown | `src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java` | config:b2c.token.url |
| Unknown | `src/main/java/com/tvsmotor/marketplace/service/dms/DmsApiCallerService.java` | config:dms.api.base-url |
| Unknown | `src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java` | config:flipkart.partner.api.base.url |
| Unknown | `src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java` | config:flipkart.seller.api.base-url |
| Unknown | `src/main/java/com/tvsmotor/marketplace/service/LeadApiCallerService.java` | config:lead.service.api.base.url |
| Unknown | `src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java` | config:location-master.base.url |
| Unknown | `src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java` | config:priceUpdate.flipkart.dealer_as_a_seller.tvsClientId |
| Unknown | `src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java`, `src/test/java/com/tvsmotor/marketplace/service/OkHttpServiceTest.java`, `src/test/java/com/tvsmotor/marketplace/service/dms/DmsHttpRequestExecutorTest.java` | literal |
| `booking-crud-services` | `src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java` | config:bookingService.api.base-url |
| `master-data-platform` | `src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java` | config:mdp.api.base-url |
| `notification-service` | `src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java` | config:notification.base-url |
| azure-service-bus subscribe uat.booking | `src/main/java/com/tvsmotor/marketplace/config/ECommerceServiceBusConfig.java:74` | spring.jms.servicebus.topic.bookingUpdates.name |
| azure-service-bus subscribe xxxx | `src/main/java/com/tvsmotor/marketplace/config/ECommerceServiceBusConfig.java:156` | spring.jms.servicebus.topic.catalogProductUpdates.name |
| azure-service-bus subscribe xxx | `src/main/java/com/tvsmotor/marketplace/config/ECommerceServiceBusConfig.java:112` | spring.jms.servicebus.topic.priceEngineUpdates.name |
| azure-service-bus subscribe dev.catalog.price_updates | `src/main/java/com/tvsmotor/marketplace/config/ECommerceServiceBusConfig.java:32` | spring.jms.servicebus.topic.vehiclePriceData.name |
| data store (db) | `src/main/resources/db/migration/v1.10__add_flipkart_current_status_to_orders_20260326.sql:1` | Unknown |
| data store (marketplace) | `src/main/java/com/tvsmotor/marketplace/entity/AuditLog.java:12` | Unknown |

## Cross-Cutting Concerns
tvsm-marketplace-service cross-cutting code:
- Auth: `src/main/java/com/tvsmotor/marketplace/config/MarketplaceOncePerRequestFilter.java:19` (OncePerRequestFilter)
- Error handling: `src/main/java/com/tvsmotor/marketplace/exceptions/handlers/RestExceptionHandler.java:23` (@ControllerAdvice)
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
tvsm-marketplace-service build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `AST_Image_Scan_marketplace_Pipeline.yml:1`, `AST_MDP_marketplace_PROD_Pipeline.yml:1`, `AST_MDP_marketplace_UAT_Pipeline.yml:1`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`, `sonar_ci_pipeline.yml:1`
