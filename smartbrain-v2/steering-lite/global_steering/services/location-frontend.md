# location-frontend


## Product Context


# Product Overview — Location Frontend

## What This Service Does

This is the **TVS Motor Location Master** frontend — a React-based web application for managing and verifying dealership geo-locations across TVS Motor's global dealer network. It serves three distinct user personas through separate flows:

1. **Dealer Flow** — Mobile-first experience where dealers capture and submit their dealership's GPS coordinates and storefront photos via SMS-triggered links.
2. **Admin Flow** — Desktop dashboard for TVS Motor admins to review, approve, or reject dealer-submitted locations, manage dealer lists, send SMS update links, and perform bulk operations.
3. **Dealer Locator** — Public-facing, internationalized dealer search tool allowing end-users to find nearby TVS dealerships by proximity, type, and outlet category.

The application is part of TVS Motor's internal platform ecosystem, deployed at `location.tvsmotor.com` (prod) and `dev-location.tvsmotor.net` (dev).

---

## Domain Entities

| Entity | Description |
|--------|-------------|
| **Dealer** | A TVS Motor dealership identified by SAP dealer code, with name, type, category, contact info, and location status |
| **DealerLocation** | GPS coordinates (lat/long), reverse-geocoded address, SAP address, and submitted address for a dealer |
| **LocationStatus** | Verification state: Pending, Verified, Rejected, etc. with user-friendly labels |
| **DealerType** | Classification: Sales, Service, Spares, Authorised Parts Stockist |
| **OutletSelection** | Vehicle categories: Two Wheeler, Three Wheeler, Super Premium, Electric, specific models (Apache RR310, TVS iQube, etc.) |
| **DealershipPhoto** | Storefront image captured by dealer for verification |
| **Country** | Multi-country support with country codes, provinces, cities, and locale-specific configurations |
| **RejectionReason** | Predefined rejection comments used by admins |
| **Contact** | Phone number and email for dealer owner, branch manager, or custom user |

---

## Integrations

| System | Purpose | Base URL Pattern |
|--------|---------|-----------------|
| **Location Master API (Admin Flow)** | Dealer list, summary, verification, SMS sending, rejection reasons | `REACT_APP_ADMIN_BASE_URL` |
| **Location Master API (Dealer Flow)** | Dealer info fetch, location submission | `REACT_APP_DEALER_BASE_URL` |
| **Location Master API (Dealer Web)** | Dealer dashboard data for dealer-flow users | `REACT_APP_DEALERWEB_BASE_URL` |
| **Location Master API (IB Admin)** | International business: dealer CRUD, bulk upload, country-specific operations | `REACT_APP_ADMIN_IB_BASE_URL` |
| **Location Master API (Dealer Locator)** | Public dealer search, filter config, province data | `REACT_APP_DEALER_LOCATER_BASE_URL` |
| **Google Maps Geocoding API** | Reverse geocoding lat/long to addresses | `maps.googleapis.com/maps/api/geocode/json` |
| **Google Maps JavaScript API** | Map rendering, marker clustering, place autocomplete | Via `@react-google-maps/api` and `@vis.gl/react-google-maps` |
| **Azure AD B2C (SSO)** | Admin authentication via OAuth/OIDC | `REACT_APP_PUBLIC_LOGIN_URL` |
| **TVS Motor API Gateway** | Unified API gateway for all backend calls | `apim.tvsmotor.com` (prod) / `dev-api.tvsmotor.net` (dev) |

---

## Business Rules

### Dealer Location Capture
- Dealers must access the capture flow from a **mobile device** (non-admin routes are blocked on desktop)
- GPS must be enabled to capture coordinates; accuracy is displayed in meters
- Dealers must capture a **clear front photo** of the dealership with the name visible
- Privacy policy and T&C acceptance is required before submission
- Location submissions include: GPS coordinates, photo, confirmed address
- SMS links contain a `secretKey` for dealer identification (links can expire)

