---
service_id: lms-tvs-credit
doc_type: hld
last_reviewed: 2026-10-11
---

# lms-tvs-credit — High-Level Design

## Context
lms-tvs-credit is a `backend-api` in the TVS-CS Lead Management System (domain: lead-management). It is one of five LMS repos: `lms` (acquisition API) and the listener workers `lms-process`, `lms-ems`, `lms-crm`, `lms-tvs-credit`, connected through Service Bus topic `lead`.

## Architecture
lms-tvs-credit components and connections (from service.yaml / registry edges):
```mermaid
flowchart LR
  svc["lms-tvs-credit"]
  n_lms_ems["lms-ems"]
  n_lms_ems -.->|event: lms| svc
  n_lms_process["lms-process"]
  n_lms_process -.->|event: lms| svc
  svc <--> br{{"azure-service-bus"}}
  svc --> db0[("mssql (_)")]
```

## Integration Points
lms-tvs-credit registry edges (2):

| Direction | Peer | Kind | Via | Criticality | Source | Match |
|---|---|---|---|---|---|---|
| in | `lms-ems` | event | azure-service-bus:topic:lead | async | inferred | entity |
| in | `lms-process` | event | azure-service-bus:topic:lead | async | inferred | entity |

## Data Ownership
lms-tvs-credit data stores (service.yaml `data_stores`). All LMS repos map the same LMS SQL schema (tables such as `leads`, `lead_push_logs`, `dealer_mediation_controls`, `lead_flow_configuration`); ownership is not declared in code.

| Store | Type | Owned | Key entities |
|---|---|---|---|
| `_` | mssql | Unknown | DealerMediationControl, LeadPushLog, TvscreditCityMaster, TvscreditDealerMaster, TvscreditStateMaster |

## Key Design Decisions
lms-tvs-credit: N/A — not determinable from code.

## Non-Functional Requirements
lms-tvs-credit NFR targets: N/A — not determinable from code.

## Security
lms-tvs-credit security: lms-tvs-credit exposes only `GET /` with no auth attribute; outbound auth to TVS Credit: Unknown (see `TvscreditService.cs`). Secrets (connection strings, client secrets, API keys) are read from configuration keys listed by name in OVERVIEW.md; values are not reproduced. PII handling: leads carry customer contact data (see request schemas); masking/encryption Unknown.

## Resilience and Failure Modes
lms-tvs-credit: The handler completes the Service Bus message *before* business processing (`AutoCompleteMessages = false` then an explicit `CompleteMessageAsync` at `lms_tvs_credit/ListenerService/TvscreditListenerService.cs:65`), so a failure in processing does not redeliver or dead-letter the message; the error handler only logs (TvscreditListenerService.cs `ProcessErrorAsync`). `MaxConcurrentCalls = 1` serialises processing. No retry policy, circuit breaker or DLQ handling found in code.

## Deployment Topology
lms-tvs-credit deployment artefacts (platform/regions: Unknown):

| Kind | File | Environments | Base images | Ports |
|---|---|---|---|---|
| azure-pipeline | `azure-pipelines/norton_ls_tvs_credit-CI.yaml` | - | - | - |

## Observability
lms-tvs-credit observability: `ILogger` logging only; no OpenTelemetry/App Insights configuration found. Dashboards/alerts: Unknown.
