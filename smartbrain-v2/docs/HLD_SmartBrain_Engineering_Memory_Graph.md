# High-Level Design: SmartBrain - Engineering Memory Graph

---

## Overview

Engineering teams at TVS Motor Company operate across hundreds of microservices, dozens of Jira projects, and multiple Confluence spaces spanning multiple business units (D2W, IB, Norton, 3W, EV, ICE). Developers, PMs, and architects lack a single unified way to understand how services connect, who owns what, what documentation exists, and what the blast radius of a change might be.

**SmartBrain (Engineering Memory Graph)** is an AI-powered knowledge platform that ingests data from GitHub, Jira, Confluence, and code-derived steering files - builds a knowledge graph + vector index - and exposes it through MCP (Model Context Protocol) servers, a REST API, and a chatbot UI. It enables natural language queries like "What services depend on booking-crud-services?" or "How does dealer change flow work?" grounded in real engineering data.

---

## Tier Classification

**Tier 3: Non-Critical / Supporting Application**

- Does not serve production traffic
- Does not affect end-user-facing systems
- Internal developer productivity tool
- Outage = degraded developer experience, not business impact

---

## Background

### Why Now?

1. **Knowledge is siloed** - Service documentation lives in scattered Confluence pages, code comments, Jira tickets, and tribal knowledge. The org spans hundreds of repos across multiple business units (D2W, IB, Norton, 3W, EV, ICE, CPS). Onboarding a new engineer takes weeks.
2. **No dependency map** - There's no single source of truth for cross-service dependencies across the entire org. Impact analysis for changes is done manually.
3. **Scale problem** - The 42 repos piloted in Common Services are just one team. The full org has significantly more repos, Jira projects, and Confluence spaces spanning multiple teams (Website, DMS, EMS, Lead Service, MDP, Marketplace, Notifications, Auth, Payments, CPS/Norton, Parts Catalogue, Price Engine, etc.). Manual documentation cannot keep up.
4. **AI tooling maturity** - MCP (Model Context Protocol) enables IDE-native AI integrations. LLMs (GPT-4o) can now reason over graph data with acceptable accuracy.
5. **Kiro adoption** - Teams are using Kiro for development. SmartBrain provides Kiro with organizational context it can't get from a single repo.

### Learnings from Previous Systems

- Manual Confluence documentation goes stale within weeks
- Static architecture diagrams never match reality
- Developers prefer asking questions over reading docs
- Code-derived documentation (steering files) is more accurate than human-written docs

---

## Requirements

### Functional

| # | Requirement |
|---|------------|
| FR-1 | Ingest service metadata from GitHub repos across the entire org (starting with 42 in Common Services, scaling to hundreds) |
| FR-2 | Ingest tickets and epics from all Jira projects across business units |
| FR-3 | Ingest documentation pages from all Confluence spaces |
| FR-4 | Ingest code-derived steering files (product context, code structure, tech stack per service) |
| FR-5 | Build a knowledge graph with services, dependencies, teams, tickets, docs as nodes |
| FR-6 | Expose 4 MCP tools: `ask_question`, `search_graph`, `get_service_info`, `get_impact` |
| FR-7 | Provide a REST API (FastAPI) with endpoints: `/services/{name}`, `/impact`, `/search`, `/ask` |
| FR-8 | Provide a web-based chatbot UI for non-developer users |
| FR-9 | Support natural language Q&A grounded in graph + vector data (GraphRAG) |
| FR-10 | Detect data staleness and mark stale entities |
| FR-11 | Webhook-driven real-time updates from GitHub, Jira, Confluence |
| FR-12 | LLM-driven selective updates: LLM decides whether a webhook event represents a meaningful graph change or can be skipped |
| FR-13 | SOP enforcement: Define and enforce standards for CODEOWNERS, service manifests, and spec files in every repo |
| FR-14 | SOP enforcement for Jira: Mandatory component/service linking on tickets, standardized epic naming |
| FR-15 | SOP enforcement for Confluence: Mandatory service labels on architecture pages, standardized page templates |
| FR-16 | Automated webhook registration in all repos across the org |

### Non-Functional

