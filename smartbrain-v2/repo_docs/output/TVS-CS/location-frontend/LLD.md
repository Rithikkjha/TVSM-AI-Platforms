---
service_id: location-frontend
doc_type: lld
last_reviewed: 2026-10-11
---

# location-frontend — Low-Level Design

## Data Model
location-frontend entities from `data_access` items (0).
N/A — no data access in this repo.

## State Machines
location-frontend: N/A — no status/state enums found in code.

## Business Rules
location-frontend validation rules on DTO fields (from schema `validation`):
N/A — no declarative validation found; other rules not determinable without manual review.

## Key Classes and Functions
location-frontend key classes:

| Class / Function | File | Responsibility |
|---|---|---|

## Sequence Details
location-frontend: N/A — no server endpoint to sequence.

## Error Handling
location-frontend error handling: no global exception handler found in code. Status mapping: Unknown.

## Configuration Details
location-frontend behaviour-relevant config keys (names only; full list in OVERVIEW.md):
- `REACT_APP_ADMIN_BASE_URL`: points to `tvsmbe-location`
- `REACT_APP_ADMIN_IB_BASE_URL`: points to `tvsmbe-location`
- `REACT_APP_DEALERWEB_BASE_URL`: points to `tvsmbe-location`
- `REACT_APP_DEALER_BASE_URL`: points to `tvsmbe-location`
- `REACT_APP_DEALER_LOCATER_BASE_URL`: points to `tvsmbe-location`
- `env:REACT_APP_ADMIN_BASE_URL`: base URL for outbound calls
- `env:REACT_APP_ADMIN_IB_BASE_URL`: base URL for outbound calls
- `env:REACT_APP_DEALERWEB_BASE_URL`: base URL for outbound calls
- `env:REACT_APP_DEALER_BASE_URL`: base URL for outbound calls
- `env:REACT_APP_DEALER_LOCATER_BASE_URL`: base URL for outbound calls

## Edge Cases
location-frontend edge cases: N/A — not determinable from code without manual review.
