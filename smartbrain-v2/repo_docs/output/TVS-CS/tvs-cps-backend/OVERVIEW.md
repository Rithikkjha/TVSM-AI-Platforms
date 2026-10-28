---
service_id: tvs-cps-backend
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["tvs cps backend", "channel partner backend", "announcement service", "appointment service", "claim service", "collateral service", "data access service", "lead allocation", "npqr service", "order service", "scheduler analytics", "training service", "tvs cps app", "workflow service", "cps"]
---

# TVS-CPS-BACKEND — Overview

## Purpose
Summary: Multi-module Spring Boot backend of the TVS Channel Partner System covering orders, appointments, claims, training, workflow, notifications, lead allocation and a BFF aggregation layer.
Also known as: tvs cps backend, channel partner backend, announcement service, appointment service, claim service, collateral service, data access service, lead allocation, npqr service, order service, scheduler analytics, training service, tvs cps app, workflow service, cps

`tvs-cps-backend` is the TVS Channel Partner System (CPS) backend: a multi-module Spring Boot application covering orders, appointments, claims, training, collateral, notifications, workflow, announcements, NPQR, lead allocation and a BFF aggregation layer (`README.md`). All modules are assembled into one runnable app, `tvs-cps-app` (`tvs-cps-app/src/main/java/com/tvsm/cps/backend/TVSCPSBackendApplication.java`). Business owners and SLAs: Unknown.

## Users and Consumers

`tvs-cps-backend` callers (service.yaml inbound): `tvs-cps-backend`, `tvs-cps-jobs`, `tvs-cps-portal`.

Event consumers of its published events: `tvs-cps-backend`.

## Key Capabilities

`tvs-cps-backend` capabilities (from endpoints, jobs and events in code):

- Domain modules (per `pom.xml` modules): order, appointment, claim, workflow, training, collateral, announcement, notification, npqr, lead-allocation
- BFF aggregation layer (`bff-service`) calling CPS domain services and other TVS services
- Kafka/Event Hubs and Azure Service Bus messaging (see API_SPEC events)
- Swagger/OpenAPI via springdoc at `/api-docs` (`README.md`)

- HTTP API handlers: `OrderBFFController` (27), `OrderController` (21), `InventoryBFFController` (19), `CatalogController` (14), `ClaimController` (14), `AppointmentController` (13), `ClaimBFFController` (13), `EnquiryBFFController` (12), `JobcardBFFController` (12), `AppointmentBFFController` (11), `InternalServiceBFFController` (11), `AnnouncementController` (10), `AnnouncementBFFController` (10), `WorkflowBFFController` (10), `CartBFFController` (9), `CartController` (9), `BookingBFFController` (8), `GrnBFFController` (8), `CustomerBFFController` (7), `GrnController` (7), `BillingBFFController` (6), `TenantConfigController` (5), `DocController` (5), `LeadAllocationController` (5), `NotificationCategoryController` (5), `NotificationMessageController` (5), `WorkflowController` (5), `WorkflowTemplateController` (5), `TrainingBFFController` (4), `LeadServiceBFFController` (4), `NotificationCategoryBFFController` (4), `NotificationMessageBFFController` (4), `NotificationActionConfigController` (4), `TrainingController` (4), `DashboardBFFController` (3), `PermissionBFFController` (3), `WarrantyBFFController` (3), `LeadAllocationBFFController` (3), `NotificationBFFController` (3), `SmartSearchBFFController` (3), `LeadAllocationSystemController` (3), `InvoiceController` (3), `InternalERPServiceController` (3), `AppointmentSystemController` (2), `ReportsBFFController` (2), `InvoiceBFFController` (2), `LocationMasterController` (2), `CollateralBFFController` (2), `NotificationDeviceBFFController` (2), `NotificationEventBFFController` (2), `NotificationPreferenceBFFController` (2), `NpqrBFFController` (2), `VehicleBFFController` (2), `CollateralController` (2), `NotificationDeviceController` (2), `NotificationPreferenceController` (2), `NpqrController` (2), `ApplicationHealthController` (2), `AppointmentAnalyticsController` (1), `ExternalAppointmentController` (1), `AppointmentJobController` (1), `L1DashboardController` (1), `ChannelPartnerBFFController` (1), `UmsBffController` (1), `AppointmentAnalyticsBFFController` (1), `BillingReportController` (1), `CalendarBFFController` (1), `ClaimAnalyticsBFFController` (1), `NotificationEventTriggerController` (1), `AnalyticsController` (1), `InventoryAnalyticsBFFController` (1), `ClaimAnalyticsController` (1), `ClaimJobController` (1), `NotificationEventConsumerController` (1), `NotificationSeedController` (1), `OrderReportController` (1), `OrderAnalyticsController` (1), `UserAssignmentController` (1), `UserAssignmentSystemController` (1)
- Scheduled jobs: `JobScheduler.loadCatalogData`, `JobScheduler.retrieveMDPDealers`, `JobScheduler.retrieveMerchandiseStock`, `JobScheduler.warmUpUmsCache`, `NotificationDeviceCleanupScheduler.deactivateStaleDevices`
- Messaging: 5 publisher(s), 7 consumer(s)

