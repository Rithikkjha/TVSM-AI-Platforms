# Graph Gap Re-Retrieval — Design & Examples

## What It Is

After the initial retrieval + re-ranking gives us top-5 chunks, and after Neo4j graph expansion reveals related entities — we check: **is there a related entity that the graph says is connected, but we have NO chunk text for?**

If yes AND the missing entity has content relevant to the question → fetch one chunk from it. This fills gaps where the answer spans multiple services.

---

## When It Fires (and When It Doesn't)

| Scenario | Does it fire? | Why |
|---|---|---|
| Simple lookup: "What DB does booking use?" | ❌ No | All chunks are from booking-crud. Graph shows payment-service is connected, but a "database" query against payment-service scores 0.31 (low). Threshold not met. |
| Cross-service: "How does booking cancellation work?" | ✅ Yes | Chunks are from booking-crud. Graph shows payment-service. Searching payment-service for "cancellation" scores 0.78 (high). The refund detail is relevant! |
| Already covered: "Compare booking and payment databases" | ❌ No | Initial retrieval already found chunks from BOTH services (the question mentions both). No gap exists. |

---

## The Logic (Pseudocode)

```python
# After step 5 (cross-encoder re-rank) and step 6 (graph expansion):

# 1. What entities did the graph find?
graph_entity_ids = set()
for neighbor in graph_neighbors:
    graph_entity_ids.add(neighbor["source_id"])
# e.g. {"service:payment-service", "service:notification-service"}

# 2. What entities do our top-5 chunks already cover?
covered_by_chunks = set()
for chunk in top_chunks:
    covered_by_chunks.add(chunk.parent_source_id)
# e.g. {"steering:booking-crud-services:tech", "steering:booking-crud-services:structure"}
# → All from booking-crud-services

# 3. Find the gap
uncovered_services = set()
for entity_id in graph_entity_ids:
    # Extract repo/service name from source_id
    if entity_id.startswith("service:"):
        service_name = entity_id.replace("service:", "")
        # Check if ANY chunk from this service is already in our top-5
        if not any(service_name in c.parent_source_id for c in top_chunks):
            uncovered_services.add(service_name)

# 4. Re-retrieve ONLY if there's a gap (max 3 to bound latency)
for service_name in list(uncovered_services)[:3]:
    extra_hit = await vector_store.search(
        query_vector=query_vector,  # SAME vector, no extra embedding call
        filters={"repo_name": service_name},
        entity_type="Chunk",
        limit=1,
    )
    
    if extra_hit and extra_hit[0].score > 0.7:
        # This chunk is relevant to the question — add it
        top_chunks.append(extra_hit[0])
    else:
        # Not relevant to this specific question — skip
        pass
```

---

## Detailed Example: "How does booking cancellation work?"

### Before re-retrieval (what we have):

```
Top-5 chunks (all from booking-crud-services):
  [ref:1] "Cancellation: cancellationSource, cancellationReason, cancellationSubReason"
  [ref:2] "PUT /bookings/cancel endpoint"
  [ref:3] "Cancellation can occur at any lifecycle stage"
  [ref:4] "Booking Status: Reserved → Confirmed → Delivered (or Cancelled)"
  [ref:5] "Refund: cancellationFee, refundAmount, customerRemarks"

Graph neighbors:
  → service:payment-service (via DEPENDS_ON edge)
  → service:notification-service (via DEPENDS_ON edge)
```

### Gap detection:

```
graph_entities = {"service:payment-service", "service:notification-service"}
covered = all chunks from booking-crud → payment NOT covered, notification NOT covered
uncovered = {"payment-service", "notification-service"}
```

### Re-retrieval for each uncovered service:

```
Search Qdrant: query="How does booking cancellation work?" + filter=repo_name:"payment-service"
  → Best chunk: "When a booking is cancelled, the refund is processed through CCAvenue..."
  → Score: 0.78
  → 0.78 > 0.7 → ✅ ADD THIS CHUNK

Search Qdrant: query="How does booking cancellation work?" + filter=repo_name:"notification-service"
  → Best chunk: "Notification templates: booking_confirmed, payment_received, delivery_scheduled..."
  → Score: 0.42
  → 0.42 < 0.7 → ❌ SKIP (notification templates aren't about cancellation)
```

### After re-retrieval (what we now have):

