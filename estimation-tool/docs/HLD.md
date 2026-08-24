# TVS Connect - High Level Design (HLD)

> **Document Type**: Architecture Document for External Engineering Partners
> **Last Updated**: June 2026
> **Status**: Living Document

---

## 1. System Architecture

### 1.1 Architecture Pattern

TVS Connect follows **MVVM + Clean Architecture** with a multi-module Gradle structure. The app employs:

- **Presentation Layer**: Activities, Fragments, Jetpack Compose screens, ViewModels
- **Domain Layer**: Use Cases, Repository interfaces, domain models
- **Data Layer**: Repository implementations, API services, local databases, BLE data sources

### 1.2 Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                         ANDROID CLIENT                             │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    Presentation Layer                      │    │
│  │  Activities │ Fragments │ Compose │ ViewModels │ Adapters  │    │
│  └────────────────────────┬───────────────────────────────────┘    │
│                           │                                        │
│  ┌────────────────────────▼───────────────────────────────────┐    │
│  │                     Domain Layer                           │    │
│  │  Use Cases │ Repository Interfaces │ Domain Models         │    │
│  └────────────────────────┬───────────────────────────────────┘    │
│                           │                                        │
│  ┌────────────────────────▼───────────────────────────────────┐    │
│  │                      Data Layer                            │    │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────┐    │    │
│  │  │ Network  │ │  Local   │ │   BLE   │ │    MQTT      │    │    │
│  │  │(Retrofit │ │(Room +   │ │  Data   │ │   Client     │    │    │
│  │  │ Apollo)  │ │ Realm)   │ │ Source  │ │              │    │    │
│  │  └────┬─────┘ └──────────┘ └─────┬───┘ └──────┬───────┘    │    │
│  └───────┼──────────────────────────┼─────────────┼───────────┘    │
│          │                          │             │                │
└──────────┼──────────────────────────┼─────────────┼────────────────┘
           │                          │             │
           ▼                          ▼             ▼
┌──────────────────┐  ┌───────────────────┐  ┌──────────────────┐
│  TVS Backend     │  │  Vehicle (BLE)    │  │  MQTT Broker     │
│  (REST + GQL)    │  │  Cluster ECU      │  │  (TrakNTell)     │
└──────────────────┘  └───────────────────┘  └──────────────────┘
```

---

## 2. Major Components / Services

### 2.1 Application Layer

| Component | Type | Responsibility |
|-----------|------|---------------|
| TVSApplication | Application | Global state, BLE management, lifecycle |
| SplashActivity | Activity | Entry routing (auth vs dashboard) |
| UniDashboardActivity | Activity | Main dashboard |
| AuthenticationActivity | Activity | OTP login/signup |

### 2.2 Network Layer

| Component | Technology | Responsibility |
|-----------|-----------|---------------|
| NetworkModule | Hilt + Retrofit | HTTP client configuration, multiple endpoints |
| ApolloModule | Apollo GraphQL | P360 platform queries and subscriptions |
| RestClient | Retrofit (Legacy) | Legacy API client management |
| TokenAuthenticator | OkHttp Authenticator | Automatic token refresh on 401 |
| SessionTimeoutInterceptor | OkHttp Interceptor | Session validity enforcement |
| NetworkLayer | Kotlin object | Coroutine-based error handling wrapper |

### 2.3 BLE Layer

| Component | Responsibility |
|-----------|---------------|
| BluetoothCentral | Central BLE connection manager |
| BluetoothPeripheral | Peripheral device representation |
| BaseConnectHelperService | Abstract BLE GATT service |
| U399/U368/U408 HelperService | Vehicle-model-specific BLE protocols |
| ClusterDataReceiver | Parses telemetry from BLE byte streams |

### 2.4 Map & Navigation

| Component | Responsibility |
|-----------|---------------|
| MapProviderType | Enum for provider selection (Google/HERE/Mappls) |
| NavigationApiService | REST API for fav/recent locations |
| VisualNavigator (HERE SDK) | Turn-by-turn navigation engine |
| MapDatabase (Room) | Local storage for places, routes |

---

## 3. Deployment Architecture

### 3.1 Build Variants

```
┌─────────────────────────────────────────────────────────┐
│                    Build Matrix                         │
├──────────────────┬──────────────────────────────────────┤
│   Flavor         │  Environments                        │
├──────────────────┼──────────────────────────────────────┤
│ domestic (India) │  Dev / Stage / Prod                  │
│ nepal            │  Dev / Stage / Prod                  │
│ srilanka         │  Dev / Stage / Prod                  │
│ southEastAsia    │  Dev / Stage / Prod                  │
│ europe           │  Dev / Stage / Prod                  │
│ latam            │  Dev / Stage / Prod                  │
│ africa           │  Dev / Stage / Prod                  │
│ middleEast       │  Dev / Stage / Prod                  │
│ bangladesh       │  Dev / Stage / Prod                  │
├──────────────────┼──────────────────────────────────────┤
│ Build Types      │  Debug / Release (ProGuard/R8)       │
├──────────────────┼──────────────────────────────────────┤
│ Dynamic Features │  googlemaps / mapplsmaps / heremaps  │
└──────────────────┴──────────────────────────────────────┘
```

### 3.2 Deployment Flow

```
Developer → Git Push → Azure DevOps Pipeline
    → Build (assembleDomesticStageDebug / assembleDomesticProdRelease)
    → Lint + ktlint checks
    → Unit tests
    → APK/AAB signing
    → Distribution (Internal Testing / Play Store)
