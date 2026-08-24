# API Specification — Booking CRUD Services

---

## 1. Service Identity

| Field | Value |
|-------|-------|
| Service Name | booking-crud-services |
| Repo | Azure DevOps / TVS Motor Company |
| Team | Common Backend Services |
| Tech Lead | Satyam Ramani |
| Deployment | AKS (Azure Kubernetes Service) |
| Base URL (prod) | `https://apim.tvsmotor.com/booking-service/bookings` |
| Swagger JSON | Auto-generated at `./swagger.json` on startup |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Product Owner | Prakash Bharati | Prakash.Bharati@tvsmotor.com  |
| Tech Lead | Satyam Ramani (TVS Digital) | Satyam@tvsd.ai |
| Dev Team | Common Backend Service| Satyam@tvsd.ai, Nivetha.Nehru@tvsmotor.com |

---

## 2. My API Endpoints (Inbound)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | `/bookings` | API Gateway | Create a booking (online/offline/pre-booking) | EV Website, ICE Website, EMS, DMS, Marketplace (Amazon/Flipkart) |
| PUT | `/bookings` | API Gateway | Update/modify a booking | EMS, DMS, SAP, CRM, EV Website, ICE Website, Marketplace Service |
| POST | `/bookings/bto_status` | API Gateway | Update BTO lifecycle status | SAP |
| POST | `/bookings/search` | API Gateway | Search/retrieve bookings | EMS, DMS, CRM, Admin Portal |
| PUT | `/bookings/cancel` | API Gateway | Cancel a booking | EV Website, ICE Website, EMS, DMS, CRM, Marketplace Service |
| POST | `/bookings/fnfrefund` | API Gateway | Initiate Full-and-Final refund | EV Website, ICE Website, EMS |
| POST | `/bookings/refundstatus` | API Gateway | CPG refund status webhook | CPG (Payment Gateway) |
| POST | `/bookings/juspayrefundstatus` | API Gateway | JusPay refund status webhook | JusPay (Payment Gateway) |
| POST | `/bookings/testbookingtopic` | API Gateway | Test Service Bus publishing | Internal/Dev |
| POST | `/bookings/dms-vehicle-master` | API Gateway | Upsert DMS vehicle master record | DMS |
| GET | `/bookings/health` | None | Health check + DB connectivity | Load Balancer / Monitoring |
| POST | `/bookings/event-repush` | API Gateway | Repush a topic event from logs | Support Operations |
| POST | `/bookings/retry-cancellation` | API Gateway | Retry a failed cancellation | Support Operations |

---

## 3. Outbound (Who I Call)

| Target | Method | Endpoint | Purpose |
|--------|--------|----------|---------|
| CPG Token Service | POST | `https://pay.tvsmotor.com/api/token` | Generate auth token for CPG refund |
| CPG Direct Refund | POST | `https://pay.tvsmotor.com/api/initiate-refund` | Auto refund via CPG |
| CPG FnF Refund | POST | `https://pay.tvsmotor.com/api/initiate-direct-refund` | Full-and-Final refund via CPG |
| JusPay Token Service | POST | `https://login.microsoftonline.com/.../oauth2/v2.0/token` | Generate OAuth2 token for JusPay |
| JusPay Direct Refund | POST | `https://apim.tvsmotor.com/cpg/api/v1/initiate-refund` | Auto refund via JusPay |
| JusPay FnF Refund | POST | `https://apim.tvsmotor.com/cpg/api/v1/initiate-payout` | FnF payout via JusPay |
| Lead System | POST | `https://apim.tvsmotor.com/lead-service/api/lead/update` | Update lead status |
| Azure Service Bus | PUBLISH | `prod.booking` topic | Publish booking lifecycle events |

---

## 4. Events & Messaging

### Topics This Service Publishes To

**Topic**: `prod.booking`

