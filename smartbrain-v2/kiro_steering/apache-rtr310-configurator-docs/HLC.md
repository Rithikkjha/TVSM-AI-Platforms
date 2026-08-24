# High Level Code Document - TVS Apache RTR 310 3D Configurator

## 1. Application Overview

The **TVS Apache RTR 310 3D Configurator** is a Direct-to-Consumer (D2C) web application that enables users to interactively explore, customize, and order the TVS Apache RTR 310 motorcycle through an immersive 3D experience. Built with React 19 and Babylon.js, the application renders a photorealistic 3D model of the motorcycle that users can rotate, zoom, and interact with.

**Key Capabilities:**
- Real-time 3D vehicle visualization using WebGL (Babylon.js)
- Interactive color customization with PBR material texture swapping
- BTO (Built-to-Order) accessory kit selection (Dynamic / Dynamic Pro)
- Feature exploration via interactive 3D hotspots with callout overlays
- OTP-based user authentication and registration
- End-to-end order placement with payment gateway redirect
- Multi-layer security protection for 3D assets

**Target Vehicle:** TVS Apache RTR 310 (Vehicle Code: 1161)

---

## 2. Module Summary

| Module | Path | Responsibility |
|--------|------|----------------|
| Babylon 3D Engine | `src/babylon/` | Scene setup, model loading, camera, hotspots |
| Authentication | `src/pages/`, `src/services/authApi.ts` | OTP login/registration flows |
| Vehicle Configuration | `src/hooks/useVehicleConfig.ts` | Color, kit, price state management |
| Order Management | `src/components/PlaceOrder/`, `ConfirmOrder/` | Order summary, T&C, order placement |
| Callouts/Hotspots | `src/components/Callouts/`, `src/constants/hotspotConfig/` | 3D-anchored feature information |
| BTO Kit Selection | `src/components/BtoPopup/` | Dynamic/Dynamic Pro kit UI |
| Security Layer | `src/utils/devtoolChecks.tsx` | DevTools detection, asset protection |
| Model Loader | `src/utils/chunkedModelLoaderAPI.ts` | Chunked GLB download from Azure |
| UI Components | `src/components/` | Header, Footer, Colors, Toast, Loaders |

---

## 3. Dependency Overview

### Production Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `@babylonjs/core` | ^8.8.5 | 3D rendering engine |
| `@babylonjs/gui` | ^8.8.5 | Babylon GUI elements |
| `@babylonjs/loaders` | ^8.8.5 | GLB/GLTF model loading |
| `@babylonjs/inspector` | ^8.9.0 | Debug inspector (dev only usage) |
| `react` | ^19.1.0 | UI framework |
| `react-dom` | ^19.1.0 | React DOM renderer |
| `react-router-dom` | ^7.6.1 | Client-side routing (HashRouter) |
| `zustand` | ^5.0.5 | Lightweight state management |
| `axios` | ^1.9.0 | HTTP client |
| `sass` | ^1.89.2 | CSS preprocessor |

### Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `vite` | ^6.3.5 | Build tool & dev server |
| `typescript` | ~5.8.3 | Type checking |
| `eslint` | ^9.25.0 | Linting |
| `@vitejs/plugin-react` | ^4.4.1 | React HMR/JSX support |

---

## 4. Runtime Flow

**Deployment:** The application is hosted on **Azure Blob Storage (Static Website)**. The built `dist/` folder is manually uploaded to the `$web` container. No CI/CD pipeline — deployments are done via Azure Portal or Azure Storage Explorer.

```
Application Startup:
1. main.tsx → createRoot → App.tsx
2. App.tsx → HashRouter → AppRoutes
3. Home route → BabylonScene.tsx
4. Security check (DevtoolChecks) → pass/block
5. If passed: Fetch SAS tokens → Download model chunks → Combine → Load GLB
6. Initialize scene: Camera, Environment, Materials, Hotspots
7. Render UI overlays: Header, Footer, Callouts, PlaceOrder
```

```
User Authentication Flow:
1. Click "Configure Your Bike" → Navigate to /signin
2. Enter mobile number → Request OTP via API
3. Enter OTP → Verify via API → Receive token
4. Store auth state (Zustand + localStorage) → Navigate home
5. Logged-in UI: BTO Kit, Color picker, Price display, Order button
```

```
Order Placement Flow:
1. Select kits + color → Price auto-calculated from API data
2. Click price → Order Summary panel
3. Accept T&C → Click "Place Order"
4. Confirm order popup → Click "Accept"
5. POST /placeorder → Receive RedirectUrl → Open payment page
```

---

## 5. Key Services

### State Management (Zustand Stores)

| Store | File | Responsibility |
|-------|------|----------------|
| `useVehicleConfigStore` | `src/hooks/useVehicleConfig.ts` | Color, kits, pricing, partId resolution |
| `useAuthStore` | `src/hooks/useAuthStore.ts` | Login state, user data, persistence |
| `usePriceStore` | `src/hooks/useBasePrice.ts` | Base price from config |
| `useBtoStore` | `src/components/BtoPopup/useBtoStore.ts` | BTO popup visibility |
| `useInstructionPosition` | `src/hooks/useInstructionPosition.ts` | UI element positions for overlay |

### Singleton Services

