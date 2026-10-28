---
service_id: tvs-cps-portal
doc_type: hlc
last_reviewed: 2026-10-11
---

# tvs-cps-portal — High-Level Code

## Application Overview
tvs-cps-portal (`TVS-CPS-PORTAL`) is a `portal` codebase; stacks nextjs, node; head `289a0e42951d8384ec8e8c8e9cf7cfd59cc76d01`.
Entry points: `channel-partner-system/next.config.ts`.

## Module Summary
tvs-cps-portal modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | unknown: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |
| channel-partner-system | `channel-partner-system` | frontend: 12 endpoints, 183 outbound calls, 0 messaging, 0 data-access |
| shared | `shared` | frontend: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
tvs-cps-portal top-level folders (3 levels):

```
TVS-CPS-PORTAL/
├── azure-pipelines/
│   ├── templates/
├── channel-partner-system/
│   ├── __mocks__/
│   │   ├── @shared/
│   ├── public/
│   │   ├── assets/
│   │   ├── common/
│   │   ├── locales/
│   │   ├── tenants/
│   ├── scripts/
│   ├── src/
│   │   ├── __tests__/
│   │   ├── app/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── constants/
│   │   ├── containers/
│   │   ├── hooks/
│   │   ├── i18n/
│   │   ├── providers/
│   │   ├── pwa/
│   │   ├── server/
│   │   ├── services/
│   │   ├── store/
│   │   ├── styles/
│   │   ├── types/
│   │   ├── utils/
├── runtime-assets/
│   ├── tenants/
│   │   ├── norton-uk/
│   │   ├── norton-us/
├── scripts/
├── shared/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── utils/
├── static-pages/
│   ├── error-page/
│   │   ├── images/
```

## Core Workflows in Code
tvs-cps-portal workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### next.config
1. `channel-partner-system/next.config.ts` receives 12 route(s), e.g. `GET /thenortonhub/api/claim/claim-details/{claimId}` → `channel-partner-system/src/app/api/claim/claim-details/[claimId]/route.ts#GET`.
2. Module `channel-partner-system` makes outbound calls to: `Unknown(env:DATABRICKS_TOKEN_URL)`, `Unknown(env:DATABRICKS_WORKSPACE_URL)`, `Unknown(env:NEXT_PUBLIC_API_BASE_URL)`, `Unknown(env:NEXT_PUBLIC_UMS_AUTH_SERVICE_URL)`, `Unknown(env:RUNTIME_ASSETS_BASE_URL)`, `Unknown(env:RUNTIME_CONFIG_BASE_URL)`, `tvs-cps-backend`, `tvs-cps-portal`.

## Integration Clients
tvs-cps-portal outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `channel-partner-system/src/app/api/chatbot/route.ts` | env:DATABRICKS_TOKEN_URL |
| Unknown | `channel-partner-system/src/app/api/chatbot/route.ts` | env:DATABRICKS_WORKSPACE_URL |
| Unknown | `channel-partner-system/src/components/ui/Invoices/common/hooks/useStockAvailability.ts`, `channel-partner-system/src/components/ui/UniversalSearch/ProfileSection/Profile.tsx`, `channel-partner-system/src/components/ui/VinList/hooks/useVinList.tsx` …+15 | env:NEXT_PUBLIC_API_BASE_URL |
| Unknown | `channel-partner-system/src/services/auth.service.ts` | env:NEXT_PUBLIC_UMS_AUTH_SERVICE_URL |
| Unknown | `channel-partner-system/scripts/build-tools.ts` | env:RUNTIME_ASSETS_BASE_URL |
| Unknown | `channel-partner-system/src/server/runtime-config.ts` | env:RUNTIME_CONFIG_BASE_URL |
| `tvs-cps-backend` | `channel-partner-system/src/components/ui/Invoices/QuickInvoice/hooks/useQuickInvoiceDetails.ts`, `channel-partner-system/src/components/ui/Merchandise/MerchandiseOrderDetails/hook/useMerchandiseOrderActions.ts`, `channel-partner-system/src/components/ui/Npqr/NpqrDetails/NpqrDetails.tsx` …+38 | env:NEXT_PUBLIC_API_BASE_URL |
| `tvs-cps-portal` | `channel-partner-system/src/services/auth.service.ts` | env:NEXT_PUBLIC_API_BASE_URL |
| `tvs-cps-portal` | `channel-partner-system/src/constants/environment.constant.ts`, `channel-partner-system/src/services/chatbot.service.ts` | unknown |

## Cross-Cutting Concerns
tvs-cps-portal cross-cutting code:
- Auth: `channel-partner-system/src/app/api/chatbot/route.ts:64` (middleware.ts)
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
tvs-cps-portal build/test commands from manifests:
- `package.json` scripts: `npm run test`, `npm run start`
- `channel-partner-system/package.json` scripts: `npm run lint`, `npm run start`, `npm run build`, `npm run test`
- `shared/package.json` scripts: `npm run build`, `npm run test`
- CI pipelines: `azure-pipelines/templates/ast-cps-portal-prod.yaml:1`, `azure-pipelines/templates/ast-cps-portal-uat.yaml:1`, `azure-pipelines/templates/cd-pipeline.yaml:1`, `azure-pipelines/templates/ci-pipeline.yaml:1`, `azure-pipelines/templates/cps-frontend-sonar-scan-pr.yaml:1`, `azure-pipelines/templates/cps-frontend-sonar-scan.yaml:1`, `azure-pipelines/templates/docker-image-scan.yaml:1`, `azure-pipelines/templates/uk-cd-pipeline.yaml:1`, `azure-pipelines/templates/uk-training-cd-pipeline.yaml:1`
