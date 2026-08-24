# tvsm-auth (Auth Ninja)

Centralized Authentication & Authorization service for TVS Motor's connected services ecosystem. Manages user identity lifecycle, OAuth 2.0 flows via Azure AD B2C, biometric face authentication, eKYC verification, and role-based access control.

## Tech Stack

- **Java 17** / **Spring Boot 3.5.7**
- **MySQL** (Azure Database for MySQL)
- **Maven 3.9+**
- **Docker** (Amazon Corretto 17 Alpine)
- **Azure**: AD B2C, Face API, Blob Storage, Service Bus

---

## Prerequisites

- JDK 17+
- Maven 3.9+
- MySQL 8.0+
- Docker (optional, for containerized runs)
- Access to Azure B2C tenant and Face API (for full functionality)

---

## Local Development

### 1. Clone & Setup

```bash
git clone https://github.com/TVSM-CS/tvsm-auth.git
cd tvsm-auth
```

### 2. Database Setup

Create a local MySQL database:

```sql
CREATE DATABASE tvsm_auth;
```

### 3. Configure Environment

Set the required environment variables (see [Environment Variables](#environment-variables) below), or update `src/main/resources/application-local.properties` with local values.

### 4. Run Locally

```bash
# Using Maven
mvn spring-boot:run -Dspring-boot.run.profiles=local

# Or build and run JAR
mvn clean package -DskipTests
java -jar target/tvsm-auth.jar --spring.profiles.active=local
```

The service starts on **port 8080**.

### 5. Verify

```bash
curl "http://localhost:8080/auth/v1/app/test/health?beacon=test"
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ACTIVE_ENVIRONMENT` | Spring profile (`local`, `dev`, `uat`, `prod`) |
| `DB_URI` | MySQL JDBC URL |
| `DB_USERNAME` | Database username |
| `DB_PASSWORD` | Database password |
| `B2C_TENANT_NAME` | Azure B2C tenant name |
| `B2C_TENANT_ID` | Azure AD tenant ID |
| `B2C_ISSUER` | B2C issuer domain |
| `UMS_CLIENT_ID` | UMS app registration client ID |
| `UMS_CLIENT_SECRET` | UMS app registration secret |
| `AZURE_FACE_URL` | Azure Face API endpoint |
| `AZURE_FACE_SUBSCRIPTION` | Face API subscription key |
| `AZURE_BLOB_CONNECTION` | Blob Storage connection string |
| `AZURE_SERVICE_BUS_NAMESPACE` | Service Bus FQDN |
| `AZURE_SERVICE_BUS_TOPIC_NAME` | Service Bus topic |
| `AZURE_CLIENT_ID` | Managed Identity client ID |
| `KARZA_API_BASE_URL` | Karza eKYC API base URL |
| `KARZA_API_KEY` | Karza API key |
| `MDP_BASE_URL` | Master Data Platform URL |
| `MDP_CLIENT_ID` | MDP client ID |
| `MDP_CLIENT_SECRET` | MDP client secret |
| `NOTIFICATION_BASE_URL` | Notification service URL |
| `FACE_CONFIDENCE_THRESHOLD` | Min face match confidence |
| `EKYC_NAME_MATCH_THRESHOLD` | Min name match score |
| `MAX_PENDING_DAYS` | Days before pending→inactive |
| `MAX_PASSIVE_DAYS` | Days before passive→inactive |
| `MAX_UNUSED_DAYS` | Days before active→passive |

> For local development, most Azure-dependent features can be stubbed. Core user CRUD works with just DB variables configured.

---

## Build Instructions

```bash
# Full build with tests
mvn clean install

# Skip tests
mvn clean package -DskipTests

# Docker build
docker build -t tvsm-auth:latest .

# Docker run
docker run -p 8080:8080 \
  -e ACTIVE_ENVIRONMENT=local \
  -e DB_URI=jdbc:mysql://host.docker.internal:3306/tvsm_auth \
  -e DB_USERNAME=root \
  -e DB_PASSWORD=password \
  tvsm-auth:latest
```

---

## Deployment

Deployment is managed via Azure DevOps pipelines with Helm charts on AKS.

| Environment | Trigger | Approval |
|-------------|---------|----------|
| DEV | Auto (on CI success) | None |
| UAT | Manual | Required |
| PROD | Manual | Required |

Pipeline files:
- `ci-pipeline.yaml` — Build, test, Docker image, push to registry
- `cd-pipeline.yaml` — Helm deploy to AKS (auth-ninja)
- `cd-norton-pipeline.yaml` — Norton variant deployment

---

## Testing

```bash
# Run all tests
mvn test

# Run with coverage report
mvn verify

# Coverage report location
open target/site/jacoco/index.html
```

**Coverage requirement**: Minimum 40% line coverage per package (enforced by JaCoCo).

---

## Folder Structure

```
tvsm-auth/
├── src/main/java/com/tvsmotor/tvsmauth/
│   ├── AuthApplication.java          # Entry point
│   ├── aop/                           # @Authenticate aspect
│   ├── applications/                  # OAuth flows, app registry
│   ├── config/                        # Security, JWT, Azure configs
│   ├── support/                       # Utilities, constants
│   └── user/
│       ├── dealership/                # Dealership management
│       ├── department/                # Department CRUD
│       ├── designation/               # Designation entity
│       ├── dynamicforms/              # Dynamic registration forms
│       ├── gateway/                   # External API clients
│       ├── group/                     # Group CRUD
│       ├── permission/                # Permission entity
│       ├── profile/                   # Core user module
│       │   ├── api/                   # REST controllers
│       │   ├── ekyc/                  # eKYC verification
│       │   ├── entity/                # JPA entities
│       │   ├── repository/            # Data access
│       │   ├── scheduler/             # Cron jobs
│       │   └── service/               # Business logic
│       ├── role/                      # Role CRUD
│       ├── specialization/            # Specialization entity
│       └── type/                      # Type entity
├── src/main/resources/
│   ├── application.properties         # Main config (env vars)
│   └── application-local.properties   # Local dev overrides
├── docs/                              # Generated documentation
│   ├── HIGH_LEVEL_CODE_DOCUMENT.md
│   ├── HIGH_LEVEL_DESIGN.md
│   ├── LOW_LEVEL_DESIGN.md
│   └── API_SPECIFICATION.md
├── Dockerfile                         # Multi-stage Docker build
├── pom.xml                            # Maven dependencies
├── api-specs.yml                      # OpenAPI spec (partial)
└── *-pipeline.yaml                    # CI/CD pipeline configs
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection refused` on startup | Ensure MySQL is running and `DB_URI` is correct |
| `401 Unauthorized` on all requests | Check `Authorization` header format: `Bearer <token>` |
| `TokenException: No valid key found` | B2C JWKS keys may have rotated; restart to clear cache |
| `Face validation failed` | Ensure image is JPEG/PNG, single face, well-lit, no accessories |
| `Error fetching dealership from MDP` | MDP service may be down; check connectivity |
| `HikariPool exhausted` | Check for connection leaks; current max is 50 |
| Docker build fails | Ensure Maven can resolve dependencies (check proxy/VPN) |
| Tests fail locally | Some tests need H2; run with `mvn test` (H2 is test-scoped) |

---

## Documentation

| Document | Description |
|----------|-------------|
| [High Level Code Document](HIGH_LEVEL_CODE_DOCUMENT.md) | Application overview, modules, workflows |
| [High Level Design](HIGH_LEVEL_DESIGN.md) | Architecture, deployment, integrations |
| [Low Level Design](LOW_LEVEL_DESIGN.md) | Implementation details, schemas, algorithms |
| [API Specification](API_SPECIFICATION.md) | Full API reference with examples |
| [OpenAPI Spec](../api-specs.yml) | Machine-readable API spec (partial) |

---

## Maintainers

| Tech Lead | Arsh Baghel | Arsh.Baghel@tvsmotor.com |
| Backend Dev | Prabhav Gupta | prabhav@tvsmotor.com |
| DevOps | Shekhar Bachu | Shekhar.Bachu@tvsmotor.com |
| QA | Umashankar | Umashankar.HD@TVSD.ai |

---

## License

Proprietary — TVS Motor Company. Internal use only.
