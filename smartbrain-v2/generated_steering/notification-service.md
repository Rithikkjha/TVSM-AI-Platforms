# notification-service

*Auto-generated from static code analysis*

## Service Overview
- **Language:** Java (Spring Boot @ 3.5.7)
- **Contacts:** shekharbachu123, sandhiya-ravichandran2002, PrashantVerma-TVS15168, santhosh-tvsd, Nivetha-Nehru
- **Purpose:** The TVS Motor Notification Service is designed to manage SMS, Email, and WhatsApp notifications through various service providers, including Infobip and Salesforce.
- **Domain:** above, access, advice, allowed, application, apps, architecture, args, argument, artifact

## Code Structure
```
📄 .gitignore
📄 AST_Image_Scan_notification_service_Pipeline.yml
📄 AST_notification_service_UAT_Pipeline.yml
📄 Create AST_notification_service_PROD_Pipeline.yml
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
| src/main/java/com/tvsmotor/notification/config/SalesforceBlobConfig.java | Contains configuration properties for processing Salesforce Blob Status. |
| src/main/java/com/tvsmotor/notification/handler/BlobStorageException.java | Defines an exception for failures in blob storage operations. |
| src/main/java/com/tvsmotor/notification/cronjobs/SalesforceBlobStatusJob.java | Executes a job to process Salesforce CSV files from Azure Blob Storage and updates the notification tracker with delivery statuses. This job is triggered via SalesforceStatusRunner when deployed as an AKS CronJob. |
| src/main/java/com/tvsmotor/notification/handler/BlobNotFoundException.java | Exception thrown when a specified blob file cannot be found. |
| src/main/java/com/tvsmotor/notification/model/ProcessedBlobFile.java | Maintains a record of processed blob files to avoid duplicate processing. |
| src/main/java/com/tvsmotor/notification/handler/InvalidMobileNumberException.java | Exception thrown when a mobile number is formatted incorrectly (e.g., in exponent form). |

## API Endpoints
| Method | Path | Description | File |
|--------|------|-------------|------|
| POST | /infobipAPIError/retry |  | src/main/java/com/tvsmotor/notification/controller/infobip/InfobipAPIErrorRetryController.java:20 |
| POST | /api/v1/notification/sms |  | src/main/java/com/tvsmotor/notification/controller/NotificationController.java:30 |
| POST | /api/v1/notification/email |  | src/main/java/com/tvsmotor/notification/controller/NotificationController.java:40 |
| POST | /api/v1/notification/whatsapp |  | src/main/java/com/tvsmotor/notification/controller/NotificationController.java:50 |
| GET | /api/v1/notification/{id} |  | src/main/java/com/tvsmotor/notification/controller/NotificationController.java:60 |
| GET | /api/v1/notification/{id}/status |  | src/main/java/com/tvsmotor/notification/controller/NotificationController.java:65 |
| POST | /api/v1/notification/user-preference/create |  | src/main/java/com/tvsmotor/notification/controller/NotificationUserPreferenceController.java:24 |
| GET | /api/v1/notification/user-preference/client/{clientId} |  | src/main/java/com/tvsmotor/notification/controller/NotificationUserPreferenceController.java:31 |
| GET | /api/v1/notification/user-preference/getAll |  | src/main/java/com/tvsmotor/notification/controller/NotificationUserPreferenceController.java:38 |
| PUT | /api/v1/notification/user-preference/update/{id} |  | src/main/java/com/tvsmotor/notification/controller/NotificationUserPreferenceController.java:43 |
| DELETE | /api/v1/notification/user-preference/delete/{id} |  | src/main/java/com/tvsmotor/notification/controller/NotificationUserPreferenceController.java:50 |
| DELETE | /api/v1/notification/user-preference/client/{clientId} |  | src/main/java/com/tvsmotor/notification/controller/NotificationUserPreferenceController.java:56 |
| GET | /health |  | src/main/java/com/tvsmotor/notification/controller/HealthCheckController.java:22 |
| GET | /api/v1/notification/retryPreference/{channel}/{priority} |  | src/main/java/com/tvsmotor/notification/controller/NotificationRetryPreferenceController.java:22 |
| DELETE | /api/v1/notification/retryPreference/{channel}/{priority}/{failureType} |  | src/main/java/com/tvsmotor/notification/controller/NotificationRetryPreferenceController.java:37 |
| DELETE | /api/v1/notification/retryPreference/{retryPreferenceId} |  | src/main/java/com/tvsmotor/notification/controller/NotificationRetryPreferenceController.java:42 |
| GET | /api/v1/notification/retryPreference |  | src/main/java/com/tvsmotor/notification/controller/NotificationRetryPreferenceController.java:27 |
| POST | /api/v1/notification/retryPreference |  | src/main/java/com/tvsmotor/notification/controller/NotificationRetryPreferenceController.java:32 |
| GET | /api/v1/notification/template/{id} |  | src/main/java/com/tvsmotor/notification/controller/NotificationTemplateController.java:22 |
| DELETE | /api/v1/notification/template/{id} |  | src/main/java/com/tvsmotor/notification/controller/NotificationTemplateController.java:37 |
| GET | /api/v1/notification/template |  | src/main/java/com/tvsmotor/notification/controller/NotificationTemplateController.java:27 |
| POST | /api/v1/notification/template |  | src/main/java/com/tvsmotor/notification/controller/NotificationTemplateController.java:32 |
| POST | /webhook/infobip/status-update |  | src/main/java/com/tvsmotor/notification/controller/infobip/InfobipCallbackController.java:20 |

## Dependencies (Outbound)
### Service Bus — Publishes
| Topic | Confidence | File |
|---|---|---|
| notifications | 🟢 high | src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java:37 |
| notifications.status-update | 🟢 high | src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java:39 |
| notification-revive | 🟢 high | src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java:41 |
| notification-revive-every-2-hours | 🟢 high | src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java:43 |
| notification-noreturn-nook | 🟢 high | src/main/java/com/tvsmotor/notification/config/ServiceBusConfig.java:45 |
| service-bus | 🟢 high | src/main/java/com/tvsmotor/notification/service_bus/ServiceBusNotifier.java:27 |

## Databases
| Type | Name | File |
|---|---|---|
| mongodb |  | pom.xml — mongodb dependency |

## Recent Activity
- **Last commit:** 2026-03-31 by PrashantVerma-TVS15168 — "CBS6-646[20260327]/SonarQube_reliability_issue_resolve (#218)"
- **Commit frequency:** inactive

## Architecture Notes
This service employs a modular architecture with clear separation of concerns, particularly in handling notifications and user preferences. The use of cron jobs for scheduled tasks indicates a robust approach to processing asynchronous operations.