# booking-crud-services


## Product Context


# Booking CRUD Services — Product Context

## What This Service Does

A centralized booking management system for TVS Motor Company (TVSM) that handles vehicle bookings across multiple platforms. It replaces previously siloed booking systems (each platform managed its own bookings) with a single unified interface supporting the full booking lifecycle.

**Booking 2.0** — the internal codename for this service rewrite.

## Domain Entities

### Core Entities

| Entity | Purpose |
|--------|---------|
| `Booking` | Central aggregate — holds customer, dealer, vehicle, status, versioning (UUID primary key, 20 chars) |
| `Payment` | Payment records linked to a booking (many-to-one). Tracks channel, gateway, mode, status, amounts |
| `Vehicle` | Vehicle details per booking (many-to-one). Includes model/variant/color, frame/engine numbers, allocation status |
| `Location` | Customer location tied to a booking (one-to-one) |
| `Product` | Accessories, merchandise, charging solutions linked to a booking |
| `SubOrders` | Child orders (e.g., NOISE bookings) linked to a parent booking |

### Supporting Entities

| Entity | Purpose |
|--------|---------|
| `BookingCancellation` | Cancellation details (reason, source, refund info) |
| `BookingRefund` | Refund transaction records |
| `BookingJournal` | Audit log — every operation is journalized with request/response/status |
| `BookingTopicLog` | Service Bus message publish log (success/failed tracking) |
| `BookingConfig` | Runtime configuration per booking context |

### Master Data Entities

| Entity | Purpose |
|--------|---------|
| `DealerMaster` | Dealer information synced from MDP |
| `DealerContact`, `DealerFlag`, `DealerLocation` | Dealer metadata |
| `DmsVehicleMaster` | Vehicle master data from DMS |

### Log Entities

`AtpLog`, `MdpLog`, `DmsLog`, `RequestLog`, `RefundTransactionLog`, `DealerChangeLeadIdGenerationLog`

## Booking Lifecycle

```
Pre-Booking → Initiated → Open → Allotted → Invoiced → Delivered
                                    ↓
                               Cancelled (with refund workflow)
```

### Booking Statuses
- `Pre Booking Initiated` / `Pre Booking Created`
- `Initiated` — payment pending
- `Open` — payment confirmed, booking active
- `Allotted` — vehicle allocated
- `Invoiced` — invoice generated
- `Delivered` — vehicle delivered to customer
- `Cancelled` — booking cancelled (triggers refund)

### BTO (Build-to-Order) Statuses
`Order Received → Order Confirmed → Order Created → Order Manufactured → Order Packed → Order Dispatched → Order At Dealership`

## Key Operations

### Creation (3 types)
- **Online** — customer books via EV/ICE website
- **Offline** — dealer creates booking via EMS/DMS
- **Pre-Booking** — reservation before full booking

### Modification (14+ types)
Payment update, Vehicle update, Customer update, Dealer change, Vehicle allocation/deallocation, BTO frame number addition, Invoice update, Invoice cancellation, Gatepass update, Retail finance update, BTO status update, DSE (Dealer Sales Executive) assign, Whole booking update, Suborder payment (NOISE)

### Cancellation
- Validates booking is cancellable (not initiated, not invoiced, not delivered)
- Triggers auto-refund workflow
- Publishes cancellation event to downstream systems

### Refund
- **Auto-refund** — triggered on cancellation via CPG/JusPay
- **FnF (Full and Final)** — manual refund initiated by operations
- Refund status webhooks from CPG (CCAvenue) and JusPay

### Retrieval (5 types)
- By Customer (phone/ID)
- By Dealer (dealer code + branch)
- BTO bookings
- CRM bookings
- Count queries

## Integrations

### Inbound (receives events via Service Bus topics)
| Source | Events |
|--------|--------|
| DMS | Booking updates, vehicle master sync |
| ATP | Vehicle ETA, milestones, full payment enable |
| MDP | Dealer master data (create/update) |
| Service Bus (self) | Refund status callbacks |

