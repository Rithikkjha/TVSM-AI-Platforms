# SmartBrain V2 — Full Pipeline Deep Dive

A complete explanation of how data flows from raw documents into the knowledge base, and how a user question becomes a grounded answer.

---

## PART 1: DATA INGESTION (How data gets IN)

When you run `python -m ingestion.run_sync --clean`, this is what happens step by step:

---

### Step 1: Read Source Documents

The orchestrator (`ingestion/clean_ingest.py`) reads from 3 sources:

| Source | Where it comes from | Example |
|---|---|---|
| Steering files | `kiro_steering/` folder on disk | `kiro_steering/booking-crud-services/tech.md` |
| Confluence pages | Live fetch from Confluence REST API | "Common services APIs availability list" page |
| Jira tickets | Live fetch from Jira REST API | CCP10-143 ticket |

At this point you have raw text (markdown, HTML, or structured fields).

---

### Step 2: Source-Type-Aware Chunking

Each document is split into **200-500 token** pieces based on its type:

**Steering files (markdown)** → `processing/chunking/markdown_chunker.py`
```
Input: booking-crud-services/tech.md (500 lines)

Split at H1-H4 headings:
  "# Tech Stack" section → chunk 0
  "## Database" section → chunk 1
  "## Dependencies" section → chunk 2
  "## API Endpoints" section → chunk 3
  ...

Each chunk gets ancestor heading prepended:
  chunk 1 display_text = "# Tech Stack > ## Database\nSQL Server (MSSQL)..."
  chunk 1 original_segment = "SQL Server (MSSQL)..."  (raw, for round-trip)
```

**Confluence pages (HTML)** → `processing/chunking/confluence_chunker.py`
```
Input: <h2>API List</h2><p>The following APIs...</p><h3>Booking API</h3>...

Step 1: Normalize HTML → markdown-style headings
  <h2>API List</h2> → "## API List"
  <p>text</p> → plain text

Step 2: Same heading-split logic as markdown chunker
```

**Jira tickets (structured fields)** → `processing/chunking/jira_chunker.py`
```
Input: CCP10-143 { summary: "...", description: "...", comments: [...] }

Split at field boundaries:
  chunk 0 = "CCP10-143 — Summary\n[summary text]"
  chunk 1 = "CCP10-143 — Description\n[description text]"
  chunk 2 = "CCP10-143 — Comment\n[comment 1 text]"
```

**Size enforcement:**
- If a section > 500 tokens → split further at paragraph boundaries, then sentences
- If a section < 200 tokens → merge with adjacent section until ≥ 200
- Exception: the very last chunk can be under 200 if there's nothing left to merge

---

### Step 3: Attach Metadata to Each Chunk

Every chunk gets a `ChunkMetadata` record:

```python
ChunkMetadata(
    section_title="Database",              # nearest heading / field name
    parent_source_id="steering:booking-crud-services:tech",  # which doc it came from
    repo_name="booking-crud-services",     # which service
    chunk_index=1,                         # position in document (0-based)
    source_ref="kiro_steering/booking-crud-services/tech.md",  # file/URL/key
    doc_type="tech",                       # product|structure|tech|confluence|jira
)
```

The chunk gets a stable ID: `"steering:booking-crud-services:tech#chunk:1"`

---

### Step 4: Embed Each Chunk (Dense Vector)

Each chunk's `display_text` (the heading-prepended version) is sent to Azure OpenAI:

```
"# Tech Stack > ## Database\nSQL Server (MSSQL) with Sequelize ORM..."
       ↓ Azure OpenAI text-embedding-3-large
       → [0.023, -0.541, 0.812, ... 1536 floats]
```

This vector captures the semantic meaning. Cost: ~$0.0001 per chunk.

---

### Step 5: Deduplication Check

Before writing, check if a near-identical chunk already exists:

```
New chunk vector → search existing chunks for same repo_name
  → Find top match: cosine similarity = 0.97

  0.97 > threshold (0.95) → DUPLICATE DETECTED

  Who's the duplicate?
    New chunk: doc_type="tech" (steering, authority=2)
    Existing chunk: doc_type="confluence" (authority=3)
    
    Confluence wins → the steering chunk is the duplicate
    → Mark steering chunk as is_duplicate=True
    → Create DUPLICATE_OF edge in graph
    → Duplicate is stored but excluded from search results
```

If no match > 0.95, the chunk is canonical (not a duplicate).

---

### Step 6: Write to 3 Stores

Each chunk is written to ALL THREE storage systems:

