# TVS-CPS-FE-BASE-FRAMEWORK


## Product Context


# Product: Channel Partner System (CPS)

## What This Service Does

A multi-tenant web application for managing channel partner operations at TVS Motor Company. It provides role-based access to business workflows (currently claims management) for different partner types — distributors and OEMs — across multiple regional brands/tenants.

## Domain Entities

### User
- Properties: `id`, `email`, `name`, `role`, `permissions[]`
- Roles: `distributor`, `oem`
- Stored in Redux (persisted to localStorage across reloads)

### Permission
- Enum values: `view_claims`, `create_claims`, `review_claims`
- Drives both UI element visibility and page-level access gating

### Tenant
- Represents a brand/region deployment (e.g. `norton-uk`, `norton-us`)
- Each tenant has its own: CSS variables, logo, feature flags, PWA manifest, icons
- Configured in `tenant.config.mjs`, resolved at build/dev time via `NEXT_APP_TENANT` env var

### Claims
- Primary business entity — partners can view, create, and review/approve claims
- Access governed by permissions per role

### Features
- Feature flags per tenant (e.g. `header`, `footer`, `sidebar`)
- Auto-generated from tenant config at build time into `src/utils/features.ts`

## Integrations

| Integration | Mechanism | Details |
|---|---|---|
| Backend API | Axios HTTP client | Base URL from `NEXT_PUBLIC_API_BASE_URL`; supports GET/POST/PUT/PATCH/DELETE with credentials |
| Authentication | JWT in httpOnly cookies | Token set/cleared via internal Next.js API routes (`/api/set-token`, `/api/clear-token`) |
| Runtime Assets Server | Fetch at build time | Tenant CSS, logo, config.json, features.json fetched from `RUNTIME_ASSETS_BASE_URL` |
| PWA | Service worker + web-push | Per-tenant manifests, push notification subscription via server actions |
| i18n | react-i18next | Client-side translations, English and French supported, locale from tenant config |

## Business Rules

1. **Authentication is mandatory** — middleware redirects unauthenticated users to `/login`; authenticated users on `/login` or `/` are redirected to `/dashboard`.
2. **RBAC at two levels:**
   - **Element-level** — `<Access permission="...">` hides/shows buttons and UI elements
   - **Page-level** — `<AccessRoute permission="...">` renders an Unauthorized page if the user lacks the required permission
3. **Permissions are additive** — `hasPermission` checks if the permission string exists in the user's permissions array; an empty permission string grants access to everyone.
4. **Tenant isolation** — each tenant gets its own styling, features, logo, and PWA config; the tenant is fixed at build/dev time.
5. **URLs are case-insensitive** — middleware normalizes all paths to lowercase.
6. **Feature flags control layout** — header, footer, and sidebar visibility are driven by the tenant's `features.json`.



## Code Structure


# Structure: Annotated Directory Layout

## Monorepo Layout

