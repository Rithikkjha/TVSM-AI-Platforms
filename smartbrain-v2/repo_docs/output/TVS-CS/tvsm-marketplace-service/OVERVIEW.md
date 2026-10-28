---
service_id: tvsm-marketplace-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["marketplace", "tvsm marketplace service", "marketplace service", "mdp marketplace", "tvsm marketplace"]
---

# tvsm-marketplace-service — Overview

## Purpose
Summary: Spring Boot marketplace integration processing orders and listings with Flipkart and Amazon, calling booking, MDP and notification services; README gives only the title.
Also known as: marketplace, tvsm marketplace service, marketplace service, mdp marketplace, tvsm marketplace
tvsm-marketplace-service is a `backend-api` repository (`tvsm-marketplace-service`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: tvsm-marketplace-service.

## Users and Consumers
tvsm-marketplace-service is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
tvsm-marketplace-service capabilities derived from code:
- `TestController`: 9 HTTP endpoint(s)
- `OrderController`: 7 HTTP endpoint(s)
- `FlipkartHelperController`: 4 HTTP endpoint(s)
- `TestServiceBusController`: 3 HTTP endpoint(s)
- `ProductsController`: 2 HTTP endpoint(s)
- `AmazonListingSyncController`: 2 HTTP endpoint(s)
- `DealerInventoryController`: 1 HTTP endpoint(s)
- `DealerMarketplaceMappingController`: 1 HTTP endpoint(s)
- `DealerRefreshTokenController`: 1 HTTP endpoint(s)
- `PartIdModelIdTransitionController`: 1 HTTP endpoint(s)
- `DealerVehicleMappingController`: 1 HTTP endpoint(s)
- `FlipkartWebhookController`: 1 HTTP endpoint(s)
- `FlipkartSaltKeyMetadataController`: 1 HTTP endpoint(s)
- `DealerController`: 1 HTTP endpoint(s)
- Scheduled job `ServerMetricsService.scheduledLogServerMetrics` (cron `0 * * * * ?`)
- Scheduled job `AmazonPriceUpdateExecutorService.scheduledDrain` (fixed-delay `None`)
- Scheduled job `FlipkartPriceUpdateExecutorService.scheduledDrain` (fixed-delay `None`)
- Scheduled job `MarketplacePriceUpdateTaskService.recoverStaleLocks` (fixed-delay `None`)
- Scheduled job `MarketplacePriceUpdateTaskService.cleanupDoneTasks` (cron `None`)
- Consumes 4 messaging entit(y/ies)

## Tech Stack
tvsm-marketplace-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | mysql | Unknown |
| Messaging | azure-service-bus | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.amazonaws:amazon-sqs-java-messaging-lib`, `com.azure:azure-messaging-servicebus`, `com.fasterxml.jackson.datatype:jackson-datatype-joda`, `com.fasterxml.jackson.datatype:jackson-datatype-jsr310`, `com.google.guava:guava`, `com.mysql:mysql-connector-j`, `com.squareup.okhttp3:okhttp`, `commons-codec:commons-codec`, `org.apache.poi:poi-ooxml`, `org.hibernate.orm:hibernate-envers`, `org.projectlombok:lombok`, `org.springdoc:springdoc-openapi-starter-webmvc-ui`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-parent`, `org.springframework.boot:spring-boot-starter-web`, `org.springframework.retry:spring-retry`, `org.springframework.security:spring-security-crypto`

## Dependencies at a Glance
Upstream (calls tvsm-marketplace-service): Unknown
Downstream (tvsm-marketplace-service calls): `booking-crud-services` (hard), `master-data-platform` (hard), `notification-service` (hard); plus 32 outbound call(s) with unresolved target
Brokers: azure-service-bus. Data stores: `_` (mysql, write), `marketplace` (mysql, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvsm-marketplace-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
tvsm-marketplace-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).
171 keys total; table lists secret/externally-provided/pointer keys (107). Key counts by prefix: `spring` 22, `AMAZON` 16, `amazon` 14, `PRICE` 13, `priceUpdate` 11, `FLIPKART` 7, `LISTING` 6, `listingSync` 6, `CATALOG` 5, `B2C` 4, `DATABASE` 4, `DMS` 4, `NOTIFICATION` 4, `notification` 4, `DEALER` 3, `MARKETPLACE` 3, `SERVICE` 3, `flipkart` 3, `server` 3, `BOOKING` 2.

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `ACTIVE_ENVIRONMENT` | Unknown | Unknown | False | env-file |
| `AKS_BASE_URL` | Unknown | Unknown | False | env-file |
| `AMAZON_LWA_API_BASE_URL` | Unknown | Unknown | False | env-file |
| `AMAZON_LWA_TVS_CLIENT_ID` | Unknown | Unknown | False | env-file |
| `AMAZON_LWA_TVS_CLIENT_SECRET` | Unknown | Unknown | True | env-file |
| `AMAZON_LWA_TVS_CLIENT_SECRET_EXPIRY_DATE_UTC` | Unknown | Unknown | True | env-file |
| `AMAZON_LWA_TVS_CLIENT_SECRET_EXPIRY_WITHIN_DAYS` | Unknown | Unknown | True | env-file |
| `AMAZON_MASTER_SELLER_ID` | Unknown | Unknown | False | env-file |
| `AMAZON_MASTER_SELLER_REFRESH_TOKEN` | Unknown | Unknown | True | env-file |
| `AMAZON_SP_API_BASE_URL` | Unknown | Unknown | False | env-file |
| `AMAZON_SP_API_MARKETPLACE_ID` | Unknown | Unknown | False | env-file |
| `AMAZON_SQS_ACCESS_KEY` | Unknown | Unknown | True | env-file |
| `AMAZON_SQS_KEY_EXPIRY_DATE_UTC` | Unknown | Unknown | True | env-file |
| `AMAZON_SQS_KEY_EXPIRY_WITHIN_DAYS` | Unknown | Unknown | True | env-file |
| `AMAZON_SQS_QUEUE_NAME` | Unknown | Unknown | False | env-file |
| `AMAZON_SQS_RECEIVER_ENABLED` | Unknown | Unknown | False | env-file |
| `AMAZON_SQS_REGION` | Unknown | True | False | env-file |
| `AMAZON_SQS_SECRET_KEY` | Unknown | Unknown | True | env-file |
| `B2C_CLIENT_ID` | Unknown | True | False | env-file |
| `B2C_CLIENT_SECRET` | Unknown | True | True | env-file |
| `B2C_SCOPE` | Unknown | True | False | env-file |
| `B2C_TOKEN_URL` | Unknown | True | True | env-file |
| `BOOKING_SERVICE_API_BASE_URL` | Unknown | Unknown | False | env-file |
| `BOOKING_SERVICE_OCP_APIM_SUBSCRIPTION_KEY` | Unknown | Unknown | True | env-file |
| `CATALOG_PRODUCT_UPDATES_AMAZON_PROCESSING_ENABLED` | Unknown | Unknown | False | env-file |
| `CATALOG_PRODUCT_UPDATES_CONNECTION_STRING` | Unknown | Unknown | True | env-file |
| `CATALOG_PRODUCT_UPDATES_ENABLED` | Unknown | Unknown | False | env-file |
| `CATALOG_PRODUCT_UPDATES_SUBSCRIPTION_NAME` | Unknown | Unknown | False | env-file |
| `CATALOG_PRODUCT_UPDATES_TOPIC_NAME` | Unknown | Unknown | False | env-file |
| `CIPHER_KEY` | Unknown | True | True | env-file |
| `DATABASE_HOST_URL` | Unknown | Unknown | False | env-file |
| `DATABASE_NAME` | Unknown | Unknown | False | env-file |
| `DATABASE_PASSWORD` | Unknown | Unknown | True | env-file |
| `DATABASE_USERNAME` | Unknown | Unknown | False | env-file |
| `DEALER_INVENTORY_LOWER_LIMIT` | Unknown | Unknown | False | env-file |
| `DEALER_VEHICLE_MAPPING_INGESTION_ENABLED` | Unknown | Unknown | False | env-file |
| `DEALER_VEHICLE_MAPPING_UPLOAD_MAX_PART_ID_ROWS` | Unknown | Unknown | False | env-file |
| `DMS_API_BASE_URL` | Unknown | Unknown | False | env-file |
| `DMS_API_PASSWORD` | Unknown | True | True | env-file |
| `DMS_API_USER_ID` | Unknown | Unknown | False | env-file |
| `DMS_INVENTORY_SYNC_ENABLED` | Unknown | Unknown | False | env-file |
| `ENABLED_ECOMMERCE_MARKETPLACES` | Unknown | Unknown | False | env-file |
| `FLIPKART_OAUTH_API_REDIRECT_URI` | Unknown | Unknown | False | env-file |
| `FLIPKART_OAUTH_APPLICATION_ID` | Unknown | True | False | env-file |
| `FLIPKART_OAUTH_APPLICATION_SECRET` | Unknown | True | True | env-file |
| `FLIPKART_PARTNER_API_BASE_URL` | Unknown | True | False | env-file |
| `FLIPKART_SALT_KEY_REGENERATE_WHEN_EXPIRY_WITHIN_DAYS` | Unknown | True | True | env-file |
| `FLIPKART_SELLER_API_BASE_URL` | Unknown | Unknown | False | env-file |
| `FLIPKART_WEBHOOK_NOTIFICATION_URL` | Unknown | True | False | env-file |
| `HOSTNAME` | Unknown | Unknown | False | env-file |
| `LEAD_SERVICE_BASE_URL` | Unknown | Unknown | False | env-file |
| `LISTING_SYNC_AMAZON_APP_RATE_LIMIT_RPS` | Unknown | Unknown | False | env-file |
| `LISTING_SYNC_AMAZON_BATCH_SIZE` | Unknown | Unknown | False | env-file |
| `LISTING_SYNC_AMAZON_ENABLED` | Unknown | Unknown | False | env-file |
| `LISTING_SYNC_AMAZON_FORCE_FULL_SYNC` | Unknown | Unknown | False | env-file |
| `LISTING_SYNC_AMAZON_MASTER_RATE_LIMIT_RPS` | Unknown | Unknown | False | env-file |
| `LISTING_SYNC_AMAZON_SELLER_RATE_LIMIT_RPS` | Unknown | Unknown | False | env-file |
| `LOCATION_MASTER_BASE_URL` | Unknown | Unknown | False | env-file |
| `MARKETPLACE_APP_ENCRYPTION_KEY` | Unknown | True | True | env-file |
| `MARKETPLACE_APP_ENCRYPTION_SALT` | Unknown | True | True | env-file |
| `MARKETPLACE_DELIVERY_UPDATE_SOURCE_EVENT` | Unknown | Unknown | False | env-file |
| `MDP_API_BASE_URL` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_EMAIL_PRICE_UPDATE_PRIORITY` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_EMAIL_PRICE_UPDATE_RECIPIENTS` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_EMAIL_PRICE_UPDATE_TEMPLATE_ID` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_SERVICE_BASE_URL` | Unknown | Unknown | False | env-file |
| `PART_ID_MODEL_ID_TRANSITION_UPLOAD_MAX_ROWS` | Unknown | Unknown | False | env-file |
| `PRICE_ENGINE_UPDATES_CONNECTION_STRING` | Unknown | Unknown | True | env-file |
| `PRICE_ENGINE_UPDATES_SUBSCRIPTION_NAME` | Unknown | Unknown | False | env-file |
| `PRICE_ENGINE_UPDATES_TOPIC_NAME` | Unknown | Unknown | False | env-file |
| `PRICE_UPDATE_AMAZON_APP_RATE_LIMIT_RPS` | Unknown | Unknown | False | env-file |
| `PRICE_UPDATE_AMAZON_BATCH_SIZE` | Unknown | Unknown | False | env-file |
| `PRICE_UPDATE_AMAZON_SELLER_RATE_LIMIT_RPS` | Unknown | Unknown | False | env-file |
| `PRICE_UPDATE_FLIPKART_DEALER_AS_A_SELLER_TVS_CLIENT_ID` | Unknown | Unknown | False | env-file |
| `PRICE_UPDATE_FLIPKART_DEALER_AS_A_SELLER_TVS_CLIENT_SECRET` | Unknown | Unknown | True | env-file |
| `PRICE_UPDATE_FLIPKART_ENABLED_FLOWS` | Unknown | Unknown | False | env-file |
| `PRICE_UPDATE_PRICE_ENGINE_ENABLED` | Unknown | Unknown | False | env-file |
| `PRICE_UPDATE_PRICE_ENGINE_EV_USE_COMPONENT_BASED_CALCULATION` | Unknown | Unknown | False | env-file |
| `PRICE_UPDATE_PRICE_THRESHOLD_IN_INR` | Unknown | Unknown | False | env-file |
| `PRICE_UPDATE_SOURCE` | Unknown | Unknown | False | env-file |
| `SERVICEBUS_RECEIVERS_ENABLED` | Unknown | True | False | env-file |
| `SERVICE_BUS_BOOKING_UPDATES_CONNECTION_STRING` | Unknown | Unknown | True | env-file |
| `SERVICE_BUS_BOOKING_UPDATES_TOPIC_NAME` | Unknown | Unknown | False | env-file |
| `SERVICE_INTERNAL_API_SECRET` | Unknown | Unknown | True | env-file |
| `SHOW_HTTP_500_ERROR_DETAILS` | Unknown | Unknown | False | env-file |
| `VEHICLE_PRICE_DATA_TOPIC_CONNECTION_STRING` | Unknown | Unknown | True | env-file |
| `VEHICLE_PRICE_DATA_TOPIC_NAME` | Unknown | Unknown | False | env-file |
| `amazon.lwa.tvs-client-secret` | Unknown | True | True | app-settings |
| `amazon.lwa.tvs-client-secret-expiry-date-utc` | Unknown | Unknown | True | app-settings |
| `amazon.lwa.tvs-client-secret-expiry-within-days` | Unknown | True | True | app-settings |
| `amazon.sp.api.master-seller-refresh-token` | Unknown | True | True | app-settings |
| `amazon.sqs.access-key` | Unknown | True | True | app-settings |
| `amazon.sqs.key-expiry-date-utc` | Unknown | Unknown | True | app-settings |
| `amazon.sqs.key-expiry-within-days` | Unknown | True | True | app-settings |
| `amazon.sqs.secret-key` | Unknown | True | True | app-settings |
| `bookingService.api.base-url` | points to booking-crud-services | True | False | app-settings |
| `bookingService.ocp.apim.subscription.key` | Unknown | True | True | app-settings |
| `mdp.api.base-url` | points to master-data-platform | True | False | app-settings |
| `notification.base-url` | points to notification-service | True | False | app-settings |
| `priceUpdate.flipkart.dealer_as_a_seller.tvsClientSecret` | Unknown | True | True | app-settings |
| `service.internal-api.secret` | Unknown | True | True | app-settings |
| `spring.datasource.password` | Unknown | Unknown | True | app-settings |
| `spring.jms.servicebus.topic.bookingUpdates.connection-string` | Unknown | True | True | app-settings |
| `spring.jms.servicebus.topic.bookingUpdates.subscription` | Unknown | True | True | app-settings |
| `spring.jms.servicebus.topic.catalogProductUpdates.connection-string` | Unknown | True | True | app-settings |
| `spring.jms.servicebus.topic.priceEngineUpdates.connection-string` | Unknown | True | True | app-settings |
| `spring.jms.servicebus.topic.vehiclePriceData.connection-string` | Unknown | True | True | app-settings |

## Ownership
tvsm-marketplace-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvsm-marketplace-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvsm-marketplace-service limitations evidenced by extraction:
- 32 outbound HTTP call(s) have no resolved target service (base URL from config/env).
- No inbound callers resolved in the registry.
