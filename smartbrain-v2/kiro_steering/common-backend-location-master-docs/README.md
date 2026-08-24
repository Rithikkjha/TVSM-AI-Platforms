# Location Master Service (`tvsmbe-location`)

Centralized microservice for managing dealer location data across the TVS Motor dealer network. Handles dealer location submissions, admin verification workflows, proximity-based dealer search, geocoding, and location master data management.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Java 17 |
| Framework | Spring Boot 3.5.x |
| Database | MongoDB |
| Object Storage | Azure Blob Storage |
| Auth | Azure AD B2C (OAuth2) |
| HTTP Client | OkHttp3 |
| Build | Maven 3.9+ |
| Container | Docker (Amazon Corretto 17 Alpine) |
| CI/CD | Azure DevOps Pipelines |

---

## Prerequisites

- Java 17 (Amazon Corretto recommended)
- Maven 3.9+
- MongoDB instance (local or Atlas)
- Docker (for containerized runs)
- Access to Azure Blob Storage, MDP, UMS, Notification Service credentials

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd tvsmbe-location
```

### 2. Configure environment variables

Copy the `.env` file and fill in the required values:

```bash
cp .env .env.local
# Edit .env.local with your credentials
```

### 3. Run locally

```bash
# Set environment variables (or use IDE run configuration)
export ACTIVE_ENVIRONMENT=local

# Build and run
mvn clean install -DskipTests
mvn spring-boot:run
```

The service starts at: `http://localhost:8080/location-master`

### 4. Verify

```bash
curl http://localhost:8080/location-master/api/v1/test/health?sapDealerCode=test
```

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ACTIVE_ENVIRONMENT` | Spring profile (local/dev/uat/prod) | `local` |
| `MONGODB_URI` | MongoDB connection string | `mongodb+srv://...` |
| `LOCATION_MASTER_AZUREBLOB_CONNECTION_STRING` | Azure Blob Storage connection | `DefaultEndpointsProtocol=...` |
| `AZUREBLOB_SAS_PRESIGNED_URL_EXPIRY_HOURS` | SAS URL expiry in hours | `2` |
| `AZUREBLOB_PUBLIC_DOMAIN` | Public CDN domain for photos | `uat-locationbe.tvsmotor.net` |
| `MDP_BASE_URL` | Master Data Platform base URL | `https://dev-api.tvsmotor.net/mdp` |
| `NOTIFICATION_BASE_URL` | Notification service URL | `https://...` |
| `NOTIFICATION_TOKEN_URL` | B2C token endpoint for Notification | `https://...` |
| `NOTIFICATION_CLIENT_ID` | OAuth2 client ID for Notification | `uuid` |
| `NOTIFICATION_CLIENT_SECRET` | OAuth2 client secret | `***` |
| `NOTIFICATION_SCOPE` | OAuth2 scope for Notification | `https://.../.default` |
| `NOTIFICATION_APIM_SUBSCRIPTION_KEY` | APIM subscription key | `***` |
| `NOTIFICATION_TEMPLATE_LOCATION_UPDATE` | SMS template ID | `1007172283034298907` |
| `NOTIFICATION_KEY_LOCATION_UPDATE` | SMS template key | `key` |
| `UMS_BASE_URL` | User Management Service URL | `https://...` |
| `UMS_TOKEN_URL` | B2C token endpoint for UMS | `https://...` |
| `UMS_CLIENT_ID` | OAuth2 client ID for UMS | `uuid` |
| `UMS_CLIENT_SECRET` | OAuth2 client secret for UMS | `***` |
| `UMS_SCOPE` | OAuth2 scope for UMS | `https://.../.default` |
| `GOOGLE_MAPS_GEOCODE_API_KEY` | Google Maps Geocoding API key | `***` |
| `LOCATION_UPDATE_SECRET_EXPIRY_DAYS` | Secret key validity in days | `2` |
| `SHOW_HTTP_500_DETAILS` | Show stack trace in 500 errors | `true` (dev only) |
| `PRIVACY_POLICY_FILE` | Blob path for privacy policy | `tvsm_documents/privacy_policy.html` |
| `TERMS_AND_CONDITION_FILE` | Blob path for T&C | `tvsm_documents/terms_and_condition.html` |
| `BETA_RELEASE_ENABLED` | Enable beta feature flag | `false` |
| `BETA_RELEASE_SAP_DEALER_CODES` | Comma-separated beta dealer codes | `10015,10016` |
| `SUBMITTED_LOCATION_ACCURACY_THRESHOLD_IN_METERS` | Max GPS accuracy for submission | `500` |
| `IMAGE_CAPTURED_LOCATION_ACCURACY_THRESHOLD_IN_METERS` | Max GPS accuracy for photo | `20` |

