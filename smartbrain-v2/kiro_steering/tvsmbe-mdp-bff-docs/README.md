# tvsmbe-mdp-bff — Onboarding Guide

> Onboarding-focused README for new contributors and vendors. The original `README.md` is preserved unchanged. For deeper docs see `HIGH_LEVEL_DESIGN.md`, `LOW_LEVEL_DESIGN.md`, and `docs/openapi.yaml`.

## 1. Application overview

`tvsmbe-mdp-bff` is the Backend-For-Frontend layer for the **MDP (Master Data Platform) Dealer module**. It abstracts MDP from clients and partner systems and propagates dealer changes outward.

The repository contains **two independently deployable Spring Boot 3 / Java 17 services**:

| Module | Role | Trigger |
|---|---|---|
| `inbound/`  (`com.tvsmotor.bff`) | Synchronous REST APIs over MDP dealer data + generic webhook intake | HTTP requests |
| `outbound/` (`com.tvsmotor.mdp_bff.outbound`) | Async consumer that fans MDP events out to Knowlarity / Single Interface / LatLong / Daksha | Azure Service Bus topic |

Shared building blocks: OkHttp for outbound HTTP, JPA on MySQL, Hibernate Envers for audit history, Spring Retry, Azure Service Bus SDK, springdoc OpenAPI.

## 2. Setup instructions

### Prerequisites
- **JDK 17** (Amazon Corretto 17 used by the Dockerfile)
- **Maven 3.9+**
- **MySQL 8.x** (local instance or Azure Database for MySQL connectivity)
- **Docker** (optional, for image builds)
- Network access to:
  - your MDP environment,
  - your Azure AD B2C tenant,
  - the Azure Service Bus namespace (outbound only),
  - partner sandboxes (outbound only — Knowlarity, Single Interface, LatLong, Daksha)

### Clone
```bash
git clone <repo-url>
cd tvsmbe-mdp-bff
```

### Database
Apply the SQL migrations in order against your MySQL database:
```bash
inbound/src/main/resources/db/migrations/v1.1_audit_log_table_20240523.sql
inbound/src/main/resources/db/migrations/v1.2_failed_mdp_message_entity_20241128.sql
inbound/src/main/resources/db/migrations/v1.3_audit_log_changes_20250203.sql
```
Both services read from the same schema.

## 3. Local development steps

The two services are independent Maven projects. Start them in separate shells.

### Inbound (port 8080, context `/mdp-bff`)
```bash
cd inbound
ACTIVE_ENVIRONMENT=local \
  DATABASE_HOST_URL=localhost \
  DATABASE_NAME=mdp_bff \
  DATABASE_USERNAME=root \
  DATABASE_PASSWORD=secret \
  MDP_BASE_URL=https://example.invalid \
  AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL=https://example.invalid/token \
  AZURE_B2C_CLIENT_ID=changeme \
  AZURE_B2C_CLIENT_SECRET=changeme \
  AZURE_B2C_SCOPE=changeme \
  mvn spring-boot:run
```