| # | Requirement |
|---|------------|
| NFR-1 | Query latency: `/search` < 2s, `/ask` < 10s (includes LLM inference) |
| NFR-2 | Ingestion: Full re-sync within 30 minutes for all sources |
| NFR-3 | Availability: 99% uptime during business hours (internal tool) |
| NFR-4 | Security: API-key based auth, VPN-only access, no PII stored |
| NFR-5 | Scalability: Support hundreds of services, 100K+ tickets, 10K+ Confluence pages across all business units |
| NFR-6 | Idempotent ingestion: Re-running sync produces no duplicates (content-hash based dedup) |
| NFR-7 | Staleness detection: Entities not updated in 24h marked stale |

---

## Current Architecture (HLD)

Before SmartBrain, there is **no centralized system**. Knowledge is distributed across:

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   GitHub     │  │    Jira      │  │  Confluence  │  │  Tribal      │
│ (hundreds of │  │ (dozens of   │  │  (multiple   │  │  Knowledge   │
│   repos)     │  │  projects)   │  │   spaces)    │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
       │                 │                  │                  │
       └─────────────────┴──────────────────┴──────────────────┘
                                    │
                            Manual lookup by developers
                            (slow, incomplete, error-prone)
```

**Pain Points:**
- No dependency visibility → surprise outages on changes
- No impact analysis tooling
- Onboarding takes 2-4 weeks
- Architecture questions require finding the right person

---

## Proposed Architecture (HLD)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SOURCE SYSTEMS                                      │
│                                                                               │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐   ┌─────────────────┐      │
│  │  GitHub   │   │   Jira   │   │  Confluence  │   │  Kiro Steering  │      │
│  │(hundreds  │   │(dozens of│   │  (multiple   │   │ (42+ services   │      │
│  │ of repos) │   │projects) │   │   spaces)    │   │  and growing)   │      │
│  └─────┬─────┘   └────┬─────┘   └──────┬───────┘   └────────┬────────┘      │
│        │ webhooks      │ webhooks       │ webhooks           │ file scan      │
└────────┼───────────────┼────────────────┼────────────────────┼───────────────┘
         │               │                │                    │
         ▼               ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INGESTION LAYER (Python)                               │
│                                                                               │
│  ┌──────────────────┐  ┌────────────────────────┐  ┌──────────────────┐     │
│  │ Webhook Adapter   │  │  MCP Orchestrator      │  │ Steering Ingest  │     │
│  │ (sig verify)      │  │  (retry + scheduling)  │  │ (file parser)    │     │
│  └────────┬──────────┘  └───────────┬────────────┘  └────────┬─────────┘     │
│           │                         │                         │               │
│           ▼                         ▼                         ▼               │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │             Graph Extraction Engine                                    │    │
│  │  • Deterministic Parser (repos, PRs, tickets → structured nodes)      │    │
│  │  • LLM Extractor (Confluence pages → service mentions, relationships) │    │
│  │  • Embedding Generator (Azure OpenAI text-embedding-3-large, 3072d)   │    │
│  │  • Write Coordinator (idempotent upsert via source_id + text_hash)    │    │
│  └──────────────────────────┬─────────────────────────┬─────────────────┘    │
│                              │                         │                       │
└──────────────────────────────┼─────────────────────────┼──────────────────────┘
                               │                         │
                               ▼                         ▼
┌──────────────────────────────────────┐  ┌────────────────────────────────────┐
│         NEO4J (Graph Database)        │  │      QDRANT (Vector Database)       │
│                                       │  │                                     │
│  Nodes: Service, Ticket, Epic, PR,    │  │  Collection: memory_graph_entities  │
│         ConfluencePage, Person, Team,  │  │  Vectors: 3072-dim (cosine)         │
│         Repository                    │  │  Metadata: source_id, entity_type,  │
│                                       │  │            name, text               │
│  Edges: DEPENDS_ON, OWNED_BY,         │  │                                     │
│         LINKED_TO, DOCUMENTED_IN,     │  │  Purpose: Semantic similarity search │
│         CONTAINS, MODIFIES            │  │  "Find things by meaning"            │
│                                       │  │                                     │
│  Purpose: Structural relationships    │  └────────────────────────────────────┘
│  "Who connects to whom"               │
└───────────────────┬──────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          QUERY LAYER (FastAPI)                                │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │  GraphRAG Pipeline (/v1/ask)                                          │    │
│  │  1. Embed question (Azure OpenAI)                                     │    │
│  │  2. Vector search (Qdrant) → top-K relevant entities                  │    │
│  │  3. Graph expansion (Neo4j) → neighbors + relationships               │    │
│  │  4. LLM synthesis (GPT-4o) → grounded answer with citations           │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  Endpoints:                                                                   │
│  • GET  /v1/services/{name}        - Service details + deps + docs            │
│  • GET  /v1/services/{name}/impact - Blast radius (2-hop traversal)           │
│  • GET  /v1/search?q=&type=&limit= - Semantic vector search                  │
│  • POST /v1/ask                    - Natural language Q&A (GraphRAG)           │
│  • POST /webhooks/github|jira|confluence - Real-time ingestion triggers        │
│  • GET  /v1/health                 - Health + freshness check                  │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CONSUMER SURFACES                                       │
│                                                                               │
│  ┌─────────────────────┐  ┌────────────────────┐                            │
│  │  MCP Server          │  │  Web Chatbot UI    │                            │
│  │  (Engineering Memory │  │  (HTML/JS SPA)     │                            │
│  │   Graph)             │  │                    │                            │
│  │                      │  │  • Search           │                            │
│  │  Tools:              │  │  • Service detail   │                            │
│  │  • ask_question      │  │  • NL chatbot       │                            │
│  │  • search_graph      │  │  • Impact analysis  │                            │
│  │  • get_service_info  │  │                    │                            │
│  │  • get_impact        │  │  Served at :8000/ui │                            │
│  │                      │  │                    │                            │
│  │  Runs: stdio in IDE  │  └────────────────────┘                            │
│  └─────────────────────┘                                                     │
│                                                                               │
│  Consumers: Developers (Kiro IDE), PMs, Architects, New Joiners              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Technology | Role |
|-----------|-----------|------|
| **Ingestion Layer** | Python + MCP SDK | Pulls data from sources, extracts entities, writes to stores |
| **Neo4j** | Neo4j 5.x Community | Graph database - stores structural relationships |
| **Qdrant** | Qdrant v1.11 | Vector database - stores text embeddings for semantic search |
| **Azure OpenAI** | GPT-4o + text-embedding-3-large | LLM reasoning + embedding generation |
| **Query API** | FastAPI (Python) | REST API + GraphRAG pipeline |
| **MCP Server** | FastMCP (Python, stdio) | IDE integration - 4 tools with full GraphRAG access |
| **Web UI** | Plain HTML/JS/CSS | Browser-based chatbot + search |

### What is MCP (Model Context Protocol)?

MCP is an open protocol that allows AI assistants (Kiro, Claude, Cursor) to call external tools. Instead of copy-pasting context into chat, the AI automatically calls the right tool when needed.

**How it works in SmartBrain:**

```
Developer asks in Kiro: "What services depend on booking-crud-services?"
    │
    │ Kiro recognizes this needs engineering knowledge
    ▼
