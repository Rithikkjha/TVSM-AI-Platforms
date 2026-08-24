# tvsm-marketplace-service

Spring Boot 3.5 (Java 17) integration service that connects TVS Motor's internal commerce platforms (CCP, MDP, ATP, Lead, Booking, Notification, Location-Master) with external e-commerce marketplaces (Flipkart today; Amazon / IndiaMART / Paytm planned).

What it does:
- Synchronises vehicle prices from CCP to marketplace listings (OEM-as-a-Seller and Dealer-as-a-Seller flows).
- Receives marketplace order webhooks, persists orders, and drives them through a fulfilment state machine.
- Pushes invoice-dispatch and delivery confirmations back to marketplaces.
- Coordinates dealer assignment (proximity + inventory) with downstream Lead / Booking services.
- Provides operational APIs for cache control, async replays, and bulk reconciliation.

For deeper context:
- High-level design — `docs/HIGH_LEVEL_DESIGN.md`
- Code walkthrough — `docs/HIGH_LEVEL_CODE_DOCUMENT.md`
- Low-level design — `docs/LOW_LEVEL_DESIGN.md`
- API specification — `docs/openapi.yaml` and `docs/API_SPECIFICATION.md`

## Tech Stack

- Java 17, Spring Boot 3.5.7, Spring Data JPA, Spring Retry
- MySQL 8 (HikariCP)
- Azure Service Bus (sessions, peek-lock)
- OkHttp 4.12 for outbound HTTP
- Hibernate Envers for entity audit history
- Maven 3.9, JaCoCo for coverage
- Docker (Amazon Corretto 17 Alpine)

## Setup

### Prerequisites

- JDK 17 (Amazon Corretto recommended)
- Maven 3.9+ (or use the bundled `./mvnw`)
- Docker (optional, for containerised runs)
- MySQL 8 (local or remote) with a database for the service
- Network access to Azure Service Bus + the internal APIs you plan to integrate against

### Clone & build

```bash
git clone <repo-url> tvsm-marketplace-service
cd tvsm-marketplace-service
./mvnw clean install -DskipTests
```

Artifact: `target/marketplace.jar`.

## Local Development

The service expects all its configuration via environment variables (see next section). For local runs, point `ACTIVE_ENVIRONMENT=local` and disable Service Bus consumers so the app does not connect to Azure.

```bash
export ACTIVE_ENVIRONMENT=local
export SERVICEBUS_RECEIVERS_ENABLED=false
# DB
export DATABASE_HOST_URL=localhost
export DATABASE_NAME=marketplace
export DATABASE_USERNAME=marketplace
export DATABASE_PASSWORD=...
# everything else: see "Environment Variables" below

./mvnw spring-boot:run
```

The service listens on `:8080` with context-path `/marketplace`. Health check:

```bash
curl http://localhost:8080/marketplace/v1/test/health
```

Tips:
- In `local` / `test` profiles, Service Bus processor clients are not started, regardless of `SERVICEBUS_RECEIVERS_ENABLED`.
- Set `logging.level.root=DEBUG` to see request headers/params in the once-per-request filter.
- Every response carries a `uuid` (transaction id); use it to correlate logs and audit-log rows.
- OpenAPI is auto-served by `springdoc` at `/marketplace/swagger-ui/index.html` (once minimal annotations are added; see `docs/openapi.yaml` for the manually-curated spec).

### Database setup

Schema is managed via versioned SQL files under `src/main/resources/db/migration/v1.1 … v1.10`. The application does **not** run migrations on boot — apply them via your preferred tool (Flyway / Liquibase) before starting the service.

```bash
mysql -h "$DATABASE_HOST_URL" -u "$DATABASE_USERNAME" -p "$DATABASE_NAME" \
  < src/main/resources/db/migration/v1.1__basic_tables_20250311.sql
# repeat in version order, or use Flyway
```

## Environment Variables

All values are environment-injected; nothing is committed. Required at runtime:

