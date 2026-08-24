# job-card-service


## Product Context


# Job Card Service — Product Context

## What This Service Does

The Job Card Service is a backend microservice for **TVS Motor Company's Dealer Management System (DMS)**. It manages the lifecycle of vehicle service job cards at authorized dealerships — from creation and tracking through invoicing and closure.

A "job card" represents a single vehicle service visit at a dealer workshop. It captures what work needs to be done (complaints, labour, spare parts), who is doing it (technicians, service advisors), and the financial outcome (estimates, proforma invoices, final invoices).

## Domain Entities

### Core Aggregates

| Aggregate | Purpose |
|-----------|---------|
| **JobCard** | Central entity — tracks a service visit including complaints, labour, parts, estimates, invoices, insurance, AMC, VAS, before/after trial checks |
| **Customer** | Vehicle owner with addresses and contacts |
| **Dealer** | Authorized service center with branches, city, and digital settings |
| **Vehicle** | Vehicle identified by frame number, linked to models and variants |
| **Labour** | FRT (Flat Rate Time) labour operations — categories, types, pricing, model-variant mappings |
| **Parts** | Spare parts with aggregates, rack/bin locations, UOM, country-specific data |
| **Leads** | Service due reminders/leads generated for vehicles approaching maintenance milestones |
| **Proforma** | Proforma invoices with labour and spare part line items |
| **Master** | Reference data — FRT actions, HSN codes |

### Key Domain Concepts

- **Frame Number**: Unique vehicle chassis identifier used as the primary lookup key
- **FRT (Flat Rate Time)**: Standardized time allocation for labour operations
- **Issue Mode**: How labour/parts are issued (paid, free service, warranty, goodwill, etc.)
- **Service Type**: Free service, paid service, running repair, accident, etc.
- **Convenience Mode**: Service delivery mode (pick-up & drop, doorstep, etc.)
- **Job Type**: Classification of work (determined by vehicle model and odometer reading)
- **Man-Hour Cost**: Labour rate calculation based on dealer, vehicle type, and city tier
- **ATW (Authorized Two-Wheeler)**: Vehicle classification logic for labour pricing

## API Endpoints

### Job Card Operations (`JobcardController`)
- `GET api/maintenance/due/fetch/{frameNo}` — Fetch service due leads for a vehicle
- `GET api/service/history/fetch/{frameNo}` — Get service history (filterable by dealer, branch, jobcard ID, status)
- `GET /api/service/history/detail/fetch/{dealerId}/{branchId}/{jobcardId}` — Detailed service history
- `GET /api/service/invoice/fetch/{dealerId}/{branchId}/{jobcardId}` — Fetch job card invoice
- `GET /api/service/health/{dealerId}` — Dealer health check / validation
- `GET api/jobcard/configurations/fetch/{frameNo}?odometerReading=N` — Get available job types and convenience modes

### Labour Operations (`LabourController`)
- `GET /api/labour/frt/fetch/{dealerId}/{branchId}/{labourTypes}` — Fetch FRT manual labours by type
- `POST /api/labour/frt/create` — Create a new dealer-specific labour entry
- `PUT /api/labour/frt/update` — Update an existing labour entry
- `POST /api/service/labour/{laborCode}/issueMode/{issueModeId}/check` — Validate labour against issue mode

### Parts Operations (`PartsController`)
- `GET /api/service/frt/parts/fetch/{modelId}/{dealerId}/{branchId}` — Fetch FRT parts by vehicle model

### Auto Labor Operations (`AutoLaborController`)
- `POST api/service/frt/autoLabor/create` — Generate auto-labor preview from complaints
- `GET /api/master/labour/fetch` — Fetch master labour reference data (categories, max FRT, SAC code, aggregates, actions)
- `GET /api/master/vehicle/fetch?dealerId=N` — Fetch vehicle variances for a dealer

## Business Rules

1. **Labour Validation**: Labour creation requires valid dealer-branch combination, unique description (for manual type), SAC code match ("998714"), time ≤ 228 minutes, valid action/aggregate enums
2. **Labour Categories**: "BEN" (Benchwork, ItemType 10) and "OUT" (Outwork, ItemType 11)
3. **Tax Categories**: "3" = Service Tax, "2" = No Tax
4. **Issue Mode Validation**: Labour must be validated against issue mode before being applied to a job card
5. **Job Type Determination**: Based on vehicle frame number + odometer reading
6. **Conflict Detection**: If a lead/job card already exists, return 409 Conflict
7. **Rate Limiting**: 25 requests per second per IP (configurable)
8. **Max FRT Settings**: 210 minutes / 3.8 FRT (configurable via `LaborSettings`)

## Integrations

