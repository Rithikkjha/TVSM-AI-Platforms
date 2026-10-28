---
service_id: tvs-cps-db-migration
doc_type: data_flows
last_reviewed: 2026-10-11
flows: []   # flow_ids, must match service.yaml `flows`
---

# tvs-cps-db-migration — Data Flows

## Flow Index

| flow_id | Name | Role of tvs-cps-db-migration | Trigger |
|---|---|---|---|
| N/A | no end-to-end flow | N/A | N/A |

N/A — tvs-cps-db-migration takes part in no end-to-end flow in registry/flows.json (no HTTP/event edge to or from another service).

Direct neighbours in registry/edges.json:
- outbound → table:analytics_dashboard (owns_schema)
- outbound → table:analytics_indicator (owns_schema)
- outbound → table:announcement (owns_schema)
- outbound → table:announcement_media (owns_schema)
- outbound → table:announcement_read_log (owns_schema)
- outbound → table:announcement_target (owns_schema)
- outbound → table:appointment (owns_schema)
- outbound → table:appointment_context_mapping (owns_schema)
- outbound → table:appointment_detail (owns_schema)
- outbound → table:appointment_follow_up (owns_schema)
- outbound → table:appointment_job_type_master (owns_schema)
- outbound → table:appointment_service_type_master (owns_schema)
- outbound → table:appointment_status_master (owns_schema)
- outbound → table:bin (owns_schema)
- outbound → table:bulk_upload (owns_schema)
- outbound → table:bulk_upload_error (owns_schema)
- outbound → table:call_result_master (owns_schema)
- outbound → table:cancellation_reason_master (owns_schema)
- outbound → table:cart (owns_schema)
- outbound → table:cart_line (owns_schema)
- (+89 more)
