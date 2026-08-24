# Price-Microservice-Backend-for-Frontend-Layer


## Product Context


# Product Context — Price Microservice BFF Layer

## What This Service Does

This is a Backend-for-Frontend (BFF) layer that sits between frontend clients and a downstream Price Microservice. It proxies, validates, reshapes, paginates, and filters pricing data before returning it to the frontend. The domain is **vehicle pricing management** for a two-wheeler manufacturer (TVS Motors), handling On-Road Price (ORP) calculations across Indian states and cities.

## Domain Entities

### On-Road Price (ORP)
The central entity. Represents the total price a customer pays for a vehicle in a specific region.
- Composed of ex-showroom price + applicable price components (taxes, charges)
- Scoped to a specific vehicle model + region (state/city)
- Has lifecycle states: generated → active/inactive → published/archived
- Key fields: `modelId`, `modelName`, `engineType`, `region`, `onRoadPrice`, `exShowroomPrice`, `isORPActive`, `isORPGenerated`

### Price Component
Individual charges that contribute to the on-road price (e.g., Road Tax, Handling Charges).
- Has a calculation method: CONSTANT (fixed value), PARAMETER (slab-based), or CUSTOM (formula-based)
- Scoped by engine type (ICE or EV)
- Can be deductible or additive
- Key fields: `componentName`, `componentKey`, `componentId`, `calculatedValue`, `calculationMethodType`, `applicableSlab`, `isActive`

### Product Price Component
Links price components to specific vehicle models and regions.
- Associates components with models at state or city level
- Supports global vs region-specific components
- Key fields: `engineType`, `componentName`, `vehicleModels`, `componentDefinitions`, `isGlobal`

### Vehicle Model (Product)
A two-wheeler model in the catalog.
- Identified by `modelId`, `modelName`, `partId`
- Categorized by `engineType` (ICE or EV), `market` (DOMESTIC), `industry` (TWO_WHEELER)
- Has `brand`, `modelDescription`, `category`

### Region
Geographic scope for pricing.
- Hierarchy: Country → State → City
- Key fields: `country`, `stateName`/`state`, `stateCode`, `cityName`/`city`, `cityCode`
- Currently focused on India with state-level and city-level pricing

### Calculator
Defines how a price component value is computed.
- **CONSTANT**: Fixed value with unit of measure (price or percentage)
- **PARAMETER**: Slab-based with min/max ranges and operators
- **CUSTOM**: Formula-based with equation and calculation rules referencing other components

## Integrations

### Downstream: Price Microservice
- Base URL configured via `PRICE_MICROSERVICE_BASE_URL` env var (default: `http://0.0.0.0:8080`)
- Communication via REST (axios HTTP client)
- All downstream endpoints are mirrored with the same path structure
- Endpoints consumed:
  - `GET /price-components/:engineType` — component names
  - `POST /product-price-components` — create product-price component
  - `GET /product-price-components/custom/engineType/:engineType` — components for custom creation
  - `GET /product-price-components/:engineType/:componentId` — associated models and regions
  - `PUT /product-price-components/publish/:componentId` — publish component
  - `GET /products/vehicle/:engineType/models` — vehicle models
  - `GET /regions/:country/states` — state list
  - `GET /regions/cities` — city list
  - `POST /on-road-prices` — generate ORP
  - `PUT /on-road-prices/:modelId` — edit ORP
  - `GET /on-road-prices/:modelId` — get ORP by model
  - `GET /on-road-prices/products/:modelId` — get ORP components
  - `PUT /on-road-prices/publish/:modelId` — publish ORP
  - `GET /on-road-prices/models/:engineType` — models by engine type

### Upstream: Frontend Clients
- Serves REST API over Express on port 8001
- CORS enabled for cross-origin access
- JSON request/response format

### Monitoring: Site24x7 APM
- `apminsight` package initialized at server startup for application performance monitoring

## Business Rules

1. **Engine Type Validation**: Only `ICE` (Internal Combustion Engine) and `EV` (Electric Vehicle) are valid. Input is case-insensitive but normalized to uppercase.

