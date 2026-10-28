"""Write the repo_docs md chunks to Qdrant + BM25 + Neo4j (Phase 8 step 3).

Full idempotent rebuild of the ``origin='repo_docs'`` docs scope:

* Qdrant: only new/changed chunks (``text_hash`` of display_text differs) are
  embedded (text-embedding-3-small, 1536); unchanged ones get a payload refresh;
  repo_docs points no longer produced are deleted.
* BM25: repo_docs keys are replaced (stale ones dropped), then persisted.
* Neo4j: ``ServiceDoc`` per file, ``Service-[:DOCUMENTED_IN]->ServiceDoc``,
  ``Chunk {text}`` + ``ServiceDoc-[:HAS_CHUNK]->Chunk``; older-run nodes deleted.
No dedup for repo_docs (generated docs; dedup against Jira could misfire).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import yaml

from ingestion.repo_docs_ingest.chunker import RepoDocChunker
from ingestion.repo_docs_ingest.common import DOC_FILES, ORIGIN, OrgPaths, require_bm25_corpus, run_cypher
from processing.extraction.deterministic import compute_text_hash

logger = logging.getLogger(__name__)

EMBED_BATCH = 64


def build_chunks(paths: OrgPaths) -> list[dict[str, Any]]:
    """Every repo_docs chunk as a plain dict (pure; no store access)."""

    chunker = RepoDocChunker()
    rows: list[dict[str, Any]] = []
    for d in paths.service_dirs():
        svc = yaml.safe_load((d / "service.yaml").read_text(encoding="utf-8"))
        sid = svc["service_id"]
        aliases = list(svc.get("aliases") or [])
        for fname in DOC_FILES:
            f = d / fname
            if not f.exists():
                continue
            doc_type = fname[:-3]
            rel = f.relative_to(paths.root.parent).as_posix()
            for chunk, h2 in chunker.chunk(
                f.read_text(encoding="utf-8"),
                service_id=sid,
                doc_type=doc_type,
                source_ref=rel,
                aliases=aliases,
                domain=svc.get("domain"),
                summary=svc.get("summary"),
            ):
                rows.append(
                    {
                        "chunk": chunk,
                        "service_id": sid,
                        "domain": svc.get("domain"),
                        "aliases": aliases,
                        "section": h2,
                        "doc_file": rel,
                        "text_hash": compute_text_hash(chunk.display_text),
                    }
                )
    return rows


async def _embed_all(embedder: Any, texts: list[str]) -> list[list[float]]:
    from processing.embeddings.service import EmbeddingError

    out: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i : i + EMBED_BATCH]
        for attempt in range(6):
            try:
                out.extend(await embedder.generate_embeddings(batch))
                break
            except EmbeddingError:
                if attempt == 5:
                    raise
                await asyncio.sleep(2 ** (attempt + 1))
        if (i // EMBED_BATCH) % 10 == 0:
            print(f"  embedded {min(i + EMBED_BATCH, len(texts))}/{len(texts)}", flush=True)
    return out


async def load_docs(
    rows: list[dict[str, Any]],
    *,
    driver: Any,
    qdrant: Any,
    bm25: Any,
    embedder: Any | None,
    run_id: str,
    dry_run: bool,
) -> dict[str, Any]:
    from storage.vector.vector_store import VectorRecord

    require_bm25_corpus(bm25)  # never flush a failed/empty load over the persisted corpus
    ids = [r["chunk"].chunk_id for r in rows]
    existing = await qdrant.retrieve_payloads(ids)
    changed = [r for r in rows if existing.get(r["chunk"].chunk_id, {}).get("text_hash") != r["text_hash"]]
    changed_ids = {r["chunk"].chunk_id for r in changed}
    unchanged = [r for r in rows if r["chunk"].chunk_id not in changed_ids]
    current = set(ids)
    stale_points = [
        p["id"]
        for p in await qdrant.scroll({"must": [{"key": "origin", "match": {"value": ORIGIN}}]}, with_payload=["source_id"])
        if p["payload"].get("source_id") not in current
    ]
    stale_bm25 = [
        k for k, v in bm25._corpus.items()
        if (v.get("metadata") or {}).get("origin") == ORIGIN and k not in current
    ]
    stats: dict[str, Any] = {
        "chunks": len(rows),
        "to_embed": len(changed),
        "unchanged": len(rows) - len(changed),
        "stale_qdrant_points": len(stale_points),
        "stale_bm25_keys": len(stale_bm25),
        "docs": len({r["chunk"].metadata.parent_source_id for r in rows}),
    }
    if dry_run:
        return stats

    # --- Qdrant -------------------------------------------------------------
    now = datetime.now(UTC).isoformat()

    def record(r: dict[str, Any], vector: list[float]) -> VectorRecord:
        c = r["chunk"]
        m = c.metadata
        return VectorRecord(
            source_id=c.chunk_id,
            entity_type="Chunk",
            text_hash=r["text_hash"],
            vector=vector,
            created_at=now,
            section_title=m.section_title,
            repo_name=m.repo_name,
            doc_type=m.doc_type,
            parent_source_id=m.parent_source_id,
            chunk_index=m.chunk_index,
            source_ref=m.source_ref,
            service_id=r["service_id"],
            domain=r["domain"],
            aliases=tuple(r["aliases"]),
            section=r["section"],
            origin=ORIGIN,
        )

    if changed:
        assert embedder is not None
        vectors = await _embed_all(embedder, [r["chunk"].display_text for r in changed])
        recs = [record(r, v) for r, v in zip(changed, vectors, strict=True)]
        for i in range(0, len(recs), 128):
            await qdrant.upsert_embeddings(recs[i : i + 128])
    for r in unchanged:
        payload = qdrant._record_payload(record(r, [0.0] * _dim()))
        payload["created_at"] = existing[r["chunk"].chunk_id].get("created_at", now)
        await qdrant.set_payload([qdrant._point_id_for(r["chunk"].chunk_id)], payload)
    if stale_points:
        await qdrant.delete_points(stale_points)

    # --- BM25 ---------------------------------------------------------------
    from storage.vector.sparse_index import tokenize

    for k in stale_bm25:
        bm25._corpus.pop(k, None)
    for r in rows:
        c = r["chunk"]
        bm25._corpus[c.chunk_id] = {
            "tokens": tokenize(c.display_text),
            "text": c.display_text,
            "metadata": {
                "repo_name": c.metadata.repo_name,
                "doc_type": c.metadata.doc_type,
                "section_title": c.metadata.section_title,
                "parent_source_id": c.metadata.parent_source_id,
                "origin": ORIGIN,
                "service_id": r["service_id"],
            },
        }
    bm25._dirty = True
    bm25.flush()

    # --- Neo4j --------------------------------------------------------------
    docs: dict[str, dict[str, Any]] = {}
    for r in rows:
        m = r["chunk"].metadata
        docs.setdefault(
            m.parent_source_id,
            {
                "source_id": m.parent_source_id,
                "props": {
                    "source_id": m.parent_source_id,
                    "title": f"{r['service_id']} — {m.doc_type}",
                    "doc_type": m.doc_type,
                    "service_id": r["service_id"],
                    "url": r["doc_file"],
                    "origin": ORIGIN,
                    "ingest_run": run_id,
                },
                "service": f"service:{r['service_id']}",
            },
        )
    chunk_rows = [
        {
            "source_id": r["chunk"].chunk_id,
            "parent": r["chunk"].metadata.parent_source_id,
            "props": {
                "source_id": r["chunk"].chunk_id,
                "parent_source_id": r["chunk"].metadata.parent_source_id,
                "chunk_index": r["chunk"].metadata.chunk_index,
                "doc_type": r["chunk"].metadata.doc_type,
                "section_title": r["chunk"].metadata.section_title,
                "service_id": r["service_id"],
                "text": r["chunk"].display_text,
                "text_hash": r["text_hash"],
                "origin": ORIGIN,
                "ingest_run": run_id,
            },
        }
        for r in rows
    ]
    async with driver.session() as s:
        for i in range(0, len(docs), 500):
            res = await s.run(
                "UNWIND $rows AS row "
                "MERGE (d:ServiceDoc {source_id: row.source_id}) SET d = row.props, d.updated_at = datetime() "
                "WITH d, row MATCH (sv:Service {source_id: row.service}) "
                "MERGE (sv)-[r:DOCUMENTED_IN {edge_id: row.source_id}]->(d) "
                "SET r.source = 'repo_docs', r.confidence = 'high', r.evidence = '[]', "
                "r.origin = $origin, r.ingest_run = $run",
                rows=list(docs.values())[i : i + 500],
                origin=ORIGIN,
                run=run_id,
            )
            await res.consume()
        for i in range(0, len(chunk_rows), 500):
            res = await s.run(
                "UNWIND $rows AS row "
                "MERGE (c:Chunk {source_id: row.source_id}) SET c = row.props, c.updated_at = datetime() "
                "WITH c, row MATCH (d:ServiceDoc {source_id: row.parent}) "
                "MERGE (d)-[r:HAS_CHUNK]->(c) SET r.origin = $origin, r.ingest_run = $run, r.source = 'deterministic'",
                rows=chunk_rows[i : i + 500],
                origin=ORIGIN,
                run=run_id,
            )
            await res.consume()
        stale = await run_cypher(
            s,
            "MATCH (n) WHERE (n:Chunk OR n:ServiceDoc) AND n.origin = $origin AND n.ingest_run <> $run "
            "DETACH DELETE n RETURN count(n) AS n",
            origin=ORIGIN,
            run=run_id,
        )
        stats["stale_neo4j_nodes_deleted"] = stale[0]["n"]
    return stats


def _dim() -> int:
    from storage.vector.vector_store import EMBEDDING_DIMENSION

    return EMBEDDING_DIMENSION