### Outbound (publishes events to Service Bus)
| Target | Events |
|--------|--------|
| Lead System (LS) | Booking created, cancelled, dealer change |
| EMS | All booking lifecycle events |
| DMS | Booking creation, modifications |
| ATP | Booking created, full payment |
| Comms | Notifications (confirmation, cancellation, milestones) |
| EV/ICE Website | Status updates |
| Refund Service (RS) | Refund initiated |
| Marketplace Service | Marketplace booking events |

### External APIs
| System | Purpose |
|--------|---------|
| Azure Key Vault | All secrets and configuration |
| CPG (CCAvenue) | Payment gateway refund API |
| JusPay | Payment gateway refund API |
| Lead Service | Lead ID generation for dealer changes |

## Business Rules

1. **Optimistic concurrency** — every mutation requires matching `version` + `checkSum`. Checksum is SHA-256 chained from previous checksum.
2. **Duplicate booking prevention** — validates by `leadId` before creation; validates no open booking exists for same customer phone + source.
3. **Booking locking** — bookings can be locked to prevent concurrent modifications.
4. **Cancellation guards** — cannot cancel `Initiated`, `Invoiced`, or `Delivered` bookings.
5. **SPD vehicle lock** — SPD (Special Purpose Dealer) bookings cannot modify vehicle after payment.
6. **BTO idempotency** — BTO status updates are idempotent (same status = no-op).
7. **Payment validation** — full payment cannot be applied twice; duplicate payments are detected.
8. **Dealer change** — creates a new booking UUID, cancels old one, generates new lead ID.
9. **Fire-and-forget publishing** — event publishing to Service Bus happens via `setImmediate()` after HTTP response is sent.
10. **Invoice scheduler** — Comms notifications for invoiced bookings are scheduled 7 days out via Service Bus scheduled messages.
11. **Vehicle types** — EV (Electric), ICE (Internal Combustion Engine), BTO (Build-to-Order).
12. **Payment channels** — Cash, CPG (CCAvenue), JusPay.
13. **Booking sources** — EV Website, ICE Website, EMS, DMS, Marketplace (Amazon/Flipkart).



## Code Structure


# Booking CRUD Services — Project Structure

## Directory Layout

