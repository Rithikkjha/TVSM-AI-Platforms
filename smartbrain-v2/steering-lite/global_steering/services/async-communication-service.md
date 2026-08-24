# async-communication-service


## Product Context


# Async Communication Service — Product Context

## What This Service Does

This is an event-driven communication orchestrator for TVS Motor's online vehicle booking platform. It listens to booking lifecycle events from Azure Service Bus topics and dispatches customer/dealer notifications through multiple channels: Salesforce Marketing Cloud (email journeys), SendGrid (direct email), SMS (Tata Teleservices), WhatsApp (Oriserve), and CMP (Customer Management Platform).

The service does not expose REST APIs to external consumers. It runs as a long-lived process that subscribes to a Service Bus topic, processes messages based on vehicle type and event context, and triggers the appropriate communication workflow.

## Domain Entities

### Booking
The central entity. Represents a customer's vehicle booking with status lifecycle: Initiated → Open → Allotted → Invoiced → Delivered (or Cancelled). Key fields: UUID, customer info, dealer assignment, vehicle type, BTO status, ATP configuration, payment state, dirty flag (deduplication).

### Vehicle
Linked to a booking. Carries vehicleType (EV, ICE, BTO), model, variant, color, partId, modelId, and optional BTO kit details (race package, favourite number).

### Payment
Tracks partial and full payments. Contains amountPaid, paymentStatus (success/failed/abandoned/awaited), paymentType (partial/full/pre-booking).

### Customer
Name, email, phone number. Used as the subscriber key for Salesforce (prefixed with country code 91).

### Dealer
Dealership info: name, address, phone, dealerType (AMD, AD, APS, BRANCH, SPD), dealerId, branchId.

### Correspondence
Audit log entity. Every communication attempt is logged with: incoming request, outgoing request, response, third-party system name, brand, UUID, and timestamp.

### BookingCancellation / BookingRefund / RefundTransactionLog
Track cancellation and refund lifecycle events.

### CommunicationEventBccList
Stores BCC email lists per communication event type (e.g., "bto-mail").

### DmsVehicleMaster
Product master data used to identify EV brand (iQube, Orbiter, TVS X) from partId/modelId.

## Vehicle Types (Communication Cohorts)

| Type | Description | Communication Handler |
|------|-------------|----------------------|
| EV   | Electric vehicles (iQube, Orbiter, TVS X) | `EVCommunicationService` |
| ICE  | Internal Combustion Engine vehicles | `ICECommunicationService` |
| BTO  | Build-To-Order (Apache series custom kits) | `BTOCommunicationService` |

## EV Brand Sub-Routing

EV communications are further routed by brand (identified via DmsVehicleMaster lookup):
- **iQube** — default EV brand, event definition keys from KeyVault config
- **Orbiter** — uses dedicated Salesforce event definition keys
- **TVS X** — uses dedicated Salesforce event definition keys, includes city-based delivery timeline

## Integrations

### Azure Service Bus (Inbound)
- Session-enabled topic subscription with up to 20 concurrent sessions
- Messages carry `EventType` in application properties and a `TopicPayloadDto` JSON body
- Messages are completed immediately upon receipt (at-most-once processing with audit logging)

### Salesforce Marketing Cloud (Outbound)
- OAuth2 client_credentials token flow
- Fires journey events via `eventDefinitionKey` + contact data payload
- Used for EV and ICE email journeys (booking confirmation, cancellation, refund, modification, ATP events)

### SendGrid (Outbound)
- Direct email sending for BTO status update emails
- HTML templates stored in `src/shared/mailBody/`
- BCC lists pulled from database

### SMS via Tata Teleservices (Outbound)
- HTTP GET-based SMS API
- Text templates stored in `src/shared/btoSMSBody/`
- Used for BTO order status notifications

### WhatsApp via Oriserve (Outbound)
- POST-based API for delivery notifications
- Used for invoice/delivery events

### CMP — Customer Management Platform (Outbound)
- Batch payload API (array of key-value records)
- Uses same Salesforce OAuth token
- Used by BTO scheduler for daily dealer communications

### Azure Key Vault
- All secrets and configuration (DB credentials, API keys, endpoints) stored in Key Vault
- Accessed via `SecretService` using `DefaultAzureCredential`
- Config key: `COMMS_SERVICE_CONFIG` env var points to the secret name

