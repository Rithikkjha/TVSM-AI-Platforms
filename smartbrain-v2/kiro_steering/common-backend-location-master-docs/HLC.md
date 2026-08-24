# High Level Code Document — Location Master

---

## 1. Application Overview

**Location Master** is a Spring Boot microservice that provides dealer discovery, location management, and dealer network administration for TVS Motor Company. It serves as the backend for the TVS Dealer Locator (consumer-facing) and the Self-Service Admin Portal (internal).

| Attribute | Value |
|-----------|-------|
| Language | Java 17 |
| Framework | Spring Boot 3.5.13 |
| Database | MongoDB Atlas (Document DB) |
| Build Tool | Maven 3.9+ |
| Deployment | Azure Kubernetes Service (AKS) |
| API Style | REST (JSON) |
| Auth | Azure AD B2C (JWT) |

---

## 2. Major Modules / Components

| Module | Package | Responsibility |
|--------|---------|---------------|
| Dealer Locator (Consumer) | CountryController, DealershipLocationService | Dealer search, proximity, provinces |
| Dealer Locator (Proximity) | DealerProximityController, DealerProximityService | Nearest dealer via MDP |
| IB Dealer Management | IBDealerController, IBDealerManagementService | CRUD, list, export, template download |
| Admin Flow (Location Verification) | AdminFlowController, AdminFlowService | Dealer verification workflow |
| Mobile Flow | MobileFlowController, MobileFlowOperationalService | Dealer submits location via mobile |
| Location Data | LocationController, LocationService | Pincode, state, district, area lookups |
| User Management | UserXController, UserXService | User CRUD, role-based access |
| Migration | MigrationController | Bulk import (CSV/XLSX) |
| Country Config | CountryController, CountryService | Country settings, filter config |

---

## 3. Folder Structure

```
src/main/java/com/tvsmotor/location_master/
├── ENUM/                    # Enums (DealerFilterType, DealershipStatus, ContactType)
├── config/                  # Spring configs (AzureBlob, OkHttp, Security, Cache)
├── controller/              # REST controllers (13 controllers)
├── entity/                  # MongoDB document entities
├── exception/               # Global exception handler (RestExceptionHandler)
├── model/
│   ├── request/             # Request DTOs
│   ├── response/            # Response DTOs
│   ├── mongo_projections/   # MongoDB aggregation projections
│   └── mongo_repo_supporter/# Supporting models for complex queries
├── repository/              # MongoDB repositories (19 repositories)
├── service/                 # Business logic services (35+ services)
│   └── interfaces/          # Service interfaces (Validateable, Sanitizeable)
└── utils/                   # Utilities (GeneralUtils, CsvFileParser, XlsxFileParser, CacheManager)

src/main/resources/
├── application.properties        # Main config (env variable references)
├── application-local.properties  # Local dev overrides
└── logback-spring.xml            # Logging config

src/test/java/                    # Unit tests (104 test files)
```

---

## 4. Core Business Workflows

### Workflow 1: Dealer Proximity Search (Consumer)
```
User enters location → Google Places Autocomplete (lat/lng) → POST /api/v1/finder/dealers
→ Backend calls MDP Service (proximity API) → Returns nearest dealers sorted by distance
```

### Workflow 2: IB Dealer Search (International)
```
User selects country + province/city → POST /api/v1/dealer-search
→ Backend queries MongoDB ($geoNear or province/city filter) → Returns dealer list
```

### Workflow 3: Dealer Location Verification (Admin)
```
Admin sends SMS to dealer → Dealer opens link → Submits address + photo
→ Admin reviews (SAP vs submitted vs photo location) → Approves/Rejects
```

### Workflow 4: Bulk Dealer Import
```
Admin uploads Excel → POST /api/v1/migration/import-dealership-locations
→ Parse XLSX → Validate + Sanitize each row → Insert/Update/Delete in MongoDB
```

### Workflow 5: Dealer Export
```
Admin requests export → POST /api/v1/dealer/export
→ Fetch dealers from MongoDB → Generate XLSX in memory → Return as file download
```

---

## 5. Key Services / Classes

| Service | Purpose |
|---------|---------|
| DealershipLocationService | Dealer search, provinces, import |
| IBDealerManagementService | Dealer CRUD, list, export, template |
| AdminFlowService | Verification workflow, SMS, approval |
| DealerProximityService | Proximity search via MDP |
| MobileFlowOperationalService | Dealer submits location data |
| LocationService | Pincode/state/district lookups |
| CountryService | Country config, filter options |
| UserXService | User management, role-based access |
| MDPDealerService | MDP API integration (dealer data) |
| AzureBlobOperationService | Photo upload, presigned URLs, file download |
| NotificationSmsDispatcherService | SMS sending via notification service |
| GeocodingService | Google Geocoding API integration |
| CronService | Periodic JVM metrics logging |
| AuditLogService | Audit trail for admin actions |
| SecretKeyManager | Secret key generation for mobile flow |

