---
service_id: tvsmbe-location
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["location master", "tvsmbe location", "dealer locater", "admin ib", "dealer", "dealerweb", "dealer detail", "dealer details", "admin dealer", "dealer flow dealer detail", "dealer flow dealer details", "location tvsmbe", "location"]
---

# tvsmbe-location — Overview

## Purpose
Summary: Spring Boot location-master service for dealer locations: admin and dealer flows, IB and domestic dealers, geocoding and dealer search, calling MDP, auth, OTP and notification services.
Also known as: location master, tvsmbe location, dealer locater, admin ib, dealer, dealerweb, dealer detail, dealer details, admin dealer, dealer flow dealer detail, dealer flow dealer details, location tvsmbe, location
tvsmbe-location is a `backend-api` repository (`tvsmbe-location`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: README # — Location-master.

## Users and Consumers
tvsmbe-location is called over HTTP by: `location-frontend`. Event consumers of its published messages: none resolved.

## Key Capabilities
tvsmbe-location capabilities derived from code:
- `AdminFlowController`: 7 HTTP endpoint(s)
- `UserXController`: 6 HTTP endpoint(s)
- `IBDealerController`: 6 HTTP endpoint(s)
- `DomesticDealerController`: 6 HTTP endpoint(s)
- `TestController`: 4 HTTP endpoint(s)
- `DealerFlowController`: 3 HTTP endpoint(s)
- `CountryController`: 2 HTTP endpoint(s)
- `LocationController`: 2 HTTP endpoint(s)
- `MobileFlowController`: 2 HTTP endpoint(s)
- `MigrationController`: 2 HTTP endpoint(s)
- `GeoCodeController`: 1 HTTP endpoint(s)
- `LocationMasterController`: 1 HTTP endpoint(s)
- `ChargingStationController`: 1 HTTP endpoint(s)
- `DealershipLocationController`: 1 HTTP endpoint(s)
- `DealerProximityController`: 1 HTTP endpoint(s)
- Scheduled job `CronService.logMetricsPeriodically` (fixed-rate `60000`)

## Tech Stack
tvsmbe-location tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | mongo, mysql | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.azure:azure-storage-blob`, `com.fasterxml.jackson.datatype:jackson-datatype-joda`, `com.google.code.gson:gson`, `com.google.guava:guava`, `com.opencsv:opencsv`, `com.squareup.okhttp3:okhttp`, `commons-io:commons-io`, `io.sentry:sentry-logback`, `io.sentry:sentry-spring-boot-starter`, `org.apache.poi:poi-ooxml`, `org.jadira.usertype:usertype.core`, `org.projectlombok:lombok`, `org.springdoc:springdoc-openapi-ui`, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-aop`, `org.springframework.boot:spring-boot-starter-cache`, `org.springframework.boot:spring-boot-starter-data-mongodb`, `org.springframework.boot:spring-boot-starter-parent`, `org.springframework.boot:spring-boot-starter-security`, `org.springframework.boot:spring-boot-starter-web`, `org.springframework.retry:spring-retry`, `us.fatehi:pointlocation6709`

## Dependencies at a Glance
Upstream (calls tvsmbe-location): `location-frontend`
Downstream (tvsmbe-location calls): `master-data-platform` (hard), `notification-service` (hard), `tvsm-auth` (hard), `tvsm-otp-service` (hard); plus 3 outbound call(s) with unresolved target
Brokers: none. Data stores: `config:spring.data.mongodb.uri` (mongo, read-write), `_` (mysql, write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvsmbe-location environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| UAT | Unknown | from config/infra file names |
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| local | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
tvsmbe-location configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `ACTIVE_ENVIRONMENT` | Unknown | Unknown | False | env-file |
| `AZUREBLOB_PUBLIC_DOMAIN` | Unknown | Unknown | False | env-file |
| `AZUREBLOB_SAS_PRESIGNED_URL_EXPIRY_HOURS` | Unknown | Unknown | True | env-file |
| `BETA_RELEASE_ENABLED` | Unknown | Unknown | False | env-file |
| `BETA_RELEASE_SAP_DEALER_CODES` | Unknown | Unknown | False | env-file |
| `GOOGLE_MAPS_GEOCODE_API_KEY` | Unknown | Unknown | True | env-file |
| `IB_DEALER_TEMPLATE_FILE_PATH` | Unknown | Unknown | False | env-file |
| `IMAGE_CAPTURED_LOCATION_ACCURACY_THRESHOLD_IN_METERS` | Unknown | True | False | env-file |
| `KAZAM_BASE_URL` | Unknown | True | False | env-file |
| `KAZAM_NAMESPACE` | Unknown | True | False | env-file |
| `KAZAM_PASSWORD` | Unknown | True | True | env-file |
| `LOCATION_MASTER_AZUREBLOB_CONNECTION_STRING` | Unknown | Unknown | True | env-file |
| `LOCATION_UPDATE_SECRET_EXPIRY_DAYS` | Unknown | Unknown | True | env-file |
| `MDP_BASE_URL` | points to master-data-platform | True | False | env-file |
| `MDP_CLIENT_ID` | Unknown | Unknown | False | env-file |
| `MDP_CLIENT_SECRET` | Unknown | Unknown | True | env-file |
| `MONGODB_URI` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_APIM_SUBSCRIPTION_KEY` | Unknown | Unknown | True | env-file |
| `NOTIFICATION_BASE_URL` | points to notification-service | True | False | env-file |
| `NOTIFICATION_CLIENT_ID` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_CLIENT_SECRET` | Unknown | Unknown | True | env-file |
| `NOTIFICATION_KEY_LOCATION_UPDATE` | Unknown | Unknown | True | env-file |
| `NOTIFICATION_SCOPE` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_TEMPLATE_LOCATION_UPDATE` | Unknown | Unknown | False | env-file |
| `NOTIFICATION_TOKEN_URL` | Unknown | Unknown | True | env-file |
| `PRIVACY_POLICY_FILE` | Unknown | Unknown | False | env-file |
| `SENTRY_AUTH_TOKEN` | Unknown | Unknown | True | app-settings |
| `SHOW_HTTP_500_DETAILS` | Unknown | Unknown | False | env-file |
| `SUBMITTED_LOCATION_ACCURACY_THRESHOLD_IN_METERS` | Unknown | True | False | env-file |
| `TERMS_AND_CONDITION_FILE` | Unknown | Unknown | False | env-file |
| `TZ` | Unknown | Unknown | False | Unknown |
| `UMS_BASE_URL` | points to tvsm-auth | True | False | env-file |
| `UMS_CLIENT_ID` | Unknown | Unknown | False | env-file |
| `UMS_CLIENT_SECRET` | Unknown | Unknown | True | env-file |
| `UMS_SCOPE` | Unknown | Unknown | False | env-file |
| `UMS_TOKEN_URL` | Unknown | Unknown | True | env-file |
| `WEBSITES_ENABLE_APP_SERVICE_STORAGE` | Unknown | Unknown | False | env-file |
| `WEBSITE_HTTPLOGGING_RETENTION_DAYS` | Unknown | Unknown | False | env-file |
| `azureBlob.connection-string` | Unknown | True | True | app-settings |
| `azureBlob.dealer-location-photo-container.name` | Unknown | True | False | app-settings |
| `azureBlob.presigned-url.expiry-hours` | Unknown | True | False | app-settings |
| `azureBlob.publicDomain` | Unknown | True | False | app-settings |
| `b2c.notification.apim-subscription-key` | Unknown | True | True | app-settings |
| `b2c.notification.client.id` | Unknown | True | False | app-settings |
| `b2c.notification.client.secret` | Unknown | True | True | app-settings |
| `b2c.notification.scope` | Unknown | True | False | app-settings |
| `b2c.notification.token.url` | Unknown | True | True | app-settings |
| `b2c.ums.client.id` | Unknown | True | False | app-settings |
| `b2c.ums.client.secret` | Unknown | True | True | app-settings |
| `b2c.ums.scope` | Unknown | True | False | app-settings |
| `b2c.ums.token.url` | Unknown | True | True | app-settings |
| `beta-release-enabled` | Unknown | True | False | app-settings |
| `beta-release-sapDealerCodes` | Unknown | True | False | app-settings |
| `google-maps.geocode.api-key` | Unknown | True | True | app-settings |
| `ib.dealer.template-file.path` | Unknown | True | False | app-settings |
| `lms.api.client.id` | Unknown | True | False | app-settings |
| `lms.apim-subscription-key` | Unknown | True | True | app-settings |
| `lms.base.url` | Unknown | True | False | app-settings |
| `lms.client.id` | Unknown | True | False | app-settings |
| `lms.client.secret` | Unknown | True | True | app-settings |
| `lms.scope` | Unknown | True | False | app-settings |
| `lms.secret.key` | Unknown | True | True | app-settings |
| `lms.token.url` | Unknown | True | True | app-settings |
| `location-update-secret-expiry-days` | Unknown | True | True | app-settings |
| `logging.level.root` | Unknown | Unknown | False | app-settings |
| `notification.dealer-locator-sms-template` | Unknown | True | False | app-settings |
| `notification.location-update-sms-key` | Unknown | True | True | app-settings |
| `notification.location-update-sms-template` | Unknown | True | False | app-settings |
| `notification.otp-sms-template` | Unknown | True | False | app-settings |
| `otp.service.base.url` | points to tvsm-otp-service | True | False | app-settings |
| `privacy-policy-file` | Unknown | True | False | app-settings |
| `sentry.dsn` | Unknown | Unknown | False | app-settings |
| `sentry.maxRequestBodySize` | Unknown | Unknown | False | app-settings |
| `sentry.sendDefaultPii` | Unknown | Unknown | False | app-settings |
| `sentry.traces-sample-rate` | Unknown | Unknown | False | app-settings |
| `server.error.whitelabel.enabled` | Unknown | Unknown | False | app-settings |
| `server.port` | Unknown | Unknown | False | app-settings |
| `server.servlet.context-path` | Unknown | Unknown | False | app-settings |
| `server.tomcat.accesslog.directory` | Unknown | Unknown | False | app-settings |
| `server.tomcat.accesslog.enabled` | Unknown | Unknown | False | app-settings |
| `show.http_500_error_details` | Unknown | True | False | app-settings |
| `spring.application.name` | Unknown | Unknown | False | app-settings |
| `spring.data.mongodb.uri` | Unknown | Unknown | False | app-settings |
| `spring.output.ansi.enabled` | Unknown | Unknown | False | app-settings |
| `spring.profiles.active` | Unknown | True | False | app-settings |
| `spring.servlet.multipart.enabled` | Unknown | Unknown | False | app-settings |
| `spring.servlet.multipart.max-file-size` | Unknown | Unknown | False | app-settings |
| `spring.servlet.multipart.max-request-size` | Unknown | Unknown | False | app-settings |
| `springdoc.api-docs.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.show-actuator` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.path` | Unknown | Unknown | False | app-settings |
| `terms-and-condition-file` | Unknown | True | False | app-settings |

## Ownership
tvsmbe-location ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvsmbe-location local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvsmbe-location limitations evidenced by extraction:
- 3 outbound HTTP call(s) have no resolved target service (base URL from config/env).
