# Catalog-Microservice-Backend-for-Frontend-Layer


## Product Context


# Product Context: Catalog BFF Layer

## What This Service Does

This is a **Backend-for-Frontend (BFF) layer** for the Catalog Microservice, part of TVS Motor's Core Commerce Platform (CCP). It sits between frontend clients (bike aggregator websites and internal apps) and the backend Catalog Microservice, providing:

- Data transformation and reshaping for specific consumer namespaces
- Field filtering based on catalog configuration definitions
- Price calculations for bike aggregator partners
- OAuth2 token management for secure downstream communication
- Azure Key Vault secret management

The BFF does not own any data. It proxies, filters, and transforms catalog data from the downstream Catalog Microservice.

## Domain Entities

### Catalog
A product catalog containing hierarchical categories of vehicles. Structure: Catalog → Categories → SubCategories → CatalogItems. Each catalog has a productType, market, industry, and namespace.

### CatalogItem
An individual product entry (e.g., a specific bike variant/color). Contains `price` and `productInfo` objects with dynamic keys.

### CatalogConfiguration
Namespace-specific configuration that defines which catalogs exist and what attributes are applicable for each. Maps catalog IDs to applicable definition IDs.

### ApplicableDefinitionInfo
Defines which price attributes and product specification attributes should be exposed for a given engine type (EV/ICE) and product type. Acts as a field-level access control for catalog items.

### CatalogAndApplicableInfos
Junction entity mapping a `catalogId` to its allowed `definitionIds`.

## Namespaces (Consumers)

| Namespace | Description |
|-----------|-------------|
| TVS | Internal TVS namespace |
| BIKEDEKHO | Bike aggregator partner |
| BIKEWALE | Bike aggregator partner |
| 91WHEELS | Bike aggregator partner |

Bike aggregator namespaces receive an additional computed `other` price field (on-road price minus sum of all itemized charges).

## Integrations

### Downstream: Catalog Microservice
- **Base URL**: `CATALOG_MICRO_SERVICES_BASE_URL` env var
- `GET /catalogs?productType=&market=&industry=&nameSpace=&isDefaultCatalog=&state=&cityName=` — Fetch default catalog
- `GET /catalog-configs/{nameSpace}` — Fetch catalog configuration for a namespace
- Authenticated via internal OAuth2 bearer token

### Azure AD OAuth2
- Client credentials flow for token generation
- Endpoint: `AZURE_OAUTH_TOKEN_BASE_URL/{tenantId}/oauth2/v2.0/token`
- Supports internal and external token scopes
- Tokens are cached with expiry buffer (60s) and concurrent refresh deduplication

### Azure Key Vault
- Secrets fetched at startup and cached in memory (`azureSecretCache`)
- Secrets: client ID, client secret, tenant ID, internal scope, external scope
- Uses `@azure/identity` EnvironmentCredential + `@azure/keyvault-secrets` SecretClient

## Business Rules

1. **nameSpace is required** — All catalog queries must include a valid namespace
2. **isDefaultCatalog defaults to true** — If not provided in the query
3. **productType is uppercased** — Normalized before forwarding to downstream
4. **nameSpace is uppercased** — Normalized before forwarding
5. **Ampersand encoding** — `&` in state/city names is replaced with `%26` to avoid query param conflicts
6. **Applicable definition matching** — Catalog items are filtered to only expose attributes defined in the matching applicable definition (matched by engineType + productType)
7. **Bike aggregator price calculation** — For BIKEDEKHO, BIKEWALE, 91WHEELS namespaces: `other = onroadprice - sum(all other price fields except onroadprice and discount)`
8. **Missing applicable definition throws error** — If no applicable definition matches the catalog, a BAD_REQUEST error is returned
9. **Token caching** — OAuth tokens are cached and reused until 60 seconds before expiry
10. **Startup dependency** — Server will not start if Azure secrets initialization fails (process exits with code 1)



## Code Structure


# Project Structure

## Annotated Directory Layout