---

## 6. External Integrations

| External Service | Purpose | Protocol | Auth |
|-----------------|---------|----------|------|
| MDP Service | Dealer master data, proximity search | REST (HTTP) | Azure B2C token |
| Notification Service | Send SMS to users/dealers | REST (HTTP) | Azure B2C token + APIM key |
| UMS Service | User management, dealer contacts | REST (HTTP) | Azure B2C token |
| Google Places API | Address autocomplete | REST (HTTPS) | API Key |
| Google Geocoding API | Address to lat/lng | REST (HTTPS) | API Key |
| Azure Blob Storage | Photo storage, templates | Azure SDK | Connection string |
| Azure AD B2C | Token generation | OAuth 2.0 | Client ID + Secret |

---

## 7. Major Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| Spring Boot | 3.5.13 | Application framework |
| Spring Data MongoDB | (managed) | MongoDB integration |
| Lombok | 1.18.34 | Boilerplate reduction |
| Apache POI | (managed) | Excel read/write (XLSX) |
| OkHttp | (managed) | HTTP client for external APIs |
| Azure Storage Blob SDK | (managed) | Blob storage operations |
| Sentry | (managed) | Error tracking |
| JaCoCo | 0.8.11 | Code coverage |
| OpenCSV | (managed) | CSV parsing |

---

## 8. Runtime Architecture

```
AKS Cluster (Central India)
├── Pod: location-master
│   • Spring Boot 3.5 (Java 17)
│   • Port: 8080
│   • Context path: /location-master
│   • Heap: 4GB max
│   • CPU: 250m request
│   • Profiles: dev / uat / prod
│
│   Ingress: Azure APIM → Internal Router → Pod:8080
│
├── MongoDB Atlas (ap-south-1, Replica Set, 3 nodes)
├── Azure Blob Storage (Central India)
└── External APIs (MDP, Notification, UMS, Google)
```

### Runtime Characteristics:
- **Startup time:** ~3 sec (with 250m CPU)
- **Thread pool:** 20 core threads (async executor)
- **Caching:** In-memory (Spring Cache) with TTL-based expiry
- **Logging:** Logback with rolling file (200MB max, daily rotation)
- **Metrics:** JVM memory + executor stats logged every 60 sec (CronService)

---

## 9. Important Entry Points

| Entry Point | Type | Path |
|-------------|------|------|
| Application Main | Class | LocationMasterApplication.java |
| Dealer Search (Consumer) | API | POST /api/v1/finder/dealers |
| IB Dealer Search | API | POST /api/v1/dealer-search |
| Create Dealer | API | POST /api/v1/dealer |
| Dealer List | API | POST /api/v1/dealer/list |
| Dealer Export | API | POST /api/v1/dealer/export |
| Template Download | API | GET /api/v1/dealer/template |
| Admin Verification | API | POST /api/v1/admin-flow/verification |
| Provinces | API | GET /api/v1/country/{code}/provinces |
| Pincode Details | API | GET /api/v1/location/pincode/{pin} |
| Health Check | API | GET /api/v1/test/health |
| Cache Clear | API | DELETE /api/v1/test/cache/{type}/{key} |

---

## 10. High-Level Data Flow

```
End User → Akamai CDN → Azure APIM → Location Master (AKS)
                                              │
                              ┌────────────────┼────────────────┐
                              │                │                │
                        MongoDB Atlas    MDP Service    Notification Service
                        (Dealers,        (Proximity,    (SMS via Infobip)
                         Locations,       Dealer Data)
                         Users)                         Azure Blob Storage
                                                       (Photos, Templates)
```

---

## Integration Summary

| Integration | Direction | Data Exchanged |
|-------------|-----------|---------------|
| Location Master → MDP | Outbound | Dealer proximity data, dealer details |
| Location Master → Notification | Outbound | SMS content (dealer info + Google Maps URL) |
| Location Master → UMS | Outbound | User contacts, dealer contacts |
| Location Master → Azure Blob | Outbound | Photo upload/download, template files |
| Location Master → Google API | Outbound | Geocoding (address → lat/lng) |
| Location Master ↔ MongoDB | Bidirectional | All CRUD operations |
| APIM → Location Master | Inbound | All API requests (authenticated) |

---

*Document generated for vendor onboarding purposes. No secrets, credentials, or sensitive business logic exposed.*
