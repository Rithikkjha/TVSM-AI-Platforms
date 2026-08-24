# Library, Docker & License Inventory

Complete inventory of every runtime dependency SmartBrain ships or runs, the
**actual installed version** (from `pip freeze` / pinned Docker tags — not the
`>=` floors in `pyproject.toml`), its license, and the extent to which we use
it.

> **Bottom line:** The stack is overwhelmingly permissive (MIT / BSD / Apache-2.0
> / PSF). The only copyleft component is **Neo4j Community Edition (GPLv3)**,
> which is compliant in our usage because we run it as an unmodified standalone
> server over the network and never embed or redistribute it. The only other
> non-permissive item is **Hypothesis (MPL-2.0)**, a test-only dependency that
> is never shipped. No AGPL, no SSPL, no commercial-restricted, no unknown
> licenses are present.

---

## 1. Container Images (Docker)

| Image | Version (pinned) | Edition | License | How / extent we use it |
| --- | --- | --- | --- | --- |
| **Neo4j** | `neo4j:5.20-community` | Community | **GPLv3** | Primary graph store. Run as an unmodified standalone container, accessed only over the Bolt network protocol. Not linked into our code, not modified, not redistributed. |
| Neo4j APOC plugin | bundled with 5.20 | — | Apache-2.0 | Utility procedures (used by ingestion/query helpers). Standard plugin, unmodified. |
| **Qdrant** | `qdrant/qdrant:v1.11.0` | OSS (only edition) | Apache-2.0 | Local/dev vector store. Standalone container over REST/gRPC. Unmodified. |
| **Python base** | `python:3.11-slim` | — | PSF License 2.0 | Base image for the API/ingestion container. Debian-slim OS layer underneath (OS packages, not linked into our code). |

**Neo4j GPLv3 — compliance note.** GPLv3 copyleft obligations attach to
*distribution* of the software or *derivative works*. We do neither: Neo4j runs
as a separate process that we talk to over Bolt (a network boundary, treated
like any client/server DB). Our application code is an independent work. This is
the standard, compliant way to use Neo4j Community. **If** SmartBrain is ever
packaged for external distribution *with Neo4j embedded*, this must be revisited
(or switch to Neo4j Enterprise, a commercial license). For an internal,
self-hosted tool this is a non-issue.

---

## 2. Python Libraries — Runtime (shipped)

| Library | Installed version | License | How / extent we use it |
| --- | --- | --- | --- |
| fastapi | 0.136.1 | MIT | Web framework for the REST/query API. Core. |
| starlette | 1.0.0 | BSD-3-Clause | ASGI toolkit under FastAPI (transitive). Core. |
| uvicorn | 0.47.0 | BSD-3-Clause | ASGI server that runs the app. Core. |
| pydantic | 2.13.4 | MIT | Request/response models, settings validation. Core. |
| pydantic-settings | 2.14.1 | MIT | Env-var / `.env` config loading. Core. |
| neo4j (driver) | 6.2.0 | Apache-2.0 | Async Bolt client for all graph reads/writes. Core. |
| openai | 2.37.0 | Apache-2.0 | Azure OpenAI client — GPT-4o synthesis + `text-embedding-3-large`. Core. |
| tiktoken | 0.13.0 | MIT | Token counting to truncate embedding input. Core. |
| rank-bm25 | 0.2.2 | Apache-2.0 | BM25 sparse keyword index for hybrid retrieval. Core. |
| httpx | 0.28.1 | BSD-3-Clause | Async HTTP client (integrations, MCP). Core. |
| mcp | 1.27.1 | MIT | Model Context Protocol SDK — powers the MCP server tools. Core. |
| PyYAML | 6.0.3 | MIT | Parses `mcp_servers.yaml` and other config. Core. |
| python-dotenv | 1.2.2 | BSD-3-Clause | Loads `.env` in scripts. Core. |
| numpy | 2.4.6 | BSD-3-Clause | Vector math (embeddings, scoring). Core (transitive + direct). |
| azure-search-documents | 12.0.0 | MIT | **Production** vector store client (Azure AI Search). Used only when the prod vector backend is selected; local dev uses Qdrant instead. |
| azure-core | 1.41.0 | MIT | Azure SDK core (transitive of azure-search-documents). Prod path only. |

---

## 3. Python Libraries — Optional Re-ranker (installed, lazy-imported)

The cross-encoder re-ranker is an **optional** feature (`pip install .[rerank]`).
It is currently installed in this environment, so the rerank path is active. If
uninstalled, retrieval falls back to hybrid top-k without re-ranking.

| Library | Installed version | License | How / extent we use it |
| --- | --- | --- | --- |
| sentence-transformers | 5.6.0 | Apache-2.0 | Cross-encoder re-ranking of top-N retrieval candidates. Optional. |
| torch | 2.13.0 | BSD-3-Clause | Tensor backend for sentence-transformers (transitive). Optional. |
| transformers | 5.14.1 | Apache-2.0 | Model loading for the cross-encoder (transitive). Optional. |

---

## 4. Python Libraries — Optional Cache (not currently installed)

| Library | Version constraint | License | How / extent we use it |
| --- | --- | --- | --- |
| redis | `>=5.0.0` (optional extra) | MIT | Optional production cache backend (`RedisBackend`). Lazy-imported; in-memory cache is the dev default. Not installed in this environment. |

---

## 5. Python Libraries — Dev / Test only (never shipped)

| Library | Installed version | License | How / extent we use it |
| --- | --- | --- | --- |
| hypothesis | 6.152.9 | **MPL-2.0** | Property-based tests. Test-time only, never shipped. |
| pytest | 9.0.3 | MIT | Test runner. |
| pytest-asyncio | 1.3.0 | Apache-2.0 | Async test support. |
| pytest-cov | 7.1.0 | MIT | Coverage reporting. |
| ruff | 0.15.13 | MIT | Linter / formatter. |
| mypy | 2.1.0 | MIT | Static type checker. |

**Hypothesis MPL-2.0 — note.** Mozilla Public License 2.0 is weak, *file-level*
copyleft: obligations would only apply if we modified and distributed
Hypothesis's own source files. We do neither, and it is a test-only dependency
that never ships in any artifact. No impact.

---

## 6. External Managed Services (not libraries — no license to us)

| Service | Purpose |
| --- | --- |
| Azure OpenAI | GPT-4o (synthesis) + text-embedding-3-large (embeddings). Consumed via API. |
| GitHub / Jira / Confluence APIs | Ingestion sources. Consumed via API. |

---

## 7. License Distribution Summary

| License | Count | Copyleft? | Concern |
| --- | --- | --- | --- |
| MIT | 9 | No | None |
| BSD-3-Clause | 6 | No | None |
| Apache-2.0 | 8 | No | None |
| PSF-2.0 | 1 | No | None |
| **GPLv3** (Neo4j Community) | 1 | Yes (strong) | Compliant as a standalone network service; revisit only if embedded/redistributed. |
| **MPL-2.0** (Hypothesis) | 1 | Yes (weak, file-level) | Test-only, never shipped. No impact. |

**Result: no blocking license issues.** We are on Community/OSS editions
throughout. The single strong-copyleft component (Neo4j Community) is used in the
standard, compliant client-server pattern.

---

_Versions captured from the running environment (`pip freeze`) and pinned Docker
tags in `docker-compose.yml` / `Dockerfile`. Re-run `pip freeze` after dependency
bumps to keep this current._
