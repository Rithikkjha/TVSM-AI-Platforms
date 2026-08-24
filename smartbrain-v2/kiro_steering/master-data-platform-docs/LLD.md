# MDP — Low Level Design (SmartBrain AI Format)

> **Service:** Master Data Platform (MDP)
> **Version:** 2.0
> **Last Updated:** July 2026
> **Source of truth:** Code in `src/main/java/com/tvsmotor/mdp/`

---

## Code Structure

```
master-data-platform/
├── src/main/java/com/tvsmotor/mdp/
│   ├── MdpApplication.java                 # Bootstrap (@EnableCaching, @EnableScheduling, @EnableRetry)
│   ├── aop/                                # Cross-cutting aspects
│   │   ├── annotations/                    # @Authorization, @DisableOnProd, @Timed
│   │   ├── AuthorizationAspect.java        # Client allow-list enforcement
│   │   ├── DisableOnProdAspect.java        # Block diagnostic endpoints in prod
│   │   └── TimedAspect.java               # Method-level latency logging
│   ├── common/                             # Shared infrastructure
│   │   ├── batch_processing/              # BatchProcessingService, BatchJobProcessorFactory
│   │   ├── cache/CacheService.java        # Redis ops (@Retryable 3 attempts, multiGet batched)
│   │   ├── config/                        # CustomConfiguration
│   │   ├── entity/AuditLog.java           # API call + exception audit entity
│   │   ├── enums/                         # CacheName(10), AuditLogType(50+), PipelineSource
│   │   ├── exceptions/                    # RestExceptionHandler, ValidationException, AccessDeniedException
│   │   ├── model/                         # ServiceBus incoming message models
│   │   ├── repository/                    # AuditLog repository
│   │   ├── service/                       # AuditLogService, AsyncJobService, ParallelJobExecutor,
│   │   │                                  # JsonHelperService, ServiceBusMessageConsumer interface
│   │   └── utils/                         # Context (thread-local), GeneralUtils, Constants
│   ├── config/                             # Configuration classes
│   │   ├── MdpOncePerRequestFilter.java   # JWT parsing, client resolution, Context setup
│   │   ├── DealerMasterServiceBusConfig.java  # 2 sender + 2 processor clients
│   │   ├── DmsDatabaseConfig.java         # MSSQL read-only datasource
│   │   ├── OkHttpClientConfig.java        # Outbound HTTP client + timeouts
│   │   └── LatLongBrandCreds.java         # 8 brand credentials for LatLong API
│   ├── controller/                         # REST controllers
│   │   ├── DealerController.java          # Dealer read APIs (8 endpoints)
│   │   ├── DealerFlagsNewController.java  # Per-dealer flag CRUD (SYSTEM)
│   │   ├── DealerFlagsTypeNewController.java # Flag type management (SYSTEM)
│   │   ├── DealerKnowlarityDataController.java # K-number map/unassign (MDP_BFF)
│   │   ├── DE_PipelineController.java     # ADF batch trigger (9 types)
│   │   ├── LatLongDetailsController.java  # LatLong sync trigger (SYSTEM)
│   │   ├── TestController.java            # Health/test endpoints
│   │   ├── TestServiceBusController.java  # SB start/stop/push (SYSTEM)
│   │   └── migration/                     # DealerMigrationController, DMSMigrationController
│   ├── dealer/                             # Dealer SB model DTOs
│   │   └── model/service_bus/             # DmsDealerData, DmsBranchData
│   ├── entity/                             # JPA entities (dealer domain)
│   │   ├── Dealer.java                    # Core dealer entity (@Audited)
│   │   ├── DealerDetails.java            # Name, GST, operating hours, K-numbers, DTR/HTR
│   │   ├── DealerLocation.java           # Address, pincode, lat/long, zone/territory
│   │   ├── DealerContact.java            # Phone, email per type (MAIN/EV/ICE)
│   │   ├── DealerEmployee.java           # Personnel (name, type, active, deleted)
│   │   ├── DealerFlag.java               # Legacy enum-based flags
│   │   ├── DealerFlagNew.java            # Scalable FK-based flags
│   │   ├── DealerFlagTypeNew.java        # Flag definitions (soft-delete)
│   │   ├── DealerTestRideVehicle.java    # Test ride inventory
│   │   ├── AuthClientUser.java           # OAuth client → MdpClient mapping
│   │   ├── BaseEntityWithId.java         # id, createdAt/updatedAt, createdBy/updatedBy, @Version
│   │   ├── CommonBaseEntity.java         # Shared base (@PrePersist/@PreUpdate)
│   │   └── DealerDependentEntity.java    # Base for dealer-FK entities
│   ├── enums/                              # Domain enums
│   │   ├── MdpClient.java                # SYSTEM, ADF, MDP_BFF
│   │   ├── DealerType.java               # AMD, SPD, APS, BRANCH, AD
│   │   ├── DealerFlagType.java           # 45 flag types (enum)
│   │   ├── SapStatus.java                # PRE_ACTIVE, ACTIVE, PERMANENTLY_BLOCKED, NOT_PRESENT_IN_SAP, TEMPORARILY_BLOCKED
│   │   ├── DmsStatus.java                # PRE_ACTIVE, ACTIVE, INACTIVE
│   │   ├── MdpDealerStatus.java          # PRE_ACTIVE, ACTIVE, INACTIVE
│   │   ├── DealerLocationType.java       # MAIN, SALES, SERVICE
│   │   ├── DealerContactType.java        # MAIN, SHOWROOM_ICE, SHOWROOM_EV
│   │   ├── DealerEmployeeType.java       # MANAGER, DSE, SHOWROOM_MANAGER, OTHER
│   │   ├── service_bus/ServiceBusEventType.java  # DEALER_CREATED, DEALER_UPDATED, ONE_TIME_MIGRATION
│   │   └── batch_processing/BatchProcessingType.java  # 9 types
│   ├── model/                              # DTOs (request, response, redis)
│   ├── repository/                         # JPA repositories (dealer domain)
│   ├── service/                            # Business logic
│   │   ├── DealerOperationsService.java   # Dealer mutation orchestration
│   │   ├── DealerApisOperationsService.java # Read-side search/filter/proximity
│   │   ├── DealerCacheService.java        # Redis cache (@Retryable 5 attempts)
│   │   ├── DealerService.java             # Core dealer persistence
│   │   ├── DealerBranchOperationsService.java # Branch-specific logic
│   │   ├── DealerFlagsOperationsService.java  # Flag CRUD
│   │   ├── DmsDealerOperationalService.java   # DMS migration orchestration
│   │   ├── LatLongService.java            # Geo-coordinate resolution (8 brands)
│   │   ├── batch_processing/              # ADF pipeline processors (9 types)
│   │   ├── service_bus/                   # DealerDataConsumerService, DmsDataConsumerService,
│   │   │                                  # DealerDataSenderService, DealerDataGeneratorService,
│   │   │                                  # TestServiceBusService
│   │   ├── migration/                     # DealerDataMigrator, DealerStatusMigrator,
│   │   │                                  # DmsDealerDataMigrator, DmsBranchDataMigrator,
│   │   │                                  # DmsEmployeeDataMigrator
│   │   └── notification_service/          # DealerOnboardingEmailNotificationService
│   ├── product/                            # Vehicle product module (self-contained)
│   │   ├── controller/ProductVehicleController.java  # 3 endpoints
│   │   ├── controller/ProductMigrationController.java # engine_type migration
│   │   ├── entity/VehicleModel.java       # model_id, sapModelId, market, industry, engineType
│   │   ├── entity/VehiclePart.java        # part_id, sapPartId, color, availabilityStatus
│   │   ├── entity/VehiclePartSpecifications.java # engineCapacity, power, weight, batteryCapacity
│   │   ├── enums/                         # VehicleMarket, VehicleIndustry, VehicleEngineType, AvailabilityStatus
│   │   └── service/, repository/, config/, cache/
│   ├── product_mna/                        # Product MnA module
│   │   ├── controller/ProductMnaController.java  # 2 endpoints (legacy + v2)
│   │   ├── entity/ProductMna.java         # sapSkuId, description
│   │   ├── entity/ProductMnaNew.java      # sapPartNo + 20 fields (class, cate, supplier, moq, hsn, pricing, etc.)
│   │   └── service/, repository/
│   ├── product_part/                       # Parts master module
│   │   ├── controller/PartController.java # 1 endpoint
│   │   ├── entity/Part.java              # sapPartId, division, materialType, grossWeight, etc.
│   │   ├── entity/PartMarket.java        # partId FK, market, minOrderQuantity
│   │   └── service/, repository/
│   ├── price/                              # Vehicle pricing module
│   │   ├── controller/PriceVehicleController.java # 2 endpoints
│   │   ├── entity/PriceVehicleModel.java  # sapModelId, locationId FK, exShowroomPrice, exFactoryPrice
│   │   ├── entity/PriceLocationDetail.java # state, country, currency
│   │   ├── enums/Currency.java
│   │   └── service/, repository/
│   ├── part_price/                         # Part pricing module
│   │   ├── controller/PartPriceController.java # 1 endpoint (country=IN only)
│   │   ├── entity/PartPrice.java          # sapPartId, price (BigDecimal), currency
│   │   └── service/, repository/
│   └── utils/                              # JWTUtil, FlagUtils, ValidationUtilityService
├── src/main/resources/
│   ├── application.properties              # Base config (all ${ENV_VAR} placeholders)
│   ├── application-{local,dev,uat,prod}.properties
│   ├── db/migration/                       # Forward-only SQL migrations (v1.1 → v1.44+)
│   └── logback-spring.xml
├── src/test/                               # JUnit 4 + Mockito Inline + H2
├── Dockerfile                              # Multi-stage (maven:3.9.x-corretto-17 → corretto:17)
├── docker-compose.yml                      # Local MySQL + Redis
└── pom.xml                                 # Spring Boot 3.5.16, Java 17
```

