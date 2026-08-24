# Master Data Platform (MDP) — Onboarding Guide

Centralized master-data service for **dealer**, **vehicle product**, **vehicle pricing**, **part**, and **part-pricing** data at TVS Motor Company. MDP is the system of record for these domains: it ingests upstream data (SAP, DMS, SharePoint), persists it in MySQL with a Redis cache layer, exposes versioned REST APIs, and emits domain events on Azure Service Bus for downstream consumers.

| | |
|---|---|
| Language / Runtime | Java 17 (Amazon Corretto) |
| Framework | Spring Boot 3.5.x |
| Build | Maven 3.9.x |
| Datastores | MySQL 8.4 (primary), Redis 7 (cache), MSSQL (DMS, read-only) |
| Messaging | Azure Service Bus (JMS) |
| Auth | OAuth2 / Azure AD B2C (Bearer JWT) |
| Container | Multi-stage Docker → Amazon Corretto 17 |
| Orchestration | Azure Kubernetes Service (AKS) |
| Context path | `/mdp` (port `8080`) |

---

## 1. Companion documentation

| Doc | Purpose |
|-----|---------|
| `README.md` | Repo quick-start (original) |
| `HIGH_LEVEL_DESIGN.md` | Architecture, components, deployment, scalability |
| `LOW_LEVEL_DESIGN.md` | Module breakdown, class responsibilities, internal flows |
| `API_SPECIFICATION.md` | Vendor-facing API reference (endpoints, payloads, errors) |
| `HIGH_LEVEL_CODE_DOCUMENT.md` | Code-walkthrough companion to the HLD |
| `MYSQL_UPGRADE_CHECKLIST.md` | DB upgrade runbook |

---

## 2. Setup

### Prerequisites

