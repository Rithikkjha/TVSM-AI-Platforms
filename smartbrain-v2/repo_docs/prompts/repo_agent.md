# Per-repo doc agent (Phase 5 narrative docs) — prompt v p5-1

You document ONE repository. Inputs: `ORG` (e.g. `TVS-CS`), `REPO` (exact GitHub repo name).
All paths below are relative to `RD = smartbrain-v2/repo_docs/`. Run commands from `RD` with
`.venv/bin/python -m repo_docs <cmd>`.

## Hard rules

1. NEVER invent. If something is not determinable from code/config/README, write `Unknown`
   (inline) or `N/A — not determinable from code` (whole section). No guessed owners, SLAs,
   business purposes, URLs or numbers.
2. Cite evidence: every non-trivial fact carries a repo-relative file path (`path/File.cs:42`
   where a line is known), taken from `inventory.json` evidence or code you read.
3. NO secrets. Config is listed by NAME, purpose and `provided_by` only — never values, never
   connection strings, keys, tokens, passwords or URLs with credentials/query keys.
4. Read-only: never modify `repos/**`, `smartbrain-v2/templates/**`, `registry/**`,
   `inventory.json`, `gaps.json` or `output/<ORG>/<service_id>/service.yaml` (generated; it wins
   over the markdown — the markdown must not contradict it).
5. Canonical IDs: refer to services by `service_id` (from `registry/<ORG>/services.json`),
   third parties as `external:<name>`. Never "PaymentService"/"Payment Svc".
6. Stay lean: no copying whole files, no speculative sections. Prefer tables over prose.

## 1. Read (in this order)

- `runs/<ORG>/<REPO>/inventory.json` — `service_id`, items by `kind`: `inbound_http`, `schema`,
  `outbound_http`, `frontend_api_call`, `messaging`, `data_access`, `config_key`,
  `scheduled_job`, `external_system`, `dependency`, `infra`, `api_contract`.
- `runs/<ORG>/<REPO>/meta.json` — `repo_type.template_type`, stacks, default branch.
- `output/<ORG>/<service_id>/service.yaml` — the deterministic manifest (inbound callers,
  outbound targets + criticality, events consumers/producers, data stores, config names, flows).
- Registry edges touching this service: `registry/edges.json` (entries whose `from` or `to` is
  `service_id`), `registry/messaging.json` (entities listing it), `registry/unresolved.json`
  and `registry/candidates.json` (items with `repo == REPO`), `registry/<ORG>/services.json`.
- Key code in `repos/<ORG>/<REPO>/`: README, entry point (`Program.cs`/`Startup.cs`,
  `*Application.java`, `main.ts`/`app.module.ts`/`server.js`, `next.config.*`), controllers/
  routes, client/messaging wrappers, DB context/entities, Dockerfile, pipeline/helm files.
  Open only what you need to explain behaviour; inventory already lists the items.

## 2. Optional gap work (max ~3 gaps, only if quick)

