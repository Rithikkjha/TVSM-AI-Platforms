---
service_id: tvsmbe-location
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvsmbe-location — High-Level Code

## Application Overview
tvsmbe-location (`tvsmbe-location`) is a `backend-api` codebase; stacks java; head `0dc09a8bd0514d35a0f618ded70cb12db15b0aeb`.
Entry points: `src/main/java/com/tvsmotor/location_master/LocationMasterApplication.java`.

## Module Summary
tvsmbe-location modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 45 endpoints, 33 outbound calls, 0 messaging, 2 data-access |

## Folder Structure
tvsmbe-location top-level folders (3 levels):

```
tvsmbe-location/
├── azure-pipelines/
├── scripts/
│   ├── python/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
```

## Core Workflows in Code
tvsmbe-location workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### AdminFlowController
1. `src/main/java/com/tvsmotor/location_master/controller/AdminFlowController.java` receives 7 route(s), e.g. `GET /location-master/api/v1/admin-flow/dealer/{sapDealerCode}/location-type/{dealerLocationType}` → `AdminFlowController.getDealerLocationDetails`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### UserXController
1. `src/main/java/com/tvsmotor/location_master/controller/UserXController.java` receives 6 route(s), e.g. `DELETE /location-master/api/v1/user-x/{userId}` → `UserXController.deleteUser`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### IBDealerController
1. `src/main/java/com/tvsmotor/location_master/controller/IBDealerController.java` receives 6 route(s), e.g. `GET /location-master/api/v1/dealer/summary` → `IBDealerController.getIBDealerSummaryByCountryCode`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### DomesticDealerController
1. `src/main/java/com/tvsmotor/location_master/controller/DomesticDealerController.java` receives 6 route(s), e.g. `POST /location-master/api/v1/domestic-dealer/brands` → `DomesticDealerController.getBrands`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### TestController
1. `src/main/java/com/tvsmotor/location_master/controller/TestController.java` receives 4 route(s), e.g. `DELETE /location-master/api/v1/test/cache/{cacheName}/{key}` → `TestController.clearCache`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### DealerFlowController
1. `src/main/java/com/tvsmotor/location_master/controller/DealerFlowController.java` receives 3 route(s), e.g. `GET /location-master/api/v1/dealer-flow/dealer/{sapDealerCode}` → `DealerFlowController.getDealerAndBranchDetails`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### CountryController
1. `src/main/java/com/tvsmotor/location_master/controller/CountryController.java` receives 2 route(s), e.g. `GET /location-master/api/v1/country/{countryCode}/filter-config` → `CountryController.getFilterConfigByCountryCode`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### LocationController
1. `src/main/java/com/tvsmotor/location_master/controller/LocationController.java` receives 2 route(s), e.g. `GET /location-master/api/v1/location/pincode/{pincode}` → `LocationController.getDetailsForPincode`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### MobileFlowController
1. `src/main/java/com/tvsmotor/location_master/controller/MobileFlowController.java` receives 2 route(s), e.g. `GET /location-master/v1/dealer-location/tcpp` → `MobileFlowController.getTermsAndConditionsPrivacyPolicy`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### MigrationController
1. `src/main/java/com/tvsmotor/location_master/controller/MigrationController.java` receives 2 route(s), e.g. `POST /location-master/api/v1/admin/migrate/import-dealership-locations` → `MigrationController.importDealershipLocations`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### GeoCodeController
1. `src/main/java/com/tvsmotor/location_master/controller/GeoCodeController.java` receives 1 route(s), e.g. `GET /location-master/api/v1/geo/geocode` → `GeoCodeController.callGeocodeApi`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### LocationMasterController
1. `src/main/java/com/tvsmotor/location_master/controller/LocationMasterController.java` receives 1 route(s), e.g. `GET /location-master/api/v1/location/states` → `LocationMasterController.getAllStates`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### ChargingStationController
1. `src/main/java/com/tvsmotor/location_master/controller/ChargingStationController.java` receives 1 route(s), e.g. `POST /location-master/api/v1/charging-station/nearby` → `ChargingStationController.getNearbyChargingStations`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### DealershipLocationController
1. `src/main/java/com/tvsmotor/location_master/controller/DealershipLocationController.java` receives 1 route(s), e.g. `POST /location-master/api/v1/dealer-search` → `DealershipLocationController.searchDealers`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### DealerProximityController
1. `src/main/java/com/tvsmotor/location_master/controller/DealerProximityController.java` receives 1 route(s), e.g. `POST /location-master/api/v1/finder/dealers` → `DealerProximityController.getActiveDealerDetails`.
2. Module `.` makes outbound calls to: `Unknown(config:kazam.base.url)`, `Unknown(config:lms.base.url)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`, `tvsm-otp-service`.
3. Module `.` data access via `src/main/java/com/tvsmotor/location_master/entity/Area.java:10`, `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11`.

### Job CronService.logMetricsPeriodically
1. `src/main/java/com/tvsmotor/location_master/service/CronService.java:32` runs on fixed-rate `60000`.

## Integration Clients
tvsmbe-location outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/main/java/com/tvsmotor/location_master/service/external_api_caller/KazamApiCallerService.java` | config:kazam.base.url |
| Unknown | `src/main/java/com/tvsmotor/location_master/service/LeadService.java` | config:lms.base.url |
| Unknown | `src/test/java/com/tvsmotor/location_master/service/AzureB2CTokenGenerationServiceTest.java`, `src/test/java/com/tvsmotor/location_master/service/KazamApiCallerServiceTest.java`, `src/test/java/com/tvsmotor/location_master/service/LeadServiceTest.java` …+5 | literal |
| `master-data-platform` | `src/main/java/com/tvsmotor/location_master/service/MDPDealerService.java` | config:mdp.base.url |
| `notification-service` | `src/main/java/com/tvsmotor/location_master/service/NotificationSmsDispatcherService.java` | config:notification.base.url |
| `tvsm-auth` | `src/main/java/com/tvsmotor/location_master/service/UMSService.java` | config:ums.base.url |
| `tvsm-otp-service` | `src/main/java/com/tvsmotor/location_master/service/OtpService.java` | config:otp.service.base.url |
| data store (db) | `src/main/java/com/tvsmotor/location_master/entity/Area.java:10` | Unknown |
| data store (db) | `src/main/resources/db/migration/v1.1__location_master_DDL_tables.sql:11` | Unknown |

## Cross-Cutting Concerns
tvsmbe-location cross-cutting code:
- Auth: `src/main/java/com/tvsmotor/location_master/security/SecurityConfig.java:10` (SecurityFilterChain), `src/main/java/com/tvsmotor/location_master/security/RequestFilter.java:17` (OncePerRequestFilter)
- Error handling: `src/main/java/com/tvsmotor/location_master/exception/RestExceptionHandler.java:22` (@ControllerAdvice)
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `io.sentry:sentry-logback`, `io.sentry:sentry-spring-boot-starter`, `org.springframework.boot:spring-boot-starter-cache`

## Build and Test
tvsmbe-location build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `AST_Image_Scan_Location_Master_Pipeline.yml:1`, `AST_Location_Master_tvsmbe_location_UAT_Pipeline.yml:1`, `azure-pipelines/uat.cd.yml:2`, `azure-pipelines/uat.ci.yml:1`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`, `sonar_ci_pr_pipeline.yml:2`