> **Note:** Never commit actual secrets. Use `.env` files locally and Azure App Service configuration for deployed environments.

---

## Build Instructions

### Maven Build

```bash
# Full build with tests
mvn clean install

# Skip tests
mvn clean install -DskipTests

# Generate JaCoCo coverage report
mvn clean test
# Report at: target/site/jacoco/index.html
```

### Docker Build

```bash
# Build image
docker build -t location-master:latest .

# Run container
docker run -p 8080:8080 \
  --env-file .env \
  location-master:latest
```

The Dockerfile uses a multi-stage build:
1. **Stage 1:** Maven build (produces `location-master.jar`)
2. **Stage 2:** Runtime image (Amazon Corretto 17 Alpine, JVM tuned with `-XX:MaxRAMPercentage=75`)

---

## Deployment

### CI/CD Pipeline (Azure DevOps)

```
Code Commit → SonarQube PR Analysis → CI Build (Maven + Docker) → AST Image Scan
    → Push to ACR → Deploy DEV (auto) → Deploy UAT (manual gate) → Deploy PROD (manual gate)
```

### Container Registry

- **Registry:** Azure Container Registry (ACR)
- **Image:** `tvsmazcmnsvcacrdev01location.azurecr.io/location-master:<tag>`
- **Target:** Azure App Service (Linux container)

### Manual Docker Push (if needed)

```bash
# See: 20250110_docker_manual_builder_and_pusher_location.sh
./20250110_docker_manual_builder_and_pusher_location.sh
```

---

## Testing

```bash
# Run all tests
mvn test

# Run specific test class
mvn test -Dtest=AdminFlowServiceTest

# Generate coverage report
mvn verify
# Coverage report: target/site/jacoco/index.html
```

### API Testing (Swagger UI)

Once running locally:
```
http://localhost:8080/location-master/internal/swagger-tvs-mdp.html
```

### Health Check

```bash
curl http://localhost:8080/location-master/api/v1/test/health?sapDealerCode=test
```

---

## Folder Structure

```
tvsmbe-location/
├── src/
│   ├── main/
│   │   ├── java/com/tvsmotor/location_master/
│   │   │   ├── config/          # Spring configuration beans
│   │   │   ├── controller/      # REST controllers (13)
│   │   │   ├── entity/          # MongoDB document entities
│   │   │   ├── ENUM/            # Application enumerations
│   │   │   ├── exception/       # Global exception handler
│   │   │   ├── model/
│   │   │   │   ├── request/     # Request DTOs (self-validating)
│   │   │   │   ├── response/    # Response DTOs
│   │   │   │   └── mongo_*/     # MongoDB projections & helpers
│   │   │   ├── repository/      # Spring Data MongoDB repos (19)
│   │   │   ├── security/        # JWT filter, RBAC, access control
│   │   │   ├── service/         # Business logic (35+ services)
│   │   │   └── utils/           # Utilities, constants, validators
│   │   └── resources/
│   │       └── application.properties
│   └── test/                    # Unit & integration tests
├── docs/
│   ├── HLD.md                   # High Level Design
│   ├── LLD.md                   # Low Level Design
│   ├── HLC.md                   # High Level Components
│   └── API_SPEC.md              # API Specification
├── azure-pipelines/             # CI/CD pipeline definitions
├── scripts/python/              # Data processing scripts
├── Dockerfile                   # Multi-stage Docker build
├── pom.xml                      # Maven project config
├── .env                         # Environment variables (local)
└── README.md                    # This file
```

