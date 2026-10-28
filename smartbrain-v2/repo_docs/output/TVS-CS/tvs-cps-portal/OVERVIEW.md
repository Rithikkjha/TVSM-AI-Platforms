---
service_id: tvs-cps-portal
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["tvs cps portal", "channel partner system", "thenortonhub", "cps portal", "cps frontend", "cps"]
---

# tvs-cps-portal — Overview

## Purpose
Summary: Next.js multi-tenant Channel Partner System portal for channel partner operations, calling tvs-cps-backend and Firebase.
Also known as: tvs cps portal, channel partner system, thenortonhub, cps portal, cps frontend, cps
tvs-cps-portal is a `portal` repository (`TVS-CPS-PORTAL`; service.yaml `type: portal`). Business purpose: README (`README.md`) describes it as: Channel Partner System — A monorepo setup for managing channel partner operations, supporting multiple tenants, and utilizing a shared package for common functionality. Built with [Next.js](https://nextjs.org/).
It contains 3 subprojects: `.` (unknown), `channel-partner-system` (frontend), `shared` (frontend).

## Users and Consumers
tvs-cps-portal is called over HTTP by: `tvs-cps-portal`. Event consumers of its published messages: none resolved.

## Key Capabilities
tvs-cps-portal capabilities derived from code:
- `channel-partner-system/src/app/api/claim/claim-details/[claimId]/route`: 1 HTTP endpoint(s)
- `channel-partner-system/src/app/api/claim/master/route`: 1 HTTP endpoint(s)
- `channel-partner-system/src/app/api/file/route`: 1 HTTP endpoint(s)
- `channel-partner-system/src/app/api/get-image/route`: 1 HTTP endpoint(s)
- `channel-partner-system/src/app/api/getEnvConfig/route`: 1 HTTP endpoint(s)
- `channel-partner-system/src/app/api/stream/route`: 1 HTTP endpoint(s)
- `channel-partner-system/src/app/firebase-messaging-sw`: 1 HTTP endpoint(s)
- `channel-partner-system/src/app/api/chatbot/route`: 1 HTTP endpoint(s)
- `channel-partner-system/src/app/api/claim/dashboard/route`: 1 HTTP endpoint(s)
- `channel-partner-system/src/app/api/claim/update/route`: 1 HTTP endpoint(s)
- `channel-partner-system/src/app/api/clear-token/route`: 1 HTTP endpoint(s)
- `channel-partner-system/src/app/api/set-token/route`: 1 HTTP endpoint(s)
- UI making 183 backend API calls

## Tech Stack
tvs-cps-portal tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | next-api, nextjs | Unknown |
| Data | None extracted | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: nextjs,node) | Unknown |

Key libraries: `@emotion/react`, `@emotion/styled`, `@eslint/eslintrc`, `@fullcalendar/core`, `@fullcalendar/daygrid`, `@fullcalendar/interaction`, `@fullcalendar/list`, `@fullcalendar/react`, `@fullcalendar/timegrid`, `@hookform/resolvers`, `@img/sharp-libvips-linuxmusl-x64`, `@img/sharp-linuxmusl-x64`, `@mui/icons-material`, `@mui/material`, `@mui/x-charts`, `@mui/x-date-pickers`, `@next/swc-linux-x64-musl`, `@react-pdf/renderer`, `@reduxjs/toolkit`, `@shared/channel-partner-system`, `@svgr/cli`, `@tailwindcss/oxide-linux-x64-musl`, `@tailwindcss/postcss`, `@testing-library/dom`, `@testing-library/jest-dom`, `@testing-library/react`, `@types/crypto-js`, `@types/jest`, `@types/jsonwebtoken`, `@types/node` …

## Dependencies at a Glance
Upstream (calls tvs-cps-portal): `tvs-cps-portal`
Downstream (tvs-cps-portal calls): `external:firebase` (None), `tvs-cps-backend` (hard), `tvs-cps-portal` (hard); plus 49 outbound call(s) with unresolved target
Brokers: none. Data stores: none
Full detail: service.yaml `inbound` / `outbound`.