2. **ORP Publish Logic**: When publishing an ORP, the system checks if ALL ORPs that have applicable price components are active (`isORPActive === true`). If yes, returns success. Otherwise returns "ORP not published for components which are not active".

3. **Region Grouping**: When fetching cities, the BFF groups cities by state, returning a structure of `{ country, stateName, stateCode, cities[] }` per state.

4. **Pagination**: The BFF performs manual pagination (not delegated to downstream) for:
   - ORP details by model (default: 10 rows/page, page 1)
   - Component associated models/regions (default: 10 rows/page, page 1)

5. **Filtering**:
   - ORP details can be filtered by `isActive` status
   - Vehicle models can be filtered by `isAvailable` (true/false)
   - Sort by `modifiedDate` with configurable sort order (ascending/descending, default descending)

6. **Data Reshaping**: The BFF transforms nested downstream responses into flattened, frontend-friendly structures with metadata (active/inactive counts, total count, component names list, pagination info).

7. **Empty State Handling**: When no data is found, services return empty arrays or structured empty responses with zero counts rather than errors.

8. **Country Validation**: Country parameter is required and validated as non-empty for region queries.

9. **Object ID Validation**: MongoDB ObjectIDs are validated with regex pattern `/^[0-9a-fA-F]{24}$/`.



## Code Structure


# Project Structure — Price Microservice BFF Layer

## Annotated Directory Layout