### Admin Verification
- Admins authenticate via Azure AD B2C SSO
- Admins can approve or reject submitted locations with predefined rejection comments
- Rejected dealers receive an SMS with a new location update link
- Admin dashboard shows summary counts by location status
- Dealer list supports pagination, search, filtering by status, and sorting
- Admins can send SMS to dealer owner, branch manager, or custom user

### International Business (IB)
- Multi-country support with country-specific dealer lists and summaries
- Users are assigned to specific countries (fetched via user ID)
- Dealers can be created, updated, and bulk-uploaded via XLSX files
- Country flags indicate dealer's operating regions

### Dealer Locator (Public)
- No authentication required
- Proximity-based search with configurable distance radius (slider)
- Filters: dealer type (Sales/Service/Spares), outlet selection (vehicle categories)
- Multi-language support: English, Italian, Turkish, Spanish, Nepali, Arabic, Swahili, Indonesian, Bengali
- Country and locale passed via URL query parameters

### Authentication & Authorization
- Admin tokens stored in localStorage (Bearer token auth)
- 401 responses redirect to admin login
- 403 responses redirect to access-denied page (if token exists) or login (if no token)
- Sensitive data in localStorage is AES-encrypted using CryptoJS
- Dealer Locator endpoints are public (no auth required)



## Code Structure


# Project Structure — Location Frontend

## Annotated Directory Layout

