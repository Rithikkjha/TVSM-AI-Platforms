---
service_id: lms-crm
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["lms crm", "lms_crm"]
---

# lms-crm — Overview

## Purpose
Summary: LMS CRM worker (.NET) consuming topic lms/CRM and pushing leads to CRM, dialer, Rezo and Salesforce CCP endpoints chosen by lead-flow configuration; no README.
Also known as: lms crm, lms_crm
lms-crm (`crmService`) is the LMS CRM push worker: a Service Bus listener on topic `lead` (subscription `CRM`) that pushes leads to CRM targets (`CRM_URL`, dialer `DIALER_URL`, CCP/Salesforce `CCP_URL`, Rezo `REZO_API_URL`) chosen from lead-flow configuration (`Services/CrmService.cs:44-69`, `Services/ApiExchangeService.cs:27,61,90`). No README.

## Users and Consumers
lms-crm HTTP callers (registry): none resolved.
Event producers feeding lms-crm: `lms-ems`, `lms-process`. Event consumers of messages lms-crm publishes: none resolved.

## Key Capabilities
lms-crm capabilities derived from code:
- Consumes `lms` / `CRM` (`ListenerService/CrmListenerService.cs:44`) → `CrmService.PushCrmLeads` (`CrmListenerService.cs:75`)
- Rezo, CCP (Salesforce, `external:salesforce`) and dialer pushes by lead-flow flags (`Services/CrmService.cs:51-65`)
- CRM push + threshold upsert + lead status update (`Services/CrmService.cs:72-105`)
- Posts results to the old LMS (`ExchangeService/LeadExchangeService.cs:27`)
- Health/root `GET /` (`CrmController.Crm`)

## Tech Stack
lms-crm tech stack (service.yaml `tech_stack`, `runs/TVS-CS/lms_crm/meta.json`):

| Layer | Technology | Version |
|---|---|---|
| Language | C# | net7.0 (`crmService.csproj:4`) |
| Framework | ASP.NET Core | see target framework |
| Data | SQL Server via EF Core (`Microsoft.EntityFrameworkCore.SqlServer`) | Unknown |
| Messaging | Azure Service Bus (`Azure.Messaging.ServiceBus`) | see csproj |
| Hosting | Unknown (no Dockerfile in repo) | - |

Key libraries: `AutoMapper.Extensions.Microsoft.DependencyInjection`, `Azure.Messaging.ServiceBus`, `Microsoft.AspNetCore.OpenApi`, `Microsoft.Azure.ServiceBus`, `Microsoft.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore.SqlServer`, `Microsoft.EntityFrameworkCore.Tools`, `Microsoft.VisualStudio.Azure.Containers.Tools.Targets`, `Newtonsoft.Json`, `Swashbuckle.AspNetCore`, `System.Data.SqlClient`

## Dependencies at a Glance
lms-crm upstream: `lms-ems`, `lms-process`.
Downstream: `external:salesforce` (Unknown).
Brokers: azure-service-bus. Data stores: `_` (mssql, key entities BrandMaster, DealerMediationControl, DialerToken …).

## Environments
lms-crm environments evidenced by config/pipeline files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| Development | Unknown | from appsettings files |
| Production | Unknown | from appsettings files |
| Uat | Unknown | from appsettings files |
| default | Unknown | from appsettings files |