Kiro calls MCP tool: get_impact(name="booking-crud-services")
    │
    │ stdio JSON-RPC (MCP protocol)
    ▼
SmartBrain MCP Server receives the call
    │
    │ Queries Neo4j graph (2-hop traversal)
    ▼
Returns: ["MDP", "ATP", "DMS"] with hop distances
    │
    │ Back to Kiro via stdio
    ▼
Kiro presents the answer to the developer in natural language
```

### External Dependencies

**How it works in SmartBrain:**

| Dependency | Type | Purpose | Criticality |
|------------|------|---------|-------------|
| **Azure OpenAI** | External API | LLM (GPT-4o) + embeddings (text-embedding-3-large) | High - `/ask` endpoint won't work without it |
| **GitHub API** | External API | Repo metadata, PRs, contributors | Medium - ingestion only |
| **Jira API** | External API (Atlassian) | Tickets, epics | Medium - ingestion only |
| **Confluence API** | External API (Atlassian) | Documentation pages | Medium - ingestion only |
| **Neo4j** | Self-hosted (Docker/AKS) | Graph storage | High - all structural queries |
| **Qdrant** | Self-hosted (Docker/AKS) | Vector storage | High - all semantic search |

### Pros

- Single source of truth for the entire org's services and their relationships (not just 42 - all of them)
- Natural language queries - no need to know Cypher or specific APIs
- Auto-updating - webhooks + periodic sync keeps data fresh
- IDE-native - developers get answers without leaving their editor

### Cons

- Depends on Azure OpenAI for NL queries (cost + latency)
- Graph quality depends on data source quality (garbage in, garbage out)
- LLM answers may hallucinate if context is insufficient
- Initial setup requires ingestion of all repos across the org (phased rollout by team)

---

## Data Flow / Sequence Diagram

### How Data Ingestion Works (Step by Step)

#### Step 1: Data Collection from Sources

```
┌────────────┐   GitHub API    ┌──────────────────────┐
│  GitHub    │ ──────────────► │  Ingestion Pipeline   │
│            │  repos, PRs,    │                      │
│            │  CODEOWNERS     │  For each source:    │
└────────────┘                 │  1. Fetch raw data   │
                               │  2. Parse structured │
