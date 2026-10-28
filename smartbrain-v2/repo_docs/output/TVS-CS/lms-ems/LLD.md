---
service_id: lms-ems
doc_type: lld
last_reviewed: 2026-10-11
---

# lms-ems — Low-Level Design

## Data Model
lms-ems EF Core entities (inventory `data_access`; DDL not in repo):

| Entity | Table | Defined in |
|---|---|---|
| `BrandMaster` | `brand_master` | `emsService/Entities/BrandMaster.cs:9` |
| `DealerMediationControl` | `dealer_mediation_controls` | `emsService/Entities/DealerMediationControl.cs:9` |
| `Lead` | `leads` | `emsService/Entities/Lead.cs:9` |
| `LeadFlowConfiguration` | `lead_flow_configuration` | `emsService/Entities/LeadFlowConfiguration.cs:9` |
| `LeadPushLog` | `lead_push_logs` | `emsService/Entities/LeadPushLog.cs:9` |

## State Machines
lms-ems event-type enumerations found in code (no persisted status state machine evidenced):

| Field | Values |
|---|---|
| Outgoing `EventType` | `EMS_LEAD` (delayed retry), `THRESHOLD_EXCEEDED_LEAD`, `DEALER_RETRY_LEAD` (`emsService/Services/DispatchService.cs:31,42,53`; constants in `emsService/Const/Constants.cs`) |

## Business Rules
lms-ems rules shown by code:
- Threshold-exceeded leads are re-scheduled to EMS for the next day (`emsService/Services/EmsService.cs:47`, `DispatchService.cs:42`)
- Failed EMS pushes may fall back to CRM (`EmsService.cs:191`) or be retried after 30 minutes (`EmsService.cs:199`, `DispatchService.cs:34`)
- Dealer-retry leads are sent back to lms-process (`PROCESS_SUBSCRIPTION`, `EmsService.cs:214`)

## Key Classes and Functions
lms-ems key classes:

| Class / function | Role | Evidence |
|---|---|---|
| DispatchService | Service Bus | `emsService/Services/DispatchService.cs:18` |
| HttpClient | HTTP | `emsService/Services/EmsService.cs:152` |
| LMSDbContext | SQL Server | `emsService/LMSContext` |

## Sequence Details
lms-ems sequences: see DATA_FLOWS.md `Request Flows` (mermaid per flow, steps with file:line).

## Error Handling
lms-ems: Listener `ProcessErrorAsync` logs only; HTTP failures are captured into push logs (see `EmsService.cs`).

## Configuration Details
lms-ems configuration keys (names only; full list in OVERVIEW.md): `AppSettings:CRM_SUBSCRIPTION`, `AppSettings:DMS_SUBSCRIPTION`, `AppSettings:EMS_API_AGGREGATOR_URL`, `AppSettings:EMS_API_URL`, `AppSettings:EMS_SUBSCRIPTION`, `AppSettings:OLD_LMS_URL`, `AppSettings:PROCESS_SUBSCRIPTION`, `AppSettings:TOPIC_NAME`, `ConnectionStrings:DbConn`, `ServiceBusConnectionString`.

## Edge Cases
lms-ems edge cases evidenced in code:
- The extractor typed the publisher as a queue; code passes `TOPIC_NAME` as the entity, so it is a topic (recorded as a conflict in `runs/TVS-CS/lms_ems/llm_notes.json`)
- Messages are completed before processing (`EmsListenerService.cs:66`)
