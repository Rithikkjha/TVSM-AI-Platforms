# High Level Code Document

## TVS Apache RR310 — Built to Order (BTO) 3D Configurator

---

## 1. Application Overview

This is a **browser-based 3D motorcycle configurator** for the TVS Apache RR310, powering the "Built to Order" direct-to-consumer purchase experience on the TVS Motor website.

Users interact with a photorealistic 3D model of the motorcycle to:

- Select accessory kits (Dynamic Kit, Dynamic Pro / Race Kit)
- Choose body color variants (Racing Red, Titanium Black, Bomber Grey, Sepang Blue, Race Replica)
- Customize alloy wheel colors
- Pick a personal race number
- Explore bike features with audio narration and animations
- View real-time pricing that reflects their configuration
- Save configurations for later
- Place an order with payment integration
- View the configured motorcycle in Augmented Reality (AR) on mobile devices

The application is served as a **static web page** embedded via iframe on `tvsmotor.com/tvs-apache/rr-310/built-to-order/book-online`.

---

## 2. Module Summary

| Module | File(s) | Responsibility |
|--------|---------|----------------|
| Configuration Schema | `configmaster_tvs_preprod_new.js` | Defines all product variants, pricing, icon behaviors, 3D settings, and API endpoints |
| 3D Rendering Engine | `avataarrenderer_preprod.js` | A-Frame scene management, model loading, material swapping, camera, interactions, AR |
| WebXR Framework | `aframe-1.4.0.min.js` | Underlying 3D/WebXR rendering (Three.js-based) |
| Entry Points | `index.html`, `index_preprod.html` | HTML shells that bootstrap the app in production and UAT environments |
| Legal Pages | `cancellationpolicy.html`, `disclaimer.html`, `privacypolicy.html` | Static policy content for the booking flow |

---

## 3. Folder Structure

```
rr310-configurator-experience-v1/
├── index.html                      # Production entry point
├── index_preprod.html              # UAT/staging entry point
├── configmaster_tvs_preprod_new.js # Master configuration schema (skuSchema)
├── avataarrenderer_preprod.js      # Core 3D rendering engine
├── aframe-1.4.0.min.js            # A-Frame framework (local copy)
├── *.glb                           # 3D model files (multiple variants)
├── ShadowCatcher_Ground_Plane_draco.glb # Ground/shadow plane
│
├── preprodAssets/                  # All UI & media assets
│   ├── hdri/                       # Environment cubemap for IBL lighting
│   ├── global menu/                # Top-level navigation icons
│   ├── kit/                        # Kit selection button images
│   ├── color/                      # Color swatch images
│   ├── feature/                    # Feature exploration icons & callouts
│   ├── race number/                # Race number selector assets
│   ├── price_summary/              # Order summary screen assets
│   ├── save functionality/         # Save configuration UI
│   ├── Textures/                   # Material textures for swaps
│   ├── videos/                     # Feature explanation videos
│   ├── audios/                     # Audio narration files
│   ├── userflow/                   # Tutorial/onboarding overlays
│   ├── alerts/                     # Alert/popup images
│   ├── loading/                    # Loading screen assets
│   └── ...                         # Other UI resource folders
│
├── common/                         # Shared assets (AR instructions, floor grid, loading GIFs)
├── _0x7f3d2a1e/                    # Split binary chunks for chunked 3D model loading
├── cancellationpolicy.html         # Legal: cancellation policy
├── disclaimer.html                 # Legal: disclaimer
└── privacypolicy.html              # Legal: privacy policy
```

---

## 4. Core Business Workflows

### 4.1 Configuration Flow

1. User lands on the configurator page
2. Default configuration loads (Dynamic Kit + Racing Red + Black Alloys)
3. User selects Kit → Color → Wheel Color → Race Number
4. Each selection triggers material/texture swaps on the 3D model
5. Pricing updates in real time based on the selected variant
6. User clicks "Buy Now" to proceed to checkout

### 4.2 Save & Load Configuration

1. User clicks "Save Configuration"
2. If guest → prompted to login via TVS account system
3. Named configuration is stored via Firebase Cloud Functions
4. On return visit, saved configs are loaded and applied to the 3D model

### 4.3 Order Placement

