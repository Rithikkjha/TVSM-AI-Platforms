# TVS-CPS-PORTAL


## Product Context


# Product — TVS Channel Partner System (CPS Portal)

## What This Service Does

The CPS Portal ("The Norton Hub") is a multi-tenant dealer management platform for TVS Motor Company's Norton motorcycle brand. It enables channel partners (dealers, OEM staff) to manage the full lifecycle of after-sales service, parts ordering, vehicle bookings, warranty claims, and dealer operations through a single web application with PWA support.

## Domain Entities

### Core Entities

| Entity | Description |
|--------|-------------|
| **Job Card** | Service job cards tracking vehicle repairs — includes parts, labor, inspection, assignment, invoicing |
| **Claim** | Warranty/service claims with create → submit → approve/reject → appeal → close workflow |
| **Appointment** | Service appointment scheduling with calendar, reminders, follow-ups, status transitions |
| **Enquiry** | Customer enquiries and sales lead management |
| **Booking** | Vehicle reservations with lifecycle: reserved → confirmed → allocated → invoiced → delivered → cancelled |
| **Parts/Vehicles/Accessories/Merchandise** | Catalog browsing, cart management, draft orders, order placement, approval workflows |
| **Inventory** | Stock management for parts, vehicles, accessories, merchandise |
| **Inwarding (GRN)** | Goods Receipt Notes — receiving and verifying incoming shipments |
| **Warranty** | Warranty registration and tracking |
| **NPQR** | New Product Quality Reports for defect tracking |
| **Invoice/Billing** | Invoice generation for parts and vehicle sales |
| **Allotment** | Vehicle allocation to customers |

### Supporting Entities

| Entity | Description |
|--------|-------------|
| **Customer** | Customer records with search, create, update |
| **Dealer** | Channel partner (dealership) information |
| **User** | Authenticated users with roles, permissions, tenant association |
| **Notification/Announcement** | System-wide announcements and banners |
| **Collateral** | Marketing materials and documents for dealers |
| **Training** | Dealer training content with categories and completion tracking |
| **Reports** | Analytics dashboards and downloadable reports |

## Integrations

| System | Purpose | Integration Point |
|--------|---------|-------------------|
| **Backend API** | All domain operations | RESTful v1 APIs via Axios (`/v1/claims/*`, `/v1/jobcards/*`, etc.) |
| **UMS (User Management Service)** | Authentication | OAuth2 PKCE token exchange, refresh tokens (`/auth/v2/app/*`) |
| **Salesforce** | Support tickets | GMS (Grievance Management), dealer support cases via iframe/URL |
| **Site24x7** | Real User Monitoring | Client-side RUM script injection |
| **FormBuilder** | Inspection checklists | Microfrontend integration with token-based auth |
| **Web Push** | PWA notifications | Service worker push subscriptions |
| **Runtime Assets Server** | Tenant configuration | External config served at runtime (not baked into build) |

## Business Rules

### Authentication & Authorization
- OAuth2 PKCE flow via UMS for login; tokens stored in httpOnly cookies via BFF API routes
- Automatic token refresh on 401 with request queuing (failed requests retry after refresh)
- Session expiry broadcasts a custom DOM event (`auth:sessionExpired`) to trigger logout UI
- Middleware blocks unauthenticated access to all `/dashboard/*` routes; redirects to `/login`
- All URLs are normalized to lowercase via middleware

### Role-Based Access Control (RBAC)
- 150+ granular permission codes (e.g., `P_JC01` = Create Job Card, `P_C06` = View Claim Details)
- Two user types: **OEM** (area sales managers) and **DEALER/DEALER_EMPLOYEE**
- `<Access permission="...">` component for element-level visibility
- `<AccessRoute permission="...">` component for page-level access (renders Unauthorized if denied)
- Permissions stored in Redux user slice after login

