# TVS Connect - Low Level Design (LLD)

> **Purpose**: Detailed implementation reference for new engineering vendors.
> **Last Updated**: June 2026

---

## 1. Detailed Module Breakdown

### 1.1 App Module (`app/`)

```
app/src/main/java/com/tvsm/connect/
├── TVSApplication.java          # Application class (@HiltAndroidApp)
├── SplashActivity.java          # Entry routing
├── DBHelper.java                # SQLite/Realm helper
├── blemanager/                  # BLE central/peripheral
├── bluetooth/                   # BLE protocols per vehicle
│   ├── bluetoothlegatt/         # GATT services
│   ├── bluetoothlespp/          # SPP services
│   ├── security/                # AES encryption/decryption
│   └── sendreceive/             # Cluster data parsers
├── dashboard/                   # Dashboard UI & models
├── di/                          # DI components (AppComponent)
├── map/                         # Navigation (legacy)
├── onboarding/                  # Vehicle onboarding
├── ota/                         # OTA updates
├── service/                     # Service booking
├── settings/                    # App settings
├── tour/                        # Ride/tour tracking
├── user/                        # Authentication, profile
├── utils/                       # Utilities
├── voiceAssist/                 # Voice assistant
├── webservice/                  # API clients (RestClient, APIService)
└── notifications/               # Notification handling
```

### 1.2 Network Core (`app-core/network-core/`)

```
com/tvsm/network_core/
├── di/
│   ├── NetworkModule.kt         # Hilt module: OkHttp + Retrofit instances
│   └── ApolloModule.kt          # Apollo GraphQL client
├── NetworkLayer.kt              # Coroutine error handler
├── NetworkUtilities.kt          # Runtime token/user state
├── SessionTimeoutInterceptor.kt # 401 handling
├── CustomInterceptor.kt         # Custom headers
├── TLSSocketFactory.kt          # TLS 1.2 socket factory
├── interceptor/
│   └── RetryInterceptor.kt      # Automatic retry logic
└── PrePurchaseFlowApiService.kt # Pre-purchase API
```

### 1.3 Maps Core (`core/maps/`)

```
com/tvsm/connect/core/maps/
├── domain/
│   ├── MapProviderType.kt       # Google/HERE/Mappls enum
│   ├── models/                  # Domain models (PlaceData, requests, responses)
│   └── repository/              # Repository interfaces
├── data/
│   └── repository/              # Repository implementations
├── network/
│   └── NavigationApiService.kt  # Retrofit interface
├── room/
│   ├── database/MapDatabase.kt  # Room DB definition
│   ├── dao/                     # Data Access Objects
│   └── entity/                  # Room entities
├── presentation/
│   └── fragments/               # Map UI fragments
└── di/
    ├── MapBindsModule.kt        # Interface bindings
    └── MapProvidesModule.kt     # Instance providers
```

---

## 2. Class / Service Responsibilities

### 2.1 Network Classes

| Class | Responsibility |
|-------|---------------|
| `NetworkModule` | Provides multiple named OkHttp clients & Retrofit instances (EV, ICE, TNT, Kazam, OTA, Dynamic) |
| `ApolloModule` | Provides Apollo GraphQL client with WebSocket subscription support |
| `NetworkLayer` | Wraps suspend functions with try/catch, maps HTTP errors to Result<T> |
| `NetworkUtilities` | Holds runtime state: access tokens, user IDs, vehicle type flags |
| `SessionTimeoutInterceptor` | Intercepts 401 responses, broadcasts session expiry |
| `RetryInterceptor` | Retries failed requests (configurable count) |
| `TLSSocketFactory` | Forces TLS 1.2 on older Android versions |
| `CustomInterceptor` | Adds custom headers (version, platform) |

### 2.2 BLE Classes

| Class | Responsibility |
|-------|---------------|
| `BluetoothCentral` | Scans, connects, manages BLE peripherals |
| `BluetoothPeripheral` | Represents a connected BLE device |
| `BaseConnectHelperService` | Abstract GATT callback handler |
| `U399HelperService` | Apache-series vehicle BLE protocol |
| `U368HelperService` | NTorq-series vehicle BLE protocol |
| `U399ClusterDataReceiver` | Parses U399 telemetry byte arrays |
| `U408ClusterDataReceiver` | Parses U408 telemetry byte arrays |
| `U368ClusterDataManager` | Manages U368 bidirectional data |
| `BluetoothSppService` | Classic Bluetooth SPP for legacy vehicles |
| `U399EncryptDecryptDataUtils` | AES encryption for BLE payloads |
| `U368EncryptDecryptDataUtils` | AES encryption for U368 |

### 2.3 API Client Classes

| Class | Responsibility |
|-------|---------------|
| `RestClient` | Initializes and manages multiple Retrofit instances (legacy) |
| `APIService` | Retrofit interface with 150+ endpoint declarations |
| `TokenAuthenticator` | OkHttp Authenticator — calls refresh token API on 401 |
| `RefreshTokenService` | Retrofit interface for token refresh endpoint |
| `NavigationApiService` | Kotlin coroutine-based location/navigation API |

