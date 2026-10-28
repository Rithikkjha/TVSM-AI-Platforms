---
service_id: cbs-admin-portal
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["cbs admin portal"]
---

# cbs-admin-portal — Overview

## Purpose
Summary: React admin SPA for managing Lead Service (LMS) configurations through a draft, validate and publish workflow with audit logging; calls booking, MDP BFF and QR-code backends.
Also known as: cbs admin portal
cbs-admin-portal is a `portal` repository (`cbs-admin-portal`; service.yaml `type: portal`). Business purpose: README (`README.md`) describes it as: CBS Admin Portal — Frontend — React SPA (Single Page Application) for managing Lead Service (LMS) configurations internally. Provides UI for the **Draft → Validate → Publish** workflow with full audit logging..

## Users and Consumers
cbs-admin-portal is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
cbs-admin-portal capabilities derived from code:
- UI making 76 backend API calls

## Tech Stack
cbs-admin-portal tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | JavaScript | Unknown |
| Framework | react | Unknown |
| Data | None extracted | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | Unknown (build: node,react) | Unknown |

Key libraries: `@testing-library/jest-dom`, `@testing-library/react`, `@testing-library/user-event`, `axios`, `fast-check`, `lucide-react`, `react`, `react-dom`, `react-hot-toast`, `react-router-dom`, `react-scripts`

## Dependencies at a Glance
Upstream (calls cbs-admin-portal): Unknown
Downstream (cbs-admin-portal calls): `booking-crud-services` (hard), `tvsmbe-mdp-bff` (hard), `tvsmbe-qrcode` (hard); plus 73 outbound call(s) with unresolved target
Brokers: none. Data stores: none
Full detail: service.yaml `inbound` / `outbound`.

## Environments
cbs-admin-portal environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| example | Unknown | from config/infra file names |

## Environment Variables
cbs-admin-portal configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `REACT_APP_API_URL` | points to tvsmbe-mdp-bff | Unknown | False | Unknown |
| `REACT_APP_BOOKING_API_URL` | points to booking-crud-services | Unknown | False | Unknown |
| `REACT_APP_BS_CLIENT_ID` | Unknown | True | False | env-file |
| `REACT_APP_BS_CLIENT_SECRET` | Unknown | True | True | env-file |
| `REACT_APP_BS_PROD_BASE_URL` | Unknown | True | False | env-file |
| `REACT_APP_BS_SCOPE` | Unknown | True | False | env-file |
| `REACT_APP_BS_SUBSCRIPTION_KEY` | Unknown | True | True | env-file |
| `REACT_APP_BS_TOKEN_URL` | Unknown | True | True | env-file |
| `REACT_APP_BS_UAT_BASE_URL` | Unknown | True | False | env-file |

## Ownership
cbs-admin-portal ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
cbs-admin-portal local setup evidence:
- README: `README.md`
- Dockerfile(s): none found
- Build commands: see HLC.md `Build and Test`

## Known Limitations
cbs-admin-portal limitations evidenced by extraction:
- 73 outbound HTTP call(s) have no resolved target service (base URL from config/env).
