---
service_id: master-data-platform
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["mdp", "master data platform", "mdp dealer", "mdp data platform", "mdp dealer operation", "mdp dealer operations"]
---

# master-data-platform — Overview

## Purpose
Summary: Spring Boot master data platform (MDP) holding dealer, product, part and vehicle price data ingested from SAP/SharePoint/DMS, served over HTTP and Service Bus topics.
Also known as: mdp, master data platform, mdp dealer, mdp data platform, mdp dealer operation, mdp dealer operations
master-data-platform (MDP, `README.md`) is a Spring Boot backend API that holds TVS master data — dealers (with branches, contacts, employees, flags, locations), vehicle products/parts, MNA, part prices and vehicle prices — ingested from SAP/SharePoint/DMS batch pipelines and served over HTTP and Azure Service Bus topics (`src/main/java/com/tvsmotor/mdp/controller/DE_PipelineController.java:20`, `src/main/java/com/tvsmotor/mdp/service/service_bus/DealerDataSenderService.java:87`). Business owner Unknown.

## Users and Consumers
master-data-platform inbound callers (registry): `price-engine-micro-service-backend`, `tvsm-auth`, `tvsm-marketplace-service`, `tvsmbe-location`, `tvsmbe-mdp-bff`.
Event consumers of master-data-platform's topics/queues: `price-engine-micro-service-backend`, `tvsmbe-mdp-bff`.

## Key Capabilities
master-data-platform capabilities:
- Dealer lookup by SAP dealer code, branches, pincode, proximity and filters (`controller/DealerController.java:20`)
- Dealer flags / flag types management (`controller/DealerFlagsNewController.java:15`, `controller/DealerFlagsTypeNewController.java:17`)
- Batch ingestion trigger for SAP/SharePoint/product/price/part data (`controller/DE_PipelineController.java:20`, `service/batch_processing/`)
- DMS / LatLong / Knowlarity migration endpoints (`controller/migration/`)
- Publishes master-data change events to Azure Service Bus topics
- Redis caching of dealer/part/price data (`common/cache/CacheService.java:25`)
- 68 HTTP endpoints (see API_SPEC.md)
- Publishes 7 event entities: `local.mdp.dealer_data`, `local.dms.dealer_data`, `local.mdp.part_data`, `local.mdp.part.price`, `local.mdp.price.vehicle`, `local.mdp.product.mna`, `local.mdp.product.vehicle`
- Consumes 6 event entities: `local.mdp.dealer_data`, `local.dms.dealer_data`, `dev.mdp.dealer_data`, `local.mdp.part`, `local.mdp.price.vehicle`, `mdp.product.vehicle`
- Scheduled jobs: `CronService.logMetricsPeriodically`

## Tech Stack
master-data-platform tech stack (service.yaml `tech_stack`, build `java`):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Java 17 (`README.md`, `Dockerfile` corretto 17) |
| Framework | spring-mvc | Spring Boot 3.5.12 (`README.md`) |
| Data | mysql, other, redis | Unknown |
| Messaging | azure-service-bus | Unknown |
| Hosting | Docker (amazoncorretto:17, port 8080, `Dockerfile:27`); Azure Pipelines CI/CD | Unknown |

