# TVS Connect - Android Application

> IoT-enabled mobile companion app for TVS Motor Company two-wheeler vehicles.

---

## Application Overview

TVS Connect provides connectivity features for TVS two-wheeler owners:

- **BLE Vehicle Pairing** — Real-time telemetry from vehicle cluster
- **Turn-by-Turn Navigation** — Multi-provider (Google/HERE/Mappls) with cluster sync
- **Ride Tracking** — GPS + telemetry recording with cloud upload
- **Crash Alerts** — Emergency assistance and contact notification
- **OTA Updates** — Over-the-air firmware updates for vehicle ECU
- **Geofencing** — Virtual boundary alerts
- **EV Features** — Charging infrastructure, range estimation (iQube)
- **Wearable** — Wear OS companion app
- **Voice Assistant** — Cerence-powered voice control
- **Community** — Ride stories, events, discussions

Supports both ICE and EV product lines across multiple regions.

---

## Setup Instructions

### Prerequisites

| Tool | Version |
|------|---------|
| Android Studio | Hedgehog (2023.1.1) or later |
| JDK | 17 |
| Android SDK | API 36 (compileSdk) |
| Gradle | 8.5.1 (bundled wrapper) |
| Git | 2.x |

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tvs-connect-repo-2
   ```

2. **Copy local properties template**
   ```bash
   cp local.properties.sample local.properties
   ```

3. **Configure local.properties**
   Add the following (obtain values from team lead):
   ```properties
   sdk.dir=/path/to/Android/sdk
   HERE_MAP_ACCESS_KEY_ID=<your-key>
   HERE_MAP_ACCESS_KEY_SECRET=<your-secret>
   MAPPLS_URL=<mappls-base-url>
   ```

4. **Open in Android Studio**
   - Import as existing Gradle project
   - Wait for sync to complete (may take several minutes on first run)

5. **Select build variant**
   - Open Build Variants panel
   - Select `domesticStageDebug` for development

---

## Local Development

### Build Debug APK

```bash
./gradlew assembleDomesticStageDebug
```

### Install on Device

```bash
./gradlew installDomesticStageDebug
```

### Run Unit Tests

```bash
./gradlew testDomesticStageDebugUnitTest
```

### Run Lint

```bash
./gradlew lintDomesticStageDebug
```

### Kotlin Style Check

```bash
./gradlew ktlintCheck
```

### Auto-format Kotlin

```bash
./gradlew ktlintFormat
```

### Clean Build

```bash
./gradlew clean assembleDomesticStageDebug
```

---

## Environment Variables

Configured via `local.properties` (gitignored):

| Variable | Purpose |
|----------|---------|
| `sdk.dir` | Android SDK path |
| `HERE_MAP_ACCESS_KEY_ID` | HERE Maps API key ID |
| `HERE_MAP_ACCESS_KEY_SECRET` | HERE Maps API key secret |
| `MAPPLS_URL` | Mappls base URL |

Build-time URLs are configured per flavor in `app/build.gradle`.

---

## Build Instructions

### Debug Builds (Development)

```bash
# India Staging
./gradlew assembleDomesticStageDebug

# India Dev
./gradlew assembleDomesticDevDebug

# Nepal Staging
./gradlew assembleNepalStageDebug
```

### Release Builds (Production)

```bash
# India Production (signed)
./gradlew assembleDomesticProdRelease

# Bundle for Play Store
./gradlew bundleDomesticProdRelease
```

### Available Flavors

| Flavor | Region | Use |
|--------|--------|-----|
| `domesticDev` | India | Development |
| `domesticStage` | India | Staging/QA |
| `domesticProd` | India | Production |
| `nepalDev/Stage/Prod` | Nepal | Nepal market |
| `srilankaDev/Stage/Prod` | Sri Lanka | Sri Lanka market |
| `southEastAsiaDev/Stage/Prod` | SEA | Southeast Asia |
| `europeDev/Stage/Prod` | Europe | European market |

---

## Deployment Steps

1. **Create release branch**
   ```bash
   git checkout -b release/8.8.0
   ```

2. **Update version** in `app/build.gradle`:
   ```groovy
   versionCode 304
   versionName "8.9.0"
   ```

3. **Build release bundle**
   ```bash
   ./gradlew bundleDomesticProdRelease
   ```

4. **Output**: `app/build/outputs/bundle/domesticProdRelease/TVSConnect-*.aab`

5. **Upload** to Google Play Console or internal distribution

---

## Testing Instructions

### Unit Tests

```bash
# All unit tests
./gradlew testDomesticStageDebugUnitTest

# Specific module
./gradlew :app-core:network-core:testDomesticStageDebugUnitTest
```

### Instrumentation Tests

```bash
# Requires connected device/emulator
./gradlew connectedDomesticStageDebugAndroidTest
```

### Lint & Code Quality

```bash
# Android Lint
./gradlew lintDomesticStageDebug

# Kotlin style
./gradlew ktlintCheck

# Auto-fix style issues
./gradlew ktlintFormat
```

---

## Folder Structure

```
tvs-connect-repo-2/
├── app/                    # Main application module
├── app-core/               # Core infrastructure
│   ├── common-core/        # Shared utilities
│   ├── db-core/            # Database setup
│   ├── hilt-core/          # DI configuration
│   ├── location-core/      # Location services
│   └── network-core/       # Networking layer
├── bluetooth-module/       # BLE stack
│   ├── bike-core/          # Vehicle protocols
│   ├── bt-core/            # BLE orchestration
│   ├── bt-layer/           # BLE abstraction
│   └── bt-feature/         # BLE features
├── core/                   # Cross-cutting
│   ├── maps/               # Map abstraction
│   ├── codp/               # CODP integration
│   └── resources/          # Shared resources
├── feature/                # Dynamic feature modules
│   ├── googlemaps/
│   ├── mapplsmaps/
│   └── heremaps/
├── kmp/                    # Kotlin Multiplatform
├── buildSrc/               # Build logic
├── docs/                   # Documentation
└── gradle/                 # Shared Gradle scripts
```

---

## Common Troubleshooting

| Issue | Solution |
|-------|----------|
| Gradle sync fails | Check `local.properties` has SDK path, check internet |
| HERE Maps crash | Verify `HERE_MAP_ACCESS_KEY_ID` in local.properties |
| Build variant missing | Sync Gradle, check flavor dimensions |
| Duplicate class errors | Run `./gradlew clean` then rebuild |
| Realm migration crash | Increment `SCHEMAVERSION` in flavor config |
| BLE not connecting | Check Bluetooth/Location permissions on device |
| ktlint failures | Run `./gradlew ktlintFormat` to auto-fix |
| Out of memory | Add `org.gradle.jvmargs=-Xmx4g` to `gradle.properties` |
| Signing error (release) | Ensure `tvs-keystore.jks` exists in `app/` |

---

## Branch Naming Convention

```
user/<initials>/<branch-name>
```

Examples:
- `user/ln/fix-ble-reconnection`
- `user/ss/feature-live-tracking`

---

## Project Ownership & Stakeholders

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner** | Lakshmi Narayana | lakshmi.narayana@tvsmotor.com |

---

## Additional Resources

| Document | Location |
|----------|----------|
| High Level Code Document | `docs/01-high-level-code-document.md` |
| High Level Design | `docs/02-high-level-design.md` |
| Low Level Design | `docs/03-low-level-design.md` |
| API Specification | `docs/04-api-specification.md` |

---

*Package: `com.tvsm.connect` | Min SDK: 28 | Target SDK: 35 | Kotlin 2.0*
