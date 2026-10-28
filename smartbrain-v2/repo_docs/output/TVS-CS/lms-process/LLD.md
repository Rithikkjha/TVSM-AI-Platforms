---
service_id: lms-process
doc_type: lld
last_reviewed: 2026-10-11
---

# lms-process — Low-Level Design

## Data Model
lms-process EF Core entities (inventory `data_access`; DDL not in repo):

| Entity | Table | Defined in |
|---|---|---|
| `BrandMaster` | `brand_master` | `lms.config/Entities/BrandMaster.cs:9` |
| `ClassifiedLead` | `classified_leads` | `lms.config/Entities/ClassifiedLead.cs:9` |
| `DealerContact` | `dealer_contacts` | `lms.config/Entities/DealerContact.cs:9` |
| `DealerFlag` | `dealer_flags` | `lms.config/Entities/DealerFlag.cs:9` |
| `DealerLocation` | `dealer_locations` | `lms.config/Entities/DealerLocation.cs:9` |
| `DealerMaster` | `dealer_master` | `lms.config/Entities/DealerMaster.cs:9` |
| `DealerMediationControl` | `dealer_mediation_controls` | `lms.config/Entities/DealerMediationControl.cs:9` |
| `LatlongPushLog` | `latlong_push_logs` | `lms.config/Entities/LatlongPushLog.cs:9` |
| `LceThreshold` | `lce_threshold` | `lms.config/Entities/LceThreshold.cs:9` |
| `Lead` | `leads` | `lms.config/Entities/Lead.cs:9` |
| `LeadFlowConfiguration` | `lead_flow_configuration` | `lms.config/Entities/LeadFlowConfiguration.cs:9` |
| `LeadProcessLog` | `lead_process_logs` | `lms.config/Entities/LeadProcessLog.cs:9` |
| `LeadPushLog` | `lead_push_logs` | `lms.config/Entities/LeadPushLog.cs:9` |
| `MdpLog` | `mdp_logs` | `lms.config/Entities/MdpLog.cs:9` |
| `StatusCode` | `status_codes` | `lms.config/Entities/StatusCode.cs:9` |
| `ThresholdMaster` | `ThresholdMaster` | `lms.config/Entities/ThresholdMaster.cs:9` |
| `UpdatedLead` | `updated_leads` | `lms.config/Entities/UpdatedLead.cs:9` |

## State Machines
lms-process event-type enumerations found in code (no persisted status state machine evidenced):

| Field | Values |
|---|---|
| Lead event (`EventType`) | `LEAD_PROCESS` | `PARTIAL_LEAD_PROCESS` | `UPDATE_LEAD_PROCESS` | `DEALER_RETRY_LEAD` (`processLeadService/Const/Constants.cs:68-76`) |
| Dealer event (`event`) | `DEALER_CREATED` | `DEALER_UPDATED` | `ONE_TIME_MIGRATION` (`processLeadService/Const/Constants.cs:50-54`) |

## Business Rules
lms-process rules shown by code:
- Finance target only when `IsFinanceEnabled` and the lead requests finance (`processLeadService/Services/TwoWheelerService.cs:62-65`)
- Invalid leads go only to CRM, and only if `IsCrmPush` or `IsDualPush` (`TwoWheelerService.cs:66-73`)
- EMS target requires `IsEmsPush` and LCE verification (`isEmsPushLceVarified`) (`TwoWheelerService.cs:74-77`)
- Delayed dispatch is scheduled for the next day at a fixed offset (`DispatchService.cs:54`)

## Key Classes and Functions
lms-process key classes:

| Class / function | Role | Evidence |
|---|---|---|
| DispatchService | Service Bus sender/processors | `processLeadService/Services/DispatchService.cs:25` |
| ApiExchangeService | HTTP | `processLeadService/ExchangeService/ApiExchangeService.cs:47` |
| LatlongService | HTTP (Latlong) | `processLeadService/Latlong/LatlongService.cs:130` |
| LMSDbContext | SQL Server | `lms.config/LMSContext` |

## Sequence Details
lms-process sequences: see DATA_FLOWS.md `Request Flows` (mermaid per flow, steps with file:line).

## Error Handling
lms-process: `LeadService.ProcessLead` wraps processing in try/catch and logs (`processLeadService/Services/LeadService.cs:62`); listener `ProcessErrorAsync` logs only.

## Configuration Details
lms-process configuration keys (names only; full list in OVERVIEW.md): `ApiUrlGclIdNotNull`, `ApiUrls:LCE_URL`, `ApiUrls:LCE_URL`, `AppSettings:CRM_SUBSCRIPTION`, `AppSettings:CRM_SUBSCRIPTION`, `AppSettings:DMS_SUBSCRIPTION`, `AppSettings:DMS_SUBSCRIPTION`, `AppSettings:EMS_SUBSCRIPTION`, `AppSettings:EMS_SUBSCRIPTION`, `AppSettings:FINANCE_SUBSCRIPTION`, `AppSettings:FINANCE_SUBSCRIPTION`, `AppSettings:MDP_LMS_SUBSCRIPTION`, `AppSettings:MDP_LMS_SUBSCRIPTION`, `AppSettings:MDP_TOPIC_NAME`, `AppSettings:MDP_TOPIC_NAME`, `AppSettings:OLD_LMS_URL`, `AppSettings:OLD_LMS_URL`, `AppSettings:SUBSCRIPTION_NAME`, `AppSettings:SUBSCRIPTION_NAME`, `AppSettings:TOPIC_NAME`, `AppSettings:TOPIC_NAME`, `ClientIdTokenURL`, `ClientSecretTokenURL`, `ConnectionStrings:DbConn`, `ConnectionStrings:DbConn`, `ConnectionStrings:aspNetCore`, `CookieTokenURL`, `GetTokenForClassificationURL`, `GrantTypeTokenURL`, `Latlong:3W_API_URL`, `Latlong:3W_API_URL`, `Latlong:COMMON_API_URL`, `Latlong:COMMON_API_URL`, `Latlong:EV_API_URL`, `Latlong:EV_API_URL`, `Latlong:RONIN_API_URL`, `Latlong:RONIN_API_URL`, `Latlong:RTR_API_URL`, `Latlong:RTR_API_URL`, `Latlong:TOKEN_URL`, `Latlong:TOKEN_URL`, `MdpServiceBusConnectionString`, `MdpServiceBusConnectionString`, `ScopeTokenURL`, `ServiceBusConnectionString`, `ServiceBusConnectionString`.

## Edge Cases
lms-process edge cases evidenced in code:
- Messages are completed before processing, so exceptions after completion lose the message (`QueueConsumer.cs:59`, `MdpConsumer.cs:65`)
- `MDP_TOPIC_NAME` is env-specific (`dev.`/`uat.`/`prod.mdp.dealer_data`) while `TOPIC_NAME` is `lms` in every env (`processLeadService/appsettings.*.json:9-10`)
