---
service_id: job-card-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["job card service", "jobcard api", "job card", "jobcard"]
---

# job-card-service — Overview

## Purpose
Summary: .NET Job Card Service managing creation, tracking and updating of vehicle-service job cards, labour, auto-labour, AMC and parts endpoints.
Also known as: job card service, jobcard api, job card, jobcard
job-card-service is a `backend-api` repository (`job-card-service`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: Job card Service — Job Card Service as a software solution manages the creation, tracking, and updating of job cards for vehicle services, streamlining workflow, task allocation, and customer communication..
It contains 7 subprojects: `src/Jobcard.API` (service), `src/Jobcard.APITests` (test-suite), `src/Jobcard.Application` (unknown), `src/Jobcard.ApplicationTests` (test-suite), `src/Jobcard.Domain` (unknown), `src/Jobcard.Infrastructure` (unknown), `src/Jobcard.InfrastructureTests` (test-suite).

## Users and Consumers
job-card-service is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
job-card-service capabilities derived from code:
- `JobcardController`: 6 HTTP endpoint(s)
- `LabourController`: 5 HTTP endpoint(s)
- `AutoLaborController`: 3 HTTP endpoint(s)
- `AmcController`: 1 HTTP endpoint(s)
- `PartsController`: 1 HTTP endpoint(s)

## Tech Stack
job-card-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | C# | Unknown |
| Framework | aspnet-core | Unknown |
| Data | mssql | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: dotnet) | Unknown |

Key libraries: `Azure.Security.KeyVault.Secrets`, `Microsoft.EntityFrameworkCore`, `Microsoft.EntityFrameworkCore.Design`, `Microsoft.EntityFrameworkCore.Relational`, `Microsoft.EntityFrameworkCore.SqlServer`, `Microsoft.EntityFrameworkCore.Tools`, `Microsoft.Extensions.Configuration.Abstractions`, `Microsoft.Extensions.Configuration.Binder`, `Microsoft.Extensions.DependencyInjection`, `Microsoft.Extensions.DependencyInjection.Abstractions`, `Microsoft.Extensions.Logging`, `Microsoft.VisualStudio.Azure.Containers.Tools.Targets`, `Newtonsoft.Json`, `OpenTelemetry.Exporter.OpenTelemetryProtocol`, `OpenTelemetry.Extensions.Hosting`, `OpenTelemetry.Instrumentation.AspNetCore`, `OpenTelemetry.Instrumentation.Http`, `OpenTelemetry.Instrumentation.SqlClient`, `RestSharp`, `Swashbuckle.AspNetCore`, `Swashbuckle.AspNetCore.Annotations`, `Swashbuckle.AspNetCore.Newtonsoft`, `Swashbuckle.AspNetCore.SwaggerGen`, `Swashbuckle.AspNetCore.SwaggerUI`, `System.ServiceModel.Duplex`, `System.ServiceModel.Federation`, `System.ServiceModel.Http`, `System.ServiceModel.NetTcp`, `System.ServiceModel.Security`

