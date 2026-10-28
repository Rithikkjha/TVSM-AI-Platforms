---
service_id: catalog-scheduler
doc_type: lld
last_reviewed: 2026-10-11
---

# catalog-scheduler — Low-Level Design

## Data Model
catalog-scheduler entities from `data_access` items (1).

Store access at `src/db-connection/db-configuration.js:19`: database Unknown; collections discounts, evPriceMasterData, evPrices, icePriceMasterData, icePrices, priceDataSourceConfig, products, vehiclePriceAuditLog.

## State Machines
catalog-scheduler: N/A — no status/state enums found in code.

## Business Rules
catalog-scheduler validation rules on DTO fields (from schema `validation`):
N/A — no declarative validation found; other rules not determinable without manual review.

## Key Classes and Functions
catalog-scheduler key classes:

| Class / Function | File | Responsibility |
|---|---|---|
| `merchandise-accessories-ingestion-job` | `src/functions/merchandise-accessories-ingestion-job.js:5` | scheduled job |
| `product-price-ingestion-job` | `src/functions/product-price-ingestion-job.js:6` | scheduled job |
| publish Unknown (name from `env:SERVICE_BUS_TOPIC_NAME`) | `src/product-price-ingestion-job/price-updates/price-updates.js:399` | azure-service-bus messaging |

## Sequence Details
catalog-scheduler: N/A — no server endpoint to sequence.

## Error Handling
catalog-scheduler error handling: no global exception handler found in code. Status mapping: Unknown.

## Configuration Details
catalog-scheduler behaviour-relevant config keys (names only; full list in OVERVIEW.md):
- `CATALOG_BASE_URL`: points to `core-commerce-platform-api-service`
- `PRICE_URL`: points to `price-engine-micro-service-backend`
- `env:CATALOG_BASE_URL`: base URL for outbound calls
- `env:MERCHANDISE_ACCESSORIES_BASE_URL`: base URL for outbound calls
- `env:PRICE_URL`: base URL for outbound calls
- `env:AUTHORIZATION_TOKEN_URL`: base URL for outbound calls
- `SERVICE_BUS_TOPIC_NAME`: publish entity name
- job `merchandise-accessories-ingestion-job` schedule from env:CRON_EXPRESSION_FOR_MERCHANDISE_ACCESSORIES_INGESTION_JOB
- job `product-price-ingestion-job` schedule from env:CRON_EXPRESSION_FOR_PRODUCT_PRICE_INGESTION_JOB

## Edge Cases
catalog-scheduler edge cases: N/A — not determinable from code without manual review.
