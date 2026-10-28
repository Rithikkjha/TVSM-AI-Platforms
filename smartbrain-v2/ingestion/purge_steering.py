"""One-off purge of the old steering data from Qdrant + BM25 + Neo4j (Phase 8 step 1).

Dry-run by default: it only counts what would be removed and compares the
counts with the investigation report (section 3, "Steering footprint to purge").

    python3.11 -m ingestion.purge_steering                # dry-run, counts only
    python3.11 -m ingestion.purge_steering --execute      # back up, then purge, then verify

With ``--execute`` the script first writes a backup under
``backups/phase8-purge-<ts>/`` (BM25 pickle copy, a Qdrant collection snapshot,
a JSONL export of every Neo4j node/relationship it is about to delete, and a
manifest), and only then deletes. Anything stamped ``origin: repo_docs`` is
never touched, so re-running after the new ingest is safe.

What is removed (design §5(d)):
* every chunk whose ``doc_type`` is not ``jira``/``confluence`` (BM25 keys,
  Qdrant points, Neo4j ``Chunk`` nodes);
* ``ConfluencePage {space_key:'STEERING'}`` nodes and their entity vectors;
* all steering ``Service`` nodes and their entity vectors;
* all ``ServiceBusTopic`` and ``Database`` nodes (with the ``dependency_graph``
  edges, ``DOCUMENTED_IN`` edges and steering ``DUPLICATE_OF`` edges, via DETACH).
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from ingestion.repo_docs_ingest.common import ORIGIN, PROJECT_ROOT, neo4j_driver, qdrant_store, run_cypher

KEEP_DOC_TYPES = ("jira", "confluence")

#: Investigation report §3 counts. A mismatch aborts ``--execute`` unless
#: ``--allow-mismatch`` is given.
EXPECTED: dict[str, int] = {
    "bm25_steering_chunks": 3628,
    "qdrant_steering_chunks": 3628,
    "neo4j_steering_chunks": 3628,
    "neo4j_steering_pages": 294,
    "neo4j_services": 97,
    "neo4j_servicebus_topics": 7,
    "neo4j_databases": 3,
    "neo4j_dependency_graph_edges": 70,
    "qdrant_service_vectors": 75,
    "qdrant_steering_page_vectors": 294,
}

# Cypher predicates (shared by count / export / delete).
_CHUNK_WHERE = (
    "NOT coalesce(c.doc_type, '') IN $keep AND coalesce(c.origin, '') <> $origin"
)
_SERVICE_WHERE = "coalesce(s.origin, '') <> $origin"


def _qdrant_chunk_filter() -> dict[str, Any]:
    return {
        "must": [{"key": "entity_type", "match": {"value": "Chunk"}}],
        "must_not": [
            {"key": "doc_type", "match": {"any": list(KEEP_DOC_TYPES)}},
            {"key": "origin", "match": {"value": ORIGIN}},
        ],
    }


def _qdrant_service_filter() -> dict[str, Any]:
    return {
        "must": [{"key": "entity_type", "match": {"value": "Service"}}],
        "must_not": [{"key": "origin", "match": {"value": ORIGIN}}],
    }


def _bm25_path() -> Path:
    from storage.vector.sparse_index import DEFAULT_BM25_INDEX_PATH

    return DEFAULT_BM25_INDEX_PATH


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


async def collect(bm25: Any, driver: Any, qdrant: Any) -> dict[str, Any]:
    """Read-only: gather the ids/counts of everything the purge would remove."""

    corpus: dict[str, Any] = bm25._corpus
    bm25_keys = sorted(
        k
        for k, v in corpus.items()
        if (v.get("metadata") or {}).get("doc_type") not in KEEP_DOC_TYPES
        and (v.get("metadata") or {}).get("origin") != ORIGIN
    )
    params = {"keep": list(KEEP_DOC_TYPES), "origin": ORIGIN}
    async with driver.session() as s:
        chunk_ids = [
            r["sid"]
            for r in await run_cypher(
                s, f"MATCH (c:Chunk) WHERE {_CHUNK_WHERE} RETURN c.source_id AS sid", **params
            )
        ]
        page_ids = [
            r["sid"]
            for r in await run_cypher(
                s,
                "MATCH (p:ConfluencePage {space_key:'STEERING'}) RETURN p.source_id AS sid",
            )
        ]
        services = await run_cypher(
            s,
            f"MATCH (s:Service) WHERE {_SERVICE_WHERE} RETURN s.source_id AS sid, s.name AS name",
            **params,
        )
        topics = (await run_cypher(s, "MATCH (t:ServiceBusTopic) RETURN count(t) AS n"))[0]["n"]
        dbs = (await run_cypher(s, "MATCH (d:Database) RETURN count(d) AS n"))[0]["n"]
        dep_edges = (
            await run_cypher(
                s, "MATCH ()-[r]->() WHERE r.source = 'dependency_graph' RETURN count(r) AS n"
            )
        )[0]["n"]
        documented_in = (
            await run_cypher(
                s,
                "MATCH (:Service)-[r:DOCUMENTED_IN]->(:ConfluencePage {space_key:'STEERING'}) "
                "RETURN count(r) AS n",
            )
        )[0]["n"]
        dup_edges = (
            await run_cypher(
                s,
                f"MATCH (c:Chunk)-[r:DUPLICATE_OF]-() WHERE {_CHUNK_WHERE} "
                "RETURN count(DISTINCT r) AS n",
                **params,
            )
        )[0]["n"]

    q_chunks = await qdrant.scroll(_qdrant_chunk_filter(), with_payload=["source_id"])
    q_services = await qdrant.scroll(_qdrant_service_filter(), with_payload=["source_id"])
    q_pages = await qdrant.retrieve_payloads(page_ids)

    point_ids: set[str] = {p["id"] for p in q_chunks} | {p["id"] for p in q_services}
    point_ids |= {qdrant._point_id_for(sid) for sid in q_pages}
    # Also every existing point keyed by a steering BM25 key (normally the same
    # set as the scroll above; this catches points with an odd payload).
    point_ids |= {qdrant._point_id_for(sid) for sid in await qdrant.retrieve_payloads(bm25_keys)}

    return {
        "bm25_keys": bm25_keys,
        "chunk_ids": chunk_ids,
        "page_ids": page_ids,
        "services": services,
        "qdrant_point_ids": sorted(point_ids),
        "counts": {
            "bm25_steering_chunks": len(bm25_keys),
            "qdrant_steering_chunks": len(q_chunks),
            "neo4j_steering_chunks": len(chunk_ids),
            "neo4j_steering_pages": len(page_ids),
            "neo4j_services": len(services),
            "neo4j_servicebus_topics": topics,
            "neo4j_databases": dbs,
            "neo4j_dependency_graph_edges": dep_edges,
            "neo4j_documented_in_steering": documented_in,
            "neo4j_steering_duplicate_of": dup_edges,
            "qdrant_service_vectors": len(q_services),
            "qdrant_steering_page_vectors": len(q_pages),
            "qdrant_points_to_delete": len(point_ids),
        },
    }


async def _export_neo4j(driver: Any, out: Path) -> dict[str, int]:
    """JSONL export of every node (and its relationships) the purge deletes."""

    params = {"keep": list(KEEP_DOC_TYPES), "origin": ORIGIN}
    node_match = (
        "CALL { "
        f"  MATCH (c:Chunk) WHERE {_CHUNK_WHERE} RETURN c AS n "
        "  UNION MATCH (n:ConfluencePage {space_key:'STEERING'}) RETURN n "
        f"  UNION MATCH (s:Service) WHERE {_SERVICE_WHERE} RETURN s AS n "
        "  UNION MATCH (n:ServiceBusTopic) RETURN n "
        "  UNION MATCH (n:Database) RETURN n "
        "} "
    )
    nodes = rels = 0
    async with driver.session() as s:
        with out.open("w", encoding="utf-8") as fh:
            result = await s.run(
                node_match
                + "RETURN elementId(n) AS eid, labels(n) AS labels, properties(n) AS props",
                **params,
            )
            async for rec in result:
                fh.write(json.dumps({"kind": "node", **dict(rec)}, default=str) + "\n")
                nodes += 1
            result = await s.run(
                node_match
                + "MATCH (n)-[r]-(m) WITH DISTINCT r "
                "RETURN elementId(r) AS eid, type(r) AS type, "
                "elementId(startNode(r)) AS start_eid, startNode(r).source_id AS start_sid, "
                "startNode(r).name AS start_name, labels(startNode(r)) AS start_labels, "
                "elementId(endNode(r)) AS end_eid, endNode(r).source_id AS end_sid, "
                "endNode(r).name AS end_name, labels(endNode(r)) AS end_labels, "
                "properties(r) AS props",
                **params,
            )
            async for rec in result:
                fh.write(json.dumps({"kind": "rel", **dict(rec)}, default=str) + "\n")
                rels += 1
    return {"nodes": nodes, "relationships": rels}


async def _snapshot_qdrant(out_dir: Path) -> dict[str, Any]:
    import httpx

    from config.settings import get_settings
    from storage.vector.vector_store import DEFAULT_INDEX_NAME

    base = get_settings().qdrant_url.rstrip("/")
    coll = DEFAULT_INDEX_NAME
    async with httpx.AsyncClient(base_url=base, timeout=600.0) as client:
        resp = await client.post(f"/collections/{coll}/snapshots", params={"wait": "true"})
        resp.raise_for_status()
        name = resp.json()["result"]["name"]
        target = out_dir / name
        async with client.stream("GET", f"/collections/{coll}/snapshots/{name}") as stream:
            stream.raise_for_status()
            with target.open("wb") as fh:
                async for block in stream.aiter_bytes(1 << 20):
                    fh.write(block)
    return {"snapshot": name, "path": str(target), "bytes": target.stat().st_size}


async def _delete(bm25: Any, driver: Any, qdrant: Any, plan: dict[str, Any]) -> None:
    await qdrant.delete_points(plan["qdrant_point_ids"])

    for key in plan["bm25_keys"]:
        bm25._corpus.pop(key, None)
    bm25._dirty = True
    bm25.flush()

    params = {"keep": list(KEEP_DOC_TYPES), "origin": ORIGIN}
    batches = [
        f"MATCH (c:Chunk) WHERE {_CHUNK_WHERE} WITH c LIMIT 2000 DETACH DELETE c RETURN count(*) AS n",
        "MATCH (n:ConfluencePage {space_key:'STEERING'}) WITH n LIMIT 2000 DETACH DELETE n RETURN count(*) AS n",
        f"MATCH (s:Service) WHERE {_SERVICE_WHERE} WITH s LIMIT 2000 DETACH DELETE s RETURN count(*) AS n",
        "MATCH (n:ServiceBusTopic) WITH n LIMIT 2000 DETACH DELETE n RETURN count(*) AS n",
        "MATCH (n:Database) WITH n LIMIT 2000 DETACH DELETE n RETURN count(*) AS n",
    ]
    async with driver.session() as s:
        for stmt in batches:
            while (await run_cypher(s, stmt, **params))[0]["n"]:
                pass


async def _keep_counts(bm25: Any, driver: Any, qdrant: Any) -> dict[str, int]:
    """Counts of the Jira/Confluence data, which must not change."""

    corpus = bm25._corpus
    out = {
        f"bm25_{dt}": sum(1 for v in corpus.values() if (v.get("metadata") or {}).get("doc_type") == dt)
        for dt in KEEP_DOC_TYPES
    }
    for dt in KEEP_DOC_TYPES:
        out[f"qdrant_{dt}"] = await qdrant.count(
            {"must": [{"key": "entity_type", "match": {"value": "Chunk"}},
                      {"key": "doc_type", "match": {"value": dt}}]}
        )
    async with driver.session() as s:
        out["neo4j_tickets"] = (await run_cypher(s, "MATCH (t:Ticket) RETURN count(t) AS n"))[0]["n"]
        out["neo4j_confluence_pages_cm_ccp"] = (
            await run_cypher(
                s, "MATCH (p:ConfluencePage) WHERE p.space_key <> 'STEERING' RETURN count(p) AS n"
            )
        )[0]["n"]
    out["qdrant_total"] = await qdrant.count()
    return out


async def main_async(execute: bool, allow_mismatch: bool) -> int:
    from storage.vector.sparse_index import LocalBM25Index

    bm25 = LocalBM25Index(_bm25_path())
    driver = neo4j_driver()
    qdrant = qdrant_store()
    try:
        plan = await collect(bm25, driver, qdrant)
        keep_before = await _keep_counts(bm25, driver, qdrant)
        counts = plan["counts"]
        print("Steering footprint (actual vs expected):")
        mismatch = False
        for key, value in counts.items():
            exp = EXPECTED.get(key)
            flag = "" if exp is None or exp == value else "  <-- MISMATCH"
            mismatch |= bool(flag)
            print(f"  {key:34s} {value:>7}" + (f"  (expected {exp})" if exp is not None else "") + flag)
        print("Jira/Confluence counts (must stay unchanged):")
        for key, value in keep_before.items():
            print(f"  {key:34s} {value:>7}")

        if not execute:
            print("\nDRY RUN — nothing was backed up or deleted. Re-run with --execute.")
            return 0
        if mismatch and not allow_mismatch:
            print("\nAborting: counts differ from the report. Use --allow-mismatch to override.")
            return 1
        if not any(counts[k] for k in EXPECTED):
            print("\nNothing to purge.")
            return 0

        ts = datetime.now(UTC).strftime("%Y-%m-%d-%H%M%S")
        out_dir = PROJECT_ROOT / "backups" / f"phase8-purge-{ts}"
        out_dir.mkdir(parents=True, exist_ok=False)
        print(f"\nBacking up to {out_dir} ...")
        bm25_src = _bm25_path()
        shutil.copy2(bm25_src, out_dir / "bm25_index.pkl")
        manifest: dict[str, Any] = {
            "created_at": ts,
            "bm25": {"source": str(bm25_src), "md5": _md5(out_dir / "bm25_index.pkl")},
        }
        manifest["qdrant"] = await _snapshot_qdrant(out_dir)
        manifest["neo4j_export"] = await _export_neo4j(driver, out_dir / "neo4j_export.jsonl")
        manifest["counts"] = counts
        manifest["keep_before"] = keep_before
        (out_dir / "purge_plan.json").write_text(
            json.dumps({k: v for k, v in plan.items() if k != "counts"}, indent=2, default=str)
        )
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
        print(json.dumps(manifest, indent=2, default=str))

        print("\nPurging ...")
        await _delete(bm25, driver, qdrant, plan)

        after = (await collect(bm25, driver, qdrant))["counts"]
        keep_after = await _keep_counts(bm25, driver, qdrant)
        manifest["after"] = after
        manifest["keep_after"] = keep_after
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
        print("After purge:")
        for key, value in after.items():
            print(f"  {key:34s} {value:>7}")
        ok = not any(after.values()) and all(
            keep_after[k] == keep_before[k] for k in keep_before if k != "qdrant_total"
        )
        print(
            f"  qdrant_total {keep_before['qdrant_total']} -> {keep_after['qdrant_total']}"
        )
        print("VERIFIED" if ok else "VERIFICATION FAILED")
        return 0 if ok else 1
    finally:
        await driver.close()
        await qdrant.close()


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--execute", action="store_true", help="back up, then purge (default: dry-run)")
    parser.add_argument("--allow-mismatch", action="store_true", help="purge even if counts differ")
    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args.execute, args.allow_mismatch)))


if __name__ == "__main__":
    main()
