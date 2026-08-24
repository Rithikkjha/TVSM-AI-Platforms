# qrcode-frontend


## Product Context


# Product Overview

## What This Service Does

QR Generator is a frontend application for TVS Motor Company that enables internal teams to create, manage, and track QR codes across global and regional markets. It supports two QR modes:

- **Trackable QR (Dynamic):** Encodes a short URL (e.g. `https://qr.tvsmotor.com/r/{code}`) that redirects to a configurable destination. Scans are tracked for analytics.
- **Static QR (Direct):** Encodes the target URL directly into the QR code. No redirect, no scan tracking, and the destination cannot be changed after creation.

The application provides three core workflows: Generate (design and save QR codes), Library (browse, filter, and manage saved QR codes), and Analytics (view scan metrics for trackable QR codes).

## Domain Entities

### QR Code
The central entity. Key attributes:
- `shortCode` — unique identifier for trackable QR codes
- `targetUrl` / `redirectUrl` — the destination URL
- `svgBlobPath` / `svgUrl` — stored SVG asset location
- `status` — lifecycle state: `ACTIVE`, `INACTIVE`, `PAUSED`, `ARCHIVED`, `EXPIRED`, `SCHEDULED`
- `documentId` — backend persistence identifier

### Scope
Defines the geographic/market applicability of a QR code:
- **GLOBAL** — applies across all markets; optionally tagged with a `marketTag` (e.g. `IB`, `DOMESTIC`)
- **REGION** — scoped to a specific region cluster (`MECIS`, `AFRICA`, `APAC`, `EU`, `LATAM`, `NA`) and optionally a country within that region

### Subject
Categorizes what the QR code represents:
- `subjectType` — one of `MODEL` (Vehicle Model), `BRAND` (Brand/Showroom), `CAMPAIGN` (Campaign/Promotion), `PRODUCT` (Accessory/Spare Part), `OTHER`
- `subjectKey` — slugified name identifier (e.g. `apache-rtr-160`)

### Logo
Embeddable logo metadata from a backend library:
- `id`, `name`, `url`, `recommendedScale`
- Scoped by `subjectType`, `subjectKey`, and `Scope`
- Special values: "Default Logo" (backend TVS fallback) and "none" (no logo embedded)

### User / Auth
- Roles: `SUPER_ADMIN`, `ADMIN`, `USER`
- Users have a `regionGroup` that determines library visibility
- JWT-based auth with access + refresh tokens

## Integrations

| Integration | Protocol | Purpose |
|---|---|---|
| QR Backend API (`/api/qr/*`) | REST/HTTP | Generate SVG previews, save QR codes, download SVGs |
| QR Create API (`/api/qr-create/*`) | REST/HTTP | Dynamic (trackable) QR preview and save with shortcode creation |
| QR Library API (`/api/qr-library/*`) | REST/HTTP | Role-scoped paginated listing, redirect URL updates, status updates |
| Auth API (`/api/auth/*`) | REST/HTTP | Login, logout, token refresh, user info, auth config |
| Analytics API (`/api/analytics/*`) | REST/HTTP | Summary stats, top QR codes by scans, scan timeline |
| Logos API (`/api/v1/logos`) | REST/HTTP | List available logos for embedding |
| Short Domain (`qr.tvsmotor.com`) | HTTP redirect | Runtime redirect for trackable QR codes (not called by frontend) |

The backend base URL is configured via `VITE_API_BASE` (defaults to `http://localhost:8084`).

## Business Rules