- **JDK 17** (Amazon Corretto recommended). IntelliJ can install Corretto 17 on first project open.
- **Maven 3.9.x** (or use IntelliJ's bundled Maven).
- **Docker** + **Docker Compose** for local infra (MySQL, Redis).
- **Git**.
- **IDE**: IntelliJ IDEA is preferred (Lombok plugin enabled, annotation processing on).

### Clone

```bash
git clone <repo-url> master-data-platform
cd master-data-platform
```

### Bring up local infrastructure

A `docker-compose.yml` is provided to run a local MySQL 8.4 and Redis 7:

```bash
docker compose up -d
```

This exposes:

- MySQL on `localhost:3307` (mapped from container's `3306`) — DB `mdp_db`, user `root`, password `rootpassword`
- Redis on `localhost:6379`

> Use port `3307` to avoid conflicts with any local MySQL on `3306`.

---

## 3. Local development

1. Set the `ACTIVE_ENVIRONMENT` environment variable (in your IDE run config or shell):

   ```bash
   export ACTIVE_ENVIRONMENT=local
   ```

2. Provide the local environment variables (see § 4). The minimum to boot are listed in `application-local.properties`. For local dev you can copy a `.env` file (gitignored) and load it via your IDE's `EnvFile` plugin.

3. Run the app:

   - **From IntelliJ:** open the project, let Maven import dependencies, run `MdpApplication`.
   - **From CLI:**

     ```bash
     mvn spring-boot:run
     ```

4. Verify:

   - REST: `http://localhost:8080/mdp/actuator/health`
   - Swagger: `http://localhost:8080/mdp/swagger-ui/index.html`

5. DB migrations live under `src/main/resources/db/migration/` and are forward-only.

### Coding conventions

- American English in code (`Sanitize`, `Authorize`, `Analyze`).
- Services call services, **never** another module's repository directly.
- Soft delete only — no `DELETE` SQL.
- Timestamps (`createdAt`, `updatedAt`) are generated in the application, not by the DB.
- Optimistic locking via `@Version` on entities.

---

## 4. Environment variables

The base `application.properties` references all keys as `${VAR}` placeholders. Per-environment files (`application-local.properties`, `application-dev.properties`, `application-uat.properties`, `application-prod.properties`) override values that differ.

```bash
# core
ACTIVE_ENVIRONMENT=local
DATABASE_HOST_URL=localhost
DATABASE_NAME=mdp_db
DATABASE_USERNAME=root
DATABASE_PASSWORD=<your-local-password>
REDIS_HOST_URL=localhost
REDIS_PASSWORD=

# diagnostic
SHOW_HTTP_500_DETAILS=true   # MUST stay false in prod

# Azure Service Bus topics (one connection-string + topic-name per topic)
SERVICE_BUS_DEALER_DATA_CONNECTION_STRING=
SERVICE_BUS_DEALER_DATA_TOPIC_NAME=local.mdp.dealer_data
SERVICE_BUS_DMS_DEALER_DATA_CONNECTION_STRING=
SERVICE_BUS_DMS_DEALER_DATA_TOPIC_NAME=local.dms.dealer_data
SERVICE_BUS_VEHICLE_DATA_CONNECTION_STRING=
SERVICE_BUS_VEHICLE_DATA_TOPIC_NAME=local.mdp.product.vehicle
SERVICE_BUS_PRICE_DATA_CONNECTION_STRING=
SERVICE_BUS_PRICE_DATA_TOPIC_NAME=local.mdp.price.vehicle
SERVICE_BUS_PRODUCT_MNA_DATA_CONNECTION_STRING=
SERVICE_BUS_PRODUCT_MNA_DATA_TOPIC_NAME=local.mdp.product.mna
SERVICE_BUS_PART_DATA_CONNECTION_STRING=
SERVICE_BUS_PART_DATA_TOPIC_NAME=local.mdp.part_data
SERVICE_BUS_PART_PRICE_DATA_CONNECTION_STRING=
SERVICE_BUS_PART_PRICE_DATA_TOPIC_NAME=local.mdp.part.price

# DMS read-only datasource
DMS_DATABASE_HOST=
DMS_DATABASE_USERNAME=
DMS_DATABASE_PASSWORD=
EXCLUDED_AMD_SAP_DEALER_CODES=

# outbound HTTP integrations
APIM_BASE_URL=
NOTIFICATION_BASE_URL=
NOTIFICATION_EMAIL_FAILURE_TEMPLATE_ID=
NOTIFICATION_EMAIL_FAILURE_RECIPIENTS=
NOTIFICATION_EMAIL_NEW_DEALER_ACTIVE_DMS_MIGRATION_RECIPIENTS=
NOTIFICATION_EMAIL_NEW_DEALER_ACTIVE_SHAREPOINT_RECIPIENTS=
NOTIFICATION_EMAIL_FAILURE_PRIORITY=

# Azure AD B2C (outbound auth)
AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL=
AZURE_B2C_CLIENT_ID=
AZURE_B2C_CLIENT_SECRET=
AZURE_B2C_SCOPE=
```

> **Never commit secrets.** `.env` is in `.gitignore`. UAT/PROD secrets are injected by the platform.

---

## 5. Build

### Local Maven build

```bash
mvn clean install
```

This compiles, runs unit tests, and produces `target/mdp.jar`.

To skip tests during a quick build:

```bash
mvn clean install -DskipTests
```

### Container build

The repo's multi-stage `Dockerfile` builds the JAR and packages it on Amazon Corretto 17:

```bash
docker build -t master-data-platform:local .
docker run --rm -p 8080:8080 \
  --env-file .env \
  master-data-platform:local
```

---

## 6. Deployment

Deployments are CI/CD-driven via Azure DevOps. Pipelines in this repo:

| Pipeline | Purpose |
|----------|---------|
| `ci-pipeline.yaml` / `cd-pipeline.yaml` | Standard build + multi-env deploy (dev → uat → prod) |
| `azure-pipelines/uat.ci.yml`, `azure-pipelines/prod.ci.yml` | Per-env image build + push to ACR |
| `azure-pipelines/uat_cd_yaml`, `azure-pipelines/prod.cd.yml` | Per-env deploy |
| `AST_Image_Scan_MDP_Pipeline.yml` | Image security scan gate |
| `sonar_ci_pr_pipelines.yml` | SonarQube static analysis on PRs |

Flow:

1. PR → Sonar pipeline runs static analysis.
2. Merge to env branch → CI pipeline builds, runs tests, builds container, pushes to ACR, runs AST image scan.
3. CD pipeline deploys to AKS via Helm. **UAT and Prod require manual approval.**
4. Rollback = redeploy the previous image tag from ACR. Schema migrations are forward-compatible (expand-then-contract).

---

## 7. Testing

```bash
mvn test                              # unit tests
mvn verify                            # unit + integration tests
mvn clean verify -Pjacoco             # coverage report at target/site/jacoco/index.html
```

- Stack: JUnit 4, Mockito Inline, H2 (in-memory) for repository tests.
- Coverage report (HTML) is also pre-generated under `htmlReport/` for reference.

---

## 8. Folder structure

```
master-data-platform/
├── src/
│   ├── main/
│   │   ├── java/com/tvsmotor/mdp/
│   │   │   ├── MdpApplication.java          # Spring Boot bootstrap
│   │   │   ├── aop/                         # @Authorization, @DisableOnProd, @Timed
│   │   │   ├── common/                      # cache, exceptions, audit log, utilities
│   │   │   ├── config/                      # request filter, datasources, SB config
│   │   │   ├── controller/                  # REST controllers (dealer + migration)
│   │   │   ├── dealer/                      # Service-Bus event models for dealer
│   │   │   ├── entity/                      # JPA entities (dealer domain)
│   │   │   ├── enums/                       # domain enums
│   │   │   ├── model/                       # DTOs (request, response, redis)
│   │   │   ├── repository/                  # JPA repositories (dealer domain)
│   │   │   ├── service/                     # business logic + service_bus + migration
│   │   │   ├── product/  product_mna/
│   │   │   │   product_part/  price/
│   │   │   │   part_price/                  # self-contained domain modules
│   │   │   └── utils/                       # JWT, validation helpers
│   │   └── resources/
│   │       ├── application.properties       # base config
│   │       ├── application-{local,dev,uat,prod}.properties
│   │       ├── db/migration/                # forward-only SQL migrations (v1.1+)
│   │       └── logback-spring.xml
│   └── test/                                # JUnit + Mockito tests
├── azure-pipelines/                         # env-specific CI/CD yamls
├── docker/                                  # local Docker artefacts
├── docker-compose.yml                       # local MySQL + Redis
├── Dockerfile                               # multi-stage build
├── pom.xml
├── ci-pipeline.yaml, cd-pipeline.yaml       # primary CI/CD entry points
├── HIGH_LEVEL_DESIGN.md, LOW_LEVEL_DESIGN.md, API_SPECIFICATION.md
├── README.md                                # original quick-start
└── ONBOARDING.md                            # this guide
```

See `LOW_LEVEL_DESIGN.md` § "Module map" for a per-package responsibility map.

---

## 9. Troubleshooting

| Symptom | Likely cause / fix |
|---------|-------------------|
| `Unable to determine Dialect for ...` on startup | `DATABASE_*` env vars not set or DB unreachable. `docker compose up -d` and confirm port `3307`. |
| `Cache region 'DEALER_DATA' is not configured` | Redis not running or `REDIS_HOST_URL` wrong. Check `docker compose ps`. |
| `403` / `Access Denied` on every API | Token doesn't carry the `mdp.api` role, or `appid` is not present in `auth_client_users`. Confirm with the Identity team. |
| `Token expired` | B2C tokens last 1 hour. Regenerate via the client-credentials flow (see `API_SPECIFICATION.md` § 1). |
| `This API is disabled on PROD.` | Endpoint is annotated `@DisableOnProd` — used for diagnostics only. Use the production-equivalent flow instead. |
| Spring Retry / `@Retryable` not retrying | Method must be on a Spring-managed bean and called through the proxy (no `this.foo()` self-calls). |
| Lombok-related compile errors in IntelliJ | Install the Lombok plugin and enable `Build → Compiler → Annotation Processors → Enable annotation processing`. |
| Migration fails on startup | Migrations are forward-only. Don't edit shipped migration files; add a new `vX.Y__...sql`. |
| Service Bus consumer not consuming | Verify connection string + topic name env vars; check `spring.jms.servicebus.topic.<name>.subscription` matches the Azure SB subscription. |
| 5xx with `"Internal Error occurred"` and no detail | `show.http_500_error_details` is `false`. Set to `true` in non-prod via `SHOW_HTTP_500_DETAILS=true` to see stack traces. **Never** enable in prod. |

For broader debugging, the `Context` thread-local logs a per-request `transactionId` (also returned in the `uuid` field of every API response). Quote that id when filing tickets.

---

## 10. Maintainers & contact

| Role | Owner |
|------|-------|
| Tech lead | _TBD_ |
| Backend maintainers | _TBD_ |
| Platform / DevOps owner | _TBD_ |
| Identity (B2C) contact | _TBD_ |
| Data engineering (ADF / Data Lake) | _TBD_ |
| On-call / paging channel | _TBD_ |
| Slack / Teams channel | _TBD_ |
| Issue tracker | _TBD_ (Jira project: _TBD_) |

> Replace placeholders with team / channel names as they're confirmed.

---

## Glossary

| Term | Meaning |
|------|---------|
| `sapDealerCode` | Dealer identifier originating in SAP, unique per dealer |
| AMD | Authorized Main Dealer |
| APS | Authorized Parts Stockist |
| BRANCH | Branch dealer linked to a parent AMD |
| DMS | Dealer Management System (operational source, MSSQL) |
| ADF | Azure Data Factory |
| APIM | Azure API Management |
| AKS | Azure Kubernetes Service |
| Soft delete | Logical-delete via flag; no `DELETE` SQL |
| Envers | Hibernate's entity-versioning module |

---

*This repository contains no committed secrets. UAT/PROD credentials are managed exclusively via the platform's secret store and CI/CD pipeline variables.*
