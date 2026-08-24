# Price-Engine-MicroService-Backend


## Product Context


# Price Engine Microservice — Product Context

## What This Service Does

This is the **Price Engine** backend microservice for TVS Motor Company. It manages vehicle pricing for the Indian domestic two-wheeler market (ICE and EV). The service:

1. Ingests vehicle model and pricing data from an upstream Master Data Platform (MDP) via Azure Service Bus
2. Allows configuration of price components (taxes, subsidies, registration fees, etc.) per region
3. Calculates product-level pricing by applying components to ex-showroom prices
4. Generates and publishes On-Road Prices (ORP) per model per region (state/city)
5. Exposes integration APIs for downstream consumers to fetch published on-road prices

## Domain Entities

### Vehicle Model
- Sourced from SAP via Service Bus
- Fields: sapModelId, modelName, modelDescription, market, industry, category, brand, engineType (ICE/EV), availabilityStatus
- Includes vehicle part (partId, color) and specifications (engineCapacity, power, weight)
- Collection: `vehicleModels`

### Price Component
- A reusable pricing element definition (e.g., "Road Tax", "Insurance", "FAME Subsidy")
- Fields: componentName, componentKey, engineType, market, industry, isDeductible
- Tracks lastUsedDate for sorting
- Collection: `price_components`

### Product Price Component
- The association of a price component to specific vehicle models in specific regions
- Fields: engineType, modelId, partId, modelName, region (country/state/city), exShowroomPrice, productSpecification, applicablePriceComponents[]
- Each applicable component has: calculatedValue, calculationMethodType, calculationDetails, isActive, slabs
- Collection: `product_price_components`

### On-Road Price (ORP)
- The final consumer-facing price for a vehicle in a specific region
- Fields: modelId, engineType, region, exShowroomPrice, onRoadPrice, isORPGenerated, isORPActive, applicablePriceComponentsForORPGeneration[]
- Collection: `on_road_prices`

### Region
- Indian states and cities with codes
- Collections: `states`, `cities`

### Dead Letter Messages
- Failed Service Bus messages stored for debugging
- Collection: `dead_letter_messages`

## Integrations

### Inbound — Azure Service Bus (MDP)
- **Product Topic**: Receives vehicle model create/update events. Filters by industry (TWO_WHEELER), market (DOMESTIC), engineType (ICE/EV). Validates specifications for ICE vehicles.
- **Price Topic**: Receives vehicle price create/update events. Updates ex-showroom prices and recalculates ORP.
- Both use session-based receivers with peek-lock mode and batch processing via temp collections.

### Outbound — Integration API
- `GET /on-road-prices/vehicles/engineType/:engineType` — Paginated, cached endpoint for downstream services to fetch published on-road prices.

### Infrastructure
- **MongoDB Atlas** — Primary data store
- **Azure Cache for Redis** — Caching layer for integration API responses
- **Site24x7 (apminsight)** — Application performance monitoring

## Business Rules

### Price Calculation Methods
1. **CONSTANT** — Fixed value (price amount) or percentage of ex-showroom price
2. **PARAMETER** — Slab-based: value determined by vehicle weight, price, or engine capacity falling within min/max ranges with configurable operators (>, >=, <, <=)
3. **CUSTOM** — Equation-based: combines calculated values of other components using BODMAS arithmetic (+, -, *, /, parentheses)

### ORP Generation Rules
- On-Road Price = Ex-Showroom Price + Σ(additive components) - Σ(deductible components)
- Only **active** components contribute to ORP calculation
- A deductible component's calculated value **cannot exceed** the ex-showroom price
- Division by zero in custom calculations throws an error
- When a component is published (activated), dependent custom components are deactivated and must be recalculated

### Data Ingestion Rules
- Only TWO_WHEELER industry, DOMESTIC market vehicles are processed
- ICE vehicles must have non-zero engineCapacity, power, and weight — otherwise sent to dead letter queue
- Redis cache is flushed at the start of every Service Bus message batch processing
- Vehicle launch status (`isNewLaunch`) is set to false when ORP is first generated

### Component Association
- Components can be **Global** (applies to all models in a region) or **SKU-specific** (applies to selected models)
- A component cannot be both global and SKU-specific simultaneously
- Duplicate component names for the same model+region are rejected

### ORP Publishing
- Publishing ORP checks that all price components for a region are active
- `isORPActive` is set per-region based on component active status



## Code Structure


# Price Engine Microservice — Project Structure

## Directory Layout