### MSSQL Database
- Azure AD service principal authentication
- Read-only access for booking lookups and deduplication
- Write access for correspondence audit logging

## Business Rules

1. **Deduplication (Dirty Flag)**: If a booking's `dirty` field is true, the message is logged as `DIRTY_RECORD` and skipped.
2. **Marketplace Exclusion**: Cancellation events from Amazon/Flipkart marketplace bookings are silently ignored.
3. **DMS ICE Exclusion**: Messages from DMS source with ICE vehicle type are skipped (handled elsewhere).
4. **BOOKING_INITIATED Skip**: Messages with context `BOOKING_INITIATED` are not processed (no communication needed at initiation).
5. **ATP Old Booking Skip**: `ATP_BOOKING_CREATED` events with an `oldBookingUUID` are skipped.
6. **Failed Payment Routing**: Failed payment events are routed based on payment type — partial failures trigger booking confirmation failure flow, full payment failures trigger full payment failure flow.
7. **SPD Dealer Handling**: If dealer type is SPD or AMD, an additional SPD-specific Salesforce event is fired alongside the normal flow.
8. **BTO Status Progression**: BTO bookings follow: Order Received → Order Confirmed → Order Manufactured → Order Packed → Order Dispatched → Order At Dealership. Each status change triggers email + SMS + Salesforce event.
9. **BTO Scheduler**: Daily cron jobs (15:30 and 16:30) push open/packed BTO bookings to CMP for dealer follow-up.
10. **ATP Full Payment Enable**: Scheduler-driven logic checks ATP-configured bookings with vehicle ETA and enables full payment flag.



## Code Structure


# Async Communication Service — Structure

## Directory Layout

