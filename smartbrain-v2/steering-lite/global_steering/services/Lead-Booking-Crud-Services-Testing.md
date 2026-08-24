# Lead-Booking-Crud-Services-Testing


## Product Context


# Product Context — Norton Motorcycles Booking Service Test Suite

## What This Service Does

This is an **API test automation suite** for the **Norton Motorcycles Booking Service** — a vehicle booking lifecycle management system operated by Norton Motorcycles (a TVS Motor Company subsidiary in the UK/EU market, tenant `UK-EU-N001`).

The suite validates two backend APIs:
- **Booking Service** (`/norton/booking-service/v2/...`) — end-to-end booking lifecycle
- **Master Data Platform (MDP)** (`/norton/mdp/v2/...`) — dealer, vehicle, labour, warranty reference data

---

## Domain Entities

### Booking
The central entity. Tracks a vehicle purchase from enquiry through delivery or cancellation.
- **type**: `online` (website/EV website) or `offline` (DMS/dealer-initiated)
- **bookingSource**: EMS, Website Reservation, EV Website, ICE Website
- **bookingStatus**: Reserved → Confirmed → Delivered (or Cancelled)
- Uses **optimistic concurrency control**: every mutation requires the current `uuid`, `checkSum`, and `version`

### Customer
- customerId, name, phone, email, gender, DOB
- customerConsentDate (GDPR-relevant for UK/EU)

### Dealer
- **sapDealerCode** — unique SAP identifier (e.g., `7500000231`)
- branchId, dealerPinCode
- **type** derived from `sapRawType`: N1→EXCLUSIVE, N2→MBO, N3→DISTRIBUTOR, Z1→EXCLUSIVE_DISTRIBUTOR, Z2→MBO_DISTRIBUTOR
- **mdpStatus**: ACTIVE
- **tenantId**: UK-EU-N001
- salesOrganization

### Vehicle
- partId, modelId, brandCode
- **vehicleType**: ICE (internal combustion) or EV (electric)
- model, variant, color
- onRoadPrice, exShowRoomPrice
- frameNumber, engineNumber (assigned at allocation)

### Payment
- paymentStatus (success), paymentType (full Payment / partial)
- isOnline (true/false), amountPaid, paymentMode (UPI / cash)
- paymentChannel (JUSPAY), paymentGateway (ccavenue)
- paymentId, paymentDate

### Invoice
- invoiceId, invoiceNumber, invoiceValue, invoiceDate
- invoiceSource (DMS), nameInInvoice, mobileNumberInInvoice, addressInInvoice

### Enquiry
- leadId, enquiryMode, enquiryType (digital), enquiryDate, enquirySource, enquiryNumber

### Reference Data (MDP)
- **Fault Types** — vehicle fault classifications
- **Warranty / Sub-Warranty** — warranty programs
- **Labour Tasks** — labourId, taskDescription, timeInMins, currency (GBP)

---

## Integrations

| System | Purpose | Auth |
|--------|---------|------|
| Norton API Gateway (Azure) | Hosts booking + MDP APIs | OAuth2 Client Credentials (Azure AD) |
| Microsoft Identity Platform | Token provider (`login.microsoftonline.com`) | client_id + client_secret + scope |
| DMS (Dealer Management System) | Source for offline bookings, invoices, allocations, gatepasses | Upstream data source |
| CRM | Booking retrieval by customer | Search via `/bookings/search` |
| JUSPAY / CCAvenue | Payment gateways for online payments | Referenced in payloads |
| SAP | Dealer master data (SAP dealer codes) | Via MDP API |

---

## Business Rules

### Booking Lifecycle (Happy Path)
1. **Create Booking** → returns `uuid`, `checkSum`, `version`
2. **Payment Update** → records payment, increments version
3. **Invoice Update** → attaches invoice, increments version
4. **Vehicle Allocation** → assigns frame/engine number, increments version
5. **Gatepass** → records delivery date, marks as delivered
6. Each step MUST pass the previous step's `checkSum` + `version` (optimistic locking)

