---
service_id: qrcode-frontend
doc_type: data_flows
last_reviewed: 2026-10-11
flows: [qrcode-frontend--tvsmbe-qrcode]   # flow_ids, must match service.yaml `flows`
---

# qrcode-frontend — Data Flows

## Flow Index
qrcode-frontend takes part in 1 end-to-end flow(s) in registry/flows.json.

| flow_id | Name | Role of qrcode-frontend | Trigger |
|---|---|---|---|
| qrcode-frontend--tvsmbe-qrcode | qrcode-frontend → tvsmbe-qrcode (1 hop) | entry | user action in qrcode-frontend (frontend) |

## Flow: qrcode-frontend--tvsmbe-qrcode
Summary: Starting at `qrcode-frontend` (user action in qrcode-frontend (frontend)), the flow ends at `tvsmbe-qrcode`, using 1 sync HTTP hop(s) and 0 async event hop(s); qrcode-frontend role: entry; confidence high.

```mermaid
sequenceDiagram
  participant qrcode_frontend as qrcode-frontend
  participant tvsmbe_qrcode as tvsmbe-qrcode
  qrcode_frontend->>tvsmbe_qrcode: GET /api/analytics/summary (+13 more)
```

Steps:
| # | From | To | Via | Data (schema names) | Sync/Async | Confidence |
|---|---|---|---|---|---|---|
| 1 | qrcode-frontend | tvsmbe-qrcode | GET /api/analytics/summary, GET /api/analytics/timeline, GET /api/analytics/top (+11 more) | Unknown | sync | high |

Data touched: tvsmbe-qrcode: mongo:tvs_qr

Failure points: hop 1 qrcode-frontend → tvsmbe-qrcode: criticality hard

Evidence:
- hop 1 (qrcode-frontend → tvsmbe-qrcode): `qrcode-frontend/src/api.ts:218`, `tvsmbe-qrcode/src/main/java/com/tvsmotor/qrcode/controller/AnalyticsController.java:27`, `qrcode-frontend/src/api.ts:236` (+20 more)