---

## Database Schema

### Core Dealer-Domain Tables

| Table | Entity Class | Purpose | Key Columns |
|-------|-------------|---------|-------------|
| `dealers` | `Dealer` | Dealer master record | `sap_dealer_code` (UK), `dms_status`, `sap_status`, `mdp_status`, `type` (AMD/SPD/APS/BRANCH/AD), `parent_amd_id`, `parent_aps_id`, `old_sap_dealer_code` |
| `dealer_details` | `DealerDetails` | Name, GST, hours, K-numbers, DTR/HTR config | FK `dealer_id`, `name`, `branch_name`, `gst_number`, `knowlarity_virtual_number`, `knowlarity_routing_cli`, `knowlarity_fallback_number`, DTR/HTR start dates & caps per platform (Default/IQUBE/TVSX/U546), offline booking caps |
| `dealer_locations` | `DealerLocation` | Address, geo-coordinates | FK `dealer_id`, `type` (MAIN/SALES/SERVICE), `pincode`, `city`, `city_code`, `state`, `country`, `territory`, `area`, `zone`, `region`, `latitude`, `longitude`, `google_maps_url`, `google_plus_code` |
| `dealer_contacts` | `DealerContact` | Phone, email per contact type | FK `dealer_id`, `type` (MAIN/SHOWROOM_ICE/SHOWROOM_EV), `primary_phone_number`, `secondary_phone_number`, `email_address` |
| `dealer_employees` | `DealerEmployee` | Personnel records | FK `dealer_id`, `full_name`, `type` (MANAGER/DSE/SHOWROOM_MANAGER/OTHER), `manager_id` (self-FK), `phone_number`, `email_address`, `is_active`, `is_deleted` |
| `dealer_flags` | `DealerFlag` | Legacy enum-based flags | FK `dealer_id`, `name` (DealerFlagType enum, 45 values), `is_enabled` (0/1). UK on (dealer_id + name) |
| `dealer_flags_new` | `DealerFlagNew` | Scalable FK-based flags | FK `dealer_id`, FK `flag_type_id`, `is_enabled` (0/1) |
| `dealer_flag_types_new` | `DealerFlagTypeNew` | Flag type definitions | `name` (UK), `is_deleted` |
| `dealer_test_ride_vehicles` | `DealerTestRideVehicle` | Test ride vehicle inventory | FK `dealer_id` |
| `auth_client_users` | `AuthClientUser` | OAuth client → MdpClient mapping | `client_id`, `user_type` |
| `audit_log` | `AuditLog` | API call + exception + domain audit | `type` (AuditLogType, 50+ values), `message`, `exception` |

