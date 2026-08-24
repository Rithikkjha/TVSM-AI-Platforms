# TVS Connect iOS

<!-- Badges (replace with actual URLs) -->
![Platform](https://img.shields.io/badge/platform-iOS%2014%2B-blue)
![Swift](https://img.shields.io/badge/swift-5.x-orange)
![Xcode](https://img.shields.io/badge/Xcode-16%2B-blue)
![CocoaPods](https://img.shields.io/badge/deps-CocoaPods-red)

---

## 1. Application Overview

TVS Connect is the official companion app for TVS Motor Company two-wheelers. It connects to vehicles via Bluetooth Low Energy (BLE) to deliver real-time telemetry, turn-by-turn navigation, ride statistics, service booking, over-the-air firmware updates, EV battery management, and community features — serving riders across 8 international markets from a single codebase.

### Key Features

- **BLE Vehicle Pairing** — Real-time telemetry from 20+ vehicle models
- **Live Dashboard** — Speed, fuel/battery, ride modes, vehicle health
- **Navigation** — Turn-by-turn via Mappls (India), Google Maps, HERE Maps
- **Ride Statistics** — Trip history, eco scoring, speed analysis
- **EV Management** — Charging stats, battery health, trip planner (iQube)
- **OTA Updates** — Over-the-air firmware updates for connected vehicles
- **Geofencing** — Virtual boundary alerts for parked vehicles

### Supported Platforms

| Platform | Target |
|----------|--------|
| iOS | 14.0+ |
| watchOS | 8.0+ |

### Multi-Region Targets

| Target | Markets |
|--------|---------|
| TVS | India (primary) |
| TVS-SEA | Indonesia, Vietnam, Mongolia |
| TVS-LATAM | Peru, Brazil |
| TVS-Middle-East | Lebanon |
| TVS-Srilanka | Sri Lanka |
| TVS-NEPAL | Nepal |
| TVS-AFRICA | Africa |
| TVS-EUROPE | Italy |

---

## 2. Prerequisites

| Requirement | Version |
|-------------|---------|
| macOS | 13.0+ (Ventura or later) |
| Xcode | 16.0+ |
| CocoaPods | 1.14+ |
| Ruby | 2.7+ (for CocoaPods) |
| Apple Developer Account | Required for device builds & signing |

### Certificates & Profiles

Provisioning profiles and certificates are located in `Certificates/`. Ensure you have:
- Development certificate (`.p12`)
- Distribution certificate (`.p12`)
- APNs certificate (for push notifications)
- Matching `.mobileprovision` files for your target

> Contact the team lead if you need access to signing credentials.

---

## 3. Setup Instructions

Get the app running in under 30 minutes:

```bash
# 1. Clone the repository
git clone <repo-url>
cd tvs-connect-ios-app

# 2. Install dependencies
cd SourceCode
pod install

# 3. Open workspace (NOT .xcodeproj)
open TVS.xcworkspace

# 4. Select scheme and device
#    Scheme: "TVS DEV"
#    Device: iPhone 15 simulator (or physical device for BLE)

# 5. Build and run
#    Cmd + R
```

> ⚠️ Always open `TVS.xcworkspace`, never `TVS.xcodeproj`. The project won't build without Pod dependencies linked via the workspace.

---

## 4. Local Development

### Switching Environments

Environment is controlled by **build scheme selection**:

| Scheme | Environment | Use For |
|--------|-------------|---------|
| TVS-Region-Dev | Development | Daily development |
| TVS Staging/UAT | Staging | Pre-release validation |
| TVS-Region-Prod | Production | App Store builds |

Compiler flags (`#if DEV_DEBUG`, `#if RELEASE`) control environment-specific behavior. API hosts are resolved at runtime by `NetworkConfiguration.shared`.

### Simulator vs Device

| Feature | Simulator | Physical Device |
|---------|-----------|-----------------|
| UI development | ✅ | ✅ |
| Network/API calls | ✅ | ✅ |
| BLE / Bluetooth | ❌ | ✅ (required) |
| Push notifications | ❌ | ✅ |
| Location (GPS) | ✅ (simulated) | ✅ |

### Debug Tips

- Use `Console.log()` for debug prints (stripped in release builds)
- BLE state is logged via `BluetoothService` — check Xcode console for `[BLE]` prefix
- Network requests are logged by Alamofire — look for request/response pairs
- Realm Browser (free tool) helps inspect local database state
- Enable "Network Link Conditioner" in Settings to test poor connectivity

---

## 5. Environment Variables / Configuration

### xcconfig Structure

```
TVS/AppConfig/
├── TVS-Dev.xcconfig          ← Development settings
├── TVS-Africa.xcconfig       ← Africa-specific
├── TVS-EU.xcconfig           ← Europe-specific
├── TVS-LATAM.xcconfig        ← Latin America
├── TVS-ME.xcconfig           ← Middle East
├── TVS-NEPAL.xcconfig        ← Nepal
├── TVS-SEA.xcconfig          ← Southeast Asia
└── TVS-Srilanka.xcconfig     ← Sri Lanka
```

### How It Works

1. **xcconfig** defines key-value pairs (e.g., `SERVER_URL`, `DATABASE_VERSION`)
2. **Info.plist** references these via `$(SERVER_URL)` variable expansion
3. **AppConfig.swift** reads values at runtime via `Bundle.main.object(forInfoDictionaryKey:)`

### Key Configuration Keys (values are environment-specific)

| Key | Purpose |
|-----|---------|
| `SERVER_URL` | Primary backend API host |
| `WEB_URL` | Web content host |
| `EV_SERVER_URL` | EV backend host |
| `MQTT_SERVER_HOST` | MQTT broker for real-time data |
| `DATABASE_VERSION` | Realm schema version |
| `AUTH_TOKEN` | Auth token identifier |
| `P_360_TOKEN` | P360 platform token key |
| `CLIENT_CERT_PASS` | Client certificate passphrase key |

### Firebase

Each target has its own `GoogleService-Info.plist` for Firebase (Crashlytics, FCM). Ensure the correct plist is included in the target's "Copy Bundle Resources" phase.

> 🔒 **Never commit actual credential values.** Keys are injected via xcconfig and CI secrets.

---

## 6. Build Instructions

```bash
# Development build (simulator)
xcodebuild -workspace TVS.xcworkspace \
  -scheme "TVS DEV" \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  build

# Production build (device)
xcodebuild -workspace TVS.xcworkspace \
  -scheme "TVS" \
  -sdk iphoneos \
  build

# Production archive
xcodebuild -workspace TVS.xcworkspace \
  -scheme "TVS" \
  -sdk iphoneos \
  archive \
  -archivePath ./build/TVS.xcarchive

# Regional variant (e.g., SEA)
xcodebuild -workspace TVS.xcworkspace \
  -scheme "TVS-SEA" \
  -sdk iphoneos \
  archive \
  -archivePath ./build/TVS-SEA.xcarchive
```

---

## 7. Deployment Steps

### Archive & Upload

1. **Select Production scheme** — `TVS` (or regional variant)
2. **Product → Archive** (Xcode menu)
3. **Organizer → Distribute App** → App Store Connect
4. **Upload** — select signing identity and provisioning profile
5. **TestFlight** — build becomes available after Apple processing (~15 min)

### Multi-Region Builds

Each regional target (`TVS-SEA`, `TVS-LATAM`, etc.) produces a separate IPA with its own:
- Bundle identifier
- `GoogleService-Info.plist`
- xcconfig (host URLs, feature flags)
- App Store listing

### Certificate Requirements

| Type | File | Usage |
|------|------|-------|
| Development | `DevelopmentCertificates.p12` | Debug builds |
| Distribution | `DistributionCertificates.p12` | App Store / TestFlight |
| APNs | `APNSCertificates.p12` | Push notifications |

---

## 8. Testing

```bash
# Run unit tests
xcodebuild -workspace TVS.xcworkspace \
  -scheme "TVS DEV" \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  test
```

| Suite | Location | Notes |
|-------|----------|-------|
| Unit tests | `TVSTests/` | Business logic, services |
| UI tests | `TVSUITests/` | Screen flows, navigation |
| SonarQube | Scheme: `TVSCI` | Code quality + coverage reports |

### BLE Testing

BLE features **require a physical device** paired with an actual TVS vehicle (or BLE simulator hardware). Simulator builds will compile BLE code but cannot discover or connect peripherals.

### SonarQube

```bash
# Generate reports for SonarQube (uses TVSCI scheme)
xcodebuild -workspace TVS.xcworkspace \
  -scheme "TVSCI" \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  test
```

Configuration: `SourceCode/sonar-project.properties`

---

## 9. Folder Structure

```
tvs-connect-ios-app/
├── SourceCode/
│   ├── TVS.xcworkspace          ← Open this
│   ├── TVS.xcodeproj/
│   ├── Podfile                   ← Dependencies (8 targets + watchOS)
│   ├── TVS/                      ← Main app target
│   │   ├── Application/          ← AppDelegate, lifecycle
│   │   ├── AppConfig/            ← Build configs (xcconfig)
│   │   ├── Modules/              ← 44 feature modules (MVVM)
│   │   ├── Services/             ← 53 shared services
│   │   ├── SupportingFiles/      ← BLE, Network, Maps, Helpers
│   │   ├── UnifiedDashboard/     ← Newer dashboard
│   │   ├── TVS_EV/              ← EV-specific (iQube)
│   │   ├── CODPSchema/          ← GraphQL generated code
│   │   └── schema.graphqls      ← P360 GraphQL schema
│   ├── TVSTests/                 ← Unit tests
│   ├── TVSUITests/               ← UI tests
│   ├── Model/                    ← Shared data models
│   ├── Frameworks/               ← Vendor xcframeworks
│   └── sonar-project.properties  ← SonarQube config
├── Certificates/                  ← Profiles & certs
├── docs/                          ← Documentation
└── .kiro/                         ← Kiro specs & steering
```

---

## 10. Code Quality

| Tool | Config | Purpose |
|------|--------|---------|
| SonarQube | `sonar-project.properties` | Static analysis, code coverage |
| SwiftLint | Reports generated for SonarQube | Style enforcement |
| Jazzy | `.jazzy.yaml` | API documentation generation |

### Generate Documentation

```bash
cd SourceCode
jazzy
# Output: docs/ directory with HTML documentation
```

### Code Review Guidelines

- Follow MVVM architecture for new features
- Use `weak` for all delegate properties
- Organize code with `// MARK: -` sections
- Document public APIs with `///` doc comments
- Vehicle-specific code belongs in `IOT-{VehicleCode}` modules or `BikeService+{code}.swift` extensions
- Use compiler flags (`#if DEV_DEBUG`) for environment branching, not runtime checks

---

## 11. Common Troubleshooting

| Issue | Solution |
|-------|----------|
| `pod install` fails | Delete `Podfile.lock` and `Pods/`, run `pod install` again |
| Build fails after pod update | Clean build folder (`Cmd+Shift+K`), delete `DerivedData` |
| Signing / provisioning errors | Verify profiles in `Certificates/`, check Xcode signing settings |
| BLE not working on simulator | BLE **requires physical device** — no workaround |
| Realm migration crash | Increment `schemaVersion` in AppDelegate (currently v49) |
| GraphQL build errors | Re-run Apollo codegen: check `apollo-codegen-config.json` |
| "No such module" errors | Run `pod install`, ensure workspace (not project) is open |
| Watch app not compiling | Check watchOS deployment target matches Podfile (`platform :watchos, '8'`) |
| Push notifications not received | Verify APNs cert, check `GoogleService-Info.plist` target membership |
| App crashes on launch (DB) | Realm schema changed — bump `schemaVersion` and add migration block |

---

## 12. Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` / `master` | Production-ready code |
| `develop` | Integration branch for upcoming release |
| `feature/*` | New feature development |
| `bugfix/*` | Bug fixes |
| `release/*` | Release candidates |
| `hotfix/*` | Critical production fixes |

### Naming Convention

```
feature/JIRA-1234-short-description
bugfix/JIRA-5678-fix-ble-disconnect
release/8.8.0
```

### PR Process

- Create PR against `develop` (or `release/*` for hotfixes)
- Require at least 1 reviewer approval
- CI must pass (build + tests)
- Use PR template (`.github/pull_request_template.md`)

---

## 13. Project Ownership & Stakeholders

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner** | Sumit Prajapat | sumit.prajapat@tvsmotor.com |

### Internal Documentation

| Resource | Link |
|----------|------|
| Confluence Space | `[TBD — add Confluence URL]` |
| JIRA Project | `[TBD — add JIRA board URL]` |
| API Documentation | `docs/API_SPECIFICATION.md` |
| Architecture (HLD) | `docs/HLD.md` |
| Low Level Design | `docs/LLD.md` |
| High Level Code Doc | `docs/HLC.md` |

---

*Last updated: June 2026*
