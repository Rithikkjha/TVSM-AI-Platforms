---
service_id: tvs-cps-be-base-framework
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["tvs cps be base framework", "tvsm be starter parent", "orders", "tvsm be archetype", "tvsm be wiremock", "be archetype", "be starter parent", "be wiremock", "cps be base framework", "order"]
---

# tvs-cps-be-base-framework — Overview

## Purpose
Summary: Spring Boot 3.5 / Java 21 base framework, archetype and starter parent providing shared components for TVSM backend applications.
Also known as: tvs cps be base framework, tvsm be starter parent, orders, tvsm be archetype, tvsm be wiremock, be archetype, be starter parent, be wiremock, cps be base framework, order
tvs-cps-be-base-framework is a `library` repository (`TVS-CPS-BE-BASE-FRAMEWORK`; service.yaml `type: library`). Business purpose: README (`README.md`) describes it as: TVSM Base Framework — A comprehensive Spring Boot 3.5.4 base framework built on Java 21, providing enterprise-ready components and architectural foundations for TVSM backend applications..
It contains 5 subprojects: `.` (unknown), `tvsm-be-archetype` (library), `tvsm-be-archetype/src/main/resources/archetype-resources` (service), `tvsm-be-core` (library), `tvsm-be-wiremock` (library).

## Users and Consumers
tvs-cps-be-base-framework is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
tvs-cps-be-base-framework capabilities derived from code:
- `OrderController`: 2 HTTP endpoint(s)
- `HealthController`: 1 HTTP endpoint(s)
- Publishes 1 messaging entit(y/ies); consumes 0

