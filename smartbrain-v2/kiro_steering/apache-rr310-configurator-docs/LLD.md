# Low Level Design — TVS Apache RR310 BTO Configurator

---

## Overview

This document details the internal implementation architecture of the TVS Apache RR310 Built-to-Order 3D Configurator. It covers module interactions, data flow, business logic algorithms, API contracts, error handling, and configuration management to enable new engineering vendors to understand and extend the codebase effectively.

---

## High Level Design — Quick Recap

Reference doc: [HLD - TVS RR310 BTO Configurator](./HLD.md)

The application is a static client-side 3D configurator embedded via iframe on tvsmotor.com. It uses A-Frame/Three.js for WebGL rendering, a JSON-driven schema (`skuSchema`) for all product logic, and integrates with TVS APIs for orders and Firebase for user config persistence.

---

## Assumptions

- All static assets are served via CDN with HTTPS
- No server-side rendering — all 3D computation happens on the client GPU
- The parent TVS website handles authentication; tokens are passed via URL parameters
- The configurator has no build toolchain — deployment is direct static file upload
- Browser must support WebGL 2.0 and ES6+ JavaScript
- jQuery 1.9.1 is available globally for DOM operations
- A-Frame 1.4.0 and Three.js are loaded before renderer initialization

---

## Components

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    index.html (Bootstrap Shell)                   │
├──────────────────────┬──────────────────────────────────────────┤
│  configmaster.js     │  avataarrenderer.js                       │
│  (Configuration      │  (Runtime Engine)                         │
│   Schema)            │                                           │
│                      │  ┌─────────────────────────────────────┐ │
│  • skuSchema object  │  │  Initialization Module              │ │
│  • Product variants  │  │  • Environment detection            │ │
│  • Icon definitions  │  │  • Schema validation                │ │
│  • Pricing data      │  │  • Scene setup                      │ │
│  • API endpoints     │  │  • Model loading                    │ │
│  • 3D action rules   │  ├─────────────────────────────────────┤ │
│                      │  │  UI Generation Module               │ │
│                      │  │  • Dynamic icon creation            │ │
│                      │  │  • Callout management               │ │
│                      │  │  • Scroll picker (race numbers)     │ │
│                      │  ├─────────────────────────────────────┤ │
│                      │  │  3D Action Dispatcher               │ │
│                      │  │  • Action routing (switch/case)     │ │
│                      │  │  • Material modification            │ │
│                      │  │  • Model transformation             │ │
│                      │  │  • Animation playback               │ │
│                      │  ├─────────────────────────────────────┤ │
│                      │  │  Configuration Engine               │ │
│                      │  │  • Variant loading                  │ │
│                      │  │  • Price calculation                │ │
│                      │  │  • State management                 │ │
│                      │  ├─────────────────────────────────────┤ │
│                      │  │  API Integration Module             │ │
│                      │  │  • Save/Load configs                │ │
│                      │  │  • Order placement                  │ │
│                      │  │  • Booking validation               │ │
│                      │  ├─────────────────────────────────────┤ │
│                      │  │  AR/XR Module                       │ │
│                      │  │  • Context switching                │ │
│                      │  │  • QR code generation               │ │
│                      │  │  • Model Viewer integration         │ │
│                      │  ├─────────────────────────────────────┤ │
│                      │  │  Analytics Module                   │ │
│                      │  │  • GA4 event tracking               │ │
│                      │  │  • GTM data layer                   │ │
│                      │  └─────────────────────────────────────┘ │
└──────────────────────┴──────────────────────────────────────────┘
```

### Component Responsibilities

| Component | File | Key Responsibilities |
|-----------|------|---------------------|
| Bootstrap Shell | `index.html` | DOM structure, script loading order, URL param extraction, auth flow, postMessage listener |
| Configuration Schema | `configmaster_tvs_preprod_new.js` | All product data, icon hierarchies, pricing matrices, API URLs, validation rules |
| 3D Rendering Engine | `avataarrenderer_preprod.js` | Scene lifecycle, model loading, material system, user interactions, business logic |
| Split GLB Loader | Custom A-Frame component in renderer | Chunked binary model reassembly and validation |
| CSS Styling | `index_preprod.css` | Responsive layout, icon positioning, animation classes |

---

## API Design

### 1. Save User Configuration

**Endpoint:** `POST https://www.tvsmotor.com/api/Headless/Post`