### 2.4 DI Classes

| Class | Responsibility |
|-------|---------------|
| `CoroutineModule` | Provides IO/Main/Default coroutine scopes and dispatchers |
| `AppComponent` | Dagger component for dynamic feature module injection |
| `MapBindsModule` | Binds repository interfaces to implementations |
| `MapProvidesModule` | Provides Room database, DAOs, Retrofit instances |

---

## 3. API Flow Details

### 3.1 Legacy API Flow (RestClient)

```
Activity/Fragment
    → RestClient.getApiService().someEndpoint(params)
    → Returns Call<ResponseType>
    → RestClient.makeApiRequest(context, call, listener, reqCode, showProgress)
        → Checks connectivity
        → Shows progress dialog
        → Enqueues call
        → onResponse:
            → 200: listener.onApiResponse(call, body, reqCode)
            → 401: Broadcast logout
            → 400/500: Show error dialog
        → onFailure: Show connectivity error
```

### 3.2 Modern API Flow (Hilt + Coroutines)

```
ViewModel
    → Repository.someMethod()
        → NetworkLayer.handleRequest(context) {
            apiService.someEndpoint(params)
        }
        → Returns Result<T>
            → Success: emit domain model
            → Failure: emit error state
    → LiveData/StateFlow updated
    → UI observes and renders
```

### 3.3 GraphQL Subscription Flow

```
ViewModel
    → ApolloClient.subscription(SomeSubscription())
        → WebSocket connection to P360 WSS endpoint
        → Authorization via connection payload
        → Receives real-time updates
        → Maps to domain model
    → UI updates with live data
```

---

## 4. Internal Component Interactions

### 4.1 BLE → UI Data Flow

```
Vehicle ECU
    → BLE Notification (byte[])
        → BaseConnectHelperService.onCharacteristicChanged()
            → Decrypt (AES if applicable)
            → Route to vehicle-specific receiver
                → U399ClusterDataReceiver.processData()
                → Parse protocol-specific fields
                → Update TVSApplication state
                → Post to LiveData / broadcast
    → ViewModel observes
    → UI renders telemetry
```

### 4.2 Navigation → BLE Cluster Sync

```
NavigationManager (HERE/Mappls)
    → Maneuver update callback
        → ManeuverUtils.mapToClusterFormat()
        → BaseConnectHelperService.writeCharacteristic()
            → Encode navigation instruction bytes
            → BLE write to vehicle display characteristic
    → Vehicle cluster shows turn arrow + distance
```

### 4.3 Module Dependency Graph (Simplified)

```
app
├── app-core:network-core
├── app-core:hilt-core
├── app-core:db-core
├── app-core:common-core
├── bluetooth-module:bt-core
│   ├── bluetooth-module:bt-layer
│   ├── bluetooth-module:bike-core
│   └── app-core:network-core
├── core:maps
│   ├── app-core:network-core
│   └── core:resources
├── vehicle-stats-module
├── geofence-module
├── notification-module
└── feature:* (dynamic)
```

---

## 5. Database Schema Usage

### 5.1 Room (MapDatabase) — Version 2

| Entity | Fields | Purpose |
|--------|--------|---------|
| `RecentPlaceData` | id, name, lat, lng, address, timestamp | User recent searches |
| `TourPlaces` | id, placeName, lat, lng, order | Tour waypoints |
| `FavPlace` | id, name, lat, lng, address, vin | Favourite locations per vehicle |
| `RecentPlacesEv` | id, name, lat, lng, address | EV-specific recent places |
| `FavAddressData` | id, label, address, lat, lng | Labelled addresses (home/work) |
| `SendToVehicleData` | id, name, lat, lng, vehicleId | Destinations shared to vehicle |

### 5.2 Realm Database

- Schema version varies by flavor (up to v40)
- Stores: User profile, Vehicle list, Ride data, OTP responses, Dashboard state
- Migrations handled per version increment

### 5.3 SharedPreferences

- Access/Refresh tokens
- User ID, session ID
- Vehicle type, connection state
- Feature flags, language preferences
- Firebase client ID

---

## 6. Request/Response Lifecycle

### 6.1 Standard REST Request

```
1. UI triggers action
2. ViewModel calls repository method
3. Repository invokes API service
4. OkHttp Interceptor chain:
   a. CacheInterceptor: Adds headers (userId, region, token)
   b. LoggingInterceptor: Logs request/response
   c. SessionTimeoutInterceptor: Checks response code
   d. RetryInterceptor: Retries on failure
5. Request sent to server
6. Response received
7. Gson deserializes to model
8. Repository maps to domain model
9. ViewModel updates state
10. UI observes and renders
```

### 6.2 Token Refresh (Transparent)

