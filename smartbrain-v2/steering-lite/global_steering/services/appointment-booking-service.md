# appointment-booking-service


## Product Context


# Appointment Booking Service — Product Context

## What This Service Does

An omnichannel appointment booking service for TVS Motor Company that enables customers to schedule and manage vehicle service appointments through multiple channels (TVS Connect app, Website, WhatsApp). It serves dealerships and service centers by streamlining the booking process for two-wheeler vehicle servicing.

## Domain Entities

### Aggregates

**AppointmentAggregate** (core)
- `AppointmentBooking` — legacy appointment record (flat table with denormalized customer/vehicle data)
- `ServAppointment` — primary appointment entity (normalized, references Dealer/Customer/Vehicle by FK)
- `AppointmentServFollowUpDet` — follow-up tracking on appointment updates/reschedules
- `ServiceAppointmentRequest` / `ServiceAppointmentSubRequest` — customer service requests attached to an appointment
- `ServiceAppointmentCategory` — appointment category lookup
- `JobCardId` — running ID generator per dealer/branch/table

**VehicleAggregate**
- `Vehicle` — identified by VehicleId, FrameNo, RegistrationNo; linked to Model and Part
- `VehicleModel` — model metadata (ModelId, Description)
- `VehicleModelPart` — part/variant metadata (PartId, Description, Series)
- `VehicleEndUser` — maps vehicles to customer end-users
- `DealerVehicleMapping` — dealer-to-vehicle association

**CustomerAggregate**
- `Customer` — CustomerId, CustomerName
- `CustomerContact` — contact numbers with type and preferred flag
- `CustomerAddress` — address details
- `CustomerEndUser` — end-user identity for a customer
- `DealerCustomerMapping` — dealer-to-customer association

**DealerAggregate**
- `Dealer` — DealerId, DealershipName, CountryCode
- `Branch` — BranchId, BranchName under a Dealer
- `DealerEmployee` / `EmpSubGroup` — service advisor tracking

### Value Objects (Smart Enumerations)

| Enumeration | Values |
|---|---|
| `Status` | Open (0), Closed (1), Automaticclosure (2), Cancelled (3), Pending (4) |
| `Channel` | TVSCONNECT, WEBSITE, WHATSAPP |
| `ServiceMode` | Normal, Break-down, Care camp-Field, Express Service, Pickup and Drop, Road Side Assistance, Quick Repair, Rapido, etc. (17 total) |
| `ServiceType` | 1st–10th Free Service, Paid Services, Bonus, Warranty, Rework, Major/Running/Accident Repair, PDI, PSF, WaterWash (32 total) |
| `ConvenienceMode` | Workshop, Pick up & Drop, Doorstep service, Road side assistance, Care camp-Field/Workshop, Pickup Only, Drop Only (8 total) |

## External Integrations

