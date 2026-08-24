# Core-Commerce-Platform-API-Service-Testng


## Product Context


# Product Context — Norton Motorcycles Core Commerce Platform API Tests

## What This Service Does

This is an **API test automation suite** for the Norton Motorcycles Core Commerce Platform. Norton Motorcycles is owned by TVS Motor Company. The test suite validates the Catalog Service APIs that power the e-commerce platform for motorcycle merchandise, parts, vehicles, and labour services.

The system under test exposes a RESTful API at `/norton/catalog-service/v2/catalogs/*` supporting multi-tenant, multi-market, multi-environment operations.

## Domain Entities

### Merchandise
Apparel and accessories (T-Shirts, Polo Shirts, Jackets, Gilets, Hard Goods) organized in a hierarchy:
- **Department** → Category → SubCategory → Variant (color + size)
- Each product has: partId, catalogSkuId, name, description, displayName, productInfo (size, MOQ), price, regionId, country

### Vehicles
2-Wheeler motorcycles in the catalog:
- catalogSkuId, partNumber, hierarchy (assembly, kit, catalogue, variant with variantPartId)
- Pricing: demo, display, stock, allocated price types

### Parts (EPC — Electronic Parts Catalogue)
Spare parts for vehicles:
- partId, partName, partNumber, catalogSkuId, partDescription
- Hierarchy: assemblyName → kitName → catalogueName → variantName → variantPartId
- Pricing: RP (Retail Price) and NDP (Net Dealer Price), each with netPrice + tax + totalPrice
- Warranty: type, duration, unit

### Labour
Service labour items with catalogSkuId and currency-based pricing.

## Integrations

- **Microsoft Azure AD (OAuth2)** — Token acquisition via `client_credentials` grant at `login.microsoftonline.com`
- **Norton Catalog Service API** — The system under test (dev/qa/uat/prod environments)
- **Allure Reporting** — Test results published as Allure reports
- **SAP** — Dealer lists and part IDs sourced from SAP (test data in `resources/data/`)

