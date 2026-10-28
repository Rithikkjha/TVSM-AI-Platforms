"""Phase 8: ingest the repo_docs output (graph + docs) and link Jira/Confluence.

Entry point::

    python3.11 -m ingestion.repo_docs_ingest --org TVS-CS [--graph] [--docs] [--link] [--dry-run]

Modules:

* :mod:`.graph_loader` — deterministic Neo4j load from ``service.yaml`` and the
  ``registry/*`` files (no LLM, no embeddings).
* :mod:`.chunker` / :mod:`.docs_loader` — heading-aware chunking of the six md
  docs per service, written to Qdrant + BM25 + Neo4j (``origin=repo_docs``).
* :mod:`.alias_linker` — links the already-ingested Jira tickets / Confluence
  pages to services by alias match (no refetch, no re-embedding).

Design: ``repo_docs/.agents/tasks/phase8/ingestion-investigation.md`` §5–§6.
"""
