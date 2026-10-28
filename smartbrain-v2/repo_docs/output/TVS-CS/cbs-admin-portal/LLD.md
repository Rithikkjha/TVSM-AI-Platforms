---
service_id: cbs-admin-portal
doc_type: lld
last_reviewed: 2026-10-11
---

# cbs-admin-portal — Low-Level Design

## Data Model
cbs-admin-portal entities from `data_access` items (0).
N/A — no data access in this repo.

## State Machines
cbs-admin-portal: N/A — no status/state enums found in code.

## Business Rules
cbs-admin-portal validation rules on DTO fields (from schema `validation`):
N/A — no declarative validation found; other rules not determinable without manual review.

## Key Classes and Functions
cbs-admin-portal key classes:

| Class / Function | File | Responsibility |
|---|---|---|

## Sequence Details
cbs-admin-portal: N/A — no server endpoint to sequence.

## Error Handling
cbs-admin-portal error handling: no global exception handler found in code. Status mapping: Unknown.

## Configuration Details
cbs-admin-portal behaviour-relevant config keys (names only; full list in OVERVIEW.md):
- `REACT_APP_API_URL`: points to `tvsmbe-mdp-bff`
- `REACT_APP_BOOKING_API_URL`: points to `booking-crud-services`
- `env:REACT_APP_API_URL`: base URL for outbound calls
- `env:REACT_APP_BOOKING_API_URL`: base URL for outbound calls

## Edge Cases
cbs-admin-portal edge cases: N/A — not determinable from code without manual review.
