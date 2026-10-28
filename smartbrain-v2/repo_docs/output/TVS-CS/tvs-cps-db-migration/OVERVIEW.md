---
service_id: tvs-cps-db-migration
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["tvs cps db migration", "tvs cps database migration", "cps db migration", "db migration", "cps database migration", "database migration"]
---
# TVS-CPS-DB-MIGRATION — Overview
## Purpose
Summary: Flyway-based CLI applying versioned PostgreSQL schema migrations per configured CPS module/schema; not a running service.
Also known as: tvs cps db migration, tvs cps database migration, cps db migration, db migration, cps database migration, database migration
tvs-cps-db-migration is a standalone Flyway-based database migration CLI (db-migration repo, not a running service) for the TVS Channel Partner System (CPS). It applies versioned PostgreSQL schema changes per configured module/schema (`README.md`, `src/main/java/com/tvsm/migration/MigrationRunner.java:18`). Business ownership of the schemas is Unknown.

## Users and Consumers
tvs-cps-db-migration has no inbound callers or event consumers in service.yaml / registry. It is run by an operator or pipeline (`java -jar ... migrate <config-file> [database-name]`, `MigrationRunner.java:84`). No registry edge links the migrated tables to the runtime services that read them, so consuming services are Unknown.

## Key Capabilities
tvs-cps-db-migration provides:
- `migrate` command: runs Flyway migrations for all configured databases, or one named database (`MigrationRunner.java:35`, `:51`).
- Per-database migration info table printed after migrating (`src/main/java/com/tvsm/migration/service/MigrationService.java:44`).
- Migration scripts for 5 modules under `src/main/resources/db/migration/`: `cps-backend` (V1–V140), `customer` (V1–V16), `jobcard` (V1–V28), `cps-inventory` (V1–V11), `cps-billing` (V1–V3).
- Optional per-database schema (default `public`) and custom migrations location (`src/main/java/com/tvsm/migration/config/DatabaseConfig.java:17`, `:76`).

## Tech Stack
| Layer | Technology | Version |
|---|---|---|
| Language | Java (runner) + PLpgSQL/SQL (migrations) | Java 21 (`pom.xml:16`) |
| Framework | Flyway core (`org.flywaydb:flyway-core`) | 9.22.3 (`pom.xml:56`) |
| Data | PostgreSQL (`org.postgresql:postgresql`) | 42.7.12 (`pom.xml:63`) |
| Messaging | N/A — none | |
| Hosting | Unknown — no Dockerfile/pipeline in repo; built as shaded jar (`pom.xml:129`) | |

Other libraries: jackson-core / jackson-databind / jackson-dataformat-yaml 2.22.2 (config parsing), slf4j-simple 2.0.9 (logging).

## Dependencies at a Glance
Upstream (calls tvs-cps-db-migration): none.
Downstream (tvs-cps-db-migration calls): no service or external targets. It writes to the PostgreSQL databases configured in its config file; service.yaml records one owned data store `_` (type other, write) with key entities such as `appointment_job_type_master`, `customer_vehicle`, `notification_message`, `tenant_config`, `workflow_template`.
Full detail: service.yaml `inbound` / `outbound`.

## Environments
| Env | URL | Notes |
|---|---|---|
| prod | Unknown | README mentions optional `config-prod.yml` (`README.md`) |
| uat | Unknown | README mentions optional `config-staging.yml` |
| dev | Unknown | README mentions optional `config-dev.yml` |

## Environment Variables
tvs-cps-db-migration reads no environment variables; configuration comes from a YAML/JSON file passed as the second CLI argument (`src/main/java/com/tvsm/migration/util/ConfigLoader.java:19`). Per-database keys under `databases.<name>`:

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| url | JDBC URL of target database | yes | no (may embed host) | config file |
| username | DB user | yes | yes | config file |
| password | DB password | yes | yes | config file |
| schema | Target schema (default `public`) | no | no | config file |
| serviceName | Migration folder name under `classpath:db/migration/` | no | no | config file |
| migrationsLocation | Override Flyway location | no | no | config file |

Configured database entries in `src/main/resources/config.yml`: `cps-backend`, `customer-service` (serviceName `customer`, schema `customer`), `cps-inventory`, `cps-billing` (schema `billing`); a `jobcard-service` entry is commented out.

## Ownership
| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvs-cps-db-migration local steps (`README.md`): Java 21+, PostgreSQL and Maven; `mvn clean install` produces `target/tvs-cps-db-migration-1.0.0-SNAPSHOT.jar`; run `java -jar target/tvs-cps-db-migration-1.0.0-SNAPSHOT.jar migrate config.yml [database-name]`.

## Known Limitations
tvs-cps-db-migration known limitations evidenced in code:
- Usage text advertises an `info` command but only `migrate` is handled; anything else exits with "Unknown command" (`MigrationRunner.java:35-43`, `:87`).
- `src/main/resources/config.yml` carries inline DB credentials in the repo (values not reproduced); should be externalised.
- The `jobcard` migration folder exists but its config entry is commented out (`config.yml:32`).
