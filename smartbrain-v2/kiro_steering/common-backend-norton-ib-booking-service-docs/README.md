# Booking CRUD Services (International Business)

**Branch**: `main_IB`

Backend microservice for TVS Motor's international vehicle booking platform. Extends the domestic booking service with multi-tenant support, structured booking IDs, state machine validation, reservation flows, and data export.

**Tech Stack**: NestJS 11 · TypeScript · TypeORM · Azure SQL (MSSQL) · Azure Service Bus · Azure Key Vault · OpenTelemetry · ExcelJS

---

## What's Different from Domestic (`main`)

| Feature | Domestic (`main`) | IB (`main_IB`) |
|---------|-------------------|----------------|
| Booking ID | Truncated UUIDv4 (20 chars) | `NBK-YYMMDD-XXXXX` (DB sequence) |
| Multi-tenancy | None | `x-tenant-id` header + CountryMaster validation |
| Status transitions | Implicit (service sets directly) | State machine validation |
| Booking sources | EV/ICE Website, EMS, DMS | + Website, Reservation, Walk-in, Telephone, Events |
| Booking statuses | Initiated, Open, Invoiced, Delivered | + Reserved, Confirmed, Ordered, Allocated, Partially Invoiced/Delivered |
| Download | None | CSV/Excel streaming export |
| Reservation flow | None | Reserved → Confirmed → ... with brand validation |
| Duplicate check | leadId only | + customerPhone + source (marketplace) |
| Line-item validation | None | vehicleId + productIds validated |

---

## Setup Instructions

### Prerequisites

- Node.js 26.x
- Yarn 1.x
- Access to Azure Key Vault
- Azure AD service principal credentials
- `country_master` table populated with tenant records
- `brand_master` table populated (for reservation bookings)

### Installation

```bash
git checkout main_IB
yarn install
```

---

## Local Development

```bash
yarn start:dev
```

- **Swagger UI**: http://localhost:{PORT}/api-doc
- **Health Check**: http://localhost:{PORT}/bookings/health

---

## Environment Variables

All domestic variables apply, plus:

| Variable | Description | Required |
|----------|-------------|----------|
| `TENANT_ID_REQUIRED` | `true` = `x-tenant-id` header is mandatory | ✅ |
| `DEFAULT_TENANT_ID` | Fallback tenant if header not required | Conditional |

---

## Build & Deploy

```bash
# Build
yarn build

# Docker
docker build -t booking-crud-services-ib .
docker run -p 8080:8080 --env-file .env booking-crud-services-ib
```

Same CI/CD pipelines as domestic (DEV → UAT → PROD).

---

## Testing

```bash
yarn test          # Unit tests
yarn test:cov      # Coverage
yarn test:e2e      # End-to-end
```

---

## Folder Structure (IB Additions)

```
src/
├── bookings/
│   ├── middleware/
│   │   └── tenant.context.ts          ★ AsyncLocalStorage for tenant
│   └── services/
│       ├── booking-creation/
│       │   └── booking-id-generation/  ★ NBK-YYMMDD-XXXXX generator
│       ├── booking-retrieval/
│       │   └── booking-download.service.ts  ★ CSV/Excel streaming
│       ├── state-transition-validator/ ★ Status state machine
│       └── tenant/                     ★ Tenant resolution service
│
├── database/entities/
│   ├── booking-id-sequence.entity.ts   ★ Daily sequence table
│   ├── country-master.entity.ts        ★ Tenant registry
│   ├── brand-master.entity.ts          ★ Brand validation
│   └── invoice.entity.ts              ★ Normalized invoices
```

---

## Key API Differences

### New Endpoint
- `POST /bookings/download` — Stream booking data as CSV or Excel

### Modified Behavior
- `POST /bookings` — validates tenant, generates `NBK-*` ID, checks duplicate phone
- `PUT /bookings` — validates line-item IDs, enforces state machine transitions
- `GET /bookings/health` — accepts optional `partid`/`modelid` headers

### New Header
```
x-tenant-id: IN
```

---

## Common Troubleshooting

| Issue | Fix |
|-------|-----|
| "Invalid tenant ID" | Ensure `x-tenant-id` header sent and tenant exists in `country_master` |
| "Dealer does not belong to tenant" | Dealer's `tenantId` must match header |
| "Invalid status transition" | Check state machine rules in `StateTransitionValidatorService` |
| "brandCode is required" | Reservation bookings need `vehicle.brandCode` |
| "Booking is open" (on create) | Marketplace duplicate: same phone already has Confirmed booking |
| Download timeout | Large date ranges; narrow the filter or add status filter |

---

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/IB/HLC.md](../IB/HLC.md) | High-Level Code Document (IB) |
| [docs/IB/HLD.md](../IB/HLD.md) | High-Level Design (IB) |
| [docs/IB/LLD.md](../IB/LLD.md) | Low-Level Design (IB) |
| [docs/IB/API_SPEC.md](../IB/API_SPEC.md) | API Specification (IB) |

---

## Maintainers

| Role | Name | Contact |
|------|------|---------|
| Tech Lead | Arun Kumar Reddy | Arunkumar.Reddy@tvsd.ai |
| Backend Dev | Abhinaya S(Partner - Exathought) | Abhinaya.S@tvsmotor.com |

---

## License

UNLICENSED — Private repository. TVS Motor Company Ltd.
