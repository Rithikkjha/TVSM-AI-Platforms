# Booking CRUD Services (International Business) — High-Level Code Document

**Branch**: `main_IB`

---

## 1. Application Overview

Booking CRUD Services (IB) is the international variant of the vehicle booking microservice for TVS Motor Company. It extends the domestic booking platform to support **multi-tenant, multi-country** operations with additional features like structured booking IDs, tenant-based access control, state machine validation, reservation bookings, and data export capabilities.

| Attribute | Value |
|-----------|-------|
| **Service Name** | booking-crud-services (IB) |
| **Branch** | `main_IB` |
| **Framework** | NestJS 11 (TypeScript) |
| **Runtime** | Node.js 26.x |
| **Database** | Azure SQL (MSSQL) via TypeORM |
| **Messaging** | Azure Service Bus (topics with sessions) |
| **Multi-Tenancy** | Header-based (`x-tenant-id`) with CountryMaster validation |
| **Booking ID Format** | `NBK-YYMMDD-00001` (sequential per day) |
| **API Docs** | Swagger at `/api-doc` |

**IB-Specific Capabilities (vs Domestic)**:
- Multi-tenant architecture with `x-tenant-id` header and CountryMaster validation
- Structured booking ID generation (`NBK-YYMMDD-XXXXX`) replacing truncated UUIDs
- State machine-based status transitions (normal + reservation booking flows)
- Reservation booking type (`Website Reservation`) with brand validation
- Booking data download (CSV/Excel streaming)
- Duplicate booking prevention per customer phone + source
- Product/dealer validation with optional `brandCode`
- Line-item-level vehicle/product ID validation for updates

---

## 2. Module Summary

| Module | Responsibility |
|--------|----------------|
| **AppModule** | Root module — ConfigModule, TypeORM (MSSQL + Azure AD), feature modules |
| **BookingsModule** | Core business logic — controller, 60+ services, all entities |
| **CloudConductorModule** | Azure infrastructure — Key Vault, Service Bus pub/sub, model transformer |
| **LoggingModule** | Winston-based logging |

### IB-Specific Services (New in this branch)

| Service | File | Purpose |
|---------|------|---------|
| `TenantService` | `services/tenant/tenant.service.ts` | Resolves tenant ID from `AsyncLocalStorage` context or default config |
| `BookingIdGenerationService` | `services/booking-creation/booking-id-generation/booking-id-generation.service.ts` | Generates `NBK-YYMMDD-XXXXX` IDs using DB sequence (MERGE with HOLDLOCK) |
| `StateTransitionValidatorService` | `services/state-transition-validator/state-transition-validator.service.ts` | Validates booking status transitions against allowed state machine |
| `BookingDownloadService` | `services/booking-retrieval/booking-download.service.ts` | Streams booking data as CSV/Excel with batch pagination |

### IB-Specific Entities (New)

| Entity | Purpose |
|--------|---------|
| `BookingIdSequence` | Daily sequence counter for booking ID generation |
| `CountryMaster` | Tenant/country registry for multi-tenant validation |
| `BrandMaster` | Brand registry for reservation booking validation |
| `Invoice` | Separate invoice entity (vs JSON column in domestic) |

---

## 3. Dependency Overview

### Additional IB Dependencies (beyond domestic)

| Package | Purpose |
|---------|---------|
| `exceljs` | Excel file generation for booking download |
| `async_hooks` (Node built-in) | AsyncLocalStorage for tenant context propagation |

### Common Commands

| Command | Action |
|---------|--------|
| `yarn build` | Compile + copy + install prod deps |
| `yarn test` | Run unit tests |
| `yarn test:cov` | Tests with coverage |
| `yarn lint` | ESLint with auto-fix |
| `yarn start:dev` | Dev server with hot-reload |

---

## 4. Runtime Flow

### Bootstrap (same as domestic + tenant middleware)

```
1. Start OpenTelemetry SDK
2. Create NestJS application
3. Register GlobalExceptionFilter
4. Register Tenant Middleware (extracts x-tenant-id → AsyncLocalStorage)
5. Generate Swagger → mount at /api-doc
6. Register global ValidationPipe (whitelist: true)
7. Start HTTP server
```