```
Price-Engine-MicroService-Backend/
├── src/                              # Application source code
│   ├── server.ts                     # Entry point — bootstraps Express, DB, Redis, Service Bus listeners
│   ├── config/                       # Environment configuration
│   │   ├── db-config.ts              # MongoDB connection string builder
│   │   ├── redis-config.ts           # Redis client factory (env-aware: local/dev/uat/prod)
│   │   ├── host.ts                   # Server host config
│   │   ├── port.ts                   # Server port config
│   │   └── index.ts                  # Barrel export
│   ├── constants/                    # Application constants and enums
│   │   ├── base-data-constants.ts    # Domain enums (engine types, markets, industries, collections)
│   │   ├── error-constants.ts        # All error message strings
│   │   ├── http-status-codes.ts      # HTTP status code enum
│   │   ├── orp-constants.ts          # On-road price specific constants
│   │   ├── price-component-constants.ts  # Calculation types, operators, units of measure
│   │   ├── logger-constants.ts       # Logger configuration
│   │   └── index.ts                  # Barrel export
│   ├── routes/                       # Express router definitions
│   │   └── api/                      # Route files grouped by domain
│   │       ├── price-component-routes.ts
│   │       ├── product-price-components-routes.ts
│   │       ├── on-road-price-routes.ts
│   │       ├── product-routes.ts
│   │       ├── region-routes.ts
│   │       └── cache-routes.ts
│   ├── handlers/                     # Request handlers (controllers)
│   │   ├── on-road-price-handler.ts
│   │   ├── price-component-handler.ts
│   │   ├── product-price-components-handler.ts
│   │   ├── product-handler.ts
│   │   ├── region-handler.ts
│   │   ├── cache-handler.ts
│   │   └── validators/               # Input validation logic per handler
│   ├── services/                     # Business logic layer
│   │   ├── on-road-price-service.ts  # ORP generation, editing, publishing
│   │   ├── on-road-price-cache-service.ts  # Cached ORP queries
│   │   ├── price-component-service.ts     # Price component CRUD
│   │   ├── product-price-components-service.ts  # Product price calculation engine
│   │   ├── product-service.ts        # Vehicle model queries
│   │   ├── product-service-bus-implementer-service.ts  # Product message consumer
│   │   ├── price-service-bus-implementer-service.ts    # Price message consumer
│   │   ├── insert-vehicle-models.ts  # Processes temp product messages into models
│   │   ├── update-product-price.ts   # Processes temp price messages into prices
│   │   ├── cache-service.ts          # Redis cache abstraction (get/set/flush)
│   │   └── region-service.ts         # State/city queries
│   ├── models/                       # Thin model wrappers (re-exports from schema)
│   │   └── mongodb/
│   ├── db/                           # Database layer
│   │   └── mongodb/
│   │       ├── db.ts                 # Mongoose connection instance
│   │       ├── schema/               # Mongoose schemas with static query methods
│   │       │   ├── vehicle-model-schema.ts
│   │       │   ├── price-components-schema.ts
│   │       │   ├── product-price-components-schema.ts
│   │       │   ├── on-road-price-schema.ts
│   │       │   ├── states-schema.ts
│   │       │   ├── cities-schema.ts
│   │       │   ├── dead-letter-messages-schema.ts
│   │       │   └── service-bus-message-db-implementor.ts
│   │       └── reusable-queries/     # Extracted MongoDB aggregation pipelines
│   │           ├── on-road-price-queries/
│   │           └── product-price-queries/
│   ├── middleware/                   # Express middleware
│   │   ├── error-middleware.ts       # Error logger + responder + 404 handler
│   │   └── response-time-middleware.ts
│   ├── rest/                         # HTTP client utilities
│   │   └── rest-client.ts            # Axios wrapper
│   └── utils/                        # Shared utilities
│       ├── classes/                  # AppCustomError
│       ├── decorators/               # @handleTryCatchError, @handleResponseError
│       ├── functions/                # Logger (Winston), utility functions
│       ├── interface/                # TypeScript interfaces
│       ├── reshape-objects/          # Data transformation (calculator, ORP reshape)
│       ├── service-bus-implementors/ # ServiceBusConnectionImplementor class
│       └── server-down-utility.ts    # Graceful shutdown (SIGINT/SIGTERM)
├── sonar-exclusion-function/         # One-time scripts excluded from SonarQube
│   ├── scripts/                      # Data validation and master data insertion
│   ├── service-bus/                  # Migration scripts for initial data seeding
│   └── swagger.ts                    # Swagger documentation (standalone)
├── data-insertion-scripts/           # CSV data files and shell scripts for DB seeding
├── Dockerfile                        # Multi-stage build (Node 20 Alpine)
├── package.json                      # Dependencies and scripts
├── jest.config.js                    # Jest + ts-jest configuration
├── .prettierrc                       # Code formatting rules
├── .husky/pre-commit                 # Pre-commit hook (lint-staged + prettier)
├── pe-ms-be-prod-ci.yml             # Azure DevOps CI pipeline
├── pe-ms-be-prod-cd.yml             # Azure DevOps CD pipeline
└── AST_MDP_Price-Engine-MicroService-Backend_release_Pipeline.yml  # Security scanning pipeline
```