```
├── .env                          # Environment variables (port, host, Azure config, downstream URLs)
├── .husky/pre-commit             # Git hook: runs lint-staged (Prettier) on commit
├── .prettierrc                   # Prettier config (140 width, single quotes, trailing commas)
├── azure-pipelines/              # CI/CD pipeline definitions
│   ├── EMS-Catalog-BFF-Prod-CI.yml   # Production pipeline (release branch)
│   └── EMS-Catalog-BFF-Uat-CI.yml    # UAT pipeline (uat branch, triggered by upstream AST pipeline)
├── jest.config.js                # Jest config (ts-jest preset, node env, coverage)
├── package.json                  # Dependencies, scripts, lint-staged config
├── sonar-exclusion-function/     # Files excluded from SonarQube analysis
│   └── swagger.ts                # Swagger/OpenAPI spec definition
└── src/
    ├── server.ts                 # Entry point — imports routes, calls startServer()
    ├── config/                   # Environment configuration readers
    │   ├── host.ts               # Reads SERVER_HOST_URL from env
    │   ├── port.ts               # Reads API_SERVER_PORT from env
    │   └── index.ts              # Barrel export
    ├── constants/                # Application constants (no logic)
    │   ├── azure-header-constants.ts   # OAuth token request field names
    │   ├── catalog-constants.ts        # Namespace identifiers, default product spec fields
    │   ├── common-constants.ts         # General constants (success string, internalApp flag)
    │   ├── error-constants.ts          # Error message strings by domain
    │   ├── http-status-codes.ts        # HTTP status code numbers
    │   ├── key-vault-constants.ts      # Azure Key Vault secret names
    │   ├── logger-constants.ts         # Winston logging config (colors, levels)
    │   ├── token-scope.enum.ts         # TokenScope enum (INTERNAL/EXTERNAL)
    │   └── index.ts                    # Barrel export
    ├── handlers/                  # Request handlers (controller layer)
    │   ├── application-health-handler.ts  # GET /health handler
    │   ├── catalog-handler.ts             # GET /catalogs handler
    │   ├── index.ts                       # Barrel export
    │   ├── validators/                    # Input validation (throws on invalid)
    │   │   ├── catalog-validator.ts       # Validates catalog query params
    │   │   ├── common-validator.ts        # ObjectId format validator
    │   │   ├── index.ts                   # Barrel export
    │   │   └── test/                      # Validator unit tests
    │   └── test/                          # Handler unit tests
    │       └── mock/                      # Shared mock request/response objects
    ├── middleware/                 # Express middleware
    │   ├── error-middleware.ts    # Error logger, responder, 404 handler
    │   ├── index.ts              # Barrel export
    │   └── test/mock/            # Middleware test mocks
    ├── rest/                      # External API integration layer
    │   ├── API-directories/       # URL builders for downstream services
    │   │   ├── azure-service-api.ts   # Azure OAuth token URL builder
    │   │   ├── catalog-api.ts         # Catalog microservice URL builders
    │   │   └── index.ts               # Barrel export
    │   ├── http/                  # HTTP client abstraction
    │   │   └── http.ts            # Axios wrapper with header management
    │   └── implementers/          # Service clients (make actual HTTP calls)
    │       ├── azure-service-implementers.ts  # OAuth token generation
    │       ├── azureSecretCache.ts            # In-memory secret cache singleton
    │       ├── azureSecretInitializer.ts      # Startup secret fetching
    │       ├── catalog-implementer.ts         # Catalog microservice client
    │       ├── key-vault-implementers.ts      # Azure Key Vault client
    │       ├── index.ts                       # Barrel export
    │       └── test/                          # Implementer unit tests
    ├── routes/                    # Express route definitions
    │   ├── routes.ts              # App setup (Express, CORS, middleware, routes, server start)
    │   └── api/                   # Individual route files
    │       ├── application-health-route.ts  # GET /health
    │       └── catalog-route.ts             # GET /catalogs
    ├── services/                  # Business logic layer
    │   ├── application-health-service.ts  # Health check (returns SUCCESS)
    │   ├── catalog-service.ts             # Core catalog logic (fetch, filter, transform)
    │   ├── token-service.ts               # OAuth token caching and refresh
    │   ├── index.ts                       # Barrel export
    │   └── test/                          # Service unit tests
    └── utils/                     # Cross-cutting utilities
        ├── classes/
        │   └── custom-error.ts    # AppCustomError (extends Error with statusCode)
        ├── decorators/
        │   └── error-decorators.ts  # @handleResponseError, @handleTryCatchError
        ├── functions/
        │   └── logger.ts          # Winston logger instance
        ├── interface/
        │   └── catalog-configuration.ts  # TypeScript interfaces for domain entities
        ├── reshape-objects/
        │   ├── reshape-bike-aggregator.ts  # Price "other" field calculator
        │   └── test/                       # Reshape unit tests
        └── index.ts               # Barrel export
```

## Module Dependencies (Data Flow)

