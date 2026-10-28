---
service_id: tvs-cps-db-migration
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---
# TVS-CPS-DB-MIGRATION — API Specification
## Authentication
N/A — tvs-cps-db-migration exposes no network API. It authenticates to PostgreSQL with the `username`/`password` from its config file (`src/main/java/com/tvsm/migration/service/MigrationService.java:20`).

## Endpoint Index
tvs-cps-db-migration has no HTTP endpoints and no scheduled jobs (inventory has 0 `inbound_http` / `scheduled_job` items). Its only interface is the CLI:

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| CLI | `migrate <config-file> [database-name]` | DB credentials from config | Run Flyway migrations (`MigrationRunner.java:35`) | Unknown (operator/pipeline) |

## Endpoints
N/A — tvs-cps-db-migration has no HTTP endpoints.

## Outbound Calls
N/A — tvs-cps-db-migration makes no outbound HTTP calls; it only opens JDBC connections to configured PostgreSQL databases.

## Schemas
tvs-cps-db-migration has no API DTOs. Its config schema:
### MigrationConfig
Defined in: `src/main/java/com/tvsm/migration/config/MigrationConfig.java:6`
| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| databases | Map<String, DatabaseConfig> | yes | Empty/null → exit 1 (`MigrationRunner.java:30`) |
### DatabaseConfig
Defined in: `src/main/java/com/tvsm/migration/config/DatabaseConfig.java:5`
| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| url | String | yes | JDBC URL |
| username | String | yes | secret |
| password | String | yes | secret |
| schema | String | no | default `public` (`:17`) |
| serviceName | String | no | migration folder; falls back to database key (`:80`) |
| migrationsLocation | String | no | overrides `classpath:db/migration/<serviceName>` (`:77`) |

## Events Published
N/A — tvs-cps-db-migration publishes no events.

## Events Consumed
N/A — tvs-cps-db-migration consumes no events.

## External Integrations
N/A — tvs-cps-db-migration has no external system integrations (only PostgreSQL via JDBC).

## Rate Limits and SLAs
N/A — not determinable from code.
