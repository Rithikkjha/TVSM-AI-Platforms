---
service_id: lms-tvs-credit
doc_type: lld
last_reviewed: 2026-10-11
---

# lms-tvs-credit — Low-Level Design

## Data Model
lms-tvs-credit EF Core entities (inventory `data_access`; DDL not in repo):

| Entity | Table | Defined in |
|---|---|---|
| `DealerMediationControl` | `dealer_mediation_controls` | `lms_tvs_credit/Entities/DealerMediationControl.cs:9` |
| `LeadPushLog` | `lead_push_logs` | `lms_tvs_credit/Entities/LeadPushLog.cs:9` |
| `TvscreditCityMaster` | `tvscredit_city_master` | `lms_tvs_credit/Entities/TvscreditCityMaster.cs:9` |
| `TvscreditDealerMaster` | `tvscredit_dealer_master` | `lms_tvs_credit/Entities/TvscreditDealerMaster.cs:9` |
| `TvscreditStateMaster` | `tvscredit_state_master` | `lms_tvs_credit/Entities/TvscreditStateMaster.cs:9` |

## State Machines
lms-tvs-credit: N/A — no status enum/state machine evidenced in code.

## Business Rules
lms-tvs-credit rules shown by code:
- Push status is -1 on exception, and the log/old-LMS publish runs in `finally` regardless of outcome (`lms_tvs_credit/Services/TvscreditService.cs:113-124`)

## Key Classes and Functions
lms-tvs-credit key classes:

| Class / function | Role | Evidence |
|---|---|---|
| HttpClient | HTTP | `lms_tvs_credit/Services/TvscreditService.cs:128` |
| ApiExchangeService | HTTP | `lms_tvs_credit/ExchangeService/ApiExchangeService.cs:27` |
| TvscreditListenerService | Service Bus | `lms_tvs_credit/ListenerService/TvscreditListenerService.cs:46` |
| LMSDbContext | SQL Server | `lms_tvs_credit/LMSContext` |

## Sequence Details
lms-tvs-credit sequences: see DATA_FLOWS.md `Request Flows` (mermaid per flow, steps with file:line).

## Error Handling
lms-tvs-credit: Exceptions in the push are caught and stored as the response text with status -1 (`TvscreditService.cs:113-119`); listener `ProcessErrorAsync` logs only.

## Configuration Details
lms-tvs-credit configuration keys (names only; full list in OVERVIEW.md): `AppSettings:OLD_LMS_URL`, `AppSettings:QUEUE`, `AppSettings:SUBSCRIPTION_NAME`, `AppSettings:TOPIC_NAME`, `AppSettings:TvsCrrditDealerURL`, `AppSettings:TvsCrrditLeadPushURL`, `ConnectionStrings:DbConn`.

## Edge Cases
lms-tvs-credit edge cases evidenced in code:
- Base `appsettings.json` sets `SUBSCRIPTION_NAME` = `CREDIT` and a `QUEUE` key, while the env files use `FINANCE` (`lms_tvs_credit/appsettings.json:14,22` vs `appsettings.Development.json:21`); lms-process routes finance leads to `FINANCE_SUBSCRIPTION` = `FINANCE`
- Messages are completed before processing (`TvscreditListenerService.cs:65`)