### Multi-Tenancy
- Tenant determined at build/deploy time via `NEXT_APP_TENANT` env var (e.g., `norton-uk`, `norton-us`)
- Tenant-specific: styles, i18n translations, PWA manifest, splash screens, icons, feature flags
- Runtime config loaded from external server on app startup (not embedded in JS bundle)
- Base path hardcoded to `/thenortonhub`

### Order Workflows
- Parts/Vehicles/Accessories/Merchandise share a common flow: Browse Catalog → Add to Cart → Save Draft → Place Order → Approval → Fulfillment
- Orders support approval workflows with approve/reject permissions
- GRN (Goods Receipt) flow for inwarding received goods

### Data & Localization
- 5 supported languages: English, French, Italian, German, Spanish
- Language persisted in Redux and localStorage; client-side translation only
- Timezone-aware date handling (user timezone from profile)
- Currency formatting based on tenant locale (GBP for UK)



## Code Structure


# Structure — Annotated Directory Layout & Architecture

## Monorepo Layout

```
TVS-CPS-PORTAL/
├── channel-partner-system/       # Next.js 15 App Router application (main package)
├── shared/                       # Reusable component library (@shared/channel-partner-system)
├── runtime-assets/               # Tenant-specific runtime config (served externally, not bundled)
├── azure-pipelines/              # CI/CD pipeline definitions
├── Dockerfile                    # Multi-stage Docker build (Node 25.9-alpine)
└── package.json                  # Root workspace config (npm workspaces)
```

## channel-partner-system/ (Main Application)