**6a. Vector Store (Qdrant or Azure AI Search)**
```
VectorRecord(
    source_id="steering:booking-crud-services:tech#chunk:1",
    entity_type="Chunk",
    vector=[0.023, -0.541, ...],      # the 1536-float embedding
    text_hash="sha256_of_original",   # for idempotency
    section_title="Database",          # filterable
    repo_name="booking-crud-services", # filterable
    doc_type="tech",                   # filterable
    is_duplicate=False,                # excluded from search if True
    ...
)
```

**6b. BM25 Keyword Index (LocalBM25Index or Azure native)**
```
index_chunk(
    chunk_id="steering:booking-crud-services:tech#chunk:1",
    text="# Tech Stack > ## Database\nSQL Server (MSSQL)...",
    metadata={"repo_name": "booking-crud-services", "doc_type": "tech"}
)
→ Tokenized: ["tech", "stack", "database", "sql", "server", "mssql", "sequelize", "orm"]
→ Stored in inverted index for keyword search
```

**6c. Neo4j Graph**
```
CREATE (c:Chunk {
    source_id: "steering:booking-crud-services:tech#chunk:1",
    parent_source_id: "steering:booking-crud-services:tech",
    chunk_index: 1,
    doc_type: "tech",
})
CREATE (parent)-[:HAS_CHUNK]->(c)
```

---

### Step 7: Deterministic Relationship Extraction

After ALL entities and chunks are materialized, structural edges are created:

```
(Service:booking-crud-services) -[:DOCUMENTED_IN]-> (ConfluencePage:steering:booking-crud-services:tech)
(Service:booking-crud-services) -[:OWNED_BY]-> (Team:CBS)
```

These come from structured data (file conventions, CODEOWNERS, config), not from reading prose.

---

### Step 8: LLM Relationship Enrichment

Finally, GPT-4o reads the text and infers edges that can't be derived structurally:

```
Input to LLM: "booking-crud-services tech.md mentions SQL Server, notification-service, payment-service"
Known services: ["booking-crud-services", "notification-service", "payment-service", "tvsm-auth", ...]

LLM output:
  dependencies_claimed: [
    {from: "booking-crud-services", to: "notification-service", confidence: "high"},
    {from: "booking-crud-services", to: "payment-service", confidence: "medium"},
  ]

→ Grounding filter: both endpoints exist in known services? YES
→ Write edges:
  (booking-crud-services) -[:DEPENDS_ON {provenance:"llm:steering", confidence:"high"}]-> (notification-service)
  (booking-crud-services) -[:DEPENDS_ON {provenance:"llm:steering", confidence:"medium"}]-> (payment-service)
```

The grounding filter ensures the LLM can't invent services that don't exist.

---

### Ingestion Summary

After a full clean ingest, your stores contain:

| Store | What's in it | Example count |
|---|---|---|
| Qdrant (vectors) | 1 vector per chunk, 1536 floats each, with metadata | ~2000 chunk vectors |
| BM25 index | 1 tokenized entry per chunk, for keyword search | ~2000 entries |
| Neo4j (graph) | Service nodes, Chunk nodes, ConfluencePage nodes, Ticket nodes, + all edges | ~200 entities, ~2000 chunks, ~500 edges |

---

## PART 2: QUERY PIPELINE (How a question becomes an answer)

When someone asks: *"What database does booking-crud-services use?"*

---

### Step 1: Result Cache Check

```
key = SHA-256("What database does booking-crud-services use?")
→ Check cache: miss (first time asking this)
```

If hit: return the cached answer instantly (< 1ms). Skip everything below.

---

### Step 2: Embedding Cache Check

```
key = SHA-256("What database does booking-crud-services use?")
→ Check embedding cache: miss (first time)
```

If hit: skip the embedding API call, use the cached vector. Save ~200ms + money.

---

### Step 3: Embed the Question

```
"What database does booking-crud-services use?"
       ↓ Azure OpenAI text-embedding-3-large (same model used for chunks)
       → [0.045, -0.321, 0.667, ... 1536 floats]

Time: ~200ms
Cost: ~$0.00001
```

Write to embedding cache (TTL 24h) so next time we skip this.

---

### Step 4: Hybrid Retrieval (Dense + BM25, in parallel)

Two searches run SIMULTANEOUSLY:

**4a. Dense vector search:**
```
cosine_similarity(question_vector, every_chunk_vector)
→ Top-30 by semantic similarity:
  #1: "booking-crud-services tech > Database: SQL Server..." (score: 0.91)
  #2: "booking-crud-services structure > Data Layer..." (score: 0.87)
  #3: "payment-service tech > Database: MongoDB..." (score: 0.84) ← wrong service!
  ...#30
```

**4b. BM25 keyword search:**
```
Query tokens: ["database", "booking", "crud", "services"]
→ Top-30 by term frequency:
  #1: "booking-crud-services tech > Database: SQL Server..." (BM25: 12.3)
  #2: "booking-crud-services structure > Module Dependencies..." (BM25: 8.1)
  #3: "booking-crud-services product > Domain Entities..." (BM25: 7.5)
  ...#30
```

