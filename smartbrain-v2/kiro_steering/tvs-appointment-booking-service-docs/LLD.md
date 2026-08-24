# Low Level Design (LLD) – Appointment Booking Service

## Service Identity

| Field | Value |
|-------|-------|
| Service Name | appointment-booking-service |
| Runtime | .NET 9 / ASP.NET Core |
| ORM | Entity Framework Core 9 |
| Database | SQL Server (OnlineDMS) |
| Architecture | Clean Architecture + DDD |

---

## 1. Code Structure

```
src/
├── Appointment.API/                    → Web API layer
│   ├── Controllers/
│   │   ├── AppointmentController.cs    → 7 appointment endpoints
│   │   └── VehicleController.cs        → 1 vehicle endpoint
│   ├── Attributes/
│   │   └── ValidateModelStateAttribute.cs → DataAnnotation validation filter
│   ├── Filters/
│   │   ├── BasePathFilter.cs           → Swagger base path configuration
│   │   └── GeneratePathParamsValidationFilter.cs
│   ├── Security/
│   │   └── BearerAuthenticationHandler.cs → Auth placeholder
│   ├── Program.cs                      → App bootstrap, DI, middleware
│   └── appsettings.json                → Configuration
│
├── Appointment.Application/            → Business logic layer
│   ├── Appointment/
│   │   ├── AppointmentService.cs       → Core service (450+ lines)
│   │   ├── IAppointmentService.cs      → Service interface
│   │   ├── AppointmentServiceDependencies.cs → DI container class
│   │   ├── Validators/
│   │   │   └── AppointmentValidator.cs → Validation rules
│   │   └── Dtos/
│   │       ├── AppointmentRequestDto.cs
│   │       ├── AppointmentResponseDto.cs
│   │       ├── AppointmentSearchRequestDto.cs
│   │       ├── AppointmentSearchResponseDto.cs
│   │       ├── UpdateAppointmentRequestDto.cs
│   │       ├── DealerDto.cs, CustomerDto.cs, VehicleDto.cs
│   │       └── ServiceAppointmentBookingDtos/
│   │           ├── AppointmentBookingRequestDto.cs
│   │           ├── AppointmentBookingResponseDto.cs
│   │           ├── AppointmentBookingDto.cs
│   │           ├── AppointmentSlotRequestDto.cs
│   │           └── CustomerRequestSubTypeDto.cs
│   ├── VehicleServices/
│   │   ├── VehicleService.cs
│   │   ├── IVehicleService.cs
│   │   ├── Validators/VehicleValidators.cs
│   │   └── Dtos/GetVehicleDetailsRequestDto.cs
│   └── Extensions/
│       └── ServiceCollectionExtensions.cs → AddApplication() DI
│
├── Appointment.Domain/                 → Pure domain layer (no deps)
│   ├── Entities/
│   │   ├── AppointmentAggregate/
│   │   │   ├── ServAppointment.cs      → Primary appointment entity
│   │   │   ├── AppointmentBooking.cs   → Legacy appointment entity
│   │   │   └── AppointmentSearchReadModel.cs
│   │   ├── CustomerAggregate/
│   │   │   ├── Customer.cs, CustomerContact.cs, CustomerAddress.cs
│   │   │   ├── CustomerRequest.cs, RequestSubType.cs
│   │   │   └── CustomerEndUser.cs
│   │   ├── DealerAggregate/
│   │   │   ├── Dealer.cs, Branch.cs, DealerEmployee.cs
│   │   │   └── DealerVehicleMapping.cs, DealerCustomerMapping.cs
│   │   ├── VehicleAggregate/
│   │   │   ├── Vehicle.cs, VehicleModel.cs, VehicleModelPart.cs
│   │   │   └── CustomerVehicle.cs
│   │   ├── Output.cs, Success.cs
│   │   └── JobCardId.cs
│   ├── Repositories/                   → Interface contracts
│   │   ├── IAppointmentRepository.cs
│   │   ├── IDealerRepository.cs
│   │   ├── IVehicleRepository.cs
│   │   ├── ICustomerRepository.cs
│   │   ├── ICustomerRequestRepository.cs
│   │   ├── ICustomerSubRequestRepository.cs
│   │   ├── ICustomerContactRepository.cs
│   │   ├── IEmployeeRepository.cs
│   │   ├── IServAppointmentFollowUpDetRepository.cs
│   │   ├── IDealerVehicleMappingRepository.cs
│   │   └── IDealerCustomerMappingRepository.cs
│   ├── SeedWork/
│   │   ├── IAggregateRoot.cs
│   │   ├── IRepository.cs
│   │   └── IUnitOfWork.cs
│   └── Exceptions/
│       └── ValidationException.cs
│
├── Appointment.Infrastructure/         → Data access layer
│   ├── Persistence/
│   │   ├── AppointmentDbContext.cs     → 28+ DbSets, OnModelCreating
│   │   └── UnitOfWork.cs              → Transaction management
│   ├── Repositories/
│   │   ├── AppointmentRepository.cs   → Main repository (300+ lines)
│   │   ├── DealerRepository.cs
│   │   ├── VehicleRepository.cs
│   │   ├── CustomerRepository.cs
│   │   ├── CustomerRequestRepository.cs
│   │   ├── RequestSubTypeRepository.cs
│   │   ├── CustomerContactRepository.cs
│   │   ├── EmployeeRepository.cs
│   │   ├── ServAppointmentFollowupDetRepository.cs
│   │   ├── DealerVehicleMappingRepository.cs
│   │   └── DealerCustomerMappingRepository.cs
│   ├── EntityConfigurations/           → 28+ Fluent API configurations
│   ├── Migrations/                     → EF Core migrations
│   └── Extensions/
│       └── ServiceCollectionExtensions.cs → AddInfrastructure() DI
│
├── Appointment.API.Tests/              → Controller unit tests
├── Appointment.Application.Tests/      → Service unit tests
└── Appointment.Infrastructure.Tests/   → Repository unit tests
```

