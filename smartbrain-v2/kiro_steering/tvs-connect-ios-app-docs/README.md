# TVS Connect — iOS Application

> **Version:** 8.12.x | **Last Updated:** June 8, 2026  
> **Bundle ID:** `com.tvsmotor.TVSConnect`  
> **Minimum Deployment:** iOS 14.0 | watchOS 8.0  
> **Language:** Swift 5.x | **Build System:** Xcode 16+ / CocoaPods

---

## 1. Overview

TVS Connect is the official companion application for TVS Motor Company connected two-wheelers. It provides real-time vehicle telemetry via Bluetooth Low Energy, ride analytics, turn-by-turn navigation, service management, over-the-air firmware updates, and EV battery/charging management.

**Supported Markets:** India (primary), Sri Lanka, Nepal, Bangladesh  
**Supported Vehicles:** 30+ vehicle types across ICE motorcycles, ICE scooters, and EV scooters (iQube series)  
**Source Files:** ~3,700+ Swift files | 41 feature modules | 1,100+ EV-specific files

---

## 2. Quick Start

```bash
git clone <repository-url>
cd tvs-connect-ios-app/SourceCode
pod install
open TVS.xcworkspace
```

Select **TVS DEV** scheme → **iPhone 15** simulator → **⌘R** to build and run.

**Critical:** Always open `TVS.xcworkspace`. The `.xcodeproj` file does not include CocoaPods dependencies and will produce build failures.

---

## 3. Prerequisites

| Requirement | Version | Mandatory | Purpose |
|:------------|:--------|:---------:|:--------|
| macOS | 13+ (Ventura) | Yes | Host OS for Xcode 16 |
| Xcode | 16+ | Yes | IDE, iOS 17 SDK included |
| CocoaPods | Latest | Yes | Dependency management |
| Ruby | 2.7+ | Yes | CocoaPods runtime |
| Physical iOS device | 14.0+ | Conditional | BLE, push, GPS testing |
| Apple Developer account | — | Conditional | Device provisioning |

### Access Requirements

| Resource | Purpose | Point of Contact |
|:---------|:--------|:-----------------|
| Bitbucket repository | Source code access | Engineering lead |
| KogoAuto pod credentials | Private Kogo SDK dependency | Kogo integration team |
| Apple Developer Team | Code signing and provisioning | iOS platform lead |
| Firebase Console | Push notifications, Crashlytics | DevOps |

---

## 4. Installation

### 4.1 Clone Repository

```bash
git clone <repository-url>
cd tvs-connect-ios-app
```

### 4.2 Install Dependencies

```bash
cd SourceCode
pod install
```

If `pod install` fails:

| Issue | Resolution |
|:------|:-----------|
| Stale cache | `rm -rf Pods Podfile.lock && pod install` |
| Outdated spec repo | `pod repo update && pod install` |
| Apple Silicon arch mismatch | `arch -x86_64 pod install` |
| Permission denied | `sudo gem install cocoapods && pod install` |
| Private pod auth failure | Configure Bitbucket credentials via `git config --global credential.helper osxkeychain` |

### 4.3 Open and Build

```bash
open TVS.xcworkspace
```

1. Select **TVS DEV** scheme (toolbar dropdown).
2. Set destination to **iPhone 15** simulator.
3. Build: **⌘R**.
4. Expected result: application launches on the Login screen.

---

## 5. Build Schemes and Environments

Environment selection is enforced at compile time via compiler flags. There is no runtime environment switching.

| Scheme | Environment | Compiler Flag | Use Case |
|:-------|:------------|:--------------|:---------|
| TVS DEV | Development | `DEV_DEBUG` / `DEV_RELEASE` | Daily development |
| TVS QA | QA | — | QA validation (production-pointed) |
| TVS Cust | Customer UAT | — | Client demonstrations |
| TVS Staging | Staging | `DEBUG` / `RELEASE` | UAT testing |
| TVS | Production | — (default) | App Store release |
| TVSCI | CI | — | SonarQube static analysis |

### Compiler Flag Usage

```swift
#if DEV_DEBUG || DEV_RELEASE
    // Development APIs
#elseif DEBUG || RELEASE
    // UAT APIs
#else
    // Production APIs (App Store)
#endif
```

---

## 6. Build Commands

### Development (Simulator)

```bash
xcodebuild -workspace TVS.xcworkspace \
  -scheme "TVS DEV" \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  build
```

### Production (Device)

```bash
xcodebuild -workspace TVS.xcworkspace \
  -scheme "TVS" \
  -sdk iphoneos \
  -configuration Release \
  build
```

### Archive (Distribution)

