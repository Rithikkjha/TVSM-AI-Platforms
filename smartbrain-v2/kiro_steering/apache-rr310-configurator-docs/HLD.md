# High Level Design — TVS Apache RR310 BTO Configurator

---

## Overview

The TVS Apache RR310 Built-to-Order (BTO) Configurator is a browser-based 3D motorcycle customization experience that enables customers to configure their Apache RR310 motorcycle in real time — selecting kits, colors, alloy wheels, and race numbers — then place an order directly through the TVS Motor digital commerce platform.

The application renders a photorealistic 3D model using WebGL/WebXR, supports Augmented Reality on mobile devices, and integrates with the TVS Motor website for authentication, order placement, and payment processing.

---

## Tier Classification

**Tier 2: Business Critical but not Life-or-Death**

The configurator is a revenue-generating customer-facing application directly tied to vehicle bookings. Downtime results in lost sales and poor customer experience but does not impact safety-critical or operational systems.

---

## Background

The BTO program allows customers to personalize their Apache RR310 with accessory kits and color options before purchase. This replaces the traditional "pick from available stock" model with a direct-to-consumer customization flow. The 3D configurator provides an immersive visualization that drives buyer confidence and reduces post-purchase returns.

Previous iterations used a simpler gallery-based approach. The current system uses real-time 3D rendering with material swapping to show exact visual output of the customer's choices.

---

## Requirements

### Functional

- Interactive 3D visualization of Apache RR310 with rotate, zoom, and pan controls
- Kit selection (Dynamic Kit, Dynamic Pro / Race Kit)
- Color variant selection (Racing Red, Titanium Black, Bomber Grey, Sepang Blue, Race Replica)
- Alloy wheel color customization
- Race number personalization
- Feature exploration with audio narration and callout overlays
- Real-time pricing calculation based on configuration
- Save and load named configurations (authenticated users)
- Order placement with TVS Booking API integration
- Augmented Reality viewing on mobile (via Google Model Viewer)
- QR code generation for desktop-to-mobile AR handoff
- Integration with TVS Motor website authentication
- Google Analytics event tracking for user interactions

### Non-Functional

- Page load time < 5 seconds on 4G connections
- 3D model interaction at 30+ FPS on mid-tier mobile devices
- Support for iOS Safari, Android Chrome, Desktop Chrome/Edge/Firefox
- No build tooling dependency — static file deployment
- Anti-tampering protection (devtools detection, console suppression)
- Responsive design for mobile portrait, landscape, and desktop viewports

---

## Current Architecture (HLD)

```
┌──────────────────────────────────────────────────────────────────┐
│                    TVS Motor Website (tvsmotor.com)               │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  BTO Product Page                                           │ │
│  │  /tvs-apache/rr-310/built-to-order/book-online              │ │
│  │                                                             │ │
│  │  ┌───────────────────────────────────────────────────────┐  │ │
│  │  │           <iframe> Configurator App                   │  │ │
│  │  │                                                       │  │ │
│  │  │  ┌─────────────┐   ┌──────────────────────────────┐  │  │ │
│  │  │  │ Config      │   │  3D Rendering Engine          │  │  │ │
│  │  │  │ Schema      │──▶│  (A-Frame + Three.js)         │  │  │ │
│  │  │  │ (skuSchema) │   │                               │  │  │ │
│  │  │  └─────────────┘   └──────────────────────────────┘  │  │ │
│  │  │                                                       │  │ │
│  │  └───────────────────────────────────────────────────────┘  │ │
│  │           ▲                          │                      │ │
│  │           │ postMessage              │ postMessage           │ │
│  │           │ (auth tokens)            │ (redirect URLs)      │ │
│  └───────────┼──────────────────────────┼──────────────────────┘ │
│              │                          ▼                         │
│  ┌───────────┴──────┐  ┌────────────────────────────────────┐   │
│  │  Auth & Session   │  │  Booking / Payment Flow            │   │
│  │  Management       │  │  (Post-configurator)               │   │
│  └───────────────────┘  └────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
            │                              │
            ▼                              ▼
┌────────────────────┐      ┌─────────────────────────────┐
│  Firebase Cloud    │      │  TVS Motor Booking API       │
│  Functions         │      │  (tvsmotor.com/api/*)        │
│  (GCP us-central1) │      └─────────────────────────────┘
└────────────────────┘
            │
            ▼
┌────────────────────┐      ┌─────────────────────────────┐
│  Azure Blob        │      │  Google Analytics /          │
│  Storage           │      │  Tag Manager                 │
│  (3D Model Chunks) │      └─────────────────────────────┘
└────────────────────┘
```

