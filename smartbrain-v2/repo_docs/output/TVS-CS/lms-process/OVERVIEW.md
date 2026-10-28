---
service_id: lms-process
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["lms process", "lms_process", "norton lms process"]
---

# lms-process — Overview

## Purpose
Summary: LMS lead-processing worker (.NET) consuming topic lms/PROCESS, allocating dealers and routing leads to FINANCE/CRM/EMS; also syncs dealers from master-data-platform mdp.dealer_data.
Also known as: lms process, lms_process, norton lms process
lms-process (`processLeadService`) is the LMS lead-processing worker: a Service Bus listener on topic `lead` (subscription `PROCESS`) that classifies and qualifies leads, allocates dealers and re-publishes each lead to the `lead` topic with routing targets `FINANCE`, `CRM` and/or `EMS` (`processLeadService/Services/TwoWheelerService.cs:60-89`). It also consumes master-data-platform dealer events (`mdp.dealer_data`, subscription `lms`) to keep LMS dealer tables in sync (`processLeadService/MdpService/MdpDealerService.cs:31-45`). No README.

## Users and Consumers
lms-process HTTP callers (registry): none resolved.
Event producers feeding lms-process: `lms-ems`, `master-data-platform`. Event consumers of messages lms-process publishes: `lms-crm`, `lms-ems`, `lms-tvs-credit`.

## Key Capabilities
lms-process capabilities derived from code:
- Consumes `lms` / `PROCESS` and dispatches by `EventType`: `LEAD_PROCESS`, `PARTIAL_LEAD_PROCESS`, `UPDATE_LEAD_PROCESS`, `DEALER_RETRY_LEAD` (`processLeadService/Services/LeadService.cs:37-56`)
- Routes leads to downstream subscriptions FINANCE / CRM / EMS from lead-flow configuration (`IsFinanceEnabled`, `IsCrmPush`, `IsDualPush`, `IsEmsPush`) (`processLeadService/Services/TwoWheelerService.cs:60-89`)
- Dealer allocation by lat/long via external Latlong APIs (`processLeadService/Latlong/LatlongService.cs:130-138`)
- Consumes master-data-platform dealer events `DEALER_CREATED`, `DEALER_UPDATED`, `ONE_TIME_MIGRATION` (`processLeadService/Const/Constants.cs:50-54`, `MdpService/MdpDealerService.cs:31-45`)
- Scheduled (next-day) re-publish via `ScheduleMessageAsync` (`processLeadService/Services/DispatchService.cs:41-54`)
- Health/root `GET /` (`leadProcessController.GetLead`)

## Tech Stack
lms-process tech stack (service.yaml `tech_stack`, `runs/TVS-CS/lms_process/meta.json`):

| Layer | Technology | Version |
|---|---|---|
| Language | C# | net7.0 (`processLeadService/processLeadService.csproj:4`) |
| Framework | ASP.NET Core | see target framework |
| Data | SQL Server via EF Core (`Microsoft.EntityFrameworkCore.SqlServer`) | Unknown |
| Messaging | Azure Service Bus (`Azure.Messaging.ServiceBus`) | see csproj |
| Hosting | Unknown (no Dockerfile in repo) | - |

Key libraries: `AutoMapper.Extensions.Microsoft.DependencyInjection`, `Azure.Messaging.ServiceBus`, `EPPlus`, `Microsoft.AspNetCore.OpenApi`, `Microsoft.Azure.ServiceBus`, `Microsoft.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore.SqlServer`, `Microsoft.EntityFrameworkCore.Tools`, `Microsoft.VisualStudio.Azure.Containers.Tools.Targets`, `Newtonsoft.Json`, `Swashbuckle.AspNetCore`, `System.Data.SqlClient`, `WindowsAzure.Storage`

## Dependencies at a Glance
lms-process upstream: `lms-ems`, `master-data-platform`.
Downstream: no registry-resolved HTTP target; event consumers `lms-crm`, `lms-ems`, `lms-tvs-credit`.
Brokers: azure-service-bus. Data stores: `_` (mssql, key entities BrandMaster, ClassifiedLead, DealerContact …).

## Environments
lms-process environments evidenced by config/pipeline files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| Development | Unknown | from appsettings files |
| Production | Unknown | from appsettings files |
| Uat | Unknown | from appsettings files |
| default | Unknown | from appsettings files |