```
src/
├── main.ts                          # Bootstrap, creates NestJS app, listens on APP_PORT
├── app.module.ts                    # Root module: TypeORM config, imports all top-level modules
│
├── communication/                   # Core business logic — message routing and dispatch
│   ├── Icommunication.service.ts    # Generic interface: processRequest(context, data, logId)
│   ├── communication-factory.service.ts  # Factory: routes by vehicleType → EV/ICE/BTO handler
│   ├── communication.module.ts      # Registers all communication providers + TypeORM entities
│   ├── salesforce-sender.service.ts # Thin wrapper: logs + sends payload to SalesForceCommunicationService
│   │
│   ├── ev-mailer/                   # EV vehicle communication handlers
│   │   ├── ev-communication.service.ts   # Router: maps Context enum → specific EV service
│   │   ├── booking-confirmation/    # EV booking confirmation + ATP confirmation
│   │   ├── booking-cancellation/    # Cancellation initiation, FnF, refund FnF
│   │   ├── booking-modification/    # Dealer change, variant change, WhatsApp comms
│   │   ├── full-payment/            # Full payment success/failure emails
│   │   ├── atp/                     # ATP-specific: EDD change, milestone, FIFO, payment enable
│   │   ├── u388/                    # U388 payment success handler
│   │   └── utils/                   # EVBrandService (iQube/Orbiter/TVSX identification)
│   │
│   ├── ice-mailer/                  # ICE vehicle communication handlers
│   │   ├── ice-communication.service.ts  # Router: maps Context → ICE services
│   │   ├── booking-confirmation/    # Customer + dealer confirmation emails
│   │   ├── booking-intimation/      # DMS booking number notification
│   │   └── booking-cancellation/    # Cancellation, refund initiation/success/failure
│   │
│   ├── bto-mailer/                  # BTO (Build-To-Order) communication handlers
│   │   ├── bto-communication.service.ts       # Router: booking events + BTO status progression
│   │   ├── bto-salesforce-communication.service.ts  # BTO-specific Salesforce payload builder
│   │   └── bto-status/             # BTO order status services
│   │       ├── bto-mailer.service.ts    # SendGrid email sender with HTML templates
│   │       ├── bto-sms.service.ts       # SMS sender via Tata Teleservices
│   │       ├── bto-dealer.service.ts    # Scheduled CMP batch push for dealers
│   │       └── dto/                     # BTO-specific DTOs
│   │
│   ├── spd-mailer/                  # SPD/AMD dealer-specific Salesforce events
│   │   └── spd-communication.service.ts
│   │
│   └── dto/                         # Data Transfer Objects
│       ├── topic/                   # Inbound message shape (TopicPayloadDto + nested DTOs)
│       ├── atp/                     # ATP-specific communication DTOs
│       ├── salesforce-payload.dto.ts     # Outbound Salesforce event structure
│       ├── booking-confirmation.dto.ts   # Legacy DTO (used in interface typing)
│       ├── correspondence.dto.ts         # Audit log DTO
│       └── ...                      # Various payload DTOs per event type
│
├── custom-repositories/             # Data access layer (global module)
│   ├── repository.module.ts         # Global module exporting DBLogger + BookingRepository
│   ├── dbLogger/
│   │   └── dblogger.service.ts      # Correspondence table insert/update (audit trail)
│   └── booking-repository/
│       └── booking-repository.service.ts  # Booking lookups, BTO queries, city/variant data
│
├── database/
│   └── entities/                    # TypeORM entity definitions (MSSQL)
│       ├── booking.entity.ts        # Central booking entity with relations
│       ├── vehicle.entity.ts        # Vehicle details per booking
│       ├── payment.entity.ts        # Payment records
│       ├── correspondence.entity.ts # Communication audit log
│       └── ...                      # Location, Product, Cancellation, Refund, etc.
│
├── logger/
│   └── logging.service.ts           # Winston logger with daily rotate (info + error files)
│
└── shared/
    ├── utils.ts                     # convertToJSON helper (KeyVault string parsing)
    ├── constants/
    │   ├── constants.ts             # All enums: Context, VehicleType, BookingStatus, etc.
    │   └── errors.ts                # ExceptionMessage enum for error strings
    ├── mailBody/                    # HTML email templates (BTO status emails)
    ├── btoSMSBody/                  # SMS text templates (BTO status SMS)
    ├── cloudService/
    │   ├── cloud-conductor.module.ts     # Global module: SecretService + TopicListenerService
    │   ├── keyvault/
    │   │   ├── ISecret.service.ts        # Interface for secret retrieval
    │   │   └── secret.service.ts         # Azure KeyVault client (+ local dev fallback)
    │   └── topicListener/
    │       └── topic-listener.service.ts # Azure Service Bus session listener (entry point)
    └── salesforce/
        ├── salesforce.module.ts          # Module for Salesforce services
        ├── services/
        │   ├── token-request.service.ts           # OAuth2 client_credentials token fetch
        │   ├── salesforce-communication.service.ts # POST to Salesforce journey API
        │   ├── whatsapp-communication.service.ts  # POST to WhatsApp/Oriserve API
        │   └── cmp-communication.service.ts       # POST to CMP batch API
        └── scheduler/
            └── bto-scheduler.ts          # Cron jobs for daily BTO dealer notifications
```

## Module Dependency Graph

```
AppModule
├── ConfigModule (global)
├── TypeOrmModule.forRootAsync (MSSQL via Azure AD SP)
├── LoggingModule
├── RepositoryModule (global) ─── DBLoggerService, BookingRepositoryService
├── CloudConductorModule (global)
│   ├── SecretService
│   ├── TopicListenerService ──→ CommunicationFactoryService
│   └── imports CommunicationModule
└── CommunicationModule
    ├── TypeOrmModule.forFeature([...entities])
    ├── CommunicationFactoryService ──→ EV/ICE/BTO services
    ├── All EV/ICE/BTO communication services
    ├── SalesForceCommunicationService + TokenRequestService
    ├── WhatsAppCommunicationService
    ├── CMPCommunicationService
    ├── SalesforcePayloadSenderService
    └── BTOScheduler (cron)
```

## Architectural Decisions

### Event-Driven, No HTTP Controllers
The service has no REST controllers. The sole entry point is `TopicListenerService.onModuleInit()` which starts an Azure Service Bus session pool. This makes the service a pure consumer/processor.

### Factory Pattern for Vehicle Type Routing
`CommunicationFactoryService` maps `vehicleType` string → concrete service instance. Each vehicle type handler implements `ICommunicationService<Context, T>` and internally routes by event context via switch statements.

### Session-Based Concurrency
Uses Azure Service Bus sessions (max 20 concurrent) to ensure ordered processing per session while allowing parallelism across sessions. Sessions auto-close after 10s idle or 5min max lifetime.