- **SQL Server Database** — primary data store, connection via `DB_CONNECTION` environment variable
- **OpenTelemetry Collector** — traces and logs exported via OTLP HTTP to `otel-gw-logs.tvsmotor.com`
- **Azure DevOps Pipelines** — CI/CD automation
- **Kubernetes** — runtime deployment target (connection strings injected via values.yaml)
- **Swagger Hub** — API documentation at `tvsswgrhub.tvsmotor.com`

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/api/service/appointment-request/create` | Create appointment (legacy flow using AppointmentBooking) |
| POST | `/api/service/appointment/create` | Create appointment booking (current flow using ServAppointment) |
| GET | `/api/service/appointment-request/fetch/{frameNo}` | Get appointments by frame number |
| POST | `/api/service/appointment/fetch/slot` | Get available time slots for a dealer/branch |
| POST | `/api/service/appointment/fetch` | Search appointments (multi-criteria) |
| PUT | `/api/service/appointment/{appointmentId}/update` | Update or cancel an appointment |
| GET | `/api/service/health/{dealerId}` | Health check / dealer validation |
| POST | `/api/Vehicle/fetch` | Get vehicle details by mobile/frame/registration |

## Business Rules

### Appointment Creation
- Appointment date must be >= current UTC date
- Only one open/pending appointment allowed per vehicle per dealer/branch
- Vehicle must exist in the system with matching ModelId and PartId
- Branch must exist under the specified dealer
- Customer must exist with a valid contact (ContactType = 6)
- Communication channel must be one of: TVSCONNECT, WEBSITE, WHATSAPP
- Communication mode must be one of: Email, Phone, SMS, Letter, Online
- Kilometer must be > 0
- ServiceMode and ConvenienceMode are required and must be valid enum values

### Appointment Updates
- Only "Open" or "Cancelled" status transitions are allowed
- Cannot update an already closed or cancelled appointment
- Every update creates a follow-up detail record with:
  - LeakageId = 3 for "Open" (reschedule)
  - LeakageId = 4 for "Cancelled"
  - ReasonId = 4 set on the appointment when cancelled, STATUS set to 1
- Follow-up number increments from the last follow-up on that appointment

### Slot Generation
- Operating hours: 10:00 AM – 6:00 PM
- Lunch break: 1:00 PM – 2:00 PM (slots skipped)
- Slot duration: 30 minutes
- Capacity per slot = ServiceAdvisorCount × CapacityPerSlot (default 4)
- Only slots with available capacity are returned

### Search
- Search by FrameNo, RegistrationNo, MobileNumber, DealerId/BranchId, date range
- Status filter defaults to "Open" if not provided
- Limit is required and must be > 0
- Date pairs must be complete (both fromDate and toDate or neither)
- BranchId requires DealerId; DealerId requires date range



## Code Structure


# Appointment Booking Service — Project Structure

## Directory Layout

```
appointment-booking-service/
├── Appointment.sln                          # Solution file (7 projects)
├── Dockerfile                               # Multi-stage Docker build (SDK 9.0 → aspnet:9.0)
├── NuGet.Config                             # Private NuGet feed configuration
├── azure_pipelines/                         # CI/CD pipeline definitions
│   ├── ci-pipeline.yaml                     # Build pipeline (triggered by Sonar completion)
│   ├── cd-pipeline.yaml                     # Deploy pipeline (dev → uat → prod with approvals)
│   ├── sonar.yaml                           # SonarQube analysis
│   ├── ast-appointment-bs-prod-pipeline.yaml
│   ├── ast-appointment-bs-uat-pipeline.yaml
│   └── ast-image-scan-appointment-booking-service-pipeline.yaml
│
└── src/
    ├── Appointment.API/                     # Presentation layer (ASP.NET Core Web API)
    │   ├── Controllers/
    │   │   ├── AppointmentController.cs     # All appointment CRUD + search + slots
    │   │   └── VehicleController.cs         # Vehicle details lookup
    │   ├── Filters/
    │   │   ├── BasePathFilter.cs            # Swagger base path configuration
    │   │   └── GeneratePathParamsValidationFilter.cs
    │   ├── Security/
    │   │   └── BearerAuthenticationHandler.cs  # Auth stub (TODO: implement token validation)
    │   ├── Attributes/
    │   │   └── ValidateModelStateAttribute.cs
    │   ├── Program.cs                       # App bootstrap, DI, OpenTelemetry, Swagger
    │   ├── appsettings.json                 # SlotSettings, logging config
    │   └── .env                             # Local environment variables
    │
    ├── Appointment.Application/             # Application/service layer
    │   ├── Appointment/
    │   │   ├── IAppointmentService.cs       # Service interface
    │   │   ├── AppointmentService.cs        # Core business logic orchestration
    │   │   ├── AppointmentServiceDependencies.cs  # Parameter object for DI
    │   │   ├── Dtos/                        # Request/response DTOs
    │   │   │   ├── AppointmentRequestDto.cs
    │   │   │   ├── AppointmentDto.cs
    │   │   │   ├── AppointmentSearchRequestDto.cs
    │   │   │   ├── UpdateAppointmentRequestDto.cs
    │   │   │   ├── UpdateAppointmentDto.cs
    │   │   │   └── ServiceAppointmentBookingDtos/
    │   │   │       ├── AppointmentBookingRequestDto.cs
    │   │   │       └── AppointmentBookingDto.cs
    │   │   └── Validators/
    │   │       ├── AppointmentValidator.cs  # All validation logic (static + instance methods)
    │   │       └── ErrorMessages.cs         # Centralized error message constants
    │   ├── VehicleServices/
    │   │   ├── IVehicleService.cs
    │   │   ├── VehicleService.cs
    │   │   ├── Dtos/
    │   │   └── Validators/
    │   │       └── VehicleValidators.cs     # Input validation with compiled regex
    │   └── Extensions/
    │       └── ServiceCollectionExtension.cs # AddApplication() DI registration
    │
    ├── Appointment.Domain/                  # Domain layer (no external dependencies)
    │   ├── Entities/
    │   │   ├── AppointmentAggregate/        # ServAppointment, AppointmentBooking, Status, Channel, etc.
    │   │   ├── CustomerAggregate/           # Customer, CustomerContact, CustomerAddress
    │   │   ├── DealerAggregate/             # Dealer, Branch
    │   │   ├── VehicleAggregate/            # Vehicle, VehicleModel, VehicleModelPart
    │   │   ├── Output.cs                    # API response envelope
    │   │   └── Success.cs                   # Success response model
    │   ├── Repositories/                    # Repository interfaces
    │   │   ├── IAppointmentRepository.cs
    │   │   ├── IDealerRepository.cs
    │   │   ├── IVehicleRepository.cs
    │   │   ├── ICustomerRepository.cs
    │   │   ├── ICustomerContactRepository.cs
    │   │   ├── ICustomerRequestRepository.cs
    │   │   └── ...
    │   ├── SeedWork/                        # Base classes and interfaces
    │   │   ├── Enumeration.cs              # Smart enum base class
    │   │   ├── IAggregateRoot.cs
    │   │   ├── IUnitOfWork.cs
    │   │   └── ValueObject.cs
    │   └── Exceptions/
    │       └── ValidationException.cs       # Custom domain validation exception
    │
    ├── Appointment.Infrastructure/          # Data access and persistence
    │   ├── Persistence/
    │   │   ├── AppointmentDbContext.cs      # EF Core DbContext (30+ DbSets)
    │   │   └── UnitOfWork.cs               # Transaction management
    │   ├── Repositories/                    # Repository implementations
    │   │   ├── AppointmentRepository.cs     # Complex queries with EF Core
    │   │   ├── VehicleRepository.cs
    │   │   ├── DealerRepository.cs
    │   │   └── ...
    │   ├── EntityConfigurations/            # EF Core Fluent API configurations
    │   │   ├── ServAppointmentEntityTypeConfiguration.cs
    │   │   ├── DealerEntityTypeConfiguration.cs
    │   │   └── ... (25+ configuration classes)
    │   ├── Migrations/                      # EF Core database migrations
    │   └── Extensions/
    │       └── ServiceCollectionExtensions.cs  # AddInfrastructure() DI registration
    │
    ├── Appointment.API.Tests/               # Controller-level unit tests
    │   └── Controllers/
    │       └── AppointmentControllerTests.cs
    │
    ├── Appointment.Application.Tests/       # Service-level unit tests
    │   └── Appointment/
    │       └── AppointmentServiceTests.cs
    │
    └── Appointment.Infrastructure.Tests/    # Repository/data access tests
