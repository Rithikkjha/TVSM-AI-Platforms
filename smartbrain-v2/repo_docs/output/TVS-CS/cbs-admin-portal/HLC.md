---
service_id: cbs-admin-portal
doc_type: hlc
last_reviewed: 2026-10-11
---

# cbs-admin-portal — High-Level Code

## Application Overview
cbs-admin-portal (`cbs-admin-portal`) is a `portal` codebase; stacks node, react; head `80a705d5a4ba1afedb56f50ac828edf16e9753d7`.
Entry points: Unknown.

## Module Summary
cbs-admin-portal modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | frontend: 0 endpoints, 76 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
cbs-admin-portal top-level folders (3 levels):

```
cbs-admin-portal/
├── backend/
│   ├── src/
│   │   ├── main/
├── public/
├── src/
│   ├── components/
│   ├── context/
│   ├── hooks/
│   ├── pages/
│   │   ├── __tests__/
│   ├── services/
│   │   ├── __tests__/
│   ├── styles/
│   ├── utils/
```

## Core Workflows in Code
cbs-admin-portal workflows traced from inventory: handler file → outbound/messaging/data access in the same module.
N/A — no server-side entry handlers; see Integration Clients for UI → API calls.

## Integration Clients
cbs-admin-portal outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/hooks/useAuth.js`, `src/services/dataService.js` | env:REACT_APP_API_URL |
| `booking-crud-services` | `src/services/dataService.js` | env:REACT_APP_BOOKING_API_URL |
| `tvsmbe-mdp-bff` | `src/services/dataService.js` | env:REACT_APP_API_URL |
| `tvsmbe-qrcode` | `src/services/dataService.js` | env:REACT_APP_API_URL |

## Cross-Cutting Concerns
cbs-admin-portal cross-cutting code:
- Auth: `backend/src/main/java/com/tvs/leadsadmin/workflow/controller/WorkflowController.java:45` (@PreAuthorize)
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
cbs-admin-portal build/test commands from manifests:
- `package.json` scripts: `npm run start`, `npm run build`, `npm run test`
- CI pipelines: none found
