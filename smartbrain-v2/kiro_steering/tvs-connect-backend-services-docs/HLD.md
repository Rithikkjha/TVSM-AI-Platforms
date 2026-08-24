# High Level Design (HLD) — TVS Connect Web API

| Attribute       | Value                                    |
|-----------------|------------------------------------------|
| Service Name    | TVS Connect Web API                      |
| Version         | 1.0.0                                    |
| Owner           | TVS Motor - Connected Vehicle Services   |
| Last Updated    | June 2026                                |
| Status          | Production                               |
| Tier            | Tier 1 (Mission Critical)                |

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Major Components / Services](#2-major-components--services)
3. [Deployment Architecture](#3-deployment-architecture)
4. [Database Interactions](#4-database-interactions)
5. [API Integrations](#5-api-integrations)
6. [Authentication & Authorization Flow](#6-authentication--authorization-flow)
7. [External Systems](#7-external-systems)
8. [Infrastructure Dependencies](#8-infrastructure-dependencies)
9. [High-Level Sequence Flows](#9-high-level-sequence-flows)
10. [Scalability & Resiliency Considerations](#10-scalability--resiliency-considerations)

---

## 1. System Architecture

### Overview

TVS Connect Web API is the backend platform powering the **TVS Connect** mobile application — a connected vehicle experience for TVS Motor two-wheeler owners. The system provides real-time telemetry, ride analytics, vehicle diagnostics, OTA updates, push notifications, service booking, and third-party content aggregation (weather, news, sports) for both ICE (Internal Combustion Engine) and EV (Electric Vehicle) product lines.

### Architecture Diagram Description

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ TVS Connect  │  │ TVS Connect  │  │   Admin      │  │  Alexa /     │       │
│  │ Android App  │  │   iOS App    │  │  Web Portal  │  │  Voice Asst  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼──────────────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │                  │
          └──────────────────┴────────┬─────────┴──────────────────┘
                                      │ HTTPS (TLS 1.2)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       AZURE APP SERVICE (Web API)                                │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    TVS.ApiService.Api (.NET Framework 4.8)                 │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │  │
│  │  │  JWT Auth   │  │  Controller │  │   Service   │  │  Repository    │  │  │
│  │  │  Filter     │  │   Layer     │  │    Layer    │  │    Layer       │  │  │
│  │  │  (60+ APIs) │  │  (60+ Ctlrs)│  │ (70+ Svcs) │  │  (50+ Repos)  │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────────┘  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │  │
│  │  │  Circuit    │  │  SMS Svc    │  │  Provider   │  │  EV DAL        │  │  │
│  │  │  Breaker    │  │  (Factory)  │  │  Service    │  │  (EV-specific) │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────┬─────────────────────────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
┌──────────────────┐    ┌──────────────────────┐    ┌──────────────────────────┐
│   Azure SQL DB   │    │   Azure Services     │    │   External APIs          │
│  (ICE + EV DBs)  │    │  Blob · Notif Hub ·  │    │  P360 · DMS · Sitecore · │
│  Entity Framework│    │  Event Hub · Storage  │    │  MapMyIndia · Weather    │
└──────────────────┘    └──────────────────────┘    └──────────────────────────┘
```

### Background Processing Layer

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        AZURE WEBJOBS / CONSOLE APPS                              │
│  ┌──────────────────────┐  ┌────────────────────────────┐                      │
│  │ TVS.WebJob.Push      │  │ TVS.Webjob.UnifiedMapping  │                      │
│  │ Notifications        │  │ TableICE                   │                      │
│  └──────────────────────┘  └────────────────────────────┘                      │
│  ┌──────────────────────┐  ┌────────────────────────────┐                      │
│  │ ConsoleForSave       │  │ ConsoleForSend             │                      │
│  │ Notifications        │  │ Notifications              │                      │
│  └──────────────────────┘  └────────────────────────────┘                      │
│  ┌──────────────────────┐  ┌────────────────────────────┐                      │
│  │ ConsoleService       │  │ ConsoleAppForSend          │                      │
│  │ Reminder             │  │ DataToNGD                  │                      │
│  └──────────────────────┘  └────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Design Principles

- **N-Tier Architecture**: Clear separation — Controller → Service → Repository → DAL (Entity Framework)
- **Dependency Injection**: Unity IoC container for loose coupling across all layers
- **Dual-Platform Support**: Separate DAL projects for ICE and EV vehicle ecosystems
- **Provider Pattern**: SMS delivery uses factory pattern for provider failover (Airtel ↔ Tata)
- **HTTP Resilience**: Built-in circuit breaker with per-host retry/timeout configuration
- **Stateless API**: JWT-based authentication; no server-side sessions

---

## 2. Major Components / Services

### Service Interaction

| Component                     | Responsibility                                              | Interactions                                    |
|-------------------------------|-------------------------------------------------------------|-------------------------------------------------|
| **User Management**           | Registration, login (OTP), profile CRUD, consent management | SMS providers, Azure SQL, Notification Hub      |
| **Vehicle Management**        | Vehicle onboarding, ownership mapping, VIN lookup           | DMS API, P360 API, Azure SQL                    |
| **Ride & Telemetry**          | Ride recording, cumulative stats, route images, CSV storage | Azure Blob, MapMyIndia, Azure Event Hub         |
| **Notification Engine**       | Push, SMS, WhatsApp notifications; nudges and reminders     | Azure Notification Hub, Airtel/Tata SMS, WhatsApp API |
| **Service Booking**           | Dealer service appointments, job card integration           | DMS Digi API, Shopify Booking Service           |
| **OTA Updates**               | Firmware delivery and version management                    | Azure Blob Storage, Vehicle ECU                 |
| **Feedback & Survey**         | CSI feedback, NPS surveys, in-app feedback, service ratings | DMS Digi API (PSF), SendGrid Email              |
| **Connected Data Provider**   | Real-time vehicle telemetry, TPMS, SoC, geofencing          | Azure Event Hub, P360 Telematics                |
| **Third-Party Content**       | Weather, AQI, news, cricket/football live scores            | OpenWeather, Bing News, RapidAPI                |
| **Preownership**              | Used vehicle data, pre-ownership transfers                  | Sitecore CMS                                   |
| **Emergency & Safety**        | Crash alert SMS, emergency contacts, breakdown assistance   | SMS providers, MapMyIndia                       |
| **EV Module**                 | EV-specific telemetry, charging, MQTT notifications         | EV Database, MQTT broker                        |
| **SMS Service**               | Multi-provider SMS delivery with failover                   | Airtel Digimate, Tata Communications            |
| **Background Jobs**           | Push notifications, data sync, service reminders            | Azure SQL, Notification Hub, DMS                |

### Internal Service Communication Pattern

```
Controller (API endpoint)
    │
    ▼
Service Layer (Business Logic + External API Orchestration)
    │
    ├──▶ Repository Layer (Data access abstraction)
    │         │
    │         ▼
    │    DAL / Entity Framework (TVSModel / EVModel / TVSDAModel)
    │         │
    │         ▼
    │    Azure SQL Database (ICE DB + EV DB)
    │
    ├──▶ Provider Service (External API calls with resilience)
    │
    └──▶ SMS Service (Factory: Airtel / Tata Communications)
```

All internal communication is synchronous request-response within the same process. Background processing is handled by separate Azure WebJobs and Console Applications that share the DAL layer.

---

## 3. Deployment Architecture

### Infra Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Azure Cloud (Central India Region)                 │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   Azure App Service Plan                        │ │
│  │                                                                 │ │
│  │  ┌─────────────────────────┐    ┌───────────────────────────┐ │ │
│  │  │  App Service: DEV       │    │  App Service: UAT          │ │ │
│  │  │  tvs-connect-api-dev    │    │  tvs-connect-api-uat       │ │ │
│  │  └─────────────────────────┘    └───────────────────────────┘ │ │
│  │                                                                 │ │
│  │  ┌─────────────────────────┐    ┌───────────────────────────┐ │ │
│  │  │  App Service: PROD      │    │  WebJobs (attached to      │ │ │
│  │  │  tvs-connect-api-prod   │    │  App Service instances)    │ │ │
│  │  └─────────────────────────┘    └───────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │ Azure SQL DB │  │ Azure Blob   │  │ Azure Notification Hub │   │
│  │ (ICE + EV)   │  │ Storage      │  │ (Push Notifications)   │   │
│  └──────────────┘  └──────────────┘  └────────────────────────┘   │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │ Azure Event  │  │ Azure AD     │  │ Application Insights   │   │
│  │ Hub (Telemetry)│ │ (OAuth)     │  │ (Monitoring)           │   │
│  └──────────────┘  └──────────────┘  └────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Deployment Flow

```
Developer → Azure DevOps (Push to branch)
                │
                ▼
┌──────────────────────────────────┐
│  Azure DevOps CI Pipeline        │
│  1. NuGet Restore (TVS-App.sln)  │
│  2. MSBuild (Release config)     │
│  3. Web Deploy Package Creation  │
│  4. Publish Build Artifacts      │
│  Agent Pool: TVSConnectAgent     │
└──────────────────┬───────────────┘
                   │ (artifact trigger)
                   ▼
┌──────────────────────────────────┐
│  Azure DevOps CD Pipeline        │
│  1. Deploy to DEV (auto)         │
│  2. Manual Approval → UAT        │
│  3. Manual Approval → PROD       │
│  (Web Deploy to App Service)     │
└──────────────────────────────────┘
```

### Runtime Specification

| Attribute          | Value                                         |
|--------------------|-----------------------------------------------|
| Framework          | .NET Framework 4.8                            |
| Web Server         | IIS (Azure App Service managed)               |
| API Framework      | ASP.NET Web API 2 (OWIN/Katana)               |
| DI Container       | Unity (Microsoft.Practices.Unity)             |
| ORM                | Entity Framework 6                            |
| Build Tool         | MSBuild / NuGet                               |
| CI/CD              | Azure DevOps Pipelines                        |
| Logging            | log4net + Application Insights                |
| Object Mapping     | Mapster                                       |

### Environments

| Environment | URL Pattern                           | Approval     | Deployment          |
|-------------|---------------------------------------|--------------|---------------------|
| DEV         | dev-tvsconnectapi.tvsmotor.net        | Automatic    | On CI completion    |
| UAT         | uat-tvsconnectapi.tvsmotor.net        | Manual       | Post-DEV validation |
| PROD        | tvsconnectapi.tvsmotor.net            | Manual       | Post-UAT sign-off   |

---

## 4. Database Interactions

### Database Technology

- **Engine**: Azure SQL Database (SQL Server)
- **ORM**: Entity Framework 6 (Database-First, EDMX models)
- **Connection Pool**: ADO.NET default pooling (managed by Azure SQL)
- **Provider**: System.Data.SqlClient

### Database Topology

| Database               | Purpose                          | Entity Model  |
|------------------------|----------------------------------|---------------|
| ICE Database           | Connected ICE vehicles, users, rides, notifications | TVSModel + TVSDAModel |
| EV Database            | Electric vehicle telemetry, EV users, MQTT data    | EVModel       |

### Core Entity Model

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   UserProfile    │       │   UserVehicle     │       │   VehicleType    │
│──────────────────│       │──────────────────│       │──────────────────│
│ UserId           │──────▶│ UserId           │──────▶│ VehicleTypeId    │
│ MobileNo         │       │ VehicleId        │       │ VehicleName      │
│ Email            │       │ FrameNumber      │       │ Series           │
│ FirstName        │       │ VehicleTypeId    │       │ PartId           │
│ DeviceToken      │       │ MacAddress       │       │ IsConnected      │
└──────────────────┘       │ RegistrationNo   │       └──────────────────┘
                           └──────────────────┘
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│      Ride        │       │  RideCumulative  │       │  PushNotification│
│──────────────────│       │──────────────────│       │──────────────────│
│ RideId           │       │ UserId           │       │ NotificationId   │
│ UserId           │       │ VehicleId        │       │ UserId           │
│ VehicleId        │       │ TotalDistance    │       │ Title            │
│ StartTime        │       │ TotalDuration    │       │ Body             │
│ EndTime          │       │ AvgSpeed         │       │ IsRead           │
│ Distance         │       │ TopSpeed         │       │ NotificationType │
│ AvgSpeed         │       │ FuelSaved        │       │ CreatedDate      │
└──────────────────┘       └──────────────────┘       └──────────────────┘

┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  UserDevice      │       │   UserConsent    │       │  UserFeedback    │
│──────────────────│       │──────────────────│       │──────────────────│
│ DeviceId         │       │ ConsentId        │       │ FeedbackId       │
│ UserId           │       │ UserId           │       │ UserId           │
│ Platform (iOS/And│       │ ConsentType      │       │ FeedbackType     │
│ AppVersion       │       │ IsAccepted       │       │ Rating           │
│ DeviceModel      │       │ ConsentDate      │       │ Comments         │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

### Key Database Operations

| Operation                  | Tables / Stored Procedures Involved         | Frequency       |
|----------------------------|---------------------------------------------|-----------------|
| User Login (OTP)           | UserProfile, UserDevice, Token validation SP | Very High       |
| Token Validation           | SP: ValidateToken / ValidateAccessToken     | Every request   |
| Ride Data Persistence      | Ride, RideCumulative                        | High            |
| Vehicle Onboarding         | UserVehicle, VehicleType, UnifiedMapping    | Medium          |
| Push Notification Queue    | PushNotification, NotificationTypesMapping  | High            |
| OTA Version Check          | Vehicle firmware tables                     | Medium          |
| Feedback Submission        | UserFeedback, CSIFeedback, NPSFeedback      | Low-Medium      |
| Service Booking            | Service tables via DMS API                  | Medium          |

---

## 5. API Integrations

### External Integrations

| Integration                  | Protocol    | Auth Method                     | Purpose                                      |
|------------------------------|-------------|---------------------------------|----------------------------------------------|
| **P360 Telematics**          | HTTPS/REST  | JWT Bearer Token                | Vehicle telemetry, connected data, SAS tokens |
| **DMS Digi API**             | HTTPS/REST  | Basic Auth (Base64 token)       | Vehicle lookup, job cards, service history, PSF feedback |
| **Sitecore CMS**             | HTTPS/REST  | API Key (Header)                | Pre-ownership data, vehicle content           |
| **Azure Notification Hub**   | Azure SDK   | Connection String (SAS)         | Push notification delivery (iOS/Android)      |
| **Azure Blob Storage**       | Azure SDK   | Storage Account Key             | Ride CSVs, route images, profile photos, OTA  |
| **Azure Event Hub**          | AMQP (SAS)  | SAS Token (per vehicle type)    | Vehicle telemetry ingestion                   |
| **MapMyIndia (Mappls)**      | HTTPS/REST  | API Key (URL param)             | Static route images, map rendering            |
| **OpenWeatherMap**           | HTTPS/REST  | API Key (URL param)             | Weather forecast + Air Quality Index          |
| **Bing News API**            | HTTPS/REST  | Subscription Key (Header)       | News and sports news aggregation              |
| **RapidAPI (Cricket)**       | HTTPS/REST  | API Key (Header)                | Live cricket scores and fixtures              |
| **RapidAPI (Football)**      | HTTPS/REST  | API Key (Header)                | Live football scores                          |
| **Airtel Digimate**          | HTTPS/REST  | Username + Encoded Key          | SMS OTP delivery (primary provider)           |
| **Tata Communications**      | HTTPS/REST  | Username + Password             | SMS OTP delivery (secondary/failover)         |
| **WhatsApp (via Notification Svc)** | HTTPS/REST | OAuth 2.0 (Azure AD B2C) | WhatsApp OTP and transactional messages       |
| **SendGrid (SMTP)**          | SMTP        | API Key                         | Email notifications (feedback, support)       |
| **Shopify Booking Service**  | HTTPS/REST  | OAuth 2.0 (Client Credentials) | Vehicle booking and appointment management    |
| **TVS Service API**          | HTTPS/REST  | Bearer Token                    | Service booking, service reminders            |
| **RSA Policy API**           | HTTPS/REST  | Direct URL                      | Road-side assistance policy data              |

### Internal API Surface (Key Controller Groups)

| Base Path                    | Module                   | Auth Required |
|------------------------------|--------------------------|---------------|
| `/api/RegisterUser/*`        | User Registration + OTP  | No (public)   |
| `/api/v3/userlogin/*`        | Login (OTP + Token)      | No (public)   |
| `/api/UserProfile/*`         | Profile Management       | Yes (JWT)     |
| `/api/Vehicle/*`             | Vehicle CRUD             | Yes (JWT)     |
| `/api/Ride/*`                | Ride Data + History      | Yes (JWT)     |
| `/api/Notification/*`        | Push Notifications       | Yes (JWT)     |
| `/api/OTA/*`                 | OTA Updates              | Yes (JWT)     |
| `/api/Geofence/*`            | Geofence Management      | Yes (JWT)     |
| `/api/Weather/*`             | Weather + AQI            | Yes (JWT)     |
| `/api/Cricket/*`             | Live Cricket Scores      | Yes (JWT)     |
| `/api/Service/*`             | Service Booking          | Yes (JWT)     |
| `/api/Feedback/*`            | User Feedback            | Yes (JWT)     |
| `/api/SasToken/*`            | Event Hub SAS Tokens     | Yes (JWT)     |
| `/api/Health/CheckHealth`    | Health Check             | No (public)   |

---

## 6. Authentication & Authorization Flow

### Authentication Architecture

```
┌──────────┐         ┌──────────────────────┐         ┌──────────────────┐
│  Mobile  │──(1)──▶ │ JwtAuthenticationFilter │──(2)──▶│   Controller     │
│   App    │         │ (AuthorizationFilter)  │         │   Action         │
└──────────┘         └──────────────────────┘         └──────────────────┘
                              │
                       (Validate JWT Token)
                       (Check token in DB via SP)
                       (Validate UserId match)
                       (Set Thread Principal)
```

### Token Lifecycle

| Token Type      | Lifetime              | Purpose                                    |
|-----------------|-----------------------|--------------------------------------------|
| Access Token    | Configurable (minutes)| Short-lived API access                     |
| Refresh Token   | Configurable (minutes)| Token renewal without re-login             |
| Legacy Token    | 1 year                | Backward-compatible long-lived token       |

### Authentication Flow (V2 — Access Token Based)

```
Mobile App                   TVS Connect API                    Azure SQL
    │                              │                              │
    │──(1) POST /GenerateOTP──────▶│                              │
    │      (mobile number)         │──(2) Generate OTP───────────▶│
    │                              │──(3) Send SMS (Airtel/Tata)──▶ SMS Provider
    │◀──(4) OTP Sent──────────────│                              │
    │                              │                              │
    │──(5) POST /VerifyLoginOTP───▶│                              │
    │      (mobile + OTP)          │──(6) Validate OTP───────────▶│
    │                              │◀──(7) OTP Valid──────────────│
    │                              │                              │
    │                              │──(8) Generate JWT tokens:    │
    │                              │      - Access Token (HMAC)   │
    │                              │      - Refresh Token (HMAC)  │
    │                              │──(9) Store tokens────────────▶│
    │                              │                              │
    │◀──(10) 200 OK───────────────│                              │
    │   {accessToken, refreshToken,│                              │
    │    userId, profile}          │                              │
```

### Token Validation (Per-Request)

1. **Header Extraction**: Extract `accesstoken` and `userid` from request headers
2. **Lifetime Validation**: JWT signature + expiry check using HMAC-SHA256 symmetric key
3. **UserId Claim Match**: Ensure token's `NameIdentifier` claim matches header `userid`
4. **Database Validation**: Stored procedure `ValidateAccessToken` confirms token is active in DB
5. **Body/QueryString Check**: Verify `UserId` in request body/querystring matches header
6. **Principal Assignment**: Set `Thread.CurrentPrincipal` for downstream authorization

### Rate Limiting & Security

- OTP rate limiting: Max 5 failed attempts, then 1-hour lockout
- Login IP blocking: 2-hour block after excessive attempts
- Rate-limited endpoints: `/api/v3/userlogin/loginv3`, `/api/RegisterUser/GenerateOTP`, `/api/v3/userlogin/verifyloginotp`
- Fixed OTP length: 6 digits

---

## 7. External Systems

| System                          | Direction     | Data Flow                                          | SLA Dependency                         |
|---------------------------------|---------------|----------------------------------------------------|----------------------------------------|
| **P360 Telematics Platform**    | Bidirectional | Vehicle data sync, telemetry tokens, TNT provider  | Critical (connected features blocked)  |
| **DMS (Dealer Management)**     | Outbound      | Vehicle lookup, service bookings, job cards, PSF   | High (onboarding + service blocked)    |
| **Azure Event Hub**             | Outbound      | Real-time vehicle telemetry streaming (per model)  | Critical (telemetry blocked)           |
| **Azure Notification Hub**      | Outbound      | Push notification delivery to iOS/Android          | High (notifications delayed)           |
| **Azure Blob Storage**          | Bidirectional | Ride CSVs, route images, profile photos, OTA files | High (degraded UX if down)             |
| **Sitecore CMS**                | Inbound       | Vehicle content, pre-ownership product data        | Medium (content stale)                 |
| **Airtel / Tata (SMS)**         | Outbound      | OTP delivery, crash alerts, reminders              | Critical (login blocked if both fail)  |
| **WhatsApp Notification Svc**   | Outbound      | WhatsApp OTP and transactional messages            | Medium (fallback to SMS)               |
| **MapMyIndia (Mappls)**         | Outbound      | Static route map images for ride history           | Low (cosmetic feature)                 |
| **OpenWeatherMap**              | Inbound       | Weather forecasts and air quality data             | Low (content feature)                  |
| **Bing News / RapidAPI**        | Inbound       | News, cricket, football live data                  | Low (content features)                 |
| **Shopify Booking Service**     | Outbound      | Vehicle booking management                         | Medium (booking flow blocked)          |
| **SendGrid**                    | Outbound      | Email notifications (feedback, support)            | Low (async, non-critical)              |
| **Azure DevOps**                | CI/CD         | Build artifacts, deployment triggers               | Deployment only                        |

### Downstream Consumers (via Azure Event Hub)

| Event Source       | Event Hub Namespace                            | Consumers              |
|--------------------|------------------------------------------------|------------------------|
| Vehicle Telemetry  | prod-tvsm-telemetry-eventhub-namespace         | Analytics, Dashboard   |
| Per-Vehicle-Model  | Separate SAS policies per vehicle series       | Model-specific pipes   |

---

## 8. Infrastructure Dependencies

| Resource                              | Service          | Purpose                                          |
|---------------------------------------|------------------|--------------------------------------------------|
| Azure App Service (Windows)           | Compute          | Hosts Web API + attached WebJobs                 |
| Azure SQL Database (ICE)              | Storage          | Primary data store for ICE vehicles/users        |
| Azure SQL Database (EV)               | Storage          | Data store for EV vehicles/telemetry             |
| Azure Blob Storage                    | Storage          | Binary assets (images, CSVs, OTA files)          |
| Azure Notification Hub                | Messaging        | Cross-platform push notification delivery        |
| Azure Event Hub                       | Streaming        | Vehicle telemetry ingestion (high throughput)    |
| Azure AD (OAuth 2.0)                  | Identity         | Service-to-service auth (WhatsApp, Shopify)      |
| Application Insights                  | Observability    | APM, request tracing, error logging              |
| log4net                               | Logging          | Application-level structured logging             |
| Azure DevOps                          | CI/CD            | Build pipelines, artifact management             |
| Self-hosted Build Agent               | CI/CD            | TVSConnectAgent pool for builds                  |

### Configuration Management

| Category          | Examples                                      | Storage               |
|-------------------|-----------------------------------------------|-----------------------|
| Connection Strings| Azure SQL (ICE, EV), Entity Framework         | Web.config (per env)  |
| API Keys          | MapMyIndia, RapidAPI, OpenWeather, SendGrid   | Web.config / App Settings |
| Azure Credentials | Blob Storage keys, Event Hub SAS, Notif Hub  | Web.config / App Settings |
| SMS Config        | Airtel/Tata endpoints, DLT template IDs       | Web.config            |
| Feature Flags     | OTP send toggle, third-party API enable       | Web.config AppSettings|
| Token Config      | Access/Refresh token lifetimes                | Web.config AppSettings|

---

## 9. High-Level Sequence Flows

### 9.1 User Registration & Login Flow

```
Mobile App            TVS Connect API           SMS Provider        Azure SQL
    │                       │                       │                  │
    │──POST /GenerateOTP───▶│                       │                  │
    │                       │──Generate 6-digit OTP─────────────────▶│
    │                       │──Send OTP SMS────────▶│                  │
    │                       │  (Airtel primary,     │                  │
    │                       │   Tata failover)      │                  │
    │◀──200 OTP Sent───────│                       │                  │
    │                       │                       │                  │
    │──POST /VerifyOTP─────▶│                       │                  │
    │                       │──Validate OTP─────────────────────────▶│
    │                       │◀──Valid──────────────────────────────── │
    │                       │──Generate JWT (HMAC-SHA256)             │
    │                       │──Store Access+Refresh Token────────────▶│
    │                       │──Register Device Info──────────────────▶│
    │◀──200 {tokens, user}─│                       │                  │
```

### 9.2 Vehicle Onboarding Flow

```
Mobile App            TVS Connect API           DMS API             Azure SQL
    │                       │                       │                  │
    │──POST /AddVehicle────▶│                       │                  │
    │  (frameNo, regNo)     │                       │                  │
    │                       │──GET Vehicle by Frame▶│                  │
    │                       │◀──Vehicle Details─────│                  │
    │                       │                       │                  │
    │                       │──Lookup VehicleType───────────────────▶│
    │                       │──Map PartId → Series──────────────────▶│
    │                       │──Create UserVehicle───────────────────▶│
    │                       │──Activate MAC (MapMyIndia)──▶ MMI API   │
    │                       │                       │                  │
    │◀──200 {vehicle}──────│                       │                  │
```

### 9.3 Ride Recording & Route Image Flow

```
Mobile App            TVS Connect API          Azure Blob        MapMyIndia
    │                       │                       │                │
    │──POST /SaveRide──────▶│                       │                │
    │  (CSV telemetry data) │                       │                │
    │                       │──Upload CSV──────────▶│                │
    │                       │──Update cumulative────────────────────▶ Azure SQL
    │                       │                       │                │
    │                       │──Request route image──────────────────▶│
    │                       │◀──Static map image────────────────────│
    │                       │──Upload route image──▶│                │
    │                       │                       │                │
    │◀──200 {rideId}───────│                       │                │
```

### 9.4 Push Notification Flow

```
WebJob/Console         Azure SQL              Azure Notification Hub    Mobile App
    │                       │                       │                       │
    │──Poll pending notifs─▶│                       │                       │
    │◀──Notification list───│                       │                       │
    │                       │                       │                       │
    │──Send push (per user)─────────────────────────▶                       │
    │                       │                       │──Deliver to device────▶│
    │──Mark as sent────────▶│                       │                       │
```

### 9.5 Service Booking Flow

```
Mobile App            TVS Connect API           DMS Digi API        Azure SQL
    │                       │                       │                  │
    │──POST /BookService───▶│                       │                  │
    │  (vehicleId, date,    │                       │                  │
    │   dealer, serviceType)│                       │                  │
    │                       │──POST ServiceBooking─▶│                  │
    │                       │◀──Booking Confirmed───│                  │
    │                       │──Save booking ref─────────────────────▶│
    │◀──200 {bookingId}────│                       │                  │
```

---

## 10. Scalability & Resiliency Considerations

### Current Design

| Aspect                  | Implementation                                                     |
|-------------------------|--------------------------------------------------------------------|
| **Vertical Scaling**    | Azure App Service plan scaling (scale-up)                          |
| **HTTP Resilience**     | Custom circuit breaker with per-host configuration                 |
| **Retry Logic**         | Configurable retry count and wait-before-retry per external host   |
| **Timeout Management**  | Per-host timeout configuration (default 15s, P360 5s)              |
| **Circuit Breaker**     | Break after N failures, hold for configurable duration             |
| **Provider Failover**   | SMS: automatic switch from primary to secondary after N failures   |
| **Caching**             | In-memory caching for third-party API responses (weather, sports)  |
| **Async Processing**    | WebJobs and Console Apps for background notification processing    |
| **Error Alerting**      | Teams webhook notifications on circuit breaker open                |
| **Email Alerting**      | Email to engineering team on circuit break events                  |

### Resilience Configuration (Circuit Breaker)

| Parameter                | Default | P360 Specific |
|--------------------------|---------|---------------|
| Retry Count              | 2       | 3             |
| Timeout (seconds)        | 15      | 5             |
| Failures Before Break    | 5       | 5             |
| Break Duration (seconds) | 30      | 30            |
| Wait Before Retry (sec)  | 1       | 2             |

### SMS Provider Failover

| Parameter                        | Value                          |
|----------------------------------|--------------------------------|
| Primary Provider                 | Tata Communications            |
| Secondary Provider               | Airtel Digimate                |
| Failed Attempts Before Switch    | 10                             |
| Primary Provider Test Frequency  | Every 10 requests (health check) |

### Resiliency Patterns Applied

| Pattern              | Where Applied                                                |
|----------------------|--------------------------------------------------------------|
| **Circuit Breaker**  | All external HTTP calls (configurable per host)              |
| **Retry with Delay** | External API calls (configurable count + wait)               |
| **Provider Failover**| SMS delivery (Airtel ↔ Tata automatic switch)                |
| **Timeout**          | Per-host HTTP timeout configuration                          |
| **Health Check**     | `/api/Health/CheckHealth` endpoint                           |
| **Alerting**         | Teams webhook + email on circuit break events                |
| **Graceful Degradation** | Third-party content (weather, sports) fails silently     |
| **TLS Enforcement**  | TLS 1.2 enforced at application startup                      |
| **Request Size Limits** | Max request length configured for large payloads          |

### Recommendations for Scale

| Area              | Recommendation                                                   |
|-------------------|------------------------------------------------------------------|
| Horizontal Scale  | Enable Azure App Service auto-scale rules based on CPU/requests  |
| Caching           | Introduce Redis for token validation and frequently-read data    |
| Database          | Read replicas for high-read endpoints (ride history, profile)    |
| Async Processing  | Migrate WebJobs to Azure Functions for elastic scale             |
| API Gateway       | Introduce Azure APIM for centralized rate limiting + analytics   |
| Observability     | Distributed tracing with Application Insights correlation        |
| Secret Management | Migrate from Web.config to Azure Key Vault                       |
| Container Deploy  | Containerize for AKS deployment (align with Auth-Ninja pattern)  |

---

## Appendix: Technology Stack Summary

| Layer              | Technology                                              |
|--------------------|---------------------------------------------------------|
| Language           | C# (.NET Framework 4.8)                                 |
| Web Framework      | ASP.NET Web API 2 (OWIN/Katana)                         |
| Security           | Custom JWT (HMAC-SHA256) + DB-backed token validation   |
| ORM                | Entity Framework 6 (Database-First / EDMX)              |
| Database           | Azure SQL Database (SQL Server)                         |
| DI Container       | Unity (Microsoft.Practices.Unity)                       |
| HTTP Resilience    | Custom Circuit Breaker (Polly-like, config-driven)      |
| Object Mapping     | Mapster                                                 |
| Logging            | log4net + Application Insights                          |
| Push Notifications | Azure Notification Hubs                                 |
| Blob Storage       | Azure Blob Storage (REST + SDK)                         |
| Telemetry Stream   | Azure Event Hubs (SAS token auth)                       |
| SMS                | Airtel Digimate + Tata Communications (DLT compliant)   |
| Email              | SendGrid (SMTP)                                         |
| Maps               | MapMyIndia / Mappls                                     |
| Build              | MSBuild + NuGet                                         |
| CI/CD              | Azure DevOps Pipelines (self-hosted agent)              |
| Hosting            | Azure App Service (Windows, IIS managed)                |
| Background Jobs    | Azure WebJobs + .NET Console Applications               |
| Testing            | MSTest (TVS.ApiService.UnitTest)                        |
| API Documentation  | Swagger (Swashbuckle)                                   |
| Monitoring         | Application Insights + Teams Webhooks                   |

---

## Glossary

| Term     | Definition                                                        |
|----------|-------------------------------------------------------------------|
| ICE      | Internal Combustion Engine (petrol/diesel vehicles)               |
| EV       | Electric Vehicle                                                  |
| OTA      | Over-The-Air (firmware updates)                                   |
| TPMS     | Tire Pressure Monitoring System                                   |
| DMS      | Dealer Management System                                          |
| P360     | Platform 360 — TVS connected vehicle telematics platform          |
| SAS      | Shared Access Signature (Azure token-based access)                |
| DLT      | Distributed Ledger Technology (telecom regulatory compliance)     |
| CSI      | Customer Satisfaction Index                                       |
| NPS      | Net Promoter Score                                                |
| PSF      | Post-Sales Feedback                                               |
| CODP     | Connected On-Demand Platform                                      |
| MMI      | MapMyIndia (now Mappls)                                           |
| HIB      | Hibernation (vehicle low-battery notification)                    |

---

*Document Type: Architecture Document for External Engineering Partners*
*Confidentiality: Internal-shareable. No credentials, secrets, or proprietary business logic included.*
*Template: D&AI Engineering — High Level Design Template (space DE2, page 4209508450)*


---

## Document Ownership

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner (iOS)** | Sumit Prajapat | sumit.prajapat@tvsmotor.com |
| **Owner (Android)** | Lakshmi Narayana | lakshmi.narayana@tvsmotor.com |
| **DevOps** | Raju Nimse | raju.nimse@tvsmotor.com |
| **Contact Person (Backend)** | Raju Nimse | raju.nimse@tvsmotor.com |