```
1. API returns 401
2. TokenAuthenticator.authenticate() triggered
3. Calls RefreshTokenService.refreshToken()
4. If 200: Updates stored tokens, retries original request
5. If fails: Returns null → user logged out
```

---

## 7. Validation Logic

### 7.1 Input Validation

| Context | Validation |
|---------|-----------|
| OTP | 4-6 digit numeric, non-empty |
| Mobile number | Country-specific format, required |
| VIN/Frame number | Alphanumeric, length validation |
| Email | Pattern match (optional field) |
| Vehicle nickname | Max length, no special chars |

### 7.2 Network Validation

| Check | Action |
|-------|--------|
| No connectivity | Show "Connection not available" dialog |
| Timeout | Show "Connection timeout" message |
| 401 Response | Trigger token refresh or force logout |
| 400 Response | Parse error body, show message |
| Empty response | Graceful fallback |

---

## 8. Error Handling

### 8.1 Network Error Handling (`NetworkLayer.kt`)

```kotlin
suspend fun <T> handleRequest(context, requestFunc): Result<T> {
    try {
        Result.success(requestFunc())
    } catch (ex: Exception) {
        when (ex) {
            is HttpException → when (ex.code()) {
                401 → broadcast logout, Result.failure
                500 → Result.failure("Something went wrong")
                502 → Result.failure("Something went wrong 502")
            }
            is UnknownHostException → Result.failure("Network error")
            is TimeoutException → Result.failure("Connection timeout")
            else → Result.failure(ex.message)
        }
    }
}
```

### 8.2 Legacy Error Handling (`RestClient.makeApiRequest`)

- HTTP 200 → Success callback
- HTTP 400 → Parse error body, show dialog
- HTTP 401 → Broadcast `USER_LOGGED_IN_OTHER_DEVICE`
- HTTP 500 → Error callback
- Network failure → Show connectivity error
- Timeout → Show timeout message
- EOF → Show generic error

### 8.3 BLE Error Handling

- Connection timeout → Retry with backoff
- GATT disconnection → Notify user, attempt reconnect
- Encryption failure → Log error, reject data
- Characteristic write failure → Retry queue

---

## 9. Key Algorithms / Business Rules

### 9.1 Vehicle Type Resolution

```
vehicleTypeId → determines:
    - BLE protocol (U399, U368, U408, U445B, N360, etc.)
    - Dashboard layout
    - Available features
    - API endpoints for ride data
    - Cluster data parser
```

### 9.2 Token Management

```
- Access Token: Short-lived, sent as header on every request
- Refresh Token: Used to obtain new access token on expiry
- RSA Key Exchange: Public key sent during login, private key stored locally
- Encrypted storage via SharedPreferences (base64 encoded)
```

### 9.3 Navigation Instruction Encoding

```
Maneuver from Map SDK → ManeuverUtils
    → Convert to byte array protocol:
        - Direction code (left/right/U-turn/straight)
        - Distance to maneuver (meters)
        - ETA (seconds)
        - Road name (truncated)
    → BLE write to cluster display characteristic
```

### 9.4 Ride Data Aggregation

```
During ride:
    - GPS coordinates sampled
    - BLE telemetry (speed, RPM, fuel) collected
    - Distance calculated from GPS
    - Duration tracked
On ride end:
    - Data serialized (multipart form)
    - Uploaded to server with route file
    - Local cumulative stats updated
```

---

## 10. Configuration Handling

### 10.1 Build-Time Configuration

| Source | Content |
|--------|---------|
| `buildSrc/Versions.kt` | Library version constants |
| `buildSrc/AppDependencies.kt` | Dependency declarations |
| `buildSrc/LibModules.kt` | Module path constants |
| `buildSrc/CommonUrl.kt` | Environment URLs (P360, MQTT) |
| `app/build.gradle` (flavors) | Per-region API URLs, feature flags |
| `gradle.properties` | HERE Maps keys, Mappls URL |

### 10.2 Runtime Configuration

| Source | Content |
|--------|---------|
| `SharedPreferences` | User tokens, preferences, flags |
| `BuildConfig` | Compile-time constants (URLs, keys) |
| `Firebase Remote Config` | Feature toggles, A/B tests |
| `NetworkUtilities` | Runtime API state (tokens, user IDs) |

### 10.3 Key BuildConfig Fields

| Field | Purpose |
|-------|---------|
| `BASE_URL` | Primary API base URL |
| `BASE_URL_EV` | EV-specific API base URL |
| `P360_URL` | GraphQL endpoint |
| `MQTT_URL` | MQTT broker URL |
| `TNT_BASE_URL` | TrakNTell API |
| `KAZAM_BASE_URL` | Kazam charging API |
| `isIndia` | Region flag |
| `COUNTRY_CODE` | Numeric country identifier |
| `isCustomerBuild` | Log verbosity flag |

---

*This document is intended to help new engineering vendors understand implementation details. No secrets or credentials are exposed.*


---

## Document Ownership

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner** | Lakshmi Narayana | lakshmi.narayana@tvsmotor.com |
