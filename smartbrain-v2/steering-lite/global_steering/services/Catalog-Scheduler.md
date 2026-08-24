# Catalog-Scheduler


## Product Context


# Catalog Scheduler — Product Context

## What This Service Does

Catalog Scheduler is a batch processing service for **TVS Motor Company** that ingests vehicle pricing, product master data, and merchandise/accessories data from multiple external sources. It transforms, stores, and publishes this data to downstream systems that power consumer-facing channels (websites, aggregator platforms, dealer tools).

The service runs as **Azure Functions** on cron schedules and Service Bus triggers, orchestrating a multi-step ETL pipeline that keeps pricing and catalog data current across all TVS digital properties.

---

## Domain Entities

### Vehicle Prices (ICE & EV)
- Ex-showroom price, on-road price, FAME subsidy, software upgrade charges
- Scoped per **state × model × part × variant × color**
- Stored in `icePriceMasterData` and `evPriceMasterData` collections

### Discounts
- Time-bound discount offers per model and state
- Applied only when current date falls within `discountstartdate` → `discountenddate`
- Stored in `discounts` collection

### Products
- Vehicle product info from Shopify (specifications, images, active status)
- Stored in `products` collection

### Vehicle Product Master Data
- Canonical definitions: model, part, variant, color, brand, category, engine type
- Upserted by `modelId + partId` composite key
- Stored in `vehicleProductMasterData` collection

### Merchandise & Accessories (M&A)
- Non-vehicle products: riding gear, helmets, bags, accessories, vehicle care items
- Sourced from Shopify Admin API
- Classified as "Merchandise" or "Accessories" by tag matching
- Linked to applicable vehicle models via fuzzy model name matching
- Stored in `merchandiseAndAccessoriesProductPriceMasterData` collection

### Catalog Configurations
- Namespace-specific catalog definitions controlling which SKUs are visible on which channel
- Updated via Catalog Service API for each namespace

### Price Audit Logs
- Change tracking for all price updates (new, modified, deleted SKUs)
- Stored in `vehiclePriceAuditLog` and `merchandiseAndAccessoriesAuditLog`

### ORP Calculation Configurators
- Rules for on-road price calculation including cashback handling
- Stored in `orpCalculationConfigurators` collection

---

## External Integrations

| System | Purpose | Protocol |
|--------|---------|----------|
| **BumbleBee (Databricks/Azure Blob)** | Source of ICE prices, EV prices, discount data | HTTPS (SAS-signed blob URLs) |
| **Price Engine API** | On-road prices for ICE and EV vehicles | REST (OAuth2 client credentials) |
| **Shopify Admin API** | Product catalog data, M&A product listings | REST (X-Shopify-Access-Token) |
| **Catalog Service (internal)** | Update catalog configs, default catalogs, clear cache | REST (PUT/DELETE) |
| **Azure Service Bus** | Publish price change messages to downstream consumers | AMQP (topic/subscription) |
| **Azure Key Vault** | Secrets management (DB creds, API keys, SAS signatures) | Azure SDK (EnvironmentCredential) |
| **MongoDB Atlas** | Primary data store for all domain entities | mongodb+srv:// |

---

## Business Rules

### Price Ingestion
- Price data is merged from BumbleBee (Databricks) and Price Engine; **Price Engine takes precedence** for allowed model IDs per state (configured in `priceDataSourceConfig` collection)
- State name normalization handles inconsistencies (e.g., "CHHATTISGARH" → "CHHATISGARH", "GOA" → "GOA, DAMAN & DIU")
- A specific modelId (`000030000300000022`) is excluded from EV price publishing via Service Bus
- Price differences are detected by comparing ex-showroom price, FAME subsidy, and software upgrade fields
- Deleted SKUs (present in master but absent from temp) are removed and audit-logged

### Product Master
- Only **DOMESTIC** market, **TWO_WHEELER** industry, **EV** engine type products are accepted
- Upsert by composite key: `modelId + partId`

### Merchandise & Accessories
- Products with price `0.00` are skipped
- Product type determined by tag matching: merchandise tags → "Merchandise", accessories tags → "Accessories", default → "Merchandise"
- Vehicle model ID association uses fuzzy/partial string matching against known ICE + EV models
- Miscellaneous M&A data from `miscMAndAMasterData` is appended to the final dataset

