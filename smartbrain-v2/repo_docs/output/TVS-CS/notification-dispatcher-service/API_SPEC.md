---
service_id: notification-dispatcher-service
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# notification-dispatcher-service — API Specification

## Authentication
notification-dispatcher-service endpoint auth as extracted: `None` × 3.
Unknown — no auth middleware or annotations found in code.

## Endpoint Index
notification-dispatcher-service exposes 3 HTTP endpoint(s) and 1 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| GET | `/health` | Unknown | handler `HealthCheckController.healthTest` | Unknown |
| POST | `/api/v1/notifications/push` | Unknown | handler `PushNotificationController.sendPushNotification` | Unknown |
| POST | `/salesforce/refresh-token` | Unknown | handler `SalesforceTokenController.refreshToken` | Unknown |

Scheduled jobs:

| Job | Trigger | Expression | Handler |
|---|---|---|---|
| `ThreadPoolMonitor.logThreadPoolStats` | fixed-rate | `60000` (literal) | `src/main/java/com/tvsmotor/notificationdispatcher/service/ThreadPoolMonitor.java:15` |

## Endpoints
notification-dispatcher-service endpoint details (from inventory `inbound_http`).

### GET /health
Handler: `HealthCheckController.healthTest` in `src/main/java/com/tvsmotor/notificationdispatcher/controller/HealthCheckController.java:23`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| beacon | query | string | True | |

Response `200`: `object`

### POST /api/v1/notifications/push
Handler: `PushNotificationController.sendPushNotification` in `src/main/java/com/tvsmotor/notificationdispatcher/controller/PushNotificationController.java:22`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| request | body | PushNotificationRequest | True | |

Request body: `PushNotificationRequest` (defined in `src/main/java/com/tvsmotor/notificationdispatcher/model/dto/request/PushNotificationRequest.java:12`)

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| title | string | True | - |
| body | string | True | - |
| deviceTokens | string[] | True | - |
| data | map<string,string> | False | - |

Response `200`: `PushNotificationResponse`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| success | boolean | False | - |
| message | string | False | - |
| deviceCount | integer | False | - |

### POST /salesforce/refresh-token
Handler: `SalesforceTokenController.refreshToken` in `src/main/java/com/tvsmotor/notificationdispatcher/controller/SalesforceTokenController.java:19`. Purpose: Unknown. Callers: Unknown.

Response `200`: `map<string,object>`

## Outbound Calls
notification-dispatcher-service outbound HTTP calls (7 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| `external:firebase` | - | - | - | - | Unknown | Unknown |
| `external:salesforce` | - | - | - | - | Unknown | hard |
| Unknown (unknown) | POST | `/email/3/send` | - | InfobipNotificationReports | Unknown | Unknown |
| Unknown (unknown) | POST | `/sms/2/text/advanced` | map<string,object> | InfobipNotificationReports | Unknown | Unknown |
| Unknown (config:infobip.baseUri) | POST | `/email/3/send` | - | InfobipNotificationReports | Unknown | Unknown |
| Unknown (config:infobip.baseUri) | POST | `/messages-api/1/messages` | map<string,object> | InfobipNotificationReports | Unknown | Unknown |
| Unknown (config:salesforce.api.authUrl) | POST | `/` | map<string,string> | SalesforceTokenResponse | Unknown | Unknown |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| POST | `/email/3/send` | webclient | unknown | `src/main/java/com/tvsmotor/notificationdispatcher/service/email/infobip/InfobipEmailSender.java:81` |
| POST | `/sms/2/text/advanced` | webclient | unknown | `src/main/java/com/tvsmotor/notificationdispatcher/service/sms/infobip/InfobipSMSSender.java:83` |
| POST | `/email/3/send` | webclient | config:infobip.baseUri | `src/main/java/com/tvsmotor/notificationdispatcher/config/WebClientConfiguration.java:17` |
| POST | `/messages-api/1/messages` | webclient | config:infobip.baseUri | `src/main/java/com/tvsmotor/notificationdispatcher/config/WebClientConfiguration.java:17` |
| POST | `/` | webclient | config:salesforce.api.authUrl | `src/main/java/com/tvsmotor/notificationdispatcher/config/WebClientConfiguration.java:49` |

## Schemas
notification-dispatcher-service DTOs/payloads referenced in this file.

### PushNotificationRequest
Defined in: `src/main/java/com/tvsmotor/notificationdispatcher/model/dto/request/PushNotificationRequest.java:12`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| title | string | True | - |
| body | string | True | - |
| deviceTokens | string[] | True | - |
| data | map<string,string> | False | - |

### PushNotificationResponse
Defined in: `src/main/java/com/tvsmotor/notificationdispatcher/model/dto/response/PushNotificationResponse.java:6`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| success | boolean | False | - |
| message | string | False | - |
| deviceCount | integer | False | - |

### InfobipNotificationReports
Defined in: `src/main/java/com/tvsmotor/notificationdispatcher/model/dto/infobip/InfobipNotificationReports.java:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| bulkId | string | False | - |
| messages | InfobipNotificationReport[] | False | - |

### SalesforceTokenResponse
Defined in: `src/main/java/com/tvsmotor/notificationdispatcher/model/dto/salesforce/SalesforceTokenResponse.java:9`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| access_token | string | False | - |
| token_type | string | False | - |
| expires_in | string | False | - |

## Events Published
notification-dispatcher-service publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
notification-dispatcher-service consumes 1 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| local.notifications | email-notifications, fcmpush-notifications, highpriority-notifications, sms-notifications, whatsapp-notifications | - | - | Unknown | `src/main/java/com/tvsmotor/notificationdispatcher/config/ServiceBusConfig.java:88` | notification-service | Unknown | {"error_handler": true} |

## External Integrations
notification-dispatcher-service third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| `external:firebase` | category other; matched `com.google.firebase:firebase-admin` at `pom.xml:178` | Unknown |
| `external:salesforce` | category crm; matched `SalesforceAuthGen` at `src/main/java/com/tvsmotor/notificationdispatcher/controller/SalesforceTokenController.java:18` | Unknown |

## Rate Limits and SLAs
notification-dispatcher-service: N/A — not determinable from code.