## Tech Stack
tvs-cps-be-base-framework tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | postgres | Unknown |
| Messaging | kafka | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.azure.spring:spring-cloud-azure-starter-storage-blob`, `com.fasterxml.jackson:jackson-bom`, `com.tvsm:tvsm-be-starter-parent`, `commons-fileupload:commons-fileupload`, `commons-io:commons-io`, `commons-validator:commons-validator`, `io.netty:netty-bom`, `net.minidev:accessors-smart`, `net.minidev:json-smart`, `org.apache.commons:commons-lang3`, `org.apache.kafka:kafka-clients`, `org.apache.tomcat.embed:tomcat-embed-core`, `org.apache.tomcat.embed:tomcat-embed-el`, `org.apache.tomcat.embed:tomcat-embed-websocket`, `org.apache.tomcat:tomcat-annotations-api`, `org.aspectj:aspectjweaver`, `org.mapstruct:mapstruct`, `org.mapstruct:mapstruct-processor`, `org.postgresql:postgresql`, `org.projectlombok:lombok`, `org.slf4j:slf4j-api`, `org.springdoc:springdoc-openapi-starter-webmvc-ui`, `org.springframework.boot:spring-boot-configuration-processor`, `org.springframework.boot:spring-boot-dependencies`, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-aop`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-validation`, `org.springframework.boot:spring-boot-starter-web`, `org.springframework.boot:spring-boot-starter-webflux` …

## Dependencies at a Glance
Upstream (calls tvs-cps-be-base-framework): Unknown
Downstream (tvs-cps-be-base-framework calls): none resolved; plus 1 outbound call(s) with unresolved target
Brokers: kafka. Data stores: `order_db` (postgres, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvs-cps-be-base-framework environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |

## Environment Variables
tvs-cps-be-base-framework configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `MAVEN_HOME` | Unknown | Unknown | False | Unknown |
| `PATH` | Unknown | Unknown | False | Unknown |
| `default.skip-path` | Unknown | True | False | Unknown |
| `logging.level.${package}` | Unknown | Unknown | False | app-settings |
| `logging.level.com.zaxxer.hikari` | Unknown | Unknown | False | app-settings |
| `logging.level.org.apache` | Unknown | Unknown | False | app-settings |
| `logging.level.org.hibernate.SQL` | Unknown | Unknown | False | app-settings |
| `logging.level.org.hibernate.type.descriptor.sql.BasicBinder` | Unknown | Unknown | False | app-settings |
| `logging.level.org.springframework` | Unknown | Unknown | False | app-settings |
| `logging.level.org.springframework.web` | Unknown | Unknown | False | app-settings |
| `logging.pattern.console` | Unknown | Unknown | False | app-settings |
| `management.endpoint.health.show-details` | Unknown | Unknown | False | app-settings |
| `management.endpoints.web.exposure.include` | Unknown | Unknown | False | app-settings |
| `rbac.config` | Unknown | True | False | Unknown |
| `rbac.configEnabled` | Unknown | True | False | Unknown |
| `rbac.defaultUnmappedApiBehavior` | Unknown | True | False | Unknown |
| `rbac.enabled` | Unknown | True | False | Unknown |
| `request.validation.skip-api-path` | Unknown | True | False | Unknown |
| `request.validation.skip-exact-words` | Unknown | True | False | Unknown |
| `server.port` | Unknown | Unknown | False | app-settings |
| `server.servlet.context-path` | Unknown | Unknown | False | app-settings |
| `spring.application.name` | Unknown | Unknown | False | app-settings |
| `spring.autoconfigure.exclude[0]` | Unknown | Unknown | False | app-settings |
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
| `tvsm.core.cloud-storage.azure` | Unknown | True | False | Unknown |
| `tvsm.core.cloud-storage.azure.connection-string` | Unknown | Unknown | True | app-settings |
| `tvsm.core.cloud-storage.azure.container-name` | Unknown | Unknown | False | app-settings |
| `tvsm.core.cloud-storage.enabled` | Unknown | Unknown | False | app-settings |
| `tvsm.core.cloud-storage.enabled` | Unknown | True | False | Unknown |
| `tvsm.core.cloud-storage.provider` | Unknown | Unknown | False | app-settings |
| `tvsm.core.cloud-storage.provider` | Unknown | True | False | Unknown |
| `tvsm.core.logging.methodLevel.enabled` | Unknown | Unknown | False | app-settings |
| `tvsm.core.logging.performance.enabled` | Unknown | Unknown | False | app-settings |
| `tvsm.core.logging.performance.thresholdMs` | Unknown | Unknown | False | app-settings |
| `tvsm.core.logging.performance.thresholdMs` | Unknown | Unknown | False | Unknown |
| `tvsm.core.multitenant.datasource.default-data-source.maximum-pool-size` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.minimum-idle` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.password` | Unknown | Unknown | True | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.url` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.username` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.defaultDataSource` | Unknown | True | False | Unknown |
| `tvsm.core.multitenant.datasource.tenants` | Unknown | True | False | Unknown |
| `tvsm.core.security.defaultTenant` | Unknown | True | False | Unknown |
| `tvsm.core.security.defaultTenantEnabled` | Unknown | True | False | Unknown |
| `tvsm.core.security.excludedPaths` | Unknown | True | False | Unknown |
| `tvsm.core.security.excludedPaths[0]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[1]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[2]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.isHeaderXTenantIDOptional` | Unknown | True | False | Unknown |
| `tvsm.core.security.jwt.publicKey.key1` | Unknown | Unknown | True | app-settings |
| `tvsm.kafka.consumer` | Unknown | True | False | Unknown |
| `tvsm.kafka.producer.enabled` | Unknown | True | False | Unknown |
| `tvsm.kafka.producer.syncTimeoutMs` | Unknown | True | False | Unknown |
| `tvsm.kafka.publisher` | Unknown | True | False | Unknown |
| `validation.files` | Unknown | True | False | Unknown |
| `wiremock.host` | Unknown | Unknown | False | app-settings |
| `wiremock.port` | Unknown | Unknown | False | app-settings |
| `wiremock.settings.enabled` | Unknown | Unknown | False | app-settings |
| `wiremock.settings.timeout` | Unknown | Unknown | False | app-settings |

## Ownership
tvs-cps-be-base-framework ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvs-cps-be-base-framework local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvs-cps-be-base-framework limitations evidenced by extraction:
- 1 outbound HTTP call(s) have no resolved target service (base URL from config/env).
- 1 messaging entit(y/ies) whose topic/queue name is not resolvable from code.
- No inbound callers resolved in the registry.
