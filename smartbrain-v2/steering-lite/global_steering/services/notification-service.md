# notification-service


## Product Context


# Notification Service — Product Context

## What This Service Does

TVS Motor Notification Service is a multi-channel notification gateway that accepts SMS, Email, and WhatsApp notification requests from internal client applications, validates them against registered templates, and dispatches them to external providers (Infobip, Salesforce) via Azure Service Bus. It tracks the full lifecycle of each notification from receipt through delivery or failure.

This service is the **intake and orchestration layer** — it does NOT directly call Infobip/Salesforce APIs. A separate **Notification Dispatcher Service** consumes from the Service Bus and handles actual delivery.

## Domain Entities

### NotificationTracker (Primary Entity)
- Central record for every notification sent through the system
- Stored in MongoDB collection `notification_tracker`
- Contains one of: `smsNotification`, `emailNotification`, or `whatsAppNotification`
- Tracks `serviceProvider` (INFOBIP, SALESFORCE) and `createdAt` timestamp
- Linked to delivery status via `ChannelStatus` (holds `InfobipData` and `SalesforceData` lists)

### NotificationTemplate
- Registered templates that define sender, body pattern, subject (email), channel type, and Salesforce keys
- Templates use `{#key#}` placeholder syntax for dynamic body/subject values
- Template IDs follow strict regex patterns: SMS = 19 digits, Email = 15 digits, WhatsApp = 13-25 digits
- Each template has a `templateOwner` used for Service Bus message routing

### NotificationUserPreference
- Per-client configuration mapping `clientId` to primary/secondary providers per channel
- Defaults to `INFOBIP` if no preference is registered
- Supports failover from primary to secondary provider

### NotificationRetryPreference
- Configurable retry rules keyed by `channel + priority + failureType`
- Defines `retryCount`, `retryChannel`, and target `queueName`
- Used to route failed notifications to retry queues or dead-letter queue

### ProcessedBlobFile
- Tracks Salesforce CSV blob files that have been processed (deduplication via fileName + fileHash)
- Records processing stats: recordsProcessed, recordsUpdated, recordsNotFound, recordsMultipleFound

## Integrations

### Azure Service Bus (Outbound)
- **Notification Topic**: Main topic where validated notifications are published for the Dispatcher Service
- **Status Update Topic**: Publishes status change events after Infobip callbacks
- **Revive Queue**: Retry queue for failed notifications (immediate retry)
- **Revive 2-Hour Queue**: Delayed retry queue, processed every 2 hours via scheduled job
- **No-Return Nook Queue**: Dead-letter queue for permanently failed notifications

### Infobip (Inbound Webhooks)
- Receives delivery status callbacks at `/webhook/infobip/status-update`
- Updates `ChannelStatus.infobipData` with delivery status, error details, and permanence flag
- Statuses: PENDING, DELIVERED, UNDELIVERABLE, EXPIRED, REJECTED

### Salesforce (Blob Storage Integration)
- Processes CSV files from Azure Blob Storage containing Salesforce delivery reports
- Matches records by mobile number + activity name + sent time (with ±60s tolerance)
- Updates `ChannelStatus.salesforceData` with delivery/undelivered status
- Deduplicates files using SHA-256 hash

### Azure Blob Storage
- Source of Salesforce delivery report CSV files
- Accessed via SAS URL configured per environment

### MongoDB
- Primary data store for all entities
- Collections: `notification_tracker`, `notification_template`, `notification_user_preference`, `notification_retry_preference`, `notification_processed_blob_files`

### Sentry
- Error monitoring and performance tracing (traces-sample-rate: 1.0)

## Business Rules

### Notification Processing
1. Every notification request MUST reference a registered template (validated by templateId regex + DB lookup)
2. Template body values must match the placeholders in the template — count and key names are validated
3. SMS phone numbers must match Indian mobile format: `^\\+?91[6789]\\d{9}$`
4. Email recipients are validated for duplicates and format
5. The `sender` field in the request must match the template's registered sender
6. Client identity is extracted from JWT `appid` claim in the Authorization header
7. Service provider is determined by the client's registered `NotificationUserPreference`; defaults to INFOBIP

