# High Level Design (HLD) - TVS Apache RTR 310 3D Configurator

## 1. System Architecture

### Architecture Style
Single Page Application (SPA) with client-side rendering, communicating with external REST APIs and Azure Blob Storage for 3D assets.

### Architecture Diagram Description

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              CLIENT TIER                                   │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                     React 19 SPA (Vite Build)                        │ │
│  │                                                                      │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────┐ │ │
│  │  │  Routing      │  │  State Mgmt  │  │  3D Engine (Babylon.js)   │ │ │
│  │  │  (HashRouter) │  │  (Zustand)   │  │  - Scene Management       │ │ │
│  │  │               │  │  - Auth      │  │  - Camera Control         │ │ │
│  │  │  Routes:      │  │  - Vehicle   │  │  - PBR Materials          │ │ │
│  │  │  / (3D Scene) │  │    Config    │  │  - Hotspot System         │ │ │
│  │  │  /signin      │  │  - Price     │  │  - Rendering Pipeline     │ │ │
│  │  │  /signup      │  │  - UI State  │  │                           │ │ │
│  │  └──────────────┘  └──────────────┘  └───────────────────────────┘ │ │
│  │                                                                      │ │
│  │  ┌──────────────────────────────────────────────────────────────┐   │ │
│  │  │                      API Layer (Axios)                        │   │ │
│  │  │  - Auth APIs (Login/Register)                                 │   │ │
│  │  │  - Product APIs (Pricing/Orders)                              │   │ │
│  │  │  - Content APIs (Model Chunks/Policy)                         │   │ │
│  │  └──────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
          │                          │                         │
          ▼                          ▼                         ▼
┌──────────────────┐   ┌──────────────────────┐   ┌────────────────────┐
│  TVS Connect API  │   │  TVS Motor Web API   │   │  Azure Blob Storage │
│  (Authentication) │   │  (Business Logic)    │   │  (3D Model Chunks)  │
│                   │   │                      │   │                     │
│  - Login/OTP      │   │  - Vehicle Pricing   │   │  - GLB file chunks  │
│  - Registration   │   │  - Place Order       │   │  - SAS Token access │
│  - Token Mgmt     │   │  - Policy Content    │   │                     │
│                   │   │  - SAS Token Gen      │   │                     │
└──────────────────┘   └──────────────────────┘   └────────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Payment Gateway  │
                       │  (Redirect-based) │
                       └──────────────────┘
```

---

## 2. Major Components/Services

### 2.1 Frontend Application (Client)

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| UI Framework | React 19 | Component rendering, state, lifecycle |
| 3D Rendering | Babylon.js 8.x | WebGL scene, camera, materials, meshes |
| State Management | Zustand 5 | Global state stores with persistence |
| Routing | React Router DOM 7 | Hash-based client navigation |
| HTTP Client | Axios 1.x | API communication with interceptors |
| Build System | Vite 6 | Dev server, HMR, production bundling |
| Styling | SCSS/Sass | Component-scoped styles |

### 2.2 Backend Services (External)

| Service | Owner | Responsibility |
|---------|-------|----------------|
| TVS Connect API | TVS Motor | User authentication (OTP-based) |
| TVS Motor Web API | TVS Motor | Vehicle pricing, order management, content |
| Azure Blob Storage | TVS Motor (Azure) | Secure 3D model asset storage |
| Payment Gateway | Third-party | Payment processing (redirect-based) |

---

## 3. Deployment Architecture

### Environments

| Environment | Frontend Hosting | API Base URL | Auth Base URL |
|-------------|-----------------|--------------|---------------|
| Development | Local (Vite dev) | `dev-www.tvsmotor.net/api` | `dev-tvsconnectapi.tvsmotor.net/api` |
| UAT | Static hosting | `uat-www.tvsmotor.net/api` | `uat-tvsconnectapi.tvsmotor.net/api` |
| Production | Static hosting | `www.tvsmotor.com/api` | `tvsconnectapi.tvsmotor.com/api` |

### Build & Deployment Flow

```
Developer Machine                                    Azure Blob Storage
┌──────────────┐                                   ┌──────────────────────┐
│  Source Code  │──► npm run build ──► dist/ ──────►│  $web Container       │
│  (TypeScript) │       (local)         │           │  (Static Website)     │
└──────────────┘                        │           │                       │
                                        │  Manual   │  Served via:          │
                                        │  Upload   │  https://<account>    │
                                        └──────────►│  .z13.web.core        │
                                                    │  .windows.net         │
                                                    └──────────────────────┘
