# High Level Design — Booking CRUD Services (International Business)

**Branch**: `main_IB`

---

## Overview

Booking CRUD Services (IB) is the international variant of TVS Motor's vehicle booking microservice. It extends the domestic platform with multi-tenant support, structured booking IDs, state-machine-based status validation, reservation booking flows, and data export capabilities — serving international dealer networks across multiple countries.

---

## Tier Classification

**Tier 1: Mission Critical Application**

---

## Background

The IB branch was created to support TVS Motor's international expansion. Key drivers:

- Multi-country operations require tenant isolation and country-specific configuration
- International dealers need structured booking IDs (`NBK-YYMMDD-XXXXX`) instead of opaque UUIDs
- Different markets have different booking flows (normal vs reservation)
- Regulatory requirements demand explicit state machine validation for status transitions
- International operations need bulk data export (CSV/Excel) for reporting

---

## Requirements

### Functional (IB-Specific)

- Multi-tenant support via `x-tenant-id` header with CountryMaster validation
- Structured booking ID generation (daily sequence, format: `NBK-YYMMDD-XXXXX`)
- Reservation booking flow (Reserved → Confirmed → Ordered → Allocated → Invoiced → Delivered)
- State machine validation for all status transitions
- Brand validation for reservation bookings
- Booking data download as CSV or Excel (streaming, paginated)
- Duplicate booking prevention per customer phone number + source
- Line-item-level product/vehicle ID validation
- Dealer-tenant association validation

### Non-Functional

- Same as domestic (10s timeout, eventual consistency, OTel tracing, journaling)
- Additional: tenant context propagation via AsyncLocalStorage
- Additional: atomic booking ID generation with HOLDLOCK (no duplicates under concurrency)

---

## System Architecture

```mermaid
flowchart TD
    subgraph clients["Clients"]
        direction LR
        c1["Website"] ~~~ c2["EMS"] ~~~ c3["DMS"] ~~~ c4["SAP"] ~~~ c5["Marketplace"] ~~~ c6["CPG Webhook"] ~~~ c7["JusPay Webhook"]
    end

    subgraph sb_in["Inbound Service Bus Topics"]
        direction LR
        t1["DMS Topic"] ~~~ t2["ATP Topic"] ~~~ t3["MDP Dealer Topic"] ~~~ t4["Booking Topic"]
    end

    subgraph service["Booking CRUD Service (IB)"]
        direction TB
        api["REST API Layer<br/>V1: /bookings | V2: /v2/bookings<br/>+ Tenant Middleware"]
        svc["Service Layer<br/>TenantSvc → Factory → Domain Services<br/>→ StateValidator → Repos → Publishers"]
        api --> svc
    end

    subgraph infra["Infrastructure"]
        direction LR
        kv["Azure Key Vault"]
        sql[("Azure SQL<br/>+ CountryMaster<br/>+ BrandMaster<br/>+ BookingIdSequence")]
        redis[("Redis Cache")]
        otel["OTel Collector"]
    end

    subgraph ext["External APIs"]
        direction LR
        cpg["CPG Gateway"]
        jp["JusPay Gateway"]
        ls["Lead System"]
    end

    sb_out["Service Bus Topic (Outbound)"]

    subgraph consumers["Event Consumers"]
        direction LR
        o1["LS"] ~~~ o2["EMS"] ~~~ o3["DMS"] ~~~ o4["Comms"] ~~~ o5["ATP"] ~~~ o6["RS"] ~~~ o7["TNH"]
    end

    clients -->|HTTPS REST| service
    sb_in -->|Subscribe| service
    service --> sql
    service --> redis
    service --> kv
    service --> otel
    service --> ext
    service --> sb_out
    sb_out --> consumers
```

---

## IB-Specific Components (★ = new vs domestic)

| Component | Technology | Role |
|-----------|-----------|------|
| ★ **Tenant Middleware** | AsyncLocalStorage | Extracts `x-tenant-id` header, propagates via request context |
| ★ **TenantService** | NestJS Injectable | Resolves tenant from context or config fallback |
| ★ **BookingIdGenerationService** | SQL MERGE + HOLDLOCK | Atomic daily sequence for `NBK-YYMMDD-XXXXX` |
| ★ **StateTransitionValidatorService** | State machine maps | Validates status change legality per booking type |
| ★ **BookingDownloadService** | ExcelJS + PassThrough streams | Batch-paginated CSV/Excel export |
| ★ **V2 Controller** | NestJS Controller | `/v2/bookings` — auto-generates leadId, delegates to V1 |
| ★ **CountryMaster entity** | TypeORM | Tenant registry |
| ★ **BrandMaster entity** | TypeORM | Brand validation for reservations |
| ★ **BookingIdSequence entity** | TypeORM | Daily sequence counter table |
| ★ **Invoice entity** | TypeORM | Normalized invoice storage |

### Pros
- Multi-tenant isolation enables single deployment for all countries
- State machine prevents invalid status transitions at validation layer
- Structured booking IDs are human-readable and debuggable
- Download feature reduces need for direct DB access by operations teams