---

## 2. Database Schema

### ServAppointments (Primary — New Flow)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| APPOINTMENT_ID | bigint | No | PK (from JobCardIds) |
| DEALER_ID | int | No | FK → Dealers |
| BRANCH_ID | int | No | FK → Branches |
| CUSTOMER_ID | bigint | No | FK → Customers |
| VEHICLE_ID | bigint | No | FK → Vehicles |
| END_USER_ID | bigint | No | Resolved end user |
| JOB_TYPE_ID | tinyint | No | Service type (1=Free, 2=Paid, 3=Running Repair) |
| APT_CAT_ID | smallint | No | Appointment category |
| SERV_MODE_ID | tinyint | No | Service mode (1=Walk-in, 2=Pick-up) |
| CONV_MODE_ID | int | Yes | Convenience mode |
| STATUS | tinyint | No | 0=Open, 1=Closed/Cancelled |
| REASON_ID | int | Yes | 0=Normal close, 4=Cancelled |
| APPOINT_DATE | datetime | Yes | Scheduled date/time |
| APPOINTMENT_NO | bigint | No | Display number |
| REGIS_NO | varchar | Yes | Vehicle registration |
| CONTACT_NO | varchar | Yes | Customer contact |
| KILOMETERS | decimal | Yes | Odometer reading |
| CHANNEL | varchar | Yes | Communication channel |
| ACTIVE | bit | No | Soft delete flag |
| CUR_FOLLOWUP_NO | tinyint | No | Current follow-up count |
| MOBILE_APP_REF_ID | bigint | Yes | External reference |
| Remarks | varchar | Yes | Customer remarks |
| CREATED_ON | datetime | Yes | Record created |
| MODIFIED_ON | datetime | Yes | Last modified |

### AppointmentBooking (Legacy Flow)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| APPOINTMENT_ID | bigint | No | PK (auto-increment) |
| DEALER_ID | int | No | Dealer reference |
| BRANCH_ID | int | No | Branch reference |
| FRAME_NO | varchar | Yes | Vehicle frame number |
| REG_NO | varchar | Yes | Registration number |
| MODEL_ID | varchar | Yes | Vehicle model |
| PART_ID | varchar | Yes | Vehicle part |
| SERVICE_MODE | tinyint | No | Service mode |
| ConvenienceMode | tinyint | No | Convenience mode |
| JOB_TYPE | tinyint | No | Job type |
| APPOINMENT_DATE | datetime | No | Appointment date |
| CUSTOMER_ID | bigint | No | Customer reference |
| CUSTOMER_NAME | varchar | Yes | Denormalized name |
| CONTACT_NUMBER | varchar | Yes | Denormalized contact |
| Status | varchar | No | Open/Pending/Closed |
| CHANNEL | varchar | Yes | Source channel |
| REF_NO | varchar | Yes | Reference number |
| DATE_INSERTED | datetime | Yes | Created timestamp |