**Request:**
```json
{
  "api": "/api/WebSiteUserConfiguration/WebSiteUserConfigurations?_t=1718400000000",
  "jsonRequest": "{\"userid\":\"<USER_ID>\",\"config\":\"<JSON_STRING>\",\"isBuyNowClicked\":false,\"isSaveClicked\":true,\"currentConfigNo\":\"0\",\"modelName\":\"RR310\"}"
}
```

**Response (Success):**
```json
{
  "Success": true,
  "Message": "Configuration saved successfully"
}
```

**Status Codes:** `200` Success | `400` Invalid payload | `401` Unauthorized | `500` Server error

---

### 2. Get User Configurations

**Endpoint:** `POST https://www.tvsmotor.com/api/Headless/Post`

**Request:**
```json
{
  "api": "/api/WebSiteUserConfiguration/GetWebSiteUserConfigurations?_t=1718400000000",
  "jsonRequest": "{\"userid\":\"<USER_ID>\",\"modelName\":\"RR310\"}"
}
```

**Response (Success):**
```json
{
  "Success": true,
  "Message": "[{\"configurationNumber\":\"0\",\"ConfigurationName\":\"My RR310\",\"FavouriteNumber\":\"24\",\"PartId\":\"N71904208F\"}]"
}
```

---

### 3. Place Order

**Endpoint:** `POST https://uat-www.tvsmotor.net/api/placeorderforavataar`

**Request:**
```json
{
  "SessionId": "<SESSION_ID>",
  "UserId": "<USER_ID>",
  "CustomVehicleName": "Apache RR310",
  "PartId": "N71904208F",
  "Price": {
    "RacePackage": "0",
    "total": "293290",
    "Base": "276690",
    "ExShowroom": "276690",
    "DynamicPackage": "16600",
    "DynamicProPackage": "0",
    "AlloyWheelColor": "0",
    "SpecialEditionColor": "0",
    "FavouriteNumber": "24"
  },
  "TotalPrice": "293290",
  "Name": "<USER_NAME>",
  "Phone": "<PHONE>",
  "Email": "<EMAIL>",
  "VehicleCode": "0",
  "VehicleName": "NA",
  "VariantCode": "NA",
  "VariantName": "NA",
  "ColorCode": "NA",
  "ColorName": "NA",
  "City": "NA"
}
```

**Response (Success):**
```json
{
  "RedirectUrl": "https://www.tvsmotor.com/payment/checkout?orderId=12345"
}
```

**Post-Response Behavior:** The `RedirectUrl` is sent to the parent frame via `postMessage`, and `window.parent.location.href` is set to navigate to payment.

---

### 4. Get Vehicle Order Count

**Endpoint:** `GET https://www.tvsmotor.com/api/Booking/GetVehicleOrderCountFromVehicleCode?vehicleCode=101`

**Response:**
```json
{
  "MaxBooking": "500",
  "SuccessRecord": "450"
}
```

**Business Logic:** `availableBooking = MaxBooking - SuccessRecord`

---

### 5. Chunked 3D Model Fetch

**Endpoint:** `GET https://uat-www.tvsmotor.net/api/Headless/Get?api=/api/BlobSas/GetRes?t=rr310`

**Response:**
```json
{
  "Message": "[\"https://blob.core.windows.net/chunk1.bin\",\"https://blob.core.windows.net/chunk2.bin\",...]"
}
```

**Idempotency:** All GET endpoints are naturally idempotent. POST endpoints for config save are idempotent by user ID (upsert semantics).

---

## Data Model / Schema Changes

### Configuration State (`skuSchema.globalVariables`)

```
┌───────────────────────────────────────────────┐
│              Global Runtime State               │
├───────────────────────────────────────────────┤
│ userid: string          → Current user ID      │
│ isGuest: boolean        → Auth status          │
│ currentConfigurationNo: number → Active variant│
│ currentConfigSlot: number → Save slot index    │
│ savedConfig: object     → Loaded configs       │
│ currentRaceNo: string   → "24" (2 digits)     │
│ tempRaceNo: string      → Pending race number  │
│ isNumberScrollActive: bool → Scroll picker on  │
└───────────────────────────────────────────────┘
```