### Outbound (port 8080 by default — bind to a different host port locally)
```bash
cd outbound
ACTIVE_ENVIRONMENT=local \
  DATABASE_HOST_URL=localhost DATABASE_NAME=mdp_bff \
  DATABASE_USERNAME=root DATABASE_PASSWORD=secret \
  MDP_BASE_URL=https://example.invalid \
  MDP_BFF_EXTERNAL_CLIENTS=KNOWLARITY \
  MDP_DEALER_DATA_TOPIC_NAME=local.mdp.dealer_data \
  MDP_DEALER_DATA_TOPIC_CONNECTION_STRING='Endpoint=sb://...' \
  KNOWLARITY_K_NUMBER_API_URL=https://example.invalid \
  KNOWLARITY_K_NUMBER_API_TOKEN=changeme \
  KNOWLARITY_K_NUM_ASSIGNMENT_ENABLED_DEALER_TYPES=AMD,AD,BRANCH \
  SI_OUTLET_API_BASE_URL=https://example.invalid SI_OUTLET_API_TOKEN=changeme \
  SI_ENABLED_DEALER_TYPES=AMD,AD,BRANCH \
  LATLONG_DEALER_DATA_API_URL=https://example.invalid LATLONG_DEALER_DATA_API_TOKEN=changeme \
  DAKSHA_DEALER_UPDATE_API_URL=https://example.invalid DAKSHA_DEALER_UPDATE_API_TOKEN=changeme \
  NOTIFICATION_BASE_URL=https://example.invalid \
  NOTIFICATION_FAILURE_EMAIL_TEMPLATE_ID=changeme \
  NOTIFICATION_EMAIL_FAILURE_PRIORITY=HIGH \
  EXTERNAL_CLIENTS_FAILURE_EMAIL_ALERT_RECIPIENTS=ops@example.com \
  AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL=https://example.invalid/token \
  AZURE_B2C_CLIENT_ID=changeme AZURE_B2C_CLIENT_SECRET=changeme AZURE_B2C_SCOPE=changeme \
  mvn spring-boot:run
```

### Quick smoke test
- Swagger UI (inbound): http://localhost:8080/mdp-bff/swagger-ui/index.html
- Diagnostic: `curl http://localhost:8080/mdp-bff/v1/test/hello`

### IDE tips
- IntelliJ: open the repo root and import `inbound/pom.xml` and `outbound/pom.xml` as separate Maven projects.
- Lombok plugin + annotation processing must be enabled.

## 4. Environment variables

Configuration is **fully externalized**. The full set with placeholder values lives in the original `README.md` and `docs/API_SPECIFICATION.md`. Quick reference:

| Group | Variables |
|---|---|
| Profile | `ACTIVE_ENVIRONMENT` (`local | dev | uat | prod`) |
| Database | `DATABASE_HOST_URL`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD` |
| MDP | `MDP_BASE_URL` |
| Azure AD B2C | `AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL`, `AZURE_B2C_CLIENT_ID`, `AZURE_B2C_CLIENT_SECRET`, `AZURE_B2C_SCOPE` |
| Service Bus *(outbound)* | `MDP_DEALER_DATA_TOPIC_NAME`, `MDP_DEALER_DATA_TOPIC_CONNECTION_STRING` |
| Feature toggle *(outbound)* | `MDP_BFF_EXTERNAL_CLIENTS` (csv of `KNOWLARITY,SINGLE_INTERFACE,LAT_LONG,DAKSHA`) |
| Knowlarity *(outbound)* | `KNOWLARITY_K_NUMBER_API_URL`, `KNOWLARITY_K_NUMBER_API_TOKEN`, `KNOWLARITY_K_NUM_ASSIGNMENT_ENABLED_DEALER_TYPES` |
| Single Interface *(outbound)* | `SI_OUTLET_API_BASE_URL`, `SI_OUTLET_API_TOKEN`, `SI_ENABLED_DEALER_TYPES` |
| LatLong *(outbound)* | `LATLONG_DEALER_DATA_API_URL`, `LATLONG_DEALER_DATA_API_TOKEN` |
| Daksha *(outbound)* | `DAKSHA_DEALER_UPDATE_API_URL`, `DAKSHA_DEALER_UPDATE_API_TOKEN` |
| Notification *(outbound)* | `NOTIFICATION_BASE_URL`, `NOTIFICATION_FAILURE_EMAIL_TEMPLATE_ID`, `NOTIFICATION_EMAIL_FAILURE_PRIORITY`, `EXTERNAL_CLIENTS_FAILURE_EMAIL_ALERT_RECIPIENTS` |

> **Never commit real tokens or connection strings.** The repo's `.env` is ignored by `.gitignore`; use it for local-only values.

## 5. Build instructions

### Maven build (per module)
```bash
# inbound
cd inbound && mvn clean install

# outbound
cd outbound && mvn clean install
```

Outputs:
- `inbound/target/mdp_bff.jar`
- `outbound/target/outbound.jar`

JaCoCo coverage runs as part of `prepare-package`. Coverage gates are configured to `0.00` (informational only); see each `pom.xml`.

### Docker
```bash
# inbound
docker build -t tvsmbe-mdp-bff-inbound:local ./inbound

