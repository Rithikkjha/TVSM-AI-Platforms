# Orchestrated Pipeline Design — Primitives + Query Routing

## Motivation

Currently every question goes through the same monolithic pipeline (embed → hybrid → rerank → graph expand → LLM → answer). This works but:

- Flow questions ("how does X work end-to-end across services?") get incomplete answers because retrieval is global, not per-service
- Structural questions ("what depends on X?") waste 3-5s on LLM when the graph already has the answer
- Single-service questions ("tell me about booking-crud") don't need reranking across all services
- MCP clients (Kiro) can't do fine-grained retrieval — they only get synthesized answers

The fix: classify the query, route to the right strategy, and expose primitives that both the server orchestrator (UI) and external agents (MCP) can use.

---

## Query Types and Routing

The orchestrated pipeline classifies each question into one of these types:

| Type | Example questions | Strategy |
|---|---|---|
| **structural** | "What depends on booking-crud?", "Who owns payment-service?", "What's the blast radius of tvsm-auth?" | Direct graph query → format as text. No embedding, no LLM. Fastest path (~100ms). |
| **single_service** | "Tell me about booking-crud-services", "What's the tech stack of payment-service?", "What API endpoints does notification-service have?" | Filtered retrieval: search only chunks from that service → LLM synthesizes. Focused, fast. |
| **cross_service_flow** | "How does dealer booking work end-to-end?", "What's the cancellation flow across services?", "How does a payment get initiated from a booking?" | Graph chain → per-service retrieval → flow-specific LLM synthesis. Multi-step. |
| **general** | "How does authentication work?", "What is a dealer code?", "Explain the notification retry logic" | Standard hybrid retrieval → rerank → LLM. Current monolithic path. |

### Classification logic (heuristic, no LLM)

```
if mentions_known_service AND asks_about_dependencies/ownership/impact:
    → structural
elif mentions_known_service AND asks_what_is/describe/detail:
    → single_service  
elif contains("end to end", "flow", "across services", "step by step", "journey", "how does X work"):
    → cross_service_flow
else:
    → general
```

Can upgrade to LLM-based classification later. Heuristic is fast and free.

---

## How Each Route Works

### Route: structural

```
Question: "What depends on booking-crud-services?"

1. Parse service name from question
2. Neo4j query: MATCH (s)-[r:DEPENDS_ON]->(target {name: $name}) RETURN s, r
3. Format as structured response (no LLM needed)
4. Return: { answer: "3 services depend on booking-crud-services: MDP, ATP, DMS", citations: [] }

Time: ~100ms
Cost: $0 (no LLM, no embedding)
```

### Route: single_service

```
Question: "Tell me about payment-service"

1. Parse service name from question
2. search(query="payment-service overview", repo_filter="payment-service", limit=5)
   → Gets: product.md chunk, tech.md chunk, structure.md chunk (all from payment-service only)
3. LLM synthesis with standard prompt
4. Return: answer + citations

Time: ~2-3s
Advantage: No noise from other services' chunks. 100% of context budget used for the right service.
```

### Route: cross_service_flow

```
Question: "How does the dealer booking flow work end-to-end?"

1. Extract primary service: "booking-crud-services"
2. get_service_chain("booking-crud-services", hops=2)
   → [booking-crud-services, payment-service, notification-service, dealer-master]
3. For each service in chain:
     search(query="dealer booking", repo_filter=svc, limit=2)
   → 1-2 relevant chunks per service
4. Assemble context ordered by service chain position:
     [ref:1] booking-crud-services: "Booking creation and lifecycle..."
     [ref:2] payment-service: "Payment initiation after booking..."
     [ref:3] notification-service: "Booking confirmation notification..."
     [ref:4] dealer-master: "Dealer validation during booking..."
5. LLM synthesis with FLOW-SPECIFIC prompt (asks for sequence, handoffs, mermaid diagram)
6. Return: flow narrative + sequence diagram + citations

Time: ~4-6s (multiple retrieval calls + LLM)
Advantage: Every service in the flow is represented. No single service dominates.
```

