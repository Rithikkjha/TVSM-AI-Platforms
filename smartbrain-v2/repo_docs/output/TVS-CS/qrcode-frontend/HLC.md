---
service_id: qrcode-frontend
doc_type: hlc
last_reviewed: 2026-10-11
---

# qrcode-frontend — High-Level Code

## Application Overview
qrcode-frontend (`qrcode-frontend`) is a `frontend-web` codebase; stacks node, react; head `386aab60ab4ffd7837d39d10d0e5dd02e6d91fc8`.
Entry points: Unknown.

## Module Summary
qrcode-frontend modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | frontend: 0 endpoints, 15 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
qrcode-frontend top-level folders (3 levels):

```
qrcode-frontend/
├── public/
├── src/
│   ├── assets/
│   ├── auth/
│   ├── components/
│   ├── pages/
│   ├── styles/
```

## Core Workflows in Code
qrcode-frontend workflows traced from inventory: handler file → outbound/messaging/data access in the same module.
N/A — no server-side entry handlers; see Integration Clients for UI → API calls.

## Integration Clients
qrcode-frontend outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `src/api.ts` | env:VITE_API_BASE |
| `tvsmbe-qrcode` | `src/api.ts`, `src/auth/AuthProvider.tsx` | env:VITE_API_BASE |

## Cross-Cutting Concerns
qrcode-frontend cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
qrcode-frontend build/test commands from manifests:
- `package.json` scripts: `npm run dev`, `npm run build`, `npm run lint`
- CI pipelines: none found
