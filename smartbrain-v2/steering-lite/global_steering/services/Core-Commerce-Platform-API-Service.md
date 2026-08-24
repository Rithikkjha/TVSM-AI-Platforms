# Core-Commerce-Platform-API-Service


## Product Context


# Core Commerce Platform (CCP) — Product Context

## What This Service Does

This is the **TVS Motors Core Commerce Platform Catalog API Service**. It serves as the backend for managing vehicle product catalogs, regional pricing, and product data across multiple consumer-facing channels (namespaces). The service powers catalog experiences for TVS Motor Company's digital commerce ecosystem.

## Domain Entities

### Catalog
The central entity. A catalog groups vehicle products into categories (ICE, EV) for a specific namespace, market, and industry. Catalogs have auto-incrementing numeric IDs alongside MongoDB ObjectIds. Soft-deleted via `isArchived` flag.

Key fields: `name`, `id`, `productType`, `market`, `industry`, `nameSpace`, `isDefaultCatalog`, `categories[]`

### Catalog Configuration
Namespace-level configuration that defines which product definitions, SKU IDs, price attributes, and product specification attributes apply. Controls behavior like `includeCategoriesWithoutRegion` and `calculateORP`.

### Catalog Audit
Audit trail for catalog mutations. Created asynchronously (fire-and-forget with `.then()/.catch()`) after catalog updates.

### Vehicle Product Master
Canonical product specifications for EV vehicles — model, variant, color, partId. Used during catalog creation to populate EV catalog items.

### EV Price Master / ICE Price Master
Region-specific pricing records. EV prices are keyed by city/state; ICE prices are keyed by state. Both support `applicableNameSpaces` to filter by channel. Price objects contain dynamic attributes (ex-showroom, road tax, insurance, subsidies).

### Merchandise & Accessories Product Price
Shopify-sourced product data for non-vehicle items (accessories, merchandise). Supports filtering by SKU ID and applicable vehicle model IDs.

### Vehicle Accessories Pricing (BAAS)
Battery-as-a-Service pricing. Simple model: `modelId + state → price`. Supports bulk upsert via matrix format (rows = states, columns = model IDs).

### Region
Geographic data (country, state, city) used for price lookups.

### Category
Hierarchical product categorization with nested subcategories and catalog items.

## Namespaces (Consumer Channels)

- **TVS** — Default namespace (TVS main channel)
- **PQC** — Pre-qualification channel (has deeper category nesting: category → subcategory → model → variant → catalogItems)
- **MARKETPLACE** — Marketplace channel
- **EVWEBSITE** — EV-specific website

## Integrations

### MongoDB (Primary Data Store)
All domain entities persisted in MongoDB. Mongoose schemas with static query methods serve as the data access layer.

### Redis (Caching Layer)
Caches prices (ICE by state, EV by city), product data, and catalog configurations. Cache keys follow pattern: `cache:ccp:{domain}:{identifier}`. Uses `getOrSet` pattern for cache-aside.

### Shopify Admin API (v2023-07)
Fetches accessories and merchandise product data including variant metafields. Configured via `SHOPIFY_API_URL`, `SHOPIFY_ACCESS_TOKEN`, `SHOPIFY_PRODUCT_IDS` env vars.

### Bumblebee Data Lake
External data source for ICE vehicle catalog items and pricing metadata. Accessed via `IceImplementer` and `EvImplementer` classes through HTTPS calls.

### Site24x7 APM (apminsight)
Application performance monitoring. Initialized at app startup before Express.

## Business Rules

### Pricing
- **ICE vehicles**: Priced by state. State names are normalized via a mapping (e.g., CHHATTISGARH → CHHATISGARH, GOA → GOA, DAMAN & DIU).
- **EV vehicles**: Priced by city/state.
- **On-Road Price (ORP) calculation**: When `calculateORP` is enabled in catalog config, subsidy fields (`famesubsidy`, `stateadditionalsubsidy`) are negated (subtracted from total).
- **Price fallback logic (ICE)**: Tries modelId+partId+variant+color → modelId+partId → modelId (first partId) → null.