1. User reviews price summary (Ex-Showroom + Kit + Accessories)
2. Accepts terms & conditions
3. Order is placed via TVS Motor Booking API
4. User is redirected to payment flow on the TVS website

### 4.4 AR Experience

1. On mobile: launches native AR via Google Model Viewer
2. On desktop: generates a QR code that links to the AR experience on mobile
3. AR places the configured motorcycle in the user's real environment

---

## 5. Key Services & Classes

### Configuration Schema (`skuSchema`)

The central data object that drives the entire application. Key sections:

| Section | Purpose |
|---------|---------|
| `glbs` / `glbIDs` | 3D model file paths and element IDs |
| `_chunksApi` | API endpoint for chunked model loading |
| `iconList` | Complete UI icon tree (parent/child hierarchy, actions, CSS classes) |
| `ConfigurationDetails` | All product variants with pricing, part IDs, material states |
| `directionalLightSettings` / `ambientLightSettings` | Scene lighting |
| `cubemapForImageBasedLighting` | HDR environment map paths |
| `containerDivs` | UI layout container definitions |
| `iconCorrelationList` | Cross-icon dependency rules |
| `globalVariables` | Runtime state (userId, auth tokens, saved configs) |

### Rendering Engine (avataarrenderer)

| Component | Responsibility |
|-----------|---------------|
| `split-gltf-model` | A-Frame component that fetches binary chunks from API, reassembles GLB, and loads into scene |
| Icon interaction handlers | Process `3D_Actions` arrays from schema (materialOpacity, modifyMeshMaterial, modelTransformation, etc.) |
| Material system | Applies textures, changes colors, manages opacity and transparency per mesh |
| Camera controls | Zoom limits, rotation blocking, programmatic camera moves |
| AR/XR toggle | Switches between 3D viewer and AR mode |
| Analytics module | Fires Google Analytics events for user interactions |
| Order module | Handles pricing calculations and TVS Booking API calls |

---

## 6. External Integrations

| Integration | Purpose | Endpoint Pattern |
|-------------|---------|-----------------|
| TVS Motor Booking API | Order placement, vehicle counts | `tvsmotor.com/api/Booking/*` |
| Firebase Cloud Functions | User auth, save/load configurations | `us-central1-tvs-configurator.cloudfunctions.net/*` |
| Azure Blob Storage (via API) | Chunked 3D model delivery | `uat-www.tvsmotor.net/api/Headless/Get` |
| Google Tag Manager | Analytics container | GTM-KD53L7 |
| Google Analytics 4 | Event tracking | G-9QYYD82JSC |
| Google Model Viewer | Mobile AR rendering | unpkg CDN |
| TVS Parent Website | iframe communication via postMessage | `tvsmotor.com` |

---

## 7. Major Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| A-Frame | 1.4.0 | WebXR/3D rendering framework (includes Three.js) |
| Three.js | Bundled with A-Frame | 3D math, materials, GLTF/Draco loading |
| Google Model Viewer | Latest (unpkg) | AR experiences on mobile |
| jQuery | 1.9.1 | DOM manipulation |
| QRCode Generator | 1.4.4 | QR codes for AR sharing |
| Google Fonts (Oxanium, Poppins) | — | Typography |

> **Note:** No package manager (npm/yarn) or build tooling is used. This is a purely static deployment with CDN-hosted dependencies.

---

