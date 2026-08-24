# Data Source Map — What Goes Where

A complete reference of how each data source flows through the ingestion pipeline and where the data lands.

---

## Summary Matrix

| Source | Chunked | Qdrant (vectors) | BM25 (keywords) | Neo4j (nodes) | Neo4j (structural edges) | Neo4j (LLM edges) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Steering files** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Jira tickets** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Confluence pages** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ (planned) |

---

## Detailed Breakdown Per Source

### 1. Steering Files

**Input:** `kiro_steering/{repo-name}/product.md`, `structure.md`, `tech.md`

| Pipeline Stage | What Happens | Where It Lands |
|---|---|---|
| Chunking | Split into 200-500 token semantic chunks | In-memory (passed to next stages) |
| Embedding | Batch embed all chunks via Azure OpenAI | **Qdrant** — 1536-dim vectors with metadata |
| BM25 indexing | Index raw chunk text + metadata | **BM25** — term frequency index |
| Dedup check | Cosine similarity > 0.95 marks as duplicate | **Qdrant** — `is_duplicate` flag on record |
| Entity nodes | Service node + ConfluencePage (steering doc) node + Chunk nodes | **Neo4j** — `(:Service)`, `(:ConfluencePage)`, `(:Chunk)` |
| Structural edges | Service → doc, doc → chunks | **Neo4j** — `DOCUMENTED_IN`, `HAS_CHUNK` |
| LLM extraction | GPT-4o reads full doc + known services list | **Neo4j** — `DEPENDS_ON` edges between services |

**Example graph result:**
```
(Service: booking-crud-services)
  ──DOCUMENTED_IN──▶ (Doc: tech.md)
      ──HAS_CHUNK──▶ (Chunk: chunk_001)
      ──HAS_CHUNK──▶ (Chunk: chunk_002)
  ──DEPENDS_ON──▶ (Service: payment-service)      ← from LLM
  ──DEPENDS_ON──▶ (Service: tvsm-auth)            ← from LLM
```

---

### 2. Jira Tickets

**Input:** Live fetch from Jira API (configured projects)

| Pipeline Stage | What Happens | Where It Lands |
|---|---|---|
| Chunking | Split ticket (summary + description + fields) into chunks | In-memory |
| Embedding | Batch embed all chunks | **Qdrant** — vectors |
| BM25 indexing | Index chunk text | **BM25** — keyword index |
| Dedup check | Check against existing chunks in same repo | **Qdrant** — `is_duplicate` flag |
| Entity nodes | Ticket node + Chunk nodes | **Neo4j** — `(:Ticket)`, `(:Chunk)` |
| Structural edges | Ticket → chunks | **Neo4j** — `HAS_CHUNK` |
| LLM extraction | GPT-4o reads ticket text + known services & tickets | **Neo4j** — `LINKED_TO` edges (ticket → service) |

**Example graph result:**
```
(Ticket: ACV2-1234)
  ──HAS_CHUNK──▶ (Chunk: chunk_010)
  ──LINKED_TO──▶ (Service: booking-crud-services)  ← from LLM
  ──LINKED_TO──▶ (Service: payment-service)        ← from LLM
```

---

### 3. Confluence Pages

**Input:** Live fetch from Confluence API (configured spaces)

| Pipeline Stage | What Happens | Where It Lands |
|---|---|---|
| Chunking | Split page HTML body into chunks | In-memory |
| Embedding | Batch embed all chunks | **Qdrant** — vectors |
| BM25 indexing | Index chunk text | **BM25** — keyword index |
| Dedup check | Check against existing chunks | **Qdrant** — `is_duplicate` flag |
| Entity nodes | ConfluencePage node + Chunk nodes | **Neo4j** — `(:ConfluencePage)`, `(:Chunk)` |
| Structural edges | Page → chunks | **Neo4j** — `HAS_CHUNK` |
| LLM extraction | ❌ NOT IMPLEMENTED YET | — |

**Current gap:** Confluence page nodes exist in Neo4j but have NO relationship edges to services. They are searchable via Qdrant/BM25, but the graph doesn't know which service a page documents.

**Example graph result (current):**
```
(ConfluencePage: "Payment Architecture")
  ──HAS_CHUNK──▶ (Chunk: chunk_050)
  ──HAS_CHUNK──▶ (Chunk: chunk_051)
  (no edges to any Service — isolated node)
```

**Example graph result (after adding LLM extraction):**
```
(ConfluencePage: "Payment Architecture")
  ──HAS_CHUNK──▶ (Chunk: chunk_050)
  ──DOCUMENTS──▶ (Service: payment-service)        ← from LLM (future)
  ──MENTIONS──▶ (Service: booking-crud-services)   ← from LLM (future)
```

---

## Phase Execution Order

```
Phase 1: Materialize (all sources in sequence)
  ├── Steering files → chunk + embed + write (Qdrant, BM25, Neo4j nodes + structural edges)
  ├── Confluence pages → chunk + embed + write (Qdrant, BM25, Neo4j nodes + structural edges)
  └── Jira tickets → chunk + embed + write (Qdrant, BM25, Neo4j nodes + structural edges)

Phase 2: Deterministic extraction
  └── Count and record structural edges already written in Phase 1

Phase 3: LLM enrichment (GPT-4o)
  ├── Steering docs → extract DEPENDS_ON edges → write to Neo4j
  ├── Jira tickets → extract LINKED_TO edges → write to Neo4j
  └── Confluence pages → ❌ NOT YET (planned: extract DOCUMENTS/MENTIONS edges)
```

---

## What Each Store Answers

| Store | Question it answers | How |
|---|---|---|
| **Qdrant** | "Find chunks semantically similar to this question" | Cosine similarity on 1536-dim vectors |
| **BM25** | "Find chunks containing these exact keywords" | Term frequency matching |
| **Neo4j** | "What services does X depend on?", "What's the blast radius of Y?", "What docs exist for Z?" | Graph traversal |

---

## Gaps & Planned Improvements

| Gap | Impact | Fix |
|---|---|---|
| Confluence pages have no LLM-extracted edges | Graph can't answer "what service does this page document?" | Add `extract_from_confluence` to Phase 3 |
| No GitHub PR ingestion in clean ingest | PRs aren't searchable via the V2 pipeline | Add PR source to Phase 1 |
| No Teams/SharePoint ingestion | Messages and SharePoint docs not searchable | Add Microsoft Graph source (requires Azure AD app) |

---

## Credential Requirements

| Source | Credential | Env Variable |
|---|---|---|
| Steering files | None (local filesystem) | — |
| Jira | Atlassian API token + email | `JIRA_TOKEN`, `JIRA_EMAIL`, `JIRA_URL` |
| Confluence | Same Atlassian token | `CONFLUENCE_TOKEN`, `CONFLUENCE_URL` |
| Azure OpenAI | API key + endpoint | `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT` |
| GitHub | PAT or App token | `GITHUB_TOKEN` |