Notice: Dense found "payment-service" (semantically similar to "database" concept). BM25 didn't — it requires the literal word "booking" to be present. That's why we use both.

---

### Step 5: Reciprocal Rank Fusion (RRF)

Merge the two ranked lists into one:

```
For each chunk, compute: score = Σ 1/(60 + rank_in_list)

"booking-crud-services tech > Database":
  Dense rank #1 → 1/(60+1) = 0.01639
  BM25 rank #1  → 1/(60+1) = 0.01639
  Fused score = 0.03278  ← HIGHEST (appeared in both lists!)

"payment-service tech > Database":
  Dense rank #3 → 1/(60+3) = 0.01587
  BM25 rank: NOT PRESENT → 0
  Fused score = 0.01587  ← drops lower because only in one list

Output: top-30 by fused score (chunks appearing in BOTH lists rank highest)
```

---

### Step 6: Cross-Encoder Re-Ranking

The top-30 fused chunks are scored by a small transformer model:

```
For each of the 30 chunks:
  Input: "What database does booking-crud-services use? [SEP] SQL Server (MSSQL) with Sequelize ORM..."
  → relevance score: 0.94

  Input: "What database does booking-crud-services use? [SEP] booking uses Redis for caching..."
  → relevance score: 0.31

Pick top-5 by cross-encoder score:
  1. (0.94) booking-crud tech > Database section
  2. (0.88) booking-crud structure > Data Layer section
  3. (0.82) booking-crud tech > Dependencies section
  4. (0.76) booking-crud product > Domain Entities section
  5. (0.71) booking-crud structure > Module Dependencies section
```

Time: ~450ms for all 30 pairs.

---

### Step 7: Graph Expansion

From the top-5 chunks, look at their `parent_source_id` values and expand 1-2 hops in Neo4j:

```
parent: "steering:booking-crud-services:tech"
  → belongs to Service: booking-crud-services
    → DEPENDS_ON: notification-service, payment-service
    → OWNED_BY: Team CBS
    → DOCUMENTED_IN: 3 steering docs

This context helps the LLM give a fuller answer.
```

---

### Step 7.5: Graph Gap Re-Retrieval

After graph expansion, we check: did the graph surface related services whose chunks we DON'T already have in our top-5?