```
├── .env                          # Environment variables (port, host, downstream URL)
├── .husky/pre-commit             # Git hook: runs lint-staged (prettier) on commit
├── .prettierrc                   # Prettier config (140 width, single quotes, trailing commas)
├── azure-pipelines.yaml          # CI/CD: Azure DevOps pipeline (develop branch trigger)
├── jest.config.js                # Jest config: ts-jest preset, node environment, coverage
├── package.json                  # Dependencies, scripts, lint-staged config
├── sonar-exclusion-function/     # Files excluded from SonarQube analysis
│   └── swagger.ts                # Legacy swagger definition (not actively used)
│
└── src/
    ├── server.ts                 # Entry point: imports app and calls startServer()
    │
    ├── config/                   # Environment configuration readers
    │   ├── host.ts               # Reads SERVER_HOST_URL from env
    │   ├── port.ts               # Reads API_SERVER_PORT from env
    │   └── index.ts              # Barrel export
    │
    ├── constants/                # Application-wide constants
    │   ├── error-constants.ts    # Error message strings by domain (HTTP, common, region, product, price, ORP)
    │   ├── http-status-codes.ts  # HTTP status code numeric constants
    │   ├── logger-constants.ts   # Winston logging colors and levels
    │   ├── pagination-constants.ts # Default ROWS_PER_PAGE=10, PAGE_NUMBER=1
    │   ├── price-component-constants.ts # Calculation type enums (CONSTANT, PARAMETER, CUSTOM)
    │   ├── product-constants.ts  # Engine type enums (ICE, EV)
    │   └── index.ts              # Barrel export
    │
    ├── handlers/                 # Request handlers (controller layer)
    │   ├── on-road-price-handler.ts      # ORP endpoints handler
    │   ├── price-component-handler.ts    # Price component endpoints handler
    │   ├── product-handler.ts            # Product/vehicle model endpoints handler
    │   ├── product-price-components-handler.ts # Product-price component endpoints handler
    │   ├── region-handler.ts             # Region endpoints handler
    │   ├── index.ts                      # Barrel export
    │   ├── validators/                   # Input validation logic
    │   │   ├── common-validator.ts       # ObjectID and empty string validators
    │   │   ├── product-validator.ts      # Engine type validation (ICE/EV only)
    │   │   ├── index.ts                  # Barrel export
    │   │   └── test/                     # Validator unit tests
    │   └── test/                         # Handler unit tests
    │       ├── mock/                     # Shared mock request/response objects
    │       │   ├── request.ts            # Mock Express Request
    │       │   └── response.ts           # Mock Express Response with status()/json()
    │       ├── on-road-price-handler.test.ts
    │       ├── price-component-handler.test.ts
    │       ├── product-handler.test.ts
    │       └── region-handler.test.ts
    │
    ├── middleware/                # Express middleware
    │   ├── error-middleware.ts    # Error logger, error responder, 404 handler
    │   └── index.ts              # Barrel export
    │
    ├── routes/                   # Express route definitions
    │   ├── routes.ts             # Main app setup: Express init, CORS, route mounting, server listen
    │   └── api/                  # Individual route files
    │       ├── on-road-price-routes.ts         # /on-road-prices/*
    │       ├── price-component-route.ts        # /price-components/*
    │       ├── product-route.ts                # /products/*
    │       ├── product-price-components-route.ts # /product-price-components/*
    │       └── region-routes.ts                # /regions/*
    │
    ├── services/                 # Business logic layer
    │   ├── on-road-price-service.ts            # ORP business logic (publish validation, filtering)
    │   ├── price-component-service.ts          # Price component passthrough
    │   ├── product-service.ts                  # Product data passthrough
    │   ├── product-price-components-service.ts # Pagination, sorting, reshaping
    │   ├── region-service.ts                   # City grouping by state
    │   ├── index.ts                            # Barrel export
    │   └── test/                               # Service unit tests
    │
    ├── rest/                     # Downstream API communication layer
    │   ├── http/
    │   │   └── http.ts           # Axios wrapper (get, post, put) with JSON headers
    │   ├── API-directories/      # URL builders for downstream endpoints
    │   │   ├── on-road-price-apis.ts
    │   │   ├── price-component-apis.ts
    │   │   ├── product-apis.ts
    │   │   ├── product-price-component-apis.ts
    │   │   ├── region-api.ts
    │   │   └── index.ts
    │   ├── implementers/         # API client classes (one per domain)
    │   │   ├── on-road-price-implemeter.ts     # ORP API calls
    │   │   ├── price-implementer.ts            # Price component API calls
    │   │   ├── product-implementer.ts          # Product API calls
    │   │   ├── product-price-components-implementer.ts
    │   │   ├── region-implementer.ts           # Region API calls
    │   │   └── index.ts
    │   └── test/                 # Implementer unit tests
    │
    └── utils/                    # Shared utilities
        ├── classes/
        │   └── custom-error.ts   # AppCustomError extends Error with statusCode
        ├── decorators/
        │   └── error-decorators.ts # @handleTryCatchError, @handleResponseError decorators
        ├── functions/
        │   ├── logger.ts         # Winston logger instance
        │   └── utilFunctions.ts  # Query string builder (convertToQueryFormate)
        ├── interface/            # TypeScript interfaces
        │   ├── calculator.ts     # Calculator type definitions
        │   ├── on-road-price-interface.ts # ORP and payload interfaces
        │   ├── price-components.ts # PriceComponentsInterface
        │   └── product-price-components-interface.ts # Complex product-price types
        ├── reshape-objects/      # Data transformation utilities
        │   ├── reshape-on-road-price.ts # Flatten ORP response + pagination + counts
        │   └── reshape-product-price-components.ts # Group by component → state → city
        ├── test/                 # Utility unit tests
        └── index.ts              # Barrel export for all utils
```

## Module Dependencies (Data Flow)

```
Routes → Handlers → Validators (input validation)
                  → Services → Implementers → HTTP Client → Downstream API
                             → Reshape Objects (data transformation)
```

Each layer only depends on the layer directly below it. Cross-cutting concerns (error handling, logging) are injected via decorators.

## Architectural Decisions

1. **BFF Pattern**: This service exists solely to adapt the downstream Price Microservice API for frontend consumption. It adds validation, pagination, filtering, and data reshaping that the core service doesn't provide.

2. **Class-Based Singletons**: Every handler, service, implementer, and validator is a class instantiated once at module level and exported as a singleton. This provides consistent structure but no dependency injection.

