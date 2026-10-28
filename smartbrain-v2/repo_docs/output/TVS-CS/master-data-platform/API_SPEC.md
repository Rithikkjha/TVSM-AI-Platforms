---
service_id: master-data-platform
doc_type: api_spec
last_reviewed: 2026-10-11
openapi: null
---

# master-data-platform — API Specification

## Authentication
master-data-platform: `MdpOncePerRequestFilter` reads the `Authorization` header; if present, the Azure B2C JWT is validated (`JWTUtil.validateAndReturnTokenPayloadIfValid`) and the `appid` client is looked up in `AuthClientUser` to get a user type (`src/main/java/com/tvsmotor/mdp/config/MdpOncePerRequestFilter.java:79-92`). Requests without the header pass through with no client context; per-endpoint authorization rules are Unknown (`AccessDeniedException` → 401 in `common/exceptions/handlers/RestExceptionHandler.java:95`).

## Endpoint Index
master-data-platform exposes 68 HTTP endpoints; generated OpenAPI at `/v3/api-docs` (springdoc).

| Method | Path | Auth | Description | Callers (service_id) |
|---|---|---|---|---|
| GET | `/mdp/v1/de-pipeline/trigger/{batchProcessingType}` | Unknown | `DE_PipelineController.startProcessing` (src/main/java/com/tvsmotor/mdp/controller/DE_PipelineController.java:20) | none recorded |
| GET | `/mdp/v1/dealer/flag-type/list` | Unknown | `DealerFlagsTypeNewController.getAllFlagTypes` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsTypeNewController.java:17) | none recorded |
| GET | `/mdp/v1/dealer/latLong/sync` | Unknown | `LatLongDetailsController.importLatLongDetails` (src/main/java/com/tvsmotor/mdp/controller/LatLongDetailsController.java:17) | none recorded |
| GET | `/mdp/v1/dealer/{sapDealerCode}` | Unknown | `DealerController.getDealerData` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20) | `tvsm-auth`, `tvsm-marketplace-service`, `tvsmbe-location` |
| GET | `/mdp/v1/dealer/{sapDealerCode}/branches` | Unknown | `DealerController.getBranchesByParentDealerId` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20) | `tvsm-auth`, `tvsmbe-location` |
| GET | `/mdp/v1/dealer/{sapDealerCode}/flag/list` | Unknown | `DealerFlagsNewController.getAllDealerFlags` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsNewController.java:15) | none recorded |
| GET | `/mdp/v1/dealers` | Unknown | `DealerController.getDealersBasedOnPincode` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20) | none recorded |
| GET | `/mdp/v1/dealers/active-counts` | Unknown | `DealerController.getActiveCounts` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20) | none recorded |
| GET | `/mdp/v1/dms-import/trigger` | Unknown | `DMSMigrationController.startDmsMigration` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33) | none recorded |
| GET | `/mdp/v1/migration/dealer/sanitizeAddressLines` | Unknown | `DealerLocationMigrationController.sanitizeAddressLinesForAllDealerLocations` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerLocationMigrationController.java:22) | none recorded |
| GET | `/mdp/v1/migration/dealer/sanitizePhoneNumbers` | Unknown | `DealerMigrationController.sanitizePhoneNumbers` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20) | none recorded |
| GET | `/mdp/v1/migration/dealer/updateMdpDealerStatus` | Unknown | `DealerMigrationController.updateMdpDealerStatus` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20) | none recorded |
| GET | `/mdp/v1/migration/dealer/updateSapStatus` | Unknown | `DealerMigrationController.updateSapStatus` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20) | none recorded |
| GET | `/mdp/v1/migration/dealer/updateUnofficialBranches` | Unknown | `DealerMigrationController.updateUnofficialBranches` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20) | none recorded |
| GET | `/mdp/v1/migration/product/vehicle/engine_type` | Unknown | `ProductMigrationController.updateVehicleEngineType` (src/main/java/com/tvsmotor/mdp/product/controller/ProductMigrationController.java:18) | none recorded |
| GET | `/mdp/v1/part/{sapPartId}` | Unknown | `PartController.getPartDataBySapPartId` (src/main/java/com/tvsmotor/mdp/product_part/controller/PartController.java:16) | none recorded |
| GET | `/mdp/v1/part_price/{sapPartId}` | Unknown | `PartPriceController.getPartPriceDataBySapPartId` (src/main/java/com/tvsmotor/mdp/part_price/controller/PartPriceController.java:15) | none recorded |
| GET | `/mdp/v1/price/vehicle/sapModelIds` | Unknown | `PriceVehicleController.getDistinctSapModelIds` (src/main/java/com/tvsmotor/mdp/price/controller/PriceVehicleController.java:15) | none recorded |
| GET | `/mdp/v1/price/vehicle/{productId}` | Unknown | `PriceVehicleController.getVehiclePriceData` (src/main/java/com/tvsmotor/mdp/price/controller/PriceVehicleController.java:15) | none recorded |
| GET | `/mdp/v1/product/mna/v2/{sapPartNo}` | Unknown | `ProductMnaController.getProductMnaDataByPartNo` (src/main/java/com/tvsmotor/mdp/product_mna/controller/ProductMnaController.java:17) | none recorded |
| GET | `/mdp/v1/product/mna/{sapSkuId}` | Unknown | `ProductMnaController.getProductMnaDataBySapSkuId` (src/main/java/com/tvsmotor/mdp/product_mna/controller/ProductMnaController.java:17) | none recorded |
| GET | `/mdp/v1/product/vehicle/part/{sapPartId}` | Unknown | `ProductVehicleController.getProductVehicleDataWithSapPartId` (src/main/java/com/tvsmotor/mdp/product/controller/ProductVehicleController.java:14) | `tvsm-marketplace-service` |
| GET | `/mdp/v1/product/vehicle/sap-model-ids` | Unknown | `ProductVehicleController.getDistinctSapModelIds` (src/main/java/com/tvsmotor/mdp/product/controller/ProductVehicleController.java:14) | none recorded |
| GET | `/mdp/v1/product/vehicle/{sapModelId}` | Unknown | `ProductVehicleController.getProductVehicleData` (src/main/java/com/tvsmotor/mdp/product/controller/ProductVehicleController.java:14) | none recorded |
| GET | `/mdp/v1/test/dealers/nearest` | Unknown | `TestController.getNearestDealers` (src/main/java/com/tvsmotor/mdp/controller/TestController.java:32) | none recorded |
| GET | `/mdp/v1/test/health` | Unknown | `TestController.healthTest` (src/main/java/com/tvsmotor/mdp/controller/TestController.java:32) | none recorded |
| GET | `/mdp/v1/test/hello` | Unknown | `TestController.helloWorldApi` (src/main/java/com/tvsmotor/mdp/controller/TestController.java:32) | none recorded |
| GET | `/mdp/v1/test/service-bus/consume-dealer-data/{sapDealerCode}` | Unknown | `TestServiceBusController.consumeDealerData` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22) | none recorded |
| GET | `/mdp/v1/test/service-bus/push-dealer-data/{sapDealerCode}` | Unknown | `TestServiceBusController.pushDealerData` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22) | none recorded |
| GET | `/mdp/v1/test/service-bus/start-receiver` | Unknown | `TestServiceBusController.startTheReceiver` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22) | none recorded |
| GET | `/mdp/v1/test/service-bus/stop-receiver` | Unknown | `TestServiceBusController.stopTheReceiver` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22) | none recorded |
| GET | `/mdp/v1/test/stress` | Unknown | `TestController.test` (src/main/java/com/tvsmotor/mdp/controller/TestController.java:32) | none recorded |
| POST | `/mdp/v1/dealer/flag-type` | Unknown | `DealerFlagsTypeNewController.createNewFlagType` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsTypeNewController.java:17) | none recorded |
| POST | `/mdp/v1/dealer/flag-type/delete-flag/{dealerFlagTypeId}` | Unknown | `DealerFlagsTypeNewController.deleteFlagType` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsTypeNewController.java:17) | none recorded |
| POST | `/mdp/v1/dealer/mapDealerWithKNumber` | Unknown | `DealerKnowlarityDataController.mapDealerWithKNumber` (src/main/java/com/tvsmotor/mdp/controller/DealerKnowlarityDataController.java:16) | `tvsmbe-mdp-bff` |
| POST | `/mdp/v1/dealer/{sapDealerCode}/unassignKNumber` | Unknown | `DealerKnowlarityDataController.unassignKNumber` (src/main/java/com/tvsmotor/mdp/controller/DealerKnowlarityDataController.java:16) | none recorded |
| POST | `/mdp/v1/dealers/basedOnFilters` | Unknown | `DealerController.getDealerBasedOnTypeStatusFlags` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20) | `tvsmbe-mdp-bff` |
| POST | `/mdp/v1/dealers/data` | Unknown | `DealerController.getDealersData` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20) | `tvsmbe-location` |
| POST | `/mdp/v1/dealers/listOfDealerDetails/basedOnProximity` | Unknown | `DealerController.getListOfDealerDetailsBasedOnProximity` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20) | `tvsm-marketplace-service`, `tvsmbe-location` |
| POST | `/mdp/v1/dealers/listOfSapDealerCode/basedOnFilters` | Unknown | `DealerController.getListOfSapDealerCodesBasedOnTypeStatusFlags` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20) | `tvsmbe-location` |
| POST | `/mdp/v1/dealers/stateWiseCount/basedOnFilters` | Unknown | `DealerController.getDealersCountStateWiseBasedOnFilters` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20) | `tvsmbe-location` |
| POST | `/mdp/v1/dms-import/branch/{parentSapDealerCode}` | Unknown | `DMSMigrationController.updateBranch` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33) | none recorded |
| POST | `/mdp/v1/dms-import/dealer` | Unknown | `DMSMigrationController.importDmsDealerData` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33) | none recorded |
| POST | `/mdp/v1/dms-import/employee/{sapDealerCode}` | Unknown | `DMSMigrationController.updateEmployee` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33) | none recorded |
| POST | `/mdp/v1/dms-import/ingestDmsBranchData` | Unknown | `DMSMigrationController.ingestDmsBranchData` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33) | none recorded |
| POST | `/mdp/v1/dms-import/ingestDmsDealerData` | Unknown | `DMSMigrationController.ingestDmsDealerData` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33) | none recorded |
| POST | `/mdp/v1/dms-import/ingestDmsInternalBranchId` | Unknown | `DMSMigrationController.ingestDmsInternalBranchId` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33) | none recorded |
| POST | `/mdp/v1/latlong-import/dealer` | Unknown | `LatLongMigrationController.updateDealer` (src/main/java/com/tvsmotor/mdp/controller/migration/LatLongMigrationController.java:19) | none recorded |
| POST | `/mdp/v1/migration/dealer/addNewFlags` | Unknown | `DealerMigrationController.addNewFlags` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20) | none recorded |
| POST | `/mdp/v1/migration/dealer/addNewStateCode` | Unknown | `DealerLocationMigrationController.addStateDetails` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerLocationMigrationController.java:22) | none recorded |
| POST | `/mdp/v1/migration/dealer/knowlarity` | Unknown | `DealerLocationMigrationController.knowlarityMigration` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerLocationMigrationController.java:22) | none recorded |
| POST | `/mdp/v1/migration/dealer/state` | Unknown | `DealerLocationMigrationController.onboardNewState` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerLocationMigrationController.java:22) | none recorded |
| POST | `/mdp/v1/part/test/service-bus/push-part-data` | Unknown | `TestPartServiceBusController.pushPartData` (src/main/java/com/tvsmotor/mdp/product_part/controller/TestPartServiceBusController.java:18) | none recorded |
| POST | `/mdp/v1/part_price/test/service-bus/push-part-price-data` | Unknown | `TestPartPriceServiceBusController.pushPartPriceData` (src/main/java/com/tvsmotor/mdp/part_price/controller/TestPartPriceServiceBusController.java:18) | none recorded |
| POST | `/mdp/v1/price/test/service-bus/push-price-data` | Unknown | `TestPriceServiceBusController.pushPriceData` (src/main/java/com/tvsmotor/mdp/price/controller/TestPriceServiceBusController.java:18) | `price-engine-micro-service-backend` |
| POST | `/mdp/v1/product/test/service-bus/push-model-data` | Unknown | `TestProductServiceBusController.pushVehicleModelData` (src/main/java/com/tvsmotor/mdp/product/controller/TestProductServiceBusController.java:18) | none recorded |
| POST | `/mdp/v1/product/test/service-bus/push-part-data` | Unknown | `TestProductServiceBusController.pushVehiclePartData` (src/main/java/com/tvsmotor/mdp/product/controller/TestProductServiceBusController.java:18) | none recorded |
| POST | `/mdp/v1/product/test/service-bus/push-product-data` | Unknown | `TestProductServiceBusController.pushProductData` (src/main/java/com/tvsmotor/mdp/product/controller/TestProductServiceBusController.java:18) | `price-engine-micro-service-backend` |
| POST | `/mdp/v1/product_mna/test/service-bus/push-mna-data` | Unknown | `TestProductMnaServiceBusController.pushProductMnaData` (src/main/java/com/tvsmotor/mdp/product_mna/controller/TestProductMnaServiceBusController.java:18) | none recorded |
| POST | `/mdp/v1/test/performance` | Unknown | `TestController.testPerformance` (src/main/java/com/tvsmotor/mdp/controller/TestController.java:32) | none recorded |
| POST | `/mdp/v1/test/price/save` | Unknown | `TestSapPriceController.ingestPriceData` (src/main/java/com/tvsmotor/mdp/price/controller/TestSapPriceController.java:22) | none recorded |
| POST | `/mdp/v1/test/service-bus/push-dealers-data` | Unknown | `TestServiceBusController.pushDealersData` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22) | none recorded |
| POST | `/mdp/v1/test/service-bus/pushDmsBranchData` | Unknown | `TestServiceBusController.pushDmsBranchData` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22) | none recorded |
| POST | `/mdp/v1/test/service-bus/pushDmsDealerData` | Unknown | `TestServiceBusController.pushDmsDealerData` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22) | none recorded |
| PUT | `/mdp/v1/dealer/{sapDealerCode}/flag-deprecated/{dealerFlagType}` | Unknown | `DealerFlagsController.updateFlagValue` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsController.java:18) | none recorded |
| PUT | `/mdp/v1/dealer/{sapDealerCode}/flag/{flagId}` | Unknown | `DealerFlagsNewController.updateDealerFlagValue` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsNewController.java:15) | none recorded |
| PUT | `/mdp/v1/migration/dealer/2WAnd3WFlagMigration` | Unknown | `DealerMigrationController.sync2WAnd3WFlagBetweenAmdAndBranch` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20) | none recorded |
| None | `None` | Unknown | `src/main/java/com/tvsmotor/mdp/common/service/CronService.java:36` (Unknown) | none recorded |

