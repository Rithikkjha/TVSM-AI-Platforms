# notification-dispatcher-service


## Product Context


# Notification Dispatcher Service — Product Context

## What This Service Does

The Notification Dispatcher Service is the downstream delivery component of TVS Motor's notification platform. It consumes notification requests from Azure Service Bus and dispatches them to external providers (Infobip, Salesforce) across multiple channels: SMS, Email, and WhatsApp.

This service does NOT accept HTTP requests for sending notifications. It is purely event-driven — messages arrive via Service Bus topic subscriptions and are processed asynchronously.

## Domain Entities

### NotificationTracker (MongoDB: `notification_tracker`)
The central aggregate. Tracks the lifecycle of a single notification request across channels. Contains:
- `id` — unique identifier (MongoDB ObjectId)
- `serviceProvider` — which provider to use (INFOBIP, SALESFORCE, NOT_REGISTERED)
- `smsNotification` — SMS channel payload and status
- `emailNotification` — Email channel payload and status
- `whatsAppNotification` — WhatsApp channel payload and status
- `createdAt` — timestamp of creation

A single tracker can carry payloads for multiple channels simultaneously (used in high-priority notifications).

### NotificationTemplate (MongoDB: `notification_template`)
Stores template metadata used for WhatsApp and Salesforce SMS dispatch:
- `templateId` — external template identifier
- `templateName` — human-readable name (used in Infobip WhatsApp API)
- `templateOwner` — owning team/system
- `channelType` — SMS, EMAIL, WHATSAPP
- `templateCategory` — UTILITY, AUTHENTICATION, MARKETING (WhatsApp Business API categories)
- `language` — template language code
- `sender` — sender identifier
- `headerType` — WhatsApp header type (IMAGE, LOCATION, VIDEO, DOCUMENT, TEXT, NO_HEADER)
- `subject` — email subject template
- `body` — message body template
- `salesforceTemplateKeys` — Salesforce-specific keys (eventDefinitionKey, eventType, activityName)

### Notification (base DTO)
Common attributes for all channel-specific notifications:
- `priority` — HIGH or LOW (affects routing and provider selection)
- `status` — lifecycle state (RECEIVED_BY_NOTIFICATION_SERVICE → PUSHED_TO_SERVICEBUS → RECEIVED_BY_NOTIFICATION_DISPATCHER_SERVICE → IN_RETRY → FAILURE)
- `channelStatus` — delivery result from providers (infobipData, salesforceData)
- `retries` — retry count

### Channel-Specific DTOs
- **SMS**: templateId, sender, toPhoneNumber, bodyValues, body
- **Email**: templateId, sender, to (set), cc (set), sameThread flag, subjectValues, bodyValues
- **WhatsApp**: templateId, sender, toPhoneNumber, bodyValues, headerValues, smsFailover (optional SMS fallback)

## External Integrations

### Azure Service Bus (Inbound)
- Topic: configurable via `SERVICE_BUS_MAIN_TOPIC_NAME`
- Subscriptions: `highpriority-notifications`, `email-notifications`, `sms-notifications`, `whatsapp-notifications`
- Mode: PEEK_LOCK with manual complete/abandon
- Concurrency: 250 max concurrent calls per processor, backed by a 30-thread pool

### Infobip (Outbound — SMS, Email, WhatsApp)
- SMS API: `/sms/2/text/advanced`
- Email API: `/email/3/send`
- WhatsApp API: `/messages-api/1/messages`
- Auth: API key in Authorization header
- Separate base URLs and auth for OTP (high-priority) vs standard notifications
- Webhook callback for delivery status updates

### Salesforce Marketing Cloud (Outbound — SMS)
- Journey Builder Event API for triggering SMS sends
- OAuth2 client_credentials flow for authentication
- Token cached with 17-minute TTL (Caffeine)
- Auto-refresh on 401 Unauthorized via Spring Retry

### Infobip Retry Service (Outbound)
- HTTP POST to a separate retry microservice when Infobip returns 4xx/5xx errors
- Sends a `RetryRequest` containing the tracker, error report, and notification type