```
booking-crud-services/
├── src/
│   ├── main.ts                          # Bootstrap: OTel SDK → NestFactory → Swagger → GlobalPipes → Listen
│   ├── otel.ts                          # OpenTelemetry setup (traces + logs, OTLP HTTP export)
│   ├── otel-propagation.ts              # OTel context propagation helpers for Service Bus messages
│   ├── app.module.ts                    # Root module: ConfigModule, TypeORM (MSSQL), CloudConductor, Bookings, Logging
│   ├── schema.gql                       # GraphQL schema (unused/legacy)
│   │
│   ├── bookings/                        # Core business domain module
│   │   ├── bookings.module.ts           # Module registration: entities, services, controllers, exports
│   │   ├── controllers/
│   │   │   └── bookings.controller.ts   # Single controller — all booking REST endpoints
│   │   ├── dto/                         # Request/response DTOs with class-validator decorators
│   │   │   ├── booking-creation/        # CreateBookingRequestDto, Online/Offline variants
│   │   │   ├── booking-modification/    # UpdateBookingRequestDto, WholeBookingUpdateDto
│   │   │   ├── booking-cancellation/    # CancelBookingRequestDto
│   │   │   ├── booking-retrieval/       # Retrieval request/response DTOs per type
│   │   │   ├── booking-refund-status-update/  # Webhook DTOs from CPG/JusPay
│   │   │   └── *.dto.ts                # Shared DTOs (BookingDto, PaymentDto, VehicleDto, etc.)
│   │   └── services/
│   │       ├── Ibooking.service.ts      # Core interfaces (ICreateBookingService, IModifyBookingService, etc.)
│   │       ├── booking-factory.service.ts  # Factory pattern — routes to correct service by enum type
│   │       ├── index.ts                 # Barrel exports for interfaces
│   │       ├── booking-creation/        # Online, Offline, Pre-booking services + booking number generation
│   │       ├── booking-modification/    # 11 subdirectories, one per modification type
│   │       │   ├── payment/
│   │       │   ├── vehicle/
│   │       │   ├── vehicle-allocation/
│   │       │   ├── customer/
│   │       │   ├── dealer/
│   │       │   ├── invoice/
│   │       │   ├── gate-pass/
│   │       │   ├── retail-finance/
│   │       │   ├── bto-status-update/
│   │       │   ├── dse-assign/
│   │       │   └── booking-update/
│   │       ├── booking-cancellation/    # Cancellation + workflow orchestration
│   │       ├── booking-refund/          # Auto-refund, FnF refund, CPG/CCAvenue/JusPay refund services
│   │       ├── booking-refund-status-update/  # Webhook handlers for refund status callbacks
│   │       ├── booking-retrieval/       # Customer, Dealer, BTO, CRM, Count retrieval services
│   │       ├── custom-repositories/     # TypeORM repository wrappers
│   │       │   ├── booking-repository/
│   │       │   ├── payment-repository/
│   │       │   ├── vehicle-repository/
│   │       │   ├── cancellation-repository/
│   │       │   ├── refund-repository/
│   │       │   ├── logging-repository/
│   │       │   └── mdp-repository/
│   │       ├── publisher/               # Event publishers (one per domain operation)
│   │       │   ├── booking-creation/
│   │       │   ├── booking-modification/
│   │       │   ├── booking-cancellation/
│   │       │   ├── booking-refund/
│   │       │   ├── booking-refund-status-update/
│   │       │   ├── atp-handler/
│   │       │   └── dms-integration/
│   │       ├── atp-handler/             # ATP event processing
│   │       ├── dms-integration/         # DMS event processing
│   │       ├── validation/              # Request validation (version/checksum, booking state)
│   │       ├── exception-handler/       # Booking-specific exception handling
│   │       ├── lead-service/            # Lead ID generation
│   │       ├── mdp/                     # Master Data Platform dealer sync
│   │       ├── noise/                   # NOISE (accessories/merchandise) booking service
│   │       ├── cpg.service.ts           # CPG payment gateway client
│   │       └── jusPay.service.ts        # JusPay payment gateway client
│   │
│   ├── cloud-conductor/                 # Azure Service Bus infrastructure module
│   │   ├── cloud-conductor.module.ts    # Global module: publisher, listeners, secrets
│   │   └── services/
│   │       ├── keyvault/                # Azure Key Vault secret retrieval
│   │       ├── publisher/               # TopicPublisherService — sends messages to Service Bus topic
│   │       ├── listener/                # Topic listeners (booking refund, DMS, ATP, MDP dealer)
│   │       └── model-transformer/       # Transforms domain events to Service Bus message format
│   │
│   ├── database/
│   │   └── entities/                    # 24 TypeORM entity classes (MSSQL)
│   │
│   ├── logger/
│   │   ├── logging.module.ts            # Global logging module
│   │   └── logging.service.ts           # Winston + OTel dual logging
│   │
│   └── shared/
│       ├── constants/constants.ts       # All enums (statuses, types, routes, messages)
│       ├── exceptions/                  # Custom exception classes + GlobalExceptionFilter
│       └── utils.ts                     # UUID generation, checksum, response builder, enum converter
│
├── azure-pipelines/                     # CI/CD pipeline definitions (dev, UAT, prod, sonar, image scan)
├── Dockerfile                           # Multi-stage build (node:25.9-alpine)
├── package.json                         # Dependencies, scripts, Jest config
├── nest-cli.json                        # NestJS CLI configuration
├── .eslintrc.js                         # ESLint + Prettier + TypeScript
└── .prettierrc                          # Single quotes, trailing commas, 80 char width
```

## Module Dependencies

