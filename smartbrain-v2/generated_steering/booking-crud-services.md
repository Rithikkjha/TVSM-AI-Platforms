# booking-crud-services

*Auto-generated from static code analysis*

## Service Overview
- **Language:** Node.js (nestjs@11.1.17)
- **Contacts:** psnarkhedetvs, paras0602, Dinesh-sb-28, DineshSB28, Nivetha-Nehru
- **Purpose:** The Booking Service serves as a centralized system for managing bookings across various platforms utilized by TVS Motor Company. It integrates with TVS-managed services (such as dealer systems and the company website) and third-party applications, ensuring a cohesive booking process. Previously, bookings were handled independently by each system; this service consolidates all bookings through a single interface.
- **Domain:** accepted, access, action, active, addition, additional, address, algorithm, allocated, allocation

## Code Structure
```
📄 AST_Website_Corporate_booking_crud_services_DEV_Pipeline.yml
📄 Dockerfile
📄 README.md
📄 nest-cli.json
📄 package.json
📁 src/
📄 src/app.module.ts
📁 src/bookings/
📄 src/bookings/bookings.module.ts
📁 src/bookings/controllers/
📁 src/bookings/dto/
📁 src/bookings/services/
📁 src/cloud-conductor/
📄 src/cloud-conductor/cloud-conductor.module.ts
📁 src/cloud-conductor/services/
📁 src/database/
📁 src/database/entities/
📁 src/logger/
📄 src/logger/logging.module.ts
📄 src/logger/logging.service.spec.ts
📄 src/logger/logging.service.ts
📄 src/main.ts
📄 src/otel-propagation.ts
📄 src/otel.ts
📄 src/schema.gql
📁 src/shared/
📁 src/shared/constants/
📁 src/shared/exceptions/
📄 src/shared/utils.spec.ts
📄 src/shared/utils.ts
📄 swagger.json
📁 test/
📄 test/app.e2e-spec.ts
📄 test/jest-e2e.json
📄 tsconfig.json
```

## API Endpoints
| Method | Path | Description | File |
|--------|------|-------------|------|
| POST | /bookings | Create a booking | swagger.json |
| PUT | /bookings | Update a booking | swagger.json |
| POST | /bookings/bto_status | Update a booking | swagger.json |
| POST | /bookings/search | Search for bookings | swagger.json |
| PUT | /bookings/cancel | Cancel a booking | swagger.json |
| POST | /bookings/fnfrefund | Process FNF refund for a booking | swagger.json |
| POST | /bookings/testbookingtopic | Testing service bus publisher | swagger.json |
| POST | /bookings/refundstatus | Update refund status | swagger.json |
| POST | /bookings/juspayrefundstatus | Update JusPay refund status | swagger.json |
| GET | /bookings/health | Health check endpoint | swagger.json |

## Dependencies (Outbound)
### HTTP Calls
| Target Service | URL/Variable | Confidence | File |
|---|---|---|---|
| unknown | `cpgApiUrl` | 🔴 low | src/bookings/services/cpg.service.ts:77 |
| unknown | `cpgTokenUrl` | 🔴 low | src/bookings/services/cpg.service.ts:118 |
| unknown | `ccaUrl` | 🔴 low | src/bookings/services/booking-refund/ccavenue-refund.service.ts:69 |
| unknown | `LS_URL` | 🔴 low | src/bookings/services/lead-service/lead.service.ts:40 |
| unknown | `TOKEN_GENERATION_URL` | 🔴 low | src/bookings/services/lead-service/lead.service.ts:68 |

### Service Bus — Publishes
| Topic | Confidence | File |
|---|---|---|
| topic | 🟡 medium | src/cloud-conductor/services/publisher/topic-publisher.service.ts:15 |
| b-t-o-status-update | 🟡 medium | src/bookings/services/publisher/booking-modification/bto-status-update-publisher.service.ts:13 |
| booking-creation | 🟡 medium | src/bookings/services/publisher/booking-creation/booking-creation-publisher.service.ts:22 |
| d-m-s-integration | 🟡 medium | src/bookings/services/publisher/dms-integration/dms-integration.publisher.service.ts:19 |
| booking-refund | 🟡 medium | src/bookings/services/publisher/booking-refund/booking-refund.publisher.service.ts:22 |
| booking-refund-status-update | 🟡 medium | src/bookings/services/publisher/booking-refund-status-update/booking-refund-status-update.publisher.service.ts:21 |
| booking-modification | 🟡 medium | src/bookings/services/publisher/booking-modification/booking-modification-publisher.service.ts:16 |
| booking-cancellation | 🟡 medium | src/bookings/services/publisher/booking-cancellation/booking-cancellation-publisher.service.ts:26 |
| a-t-p-handler | 🟡 medium | src/bookings/services/publisher/atp-handler/atp-handler-publisher.service.ts:12 |

### Service Bus — Subscribes
| Topic | Source Service | Confidence | File |
|---|---|---|---|
| topicName | unknown | 🟢 high | src/cloud-conductor/services/listener/dms-topic-listener.service.ts:47 |

## Databases
| Type | Name | File |
|---|---|---|
| mssql |  | package.json — mssql/tedious dependency |
| redis |  | package.json — ioredis/redis dependency |

## Recent Activity
- **Last commit:** 2026-05-04 by Nivetha-Nehru — "Feature/spd dealer test coverage (#409)"
- **Active contributors (30d):** Nivetha-Nehru, sureshkannantvs
- **Commit frequency:** ~1/week

## Architecture Notes
This service is structured using NestJS, which promotes modular development. The separation of concerns is evident with distinct modules for bookings, cloud conductor services, and logging, enhancing maintainability and scalability.