```

### 3.3 Infrastructure Topology

```
┌─────────────┐     HTTPS      ┌───────────────────────────┐
│ Android App │ ◄────────────► │   TVS Connect API         │
│             │                │   (Azure Cloud)           │
│             │                └───────────────────────────┘
│             │     GraphQL    ┌───────────────────────────┐
│             │ ◄────────────► │   P360 Platform (GQL)     │
│             │                │   (Azure Cloud)           │
│             │                └───────────────────────────┘
│             │     MQTT/SSL   ┌───────────────────────────┐
│             │ ◄────────────► │   TrakNTell Broker        │
│             │                │   (Vehicle Telemetry)     │
│             │                └───────────────────────────┘
│             │     BLE        ┌───────────────────────────┐
│             │ ◄────────────► │   Vehicle ECU/Cluster     │
│             │                │   (Onboard Hardware)      │
│             │                └───────────────────────────┘
│             │     HTTPS      ┌───────────────────────────┐
│             │ ◄────────────► │   Firebase Services       │
│             │                │   (Google Cloud)          │
│             │                └───────────────────────────┘
│             │     HTTPS      ┌───────────────────────────┐
│             │ ◄────────────► │   Map SDKs (HERE/         │
│             │                │   Google/Mappls)          │
└─────────────┘                └───────────────────────────┘
```

---

## 4. Database Interactions

### 4.1 Room Database (Maps)

| Entity | Purpose |
|--------|---------|
| RecentPlaceData | Recently searched/navigated places |
| TourPlaces | Tour/ride waypoints |
| FavPlace | User favourite locations |
| RecentPlacesEv | EV-specific recent places |
| FavAddressData | Favourite addresses |
| SendToVehicleData | Destinations shared to vehicle |

### 4.2 Realm Database (App-wide)

- User profile data
- Vehicle list and details
- Ride history and statistics
- Offline-first data caching
- Schema version managed per flavor (up to v40)

### 4.3 Apollo SQL Cache

- GraphQL response caching for P360 platform
- Normalized cache using `SqlNormalizedCacheFactory`

---

## 5. API Integrations

### 5.1 TVS Connect Backend

| Endpoint Group | Base Path | Purpose |
|----------------|-----------|---------|
| Authentication | `UserLogin/`, `RegisterUser/` | OTP login, signup, token refresh |
| Vehicle | `Vehicle/` | Add/manage vehicles |
| Dashboard | `UserDashboard/` | Vehicle overview |
| Ride Data | `ride`, `Travel/` | Ride recording and retrieval |
| Navigation | `location/` | Favourites, recents, sharing |
| Settings | `mobilesetting` | App configuration |
| Notifications | Push via Firebase | Alerts and updates |

### 5.2 P360 Platform (GraphQL)

- Live vehicle tracking subscriptions
- EV-specific data queries
- WebSocket-based real-time updates

### 5.3 TrakNTell (TNT)

- Vehicle telemetry via MQTT
- Certificate-pinned HTTPS for REST endpoints
- Mutual TLS authentication (PKCS12 client certificate)

### 5.4 Kazam

- EV public charging station data
- Bearer token authentication

---

## 6. Authentication / Authorization Flow

```
┌──────────┐         ┌──────────────┐         ┌───────────────┐
│  Client  │         │  TVS Backend │         │  Token Store  │
└────┬─────┘         └───────┬──────┘         └────────┬──────┘
     │                       │                         │
     │  1. Login (OTP)       │                         │
     │──────────────────────►│                         │
     │                       │                         │
     │  2. AccessToken +     │                         │
     │     RefreshToken      │                         │
     │◄──────────────────────│                         │
     │                       │                         │
     │  3. Store tokens      │                         │
     │─────────────────────────────────────────────────►
     │                       │                         │
     │  4. API Request       │                         │
     │   (AccessToken header)│                         │
     │──────────────────────►│                         │
     │                       │                         │
     │  5. 401 Unauthorized  │                         │
     │◄──────────────────────│                         │
     │                       │                         │
     │  6. Refresh Token     │                         │
     │──────────────────────►│                         │
     │                       │                         │
     │  7. New tokens        │                         │
     │◄──────────────────────│                         │
     │                       │                         │
     │  8. Retry original    │                         │
     │──────────────────────►│                         │
     │                       │                         │