### Request Processing (IB-specific additions highlighted with ★)

```
HTTP Request (with x-tenant-id header)
  ★ Tenant Middleware → extract tenant → store in AsyncLocalStorage
  → Controller
  ★ → validateTenantId() — verify against CountryMaster table
  ★ → validateOpenBookingByCustomerNumber() — duplicate check for marketplace
  ★ → BookingIdGenerationService.generate() — NBK-YYMMDD-XXXXX
  → BookingFactoryService.resolve(type/action)
  → Domain Service.process()
  ★ → StateTransitionValidatorService (if bookingStatus change requested)
  ★ → validateVehicleUpdateProductIds() — line-item ID validation
  → Repository → DB → Publisher → Journal
```

### Booking ID Generation Algorithm

```sql
MERGE booking_id_sequence WITH (HOLDLOCK) AS target
USING (SELECT CAST(@date AS DATE) AS sequence_date) AS source
  ON target.sequence_date = source.sequence_date
WHEN MATCHED THEN UPDATE SET last_seq = last_seq + 1
WHEN NOT MATCHED THEN INSERT (sequence_date, last_seq) VALUES (@date, 1)
OUTPUT INSERTED.last_seq;

Result: NBK-260607-00001, NBK-260607-00002, ...
```

### State Machine (Normal Booking)

```
Initiated → Confirmed → Ordered → Allocated → Invoiced → Delivered
                ↓                      ↓           ↓
            Cancelled              Cancelled   Partially Invoiced → Invoiced
                                                                       ↓
                                                               Partially Delivered → Delivered
```

### State Machine (Reservation Booking)

```
Reserved → Confirmed → Ordered → Allocated → Invoiced → Delivered
    ↓          ↓                     ↓           ↓
 Cancelled  Cancelled            Cancelled   Partially Invoiced → Invoiced
```

---

## 5. Key Services

### IB-Specific Services

| Service | Trigger | Core Logic |
|---------|---------|------------|
| `TenantService` | Every request | Reads `x-tenant-id` from AsyncLocalStorage; falls back to `DEFAULT_TENANT_ID` if not mandatory |
| `BookingIdGenerationService` | Booking creation + dealer change | MERGE-based atomic sequence per UTC date; format: `NBK-YYMMDD-XXXXX` |
| `StateTransitionValidatorService` | Modification with `bookingStatus` field | Validates transition against allowed map; different rules for reservation vs normal |
| `BookingDownloadService` | `POST /bookings/download` | Streams CSV/Excel in batches of 500; filters by dealer, branch, date, status |

### Modified Validation Rules (IB vs Domestic)

| Validation | Domestic | IB |
|-----------|----------|-----|
| Tenant validation | None | `x-tenant-id` header validated against `CountryMaster` table |
| Duplicate booking | By leadId only | By leadId + by customerPhone + bookingSource (marketplace) |
| Status transitions | Implicit (set by service) | Explicit state machine with `StateTransitionValidatorService` |
| Product validation | partId + modelId | partId + modelId + optional brandCode |
| Line-item IDs | Not validated | vehicleId + productIds validated against booking's records |
| Dealer-tenant check | None | `validateDealerTenant()` — dealer must belong to tenant |
| Booking ID | Truncated UUIDv4 (20 chars) | `NBK-YYMMDD-XXXXX` (DB sequence) |

---

## 6. Integration Summary

### IB-Specific Endpoints (New)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bookings/download` | Download booking data as CSV or Excel stream |

### IB-Specific Headers

| Header | Required | Purpose |
|--------|----------|---------|
| `x-tenant-id` | Conditional (configurable via `TENANT_ID_REQUIRED`) | Multi-tenant identification |

### Additional Booking Sources (IB)

- `Website` (generic international website)
- `Website Reservation` (reservation flow with brand validation)
- `Walk-in`
- `Telephone`
- `Events`
- `Others`

### Additional Booking Statuses (IB)

- `Reserved` (reservation flow initial state)
- `Confirmed` (replaces `Open` from domestic)
- `Ordered`
- `Allocated`
- `Partially Invoiced`
- `Partially Delivered`

---