```
channel-partner-system/
├── src/
│   ├── app/                      # Next.js App Router — file-based routing
│   │   ├── layout.tsx            # Root layout: providers stack (Redux → Environment → i18n → MUI)
│   │   ├── login/                # Login page (OAuth2 PKCE flow)
│   │   ├── dashboard/            # Protected area (requires auth token in cookie)
│   │   │   ├── layout.tsx        # Dashboard shell: Header + Sidebar + OemDealerErrorGuard
│   │   │   ├── page.tsx          # Dashboard home (analytics/indicators)
│   │   │   ├── claims/           # Claims list, details, create, timeline
│   │   │   ├── jobcard/          # Job card list, details, create, invoice
│   │   │   ├── appointment/      # Appointment list, details, calendar, create
│   │   │   ├── enquiry/          # Enquiry management
│   │   │   ├── booking/          # Vehicle booking list, details, create
│   │   │   ├── parts/            # Parts catalog, cart, orders, stock, drafts
│   │   │   ├── vehicles/         # Vehicle catalog and orders
│   │   │   ├── merchandise/      # Merchandise catalog and orders
│   │   │   ├── inwarding/        # GRN (Goods Receipt Notes)
│   │   │   ├── warranty/         # Warranty registration
│   │   │   ├── warrantylist/     # Warranty list view
│   │   │   ├── allotment/        # Vehicle allotment
│   │   │   ├── npqr/             # New Product Quality Reports
│   │   │   ├── invoices/         # Parts and vehicle invoicing
│   │   │   ├── notifications/    # Announcements management
│   │   │   ├── collateral/       # Marketing materials
│   │   │   ├── training/         # Dealer training content
│   │   │   ├── reports/          # Analytics reports
│   │   │   ├── uploads/          # Bulk upload history
│   │   │   ├── support/          # Salesforce support integration
│   │   │   └── ums-portal/       # User management portal (iframe)
│   │   └── api/                  # Next.js API routes (BFF layer)
│   │       ├── set-token/        # Store auth token in httpOnly cookie
│   │       ├── clear-token/      # Remove auth token cookie
│   │       ├── getEnvConfig/     # Serve runtime environment config to client
│   │       └── file/             # Document proxy (view files via backend)
│   │
│   ├── components/
│   │   ├── layouts/              # App-level layout components
│   │   │   ├── HeaderWrapper/    # Top navigation bar
│   │   │   ├── Sidebar/          # Navigation sidebar with menu items
│   │   │   └── Access/           # RBAC wrapper components (Access, AccessRoute)
│   │   ├── ui/                   # Feature-specific UI components (50+ folders)
│   │   │   ├── JobCardDetails/   # Example: component + hook + __tests__/
│   │   │   ├── ClaimDetails/
│   │   │   ├── Common/           # Shared UI patterns (OemDealerErrorGuard, etc.)
│   │   │   └── ...
│   │   └── Site24x7Script/       # RUM monitoring script injection
│   │
│   ├── services/                 # API service layer (one file per domain)
│   │   ├── auth.service.ts       # Login, token exchange, refresh, logout
│   │   ├── jobCard.service.ts    # Job card CRUD, invoice generation
│   │   ├── claim.service.ts      # Claims CRUD, bulk upload, download
│   │   ├── appointment.service.ts
│   │   ├── booking.service.ts
│   │   ├── enquiry.service.ts
│   │   ├── stocks.service.ts
│   │   ├── merchandise.service.ts
│   │   ├── invoice.service.ts
│   │   └── ...                   # 25 service files total
│   │
│   ├── store/                    # Redux Toolkit state management
│   │   ├── config/
│   │   │   ├── store.config.ts   # Store setup with redux-persist
│   │   │   └── storage.ts        # Storage adapter for persist
│   │   └── reducers/             # 20 Redux slices
│   │       ├── user/             # Auth state, permissions, DSE list
│   │       ├── dealer/           # Dealer info
│   │       ├── parts/            # Cart, catalog, orders, stock
│   │       ├── JobCard/          # Job card state
│   │       ├── Appointment/      # Appointment state
│   │       ├── claim/            # Claims + selectedItem sub-slice
│   │       ├── Enquiry/          # Enquiry + form data
│   │       ├── booking/          # Booking state
│   │       ├── Inwarding/        # GRN state
│   │       ├── Allotment/        # Allotment state
│   │       ├── merchandise/      # Merchandise orders
│   │       ├── invoice/          # Invoice state
│   │       ├── npqr/             # NPQR state
│   │       ├── MasterData/       # Shared master data (job types, service types, etc.)
│   │       ├── AppData/          # Global UI state (loading, toast)
│   │       ├── language/         # i18n language selection
│   │       └── pwa/              # PWA install prompt state
│   │
│   ├── providers/                # React context providers
│   │   ├── ReduxProvider.tsx     # Redux + PersistGate
│   │   ├── EnvironmentProvider.tsx # Loads runtime config, gates app until ready
│   │   ├── MUIProvider.tsx       # MUI ThemeProvider + locale
│   │   ├── OemDealerProvider.tsx # OEM vs Dealer context
│   │   ├── SessionExpiredProvider.tsx # Listens for session expiry events
│   │   └── ...
│   │
│   ├── constants/                # Application constants
│   │   ├── endpoint.constant.ts  # All API endpoint paths
│   │   ├── permissions.constant.ts # 150+ RBAC permission codes
│   │   ├── route.constant.ts    # Client-side route paths
│   │   ├── environment.constant.ts # EnvironmentConstants class (runtime config)
│   │   └── app.constant.ts      # Enums, user types, session events
│   │
│   ├── hooks/                    # Custom React hooks
│   ├── utils/                    # Utility functions
│   │   ├── api.ts               # Axios instance, interceptors, CRUD helpers
│   │   ├── errorHandler.ts      # Centralized error translation + toast dispatch
│   │   ├── config.ts            # Tenant site config (name, locale, currency)
│   │   ├── features.ts          # Auto-generated feature flags
│   │   └── ...
│   │
│   ├── i18n/                     # Internationalization setup
│   │   ├── i18n.ts              # i18next initialization with 5 languages
│   │   └── Provider.tsx         # I18nProvider component
│   │
│   ├── types/                    # TypeScript interfaces for domain entities
│   ├── styles/                   # Global + tenant-specific CSS
│   ├── pwa/                      # PWA install prompt, service worker registration
│   ├── libs/                     # Third-party library configurations
│   └── middleware.ts             # Auth guard, URL lowercase normalization
│
├── public/                       # Static assets
│   ├── locales/{en,fr,it,de,es}/ # Translation JSON files
│   └── assets/                   # Images, icons
│
├── __mocks__/                    # Global Jest mocks (uuid, shared package)
├── jest.config.ts                # Jest configuration (next/jest, 80% threshold)
├── jest.setup.ts                 # Global test setup (i18n, navigation, accessControl mocks)
├── next.config.ts                # Next.js config (basePath, CSP headers, image domains)
├── eslint.config.mjs             # ESLint flat config (next/core-web-vitals + typescript)
├── build-tenant.mjs              # Build script for tenant-specific output
└── dev-tenant.mjs                # Dev script for tenant-specific local dev
```

