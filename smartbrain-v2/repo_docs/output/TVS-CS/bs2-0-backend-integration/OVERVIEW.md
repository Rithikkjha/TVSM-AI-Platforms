---
service_id: bs2-0-backend-integration
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["bs2.0 backend integration", "bs2.0backend_integration"]
---

# bs2-0-backend-integration — Overview

## Purpose
Summary: .NET backend exposing dealer-dashboard, bookings, booking-export and SAP endpoints, consuming a booking topic; no README, so business context beyond endpoint names is unclear.
Also known as: bs2.0 backend integration, bs2.0backend_integration
bs2-0-backend-integration is a `backend-api` repository (`BS2.0Backend_Integration`; service.yaml `type: backend-api`). Business purpose: Unknown — not stated in README/code.

## Users and Consumers
bs2-0-backend-integration is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
bs2-0-backend-integration capabilities derived from code:
- `DealerDashboardController`: 13 HTTP endpoint(s)
- `BookingsController`: 10 HTTP endpoint(s)
- `BookingExport`: 2 HTTP endpoint(s)
- `SAPController`: 2 HTTP endpoint(s)
- Scheduled job `ExportQueue` (hosted-service `None`)
- Publishes 1 messaging entit(y/ies); consumes 1

## Tech Stack
bs2-0-backend-integration tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | C# | Unknown |
| Framework | aspnet-core | Unknown |
| Data | mssql | Unknown |
| Messaging | azure-service-bus | Unknown |
| Hosting | Unknown (build: dotnet) | Unknown |

Key libraries: `AutoMapper.Extensions.Microsoft.DependencyInjection`, `Azure.Messaging.ServiceBus`, `ClosedXML`, `EPPlus`, `Microsoft.AspNet.WebApi.Core`, `Microsoft.AspNetCore.Authentication.JwtBearer`, `Microsoft.AspNetCore.OpenApi`, `Microsoft.Azure.ServiceBus`, `Microsoft.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore.Design`, `Microsoft.EntityFrameworkCore.SqlServer`, `Microsoft.Office.Interop.Excel`, `Newtonsoft.Json`, `SendGrid`, `Swashbuckle.AspNetCore`, `System.IdentityModel.Tokens.Jwt`

## Dependencies at a Glance
Upstream (calls bs2-0-backend-integration): Unknown
Downstream (bs2-0-backend-integration calls): none resolved; plus 1 outbound call(s) with unresolved target
Brokers: azure-service-bus. Data stores: `tvsmazevsdbprd01-dealer` (mssql, None)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
bs2-0-backend-integration environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| Development | Unknown | from config/infra file names |
| default | Unknown | from config/infra file names |

## Environment Variables
bs2-0-backend-integration configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `AllowedHosts` | Unknown | Unknown | False | app-settings |
| `AppSettings:BRIDGE_AUTH_TOKEN` | Unknown | Unknown | True | app-settings |
| `ConnectionStrings:DbConn` | Unknown | Unknown | True | app-settings |
| `Logging:LogLevel:Default` | Unknown | Unknown | False | app-settings |
| `Logging:LogLevel:Microsoft.AspNetCore` | Unknown | Unknown | False | app-settings |
| `ServiceBusSettings:ServiceBusEndpoint` | Unknown | Unknown | True | app-settings |
| `ServiceBusSettings:Subscription` | Unknown | Unknown | False | app-settings |
| `ServiceBusSettings:TopicName` | Unknown | Unknown | False | app-settings |

## Ownership
bs2-0-backend-integration ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
bs2-0-backend-integration local setup evidence:
- README: none
- Dockerfile(s): none found
- Build commands: see HLC.md `Build and Test`

## Known Limitations
bs2-0-backend-integration limitations evidenced by extraction:
- 1 outbound HTTP call(s) have no resolved target service (base URL from config/env).
- 1 messaging entit(y/ies) whose topic/queue name is not resolvable from code.
- No inbound callers resolved in the registry.