### Catalog Creation
1. Validate payload and catalog item source (EV, ICE, ALL)
2. Fetch catalog configuration for the namespace
3. Match applicable definition IDs
4. Pull product data from Vehicle Product Master (EV) or Bumblebee (ICE)
5. Assign auto-incremented catalog ID
6. Persist catalog and update catalog configuration with new catalog-definition mapping

### Catalog Retrieval (Default)
1. Query by namespace, market, industry, productType
2. Sort by ID descending (latest first)
3. Populate price data per category based on engine type and region
4. If `includeCategoriesWithoutRegion` is false and no price data exists for the region, empty out that category's items

### Soft Deletion
Catalogs are never physically deleted. `deleteCatalog` sets `isArchived: true`.

### State Name Normalization
Multiple mappings exist (handler-level and service-level) to normalize Indian state names between different data sources. This is a known duplication.



## Code Structure


# Project Structure

## Annotated Directory Layout

```
Core-Commerce-Platform-API-Service/
├── .husky/                          # Git hooks (pre-commit runs lint-staged/prettier)
├── data-insertion-scripts/          # Shell scripts for MongoDB data seeding
│   ├── bumblebee-ice-ev-data.sh     # Seed ICE/EV data from Bumblebee
│   ├── catalog-configuration-data.sh
│   ├── product-master-data.sh
│   └── region-master-data.sh
├── sonar-exclusion-function/        # Scripts excluded from SonarQube analysis
│   └── scripts/
│       ├── swagger.ts               # Swagger JSON definition
│       ├── data-migration-script.ts
│       ├── insert-catalog-configuration.ts
│       ├── insert-product-master.ts
│       └── ice-ev-model-data-grouping.ts
├── src/
│   ├── server.ts                    # App entry point (starts Express server)
│   ├── config/                      # Environment configuration
│   │   ├── db-config.ts             # MongoDB connection params from env
│   │   ├── redis-config.ts          # Redis client factory with reconnect strategy
│   │   ├── shopify-config.ts        # Shopify API credentials from env
│   │   ├── host.ts                  # Server host config
│   │   └── port.ts                  # Server port config
│   ├── constants/                   # Application-wide constants
│   │   ├── error-constants.ts       # Domain-specific error messages
│   │   ├── http-status-codes.ts     # HTTP status code exports
│   │   ├── catalog-constants.ts     # Catalog domain enums and keys
│   │   ├── cache-constants.ts       # Redis cache key prefixes (enum)
│   │   ├── orp-calculation-constants.ts  # ORP subtraction parameters
│   │   └── logger-constants.ts      # Winston logging config
│   ├── db/                          # Database layer
│   │   └── mongodb/
│   │       ├── db.ts                # Mongoose connection class
│   │       ├── schema/              # Mongoose schemas (14 files)
│   │       │   ├── catalog-schema.ts
│   │       │   ├── catalog-configuration-schema.ts
│   │       │   ├── ev-price-master-schema.ts
│   │       │   ├── ice-price-master-schema.ts
│   │       │   ├── vehicle-product-master-schema.ts
│   │       │   ├── vehicle-accessories-pricing-schema.ts
│   │       │   ├── merchandise-accessories-product-price-master-data-schema.ts
│   │       │   └── ... (audit, health, categories, regions, products, prices)
│   │       └── aggregation-queries.ts/  # MongoDB aggregation pipelines
│   │           ├── vehicle-product-master-queries.ts
│   │           └── merchandise-accessories-queries.ts
│   ├── models/                      # Thin re-export layer for schemas
│   │   └── mongodb/                 # One file per model, re-exports schema default
│   ├── routes/                      # Express route definitions
│   │   ├── routes.ts                # Main router setup (app.use registrations)
│   │   └── api/
│   │       ├── catalog-routes.ts    # /catalogs endpoints
│   │       ├── catalog-configuration-routes.ts  # /catalog-configs endpoints
│   │       ├── cache-routes.ts      # /cache endpoints
│   │       ├── shopify-routes.ts    # /shopify endpoints
│   │       ├── vehicle-accessories-pricing-routes.ts  # /vehicle-accessories-pricing
│   │       └── application-heath-routes.ts  # /health endpoints
│   ├── handlers/                    # Request handlers (controller layer)
│   │   ├── catalog-handler.ts       # Catalog CRUD + default catalog
│   │   ├── catalog-configuration-handler.ts
│   │   ├── cache-handler.ts
│   │   ├── shopify-handler.ts
│   │   ├── vehicle-accessories-pricing-handler.ts
│   │   ├── validators/              # Request-level validation
│   │   └── test/                    # Handler unit tests
│   ├── services/                    # Business logic layer
│   │   ├── catalog-service.ts       # Core catalog operations
│   │   ├── catalog-configuration-service.ts
│   │   ├── catalog-audit-service.ts
│   │   ├── merchandise-accessories-catalog-service.ts
│   │   ├── vehicle-accessories-pricing-service.ts
│   │   ├── shopify-service.ts
│   │   ├── region-service.ts
│   │   ├── category-service.ts
│   │   ├── application-health-service.ts
│   │   ├── cache/                   # Redis cache services
│   │   │   ├── base-cache-service.ts    # Generic get/put/remove/getOrSet
│   │   │   ├── ev-price-cache-service.ts
│   │   │   ├── ice-price-cache-service.ts
│   │   │   └── product-cache-service.ts
│   │   ├── validators/              # Service-level validation
│   │   └── test/                    # Service unit tests
│   ├── middleware/                   # Express middleware
│   │   ├── error-middleware.ts      # Error logging + response + 404
│   │   └── response-time-middleware.ts  # X-Time-Taken-In-Ms header
│   ├── rest/                        # External HTTP client utilities
│   │   ├── http/                    # HTTP client wrapper
│   │   ├── https/                   # HTTPS client wrapper (Shopify, Bumblebee)
│   │   └── API-directories/         # External API endpoint URL definitions
│   └── utils/                       # Shared utilities
│       ├── classes/                 # AppCustomError
│       ├── decorators/              # @handleTryCatchError, @handleResponseError
│       ├── functions/               # logger (Winston), utilFunctions
│       ├── implementers/            # External data adapters
│       │   ├── shopify-implementer/ # Shopify data fetching
│       │   ├── ice-implementer/     # Bumblebee ICE data
│       │   └── ev-implementer/      # Bumblebee EV data
│       ├── interface/               # TypeScript interfaces (17 files)
│       ├── reshapeObjects/          # Data transformation utilities
│       └── test/                    # Utility unit tests
├── Dockerfile                       # Multi-stage build (Node 20 Alpine)
├── package.json
├── jest.config.js
├── tsconfig.json
└── .prettierrc
```