### Product/Price/Part Tables

| Table | Entity Class | Purpose | Key Columns |
|-------|-------------|---------|-------------|
| `vehicle_models` | `VehicleModel` | Vehicle model catalog | `model_id` (PK), `sap_model_id`, `model_name`, `market` (VehicleMarket), `industry` (VehicleIndustry), `engine_type` (VehicleEngineType), `availability_status`, `brand`, `category` |
| `vehicle_parts` | `VehiclePart` | Vehicle parts | `part_id` (PK), FK `model_id`, `sap_part_id`, `part_name`, `part_description`, `color`, `availability_status` |
| `vehicle_part_specifications` | `VehiclePartSpecifications` | Part specs | `specifications_id` (PK), FK `part_id`, `engine_capacity`, `power`, `weight`, `battery_certified_capacity` (all BigDecimal) |
| `price_vehicle_model` | `PriceVehicleModel` | Vehicle pricing | `sap_model_id`, FK `location_id`, `ex_showroom_price`, `ex_factory_price` (BigDecimal) |
| `price_location_details` | `PriceLocationDetail` | Location definitions for pricing | `state`, `country`, `currency` (Currency enum) |
| `products_mna` | `ProductMna` | Legacy MnA data | `sap_sku_id` (UK), `description` |
| `products_mna_new` | `ProductMnaNew` | New MnA data (20+ fields) | `sap_part_no` (UK), `part_description`, `class`, `cate`, `cate_2`, `supplier`, `moq`, `hsn_code`, `mrp_rate`, `gst`, `gst_value`, `invoice_price`, `ndp_dlr`, `ndp_aas`, `type`, `model`, `status`, `category`, `cate_3`, `cate_4`, `non_moving`, `dkp_category`, `so_flag` |
| `parts` | `Part` | Spare parts master | `sap_part_id` (UK), `hierarchy_id`, `division`, `description`, `material_type`, `material_group`, `base_unit_measure`, `gross_weight`, `valid_from`, SAP audit fields |
| `part_market` | `PartMarket` | Part market availability | FK `part_id`, `market`, `min_order_quantity` |
| `parts_price` | `PartPrice` | Part pricing | `sap_part_id` (UK), `price` (BigDecimal), `currency` |