## Module Dependencies

```
Routes → Handlers → Services → Models/Schemas → MongoDB
                  ↘ Validators
Services → Utils (reshape-objects, decorators, functions)
Services → Constants
Services ↔ Services (e.g., productPriceComponentsService ↔ onRoadPriceService)
Service Bus Implementors → Services (insertVehicleModels, updatePriceData)
Service Bus Implementors → Utils (ServiceBusConnectionImplementor)
Cache Service → Redis Config
```

## Architectural Decisions

### Layered Architecture
Handler → Service → Schema pattern. Handlers deal with HTTP concerns (request/response), services contain business logic, schemas encapsulate database operations via Mongoose static methods.

### Repository Pattern via Mongoose Statics
Database queries are defined as static methods on Mongoose schemas rather than in a separate repository layer. Complex queries use extracted aggregation pipelines in `reusable-queries/`.

### Singleton Service Instances
All services and handlers are instantiated as singletons at module level and exported as default. No dependency injection container — dependencies are imported directly.

### Decorator-Based Error Handling
TypeScript decorators (`@handleTryCatchError`, `@handleResponseError`) wrap methods with try/catch, eliminating repetitive error handling boilerplate across the codebase.

### Event-Driven Data Ingestion
Vehicle and price data flows in via Azure Service Bus sessions. Messages are buffered in memory during a session, batch-stored to temp collections, then processed. This decouples ingestion from processing and handles backpressure.

### Cache-Aside Pattern
Redis caching uses a `getOrSet` pattern — check cache first, fetch from DB on miss, store result. Cache is invalidated (flushed) when new data arrives via Service Bus.

### Barrel Exports
Every directory has an `index.ts` that re-exports its contents, keeping import paths clean and centralized.



## Tech Stack & Dependencies


# Price Engine Microservice — Technical Reference

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Node.js | 20 (Alpine) |
| Language | TypeScript | 5.3 |
| Framework | Express | 4.18 |
| Database | MongoDB (Mongoose) | Mongoose 8.9 |
| Cache | Redis | redis 5.10 |
| Message Bus | Azure Service Bus | @azure/service-bus 7.9 |
| Logging | Winston | 3.10 |
| APM | apminsight (Site24x7) | 5.1 |
| HTTP Client | Axios | 1.7 |
| Testing | Jest + ts-jest + supertest + mongodb-memory-server | Jest 29 |
| Formatting | Prettier | 3.0 |
| Git Hooks | Husky + lint-staged | Husky 8 |
| CI/CD | Azure DevOps Pipelines | — |
| Hosting | Azure App Service (Linux) | — |

## Coding Conventions

### Formatting (Prettier)
- Print width: 140 characters
- Tab width: 2 spaces (no tabs)
- Semicolons: yes
- Single quotes: yes
- Trailing commas: all
- Arrow parens: avoid (omit when single param)
- End of line: LF
- Bracket spacing: yes

### Naming
- Files: kebab-case (`on-road-price-service.ts`)
- Classes: PascalCase (`OnRoadPriceService`)
- Variables/functions: camelCase (`generateOnRoadPrice`)
- Constants: UPPER_SNAKE_CASE for enum-like objects (`ENGINE_TYPE_CONSTANTS`)
- Interfaces: PascalCase with `Interface` suffix (`ProductPriceComponentsInterface`)
- Collections: snake_case (`product_price_components`)

### Module Organization
- One class per file, instantiated as singleton, exported as default
- Barrel exports (`index.ts`) in every directory
- Co-located tests in `test/` subdirectories within each module
- Mocks in `test/mock/` subdirectories

### TypeScript
- Strict mode not enforced globally but interfaces are used extensively
- Experimental decorators enabled (`experimentalDecorators: true`)
- Target: ES2016, Module: CommonJS
- Path aliases not used — relative imports throughout

