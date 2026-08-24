# bto_api


## Product Context


# BTO Dashboard API — Product Context

## What This Service Does

This is the backend API for a **Build-To-Order (BTO) vehicle booking dashboard**. It serves an internal dashboard used by operations teams to monitor and manage online vehicle bookings placed by customers through a BTO e-commerce flow.

The API provides:
- Authentication for dashboard users
- Booking search and lifecycle tracking
- Aggregated reporting on booking pipeline stages

## Domain Entities

### BTODashboardUser
Internal dashboard users (operations staff). Fields: email, hashed password, role.

### BookingDetail (`tb_1000_booking_details`)
The primary booking record created when a customer places an online vehicle order. Tracks the full lifecycle from payment through DMS push, SAP order status, frame number assignment, and delivery. Key fields:
- Customer info (name, phone, email)
- Vehicle config (model, variant, color, BTO packages, accessories)
- Payment (transaction ID, payment gateway, amount, status)
- DMS integration (internet enquiry ID, push status/response, booking number)
- SAP order tracking (frame number, bill-to-order number, order status)
- UTM/campaign attribution

### BookingStatus
A secondary booking record (legacy system) linked by BookingID. Tracks dealer-side status: DMS booking ID, invoice, insurance, document status, payment confirmations, and dealer correspondence.

### Correspondence
Communication logs (SMS/email) sent to customers or dealers, with request/response payloads and status.

### SMSPushDetail (`tb_151_SMSPush_Details`)
Detailed SMS delivery records including template ID, message ID, and carrier response.

### SAPStatusUpdateLog (`tb_1014_SAPOrderStatus_API_Log`)
Audit log of SAP order status updates received via API — tracks order number, frame number, status transitions, and any errors.

## Integrations

| System | Purpose |
|--------|---------|
| **SQL Server** | Primary data store (via Prisma ORM) |
| **DMS (Dealer Management System)** | Bookings are pushed to DMS; DMS booking IDs and statuses flow back |
| **SAP** | Order lifecycle updates (created → confirmed → manufactured → packed → dispatched) |
| **Payment Gateway (CCAvenue/ICICI)** | Payment processing; transaction IDs and payout references stored |
| **iQube** | Connected services / vehicle delivery data push |
| **SMS Gateway** | Customer and dealer notifications |

## Business Rules

### Order Lifecycle Stages
1. **Order Received** — booking placed, payment captured
2. **Full Payment Received** (Order Created in SAP) — full payment marked
3. **Order Confirmed** — SAP confirms the order
4. **Order Manufactured** — vehicle built
5. **Order Packed** — ready for dispatch
6. **Order Dispatched** — in transit to dealer

### Key Rules
- Only BTO bookings (`isBTO = true`) are surfaced in this dashboard
- Bookings are filtered by date range using IST offset (UTC+5:30)
- A booking is considered "pushed to DMS" when `internetenquiryid` is not null
- A booking is considered cancelled when `dms_cancel_status` is not null
- Invoice/insurance status is determined by joining BookingStatus with BookingDetail on TransactionId
- DMS push success is validated by `dms_post_response in ('Sucess', 'Success')` (note: legacy typo "Sucess" is intentional)
- JWT tokens expire after 480 minutes (8 hours)
- Passwords are hashed with Argon2
- All booking and report endpoints require JWT authentication
- Duplicate email registration is rejected with a conflict error



## Code Structure


# BTO Dashboard API — Project Structure

## Directory Layout