## Environment Variables
lms-crm configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Secret | Provided by |
|---|---|---|---|
| `AllowedHosts` | Unknown | False | app-settings |
| `AppSettings:CCP_CLIENT_ID` | Unknown | True | app-settings |
| `AppSettings:CCP_CLIENT_SECRET` | Unknown | True | app-settings |
| `AppSettings:CCP_RECORD_TYPE_ID` | Unknown | False | app-settings |
| `AppSettings:CCP_TOKEN_URL` | Unknown | True | app-settings |
| `AppSettings:CCP_URL` | Unknown | False | app-settings |
| `AppSettings:CRM_KEY` | Unknown | True | app-settings |
| `AppSettings:CRM_SUBSCRIPTION` | Unknown | False | app-settings |
| `AppSettings:CRM_URL` | Unknown | False | app-settings |
| `AppSettings:DIALER_TOKEN_URL` | Unknown | True | app-settings |
| `AppSettings:DIALER_URL` | Unknown | False | app-settings |
| `AppSettings:OLD_LMS_URL` | Unknown | False | app-settings |
| `AppSettings:REZO_API_URL` | Unknown | False | app-settings |
| `AppSettings:REZO_AUTH_KEY` | Unknown | True | app-settings |
| `AppSettings:TOPIC_NAME` | Unknown | False | app-settings |
| `ConnectionStrings:DbConn` | Unknown | True | app-settings |
| `Logging:LogLevel:Default` | Unknown | False | app-settings |
| `Logging:LogLevel:Microsoft.AspNetCore` | Unknown | False | app-settings |
| `ServiceBusConnectionString` | Unknown | True | app-settings |
| `StateSettings` | Unknown | False | Unknown |
| `StateSettings:StateSource` | Unknown | False | Unknown |
| `StateSettings:StateSource:0` | Unknown | False | app-settings |
| `StateSettings:StateSource:1` | Unknown | False | app-settings |
| `StateSettings:StateSource:10` | Unknown | False | app-settings |
| `StateSettings:StateSource:11` | Unknown | False | app-settings |
| `StateSettings:StateSource:12` | Unknown | False | app-settings |
| `StateSettings:StateSource:13` | Unknown | False | app-settings |
| `StateSettings:StateSource:14` | Unknown | False | app-settings |
| `StateSettings:StateSource:15` | Unknown | False | app-settings |
| `StateSettings:StateSource:16` | Unknown | False | app-settings |
| `StateSettings:StateSource:17` | Unknown | False | app-settings |
| `StateSettings:StateSource:18` | Unknown | False | app-settings |
| `StateSettings:StateSource:19` | Unknown | False | app-settings |
| `StateSettings:StateSource:2` | Unknown | False | app-settings |
| `StateSettings:StateSource:20` | Unknown | False | app-settings |
| `StateSettings:StateSource:21` | Unknown | False | app-settings |
| `StateSettings:StateSource:22` | Unknown | False | app-settings |
| `StateSettings:StateSource:23` | Unknown | False | app-settings |
| `StateSettings:StateSource:24` | Unknown | False | app-settings |
| `StateSettings:StateSource:25` | Unknown | False | app-settings |
| `StateSettings:StateSource:26` | Unknown | False | app-settings |
| `StateSettings:StateSource:27` | Unknown | False | app-settings |
| `StateSettings:StateSource:28` | Unknown | False | app-settings |
| `StateSettings:StateSource:29` | Unknown | False | app-settings |
| `StateSettings:StateSource:3` | Unknown | False | app-settings |
| `StateSettings:StateSource:30` | Unknown | False | app-settings |
| `StateSettings:StateSource:31` | Unknown | False | app-settings |
| `StateSettings:StateSource:32` | Unknown | False | app-settings |
| `StateSettings:StateSource:33` | Unknown | False | app-settings |
| `StateSettings:StateSource:34` | Unknown | False | app-settings |
| `StateSettings:StateSource:35` | Unknown | False | app-settings |
| `StateSettings:StateSource:4` | Unknown | False | app-settings |
| `StateSettings:StateSource:5` | Unknown | False | app-settings |
| `StateSettings:StateSource:6` | Unknown | False | app-settings |
| `StateSettings:StateSource:7` | Unknown | False | app-settings |
| `StateSettings:StateSource:8` | Unknown | False | app-settings |
| `StateSettings:StateSource:9` | Unknown | False | app-settings |

## Ownership
lms-crm ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |

## Local Setup
lms-crm local setup evidence: build/test commands in HLC.md `Build and Test`; configuration from `appsettings.json` + `appsettings.<env>.json` (Development/Uat/Production); a Service Bus namespace and the LMS SQL database are required (connection settings by name above).

## Known Limitations
lms-crm limitations evidenced in code:
- Only CCP (`CCP_URL`) is matched to `external:salesforce`; CRM_URL, dialer and Rezo targets are config-only.
