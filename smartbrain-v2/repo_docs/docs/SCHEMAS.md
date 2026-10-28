# repo_docs schemas

All files are UTF-8 JSON (`indent=2`), written atomically (temp file + `fsync` + `os.replace`).
Timestamps are UTC ISO-8601 with `Z`. Every file carries `schema_version: 1`. Paths are relative to
`repo_docs/`. Files marked **planned** are not produced yet; the shape is the contract later phases
must implement. No file may ever contain a token or secret value.

Contents: [config/orgs.yaml](#configorgsyaml) · [allowlist](#configreposorgtxt-allowlist) ·
[service_id rules](#service_id-rules) · [state.json](#statestatejson) · [repos.json](#runsorgreposjson) ·
[meta.json](#runsorgrepometajson) · [ledger.json](#runsorgrepoledgerjson) ·
[inventory.json](#runsorgrepoinventoryjson) · [item kinds](#item-kinds-and-attributes) ·
[template mapping](#inventory--template-mapping) · [config classifier](#config-value-classifier) ·
[external_systems.yaml](#registryexternal_systemsyaml) ·
[gaps.json](#runsorgrepogapsjson) · [llm_notes.json (planned)](#runsorgrepollm_notesjson-planned) · [registry (planned)](#registry-files-planned) ·
[output (planned)](#outputorgservice-id-planned) · [coverage/review (planned)](#coverage-and-review-files-planned) ·
[eval (planned)](#evalquestionsyaml-planned)

## config/orgs.yaml

```yaml
schema_version: 1
defaults:
  workers: 5            # parallel repos per command
  max_retries: 4        # retries after first failure; backoff 2,4,8,16 s (+jitter)
  max_file_bytes: 1000000
  clone_depth: 1
orgs:
  - name: TVS-CS                      # GitHub org login (required)
    enabled: true
    token_env_file: ../.env           # required; relative to repo_docs/ or absolute
    token_key: GITHUB_TOKEN           # required; KEY in that file
    api_base: https://api.github.com
    git_base: https://github.com
    include: ["*"]                    # fnmatch (case-sensitive) on repo name
    exclude: []
    include_archived: true
    allowlist: config/repos/TVS-CS.txt   # optional
    service_id_overrides: {}             # optional {RepoName: service-id}
    self_repos: [tvsm-brain]             # → self: true
    # optional per-org overrides of defaults: workers, max_retries, max_file_bytes, clone_depth
```
A repo is registered iff it is in the allowlist (when set) AND matches any `include` AND no `exclude`
AND (`include_archived` or not archived). Invalid config → `ConfigError` naming the field.
Only the repo's **default branch** is ever cloned or documented (agreed decision, see
[PIPELINE.md#decisions](PIPELINE.md#decisions)).

Planned optional keys (read by phases 2–4; absent = default):
```yaml
    internal_package_patterns: ["com.tvs.*", "com.tvsmotor.*", "@tvs/*"]   # phase 2: flag internal libs early
    submodule_exempt: {}            # phase 6: {path: reason} for submodules whose target is not registered
llm_scan:                           # phase 3 (top level, planned): targeted gap-fill agent (Option B)
  prompt_version: p3b-1             # agent brief version; a bump makes llm_scan stale
```

## config/repos/<org>.txt (allowlist)

One exact GitHub repo name per line (case-sensitive). `#` starts a comment (full-line or trailing);
whitespace stripped; blank lines ignored.
```
AUDIT-SERVICE                # empty
PaymentService
```

## service_id rules

`repo` = exact GitHub name (state key, `repos/<org>/<repo>`, `runs/<org>/<repo>`).
`service_id` = canonical lowercase kebab used in docs/graph (`output/<org>/<service-id>`):

1. insert `-` at camelCase boundaries `([a-z0-9])([A-Z])` and `([A-Z]+)([A-Z][a-z])`
2. lowercase
3. every run of non-`[a-z0-9]` → `-`
4. collapse repeated `-`, trim leading/trailing `-`

| repo | service_id |
|---|---|
| `TVS-CPS-BACKEND` | `tvs-cps-backend` |
| `BS2.0Backend_Integration` | `bs2-0-backend-integration` |
| `PaymentService` | `payment-service` (base) |
| `tvsm-location-FE` | `tvsm-location-fe` |
| `Catalog-Microservice-Backend-for-Frontend-Layer` | `catalog-microservice-backend-for-frontend-layer` |

**Overrides** (`service_id_overrides`) are applied first and must be unique.
**Collisions** inside one org (several repos → same id): repos are never merged. The repo whose
`name.lower()` equals the base id keeps it; every other colliding repo (or all, if none equals) gets
`<base>-<first 6 hex of sha1(repo)>`. All colliding repos get `service_id_collision: true`; `discover`
logs a WARNING and `status` lists them. Real case in TVS-CS: `Payment-Service` (empty) →
`payment-service`; `PaymentService` (C#) → `payment-service-<hash6>`. Use `service_id_overrides` to pick
names manually.

## state/state.json

Master tracker. Mutated only inside `StateStore.transaction()` (thread lock + `fcntl.flock` on
`state/state.lock`, re-read, mutate, atomic write), so concurrent processes never lose updates.

```json
{
  "schema_version": 1,
  "updated_at": "2025-10-10T16:00:00Z",
  "orgs": {
    "TVS-CS": {
      "discovered_at": "2025-10-10T15:00:00Z",
      "api_repo_count": 161,
      "repo_count": 46,
      "allowlist_missing": [],
      "service_id_collisions": ["Payment-Service", "PaymentService"],
      "repos": {
        "PaymentService": {
          "service_id": "payment-service-1a2b3c",
          "service_id_collision": true,
          "default_branch": "main",
          "language": "C#",
          "size_kb": 1234,
          "archived": false,
          "empty": false,
          "self": false,
          "pushed_at": "2025-09-01T10:00:00Z",
          "html_url": "https://github.com/TVS-CS/PaymentService",
          "remote_sha": "3f2c…",
          "head_sha": "3f2c…",
          "stacks": ["dotnet"],
          "phases": {
            "clone": {"status": "done", "version": "0.1.0", "input_sha": null, "output_sha": "3f2c…",
                      "started_at": "…Z", "finished_at": "…Z", "attempts": 1,
                      "error": null, "skip_reason": null},
            "ledger": {"status": "done", "version": "0.1.0", "input_sha": "3f2c…",
                       "started_at": "…Z", "finished_at": "…Z", "attempts": 1,
                       "error": null, "skip_reason": null,
                       "counts": {"total": 420, "pending": 380, "skipped": 40, "failed": 0}},
            "extract": {"status": "done", "version": "0.1.2+9c1e4b7a2d10", "input_sha": "3f2c…",
                        "ledger_generated_at": "…Z",
                        "extractor_versions": {"dotnet.aspnet": "0.1.0", "shared.config": "0.1.0",
                                               "shared.infra": "0.1.0", "shared.manifests": "0.1.0"},
                        "registry_hash": "5be0…",
                        "started_at": "…Z", "finished_at": "…Z", "attempts": 1,
                        "error": null, "skip_reason": null, "missing_extractors": [],
                        "counts": {"items": 212, "files_extracted": 31, "files_partial": 140,
                                   "files_untouched": 209, "file_errors": 0,
                                   "by_kind": {"inbound_http": 18, "schema": 40, "config_key": 55}},
                        "gaps": {"unresolved_base_url": 1, "unresolved_entity": 0,
                                 "missing_payload": 2, "missing_schema": 3, "partial_parse": 4,
                                 "silent_client_file": 1, "untouched_source": 0,
                                 "untouched_file": 0, "unknown_repo_type": 0}}
          }
        }
      }
    }
  }
}
```

| Field | Meaning |
|---|---|
| `phases.<key>` | key ∈ `clone, ledger, extract, llm_scan, resolve, generate, verify, review, ingest` |
| `status` (stored) | `pending \| running \| done \| failed \| skipped` |
| effective `stale` | derived, never stored: `done` but `input_sha != head_sha` (non-clone phases), `version != current`, or (extract) `ledger_generated_at != ledger.json generated_at` |
| `version` | phase version (`PHASE_VERSION`); for `extract` the composite `"<PHASE_VERSION>+<h12>"`, `h12` = first 12 hex of `sha1(",".join(sorted("<id>@<ver>")) + "|" + registry_hash)` over the extractors that applied |
| `extractor_versions` | (extract) human-readable `{extractor_id: extractor_version}` behind the composite |
| `registry_hash` | (extract) sha1 of `registry/external_systems.yaml` bytes |
| `input_sha` | repo `head_sha` the phase consumed |
| `output_sha` | (clone) HEAD after clone/refresh |
| `attempts` | number of runs that started this unit |
| `error` | text passed through `secrets.redact(…, SecretFilter.secrets())` **before** it is stored or logged, ≤2000 chars (all phases) |
| `skip_reason` | e.g. `empty` |
| `running` | left behind by a crash → treated as needing work |
| `counts` | (ledger) `total`, `pending`, `skipped` (all `skipped:*`), `failed` (all `failed:*`); (extract) see example |
| `missing_extractors` | (extract) detected stacks whose extractor is still a planned stub; their files stay `pending` |
| `gaps` | (extract) `gaps.json` count per gap type ([gaps.json](#runsorgrepogapsjson)) |

Empty repo example (both phases skipped, mirrored by `ledger`):
```json
"Payment-Service": {"service_id": "payment-service", "service_id_collision": true, "empty": true,
  "head_sha": null, "phases": {
    "clone":  {"status": "skipped", "version": "0.1.0", "skip_reason": "empty", "attempts": 1, "…": null},
    "ledger": {"status": "skipped", "version": "0.1.0", "skip_reason": "empty", "attempts": 0, "…": null}}}
```
A repo is only `skipped(empty)` after `clone` has confirmed with `git ls-remote` that the remote has no
refs (see [repos.json](#runsorgreposjson)). `status` reports phases with no record yet as `pending`.

## runs/<org>/repos.json

Full discovery snapshot (all org repos, not only allowlisted).
```json
{
  "schema_version": 1, "org": "TVS-CS", "fetched_at": "…Z", "count": 161,
  "allowlist_missing": [],
  "repos": [
    {"name": "PaymentService", "full_name": "TVS-CS/PaymentService", "default_branch": "main",
     "language": "C#", "size_kb": 1234, "archived": false, "empty": false,
     "pushed_at": "…Z", "html_url": "https://github.com/TVS-CS/PaymentService",
     "self": false, "allowlisted": true, "registered": true,
     "service_id": "payment-service-1a2b3c"}
  ]
}
```
`empty = size_kb == 0` here is only the **GitHub API hint** (GitHub computes `size` lazily, so a repo with
commits can still report 0). It is never trusted alone: `clone` always runs `git ls-remote --heads` for a
repo flagged empty and marks it `skipped(empty)` only when the remote has no refs at all. If refs exist,
the flag is cleared (`empty: false`) and the repo is cloned normally. `service_id` is set only for
registered repos (else `null`).

## runs/<org>/<repo>/meta.json

Written by phase 0; phase 1 merges the `ledger` block, phase 2 merges `repo_type` and `extract`
(read-modify-write, atomic).
```json
{
  "schema_version": 1, "org": "TVS-CS", "repo": "PaymentService",
  "service_id": "payment-service-1a2b3c", "service_id_collision": true, "self": false,
  "default_branch": "main", "head_sha": "3f2c…", "html_url": "https://github.com/TVS-CS/PaymentService",
  "language": "C#", "archived": false,
  "clone": {"path": "repos/TVS-CS/PaymentService", "depth": 1, "cloned_at": "…Z", "phase_version": "0.1.0"},
  "stacks": [
    {"stack": "dotnet", "subproject": "src/Payment.Api", "evidence": ["src/Payment.Api/Payment.Api.csproj"]},
    {"stack": "angular", "subproject": "web", "evidence": ["web/angular.json"]},
    {"stack": "node", "subproject": "web", "evidence": ["web/package.json"]}
  ],
  "stack_ids": ["angular", "dotnet", "node"],
  "ledger": {
    "phase_version": "0.1.0", "generated_at": "…Z",
    "git_ls_files_count": 420, "ledger_count": 420, "self_check": "pass",
    "by_class": {"source": 300, "config": 20, "build_manifest": 4, "vendor": 30, "binary": 10, "…": 0},
    "by_status": {"pending": 380, "skipped:vendor": 30, "skipped:binary": 10},
    "by_language": {"csharp": 280, "json": 18},
    "secret_risk_files": [".env"]
  },
  "repo_type": {
    "value": "service",
    "template_type": "backend-api",
    "rules_fired": ["inbound_http>0"],
    "evidence": [{"file": "src/Payment.Api/Program.cs", "line": 9,
                  "snippet": "var app = builder.Build();"}],
    "subprojects": {"src/Payment.Api": "service", "web": "frontend"}
  },
  "extract": {"phase_version": "0.1.2", "version": "0.1.2+9c1e4b7a2d10",
              "items": 212, "files_extracted": 31, "files_partial": 140, "files_untouched": 209,
              "gaps": 11}
}
```
`meta.ledger` stays the phase-1 snapshot (its `by_status` is not rewritten by later phases); current
per-file statuses are always read from `ledger.json`.

`repo_type.value` ∈ `service | frontend | library | test-suite | db-migration | function-app | scheduler |
mobile | unknown`; rules in [EXTRACTORS.md#repo_type-classification](EXTRACTORS.md#repo_type-classification).
`template_type` is the `service.yaml` `type` value phase 5 will use (`null` where the template has no
equivalent: `test-suite`, `db-migration`, `unknown` — open item for phase 5).

## runs/<org>/<repo>/ledger.json

```json
{
  "schema_version": 1, "org": "TVS-CS", "repo": "PaymentService", "head_sha": "3f2c…",
  "phase_version": "0.1.0", "generated_at": "…Z", "max_file_bytes": 1000000,
  "files": [
    {"path": "src/Payment.Api/Controllers/PaymentController.cs", "class": "source",
     "language": "csharp", "size": 5321, "lines": 180, "status": "pending",
     "extractors": [{"id": "dotnet.aspnet", "version": "0.1.0", "parse": "partial", "items": 4}]},
    {"path": "src/Payment.Api/appsettings.json", "class": "config", "language": "json",
     "size": 812, "lines": 30, "status": "extracted",
     "extractors": [{"id": "shared.config", "version": "0.1.0", "parse": "full", "items": 11}]},
    {"path": "web/node_modules/x/index.js", "class": "vendor", "language": "javascript",
     "size": 100, "lines": null, "status": "skipped:vendor"}
  ]
}
```
- `files` sorted by `path`; exactly one entry per `git ls-files` entry. Phases 2 and 3 only update
  `status`, `extractors` and `llm`; they never add, drop or reorder entries (path set re-checked on write).
- `class` ∈ `source | config | infra | api_contract | docs | test | build_manifest | other`
  (→ `status: pending`) or `vendor | generated | binary | lockfile | minified | asset | large |
  symlink | submodule` (→ `status: skipped:<class>`).
- `lines` = newline count (+1 if the last byte isn't `\n`) for pending files; `null` for skipped.
- `size` = bytes on disk (`null` for submodules).

### File status lifecycle

| status | set by | meaning |
|---|---|---|
| `pending` | phase 1 | not settled by phase 2; listed in `gaps.json` (`partial_parse` / `untouched_source` / `untouched_file`) for phase 3 |
| `extracted` | phase 2 | at least one extractor reported `parse: "full"` for this file |
| `scanned` | phase 3 (planned) | the gap-fill agent resolved the file's gaps for its current content (only gap files; `extracted` files are not revisited) |
| `skipped:<class>` | phase 1 | explicit, reasoned exclusion |
| `failed:<reason>` | phase 1/2 | e.g. `failed:missing` (tracked file absent on disk). Always a coverage-gate failure |

Status is **recomputed**, not appended, every time phase 2 or 3 writes the ledger:
`failed:*` if a current failure is recorded → else `scanned` if `llm` matches the file's current content
sha1 and the current prompt version → else `extracted` if any `extractors[].parse == "full"` →
else `pending`. Skipped entries never change. So a phase-2 re-run never undoes a valid phase-3 scan, and
a phase-1 rebuild (new `head_sha`) resets every file to `pending` with no `extractors`/`llm` (phases 2–3
become stale through `input_sha`).

### `extractors[]` (written by phase 2)

One entry per extractor that **opened** the file because it was in that extractor's scope, even when it
emitted 0 items; sorted by `id`. This is the record phase 3 and phase 6 use to see which extractors
touched each file.

| Field | Meaning |
|---|---|
| `id`, `version` | extractor id and `extractor_version` ([EXTRACTORS.md](EXTRACTORS.md#extractor-ids)) |
| `parse` | `full` = parsed with a real grammar-level parser (JSON/YAML/XML/properties/.env/Dockerfile/contract/SQL DDL) without errors and every construct of interest resolved; `partial` = scanned (pattern/AST-lite) or some construct unresolved (dynamic URL, unknown wrapper, parse error) |
| `items` | number of inventory items whose evidence cites this file |
| `error` | optional, redacted parse error (file stays `pending`) |

Source files parsed by the tree-sitter stack extractors are `full` when the tree is clean and every
construct of interest resolved (also when there is none), `partial` otherwise (EXTRACTORS rule 2). Every
file left `pending` is listed in `gaps.json` exactly once (`partial_parse`, `untouched_source` or
`untouched_file`); phase 3 reads only those.

### `llm` (written by phase 3, planned)
`{"agent": "kiro-agent", "prompt_version": "p3b-1", "content_sha1": "…", "items": 2, "rejected": 0}`.

## runs/<org>/<repo>/inventory.json

Written by phase 2 only (phase 3 writes its own [llm_notes.json](#runsorgrepollm_notesjson-planned);
phases 4–5 read both). Every item maps 1:1 onto a field group of the template
(`templates/service-docs/service.yaml` + `API_SPEC.md`, read-only), see
[template mapping](#inventory--template-mapping).

```json
{
  "schema_version": 1, "org": "TVS-CS", "repo": "PaymentService", "service_id": "payment-service-1a2b3c",
  "head_sha": "3f2c…", "phase_version": "0.1.2", "version": "0.1.2+9c1e4b7a2d10",
  "extractor_versions": {"dotnet.aspnet": "0.1.0", "shared.config": "0.1.0"},
  "registry_hash": "5be0…",
  "repo_type": "service",
  "items": [
    {"id": "inbound_http:src/Payment.Api:POST:/api/payments",
     "kind": "inbound_http",
     "subproject": "src/Payment.Api",
     "attributes": {"method": "POST", "path": "/api/payments", "path_raw": "api/[controller]",
                    "handler": "PaymentController.Create", "auth": "bearer-jwt",
                    "auth_raw": "[Authorize(Policy = \"Payments\")]",
                    "params": [{"name": "X-Correlation-Id", "in": "header", "type": "string", "required": false}],
                    "request": "CreatePaymentRequest",
                    "responses": [{"status": 201, "schema": "PaymentResponse", "from": "ProducesResponseType"},
                                  {"status": 400, "schema": "ProblemDetails", "from": "ProducesResponseType"}]},
     "evidence": [{"file": "src/Payment.Api/Controllers/PaymentController.cs", "line": 42,
                   "snippet": "[HttpPost]"}],
     "source": "code", "extractor": {"id": "dotnet.aspnet", "version": "0.1.0"}, "confidence": "high"}
  ],
  "errors": [{"level": "file", "file": "deploy/values.yaml", "extractor": "shared.infra",
              "reason": "YAMLError: mapping values are not allowed here (line 12)"}],
  "stats": {"by_kind": {"inbound_http": 1}}
}
```

### Item fields (all kinds)

| Field | Rule |
|---|---|
| `id` | stable, deterministic: `<kind>:<subproject or ".">:<kind key>` (kind keys in the table below). Same construct found at several call sites → **one** item, evidence merged |
| `kind` | one of the kinds below |
| `subproject` | the `meta.stacks[].subproject` it was found in (`.` = repo root) |
| `attributes` | normalized attributes of that kind; every key always present (`null`/`[]` when unknown), keys sorted |
| `evidence` | ≥1 `{file, line, snippet}`; `file` is a ledgered, non-skipped path; `line` 1-based and ≤ the file's `lines`; `snippet` = that source line, whitespace-trimmed, ≤200 chars, **after** secret redaction ([config classifier](#config-value-classifier) masks + `secrets.redact` token forms). Sorted by `(file, line)`; capped at 25 per item; `evidence_count` (always present) holds the true total |
| `source` | `code` (from source/config/manifests) or `contract` (from an OpenAPI/Swagger/Postman/proto/GraphQL/WSDL file); phase 3 uses `inferred`; phase 7 promotes to `manual`. Phase 5 writes `contract` as `source: code` in `service.yaml` (the template enum is `code \| manual \| inferred`) |
| `extractor` | `{"id": "<extractor id>", "version": "<extractor_version>"}` |
| `confidence` | `high` = read from one explicit construct (annotation/attribute literal, config literal, manifest entry); `medium` = needed a heuristic (one-level wrapper following, string concatenation, config value differing per env, convention-based names, status codes inferred from `return` statements). Phase 2 never emits low-confidence items: such constructs leave the file `partial` for phase 3 |

**Determinism:** same clone SHA + same extractor versions + same registry → **byte-identical**
`inventory.json`. Files are visited in ledger path order; items sorted by `(kind, id)`; JSON written with
sorted keys, `indent=2`, `ensure_ascii=false`, trailing newline; no timestamps or absolute paths in the
file (timestamps live in `state.json`); no dependence on set/dict iteration order or locale.

**Stale detection:** `state.phases.extract` is stale when `head_sha` changes, when any applicable
`extractor_version` / `PHASE_VERSION` changes (composite `version`), when `registry/external_systems.yaml`
changes (`registry_hash`), or when `ledger.json` was regenerated after the extract (`ledger_generated_at`).

## Item kinds and attributes

| kind | kind key (in `id`) | attributes |
|---|---|---|
| `inbound_http` | `<METHOD>:<path>` | `method`, `path` (fully combined, normalized display form), `path_raw`, `path_params_normalized` (`/api/bookings/{}`), `handler` (`Class.method` / `file#fn`), `framework` (`spring-mvc \| spring-webflux \| jax-rs \| aspnet-core \| aspnet-minimal \| azure-functions \| nest \| express \| next-api`), `params[{name, in: path\|query\|header\|body\|form\|cookie, type, required}]`, `request` (schema name or `null`), `responses[{status, schema, when, from}]`, `auth` (`none \| bearer-jwt \| api-key \| basic \| policy:<p> \| roles:<r1,r2> \| guard:<Name> \| unknown`), `auth_raw`, `allow_anonymous`, `deprecated`, `contract_file` (contract items), `context_path_by_env{<env>: <prefix>}` (Spring context-path / servlet path per env; differing values → `medium`) |
| `schema` | `<TypeName>` (generic instances `Page<Booking>`) | `name`, `defined_in` (`file:line`), `language`, `schema_kind` (`class \| record \| interface \| type \| enum \| contract`), `fields[{name, json_name, type, required, nullable, validation, default}]`, `enum_values[]`, `type_params[]`, `extends`, `resolved` (false when the type lives outside the repo, e.g. a jar/NuGet/npm type) |
| `outbound_http` | `<METHOD>:<base_ref>:<path_template>` | `method`, `client` (`resttemplate \| webclient \| restclient \| feign \| okhttp \| apache-httpclient \| retrofit \| httpclient \| ihttpclientfactory \| refit \| restsharp \| flurl \| axios \| fetch \| got \| nest-httpservice`), `client_name` (Feign `name`, named HttpClient, axios instance var), `base_url_source` (`literal \| config:<key> \| env:<VAR> \| unknown`), `base_url_values{<env>: <url>}` (non-secret only), `path_template` (`/api/payments/{}/status`), `path_raw`, `query_params[]`, `headers[]`, `request`, `response`, `via_wrapper` (`file:line` of the wrapper when one level of indirection was followed), `role` (`runtime \| tests_target`), `target_hint` (host, Feign name or registry match; resolved in phase 4) |
| `frontend_api_call` | `<METHOD>:<base_ref>:<path_template>` | same as `outbound_http` plus `ui_framework` (`react \| nextjs \| angular \| plain-js`), `runtime` (`browser \| server` — Next.js server components/route handlers/`getServerSideProps`), `base_url_kind` (`environment-ts \| dotenv \| config-js \| next-config \| runtime-config-json \| proxy`) |
| `messaging` | `<direction>:<broker>:<entity_ref>`; for `name_from: unknown` with a `name_key`: `<direction>:<broker>:unknown:<name_key>` (node.backend without a key: `unknown@<file>:<line>`), so dynamic entities of one repo stay separate | `direction` (`publish \| subscribe`), `broker` (`azure-service-bus \| event-grid \| event-hub \| storage-queue \| kafka \| rabbitmq \| redis-pubsub \| bull`, or `null` for Nest `@EventPattern`/`@MessagePattern` without a known transport), `entity`, `entity_type` (`topic \| queue \| subscription \| event-hub \| kafka-topic \| exchange \| bull-queue`), `namespace`, `name_from` (`literal \| config:<key> \| env:<VAR> \| unknown` — `unknown` for dynamic names, entity `null`, file `partial`), `name_key`, `resolved_values{<env>: <name>}`, `subscription` (resolved name, else the reference `config:<key>` / `env:<VAR>` / `unknown:<KEY>`), `filter`, `message_types[]`, `payload`, `properties{session_id, correlation_id, partition_key, app_properties[]}`, `published_by` / `handler` (`file:line`), `trigger` (`processor \| function-trigger \| jms-listener \| stream-binding \| message-pattern \| poll \| listener-annotation`), `error_handling{max_delivery, dead_letter, retry}`, `library`, `role` (`runtime \| script`; `script` when every evidence file is under a `script/`, `scripts/` or `tools/` directory, so phase 4 draws no service edge for it) |
| `data_access` | `<store_type>:<store_ref>` | `store_type` (`mssql \| postgres \| mysql \| oracle \| mongo \| cosmos \| redis \| blob \| s3 \| elastic \| opensearch \| nebula \| sqlite \| other`), `host`, `database` (both parsed from config/connection strings; **never** the connection-string value), `name_from`, `orm` (`jpa \| spring-data \| jdbctemplate \| mybatis \| ef-core \| dapper \| ado \| typeorm \| prisma \| sequelize \| mongoose \| knex \| pg \| mysql2 \| redis-client \| cosmos-sdk \| blob-sdk \| s3-sdk \| elastic-client \| mongo-template \| opensearch-client \| nebula-client`), `entities[{name, table, schema, defined_in, operation}]` (`operation` ∈ `read \| write \| both`), `collections[]`, `stored_procedures[{name, evidence}]`, `operation` (rolled up), `owns_schema` (true for db-migration repos), `routines[]`, `tables_ddl[{name, schema, columns[{name, type, nullable}], view?}]` (from `*.sql` DDL in any repo; `owns_schema: true` only in db-migration repos) |
| `config_key` | `<canonical key>` | `name` (as written), `canonical` ([key normalization](EXTRACTORS.md#config)), `reads[{file, line, api}]`, `defined_in[{file, env}]`, `values{<env>: <value>}` (**only** when the classifier allows), `value_kind` (`url \| host \| path \| topic \| queue \| entity \| db-name \| hidden \| reference`), `secret` (bool), `kv_ref` (Key Vault reference name), `ref` (placeholder target, e.g. `${X}` → `X`), `provided_by` (`app-settings \| env-file \| k8s-configmap \| k8s-secret \| key-vault \| pipeline \| unknown`), `required` |
| `scheduled_job` | `<handler>` | `trigger_type` (`cron \| fixed-rate \| fixed-delay \| interval \| timer-trigger \| hosted-service \| hangfire \| quartz \| node-cron \| agenda \| bull-repeat \| k8s-cronjob`), `expression`, `expression_from`, `resolved_values{}`, `timezone`, `handler` (`file:line`), `name` |
| `external_system` | `<name>` | `name` (registry `name`), `matched_by` (`host \| package \| sdk-symbol`), `match` (the matched host/package/symbol), `category`, `from_item` (id of the outbound/dependency item) |
| `dependency` | `<ecosystem>:<name>` | `ecosystem` (`maven \| gradle \| nuget \| npm`), `name` (`groupId:artifactId`, NuGet id, npm name), `version` (resolved literal or `${prop}` left as is when unresolvable), `version_from`, `scope` (`compile \| runtime \| test \| provided \| dev \| peer \| optional`), `manifest` (file), `internal` (bool), `internal_repo` (registered repo publishing it, when known), `kind` (`package \| parent \| module \| project-reference \| bom`) |
| `artifact` | `<ecosystem>:<name>` | what this repo **publishes**: `ecosystem`, `name`, `version`, `packaging` — used by phase 4 to resolve internal library edges |
| `infra` | `<infra_kind>:<name>` | `infra_kind` (`dockerfile \| compose-service \| k8s-deployment \| k8s-service \| k8s-ingress \| k8s-configmap \| k8s-secret-ref \| k8s-cronjob \| helm-values \| azure-pipeline \| github-workflow \| bicep \| terraform`), `name`, `namespace`, `image`, `base_images[]`, `ports[]`, `env[{name, value?, from}]` (values via classifier), `hosts[]`, `paths[{path, backend_service, port}]`, `configmap_refs[]`, `secret_refs[]` (names only), `variables[{name, value?, secret}]`, `variable_groups[]`, `environments[]`, `deploy_targets[]`, `servicebus_entities[{name, type, max_delivery, dead_letter}]` |
| `api_contract` | `<contract file or generator>` | `format` (`openapi-2 \| openapi-3 \| postman \| proto \| graphql \| wsdl \| asyncapi \| raml`), `file`, `generator` (`swashbuckle \| springdoc \| nestjs-swagger \| null`), `generated` (bool), `docs_path` (`/swagger/v1/swagger.json`, `/v3/api-docs`), `operations` (count), `title`, `version` |

`base_ref` / `entity_ref` / `store_ref` = `config:<key>`, `env:<VAR>`, the literal host (`api.example.com`)
or `_` when unknown. Paths in keys use the normalized form (`{}` for every parameter).

Per-env maps (`base_url_values`, `resolved_values`) may carry the pseudo-env `code-default` (node
extractors): the literal fallback of `process.env.X || 'http://…'` / `?? '…'`, classifier-filtered like
any other value. java.spring uses `code-default` for store object names only (OpenSearch index names in
`collections`/`entities`, the Nebula space in `database`): the literal initializer of the
`@ConfigurationProperties` field the code reads, when the key is defined nowhere in the repo
([EXTRACTORS.md](EXTRACTORS.md#javaspring-implementation-notes)).

## Inventory → template mapping

| inventory kind | `service.yaml` field(s) | `API_SPEC.md` section |
|---|---|---|
| `inbound_http` | `inbound[]` (`kind: http`, `method`, `path`, `auth`, `params`, `request`, `responses`; `callers` filled by phase 4) | Endpoint Index, `### METHOD /path` blocks, Authentication |
| `schema` | `schemas.<Name>` (`defined_in`, `fields[{name,type,required,validation}]`; enums as `enum[A,B]`) | Schemas `### <Name>`, request/response field tables |
| `outbound_http` | `outbound[]` (`target` by phase 4, `kind: http`, `method`, `path`, `request`, `response`, `criticality`) | Outbound Calls |
| `frontend_api_call` | caller side of other services' `inbound[].callers`; the frontend's own `outbound[]` | Outbound Calls (frontend docs) |
| `messaging` (publish) | `events.publishes[]` (`entity`, `entity_type`, `broker`, `namespace`, `name_from`, `message_types`, `payload`, `properties`, `published_by`; `consumers` by phase 4) | Events Published |
| `messaging` (subscribe) | `events.subscribes[]` (+ `subscription`, `filter`, `handler`, `trigger`, `action`, `error_handling`; `producers` by phase 4) | Events Consumed |
| `data_access` | `data_stores[]` (`name`, `type`, `access`, `owned`, `owner_service`, `key_entities`) | Side effects lines |
| `config_key` | `config[]` (`name`, `secret`, `required`, `provided_by`, `points_to` by phase 4) — **never values** | – |
| `scheduled_job` | `inbound[]` with `kind: scheduled` | Endpoint Index (scheduled rows) |
| `external_system` | `outbound[].target: external:<name>` | External Integrations |
| `dependency` / `artifact` | `tech_stack.key_libraries`, `library_dependency` edges (phase 4) | – |
| `infra` | `deployment` (`platform`, `environments[].base_url`), phase-4 host→service index | – |
| `api_contract` | front-matter `openapi:` of `API_SPEC.md`; contract items as `inbound`/`schemas` | – |
| `meta.repo_type` | `type` | – |

## Config value classifier

Module `repo_docs/config_classify.py`, unit-tested in `tests/test_config_classify.py` (a table of
key/value cases per rule, including near-misses like `keyspace`, `monkey`, `tokenizer`). Every config
value, `ENV`/`ARG` value, pipeline variable and evidence snippet goes through it before anything is
written. Rules, first match wins:

| # | Rule | Result |
|---|---|---|
| 1 | Placeholder value: `${X}`, `${X:default}`, `#{X}#`, `$(X)`, `%X%`, `__X__`, `{{X}}` | `value_kind: reference`, `ref: X`; a literal default after `:` is classified again by rules 2–6 |
| 2 | Key Vault reference: `@Microsoft.KeyVault(SecretUri=https://<vault>.vault.azure.net/secrets/<name>…)`, `@Microsoft.KeyVault(VaultName=…;SecretName=…)`, k8s `secretKeyRef`, CSI `SecretProviderClass` `objectName`, Spring Key Vault property sources | `secret: true`, `provided_by: key-vault`, `kv_ref: <vault>/<name>` (reference name only), no value |
| 3 | Key name is secret-like: camel/snake/kebab-split words include `password, passwd, pwd, secret, token, key, keys, apikey, credential(s), cert, certificate, pfx, sas, signature, salt, private`, or the name contains `connectionstring`, `connstr`, `connection_string`, `connection-string`, or sits under `ConnectionStrings:` | `secret: true`, name only |
| 4 | Value is secret-like whatever the name: `;`-separated `k=v` with `Password=`/`Pwd=`/`AccountKey=`/`SharedAccessKey=`/`User ID=`, URI with userinfo (`scheme://user:pass@`), JWT (`eyJ…​.…​.`), PEM header, `AKIA…`, `ghp_`/`github_pat_`, SAS (`sig=`), or ≥24 chars with Shannon entropy ≥ 4.0 that is not a URL/path | `secret: true`, name only |
| 5 | Value kind is allowed: `url` (http/https/sb/amqp/amqps/ws/wss/grpc, no userinfo; **query string and fragment stripped**), `host` (hostname/IP[:port]), `path` (starts with `/`), `topic`/`queue`/`entity` (key contains `topic, queue, subscription, entity, exchange, eventhub, binding, destination` and value matches `^[A-Za-z0-9._/-]{1,260}$`), `db-name` (key contains `database, dbname, db_name, catalog, schema` and value is an identifier) | value recorded per env |
| 6 | Anything else | `value_kind: hidden`, name only |

Connection strings are never stored, but `host` and `database` may be parsed out of them (e.g.
`Server=`/`Host=`/`Data Source=`, `Database=`/`Initial Catalog=`, JDBC `jdbc:postgresql://<host>/<db>`,
`mongodb+srv://…@<host>/<db>` with userinfo dropped, Service Bus `Endpoint=sb://<ns>.servicebus.windows.net/`
→ namespace only). Snippet redaction (`config_classify.redact_line`, used both when evidence is built
and when it is validated) replaces the value part of any rule-2/3/4 hit with `***`, and also masks
literal query values of absolute `http(s)://` URLs (`?subscription=***`, APIM keys are often passed this
way); template holes (`${..}`, `{..}`, `:x`, `%x%`) are left as written.

Env name from file name: `appsettings.Development.json` → `Development`, `application-uat.yml` /
`application-uat.properties` → `uat`, Spring profile documents (`spring.config.activate.on-profile`) →
that profile, `.env.prod` → `prod`, `environment.prod.ts` → `prod`, `local.settings.json` → `local`,
helm `values-<env>.yaml` → `<env>`; files without a suffix → `default`.

## registry/external_systems.yaml

Maintained registry of third-party systems; tracked in git, edited by humans (phase 2 reads it; its sha1
is part of the extract version, so editing it makes `extract` stale for every repo, which is cheap).
```yaml
schema_version: 1
systems:
  - name: juspay                  # → external:juspay (kebab-case, unique)
    category: payments            # payments | sms | email | maps | identity | analytics | crm | storage | other
    hosts: ["api.juspay.in", "*.juspay.in"]     # fnmatch on lower-cased host
    packages: ["in.juspay:*"]     # fnmatch on maven/nuget/npm names
    sdk_symbols: []               # class/module names (e.g. "JuspayClient")
    note: ""
```
How to extend: run `resolve` (phase 4); it lists every non-internal host/package it could not map in
`registry/external_candidates.json` (with the repos and evidence that use it). Add an entry here for each
real third-party system (never for internal services, which are matched by host/path), then re-run
`extract` and `resolve`. The file starts with the systems found in the first TVS-CS run ("seed from
findings"); never add an entry without at least one evidence-backed candidate.

## runs/<org>/<repo>/gaps.json
Written by phase 2 (`repo_docs/gaps.py`, `GAPS_VERSION = "0.1.1"`) next to `inventory.json`, from the
same in-memory results; deterministic (sorted keys and entries, no timestamps), part of the extract
version and staleness (missing file → `extract` stale). The work list of the phase-3 gap-fill agent.
Never contains values: only paths, item ids and short reasons (≤200 chars).
```json
{"schema_version": 1, "org": "TVS-CS", "repo": "master-data-platform", "head_sha": "3f2c…",
 "gaps_version": "0.1.2", "version": "0.1.2+9c1e4b7a2d10", "repo_type": "service",
 "summary": {"total": 3,
             "by_type": {"unresolved_base_url": 0, "unresolved_entity": 0, "missing_payload": 1,
                         "missing_schema": 1, "partial_parse": 1, "silent_client_file": 0,
                         "untouched_source": 0, "untouched_file": 0,
                         "unknown_repo_type": 0},
             "suppressed": {"client-factory": 1},
             "suppressed_paths": ["src/main/java/…/config/RestTemplateConfig.java (client-factory)"]},
 "gaps": [
   {"type": "missing_payload", "file": "src/main/java/…/DealerMasterServiceBusConfig.java", "line": 52,
    "reason": "subscribe local.mdp.dealer_data: payload type not resolved",
    "item": "messaging:.:subscribe:azure-service-bus:config:spring.jms.servicebus.topic.dealerData.name"},
   {"type": "missing_schema", "file": "src/main/java/…/DealerController.java", "line": 31,
    "reason": "POST /mdp/v1/dealer: no request schema", "item": "inbound_http:.:POST:/mdp/v1/dealer"},
   {"type": "partial_parse", "file": "src/main/java/…/Legacy.java", "line": null,
    "reason": "java.spring: parse error: tree-sitter: 2 error nodes", "item": null}
 ]}
```
Entries are sorted by (type order below, `file`, `line`, `item`, `reason`); each has exactly `type`,
`file`, `line` (null when unknown), `reason`, `item` (related item id or null).

| type | emitted for |
|---|---|
| `unresolved_base_url` | `outbound_http` / `frontend_api_call` with `base_url_source` `unknown` |
| `unresolved_entity` | `messaging` with `name_from: unknown`, or no `entity` and no `resolved_values` |
| `missing_payload` | `messaging` with `payload: null` |
| `missing_schema` | `inbound_http` with `POST/PUT/PATCH` and no `request`, or with no response carrying a `schema` (one entry each) |
| `partial_parse` | `pending` ledger file with a `partial` extractor touch: parse error (`parse error: …`) or an unresolved / unsupported construct |
| `silent_client_file` | `source` file (java, C#, JS/TS) using an HTTP client, messaging SDK or data-store client (`gaps.CLIENT_RULES`) that yielded no item of the matching kind (`outbound_http`/`frontend_api_call`, `messaging`, `data_access`). Not listed for the HTTP client rule: files an extractor marked as client factory / holder / interface / interceptor (`client-factory`, `client-holder`, `client-interface`, `client-interceptor`); they are counted in `summary.suppressed` `{reason: count}` and named in `summary.suppressed_paths` (`"<path> (<reason>)"`, sorted) |
| `untouched_source` | `source`-class ledger file (tests and generated files are other classes) no extractor opened; every one is listed (no cap) |
| `untouched_file` | every other `pending` ledger file not listed above: non-source classes (test, config, docs, other, build_manifest, infra) and opened-but-unsettled files; `reason` starts with the ledger class (`config file left pending: …`) |
| `unknown_repo_type` | `repo_type: unknown` (one entry, `file: null`) |

`summary.total` = sum of `by_type` = number of entries (suppressed paths are not entries). `total == 0` → the
phase-3 agent skips the investigation for the repo.

## runs/<org>/<repo>/llm_notes.json (planned)
Written by the phase-3 gap-fill agent (Option B), validated and merged by `llm-scan`.
```json
{"schema_version": 1, "repo": "master-data-platform", "head_sha": "3f2c…", "gaps_version": "0.1.1",
 "prompt_version": "p3b-1",
 "items": [<inventory item, source: "inferred", extractor: {"id": "kiro-agent", "version": "p3b-1"}>],
 "resolved_gaps": [{"gap": {"type": "missing_payload", "file": "…", "line": 52, "item": "messaging:…"},
                    "items": ["messaging:…"], "not_applicable": null}],
 "rejected": [{"proposal": {…}, "reason": "evidence_not_found | line_out_of_range | schema_invalid | secret_detected"}],
 "conflicts": [{"item": "<phase-2 id>", "attribute": "…", "phase2": …, "inferred": …, "evidence": "file:line"}]}
```
- `items` use the phase-2 item shape and kinds and pass `inventory_schema.validate_item` (evidence line
  re-read, redacted, snippet substring; no secret values); invalid proposals go to `rejected`. Extra
  phase-3-only kinds: `purpose` (`{target_id, text ≤300 chars}`) and `flow_step`
  (`{flow_hint, from, to, via, data}`). An item that restates a phase-2 item carries `corroborates: <id>`;
  contradictions go to `conflicts[]` for phase 7.
- `resolved_gaps[]`: one entry per `gaps.json` entry handled, with the items that close it or a
  `not_applicable` reason (e.g. a `missing_schema` for an endpoint that really has no body).

## Registry files (planned)

All written by phase 4 (`resolve`), deterministic, sorted.

`registry/<org>/services.json`
```json
{"schema_version": 1, "org": "TVS-CS", "services": {
  "booking-crud-services": {"repo": "booking-crud-services", "repo_type": "service",
    "aliases": ["BookingService"],
    "hosts": [{"host": "booking-crud-services", "from": "k8s-service", "env": "default"},
              {"host": "api.tvsm.example", "path_prefix": "/booking", "from": "k8s-ingress", "env": "prod"}],
    "base_urls": ["https://api.tvsm.example/booking"],
    "config_keys": ["services.booking.baseurl", "BOOKING_API_URL"],
    "inbound_routes": 23, "topics_published": ["booking-events"], "topics_consumed": [],
    "data_stores": ["mongo:_:booking"], "artifacts": []}}}
```

`registry/edges.json`
```json
{"schema_version": 1, "edges": [
  {"id": "sha1(from|to|kind|via)", "from": "booking-crud-services", "to": "payment-service",
   "kind": "http", "via": "POST /api/payments", "from_item": "outbound_http:.:POST:config:payment.url:/api/payments",
   "to_item": "inbound_http:.:POST:/api/payments", "match": "host+path", "caller_type": "service",
   "criticality": "hard", "source": "code", "confidence": "high",
   "evidence": [{"repo": "booking-crud-services", "file": "…", "line": 88, "snippet": "…"}]}]}
```
`kind` ∈ `http | grpc | soap | event | shared_db | owns_schema | library_dependency | tests`;
`caller_type` ∈ `service | frontend | test-suite`; `match` ∈ `host+path | host | path-unique | path-suffix |
entity | entity+namespace | table | artifact | manual`; `criticality` ∈ `hard | soft | async` (template
semantics; phase 4 defaults `hard` for sync http, `async` for events; `soft` comes from phase 3/manual);
`to` may be `external:<name>`.

`registry/candidates.json` — calls matching **several** inbound routes:
`{"schema_version":1, "items":[{"repo", "item_id", "call": "GET /api/{}/status", "candidates":[{"service_id", "item_id", "score", "reason"}]}]}`.

`registry/unresolved.json` — calls / entities matching nothing:
`{"schema_version":1, "items":[{"repo", "item_id", "target", "reason": "no_route_match|unknown_host|dynamic_url|no_base_url"}]}`.

`registry/messaging.json` — one record per broker entity:
`{"schema_version":1, "entities":[{"key": "azure-service-bus:sb-tvsm-prod:topic:booking-events", "publishers":[…], "subscribers":[{"service_id","subscription","filter","message_types"}], "flags": ["no_subscribers"|"no_publishers"|"message_type_unmatched"|"namespace_unknown"]}]}`.

`registry/contract_mismatches.json` — field-level DTO diffs caller vs callee (report only, never blocking):
`{"schema_version":1, "items":[{"edge_id", "direction": "request|response", "caller_schema", "callee_schema", "diffs":[{"field", "issue": "missing_required|extra|type_mismatch|enum_mismatch|name_case", "caller", "callee", "severity": "error|warn|info"}]}]}`.

`registry/external_candidates.json` — hosts/packages not internal and not in `external_systems.yaml`:
`{"schema_version":1, "items":[{"kind": "host|package", "value", "used_by":[{"repo","item_id"}]}]}`.

`registry/flows.json` — written by `flows` (`repo_docs/flows.py`); sorted keys, flows sorted by
`flow_id`, no timestamps (re-runs are byte-identical):
```json
{"schema_version": 1, "org": "TVS-CS", "version": "0.1.0", "max_depth": 5,
 "stats": {"flows": 101, "by_length": {"1": 17}, "services_covered": 26, "services_without_flow": ["bto-api"]},
 "flows": [{"flow_id": "cbs-admin-portal--external-juspay", "name": "cbs-admin-portal → external:juspay (2 hops)",
   "entry": "cbs-admin-portal", "terminal": "external:juspay", "services": ["cbs-admin-portal", "…"],
   "entry_types": ["frontend"], "triggers": ["user action in cbs-admin-portal (frontend)"],
   "length": 2, "truncated": false, "confidence": "high",
   "steps": [{"n": 1, "from": "cbs-admin-portal", "to": "booking-crud-services", "kind": "http", "mode": "sync",
     "via": "POST /bookings/dms-vehicle-master", "vias": ["…"], "data": ["DmsVehicleMasterDto"],
     "confidence": "high", "criticality": ["hard"], "edges": ["<edge id>"],
     "evidence": [{"repo": "…", "file": "…", "line": 76}], "evidence_total": 2}]}]}
```
`flow_id` = `<entry>--<terminal>` (slugged; `-<sha1[:6]>` of the hop sequence appended to every member
of a colliding group). `entry_types` ⊂ `frontend | scheduled | event_publisher | no_inbound | uncovered`.
Step `via` = first of the sorted `vias` (`METHOD path` or `<entity_type>:<topic>`); event steps add
`topics` (normalized names). `data` = schema names from the callee contract (request + responses), else
the caller DTOs; events use the message payload; generic types (`map<…>`, `string`, `object`…) dropped.
Step `confidence` = best of its edges; flow `confidence` = min over steps. `evidence` capped at 10.

`registry/aliases.yaml` — written by `aliases` (`repo_docs/aliases.py`); deterministic, no timestamps:
```yaml
schema_version: 1
org: TVS-CS
services:
  booking-crud-services:
    canonical: booking-crud-services
    repo: booking-crud-services
    aliases:            # ranked: manual > high > medium > low, unambiguous first, more sources first
    - alias: booking service
      confidence: high  # manual | high | medium | low
      sources: [{type: readme_h1, repo: booking-crud-services, file: README.md, line: 1}]  # max 8
      source_count: 3
ambiguous:            # alias -> 2+ service_ids
  mdp: [master-data-platform, tvsmbe-mdp-bff]
```
Source `type` ∈ `name | readme_h1 | readme_bold | artifact | caller_config | caller_client | host |
base_path | infra | pipeline | derived | manual`; `derived` sources add `from` (the phrase it was
derived from), `caller_config` / `caller_client` add `from` (key name / class name). Confidence:
name, README H1, root manifest artifact = high; caller config key / `*Client`/`*Gateway` class /
hostname / dominant inbound base path / compose-k8s name / README bold / sub-module artifact = medium;
`*Service` caller class, pipeline file name, suffix-stripped/singular variants = low. Junk dropped:
< 3 chars, only generic words (`service`, `api`, `backend`, `app`, `portal`, `common`, `core`, `main`,
`server`, `test`, …) or org prefixes (`tvs`, `tvsm`, `tvsmbe`), placeholders (`xxx`, `${…}`).
Only key NAMES and hostnames are used, never values.

`config/aliases.manual.yaml` — user-owned, never overwritten (`aliases` creates a commented template
once). `<alias>: [<service_id>, ...]`; merged at the highest priority (`confidence: manual`), and a
manual alias maps ONLY to the listed services (derived hits elsewhere are dropped).

`config/service_summaries.yaml` — user-editable `{service_id: {summary, domain, source, based_on}}`:
one factual sentence (≤ 30 words) + short kebab `domain`, `source: inferred` (set `manual` when edited),
`based_on` = files read. Read by `generate`; survives regeneration.

## output/<org>/<service-id>/ (planned)

Exactly the template set in `smartbrain-v2/templates/service-docs/`: `service.yaml` (template schema v1),
`OVERVIEW.md`, `API_SPEC.md`, `DATA_FLOWS.md`, `HLD.md`, `HLC.md`, `LLD.md`, each `.md` with front-matter
`service_id`, `doc_type`, `last_reviewed` (+ `aliases` on OVERVIEW.md, see `generate`). The template is the spec; it is never copied into or modified by
this subsystem.

## Coverage and review files (planned)

`runs/<org>/<repo>/coverage.json`
```json
{"schema_version": 1, "repo": "PaymentService", "result": "fail", "checked_at": "…Z",
 "gaps": {"ledger_pending": ["src/x.cs"], "ledger_failed": ["src/gone.cs (failed:missing)"], "open_phase2_gaps": 3,
          "submodules_unregistered": ["libs/common"], "items_missing_in_docs": ["inbound_http:.:POST:/api/payments"],
          "asymmetric_edges": [], "secret_hits": 0, "template_violations": []}}
```
`review/<org>/pending_inferred.json`: `{"schema_version":1, "edges":[<edge>], "candidates":[…], "unresolved":[…], "conflicts":[…]}`;
`review/<org>/decisions.json`: `{"schema_version":1, "decisions":[{"edge_id","decision":"approve|reject|edit","reviewer","at","note"}]}`.

## eval/questions.yaml (planned)

Extends the format of `smartbrain-v2/steering-lite/bench/questions.yaml` (referenced, never modified).
```yaml
schema_version: 1
based_on: ../steering-lite/bench/questions.yaml
questions:
  - id: msg_01
    category: messaging          # dependency | data_flow | blast_radius | messaging | request_response | frontend_callers | config | shared_db | library
    difficulty: medium           # easy | medium | hard | expert
    question: "Which services publish to the booking-events topic, and who consumes it?"
    expected_keywords: ["booking-events", "publish", "subscribe"]
    expected_entities: [booking-crud-services, async-communication-service]   # service_ids / topics / tables
    ground_truth: {from: registry, query: "messaging.entities[entity=booking-events]"}   # or from: manual
    verified_by: null            # name of the human who checked it against code (≥10 questions must be)
```
Results: `eval/results/<UTCts>-<label>.json` = `{label: before|after, system, per_question[{id, entity_recall,
entity_precision, keyword_recall, cites_evidence}], summary{by_category}}`.