### Route: general

```
Question: "How does authentication work?"

1. Falls through to existing monolithic pipeline (ask_pipeline.py)
2. embed → hybrid → rerank → graph expand → LLM → answer

Time: ~3-5s
Same as today. No regression.
```

---

## Architecture

```
                     ┌──────────────────────────────┐
                     │         /v1/ask               │
                     │   body: {question, mode}      │
                     └──────────────┬───────────────┘
                                    │
                          ┌─────────┴─────────┐
                          │                   │
                   mode="monolithic"    mode="orchestrated"
                          │                   │
                          ▼                   ▼
               ┌──────────────────┐  ┌────────────────────┐
               │  ask_pipeline.py │  │  query_classifier   │
               │  (current code,  │  │                    │
               │   unchanged)     │  │  structural?       │
               └──────────────────┘  │  single_service?   │
                                     │  cross_service?    │
                                     │  general?          │
                                     └───────┬────────────┘
                                             │
                          ┌──────────────────┼──────────────────┐
                          │                  │                   │
                          ▼                  ▼                   ▼
                   ┌─────────────┐  ┌───────────────┐  ┌───────────────┐
                   │ STRUCTURAL  │  │ SINGLE_SERVICE│  │  CROSS_FLOW   │
                   │             │  │               │  │               │
                   │ graph query │  │ filtered      │  │ get_chain()   │
                   │ format text │  │ search()      │  │ search() × N  │
                   │ (no LLM)   │  │ + LLM synth   │  │ + flow LLM    │
                   └─────────────┘  └───────────────┘  └───────────────┘
                                             │
                                             ▼ (fallback)
                                     ┌───────────────┐
                                     │   GENERAL     │
                                     │               │
                                     │ monolithic    │
                                     │ pipeline      │
                                     │ (existing)    │
                                     └───────────────┘

ALL routes use the same PRIMITIVES LAYER:

┌─────────────────────────────────────────────────────────────────┐
│                     PRIMITIVES (shared)                           │
│                                                                   │
│  search(query, repo_filter?, doc_type?, limit?)                   │
│    → embed query → hybrid retrieval → rerank → return raw chunks  │
│                                                                   │
│  get_service_chain(service, direction?, hops?)                     │
│    → Neo4j traversal → return ordered service list                │
│                                                                   │
│  get_service_info(name)                                           │
│    → Neo4j property lookup → return entity                        │
│                                                                   │
│  get_impact(name)                                                 │
│    → Neo4j 2-hop reverse traversal → return dependents            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Surface

### Existing endpoints (unchanged)

| Method | Path | Behavior |
|---|---|---|
| GET | `/v1/services/{name}` | Service details from Neo4j |
| GET | `/v1/health` | Health check |
| POST | `/webhooks/steering-update` | Trigger steering update |
| POST | `/v1/steering/batch-update` | Batch steering update |

### Modified endpoint

**POST /v1/ask**

```json
// Request
{
  "question": "How does dealer booking work end-to-end?",
  "mode": "orchestrated"  // "orchestrated" | "monolithic" (default from settings)
}

// Response (same schema as today)
{
  "answer": "...",
  "citations": [...],
  "metadata": {
    "mode": "orchestrated",
    "query_type": "cross_service_flow",  // NEW: tells you which route was taken
    "services_involved": ["booking-crud-services", "payment-service", "notification-service"],
    "latency_ms": 4200
  }
}
```

### New primitive endpoints (for programmatic access / future MCP HTTP)

**POST /v1/search** — Raw retrieval without LLM

```json
// Request
{
  "query": "booking cancellation refund",
  "repo_filter": "payment-service",   // optional: scope to one service
  "doc_type": "tech",                  // optional: filter by doc type
  "limit": 5                           // default 5
}

