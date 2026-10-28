---
service_id: form-builder
doc_type: hlc
last_reviewed: 2026-10-11
---

# form-builder — High-Level Code

## Application Overview
form-builder (`FormBuilder`) is a `frontend-web` codebase; stacks nextjs, node; head `d2b40c3acebbf4f0033e8a20cada0e362f4e3eba`.
Entry points: `next.config.ts`.

## Module Summary
form-builder modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | frontend: 20 endpoints, 40 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
form-builder top-level folders (3 levels):

```
FormBuilder/
├── __tests__/
├── app/
│   ├── admin/
│   │   ├── templatebuilder/
│   ├── auth/
│   ├── components/
│   │   ├── Admin/
│   ├── constants/
│   ├── error/
│   ├── feedback/
│   │   ├── [templateID]/
│   │   ├── submission/
│   ├── hooks/
│   ├── lib/
│   │   ├── redux/
│   ├── styles/
│   ├── success/
│   ├── types/
├── pages/
│   ├── api/
│   │   ├── admin/
├── public/
│   ├── fonts/
├── utils/
│   ├── data/
│   │   ├── multi-page-form/
│   │   ├── quiz/
│   │   ├── single-page-form/
│   ├── functions/
│   ├── interceptors/
```

## Core Workflows in Code
form-builder workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### add-user
1. `pages/api/admin/add-user.ts` receives 1 route(s), e.g. `None /api/admin/add-user` → `pages/api/admin/add-user.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### [id]
1. `pages/api/admin/delete-form/[id].ts` receives 1 route(s), e.g. `None /api/admin/delete-form/{id}` → `pages/api/admin/delete-form/[id].ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### [id]
1. `pages/api/admin/delete-user/[id].ts` receives 1 route(s), e.g. `None /api/admin/delete-user/{id}` → `pages/api/admin/delete-user/[id].ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### [id]
1. `pages/api/admin/edit-user/[id].ts` receives 1 route(s), e.g. `None /api/admin/edit-user/{id}` → `pages/api/admin/edit-user/[id].ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### get-client
1. `pages/api/admin/get-client.ts` receives 1 route(s), e.g. `None /api/admin/get-client` → `pages/api/admin/get-client.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### get-form-list
1. `pages/api/admin/get-form-list.ts` receives 1 route(s), e.g. `None /api/admin/get-form-list` → `pages/api/admin/get-form-list.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### [id]
1. `pages/api/admin/get-form/[id].ts` receives 1 route(s), e.g. `None /api/admin/get-form/{id}` → `pages/api/admin/get-form/[id].ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### get-user-list
1. `pages/api/admin/get-user-list.ts` receives 1 route(s), e.g. `None /api/admin/get-user-list` → `pages/api/admin/get-user-list.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### [id]
1. `pages/api/admin/get-user/[id].ts` receives 1 route(s), e.g. `None /api/admin/get-user/{id}` → `pages/api/admin/get-user/[id].ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### login-sso-user
1. `pages/api/admin/login-sso-user.ts` receives 1 route(s), e.g. `None /api/admin/login-sso-user` → `pages/api/admin/login-sso-user.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### generate-pdf
1. `pages/api/generate-pdf.ts` receives 1 route(s), e.g. `None /api/generate-pdf` → `pages/api/generate-pdf.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### get-env-config
1. `pages/api/get-env-config.ts` receives 1 route(s), e.g. `None /api/get-env-config` → `pages/api/get-env-config.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### get-masterdata
1. `pages/api/get-masterdata.ts` receives 1 route(s), e.g. `None /api/get-masterdata` → `pages/api/get-masterdata.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### get-submission-data
1. `pages/api/get-submission-data.ts` receives 1 route(s), e.g. `None /api/get-submission-data` → `pages/api/get-submission-data.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### save-template-data
1. `pages/api/save-template-data.ts` receives 1 route(s), e.g. `None /api/save-template-data` → `pages/api/save-template-data.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### submission-approval
1. `pages/api/submission-approval.ts` receives 1 route(s), e.g. `None /api/submission-approval` → `pages/api/submission-approval.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### submission-update
1. `pages/api/submission-update.ts` receives 1 route(s), e.g. `None /api/submission-update` → `pages/api/submission-update.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### templates
1. `pages/api/templates.ts` receives 1 route(s), e.g. `None /api/templates` → `pages/api/templates.ts#default`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### update-template
1. `pages/api/admin/update-template.ts` receives 1 route(s), e.g. `PATCH /api/admin/update-template` → `pages/api/admin/update-template.ts#PATCH`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

### create-template
1. `pages/api/admin/create-template.ts` receives 1 route(s), e.g. `POST /api/admin/create-template` → `pages/api/admin/create-template.ts#POST`.
2. Module `.` makes outbound calls to: `Unknown(env:API_URL)`, `Unknown(env:BASE_PATH)`, `Unknown(env:NEXT_PUBLIC_API_URL)`, `form-builder`.

## Integration Clients
form-builder outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `pages/api/admin/add-user.ts`, `pages/api/admin/create-template.ts`, `pages/api/admin/delete-form/[id].ts` …+16 | env:API_URL |
| Unknown | `app/admin/templatebuilder/[id]/page.tsx`, `app/components/Admin/Dashboard.tsx`, `app/components/Admin/FormManagement/Designer.tsx` …+8 | env:BASE_PATH |
| Unknown | `app/components/RenderForms.tsx` | env:NEXT_PUBLIC_API_URL |
| `form-builder` | `app/components/Admin/TemplateBuilder.tsx` | env:BASE_PATH |

## Cross-Cutting Concerns
form-builder cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: `loglevel`

## Build and Test
form-builder build/test commands from manifests:
- `package.json` scripts: `npm run dev`, `npm run build`, `npm run start`, `npm run lint`, `npm run test`
- CI pipelines: `cd-pipeline.yaml:1`, `ci-pipeline.yaml:1`, `ci-sonar-pipeline-pr.yml:1`, `ci-sonar-pipeline.yml:1`