```
AppModule
├── ConfigModule (global)
├── TypeOrmModule.forRootAsync (MSSQL via Azure AD service principal)
├── CloudConductorModule (global)
│   ├── SecretService (Azure Key Vault)
│   ├── TopicPublisherService (Service Bus publish)
│   ├── TopicListenerService (booking refund events)
│   ├── DMSTopicListenerService
│   ├── ATPTopicListenerService
│   └── MDPDealerTopicListenerService
├── BookingsModule
│   ├── BookingsController (single controller, all endpoints)
│   ├── BookingFactoryService (routes to creation/modification/retrieval services)
│   ├── 40+ provider services
│   └── TypeOrmModule.forFeature([24 entities])
└── LoggingModule (global)
    └── LoggingService (Winston + OTel)
```

### Circular Dependency

`BookingsModule ↔ CloudConductorModule` — resolved via `forwardRef(() => ...)` in both modules. CloudConductorModule listeners need booking services; BookingsModule publishers need the topic publisher.

## Architectural Decisions

1. **Single controller** — all booking endpoints live in one controller. Routing is by HTTP method + path, not by separate controllers per domain.

2. **Factory pattern for dispatch** — `BookingFactoryService` maps enum values to service instances. Adding a new booking type means: add enum value, create service, register in factory constructor.

3. **Interface-first services** — every service implements an interface (prefixed with `I`). Injection uses `@Inject(ConcreteService)` with interface typing.

4. **Custom repository layer** — TypeORM repositories are wrapped in custom service classes under `custom-repositories/`. Direct repository injection is not used in business services.

5. **Publisher per operation** — each domain operation (creation, modification, cancellation, refund) has its own publisher service that builds the topic message and delegates to `TopicPublisherService`.

6. **Global module for infrastructure** — `CloudConductorModule` is `@Global()` so all modules can access secrets and publishing without explicit imports.

7. **Listeners as OnModuleInit** — Service Bus listeners initialize on module startup, accept sessions in an infinite loop with retry.

8. **Optimistic concurrency at controller level** — version/checksum validation happens in the controller before delegating to services.

9. **Journal everything** — every controller method creates a `JournalDto`, populates it through the flow, and persists it in `finally` block regardless of success/failure.

10. **Fire-and-forget publishing** — `setImmediate()` is used to publish events after the HTTP response is sent, decoupling response latency from messaging.



## Tech Stack & Dependencies


# Booking CRUD Services — Technical Guide

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Node.js | 25.9 (Alpine) |
| Framework | NestJS | 11.x |
| Language | TypeScript | 5.x |
| Database | Microsoft SQL Server | via TypeORM 0.3.x |
| DB Auth | Azure AD Service Principal | `azure-active-directory-service-principal-secret` |
| Messaging | Azure Service Bus | `@azure/service-bus` 7.x (topics + sessions) |
| Secrets | Azure Key Vault | `@azure/keyvault-secrets` 4.x |
| Observability | OpenTelemetry | SDK 0.214, traces + logs via OTLP HTTP |
| Logging | Winston | 3.x + daily-rotate-file |
| Validation | class-validator + class-transformer | 0.14.x / 0.5.x |
| API Docs | Swagger | `@nestjs/swagger` 11.x |
| HTTP Client | Axios | 1.x |
| Cache | ioredis | 5.x (Redis) |
| Testing | Jest + ts-jest | 30.x / 29.x |
| Linting | ESLint + Prettier | 10.x / 3.x |
| CI/CD | Azure DevOps Pipelines | YAML-based |
| Container | Docker | Multi-stage, node:25.9-alpine |

## Coding Conventions

### File Naming
- Entity files: `kebab-case.entity.ts` (e.g., `booking-cancellation.entity.ts`)
- Service files: `kebab-case.service.ts` (e.g., `online-booking.service.ts`)
- Interface files: `I` prefix + PascalCase (e.g., `IBooking-repository.service.ts`, `Ibooking.service.ts`)
- DTO files: `kebab-case.dto.ts` (e.g., `create-booking-request.dto.ts`)
- Spec files: co-located as `*.spec.ts`
- Constants: single file `constants.ts` with all enums

