# High Level Design (HLD) – Appointment Booking Service

## Service Identity

| Field | Value |
|-------|-------|
| Service Name | appointment-booking-service |
| Repo | github.com/tvsmotorcompany/appointment-booking-service |
| Team | Digital Engineering |
| Tech Lead | @sapna.bhandari |
| Deployment | AKS (Azure Kubernetes Service) |
| Runtime | .NET 9 / ASP.NET Core |

---

## System Purpose

The Appointment Booking Service enables customers to schedule, manage, and track vehicle service appointments online. It solves the problem of manual appointment scheduling at dealerships by providing:

- Multi-channel appointment creation (Mobile App, Dealer Portal)
- Time slot availability management based on service advisor capacity
- Appointment lifecycle management (create → reschedule → cancel → close)
- Multi-criteria search across dealers, vehicles, and customers

---

## Architecture Diagram Description

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Clients                                      │
│   ┌─────────────┐   ┌──────────────┐   ┌────────────────────┐       │
│   │ TVS Connect │   │ Dealer Portal│   │ Admin Portal       │       │
│   │  Mobile App │   │    (Web)     │   │    (Web)           │       │
│   └──────┬──────┘   └──────┬───────┘   └─────────┬──────────┘       │
└──────────┼──────────────────┼─────────────────────┼──────────────────┘
           │                  │                     │
           ▼                  ▼                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        API Gateway                                    │
│  Base: /virts/tvsmotorcompany/appointment-booking-service/1.0.0      │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ HTTPS
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│              Appointment Booking Service (AKS Pod)                    │
│                                                                      │
│  ┌────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│  │    API     │───→│   Application    │───→│     Domain       │     │
│  │  (ASP.NET  │    │  (Services +     │    │  (Entities +     │     │
│  │   Core)    │    │   Validators)    │    │   Contracts)     │     │
│  └────────────┘    └──────────────────┘    └──────────────────┘     │
│        │                                           ▲                  │
│        │           ┌──────────────────┐            │                  │
│        └──────────→│  Infrastructure  │────────────┘                  │
│                    │  (EF Core +      │                               │
│                    │   Repositories)  │                               │
│                    └────────┬─────────┘                               │
└─────────────────────────────┼────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               │               ▼
     ┌──────────────┐        │      ┌─────────────────┐
     │  SQL Server  │        │      │  OpenTelemetry  │
     │  (OnlineDMS) │        │      │   Collector     │
     └──────────────┘        │      └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Azure DevOps   │
                    │   Pipelines     │
                    └─────────────────┘
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Clean Architecture (4 layers) | Separation of concerns, testability, domain isolation |
| DDD (Domain-Driven Design) | Complex business rules around appointments, dealers, vehicles |
| Shared Database (OnlineDMS) | Existing DMS system — service reads/writes to shared SQL Server |
| UnitOfWork pattern | Multi-table transactional integrity for appointment creation |
| Custom ID generation (JobCardIds) | Dealer-specific sequential numbering requirement |
| Two appointment flows (legacy + new) | Migration path from legacy system to new normalized schema |
| Synchronous-only | No async messaging — all operations are request/response |
| No caching layer | Data freshness priority over read performance |

---

## Scalability Approach

| Aspect | Strategy |
|--------|----------|
| Horizontal scaling | Stateless pods — scale replicas via Kubernetes HPA |
| Database connections | Max pool: 2500, Connect timeout: 200s |
| Container orchestration | AKS manages pod lifecycle, health, and scaling |
| Read performance | EF Core `AsNoTracking()` for read-only queries |
| Query optimization | Selective includes, filtered queries, `Take()` for pagination |

### Scalability Constraints

- **Shared database**: OnlineDMS is shared with other DMS services — DB is the bottleneck
- **No read replicas**: All reads go to primary
- **No caching**: Slot availability recalculated on every request
- **Sequential ID generation**: `JobCardIds` table creates serialization point per dealer/branch

---

## Error Handling Strategy

| Layer | Strategy |
|-------|----------|
| Controller | try-catch with structured error responses (`Output` DTO) |
| Service | Transaction rollback on failure, structured logging before re-throw |
| Repository | EF Core exception propagation |
| Validation | FluentValidation + custom validators — fail fast before DB operations |

