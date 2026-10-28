---
service_id: tvs-cps-fe-base-framework
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["tvs cps fe base framework", "channel partner system", "cps fe base framework"]
---

# TVS-CPS-FE-BASE-FRAMEWORK — Overview

## Purpose
Summary: Base Next.js monorepo for the multi-tenant Channel Partner System web front end, with shared hooks, API services and Redux slices.
Also known as: tvs cps fe base framework, channel partner system, cps fe base framework
tvs-cps-fe-base-framework is the base Next.js monorepo for the multi-tenant Channel Partner System (CPS) web front end: `channel-partner-system` (Next.js app) plus `shared` (`@shared/channel-partner-system` — hooks, API services, Redux store slices) (`README.md`). Tenants are configured at build/runtime (e.g. `norton-uk`, `norton-us` under `runtime-assets/tenants/`).

## Users and Consumers
tvs-cps-fe-base-framework inbound callers (registry): `tvs-cps-fe-base-framework`.
Event consumers of tvs-cps-fe-base-framework's topics/queues: none recorded.
End users are channel-partner staff using the web UI (README); the only HTTP callers of its Next API routes are its own pages (`shared/src/services/auth.service.ts:24`).

## Key Capabilities
tvs-cps-fe-base-framework capabilities:
- Login/dashboard pages (`channel-partner-system/src/app/login`, `src/app/dashboard`)
- Cookie-based session: `/api/set-token` stores an httpOnly `token` cookie, `/api/clear-token` removes it (`channel-partner-system/src/app/api/set-token/route.ts:3`)
- Auth redirect middleware (`channel-partner-system/src/middleware.ts:21-31`)
- Runtime tenant config/features fetched from `RUNTIME_CONFIG_BASE_URL` (`channel-partner-system/src/server/runtime-config.ts:40`, `:55`)
- Per-tenant build/dev scripts (`channel-partner-system/package.json:6-9`), i18n, PWA (`src/pwa`)
- 2 HTTP endpoints (see API_SPEC.md)

## Tech Stack
tvs-cps-fe-base-framework tech stack (service.yaml `tech_stack`, build `nextjs,node`):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | next-api, nextjs | Unknown |
| Data | none | Unknown |
| Messaging | none | Unknown |
| Hosting | Unknown — no Dockerfile/pipeline in repo | Unknown |

Key libraries: `@emotion/react` ^11.14.0, `@emotion/styled` ^11.14.1, `@eslint/eslintrc` ^3, `@mui/icons-material` ^7.2.0, `@mui/material` ^7.2.0, `@reduxjs/toolkit` ^2.8.2, `@shared/channel-partner-system` 1.0.0, `@svgr/cli` ^8.0.0, `@tailwindcss/postcss` ^4.1.11, `@testing-library/dom` ^10.4.0, `@testing-library/jest-dom` ^6.6.3, `@testing-library/react` ^16.3.0, `@types/jest` ^30.0.0, `@types/jsonwebtoken` ^9.0.10, `@types/node` ^20, `@types/react` ^19, `@types/react-dom` ^19, `@types/web-push` ^3.6.4, `autoprefixer` ^10.4.21, `axios` ^1.11.0, `eslint` ^9, `eslint-config-next` 15.3.5, `i18next` ^25.3.2, `i18next-parser` ^9.0.2, `identity-obj-proxy` ^3.0.0, `jest` ^30.0.4, `jest-environment-jsdom` ^30.0.4, `jsonwebtoken` ^9.0.2, `next` 15.3.5, `next-pwa` ^5.6.0

## Dependencies at a Glance
Upstream (calls tvs-cps-fe-base-framework): `tvs-cps-fe-base-framework`
Downstream (tvs-cps-fe-base-framework calls): `tvs-cps-fe-base-framework` (hard); 5 unresolved outbound calls (see API_SPEC.md)
Brokers: none
Data stores: none
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvs-cps-fe-base-framework environments (service.yaml `deployment.environments`: none recorded).

| Env | URL | Notes |
|---|---|---|
| prod | Unknown | |
| uat | Unknown | |
| dev | `NEXT_PUBLIC_DOMAIN_NAME` local value in README | README `.env.local` example |

## Environment Variables
tvs-cps-fe-base-framework configuration keys (15; names only, from service.yaml `config`):

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `NEXT_APP_TENANT` | Unknown | Unknown | no | Unknown |
| `NEXT_PUBLIC_API_BASE_URL` | Unknown | Unknown | no | Unknown |
| `NEXT_PUBLIC_DOMAIN_NAME` | Unknown | Unknown | no | Unknown |
| `NODE_ENV` | Unknown | Unknown | no | Unknown |
| `RUNTIME_ASSETS_BASE_URL` | Unknown | Unknown | no | Unknown |
| `RUNTIME_CONFIG_BASE_URL` | Unknown | Unknown | no | Unknown |
| `TENANT` | Unknown | Unknown | no | Unknown |
| `applicationInsightsKey` | Unknown | Unknown | yes | Unknown |
| `defaultLocale` | Unknown | Unknown | no | Unknown |
| `loaderColor` | Unknown | Unknown | no | Unknown |
| `manifest` | Unknown | Unknown | no | Unknown |
| `siteDescription` | Unknown | Unknown | no | Unknown |
| `siteName` | Unknown | Unknown | no | Unknown |
| `supportedLocales:0` | Unknown | Unknown | no | Unknown |
| `supportedLocales:1` | Unknown | Unknown | no | Unknown |

## Ownership
tvs-cps-fe-base-framework ownership is not recorded in code unless shown below.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvs-cps-fe-base-framework (`README.md`): `npm install` at root; create `channel-partner-system/.env.local` with `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_DOMAIN_NAME`, `NEXT_APP_TENANT`; run `npm run dev:cps` (→ `dev:norton-uk`, `package.json`). Build shared with `npm run build:shared`.

## Known Limitations
tvs-cps-fe-base-framework: none evidenced in code.