### Icon State Machine (`iconCurrentSelectionState`)

```
{
  "<iconName>": {
    "iconSelectionState": boolean,      // Currently selected?
    "defaultIconSource": string,        // Unselected image path
    "selectedIconSource": string,       // Selected image path
    "parentId": string,                 // Parent icon reference
    "iconType": string,                 // "intro-parent" | "child" | "intro-child"
    "iconLoadedState": boolean,         // Rendered in DOM?
    "icon3DActions": string[],          // Actions to dispatch on click
    "iconScreenspaceCallOuts": {},      // Active 2D callouts
    "iconWorldspaceCallOuts": []        // Active 3D callouts
  }
}
```

### Configuration Variant Schema (`ConfigurationDetails[N]`)

```
{
  "name": "ApacheRR310_DynamicKit_RacingRed_AlloyBlack",
  "id": 0,
  "currentConfiguration": boolean,
  "PartId": "N71904208F",
  "price": {
    "Base": "2 76 690",           // Display format (Indian notation)
    "ExShowroom": "2 76 690",
    "DynamicPackage": "16 600",
    "DynamicProPackage": "0",
    "AlloyWheelColor": "0",
    "SpecialEditionColor": "0",
    "total": "2 93 290"
  },
  "priceAPI": {
    "Base": "276690",             // API format (raw number as string)
    "ExShowroom": "276690",
    "DynamicPackage": "16600",
    "DynamicProPackage": "0",
    "AlloyWheelColor": "0",
    "SpecialEditionColor": "0",
    "total": "293290"
  },
  "updateButtons": { ... },       // Icon image swaps for this variant
  "changeButtonState": { ... },   // Icon selection state changes
  "updateCalloutImage": { ... },  // Feature callout overrides
  "3D_Actions": [ ... ]           // Actions to execute when loaded
}
```

### Configuration Lookup Map (`loadConfiguration`)

Maps composite keys to configuration variant numbers:

```
Format: "k{kit}bc{bodyColor}ac{alloyColor}" → configurationNo

Examples:
"k0bc0ac0" → "0"   (Dynamic Kit + Red + Black Alloy)
"k1bc1ac0" → "5"   (Dynamic Pro + Grey + Black Alloy)
"k2bc0ac0" → "8"   (Race Kit + Red + Black Alloy)
```

---

## Class & Interface Design

> Note: The codebase uses a procedural/functional pattern (no ES6 classes). Below documents the logical module boundaries.

### Module: Initialization (`avataarrenderer_preprod.js` lines 1-400)

| Function | Purpose |
|----------|---------|
| `(function() { ... })()` IIFE | Console suppression for production |
| Global variable declarations | State initialization from `skuSchema` |
| `_0xa1(u8, o)` | Read 32-bit LE integer from Uint8Array |
| `_0xb2(ab)` | Validate GLB magic number (0x46546C67) and version |
| `_0xc3Api(apiUrl)` | Fetch chunk URLs from API, parse JSON response |
| `_0xd4(paths)` | Download all chunks, concatenate, validate as GLB |
| `split-gltf-model` (A-Frame component) | Register custom component for chunked model loading |

### Module: UI Generation

| Function | Purpose |
|----------|---------|
| `populateIconSelectionState(modelSchema)` | Initialize state for all icons from schema |
| `loadInteractiveIconsForModel(model, schema, parentId, state)` | Create child icon DOM elements for a parent |
| `createImageWithinDiv(...)` | Generate icon div + img with click handler |
| `removeChildDivsIfNeeded(containerDiv)` | Clean child layer icons on parent switch |
| `handleAllIconsSelectionToggle(model, schema)` | Refresh all icon images based on selection state |
| `addScrollPicker(model, schema, parentDiv, scrollSchema)` | Create number scroll picker for race numbers |
| `loadScreenSpaceCallOutForModel(...)` | Create 2D overlay callouts |
| `loadWorldSpaceCallOutForModel(...)` | Create 3D plane callouts in scene |

### Module: 3D Action Dispatcher