Scheduled jobs:

| Job | Trigger | Expression | Handler |
|---|---|---|---|
| `CronService.logMetricsPeriodically` | fixed-rate | 60000 (literal) | `src/main/java/com/tvsmotor/mdp/common/service/CronService.java:36` |

## Endpoints
master-data-platform endpoint details (params/schemas from service.yaml; `Unknown` = not extracted).
### GET /mdp/v1/de-pipeline/trigger/{batchProcessingType}

Handler: `DE_PipelineController.startProcessing` (src/main/java/com/tvsmotor/mdp/controller/DE_PipelineController.java:20)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| batchProcessingType | path | enum[SAP_DATA,SHAREPOINT_DATA,DEALER_SAP_SERVICE_CENTER_ADDRESS_DATA,PRODUCT_VEHICLE_SAP_DATA,PRICE_VEHICLE_SAP_DATA,PRODUCT_MNA_SAP_DATA,PRODUCT_MNA_NEW_SAP_DATA,PART_SAP_DATA,PART_PRICE_SAP_DATA] | True | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/dealer/flag-type/list

Handler: `DealerFlagsTypeNewController.getAllFlagTypes` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsTypeNewController.java:17)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/dealer/latLong/sync

Handler: `LatLongDetailsController.importLatLongDetails` (src/main/java/com/tvsmotor/mdp/controller/LatLongDetailsController.java:17)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/dealer/{sapDealerCode}

