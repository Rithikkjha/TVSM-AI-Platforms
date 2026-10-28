---
service_id: tvs-cps-db-migration
doc_type: hlc
last_reviewed: 2026-10-11
---
# TVS-CPS-DB-MIGRATION — High-Level Code
## Application Overview
tvs-cps-db-migration is a Maven Java 21 console application (artifact `com.tvsm:tvs-cps-db-migration:1.0.0-SNAPSHOT`, `pom.xml:8`) with entry point `com.tvsm.migration.MigrationRunner.main` and 195 SQL migration files.

## Module Summary
| Module | Path | Responsibility |
|---|---|---|
| Runner | `src/main/java/com/tvsm/migration/MigrationRunner.java` | CLI parsing, command dispatch |
| Config | `src/main/java/com/tvsm/migration/config/` | `MigrationConfig`, `DatabaseConfig` POJOs |
| Service | `src/main/java/com/tvsm/migration/service/MigrationService.java` | Flyway migrate + info |
| Util | `src/main/java/com/tvsm/migration/util/ConfigLoader.java` | YAML/JSON config loading |
| Migrations | `src/main/resources/db/migration/{cps-backend,customer,jobcard,cps-inventory,cps-billing}/` | Versioned `V<n>__*.sql` scripts |

## Folder Structure
```
TVS-CPS-DB-MIGRATION/
├── pom.xml
├── README.md
└── src/main/
    ├── java/com/tvsm/migration/
    │   ├── MigrationRunner.java
    │   ├── config/
    │   ├── service/
    │   └── util/
    └── resources/
        ├── config.yml
        └── db/migration/
            ├── cps-backend/   (138 files)
            ├── customer/      (15)
            ├── jobcard/       (28)
            ├── cps-inventory/ (11)
            └── cps-billing/   (3)
```

## Core Workflows in Code
### migrate
1. `MigrationRunner.main` reads `args[0]` command and `args[1]` config path (`MigrationRunner.java:24`).
2. `ConfigLoader.loadConfig` loads the file, falling back to classpath (`ConfigLoader.java:19`).
3. `handleMigrate` picks one named database or iterates all (`MigrationRunner.java:51`).
4. `MigrationService.migrate` builds Flyway with datasource, `locations`, optional `schemas`, runs `migrate()` then `info()` (`MigrationService.java:14`).

## Integration Clients
| Target service_id | Client class / file | Config key |
|---|---|---|
| PostgreSQL (data store `_`) | Flyway `Flyway.configure().dataSource(...)` in `MigrationService.java:19` | `databases.<name>.url` / `username` / `password` |

## Cross-Cutting Concerns
tvs-cps-db-migration: logging via slf4j (`LoggerFactory` in each class); errors wrapped as RuntimeException and mapped to exit code 1; no auth, validation beyond null checks, or caching.

## Build and Test
tvs-cps-db-migration: `mvn clean install` (README) → `target/tvs-cps-db-migration-1.0.0-SNAPSHOT.jar` (maven-shade-plugin). No tests in repo.
