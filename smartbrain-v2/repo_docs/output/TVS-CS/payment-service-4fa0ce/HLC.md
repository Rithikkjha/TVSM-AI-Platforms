---
service_id: payment-service-4fa0ce
doc_type: hlc
last_reviewed: 2026-10-11
---

# payment-service-4fa0ce — High-Level Code

## Application Overview
payment-service-4fa0ce (`PaymentService`) is a `function` codebase; stacks dotnet; head `a6f4c938975c2caa7c2d234177076c3defd1416b`.
Entry points: `Program.cs`.

## Module Summary
payment-service-4fa0ce modules (subprojects from repo classification):

| Module | Path | Responsibility |
|---|---|---|
| . | `.` | function-app: 0 endpoints, 5 outbound calls, 1 messaging, 0 data-access |
| PaymentService.Tests | `PaymentService.Tests` | test-suite: 0 endpoints, 0 outbound calls, 0 messaging, 0 data-access |

## Folder Structure
payment-service-4fa0ce top-level folders (3 levels):

```
PaymentService/
├── Constants/
├── Enums/
├── Functions/
├── Helpers/
├── Mappers/
├── Models/
├── PaymentService.Tests/
├── Properties/
│   ├── ServiceDependencies/
│   │   ├── tvsmazcmnsvcftaprd01-justpay-api - Web Deploy/
│   │   ├── tvsmazcmnsvcftauat01 - Web Deploy/
├── payment-service-docs/
```

## Core Workflows in Code
payment-service-4fa0ce workflows traced from inventory: handler file → outbound/messaging/data access in the same module.

### Consumer cpg-juspay
1. `Functions/JusPayWebhooks.cs:23` handles messages (azure-service-bus, trigger function-trigger).

## Integration Clients
payment-service-4fa0ce outbound client wiring:

| Target service_id | Client class / file | Config key |
|---|---|---|
| Unknown | `Functions/JusPayWebhooks.cs` | env:BookingService |
| Unknown | `Functions/JusPayWebhooks.cs` | env:TVSConnectEVMandate |
| Unknown | `Functions/JusPayWebhooks.cs` | env:TVSSparesAutoRefunds |
| Unknown | `Functions/JusPayWebhooks.cs` | env:TokenUrl |
| Unknown | `Functions/JusPayWebhooks.cs` | env:iceWebsiteShopify |
| azure-service-bus subscribe cpg-juspay | `Functions/JusPayWebhooks.cs:23` | literal |

## Cross-Cutting Concerns
payment-service-4fa0ce cross-cutting code:
- Auth: none found
- Error handling: none found
- Validation: 0 validated DTO fields (see LLD.md Business Rules)
- Caching/logging libs: none found

## Build and Test
payment-service-4fa0ce build/test commands from manifests:
- .NET: `dotnet build` / `dotnet test` (`PaymentService.sln`)
- CI pipelines: none found