```bash
xcodebuild -workspace TVS.xcworkspace \
  -scheme "TVS" \
  -sdk iphoneos \
  -configuration Release \
  archive -archivePath ./build/TVS.xcarchive
```

### Watch App (Standalone)

```bash
xcodebuild -workspace TVS.xcworkspace \
  -scheme "TVS Watch App" \
  -destination 'platform=watchOS Simulator,name=Apple Watch Series 9 (45mm)' \
  build
```

### Code Signing

Provisioning profiles are stored in `Certificates/`:
- **Development:** `TVSConnect__Development_Profile.mobileprovision`
- **Distribution:** `TVSConnect_Distribution_Profile.mobileprovision`

---

## 7. Project Structure

```
tvs-connect-ios-app/
├── SourceCode/
│   ├── TVS.xcworkspace              # Workspace (always open this)
│   ├── Podfile                      # CocoaPods manifest
│   ├── TVS/                         # Main app target
│   │   ├── Application/             # AppDelegate, Migration, lifecycle
│   │   ├── AppConfig/               # xcconfig files
│   │   ├── Modules/                 # 41 feature modules
│   │   │   ├── IOT-{VehicleCode}/   # Per-vehicle BLE modules
│   │   │   ├── Login/               # Authentication
│   │   │   ├── Navigation/          # Maps and routing
│   │   │   ├── Community/           # Social features
│   │   │   └── ...
│   │   ├── Services/                # Shared services (54 files)
│   │   ├── NewService/              # Modern protocol-based API pattern
│   │   ├── UnifiedDashboard/        # Primary dashboard (all vehicles)
│   │   ├── SupportingFiles/         # Core infrastructure (303 files)
│   │   │   ├── BluetoothService/    # BLE core, parsers, senders
│   │   │   ├── WebService/          # NetworkManager, APIList
│   │   │   ├── HelperClass/         # DataManager, CommonMethods
│   │   │   └── MapManager/          # Multi-provider map abstraction
│   │   ├── TVS_EV/                  # EV features (1,101 files)
│   │   │   ├── U388/               # iQube (primary EV)
│   │   │   ├── U546/               # Orbiter
│   │   │   └── CommonModules/      # Shared EV utilities
│   │   └── schema.graphqls          # Apollo GraphQL schema
│   ├── TVS Watch App/               # watchOS companion
│   ├── TVSTests/                    # Unit tests
│   ├── TVSUITests/                  # UI tests
│   └── Frameworks/                  # Vendor xcframeworks
├── Certificates/                    # Provisioning profiles and certificates
├── docs/                            # Engineering documentation
└── .kiro/                           # AI automation configuration
```

---

## 8. Architecture

The application follows MVVM with protocol-oriented service injection and vehicle-type isolation.

### Layer Responsibilities

| Layer | Contents | Responsibility |
|:------|:---------|:---------------|
| Presentation | UIKit ViewControllers, SwiftUI Views, Storyboards, XIBs | UI rendering, user interaction |
| ViewModel | ViewModels, DataSources, Delegate protocols | Business logic, state management, API orchestration |
| Service | BluetoothService, NetworkManager, RealmService, LocationManager | Shared infrastructure, hardware abstraction |
| Data | CoreBluetooth, Alamofire, Apollo, CocoaMQTT, RealmSwift | Framework-level I/O |

### Core Singletons

| Service | Access | Responsibility |
|:--------|:-------|:---------------|
| `BluetoothService.shared` | App-wide | BLE central manager, connection lifecycle |
| `NetworkManager.sharedInstance` | App-wide | HTTP execution, retry logic, auth headers |
| `NetworkConfiguration.shared` | App-wide | Environment URLs, country configuration |
| `DataManager.shared` | App-wide | UserDefaults-backed state flags |
| `BikeService.shared` | App-wide | Vehicle list, selection, capabilities |
| `LocationManager.shared` | App-wide | GPS tracking, geofencing |

### Design Patterns

| Pattern | Application |
|:--------|:------------|
| MVVM | All feature modules |
| Protocol-based services | `ServiceAPIProtocol` → `ServiceAPI` (newer code) |
| MulticastDelegate | BLE event broadcasting to multiple listeners |
| Singleton | Core services (BLE, Network, Data, Location) |
| Vehicle-type isolation | Separate `IOT-{Code}` module per vehicle |
| Compile-time environment | `#if` flags, not runtime checks |

---

## 9. Configuration

### Multi-Country

```swift
NetworkConfiguration.shared.country = .INDIA  // .SRILANKA | .NEPAL | .BANGLADESH
```

