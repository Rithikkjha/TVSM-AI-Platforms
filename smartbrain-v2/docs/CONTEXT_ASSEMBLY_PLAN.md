# Context Assembly & Retrieval Granularity — Current State + Improvement Plan

> **Scope:** How SmartBrain turns a user question into the text it feeds the LLM,
> what is wrong with it today, the concepts involved (chunk / section / full-doc
> granularity, token budget, parent-document retrieval, auto-merging, graph-guided
> expansion), and the concrete steps to fix it.
>
> **Audience:** Engineers working on `retrieval/search/ask_pipeline.py` and the
> retrieval layer. Read this before touching context assembly.

---

## 0. TL;DR

- Retrieval does expensive **chunk-level precision** work (hybrid + RRF + cross-encoder rerank to top-5), then **throws the chunk text away** and feeds the LLM the **entire parent document** from Neo4j.
- This is fine for **single-service** questions (one small doc), but breaks on **cross-service flow** questions: multiple full docs overflow the context, hit the `[:10]` parent cap and the 12 000-char per-doc cap, and the section that actually answers the question can get **silently truncated / dropped**.
- The fix is the industry-standard **parent-document / auto-merging** pattern with a **token budget**: pick the retrieval **granularity** (full doc vs section) based on whether the selected docs fit the budget.
- Additional gap-closers: **edge types in graph context**, **query decomposition**, **heading-aware chunking**, and an **eval harness** to measure it.

---

## 1. Glossary (the concepts, in plain terms)

### 1.1 Granularity
The **size of the text unit** we retrieve and send to the LLM. Smallest → largest:

```
chunk        ~200 tokens     precise match, low tokens, loses surrounding context
section      ~1–2K tokens    one heading's worth — balanced
full doc     ~15K tokens     complete context, expensive, can overflow
```

- **Fine granularity** (chunk/section) = precise, cheap, but may miss context.
- **Coarse granularity** (full doc) = complete, but wasteful and can blow the context window.
- **Switch granularity by budget** = choose the unit size based on how much context-window room is available for this query.

### 1.2 Chunk
The small unit we **embed and index** in Qdrant (dense) + BM25 (sparse). Small chunks embed more accurately (their vector reflects one idea). Used for **matching**, not necessarily for the final context.

### 1.3 Section / Section-window
A block of the parent document under one heading (e.g. `### Payment Update Status Logic`). Extracted from the parent's `content_summary` using the chunk's `section_title`. The "middle ground" between a tiny chunk and a whole doc.

### 1.4 Full document (parent document)
The complete `content_summary` stored on the Neo4j parent node (steering doc, Confluence page, etc.). What we currently always send.

### 1.5 Parent-Document Retrieval (industry pattern)
Index **small child chunks** for accurate embedding match, but at answer time **look up the chunk's parent and send the larger parent** to the LLM. Resolves the tension: small chunks embed well, but the LLM needs more surrounding context than a lone chunk. (LangChain `ParentDocumentRetriever`, MongoDB Atlas, Azure RAG guide.)

- **We already do a coarse version of this** — we fetch the parent doc. The problem is we *always* send the *whole* parent, with no budget control.

### 1.6 Auto-Merging Retrieval (LlamaIndex)
A dynamic version of parent-document retrieval: index a **hierarchy** (leaf chunks → parent nodes). At query time, if **enough leaf chunks under the same parent** are relevant (cross a threshold), **merge them up** into the parent; otherwise keep the small leaves. i.e. granularity is decided **per parent, dynamically**, based on how much of it is relevant.

### 1.7 Token budget
A cap on how much retrieved context (in tokens) we put in the prompt, leaving room for the system prompt + the model's answer. Even with a 128K-token model, you don't fill the window — a large window is not a substitute for good context management. Common practice: cap retrieved context at ~8–16K tokens.

### 1.8 Graph-guided expansion (context-graph RAG)
Flat RAG finds context **only by text similarity**. Graph-guided RAG additionally **walks the dependency graph edges** (`booking --DEPENDS_ON--> payment`) to pull in **structurally connected** content even when its text is not similar to the question. This is what makes cross-service flow answers possible. (SmartBrain already does this via Neo4j traversal + graph-gap re-retrieval.)

### 1.9 RRF (Reciprocal Rank Fusion)
Merges the dense (vector) and sparse (BM25) ranked lists into one. A doc ranking high in either list surfaces; a doc both agree on gets a consensus boost.

### 1.10 Cross-encoder rerank
A transformer that re-scores the top-N candidates against the query for precision (top-30 → top-5). Raises precision from ~40% to ~85% — but today that precision is wasted at context assembly (see §3).

---

## 2. Current pipeline (as implemented in `retrieval/search/ask_pipeline.py`)

