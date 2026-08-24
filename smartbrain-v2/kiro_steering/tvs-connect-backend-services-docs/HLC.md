# High Level Code Document — TVS Connect Web API

| Attribute       | Value                                    |
|-----------------|------------------------------------------|
| Service Name    | TVS Connect Web API                      |
| Solution File   | TVS-App.sln                              |
| Framework       | .NET Framework 4.8 / ASP.NET Web API 2   |
| Total Projects  | 24                                       |
| Last Updated    | June 2026                                |

---

## Table of Contents

1. [Application Overview](#1-application-overview)
2. [Module Summary](#2-module-summary)
3. [Folder Structure Explanation](#3-folder-structure-explanation)
4. [Runtime Flow](#4-runtime-flow)
5. [Core Business Workflows](#5-core-business-workflows)
6. [Key Services](#6-key-services)
7. [Dependency Overview](#7-dependency-overview)
8. [Integration Summary](#8-integration-summary)
9. [Important Entry Points](#9-important-entry-points)
10. [High-Level Data Flow](#10-high-level-data-flow)

---

## 1. Application Overview

TVS Connect Web API is the backend platform powering the **TVS Connect** mobile application — a connected vehicle experience for TVS Motor two-wheeler owners. It provides real-time telemetry, ride analytics, vehicle diagnostics, push notifications, service booking, OTA updates, and third-party content aggregation for both ICE and EV product lines.

The solution is built on **ASP.NET Web API 2** (OWIN/Katana) running on **Azure App Service** (Windows/IIS). It follows an N-tier architecture with clear separation into Controller → Service → Repository → DAL layers, using **Unity IoC** for dependency injection and **Entity Framework 6** (Database-First) for data access.

### Key Metrics

| Metric | Count |
|--------|-------|
| API Controllers | 79 |
| Service Classes | 173 |
| Repository Classes | 103 |
| Solution Projects | 24 |
| External Integrations | 18+ |
| Azure SQL Databases | 2 (ICE + EV) |

---

## 2. Module Summary

### Core Projects (N-Tier Layers)

| Project | Layer | Responsibility |
|---------|-------|----------------|
| `TVS.ApiService.Api` | Presentation | Controllers, Filters (JWT auth), OWIN startup, Swagger |
| `TVS.ApiService.Service` | Business Logic | Service interfaces/implementations, external API orchestration |
| `TVS.ApiService.Repository` | Data Access | Repository pattern abstraction over EF contexts |
| `TVS.ApiService.DAL` | Data Access (ICE) | Entity Framework EDMX for ICE database (TVSModel, TVSDAModel) |
| `TVS.ApiService.EV.DAL` | Data Access (EV) | Entity Framework EDMX for EV database (EVModel) |
| `TVS.ApiService.Model` | DTOs/Models | Request/Response models, shared DTOs, enums |
| `TVS.ApiService.Common` | Shared Utilities | Helpers, constants, extensions, config wrappers |
| `TVS.ApiService.ProviderService` | External Calls | HTTP resilience (circuit breaker), provider abstractions |

### Background Processing Projects

| Project | Responsibility |
|---------|----------------|
| `TVS.WebJob.PushNotifications` | Push notification delivery via Azure Notification Hub |
| `TVS.Webjob.UnifiedMappingTableICE` | Vehicle mapping data sync from DMS |
| `TVS.Webjob.UnifiedMobileChangeRequestICE` | Mobile number change request processing |
| `TVS.WebJob.NotificationCleanupJob` | Notification purge and archival |
| `ConsoleForSaveNotifications` | Notification persistence from queue |
| `ConsoleForSendNotifications` | Notification dispatch to Azure Notification Hub |
| `ConsoleServiceReminder` | Service reminder scheduling and delivery |
| `ConsoleAppForSendDataToNGD` | Telemetry data forwarding to NGD platform |

### Supporting Projects

| Project | Responsibility |
|---------|----------------|
| `TVS.SMSService` | Multi-provider SMS delivery (Airtel/Tata factory pattern) |
| `TVS.Service.Notification` | Notification service shared library |
| `TVS.NotificationService` | Notification hub integration |
| `TVS.WebClient.Web` | Admin web portal (ASP.NET MVC) |
| `TVS.NewVaraintAutomation` | New vehicle variant onboarding automation |
| `TVS.ApiService.Database` | SQL Server database project (schema/migrations) |
| `TVS.ApiService.UnitTest` | Unit test project |
| `TVS-App` | Legacy/parent project (shared configs) |

---

## 3. Folder Structure Explanation

```
tvs-connect-web-api/
│
├── TVS-App.sln                          # Solution file (24 projects)
├── azure-pipelines.yml                  # CI/CD pipeline definition
├── azure-pipeline-pr-trigger.yml        # PR validation pipeline
│
├── TVS.ApiService.Api/                  # Web API host project
│   ├── App_Start/                       #   Unity DI config, WebAPI config, OWIN startup
│   ├── Controllers/                     #   79 controllers organized by feature folder
│   │   ├── Registration/               #     User registration + OTP
│   │   ├── Vehicle/                     #     Vehicle CRUD + onboarding
│   │   ├── Ride/                        #     Ride data management
│   │   ├── Notification/               #     Push notification endpoints
│   │   ├── Home/                        #     Dashboard / telemetry
│   │   ├── Geofence/                    #     Geofence CRUD
│   │   ├── Cricket/Football/AQI/        #     Third-party content
│   │   ├── CSIFeedback/NPSFeedback/     #     Feedback modules
│   │   └── HealthCheck/                 #     Service health endpoint
│   ├── Filters/                         #   JwtAuthenticationFilter, RateLimit, UserVehicleAuth
│   ├── Web.config                       #   App settings, connection strings, feature flags
│   └── Startup.cs                       #   OWIN pipeline configuration
│
├── TVS.ApiService.Service/              # Business logic layer
│   ├── Home/                            #   HomeService (dashboard data)
│   ├── Ride/                            #   RideService (ride CRUD + analytics)
│   ├── Vehicle/                         #   VehicleService (onboarding, lookup)
│   ├── P360/                            #   P360Service (telematics integration)
│   ├── ExternalApi/                     #   ExternalApiService (generic HTTP)
│   ├── MMIDownload/                     #   MapMyIndia route image service
│   ├── CSIFeedback/NPSFeedback/         #   Feedback services
│   ├── InAppFeedback/                   #   In-app feedback service
│   ├── Referral/                        #   Referral program service
│   ├── Widget/                          #   Widget data service
│   └── P360TntProviderFactory/          #   Factory for P360/TnT providers
│
├── TVS.ApiService.Repository/           # Repository pattern (data access abstraction)
│   ├── Home/                            #   IHomeRepository + impl
│   ├── Ride/                            #   IRideRepository + impl
│   ├── Vehicle/                         #   IVehicleRepository + impl
│   ├── Notification/                    #   INotificationRepository + impl
│   └── ... (103 files across features)
│
├── TVS.ApiService.DAL/                  # ICE Database context
│   ├── TVSModel.edmx                    #   EF6 Database-First model (ICE)
│   └── TVSDAModel.edmx                  #   Secondary EF model (stored procedures)
│
├── TVS.ApiService.EV.DAL/              # EV Database context
│   └── EVModel.edmx                     #   EF6 Database-First model (EV)
│
├── TVS.ApiService.Model/               # Shared DTOs and models
│   ├── Request/                         #   Request DTOs
│   ├── Response/                        #   Response DTOs
│   └── Enums/                           #   Shared enumerations
│
├── TVS.ApiService.Common/              # Cross-cutting utilities
│   ├── Constants/                       #   Application constants
│   ├── Helpers/                         #   Utility classes
│   └── Extensions/                      #   Extension methods
│
├── TVS.ApiService.ProviderService/     # External API resilience layer
│   ├── CircuitBreaker/                  #   Polly-based circuit breaker
│   └── Providers/                       #   HTTP provider abstractions
│
├── TVS.SMSService/                     # SMS delivery
│   ├── AirtelDigimateProvider.cs        #   Airtel SMS provider
│   ├── TataCommunicationProvider.cs     #   Tata SMS provider (failover)
│   └── SMSServiceFactory.cs            #   Factory for provider selection
│
├── TVS.WebJob.PushNotifications/       # Azure WebJob: push delivery
├── TVS.Webjob.UnifiedMappingTableICE/  # Azure WebJob: vehicle sync
├── ConsoleForSaveNotifications/        # Console app: save notifications
├── ConsoleForSendNotifications/        # Console app: send notifications
├── ConsoleServiceReminder/             # Console app: service reminders
├── ConsoleAppForSendDataToNGD/         # Console app: data to NGD
│
├── DBScript/                           # Database migration scripts
├── DatabaseChanges/                    # Incremental DB change scripts
├── DatabaseScriptForPipeline/          # Pipeline-executed DB scripts
├── DeployTarget/                       # Deployment target configurations
├── Docs/                               # Documentation (this folder)
└── azure-pipelines/                    # Pipeline YAML templates
```

---

## 4. Runtime Flow

### Request Processing Pipeline

```
Client Request (HTTPS)
    │
    ▼
IIS (Azure App Service) → OWIN Middleware Pipeline
    │
    ├──▶ Swagger (if /swagger route)
    │
    ▼
ASP.NET Web API 2 Routing
    │
    ├──▶ Rate Limiting Filter (IP-based, for login/OTP endpoints)
    │
    ▼
JwtAuthenticationFilter (Authorization Filter)
    │   1. Extract accesstoken + userid headers
    │   2. Validate JWT signature (HMAC-SHA256)
    │   3. Verify claim matches header
    │   4. DB validation via stored procedure
    │   5. Set Thread.CurrentPrincipal
    │
    ▼
Controller Action Method
    │
    ├──▶ Model Binding + Validation Attributes
    │
    ▼
Service Layer (injected via Unity DI)
    │
    ├──▶ Repository Layer (EF6 DbContext)
    │        └──▶ Azure SQL Database
    │
    ├──▶ Provider Service (external HTTP with circuit breaker)
    │        └──▶ P360, DMS, MapMyIndia, etc.
    │
    └──▶ SMS Service (factory pattern)
             └──▶ Airtel / Tata Communications
```

### Dependency Injection (Unity IoC)

All dependencies are registered in `App_Start/UnityConfig.cs` with 100+ registrations:
- Services registered as `TransientLifetimeManager` (new instance per request)
- Repository layer follows interface → implementation pattern
- EF DbContext injected per-request

---

## 5. Core Business Workflows

### 5.1 User Login (OTP-Based)

```
1. POST /api/v3/userlogin/loginv3 (MobileNumber)
2. System checks ICE + EV databases for user
3. Generates 6-digit OTP → sends via Airtel SMS (failover: Tata)
4. POST /api/v3/userlogin/verifyloginotp (OTP)
5. Validates OTP → generates JWT Access + Refresh tokens
6. Registers device for push notifications (Azure Notification Hub)
7. Returns tokens + user profile data
```

### 5.2 Vehicle Onboarding

```
1. GET /api/v3/vehicle/vehiclelist (fetch from DMS by mobile)
2. User selects vehicle from DMS list
3. POST /api/v3/Vehicle/AddVehicle (frame number, engine number, etc.)
4. System creates UserVehicle mapping in DB
5. If connected vehicle → registers with P360/TrakNTell for telemetry
6. Returns vehicle details + connected status
```

### 5.3 Ride Data Flow

```
1. Mobile app records ride locally (BLE/telemetry)
2. POST /api/ride (multipart: RideDetails JSON + CSV file)
3. Service uploads CSV to Azure Blob Storage
4. Calculates cumulative stats (distance, speed, duration)
5. Requests route image from MapMyIndia API
6. Stores ride metadata in Azure SQL
7. Returns ride summary + download links
```

### 5.4 Push Notification Delivery

```
1. Notification triggered (service reminder, promo, alert)
2. Notification record saved to DB (NotificationType, UserId, Body)
3. Azure WebJob picks up pending notifications
4. Resolves device tokens (FCM/APNS) from user profile
5. Sends via Azure Notification Hub
6. Updates delivery status in DB
```

### 5.5 Connected Vehicle Telemetry

```
1. Vehicle ECU sends data to P360 platform
2. App requests SAS token: GET /api/SasToken/GetSASToken
3. App connects to Azure Event Hub with SAS token
4. Real-time telemetry streamed (speed, location, fuel/SoC, TPMS)
5. Dashboard: GET /api/Home/GetLatestDeviceData
6. Service calls P360 API for latest device snapshot
```

---

## 6. Key Services

### Critical Path Services

| Service Class | File | Responsibility |
|---------------|------|----------------|
| `HomeService` | Home/HomeService.cs | Dashboard data, latest device telemetry, cumulative stats |
| `RideService` | Ride/RideService.cs | Ride CRUD, CSV upload, cumulative calculation, route images |
| `VehicleService` | Vehicle/VehicleService.cs | Vehicle onboarding, DMS lookup, P360 registration |
| `P360Service` | P360/P360Service.cs | P360 telematics API integration (connected data) |
| `ExternalApiService` | ExternalApi/ExternalApiService.cs | Generic HTTP client for third-party APIs |
| `MMIDownloadService` | MMIDownload/MMIDownloadService.cs | MapMyIndia route image generation |
| `SMSServiceFactory` | TVS.SMSService | Multi-provider SMS with failover (Airtel → Tata) |
| `InAppFeedbackService` | InAppFeedback/ | User feedback collection and submission |
| `CSIFeedbackService` | CSIFeedback/ | Customer Satisfaction Index feedback |
| `ReferralService` | Referral/ | Referral program management |

### Key Controllers (High Traffic)

| Controller | Path | Traffic Level |
|------------|------|---------------|
| `UserLoginControllerV3` | `/api/v3/userlogin/*` | Very High |
| `RegisterUserController` | `/api/RegisterUser/*` | Very High |
| `HomeController` | `/api/Home/*` | Very High |
| `VehicleControllerV3` | `/api/v3/vehicle/*` | High |
| `RideController` | `/api/ride/*` | High |
| `NotificationController` | `/api/Notification/*` | High |
| `GeofenceController` | `/api/geofence/*` | Medium |
| `CricketController` | `/api/Cricket/*` | Medium |
| `WeatherController` | `/api/Weather/*` | Medium |

### Auth & Security Filters

| Filter | Purpose |
|--------|---------|
| `JwtAuthenticationFilter` | JWT validation + DB check on every authenticated request |
| `RateLimitFilter` | IP-based rate limiting for login/OTP endpoints |
| `UserVehicleAuthorization` | Validates user owns the vehicle for ride endpoints |
| `RefreshTokenValidationFilter` | Validates refresh token for token renewal |

---

## 7. Dependency Overview

### NuGet Dependencies (Major)

| Package | Version | Purpose |
|---------|---------|---------|
| Microsoft.AspNet.WebApi | 5.x | Web API framework |
| Microsoft.Owin | 4.x | OWIN hosting |
| EntityFramework | 6.x | ORM (Database-First) |
| Unity | 5.x | Dependency injection |
| Newtonsoft.Json | 13.x | JSON serialization |
| log4net | 2.x | Logging framework |
| Mapster | 7.x | Object mapping (DTO ↔ Entity) |
| Polly | 7.x | Resilience / circuit breaker |
| Microsoft.Azure.NotificationHubs | 4.x | Push notifications |
| WindowsAzure.Storage | 9.x | Azure Blob Storage |
| System.IdentityModel.Tokens.Jwt | 6.x | JWT token handling |
| Swashbuckle | 5.x | Swagger UI generation |

### Azure Platform Dependencies

| Service | Usage |
|---------|-------|
| Azure App Service (Windows) | Web API hosting + WebJobs |
| Azure SQL Database | Primary data store (ICE + EV) |
| Azure Blob Storage | Binary assets (rides, images, OTA) |
| Azure Notification Hub | Push notification delivery |
| Azure Event Hub | Vehicle telemetry streaming |
| Azure AD | OAuth 2.0 for service-to-service auth |
| Application Insights | APM and monitoring |
| Azure DevOps | CI/CD pipelines |

---

## 8. Integration Summary

### Outbound Integrations

| System | Protocol | Purpose |
|--------|----------|---------|
| P360 Telematics | REST/JWT | Vehicle telemetry, connected data, SAS tokens |
| DMS Digi API | REST/Basic Auth | Vehicle lookup, service history, job cards |
| Sitecore CMS | REST/API Key | Vehicle content, pre-ownership data |
| MapMyIndia (Mappls) | REST/API Key | Static route map images |
| OpenWeatherMap | REST/API Key | Weather forecast + AQI |
| Bing News API | REST/Subscription Key | News aggregation |
| RapidAPI (Cricket/Football) | REST/API Key | Live sports scores |
| Airtel Digimate | REST/Encoded Key | SMS OTP (primary) |
| Tata Communications | REST/Username+Pwd | SMS OTP (failover) |
| WhatsApp Notification Svc | REST/OAuth 2.0 | WhatsApp messages |
| SendGrid | SMTP/API Key | Email notifications |
| Shopify Booking | REST/OAuth 2.0 | Vehicle booking |
| Azure Notification Hub | SDK/SAS | Push notifications |
| Azure Blob Storage | SDK/Account Key | File storage |
| Azure Event Hub | AMQP/SAS | Telemetry ingestion |

### Inbound Integrations

| Source | Method | Purpose |
|--------|--------|---------|
| TVS Connect Mobile App (iOS/Android) | REST API | Primary consumer |
| Admin Web Portal | REST API | Admin operations |
| Alexa Voice Assistant | REST API | Voice commands |
| HIB Notification Service | REST/Bearer | External notification push |

---

## 9. Important Entry Points

| Entry Point | File | Purpose |
|-------------|------|---------|
| OWIN Startup | `TVS.ApiService.Api/Startup.cs` | App pipeline initialization |
| Unity DI Config | `TVS.ApiService.Api/App_Start/UnityConfig.cs` | All dependency registrations (100+) |
| WebAPI Config | `TVS.ApiService.Api/App_Start/WebApiConfig.cs` | Route registration, formatters |
| JWT Filter | `TVS.ApiService.Api/Filters/JwtAuthenticationFilter.cs` | Request authentication |
| Rate Limiter | `TVS.ApiService.Api/Filters/RateLimitFilter.cs` | Login rate limiting |
| Web.config | `TVS.ApiService.Api/Web.config` | All config: connection strings, API keys, feature flags |
| Global.asax | `TVS.ApiService.Api/Global.asax.cs` | Application lifecycle events |

### Background Entry Points

| Entry Point | Project | Schedule |
|-------------|---------|----------|
| Push WebJob | `TVS.WebJob.PushNotifications/Program.cs` | Continuous |
| Unified Mapping WebJob | `TVS.Webjob.UnifiedMappingTableICE/Program.cs` | Scheduled |
| Notification Save Console | `ConsoleForSaveNotifications/Program.cs` | Scheduled |
| Notification Send Console | `ConsoleForSendNotifications/Program.cs` | Scheduled |
| Service Reminder Console | `ConsoleServiceReminder/Program.cs` | Scheduled (daily) |

---

## 10. High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW OVERVIEW                               │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────┐
                    │  Mobile App │
                    │ (iOS/Android)│
                    └──────┬──────┘
                           │ HTTPS/JSON
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    TVS.ApiService.Api                          │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────────┐ │
│  │JWT Filter│→ │Controller│→ │  Service  │→ │ Repository │ │
│  └──────────┘  └──────────┘  └─────┬─────┘  └──────┬─────┘ │
└──────────────────────────────────────┼───────────────┼───────┘
                                       │               │
              ┌────────────────────────┼───────────────┼────────────────┐
              │                        │               │                │
              ▼                        ▼               ▼                ▼
┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐  ┌────────────┐
│  External APIs   │  │  Azure Services  │  │  Azure SQL  │  │  SMS/Push  │
│  P360, DMS,      │  │  Blob, EventHub  │  │  ICE + EV   │  │  Airtel,   │
│  MapMyIndia,     │  │  Notif Hub       │  │  Databases  │  │  Tata, FCM │
│  Weather, News   │  │                  │  │             │  │            │
└──────────────────┘  └──────────────────┘  └─────────────┘  └────────────┘
                                                    │
                                                    ▼
                                       ┌──────────────────────┐
                                       │  Background Jobs     │
                                       │  WebJobs + Consoles  │
                                       │  (Push, Sync, Remind)│
                                       └──────────────────────┘
```

### Data Categories

| Data Type | Storage | Access Pattern |
|-----------|---------|----------------|
| User profiles, vehicles, rides | Azure SQL (ICE DB) | CRUD via EF6 |
| EV telemetry, EV users | Azure SQL (EV DB) | CRUD via EF6 |
| Ride CSVs, route images, OTA files | Azure Blob Storage | Upload/download via SDK |
| Real-time vehicle data | Azure Event Hub | Stream via SAS tokens |
| Push notification delivery | Azure Notification Hub | Send via SDK |
| Session tokens | Azure SQL (stored procedures) | Validate per-request |
| Config & secrets | Web.config / App Settings | Read at startup |

---

*Generated for vendor onboarding. Avoid exposing secrets, credentials, or sensitive business logic.*


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