3. **Decorator-Based Error Handling**: TypeScript decorators (`@handleResponseError` for handlers, `@handleTryCatchError` for services/implementers) wrap methods with try-catch logic, eliminating repetitive error handling code.

4. **Barrel Exports**: Every directory has an `index.ts` that re-exports its contents, enabling clean imports like `import { errorDecorator } from '../utils'`.

5. **URL Builders Separated from HTTP Calls**: API endpoint URLs are constructed in `API-directories/` files, separate from the implementer classes that make the actual HTTP calls. This makes URL logic testable independently.

6. **Manual Pagination in BFF**: Rather than relying on the downstream service for pagination, the BFF fetches full datasets and paginates in-memory. This gives the BFF control over sorting and filtering logic.

7. **No Database**: This service has no direct database access. All data comes from the downstream Price Microservice via HTTP.

8. **No Authentication/Authorization**: The BFF does not implement auth. It's expected to sit behind an API gateway or similar infrastructure that handles auth.

9. **Shared Mock Objects for Tests**: Handler tests share mock request/response objects defined in `test/mock/` directories, keeping test setup DRY.

10. **Environment-Based Configuration**: All external URLs and server settings come from environment variables loaded via dotenv, with no hardcoded values.



## Tech Stack & Dependencies


# Technical Reference — Price Microservice BFF Layer

## Tech Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Runtime | Node.js | 18.x |
| Language | TypeScript | 5.2 |
| Framework | Express | 4.18 |
| HTTP Client | Axios | 1.7 |
| Logging | Winston | 3.10 |
| APM | apminsight (Site24x7) | 5.1 |
| Testing | Jest + ts-jest | 29.7 |
| Formatting | Prettier | 3.0 |
| Git Hooks | Husky + lint-staged | 8.x / 14.x |
| CI/CD | Azure Pipelines | — |
| Env Config | dotenv | 16.3 |

## Coding Conventions

### Style
- **Prettier** enforces formatting on commit (via Husky pre-commit hook)
- Print width: 140 characters
- Single quotes, trailing commas (all), no semicolons omitted
- Arrow parens: avoid (single param without parens)
- 2-space indentation, LF line endings

### Naming
- Files: kebab-case (`on-road-price-handler.ts`, `price-component-apis.ts`)
- Classes: PascalCase (`OnRoadPriceHandler`, `RegionService`)
- Instances/exports: camelCase (`onRoadPriceHandler`, `regionService`)
- Constants: UPPER_SNAKE_CASE for objects (`HTTP_ERROR_CONSTANTS`), camelCase for individual values
- Interfaces: PascalCase with `Interface` suffix (`ORPInterface`, `PriceComponentsInterface`)
- Test files: `<module-name>.test.ts` in `test/` subdirectories

### Structure Patterns
- One class per file, instantiated as singleton at bottom, exported as default
- Barrel `index.ts` in every directory for clean re-exports
- Tests co-located in `test/` subdirectories within each module (not a top-level `__tests__` folder)
- Mock data defined inline in test files or in `test/mock/` directories

### TypeScript
- Strict mode not explicitly enabled
- Experimental decorators enabled (for error handling decorators)
- `any` type used liberally (especially for downstream API responses)
- Interfaces defined in `src/utils/interface/` directory
- No enums — constants objects used instead

## Patterns

### Error Handling (Decorator Pattern)

Two decorators handle all error scenarios:

**`@errorDecorator.handleResponseError`** — Used on handler methods (controller layer)
- Wraps the method in try-catch
- On error: extracts status code and message, sends JSON error response
- Handles both Axios errors (with `response.data.message`) and AppCustomError instances
- Falls back to 500 Internal Server Error if no status code

**`@errorDecorator.handleTryCatchError`** — Used on service and implementer methods
- Wraps the method in try-catch
- Logs successful results at info level
- Logs errors at error level with message and status code
- Re-throws the error for upstream handling

**`AppCustomError`** — Custom error class
- Extends `Error` with a `statusCode` property
- Used throughout validators and services to throw typed errors
- Constructor: `new AppCustomError(statusCode: number, message: string)`