┌────────────┐   Jira API      │     entities         │
│   Jira     │ ──────────────► │  3. Extract          │
│            │  tickets,       │     relationships    │
│            │  epics          │  4. Compute          │
└────────────┘                 │     text_hash        │
                               │  5. Generate         │
┌────────────┐   Confluence    │     embedding        │
│ Confluence │ ──────────────► │  6. Write to both    │
│            │  pages,         │     stores           │
│            │  content        │                      │
└────────────┘                 └──────────┬───────────┘
                                          │
┌────────────┐   File read                │
│   Kiro     │ ──────────────►            │
│  Steering  │  product.md,              │
│  Files     │  structure.md,            │
│            │  tech.md                   │
└────────────┘                            │
                                          ▼
                               WRITES TO BOTH STORES
                               (always in sync)
```

#### Step 2: How the Graph (Neo4j) is Built

Every piece of data becomes a **node** with **relationships**:

```
Example: Ingesting "booking-crud-services" from GitHub + Steering

Node created:
  (:Service {
    source_id: "service:booking-crud-services",
    name: "booking-crud-services",
    description: "Centralized vehicle booking management",
    created_at: "2025-05-12T...",
    text_hash: "abc123..."       ← content fingerprint for dedup
  })

Relationship created (from steering file):
  (:Service {source_id: "service:booking-crud-services"})
    -[:DOCUMENTED_IN]→
  (:ConfluencePage {source_id: "steering:booking-crud-services:product"})

Relationship created (from code analysis):
  (:Service {source_id: "service:booking-crud-services"})
    -[:DEPENDS_ON {dependency_type: "service_bus"}]→
  (:Service {source_id: "service:DMS"})
```

**Graph grows organically:**
- Each repo ingested adds Service + Repository nodes
- Each Jira ticket ingested adds Ticket nodes linked to Services
- Each Confluence page adds ConfluencePage nodes linked to Services
- Each steering file adds rich dependency edges between Services

**Idempotency:** Every entity has a `source_id` + `text_hash`. If you re-ingest the same data, the hash matches → write is skipped. If content changed, hash differs → node is updated.

#### Step 3: How Vectors (Qdrant) are Created

Every text-heavy entity gets an **embedding** — a 3072-dimensional number array that captures its semantic meaning:

```
Input text: "Booking CRUD Services is a centralized booking management
             system that handles vehicle bookings across multiple platforms.
             It replaces previously siloed booking systems..."

                    ▼ Azure OpenAI text-embedding-3-large

Output vector: [0.0234, -0.0891, 0.0456, ..., 0.0123]  (3072 dimensions)

Stored in Qdrant:
  {
    id: "steering:booking-crud-services:product",
    vector: [0.0234, -0.0891, ...],           ← the embedding
    payload: {
      source_id: "steering:booking-crud-services:product",
      entity_type: "ConfluencePage",
      name: "Product Context: booking-crud-services",
      text: "Booking CRUD Services is a centralized..."  ← original text
    }
  }