### Reservation Flow (Online)
1. Create Booking (reservation) → status = `Reserved`
2. Vehicle Confirm (update partId/modelId) → status = `Confirmed`
3. Payment → Invoice → Allocation → Gatepass → status = `Delivered`

### Cancellation
- Can occur at any lifecycle stage
- Requires: cancellationSource, cancellationReason, cancellationSubReason
- Tracks: cancellationFee, refundAmount, customerRemarks
- Endpoint: PUT `/norton/booking-service/v2/bookings/cancel`

### Dealer Type Mapping
| sapRawType | Dealer Type |
|------------|-------------|
| N1 | EXCLUSIVE |
| N2 | MBO |
| N3 | DISTRIBUTOR |
| Z1 | EXCLUSIVE_DISTRIBUTOR |
| Z2 | MBO_DISTRIBUTOR |

### Validation Rules
- `brandCode` is required (null → rejection)
- Vehicle `partId` and `modelId` can be null for reservations (confirmed later)
- `bookingStatus` transitions must follow valid state machine
- All dealers must have `mdpStatus = ACTIVE` and `tenantId = UK-EU-N001`
- Labour currency must be `GBP`

### Pagination
- Cursor-based pagination: `?cursor=X&size=N`
- Response includes `data.hasMore` (boolean) and `data.nextCursor` (string)

### SLA Requirements
- Dev environment: 20 seconds max response time
- UAT/Training/Prod: 90 seconds max response time



## Code Structure


# Project Structure — Annotated Directory Layout

```
Lead-Booking-Crud-Services-Testing/
├── pom.xml                              # Maven build: Java 11, TestNG, REST Assured, Jackson, POI, Allure
├── booking.csv.txt                      # Scratch/notes file (not used in automation)
│
├── src/main/java/                       # ⚠️ LEGACY — mostly commented-out code from earlier iteration
│   ├── api/Routers/Routers.java         #   Route constants (unused)
│   ├── api/endpoints/                   #   Old request builders (commented out)
│   │   ├── CreatePostRequest.java
│   │   └── Iconstants.java
│   └── genericUtilities/
│       └── GenericUtilities.java        #   Old JSON utilities (commented out)
│
└── src/test/                            # ✅ ACTIVE CODE — all test automation lives here
    ├── java/
    │   ├── base/
    │   │   └── BaseTest.java            # @BeforeSuite: prints active env, global setup hook
    │   │
    │   ├── core/                        # Framework infrastructure
    │   │   ├── ApiClient.java           # Static HTTP methods: get(), post(), put()
    │   │   └── Specs.java               # RequestSpec (baseUri, auth, logging) + ResponseSpecs (200, SLA)
    │   │
    │   ├── Pojo/                        # Request body POJOs and helpers
    │   │   ├── DealerType.java          # Simple POJO: { "type": "MBO" }
    │   │   ├── DealercodeandVechicalparts.java  # List<String> sapDealerCodes wrapper
    │   │   └── Pagenationsize.java      # Cursor-based pagination client (fetches all pages)
    │   │
    │   ├── models/
    │   │   └── User.java                # ⚠️ Legacy POJO (unused)
    │   │
    │   ├── tests/                       # Test classes — one per environment × flow type
    │   │   ├── BookingDevOffline.java         # Dev: Offline booking lifecycle
    │   │   ├── BookingDevOnline.java          # Dev: Online booking lifecycle
    │   │   ├── BookingOnlineUAT.java          # UAT: Online booking lifecycle
    │   │   ├── BookingUATOffline.java         # UAT: Offline booking lifecycle
    │   │   ├── BookingTrainingOffline.java    # Training: Offline booking lifecycle
    │   │   ├── BookingTrainingOnline.java     # Training: Online booking lifecycle
    │   │   ├── BookingProdOffline.java        # Prod: Offline booking lifecycle
    │   │   ├── BookingProdOnline.java         # Prod: Online booking lifecycle
    │   │   ├── BookingReservationFlowTest.java  # Reservation workflow + negative cases
    │   │   ├── BookingSearchTest.java         # Data-driven search (Excel-powered)
    │   │   └── GetUsersTest.java              # MDP tests: dealers, labour, warranty, pagination
    │   │
    │   └── utils/                       # Shared utilities
    │       ├── Config.java              # Properties loader (env-aware via -Denv system property)
    │       ├── TokenManager.java        # OAuth2 token acquisition + in-memory caching
    │       ├── Db.java                  # JDBC utility (connect/query/close) — configured but rarely used
    │       ├── ExcelDataProvider.java   # TestNG @DataProvider backed by Excel
    │       ├── Excelreader.java         # Apache POI: reads .xlsx → List<Map<String,String>>
    │       ├── Dataprovider.java        # TestNG @DataProvider backed by JSON
    │       ├── JsonReader.java          # Simple file → String reader
    │       └── jsondatareder.java       # Jackson: reads JSON array by key (e.g., SapDealerIds)
    │
    └── resources/
        ├── BookingTestCases.xlsx        # Excel test data for BookingSearchTest
        ├── config/                      # Environment-specific properties files
        │   ├── Bookingdev.properties    #   Dev: dev-api.nortonmotorcycles.com (20s SLA)
        │   ├── BookingQa.properties     #   UAT: uat-api.nortonmotorcycles.com (90s SLA)
        │   ├── BookingTraining.properties  # Training: training-api.nortonmotorcycles.com (90s SLA)
        │   └── BookingProd.properties   #   Prod: api.nortonmotorcycles.com (90s SLA)
        ├── data/                        # JSON payload templates (~42 files)
        │   ├── CreateBooking*.json      #   Booking creation payloads (per env)
        │   ├── OfflineBooking*.json     #   Offline booking payloads (per env)
        │   ├── paymentupdate*.json      #   Payment update payloads
        │   ├── InvoiceUpdate*.json      #   Invoice update payloads
        │   ├── AllocationUpdate*.json   #   Vehicle allocation payloads
        │   ├── Gatepass*.json           #   Gatepass/delivery payloads
        │   ├── Cancellation*.json       #   Cancellation payloads
        │   ├── vehicleUpdate*.json      #   Vehicle confirm/negative test payloads
        │   ├── CreateReservationBooking.json  # Reservation flow template
        │   ├── CustomerRetreival.json   #   CRM search payload
        │   └── bookingSearchPayload.json  # Search template with DEALER_IDS placeholder
        └── schemas/                     # JSON Schema files for response validation
            ├── faultdataschema.json
            ├── SubwarrentyData.json
            └── Warrentydata.json
```

