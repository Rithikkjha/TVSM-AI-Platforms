---
service_id: tvs-cps-fe-base-framework
doc_type: lld
last_reviewed: 2026-10-11
---

# TVS-CPS-FE-BASE-FRAMEWORK — Low-Level Design

## Data Model
tvs-cps-fe-base-framework data entities (from inventory `data_access`; columns per schema items where extracted).
## State Machines
tvs-cps-fe-base-framework: N/A — no state machine evident in code.

## Business Rules
- tvs-cps-fe-base-framework: URLs are redirected to lowercase (`channel-partner-system/src/middleware.ts:17`).
- No token and path not `/login` → redirect to login (`middleware.ts:21-24`).
- Token present on `/` or `/login` → redirect to `/dashboard` (`middleware.ts:28-31`).

## Key Classes and Functions
tvs-cps-fe-base-framework key classes:

| Class / Function | File | Responsibility |
|---|---|---|
| `POST (set-token)` | `channel-partner-system/src/app/api/set-token/route.ts` | Set httpOnly token cookie |
| `POST (clear-token)` | `channel-partner-system/src/app/api/clear-token/route.ts` | Clear token cookie |
| `middleware` | `channel-partner-system/src/middleware.ts` | Auth redirects, lowercase URL redirect |
| `fetchTenantConfig / fetchTenantFeatures` | `channel-partner-system/src/server/runtime-config.ts` | Load tenant runtime config |
| `authService` | `shared/src/services/auth.service.ts` | Client calls to token routes |

## Sequence Details
tvs-cps-fe-base-framework: see DATA_FLOWS.md.

## Error Handling
tvs-cps-fe-base-framework: global error page `channel-partner-system/src/app/global-error.tsx`; runtime config fetch failures caught (`src/server/runtime-config.ts:41`).

## Configuration Details
tvs-cps-fe-base-framework: `NEXT_PUBLIC_API_BASE_URL` base for API calls; `NEXT_PUBLIC_DOMAIN_NAME` app domain; `NEXT_APP_TENANT`/`TENANT` selects tenant; `RUNTIME_ASSETS_BASE_URL` tenant asset host (build); `RUNTIME_CONFIG_BASE_URL` tenant config host; tenant config keys (`siteName`, `siteDescription`, `defaultLocale`, `supportedLocales`, `loaderColor`, `manifest`, `applicationInsightsKey`) from tenant config.

## Edge Cases
tvs-cps-fe-base-framework: N/A — not determinable from code.