### Status Lifecycle
- `RECEIVED_BY_NOTIFICATION_SERVICE` → `PUSHED_TO_SERVICEBUS` → `RECEIVED_BY_NOTIFICATION_DISPATCHER_SERVICE` → `SUCCESS` or `FAILURE`
- Failed notifications may enter `IN_RETRY` if a matching retry preference exists and the error is not permanent
- Retries are capped by `retryCount` in the preference; exceeded retries go to dead-letter queue

### Retry Logic
- Retry is triggered only for non-permanent Infobip errors
- Retry preference is looked up by `failureType + channel + priority`
- If no retry preference exists OR error is permanent → notification goes to No-Return Nook (DLQ)
- Email notifications currently skip retry (hardcoded check)

### Salesforce Blob Processing
- CSV files may use pipe (`"||"`) or comma delimiters (auto-detected)
- Mobile numbers in scientific notation (containing E/e) are rejected as invalid
- Records with multiple matching trackers are skipped (logged as MULTIPLE_FOUND)
- Files already processed (same name + hash + SUCCESS status) are skipped
- Processing happens in configurable batch sizes (default: 100)

### WhatsApp Specifics
- WhatsApp messages support SMS failover (`smsFailover` field)
- Header types (IMAGE, VIDEO, DOCUMENT, LOCATION, TEXT, NO_HEADER) require specific keys in header values



## Code Structure


# Notification Service — Structure & Architecture

## Directory Layout