## shared/ (Reusable Library)

```
shared/
├── src/
│   ├── components/               # 50+ reusable UI components
│   │   ├── CommonTable/          # Data table with pagination, sorting, actions
│   │   ├── CardList/             # Mobile-friendly card layout
│   │   ├── CustomAccordion/      # Expandable sections
│   │   ├── CustomButton/         # Styled button variants
│   │   ├── CustomDrawer/         # Slide-out panels
│   │   ├── Filter/               # Filter bar with chips
│   │   ├── SearchBar/            # Search input with debounce
│   │   └── ...
│   ├── hooks/                    # Shared hooks (useDebounce, useAudioRecorder, useHeader)
│   ├── utils/                    # Shared utilities
│   │   ├── accessControl.ts     # hasPermission(permission, userPermissions)
│   │   ├── baseUtils.ts         # Date formatting, currency, common helpers
│   │   └── ...
│   ├── assets/svg/               # SVG source files
│   ├── generated-icon/           # SVGR-generated React icon components
│   └── index.ts                  # Package entry point
├── package.json                  # @shared/channel-partner-system (peer deps on React, Redux, Next)
└── jest.config.ts                # ts-jest preset (no Next.js dependency)
```

## Module Dependencies

```
┌─────────────────────────────────────────────────────┐
│                   app/ (pages)                       │
│  Uses: components, services, store, hooks, utils    │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌────────────┐
│ components/  │ │ services/│ │   store/   │
│ (UI layer)   │ │ (API)    │ │ (Redux)    │
└──────┬───────┘ └────┬─────┘ └─────┬──────┘
       │               │             │
       ▼               ▼             ▼
┌──────────────────────────────────────────┐
│           utils/ (api.ts, errorHandler)  │
│           constants/ (endpoints, perms)  │
│           @shared/channel-partner-system │
└──────────────────────────────────────────┘
```

**Key dependency rules:**
- Pages (`app/`) import components, call services, read from store
- Components import from `@shared/channel-partner-system`, use hooks, read store via selectors
- Services use `utils/api.ts` (Axios wrapper) and `constants/endpoint.constant.ts`
- Store slices call services in async thunks
- `errorHandler.ts` uses lazy `require()` for store to avoid circular dependency
- `api.ts` uses dynamic `import()` for store access in interceptors (same reason)

## Key Architectural Decisions

1. **Runtime config over build-time env vars** — Environment config is fetched from `/api/getEnvConfig` at startup. This allows the same Docker image to run in any environment without rebuilding.

2. **BFF pattern for auth** — Token is stored/cleared via internal Next.js API routes (`/api/set-token`, `/api/clear-token`) to keep httpOnly cookies server-side only.

3. **Provider composition in root layout** — Providers are stacked: Redux → PersistGate → EnvironmentProvider (gates until config loads) → OemDealer → i18n → MUI.

4. **Feature-per-folder components** — Each feature (JobCard, Claims, etc.) has its own folder under `components/ui/` containing the component, its custom hook, sub-components, and co-located `__tests__/`.