```

**What gets embedded:**
- Steering file content (product context, code structure, tech stack)
- Confluence page content
- Jira ticket descriptions
- PR descriptions

**What does NOT get embedded (structure only):**
- Relationship types (stored only in Neo4j)
- Status fields, dates, IDs

#### Step 4: How Both Stores Work Together at Query Time (GraphRAG)

This is the magic — when a user asks a question, BOTH databases collaborate:

```
User question: "What services depend on booking-crud-services
                and how does the payment flow work?"

Step 1 — EMBED the question:
  question_vector = embed("What services depend on booking-crud-services...")
  → [0.0312, -0.0745, ...]

Step 2 — VECTOR SEARCH (Qdrant):
  "Find the top 10 entities whose content is semantically similar"
  Results:
    1. steering:booking-crud-services:product (score: 0.92)
    2. steering:PaymentService:product (score: 0.78)
    3. confluence:page:4338450436 "Booking Service API Contracts" (score: 0.74)
    4. steering:booking-crud-services:tech (score: 0.71)
    ...

Step 3 — GRAPH EXPANSION (Neo4j):
  "For each result above, traverse 2 hops in the graph to find context"
  
  Starting from service:booking-crud-services:
    → DEPENDS_ON → service:DMS (1 hop)
    → DEPENDS_ON → service:JusPay (1 hop)
    → DEPENDS_ON → service:CPG (1 hop)
    ← DEPENDS_ON ← service:MDP (1 hop, reverse = who depends on BS)
    ← DEPENDS_ON ← service:ATP (1 hop)

Step 4 — LLM SYNTHESIS (Azure OpenAI GPT-4o):
  Prompt: "Given this context from the knowledge graph:
           [vector search results + graph neighbors]
           Answer: What services depend on booking-crud-services
           and how does the payment flow work?"

  → LLM generates a grounded answer with citations

Step 5 — RETURN to user with citations
```

**Why both are needed:**

| Qdrant alone | Neo4j alone | Both together |
|---|---|---|
| Finds relevant text by meaning | Knows structure/dependencies | Finds relevant content AND its structural context |
| Can't tell you "who depends on whom" | Can't find things by meaning ("payment retry logic") | Natural language + relationship traversal |
| No relationship awareness | Requires knowing exact node names | Handles vague questions with precision |

#### How They Complement Each Other (Real Scenario)

```
User asks: "What documentation exists for booking service?"

