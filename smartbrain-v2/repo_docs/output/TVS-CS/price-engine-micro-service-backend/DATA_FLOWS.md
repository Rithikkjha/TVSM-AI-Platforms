---
service_id: price-engine-micro-service-backend
doc_type: data_flows
last_reviewed: 2026-10-11
flows: [catalog-scheduler--external-salesforce-7dacdd, catalog-scheduler--external-salesforce-ee1cc0, catalog-scheduler--external-salesforce-fc87bd, catalog-scheduler--external-salesforce-fdb9af, catalog-scheduler--lms-crm, catalog-scheduler--lms-tvs-credit-bd6cbe, catalog-scheduler--lms-tvs-credit-db10c6, catalog-scheduler--notification-dispatcher-service, cbs-admin-portal--price-engine-micro-service-backend, location-frontend--price-engine-micro-service-backend-17193f, location-frontend--price-engine-micro-service-backend-51d763, master-data-platform--price-engine-micro-service-backend, tvsm-auth--price-engine-micro-service-backend, tvsm-marketplace-service--price-engine-micro-service-backend, tvsmbe-location--price-engine-micro-service-backend-45a56f, tvsmbe-location--price-engine-micro-service-backend-834d3e, tvsmbe-mdp-bff--price-engine-micro-service-backend]   # flow_ids, must match service.yaml `flows`
---

# price-engine-micro-service-backend — Data Flows

## Flow Index
price-engine-micro-service-backend takes part in 17 end-to-end flow(s) in registry/flows.json.

| flow_id | Name | Role of price-engine-micro-service-backend | Trigger |
|---|---|---|---|
| catalog-scheduler--external-salesforce-7dacdd | catalog-scheduler → external:salesforce (5 hops) | participant | scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller) |
| catalog-scheduler--external-salesforce-ee1cc0 | catalog-scheduler → external:salesforce (4 hops) | participant | scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller) |
| catalog-scheduler--external-salesforce-fc87bd | catalog-scheduler → external:salesforce (5 hops) | participant | scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller) |
| catalog-scheduler--external-salesforce-fdb9af | catalog-scheduler → external:salesforce (5 hops) | participant | scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller) |
| catalog-scheduler--lms-crm | catalog-scheduler → lms-crm (5 hops) | participant | scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller) |
| catalog-scheduler--lms-tvs-credit-bd6cbe | catalog-scheduler → lms-tvs-credit (5 hops) | participant | scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller) |
| catalog-scheduler--lms-tvs-credit-db10c6 | catalog-scheduler → lms-tvs-credit (4 hops) | participant | scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller) |
| catalog-scheduler--notification-dispatcher-service | catalog-scheduler → notification-dispatcher-service (5 hops) | participant | scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller) |
| cbs-admin-portal--price-engine-micro-service-backend | cbs-admin-portal → price-engine-micro-service-backend (3 hops) | terminal | user action in cbs-admin-portal (frontend) |
| location-frontend--price-engine-micro-service-backend-17193f | location-frontend → price-engine-micro-service-backend (4 hops) | terminal | user action in location-frontend (frontend) |
| location-frontend--price-engine-micro-service-backend-51d763 | location-frontend → price-engine-micro-service-backend (3 hops) | terminal | user action in location-frontend (frontend) |
| master-data-platform--price-engine-micro-service-backend | master-data-platform → price-engine-micro-service-backend (1 hop) | terminal | scheduled job(s) in master-data-platform (job-to-call link not resolved): CronService.logMetricsPeriodically; master-data-platform publishes mdp.price.vehicle, mdp.product.vehicle |
| tvsm-auth--price-engine-micro-service-backend | tvsm-auth → price-engine-micro-service-backend (2 hops) | terminal | scheduled job(s) in tvsm-auth (job-to-call link not resolved): CacheClearScheduler.evictAllCachesAtIntervals, NotificationReminder.sendSMSForFaceLogin |
| tvsm-marketplace-service--price-engine-micro-service-backend | tvsm-marketplace-service → price-engine-micro-service-backend (2 hops) | terminal | scheduled job(s) in tvsm-marketplace-service (job-to-call link not resolved): AmazonPriceUpdateExecutorService.scheduledDrain, FlipkartPriceUpdateExecutorService.scheduledDrain, MarketplacePriceUpdateTaskService.cleanupDoneTasks (+2 more); request to tvsm-marketplace-service from outside the registry (no internal caller) |
| tvsmbe-location--price-engine-micro-service-backend-45a56f | tvsmbe-location → price-engine-micro-service-backend (3 hops) | terminal | scheduled job(s) in tvsmbe-location (job-to-call link not resolved): CronService.logMetricsPeriodically |
| tvsmbe-location--price-engine-micro-service-backend-834d3e | tvsmbe-location → price-engine-micro-service-backend (2 hops) | terminal | scheduled job(s) in tvsmbe-location (job-to-call link not resolved): CronService.logMetricsPeriodically |
| tvsmbe-mdp-bff--price-engine-micro-service-backend | tvsmbe-mdp-bff → price-engine-micro-service-backend (2 hops) | terminal | scheduled job(s) in tvsmbe-mdp-bff (job-to-call link not resolved): CronService.logMetricsPeriodically |

## Flow: catalog-scheduler--external-salesforce-7dacdd
Summary: Starting at `catalog-scheduler` (scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller)), the flow passes through `price-engine-micro-service-backend`, `master-data-platform`, `notification-service`, `notification-dispatcher-service` and ends at `external:salesforce`, using 4 sync HTTP hop(s) and 1 async event hop(s); price-engine-micro-service-backend role: participant; confidence medium.