---

## Module Dependencies

```
tests/* ──→ core/ApiClient ──→ core/Specs ──→ utils/Config
                                    │              │
                                    └──→ utils/TokenManager ──→ utils/Config
tests/* ──→ base/BaseTest (inheritance)
tests/* ──→ Pojo/* (request bodies)
tests/* ──→ utils/ExcelDataProvider ──→ utils/Excelreader
tests/* ──→ utils/jsondatareder (JSON data files)
tests/* ──→ utils/JsonReader (payload templates)
```

### Dependency Flow
1. **Config** is the root — loads environment properties at class-load time
2. **TokenManager** depends on Config for OAuth2 credentials
3. **Specs** depends on Config (baseUrl, SLA) and TokenManager (auth header)
4. **ApiClient** depends on Specs (request specification)
5. **Test classes** depend on ApiClient + data utilities

---

## Architectural Decisions

### Environment-per-Class Pattern
Each environment (Dev/UAT/Training/Prod) × flow type (Online/Offline) has its own test class. This results in code duplication but provides:
- Independent execution per environment
- Environment-specific JSON payloads (different dealer IDs, pricing, dates)
- Clear TestNG reporting per environment

### Stateful Sequential Tests
Tests within a workflow class use `dependsOnMethods` to chain steps. Instance variables carry `uuid`, `checkSum`, and `version` between steps. This mirrors the real booking lifecycle where each mutation depends on the previous state.

### Template-Based Payloads
JSON files in `src/test/resources/data/` serve as templates with placeholders (`UUID`, `CHECKSUM`, `VERSION`, `CUSTOMER_NAME`, `PHONE_NUMBER`). Tests read these files and perform string replacement at runtime.