| Service | File | Responsibility |
|---------|------|----------------|
| `ChunkedModelLoaderAPI` | `src/utils/chunkedModelLoaderAPI.ts` | Fetches SAS URLs, downloads chunks, combines model |
| `DevtoolChecks` | `src/utils/devtoolChecks.tsx` | Multi-method DevTools detection |
| `CalloutManager` | `src/components/Callouts/CalloutManager.ts` | Pub/sub for callout show/hide |
| `PlaceOrderManager` | `src/components/PlaceOrder/PlaceOrderManager.ts` | Pub/sub for order panel visibility |

### API Services

| Service | File | Responsibility |
|---------|------|----------------|
| `authApi` | `src/services/authApi.ts` | Login OTP, verify OTP, registration |
| `productApi` | `src/services/productApi.ts` | Place order, get vehicle prices |
| `axiosInstance` | `src/services/axiosInstance.ts` | Configured Axios with interceptors |

---

## 6. Integration Summary

### External APIs
- **TVS Motor Backend** — Authentication, vehicle pricing, order placement, policy content
- **Azure Blob Storage** — 3D model chunk files (accessed via SAS tokens)
- **Payment Gateway** — Redirect-based payment (URL received from placeorder API)

### API Environments
| Environment | Base URL |
|-------------|----------|
| Development | `https://dev-www.tvsmotor.net/api` |
| UAT | `https://uat-www.tvsmotor.net/api` |
| Production | `https://www.tvsmotor.com/api` |

---

## 7. Folder Structure Explanation

```
RTR310/
├── public/                    # Static assets served directly
│   ├── fonts/gilroy/         # Custom Gilroy font family
│   └── plugins/situ-design/  # SITU design plugin assets
├── src/
│   ├── assets/               # Images, textures, environment maps, icons
│   │   ├── env/              # Babylon environment .env file
│   │   ├── images/           # UI images, callout images, vehicle renders
│   │   └── models/textures/  # PBR textures (color maps, roughness)
│   ├── babylon/              # 3D engine code
│   │   ├── BabylonScene.tsx  # Main scene component
│   │   ├── cameraController.ts  # Camera animation & limits
│   │   └── hotspots.ts       # 3D hotspot creation & visibility
│   ├── components/           # Reusable UI components
│   ├── config/               # Environment variable accessor
│   ├── constants/            # Configuration objects (camera, price, materials)
│   ├── context/              # React Context providers (Scene, Camera)
│   ├── hooks/                # Zustand stores & custom hooks
│   ├── pages/                # Route-level page components
│   ├── route/                # Router configuration
│   ├── services/             # API layer (Axios)
│   ├── styles/               # Global SCSS & mixins
│   └── utils/                # Security, model loading utilities
├── .env.*                     # Environment configurations
├── package.json              # Dependencies & scripts
├── index.html                # HTML entry point
└── vite.config.*             # Vite build configuration
```

---

## 8. Important Entry Points

| Entry Point | Path | Description |
|-------------|------|-------------|
| HTML Entry | `index.html` | Vite HTML template |
| App Bootstrap | `src/main.tsx` | React root creation, console suppression in prod |
| Root Component | `src/App.tsx` | HashRouter, Toast, RotateOverlay |
| 3D Scene | `src/babylon/BabylonScene.tsx` | Main interactive experience |
| Sign In | `src/pages/SignIn/SignIn.tsx` | OTP login |
| Sign Up | `src/pages/SignUp/SignUp.tsx` | User registration |
| Route Config | `src/route/route.tsx` | Route definitions |

---

## 9. High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                          │
├─────────────────────────────────────────────────────────────────┤
│  React App (Vite SPA)                                           │
│  ┌───────────────┐    ┌──────────────────┐    ┌──────────────┐ │
│  │  BabylonScene  │    │  Zustand Stores   │    │  API Layer   │ │
│  │  (3D Render)   │◄──►│  (Vehicle Config) │◄──►│  (Axios)     │ │
│  └───────────────┘    └──────────────────┘    └──────┬───────┘ │
│         ▲                       ▲                     │         │
│         │                       │                     ▼         │
│  ┌──────┴───────┐    ┌─────────┴────────┐   ┌──────────────┐  │
│  │ UI Components │    │  Auth Store       │   │ TVS Motor    │  │
│  │ (Footer,      │    │  (localStorage)   │   │ Backend APIs │  │
│  │  Header, etc) │    └──────────────────┘   └──────────────┘  │
│  └──────────────┘                                     │         │
│                                                       ▼         │
│                                              ┌──────────────┐   │
│                                              │ Azure Blob   │   │
│                                              │ (3D Chunks)  │   │
│                                              └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Core Business Workflows

### Color Selection
- User selects a color → texture map applied to PBR material → price recalculated via partId lookup
- Sepang Blue requires at least one BTO kit selected (premium color constraint)

### BTO Kit Configuration
- Two kits available: Dynamic (₹18,000) and Dynamic Pro (₹28,000)
- Selecting a kit updates hotspot visibility, enables premium color, recalculates price
- Part ID is determined by `color × kit combination` matrix

### Price Calculation
- Base price fetched from API filtered by Delhi state
- Part ID resolved from color + kit selection → matched against product list
- Total displayed in header; order summary shows breakdown

### Security & Asset Protection
- DevTools detection blocks page access with overlay
- 3D model loaded via temporary SAS-token URLs (expire after use)
- Model chunks combined in memory, blob URLs revoked immediately after GPU load
- Console logs suppressed in production build

---

*Document generated for vendor onboarding purposes. No secrets, credentials, or sensitive business logic exposed.*