```mermaid
sequenceDiagram
  participant catalog_scheduler as catalog-scheduler
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  participant master_data_platform as master-data-platform
  participant notification_service as notification-service
  participant notification_dispatcher_service as notification-dispatcher-service
  participant external_salesforce as external:salesforce
  catalog_scheduler->>price_engine_micro_service_backend: GET /on-road-prices/vehicles/engineType/{engineType}
  price_engine_micro_service_backend->>master_data_platform: POST /mdp/v1/price/test/service-bus/push-price-data (+1 more)
  master_data_platform->>notification_service: POST /api/v1/notification/email
  notification_service--)notification_dispatcher_service: topic:notifications
  notification_dispatcher_service->>external_salesforce: sdk-symbol:SalesforceAuthGen
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | catalog-scheduler | price-engine-micro-service-backend | GET /on-road-prices/vehicles/engineType/{engineType} | Unknown | sync | medium |
| 2 | price-engine-micro-service-backend | master-data-platform | POST /mdp/v1/price/test/service-bus/push-price-data, POST /mdp/v1/product/test/service-bus/push-product-data | GeneralResponse | sync | high |
| 3 | master-data-platform | notification-service | POST /api/v1/notification/email | EmailNotification, NotificationResponse | sync | high |
| 4 | notification-service | notification-dispatcher-service | topic:notifications | Unknown | async | medium |
| 5 | notification-dispatcher-service | external:salesforce | sdk-symbol:SalesforceAuthGen | Unknown | sync | high |

Data touched: catalog-scheduler: mongo; price-engine-micro-service-backend: mongo, redis; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; notification-service: mongo; notification-dispatcher-service: mongo

Failure points: hop 1 catalog-scheduler → price-engine-micro-service-backend: criticality hard; hop 2 price-engine-micro-service-backend → master-data-platform: criticality hard; hop 3 master-data-platform → notification-service: criticality hard; hop 4 notification-service → notification-dispatcher-service: criticality async; hop 5 notification-dispatcher-service → external:salesforce: criticality hard

Evidence:
- hop 1 (catalog-scheduler → price-engine-micro-service-backend): `Catalog-Scheduler/src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js:21`, `Price-Engine-MicroService-Backend/src/routes/api/on-road-price-routes.ts:31`
- hop 2 (price-engine-micro-service-backend → master-data-platform): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:23`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/controller/TestPriceServiceBusController.java:18`, `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:9` (+1 more)
- hop 3 (master-data-platform → notification-service): `master-data-platform/src/main/java/com/tvsmotor/mdp/service/OkHttpService.java:24`, `master-data-platform/src/main/java/com/tvsmotor/mdp/service/notification_service/NotificationSenderService.java:69`, `notification-service/src/main/java/com/tvsmotor/notification/controller/NotificationController.java:23`
- hop 4 (notification-service → notification-dispatcher-service): `notification-dispatcher-service/src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:33`, `notification-dispatcher-service/src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:34`, `notification-service/src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java:37` (+1 more)
- hop 5 (notification-dispatcher-service → external:salesforce): `notification-dispatcher-service/src/main/java/com/tvsmotor/notificationdispatcher/controller/SalesforceTokenController.java:18`, `notification-dispatcher-service/src/main/java/com/tvsmotor/notificationdispatcher/model/dto/salesforce/SalesforceData.java:5`, `notification-dispatcher-service/src/main/java/com/tvsmotor/notificationdispatcher/model/dto/salesforce/SalesforceTemplateKeys.java:8`

## Flow: catalog-scheduler--external-salesforce-ee1cc0
Summary: Starting at `catalog-scheduler` (scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller)), the flow passes through `price-engine-micro-service-backend`, `master-data-platform`, `notification-service` and ends at `external:salesforce`, using 4 sync HTTP hop(s) and 0 async event hop(s); price-engine-micro-service-backend role: participant; confidence medium.

```mermaid
sequenceDiagram
  participant catalog_scheduler as catalog-scheduler
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  participant master_data_platform as master-data-platform
  participant notification_service as notification-service
  participant external_salesforce as external:salesforce
  catalog_scheduler->>price_engine_micro_service_backend: GET /on-road-prices/vehicles/engineType/{engineType}
  price_engine_micro_service_backend->>master_data_platform: POST /mdp/v1/price/test/service-bus/push-price-data (+1 more)
  master_data_platform->>notification_service: POST /api/v1/notification/email
  notification_service->>external_salesforce: sdk-symbol:SalesforceBlobConfig
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | catalog-scheduler | price-engine-micro-service-backend | GET /on-road-prices/vehicles/engineType/{engineType} | Unknown | sync | medium |
| 2 | price-engine-micro-service-backend | master-data-platform | POST /mdp/v1/price/test/service-bus/push-price-data, POST /mdp/v1/product/test/service-bus/push-product-data | GeneralResponse | sync | high |
| 3 | master-data-platform | notification-service | POST /api/v1/notification/email | EmailNotification, NotificationResponse | sync | high |
| 4 | notification-service | external:salesforce | sdk-symbol:SalesforceBlobConfig | Unknown | sync | high |

Data touched: catalog-scheduler: mongo; price-engine-micro-service-backend: mongo, redis; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; notification-service: mongo

Failure points: hop 1 catalog-scheduler → price-engine-micro-service-backend: criticality hard; hop 2 price-engine-micro-service-backend → master-data-platform: criticality hard; hop 3 master-data-platform → notification-service: criticality hard; hop 4 notification-service → external:salesforce: criticality hard

Evidence:
- hop 1 (catalog-scheduler → price-engine-micro-service-backend): `Catalog-Scheduler/src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js:21`, `Price-Engine-MicroService-Backend/src/routes/api/on-road-price-routes.ts:31`
- hop 2 (price-engine-micro-service-backend → master-data-platform): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:23`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/controller/TestPriceServiceBusController.java:18`, `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:9` (+1 more)
- hop 3 (master-data-platform → notification-service): `master-data-platform/src/main/java/com/tvsmotor/mdp/service/OkHttpService.java:24`, `master-data-platform/src/main/java/com/tvsmotor/mdp/service/notification_service/NotificationSenderService.java:69`, `notification-service/src/main/java/com/tvsmotor/notification/controller/NotificationController.java:23`
- hop 4 (notification-service → external:salesforce): `notification-service/src/main/java/com/tvsmotor/notification/config/SalesforceBlobConfig.java:10`, `notification-service/src/main/java/com/tvsmotor/notification/cronjobs/SalesforceBlobStatusJob.java:17`, `notification-service/src/main/java/com/tvsmotor/notification/model/dto/salesforce/SalesforceData.java:8`

## Flow: catalog-scheduler--external-salesforce-fc87bd
Summary: Starting at `catalog-scheduler` (scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller)), the flow passes through `price-engine-micro-service-backend`, `master-data-platform`, `tvsmbe-mdp-bff`, `notification-service` and ends at `external:salesforce`, using 4 sync HTTP hop(s) and 1 async event hop(s); price-engine-micro-service-backend role: participant; confidence medium.