## Patterns

### Error Handling

**Custom Error Class:**
```typescript
class AppCustomError extends Error {
  statusCode: number;
  constructor(statusCode: number, errorMessage: string) { ... }
}
```

**Decorator Pattern:**
- `@errorDecorator.handleTryCatchError` — For service methods. Wraps in try/catch, logs result on success, logs error on failure, rethrows.
- `@errorDecorator.handleResponseError` — For handler methods. Catches errors and sends HTTP error response with appropriate status code.

**Error Middleware:**
- `errorLogger` — Logs error details via Winston
- `errorResponder` — Sends JSON error response `{ message: string }`
- `routeNotFound` — Returns 404 for unmatched routes

**Convention:** Throw `AppCustomError` with appropriate HTTP status code from services. Decorators handle the rest.

### Caching

**BaseCacheService** provides:
- `put(key, data)` — Serialize and store in Redis
- `getStringFromCache<T>(key)` — Retrieve and deserialize
- `getOrSet<T>(key, fetcher)` — Cache-aside pattern
- `flushAll()` — Invalidate entire cache (used on data ingestion)
- `isHealthy()` — Redis health check via ping

**OnRoadPriceCacheService** extends BaseCacheService with domain-specific key building (`engine:X:model:Y:state:Z:page:N:size:M`).

### Service Bus Processing

1. `ServiceBusConnectionImplementor` manages connection lifecycle (connect, receive sessions, close)
2. Session-based receivers with 100s timeout for session acceptance
3. Messages processed one at a time (`maxConcurrentCalls: 1`)
4. Inactivity timeout (10s) closes session when no more messages arrive
5. Messages buffered in memory, then batch-inserted to temp collection
6. After session closes, batch is processed (insert models or update prices)
7. Graceful shutdown via AbortController listening to SIGINT/SIGTERM

### Data Transformation
- `ReshapeCalculator` — Applies calculation methods (constant/parameter/custom) to produce calculated values
- `ReshapeOnRoadPrice` — Groups price components by region key, computes ORP totals
- Region key format: `Country-STATE-STATECODE-CITY-CITYCODE`

### Validation
- Input validation in `handlers/validators/` directory
- Validators throw `AppCustomError` with 400 status on invalid input
- No external validation library — manual checks with descriptive error messages from constants

## Testing

### Configuration
```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coveragePathIgnorePatterns: ['src/services/test/mock/'],
};
```

### Approach
- **Unit tests**: Service and utility logic with mocked dependencies
- **Integration tests**: Handler tests using supertest against Express app with mongodb-memory-server
- **Test location**: `<module>/test/<module-name>.test.ts`
- **Mocks**: `<module>/test/mock/` directories with mock data objects
- **Coverage**: Collected in cobertura format for CI reporting

### Commands
- `npm test` — Run all tests with coverage
- `npm run test-coverage` — Same with explicit coverage flag
- `npm run coverage` — Coverage in cobertura format (for CI)

## Deployment

### Docker (Multi-stage)
1. **Build stage**: Node 20 Alpine, install all deps, compile TypeScript
2. **Runtime stage**: Node 20 Alpine, copy node_modules + dist, non-root user (`appuser`), expose 8080

### CI Pipeline (`pe-ms-be-prod-ci.yml`)
- Triggered by upstream release pipeline completion on `release` branch
- Steps: checkout → Node 18 → npm install → npm build → archive → publish artifact

### CD Pipeline (`pe-ms-be-prod-cd.yml`)
- Triggered by CI pipeline success on `uat` branch
- Manual approval gate (staging environment)
- Downloads artifact → deploys to Azure App Service (`tvsmazpqcappprd01-PriceEngine-api`)

### Security Pipeline (`AST_MDP_...release_Pipeline.yml`)
- Gitleaks (secret scanning)
- SCA/SBOM (dependency analysis)
- Checkmarx SAST (static analysis)
- API Security scanning
- DAST (dynamic analysis)
- Tenable (vulnerability scanning)

### Environment Configuration
- `NODE_ENV`: local | test | dev | uat | prod
- Redis: localhost:6379 (local), TLS on port 6380 (dev/uat/prod)
- MongoDB: Atlas connection string built from env vars
- Service Bus: Separate connection strings for product and price topics

### Scripts
- `npm run dev` — Development with nodemon + ts-node
- `npm run build` — TypeScript compilation
- `npm start` — Run compiled output (`dist/src/server.js`)
- `npm test` — Jest test suite