### Centralized Auth
Token acquisition is handled once by `TokenManager` (with caching) and injected into all requests via `Specs.request()`. Tests never manage tokens directly.

### Legacy src/main/java
The `src/main/java` directory contains commented-out code from an earlier approach. It is not used by any active tests and can be considered dead code.

### No Dependency Injection
Despite Guice being declared in pom.xml, the project uses static utility classes and direct instantiation. There is no DI container wiring.



## Tech Stack & Dependencies


# Tech Stack & Conventions

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 11 (compiler target) |
| Build | Maven | 3.x (wrapper not included) |
| Test Framework | TestNG | 7.10.2 |
| HTTP Client | REST Assured | 5.4.0 |
| JSON Serialization | Jackson (databind + annotations) | 2.17.1 |
| JSON Processing | org.json, json-simple, Gson | 20240303, 1.1.1, 2.10.1 |
| Excel Reading | Apache POI (poi-ooxml) | 5.2.2 |
| Reporting | Allure TestNG | 2.24.0 |
| Schema Validation | REST Assured JSON Schema Validator | 5.4.0 |
| Logging | SLF4J Simple | 2.0.9 |
| Code Generation | Lombok | 1.18.20 (declared, minimally used) |
| DI Framework | Guice | 5.0.1 (declared, not actively used) |
| Database | JDBC (driver not specified in pom) | — |

---

## Coding Conventions

### Naming
- **Packages**: lowercase (`tests`, `utils`, `core`, `base`), except `Pojo` (non-standard)
- **Classes**: PascalCase — some inconsistencies exist (`jsondatareder`, `Pagenationsize`)
- **Test methods**: mixed — some use `camelCase`, others `PascalCase_With_Underscores`
- **Variables**: camelCase, occasional uppercase starts (`Delares`, `Labourids`)

### Package Organization
- `core/` — framework infrastructure (ApiClient, Specs)
- `utils/` — shared utilities (Config, TokenManager, data readers)
- `Pojo/` — request body POJOs and helper classes
- `tests/` — all test classes
- `base/` — test base class with suite-level setup

### File Naming for Test Data
- Environment suffix pattern: `*Dev.json`, `*Prod.json`, `*Training.json`
- Reservation suffix: `*Reservation.json`
- Negative test suffix: `*_negative.json`, `*_brandNull.json`, `*_modelEmpty.json`

---

## Patterns

### API Client Pattern
Static methods on `ApiClient` wrap REST Assured calls with pre-configured specs:
```java
ApiClient.get("/path")      // GET with auth + base URI
ApiClient.post("/path", body)  // POST with JSON body
ApiClient.put("/path", body)   // PUT with JSON body
```

### Request/Response Specification
`Specs.java` provides reusable specifications:
- `Specs.request()` — base URI, content type, auth token, optional logging
- `Specs.responseOK()` — expects 200 + JSON content type
- `Specs.responseTimeUnder()` — SLA assertion (configurable per env)

### Optimistic Concurrency Control
Every booking mutation follows this pattern:
1. Extract `checkSum`, `version`, `uuid` from previous response
2. Inject into next request payload
3. API validates these match current state before applying changes

### Stateful Workflow Chaining
```java
@Test(description = "Step 1")
public void CreateBooking() { /* stores uuid, checksum, version */ }

@Test(dependsOnMethods = {"CreateBooking"})
public void PaymentUpdate() { /* uses stored metadata, updates it */ }
```

### Template Payload Pattern
```java
String payload = readFile("template.json");
payload = payload.replace("UUID", uuid);
payload = payload.replace("CHECKSUM", checksum);
payload = payload.replace("VERSION", String.valueOf(version));
```

### Dynamic Test Data
Customer name and phone are randomized per run to avoid conflicts:
```java
String name = "Cust_" + (int)(Math.random() * 100000);
String phone = "9" + (90000000 + (int)(Math.random() * 80000000));
```

### Bracket Trimming
API sometimes returns values wrapped in arrays. Helper method handles this:
```java
private String trimBrackets(String s) {
    if (s.startsWith("[") && s.endsWith("]"))
        return s.substring(1, s.length() - 1).trim();
    return s;
}
```

