# Job Card Service — Low Level Design

## API Endpoints (All Controllers)

### JobcardController [Route: api/]

| Method | Route | Auth | Description | Request Params | Response |
|--------|-------|------|-------------|----------------|----------|
| GET | /api/maintenance/due/fetch/{frameNo} | None (stub) | Get next service due/lead for vehicle | frameNo (path) | LeadsDto |
| GET | /api/service/history/fetch/{frameNo} | None (stub) | Get job card history by frame number | frameNo (path), dealerId? (query), branchId? (query), jobcardId? (query), status? (query) | List\<ServiceHistoryDto\> |
| GET | /api/service/history/detail/fetch/{dealerId}/{branchId}/{jobcardId} | None (stub) | Get detailed service history (complaints, parts, labour, estimates, proforma) | dealerId, branchId, jobcardId (path) | ServiceHistoryDetailsDto |
| GET | /api/service/invoice/fetch/{dealerId}/{branchId}/{jobcardId} | None (stub) | Get job card invoice details | dealerId, branchId, jobcardId (path) | List\<JobCardInvoiceResponseDto\> |
| GET | /api/service/health/{dealerId} | None (stub) | Health check / dealer validation | dealerId (path) | Output { StatusCode, Message } |
| GET | /api/jobcard/configurations/fetch/{frameNo}?odometerReading= | None (stub) | Get job types and convenience modes based on frame + odometer | frameNo (path), odometerReading (query, required) | JobTypeResponseDto |

### PartsController [Route: /api/service/frt]

| Method | Route | Auth | Description | Request Params | Response |
|--------|-------|------|-------------|----------------|----------|
| GET | /api/service/frt/parts/fetch/{modelId}/{dealerId}/{branchId} | None (stub) | Fetch FRT parts based on vehicle model ID | modelId, dealerId, branchId (path), isPmlEnabled (query, default false) | List of FRT parts |

### AutoLaborController [Route: api/service/frt/autoLabor]

| Method | Route | Auth | Description | Request Params | Response |
|--------|-------|------|-------------|----------------|----------|
| POST | /api/service/frt/autoLabor/create | None (stub) | Generate auto-labour preview from complaints | Body: AutoLaborRequestDto { dealerId, modelId, complaints[], labourDiscounts } | AutoLaborResponseDto { Complaints[], Labors[] } |
| GET | /api/master/labour/fetch | None (stub) | Get master labour data (categories, max FRT, SAC code, aggregates, actions) | None | MasterLaborResponseDto |
| GET | /api/master/vehicle/fetch?dealerId= | None (stub) | Get vehicle variances for a specified dealer | dealerId (query) | VehicleVarianceResponseDto { VehicleVariance[] } |

### LabourController [Route: /api/labour/frt]

| Method | Route | Auth | Description | Request Params | Response |
|--------|-------|------|-------------|----------------|----------|
| GET | /api/labour/frt/fetch/{dealerId}/{branchId}/{labourTypes} | None (stub) | Fetch FRT manual labours by dealer/branch/types | dealerId, branchId (path), labourTypes (path, comma-separated ints e.g. "2,3,4") | List of dealer labours |
| POST | /api/labour/frt/create | None (stub) | Create a new labour entry for dealer/branch | Body: CreateLabourRequestDto | CreateLabourResponseDto { Code, Description } |
| PUT | /api/labour/frt/update | None (stub) | Update an existing labour entry | Body: UpdateLabourRequestDto | UpdateLabourResponseDto |
| POST | /api/service/labour/{laborCode}/issueMode/{issueModeId}/check | None (stub) | Validate labour code against issue mode | laborCode, issueModeId (path), Body: ValidateLabourRequestDto { dealer, vehicle, subscriptions } | ValidateLabourResponseDto { IsValid, Message } |
| POST | /api/labour/pml/fetch | None (stub) | Fetch PML (Periodic Maintenance Labour) preview | Body: PmlFetchRequestDto { modelId, dealerId, jobType, isAmcChecked } | PmlFetchResponseDto { code, cost, issueMode, configurations } |

---

## Code Structure

