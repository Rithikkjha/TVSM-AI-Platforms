# High Level Code Document — TVS Connect Web API

## 1. Application Overview

**TVS Connect Web API** is a backend REST API platform built on ASP.NET Web API 2 (.NET Framework 4.8) that powers the **TVS Connect** mobile application ecosystem. The application provides connected vehicle services for TVS Motor Company's two-wheeler lineup, supporting features like ride tracking, vehicle telemetry, user authentication, notifications, and dealer/service integrations.

The platform is deployed across **multiple geographies** (India/Domestic, Africa, Bangladesh, Egypt, Europe, Latin America, Middle East, Nepal, SEA, Sri Lanka) with country-specific configurations and separate Azure deployments per region.

---

## 2. Major Modules/Components

| Module | Project | Purpose |
|--------|---------|---------|
| API Layer | `TVS.ApiService.Api` | Controllers, routing, authentication filters, middleware |
| Business Logic | `TVS.ApiService.Service` | Service classes implementing business workflows |
| Data Access | `TVS.ApiService.Repository` | Repository pattern for database operations |
| Data Models | `TVS.ApiService.Model` | DTOs, request/response models, settings |
| Entity Framework | `TVS.ApiService.DAL` | EF6 entities, EDMX models, database context |
| Database Project | `TVS.ApiService.Database` | SQL Server schema definitions (SSDT) |
| Common Utilities | `TVS.ApiService.Common` | Constants, enums, logging, encryption, SMS utilities |
| SMS Service | `TVS.SMSService` | Multi-provider SMS delivery (Tata, Airtel, Plivo) |
| Web Client | `TVS.WebClient.Web` | MVC web client for admin/web portal operations |
| Unit Tests | `TVS.ApiService.UnitTest` | Unit test project for API, Service, Repository layers |

---

## 3. Folder Structure Explanation

```
tvs-connect-web-api/
├── TVS.ApiService.Api/              # Web API host project (entry point)
│   ├── Controllers/                 # 75+ API controller groups
│   ├── App_Start/                   # Startup config (Auth, DI, Routes, Swagger)
│   ├── AzureADAuthentication/       # Azure AD auth integration
│   ├── CustomHandler/               # Rate limiting, logging handlers
│   ├── CustomFilterAttributes/      # Action filters (localization, logging)
│   ├── Helpers/                     # Utility helper classes
│   ├── Models/                      # API-layer specific models
│   └── Providers/                   # OAuth provider implementation
├── TVS.ApiService.Service/          # Business logic layer (~85 service modules)
├── TVS.ApiService.Repository/       # Data access layer (~65 repository modules)
├── TVS.ApiService.Model/            # Shared models and DTOs
├── TVS.ApiService.DAL/              # Entity Framework EDMX and entities
├── TVS.ApiService.Common/           # Shared utilities, constants, security
├── TVS.ApiService.Database/         # SQL Server database project (SSDT)
├── TVS.SMSService/                  # SMS provider abstraction layer
├── TVS.WebClient.Web/               # MVC web application
├── TVS.ApiService.UnitTest/         # Unit test project
├── azure-pipelines/                 # CI/CD pipeline definitions (~50 YAML files)
├── Country_Specific_Configuration_Files/  # Per-country config overrides
├── DBScript/                        # Database migration and setup scripts
├── DatabaseChanges/                 # Incremental DB change scripts
├── DatabaseScriptForPipeline/       # DB scripts executed during deployments
├── localpackages/                   # Local DLL dependencies
└── TVS-App.sln                      # Visual Studio solution file
```

---

## 4. Core Business Workflows

### User Registration & Authentication
1. User registers via mobile number, email, or social login (Facebook, Google, Apple)
2. OTP is generated and sent via SMS (domestic) or Email + SMS (international)
3. OTP verification grants an OAuth Bearer token
4. Refresh token mechanism for session management

### Vehicle Onboarding
1. User adds vehicle by frame number/VIN
2. Vehicle validated against master data
3. MAC address activation for BLE-connected vehicles
4. Vehicle-type-specific telemetry configuration applied

### Ride Tracking & Analytics
1. Telemetry data collected from connected vehicles (BLE/IoT)
2. Ride data processed and stored (per vehicle type: NTorq, Apache, iQube, etc.)
3. Cumulative statistics calculated
4. Route images generated via MapMyIndia/HERE Maps

### Connected Vehicle Services
- Real-time vehicle location (Last Parked Location)
- Geofencing alerts
- Crash detection & emergency contact notification
- TPMS (Tire Pressure Monitoring)
- OTA updates
- Voice assistant integration

### Dealer & Service Integration
- DMS (Dealer Management System) integration
- Service booking via TVS dealers
- CSI/NPS feedback collection
- Test ride booking

---

## 5. Key Services/Classes

| Service | Responsibility |
|---------|---------------|
| `UserLoginController` | Authentication, OTP, login/logout flows |
| `RideService` | Ride data processing, ride history |
| `UserVehicleService` | Vehicle management, activation |
| `NotificationService` | Push notifications via Azure Notification Hub |
| `TrakNTellService` | Vehicle tracking device integration |
| `P360Service` | P360 platform integration (weather, sports, news) |
| `WeatherService` | Weather data (OpenWeatherMap) |
| `SMSNotificationService` | Multi-provider SMS delivery |
| `HereMapService` | Map and routing services |
| `CodpService` | Connected Data Platform operations |
| `DmsService` | Dealer Management System integration |
| `TechPerspectService` | EV charging infrastructure |
| `GeofenceService` | Geofencing logic |
| `EmergencyContactService` | Crash alert and emergency notifications |
| `SmartCacheService` | In-memory caching layer |

---

## 6. External Integrations

