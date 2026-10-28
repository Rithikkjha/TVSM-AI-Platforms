---
service_id: lms-crm
doc_type: lld
last_reviewed: 2026-10-11
---

# lms-crm — Low-Level Design

## Data Model
lms-crm EF Core entities (inventory `data_access`; DDL not in repo):

| Entity | Table | Defined in |
|---|---|---|
| `BrandMaster` | `brand_master` | `Entities/BrandMaster.cs:9` |
| `DealerMediationControl` | `dealer_mediation_controls` | `Entities/DealerMediationControl.cs:9` |
| `DialerToken` | `dialer_token` | `Entities/DialerToken.cs:9` |
| `Lead` | `leads` | `Entities/Lead.cs:9` |
| `LeadFlowConfiguration` | `lead_flow_configuration` | `Entities/LeadFlowConfiguration.cs:9` |
| `LeadPushLog` | `lead_push_logs` | `Entities/LeadPushLog.cs:9` |
| `ModelIdPartIdMaster` | `model_id_part_id_master` | `Entities/ModelIdPartIdMaster.cs:9` |

## State Machines
lms-crm: N/A — no status enum/state machine evidenced in code.

## Business Rules
lms-crm rules shown by code:
- Rezo, CCP and dialer pushes are each gated by lead-flow configuration for the lead's `sourceId` (`Services/CrmService.cs:51-65`)
- Successful CRM push upserts the dealer/branch threshold for the day (`Services/CrmService.cs:92`)
- Lead status updated after push (`Services/CrmService.cs:105`)

## Key Classes and Functions
lms-crm key classes:

| Class / function | Role | Evidence |
|---|---|---|
| ApiExchangeService | HTTP | `Services/ApiExchangeService.cs:27` |
| LeadExchangeService | HTTP | `ExchangeService/LeadExchangeService.cs:27` |
| CrmListenerService | Service Bus | `Services/DispatchService.cs:19` |
| LMSDbContext | SQL Server | `LMSContext/LMSDbContext.cs` |

## Sequence Details
lms-crm sequences: see DATA_FLOWS.md `Request Flows` (mermaid per flow, steps with file:line).

## Error Handling
lms-crm: Listener `ProcessErrorAsync` logs only; push responses/status stored via `ProcessLeadLog` (`Services/CrmService.cs:103`).

## Configuration Details
lms-crm configuration keys (names only; full list in OVERVIEW.md): `AppSettings:CCP_TOKEN_URL`, `AppSettings:CCP_URL`, `AppSettings:CRM_SUBSCRIPTION`, `AppSettings:CRM_URL`, `AppSettings:DIALER_TOKEN_URL`, `AppSettings:DIALER_URL`, `AppSettings:OLD_LMS_URL`, `AppSettings:REZO_API_URL`, `AppSettings:TOPIC_NAME`, `ConnectionStrings:DbConn`, `ServiceBusConnectionString`.

## Edge Cases
lms-crm edge cases evidenced in code:
- `DispatchService.Dispatch` (`Services/DispatchService.cs:17-22`) has no caller in code, so the publish item stays unresolved
- Messages are completed before processing (`CrmListenerService.cs:66`)
