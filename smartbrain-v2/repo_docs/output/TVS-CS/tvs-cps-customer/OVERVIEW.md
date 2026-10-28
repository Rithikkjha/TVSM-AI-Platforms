---
service_id: tvs-cps-customer
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["customer", "tvs cps customer", "customer service", "customer vehicle", "cps customer"]
---

# tvs-cps-customer — Overview

## Purpose
Summary: CPS customer Spring Boot API for creating, updating, searching customers, external customer operations and vehicle search; no README purpose.
Also known as: customer, tvs cps customer, customer service, customer vehicle, cps customer
tvs-cps-customer is a `backend-api` repository (`TVS-CPS-CUSTOMER`; service.yaml `type: backend-api`). Business purpose: Unknown — not stated in README/code.

## Users and Consumers
tvs-cps-customer is called over HTTP by: `tvs-cps-backend`. Event consumers of its published messages: none resolved.

## Key Capabilities
tvs-cps-customer capabilities derived from code:
- `CustomerController`: 5 HTTP endpoint(s)
- `ExternalCustomerController`: 3 HTTP endpoint(s)
- `VehicleSearchController`: 1 HTTP endpoint(s)

## Tech Stack
tvs-cps-customer tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | postgres | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.tvsm:tvsm-be-core`, `com.tvsm:tvsm-be-starter-parent`, `org.mapstruct:mapstruct`, `org.mapstruct:mapstruct-processor`, `org.postgresql:postgresql`, `org.projectlombok:lombok`, `org.springdoc:springdoc-openapi-starter-webmvc-ui`, `org.springframework.boot:spring-boot-starter`, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-web`

## Dependencies at a Glance
Upstream (calls tvs-cps-customer): `tvs-cps-backend`
Downstream (tvs-cps-customer calls): none resolved
Brokers: none. Data stores: `customer` (postgres, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvs-cps-customer environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| training | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
tvs-cps-customer configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `app.rest.timeout.connect` | Unknown | Unknown | False | Unknown |
| `app.rest.timeout.read` | Unknown | Unknown | False | Unknown |
| `default.skip-path` | Unknown | Unknown | False | app-settings |
| `default.tenant-id` | Unknown | True | False | app-settings |
| `logging.level.com.tvsm.core` | Unknown | Unknown | False | app-settings |
| `logging.level.com.tvsm.customer` | Unknown | Unknown | False | app-settings |
| `logging.pattern.console` | Unknown | Unknown | False | app-settings |
| `logging.pattern.file` | Unknown | Unknown | False | app-settings |
| `management.endpoint.health.show-details` | Unknown | Unknown | False | app-settings |
| `management.endpoints.web.exposure.include` | Unknown | Unknown | False | app-settings |
| `request.validation.skip-api-path` | Unknown | Unknown | False | app-settings |
| `request.validation.skip-exact-words` | Unknown | Unknown | False | app-settings |
| `server.port` | Unknown | Unknown | False | app-settings |
| `spring.application.name` | Unknown | Unknown | False | app-settings |
| `spring.autoconfigure.exclude[0]` | Unknown | Unknown | False | app-settings |
| `spring.flyway.enabled` | Unknown | Unknown | False | app-settings |
| `spring.jpa.hibernate.ddl-auto` | Unknown | Unknown | False | app-settings |
| `spring.jpa.properties.hibernate.dialect` | Unknown | Unknown | False | app-settings |
| `spring.jpa.properties.hibernate.format_sql` | Unknown | Unknown | False | app-settings |
| `spring.jpa.show-sql` | Unknown | Unknown | False | app-settings |
| `springdoc.api-docs.path` | Unknown | Unknown | False | app-settings |
| `springdoc.info.description` | Unknown | Unknown | False | app-settings |
| `springdoc.info.title` | Unknown | Unknown | False | app-settings |
| `springdoc.info.version` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.enabled` | Unknown | Unknown | False | app-settings |
| `springdoc.swagger-ui.path` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.maximum-pool-size` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.minimum-idle` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.password` | Unknown | Unknown | True | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.url` | Unknown | Unknown | False | app-settings |
| `tvsm.core.multitenant.datasource.default-data-source.username` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[0]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[1]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[2]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[3]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[4]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[5]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[6]` | Unknown | Unknown | False | app-settings |
| `validation.files` | Unknown | Unknown | False | app-settings |

## Ownership
tvs-cps-customer ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvs-cps-customer local setup evidence:
- README: none
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvs-cps-customer limitations evidenced by extraction:
- N/A — none evidenced in code
