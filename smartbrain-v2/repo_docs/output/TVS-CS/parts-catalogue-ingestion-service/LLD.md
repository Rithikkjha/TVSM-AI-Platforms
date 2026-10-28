---
service_id: parts-catalogue-ingestion-service
doc_type: lld
last_reviewed: 2026-10-11
---

# parts-catalogue-ingestion-service — Low-Level Design

## Data Model
parts-catalogue-ingestion-service entities from `data_access` items (2).

Store access at `src/main/java/org/com/graph/config/NebulaGraphConfig.java:63`: database Unknown; collections -.

### HAS_ASSEMBLY
Entity `HAS_ASSEMBLY` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table HAS_ASSEMBLY; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### HAS_CATALOGUE
Entity `HAS_CATALOGUE` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table HAS_CATALOGUE; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### HAS_COLOR
Entity `HAS_COLOR` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table HAS_COLOR; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### HAS_MODEL
Entity `HAS_MODEL` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table HAS_MODEL; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### HAS_PART
Entity `HAS_PART` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table HAS_PART; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### HAS_VARIANT
Entity `HAS_VARIANT` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table HAS_VARIANT; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### HAS_VEHICLE
Entity `HAS_VEHICLE` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table HAS_VEHICLE; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### assembly
Entity `assembly` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table assembly; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### catalogue
Entity `catalogue` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table catalogue; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### color
Entity `color` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table color; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### model
Entity `model` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table model; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### part
Entity `part` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:501`; table part; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### product
Entity `product` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table product; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### variant
Entity `variant` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table variant; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

### vehicle
Entity `vehicle` defined in `src/main/java/org/com/graph/repository/CatalogueGraphRepository.java:569`; table vehicle; operation read.
Columns: Unknown (no fields extracted).
Relationships: Unknown.

Store access at `src/main/java/org/com/graph/config/OpenSearchConfig.java:59`: database Unknown; collections -.

## State Machines
parts-catalogue-ingestion-service: N/A — no status/state enums found in code.

## Business Rules
parts-catalogue-ingestion-service validation rules on DTO fields (from schema `validation`):
N/A — no declarative validation found; other rules not determinable without manual review.

## Key Classes and Functions
parts-catalogue-ingestion-service key classes:

| Class / Function | File | Responsibility |
|---|---|---|

## Sequence Details
parts-catalogue-ingestion-service: N/A — no server endpoint to sequence.

## Error Handling
parts-catalogue-ingestion-service error handling: no global exception handler found in code. Status mapping: Unknown. Retry evidence: `src/main/java/org/com/graph/config/ResilienceConfig.java:208`, `src/main/java/org/com/graph/config/CatalogueApiProperties.java:23`.

## Configuration Details
parts-catalogue-ingestion-service behaviour-relevant config keys (names only; full list in OVERVIEW.md):
- `config:catalogue.api.mdp.baseUrl`: base URL for outbound calls
- `config:catalogue.api.norton.baseUrl`: base URL for outbound calls
- `config:catalogue.api.price.baseUrl`: base URL for outbound calls
- `config:catalogue.api.mdp.tokenUrl`: base URL for outbound calls

## Edge Cases
parts-catalogue-ingestion-service edge cases: N/A — not determinable from code without manual review.
