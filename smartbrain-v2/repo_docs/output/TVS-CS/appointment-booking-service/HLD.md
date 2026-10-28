---
service_id: appointment-booking-service
doc_type: hld
last_reviewed: 2026-10-11
---

# appointment-booking-service — High-Level Design

## Context
appointment-booking-service is a `backend-api` in the TVS-CS org (domain: Unknown). Neighbours: callers Unknown; downstream none resolved.

## Architecture
appointment-booking-service components and connections (from service.yaml):

```mermaid
flowchart LR
  svc["appointment-booking-service"]
  svc --> db0[("env:DB_CONNECTION")]
```

## Integration Points
appointment-booking-service registry edges (0):

| Direction | Peer | Kind | Via | Criticality | Source | Match |
|---|---|---|---|---|---|---|
| N/A | | | | | | no registry edges |

## Data Ownership
appointment-booking-service data stores (service.yaml `data_stores`; ownership flag not determinable unless set):

| Store | Type | Access | Owned | Key entities |
|---|---|---|---|---|
| `env:DB_CONNECTION` | mssql | Unknown | Unknown | AppointmentBooking, AppointmentServFollowUpDet, Branch, Customer, CustomerAddress, CustomerContact, CustomerEndUser, CustomerRequest, CustomerVehicle, Dealer, DealerCustomerMapping, DealerEmployee, DealerVehicleMapping, EmpSubGroup, JobCardId … |

## Key Design Decisions
appointment-booking-service: N/A — not determinable from code.

| Decision | Alternatives considered | Reason |
|---|---|---|
| Unknown | Unknown | Unknown |

## Non-Functional Requirements
appointment-booking-service NFR targets: N/A — not determinable from code.

## Security
appointment-booking-service security: endpoint auth values None, bearer-jwt. No auth middleware found in code. 4 secret config key(s), sourced via: {'app-settings': 4} (names in OVERVIEW.md). PII handling: Unknown.

## Resilience and Failure Modes
appointment-booking-service hard dependencies: none resolved. No retry/circuit-breaker code found; failure behaviour Unknown.

## Deployment Topology
appointment-booking-service deployment artefacts (platform/regions: Unknown unless listed):

| Kind | Name | File | Environments | Image | Ports | Variable groups |
|---|---|---|---|---|---|---|
| azure-pipeline | azure_pipelines/ast-appointment-bs-prod-pipeline.yaml | `azure_pipelines/ast-appointment-bs-prod-pipeline.yaml:1` | - | - | - | PROD_Threshold, Tenable |
| azure-pipeline | azure_pipelines/ast-appointment-bs-uat-pipeline.yaml | `azure_pipelines/ast-appointment-bs-uat-pipeline.yaml:1` | - | - | - | Checkmarx_Common, Tenable, UAT_Threshold |
| azure-pipeline | azure_pipelines/ast-image-scan-appointment-booking-service-pipeline.yaml | `azure_pipelines/ast-image-scan-appointment-booking-service-pipeline.yaml:1` | - | - | - | Checkmarx_Common, UAT_Threshold |
| azure-pipeline | azure_pipelines/cd-pipeline.yaml | `azure_pipelines/cd-pipeline.yaml:1` | dev, prod, uat | - | - | - |
| azure-pipeline | azure_pipelines/ci-pipeline.yaml | `azure_pipelines/ci-pipeline.yaml:1` | - | - | - | - |
| azure-pipeline | azure_pipelines/sonar.yaml | `azure_pipelines/sonar.yaml:1` | - | - | - | - |
| dockerfile | Dockerfile | `Dockerfile:4` | - | mcr.microsoft.com/dotnet/aspnet:9.0, mcr.microsoft.com/dotnet/sdk:9.0 | 8080 | - |
| dockerfile | src/Appointment.API/Dockerfile | `src/Appointment.API/Dockerfile:5` | - | mcr.microsoft.com/dotnet/aspnet:9.0, mcr.microsoft.com/dotnet/sdk:9.0 | 8080 | - |

## Observability
appointment-booking-service observability libraries: `OpenTelemetry`, `OpenTelemetry.Exporter.OpenTelemetryProtocol`, `OpenTelemetry.Extensions.Hosting`, `OpenTelemetry.Instrumentation.AspNetCore`, `OpenTelemetry.Instrumentation.Http`. Related config keys: `Logging:IncludeScopes`, `Logging:LogLevel:Default`, `Logging:LogLevel:Microsoft`, `Logging:LogLevel:System`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, `OpenTelemetry:OTEL_EXPORTER_OTLP_ENDPOINT`, `OpenTelemetry:OTEL_SERVICE_NAME`. Dashboards/alerts: Unknown.