### Namespace Visibility
- Applicable namespaces control which channels see which products
- Channels: TVS, BIKEDEKHO, BIKEWALE, 91WHEELS, HTAUTO, EVINDIA, PQC, MARKETPLACE, EVWEBSITE
- Some namespaces only receive EV data (HTAUTO, EVINDIA), others receive ALL

### Service Bus Messaging
- Messages are batched (configurable via `SERVICE_BUS_MESSAGE_COUNT` env var)
- Message deduplication by composite key: `modelId + partId + color + variant + state`
- Session-enabled with sessionId: `partId_state`



## Code Structure


# Catalog Scheduler — Project Structure

## Directory Layout

```
Catalog-Scheduler/
├── .kiro/steering/                         # Kiro steering files (this documentation)
├── src/
│   ├── functions/                          # Azure Function trigger definitions (entry points)
│   │   ├── product-price-ingestion-job.js  # Timer trigger — cron-scheduled price ETL
│   │   ├── product-master-ingestion-job.js # Service Bus topic trigger — event-driven master upsert
│   │   └── merchandise-accessories-ingestion-job.js  # Timer trigger — cron-scheduled M&A ETL
│   │
│   ├── product-price-ingestion-job/        # Core price ingestion business logic (26-step pipeline)
│   │   ├── index.js                        # Orchestrator — coordinates all steps sequentially
│   │   ├── constants/                      # Domain constants for this job
│   │   │   ├── catalog-constants.js        # Catalog types, secret key mappings, namespace applicability
│   │   │   ├── databricks-constants.js     # BumbleBee/Databricks secret key names
│   │   │   ├── db-constant.js             # MongoDB collection names, credential keys, limit constant
│   │   │   ├── name-spaces.js             # Channel namespace identifiers (TVS, BIKEDEKHO, etc.)
│   │   │   ├── active-applications.js     # Active status keys for filtering (PQC)
│   │   │   ├── image-keys.js             # Image-related constants
│   │   │   ├── pagination-constants.js    # Price Engine API pagination config
│   │   │   ├── price-engine-databricks-key-mapping.js  # Key mappings for price reshaping
│   │   │   ├── service-bus-constants.js   # Service Bus secret key names
│   │   │   └── shopify-constants.js       # Shopify-related constants
│   │   ├── data-sources/                   # External data fetching layer
│   │   │   ├── ice-data-source/           # BumbleBee ICE price fetching + reshaping
│   │   │   ├── discount-data-source/      # BumbleBee discount data fetching
│   │   │   ├── price-engine-data-source/  # Price Engine API (OAuth2 + pagination)
│   │   │   └── product-data-source/       # Shopify product data fetching
│   │   ├── db-connection/                  # Job-specific MongoDB collection operations
│   │   ├── catalog-service/                # Catalog API client
│   │   │   ├── catalog-service.js         # Default catalog updates, PQC categories, cache clear
│   │   │   └── catalog-config-service.js  # Catalog configuration updates per namespace
│   │   ├── wrapper-service/                # Data transformation utilities
│   │   ├── master-data/                    # Price master data insertion logic
│   │   └── price-updates/                  # Diff detection, bulk upserts, Service Bus publishing
│   │       └── price-updates.js           # Core: temp-vs-master diff, bulk update, delete, audit
│   │
│   ├── product-master-ingestion-job/       # Product master data ingestion (Service Bus triggered)
│   │   ├── index.js                        # Validates message, upserts to vehicleProductMasterData
│   │   └── validator.js                    # Market/engine/industry validation + field transformation
│   │
│   ├── merchandise-accessories-ingestion-job/  # M&A ingestion (cron-scheduled)
│   │   ├── index.js                        # Orchestrator — fetch, reshape, update master
│   │   ├── constants/
│   │   │   └── merchandise-accessories.js  # Brand tags, merchandise/accessories tag lists
│   │   ├── db-connection/                  # M&A-specific DB operations (audit log, catalog data)
│   │   │   ├── merchandise-accessories-master-db-coonection.js
│   │   │   └── price-master-db-connection.js
│   │   ├── merchandise-accessories-service/
│   │   │   ├── merchandise-accessories-implementer.js  # Shopify fetch, reshape, tag classification
│   │   │   └── merchandise-accessories-updates.js      # Temp-vs-master diff, delete stale, audit
│   │   └── wrapper-service/
│   │       └── vehicle-model-id-search.js  # Fuzzy model name → modelId resolution
│   │
│   ├── constants/                          # Shared constants
│   │   ├── db-constant.js                 # Shared collection names (being consolidated here)
│   │   └── generic-constants.js           # Market/engine/industry enums, string constants
│   │
│   ├── db-connection/                      # Shared MongoDB infrastructure
│   │   ├── db-configuration.js            # MongoClient connect/disconnect (Key Vault credentials)
│   │   └── master-data-db-connection.js   # Generic CRUD: insert, upsert, get, query, drop
│   │
│   ├── http/
│   │   └── http.js                        # Shared axios wrapper (get, post, put, del)
│   │
│   └── secrete-keys-service/
│       └── key-vault-secret.js            # Azure Key Vault secret retrieval
│
├── host.json                               # Azure Functions host config (unlimited timeout)
├── local.settings.json                     # Local dev environment variables
├── package.json                            # Dependencies and metadata
│
├── ci-dev-pipeline.yaml                    # CI: develop branch → build
├── cd-dev-pipeline.yaml                    # CD: develop branch → deploy to dev
├── ci-uat-pipeline.yaml                    # CI: uat branch → build
├── cd-uat-pipeline.yaml                    # CD: uat branch → deploy to UAT
├── ci-prod-pipeline.yaml                   # CI: release branch → build
├── cd-prod-pipeline.yaml                   # CD: release branch → deploy to prod
├── AST_CCP_Catalog_Service_Catalog_Scheduler_UAT_Pipeline.yml   # Security scans (UAT)
└── AST_CCP_Catalog_Service_Catalog_Scheduler_Release_Pipeline.yml  # Security scans (Prod)
```

