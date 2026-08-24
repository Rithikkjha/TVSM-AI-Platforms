# TVSM IB Next.js Website

Multi-country, multi-language marketing and lead-capture website for TVS Motor's International Business markets (Malta, Spain, Portugal, Italy, Nepal, Bangladesh, and more). Built with **Next.js 16 (App Router)** and **React 19**, content sourced from **Liferay DXP** (headless), forms forwarded to the **TVS Lead Submission API**.

> Companion docs: [`HLC.md`](./HLC.md) · [`HLD.md`](./HLD.md) · [`LLD.md`](./LLD.md) · [`API_SPEC.md`](./API_SPEC.md)

---

## Table of contents

1. [Overview](#overview)
2. [Tech stack](#tech-stack)
3. [Prerequisites](#prerequisites)
4. [Getting started](#getting-started)
5. [Environment variables](#environment-variables)
6. [Build](#build)
7. [Deployment](#deployment)
8. [Testing](#testing)
9. [Folder structure](#folder-structure)
10. [Troubleshooting](#troubleshooting)
11. [Maintainers](#maintainers)

---

## Overview

A single Next.js codebase serves multiple country sites. The country is resolved at request time from the host (e.g. `malta.tvsmotor.com`) or `?country=` on localhost. Per-country configuration is supplied via environment variables using the convention `<KEY>_<COUNTRY>` (e.g. `LIFERAY_SITE_ID_MALTA`).

Capabilities:
- Server-rendered, ISR-cached pages (home, products, promotions, news, press-room, history, services, who-we-are, dealer-locator, contact-us, become-dealer, legal pages).
- Headless content fetched from Liferay using OAuth2 client-credentials.
- Lead capture forms (Contact Us, Become Dealer) forwarded to the TVS Lead Submission API.
- Cookie consent, deferred Google Analytics, dynamic sitemap and robots.

---

## Tech stack

| Area | Choice |
| --- | --- |
| Framework | Next.js 16 (App Router, RSC) |
| UI | React 19, Tailwind CSS, Swiper, Photoswipe, intl-tel-input |
| Language | TypeScript 5.9 |
| CMS | Liferay DXP (headless) |
| Tests | Jest 30 + Testing Library, Playwright |
| Container | Node 22 Alpine, Next.js standalone server |
| Deploy | Azure DevOps pipelines → ACR → AKS (Application Gateway Ingress) |

---

## Prerequisites

- **Node.js 22** (matches the Docker base image; nvm or volta recommended).
- **npm** (the lockfile is `package-lock.json`).
- Network access to Liferay UAT / dev endpoints.
- A populated `.env.local` (see below).

---

## Getting started

```bash
git clone <repo-url>
cd TVSM-IB-NextJS
npm install
cp .env.example .env.local   # fill in values, see below
npm run dev                   # http://localhost:3000
```

By default the app boots as **MALTA** on localhost. To switch country in dev, append `?country=<code>` to the URL — e.g. `http://localhost:3000/?country=spain`. The middleware writes the `country` cookie so subsequent navigation stays on that country.

### npm scripts

| Script | Purpose |
| --- | --- |
| `npm run dev` | Start the Next.js dev server. |
| `npm run build` | Production build (Next.js standalone output). |
| `npm run start` | Run the built dev server (`next start`). |
| `npm run start:prod` | Run the standalone server (`node ./.next/standalone/server.js`). |
| `npm test` | Run Jest unit tests. |
| `npm run test:coverage` | Jest with coverage report. |

---

## Environment variables

All country-specific config follows `<KEY>_<COUNTRY>`. Country is the uppercase token from the host subdomain (e.g. `MALTA`, `SPAIN`, `PORTUGAL`).

### Global (non-country)

| Variable | Required | Purpose |
| --- | --- | --- |
| `API_BASE_URL` | yes | Default Liferay base URL (e.g. `http://internal-app:80/`). |
| `LIFERAY_CLIENT_ID` | yes | OAuth2 client id (non-secret). |
| `LIFERAY_CLIENT_SECRET` | yes (secret) | OAuth2 client secret — Kubernetes Secret in cluster. |
| `TVS_LEAD_TOKEN` | yes (secret) | Bearer token for the Lead API. |
| `GAEVENTID` | optional | Google Tag Manager / GA container id. |
| `HOSTNAME` | auto | Pod identifier (used in `Server-Name` response header). |

### Per-country (repeat for each `<COUNTRY>` you support)

| Variable | Purpose |
| --- | --- |
| `API_BASE_URL_<COUNTRY>` | Liferay base URL for the country. |
| `LIFERAY_SITE_ID_<COUNTRY>` | Liferay site id (used as `Site-Id` header). |
| `IMAGE_BASE_URL_<COUNTRY>` | Server-side asset URL prefix. |
| `NEXT_PUBLIC_IMAGE_BASE_URL_<COUNTRY>` | Client-side asset URL prefix. |
| `HEADER_STRUCTURE_ID_<COUNTRY>` | Liferay structure id for header. |
| `FOOTER_STRUCTURE_ID_<COUNTRY>` | Liferay structure id for footer. |
| `COOKIE_CONSENT_STRUCTURE_ID_<COUNTRY>` | Cookie banner copy structure. |
| `PAGE_STRUCTURE_ID_<COUNTRY>` | Parent page-config structure. |
| `ALLOWED_ROUTES_<COUNTRY>` | Comma-separated allow-list (`*` permits all; `/path/*` matches prefix). |
| `DEFAULT_LANGUAGE_<COUNTRY>` | Default language for `/` redirect. |
| `FULL_LANG_CODES_<COUNTRY>` | JSON map, e.g. `{"en":"en_US"}`. |
| `ALPHA2_CODE_<COUNTRY>` | ISO 3166-1 alpha-2 code (used by Lead API). |
| `TVS_LEAD_URL_<COUNTRY>` | Lead Submission API URL. |
| `DEALER_LOCATOR_URL_<COUNTRY>` | External dealer locator URL. |
| `GRAPHQL_API_URL_<COUNTRY>` | Reserved (Liferay GraphQL). |

### Example `.env.local`

```bash
# --- Global ---
API_BASE_URL=https://uat-malta.tvsmotor.net/
LIFERAY_CLIENT_ID=replace-me
LIFERAY_CLIENT_SECRET=replace-me
TVS_LEAD_TOKEN=replace-me
GAEVENTID=GTM-XXXXXX

# --- MALTA ---
API_BASE_URL_MALTA=https://uat-malta.tvsmotor.net/
IMAGE_BASE_URL_MALTA=https://uat-malta.tvsmotor.net
NEXT_PUBLIC_IMAGE_BASE_URL_MALTA=https://uat-malta.tvsmotor.net
LIFERAY_SITE_ID_MALTA=2867061
HEADER_STRUCTURE_ID_MALTA=2873907
FOOTER_STRUCTURE_ID_MALTA=2873911
COOKIE_CONSENT_STRUCTURE_ID_MALTA=3612614
PAGE_STRUCTURE_ID_MALTA=2873987
ALLOWED_ROUTES_MALTA=/,/services,/contact-us,/products/*,/our-products/*,/privacy-policy,/cookie-policy,/dealer-locator,/who-we-are,/history,/health_check/data_source
DEFAULT_LANGUAGE_MALTA=en
FULL_LANG_CODES_MALTA={"en":"en_US"}
ALPHA2_CODE_MALTA=MT
TVS_LEAD_URL_MALTA=https://lms-api.tvsmotor.com/weu/api/lead
```

> Never commit `.env.local`. Production secrets are stored in the `nextjs-secrets` Kubernetes Secret; non-secret values live in the `nextjs-config` ConfigMap (see `devops/k8s/`).

---

## Build

### Local production build

```bash
npm run build           # outputs .next/standalone, .next/static
npm run start:prod      # runs node ./.next/standalone/server.js on :3000
```

### Docker build

```bash
docker build -t tvsm-ib-nextjs:local .
docker run --rm -p 3000:3000 --env-file .env.local tvsm-ib-nextjs:local
```

The `Dockerfile` is multi-stage: a Node 22 Alpine builder produces the `.next/standalone` output, and a slim runner image runs `node server.js`.

---

## Deployment

Production and UAT deployments are driven by Azure DevOps pipelines under `devops/pipelines/`:

| Pipeline | Trigger | Purpose |
| --- | --- | --- |
| `build.yml` | After UAT Sonar | Build & push UAT image to ACR. |
| `deploy.yml` | After build | Apply UAT manifests (primary + DR). |
| `build-prod.yml` | Push to `release` | Build & push prod image. |
| `deploy-prod.yml` | After prod build | Apply prod manifests. |
| `sonar.yml`, `sonar-pr.yml` | UAT branch / PR | SonarQube quality gate. |

Kubernetes manifests live under `devops/k8s/{prod,uat/{primary,dr}}/`:

- `Deployment` (`nextjs-deployment`, single replica, rolling update, `/api/health` probes).
- `Service` (`nextjs-app`, internal LoadBalancer, port 80 → 3000).
- `Ingress` (Application Gateway, per-country hosts, TLS via `tvsmotor-com` / `tvsmotor-net-wc` certs).
- `ConfigMap` (`nextjs-config`, all `<KEY>_<COUNTRY>` non-secrets).
- `Secret` (`nextjs-secrets`, `tvs-lead-token`, `liferay-client-secret`).

Onboarding a new country is **config-only**: add the `<KEY>_<COUNTRY>` values to the ConfigMap, add an Ingress rule for the new host, and ensure the Liferay site/structures exist for that country.

---

## Testing

```bash
npm test                  # unit tests (Jest + Testing Library)
npm run test:coverage     # generate coverage report
```

Test layout:
- `__tests__/` — Jest unit tests.
- `__mocks__/` — Module mocks (e.g. for `next/image`, `next/link`).
- `jest.config.js`, `jest.setup.tsx` — config and global setup.
- Playwright is installed but E2E specs (if any) live alongside `playwright.config.*` when added.

Recommended local checks before pushing:

```bash
npm run build && npm test
```

---

## Folder structure

```
TVSM-IB-NextJS/
├── app/
│   ├── api/{become-dealer-submit,contact-submit,health}/route.ts
│   ├── health_check/data_source/route.ts
│   ├── robots.txt/route.ts, sitemap.xml/route.ts
│   ├── layout.tsx, not-found.tsx
│   └── [lang]/                 # localized pages (home, products, news, ...)
├── components/                 # UI components (Header, Footer, Home, Forms, ...)
├── lib/
│   ├── liferayClient.ts        # Authenticated Liferay HTTP wrapper
│   ├── liferayAPI.ts           # Domain calls (content, navigation, products)
│   ├── leadSubmissionClient.ts # Lead API client
│   ├── hooks/                  # Client-side React hooks
│   └── utils/                  # Country, localization, SEO, validation, logger
├── types/                      # TypeScript types (Liferay + domain + forms)
├── public/                     # Static assets
├── styles/                     # Tailwind / CSS / fonts
├── proxy.ts                    # Edge middleware (country, lang, allow-list)
├── next.config.ts              # Image patterns, standalone output
├── Dockerfile                  # Multi-stage build → standalone runner
├── jest.config.js, jest.setup.tsx
├── __tests__/, __mocks__/
└── devops/
    ├── pipelines/              # Azure DevOps pipelines
    └── k8s/{prod,uat/{primary,dr}}/
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Liferay fetch failed: 401` on every page | Token refresh failure or wrong client secret. | Verify `LIFERAY_CLIENT_ID` / `LIFERAY_CLIENT_SECRET` in `.env.local` (or Secret in cluster). Restart the pod / dev server to clear cached token. |
| Pages render with empty sections | A Liferay structure id is missing or wrong. | Check `PAGE_STRUCTURE_ID_<COUNTRY>` and the per-section structure ids; logs from `logger` will name the section. |
| Redirect to `/not-found` for a valid URL | `ALLOWED_ROUTES_<COUNTRY>` doesn't include the path. | Add the path (or a `/prefix/*` entry) to the env value, then redeploy / restart. |
| 503 on `/health_check/data_source` | Liferay unreachable or 10-second timeout. | Verify `API_BASE_URL` and Liferay availability; check ingress / NetworkPolicy. |
| Form submits but customer never sees in CRM | Lead API rejected or returned error. | Check `success` and `apiStatus` in the response envelope; check Lead API logs (404/401 likely means wrong `TVS_LEAD_URL_<COUNTRY>` or stale `TVS_LEAD_TOKEN`). |
| `Failed to fetch admin token` | OAuth2 endpoint unreachable. | Verify `API_BASE_URL` ends with `/` semantics handled, and that the Liferay node accepts client credentials grant. |
| Images broken | Host not in `next.config.ts > images.remotePatterns` or missing `IMAGE_BASE_URL_<COUNTRY>`. | Add the host pattern, set `IMAGE_BASE_URL_<COUNTRY>`, and rebuild. |
| CSP blocks a third-party script | CSP at AppGw / Liferay layer. | Add the host to `script-src` at the layer that emits the CSP — not in this repo. |
| `?country=` not switching country in dev | Old cookie sticking around. | Clear `country`, `langCode`, `fullLangCode` cookies, then reload with `?country=<code>`. |
| `next/image` warning about width/height | Image without dimensions. | Provide width/height or use `fill` with a sized parent. |

For deeper architecture context see [`HLD.md`](./HLD.md); for implementation details see [`LLD.md`](./LLD.md).

---

## Maintainers

| Role | Owner | Contact |
| --- | --- | --- |
| Engineering Lead | _TBD_ | _email / Slack handle_ |
| Front-end Lead | _TBD_ | _email / Slack handle_ |
| DevOps / SRE | _TBD_ | _email / Slack handle_ |
| Liferay / CMS | _TBD_ | _email / Slack handle_ |
| Product / PM | _TBD_ | _email / Slack handle_ |

Issues and proposals: use the team's tracker (Jira project _TBD_). For incidents, follow the on-call rota in the operations runbook.

---

## License

Internal — TVS Motor Company. Not for external distribution without permission.
