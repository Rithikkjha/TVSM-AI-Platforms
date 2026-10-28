"""CLI: ``python3.11 -m ingestion.repo_docs_ingest --org TVS-CS [--graph] [--docs] [--link] [--link-entities] [--dry-run]``.

No step flag = all four. ``--docs`` also re-runs ``--link-entities`` (chunk ids may change). ``--dry-run`` reads the stores and prints counts only
(the link step still writes its coverage report, which is the point of a dry run).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import UTC, datetime

from dotenv import load_dotenv

from ingestion.repo_docs_ingest.common import (
    PROJECT_ROOT,
    REPO_DOCS_ROOT,
    OrgPaths,
    neo4j_driver,
    qdrant_store,
    require_bm25_corpus,
)

COVERAGE_MD = REPO_DOCS_ROOT / ".agents" / "tasks" / "phase8" / "link-coverage.md"
QDRANT_INDEXES = ("origin", "entity_type", "doc_type", "repo_name", "parent_source_id")


def _p(title: str, data: object) -> None:
    print(f"\n== {title}\n{json.dumps(data, indent=2, default=str)}", flush=True)


async def run(args: argparse.Namespace) -> int:
    from ingestion.repo_docs_ingest import alias_linker, chunk_linker, docs_loader, graph_loader
    from ingestion.repo_docs_ingest.schema import ensure_schema
    from retrieval.search.entity_linker import build_index
    from storage.vector.sparse_index import LocalBM25Index

    do_all = not (args.graph or args.docs or args.link or args.link_entities)
    paths = OrgPaths(REPO_DOCS_ROOT, args.org)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    driver = neo4j_driver()
    qdrant = qdrant_store()
    bm25 = None
    try:
        if not args.dry_run:
            _p("neo4j constraints", [c["name"] for c in await ensure_schema(driver)])
            for f in QDRANT_INDEXES:
                await qdrant.create_keyword_index(f)

        if do_all or args.graph:
            t = time.time()
            plan = graph_loader.build_graph(graph_loader.load_inputs(paths))
            _p("graph plan", {**plan.counts(), "warnings": plan.warnings[:20]})
            if not args.dry_run:
                _p("graph load", await graph_loader.load_graph(driver, plan, run_id))
                _p("graph counts (origin=repo_docs)", await graph_loader.graph_counts(driver))
            print(f"graph step {time.time() - t:.1f}s")

        if do_all or args.docs or args.link:
            bm25 = LocalBM25Index()
            _p("bm25 existing corpus", require_bm25_corpus(bm25))

        if do_all or args.docs:
            t = time.time()
            rows = docs_loader.build_chunks(paths)
            embedder = None
            if not args.dry_run:
                from config.settings import get_settings
                from processing.embeddings.service import get_embedding_service

                embedder = get_embedding_service(get_settings())
            try:
                stats = await docs_loader.load_docs(
                    rows, driver=driver, qdrant=qdrant, bm25=bm25, embedder=embedder,
                    run_id=run_id, dry_run=args.dry_run,
                )
            finally:
                if embedder is not None:
                    await embedder.close()
            _p("docs", stats)
            print(f"docs step {time.time() - t:.1f}s")

        if do_all or args.link:
            t = time.time()
            idx = build_index(REPO_DOCS_ROOT, args.org)
            results = await alias_linker.compute_links(driver, idx, bm25)
            report = alias_linker.coverage(results)
            alias_linker.write_coverage(report, COVERAGE_MD)
            _p("link coverage", {"by_doc_type": report["by_doc_type"], "confidence": report["confidence"],
                                 "report": str(COVERAGE_MD)})
            if not args.dry_run:
                _p("links", await alias_linker.write_links(driver, qdrant, bm25, results, run_id))
            print(f"link step {time.time() - t:.1f}s")

        if do_all or args.docs or args.link_entities:
            t = time.time()
            _p("chunk -> entity DESCRIBES", await chunk_linker.link_chunks(driver, run_id, dry_run=args.dry_run))
            print(f"link-entities step {time.time() - t:.1f}s")
        if args.dry_run:
            print("\nDRY RUN — no store was written.")
        return 0
    finally:
        await driver.close()
        await qdrant.close()


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)
    ap = argparse.ArgumentParser(description="Ingest repo_docs output into Neo4j/Qdrant/BM25")
    ap.add_argument("--org", required=True)
    ap.add_argument("--graph", action="store_true")
    ap.add_argument("--docs", action="store_true")
    ap.add_argument("--link", action="store_true")
    ap.add_argument("--link-entities", action="store_true", help="(Chunk)-[:DESCRIBES]->(Endpoint|Topic|Flow)")
    ap.add_argument("--dry-run", action="store_true")
    sys.exit(asyncio.run(run(ap.parse_args())))


if __name__ == "__main__":
    main()