### JobCardIds (ID Generation)

| Column | Type | Description |
|--------|------|-------------|
| DealerId | int | Composite PK |
| BranchId | int | Composite PK |
| TableName | varchar | Target table (e.g., MDMS_SERV_APPOINT) |
| FinYear | int | Financial year (nullable) |
| StartRange | bigint | Range start value |
| CurrentId | bigint | Current running value |

### AppointmentServFollowUpDet (Audit Trail)

| Column | Type | Description |
|--------|------|-------------|
| DEALER_ID | int | PK |
| BRANCH_ID | int | PK |
| APPOINTMENT_ID | bigint | PK |
| SERV_APP_FOLLOWUP_ID | bigint | PK |
| FOLLOWUP_NO | smallint | Sequence number |
| FOLLOWUP_DATE | datetime | When follow-up created |
| EXP_VISIT_DT | datetime | Expected visit date |
| RESCHEDULE_DATE | datetime | New scheduled date |
| COMMENTS | varchar | Follow-up comments |
| CHANNEL | varchar | Communication channel |
| LEAKAGE_ID | int | 3=Rescheduled, 4=Cancelled |
| FOLLOWUP_TYPE | bit | Type flag |
| EMPLOYEE_ID | int | Service advisor |

### Relationships

```
Dealer (1) ──→ (N) Branch
Dealer (1) ──→ (N) DealerVehicleMapping ←── (1) Vehicle
Dealer (1) ──→ (N) DealerCustomerMapping ←── (1) Customer
Customer (1) ──→ (N) CustomerContact
Customer (1) ──→ (N) CustomerAddress
Vehicle (1) ──→ (1) VehicleModel ──→ (1) VehicleModelPart
ServAppointment (N) ←── (1) Dealer
ServAppointment (N) ←── (1) Customer
ServAppointment (N) ←── (1) Vehicle
ServAppointment (1) ──→ (N) ServiceAppointmentRequest ──→ (N) ServiceAppointmentSubRequest
ServAppointment (1) ──→ (N) AppointmentServFollowUpDet
```

---

## 3. Key Algorithms / Business Logic

### Slot Generation Algorithm

```csharp
// Config: StartTime=10AM, EndTime=6PM, SlotDuration=30min, Lunch=1-2PM, CapacityPerSlot=4
totalCapacity = serviceAdvisorCount × capacityPerSlot

for each day in [startDate..endDate]:
    currentSlot = day + StartTime
    while currentSlot < day + EndTime:
        nextSlot = currentSlot + SlotDuration
        
        // Skip lunch
        if currentSlot overlaps [LunchStart, LunchEnd] → skip
        
        bookedCount = bookedSlots.Count(b => b.Date == day && b.Time in [current, next))
        available = totalCapacity - bookedCount
        
        if available > 0 → add slot { Time, Available, Total }
        currentSlot = nextSlot
```

### ID Generation (JobCardIds)

```csharp
// Sequential per dealer/branch/table
currentId = GetCurrentId(dealerId, branchId, "MDMS_SERV_APPOINT", null)
// Use currentId as new APPOINTMENT_ID
// After insert: UPDATE SET CurrentId = currentId + 1
```

### Status State Machine

```
Open (STATUS=0)
  ├─→ Rescheduled (STATUS=0, new APPOINT_DATE, FollowUp with leakageId=3)
  ├─→ Cancelled (STATUS=1, REASON_ID=4, FollowUp with leakageId=4)
  └─→ Closed (STATUS≥1, REASON_ID=0)

// Guards:
// - Cannot update if STATUS > 0 (already closed/cancelled)
// - Each update creates AppointmentServFollowUpDet record
// - Follow-up ID generated from JobCardIds (MDMS_SERV_APP_FOLLOWUP_DET)
```

