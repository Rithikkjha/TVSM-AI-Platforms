# High Level Design (HLD) — TVS Connect Web API

## 1. Document Overview

| Field | Details |
|-------|---------|
| Project | TVS Connect Web API |
| Version | 1.0 |
| Last Updated | June 2026 |
| Audience | External engineering partners, architecture review |

---

## 2. System Architecture

### 2.1 Architecture Diagram Description

The TVS Connect Web API follows a **multi-tier, multi-region** architecture hosted on Microsoft Azure. The system serves as the backend for the TVS Connect mobile application (iOS/Android) and web portal, providing connected vehicle services across 10+ geographic regions.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐   │
│  │  iOS App │  │Android   │  │ Web      │  │ IB Website    │   │
│  │          │  │  App     │  │ Portal   │  │ (TestRide/    │   │
│  │          │  │          │  │ (MVC)    │  │  Enquiry)     │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬────────┘   │
└───────┼──────────────┼──────────────┼───────────────┼────────────┘
        │              │              │               │
        ▼              ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                            │
│                   (Azure App Service / IIS)                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  OWIN Pipeline                                             │  │
│  │  ┌──────────┐ ┌─────────┐ ┌────────────┐ ┌─────────────┐ │  │
│  │  │Rate Limit│→│ CORS    │→│ OAuth Auth │→│ Localization│ │  │
│  │  └──────────┘ └─────────┘ └────────────┘ └─────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  75+ REST API Controllers (Attribute Routing)              │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  85+ Service Classes (Stateless, DI-managed)                │ │
│  │  - Vehicle Telemetry Processing                              │ │
│  │  - Ride Analytics & Calculations                             │ │
│  │  - User Management & GDPR Compliance                         │ │
│  │  - Notification Orchestration                                │ │
│  │  - Third-Party API Integration                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA ACCESS LAYER                             │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Repository Pattern   │  │ Direct ADO.NET (Stored Procs)    │ │
│  │ (65+ Repositories)   │  │ (UserProfileDa, LogExceptionDa) │ │
│  └──────────┬───────────┘  └──────────────┬───────────────────┘ │
│             │                              │                      │
│  ┌──────────▼──────────────────────────────▼───────────────────┐ │
│  │  Entity Framework 6 (EDMX - Database First)                 │ │
│  │  TVSModel.edmx / TVSDAModel.edmx                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                   │
│  ┌─────────────┐  ┌───────────────┐  ┌──────────────────────┐   │
│  │ Azure SQL   │  │ Azure Cosmos  │  │ Azure Blob Storage   │   │
│  │ Database    │  │ DB            │  │ (Ride data, images)  │   │
│  └─────────────┘  └───────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Architecture Style

- **Pattern**: N-Tier (Presentation → Business → Data Access → Persistence)
- **API Style**: RESTful with attribute-based routing
- **DI Framework**: Unity Container (IoC)
- **ORM**: Entity Framework 6 (Database-First, EDMX)
- **Auth**: OAuth 2.0 Bearer Token (OWIN) + Azure AD (admin operations)

---

## 3. Major Components/Services

### 3.1 TVS.ApiService.Api (API Host)
- ASP.NET Web API 2 controllers
- OWIN authentication middleware
- Rate limiting handler
- Global exception handling
- Request/response logging
- Swagger documentation

### 3.2 TVS.ApiService.Service (Business Logic)
- Vehicle-type specific ride calculations
- Connected Data Platform (CODP) integration
- Third-party API orchestration
- Notification management
- Caching strategies
- GDPR data encryption/decryption

### 3.3 TVS.ApiService.Repository (Data Access)
- Repository pattern implementation
- Entity Framework queries
- Stored procedure execution
- Data transformation

### 3.4 TVS.SMSService (SMS Abstraction)
- Multi-provider SMS factory pattern
- Provider failover logic
- Supports: Tata Communications, Airtel, Plivo

