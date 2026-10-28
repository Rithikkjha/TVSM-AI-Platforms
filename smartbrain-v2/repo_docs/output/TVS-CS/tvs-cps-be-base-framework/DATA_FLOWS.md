---
service_id: tvs-cps-be-base-framework
doc_type: data_flows
last_reviewed: 2026-10-11
flows: []   # flow_ids, must match service.yaml `flows`
---

# tvs-cps-be-base-framework — Data Flows

## Flow Index

| flow_id | Name | Role of tvs-cps-be-base-framework | Trigger |
|---|---|---|---|
| N/A | no end-to-end flow | N/A | N/A |

N/A — tvs-cps-be-base-framework takes part in no end-to-end flow in registry/flows.json (no HTTP/event edge to or from another service).

Direct neighbours in registry/edges.json:
- inbound ← tvs-cps-backend (library_dependency)
- inbound ← tvs-cps-billing (library_dependency)
- inbound ← tvs-cps-customer (library_dependency)
- inbound ← tvs-cps-inventory (library_dependency)
- inbound ← tvs-cps-job-card-service (library_dependency)
- inbound ← tvs-cps-jobs (library_dependency)
