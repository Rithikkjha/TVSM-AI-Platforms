# Booking CRUD Services

Backend microservice for TVS Motor's vehicle booking platform (Booking 2.0). Manages the full booking lifecycle — creation, modification, cancellation, retrieval, and refund processing.

**Tech Stack**: NestJS 11 · TypeScript · TypeORM · Azure SQL (MSSQL) · Azure Service Bus · Azure Key Vault · OpenTelemetry

---

## Setup Instructions

### Prerequisites

- Node.js 26.x
- Yarn 1.x
- Access to Azure Key Vault (for DB and Service Bus config)
- Azure AD service principal credentials

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd booking-crud-services

# Install dependencies
yarn install
```

---

## Local Development

```bash
# Start in development mode (hot-reload)
yarn start:dev

# Start with debugger
yarn start:debug
```

The service starts on the port defined in `APP_PORT` (default from `.env`).

- **Swagger UI**: http://localhost:{PORT}/api-doc
- **Health Check**: http://localhost:{PORT}/bookings/health

---

## Environment Variables

Create a `.env` file in the project root:

| Variable | Description | Required |
|----------|-------------|----------|
| `APP_PORT` | HTTP server port | ✅ |
| `KEYVAULT_URL` | Azure Key Vault endpoint URL | ✅ |
| `BOOKING_SERVICE_DB_CONFIG` | Key Vault secret name for DB configuration | ✅ |
| `BOOKING_SERVICE_CONFIG` | Key Vault secret name for service configuration (SB, APIs) | ✅ |
| `BAS_DB_CLIENT_ID` | Azure AD service principal client ID | ✅ |
| `BAS_DB_CLIENT_SECRET` | Azure AD service principal secret | ✅ |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector endpoint | Optional |
| `OTEL_SERVICE_NAME` | Service name for traces (default: `booking-service`) | Optional |
| `DEPLOYMENT_ENVIRONMENT` | Environment label (dev/uat/prod) | Optional |
| `OTEL_LOG_LEVEL` | Set to `DEBUG` for verbose OTel logs | Optional |

> **Note**: Database connection details, Service Bus endpoints, and API keys are stored in Azure Key Vault — not in environment variables directly.

---

## Build Instructions

```bash
# Production build
yarn build

# This runs: nest build → copy package.json to dist/ → install prod deps in dist/
```

### Docker Build

```bash
# Build Docker image
docker build -t booking-crud-services .

# Run container
docker run -p 8080:8080 --env-file .env booking-crud-services
```

The Dockerfile uses a multi-stage build (Node.js 26 Alpine):
1. **Builder stage**: installs all deps, compiles TypeScript
2. **Runner stage**: copies only `dist/` and `node_modules`, runs `node dist/main.js`

---

## Deployment

| Environment | Pipeline File |
|-------------|--------------|
| DEV | `AST_Website_Corporate_booking_crud_services_DEV_Pipeline.yml` |
| UAT | `azure-pipelines/ast-booking-crud-uat-pipeline.yaml` |
| PROD | `azure-pipelines/ast-booking-crud-prod-pipeline.yaml` |
| Image Scan | `azure-pipelines/ast-image-scan-booking-crud-pipeline.yaml` |

**Deployment flow**: DEV → UAT → Image Scan → PROD

**Rollback**: Redeploy the previous Docker image version via pipeline.

---

## Testing

```bash
# Run unit tests
yarn test

# Run tests with coverage
yarn test:cov

# Run e2e tests
yarn test:e2e