---

## Module Dependencies

```
functions/ (entry points)
  ├── product-price-ingestion-job/index.js
  │     ├── data-sources/* (external API calls)
  │     ├── catalog-service/* (Catalog API updates)
  │     ├── wrapper-service/* (data transformation)
  │     ├── master-data/* (DB insertion)
  │     ├── price-updates/* (diff + Service Bus)
  │     ├── db-connection/ (shared MongoDB)
  │     └── secrete-keys-service/ (Key Vault)
  │
  ├── product-master-ingestion-job/index.js
  │     ├── validator.js
  │     ├── db-connection/ (shared MongoDB)
  │     └── constants/ (shared + price-job constants)
  │
  └── merchandise-accessories-ingestion-job/index.js
        ├── merchandise-accessories-service/*
        ├── db-connection/ (job-specific + shared)
        ├── wrapper-service/vehicle-model-id-search.js
        ├── http/ (shared)
        └── secrete-keys-service/ (Key Vault)
```

**Cross-module dependencies to note:**
- `product-master-ingestion-job` imports constants from `product-price-ingestion-job/constants/` (catalog-constants, db-constant)
- `merchandise-accessories-ingestion-job` imports from `product-price-ingestion-job/constants/db-constant.js`
- All jobs share `db-connection/db-configuration.js` for MongoDB connect/disconnect
- All jobs share `secrete-keys-service/key-vault-secret.js` for secrets
- All jobs share `http/http.js` for HTTP calls

---

## Architectural Decisions

### Modular by Job
Each ingestion job is a self-contained module with its own constants, DB operations, and services. This allows independent development and deployment of each pipeline.

### Shared Infrastructure Layer
Common concerns (DB connection, HTTP, Key Vault, generic constants) live in top-level `src/` directories and are imported by all jobs.

### Class-Based Singletons
Services are implemented as classes, instantiated once at module load, and exported as singleton instances. No dependency injection — direct `require()` throughout.

### Temp Collection Pattern
New data is written to temporary MongoDB collections, diffed against master collections using aggregation pipelines, then master is updated (upsert/delete) and temp is dropped. This ensures atomic-like updates and enables audit logging of changes.

### Sequential Orchestration
The price ingestion job runs 26 steps sequentially in a single function invocation. Each step is logged with a step number for debugging. No parallel execution within a job.

### No Retry/Circuit Breaker
Errors propagate up via `throw`. The Azure Functions runtime handles retries at the trigger level. No application-level retry logic or circuit breakers.