### Notification Service (Outbound — Webhook)
- Status update callback API for delivery reports from Infobip

### Sentry (Observability)
- APM and error tracking integration

## Business Rules

1. **Subscription-based routing**: The Service Bus subscription name determines which channel handler processes the message.

2. **High-priority notifications** can contain multiple channel payloads (SMS + Email + WhatsApp) and all present channels are dispatched in sequence.

3. **Provider selection for SMS**: Determined by `serviceProvider` field on the tracker AND feature flags (`notification.sendInfobipNotification.value`, `notification.sendSalesforceNotification.value`). Both must align for dispatch to occur.

4. **Email and WhatsApp** are currently Infobip-only, gated by the `sendInfobipNotification` flag.

5. **Priority affects routing**: HIGH priority SMS/Email uses a different Infobip base URL and auth (OTP channel). LOW priority uses the standard channel.

6. **Email domain selection**: Transactional (HIGH priority) emails use one domain, promotional (LOW priority) use another.

7. **WhatsApp SMS failover**: When enabled (`whatsapp.smsfailover.sendsms`), WhatsApp messages include an SMS failover channel in the Infobip multi-channel API.

8. **India DLT compliance**: SMS messages include `principalEntityId` and `contentTemplateId` for India's DLT regulatory requirements.

9. **Status tracking**: The service updates the tracker status to `RECEIVED_BY_NOTIFICATION_DISPATCHER_SERVICE` upon receipt, then updates with provider response data after dispatch. Updates are only persisted if the status actually changed.

10. **Error handling with retry delegation**: On 4xx/5xx errors from Infobip, the service records the error in the tracker and delegates retry to a separate retry microservice. It does NOT retry inline (except Salesforce 401 which retries once with token refresh).

11. **Salesforce token management**: Tokens are cached for 17 minutes. On 401, the token is refreshed via `@CachePut` and the request retried (max 2 attempts via Spring Retry). A manual refresh endpoint exists at `POST /salesforce/refresh-token`.

12. **Template lookup**: WhatsApp and Salesforce SMS require template data from MongoDB. If the template is not found, a `TemplateIdNotFoundException` is thrown.



## Code Structure


# Notification Dispatcher Service — Project Structure

## Directory Layout