## Module Dependencies (Data Flow)

```
Routes → Handlers → Services → Models (Schemas)
                  ↘ Validators     ↗ Cache Services
                                   ↗ Implementers (external APIs)
```

- **Routes** only wire HTTP verbs to handler methods. No logic.
- **Handlers** parse request params/body, call validators, invoke services, send responses. Error handling via `@handleResponseError` decorator.
- **Services** contain all business logic. Use `@handleTryCatchError` decorator. Call models directly and other services as needed.
- **Models** are thin re-exports of Mongoose schemas. Schemas contain static methods for data access (no separate repository pattern).
- **Cache Services** wrap Redis operations with domain-specific key building and `getOrSet` patterns.
- **Implementers** encapsulate external API calls (Shopify, Bumblebee data lake).

## Architectural Decisions

1. **Class-based singletons** — Services, handlers, and implementers are classes instantiated once and exported as default. No dependency injection framework.

2. **Decorator-based error handling** — Two decorators (`handleTryCatchError` for services, `handleResponseError` for handlers) eliminate repetitive try/catch blocks.

3. **Static methods on schemas** — Mongoose schemas define their own query methods as statics. This couples data access to schema definitions but keeps queries co-located with their models.

4. **Barrel exports everywhere** — Every directory has an `index.ts` that re-exports its contents. Import from the directory, not individual files.