```mermaid
sequenceDiagram
  participant catalog_scheduler as catalog-scheduler
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  participant master_data_platform as master-data-platform
  participant tvsmbe_mdp_bff as tvsmbe-mdp-bff
  participant notification_service as notification-service
  participant external_salesforce as external:salesforce
  catalog_scheduler->>price_engine_micro_service_backend: GET /on-road-prices/vehicles/engineType/{engineType}
  price_engine_micro_service_backend->>master_data_platform: POST /mdp/v1/price/test/service-bus/push-price-data (+1 more)
  master_data_platform--)tvsmbe_mdp_bff: topic:mdp.dealer_data
  tvsmbe_mdp_bff->>notification_service: POST /api/v1/notification/email
  notification_service->>external_salesforce: sdk-symbol:SalesforceBlobConfig
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | catalog-scheduler | price-engine-micro-service-backend | GET /on-road-prices/vehicles/engineType/{engineType} | Unknown | sync | medium |
| 2 | price-engine-micro-service-backend | master-data-platform | POST /mdp/v1/price/test/service-bus/push-price-data, POST /mdp/v1/product/test/service-bus/push-product-data | GeneralResponse | sync | high |
| 3 | master-data-platform | tvsmbe-mdp-bff | topic:mdp.dealer_data | DealerData | async | medium |
| 4 | tvsmbe-mdp-bff | notification-service | POST /api/v1/notification/email | EmailNotification, NotificationResponse | sync | high |
| 5 | notification-service | external:salesforce | sdk-symbol:SalesforceBlobConfig | Unknown | sync | high |

Data touched: catalog-scheduler: mongo; price-engine-micro-service-backend: mongo, redis; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; tvsmbe-mdp-bff: mysql, mysql:tvsmazcmndbsdev01-ci.mysql.database.azure.com:tvsmazebffsdbdev01; notification-service: mongo

Failure points: hop 1 catalog-scheduler → price-engine-micro-service-backend: criticality hard; hop 2 price-engine-micro-service-backend → master-data-platform: criticality hard; hop 3 master-data-platform → tvsmbe-mdp-bff: criticality async; hop 4 tvsmbe-mdp-bff → notification-service: criticality hard; hop 5 notification-service → external:salesforce: criticality hard

Evidence:
- hop 1 (catalog-scheduler → price-engine-micro-service-backend): `Catalog-Scheduler/src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js:21`, `Price-Engine-MicroService-Backend/src/routes/api/on-road-price-routes.ts:31`
- hop 2 (price-engine-micro-service-backend → master-data-platform): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:23`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/controller/TestPriceServiceBusController.java:18`, `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:9` (+1 more)
- hop 3 (master-data-platform → tvsmbe-mdp-bff): `master-data-platform/src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:26`, `master-data-platform/src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:27`, `tvsmbe-mdp-bff/outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/config/BffServiceBusConfig.java:24` (+1 more)
- hop 4 (tvsmbe-mdp-bff → notification-service): `notification-service/src/main/java/com/tvsmotor/notification/controller/NotificationController.java:23`, `tvsmbe-mdp-bff/outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/NotificationSenderService.java:46`, `tvsmbe-mdp-bff/outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/OkHttpService.java:88`
- hop 5 (notification-service → external:salesforce): `notification-service/src/main/java/com/tvsmotor/notification/config/SalesforceBlobConfig.java:10`, `notification-service/src/main/java/com/tvsmotor/notification/cronjobs/SalesforceBlobStatusJob.java:17`, `notification-service/src/main/java/com/tvsmotor/notification/model/dto/salesforce/SalesforceData.java:8`

## Flow: catalog-scheduler--external-salesforce-fdb9af
Summary: Starting at `catalog-scheduler` (scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller)), the flow passes through `price-engine-micro-service-backend`, `master-data-platform`, `lms-process`, `lms-crm` and ends at `external:salesforce`, using 3 sync HTTP hop(s) and 2 async event hop(s); price-engine-micro-service-backend role: participant; confidence medium.

```mermaid
sequenceDiagram
  participant catalog_scheduler as catalog-scheduler
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  participant master_data_platform as master-data-platform
  participant lms_process as lms-process
  participant lms_crm as lms-crm
  participant external_salesforce as external:salesforce
  catalog_scheduler->>price_engine_micro_service_backend: GET /on-road-prices/vehicles/engineType/{engineType}
  price_engine_micro_service_backend->>master_data_platform: POST /mdp/v1/price/test/service-bus/push-price-data (+1 more)
  master_data_platform--)lms_process: topic:mdp.dealer_data
  lms_process--)lms_crm: topic:lead
  lms_crm->>external_salesforce: host:tvsm-c360a--dev.sandbox.my.salesforce.com
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | catalog-scheduler | price-engine-micro-service-backend | GET /on-road-prices/vehicles/engineType/{engineType} | Unknown | sync | medium |
| 2 | price-engine-micro-service-backend | master-data-platform | POST /mdp/v1/price/test/service-bus/push-price-data, POST /mdp/v1/product/test/service-bus/push-product-data | GeneralResponse | sync | high |
| 3 | master-data-platform | lms-process | topic:mdp.dealer_data | DealerData | async | medium |
| 4 | lms-process | lms-crm | topic:lead | Unknown | async | medium |
| 5 | lms-crm | external:salesforce | host:tvsm-c360a--dev.sandbox.my.salesforce.com | Unknown | sync | high |

Data touched: catalog-scheduler: mongo; price-engine-micro-service-backend: mongo, redis; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; lms-process: mssql; lms-crm: mssql

Failure points: hop 1 catalog-scheduler → price-engine-micro-service-backend: criticality hard; hop 2 price-engine-micro-service-backend → master-data-platform: criticality hard; hop 3 master-data-platform → lms-process: criticality async; hop 4 lms-process → lms-crm: criticality async; hop 5 lms-crm → external:salesforce: criticality hard

Evidence:
- hop 1 (catalog-scheduler → price-engine-micro-service-backend): `Catalog-Scheduler/src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js:21`, `Price-Engine-MicroService-Backend/src/routes/api/on-road-price-routes.ts:31`
- hop 2 (price-engine-micro-service-backend → master-data-platform): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:23`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/controller/TestPriceServiceBusController.java:18`, `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:9` (+1 more)
- hop 3 (master-data-platform → lms-process): `lms_process/processLeadService/Const/Constants.cs:7`, `lms_process/processLeadService/ListenerService/MdpConsumer.cs:42`, `master-data-platform/src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:26` (+1 more)
- hop 4 (lms-process → lms-crm): `lms_crm/ListenerService/CrmListenerService.cs:44`, `lms_crm/Utils/Constants.cs:16`, `lms_process/processLeadService/Const/Constants.cs:6` (+1 more)
- hop 5 (lms-crm → external:salesforce): `lms_crm/appsettings.Development.json:16`, `lms_crm/appsettings.Production.json:17`, `lms_crm/appsettings.Uat.json:17`

## Flow: catalog-scheduler--lms-crm
Summary: Starting at `catalog-scheduler` (scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller)), the flow passes through `price-engine-micro-service-backend`, `master-data-platform`, `lms-process`, `lms-ems` and ends at `lms-crm`, using 2 sync HTTP hop(s) and 3 async event hop(s); price-engine-micro-service-backend role: participant; confidence medium; truncated at the depth cap.

