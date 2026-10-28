"""Link the existing Jira tickets / Confluence pages to services (Phase 8 step 4).

No refetch and no re-embedding. Text comes from the live BM25 corpus
(``LocalBM25Index()._corpus``, ``doc_type`` jira/confluence), grouped by
``parent_source_id``; titles come from Neo4j.

Matching uses the shared entity index (``retrieval.search.entity_linker``):
aliases.yaml + aliases.manual.yaml, word-boundary, longest-first. Term tiers:

* high   — exact service_id / repo name, or a manual alias;
* medium — multi-word alias with high/medium confidence, not ambiguous;
* weak   — single-word aliases, low-confidence aliases, ambiguous aliases.

A document links to a service when it has a high/medium term for it, or at least
two distinct weak, unambiguous terms for it (one multi-word) -> ``low``. An
ambiguous term is credited to a candidate only when exactly one candidate is
already linked by those rules (corroboration); otherwise it is skipped and
logged. The LLM fallback stays OFF.

A coverage report is written BEFORE any link is written.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ingestion.repo_docs_ingest.common import EXISTING_DOC_TYPES, LINK_SOURCE, require_bm25_corpus, run_cypher
from retrieval.search.entity_linker import CONF_RANK, EntityIndex


def read_docs(bm25: Any) -> dict[str, dict[str, Any]]:
    """``parent_source_id -> {"doc_type", "repo_name", "text", "chunk_ids"}`` from the BM25 corpus."""

    require_bm25_corpus(bm25)
    docs: dict[str, dict[str, Any]] = {}
    for chunk_id, entry in bm25._corpus.items():
        meta = entry.get("metadata") or {}
        if meta.get("doc_type") not in EXISTING_DOC_TYPES:
            continue
        pid = meta.get("parent_source_id") or chunk_id.split("#chunk:")[0]
        d = docs.setdefault(
            pid,
            {"doc_type": meta.get("doc_type"), "repo_name": meta.get("repo_name"), "parts": [], "chunk_ids": []},
        )
        d["parts"].append(entry.get("text") or "")
        d["chunk_ids"].append(chunk_id)
    for d in docs.values():
        d["text"] = "\n".join(d.pop("parts"))
    return docs


def _tier(term: str, sid: str, conf: str, entry: dict[str, Any], idx: EntityIndex) -> str:
    if idx.canonical.get(term) == sid or conf == "manual":
        return "high"
    if entry["ambiguous"]:
        return "weak"
    if " " in term.strip() and conf in ("high", "medium"):
        return "medium"
    return "weak"


def match_doc(text: str, idx: EntityIndex) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Return ``({sid: {confidence, matched, hits}}, skipped_ambiguous)``."""

    terms = idx.find_terms(text)
    per: dict[str, dict[str, Any]] = defaultdict(lambda: {"tiers": [], "matched": set(), "hits": 0, "weak": set()})
    ambiguous: list[tuple[str, int, dict[str, Any]]] = []
    for term, count in terms.items():
        entry = idx.aliases[term]
        if entry["ambiguous"] and not any(idx.canonical.get(term) == s for s in entry["services"]):
            ambiguous.append((term, count, entry))
            continue
        for sid, conf in entry["services"].items():
            tier = _tier(term, sid, conf, entry, idx)
            p = per[sid]
            p["tiers"].append(tier)
            p["matched"].add(term)
            p["hits"] += count
            if tier == "weak":
                p["weak"].add(term)

    links: dict[str, dict[str, Any]] = {}
    for sid, p in per.items():
        if "high" in p["tiers"]:
            conf = "high"
        elif "medium" in p["tiers"]:
            conf = "medium"
        elif len(p["weak"]) >= 2 and any(" " in t for t in p["weak"]):
            conf = "low"
        else:
            continue
        links[sid] = {"confidence": conf, "matched": set(p["matched"]), "hits": p["hits"]}

    skipped: list[dict[str, Any]] = []
    for term, count, entry in ambiguous:
        linked = [s for s in entry["services"] if s in links]
        if len(linked) == 1:
            links[linked[0]]["matched"].add(term)
            links[linked[0]]["hits"] += count
        else:
            skipped.append({"term": term, "candidates": sorted(entry["services"]), "linked": sorted(linked)})
    for v in links.values():
        v["matched"] = sorted(v["matched"])
    return links, skipped


async def compute_links(driver: Any, idx: EntityIndex, bm25: Any) -> dict[str, Any]:
    docs = read_docs(bm25)
    async with driver.session() as s:
        titles = {
            r["sid"]: r["title"]
            for r in await run_cypher(
                s,
                "MATCH (n) WHERE (n:Ticket OR (n:ConfluencePage AND n.space_key <> 'STEERING')) "
                "RETURN n.source_id AS sid, coalesce(n.key + ' ', '') + coalesce(n.title, '') AS title",
            )
        }
    results: dict[str, Any] = {}
    for pid, d in docs.items():
        text = f"{titles.get(pid, '')}\n{d['repo_name'] or ''}\n{d['text']}"
        links, skipped = match_doc(text, idx)
        results[pid] = {"doc_type": d["doc_type"], "chunk_ids": d["chunk_ids"], "links": links, "skipped": skipped,
                        "in_graph": pid in titles}
    return results