```
location-frontend/
├── .env.dev / .env.uat / .env.prod   # Environment-specific API URLs and config
├── .github/PULL_REQUEST_TEMPLATE/    # PR templates for issues, releases, bugs, features
├── azure-pipelines/                  # CI/CD pipeline definitions (dev, uat, prod)
│   ├── dev-ci.yaml
│   ├── uat-ci.yaml
│   └── prod-ci.yaml
├── public/
│   ├── assets/                       # Static PDFs (user guides)
│   ├── index.html                    # SPA entry point
│   └── favicon.ico, logos, robots.txt
├── src/
│   ├── index.tsx                     # Entry point — loads i18n, then dynamic import of bootstrap
│   ├── bootstrap.tsx                 # ReactDOM.createRoot render
│   ├── App.tsx                       # Root component: Redux Provider + ToastProvider + HashRouter
│   ├── RemoteApp.tsx                 # Micro-frontend remote entry (Module Federation placeholder)
│   ├── i18n.ts                       # Internationalization config (9 languages)
│   ├── declaration.d.ts             # TypeScript module declarations
│   │
│   ├── components/
│   │   ├── Navigation/
│   │   │   └── AppRouter.tsx         # All route definitions (React Router v6)
│   │   ├── pages/                    # Feature pages (one folder per page/flow)
│   │   │   ├── AdminDashboard/       # Admin summary dashboard
│   │   │   ├── DealerDashboard/      # Dealer-flow dashboard
│   │   │   ├── DealerInfo/           # Admin view of dealer details
│   │   │   ├── DealerInfoDealerFlow/ # Dealer's own info view
│   │   │   ├── DealerList/           # Admin paginated dealer list
│   │   │   ├── ConfirmLoc/           # Dealer confirms captured location
│   │   │   ├── CaptureImage/         # Camera capture for dealership photo
│   │   │   ├── CaptureInstruction/   # Photo capture instructions
│   │   │   ├── Instruction/          # Dealer flow landing/instructions
│   │   │   ├── Login/                # SSO login callback handler
│   │   │   ├── SSOLogin/             # SSO login initiation
│   │   │   ├── SuccessPage/          # Submission success confirmation
│   │   │   ├── PrivacyPolicy/        # Privacy policy display
│   │   │   ├── DealerErrorPage/      # Error pages (dealer, admin, access denied)
│   │   │   └── AppVersion/           # App version display
│   │   ├── common/                   # Shared/reusable UI components
│   │   │   ├── GoogleMapsComponent.tsx / MapComponent.tsx  # Map rendering
│   │   │   ├── DealerInfoHeader*.tsx  # Dealer info headers (desktop/mobile)
│   │   │   ├── FilterBar.tsx / SortBar.tsx / SearchBar.tsx # List controls
│   │   │   ├── BulkUpload.tsx        # XLSX bulk upload UI
│   │   │   ├── AddDealer.tsx         # Add/edit dealer form
│   │   │   ├── Loader.tsx / LoaderPopup.tsx  # Loading states
│   │   │   ├── PopupHandler.tsx / DealerModal.tsx  # Modal dialogs
│   │   │   ├── PdfReder.tsx          # PDF viewer (user guides)
│   │   │   ├── Dropdown.tsx / Select.tsx / VehicleDropdown.tsx  # Form controls
│   │   │   ├── Tile_desktop.tsx / Tile_mobile.tsx  # Responsive tiles
│   │   │   └── cta/ , test/          # CTA buttons, test utilities
│   │   └── MapComponent.tsx          # Top-level map component
│   │
│   ├── DealerLocator/                # Dealer Locator feature module (public-facing)
│   │   ├── DealerCardPage.tsx        # Main page container
│   │   ├── DealerCardContainer.tsx   # Card list + map layout
│   │   ├── DealerLocatorDealerCard.tsx  # Individual dealer card
│   │   ├── DealerLocatorHeader.tsx   # Search header with autocomplete
│   │   ├── FilterDropdown.tsx        # Type/outlet filter UI
│   │   ├── Slider.tsx               # Distance radius slider
│   │   ├── FitBoundsHandler.tsx      # Map bounds auto-fit
│   │   ├── ZoomComponent.tsx         # Map zoom controls
│   │   ├── googleMapLoader.ts        # Google Maps script loader
│   │   ├── DealerLocatorPopUp.tsx    # Dealer detail popup
│   │   └── PopUpModalForDealerLocator.tsx  # Location permission modal
│   │
│   ├── rest/                         # HTTP client layer (Axios instances)
│   │   ├── httpCommon.ts             # Shared Axios factory with auth interceptors
│   │   ├── httpAdmin.ts             # Admin flow API client
│   │   ├── httpDealer.ts            # Dealer flow API client (no auth on requests)
│   │   ├── httpDealerWeb.ts         # Dealer web flow API client
│   │   ├── httpIbAdmin.ts           # International business admin API client
│   │   └── httpDealerLocator.ts     # Dealer locator API client (public, no auth)
│   │
│   ├── services/                     # Business logic / API call wrappers
│   │   ├── DealerDetailsService.ts   # Core service: dealer CRUD, lists, verification, SMS
│   │   ├── DealerFlowDealerDetailsService.ts  # Dealer-flow specific data fetching
│   │   ├── DealerLocaterService.ts   # Dealer locator search and filter config
│   │   ├── DealerService.ts          # IB dealer create/update
│   │   └── AdminDealerService.ts     # Bulk upload service
│   │
│   ├── store/                        # Redux Toolkit state management
│   │   ├── store.tsx                 # Store configuration with all slice reducers
│   │   ├── slices/                   # Redux slices (state + reducers)
│   │   │   ├── AdminDealerInfoFetchSlice.ts  # Admin dashboard state
│   │   │   ├── AdminDealerSlice.ts           # Admin dealer operations
│   │   │   ├── DealerflowDealerInfoSlice.ts  # Dealer dashboard state
│   │   │   ├── DealerInfoDealerFlowSlice.ts  # Dealer location details
│   │   │   ├── DealerLocatorSlice.ts         # Dealer locator results
│   │   │   ├── DealerLocatorNewSlice.ts      # Dealer locator filter options
│   │   │   ├── DelearDetailsSlice.ts         # Dealer details state
│   │   │   └── SendSmsFLowSlice.ts           # SMS sending state
│   │   └── thunks/                   # Async thunks (API calls)
│   │       ├── AdminDealerInfoFetchThunk.ts  # Admin list/summary/verify thunks
│   │       ├── AdminDealerThunk.ts           # Admin dealer operations
│   │       ├── DealerFlowInfoFetchThunk.ts   # Dealer flow data thunks
│   │       ├── DealerLocaterThunk.ts         # Dealer locator search thunk
│   │       ├── DealerLocatorNewThunk.ts      # Dealer locator filter thunk
│   │       ├── DealerThunk.ts                # IB dealer create/update thunks
│   │       ├── DelearDetailsThunk.ts         # Dealer details thunk
│   │       └── SendSmsFLowThunk.ts           # SMS flow thunk
│   │
│   ├── context/
│   │   └── ToastContext.tsx          # Toast notification system (success/error)
│   │
│   ├── constants/
│   │   ├── Constants.ts              # UI strings, labels, messages
│   │   ├── PageRoutes.ts            # Route path constants
│   │   ├── AppVersion.ts            # Version number and build date
│   │   └── index.ts                 # Barrel export
│   │
│   ├── utils/
│   │   └── DataEncryption.ts        # AES encrypt/decrypt for localStorage
│   │
│   ├── json/                         # Static GeoJSON data
│   │   ├── india_state_geo.json     # India state boundaries
│   │   └── MaskGeojson*.json        # Map mask overlays
│   │
│   ├── styles/
│   │   └── tailwind.css             # Tailwind CSS entry point
│   │
│   └── " assets"/                    # SVG/PNG icon components (React components)
│       ├── *.tsx                     # Icon components (ActiveDealerIcon, BikeIcon, etc.)
│       └── Images/                   # Additional icon components and PNGs
```