```
notification-dispatcher-service/
├── pom.xml                          # Maven build config (Spring Boot 3.5.7, Java 17)
├── Dockerfile                       # Multi-stage: maven build → amazoncorretto:21 runtime
├── ci-pipeline.yaml                 # Azure DevOps CI (extends shared build-template)
├── cd-pipeline.yaml                 # Azure DevOps CD (dev → uat → prod with manual gates)
├── AST_*.yml                        # Image scanning and environment-specific pipeline triggers
├── sonar_ci_pr_pipeline.yml         # SonarQube PR analysis pipeline
│
└── src/
    ├── main/
    │   ├── java/com/tvsmotor/notificationdispatcher/
    │   │   ├── NotificationDispatcherApplication.java   # Spring Boot entry point
    │   │   │
    │   │   ├── config/                  # Spring @Configuration classes
    │   │   │   ├── BeanCreator.java         # ObjectMapper (with JavaTimeModule), HttpClient beans
    │   │   │   ├── CacheConfiguration.java  # Caffeine cache (Salesforce token, 17min TTL)
    │   │   │   ├── ServiceBusConfig.java    # 4 ServiceBusProcessorClient beans + ThreadPoolExecutor(30)
    │   │   │   └── WebClientConfiguration.java  # WebClient beans for Infobip + Salesforce
    │   │   │
    │   │   ├── controller/              # REST endpoints (minimal — not the primary interface)
    │   │   │   ├── HealthCheckController.java       # Health probe
    │   │   │   └── SalesforceTokenController.java   # POST /salesforce/refresh-token
    │   │   │
    │   │   ├── enums/                   # Domain enumerations
    │   │   │   ├── NotificationPriority.java    # HIGH, LOW
    │   │   │   ├── NotificationStatus.java      # Lifecycle states
    │   │   │   ├── NotificationType.java        # SMS, EMAIL, WHATSAPP, INAPP
    │   │   │   ├── ServiceProvider.java         # INFOBIP, SALESFORCE, NOT_REGISTERED
    │   │   │   ├── TemplateCategory.java        # UTILITY, AUTHENTICATION, MARKETING
    │   │   │   ├── WhatsAppHeaderType.java      # IMAGE, LOCATION, VIDEO, DOCUMENT, TEXT, NO_HEADER
    │   │   │   └── infobip/
    │   │   │       └── InfobipNotificationStatus.java  # PENDING, UNDELIVERABLE, DELIVERED, EXPIRED, REJECTED
    │   │   │
    │   │   ├── exceptions/
    │   │   │   └── TemplateIdNotFoundException.java  # Thrown when template lookup fails
    │   │   │
    │   │   ├── model/                   # MongoDB documents
    │   │   │   ├── NotificationTemplate.java    # Template metadata (collection: notification_template)
    │   │   │   ├── NotificationTracker.java     # Central aggregate (collection: notification_tracker)
    │   │   │   └── dto/
    │   │   │       ├── request/             # Inbound message DTOs
    │   │   │       │   ├── Notification.java                # Base class (priority, status, channelStatus)
    │   │   │       │   ├── NotificationCommonAttributes.java # Shared: templateOwner
    │   │   │       │   ├── SMSNotification.java             # extends Notification + SMS
    │   │   │       │   ├── EmailNotification.java           # extends Notification + Email
    │   │   │       │   ├── WhatsAppNotification.java        # extends Notification + WhatsApp
    │   │   │       │   ├── SMS.java                         # SMS payload fields
    │   │   │       │   ├── Email.java                       # Email payload fields
    │   │   │       │   ├── WhatsApp.java                    # WhatsApp payload fields
    │   │   │       │   ├── ChannelStatus.java               # Provider response container
    │   │   │       │   └── RetryRequest.java                # Retry delegation payload
    │   │   │       ├── infobip/             # Infobip API response DTOs
    │   │   │       │   ├── InfobipData.java
    │   │   │       │   ├── InfobipNotificationReport.java
    │   │   │       │   ├── InfobipNotificationReports.java
    │   │   │       │   ├── InfobipNotificationDeliveryStatus.java
    │   │   │       │   └── InfobipNotificationDeliveryError.java
    │   │   │       └── salesforce/          # Salesforce API DTOs
    │   │   │           ├── SalesforceData.java
    │   │   │           ├── SalesforceTemplateKeys.java
    │   │   │           └── SalesforceTokenResponse.java
    │   │   │
    │   │   ├── repository/              # MongoDB repositories
    │   │   │   ├── NotificationTrackerRepository.java       # MongoRepository<NotificationTracker>
    │   │   │   ├── NotificationTemplateRepository.java      # MongoRepository<NotificationTemplate>
    │   │   │   └── NotificationTemplateRepositoryWrapper.java  # findOrThrow wrapper
    │   │   │
    │   │   ├── service/                 # Core business logic
    │   │   │   ├── NotificationDispatcherService.java   # Orchestrator: routes messages to senders
    │   │   │   ├── NotificationSender.java              # Interface: sendNotification(tracker)
    │   │   │   ├── NotificationSenderFactory.java       # Factory: type → sender implementation
    │   │   │   ├── EmailSender.java                     # Interface: sendEmail(tracker)
    │   │   │   ├── SMSSender.java                       # Interface: sendSMS(tracker)
    │   │   │   ├── WhatsAppSender.java                  # Interface: sendWhatsApp(tracker)
    │   │   │   ├── InfobipAPIErrorRetryService.java     # Delegates failed requests to retry service
    │   │   │   ├── ThreadPoolMonitor.java               # Scheduled logging of thread pool stats
    │   │   │   │
    │   │   │   ├── email/
    │   │   │   │   ├── EmailNotificationSender.java     # NotificationSender impl (delegates to Infobip)
    │   │   │   │   └── infobip/
    │   │   │   │       └── InfobipEmailSender.java      # EmailSender impl (Infobip Email API)
    │   │   │   │
    │   │   │   ├── sms/
    │   │   │   │   ├── SMSNotificationSender.java       # NotificationSender impl (routes to provider)
    │   │   │   │   ├── infobip/
    │   │   │   │   │   └── InfobipSMSSender.java        # SMSSender impl (Infobip SMS API)
    │   │   │   │   └── salesforce/
    │   │   │   │       ├── SalesforceSMSSender.java     # SMSSender impl (Salesforce Journey API)
    │   │   │   │       └── SalesforceAuthGen.java       # OAuth token management with caching
    │   │   │   │
    │   │   │   ├── whatsapp/
    │   │   │   │   ├── WhatsAppNotificationSender.java  # NotificationSender impl (delegates to Infobip)
    │   │   │   │   └── infobip/
    │   │   │   │       └── InfobipWhatsAppSender.java   # WhatsAppSender impl (Infobip Messages API)
    │   │   │   │
    │   │   │   └── factory/                 # Status update strategy pattern
    │   │   │       ├── NotificationStatusUpdater.java       # Interface: updateStatus(tracker, status)
    │   │   │       ├── NotificationStatusFactory.java       # Maps subscription → updater
    │   │   │       ├── SmsNotificationUpdater.java
    │   │   │       ├── EmailNotificationUpdater.java
    │   │   │       ├── WhatsappNotificationUpdater.java
    │   │   │       └── HighPriorityNotificationUpdater.java
    │   │   │
    │   │   ├── service_bus/             # Service Bus message consumption
    │   │   │   └── ServiceBusNotificationReceiver.java  # @PostConstruct starts all 4 processors
    │   │   │
    │   │   └── utils/                   # Constants and utility methods
    │   │       ├── Constants.java               # Subscription names, auth header key
    │   │       ├── LogConstants.java            # Centralized log message templates
    │   │       ├── NotificationUtils.java       # Status processing, tracker updates
    │   │       ├── infobip_util/
    │   │       │   ├── InfobipAPIConstants.java # API paths, field names, error codes
    │   │       │   └── InfobipUtils.java        # RetryRequest/Report builder helpers
    │   │       └── salesforce_util/
    │   │           └── SalesforceConstants.java # Salesforce API field names
    │   │
    │   └── resources/
    │       ├── application.properties       # Shared config (env vars, feature flags)
    │       ├── application-local.properties # Local dev overrides
    │       ├── application-dev.properties   # Dev environment
    │       ├── application-uat.properties   # UAT environment
    │       └── application-prod.properties  # Production environment
    │
    └── test/
        ├── java/com/tvsmotor/notificationdispatcher/
        │   ├── controller/          # Controller unit tests
        │   ├── repository/          # Repository wrapper tests
        │   ├── service/             # Service layer tests (mirrors main structure)
        │   ├── service_bus/         # Service Bus receiver tests
        │   └── utils/               # Utility tests
        └── resources/
            ├── application.properties
            └── mockito-extensions/org.mockito.plugins.MockMaker  # Enables mocking final classes
```

