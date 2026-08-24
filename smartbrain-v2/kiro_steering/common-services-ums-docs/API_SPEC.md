# API Specification Document — tvsm-auth (Auth Ninja)

| Attribute | Value |
|-----------|-------|
| Service | tvsm-auth (Auth Ninja) |
| Base URL (Dev) | `https://dev-api.tvsmotor.net` |
| Version | 1.0.0 |
| Content Type | `application/json` (unless multipart) |
| Max Upload Size | 5MB |

---

## Table of Contents

1. [Authentication Requirements](#1-authentication-requirements)
2. [Application Controller (Public)](#2-application-controller-public)
3. [User Profile Controller (Authenticated)](#3-user-profile-controller-authenticated)
4. [eKYC Controller (Authenticated)](#4-ekyc-controller-authenticated)
5. [Consent Controller (Public)](#5-consent-controller-public)
6. [Dealer Controller (Authenticated)](#6-dealer-controller-authenticated)
7. [Admin Controller (Authenticated)](#7-admin-controller-authenticated)
8. [Role Controller (Authenticated)](#8-role-controller-authenticated)
9. [Group Controller (Authenticated)](#9-group-controller-authenticated)
10. [Department Controller (Authenticated)](#10-department-controller-authenticated)
11. [User Application Controller (Authenticated)](#11-user-application-controller-authenticated)
12. [Dynamic Forms Controller (Authenticated)](#12-dynamic-forms-controller-authenticated)
13. [Error Responses](#13-error-responses)
14. [External API Dependencies](#14-external-api-dependencies)

---

## 1. Authentication Requirements

### JWT Bearer Token

All endpoints under `/api/v1/**` require a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

The token is issued by Azure AD B2C and validated by the service's `JwtTokenFilter`.

### Public Endpoints (No Auth Required)

| Path Pattern | Description |
|-------------|-------------|
| `/auth/v1/app/**` | OAuth flows, token operations |
| `/v1/app/**` | OAuth flows (alternate path) |
| `/api/v1/user/b2c-login-profile` | B2C login profile lookup |
| `/api/v1/user/b2c-login-profile-login-audit` | Login profile with audit |
| `/v1/user/ekyc/get-consent-content` | Consent content retrieval |
| `/v1/user/ekyc/submit-consent` | Consent submission |
| `/api/v1/dealer/get-contacts` | Dealer contacts |
| `/api/v1/admin/onboard-tvsm-user` | TVSM user onboarding |

### Rate Limiting

Rate limiting is enforced at the Azure API Management (APIM) layer, not within the application. Specific limits are configured per subscription/product in APIM.

---

## 2. Application Controller (Public)

**Base Path**: `/auth/v1/app` and `/v1/app`

### GET /token — Initiate OAuth Login

Redirects user to Azure B2C login page.

| Parameter | In | Required | Type | Description |
|-----------|-----|----------|------|-------------|
| `app_id` | query | Yes | string | Application client ID |
| `callback_uri` | query | No | string | Override callback URL |
| `country` | query | No | string | Country code (e.g., "IN") |
| `aut` | query | No | string | Auth type: `uid`, `otp`, `FID` |
| `lhi` | query | No | string | Login hint (phone number) |
| `scp` | query | No | string | Custom scope |

**Response**: `302 Found` → Redirect to B2C authorize URL

---

### GET /callback/{appName} — B2C Auth Callback

Receives auth code from B2C, exchanges for token, redirects to app.

| Parameter | In | Required | Type | Description |
|-----------|-----|----------|------|-------------|
| `appName` | path | Yes | string | Application name |
| `code` | query | No | string | Authorization code from B2C |
| `state` | query | No | string | Policy name |
| `error` | query | No | string | Error from B2C |

**Response**: `302 Found` → Redirect to `app_callback_uri?token=<jwt>`

---

### POST /token/validate — Validate JWT Token

| Parameter | In | Required | Type | Description |
|-----------|-----|----------|------|-------------|
| `Authorization` | header | Yes | string | Bearer token to validate |

**Request Body**:
```json
{
  "appId": "dca97542-7701-4dad-84de-49c161421ef4",
  "countryCode": "IN"
}
```

**Response** `200 OK`:
```json
{
  "valid": true
}
```

---

### POST /token/generate — Generate Service Token

Generates a B2C token using client credentials flow.

**Request Body**:
```json
{
  "appId": "client-id-here",
  "secret": "client-secret-here",
  "scope": "https://tenant.onmicrosoft.com/api/.default"
}
```

**Response** `200 OK`:
```json
{
  "idToken": "eyJ...",
  "accessToken": "eyJ...",
  "tokenType": "Bearer",
  "expiresIn": "3600"
}
```

---

### POST /face-login — Face-Based Login

**Content-Type**: `multipart/form-data`

| Part | Required | Type | Description |
|------|----------|------|-------------|
| `face` | Yes | file (JPEG/PNG) | Face image for identification |

**Response** `200 OK`:
```json
{
  "exists": true,
  "faceId": "abc-123-def",
  "personId": "person-uuid",
  "groupId": "large-person-group-id",
  "userId": 12345,
  "firstName": "John",
  "lastName": "Doe",
  "dealerId": "DEALER001",
  "status": "ACTIVE",
  "b2cId": "b2c-user-uuid"
}
```

---

### POST /face/session — Create Liveness Session

**Content-Type**: `multipart/form-data`

| Part | Required | Type | Description |
|------|----------|------|-------------|
| `image` | Yes | file (JPEG/PNG) | Reference image for verification |

**Response** `200 OK`:
```json
{
  "sessionId": "session-uuid",
  "authToken": "auth-token-for-client-sdk",
  "verifyImage": {
    "faceRectangle": { "top": 100, "left": 150, "width": 200, "height": 250 },
    "qualityForRecognition": "high"
  }
}
```

---

### POST /face/verification — Face Login with Liveness

**Content-Type**: `multipart/form-data`

| Part/Param | Required | Type | Description |
|------------|----------|------|-------------|
| `face` | Yes | file | Face image |
| `sessionId` | Yes | query string | Liveness session ID |

**Response** `200 OK`: Same as `/face-login`

---

### GET /get-login-form — Get Login Form Config

| Parameter | In | Required | Type | Description |
|-----------|-----|----------|------|-------------|
| `x-client-key` | header | Yes | string | Application client ID |

**Response** `200 OK`:
```json
{
  "appId": "dca97542-...",
  "name": "dms-app",
  "authMethods": ["OTP", "FID", "UID"],
  "title": "TVS Motor Login",
  "logoImageUrl": "https://blob.../logo.png?sv=..."
}
```

---

### GET /logout — End Session

| Parameter | In | Required | Type | Description |
|-----------|-----|----------|------|-------------|
| `app_id` | query | Yes | string | Application client ID |
| `country` | query | No | string | Country code |
| `aut` | query | No | string | Auth type |
| `errorMessage` | query | No | string | Error to display |

**Response**: `302 Found` → Redirect to B2C logout endpoint

---

### GET /test/health — Health Check

| Parameter | In | Required | Type |
|-----------|-----|----------|------|
| `beacon` | query | Yes | string |

**Response** `200 OK`:
```json
{
  "beacon": "test",
  "activeProfile": "dev",
  "key": "key",
  "dateTimeNow": "Mon Jun 01 10:30:00 IST 2026",
  "version-x": "1.5.49 Mon, Apr 10 11:45:00 IST 2026"
}
```

---

## 3. User Profile Controller (Authenticated)

**Base Path**: `/api/v1/user`

### POST /register-user — Register Dealer Employee

**Content-Type**: `multipart/form-data`

| Part | Required | Type | Description |
|------|----------|------|-------------|
| `face` | Yes | file (JPEG/PNG, max 5MB) | Face image |
| `data` | Yes | JSON | User registration data |

**`data` payload**:
```json
{
  "firstName": "Rajesh",
  "lastName": "Kumar",
  "primaryPhoneNumber": "+919876543210",
  "secondaryPhoneNumber": "+919876543211",
  "email": "rajesh@example.com",
  "gender": "MALE",
  "dateOfBirth": "1990/05/15",
  "address": {
    "line1": "123 Main St",
    "city": "Chennai",
    "state": "Tamil Nadu",
    "country": "India",
    "zipCode": "600001"
  },
  "baseRoles": [1, 2],
  "applicationIds": [1, 3]
}
```

**Response** `201 Created`:
```json
{
  "userDetails": {
    "id": 12345,
    "firstName": "Rajesh",
    "lastName": "Kumar",
    "status": "PENDING_ACTIVE",
    "b2cUserId": "uuid-from-b2c",
    "dealerId": "DEALER001"
  },
  "applications": [...]
}
```

**Validation Rules**:
- `face`: Must be JPEG/PNG, max 5MB, passes face quality checks
- `firstName`: Required, not blank
- `primaryPhoneNumber`: Must be unique, numeric with optional `+`
- `email`: Valid email format if provided

---

### POST /update-user — Update User with Face

**Content-Type**: `multipart/form-data`

| Part | Required | Type | Description |
|------|----------|------|-------------|
| `face` | No | file | Updated face image |
| `data` | Yes | JSON | Update payload (same structure as register) |

**Response** `200 OK`: Updated user details

---

### PUT /update — Update User Details (JSON only)

**Request Body**: `DealerEmployeeUpdateRequest` (same as register `data` + `id` field)

**Response** `200 OK`: Updated user details

---

### GET /pending-active — List Pending Active Users

| Parameter | In | Required | Type | Default |
|-----------|-----|----------|------|---------|
| `page` | query | No | int | 0 |
| `size` | query | No | int | 10 |

**Response** `200 OK`:
```json
{
  "content": [...],
  "totalElements": 25,
  "totalPages": 3,
  "currentPage": 0,
  "size": 10
}
```

---

### GET /{userId} — Get User Details

**Response** `200 OK`: Full user details with application mappings

---

### GET /{dealerId}/list-all — List Dealer Employees

| Parameter | In | Required | Type | Description |
|-----------|-----|----------|------|-------------|
| `dealerId` | path | Yes | string | Dealer identifier |
| `page` | query | No | int | Page number |
| `size` | query | No | int | Page size |
| `status` | query | No | enum | Filter: ACTIVE, INACTIVE, PENDING_ACTIVE, PASSIVE |
| `conflict` | query | No | boolean | Filter conflicted users |

**Response** `200 OK`: Paginated `DealerEmployeeResponseDto` list

---

### GET /list-all — List All Employees (Logged-in Dealer)

Same params as above (without `dealerId`), scoped to logged-in dealer.

---

### POST /change-status — Change User Status

**Request Body**:
```json
{
  "userId": 12345,
  "status": "ACCEPT"
}
```

**Valid status values**: `ACCEPT`, `DEACTIVATE`, `REJECT`, `CONFLICT_APPROVE`, `CONFLICT_REJECT`, `ACTIVATE`

**Response** `200 OK`:
```json
{
  "message": "User status changed successfully"
}
```

---

### POST /{userId} — Deactivate User

**Request Body**:
```json
{
  "reason": "Employee resigned",
  "exitReasonId": 3
}
```

**Response** `204 No Content`

---

### GET /verify-phone-exists/{phoneNumber} — Check Phone Uniqueness

**Response** `200 OK`:
```json
{
  "exists": true,
  "userId": 12345,
  "status": "ACTIVE"
}
```

---

### GET /counts — Profile Counts for Dealer

**Response** `200 OK`:
```json
{
  "totalActive": 45,
  "totalPendingActive": 5,
  "totalPassive": 3,
  "totalInactive": 12,
  "totalConflicted": 2
}
```

---

### GET /b2c-login-profile — Get User by B2C ID (Public)

| Parameter | In | Required | Type |
|-----------|-----|----------|------|
| `b2cUserId` | query | Yes | string |

**Response** `200 OK`: `AzureLoginUserResponse` with user details + roles

---

### GET /b2c-login-profile-login-audit — Login Profile + Audit

| Parameter | In | Required | Type |
|-----------|-----|----------|------|
| `b2cUserId` | query | Yes | string |
| `appId` | query | Yes | string |
| `aut` | query | No | string |

**Response** `200 OK`: Same as above + creates login audit record

---

### POST /verify-face-exists — Check Face Uniqueness

**Content-Type**: `multipart/form-data`

| Part | Required | Type |
|------|----------|------|
| `face` | Yes | file (JPEG/PNG) |

**Response** `200 OK`:
```json
{
  "exists": true,
  "userId": 12345
}
```

---

### POST /{userId}/update-profile-photo — Update Profile Photo

**Content-Type**: `multipart/form-data`

| Part | Required | Type |
|------|----------|------|
| `face` | Yes | file (JPEG/PNG) |

**Response** `200 OK`

---

### GET /trainings-certifications — List Training Options

**Response** `200 OK`: Set of `TrainingCertificationDto`

---

### POST /onboard-users-flx — Bulk User Onboarding (CSV)

**Content-Type**: `multipart/form-data`

| Part | Required | Type |
|------|----------|------|
| `users` | Yes | file (CSV) |

**Response** `200 OK`: CSV file download (response report)

---

### POST /activate-users-flx — Bulk Activate Users

**Request Body**: `List<Long>` (user IDs)

**Response** `200 OK`: CSV file download (activation report)

---

### POST /register-user-flx — Register User (FLX Flow)

**Request Body**: `UserRegisterDto`

**Response** `200 OK` or `400 Bad Request`

---

### POST /self-registration — Self Onboarding

**Request Body**: `UserRegisterDto`

**Response** `200 OK`:
```json
{
  "status": true,
  "reason": null,
  "userId": 12345
}
```

---

### POST /send-consent — Send Consent SMS

| Parameter | In | Required | Type |
|-----------|-----|----------|------|
| `userId` | query | Yes | Long |

**Response** `200 OK`:
```json
{
  "message": "SMS sent successfully",
  "smsSent": true
}
```

---

### GET /get-all-reporting-managers — List Reporting Managers

| Parameter | In | Required | Type |
|-----------|-----|----------|------|
| `roleId` | query | Yes | Long |

**Response** `200 OK`: `List<ReportingManagerDto>`

---

### GET /list-exit-reasons — Get Exit Reasons

**Response** `200 OK`: `ExitReasonResponseDto`

---

### GET /get-user-exit-reasons/{primaryPhoneNumber} — User Exit History

**Response** `200 OK`: `List<UserExitDetailsDto>`

---

### POST /bulk-deactivation — Bulk Deactivate Users

**Request Body**: `List<Long>` (user IDs, non-empty)

**Response** `200 OK`:
```json
{
  "successCount": 8,
  "failedCount": 2,
  "failures": [...]
}
```

---

### GET /download-consent — Download Consent Template

**Response** `200 OK`: Binary file (PDF), `Content-Disposition: attachment`

---

### GET /download-signed-consent — Download Signed Consent

| Parameter | In | Required | Type |
|-----------|-----|----------|------|
| `userId` | query | Yes | Long |

**Response** `200 OK`: Binary file (PDF)

---

### GET /download-passbook — Download Passbook

| Parameter | In | Required | Type |
|-----------|-----|----------|------|
| `userId` | query | Yes | Long |

**Response** `200 OK`: Binary file

---

## 4. eKYC Controller (Authenticated)

**Base Path**: `/api/v1/user/ekyc`

### POST /verify — Verify User eKYC

**Request Body**:
```json
{
  "userId": 12345,
  "ekycType": "PAN",
  "panNumber": "ABCDE1234F",
  "fullName": "Rajesh Kumar",
  "externalCall": false
}
```

For DL verification:
```json
{
  "userId": 12345,
  "ekycType": "DL",
  "drivingLicenseNumber": "TN0120190012345",
  "dateOfBirth": "1990-05-15",
  "externalCall": false
}
```

For Bank verification:
```json
{
  "userId": 12345,
  "ekycType": "BANK",
  "accountNumber": "1234567890123",
  "ifscCode": "SBIN0001234",
  "externalCall": false
}
```

**Validation Rules**:
- `userId`: Required
- `ekycType`: Required, one of `PAN`, `DL`, `BANK`
- `panNumber`: Required when ekycType=PAN
- `drivingLicenseNumber` + `dateOfBirth`: Required when ekycType=DL
- `accountNumber` + `ifscCode`: Required when ekycType=BANK
- User must have accepted consent
- eKYC must be enabled for user's assigned application

**Response** `200 OK`:
```json
{
  "verified": true,
  "comments": "PAN Validation successful with name match score : 0.95",
  "userNameFromEKyc": "RAJESH KUMAR"
}
```

**Response (already verified)**:
```json
{
  "verified": true,
  "comments": "PAN already verified",
  "userNameFromEKyc": null
}
```

**Response (name mismatch)**:
```json
{
  "verified": false,
  "comments": "Name mismatch with name match score : 0.45",
  "userNameFromEKyc": "RAJESH K"
}
```

---

## 5. Consent Controller (Public)

**Base Path**: `/v1/user`

### GET /ekyc/get-consent-content — Get Consent Content

| Parameter | In | Required | Type | Description |
|-----------|-----|----------|------|-------------|
| `key` | query | Yes | string | Encrypted consent key |

**Response** `200 OK`:
```json
{
  "privacyPolicy": "<html>...</html>",
  "termsAndConditions": "<html>...</html>"
}
```

---

### POST /ekyc/submit-consent — Submit User Consent

**Request Body**:
```json
{
  "key": "encrypted-key-string",
  "status": "ACCEPTED"
}
```

**Valid status values**: `ACCEPTED`, `REJECTED`

**Response** `200 OK`:
```json
{
  "message": "Consent submitted successfully"
}
```

---

## 6. Dealer Controller (Authenticated)

**Base Path**: `/api/v1/dealer`

### GET /branch/list-all — List All Branches

**Response** `200 OK`:
```json
[
  {
    "name": "Chennai Main Branch",
    "sapDealerCode": "ABC_DD",
    "tempDmsBranchSequence": 1
  }
]
```

---

### GET /get-contacts — Get Dealer Contacts (Public)

| Parameter | In | Required | Type |
|-----------|-----|----------|------|
| `dealerId` | query | Yes | string |

**Response** `200 OK`: `DealerContacts`

---

### POST /add-dealership — Register Dealership

**Request Body**: `DealershipDto`

**Response** `200 OK`: `Dealership` entity

---

### POST /onboard-dealers-flx — Bulk Dealer Onboarding (CSV)

**Content-Type**: `multipart/form-data`

| Part | Required | Type |
|------|----------|------|
| `dealerIds` | Yes | file (CSV) |

**Response** `200 OK`: CSV file download

---

### POST /upgrade-dealership — Migrate Dealership

**Request Body**: `DealershipMigrationDto`

**Response** `200 OK`: Updated `Dealership`

---

### GET /list-all — List All Dealers

| Parameter | In | Required | Type |
|-----------|-----|----------|------|
| `country` | query | No | string |
| `region` | query | No | string |
| `city` | query | No | string |

**Response** `200 OK`: `List<DealerDetailsResponse>`

---

## 7. Admin Controller (Authenticated)

**Base Path**: `/api/v1/admin`

### POST /onboard-tvsm-user — Onboard TVSM User (Public)

**Request Body**: `OnboardTvsmUserRequest`

**Response** `200 OK`: User details

---

### POST /register-user — Register Admin User

**Content-Type**: `multipart/form-data`

| Part | Required | Type |
|------|----------|------|
| `face` | No | file (JPEG/PNG) |
| `data` | Yes | JSON (`AdminUserOnboardRequest`) |

**Response** `200 OK`: Registered user details

---

### GET /dealerships — List Dealerships

| Parameter | In | Required | Type |
|-----------|-----|----------|------|
| `distributorId` | query | No | Long |

**Response** `200 OK`: List of dealerships

---

## 8. Role Controller (Authenticated)

**Base Path**: `/api/v1/role`

### POST /create — Create Role

**Request Body**:
```json
{
  "name": "Service Advisor",
  "description": "Handles service bookings",
  "permissionIds": [1, 2, 5, 8]
}
```

**Response** `201 Created`: Role entity

---

### PUT /update — Update Role

**Request Body**:
```json
{
  "id": 5,
  "name": "Senior Service Advisor",
  "description": "Updated description",
  "permissionIds": [1, 2, 5, 8, 12]
}
```

**Response** `200 OK`: Updated Role entity

---

### GET /{roleId}/get-types-specializations — Types & Specializations

**Response** `200 OK`: `TypeSpecializationDto`

---

### GET /{roleId}/get-designations — Designations by Role

**Response** `200 OK`: `List<DesignationDto>`

---

### GET /{roleId}/get-reporting-roles — Reporting Roles

**Response** `200 OK`: `ReportingRoleMappingDto`

---

### GET /{roleId}/get — Get Role with Sub-Roles

**Response** `200 OK`: `List<Role>`

---

## 9. Group Controller (Authenticated)

**Base Path**: `/api/v1/group`

### POST /create — Create Group

**Request Body**:
```json
{
  "name": "Sales Team",
  "description": "Sales department group",
  "roleIds": [1, 3, 5]
}
```

**Response** `201 Created`: Group entity

---

### PUT /update — Update Group

**Request Body**:
```json
{
  "id": 2,
  "name": "Sales Team Updated",
  "roleIds": [1, 3, 5, 7]
}
```

**Response** `200 OK`: Updated Group entity

---

### GET /{groupId}/roles — Get Roles by Group

**Response** `200 OK`: `Set<RolesDto>`

---

## 10. Department Controller (Authenticated)

**Base Path**: `/api/v1/department`

### GET /{departmentId}/get-all-groups — Groups by Department

**Response** `200 OK`: `Set<GroupsDto>`

---

### GET /list-all — List All Departments

**Response** `200 OK`:
```json
[
  { "id": 1, "name": "Sales" },
  { "id": 2, "name": "Service" },
  { "id": 3, "name": "Spare Parts" }
]
```

---

## 11. User Application Controller (Authenticated)

**Base Path**: `/api/v1/application`

### POST /assign-user — Assign Application to User

**Request Body**:
```json
{
  "userId": 12345,
  "applicationId": 3
}
```

**Response** `201 Created`: `UserAssignApplicationResponseDto`

---

### POST /remove-user — Remove Application from User

**Request Body**: Same as assign

**Response** `200 OK`: Success message

---

### GET /list-all — List All Applications

**Response** `200 OK`:
```json
[
  {
    "id": 1,
    "name": "dms-app",
    "clientId": "uuid-here",
    "userCount": 150
  }
]
```

---

### GET /{application-id} — Application with Users

**Response** `200 OK`: `ApplicationDetails` with user list

---

## 12. Dynamic Forms Controller (Authenticated)

**Base Path**: `/api/v1/dynamic-forms`

### POST /get-registration-form — Get Form Configuration

**Request Body**:
```json
{
  "applicationId": 3,
  "dealerId": "DEALER001"
}
```

**Response** `200 OK`: `FormResponse` with field definitions

---

### POST /validate — Validate Form Data

**Request Body**: `DynamicUserDto` (form field values)

**Response** `200 OK`:
```json
{
  "isValid": true,
  "errors": {}
}
```

**Response** `400 Bad Request`:
```json
{
  "isValid": false,
  "errors": {
    "firstName": "Field is required",
    "phoneNumber": "Invalid format"
  }
}
```

---

### POST /register — Register via Dynamic Form

**Content-Type**: `multipart/form-data`

| Part | Required | Type |
|------|----------|------|
| `face` | No | file |
| `body` | Yes | JSON (`DynamicUserDto`) |

**Response** `200 OK`: Registration result

---

### POST /user-details — Get User Details (Dynamic)

**Request Body**: `DynamicGetUserDetailsRequest`

**Response** `200 OK`: User details in dynamic form format

---

### POST /update/{userId} — Update via Dynamic Form

**Content-Type**: `multipart/form-data`

| Part | Required | Type |
|------|----------|------|
| `face` | No | file |
| `body` | Yes | JSON (`DynamicUserDto`) |

**Response** `200 OK`: Update result

---

## 13. Error Responses

### Standard Error Format

```json
{
  "status": "BAD_REQUEST",
  "timestamp": "Mon Jun 01 10:30:00 IST 2026",
  "message": "Descriptive error message"
}
```

### Validation Error Format

```json
{
  "firstName": "First name should not be empty.",
  "primaryPhoneNumber": "Field should contain only numeric and +",
  "email": "must be a well-formed email address"
}
```

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| `200` | OK | Successful operation |
| `201` | Created | Resource created (registration, role/group creation) |
| `204` | No Content | Successful deletion/deactivation |
| `302` | Found | OAuth redirects (login, callback, logout) |
| `400` | Bad Request | Validation failure, business rule violation |
| `401` | Unauthorized | Missing/invalid JWT token |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource not found |
| `500` | Internal Server Error | Unexpected server error |

### Common Error Messages

| Error | Cause |
|-------|-------|
| `"Auth Token & Client Id can't be empty"` | Missing Authorization or x-client-id header |
| `"Invalid Token or Client Id"` | JWT signature verification failed |
| `"Authorization token missing"` | No Authorization header on authenticated endpoint |
| `"User not found"` | B2C user ID not in local database |
| `"Consent is not accepted for user [X]"` | eKYC attempted before consent |
| `"EKYC is not enabled for the application"` | App doesn't have eKYC feature |
| `"Face verification failed: not live or not identical"` | Liveness check failed |
| `"Error fetching dealership from MDP"` | MDP API unavailable |

---

## 14. External API Dependencies

### 14.1 Azure AD B2C (Graph API)

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create User | POST | `https://graph.microsoft.com/v1.0/users` |
| Delete User | DELETE | `https://graph.microsoft.com/v1.0/users/{id}` |
| Update User | PATCH | `https://graph.microsoft.com/v1.0/users/{id}` |
| Find by Identity | GET | `https://graph.microsoft.com/v1.0/users?$filter=identities/any(...)` |
| OpenID Config | GET | `https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{policy}/v2.0/.well-known/openid-configuration` |
| Token Exchange | POST | `https://{tenant}.b2clogin.com/{tenant}.onmicrosoft.com/{policy}/oauth2/v2.0/token` |

### 14.2 Azure Face API

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Detect Face | POST | `{faceApiUrl}/face/v1.0/detect?returnFaceAttributes=...` |
| Identify Face | POST | `{faceApiUrl}/face/v1.0/identify` |
| Create Person Group | PUT | `{faceApiUrl}/face/v1.0/largepersongroups/{groupId}` |
| Add Person | POST | `{faceApiUrl}/face/v1.0/largepersongroups/{groupId}/persons/` |
| Add Face to Person | POST | `{faceApiUrl}/face/v1.0/largepersongroups/{groupId}/persons/{personId}/persistedfaces` |
| Train | POST | `{faceApiUrl}/face/v1.0/largepersongroups/{groupId}/train` |
| Remove Person | DELETE | `{faceApiUrl}/face/v1.0/largepersongroups/{groupId}/persons/{personId}` |
| Create Liveness Session | Azure SDK | `FaceSessionClient.createLivenessWithVerifySession()` |
| Get Session Result | Azure SDK | `FaceSessionClient.getLivenessWithVerifySessionResult()` |

### 14.3 Karza (eKYC)

| Operation | Method | Endpoint | Auth |
|-----------|--------|----------|------|
| PAN Validation | POST | `{karzaBaseUrl}/v3/pan-profile` | `x-karza-key` header |
| DL Validation | POST | `{karzaBaseUrl}/v3/dl` | `x-karza-key` header |
| Bank Account | POST | `{karzaBaseUrl}/v3/bankacc-verification` | `x-karza-key` header |
| Name Match | POST | `{karzaBaseUrl}/v3/name` | `x-karza-key` header |

### 14.4 MDP (Master Data Platform)

| Operation | Method | Endpoint | Auth |
|-----------|--------|----------|------|
| Fetch Dealer | GET | `{mdpBaseUrl}/v1/dealer/{dealerId}` | Bearer token |
| Fetch Branches | GET | `{mdpBaseUrl}/v1/dealer/{dealerId}/branches` | Bearer token |

### 14.5 Notification Service

| Operation | Method | Endpoint | Auth |
|-----------|--------|----------|------|
| Send SMS | POST | `{notificationBaseUrl}/api/v1/notification/sms` | Bearer token |

### 14.6 Azure Service Bus

| Operation | Protocol | Topic |
|-----------|----------|-------|
| Publish Event | AMQP (Azure SDK) | `{env}.ums.user_apps` |

Events published: `UmsUserActivatedEvent`, `UmsUserUpdatedEvent`, `UmsUserDeactivatedEvent`

---

## Appendix: Enum Reference

### Status
`ACTIVE`, `INACTIVE`, `PENDING_ACTIVE`, `PASSIVE`

### UserType
`DEALER_EMPLOYEE`, `HO`, `TVSM`, `DISTRIBUTOR`, `SUPPORT`, `CUSTOMER`

### Gender
`MALE`, `FEMALE`, `OTHER`

### EkycType
`PAN`, `DL`, `BANK`

### AuthenticationMethod
`OTP`, `UID`, `FID` (Face ID)

### UserStatusDto (Status Change Actions)
`ACCEPT`, `DEACTIVATE`, `REJECT`, `CONFLICT_APPROVE`, `CONFLICT_REJECT`, `ACTIVATE`

---

*This document is generated for engineering vendor reference. No secrets or credentials are exposed. For the machine-readable OpenAPI spec, refer to `api-specs.yml` in the repository root.*