```
server.ts
  └── routes/routes.ts (Express app setup + startServer)
        ├── routes/api/catalog-route.ts
        │     └── handlers/catalog-handler.ts
        │           ├── handlers/validators/catalog-validator.ts
        │           └── services/catalog-service.ts
        │                 ├── rest/implementers/catalog-implementer.ts
        │                 │     ├── rest/API-directories/catalog-api.ts (URL builders)
        │                 │     ├── rest/http/http.ts (Axios wrapper)
        │                 │     └── services/token-service.ts
        │                 │           └── rest/implementers/azure-service-implementers.ts
        │                 │                 ├── rest/API-directories/azure-service-api.ts
        │                 │                 └── rest/implementers/azureSecretCache.ts
        │                 └── utils/reshape-objects/reshape-bike-aggregator.ts
        ├── routes/api/application-health-route.ts
        │     └── handlers/application-health-handler.ts
        │           └── services/application-health-service.ts
        └── rest/implementers/azureSecretInitializer.ts (called at startup)
              ├── rest/implementers/key-vault-implementers.ts
              └── rest/implementers/azureSecretCache.ts
```

## Architectural Decisions

1. **Layered architecture** — Routes → Handlers → Services → Implementers. Each layer has a single responsibility.
2. **BFF pattern** — This service does not own data. It proxies, filters, and transforms data from the Catalog Microservice for specific frontend consumers.
3. **Class-based singletons** — All handlers, services, and implementers are classes instantiated once at module level and exported as singletons.
4. **Decorator-based error handling** — TypeScript decorators wrap methods with try/catch logic, keeping handler/service code clean.
5. **Startup secret initialization** — Azure secrets are fetched once at startup and cached in memory. Server refuses to start if secrets cannot be loaded.
6. **Token caching with deduplication** — TokenService prevents thundering herd by storing in-flight token generation promises and sharing results across concurrent callers.
7. **Barrel exports everywhere** — Every directory has an `index.ts` for clean imports.
8. **Swagger excluded from SonarQube** — Placed in `sonar-exclusion-function/` directory to avoid analysis.
9. **No database in BFF** — MongoDB/Mongoose dependencies exist but the BFF delegates all data persistence to the downstream Catalog Microservice.



## Tech Stack & Dependencies


# Technical Reference

## Tech Stack

| Category | Technology | Version |
|----------|-----------|---------|
| Runtime | Node.js | (not pinned) |
| Language | TypeScript | ^5.5.3 |
| Framework | Express.js | ^4.19.2 |
| HTTP Client | Axios | ^1.7.2 |
| Logging | Winston | ^3.13.0 |
| Testing | Jest + ts-jest | ^29.7.0 / ^29.1.5 |
| APM | apminsight (Site24x7) | ^5.1.1 |
| API Docs | swagger-ui-express | ^5.0.1 |
| Secrets | @azure/keyvault-secrets | ^4.8.0 |
| Identity | @azure/identity | ^4.0.1 |
| Formatting | Prettier | 3.0.3 |
| Git Hooks | Husky + lint-staged | ^9.0.11 / ^14.0.1 |
| CI/CD | Azure Pipelines | — |

## Coding Conventions

### Formatting (Prettier)
- Print width: 140 characters
- Tab width: 2 spaces (no tabs)
- Single quotes for strings
- Trailing commas: all
- Arrow parens: avoid (omit parens for single param)
- Semicolons: always
- End of line: LF
- Bracket spacing: true

### Naming
- Files: kebab-case (`catalog-handler.ts`, `error-constants.ts`)
- Classes: PascalCase (`CatalogService`, `AppCustomError`)
- Instances/singletons: camelCase (`catalogService`, `errorDecorator`)
- Constants objects: UPPER_SNAKE_CASE (`CATALOG_ERROR_CONSTANTS`, `HTTP_ERROR_CONSTANTS`)
- Interfaces: PascalCase with `Interface` suffix (`CatalogConfigurationInterface`)
- Enums: PascalCase (`TokenScope`)

### Module Organization
- Every directory has an `index.ts` barrel export
- Imports use barrel paths where possible (`'../constants'` not `'../constants/error-constants'`)
- `require('dotenv').config()` called in files that read `process.env` directly (config files, API directories)

### Class Pattern
- Business logic lives in classes instantiated as module-level singletons
- Classes are not dependency-injected; they import dependencies directly
- One class per file, exported as default singleton instance

## Patterns

### Error Handling

