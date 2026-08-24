# TVS-CPS-DB-MIGRATION


## Product Context


# Product Context — TVS CPS Database Migration

## What This Service Does

This is a standalone CLI-based database migration tool for the **TVS Channel Partner System (CPS)** — a dealer/channel partner management platform for TVS Motor Company. It uses Flyway to apply versioned SQL schema changes across multiple PostgreSQL databases serving different microservices in the CPS ecosystem.

It is not a runtime service. It runs as a one-shot job to bring database schemas up to date.

## Domain Entities

### CPS Backend (62 migrations, `cps_db` / public schema)

| Entity | Purpose |
|--------|---------|
| **Announcements** | Multi-media announcements targeted to channel partners with criticality (LOW/MEDIUM/HIGH), read tracking, and validity windows |
| **Orders** | Parts ordering with order lines, state history, ERP (SAP) integration, workflow-driven approvals, and cart functionality |
| **Workflows** | Configurable workflow templates with versioning, actor-based routing (SYSTEM/USER/ROLE), and status tracking |
| **Claims** | Warranty, goodwill, transit damage, shortage, recall, and TSB claims with catalog mapping, ERP credit notes, timeline tracking, file attachments |
| **Appointments** | Service appointments with follow-ups, CCE (Customer Care Executive) assignment, context mapping |
| **Invoices & GRN** | Invoice management with line items, Goods Receipt Notes with delivery details, damage/shortage tracking |
| **NPQR (Quality Reports)** | Non-conformance/quality reporting for parts with defect codes and fault types |
| **Training** | Training content management with media attachments and read tracking |
| **Collateral** | Document/collateral management with tags and media |
| **Bulk Upload** | Async bulk data import with progress tracking and error reporting |
| **Warranty Registration Audit** | Step-based warranty registration tracking per VIN |
| **Cart** | Shopping cart for parts ordering before order creation |
| **Tenant Config** | Multi-tenant configuration (currency, timezone, locale) |
| **Analytics Indicators** | KPI/metrics per channel partner |

### CPS Billing (2 migrations, `billing_db` / billing schema)

- **Invoices** — Line items, discounts (line-level and invoice-level), tax calculations
- **Payments** — Multiple payment methods, receipt tracking
- **Invoice Sequencing** — Auto-generated invoice numbers

### CPS Inventory (9 migrations, `inventory_db`)

- **Inventory** — Stock tracking with location/rack/bin hierarchy
- **Vehicles** — VIN, engine number, manufacture date, PDI status
- **Vehicle-Dealer Mapping** — Stock types, inward types, damage tracking
- **Locations/Racks/Bins** — Warehouse hierarchy
- **Inventory Audit** — Stock movement audit trail

### Customer Service (14 migrations, `cps_db` / customer schema)

- **Customer** — Profiles, communication preferences, gender, DOB
- **Customer Address** — Multiple addresses per customer with primary flag
- **Customer Vehicle** — Vehicle ownership relationships (OWNER/SERVICE/USER)
- **Customer Dealer Mapping** — Sales/service dealer relationships

### Job Card (21 migrations, `cps_db` / jobcard schema)

- **Job Card** — Service job cards with lifecycle (CREATED → WORK_IN_PROGRESS → COMPLETED → CANCELLED → CLOSED)
- **Job Types** — PDI, MILEAGE_SERVICE, ANNUAL_SERVICE, ACCIDENT_REPAIR, OPEN_TIME
- **Service Types** — ROAD_SIDE_ASSIST, REGULAR_SERVICE, DEALERSHIP_COLLECT_AND_RETURN, WHILE_YOU_WAIT_SERVICE
- **Labor/Part Mapping** — Parts and labor consumed per job card
- **Billing** — Job card billing with line items, tax, discounts
- **Master Data** — Labour types, complaints, service types, job types, statuses

## Integrations

- **ERP/SAP** — Order and claim data syncs with SAP (sale order references, credit notes, RSO numbers)
- **Flyway** — Migration engine managing schema versioning and execution
- **PostgreSQL** — Target database (uses PG-specific features: `gen_random_uuid()`, JSONB, array types, partial indexes)

## Business Rules