```
  [ref:1] "Cancellation: cancellationSource, cancellationReason..."
  [ref:2] "PUT /bookings/cancel endpoint"
  [ref:3] "Cancellation can occur at any lifecycle stage"
  [ref:4] "Booking Status: Reserved → Confirmed → Delivered (or Cancelled)"
  [ref:5] "Refund: cancellationFee, refundAmount, customerRemarks"
  [ref:6] "payment-service: When a booking is cancelled, refund through CCAvenue..." ← NEW
```

### LLM answer comparison:

**Without re-retrieval:**
> "Booking cancellation is triggered via PUT /bookings/cancel [ref:2]. It requires a cancellationSource and cancellationReason [ref:1]. A refundAmount is tracked in the booking record [ref:5]."

**With re-retrieval:**
> "Booking cancellation is triggered via PUT /bookings/cancel [ref:2]. It requires a cancellationSource and cancellationReason [ref:1]. A refundAmount is tracked [ref:5], and the **refund is processed through the CCAvenue payment gateway with 3-5 day settlement** [ref:6]."

The extra chunk gave the LLM the actual refund mechanism — information that only exists in payment-service's docs.

---

## Example: When It DOESN'T Fire

**Question:** "What database does booking-crud-services use?"

```
Top-5 chunks: all from booking-crud/tech.md (Database section, Dependencies section, etc.)

Graph neighbors: payment-service, notification-service

Gap check:
  uncovered = {"payment-service", "notification-service"}

Re-retrieval:
  Search payment-service for "What database does booking-crud use?"
  → Best chunk: "Payment gateway integration with CCAvenue and JUSPAY..."
  → Score: 0.31
  → 0.31 < 0.7 → SKIP

  Search notification-service for "What database does booking-crud use?"
  → Best chunk: "Notification templates stored in MongoDB..."
  → Score: 0.35
  → 0.35 < 0.7 → SKIP

Result: No re-retrieval happens. Zero extra cost.
The question is specifically about booking's database — other services' databases aren't relevant.
```

---

## Cost Analysis

| Scenario | Extra Qdrant calls | Extra latency | Extra tokens |
|---|---|---|---|
| No gap (all chunks from same service that graph mentions) | 0 | 0ms | 0 |
| Gap exists, but score < 0.7 for all | 1-3 calls | 50-150ms | 0 (nothing added) |
| Gap exists, 1 chunk scores > 0.7 | 1-3 calls | 50-150ms | +200-500 tokens to LLM |
| Gap exists, 3 chunks score > 0.7 | 3 calls | 150ms | +600-1500 tokens to LLM |

**Worst case:** 3 extra Qdrant lookups (150ms) + 1500 extra tokens (~$0.003). Negligible.
**Common case:** 0 extra calls (question is about one service and graph neighbors aren't relevant).

---

## Configuration

| Setting | Default | What it controls |
|---|---|---|
| `GRAPH_GAP_ENABLED` | `true` | Toggle the feature on/off |
| `GRAPH_GAP_SCORE_THRESHOLD` | `0.7` | Minimum cosine score to include a re-retrieved chunk |
| `GRAPH_GAP_MAX_ENTITIES` | `3` | Maximum number of uncovered entities to check |

---

## Where It Sits in the Pipeline

```
Step 1-3: Cache checks + embed question
Step 4:   Hybrid retrieval → top-30
Step 5:   Cross-encoder re-rank → top-5
Step 6:   Graph expansion (Neo4j 1-2 hops)
Step 6.5: ★ GRAPH GAP RE-RETRIEVAL ★    ← HERE
            → Detect uncovered entities
            → Re-retrieve relevant chunks
            → Add to top-5 (becomes top-6, top-7, max top-8)
Step 7:   Citation context assembly
Step 8:   LLM call
...
```

---

## Summary

- **What:** After graph expansion, if a related service has no chunks in our context, try to fetch one.
- **When it fires:** Only when the graph says entity X is connected AND Qdrant confirms X has a chunk relevant (score > 0.7) to THIS specific question.
- **When it doesn't fire:** Most single-service questions. Irrelevant neighbors. Already-covered services.
- **Cost:** Usually zero. Worst case: 150ms + $0.003. Bounded by max 3 extra lookups.
- **Benefit:** Cross-service questions get complete answers (e.g., cancellation flow includes the refund mechanism from payment-service).