```
1. Result-cache check        (SHA-256 of question → instant return on hit)
2. Embedding-cache check     (reuse query vector if seen before)
3. Embed query              (Azure OpenAI text-embedding-3-large)
4. Hybrid retrieval          (dense [Qdrant] ∥ BM25 [sparse]) → RRF → top-30
5. Cross-encoder rerank      (top-30 → top-5 ScoredChunks)         ← precision step
6. Graph expansion           (1–2 hops from each chunk's parent_source_id in Neo4j)
6.5 Graph-gap re-retrieval   (for graph-surfaced services we have no chunk for,
                              re-query Qdrant for 1 relevant chunk; score > 0.7; max 3)
7. Context assembly          (dedupe parents → fetch FULL content_summary per parent,
                              cap: first 10 parents, 12 000 chars each)   ← the problem
8. LLM synthesis             (GPT-4o, [ref:N] citations)
9. Cache write               (embedding 24h, result 1h)
```

Storage split (why two stores):
- **Qdrant** — dense vectors (semantic match). **BM25** — sparse keyword match (exact terms).
- **Neo4j** — relationships (`DEPENDS_ON`, `DOCUMENTED_IN`, …) **and** the full `content_summary` used at step 7.

---

## 3. The problem (the gap)

At **step 7**, the pipeline:
1. Collects the `parent_source_id` of each top-5 (+ gap) chunk.
2. **Discards the chunk text** (`chunk.text` is never used).
3. Fetches the **entire parent `content_summary`** (capped 12 000 chars) for up to **10** parents.

Consequences:

| Issue | Detail |
|---|---|
| **Rerank precision wasted** | We carefully pick the best 5 *chunks*, then feed whole *documents* — including all irrelevant sections. Precision@5 becomes coarse "precision@5 docs". |
| **Chunks degrade to a doc-selector** | Their only surviving role is "which parent to fetch". |
| **Token blow-up** | Up to 10 × 12K = 120K chars of context. Slow, expensive, dilutes the signal. |
| **Silent truncation / drops** | Cross-service questions pull many full docs; the `[:10]` parent cap + 12K char cap can **cut the section that actually answers the question**, especially gap-chunk parents appended last. |

**Worked example**

Question: *"How does payment update happen in the booking service?"*
Relevant facts live in 3 docs / specific sections:
- `API_SPEC.md §7.2` PUT /bookings (action), `§7.6/7.7` payment webhooks
- `LLD.md §6` Payment Update Status Logic
- `HLD.md §2` Booking Modification (Payment Update) sequence

- **Full-doc (today):** fetches *all* of API_SPEC + LLD + HLD (≈30K+ chars), ~8% relevant. On a bigger multi-service question, the payment section can be truncated out entirely.
- **Section-window (fix):** feeds only §7.2/§7.6/§7.7 + LLD §6 + HLD §2 (≈2K chars), 100% relevant.

For a **single well-structured doc**, full-doc still answers fine (why it was chosen). The pain is **cross-service flow** + **token budget** — precisely SmartBrain's headline use case.

---

## 4. The fix — budget-driven granularity switch

Deterministic, no LLM, does **not** rely on the brittle keyword classifier. Decided **after** retrieval using **measured** facts (parent count + total size vs budget).

### 4.1 Decision rule

```
1. parents_ordered = unique parent_source_ids in chunk-rank order
   (each remembers the section_title of its highest-ranked chunk)
2. total_full = Σ tokens(content_summary) for each parent
3. IF total_full <= CONTEXT_TOKEN_BUDGET:
        → FULL DOC mode      (fetch whole content_summary per parent)
   ELSE:
        → SECTION mode       (per parent, extract just its chunk's section)
```

### 4.2 SECTION mode (greedy, rank-ordered, never truncates blindly)

```
budget = CONTEXT_TOKEN_BUDGET
for parent in parents_ordered:                 # already relevance-ordered
    section = extract_section(content_summary, section_title)
    if not section:                            # no clean heading match
        section = window_around(chunk_index, SECTION_WINDOW_TOKENS)
    if tokens(section) <= budget:
        add section; budget -= tokens(section)
    else:
        break                                  # stop at budget, highest-rank first
```

- Fills **highest-relevance first** → if budget runs out we drop the *least* relevant, not arbitrary ones.
- **Fixes the gap-chunk drop bug**: gap chunks are already in the ranked list, so their section competes on rank — no special-casing, no `[:10]` truncation surprise.

### 4.3 Edge cases

| Case | Decision |
|---|---|
| 1 parent, fits budget | Full doc |
| 1 parent, larger than budget | Section (+ window fallback) |
| Many parents, all fit | Full docs |
| Many parents, overflow | Sections, greedy by rank |
| Chunk has no matching heading | Char/token window around `chunk_index` |
| Section extraction fails | Fall back to that parent's full doc, counted against budget |

### 4.4 Config knobs (tunable, no code change)

| Knob | Default | Meaning |
|---|---|---|
| `CONTEXT_TOKEN_BUDGET` | ~12 000 tokens | Total retrieved-context cap (measure with tiktoken). Crossover where whole-doc becomes competitive is ~16K per the literature. |
| `SECTION_WINDOW_TOKENS` | ~500–800 | Fallback window size when no heading matches |
| `CONTEXT_ASSEMBLY_MODE` | `auto` | `auto` / `full` / `section` — escape hatch for testing & rollback |

