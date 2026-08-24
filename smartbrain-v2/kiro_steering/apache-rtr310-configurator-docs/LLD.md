# Low Level Design (LLD) - TVS Apache RTR 310 3D Configurator

## 1. Detailed Module Breakdown

### 1.1 Babylon 3D Engine Module (`src/babylon/`)

| File | Responsibility |
|------|----------------|
| `BabylonScene.tsx` | Main React component; initializes Engine, Scene, Camera, loads model, renders overlays |
| `cameraController.ts` | Camera animation (eased transitions), limits, default positions |
| `hotspots.ts` | Creates clickable 3D hotspot planes, manages visibility per kit/login state |

### 1.2 State Management Module (`src/hooks/`)

| File | Store Name | State Shape |
|------|-----------|-------------|
| `useAuthStore.ts` | `useAuthStore` | `{isLoggedIn, user, login(), logout()}` |
| `useVehicleConfig.ts` | `useVehicleConfigStore` | `{color, selectedKits, basePrice, totalPrice, products[], ...actions}` |
| `useBasePrice.ts` | `usePriceStore` | `{basePrice, setBasePrice()}` |
| `useInstructionPosition.ts` | `useInstructionPosition` | `{hotspotPos, colorPos, configurePos, btoKitPos, pricePos}` |
| `useTotalPrice.ts` | `useTotalPrice()` hook | Derived: basePrice + kitPrices sum |

### 1.3 Services Module (`src/services/`)

| File | Exports | Protocol |
|------|---------|----------|
| `axiosInstance.ts` | Configured Axios with interceptors | HTTPS + Bearer token |
| `authApi.ts` | `requestOtpApi`, `verifyOtpApi`, `registerUserApi`, `registerUserVerifyOtpApi` | POST |
| `productApi.ts` | `placeOrderApi`, `getProductListApi` | POST/GET |

### 1.4 Constants/Configuration Module (`src/constants/`)

| File | Exports | Purpose |
|------|---------|---------|
| `shared.ts` | `VehicleColor`, `KitTypeEnum`, `textureMap`, color codes | Shared enums & mappings |
| `priceConfig.ts` | `priceConfig`, `vehicleConfig` | Pricing rules, part ID matrix |
| `cameraConfig.ts` | `CAMERA_VALUES` | Camera angles, radius, limits |
| `helper.ts` | Utility functions | Material changes, mesh operations, validation |
| `materialNames.ts` | `MaterialName` | PBR material name constants |
| `initalSceneConfig.ts` | `meshMap`, `hideMeshesOnLoad` | Initial scene mesh config |
| `highlightConfig.ts` | `GhostHighlightMeshes` | Mesh name arrays per feature |
| `hotspotConfig/hotspotConfig.ts` | `getHotspotMeshes()` | Hotspot positions & click handlers |
| `hotspotConfig/hotspotIds.ts` | `HotspotId` enum | All hotspot identifiers |
| `hotspotConfig/hotspotVisibilityConfig.ts` | Visibility rules per user state + kit | Conditional hotspot display |

### 1.5 Components Module (`src/components/`)

| Component | File | UI Responsibility |
|-----------|------|-------------------|
| Footer | `Footer/Footer.tsx` | Bottom navigation: Color, Hotspot, BTO Kit, Reset |
| Header | `header/Header.tsx` | Price display, expand button |
| Colors | `Colors/Colors.tsx` | Color swatches (logged-out) / Bike previews (logged-in) |
| BtoPopup | `BtoPopup/BtoPopup.tsx` | Kit selection overlay |
| Callouts | `Callouts/Callouts.tsx` | Feature information panel |
| PlaceOrder | `PlaceOrder/PlaceOrder.tsx` | Order summary with price breakdown |
| ConfirmOrder | `ConfirmOrder/ConfirmOrder.tsx` | Order confirmation modal |
| PolicyPopup | `PolicyPopup/PolicyPopup.tsx` | T&C / Privacy Policy HTML display |
| Toast | `Toast/ToastManager.tsx` | Global toast notification system |
| InstructionOverlay | `InstructionOverlay/` | First-time user guidance |
| RotateOverlay | `RotateOverlay/` | Portrait mode rotate prompt |
| Loader | `Loader.tsx` | Loading spinner/animation |

