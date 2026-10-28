---
service_id: notification-dispatcher-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["notification dispatcher service", "tvsm notification dispatcher", "notification dispatcher"]
---

# notification-dispatcher-service — Overview

## Purpose
Summary: Spring Boot dispatcher consuming a notifications messaging entity and sending push (Firebase), email and SMS via providers, with a Salesforce token refresh endpoint.
Also known as: notification dispatcher service, tvsm notification dispatcher, notification dispatcher
notification-dispatcher-service is a `backend-api` repository (`notification-dispatcher-service`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: README #.

## Users and Consumers
notification-dispatcher-service is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
notification-dispatcher-service capabilities derived from code:
- `HealthCheckController`: 1 HTTP endpoint(s)
- `PushNotificationController`: 1 HTTP endpoint(s)
- `SalesforceTokenController`: 1 HTTP endpoint(s)
- Scheduled job `ThreadPoolMonitor.logThreadPoolStats` (fixed-rate `60000`)
- Consumes 1 messaging entit(y/ies)

## Tech Stack
notification-dispatcher-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | mongo | Unknown |
| Messaging | azure-service-bus | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.azure:azure-messaging-servicebus`, `com.fasterxml.jackson.core:jackson-core`, `com.fasterxml.jackson.core:jackson-databind`, `com.github.ben-manes.caffeine:caffeine`, `com.google.firebase:firebase-admin`, `io.github.classgraph:classgraph`, `io.micrometer:micrometer-observation`, `io.sentry:sentry-logback`, `io.sentry:sentry-spring-boot-starter`, `io.springfox:springfox-boot-starter`, `net.bytebuddy:byte-buddy`, `org.apache.tomcat.embed:tomcat-embed-core`, `org.mockito:mockito-core`, `org.projectlombok:lombok`, `org.springframework.boot:spring-boot-configuration-processor`, `org.springframework.boot:spring-boot-starter-cache`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-data-mongodb`, `org.springframework.boot:spring-boot-starter-parent`, `org.springframework.boot:spring-boot-starter-validation`, `org.springframework.boot:spring-boot-starter-webflux`, `org.springframework.retry:spring-retry`, `org.springframework:spring-aspects`, `org.springframework:spring-webmvc`

## Dependencies at a Glance
Upstream (calls notification-dispatcher-service): Unknown
Downstream (notification-dispatcher-service calls): `external:firebase` (None), `external:salesforce` (hard); plus 5 outbound call(s) with unresolved target
Brokers: azure-service-bus. Data stores: `config:spring.data.mongodb.host` (mongo, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
notification-dispatcher-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| local | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| training | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
notification-dispatcher-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `SENTRY_AUTH_TOKEN` | Unknown | Unknown | True | app-settings |
| `TZ` | Unknown | Unknown | False | Unknown |
| `firebase.client.email` | Unknown | True | True | app-settings |
| `firebase.private.key` | Unknown | True | True | app-settings |
| `firebase.private.key.id` | Unknown | True | True | app-settings |
| `firebase.project.id` | Unknown | True | False | app-settings |
| `infobip.appAuth` | Unknown | True | False | app-settings |
| `infobip.baseUri` | Unknown | True | False | app-settings |
| `infobip.email.promotional.domain` | Unknown | True | False | app-settings |
| `infobip.email.transactional.domain` | Unknown | True | False | app-settings |
| `infobip.otpAppAuth` | Unknown | True | False | app-settings |
| `infobip.sendOtpSMSBaseUrl` | Unknown | True | False | app-settings |
| `notification.infobip.retry.url` | Unknown | True | False | app-settings |
| `notification.sendInfobipNotification.value` | Unknown | Unknown | False | app-settings |
| `notification.sendSalesforceNotification.value` | Unknown | Unknown | False | app-settings |
| `notification.service.status-update.api` | Unknown | True | False | app-settings |
| `notification.serviceBus.enabled` | Unknown | Unknown | False | app-settings |
| `salesforce.api.authUrl` | Unknown | True | False | app-settings |
| `salesforce.api.sendSMS.url` | Unknown | True | False | app-settings |
| `salesforce.auth.clientId` | Unknown | True | False | app-settings |
| `salesforce.auth.clientSecret` | Unknown | True | True | app-settings |
| `salesforce.auth.grantType` | Unknown | True | False | app-settings |
| `sentry.dsn` | Unknown | Unknown | False | app-settings |
| `sentry.send-default-pii` | Unknown | Unknown | False | app-settings |
| `sentry.traces-sample-rate` | Unknown | Unknown | False | app-settings |
| `sms.principalEntityId.value` | Unknown | True | False | app-settings |
| `spring.data.mongodb.database` | Unknown | Unknown | False | app-settings |
| `spring.data.mongodb.host` | Unknown | Unknown | False | app-settings |
| `spring.data.mongodb.port` | Unknown | Unknown | False | app-settings |
| `spring.data.mongodb.uri` | Unknown | Unknown | False | app-settings |
| `spring.jms.servicebus.connection-string` | Unknown | True | True | app-settings |
| `spring.jms.servicebus.idle-timeout` | Unknown | Unknown | False | app-settings |
| `spring.jms.servicebus.subscription.email` | Unknown | True | False | app-settings |
| `spring.jms.servicebus.subscription.fcmpush` | Unknown | True | False | app-settings |
| `spring.jms.servicebus.subscription.highpriority` | Unknown | True | False | app-settings |
| `spring.jms.servicebus.subscription.sms` | Unknown | True | False | app-settings |
| `spring.jms.servicebus.subscription.whatsapp` | Unknown | True | False | app-settings |
| `spring.jms.servicebus.topic.notifications` | Unknown | True | False | app-settings |
| `spring.mvc.pathmatch.matching-strategy` | Unknown | Unknown | False | app-settings |
| `spring.profiles.active` | Unknown | True | False | app-settings |
| `whatsapp.smsfailover.sendsms` | Unknown | True | False | app-settings |

## Ownership
notification-dispatcher-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
notification-dispatcher-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
notification-dispatcher-service limitations evidenced by extraction:
- 5 outbound HTTP call(s) have no resolved target service (base URL from config/env).
- No inbound callers resolved in the registry.