### Event-Driven Product Master
Unlike the cron-scheduled price and M&A jobs, product master ingestion is triggered by Service Bus messages, enabling real-time updates when upstream systems publish changes.



## Tech Stack & Dependencies


# Catalog Scheduler — Technical Reference

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Node.js |
| Framework | Azure Functions v4 (`@azure/functions ^4.6.1`) |
| Database | MongoDB Atlas (`mongodb ^6.3.0`, native driver) |
| HTTP Client | Axios (`^1.6.7`) wrapped in custom `Http` class |
| Secrets | Azure Key Vault (`@azure/keyvault-secrets ^4.8.0`) |
| Auth | Azure Identity (`@azure/identity ^4.0.1`, EnvironmentCredential) |
| Messaging | Azure Service Bus (`@azure/service-bus ^7.9.5`) |
| Utilities | Lodash (`^4.17.21`) for groupBy, data manipulation |
| Env Config | dotenv (`^16.4.4`) |
| CI/CD | Azure DevOps Pipelines (YAML) |
| Hosting | Azure Functions (consumption/premium plan) |

---

## Coding Conventions

### Module System
- **CommonJS** (`require` / `module.exports`) is the standard
- Exception: `generic-constants.js` and `merchandise-accessories.js` use ES module `export` syntax (inconsistency — treat CommonJS as the norm for new code)

### Service Pattern
- Classes with methods, instantiated once at module level, exported as singletons
- Example: `const myService = new MyService(); module.exports = myService;`
- No dependency injection; direct `require()` imports

### Naming
- Files: kebab-case (`price-engine-data-source.js`)
- Classes: PascalCase (`PriceEngineDataSource`)
- Variables/functions: camelCase (`getIceDataFromBumbleBee`)
- Constants objects: camelCase (`collectionNames`, `catalogs`)
- Environment variables: SCREAMING_SNAKE_CASE (`CRON_EXPRESSION_FOR_PRODUCT_PRICE_INGESTION_JOB`)

### Logging
- Use `context.log()` for info, `context.error()` for errors
- Step-by-step logging in orchestrators: `context.log("step N")`
- Log counts and operation results for observability

### No TypeScript
- Plain JavaScript throughout; no type annotations or `.d.ts` files

### No Tests
- No test framework or test files exist in the repository currently

---

## Patterns

### ETL Pipeline
Each job follows Extract → Transform → Load:
1. **Extract**: Fetch from external APIs (BumbleBee, Price Engine, Shopify)
2. **Transform**: Reshape, normalize, merge data from multiple sources
3. **Load**: Store in MongoDB, update Catalog Service, publish to Service Bus

### Temp-Then-Diff-Then-Upsert
1. Write fresh data to a temporary collection (`temp*` prefix)
2. Compare temp vs master using MongoDB aggregation `$lookup` pipelines
3. Identify new, modified, and deleted records
4. Bulk upsert changes to master collection
5. Delete stale records from master
6. Store audit log of all changes
7. Drop temporary collection

### Pagination
- Price Engine API is consumed with cursor-based pagination (`rowsPerPage` + `pageNumber`)
- Shopify M&A API uses `since_id` cursor pagination
- MongoDB operations use skip/limit with `limitConstant` (1000) for large collections

### Drop-and-Replace
- Some collections (`icePrices`, `evPrices`, `discounts`, `products`) are dropped and recreated each run
- Master collections (`icePriceMasterData`, `evPriceMasterData`, `mAndAMasterData`) use the diff pattern instead

### Bulk Operations
- MongoDB `bulkWrite` with `updateOne` + `upsert: true` for efficient mass updates
- `allowDiskUse: true` on aggregation pipelines for large datasets

---

## Error Handling

### General Approach
- `try/catch` blocks in service methods
- Errors are re-thrown (`throw error`) to propagate up to the function trigger
- Azure Functions runtime handles retry behavior based on trigger type
- No application-level retry logic, circuit breakers, or dead-letter handling

### Key Vault Errors
- `key-vault-secret.js` catches errors and logs them but does **not** re-throw (returns `undefined`)
- This can cause silent failures downstream — be aware when debugging

### HTTP Errors
- The `Http` class re-throws axios errors without transformation
- No request timeout configuration; relies on axios defaults

