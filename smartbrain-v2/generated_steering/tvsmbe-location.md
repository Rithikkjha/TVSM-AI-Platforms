# tvsmbe-location

*Auto-generated from static code analysis*

## Service Overview
- **Language:** Java (Spring Boot @ 3.5.13)
- **Contacts:** riteshkr94, shekharbachu123, sumanmahanty13, arsh-tvs, Prabhavtvs
- **Purpose:** This service acts as a location master, managing and providing access to location-related data for dealers and administrative functions.
- **Domain:** access, accessible, accuracy, active, address, admin, admin-flow, administrative, allowed, amphitheatre

## Code Structure
```
📄 .env
📄 .gitignore
📄 20250110_docker_manual_builder_and_pusher_location.sh
📄 AST_Image_Scan_Location_Master_Pipeline.yml
📄 AST_Location_Master_tvsmbe_location_UAT_Pipeline.yml
📄 Dockerfile
📄 PR_CBS1-693_code_review_report_2026-04-02.md
📄 README.md
📁 azure-pipelines/
📄 azure-pipelines/uat.cd.yml
📄 azure-pipelines/uat.ci.yml
📄 cd-pipeline.yaml
📄 ci-pipeline.yaml
📄 pom.xml
📁 scripts/
📁 scripts/python/
📄 scripts/python/20250421_extraxt_pincode_from_latlong.py
📄 scripts/python/Analysis_Dataset.py
📄 scripts/python/Converting_Missing_Data_latlongs.py
📄 scripts/python/GeoCode_AllData.py
📄 scripts/python/GeoCodingAPI.py
📄 scripts/python/MapsOfIndia.py
📄 scripts/python/geocode_threads.py
📄 scripts/python/geocodedAddressAlongWithPincode.py
📄 scripts/python/missingDataScript.py
📄 scripts/python/negativeValues.py
📄 sonar_ci_pr_pipeline.yml
📁 src/
📁 src/main/
📁 src/main/java/
📁 src/main/resources/
📁 src/test/
📁 src/test/java/
```

## Key Modules
| File | Purpose |
|---|---|
| src/main/java/com/tvsmotor/location_master/service/interfaces/Copyeable.java | Implements a method for copying parameters exclusively from source to target, ensuring mission-critical parameters are copied explicitly. |
| src/main/java/com/tvsmotor/location_master/service/DealerLocationStatusManager.java | Manages the status of dealer locations based on actions performed; no database changes occur within this class. |
| src/main/java/com/tvsmotor/location_master/service/AuditLogService.java | Provides functionality for logging audit records. |
| src/main/java/com/tvsmotor/location_master/service/CountryService.java | Handles operations related to country data. |
| src/main/java/com/tvsmotor/location_master/config/OkHttpClientConfig.java | Configures and creates a bean for OkHttpClient, utilized for making API calls. |

