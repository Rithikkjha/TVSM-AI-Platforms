---
service_id: lms-tvs-credit
doc_type: hlc
last_reviewed: 2026-10-11
---

# lms-tvs-credit — High-Level Code

## Application Overview
lms-tvs-credit is a C# / ASP.NET Core service in repo `lms_tvs_credit` (default branch per `runs/TVS-CS/lms_tvs_credit/meta.json`). Its HTTP surface is only `GET /`; the work happens in a Service Bus processor registered at startup.

## Module Summary
lms-tvs-credit modules:

| Module | Responsibility |
|---|---|
| `lms_tvs_credit/` | ASP.NET Core host (net7.0): ListenerService, Services, ExchangeService, Repository, Entities, LMSContext, Models, Const, Utils |
| `CreditTest/` | Test project (`CreditTest.csproj`, single `UnitTest1.cs`) |
| `azure-pipelines/, LMS_TVS_Credit-CI-Dev.YML` | Azure DevOps CI |

## Folder Structure
lms-tvs-credit top-level folders (real paths):
```
lms_tvs_credit/
CreditTest/
azure-pipelines/, LMS_TVS_Credit-CI-Dev.YML
```

## Core Workflows in Code
lms-tvs-credit entry → handler → service → client/repository:
- `TvscreditListenerService.ProcessMessagesAsync` → `TvscreditService.PushFinanceLeads` → `SendPostRequest` (HTTP) → `PushFinanceLog` → `ApiExchangeService.PublishToOldLms`

## Integration Clients
lms-tvs-credit client classes:

| Kind | Client | Evidence |
|---|---|---|
| HTTP | `HttpClient` in `TvscreditService.SendPostRequest` | `lms_tvs_credit/Services/TvscreditService.cs:128` |
| HTTP | `ApiExchangeService` (OLD_LMS_URL) | `lms_tvs_credit/ExchangeService/ApiExchangeService.cs:27` |
| Service Bus | `TvscreditListenerService` processor | `lms_tvs_credit/ListenerService/TvscreditListenerService.cs:46` |
| SQL Server | EF Core `LMSDbContext` | `lms_tvs_credit/LMSContext` |

## Cross-Cutting Concerns
lms-tvs-credit cross-cutting concerns:
- Configuration via `AppSettingsService` (`AppSettings:*`, `lms_tvs_credit/Services/AppSettingsService.cs:27-30`)

## Build and Test
lms-tvs-credit build/test (dotnet CLI against the committed solution/project files; CI pipelines use shared templates):
- `dotnet build lms_tvs_credit/lms_tvs_credit.sln`
- `dotnet test CreditTest/CreditTest.csproj`