## 8. Runtime Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 TVS Motor Website                         │
│              (tvsmotor.com)                               │
│                                                          │
│   ┌────────────────────────────────────────────────┐     │
│   │              <iframe>                          │     │
│   │                                                │     │
│   │   index.html                                   │     │
│   │       │                                        │     │
│   │       ├── configmaster (skuSchema)             │     │
│   │       │       └── Product config, pricing,     │     │
│   │       │           icons, variants              │     │
│   │       │                                        │     │
│   │       ├── avataarrenderer (3D Engine)           │     │
│   │       │       ├── A-Frame Scene                │     │
│   │       │       ├── GLB Model Loading            │     │
│   │       │       ├── Material/Texture System      │     │
│   │       │       ├── Icon Interaction Engine      │     │
│   │       │       ├── Camera & AR Controls         │     │
│   │       │       └── Order/Save Logic             │     │
│   │       │                                        │     │
│   │       └── External Services                    │     │
│   │               ├── Azure (chunked 3D models)    │     │
│   │               ├── Firebase (user/configs)      │     │
│   │               ├── TVS API (orders)             │     │
│   │               └── Google Analytics             │     │
│   │                                                │     │
│   └────────────────────────────────────────────────┘     │
│                                                          │
│   postMessage ↕ (auth tokens, navigation events)         │
└─────────────────────────────────────────────────────────┘
```

### Environment Modes

| Environment | Host | Config |
|-------------|------|--------|
| Production | `bto.tvsmotor.com` / `tvsmotor.com` | Minified JS, console suppressed |
| UAT / Pre-prod | `uat-www.tvsmotor.net` | Non-minified JS, debug enabled |
| Local Dev | `localhost` | Full console output, debug flag |

---

## 9. Important Entry Points

| Entry Point | Context |
|-------------|---------|
| `index.html` | Production iframe embed |
| `index_preprod.html` | UAT/staging iframe embed |
| URL parameter `skuid` | Selects product SKU (reserved for multi-product expansion) |
| URL parameter `ar=true` | Launches directly into AR mode |
| URL parameter `authToken` | Passes user session from parent site |
| URL parameter `configurationNo` | Loads a previously saved configuration |
| URL parameter `userId` | Identifies the logged-in user |
| URL parameter `favouriteNo` | Loads a favorited configuration |

---

## 10. High-Level Data Flow

```
User Action (click icon)
        │
        ▼
Icon Handler (avataarrenderer)
        │
        ├── Reads icon's "3D_Actions" array from skuSchema
        │
        ▼
Action Dispatcher
        │
        ├── materialOpacity      → Modify mesh transparency
        ├── modifyMeshMaterial    → Swap textures/colors on 3D model
        ├── modelTransformation   → Animate camera position/rotation
        ├── changeGlobalConfigVariables → Update active configuration ID
        ├── highlightMesh        → Show/hide feature callout overlays
        ├── CheckOut             → Trigger pricing summary & order flow
        ├── loadSavedConfiguration → Fetch from Firebase & apply state
        └── ShowHideDiv          → Toggle UI panel visibility
        │
        ▼
Configuration State Update
        │
        ├── Updates `ConfigurationDetails` active variant
        ├── Recalculates total price
        └── Updates UI (price display, icon states)
        │
        ▼
3D Scene Update
        │
        ├── Three.js material modifications applied to mesh
        ├── Camera animates to new position
        └── UI overlays shown/hidden
```

---

## Dependencies Overview (Visual)

```
index.html
    │
    ├── A-Frame 1.4.0 (3D engine)
    │       └── Three.js (bundled)
    │
    ├── configmaster_tvs_preprod.min.js
    │       └── skuSchema (all config data)
    │
    ├── avataarrenderer_preprod.min.js
    │       ├── Uses: A-Frame, Three.js, jQuery, skuSchema
    │       ├── Calls: TVS API, Firebase, Azure Blob
    │       └── Tracks: Google Analytics
    │
    ├── Google Model Viewer (AR)
    ├── jQuery 1.9.1
    ├── QRCode Generator
    └── Google Tag Manager
```

---

## Integration Summary

| System | Direction | Protocol | Purpose |
|--------|-----------|----------|---------|
| TVS Parent Website | Bidirectional | postMessage | Auth tokens, navigation, user context |
| TVS Booking API | Outbound | REST/HTTPS | Order creation, pricing validation |
| Firebase Cloud Functions | Outbound | REST/HTTPS | User authentication, config persistence |
| Azure Blob Storage | Outbound | REST/HTTPS | 3D model chunk delivery |
| Google Analytics | Outbound | JS SDK | User behavior tracking |
| Google Tag Manager | Outbound | JS SDK | Tag/pixel management |

---

## Notes for Vendor Onboarding

- **No build step required** — edit JS/HTML directly, deploy static files
- **Two environment configs** — switch between `index.html` (prod) and `index_preprod.html` (UAT) entry points
- **All product logic lives in `skuSchema`** — pricing, variants, icon behavior are data-driven
- **3D models are `.glb` format** — use tools like Blender for editing; Draco compression is supported
- **Anti-devtools protection** is present — disable the debugger detection block during development
- **Console logging is suppressed in production** — set `isProduction = false` or develop on localhost
- **Version identifier**: currently `Version 1.0.16` (defined in renderer)

---

*Document generated: June 2026*