## Module Dependencies (Data Flow)

```
Azure Service Bus
       │
       ▼
ServiceBusNotificationReceiver (@PostConstruct starts processors)
       │
       ▼
ServiceBusConfig (onMessage callback → ThreadPoolExecutor)
       │
       ▼
NotificationDispatcherService (orchestrator)
       │
       ├──► NotificationStatusFactory → NotificationStatusUpdater impls
       │
       ├──► NotificationSenderFactory
       │         │
       │         ├──► EmailNotificationSender → InfobipEmailSender → Infobip Email API
       │         │
       │         ├──► SMSNotificationSender
       │         │         ├──► InfobipSMSSender → Infobip SMS API
       │         │         └──► SalesforceSMSSender → Salesforce Journey API
       │         │                    └──► SalesforceAuthGen (cached OAuth)
       │         │
       │         └──► WhatsAppNotificationSender → InfobipWhatsAppSender → Infobip Messages API
       │
       ├──► InfobipAPIErrorRetryService → External Retry Microservice
       │
       └──► NotificationTrackerRepository → MongoDB
```

## Architectural Decisions

1. **Event-driven, not REST-based**: The service is a consumer, not an API. Messages arrive via Service Bus; the only REST endpoints are health check and token management.

2. **Factory pattern for sender selection**: `NotificationSenderFactory` maps `NotificationType` → sender implementation. Each channel sender further delegates to provider-specific implementations.

