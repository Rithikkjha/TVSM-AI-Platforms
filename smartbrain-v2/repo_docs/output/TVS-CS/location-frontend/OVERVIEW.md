---
service_id: location-frontend
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["location frontend", "location"]
---

# location-frontend — Overview

## Purpose
Summary: React frontend for dealer location administration, calling tvsmbe-location dealer, contacts, summary and rejection-comment APIs and Google Maps; README is the CRA template.
Also known as: location frontend, location
location-frontend is a `frontend-web` repository (`location-frontend`; service.yaml `type: frontend-web`). Business purpose: Unknown — not stated in README/code.

## Users and Consumers
location-frontend is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
location-frontend capabilities derived from code:
- UI making 31 backend API calls

## Tech Stack
location-frontend tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | react | Unknown |
| Data | None extracted | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | Unknown (build: node,react) | Unknown |

Key libraries: `@googlemaps/markerclusterer`, `@react-google-maps/api`, `@reduxjs/toolkit`, `@tailwindcss/typography`, `@testing-library/jest-dom`, `@testing-library/react`, `@testing-library/user-event`, `@types/axios`, `@types/crypto-js`, `@types/geojson`, `@types/google.maps`, `@types/jest`, `@types/jwt-decode`, `@types/node`, `@types/react`, `@types/react-dom`, `@types/redux-mock-store`, `@vis.gl/react-google-maps`, `autoprefixer`, `axios`, `classnames`, `cross-env`, `crypto-js`, `css-loader`, `css-minimizer-webpack-plugin`, `env-cmd`, `i18next`, `i18next-browser-languagedetector`, `leaflet`, `pdfjs-dist` …

## Dependencies at a Glance
Upstream (calls location-frontend): Unknown
Downstream (location-frontend calls): `external:google-maps` (None), `tvsmbe-location` (hard)
Brokers: none. Data stores: none
Full detail: service.yaml `inbound` / `outbound`.

## Environments
location-frontend environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| dev | Unknown | from config/infra file names |
| prod | Unknown | from config/infra file names |
| uat | Unknown | from config/infra file names |

## Environment Variables
location-frontend configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `NODE_ENV` | Unknown | Unknown | False | Unknown |
| `PUBLIC_URL` | Unknown | Unknown | False | Unknown |
| `REACT_APP_ADMIN_BASE_URL` | points to tvsmbe-location | Unknown | False | env-file |
| `REACT_APP_ADMIN_IB_BASE_URL` | points to tvsmbe-location | Unknown | False | env-file |
| `REACT_APP_APPID` | Unknown | Unknown | False | env-file |
| `REACT_APP_ASSET_BASE_URL` | Unknown | Unknown | False | env-file |
| `REACT_APP_DEALERWEB_BASE_URL` | points to tvsmbe-location | Unknown | False | env-file |
| `REACT_APP_DEALER_BASE_URL` | points to tvsmbe-location | Unknown | False | env-file |
| `REACT_APP_DEALER_LOCATER_BASE_URL` | points to tvsmbe-location | Unknown | False | env-file |
| `REACT_APP_GOOGLE_MAPS_API_KEY` | Unknown | Unknown | True | env-file |
| `REACT_APP_GOOGLE_MAP_API_BASE_URL` | Unknown | Unknown | False | env-file |
| `REACT_APP_LOGINURL` | Unknown | Unknown | False | env-file |
| `REACT_APP_LOGIN_REDIRECT_URL` | Unknown | Unknown | False | env-file |
| `REACT_APP_PUBLIC_LOGIN_URL` | Unknown | Unknown | False | env-file |
| `REACT_APP_SCP_URL` | Unknown | Unknown | False | env-file |
| `REACT_APP_SECRET_KEY` | Unknown | Unknown | True | Unknown |

## Ownership
location-frontend ownership: see `CODEOWNERS`.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
location-frontend local setup evidence:
- README: `README.md`
- Dockerfile(s): none found
- Build commands: see HLC.md `Build and Test`

## Known Limitations
location-frontend limitations evidenced by extraction:
- N/A — none evidenced in code
