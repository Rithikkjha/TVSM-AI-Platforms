---
service_id: payment-service-4fa0ce
doc_type: lld
last_reviewed: 2026-10-11
---

# payment-service-4fa0ce — Low-Level Design

## Data Model
payment-service-4fa0ce entities from `data_access` items (0).
N/A — no data access in this repo.

## State Machines
payment-service-4fa0ce: N/A — no status/state enums found in code.

## Business Rules
payment-service-4fa0ce validation rules on DTO fields (from schema `validation`):
N/A — no declarative validation found; other rules not determinable without manual review.

## Key Classes and Functions
payment-service-4fa0ce key classes:

| Class / Function | File | Responsibility |
|---|---|---|
| subscribe cpg-juspay | `Functions/JusPayWebhooks.cs:23` | azure-service-bus messaging |

## Sequence Details
payment-service-4fa0ce: N/A — no server endpoint to sequence.

## Error Handling
payment-service-4fa0ce error handling: no global exception handler found in code. Status mapping: Unknown.

## Configuration Details
payment-service-4fa0ce behaviour-relevant config keys (names only; full list in OVERVIEW.md):
- `env:BookingService`: base URL for outbound calls
- `env:TVSConnectEVMandate`: base URL for outbound calls
- `env:TVSSparesAutoRefunds`: base URL for outbound calls
- `env:TokenUrl`: base URL for outbound calls
- `env:iceWebsiteShopify`: base URL for outbound calls

## Edge Cases
payment-service-4fa0ce edge cases: N/A — not determinable from code without manual review.