Handler: `DealerController.getDealerData` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20)

Callers: `tvsm-auth`, `tvsm-marketplace-service`, `tvsmbe-location`

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapDealerCode | path | string | True | |
| skipCache | query | boolean | False | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/dealer/{sapDealerCode}/branches

Handler: `DealerController.getBranchesByParentDealerId` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20)

Callers: `tvsm-auth`, `tvsmbe-location`

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapDealerCode | path | string | True | |
| skipUnofficialBranches | query | boolean | False | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/dealer/{sapDealerCode}/flag/list

Handler: `DealerFlagsNewController.getAllDealerFlags` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsNewController.java:15)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapDealerCode | path | string | True | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/dealers

Handler: `DealerController.getDealersBasedOnPincode` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| pincode | query | string | True | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/dealers/active-counts

Handler: `DealerController.getActiveCounts` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/dms-import/trigger

Handler: `DMSMigrationController.startDmsMigration` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/migration/dealer/sanitizeAddressLines

Handler: `DealerLocationMigrationController.sanitizeAddressLinesForAllDealerLocations` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerLocationMigrationController.java:22)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/migration/dealer/sanitizePhoneNumbers

Handler: `DealerMigrationController.sanitizePhoneNumbers` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/migration/dealer/updateMdpDealerStatus

Handler: `DealerMigrationController.updateMdpDealerStatus` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/migration/dealer/updateSapStatus

Handler: `DealerMigrationController.updateSapStatus` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/migration/dealer/updateUnofficialBranches

Handler: `DealerMigrationController.updateUnofficialBranches` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/migration/product/vehicle/engine_type

Handler: `ProductMigrationController.updateVehicleEngineType` (src/main/java/com/tvsmotor/mdp/product/controller/ProductMigrationController.java:18)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/part/{sapPartId}

Handler: `PartController.getPartDataBySapPartId` (src/main/java/com/tvsmotor/mdp/product_part/controller/PartController.java:16)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapPartId | path | string | True | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/part_price/{sapPartId}

Handler: `PartPriceController.getPartPriceDataBySapPartId` (src/main/java/com/tvsmotor/mdp/part_price/controller/PartPriceController.java:15)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapPartId | path | string | True | |
| country | query | string | True | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/price/vehicle/sapModelIds

Handler: `PriceVehicleController.getDistinctSapModelIds` (src/main/java/com/tvsmotor/mdp/price/controller/PriceVehicleController.java:15)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/price/vehicle/{productId}

Handler: `PriceVehicleController.getVehiclePriceData` (src/main/java/com/tvsmotor/mdp/price/controller/PriceVehicleController.java:15)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| productId | path | string | True | |
| state | query | string | True | |
| country | query | string | True | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/product/mna/v2/{sapPartNo}

Handler: `ProductMnaController.getProductMnaDataByPartNo` (src/main/java/com/tvsmotor/mdp/product_mna/controller/ProductMnaController.java:17)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapPartNo | path | string | True | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/product/mna/{sapSkuId}

Handler: `ProductMnaController.getProductMnaDataBySapSkuId` (src/main/java/com/tvsmotor/mdp/product_mna/controller/ProductMnaController.java:17)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapSkuId | path | string | True | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/product/vehicle/part/{sapPartId}

Handler: `ProductVehicleController.getProductVehicleDataWithSapPartId` (src/main/java/com/tvsmotor/mdp/product/controller/ProductVehicleController.java:14)

Callers: `tvsm-marketplace-service`

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapPartId | path | string | True | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/product/vehicle/sap-model-ids

Handler: `ProductVehicleController.getDistinctSapModelIds` (src/main/java/com/tvsmotor/mdp/product/controller/ProductVehicleController.java:14)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/product/vehicle/{sapModelId}

Handler: `ProductVehicleController.getProductVehicleData` (src/main/java/com/tvsmotor/mdp/product/controller/ProductVehicleController.java:14)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapModelId | path | string | True | |
| partsData | query | boolean | False | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/test/dealers/nearest

Handler: `TestController.getNearestDealers` (src/main/java/com/tvsmotor/mdp/controller/TestController.java:32)

Callers: none recorded

Request body: `LatLongRequest[]`