### Entity Hierarchy & Common Fields

All entities extend one of:
- `BaseEntityWithId` → `id` (PK auto), `createdAt`, `updatedAt`, `createdBy`, `updatedBy`, `version` (@Version)
- `CommonBaseEntity` → same fields without auto-id (for entities with custom PK)
- `DealerDependentEntity` extends `BaseEntityWithId` → used by dealer sub-entities

`@PrePersist` / `@PreUpdate` populate timestamps from `Context.getUserId()` (defaults to `"System"`).

### Relationships

- `dealers` 1:1 `dealer_details`
- `dealers` 1:N `dealer_locations`, `dealer_contacts`, `dealer_employees`, `dealer_flags`, `dealer_flags_new`, `dealer_test_ride_vehicles`
- `dealer_flags_new` N:1 `dealer_flag_types_new`
- `dealers` self-referencing: `parent_amd_id` (BRANCH→AMD), `parent_aps_id` (AMD→APS)
- `vehicle_models` 1:N `vehicle_parts` 1:1 `vehicle_part_specifications`
- `price_vehicle_model` N:1 `price_location_details`
- `parts` 1:N `part_market`

### Hibernate Envers

All major entities annotated `@Audited` → produces `*_aud` audit tables + `revinfo` revision table.

---

## Key Algorithms & Business Logic