```
notification-service/
├── .kiro/steering/              # Kiro steering files (this documentation)
├── src/main/java/com/tvsmotor/notification/
│   ├── NotificationApplication.java        # Spring Boot entry point
│   ├── config/                             # Spring configuration beans
│   │   ├── FilterConfig.java              # Registers servlet filters
│   │   ├── MongoAuditingConfig.java       # Enables @CreatedDate auditing
│   │   ├── NotificationOncePerFilter.java # JWT extraction filter (extracts clientId from token)
│   │   ├── SalesforceBlobConfig.java      # Blob storage SAS URL + batch size config
│   │   └── ServiceBusConfig.java          # Azure Service Bus clients (topics, queues, Caffeine cache)
│   ├── controller/                         # REST API layer
│   │   ├── HealthCheckController.java     # GET /health
│   │   ├── NotificationController.java    # POST /sms, /email, /whatsapp; GET /{id}, /{id}/status
│   │   ├── NotificationRetryPreferenceController.java  # CRUD for retry preferences
│   │   ├── NotificationTemplateController.java         # CRUD for templates
│   │   ├── NotificationUserPreferenceController.java   # CRUD for user preferences
│   │   └── infobip/
│   │       ├── InfobipCallbackController.java          # POST /webhook/infobip/status-update
│   │       └── InfobipAPIErrorRetryController.java     # POST /infobipAPIError/retry
│   ├── cronjobs/
│   │   └── SalesforceBlobStatusJob.java   # Scheduled job for Salesforce blob processing
│   ├── enums/                              # Domain enumerations
│   │   ├── NotificationPriority.java      # HIGH, LOW
│   │   ├── NotificationStatus.java        # RECEIVED_BY_NOTIFICATION_SERVICE, PUSHED_TO_SERVICEBUS, etc.
│   │   ├── NotificationType.java          # SMS, EMAIL, WHATSAPP, IN_APP
│   │   ├── ServiceProvider.java           # INFOBIP, SALESFORCE, NOT_REGISTERED
│   │   ├── TemplateCategory.java          # UTILITY, AUTHENTICATION, MARKETING
│   │   ├── WhatsAppHeaderType.java        # IMAGE, LOCATION, VIDEO, DOCUMENT, TEXT, NO_HEADER
│   │   ├── infobip/InfobipNotificationStatus.java     # PENDING, DELIVERED, UNDELIVERABLE, EXPIRED, REJECTED
│   │   └── salesforce/BlobUpdateStatus.java           # UPDATED, NOT_FOUND, SKIPPED, MULTIPLE_FOUND
│   ├── handler/                            # Exception handlers & custom validators
│   │   ├── ValidationHandler.java         # @ControllerAdvice — global error handling
│   │   ├── BlobNotFoundException.java     # Custom exception
│   │   ├── BlobStorageException.java      # Custom exception
│   │   ├── InfobipDataNotFoundException.java
│   │   ├── InvalidMobileNumberException.java
│   │   ├── MultipleReportsException.java
│   │   ├── NotificationTemplateNotFoundException.java
│   │   ├── NotificationPriorityDeserializer.java      # Custom Jackson deserializer
│   │   ├── ValidEmailSet.java / EmailSetValidator.java         # Custom annotation + validator
│   │   └── NoDuplicateEmails.java / NoDuplicateEmailValidator.java  # Custom annotation + validator
│   ├── model/                              # MongoDB document entities
│   │   ├── NotificationTracker.java       # Primary entity (@Document)
│   │   ├── NotificationTemplate.java
│   │   ├── NotificationUserPreference.java
│   │   ├── NotificationRetryPreference.java
│   │   ├── ProcessedBlobFile.java
│   │   └── dto/                           # Data Transfer Objects
│   │       ├── ClientContext.java         # ThreadLocal holder for JWT clientId
│   │       ├── ProcessingResult.java      # Blob processing summary DTO
│   │       ├── TemplateValidationContext.java  # Generic validation context
│   │       ├── request/                   # Inbound request DTOs
│   │       │   ├── Notification.java      # Base class (priority, status, channelStatus, retries)
│   │       │   ├── NotificationCommonAttributes.java  # Abstract base (templateOwner)
│   │       │   ├── SMSNotification.java / SMS.java
│   │       │   ├── EmailNotification.java / Email.java
│   │       │   ├── WhatsAppNotification.java / WhatsApp.java
│   │       │   ├── ChannelStatus.java     # Holds InfobipData + SalesforceData lists
│   │       │   ├── NotificationTemplateRequest.java
│   │       │   ├── NotificationUserPreferenceRequest.java
│   │       │   ├── NotificationRetryPreferenceRequest.java
│   │       │   └── RetryRequest.java      # For Infobip API error retry
│   │       ├── response/                  # Outbound response DTOs
│   │       │   ├── NotificationResponse.java
│   │       │   ├── StatusResponse.java
│   │       │   ├── NotificationRetryPreferenceResponse.java
│   │       │   └── NotificationTemplateResponse.java
│   │       ├── infobip/                   # Infobip webhook payload DTOs
│   │       │   ├── InfobipData.java
│   │       │   ├── InfobipNotificationReport.java
│   │       │   ├── InfobipNotificationReports.java
│   │       │   ├── InfobipNotificationDeliveryStatus.java
│   │       │   └── InfobipNotificationDeliveryError.java
│   │       └── salesforce/                # Salesforce integration DTOs
│   │           ├── SalesforceData.java
│   │           └── SalesforceTemplateKeys.java
│   ├── repository/                         # Spring Data MongoDB repositories
│   │   ├── NotificationTrackerRepository.java
│   │   ├── NotificationTemplateRepository.java
│   │   ├── NotificationUserPreferenceRepository.java
│   │   ├── NotificationRetryPreferenceRepository.java
│   │   └── ProcessedBlobFileRepository.java
│   ├── runner/
│   │   └── SalesforceStatusRunner.java    # ApplicationRunner for startup blob processing
│   ├── service/                            # Business logic layer
│   │   ├── NotificationService.java       # Core orchestration: validate → create tracker → push to bus
│   │   ├── NotificationTemplateService.java
│   │   ├── NotificationUserPreferenceService.java
│   │   ├── NotificationRetryPreferenceService.java  # Retry logic + DLQ routing
│   │   ├── SalesforceBlobStatusService.java         # CSV parsing + MongoDB update
│   │   ├── creator/                       # Factory pattern — creates NotificationTracker from request
│   │   │   ├── NotificationStatusCreator.java       # Interface/abstract
│   │   │   ├── SMSNotificationCreator.java
│   │   │   ├── EmailNotificationCreator.java
│   │   │   └── WhatsAppNotificationCreator.java
│   │   ├── updator/                       # Factory pattern — updates status on tracker
│   │   │   ├── NotificationStatusUpdater.java       # Interface/abstract
│   │   │   ├── SmsNotificationUpdater.java
│   │   │   ├── EmailNotificationUpdater.java
│   │   │   └── WhatsAppNotificationUpdater.java
│   │   ├── factory/                       # Factory registries (EnumMap-based)
│   │   │   ├── NotificationCreatorFactory.java
│   │   │   └── NotificationUpdaterFactory.java
│   │   ├── infobip/
│   │   │   └── InfobipCallbackService.java  # Processes Infobip webhook reports
│   │   └── validator/                     # Channel-specific validation
│   │       ├── SMSValidator.java
│   │       ├── EmailValidator.java
│   │       └── WhatsAppValidator.java
│   ├── service_bus/                        # Azure Service Bus integration
│   │   ├── ServiceBusNotifier.java        # Sends messages to topics/queues
│   │   └── QueueToTopicService.java       # Scheduled: drains 2-hour retry queue back to topic
│   └── utils/                              # Utility classes and constants
│       ├── Constants.java                 # Interface with static constants
│       ├── LogConstants.java              # Centralized log message templates
│       ├── InfobipAPIConstants.java       # Infobip-specific constants
│       ├── JWTUtil.java                   # JWT payload extraction (appid claim)
│       ├── NotificationsUtil.java         # Shared validation helpers
│       ├── ChannelStatusUtil.java         # ChannelStatus initialization
│       ├── ServiceBusMessageUtil.java     # Service Bus message construction
│       └── BlobFileProcessorUtil.java     # Blob download + processing orchestration
├── src/main/resources/
│   ├── application.properties             # Base config (env vars, swagger, sentry, logging)
│   ├── application-local.properties       # Local MongoDB + Service Bus config
│   ├── application-dev.properties
│   ├── application-uat.properties
│   ├── application-prod.properties
│   ├── ValidationMessages.properties      # Externalized validation error messages
│   └── db.migration/                      # MongoDB migration scripts (JS)
├── src/test/
│   ├── java/com/tvsmotor/notification/   # Mirrors main structure
│   └── resources/
│       ├── application.properties         # Test config
│       └── mockito-extensions/            # Mockito inline mock support
├── Dockerfile                             # Multi-stage: Maven build → Amazon Corretto 21 runtime
├── pom.xml                                # Maven project descriptor
├── ci-pipeline.yaml                       # Azure DevOps CI pipeline
├── cd-pipeline.yaml                       # Azure DevOps CD pipeline (dev → uat → prod)
└── sonar_ci_pr_pipeline.yml               # SonarQube PR analysis pipeline
```