| Function | Purpose |
|----------|---------|
| `handle3DActionsforIcon(model, schema, name, actions, state, playAnim, isStar, isOnload)` | **Central dispatcher** — routes action strings to handlers |
| `return3DActionSchemaForIcon(schema, iconName, actionType)` | Lookup action configuration from schema |
| `handleModelTransformation(...)` | Animate camera/model position, rotation, scale |
| `handleModifyMeshMaterial(...)` | Swap textures on 3D mesh materials |
| `handleMaterialOpacity(...)` | Change mesh transparency |
| `handleHighlightMaterial(...)` | Dim non-target meshes for feature highlight |
| `handleChangeGlobalConfigVariables(...)` | Update configuration state and load variant |
| `handlePlayAnimationSequence(...)` | Play GLTF animation clips |
| `handleDisplayCallOuts(...)` | Load/unload feature information overlays |
| `handleBlockRotate(...)` | Enable/disable model rotation |
| `handleBlockZoom(...)` | Enable/disable model zoom |

### Module: Configuration Engine

| Function | Purpose |
|----------|---------|
| `loadConfiguration(configNo, model, schema)` | **Core** — apply full variant (buttons, states, materials, price) |
| `changeButtonState(model, schema, iconName, stateObj)` | Update icon selection + disabled state |
| `updateButtons(model, schema, iconName, buttonObj)` | Swap icon images for new variant |
| `formatIndianNumber(number)` | Format price with Indian comma notation (₹ X,XX,XXX) |
| `setColorIconsStatus(...)` | Mark color icons active/inactive per variant |

### Module: API Integration

| Function | Purpose |
|----------|---------|
| `SaveUserConfigUsingApi(payload)` | POST config to TVS Headless API |
| `fetchAndStoreUserConfigurations(userId, schema)` | GET saved configs, populate `globalVariables` |
| `handleUserBuyNowClicked(...)` | Check prior orders, show price summary |
| `handleRedirectCheckOut(...)` | POST order to booking API, redirect to payment |
| `withTimestamp(apiPath)` | Append `?_t=<timestamp>` cache buster to API paths |

### Module: AR/XR

| Function | Purpose |
|----------|---------|
| `openAR()` | Launch model-viewer AR with current config GLB |
| `showQRCode()` | Generate QR code linking to current AR URL |
| `toggleButtonClick(context, isInit)` | Switch between XR (3D) and AR modes |
| `refreshLinkwithARParam(context)` | Update URL `ar=0|1` parameter |

---

## UI Changes

### Dynamic Icon Generation Flow

```
skuSchema.iconList
       │
       ▼
populateIconSelectionState() → iconCurrentSelectionState{}
       │
       ▼
For each icon where parentIcon == "":
   createImageWithinDiv() → DOM <div><img></div>
       │
       ▼
Click handler attached:
   toggleIconSelection() → update state
   handle3DActionsforIcon() → dispatch 3D actions
   loadInteractiveIconsForModel() → load children
```

### Icon Hierarchy (Parent → Child)

```
Kit (intro-parent)
├── KitDynamic (child)
└── KitDynamicPro (child)

Color (intro-parent)
├── BikeRed (child)
├── BomberGrey (child)
├── BikeBlackWheelRed (child)
└── RaceReplica (child)

RaceNumber (intro-child)
└── Number scroll picker UI

BuyNow (intro-parent)
└── Price summary → Place order flow

SaveConfiguration (intro-parent)
└── Save/Load config UI
```

### Container Div Layer System

```
Layer 0: TopRightContainer, TopLeftContainer, TopMiddleContainer, interactiveIconDivContainer
Layer 1: interactiveChildKitDivContainer, interactiveChildColorDivContainer, interactiveChildFeatureDivContainer
Layer 2: interactiveChildWheelColorDivContainer
```

When a Layer 0 icon is selected, all Layer 1+ children are cleared. When a Layer 1 icon is selected, Layer 2+ children are cleared.

---

## Error Handling & Retries

### Error Categories

