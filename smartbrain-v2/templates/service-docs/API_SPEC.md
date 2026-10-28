---
service_id: <service-id>
doc_type: api_spec
last_reviewed: YYYY-MM-DD
openapi: null   # path/URL to OpenAPI/Swagger file if one exists
---

# <Service Name> — API Specification

## Authentication
How callers authenticate to <service-id> (JWT issuer, API key, mTLS).

## Endpoint Index
| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| | | | | |

## Endpoints
Repeat this block per endpoint. Heading format is fixed: `### METHOD /path`.

### POST /api/bookings
Purpose: …
Callers: `tvs-connect-android-app`, `dealer-portal`

Parameters:
| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| | path/query/header | | | |

Request body: `CreateBookingRequest` (defined in `path/to/File:line`)
| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| | | | |

Example request:
```json
{ }
```

Response `201`: `BookingResponse`
| Field | Type | Required | Notes |
|---|---|---|---|
| | | | |

Example response:
```json
{ }
```

Errors:
| Status | Code | When |
|---|---|---|
| | | |

Side effects: writes `booking-db.Booking`, calls `payment-service`, publishes `BOOKING_CREATED`.

## Outbound Calls
| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| | | | | | | |

## Schemas
Every DTO / payload referenced in this file. Heading format is fixed: `### <SchemaName>`.

### CreateBookingRequest
Defined in: `path/to/File:line`
| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| | | | |

## Events Published
| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| | topic/queue | | | | | |

## Events Consumed
| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

## External Integrations
| System | Purpose | Auth |
|---|---|---|
| | | |

## Rate Limits and SLAs
