# notification-dispatcher-service

*Auto-generated from static code analysis*

## Service Overview
- **Language:** Java (Spring Boot @3.5.7)
- **Contacts:** shekharbachu123, PrashantVerma-TVS15168, sandhiya-ravichandran2002, santhosh-tvsd, Nivetha-Nehru
- **Purpose:** This service is responsible for managing notifications, including handling Salesforce authentication tokens and facilitating communication with various notification channels.
- **Domain:** access, active, activity, adjust, application, args, argument, artifact, artifactid, asia

## Code Structure
```
📄 .gitignore
📄 AST_Image_Scan_notification_dispatcher_service_Pipeline.yml
📄 AST_notification_dispatcher_service_PROD_Pipeline.yml
📄 AST_notification_dispatcher_service_UAT_Pipeline.yml
📄 Dockerfile
📄 README.md
📄 cd-pipeline.yaml
📄 ci-pipeline.yaml
📄 pom.xml
📄 sonar_ci_pr_pipeline.yml
📁 src/
📁 src/main/
📁 src/main/java/
📁 src/main/resources/
📁 src/test/
📁 src/test/java/
📁 src/test/resources/
📄 uk-cd-pipeline.yaml
📄 uk-training-cd-pipeline.yaml
```

## Key Modules
| File | Purpose |
|---|---|
| src/main/java/com/tvsmotor/notificationdispatcher/controller/SalesforceTokenController.java | Controller for managing Salesforce authentication tokens. |

## API Endpoints
| Method | Path | Description | File |
|--------|------|-------------|------|
| GET | /health | Health check endpoint to monitor service status. | src/main/java/com/tvsmotor/notificationdispatcher/controller/HealthCheckController.java:23 |
| POST | /salesforce/refresh-token | Endpoint to refresh Salesforce authentication tokens. | src/main/java/com/tvsmotor/notificationdispatcher/controller/SalesforceTokenController.java:35 |

## Dependencies (Outbound)
### HTTP Calls
| Target Service | URL/Variable | Confidence | File |
|---|---|---|---|
| notification-service | `@Value("${notification.infobip.retry.url}")` | 🟡 medium | src/main/java/com/tvsmotor/notificationdispatcher/service/InfobipAPIErrorRetryService.java:20 |
| TVS-CPS-BE-BASE-FRAMEWORK | `@Value("${infobip.baseUri}")` | 🟡 medium | src/main/java/com/tvsmotor/notificationdispatcher/config/WebClientConfiguration.java:12 |
| unknown | `@Value("${salesforce.api.sendSMS.url}")` | 🔴 low | src/main/java/com/tvsmotor/notificationdispatcher/config/WebClientConfiguration.java:18 |
| tvsm-auth | `@Value("${salesforce.api.authUrl}")` | 🟢 high | src/main/java/com/tvsmotor/notificationdispatcher/config/WebClientConfiguration.java:21 |

### Service Bus — Publishes
| Topic | Confidence | File |
|---|---|---|
| notifications | 🟢 high | src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:31 |

### Service Bus — Subscribes
| Topic | Source Service | Confidence | File |
|---|---|---|---|
| service-bus-notification | unknown | 🟢 high | src/main/java/com/tvsmotor/notificationdispatcher/service_bus/ServiceBusNotificationReceiver.java:12 |
| highpriority | unknown | 🟢 high | src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:32 |
| email | unknown | 🟢 high | src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:43 |
| sms | unknown | 🟢 high | src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:54 |
| whatsapp | unknown | 🟢 high | src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:65 |
| subscription:high-priority | unknown | 🟢 high | src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:29 |
| subscription:email | unknown | 🟢 high | src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:40 |
| subscription:sms | unknown | 🟢 high | src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:51 |
| subscription:whats-app | unknown | 🟢 high | src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:62 |

## Databases
| Type | Name | File |
|---|---|---|
| mongodb |  | pom.xml — mongodb dependency |

## Recent Activity
- **Last commit:** 2026-03-27 by PrashantVerma-TVS15168 — "CBS6-541_Notification_Dispatcher[20260324]/Code_Coverage_Improvement (#155)"
- **Commit frequency:** inactive

## Architecture Notes
This service utilizes a microservices architecture, leveraging Spring Boot for RESTful API development and integrating with various external services through HTTP calls and service bus messaging. The structure indicates a focus on modularity and separation of concerns, particularly in the handling of notifications and Salesforce token management.