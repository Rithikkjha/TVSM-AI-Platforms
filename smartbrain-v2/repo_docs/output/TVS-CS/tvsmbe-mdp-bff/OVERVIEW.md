---
service_id: tvsmbe-mdp-bff
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["tvsmbe mdp bff", "mdp bff", "mdp bff tvsmbe", "tvsmbe mdp", "mdp bff inbound tvsmbe", "mdp bff outbound tvsmbe", "mdp"]
---

# tvsmbe-mdp-bff — Overview

## Purpose
Summary: BFF for master-data-platform (dealer, product, price) that also talks to external services such as single-interface and Knowlarity, with inbound and outbound modules.
Also known as: tvsmbe mdp bff, mdp bff, mdp bff tvsmbe, tvsmbe mdp, mdp bff inbound tvsmbe, mdp bff outbound tvsmbe, mdp
tvsmbe-mdp-bff is a `bff` repository (`tvsmbe-mdp-bff`; service.yaml `type: bff`). Business purpose: README (`README.md`) describes it as: tvsmbe-mdp-bff — This service holds these major responsibilities :.
It contains 2 subprojects: `inbound` (service), `outbound` (service).

## Users and Consumers
tvsmbe-mdp-bff is called over HTTP by: `cbs-admin-portal`. Event consumers of its published messages: none resolved.

## Key Capabilities
tvsmbe-mdp-bff capabilities derived from code:
- `MdpController`: 3 HTTP endpoint(s)
- `TestController`: 3 HTTP endpoint(s)
- `WebHookController`: 1 HTTP endpoint(s)
- Scheduled job `CronService.logMetricsPeriodically` (fixed-rate `60000`)
- Scheduled job `CronService.logMetricsPeriodically` (fixed-rate `60000`)
- Consumes 1 messaging entit(y/ies)

## Tech Stack
tvsmbe-mdp-bff tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | mysql | Unknown |
| Messaging | azure-service-bus | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.azure:azure-messaging-servicebus`, `com.google.guava:guava`, `com.mysql:mysql-connector-j`, `com.squareup.okhttp3:okhttp`, `org.hibernate:hibernate-envers`, `org.projectlombok:lombok`, `org.springdoc:springdoc-openapi-starter-webmvc-ui`, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-parent`, `org.springframework.boot:spring-boot-starter-web`, `org.springframework.retry:spring-retry`

