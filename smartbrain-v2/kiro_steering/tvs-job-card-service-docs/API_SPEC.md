# Job Card Service — API Specification

## Service Identity

| Field | Value |
|-------|-------|
| Service Name | job-card-service |
| Repo | github.com/tvsmotorcompany/job-card-service |
| Team | Connected Commerce Backend |
| Tech Lead | sapna.bhandari@tvsmotor.com |
| Deployment | AKS (Azure Kubernetes Service) |
| Base URL (dev) | https://dev-api.tvsmotor.net/job-card-service |
| Base URL (internal) | https://dev-cmnsvc-ingress.tvsmotor.net/job-card |
| Framework | ASP.NET Core 9.0 |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Tech Contact | Sapna Bhandari | sapna.bhandari@tvsmotor.com |
| Prod Approval | Dushyant Satyapal | Dushyant.Satyapal@tvsmotor.com |
| Prod Approval | Bipin Chandra | Bipin.Chandra@tvsmotor.com |
| Dev Team | Connected Commerce Backend | Suraj.Ray@tvsmotor.com |

---

## My API Endpoints (Inbound)

### Job Card Operations

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | /api/maintenance/due/fetch/{frameNo} | None (stub) | Get next service due/lead for vehicle | Digi DMS App, TVS Connect |
| GET | /api/service/history/fetch/{frameNo} | None (stub) | Get job card history by frame (filters: dealerId, branchId, jobcardId, status) | Digi DMS App, CentralisedAPI |
| GET | /api/service/history/detail/fetch/{dealerId}/{branchId}/{jobcardId} | None (stub) | Get detailed service history (complaints, parts, labour, estimates) | Digi DMS App |
| GET | /api/service/invoice/fetch/{dealerId}/{branchId}/{jobcardId} | None (stub) | Get job card invoice | Digi DMS App |
| GET | /api/service/health/{dealerId} | None (stub) | Health check / dealer validation | Monitoring, CentralisedAPI |
| GET | /api/jobcard/configurations/fetch/{frameNo}?odometerReading= | None (stub) | Get job types and convenience modes | Digi DMS App |

### FRT Parts

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | /api/service/frt/parts/fetch/{modelId}/{dealerId}/{branchId}?isPmlEnabled= | None (stub) | Fetch FRT parts by vehicle model | Digi DMS App |

### Auto Labor

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | /api/service/frt/autoLabor/create | None (stub) | Generate auto-labour preview from complaints | Digi DMS App |
| GET | /api/master/labour/fetch | None (stub) | Get master labour data (categories, FRT, SAC, aggregates) | Digi DMS App |
| GET | /api/master/vehicle/fetch?dealerId= | None (stub) | Get vehicle variances for a dealer | Digi DMS App |

### Labour (FRT Manual)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | /api/labour/frt/fetch/{dealerId}/{branchId}/{labourTypes} | None (stub) | Fetch FRT manual labours | Digi DMS App |
| POST | /api/labour/frt/create | None (stub) | Create a new labour entry | Digi DMS App |
| PUT | /api/labour/frt/update | None (stub) | Update existing labour entry | Digi DMS App |
| POST | /api/service/labour/{laborCode}/issueMode/{issueModeId}/check | None (stub) | Validate labour against issue mode | Digi DMS App |
| POST | /api/labour/pml/fetch | None (stub) | Fetch PML labour preview | Digi DMS App |

---

## Outbound (Who I Call)

| Target | Method | Endpoint/Purpose | Auth |
|--------|--------|------------------|------|
| Azure Key Vault | SDK | Secret management (connection strings in AKS) | Azure Identity |
| OTEL Gateway | POST | http://otel-gw-logs.tvsmotor.com/v1/traces, /v1/logs | None |

> Note: This service is primarily database-driven with no explicit outbound calls to other TVS microservices currently in code. Future integrations may use RestSharp (referenced in Infrastructure project).

---

## External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| Azure Key Vault | Secret Store | Connection strings + secrets in AKS | Azure Identity SDK |
| OpenTelemetry Collector | Observability | Traces + Logs export (OTLP/Protobuf) | None |

---

## Database & Storage

| Store | Type | Purpose | Connection Key |
|-------|------|---------|----------------|
| onlineDMS_Staging | MSSQL (SQL Server) | Primary job card data — dealers, branches, customers, vehicles, job cards, parts, labours, invoices, FRT | JobcardDbConnection |
| DMS_SMR_Trans_UAT | MSSQL (SQL Server) | Reminder/leads data — service due dates, dealer-vehicle mappings | ReminderDbConnection |

---

## Rate Limiting

| Setting | Value |
|---------|-------|
| Type | Fixed Window per IP |
| Permit Limit | 25 requests |
| Window | 1 second |
| Rejection | HTTP 429 Too Many Requests |