### MDP Status Derivation (`MdpDealerStatus`)

```
if dmsStatus == PRE_ACTIVE → mdpStatus = PRE_ACTIVE  (regardless of sapStatus)
if dmsStatus == ACTIVE and sapStatus == ACTIVE → mdpStatus = ACTIVE
otherwise → mdpStatus = INACTIVE
```

### AMD ↔ Branch Flag/Status Sync

When an AMD's status or flags change (`DealerOperationsService.syncMdpStatusForChildBranches`):
1. Find all BRANCH dealers with `parent_amd_id` pointing to this AMD
2. Propagate status/flag changes to branches
3. Invalidate cache for all affected branches
4. Publish SB events for each updated branch (only if `isDealerDataPushAllowed`)

### Dealer Data Push Filtering (`DealerDataSenderService.isDealerDataPushAllowed`)

Not all dealers get pushed to Service Bus:
- AMD, SPD, AD, APS → always allowed
- BRANCH → blocked if unofficial branch (`NOT_PRESENT_IN_SAP`) OR if `tempDmsBranchSequence == 1`

### Batch Processing Pipeline (9 types)

1. ADF triggers `GET /v1/de-pipeline/trigger/{BatchProcessingType}`
2. `BatchJobProcessorFactory` selects processor by type
3. Processor reads from MySQL staging/temp tables
4. Rows validated via `Validateable` / `Sanitizeable` interfaces (per-row try/catch)
5. Valid rows upserted to canonical tables (soft-delete, optimistic locking)
6. Per-row outcomes recorded in ADF digest table
7. Change events published to appropriate Service Bus topic
8. Failure email sent if error threshold exceeded
9. Audit log entries: `TRIGGERED`, `COMPLETED`, or `FAILED`

**BatchProcessingType values:** `SAP_DATA`, `SHAREPOINT_DATA`, `DEALER_SAP_SERVICE_CENTER_ADDRESS_DATA`, `PRODUCT_VEHICLE_SAP_DATA`, `PRICE_VEHICLE_SAP_DATA`, `PRODUCT_MNA_SAP_DATA`, `PRODUCT_MNA_NEW_SAP_DATA`, `PART_SAP_DATA`, `PART_PRICE_SAP_DATA`

### Cache Strategy (Read-Through, 10 regions)

1. Check Redis (`CacheName::key`) — keys namespaced as `<CacheName>::<key>`
2. On hit → return cached composite (deserialized from JSON)
3. On miss → assemble from MySQL via `DealerDataGeneratorService.constructDealerDataObjFromScratchFromDatabase`
4. Store assembled composite in Redis (`@Retryable maxAttempts=3`)
5. Return to caller
6. On mutations → invalidate + repopulate cache proactively via `DealerCacheService.populateDealerDataInCache`
7. Bulk reads use `CacheService.getListFromCache` → partitioned `multiGet` in `REDIS_BATCH_SIZE` batches

### DMS Migration Flow

1. `GET /v1/dms-import/trigger` → `DmsDealerOperationalService.startDmsMigration()` (async)
2. Reads dealer/branch data from MSSQL OnlineDMS (read-only, `applicationIntent=ReadOnly`)
3. Processes DMS dealer data and branch data
4. Upserts into MDP MySQL
5. Publishes events to Service Bus
6. Audit logged: `DMS_MIGRATION_STARTED` → `DMS_MIGRATION_COMPLETED` or `DMS_MIGRATION_FAILED`