5. **No separate repository layer** — Services call model statics directly. The schema IS the repository.

6. **Cache-aside pattern** — `getOrSet(key, fetcher)` checks Redis first, falls back to DB, then populates cache.

7. **Soft deletes** — `isArchived: true` instead of physical deletion for catalogs.

8. **Auto-incrementing IDs** — Custom `getMaximumId()` + increment pattern alongside MongoDB ObjectIds for human-readable catalog IDs.

9. **Environment-based Redis config** — Different ports, TLS settings, and connection strategies per environment (local/test/dev/uat/prod).

10. **Multi-stage Docker build** — Separate build and runtime stages. Non-root user in production image.



## Tech Stack & Dependencies


# Tech Stack & Conventions

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Node.js | 20 (Alpine) |
| Language | TypeScript | 5.5 |
| Framework | Express | 4.19 |
| Database | MongoDB via Mongoose | 8.9 |
| Cache | Redis | 5.10 |
| HTTP Client | Axios | 1.7 |
| Logging | Winston | 3.13 |
| APM | apminsight (Site24x7) | 5.1 |
| Utilities | Lodash | 4.17 |
| Testing | Jest + ts-jest + Supertest | 29.7 |
| Formatting | Prettier | 3.0 |
| Git Hooks | Husky + lint-staged | 9.x |

## Coding Conventions

### File & Naming
- Files use **kebab-case**: `catalog-service.ts`, `ev-price-master-schema.ts`
- Classes use **PascalCase**: `CatalogService`, `AppCustomError`
- Interfaces use **PascalCase** with `Interface` suffix: `CatalogInterface`, `EVPriceMasterInterface`
- Constants use **UPPER_SNAKE_CASE** for objects, **camelCase** for properties within
- Enums use **PascalCase** name, **UPPER_SNAKE_CASE** members: `CacheName.ICE_PRICES`

### Module Structure
- Every directory has an `index.ts` barrel export
- Import from the directory path, not individual files: `import { catalogService } from '../services'`
- One class per file, instantiated as singleton and exported as default
- Named exports for interfaces and types

### Class Pattern
```typescript
class SomeService {
  @errorDecorator.handleTryCatchError
  public async someMethod(params: SomeInterface) {
    // business logic
  }
}

const someService = new SomeService();
export default someService;
```

### Prettier Configuration
- Print width: 140
- Tab width: 2 (spaces, not tabs)
- Single quotes
- Trailing commas: all
- Arrow parens: avoid (omit when single param)
- Semicolons: yes
- Line endings: LF
- Bracket spacing: yes

### TypeScript
- Strict mode not enforced (uses `as` casts and `any` in places)
- Interfaces preferred over types for domain objects
- `require('dotenv').config()` used in config files (not import)

## Patterns

### Error Handling

**Custom Error Class:**
```typescript
class AppCustomError extends Error {
  statusCode: number;
  constructor(statusCode: number, errorMessage: string) {
    super(errorMessage);
    this.statusCode = statusCode;
  }
}
```

**Error Decorators:**
- `@errorDecorator.handleTryCatchError` — Used on service methods. Wraps in try/catch, logs success/error, rethrows.
- `@errorDecorator.handleResponseError` — Used on handler methods. Catches errors and sends HTTP response with status code and message.

**Error Middleware (fallback):**
- `errorLogger` → logs error
- `errorResponder` → sends JSON `{ message }` with status code
- `routeNotFound` → 404 for unmatched routes

**Error Constants:**
Domain-specific error messages organized by feature in `src/constants/error-constants.ts`. Reference via `ErrorMessages.CATALOG_ERROR_CONSTANTS.catalogNotFound`.

### Validation
- **Handler validators** (`src/handlers/validators/`): Validate request shape, required fields, query params
- **Service validators** (`src/services/validators/`): Validate business rules, data consistency
- **Common validators**: `numberValidator`, `objectIdValidator`, `emptyStringValidator`
- Validators throw `AppCustomError` with appropriate HTTP status codes