**Custom Error Class:**
```typescript
class AppCustomError extends Error {
  statusCode: number;
  constructor(statusCode: number, errorMessage: string) { ... }
}
```

**Decorator Pattern (two variants):**

1. `@errorDecorator.handleResponseError` — Used on handler methods. Catches errors and sends HTTP error response with status code and message.

2. `@errorDecorator.handleTryCatchError` — Used on service methods. Catches errors, logs them, and re-throws for the handler layer to handle.

**Implementer Error Handling:**
- Catch AxiosError explicitly
- Extract status from `error.response.status` (fallback to 500)
- Extract message from `error.response.data.message` (fallback to constant)
- Wrap in AppCustomError and throw

**Error Middleware (defined but not wired):**
- `errorLogger`: Logs error details
- `errorResponder`: Sends JSON error response
- `routeNotFound`: Returns 404 for unmatched routes

### Authentication Flow

1. At startup: `initializeAzureSecrets()` fetches all secrets from Azure Key Vault into `azureSecretCache`
2. On API request: `tokenService.getBearerToken(internal)` is called
3. TokenService checks cache → if valid token exists, returns it
4. If expired/missing: generates new token via `generateOAuthToken(internal)`
5. Concurrent requests share the same in-flight promise (deduplication)
6. Token cached with 60-second expiry buffer

### Validation Pattern
- Validators are classes with methods that either return a sanitized query object or throw `AppCustomError(BAD_REQUEST, message)`
- Called at the start of handler methods before any service logic
- Responsible for: required field checks, normalization (uppercase, URL encoding), default values

### Data Transformation
- `ReshapeBikeAggregator.bikeAggregatorCalculator(price)` computes `other = onroadprice - sum(all fields except onroadprice and discount)`
- `CatalogService.filterRequiredFields(obj, allowedKeys)` removes keys not in the allowed list
- Applied per catalog item based on applicable definition matching

## Testing

### Framework & Config
- Jest with `ts-jest` preset
- Test environment: `node`
- Coverage collected automatically, output to `coverage/` directory
- Coverage reporter: Cobertura (for CI integration)

### Test Organization
- Tests live in `test/` subdirectories within each module (co-located)
- Mock objects in `test/mock/` directories
- Pattern: `{module-name}.test.ts`

### Mocking Strategy
- Manual mock objects for Express Request/Response (in `test/mock/`)
- `jest.fn()` for mocking service/implementer methods
- `jest.spyOn()` for verifying calls without replacing implementation
- No dependency injection — mocks replace singleton methods directly

### Running Tests
```bash
npm test              # Run all tests
npm run test-coverage # Run with coverage report
npm run coverage      # Jest coverage with Cobertura reporter
```

## Build & Development

### Scripts
```bash
npm run dev           # Development with nodemon + ts-node
npm run build         # TypeScript compilation (tsc)
npm start             # Run compiled JS (dist/src/server.js)
npm test              # Run Jest tests
npm run test-coverage # Jest with coverage
```

### Build Output
- TypeScript compiles to `dist/` directory
- Entry point after build: `dist/src/server.js`

## Deployment

### Environments
| Environment | Branch | Trigger |
|-------------|--------|---------|
| UAT | `uat` | Upstream AST pipeline completion |
| Production | `release` | Push to branch |

### Pipeline Steps (both environments)
1. `npm install`
2. `npm run build` (TypeScript compilation)
3. `npm test`
4. `npm run test-coverage`
5. Archive as zip
6. Publish build artifact

### Infrastructure
- Self-hosted Azure DevOps agent pool: `self-hosted-agent-pool-LeadsCapturingSystem`
- SonarQube integration (currently disabled in UAT pipeline)
- Quality gate breaking (currently disabled)

### Required Environment Variables
| Variable | Purpose |
|----------|---------|
| `API_SERVER_PORT` | Express server port |
| `SERVER_HOST_URL` | Express server host binding |
| `AZURE_CLIENT_ID` | Azure identity for Key Vault access |
| `AZURE_CLIENT_SECRET` | Azure identity for Key Vault access |
| `AZURE_TENANT_ID` | Azure identity for Key Vault access |
| `KEY_VAULT_NAME` | Azure Key Vault instance name |
| `AZURE_OAUTH_TOKEN_BASE_URL` | Azure AD token endpoint base URL |
| `CATALOG_MICRO_SERVICES_BASE_URL` | Downstream catalog service base URL |
| `HOST_NAME` | Swagger host display |