## API Endpoints Under Test

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/norton/catalog-service/v2/catalogs/merchandise` | Merchandise search with filters, sorting, pagination |
| GET | `/norton/catalog-service/v2/catalogs/labour` | Labour catalog listing |
| GET | `/norton/catalog-service/v2/catalogs/vehicles` | Vehicle catalog listing |
| GET | `/norton/catalog-service/v2/catalogs/allParts` | All parts (paginated) |
| GET | `/norton/catalog-service/v2/catalogs/parts/vehicleCatalogSkus/{skuId}` | Parts by vehicle SKU |
| GET | `/norton/catalog-service/v2/catalogs/parts/assemblies` | Master data for assemblies |
| GET | `/norton/catalog-service/v2/catalogs/search/part` | Part search by partNumber/catalogSkuId |

## Business Rules Validated

### Price Calculations (Merchandise)
- `netPrice = RRP - stdDiscount - addDiscount + freight`
- `tax = netPrice × taxPercent / 100`
- `totalPrice = netPrice + tax`

### Price Calculations (Parts)
- RP (Retail Price): `totalPrice = netPrice + tax`
- NDP (Net Dealer Price): `totalPrice = netPrice + tax`
- Tolerance: ±0.5 for floating-point comparison

### Pagination
- `totalPages = ceil(totalElements / size)`
- Returned records must not exceed requested page size
- No duplicate PartIds across paginated results

### Sorting
- **Name**: Case-insensitive alphabetical (ASC/DESC)
- **Price**: Numeric comparison on RRP (ASC/DESC)
- **Size**: Ranked ordering (XS=1, S=2, M=3, L=4, XL=5, XXL=6, XXXL=7, nXL=7+n) with apparel vs footwear type detection — mixed types are skipped

### Keyword Search
- Matches against product `name`, `description`, or `displayName` (case-insensitive contains)

### Hierarchy Filtering
- Department filter: all returned products must belong to the specified department (strict, case-insensitive)
- Category/SubCategory: validated when provided in the request

### Multi-Tenant / Multi-Market
- Namespace: NORTON
- Market: IB (International Business)
- Industry: 2Wheeler
- TenantId: UK-EU-N001, IT, GB (varies by environment)
- RegionId: numeric identifier (e.g., 123)

### Response Time
- All API responses must complete within configured threshold (default: 20000ms)



## Code Structure


# Project Structure — Core Commerce Platform API Test Suite

## Annotated Directory Layout

```
Core-Commerce-Platform-API-Service-Testng/
├── pom.xml                          # Maven build config (Java 11, TestNG, REST Assured, Allure)
├── .gitignore.txt                   # Git ignore rules
│
├── src/main/java/                   # Shared/legacy utilities (mostly unused)
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── Iconstants.java      # Legacy constants interface (minimal use)
│   │   │   └── CreatePostRequest.java # Legacy POST request helper
│   │   └── Routers/
│   │       └── Routers.java         # Legacy URL routing (placeholder)
│   ├── core/
│   │   └── ResponseValidator.java   # Reusable HTTP response validation (status, JSON, time)
│   └── genericUtilities/
│       └── GenericUtilities.java    # Legacy utility class (commented out)
│
├── src/test/java/                   # All active test code lives here
│   ├── base/
│   │   └── BaseTest.java           # @BeforeSuite setup, Allure listener registration
│   │
│   ├── core/                        # Test infrastructure
│   │   ├── ApiClient.java          # REST client wrapper (get/post via RestAssured specs)
│   │   └── Specs.java              # RequestSpec (baseUri, auth, logging) + ResponseSpec
│   │
│   ├── Pojo/                        # Request & Response DTOs
│   │   ├── CatalogRequest.java     # Main request body for merchandise search
│   │   ├── DepartmentRequest.java  # Department filter (name + categories)
│   │   ├── CategoryRequest.java    # Category filter (name + subcategories)
│   │   ├── SubCategoryRequest.java # SubCategory filter (name + variants)
│   │   ├── VariantRequest.java     # Variant filter (color + size)
│   │   ├── MerchandiseRequest.java # Alternate merchandise request (legacy)
│   │   ├── Pagination.java         # Pagination params (page, size)
│   │   ├── Sort.java               # Sort params (by, order)
│   │   ├── response/               # Merchandise response POJOs
│   │   │   ├── CatalogResponse.java    # Top-level response wrapper
│   │   │   ├── Category.java           # Product/item entity
│   │   │   ├── Price.java              # Price with RRP, currency, stock
│   │   │   ├── Stock.java              # Stock pricing breakdown
│   │   │   ├── PriceComponent.java     # Individual price component (value, percentage)
│   │   │   ├── Percentage.java         # Percentage value object
│   │   │   ├── Currency.java           # Currency code/name
│   │   │   └── ProductInfo.java        # Product metadata (size, MOQ)
│   │   └── Epc_partsresponse/      # Parts-specific response POJOs
│   │       ├── CatalogPartsResponse.java  # Parts response wrapper (paginated)
│   │       ├── PartsCategory.java         # Individual part entity
│   │       ├── PartsHierarchy.java        # Part hierarchy (assembly, model, vehicle)
│   │       ├── PartsPrice.java            # Parts pricing (RP + NDP)
│   │       ├── PartsPriceType.java        # Price type (netPrice, tax, totalPrice)
│   │       ├── PartsPriceComponent.java   # Numeric price value
│   │       └── PartsWarranty.java         # Warranty (duration, unit)
│   │
│   ├── tests/                       # Test classes
│   │   ├── Catalog_Testcases_ver1.java  # Main test class (~15 test methods)
│   │   └── test1.java                   # Experimental/scratch test
│   │
│   ├── utils/                       # Test utilities
│   │   ├── Config.java             # Environment-aware properties loader (-Denv=...)
│   │   ├── TokenManager.java       # OAuth2 token acquisition + caching
│   │   ├── RequestBuilder.java     # Fluent builder for CatalogRequest
│   │   ├── CatalogDataProvider.java # TestNG @DataProvider definitions
│   │   ├── AutoPaginationUtil.java # Multi-page fetcher with duplicate detection
│   │   └── SortValidator.java      # Sort order validation (name/price/size)
│   │
│   └── validators/                  # Business rule validators
│       ├── DefaultValidator.java        # Baseline response structure validation
│       ├── PaginationValidator.java     # Pagination metadata validation
│       ├── PriceValidator.java          # Price calculation validation (merchandise)
│       ├── HierarchyValidator.java      # Department/Category/SubCategory filter validation
│       ├── KeywordValidator.java        # Keyword search match validation
│       ├── DepartmentValidator.java     # Strict department filter validation
│       ├── CategoryValidator_Parts.java # Parts basic field validation
│       ├── Parts_PriceValidator.java    # Parts RP/NDP price calculation validation
│       ├── CategoryVariantValidator.java # Category + variant combination validation
│       └── FinalFilterValidator.java    # Combined filter validation
│
├── src/test/resources/
│   ├── config/                      # Environment-specific configuration
│   │   ├── Catalog_dev.properties   # Dev environment (dev-api.nortonmotorcycles.com)
│   │   ├── Catalog_qa.properties    # QA/UAT environment (uat-api.nortonmotorcycles.com)
│   │   ├── Catalog_Prod.properties  # Production environment
│   │   ├── Catalog_TrainingEnv.properties # Training environment
│   │   ├── config.properties        # Default/fallback config
│   │   ├── DB.properties            # Database connection config
│   │   └── EnvironmentConfig.properties # Environment selector
│   ├── data/                        # Test data files
│   │   ├── SapDealerlist.json       # SAP dealer list data
│   │   ├── Sappartids.json          # SAP part IDs for testing
│   │   ├── Proximity.json           # Proximity/location test data
│   │   └── User_Payload.json        # User request payload template
│   └── schemas/                     # JSON schema validation files
│       ├── masterdata.json          # Master data schema
│       └── AllLabourdata            # Labour data schema
│
├── Catalog/                         # Historical test result reports (HTML)
│   ├── Catalog_TestResults_070426 And 080426/
│   ├── Catalog_TestResults_090426/
│   └── Catalog_TestResults_130426/
│
├── PriceEngine/                     # Price Engine test result reports (HTML)
│   ├── PriceEngine_TestResults_080426/
│   ├── PriceEngine_TestResults_090426/
│   └── PriceEngine_TestResults_190426/
│
└── allure-results.zip               # Archived Allure results
```

## Module Dependencies

```
tests/Catalog_Testcases_ver1
    ├── extends base/BaseTest (Allure listener, suite init)
    ├── uses core/ApiClient (HTTP calls)
    │       └── uses core/Specs (request/response specifications)
    │               ├── uses utils/Config (environment config)
    │               └── uses utils/TokenManager (OAuth2 auth)
    ├── uses utils/RequestBuilder (request body construction)
    │       └── uses Pojo/* (request DTOs)
    ├── uses utils/CatalogDataProvider (@DataProvider test data)
    ├── uses utils/AutoPaginationUtil (multi-page fetching)
    ├── uses utils/SortValidator (sort order checks)
    └── uses validators/* (business rule assertions)
            └── uses Pojo/response/* (response DTOs)
```

## Architectural Decisions

1. **Single test class approach** — All catalog tests live in `Catalog_Testcases_ver1.java`. This is a pragmatic choice for a focused API test suite but may need splitting as tests grow.

2. **Validator separation** — Each business concern (price, sort, hierarchy, keyword, department) has its own validator class. This keeps test methods focused on orchestration while validators handle assertion logic.

3. **Dual serialization** — Gson for request serialization, Jackson for response deserialization. This is intentional: Gson handles the request builder pattern well, while Jackson's `@JsonIgnoreProperties` provides resilient response parsing.

4. **Environment-driven configuration** — The `-Denv` system property selects which `.properties` file to load, enabling the same test suite to run against dev, QA, UAT, training, or production.

5. **Token caching** — `TokenManager` caches OAuth2 tokens with expiry tracking (30s buffer) to avoid redundant token requests across tests.

6. **Legacy code preserved** — `src/main/java` contains mostly legacy/placeholder code from an earlier iteration. Active test infrastructure lives entirely in `src/test/java`.

7. **Allure-first reporting** — Tests are annotated with `@Epic`, `@Feature`, `@Story`, `@Severity` and use `Allure.step()` / `Allure.addAttachment()` extensively for rich test reports.



## Tech Stack & Dependencies


# Tech Stack & Conventions — Core Commerce Platform API Tests

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 11 (compiler target) |
| Build | Maven | 3.x (with Surefire 3.2.5) |
| Test Framework | TestNG | 7.10.2 |
| HTTP Client | REST Assured | 5.4.0 |
| JSON Serialization (requests) | Gson | 2.10.1 |
| JSON Deserialization (responses) | Jackson (databind + annotations) | 2.17.1 |
| Boilerplate Reduction | Lombok | 1.18.30 |
| Test Reporting | Allure | 2.24.0 |
| JSON Schema Validation | REST Assured JSON Schema Validator | 5.4.0 |
| Auth | Microsoft Azure AD OAuth2 (client_credentials) | — |

## Coding Conventions

### Naming
- Test classes: `{Feature}_Testcases_ver{N}.java` (e.g., `Catalog_Testcases_ver1`)
- Test methods: descriptive camelCase or snake_case mix (e.g., `get_vehicleDetails`, `validateMerchandise_CatalogFlow`)
- Validators: `{Concern}Validator.java` (e.g., `PriceValidator`, `HierarchyValidator`)
- Request POJOs: `{Entity}Request.java` in `Pojo` package
- Response POJOs: in `Pojo.response` or `Pojo.Epc_partsresponse` packages
- Data providers: named with `@DataProvider(name = "descriptiveName")`

### Package Structure
- `Pojo` — Request/response data transfer objects (note: uppercase P, non-standard but established)
- `core` — Infrastructure (API client, specs)
- `utils` — Utilities (config, token, builders, sort validation)
- `validators` — Business rule assertion classes
- `tests` — Test classes
- `base` — Base test class

### POJO Conventions
- Use `@Data` from Lombok for getters/setters/toString
- Use `@JsonIgnoreProperties(ignoreUnknown = true)` on all response POJOs for forward compatibility
- Some POJOs have both Lombok annotations and explicit getters (transitional state — prefer Lombok-only for new code)
- Request POJOs use public fields for Gson serialization; response POJOs use private fields with Lombok

### Test Method Structure
```java
@Test(dataProvider = "dataName", dataProviderClass = CatalogDataProvider.class)
@Story("Business scenario description")
@Severity(SeverityLevel.CRITICAL)
public void testMethodName(params...) {
    // Step 1: Build Request
    CatalogRequest req = RequestBuilder.baseRequest();
    RequestBuilder.addXxx(req, ...);

    // Step 2: API Call
    String body = new Gson().toJson(req);
    Response res = post("/norton/catalog-service/v2/catalogs/merchandise", body);

    // Step 3: Status Validation
    Assert.assertEquals(res.getStatusCode(), 200);

    // Step 4: Deserialize Response
    CatalogResponse response = res.as(CatalogResponse.class);

    // Step 5: Business Validations
    DefaultValidator.validate(response);
    PriceValidator.validate(response.getCategories());
    // ... more validators
}
```

## Patterns

### Request Specification Pattern
Centralized `Specs.request()` builds a `RequestSpecification` with:
- Base URI from config
- Content-Type: application/json
- Accept: application/json
- Relaxed HTTPS validation
- Bearer token from TokenManager
- Optional request/response logging

### Builder Pattern (RequestBuilder)
```java
CatalogRequest req = RequestBuilder.baseRequest();  // defaults: MERCHANDISE, IB, 2Wheeler, NORTON
RequestBuilder.addKeyword(req, keyword);
RequestBuilder.addDepartment(req, dept);
RequestBuilder.addFullHierarchy(req, dept, category, subCategory, color, size);
RequestBuilder.addSorting(req, sortBy, order);
RequestBuilder.addPagination(req, page, size);
```

### Data-Driven Testing
TestNG `@DataProvider` in `CatalogDataProvider` supplies test combinations:
- `sortData` — sort field + order combinations
- `catalogData_keywordandDept` — keyword + department filter combos
- `baseData` — sort + pagination only
- `keyword` — keyword-only filter scenarios
- `fullData` — complete hierarchy + keyword + sort + pagination
- `CategoryAndVaraint` — category + variant filter combos

### Validator Pattern
Each validator is a static utility class with a `validate()` method:
```java
public class PriceValidator {
    public static void validate(List<Category> products) { ... }
}
```
Validators use TestNG `Assert` for hard failures and `Allure.step()` / `Allure.addAttachment()` for reporting.

### Token Management
- OAuth2 client_credentials grant via Azure AD
- Token cached in-memory with expiry tracking (30s safety buffer)
- Lazy initialization on first API call
- Config-driven: tokenUrl, clientId, clientSecret, scope from properties

## Error Handling

- **Response validation**: `ResponseValidator.validateJsonResponse()` checks status code, non-empty body, and JSON content type
- **Response time**: Configurable threshold via `responseTimeMs` property (default 20000ms)
- **Null-safe price handling**: Price can be null — validators log warnings via Allure but don't fail on null prices (business-allowed case)
- **Token errors**: `TokenManager` throws `RuntimeException` with detailed error messages on auth failures
- **Config errors**: Missing config file throws `RuntimeException` at static initialization

## Testing Approach

### Test Categories
1. **GET endpoint tests** — Direct GET calls validating response structure (vehicles, labour, parts, assemblies)
2. **POST search tests** — Merchandise search with various filter/sort/pagination combinations
3. **Cross-API validation** — Fetch from one endpoint, validate via another (allParts → search/part)
4. **Pagination tests** — Page size limits, totalPages calculation, no duplicates across pages
5. **Sort validation** — Name/price/size ordering correctness
6. **Price calculation tests** — Mathematical validation of pricing formulas

### Assertions
- TestNG `Assert` for hard failures
- Hamcrest matchers for fluent assertions (via REST Assured)
- Custom validators for domain-specific business rules

### Reporting
- Allure annotations: `@Epic("Catalog API")`, `@Feature("Merchandise Filtering")`, `@Story("...")`
- `@Severity(SeverityLevel.CRITICAL)` on key tests
- `Allure.step()` for granular step-level reporting
- `Allure.addAttachment()` for request/response bodies and failure details
- `Allure.parameter()` for parameterized test visibility

## Running Tests

### Environment Selection
```bash
# Run against QA (default)
mvn test

# Run against Dev
mvn test -Denv=Catalog_dev

# Run against UAT
mvn test -Denv=Catalog_qa

# Run against Production
mvn test -Denv=Catalog_Prod

# Run against Training
mvn test -Denv=Catalog_TrainingEnv
```

### Allure Reports
```bash
# Results output to target/allure-results/
mvn test

# Generate and open report (requires allure CLI)
allure serve target/allure-results
```

## Configuration

Each environment properties file contains:
```properties
baseUrl=https://{env}-api.nortonmotorcycles.com
tokenUrl=https://login.microsoftonline.com/{tenantId}
clientId=...
clientSecret=...
scope=https://nmukdev.onmicrosoft.com/{env}-api-gw-internal/.default
responseTimeMs=20000
logRequests=true
tenantId=...
grant_type=client_credentials
```

## Key Considerations for New Code

- Always add `@JsonIgnoreProperties(ignoreUnknown = true)` to new response POJOs
- Use `RequestBuilder` for constructing requests — don't build CatalogRequest manually in tests
- Add `Allure.step()` calls in validators for report visibility
- Handle null prices gracefully — they are a valid business case
- Use `CatalogDataProvider` for new test data combinations
- New validators should follow the static `validate(List<Category> products, ...)` pattern
- Prefer Lombok `@Data` over manual getters/setters in new POJOs

