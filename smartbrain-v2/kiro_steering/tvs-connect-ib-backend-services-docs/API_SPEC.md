# API_SPEC.md — TVS Connect AI Assistant Service

---

## Service Identity

| Field | Value |
|-------|-------|
| Service Name | tvs-connect-ai-assistant |
| Repo | (New module within tvs-connect-web-api) |
| Team | Connected Services - ISSM |
| Tech Lead | Lakshmi Narayana Neduri |
| Deployment | Azure App Service (same host as tvs-connect-web-api) |
| Base URL (Dev) | https://dev-api.tvsmotor.net/connect |
| Base URL (UAT) | https://uat-api.tvsmotor.net/connect |
| Base URL (Prod) | https://apim.tvsmotor.com/connect |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Product Owner | [To be filled] | - |
| Tech Lead | Lakshmi Narayana Neduri | lakshmi.narayana@tvsd.ai |
| Dev Team | ISSM Backend | Teams: ISSM-Backend |
| On-call | Rotational | PagerDuty: #issm-oncall |
| AI/ML Support | [To be filled] | - |

---

## My API Endpoints (Inbound)

### Chat Endpoints

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | /api/ai/chat | Bearer JWT | Send message to AI, get response | TVS Connect App |
| GET | /api/ai/chat/stream | Bearer JWT + SSE | Stream AI response real-time | TVS Connect App |
| GET | /api/ai/chat/history | Bearer JWT | Get conversation history | TVS Connect App |
| DELETE | /api/ai/chat/history | Bearer JWT | Clear conversation history | TVS Connect App |
| POST | /api/ai/chat/rate | Bearer JWT | Rate response (thumbs up/down) | TVS Connect App |

### Insight Endpoints

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | /api/ai/insights/ride | Bearer JWT | Get ride analytics and score | TVS Connect App |
| GET | /api/ai/insights/ride/weekly | Bearer JWT | Get weekly ride summary | TVS Connect App, Notification WebJob |
| GET | /api/ai/insights/vehicle | Bearer JWT | Get vehicle health score | TVS Connect App |
| GET | /api/ai/insights/vehicle/alerts | Bearer JWT | Get maintenance alerts | TVS Connect App, Nudge Service |

### Trip Planning Endpoints

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | /api/ai/trip/plan | Bearer JWT | Generate AI trip plan | TVS Connect App |
| GET | /api/ai/trip/saved | Bearer JWT | Get saved trip plans | TVS Connect App |
| DELETE | /api/ai/trip/saved/{tripId} | Bearer JWT | Delete saved trip | TVS Connect App |

### Configuration & Admin

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| GET | /api/ai/config | Bearer JWT | Get feature config and usage quota | TVS Connect App |
| GET | /api/ai/admin/usage | Admin Auth | Token usage dashboard | Admin Portal |
| POST | /api/ai/admin/prompts | Admin Auth | Update prompt templates | Admin Portal |
| GET | /api/ai/health | None | Health check | Azure Monitor |

---

## Outbound (Who I Call)

### Internal Services

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| TVS Connect API (Ride module) | GET | Internal service call | Fetch ride history and cumulative stats |
| TVS Connect API (Vehicle module) | GET | Internal service call | Fetch vehicle details and config |
| TVS Connect API (Notification) | POST | Internal service call | Send proactive insight notifications |
| P360 / TrakNTell | GET | /api/v1/vehicle/status | Real-time telemetry (SOC, DTE, location) |
| P360 / TrakNTell | GET | /api/v1/vehicle/diagnostics | DTC codes and diagnostic data |

### External AI/ML Services

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| OpenAI API | POST | /v1/chat/completions | Primary LLM inference |
| OpenAI API | POST | /v1/embeddings | Semantic cache matching (future) |
| Google Gemini API | POST | /v1/models/gemini-pro:generateContent | Fallback LLM |

### External Data Services

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| OpenWeather API | GET | /data/2.5/forecast | Weather for trip planning |
| Google Maps Directions | GET | /maps/api/directions/json | Route planning |
| Google Maps Places | GET | /maps/api/place/nearbysearch/json | Fuel/charging stations, POI |