## Tech Stack

`tvs-cps-backend` tech stack from service.yaml `tech_stack` and manifests (stacks: java).

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | postgres (_), postgres (nmazcpsdbdev01-cps) | — |
| Messaging | azure-service-bus, kafka | — |
| Hosting | docker | — |
| Build | java | — |

Key libraries: `com.azure:azure-messaging-servicebus`, `com.fasterxml.jackson.core:jackson-databind`, `com.github.ben-manes.caffeine:caffeine`, `com.tvsm:tvs-cps-backend`, `com.tvsm:tvsm-be-core`, `com.tvsm:tvsm-be-starter-parent`, `commons-validator:commons-validator`, `io.swagger.core.v3:swagger-annotations-jakarta`, `jakarta.validation:jakarta.validation-api`, `org.apache.commons:commons-csv`, `org.apache.poi:poi`, `org.apache.poi:poi-ooxml`, `org.drools:drools-compiler`, `org.drools:drools-core`, `org.drools:drools-engine`, `org.drools:drools-mvel`, `org.drools:drools-xml-support`, `org.hibernate.orm:hibernate-core`, `org.junit:junit-bom`, `org.kie:kie-api`, `org.mapstruct:mapstruct`, `org.mapstruct:mapstruct-processor`, `org.postgresql:postgresql`, `org.projectlombok:lombok`, `org.slf4j:slf4j-api`, `org.springdoc:springdoc-openapi-starter-webmvc-ui`, `org.springframework.boot:spring-boot`, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-aop`, `org.springframework.boot:spring-boot-starter-cache`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-validation`, `org.springframework.boot:spring-boot-starter-web`, `org.springframework.boot:spring-boot-starter-webflux`, `org.springframework.data:spring-data-jpa`, `org.springframework.kafka:spring-kafka`, `org.springframework.retry:spring-retry`, `org.springframework:spring-context`, `org.springframework:spring-framework-bom`, `org.springframework:spring-tx` (+2 more in service.yaml)

## Dependencies at a Glance

`tvs-cps-backend` dependencies.

Upstream (calls `tvs-cps-backend`): `tvs-cps-backend`, `tvs-cps-jobs`, `tvs-cps-portal`

Downstream (`tvs-cps-backend` calls): `external:onetrust` (hard/unknown), `tvs-cps-backend` (hard), `tvs-cps-customer` (hard), `tvs-cps-inventory` (hard), `tvs-cps-job-card-service` (hard), `tvs-cps-billing` (hard), `booking-crud-services` (hard), `notification-service` (hard), `tvsm-otp-service` (hard); plus 60 outbound call(s) with unresolved target (see API_SPEC Outbound Calls)

Brokers: azure-service-bus, kafka  
Data stores: `nmazcpsdbdev01-cps`, `_`

Full detail: service.yaml `inbound` / `outbound`.

## Environments

`tvs-cps-backend` environments seen in config/infra files: dev, prod, training, uat. URLs are not documented here (Unknown / not taken from config).

| Env | URL | Notes |
|---|---|---|
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| training | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables

`tvs-cps-backend` reads 904 distinct config key(s) (names only, values never shown). Showing 150 (secrets and externally-provided first); full list in service.yaml `config`.

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `apim.client-secret` | Unknown | True | True | Unknown |
| `apim.clientSecret` | Unknown | True | True | Unknown |
| `azure.client-secret` | Unknown | True | True | Unknown |
| `azure.token-url` | Unknown | True | True | Unknown |
| `bff.booking.messaging.kafka.consumer.consumers.booking.security.sasl-jaas-config` | Unknown | Unknown | True | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.subscribers.booking.key-deserializer` | Unknown | Unknown | True | app-settings |
| `bff.catalog-service.catalog.add-discount.parent.key` | Unknown | True | True | Unknown |
| `bff.catalog-service.catalog.discount.percentage.key` | Unknown | True | True | Unknown |
| `bff.catalog-service.catalog.freight-charge.value.key` | Unknown | True | True | Unknown |
| `bff.catalog-service.catalog.payment-term.value.key` | Unknown | True | True | Unknown |
| `bff.catalog-service.catalog.price.value.key` | Unknown | True | True | Unknown |
| `bff.catalog-service.catalog.rrp.value.key` | Unknown | True | True | Unknown |
| `bff.catalog-service.catalog.std-discount.parent.key` | Unknown | True | True | Unknown |
| `bff.catalog-service.catalog.total-price.value.key` | Unknown | True | True | Unknown |
| `bff.catalog-service.catalog.vat.parent.key` | Unknown | True | True | Unknown |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.subscribers.servicelead.key-deserializer` | Unknown | Unknown | True | app-settings |
| `bff.servicelead.messaging.kafka.publisher.publishers.servicelead.key-serializer` | Unknown | Unknown | True | app-settings |
| `billing.catalog.parts-price-key` | Unknown | True | True | Unknown |
| `billing.catalog.vehicle-price-key` | Unknown | True | True | Unknown |
| `booking-service.master-data-file-path` | Unknown | Unknown | True | app-settings |
| `booking.servicebus.connection-string` | Unknown | True | True | Unknown |
| `claim.sap.data-lake.function-code` | Unknown | Unknown | True | app-settings |
| `claim.sap.oauth.client.id` | Unknown | Unknown | True | app-settings |
| `claim.sap.oauth.client.secret` | Unknown | True | True | Unknown |
| `claim.sap.oauth.token.url` | Unknown | True | True | Unknown |
| `commons.messaging.kafka.consumer.security.sasl-jaas-config` | Unknown | Unknown | True | app-settings |
| `commons.messaging.kafka.consumer.subscribers.order.key-deserializer` | Unknown | Unknown | True | app-settings |
| `commons.messaging.kafka.consumer.subscribers.serviceLead.key-deserializer` | Unknown | Unknown | True | app-settings |
| `commons.messaging.kafka.publisher.key-serializer` | Unknown | Unknown | True | app-settings |
| `enquiry.service.master-data-file-path` | Unknown | Unknown | True | app-settings |
| `erp.api.bearer.token` | Unknown | Unknown | True | Unknown |
| `erp.data-lake.function-code` | Unknown | Unknown | True | app-settings |
| `erp.oauth.client.id` | Unknown | Unknown | True | app-settings |
| `erp.oauth.client.secret` | Unknown | True | True | Unknown |
| `erp.oauth.token.url` | Unknown | True | True | Unknown |
| `lead.servicebus.connection-string` | Unknown | True | True | Unknown |
| `notification.gateway.email.cc` | Unknown | Unknown | True | app-settings |
| `notification.messaging.kafka.consumer.consumers.notification.security.sasl-jaas-config` | Unknown | Unknown | True | app-settings |
| `notification.messaging.kafka.consumer.consumers.notification.subscribers.notification.key-deserializer` | Unknown | Unknown | True | app-settings |
| `notification.messaging.kafka.publisher.publishers.notification.key-serializer` | Unknown | Unknown | True | app-settings |
| `notification.messaging.kafka.publisher.publishers.notification.security.sasl-jaas-config` | Unknown | Unknown | True | app-settings |
| `one-trust.client-secret` | Unknown | True | True | Unknown |
| `one-trust.purpose.legitimate-interest.custom-preference.options` | Unknown | Unknown | True | app-settings |
| `one-trust.purpose.marketing-communication.custom-preference.options` | Unknown | Unknown | True | app-settings |
| `one-trust.token-url` | Unknown | True | True | Unknown |
| `order.messaging.kafka.consumer.consumers.order.security.sasl-jaas-config` | Unknown | Unknown | True | app-settings |
| `order.messaging.kafka.consumer.consumers.order.subscribers.order.key-deserializer` | Unknown | Unknown | True | app-settings |
| `order.messaging.kafka.publisher.publishers.booking.key-serializer` | Unknown | Unknown | True | app-settings |
| `order.messaging.kafka.publisher.publishers.booking.security.sasl-jaas-config` | Unknown | Unknown | True | app-settings |
| `order.messaging.kafka.publisher.publishers.default.key-serializer` | Unknown | Unknown | True | app-settings |
| `order.messaging.kafka.publisher.publishers.default.security.sasl-jaas-config` | Unknown | Unknown | True | app-settings |
| `tvsm.core.cloud-storage.azure.connection-string` | Unknown | Unknown | True | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.password` | Unknown | Unknown | True | app-settings |
| `tvsm.core.security.jwt.publicKey.key1` | Unknown | Unknown | True | app-settings |
| `ums.servicebus.connection-string` | Unknown | True | True | Unknown |
| `analytics.default.page-size` | Unknown | True | False | Unknown |
| `analytics.default.start-date` | Unknown | True | False | Unknown |
| `apim.client-id` | Unknown | True | False | Unknown |
| `apim.clientId` | Unknown | True | False | Unknown |
| `apim.rest.timeout.connect` | Unknown | Unknown | False | Unknown |
| `apim.rest.timeout.read` | Unknown | Unknown | False | Unknown |
| `apim.scope` | Unknown | True | False | Unknown |
| `apim.scope-ui` | Unknown | True | False | Unknown |
| `apim.tenant-id` | Unknown | True | False | Unknown |
| `apim.tenantId` | Unknown | True | False | Unknown |
| `app.reminder-days` | Unknown | Unknown | False | Unknown |
| `app.rest.timeout.connect` | Unknown | Unknown | False | Unknown |
| `app.rest.timeout.read` | Unknown | Unknown | False | Unknown |
| `appointment.auto-close-days` | Unknown | Unknown | False | Unknown |
| `appointment.external.allowed-tenant-ids` | Unknown | True | False | Unknown |
| `azure.client-id` | Unknown | True | False | Unknown |
| `azure.eventhub.appointment.hub-name` | Unknown | True | False | Unknown |
| `azure.grant-type` | Unknown | True | False | Unknown |
| `azure.kafka.bootstrap-servers` | Unknown | True | False | Unknown |
| `azure.kafka.properties.sasl.jaas.config` | Unknown | True | False | Unknown |
| `azure.kafka.properties.sasl.mechanism` | Unknown | Unknown | False | app-settings |
| `azure.kafka.properties.security.protocol` | Unknown | Unknown | False | app-settings |
| `azure.scope` | Unknown | True | False | Unknown |
| `bff.announcement-service.base-url` | points to tvs-cps-backend | True | False | Unknown |
| `bff.appointment-service.base-url` | points to tvs-cps-backend | True | False | Unknown |
| `bff.billing-service.base-url` | points to tvs-cps-billing | True | False | Unknown |
| `bff.booking-service.base-url` | points to booking-crud-services | True | False | Unknown |
| `bff.booking.messaging.kafka.consumer.consumers.booking.bootstrap-servers` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.enabled-dlt` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.group-id-prefix` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.security.sasl-mechanism` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.security.security-protocol` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.security.ssl-endpoint-identification-algorithm` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.subscribers.booking.batch-list` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.subscribers.booking.concurrency` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.subscribers.booking.dlt.enabled` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.subscribers.booking.retry.attempt` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.subscribers.booking.retry.back-off-ms` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.consumers.booking.subscribers.booking.value-deserializer` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.consumer.enabled` | Unknown | Unknown | False | app-settings |
| `bff.booking.messaging.kafka.topics.booking` | Unknown | Unknown | False | app-settings |
| `bff.catalog-service.base-url` | Unknown | True | False | Unknown |
| `bff.catalog-service.catalog.page-size` | Unknown | True | False | Unknown |
| `bff.claim-service.base-url` | points to tvs-cps-backend | True | False | Unknown |
| `bff.collateral-service.base-url` | points to tvs-cps-backend | True | False | Unknown |
| `bff.customer-service-local.base-url` | points to tvs-cps-backend | True | False | Unknown |
| `bff.customer-service.base-url` | points to tvs-cps-customer | True | False | Unknown |
| `bff.doc-service.base-url` | Unknown | True | False | Unknown |
| `bff.header-forwarding.allowed-headers[0]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[1]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[2]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[3]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[4]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[5]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[6]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[7]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowedHeaders` | Unknown | True | False | Unknown |
| `bff.inventory-service-internal.base-url` | Unknown | True | False | Unknown |
| `bff.inventory-service-local.base-url` | points to tvs-cps-backend | True | False | Unknown |
| `bff.inventory-service.base-url` | points to tvs-cps-inventory | True | False | Unknown |
| `bff.inventory-update.pool-size` | Unknown | Unknown | False | Unknown |
| `bff.jobcard-service.base-url` | points to tvs-cps-job-card-service | True | False | Unknown |
| `bff.lead-allocation.base-url` | points to tvs-cps-backend | True | False | Unknown |
| `bff.lead-service.base-url` | Unknown | True | False | Unknown |
| `bff.location-master-service.base-url` | Unknown | Unknown | False | Unknown |
| `bff.mdp-service.base-url` | Unknown | Unknown | False | app-settings |
| `bff.notification-service.base-url` | points to tvs-cps-backend | True | False | Unknown |
| `bff.npqr-service.base-url` | points to tvs-cps-backend | True | False | Unknown |
| `bff.order-service.base-url` | points to tvs-cps-backend | True | False | Unknown |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.bootstrap-servers` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.enabled-dlt` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.group-id-prefix` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.security.sasl-jaas-config` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.security.sasl-mechanism` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.security.security-protocol` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.security.ssl-endpoint-identification-algorithm` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.subscribers.servicelead.batch-list` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.subscribers.servicelead.concurrency` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.subscribers.servicelead.dlt.enabled` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.subscribers.servicelead.retry.attempt` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.subscribers.servicelead.retry.back-off-ms` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.consumers.servicelead.subscribers.servicelead.value-deserializer` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.consumer.enabled` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.producer.enabled` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.publisher.enabled` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.publisher.publishers.servicelead.bootstrap-servers` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.publisher.publishers.servicelead.security.sasl-jaas-config` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.publisher.publishers.servicelead.security.sasl-mechanism` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.publisher.publishers.servicelead.security.security-protocol` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.publisher.publishers.servicelead.security.ssl-endpoint-identification-algorithm` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.publisher.publishers.servicelead.value-serializer` | Unknown | Unknown | False | app-settings |
| `bff.servicelead.messaging.kafka.topics.service-lead` | Unknown | Unknown | False | Unknown |
| `bff.source-lookup.base-url` | Unknown | Unknown | False | app-settings |
| `bff.training-service.base-url` | points to tvs-cps-backend | True | False | Unknown |
| `bff.ums-auth-service.base-url` | Unknown | Unknown | False | app-settings |

## Ownership

`tvs-cps-backend` ownership is not recorded in code (no CODEOWNERS file).

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup

`tvs-cps-backend` local setup (from `README.md`):

1. Requires Java 21+, Maven 3.8+, local PostgreSQL.
2. Create and migrate the schema with the `tvs-cps-db-migration` repo (Flyway; `mvn clean install` then `java -jar target/tvs-cps-db-migration-1.0.0-SNAPSHOT.jar migrate config.yml`).
3. Point `tvsm.core.multitenant.datasource.default-data-source` in `tvs-cps-app/src/main/resources/config/application.yml` at the local DB (credentials via `DB_USERNAME` / `DB_PASSWORD` env vars).
4. Downstream `bff.*.base-url` entries default to `http://localhost:8080`.
5. `mvn clean install` at the root, then `cd tvs-cps-app && mvn spring-boot:run` (port 8080).
6. Verify: `/swagger-ui.html`, `/api-docs`, `/actuator/health`.

## Known Limitations

`tvs-cps-backend` has 67 unresolved registry item(s) (registry/unresolved.json): outbound_http: dynamic_url ×35, outbound_http: no_route_match ×22, outbound_http: unknown_host ×8, outbound_http: no_base_url ×2