## Module Dependencies (Internal Flow)

```
Controller → Validator → Service → Repository
                              ↓
                        ServiceBusNotifier → Azure Service Bus
                              ↓
                    Creator/Updater Factories
```

1. **Controllers** receive HTTP requests, delegate validation to channel-specific validators
2. **Validators** check template existence, field matching, format constraints
3. **NotificationService** orchestrates: creates tracker via factory, determines provider, pushes to Service Bus
4. **Factories** (Creator/Updater) use EnumMap dispatch to select channel-specific implementations
5. **ServiceBusNotifier** serializes tracker to JSON and sends to appropriate topic/queue
6. **InfobipCallbackService** processes inbound webhooks, updates tracker, triggers retry logic
7. **SalesforceBlobStatusService** processes CSV files, updates trackers via MongoTemplate queries

## Architectural Decisions

### Factory Pattern for Channel Dispatch
- `NotificationCreatorFactory` and `NotificationUpdaterFactory` use `EnumMap<NotificationType, ...>` initialized at `@PostConstruct`
- Avoids switch statements in service layer; new channels require only a new creator/updater + factory registration

### ThreadLocal for Client Identity
- `ClientContext` uses `ThreadLocal<String>` to propagate JWT-extracted `clientId` through the request lifecycle
- Set in `NotificationOncePerFilter`, cleared in `finally` block

### Caffeine Cache for Service Bus Clients
- `ServiceBusSenderClient` instances for queues are cached with TTL-based expiration
- Avoids creating new connections per message; auto-closes on eviction

### Async Dispatch via Service Bus
- Notifications are NOT sent synchronously to providers
- The service publishes to Azure Service Bus topics; a separate Dispatcher Service handles delivery
- This decouples intake from delivery, enabling independent scaling and retry

### MongoDB as Primary Store
- All entities use Spring Data MongoDB repositories
- `MongoTemplate` used directly for complex queries (Salesforce blob matching with elemMatch)
- Auditing enabled for `@CreatedDate` fields