| Event | Targets |
|-------|---------|
| BOOKING_INITIATED | DMS, EMS, LS, ATP, Comms |
| BOOKING_CREATED | DMS, EMS, LS, ATP, Comms |
| BOOKING_CANCELLED | DMS, EMS, LS, ATP, Comms |
| BOOKING_VEHICLE_UPDATED | DMS, EMS, LS |
| BOOKING_DEALER_UPDATED | DMS, EMS, LS |
| CUSTOMER_INFO_UPDATED | DMS, EMS, LS, RS |
| VEHICLE_UPDATED | DMS, EMS, LS, Comms, RS |
| DMS_BOOKING_UPDATE | DMS, EMS, LS, RS |
| INVOICED | DMS, EMS, LS, Comms |
| VEHICLE_ALLOCATION | DMS, EMS, LS |
| VEHICLE_DEALLOCATION | DMS, EMS, LS |
| GATEPASS_UPDATE | DMS, EMS, LS, Comms |
| HSRP_INITIATED | DMS, EMS, LS |
| BOOKING_REFUND_INITIATED | DMS, EMS, LS |
| BOOKING_REFUND_SUCCESS | DMS, EMS, LS |
| BOOKING_REFUND_AWAITED | DMS, EMS, LS |
| BOOKING_REFUND_DECLINED | DMS, EMS, LS |
| BOOKING_REFUND_FAILURE | DMS, EMS, LS |
| FNF_BOOKING_REFUND_INITIATED | DMS, EMS, LS |
| FNF_BOOKING_REFUND_SUCCESS | DMS, EMS, LS |
| FNF_BOOKING_REFUND_DECLINED | DMS, EMS, LS |
| FNF_BOOKING_REFUND_FAILURE | DMS, EMS, LS |

**Format**: JSON (ServiceBusMessage with sessionId = bookingUUID)

### Topics This Service Subscribes To

| Topic | Subscription | Events Consumed | Action |
|-------|--------------|-----------------|--------|
| `prod.booking` | `bs-booking-subscription` | ATP_BOOKING_CREATED, ATP_FULL_PAYMENT_UPDATED | Process ATP booking creation & full payment |
| `prod.atp.booking` | `rm-booking-subscription` | ATP events | Process ATP status updates |
| `prod.dms.booking` | `booking-dms-subscription` | DMS_BOOKING_CREATED | Process DMS integration (offline bookings from dealer) |
| `prod.mdp.dealer_data` | `booking_service` | VEHICLE_CREATED, VEHICLE_UPDATED, DEALER_CREATED, DEALER_UPDATED | Sync dealer/vehicle master data |

---

## 5. External Integrations

| System | Type | Purpose | Auth | Endpoint |
|--------|------|---------|------|----------|
| CPG (TVS Pay) | Payment Gateway | Process refunds (auto + FnF) | ClientCode + encrypted ClientSecret → Bearer token | `https://pay.tvsmotor.com/api/*` |
| JusPay (via APIM) | Payment Gateway | Process refunds (FnF + auto) | OAuth2 client_credentials → Bearer token | `https://apim.tvsmotor.com/cpg/api/v1/*` |
| Lead System (via APIM) | Lead Management | Update lead status on booking events | OAuth2 Bearer + `Ocp-Apim-Subscription-Key` | `https://apim.tvsmotor.com/lead-service/api/lead/update` |
| CCAvenue | Payment Verification | Hash verification for refund webhooks | Access code + working key (MD5 hash) | `https://api.ccavenue.com/apis/servlet/DoWebTrans` |
| Azure AD | Identity | OAuth2 token generation | Client credentials | `https://login.microsoftonline.com/.../oauth2/v2.0/token` |
| Azure Service Bus | Messaging | Pub/sub for booking events | SAS key (from Key Vault) | `sb://tvsmazcmnsvcasbprd01-cin.servicebus.windows.net` |
| Azure Service Bus (MDP) | Messaging | Dealer/vehicle master sync | SAS key (from Key Vault) | `sb://tvsmazeshasbprod01.servicebus.windows.net` |
| Azure Key Vault | Secrets | All service config & keys | Managed Identity / Service Principal | Configured via `KEYVAULT_URL` env var |

---

## 6. Database & Storage

| Store | Type | Purpose |
|-------|------|---------|
| tvsmazebooksdbprd01 | MSSQL (Azure SQL) | Primary booking data (bookings, payments, vehicles, cancellations, refunds, topic logs, journals) |
| Azure Key Vault | Secrets | Service configuration, connection strings, API keys |

### Key Tables

| Table | Purpose |
|-------|---------|
| `booking` | Core booking records |
| `payment` | Payment transactions linked to bookings |
| `vehicle` | Vehicle details per booking |
| `location` | Customer location per booking |
| `booking_cancellation` | Cancellation records |
| `booking_refund` | Refund records (FK to cancellation) |
| `refund_transaction_logs` | Raw refund API request/response logs |
| `booking_topic_log` | Service Bus publish audit trail |
| `booking_journal` | API request/response journal for all operations |
| `product` | Add-on products per booking |
| `sub_orders` | Sub-order records (noise bookings) |
| `dms_vehicle_master` | Synced DMS vehicle catalog |
| `dealer_master` | Synced dealer catalog |

---

## 7. API Details

### 7.1 POST /bookings — Create Booking

**Description**: Creates a new booking (online, offline, or pre-booking).

#### Request Payload