```mermaid
sequenceDiagram
  participant catalog_scheduler as catalog-scheduler
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  participant master_data_platform as master-data-platform
  participant lms_process as lms-process
  participant lms_ems as lms-ems
  participant lms_crm as lms-crm
  catalog_scheduler->>price_engine_micro_service_backend: GET /on-road-prices/vehicles/engineType/{engineType}
  price_engine_micro_service_backend->>master_data_platform: POST /mdp/v1/price/test/service-bus/push-price-data (+1 more)
  master_data_platform--)lms_process: topic:mdp.dealer_data
  lms_process--)lms_ems: topic:lead
  lms_ems--)lms_crm: topic:lead
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | catalog-scheduler | price-engine-micro-service-backend | GET /on-road-prices/vehicles/engineType/{engineType} | Unknown | sync | medium |
| 2 | price-engine-micro-service-backend | master-data-platform | POST /mdp/v1/price/test/service-bus/push-price-data, POST /mdp/v1/product/test/service-bus/push-product-data | GeneralResponse | sync | high |
| 3 | master-data-platform | lms-process | topic:mdp.dealer_data | DealerData | async | medium |
| 4 | lms-process | lms-ems | topic:lead | Unknown | async | medium |
| 5 | lms-ems | lms-crm | topic:lead | Unknown | async | medium |

Data touched: catalog-scheduler: mongo; price-engine-micro-service-backend: mongo, redis; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; lms-process: mssql; lms-ems: mssql; lms-crm: mssql

Failure points: hop 1 catalog-scheduler → price-engine-micro-service-backend: criticality hard; hop 2 price-engine-micro-service-backend → master-data-platform: criticality hard; hop 3 master-data-platform → lms-process: criticality async; hop 4 lms-process → lms-ems: criticality async; hop 5 lms-ems → lms-crm: criticality async

Evidence:
- hop 1 (catalog-scheduler → price-engine-micro-service-backend): `Catalog-Scheduler/src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js:21`, `Price-Engine-MicroService-Backend/src/routes/api/on-road-price-routes.ts:31`
- hop 2 (price-engine-micro-service-backend → master-data-platform): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:23`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/controller/TestPriceServiceBusController.java:18`, `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:9` (+1 more)
- hop 3 (master-data-platform → lms-process): `lms_process/processLeadService/Const/Constants.cs:7`, `lms_process/processLeadService/ListenerService/MdpConsumer.cs:42`, `master-data-platform/src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:26` (+1 more)
- hop 4 (lms-process → lms-ems): `lms_ems/emsService/Const/Constants.cs:14`, `lms_ems/emsService/ListenerService/EmsListenerService.cs:43`, `lms_process/processLeadService/Const/Constants.cs:6` (+1 more)
- hop 5 (lms-ems → lms-crm): `lms_crm/ListenerService/CrmListenerService.cs:44`, `lms_crm/Utils/Constants.cs:16`, `lms_ems/emsService/Const/Constants.cs:13` (+1 more)

## Flow: catalog-scheduler--lms-tvs-credit-bd6cbe
Summary: Starting at `catalog-scheduler` (scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller)), the flow passes through `price-engine-micro-service-backend`, `master-data-platform`, `lms-process`, `lms-ems` and ends at `lms-tvs-credit`, using 2 sync HTTP hop(s) and 3 async event hop(s); price-engine-micro-service-backend role: participant; confidence medium.

```mermaid
sequenceDiagram
  participant catalog_scheduler as catalog-scheduler
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  participant master_data_platform as master-data-platform
  participant lms_process as lms-process
  participant lms_ems as lms-ems
  participant lms_tvs_credit as lms-tvs-credit
  catalog_scheduler->>price_engine_micro_service_backend: GET /on-road-prices/vehicles/engineType/{engineType}
  price_engine_micro_service_backend->>master_data_platform: POST /mdp/v1/price/test/service-bus/push-price-data (+1 more)
  master_data_platform--)lms_process: topic:mdp.dealer_data
  lms_process--)lms_ems: topic:lead
  lms_ems--)lms_tvs_credit: topic:lead
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | catalog-scheduler | price-engine-micro-service-backend | GET /on-road-prices/vehicles/engineType/{engineType} | Unknown | sync | medium |
| 2 | price-engine-micro-service-backend | master-data-platform | POST /mdp/v1/price/test/service-bus/push-price-data, POST /mdp/v1/product/test/service-bus/push-product-data | GeneralResponse | sync | high |
| 3 | master-data-platform | lms-process | topic:mdp.dealer_data | DealerData | async | medium |
| 4 | lms-process | lms-ems | topic:lead | Unknown | async | medium |
| 5 | lms-ems | lms-tvs-credit | topic:lead | Unknown | async | medium |

Data touched: catalog-scheduler: mongo; price-engine-micro-service-backend: mongo, redis; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; lms-process: mssql; lms-ems: mssql; lms-tvs-credit: mssql

Failure points: hop 1 catalog-scheduler → price-engine-micro-service-backend: criticality hard; hop 2 price-engine-micro-service-backend → master-data-platform: criticality hard; hop 3 master-data-platform → lms-process: criticality async; hop 4 lms-process → lms-ems: criticality async; hop 5 lms-ems → lms-tvs-credit: criticality async

Evidence:
- hop 1 (catalog-scheduler → price-engine-micro-service-backend): `Catalog-Scheduler/src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js:21`, `Price-Engine-MicroService-Backend/src/routes/api/on-road-price-routes.ts:31`
- hop 2 (price-engine-micro-service-backend → master-data-platform): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:23`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/controller/TestPriceServiceBusController.java:18`, `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:9` (+1 more)
- hop 3 (master-data-platform → lms-process): `lms_process/processLeadService/Const/Constants.cs:7`, `lms_process/processLeadService/ListenerService/MdpConsumer.cs:42`, `master-data-platform/src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:26` (+1 more)
- hop 4 (lms-process → lms-ems): `lms_ems/emsService/Const/Constants.cs:14`, `lms_ems/emsService/ListenerService/EmsListenerService.cs:43`, `lms_process/processLeadService/Const/Constants.cs:6` (+1 more)
- hop 5 (lms-ems → lms-tvs-credit): `lms_ems/emsService/Const/Constants.cs:13`, `lms_ems/emsService/Services/EmsService.cs:191`, `lms_tvs_credit/lms_tvs_credit/ListenerService/TvscreditListenerService.cs:46` (+1 more)

## Flow: catalog-scheduler--lms-tvs-credit-db10c6
Summary: Starting at `catalog-scheduler` (scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller)), the flow passes through `price-engine-micro-service-backend`, `master-data-platform`, `lms-process` and ends at `lms-tvs-credit`, using 2 sync HTTP hop(s) and 2 async event hop(s); price-engine-micro-service-backend role: participant; confidence medium.

