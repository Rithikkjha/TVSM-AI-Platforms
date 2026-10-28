---
service_id: location-frontend
doc_type: hlc
last_reviewed: 2026-10-11
---

# location-frontend — High-Level Code

## Application Overview
location-frontend (`location-frontend`) is a `frontend-web` codebase; stacks node, react; head `ef5a3c4a59ec8706ea4bd2a3e721f309850ff37c`.
Entry points: Unknown.

## Module Summary
location-frontend modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | frontend: 0 endpoints, 31 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
location-frontend top-level folders (3 levels):

```
location-frontend/
├── azure-pipelines/
├── public/
│   ├── assets/
│   │   ├── Images/
│   │   ├── V2Folder/
│   ├── embed/
├── scripts/
├── src/
│   ├──  assets/
│   │   ├── Images/
│   ├── DealerLocator/
│   ├── DealerLocatorV2/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── context/
│   │   ├── docs/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── utils/
│   ├── __mocks__/
│   ├── components/
│   │   ├── Navigation/
│   │   ├── common/
│   │   ├── pages/
│   ├── constants/
│   ├── context/
│   ├── json/
│   ├── rest/
│   ├── services/
│   ├── store/
│   │   ├── slices/
│   │   ├── thunks/
│   ├── styles/
│   ├── utils/
```

## Core Workflows in Code
location-frontend workflows traced from inventory: handler file → outbound/messaging/data access in the same module.
N/A — no server-side entry handlers; see Integration Clients for UI → API calls.

## Integration Clients
location-frontend outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| `tvsmbe-location` | `src/services/DealerDetailsService.ts` | env:REACT_APP_ADMIN_BASE_URL |
| `tvsmbe-location` | `src/services/AdminDealerService.ts`, `src/services/DealerDetailsService.ts`, `src/services/DealerService.ts` | env:REACT_APP_ADMIN_IB_BASE_URL |
| `tvsmbe-location` | `src/services/DealerFlowDealerDetailsService.ts` | env:REACT_APP_DEALERWEB_BASE_URL |
| `tvsmbe-location` | `src/services/DealerDetailsService.ts` | env:REACT_APP_DEALER_BASE_URL |
| `tvsmbe-location` | `src/DealerLocatorV2/services/clusterService.ts`, `src/DealerLocatorV2/services/dealerLocatorV2Service.ts`, `src/DealerLocatorV2/services/geocodeService.ts` …+1 | env:REACT_APP_DEALER_LOCATER_BASE_URL |

## Cross-Cutting Concerns
location-frontend cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
location-frontend build/test commands from manifests:
- `package.json` scripts: `npm run start`, `npm run build`, `npm run test`, `npm run start:dev`
- CI pipelines: `azure-pipelines/dev-ci.yaml:6`, `azure-pipelines/prod-ci.yaml:6`, `azure-pipelines/uat-ci.yaml:6`
