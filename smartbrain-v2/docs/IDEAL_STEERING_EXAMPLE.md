# booking-crud-services

*Ideal steering file — what we should aim for*

## Service Overview
- **Language:** TypeScript / Node.js (NestJS 11.1.17)
- **Owner:** team-cbs (psnarkhedetvs, paras0602, Dinesh-sb-28)
- **Purpose:** Centralized booking management system for TVS Motor Company. Consolidates bookings from website, dealer systems, and third-party apps into a single service. Handles the full booking lifecycle: creation, modification, cancellation, refunds, and vehicle allocation.
- **Domain:** booking, vehicle, dealer, payment, refund, cancellation, invoice, customer, BTO (build-to-order)
- **APIM Gateway:** `https://apim.tvsmotor.com/booking-service/bookings`

## Code Structure
```
src/
├── bookings/
│   ├── controllers/        ← REST API (single controller)
│   ├── dto/                ← Request/Response DTOs (40+ files)
│   ├── services/
│   │   ├── booking-creation/       ← Online + offline booking flows
│   │   ├── booking-modification/   ← Updates: vehicle, dealer, payment, invoice, gate-pass
│   │   ├── booking-cancellation/   ← Cancellation + refund trigger
│   │   ├── booking-refund/         ← CPG, JusPay, CCAvenue refund processing
│   │   ├── booking-refund-status-update/  ← Refund status callbacks
│   │   ├── booking-retrieval/      ← Search, customer/dealer/CRM/BTO queries
│   │   ├── lead-service/           ← Lead creation in external Lead Service
│   │   ├── dms-integration/        ← DMS (Dealer Management System) sync
│   │   ├── atp-handler/            ← ATP (Available-to-Promise) vehicle allocation
│   │   ├── publisher/              ← Service bus event publishers (9 publishers)
│   │   └── custom-repositories/    ← TypeORM query builders
│   └── dto/                ← 40+ DTOs for all operations
├── cloud-conductor/
│   ├── services/
│   │   ├── publisher/      ← Generic topic publisher (sends to Azure Service Bus)
│   │   ├── listener/       ← 4 topic listeners (main, ATP, DMS, MDP-dealer)
│   │   ├── keyvault/       ← Azure Key Vault secret reader
│   │   └── model-transformer/  ← DTO → topic message transformer
├── database/
│   └── entities/           ← 24 TypeORM entities (MSSQL)
├── logger/                 ← Structured logging service
└── shared/
    ├── constants/          ← Enums: API_ROUTE, EVENT_TYPE, BOOKING_STATUS, etc.
    └── exceptions/         ← Custom exception classes
```

## API Endpoints (from swagger.json)
| Method | Path | Description |
|--------|------|-------------|
| POST | /bookings | Create a booking (online or offline) |
| PUT | /bookings | Update a booking (vehicle, dealer, payment, etc.) |
| POST | /bookings/bto_status | Update BTO (build-to-order) booking status |
| POST | /bookings/search | Search bookings by criteria |
| PUT | /bookings/cancel | Cancel a booking (triggers refund if paid) |
| POST | /bookings/fnfrefund | Process FNF (full & final) refund |
| POST | /bookings/testbookingtopic | Test service bus publisher (dev tool) |
| POST | /bookings/refundstatus | Update refund status (CCAvenue callback) |
| POST | /bookings/juspayrefundstatus | Update JusPay refund status |
| POST | /bookings/dms-vehicle-master | DMS vehicle master data sync |
| GET | /bookings/health | Health check |

## Dependencies (Outbound)
### HTTP Calls
| Target | URL Variable | Purpose | File |
|---|---|---|---|
| Lead Service (external) | `LS_URL` | Create lead when booking is made | src/bookings/services/lead-service/lead.service.ts:40 |
| Lead Service OAuth | `TOKEN_GENERATION_URL` | Get OAuth token for Lead Service | src/bookings/services/lead-service/lead.service.ts:68 |
| CPG Payment Gateway | `cpgApiUrl` (from Key Vault) | Process payment via CPG | src/bookings/services/cpg.service.ts:77 |
| CPG Token Endpoint | `cpgTokenUrl` (from Key Vault) | Get CPG auth token | src/bookings/services/cpg.service.ts:118 |
| JusPay Payment Gateway | `jusPayApiUrl` (from Key Vault) | Process payment via JusPay | src/bookings/services/jusPay.service.ts:76 |
| JusPay Token Endpoint | `tokenUrl` (from Key Vault) | Get JusPay auth token | src/bookings/services/jusPay.service.ts:169 |
| CCAvenue Gateway | `ccaUrl` (from Key Vault) | Process refunds via CCAvenue | src/bookings/services/booking-refund/ccavenue-refund.service.ts:69 |

### Service Bus — Publishes
All published to a single topic (name from Key Vault: `TOPIC_NAME`). Events differentiated by `EventType` header:

| Event Type | When | Publisher File |
|---|---|---|
| BOOKING_CREATED | New booking confirmed | booking-creation-publisher.service.ts |
| BOOKING_CANCELLED | Booking cancelled | booking-cancellation-publisher.service.ts |
| BOOKING_REFUND_INITIATED | Refund started | booking-refund.publisher.service.ts |
| BOOKING_REFUND_SUCCESS | Refund completed | booking-refund-status-update.publisher.service.ts |
| VEHICLE_ALLOCATION | Vehicle assigned to booking | booking-modification-publisher.service.ts |
| VEHICLE_DEALLOCATION | Vehicle unassigned | booking-modification-publisher.service.ts |
| INVOICE_UPDATE | Invoice generated | booking-modification-publisher.service.ts |
| DMS_BOOKING_UPDATE | DMS sync event | dms-integration.publisher.service.ts |
| ATP_BOOKING_CREATED | ATP allocation request | atp-handler-publisher.service.ts |
| BTO status events | BTO lifecycle updates | bto-status-update-publisher.service.ts |

### Service Bus — Subscribes
Listens on the SAME topic (from Key Vault: `TOPIC_NAME`) with subscription `BS_SUBSCRIPTION_NAME`:

| Listener | Events Handled | Purpose | File |
|---|---|---|---|
| TopicListenerService | BOOKING_CANCELLED, BOOKING_REFUND_CCAVENUE_STATUS | Trigger refund on cancellation, process CCAvenue status | cloud-conductor/services/listener/topic-listener.service.ts |
| ATPTopicListenerService | ATP events | Handle ATP vehicle allocation responses | cloud-conductor/services/listener/atp-topic-listener.service.ts |
| DMSTopicListenerService | DMS events | Handle DMS sync responses | cloud-conductor/services/listener/dms-topic-listener.service.ts |
| MDPDealerTopicListenerService | MDP dealer events | Handle dealer master data updates | cloud-conductor/services/listener/mdp-dealer-topic-listener.service.ts |

## Data Model (Key Entities)
| Entity | Key Fields | Purpose |
|---|---|---|
| Booking | UUID, customerId, dealerId, bookingStatus, bookingSource, bookingNumber, btoStatus | Main booking record |
| Payment | bookingUUID, amount, paymentType, transactionId, status | Payment transactions |
| Vehicle | bookingUUID, modelId, frameNumber, engineNumber, color | Vehicle allocation |
| Product | bookingUUID, productId, quantity, amount | Products/accessories in booking |
| Location | bookingUUID, address, pincode, city, state | Delivery location |
| BookingCancellation | bookingUUID, reason, refundAmount, cancelledDate | Cancellation details |
| BookingRefund | bookingUUID, refundAmount, refundStatus, gateway | Refund tracking |
| DealerMaster | dealerCode, dealerName, branchId, city, state | Dealer reference data |
| SubOrders | parentBookingUUID, subOrderId | BTO sub-orders |

## Databases
| Type | Purpose | Evidence |
|---|---|---|
| MSSQL (via TypeORM) | Primary data store — all booking entities | package.json: mssql, tedious |
| Redis (via ioredis) | Caching — dealer master data, vehicle availability | package.json: ioredis |

## Key Configuration (from Key Vault)
All external service URLs and service bus config are stored in a single Key Vault secret: `BOOKING_SERVICE_CONFIG`

Contains (JSON):
- `TOPIC_SB_ENDPOINT` — Service Bus connection string
- `TOPIC_NAME` — Topic name for pub/sub
- `BS_SUBSCRIPTION_NAME` — This service's subscription name
- `LS_URL` — Lead Service URL
- `CPG_FNF_API_URL` — CPG payment (FNF) URL
- `CPG_DIRECT_API_URL` — CPG payment (direct) URL
- `CPG_TOKEN_URL` — CPG OAuth token URL
- `JUSPAY_DIRECT_API_URL` — JusPay payment URL
- `JUSPAY_FNF_API_URL` — JusPay FNF URL
- `JUSPAY_TOKEN_URL` — JusPay OAuth token URL
- `CCA_URL` — CCAvenue URL

## Recent Activity
- **Last commit:** 2026-05-04 by Nivetha-Nehru — "Feature/spd dealer test coverage (#409)"
- **Active contributors (30d):** Nivetha-Nehru, sureshkannantvs
- **Commit frequency:** ~1/week

## Business Rules
- A booking can be **online** (customer via website/app) or **offline** (dealer creates)
- Booking status flow: INITIATED → CONFIRMED → VEHICLE_ALLOCATED → INVOICED → DELIVERED
- BTO flow: CONFIRMED → MANUFACTURED → PACKED → DISPATCHED → AT_DEALERSHIP → DELIVERED
- Cancellation triggers automatic refund if payment exists
- Refund goes through CPG, JusPay, or CCAvenue depending on original payment gateway
- Vehicle allocation is managed via ATP (Available-to-Promise) system
- Each booking has a `version` + `checksum` for optimistic locking