# Run tests in watch mode
yarn test:watch
```

- Test files are co-located with source: `*.spec.ts`
- Framework: Jest 30 + ts-jest
- Coverage excludes: DTOs, modules, migrations, interfaces, main.ts

---

## Folder Structure

```
src/
├── main.ts                    # Bootstrap (OTel → NestJS → Swagger → Listen)
├── app.module.ts              # Root module
├── otel.ts                    # OpenTelemetry setup
├── otel-propagation.ts        # Trace context helpers
│
├── bookings/                  # Core feature module
│   ├── controllers/           # REST API (single controller)
│   ├── dto/                   # Request/response DTOs
│   ├── middleware/            # HTTP middleware
│   └── services/
│       ├── booking-creation/  # Online, offline, pre-booking
│       ├── booking-modification/ # Payment, vehicle, dealer, invoice, etc.
│       ├── booking-cancellation/ # Cancel workflow + refund
│       ├── booking-refund/    # CPG, JusPay, CCAvenue refunds
│       ├── booking-retrieval/ # Search/fetch services
│       ├── custom-repositories/ # TypeORM data access layer
│       ├── publisher/         # Service Bus event publishers
│       └── validation/        # Request validation logic
│
├── cloud-conductor/           # Azure integration module
│   └── services/
│       ├── keyvault/          # Secret retrieval
│       ├── listener/          # Service Bus consumers (4 listeners)
│       ├── publisher/         # Service Bus producer
│       └── model-transformer/ # DTO → message transformers
│
├── database/entities/         # TypeORM entity definitions
├── logger/                    # Winston logging service
└── shared/                    # Constants, utils, exceptions
```

---

## Common Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Service fails to start | Key Vault unreachable or secret names misconfigured | Verify `KEYVAULT_URL`, `BOOKING_SERVICE_DB_CONFIG`, `BOOKING_SERVICE_CONFIG` env vars |
| DB connection error | Azure AD credentials invalid or expired | Rotate `BAS_DB_CLIENT_ID` / `BAS_DB_CLIENT_SECRET` |
| Service Bus listener not consuming | Wrong topic/subscription config in Key Vault | Check the JSON secret contains correct `TOPIC_NAME`, `BS_SUBSCRIPTION_NAME` |
| `Version or Checksum Mismatch Error` | Concurrent modification detected | Client must send current `checkSum` + `version` from their last response |
| OTel traces not exporting | Collector endpoint unreachable | Check `OTEL_EXPORTER_OTLP_ENDPOINT`, set `OTEL_LOG_LEVEL=DEBUG` for diagnostics |
| Refund API fails | CPG/JusPay token expired or API down | Check logs for token generation errors; JusPay retries 2x automatically |
| `Booking Update Not Allowed` | Vehicle already allocated | Cannot modify vehicle/dealer/booking after allocation |
| Swagger not loading | Service not started or wrong port | Verify `APP_PORT` and access `/api-doc` |

---

## Database Migrations

```bash
# Create a new migration
yarn typeorm:create-migration --name=MigrationName

# Run pending migrations
yarn typeorm:run-migration

# Revert last migration
yarn typeorm:revert-migration
```

> **Note**: `synchronize: false` in production. Schema changes require explicit migrations.

---

## Documentation

| Document | Purpose |
|----------|---------|
| [HIGH_LEVEL_CODE_DOCUMENT.md](./HIGH_LEVEL_CODE_DOCUMENT.md) | Code-level architecture reference |
| [HIGH_LEVEL_DESIGN.md](./HIGH_LEVEL_DESIGN.md) | System design document (HLD) |
| [LOW_LEVEL_DESIGN.md](./LOW_LEVEL_DESIGN.md) | Implementation details (LLD) |
| [API_SPECIFICATION.md](./API_SPECIFICATION.md) | API contracts and payloads |
| `/api-doc` (runtime) | Live Swagger UI |

---

## Maintainers

| Role | Name | Contact |
|------|------|---------|
| Engineering Lead | Suman Kumar | Suman.Kumar@tvsmotor.com |
| Backend Developer | Satyam Ramani (TVS Digital) | Satyam@tvsd.ai |
| Backend Developer | Nivetha Nehru (D&AI/Electronic City/TVSMotor) | Nivetha.Nehru@tvsmotor.com |
| DevOps | Jayasri Uppara | Jayasri.Uppara@tvsmotor.com |
| Product Owner | Prakash Bharati | Prakash.Bharati@tvsmotor.com |
| Support Mail | BS Support | Bs.support@tvsmotor.com |

---

## License

UNLICENSED — Private repository. TVS Motor Company Ltd.