- **SQL Server**: Two databases — `JOBCARD_DB_CONNECTION` (primary) and `REMINDER_DB_CONNECTION` (leads/reminders)
- **Azure Key Vault**: Secrets management for connection strings and OTEL config
- **OpenTelemetry**: Distributed tracing and log export to `otel-gw-logs.tvsmotor.com`
- **Azure DevOps Pipelines**: CI/CD via shared templates from `TVSM-DMS/Devops_ISSM_pipelines`
- **WCF Services**: System.ServiceModel references suggest integration with legacy SOAP services



## Code Structure


# Job Card Service — Project Structure

## Solution Layout

```
job-card-service/
├── Jobcard.sln                          # Solution file
├── Dockerfile                           # Multi-stage Docker build (SDK 9.0 + EF migrations)
├── NuGet.Config                         # Private NuGet feed configuration
├── azure_pipelines/                     # CI/CD pipeline definitions
│   ├── ci-pipeline.yaml                 # Build pipeline (extends shared template)
│   ├── cd-pipeline.yaml                 # Deployment pipeline
│   ├── sonar.yaml                       # SonarQube analysis
│   ├── ast-job-card-uat-pipeline.yaml   # UAT deployment
│   └── ast-job-card-prod-pipeline.yaml  # Production deployment
│
└── src/
    ├── Jobcard.API/                     # Presentation layer (ASP.NET Core Web API)
    ├── Jobcard.Application/             # Application/service layer
    ├── Jobcard.Domain/                  # Domain layer (entities, repositories interfaces)
    ├── Jobcard.Infrastructure/          # Infrastructure layer (EF Core, persistence)
    ├── Jobcard.APITests/                # Controller unit tests
    ├── Jobcard.ApplicationTests/        # Service layer unit tests
    └── Jobcard.InfrastructureTests/     # Infrastructure unit tests
```

## Layer Details

### Jobcard.API (Presentation)

```
Jobcard.API/
├── Controllers/
│   ├── JobcardController.cs         # Job card CRUD and queries
│   ├── LabourController.cs          # FRT labour management
│   ├── PartsController.cs           # FRT parts queries
│   └── AutoLaborController.cs       # Auto-labor generation and master data
├── Models/                          # API-level DTOs (legacy swagger-codegen models)
├── Attributes/
│   └── ValidateModelStateAttribute.cs
├── Filters/
│   ├── BasePathFilter.cs            # Swagger base path
│   └── GeneratePathParamsValidationFilter.cs
├── Security/
│   └── BearerAuthenticationHandler.cs
├── Program.cs                       # App bootstrap, DI, middleware, OpenTelemetry
└── appsettings.json                 # Configuration (connection strings, rate limiter, OTEL)
```

### Jobcard.Application (Business Logic)

```
Jobcard.Application/
├── Extensions/
│   └── ServiceCollectionExtensions.cs   # DI registration for services
├── Jobcard/
│   ├── IJobcardService.cs / JobcardService.cs
│   ├── ILabourService.cs / LabourService.cs
│   ├── IPartsService.cs / PartsService.cs
│   ├── IAutoLaborService.cs / AutoLaborService.cs
│   ├── Dtos/                            # Data transfer objects
│   │   ├── RequestDto/                  # Inbound request DTOs
│   │   └── ResponseDto/                 # Outbound response DTOs
│   └── Validators/
│       ├── CreateLabourValidator.cs     # Business rule validation
│       └── ErrorMessages.cs
```

### Jobcard.Domain (Core Domain)

```
Jobcard.Domain/
├── Entities/
│   ├── CustomerAggregate/       # Customer, CustomerAddress, CustomerContact
│   ├── DealerAggregate/         # Dealer, Branch, City, CityType, DigiDealerSetting
│   ├── JobCardAggregate/        # JobCard*, Complaint*, Employee, IssueMode, Status, etc.
│   ├── LabourAggregate/         # Labour, LabourCategory, FrtId, ServicePrice, etc.
│   ├── PartsAggregate/          # Part, SparePart, RackBIN, Aggregate, VehModelVariance
│   ├── VehicleAggregate/        # Vehicle, VehicleModel, FrtVariance, ManHourCost
│   ├── LeadsAggregate/          # Leads
│   ├── ProformaAggregate/       # ProformaInvoice, ProformaInvoiceLabor/SparePart
│   ├── MasterAggregate/         # FrtAction, Hsn
│   ├── ItemAggregate/           # ItemTaxEnum, ItemTypeEnum
│   ├── Output.cs                # Standard API response wrapper
│   └── ProjectConstants.cs
├── Repositories/                # Repository interfaces (one per aggregate/entity)
├── Exceptions/
│   └── ValidationException.cs
└── Seedwork/                    # DDD building blocks
    ├── Entity.cs                # Base entity with identity
    ├── IAggregateRoot.cs        # Marker interface
    ├── IRepository.cs           # Generic repository interface
    ├── IUnitOfWork.cs           # Transaction abstraction
    ├── ValueObject.cs
    └── Enumeration.cs           # Smart enum base class
```