# outbound
docker build -t tvsmbe-mdp-bff-outbound:local ./outbound
```
Both images expose port `8080`, set `TZ=Asia/Kolkata`, and run with `-XX:MaxRAMPercentage=75`.

A reference manual-build script exists at `20241004_docker_manual_builder_and_pusher_MDP_BFF_v3.sh` (developer convenience only).

## 6. Deployment steps

CI/CD is driven by per-module pipelines:

| File | Stage |
|---|---|
| `inbound/ci-pipeline.yaml`, `outbound/ci-pipeline.yaml` | Build, test, image publish |
| `inbound/cd-pipeline.yaml`, `outbound/cd-pipeline.yaml` | Deploy to target environment |
| `*/sonar_ci_pr_pipelines.yml` | SonarQube on PR |
| `AST_Image_Scan_*` | AST/security image scans (UAT/PROD) |

Process:
1. Merge to the release branch triggers `ci-pipeline.yaml` for the affected module.
2. Image is pushed to the registry; `cd-pipeline.yaml` rolls out to the environment.
3. Spring Boot Actuator (`/actuator/health`) is the readiness/liveness target.
4. Schema migrations (`inbound/src/main/resources/db/migrations/v*.sql`) must be applied **manually** before the release that depends on them.
5. Rollback = redeploy previous image tag. Schema rollback must be planned per release (no migration framework).

> Promotion order: `dev` → `uat` → `prod`. Profile is selected via `ACTIVE_ENVIRONMENT`.

## 7. Testing instructions

```bash
# all tests for one module
cd inbound  && mvn test
cd outbound && mvn test