// Response
{
  "chunks": [
    {
      "chunk_id": "steering:payment-service:tech#chunk:3",
      "text": "## Refund Flow\nWhen a booking is cancelled...",
      "score": 0.87,
      "section_title": "Refund Flow",
      "repo_name": "payment-service",
      "source_ref": "kiro_steering/payment-service/tech.md",
      "parent_source_id": "steering:payment-service:tech"
    }
  ]
}
```

**GET /v1/graph/chain** — Service dependency chain

```json
// Request: GET /v1/graph/chain?service=booking-crud-services&direction=downstream&hops=2

// Response
{
  "root": "booking-crud-services",
  "direction": "downstream",
  "chain": [
    { "name": "payment-service", "relationship": "DEPENDS_ON", "hop": 1 },
    { "name": "notification-service", "relationship": "DEPENDS_ON", "hop": 1 },
    { "name": "dealer-master", "relationship": "DEPENDS_ON", "hop": 1 },
    { "name": "CCAvenue", "relationship": "DEPENDS_ON", "hop": 2, "via": "payment-service" }
  ]
}
```

---

## MCP Tools

### Existing (keep unchanged)

| Tool | Input | Output | LLM? |
|---|---|---|---|
| `ask_question` | `{question: str}` | `{answer, citations}` | ✅ |
| `search_graph` | `{query: str}` | `{entities}` | ❌ |
| `get_service_info` | `{name: str}` | `{service properties}` | ❌ |
| `get_impact` | `{name: str}` | `{affected services}` | ❌ |

### New primitive tools

| Tool | Input | Output | LLM? | Purpose |
|---|---|---|---|---|
| `search` | `{query, repo_filter?, doc_type?, limit?}` | `{chunks: [...]}` | ❌ | Scoped retrieval. Agent can call per-service. |
| `get_service_chain` | `{service, direction?, hops?}` | `{chain: [...]}` | ❌ | Dependency traversal. Agent uses for flow questions. |

### How Kiro uses the new tools (example)

```
User asks Kiro: "How does the booking payment flow work?"

Kiro (thinking): This is a cross-service question. Let me trace the flow.

Step 1: Kiro calls get_service_chain(service="booking-crud-services", hops=2)
  → Response: [payment-service (hop 1), notification-service (hop 1)]

Step 2: Kiro calls search(query="booking payment initiation", repo_filter="booking-crud-services", limit=2)
  → Response: 2 chunks about how booking triggers payment

Step 3: Kiro calls search(query="payment processing booking", repo_filter="payment-service", limit=2)
  → Response: 2 chunks about payment service handling

