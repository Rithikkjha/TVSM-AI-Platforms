---
service_id: notification-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["tvsm notification", "notification service", "notification", "notification sms dispatcher", "notification sender"]
---

# notification-service — Overview

## Purpose
Summary: TVS Motor Notification Service handling SMS, email and WhatsApp notifications via Infobip and Salesforce, with templates, user and retry preferences.
Also known as: tvsm notification, notification service, notification, notification sms dispatcher, notification sender
notification-service is a `backend-api` repository (`notification-service`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: Notification Service — TVS Motor Notification Service for handling SMS, Email, and WhatsApp notifications via multiple service providers (Infobip, Salesforce)..

## Users and Consumers
notification-service is called over HTTP by: `master-data-platform`, `tvs-cps-backend`, `tvsm-auth`, `tvsm-marketplace-service`, `tvsmbe-location`, `tvsmbe-mdp-bff`. Event consumers of its published messages: `notification-dispatcher-service`.

## Key Capabilities
notification-service capabilities derived from code:
- `NotificationUserPreferenceController`: 6 HTTP endpoint(s)
- `NotificationController`: 6 HTTP endpoint(s)
- `NotificationRetryPreferenceController`: 5 HTTP endpoint(s)
- `NotificationTemplateController`: 4 HTTP endpoint(s)
- `HealthCheckController`: 1 HTTP endpoint(s)
- `InfobipAPIErrorRetryController`: 1 HTTP endpoint(s)
- `InfobipCallbackController`: 1 HTTP endpoint(s)
- Scheduled job `QueueToTopicService.processQueueMessages` (fixed-rate `7200000`)
- Publishes 3 messaging entit(y/ies); consumes 1

## Tech Stack
notification-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | mongo | Unknown |
| Messaging | azure-service-bus | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.azure:azure-messaging-servicebus`, `com.azure:azure-storage-blob`, `com.azure:azure-storage-queue`, `com.fasterxml.jackson.core:jackson-core`, `com.github.ben-manes.caffeine:caffeine`, `io.micrometer:micrometer-observation`, `io.netty:netty-codec-http2`, `io.sentry:sentry-logback`, `jakarta.annotation:jakarta.annotation-api`, `net.bytebuddy:byte-buddy`, `org.apache.qpid:proton-j`, `org.apache.tomcat.embed:tomcat-embed-core`, `org.apache.tomcat.embed:tomcat-embed-websocket`, `org.mockito:mockito-core`, `org.projectlombok:lombok`, `org.springdoc:springdoc-openapi-ui`, `org.springframework.boot:spring-boot-configuration-processor`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-data-mongodb`, `org.springframework.boot:spring-boot-starter-parent`, `org.springframework.boot:spring-boot-starter-validation`, `org.springframework.boot:spring-boot-starter-webflux`, `org.springframework:spring-expression`, `org.yaml:snakeyaml`

## Dependencies at a Glance
Upstream (calls notification-service): `master-data-platform`, `tvs-cps-backend`, `tvsm-auth`, `tvsm-marketplace-service`, `tvsmbe-location`, `tvsmbe-mdp-bff`
Downstream (notification-service calls): `external:salesforce` (hard)
Brokers: azure-service-bus. Data stores: `config:spring.data.mongodb.host` (mongo, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
notification-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| local | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| training | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
notification-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `SENTRY_AUTH_TOKEN` | Unknown | Unknown | True | app-settings |
| `TZ` | Unknown | Unknown | False | Unknown |
| `logging.level.org.springframework` | Unknown | Unknown | False | app-settings |
| `salesforce.blob.batchSize` | Unknown | True | False | Unknown |
| `salesforce.blob.fileName` | Unknown | True | False | Unknown |
| `salesforce.blob.sasUrl` | Unknown | True | True | Unknown |
| `sentry.dsn` | Unknown | Unknown | False | app-settings |
| `sentry.send-default-pii` | Unknown | Unknown | False | app-settings |
| `sentry.traces-sample-rate` | Unknown | Unknown | False | app-settings |
| `spring.data.mongodb.database` | Unknown | Unknown | False | app-settings |
| `spring.data.mongodb.host` | Unknown | Unknown | False | app-settings |
| `spring.data.mongodb.port` | Unknown | Unknown | False | app-settings |
| `spring.data.mongodb.uri` | Unknown | Unknown | False | app-settings |
| `spring.jms.servicebus.client-expiry-time-in-minutes` | Unknown | True | False | app-settings |
| `spring.jms.servicebus.connection-string` | Unknown | True | True | app-settings |
| `spring.jms.servicebus.connection-string.queue.notification-noreturn-nook` | Unknown | True | True | app-settings |
| `spring.jms.servicebus.connection-string.queue.notification-revive` | Unknown | True | True | app-settings |
| `spring.jms.servicebus.connection-string.queue.notification-revive-every-2-hours` | Unknown | True | True | app-settings |
| `spring.jms.servicebus.connection-string.status-update-topic` | Unknown | True | True | app-settings |
| `spring.jms.servicebus.idle-timeout` | Unknown | Unknown | False | app-settings |
| `spring.jms.servicebus.queue.notification-noreturn-nook` | Unknown | True | False | app-settings |
| `spring.jms.servicebus.queue.notification-revive` | Unknown | True | False | app-settings |
| `spring.jms.servicebus.queue.notification-revive-every-2-hours` | Unknown | True | False | app-settings |
| `spring.jms.servicebus.topic.notifications` | Unknown | True | False | app-settings |
| `spring.jms.servicebus.topic.notifications.status-update` | Unknown | True | False | app-settings |
| `spring.mvc.pathmatch.matching-strategy` | Unknown | Unknown | False | app-settings |
| `spring.profiles.active` | Unknown | True | False | app-settings |
| `springdoc.api-docs.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.path` | Unknown | Unknown | False | app-settings |

## Ownership
notification-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
notification-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
notification-service limitations evidenced by extraction:
- 2 messaging entit(y/ies) whose topic/queue name is not resolvable from code.
