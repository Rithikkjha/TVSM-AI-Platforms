# Appointment Booking Service

A .NET 9 Web API that enables customers to schedule and manage vehicle service appointments online, streamlining the booking process for TVS Motor dealerships and service centers.

---

## Service Identity

| Field | Value |
|-------|-------|
| Service Name | appointment-booking-service |
| Repo | github.com/tvsmotorcompany/appointment-booking-service |
| Team | Digital Engineering |
| Tech Lead | @sapna.bhandari |
| Deployment | AKS (Azure Kubernetes Service) |
| Base URL (prod) | https://api.tvsmotor.com/virts/tvsmotorcompany/appointment-booking-service/1.0.0 |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Tech Lead | Dushyant Singh Satyapal | Dushyant.Satyapal@tvsmotor.com |
| Dev Team | Digital Engineering | <!-- TODO: Teams channel --> |

---

## How to Run Locally

### Prerequisites

- [.NET 9 SDK](https://dotnet.microsoft.com/download/dotnet/9.0)
- SQL Server (local or remote)

### Steps

```bash
# 1. Clone
git clone <repository-url>
cd appointment-booking-service

# 2. Restore dependencies
dotnet restore src/Appointment.API/Appointment.API.csproj

# 3. Configure database (edit appsettings.json or set env var)
# Update ConnectionStrings:AppointmentDbConnection

# 4. Run migrations
dotnet ef database update \
  --project src/Appointment.Infrastructure/Appointment.Infrastructure.csproj \
  --startup-project src/Appointment.API/Appointment.API.csproj

# 5. Run the service
dotnet run --project src/Appointment.API/Appointment.API.csproj
```

Swagger UI: `https://localhost:5001/swagger/index.html`

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DB_CONNECTION` | Yes (prod) | SQL Server connection string |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | OpenTelemetry collector (default: `http://otel-gw-logs.tvsmotor.com`) |
| `OTEL_SERVICE_NAME` | No | Telemetry service name (default: `appointment-booking-service`) |
| `SERVICE_VERSION` | No | Version tag (default: `1.0.0`) |
| `DEPLOYMENT_ENVIRONMENT` | No | Environment label (default: `dev`) |

---

## Build & Test

```bash
# Build
dotnet build Appointment.sln -c Release

# Run all tests
dotnet test Appointment.sln

# Docker build
docker build -t appointment-booking-service .
docker run -p 8080:8080 appointment-booking-service
```

---

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/service/appointment-request/create | Create appointment (legacy) |
| POST | /api/service/appointment/create | Create appointment booking (new) |
| POST | /api/service/appointment/fetch/slot | Get available time slots |
| POST | /api/service/appointment/fetch | Search appointments |
| PUT | /api/service/appointment/{id}/update | Update/cancel appointment |
| GET | /api/service/appointment-request/fetch/{frameNo} | Get by frame number |
| GET | /api/service/health/{dealerId} | Dealer health check |
| POST | /api/Vehicle/fetch | Get vehicle details |

---

## Architecture

Clean Architecture with 4 layers:

```
API → Application → Domain ← Infrastructure
```

| Layer | Purpose |
|-------|---------|
| Appointment.API | Controllers, middleware, Swagger |
| Appointment.Application | Services, DTOs, validators |
| Appointment.Domain | Entities, repository interfaces |
| Appointment.Infrastructure | EF Core, SQL Server, repositories |

---

## Documentation

| Document | Content |
|----------|---------|
| [API_SPEC.md](./API_SPEC.md) | Full API specification, inbound/outbound, storage |
| [HLD.md](./HLD.md) | High-level architecture, design decisions, deployment |
| [LLD.md](./LLD.md) | Code structure, database schema, algorithms |

---

*Last updated: July 2026*
