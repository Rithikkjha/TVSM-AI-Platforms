---
service_id: tvs-cps-job-card-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["jobcard service", "tvs cps job card service", "jobcards", "job card", "appointment analytic", "appointment analytics", "appointment analytics bff", "cps job card", "cps job card service", "job card invoice", "jobcard bff", "tvs cps job card", "jobcard", "job card service", "lead"]
---

# tvs-cps-job-card-service — Overview

## Purpose
Summary: CPS job card Spring Boot API for job card creation, updates, analytics and external job card access, publishing one message.
Also known as: jobcard service, tvs cps job card service, jobcards, job card, appointment analytic, appointment analytics, appointment analytics bff, cps job card, cps job card service, job card invoice, jobcard bff, tvs cps job card, jobcard, job card service, lead
tvs-cps-job-card-service is a `backend-api` repository (`TVS-CPS-JOB-CARD-SERVICE`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: jobcard-service — Order Service - A TVSM Spring Boot application that has an Order sample.

## Users and Consumers
tvs-cps-job-card-service is called over HTTP by: `tvs-cps-backend`. Event consumers of its published messages: none resolved.

## Key Capabilities
tvs-cps-job-card-service capabilities derived from code:
- `JobcardController`: 13 HTTP endpoint(s)
- `HealthController`: 1 HTTP endpoint(s)
- `JobCardAnalyticsController`: 1 HTTP endpoint(s)
- `ExternalJobcardController`: 1 HTTP endpoint(s)
- Publishes 1 messaging entit(y/ies); consumes 0

## Tech Stack
tvs-cps-job-card-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | postgres | Unknown |
| Messaging | kafka | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.tvsm:tvsm-be-core`, `com.tvsm:tvsm-be-starter-parent`, `org.apache.commons:commons-csv`, `org.apache.poi:poi`, `org.apache.poi:poi-ooxml`, `org.apache.xmlbeans:xmlbeans`, `org.mapstruct:mapstruct`, `org.mapstruct:mapstruct-processor`, `org.postgresql:postgresql`, `org.projectlombok:lombok`, `org.springdoc:springdoc-openapi-starter-webmvc-ui`, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-validation`, `org.springframework.boot:spring-boot-starter-web`, `org.springframework.kafka:spring-kafka`

## Dependencies at a Glance
Upstream (calls tvs-cps-job-card-service): `tvs-cps-backend`
Downstream (tvs-cps-job-card-service calls): none resolved; plus 1 outbound call(s) with unresolved target
Brokers: kafka. Data stores: `nmazcpsdbdev01-jobcard` (postgres, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvs-cps-job-card-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| training | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
tvs-cps-job-card-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `azure.eventhub.jobcard.hub-name` | Unknown | True | False | app-settings |
| `azure.kafka.bootstrap-servers` | Unknown | True | False | app-settings |
| `azure.kafka.properties.sasl.jaas.config` | Unknown | True | False | app-settings |
| `azure.kafka.properties.sasl.mechanism` | Unknown | Unknown | False | app-settings |
| `azure.kafka.properties.security.protocol` | Unknown | Unknown | False | app-settings |
| `customer.search-url` | Unknown | True | False | app-settings |
| `default.skip-path` | Unknown | Unknown | False | app-settings |
| `jobcard.external.allowed-tenant-ids` | Unknown | True | False | app-settings |
| `logging.level.com.tvsm.jobcard` | Unknown | Unknown | False | app-settings |
| `logging.level.org.hibernate.SQL` | Unknown | Unknown | False | app-settings |
| `logging.level.org.hibernate.type.descriptor.sql.BasicBinder` | Unknown | Unknown | False | app-settings |
| `logging.level.org.springframework.web` | Unknown | Unknown | False | app-settings |
| `management.endpoint.health.show-details` | Unknown | Unknown | False | app-settings |
| `management.endpoints.web.exposure.include` | Unknown | Unknown | False | app-settings |
| `request.validation.skip-api-path` | Unknown | Unknown | False | app-settings |
| `request.validation.skip-exact-words` | Unknown | Unknown | False | app-settings |
| `rolesWithSelfOnlyAccess` | Unknown | True | False | app-settings |
| `server.port` | Unknown | Unknown | False | app-settings |
| `server.servlet.context-path` | Unknown | Unknown | False | app-settings |
| `spring.application.name` | Unknown | Unknown | False | app-settings |
| `spring.autoconfigure.exclude[0]` | Unknown | Unknown | False | app-settings |
| `spring.cache.caffeine.spec` | Unknown | Unknown | True | app-settings |
| `spring.cache.type` | Unknown | Unknown | False | app-settings |
| `spring.jmx.enabled` | Unknown | Unknown | False | app-settings |
| `spring.jpa.database-platform` | Unknown | Unknown | False | app-settings |
| `spring.jpa.hibernate.ddl-auto` | Unknown | Unknown | False | app-settings |
| `spring.jpa.properties.hibernate.format_sql` | Unknown | Unknown | False | app-settings |
| `spring.jpa.show-sql` | Unknown | Unknown | False | app-settings |
| `springdoc.api-docs.path` | Unknown | Unknown | False | app-settings |
| `springdoc.info.description` | Unknown | Unknown | False | app-settings |
| `springdoc.info.title` | Unknown | Unknown | False | app-settings |
| `springdoc.info.version` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.path` | Unknown | Unknown | False | app-settings |
| `tvsm.core.logging.methodLevel.enabled` | Unknown | Unknown | False | app-settings |
| `tvsm.core.logging.performance.enabled` | Unknown | Unknown | False | app-settings |
| `tvsm.core.logging.performance.thresholdMs` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.maximum-pool-size` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.minimum-idle` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.password` | Unknown | Unknown | True | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.url` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.username` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[0]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[1]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[2]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[3]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.jwt.publicKey.key1` | Unknown | Unknown | True | app-settings |
| `validation.files` | Unknown | Unknown | False | app-settings |

## Ownership
tvs-cps-job-card-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvs-cps-job-card-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvs-cps-job-card-service limitations evidenced by extraction:
- 1 outbound HTTP call(s) have no resolved target service (base URL from config/env).
