# API Specification — `tvsmbe-mdp-bff`

> Companion to the machine-readable spec at [`docs/openapi.yaml`](./openapi.yaml).
> Internal reference page: [MDP-BFF APIs Reference](https://tvsmotorcompany.atlassian.net/wiki/spaces/DA/pages/3684696080/MDP-BFF+APIs+Reference).
> No production credentials, tokens, or hostnames are included in this document.

This document covers everything that does not fit cleanly into the OpenAPI YAML: cross-cutting auth context, validation rules in narrative form, rate limits, external dependencies, and the message-driven (Service Bus) contract for the outbound service.

---

## 1. API endpoint list

The repository ships **two services**. Only the inbound service exposes business APIs; the outbound service exposes diagnostic endpoints only and is otherwise message-driven.

### Inbound BFF — context path `/mdp-bff`

| # | Method | Path | Purpose |
|---|---|---|---|
| 1 | `GET`  | `/v1/mdp/dealer/{sapDealerCode}` | Get dealer by SAP code |
| 2 | `GET`  | `/v1/mdp/dealers?pincode=...` | Get dealers by pincode |
| 3 | `POST` | `/v1/mdp/dealer/basedOnFilters` | Get dealers by filter |
| 4 | `POST` | `/webhook/v1/{mdpModule}/{externalClient}/{webHookEventType}` | Generic webhook intake |
| 5 | `GET`  | `/v1/test/hello` | Diagnostic |
| 6 | `GET`  | `/swagger-ui/index.html`, `/v3/api-docs` | API docs (springdoc; toggleable) |

### Outbound BFF — context path `/mdp-bff-outbound`

| # | Method | Path | Purpose |
|---|---|---|---|
| 1 | `GET` | `/v1/test/health` | Diagnostic + env/property introspection |
| 2 | `GET` | `/v1/test/hello` | Diagnostic + thread-pool stats |
| 3 | `GET` | `/swagger-ui/index.html`, `/v3/api-docs` | API docs |

The outbound service's primary contract is a **message-driven** consumer; see §9.2.

## 2. Request methods

- **GET** — single-dealer fetch, dealers-by-pincode, diagnostics, docs.
- **POST** — filter-based dealer fetch, webhook intake.

There are no `PUT`, `PATCH`, or `DELETE` endpoints exposed to callers.

## 3. Authentication requirements

### What callers of this BFF need to do
- **Nothing at the application layer.** The BFF does not enforce authentication on its REST controllers. Trust is established at the network layer (private VNet / API gateway).
- All calls must use **HTTPS**.

### What the BFF does on outgoing calls (informational)
- **MDP and the internal Notification API** require an Azure AD B2C OAuth2 **client-credentials** Bearer token. The BFF fetches it via `AzureB2CTokenGenerationService` and sets `Authorization: Bearer <token>`.
- **Knowlarity, Single Interface, LatLong, Daksha** use partner-issued static tokens passed in the partner's expected header (`Authorization`, `auth`, `token`) or query parameter (`access_token`). These never traverse the BFF's REST contract.

### Recommended hardening
- Application-level shared-secret auth on `POST /webhook/v1/...` per partner. *(Not implemented today.)*
- B2C token caching (currently every external call refetches a token).

## 4. Request payloads

### `POST /v1/mdp/dealer/basedOnFilters`
```json
{
  "type": "AMD",
  "sapStatus": "ACTIVE",
  "dmsStatus": "INACTIVE",
  "mdpStatus": null,
  "flags": ["SALES", "SERVICE", "THREE_WHEELER"],
  "search": {
    "searchTerm": "akb motors",
    "searchParams": ["dealerName"]
  }
}
```
All fields are optional individually, but **at least one** must be present.

- `type` — one of `AMD | APS | BRANCH | AD`
- `sapStatus`, `dmsStatus`, `mdpStatus` — free-form strings
- `flags` — non-empty list of non-blank strings
- `search.searchTerm` — ≥ 3 characters
- `search.searchParams` — non-empty list of non-blank strings

### `POST /webhook/v1/{mdpModule}/{externalClient}/{webHookEventType}`
- Path enums:
  - `mdpModule` — `DEALER`
  - `externalClient` — `KNOWLARITY | SINGLE_INTERFACE | LAT_LONG`
  - `webHookEventType` — `DEALER_UNPROCESSABLE | DEALER_PROCESSED_SUCCESSFULLY`
- Body — free-form JSON object (`Map<String, Object>` server-side). The BFF audit-logs the payload as-is.

## 5. Response payloads

All inbound endpoints return the same envelope:

```json
{
  "data": <object | array | string | null>,
  "errorMessage": "<string | null>"
}
```

- On success, `data` is populated and `errorMessage` is `null`.
- On error, `data` is `null` and `errorMessage` is a human-readable message.

For full schemas of `MdpDealerData` and the filter request, see [`openapi.yaml`](./openapi.yaml). Detailed examples are provided in §10.

## 6. Error responses

| HTTP | When |
|---|---|
| `400 Bad Request` | Application-level `ValidationException`, malformed JSON (`HttpMessageNotReadableException`), unknown enum value in path (`TypeMismatchException`), or upstream MDP returned 400 (relayed) |
| `401 Unauthorized` | Upstream MDP returned 401 (relayed only on the dealer-by-SAP-code endpoint) |
| `500 Internal Server Error` | Any other unexpected error, including `ExternalServiceException` raised after the upstream retry budget is exhausted |

The body is always a `GeneralResponse` with `errorMessage` set. Examples:

```json
// Empty / invalid input
{ "data": null, "errorMessage": "Validation error occurred : sapDealerCode (string) is EMPTY" }

// Filter request missing all attributes
{ "data": null, "errorMessage": "Validation error occurred : At least one of type, sapStatus, dmsStatus, mdpStatus or flags must be provided." }

// Search term too short
{ "data": null, "errorMessage": "Validation error occurred : request.search.searchTerm must be at least 3 characters long" }

// Malformed JSON
{ "data": null, "errorMessage": "Un-processable request received" }

// Upstream failure (after retries)
{ "data": null, "errorMessage": "Internal Error occurred : Unable to retrieve dealer data from the MDP service." }
```

The error-mapping is implemented in `RestExceptionHandler` (`@ControllerAdvice`).

## 7. Validation rules (summary)

Implemented in `GeneralUtils` and per-DTO `validate(...)` / `sanitizeIncomingData(...)` methods.

### Generic helpers
- `notNullAndNotEmptyOrElseThrow(s, name)` — null or blank-after-trim → `ValidationException("<name> is NULL"|"<name> (string) is EMPTY")`.
- `nullableButNotEmptyOrElseThrow(s, name)` — allows null; rejects non-null blank.
- `notNullNotEmptyAndAllElementsNotNullOrElseThrow(list, name)` — non-null + non-empty list with no null/blank items.
- `validateAndSanitize(s, name)` — combines null-and-blank checks; returns trimmed value.

### Per endpoint
| Endpoint | Rule |
|---|---|
| `GET /v1/mdp/dealer/{sapDealerCode}` | `sapDealerCode` non-blank (path-bound; trimmed). |
| `GET /v1/mdp/dealers` | `pincode` non-blank query param. |
| `POST /v1/mdp/dealer/basedOnFilters` | At least one filter present; nullable-but-not-blank for status strings; `flags` if present must be a non-empty list of non-blank strings; `search.searchTerm` ≥ 3 chars; `search.searchParams` non-empty list of non-blank strings. Sanitization trims all string inputs. |
| `POST /webhook/v1/...` | Path enums must bind successfully (Spring 400 on unknown). Body must be non-null. The `(mdpModule, externalClient)` combination must be `(DEALER, SINGLE_INTERFACE)`; everything else → `ValidationException`. |

## 8. Rate limits

- **No application-level rate limiting** is configured in the codebase.
- Throttling is expected at the API gateway / ingress layer in front of the service.
- The Outbound BFF *self-throttles* through:
  - Service Bus `maxConcurrentSessions = 10`,
  - `AsyncJobService` fixed thread pool of size 20,
  - Spring `@Retryable` (5 attempts, 1s → 10s exponential, multiplier 2.0) on each external call.
- The Notification API caller uses `@Retryable(maxAttempts = 3)` to limit alert-email amplification.
- `FailureEventTypeInfoService` enforces a per-`FailureEventType` email cooldown (`nextEmailBackoffTimeInHrs = 1` for all known types) to suppress alert storms.

## 9. External API dependencies

### 9.1 HTTP dependencies (consumed by the BFF)

| System | Endpoint | Method | Auth | Used by |
|---|---|---|---|---|
| MDP — read | `${MDP_BASE_URL}/mdp/v1/dealer/{code}` | GET | Azure B2C Bearer | Inbound `getDealerBySapCode` |
| MDP — read | `${MDP_BASE_URL}/mdp/v1/dealers/basedOnFilters` | POST | Azure B2C Bearer | Inbound `getDealersByFilters` |
| MDP — read | `${MDP_BASE_URL}/mdp/v1/dealers?pincode=...` | GET | Azure B2C Bearer | Inbound `getDealersByPincode` |
| MDP — write | `${MDP_BASE_URL}/mdp/v1/dealer/mapDealerWithKNumber` | POST | Azure B2C Bearer | Outbound (Knowlarity assign flow) |
| MDP — write | `${MDP_BASE_URL}/mdp/v1/dealer/{code}/unassignKNumber` | POST | Azure B2C Bearer | Outbound (Knowlarity un-assign flow) |
| Azure AD B2C | `${AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL}` | POST (form-urlencoded) | client-credentials | Both services |
| Knowlarity | `${KNOWLARITY_K_NUMBER_API_URL}` (`?query_type=fetch|update|delete`) | GET | Static `Authorization` header | Outbound |
| Single Interface | `${SI_OUTLET_API_BASE_URL}/v1/Outlets/Add`, `/v1/Outlets/Close` | POST JSON | Static `auth` header | Outbound |
| LatLong | `${LATLONG_DEALER_DATA_API_URL}` | POST JSON + `?access_token=...` | Token | Outbound |
| Daksha | `${DAKSHA_DEALER_UPDATE_API_URL}?r=client_api/dealerCreationAPI/JxGetDealerCreationData` | POST JSON | `token` header | Outbound |
| Internal Notification | `${NOTIFICATION_BASE_URL}/api/v1/notification/email` | POST JSON | Azure B2C Bearer | Outbound (failure alerts) |

All outbound HTTP uses OkHttp 4.12 via `OkHttpService`. Every call is wrapped in `@Retryable` (5 attempts, exponential backoff; Notification uses 3) and audit-logged with timing.

### 9.2 Message-driven dependency (Outbound BFF)

The Outbound BFF consumes events from an Azure Service Bus topic.

- **Broker**: Azure Service Bus
- **Topic**: `${MDP_DEALER_DATA_TOPIC_NAME}` (env-specific, e.g., `dev.mdp.dealer_data`)
- **Subscription**: `mdp_bff` (must exist in the topic before deploying)
- **Receive mode**: `PEEK_LOCK`
- **Auto-complete**: disabled — `context.complete()` called only after successful processing
- **Concurrency**: `maxConcurrentSessions = 10` per pod (session-aware processor)
- **Auth**: Service Bus connection string (`${MDP_DEALER_DATA_TOPIC_CONNECTION_STRING}`)
- **Application property**: `event` (string) is read from `ApplicationProperties` and logged

#### Message body schema (informal)
```jsonc
{
  "dealer": {
    "sapDealerCode": "string",
    "dmsStatus": "PRE_ACTIVE | ACTIVE | INACTIVE",
    "sapStatus": "string",
    "sapRawStatus": "integer | null",
    "mdpStatus": "PRE_ACTIVE | ACTIVE | INACTIVE",
    "type": "AMD | APS | BRANCH | AD",
    "oldSapDealerCode": "string | null",
    "parentAmdSapDealerCode": "string | null",
    "parentApsSapDealerCode": "string | null"
  },
  "dealerDetails": { "name": "...", "tempDmsBranchSequence": 0,
                     "knowlarityVirtualNumber": "...", "knowlarityRoutingCli": "...",
                     "knowlarityFallbackNumber": "...", "...": "..." },
  "locations": [ { "type": "MAIN", "addressLine1": "...", "pincode": "...",
                   "city": "...", "latitude": "...", "longitude": "...", "...": "..." } ],
  "contacts":  [ { "type": "MAIN", "primaryPhoneNumber": "...", "emailAddress": "...", "...": "..." } ],
  "flags":     [ { "name": "K_NUMBER_NEEDED", "isEnabled": 1 } ],
  "employees": [ { "fullName": "...", "type": "SHOWROOM_MANAGER",
                   "phoneNumber": "...", "emailAddress": "...",
                   "isActive": "0|1", "isDeleted": "0|1" } ]
}
```
Modeled by `MdpServiceBusIncomingMessagePayloadBody`. Unknown JSON fields are tolerated.

## 10. Sample requests/responses

> Hostnames are illustrative. Replace with the gateway URL for the target environment.

### 10.1 Get dealer by SAP code

**Request**
```bash
curl --location 'https://mdp-bff.example.tvsmotor.com/mdp-bff/v1/mdp/dealer/14988'
```

**Response — 200 OK** (truncated for readability; full sample in [`openapi.yaml`](./openapi.yaml))
```json
{
  "data": {
    "dealer": {
      "sapDealerCode": "14988",
      "dmsStatus": "PRE_ACTIVE",
      "sapStatus": "ACTIVE",
      "mdpStatus": "PRE_ACTIVE",
      "type": "AMD"
    },
    "dealerDetails": {
      "name": "ARC AUTOMOTIVE LLP",
      "gstNumber": "27ABUFA3325P1ZT"
    },
    "locations": [
      {
        "type": "MAIN",
        "addressLine1": "UNIT 3,4,SURVEY NO.265",
        "city": "VASAI",
        "state": "MAH",
        "country": "IN",
        "stateName": "MAHARASHTRA"
      }
    ],
    "contacts": [
      { "type": "MAIN", "primaryPhoneNumber": "9819956566" }
    ],
    "flags": [
      { "name": "SALES",   "isEnabled": 1 },
      { "name": "SERVICE", "isEnabled": 1 }
    ],
    "employees": [
      {
        "fullName": "AUTOMATICALLY_CREATED",
        "type": "SHOWROOM_MANAGER",
        "isActive": "0",
        "isDeleted": "0"
      }
    ]
  },
  "errorMessage": null
}
```

**Response — 400 Bad Request** (input validation)
```json
{ "data": null, "errorMessage": "Validation error occurred : sapDealerCode (string) is EMPTY" }
```

### 10.2 Get dealers by pincode

**Request**
```bash
curl --location 'https://mdp-bff.example.tvsmotor.com/mdp-bff/v1/mdp/dealers?pincode=673005'
```

**Response — 200 OK** (truncated)
```json
{
  "data": [
    {
      "dealer": {
        "sapDealerCode": "NX_SAP_11464_6",
        "type": "BRANCH",
        "mdpStatus": "INACTIVE",
        "parentAmdSapDealerCode": "11464"
      },
      "dealerDetails": { "name": "A K B MOTORS WESTHILL", "tempDmsBranchSequence": 6 },
      "locations": [{ "type": "MAIN", "pincode": "673005", "city": "CALICUT" }]
    },
    {
      "dealer": {
        "sapDealerCode": "NX_SAP_14858_6",
        "type": "BRANCH",
        "mdpStatus": "ACTIVE",
        "parentAmdSapDealerCode": "14858"
      },
      "dealerDetails": { "name": "AKB MOTORS LLP - WESTHILL", "tempDmsBranchSequence": 6 },
      "locations": [{ "type": "MAIN", "pincode": "673005", "city": "CALICUT" }]
    }
  ],
  "errorMessage": null
}
```

### 10.3 Get dealers by filter

**Request**
```bash
curl --location 'https://mdp-bff.example.tvsmotor.com/mdp-bff/v1/mdp/dealer/basedOnFilters' \
  --header 'Content-Type: application/json' \
  --data '{
    "type": "AMD",
    "sapStatus": "ACTIVE",
    "dmsStatus": "INACTIVE",
    "flags": ["SALES", "SERVICE", "THREE_WHEELER"]
  }'
```

**Response — 200 OK** (shape only; same as §10.2)
```json
{ "data": [ /* MdpDealerData[] */ ], "errorMessage": null }
```

**Response — 400 Bad Request** (no filter present)
```json
{
  "data": null,
  "errorMessage": "Validation error occurred : At least one of type, sapStatus, dmsStatus, mdpStatus or flags must be provided."
}
```

### 10.4 Webhook intake

**Request**
```bash
curl --location 'https://mdp-bff.example.tvsmotor.com/mdp-bff/webhook/v1/DEALER/SINGLE_INTERFACE/DEALER_UNPROCESSABLE' \
  --header 'Content-Type: application/json' \
  --data '{
    "sapDealerCode": "10023",
    "reason": "missing main location",
    "attemptId": "attempt-12345"
  }'
```

**Response — 200 OK**
```json
{ "data": "Webhook data received successfully", "errorMessage": null }
```

**Response — 400 Bad Request** (unsupported client)
```json
{ "data": null, "errorMessage": "Validation error occurred : Invalid External Client = KNOWLARITY" }
```

---

## Appendix A — `GeneralResponse` envelope

```json
{ "data": <payload>, "errorMessage": "<string|null>" }
```

Java type: `com.tvsmotor.bff.model.response.GeneralResponse` (Lombok `@Data @Builder`).

## Appendix B — `MdpGeneralResponse` (upstream)

The upstream MDP service returns its own envelope:

```json
{
  "data": "...",
  "errorMessage": "...",
  "time": "...",
  "uuid": "...",
  "timeTakenInMs": 0,
  "serverId": "..."
}
```

The BFF only ever exposes `data` and `errorMessage` to callers; the rest is consumed internally for logging/audit.

## Appendix C — Idempotency notes

- **Read endpoints** (`GET /v1/mdp/...`, `POST /v1/mdp/dealer/basedOnFilters`) are naturally idempotent.
- **Webhook intake** is best-effort idempotent; partners are expected to retry safely. The BFF does not deduplicate by event id today (no event-id field is enforced in the contract).
- **Outbound message processing** is designed to be idempotent end-to-end: Knowlarity uses assign-or-update, Single Interface uses create-or-close, LatLong/Daksha forwards are full-document overwrites driven off `sapDealerCode`.

## Appendix D — Configuration env-vars referenced (names only, no values)

`ACTIVE_ENVIRONMENT`, `MDP_BASE_URL`, `AZURE_B2C_GENERATE_AUTH_TOKEN_API_URL`, `AZURE_B2C_CLIENT_ID`, `AZURE_B2C_CLIENT_SECRET`, `AZURE_B2C_SCOPE`, `MDP_BFF_EXTERNAL_CLIENTS`, `MDP_DEALER_DATA_TOPIC_NAME`, `MDP_DEALER_DATA_TOPIC_CONNECTION_STRING`, `KNOWLARITY_K_NUMBER_API_URL`, `KNOWLARITY_K_NUMBER_API_TOKEN`, `KNOWLARITY_K_NUM_ASSIGNMENT_ENABLED_DEALER_TYPES`, `SI_OUTLET_API_BASE_URL`, `SI_OUTLET_API_TOKEN`, `SI_ENABLED_DEALER_TYPES`, `LATLONG_DEALER_DATA_API_URL`, `LATLONG_DEALER_DATA_API_TOKEN`, `DAKSHA_DEALER_UPDATE_API_URL`, `DAKSHA_DEALER_UPDATE_API_TOKEN`, `NOTIFICATION_BASE_URL`, `NOTIFICATION_FAILURE_EMAIL_TEMPLATE_ID`, `NOTIFICATION_EMAIL_FAILURE_PRIORITY`, `EXTERNAL_CLIENTS_FAILURE_EMAIL_ALERT_RECIPIENTS`, `DATABASE_HOST_URL`, `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`.