Step 1: Qdrant vector search (by meaning)
  Returns 1 result: steering:booking-crud-services:product (score: 0.89)
  (Other 4 docs scored too low — "API Contracts" doesn't match "documentation" semantically)

Step 2: Neo4j graph expansion (by structure)
  Takes source_id from Step 1 → finds the Service node → traverses DOCUMENTED_IN edges
  Discovers ALL 5 linked docs:
    1. Product Context (Qdrant already found this)
    2. Code Structure (NEW — Qdrant missed it)
    3. Tech Stack (NEW)
    4. Booking Service API Contracts (NEW)
    5. Norton Env Setup (NEW)
  
  Neo4j also stores content_summary on each node → full text available

Step 3: Context assembly (token-budget aware)
  Priority: Qdrant results first (most relevant) → Neo4j discoveries fill remaining budget
  Deduplication: remove any Neo4j results already in Qdrant set

Step 4: GPT-4o synthesis
  Gets ALL 5 docs' content + structural info → answers comprehensively

RESULT: Even though Qdrant only matched 1 doc by meaning,
        Neo4j discovered 4 more by structure → answer covers everything.
```

This is already implemented in `src/query/ask.py` — the `get_entity_neighborhood()` call expands the graph 1-2 hops from each Qdrant hit, catching everything that's structurally connected but semantically distant from the question.

---

### Main Flow: Developer Asks a Question

```
Developer (Kiro)          MCP Server           Qdrant            Neo4j          Azure OpenAI
      │                       │                   │                 │                 │
      │  ask_question(Q)      │                   │                 │                 │
      │──────────────────────►│                   │                 │                 │
      │                       │  embed(Q)         │                 │                 │
      │                       │──────────────────────────────────────────────────────►│
      │                       │◄─────────────────────────────────────────────────────│
      │                       │  vector_search(Q_embedding, top_k=10)                 │
      │                       │──────────────────►│                 │                 │
      │                       │◄──────────────────│ matching entities                │
      │                       │                   │                 │                 │
      │                       │  expand_graph(entity_ids, hops=2)   │                 │
      │                       │────────────────────────────────────►│                 │
      │                       │◄────────────────────────────────────│ neighbors+rels  │
      │                       │                   │                 │                 │
      │                       │  synthesize(Q, context)             │                 │
      │                       │──────────────────────────────────────────────────────►│
      │                       │◄─────────────────────────────────────────────────────│
      │                       │                   │                 │  grounded answer │
      │  answer + citations   │                   │                 │                 │
      │◄──────────────────────│                   │                 │                 │
```

### Ingestion Flow: Webhook-Driven Update (with LLM Decision Gate)

```
GitHub/Jira/Confluence    Webhook Adapter    MCP Orchestrator     LLM Decision Gate     Extraction Engine    Neo4j + Qdrant
         │                      │                  │                      │                    │                    │
         │  webhook event       │                  │                      │                    │                    │
         │─────────────────────►│                  │                      │                    │                    │
         │                      │ verify signature │                      │                    │                    │
         │                      │─────────────────►│                      │                    │                    │
         │                      │                  │ fetch changed data   │                    │                    │
         │                      │                  │─────────────────────►│                    │                    │
         │                      │                  │                      │ "Is this a         │                    │
         │                      │                  │                      │  meaningful change  │                    │
         │                      │                  │                      │  to architecture,   │                    │
         │                      │                  │                      │  deps, or service   │                    │
         │                      │                  │                      │  boundaries?"       │                    │
         │                      │                  │                      │                    │                    │
         │                      │                  │                      │── YES ────────────►│                    │
         │                      │                  │                      │                    │ extract + embed    │
         │                      │                  │                      │                    │───────────────────►│
         │                      │                  │                      │                    │  upsert            │
         │                      │                  │                      │── NO (skip) ──────►│ (no graph update)  │
         │  HTTP 200            │                  │                      │                    │                    │
         │◄─────────────────────│                  │                      │                    │                    │
```

**LLM Decision Gate:** Not every commit needs to update the graph. The LLM evaluates the webhook payload and decides whether it represents a meaningful architectural change (new dependency, API contract change, service boundary shift, new service added) vs. a routine code change (bug fix, style change, test addition). Only meaningful changes trigger graph updates - this reduces noise and keeps data high-quality.

### Retry & Error Handling

| Scenario | Strategy |
|----------|----------|
| Azure OpenAI timeout | Exponential backoff (3 retries, 2s/4s/8s) |
| Neo4j connection lost | Auto-reconnect via async driver |
| Qdrant unavailable | `/search` returns 503, `/ask` falls back to graph-only |
| GitHub API rate limit | Backoff until rate limit resets (X-RateLimit-Reset header) |
| Jira/Confluence 429 | Retry after `Retry-After` header value |
| Ingestion duplicate | Skip (source_id + text_hash match → no write) |
| LLM hallucination | GraphRAG grounds answers in retrieved context; citations provided |

---

## Deployment & Rollout Plan

### Phase 1: POC (Completed - Local Machine)

- Ran on developer's local machine via Docker Compose
- Scope: 42 repos from Common Services team as proof of concept
- Validated: graph ingestion, MCP tooling, GraphRAG Q&A quality, chatbot UI
- Outcome: Proved the architecture works end-to-end

### Phase 2: Org-Wide Deployment (Next)

- Deploy to Azure Kubernetes Service (AKS) - internal VPN, org-wide access
- Onboard ALL teams and data sources:
  - All GitHub repos across all business units
  - All Jira projects across the org
  - All Confluence spaces
- Webhook integration for real-time updates
- MCP server distributed to all Kiro users
- Per-team API keys with usage quotas
- SSO integration via Azure AD

### Phase 3: Data Governance & Continuous Enrichment

> **Core Principle: The answers are only as good as the source data.** Our goal is to ensure the data ingested is of the highest quality - garbage in, garbage out. Every SOP below exists to maximize data quality at the source.

**GitHub SOPs:**
- Mandatory `CODEOWNERS` file in every repo - defines service ownership
- Mandatory service manifest file (`.service-manifest.yaml`) - declares service name, team, dependencies, API contracts
- Mandatory spec files (`.kiro/specs/`) - architecture decisions and design docs live with code
- Webhook auto-registered in every repo via GitHub App - triggers graph updates on PR merge

**Example: CODEOWNERS file (every repo root)**
```
# .github/CODEOWNERS
# Global owners
* @TVSM-CS/common-backend-services

# Service-specific ownership
/src/ @rithik-kumar @deepak-krishnan @kalpak-keskar
```

**Example: .service-manifest.yaml (every repo root)**
```yaml
service:
  name: booking-crud-services
  team: common-backend-services
  tier: 1  # mission-critical
  description: "Centralized vehicle booking management across all platforms"

ownership:
  product_owner: "kalpak.keskar@tvsmotor.com"
  tech_lead: "nivash@tvsmotor.com"
  squad: "booking-engine"

dependencies:
  http:
    - name: JusPay
      purpose: "Payment gateway refund API"
    - name: CPG
      purpose: "CCAvenue payment gateway refund API"
    - name: Lead Service
      purpose: "Lead ID generation for dealer changes"
  service_bus:
    publishes_to:
      - topic: booking-events
        consumers: [EMS, DMS, Lead System, Comms, ATP, Refund Service, Marketplace Service]
    subscribes_from:
      - topic: dms-events
        publisher: DMS
      - topic: atp-events
        publisher: ATP
      - topic: mdp-dealer-events
        publisher: MDP

tech_stack:
  runtime: Node.js 25.9
  framework: NestJS 11.x
  database: MSSQL (TypeORM)
  messaging: Azure Service Bus

api_contracts:
  swagger: "https://tvsswgrhub.tvsmotor.com/apis-docs/tvsmotorcompany/BookingService"
```

**What SmartBrain extracts from this manifest (deterministic, no LLM):**
- Service node → name, team, tier, description
- OWNED_BY relationship → team/squad
- DEPENDS_ON relationships → all declared dependencies with type (http/service_bus)
- DOCUMENTED_IN → links to swagger/API contracts

**Jira SOPs:**
- Standardized ticket linking: every ticket must be linked to a service/component via labels or components field
- Epic naming conventions: `[ServiceName] - Feature Description` - enables auto-linking to services
- Mandatory `component` field on tickets - maps to service nodes in the graph
- Sprint board hygiene: tickets must move to Done/Cancelled (not left in limbo) - prevents stale ticket data

**Confluence SOPs:**
- Standardized page structure for architecture docs: Overview → Dependencies → API Contracts → Deployment
- Mandatory `service:` label on every page that documents a service - enables auto-linking
- HLD template (this document format) enforced for all new feature designs
- Deprecation labels: pages marked `deprecated` or `archived` are excluded from graph ingestion

**LLM-Driven Selective Updates:**
- When a webhook fires, the LLM evaluates: "Does this change affect service architecture, dependencies, or boundaries?"
- YES → trigger graph extraction and update
- NO (routine code change, test fix, style change) → skip, don't pollute the graph
- This keeps the knowledge graph focused on structural truth, not noisy commit history

### Rollback Strategy

- Docker Compose: `docker compose down && docker compose up` with previous image tag
- AKS: Helm rollback to previous revision
- Data: Seed files provide point-in-time snapshots for full graph restore

---

## Metrics to be Tracked

### Application Metrics

| Metric | Alarm Threshold | Description |
|--------|----------------|-------------|
| `/ask` p95 latency | > 15s | GraphRAG end-to-end response time |
| `/search` p95 latency | > 3s | Vector search response time |
| Error rate (5xx) | > 5% | API errors |
| Neo4j connection pool utilization | > 80% | Database pressure |
| Azure OpenAI token usage/day | > 100K tokens | Cost monitoring |
| Ingestion sync duration | > 60 min | Full re-sync taking too long |
| Stale entity percentage | > 30% | Data freshness degradation |

### Business Metrics

| Metric | Description |
|--------|-------------|
| Questions asked/day | Platform adoption |
| Unique users/week | Breadth of usage |
| Mean time to answer (onboarding questions) | Developer productivity |
| Services with complete steering docs | Knowledge coverage |

### Data Analytics / Data Engineering

| Table | Enabled | Description |
|-------|---------|-------------|
| `audit_log` (Neo4j property) | Yes | All ingestion events with timestamps |
| `query_log` (application log) | Yes | All API queries with latency + user |
| Data lake export | Not yet | Future: export graph snapshots to Azure Data Lake for BI |

---

## Alternatives Considered

### Option A: Pure Confluence + Manual Documentation

| | |
|---|---|
| **Pros** | Zero engineering effort, everyone already uses Confluence, searchable |
| **Cons** | Goes stale immediately, no dependency graph, no impact analysis, no NL queries, relies on humans to update |

**Rejected because:** This is the current state - it doesn't work. Documentation becomes outdated within weeks. No one maintains it consistently.

### Option B: Custom Graph DB + Traditional Search (No LLM)

| | |
|---|---|
| **Pros** | No Azure OpenAI dependency, no LLM cost, faster responses, deterministic |
| **Cons** | Users must learn query syntax, no natural language, limited to exact matches, poor UX for non-developers |

**Rejected because:** The primary value is natural language access. Without LLM, adoption drops significantly - developers won't learn another query language. PMs and architects would be completely excluded.

---

## Risks (If Any)

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Poor source data quality** | Wrong/incomplete answers - THE #1 RISK | SOPs for Git (CODEOWNERS, manifests), Jira (component linking, naming), Confluence (templates, labels). Data quality audits. LLM filtering of noise. |
| Azure OpenAI cost escalation | High cost if heavily adopted | Token budget caps, caching frequent queries |
| LLM hallucination | Wrong answers erode trust | GraphRAG grounding, citations, confidence thresholds |
| Data staleness | Stale data → wrong answers | Webhook-driven updates + 6h full re-sync + staleness indicators |
| Neo4j/Qdrant data loss | Full rebuild required | Seed export/import scripts, scheduled snapshots |
| GitHub/Jira API rate limits | Ingestion throttled | Backoff + prioritized incremental sync |
| MCP protocol changes | Breaking changes in SDK | Pin MCP SDK version, update on schedule |
| Low adoption | Effort wasted | Start with highest-value team (Common Services), expand based on proven value |

---

## Appendix

### Glossary

| Term | Definition |
|------|-----------|
| **MCP** | Model Context Protocol - open standard for AI tool integration (stdio JSON-RPC) |
| **GraphRAG** | Retrieval-Augmented Generation using graph traversal + vector search as context |
| **Steering Files** | Code-derived documentation: product context, code structure, tech stack per service |
| **Neo4j** | Graph database storing nodes (services, tickets, docs) and edges (dependencies, ownership) |
| **Qdrant** | Vector database storing text embeddings for semantic similarity search |
| **FastMCP** | Python SDK for building MCP servers (by Anthropic) |
| **Kiro** | AI-powered IDE by AWS that supports MCP tool integration |
| **Idempotent Ingestion** | Re-running sync doesn't create duplicates (uses content hash dedup) |
| **Staleness** | Entity not updated within threshold (24h) - indicates potentially outdated data |
| **Blast Radius** | Set of services transitively affected if a given service goes down |
| **Fire-and-Forget** | Async operation where caller doesn't wait for completion |

### Acronyms

| Acronym | Full Form |
|---------|-----------|
| MCP | Model Context Protocol |
| HLD | High-Level Design |
| AKS | Azure Kubernetes Service |
| NL | Natural Language |
| LLM | Large Language Model |
| RAG | Retrieval-Augmented Generation |
| SPA | Single Page Application |
| VPN | Virtual Private Network |
| SSO | Single Sign-On |
| API | Application Programming Interface |
| SDK | Software Development Kit |
| CI/CD | Continuous Integration / Continuous Delivery |