### HTTP Communication

The `Http` class in `src/rest/http/http.ts` wraps Axios:
- Sets `Content-Type: application/json` and `Accept: application/json` headers on all requests
- Exposes `get`, `post`, `put` methods
- Returns `response.data` directly (unwraps Axios response)
- Re-throws errors without transformation (handled by decorators above)

### URL Construction

API URLs are built in `src/rest/API-directories/` files:
- Each file exports functions that construct full URLs from base URL + path + query params
- Query params converted via `utilFunctions.convertToQueryFormate()` which handles arrays and encoding
- Base URL read from `PRICE_MICROSERVICE_BASE_URL` environment variable

### Data Reshaping

Complex transformations live in `src/utils/reshape-objects/`:
- `ReshapeOnRoadPrice`: Flattens nested ORP response, adds pagination metadata, calculates active/inactive counts, extracts unique component names
- `ReshapeProductPriceComponent`: Groups flat component list into hierarchical structure (component → state → city)

### Validation

Validators in `src/handlers/validators/`:
- Throw `AppCustomError` with `BAD_REQUEST` (400) status on invalid input
- `commonValidator`: ObjectID format check, empty string check
- `productValidator`: Engine type must be ICE or EV (case-insensitive)
- Called directly in handlers before service calls

## Testing

### Framework & Config
- Jest with ts-jest preset
- Node test environment
- Coverage collected to `coverage/` directory
- Cobertura format for CI reporting (`jest --coverage --coverageReporters=cobertura`)

### Test Structure
- Tests in `test/` subdirectories within each module
- Pattern: `<module-name>.test.ts`
- Shared mocks in `test/mock/` directories

### Testing Approach
- **Unit tests only** — no integration or e2e tests
- **Mock everything downstream**: Services mock implementers, handlers mock services, implementers mock HTTP client
- **Jest mocking**: `jest.fn().mockResolvedValue()` for async mocks, `jest.spyOn()` for spy assertions
- **Mock request/response**: Simple objects with `status()` and `json()` chainable methods
- **Assertions**: `expect().toBe()`, `expect().toEqual()`, `expect().toStrictEqual()`, `toHaveBeenCalled()`, `toHaveBeenCalledTimes()`
- **Setup/teardown**: `beforeEach(() => jest.clearAllMocks())` and `afterEach(() => jest.clearAllMocks())`

### Running Tests
```bash
npm test              # Run all tests
npm run test-coverage # Run with coverage report
npm run coverage      # Run with Cobertura coverage (for CI)
```

## Build & Development

### Scripts
```bash
npm run dev           # Development with nodemon + ts-node (auto-reload)
npm run build         # TypeScript compilation to dist/
npm start             # Build then run dist/src/server.js
npm test              # Run Jest tests
```

### Build Output
- TypeScript compiles to `dist/` directory
- Entry point: `dist/src/server.js`

## Deployment

### Azure Pipelines (CI)
- Triggers on `develop` branch
- Ubuntu latest VM
- Steps: checkout → Node 18 setup → npm install → npm build → npm test → copy files → publish artifact
- Artifact name: `drop`

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `API_SERVER_PORT` | Server port | 8001 |
| `SERVER_HOST_URL` | Server bind address | 0.0.0.0 |
| `PRICE_MICROSERVICE_BASE_URL` | Downstream service URL | http://0.0.0.0:8080 |
| `NODEJS_STARTER_ENV` | Environment name | local |

### Server Startup
1. `apminsight` is configured first (APM instrumentation)
2. Express app created with JSON body parser and CORS
3. Routes mounted at their respective paths
4. Server listens on configured host:port

## Dependencies of Note

- **apminsight**: Site24x7 APM agent — must be imported and configured before other imports in `routes.ts`
- **npm-force-resolutions**: Used in postinstall to force specific versions of transitive dependencies (security patches for `debug`, `inflight`, `formidable`, `micromatch`)
- **No ORM/database driver**: This is a pure BFF with no direct data store access