```

**Deployment is manual:**
1. Run `npm run build` locally to produce the `dist/` folder
2. Upload the contents of `dist/` to the Azure Blob Storage `$web` container
3. No CI/CD pipeline — files are manually uploaded via Azure Portal or Azure Storage Explorer

### Infrastructure Topology

```
┌─────────────────────────────────────────────────────────┐
│           Azure Blob Storage (Static Website)            │
│              $web container serves SPA                    │
│         Index document: index.html                       │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     User's Browser                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │  React SPA + Babylon.js WebGL                      │  │
│  │  - Renders 3D model on GPU                         │  │
│  │  - All logic runs client-side                      │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────┬──────────────────┬────────────────────────┘
              │                  │
    REST APIs │                  │ Blob Download (SAS)
              ▼                  ▼
┌──────────────────┐   ┌──────────────────────┐
│  TVS Backend     │   │  Azure Blob Storage   │
│  (API Gateway)   │   │  (Separate Container) │
│  ┌────────────┐  │   │                       │
│  │ Auth Service│  │   │  Model chunks (.glb)  │
│  │ Order Svc  │  │   │  10+ chunks per model │
│  │ Pricing Svc│  │   └──────────────────────┘
│  │ Content Svc│  │
│  │ SAS Gen Svc│  │
│  └────────────┘  │
└──────────────────┘
```

---

## 4. Database Interactions

This is a **frontend-only** application. There is no direct database access from the client. All data persistence is handled by:

- **Backend APIs** (server-side database managed by TVS Motor)
- **localStorage** (client-side persistence for auth state via Zustand `persist` middleware)
- **sessionStorage** (cleared on security detection)

### Client-Side Data Storage

| Storage | Key | Content |
|---------|-----|---------|
| localStorage | `auth-storage` | User login state, token, user details |
| In-memory (Zustand) | Vehicle config | Color, kits, pricing, products cache |
| GPU Memory | 3D Model | Loaded GLB model data |

---

## 5. API Integrations

### 5.1 Authentication APIs (TVS Connect)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/UserLogin/Loginv1` | POST | Request OTP for registered user |
| `/UserLogin/VerifyLoginOtp` | POST | Verify OTP and get auth token |
| `/RegisterUser/CreateUser` | POST | Register new user |
| `/RegisterUser/VerifyOTP` | POST | Verify registration OTP |

### 5.2 Business APIs (TVS Motor Web)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/Booking/LastestVehiclePricesDetails` | GET | Get current vehicle prices by state |
| `/placeorder` | POST | Submit vehicle order |
| `/Booking/PageContent` | GET | Fetch T&C and Privacy Policy HTML |

### 5.3 Asset APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/Headless/Get` | GET | Get signed blob SAS URLs for model chunks |
| `/BlobSas/GetRes` | GET | Generate SAS tokens for blob access |

---

## 6. Authentication/Authorization Flow

### Authentication Method: OTP-Based (Passwordless)

```
┌────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│  User  │     │  Client  │     │ TVS Connect  │     │  SMS/OTP │
│        │     │  (React) │     │    API       │     │  Service │
└───┬────┘     └────┬─────┘     └──────┬───────┘     └────┬─────┘
    │               │                   │                   │
    │ Enter Mobile  │                   │                   │
    ├──────────────►│                   │                   │
    │               │ POST /Loginv1     │                   │
    │               ├──────────────────►│                   │
    │               │                   │  Dispatch OTP     │
    │               │                   ├──────────────────►│
    │               │    200 OK         │                   │  SMS
    │               │◄──────────────────┤                   ├────►
    │               │                   │                   │
    │ Enter OTP     │                   │                   │
    ├──────────────►│                   │                   │
    │               │ POST /VerifyOTP   │                   │
    │               ├──────────────────►│                   │
    │               │  Token + UserData │                   │
    │               │◄──────────────────┤                   │
    │               │                   │                   │
    │               │ Store in Zustand  │                   │
    │               │ + localStorage    │                   │
    │  Logged In    │                   │                   │
    │◄──────────────┤                   │                   │
```

### Token Management
- Token received on successful OTP verification
- Stored in Zustand auth store (persisted to `localStorage`)
- Attached to requests via Axios request interceptor (`Authorization: Bearer {token}`)
- 401 responses logged (no auto-redirect currently)

---

## 7. External Systems