| Category | Scenario | Handling |
|----------|----------|----------|
| 3D Model Load Failure | Chunk fetch fails, GLB validation fails | `model-error` event emitted; no automatic retry; user sees loading state |
| Texture Load Failure | Image 404 or CORS error | `assignTextureWithCallBack` catches error via THREE loader `onError`; material keeps previous state |
| API Call Failure | Network timeout, 4xx/5xx | `fetch().catch()` logs error; no automatic retry; user can retry manually |
| GLB Validation Failure | Corrupted chunks, wrong magic number | `_0xb2()` returns `{ ok: false }`; throws error stopping load |
| DOM Element Missing | Icon div not found | Null checks (`if (document.getElementById(x) != null)`) prevent crashes |

### Timeout Thresholds

| Operation | Timeout | Behavior |
|-----------|---------|----------|
| Fetch API calls | Browser default (~30s) | No custom timeout configured |
| Instructional overlay (3D drag hint) | 3000ms | Auto-hide via `setTimeout` |
| AR floor placement hint | 3000ms | Auto-hide via `setTimeout` |
| Place Order button debounce | 500ms | `blockClick` flag prevents double-tap |
| Alert notifications | 2000ms | Auto-hide via `setTimeout` |

### Fallback Mechanisms

| Failure | Fallback |
|---------|----------|
| `skuSchema` property undefined | Default constants (e.g., `defaultGlbMaxZoom = 1.5`) |
| AR not supported | Desktop shows QR code instead |
| `introImageSource` not provided | Falls back to `./common/avataar_loading.gif` |
| Race number empty on apply | Shows alert, keeps previous number |
| User is guest | Save/order features disabled; limited to configuration only |

---

## Security and Compliance

### Transport Security
- All API calls use HTTPS
- Cross-origin requests use `mode: "cors"`
- iframe communication restricted to `https://www.tvsmotor.com` origin

### Anti-Tampering
- DevTools detection via `debugger` timing (>120ms = devtools open)
- Right-click context menu disabled
- Keyboard shortcuts (F12, Ctrl+Shift+I) intercepted
- Console output suppressed in production

### Token Management
- Auth tokens passed via URL parameters (one-shot, no refresh)
- No client-side token storage (no cookies/localStorage for auth)
- User ID passed in API request bodies for session correlation

### Data Handling
- No PII stored client-side beyond the session
- Configuration data stored in Firebase (server-side)
- `localStorage` used only for `isSaveClicked` boolean flag

---

## RBAC (Role-Based Access Control)

| Role | Permissions | Determination |
|------|-------------|---------------|
| Guest | View 3D, configure, explore features | `isGuest = true` (no authToken or expired) |
| Authenticated User | All guest + save config, load config, place order | `isGuest = false` (valid authToken from TVS website) |
| Returning User with Order | All authenticated + "already ordered" flag | `isBuyNowClicked = true` from API response |

Access control is enforced via:
1. Client-side: Disabled buttons (`active: false`), CSS `inactive` class
2. Server-side: TVS Booking API validates user session before accepting orders

---

## Configuration Rules & Feature Flags

### Runtime Configuration (`skuSchema` Properties)

| Property | Type | Purpose | Default |
|----------|------|---------|---------|
| `glbMaxZoom` | string | Maximum zoom scale | "1.5" |
| `glbMinZoom` | string | Minimum zoom scale | "0.5" |
| `instructional3DRotateDragTimeout` | number | Instruction overlay duration (ms) | 5000 |
| `enableorDisableTapToPlace` | boolean | AR tap-to-place feature | true |
| `enableCameraMoveToPlace` | boolean | Camera auto-move in AR | false |
| `rotateAnimationDuration` | number | Camera rotation animation (ms) | 2500 |
| `defaultIdleAnimationClipName` | string | Idle animation clip name | "still" |

### Feature Flags

| Flag | Location | Effect |
|------|----------|--------|
| `debugFlag` | `index.html` inline script | Controls MixPanel analytics init (true = disabled) |
| `enableLogs` | `avataarrenderer_preprod.js` | Enables/disables console.log output |
| `isProduction` (IIFE) | `avataarrenderer_preprod.js` | Suppresses all console output on production domains |
| `ar` URL parameter | URL | `ar=1` launches directly into AR mode |

### Icon Behavior Configuration