### Jobcard.Infrastructure (Data Access)

```
Jobcard.Infrastructure/
├── Persistence/
│   ├── JobcardDbContext.cs          # Primary EF Core DbContext (80+ DbSets)
│   ├── ReminderDbContext.cs         # Secondary context for leads/reminders
│   └── UnitOfWork.cs                # IUnitOfWork implementation with transactions
├── EntityConfigurations/            # Fluent API entity configurations (75+ files)
├── Repositories/                    # Repository implementations (30+ files)
├── Extensions/
│   └── ServiceCollectionExtensions.cs  # DI registration for infrastructure
├── Factory/
│   └── DbContextFactory.cs
├── Interfaces/
│   └── IDbCommonContextFactory.cs
└── Migrations/                      # EF Core migrations
```

## Module Dependencies

```
Jobcard.API
  ├── Jobcard.Application
  └── Jobcard.Infrastructure

Jobcard.Application
  └── Jobcard.Domain

Jobcard.Infrastructure
  └── Jobcard.Application
      └── Jobcard.Domain
```

Note: Infrastructure references Application (not just Domain) — this is a pragmatic deviation from strict Clean Architecture to allow Infrastructure to resolve Application-layer interfaces directly.

## Architectural Decisions

1. **Clean Architecture (adapted)**: Four-layer structure with dependency inversion. Domain has zero external dependencies.
2. **DDD Aggregates**: Entities grouped by aggregate (CustomerAggregate, JobCardAggregate, etc.) with IAggregateRoot marker.
3. **Repository Pattern**: One interface per repository in Domain, implementation in Infrastructure. Not strictly one-per-aggregate — finer-grained repositories exist.
4. **Unit of Work**: Manual transaction management via `IUnitOfWork` (BeginTransaction/Commit/Rollback/Save).
5. **Service Layer**: Application services orchestrate domain logic. Dependencies injected via custom "Dependencies" objects (e.g., `LabourServiceDependencies`, `AutoLaborServiceDependencies`).
6. **Two Database Contexts**: `JobCardDbContext` (primary, 80+ entities) and `ReminderDbContext` (leads/reminders).
7. **No MediatR/CQRS**: Direct service calls from controllers. No command/query separation.
8. **Swagger-Codegen Origin**: API models in `Jobcard.API/Models/` were originally generated from an OpenAPI spec.



## Tech Stack & Dependencies


# Job Card Service — Technical Reference

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | .NET 9.0 (ASP.NET Core) |
| Language | C# (latest LangVersion) |
| ORM | Entity Framework Core 9.0.2 (SQL Server provider) |
| Database | Microsoft SQL Server (two databases) |
| Observability | OpenTelemetry (traces + logs via OTLP/HTTP Protobuf) |
| API Docs | Swashbuckle / Swagger UI 6.4.0 |
| HTTP Client | RestSharp 112.1.0 |
| Secrets | Azure Key Vault (via environment variables in AKS) |
| Serialization | Newtonsoft.Json 13.0.3 |
| WCF Client | System.ServiceModel 6.0.x (legacy SOAP integration) |
| Container | Docker (multi-stage, .NET 9.0 SDK + ASP.NET runtime) |
| Orchestration | Azure Kubernetes Service (AKS) |
| CI/CD | Azure DevOps Pipelines (shared templates from TVSM-DMS/Devops_ISSM_pipelines) |
| Code Quality | SonarQube |

## Coding Conventions

### Naming
- **Namespaces**: `Jobcard.{Layer}.{Feature}` (e.g., `Jobcard.Application.Jobcard`, `Jobcard.Infrastructure.Repositories`)
- **Controllers**: PascalCase, suffixed with `Controller`
- **Services**: Interface `I{Name}Service` + implementation `{Name}Service`
- **Repositories**: Interface `I{Name}Repository` + implementation `{Name}Repository`
- **DTOs**: Suffixed with `Dto`, `RequestDto`, or `ResponseDto`
- **Entity Configurations**: Suffixed with `EntityTypeConfiguration`
- **Properties**: PascalCase for public properties in domain/application DTOs; some legacy models use camelCase (`statusCode`, `message`)

### File Organization
- One class per file (with exceptions for small related types)
- File-scoped namespaces (`namespace X;` syntax)
- Primary constructors used in controllers and DbContext

### Dependency Injection
- All services registered as `Scoped`
- Application services use custom dependency aggregate objects (`LabourServiceDependencies`, `AutoLaborServiceDependencies`) instead of individual constructor parameters
- Infrastructure registers repositories and DbContexts
- Registration split across `AddApplication()` and `AddInfrastructure(configuration)` extension methods