```
TVS-CPS-FE-BASE-FRAMEWORK/
├── package.json                    # Root workspace config (npm workspaces)
├── .gitignore
├── README.md
│
├── channel-partner-system/         # Main Next.js application
│   ├── package.json                # App dependencies & tenant-specific scripts
│   ├── tsconfig.json               # TypeScript config with path aliases
│   ├── next.config.ts              # Next.js config (transpilePackages, webpack hooks)
│   ├── jest.config.ts              # Jest config (covers both app + shared)
│   ├── jest.setup.ts               # Test setup (Testing Library matchers)
│   ├── .eslintrc.json              # ESLint (next/core-web-vitals + next/typescript)
│   ├── postcss.config.mjs          # PostCSS with Tailwind
│   ├── i18next-parser.config.js    # i18n string extraction config
│   ├── tenant.config.mjs           # Tenant registry (list + default)
│   ├── build-tenant.mjs            # Production build script (sets tenant, runs next build)
│   ├── dev-tenant.mjs              # Dev server script (sets tenant, optional PWA/HTTPS)
│   │
│   ├── scripts/
│   │   └── build-tools.ts          # Fetches tenant assets (CSS, logo, config, features) from runtime server
│   │
│   ├── public/
│   │   ├── common/                 # Shared static assets (user avatar)
│   │   ├── locales/                # i18n translation JSON files (en, fr)
│   │   ├── sw.js                   # Service worker for PWA
│   │   └── tenants/                # Per-tenant PWA manifests & icons
│   │       ├── norton-uk/
│   │       └── norton-us/
│   │
│   └── src/
│       ├── middleware.ts           # Auth guard + URL lowercase normalization
│       ├── app/                    # Next.js App Router (file-based routing)
│       │   ├── layout.tsx          # Root layout (fonts, providers, PWA)
│       │   ├── page.tsx            # Root page (redirects via middleware)
│       │   ├── loading.tsx         # Global loading state
│       │   ├── global-error.tsx    # Global error boundary
│       │   ├── api/                # Internal API routes (server-side)
│       │   │   ├── set-token/      # POST: stores JWT in httpOnly cookie
│       │   │   └── clear-token/    # POST: removes JWT cookie
│       │   ├── login/              # Login page (client component)
│       │   └── dashboard/          # Protected area
│       │       ├── layout.tsx      # Dashboard layout (header, footer, sidebar)
│       │       ├── page.tsx        # Dashboard home
│       │       └── claims/         # Claims feature page
│       │
│       ├── components/
│       │   ├── layouts/            # App-specific layout wrappers (HeaderWrapper)
│       │   ├── tenants/            # Tenant-specific component overrides
│       │   │   └── norton/layouts/ # Norton-specific layout components
│       │   └── ui/                 # App-level UI components (RouteLoader)
│       │
│       ├── i18n/                   # i18next initialization & React provider
│       ├── providers/              # ReduxProvider (with PersistGate)
│       ├── pwa/                    # PWA install prompt, push notifications, server actions
│       ├── server/                 # Server-only utilities (runtime config fetching)
│       ├── styles/
│       │   ├── style.css           # Main stylesheet (imports Tailwind + variables)
│       │   └── variable.css        # AUTO-GENERATED: tenant CSS variables
│       ├── utils/
│       │   ├── config.ts           # AUTO-GENERATED: tenant config (siteName, locales, etc.)
│       │   ├── features.ts         # AUTO-GENERATED: tenant feature flags
│       │   └── routes.ts           # AUTO-GENERATED: route definitions
│       └── assets/
│           └── logo.svg            # AUTO-GENERATED: tenant logo
│
└── shared/                         # Shared library (@shared/channel-partner-system)
    ├── package.json                # Peer deps, build scripts (tsc + svgr)
    ├── tsconfig.json
    └── src/
        ├── index.ts                # Barrel export (re-exports all modules)
        ├── api/                    # Axios HTTP client (get, post, put, patch, del)
        ├── assets/svg/             # Source SVG icons
        ├── generated-icons/        # AUTO-GENERATED: React components from SVGs (via @svgr/cli)
        ├── components/             # Reusable UI components
        │   ├── Access/             # Element-level RBAC wrapper
        │   ├── AccessRoute/        # Page-level RBAC wrapper
        │   ├── Button/             # Generic button
        │   ├── DebouncedSearchInput/ # Search with debounce
        │   ├── Footer/             # App footer
        │   ├── Header/             # App header with navigation
        │   ├── Select/             # Dropdown select
        │   ├── Sidebar/            # Navigation sidebar
        │   └── Unauthorized/       # 403 fallback page
        ├── hooks/                  # Custom React hooks (useDebounce)
        ├── services/               # Auth service (setToken, clearToken, mock users)
        ├── store/                  # Redux Toolkit store
        │   ├── config/             # Store configuration + persist setup
        │   └── reducers/user/      # User slice (setUser, clearUser, getUser selector)
        └── utils/                  # Utilities
            ├── accessControl.ts    # hasPermission helper
            └── permissions.ts      # Permission enum
```

## Module Dependencies