| Integration | Purpose |
|-------------|---------|
| Azure Notification Hubs | Push notifications (iOS/Android) |
| Azure Blob Storage | File storage (ride images, profile pics, CSV data) |
| Azure Event Hubs | Vehicle telemetry data ingestion |
| Azure Key Vault | Secrets management |
| Azure CosmosDB | Document storage |
| HERE Maps API | Route rendering, geocoding |
| MapMyIndia (Mappls) | Route image generation (India) |
| OpenWeatherMap | Weather & AQI data |
| Tata Communications | Domestic SMS OTP delivery |
| Airtel SMS | Secondary SMS provider |
| Plivo | International SMS delivery |
| TrakNTell | Vehicle GPS tracking |
| TechPerspect | EV charging station data |
| P360 Platform | Connected vehicle telemetry |
| DMS (TVS Dealer System) | Service booking, vehicle data |
| Azure AD | Admin/B2B authentication |
| SendGrid | Email delivery (SMTP) |
| RapidAPI (Bing News) | News content |
| Cricket/Football APIs | Sports data feeds |

---

## 7. Major Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| .NET Framework | 4.8 | Runtime |
| ASP.NET Web API 2 | 5.3.0 | REST framework |
| Entity Framework | 6.1.3 | ORM |
| Microsoft.Owin.Security.OAuth | 3.0.1 | OAuth token auth |
| Unity Container | 5.11.11 | Dependency Injection |
| Newtonsoft.Json | 13.0.1 | JSON serialization |
| WindowsAzure.Storage | 9.3.3 | Blob/Table storage |
| Microsoft.Azure.NotificationHubs | 1.0.9 | Push notifications |
| Microsoft.Azure.DocumentDB.Core | 2.19.0 | CosmosDB client |
| Application Insights | 2.23.0 | Monitoring/telemetry |
| log4net | 2.0.17 | Logging |
| CsvHelper | 12.2.1 | CSV parsing (ride data) |
| ClosedXML | 0.95.4 | Excel generation |
| System.IdentityModel.Tokens.Jwt | 4.0.4 | JWT handling |
| TP.SDKEncryption.dll | Local | Proprietary encryption SDK |

---

## 8. Runtime Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Azure App Service                    │
│                  (IIS / OWIN Pipeline)                 │
├──────────────────────────────────────────────────────┤
│  Request → Rate Limiter → Logging Handler →           │
│  Localization Filter → JWT/OAuth Auth →               │
│  Controller → Service → Repository → DB              │
├──────────────────────────────────────────────────────┤
│  DI Container: Unity (singleton/transient services)   │
│  Caching: In-Memory SmartCacheService                 │
│  Logging: log4net + Application Insights              │
└──────────────────────────────────────────────────────┘
         │              │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │ SQL DB  │   │  Azure  │   │External │
    │ (EF6)   │   │ Storage │   │  APIs   │
    └─────────┘   └─────────┘   └─────────┘
```

- **Hosting**: Azure App Service (Windows, IIS)
- **Auth Pipeline**: OWIN middleware → OAuth Bearer Token + Azure AD (admin)
- **DI**: Unity Container (constructor injection)
- **Data Access**: Entity Framework 6 + Raw ADO.NET (stored procedures)
- **Caching**: SmartCacheService (in-memory, per-request/configurable TTL)

---

## 9. Important Entry Points

| Entry Point | Path | Description |
|-------------|------|-------------|
| Application Start | `Global.asax.cs` | App initialization, TLS config, route registration |
| OWIN Startup | `Startup.cs` → `Startup.Auth.cs` | OAuth server configuration |
| WebAPI Config | `App_Start/WebApiConfig.cs` | Route mapping, CORS, filters, DI |
| DI Registration | `App_Start/UnityConfig.cs` | All service/repository bindings |
| Health Check | `GET /api/Health/CheckHealth` | Application health endpoint |
| Token Endpoint | `POST /token` | OAuth token generation |
| Login | `POST /api/UserLogin/Login` | User authentication |

---

## 10. High-Level Data Flow

```
Mobile App / Web Client
        │
        ▼
┌─────────────────────────┐
│   Azure App Service     │
│   (TVS Connect API)     │
│                         │
│  ┌───────────────────┐  │
│  │  Rate Limiter     │  │
│  │  Auth Filter      │  │
│  │  Localization     │  │
│  └────────┬──────────┘  │
│           ▼              │
│  ┌───────────────────┐  │
│  │   Controllers     │  │  ← Request routing
│  └────────┬──────────┘  │
│           ▼              │
│  ┌───────────────────┐  │
│  │    Services       │  │  ← Business logic
│  └────────┬──────────┘  │
│           ▼              │
│  ┌───────────────────┐  │
│  │  Repositories     │  │  ← Data access
│  └────────┬──────────┘  │
└───────────┼─────────────┘
            │
    ┌───────┼───────────────────────┐
    │       │                       │
    ▼       ▼                       ▼
┌───────┐ ┌────────────────┐ ┌──────────────┐
│SQL DB │ │ Azure Services │ │ Third-Party  │
│(EF6)  │ │ - Blob Storage │ │ - HERE Maps  │
│       │ │ - Event Hubs   │ │ - Weather    │
│       │ │ - Notif. Hub   │ │ - TrakNTell  │
│       │ │ - CosmosDB     │ │ - DMS        │
│       │ │ - Key Vault    │ │ - SMS APIs   │
└───────┘ └────────────────┘ └──────────────┘
```

---

## Document Info

| Field | Value |
|-------|-------|
| Application | TVS Connect Web API |
| Framework | .NET Framework 4.8 / ASP.NET Web API 2 |
| Architecture | N-Tier (API → Service → Repository → DAL) |
| Hosting | Azure App Service (Multi-region) |
| Database | Azure SQL Server |
| Generated | June 2026 |


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