---

## Module Dependencies

```
index.tsx → bootstrap.tsx → App.tsx
                              ├── store/store.tsx (Redux Provider)
                              ├── context/ToastContext.tsx (Toast Provider)
                              └── Navigation/AppRouter.tsx (Routes)
                                    ├── pages/* (feature pages)
                                    │     ├── use store/slices/* (via useSelector)
                                    │     ├── dispatch store/thunks/* (via useDispatch)
                                    │     └── use components/common/* (shared UI)
                                    └── DealerLocator/* (public dealer search)

store/thunks/* → services/* → rest/http*.ts → Axios → Backend APIs
```

### Key Dependency Flows
- **Pages** consume Redux state via `useSelector` and dispatch thunks via `useDispatch`
- **Thunks** call service functions which use HTTP clients
- **HTTP clients** are pre-configured Axios instances per API domain
- **Common components** are shared across pages (no cross-page imports)
- **DealerLocator** is a self-contained module with its own components (not under `components/pages/`)

---

## Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **HashRouter** (`/#/path`) | Avoids server-side routing config; works with static hosting and Azure Blob Storage |
| **Redux Toolkit** for state | Centralized async state with loading/success/error status tracking per operation |
| **Multiple HTTP clients** | Each API domain has its own Axios instance with appropriate auth/interceptor config |
| **Dealer Locator as separate module** | Public-facing, no auth, different UX pattern — kept outside `components/pages/` |
| **Dynamic import for bootstrap** | Enables Module Federation compatibility (micro-frontend architecture) |
| **i18n inline translations** | All translations bundled in `i18n.ts` rather than external JSON files for simplicity |
| **localStorage + AES encryption** | Tokens and sensitive data encrypted at rest in browser storage |
| **Mobile-first gating** | Non-admin routes blocked on desktop via viewport width check in router |
| **Environment-based builds** | `env-cmd` switches `.env.*` files per environment at build time |
| **Tailwind CSS** | Utility-first styling; no CSS modules or styled-components |
| **GeoJSON static files** | India state boundaries and map masks bundled as static JSON |



## Tech Stack & Dependencies


# Tech Stack & Conventions — Location Frontend

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Framework** | React | 18.3.x |
| **Language** | TypeScript | 4.9.x |
| **Build Tool** | Create React App (react-scripts) | 5.0.1 |
| **State Management** | Redux Toolkit (`@reduxjs/toolkit`) | 2.2.x |
| **Routing** | React Router DOM (HashRouter) | 6.23.x |
| **HTTP Client** | Axios | 1.7.x |
| **Styling** | Tailwind CSS | 3.4.x |
| **Maps** | `@react-google-maps/api`, `@vis.gl/react-google-maps`, Leaflet + react-leaflet | Various |
| **Internationalization** | i18next + react-i18next | 23.x / 12.x |
| **Encryption** | crypto-js (AES) | 4.2.x |
| **PDF Rendering** | pdfjs-dist | 3.11.x |
| **UI Components** | rc-slider, classnames | Various |
| **Map Clustering** | `@googlemaps/markerclusterer` | 2.6.x |
| **Node Runtime** | Node.js | 18.19.0 (pinned in CI) |