---

## 2. Class/Service Responsibilities

### 2.1 ChunkedModelLoaderAPI (Singleton)

```typescript
class ChunkedModelLoaderAPI {
  private static instance: ChunkedModelLoaderAPI;
  
  static getInstance(): ChunkedModelLoaderAPI;
  
  // Fetch SAS-token URLs from TVS API
  private fetchChunkUrls(): Promise<string[]>;
  
  // Download a single chunk with retry (3 attempts, exponential backoff)
  private fetchChunk(url: string, index: number, retries: number): Promise<{index, buffer}>;
  
  // Concatenate ArrayBuffers maintaining sequence order
  private combineChunks(chunks: ArrayBuffer[]): ArrayBuffer;
  
  // Public: Full load pipeline (fetch URLs → download → combine)
  loadChunkedModel(): Promise<{buffer: ArrayBuffer, fileName: string} | null>;
}
```

### 2.2 DevtoolChecks (Singleton)

```typescript
class DevtoolChecks {
  private static instance: DevtoolChecks;
  private isBlocked: boolean;
  private devToolsOpen: boolean;
  private callbacks: Set<SecurityCallback>;
  
  // Initial security validation
  runSecurityCheck(): Promise<boolean>;
  
  // Detection methods (7 total)
  private setupConsoleDetection(): void;       // Image ID getter
  private setupWindowSizeDetection(): void;    // outer-inner threshold
  private setupPerformanceDetection(): void;   // debugger timing
  private setupDebuggerDetection(): void;      // debugger + eval
  private setupToStringDetection(): void;      // Element ID getter
  private blockKeyboardShortcuts(): void;      // F12, Ctrl+Shift+I/J/C
  private blockContextMenu(): void;            // Right-click
  
  // Response actions
  private onDevToolsDetected(method: string): void;
  private createBlockingOverlay(): void;
  private clearSensitiveData(): void;
  private setupDataProtection(): void;         // Override fetch/XHR
  
  // Public API
  onBlock(callback: () => void): void;
  isAccessBlocked(): boolean;
}
```

### 2.3 CalloutManager (Singleton)

```typescript
class CalloutManager {
  private listener: CalloutListener | null;
  private currentIndex: number | null;
  
  subscribe(listener: (index: number | null) => void): void;
  unsubscribe(): void;
  showCallout(index: number): void;   // Notify listener, store index
  hideCallout(): void;                // Reset, apply default mesh map
  getCurrentIndex(): number | null;
}
```

### 2.4 PlaceOrderManager (Singleton)

```typescript
class PlaceOrderManager {
  private listener: PlaceOrderListener | null;
  private isVisible: boolean;
  
  subscribe(listener: (isVisible: boolean) => void): void;
  unsubscribe(): void;
  show(): void;
  hide(): void;
  toggle(): void;
  getVisibility(): boolean;
}
```

---

## 3. API Flow Details

### 3.1 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  requestOtpApi({mobileNumber})                                   │
│  POST → {LOGIN_URL}/UserLogin/Loginv1                            │
│  Response: {StatusCode: 200} OR {StatusCode: 404 (new user)}     │
├─────────────────────────────────────────────────────────────────┤
│  verifyOtpApi({mobileNumber, otp})                               │
│  POST → {LOGIN_URL}/UserLogin/VerifyLoginOtp                     │
│  Response: {Data: [{Email, FullName, Token, UserId}]}            │
├─────────────────────────────────────────────────────────────────┤
│  registerUserApi({fullName, email, mobileNumber})                 │
│  POST → {LOGIN_URL}/RegisterUser/CreateUser                      │
│  Response: Success indicator                                     │
├─────────────────────────────────────────────────────────────────┤
│  registerUserVerifyOtpApi({mobileNumber, otp})                   │
│  POST → {LOGIN_URL}/RegisterUser/VerifyOTP                       │
│  Response: Success indicator                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Vehicle Pricing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  getProductListApi()                                             │
│  GET → {API_BASE_URL}/Booking/LastestVehiclePricesDetails        │
│         ?vehicleCode=1161                                        │
│  Response: {data: [{State, PartId, Price, ...}]}                 │
│  Client filter: item.State === "Delhi"                           │
│  Cached in: useVehicleConfigStore.products[]                     │
└─────────────────────────────────────────────────────────────────┘

