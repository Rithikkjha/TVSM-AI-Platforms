# Service Documentation Template

**For: Engineering teams documenting their services for SmartBrain AI**

Please create one folder per service with the following markdown files. You don't need all files — fill in what you have. The more you provide, the better our AI can answer questions and map dependencies.

---

## Folder Structure

```
your-service-name/
├── API_SPEC.md        (endpoints + integrations)
├── HLD.md             (high-level architecture)
├── LLD.md             (low-level implementation details)
└── README.md          (quick overview)
```

---

## API_SPEC.md — What to Include

This is the most valuable file for dependency mapping. Please include:

### 1. Service Identity (required)

```markdown
## Service Identity

| Field | Value |
|-------|-------|
| Service Name | booking-crud-services |
| Repo | github.com/tvsmotorcompany/booking-crud-services |
| Team | Connected Commerce |
| Tech Lead | @firstname.lastname |
| Deployment | AKS / Azure Functions / App Service |
| Base URL (prod) | https://api.tvsmotor.com/bookings |

## Ownership & Contacts

| Role | Person / Team | Contact |
|------|---------------|---------|
| Product Owner | Rajesh Kumar | rajesh.kumar@tvsd.ai |
| Tech Lead | Arun Sharma | arun.sharma@tvsd.ai |
| Dev Team | Connected Commerce Backend | Teams: CC-Backend |
| On-call | Rotational | PagerDuty: #cc-oncall |
| Vendor (if external) | Vendor Company Name | vendor-contact@company.com |
```

### 2. Inbound — My API Endpoints + Who Calls Them (required)

List every endpoint YOUR service exposes AND who calls it:

```markdown
## My API Endpoints (Inbound)

| Method | Endpoint | Auth | Description | Called By |
|--------|----------|------|-------------|-----------|
| POST | /api/bookings | Bearer JWT | Create new booking | TVS Connect App, Admin Portal |
| GET | /api/bookings/:id | Bearer JWT | Get booking by ID | Core-Commerce-Platform, Admin Portal |
| POST | /api/bookings/refund-callback | Bearer JWT | Refund webhook | PaymentService |
| PUT | /api/bookings/:id/cancel | Bearer JWT | Cancel booking | TVS Connect App |
| GET | /api/bookings/user/:userId | Bearer JWT | List user bookings | TVS Connect App |
```

### 3. Outbound — Who This Service Calls (required)

List every service/system YOUR service calls:

```markdown
## Outbound (Who I Call)

| Target | Method | Endpoint/Topic | Purpose |
|--------|--------|----------------|---------|
| tvsm-auth | POST | /api/auth/validate | Token validation on every request |
| PaymentService | POST | /api/payments/initiate | Initiate payment for booking |
| async-communication-service | POST | /api/notifications/send | Send booking confirmation SMS/email |
| Azure Service Bus | PUBLISH | topic: booking-events | Emit BOOKING_CREATED event |
```

### 4. Service Bus / Event Topics (if applicable)

```markdown
## Events & Messaging

### Topics This Service Publishes To
| Topic/Queue | Events | Format |
|-------------|--------|--------|
| booking-events | BOOKING_CREATED, BOOKING_CANCELLED, BOOKING_UPDATED | JSON |
| payment-requests | PAYMENT_INITIATE | JSON |

### Topics This Service Subscribes To
| Topic/Queue | Events | Action |
|-------------|--------|--------|
| payment-events | PAYMENT_SUCCEEDED, PAYMENT_FAILED | Update booking status |
| inventory-updates | VEHICLE_AVAILABLE | Notify user |
```


### 5. External Integrations (if applicable)

```markdown
## External Integrations

| System | Type | Purpose | Auth |
|--------|------|---------|------|
| JusPay | Payment Gateway | Process payments | API key + HMAC |
| Azure AD | Identity | OAuth2 tokens | Client credentials |
| SendGrid | Email | Booking confirmations | API key |
| Firebase | Push Notifications | Mobile alerts | Service account |
```

### 6. Database & Storage (recommended)

```markdown
## Data Storage

| Store | Type | Purpose |
|-------|------|---------|
| booking-db | MSSQL | Primary booking data |
| Redis | Cache | Session + rate limiting |
| Azure Blob Storage | Files | Invoice PDFs |
```

---

## HLD.md — What to Include

High-level architecture overview:

- System purpose (what problem it solves)
- Architecture diagram description (data flow)
- Key design decisions
- Scalability approach
- Error handling strategy
- Deployment topology

---

## LLD.md — What to Include

Low-level implementation details:

- Code structure (folder layout, key modules)
- Database schema (tables, relationships)
- Key algorithms or business logic
- Configuration management
- Testing strategy

---

## README.md — What to Include

Quick start for new developers:

- What is this service (1-2 sentences)
- How to run locally
- Environment variables needed
- Key contacts / team ownership

---

## Priority Order (if you can only provide one file)

1. **API_SPEC.md** — Most valuable (dependencies + endpoints)
2. **HLD.md** — Second most valuable (architecture + decisions)
3. **README.md** — Useful for onboarding context
4. **LLD.md** — Deepest detail but least unique value for AI

---

## Tips for Best Results

- Include **all** downstream calls, even to infrastructure services like auth, notifications
- List **Service Bus topics** — these reveal hidden dependencies between services
- Mention **who calls you** — this helps map blast radius ("if this service goes down, what breaks?")
- Keep it up to date — outdated docs create wrong edges in the graph