---

## Proposed Architecture (HLD)

> *Note: This section documents the current production architecture as implemented.*

### Key Components

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| Host Page | TVS Motor CMS | Embeds configurator iframe, manages user session |
| Configurator Shell | Static HTML/CSS | Bootstrap, layout containers, A-Frame scene |
| Configuration Schema | JavaScript Object (skuSchema) | All product data, pricing, icon behaviors, API endpoints |
| 3D Rendering Engine | A-Frame 1.4.0 + Three.js | WebGL rendering, material system, camera, interactions |
| AR Module | Google Model Viewer | Native AR on mobile (ARCore/ARKit) |
| User Config Service | Firebase Cloud Functions (GCP) | Save/load/manage user configurations |
| Order Service | TVS Motor Booking API | Order placement, payment redirect |
| Asset Delivery | Azure Blob Storage | Chunked 3D model delivery via API gateway |
| Static Assets | TVS BTO CDN (bto.tvsmotor.com) | JS frameworks, images, textures, audio |
| Analytics | Google Tag Manager + GA4 | User behavior and conversion tracking |

### Interactions and Boundaries

- **Iframe boundary**: Configurator runs in a sandboxed iframe. Communication with parent site happens exclusively via `window.postMessage`
- **Authentication boundary**: Auth tokens originate from TVS website, passed via URL parameters into the iframe
- **API gateway**: TVS Motor exposes a `/api/Headless/Post` endpoint that proxies requests to internal microservices (user config, booking)
- **3D asset boundary**: Models are either loaded locally (static GLB files) or assembled from encrypted binary chunks fetched via API

### Pros
- Zero build tooling — instant deploy via static file upload
- Full client-side rendering — no server-side compute for 3D
- CDN-served assets — global edge caching for performance
- Modular configuration — product changes via schema only (no code changes)

### Cons
- No server-side rendering — poor SEO (mitigated by iframe embed on SEO-friendly parent page)
- Large JavaScript bundle — single-file renderer (~4000+ lines, not tree-shaken)
- Client-side pricing logic — requires validation on backend before order completion
- No automated testing infrastructure

---

## Data Flow / Sequence Diagrams

### Sequence 1: Application Initialization

```
User Browser          TVS Website        Configurator       Azure Blob API       CDN
     │                    │                   │                   │                │
     │──GET BTO Page─────▶│                   │                   │                │
     │◀──HTML + iframe────│                   │                   │                │
     │                    │                   │                   │                │
     │──Load iframe───────┼──────────────────▶│                   │                │
     │                    │──postMessage──────▶│                   │                │
     │                    │  (authToken,       │                   │                │
     │                    │   userId)          │                   │                │
     │                    │                   │                   │                │
     │                    │                   │──GET A-Frame.js──▶│                │
     │                    │                   │◀─────────────────│                │
     │                    │                   │                   │                │
     │                    │                   │──GET chunks API──▶│                │
     │                    │                   │◀──chunk URLs──────│                │
     │                    │                   │──GET chunk[0..N]─▶│                │
     │                    │                   │◀──binary data─────│                │
     │                    │                   │                   │                │
     │                    │                   │──Reassemble GLB───│                │
     │                    │                   │──Parse GLTF───────│                │
     │                    │                   │──Render 3D Scene──│                │
     │◀──3D Scene Ready───┼───────────────────│                   │                │
```

### Sequence 2: Configuration Change (Color/Kit Selection)

```
User                    Configurator Engine          Schema (skuSchema)
  │                           │                            │
  │──Click "Racing Red"──────▶│                            │
  │                           │──Lookup icon 3D_Actions───▶│
  │                           │◀──[modifyMeshMaterial,     │
  │                           │    changeGlobalConfig,     │
  │                           │    modelTransformation]────│
  │                           │                            │
  │                           │──Apply texture swap────────│
  │                           │──Update active config ID───│
  │                           │──Animate camera position───│
  │                           │──Recalculate price─────────│
  │                           │                            │
  │◀──Updated 3D + Price──────│                            │
```

