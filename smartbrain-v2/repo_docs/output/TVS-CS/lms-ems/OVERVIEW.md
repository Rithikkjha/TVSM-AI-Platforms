---
service_id: lms-ems
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["lms ems", "lms_ems"]
---

# lms-ems — Overview

## Purpose
Summary: LMS EMS worker (.NET) consuming topic lms/EMS, pushing leads to the EMS API and re-publishing CRM fallback, delayed retry and dealer-retry messages to the same topic.
Also known as: lms ems, lms_ems
lms-ems (`emsService`) is the LMS EMS push worker: a Service Bus listener on topic `lead` (subscription `EMS`) that pushes leads to the EMS API (`EMS_API_URL` / `EMS_API_AGGREGATOR_URL`, `emsService/Services/EmsService.cs:152-156`), records push logs and re-publishes to the `lead` topic for CRM fallback, delayed EMS retry, threshold delay and dealer retry (`emsService/Services/EmsService.cs:47,191,199,214`). README (`readme.md`) only contains EF scaffold notes.

## Users and Consumers
lms-ems HTTP callers (registry): none resolved.
Event producers feeding lms-ems: `lms-process`. Event consumers of messages lms-ems publishes: `lms-crm`, `lms-process`, `lms-tvs-credit`.

## Key Capabilities
lms-ems capabilities derived from code:
- Consumes `lms` / `EMS` (`emsService/ListenerService/EmsListenerService.cs:43`) and calls `EmsService.ProcessEmsLead` (`EmsListenerService.cs:75`)
- Pushes leads to EMS over HTTP POST (`emsService/Services/EmsService.cs:152`)
- Publishes to `lms` with target `CRM_SUBSCRIPTION` (CRM fallback), `EMS_SUBSCRIPTION` (30-minute delayed retry / threshold delay) and `PROCESS_SUBSCRIPTION` (dealer retry) (`emsService/Services/EmsService.cs:47,191,199,214`, `DispatchService.cs:16-50`)
- Repush of threshold leads (`emsService/Services/RepushService.cs:30`)
- Posts results to the old LMS (`OLD_LMS_URL`, `emsService/ExchangeService/ApiExchangeService.cs:46`)
- Health/root `GET /` (`EmsController.Ems`)

## Tech Stack
lms-ems tech stack (service.yaml `tech_stack`, `runs/TVS-CS/lms_ems/meta.json`):

| Layer | Technology | Version |
|---|---|---|
| Language | C# | net7.0 (`emsService/emsService.csproj:4`) |
| Framework | ASP.NET Core | see target framework |
| Data | SQL Server via EF Core (`Microsoft.EntityFrameworkCore.SqlServer`) | Unknown |
| Messaging | Azure Service Bus (`Azure.Messaging.ServiceBus`) | see csproj |
| Hosting | Unknown (no Dockerfile in repo) | - |

Key libraries: `AutoMapper.Extensions.Microsoft.DependencyInjection`, `Azure.Messaging.ServiceBus`, `Microsoft.AspNetCore.OpenApi`, `Microsoft.Azure.ServiceBus`, `Microsoft.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore.SqlServer`, `Microsoft.EntityFrameworkCore.Tools`, `Microsoft.VisualStudio.Azure.Containers.Tools.Targets`, `Newtonsoft.Json`, `Swashbuckle.AspNetCore`, `System.Data.SqlClient`, `coverlet.msbuild`

## Dependencies at a Glance
lms-ems upstream: `lms-process`.
Downstream: no registry-resolved HTTP target; event consumers `lms-crm`, `lms-process`, `lms-tvs-credit`.
Brokers: azure-service-bus. Data stores: `_` (mssql, key entities BrandMaster, DealerMediationControl, Lead …).

## Environments
lms-ems environments evidenced by config/pipeline files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| Development | Unknown | from appsettings files |
| Production | Unknown | from appsettings files |
| Uat | Unknown | from appsettings files |
| default | Unknown | from appsettings files |

## Environment Variables
lms-ems configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Secret | Provided by |
|---|---|---|---|
| `AggregatorSettings:AggregatorSource:0` | Unknown | False | app-settings |
| `AggregatorSettings:AggregatorSource:1` | Unknown | False | app-settings |
| `AggregatorSettings:AggregatorSource:2` | Unknown | False | app-settings |
| `AllowedHosts` | Unknown | False | app-settings |
| `AppSettings:API_KEY_VALUE` | Unknown | True | app-settings |
| `AppSettings:CRM_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:DMS_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:EMS_API_AGGREGATOR_URL` | Unknown | False | app-settings |
| `AppSettings:EMS_API_URL` | Unknown | False | app-settings |
| `AppSettings:EMS_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:OLD_LMS_URL` | Unknown | False | app-settings |
| `AppSettings:PROCESS_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:TOPIC_NAME` | Unknown | False | app-settings |
| `ConnectionStrings:DbConn` | Unknown | True | app-settings |
| `Logging:LogLevel:Default` | Unknown | False | app-settings |
| `Logging:LogLevel:Microsoft.AspNetCore` | Unknown | False | app-settings |
| `ServiceBusConnectionString` | Unknown | True | app-settings |

## Ownership
lms-ems ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |

## Local Setup
lms-ems local setup evidence: build/test commands in HLC.md `Build and Test`; configuration from `appsettings.json` + `appsettings.<env>.json` (Development/Uat/Production); a Service Bus namespace and the LMS SQL database are required (connection settings by name above).

## Known Limitations
lms-ems limitations evidenced in code:
- EMS API URLs are config-driven and not resolved to a registry service or `external:` system.