### 3.5 TVS.WebClient.Web (Web Portal)
- ASP.NET MVC 5 web application
- Admin operations
- User delete/consent management

---

## 4. Deployment Architecture

### 4.1 Multi-Region Deployment

The application is deployed independently across multiple Azure regions:

| Region | Deployment | Database |
|--------|-----------|----------|
| India (Domestic) | Dedicated App Service | Dedicated SQL DB |
| Europe | Dedicated App Service | Dedicated SQL DB |
| Africa | Dedicated App Service | Dedicated SQL DB |
| Latin America | Dedicated App Service | Dedicated SQL DB |
| Middle East | Dedicated App Service | Dedicated SQL DB |
| SEA (Indonesia) | Dedicated App Service | Dedicated SQL DB |
| Bangladesh | Dedicated App Service | Dedicated SQL DB |
| Nepal | Dedicated App Service | Dedicated SQL DB |
| Sri Lanka | Dedicated App Service | Dedicated SQL DB |
| Egypt | Dedicated App Service | Dedicated SQL DB |

### 4.2 Deployment Pipeline

```
Developer → Feature Branch → PR Trigger Pipeline
                                    │
                                    ▼
                           ┌─────────────────┐
                           │  Build Pipeline  │
                           │  (Azure DevOps)  │
                           └────────┬────────┘
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
              ┌───────────┐  ┌───────────┐  ┌───────────┐
              │   DEV     │  │   UAT     │  │   PROD    │
              │ (Auto)    │  │ (Manual)  │  │ (Manual)  │
              └───────────┘  └───────────┘  └───────────┘
```

- **CI/CD**: Azure DevOps Pipelines (50+ YAML definitions)
- **Build**: MSBuild with solution configurations (Debug/Dev/Staging/Prod)
- **Deployment**: Azure App Service deployment slots
- **DB Migrations**: SQL scripts executed via pipeline stages
- **Config Management**: Country-specific configuration files + Web.config transforms

### 4.3 Infrastructure Topology