```mermaid
sequenceDiagram
  participant catalog_scheduler as catalog-scheduler
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  participant master_data_platform as master-data-platform
  participant lms_process as lms-process
  participant lms_tvs_credit as lms-tvs-credit
  catalog_scheduler->>price_engine_micro_service_backend: GET /on-road-prices/vehicles/engineType/{engineType}
  price_engine_micro_service_backend->>master_data_platform: POST /mdp/v1/price/test/service-bus/push-price-data (+1 more)
  master_data_platform--)lms_process: topic:mdp.dealer_data
  lms_process--)lms_tvs_credit: topic:lead
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | catalog-scheduler | price-engine-micro-service-backend | GET /on-road-prices/vehicles/engineType/{engineType} | Unknown | sync | medium |
| 2 | price-engine-micro-service-backend | master-data-platform | POST /mdp/v1/price/test/service-bus/push-price-data, POST /mdp/v1/product/test/service-bus/push-product-data | GeneralResponse | sync | high |
| 3 | master-data-platform | lms-process | topic:mdp.dealer_data | DealerData | async | medium |
| 4 | lms-process | lms-tvs-credit | topic:lead | Unknown | async | medium |

Data touched: catalog-scheduler: mongo; price-engine-micro-service-backend: mongo, redis; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; lms-process: mssql; lms-tvs-credit: mssql

Failure points: hop 1 catalog-scheduler → price-engine-micro-service-backend: criticality hard; hop 2 price-engine-micro-service-backend → master-data-platform: criticality hard; hop 3 master-data-platform → lms-process: criticality async; hop 4 lms-process → lms-tvs-credit: criticality async

Evidence:
- hop 1 (catalog-scheduler → price-engine-micro-service-backend): `Catalog-Scheduler/src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js:21`, `Price-Engine-MicroService-Backend/src/routes/api/on-road-price-routes.ts:31`
- hop 2 (price-engine-micro-service-backend → master-data-platform): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:23`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/controller/TestPriceServiceBusController.java:18`, `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:9` (+1 more)
- hop 3 (master-data-platform → lms-process): `lms_process/processLeadService/Const/Constants.cs:7`, `lms_process/processLeadService/ListenerService/MdpConsumer.cs:42`, `master-data-platform/src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:26` (+1 more)
- hop 4 (lms-process → lms-tvs-credit): `lms_process/processLeadService/Const/Constants.cs:6`, `lms_process/processLeadService/Services/TwoWheelerService.cs:97`, `lms_tvs_credit/lms_tvs_credit/ListenerService/TvscreditListenerService.cs:46` (+1 more)

## Flow: catalog-scheduler--notification-dispatcher-service
Summary: Starting at `catalog-scheduler` (scheduled job(s) in catalog-scheduler (job-to-call link not resolved): merchandise-accessories-ingestion-job, product-price-ingestion-job; request to catalog-scheduler from outside the registry (no internal caller)), the flow passes through `price-engine-micro-service-backend`, `master-data-platform`, `tvsmbe-mdp-bff`, `notification-service` and ends at `notification-dispatcher-service`, using 3 sync HTTP hop(s) and 2 async event hop(s); price-engine-micro-service-backend role: participant; confidence medium; truncated at the depth cap.

```mermaid
sequenceDiagram
  participant catalog_scheduler as catalog-scheduler
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  participant master_data_platform as master-data-platform
  participant tvsmbe_mdp_bff as tvsmbe-mdp-bff
  participant notification_service as notification-service
  participant notification_dispatcher_service as notification-dispatcher-service
  catalog_scheduler->>price_engine_micro_service_backend: GET /on-road-prices/vehicles/engineType/{engineType}
  price_engine_micro_service_backend->>master_data_platform: POST /mdp/v1/price/test/service-bus/push-price-data (+1 more)
  master_data_platform--)tvsmbe_mdp_bff: topic:mdp.dealer_data
  tvsmbe_mdp_bff->>notification_service: POST /api/v1/notification/email
  notification_service--)notification_dispatcher_service: topic:notifications
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | catalog-scheduler | price-engine-micro-service-backend | GET /on-road-prices/vehicles/engineType/{engineType} | Unknown | sync | medium |
| 2 | price-engine-micro-service-backend | master-data-platform | POST /mdp/v1/price/test/service-bus/push-price-data, POST /mdp/v1/product/test/service-bus/push-product-data | GeneralResponse | sync | high |
| 3 | master-data-platform | tvsmbe-mdp-bff | topic:mdp.dealer_data | DealerData | async | medium |
| 4 | tvsmbe-mdp-bff | notification-service | POST /api/v1/notification/email | EmailNotification, NotificationResponse | sync | high |
| 5 | notification-service | notification-dispatcher-service | topic:notifications | Unknown | async | medium |

Data touched: catalog-scheduler: mongo; price-engine-micro-service-backend: mongo, redis; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; tvsmbe-mdp-bff: mysql, mysql:tvsmazcmndbsdev01-ci.mysql.database.azure.com:tvsmazebffsdbdev01; notification-service: mongo; notification-dispatcher-service: mongo

Failure points: hop 1 catalog-scheduler → price-engine-micro-service-backend: criticality hard; hop 2 price-engine-micro-service-backend → master-data-platform: criticality hard; hop 3 master-data-platform → tvsmbe-mdp-bff: criticality async; hop 4 tvsmbe-mdp-bff → notification-service: criticality hard; hop 5 notification-service → notification-dispatcher-service: criticality async

Evidence:
- hop 1 (catalog-scheduler → price-engine-micro-service-backend): `Catalog-Scheduler/src/product-price-ingestion-job/data-sources/price-engine-data-source/price-engine-data-source.js:21`, `Price-Engine-MicroService-Backend/src/routes/api/on-road-price-routes.ts:31`
- hop 2 (price-engine-micro-service-backend → master-data-platform): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:23`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/controller/TestPriceServiceBusController.java:18`, `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/service-bus.ts:9` (+1 more)
- hop 3 (master-data-platform → tvsmbe-mdp-bff): `master-data-platform/src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:26`, `master-data-platform/src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:27`, `tvsmbe-mdp-bff/outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/config/BffServiceBusConfig.java:24` (+1 more)
- hop 4 (tvsmbe-mdp-bff → notification-service): `notification-service/src/main/java/com/tvsmotor/notification/controller/NotificationController.java:23`, `tvsmbe-mdp-bff/outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/NotificationSenderService.java:46`, `tvsmbe-mdp-bff/outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/OkHttpService.java:88`
- hop 5 (notification-service → notification-dispatcher-service): `notification-dispatcher-service/src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:33`, `notification-dispatcher-service/src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:34`, `notification-service/src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java:37` (+1 more)

## Flow: cbs-admin-portal--price-engine-micro-service-backend
Summary: Starting at `cbs-admin-portal` (user action in cbs-admin-portal (frontend)), the flow passes through `tvsmbe-mdp-bff`, `master-data-platform` and ends at `price-engine-micro-service-backend`, using 2 sync HTTP hop(s) and 1 async event hop(s); price-engine-micro-service-backend role: terminal; confidence medium.