---

## Events & Messaging

### Topics This Service Publishes To

| Topic/Queue | Events | Format |
|-------------|--------|--------|
| ai-insights-events | RIDE_INSIGHT_GENERATED, VEHICLE_ALERT_GENERATED | JSON |
| ai-usage-events | TOKEN_LIMIT_REACHED, DAILY_USAGE_REPORT | JSON |

### Topics This Service Subscribes To

| Topic/Queue | Events | Action |
|-------------|--------|--------|
| ride-completed-events | RIDE_COMPLETED | Compute ride score for completed ride |
| vehicle-telemetry-events | TELEMETRY_UPDATE | Update vehicle health on significant changes |
| user-onboarding-events | VEHICLE_ONBOARDED | Initialize AI context for new vehicle |

---

## External Integrations

| System | Type | Purpose | Auth | Rate Limit |
|--------|------|---------|------|------------|
| OpenAI | LLM Provider | Chat completions | API Key (Bearer) | 10,000 RPM |
| Google Gemini | LLM Fallback | Backup inference | API Key | 1000 RPM |
| OpenWeather | Weather | Trip forecast | API Key (param) | 60/min |
| Google Maps | Routing + Places | Routes, stops | API Key (param) | 50 QPS |
| Azure Key Vault | Secrets | API key storage | Managed Identity | N/A |
| Application Insights | Monitoring | Logging, metrics | Conn String | N/A |

---

## Data Storage

| Store | Type | Purpose | New/Existing |
|-------|------|---------|--------------|
| TVS Connect SQL DB | MSSQL | Sessions, messages, usage, prompts, insights | New tables in existing DB |
| Azure Redis Cache | Cache | Response caching, rate limiting | New (recommended) |
| Azure Blob Storage | Files | Prompt templates, trip exports | New container |

### New Tables

| Table | Purpose | Est. Growth |
|-------|---------|-------------|
| AI_ChatSession | Chat sessions | ~1M rows/year |
| AI_ChatMessage | Messages (user + AI) | ~10M rows/year |
| AI_TokenUsage | Daily token consumption | ~5M rows/year |
| AI_PromptVersion | Versioned prompts | ~100 rows |
| AI_RideInsight | Cached ride insights | ~5M rows/year |
| AI_TripPlan | Saved trip plans | ~500K rows/year |

---

## Rate Limiting

| Endpoint | Limit | Window | On Exceed |
|----------|-------|--------|-----------|
| POST /api/ai/chat | 30 req | Per min per user | 429 |
| GET /api/ai/insights/* | 60 req | Per min per user | 429 |
| POST /api/ai/trip/plan | 10 req | Per hour per user | 429 |
| Token budget | 5,000 tokens | Per day per user | Soft block |
| Token budget | 100,000 tokens | Per month per user | Soft block |

---

## Disaster Recovery & Fallback

| Scenario | Fallback |
|----------|----------|
| OpenAI down | Route to Gemini |
| Both LLMs down | Canned responses from local DB |
| High latency (>5s) | Partial cached response |
| Token quota exceeded | Friendly limit message |
| Database down | Error response, log to App Insights |
| Redis down | Direct LLM call (higher cost) |

---

*Document Owner: Lakshmi Narayana Neduri*
*Last Updated: 2026-06-17*
*Status: DRAFT*


---

## Document Ownership

| Role | Person / Team | Contact |
|------|---------------|---------|
| **Project Manager** | Smaranika Tripathy | smaranika.tripathy@tvsmotor.com |
| **Product Owner** | ISSM Team / Malavika | malavika@tvsmotor.com |
| **Owner (iOS)** | Sumit Prajapat | sumit.prajapat@tvsmotor.com |
| **Owner (Android)** | Lakshmi Narayana | lakshmi.narayana@tvsmotor.com |
| **DevOps** | Raju Nimse | raju.nimse@tvsmotor.com |
| **Contact Person (Backend)** | Raju Nimse | raju.nimse@tvsmotor.com |