### Error Response Contract

```json
{
  "statusCode": 400,
  "message": "Human-readable error description"
}
```

### HTTP Status Mapping

| Exception Type | HTTP Status |
|---------------|-------------|
| Message contains "Exists" | 409 Conflict |
| `KeyNotFoundException` | 404 Not Found |
| `ValidationException` | 400 Bad Request |
| `InvalidOperationException` | 400 Bad Request |
| Generic `Exception` | 400 Bad Request |

---

## Deployment Topology

### Container

| Property | Value |
|----------|-------|
| Base Image | mcr.microsoft.com/dotnet/aspnet:9.0 |
| Port | 8080 |
| Timezone | Asia/Kolkata (IST) |
| Build | Multi-stage Docker (SDK → Publish → Runtime) |

### CI/CD Pipeline (Azure DevOps)

| Pipeline | Purpose |
|----------|---------|
| `ci-pipeline.yaml` | Build + test + Docker image |
| `cd-pipeline.yaml` | Deploy to environments |
| `ast-appointment-bs-uat-pipeline.yaml` | UAT deployment |
| `ast-appointment-bs-prod-pipeline.yaml` | Production deployment |
| `ast-image-scan-appointment-booking-service-pipeline.yaml` | Security image scan |
| `sonar.yaml` | Code quality analysis |

### Environment Configuration

| Environment | Config Source |
|-------------|--------------|
| Local | `appsettings.json` + `.env` file |
| UAT/Prod | Kubernetes ConfigMaps + Secrets (environment variables) |

---

## Data Flow

### Appointment Creation (New Flow)

```
1. Client → POST /api/service/appointment/create
2. Controller deserializes request
3. Validator checks: dealer, branch, vehicle, customer existence
4. Ensure dealer-vehicle and dealer-customer mappings
5. Begin DB transaction
6. Generate next appointment ID (JobCardIds)
7. Resolve: registration number, category, end-user
8. INSERT ServAppointment
9. INSERT ServiceAppointmentRequests + SubRequests
10. UPDATE JobCardIds (increment)
11. Commit transaction
12. Return { appointmentId, appointmentDateTime }
```

### Slot Availability Calculation

```
1. Client → POST /api/service/appointment/fetch/slot
2. Query booked appointments for dealer/branch in date range
3. Query service advisor count for branch
4. Calculate: totalCapacity = advisorCount × capacityPerSlot
5. Generate 30-min slots (10AM–6PM, skip 1–2PM lunch)
6. For each slot: available = totalCapacity − bookedInSlot
7. Return daily availability grid
```

---

## Observability

| Aspect | Implementation |
|--------|---------------|
| Distributed Tracing | OpenTelemetry → OTLP HTTP → otel-gw-logs.tvsmotor.com/v1/traces |
| Structured Logging | OpenTelemetry → OTLP HTTP → otel-gw-logs.tvsmotor.com/v1/logs |
| ASP.NET Core instrumentation | Request/response tracing (auto) |
| HttpClient instrumentation | Outbound HTTP tracing (auto) |

---

## Security

| Aspect | Current State |
|--------|--------------|
| Authentication | Bearer token handler exists (placeholder — no real validation) |
| Authorization | `UseAuthorization()` middleware enabled, no `[Authorize]` on controllers |
| HTTPS | Enforced via `UseHttpsRedirection()` |
| SQL Injection | Protected by EF Core parameterized queries |
| Input Validation | FluentValidation + DataAnnotation attributes |

---

## Potential Improvements

- Implement real JWT token validation in `BearerAuthenticationHandler`
- Add `[Authorize]` attribute to all controllers
- Introduce Redis caching for dealer/vehicle master data
- Add health check endpoints (`/health/live`, `/health/ready`) for K8s probes
- Implement retry policies (Polly) for transient DB failures
- Add async event publishing (Service Bus) for appointment state changes
- Separate read model from write model (CQRS) for search performance
- Add rate limiting at application level

---

*Last updated: July 2026*