5. **Shared package as npm workspace** — `@shared/channel-partner-system` is a sibling workspace with its own build (TypeScript + SVGR). It exports components, hooks, utils, and icons. Consumed via `transpilePackages` in Next.js config.

6. **Redux-persist whitelist** — Only `user`, `pwa`, `selectedItem`, and `language` slices are persisted across page reloads. Other slices reset on refresh.

7. **Centralized error handling** — All API errors flow through `errorHandler.ts` which translates backend `messageKey` values via i18n (`BE_ERROR.*` namespace) and dispatches toast notifications via Redux.

8. **Middleware for auth + URL normalization** — Next.js middleware enforces authentication (cookie check) and lowercases all URLs before they reach page components.



## Tech Stack & Dependencies


# Tech — Stack, Conventions, Patterns & Operations

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 15.x |
| Language | TypeScript | 5.x |
| UI Library | React | 19.x |
| Component Library | MUI (Material UI) | 7.x |
| Styling | Tailwind CSS + CSS Modules + Emotion | 4.x |
| State Management | Redux Toolkit + redux-persist | 2.8.x |
| Forms | react-hook-form + Zod | 7.x / 4.x |
| HTTP Client | Axios | 1.16.x |
| Internationalization | i18next + react-i18next | 25.x |
| Date Handling | dayjs (with timezone/utc plugins) | 1.11.x |
| Calendar | FullCalendar | 6.x |
| PDF Generation | @react-pdf/renderer + pdf-lib | 4.x / 1.17.x |
| Charts | MUI X Charts | 8.x |
| Testing | Jest + @testing-library/react | 30.x / 16.x |
| Linting | ESLint (flat config) + Stylelint | 9.x |
| Build | next build (output: `dist/`) | — |
| Container | Docker (Node 25.9-alpine) | — |
| CI/CD | Azure DevOps Pipelines | — |
| Monitoring | Site24x7 RUM | — |

## Coding Conventions

### File Naming
- Components: `PascalCase.tsx` (e.g., `JobCardDetails.tsx`)
- Hooks: `use<Name>.tsx` (e.g., `useJobCardDetail.tsx`)
- Services: `<domain>.service.ts` (e.g., `claim.service.ts`)
- Store slices: `<domain>.slice.ts` (e.g., `user.slice.ts`)
- Constants: `<domain>.constant.ts` (e.g., `endpoint.constant.ts`)
- Interfaces: `<domain>.interface.ts` (e.g., `user.interface.ts`)
- Tests: `<SourceFile>.test.tsx` inside `__tests__/components/` or `__tests__/hooks/`

### Component Structure
Each feature component folder follows this pattern:
```
src/components/ui/<FeatureName>/
├── <FeatureName>.tsx              # Main component (presentational)
├── <FeatureName>.module.css       # Scoped styles (CSS Modules)
├── use<FeatureName>.tsx           # Custom hook (data fetching, business logic)
├── <SubComponent>/                # Sub-components in own folders
└── __tests__/
    ├── test-utils.tsx             # Mock store, renderWithProviders, mock data
    ├── components/<Name>.test.tsx
    └── hooks/use<Name>.test.ts
```

### TypeScript
- Strict mode enabled
- Interfaces for domain entities in dedicated `.interface.ts` files
- `@/` path alias for `src/` imports
- `@shared/channel-partner-system` for shared package imports
- Avoid `any` — use `eslint-disable` comment when unavoidable (legacy patterns)

### Imports
- Path aliases: `@/` → `src/`, `@shared/channel-partner-system` → `shared/src`
- Group order: React/Next → third-party → `@shared/` → `@/` (relative last)
- Services import endpoint constants, not hardcoded strings