## Environments
tvs-cps-portal environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| constant.test | Unknown | from config/infra file names |
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| training | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
tvs-cps-portal configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `DATABRICKS_CLIENT_ID` | Unknown | Unknown | False | Unknown |
| `DATABRICKS_CLIENT_SECRET` | Unknown | Unknown | True | Unknown |
| `DATABRICKS_TOKEN_URL` | Unknown | Unknown | True | Unknown |
| `DATABRICKS_WORKSPACE_URL` | Unknown | Unknown | False | Unknown |
| `NEXT_APP_TENANT` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_ANALYTICS_DASHBOARD_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_API_BASE_INTERNAL_URL` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_API_BASE_URL` | points to tvs-cps-backend | Unknown | False | Unknown |
| `NEXT_PUBLIC_APPLICATION_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_APPLICATION_KEY` | Unknown | Unknown | True | Unknown |
| `NEXT_PUBLIC_CHECKLIST_FORM_URL` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_CHECKLIST_TEMPLATE_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_DASHBOARD_BFF_URL` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_DOMAIN_NAME` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_ENV` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_EPC_UI_URL` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Unknown | Unknown | True | Unknown |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_VAPID_KEY` | Unknown | Unknown | True | Unknown |
| `NEXT_PUBLIC_GMS_URL` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_LEARNING_360_URL` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_SALESFORCE_SUPPORT_URL` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_SF_LOGOUT_URL` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_SITE24X7_APP_KEY` | Unknown | Unknown | True | Unknown |
| `NEXT_PUBLIC_UMS_AUTH_SERVICE_URL` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_UMS_SCOPE` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_USE_DATABRICKS_DASHBOARD` | Unknown | Unknown | False | Unknown |
| `NODE_ENV` | Unknown | Unknown | False | Unknown |
| `NODE_OPTIONS` | Unknown | Unknown | False | Unknown |
| `RUNTIME_ASSETS_BASE_URL` | Unknown | Unknown | False | Unknown |
| `RUNTIME_CONFIG_BASE_URL` | Unknown | Unknown | False | Unknown |
| `TENANT` | Unknown | Unknown | False | Unknown |
| `applicationInsightsKey` | Unknown | Unknown | True | Unknown |
| `currencyCode` | Unknown | Unknown | False | Unknown |
| `defaultLocale` | Unknown | Unknown | False | Unknown |
| `loaderColor` | Unknown | Unknown | False | Unknown |
| `locale` | Unknown | Unknown | False | Unknown |
| `manifest` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_APP_TENANT` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_API_BASE_INTERNAL_URL` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_API_BASE_URL` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_APPLICATION_ID` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_APPLICATION_KEY` | Unknown | Unknown | True | Unknown |
| `mockConfig.NEXT_PUBLIC_CHECKLIST_FORM_URL` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_CHECKLIST_TEMPLATE_ID` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_DOMAIN_NAME` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_ENV` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_GMS_URL` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_SALESFORCE_SUPPORT_URL` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_SF_LOGOUT_URL` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_SITE24X7_APP_KEY` | Unknown | Unknown | True | Unknown |
| `mockConfig.NEXT_PUBLIC_UMS_AUTH_SERVICE_URL` | Unknown | Unknown | False | Unknown |
| `mockConfig.NEXT_PUBLIC_UMS_SCOPE` | Unknown | Unknown | False | Unknown |
| `mockConfig.RUNTIME_ASSETS_BASE_URL` | Unknown | Unknown | False | Unknown |
| `siteDescription` | Unknown | Unknown | False | Unknown |
| `siteName` | Unknown | Unknown | False | Unknown |
| `supportedLocales:0` | Unknown | Unknown | False | Unknown |
| `supportedLocales:1` | Unknown | Unknown | False | Unknown |
| `timeZone` | Unknown | Unknown | False | Unknown |

## Ownership
tvs-cps-portal ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
tvs-cps-portal local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
tvs-cps-portal limitations evidenced by extraction:
- 49 outbound HTTP call(s) have no resolved target service (base URL from config/env).
