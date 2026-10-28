---
service_id: <service-id>
doc_type: hlc
last_reviewed: YYYY-MM-DD
---

# <Service Name> — High-Level Code

## Application Overview
What the <service-id> codebase is, in code terms (entry points, app type).

## Module Summary
| Module | Path | Responsibility |
|---|---|---|
| | | |

## Folder Structure
```
<repo-root>/
├── src/
└── ...
```

## Core Workflows in Code
For each main workflow: entry point (controller/handler) → services → repositories → outbound calls.

### <Workflow name>
1. `Controller.Method` receives …
2. `Service.Method` validates …
3. Calls `payment-service` via `PaymentClient.Initiate`

## Integration Clients
Where each outbound dependency is wired in the code.
| Target service_id | Client class / file | Config key |
|---|---|---|
| | | |

## Cross-Cutting Concerns
Auth middleware, logging, error handling, validation, caching.

## Build and Test
How to build, test commands, coverage notes.