# JaCoCo HTML report
open inbound/target/site/jacoco/index.html
```

- Unit tests use **JUnit 5 + Mockito** via `spring-boot-starter-test`.
- Integration tests use an **in-memory H2** database (test scope) — no external services required.
- Excluded from coverage: `model/**`, `entity/**`, `exceptions/**` (configured in each `pom.xml`).

### Manual API test (inbound)
```bash
curl http://localhost:8080/mdp-bff/v1/mdp/dealer/14988
curl 'http://localhost:8080/mdp-bff/v1/mdp/dealers?pincode=600100'
curl -X POST http://localhost:8080/mdp-bff/v1/mdp/dealer/basedOnFilters \
  -H 'Content-Type: application/json' \
  -d '{"type":"AMD","sapStatus":"ACTIVE","flags":["SALES"]}'
```

## 8. Folder structure

```
.
├── README.md                           # original readme (env-var template, intent)
├── ONBOARDING.md                       # this guide
├── HIGH_LEVEL_DESIGN.md                # HLD
├── LOW_LEVEL_DESIGN.md                 # LLD
├── docs/
│   ├── HLD_tvsmbe-mdp-bff.md           # HLD (template-aligned)
│   ├── LLD_tvsmbe-mdp-bff.md           # LLD (template-aligned)
│   ├── API_SPECIFICATION.md            # narrative API doc
│   └── openapi.yaml                    # OpenAPI 3.0 spec
├── inbound/                            # Inbound Spring Boot service
│   ├── Dockerfile
│   ├── pom.xml
│   ├── ci-pipeline.yaml / cd-pipeline.yaml
│   ├── sonar_ci_pr_pipelines.yml
│   ├── AST_MDP_BFF_*_Pipeline.yml
│   └── src/
│       ├── main/java/com/tvsmotor/bff/  (BffApplication, controller, service,
│       │                                 entity, repository, model, enums,
│       │                                 exceptions, utils, cache, config)
│       └── main/resources/
│           ├── application*.properties  (per-profile)
│           └── db/migrations/*.sql
├── outbound/                           # Outbound Spring Boot service
│   ├── Dockerfile, pom.xml, *-pipeline.*
│   └── src/main/java/com/tvsmotor/mdp_bff/outbound/
│       (OutboundApplication, config/BffServiceBusConfig,
│        service/{service_bus, knowlarity, single_interface,
│                 lat_long, daksha, gmb_common}, ...)
├── AST_Image_Scan_MDP_BFF_*.yml        # repo-level image scan pipelines
└── 20241004_docker_manual_builder_and_pusher_MDP_BFF_v3.sh
```

## 9. Common troubleshooting

| Symptom | Likely cause | What to check |
|---|---|---|
| `Failed to determine a suitable driver class` on startup | DB env vars unset | `DATABASE_HOST_URL`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD` |
| `Connection refused` to MySQL | DB not reachable from pod/dev machine | Firewall, VNet peering, JDBC URL `jdbc:mysql://${DATABASE_HOST_URL}:3306/${DATABASE_NAME}` |
| Repeated `ExternalServiceException: Error while generating Azure B2C token` | Bad client_id/secret/scope or B2C URL | All four `AZURE_B2C_*` values |
| `400 Validation error occurred : sapDealerCode (string) is EMPTY` | Path variable missing/blank | URL path |
| `400 Validation error occurred : At least one of type, sapStatus, ...` | Empty filter body | Send at least one filter attribute |
| `400 Un-processable request received` | Malformed JSON body | `Content-Type: application/json` + valid JSON |
| Outbound consumer not picking messages | Bad connection string or missing subscription | `MDP_DEALER_DATA_TOPIC_NAME` and that the subscription `mdp_bff` exists in the topic |
| Outbound retries forever, no email alerts | `EXTERNAL_CLIENTS_FAILURE_EMAIL_ALERT_RECIPIENTS` empty, or cooldown active | Check `failure_event_type_info.last_notified_time`; cooldown is 1h per `FailureEventType` |
| Knowlarity flow stops with `KNOWLARITY_POOL_API_EMPTY` audit row | Pool exhausted at partner | Coordinate with Knowlarity ops; rows queued in `failed_mdp_message_exception` |
| `failed_mdp_message_exception` rows piling up | Partner outage or invalid mapping | Inspect `mdp_dealer_data` + `api_response`; replay manually after fix |
| Two pods log same UUID `serverInstanceId` collision | UUID collision (4-char fragment) | Cosmetic; for log correlation prefer Service Bus session id / transactionId |
| Swagger UI returns 404 in prod | Disabled by config | `springdoc.swagger-ui.enabled=false` (recommended in prod) |
| `@Retryable` doesn't seem to fire on SI create/close outlet | `@Retryable` on private methods is bypassed by Spring AOP proxies | Known issue; tracked in LLD risks |

### Useful diagnostics
- `audit_log` table — every external interaction (request body, status code, time-taken).
- Periodic `JVM_MEMORY_DATA_*` audit rows (every 60s).
- Outbound `GET /mdp-bff-outbound/v1/test/hello` returns the thread-pool stats.

## 10. Maintainer / contact

> Replace placeholders before sharing externally.

| Role | Contact |
|---|---|
| Service owner / Tech lead | _<name@tvsmotor.com>_ |
| Engineering manager | _<name@tvsmotor.com>_ |
| On-call / SRE | _<rotation@tvsmotor.com>_ |
| Slack / Teams channel | _#mdp-bff_ |
| JIRA project | _CBS02 (or current key)_ |
| Confluence space | [D&AI for D2W and IB](https://tvsmotorcompany.atlassian.net/wiki/spaces/DA) |

For partner integration questions (Knowlarity, Single Interface, LatLong, Daksha, Notification) raise a JIRA in the project above and tag the partner liaison.

---

### Related docs in this repo
- `README.md` — original repo intent + full env-var template
- `HIGH_LEVEL_DESIGN.md` / `docs/HLD_tvsmbe-mdp-bff.md` — system architecture
- `LOW_LEVEL_DESIGN.md` / `docs/LLD_tvsmbe-mdp-bff.md` — implementation detail
- `docs/API_SPECIFICATION.md` + `docs/openapi.yaml` — API reference