| Schema Key | Purpose |
|------------|---------|
| `preventIconReset` | Icons that retain selection state across parent switches |
| `preventHighlightReset` | Icons that don't trigger mesh highlight reset |
| `iconCorrelationList["*"]` | Global cross-icon side effects (divs to hide, actions to unselect) |
| `containerDivs` | Layer hierarchy for icon container management |

---

## Key Algorithms / Business Rules

### 1. Configuration Variant Resolution

```javascript
// Algorithm: Composite key → Configuration number lookup
function handleChangeGlobalConfigVariables(...) {
    // Build composite key from global state
    let configString = "";
    for (var globalVariable in modelSchema.globalConfigVariables) {
        configString += globalConfigVariables[globalVariable];
    }
    // Key format: "k{kit}bc{bodyColor}ac{alloyColor}"
    // Example: "k0bc0ac0" → Kit=Dynamic, Color=Red, Alloy=Black
    
    let configurationNo = modelSchema.loadConfiguration[configString];
    // configurationNo maps to ConfigurationDetails[N]
    loadConfiguration(configurationNo, model, modelSchema);
}
```

### 2. Price Calculation

```javascript
// Algorithm: Sum all price components for active configuration
function loadConfiguration(configNo, ...) {
    let config = modelSchema.ConfigurationDetails[configNo];
    let totalPrice = parseFloat(config.priceAPI.ExShowroom)
                   + parseFloat(config.priceAPI.DynamicPackage)
                   + parseFloat(config.priceAPI.DynamicProPackage)
                   + parseFloat(config.priceAPI.AlloyWheelColor)
                   + parseFloat(config.priceAPI.SpecialEditionColor);
    
    // Display with Indian number formatting (₹ X,XX,XXX)
    document.getElementById("Total1").innerHTML = "₹ " + formatIndianNumber(totalPrice);
}

function formatIndianNumber(number) {
    const numStr = number.toString();
    const lastThree = numStr.slice(-3);
    const others = numStr.slice(0, -3);
    return others.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + lastThree;
}
```

### 3. GLB Chunk Validation

```javascript
// Algorithm: Validate reassembled binary is valid glTF 2.0
function _0xb2(arrayBuffer) {
    var u8 = new Uint8Array(arrayBuffer);
    if (u8.byteLength < 12) return { ok: false };
    
    var magic   = read32LE(u8, 0);  // Must be 0x46546C67 ("glTF")
    var version = read32LE(u8, 4);  // Must be 2
    var length  = read32LE(u8, 8);  // Must equal total byte length
    
    return { ok: (magic === 0x46546C67) && (version === 2) && (length === u8.byteLength) };
}
```

### 4. Icon Click Deduplication

```javascript
// Algorithm: Prevent duplicate action dispatch within single interaction
function handle3DActionsforIcon(..., iconName, ..., iconSelectionState, ...) {
    // Check if this exact icon+state combination was already processed
    if (iconsClicked.includes(iconName + "_" + iconSelectionState)) {
        return; // Skip duplicate
    }
    iconsClicked.push(iconName + "_" + iconSelectionState);
    // ... proceed with action dispatch
}
// iconsClicked[] is reset to [] before each new user interaction
```

### 5. Race Number Texture Application

```javascript
// Algorithm: Map scroll position → digit → texture path → material swap
function numberOnScrollEvent(scrollDiv, modelSchema) {
    // Convert scroll position to digit (0-9)
    var val = ((scrollDiv.scrollTop / scrollDiv.scrollHeight) * 10 + 0.5);
    val = val - val % 1; // Floor to integer
    
    // Update temp race number (2-character string)
    if (actionNo == "0") {
        tempRaceNo = "" + val + tempRaceNo[1]; // First digit
    } else {
        tempRaceNo = "" + tempRaceNo[0] + val; // Second digit
    }
    
    // Texture path: "./preprodAssets/Textures/visor number/No.0{digit}.png"
    // Applied to materials: "Number_WindShield_01_RHS", "Number_WindShield_02_RHS"
}
```

### 6. Material Modification Pipeline

