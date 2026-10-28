---
service_id: lms-tvs-credit
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["lms tvs credit", "lms_tvs_credit", "norton ls tvs credit"]
---

# lms-tvs-credit — Overview

## Purpose
Summary: LMS finance worker (.NET) consuming topic lms/FINANCE, mapping dealers to TVS Credit codes and pushing finance leads to the TVS Credit lead API.
Also known as: lms tvs credit, lms_tvs_credit, norton ls tvs credit
lms-tvs-credit is the LMS finance push worker: a Service Bus listener on topic `lead` (subscription `FINANCE` in Development/Uat/Production appsettings) that maps dealers/cities/states to TVS Credit codes and pushes finance leads to the TVS Credit lead API (`TvsCrrditLeadPushURL`), then logs the result and posts it to the old LMS (`lms_tvs_credit/Services/TvscreditService.cs:52-125`). `lms_tvs_credit/Readme.md` holds EF scaffold notes only.

## Users and Consumers
lms-tvs-credit HTTP callers (registry): none resolved.
Event producers feeding lms-tvs-credit: `lms-ems`, `lms-process`. Event consumers of messages lms-tvs-credit publishes: none resolved.

## Key Capabilities
lms-tvs-credit capabilities derived from code:
- Consumes `lms` / `FINANCE` (`lms_tvs_credit/ListenerService/TvscreditListenerService.cs:46`) → `TvscreditService.PushFinanceLeads` (`TvscreditListenerService.cs:75`)
- Dealer code mapping (`GetTvsCreditDealerCode`, `lms_tvs_credit/Services/TvscreditService.cs:26`) using `tvscredit_*_master` tables
- HTTP POST to the TVS Credit lead URL `TvsCrrditLeadPushURL` (`lms_tvs_credit/Services/TvscreditService.cs:83,128-135`); dealer lookup via `TvsCrrditDealerURL` (`TvscreditService.cs:34`)
- Finance push log + old-LMS publish (`TvscreditService.cs:121-124`)
- Health/root `GET /` (`TvsCreditController.Credit`)

## Tech Stack
lms-tvs-credit tech stack (service.yaml `tech_stack`, `runs/TVS-CS/lms_tvs_credit/meta.json`):

| Layer | Technology | Version |
|---|---|---|
| Language | C# | net7.0 (`lms_tvs_credit/lms_tvs_credit.csproj:4`) |
| Framework | ASP.NET Core | see target framework |
| Data | SQL Server via EF Core (`Microsoft.EntityFrameworkCore.SqlServer`) | Unknown |
| Messaging | Azure Service Bus (`Azure.Messaging.ServiceBus`) | see csproj |
| Hosting | Unknown (no Dockerfile in repo) | - |

Key libraries: `AutoMapper.Extensions.Microsoft.DependencyInjection`, `Azure.Messaging.ServiceBus`, `Microsoft.AspNetCore.OpenApi`, `Microsoft.Azure.ServiceBus`, `Microsoft.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore.SqlServer`, `Microsoft.EntityFrameworkCore.Tools`, `Newtonsoft.Json`, `Swashbuckle.AspNetCore`, `System.Data.SqlClient`

## Dependencies at a Glance
lms-tvs-credit upstream: `lms-ems`, `lms-process`.
Downstream: no registry-resolved HTTP target.
Brokers: azure-service-bus. Data stores: `_` (mssql, key entities DealerMediationControl, LeadPushLog, TvscreditCityMaster …).

## Environments
lms-tvs-credit environments evidenced by config/pipeline files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| Development | Unknown | from appsettings files |
| Production | Unknown | from appsettings files |
| Uat | Unknown | from appsettings files |
| default | Unknown | from appsettings files |

## Environment Variables
lms-tvs-credit configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Secret | Provided by |
|---|---|---|---|
| `AllowedHosts` | Unknown | False | app-settings |
| `AppSettings:AgencyCode` | Unknown | False | app-settings |
| `AppSettings:ChannelCode` | Unknown | False | app-settings |
| `AppSettings:DealerSource` | Unknown | False | app-settings |
| `AppSettings:OLD_LMS_URL` | Unknown | False | app-settings |
| `AppSettings:ProductCode` | Unknown | False | app-settings |
| `AppSettings:QUEUE` | Unknown | False | app-settings |
| `AppSettings:SERVICE_BUS_ENDPOINT` | Unknown | True | app-settings |
| `AppSettings:SUBSCRIPTION_NAME` | Unknown | False | app-settings |
| `AppSettings:TOPIC_NAME` | Unknown | False | app-settings |
| `AppSettings:TvsCrrditDealerURL` | Unknown | False | app-settings |
| `AppSettings:TvsCrrditLeadPushURL` | Unknown | False | app-settings |
| `ConnectionStrings:DbConn` | Unknown | True | app-settings |
| `Logging:LogLevel:Default` | Unknown | False | app-settings |
| `Logging:LogLevel:Microsoft.AspNetCore` | Unknown | False | app-settings |

## Ownership
lms-tvs-credit ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |

## Local Setup
lms-tvs-credit local setup evidence: build/test commands in HLC.md `Build and Test`; configuration from `appsettings.json` + `appsettings.<env>.json` (Development/Uat/Production); a Service Bus namespace and the LMS SQL database are required (connection settings by name above).

## Known Limitations
lms-tvs-credit limitations evidenced in code:
- TVS Credit endpoint is config-only (`TvsCrrditLeadPushURL`); not resolved to a registry service or `external:` system.
