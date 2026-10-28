---
service_id: price-engine-frontend
doc_type: hlc
last_reviewed: 2026-10-11
---

# price-engine-frontend — High-Level Code

## Application Overview
price-engine-frontend (`Price-Engine-Frontend`) is a `frontend-web` codebase; stacks node, react; head `b329ab6ff5256ece2945fdc5a84cec2151e0bd63`.
Entry points: Unknown.

## Module Summary
price-engine-frontend modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | frontend: 0 endpoints, 17 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
price-engine-frontend top-level folders (3 levels):

```
Price-Engine-Frontend/
├── public/
├── src/
│   ├── __tests__/
│   ├── assets/
│   │   ├── icons/
│   │   ├── images/
│   │   ├── theme/
│   ├── components/
│   │   ├── common/
│   │   ├── helpers/
│   │   ├── hoc/
│   │   ├── pages/
│   ├── constants/
│   ├── navigation/
│   ├── rest/
│   │   ├── api-directory/
│   │   ├── http/
│   ├── serializer/
│   ├── store/
│   │   ├── actions/
│   │   ├── adapter/
│   ├── utils/
│   │   ├── commonFunctions/
│   │   ├── constants/
│   │   ├── enum/
│   │   ├── interfaces/
```

## Core Workflows in Code
price-engine-frontend workflows traced from inventory: handler file → outbound/messaging/data access in the same module.
N/A — no server-side entry handlers; see Integration Clients for UI → API calls.

## Integration Clients
price-engine-frontend outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/store/actions/location.ts`, `src/store/actions/price-component.ts`, `src/store/actions/product-price.ts` …+1 | env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL |

## Cross-Cutting Concerns
price-engine-frontend cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
price-engine-frontend build/test commands from manifests:
- `package.json` scripts: `npm run start`, `npm run build`, `npm run test`
- CI pipelines: none found