Price Resolution:
1. Get partId from vehicleConfig.partIds[color][kitKey]
2. Find product where product.PartId === partId
3. Set basePrice = Number(product.Price)
4. totalPrice = basePrice (API price is final)
```

### 3.3 Order Placement Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  placeOrderApi(user, vehicleConfig, summary)                     │
│  POST → {API_BASE_URL}/placeorder                                │
│                                                                  │
│  Payload Structure:                                              │
│  {                                                               │
│    OrderVehicle: 1,                                              │
│    Token: user.token,                                            │
│    UserId: user.userId,                                          │
│    Name: user.name,                                              │
│    Phone: user.mobileNumber,                                     │
│    Email: user.email,                                            │
│    VehicleName: "RTR-310",                                       │
│    VariantCode: 1161,                                            │
│    PartId: vehicleConfig.partId,                                 │
│    Price: { ExShowroom, DynamicPackage?, DynamicProPackage?,      │
│             AdditonalColorPrice },                                │
│    BTO: { Status: false },                                       │
│    PreBooking: { PaymentStatus, Phone, ... }                     │
│  }                                                               │
│                                                                  │
│  Response: { RedirectUrl: "https://payment-gateway/..." }        │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Model Loading Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Fetch Chunk URLs                                        │
│  GET → {API_BASE_URL}/Headless/Get                               │
│         ?api=/api/BlobSas/GetRes?t=rtr310&_t={timestamp}         │
│  Response: { Message: "[url1, url2, ...]", Success: true }       │
├─────────────────────────────────────────────────────────────────┤
│  Step 2: Download Chunks (batches of 10)                         │
│  GET → Each SAS URL (with cache-busting _t param)                │
│  Headers: Cache-Control: no-cache, no-store                      │
│  Response: ArrayBuffer (binary chunk data)                       │
│  Retry: 3 attempts with 500ms * attempt delay                   │
├─────────────────────────────────────────────────────────────────┤
│  Step 3: Combine Chunks                                          │
│  Sort by index → Concatenate into single Uint8Array              │
│  Return: { buffer: ArrayBuffer, fileName: "model.glb" }         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Internal Component Interactions

### 4.1 Component Communication Map

```
BabylonScene
├── provides: SceneContext, CameraContext
├── renders: Header, Footer, Callouts, PlaceOrder, InstructionOverlay
│
├── Header
│   ├── reads: useAuthStore.isLoggedIn
│   ├── reads: useVehicleConfigStore.totalPrice
│   └── calls: placeOrderManager.toggle()
│
├── Footer
│   ├── reads: useAuthStore.isLoggedIn
│   ├── reads: useBtoStore.isPopupVisible
│   ├── reads: useVehicleConfigStore.selectedKits
│   ├── calls: showHotspots() / hideHotspots()
│   ├── calls: useBtoStore.showPopup()
│   ├── calls: changeVehicleColor()
│   └── renders: Colors, BtoPopup (conditional)
│
├── Callouts
│   ├── subscribes: calloutManager
│   ├── reads: CalloutConfig[index]
│   └── calls: calloutManager.hideCallout()
│
└── PlaceOrder
    ├── subscribes: placeOrderManager
    ├── reads: useVehicleConfigStore (price, kits, color)
    ├── renders: PolicyPopup, ConfirmOrder
    └── calls: buildOrderSummary()
```

### 4.2 State Flow Between Stores

```
useVehicleConfigStore ────────────────────────────────────────
  │                                                           │
  │ color change ──► fetchBasePrice() ──► recalculatePrice()  │
  │ kit change   ──► fetchBasePrice() ──► recalculatePrice()  │
  │                                                           │
  │ getPartId(): color × kitKey → vehicleConfig.partIds       │
  │ products[]: cached API response, filtered by "Delhi"      │
  │                                                           │
  └───────────────────────────────────────────────────────────

