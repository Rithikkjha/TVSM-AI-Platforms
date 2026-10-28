---
service_id: lms
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["lead service", "service reminder", "lead api caller", "lead", "booking"]
---

# lms — Overview

## Purpose
Summary: Lead Management System acquisition API (.NET) that receives, validates, de-duplicates and stores leads (incl. B2B webhooks) and publishes them to Azure Service Bus for the LMS workers.
Also known as: lead service, service reminder, lead api caller, lead, booking
lms is the Lead Management System acquisition API (`leadLogs/leadReceiptService.csproj`): it receives leads over HTTP (`POST /api/lead`, B2B and webhook endpoints), logs and validates them (`leadLogs/Services/LeadLogService.cs:61-90`), persists them to the LMS SQL database and dispatches them to an Azure Service Bus topic for downstream processing (`leadLogs/Services/LeadDispatchService.cs:21`). The README (`readme.md`) only contains an EF Core scaffold command (connection details not reproduced).

## Users and Consumers
lms HTTP callers (registry): `tvs-cps-backend`, `tvsm-marketplace-service`, `tvsmbe-location`.
Event producers feeding lms: none resolved. Event consumers of messages lms publishes: none resolved.

## Key Capabilities
lms capabilities derived from code:
- Lead acquisition: `POST /api/lead` → `LeadAcquisitionController.Lead` (`leadLogs/Controllers/LeadAcquisitionController.cs:61`)
- Lead update and B2B lead update: `POST /api/lead/update`, `POST /api/b2b/lead/update`
- Webhook endpoint `GET/POST /api/b2b/lead` (`leadLogs/Controllers/WebhooksController.cs:31,54`); GET performs a `hub.mode`/`hub.challenge`/`hub.verify_token` verification handshake (`WebhooksController.cs:40-44`)
- Lead communications: `POST /api/lead/comms` (`leadLogs/Controllers/LeadCommsController.cs:18`)
- Lead queries: `/api/leads/Count`, `/api/leads/getDetails`, `/api/leads/all`, `/api/leads/filter`, `/api/leads/one-view` (`leadLogs/Controllers/LeadGetController.cs`)
- Dealer lookup `POST /dealers` and health/root `GET /`
- Publishes accepted/invalid/duplicate leads to Azure Service Bus with `EventType`, `EventSource`, `EventTarget`, `CreatedAt`, `Version` application properties (`leadLogs/Services/LeadDispatchService.cs:28-34`)

## Tech Stack
lms tech stack (service.yaml `tech_stack`, `runs/TVS-CS/lms/meta.json`):

| Layer | Technology | Version |
|---|---|---|
| Language | C# | net8.0 (`leadLogs/leadReceiptService.csproj:4`) |
| Framework | ASP.NET Core | see target framework |
| Data | SQL Server via EF Core (`Microsoft.EntityFrameworkCore.SqlServer`) | Unknown |
| Messaging | Azure Service Bus (`Azure.Messaging.ServiceBus`) | see csproj |
| Hosting | Docker (`Dockerfile`) | - |

Key libraries: `AutoMapper.Extensions.Microsoft.DependencyInjection`, `Azure.Messaging.ServiceBus`, `Azure.Security.KeyVault.Secrets`, `FluentValidation.AspNetCore`, `Microsoft.AspNet.Cors`, `Microsoft.AspNetCore.Authentication`, `Microsoft.AspNetCore.OpenApi`, `Microsoft.Azure.ServiceBus`, `Microsoft.Data.SqlClient`, `Microsoft.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore.Design`, `Microsoft.EntityFrameworkCore.SqlServer`, `Microsoft.EntityFrameworkCore.Tools`, `Microsoft.Extensions.Azure`, `Microsoft.VisualStudio.Azure.Containers.Tools.Targets`, `Newtonsoft.Json`, `Swashbuckle.AspNetCore`, `System.Data.SqlClient`

## Dependencies at a Glance
lms upstream: `tvs-cps-backend`, `tvsm-marketplace-service`, `tvsmbe-location`.
Downstream: no registry-resolved HTTP target.
Brokers: azure-service-bus. Data stores: `_` (mssql, key entities AccountMaster, AdditionalDetail, AdditionalDetailsLogMapping …), `tazlmssqldbdev01` (mssql, key entities DealerMediationControl …).

## Environments
lms environments evidenced by config/pipeline files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| config | Unknown | from appsettings files |
| default | Unknown | from appsettings files |
| dev | Unknown | from pipeline files |
| uat | Unknown | from pipeline files |

## Environment Variables
lms configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Secret | Provided by |
|---|---|---|---|
| `DB_CONNECTION` | Unknown | False | Unknown |
| `EVENT_SOURCE_VALUE` | Unknown | False | Unknown |
| `EVENT_TARGET_VALUE` | Unknown | False | Unknown |
| `FacebookSettings:version` | Unknown | False | Unknown |
| `KeyVault` | Unknown | False | Unknown |
| `LATLONG_3W_API_URL` | Unknown | False | Unknown |
| `LATLONG_3W_CLIENT_ID` | Unknown | False | Unknown |
| `LATLONG_3W_CLIENT_SECRET` | Unknown | False | Unknown |
| `LATLONG_COMMON_API_URL` | Unknown | False | Unknown |
| `LATLONG_COMMON_CLIENT_ID` | Unknown | False | Unknown |
| `LATLONG_COMMON_CLIENT_SECRET` | Unknown | False | Unknown |
| `LATLONG_EV_API_URL` | Unknown | False | Unknown |
| `LATLONG_EV_CLIENT_ID` | Unknown | False | Unknown |
| `LATLONG_EV_CLIENT_SECRET` | Unknown | False | Unknown |
| `LATLONG_RONIN_API_URL` | Unknown | False | Unknown |
| `LATLONG_RONIN_CLIENT_ID` | Unknown | False | Unknown |
| `LATLONG_RONIN_CLIENT_SECRET` | Unknown | False | Unknown |
| `LATLONG_RTR_API_URL` | Unknown | False | Unknown |
| `LATLONG_RTR_CLIENT_ID` | Unknown | False | Unknown |
| `LATLONG_RTR_CLIENT_SECRET` | Unknown | False | Unknown |
| `LATLONG_TOKEN_URL` | Unknown | False | Unknown |
| `LEAD_PROCESS` | Unknown | False | Unknown |
| `Logging:LogLevel:Default` | Unknown | False | app-settings |
| `Logging:LogLevel:Microsoft.AspNetCore` | Unknown | False | app-settings |
| `OLD_LMS_URL` | Unknown | False | Unknown |
| `PARTIAL_LEAD_PROCESS` | Unknown | False | Unknown |
| `SERVICE_BUS_CONNECTION_STRING` | Unknown | False | Unknown |
| `TOPIC_NAME` | Unknown | False | Unknown |
| `UPDATE_LEAD_PROCESS` | Unknown | False | Unknown |

## Ownership
lms ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |

## Local Setup
lms local setup evidence: build/test commands in HLC.md `Build and Test`; configuration from `appsettings.json` + `appsettings.<env>.json` (Development/Uat/Production); a Service Bus namespace and the LMS SQL database are required (connection settings by name above).

## Known Limitations
lms limitations evidenced in code:
- The Service Bus topic name (`TOPIC_NAME`) is not in the repo, so the registry cannot link lms to its subscribers; the four listener repos all read topic `lead` from their own appsettings (see DATA_FLOWS.md).
- README contains an EF scaffold command with inline connection details; values are not reproduced here and should be removed from the repo.