Defined in `src/main/java/com/tvsmotor/mdp/common/model/request/LatLongRequest.java:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| pincode | string | False |  |
| latitude | string | False |  |
| longitude | string | False |  |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/test/health

Handler: `TestController.healthTest` (src/main/java/com/tvsmotor/mdp/controller/TestController.java:32)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapDealerCode | query | string | False | |
| property | query | string | False | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/test/hello

Handler: `TestController.helloWorldApi` (src/main/java/com/tvsmotor/mdp/controller/TestController.java:32)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapDealerCode | query | string | False | |
| threadSleepTimeInMs | query | integer | False | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/test/service-bus/consume-dealer-data/{sapDealerCode}

Handler: `TestServiceBusController.consumeDealerData` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapDealerCode | path | string | True | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/test/service-bus/push-dealer-data/{sapDealerCode}

Handler: `TestServiceBusController.pushDealerData` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapDealerCode | path | string | True | |
| eventType | query | enum[DEALER_CREATED,DEALER_UPDATED,ONE_TIME_MIGRATION] | True | |

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/test/service-bus/start-receiver

Handler: `TestServiceBusController.startTheReceiver` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/test/service-bus/stop-receiver

Handler: `TestServiceBusController.stopTheReceiver` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### GET /mdp/v1/test/stress

Handler: `TestController.test` (src/main/java/com/tvsmotor/mdp/controller/TestController.java:32)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dealer/flag-type

Handler: `DealerFlagsTypeNewController.createNewFlagType` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsTypeNewController.java:17)

Callers: none recorded

Request body: `DealerFlagTypeCreationRequest`

Defined in `src/main/java/com/tvsmotor/mdp/model/request/DealerFlagTypeCreationRequest.java:12`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| name | string | False |  |
| description | string | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dealer/flag-type/delete-flag/{dealerFlagTypeId}

Handler: `DealerFlagsTypeNewController.deleteFlagType` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsTypeNewController.java:17)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| dealerFlagTypeId | path | integer | True | |
| reasonForDeletion | query | string | True | |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dealer/mapDealerWithKNumber

Handler: `DealerKnowlarityDataController.mapDealerWithKNumber` (src/main/java/com/tvsmotor/mdp/controller/DealerKnowlarityDataController.java:16)

Callers: `tvsmbe-mdp-bff`

Request body: `MapDealerWithKNumberRequest`

Defined in `src/main/java/com/tvsmotor/mdp/model/request/MapDealerWithKNumberRequest.java:9`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| sapDealerCode | string | False |  |
| knowlarityVirtualNumber | string | False |  |
| knowlarityRoutingCli | string | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dealer/{sapDealerCode}/unassignKNumber

Handler: `DealerKnowlarityDataController.unassignKNumber` (src/main/java/com/tvsmotor/mdp/controller/DealerKnowlarityDataController.java:16)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapDealerCode | path | string | True | |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dealers/basedOnFilters

Handler: `DealerController.getDealerBasedOnTypeStatusFlags` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20)

Callers: `tvsmbe-mdp-bff`

Request body: `DealerTypeStatusFlagsFilterRequest`

Defined in `src/main/java/com/tvsmotor/mdp/model/request/DealerTypeStatusFlagsFilterRequest.java:18`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| type | enum[AMD,SPD,APS,BRANCH,AD] | False |  |
| sapStatus | enum[PRE_ACTIVE,ACTIVE,PERMANENTLY_BLOCKED,NOT_PRESENT_IN_SAP,TEMPORARILY_BLOCKED] | False |  |
| dmsStatus | enum[PRE_ACTIVE,ACTIVE,INACTIVE] | False |  |
| mdpStatus | enum[PRE_ACTIVE,ACTIVE,INACTIVE] | False |  |
| flags | enum[SALES,SERVICE,DIGITAL_LEADS,EMS,TWO_WHEELER,THREE_WHEELER,IQUBE,RONIN,RR310,U400,RTR310,RTR200,TVSX,DIGITAL_LEADS_EV,DIGITAL_LEADS_3W,U546,RTX,THREE_WHEELER_ICE_PASSENGER,THREE_WHEELER_EV_PASSENGER,THREE_WHEELER_ICE_CARGO,THREE_WHEELER_EV_CARGO,NORTON_MANXR,NORTON_ATLAS,DEFAULT_DTR_PROVIDED,IQUBE_DTR_PROVIDED,TVSX_DTR_PROVIDED,U546_DTR_PROVIDED,DEFAULT_HTR_PROVIDED,IQUBE_HTR_PROVIDED,TVSX_HTR_PROVIDED,U546_HTR_PROVIDED,IQUBE_OFFLINE_BOOKING_ENABLED,TVSX_OFFLINE_BOOKING_ENABLED,U546_OFFLINE_BOOKING_ENABLED,K_NUMBER_NEEDED,BIKE_DEKHO,BIKE_WALE,NINETY_ONE_WHEELS,ASSP,MKTPLACE_FLIPKART_ENABLED,MKTPLACE_AMAZON_ENABLED,RVSF,PBZ,EV_SAFETY_COMPLIANCE][] | False |  |
| search | Search | False |  |
| location | Location | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dealers/data

Handler: `DealerController.getDealersData` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20)

Callers: `tvsmbe-location`

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| fetchMdpActiveDealersOnly | query | boolean | False | |

Request body: `string[]`

Fields: Unknown (no schema extracted for `string[]`).

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dealers/listOfDealerDetails/basedOnProximity

Handler: `DealerController.getListOfDealerDetailsBasedOnProximity` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20)

Callers: `tvsm-marketplace-service`, `tvsmbe-location`

Request body: `ProximityRequest`

Defined in `src/main/java/com/tvsmotor/mdp/model/request/ProximityRequest.java:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| proximity | Proximity | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dealers/listOfSapDealerCode/basedOnFilters

Handler: `DealerController.getListOfSapDealerCodesBasedOnTypeStatusFlags` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20)

Callers: `tvsmbe-location`

Request body: `DealerTypeStatusFlagsFilterRequest`

Defined in `src/main/java/com/tvsmotor/mdp/model/request/DealerTypeStatusFlagsFilterRequest.java:18`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| type | enum[AMD,SPD,APS,BRANCH,AD] | False |  |
| sapStatus | enum[PRE_ACTIVE,ACTIVE,PERMANENTLY_BLOCKED,NOT_PRESENT_IN_SAP,TEMPORARILY_BLOCKED] | False |  |
| dmsStatus | enum[PRE_ACTIVE,ACTIVE,INACTIVE] | False |  |
| mdpStatus | enum[PRE_ACTIVE,ACTIVE,INACTIVE] | False |  |
| flags | enum[SALES,SERVICE,DIGITAL_LEADS,EMS,TWO_WHEELER,THREE_WHEELER,IQUBE,RONIN,RR310,U400,RTR310,RTR200,TVSX,DIGITAL_LEADS_EV,DIGITAL_LEADS_3W,U546,RTX,THREE_WHEELER_ICE_PASSENGER,THREE_WHEELER_EV_PASSENGER,THREE_WHEELER_ICE_CARGO,THREE_WHEELER_EV_CARGO,NORTON_MANXR,NORTON_ATLAS,DEFAULT_DTR_PROVIDED,IQUBE_DTR_PROVIDED,TVSX_DTR_PROVIDED,U546_DTR_PROVIDED,DEFAULT_HTR_PROVIDED,IQUBE_HTR_PROVIDED,TVSX_HTR_PROVIDED,U546_HTR_PROVIDED,IQUBE_OFFLINE_BOOKING_ENABLED,TVSX_OFFLINE_BOOKING_ENABLED,U546_OFFLINE_BOOKING_ENABLED,K_NUMBER_NEEDED,BIKE_DEKHO,BIKE_WALE,NINETY_ONE_WHEELS,ASSP,MKTPLACE_FLIPKART_ENABLED,MKTPLACE_AMAZON_ENABLED,RVSF,PBZ,EV_SAFETY_COMPLIANCE][] | False |  |
| search | Search | False |  |
| location | Location | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dealers/stateWiseCount/basedOnFilters

Handler: `DealerController.getDealersCountStateWiseBasedOnFilters` (src/main/java/com/tvsmotor/mdp/controller/DealerController.java:20)

Callers: `tvsmbe-location`

Request body: `DealerStateWiseCountFilterRequest`