## Dependencies at a Glance
Upstream (calls tvsmbe-mdp-bff): `cbs-admin-portal`
Downstream (tvsmbe-mdp-bff calls): `master-data-platform` (hard), `notification-service` (hard); plus 5 outbound call(s) with unresolved target
Brokers: azure-service-bus. Data stores: `_` (mysql, write), `tvsmazebffsdbdev01` (mysql, write), `tvsmazebffsdbdev01` (mysql, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvsmbe-mdp-bff environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
tvsmbe-mdp-bff configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `ACTIVE_ENVIRONMENT` | Unknown | Unknown | False | env-file |
| `AZURE_B2C_CLIENT_ID` | Unknown | Unknown | False | env-file |
| `AZURE_B2C_CLIENT_SECRET` | Unknown | Unknown | True | env-file |
| `AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL` | Unknown | Unknown | True | env-file |
| `AZURE_B2C_SCOPE` | Unknown | Unknown | False | env-file |
| `AZURE_CLIENT_ID` | Unknown | Unknown | False | env-file |
| `DAKSHA_DEALER_UPDATE_API_TOKEN` | Unknown | Unknown | True | env-file |
| `DAKSHA_DEALER_UPDATE_API_URL` | Unknown | Unknown | False | env-file |
| `DATABASE_HOST_URL` | Unknown | Unknown | False | env-file |
| `DATABASE_NAME` | Unknown | Unknown | False | env-file |
| `DATABASE_PASSWORD` | Unknown | Unknown | True | env-file |
| `DATABASE_USERNAME` | Unknown | Unknown | False | env-file |
| `EXTERNAL_CLIENTS_FAILURE_EMAIL_ALERT_RECIPIENTS` | Unknown | Unknown | False | env-file |
| `KNOWLARITY_K_NUMBER_API_TOKEN` | Unknown | Unknown | True | env-file |
| `KNOWLARITY_K_NUMBER_API_URL` | Unknown | Unknown | False | env-file |
| `KNOWLARITY_K_NUM_ASSIGNMENT_ENABLED_DEALER_TYPES` | Unknown | Unknown | False | env-file |
| `KNOWLARITY_K_NUM_POOL_API_EMPTY_NOTIFICATION_RECIPIENTS` | Unknown | Unknown | False | env-file |
| `LATLONG_DEALER_DATA_API_TOKEN` | Unknown | Unknown | True | env-file |
| `LATLONG_DEALER_DATA_API_URL` | Unknown | Unknown | False | env-file |
| `MDP_BASE_URL` | Unknown | Unknown | False | env-file |
| `MDP_BFF_EXTERNAL_CLIENTS` | Unknown | Unknown | False | env-file |
| `MDP_DEALER_DATA_TOPIC_CONNECTION_STRING` | Unknown | Unknown | True | env-file |
| `MDP_DEALER_DATA_TOPIC_NAME` | Unknown | Unknown | False | env-file |
| `MDP_DEALER_DATA_TOPIC_NAMESPACE` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_B2C_SCOPE` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_BASE_URL` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_EMAIL_FAILURE_PRIORITY` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_FAILURE_EMAIL_TEMPLATE_ID` | Unknown | Unknown | False | env-file |
| `SI_ENABLED_DEALER_TYPES` | Unknown | Unknown | False | env-file |
| `SI_OUTLET_API_BASE_URL` | Unknown | Unknown | False | env-file |
| `SI_OUTLET_API_TOKEN` | Unknown | Unknown | True | env-file |
| `TZ` | Unknown | Unknown | False | Unknown |
| `TZ` | Unknown | Unknown | False | Unknown |
| `WEBSITE_HTTPLOGGING_RETENTION_DAYS` | Unknown | Unknown | False | env-file |
| `azure.b2c.client.id` | Unknown | True | False | app-settings |
| `azure.b2c.client.id` | Unknown | True | False | app-settings |
| `azure.b2c.client.secret` | Unknown | True | True | app-settings |
| `azure.b2c.client.secret` | Unknown | True | True | app-settings |
| `azure.b2c.scope` | Unknown | True | False | app-settings |
| `azure.b2c.scope` | Unknown | True | False | app-settings |
| `azure.b2c.token.url` | Unknown | True | True | app-settings |
| `azure.b2c.token.url` | Unknown | True | True | app-settings |
| `daksha.dealer.update.api.auth.token` | Unknown | True | True | app-settings |
| `daksha.dealer.update.api.url` | Unknown | True | False | app-settings |
| `external.clients.failure.email.alert.recipients` | Unknown | True | False | app-settings |
| `generate.azure.b2c.token` | Unknown | Unknown | True | app-settings |
| `knowlarity.kNumber.assignment.enabled.dealer.types` | Unknown | True | False | app-settings |
| `knowlarity.kNumberApi.authToken` | Unknown | True | True | app-settings |
| `knowlarity.kNumberApi.url` | Unknown | True | False | app-settings |
| `latLong.api.authToken` | Unknown | True | True | app-settings |
| `latLong.api.url` | Unknown | True | False | app-settings |
| `logging.level.com.azure.*` | Unknown | Unknown | False | app-settings |
| `logging.level.com.azure.*` | Unknown | Unknown | False | app-settings |
| `logging.level.com.microsoft.aad.msal4j` | Unknown | Unknown | False | app-settings |
| `logging.level.root` | Unknown | Unknown | False | app-settings |
| `logging.level.root` | Unknown | Unknown | False | app-settings |
| `mdp.api.dealer.mapDealerWithKNumber` | points to master-data-platform | True | False | app-settings |
| `mdp.api.dealer.unassignVirtualNumber` | Unknown | True | False | app-settings |
| `mdp.base-url` | Unknown | Unknown | False | app-settings |
| `mdp.base-url` | Unknown | Unknown | False | app-settings |
| `mdp.bff.enabled.clients` | Unknown | True | False | app-settings |
| `mdp.generate.auth.token` | Unknown | Unknown | True | app-settings |
| `mdp.get-dealer-data.api-url` | Unknown | True | False | app-settings |
| `mdp.get-dealer-data.based-on-filters.api-url` | points to master-data-platform | True | False | app-settings |
| `mdp.get-dealer-data.by-pincode.api-url` | Unknown | True | False | app-settings |
| `mdp.get.dealer.data` | Unknown | Unknown | False | app-settings |
| `notification.base-url` | points to notification-service | True | False | app-settings |
| `notification.email.failure.priority` | Unknown | True | False | app-settings |
| `notification.failure-email.templateId` | Unknown | True | False | app-settings |
| `server.error.whitelabel.enabled` | Unknown | Unknown | False | app-settings |
| `server.error.whitelabel.enabled` | Unknown | Unknown | False | app-settings |
| `server.port` | Unknown | Unknown | False | app-settings |
| `server.port` | Unknown | Unknown | False | app-settings |
| `server.servlet.context-path` | Unknown | Unknown | False | app-settings |
| `server.servlet.context-path` | Unknown | Unknown | False | app-settings |
| `si.outletApi.authToken` | Unknown | True | True | app-settings |
| `si.outletApi.baseUrl` | Unknown | True | False | app-settings |
| `single.interface.enabled.dealer.types` | Unknown | True | False | app-settings |
| `spring.application.name` | Unknown | Unknown | False | app-settings |
| `spring.application.name` | Unknown | Unknown | False | app-settings |
| `spring.datasource.driver-class-name` | Unknown | Unknown | False | app-settings |
| `spring.datasource.driver-class-name` | Unknown | Unknown | False | app-settings |
| `spring.datasource.password` | Unknown | Unknown | True | app-settings |
| `spring.datasource.password` | Unknown | Unknown | True | app-settings |
| `spring.datasource.url` | Unknown | Unknown | False | app-settings |
| `spring.datasource.url` | Unknown | Unknown | False | app-settings |
| `spring.datasource.username` | Unknown | Unknown | False | app-settings |
| `spring.datasource.username` | Unknown | Unknown | False | app-settings |
| `spring.h2.console.enabled` | Unknown | Unknown | False | app-settings |
| `spring.h2.console.enabled` | Unknown | Unknown | False | app-settings |
| `spring.h2.console.path` | Unknown | Unknown | False | app-settings |
| `spring.h2.console.path` | Unknown | Unknown | False | app-settings |
| `spring.jms.servicebus.topic.mdpDealerData.connection-string` | Unknown | True | True | app-settings |
| `spring.jms.servicebus.topic.mdpDealerData.name` | Unknown | True | False | app-settings |
| `spring.jms.servicebus.topic.mdpDealerData.subscription` | Unknown | True | False | app-settings |
| `spring.jpa.database-platform` | Unknown | Unknown | False | app-settings |
| `spring.jpa.database-platform` | Unknown | Unknown | False | app-settings |
| `spring.output.ansi.enabled` | Unknown | Unknown | False | app-settings |
| `spring.output.ansi.enabled` | Unknown | Unknown | False | app-settings |
| `spring.profiles.active` | Unknown | Unknown | False | app-settings |
| `spring.profiles.active` | Unknown | True | False | app-settings |
| `springdoc.api-docs.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.api-docs.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.show-actuator` | Unknown | Unknown | False | app-settings |
| `springdoc.show-actuator` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.path` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.path` | Unknown | Unknown | False | app-settings |

## Ownership
tvsmbe-mdp-bff ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvsmbe-mdp-bff local setup evidence:
- README: `README.md`
- Dockerfile(s): `inbound/Dockerfile`, `outbound/Dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvsmbe-mdp-bff limitations evidenced by extraction:
- 5 outbound HTTP call(s) have no resolved target service (base URL from config/env).
