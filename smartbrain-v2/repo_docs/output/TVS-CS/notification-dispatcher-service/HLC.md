---
service_id: notification-dispatcher-service
doc_type: hlc
last_reviewed: 2026-10-11
---

# notification-dispatcher-service — High-Level Code

## Application Overview
notification-dispatcher-service (`notification-dispatcher-service`) is a `backend-api` codebase; stacks java; head `f770c984fecacaa826ebd48d8db89e3d0da915ac`.
Entry points: `src/main/java/com/tvsmotor/notificationdispatcher/NotificationDispatcherApplication.java`.

## Module Summary
notification-dispatcher-service modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | service: 3 endpoints, 5 outbound calls, 1 messaging, 1 data-access |

## Folder Structure
notification-dispatcher-service top-level folders (3 levels):

```
notification-dispatcher-service/
├── src/
│   ├── main/
│   │   ├── java/
│   │   ├── resources/
│   ├── test/
│   │   ├── java/
│   │   ├── resources/
```

## Core Workflows in Code
notification-dispatcher-service workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### HealthCheckController
1. `src/main/java/com/tvsmotor/notificationdispatcher/controller/HealthCheckController.java` receives 1 route(s), e.g. `GET /health` → `HealthCheckController.healthTest`.
2. Module `.` makes outbound calls to: `Unknown(config:infobip.baseUri)`, `Unknown(config:salesforce.api.authUrl)`, `Unknown(unknown)`.
3. Module `.` data access via `src/main/java/com/tvsmotor/notificationdispatcher/model/NotificationTemplate.java:17`.

### PushNotificationController
1. `src/main/java/com/tvsmotor/notificationdispatcher/controller/PushNotificationController.java` receives 1 route(s), e.g. `POST /api/v1/notifications/push` → `PushNotificationController.sendPushNotification`.
2. Module `.` makes outbound calls to: `Unknown(config:infobip.baseUri)`, `Unknown(config:salesforce.api.authUrl)`, `Unknown(unknown)`.
3. Module `.` data access via `src/main/java/com/tvsmotor/notificationdispatcher/model/NotificationTemplate.java:17`.

### SalesforceTokenController
1. `src/main/java/com/tvsmotor/notificationdispatcher/controller/SalesforceTokenController.java` receives 1 route(s), e.g. `POST /salesforce/refresh-token` → `SalesforceTokenController.refreshToken`.
2. Module `.` makes outbound calls to: `Unknown(config:infobip.baseUri)`, `Unknown(config:salesforce.api.authUrl)`, `Unknown(unknown)`.
3. Module `.` data access via `src/main/java/com/tvsmotor/notificationdispatcher/model/NotificationTemplate.java:17`.

### Job ThreadPoolMonitor.logThreadPoolStats
1. `src/main/java/com/tvsmotor/notificationdispatcher/service/ThreadPoolMonitor.java:15` runs on fixed-rate `60000`.

### Consumer local.notifications
1. `src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:88` handles messages (azure-service-bus, trigger processor).

## Integration Clients
notification-dispatcher-service outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/main/java/com/tvsmotor/notificationdispatcher/config/WebClientConfiguration.java` | config:infobip.baseUri |
| Unknown | `src/main/java/com/tvsmotor/notificationdispatcher/config/WebClientConfiguration.java` | config:salesforce.api.authUrl |
| Unknown | `src/main/java/com/tvsmotor/notificationdispatcher/service/email/infobip/InfobipEmailSender.java`, `src/main/java/com/tvsmotor/notificationdispatcher/service/sms/infobip/InfobipSMSSender.java` | unknown |
| azure-service-bus subscribe local.notifications | `src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:88` | spring.jms.servicebus.topic.notifications |
| data store (db) | `src/main/java/com/tvsmotor/notificationdispatcher/model/NotificationTemplate.java:17` | Unknown |

## Cross-Cutting Concerns
notification-dispatcher-service cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `com.github.ben-manes.caffeine:caffeine`, `io.github.hakky54:logcaptor`, `io.sentry:sentry-logback`, `io.sentry:sentry-spring-boot-starter`, `org.springframework.boot:spring-boot-starter-cache`

## Build and Test
notification-dispatcher-service build/test commands from manifests:
- Maven: `mvn clean package` / `mvn test` (`pom.xml`)
- CI pipelines: `AST_Image_Scan_notification_dispatcher_service_Pipeline.yml:2`, `AST_notification_dispatcher_service_PROD_Pipeline.yml:1`, `AST_notification_dispatcher_service_UAT_Pipeline.yml:2`, `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`, `sonar_ci_pr_pipeline.yml:6`, `uk-cd-pipeline.yaml:1`, `uk-training-cd-pipeline.yaml:1`
