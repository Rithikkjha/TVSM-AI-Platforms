---
service_id: tvs-cps-inventory
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["inventory service", "tvs cps inventory", "inventory", "cps inventory"]
---

# tvs-cps-inventory — Overview

## Purpose
Summary: CPS inventory Spring Boot API managing vehicle inventory, bins, racks, locations, stock issue/receive and inspections; README is the base-framework sample text.
Also known as: inventory service, tvs cps inventory, inventory, cps inventory
tvs-cps-inventory is a `backend-api` repository (`TVS-CPS-INVENTORY`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: inventory-service — Order Service - A TVSM Spring Boot application that has an Order sample.

## Users and Consumers
tvs-cps-inventory is called over HTTP by: `tvs-cps-backend`. Event consumers of its published messages: none resolved.

## Key Capabilities
tvs-cps-inventory capabilities derived from code:
- `VehicleController`: 8 HTTP endpoint(s)
- `InventoryController`: 5 HTTP endpoint(s)
- `ExternalVehicleController`: 2 HTTP endpoint(s)
- `BinController`: 2 HTTP endpoint(s)
- `LocationController`: 2 HTTP endpoint(s)
- `RackController`: 2 HTTP endpoint(s)
- `InventoryDashboardController`: 2 HTTP endpoint(s)
- `HealthController`: 1 HTTP endpoint(s)
- `VehicleReportController`: 1 HTTP endpoint(s)

## Tech Stack
tvs-cps-inventory tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | Java | Unknown |
| Framework | spring-mvc | Unknown |
| Data | postgres | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: java) | Unknown |

Key libraries: `com.tvsm:tvsm-be-core`, `com.tvsm:tvsm-be-starter-parent`, `org.mapstruct:mapstruct`, `org.mapstruct:mapstruct-processor`, `org.postgresql:postgresql`, `org.projectlombok:lombok`, `org.springdoc:springdoc-openapi-starter-webmvc-ui`, `org.springframework.boot:spring-boot-starter-actuator`, `org.springframework.boot:spring-boot-starter-data-jpa`, `org.springframework.boot:spring-boot-starter-validation`, `org.springframework.boot:spring-boot-starter-web`

## Dependencies at a Glance
Upstream (calls tvs-cps-inventory): `tvs-cps-backend`
Downstream (tvs-cps-inventory calls): none resolved
Brokers: none. Data stores: `inventory_db` (postgres, read-write)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvs-cps-inventory environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| training | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
tvs-cps-inventory configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `app.rest.timeout.connect` | Unknown | Unknown | False | app-settings |
| `app.rest.timeout.read` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[0]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[1]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[2]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[3]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[4]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[5]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[6]` | Unknown | Unknown | False | app-settings |
| `bff.header-forwarding.allowed-headers[7]` | Unknown | Unknown | False | app-settings |
| `claim.catalog.appeal.limit` | Unknown | Unknown | False | app-settings |
| `default.skip-path` | Unknown | Unknown | False | app-settings |
| `default.tenant-id` | Unknown | Unknown | False | app-settings |
| `logging.level.com.tvsm.order` | Unknown | Unknown | False | app-settings |
| `logging.level.org.hibernate.SQL` | Unknown | Unknown | False | app-settings |
| `logging.level.org.hibernate.type.descriptor.sql.BasicBinder` | Unknown | Unknown | False | app-settings |
| `logging.level.org.springframework.web` | Unknown | Unknown | False | app-settings |
| `logging.pattern.console` | Unknown | Unknown | False | app-settings |
| `logging.pattern.file` | Unknown | Unknown | False | app-settings |
| `management.endpoint.health.show-details` | Unknown | Unknown | False | app-settings |
| `management.endpoints.web.exposure.include` | Unknown | Unknown | False | app-settings |
| `request.validation.skip-api-path` | Unknown | Unknown | False | app-settings |
| `request.validation.skip-exact-words` | Unknown | Unknown | False | app-settings |
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
| `tvsm.core.cloud-storage.azure.connection-string` | Unknown | Unknown | True | app-settings |
| `tvsm.core.cloud-storage.azure.container-name` | Unknown | Unknown | False | app-settings |
| `tvsm.core.cloud-storage.enabled` | Unknown | Unknown | False | app-settings |
| `tvsm.core.cloud-storage.provider` | Unknown | Unknown | False | app-settings |
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
| `tvsm.core.security.excludedPaths[4]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[5]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[6]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.excludedPaths[7]` | Unknown | Unknown | False | app-settings |
| `tvsm.core.security.jwt.publicKey.key1` | Unknown | Unknown | True | app-settings |
| `validation.files` | Unknown | Unknown | False | app-settings |

## Ownership
tvs-cps-inventory ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvs-cps-inventory local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvs-cps-inventory limitations evidenced by extraction:
- N/A — none evidenced in code