useAuthStore (persisted to localStorage)
  │
  │ login(user) ──► isLoggedIn: true, user: {...}
  │ logout()    ──► isLoggedIn: false, user: null
  │
  │ Token used by: axiosInstance interceptor
  └───────────────────────────────────────────────
```

---

## 5. Database Schema Usage

### 5.1 Client-Side Data Models

```typescript
// User model (from API response, stored in auth store)
interface User {
  mobileNumber: string;
  email: string;
  name: string;
  token: string;
  userId: number;
}

// Vehicle configuration state
interface VehicleConfigState {
  color: VehicleColor;          // enum: fieryRed | furyYellow | arsenalBlack | sepangBlue
  selectedKits: KitTypeEnum[];  // enum values: dynamic | dynamicPro
  basePrice: number;            // From API based on partId
  totalPrice: number;           // Currently = basePrice
  products: any[];              // Cached API product list
}

// Part ID resolution matrix (Color × Kit → SKU)
// Example: arsenalBlack + dynamic → "N71903502D"
type PartIdMatrix = Record<VehicleColor, Record<KitKey, string>>;
// KitKey: "none" | "dynamic" | "dynamicPro" | "dynamic_dynamicPro"
```

### 5.2 API Data Structures

```typescript
// Product price response item (from /Booking/LastestVehiclePricesDetails)
interface ProductItem {
  State: string;      // e.g., "Delhi"
  PartId: string;     // e.g., "N71903502D"
  Price: string;      // e.g., "236890"
  // Additional fields from API
}

// Order payload (POST /placeorder)
interface OrderPayload {
  OrderVehicle: 1;
  OrderAccessories: 1;
  Token: string;
  SessionId: string;
  UserId: number;
  Name: string;
  Phone: string;
  Email: string;
  VehicleName: "RTR-310";
  VariantCode: 1161;
  PartId: string;
  Price: {
    ExShowroom: number;
    AdditonalColorPrice: number;
    DynamicPackage?: number;
    DynamicProPackage?: number;
  };
  BTO: { Status: boolean };
  PreBooking: { PaymentStatus: string; Phone: string; ... };
}
```

---

## 6. Request/Response Lifecycle

### 6.1 Axios Interceptor Pipeline

```
Request:
  Client code → axiosInstance.post/get()
    → Request Interceptor:
        - Read token from localStorage
        - Attach Authorization: Bearer {token}
    → Network Request (HTTPS)

Response:
  Network Response
    → Response Interceptor:
        - Check status === 200 || 201 → pass through
        - Status 401 → console.warn("Unauthorized")
        - Other status → reject with {message, statusCode, data}
    → Client receives response.data
    
Error:
  Network error or non-200
    → Response error handler
        - 401: Log warning
        - Other: Reject promise
    → Client catch block → show error UI
```

### 6.2 Model Loading Lifecycle

```
1. securityCheckPassed = true
2. modelLoadingRef.current = false (guard against duplicate)
3. modelLoadingRef.current = true (lock)
4. chunkedModelLoader.loadChunkedModel()
   4a. GET /Headless/Get → parse JSON Message → string[] URLs
   4b. Batch download (10 parallel) with retries
   4c. Sort by index → combine Uint8Array
5. Create File object → URL.createObjectURL()
6. SceneLoader.ImportMesh(fileUrl, scene, callback)
7. Callback:
   - URL.revokeObjectURL(fileUrl) ← immediate cleanup
   - Scale meshes (10, 10, -10)
   - Initialize camera
   - Apply all 4 color textures (pre-cache)
   - Create hotspots
   - Initialize mesh map
   - Apply roughness map
   - Create shadow plane
   - Hide unwanted meshes
   - setLoading(false)