### Immediate Message Completion
Messages are completed before processing (`completeMessage` called first). This is an at-most-once delivery guarantee — if processing fails, the message is lost but the error is logged to the Correspondence table.

### Global Modules for Cross-Cutting Concerns
`RepositoryModule` and `CloudConductorModule` are `@Global()` so their exports (DBLoggerService, BookingRepositoryService, SecretService) are available everywhere without explicit imports.

### Audit-First Design
Every communication attempt creates a Correspondence record before dispatching. The record is updated with the outgoing payload and response after the third-party call completes (or fails).

### Template-Based Email/SMS
BTO emails use HTML files in `shared/mailBody/` with placeholder replacement (e.g., `cust_name`, `vehicleName`). SMS uses text files in `shared/btoSMSBody/`. Templates are copied to `dist/` at build time via nest-cli assets config.

### Secrets as Bundled Config
A single KeyVault secret (referenced by `COMMS_SERVICE_CONFIG`) contains a JSON blob with all external service credentials and endpoints (Salesforce, SendGrid, SMS, WhatsApp, CMP URLs and keys).



## Tech Stack & Dependencies


# Async Communication Service — Tech & Conventions

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Node.js | 25.x (Alpine Docker image) |
| Framework | NestJS | 11.x |
| Language | TypeScript | 5.x |
| ORM | TypeORM | 0.3.x |
| Database | MSSQL (Azure SQL) | via `mssql` driver |
| Messaging | Azure Service Bus | SDK 7.9.5 (session-enabled topics) |
| Secrets | Azure Key Vault | SDK 4.8.x with DefaultAzureCredential |
| Email (BTO) | SendGrid | @sendgrid/mail 8.x |
| HTTP Client | Axios | 1.x |
| Logging | Winston + daily-rotate-file | 3.x / 5.x |
| Validation | class-validator + class-transformer | 0.14.x / 0.5.x |
| Scheduling | node-cron | 4.x |
| Config | @nestjs/config (dotenv-based) | 4.x |
| Build | NestJS CLI (`nest build`) | 11.x |
| Testing | Jest + ts-jest | 29.x |
| Linting | ESLint + Prettier | 8.x / 3.x |
| Container | Docker (multi-stage Alpine) | — |
| CI/CD | Azure Pipelines | YAML templates |

## Coding Conventions

### File Naming
- Services: `<name>.service.ts` (e.g., `bto-mailer.service.ts`)
- Specs: `<name>.spec.ts` colocated with the service
- DTOs: `<name>.dto.ts` in `dto/` folders
- Entities: `<name>.entity.ts` in `database/entities/`
- Modules: `<name>.module.ts`
- Interfaces: `I<name>.service.ts` (prefix with `I`, default export)
- Constants/enums: collected in `shared/constants/constants.ts`

### Naming Style
- Classes: PascalCase (e.g., `EVConfirmationService`, `BTOMailer`)
- Enums: UPPER_SNAKE_CASE for enum names and values (e.g., `VEHICLE_TYPE.EV`, `BTO_ORDER_STATUS.ORDER_RECEIVED`)
- Files/folders: kebab-case (e.g., `booking-confirmation`, `ev-mailer`)
- Variables/methods: camelCase
- Interfaces: PascalCase with `I` prefix (e.g., `ICommunicationService`, `ISecretService`)

### Module Organization
- Each feature area has its own folder under `communication/`
- DTOs are grouped by concern: `dto/topic/` for inbound, `dto/atp/` for ATP-specific, flat files for outbound payloads
- Barrel exports via `index.ts` files in entity and DTO folders
- Global modules (`@Global()`) for cross-cutting services (repositories, secrets)

### Dependency Injection
- Constructor injection throughout
- `@Inject()` decorator used when injecting by class reference that differs from the interface
- Services are registered as providers in their module and exported when needed by other modules
- No custom injection tokens — classes serve as their own tokens

## Patterns

### Factory + Strategy
`CommunicationFactoryService` selects the handler by vehicle type. Each handler (`EVCommunicationService`, `ICECommunicationService`, `BTOCommunicationService`) implements `ICommunicationService` and uses a switch statement to delegate to specific sub-services.

### Template Method (Email/SMS)
BTO emails and SMS follow a pattern: read template file → replace placeholders → send via external API. Placeholder tokens are simple strings like `cust_name`, `vehicleName`, `amount_value`.