### State Management
- One Redux slice per domain entity
- Async operations via `createAsyncThunk`
- Selectors via `createSelector` (memoized)
- Global loading state: dispatch `setIsLoading(true/false)` from `AppData` slice
- Toast notifications: dispatch `triggerToast(message, type)` from `AppData` slice
- Persisted slices (survive reload): `user`, `pwa`, `selectedItem`, `language`

### API Layer
- All HTTP calls go through `utils/api.ts` which exports `get`, `post`, `put`, `patch`, `del`, `postFile`
- Each function wraps calls with automatic loading state management
- Services are thin wrappers: call the appropriate HTTP method with the endpoint constant
- Response shape: `ApiResponse<T> = { status, statusCode, message, data, errors? }`
- File uploads use `postFile` with `multipart/form-data` content type

### Internationalization
- All user-facing strings use translation keys: `t('CLAIMS.STATUS_LABEL')`
- Translation files: `public/locales/{lang}/translations.json`
- Backend errors translated via `BE_ERROR.<messageKey>` namespace
- HTTP errors via `HTTP_ERRORS.GENERIC` fallback
- Language persisted in Redux + localStorage

## Patterns

### Authentication Flow
1. User lands on `/login` → redirected to UMS OAuth2 authorize endpoint with PKCE
2. UMS redirects back with auth code → `exchangeToken()` calls UMS token exchange API
3. Tokens (access + refresh) stored in Redux user slice + httpOnly cookie via `/api/set-token`
4. Axios request interceptor attaches `Authorization: Bearer <token>` + `X-Tenant-ID` header
5. On 401 → response interceptor attempts token refresh, queues concurrent requests
6. If refresh fails → dispatches `clearUser()`, fires `auth:sessionExpired` custom event
7. `SessionExpiredProvider` listens for event → shows expiry dialog → redirects to login

### RBAC Pattern
```tsx
// Element-level: hide/show based on permission
<Access permission="P_JC01">
  <Button>Create Job Card</Button>
</Access>

// Page-level: render Unauthorized if no permission
<AccessRoute permission="P_C06">
  <ClaimDetailsPage />
</AccessRoute>
```
- Permission check: `hasPermission(permCode, user.permissions)` — returns true if code is empty string or found in array

### Error Handling
```
API call fails
  → Axios interceptor rejects promise
  → Service catches error (or lets it propagate)
  → resolveApiError(error) in errorHandler.ts:
      1. Extracts response.data.messageKey
      2. Translates via i18n: t(`BE_ERROR.${messageKey}`)
      3. Falls back to t('HTTP_ERRORS.GENERIC')
      4. Dispatches toast notification (unless showToast=false)
      5. Returns translated error string
```
- `handleApiError()` returns `{ shouldThrow, errorMessage, errorCode, errorDetails }` for structured handling
- 401/403 errors set `shouldThrow: true` to signal auth issues
- Circular dependency with store avoided via lazy `require()` in errorHandler

### Loading State
- Global spinner controlled by `AppData.isLoading` in Redux
- `api.ts` `withLoading()` wrapper automatically sets loading true/false around API calls
- Components can opt out with `manageLoading: false` parameter on `post()`

### Responsive Design
- MUI `useMediaQuery` for breakpoint detection
- Desktop: `CommonTable` (data grid with pagination)
- Mobile: `CardList` (card-based layout with render props)
- Components handle both views in same file, switching on media query

### Form Handling
- `react-hook-form` for form state management
- `Zod` schemas for validation (via `@hookform/resolvers`)
- Form data often stored in dedicated Redux slice (e.g., `enquiryFormData.slice.ts`) for multi-step flows

## Testing

### Framework & Configuration
- Jest 30 with `next/jest` integration
- jsdom test environment
- V8 coverage provider with worker threads
- `resetMocks: true` — all mocks auto-reset between tests

### Coverage Requirements
- **80% minimum** for branches, functions, lines, and statements
- Collected from: `components/`, `hooks/`, `utils/`, `services/`, `store/`, `libs/`
- Excluded: `.interface.ts`, `.types.ts`, `.d.ts`, `__tests__/`, test files

