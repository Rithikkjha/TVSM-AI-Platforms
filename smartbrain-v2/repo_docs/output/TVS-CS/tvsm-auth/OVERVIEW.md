---
service_id: tvsm-auth
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["tvsm auth", "ums", "auth ninja", "auth", "norton auth ninja"]
---

# tvsm-auth — Overview

## Purpose
Summary: Spring Boot authentication and user-management service (Azure AD B2C sign-in) with user profile, application, role, dealer and dynamic-form APIs.
Also known as: tvsm auth, ums, auth ninja, auth, norton auth ninja
tvsm-auth is a `backend-api` repository (`tvsm-auth`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as:  — page_type: Authentication Service languages:.

## Users and Consumers
tvsm-auth is called over HTTP by: `tvsm-auth`, `tvsmbe-location`. Event consumers of its published messages: none resolved.

## Key Capabilities
tvsm-auth capabilities derived from code:
- `UserProfileController`: 32 HTTP endpoint(s)
- `ApplicationController`: 20 HTTP endpoint(s)
- `DealerController`: 6 HTTP endpoint(s)
- `RoleController`: 6 HTTP endpoint(s)
- `DynamicFormController`: 5 HTTP endpoint(s)
- `UserApplicationController`: 4 HTTP endpoint(s)
- `Unknown`: 4 HTTP endpoint(s)
- `AdminController`: 3 HTTP endpoint(s)
- `GroupController`: 3 HTTP endpoint(s)
- `DepartmentController`: 2 HTTP endpoint(s)
- `ConsentController`: 2 HTTP endpoint(s)
- `LocationController`: 1 HTTP endpoint(s)
- `EkycController`: 1 HTTP endpoint(s)
- Scheduled job `CacheClearScheduler.evictAllCachesAtIntervals` (cron `0 0 2 * * ?`)
- Scheduled job `NotificationReminder.sendSMSForFaceLogin` (cron `0 0 18 * * ?`)
- Publishes 1 messaging entit(y/ies); consumes 0

## Tech Stack
tvsm-auth tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | mysql | Unknown |
| Messaging | azure-service-bus | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.auth0:java-jwt`, `com.azure:azure-ai-vision-face`, `com.azure:azure-identity`, `com.azure:azure-messaging-servicebus`, `com.azure:azure-storage-blob`, `com.fasterxml.jackson.datatype:jackson-datatype-jsr310`, `com.microsoft.graph:microsoft-graph`, `com.mysql:mysql-connector-j`, `com.opencsv:opencsv`, `org.apache.poi:poi-ooxml`, `org.json:json`, `org.projectlombok:lombok`, `org.springdoc:springdoc-openapi-starter-webmvc-ui`, `org.springframework.boot:spring-boot-configuration-processor`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-parent`, `org.springframework.boot:spring-boot-starter-security`, `org.springframework.boot:spring-boot-starter-validation`, `org.springframework.boot:spring-boot-starter-web`, `org.springframework.boot:spring-boot-starter-webflux`, `org.springframework.retry:spring-retry`

## Dependencies at a Glance
Upstream (calls tvsm-auth): `tvsm-auth`, `tvsmbe-location`
Downstream (tvsm-auth calls): `master-data-platform` (hard), `notification-service` (hard), `tvsm-auth` (hard); plus 17 outbound call(s) with unresolved target
Brokers: azure-service-bus. Data stores: `_` (mysql, write), `config:spring.datasource.url` (mysql, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvsm-auth environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| local | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| test | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
tvsm-auth configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `AZURE_SERVICE_BUS_NAMESPACE` | Unknown | Unknown | False | app-settings |
| `AZURE_SERVICE_BUS_TOPIC_NAME` | Unknown | Unknown | False | app-settings |
| `B2C_TENANT` | Unknown | Unknown | False | env-file |
| `CLIENT_ID` | Unknown | Unknown | False | env-file |
| `CLIENT_SECRET` | Unknown | Unknown | True | env-file |
| `FILE_NAME_CREATE` | Unknown | Unknown | False | env-file |
| `FILE_NAME_UPDATE` | Unknown | Unknown | False | env-file |
| `JAVA_OPTS` | Unknown | Unknown | False | Unknown |
| `RESOURCE_ID` | Unknown | Unknown | False | env-file |
| `SCOPE` | Unknown | Unknown | False | env-file |
| `TZ` | Unknown | Unknown | False | Unknown |
| `admin.roles.department` | Unknown | True | False | app-settings |
| `application.b2c.api.password` | Unknown | Unknown | True | app-settings |
| `application.b2c.api.username` | Unknown | Unknown | False | app-settings |
| `application.b2c.baseUri` | Unknown | True | False | app-settings |
| `application.b2c.clientId` | Unknown | True | False | app-settings |
| `application.b2c.clientSecret` | Unknown | True | True | app-settings |
| `application.b2c.grantType` | Unknown | True | False | app-settings |
| `application.b2c.graphApiScope` | Unknown | True | False | app-settings |
| `application.b2c.issuer` | Unknown | True | False | app-settings |
| `application.b2c.responseType` | Unknown | True | False | app-settings |
| `application.b2c.scope` | Unknown | True | False | app-settings |
| `application.b2c.tenantId` | Unknown | True | False | app-settings |
| `application.ums-admin-id` | Unknown | True | False | app-settings |
| `application.ums-app-id` | Unknown | True | False | app-settings |
| `application.ums.scope` | Unknown | True | False | app-settings |
| `application.ums.tokenUrl` | Unknown | True | True | app-settings |
| `application.user.face-api-login-reminder-cron` | Unknown | Unknown | False | app-settings |
| `application.user.first-notification-reminder-days` | Unknown | True | False | app-settings |
| `application.user.max-face-login-days` | Unknown | True | False | app-settings |
| `application.user.max-passive-days` | Unknown | True | False | app-settings |
| `application.user.max-pending-active-days` | Unknown | True | False | app-settings |
| `application.user.max-unused-days` | Unknown | True | False | app-settings |
| `application.user.passive-and-pending-active-to-inactive-cron` | Unknown | Unknown | False | app-settings |
| `application.user.second-notification-reminder-days` | Unknown | True | False | app-settings |
| `azure.face-api.custom.url` | Unknown | True | False | app-settings |
| `azure.face.liveness.enableSessionImage` | Unknown | Unknown | False | app-settings |
| `azure.face.liveness.login.operationMode` | Unknown | True | False | app-settings |
| `azure.face.liveness.registration.operationMode` | Unknown | True | False | app-settings |
| `azure.face.liveness.session-ttl-minutes` | Unknown | Unknown | False | app-settings |
| `azure.faceApi.subscriptionKey` | Unknown | True | True | app-settings |
| `azure.faceApi.url` | Unknown | True | False | app-settings |
| `azure.servicebus.client-id` | Unknown | True | False | app-settings |
| `azure.servicebus.managed-identity-enabled` | Unknown | Unknown | False | app-settings |
| `azure.servicebus.namespace` | Unknown | True | False | app-settings |
| `azure.servicebus.topic-name` | Unknown | True | False | app-settings |
| `azure.storage.blob.connection-string` | Unknown | True | True | app-settings |
| `azure.storage.blob.container-name` | Unknown | True | False | app-settings |
| `azureBlob.preSigned-url.expiry-hours` | Unknown | True | False | app-settings |
| `azureBlob.publicDomain` | Unknown | True | False | app-settings |
| `b2c.password-policies` | Unknown | True | True | app-settings |
| `ekyc.consent-expiry` | Unknown | True | False | app-settings |
| `ekyc.consent-link` | Unknown | True | False | app-settings |
| `ekyc.namematch-threshold` | Unknown | True | False | app-settings |
| `employee-confirmation` | Unknown | True | False | app-settings |
| `face-confidence-threshold` | Unknown | True | False | app-settings |
| `karza.baseUrl` | Unknown | True | False | app-settings |
| `karza.key` | Unknown | True | True | app-settings |
| `location-master.baseUrl` | points to tvsm-auth | True | False | app-settings |
| `mdp.baseUrl` | points to master-data-platform | True | False | app-settings |
| `mdp.clientId` | Unknown | True | False | app-settings |
| `mdp.clientSecret` | Unknown | True | True | app-settings |
| `notification.apim-subscription-key` | Unknown | Unknown | True | app-settings |
| `notification.baseUrl` | points to notification-service | True | False | app-settings |
| `notification.consent-template` | Unknown | True | False | app-settings |
| `notification.face-api-login-reminder-template` | Unknown | True | False | app-settings |
| `pending-active-to-inactive-cron` | Unknown | Unknown | False | app-settings |
| `roles.filter-by-branch` | Unknown | True | False | app-settings |
| `security.basic.enabled` | Unknown | Unknown | False | app-settings |
| `sentry.dsn` | Unknown | Unknown | True | app-settings |
| `sentry.traces-sample-rate` | Unknown | Unknown | False | app-settings |
| `server.max-http-header-size` | Unknown | Unknown | False | app-settings |
| `server.port` | Unknown | Unknown | False | app-settings |
| `spring.datasource.driver-class-name` | Unknown | Unknown | False | app-settings |
| `spring.datasource.hikari.maximum-pool-size` | Unknown | Unknown | False | app-settings |
| `spring.datasource.hikari.minimum-idle` | Unknown | Unknown | False | app-settings |
| `spring.datasource.password` | Unknown | Unknown | True | app-settings |
| `spring.datasource.url` | Unknown | Unknown | False | app-settings |
| `spring.datasource.username` | Unknown | Unknown | False | app-settings |
| `spring.jpa.database-platform` | Unknown | Unknown | False | app-settings |
| `spring.jpa.show-sql` | Unknown | Unknown | False | app-settings |
| `spring.mvc.pathmatch.matching-strategy` | Unknown | Unknown | False | app-settings |
| `spring.profiles.active` | Unknown | True | False | app-settings |
| `spring.servlet.multipart.max-file-size` | Unknown | Unknown | False | app-settings |
| `spring.servlet.multipart.max-request-size` | Unknown | Unknown | False | app-settings |
| `user.onboard.authorities` | Unknown | True | False | app-settings |

## Ownership
tvsm-auth ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvsm-auth local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvsm-auth limitations evidenced by extraction:
- 17 outbound HTTP call(s) have no resolved target service (base URL from config/env).