## Environment Variables
lms-process configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Secret | Provided by |
|---|---|---|---|
| `AllowedHosts` | Unknown | False | app-settings |
| `AllowedHosts` | Unknown | False | app-settings |
| `ApiUrlGclIdNotNull` | Unknown | False | app-settings |
| `ApiUrls:LCE_URL` | Unknown | False | app-settings |
| `ApiUrls:LCE_URL` | Unknown | False | app-settings |
| `AppSettings:CRM_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:CRM_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:DMS_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:DMS_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:EMS_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:EMS_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:EVENT_SOURCE_VALUE` | Unknown | False | app-settings |
| `AppSettings:EVENT_SOURCE_VALUE` | Unknown | False | app-settings |
| `AppSettings:FINANCE_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:FINANCE_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:MDP_LMS_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:MDP_LMS_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:MDP_TOPIC_NAME` | Unknown | False | app-settings |
| `AppSettings:MDP_TOPIC_NAME` | Unknown | False | app-settings |
| `AppSettings:OLD_LMS_URL` | Unknown | False | app-settings |
| `AppSettings:OLD_LMS_URL` | Unknown | False | app-settings |
| `AppSettings:SUBSCRIPTION_NAME` | Unknown | False | app-settings |
| `AppSettings:SUBSCRIPTION_NAME` | Unknown | False | app-settings |
| `AppSettings:THRESHOLD_EVENT_TYPE` | Unknown | False | app-settings |
| `AppSettings:THRESHOLD_EVENT_TYPE` | Unknown | False | app-settings |
| `AppSettings:TOPIC_NAME` | Unknown | False | app-settings |
| `AppSettings:TOPIC_NAME` | Unknown | False | app-settings |
| `ClientIdTokenURL` | Unknown | True | app-settings |
| `ClientSecretTokenURL` | Unknown | True | app-settings |
| `ConnectionStrings:DbConn` | Unknown | True | app-settings |
| `ConnectionStrings:DbConn` | Unknown | True | app-settings |
| `ConnectionStrings:aspNetCore` | Unknown | True | app-settings |
| `CookieTokenURL` | Unknown | True | app-settings |
| `GetTokenForClassificationURL` | Unknown | True | app-settings |
| `GrantTypeTokenURL` | Unknown | True | app-settings |
| `Latlong:3W_API_URL` | Unknown | False | app-settings |
| `Latlong:3W_API_URL` | Unknown | False | app-settings |
| `Latlong:3W_CLIENT_ID` | Unknown | False | app-settings |
| `Latlong:3W_CLIENT_ID` | Unknown | False | app-settings |
| `Latlong:3W_CLIENT_SECRET` | Unknown | True | app-settings |
| `Latlong:3W_CLIENT_SECRET` | Unknown | True | app-settings |
| `Latlong:COMMON_API_URL` | Unknown | False | app-settings |
| `Latlong:COMMON_API_URL` | Unknown | False | app-settings |
| `Latlong:COMMON_CLIENT_ID` | Unknown | False | app-settings |
| `Latlong:COMMON_CLIENT_ID` | Unknown | False | app-settings |
| `Latlong:COMMON_CLIENT_SECRET` | Unknown | True | app-settings |
| `Latlong:COMMON_CLIENT_SECRET` | Unknown | True | app-settings |
| `Latlong:EV_API_URL` | Unknown | False | app-settings |
| `Latlong:EV_API_URL` | Unknown | False | app-settings |
| `Latlong:EV_CLIENT_ID` | Unknown | False | app-settings |
| `Latlong:EV_CLIENT_ID` | Unknown | False | app-settings |
| `Latlong:EV_CLIENT_SECRET` | Unknown | True | app-settings |
| `Latlong:EV_CLIENT_SECRET` | Unknown | True | app-settings |
| `Latlong:RONIN_API_URL` | Unknown | False | app-settings |
| `Latlong:RONIN_API_URL` | Unknown | False | app-settings |
| `Latlong:RONIN_CLIENT_ID` | Unknown | False | app-settings |
| `Latlong:RONIN_CLIENT_ID` | Unknown | False | app-settings |
| `Latlong:RONIN_CLIENT_SECRET` | Unknown | True | app-settings |
| `Latlong:RONIN_CLIENT_SECRET` | Unknown | True | app-settings |
| `Latlong:RTR_API_URL` | Unknown | False | app-settings |
| `Latlong:RTR_API_URL` | Unknown | False | app-settings |
| `Latlong:RTR_CLIENT_ID` | Unknown | False | app-settings |
| `Latlong:RTR_CLIENT_ID` | Unknown | False | app-settings |
| `Latlong:RTR_CLIENT_SECRET` | Unknown | True | app-settings |
| `Latlong:RTR_CLIENT_SECRET` | Unknown | True | app-settings |
| `Latlong:TOKEN_URL` | Unknown | True | app-settings |
| `Latlong:TOKEN_URL` | Unknown | True | app-settings |
| `Logging:LogLevel:Default` | Unknown | False | app-settings |
| `Logging:LogLevel:Default` | Unknown | False | app-settings |
| `Logging:LogLevel:Microsoft.AspNetCore` | Unknown | False | app-settings |
| `Logging:LogLevel:Microsoft.AspNetCore` | Unknown | False | app-settings |
| `MdpServiceBusConnectionString` | Unknown | True | app-settings |
| `MdpServiceBusConnectionString` | Unknown | True | app-settings |
| `ScopeTokenURL` | Unknown | True | app-settings |
| `ServiceBusConnectionString` | Unknown | True | app-settings |
| `ServiceBusConnectionString` | Unknown | True | app-settings |

## Ownership
lms-process ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |

## Local Setup
lms-process local setup evidence: build/test commands in HLC.md `Build and Test`; configuration from `appsettings.json` + `appsettings.<env>.json` (Development/Uat/Production); a Service Bus namespace and the LMS SQL database are required (connection settings by name above).

## Known Limitations
lms-process limitations evidenced in code:
- A literal API key constant exists at `processLeadService/Const/Constants.cs:40` (value not reproduced); it should move to configuration/Key Vault.
- Latlong/LCE HTTP targets are config-driven (`Latlong:*_API_URL`, `ApiUrls:LCE_URL`) and not resolved to registry services.