---

## Coding Conventions

### File & Folder Naming
- **Pages**: PascalCase folder per page under `src/components/pages/` (e.g., `AdminDashboard/AdminDashboard.tsx`)
- **Components**: PascalCase `.tsx` files (e.g., `FilterBar.tsx`, `DealerModal.tsx`)
- **Services**: PascalCase with `Service` suffix (e.g., `DealerDetailsService.ts`)
- **Redux slices**: PascalCase with `Slice` suffix (e.g., `AdminDealerInfoFetchSlice.ts`)
- **Redux thunks**: PascalCase with `Thunk` suffix (e.g., `AdminDealerInfoFetchThunk.ts`)
- **HTTP clients**: camelCase with `http` prefix (e.g., `httpAdmin.ts`, `httpDealerLocator.ts`)
- **Constants**: PascalCase files, UPPER_CASE for route constants, PascalCase object keys for UI strings
- **Assets**: PascalCase `.tsx` icon components (e.g., `BikeIcon.tsx`, `ElectricIcon.tsx`)

### Component Patterns
- Functional components with `React.FC` type annotation
- Props interfaces defined inline or co-located in the same file
- No class components anywhere in the codebase
- Icons are React components returning SVG JSX (not imported SVG files)

### State Management
- Redux Toolkit `createSlice` for all state definitions
- `createAsyncThunk` for all API calls
- Status tracking pattern: every async operation has a `status` field with values from `STATUS` enum (`'idle' | 'loading' | 'success' | 'failed'`)
- Store typed with `RootState` and `AppDispatch` exports
- Slices include `resetX` reducers for clearing operation status

### Service Layer
- One service file per domain area
- Each function is an `async` function that calls an HTTP client method and returns `response.data` (or `response`)
- Services throw errors upward — thunks or components handle them
- No business logic in services; they are pure API wrappers

### HTTP Client Layer
- `httpCommon.ts` exports a `createHttpService` factory that produces `{ get, post, put, delete }` methods
- Each API domain has a dedicated HTTP client file importing from `httpCommon`
- Auth token read from `localStorage` and attached as `Bearer` header
- Response interceptors handle 401 (redirect to login) and 403 (redirect to access-denied)
- `httpDealerLocator.ts` is standalone (no auth, no interceptor redirects) for public endpoints

### Routing
- All routes defined in a single `AppRouter.tsx` file
- Route constants in `PageRoutes.ts` — always use constants, never hardcode paths
- HashRouter (`/#/path`) for all navigation
- Mobile-only gating: non-admin routes return a restriction message on desktop (viewport width ≤ 768px check)

### Internationalization
- Translations defined inline in `src/i18n.ts` (not external JSON files)
- Use `useTranslation()` hook in components
- Language determined by `locale` URL parameter or localStorage
- Fallback language: English (`en`)
- Supported: en, it, tr, es, ne, ar, sw, id, bn

---

## Patterns

### Async Data Flow
```
Component → dispatch(thunkAction(params))
  → Thunk calls service function
    → Service calls httpClient.get/post/put/delete
      → Axios request with auth headers
        → Backend API
      ← Response / Error (interceptors handle 401/403)
    ← Returns response.data or throws
  ← Thunk fulfilled/rejected
← Slice reducer updates state (data + status)
← Component re-renders via useSelector
```

### Status Pattern in Slices
```typescript
// Every async operation follows this pattern:
interface SliceState {
  data: DataType | null;
  status: 'idle' | 'loading' | 'success' | 'failed';
  errorMessage: string | null;
}

// In extraReducers:
.addCase(thunk.pending, (state) => { state.status = 'loading'; state.errorMessage = null; })
.addCase(thunk.fulfilled, (state, action) => { state.data = action.payload; state.status = 'success'; })
.addCase(thunk.rejected, (state, action) => { state.status = 'failed'; state.errorMessage = action.error.message; })
```