Defined in `src/main/java/com/tvsmotor/mdp/model/request/DealerStateWiseCountFilterRequest.java:19`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| types | enum[AMD,SPD,APS,BRANCH,AD][] | False |  |
| mdpStatus | enum[PRE_ACTIVE,ACTIVE,INACTIVE] | False |  |
| flags | enum[SALES,SERVICE,DIGITAL_LEADS,EMS,TWO_WHEELER,THREE_WHEELER,IQUBE,RONIN,RR310,U400,RTR310,RTR200,TVSX,DIGITAL_LEADS_EV,DIGITAL_LEADS_3W,U546,RTX,THREE_WHEELER_ICE_PASSENGER,THREE_WHEELER_EV_PASSENGER,THREE_WHEELER_ICE_CARGO,THREE_WHEELER_EV_CARGO,NORTON_MANXR,NORTON_ATLAS,DEFAULT_DTR_PROVIDED,IQUBE_DTR_PROVIDED,TVSX_DTR_PROVIDED,U546_DTR_PROVIDED,DEFAULT_HTR_PROVIDED,IQUBE_HTR_PROVIDED,TVSX_HTR_PROVIDED,U546_HTR_PROVIDED,IQUBE_OFFLINE_BOOKING_ENABLED,TVSX_OFFLINE_BOOKING_ENABLED,U546_OFFLINE_BOOKING_ENABLED,K_NUMBER_NEEDED,BIKE_DEKHO,BIKE_WALE,NINETY_ONE_WHEELS,ASSP,MKTPLACE_FLIPKART_ENABLED,MKTPLACE_AMAZON_ENABLED,RVSF,PBZ,EV_SAFETY_COMPLIANCE][] | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dms-import/branch/{parentSapDealerCode}

Handler: `DMSMigrationController.updateBranch` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| parentSapDealerCode | path | string | True | |

Request body: `DealerBranches`

Defined in `src/main/java/com/tvsmotor/mdp/model/migration/DealerBranches.java:11`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dmsBranches | DMSBranch[] | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dms-import/dealer

Handler: `DMSMigrationController.importDmsDealerData` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33)

Callers: none recorded

Request body: `DMSDealerBatch`

Defined in `src/main/java/com/tvsmotor/mdp/model/migration/DMSDealerBatch.java:8`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dmsDealers | DMSDealer[] | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dms-import/employee/{sapDealerCode}

Handler: `DMSMigrationController.updateEmployee` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapDealerCode | path | string | True | |

Request body: `DealerEmployees`

Defined in `src/main/java/com/tvsmotor/mdp/model/migration/DealerEmployees.java:8`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dealerEmployees | DMSEmployee[] | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dms-import/ingestDmsBranchData

Handler: `DMSMigrationController.ingestDmsBranchData` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33)

Callers: none recorded

Request body: `DmsBranchData[]`

Defined in `src/main/java/com/tvsmotor/mdp/dealer/model/service_bus/DmsBranchData.java:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| branch | Branch | False |  |
| address | Address | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dms-import/ingestDmsDealerData

Handler: `DMSMigrationController.ingestDmsDealerData` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33)

Callers: none recorded

Request body: `DmsDealerData[]`

Defined in `src/main/java/com/tvsmotor/mdp/dealer/model/service_bus/DmsDealerData.java:9`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dealer | DmsDealer | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/dms-import/ingestDmsInternalBranchId

Handler: `DMSMigrationController.ingestDmsInternalBranchId` (src/main/java/com/tvsmotor/mdp/controller/migration/DMSMigrationController.java:33)

Callers: none recorded

Request body: `DmsBranchData`

Defined in `src/main/java/com/tvsmotor/mdp/dealer/model/service_bus/DmsBranchData.java:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| branch | Branch | False |  |
| address | Address | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/latlong-import/dealer

Handler: `LatLongMigrationController.updateDealer` (src/main/java/com/tvsmotor/mdp/controller/migration/LatLongMigrationController.java:19)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/migration/dealer/addNewFlags

Handler: `DealerMigrationController.addNewFlags` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/migration/dealer/addNewStateCode

Handler: `DealerLocationMigrationController.addStateDetails` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerLocationMigrationController.java:22)

Callers: none recorded

Request body: `StateDetailsRequest[]`

Defined in `src/main/java/com/tvsmotor/mdp/common/model/request/StateDetailsRequest.java:9`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| stateCode | string | False |  |
| stateName | string | False |  |
| addedBy | string | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/migration/dealer/knowlarity

Handler: `DealerLocationMigrationController.knowlarityMigration` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerLocationMigrationController.java:22)

Callers: none recorded

Request body: `KnowlarityMigrationRequest[]`

Defined in `src/main/java/com/tvsmotor/mdp/common/model/request/KnowlarityMigrationRequest.java:11`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| sapDealerCode | string | False |  |
| branchId | integer | False |  |
| knowlarityVirtualNumber | string | False |  |
| knowlarityRoutingCli | string | False |  |
| knowlarityFallbackNumber | string | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/migration/dealer/state

Handler: `DealerLocationMigrationController.onboardNewState` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerLocationMigrationController.java:22)

Callers: none recorded

Request body: `OnBoardNewStateRequest[]`

Defined in `src/main/java/com/tvsmotor/mdp/common/model/request/OnBoardNewStateRequest.java:9`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| stateName | string | False |  |
| knowlarityFallbackNumber | string | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/part/test/service-bus/push-part-data

Handler: `TestPartServiceBusController.pushPartData` (src/main/java/com/tvsmotor/mdp/product_part/controller/TestPartServiceBusController.java:18)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| eventType | query | enum[PART_CREATED,PART_UPDATED,ONE_TIME_MIGRATION] | True | |

Request body: `string[]`

Fields: Unknown (no schema extracted for `string[]`).

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/part_price/test/service-bus/push-part-price-data

Handler: `TestPartPriceServiceBusController.pushPartPriceData` (src/main/java/com/tvsmotor/mdp/part_price/controller/TestPartPriceServiceBusController.java:18)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| eventType | query | enum[PART_PRICE_CREATED,PART_PRICE_UPDATED,ONE_TIME_MIGRATION] | True | |

Request body: `string[]`

Fields: Unknown (no schema extracted for `string[]`).

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/price/test/service-bus/push-price-data

Handler: `TestPriceServiceBusController.pushPriceData` (src/main/java/com/tvsmotor/mdp/price/controller/TestPriceServiceBusController.java:18)

Callers: `price-engine-micro-service-backend`

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| state | query | string | False | |
| country | query | string | False | |
| eventType | query | enum[VEHICLE_PRICE_CREATED,VEHICLE_PRICE_UPDATED,ONE_TIME_MIGRATION] | True | |

Request body: `string[]`

Fields: Unknown (no schema extracted for `string[]`).

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/product/test/service-bus/push-model-data

Handler: `TestProductServiceBusController.pushVehicleModelData` (src/main/java/com/tvsmotor/mdp/product/controller/TestProductServiceBusController.java:18)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| eventType | query | enum[VEHICLE_CREATED,VEHICLE_UPDATED,VEHICLE_MODEL_CREATED,VEHICLE_MODEL_UPDATED,VEHICLE_PART_CREATED,VEHICLE_PART_UPDATED,ONE_TIME_MIGRATION] | True | |

Request body: `string[]`

Fields: Unknown (no schema extracted for `string[]`).

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/product/test/service-bus/push-part-data

Handler: `TestProductServiceBusController.pushVehiclePartData` (src/main/java/com/tvsmotor/mdp/product/controller/TestProductServiceBusController.java:18)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| eventType | query | enum[VEHICLE_CREATED,VEHICLE_UPDATED,VEHICLE_MODEL_CREATED,VEHICLE_MODEL_UPDATED,VEHICLE_PART_CREATED,VEHICLE_PART_UPDATED,ONE_TIME_MIGRATION] | True | |