def coverage(results: dict[str, Any]) -> dict[str, Any]:
    by_type: dict[str, Counter[str]] = defaultdict(Counter)
    per_service: dict[str, Counter[str]] = defaultdict(Counter)
    per_term: Counter[str] = Counter()
    skipped_terms: Counter[str] = Counter()
    for pid, r in results.items():
        dt = r["doc_type"]
        by_type[dt]["docs"] += 1
        by_type[dt]["linked_docs"] += bool(r["links"])
        by_type[dt]["links"] += len(r["links"])
        by_type[dt]["not_in_graph"] += not r["in_graph"]
        for sid, link in r["links"].items():
            per_service[sid][f"{dt}_{link['confidence']}"] += 1
            per_service[sid][dt] += 1
            for t in link["matched"]:
                per_term[t] += 1
        for sk in r["skipped"]:
            skipped_terms[sk["term"]] += 1
    return {
        "by_doc_type": {k: dict(v) for k, v in by_type.items()},
        "per_service": {k: dict(v) for k, v in sorted(per_service.items())},
        "top_terms": per_term.most_common(60),
        "skipped_ambiguous_terms": skipped_terms.most_common(),
        "confidence": dict(Counter(l["confidence"] for r in results.values() for l in r["links"].values())),
    }


def write_coverage(report: dict[str, Any], out_md: Path) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.with_suffix(".json").write_text(json.dumps(report, indent=2))
    lines = ["# Phase 8 alias-link coverage (written before any link)", ""]
    lines.append("| doc_type | docs | linked docs | links | not in graph |")
    lines.append("|---|---|---|---|---|")
    for dt, c in sorted(report["by_doc_type"].items()):
        lines.append(f"| {dt} | {c.get('docs', 0)} | {c.get('linked_docs', 0)} | {c.get('links', 0)} | {c.get('not_in_graph', 0)} |")
    lines += ["", f"Link confidence: {report['confidence']}", "", "## Per service", "",
              "| service | jira | confluence | detail |", "|---|---|---|---|"]
    for sid, c in report["per_service"].items():
        detail = ", ".join(f"{k}={v}" for k, v in sorted(c.items()) if "_" in k)
        lines.append(f"| {sid} | {c.get('jira', 0)} | {c.get('confluence', 0)} | {detail} |")
    lines += ["", "## Top matched terms (docs)", ""] + [f"- `{t}`: {n}" for t, n in report["top_terms"]]
    lines += ["", "## Ambiguous terms skipped (no single corroborated candidate)", ""]
    lines += [f"- `{t}`: {n} docs" for t, n in report["skipped_ambiguous_terms"]] or ["- none"]
    out_md.write_text("\n".join(lines) + "\n")


async def write_links(driver: Any, qdrant: Any, bm25: Any, results: dict[str, Any], run_id: str) -> dict[str, Any]:
    require_bm25_corpus(bm25)  # bm25.flush() below must never persist a failed load
    ticket_rows, page_rows = [], []
    for pid, r in results.items():
        for sid, link in r["links"].items():
            row = {"doc": pid, "svc": f"service:{sid}", "props": {
                "source": LINK_SOURCE, "confidence": link["confidence"], "matched": link["matched"],
                "hits": link["hits"], "origin": LINK_SOURCE, "ingest_run": run_id, "evidence": "[]",
                "edge_id": f"{LINK_SOURCE}:{pid}:{sid}"}}
            (ticket_rows if r["doc_type"] == "jira" else page_rows).append(row)
    async with driver.session() as s:
        deleted = (await run_cypher(
            s, "MATCH ()-[r]->() WHERE r.source = $src AND type(r) IN ['LINKED_TO','DOCUMENTED_IN'] "
               "DELETE r RETURN count(r) AS n", src=LINK_SOURCE))[0]["n"]
        written = {}
        for name, rows, cypher in (
            ("LINKED_TO", ticket_rows,
             "MATCH (t:Ticket {source_id: row.doc}) MATCH (sv:Service {source_id: row.svc}) "
             "MERGE (t)-[r:LINKED_TO {edge_id: row.props.edge_id}]->(sv) SET r = row.props RETURN count(r) AS n"),
            ("DOCUMENTED_IN", page_rows,
             "MATCH (p:ConfluencePage {source_id: row.doc}) MATCH (sv:Service {source_id: row.svc}) "
             "MERGE (sv)-[r:DOCUMENTED_IN {edge_id: row.props.edge_id}]->(p) SET r = row.props RETURN count(r) AS n"),
        ):
            n = 0
            for i in range(0, len(rows), 1000):
                res = await s.run("UNWIND $rows AS row " + cypher, rows=rows[i : i + 1000])
                n += (await res.single())["n"]
            written[name] = n

    # Metadata-only service_ids on the existing Jira/Confluence points (no vector change).
    await qdrant.delete_payload_keys(
        ["service_ids"], {"must": [{"key": "doc_type", "match": {"any": ["jira", "confluence"]}}]}
    )
    groups: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for pid, r in results.items():
        sids = tuple(sorted(r["links"]))
        if sids:
            groups[sids].extend(qdrant._point_id_for(c) for c in r["chunk_ids"])
            groups[sids].append(qdrant._point_id_for(pid))  # Ticket / ConfluencePage entity vector
    existing_ids = {qdrant._point_id_for(k) for k in (await qdrant.retrieve_payloads(
        [pid for pid in results] + [c for r in results.values() for c in r["chunk_ids"]]))}
    points = 0
    for sids, pids in groups.items():
        pids = [p for p in pids if p in existing_ids]
        await qdrant.set_payload(pids, {"service_ids": list(sids)})
        points += len(pids)

    bm25_updated = 0
    for pid, r in results.items():
        sids = sorted(r["links"])
        for cid in r["chunk_ids"]:
            entry = bm25._corpus.get(cid)
            if entry is None:
                continue
            meta = entry.setdefault("metadata", {})
            if sids:
                meta["service_ids"] = sids
                bm25_updated += 1
            else:
                meta.pop("service_ids", None)
    bm25.flush()
    return {"deleted_old_links": deleted, "written": written, "qdrant_points_tagged": points,
            "bm25_chunks_tagged": bm25_updated}