```javascript
// Algorithm: Texture swap with proper GPU memory management
async function assignTextureWithCallBack(objs, node, texturePath, mapType, intensity) {
    // Deduplication: skip if material already being modified
    if (materialsModified.includes(node.material.name)) return;
    materialsModified.push(node.material.name);
    
    loader.load(texturePath, function(texture) {
        objs.traverse((node1) => {
            if (node1.material.name === node.material.name) {
                // 1. Dispose old texture (prevent GPU memory leak)
                if (node1.material[mapType]) {
                    node1.material[mapType].dispose();
                    node1.material[mapType] = null;
                }
                // 2. Assign new texture
                node1.material[mapType] = texture;
                node1.material[mapType].encoding = THREE.sRGBEncoding;
                // 3. Apply intensity if provided
                if (intensity) applyIntensity(node1.material, mapType, intensity);
                // 4. Clear Three.js cache and flag update
                THREE.Cache.clear();
                node1.material.needsUpdate = true;
            }
        });
    });
}
```

### 7. Container Layer Cleanup

```javascript
// Algorithm: When icon at layer N is selected, clear all layers > N
function removeChildDivsIfNeeded(containerDivToCleanUp) {
    var currentLayer = containerDivs[containerDivToCleanUp]; // e.g., 1
    
    for (var div in containerDivs) {
        if (containerDivs[div] > currentLayer) {
            // Remove all child DOM elements from higher layers
            removeAllChildImagesWithinADiv(div);
        }
    }
}
```

---

## Request/Response Lifecycle

### Full Page Load Sequence

```
1. Browser loads index.html
2. External scripts loaded in order:
   a. A-Frame 1.4.0 (from bto.tvsmotor.com CDN)
   b. Google Model Viewer (from unpkg)
   c. QR Code Generator (from jsDelivr)
   d. jQuery 1.9.1 (from Google CDN)
   e. configmaster_tvs_preprod.min.js (local) → defines skuSchema
   f. avataarrenderer_preprod.min.js (loaded dynamically via loadJS())

3. avataarrenderer initializes:
   a. Console suppression IIFE runs
   b. Global variables initialized from skuSchema
   c. A-Frame scene starts rendering
   d. 'split-gltf-model' component triggers:
      i.   _0xc3Api() fetches chunk URLs from Azure
      ii.  _0xd4() downloads all chunks in parallel
      iii. Chunks concatenated and validated (_0xb2)
      iv.  THREE.GLTFLoader.parse() processes the GLB
      v.   Model set as scene object, 'model-loaded' event fires

4. On 'model-loaded':
   a. populateIconSelectionState() initializes icon state
   b. handleOnLoad3DActions() runs startup actions
   c. loadConfiguration() applies default variant
   d. loadInteractiveIconsForModel() renders UI icons
   e. Instructional overlay shown (auto-hides after timeout)

5. User interactions dispatch via handle3DActionsforIcon()
```

### API Call Lifecycle

```
User Action
    │
    ▼
Handler Function (e.g., handleRedirectCheckOut)
    │
    ├── Construct POST_Data from schema + global state
    ├── Add timestamp cache buster: withTimestamp(apiPath)
    │
    ▼
fetch(url, { method: "POST", headers: {...}, body: JSON.stringify(data) })
    │
    ├── Success (200):
    │   ├── Parse JSON response
    │   ├── Process business logic (redirect, update state)
    │   └── Update UI accordingly
    │
    └── Failure:
        ├── catch() logs error to console
        └── No user-facing error message (silent failure)
```

---

## Validation Logic

### Input Validation

| Field | Validation | Location |
|-------|-----------|----------|
| Race Number | Must be 2 digits (00-99) | Scroll picker constrains to `minVal: 0, maxVal: 9` per digit |
| Race Number on Apply | Must not be empty string | `if (tempRaceNo != "")` check; shows alert if empty |
| Configuration Name | Max 10 characters | `<input maxlength="10">` HTML constraint |
| Auth Token | Non-null check | `if (authToken != null && authToken != "")` |
| Terms & Conditions | Must accept before order | `tncAccepted` boolean gates "Place Order" button |

### GLB Model Validation

```javascript
// Validation checks in _0xb2():
1. Byte length >= 12 (minimum header size)
2. Bytes 0-3 == 0x46546C67 (ASCII "glTF" magic number)
3. Bytes 4-7 == 2 (glTF version 2)
4. Bytes 8-11 == total byte length (integrity check)
```