## Dependencies at a Glance
Upstream (calls job-card-service): Unknown
Downstream (job-card-service calls): none resolved; plus 1 outbound call(s) with unresolved target
Brokers: none. Data stores: `env:JOBCARD_DB_CONNECTION` (mssql, None), `env:REMINDER_DB_CONNECTION` (mssql, None)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
job-card-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
job-card-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `ASPNETCORE_URLS` | Unknown | Unknown | False | Unknown |
| `ASPNETCORE_URLS` | Unknown | Unknown | False | Unknown |
| `ConnectionStrings:JobcardDbConnection` | Unknown | Unknown | True | app-settings |
| `ConnectionStrings:ReminderDbConnection` | Unknown | Unknown | True | app-settings |
| `ConnectionStrings:X-Content-Type-Options` | Unknown | Unknown | True | app-settings |
| `ConnectionStrings:aspNetCore` | Unknown | Unknown | True | app-settings |
| `ConnectionStrings:httpPlatformHandler` | Unknown | Unknown | True | app-settings |
| `DEPLOYMENT_ENVIRONMENT` | Unknown | Unknown | False | Unknown |
| `ExpectedSacCode` | Unknown | Unknown | False | Unknown |
| `FrtAutoLaborActionDescription` | Unknown | Unknown | False | Unknown |
| `FrtAutoLaborCategoryDescription` | Unknown | Unknown | False | Unknown |
| `FrtAutoLaborCategoryId` | Unknown | Unknown | False | Unknown |
| `FrtAutoLaborItemTypeDescription` | Unknown | Unknown | False | Unknown |
| `FrtAutoLaborItemTypeId` | Unknown | Unknown | False | Unknown |
| `FrtAutoLaborSACCode` | Unknown | Unknown | False | Unknown |
| `JOBCARD_DB_CONNECTION` | Unknown | Unknown | False | Unknown |
| `Keys` | Unknown | Unknown | False | Unknown |
| `LaborSettings:FrtAutoLaborSACCode` | Unknown | Unknown | False | Unknown |
| `LaborSettings:MaxFrt:Frt` | Unknown | Unknown | False | app-settings |
| `LaborSettings:MaxFrt:Frt` | Unknown | Unknown | False | Unknown |
| `LaborSettings:MaxFrt:TimeInMinutes` | Unknown | Unknown | False | app-settings |
| `LaborSettings:MaxFrt:TimeInMinutes` | Unknown | Unknown | False | Unknown |
| `LaborSettings:SacCode` | Unknown | Unknown | False | app-settings |
| `Logging:IncludeScopes` | Unknown | Unknown | False | app-settings |
| `Logging:LogLevel:Default` | Unknown | Unknown | False | app-settings |
| `Logging:LogLevel:Microsoft` | Unknown | Unknown | False | app-settings |
| `Logging:LogLevel:System` | Unknown | Unknown | False | app-settings |
| `OTEL_BSP_EXPORT_TIMEOUT_SECONDS` | Unknown | Unknown | False | Unknown |
| `OTEL_BSP_MAX_EXPORT_BATCH_SIZE` | Unknown | Unknown | False | Unknown |
| `OTEL_BSP_MAX_QUEUE_SIZE` | Unknown | Unknown | False | Unknown |
| `OTEL_BSP_SCHEDULE_DELAY_SECONDS` | Unknown | Unknown | False | Unknown |
| `OTEL_EXPORTER_ENABLED` | Unknown | Unknown | False | Unknown |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Unknown | Unknown | False | Unknown |
| `OTEL_EXPORTER_TIMEOUT_SECONDS` | Unknown | Unknown | False | Unknown |
| `OTEL_SERVICE_NAME` | Unknown | Unknown | False | Unknown |
| `OpenTelemetry:DEPLOYMENT_ENVIRONMENT` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:OTEL_BSP_EXPORT_TIMEOUT_SECONDS` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:OTEL_BSP_MAX_EXPORT_BATCH_SIZE` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:OTEL_BSP_MAX_QUEUE_SIZE` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:OTEL_BSP_SCHEDULE_DELAY_SECONDS` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:OTEL_EXPORTER_ENABLED` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:OTEL_EXPORTER_OTLP_ENDPOINT` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:OTEL_EXPORTER_TIMEOUT_SECONDS` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:OTEL_SERVICE_NAME` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:SERVICE_VERSION` | Unknown | Unknown | False | app-settings |
| `PATH` | Unknown | Unknown | False | Unknown |
| `PATH` | Unknown | Unknown | False | Unknown |
| `PmlSettings:Description` | Unknown | Unknown | False | app-settings |
| `PmlSettings:Description` | Unknown | Unknown | False | Unknown |
| `PmlSettings:FreeServiceJobTypes` | Unknown | Unknown | False | Unknown |
| `PmlSettings:FreeServiceJobTypes:0` | Unknown | Unknown | False | app-settings |
| `PmlSettings:FreeServiceJobTypes:1` | Unknown | Unknown | False | app-settings |
| `PmlSettings:FreeServiceJobTypes:2` | Unknown | Unknown | False | app-settings |
| `PmlSettings:FreeServiceJobTypes:3` | Unknown | Unknown | False | app-settings |
| `PmlSettings:FreeServiceJobTypes:4` | Unknown | Unknown | False | app-settings |
| `PmlSettings:FreeServiceJobTypes:5` | Unknown | Unknown | False | app-settings |
| `PmlSettings:FreeServiceJobTypes:6` | Unknown | Unknown | False | app-settings |
| `PmlSettings:FreeServiceJobTypes:7` | Unknown | Unknown | False | app-settings |
| `PmlSettings:FreeServiceJobTypes:8` | Unknown | Unknown | False | app-settings |
| `PmlSettings:FreeServiceJobTypes:9` | Unknown | Unknown | False | app-settings |
| `PmlSettings:HsnCode` | Unknown | Unknown | False | app-settings |
| `PmlSettings:HsnCode` | Unknown | Unknown | False | Unknown |
| `PmlSettings:ItemTaxCatId` | Unknown | Unknown | False | app-settings |
| `PmlSettings:ItemTaxCatId` | Unknown | Unknown | False | Unknown |
| `PmlSettings:ItemTypeId` | Unknown | Unknown | False | app-settings |
| `PmlSettings:ItemTypeId` | Unknown | Unknown | False | Unknown |
| `PmlSettings:LabourCatId` | Unknown | Unknown | False | app-settings |
| `PmlSettings:LabourCatId` | Unknown | Unknown | False | Unknown |
| `PmlSettings:PaidServiceJobTypes` | Unknown | Unknown | False | Unknown |
| `PmlSettings:PaidServiceJobTypes:0` | Unknown | Unknown | False | app-settings |
| `REMINDER_DB_CONNECTION` | Unknown | Unknown | False | Unknown |
| `RateLimiterSettings` | Unknown | Unknown | False | Unknown |
| `RateLimiterSettings:PermitLimit` | Unknown | Unknown | False | app-settings |
| `RateLimiterSettings:WindowInSeconds` | Unknown | Unknown | False | app-settings |
| `SERVICE_VERSION` | Unknown | Unknown | False | Unknown |
| `TZ` | Unknown | Unknown | False | Unknown |

## Ownership
job-card-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
job-card-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
job-card-service limitations evidenced by extraction:
- 1 outbound HTTP call(s) have no resolved target service (base URL from config/env).
- No inbound callers resolved in the registry.
