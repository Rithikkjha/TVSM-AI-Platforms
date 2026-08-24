# Engineering Memory Graph — Context Enrichment Plan

## Vision

```
Static Analysis    +    Runtime Telemetry    +    Human Feedback Loops
      ↓                       ↓                         ↓
                    KNOWLEDGE GRAPH
                         ↓
                    AI REASONING
```

Three data sources feed the graph. Each fills gaps the others can't.
The AI reasons over all three, weighting answers by confidence and evidence count.

---

## Current State (V1 Baseline)

| What we have | Source | Accuracy |
|---|---|---|
| Service names + repo metadata | GitHub API | ✅ 100% |
| CODEOWNERS → team ownership | GitHub API | ✅ where file exists (~30% of repos) |
| Last 30 PRs per repo | GitHub API | ✅ 100% |
| Jira tickets + epics | Jira API | ✅ 100% |
| Confluence pages | Confluence API | ✅ 100% |
| DEPENDS_ON edges | LLM extraction from Confluence prose | ⚠️ ~60% (hallucination-prone) |
| Steering files (service summaries) | LLM-generated from README + tree + key files | ⚠️ ~80% |
| Vector embeddings | Steering files + key files + tickets + pages | ✅ searchable |

**Key gaps:**
- No API endpoint data (what does each service expose?)
- No inter-service call data (who calls whom?)
- No service bus topology (who publishes/subscribes to what?)
- No build dependency data (shared libraries, packages)
- Ownership missing for ~70% of repos
- No way to correct wrong answers
- No runtime validation of static claims

---

## Phases Overview

| Phase | What | Accuracy Target | Cost | Time |
|---|---|---|---|---|
| **Phase 1** | Static code analysis + team review | ~90-92% | $0 ongoing | 2-3 weeks |
| **Phase 2** | Human feedback & corrections | ~95% | $0 ongoing | 1-2 weeks |
| **Phase 3** | Runtime telemetry validation | ~97-98% | Azure Monitor costs | 4-6 weeks |

Each phase builds on the previous. Phase 1 is the foundation.

---

## Phase 1: Static Analysis

Scan all repos, extract structured facts from code, feed into graph deterministically.

**Detailed plan:** [docs/PHASE_1_STATIC_ANALYSIS.md](./PHASE_1_STATIC_ANALYSIS.md)

---

## Phase 2: Human Feedback Loops

Let users correct wrong answers. Corrections feed back into the graph over time.

**Key features:**
- 👍/👎 on chatbot answers
- "This is wrong" correction flow
- "Add missing dependency" form
- Confidence decay (unverified edges degrade over time)

**Detailed plan:** `docs/PHASE_2_HUMAN_FEEDBACK.md` (to be created)

---

## Phase 3: Runtime Telemetry

Ingest actual API call traces and service bus message flows to validate/discover dependencies.

**Data sources:**
- Azure Application Insights (HTTP traces between services)
- Azure Service Bus metrics (message counts, publisher/subscriber identity)
- Azure API Management (full API call logs)

**Key value:**
- Validates static analysis claims ("yes, this dependency is real")
- Discovers hidden dependencies (Key Vault topics, dynamic routing)
- Identifies dead code (endpoint exists but 0 calls in 30 days)
- Enables blast radius with real traffic data

**Detailed plan:** `docs/PHASE_3_RUNTIME_TELEMETRY.md` (to be created)
