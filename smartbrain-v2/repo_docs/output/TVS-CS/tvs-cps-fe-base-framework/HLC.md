---
service_id: tvs-cps-fe-base-framework
doc_type: hlc
last_reviewed: 2026-10-11
---

# TVS-CPS-FE-BASE-FRAMEWORK — High-Level Code

## Application Overview
tvs-cps-fe-base-framework is an npm workspaces monorepo (`package.json` workspaces `channel-partner-system`, `shared`); the app entry is Next.js App Router `channel-partner-system/src/app/layout.tsx` / `page.tsx`. Artifact `@shared/channel-partner-system` 1.0.0 (npm).

## Module Summary
tvs-cps-fe-base-framework modules:

| Module | Path | Responsibility |
|---|---|---|
| App | `channel-partner-system/src/app` | Pages (login, dashboard) and API routes (set-token, clear-token) |
| Middleware | `channel-partner-system/src/middleware.ts` | Auth redirect guard |
| Server | `channel-partner-system/src/server` | Runtime tenant config fetch |
| Build scripts | `channel-partner-system/scripts` | Tenant asset download at build |
| Shared services | `shared/src/services` | auth.service (set/clear token) |
| Shared store | `shared/src/store` | Redux toolkit store/reducers |
| Runtime assets | `runtime-assets/tenants` | norton-uk, norton-us tenant assets |

## Folder Structure
tvs-cps-fe-base-framework repository layout (top levels):

```
TVS-CPS-FE-BASE-FRAMEWORK/
├── package.json (workspaces)
├── channel-partner-system/
│   ├── next.config.ts, tenant.config.mjs, build-tenant.mjs, dev-tenant.mjs
│   ├── scripts/
│   └── src/ (app/, components/, providers/, server/, i18n/, pwa/, styles/, utils/, middleware.ts)
├── shared/
│   └── src/ (api/, services/, store/, hooks/, components/, utils/)
└── runtime-assets/tenants/ (norton-uk, norton-us)
```

## Core Workflows in Code
### Login session
1. Login page obtains a token (source Unknown) and calls `authService` → `POST /api/set-token` (`shared/src/services/auth.service.ts:24`).
2. `set-token/route.ts` sets httpOnly cookie `token` (`channel-partner-system/src/app/api/set-token/route.ts:5`).
3. `middleware.ts` allows `/dashboard` when cookie present; logout calls `POST /api/clear-token` (`auth.service.ts:28`).

### Tenant runtime config
1. `fetchTenantConfig` / `fetchTenantFeatures` read `config.json` / `features.json` from `RUNTIME_CONFIG_BASE_URL` (`src/server/runtime-config.ts:35-56`) into `RuntimeTenantConfig`.

## Integration Clients
tvs-cps-fe-base-framework integration wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | Unknown | env:RUNTIME_ASSETS_BASE_URL |
| Unknown | Unknown | env:RUNTIME_ASSETS_BASE_URL |
| Unknown | Unknown | env:RUNTIME_ASSETS_BASE_URL |
| Unknown | Unknown | env:RUNTIME_CONFIG_BASE_URL |
| Unknown | Unknown | env:RUNTIME_CONFIG_BASE_URL |
| tvs-cps-fe-base-framework | Unknown | env:NEXT_PUBLIC_API_BASE_URL |
| tvs-cps-fe-base-framework | Unknown | env:NEXT_PUBLIC_API_BASE_URL |

## Cross-Cutting Concerns
tvs-cps-fe-base-framework: auth middleware, Redux toolkit store, MUI/Emotion + Tailwind styling, i18next (`i18next-parser.config.js`), PWA support, Jest tests (`jest.config.ts`).

## Build and Test
tvs-cps-fe-base-framework: `npm install`; `npm run build:shared`; `npm run build` or `npm run build:norton-uk` in `channel-partner-system`; `npm test` (jest); `npm run lint` (`channel-partner-system/package.json:5-15`).
