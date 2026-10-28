---
service_id: tvsm-auth
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvsm-auth — High-Level Code

## Application Overview
tvsm-auth (`tvsm-auth`) is a `backend-api` codebase; stacks java; head `c941d241dc0725ad68a672aac6e7043dced7f998`.
Entry points: `src/main/java/com/tvsmotor/tvsmauth/AuthApplication.java`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java`.

## Module Summary
tvsm-auth modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 89 endpoints, 30 outbound calls, 1 messaging, 2 data-access |

## Folder Structure
tvsm-auth top-level folders (3 levels):

```
tvsm-auth/
├── script/
│   ├── python/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
│   │   ├── resources/
```

## Core Workflows in Code
tvsm-auth workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### UserProfileController
1. `src/main/java/com/tvsmotor/tvsmauth/user/profile/api/UserProfileController.java` receives 32 route(s), e.g. `GET /api/v1/user/b2c-login-profile` → `UserProfileController.getUserDetailsByB2CId`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### api-specs
1. `api-specs.yml` receives 14 route(s), e.g. `GET /v1/app/callback/{appName}` → `ApplicationController.authCallback`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### ApplicationController
1. `src/main/java/com/tvsmotor/tvsmauth/applications/controller/ApplicationController.java` receives 10 route(s), e.g. `GET /auth/v1/app/callback/{appName}` → `ApplicationController.authCallback`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### DealerController
1. `src/main/java/com/tvsmotor/tvsmauth/user/profile/api/DealerController.java` receives 6 route(s), e.g. `GET /api/v1/dealer/branch/list-all` → `DealerController.listAllBranches`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### RoleController
1. `src/main/java/com/tvsmotor/tvsmauth/user/role/api/RoleController.java` receives 6 route(s), e.g. `GET /api/v1/role/{roleId}/get` → `RoleController.fetchRoles`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### DynamicFormController
1. `src/main/java/com/tvsmotor/tvsmauth/user/dynamicforms/api/DynamicFormController.java` receives 5 route(s), e.g. `POST /api/v1/dynamic-forms/get-registration-form` → `DynamicFormController.getFormByApplicationId`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### UserApplicationController
1. `src/main/java/com/tvsmotor/tvsmauth/user/profile/api/UserApplicationController.java` receives 4 route(s), e.g. `GET /api/v1/application/list-all` → `UserApplicationController.listAllApplication`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### AdminController
1. `src/main/java/com/tvsmotor/tvsmauth/user/profile/api/AdminController.java` receives 3 route(s), e.g. `GET /api/v1/admin/dealerships` → `AdminController.listDealerships`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### GroupController
1. `src/main/java/com/tvsmotor/tvsmauth/user/group/api/GroupController.java` receives 3 route(s), e.g. `GET /api/v1/group/{groupId}/roles` → `GroupController.fetchRolesByGroupId`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### DepartmentController
1. `src/main/java/com/tvsmotor/tvsmauth/user/department/api/DepartmentController.java` receives 2 route(s), e.g. `GET /api/v1/department/list-all` → `DepartmentController.getAllDepartments`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### ums-api-specs
1. `ums-api-specs.yml` receives 2 route(s), e.g. `POST /api/v1/permission/create` → `None`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### LocationController
1. `src/main/java/com/tvsmotor/tvsmauth/user/location/api/LocationController.java` receives 1 route(s), e.g. `GET /api/v1/location/state/list` → `LocationController.getStateList`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### EkycController
1. `src/main/java/com/tvsmotor/tvsmauth/user/profile/ekyc/api/EkycController.java` receives 1 route(s), e.g. `POST /api/v1/user/ekyc/verify` → `EkycController.verifyUserEkyc`.
2. Module `.` makes outbound calls to: `Unknown(config:application.b2c.baseUri)`, `Unknown(config:application.ums.tokenUrl)`, `Unknown(config:azure.faceApi.url)`, `Unknown(config:karza.baseUrl)`, `Unknown(literal)`, `master-data-platform`, `notification-service`, `tvsm-auth`.
3. Module `.` data access via `src/main/resources/db/migration/20240116_add_permission.sql:3`, `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19`.

### Job CacheClearScheduler.evictAllCachesAtIntervals
1. `src/main/java/com/tvsmotor/tvsmauth/config/CacheClearScheduler.java:16` runs on cron `0 0 2 * * ?`.

### Job NotificationReminder.sendSMSForFaceLogin
1. `src/main/java/com/tvsmotor/tvsmauth/user/profile/scheduler/NotificationReminder.java:43` runs on cron `0 0 18 * * ?`.

## Integration Clients
tvsm-auth outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/main/java/com/tvsmotor/tvsmauth/applications/ApplicationServiceImpl.java`, `src/main/java/com/tvsmotor/tvsmauth/applications/gateway/AzureB2CGateway.java` | config:application.b2c.baseUri |
| Unknown | `src/main/java/com/tvsmotor/tvsmauth/user/gateway/MDPServiceClient.java` | config:application.ums.tokenUrl |
| Unknown | `src/main/java/com/tvsmotor/tvsmauth/user/gateway/FaceRecognitionService.java` | config:azure.faceApi.url |
| Unknown | `src/main/java/com/tvsmotor/tvsmauth/support/OkHttpService.java` | config:karza.baseUrl |
| Unknown | `src/test/java/com/tvsmotor/tvsmauth/support/OkHttpClientTest.java`, `src/test/java/com/tvsmotor/tvsmauth/user/gateway/LocationMasterServiceClientTest.java`, `src/test/java/com/tvsmotor/tvsmauth/user/gateway/MDPServiceClientTest.java` …+2 | literal |
| `master-data-platform` | `src/main/java/com/tvsmotor/tvsmauth/user/gateway/MDPServiceClient.java` | config:mdp.baseUrl |
| `notification-service` | `src/main/java/com/tvsmotor/tvsmauth/user/gateway/NotificationGateway.java` | config:notification.baseUrl |
| `tvsm-auth` | `src/main/java/com/tvsmotor/tvsmauth/user/gateway/LocationMasterServiceClient.java` | config:location-master.baseUrl |
| azure-service-bus publish dev.ums.user_apps | `src/main/java/com/tvsmotor/tvsmauth/user/gateway/AzureServiceBusPublisher.java:49` | azure.servicebus.topic-name |
| data store (db) | `src/main/resources/db/migration/20240116_add_permission.sql:3` | Unknown |
| data store (db) | `src/main/java/com/tvsmotor/tvsmauth/applications/entity/Application.java:19` | Unknown |

## Cross-Cutting Concerns
tvsm-auth cross-cutting code:
- Auth: `src/main/java/com/tvsmotor/tvsmauth/config/SecurityConfig.java:19` (SecurityFilterChain), `src/main/java/com/tvsmotor/tvsmauth/config/JwtTokenFilter.java:11` (OncePerRequestFilter)
- Error handling: `src/main/java/com/tvsmotor/tvsmauth/applications/controller/ApplicationExceptionHandler.java:15` (@RestControllerAdvice), `src/main/java/com/tvsmotor/tvsmauth/applications/controller/ValidationHandler.java:18` (@ControllerAdvice)
- Validation: 64 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
tvsm-auth build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `AST_Image_Scan_auth_ninja_Pipeline.yml:1`, `AST_auth_ninja_UAT_Pipeline.yml:1`, `AST_norton_auth_ninja_UAT_Pipeline.yml:1`, `auth-ninja-sonar-scan.yaml:1`, `cd-norton-pipeline.yaml:1`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`, `gitleaks-scan.yaml:1`, `sonar_ci_pr_pipeline.yml:11`, `uk-cd-pipeline.yaml:1`