---

## Key APIs

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/admin-flow/summary` | GET | Admin | Verification status summary |
| `/api/v1/admin-flow/list` | POST | Admin | Paginated dealer list |
| `/api/v1/admin-flow/verification` | POST | Admin | Verify/reject dealer |
| `/api/v1/admin-flow/send-location-update-sms` | POST | Admin | Send SMS to dealer |
| `/api/v1/dealer-flow/dealer/{code}` | GET | Dealer | Dealer + branch details |
| `/v1/dealer-location/submit` | POST | Open | Mobile location submission |
| `/api/v1/finder/dealers` | POST | Open | Proximity dealer search |
| `/api/v1/dealer-search` | POST | Open | IB dealer search |
| `/api/v1/dealer` | POST | Admin | Create IB dealer |
| `/api/v1/country/{code}/filter-config` | GET | Open | Country filter config |
| `/api/v1/location/{type}/list` | GET | Open | Location hierarchy |
| `/api/v1/geo/geocode` | GET | Open | Geocoding |

Full API documentation: [`docs/API_SPEC.md`](docs/API_SPEC.md)

---

## Common Troubleshooting

| Issue | Solution |
|-------|----------|
| `MONGODB_URI` connection failure | Ensure IP is whitelisted in MongoDB Atlas. Check connection string format includes `?retryWrites=true&w=majority` |
| `401 Unauthorized` on external APIs | Token may be expired. Clear cache: `DELETE /api/v1/test/cache/AZURE_B2C_TOKEN/{MDP\|NOTIFICATION\|UMS}` |
| `ValidationException: Invalid secret key` | Secret key expired (check `LOCATION_UPDATE_SECRET_EXPIRY_DAYS`). Admin must resend SMS |
| Photo upload fails | Verify `LOCATION_MASTER_AZUREBLOB_CONNECTION_STRING` and container `dealer-location-photo` exists |
| `Port 8080 already in use` | Kill existing process: `lsof -ti:8080 \| xargs kill -9` |
| Maven build fails on tests | Run with `-DskipTests` for quick builds. Ensure MongoDB is accessible for integration tests |
| `ClassNotFoundException` after dependency change | Run `mvn clean install` to rebuild |
| Swagger UI not loading | Verify `springdoc.swagger-ui.enabled=true` in properties. URL: `/location-master/internal/swagger-tvs-mdp.html` |
| Geocoding returns empty | Check `GOOGLE_MAPS_GEOCODE_API_KEY` is valid and has Geocoding API enabled |
| SMS not delivered | Check Notification Service status. Verify `NOTIFICATION_APIM_SUBSCRIPTION_KEY` and phone number format (+91XXXXXXXXXX) |

---

## Documentation

| Document | Path | Description |
|----------|------|-------------|
| High Level Design | [`docs/HLD.md`](docs/HLD.md) | Architecture, infrastructure, deployment |
| Low Level Design | [`docs/LLD.md`](docs/LLD.md) | Implementation details, algorithms, schemas |
| API Specification | [`docs/API_SPEC.md`](docs/API_SPEC.md) | Full API reference with samples |
| High Level Components | [`docs/HLC.md`](docs/HLC.md) | Component overview |

---

## Maintainers

| Role | Name | Contact |
|------|------|---------|
| Tech Lead | `<NAME>` | `<email>` |
| Backend Developer | `<NAME>` | `<email>` |
| DevOps | `<NAME>` | `<email>` |
| Product Owner | `<NAME>` | `<email>` |

**Team:** TVS Motor - Digital Engineering  
**Repository:** `TVSM-DMS/tvsmbe-location`  
**Slack/Teams Channel:** `#location-master-dev`

---

## License

Internal — TVS Motor Company. Not for public distribution.