### Database Errors
- Connection errors are thrown and will fail the entire job
- Individual collection operations throw on failure

---

## Environment Configuration

### Required Environment Variables
```
# Database
DB_HOST                          # MongoDB Atlas cluster host
DB_NAME                          # Database name

# Azure
KEY_VAULT_NAME                   # Azure Key Vault name
FUNCTIONS_WORKER_RUNTIME=node

# APIs
CATALOG_BASE_URL                 # Internal Catalog Service base URL
PRICE_URL                        # Price Engine API base URL
AUTHORIZATION_TOKEN_URL          # OAuth2 token endpoint base URL
MERCHANDISE_ACCESSORIES_BASE_URL # Shopify store URL for M&A

# Service Bus
SERVICE_BUS_ENDPOINT             # Service Bus namespace endpoint
SERVICE_BUS_TOPIC_NAME           # Topic for price update messages
SERVICE_BUS_MESSAGE_COUNT        # Batch size for Service Bus sends
PRODUCT_MASTER_SERVICE_BUS_CONNECTION_STRING  # Connection string for product master trigger
PRODUCT_MASTER_TOPIC             # Topic name for product master messages
PRODUCT_MASTER_SUBSCRIPTION      # Subscription name for product master

# Scheduling
CRON_EXPRESSION_FOR_PRODUCT_PRICE_INGESTION_JOB   # Cron for price job
CRON_EXPRESSION_FOR_MERCHANDISE_ACCESSORIES_INGESTION_JOB  # Cron for M&A job
```

### Key Vault Secrets
```
mongo-user-name                  # MongoDB username
mongo-password                   # MongoDB password
BUMBLEBEE-ICE-SIGNATURE          # SAS signature for ICE blob
BUMBLEBEE-EV-SIGNATURE           # SAS signature for EV blob
BUMBLEBEE-DISCOUNT-SIGNATURE     # SAS signature for discount blob
CATALOG-TENANT-ID                # OAuth2 tenant ID
CATALOG-CLIENT-ID                # OAuth2 client ID
CATALOG-CLIENT-SECRET            # OAuth2 client secret
CATALOG-GRANT-TYPE               # OAuth2 grant type
CATALOG-SCOPE                    # OAuth2 scope
SERVICE-BUS-SHARED-ACCESS-KEY-NAME  # Service Bus SAS key name
SERVICE-BUS-SHARED-ACCESS-KEY       # Service Bus SAS key
MERCHANDISE-ACCESSORIES-ACCESS-TOKEN  # Shopify access token for M&A
```

---

## Deployment

### Environments & Branches
| Environment | Branch | CI Pipeline | CD Pipeline |
|-------------|--------|-------------|-------------|
| Dev | `develop` | `ci-dev-pipeline.yaml` | `cd-dev-pipeline.yaml` |
| UAT | `uat` | `ci-uat-pipeline.yaml` | `cd-uat-pipeline.yaml` |
| Prod | `release` | `ci-prod-pipeline.yaml` | `cd-prod-pipeline.yaml` |

### Pipeline Architecture
- CI triggers on branch push; CD triggers on successful CI completion
- Pipeline templates stored in external repo: `TVSM-Common-Support/ISSM_Websites_DevOpsSupport`
- Self-hosted agent pools (`$(AGENT_POOL_NAME)`) for dev; Azure Pipelines pool for security scans

### Security Scanning (UAT & Prod)
- Secret Detection Scan
- SCA/SBOM Scan (Software Composition Analysis)
- SAST Scan (Checkmarx)
- API Security Scan
- Stage status check gate

### Host Configuration
- Function timeout: unlimited (`"-1"` in host.json)
- Extension bundle: `Microsoft.Azure.Functions.ExtensionBundle [4.*, 5.0.0)`
- Application Insights sampling enabled (requests excluded)

---

## Development Setup

```bash
# Install dependencies
npm install

# Configure local environment
# Edit local.settings.json with required env vars (see above)

# Run locally
npm start  # runs `func start` (requires Azure Functions Core Tools)
```

### Prerequisites
- Node.js (version not pinned — use LTS)
- Azure Functions Core Tools v4
- Access to Azure Key Vault (requires `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` env vars for EnvironmentCredential)
- MongoDB Atlas connectivity