Step 4: Kiro synthesizes everything into a coherent flow answer.
```

The agent orchestrates. SmartBrain just serves primitives. Fast, cheap, flexible.

---

## File Changes

| File | Status | Description |
|---|---|---|
| `retrieval/search/primitives.py` | **NEW** | Shared primitive functions: `search()`, `get_service_chain()`. Extracts embed+retrieve+rerank logic from ask_pipeline into reusable async functions. |
| `retrieval/search/query_classifier.py` | **NEW** | `classify_query(question, known_services)` → returns query type enum. Keyword heuristic. |
| `retrieval/search/orchestrated_pipeline.py` | **NEW** | `ask_orchestrated(question)` — the router. Classifies, dispatches to the right strategy, returns answer. |
| `retrieval/search/strategies/structural.py` | **NEW** | Handles structural questions directly via Neo4j. No LLM. |
| `retrieval/search/strategies/single_service.py` | **NEW** | Handles single-service questions with filtered retrieval. |
| `retrieval/search/strategies/cross_service_flow.py` | **NEW** | Handles flow questions: chain → per-service search → flow synthesis. |
| `retrieval/search/ask_pipeline.py` | **UNCHANGED** | Existing monolithic pipeline. Used as fallback for "general" type and `mode=monolithic`. |
| `api/app.py` | **MODIFY** | Add mode routing to `/v1/ask`. Add `/v1/search` and `/v1/graph/chain` endpoints. |
| `api/schemas.py` | **MODIFY** | Add request/response models for new endpoints. |
| MCP server | **MODIFY** | Register `search` and `get_service_chain` tools. |
| `config/settings.py` | **MODIFY** | Add `default_ask_mode` setting. |
| Web UI | **MODIFY** | Add mode toggle dropdown. Show `query_type` in response metadata. |

---

## Latency Comparison

| Question type | Current (monolithic) | Orchestrated |
|---|---|---|
| "What depends on booking?" (structural) | 3-5s (full pipeline + LLM) | **~100ms** (graph only, no LLM) |
| "Tell me about payment-service" (single_service) | 3-5s (retrieves from all services) | **~2-3s** (filtered retrieval, focused context) |
| "How does booking flow work E2E?" (cross_service_flow) | 3-5s (incomplete — misses services) | **~4-6s** (slower but complete — covers all services) |
| "How does authentication work?" (general) | 3-5s | **3-5s** (same path, no regression) |

---

## Rollout Plan

**Phase 1: Build primitives + classifier (no user-facing change)**
- Implement `primitives.py`, `query_classifier.py`
- Add `/v1/search` and `/v1/graph/chain` endpoints
- Add MCP tools `search` and `get_service_chain`
- Default mode stays `monolithic` — nothing changes for users

**Phase 2: Build orchestrated strategies**
- Implement structural, single_service, cross_service_flow strategies
- Implement `orchestrated_pipeline.py` as the router
- Add `mode` param to `/v1/ask`
- UI toggle available but defaults to "Classic"

**Phase 3: A/B test and flip default**
- Run both modes in parallel
- Compare answer quality, latency, completeness
- When orchestrated wins consistently → flip `default_ask_mode` to `"orchestrated"`
- Keep `monolithic` available as fallback forever

---

## Example Comparisons

### Question: "What services depend on tvsm-auth?"

**Monolithic (current):**
- Embeds question (~200ms)
- Hybrid search across all chunks (~80ms)
- Reranks 30 candidates (~450ms)
- Graph expansion (~100ms)
- LLM call (~3s)
- Total: ~4s, costs $0.01
- Answer: Correct but slow

**Orchestrated (structural route):**
- Classifies as "structural" (~1ms)
- Neo4j query: `MATCH (s)-[:DEPENDS_ON]->(t {name:"tvsm-auth"}) RETURN s.name` (~50ms)
- Formats response (~1ms)
- Total: **~52ms**, costs **$0**
- Answer: Same information, 80x faster, free

### Question: "How does the cancellation flow work across booking and payment?"

**Monolithic (current):**
- Retrieves top-5 globally
- 4 of 5 chunks from booking-crud (it has more content about "cancellation")
- 1 chunk from payment-service (maybe)
- LLM answer: Mostly about booking-crud's cancellation logic. Payment refund mentioned briefly.

**Orchestrated (cross_service_flow route):**
- Classifies as "cross_service_flow"
- Chain: booking-crud → payment-service → notification-service
- Retrieves 2 chunks from booking-crud about cancellation
- Retrieves 2 chunks from payment-service about refund
- Retrieves 1 chunk from notification-service about cancellation notification
- LLM synthesizes with flow prompt: sequenced narrative + mermaid diagram
- Answer: Complete E2E flow with every service's role clear

### Question: "Tell me about notification-service"

**Monolithic (current):**
- Retrieves top-5 globally
- Gets 3 notification-service chunks + 2 from other services (because "notification" appears in other service docs)
- LLM answer: Good but diluted with noise

**Orchestrated (single_service route):**
- Classifies as "single_service", extracts service name: "notification-service"
- search(query="notification-service overview", repo_filter="notification-service", limit=5)
- Gets 5 chunks ALL from notification-service (product, tech, structure)
- LLM synthesizes: comprehensive service overview with zero noise
- Answer: Deeper, more complete, uses full context budget on the right service