| Country | API Host | Maps Provider |
|:--------|:---------|:-------------|
| India | `{env}-tvsconnectapi.tvsmotor.net` | Mappls (primary), Google (secondary) |
| Sri Lanka | `tvs-ibasia.azurewebsites.net` | Google Maps |
| Nepal | `tvs-ibasia-nepal.azurewebsites.net` | Google Maps |
| Bangladesh | `tvs-ibasia.azurewebsites.net` | Google Maps |

### Configuration Files

| File | Purpose | Location |
|:-----|:--------|:---------|
| `TVS-Dev.xcconfig` | Environment-specific build settings | `TVS/AppConfig/` |
| `Info.plist` | Permissions, background modes, URL schemes | `TVS/Application/` |
| `TVS.entitlements` | App capabilities (production) | `TVS_EV/` |
| `TVSDebug.entitlements` | App capabilities (debug) | `TVS_EV/` |
| `NetworkConfiguration.swift` | API URL resolution | `SupportingFiles/WebService/` |
| `schema.graphqls` | GraphQL type definitions | `TVS/` |
| `apollo-codegen-config.json` | Apollo code generation config | `TVS/` |

### SDK Key Management

Third-party SDK keys are fetched from the backend at runtime:
```
GET /api/v3/secret?platform=ios
```
Build-time secrets are injected via xcconfig variables referenced in Info.plist.

---

## 10. Testing

### Run Unit Tests

```bash
xcodebuild -workspace TVS.xcworkspace \
  -scheme "TVS DEV" \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 15' \
  test
```

### Test Organization

```
TVSTests/
├── Apache/
│   └── LiveDashboard/
│       └── ApacheOnGoingRideViewModelTests.swift
├── Service/
└── ...
TVSUITests/
└── ...
```

### Testing Pattern (Standard for New Code)

```swift
protocol ServiceAPIProtocol {
    func fetchData(completion: @escaping (Result<[Model], Error>) -> Void)
}

class MockServiceAPI: ServiceAPIProtocol {
    var mockResult: Result<[Model], Error> = .success([])
    func fetchData(completion: @escaping (Result<[Model], Error>) -> Void) {
        completion(mockResult)
    }
}

func testFetchSuccess() {
    let mock = MockServiceAPI()
    mock.mockResult = .success([Model(...)])
    let vm = FeatureViewModel(api: mock)
    vm.fetchData()
    XCTAssertEqual(vm.items.count, 1)
}
```

### Code Quality

| Tool | Command | Configuration |
|:-----|:--------|:-------------|
| Jazzy (documentation) | `cd SourceCode && jazzy` | `.jazzy.yaml` |
| SonarQube (static analysis) | `sonar-scanner` | `sonar-project.properties` |
| SwiftLint | Integrated via SonarQube | — |

---

## 11. Deployment

### TestFlight Distribution

1. Increment build number in project settings.
2. Archive using the **TVS** (Production) scheme.
3. Upload via Xcode Organizer or `xcodebuild -exportArchive`.
4. Distribute through App Store Connect to TestFlight.
5. Communicate build number to QA.

### App Store Submission Checklist

- [ ] All unit tests pass.
- [ ] `CFBundleShortVersionString` incremented.
- [ ] `CURRENT_PROJECT_VERSION` incremented.
- [ ] Release notes finalized.
- [ ] Screenshots updated (if UI changed).
- [ ] Archive produced with **TVS** scheme (Production).
- [ ] No debug logging present in Release configuration.
- [ ] Firebase Crashlytics enabled and verified.
- [ ] `NSAllowsArbitraryLoads` is not set.

### Branch Strategy

| Branch | Purpose |
|:-------|:--------|
| `main` / `master` | Production-ready, release-tagged |
| `develop` | Integration branch for current sprint |
| `feature/{ticket-id}-description` | New feature development |
| `bugfix/{ticket-id}-description` | Bug fixes |
| `release/{version}` | Release stabilization |
| `hotfix/{version}` | Critical production fixes |

---

## 12. Simulator vs Device Capabilities

| Capability | Simulator | Physical Device |
|:-----------|:---------:|:--------------:|
| UI development | ✅ | ✅ |
| REST API testing | ✅ | ✅ |
| Bluetooth Low Energy | — | ✅ |
| Push notifications | — | ✅ |
| GPS (hardware) | — | ✅ |
| Apple Watch pairing | — | ✅ |
| Camera | — | ✅ |

BLE, push notifications, and Watch pairing require a physical device. Simulator-only development is limited to UI and API work.

---

## 13. Troubleshooting