| Variable | Purpose |
|---|---|
| `ACTIVE_ENVIRONMENT` | Spring profile selector (`local`, `dev`, `uat`, `prod`, `test`) |
| `DATABASE_HOST_URL` | MySQL host (no port) |
| `DATABASE_NAME` | DB schema name |
| `DATABASE_USERNAME` | DB username |
| `DATABASE_PASSWORD` | DB password |
| `SERVICEBUS_RECEIVERS_ENABLED` | `true` / `false` master switch for SB consumers |
| `VEHICLE_PRICE_DATA_TOPIC_NAME` | Azure SB topic name (CCP price events) |
| `VEHICLE_PRICE_DATA_TOPIC_CONNECTION_STRING` | SAS connection string for the above topic |
| `SERVICE_BUS_BOOKING_UPDATES_TOPIC_NAME` | Azure SB topic name (booking lifecycle events) |
| `SERVICE_BUS_BOOKING_UPDATES_CONNECTION_STRING` | SAS connection string for the above |
| `ENABLED_ECOMMERCE_MARKETPLACES` | Comma-separated list (e.g. `FLIPKART`) |
| `FLIPKART_SELLER_API_BASE_URL` | Flipkart Seller API root |
| `FLIPKART_OAUTH_APPLICATION_ID` | Flipkart OAuth app id (webhook signature) |
| `FLIPKART_OAUTH_APPLICATION_SECRET` | Flipkart OAuth app secret |
| `FLIPKART_WEBHOOK_NOTIFICATION_URL` | Public webhook URL Flipkart calls |
| `B2C_TOKEN_URL` | Azure AD B2C token endpoint |
| `B2C_CLIENT_ID` | B2C client id (this service) |
| `B2C_CLIENT_SECRET` | B2C client secret |
| `B2C_SCOPE` | B2C scope |
| `MDP_API_BASE_URL` | MDP base URL |
| `LOCATION_MASTER_BASE_URL` | Location master base URL |
| `LEAD_SERVICE_BASE_URL` | Lead service base URL |
| `BOOKING_SERVICE_API_BASE_URL` | Booking service base URL |
| `BOOKING_SERVICE_OCP_APIM_SUBSCRIPTION_KEY` | APIM subscription key for booking |
| `NOTIFICATION_SERVICE_BASE_URL` | Notification service base URL |
| `NOTIFICATION_EMAIL_PRICE_UPDATE_PRIORITY` | Email priority |
| `NOTIFICATION_EMAIL_PRICE_UPDATE_TEMPLATE_ID` | Email template id |
| `NOTIFICATION_EMAIL_PRICE_UPDATE_RECIPIENTS` | Comma-separated recipients |
| `PRICE_UPDATE_PRICE_THRESHOLD_IN_INR` | Min. price guard (currently informational) |
| `PRICE_UPDATE_FLIPKART_ENABLED_FLOWS` | `OEM_AS_A_SELLER`, `DEALER_AS_A_SELLER`, or both |
| `PRICE_UPDATE_FLIPKART_DEALER_AS_A_SELLER_TVS_CLIENT_ID` | Flipkart client id (Dealer flow) |
| `PRICE_UPDATE_FLIPKART_DEALER_AS_A_SELLER_TVS_CLIENT_SECRET` | Flipkart client secret (Dealer flow) |
| `SHOW_HTTP_500_ERROR_DETAILS` | `true` exposes stack traces in 500 responses (off in PROD) |
| `HOSTNAME` | Auto-injected by Kubernetes; used as `k8sPodName` |

> Do not commit `.env` or any secrets to git. Use your platform's secret store (AKS secrets, Azure Key Vault) for non-local environments.

## Build

```bash
# JAR
./mvnw clean install                 # runs tests + JaCoCo report
./mvnw clean install -DskipTests     # skip tests

# Docker (multi-stage; produces /usr/local/lib/marketplace.jar inside the image)
docker build -t tvsm/marketplace:local .

# Run the container
docker run --rm -p 8080:8080 \
  -e ACTIVE_ENVIRONMENT=local \
  -e SERVICEBUS_RECEIVERS_ENABLED=false \
  -e DATABASE_HOST_URL=host.docker.internal \
  -e DATABASE_NAME=marketplace \
  -e DATABASE_USERNAME=... -e DATABASE_PASSWORD=... \
  # ... add the rest of the env vars ...
  tvsm/marketplace:local
```

The Docker image runs with `-XX:MaxRAMPercentage=75` and timezone `Asia/Kolkata`.

## Testing

```bash
./mvnw test                          # unit + integration tests
./mvnw verify                        # tests + JaCoCo coverage report (target/site/jacoco)
```

Manual smoke tests (after local boot):

```bash
# health
curl http://localhost:8080/marketplace/v1/test/health

# Service Bus processor status
curl http://localhost:8080/marketplace/v1/test/service-bus/status

# replay an order through the state machine
curl http://localhost:8080/marketplace/v1/test/processOrderAsync?orderId=1
```

For end-to-end validation, point the service at a non-prod APIM and replay synthetic Flipkart payloads via Postman / `curl` against the webhook endpoint with a valid signed `X-Authorization` header.

## Deployment

The service ships as a single container deployed to Azure Kubernetes Service.