### Caching
- **Cache-aside pattern** via `baseCacheService.getOrSet(key, fetcher)`
- **Key format**: `cache:ccp:{domain}:{identifier}` (defined in `CacheName` enum)
- **Domain-specific cache services** extend base: `evPriceCacheService`, `icePriceCacheService`, `productCacheService`
- **No TTL configured** — cache entries persist until explicitly cleared via `/cache` endpoints
- **Graceful degradation** — if Redis is unavailable, operations return null/false without throwing

### Data Access
- Mongoose schemas define static methods for queries
- No separate repository layer — services call model statics directly
- Aggregation pipelines defined in `src/db/mongodb/aggregation-queries.ts/`
- Soft deletes: `isArchived: true` filter applied in queries

### External API Calls
- Wrapped in implementer classes (`ShopifyImplementer`, `IceImplementer`, `EvImplementer`)
- Use `httpsClient` wrapper around Axios
- Timeout: 10 seconds for Shopify calls
- Parallel fetching with `Promise.all` where possible

### Response Time Tracking
Custom middleware measures request duration and adds `X-Time-Taken-In-Ms` response header.

## Testing

### Framework & Config
- **Jest** with `ts-jest` preset, Node test environment
- Coverage enabled, output to `coverage/` directory
- Cobertura reporter for CI integration

### Test Location
Tests are co-located in `test/` subdirectories within each module:
- `src/handlers/test/`
- `src/services/test/`
- `src/utils/test/`
- `src/db/mongodb/aggregation-queries.ts/test/`

### Test Patterns
- Unit tests with extensive mocking (`jest.fn().mockResolvedValue()`)
- `describe` blocks per class/service
- `beforeEach`/`afterEach` for mock setup and cleanup
- Spy on validators and dependent services
- No integration tests or E2E tests in the repo

### Running Tests
```bash
npm test              # Run all tests
npm run test-coverage # Run with coverage report
npm run coverage      # Coverage with cobertura output (CI)
```

## Deployment

### Docker
- **Multi-stage build**: Stage 1 (build) compiles TypeScript, Stage 2 (runtime) runs compiled JS
- **Base image**: `node:20-alpine`
- **Non-root user**: `appuser` created in runtime stage
- **Port**: 8080
- **Start command**: `npm start` → `node dist/src/server.js`

### Environments
| Env | Redis Port | TLS | Notes |
|-----|-----------|-----|-------|
| local | 6379 | No | Local development |
| test | — | — | Redis disabled (returns null) |
| dev | 6380 | Yes | Development server |
| uat | 6380 | Yes | User acceptance testing |
| prod | 6380 | Yes | Production |

### Environment Variables
Key env vars (configured via `.env` or deployment platform):
- `DB_SCHEME`, `DB_USER_NAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` — MongoDB
- `REDIS_HOST`, `REDIS_PASSWORD` — Redis
- `NODE_ENV` — Environment (local/test/dev/uat/prod)
- `SHOPIFY_API_URL`, `SHOPIFY_ACCESS_TOKEN`, `SHOPIFY_PRODUCT_IDS` — Shopify
- `APP_PORT`, `APP_HOST` — Server binding

### Build & Dev Commands
```bash
npm run dev    # Development with nodemon + ts-node
npm run build  # Compile TypeScript to dist/
npm start      # Run compiled app (production)
npm run watch  # TypeScript watch mode
```

### Data Seeding
Shell scripts in `data-insertion-scripts/` for initial data population:
```bash
sh data-insertion-scripts/product-master-data.sh
sh data-insertion-scripts/catalog-configuration-data.sh
sh data-insertion-scripts/region-master-data.sh
```

### Code Quality
- **Prettier** auto-formats on commit via Husky pre-commit hook
- **SonarQube** analysis (scripts in `sonar-exclusion-function/` are excluded)
- No ESLint configured — formatting only via Prettier