```json
{
  "type": "online",
  "isATPConfigured": true,
  "booking": {
    "bookingSource": "EV Website",
    "homeDeliverySelected": false,
    "bookingType": "vehicle",
    "customer": {
      "name": "John Doe",
      "phone": "9876543210",
      "email": "john@example.com"
    },
    "enquiry": {
      "leadId": "LEAD-456"
    },
    "dealer": {
      "dealerId": "DLR-001",
      "branchId": "BR-001"
    },
    "vehicle": {
      "partId": "PART-001",
      "modelId": "MODEL-001",
      "vehicleType": "EV"
    },
    "location": {
      "cityName": "Chennai",
      "stateName": "Tamil Nadu",
      "bookingPinCode": "600001"
    }
  }
}
```

#### Response (202 Accepted)

```json
{
  "message": "Booking Initiated Successfully",
  "checkSum": "sha256-hash",
  "version": 1,
  "uuid": "abc12def34gh56ij78kl"
}
```

---

### 7.2 PUT /bookings — Update Booking

**Description**: Modifies an existing booking. The `action` field determines the modification type.

#### Request Payload

```json
{
  "action": "payment update",
  "uuid": "abc12def34gh56ij78kl",
  "checkSum": "current-checksum",
  "version": 1,
  "updateSource": "EMS",
  "isATPConfigured": true,
  "bookingUpdate": { }
}
```

#### Response (202 Accepted)

```json
{
  "message": "Payment Update Initiated",
  "checkSum": "new-checksum",
  "version": 2,
  "uuid": "abc12def34gh56ij78kl"
}
```

---

### 7.3 POST /bookings/bto_status — Update BTO Status

**Description**: Updates BTO lifecycle status. Called by SAP.

#### Request Payload

```json
{
  "uuid": "abc12def34gh56ij78kl",
  "btoStatus": "Order Manufactured",
  "btoStatusDate": "2026-06-07T10:30:00.000Z"
}
```

---

### 7.4 PUT /bookings/cancel — Cancel Booking

**Description**: Cancels a booking and initiates refund processing.

#### Request Payload

```json
{
  "uuid": "abc12def34gh56ij78kl",
  "checkSum": "current-checksum",
  "version": 2,
  "isATPConfigured": true,
  "cancellationSource": "EV Website",
  "cancellationReason": "Changed mind",
  "refundAmount": 5000,
  "clientAppUserID": "USER-123"
}
```

---

### 7.5 POST /bookings/fnfrefund — FnF Refund

**Description**: Initiates Full-and-Final refund for a cancelled booking.

#### Request Payload

```json
{
  "uuid": "abc12def34gh56ij78kl",
  "refundPayload": "encrypted-or-plain-refund-payload",
  "clientAppUserID": "USER-123",
  "source": "EV Website"
}
```

---

### 7.6 POST /bookings/refundstatus — CPG Refund Status Webhook

**Called By**: CPG (CCAvenue)

```json
{
  "data": "encrypted-refund-status-payload",
  "clientcode": "ccavenue"
}
```

---

### 7.7 POST /bookings/juspayrefundstatus — JusPay Refund Status Webhook

**Called By**: JusPay

```json
{
  "clientcode": "juspay",
  "clientappuserid": "USER-123",
  "refundamount": 5000,
  "refundstatus": "Success"
}
```

---

### 7.8 GET /bookings/health — Health Check

**Response (200)**: `{ "status": "success", "message": "Booking service is up and database connection verified" }`

---

## 8. Error Responses

| Status | Message | Trigger |
|--------|---------|---------|
| 400 | `Invalid UUID` | Booking not found |
| 400 | `Version or Checksum Mismatch Error` | Optimistic concurrency conflict |
| 400 | `Booking is locked` | version = -1 |
| 400 | `Booking is already cancelled` | version = 0 |
| 400 | `Cancellation is not allowed for initiated bookings` | Non-marketplace, status = Initiated |
| 400 | `Booking is invoiced, cannot cancel` | Marketplace, already invoiced |
| 400 | `Client app userId is empty` | EV Website source without clientAppUserID |
| 400 | `Invalid Request Payload` | Missing required fields |

---

## 9. Observability

| Aspect | Implementation |
|--------|---------------|
| **Logging** | Winston + OpenTelemetry (OTel) → Grafana |
| **Traces** | OTel traces via OTLP → Grafana Tempo |
| **Log Attributes** | `bookingUUID`, `eventType`, `eventTargets`, `status`, `trace_id`, `span_id` |
| **Request/Response Logging** | Global `LoggingInterceptor` logs all API payloads |
| **Publisher Logging** | Every topic publish logs event, targets, UUID, payload, status |
| **Dashboard** | Grafana — filter by `service_name="booking-service"` |

---