```mermaid
sequenceDiagram
  participant cbs_admin_portal as cbs-admin-portal
  participant tvsmbe_mdp_bff as tvsmbe-mdp-bff
  participant master_data_platform as master-data-platform
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  cbs_admin_portal->>tvsmbe_mdp_bff: GET /mdp-bff/v1/mdp/dealer/{sapDealerCode}
  tvsmbe_mdp_bff->>master_data_platform: POST /mdp/v1/dealer/mapDealerWithKNumber (+1 more)
  master_data_platform--)price_engine_micro_service_backend: topic:mdp.price.vehicle (+1 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | cbs-admin-portal | tvsmbe-mdp-bff | GET /mdp-bff/v1/mdp/dealer/{sapDealerCode} | GeneralResponse | sync | medium |
| 2 | tvsmbe-mdp-bff | master-data-platform | POST /mdp/v1/dealer/mapDealerWithKNumber, POST /mdp/v1/dealers/basedOnFilters | DealerTypeStatusFlagsFilterRequest, GeneralResponse, MapDealerWithKNumberRequest | sync | high |
| 3 | master-data-platform | price-engine-micro-service-backend | topic:mdp.price.vehicle, topic:mdp.product.vehicle | PriceVehicleData, ServiceBusOutgoingMessagePayloadBody | async | medium |

Data touched: tvsmbe-mdp-bff: mysql, mysql:tvsmazcmndbsdev01-ci.mysql.database.azure.com:tvsmazebffsdbdev01; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; price-engine-micro-service-backend: mongo, redis

Failure points: hop 1 cbs-admin-portal → tvsmbe-mdp-bff: criticality hard; hop 2 tvsmbe-mdp-bff → master-data-platform: criticality hard; hop 3 master-data-platform → price-engine-micro-service-backend: criticality async

Evidence:
- hop 1 (cbs-admin-portal → tvsmbe-mdp-bff): `cbs-admin-portal/src/services/dataService.js:225`, `tvsmbe-mdp-bff/inbound/src/main/java/com/tvsmotor/bff/controller/MdpController.java:14`
- hop 2 (tvsmbe-mdp-bff → master-data-platform): `master-data-platform/src/main/java/com/tvsmotor/mdp/controller/DealerKnowlarityDataController.java:16`, `tvsmbe-mdp-bff/outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/MdpDealerOperationsService.java:54`, `tvsmbe-mdp-bff/outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/OkHttpService.java:88` (+3 more)
- hop 3 (master-data-platform → price-engine-micro-service-backend): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:19`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:20` (+3 more)

## Flow: location-frontend--price-engine-micro-service-backend-17193f
Summary: Starting at `location-frontend` (user action in location-frontend (frontend)), the flow passes through `tvsmbe-location`, `tvsm-auth`, `master-data-platform` and ends at `price-engine-micro-service-backend`, using 3 sync HTTP hop(s) and 1 async event hop(s); price-engine-micro-service-backend role: terminal; confidence medium.

```mermaid
sequenceDiagram
  participant location_frontend as location-frontend
  participant tvsmbe_location as tvsmbe-location
  participant tvsm_auth as tvsm-auth
  participant master_data_platform as master-data-platform
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  location_frontend->>tvsmbe_location: GET /location-master/api/v1/admin-flow/dealer/{sapDealerCode}/location-type/{dealerLocationType} (+28 more)
  tvsmbe_location->>tvsm_auth: GET /api/v1/dealer/get-contacts (+1 more)
  tvsm_auth->>master_data_platform: GET /mdp/v1/dealer/{sapDealerCode} (+1 more)
  master_data_platform--)price_engine_micro_service_backend: topic:mdp.price.vehicle (+1 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | location-frontend | tvsmbe-location | GET /location-master/api/v1/admin-flow/dealer/{sapDealerCode}/location-type/{dealerLocationType}, GET /location-master/api/v1/admin-flow/rejection-comments, GET /location-master/api/v1/admin-flow/summary (+26 more) | CreateDealerRequest, DealerListRequest, DealerResponse, DealerSearchFilterRequest, DealerSearchRequest (+8 more) | sync | high |
| 2 | tvsmbe-location | tvsm-auth | GET /api/v1/dealer/get-contacts, POST /auth/v1/app/token/validate | DealerContacts, TokenVerificationRequest, TokenVerificationResponse | sync | high |
| 3 | tvsm-auth | master-data-platform | GET /mdp/v1/dealer/{sapDealerCode}, GET /mdp/v1/dealer/{sapDealerCode}/branches | GeneralResponse | sync | medium |
| 4 | master-data-platform | price-engine-micro-service-backend | topic:mdp.price.vehicle, topic:mdp.product.vehicle | PriceVehicleData, ServiceBusOutgoingMessagePayloadBody | async | medium |

Data touched: tvsmbe-location: mongo, mysql; tvsm-auth: mysql; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; price-engine-micro-service-backend: mongo, redis

Failure points: hop 1 location-frontend → tvsmbe-location: criticality hard; hop 2 tvsmbe-location → tvsm-auth: criticality hard; hop 3 tvsm-auth → master-data-platform: criticality hard; hop 4 master-data-platform → price-engine-micro-service-backend: criticality async

Evidence:
- hop 1 (location-frontend → tvsmbe-location): `location-frontend/src/services/DealerDetailsService.ts:38`, `tvsmbe-location/src/main/java/com/tvsmotor/location_master/controller/AdminFlowController.java:28`, `location-frontend/src/services/DealerDetailsService.ts:69` (+42 more)
- hop 2 (tvsmbe-location → tvsm-auth): `tvsm-auth/src/main/java/com/tvsmotor/tvsmauth/user/profile/api/DealerController.java:42`, `tvsmbe-location/src/main/java/com/tvsmotor/location_master/service/UMSService.java:49`, `tvsmbe-location/src/main/java/com/tvsmotor/location_master/utils/OkHttpUtil.java:35` (+3 more)
- hop 3 (tvsm-auth → master-data-platform): `master-data-platform/src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20`, `tvsm-auth/src/main/java/com/tvsmotor/tvsmauth/user/gateway/MDPServiceClient.java:86`, `tvsm-auth/src/main/java/com/tvsmotor/tvsmauth/user/gateway/MDPServiceClient.java:110` (+2 more)
- hop 4 (master-data-platform → price-engine-micro-service-backend): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:19`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:20` (+3 more)

## Flow: location-frontend--price-engine-micro-service-backend-51d763
Summary: Starting at `location-frontend` (user action in location-frontend (frontend)), the flow passes through `tvsmbe-location`, `master-data-platform` and ends at `price-engine-micro-service-backend`, using 2 sync HTTP hop(s) and 1 async event hop(s); price-engine-micro-service-backend role: terminal; confidence medium.

```mermaid
sequenceDiagram
  participant location_frontend as location-frontend
  participant tvsmbe_location as tvsmbe-location
  participant master_data_platform as master-data-platform
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  location_frontend->>tvsmbe_location: GET /location-master/api/v1/admin-flow/dealer/{sapDealerCode}/location-type/{dealerLocationType} (+28 more)
  tvsmbe_location->>master_data_platform: GET /mdp/v1/dealer/{sapDealerCode} (+5 more)
  master_data_platform--)price_engine_micro_service_backend: topic:mdp.price.vehicle (+1 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | location-frontend | tvsmbe-location | GET /location-master/api/v1/admin-flow/dealer/{sapDealerCode}/location-type/{dealerLocationType}, GET /location-master/api/v1/admin-flow/rejection-comments, GET /location-master/api/v1/admin-flow/summary (+26 more) | CreateDealerRequest, DealerListRequest, DealerResponse, DealerSearchFilterRequest, DealerSearchRequest (+8 more) | sync | high |
| 2 | tvsmbe-location | master-data-platform | GET /mdp/v1/dealer/{sapDealerCode}, GET /mdp/v1/dealer/{sapDealerCode}/branches, POST /mdp/v1/dealers/data (+3 more) | DealerStateWiseCountFilterRequest, DealerTypeStatusFlagsFilterRequest, GeneralResponse, ProximityRequest | sync | high |
| 3 | master-data-platform | price-engine-micro-service-backend | topic:mdp.price.vehicle, topic:mdp.product.vehicle | PriceVehicleData, ServiceBusOutgoingMessagePayloadBody | async | medium |

Data touched: tvsmbe-location: mongo, mysql; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; price-engine-micro-service-backend: mongo, redis

Failure points: hop 1 location-frontend → tvsmbe-location: criticality hard; hop 2 tvsmbe-location → master-data-platform: criticality hard; hop 3 master-data-platform → price-engine-micro-service-backend: criticality async

Evidence:
- hop 1 (location-frontend → tvsmbe-location): `location-frontend/src/services/DealerDetailsService.ts:38`, `tvsmbe-location/src/main/java/com/tvsmotor/location_master/controller/AdminFlowController.java:28`, `location-frontend/src/services/DealerDetailsService.ts:69` (+42 more)
- hop 2 (tvsmbe-location → master-data-platform): `master-data-platform/src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20`, `tvsmbe-location/src/main/java/com/tvsmotor/location_master/service/MDPDealerService.java:68`, `tvsmbe-location/src/main/java/com/tvsmotor/location_master/utils/OkHttpUtil.java:35` (+7 more)
- hop 3 (master-data-platform → price-engine-micro-service-backend): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:19`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:20` (+3 more)

## Flow: master-data-platform--price-engine-micro-service-backend
Summary: Starting at `master-data-platform` (scheduled job(s) in master-data-platform (job-to-call link not resolved): CronService.logMetricsPeriodically; master-data-platform publishes mdp.price.vehicle, mdp.product.vehicle), the flow ends at `price-engine-micro-service-backend`, using 0 sync HTTP hop(s) and 1 async event hop(s); price-engine-micro-service-backend role: terminal; confidence medium.

```mermaid
sequenceDiagram
  participant master_data_platform as master-data-platform
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  master_data_platform--)price_engine_micro_service_backend: topic:mdp.price.vehicle (+1 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | master-data-platform | price-engine-micro-service-backend | topic:mdp.price.vehicle, topic:mdp.product.vehicle | PriceVehicleData, ServiceBusOutgoingMessagePayloadBody | async | medium |

Data touched: master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; price-engine-micro-service-backend: mongo, redis

Failure points: hop 1 master-data-platform → price-engine-micro-service-backend: criticality async

Evidence:
- hop 1 (master-data-platform → price-engine-micro-service-backend): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:19`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:20` (+3 more)

## Flow: tvsm-auth--price-engine-micro-service-backend
Summary: Starting at `tvsm-auth` (scheduled job(s) in tvsm-auth (job-to-call link not resolved): CacheClearScheduler.evictAllCachesAtIntervals, NotificationReminder.sendSMSForFaceLogin), the flow passes through `master-data-platform` and ends at `price-engine-micro-service-backend`, using 1 sync HTTP hop(s) and 1 async event hop(s); price-engine-micro-service-backend role: terminal; confidence medium.

```mermaid
sequenceDiagram
  participant tvsm_auth as tvsm-auth
  participant master_data_platform as master-data-platform
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  tvsm_auth->>master_data_platform: GET /mdp/v1/dealer/{sapDealerCode} (+1 more)
  master_data_platform--)price_engine_micro_service_backend: topic:mdp.price.vehicle (+1 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | tvsm-auth | master-data-platform | GET /mdp/v1/dealer/{sapDealerCode}, GET /mdp/v1/dealer/{sapDealerCode}/branches | GeneralResponse | sync | medium |
| 2 | master-data-platform | price-engine-micro-service-backend | topic:mdp.price.vehicle, topic:mdp.product.vehicle | PriceVehicleData, ServiceBusOutgoingMessagePayloadBody | async | medium |

Data touched: tvsm-auth: mysql; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; price-engine-micro-service-backend: mongo, redis

Failure points: hop 1 tvsm-auth → master-data-platform: criticality hard; hop 2 master-data-platform → price-engine-micro-service-backend: criticality async

Evidence:
- hop 1 (tvsm-auth → master-data-platform): `master-data-platform/src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20`, `tvsm-auth/src/main/java/com/tvsmotor/tvsmauth/user/gateway/MDPServiceClient.java:86`, `tvsm-auth/src/main/java/com/tvsmotor/tvsmauth/user/gateway/MDPServiceClient.java:110` (+2 more)
- hop 2 (master-data-platform → price-engine-micro-service-backend): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:19`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:20` (+3 more)

## Flow: tvsm-marketplace-service--price-engine-micro-service-backend
Summary: Starting at `tvsm-marketplace-service` (scheduled job(s) in tvsm-marketplace-service (job-to-call link not resolved): AmazonPriceUpdateExecutorService.scheduledDrain, FlipkartPriceUpdateExecutorService.scheduledDrain, MarketplacePriceUpdateTaskService.cleanupDoneTasks (+2 more); request to tvsm-marketplace-service from outside the registry (no internal caller)), the flow passes through `master-data-platform` and ends at `price-engine-micro-service-backend`, using 1 sync HTTP hop(s) and 1 async event hop(s); price-engine-micro-service-backend role: terminal; confidence medium.

```mermaid
sequenceDiagram
  participant tvsm_marketplace_service as tvsm-marketplace-service
  participant master_data_platform as master-data-platform
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  tvsm_marketplace_service->>master_data_platform: GET /mdp/v1/dealer/{sapDealerCode} (+2 more)
  master_data_platform--)price_engine_micro_service_backend: topic:mdp.price.vehicle (+1 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | tvsm-marketplace-service | master-data-platform | GET /mdp/v1/dealer/{sapDealerCode}, GET /mdp/v1/product/vehicle/part/{sapPartId}, POST /mdp/v1/dealers/listOfDealerDetails/basedOnProximity | GeneralResponse, ProximityRequest | sync | high |
| 2 | master-data-platform | price-engine-micro-service-backend | topic:mdp.price.vehicle, topic:mdp.product.vehicle | PriceVehicleData, ServiceBusOutgoingMessagePayloadBody | async | medium |

Data touched: tvsm-marketplace-service: mysql, mysql:localhost:marketplace; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; price-engine-micro-service-backend: mongo, redis

Failure points: hop 1 tvsm-marketplace-service → master-data-platform: criticality hard; hop 2 master-data-platform → price-engine-micro-service-backend: criticality async

Evidence:
- hop 1 (tvsm-marketplace-service → master-data-platform): `master-data-platform/src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20`, `tvsm-marketplace-service/src/main/java/com/tvsmotor/marketplace/service/OkHttpService.java:39`, `tvsm-marketplace-service/src/main/java/com/tvsmotor/marketplace/service/mdp/MdpApiCallerService.java:72` (+4 more)
- hop 2 (master-data-platform → price-engine-micro-service-backend): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:19`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:20` (+3 more)

## Flow: tvsmbe-location--price-engine-micro-service-backend-45a56f
Summary: Starting at `tvsmbe-location` (scheduled job(s) in tvsmbe-location (job-to-call link not resolved): CronService.logMetricsPeriodically), the flow passes through `tvsm-auth`, `master-data-platform` and ends at `price-engine-micro-service-backend`, using 2 sync HTTP hop(s) and 1 async event hop(s); price-engine-micro-service-backend role: terminal; confidence medium.

```mermaid
sequenceDiagram
  participant tvsmbe_location as tvsmbe-location
  participant tvsm_auth as tvsm-auth
  participant master_data_platform as master-data-platform
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  tvsmbe_location->>tvsm_auth: GET /api/v1/dealer/get-contacts (+1 more)
  tvsm_auth->>master_data_platform: GET /mdp/v1/dealer/{sapDealerCode} (+1 more)
  master_data_platform--)price_engine_micro_service_backend: topic:mdp.price.vehicle (+1 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | tvsmbe-location | tvsm-auth | GET /api/v1/dealer/get-contacts, POST /auth/v1/app/token/validate | DealerContacts, TokenVerificationRequest, TokenVerificationResponse | sync | high |
| 2 | tvsm-auth | master-data-platform | GET /mdp/v1/dealer/{sapDealerCode}, GET /mdp/v1/dealer/{sapDealerCode}/branches | GeneralResponse | sync | medium |
| 3 | master-data-platform | price-engine-micro-service-backend | topic:mdp.price.vehicle, topic:mdp.product.vehicle | PriceVehicleData, ServiceBusOutgoingMessagePayloadBody | async | medium |

Data touched: tvsmbe-location: mongo, mysql; tvsm-auth: mysql; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; price-engine-micro-service-backend: mongo, redis

Failure points: hop 1 tvsmbe-location → tvsm-auth: criticality hard; hop 2 tvsm-auth → master-data-platform: criticality hard; hop 3 master-data-platform → price-engine-micro-service-backend: criticality async

Evidence:
- hop 1 (tvsmbe-location → tvsm-auth): `tvsm-auth/src/main/java/com/tvsmotor/tvsmauth/user/profile/api/DealerController.java:42`, `tvsmbe-location/src/main/java/com/tvsmotor/location_master/service/UMSService.java:49`, `tvsmbe-location/src/main/java/com/tvsmotor/location_master/utils/OkHttpUtil.java:35` (+3 more)
- hop 2 (tvsm-auth → master-data-platform): `master-data-platform/src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20`, `tvsm-auth/src/main/java/com/tvsmotor/tvsmauth/user/gateway/MDPServiceClient.java:86`, `tvsm-auth/src/main/java/com/tvsmotor/tvsmauth/user/gateway/MDPServiceClient.java:110` (+2 more)
- hop 3 (master-data-platform → price-engine-micro-service-backend): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:19`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:20` (+3 more)

## Flow: tvsmbe-location--price-engine-micro-service-backend-834d3e
Summary: Starting at `tvsmbe-location` (scheduled job(s) in tvsmbe-location (job-to-call link not resolved): CronService.logMetricsPeriodically), the flow passes through `master-data-platform` and ends at `price-engine-micro-service-backend`, using 1 sync HTTP hop(s) and 1 async event hop(s); price-engine-micro-service-backend role: terminal; confidence medium.

```mermaid
sequenceDiagram
  participant tvsmbe_location as tvsmbe-location
  participant master_data_platform as master-data-platform
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  tvsmbe_location->>master_data_platform: GET /mdp/v1/dealer/{sapDealerCode} (+5 more)
  master_data_platform--)price_engine_micro_service_backend: topic:mdp.price.vehicle (+1 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | tvsmbe-location | master-data-platform | GET /mdp/v1/dealer/{sapDealerCode}, GET /mdp/v1/dealer/{sapDealerCode}/branches, POST /mdp/v1/dealers/data (+3 more) | DealerStateWiseCountFilterRequest, DealerTypeStatusFlagsFilterRequest, GeneralResponse, ProximityRequest | sync | high |
| 2 | master-data-platform | price-engine-micro-service-backend | topic:mdp.price.vehicle, topic:mdp.product.vehicle | PriceVehicleData, ServiceBusOutgoingMessagePayloadBody | async | medium |

Data touched: tvsmbe-location: mongo, mysql; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; price-engine-micro-service-backend: mongo, redis

Failure points: hop 1 tvsmbe-location → master-data-platform: criticality hard; hop 2 master-data-platform → price-engine-micro-service-backend: criticality async

Evidence:
- hop 1 (tvsmbe-location → master-data-platform): `master-data-platform/src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20`, `tvsmbe-location/src/main/java/com/tvsmotor/location_master/service/MDPDealerService.java:68`, `tvsmbe-location/src/main/java/com/tvsmotor/location_master/utils/OkHttpUtil.java:35` (+7 more)
- hop 2 (master-data-platform → price-engine-micro-service-backend): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:19`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:20` (+3 more)

## Flow: tvsmbe-mdp-bff--price-engine-micro-service-backend
Summary: Starting at `tvsmbe-mdp-bff` (scheduled job(s) in tvsmbe-mdp-bff (job-to-call link not resolved): CronService.logMetricsPeriodically), the flow passes through `master-data-platform` and ends at `price-engine-micro-service-backend`, using 1 sync HTTP hop(s) and 1 async event hop(s); price-engine-micro-service-backend role: terminal; confidence medium.

```mermaid
sequenceDiagram
  participant tvsmbe_mdp_bff as tvsmbe-mdp-bff
  participant master_data_platform as master-data-platform
  participant price_engine_micro_service_backend as price-engine-micro-service-backend
  tvsmbe_mdp_bff->>master_data_platform: POST /mdp/v1/dealer/mapDealerWithKNumber (+1 more)
  master_data_platform--)price_engine_micro_service_backend: topic:mdp.price.vehicle (+1 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | tvsmbe-mdp-bff | master-data-platform | POST /mdp/v1/dealer/mapDealerWithKNumber, POST /mdp/v1/dealers/basedOnFilters | DealerTypeStatusFlagsFilterRequest, GeneralResponse, MapDealerWithKNumberRequest | sync | high |
| 2 | master-data-platform | price-engine-micro-service-backend | topic:mdp.price.vehicle, topic:mdp.product.vehicle | PriceVehicleData, ServiceBusOutgoingMessagePayloadBody | async | medium |

Data touched: tvsmbe-mdp-bff: mysql, mysql:tvsmazcmndbsdev01-ci.mysql.database.azure.com:tvsmazebffsdbdev01; master-data-platform: mysql:xxxx.mysql.database.azure.com:mdp_20230904, other, redis; price-engine-micro-service-backend: mongo, redis

Failure points: hop 1 tvsmbe-mdp-bff → master-data-platform: criticality hard; hop 2 master-data-platform → price-engine-micro-service-backend: criticality async

Evidence:
- hop 1 (tvsmbe-mdp-bff → master-data-platform): `master-data-platform/src/main/java/com/tvsmotor/mdp/controller/DealerKnowlarityDataController.java:16`, `tvsmbe-mdp-bff/outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/MdpDealerOperationsService.java:54`, `tvsmbe-mdp-bff/outbound/src/main/java/com/tvsmotor/mdp_bff/outbound/service/OkHttpService.java:88` (+3 more)
- hop 2 (master-data-platform → price-engine-micro-service-backend): `Price-Engine-MicroService-Backend/sonar-exclusion-function/service-bus/implemeters/price-service-bus-implementer.ts:18`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:19`, `master-data-platform/src/main/java/com/tvsmotor/mdp/price/config/PriceVehicleServiceBusConfig.java:20` (+3 more)