### Search Routing

```csharp
if (ONLY MobileNumber provided):
    → Resolve customerIds from CustomerContact table
    → Query by customerIds OR contactNo
else:
    → Resolve customerIds from mobile (if provided)
    → Resolve vehicleId from frameNo/registrationNo (if provided)
    → Apply dealer/branch/date/status filters
    → Status mapping: "open"→STATUS=0, "cancelled"→REASON_ID=4+STATUS=1, "closed"→REASON_ID=0+STATUS≥1
```

---

## 4. Configuration Management

### Configuration Sources (Priority Order)

1. **Environment variables** (Kubernetes ConfigMaps/Secrets) — highest
2. **`.env` file** (loaded via DotNetEnv) — local dev
3. **`appsettings.json`** — defaults

### Key Configuration Sections

```json
{
  "ConnectionStrings": {
    "AppointmentDbConnection": "Server=...;Database=OnlineDMS_UAT_New;..."
  },
  "SlotSettings": {
    "StartTime": "10:00 AM",
    "EndTime": "6:00 PM",
    "SlotDuration": 30,
    "LunchStart": "01:00 PM",
    "LunchEnd": "02:00 PM",
    "CapacityPerSlot": 4
  },
  "OpenTelemetry": {
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://otel-gw-logs.tvsmotor.com",
    "OTEL_SERVICE_NAME": "appointment-booking-service",
    "SERVICE_VERSION": "1.0.0",
    "DEPLOYMENT_ENVIRONMENT": "dev"
  }
}
```

### Environment Variables (Kubernetes)

| Variable | Purpose |
|----------|---------|
| `DB_CONNECTION` | SQL Server connection string override |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Telemetry collector URL |
| `OTEL_SERVICE_NAME` | Service identifier in traces |
| `SERVICE_VERSION` | Deployed version tag |
| `DEPLOYMENT_ENVIRONMENT` | Environment label (dev/uat/prod) |

---

## 5. Testing Strategy

### Test Projects

| Project | Scope | Framework |
|---------|-------|-----------|
| `Appointment.API.Tests` | Controller unit tests | xUnit + Moq |
| `Appointment.Application.Tests` | Service logic tests | xUnit + Moq |
| `Appointment.Infrastructure.Tests` | Repository tests | xUnit + EF InMemory |

### Coverage Configuration

All test projects include `coverlet.runsettings` for code coverage collection.

```bash
# Run all tests with coverage
dotnet test Appointment.sln --settings coverlet.runsettings --collect:"XPlat Code Coverage"
```

### Test Patterns

- **Controller tests**: Mock `IAppointmentService`, verify HTTP responses
- **Service tests**: Mock repositories, validate business logic
- **Repository tests**: In-memory DbContext, verify query correctness

---

## 6. Dependency Injection Registration

### Application Layer (`AddApplication()`)

```csharp
services.AddScoped<AppointmentServiceDependencies>();
services.AddScoped<IAppointmentService, AppointmentService>();
services.AddScoped<IVehicleService, VehicleService>();
```

### Infrastructure Layer (`AddInfrastructure()`)

```csharp
services.AddDbContext<AppointmentDbContext>(options => options.UseSqlServer(connectionString));
services.AddScoped<IAppointmentRepository, AppointmentRepository>();
services.AddScoped<IDealerRepository, DealerRepository>();
services.AddScoped<IVehicleRepository, VehicleRepository>();
services.AddScoped<ICustomerRepository, CustomerRepository>();
services.AddScoped<ICustomerRequestRepository, CustomerRequestRepository>();
services.AddScoped<ICustomerSubRequestRepository, RequestSubTypeRepository>();
services.AddScoped<IEmployeeRepository, EmployeeRepository>();
services.AddScoped<ICustomerContactRepository, CustomerContactRepository>();
services.AddScoped<IServAppointmentFollowUpDetRepository, ServAppointmentFollowupDetRepository>();
services.AddScoped<IUnitOfWork, UnitOfWork>();
services.AddScoped<IDealerVehicleMappingRepository, DealerVehicleMappingRepository>();
services.AddScoped<IDealerCustomerMappingRepository, DealerCustomerMappingRepository>();
```

---

*Last updated: July 2026*