1. **Auth gating:** When `authEnabled` is true (from `/api/auth/config`), users must authenticate before accessing any functionality. When false, the app operates without login.
2. **Token lifecycle:** Access tokens are stored in localStorage. On 401 responses, the app attempts a silent refresh using the stored refresh token. If refresh fails, the user is logged out and the page reloads.
3. **Scope validation:** GLOBAL scope must not have `regionCode` or `countryCode`. REGION scope requires `regionCode` and must not have `marketTag`.
4. **Subject key slugification:** The `subjectKey` is auto-slugified on blur (lowercase, hyphens, no special chars).
5. **Preview-before-save:** Users must generate a preview before saving. The preview shortcode (for dynamic mode) is reused on save so the final QR is identical to what was previewed.
6. **Library role scoping:** The library endpoint returns QR codes filtered by the user's role and region group. Users can filter by "all" (role-scoped) or "mine only".
7. **Redirect URL immutability for static QR:** Only trackable (redirect-based) QR codes allow updating the redirect URL post-creation. Static QR codes encode the URL directly and cannot be changed.
8. **Analytics scope:** Analytics data is only available for trackable QR codes. Static QR codes do not generate scan data.
9. **Logo selection:** "Default Logo" uses the backend's TVS fallback. "No Logo" explicitly omits any logo. Library logos are fetched from the backend and include a recommended scale.
10. **Pagination:** The UI uses 0-based page indexing internally but converts to 1-based when calling the backend.



## Code Structure


# Project Structure

## Directory Layout

```
qrcode-frontend/
├── .kiro/steering/          # Kiro steering files (product, structure, tech)
├── public/
│   ├── QrCode.svg           # App favicon / logo asset
│   └── vite.svg             # Vite default asset (unused)
├── src/
│   ├── main.tsx             # Entry point — renders <AuthProvider><App/></AuthProvider>
│   ├── App.tsx              # Root component — header, tab navigation, auth gating
│   ├── config.ts            # Runtime config from Vite env vars (apiBase, shortDomain, env)
│   ├── api.ts               # All backend API calls (auth, QR CRUD, library, analytics, logos)
│   ├── types.ts             # Shared TypeScript types and interfaces for domain entities
│   ├── utils.ts             # Small pure utilities (slugify, clipboard, JSON parse)
│   ├── auth/
│   │   └── AuthProvider.tsx # React context for auth state, token refresh, apiFetch wrapper
│   ├── components/
│   │   ├── AuthGate.tsx     # Login gate UI — credential form shown when auth is required
│   │   └── LogoPicker.tsx   # Logo selection widget (default / pick from library / no logo)
│   ├── pages/
│   │   ├── Generate.tsx     # QR design form — preview + save workflow with Zod validation
│   │   ├── Library.tsx      # Paginated QR library — search, filter, edit redirect/status
│   │   └── Analytics.tsx    # Scan analytics — summary cards, timeline chart, top QR table
│   ├── styles.css           # Primary stylesheet — all component and layout styles
│   ├── styles/
│   │   └── tabs.css         # Tab navigation styles (duplicates some rules from styles.css)
│   ├── index.css            # Vite scaffold base styles (mostly overridden by styles.css)
│   ├── App.css              # Vite scaffold styles (mostly unused, overridden)
│   └── assets/
│       └── react.svg        # Vite scaffold asset (unused)
├── index.html               # SPA shell — mounts #root
├── vite.config.ts           # Vite config — React plugin only
├── tsconfig.json            # TS project references (app + node)
├── tsconfig.app.json        # App TS config — strict, ES2022, bundler resolution
├── tsconfig.node.json       # Node TS config (for vite.config.ts)
├── eslint.config.js         # Flat ESLint config — TS + React Hooks + React Refresh
├── package.json             # Dependencies, scripts, engine constraints
├── Dockerfile               # Multi-stage: node build → nginx serve
├── docker-compose.yml       # Single-service compose for the frontend container
├── nginx.conf               # SPA fallback + static asset caching
└── .dockerignore / .gitignore
```

## Module Dependencies

```
main.tsx
  └── AuthProvider (context)
       └── App.tsx
            ├── AuthGate (login UI)
            ├── Generate (page)
            │    ├── api.ts (generateQr, generateQrDynamic, saveQr, saveQrDynamic, ...)
            │    ├── LogoPicker (component)
            │    │    └── api.ts (listLogos)
            │    ├── types.ts
            │    ├── utils.ts (slugify, safeJsonParse, copyToClipboard)
            │    └── config.ts
            ├── Library (page)
            │    ├── api.ts (listQrLibrary, updateRedirectUrl, updateQrStatus)
            │    ├── types.ts
            │    └── config.ts
            └── Analytics (page)
                 └── api.ts (fetchAnalyticsSummary, fetchTopQrCodes, fetchTimeline)
```