**The logic:**
1. Look at which services the top-5 chunks came from (e.g. all from "booking-crud-services")
2. Look at which services the graph expansion found (e.g. "payment-service", "notification-service")
3. If a graph neighbor is NOT covered by any of our chunks → that's a "gap"
4. For each gap: search Qdrant for the best chunk from that service, filtered to the SAME question vector
5. If the score > 0.7 → add it (it's relevant to the question)
6. If the score < 0.7 → skip it (not relevant to THIS question)

**Example — when it FIRES:**

```
Question: "How does booking cancellation work?"
Top-5 chunks: all from booking-crud-services
Graph says: payment-service is connected

Gap detected: payment-service has no chunks in our top-5

Re-retrieve: search payment-service chunks with query "How does booking cancellation work?"
  → Best chunk: "When a booking is cancelled, refund flows through CCAvenue..."
  → Score: 0.78 > threshold 0.7
  → ✅ ADD to context as [ref:6]

Now the LLM knows about the refund mechanism in payment-service too!
```

**Example — when it DOESN'T fire:**

```
Question: "What database does booking use?"
Top-5 chunks: all from booking-crud-services
Graph says: payment-service is connected

Gap detected: payment-service has no chunks

Re-retrieve: search payment-service chunks with query "What database does booking use?"
  → Best chunk: "Payment gateway integration with CCAvenue..."
  → Score: 0.31 < threshold 0.7
  → ❌ SKIP (payment gateway ≠ database question)

No extra chunk added. Zero wasted context.
```

**Key points:**
- Uses the SAME query vector from step 3 (no extra embedding call)
- Max 3 extra Qdrant lookups (~150ms worst case)
- Most queries: zero extra cost (no relevant gap)
- Bounded: never adds more than 3 extra chunks

---

### Step 8: Citation Context Assembly

Build the LLM context with [ref:N] markers:

```
[ref:1] # Tech Stack > ## Database
SQL Server (MSSQL) with Sequelize ORM. Two connections: primary + read replica...

[ref:2] # Code Structure > ## Data Layer
The data layer uses Sequelize models mapped to SQL Server tables...

[ref:3] # Tech Stack > ## Dependencies
- mssql: ^9.0.0
- sequelize: ^6.35.0
...

[ref:4] ...
[ref:5] ...

## Graph Neighborhood
- notification-service: async notification delivery
- payment-service: payment gateway integration
```

Each [ref:N] maps to a Citation object with source_id, section_title, URL.

---

### Step 9: LLM Call (GPT-4o)

```
System prompt: "You are the Engineering Memory Graph Assistant. Cite using [ref:N]..."
User message: [the context from step 8] + "Question: What database does booking-crud-services use?"

→ GPT-4o response:
"booking-crud-services uses **SQL Server (MSSQL)** as its primary database [ref:1],
accessed via the **Sequelize ORM** [ref:2]. The connection is configured with two
pools — a primary for writes and a read replica for queries [ref:1].

Dependencies include `mssql` v9.0.0 and `sequelize` v6.35.0 [ref:3]."
```

---

### Step 10: Citation Mapping

Parse [ref:N] markers from the LLM output and map to structured citations:

```
Used refs: [1, 2, 3]  (ref:4 and ref:5 weren't cited → dropped)

Citations:
  [ref:1] → {source_id: "steering:booking-crud-services:tech#chunk:1",
             section_title: "Database",
             source_ref: "kiro_steering/booking-crud-services/tech.md"}
  [ref:2] → {source_id: "steering:booking-crud-services:structure#chunk:3",
             section_title: "Data Layer",
             source_ref: "kiro_steering/booking-crud-services/structure.md"}
  [ref:3] → {source_id: "steering:booking-crud-services:tech#chunk:2",
             section_title: "Dependencies",
             source_ref: "kiro_steering/booking-crud-services/tech.md"}
```

---

### Step 11: Cache Write

```
Embedding cache: store query vector (TTL 24h)
Result cache: store full answer + citations (TTL 1h)
```

Next time anyone asks the same question → instant response from cache.

---

### Step 12: Return

```json
{
  "answer": "booking-crud-services uses **SQL Server (MSSQL)**...",
  "citations": [
    {"ref": 1, "source_id": "...", "section_title": "Database", "source_ref": "..."},
    {"ref": 2, "source_id": "...", "section_title": "Data Layer", "source_ref": "..."},
    {"ref": 3, "source_id": "...", "section_title": "Dependencies", "source_ref": "..."}
  ]
}
```

---

## TIMING BREAKDOWN

| Step | Time | Skippable? |
|---|---|---|
| Result cache check | 1ms | — |
| Embedding cache check | 1ms | — |
| Embed question | 200ms | Skipped on cache hit |
| Dense vector search | 50ms | — |
| BM25 keyword search | 30ms | Runs in parallel with dense |
| RRF fusion | 1ms | — |
| Cross-encoder re-rank (30 pairs) | 450ms | Falls back to hybrid top-5 on failure |
| Graph expansion | 100ms | — |
| Graph gap re-retrieval | 0-150ms | Only fires when there's a relevant gap (usually 0ms) |
| Citation assembly | 1ms | — |
| LLM call (GPT-4o) | 2-4s | Skipped on result cache hit |
| Citation mapping | 1ms | — |
| Cache write | 5ms | — |
| **Total (cache miss, no gap)** | **~3-5s** | |
| **Total (cache miss, with gap)** | **~3.2-5.2s** | |
| **Total (result cache hit)** | **~1ms** | |

---

## DB WRITES SUMMARY

| What gets written | Where | When | Key |
|---|---|---|---|
| Chunk vector (1536 floats + metadata) | Qdrant / Azure AI Search | Ingestion step 6a | source_id (chunk_id) |
| Chunk keywords (tokenized text) | BM25 index (memory + disk) | Ingestion step 6b | chunk_id |
| Chunk node (source_id, doc_type, etc.) | Neo4j | Ingestion step 6c | source_id |
| HAS_CHUNK edge | Neo4j | Ingestion step 6c | (parent → chunk) |
| DUPLICATE_OF edge | Neo4j | Ingestion step 5 (if dup) | (dup → canonical) |
| Service/ConfluencePage/Ticket node | Neo4j | Ingestion step 1 | source_id |
| DOCUMENTED_IN / DEPENDS_ON / LINKED_TO | Neo4j | Ingestion steps 7-8 | (source, target, type, text_hash) |
| Query embedding | Embedding cache (memory) | Query step 11 | SHA-256(query) |
| Full answer + citations | Result cache (memory) | Query step 11 | SHA-256(query+filters) |

---

## IDEMPOTENCY

Every write is safe to repeat:
- **Entities**: upsert by `source_id` — same source_id → update, not duplicate
- **Chunks**: upsert by `text_hash` + `parent_source_id` — same content → skip
- **Edges**: check existence before writing — same (source, target, type) → skip
- **Vectors**: upsert by `source_id` — same chunk → replace vector

This is why `python -m ingestion.run_sync --clean` is safe to run repeatedly — it only does real work on files that actually changed.