### Cons
- Additional DB round-trip for tenant validation on every request
- Booking ID generation holds DB lock briefly (potential bottleneck at extreme scale)
- State machine adds complexity for every new status or booking type

---

## Data Flow / Sequence Diagrams

### 1. Multi-Tenant Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant TM as Tenant Middleware
    participant TS as TenantService
    participant Ctrl as Controller
    participant Val as ValidationService
    participant DB as CountryMaster DB

    C->>TM: POST /bookings (x-tenant-id: IN)
    TM->>TS: store tenantId in AsyncLocalStorage
    TS-->>TM: stored
    TM->>Ctrl: next()
    Ctrl->>Val: validateTenantId(tenantId)
    Val->>DB: findOne(tenantId)
    DB-->>Val: record or null
    alt Tenant not found
        Val-->>Ctrl: throw InvalidTenantIdException
    else Tenant valid
        Val-->>Ctrl: validated
        Ctrl->>Ctrl: proceed with business logic
    end
```

### 2. Booking ID Generation

```mermaid
sequenceDiagram
    participant Ctrl as Controller
    participant Gen as BookingIdGenerationService
    participant DB as Azure SQL (booking_id_sequence)

    Ctrl->>Gen: generate()
    Gen->>DB: MERGE WITH HOLDLOCK on sequence_date
    Note over DB: Atomic: INSERT(1) or UPDATE(+1)
    DB-->>Gen: OUTPUT INSERTED.last_seq
    Gen-->>Ctrl: "NBK-260709-00003"
```

### 3. State Machine Validation

```mermaid
sequenceDiagram
    participant Ctrl as Controller
    participant Val as ValidationService
    participant SM as StateTransitionValidator

    Ctrl->>Val: validateVersionAndChecksum(request)
    Val->>Val: check version + checksum match
    alt bookingStatus changed
        Val->>SM: validateStatusTransition(current, requested, source)
        SM->>SM: lookup allowed transitions
        alt Invalid transition
            SM-->>Val: throw BadRequestException with valid options
        else Valid transition
            SM-->>Val: OK
        end
    end
    Val-->>Ctrl: proceed
```

### 4. Booking Download (CSV/Excel Streaming)

```mermaid
sequenceDiagram
    participant C as Client
    participant Ctrl as Controller
    participant Val as ValidationService
    participant DL as BookingDownloadService
    participant DB as Database

    C->>Ctrl: POST /bookings/download
    Ctrl->>Val: validateTenantId(tenantId)
    Ctrl->>Val: validateDealerTenant(dealerId, tenantId)
    Val-->>Ctrl: OK
    Ctrl->>DL: resolveDateRange(startDate, endDate)
    Ctrl->>DL: streamCSV() or streamExcel()
    loop Batch of 500
        DL->>DB: SELECT bookings (offset, limit 500)
        DB-->>DL: results
        DL->>C: write to stream (chunked)
    end
    DL->>C: stream end
```

### 5. Creation, Modification, Cancellation

Same as domestic (see `docs/HLD.md`) with these IB additions:
- **Creation**: `BookingIdGenerationService.generate()` replaces `generateUUID()`
- **Creation**: `validateTenantId()` + `validateOpenBookingByCustomerNumber()` called first
- **Modification**: `validateVehicleUpdateProductIds()` validates line-item IDs
- **Modification**: `StateTransitionValidatorService` validates bookingStatus changes
- **V2 Create**: Auto-generates `leadId` if not provided

---

## Scalability Approach

| Aspect | Strategy |
|--------|----------|
| **Concurrent bookings** | Optimistic concurrency (UUID + checksum + version) — no DB-level locks for reads |
| **Booking ID generation** | HOLDLOCK scope limited to single row per day — minimal contention |
| **Download large datasets** | Streaming with batches of 500 — constant memory regardless of result size |
| **Service Bus processing** | MDP listener: serial session processing. ATP/DMS: session-per-message with infinite retry loop |
| **Multi-tenant** | Single deployment serves all tenants — horizontal scaling via container replicas |
| **External API calls** | JusPay token cached (TTL-based, singleton). CPG per-request. Fire-and-forget publishing via `setImmediate` |
| **HTTP timeout** | 10 seconds — prevents slow requests from blocking the pool |

---

## Error Handling Strategy

| Layer | Strategy |
|-------|----------|
| **HTTP Validation** | `ValidationPipe` with `whitelist: true` — rejects unknown/invalid fields with 400 |
| **Business Validation** | Custom exceptions (`InvalidUUIDException`, `BookingLockedException`, etc.) → re-thrown as 400 |
| **State Machine** | Invalid transitions throw `BadRequestException` with valid options listed |
| **Tenant Errors** | Missing/invalid tenant → `InvalidTenantIdException` (400) |
| **External API Failures** | CPG: fail-fast (no retry). JusPay: 2 attempts with 300ms backoff |
| **Service Bus Listeners** | Messages abandoned on error → Service Bus redelivers (up to max delivery count) |
| **Service Bus Publish** | Failures logged to `BookingTopicLog` with status "failed" — no retry (eventual consistency) |
| **Transaction Rollback** | Cancellation workflow uses QueryRunner transaction — rolls back on failure |
| **Global Exception Filter** | Catches unhandled exceptions → returns structured `{statusCode, message, timestamp}` |
| **Graceful Shutdown** | SIGINT/SIGTERM → close app → shutdown OTel → exit |

---

## Deployment Topology

```mermaid
graph TB
    subgraph "Azure Cloud"
        subgraph "Compute"
            Container["Docker Container<br/>Node.js 26 Alpine<br/>Port: 8080<br/>Timeout: 10s"]
        end

        subgraph "Data"
            SQL[("Azure SQL (MSSQL)")]
            Redis[("Redis Cache")]
        end

        subgraph "Messaging"
            SB["Azure Service Bus<br/>4 Topics (session-based)"]
        end

        subgraph "Security"
            KV["Azure Key Vault"]
            AD["Azure AD (Service Principal)"]
        end

        subgraph "Observability"
            OTel["OTel Collector<br/>Traces + Logs"]
        end

        subgraph "CI/CD (Azure DevOps)"
            DEV["DEV Pipeline"] --> UAT["UAT Pipeline"]
            UAT --> PROD["PROD Pipeline"]
        end
    end

    Container -->|TypeORM| SQL
    Container -->|ioredis| Redis
    Container -->|pub/sub| SB
    Container -->|secrets| KV
    KV -->|auth| AD
    Container -->|OTLP HTTP| OTel