| # | Issue | Resolution |
|:-:|:------|:-----------|
| 1 | `pod install` fails | `rm -rf Pods Podfile.lock && pod install` |
| 2 | "Module not found" after pull | Close workspace → `pod install` → reopen |
| 3 | Build errors after pull | Clean build folder (`⇧⌘K`) → rebuild (`⌘B`) |
| 4 | Signing/provisioning failure | Verify team selection; check `Certificates/` folder |
| 5 | Realm migration crash | Increment `schemaVersion` in `AppDelegate` |
| 6 | BLE not connecting | Simulator unsupported; use physical device |
| 7 | Watch app build failure | Select watchOS scheme; verify pod targets |
| 8 | Storyboard merge conflict | Resolve XML manually; prefer XIBs for new UI |
| 9 | `arm64` simulator error | Handled in Podfile `post_install` hook |
| 10 | Private pod auth failure | Configure Bitbucket credentials in system keychain |
| 11 | Firebase crash in debug | Firebase is intentionally disabled in DEBUG builds |
| 12 | Push notifications not received | Requires physical device + valid APNs certificate |
| 13 | Map tiles not loading | Verify Mappls/Google API key in AppDelegate |
| 14 | API returns HTTP 401 | Token expired; verify refresh logic in NetworkManager |
| 15 | Freeze on BLE connect | Ensure `setupBLECharecteristics` receives correct `BLEType` |
| 16 | Watch not receiving data | Check `WCSession.isReachable`; verify App Groups entitlement |

---

## 14. Security Requirements

| Requirement | Implementation |
|:------------|:---------------|
| No secrets in source control | Keys fetched at runtime or injected via xcconfig |
| No hardcoded production URLs | All URLs resolved through `NetworkConfiguration` |
| Secure credential storage | iOS Keychain with `kSecAttrAccessibleWhenUnlocked` |
| Memory safety in closures | `[weak self]` in all escaping closures |
| Delegate retain cycle prevention | All delegate properties declared `weak` |
| Build-time secret injection | Info.plist `${VARIABLE}` references to xcconfig values |

---

## 15. Developer Onboarding Path

| Step | Action | Outcome |
|:----:|:-------|:--------|
| 1 | Read this document | Understand project setup and structure |
| 2 | Read [HLC.md](./HLC.md) | Understand all modules and data flows (30 min) |
| 3 | Explore `NewService/` | Learn the standard pattern for new code |
| 4 | Explore `UnifiedDashboard/` | Understand the primary user-facing screen |
| 5 | Explore `SupportingFiles/BluetoothService/` | Understand the BLE communication layer |
| 6 | Read [HLD.md](./HLD.md) | Understand system architecture and integrations |
| 7 | Reference [API_SPEC.md](./API_SPEC.md) | Look up specific endpoints as needed |

---

## 16. Developer Quick Reference

| Task | Location |
|:-----|:---------|
| Add a new vehicle type | `Modules/IOT-{Code}/` + `SupportingFiles/BluetoothService/` |
| Add a new API endpoint | `NewService/Networking/` (follow `ServiceAPI` pattern) |
| Modify BLE behavior | `SupportingFiles/BluetoothService/BluetoothService.swift` |
| Add a feature module | `Modules/{Feature}/Controller/`, `ViewModel/`, `Model/`, `View/` |
| Change API URLs | `SupportingFiles/WebService/NetworkConfiguration.swift` |
| Add a Realm object | Define class → `Application/Migration.swift` → increment schema |
| EV-specific development | `TVS_EV/U388/` (iQube) or `TVS_EV/U546/` (Orbiter) |
| Modify dashboard | `UnifiedDashboard/UnifiedDashboardVM.swift` + vehicle extension |

---

## 17. Related Documentation

| Document | Scope |
|:---------|:------|
| [HLC.md](./HLC.md) | High Level Code — module inventory, data flows, entry points |
| [HLD.md](./HLD.md) | High Level Design — architecture, deployment, security, ADRs |
| [LLD.md](./LLD.md) | Low Level Design — class responsibilities, algorithms, patterns |
| [API_SPEC.md](./API_SPEC.md) | API Specification — 190+ endpoints, payloads, authentication |
| [DOC_IMPROVEMENT_SCOPE.md](./DOC_IMPROVEMENT_SCOPE.md) | Documentation improvement backlog |
| [PR Template](../.github/PULL_REQUEST_TEMPLATE.md) | Pull request checklist |

---

## 18. Changelog

| Version | Year | Changes |
|:--------|:-----|:--------|
| 8.12.0 | 2026 | Vehicle feature config, per-vehicle map provider |
| 8.11.x | 2026 | Apache N597 ride statistics |
| 8.9.0 | 2025 | EV Trip Planner |
| 8.7.0 | 2025 | Mobile number update restriction |

---

## Project Ownership & Stakeholders

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner** | Sumit Prajapat | sumit.prajapat@tvsmotor.com |

---

> **Confidentiality:** This document is intended for authorized engineering partners. It excludes API keys, secrets, production credentials, and proprietary BLE protocol details.