### Icon Click Validation

```javascript
// Disabled icon check
if (disabledIcons.includes(iconName)) return; // Skip click on inactive icons

// Double-click prevention
if (iconsClicked.includes(iconName + "_" + state)) return;

// Place order debounce
if (blockClick) return;
blockClick = true;
setTimeout(unBlockClick, 500);
```

---

## Dependencies

### Internal Dependencies

| Module | Depends On | Guarantee |
|--------|-----------|-----------|
| avataarrenderer | skuSchema (configmaster) | Must be loaded first (script order in HTML) |
| avataarrenderer | A-Frame + Three.js | Must be loaded first; THREE global available |
| UI icons | skuSchema.iconList | Schema must define all icons before render |
| Order flow | Valid `configuredUserId` | Must have user ID from URL params |
| AR mode | Google Model Viewer | ES module loaded async |

### External Dependencies

| Dependency | Version | Upgrade Risk |
|------------|---------|--------------|
| A-Frame | 1.4.0 (pinned) | Local copy; no CDN version drift |
| Three.js | Bundled with A-Frame | Tied to A-Frame version |
| jQuery | 1.9.1 (pinned) | Google CDN hosted; widely cached |
| Google Model Viewer | Latest (unpkg) | **Risk**: unpinned version could break AR |
| QRCode Generator | 1.4.4 (pinned) | Low risk; stable library |
| Google Fonts | Dynamic | Visual-only; graceful degradation if unavailable |

---

## Trade-offs & Alternatives Considered

### Static Schema vs. Dynamic API-Driven Config

- **Current (Static):** All product data embedded in `configmaster.js`
- **Alternative:** Fetch product config from CMS API at runtime
- **Trade-off:** Static is faster (no API latency) but requires redeployment for price/variant changes. Chosen for reliability and load performance.

### Single GLB vs. Chunked Loading

- **Current (Chunked):** Model split into binary chunks, fetched via API, reassembled client-side
- **Alternative:** Single GLB file download
- **Trade-off:** Chunked adds complexity but prevents easy model extraction (IP protection) and enables CDN edge caching per chunk.

### Firebase vs. TVS Internal API for Config Storage

- **Current (Hybrid):** Migrated from Firebase to TVS Headless API (`/api/WebSiteUserConfiguration/`)
- **Legacy:** Firebase Cloud Functions still referenced in code (partially deprecated)
- **Trade-off:** TVS API provides unified auth and data residency; Firebase legacy kept for backward compatibility.

### Procedural JS vs. Component Framework (React/Vue)

- **Current (Procedural):** Single-file ~4500 line JavaScript
- **Alternative:** React with state management
- **Trade-off:** No build step means instant deployment and zero toolchain dependency. Procedural approach is harder to test and maintain but has zero build overhead.

### Price Display Format vs. API Format

- **Current:** Dual format — `price` (display: "2 76 690") and `priceAPI` (raw: "276690")
- **Alternative:** Single source with runtime formatting
- **Trade-off:** Redundant but eliminates formatting errors at order time; API always gets clean numbers.

---

## Open Questions

1. **Firebase Deprecation Status**: Several Firebase Cloud Functions are still referenced in commented code. Are they fully deprecated or do some flows still use them?

2. **Price API Integration**: The `getVehiclePriceDetails()` function is commented out. Is dynamic price fetching from `/api/Booking/LastestVehiclePricesDetails` planned for re-enablement?

3. **Model Viewer Version Pinning**: Google Model Viewer is loaded from unpkg without version pinning. Should this be pinned to prevent breaking changes?

4. **Error Recovery UX**: API failures are silently caught. Should user-facing error messages or retry mechanisms be implemented?

5. **Multi-Model Expansion**: The `skuid` URL parameter exists but is unused. Is multi-product support planned for other TVS models?

6. **Automated Testing**: No test infrastructure exists. Is there a plan to add E2E tests for critical flows (order placement, config save)?

7. **Content Security Policy**: No CSP headers are configured. Should these be added given the cross-origin CDN dependencies?

---

*Document generated: June 2026 | Version: 1.0 | For external engineering vendor onboarding*