Key libraries: `com.azure:azure-messaging-servicebus` 7.17.17, `com.fasterxml.jackson.datatype:jackson-datatype-jsr310` 2.21.5, `com.google.guava:guava` 33.4.2-jre, `com.microsoft.sqlserver:mssql-jdbc` 12.10.2.jre11, `com.mysql:mysql-connector-j` 8.4.0, `com.opencsv:opencsv` 5.12.0, `com.squareup.okhttp3:okhttp` 4.12.0, `commons-beanutils:commons-beanutils` 1.11.0, `net.bytebuddy:byte-buddy` 1.18.10, `org.apache.commons:commons-collections4` 4.5.0, `org.hibernate:hibernate-envers` 6.6.13.Final, `org.projectlombok:lombok` 1.18.46, `org.springdoc:springdoc-openapi-starter-webmvc-ui` 2.8.9, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-parent` 3.5.16, `org.springframework.boot:spring-boot-starter-web`, `org.springframework.data:spring-data-redis` 3.5.1, `org.springframework.retry:spring-retry` 2.0.13, `redis.clients:jedis` 5.2.0

## Dependencies at a Glance
Upstream (calls master-data-platform): `price-engine-micro-service-backend`, `tvsm-auth`, `tvsm-marketplace-service`, `tvsmbe-location`, `tvsmbe-mdp-bff`
Downstream (master-data-platform calls): `notification-service` (hard); 3 unresolved outbound calls (see API_SPEC.md)
Brokers: azure-service-bus
Data stores: `mdp_20230904` (mysql, read-write; e.g. `AuditLog`), `_` (other, write; e.g. `audit_log`), `_` (redis, access Unknown)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
master-data-platform environments (service.yaml `deployment.environments`: none recorded).

| Env | URL | Notes |
|---|---|---|
| prod | Unknown | |
| uat | Unknown | |
| dev | Unknown | |

## Environment Variables
master-data-platform configuration keys (142; names only, from service.yaml `config`):

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `ACTIVE_ENVIRONMENT` | Unknown | Unknown | no | env-file |
| `APIM_BASE_URL` | Unknown | Unknown | no | env-file |
| `AZURE_B2C_CLIENT_ID` | Unknown | True | no | env-file |
| `AZURE_B2C_CLIENT_SECRET` | Unknown | True | yes | env-file |
| `AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL` | Unknown | Unknown | yes | env-file |
| `AZURE_B2C_SCOPE` | Unknown | True | no | env-file |
| `AZ_CLIENT_ID` | Unknown | Unknown | no | env-file |
| `AZ_CLIENT_SECRET` | Unknown | Unknown | yes | env-file |
| `AZ_TENANT_ID` | Unknown | Unknown | no | env-file |
| `CLIENT_ID` | Unknown | Unknown | no | env-file |
| `CLIENT_SECRET` | Unknown | Unknown | yes | env-file |
| `DATABASE_HOST_URL` | Unknown | Unknown | no | env-file |
| `DATABASE_NAME` | Unknown | Unknown | no | env-file |
| `DATABASE_PASSWORD` | Unknown | Unknown | yes | env-file |
| `DATABASE_USERNAME` | Unknown | Unknown | no | env-file |
| `DB_HOST` | Unknown | Unknown | no | env-file |
| `DB_NAME` | Unknown | Unknown | no | env-file |
| `DB_PASSWORD` | Unknown | Unknown | yes | env-file |
| `DB_USER` | Unknown | Unknown | no | env-file |
| `DMS_DATABASE_HOST` | Unknown | Unknown | no | env-file |
| `DMS_DATABASE_PASSWORD` | Unknown | True | yes | env-file |
| `DMS_DATABASE_USERNAME` | Unknown | True | no | env-file |
| `EMAIL_NOTIFICATION_PRIORITY` | Unknown | Unknown | no | env-file |
| `EXCLUDED_AMD_SAP_DEALER_CODES` | Unknown | True | no | env-file |
| `LOCAL_AREA_OFFICE_EXCEL_PATH` | Unknown | Unknown | no | env-file |
| `LOCAL_MARKETING_EXCEL_PATH` | Unknown | Unknown | no | env-file |
| `MDP_DEV_AZURE_B2C_CLIENT_ID` | Unknown | Unknown | no | env-file |
| `MDP_DEV_AZURE_B2C_CLIENT_SECRET` | Unknown | Unknown | yes | env-file |
| `MDP_DEV_AZURE_B2C_SCOPE` | Unknown | Unknown | no | env-file |
| `MDP_DEV_BASE_URL` | Unknown | Unknown | no | env-file |
| `MDP_PROD_AZURE_B2C_CLIENT_ID` | Unknown | Unknown | no | env-file |
| `MDP_PROD_AZURE_B2C_CLIENT_SECRET` | Unknown | Unknown | yes | env-file |
| `MDP_PROD_AZURE_B2C_SCOPE` | Unknown | Unknown | no | env-file |
| `MDP_PROD_BASE_URL` | Unknown | Unknown | no | env-file |
| `MDP_PROD_DATABASE_HOST` | Unknown | Unknown | no | env-file |
| `MDP_PROD_DATABASE_PASSWORD` | Unknown | Unknown | yes | env-file |
| `MDP_PROD_DATABASE_USERNAME` | Unknown | Unknown | no | env-file |
| `MDP_UAT_AZURE_B2C_CLIENT_ID` | Unknown | Unknown | no | env-file |
| `MDP_UAT_AZURE_B2C_CLIENT_SECRET` | Unknown | Unknown | yes | env-file |
| `MDP_UAT_AZURE_B2C_SCOPE` | Unknown | Unknown | no | env-file |
| `MDP_UAT_BASE_URL` | Unknown | Unknown | no | env-file |
| `NEW_RELIC_AGENT_ENABLED` | Unknown | Unknown | no | env-file |
| `NOTIFICATION_BASE_URL` | Unknown | Unknown | no | env-file |
| `NOTIFICATION_EMAIL_FAILURE_PRIORITY` | Unknown | True | no | env-file |
| `NOTIFICATION_EMAIL_FAILURE_RECIPIENTS` | Unknown | True | no | env-file |
| `NOTIFICATION_EMAIL_FAILURE_TEMPLATE_ID` | Unknown | Unknown | no | env-file |
| `NOTIFICATION_EMAIL_NEW_DEALER_ACTIVE_DMS_MIGRATION_RECIPIENTS` | Unknown | Unknown | no | env-file |
| `NOTIFICATION_EMAIL_NEW_DEALER_ACTIVE_RECIPIENTS` | Unknown | Unknown | no | env-file |
| `NOTIFICATION_EMAIL_NEW_DEALER_ACTIVE_SHAREPOINT_RECIPIENTS` | Unknown | Unknown | no | env-file |
| `NOTIFICATION_GENERATE_B2C_TOKEN_API_URL` | Unknown | Unknown | yes | env-file |
| `NOTIFICATION_GENERATE_B2C_TOKEN_CLIENT_ID` | Unknown | Unknown | yes | env-file |
| `NOTIFICATION_GENERATE_B2C_TOKEN_CLIENT_SECRET` | Unknown | Unknown | yes | env-file |
| `ONLINE_DMS_PASSWORD` | Unknown | Unknown | yes | env-file |
| `ONLINE_DMS_USER_NAME` | Unknown | Unknown | no | env-file |
| `REDIS_HOST_URL` | Unknown | Unknown | no | env-file |
| `REDIS_PASSWORD` | Unknown | Unknown | yes | env-file |
| `SERVICE_BUS_DEALER_DATA_CONNECTION_STRING` | Unknown | Unknown | yes | env-file |
| `SERVICE_BUS_DEALER_DATA_TOPIC_NAME` | Unknown | Unknown | no | env-file |
| `SERVICE_BUS_DMS_DEALER_DATA_CONNECTION_STRING` | Unknown | Unknown | yes | env-file |
| `SERVICE_BUS_DMS_DEALER_DATA_TOPIC_NAME` | Unknown | Unknown | no | env-file |
| `SERVICE_BUS_PART_DATA_CONNECTION_STRING` | Unknown | Unknown | yes | env-file |
| `SERVICE_BUS_PART_DATA_TOPIC_NAME` | Unknown | Unknown | no | env-file |
| `SERVICE_BUS_PART_PRICE_DATA_CONNECTION_STRING` | Unknown | Unknown | yes | env-file |
| `SERVICE_BUS_PART_PRICE_DATA_TOPIC_NAME` | Unknown | Unknown | no | env-file |
| `SERVICE_BUS_PRICE_DATA_CONNECTION_STRING` | Unknown | Unknown | yes | env-file |
| `SERVICE_BUS_PRICE_DATA_TOPIC_NAME` | Unknown | Unknown | no | env-file |
| `SERVICE_BUS_PRODUCT_MNA_DATA_CONNECTION_STRING` | Unknown | Unknown | yes | env-file |
| `SERVICE_BUS_PRODUCT_MNA_DATA_TOPIC_NAME` | Unknown | Unknown | no | env-file |
| `SERVICE_BUS_VEHICLE_DATA_CONNECTION_STRING` | Unknown | Unknown | yes | env-file |
| `SERVICE_BUS_VEHICLE_DATA_TOPIC_NAME` | Unknown | Unknown | no | env-file |
| `SHAREPOINT_AREA_OFFICE_URL` | Unknown | Unknown | no | env-file |
| `SHAREPOINT_MARKETING_URL` | Unknown | Unknown | no | env-file |
| `SHOW_HTTP_500_DETAILS` | Unknown | Unknown | no | env-file |
| `TENANT_ID` | Unknown | Unknown | no | env-file |
| `TZ` | Unknown | Unknown | no | Unknown |
| `apim.base-url` | Unknown | Unknown | no | app-settings |
| `azure.b2c.token.url` | Unknown | True | yes | app-settings |
| `cache.redis.host` | Unknown | True | no | app-settings |
| `cache.redis.password` | Unknown | True | yes | app-settings |
| `dms.database.url` | Unknown | True | no | app-settings |
| `k8s.pod.name` | Unknown | True | no | app-settings |
| `latlong.brandCreds` | Unknown | True | no | Unknown |
| `latlong.brandCreds[0]` | Unknown | Unknown | no | app-settings |
| `latlong.brandCreds[1]` | Unknown | Unknown | no | app-settings |
| `latlong.brandCreds[2]` | Unknown | Unknown | no | app-settings |
| `latlong.brandCreds[3]` | Unknown | Unknown | yes | app-settings |
| `latlong.brandCreds[4]` | Unknown | Unknown | yes | app-settings |
| `latlong.brandCreds[5]` | Unknown | Unknown | no | app-settings |
| `latlong.brandCreds[6]` | Unknown | Unknown | yes | app-settings |
| `latlong.brandCreds[7]` | Unknown | Unknown | yes | app-settings |
| `local.servicebus.common.connection-string` | Unknown | Unknown | yes | app-settings |
| `logging.level.com.azure.*` | Unknown | Unknown | no | app-settings |
| `logging.level.org.hibernate.SQL` | Unknown | Unknown | no | app-settings |
| `logging.level.org.hibernate.envers` | Unknown | Unknown | no | app-settings |
| `logging.level.root` | Unknown | Unknown | no | app-settings |
| `notification.base-url` | Unknown | True | no | app-settings |
| `notification.email.failure.templateId` | Unknown | True | no | app-settings |
| `notification.email.newDealerActiveDmsMigration.recipients` | Unknown | True | no | app-settings |
| `notification.email.newDealerActiveSharepoint.recipients` | Unknown | True | no | app-settings |
| `server.error.whitelabel.enabled` | Unknown | Unknown | no | app-settings |
| `server.host` | Unknown | Unknown | no | app-settings |
| `server.port` | Unknown | Unknown | no | app-settings |
| `server.servlet.context-path` | Unknown | Unknown | no | app-settings |
| `server.tomcat.accesslog.directory` | Unknown | Unknown | no | app-settings |
| `server.tomcat.accesslog.enabled` | Unknown | Unknown | no | app-settings |
| `show.http_500_error_details` | Unknown | True | no | app-settings |
| `spring.application.name` | Unknown | Unknown | no | app-settings |
| `spring.datasource.driver-class-name` | Unknown | Unknown | no | app-settings |
| `spring.datasource.hikari.maximumPoolSize` | Unknown | Unknown | no | app-settings |
| `spring.datasource.hikari.minimumIdle` | Unknown | Unknown | no | app-settings |
| `spring.datasource.password` | Unknown | Unknown | yes | app-settings |
| `spring.datasource.platform` | Unknown | Unknown | no | app-settings |
| `spring.datasource.url` | Unknown | Unknown | no | app-settings |
| `spring.datasource.username` | Unknown | Unknown | no | app-settings |
| `spring.h2.console.enabled` | Unknown | Unknown | no | app-settings |
| `spring.h2.console.path` | Unknown | Unknown | no | app-settings |
| `spring.jms.servicebus.idle-timeout` | Unknown | Unknown | no | app-settings |
| `spring.jms.servicebus.topic.dealerData.connection-string` | Unknown | True | yes | app-settings |
| `spring.jms.servicebus.topic.dealerData.name` | Unknown | True | no | app-settings |
| `spring.jms.servicebus.topic.dealerData.subscription` | Unknown | True | no | app-settings |
| `spring.jms.servicebus.topic.dmsDealerData.connection-string` | Unknown | True | yes | app-settings |
| `spring.jms.servicebus.topic.dmsDealerData.name` | Unknown | True | no | app-settings |
| `spring.jms.servicebus.topic.partData.connection-string` | Unknown | True | yes | app-settings |
| `spring.jms.servicebus.topic.partData.name` | Unknown | True | no | app-settings |
| `spring.jms.servicebus.topic.partPriceData.connection-string` | Unknown | True | yes | app-settings |
| `spring.jms.servicebus.topic.partPriceData.name` | Unknown | True | no | app-settings |
| `spring.jms.servicebus.topic.priceVehicleData.connection-string` | Unknown | True | yes | app-settings |
| `spring.jms.servicebus.topic.priceVehicleData.name` | Unknown | True | no | app-settings |
| `spring.jms.servicebus.topic.productMnaData.connection-string` | Unknown | True | yes | app-settings |
| `spring.jms.servicebus.topic.productMnaData.name` | Unknown | True | no | app-settings |
| `spring.jms.servicebus.topic.productVehicleData.connection-string` | Unknown | True | yes | app-settings |
| `spring.jms.servicebus.topic.productVehicleData.name` | Unknown | True | no | app-settings |
| `spring.jpa.database` | Unknown | Unknown | no | app-settings |
| `spring.jpa.database-platform` | Unknown | Unknown | no | app-settings |
| `spring.jpa.open-in-view` | Unknown | Unknown | no | app-settings |
| `spring.jpa.properties.hibernate.dialect` | Unknown | Unknown | no | app-settings |
| `spring.jpa.properties.hibernate.jdbc.lob.non_contextual_creation` | Unknown | Unknown | no | app-settings |
| `spring.output.ansi.enabled` | Unknown | Unknown | no | app-settings |
| `spring.profiles.active` | Unknown | True | no | app-settings |
| `springdoc.api-docs.enabled` | Unknown | Unknown | no | app-settings |
| `springdoc.show-actuator` | Unknown | Unknown | no | app-settings |
| `springdoc.swagger-ui.enabled` | Unknown | Unknown | no | app-settings |

## Ownership
master-data-platform ownership is not recorded in code unless shown below.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
master-data-platform (`README.md`): local MySQL 8, JDK, Maven 3; set env `ACTIVE_ENVIRONMENT=local`; run `MdpApplication` (`src/main/java/com/tvsmotor/mdp/MdpApplication.java`). Docker: multi-stage `mvn clean install` then `java -jar /usr/local/lib/mdp.jar` (`Dockerfile:30`).

## Known Limitations
- master-data-platform exposes many `test/*` and `migration/*` endpoints in the main controller set (`controller/TestController.java:32`, `controller/TestServiceBusController.java:22`) — Unknown whether gated in prod.
- README notes only soft deletes are allowed; no DELETE queries (`README.md`).
- Several outbound calls have literal/unresolved base URLs (see API_SPEC Outbound Calls).
