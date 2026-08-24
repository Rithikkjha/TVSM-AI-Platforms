# Job Card Service — High Level Design

## System Purpose

The Job Card Service manages the creation, tracking, and updating of job cards (work orders) for vehicle services at TVS Motor dealerships. It provides the data backbone for service history, labour/parts management, and invoice retrieval — supporting omnichannel access from mobile apps, web portals, and messaging platforms.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        Client Applications                        │
├──────────────┬───────────────┬───────────────────────────────────┤
│ Digi DMS App │ CentralisedAPI│ TVS Connect / WhatsApp            │
│ (Android)    │ (Legacy DMS)  │ (Omnichannel)                     │
└──────┬───────┴───────┬───────┴───────────────┬───────────────────┘
       │               │                       │
       ▼               ▼                       ▼
┌──────────────────────────────────────────────────────────────────┐
│              Azure API Management (APIM) / Ingress               │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│              Job Card Service (AKS Pod - .NET 9)                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ API Layer (Controllers)                                     │ │
│  │ JobcardController | LabourController | PartsController |    │ │
│  │ AutoLaborController                                         │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│  ┌──────────────────────────┴──────────────────────────────────┐ │
│  │ Application Layer (Services)                                │ │
│  │ JobcardService | LabourService | PartsService |             │ │
│  │ AutoLaborService                                            │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│  ┌──────────────────────────┴──────────────────────────────────┐ │
│  │ Domain Layer (Entities + Repository Interfaces)             │ │
│  │ JobCard, Customer, Dealer, Vehicle, Labour, Parts, Invoice  │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│  ┌──────────────────────────┴──────────────────────────────────┐ │
│  │ Infrastructure Layer (EF Core + Repositories)               │ │
│  │ JobCardDbContext | ReminderDbContext | 37 Repositories       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
       │                                    │
       ▼                                    ▼
┌──────────────────┐             ┌──────────────────┐
│ onlineDMS        │             │ DMS_SMR_Trans    │
│ (Job Card DB)    │             │ (Reminder DB)    │
│ SQL Server       │             │ SQL Server       │
└──────────────────┘             └──────────────────┘
```

---

## Major Components

| Component | Responsibility |
|-----------|---------------|
| **API Layer** (4 Controllers) | HTTP routing, request validation, response formatting |
| **Application Layer** (4 Services) | Business logic orchestration, DTOs, validation |
| **Domain Layer** | Entity definitions, repository interfaces, domain exceptions |
| **Infrastructure Layer** | EF Core DbContexts, repository implementations, migrations |
| **Rate Limiter** | Fixed-window IP-based rate limiting (25 req/sec) |
| **OpenTelemetry** | Distributed traces + structured logs via OTLP |

---

## Key Design Decisions

1. **Clean Architecture** — API → Application → Domain ← Infrastructure (dependency inversion)
2. **Entity Framework Core 9.0** — Code-first with migrations; replaces stored procedure approach from legacy CentralisedAPI
3. **Domain-Driven Design** — Aggregates (Customer, Dealer, JobCard, Labour, Parts, Vehicle, Proforma)
4. **Rate limiting** — IP-based fixed window (25/sec) to protect against abuse
5. **Containerized** — Docker + AKS deployment (Linux containers)
6. **OpenTelemetry native** — Traces (ASP.NET Core + HTTP + SQL) + Logs exported to central collector
7. **No auth enforcement currently** — Bearer handler is a stub; relies on APIM/Ingress-level auth

---

## Deployment Topology

| Environment | Infrastructure | Database |
|-------------|---------------|----------|
| Dev | AKS (Azure Kubernetes Service) | 10.42.57.36 (onlineDMS_Staging) |
| UAT | AKS | UAT SQL Server instances |
| Production | AKS | Production SQL Server instances |

- **Container**: .NET 9 runtime on Linux (`mcr.microsoft.com/dotnet/aspnet:9.0`)
- **Port**: 8080
- **Timezone**: Asia/Kolkata
- **Secrets**: Azure Key Vault (mounted as env vars in AKS)
- **Observability**: OpenTelemetry → otel-gw-logs.tvsmotor.com → Grafana (Tempo + Loki)
- **CI/CD**: Azure DevOps (build → SonarQube → image scan → Helm deploy)
- **Helm chart name**: `job-card`

---

## Scalability Considerations

- Horizontal pod scaling in AKS based on CPU/memory
- EF Core connection pooling for SQL Server
- Rate limiting prevents individual IP abuse
- Stateless design (no session state) enables easy scaling
- Batch export for OTLP (configurable queue size, delay, batch size)

---

## Error Handling Strategy

- Controllers use try/catch with structured `Output` response objects
- Domain-specific exceptions (`PmlException`) for business rule violations
- HTTP status codes: 200, 201, 400, 404, 409, 422, 429, 500
- Structured logging via ILogger → OpenTelemetry → Loki
- No global exception middleware currently

---

## Resiliency Considerations

- Database connection retries via EF Core's built-in resiliency
- OTLP exporter can be disabled (`OTEL_EXPORTER_ENABLED=false`) if collector is unreachable
- Rate limiter protects against traffic spikes
- Health check endpoint (`/api/service/health/{dealerId}`) for liveness probes