```
channel-partner-system
  └── @shared/channel-partner-system (via TypeScript path alias + transpilePackages)
        ├── @reduxjs/toolkit + redux-persist (state)
        ├── react-redux (bindings)
        ├── react-i18next + i18next (i18n)
        ├── axios (HTTP)
        └── next, react, react-dom (peer deps)
```

- The `shared` package declares framework libraries as **peer dependencies** — the app provides the actual versions.
- The app imports from `@shared/channel-partner-system` which resolves to `../shared/src` via `tsconfig.json` paths.
- Next.js `transpilePackages` ensures the shared source is compiled alongside the app.

## Architectural Decisions

| Decision | Rationale |
|---|---|
| **npm workspaces monorepo** (no Turborepo/Lerna) | Simplicity; only two packages with a clear dependency direction |
| **Shared package as source (not published)** | Path alias resolves directly to TypeScript source; no separate build step needed during dev |
| **Tenant config at build time** | CSS variables, feature flags, and config are baked in per build; avoids runtime tenant switching complexity |
| **Runtime Assets Server** | Decouples tenant branding from code deploys; designers can update CSS/logos independently |
| **Auto-generated files** | `config.ts`, `features.ts`, `variable.css`, `routes.ts`, `logo.svg` are generated from external sources — never edit manually |
| **Redux Persist for user state** | Survives page reloads without re-authentication; only the `user` slice is whitelisted |
| **Middleware-based auth** | Server-side redirect before page render; no flash of unauthorized content |
| **RBAC via components** | Declarative permission checks in JSX; keeps business logic out of page components |
| **Barrel exports everywhere** | Every module folder has an `index.ts`; enables clean imports from `@shared/channel-partner-system` |
| **Separate interface files** | Component interfaces live in `*.interface.ts` files alongside the component |
| **PWA per tenant** | Each tenant has its own manifest.json and icons in `public/tenants/<name>/` |



## Tech Stack & Dependencies


# Tech: Stack, Conventions & Practices

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Framework | Next.js (App Router) | 15.3.5 |
| Language | TypeScript | 5.x |
| UI Library | Material UI (`@mui/material`) | 7.2.0 |
| Styling | Tailwind CSS + PostCSS + tenant CSS variables | 4.x |
| State Management | Redux Toolkit + Redux Persist | RTK 2.8, persist 6.0 |
| HTTP Client | Axios | 1.11 |
| i18n | react-i18next / i18next | 15.6 / 25.3 |
| PWA | next-pwa + web-push | 5.6 / 3.6 |
| Fonts | Google Fonts (Geist, Geist Mono) | — |
| Route Loading | nextjs-toploader | 3.8 |
| Monorepo | npm workspaces | — |
| SVG Icons | @svgr/cli (SVG → React components) | 8.x |

## Coding Conventions

### File & Folder Naming
- **Pages/routes**: lowercase folder names matching URL segments (`dashboard/claims/page.tsx`)
- **Components**: PascalCase filenames (`HeaderWrapper.tsx`, `InstallPrompt.tsx`)
- **Interfaces**: separate `*.interface.ts` file per component (e.g. `Access.interfact.ts`, `Button.interface.ts`)
- **Barrel exports**: every module folder has an `index.ts` re-exporting its public API
- **Auto-generated files**: marked with `/*AUTO GENERATED FILE - NO DOT UPDATE THIS FILE*/` — never edit manually

### Component Patterns
- Use `"use client"` directive only on components that need browser APIs or interactivity
- Server components are the default (no directive needed)
- Props defined via dedicated interface files, not inline
- RBAC wrapped declaratively: `<Access permission="...">` for elements, `<AccessRoute permission="...">` for pages

### Imports
- Path alias `@/*` resolves to `./src/*` within the app
- Path alias `@shared/channel-partner-system` resolves to `../shared/src`
- Import from the shared package barrel: `import { Access, Button, setUser } from "@shared/channel-partner-system"`
- Prefer named exports; default exports only for Next.js page/layout conventions

### TypeScript
- Strict mode enabled
- `noEmit: true` (Next.js handles compilation)
- Target: ES2017
- Module resolution: bundler