Request body: `string[]`

Fields: Unknown (no schema extracted for `string[]`).

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/product/test/service-bus/push-product-data

Handler: `TestProductServiceBusController.pushProductData` (src/main/java/com/tvsmotor/mdp/product/controller/TestProductServiceBusController.java:18)

Callers: `price-engine-micro-service-backend`

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| eventType | query | enum[VEHICLE_CREATED,VEHICLE_UPDATED,VEHICLE_MODEL_CREATED,VEHICLE_MODEL_UPDATED,VEHICLE_PART_CREATED,VEHICLE_PART_UPDATED,ONE_TIME_MIGRATION] | True | |

Request body: `string[]`

Fields: Unknown (no schema extracted for `string[]`).

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/product_mna/test/service-bus/push-mna-data

Handler: `TestProductMnaServiceBusController.pushProductMnaData` (src/main/java/com/tvsmotor/mdp/product_mna/controller/TestProductMnaServiceBusController.java:18)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| eventType | query | enum[PRODUCT_MNA_CREATED,PRODUCT_MNA_UPDATED,ONE_TIME_MIGRATION] | True | |

Request body: `string[]`

Fields: Unknown (no schema extracted for `string[]`).

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/test/performance

Handler: `TestController.testPerformance` (src/main/java/com/tvsmotor/mdp/controller/TestController.java:32)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| nThreads | query | integer | True | |
| threadSleepTimeInMs | query | integer | False | |
| option | query | integer | True | |

Request body: `string[]`

Fields: Unknown (no schema extracted for `string[]`).

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/test/price/save

Handler: `TestSapPriceController.ingestPriceData` (src/main/java/com/tvsmotor/mdp/price/controller/TestSapPriceController.java:22)

Callers: none recorded

Request body: `PriceVehicleSapData[]`

Defined in `src/main/java/com/tvsmotor/mdp/price/entity/batch_processing/PriceVehicleSapData.java:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| id | integer | False |  |
| createdAt | datetime | False |  |
| createdBy | string | False |  |
| requestAcceptedByAzureDatalakeOn | datetime | False |  |
| sapModelId | string | False |  |
| exShowroomPrice | string | False |  |
| exFactoryPrice | string | False |  |
| country | string | False |  |
| state | string | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/test/service-bus/push-dealers-data

Handler: `TestServiceBusController.pushDealersData` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| eventType | query | enum[DEALER_CREATED,DEALER_UPDATED,ONE_TIME_MIGRATION] | True | |

Request body: `string[]`

Fields: Unknown (no schema extracted for `string[]`).

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/test/service-bus/pushDmsBranchData

Handler: `TestServiceBusController.pushDmsBranchData` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22)

Callers: none recorded

Request body: `DmsBranchData[]`

Defined in `src/main/java/com/tvsmotor/mdp/dealer/model/service_bus/DmsBranchData.java:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| branch | Branch | False |  |
| address | Address | False |  |

Response `200`: `GeneralResponse` — see Schemas

### POST /mdp/v1/test/service-bus/pushDmsDealerData

Handler: `TestServiceBusController.pushDmsDealerData` (src/main/java/com/tvsmotor/mdp/controller/TestServiceBusController.java:22)

Callers: none recorded

Request body: `DmsDealerData[]`

Defined in `src/main/java/com/tvsmotor/mdp/dealer/model/service_bus/DmsDealerData.java:9`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dealer | DmsDealer | False |  |

Response `200`: `GeneralResponse` — see Schemas

### PUT /mdp/v1/dealer/{sapDealerCode}/flag-deprecated/{dealerFlagType}

Handler: `DealerFlagsController.updateFlagValue` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsController.java:18)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapDealerCode | path | string | True | |
| dealerFlagType | path | enum[SALES,SERVICE,DIGITAL_LEADS,EMS,TWO_WHEELER,THREE_WHEELER,IQUBE,RONIN,RR310,U400,RTR310,RTR200,TVSX,DIGITAL_LEADS_EV,DIGITAL_LEADS_3W,U546,RTX,THREE_WHEELER_ICE_PASSENGER,THREE_WHEELER_EV_PASSENGER,THREE_WHEELER_ICE_CARGO,THREE_WHEELER_EV_CARGO,NORTON_MANXR,NORTON_ATLAS,DEFAULT_DTR_PROVIDED,IQUBE_DTR_PROVIDED,TVSX_DTR_PROVIDED,U546_DTR_PROVIDED,DEFAULT_HTR_PROVIDED,IQUBE_HTR_PROVIDED,TVSX_HTR_PROVIDED,U546_HTR_PROVIDED,IQUBE_OFFLINE_BOOKING_ENABLED,TVSX_OFFLINE_BOOKING_ENABLED,U546_OFFLINE_BOOKING_ENABLED,K_NUMBER_NEEDED,BIKE_DEKHO,BIKE_WALE,NINETY_ONE_WHEELS,ASSP,MKTPLACE_FLIPKART_ENABLED,MKTPLACE_AMAZON_ENABLED,RVSF,PBZ,EV_SAFETY_COMPLIANCE] | True | |
| newValue | query | boolean | True | |

Response `200`: `GeneralResponse` — see Schemas

### PUT /mdp/v1/dealer/{sapDealerCode}/flag/{flagId}

Handler: `DealerFlagsNewController.updateDealerFlagValue` (src/main/java/com/tvsmotor/mdp/controller/DealerFlagsNewController.java:15)

Callers: none recorded

Parameters:

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| sapDealerCode | path | string | True | |
| flagId | path | integer | True | |
| newFlagValue | query | integer | True | |

Response `200`: `GeneralResponse` — see Schemas

### PUT /mdp/v1/migration/dealer/2WAnd3WFlagMigration

Handler: `DealerMigrationController.sync2WAnd3WFlagBetweenAmdAndBranch` (src/main/java/com/tvsmotor/mdp/controller/migration/DealerMigrationController.java:20)

Callers: none recorded

Response `200`: `GeneralResponse` — see Schemas

### None None

Handler: `src/main/java/com/tvsmotor/mdp/common/service/CronService.java:36` (Unknown)

Callers: none recorded

## Outbound Calls
master-data-platform outbound HTTP calls (service.yaml `outbound`):

| Target (service_id) | Method | Path / Topic | Request schema | Response schema | Purpose | Criticality |
|---|---|---|---|---|---|---|
| Unknown | GET | `/v2/brands/{}/stores.json` | Unknown | Unknown | Unknown (base URL: literal) | Unknown |
| Unknown | POST | `/oauth/token` | Unknown | Unknown | Unknown (base URL: literal) | Unknown |
| Unknown | POST | `/` | Unknown | Unknown | Unknown (base URL: config:azure.b2c.token.url) | Unknown |
| notification-service | POST | `/api/v1/notification/email` | Unknown | Unknown | Unknown (base URL: config:notification.base-url) | hard |

## Schemas
master-data-platform schemas referenced by endpoints/events (22 of 51 extracted).
### GeneralResponse
Defined in `src/main/java/com/tvsmotor/mdp/model/GeneralResponse.java:9`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| data | object | False |  |
| errorMessage | string | False |  |
| time | string | False |  |
| uuid | string | False |  |
| timeTakenInMs | integer | False |  |
| serverId | string | False |  |