### Sequence 3: Order Placement

```
User         Configurator       TVS Booking API       TVS Website
  │               │                    │                   │
  │──Buy Now─────▶│                    │                   │
  │◀──Price ──────│                    │                   │
  │   Summary     │                    │                   │
  │               │                    │                   │
  │──Accept T&C──▶│                    │                   │
  │──Place Order─▶│                    │                   │
  │               │──POST /api/        │                   │
  │               │  placeorderfor     │                   │
  │               │  avataar───────────▶                   │
  │               │                    │                   │
  │               │◀──{RedirectUrl}────│                   │
  │               │                    │                   │
  │               │──postMessage───────┼──────────────────▶│
  │               │  (RedirectUrl)     │                   │
  │               │                    │    ┌──────────────│
  │               │                    │    │ Navigate to  │
  │◀──────────────┼────────────────────┼────┤ Payment Page │
  │               │                    │    └──────────────│
```

### Error Handling & Retry

- **3D Model Load Failure**: If chunk fetch fails, `split-gltf-model` component emits `model-error` event; fallback to local GLB file
- **API Timeout**: Order placement has no client-side retry; user is shown error state and can retry manually
- **Auth Token Expiry**: If Firebase/TVS API returns 401, user is redirected to login on parent site
- **Network Offline**: No explicit offline support; user must have active connectivity

---

## Deployment & Rollout Plan

### Deployment Model

| Environment | Domain | Deployment |
|-------------|--------|------------|
| Production | `bto.tvsmotor.com` | Manual upload to Azure Blob Storage (static website hosting) |
| UAT / Pre-prod | `dev-bto.tvsmotor.net` / `uat-www.tvsmotor.net` | Manual upload to UAT Azure Blob Storage |
| Local Dev | `localhost` | Direct file serving (no build step) |

### Deployment Process

1. Code changes made to non-minified JS files
2. Minification applied manually (configmaster → `.min.js`, avataarrenderer → `.min.js`)
3. Version bump via query string parameter (`?v=09` → `?v=10`)
4. Static files uploaded manually to Azure Blob Storage container (`$web`)
5. CDN cache purged (if Azure CDN sits in front of blob storage)

### Rollback Strategy

- Revert to previous versioned files on CDN
- Query string versioning ensures browser cache bypass
- No database migrations — rollback is purely file-based

### Feature Flags

- `debugFlag` variable controls analytics initialization
- Commented-out code blocks serve as feature toggles (e.g., Firebase auth flow, MixPanel)
- URL parameters control runtime behavior (`ar=true`, `platform=`)

---

## Metrics to be Tracked

| Metric | Tool | Purpose |
|--------|------|---------|
| Page Load Time | GA4 / Web Vitals | Performance monitoring |
| 3D Model Load Time | Custom GA Event | Asset delivery performance |
| Configuration Interactions | GA4 Events | User engagement (kit/color/wheel changes) |
| Buy Now Click Rate | GA4 Events | Conversion funnel |
| Order Placement Success | GA4 Events + Backend | End-to-end conversion |
| AR Launch Rate | GA4 Events | AR feature adoption |
| Session Duration | GA4 | Time spent configuring |
| Device/Browser Distribution | GA4 | Compatibility insights |
| Error Rate (model-error events) | Custom logging | Reliability |

---

## Data Analytics / Data Engineering

| Data Point | Source | Destination |
|------------|--------|-------------|
| User interactions (clicks, selections) | GA4 Events | Google Analytics Dashboard |
| GTM Container events | Google Tag Manager (GTM-KD53L7) | Marketing platforms |
| Order data | TVS Booking API | TVS Backend / Data Lake |
| Configuration save/load | Firebase Cloud Functions | Firestore (GCP) |
| Session metadata | GA4 (G-9QYYD82JSC) | BigQuery (via GA4 export) |

---

## API Integrations