1. Pipeline `ci-pipeline.yaml` runs `./mvnw clean install`.
2. `sonar_ci_pipeline.yml` runs SonarQube static analysis.
3. `AST_Image_Scan_marketplace_Pipeline.yml` scans the produced image.
4. `cd-pipeline.yaml`, `AST_MDP_marketplace_UAT_Pipeline.yml`, `AST_MDP_marketplace_PROD_Pipeline.yml` deploy to UAT / PROD via standard rolling updates.
5. AKS CronJobs in `scripts/bash/aks/cronjob/` invoke periodic operational endpoints (process orders, sync status, bulk price update, cancellation discrepancy notifications).

Rollout guidance:
- Feature gates: `SERVICEBUS_RECEIVERS_ENABLED`, `ENABLED_ECOMMERCE_MARKETPLACES`, `PRICE_UPDATE_FLIPKART_ENABLED_FLOWS`.
- Schema changes follow expand-contract: roll out app first that tolerates both old + new schema, run migration, then remove old paths.
- Rollback: previous image tag; the service is stateless so rollbacks are safe. Service Bus messages remain in the subscription for redelivery.

A manual image build/push helper exists at `20250327_docker_manual_builder_and_pusher_marketplace.sh` for emergency hotfixes.

## Folder Structure

```
.
├── Dockerfile
├── pom.xml
├── ci-pipeline.yaml / cd-pipeline.yaml / sonar_ci_pipeline.yml
├── AST_*_Pipeline.yml
├── docs/                              # design docs + OpenAPI spec (this folder)
├── scripts/
│   ├── bash/aks/cronjob/              # AKS CronJob shell triggers
│   ├── java/                          # one-off helpers
│   └── python/                        # ops scripts
└── src/main/
    ├── java/com/tvsmotor/marketplace/
    │   ├── MarketplaceApplication.java
    │   ├── cache/                     # in-memory caches + token cache mgr
    │   ├── config/                    # OkHttp, ObjectMapper, ServiceBus, request filter
    │   ├── controller/                # REST controllers
    │   ├── entity/                    # JPA entities (+ order_management/, price_update/)
    │   ├── enums/
    │   ├── exceptions/                # ValidationException, RetryableException, RestExceptionHandler
    │   ├── model/                     # request/response DTOs
    │   ├── projection/                # Spring Data projections
    │   ├── repository/                # Spring Data JPA
    │   ├── service/                   # business services (sub-packages by domain)
    │   └── utils/                     # Constants, Context (ThreadLocal), GeneralUtils
    └── resources/
        ├── application.properties     # all values via env vars
        ├── logback-spring.xml
        └── db/migration/              # versioned SQL migrations v1.1 … v1.10
```

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| App fails to start, `Could not resolve placeholder '${...}'` | Missing env var. Verify the variables in §Environment Variables are all set. |
| `Communications link failure` to MySQL | Wrong `DATABASE_HOST_URL` / firewall; verify with `mysql -h "$DATABASE_HOST_URL" ...`. |
| Service Bus processor not running | Check `SERVICEBUS_RECEIVERS_ENABLED=true`, profile is not `local`/`test`, and connection strings are valid. Hit `/v1/test/service-bus/status`. |
| 401/403 from internal APIs (MDP, Booking, Lead, …) | B2C token cache may be stale. Evict via `DELETE /v1/test/cache/AZURE_B2C_TOKEN/AZURE_B2C_TOKEN`, then retry. |
| Webhook returns 400 `"Invalid hash"` | Mismatch between `FLIPKART_OAUTH_APPLICATION_ID/SECRET` and `FLIPKART_WEBHOOK_NOTIFICATION_URL`, or `X-Date` not in expected format. |
| Order stuck in a transient status | Check `Order.lastFailureReason` / `lastFailureAt`. Re-trigger via `GET /v1/order/process/{marketplace}` or `GET /v1/test/processOrderAsync?orderId=…`. |
| Bulk price update times out | Reduce dealer count via DB query, or run with smaller batches. Check upstream Flipkart rate limits via audit log entries tagged `BULK_PRICE_UPDATE_FLIPKART`. |
| Logs missing transaction id | Verify the call passed through `MarketplaceOncePerRequestFilter`. Background tasks must call `Context.setValues(...)` to propagate the id. |
| Hibernate optimistic-lock failure | Concurrent updates on the same `Order` row; safe to retry — the state machine reads + writes idempotently. |
| Tests failing on a fresh checkout | Ensure JDK 17 is on PATH (`java -version`) and run `./mvnw -U clean install` to refresh dependencies. |

## Maintainer / Contact

| Role | Owner |
|---|---|
| Engineering owner | _<add team / DL>_ |
| On-call | _<add rotation link>_ |
| Slack / Teams | _<add channel>_ |
| JIRA | _<add project key>_ |
| Confluence space | _<add link>_ |
| Incident runbook | _<add link>_ |

For production access, raise a request via the standard TVS Motor access workflow. External engineering partners should reach out to the engineering owner for environment provisioning and credentials.