### Toast Notifications
- `ToastContext` provides `showToast(type, message)` via React Context
- Types: `"success"` or `"error"`
- Auto-dismiss after 3 seconds
- Rendered as fixed-position bottom-right overlay

### Data Encryption
- `writeToLocalStorage(key, value)` — AES encrypts before storing
- `readFromLocalStorage(key)` — decrypts on read
- Secret key from `REACT_APP_SECRET_KEY` env variable
- Used for tokens and locale preferences

### Environment Configuration
- Three environments: dev, uat, prod
- `env-cmd -f .env.<env>` selects the config at build time
- All API base URLs are environment variables (`REACT_APP_*`)
- Google Maps API key injected via CI pipeline variable (not in `.env` files)

---

## Error Handling

### HTTP Layer
- Axios response interceptors catch 401 → redirect to `/#/admin-login`
- Axios response interceptors catch 403 → redirect to `/#/admin-access-denied` (with token) or `/#/login` (without)
- All HTTP methods wrap calls in try/catch, log errors with `console.error`, and re-throw
- No global error boundary component

### Redux Layer
- Thunk `rejected` cases store error message in slice state
- Components check `status === 'failed'` and display error UI or toast
- Some thunks use `rejectWithValue` for structured error payloads

### Component Layer
- Error pages exist for dealer errors, admin errors, and access denied
- Expired/invalid SMS links show dealer error page with contact admin message
- Toast notifications for operation failures (create, update, verify)

### Known Gaps
- No global React error boundary
- `console.error` used extensively (no structured logging or error reporting service)
- Some error messages are generic ("Error fetching users:" even for non-user operations)

---

## Testing

### Framework
- Jest (via react-scripts) with React Testing Library
- `@testing-library/jest-dom` for DOM assertions
- `@testing-library/react` for component rendering
- `@testing-library/user-event` for interaction simulation
- `redux-mock-store` for Redux state mocking in tests

### Configuration
- Test command: `npm test` → `react-scripts test --coverage --watchAll=false`
- Coverage collected from `src/**/*.{js,jsx,ts,tsx}`
- Transform ignore: `node_modules/(?!axios)/`
- SonarQube exclusions: `src/components/pages/**/*.tsx`, `src/components/common/test/*`, `src/DealerLocator/DealerCardPage.tsx`

### Conventions
- Test files co-located in `src/components/common/test/` directory
- `App.test.tsx` exists at root level
- Coverage reports generated as `lcov.info` for SonarQube integration

---

## Deployment

### CI/CD Pipeline
- **Platform**: Azure DevOps Pipelines
- **Agent Pool**: `EA-Self-Hosted-Agent-For-PGM`
- **Environments**: dev, uat, prod (separate YAML files, same structure)
- **Trigger**: Manual (`trigger: none`)

### Pipeline Steps
1. Checkout (full history: `fetchDepth: 0`)
2. Node.js 18.19.0 setup
3. `npm install`
4. SonarQube prepare (project key: `Location-Frontend`)
5. `npm test` (with coverage)
6. `npm run build:<env>` (with Google Maps API key from pipeline variable)
7. SonarQube analyze (Java 17)
8. Copy `build/**` to artifact staging
9. SonarQube publish results
10. Publish build artifacts (e.g., `locationui-dev`)

### Static Analysis
- SonarQube for code quality and coverage
- ESLint via `react-app` and `react-app/jest` presets
- No Prettier config (relies on ESLint defaults)

### Versioning
- Manual version bump in `src/constants/AppVersion.ts` before each deployment
- `APP_VERSION` string and `BUILD_DATE` timestamp

### Hosting
- Static SPA build (`build/` folder) deployed to Azure infrastructure
- HashRouter ensures all routes work without server-side routing config
- Production domain: `location.tvsmotor.com`
- Dev domain: `dev-location.tvsmotor.net`

