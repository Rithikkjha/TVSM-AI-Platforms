---
service_id: notification-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# notification-service — High-Level Code

## Application Overview
notification-service (`notification-service`) is a `backend-api` codebase; stacks java; head `6e70d00652433dc383454569a30f24e3f5dc400c`.
Entry points: `src/main/java/com/tvsmotor/notification/NotificationApplication.java`.

## Module Summary
notification-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 24 endpoints, 0 outbound calls, 4 messaging, 1 data-access |

## Folder Structure
notification-service top-level folders (3 levels):

```
notification-service/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
│   │   ├── resources/
```

## Core Workflows in Code
notification-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### NotificationUserPreferenceController
1. `src/main/java/com/tvsmotor/notification/controller/NotificationUserPreferenceController.java` receives 6 route(s), e.g. `DELETE /api/v1/notification/user-preference/client/{clientId}` → `NotificationUserPreferenceController.deleteByClientId`.
3. Module `.` data access via `src/main/java/com/tvsmotor/notification/model/NotificationRetryPreference.java:12`.

### NotificationController
1. `src/main/java/com/tvsmotor/notification/controller/NotificationController.java` receives 6 route(s), e.g. `GET /api/v1/notification/{id}` → `NotificationController.fetchNotification`.
3. Module `.` data access via `src/main/java/com/tvsmotor/notification/model/NotificationRetryPreference.java:12`.

### NotificationRetryPreferenceController
1. `src/main/java/com/tvsmotor/notification/controller/NotificationRetryPreferenceController.java` receives 5 route(s), e.g. `DELETE /api/v1/notification/retryPreference/{retryPreferenceId}` → `NotificationRetryPreferenceController.deleteNotificationRetryPreferenceById`.
3. Module `.` data access via `src/main/java/com/tvsmotor/notification/model/NotificationRetryPreference.java:12`.

### NotificationTemplateController
1. `src/main/java/com/tvsmotor/notification/controller/NotificationTemplateController.java` receives 4 route(s), e.g. `DELETE /api/v1/notification/template/{id}` → `NotificationTemplateController.deleteNotificationTemplate`.
3. Module `.` data access via `src/main/java/com/tvsmotor/notification/model/NotificationRetryPreference.java:12`.

### HealthCheckController
1. `src/main/java/com/tvsmotor/notification/controller/HealthCheckController.java` receives 1 route(s), e.g. `GET /health` → `HealthCheckController.healthTest`.
3. Module `.` data access via `src/main/java/com/tvsmotor/notification/model/NotificationRetryPreference.java:12`.

### InfobipAPIErrorRetryController
1. `src/main/java/com/tvsmotor/notification/controller/infobip/InfobipAPIErrorRetryController.java` receives 1 route(s), e.g. `POST /infobipAPIError/retry` → `InfobipAPIErrorRetryController.infobipAPIErrorRetry`.
3. Module `.` data access via `src/main/java/com/tvsmotor/notification/model/NotificationRetryPreference.java:12`.

### InfobipCallbackController
1. `src/main/java/com/tvsmotor/notification/controller/infobip/InfobipCallbackController.java` receives 1 route(s), e.g. `POST /webhook/infobip/status-update` → `InfobipCallbackController.infobipStatusUpdate`.
3. Module `.` data access via `src/main/java/com/tvsmotor/notification/model/NotificationRetryPreference.java:12`.

### Job QueueToTopicService.processQueueMessages
1. `src/main/java/com/tvsmotor/notification/service_bus/QueueToTopicService.java:17` runs on fixed-rate `7200000`.

### Consumer Unknown (`unresolved`)
1. `src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java:117` handles messages (azure-service-bus, trigger processor).

## Integration Clients
notification-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| azure-service-bus publish local.notifications | `src/main/java/com/tvsmotor/notification/service_bus/ServiceBusNotifier.java:100` | spring.jms.servicebus.topic.notifications |
| azure-service-bus publish notifications-status-update | `src/main/java/com/tvsmotor/notification/service_bus/ServiceBusNotifier.java:158` | spring.jms.servicebus.topic.notifications.status-update |
| azure-service-bus publish Unknown (`unresolved`) | `src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java:93` | unknown |
| azure-service-bus subscribe Unknown (`unresolved`) | `src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java:117` | unknown |
| data store (db) | `src/main/java/com/tvsmotor/notification/model/NotificationRetryPreference.java:12` | Unknown |

## Cross-Cutting Concerns
notification-service cross-cutting code:
- Auth: `src/main/java/com/tvsmotor/notification/config/NotificationOncePerFilter.java:13` (OncePerRequestFilter)
- Error handling: `src/main/java/com/tvsmotor/notification/handler/ValidationHandler.java:22` (@ControllerAdvice)
- Validation: 12 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `com.github.ben-manes.caffeine:caffeine`, `io.github.hakky54:logcaptor`, `io.sentry:sentry-logback`

## Build and Test
notification-service build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `AST_Image_Scan_notification_service_Pipeline.yml:1`, `AST_notification_service_PROD_Pipeline.yml:1`, `AST_notification_service_UAT_Pipeline.yml:2`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`, `sonar_ci_pr_pipeline.yml:1`, `uk-cd-pipeline.yaml:1`, `uk-training-cd-pipeline.yaml:1`