3. **Strategy pattern for status updates**: `NotificationStatusFactory` maps subscription names to `NotificationStatusUpdater` implementations, avoiding switch statements in the main service.

4. **Provider abstraction**: Each channel has an interface (`SMSSender`, `EmailSender`, `WhatsAppSender`) with provider-specific implementations nested under `infobip/` or `salesforce/` packages.

5. **Thread pool isolation**: Service Bus message processing is offloaded to a fixed-size ThreadPoolExecutor (30 threads), separate from the Service Bus SDK's internal threads.

6. **No inline retry for Infobip**: Errors are delegated to a separate retry microservice rather than blocking the processing thread. This keeps throughput high.

7. **Caffeine caching for auth tokens**: Salesforce tokens are cached with TTL-based expiration rather than manual refresh scheduling.

8. **Feature flags for provider toggling**: Boolean properties (`sendInfobipNotification`, `sendSalesforceNotification`) allow disabling providers without code changes.



## Tech Stack & Dependencies


# Notification Dispatcher Service — Tech Stack & Conventions

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Java | 17 |
| Framework | Spring Boot | 3.5.7 |
| Build | Maven | 3.9.14 (in Docker) |
| Database | MongoDB | via Spring Data MongoDB |
| Messaging | Azure Service Bus | SDK 7.17.17 |
| HTTP Client | Spring WebFlux (WebClient) | 3.5.7 |
| Caching | Caffeine (via Spring Cache) | managed by Spring Boot |
| Retry | Spring Retry + spring-aspects | managed by Spring Boot |
| Observability | Sentry (APM + error tracking) | 6.30.0 |
| Metrics | Micrometer | 1.16.0 |
| Boilerplate | Lombok | managed by Spring Boot |
| Serialization | Jackson (with JavaTimeModule) | 2.21.2 |
| API Docs | Springfox | 3.0.0 |
| Testing | JUnit 5 + Mockito + LogCaptor | managed by Spring Boot |
| Code Coverage | JaCoCo | 0.8.11 (80% line coverage minimum) |
| Container | Amazon Corretto 21 (runtime) | 21.0.10-al2023 |
| CI/CD | Azure DevOps Pipelines | — |
| Code Quality | SonarQube | via PR pipeline |

## Coding Conventions

### Naming
- Package names: lowercase, underscore-separated for multi-word (`service_bus`, `infobip_util`, `salesforce_util`)
- Classes: PascalCase, suffixed by role (`*Sender`, `*Service`, `*Factory`, `*Updater`, `*Controller`, `*Repository`)
- Constants: interfaces with `String` fields (not `final class` with `static final`)
- Enums: UPPER_SNAKE_CASE values
- Test classes: `<ClassName>Test.java` mirroring the source structure

### Lombok Usage
- `@Data`, `@Builder`/`@SuperBuilder`, `@AllArgsConstructor`, `@NoArgsConstructor` on all DTOs and models
- `@RequiredArgsConstructor` on services for constructor injection
- `@Slf4j` on all classes that log
- `@SneakyThrows` used sparingly (in dispatcher service)
- `@EqualsAndHashCode(callSuper = true)` on subclasses

### Dependency Injection
- Constructor injection via `@RequiredArgsConstructor` (preferred)
- `@Qualifier` annotations for disambiguating multiple beans of the same type (WebClient, ServiceBusProcessorClient)
- `@Value` for property injection directly into fields

### Configuration
- Environment-specific properties via Spring profiles (`application-{profile}.properties`)
- All secrets and environment-specific values injected via `${ENV_VAR}` placeholders
- Feature flags as boolean properties (`notification.sendInfobipNotification.value`)

## Design Patterns

### Factory Pattern
- `NotificationSenderFactory`: maps `NotificationType` enum → `NotificationSender` implementation
- `NotificationStatusFactory`: maps subscription string → `NotificationStatusUpdater` implementation (initialized in `@PostConstruct`)