### Test Commands
```bash
npm test                    # Run all tests
npm run test:watch          # Watch mode
npm run test:coverage       # Full coverage report
npm run test:sonar          # Coverage in lcov format for SonarQube
```

### Key Testing Patterns
- **renderWithProviders**: Custom render wrapping components in Redux Provider + MUI ThemeProvider
- **renderHookWithProvider**: Custom renderHook with Redux Provider wrapper
- **Mock services**: `jest.fn()` exported from test-utils, wired into `jest.mock()` factory
- **Mock shared components**: Simplified JSX with `data-testid` attributes; callback props invoked to exercise parent logic
- **Mock i18n**: `useTranslation` returns key as-is (`t(key) => key`)
- **Mock navigation**: `useRouter`, `usePathname`, `useSearchParams` from `next/navigation`
- **Mock MUI useMediaQuery**: Toggle between desktop/mobile in tests
- **UUID mock**: Global `__mocks__/uuid.js` to avoid ESM issues
- **CSS modules**: `identity-obj-proxy` returns class names as strings

### Global Setup (`jest.setup.ts`)
Pre-mocks three modules every test needs:
1. `@shared/channel-partner-system/src/utils/accessControl` → `hasPermission` returns true
2. `react-i18next` → `useTranslation` returns key passthrough
3. `next/navigation` → router/pathname/searchParams stubs

### Test File Organization
```
__tests__/
├── test-utils.tsx              # Mock store, renderWithProviders, mock data, service mocks
├── hooks-test-utils.tsx        # renderHookWithProvider (optional)
├── components/
│   └── <Component>.test.tsx    # Component tests
└── hooks/
    └── use<Hook>.test.ts       # Hook tests
```

## Deployment

### Docker Build
```dockerfile
FROM node:25.9.0-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
COPY channel-partner-system ./channel-partner-system
COPY shared ./shared
COPY runtime-assets ./runtime-assets
RUN npm ci --ignore-scripts && npm run build:shared && npm run build:cps
EXPOSE 3000
USER norton
CMD ["npm", "start", "--workspace", "channel-partner-system"]
```
- Single image serves all environments (config loaded at runtime)
- Non-root user (`norton`) for security
- Build order: shared package first, then CPS app

### CI/CD (Azure DevOps)
- **CI Pipeline**: Triggered on push to main/dev → SonarQube scan → Docker build → push to registry
- **CD Pipeline**: Triggered by successful CI → deploy via Helm chart to Kubernetes
- **Environments**: dev → UAT (manual approval) → prod (manual approval)
- **Tenants**: Separate deployments for norton-uk and norton-us

### Environment Configuration
Runtime config loaded from `/api/getEnvConfig` (internal Next.js route that reads server-side env vars):
- `NEXT_PUBLIC_API_BASE_URL` — Backend API base URL
- `NEXT_PUBLIC_DOMAIN_NAME` — Frontend domain
- `NEXT_APP_TENANT` — Active tenant (norton-uk, norton-us)
- `RUNTIME_ASSETS_BASE_URL` — External assets server URL
- `NEXT_PUBLIC_UMS_AUTH_SERVICE_URL` — UMS authentication service
- `NEXT_PUBLIC_APPLICATION_ID` / `APPLICATION_KEY` — OAuth2 app credentials
- `NEXT_PUBLIC_ENV` — Environment name (dev, uat, training, prod)
- `NEXT_PUBLIC_SALESFORCE_SUPPORT_URL` — Salesforce integration URL

### Security Headers (next.config.ts)
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy` — restrictive CSP with explicit allowlists
- `Permissions-Policy` — camera/microphone/geolocation restricted

### PWA Support
- Service worker for offline caching
- Web push notifications via `web-push` library
- Tenant-specific manifest.json and splash screens
- Install prompt managed via Redux `pwa` slice

