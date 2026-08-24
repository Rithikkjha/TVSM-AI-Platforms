# High Level Code Document – Appointment Booking Service

> **Note**: This is a supplementary document. For SmartBrain AI dependency mapping, refer to [API_SPEC.md](./API_SPEC.md) (primary) and [HLD.md](./HLD.md).

---

## Application Overview

| Field | Value |
|-------|-------|
| Service Name | appointment-booking-service |
| Runtime | .NET 9 / ASP.NET Core |
| Architecture | Clean Architecture + DDD |
| Database | SQL Server (OnlineDMS) via EF Core 9 |
| Observability | OpenTelemetry (traces + logs) |
| Containerization | Docker → AKS |

The service manages vehicle service appointment lifecycle for TVS Motor dealerships — creation, slot availability, updates (reschedule/cancel), and multi-criteria search.

---

## Module Summary

| Module | Layer | Key Responsibility |
|--------|-------|--------------------|
| Appointment.API | Presentation | HTTP routing, Swagger, auth middleware |
| Appointment.Application | Business | Service logic, validation, DTO mapping, slot generation |
| Appointment.Domain | Domain | Entities, aggregates, repository contracts, enumerations |
| Appointment.Infrastructure | Data | EF Core persistence, repository implementations, migrations |

---

## Dependency Overview

### NuGet Packages

| Package | Version | Layer | Purpose |
|---------|---------|-------|---------|
| Microsoft.EntityFrameworkCore.SqlServer | 9.0.1 | Infrastructure | SQL Server provider |
| FluentValidation.AspNetCore | 11.3.0 | Application | Request validation |
| Swashbuckle.AspNetCore | 6.4.0 | API | OpenAPI/Swagger |
| OpenTelemetry | 1.15.0 | API | Distributed tracing |
| OpenTelemetry.Exporter.OpenTelemetryProtocol | 1.15.0 | API | OTLP export |
| OpenTelemetry.Instrumentation.AspNetCore | 1.15.1 | API | Auto-instrumentation |
| DotNetEnv | 3.1.1 | API | .env file loading |
| Newtonsoft.Json | — | API | JSON deserialization |

### Project References

```
Appointment.API
  ├── → Appointment.Application → Appointment.Domain
  └── → Appointment.Infrastructure → Appointment.Application → Appointment.Domain
```

---

## Runtime Flow

```
HTTP Request
    │
    ▼
┌──────────────────────┐
│  ASP.NET Middleware   │  HTTPS redirect → Auth → Routing
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     Controller       │  Deserialize → Route to service
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   AppointmentService │  Validate → Business logic → Map DTOs
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Repository (EF)    │  LINQ queries → SQL Server
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   SQL Server         │  OnlineDMS database
└──────────────────────┘
```

---

## Key Services

### AppointmentService (Core)

| Method | Purpose |
|--------|---------|
| `Create()` | Legacy appointment creation → `AppointmentBooking` table |
| `CreateAppointmentBooking()` | Full booking with transactions → `ServAppointments` table |
| `GetAppointmentByFrameNo()` | Fetch by vehicle frame number |
| `GetAppointmentSlotByDealerBranchId()` | Calculate available time slots |
| `UpdateAppointment()` | Reschedule/cancel with follow-up tracking |
| `GetAppointmentsAsync()` | Multi-criteria search |
| `DealerExistsAsync()` | Health check |

### VehicleService

| Method | Purpose |
|--------|---------|
| `GetVehicleDetailsAsync()` | Lookup by mobile/frame/registration |

---

## Integration Summary

| Integration | Type | Direction | Purpose |
|-------------|------|-----------|---------|
| SQL Server (OnlineDMS) | Database | Bidirectional | Primary data store |
| OpenTelemetry Collector | HTTP/OTLP | Outbound | Traces + logs |
| API Gateway | HTTP | Inbound | Client request routing |
| TVS Connect App | HTTP | Inbound | Mobile client |
| Dealer Portal | HTTP | Inbound | Web client |

---

## Data Flow: Appointment Creation (New)

```
1. Client → POST /api/service/appointment/create
2. Deserialize JSON → AppointmentBookingRequestDto
3. Validate: dealer exists, branch valid, vehicle exists, customer exists
4. Ensure DealerVehicleMapping + DealerCustomerMapping
5. BEGIN TRANSACTION
6. Get next ID from JobCardIds
7. Resolve: RegistrationNo, APT_CAT_ID, EndUserId
8. INSERT → ServAppointments
9. INSERT → ServiceAppointmentRequests + SubRequests
10. UPDATE → JobCardIds (increment)
11. COMMIT
12. Return { AppointmentId, AppointmentDateTime }
```

## Data Flow: Slot Calculation

```
1. Query booked appointments for dealer/branch in [fromDate, toDate]
2. Get service advisor count for branch
3. totalCapacity = advisorCount × capacityPerSlot (default 4)
4. Generate 30-min slots: 10AM–6PM (skip 1–2PM lunch)
5. available = totalCapacity − bookedInSlot
6. Return per-day slot grid with availability
```

---

*Last updated: July 2026*
