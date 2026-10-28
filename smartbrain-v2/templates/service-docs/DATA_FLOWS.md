---
service_id: <service-id>
doc_type: data_flows
last_reviewed: YYYY-MM-DD
flows: [vehicle-booking]   # flow_ids, must match service.yaml `flows`
---

# <Service Name> — Data Flows

## Flow Index
| flow_id | Name | Role of <service-id> | Trigger |
|---|---|---|---|
| vehicle-booking | Customer books a vehicle | orchestrator | User taps "Book" |

## Flow: vehicle-booking
Heading format is fixed: `## Flow: <flow_id>`. Use the same flow_id in every service that participates.

Summary: one paragraph in plain language, naming every service_id involved.

```mermaid
sequenceDiagram
  participant App as tvs-connect-android-app
  participant B as booking-crud-services
  participant P as payment-service
  participant N as async-communication-service
  App->>B: POST /api/bookings
  B->>P: POST /api/payments/initiate
  P--)B: payment-events: PAYMENT_SUCCEEDED
  B--)N: booking-events: BOOKING_CREATED
```

Steps:
| # | From | To | Via | Data | Sync/Async |
|---|---|---|---|---|---|
| 1 | tvs-connect-android-app | booking-crud-services | POST /api/bookings | booking request | sync |

Data touched: which stores are read/written at which step.

Failure points: what happens if each step fails, and who notices.
