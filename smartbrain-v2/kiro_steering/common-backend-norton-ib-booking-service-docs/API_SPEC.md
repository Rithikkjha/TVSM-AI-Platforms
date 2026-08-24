# API Specification — Booking CRUD Services (International Business)

**Branch**: `main_IB`

---

## 1. Service Identity

| Field | Value |
|-------|-------|
| Service Name | booking-crud-services (IB / Norton) |
| Repo | Azure DevOps — TVSM-CX/booking-crud-services |
| Team | Common Backend Services |
| Tech Lead | Arun Kumar Reddy |
| Deployment | AKS (Docker, Node.js 26 Alpine) |
| Base URL | `/bookings` (v1), `/v2/bookings` (v2) |
| Swagger UI | `{base-url}/api-doc` |
| Global Header | `x-tenant-id` (conditional) |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Product Owner | Prakash Bharati | Prakash.Bharati@tvsmotor.com |
| Tech Lead | Arun Kumar Reddy | Arunkumar.Reddy@tvsd.ai |
| Dev Team | Abhinaya S(Partner - Exathought) | Abhinaya.S@tvsmotor.com |

---

## 2. My API Endpoints (Inbound)

### V1 — `/bookings`

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | `/bookings` | API Gateway + `x-tenant-id` | Create a booking | Website, EMS, DMS, Walk-in, Telephone, Events, Marketplace |
| PUT | `/bookings` | API Gateway + `x-tenant-id` | Update/modify a booking | EMS, DMS, SAP, CRM, Website, Marketplace Service |
| POST | `/bookings/bto_status` | API Gateway | Update BTO status (from SAP) | SAP |
| POST | `/bookings/search` | API Gateway | Search/retrieve bookings | EMS, DMS, CRM, Admin Portal |
| PUT | `/bookings/cancel` | API Gateway | Cancel a booking | Website, EMS, DMS, CRM, Marketplace Service |
| POST | `/bookings/fnfrefund` | API Gateway | Initiate FnF refund | Website, EMS |
| POST | `/bookings/refundstatus` | API Gateway | CPG refund status webhook | CPG (Payment Gateway) |
| POST | `/bookings/juspayrefundstatus` | API Gateway | JusPay refund status webhook | JusPay (Payment Gateway) |
| POST | `/bookings/testbookingtopic` | API Gateway | Test Service Bus publishing | Internal/Dev |
| POST | `/bookings/download` | API Gateway + `x-tenant-id` | Download bookings (CSV/Excel) ★ | EMS, DMS, Admin Portal |
| GET | `/bookings/health` | None | Health check + DB verification | Load Balancer / Monitoring |

### V2 — `/v2/bookings`

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | `/v2/bookings` | API Gateway + `x-tenant-id` | Create booking (auto-generates leadId if missing) | Norton Website |
| PUT | `/v2/bookings` | API Gateway + `x-tenant-id` | Update booking (delegates to V1) | Norton Website |
| POST | `/v2/bookings/bto_status` | API Gateway | Update BTO status (delegates to V1) | SAP |
| POST | `/v2/bookings/search` | API Gateway | Search bookings (delegates to V1) | Norton EMS/DMS |
| PUT | `/v2/bookings/cancel` | API Gateway | Cancel booking (delegates to V1) | Norton Website |
| POST | `/v2/bookings/fnfrefund` | API Gateway | FnF refund (delegates to V1) | Norton Website |
| POST | `/v2/bookings/refundstatus` | API Gateway | CPG webhook (delegates to V1) | CPG |
| POST | `/v2/bookings/juspayrefundstatus` | API Gateway | JusPay webhook (delegates to V1) | JusPay |
| POST | `/v2/bookings/testbookingtopic` | API Gateway | Test publish (delegates to V1) | Internal |
| GET | `/v2/bookings/health` | None | Simple health check | Monitoring |

★ = IB-specific endpoint

---

## 3. Outbound (Who I Call)