### LatLongRequest
Defined in `src/main/java/com/tvsmotor/mdp/common/model/request/LatLongRequest.java:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| pincode | string | False |  |
| latitude | string | False |  |
| longitude | string | False |  |

### DealerFlagTypeCreationRequest
Defined in `src/main/java/com/tvsmotor/mdp/model/request/DealerFlagTypeCreationRequest.java:12`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| name | string | False |  |
| description | string | False |  |

### MapDealerWithKNumberRequest
Defined in `src/main/java/com/tvsmotor/mdp/model/request/MapDealerWithKNumberRequest.java:9`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| sapDealerCode | string | False |  |
| knowlarityVirtualNumber | string | False |  |
| knowlarityRoutingCli | string | False |  |

### DealerTypeStatusFlagsFilterRequest
Defined in `src/main/java/com/tvsmotor/mdp/model/request/DealerTypeStatusFlagsFilterRequest.java:18`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| type | enum[AMD,SPD,APS,BRANCH,AD] | False |  |
| sapStatus | enum[PRE_ACTIVE,ACTIVE,PERMANENTLY_BLOCKED,NOT_PRESENT_IN_SAP,TEMPORARILY_BLOCKED] | False |  |
| dmsStatus | enum[PRE_ACTIVE,ACTIVE,INACTIVE] | False |  |
| mdpStatus | enum[PRE_ACTIVE,ACTIVE,INACTIVE] | False |  |
| flags | enum[SALES,SERVICE,DIGITAL_LEADS,EMS,TWO_WHEELER,THREE_WHEELER,IQUBE,RONIN,RR310,U400,RTR310,RTR200,TVSX,DIGITAL_LEADS_EV,DIGITAL_LEADS_3W,U546,RTX,THREE_WHEELER_ICE_PASSENGER,THREE_WHEELER_EV_PASSENGER,THREE_WHEELER_ICE_CARGO,THREE_WHEELER_EV_CARGO,NORTON_MANXR,NORTON_ATLAS,DEFAULT_DTR_PROVIDED,IQUBE_DTR_PROVIDED,TVSX_DTR_PROVIDED,U546_DTR_PROVIDED,DEFAULT_HTR_PROVIDED,IQUBE_HTR_PROVIDED,TVSX_HTR_PROVIDED,U546_HTR_PROVIDED,IQUBE_OFFLINE_BOOKING_ENABLED,TVSX_OFFLINE_BOOKING_ENABLED,U546_OFFLINE_BOOKING_ENABLED,K_NUMBER_NEEDED,BIKE_DEKHO,BIKE_WALE,NINETY_ONE_WHEELS,ASSP,MKTPLACE_FLIPKART_ENABLED,MKTPLACE_AMAZON_ENABLED,RVSF,PBZ,EV_SAFETY_COMPLIANCE][] | False |  |
| search | Search | False |  |
| location | Location | False |  |

### ProximityRequest
Defined in `src/main/java/com/tvsmotor/mdp/model/request/ProximityRequest.java:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| proximity | Proximity | False |  |

### DealerStateWiseCountFilterRequest
Defined in `src/main/java/com/tvsmotor/mdp/model/request/DealerStateWiseCountFilterRequest.java:19`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| types | enum[AMD,SPD,APS,BRANCH,AD][] | False |  |
| mdpStatus | enum[PRE_ACTIVE,ACTIVE,INACTIVE] | False |  |
| flags | enum[SALES,SERVICE,DIGITAL_LEADS,EMS,TWO_WHEELER,THREE_WHEELER,IQUBE,RONIN,RR310,U400,RTR310,RTR200,TVSX,DIGITAL_LEADS_EV,DIGITAL_LEADS_3W,U546,RTX,THREE_WHEELER_ICE_PASSENGER,THREE_WHEELER_EV_PASSENGER,THREE_WHEELER_ICE_CARGO,THREE_WHEELER_EV_CARGO,NORTON_MANXR,NORTON_ATLAS,DEFAULT_DTR_PROVIDED,IQUBE_DTR_PROVIDED,TVSX_DTR_PROVIDED,U546_DTR_PROVIDED,DEFAULT_HTR_PROVIDED,IQUBE_HTR_PROVIDED,TVSX_HTR_PROVIDED,U546_HTR_PROVIDED,IQUBE_OFFLINE_BOOKING_ENABLED,TVSX_OFFLINE_BOOKING_ENABLED,U546_OFFLINE_BOOKING_ENABLED,K_NUMBER_NEEDED,BIKE_DEKHO,BIKE_WALE,NINETY_ONE_WHEELS,ASSP,MKTPLACE_FLIPKART_ENABLED,MKTPLACE_AMAZON_ENABLED,RVSF,PBZ,EV_SAFETY_COMPLIANCE][] | False |  |

### DealerBranches
Defined in `src/main/java/com/tvsmotor/mdp/model/migration/DealerBranches.java:11`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dmsBranches | DMSBranch[] | False |  |

### DMSDealerBatch
Defined in `src/main/java/com/tvsmotor/mdp/model/migration/DMSDealerBatch.java:8`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dmsDealers | DMSDealer[] | False |  |

### DealerEmployees
Defined in `src/main/java/com/tvsmotor/mdp/model/migration/DealerEmployees.java:8`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dealerEmployees | DMSEmployee[] | False |  |

