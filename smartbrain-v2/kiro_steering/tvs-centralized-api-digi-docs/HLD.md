# CentralisedAPI — High Level Design

## System Purpose

CentralisedAPI (DIGI DMS) is the monolithic backend API that powers TVS Motor's Dealer Management System. It solves the problem of managing the complete vehicle service lifecycle at 5000+ dealerships — from customer walk-in/appointment through job card creation, labour/parts allocation, GST-compliant invoicing, and post-service feedback collection.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        Client Applications                        │
├──────────────┬───────────────┬───────────────┬───────────────────┤
│ Digi DMS App │ Admin Portal  │ TVS Connect   │ Self-Service JC   │
│ (Android)    │ (Web)         │ (Mobile)      │ (Customer)        │
└──────┬───────┴───────┬───────┴───────┬───────┴────────┬──────────┘
       │               │               │                │
       ▼               ▼               ▼                ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Azure API Management (APIM)                     │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    CentralisedAPI (IIS / App Service)             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Controllers (38)                                            │ │
│  │ Login | JobCard | Invoice | Customer | Master | Parts |     │ │
│  │ FRT | SMR | PSF | AMC | PDI | PickNDrop | Dashboard | ...  │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│  ┌──────────────────────────┴──────────────────────────────────┐ │
│  │ Business Layer (BL)                                         │ │
│  │ JobCardBL | InvoiceBL | GSTTaxProcessor | SMRBL | PsfBL |  │ │
│  │ AmcBL | CustomerBL | FRTMasterBL | PredictionBL | ...       │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│  ┌──────────────────────────┴──────────────────────────────────┐ │
│  │ Data Access Layer (DAL)                                     │ │
│  │ ADO.NET + Stored Procedures via DALHelper / DBFactoryHelper │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
       │         │         │         │         │         │
       ▼         ▼         ▼         ▼         ▼         ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│onlineDMS││DMS_SMR  ││ADVTVS   ││EMS_APP  ││WIP DB   ││PARTS_QR │
│(Primary)││(SMR)    ││(Offline)││(Portal) ││(Azure)  ││(QR Code)│
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
```

---

## Major Components

| Component | Responsibility |
|-----------|---------------|
| **Controllers (38)** | HTTP request handling, input validation, auth enforcement |
| **Authentication Layer** | Multi-scheme auth (JWT, UMS, Basic, SuperDMS, Audit, HeaderKey) |
| **Business Layer** | Core business logic, tax calculation, SMS dispatch |
| **Data Access Layer** | Stored procedure invocation via ADO.NET |
| **Webhook Services** | Outbound integrations (APIM token acquisition, notification, WIP, P360) |
| **Token Manager** | JWT generation/validation for 6+ token types |
| **OtelHelper** | OpenTelemetry traces + logs export |
| **GSTTaxProcessor** | GST tax calculation engine |

---

## Key Design Decisions

1. **Monolithic architecture** — Single deployable unit with 38 controllers covering all DMS domains
2. **Stored procedure-driven** — All database logic resides in SQL Server stored procedures; API layer is thin orchestration
3. **Multi-auth scheme** — Supports 6+ authentication mechanisms for different client types
4. **APIM gateway** — External service calls (Notification, WIP, PickNDrop) go through Azure APIM with OAuth2 client credentials
5. **In-memory cache** — UMS token validation results cached to reduce auth service calls
6. **Feature flags** — Business features toggleable via Web.config appSettings

---

## Deployment Topology

| Environment | Infrastructure | Database |
|-------------|---------------|----------|
| Dev | IIS Express / Azure App Service | 10.42.57.36 (onlineDMS_Staging) |
| UAT | Azure App Service | UAT SQL instances |
| Production | Azure App Service / IIS | Production SQL instances |

- **Secrets**: Azure Key Vault (DigiKeyVault, SendGrid, SuperDMS)
- **Observability**: OpenTelemetry → otel-gw-logs.tvsmotor.com → Grafana (Tempo + Loki)
- **Monitoring**: Application Insights

---

## Scalability Considerations

- Database connection pooling (Max Pool Size=15000 for primary connection)
- Extended command timeouts (40000ms) for heavy SP operations
- SMS delivery via multiple providers (Airtel IQ primary, Infobip fallback)
- Async/await throughout controller layer for I/O-bound operations

---

## Error Handling Strategy

- Controllers wrap logic in try/catch, returning structured `Output` objects with `statusCode` and `statusMessage`
- File-based logging via `LogGeneration.WriteToFile()` for exception tracking
- HTTP status codes: 200 (success), 401 (unauthorized), 500 (internal error)
- Token validation failures return 401 with `TokenOutput` message

---

## External Systems Integration

| System | Integration Pattern |
|--------|-------------------|
| SMS Providers (Airtel, Infobip) | Direct HTTP POST |
| APIM-protected services | OAuth2 client credentials → Bearer token → HTTP POST |
| Azure Key Vault | Azure Identity SDK (ClientSecretCredential) |
| SAP | SOAP/WCF Web Reference |
| P360 EV | GraphQL over HTTP |
| OTEL Collector | OTLP/Protobuf batch export |
