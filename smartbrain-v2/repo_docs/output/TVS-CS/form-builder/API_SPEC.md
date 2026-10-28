---
service_id: form-builder
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# form-builder — API Specification

## Authentication
form-builder endpoint auth as extracted: `None` × 20.
Auth libraries: `jwt-decode`.

## Endpoint Index
form-builder exposes 20 HTTP endpoint(s) and 0 scheduled job(s).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| None | `/api/admin/add-user` | Unknown | handler `pages/api/admin/add-user.ts#default` | Unknown |
| None | `/api/admin/delete-form/{id}` | Unknown | handler `pages/api/admin/delete-form/[id].ts#default` | Unknown |
| None | `/api/admin/delete-user/{id}` | Unknown | handler `pages/api/admin/delete-user/[id].ts#default` | Unknown |
| None | `/api/admin/edit-user/{id}` | Unknown | handler `pages/api/admin/edit-user/[id].ts#default` | Unknown |
| None | `/api/admin/get-client` | Unknown | handler `pages/api/admin/get-client.ts#default` | Unknown |
| None | `/api/admin/get-form-list` | Unknown | handler `pages/api/admin/get-form-list.ts#default` | Unknown |
| None | `/api/admin/get-form/{id}` | Unknown | handler `pages/api/admin/get-form/[id].ts#default` | Unknown |
| None | `/api/admin/get-user-list` | Unknown | handler `pages/api/admin/get-user-list.ts#default` | Unknown |
| None | `/api/admin/get-user/{id}` | Unknown | handler `pages/api/admin/get-user/[id].ts#default` | Unknown |
| None | `/api/admin/login-sso-user` | Unknown | handler `pages/api/admin/login-sso-user.ts#default` | Unknown |
| None | `/api/generate-pdf` | Unknown | handler `pages/api/generate-pdf.ts#default` | Unknown |
| None | `/api/get-env-config` | Unknown | handler `pages/api/get-env-config.ts#default` | Unknown |
| None | `/api/get-masterdata` | Unknown | handler `pages/api/get-masterdata.ts#default` | Unknown |
| None | `/api/get-submission-data` | Unknown | handler `pages/api/get-submission-data.ts#default` | Unknown |
| None | `/api/save-template-data` | Unknown | handler `pages/api/save-template-data.ts#default` | Unknown |
| None | `/api/submission-approval` | Unknown | handler `pages/api/submission-approval.ts#default` | Unknown |
| None | `/api/submission-update` | Unknown | handler `pages/api/submission-update.ts#default` | Unknown |
| None | `/api/templates` | Unknown | handler `pages/api/templates.ts#default` | Unknown |
| PATCH | `/api/admin/update-template` | Unknown | handler `pages/api/admin/update-template.ts#PATCH` | form-builder |
| POST | `/api/admin/create-template` | Unknown | handler `pages/api/admin/create-template.ts#POST` | form-builder |

## Endpoints
form-builder endpoint details (from inventory `inbound_http`).

### None /api/admin/add-user
Handler: `pages/api/admin/add-user.ts#default` in `pages/api/admin/add-user.ts:17`. Purpose: Unknown. Callers: Unknown.

### None /api/admin/delete-form/{id}
Handler: `pages/api/admin/delete-form/[id].ts#default` in `pages/api/admin/delete-form/[id].ts:7`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | |

### None /api/admin/delete-user/{id}
Handler: `pages/api/admin/delete-user/[id].ts#default` in `pages/api/admin/delete-user/[id].ts:6`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | |

### None /api/admin/edit-user/{id}
Handler: `pages/api/admin/edit-user/[id].ts#default` in `pages/api/admin/edit-user/[id].ts:16`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | |

### None /api/admin/get-client
Handler: `pages/api/admin/get-client.ts#default` in `pages/api/admin/get-client.ts:6`. Purpose: Unknown. Callers: Unknown.

### None /api/admin/get-form-list
Handler: `pages/api/admin/get-form-list.ts#default` in `pages/api/admin/get-form-list.ts:6`. Purpose: Unknown. Callers: Unknown.

### None /api/admin/get-form/{id}
Handler: `pages/api/admin/get-form/[id].ts#default` in `pages/api/admin/get-form/[id].ts:6`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | |

### None /api/admin/get-user-list
Handler: `pages/api/admin/get-user-list.ts#default` in `pages/api/admin/get-user-list.ts:6`. Purpose: Unknown. Callers: Unknown.

### None /api/admin/get-user/{id}
Handler: `pages/api/admin/get-user/[id].ts#default` in `pages/api/admin/get-user/[id].ts:6`. Purpose: Unknown. Callers: Unknown.

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| id | path | string | True | |

### None /api/admin/login-sso-user
Handler: `pages/api/admin/login-sso-user.ts#default` in `pages/api/admin/login-sso-user.ts:7`. Purpose: Unknown. Callers: Unknown.