### State Management
- One Redux slice per domain entity (currently: `user`)
- Use `createSlice` + `createSelector` from RTK
- Persist config whitelists specific slices (currently: `['user']`)
- SSR-safe storage (noop on server, localStorage on client)

### Styling
- Tailwind utility classes for layout and spacing
- Tenant-specific CSS variables in `variable.css` (auto-generated)
- MUI theme customization via Emotion (`@emotion/react`, `@emotion/styled`)
- Global styles in `src/styles/style.css`

## Error Handling

| Layer | Strategy |
|---|---|
| API calls | Axios wrapper catches errors, logs to console, returns `null` on failure |
| POST errors | Distinguishes HTML responses, timeouts (`ECONNABORTED`), and 5xx errors; returns error object |
| Global UI | `global-error.tsx` error boundary at app root |
| Auth failures | Middleware redirects to `/login` (no token = unauthenticated) |
| Permission denied | `<AccessRoute>` renders `<Unauthorized />` component |

### API Error Flow
```
Request → Axios interceptor (withCredentials) → Success: return data
                                              → Failure: handleApiError()
                                                  ├── Response error → log response data
                                                  ├── Request error → log request details
                                                  └── Setup error → log message
```

## Testing

| Aspect | Detail |
|---|---|
| Framework | Jest 30 + jsdom |
| Component testing | React Testing Library (`@testing-library/react`) |
| Coverage tool | V8 provider |
| Coverage thresholds | 80% branches, functions, lines, statements |
| Test scope | Both `channel-partner-system` and `shared/src` (configured via `roots`) |
| CSS mocking | `identity-obj-proxy` |
| Setup file | `jest.setup.ts` (Testing Library matchers) |
| Run command | `npm run test` (single run) or `npm run test:watch` (watch mode) |
| Mocks | `resetMocks: true` — all mocks reset between tests |

### Test File Conventions
- Test files co-located with source or in `__tests__/` directories
- Name pattern: `*.test.ts` or `*.test.tsx`
- Module aliases mapped in Jest config to match tsconfig paths

## Deployment & Build

### Build Process
1. Set `NEXT_APP_TENANT` environment variable (e.g. `norton-uk`)
2. `build-tenant.mjs` validates tenant against registry, runs `next build`
3. `scripts/build-tools.ts` fetches tenant assets from `RUNTIME_ASSETS_BASE_URL`:
   - `variable.css` → `src/styles/variable.css`
   - `logo.svg` → `src/assets/logo.svg`
   - `config.json` → `src/utils/config.ts`
   - `features.json` → `src/utils/features.ts`
4. Output directory: `dist/`

### Dev Process
1. `dev-tenant.mjs` sets tenant, starts `next dev`
2. Optional `pwa` flag enables `--experimental-https` for service worker testing
3. Webpack plugin triggers `generateTenantConfigFiles()` on first compile

### Environment Variables
| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL |
| `NEXT_PUBLIC_DOMAIN_NAME` | Frontend app base URL |
| `NEXT_APP_TENANT` | Active tenant identifier |
| `RUNTIME_ASSETS_BASE_URL` | Server hosting tenant config/assets |

### Scripts Reference
| Script | Description |
|---|---|
| `npm run dev:norton-uk` | Dev server for norton-uk tenant |
| `npm run dev:norton-us` | Dev server for norton-us tenant |
| `npm run dev:norton-uk:pwa` | Dev server with HTTPS for PWA testing |
| `npm run build:norton-uk` | Production build for norton-uk |
| `npm run test` | Run all tests (app + shared) |
| `npm run test:watch` | Run tests in watch mode |
| `npm run lint` | ESLint check |
| `npm run i18n:extract` | Extract translation keys from source |
| `npm run build:shared` | Build shared package (tsc + svgr) |

### Adding a New Tenant
1. Add tenant name to `tenants` array in `tenant.config.mjs`
2. Create `public/tenants/<name>/` with `manifest.json` and `icons/`
3. Ensure runtime assets server has `tenants/<name>/` with `config.json`, `features.json`, `variable.css`, `logo.svg`
4. Add dev/build scripts to `package.json`