### Controller Patterns
- Primary constructors for DI: `public class XController(IXService service) : ControllerBase`
- Return `IActionResult` or `ActionResult<T>`
- Route attributes on methods (not class-level for most)
- Standard response wrapper: `Output { StatusCode, Message }`

## Error Handling

### Controller Level
- Try/catch blocks in every action method
- Exceptions mapped to HTTP status codes:
  - General exceptions → `400 Bad Request` with `Output` wrapper
  - Message contains "Exists" → `409 Conflict`
  - `KeyNotFoundException` → `404 Not Found`
  - `ApplicationException` → `400 Bad Request`
  - Unhandled → `500 Internal Server Error`
- No global exception filter or middleware (each controller handles its own errors)

### Validation
- Manual validation in controllers (null checks, parameter parsing)
- Business rule validation via dedicated validator classes (e.g., `CreateLabourValidator`)
- Validators throw `ArgumentException` or `InvalidOperationException` with descriptive messages
- `[ValidateModelState]` attribute available but not widely used

### Domain Exceptions
- `ValidationException` in Domain layer (custom exception class)

## Patterns

### Repository Pattern
- Interfaces in `Jobcard.Domain/Repositories/`
- Implementations in `Jobcard.Infrastructure/Repositories/`
- Repositories receive `JobCardDbContext` or `ReminderDbContext` via constructor injection
- Direct LINQ queries against DbContext DbSets
- No generic base repository — each repository is purpose-built

### Unit of Work
- `IUnitOfWork` with `BeginTransaction()`, `Commit()`, `Rollback()`, `Save()`
- Used for multi-step write operations requiring atomicity
- Wraps EF Core's `IDbContextTransaction`

### Smart Enums
- `Enumeration` base class in Seedwork
- Domain enums like `LabourTypeEnum`, `ActionEnum`, `AggregateEnum` use `FromId()` pattern
- Provides validation that ID matches expected description

### Entity Configuration
- Fluent API via `IEntityTypeConfiguration<T>` implementations
- All configurations applied explicitly in `OnModelCreating` (no assembly scanning)
- DateTime sanitization helper on DbContext to prevent SQL Server range errors

## Testing

### Framework
- **xUnit** for test execution
- **MSTest** attributes also available (dual framework setup)
- **Moq** for mocking
- **Coverlet** for code coverage (with `coverlet.runsettings`)

### Test Structure
- `Jobcard.APITests/Controllers/` — Controller unit tests (mock services, verify HTTP responses)
- `Jobcard.ApplicationTests/Jobcard/` — Service layer tests
- `Jobcard.InfrastructureTests/Extensions/` — Infrastructure tests

### Test Conventions
- One test class per controller/service
- `[Fact]` attribute for test methods
- Arrange-Act-Assert pattern
- Mock all dependencies via `Mock<IService>()`
- Assert on both status code and response body type/content

### Running Tests
```bash
dotnet test src/Jobcard.APITests/
dotnet test src/Jobcard.ApplicationTests/
dotnet test src/Jobcard.InfrastructureTests/
```

## Build & Deployment

### Local Development
```bash
dotnet restore
dotnet build
dotnet run --project src/Jobcard.API/
```

### Docker Build
```bash
docker build -t job-card-service .
```
- Multi-stage: build → publish → migrations → runtime
- Exposes port 8080
- Timezone set to `Asia/Kolkata`
- EF migrations generated at build time (not applied at runtime)

### CI/CD Pipeline
- **Trigger**: SonarQube pipeline completion on `main` branch triggers CI
- **CI**: Extends `build-template.yml` from shared DevOps repo (`TVSM-DMS/Devops_ISSM_pipelines`)
- **CD**: Separate pipeline for deployment
- **Environments**: dev → UAT → Production (separate pipeline files for UAT and prod)
- **Image Scanning**: Dedicated AST image scan pipeline

### Configuration
- Connection strings via environment variables (`JOBCARD_DB_CONNECTION`, `REMINDER_DB_CONNECTION`)
- OpenTelemetry settings via environment variables (populated from Azure Key Vault in AKS)
- Rate limiter settings in `appsettings.json` (25 req/s per IP, 1-second window)
- `LaborSettings` in `appsettings.json` for business rule thresholds

### Observability
- OpenTelemetry traces: ASP.NET Core + HttpClient + SqlClient instrumentation
- OpenTelemetry logs: Structured logging with scopes and formatted messages
- Export via OTLP HTTP/Protobuf to `otel-gw-logs.tvsmotor.com`
- Batch export with configurable queue size, batch size, and timeouts
- Startup connectivity diagnostics (DNS, TCP, HTTP POST) logged for troubleshooting
- Can be disabled via `OTEL_EXPORTER_ENABLED=false`