### TypeScript Style
- **Prettier**: single quotes, trailing commas (`all`), 80 char print width
- **ESLint**: `@typescript-eslint/recommended` + `prettier/recommended`
- `@typescript-eslint/no-explicit-any`: **off** — `any` is used freely
- `explicit-function-return-type`: **off**
- `explicit-module-boundary-types`: **off**
- Prefer `class` over functional patterns for services
- Use `enum` for all domain constants (not string unions or `as const`)

### NestJS Patterns
- **Dependency injection**: `@Inject(ConcreteService)` with interface type annotation
- **Module structure**: one module file, one controller, many services
- **Global modules**: `@Global()` decorator on infrastructure modules (CloudConductor, Logging)
- **Circular deps**: resolved with `forwardRef(() => Module)`
- **Validation pipe**: global `ValidationPipe({ whitelist: true })` strips unknown properties
- **Swagger decorators**: `@ApiOperation`, `@ApiBody`, `@ApiResponse`, `@ApiTags` on all endpoints

### DTO Conventions
- Use `class-validator` decorators (`@IsString`, `@IsNotEmpty`, `@IsOptional`, etc.)
- Use `class-transformer` `@Type()` for polymorphic deserialization based on request type
- DTOs are plain classes (not interfaces) to support runtime validation
- Nested DTOs use `@ValidateNested()` + `@Type()`

### Entity Conventions
- TypeORM decorators (`@Entity`, `@Column`, `@PrimaryColumn`, `@Index`)
- `Booking` uses `@PrimaryColumn` (app-generated UUID), not `@PrimaryGeneratedColumn`
- Other entities use `@PrimaryGeneratedColumn()` (auto-increment)
- Relations: `@OneToOne`, `@OneToMany`, `@ManyToOne` with `@JoinColumn`
- MSSQL-specific types: `nvarchar(max)`, `datetime`, `decimal(10,2)`
- `@CreateDateColumn()` for audit timestamps
- Composite indexes for query optimization

## Patterns

### Factory Pattern (Core Dispatch)
```typescript
// BookingFactoryService maps enum → service instance
const service = this.bookingFactoryService.getBookingCreationService(type);
const result = await service.processBooking(request, data);
```
To add a new operation type:
1. Add value to the relevant enum in `constants.ts`
2. Create service implementing the interface (`ICreateBookingService`, `IModifyBookingService`, etc.)
3. Register in `BookingFactoryService` constructor map
4. Add to `bookings.module.ts` providers

### Optimistic Concurrency
```typescript
// Every mutation: validate → increment version → generate new checksum → persist
await this.validationService.validateVersionAndChecksum(request);
const newChecksum = generateChecksum(request.checkSum); // SHA-256 chain
await this.bookingRepositoryService.updateVersionChecksum(uuid, version + 1, newChecksum);
```

### Journal Pattern
```typescript
// Every controller method follows this structure:
let journalDto = new JournalDto();
journalDto.source = request.source;
journalDto.request = request;
journalDto.status = -1; // default failure
try {
  // ... business logic ...
  journalDto.status = 1; // success
  return response;
} catch (error) {
  journalDto.outgoingResponse = error.message;
  await this.exceptionHandlerService.handleBookingException(error);
} finally {
  await this.dbLoggingService.journalizeBooking(journalDto); // always persists
}
```

### Event Publishing (Fire-and-Forget)
```typescript
// After returning HTTP response, publish asynchronously
setImmediate(async () => {
  await this.bookingCreationPublisherService.processPublish(request, data, response);
});
return response;
```

### Service Bus Message Structure
```typescript
// TopicModelDto → ServiceBusMessage
{
  body: JSON.stringify(payload),
  sessionId: bookingUUID,
  applicationProperties: {
    EventType: 'BOOKING_CREATED',
    EventSource: 'BS 2.0',
    EventTarget: 'LS-EMS-DMS',  // joined targets
  }
}
```

## Error Handling

### Exception Hierarchy
- `GlobalExceptionFilter` — catches all unhandled exceptions, normalizes to JSON response
  - All 500 errors are **downgraded to 400** with generic message (intentional design)
