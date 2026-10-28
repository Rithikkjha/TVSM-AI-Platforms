---
service_id: bto-api
doc_type: hlc
last_reviewed: 2026-10-11
---

# bto-api — High-Level Code

## Application Overview
bto-api (`bto_api`) is a `backend-api` codebase; stacks nest, node; head `02b50b1ce5369b4f0d3ea2bff32fc0b395853397`.
Entry points: `src/main.ts`, `src/app.module.ts`.

## Module Summary
bto-api modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 5 endpoints, 0 outbound calls, 0 messaging, 1 data-access |

## Folder Structure
bto-api top-level folders (3 levels):

```
bto_api/
├── prisma/
├── src/
│   ├── auth/
│   │   ├── dto/
│   │   ├── guard/
│   │   ├── strategy/
│   ├── booking/
│   │   ├── dto/
│   ├── prisma/
│   ├── report/
│   │   ├── dto/
│   ├── utils/
├── test/
```

## Core Workflows in Code
bto-api workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### booking.controller
1. `src/booking/booking.controller.ts` receives 2 route(s), e.g. `GET /api/bookinginfo` → `BookingController.fetchBookingInfo`.
3. Module `.` data access via `prisma/schema.prisma:6`.

### auth.controller
1. `src/auth/auth.controller.ts` receives 2 route(s), e.g. `POST /auth/signin` → `AuthController.signin`.
3. Module `.` data access via `prisma/schema.prisma:6`.

### report.controller
1. `src/report/report.controller.ts` receives 1 route(s), e.g. `GET /reports` → `ReportController.fetchReport`.
3. Module `.` data access via `prisma/schema.prisma:6`.

## Integration Clients
bto-api outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| data store (db) | `prisma/schema.prisma:6` | Unknown |

## Cross-Cutting Concerns
bto-api cross-cutting code:
- Auth: `src/auth/auth.module.ts:5` (JwtStrategy), `src/auth/guard/jwt.guard.ts:1` (AuthGuard), `src/auth/strategy/jwt.strategy.ts:8` (JwtStrategy), `src/booking/booking.controller.ts:23` (@UseGuards), `src/report/report.controller.ts:9` (@UseGuards)
- Error handling: none found
- Validation: 31 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
bto-api build/test commands from manifests:
- `package.json` scripts: `npm run build`, `npm run start`, `npm run start:dev`, `npm run start:prod`, `npm run lint`, `npm run test`, `npm run test:cov`, `npm run test:e2e`
- CI pipelines: none found