```
job-card-service/
├── src/
│   ├── Jobcard.API/                    (ASP.NET Core 9.0 Web API)
│   │   ├── Controllers/
│   │   │   ├── JobcardController.cs    (Service history, leads, invoice, health, job types)
│   │   │   ├── LabourController.cs     (FRT labour CRUD, PML fetch, issue mode validation)
│   │   │   ├── PartsController.cs      (FRT parts retrieval)
│   │   │   └── AutoLaborController.cs  (Auto-labour generation, master data)
│   │   ├── Security/
│   │   │   └── BearerAuthenticationHandler.cs  (Stub - TODO implementation)
│   │   ├── Filters/
│   │   │   ├── BasePathFilter.cs       (Swagger base path)
│   │   │   └── GeneratePathParamsValidationFilter.cs
│   │   ├── Models/
│   │   │   ├── Output.cs              (Standard API response wrapper)
│   │   │   └── RateLimiterSettings.cs
│   │   ├── Program.cs                 (App bootstrap, DI, OTEL, rate limiting, Swagger)
│   │   └── appsettings.json           (Configuration)
│   │
│   ├── Jobcard.Application/           (Business Logic Layer)
│   │   ├── Jobcard/
│   │   │   ├── IJobcardService.cs     (Interface: leads, history, invoice, health, job types)
│   │   │   ├── JobcardService.cs      (Implementation)
│   │   │   ├── IPartsService.cs / PartsService.cs
│   │   │   ├── IAutoLaborService.cs / AutoLaborService.cs
│   │   │   ├── ILabourService.cs / LabourService.cs
│   │   │   ├── Dtos/
│   │   │   │   ├── RequestDto/        (AutoLaborRequestDto, CreateLabourRequestDto, PmlFetchRequestDto, etc.)
│   │   │   │   └── ResponseDto/       (ServiceHistoryDto, AutoLaborResponseDto, PmlFetchResponseDto, etc.)
│   │   │   └── Validators/
│   │   │       └── CreateLabourValidator.cs
│   │   └── Extensions/
│   │       └── ServiceCollectionExtensions.cs  (DI: services + validators)
│   │
│   ├── Jobcard.Domain/                (Domain Layer - no dependencies)
│   │   ├── Entities/
│   │   │   ├── CustomerAggregate/     (Customer, CustomerAddress, CustomerContact)
│   │   │   ├── DealerAggregate/       (Dealer, Branch, Employee, Status)
│   │   │   ├── JobCardAggregate/      (JobCardBooking, JobComplaint, JobSpares, JobCardLabour, JobCardEstimation, etc.)
│   │   │   ├── LabourAggregate/       (Labour, LabourCategory, LabourType, LabourIdGenerate, ManHourCost, FrtVariance)
│   │   │   ├── PartAggregate/        (SparePart, Part, Aggregate, VehModelVariance, RackBIN)
│   │   │   ├── ProformaAggregate/    (ProformaInvoice, ProformaInvoiceLabor, ProformaInvoiceSparePart)
│   │   │   ├── VehicleAggregate/     (Vehicle, VehicleModel, AtwModelLogic, AtwVehicle)
│   │   │   ├── LeadsAggregate/       (Lead)
│   │   │   └── MasterAggregate/      (City, FrtId, ServicePrice, JobTypeCategory, ModelJobType, etc.)
│   │   ├── Repositories/             (37 repository interfaces)
│   │   ├── Exceptions/               (PmlException, domain exceptions)
│   │   └── SeedWork/                 (IUnitOfWork, base entity classes)
│   │
│   ├── Jobcard.Infrastructure/        (Data Access Layer)
│   │   ├── Persistence/
│   │   │   ├── JobCardDbContext.cs    (80+ DbSets, entity configurations)
│   │   │   ├── ReminderDbContext.cs   (Leads, Dealer, Branch, DealerVehicleMapping)
│   │   │   └── UnitOfWork.cs
│   │   ├── Repositories/             (37 repository implementations)
│   │   ├── EntityConfigurations/     (EF Core Fluent API configurations)
│   │   ├── Extensions/
│   │   │   └── ServiceCollectionExtensions.cs  (DI: DbContexts + repos)
│   │   └── Migrations/              (EF Core migrations)
│   │
│   ├── Jobcard.APITests/             (Integration tests)
│   ├── Jobcard.ApplicationTests/     (Unit tests)
│   └── Jobcard.InfrastructureTests/  (Infrastructure tests)
│
├── azure_pipelines/                   (CI/CD definitions)
│   ├── ci-pipeline.yaml
│   └── cd-pipeline.yaml
├── Dockerfile                         (Multi-stage: build + migrations + runtime)
├── Jobcard.sln                        (Solution file)
├── NuGet.Config                       (Feed configuration)
├── sonar.yaml                         (SonarQube config)
└── openapi 3.0.1.yaml                 (OpenAPI specification)
```

---

## Database Schema (EF Core — Code First)

### JobCardDbContext Entities (80+ tables)

#### Core Aggregates

| Entity | Table | Key Fields | Purpose |
|--------|-------|------------|---------|
| Dealer | Dealer | DealerId | Dealer master |
| Branch | Branch | BranchId, DealerId | Dealer branch |
| Customer | Customer | CustomerId | Customer master |
| CustomerAddress | CustomerAddress | AddressId, CustomerId | Customer addresses |
| CustomerContact | CustomerContact | ContactId, CustomerId | Customer phone/email |
| Vehicle | Vehicle | VehicleId, FrameNo | Vehicle registration |
| JobCardBooking | JobCardBooking | JobCardId, DealerId, BranchId | Job card header |
| JobComplaint | JobComplaint | ComplaintId, JobCardId | Complaints on job card |
| JobCardLabour | JobCardLabour | LabourId, JobCardId | Labour assigned |
| JobSpares | JobSpares | SpareId, JobCardId | Parts issued |
| JobCardEstimation | JobCardEstimation | EstimationId | Cost estimation |
| JobCardInvoice | JobCardInvoice | InvoiceId, JobCardId | Final invoice |
| ProformaInvoice | ProformaInvoice | ProformaId, JobCardId | Proforma invoice |
| Employee | Employee | EmployeeId, DealerId | Service technicians |

