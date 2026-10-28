---
service_id: appointment-booking-service
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["appointment booking service", "appointment api", "appointment booking", "appointment bs", "appointment"]
---

# appointment-booking-service — Overview

## Purpose
Summary: Backend API that lets customers schedule and manage vehicle service appointment requests online for dealerships and service centres, with appointment and vehicle endpoints.
Also known as: appointment booking service, appointment api, appointment booking, appointment bs, appointment
appointment-booking-service is a `backend-api` repository (`appointment-booking-service`; service.yaml `type: backend-api`). Business purpose: README (`README.md`) describes it as: Appointment Booking Service — Appointment Booking Service as a software solution enables customers to schedule and manage service appointments request online, streamlining the booking process for dealerships or service centers..
It contains 7 subprojects: `src/Appointment.API` (service), `src/Appointment.API.Tests` (test-suite), `src/Appointment.Application` (unknown), `src/Appointment.Application.Tests` (test-suite), `src/Appointment.Domain` (unknown), `src/Appointment.Infrastructure` (unknown), `src/Appointment.Infrastructure.Tests` (test-suite).

## Users and Consumers
appointment-booking-service is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
appointment-booking-service capabilities derived from code:
- `AppointmentController`: 7 HTTP endpoint(s)
- `Unknown`: 2 HTTP endpoint(s)
- `VehicleController`: 1 HTTP endpoint(s)

## Tech Stack
appointment-booking-service tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | C# | Unknown |
| Framework | aspnet-core | Unknown |
| Data | mssql | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: dotnet) | Unknown |

Key libraries: `DotNetEnv`, `EntityFramework`, `FluentValidation.AspNetCore`, `Microsoft.EntityFrameworkCore.Design`, `Microsoft.EntityFrameworkCore.SqlServer`, `Microsoft.EntityFrameworkCore.Tools`, `Microsoft.Extensions.Logging.Abstractions`, `Microsoft.VisualStudio.Azure.Containers.Tools.Targets`, `OpenTelemetry`, `OpenTelemetry.Exporter.OpenTelemetryProtocol`, `OpenTelemetry.Extensions.Hosting`, `OpenTelemetry.Instrumentation.AspNetCore`, `OpenTelemetry.Instrumentation.Http`, `SourceFlow.Stores.EntityFramework`, `Swashbuckle.AspNetCore`, `Swashbuckle.AspNetCore.Annotations`, `Swashbuckle.AspNetCore.Newtonsoft`, `Swashbuckle.AspNetCore.SwaggerGen`, `Swashbuckle.AspNetCore.SwaggerUI`

## Dependencies at a Glance
Upstream (calls appointment-booking-service): Unknown
Downstream (appointment-booking-service calls): none resolved
Brokers: none. Data stores: `env:DB_CONNECTION` (mssql, None)
Full detail: service.yaml `inbound` / `outbound`.

## Environments
appointment-booking-service environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
appointment-booking-service configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `ASPNETCORE_ENVIRONMENT` | Unknown | Unknown | False | env-file |
| `ASPNETCORE_URLS` | Unknown | Unknown | False | Unknown |
| `ASPNETCORE_URLS` | Unknown | Unknown | False | Unknown |
| `ConnectionStrings:AppointmentDbConnection` | Unknown | Unknown | True | app-settings |
| `ConnectionStrings:X-Content-Type-Options` | Unknown | Unknown | True | app-settings |
| `ConnectionStrings:aspNetCore` | Unknown | Unknown | True | app-settings |
| `ConnectionStrings:httpPlatformHandler` | Unknown | Unknown | True | app-settings |
| `DB_CONNECTION` | Unknown | Unknown | False | Unknown |
| `DEPLOYMENT_ENVIRONMENT` | Unknown | Unknown | False | Unknown |
| `Logging:IncludeScopes` | Unknown | Unknown | False | app-settings |
| `Logging:LogLevel:Default` | Unknown | Unknown | False | app-settings |
| `Logging:LogLevel:Microsoft` | Unknown | Unknown | False | app-settings |
| `Logging:LogLevel:System` | Unknown | Unknown | False | app-settings |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Unknown | Unknown | False | Unknown |
| `OTEL_SERVICE_NAME` | Unknown | Unknown | False | Unknown |
| `OpenTelemetry:DEPLOYMENT_ENVIRONMENT` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:OTEL_EXPORTER_OTLP_ENDPOINT` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:OTEL_SERVICE_NAME` | Unknown | Unknown | False | app-settings |
| `OpenTelemetry:SERVICE_VERSION` | Unknown | Unknown | False | app-settings |
| `PATH` | Unknown | Unknown | False | Unknown |
| `PATH` | Unknown | Unknown | False | Unknown |
| `SERVICE_VERSION` | Unknown | Unknown | False | Unknown |
| `SlotSettings` | Unknown | Unknown | False | Unknown |
| `SlotSettings:CapacityPerSlot` | Unknown | Unknown | False | app-settings |
| `SlotSettings:CapacityPerSlot` | Unknown | Unknown | False | Unknown |
| `SlotSettings:EndTime` | Unknown | Unknown | False | app-settings |
| `SlotSettings:EndTime` | Unknown | Unknown | False | Unknown |
| `SlotSettings:LunchEnd` | Unknown | Unknown | False | app-settings |
| `SlotSettings:LunchEnd` | Unknown | Unknown | False | Unknown |
| `SlotSettings:LunchStart` | Unknown | Unknown | False | app-settings |
| `SlotSettings:LunchStart` | Unknown | Unknown | False | Unknown |
| `SlotSettings:SlotDuration` | Unknown | Unknown | False | app-settings |
| `SlotSettings:SlotDuration` | Unknown | Unknown | False | Unknown |
| `SlotSettings:StartTime` | Unknown | Unknown | False | app-settings |
| `SlotSettings:StartTime` | Unknown | Unknown | False | Unknown |
| `TZ` | Unknown | Unknown | False | Unknown |

## Ownership
appointment-booking-service ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
appointment-booking-service local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
appointment-booking-service limitations evidenced by extraction:
- No inbound callers resolved in the registry.