```
┌─────────────────── Azure Subscription ───────────────────────┐
│                                                               │
│  ┌─── Per Region ────────────────────────────────────────┐   │
│  │                                                        │   │
│  │  ┌──────────────┐    ┌──────────────────────────────┐ │   │
│  │  │ App Service  │    │ Azure SQL Database           │ │   │
│  │  │ (API + Web)  │───▶│ (Entity Framework models)   │ │   │
│  │  └──────────────┘    └──────────────────────────────┘ │   │
│  │         │                                              │   │
│  │         ▼                                              │   │
│  │  ┌──────────────┐                                     │   │
│  │  │ Blob Storage │  (ride CSVs, images, maps)          │   │
│  │  └──────────────┘                                     │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─── Shared Services ───────────────────────────────────┐   │
│  │  ┌────────────────┐  ┌──────────────────┐             │   │
│  │  │ Event Hubs     │  │ Notification Hub │             │   │
│  │  │ (Telemetry)    │  │ (Push Notif.)    │             │   │
│  │  └────────────────┘  └──────────────────┘             │   │
│  │  ┌────────────────┐  ┌──────────────────┐             │   │
│  │  │ Key Vault      │  │ CosmosDB         │             │   │
│  │  │ (Secrets)      │  │ (Documents)      │             │   │
│  │  └────────────────┘  └──────────────────┘             │   │
│  │  ┌────────────────┐                                    │   │
│  │  │ Application    │                                    │   │
│  │  │ Insights       │                                    │   │
│  │  └────────────────┘                                    │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

---

## 5. Database Interactions

### 5.1 Database Technology
- **Primary**: Azure SQL Database
- **ORM**: Entity Framework 6 (Database-First with EDMX)
- **Secondary**: Azure CosmosDB (document storage)
- **Access Patterns**: 
  - Repository pattern via EF6 (LINQ queries)
  - Direct ADO.NET with stored procedures (performance-critical paths)

### 5.2 Key Data Domains

| Domain | Tables (Examples) | Purpose |
|--------|-------------------|---------|
| User Management | UserProfile, UserDevice, UserConsent | User data, GDPR |
| Vehicle | UserVehicle, VehicleDetail, VehicleType | Vehicle registry |
| Ride/Telemetry | Ride, RideCumulative, TravelTransection | Ride analytics |
| Notifications | PushNotification, MQTTNotification | Notification queue |
| Service/Dealer | BikeService, DealerDetail, ServiceHistory | Dealer integration |
| Content | FAQ, AppBanner, HowtoVideo, MobileSetting | App content |

### 5.3 Database Schema Management
- SSDT project (`TVS.ApiService.Database`) for schema definitions
- Migration scripts in `DBScript/` and `DatabaseScriptForPipeline/`
- Country-specific data seeding per region

---

## 6. API Integrations

### 6.1 Internal API Patterns
- RESTful endpoints with `api/{controller}/{action}` and attribute routing
- Request validation in controller layer
- Standardized response wrapper (`Responsecls`) with HTTP status, message, data

### 6.2 External API Integrations

| API | Type | Purpose |
|-----|------|---------|
| P360 Platform | REST | Vehicle telemetry, weather, sports |
| TrakNTell | REST + mTLS | GPS tracking device management |
| HERE Maps | REST | Route images, geocoding |
| MapMyIndia | REST | Route images (India market) |
| OpenWeatherMap | REST | Weather and AQI data |
| TVS DMS | REST | Dealer/service operations |
| TechPerspect | REST | EV charging station data |
| Azure Event Hubs | AMQP/HTTPS | Telemetry data ingestion |
| Bing News API | REST | News feeds |
| Cricket/Football APIs | REST | Sports data |

---

## 7. Authentication/Authorization Flow

### 7.1 Mobile App Authentication (OAuth 2.0)

```
┌──────────┐          ┌─────────────────┐          ┌──────────┐
│  Mobile  │          │  TVS Connect    │          │  SQL DB  │
│   App    │          │  API            │          │          │
└────┬─────┘          └────────┬────────┘          └────┬─────┘
     │  1. POST /api/UserLogin/Login                    │
     │     (mobile/email/social)                        │
     │─────────────────────────────────────────────────▶│
     │                         │  2. Generate OTP       │
     │                         │─────────────────────────▶
     │                         │  3. Send OTP (SMS/Email)
     │  4. OTP sent            │◀─────────────────────── │
     │◀────────────────────────│                         │
     │                         │                         │
     │  5. POST /api/UserLogin/VerifyLoginOtp            │
     │─────────────────────────────────────────────────▶│
     │                         │  6. Validate OTP       │
     │                         │─────────────────────────▶
     │  7. OAuth Bearer Token  │                         │
     │◀────────────────────────│                         │
     │                         │                         │
     │  8. API calls with      │                         │
     │     Authorization: Bearer <token>                 │
     │─────────────────────────▶                         │