```

## Module Dependencies

```
Appointment.API
  ├── Appointment.Application
  │   └── Appointment.Domain (no external deps)
  └── Appointment.Infrastructure
      └── Appointment.Application
          └── Appointment.Domain
```

- **Domain** has zero NuGet dependencies — pure C# with no framework references
- **Application** depends on Domain + FluentValidation + Microsoft.Extensions.Logging.Abstractions
- **Infrastructure** depends on Application + EF Core + SQL Server provider
- **API** depends on Application + Infrastructure + Swagger + OpenTelemetry + DotNetEnv

## Architectural Decisions

### Clean Architecture with DDD Influence
The project follows a layered architecture inspired by Clean Architecture. Domain is the innermost layer with no outward dependencies. Repository interfaces live in Domain; implementations in Infrastructure. This allows the Application layer to depend only on abstractions.

### Two Appointment Models (Legacy + Current)
- `AppointmentBooking` — original flat table with denormalized data (frame_no, customer_name, etc. stored directly)
- `ServAppointment` — normalized model referencing Dealer, Customer, Vehicle by foreign keys
- The "create" endpoint (`/api/service/appointment-request/create`) uses the legacy model
- The "booking" endpoint (`/api/service/appointment/create`) uses the current model
- Both coexist; new features should target `ServAppointment`

### Smart Enumerations over Database Lookups
Domain value types (Status, Channel, ServiceMode, ServiceType, ConvenienceMode) use the `Enumeration` base class pattern instead of database lookup tables. Values are defined as static fields and resolved via reflection.

### Dependency Aggregation Pattern
`AppointmentServiceDependencies` bundles all 12+ repository/service dependencies into a single parameter object, avoiding constructor parameter explosion. The DI container builds this object explicitly in `ServiceCollectionExtension.AddApplication()`.

### Unit of Work with Explicit Transactions
The `UnitOfWork` wraps EF Core's `DbContextTransaction`. Services call `BeginTransaction()`, perform multiple repository operations, then `Commit()` or `Rollback()`. `Save()` calls `SaveChanges()` without committing the transaction.

### Running ID Generation
Instead of database-generated identity columns for appointments, the system uses a `JobCardId` table that tracks running IDs per dealer/branch/table. IDs are fetched, incremented, and updated within the same transaction.

### No Global Exception Middleware
Error handling is done per-action in controllers via try/catch. Exceptions containing "Exists" in the message return 409 Conflict; all others return 400 Bad Request. `ValidationException` and `KeyNotFoundException` are caught specifically in the update endpoint.



## Tech Stack & Dependencies


# Appointment Booking Service — Tech Stack & Conventions

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | .NET | 9.0 |
| Web Framework | ASP.NET Core | 9.0 |
| ORM | Entity Framework Core | 9.0.1 |
| Database | SQL Server | (via EF Core SqlServer provider) |
| Validation | FluentValidation.AspNetCore | 11.3.0 |
| API Docs | Swashbuckle (Swagger) | 6.4.0 |
| Observability | OpenTelemetry (traces + logs) | 1.15.0 |
| JSON | Newtonsoft.Json | (via Swashbuckle.AspNetCore.Newtonsoft) |
| Env Loading | DotNetEnv | 3.1.1 |
| Testing | xUnit 2.6.6 + Moq 4.20.72 + coverlet | |
| Container | Docker (aspnet:9.0 runtime) | |
| CI/CD | Azure DevOps Pipelines | |
| Orchestration | Kubernetes | |

## Coding Conventions

### Language Features
- C# 12 with `<LangVersion>latest</LangVersion>`
- Primary constructors for controllers and simple services: `public class VehicleController(IVehicleService vehicleService) : ControllerBase`
- `required` keyword on properties that must be initialized
- Nullable reference types enabled (`<Nullable>enable</Nullable>`)
- Implicit usings enabled
- Source-generated regex via `[GeneratedRegex]` attribute

### Naming
- Domain entities use UPPER_SNAKE_CASE for database-mapped properties (e.g., `DEALER_ID`, `BRANCH_ID`, `APPOINTMENT_ID`)
- DTOs use camelCase for JSON serialization (e.g., `dealerId`, `branchId`)
- Interfaces prefixed with `I` (e.g., `IAppointmentService`, `IAppointmentRepository`)
- Repository implementations are `internal` classes
- Extension methods in static classes named `ServiceCollectionExtensions`

### Project Organization
- One service interface + one implementation per bounded context feature
- DTOs grouped in `Dtos/` folders within the feature directory
- Validators in `Validators/` folders alongside their feature
- Entity configurations in `EntityConfigurations/` folder (one file per entity)
- Error messages centralized in `ErrorMessages.cs` as `const string` fields

### Dependency Injection
- Registered via extension methods: `AddApplication()` and `AddInfrastructure()`
- All services and repositories registered as `Scoped`
- `AppointmentServiceDependencies` parameter object built explicitly in the DI registration

## Patterns

### Repository Pattern
- Interfaces defined in `Domain/Repositories/`
- Implementations in `Infrastructure/Repositories/` (marked `internal`)
- Repositories receive `AppointmentDbContext` via constructor injection
- Complex queries use EF Core LINQ with `.Include()` / `.ThenInclude()` for eager loading
- `AsNoTracking()` used for read-only queries

### Unit of Work
```csharp
_unitOfWork.BeginTransaction();
try {
    // multiple repository operations
    _unitOfWork.Save();       // calls SaveChanges()
    _unitOfWork.Commit();     // commits transaction
} catch {
    _unitOfWork.Rollback();
    throw;
}
```

### Smart Enumeration (Value Objects)
Domain enums inherit from `Enumeration` base class:
- Static fields define all values
- `GetAll<T>()` returns all values via reflection
- `FromValue<T>(int)` and `FromDisplayName<T>(string)` for lookup
- `FromId(int)` on specific types for convenience
- Throws `KeyNotFoundException` or `InvalidOperationException` on invalid values

### Validation
- `AppointmentValidator` class with mix of static and instance methods
- Instance methods call repository for data-dependent validation (e.g., vehicle exists, branch exists)
- Static methods for pure input validation (date ranges, required fields)
- Throws custom `ValidationException` (in `Domain/Exceptions/`) on failure
- `VehicleValidators` uses compiled regex for input format validation
- No FluentValidation rule builders used despite the package being referenced

### Controller Pattern
- Controllers use primary constructors with service injection
- Request bodies accepted as `object` then deserialized via `JsonConvert.DeserializeObject<T>()`
- Responses use `Output` envelope: `{ statusCode, message }`
- Success responses use `Ok()`, `Created()`, or `NotFound()` with typed objects

## Error Handling

### Strategy
- No global exception handling middleware
- Each controller action wraps logic in try/catch
- Exception message content determines HTTP status:
  - Contains "Exists" → 409 Conflict
  - `ValidationException` → 400 Bad Request
  - `KeyNotFoundException` → 404 Not Found
  - `InvalidOperationException` → 400 Bad Request (wraps inner exceptions)
  - All other exceptions → 400 Bad Request

### Custom Exceptions
- `ValidationException` (Domain layer) — thrown for business rule violations
- `InvalidOperationException` — thrown when internal processing fails (wraps original exception)
- `KeyNotFoundException` — thrown when entity not found (e.g., appointment by ID)

### Error Response Format
```json
{
  "statusCode": 400,
  "message": "Error description here"
}
```

## Testing

### Structure
- **Appointment.API.Tests** — controller tests mocking `IAppointmentService`
- **Appointment.Application.Tests** — service tests mocking all repositories
- **Appointment.Infrastructure.Tests** — data access tests

### Frameworks & Tools
- xUnit as test framework (`[Fact]` attributes)
- Moq with `MockBehavior.Strict` for repository mocks
- MSTest also referenced (dual framework support)
- coverlet for code coverage (`coverlet.collector` + `coverlet.msbuild`)
- Microsoft.NET.Test.Sdk 17.12.0

### Conventions
- Test classes named `{Class}Tests` (e.g., `AppointmentServiceTests`, `AppointmentControllerTests`)
- Test methods named `{Method}_{Scenario}_{ExpectedResult}` (e.g., `GetAppointmentByFrameNo_ShouldReturnNull_WhenNoAppointments`)
- Private helper methods for creating test service instances (`CreateService()`)
- Reflection used to test private methods (`BindingFlags.NonPublic | BindingFlags.Instance`)
- Config mocked for slot settings (StartTime, EndTime, LunchStart, LunchEnd, SlotDuration, CapacityPerSlot)

### Running Tests
```bash
dotnet test src/Appointment.API.Tests/
dotnet test src/Appointment.Application.Tests/
dotnet test src/Appointment.Infrastructure.Tests/
```

## Deployment

### Docker
- Multi-stage build: `sdk:9.0` (build/publish) → `aspnet:9.0` (runtime)
- Exposed port: 8080
- Timezone: Asia/Kolkata
- Entry point: `dotnet Appointment.API.dll`
- Migrations stage included in Dockerfile (uses `dotnet-ef` tool)

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `DB_CONNECTION` | SQL Server connection string |
| `OTEL_SERVICE_NAME` | OpenTelemetry service name (default: appointment-booking-service) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint |
| `SERVICE_VERSION` | Deployed version |
| `DEPLOYMENT_ENVIRONMENT` | Environment name (dev/uat/prod) |

### CI/CD (Azure DevOps)
- **CI**: Triggered by Sonar pipeline completion on `main` branch; uses shared `build-template.yml`
- **CD**: Deploys to dev (auto) → uat (manual approval) → prod (manual approval)
- Image scanning pipeline runs between CI and CD
- Shared templates from `TVSM-DMS/Devops_ISSM_pipelines` repo

### Kubernetes
- Helm chart named `appointment-booking`
- Connection string injected via `values.yaml` → environment variable
- Service name for deployment: `appointment-booking-service`

## Build Commands

```bash
# Restore and build
dotnet restore
dotnet build Appointment.sln

# Run locally
dotnet run --project src/Appointment.API/

# Run tests with coverage
dotnet test --collect:"XPlat Code Coverage"

# Docker build
docker build -t appointment-booking-service .
```