All API calls flow through `api.ts`, which uses `apiFetch` from `AuthProvider.tsx` for automatic 401 → refresh → retry handling.

## Architectural Decisions

1. **Single-page app with tab navigation (no router).** The app uses a simple `useState<Tab>` to switch between Generate, Library, and Analytics. There is no client-side routing library — all views live under the same URL path.

2. **Auth as a React context wrapping the entire tree.** `AuthProvider` sits above `App` and exposes user state, login/logout actions, and a config flag. The `apiFetch` utility handles token injection and silent refresh globally.

3. **Centralized API module.** All HTTP calls are in `src/api.ts`. This keeps network logic out of components and makes it easy to update endpoints or add headers in one place.

4. **Form validation with Zod + react-hook-form.** The Generate page uses a Zod schema with `superRefine` for cross-field validation (scope ↔ region/market constraints). The resolver bridges Zod into react-hook-form.

5. **Preview-then-save two-step flow.** Generate calls a preview endpoint (returns SVG only, no persistence) and displays it as a Blob URL. Save is a separate action that persists to the backend. For dynamic mode, the preview also allocates a shortcode that is reused on save.

6. **No state management library.** State is local to each page component or lifted to AuthProvider context. There is no Redux, Zustand, or similar.

7. **CSS-only styling (no CSS-in-JS, no utility framework).** A single `styles.css` file contains all custom styles using CSS custom properties. No Tailwind, no styled-components.

8. **Docker deployment with nginx.** The production build is a static bundle served by nginx with SPA fallback (`try_files $uri /index.html`) and 30-day cache headers for hashed assets.

9. **Environment-driven configuration.** `VITE_API_BASE`, `VITE_SHORT_DOMAIN`, and `VITE_ENV` are injected at build time via Vite's `import.meta.env`. Docker build args pass these through.

10. **Country lists are frontend-provided.** The region → country mapping lives in `Generate.tsx` as a static constant rather than being fetched from the backend.



## Tech Stack & Dependencies


# Tech Stack & Conventions

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | 5.5.4 |
| UI Framework | React | 18.3.1 |
| Build Tool | Vite | 5.4.10 |
| Form Management | react-hook-form | 7.53.0 |
| Schema Validation | Zod | 3.23.8 |
| Form Resolver | @hookform/resolvers | 3.9.0 |
| Icons | lucide-react | 0.454.0 |
| Linting | ESLint (flat config) | typescript-eslint + react-hooks + react-refresh |
| Styling | Plain CSS with custom properties | — |
| Production Server | nginx (Alpine) | latest |
| Containerization | Docker (multi-stage) | node:18-alpine → nginx:alpine |
| Node Runtime | Node.js | >=18 <20.19 |

## Coding Conventions