### None /api/generate-pdf
Handler: `pages/api/generate-pdf.ts#default` in `pages/api/generate-pdf.ts:11`. Purpose: Unknown. Callers: Unknown.

### None /api/get-env-config
Handler: `pages/api/get-env-config.ts#default` in `pages/api/get-env-config.ts:3`. Purpose: Unknown. Callers: Unknown.

### None /api/get-masterdata
Handler: `pages/api/get-masterdata.ts#default` in `pages/api/get-masterdata.ts:6`. Purpose: Unknown. Callers: Unknown.

### None /api/get-submission-data
Handler: `pages/api/get-submission-data.ts#default` in `pages/api/get-submission-data.ts:5`. Purpose: Unknown. Callers: Unknown.

### None /api/save-template-data
Handler: `pages/api/save-template-data.ts#default` in `pages/api/save-template-data.ts:17`. Purpose: Unknown. Callers: Unknown.

### None /api/submission-approval
Handler: `pages/api/submission-approval.ts#default` in `pages/api/submission-approval.ts:14`. Purpose: Unknown. Callers: Unknown.

### None /api/submission-update
Handler: `pages/api/submission-update.ts#default` in `pages/api/submission-update.ts:17`. Purpose: Unknown. Callers: Unknown.

### None /api/templates
Handler: `pages/api/templates.ts#default` in `pages/api/templates.ts:5`. Purpose: Unknown. Callers: Unknown.

### PATCH /api/admin/update-template
Handler: `pages/api/admin/update-template.ts#PATCH` in `pages/api/admin/update-template.ts:6`. Purpose: Unknown. Callers: form-builder.

### POST /api/admin/create-template
Handler: `pages/api/admin/create-template.ts#POST` in `pages/api/admin/create-template.ts:6`. Purpose: Unknown. Callers: form-builder.

## Outbound Calls
form-builder outbound HTTP calls (41 in service.yaml).

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| `external:firebase` | - | - | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | DELETE | `/api/template/{}` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | DELETE | `/api/user/{}` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | DELETE | `/api/admin/delete-form/{}` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | DELETE | `/api/admin/delete-user/{}` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | GET | `/api/client` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | GET | `/api/master` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | GET | `/api/template` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | GET | `/api/template/{}` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | GET | `/api/user` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | GET | `/api/user/{}` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | GET | `/api/admin/get-client` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | GET | `/api/admin/get-form-list` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | GET | `/api/admin/get-form/{}` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | GET | `/api/admin/get-user-list` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | GET | `/api/admin/get-user/{}` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | GET | `/api/get-env-config` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | PATCH | `/api/submission/approve/{}/{}` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | PATCH | `/api/submission/update/{}` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | PATCH | `/api/template/{}` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | PATCH | `/api/user/{}` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | PATCH | `/api/admin/edit-user/{}` | - | - | Unknown | Unknown |
| `form-builder` | PATCH | `/api/admin/update-template` | - | - | Unknown | hard |
| Unknown (env:BASE_PATH) | PATCH | `/api/submission-approval` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | PATCH | `/api/submission-update` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | POST | `/api/auth/sso-login` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | POST | `/api/submission/create` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | POST | `/api/submission/generate-pdf` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | POST | `/api/submission/get-submission` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | POST | `/api/template` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | POST | `/api/template/get-template` | - | - | Unknown | Unknown |
| Unknown (env:API_URL) | POST | `/api/user` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | POST | `/api/admin/add-user` | - | - | Unknown | Unknown |
| `form-builder` | POST | `/api/admin/create-template` | - | - | Unknown | hard |
| Unknown (env:BASE_PATH) | POST | `/api/admin/login-sso-user` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | POST | `/api/generate-pdf` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | POST | `/api/get-masterdata` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | POST | `/api/get-submission-data` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | POST | `/api/save-template-data` | - | - | Unknown | Unknown |
| Unknown (env:BASE_PATH) | POST | `/api/templates` | - | - | Unknown | Unknown |
| Unknown (env:NEXT_PUBLIC_API_URL) | POST | `/api/submission/upload` | - | - | Unknown | Unknown |

Client call sites:

| Method | Path | Client | Base URL source | File |
|---|---|---|---|---|
| DELETE | `/api/template/{}` | axios | env:API_URL | `pages/api/admin/delete-form/[id].ts:12` |
| DELETE | `/api/user/{}` | axios | env:API_URL | `pages/api/admin/delete-user/[id].ts:11` |
| DELETE | `/api/admin/delete-form/{}` | axios | env:BASE_PATH | `app/components/Admin/FormManagement/FormGrid.tsx:168` |
| DELETE | `/api/admin/delete-user/{}` | axios | env:BASE_PATH | `app/components/Admin/UserManagement/UserGrid.tsx:148` |
| GET | `/api/client` | axios | env:API_URL | `pages/api/admin/get-client.ts:9` |
| GET | `/api/master` | axios | env:API_URL | `pages/api/get-masterdata.ts:9` |
| GET | `/api/template` | axios | env:API_URL | `pages/api/admin/get-form-list.ts:16` |
| GET | `/api/template/{}` | axios | env:API_URL | `pages/api/admin/get-form/[id].ts:15` |
| GET | `/api/user` | axios | env:API_URL | `pages/api/admin/get-user-list.ts:16` |
| GET | `/api/user/{}` | axios | env:API_URL | `pages/api/admin/get-user/[id].ts:11` |
| GET | `/api/admin/get-client` | axios | env:BASE_PATH | `app/components/Admin/FormManagement/Designer.tsx:325` |
| GET | `/api/admin/get-form-list` | axios | env:BASE_PATH | `app/components/Admin/FormManagement/FormGrid.tsx:123` |
| GET | `/api/admin/get-form/{}` | axios | env:BASE_PATH | `app/admin/templatebuilder/[id]/page.tsx:33` |
| GET | `/api/admin/get-user-list` | axios | env:BASE_PATH | `app/components/Admin/UserManagement/UserGrid.tsx:108` |
| GET | `/api/admin/get-user/{}` | axios | env:BASE_PATH | `app/components/Admin/UserManagement/UserGrid.tsx:131` |
| GET | `/api/get-env-config` | axios | env:BASE_PATH | `app/constants/app.constant.ts:35` |
| PATCH | `/api/submission/approve/{}/{}` | axios | env:API_URL | `pages/api/submission-approval.ts:34` |
| PATCH | `/api/submission/update/{}` | axios | env:API_URL | `pages/api/submission-update.ts:46` |
| PATCH | `/api/template/{}` | axios | env:API_URL | `pages/api/admin/update-template.ts:19` |
| PATCH | `/api/user/{}` | axios | env:API_URL | `pages/api/admin/edit-user/[id].ts:44` |
| PATCH | `/api/admin/edit-user/{}` | axios | env:BASE_PATH | `app/components/Admin/UserManagement/AddUser.tsx:244` |
| PATCH | `/api/admin/update-template` | axios | env:BASE_PATH | `app/components/Admin/TemplateBuilder.tsx:100` |
| PATCH | `/api/submission-approval` | axios | env:BASE_PATH | `app/feedback/submission/[submissionID]/page.tsx:101` |
| PATCH | `/api/submission-update` | axios | env:BASE_PATH | `app/components/RenderForms.tsx:355` |
| POST | `/api/auth/sso-login` | axios | env:API_URL | `pages/api/admin/login-sso-user.ts:13` |
| POST | `/api/submission/create` | axios | env:API_URL | `pages/api/save-template-data.ts:42` |
| POST | `/api/submission/generate-pdf` | axios | env:API_URL | `pages/api/generate-pdf.ts:22` |
| POST | `/api/submission/get-submission` | axios | env:API_URL | `pages/api/get-submission-data.ts:15` |
| POST | `/api/template` | axios | env:API_URL | `pages/api/admin/create-template.ts:13` |
| POST | `/api/template/get-template` | axios | env:API_URL | `pages/api/templates.ts:11` |
| POST | `/api/user` | axios | env:API_URL | `pages/api/admin/add-user.ts:44` |
| POST | `/api/admin/add-user` | axios | env:BASE_PATH | `app/components/Admin/UserManagement/AddUser.tsx:223` |
| POST | `/api/admin/create-template` | axios | env:BASE_PATH | `app/components/Admin/TemplateBuilder.tsx:95` |
| POST | `/api/admin/login-sso-user` | axios | env:BASE_PATH | `app/components/Admin/Login.tsx:54` |
| POST | `/api/generate-pdf` | axios | env:BASE_PATH | `app/feedback/[templateID]/page.tsx:137` |
| POST | `/api/get-masterdata` | axios | env:BASE_PATH | `app/components/Admin/Dashboard.tsx:185` |
| POST | `/api/get-submission-data` | axios | env:BASE_PATH | `app/feedback/submission/[submissionID]/page.tsx:60` |
| POST | `/api/save-template-data` | axios | env:BASE_PATH | `app/components/RenderForms.tsx:334` |
| POST | `/api/templates` | axios | env:BASE_PATH | `app/feedback/[templateID]/page.tsx:61` |
| POST | `/api/submission/upload` | axios | env:NEXT_PUBLIC_API_URL | `app/components/RenderForms.tsx:234` |

## Schemas
form-builder DTOs/payloads referenced in this file.
N/A — no referenced schema resolved.

## Events Published
form-builder publishes 0 messaging entit(y/ies).

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| N/A | | | | | no publishers in code | |

## Events Consumed
form-builder consumes 0 messaging entit(y/ies).

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| N/A | | | | | | no consumers in code | | |

## External Integrations
form-builder third-party systems detected in code.

| System | Purpose | Auth |
|---|---|---|
| `external:firebase` | category other; matched `firebase` at `package.json:25` | Unknown |

## Rate Limits and SLAs
form-builder: N/A — not determinable from code.