### Validation Strategy
- Two-layer validation: Jakarta Bean Validation annotations + custom programmatic validators
- Custom validators handle template-specific business rules (body value matching, sender verification)
- `ValidationHandler` (@ControllerAdvice) provides consistent error response format

### Scheduled Jobs
- `QueueToTopicService`: Every 2 hours, drains retry queue back to main topic
- `SalesforceBlobStatusJob`: Cron-triggered Salesforce CSV processing



## Tech Stack & Dependencies


# Notification Service — Tech Stack & Conventions

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 17 |
| Framework | Spring Boot | 3.5.7 |
| Build | Maven | 3.9.14 (Docker) |
| Database | MongoDB | via Spring Data MongoDB |
| Messaging | Azure Service Bus | SDK 7.17.17 |
| Blob Storage | Azure Blob Storage | SDK 12.25.1 |
| Queue Storage | Azure Storage Queue | SDK 12.26.2 |
| HTTP Client | Spring WebFlux (WebClient) | via starter |
| Caching | Caffeine | 3.2.2 |
| Validation | Jakarta Bean Validation | via spring-boot-starter-validation |
| API Docs | SpringDoc OpenAPI | 1.8.0 |
| Monitoring | Sentry (Logback) | 8.26.0 |
| Serialization | Jackson | 2.21.2 |
| Boilerplate | Lombok | managed by Spring Boot |
| Testing | JUnit 5 + Mockito + AssertJ + LogCaptor | |
| Coverage | JaCoCo | 0.8.11 (80% line coverage minimum) |
| Container | Amazon Corretto 21 (runtime) | al2023-headless |
| CI/CD | Azure DevOps Pipelines | |
| Code Quality | SonarQube | via dedicated pipeline |

## Coding Conventions

### Naming
- Package: `com.tvsmotor.notification.<layer>` (controller, service, model, repository, etc.)
- Classes: PascalCase, suffixed by role (`*Controller`, `*Service`, `*Repository`, `*Validator`, `*Creator`, `*Updater`)
- Constants: defined in `Constants.java` interface as `String` fields (not enum, not class)
- Log messages: centralized in `LogConstants.java` as static string templates with SLF4J `{}` placeholders
- Enums: UPPER_SNAKE_CASE values

### Lombok Usage
- `@Data`, `@Builder` / `@SuperBuilder`, `@AllArgsConstructor`, `@NoArgsConstructor` on all DTOs and models
- `@RequiredArgsConstructor` + `private final` fields for constructor injection (no `@Autowired` on fields)
- `@Slf4j` for logging
- `@SneakyThrows` used sparingly in Service Bus code

### Dependency Injection
- Constructor injection via `@RequiredArgsConstructor` (preferred)
- `@Autowired` constructor only when `@Qualifier` is needed (e.g., `ServiceBusNotifier`)
- `@Bean` with `@Qualifier` names for multiple beans of same type

### API Design
- Base path: `/api/v1/notification`
- RESTful conventions: POST for create/send, GET for fetch, PUT for update, DELETE for remove
- Response wrapper: `NotificationResponse` with `isValid`, `message`, `notificationId`, `notification` fields
- Validation errors return HTTP 400 with structured error map

### Configuration
- Environment-specific profiles: `local`, `dev`, `uat`, `prod`
- Secrets via environment variables (never hardcoded): `${SERVICE_BUS_CONNECTION_STRING}`, `${SENTRY_DSN}`, etc.
- Base `application.properties` references env vars; profile files override connection details
- Timezone: `Asia/Kolkata` (set in Dockerfile)

## Patterns

### Factory Pattern
- `NotificationCreatorFactory`: maps `NotificationType` → `NotificationStatusCreator<T>` implementation
- `NotificationUpdaterFactory`: maps `NotificationType` → `NotificationStatusUpdater` implementation
- Both use `EnumMap` initialized in `@PostConstruct`
- Adding a new channel: create Creator + Updater classes, register in both factories

### Inheritance Hierarchy (DTOs)
```
NotificationCommonAttributes (abstract: templateOwner)
  └── SMS / Email / WhatsApp

Notification (base: priority, status, channelStatus, retries)
  ├── SMSNotification (has SMS)
  ├── EmailNotification (has Email)
  └── WhatsAppNotification (has WhatsApp)
```