- `ExceptionHandlerService` — booking-specific exception re-throwing
- Custom exceptions extend `BadRequestException`:
  - `InvalidDealerCodeException`
  - `InvalidVersionOrChecksumException`
  - `BookingLockedException`
  - `BookingCancelledException`
  - `InvalidUUIDException`
  - `BookingUpdateNotAllowed`
  - `InvalidPartOrModelIdException`
  - `InvalidActionOrType`
  - `BookingOpenException`
  - `InitiatedBookingCancellException`
  - `InvoicedBookingCancelException`
  - `DeliveredBookingCancelException`
  - `SPDVehicleModificationLockedException`
  - `InvalidVehicleTypeFrameNumberAllocation`
- `DatabaseException` extends `Error` (not HttpException)

### Error Response Format
```json
{
  "statusCode": 400,
  "message": "Version or Checksum Mismatch Error",
  "timestamp": "2025-01-15T10:30:00.000Z"
}
```

### Logging on Error
- `LoggingService.logError()` writes to Winston error transport + OTel log
- `console.log`/`console.error` also used in some paths (legacy)
- Errors are logged with context (controller method, UUID, event type)

## Testing

### Framework
- **Jest** with `ts-jest` transform
- Test files co-located: `service-name.spec.ts` next to `service-name.ts`
- E2E tests in `test/` directory with separate Jest config (`jest-e2e.json`)

### Commands
```bash
npm run test          # unit tests
npm run test:cov      # with coverage
npm run test:e2e      # end-to-end
npm run test:watch    # watch mode
```

### Coverage Configuration
- Coverage excludes: `node_modules`, `logs`, `dto/`, `test-config`, `interfaces`, `.module.ts`, `main.ts`, `database/`, `index.ts`, `migrations/`, `schema.gql`, `scalars/`, `typeorm.config.ts`
- Reporters: `text` + `lcov`
- Output: `../coverage/`

### Test Style
- Mock all dependencies via `@nestjs/testing` `Test.createTestingModule`
- Use `jest.fn()` for service mocks
- Test service logic in isolation from database/messaging

## Deployment

### Docker
- Multi-stage build: `builder` (install + compile) → `runner` (dist + node_modules only)
- Base image: `node:25.9.0-alpine`
- Production port: `8080`
- `NODE_ENV=production`
- Entry: `node dist/main.js`

### Build Process
```bash
nest build                    # Compile TypeScript
cp package.json dist/         # Copy package.json to dist
cd dist && npm install --only=production  # Install prod deps in dist
```

### CI/CD (Azure DevOps)
- `ci-pipeline.yaml` — build + test + SonarQube
- `cd-pipeline.yaml` — Docker build + push + deploy
- `ast-booking-crud-uat-pipeline.yaml` — UAT deployment
- `ast-booking-crud-prod-pipeline.yaml` — Production deployment
- `ast-image-scan-booking-crud-pipeline.yaml` — Container image security scan
- `sonar.yaml` — SonarQube quality gate

### Environment Configuration
- All config via environment variables (loaded by `@nestjs/config` ConfigModule)
- Secrets stored in Azure Key Vault, fetched at runtime by `SecretService`
- Key env vars: `APP_PORT`, `KEYVAULT_URL`, `BOOKING_SERVICE_DB_CONFIG`, `BOOKING_SERVICE_CONFIG`, `BAS_DB_CLIENT_ID`, `BAS_DB_CLIENT_SECRET`
- OTel env vars: `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `DEPLOYMENT_ENVIRONMENT`, `SERVICE_VERSION`

### Startup Order
1. OpenTelemetry SDK starts (traces + logs)
2. NestJS app created
3. GlobalExceptionFilter registered
4. Swagger document generated + written to `swagger.json`
5. ValidationPipe registered globally
6. Service Bus listeners initialize (`onModuleInit`)
7. HTTP server starts on configured port

### Graceful Shutdown
- Handles `SIGINT` and `SIGTERM`
- Closes NestJS app → shuts down OTel SDK + log provider
- HTTP server timeout: 10 seconds

