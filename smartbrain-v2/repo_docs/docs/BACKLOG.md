# repo_docs backlog: deferred work

These were skipped on 2026-10-11 to save tokens. Each item lists what it is, why it matters, how to run it, and the expected cost. Pick them up in this order unless priorities change.
Paths are relative to `smartbrain-v2/repo_docs/` (RD).

| # | Item | Value | LLM? | Est. effort |
|---|---|---|---|---|
| 1 | Endpoint purpose lines | High for search | Yes (light) | ~0.5M tokens |
| 2 | Auth per endpoint from global security config | Medium | No | 1 coder run (~30 min) |
| 3 | Env-var purpose from key names | Medium | No | Same run as 2 |
| 4 | Doc polish: flow wording, split "+N more", versions | Medium | No | 1 coder run (~20 min) |
| 5 | Phase 3 gap-fill agents (remaining real gaps) | Medium | Yes | ~2-3 h of agents |
| 6 | Unresolved topic names / base URLs (deploy-time values) | High for graph | No (needs user input) | Minutes once values are known |
| 7 | Team nicknames (manual aliases) | High for search | No | Minutes |
| 8 | More orgs (TVSM-DMS etc.) | High | Pipeline cost | Per org |
| 9 | Low-priority review findings | Low | No | Small |
| 10 | Freshness automation (webhook/nightly) | Medium | No | 0.5-1 d |

## 1. Endpoint purpose lines (Unknown -> inferred one-liners)
- **Problem:** 464 of ~990 endpoints say `Purpose: Unknown` in API_SPEC.md. Natural-language search ("how do admins see dealers pending verification") ranks field tables poorly.
- **Do:** write one line per endpoint from the method name, route, DTO fields/enums and handler body. Mark it `source: inferred`. Write it to `config/endpoint_purposes.yaml` (user-editable). `generate` merges it into service.yaml and API_SPEC.md. Vague handlers get "Unclear from code".
- **How:** pilot on `tvsmbe-location` (~45 endpoints) first, then everything else. Cheapest option: a script that calls Azure OpenAI from `../.env`, batching 20 endpoints per call. Alternative: a Kiro agent on Auto.
- **Cost:** ~370k input + ~20k output tokens (plus ~100-200k agent overhead if Kiro is used).

## 2. Auth per endpoint (388 `Auth: Unknown`)
- Derive per-endpoint auth from global config: Spring Security `SecurityFilterChain`/`permitAll` matchers, Nest global guards, ASP.NET `[Authorize]` defaults / `RequireAuthorization`, plus `[AllowAnonymous]` exceptions. Deterministic, `confidence: medium`.

## 3. Env-var purpose (~1,200 rows `Purpose: Unknown`)
- Infer the purpose from the key name and how it is used: `*_URL` -> "Base URL of <resolved service>", `*_TOPIC*` -> "Service Bus topic name", `*_SUBSCRIPTION*`, `*CONNECTION*` -> "connection (secret)", `*_KEY/SECRET/TOKEN` -> "credential (secret)". Use edges.json to name the target service. Mark as `inferred`.

## 4. Doc polish (deterministic)
- Label flows as "possible path (derived from the call graph)". They chain verified hops, but a single user action is not proven to trigger the whole chain.
- Split the DATA_FLOWS step rows that say "(+N more)" into one row per endpoint.
- Fill the Tech Stack "Version" column from pom/package.json/csproj dependency items that are already extracted.

## 5. Phase 3 gap-fill (targeted)
- See `config/phase3.yaml`. Investigate only `silent_client_file`, `missing_payload`, `unresolved_entity`, `unresolved_base_url` and `unknown_repo_type`. Skip TVS-CPS-PORTAL. Each agent writes `runs/<org>/<repo>/llm_notes.json` (validated, with file:line evidence). Prompt: `prompts/repo_agent.md`.
- Current gap totals: `.agents/tasks/phase4/stabilize.md` and `runs/*/*/gaps.json`.

## 6. Values only known at deploy time (graph completeness)
- 16 messaging entities read their topic name from env vars or Key Vault (booking-crud-services, async-communication-service, Price-Engine, Catalog-Scheduler, BS2.0 QueueDispatcher, tvs-cps-be-base-framework Kafka). tvsm-marketplace-service has placeholder topic names `xxx`/`xxxx`.
- 331 HTTP calls are unresolved and 51 have candidates: `.agents/tasks/phase4/resolve-report.md`.
- **Do:** ask the owning teams for prod values. Record them as user-confirmed notes, like the `lms` -> `lead` topic in `runs/TVS-CS/lms*/llm_notes.json`. Then run `resolve`, `flows`, `generate`.
- Also note for the LMS team: appsettings say `TOPIC_NAME: "lms"`, but production is reportedly `lead`.

## 7. Team nicknames
- Add them to `config/aliases.manual.yaml` (e.g. `bs: [booking-crud-services]`, `mdp: [master-data-platform]`), then run `aliases`, `generate` and re-ingest. This also resolves the 16 ambiguous aliases listed in `.agents/tasks/phase5/aliases-report.md`.

## 8. More orgs
- The TVSM-DMS entry exists in `config/orgs.yaml` but is `enabled: false`. The token could not see the org: fix the fine-grained token resource owner / admin approval / membership. Then set `enabled: true`, fill `config/repos/TVSM-DMS.txt`, and run discover -> clone -> ledger -> extract -> resolve -> flows -> aliases -> generate -> docs (`prompts/repo_agent.md`) -> verify -> re-ingest.
- **Security:** revoke the two tokens pasted in chat on 2026-10-11 (one classic token with admin scopes, one fine-grained `github_pat_...`).

## 9. Low-priority review findings
- Phase 4: bare-path matches labelled `high`, missing tests for the fix-pass behaviours, a stale comment (`.agents/tasks/phase4/resolve-review.md`).
- Contract-only inbound items from SwaggerHub mock `servers` paths (appointment-booking-service): ignore them in matching.
- Evidence snippets over-redact `@Value("${...}")` as `***`. This is safe but noisy.
- The `_:_` data-store bucket was deliberately left.
- `verify --org` now takes minutes because of the 218 flows. Optimize if it becomes a problem.

## 10. Freshness
- Repos marked stale are already detected by SHA/version. Add a nightly job or a GitHub webhook that runs clone -> ledger -> extract -> resolve -> flows -> aliases -> generate -> verify -> incremental ingest, and re-runs the doc agent only for repos whose inventory changed.