```

### Environments

| Environment | Pipeline |
|-------------|----------|
| DEV | `AST_Website_Corporate_booking_crud_services_DEV_Pipeline.yml` |
| UAT | `azure-pipelines/ast-booking-crud-uat-pipeline.yaml` |
| PROD | `azure-pipelines/ast-booking-crud-prod-pipeline.yaml` |

### IB-Specific Configuration

| Variable | Purpose |
|----------|---------|
| `TENANT_ID_REQUIRED` | `true` = `x-tenant-id` header mandatory; `false` = use fallback |
| `DEFAULT_TENANT_ID` | Fallback tenant ID when header not required |
| `IS_NORTON_BOOKING` | Controls Norton-specific event target routing |

---

## Key Design Decisions

| Decision | Chosen | Alternative | Reason |
|----------|--------|-------------|--------|
| Booking ID | DB MERGE + HOLDLOCK | Redis INCR | DB guarantees uniqueness; Redis risks duplicates on failure |
| Multi-Tenancy | `x-tenant-id` header | URL-path-based (`/{tenantId}/bookings`) | Simpler, backward-compatible API routes |
| State Machine | Hardcoded maps in code | DB-configurable transitions | Simpler, version-controlled; not enough states to justify DB |
| Download | ExcelJS streaming + PassThrough | Generate full file in memory | Memory-safe for large datasets |
| V2 API | Separate controller delegating to V1 | Duplicate logic | DRY — V2 only adds leadId auto-generation |

---

## Metrics to be Tracked

| Category | Metric |
|----------|--------|
| **Availability** | Health check uptime (`GET /bookings/health`) |
| **Latency** | API response time per endpoint (OTel traces) |
| **Multi-Tenancy** | Requests per tenant, invalid tenant rejections |
| **Booking IDs** | Sequence generation rate, lock contention |
| **Downloads** | Download requests per dealer, file sizes, stream durations |
| **State Machine** | Invalid transition attempts (signals integration issues) |
| **Messaging** | Publish success/failure rate (from BookingTopicLog) |
| **Refunds** | CPG/JusPay API call success/failure/latency |

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Booking ID lock contention | Slow ID generation under burst traffic | HOLDLOCK is brief; sequence per day limits contention |
| Tenant header missing | Request rejected or wrong tenant | `TENANT_ID_REQUIRED` config + `DEFAULT_TENANT_ID` fallback |
| State machine mismatch | Valid operations rejected | Comprehensive transition maps + clear error messages |
| Download OOM for large datasets | Service crash | Streaming with batches of 500, never loads all into memory |
| ATP/DMS listener not configured | Listener fails to start | Skip initialization if endpoint is empty (Norton use case) |

---

## Appendix

### IB-Specific Glossary

| Term | Meaning |
|------|---------|
| **NBK** | Norton Booking (booking ID prefix) |
| **Tenant** | Country/region identifier for multi-tenant isolation |
| **Reservation Booking** | Website Reservation flow with brand validation and Reserved initial state |
| **State Machine** | Allowed status transition map per booking type |
| **PAM** | Parts, Accessories, Merchandise (booking type) |
| **TNH** | Norton event target (TVS Norton Holdings) |

### Booking ID Format

```
NBK-YYMMDD-XXXXX
 │    │       │
 │    │       └── 5-digit zero-padded daily sequence
 │    └────────── UTC date (year-month-day)
 └─────────────── Fixed prefix (Norton Booking)
```
---
