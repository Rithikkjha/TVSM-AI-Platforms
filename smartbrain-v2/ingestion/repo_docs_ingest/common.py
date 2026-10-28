"""Shared paths, constants and store helpers for the repo_docs ingest."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: smartbrain-v2 project root (``ingestion/repo_docs_ingest/common.py`` -> parents[2]).
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

#: Root of the repo_docs subsystem (its ``output/`` and ``registry/`` are read here).
REPO_DOCS_ROOT: Path = PROJECT_ROOT / "repo_docs"

#: ``origin`` value stamped on every node / relationship / point this ingest owns.
ORIGIN = "repo_docs"

#: ``source`` value of the Jira/Confluence -> Service links written by the linker.
LINK_SOURCE = "alias_match"

#: The six narrative docs per service, in a stable order.
DOC_FILES: tuple[str, ...] = (
    "OVERVIEW.md",
    "API_SPEC.md",
    "DATA_FLOWS.md",
    "HLD.md",
    "HLC.md",
    "LLD.md",
)

#: Every label the graph loader / docs loader writes (constraints are created for each).
REPO_DOCS_LABELS: tuple[str, ...] = (
    "Service",
    "Endpoint",
    "Topic",
    "Schema",
    "DataStore",
    "ExternalSystem",
    "ConfigKey",
    "Flow",
    "Alias",
    "Domain",
    "ServiceDoc",
)


@dataclass(frozen=True)
class OrgPaths:
    """Resolved input locations for one org."""

    root: Path
    org: str

    @property
    def output_dir(self) -> Path:
        return self.root / "output" / self.org

    @property
    def registry_dir(self) -> Path:
        return self.root / "registry"

    @property
    def manual_aliases(self) -> Path:
        return self.root / "config" / "aliases.manual.yaml"

    def service_dirs(self) -> list[Path]:
        return sorted(p for p in self.output_dir.iterdir() if (p / "service.yaml").is_file())


def stable_id(*parts: Any) -> str:
    """Deterministic sha1 over ``parts`` joined with ``|`` (used as edge_id)."""

    return hashlib.sha1("|".join("" if p is None else str(p) for p in parts).encode("utf-8")).hexdigest()


def to_json(value: Any) -> str:
    """Compact, deterministic JSON string for Neo4j properties (maps aren't allowed)."""

    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def neo4j_driver():  # type: ignore[no-untyped-def]
    """Async neo4j driver from ``config.settings`` (credentials never printed)."""

    from neo4j import AsyncGraphDatabase

    from config.settings import get_settings

    settings = get_settings()
    return AsyncGraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )


def qdrant_store():  # type: ignore[no-untyped-def]
    """The existing :class:`QdrantVectorStore` pointed at ``settings.qdrant_url``."""

    from config.settings import get_settings
    from storage.vector.vector_store import DEFAULT_INDEX_NAME, QdrantVectorStore

    return QdrantVectorStore(
        url=get_settings().qdrant_url, collection_name=DEFAULT_INDEX_NAME, timeout=120.0
    )


#: Doc types the docs/link steps must find in the BM25 corpus before writing it.
EXISTING_DOC_TYPES: tuple[str, ...] = ("jira", "confluence")


def require_bm25_corpus(bm25: Any) -> dict[str, int]:
    """Abort unless the BM25 corpus loaded and still holds the Jira/Confluence texts.

    ``LocalBM25Index`` starts empty when ``rank_bm25`` is missing or the pickle is
    unreadable; flushing that would overwrite the persisted corpus with only the
    repo_docs entries. Returns per-doc_type counts for the existing doc types.
    """

    if not getattr(bm25, "_available", False):
        raise RuntimeError("BM25 index unavailable (rank_bm25 missing or pickle unreadable); aborting")
    counts = {dt: 0 for dt in EXISTING_DOC_TYPES}
    for entry in bm25._corpus.values():
        dt = (entry.get("metadata") or {}).get("doc_type")
        if dt in counts:
            counts[dt] += 1
    if not all(counts.values()):
        raise RuntimeError(f"BM25 corpus is missing Jira/Confluence entries {counts}; aborting")
    return counts


async def run_cypher(session: Any, cypher: str, **params: Any) -> list[dict[str, Any]]:
    result = await session.run(cypher, **params)
    return [dict(r) for r in await result.data()]


async def unwind_write(
    session: Any, cypher: str, rows: list[dict[str, Any]], *, batch: int = 500
) -> int:
    """Run ``UNWIND $rows AS row <cypher>`` in batches; returns rows sent."""

    for i in range(0, len(rows), batch):
        result = await session.run("UNWIND $rows AS row " + cypher, rows=rows[i : i + batch])
        await result.consume()
    return len(rows)
