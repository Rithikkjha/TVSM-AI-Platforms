---
service_id: async-communication-service
doc_type: lld
last_reviewed: 2026-10-11
---

# async-communication-service — Low-Level Design

## Data Model
async-communication-service entities from `data_access` items (1).

Store access at `src/app.module.ts:40`: database Unknown; collections -.

### Booking
Entity `Booking` defined in `src/database/entities/booking.entity.ts:22`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### BookingCancellation
Entity `BookingCancellation` defined in `src/database/entities/booking-cancellation.entity.ts:11`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### BookingRefund
Entity `BookingRefund` defined in `src/database/entities/booking-refund.entity.ts:7`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### BookingTopicLog
Entity `BookingTopicLog` defined in `src/database/entities/booking-topic-log.entity.ts:8`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### CityDetails
Entity `CityDetails` defined in `src/database/entities/city-details.ts:4`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### CommunicationEventBccList
Entity `CommunicationEventBccList` defined in `src/database/entities/communication-event-bcc-list.entity.ts:4`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### Correspondence
Entity `Correspondence` defined in `src/database/entities/correspondence.entity.ts:4`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### DmsVehicleMaster
Entity `DmsVehicleMaster` defined in `src/database/entities/dms-vehicle-master.entity.ts:4`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### Location
Entity `Location` defined in `src/database/entities/location.entity.ts:8`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### Payment
Entity `Payment` defined in `src/database/entities/payment.entity.ts:8`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### Product
Entity `Product` defined in `src/database/entities/product.entity.ts:8`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### refund_transaction_logs
Entity `RefundTransactionLog` defined in `src/database/entities/refund-transaction-log.entity.ts:13`; table refund_transaction_logs; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### Vehicle
Entity `Vehicle` defined in `src/database/entities/vehicle.entity.ts:8`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### VehicleVariantColor
Entity `VehicleVariantColor` defined in `src/database/entities/vehicle-variant-color.entity.ts:4`; table Unknown; operation Unknown.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

## State Machines
async-communication-service: N/A — no status/state enums found in code.

## Business Rules
async-communication-service validation rules on DTO fields (from schema `validation`):
N/A — no declarative validation found; other rules not determinable without manual review.

## Key Classes and Functions
async-communication-service key classes:

| Class / Function | File | Responsibility |
|---|---|---|
| `None` | `src/shared/salesforce/scheduler/bto-scheduler.ts:13` | scheduled job |
| `None` | `src/shared/salesforce/scheduler/bto-scheduler.ts:24` | scheduled job |
| subscribe Unknown (`TOPIC_NAME`) | `src/shared/cloudService/topicListener/topic-listener.service.ts:71` | azure-service-bus messaging |

## Sequence Details
async-communication-service: N/A — no server endpoint to sequence.

## Error Handling
async-communication-service error handling: no global exception handler found in code. Status mapping: Unknown.

## Configuration Details
async-communication-service behaviour-relevant config keys (names only; full list in OVERVIEW.md):
- `TOPIC_NAME`: subscribe entity name

## Edge Cases
async-communication-service edge cases: N/A — not determinable from code without manual review.
