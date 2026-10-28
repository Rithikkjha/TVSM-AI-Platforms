# repo_docs — GitHub repos → standardized SmartBrain service docs

SmartBrain v2's data source was inconsistent: each repo documented itself differently. `repo_docs`
builds a complete, evidence-backed doc set per service in the standard format
([`../templates/service-docs/`](../templates/service-docs/README.md)) so the RAG + Neo4j graph can answer
dependency, data-flow and blast-radius questions.

- Phase design (0–8 + evaluation) and agreed decisions: [docs/PIPELINE.md](docs/PIPELINE.md)
  ([decisions](docs/PIPELINE.md#decisions): default branch only · no APIM configs · phase 3 is a targeted
  gap-fill by a per-repo Kiro agent over `gaps.json` (Option B) · frontends are callers)
- Schemas (incl. inventory item kinds → template mapping): [docs/SCHEMAS.md](docs/SCHEMAS.md)
- Extractor contract and per-kind rules (phase 2): [docs/EXTRACTORS.md](docs/EXTRACTORS.md)
- Resume / operating rules for any agent: [RUNBOOK.md](RUNBOOK.md)

Implemented: phase 0 (discover + shallow clone + stack detection), phase 1 (file ledger), phase 2
(deterministic extraction → `inventory.json`: inbound HTTP with request/response schemas, outbound HTTP,
frontend API calls, Service Bus and other messaging, data access, config keys with a secret classifier,
scheduled jobs, external systems, dependencies, infra, API contracts, repo type) plus `gaps.json`, the
list of what phase 2 could not settle.
Planned: phase 3 (targeted gap-fill agent over `gaps.json` + narrative docs), 4 (cross-repo resolution without APIM), 5 (generate),
6 (coverage gate), 7 (review), 8 (ingest into Neo4j + Qdrant/BM25) and the before/after evaluation.

## Quick start
```bash
cd /Users/Rithik.Kumar/code/SmartBrain/tvsm-ai-platform/smartbrain-v2/repo_docs
/opt/homebrew/bin/python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m repo_docs status
.venv/bin/python -m repo_docs discover --org TVS-CS
.venv/bin/python -m repo_docs clone    --org TVS-CS
.venv/bin/python -m repo_docs ledger   --org TVS-CS
.venv/bin/python -m repo_docs extract  --org TVS-CS
.venv/bin/python -m repo_docs selfcheck
```

## Environment decision
smartbrain-v2's `pyproject.toml` belongs to the main app (hatchling, heavy deps, no dev venv), so repo_docs
is self-contained: `requirements.txt` with exact pins (`PyYAML==6.0.2`, `pytest==8.3.3`), venv at
`repo_docs/.venv` built with Python 3.11. Everything else is stdlib (GitHub REST via `urllib`, git via
`subprocess` argv lists, `fcntl` locks). The `gh` CLI is not used.

## Layout
```
repo_docs/
├── .gitignore               # /repos/ /.venv/ /logs/ /.agents/ *.tmp* *.partial/ /state/*.lock caches
│                            # (anchored, so config/repos/ allowlists stay tracked)
├── README.md  RUNBOOK.md  requirements.txt  pytest.ini
├── config/orgs.yaml         # orgs: token file+key, include/exclude, allowlist, overrides
├── config/repos/<org>.txt   # allowlist (user-owned)
├── docs/PIPELINE.md SCHEMAS.md EXTRACTORS.md
├── repo_docs/               # python package: python -m repo_docs <command>
│   ├── cli.py paths.py config.py naming.py secrets.py state.py
│   ├── github_client.py gitops.py stack_detect.py classify.py selfcheck.py
│   ├── phase0_discover_clone.py phase1_ledger.py phase2_extract.py
│   ├── config_classify.py repo_type.py           # secret/value classifier, repo_type rules
│   ├── inventory_schema.py pathnorm.py external_systems.py coverage.py gaps.py
│   └── extractors/ base.py registry.py stubs.py syntax.py configfmt.py config_index.py
│       shared_config.py shared_manifests.py shared_infra.py shared_contracts.py shared_sql.py
│       java_spring.py (+ java_symbols/inbound/http/messaging/data/types.py)
│       dotnet_aspnet.py (+ dotnet_symbols/types.py)
│       node_backend.py node_frontend.py (+ node_common.py)
├── tests/                   # pytest suite (no network)
├── state/state.json         # master tracker (+ state.lock, ignored)
├── runs/<org>/repos.json                # discovery snapshot
├── runs/<org>/<repo>/meta.json ledger.json inventory.json gaps.json
│                            # (+ llm_notes.json, coverage.json planned)
├── repos/<org>/<repo>/      # shallow clones — gitignored
├── logs/<org>/              # run logs, token-redacted — gitignored
├── registry/external_systems.yaml   # maintained third-party registry (phase 2, tracked)
├── registry/<org>/ registry/*.json  # planned (phase 4): services, edges, candidates, unresolved, messaging, …
├── review/                  # planned (phase 7)
├── output/<org>/<service-id>/  # planned (phase 5): template doc set
└── eval/questions.yaml eval/results/   # planned (evaluation)
```

## Commands
| Command | Phase | Status |
|---|---|---|
| `status [--org] [--json]` | – | implemented |
| `discover [--org]` | 0 | implemented |
| `clone [--org] [--repo ...] [--force] [--workers N]` | 0 | implemented |
| `ledger [--org] [--repo ...] [--force] [--workers N]` | 1 | implemented |
| `extract [--org] [--repo ...] [--force] [--workers N]` | 2 | implemented |
| `selfcheck [--org]` | – | implemented (token leak scan) |
| `llm-scan`, `resolve`, `generate`, `verify`, `review`, `ingest` | 3–8 | planned (exit 2) |
| `eval --label before\|after` | eval | planned (exit 2) |