```

---

## 7. Validation Logic

### 7.1 Form Validation

| Field | Rule | Implementation |
|-------|------|----------------|
| Mobile Number | Exactly 10 digits | `/^[0-9]{10}$/` |
| Email | Standard email format | `/^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/` |
| OTP | Non-empty | `if (!otp)` check |
| Full Name | Non-empty | `if (!fullName)` check |
| T&C Checkbox | Must be checked for order | `disabled={!isChecked}` |

### 7.2 Business Rule Validation

| Rule | Logic |
|------|-------|
| Sepang Blue requires kit | `isSepangBlueDisabled = selectedKits.length === 0` |
| Hotspots require kit (logged in) | `disabled={!isKitSelected}` → toast message |
| No kits → reset to default color | `if (selectedKits.length === 0) setColor(furyYellow)` |
| Order requires auth | Route guard via `isLoggedIn` state |

---

## 8. Error Handling

### 8.1 API Error Handling Pattern

```typescript
// Standard pattern used across all API calls
try {
  const response = await apiCall(payload);
  // Handle success
} catch (error) {
  console.error('Operation failed:', error);
  // Show user-facing error (inline message or toast)
  throw error; // Re-throw for caller handling
}
```

### 8.2 Error Handling by Layer

| Layer | Strategy | User Feedback |
|-------|----------|---------------|
| API calls | try/catch + console.error | Inline error text / Toast |
| Model loading | Retry 3x per chunk, 500ms backoff | Loader stays visible |
| Auth | 401 logged, token invalidation | Console warning |
| Form validation | State-based error messages | Red error text below input |
| Security | Block page with overlay | Full-screen overlay message |
| Rendering | Babylon.js internal recovery | No explicit handling |

### 8.3 Toast Notification System

```typescript
// Global toast (singleton pattern via module-level variable)
let showExternalToast: (msg: string, duration?: number) => void;

// Usage anywhere in app:
import { showToast } from '../components/Toast/ToastManager';
showToast('Please choose a kit to proceed.');
```

---

## 9. Key Algorithms/Business Rules

### 9.1 Part ID Resolution Algorithm

```typescript
// Determines the SKU part ID based on color + kit selection
function getPartId(): string {
  const { color, selectedKits } = get();
  
  // Build kit key from sorted selection
  const sorted = [...selectedKits].sort();
  const key = sorted.length === 0 ? 'none' : sorted.join('_');
  // Possible keys: "none", "dynamic", "dynamicPro", "dynamic_dynamicPro"
  
  return vehicleConfig.partIds[color][key];
  // Returns: e.g., "N71903502D" for arsenalBlack + dynamic
}
```

### 9.2 Price Calculation Algorithm

```typescript
// Price fetched from API based on part ID
function fetchBasePrice(): void {
  const partId = getPartId();
  const product = products.find(item => item.PartId === partId);
  const price = Number(product.Price);
  set({ basePrice: price });
  recalculatePrice(); // totalPrice = basePrice
}
```

### 9.3 Ghost Effect Algorithm (3D Highlight)

```typescript
// Makes all meshes transparent except the highlighted ones
function ghostEffect(scene: Scene, meshNamesToExclude: string[]): void {
  const dimMaterial = new PBRMaterial("dimmed_pbr", scene);
  dimMaterial.albedoColor = new Color3(0, 0, 0);
  dimMaterial.alpha = 0.02;
  dimMaterial.transparencyMode = PBRMaterial.PBRMATERIAL_ALPHABLEND;
  
  const excludeSet = new Set([...ghostEffectExcludedMeshes, ...meshNamesToExclude]);
  
  scene.meshes.forEach(mesh => {
    if (!excludeSet.has(mesh.name)) {
      mesh.material = dimMaterial;  // Apply ghost material
    }
    // Excluded meshes keep their original materials (highlighted)
  });
}
```

### 9.4 Camera Animation Algorithm

```typescript
// Smooth camera transition with easing
function rotateCamera({ camera, alpha, beta, radius, target }): Promise<void> {
  // 1. Normalize alpha to avoid >180° rotation
  const normalizedAlpha = normalizeAlpha(camera.alpha, alpha);
  
  // 2. Create animations for each property (60fps, 100 frames)
  // 3. Apply QuadraticEase (EASEINOUT) to each animation
  // 4. Group animations and play
  // 5. Resolve promise on animation end
}
```

### 9.5 Hotspot Visibility Algorithm

```typescript
function showHotspots(): void {
  const { selectedKits } = useVehicleConfigStore.getState();
  const userState = isLoggedIn ? 'loggedIn' : 'loggedOut';
  
  const config = hotspotVisibilityConfig[userState];
  const visibleHotspots = new Set<string>();
  
  // Add base hotspots for current state
  (config.all ?? []).forEach(id => visibleHotspots.add(id));
  
  // Add kit-specific hotspots
  selectedKits.forEach(kit => {
    const kitHotspots = config[kit] || [];
    kitHotspots.forEach(id => visibleHotspots.add(id));
  });
  
  // Apply visibility to all hotspot planes
  hotspotPlaneMap.forEach((plane, name) => {
    plane.setEnabled(visibleHotspots.has(name));
  });
}
```

---

## 10. Configuration Handling

### 10.1 Environment Variables

```
File: src/config/env.tsx
─────────────────────
export const ENV = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  LOGIN_URL: import.meta.env.VITE_LOGIN_URL,
  BLOB_SAS_ENDPOINT: import.meta.env.VITE_BLOB_SAS_ENDPOINT,
};
```

### 10.2 Environment Files

| File | VITE_ENV | API_BASE_URL | LOGIN_URL |
|------|----------|--------------|-----------|
| `.env` | local | dev-www.tvsmotor.net/api | dev-tvsconnectapi.tvsmotor.net/corspolicyenable/api |
| `.env.development` | dev | dev-www.tvsmotor.net/api | dev-tvsconnectapi.tvsmotor.net/api |
| `.env.uat` | uat | uat-www.tvsmotor.net/api | uat-tvsconnectapi.tvsmotor.net/api |
| `.env.production` | production | www.tvsmotor.com/api | tvsconnectapi.tvsmotor.com/api |

### 10.3 Vehicle Configuration Constants

```typescript
// priceConfig.ts
priceConfig = {
  basePrice: 236890,              // Fallback price
  kitPrices: { dynamic: 18000, dynamicPro: 28000 },
  colorPrices: { furyYellow: 0, arsenalBlack: 0, sepangBlue: 10000, fieryRed: 0 },
  AdditonalColorPrice: 10000      // Sepang Blue surcharge
};

