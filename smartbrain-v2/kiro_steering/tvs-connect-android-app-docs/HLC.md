# TVS Connect - High Level Code Document

> **Purpose**: Vendor onboarding reference for understanding the TVS Connect Android application codebase.
> **Last Updated**: June 2026

---

## 1. Application Overview

TVS Connect is an IoT-enabled mobile companion application for TVS Motor Company two-wheeler vehicles. It provides connectivity, telemetry, navigation, and vehicle management features for both ICE (Internal Combustion Engine) and EV (Electric Vehicle) product lines.

| Attribute | Value |
|-----------|-------|
| Package Name | `com.tvsm.connect` |
| Platform | Android (minSdk 28 / targetSdk 35) |
| Language | Kotlin 2.0 + Legacy Java |
| Architecture | MVVM + Clean Architecture |
| DI Framework | Dagger Hilt 2.54 |
| Build System | Gradle 8.5.1 (Groovy + Kotlin DSL) |

---

## 2. Major Modules / Components

### Core Infrastructure (`app-core/`)

| Module | Responsibility |
|--------|---------------|
| `network-core` | Retrofit/OkHttp/Apollo networking with multiple base URL support |
| `db-core` | Room + Realm database setup |
| `hilt-core` | Application-wide DI configuration (coroutine scopes, dispatchers) |
| `location-core` | Location services abstraction |
| `common-core` | Shared utilities, base classes, constants |

### Bluetooth Stack (`bluetooth-module/`)

| Module | Responsibility |
|--------|---------------|
| `bt-layer` | BLE abstraction layer (central/peripheral pattern) |
| `bt-core` | BLE connection orchestration |
| `bike-core` | Vehicle-specific BLE protocol handling |
| `bt-feature` | BLE feature implementations per vehicle model |

### Maps & Navigation

| Module | Responsibility |
|--------|---------------|
| `core:maps` | Map abstraction with clean architecture (domain/data/presentation) |
| `feature:googlemaps` | Dynamic feature module — Google Maps |
| `feature:mapplsmaps` | Dynamic feature module — Mappls (India) |
| `feature:heremaps` | Dynamic feature module — HERE Maps |

### Vehicle & Telemetry

| Module | Responsibility |
|--------|---------------|
| `vehicle-stats-module` | Vehicle telemetry and statistics |
| `geofence-module` | Geofencing features |
| `ota-update` | Over-the-air firmware updates |
| `live-dashboard` | Real-time vehicle dashboard |
| `vehicle-access` | Remote/keyless vehicle access |

### Companion & Accessories

| Module | Responsibility |
|--------|---------------|
| `wearable` | Wear OS companion app |
| `noise-fit` | Smart accessory integration |
| `hudmodule` | Head-up display support |
| `tvs-screen-mirroring` | Screen mirroring via WiFi |
| `smart-accessory` | Smart helmet/accessory pairing |

### KMP Shared Logic (`kmp/`)

| Module | Responsibility |
|--------|---------------|
| `shared-core` | Cross-platform core logic |
| `shared-domain` | Shared domain models |
| `feature-auth` | Authentication shared logic |
| `feature-vehicle` | Vehicle management shared logic |
| `feature-alerts` | Alerts shared logic |

---

## 3. Folder Structure

```
tvs-connect-repo-2/
├── app/                        # Main application module (entry point)
├── app-core/                   # Shared core infrastructure
│   ├── common-core/
│   ├── db-core/
│   ├── hilt-core/
│   ├── location-core/
│   └── network-core/
├── bluetooth-module/           # BLE connectivity stack
│   ├── bike-core/
│   ├── bt-core/
│   ├── bt-layer/
│   └── bt-feature/
├── core/                       # Cross-cutting libraries
│   ├── maps/
│   ├── codp/
│   ├── libs/
│   └── resources/
├── feature/                    # Dynamic feature modules (maps)
│   ├── googlemaps/
│   ├── mapplsmaps/
│   └── heremaps/
├── kmp/                        # Kotlin Multiplatform modules
├── charging-infra-module/      # EV charging
├── geofence-module/
├── location-module/
├── mqtt/                       # MQTT telemetry
├── notification-module/
├── ota-update/
├── vehicle-stats-module/
├── vehicle-access/
├── wearable/
├── subscription/
├── buildSrc/                   # Centralized build logic
│   └── src/main/java/
│       ├── AppConfig.kt
│       ├── AppDependencies.kt
│       ├── LibModules.kt
│       └── Versions.kt
└── docs/                       # Documentation
```

---

## 4. Core Business Workflows

### User Onboarding
1. Splash screen → Check session validity
2. If new user → Authentication (OTP-based login/signup)
3. If existing user → Token validation → Dashboard

### Vehicle Connection (BLE)
1. User selects vehicle from dashboard
2. BLE scan initiated via `BluetoothCentral`
3. Vehicle-specific helper service activated (U399, U368, U408, etc.)
4. Cluster data receiver instantiated for telemetry parsing
5. Real-time data streamed to UI

### Navigation
1. User selects destination (search/favourites/recent)
2. Map provider resolved via `MapProviderType`
3. Route calculated (HERE/Google/Mappls)
4. Turn-by-turn navigation with BLE cluster sync
5. Navigation instructions sent to vehicle display

