---
service_id: form-builder
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["checklist form builder", "form builder", "formbuilder"]
---

# form-builder — Overview

## Purpose
Summary: Next.js Checklist Form Builder app, based on SurveyJS, with admin APIs for forms, users and clients and Firebase integration.
Also known as: checklist form builder, form builder, formbuilder
form-builder is a `frontend-web` repository (`FormBuilder`; service.yaml `type: frontend-web`). Business purpose: README (`README.md`) describes it as: Checklist Form Builder — ======= The objective of this App is to handle checklist form , which is based on Survey JS form Builder..

## Users and Consumers
form-builder is called over HTTP by: `form-builder`. Event consumers of its published messages: none resolved.

## Key Capabilities
form-builder capabilities derived from code:
- `pages/api/admin/add-user`: 1 HTTP endpoint(s)
- `pages/api/admin/delete-form/[id]`: 1 HTTP endpoint(s)
- `pages/api/admin/delete-user/[id]`: 1 HTTP endpoint(s)
- `pages/api/admin/edit-user/[id]`: 1 HTTP endpoint(s)
- `pages/api/admin/get-client`: 1 HTTP endpoint(s)
- `pages/api/admin/get-form-list`: 1 HTTP endpoint(s)
- `pages/api/admin/get-form/[id]`: 1 HTTP endpoint(s)
- `pages/api/admin/get-user-list`: 1 HTTP endpoint(s)
- `pages/api/admin/get-user/[id]`: 1 HTTP endpoint(s)
- `pages/api/admin/login-sso-user`: 1 HTTP endpoint(s)
- `pages/api/generate-pdf`: 1 HTTP endpoint(s)
- `pages/api/get-env-config`: 1 HTTP endpoint(s)
- `pages/api/get-masterdata`: 1 HTTP endpoint(s)
- `pages/api/get-submission-data`: 1 HTTP endpoint(s)
- `pages/api/save-template-data`: 1 HTTP endpoint(s)
- `pages/api/submission-approval`: 1 HTTP endpoint(s)
- `pages/api/submission-update`: 1 HTTP endpoint(s)
- `pages/api/templates`: 1 HTTP endpoint(s)
- `pages/api/admin/update-template`: 1 HTTP endpoint(s)
- `pages/api/admin/create-template`: 1 HTTP endpoint(s)
- UI making 40 backend API calls

## Tech Stack
form-builder tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | next-api, nextjs | Unknown |
| Data | None extracted | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: nextjs,node) | Unknown |

Key libraries: `@azure/msal-browser`, `@azure/msal-react`, `@eslint/eslintrc`, `@reduxjs/toolkit`, `@testing-library/dom`, `@testing-library/jest-dom`, `@testing-library/react`, `@types/bootstrap-datepicker`, `@types/css-modules`, `@types/he`, `@types/jest`, `@types/jquery`, `@types/multer`, `@types/node`, `@types/react`, `@types/react-dom`, `axios`, `bootstrap`, `bootstrap-datepicker`, `crypto-js`, `dayjs`, `eslint`, `eslint-config-next`, `firebase`, `he`, `jest`, `jest-environment-jsdom`, `jest-sonar-reporter`, `jquery`, `jwt-decode` …

## Dependencies at a Glance
Upstream (calls form-builder): `form-builder`
Downstream (form-builder calls): `external:firebase` (None), `form-builder` (hard); plus 38 outbound call(s) with unresolved target
Brokers: none. Data stores: none
Full detail: service.yaml `inbound` / `outbound`.

## Environments
form-builder environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
form-builder configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `API_URL` | Unknown | Unknown | False | Unknown |
| `BASE_PATH` | points to form-builder | Unknown | False | Unknown |
| `NEXT_PUBLIC_AUTHORITY` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_CLIENT_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Unknown | Unknown | True | Unknown |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_ENABLE` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_LOGIN_SCOPE` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_REDIRECT_URI` | Unknown | Unknown | False | Unknown |
| `NEXT_PUBLIC_SECRET_KEY` | Unknown | Unknown | True | Unknown |
| `NODE_ENV` | Unknown | Unknown | False | Unknown |
| `OCP_APIM_SUBSCRIPTION_KEY` | Unknown | Unknown | True | Unknown |

## Ownership
form-builder ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
form-builder local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
form-builder limitations evidenced by extraction:
- 38 outbound HTTP call(s) have no resolved target service (base URL from config/env).