// Camera configuration
CAMERA_VALUES = {
  defaultAlphaValue: 1.5,
  defaultBetaValue: 1.65,
  defaultDesktopRadiusValue: 36,
  desktopLowerRadiusLimit: 25,
  desktopUpperRadiusLimit: 50,
  defaultTargetPositionY: 7.5,
  defaultFov: 0.8,
  ...
};
```

---

## 11. File-Level Dependency Graph

```
main.tsx
└── App.tsx
    ├── route/route.tsx
    │   ├── babylon/BabylonScene.tsx
    │   │   ├── utils/chunkedModelLoaderAPI.ts
    │   │   ├── utils/devtoolChecks.tsx
    │   │   ├── babylon/cameraController.ts
    │   │   ├── babylon/hotspots.ts
    │   │   ├── constants/helper.ts
    │   │   ├── constants/hotspotConfig/hotspotConfig.ts
    │   │   ├── components/Header/Header.tsx
    │   │   ├── components/Footer/Footer.tsx
    │   │   │   ├── components/Colors/Colors.tsx
    │   │   │   └── components/BtoPopup/BtoPopup.tsx
    │   │   ├── components/Callouts/Callouts.tsx
    │   │   ├── components/PlaceOrder/PlaceOrder.tsx
    │   │   │   ├── components/ConfirmOrder/ConfirmOrder.tsx
    │   │   │   └── components/PolicyPopup/PolicyPopup.tsx
    │   │   └── components/InstructionOverlay/InstructionOverlay.tsx
    │   ├── pages/SignIn/SignIn.tsx
    │   │   └── services/authApi.ts → axiosInstance.ts
    │   └── pages/SignUp/SignUp.tsx
    │       └── services/authApi.ts
    └── components/Toast/ToastManager.tsx
```

---

*Document generated for new engineering vendor onboarding. No secrets or credentials exposed.*