| Target | Method | Endpoint | Purpose |
|--------|--------|----------|---------|
| CPG Token Service | POST | `https://pay.tvsmotor.com/api/token` | Generate auth token for CPG refund |
| CPG Direct Refund | POST | `https://pay.tvsmotor.com/api/initiate-refund` | Auto refund via CPG |
| CPG FnF Refund | POST | `https://pay.tvsmotor.com/api/initiate-direct-refund` | Full-and-Final refund via CPG |
| JusPay Token Service | POST | Azure AD OAuth2 endpoint | Generate OAuth2 token for JusPay |
| JusPay Direct Refund | POST | `https://apim.tvsmotor.com/cpg/api/v1/initiate-refund` | Auto refund via JusPay |
| JusPay FnF Payout | POST | `https://apim.tvsmotor.com/cpg/api/v1/initiate-payout` | FnF payout via JusPay |
| Lead System | POST | `https://apim.tvsmotor.com/lead-service/api/lead/update` | Update lead status |
| Azure Service Bus | PUBLISH | Booking Topic | Publish booking lifecycle events |

---

## 4. Events & Messaging

### Topics This Service Publishes To

**Topic**: `prod.booking`

| Event | Targets |
|-------|---------|
| BOOKING_INITIATED | DMS, EMS, LS, Comms, TNH |
| BOOKING_CREATED | DMS, EMS, LS, ATP, Comms, RS (conditional) |
| FULL_PAYMENT_UPDATED | DMS, EMS, LS, ATP, Comms, RS (conditional) |
| FAILED_PAYMENT_UPDATE | DMS, EMS, LS, Comms |
| BOOKING_CANCELLED | DMS, EMS, LS, Comms |
| VEHICLE_UPDATED | DMS, EMS, LS, Comms, TNH, ATP (if configured) |
| CUSTOMER_INFO_UPDATED | DMS, EMS, LS, Comms, TNH |
| BOOKING_DEALER_UPDATED | DMS, EMS, LS, RS (conditional) |
| DMS_BOOKING_UPDATE | DMS, EMS, LS, Comms, TNH |
| INVOICED | EMS, LS, DMS, Comms, TNH, RS (conditional), MARKETPLACE_SERVICE (conditional) |
| INVOICE_CANCEL | EMS, LS, DMS, Comms, TNH, RS (conditional), MARKETPLACE_SERVICE (conditional) |
| VEHICLE_ALLOCATION | LS, EMS, DMS, Comms, TNH, ATP (if BTO + configured) |
| VEHICLE_DEALLOCATION | LS, EMS, DMS, Comms, TNH |
| GATEPASS_UPDATE | DMS, EMS, LS, Comms, TNH, MARKETPLACE_SERVICE (conditional) |
| RETAIL_FINANCE_UPDATE | DMS, EMS, TNH |
| ORDER_MANUFACTURED | DMS, EMS, LS, ATP (if configured) |
| ORDER_PACKED | DMS, EMS, LS, ATP (if configured) |
| ORDER_DISPATCHED | DMS, EMS, LS, ATP (if configured) |
| ORDER_AT_DEALERSHIP | DMS, EMS, LS, ATP (if configured) |
| BOOKING_REFUND_INITIATED | DMS, EMS, LS |
| BOOKING_REFUND_SUCCESS | DMS, EMS, LS |
| BOOKING_REFUND_FAILURE | DMS, EMS, LS |
| FNF_BOOKING_REFUND_INITIATED | DMS, EMS, LS |
| FNF_BOOKING_REFUND_SUCCESS | DMS, EMS, LS |
| FNF_BOOKING_REFUND_FAILURE | DMS, EMS, LS |

**Conditional targets:**
- `RS` — added when bookingSource is NOT DMS, MARKETPLACE_AMAZON, or MARKETPLACE_FLIPKART
- `MARKETPLACE_SERVICE` — added for marketplace bookings (GATEPASS, INVOICE, INVOICE_CANCEL)
- `ATP` — added when `isATPConfigured = true`
- `TNH` — added for Norton-specific events