### 4.5 Why not use the classifier to decide?
The keyword classifier (`query_classifier.py`) is brittle on phrasing ("payment update in booking" has no `flow`/`e2e` keyword → mislabels as single_service). The **measured parent-count + token-budget** signals are facts, not guesses, and self-correct: even if the query is mislabeled, once graph-gap retrieval pulls in extra services, the budget check fires and switches to sections anyway.

---

## 5. Additional gap-closers (ranked by impact)

### 5.1 Source-doc quality — the real #1 ceiling *(highest impact, highest effort)*
Retrieval can only surface what the docs contain. Team-written MDs are inconsistent; if a service's doc omits its payment flow, no retrieval trick recovers it.
- **Action:** code-derived doc generator (`analysis/github_fetcher.py` + scanner) → auto-generate accurate per-repo MD (endpoints, deps, DB, events) from the actual code via GitHub API. Ground truth beats hand-written docs.

### 5.2 Query decomposition / multi-query *(high impact on flow questions)*
A cross-service question is really several sub-questions. Today we embed the whole thing as one vector.
- **Action:** split into sub-queries — one per service in the dependency chain (graph-driven) or via a cheap LLM call — retrieve per sub-query, merge. Directly boosts end-to-end flow answers.

### 5.3 Edge types in graph context *(cheap, high value — ship with §4)*
Graph expansion currently feeds `- payment-service: description` — just names, no relationship.
- **Action:** include the edge: `booking --DEPENDS_ON (service_bus: "Booking Topic")--> async-comms`. Lets the LLM describe *how* services connect, not just *that* they do. We already traverse the edges; just format them in.

### 5.4 Heading-aware chunking at ingest *(structural, needs re-ingest)*
Section-window extraction is only reliable if chunks align to headings.
- **Action:** chunk on markdown headings (`##`/`###` = boundary) so section == chunk. Makes §4 robust.

### 5.5 Eval harness *(low effort, makes everything measurable)*
`steering-lite/bench/questions.yaml` exists but is unused.
- **Action:** build ~30 labelled TVS questions with expected answers/services; run before + after each change. Converts "feels better" into "recall 78% → 91%". Required to defend changes.

---

## 6. Recommended sequence

1. **Now (ship together):** §4 budget-driven granularity switch + §5.3 edge types in context. Small, high value, low risk (default `auto`, escape hatch to `full` for rollback).
2. **Next:** §5.5 eval harness — so improvements are measured.
3. **Then:** §5.2 query decomposition for flow questions.
4. **On next re-ingest:** §5.4 heading-aware chunking.
5. **Ongoing (biggest ceiling):** §5.1 code-derived doc quality.

---

## 7. How the industry solves this (references)

| Pattern | Source | Relation to us |
|---|---|---|
| Parent-Document Retrieval (index small chunks, send parents) | LangChain `ParentDocumentRetriever`; MongoDB Atlas; Azure RAG guide | We do a coarse version; §4 adds the budget control they use |
| Auto-Merging Retrieval (merge leaves→parent when enough are relevant) | LlamaIndex `AutoMergingRetriever` | §4 is a budget-based variant of this |
| Whole-file competitive only at larger budgets (~16K tokens); small chunks win at small budgets | arXiv 2510.20609 (Task-Aware Retrieval under Compute Budgets) | Validates the budget crossover in §4.4 |
| Don't stuff entire/oversized docs — expensive, overflows, worse results | Microsoft Azure Architecture Center (RAG chunking) | Names our current step-7 behaviour as the anti-pattern |
| Parent-child production tuning: ~200-token children, ~1–2K-token parents | System Design for RAG (Substack) | Matches our section-window target size |
| Context-graph RAG ~35% accuracy gain over flat chunk retrieval | Atlan (Context Graph) | Justifies our Neo4j + graph-gap layer (§1.8) |

*(All third-party figures rephrased for licensing compliance; see linked sources for originals.)*

---

## 8. Current state vs target — summary table

| Aspect | Today | Target |
|---|---|---|
| Chunk matching (Qdrant + BM25 + RRF) | ✅ | ✅ (unchanged) |
| Cross-encoder rerank | ✅ but wasted at assembly | ✅ and honoured (section granularity) |
| Graph expansion + gap re-retrieval | ✅ | ✅ + edge types in context (§5.3) |
| Context unit | ❌ always full doc | ✅ budget-driven: full ↔ section |
| Context cap | ❌ by count (10 parents), 12K chars each | ✅ by **token budget** |
| Gap-chunk parents | ⚠️ can be truncated by `[:10]` | ✅ rank-ordered, never blindly dropped |
| Granularity switch | ❌ none (single mode) | ✅ auto (parent count + token budget) |
| Eval / measurement | ❌ harness unused | ✅ bench run before/after |
| Doc quality | ⚠️ hand-written, inconsistent | ➡️ code-derived generation (§5.1) |