### TVS Motor Platform APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/Headless/Post` | POST | Generic proxy to internal services |
| `/api/Headless/Get?api=/api/BlobSas/GetRes?t=rr310` | GET | Fetch signed URLs for 3D model chunks |
| `/api/placeorderforavataar` | POST | Place BTO order, returns payment redirect URL |
| `/api/Booking/GetVehicleOrderCountFromVehicleCode?vehicleCode=101` | GET | Get remaining booking slots |
| `/api/WebSiteUserConfiguration/WebSiteUserConfigurations` | POST (via Headless) | Save user configuration |
| `/api/WebSiteUserConfiguration/GetWebSiteUserConfigurations` | POST (via Headless) | Load user configurations |

### Firebase Cloud Functions (GCP)

| Function | Method | Purpose |
|----------|--------|---------|
| `GetAuthInfo` | POST | Validate auth token, return user details |
| `GetUserInfoAvataar` | POST | Retrieve user profile and saved configs |
| `SaveConfiguration` | POST | Persist configuration state |
| `GetUserDetails` | POST | Check if user has placed order previously |
| `UserPlacedOrder` | POST | Record order placement event |

---

## Authentication / Authorization Flow

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ TVS Website │     │  Configurator    │     │  Backend APIs    │
│ (Parent)    │     │  (iframe)        │     │                  │
└──────┬──────┘     └────────┬─────────┘     └────────┬─────────┘
       │                     │                         │
       │  User logs in on    │                         │
       │  TVS website        │                         │
       │                     │                         │
       │──URL params─────────▶                         │
       │  ?authToken=xxx     │                         │
       │  &userId=yyy        │                         │
       │  &configurationNo=z │                         │
       │                     │                         │
       │                     │──POST GetAuthInfo──────▶│
       │                     │  {authtoken: xxx}       │
       │                     │                         │
       │                     │◀──{userId, isGuest}─────│
       │                     │                         │
       │                     │  (If guest: limited     │
       │                     │   save/order disabled)  │
       │                     │                         │
       │                     │──API calls with─────────▶
       │                     │  userId in body         │
       │                     │                         │