| System | Type | Protocol | Purpose |
|--------|------|----------|---------|
| TVS Connect API | REST API | HTTPS | Authentication |
| TVS Motor Web API | REST API | HTTPS | Business operations |
| Azure Blob Storage | Cloud Storage | HTTPS (SAS) | 3D model hosting |
| Payment Gateway | External | HTTPS (Redirect) | Payment processing |
| Vite Dev Proxy | Dev Middleware | HTTP | CORS bypass (dev only) |

---

## 8. Infrastructure Dependencies

| Dependency | Purpose | Impact if Unavailable |
|-----------|---------|----------------------|
| Azure Blob Storage | 3D model chunks | App shows loader indefinitely |
| TVS Connect API | Authentication | Users cannot log in |
| TVS Motor Web API | Pricing & Orders | No price display, no orders |
| Azure Blob Static Website | Serve SPA (manual upload) | App not accessible |
| User's GPU | WebGL rendering | 3D scene won't render |
| Modern Browser | WebGL2 support | App not functional |

---

## 9. High-Level Sequence Flows

### 9.1 Application Load Sequence

```
Browser              App                  DevtoolChecks        Model Loader         Azure
  │                   │                       │                    │                  │
  │── Load SPA ──────►│                       │                    │                  │
  │                   │── runSecurityCheck() ─►│                    │                  │
  │                   │                       │── checks ──────►   │                  │
  │                   │◄── isSecure: true ────┤                    │                  │
  │                   │── loadChunkedModel() ─────────────────────►│                  │
  │                   │                                            │── GET /Headless ─►│
  │                   │                                            │◄── SAS URLs ─────┤
  │                   │                                            │── GET chunks ────►│
  │                   │                                            │◄── chunk data ───┤
  │                   │◄── combined ArrayBuffer ──────────────────┤                  │
  │                   │── SceneLoader.ImportMesh() ──►            │                  │
  │◄── 3D Scene ─────┤                                            │                  │
```

### 9.2 Order Placement Sequence

```
User         PlaceOrder        ConfirmOrder       ProductApi        Backend        Payment
  │               │                 │                 │               │               │
  │─ View Summary─►│                 │                 │               │               │
  │               │─ Accept T&C ───►│                 │               │               │
  │               │                 │─ placeOrderApi ─►│               │               │
  │               │                 │                 │─ POST /placeorder──►│          │
  │               │                 │                 │◄── RedirectUrl ─────┤          │
  │               │                 │◄── url ─────────┤               │               │
  │               │                 │─── window.open(url) ────────────────────────────►│
  │◄── Payment Page ──────────────────────────────────────────────────────────────────┤
```

---

## 10. Scalability and Resiliency Considerations

### Current Architecture Strengths
- **Client-side rendering**: No server compute for 3D rendering; scales with user devices
- **Static SPA deployment**: Azure Blob Storage static website hosting (no server needed)
- **Chunked model loading**: Parallel downloads, retry logic per chunk
- **State persistence**: Auth survives page refreshes via localStorage
- **Environment-based configuration**: Easy environment switching
- **Manual deployment**: Simple and controlled release process via Azure Portal/Storage Explorer

### Scalability Factors
| Factor | Current Approach | Consideration |
|--------|-----------------|---------------|
| 3D Model Size | Chunked parallel download (10 concurrent) | CDN caching for chunks would improve repeat loads |
| API Load | Direct client-to-API calls | API gateway rate limiting managed server-side |
| Asset Delivery | Azure Blob with SAS tokens | Token expiry requires fresh fetch each session |
| State Management | Client-side (Zustand) | No server session; stateless backend |

### Resiliency Patterns
- **Retry with backoff**: Model chunk downloads retry 3 times with 500ms/1s/1.5s delays
- **Graceful degradation**: Security check failure shows overlay rather than crashing
- **Error boundaries**: API errors caught and displayed via toast/inline messages
- **Fallback pricing**: Static `priceConfig.basePrice` used if API unavailable

### Potential Improvements
- Service Worker for offline asset caching
- WebSocket for real-time price updates
- Progressive model loading (LOD)
- Server-side rendering for SEO (currently hash-routed)
- Circuit breaker pattern for API calls

---

## 11. Security Architecture

### Asset Protection
- DevTools detection (7+ methods: console, window size, performance, debugger, toString, keyboard, context menu)
- 3D model loaded via temporary SAS tokens (not stored)
- Blob URLs revoked immediately after GPU loading
- Fetch/XHR intercepted and blocked when DevTools detected
- Console output suppressed in production

### Network Security
- All APIs over HTTPS
- Bearer token authentication
- No sensitive data in URL parameters
- CORS handled via proxy (dev) or server config (prod)

---

*Document generated for external engineering partners. Confidential business-sensitive information excluded.*