- **Multi-tenancy** — All major entities carry a `tenant_id` column; tenant config stores currency/locale per tenant
- **Channel Partner scoping** — Most entities are scoped to a `channel_partner_id` with a `channel_partner_type`
- **Soft deletes** — Entities use `is_active`/`active` boolean flags rather than physical deletion
- **Audit trail** — All entities have `created_at`, `created_by`, `updated_at`, `updated_by` columns
- **UUID primary keys** — All entities use UUID PKs (mostly `gen_random_uuid()`)
- **Locale-aware master data** — Master/lookup tables support multiple locales via `(code, locale)` unique constraints
- **Workflow-driven approvals** — Orders and claims go through configurable workflow states with actor routing
- **Claim lifecycle** — Claims follow SUBMITTED → UNDER_REVIEW → APPROVED/REJECTED → PAID with per-line-item status tracking
- **Appointment follow-ups** — Appointments support follow-up scheduling with outcome tracking
- **Inventory hierarchy** — Location → Rack → Bin with default flags and active status



## Code Structure


# Project Structure — TVS CPS Database Migration

## Directory Layout

```
TVS-CPS-DB-MIGRATION/
├── pom.xml                              # Maven build config (shade plugin → fat JAR)
├── dependency-reduced-pom.xml           # Auto-generated by shade plugin (gitignored)
├── README.md                            # Usage documentation
├── .gitignore
│
└── src/main/
    ├── java/com/tvsm/migration/
    │   ├── MigrationRunner.java         # Entry point — CLI arg parsing, dispatches commands
    │   ├── config/
    │   │   ├── MigrationConfig.java     # Root config POJO (map of database names → DatabaseConfig)
    │   │   └── DatabaseConfig.java      # Per-database config (url, credentials, schema, service name)
    │   ├── service/
    │   │   └── MigrationService.java    # Flyway execution — migrate + info display
    │   └── util/
    │       └── ConfigLoader.java        # YAML/JSON config file reader (file system or classpath)
    │
    └── resources/
        ├── config.yml                   # Default database connection configuration
        └── db/migration/
            ├── cps-backend/             # 62 SQL migrations — core CPS tables
            ├── cps-billing/             # 2 SQL migrations — billing/invoice/payment
            ├── cps-inventory/           # 9 SQL migrations — inventory/vehicle/warehouse
            ├── customer/                # 14 SQL migrations — customer master
            └── jobcard/                 # 21 SQL migrations — service job cards
```

## Module Dependencies

```
MigrationRunner (entry point)
    ├── ConfigLoader         → reads YAML/JSON config file
    ├── MigrationConfig      → holds map of DatabaseConfig objects
    └── MigrationService     → executes Flyway migrations
         └── DatabaseConfig  → provides JDBC URL, credentials, schema, migration location
```

The dependency graph is intentionally flat. There are no circular dependencies or deep hierarchies.

## Architectural Decisions

### Standalone CLI (no framework)
The tool is a plain Java application with a `main()` method. No Spring Boot, no DI container. This keeps the JAR small, startup fast, and deployment simple. It runs as a one-shot process.

### Fat JAR via maven-shade-plugin
All dependencies are bundled into a single executable JAR. This simplifies deployment — just copy the JAR and a config file to the target environment.

### Convention-based migration location
`DatabaseConfig.getEffectiveMigrationsLocation(databaseName)` resolves the migration folder using the `serviceName` field (or falls back to the database key name). This means adding a new service only requires adding a config entry and a migration folder — no code changes.

### One config file, multiple databases
A single `config.yml` maps database names to connection details. The tool can migrate all databases in one run or target a specific one via CLI argument.

### Schema isolation
Different services use different PostgreSQL schemas within the same database (e.g., `customer` schema in `cps_db`, `billing` schema in `billing_db`). Flyway's `schemas()` config handles schema creation and migration table placement.

### Flyway versioned migrations only
All migrations use Flyway's `V{version}__{description}.sql` naming convention. No repeatable migrations (R__) or undo migrations (U__) are used.

### No rollback mechanism
Migrations are forward-only. There is no `undo` or `rollback` command. Schema changes should be additive or handled via new migration scripts.

## Key Conventions for New Migrations