### Strategy Pattern
- `NotificationSender` interface with channel-specific implementations
- `NotificationStatusUpdater` interface with subscription-specific implementations
- Provider-specific sender interfaces (`SMSSender`, `EmailSender`, `WhatsAppSender`)

### Template Method (informal)
- Channel senders follow a consistent pattern: build headers → build message payload → call API → handle errors → update tracker

### Builder Pattern
- Lombok `@Builder`/`@SuperBuilder` on all DTOs
- Manual builder usage in `InfobipUtils` for constructing error reports

## Error Handling

### Infobip API Errors
- `WebClientResponseException` caught explicitly
- 5xx → record error in tracker, delegate to retry service via `InfobipAPIErrorRetryService`
- 4xx → same as 5xx (record + delegate to retry)
- 429 Too Many Requests (Email only) → separate handling, also delegated to retry
- Other errors → record in tracker, no retry delegation
- Error details stored in `InfobipData` on the tracker's `ChannelStatus`

### Salesforce API Errors
- 401 Unauthorized → Spring Retry (max 2 attempts) with token refresh via `@Recover`
- Other errors → caught generically, status set to error message string
- Token generation failures → `RuntimeException` with cause

### Service Bus Errors
- Processing exceptions → `context.abandon()` (message returns to queue)
- SDK errors → logged with namespace, entity path, error source, and reason

### Template Not Found
- `TemplateIdNotFoundException` (unchecked) thrown by repository wrapper
- Propagates up and causes message abandon in Service Bus handler

### General Approach
- No global exception handler (`@ControllerAdvice`) — this is not primarily a REST service
- Errors are logged and recorded on the tracker rather than thrown to callers
- `@SneakyThrows` on the main processing method to avoid checked exception boilerplate

## Testing

### Framework
- JUnit 5 (`@ExtendWith(MockitoExtension.class)`)
- Mockito for mocking (with `mockito-inline` for final classes like `ServiceBusReceivedMessage`)
- `mockito-extensions/org.mockito.plugins.MockMaker` configured for inline mock maker
- LogCaptor for verifying log output

### Patterns
- Unit tests only (no integration tests or testcontainers)
- `@Mock` for dependencies, `@InjectMocks` or manual construction with `@Spy`
- `@Captor` for capturing arguments passed to mocks
- `@ParameterizedTest` with `@EnumSource` for testing multiple subscription types
- Test data built using Lombok builders
- `lenient()` for mocks that may not be invoked in all parameterized cases
- `verify()` for asserting interactions
- `assertEquals` / `assertNotNull` for state assertions

### Coverage
- JaCoCo enforces 80% line coverage at package level
- Excluded from coverage: `config/`, `enums/`, `model/`, `dto/`, `Constants`, `Application` class
- Test structure mirrors main source structure exactly

## Deployment

### Docker
- Multi-stage build: `maven:3.9.14-amazoncorretto-17` (build) → `amazoncorretto:21.0.10-al2023` (runtime)
- Timezone set to `Asia/Kolkata`
- JVM flag: `-XX:MaxRAMPercentage=75`
- Exposes port 8080
- Final artifact: `tvsm_notification_dispatcher.jar`

### CI/CD (Azure DevOps)
- CI: triggered by upstream pipeline completion on `main`, extends shared `build-template.yml`
- CD: multi-stage deployment (dev → uat → prod) with manual approval gates
- Image scanning via AST pipelines
- SonarQube analysis on PR builds
- Helm charts for Kubernetes deployment (chart name matches service name)

### Environments
- `local` — local development
- `dev` — development (auto-deploy after CI)
- `uat` — user acceptance testing (manual approval required)
- `prod` — production (manual approval required)

### Configuration Management
- All environment-specific values via environment variables
- Spring profile activated via `ACTIVE_ENVIRONMENT` env var
- Secrets managed externally (not in source)

## Build Commands

```bash
# Build and run tests
mvn clean install

# Run tests only
mvn test

# Run with specific profile
mvn spring-boot:run -Dspring-boot.run.profiles=local

# Generate coverage report
mvn verify  # JaCoCo report at target/site/jacoco/index.html
```