```
bto_api/
├── prisma/
│   └── schema.prisma          # Database schema (SQL Server) — all domain models defined here
├── src/
│   ├── main.ts                # App bootstrap: validation pipe, CORS, Swagger, port binding
│   ├── app.module.ts          # Root module — imports Auth, Booking, Report, Prisma, Winston
│   ├── auth/                  # Authentication module
│   │   ├── auth.module.ts     # Registers JwtModule, AuthService, JwtStrategy
│   │   ├── auth.controller.ts # POST /auth/signin, POST /auth/signup
│   │   ├── auth.service.ts    # Password hashing (Argon2), JWT token generation
│   │   ├── dto/               # SignInDto, SignUpDto, TokenDto
│   │   ├── guard/             # JwtGuard — reusable auth guard for protected routes
│   │   └── strategy/          # JwtStrategy — validates Bearer token, loads user from DB
│   ├── booking/               # Booking module
│   │   ├── booking.module.ts  # Registers BookingService
│   │   ├── booking.controller.ts  # GET /api/bookings, GET /api/bookinginfo (JWT-protected)
│   │   ├── booking.service.ts     # Booking search, order lifecycle info retrieval
│   │   └── dto/               # BookingRequestDto, BookingResponseDto, BookingInfoRequest/Response
│   ├── report/                # Report module
│   │   ├── report.module.ts   # Registers ReportService
│   │   ├── report.controller.ts  # GET /reports (JWT-protected)
│   │   ├── report.service.ts     # Aggregated booking pipeline counts by date range
│   │   └── dto/               # ReportDto (input), ReportResponseDto (output)
│   ├── prisma/                # Database access layer
│   │   ├── prisma.module.ts   # Global module — exports PrismaService to all modules
│   │   └── prisma.service.ts  # Extends PrismaClient, handles disconnect on module destroy
│   └── utils/                 # Shared constants and helpers
│       ├── constants.ts       # OrderStatus enum, Endpoints enum, ExceptionMessage, Logging, IST offset
│       └── index.ts           # Barrel export
├── test/
│   ├── app.e2e-spec.ts        # E2E test scaffold
│   └── jest-e2e.json          # E2E Jest config
├── package.json               # Dependencies, scripts, Jest config
├── tsconfig.json              # TypeScript config (CommonJS, ES2022 target, path aliases)
├── tsconfig.build.json        # Build-specific TS config
├── nest-cli.json              # NestJS CLI config
├── .eslintrc.js               # ESLint + Prettier integration
└── .prettierrc                # Prettier rules (single quotes, trailing commas, 100 width)
```

## Module Dependencies

```
AppModule
├── AuthModule        → JwtModule, PrismaService (via global PrismaModule)
├── BookingModule     → PrismaService (via global PrismaModule)
├── ReportModule      → PrismaService (via global PrismaModule)
├── PrismaModule      → @Global, exports PrismaService to all modules
└── WinstonModule     → Console + DailyRotateFile transports (injected via WINSTON_MODULE_PROVIDER)
```

## Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **NestJS framework** | Structured module system, DI, decorators for routes/guards/pipes |
| **Prisma ORM with SQL Server** | Type-safe database access against an existing legacy SQL Server schema |
| **Global PrismaModule** | Single shared database connection across all modules without re-importing |
| **JWT authentication (Passport)** | Stateless auth; tokens issued on signin, validated via JwtStrategy |
| **class-validator + ValidationPipe (whitelist)** | Auto-strips unknown fields, validates DTOs at controller boundary |
| **Winston with DailyRotateFile** | Structured JSON logging with automatic daily rotation and compression |
| **Raw SQL ($executeRaw) for complex joins** | Used in reports where Prisma's query builder can't express cross-table joins efficiently |
| **Path aliases (`@/*`)** | Cleaner imports from project root (e.g., `@/src/utils`) |
| **Swagger (OpenAPI)** | Auto-generated API docs at `/api-doc`, secured with X-API-KEY header |
| **CORS with allowlist** | Origins controlled via `CORS_ALLOWED_ORIGINS` env var |
| **No ORM migrations checked in** | Schema maps to an existing production database; Prisma introspects rather than migrates |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/signin` | None | Authenticate and receive JWT |
| POST | `/auth/signup` | None | Register new dashboard user |
| GET | `/api/bookings` | JWT | Search bookings by date, customer, dealer, transaction |
| GET | `/api/bookinginfo` | JWT | Get order lifecycle stages for a specific frame/order number |
| GET | `/reports` | JWT | Aggregated booking pipeline report by date range |



## Tech Stack & Dependencies


# BTO Dashboard API — Technical Reference

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Node.js | — |
| Language | TypeScript | ^5.1 |
| Framework | NestJS | ^10.0 |
| ORM | Prisma | ^5.8 |
| Database | SQL Server | — |
| Auth | Passport + passport-jwt | ^0.7 / ^4.0 |
| Token | @nestjs/jwt | ^10.2 |
| Hashing | Argon2 | ^0.31 |
| Validation | class-validator + class-transformer | ^0.14 / ^0.5 |
| Logging | Winston + nest-winston + winston-daily-rotate-file | ^3.11 / ^1.9 / ^4.7 |
| API Docs | @nestjs/swagger | ^7.2 |
| Config | dotenv | ^16.4 |
| Testing | Jest + ts-jest + Pactum + Supertest | ^29 / ^3.6 / ^6.3 |
| Linting | ESLint + Prettier | ^8 / ^3 |

## Coding Conventions

### File Naming
- Modules: `<feature>.module.ts`
- Controllers: `<feature>.controller.ts`
- Services: `<feature>.service.ts`
- DTOs: `<name>.dto.ts` inside a `dto/` subfolder with barrel `index.ts`
- Guards: `<name>.guard.ts` inside a `guard/` subfolder
- Strategies: `<name>.strategy.ts` inside a `strategy/` subfolder

### Code Style (enforced by ESLint + Prettier)
- Single quotes
- Trailing commas (all)
- Print width: 100 characters
- Tab width: 2 spaces
- No explicit return types enforced (`explicit-function-return-type: off`)
- No strict null checks (`strictNullChecks: false`)
- `@typescript-eslint/no-explicit-any: off`

### Import Conventions
- Path alias `@/*` maps to project root (e.g., `@/src/utils`)
- Relative imports used for intra-module references (e.g., `'./dto'`)
- Absolute-style imports for cross-module (e.g., `'src/prisma/prisma.service'`)

### DTO Patterns
- Request DTOs use `class-validator` decorators (`@IsString`, `@IsNotEmpty`, `@IsEmail`)
- Some request DTOs are plain interfaces (e.g., `BookingRequestDto`) — no runtime validation
- Response DTOs are classes with validator decorators for documentation purposes
- DTOs are exported via barrel `index.ts` files

### Constants
- All string constants centralized in `src/utils/constants.ts`
- Enums used for: `OrderStatus`, `Endpoints`, `ExceptionMessage`, `Logging`
- IST offset exported as a numeric constant

## Patterns

### Authentication Flow
1. User calls `POST /auth/signin` with email + password
2. Service looks up user by email, verifies password with Argon2
3. On success, returns a signed JWT (480min expiry, secret from `JWT_SECRET` env var)
4. Protected routes use `@UseGuards(JwtGuard)` at controller level
5. JwtStrategy extracts token from Authorization Bearer header, validates, and attaches user to request

### Service Layer
- Services are `@Injectable()` and receive `PrismaService` via constructor injection
- Business logic lives in services; controllers handle HTTP concerns and logging
- Services throw NestJS HTTP exceptions (`ForbiddenException`, `NotFoundException`)

### Database Access
- PrismaService is a thin wrapper extending `PrismaClient`
- Registered as a `@Global()` module — no need to import PrismaModule in feature modules
- Disconnects on module destroy (`OnModuleDestroy`)
- Complex cross-table queries use `$executeRaw` with template literals (parameterized)
- Date filtering applies IST offset manually before querying

### Logging
- Winston injected via `@Inject(WINSTON_MODULE_PROVIDER)`
- Structured JSON format with timestamps
- Log levels: `info` for incoming requests, `error` for exceptions
- Daily rotating file output (`logs/cbmodule-<DATE>.log`), max 50MB, zipped archives
- Console transport for development

## Error Handling

- **Controller level**: try/catch wraps service calls; errors are logged then re-thrown
- **Prisma errors**: `PrismaClientKnownRequestError` caught for specific codes (e.g., P2002 = unique constraint → 409 Conflict)
- **Auth errors**: `ForbiddenException` (401-equivalent) for invalid credentials
- **Not found**: `NotFoundException` thrown when no bookings match query
- **Validation**: Global `ValidationPipe` with `whitelist: true` strips unknown fields and returns 400 for invalid input
- **No global exception filter** — relies on NestJS default exception handling

## Testing

- **Unit tests**: Jest with ts-jest, ESM mode (`useESM: true`)
- **E2E tests**: Pactum + Supertest, separate config in `test/jest-e2e.json`
- **Test file pattern**: `*.spec.ts` (unit), `*.e2e-spec.ts` (integration)
- **Coverage**: collected from all `.ts`/`.js` files, output to `../coverage`
- **Run**: `npm test` (unit), `npm run test:e2e` (e2e)

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQL Server connection string (used by Prisma) |
| `JWT_SECRET` | Secret key for signing/verifying JWT tokens |
| `PORT` | Server listen port |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins |

## Build & Deployment

- **Build**: `npm run build` → NestJS compile → copies `package.json` to `dist/` → installs production deps in `dist/`
- **Start (prod)**: `node dist/main`
- **Start (dev)**: `nest start --watch`
- **Output**: `dist/` directory with compiled JS + production `node_modules`
- **Swagger docs**: available at `/api-doc` in all environments