### ThreadLocal Context
- `ClientContext.setClientId()` in filter → used in service layer → `ClientContext.clear()` in finally
- Enables per-request client identification without passing clientId through every method

### Service Bus Message Routing
- Messages carry application properties: `priority`, `notificationType`, `templateOwner`, `isStatusReport`
- Used by Dispatcher Service subscriptions for filtering

## Error Handling

### Global Exception Handler (`ValidationHandler`)
- Extends `ResponseEntityExceptionHandler`
- Handles `MethodArgumentNotValidException` → field-level error map
- Handles `HttpMessageNotReadableException` → JSON parse errors with line/column info, mapping errors with field path
- Returns HTTP 400 with `{valid: false, message: "..."}` structure

### Custom Exceptions
- `BlobNotFoundException`, `BlobStorageException` — Salesforce blob processing
- `InvalidMobileNumberException` — scientific notation in phone numbers
- `MultipleReportsException` — multiple Infobip reports in single webhook (rejected)
- `InfobipDataNotFoundException` — missing Infobip data in tracker
- `NotificationTemplateNotFoundException` — template lookup failure

### Validation Error Formatting
- Errors wrapped in square brackets: `[error message]`
- Multiple errors comma-separated: `[error1], [error2]`
- Custom validators return `NotificationResponse` with `isValid=false` and formatted message

### Logging
- SLF4J via Lombok `@Slf4j`
- All log message templates in `LogConstants.java`
- Levels: INFO for flow tracking, WARN for recoverable issues, ERROR for failures
- Structured context: notification type, tracker ID, message ID included in log entries

## Testing

### Framework & Tools
- JUnit 5 (`@ExtendWith(MockitoExtension.class)`)
- Mockito for mocking (`@Mock`, `@InjectMocks`, `lenient().when(...)`)
- Mockito Inline for static method mocking
- AssertJ for fluent assertions
- LogCaptor for verifying log output

### Test Structure
- Mirrors main source: `src/test/java/com/tvsmotor/notification/<layer>/`
- Test class naming: `<ClassName>Test.java`
- Tests cover: services, validators, controllers, factories, service bus, utils

### Coverage Requirements
- JaCoCo enforces **80% line coverage** at PACKAGE level
- Excluded from coverage: `config/`, `enums/`, `model/`, `model/dto/`, `Constants`, `LogConstants`, `InfobipAPIConstants`, `BlobFileProcessorUtil`, `NotificationApplication`, `cronjobs/`, `runner/`, blob exceptions

### Test Patterns
- Builder pattern for test data construction (Lombok `@Builder`)
- `@BeforeEach` for service instantiation with mocks
- Verify interactions with `verify()`, `never()`, `times()`
- Test both success and failure paths
- No integration tests (pure unit tests with mocked dependencies)

## Deployment

### Docker
- Multi-stage build: Maven 3.9.14 + Corretto 17 (build) → Corretto 21 (runtime)
- JVM flag: `-XX:MaxRAMPercentage=75` (container-aware memory)
- Exposes port 8080
- Timezone set to `Asia/Kolkata`

### CI/CD (Azure DevOps)
- **CI Pipeline** (`ci-pipeline.yaml`): triggered by SonarQube pipeline completion on `main`; uses shared build template from `Devops_ISSM_pipelines` repo
- **CD Pipeline** (`cd-pipeline.yaml`): multi-stage deployment: dev → uat (manual approval) → prod (manual approval)
- **SonarQube Pipeline** (`sonar_ci_pr_pipeline.yml`): PR-triggered code quality analysis
- **AST Pipelines**: image scanning for UAT and PROD
- Deployment via Helm charts (chart name matches service name: `notification`)
- Approval gates with email notifications to team leads

### Environments
- `dev` — auto-deploys after CI
- `uat` — requires manual approval (24h timeout)
- `prod` — requires manual approval (24h timeout), depends on UAT success

### Database Migrations
- JavaScript files in `src/main/resources/db.migration/`
- Naming: `v<version>_<collection>_<date>.js`
- Applied manually or via deployment scripts (not auto-run by app)