## API Endpoints
| Method | Path | Description | File |
|--------|------|-------------|------|
| POST | /dealers | http://localhost:8080/location-master/api/v1/finder/dealers | src/main/java/com/tvsmotor/location_master/controller/DealerProximityController.java:26 |
| GET | /dealerInfo | http://localhost:8080/location-master/api/v1/dealer-flow/dealerInfo?secretKey=123123 | src/main/java/com/tvsmotor/location_master/controller/DealerFlowController.java:25 |
| GET | /dealer/{sapDealerCode} | http://localhost:8080/location-master/api/v1/dealer-flow/dealer/12345 | src/main/java/com/tvsmotor/location_master/controller/DealerFlowController.java:35 |
| GET | /dealer/{sapDealerCode}/location-type/{dealerLocationType} | http://localhost:8080/location-master/api/v1/dealer-flow/dealer/12345/location-type/SALES | src/main/java/com/tvsmotor/location_master/controller/DealerFlowController.java:46 |
| GET | /summary | http://localhost:8080/location-master/api/v1/dealer/summary?countryCode=IN | src/main/java/com/tvsmotor/location_master/controller/IBDealerController.java:42 |
| POST | /list | http://localhost:8080/location-master/api/v1/dealer/list | src/main/java/com/tvsmotor/location_master/controller/IBDealerController.java:55 |
| PUT | /{id} | http://localhost:8080/location-master/api/v1/dealer/{id} | src/main/java/com/tvsmotor/location_master/controller/IBDealerController.java:69 |
| POST | / | http://localhost:8080/location-master/api/v1/dealer | src/main/java/com/tvsmotor/location_master/controller/IBDealerController.java:31 |
| GET | /api/v1/location/states |  | src/main/java/com/tvsmotor/location_master/controller/LocationMasterController.java:24 |
| GET | /{childAdministrativeLocationType}/list | http://localhost:8080/location-master/api/v1/location/STATE/list?parentName=IND&parentType=COUNTRY | src/main/java/com/tvsmotor/location_master/controller/LocationController.java:28 |
| GET | /pincode/{pincode} | http://localhost:8080/location-master/api/v1/location/pincode/632014?country=IND | src/main/java/com/tvsmotor/location_master/controller/LocationController.java:41 |
| GET | /api/v1/user-x/{userId} | http://localhost:8080/location-master/api/v1/user-x/{userId} | src/main/java/com/tvsmotor/location_master/controller/UserXController.java:39 |
| DELETE | /api/v1/user-x/{userId} | http://localhost:8080/location-master/api/v1/user-x/{userId} | src/main/java/com/tvsmotor/location_master/controller/UserXController.java:48 |
| POST | /api/v1/user-x/{userId}/owned-entity | http://localhost:8080/location-master/api/v1/user-x/1/owned-entity | src/main/java/com/tvsmotor/location_master/controller/UserXController.java:57 |
| PUT | /api/v1/user-x/{userId}/owned-entity/delete | http://localhost:8080/location-master/api/v1/user-x/1/owned-entity | src/main/java/com/tvsmotor/location_master/controller/UserXController.java:67 |
| GET | /api/v1/user-x/{userId}/countries | http://localhost:8080/location-master/api/v1/user-x/1/countries | src/main/java/com/tvsmotor/location_master/controller/UserXController.java:77 |
| POST | /api/v1/user-x | http://localhost:8080/location-master/api/v1/user-x | src/main/java/com/tvsmotor/location_master/controller/UserXController.java:27 |
| POST | /verification | http://localhost:8080/location-master/api/v1/admin-flow/verification | src/main/java/com/tvsmotor/location_master/controller/AdminFlowController.java:58 |
| POST | /send-location-update-sms | http://localhost:8080/location-master/api/v1/admin-flow/send-location-update-sms | src/main/java/com/tvsmotor/location_master/controller/AdminFlowController.java:84 |
| GET | /rejection-comments | http://localhost:8080/location-master/api/v1/admin-flow/rejection-comments?type=REJECTION_COMMENTS | src/main/java/com/tvsmotor/location_master/controller/AdminFlowController.java:96 |
| GET | /{sapDealerCode}/contacts/{dealerLocationType} | http://localhost:8080/location-master/api/v1/admin-flow/10015/contacts/SERVICE | src/main/java/com/tvsmotor/location_master/controller/AdminFlowController.java:112 |
| POST | /tamil-nadu-pincodes | http://localhost:8080/location-master/api/v1/geo/tamil-nadu-pincodes | src/main/java/com/tvsmotor/location_master/controller/GeoCodeController.java:25 |
| GET | /geocode | http://localhost:8080/location-master/api/v1/geo/geocode | src/main/java/com/tvsmotor/location_master/controller/GeoCodeController.java:36 |
| GET | /{countryCode}/filter-config | http://localhost:8080/location-master/api/v1/country/IN/filter-config?locale=en | src/main/java/com/tvsmotor/location_master/controller/CountryController.java:25 |
| GET | /{countryCode}/provinces |  | src/main/java/com/tvsmotor/location_master/controller/CountryController.java:34 |
| POST | /location-data |  | src/main/java/com/tvsmotor/location_master/controller/MigrationController.java:38 |
| POST | /import-dealership-locations |  | src/main/java/com/tvsmotor/location_master/controller/MigrationController.java:46 |
| POST | /submit | http://localhost:8080/location-master/v1/dealer-location/submit | src/main/java/com/tvsmotor/location_master/controller/MobileFlowController.java:26 |
| GET | /tcpp | http://localhost:8080/location-master/v1/dealer-location/tcpp | src/main/java/com/tvsmotor/location_master/controller/MobileFlowController.java:36 |

## Dependencies (Outbound)
### HTTP Calls
| Target Service | URL/Variable | Confidence | File |
|---|---|---|---|
| unknown | `String getDealerContactsApiUrl = String.format(UMS_GET_DEALER_CONTACTS_API_URL, umsBaseUrl, sapDeale` | 🔴 low | src/main/java/com/tvsmotor/location_master/service/UMSService.java:48 |
| TVS-CPS-BE-BASE-FRAMEWORK | `@Value("${ums.base.url}")` | 🟡 medium | src/main/java/com/tvsmotor/location_master/service/UMSService.java:33 |
| notification-service | `@Value("${b2c.notification.token.url}")` | 🟡 medium | src/main/java/com/tvsmotor/location_master/service/AzureB2CTokenGenerationService.java:31 |

## Databases
| Type | Name | File |
|---|---|---|
| mongodb |  | pom.xml — mongodb dependency |

## Recent Activity
- **Last commit:** 2026-05-12 by shekharbachu123 — "Merge pull request #349 from TVSM-CS/shekharbachu123-patch-1"
- **Active contributors (30d):** mandvi22, riteshkr94, shekharbachu123
- **Commit frequency:** ~1/week

## Architecture Notes
This service is structured to facilitate modular development, with clear separation of concerns across various components, including services for dealer management, country data, and audit logging. The use of Spring Boot enhances its scalability and maintainability.