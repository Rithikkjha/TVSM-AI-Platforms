# API Specification Document — Location Master Service

**Service Name:** `tvsmbe-location` (location-master)  
**Base URL:** `https://{host}/location-master`  
**Version:** 1.0.0  
**Last Updated:** 2026-05-29  
**API Documentation (Swagger UI):** `/location-master/internal/swagger-tvs-mdp.html`

---

## Table of Contents

1. [Authentication & Authorization](#1-authentication--authorization)
2. [Common Response Structure](#2-common-response-structure)
3. [Error Responses](#3-error-responses)
4. [Admin Flow APIs](#4-admin-flow-apis)
5. [Dealer Flow APIs](#5-dealer-flow-apis)
6. [Mobile Flow APIs](#6-mobile-flow-apis)
7. [Dealer Proximity APIs](#7-dealer-proximity-apis)
8. [Dealer Search APIs](#8-dealer-search-apis)
9. [IB Dealer Management APIs](#9-ib-dealer-management-apis)
10. [Country APIs](#10-country-apis)
11. [Location Master APIs](#11-location-master-apis)
12. [Geocoding APIs](#12-geocoding-apis)
13. [Migration APIs](#13-migration-apis)
14. [User Management APIs](#14-user-management-apis)
15. [Test/Health APIs](#15-testhealth-apis)
16. [Validation Rules Summary](#16-validation-rules-summary)
17. [Rate Limits](#17-rate-limits)
18. [External API Dependencies](#18-external-api-dependencies)

---

## 1. Authentication & Authorization

### 1.1 Authentication Mechanism

| Aspect | Detail |
|--------|--------|
| Type | JWT Bearer Token (Azure AD B2C) |
| Header | `Authorization: <JWT_TOKEN>` |
| Validation | Delegated to Azure APIM Gateway (upstream) |
| Service Behavior | Extracts payload only, no signature verification |

### 1.2 JWT Token Payload Structure

```json
{
  "sub": "user-uuid-123",
  "name": "John Doe",
  "dealerId": "11016",
  "primaryPhoneNumber": "+919876543210",
  "baseRoles": [
    { "role": { "name": "Territory Manager" }, "department": "...", "group": "..." }
  ],
  "branches": [...]
}
```

### 1.3 Authorization Levels

| Level | Required Roles | API Patterns |
|-------|---------------|--------------|
| **Open** | None | `/v1/dealer-location/**`, `/api/v1/finder/**`, `/api/v1/location/**`, `/api/v1/country/**`, `/api/v1/dealer-search`, `/api/v1/dealership-locations/**`, `/api/v1/test/**`, `/api/v1/dealer-flow/dealerInfo` |
| **Admin** | `Territory Manager` OR `HR Manager` | `/api/v1/admin-flow/**`, `/api/v1/admin/migrate/**`, `/api/v1/dealer/**` |
| **Dealer** | `Dealer Owner/Partner` OR `Branch Manager` | `/api/v1/dealer-flow/**` |

---

## 2. Common Response Structure

### 2.1 Success Response Wrapper

```json
{
  "data": "<any>",
  "errorMessage": null,
  "time": "Thu May 29 10:30:00 IST 2026",
  "timeTakenInMs": null,
  "serverId": "instance-id-123"
}
```

### 2.2 Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `data` | Object/Array/String | Response payload (varies per endpoint) |
| `errorMessage` | String | null on success, error message on failure |
| `time` | String | Server timestamp |
| `timeTakenInMs` | Long | Processing time (present in some responses) |
| `serverId` | String | Server instance identifier |

---

## 3. Error Responses

### 3.1 HTTP Status Codes

| Status | Meaning | When |
|--------|---------|------|
| `200` | Success | All successful operations |
| `400` | Bad Request | Validation failures, business rule violations |
| `401` | Unauthorized | Missing/invalid JWT token |
| `403` | Forbidden | Insufficient role/permissions |
| `500` | Internal Server Error | Unexpected errors |

### 3.2 Error Response Format

**400 — Validation Error:**
```json
{
  "data": null,
  "errorMessage": "sapDealerCode is NULL",
  "time": "Thu May 29 10:30:00 IST 2026"
}
```

**400 — Invalid Enum Value:**
```json
{
  "data": null,
  "errorMessage": "Invalid value 'UNKNOWN' for field 'status'. Allowed values: [VERIFIED, REJECTED, VERIFICATION_PENDING, ...]",
  "time": "Thu May 29 10:30:00 IST 2026"
}
```

**401 — Unauthorized:**
```json
{
  "errorMessage": "Authorization is NULL",
  "timeTakenInMs": 5,
  "serverId": "instance-id-123"
}
```

**403 — Forbidden:**
```json
{
  "errorMessage": "Access Denied"
}
```

**500 — Internal Error:**
```json
{
  "data": null,
  "errorMessage": "Internal Error occurred",
  "time": "Thu May 29 10:30:00 IST 2026"
}
```

---

## 4. Admin Flow APIs

**Base Path:** `/api/v1/admin-flow`  
**Authentication:** Required (Admin roles)  
**Required Roles:** `Territory Manager` OR `HR Manager`

---

### 4.1 GET /api/v1/admin-flow/summary

**Description:** Get dealer location verification summary with counts per status.

**Request:** No body required.

**Response (200):**
```json
{
  "data": {
    "counts": [
      { "locationStatus": "VERIFICATION_TO_BE_INITIATED", "locationStatusUserFriendly": "Verification to be Initiated", "count": 150 },
      { "locationStatus": "VERIFICATION_INITIATED", "locationStatusUserFriendly": "Verification Initiated", "count": 25 },
      { "locationStatus": "VERIFICATION_PENDING", "locationStatusUserFriendly": "Verification Pending", "count": 10 },
      { "locationStatus": "VERIFIED", "locationStatusUserFriendly": "Verified", "count": 500 },
      { "locationStatus": "REJECTED", "locationStatusUserFriendly": "Rejected", "count": 5 },
      { "locationStatus": "RE_VERIFICATION_INITIATED", "locationStatusUserFriendly": "Re-Verification Initiated", "count": 3 },
      { "locationStatus": "RE_VERIFICATION_PENDING", "locationStatusUserFriendly": "Re-Verification Pending", "count": 2 }
    ]
  }
}
```

---

### 4.2 POST /api/v1/admin-flow/list

**Description:** Get paginated dealer list filtered by status with search.

**Request Body:**
```json
{
  "status": "VERIFICATION_PENDING",
  "page": 1,
  "size": 10,
  "searchTerm": "dealer name or code"
}
```

**Validation Rules:**
| Field | Rule |
|-------|------|
| `status` | Optional. Enum: VERIFICATION_TO_BE_INITIATED, VERIFICATION_INITIATED, VERIFICATION_PENDING, VERIFIED, REJECTED, RE_VERIFICATION_INITIATED, RE_VERIFICATION_PENDING |
| `page` | Required. Positive integer |
| `size` | Required. Positive integer |
| `searchTerm` | Optional. If present, min 3 chars |

**Response (200):**
```json
{
  "data": {
    "dealers": [
      {
        "sapDealerCode": "11016",
        "dealershipName": "TVS Dealer Chennai",
        "type": "AMD",
        "locationType": "SALES",
        "locationStatus": "VERIFICATION_PENDING",
        "locationStatusUserFriendly": "Verification Pending",
        "contact": { "phoneNumber": "9876543210", "email": "dealer@example.com" },
        "dmsStatus": "ACTIVE",
        "sapStatus": "ACTIVE",
        "mdpStatus": "ACTIVE",
        "sapAddress": { "address": "123, Main Road, Chennai, Tamil Nadu, 600001", "territory": "CHENNAI" },
        "dealershipLocationPhoto": { "url": "https://cdn.example.com/photo.jpg?sas=..." },
        "adminComments": null
      }
    ],
    "pageNo": 1,
    "totalNoRecords": 150
  }
}
```

---

### 4.3 POST /api/v1/admin-flow/verification

**Description:** Verify or reject a dealer's submitted location.

**Request Body:**
```json
{
  "sapDealerCode": "11016",
  "status": "VERIFIED",
  "locationType": "SALES",
  "adminComments": "Location verified successfully"
}
```

**Validation Rules:**
| Field | Rule |
|-------|------|
| `sapDealerCode` | Required. Max 100 chars |
| `status` | Required. Must be `VERIFIED` or `REJECTED` |
| `locationType` | Required. Enum: SALES, SERVICE |
| `adminComments` | Max 200 chars. **Required** if status is `REJECTED` |

**Response (200):**
```json
{
  "data": "Dealer's verification-status successfully updated"
}
```

**Error (400):**
```json
{
  "errorMessage": "status is invalid: VERIFICATION_PENDING"
}
```

---

### 4.4 GET /api/v1/admin-flow/dealer/{sapDealerCode}/location-type/{dealerLocationType}

**Description:** Get detailed dealer location information including distance matrix.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `sapDealerCode` | String | SAP dealer code (max 20 chars) |
| `dealerLocationType` | Enum | `SALES` or `SERVICE` |

**Response (200):**
```json
{
  "data": {
    "sapDealerCode": "11016",
    "dealershipName": "TVS Dealer Chennai",
    "type": "AMD",
    "locationType": "SALES",
    "locationStatus": "VERIFICATION_PENDING",
    "locationStatusUserFriendly": "Verification Pending",
    "submittedLocationDetails": {
      "latitude": 13.0827,
      "longitude": 80.2707,
      "addressLine1": "123 Main Road",
      "addressLine2": "Near Bus Stand",
      "addressLine3": "Chennai",
      "addressLine4": "Tamil Nadu",
      "googlePlaceId": "ChIJ...",
      "accuracy": 15.5
    },
    "imageCapturedLocationDetails": {
      "latitude": 13.0828,
      "longitude": 80.2708,
      "reverseGeocodedAddress": "123, Main Road, Chennai",
      "googlePlaceId": "ChIJ...",
      "accuracy": 10.2,
      "submittedAt": "2026-05-28T14:30:00"
    },
    "sapAddress": {
      "address": "123, Main Road, Chennai, Tamil Nadu, 600001, India",
      "territory": "CHENNAI",
      "latitude": 13.0830,
      "longitude": 80.2710
    },
    "contact": { "phoneNumber": "9876543210", "email": "dealer@example.com" },
    "dealershipLocationPhoto": { "url": "https://cdn.example.com/photo.jpg?sas=..." },
    "adminComments": null,
    "dmsStatus": "ACTIVE",
    "sapStatus": "ACTIVE",
    "mdpStatus": "ACTIVE",
    "locationUpdateSmsStatus": "DELIVERED",
    "distanceMatrix": [
      { "pointA": "SAP_ADDRESS_GEOLOCATION", "pointB": "USER_SUBMITTED_ADDRESS_GEOLOCATION", "distanceInMeters": 150 },
      { "pointA": "USER_SUBMITTED_ADDRESS_GEOLOCATION", "pointB": "USER_GEOLOCATION", "distanceInMeters": 25 },
      { "pointA": "USER_GEOLOCATION", "pointB": "SAP_ADDRESS_GEOLOCATION", "distanceInMeters": 160 }
    ]
  }
}
```

---

### 4.5 POST /api/v1/admin-flow/send-location-update-sms

**Description:** Send SMS to dealer with secret key for location submission.

**Request Body:**
```json
{
  "sapDealerCode": "11016",
  "phoneNumber": "+919876543210",
  "locationType": "SALES"
}
```

**Validation Rules:**
| Field | Rule |
|-------|------|
| `sapDealerCode` | Required. Max 20 chars |
| `phoneNumber` | Required. Max 13 chars |
| `locationType` | Required. Enum: SALES, SERVICE |

**Response (200):**
```json
{
  "data": "SMS sent successfully"
}
```

---

### 4.6 GET /api/v1/admin-flow/rejection-comments

**Description:** Get configurable rejection comment options.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | Enum | Yes | `REJECTION_COMMENTS` |

**Response (200):**
```json
{
  "data": [
    { "code": "WRONG_LOCATION", "description": "Location does not match dealer address" },
    { "code": "BLURRY_PHOTO", "description": "Photo is not clear enough" },
    { "code": "WRONG_PHOTO", "description": "Photo does not show dealership" }
  ]
}
```

---

### 4.7 GET /api/v1/admin-flow/{sapDealerCode}/contacts/{dealerLocationType}

**Description:** Get dealer and branch manager contact details.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `sapDealerCode` | String | SAP dealer code |
| `dealerLocationType` | Enum | `SALES` or `SERVICE` |

**Response (200):**
```json
{
  "data": {
    "dealerContacts": [
      { "name": "John Doe", "phoneNumber": "+919876543210", "role": "Dealer Owner" }
    ],
    "branchManagerContacts": [
      { "name": "Jane Smith", "phoneNumber": "+919876543211", "role": "Branch Manager" }
    ]
  }
}
```

---

## 5. Dealer Flow APIs

**Base Path:** `/api/v1/dealer-flow`  
**Authentication:** Required (Dealer roles, except `/dealerInfo`)  
**Required Roles:** `Dealer Owner/Partner` OR `Branch Manager`

---

### 5.1 GET /api/v1/dealer-flow/dealerInfo

**Description:** Get dealer info by secret key (Open API — no JWT required).

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `secretKey` | String | Yes | 5-char secret key from SMS |

**Response (200):**
```json
{
  "data": {
    "sapDealerCode": "11016",
    "locationType": "SALES",
    "phoneNo": "9876543210",
    "sapAddress": "123, Main Road, Chennai, Tamil Nadu, 600001, India",
    "dealershipName": "TVS Dealer Chennai",
    "type": "AMD"
  }
}
```

**Error (400):**
```json
{
  "errorMessage": "Invalid secret key : [abc12]"
}
```

---

### 5.2 GET /api/v1/dealer-flow/dealer/{sapDealerCode}

**Description:** Get dealer details with all branches and location statuses.

**Authorization:** Dealer can only access own data or own branches.

**Response (200):**
```json
{
  "data": {
    "sapDealerCode": "11016",
    "dealershipName": "TVS Dealer Chennai",
    "type": "AMD",
    "dmsStatus": "ACTIVE",
    "sapStatus": "ACTIVE",
    "mdpStatus": "ACTIVE",
    "contactDetails": { "phoneNumber": "9876543210", "email": "dealer@example.com" },
    "locations": [
      {
        "dealerLocationType": "SALES",
        "locationStatus": "VERIFIED",
        "locationStatusUserFriendly": "Verified",
        "address": { "addressLine1": "123 Main Road", "city": "Chennai", "stateName": "Tamil Nadu", "pincode": "600001" },
        "contactDetails": { "phoneNumber": "9876543210", "email": "dealer@example.com" },
        "uploadedPhoto": { "url": "https://cdn.example.com/photo.jpg?sas=..." }
      }
    ],
    "branches": [
      {
        "sapDealerCode": "11017",
        "dealershipName": "TVS Branch Adyar",
        "type": "BRANCH",
        "dealerLocationType": "SALES",
        "locationStatus": "VERIFICATION_INITIATED",
        "locationStatusUserFriendly": "Location Submission Pending",
        "tempDmsBranchSequence": 1,
        "address": { "addressLine1": "45 Adyar Road", "city": "Chennai", "stateName": "Tamil Nadu", "pincode": "600020" },
        "contactDetails": { "phoneNumber": "9876543211", "email": "branch@example.com" },
        "uploadedPhoto": null
      }
    ]
  }
}
```

---

### 5.3 GET /api/v1/dealer-flow/dealer/{sapDealerCode}/location-type/{dealerLocationType}

**Description:** Get dealer location details (dealer view — limited fields compared to admin).

**Authorization:** Dealer can only access own data.

**Response (200):** Same structure as admin dealer details but with dealer-friendly status names.

---

## 6. Mobile Flow APIs

**Base Path:** `/v1/dealer-location`  
**Authentication:** None (uses secret key for authorization)

---

### 6.1 POST /v1/dealer-location/submit

**Description:** Submit dealer location data with photo from mobile app.

**Content-Type:** `multipart/form-data`

**Request Parts:**
| Part | Type | Required | Description |
|------|------|----------|-------------|
| `data` | JSON | Yes | Location submission data |
| `file` | File | Yes | Dealership photo (max 100MB) |

**`data` JSON Structure:**
```json
{
  "secretKey": "ab12c",
  "submittedLocationDetails": {
    "latitude": 13.0827,
    "longitude": 80.2707,
    "addressLine1": "123 Main Road",
    "addressLine2": "Near Bus Stand",
    "addressLine3": "Chennai",
    "addressLine4": "Tamil Nadu",
    "googlePlaceId": "ChIJ...",
    "accuracy": 15.5
  },
  "imageCapturedLocationDetails": {
    "latitude": 13.0828,
    "longitude": 80.2708,
    "reverseGeocodedAddress": "123, Main Road, Chennai, Tamil Nadu",
    "googlePlaceId": "ChIJ...",
    "accuracy": 10.2
  }
}
```

**Validation Rules:**
| Field | Rule |
|-------|------|
| `secretKey` | Required. Max 10 chars |
| `submittedLocationDetails` | Required object |
| `submittedLocationDetails.addressLine1-4` | Required. Max 200 chars each |
| `submittedLocationDetails.latitude` | Required. Range: -90 to 90 |
| `submittedLocationDetails.longitude` | Required. Range: -180 to 180 |
| `submittedLocationDetails.accuracy` | Required. Range: 0 to configured threshold |
| `submittedLocationDetails.googlePlaceId` | Optional. Max 1000 chars |
| `imageCapturedLocationDetails` | Required object |
| `imageCapturedLocationDetails.reverseGeocodedAddress` | Required. Max 1000 chars |
| `imageCapturedLocationDetails.latitude` | Required. Range: -90 to 90 |
| `imageCapturedLocationDetails.longitude` | Required. Range: -180 to 180 |
| `imageCapturedLocationDetails.accuracy` | Required. Range: 0 to configured threshold |
| `file` | Required. Max 100MB |

**Response (200):**
```json
{
  "success": true,
  "message": "Dealer information updated successfully."
}
```

**Error (400):**
```json
{
  "success": false,
  "message": "Invalid secret key : [abc12]"
}
```

---

### 6.2 GET /v1/dealer-location/tcpp *(Deprecated)*

**Description:** Get Terms & Conditions and Privacy Policy documents.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `secretKey` | String | Yes | Valid secret key |

**Response (200):**
```json
{
  "data": {
    "privacyPolicy": "<base64-encoded-pdf>",
    "termsAndCondition": "<base64-encoded-pdf>"
  }
}
```

---

## 7. Dealer Proximity APIs

**Base Path:** `/api/v1/finder`  
**Authentication:** None (Open API)

---

### 7.1 POST /api/v1/finder/dealers

**Description:** Find nearest active dealers based on coordinates and filter type.

**Request Body:**
```json
{
  "latitude": 12.9716,
  "longitude": 77.5946,
  "limit": 10,
  "filterType": "TWO_WHEELER_SALES"
}
```

**Validation Rules:**
| Field | Rule |
|-------|------|
| `latitude` | Required. Range: -90 to 90 |
| `longitude` | Required. Range: -180 to 180 |
| `limit` | Required. Positive integer, max 20 |
| `filterType` | Required. Enum: TWO_WHEELER_SALES, TWO_WHEELER_SERVICE, TWO_WHEELER_APS, THREE_WHEELER_SALES, SUPER_PREMIUM_APACHE_RR310, SUPER_PREMIUM_APACHE_RTR310, SUPER_PREMIUM_TVS_RONIN, ELECTRIC_IQUBE, ELECTRIC_TVSX |

**Response (200):**
```json
{
  "data": [
    {
      "sapDealerCode": "11016",
      "name": "TVS Dealer Bangalore",
      "tempDmsBranchSequence": null,
      "parentAmdSapDealerCode": null,
      "location": {
        "latitude": 12.9750,
        "longitude": 77.5900,
        "googlePlusCode": "7J4V+XR Bangalore",
        "googleMapsUrl": "https://maps.google.com/?q=12.975,77.59"
      },
      "address": "45, MG Road, Bangalore, Karnataka, 560001, India",
      "distanceInKm": 2.5,
      "dealershipPhotoUrl": "https://cdn.example.com/photo.jpg?sas=...",
      "contact": {
        "primaryPhoneNumber": "9876543210",
        "secondaryPhoneNumber": "9876543211",
        "emailAddress": "dealer@example.com"
      }
    }
  ]
}
```

---

## 8. Dealer Search APIs

**Base Path:** `/api/v1/dealer-search`  
**Authentication:** None (Open API)

---

### 8.1 POST /api/v1/dealer-search

**Description:** Search IB (International Business) dealers by country, location, or geo-coordinates.

**Request Body (Geo-based search):**
```json
{
  "countryCode": "IT",
  "locale": "en",
  "geoCode": {
    "latitude": 41.8919,
    "longitude": 12.5113,
    "radiusInKM": 50
  },
  "dealerFilterType": "TWO_WHEELER_SALES",
  "pagination": { "page": 1, "size": 20 }
}
```

**Request Body (Location-based search):**
```json
{
  "countryCode": "IT",
  "locale": "en",
  "location": {
    "province": "Lazio",
    "city": "Rome"
  },
  "dealerFilterType": "TWO_WHEELER_SALES",
  "pagination": { "page": 1, "size": 20 }
}
```

**Request Body (Country-only search):**
```json
{
  "countryCode": "IT",
  "locale": "en",
  "pagination": { "page": 1, "size": 20 }
}
```

**Validation Rules:**
| Field | Rule |
|-------|------|
| `countryCode` | Required. Max 2 chars |
| `locale` | Optional. Max 2 chars |
| `geoCode.latitude` | Range: -90 to 90 |
| `geoCode.longitude` | Range: -180 to 180 |
| `geoCode.radiusInKM` | Optional. Positive long |
| `location.province` | Required if location present. Max 100 chars |
| `location.city` | Optional. Max 100 chars |
| `dealerFilterType` | Optional. Enum values |
| `pagination.page` | Positive integer |
| `pagination.size` | Positive integer, max 100 |

**Response (200):**
```json
{
  "data": {
    "dealers": [
      {
        "dealerCode": "IT001",
        "dealershipName": "TVS Roma Centro",
        "location": {
          "address": "Via Roma 123, 00100 Roma",
          "city": "Roma",
          "province": "Lazio",
          "zipCode": "00100",
          "geoCode": { "latitude": 41.8920, "longitude": 12.5115 }
        },
        "contacts": {
          "phoneNumbers": [{ "type": "PRIMARY", "value": "+39061234567" }],
          "emailAddresses": [{ "type": "PRIMARY", "value": "roma@tvs.it" }]
        },
        "distanceInKm": 3.2
      }
    ],
    "total": 15,
    "page": 1,
    "size": 20
  }
}
```

---

## 9. IB Dealer Management APIs

**Base Path:** `/api/v1/dealer`  
**Authentication:** Required (Admin roles)  
**Required Roles:** `Territory Manager` OR `HR Manager`

---

### 9.1 POST /api/v1/dealer

**Description:** Create a new IB dealer.

**Request Body:**
```json
{
  "dealerCode": "IT001",
  "dealershipName": "TVS Roma Centro",
  "status": "ACTIVE",
  "flags": ["TWO_WHEELER_SALES", "TWO_WHEELER_SERVICE"],
  "location": {
    "countryCode": "IT",
    "address": "Via Roma 123",
    "zipcode": "00100",
    "city": "Roma",
    "province": "Lazio",
    "latitude": 41.8920,
    "longitude": 12.5115
  },
  "contacts": {
    "phoneNumbers": [{ "type": "PRIMARY", "value": "+39061234567" }],
    "emailAddresses": [{ "type": "PRIMARY", "value": "roma@tvs.it" }]
  }
}
```

**Validation Rules:**
| Field | Rule |
|-------|------|
| `dealerCode` | Required. Max 50 chars |
| `dealershipName` | Required. Max 100 chars |
| `status` | Required. Must be `ACTIVE` or `PRE_ACTIVE` (cannot create DELETED/INACTIVE) |
| `flags` | Required. Non-empty list, all elements non-null |
| `location` | Required object |
| `location.countryCode` | Required. Max 3 chars. Must exist in country collection |
| `location.province` | Required. Max 100 chars |
| `location.city` | Required. Max 100 chars |
| `location.address` | Required. Max 500 chars |
| `location.latitude` | Optional. Range: -90 to 90. Must be provided with longitude |
| `location.longitude` | Optional. Range: -180 to 180. Must be provided with latitude |

**Response (200):**
```json
{
  "data": {
    "id": "665abc123def456",
    "dealerCode": "IT001",
    "dealershipName": "TVS Roma Centro",
    "status": "ACTIVE",
    "flags": ["TWO_WHEELER_SALES", "TWO_WHEELER_SERVICE"],
    "location": {
      "countryCode": "IT",
      "address": "Via Roma 123",
      "zipcode": "00100",
      "city": "Roma",
      "province": "Lazio",
      "geoCode": { "latitude": 41.892, "longitude": 12.5115 }
    },
    "contacts": { ... },
    "createdAt": "2026-05-29T10:30:00",
    "updatedAt": "2026-05-29T10:30:00"
  }
}
```

---

### 9.2 PUT /api/v1/dealer/{id}

**Description:** Update an existing IB dealer.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | String | MongoDB document ID |

**Request Body:** Same as POST (CreateDealerRequest).

**Business Rules:**
- `countryCode` cannot be changed after creation
- If no fields changed, update is skipped

**Response (200):**
```json
{
  "data": {
    "dealerCode": "IT001",
    "dealershipName": "TVS Roma Centro Updated",
    "status": "ACTIVE"
  }
}
```

---

### 9.3 GET /api/v1/dealer/summary

**Description:** Get dealer count summary by status for a country.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `countryCode` | String | Yes | ISO country code |

**Response (200):**
```json
{
  "data": {
    "totalDealers": 150,
    "activeDealers": 120,
    "preActiveDealers": 15,
    "inactiveDealers": 10,
    "deletedDealers": 5
  }
}
```

---

### 9.4 POST /api/v1/dealer/list

**Description:** List IB dealers with filters and pagination.

**Request Body:**
```json
{
  "countryCode": "IT",
  "search": "Roma",
  "province": "Lazio",
  "city": "Roma",
  "flag": "TWO_WHEELER_SALES",
  "status": "ACTIVE",
  "pagination": { "page": 1, "size": 10 }
}
```

**Validation Rules:**
| Field | Rule |
|-------|------|
| `countryCode` | Required. Max 3 chars |
| `search` | Optional. Min 3 chars, max 100 chars |
| `province` | Optional. Max 100 chars |
| `city` | Optional. Max 100 chars |
| `flag` | Optional. DealerFilterType enum |
| `status` | Optional. DealershipStatus enum |
| `pagination.page` | Positive, max 10000 |
| `pagination.size` | Positive, max 100 |

**Response (200):**
```json
{
  "data": {
    "total": 45,
    "page": 1,
    "size": 10,
    "dealers": [ ... ]
  }
}
```

---

### 9.5 POST /api/v1/dealer/export

**Description:** Export dealers to Excel file.

**Request Body:** Same as `/api/v1/dealer/list` (DealerSearchFilterRequest).

**Response:** Binary file download (XLSX).

**Response Headers:**
```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename=Dealers_IT_29-05-2026.xlsx
```

---

## 10. Country APIs

**Base Path:** `/api/v1/country`  
**Authentication:** None (Open API)

---

### 10.1 GET /api/v1/country/{countryCode}/filter-config

**Description:** Get country-specific dealer filter configuration and UI settings.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `countryCode` | String | ISO 3166-1 alpha-2 code (e.g., "IN", "IT") |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `locale` | String | No | Language code (e.g., "en", "it") |

**Response (200):**
```json
{
  "data": {
    "code": "IT",
    "name": "Italy",
    "defaultLocale": "it",
    "dealerSearchProximityLimit": 20,
    "showFrontImage": true,
    "showDirectionButton": true,
    "showGetSmsButton": false,
    "centroid": { "latitude": 41.8719, "longitude": 12.5674 },
    "filterConfig": {
      "viewMode": "LIST",
      "filterOptions": [
        {
          "name": "TWO_WHEELER_SALES",
          "friendlyName": "2W Sales",
          "icon": "bike_icon",
          "isDefault": true,
          "subCategories": []
        }
      ]
    }
  }
}
```

---

### 10.2 GET /api/v1/country/{countryCode}/provinces

**Description:** Get list of provinces and cities for a country (from active dealers).

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `countryCode` | String | ISO country code (max 2 chars) |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `locale` | String | No | Language code |

**Response (200):**
```json
{
  "data": {
    "countryCode": "IT",
    "provinces": [
      { "name": "Lazio", "cities": ["Roma", "Latina", "Viterbo"] },
      { "name": "Lombardia", "cities": ["Milano", "Bergamo", "Brescia"] }
    ]
  }
}
```

---

## 11. Location Master APIs

**Base Path:** `/api/v1/location`  
**Authentication:** None (Open API)

---

### 11.1 GET /api/v1/location/states

**Description:** Get all Indian states.

**Response (200):**
```json
[
  { "id": "...", "stateName": "Tamil Nadu", "stateCode": "TN" },
  { "id": "...", "stateName": "Karnataka", "stateCode": "KA" }
]
```

---

### 11.2 GET /api/v1/location/{childAdministrativeLocationType}/list

**Description:** Get location hierarchy data (districts, areas, pincodes) by parent.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `childAdministrativeLocationType` | Enum | `STATE`, `DISTRICT`, `AREA`, `PINCODE`, `AREA_PINCODE` |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `parentType` | Enum | Yes | `COUNTRY`, `STATE`, `STATE_CODE`, `DISTRICT` |
| `parentName` | String | Yes | Parent location name (max 100 chars, no special chars) |

**Valid Combinations:**
| parentType | childType | Returns |
|-----------|-----------|---------|
| COUNTRY | STATE | List of states with codes |
| STATE | DISTRICT | List of district names |
| STATE | AREA | List of {district, pincode, area} |
| STATE | PINCODE | List of pincodes |
| STATE | AREA_PINCODE | List of {area, pincode} |
| DISTRICT | AREA | List of {area, pincode} |
| DISTRICT | PINCODE | List of pincodes |
| STATE_CODE | DISTRICT | Resolves state code → state name, then returns districts |

**Sample Request:**
```
GET /api/v1/location/DISTRICT/list?parentType=STATE&parentName=TAMIL%20NADU
```

**Response (200):**
```json
{
  "data": ["CHENNAI", "COIMBATORE", "MADURAI", "SALEM", "TIRUCHIRAPPALLI"]
}
```

---

### 11.3 GET /api/v1/location/pincode/{pincode}

**Description:** Get detailed information for a pincode.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `pincode` | String | 6-digit pincode |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `country` | String | Yes | Country code (e.g., "IND") |

**Validation:** Pincode must be exactly 6 digits, numeric, positive.

**Response (200):**
```json
{
  "data": {
    "details": {
      "state": "TAMIL NADU",
      "stateCode": "TN",
      "division": "CHENNAI",
      "district": "CHENNAI",
      "centroid": { "latitude": 13.0827, "longitude": 80.2707 }
    },
    "areas": [
      { "area": "ADYAR", "latitude": 13.0063, "longitude": 80.2574 },
      { "area": "BESANT NAGAR", "latitude": 13.0002, "longitude": 80.2668 }
    ]
  }
}
```

---

## 12. Geocoding APIs

**Base Path:** `/api/v1/geo`  
**Authentication:** None (Open API)

---

### 12.1 GET /api/v1/geo/geocode

**Description:** Forward or reverse geocoding via Google Maps API.

**Query Parameters (Forward Geocoding):**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `address` | String | Yes* | Address to geocode |

**Query Parameters (Reverse Geocoding):**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | String | Yes* | Latitude |
| `lng` | String | Yes* | Longitude |

*Either `address` OR (`lat` + `lng`) must be provided.

**Response (200) — Forward Geocoding:**
```json
{
  "data": {
    "results": [
      {
        "formatted_address": "123, Main Road, Chennai, Tamil Nadu 600001, India",
        "geometry": {
          "location": { "lat": "13.0827", "lng": "80.2707" }
        },
        "place_id": "ChIJ..."
      }
    ],
    "status": "OK"
  }
}
```

---

## 13. Migration APIs

**Base Path:** `/api/v1/admin/migrate`  
**Authentication:** Required (Admin roles)

---

### 13.1 POST /api/v1/admin/migrate/location-data

**Description:** Import location master data from CSV file.

**Content-Type:** `multipart/form-data`

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | CSV file with headers: Division Name, Area, Pincode, District, StateName, Country, Latitude, Longitude |

**Response (200):**
```json
{
  "data": {
    "insertedRecordsCount": 150,
    "duplicateRecordsCount": 5,
    "duplicateRecords": [...],
    "updatedRecordsCount": 10,
    "updatedRecords": [...]
  }
}
```

---

### 13.2 POST /api/v1/admin/migrate/import-dealership-locations

**Description:** Import IB dealership locations from XLSX file.

**Content-Type:** `multipart/form-data`

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `countryCode` | String | Yes | Target country code |
| `dealershipLocationXlsx` | File | Yes | XLSX file (must be `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) |

**Response (200):**
```json
{
  "data": {
    "insertCount": 50,
    "updateCount": 30,
    "deleteCount": 5
  }
}
```

---

## 14. User Management APIs

**Base Path:** `/api/v1/user-x`  
**Authentication:** Required (Admin roles)

---

### 14.1 POST /api/v1/user-x

**Description:** Create internal user.

**Request Body:**
```json
{
  "userId": "azure-b2c-user-id",
  "phoneNumber": "+919876543210",
  "name": "John Doe",
  "role": "TERRITORY_MANAGER"
}
```

**Enum Values for `role`:** `ADMIN`, `DEALER`, `TERRITORY_MANAGER`

---

### 14.2 GET /api/v1/user-x/{userId}

**Description:** Get user data by Azure B2C user ID.

---

### 14.3 DELETE /api/v1/user-x/{userId}

**Description:** Delete user.

---

### 14.4 POST /api/v1/user-x/{userId}/owned-entity

**Description:** Add owned entity (territory, dealer, location type) to user.

**Request Body:**
```json
{
  "type": "TERRITORY",
  "whats": ["CHENNAI", "BANGALORE"]
}
```

**Enum Values for `type`:** `COUNTRY`, `DEALER`, `DEALER_LOCATION_TYPE`, `TERRITORY`, `AREA`, `ZONE`

---

### 14.5 PUT /api/v1/user-x/{userId}/owned-entity/delete

**Description:** Remove owned entity from user.

---

### 14.6 GET /api/v1/user-x/{userId}/countries

**Description:** Get list of countries accessible to user.

---

## 15. Test/Health APIs

**Base Path:** `/api/v1/test`  
**Authentication:** None (Open API)

---

### 15.1 GET /api/v1/test/health

**Description:** Health check with environment info.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sapDealerCode` | String | Yes | Any dealer code (for testing) |

**Response (200):**
```json
{
  "data": {
    "activeProfile": "uat",
    "sapDealerCode": "11016",
    "key": "testUpness_1716969600000",
    "dateTimeNow": "Thu May 29 10:30:00 IST 2026",
    "version-x": "53 - Fri May 22 12:08:24 IST 2026"
  },
  "serverId": "instance-id-123"
}
```

---

### 15.2 GET /api/v1/test/mdp-dealer-data/{sapDealerCode}

**Description:** Test MDP integration by fetching dealer data.

---

### 15.3 POST /api/v1/test/distance-calculator

**Description:** Calculate distance between two coordinates using all formulas.

**Request Body:**
```json
{
  "lat1": 13.0827,
  "lon1": 80.2707,
  "lat2": 12.9716,
  "lon2": 77.5946
}
```

**Response (200):**
```json
{
  "data": {
    "HAVERSINE": { "distance": 290123.5, "measurementType": "METER", "timeTaken": 2 },
    "VINCENTY": { "distance": 290145.2, "measurementType": "METER", "timeTaken": 5 },
    "EQUIRECTANGULAR_DISTANCE_APPROXIMATION": { "distance": 289980.1, "measurementType": "METER", "timeTaken": 1 }
  }
}
```

---

### 15.4 DELETE /api/v1/test/cache/{cacheName}/{key}

**Description:** Clear specific cache entry.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `cacheName` | Enum | `AZURE_B2C_TOKEN` or `COUNTRY_PROVINCES` |
| `key` | String | Cache key (e.g., `MDP`, `NOTIFICATION`, `UMS`) |

---

## 16. Validation Rules Summary

### 16.1 Common Field Validations

| Field Type | Validation | Error Message Pattern |
|-----------|-----------|---------------------|
| Required String | Not null, not empty after trim | `"{field} is NULL"` or `"{field} (string) is EMPTY"` |
| Max Length | `str.length() <= max` | `"{field} cannot exceed {max} characters"` |
| Latitude | -90 ≤ value ≤ 90 | `"{field} must be between -90 and 90 degrees"` |
| Longitude | -180 ≤ value ≤ 180 | `"{field} must be between -180 and 180 degrees"` |
| Positive Integer | value > 0 | `"{field} should be positive"` |
| Pincode | 6 digits, numeric, positive | `"Invalid {field} provided"` |
| No Special Chars | `[a-zA-Z0-9\s]+` | `"{field} contains special characters, which are not allowed"` |
| Both or None | Both present or both null | `"{field1} and {field2} must be provided together"` |
| File Type | MIME type match | `"{field} must be of type {expected}"` |
| Enum | Valid enum value | `"Invalid value '{val}' for field '{field}'. Allowed values: [...]"` |

### 16.2 Pagination Defaults

| Parameter | Default | Min | Max |
|-----------|---------|-----|-----|
| `page` | 1 | 1 | 10000 |
| `size` | 10 | 1 | 100 (list), 1000 (search), 2000 (export) |

### 16.3 File Upload Limits

| Parameter | Limit |
|-----------|-------|
| Max file size | 100 MB |
| Max request size | 200 MB |
| Allowed XLSX type | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

---

## 17. Rate Limits

Rate limiting is handled at the **Azure API Management (APIM) gateway** level, not within the application itself.

| Aspect | Detail |
|--------|--------|
| Rate Limit Enforcement | Azure APIM (upstream) |
| Application-Level Throttling | None |
| Retry Behavior | External API calls retry up to 3 times on 401/5xx |
| Proximity Search Limit | Max 20 results per request |
| Export Limit | Max 2000 records per export |
| Secret Key Generation | Max 1000 attempts per generation call |

---

## 18. External API Dependencies

### 18.1 MDP (Master Data Platform)

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `{MDP_BASE_URL}/v1/dealer/{code}` | GET | Get single dealer data | Azure B2C Token |
| `{MDP_BASE_URL}/v1/dealers/data?fetchMdpActiveDealersOnly=true` | POST | Bulk dealer data | Azure B2C Token |
| `{MDP_BASE_URL}/v1/dealers/listOfSapDealerCode/basedOnFilters` | POST | List dealer codes with filters | Azure B2C Token |
| `{MDP_BASE_URL}/v1/dealer/{code}/branches` | GET | Get dealer branches | Azure B2C Token |
| `{MDP_BASE_URL}/v1/dealers/listOfDealerDetails/basedOnProximity` | POST | Proximity-based dealer search | Azure B2C Token |

**Retry:** 3 attempts on 401 (token refresh) and 5xx errors.

### 18.2 UMS (User Management Service)

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `{UMS_BASE_URL}/api/v1/dealer/get-contacts?dealerId={id}` | GET | Get dealer contacts | Azure B2C Token |
| `{UMS_BASE_URL}/auth/v1/app/token/validate` | POST | Validate JWT token | Azure B2C Token |

**Retry:** 3 attempts on 401/5xx.

### 18.3 Notification Service

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `{NOTIFICATION_BASE_URL}/api/v1/notification/sms` | POST | Send SMS | Azure B2C Token + APIM Key |
| `{NOTIFICATION_BASE_URL}/api/v1/notification/{id}` | GET | Check SMS status | Azure B2C Token + APIM Key |

**Retry:** 3 attempts on 401/5xx.

### 18.4 Google Maps Geocoding API

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `https://maps.googleapis.com/maps/api/geocode/json?address={addr}&key={key}` | GET | Forward geocoding | API Key |
| `https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={key}` | GET | Reverse geocoding | API Key |

### 18.5 Azure Blob Storage

| Operation | Purpose | Auth |
|-----------|---------|------|
| Upload blob | Store dealer photos | Connection String |
| Generate SAS URL | Time-limited read access to photos | Connection String |
| Download blob | Retrieve T&C/Privacy Policy docs | Connection String |

### 18.6 Azure AD B2C

| Operation | Purpose | Auth |
|-----------|---------|------|
| POST token endpoint | Generate service-to-service tokens | Client Credentials (client_id + client_secret) |

**Token Caching:** In-memory with 60-second buffer before actual expiry.

---

## Appendix A: Enum Values Reference

### DealerLocationStatus
```
VERIFICATION_TO_BE_INITIATED | VERIFICATION_INITIATED | VERIFICATION_PENDING
VERIFIED | REJECTED | RE_VERIFICATION_INITIATED | RE_VERIFICATION_PENDING
```

### DealerLocationType
```
SALES | SERVICE | PARTS
```

### DealerFilterType
```
TWO_WHEELER_SALES | TWO_WHEELER_SERVICE | TWO_WHEELER_APS
THREE_WHEELER_SALES | SUPER_PREMIUM_APACHE_RR310 | SUPER_PREMIUM_APACHE_RTR310
SUPER_PREMIUM_TVS_RONIN | ELECTRIC_IQUBE | ELECTRIC_TVSX
```

### DealershipStatus
```
ACTIVE | DELETED | PRE_ACTIVE | INACTIVE
```

### DealerType
```
AMD | APS | BRANCH | AD
```

### UserRole
```
ADMIN | DEALER | TERRITORY_MANAGER
```

### ContactType
```
PRIMARY | SECONDARY
```

### UserOwnedEntityType
```
COUNTRY | DEALER | DEALER_LOCATION_TYPE | TERRITORY | AREA | ZONE
```

### RejectionCommentType
```
REJECTION_COMMENTS
```

### UserInputAdministrativeLocationType
```
COUNTRY | STATE | STATE_CODE | DISTRICT | AREA | PINCODE | AREA_PINCODE
```

---

## Appendix B: OpenAPI 3.0 Schema Definitions

```yaml
openapi: 3.0.3
info:
  title: Location Master Service API
  version: 1.0.0
  description: Centralized platform for managing TVS Motor dealer location data
servers:
  - url: https://{host}/location-master
    variables:
      host:
        default: localhost:8080

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: Azure AD B2C JWT token (validated by APIM gateway)

  schemas:
    GeneralResponse:
      type: object
      properties:
        data:
          description: Response payload
        errorMessage:
          type: string
          nullable: true
        time:
          type: string
        timeTakenInMs:
          type: integer
          format: int64
          nullable: true
        serverId:
          type: string
          nullable: true

    PointLocation:
      type: object
      properties:
        latitude:
          type: number
          format: decimal
          minimum: -90
          maximum: 90
        longitude:
          type: number
          format: decimal
          minimum: -180
          maximum: 180

    ProximitySearchRequest:
      type: object
      required: [latitude, longitude, limit, filterType]
      properties:
        latitude:
          type: number
          format: double
          minimum: -90
          maximum: 90
        longitude:
          type: number
          format: double
          minimum: -180
          maximum: 180
        limit:
          type: integer
          minimum: 1
          maximum: 20
        filterType:
          type: string
          enum: [TWO_WHEELER_SALES, TWO_WHEELER_SERVICE, TWO_WHEELER_APS, THREE_WHEELER_SALES, SUPER_PREMIUM_APACHE_RR310, SUPER_PREMIUM_APACHE_RTR310, SUPER_PREMIUM_TVS_RONIN, ELECTRIC_IQUBE, ELECTRIC_TVSX]

    DealerVerificationRequest:
      type: object
      required: [sapDealerCode, status, locationType]
      properties:
        sapDealerCode:
          type: string
          maxLength: 100
        status:
          type: string
          enum: [VERIFIED, REJECTED]
        locationType:
          type: string
          enum: [SALES, SERVICE]
        adminComments:
          type: string
          maxLength: 200
          description: Required when status is REJECTED

    LocationUpdateSmsRequest:
      type: object
      required: [sapDealerCode, phoneNumber, locationType]
      properties:
        sapDealerCode:
          type: string
          maxLength: 20
        phoneNumber:
          type: string
          maxLength: 13
        locationType:
          type: string
          enum: [SALES, SERVICE]

    DealerListRequest:
      type: object
      required: [page, size]
      properties:
        status:
          type: string
          enum: [VERIFICATION_TO_BE_INITIATED, VERIFICATION_INITIATED, VERIFICATION_PENDING, VERIFIED, REJECTED, RE_VERIFICATION_INITIATED, RE_VERIFICATION_PENDING]
        page:
          type: integer
          minimum: 1
        size:
          type: integer
          minimum: 1
        searchTerm:
          type: string
          minLength: 3

    DealerSearchRequest:
      type: object
      required: [countryCode]
      properties:
        countryCode:
          type: string
          maxLength: 2
        locale:
          type: string
          maxLength: 2
        geoCode:
          type: object
          properties:
            latitude:
              type: number
              minimum: -90
              maximum: 90
            longitude:
              type: number
              minimum: -180
              maximum: 180
            radiusInKM:
              type: integer
              format: int64
        location:
          type: object
          properties:
            province:
              type: string
              maxLength: 100
            city:
              type: string
              maxLength: 100
        dealerFilterType:
          type: string
          enum: [TWO_WHEELER_SALES, TWO_WHEELER_SERVICE, TWO_WHEELER_APS, THREE_WHEELER_SALES, SUPER_PREMIUM_APACHE_RR310, SUPER_PREMIUM_APACHE_RTR310, SUPER_PREMIUM_TVS_RONIN, ELECTRIC_IQUBE, ELECTRIC_TVSX]
        pagination:
          type: object
          properties:
            page:
              type: integer
              minimum: 1
            size:
              type: integer
              minimum: 1
              maximum: 100

    CreateDealerRequest:
      type: object
      required: [dealerCode, dealershipName, status, flags, location]
      properties:
        dealerCode:
          type: string
          maxLength: 50
        dealershipName:
          type: string
          maxLength: 100
        status:
          type: string
          enum: [ACTIVE, PRE_ACTIVE]
        flags:
          type: array
          items:
            type: string
            enum: [TWO_WHEELER_SALES, TWO_WHEELER_SERVICE, TWO_WHEELER_APS, THREE_WHEELER_SALES, SUPER_PREMIUM_APACHE_RR310, SUPER_PREMIUM_APACHE_RTR310, SUPER_PREMIUM_TVS_RONIN, ELECTRIC_IQUBE, ELECTRIC_TVSX]
          minItems: 1
        location:
          type: object
          required: [countryCode, province, city, address]
          properties:
            countryCode:
              type: string
              maxLength: 3
            address:
              type: string
              maxLength: 500
            zipcode:
              type: string
            city:
              type: string
              maxLength: 100
            province:
              type: string
              maxLength: 100
            latitude:
              type: number
              minimum: -90
              maximum: 90
            longitude:
              type: number
              minimum: -180
              maximum: 180
        contacts:
          type: object
          properties:
            phoneNumbers:
              type: array
              items:
                type: object
                properties:
                  type:
                    type: string
                    enum: [PRIMARY, SECONDARY]
                  value:
                    type: string
            emailAddresses:
              type: array
              items:
                type: object
                properties:
                  type:
                    type: string
                    enum: [PRIMARY, SECONDARY]
                  value:
                    type: string
```

---

*End of API Specification Document*