### Service Bus Consumer Flow (Inbound)

**DealerDataConsumerService:** Receives dealer data → validates → upserts by `sapDealerCode` → invalidates cache → does NOT re-publish (avoids loops)

**DmsDataConsumerService:** Receives JSON → tries to parse as `DmsDealerData`, falls back to `DmsBranchData` (Jackson exception-based routing) → calls `dealerOperationsService.digestDmsDealerDataFromServiceBus` or `dealerBranchOperationsService.digestDmsBranchDataFromServiceBus`

---

## Configuration Management

### Profiles

`ACTIVE_ENVIRONMENT` selects Spring profile: `local | dev | uat | prod`

### Key Environment Variables (from `application.properties`)

| Variable | Purpose |
|----------|---------|
| `DATABASE_HOST_URL`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD` | MySQL connection (port 3306) |
| `REDIS_HOST_URL`, `REDIS_PASSWORD` | Redis connection |
| `SERVICE_BUS_DEALER_DATA_CONNECTION_STRING` + `_TOPIC_NAME` | Dealer topic |
| `SERVICE_BUS_DMS_DEALER_DATA_CONNECTION_STRING` + `_TOPIC_NAME` | DMS dealer topic |
| `SERVICE_BUS_VEHICLE_DATA_CONNECTION_STRING` + `_TOPIC_NAME` | Product vehicle topic |
| `SERVICE_BUS_PRICE_DATA_CONNECTION_STRING` + `_TOPIC_NAME` | Price vehicle topic |
| `SERVICE_BUS_PRODUCT_MNA_DATA_CONNECTION_STRING` + `_TOPIC_NAME` | Product MnA topic |
| `SERVICE_BUS_PART_DATA_CONNECTION_STRING` + `_TOPIC_NAME` | Part data topic |
| `SERVICE_BUS_PART_PRICE_DATA_CONNECTION_STRING` + `_TOPIC_NAME` | Part price topic |
| `DMS_DATABASE_HOST`, `DMS_DATABASE_USERNAME`, `DMS_DATABASE_PASSWORD` | DMS MSSQL read-only |
| `EXCLUDED_AMD_SAP_DEALER_CODES` | CSV of excluded AMD codes |
| `APIM_BASE_URL` | Outbound APIM gateway |
| `NOTIFICATION_BASE_URL`, `NOTIFICATION_EMAIL_FAILURE_TEMPLATE_ID`, `_RECIPIENTS`, `_PRIORITY` | Email config |
| `NOTIFICATION_EMAIL_NEW_DEALER_ACTIVE_DMS_MIGRATION_RECIPIENTS` | DMS migration email recipients |
| `NOTIFICATION_EMAIL_NEW_DEALER_ACTIVE_SHAREPOINT_RECIPIENTS` | SharePoint email recipients |
| `AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL`, `_CLIENT_ID`, `_CLIENT_SECRET`, `_SCOPE` | B2C outbound auth |
| `SHOW_HTTP_500_DETAILS` | Error detail visibility (must be `false` in prod) |
| `HOSTNAME` | K8s pod name (injected by platform) |

### Application-level Config

| Key | Value/Purpose |
|-----|--------------|
| `server.servlet.context-path` | `/mdp` |
| `server.port` | `8080` |
| `spring.datasource.hikari.minimumIdle` | `20` |
| `spring.datasource.hikari.maximumPoolSize` | `50` |
| `spring.jms.servicebus.idle-timeout` | `1800000` (30 min) |
| `spring.jms.servicebus.topic.dealerData.subscription` | `mdp` |
| `springdoc.swagger-ui.enabled` | `true` |
| `latlong.brandCreds[0..7]` | 8 brand-keyed LatLong API credentials |

---

## Dependencies (from pom.xml)

### Runtime Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| Spring Boot Starter (web, data-jpa, actuator) | 3.5.16 | Framework |
| spring-data-redis | 3.5.1 | Redis abstraction |
| jedis | 5.2.0 | Redis client |
| mysql-connector-j | 8.4.0 | MySQL JDBC |
| mssql-jdbc | 12.10.2.jre11 | MSSQL DMS read-only |
| azure-messaging-servicebus | 7.17.17 | Azure Service Bus |
| hibernate-envers | 6.6.13.Final | Entity versioning/audit |
| okhttp | 4.12.0 | Outbound HTTP calls |
| spring-retry | 2.0.13 | Retry on transient failures |
| springdoc-openapi-starter-webmvc-ui | 2.8.9 | Swagger UI |
| guava | 33.4.2-jre | Utilities (partition, etc.) |
| opencsv | 5.12.0 | CSV parsing |
| jackson-datatype-jsr310 | 2.21.2 | Java time serialization |
| lombok | 1.18.46 | Boilerplate reduction |
| commons-beanutils | 1.11.0 | Bean utilities |
| commons-collections4 | 4.5.0 | Collections utilities |

### Overridden Versions (CVE fixes)

| Component | Version | Reason |
|-----------|---------|--------|
| Tomcat | 10.1.56 | CVE fix |
| Logback | 1.5.36 | CVE fix |

### Test Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| junit | 4.13.2 | Unit test framework |
| mockito-inline | 5.2.0 | Mocking final classes (SB) |
| h2 | 2.3.232 | In-memory DB for tests |
| byte-buddy | 1.18.10 | Runtime code generation |

---

## Testing Strategy

| Type | Framework | Scope |
|------|-----------|-------|
| Unit tests | JUnit 4 + Mockito Inline | Service layer, utilities, validation |
| Repository tests | Spring Data JPA + H2 (in-memory) | Repository methods, queries |
| Integration tests | `mvn verify` | End-to-end with in-memory DB |
| Coverage | JaCoCo 0.8.11 | Report at `target/site/jacoco/index.html` |
| Static analysis | SonarQube (PR pipeline) | Code quality, security hotspots |
| Image security | AST Image Scan | Container vulnerability scanning |

```bash
mvn test                              # unit tests
mvn verify                            # unit + integration
mvn clean verify -Pjacoco             # with coverage report
```

### JaCoCo Exclusions (from pom.xml)

- `**/enums/**` — no logic to test
- `**/entity/**` — POJOs
- `**/repository/**` — Spring Data generated
- `product/config/**` — configuration
- `ProductVehicleDataConsumerService` — SB consumer (integration-tested)

---

## Key Patterns & Conventions

- **Service-to-service rule:** Services call services, never another module's repository directly
- **Soft-delete only:** No `DELETE` SQL; entities use status/isDeleted fields
- **App-generated timestamps:** `createdAt`/`updatedAt` from application (`@PrePersist`/`@PreUpdate`), not by DB
- **Optimistic locking:** `@Version` on every entity via `BaseEntityWithId`
- **American English in code:** Sanitize, Authorize, Analyze
- **Request validation:** DTOs implement `APIRequest<T>` (extends `Validateable<T>` + `Sanitizeable<T>`)
- **Thread-local context:** `Context` carries `transactionId`, `clientId`, `userType`, `authToken`, `serverId`, `startTimeInMs` per request; cleared in filter's `finally`
- **Idempotent writes:** Keyed on natural IDs (`sapDealerCode`); no-op if `Objects.equals(oldCopy, updatedCopy)`
- **Idempotent SB consumers:** Re-derive state from source; redelivered messages converge
- **No re-publish on same topic:** Consumers never publish back to the topic they consumed from
- **CORS:** Allowed origins `localhost:3000` and `satanlabs-arsh.github.io` on DealerController

---

*For architecture overview, see `HLD.md`. For full API contract, see `API_SPEC.md`. For comprehensive details with Mermaid diagrams, see `HIGH_LEVEL_DESIGN.md` and `LOW_LEVEL_DESIGN.md`.*