### TypeScript
- Strict mode enabled (`strict: true`, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`)
- Target ES2022 with bundler module resolution
- `verbatimModuleSyntax: true` — use `import type` for type-only imports
- No class fields emit (`useDefineForClassFields: true`)
- JSX transform: `react-jsx` (no manual React import needed)

### Component Patterns
- Functional components only (no class components)
- Default exports for page and provider components
- Named exports for hooks (`useAuth`) and utilities
- Props destructured in function signature
- `type` keyword for component prop types (not `interface` unless extending)

### File Naming
- Components and pages: PascalCase (e.g. `AuthGate.tsx`, `Generate.tsx`)
- Utilities and config: camelCase (e.g. `api.ts`, `config.ts`, `utils.ts`)
- Style files: camelCase (e.g. `styles.css`, `tabs.css`)
- One component per file for pages and shared components

### State Management
- `useState` for local component state
- `useRef` for mutable values that don't trigger re-renders (timers, blob URLs, shortcodes)
- `useCallback` for stable function references passed as props or in dependency arrays
- React Context (`createContext` + `useContext`) for cross-cutting concerns (auth only)
- No external state libraries

### Forms
- `react-hook-form` with `zodResolver` for the Generate form
- Zod schemas define validation rules including cross-field constraints via `superRefine`
- `register` for simple inputs, `watch` for reactive field values, `setValue` for programmatic updates
- Error messages rendered inline below fields

### Styling
- Single global `styles.css` with CSS custom properties (`:root` variables)
- Dark theme by default (no light mode toggle)
- BEM-ish class naming without strict methodology (e.g. `.card-h`, `.card-b`, `.auth-gate-pill`)
- Responsive breakpoints at 960px and 720px using `@media`
- `clamp()` for fluid padding
- Inline styles used sparingly in components for one-off layout (grid columns, gaps)

## Patterns

### API Communication
- All API functions live in `src/api.ts`
- Each function constructs the full URL using `CONFIG.apiBase`
- `apiFetch` (from AuthProvider) wraps native `fetch` with:
  - Automatic `Authorization: Bearer <token>` header injection
  - 401 interception → silent token refresh → retry
  - On refresh failure: clear localStorage, reload page
- FormData used for QR generation/save endpoints (supports file-like payloads)
- JSON used for auth and simple CRUD endpoints
- Error handling: check `res.ok`, parse error body, throw `Error` with message

### Authentication Flow
1. On mount, `AuthProvider` fetches `/api/auth/config` to determine if auth is enabled
2. If a token exists in localStorage, validates via `/api/auth/me`
3. On 401 from `/me`, attempts refresh via `/api/auth/refresh`
4. Credential login posts to `/api/auth/login`, stores both access and refresh tokens
5. Token-based login (from URL callback `?token=xxx`) stores the token and triggers `/me` validation
6. Logout calls `/api/auth/logout` then clears localStorage

### Data Fetching
- No query caching library (no React Query, SWR, etc.)
- Pages fetch data on mount and when the tab becomes active (`active` prop)
- Loading states managed with `useState<boolean>`
- Cleanup via `cancelled` flag pattern in useEffect to prevent state updates on unmounted components

### Toast Notifications
- Simple `useState<string>` + `setTimeout` pattern for transient messages
- Fixed-position `.toast` element toggled via `.show` class
- Auto-dismiss after 1.4–2 seconds

## Error Handling

- API errors: caught in try/catch, displayed via toast or inline error state
- Form validation errors: rendered inline via react-hook-form's `formState.errors`
- Auth errors: 401 triggers silent refresh; on failure, clears state and reloads
- Network failures: caught generically, shown as toast messages
- No global error boundary component
- No Sentry or external error reporting integration
- `console.warn` used for non-critical failures (auth config fetch, logout request)

## Testing

- **No test framework is currently configured.** There are no test files, no test runner in `package.json`, and no testing libraries in dependencies.
- If adding tests, use Vitest (natural fit with Vite) + React Testing Library for component tests.

## Deployment

### Build
```bash
npm ci              # Install exact dependencies from lockfile
tsc -b              # Type-check (may be skipped in Docker due to TS version issues)
vite build          # Bundle to dist/
```

### Docker
- Multi-stage build: `node:18-alpine` for building, `nginx:alpine` for serving
- Build args: `VITE_API_BASE`, `VITE_ENV` (injected at build time, baked into bundle)
- The Dockerfile skips `tsc` and runs `npx vite build` directly (noted in comment)
- Output served from `/usr/share/nginx/html`

### nginx Configuration
- Listens on port 80
- SPA fallback: `try_files $uri $uri/ /index.html`
- Static assets (js, css, images, fonts): 30-day cache with `immutable` header
- Container exposed on port 3000 via docker-compose

### Environment Variables
| Variable | Purpose | Default |
|---|---|---|
| `VITE_API_BASE` | Backend API base URL | `http://localhost:8084` |
| `VITE_SHORT_DOMAIN` | Short URL domain for display | `https://qr.tvsmotor.com` |
| `VITE_ENV` | Environment label shown in UI | `UAT` |

### Scripts
| Script | Command | Purpose |
|---|---|---|
| `dev` | `vite` | Local dev server with HMR |
| `build` | `tsc -b && vite build` | Type-check + production bundle |
| `lint` | `eslint .` | Run ESLint across all files |
| `preview` | `vite preview` | Preview production build locally |