### DmsBranchData
Defined in `src/main/java/com/tvsmotor/mdp/dealer/model/service_bus/DmsBranchData.java:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| branch | Branch | False |  |
| address | Address | False |  |

### DmsDealerData
Defined in `src/main/java/com/tvsmotor/mdp/dealer/model/service_bus/DmsDealerData.java:9`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dealer | DmsDealer | False |  |

### StateDetailsRequest
Defined in `src/main/java/com/tvsmotor/mdp/common/model/request/StateDetailsRequest.java:9`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| stateCode | string | False |  |
| stateName | string | False |  |
| addedBy | string | False |  |

### KnowlarityMigrationRequest
Defined in `src/main/java/com/tvsmotor/mdp/common/model/request/KnowlarityMigrationRequest.java:11`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| sapDealerCode | string | False |  |
| branchId | integer | False |  |
| knowlarityVirtualNumber | string | False |  |
| knowlarityRoutingCli | string | False |  |
| knowlarityFallbackNumber | string | False |  |

### OnBoardNewStateRequest
Defined in `src/main/java/com/tvsmotor/mdp/common/model/request/OnBoardNewStateRequest.java:9`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| stateName | string | False |  |
| knowlarityFallbackNumber | string | False |  |

### PriceVehicleSapData
Defined in `src/main/java/com/tvsmotor/mdp/price/entity/batch_processing/PriceVehicleSapData.java:10`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| id | integer | False |  |
| createdAt | datetime | False |  |
| createdBy | string | False |  |
| requestAcceptedByAzureDatalakeOn | datetime | False |  |
| sapModelId | string | False |  |
| exShowroomPrice | string | False |  |
| exFactoryPrice | string | False |  |
| country | string | False |  |
| state | string | False |  |

### DealerData
Defined in `src/main/java/com/tvsmotor/mdp/model/redis/DealerData.java:13`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| dealer | map<string,object> | False |  |
| dealerDetails | map<string,object> | False |  |
| locations | map<string,object>[] | False |  |
| contacts | map<string,object>[] | False |  |
| flags | map<string,object>[] | False |  |
| employees | map<string,object>[] | False |  |

### PartData
Defined in `src/main/java/com/tvsmotor/mdp/product_part/model/redis/PartData.java:13`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| partData | map<string,object> | False |  |
| partMarkets | map<string,object>[] | False |  |

### PartPriceData
Defined in `src/main/java/com/tvsmotor/mdp/part_price/model/redis/PartPriceData.java:12`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| partPriceData | map<string,object> | False |  |

### PriceVehicleData
Defined in `src/main/java/com/tvsmotor/mdp/price/redis/PriceVehicleData.java:12`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| vehiclePrice | map<string,object> | False |  |

### ProductMnaData
Defined in `src/main/java/com/tvsmotor/mdp/product_mna/redis/ProductMnaData.java:12`

| Field | Type | Required | Validation / Notes |
|---|---|---|---|
| productMnaData | map<string,object> | False |  |

### ServiceBusOutgoingMessagePayloadBody
`ServiceBusOutgoingMessagePayloadBody` defined in `src/main/java/com/tvsmotor/mdp/common/model/service_bus/ServiceBusOutgoingMessagePayloadBody.java:3`; no fields extracted.

Other extracted schemas (see service.yaml `schemas`): `APIRequest<DealerStateWiseCountFilterRequest>`, `APIRequest<DealerTypeStatusFlagsFilterRequest>`, `APIRequest<KnowlarityMigrationRequest>`, `APIRequest<LatLongRequest>`, `APIRequest<MapDealerWithKNumberRequest>`, `APIRequest<OnBoardNewStateRequest>`, `APIRequest<StateDetailsRequest>`, `Address`, `Branch`, `CacheableObject`, `DMSBranch`, `DMSDealer`, `DMSEmployee`, `DealerFlagType`, `DealerType`, `DmsData`, `DmsDealer`, `DmsServiceBusIncomingMessagePayloadBody`, `DmsStatus`, `Location`, `MdpDealerStatus`, `Proximity`, `Sanitizeable<DealerFlagTypeCreationRequest>`, `Sanitizeable<E>`, `SapStatus`, `Search`, `ServiceBusIncomingMessagePayloadBody`, `Validateable<DealerFlagTypeCreationRequest>`, `Validateable<E>`

## Events Published
master-data-platform publishes:

| Topic / Queue | Type | Broker | Message types | Payload schema | Published from (file:line) | Consumers |
|---|---|---|---|---|---|---|
| `local.mdp.dealer_data` (name from config:spring.jms.servicebus.topic.dealerData.name) | topic | azure-service-bus | Unknown | DealerData | `src/main/java/com/tvsmotor/mdp/service/service_bus/DealerDataSenderService.java:87` | `master-data-platform`, `tvsmbe-mdp-bff` |
| `local.dms.dealer_data` (name from config:spring.jms.servicebus.topic.dmsDealerData.name) | topic | azure-service-bus | Unknown | DealerData | `src/main/java/com/tvsmotor/mdp/service/service_bus/DealerDataSenderService.java:176` | `master-data-platform` |
| `local.mdp.part_data` (name from config:spring.jms.servicebus.topic.partData.name) | topic | azure-service-bus | Unknown | PartData | `src/main/java/com/tvsmotor/mdp/product_part/service/service_bus/PartDataSenderService.java:45` | none recorded |
| `local.mdp.part.price` (name from config:spring.jms.servicebus.topic.partPriceData.name) | topic | azure-service-bus | Unknown | PartPriceData | `src/main/java/com/tvsmotor/mdp/part_price/service/service_bus/PartPriceDataSenderService.java:45` | none recorded |
| `local.mdp.price.vehicle` (name from config:spring.jms.servicebus.topic.priceVehicleData.name) | topic | azure-service-bus | Unknown | PriceVehicleData | `src/main/java/com/tvsmotor/mdp/price/service/service_bus/PriceVehicleDataSenderService.java:52` | `price-engine-micro-service-backend` |
| `local.mdp.product.mna` (name from config:spring.jms.servicebus.topic.productMnaData.name) | topic | azure-service-bus | Unknown | ProductMnaData | `src/main/java/com/tvsmotor/mdp/product_mna/service/service_bus/ProductMnaDataSenderService.java:50` | none recorded |
| `local.mdp.product.vehicle` (name from config:spring.jms.servicebus.topic.productVehicleData.name) | topic | azure-service-bus | Unknown | ServiceBusOutgoingMessagePayloadBody | `src/main/java/com/tvsmotor/mdp/product/service/service_bus/ProductVehicleDataSenderService.java:50` | `price-engine-micro-service-backend` |

## Events Consumed
master-data-platform consumes:

| Topic / Queue | Subscription | Filter | Message types | Payload schema | Handler (file:line) | Producers | Action | DLQ / retry |
|---|---|---|---|---|---|---|---|---|
| `local.mdp.dealer_data` (name from config:spring.jms.servicebus.topic.dealerData.name) | mdp | Unknown | Unknown | Unknown | `src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:50` | `master-data-platform` | Unknown | {'error_handler': True} |
| `local.dms.dealer_data` (name from config:spring.jms.servicebus.topic.dmsDealerData.name) | mdp | Unknown | Unknown | Unknown | `src/main/java/com/tvsmotor/mdp/config/DealerMasterServiceBusConfig.java:91` | `master-data-platform` | Unknown | {'error_handler': True} |
| `dev.mdp.dealer_data` (name from literal) | user | Unknown | Unknown | Unknown | `script/java/service_bus/DealerDataConsumer.java:17` | none recorded | Unknown | {'error_handler': True} |
| `local.mdp.part` (name from literal) | mdp | Unknown | Unknown | Unknown | `script/java/service_bus/ProductPartDataConsumer.java:17` | none recorded | Unknown | {'error_handler': True} |
| `local.mdp.price.vehicle` (name from literal) | price | Unknown | Unknown | Unknown | `script/java/service_bus/PriceVehicleDataConsumer.java:17` | none recorded | Unknown | {'error_handler': True} |
| `mdp.product.vehicle` (name from literal) | ccp | Unknown | Unknown | Unknown | `script/java/service_bus/ProductVehicleDataConsumer.java:17` | none recorded | Unknown | {'error_handler': True} |

Non-runtime (script) messaging found in repo: `dev.mdp.dealer_data` handler `script/java/service_bus/DealerDataConsumer.java:17`; `local.mdp.part` handler `script/java/service_bus/ProductPartDataConsumer.java:17`; `local.mdp.price.vehicle` handler `script/java/service_bus/PriceVehicleDataConsumer.java:17`; `mdp.product.vehicle` handler `script/java/service_bus/ProductVehicleDataConsumer.java:17`

## External Integrations
master-data-platform external integrations:

| System | Purpose | Auth |
|---|---|---|
| none resolved | | |

master-data-platform also calls `api.latlong.in` (`service/LatLongService.java:66`, literal base URL) and an Azure B2C token endpoint (`service/AzureB2CTokenGenerationService.java:47`, base `config:azure.b2c.token.url`); not registered as `external:` targets.

## Rate Limits and SLAs
master-data-platform: N/A — not determinable from code.