- Place SQL files in `src/main/resources/db/migration/{serviceName}/`
- Name files as `V{next_version}__{description}.sql` (double underscore)
- Version numbers are sequential integers (V1, V2, ... V62)
- Each migration should be idempotent where possible (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`)
- Include indexes in the same migration that creates the table
- Use `CREATE INDEX IF NOT EXISTS` for index creation



## Tech Stack & Dependencies


# Tech Stack & Conventions — TVS CPS Database Migration

## Tech Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Java | 21 | Runtime |
| Maven | — | Build tool |
| Flyway | 9.22.3 | Database migration engine |
| PostgreSQL Driver | 42.7.11 | JDBC connectivity |
| Jackson (core, databind, yaml) | 2.18.6 | YAML/JSON config parsing |
| SLF4J Simple | 2.0.9 | Logging |
| maven-shade-plugin | 3.4.1 | Fat JAR packaging |
| maven-compiler-plugin | 3.11.0 | Java 21 compilation |

**Security:** Jackson pinned to 2.18.6 via `<dependencyManagement>` to fix GHSA-72hv-8253-57qq (DoS via async parser).

## Build & Run

```bash
# Build
mvn clean install

# Run all migrations
java -jar target/tvs-cps-db-migration-1.0.0-SNAPSHOT.jar migrate config.yml

# Run migrations for a specific database
java -jar target/tvs-cps-db-migration-1.0.0-SNAPSHOT.jar migrate config.yml cps-backend
```

## Coding Conventions

### Java Code
- Standard Java POJOs — no Lombok, no records
- Jackson `@JsonProperty` annotations for config deserialization
- SLF4J `Logger` for all logging (no `System.out` except for formatted info display)
- Package structure: `config`, `service`, `util` under `com.tvsm.migration`
- No interfaces for single implementations — concrete classes only
- Constructor-less POJOs with getters/setters (Jackson default deserialization)

### SQL Migrations
- **Naming:** `V{integer}__{snake_case_description}.sql` (e.g., `V25__npqr_table.sql`)
- **Idempotent DDL:** Use `IF NOT EXISTS` / `IF NOT EXISTS` guards
- **Primary keys:** UUID with `gen_random_uuid()` default (PostgreSQL native)
- **Audit columns:** Every table includes `created_at`, `created_by`, `updated_at`, `updated_by`
- **Multi-tenancy:** `tenant_id VARCHAR(50) NOT NULL` on all business tables
- **Soft deletes:** `is_active BOOLEAN NOT NULL DEFAULT TRUE` or `active BOOLEAN NOT NULL`
- **Timestamps:** `TIMESTAMP` or `TIMESTAMP WITH TIME ZONE` (no `DATE` for audit fields)
- **JSONB:** Used for flexible/extensible fields (`additional_info`, `payment_terms`, `configuration`)
- **Arrays:** PostgreSQL array types for tags (`TEXT[]`, `VARCHAR[]`)
- **Check constraints:** Inline `CHECK` for enum-like columns (e.g., status values)
- **Foreign keys:** Named constraints with `CONSTRAINT fk_{child}_{parent}` pattern
- **Indexes:** Created in the same migration as the table, named `idx_{table}_{column(s)}`
- **Master/lookup tables:** Use `(code, locale)` unique constraint for i18n support
- **Sequences:** Named sequences for business number generation (e.g., `npqr_sequence`, `order_sequence`)

### Configuration
- YAML format preferred (also supports JSON)
- Environment-specific files: `config-dev.yml`, `config-staging.yml`, `config-prod.yml`
- Passwords stored in plain text in config (expected to be overridden per environment)
- Schema defaults to `public` if not specified

## Patterns

### Migration Location Resolution
```
serviceName provided → classpath:db/migration/{serviceName}
serviceName absent   → classpath:db/migration/{databaseConfigKey}
migrationsLocation override → use as-is
```

### Error Handling
- `ConfigLoader` — wraps all exceptions in `RuntimeException` with context message
- `MigrationService` — catches Flyway exceptions, logs with database name context, re-throws as `RuntimeException`
- `MigrationRunner` — catches top-level exceptions, logs, and calls `System.exit(1)`
- No custom exception hierarchy — all failures are fatal (tool exits non-zero)
- Flyway handles per-migration atomicity (each migration runs in a transaction)

### Logging
- SLF4J with `slf4j-simple` backend
- Log levels: `INFO` for progress, `ERROR` for failures
- Pattern: log at entry/exit of operations with relevant context (database name, migration count)

## Testing

No test framework is present. The project has no unit or integration tests. Migrations are validated by Flyway's built-in checksum verification at runtime.

## Deployment

- **Artifact:** Single fat JAR (`tvs-cps-db-migration-1.0.0-SNAPSHOT.jar`)
- **Execution:** CLI invocation — typically run as a pre-deployment step or CI/CD job
- **Configuration:** External YAML file passed as CLI argument (not bundled in JAR for production)
- **Database targets:** 3 PostgreSQL databases (`cps_db`, `inventory_db`, `billing_db`)
- **Schema management:** Flyway creates schemas if they don't exist when `schemas()` is configured
- **Idempotency:** Safe to re-run — Flyway tracks applied migrations in `flyway_schema_history` table per schema
- **No rollback:** Forward-only migrations; fix-forward with new migration scripts if issues arise