### Payload Builder
EV services use builder utility functions (`buildSalesforcePayloadData`, `buildSalesforcePayloadEventDefinition`) to construct Salesforce payloads consistently.

### Audit Logging
All communication flows follow: `insertLogs()` → process → `updateLogs()`. The `logId` is threaded through every service call to maintain traceability.

### Configuration via Secrets
Runtime config is not in env vars directly. A single KeyVault secret contains a JSON blob with all service endpoints and credentials. Services parse this at runtime via `secretService.getSecret(configKey)`.

## Error Handling

### General Approach
- Services throw `InternalServerErrorException` or `HttpException` with descriptive messages from the `ExceptionMessage` enum
- Errors in the topic listener's `processMessage` are caught and logged (not re-thrown) to prevent session crashes
- Third-party call failures are logged to the Correspondence table before re-throwing

### Error Logging
- Errors are logged to both Winston (file-based) and the Correspondence DB table
- The `DBLoggerService.updateLogs()` records the error message as the response field
- Third-party system name is recorded (e.g., "SALESFORCE", "SENDGRID", "TATATEL", "WHATSAPP", "CMP")

### No Retry Logic
- Messages are completed immediately (at-most-once delivery)
- No built-in retry mechanism for failed third-party calls
- Failed communications are traceable via the Correspondence table for manual intervention

### Validation
- DTOs use `class-validator` decorators (`@IsString`, `@IsNotEmpty`, `@IsOptional`, etc.)
- No global validation pipe is configured — validation decorators serve as documentation rather than runtime enforcement in the current setup

## Testing

### Framework
- Jest with ts-jest transform
- Test files colocated with source: `*.spec.ts`
- `jest-mock-extended` for creating typed mocks

### Coverage Configuration
- Coverage collected from all `.ts`/`.js` files
- Excluded from coverage: `node_modules`, `logs`, `dto/`, `test-config/`, `.module.ts`, `main.ts`, `database/`, `index.ts`, `migrations/`, `scalars/`, `typeorm.config.ts`
- Reports: text + lcov

### Test Style
- Unit tests mock all dependencies via `jest.fn()` or `jest-mock-extended`
- NestJS `Test.createTestingModule()` used to build test modules
- Services are tested in isolation with mocked repository/HTTP/secret services

### Running Tests
```bash
npm test              # Run all tests
npm run test:cov      # Run with coverage
npm run test:watch    # Watch mode
```

## Build & Deployment

### Build Process
```bash
npm run build    # nest build → copy package.json to dist/ → npm install --production in dist/
```
The build produces a self-contained `dist/` folder with production dependencies.

### Docker
- Multi-stage build: `builder` (install + compile) → `runner` (copy dist + node_modules)
- Base image: `node:25.9.0-alpine`
- Exposes port 8080, runs `node dist/main.js`

### CI/CD (Azure Pipelines)
- **CI**: Triggered after SonarQube scan passes on `main`. Uses shared `build-template.yml` from DevOps repo.
- **CD**: Multi-environment deploy (dev → UAT → prod) with manual approval gates. Uses shared `deploy-template-cs.yml`. Helm chart name: `async-communication`.
- **Image Scan**: Separate pipeline for container security scanning.
- **UAT**: Dedicated pipeline for UAT environment testing.

### Environment Variables Required
| Variable | Purpose |
|----------|---------|
| `COMMS_SERVICE_CONFIG` | KeyVault secret name containing all service config |
| `COMMS_SERVICE_DB_CONFIG` | KeyVault secret name for DB connection details |
| `COMMS_DB_CLIENT_ID` | Azure AD SP client ID for DB auth |
| `COMMS_DB_CLIENT_SECRET` | Azure AD SP client secret for DB auth |
| `COMMS_DB_TENANT_ID` | Azure AD tenant ID for DB auth |
| `KEYVAULT_URL` | Azure Key Vault URL (production only) |
| `NODE_ENV` | `development` for local mode (reads local-secret.json) |
| `APP_PORT` | HTTP port (default 3000, Docker sets 8080) |

### Local Development
- Set `NODE_ENV=development` to bypass Azure Key Vault and read from `local-secret.json` at project root
- Fallback to `.env` via ConfigService if JSON file doesn't contain the key
- Run with `npm run start:dev` for watch mode