```

**Key Points:**
- No OAuth/JWT refresh flow in the configurator — tokens are one-shot from parent page
- Guest users can configure but not save/order
- User identity is passed as a simple string parameter (no client-side token storage)
- Authorization is enforced server-side on the TVS Booking API

---

## External Systems

| System | Owner | Integration Type | Criticality |
|--------|-------|-----------------|-------------|
| TVS Motor Website | TVS Motor | iframe embed + postMessage | Critical — hosts the experience |
| TVS Booking API | TVS Backend | REST API | Critical — order placement |
| Firebase / GCP | Google Cloud | Cloud Functions | Medium — config persistence |
| Azure Blob Storage | Microsoft Azure | REST API (via TVS gateway) | Critical — 3D model delivery |
| Google Analytics | Google | JavaScript SDK | Low — analytics only |
| Google Tag Manager | Google | JavaScript SDK | Low — tag management |
| Google Fonts | Google | CSS CDN | Low — typography |
| Google Draco CDN | Google | Static files | Medium — 3D compression decoder |
| unpkg CDN | Unpkg | ES Module | Medium — AR model viewer |
| jsDelivr CDN | jsDelivr | Static files | Low — QR code library |

---

## Infrastructure Dependencies

| Layer | Technology | Provider |
|-------|-----------|----------|
| Static Hosting | Azure Blob Storage (static website) | Microsoft Azure |
| CDN (optional) | Azure CDN in front of blob storage | Microsoft Azure |
| 3D Asset Storage | Azure Blob Storage (separate container for chunks) | Microsoft Azure |
| API Gateway | TVS Headless API (`/api/Headless/*`) | TVS Backend |
| Serverless Functions | Firebase Cloud Functions | Google Cloud Platform |
| DNS / Domain | `tvsmotor.com`, `tvsmotor.net` | TVS IT |
| SSL/TLS | HTTPS on all endpoints | TVS / Cloud providers |
| Analytics | Google Analytics 4 + GTM | Google |
| 3D Compression | Draco Decoder (gstatic.com) | Google |

---

## Scalability and Resiliency Considerations

### Scalability

| Aspect | Current Approach | Notes |
|--------|-----------------|-------|
| Static Assets | CDN-served | Scales horizontally via CDN edge nodes |
| 3D Models | Azure Blob + chunked delivery | Blob storage scales independently |
| API Load | TVS backend handles scaling | Order API managed by TVS platform team |
| Firebase Functions | Auto-scaling (GCP managed) | Pay-per-invocation, scales to demand |
| Client Rendering | GPU on user's device | No server-side rendering load |

### Resiliency

| Risk | Mitigation |
|------|-----------|
| CDN outage | Multiple CDN fallbacks (CloudFront `d77dh4faztz32.cloudfront.net` as backup) |
| 3D model chunk fetch failure | Local GLB fallback files bundled with deployment |
| Firebase unavailability | Graceful degradation — guest mode continues to work |
| TVS API downtime | User shown error; can retry; configuration preserved client-side |
| Browser GPU crash | A-Frame handles WebGL context loss with scene re-initialization |
| High traffic (product launch) | CDN caching, no server-side compute for rendering |

### Current Limitations

- No client-side caching strategy for 3D models (loaded fresh each session)
- No service worker for offline resilience
- Single-region Firebase deployment (us-central1)
- No load testing data available
- No circuit breaker pattern on API calls

---

## Alternatives Considered

### Option A: Server-Side Rendering (SSR) for 3D

- **Pros**: Consistent rendering across devices, no GPU dependency
- **Cons**: High infrastructure cost, latency for real-time interactions, complex streaming architecture
- **Rejected**: Real-time interaction requires client-side rendering; SSR not viable for 60fps 3D manipulation

### Option B: React/Next.js with Three.js (react-three-fiber)

- **Pros**: Component-based architecture, better developer experience, tree-shaking, testing infrastructure
- **Cons**: Build tooling dependency, higher onboarding complexity, migration effort from current working system
- **Rejected**: Current system is stable and performant; migration cost not justified for incremental benefit

### Option C: Unity WebGL Export

- **Pros**: Industry-standard 3D engine, visual editor for scenes, built-in physics
- **Cons**: Large bundle size (10+ MB), longer load times, poor mobile browser compatibility, opaque build output
- **Rejected**: Web-native approach (A-Frame) provides better load performance and broader compatibility

---

## Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| CDN cache poisoning | Users see stale/broken experience | Low | Version query strings, cache headers |
| 3D model IP theft | Competitors extract bike model | Medium | Chunked delivery, obfuscated assembly, devtools blocking |
| Client-side price tampering | Incorrect order amounts | Medium | Server-side price validation before payment |
| Firebase quota exhaustion | Save/load features fail | Low | Monitoring + auto-scaling |
| Browser compatibility regression | Features break on update | Medium | Manual testing on major browser releases |
| Large model files on slow networks | Users abandon before load | Medium | Progressive loading, chunked delivery, loading UX |

---

## Appendix

### Glossary

| Term | Definition |
|------|-----------|
| BTO | Built to Order — customization-before-purchase model |
| GLB | GL Transmission Format Binary — 3D model file format |
| Draco | Google's 3D mesh compression library |
| A-Frame | Mozilla's open-source WebXR framework built on Three.js |
| IBL | Image-Based Lighting — environment map for realistic reflections |
| skuSchema | The master configuration object that drives all product behavior |
| WebXR | Web API for VR/AR experiences in the browser |
| postMessage | Browser API for cross-origin iframe communication |

### Acronyms

| Acronym | Expansion |
|---------|-----------|
| D2C | Direct to Consumer |
| HLD | High Level Design |
| CDN | Content Delivery Network |
| API | Application Programming Interface |
| AR | Augmented Reality |
| XR | Extended Reality (umbrella for AR/VR) |
| GTM | Google Tag Manager |
| GA4 | Google Analytics 4 |
| GCP | Google Cloud Platform |
| UAT | User Acceptance Testing |
| GLB | GL Binary (glTF binary format) |
| FPS | Frames Per Second |
| SSL | Secure Sockets Layer |
| TLS | Transport Layer Security |

---

*Document generated: June 2026 | Version: 1.0 | Classification: For External Engineering Partners*
