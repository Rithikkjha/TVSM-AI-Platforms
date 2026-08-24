# Job Card Service

A microservice that manages creation, tracking, and updating of job cards (work orders) for vehicle services at TVS Motor dealerships. Provides an omnichannel interface for streamlining service workflow, task allocation, and customer communication.

## Quick Start

### Prerequisites
- .NET 9.0 SDK
- SQL Server access (Dev/UAT instances)
- Docker (for containerized runs)
- Azure Key Vault access (for secrets in deployed environments)

### Run Locally
1. Clone the repo
2. Update `src/Jobcard.API/appsettings.json` with your DB connection strings
3. Run:
```bash
cd src/Jobcard.API
dotnet run
```
4. Swagger UI available at: `http://localhost:5000/swagger/index.html`

### Environment Variables
| Variable | Purpose | Default |
|----------|---------|---------|
| ConnectionStrings__ReminderDbConnection | Reminder/Leads DB | (see appsettings.json) |
| ConnectionStrings__JobcardDbConnection | Primary Job Card DB | (see appsettings.json) |
| OTEL_SERVICE_NAME | OpenTelemetry service name | job-card-service |
| OTEL_EXPORTER_OTLP_ENDPOINT | OTLP collector endpoint | http://otel-gw-logs.tvsmotor.com |
| OTEL_EXPORTER_ENABLED | Enable/disable OTLP export | true |
| DEPLOYMENT_ENVIRONMENT | Environment label | dev |

### Build
```bash
dotnet build Jobcard.sln
```

### Docker Build
```bash
docker build -t job-card-service .
docker run -p 8080:8080 job-card-service
```

### Deployment
- **Platform**: AKS (Azure Kubernetes Service)
- **CI/CD**: Azure DevOps Pipelines (build → image scan → deploy)
- **Environments**: Dev → UAT (manual approval) → Prod (manual approval)
- **Helm chart**: `job-card`

### Key Contacts / Ownership

| Role | Contact |
|------|---------|
| Dev Team | Connected Commerce Backend |
| Tech Contact | sapna.bhandari@tvsmotor.com |
| Prod Approval | Dushyant.Satyapal@tvsmotor.com, Bipin.Chandra@tvsmotor.com |

### Swagger Docs
- Hub: https://tvsswgrhub.tvsmotor.com/apis/tvsmotorcompany/job-card-service/1.0.1
- Confluence: https://tvsmotorcompany.atlassian.net/wiki/spaces/DESIGN/pages/3823567352
