# RUNBOOK — resume the repo_docs pipeline from any session

If you are an agent told "read RUNBOOK.md and continue", this file is all you need.
Subsystem root (run every command from here):
`/Users/Rithik.Kumar/code/SmartBrain/tvsm-ai-platform/smartbrain-v2/repo_docs`

## Purpose
Turn every repo of every configured GitHub org into standardized SmartBrain service docs
(template: `../templates/service-docs/`). Phase design: [docs/PIPELINE.md](docs/PIPELINE.md).
File formats: [docs/SCHEMAS.md](docs/SCHEMAS.md). Extractor contract: [docs/EXTRACTORS.md](docs/EXTRACTORS.md).
Progress lives in `state/state.json`; never keep progress only in your head or chat.

Agreed decisions ([PIPELINE.md#decisions](docs/PIPELINE.md#decisions)): default branch only; no APIM/gateway
configs exist (resolution uses config/env, k8s names and path matching); phase 3 is a targeted gap-fill
(Option B): a per-repo Kiro agent works only through `runs/<org>/<repo>/gaps.json`, writes
`llm_notes.json` and the narrative docs in the same session; frontends (portals/UIs) are included as callers.

## Rules (non-negotiable)
1. **Idempotent steps.** Every command can be re-run safely; it skips work that is `done` and fresh.
2. **Checkpoint per unit.** State is updated as each repo finishes. Killing a command is safe.
3. **Never leak secrets.** Never print, log, write, or commit a token. Never put a token in a URL or
   argv. Never `cat`/`echo` the `.env`. Tokens reach git only via env-scoped `GIT_CONFIG_*`.
   Every stored/logged error goes through `secrets.redact`. Config values reach outputs only through
   `config_classify` (secret-like keys/values → name only; Key Vault refs → reference name only).
   Run `selfcheck` after every phase.
4. **Never mark done without outputs on disk.** A phase is `done` only when its output files exist and its
   own check passed (e.g. ledger self-check).
5. **Never delete others' outputs.** Only `clone` may reset/clean files, and only inside its own
   `repos/<org>/<repo>/`. Do not delete `runs/`, `state/`, `output/` by hand.
6. **Stay inside `repo_docs/`.** Never edit `../templates/` or other smartbrain-v2 modules. Phase 8
   (ingest) lists the outside changes it would need as open items; they require explicit user approval.
   The phase-3 agent writes only `runs/<org>/<repo>/llm_notes.json` (+ the narrative docs); it never
   edits `inventory.json`, `gaps.json` or ledger statuses by hand.
7. **Don't commit or push** unless the user asks. Clones (`repos/`), `.venv/`, `logs/` are gitignored.
8. Planned phases (3–8, `eval`) are stubs that exit 2; implement them per PIPELINE.md before running.
9. **Evidence or nothing.** Never hand-edit `inventory.json` or ledger statuses; fix the extractor, bump
   its `extractor_version`, re-run `extract`.

## Setup (once per machine)
```bash
cd /Users/Rithik.Kumar/code/SmartBrain/tvsm-ai-platform/smartbrain-v2/repo_docs
/opt/homebrew/bin/python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt     # PyYAML==6.0.2, pytest==8.3.3
.venv/bin/python -m pytest -q                 # must pass
```
repo_docs has its own venv/requirements (independent of smartbrain-v2's pyproject.toml).

## Resume protocol
1. `.venv/bin/python -m repo_docs status` — per org: repo count, per-phase counts by effective status
   (`pending/running/done/failed/skipped/stale`), failed repos with first error line, collisions, and the
   **next suggested command**.
2. Pick the first phase, in order `clone → ledger → extract → llm-scan → resolve → generate → verify →
   review → ingest` (after every `resolve`, run `flows --org X` then `aliases --org X` before `generate`; neither is tracked in state), that has any `pending`, `failed`, `stale`, or `running` repos. If the org has never
   been discovered (no repos in state), run `discover` first. (`eval` is run by hand before and after
   `ingest`.)
3. Run it:
   ```bash
   .venv/bin/python -m repo_docs discover --org TVS-CS
   .venv/bin/python -m repo_docs clone    --org TVS-CS --workers 5
   .venv/bin/python -m repo_docs ledger   --org TVS-CS --workers 5
   .venv/bin/python -m repo_docs extract  --org TVS-CS --workers 5
   ```
   Long runs: run in the background and poll `status`. Interrupting is safe; re-run the same command.
4. Re-run `status`; repeat until the phase is all `done`/`skipped`.
5. `.venv/bin/python -m repo_docs selfcheck` — must report `0 files contain the token`.
6. Record anything unusual (persistent failures + reason) for the user.

Useful flags: `--repo NAME` (repeatable, exact GitHub name) to target repos; `--force` to redo
regardless of status; `--workers N`; `status --json` for machine-readable output.

## Adding a new org
1. Put its token in a gitignored file (e.g. `../.env` key `GITHUB_TOKEN_<ORG>`); fine-grained, read-only
   (Contents + Metadata), scoped to that org.
2. Append an entry to `config/orgs.yaml` with its own `token_env_file` / `token_key`, `include`/`exclude`,
   optional `allowlist: config/repos/<ORG>.txt`.
3. `discover --org <ORG>`, then follow the resume protocol.

## Troubleshooting
| Symptom | Action |
|---|---|
| `401`/`403` from API on discover | token expired / wrong key / no org access. Ask the user for a new token; never print it. |
| `rate limit` | the client waits for reset automatically; re-run later if it gave up |
| allowlist name missing (exit 1) | name typo/case or repo renamed; fix `config/repos/<org>.txt` with the user |
| one repo `failed` on clone | `clone --org X --repo NAME --force`; check `error` in `status` |
| ledger self-check fail | `ledger --org X --repo NAME --force`; if persists, inspect `git -C repos/X/NAME ls-files` |
| disk space | clones are shallow; the 42 allowlisted TVS-CS repos take ~606 MB (whole org ~2.4 GB). `du -sh repos runs` |
| repo flagged empty by the API | `clone` re-checks with `git ls-remote`; it stays `skipped(empty)` only with no refs. If it has refs it is cloned and a WARNING is logged |
| `extract` failed for a repo | read `error` in `status`; `extract --org X --repo NAME --force`. File-level parse errors don't fail the repo (see `inventory.json` `errors[]`) |
| all repos `extract: stale` | an extractor version was bumped or `registry/external_systems.yaml` changed: re-run `extract` (cheap, deterministic) |
| stack listed in `missing_extractors` | that stack has no extractor yet; its files stay `pending` and appear in `gaps.json` as `untouched_source` (non-source ones as `untouched_file`) for phase 3 — expected, report it |
| `extract: stale` with nothing changed | `gaps.json` is missing for the repo (or `GAPS_VERSION` bumped): re-run `extract` |
| phase 3 / resume after `extract` | read `gaps.json` `summary`: `total == 0` → skip the investigation, write only the narrative docs; otherwise hand the open `gaps[]` (not yet in `llm_notes.json` `resolved_gaps`) to the agent |
| unknown third-party host/package | add it to `registry/external_systems.yaml` (format in docs/SCHEMAS.md), re-run `extract` |
| `status` next = a planned phase | phases 3–8 / `eval` are not implemented yet: stop and report; implement per docs/PIPELINE.md first |
| stale lock | `state/state.lock` is just a flock target; safe to leave; locks release when processes exit |