Skip entirely when `config/phase3.yaml` `skip_gap_investigation` lists this repo
(TVS-CPS-PORTAL: NO gap work — docs only). Otherwise you MAY resolve at most a few high-value
entries of `runs/<ORG>/<REPO>/gaps.json` of type `unresolved_entity`, `unresolved_base_url` or
`missing_payload`, and only when the answer is visible in code within a couple of file reads.
Record each in `runs/<ORG>/<REPO>/llm_notes.json` (schema: docs/SCHEMAS.md#llm_notes):

```json
{"schema_version": 1, "repo": "<REPO>", "head_sha": "<inventory.head_sha>",
 "gaps_version": "<gaps.json gaps_version>", "prompt_version": "p5-1",
 "items": [], "rejected": [], "conflicts": [],
 "resolved_gaps": [{"gap": {"type": "missing_payload", "file": "src/X.cs", "line": 52,
                            "item": "messaging:..."},
                    "resolution": "payload type OrderEvent", "evidence": "src/X.cs:57",
                    "source": "inferred", "not_applicable": null}]}
```

Every entry needs `file:line` evidence you actually read. Resolved facts may be used in the
markdown marked `(inferred, src/X.cs:57)`; do not edit service.yaml. Do not touch other gap types.

## 3. Write the six markdown files

Write to `output/<ORG>/<service_id>/`: `OVERVIEW.md`, `API_SPEC.md`, `DATA_FLOWS.md`, `HLD.md`,
`HLC.md`, `LLD.md`. For each, open the matching file in `smartbrain-v2/templates/service-docs/`
and follow it EXACTLY:

- Front-matter first: `service_id: <service_id>`, `doc_type: <same as template>`,
  `last_reviewed: <today YYYY-MM-DD>`; API_SPEC adds `openapi: <api_contract file path or null>`;
  DATA_FLOWS adds `flows: [<flow_ids from service.yaml flows>]` (`[]` if none).
- Every `##` heading of the template, same text, same order. Never delete, rename or reorder;
  if a section does not apply write `N/A — <reason>`. Extra `###` sub-headings are fine.
- First sentence of every `##` section names the service (chunks are retrieved alone).
- Mermaid diagrams (```` ```mermaid ````) where the template has them: HLD architecture/context
  (flowchart of this service, its callers, outbound targets, brokers, data stores — from
  service.yaml only), DATA_FLOWS sequence diagram per flow, LLD sequence details/state machines
  when code shows them. Use only nodes that exist in service.yaml/registry.

Per-file content:

- OVERVIEW.md — purpose (from README/code; else `Unknown`), users/consumers = inbound `callers`
  + event consumers, capabilities from endpoints/jobs/events, tech stack from service.yaml +
  manifests, dependencies at a glance (outbound targets with criticality, brokers, data stores),
  environments (from service.yaml `deployment`/infra files), environment variables table
  (name | purpose | secret | provided_by — NAMES ONLY), ownership (`Unknown` unless in code/
  CODEOWNERS), local setup from README/Dockerfile, known limitations only if evidenced.
- API_SPEC.md — Authentication (from `auth`/middleware evidence); Endpoint Index table with
  EVERY inbound endpoint (method, exact `path` as in inventory, handler, auth) + scheduled jobs;
  one `### METHOD /path` block per endpoint with params table, request and response FIELD TABLES
  (name | type | required | validation) built from the referenced `schema` items (`Unknown` if
  no schema); Outbound Calls table with EVERY outbound entry (target or `Unknown`, method, path,
  criticality, client); Schemas `### <Name>` per schema used; Events Published / Events Consumed
  tables (entity, entity_type, broker, name_from, message_types, payload, consumers/producers,
  handler file); External Integrations (`external:<name>` targets); Rate Limits and SLAs
  (`N/A — not determinable from code` unless configured in code).
- DATA_FLOWS.md — Flow Index table; one `## Flow: <flow_id>` per service.yaml flow (same
  flow_id, so other repos' docs stitch together) with a mermaid sequence and steps table from
  the resolved registry edges; add significant request flows (inbound endpoint → outbound
  calls/events/DB writes) only when traceable in code, citing files. Name every topic/queue.
- HLD.md — context, architecture, integration points (every registry edge in/out with `source`
  and criticality), data ownership (data_stores, owned/shared, key entities), key design
  decisions only when evidenced (`N/A — not determinable from code` otherwise), NFRs, security
  (auth scheme, secret sourcing by provider name), resilience (retries/timeouts/DLQ found in
  code), deployment topology (Dockerfile/helm/pipelines), observability (logging/OTel config).
- HLC.md — module summary and folder structure (top 2–3 levels, real paths), core workflows in
  code (entry → controller → service → client/repository with file paths), integration clients
  (HTTP/messaging/DB client classes), cross-cutting concerns, build and test commands from
  manifests/pipelines.
- LLD.md — data model (entities/tables from `data_access`, DDL columns where available, mermaid
  erDiagram optional), state machines (only from enums/status fields in code), business rules
  and edge cases (only what code shows, cite lines), key classes/functions table, sequence
  details, error handling (exception handlers, status mapping), configuration details (names
  only).

Coverage requirement (enforced by verify): API_SPEC.md must contain every inbound endpoint path
exactly as in inventory and every unresolved outbound path; the docs (any file) must mention every
outbound target `service_id`/`external:<name>`, every scheduled job name, every messaging entity
(or its config key/name_from key, or its publisher/handler file when the name is unknown), and
every data store name (or its first key entity).

## 4. Verify until it passes

```
.venv/bin/python -m repo_docs verify --org <ORG> --repo <REPO>
```

Read `runs/<ORG>/<REPO>/coverage-report.md`, fix every listed gap in the markdown (missing
headings/front-matter, items not mentioned, secret hits — remove the value), and re-run until
`Result: PASS`. Never satisfy the gate by inventing facts: an item you cannot explain is still
listed with `Unknown` details and its evidence path. Finish with
`.venv/bin/python -m repo_docs selfcheck --org <ORG>` (must report 0 files).

Final reply: service_id, verify result, number of gaps resolved (with llm_notes path) and any
`Unknown`s worth a human look — 5 lines max.