#### FRT & Labour

| Entity | Table | Purpose |
|--------|-------|---------|
| Labour | Labour | Labour master (code, description, FRT, cost) |
| LabourCategory | LabourCategory | Labour type categories |
| LabourType | LabourType | Labour classification |
| FrtVariance | FrtVariance | FRT time variance by model |
| ManHourCost | ManHourCost | Man-hour cost by city/vehicle type |
| FrtId | FrtId | FRT ID master |
| ServicePrice | ServicePrice | Service pricing matrix |
| LabourIdGenerate | LabourIdGenerate | Auto-incrementing labour code |

#### Parts & Vehicle

| Entity | Table | Purpose |
|--------|-------|---------|
| Part | Part | Parts master |
| SparePart | SparePart | Spare part inventory |
| VehModelVariance | VehModelVariance | Vehicle model variants |
| VehicleModel | VehicleModel | Vehicle model master |
| AtwModelLogic | AtwModelLogic | ATW model mapping logic |

### ReminderDbContext Entities

| Entity | Table | Purpose |
|--------|-------|---------|
| Dealer | Dealer | Dealer (shared) |
| Branch | Branch | Branch (shared) |
| Lead | Lead | Service due/reminder leads |
| DealerVehicleMapping | DealerVehicleMapping | Which dealers service which vehicles |

---

## Key Algorithms / Business Logic

### Free Service Eligibility (JobcardService.GetJobTypesAsync)
```
1. Lookup vehicle by frameNo → get model, sale date
2. Get dealer settings (grace days, max free services)
3. Count existing free service job cards for this vehicle
4. If count < max AND within eligible window → eligible for free service
5. Determine job types: Free Service (1,2,3,15,16,25,26,28,29,30) vs Paid (31)
6. Return available job types + convenience modes
```

### Auto Labor Generation (AutoLaborService.GenerateAutoLaborPreviewAsync)
```
1. Input: dealerId, modelId, complaints[], labourDiscounts
2. Lookup FRT variance for model
3. For each complaint → find matching FRT labour codes
4. Calculate man-hour cost based on city type + vehicle type
5. Apply dealer-specific pricing overrides
6. Return generated complaints + labour items with costs
```

### PML Labour Calculation (LabourService.FetchPmlLabourAsync)
```
1. Input: modelId, dealerId, jobType, isAmcChecked
2. Lookup service price matrix for model
3. Determine PML cost based on job type category
4. Apply AMC discount if applicable
5. Return PML code, cost, issue mode, configurations
```

### Labour Code Generation (LabourService.CreateLabour)
```
1. Validate input via CreateLabourValidator
2. Get next available labour ID from LabourIdGenerate table
3. Create labour with dealer-specific pricing
4. Return generated code + description
```

---

## Configuration Handling

### appsettings.json
```json
{
  "ConnectionStrings": {
    "ReminderDbConnection": "...",
    "JobcardDbConnection": "..."
  },
  "LaborSettings": {
    "MaxFrt": { "TimeInMinutes": 210, "Frt": 3.8 },
    "SacCode": "998714"
  },
  "PmlSettings": {
    "Description": "PERIODIC MAINTENANCE LABOUR",
    "LabourCatId": "BEN",
    "HsnCode": "9985",
    "FreeServiceJobTypes": [1,2,3,15,16,25,26,28,29,30],
    "PaidServiceJobTypes": [31]
  },
  "RateLimiterSettings": { "PermitLimit": 25, "WindowInSeconds": 1 }
}
```

### Environment Variable Overrides (AKS)
- Connection strings injected from Azure Key Vault via CSI driver
- OTEL settings via env vars: `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, etc.
- `ASPNETCORE_ENVIRONMENT` for environment detection

---

## Request/Response Lifecycle

```
1. HTTP Request → Kestrel
2. → Rate Limiter middleware (25 req/sec per IP)
3. → Authorization middleware (currently no-op)
4. → Controller action
5. → Service layer (business logic + validation)
6. → Repository layer (EF Core queries)
7. → DbContext → SQL Server
8. → Return DTO → Controller → HTTP Response
```

---

## Validation Logic

- **Input validation**: Manual checks in controllers (null/empty, positive integers)
- **CreateLabourValidator**: Dedicated validator class for labour creation
- **Domain exceptions**: `PmlException` for business rule violations (HTTP 422)
- **EF Core constraints**: Entity configurations enforce DB-level constraints

---

## Error Handling

- **Controller level**: Try/catch with typed exception handling
- **Response codes**: 200, 201, 400, 404, 409, 422, 429, 500
- **Structured response**: `Output { StatusCode, Message }` or `Output { statusCode, message }`
- **Logging**: ILogger → Console + OpenTelemetry → Loki
- **No global exception middleware**: Each controller handles its own errors

---

## Testing Strategy

- `Jobcard.APITests/` — Integration tests (controller-level)
- `Jobcard.ApplicationTests/` — Unit tests for business logic services
- `Jobcard.InfrastructureTests/` — Repository/DB tests
- SonarQube for static analysis (configured in `sonar.yaml`)