```

**Key mechanisms:**
- OTP-based authentication (mobile number)
- RSA key exchange for secure token handling
- `TokenAuthenticator` (OkHttp) handles transparent token refresh
- `SessionTimeoutInterceptor` handles forced logout on session expiry
- Multi-session detection via broadcast (`USER_LOGGED_IN_OTHER_DEVICE`)

---

## 7. External Systems

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| Firebase Analytics | SDK | User behavior tracking |
| Firebase Crashlytics | SDK | Crash reporting |
| Firebase Messaging | SDK | Push notifications |
| Firebase Remote Config | SDK | Feature flags |
| HERE Maps SDK | SDK | Navigation & mapping |
| Mappls SDK | SDK | India-specific mapping |
| Google Maps SDK | SDK | Global mapping |
| What3Words | SDK | Location by 3-word address |
| Cerence ARK | SDK | Voice assistant |
| Eclipse Paho | Library | MQTT client |

---

## 8. Infrastructure Dependencies

| Dependency | Purpose | Type |
|------------|---------|------|
| Azure Cloud | Backend hosting | Cloud |
| Azure DevOps | CI/CD pipeline | DevOps |
| Google Play Store | App distribution | Distribution |
| Firebase (GCP) | Analytics, push, config | Cloud Service |
| TrakNTell MQTT | Vehicle telemetry broker | Third-party |
| Kazam Platform | EV charging network | Third-party |

---

## 9. High-Level Sequence Flows

### 9.1 App Launch Sequence

```
App Start → TVSApplication.onCreate()
    → Initialize Hilt DI
    → Initialize Firebase
    → Initialize BLE subsystem
    → Setup HERE Maps SDK
    → SplashActivity
        → Check stored session
        → [Has session] → Validate token → UniDashboardActivity
        → [No session] → AuthenticationActivity
```

### 9.2 BLE Connection Sequence

```
User taps "Connect" → Initiate BLE scan
    → Discover vehicle peripheral
    → Connect GATT
    → Discover services & characteristics
    → Enable notifications on data characteristic
    → Vehicle-specific helper service activates
    → ClusterDataReceiver parses incoming bytes
    → ViewModel receives telemetry updates
    → UI displays live data
```

### 9.3 Navigation Sequence

```
User enters destination → Search API (Mappls/HERE/Google)
    → Route calculation
    → Display route on map
    → User starts navigation
    → VisualNavigator / MapplsNavigationHelper initialized
    → Maneuver updates → BLE send to cluster
    → Voice TTS announcements
    → Destination reached → Stop navigation
```

---

## 10. Scalability and Resiliency

### 10.1 Network Resilience
- `RetryInterceptor` for automatic retry on transient failures
- `SessionTimeoutInterceptor` for graceful session handling
- Offline-first approach with Room + Realm caching
- Apollo normalized cache for GraphQL responses

### 10.2 Multi-Region Support
- 9 regional flavors with environment-specific endpoints
- Region/language headers sent with every API request
- Dynamic base URL selection (ICE vs EV endpoints)

### 10.3 Modular Architecture
- 50+ Gradle modules for separation of concerns
- Dynamic feature modules for on-demand map SDK delivery
- KMP shared modules for cross-platform logic reuse

### 10.4 BLE Resilience
- Reconnection handling in BluetoothCentral
- Vehicle-model-specific protocol adapters
- Encrypted communication (AES) for sensitive data

---

*This document is prepared for external engineering partners. Confidential business logic and credentials are excluded.*