### Ride Tracking
1. Tour initiated from dashboard
2. GPS + BLE telemetry recorded
3. Ride data uploaded to backend on completion
4. Cumulative stats updated

---

## 5. Key Services / Classes

| Class | Role |
|-------|------|
| `TVSApplication` | Application class — BLE state, navigation, lifecycle management |
| `SplashActivity` | Entry point — session routing |
| `UniDashboardActivity` | Main dashboard |
| `RestClient` | Legacy Retrofit client manager (multiple API services) |
| `NetworkModule` | Hilt DI module for modern networking |
| `ApolloModule` | GraphQL client setup (P360 platform) |
| `TokenAuthenticator` | OkHttp Authenticator for token refresh |
| `NetworkLayer` | Kotlin coroutine-based network error handling |
| `BluetoothCentral` | BLE connection manager |
| `BaseConnectHelperService` | Abstract BLE service base class |
| `NavigationApiService` | Location/navigation API interface |
| `MapDatabase` | Room database for map/navigation data |

---

## 6. External Integrations

| Integration | Purpose | Protocol |
|-------------|---------|----------|
| TVS Connect Backend | Core APIs (user, vehicle, rides) | REST (HTTPS) |
| P360 Platform | EV telemetry, subscriptions | GraphQL + WebSocket |
| TrakNTell (TNT) | Vehicle tracking/telematics | REST + MQTT (SSL) |
| Kazam | EV charging station network | REST |
| HERE Maps | Navigation (global) | SDK |
| Mappls | Navigation (India) | SDK |
| Google Maps | Navigation (global) | SDK |
| What3Words | Location addressing | SDK |
| Firebase | Analytics, Crashlytics, Push, Config | SDK |
| Cerence | Voice assistant | SDK |
| MQTT Broker | Real-time vehicle events | MQTT over SSL |

---

## 7. Major Dependencies

| Category | Library | Version |
|----------|---------|---------|
| DI | Dagger Hilt | 2.54 |
| Networking | Retrofit | 2.9.0 |
| HTTP Client | OkHttp | 5.0.0-alpha.2 |
| GraphQL | Apollo | 3.7.3 |
| Database | Room | 2.6.1 |
| Database | Realm | 10.x |
| BLE | RxAndroidBle | 1.13.0 |
| Reactive | RxJava | 2.2.21 |
| Coroutines | Kotlinx Coroutines | 1.5.2 |
| UI | Jetpack Compose | 1.7.1 |
| Image | Glide | 4.11.0 |
| Logging | Timber | 5.0.1 |
| Analytics | Firebase BOM | 32.7.4 |
| Navigation | Jetpack Navigation | 2.7.7 |
| Serialization | Gson | 2.9.0 |

---

## 8. Runtime Architecture

```
┌─────────────────────────────────────────────────────┐
│                   TVS Connect App                     │
├─────────────┬──────────────┬────────────────────────┤
│   UI Layer  │  Domain Layer │     Data Layer          │
│ (Activities │  (Use Cases,  │  (Repositories,         │
│  Fragments, │   ViewModels) │   API Services,         │
│  Compose)   │               │   Room/Realm DAOs)      │
├─────────────┴──────────────┴────────────────────────┤
│              Core Services Layer                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Network  │ │   BLE    │ │ Location │ │  MQTT  │ │
│  │  Core    │ │  Stack   │ │  Service │ │ Client │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
├─────────────────────────────────────────────────────┤
│              External Services                        │
│  TVS Backend │ P360 │ TNT │ Firebase │ Maps SDKs    │
└─────────────────────────────────────────────────────┘
```

---

## 9. Important Entry Points

| Entry Point | Purpose |
|-------------|---------|
| `TVSApplication.onCreate()` | App initialization, Hilt, Firebase, BLE setup |
| `SplashActivity.onCreate()` | Session validation, routing |
| `UniDashboardActivity` | Main user-facing dashboard |
| `AuthenticationActivity` | Login/signup flow |
| `TourBaseActivity` | Ride/tour tracking |
| `TVSMMapActivity` | Map and navigation |
| `BaseHereMapActivity` | HERE Maps navigation |

---

## 10. High-Level Data Flow

```
User Action → UI (Activity/Fragment/Compose)
    → ViewModel (LiveData/StateFlow)
        → Repository / Use Case
            → API Service (Retrofit/Apollo) → Backend Server
            → BLE Service → Vehicle Cluster
            → Room/Realm DAO → Local Database
            → MQTT Client → Telemetry Broker
        ← Response mapped to domain model
    ← UI state updated
← User sees result
```

**Key data paths:**
- **Telemetry**: Vehicle → BLE → ClusterDataReceiver → ViewModel → UI
- **API calls**: UI → ViewModel → Repository → Retrofit → Server
- **Navigation**: MapProvider → VisualNavigator → BLE cluster sync → Vehicle display
- **Real-time tracking**: P360 GraphQL Subscription → WebSocket → UI update

---

*This document is intended for vendor onboarding purposes. No secrets, credentials, or sensitive business logic are exposed.*


---

## Document Ownership

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner** | Lakshmi Narayana | lakshmi.narayana@tvsmotor.com |