```

### 7.2 Token Management
- **Access Token**: OAuth 2.0 Bearer Token (configurable expiry)
- **Refresh Token**: Issued alongside access token for re-authentication
- **JWT Filters**: Custom `JWTAuthenticationFilter` for specific endpoints
- **Rate Limiting**: `RateLimitingHandler` for API abuse prevention

### 7.3 Admin/Azure AD Authentication
- Azure AD B2B for admin operations
- Separate CORS policy for external user management pages
- `ExternalUserDeleteCorePolicyAttribute` for delete operations

---

## 8. External Systems

| System | Integration Type | Direction |
|--------|-----------------|-----------|
| TVS DMS (Dealer Management) | REST API | Bidirectional |
| P360 Connected Platform | REST API | Bidirectional |
| TrakNTell Vehicle Tracking | REST + mTLS | Bidirectional |
| TechPerspect (EV Charging) | REST API | Outbound |
| Azure Notification Hubs | SDK | Outbound |
| Azure Event Hubs | SDK/AMQP | Outbound (SAS tokens) |
| SMS Providers (Tata/Airtel/Plivo) | REST API | Outbound |
| SendGrid (Email) | SMTP | Outbound |
| Microsoft Teams (Webhooks) | HTTP | Outbound (alerts) |
| MapMyIndia / HERE Maps | REST API | Outbound |
| OpenWeatherMap | REST API | Outbound |
| RapidAPI Services | REST API | Outbound |

---

## 9. Infrastructure Dependencies

| Dependency | Service | Purpose |
|-----------|---------|---------|
| Azure App Service | Compute | Application hosting (Windows/IIS) |
| Azure SQL Database | Database | Primary data store |
| Azure Blob Storage | Storage | Files, images, ride CSVs |
| Azure Event Hubs | Messaging | Vehicle telemetry ingestion |
| Azure Notification Hubs | Messaging | Push notifications |
| Azure CosmosDB | Database | Document storage |
| Azure Key Vault | Security | Secrets management |
| Azure Application Insights | Monitoring | APM, logging, telemetry |
| Azure DevOps | CI/CD | Build and deployment pipelines |
| Azure AD | Identity | Admin authentication |

---

## 10. High-Level Sequence Flows

### 10.1 Ride Data Processing

```
Vehicle (BLE/IoT) → Mobile App → API (POST ride data)
    → RideService (calculate stats per vehicle type)
    → RideRepository (store in DB)
    → MMIDownloadService (generate route image)
    → StorageUploadService (upload to Blob)
    → Response to client
```

### 10.2 Emergency Contact Alert (Crash Detection)

```
Vehicle detects crash → Mobile App → API (POST crash alert)
    → EmergencyContactService
    → Fetch emergency contacts from DB
    → Send SMS to contacts (with location link)
    → Send push notification
    → Log incident
```

### 10.3 Vehicle Onboarding

```
User → API (POST add vehicle)
    → Validate frame number against VehicleDetail master
    → Assign vehicle type configuration
    → MAC activation (MapMyIndia/TrakNTell)
    → Create UserVehicle record
    → Configure telemetry (SAS token generation)
    → Return vehicle details
```

---

## 11. Scalability and Resiliency Considerations

### 11.1 Current Design
- **Horizontal Scaling**: Azure App Service auto-scaling per region
- **Database**: Per-region SQL databases (data isolation)
- **Caching**: In-memory `SmartCacheService` for frequently accessed data
- **Rate Limiting**: `RateLimitingHandler` to prevent API abuse
- **Failover**: SMS provider failover (primary → secondary after N failures)
- **Third-Party API Management**: Hit count tracking, circuit-breaker patterns
- **Logging**: Centralized via Application Insights + log4net

### 11.2 Resiliency Patterns
- Global exception handler with structured error responses
- Configurable timeouts for external API calls (TrakNTell: 5s, default: 30s)
- TLS 1.2 enforcement at application start
- GDPR compliance with encrypted PII storage
- Archived tables for historical ride data (reduces active table size)

### 11.3 Monitoring
- Azure Application Insights (performance counters, dependency tracking)
- Custom exception logging to database (`LogException` table)
- Microsoft Teams webhook alerts for critical failures
- Third-party API failure notifications

---

## 12. Security Considerations

| Aspect | Implementation |
|--------|---------------|
| Transport | TLS 1.2 enforced |
| Authentication | OAuth 2.0 Bearer + Azure AD |
| Authorization | Role-based with custom filters |
| Data Protection | GDPR encryption for PII fields |
| API Security | Rate limiting, CORS, X-Frame-Options: DENY |
| Secrets | Azure Key Vault + config-based |
| Client Auth | mTLS for TrakNTell integration |
| Input Validation | Controller-level validation |

---

*This document is intended for external engineering partners. Sensitive credentials and proprietary business logic have been excluded.*


---

## Document Ownership

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner** | Lakshmi Narayana | lakshmi.narayana@tvsmotor.com |