**Format**: JSON (ServiceBusMessage with sessionId = bookingUUID)

### Topics This Service Subscribes To

| Topic | Subscription | Events Consumed | Action |
|-------|--------------|-----------------|--------|
| `prod.booking` | `bs-booking-subscription` | BOOKING_CANCELLED, BOOKING_REFUND_CCAVENUE_STATUS | Auto-refund processing, CCAvenue status update |
| ATP Topic | ATP subscription | ATP vehicle ETA, Comms, milestone changes, full payment enable | Update vehicle ETA, process ATP events |
| DMS Topic | DMS subscription | DMS_BOOKING_CREATED | Process DMS integration (offline bookings) |
| MDP Dealer Topic | `booking_service` | VEHICLE_CREATED, VEHICLE_UPDATED, DEALER_CREATED, DEALER_UPDATED, LLP_DEALER_CREATED, LLP_DEALER_UPDATED | Sync dealer/vehicle master data |

> **Note**: ATP and DMS listeners skip initialization if their Service Bus endpoint is empty (Norton use case where these topics may not exist).

---

## 5. External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| CPG (TVS Pay) | Payment Gateway | Process refunds (auto + FnF) | ClientCode + encrypted ClientSecret → Bearer token |
| JusPay (via APIM) | Payment Gateway | Process refunds (FnF + auto) | OAuth2 client_credentials → Bearer token |
| CCAvenue | Payment Verification | Hash verification for refund webhooks | Access code + working key (MD5 hash) |
| Lead System (via APIM) | Lead Management | Update lead status | OAuth2 Bearer + `Ocp-Apim-Subscription-Key` |
| Azure AD | Identity | OAuth2 token generation | Client credentials |
| Azure Service Bus | Messaging | Pub/sub for booking events | SAS key (from Key Vault) |
| Azure Key Vault | Secrets | All service config & keys | Managed Identity / Service Principal |
| OTel Collector | Observability | Traces + Logs export | None |

---

## 6. Database & Storage

| Store | Type | Purpose |
|-------|------|---------|
| Azure SQL (MSSQL) | Database | Primary booking data + IB-specific tables |
| Redis (ioredis) | Cache | Dealer/product master data |
| Azure Key Vault | Secrets | Connection strings, API keys, crypto keys |

### Key Tables (IB-Specific)

| Table | Purpose |
|-------|---------|
| `booking` | Core booking records (includes `tenant_id`, `dse_name` columns) |
| `booking_id_sequence` | Atomic daily sequence for NBK-YYMMDD-XXXXX IDs |
| `country_master` | Tenant registry (countryCode, tenantId, countryName) |
| `brand_master` | Brand validation for reservation bookings (brandCode, modelName, tenantId) |
| `invoice` | Normalized invoice storage (bookingUUID, invoiceId, vehicleId, productId, tenant_id) |

---

## 7. IB-Specific Features

### Booking ID Format
```
NBK-YYMMDD-XXXXX
Example: NBK-260709-00001
```

### Multi-Tenancy
- Header: `x-tenant-id`
- Middleware: AsyncLocalStorage propagation
- Validation: Against `country_master` table
- Config: `TENANT_ID_REQUIRED` env var (true/false)

### State Machine (Status Transitions)

**Normal Bookings:**
```
Initiated → Confirmed, Cancelled
Confirmed → Ordered, Partially Invoiced, Cancelled, Invoiced, Allocated
Ordered → Allocated, Cancelled
Allocated → Invoiced, Cancelled, Partially Invoiced
Partially Invoiced → Invoiced, Cancelled
Invoiced → Partially Delivered, Delivered
Partially Delivered → Delivered, Cancelled
```

**Reservation Bookings (Website Reservation):**
```
Reserved → Confirmed, Cancelled
(then same as Normal from Confirmed onwards)
```

### Download Endpoint
- `POST /bookings/download`
- Formats: CSV (UTF-8 with BOM) or Excel (.xlsx)
- Streaming response (batches of 500)
- Validates dealer belongs to tenant