---

## Error Handling

### Tolerant Status Validation
Tests accept multiple success codes rather than strictly 200:
```java
if (!(status == 200 || status == 201 || status == 202 || status == 204)) {
    Assert.fail("API failed. Status=" + status);
}
```

### Graceful SLA Failures
Response time assertions are wrapped in try-catch — SLA violations are logged but don't fail the test:
```java
try { res.then().spec(Specs.responseTimeUnder()); }
catch (AssertionError e) { System.out.println("SLA: " + e.getMessage()); }
```

### Null-Safe JSON Extraction
Multiple JSON paths are tried with fallback:
```java
private String getValueFromJsonPaths(Response res, String... paths) {
    for (String p : paths) {
        Object v = res.jsonPath().get(p);
        if (v != null) return String.valueOf(v).trim();
    }
    return null;
}
```

### Token Acquisition
- Fallback to 3600s expiry if `expires_in` is missing or unparseable
- Throws `RuntimeException` if `access_token` is null in response
- 30-second buffer before expiry to avoid edge-case failures

---

## Testing Approach

### Test Types
1. **Workflow Tests** (BookingDev/UAT/Training/Prod Online/Offline) — sequential lifecycle validation
2. **Reservation Flow Tests** (BookingReservationFlowTest) — reservation-specific lifecycle + negative cases
3. **Data-Driven Tests** (BookingSearchTest) — Excel-powered parameterized search validation
4. **Reference Data Tests** (GetUsersTest) — MDP endpoint validation with schema checks

### Data Sources
- **JSON files** — payload templates in `src/test/resources/data/`
- **Excel** — `BookingTestCases.xlsx` for search test parameters
- **JSON data files** — `SapDealerlist.json` for dealer code lists

### Assertions
- Status code validation (tolerant: 200/201/202/204)
- Response time SLA (soft assertion)
- JSON Schema validation (for MDP endpoints)
- Field-level equality checks (dealer type mapping, currency, descriptions)
- List containment checks (all expected dealers present)
- State transition validation (booking status progression)

### Negative Testing
- Null `brandCode` → expects non-200 response
- Missing `partId`/`modelId` → validates error handling
- Invalid `bookingStatus` → expects rejection
- Empty dealer IDs in search → expects empty result or error message

---

## Environment Configuration

### Switching Environments
Pass `-Denv=<name>` to Maven/TestNG:
```bash
mvn test -Denv=Bookingdev      # Default
mvn test -Denv=BookingQa       # UAT
mvn test -Denv=BookingTraining # Training
mvn test -Denv=BookingProd     # Production
```

### Properties File Structure
Each `config/<env>.properties` contains:
- `baseUrl` — API gateway URL
- `tokenUrl` — Azure AD token endpoint
- `clientId` / `clientSecret` / `scope` — OAuth2 credentials
- `responseTimeMs` — SLA threshold in milliseconds
- `logRequests` — enable/disable request/response logging

---

## Build & Execution

### Build
```bash
mvn clean compile
```

### Run All Tests (Default: Dev)
```bash
mvn test
```

### Run Specific Test Class
```bash
mvn test -Dtest=BookingDevOnline
mvn test -Dtest=GetUsersTest
```

### Run Against Specific Environment
```bash
mvn test -Denv=BookingQa -Dtest=BookingOnlineUAT
```

### Generate Allure Report
```bash
mvn allure:serve
```

---

## Key Conventions to Follow

1. **New test payloads** go in `src/test/resources/data/` with environment suffix
2. **New environment configs** go in `src/test/resources/config/<EnvName>.properties`
3. **All HTTP calls** should go through `ApiClient` — never use `given()` directly in tests (except BookingSearchTest/ReservationFlowTest which predate this convention)
4. **Workflow tests** must use `dependsOnMethods` and propagate `uuid`/`checkSum`/`version`
5. **Response validation** should use `Specs.responseOK()` and `Specs.responseTimeUnder()`
6. **Token management** is automatic — never manually acquire tokens in test code
7. **JSON payloads** use placeholder strings for dynamic values, replaced at runtime

