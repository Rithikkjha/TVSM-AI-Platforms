# MDP — API Specification (SmartBrain AI Format)

> **Service:** Master Data Platform (MDP)
> **Version:** 2.0
> **Last Updated:** July 2026
> **Source of truth:** Code in `src/main/java/com/tvsmotor/mdp/`

---

## Service Identity

| Field | Value |
|-------|-------|
| Service Name | master-data-platform (MDP) |
| Repo | github.com/tvsmotorcompany/master-data-platform |
| Team | D&AI Engineering |
| Tech Lead | _TBD_ |
| Deployment | AKS (Azure Kubernetes Service) |
| Base URL (prod) | `https://<prod-apim-host>/mdp/v1/...` |
| Context Path | `/mdp` (port `8080`) |
| Swagger Hub | [https://tvsswgrhub.tvsmotor.com/apis/tvsmotorcompany/mdp/1.0.6](https://tvsswgrhub.tvsmotor.com/apis/tvsmotorcompany/mdp/1.0.6) |
| Framework | Spring Boot 3.5.16 / Java 17 |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Product Owner | _TBD_ | _TBD_ |
| Tech Lead | _TBD_ | _TBD_ |
| Dev Team | D&AI Backend | Teams: _TBD_ |
| On-call | Rotational | _TBD_ |
| Platform / DevOps | Platform Team | _TBD_ |
| Identity (B2C) | Identity Team | _TBD_ |
| Data Engineering (ADF) | DE Team | _TBD_ |

---

## My API Endpoints (Inbound)

### Dealer Read APIs (`DealerController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/dealer/{sapDealerCode}?skipCache=false` | Bearer JWT | Get full dealer composite record (cached) | D2C Web, Mobile BFF, Admin Portal, Partner Channels |
| GET | `/v1/dealer/{sapDealerCode}/branches?skipUnofficialBranches=true` | Bearer JWT | List branches for an AMD/SPD dealer | D2C Web, Mobile BFF |
| GET | `/v1/dealers?pincode={pincode}` | Bearer JWT | Dealers by pincode | D2C Web, Mobile BFF |
| POST | `/v1/dealers/basedOnFilters` | Bearer JWT | Filter dealers by type/status/flags/location/search | D2C Web, Mobile BFF, Admin Portal |
| POST | `/v1/dealers/listOfSapDealerCode/basedOnFilters` | Bearer JWT | Filter dealers — SAP codes only | D2C Web, Mobile BFF |
| POST | `/v1/dealers/data?fetchMdpActiveDealersOnly=false` | Bearer JWT | Bulk fetch dealers by SAP codes (Set) | D2C Web, Mobile BFF, Reporting |
| GET | `/v1/dealers/active-counts` | Bearer JWT | Aggregate dealer counts by status | Admin Portal, Reporting |
| POST | `/v1/dealers/listOfDealerDetails/basedOnProximity` | Bearer JWT | Geo-proximity dealer search | D2C Web, Mobile BFF |

### Dealer Flag Operations (`DealerFlagsNewController`, `DealerFlagsTypeNewController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/dealer/{sapDealerCode}/flag/list` | Bearer JWT (SYSTEM) | List all flags for a dealer | Admin Portal, Internal Tools |
| PUT | `/v1/dealer/{sapDealerCode}/flag/{flagId}?newFlagValue=0\|1` | Bearer JWT (SYSTEM) | Update a single dealer flag value | Admin Portal, Internal Tools |
| GET | `/v1/dealer/flag-type/list` | Bearer JWT (SYSTEM) | List all flag type definitions | Admin Portal |
| POST | `/v1/dealer/flag-type` | Bearer JWT (SYSTEM) | Create new flag type (async flag creation) | Admin Portal |
| POST | `/v1/dealer/flag-type/delete-flag/{dealerFlagTypeId}?reasonForDeletion=` | Bearer JWT (SYSTEM) | Soft-delete a flag type | Admin Portal |

### Dealer Knowlarity / K-Number (`DealerKnowlarityDataController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | `/v1/dealer/mapDealerWithKNumber` | Bearer JWT (MDP_BFF) | Map Knowlarity virtual number to dealer | MDP-BFF |
| POST | `/v1/dealer/{sapDealerCode}/unassignKNumber` | Bearer JWT (MDP_BFF) | Unassign K-number from dealer | MDP-BFF |

### Dealer LatLong (`LatLongDetailsController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/dealer/latLong/sync` | Bearer JWT (SYSTEM) | Trigger async lat/long refresh for all dealers | Admin Portal, SYSTEM |

### Product Vehicle (`ProductVehicleController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/product/vehicle/{sapModelId}?partsData=false` | Bearer JWT | Vehicle product by model ID (optional parts) | D2C Web, Mobile BFF, Partner Channels |
| GET | `/v1/product/vehicle/part/{sapPartId}` | Bearer JWT | Vehicle by part ID | D2C Web, Partner Channels |
| GET | `/v1/product/vehicle/sap-model-ids` | Bearer JWT | List distinct SAP model IDs | Reporting, Internal Tools |

### Product MnA (`ProductMnaController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/product/mna/{sapSkuId}` | Bearer JWT | Legacy MnA lookup by SKU ID | D2C Web |
| GET | `/v1/product/mna/v2/{sapPartNo}` | Bearer JWT | New MnA lookup by part number | D2C Web, Mobile BFF |

### Vehicle Price (`PriceVehicleController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/price/vehicle/{productId}?state=&country=` | Bearer JWT | Vehicle price by SAP model ID + state + country | D2C Web, Mobile BFF, Partner Channels |
| GET | `/v1/price/vehicle/sapModelIds` | Bearer JWT | Distinct SAP model IDs for pricing | Reporting |

### Parts Master (`PartController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/part/{sapPartId}` | Bearer JWT | Part master record | D2C Web, Partner Channels |

### Part Price (`PartPriceController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/part_price/{sapPartId}?country=IN` | Bearer JWT | Part price (currently only country=IN) | D2C Web, Partner Channels |

### Data Engineering Pipeline (`DE_PipelineController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/de-pipeline/trigger/{batchProcessingType}` | Bearer JWT (ADF) | Trigger batch processing pipeline | Azure Data Factory |

**Valid `batchProcessingType` values:** `SAP_DATA`, `SHAREPOINT_DATA`, `DEALER_SAP_SERVICE_CENTER_ADDRESS_DATA`, `PRODUCT_VEHICLE_SAP_DATA`, `PRICE_VEHICLE_SAP_DATA`, `PRODUCT_MNA_SAP_DATA`, `PRODUCT_MNA_NEW_SAP_DATA`, `PART_SAP_DATA`, `PART_PRICE_SAP_DATA`

### DMS Migration (`DMSMigrationController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/dms-import/trigger` | Bearer JWT (SYSTEM) | Trigger async DMS migration (reads from MSSQL) | SYSTEM, Scheduled |
| POST | `/v1/dms-import/dealer` | Bearer JWT (SYSTEM), @DisableOnProd | Import DMS dealer batch | Internal Migration |
| POST | `/v1/dms-import/branch/{parentSapDealerCode}` | Bearer JWT (SYSTEM), @DisableOnProd | Import DMS branch data | Internal Migration |
| POST | `/v1/dms-import/employee/{sapDealerCode}` | Bearer JWT (SYSTEM), @DisableOnProd | Import DMS employee data | Internal Migration |
| POST | `/v1/dms-import/ingestDmsInternalBranchId` | Bearer JWT (SYSTEM), @DisableOnProd | Ingest DMS internal branch ID | Internal Migration |
| POST | `/v1/dms-import/ingestDmsDealerData` | Bearer JWT (SYSTEM), @Deprecated | Ingest DMS dealer data (use /trigger instead) | Legacy |
| POST | `/v1/dms-import/ingestDmsBranchData` | Bearer JWT (SYSTEM), @Deprecated | Ingest DMS branch data (use /trigger instead) | Legacy |

### Dealer Migration (`DealerMigrationController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| PUT | `/v1/migration/dealer/2WAnd3WFlagMigration` | Bearer JWT (SYSTEM) | Sync 2W/3W flags between AMD and branches (async) | Internal Migration |
| POST | `/v1/migration/dealer/addNewFlags` | Bearer JWT (SYSTEM) | Add new flags to all dealers | Internal Migration |
| GET | `/v1/migration/dealer/updateSapStatus` | Bearer JWT (SYSTEM) | Migrate SAP status | Internal Migration |
| GET | `/v1/migration/dealer/updateMdpDealerStatus` | Bearer JWT (SYSTEM) | Migrate MDP dealer status | Internal Migration |
| GET | `/v1/migration/dealer/updateUnofficialBranches` | Bearer JWT (SYSTEM) | Sync unofficial branches to NOT_PRESENT_IN_SAP | Internal Migration |
| GET | `/v1/migration/dealer/sanitizePhoneNumbers` | Bearer JWT (SYSTEM) | Sanitize phone numbers for all dealers | Internal Migration |

### Product Migration (`ProductMigrationController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/migration/product/vehicle/engine_type` | Bearer JWT (SYSTEM) | Migrate vehicle engine type data | Internal Migration |

### Test / Service Bus Control (`TestServiceBusController`)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | `/v1/test/service-bus/stop-receiver` | Bearer JWT (SYSTEM) | Stop SB processor clients | Internal Ops |
| GET | `/v1/test/service-bus/start-receiver` | Bearer JWT (SYSTEM) | Start SB processor clients | Internal Ops |
| GET | `/v1/test/service-bus/push-dealer-data/{sapDealerCode}?eventType=` | Bearer JWT (SYSTEM) | Push single dealer to SB | Internal Testing |
| POST | `/v1/test/service-bus/push-dealers-data?eventType=` | Bearer JWT (SYSTEM) | Push multiple dealers to SB | Internal Testing |
| GET | `/v1/test/service-bus/consume-dealer-data/{sapDealerCode}` | Bearer JWT (SYSTEM), @DisableOnProd | Consume dealer from SB | Internal Testing |
| POST | `/v1/test/service-bus/pushDmsDealerData` | Bearer JWT (SYSTEM) | Push DMS dealer data to SB | Internal Testing |
| POST | `/v1/test/service-bus/pushDmsBranchData` | Bearer JWT (SYSTEM) | Push DMS branch data to SB | Internal Testing |

---

## Outbound (Who I Call)

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| Azure AD B2C | POST | `/oauth2/v2.0/token` | Acquire app-to-app Bearer tokens (client_credentials flow) |
| Notification Service | POST | `{NOTIFICATION_BASE_URL}/...` | Send transactional emails (dealer onboarding, failure alerts) |
| Lat/Long Service | GET/POST | Brand-keyed endpoints (8 brand credentials configured) | Resolve geo-coordinates for dealer locations |
| APIM (downstream) | various | `{APIM_BASE_URL}/...` | Proxied downstream service calls |
| Azure Service Bus | PUBLISH | 7 topics (see Events section) | Emit domain change events to downstream consumers |
| DMS (MSSQL) | SQL (read-only) | `applicationIntent=ReadOnly`, port 1433, database `OnlineDMS` | Migration source — dealer operational data |

---

## Events & Messaging

### Topics This Service Publishes To

| Topic (config key) | Events Published | Format | Triggered By |
|--------------------|-----------------|--------|--------------|
| `dealerData` | DEALER_CREATED, DEALER_UPDATED, ONE_TIME_MIGRATION | JSON (session-based FIFO, sessionId=`DEALER_{sapDealerCode}`) | Dealer mutations, batch ingestion, migration |
| `dmsDealerData` | DMS_DEALER_SYNC (temporary push for testing) | JSON | DMS data push (test) |
| `productVehicleData` | PRODUCT_VEHICLE_CREATED, PRODUCT_VEHICLE_UPDATED | JSON | ADF batch ingestion (PRODUCT_VEHICLE_SAP_DATA) |
| `priceVehicleData` | PRICE_VEHICLE_CREATED, PRICE_VEHICLE_UPDATED | JSON | ADF batch ingestion (PRICE_VEHICLE_SAP_DATA) |
| `productMnaData` | PRODUCT_MNA_CREATED, PRODUCT_MNA_UPDATED | JSON | ADF batch ingestion (PRODUCT_MNA_SAP_DATA, PRODUCT_MNA_NEW_SAP_DATA) |
| `partData` | PART_CREATED, PART_UPDATED | JSON | ADF batch ingestion (PART_SAP_DATA) |
| `partPriceData` | PART_PRICE_CREATED, PART_PRICE_UPDATED | JSON | ADF batch ingestion (PART_PRICE_SAP_DATA) |

### Topics This Service Subscribes To

| Topic (config key) | Subscription | Concurrency | Events Consumed | Action |
|--------------------|-------------|-------------|-----------------|--------|
| `dealerData` | `mdp` | maxConcurrentSessions=1 | DEALER_CREATED, DEALER_UPDATED | Upsert dealer into MySQL, invalidate/repopulate cache (`DealerDataConsumerService`) |
| `dmsDealerData` | `mdp` | maxConcurrentSessions=250 | DmsDealerData, DmsBranchData | Consume DMS dealer/branch updates, sync status/details (`DmsDataConsumerService`) |

> **Note:** Product/Price/Part/MnA topics are sender-only from MDP. Consumers do NOT re-publish on the same topic — avoids event loops.

### Service Bus Message Properties

All outbound messages include these application properties:
- `event` — `ServiceBusEventType` value (DEALER_CREATED, DEALER_UPDATED, ONE_TIME_MIGRATION)
- `createdAt` — timestamp string
- `eventSource` — `"MDP"`

### Service Bus Event Types (enum `ServiceBusEventType`)

```
DEALER_CREATED     — New dealer created at SAP (dealer and branch)
DEALER_UPDATED     — Dealer data modified
ONE_TIME_MIGRATION — Used for one-time migration pushes
```

---

## External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| Azure AD B2C | Identity Provider | OAuth2 token issuance (inbound JWT validation + outbound token acquisition) | Client credentials (client_id + client_secret + scope) |
| Azure API Management (APIM) | API Gateway | TLS termination, rate limiting (1000 req/min/appid), JWT signature enforcement | Managed by Platform Team |
| Azure Data Factory (ADF) | ETL Orchestrator | Batch ingestion from SAP/SharePoint → Data Lake → MDP trigger | Bearer JWT (ADF client role) |
| Azure Data Lake Storage | File Storage | Staging zone for ingested batch files | Managed identity |
| SAP (ECC / S/4 HANA) | ERP System | Authoritative source for dealer, vehicle, pricing master data | Via ADF pipeline |
| DMS (MSSQL — OnlineDMS) | Dealer Management System | Operational dealer data (read-only migration source) | DB credentials (applicationIntent=ReadOnly) |
| SharePoint | Operations Sheets | Operational dealer attributes ingested via ADF | Via ADF pipeline |
| Notification Service | Internal Platform Service | Templated transactional email (onboarding, failure alerts) | Bearer JWT (B2C-issued) |
| Lat/Long Service | Internal Service | Geo-coordinate resolution for dealer locations | Brand-keyed API credentials (8 brands configured) |

---

## Data Storage

| Store | Type | Purpose |
|-------|------|---------|
| Azure Database for MySQL 8 | Primary RDBMS | Canonical master data store (dealers, products, prices, parts, audit). HikariCP pool: min 20, max 50. |
| Azure Cache for Redis | Cache (Jedis 5.2.0) | Composite payload cache for read-heavy APIs. 10 cache regions. Event-driven invalidation. |
| DMS / MSSQL (OnlineDMS) | Read-only DB | Migration source for dealer operational data. applicationIntent=ReadOnly. |
| Azure Data Lake Storage | File Storage | Landing zone for ADF batch files |

### Cache Regions (`CacheName` enum)

| Region | Key | Purpose |
|--------|-----|---------|
| `DEALER_DATA` | sapDealerCode | Composite dealer payload |
| `DEALER_EMPLOYEE_DATA` | sapDealerCode | Employee data |
| `AUTH_DATA` | clientId | AuthClientUser mapping |
| `VEHICLE_DATA_SAP_MODELID` | sapModelId | Vehicle model data |
| `VEHICLE_DATA_SAP_PARTID` | sapPartId | Vehicle part data |
| `PRICE_VEHICLE_DATA` | composite key | Vehicle price data |
| `PRODUCT_MNA_DATA` | sapSkuId | MnA legacy data |
| `PRODUCT_MNA_NEW_DATA` | sapPartNo | MnA new data |
| `PART_DATA` | sapPartId | Part master data |
| `PART_PRICE_DATA` | sapPartId | Part price data |

---

## Authentication & Authorization Summary

| Mechanism | Details |
|-----------|---------|
| Protocol | OAuth2 Bearer JWT (Azure AD B2C, client_credentials flow) |
| Token validity | 1 hour (3599 seconds) |
| Required claims | `appid` (maps to internal client), `exp` (not expired), `roles` contains `mdp.api` |
| Rate limit | 1000 requests/min/appid (APIM-enforced) |
| Client types (`MdpClient` enum) | `SYSTEM` (full access bypass), `ADF` (batch trigger only), `MDP_BFF` (reads + K-number ops) |
| Method-level auth | `@Authorization(allowedUsers = {...})` annotation on controllers |
| Prod guard | `@DisableOnProd` blocks diagnostic/migration endpoints in prod profile |

---

## Downstream Consumers (Who Calls Me — Blast Radius)

| Consumer | What They Use | Impact If MDP Is Down |
|----------|---------------|----------------------|
| D2C Web (TVS Connect Web) | Dealer search, product/price lookups, proximity search | Dealer locator breaks, pricing unavailable |
| Mobile BFF (TVS Connect App) | Same as D2C Web + K-number operations | Mobile dealer & product experience breaks |
| Admin Portal | Dealer flag management, bulk operations, counts | Admin operations blocked |
| Reporting / Analytics | Bulk dealer data, active counts, SB events | Reports stale, dashboards lag |
| Partner Channels (BikeWale, BikeDekho, 91Wheels) | Dealer data, product/price APIs | Partner listings stale/unavailable |
| Azure Data Factory | Pipeline trigger endpoints | Batch ingestion fails, data goes stale |

---

## API Response Envelope (`GeneralResponse`)

```json
{
  "data":          "<object | array | scalar | null>",
  "errorMessage":  "string or null",
  "time":          "Thu May 28 11:00:00 IST 2026",
  "uuid":          "<transactionId — quote this when filing tickets>",
  "timeTakenInMs": 142,
  "serverId":      "<k8s pod hostname from HOSTNAME env var>"
}
```

---

## Error Codes

| HTTP | Trigger |
|------|---------|
| 400 | `ValidationException`, `NoSuchElementException`, malformed JSON, missing params, type mismatch |
| 401 | `AccessDeniedException` — token missing/invalid/expired/role missing |
| 403 | Authenticated but client type not in endpoint's `allowedUsers` |
| 405 | HTTP method not supported on path |
| 500 | Unhandled exception. Detail visible only when `SHOW_HTTP_500_DETAILS=true` (never in prod). |

---

## Dealer Domain Enums (from code)

### DealerType
`AMD`, `SPD`, `APS`, `BRANCH`, `AD`

### DealerFlagType (45 flags)
`SALES`, `SERVICE`, `DIGITAL_LEADS`, `EMS`, `TWO_WHEELER`, `THREE_WHEELER`, `IQUBE`, `RONIN`, `RR310`, `U400`, `RTR310`, `RTR200`, `TVSX`, `DIGITAL_LEADS_EV`, `DIGITAL_LEADS_3W`, `U546`, `RTX`, `THREE_WHEELER_ICE_PASSENGER`, `THREE_WHEELER_EV_PASSENGER`, `THREE_WHEELER_ICE_CARGO`, `THREE_WHEELER_EV_CARGO`, `DEFAULT_DTR_PROVIDED`, `IQUBE_DTR_PROVIDED`, `TVSX_DTR_PROVIDED`, `U546_DTR_PROVIDED`, `DEFAULT_HTR_PROVIDED`, `IQUBE_HTR_PROVIDED`, `TVSX_HTR_PROVIDED`, `U546_HTR_PROVIDED`, `IQUBE_OFFLINE_BOOKING_ENABLED`, `TVSX_OFFLINE_BOOKING_ENABLED`, `U546_OFFLINE_BOOKING_ENABLED`, `K_NUMBER_NEEDED`, `BIKE_DEKHO`, `BIKE_WALE`, `NINETY_ONE_WHEELS`, `ASSP`, `MKTPLACE_FLIPKART_ENABLED`, `MKTPLACE_AMAZON_ENABLED`, `RVSF`

### SapStatus
`PRE_ACTIVE`, `ACTIVE`, `PERMANENTLY_BLOCKED`, `NOT_PRESENT_IN_SAP`, `TEMPORARILY_BLOCKED`

### DmsStatus
`PRE_ACTIVE`, `ACTIVE`, `INACTIVE`

### MdpDealerStatus
`PRE_ACTIVE`, `ACTIVE`, `INACTIVE`

### DealerLocationType
`MAIN`, `SALES`, `SERVICE`

### DealerContactType
`MAIN`, `SHOWROOM_ICE`, `SHOWROOM_EV`

### DealerEmployeeType
`MANAGER`, `DSE`, `SHOWROOM_MANAGER`, `OTHER`

---

*For detailed request/response samples and validation rules, see `API_SPECIFICATION.md`. For architecture, see `HLD.md`.*
