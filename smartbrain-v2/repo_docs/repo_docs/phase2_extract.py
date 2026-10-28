"""Phase 2: deterministic extraction (docs/PIPELINE.md#phase-2--deterministic-extraction).

Per repo: run every applicable extractor (fixed order) over the ledgered files, merge items by id
(EXTRACTORS rule 6), classify repo_type, match external systems, validate every item, then write
inventory.json and gaps.json (sorted keys, byte-identical for the same input), recompute ledger
statuses and merge meta.json. Any extractor exception or validation failure fails the repo and leaves the
previous outputs untouched. No network access.
"""
from __future__ import annotations

import copy
import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import coverage, external_systems, gaps, gitops, paths, phase1_ledger as p1
from .config import OrgConfig
from .extractors import registry as reg
from .extractors.base import FileTouch, InventoryItem, RepoContext
from .inventory_schema import validate_item
from .repo_type import classify_repo
from .secrets import SecretFilter, redact
from .state import StateStore

PHASE_VERSION = "0.1.2"
log = logging.getLogger(__name__)


class ExtractError(RuntimeError):
    pass


# ---- versions ------------------------------------------------------------------------------
def extractor_versions(meta: dict) -> dict[str, str]:
    return {ex.id: ex.extractor_version for ex, _ in reg.applicable(meta or {})}


def current_version(meta: dict, registry_bytes: bytes) -> str:
    """Composite ``"<PHASE_VERSION>+<h12>"`` over applicable extractor versions, the gaps.json
    builder version and the registry hash."""
    vers = extractor_versions(meta)
    joined = ",".join(sorted(f"{k}@{v}" for k, v in vers.items())) + f",gaps@{gaps.GAPS_VERSION}"
    rhash = hashlib.sha1(registry_bytes).hexdigest()
    return f"{PHASE_VERSION}+{hashlib.sha1((joined + '|' + rhash).encode()).hexdigest()[:12]}"


def registry_bytes() -> bytes:
    try:
        return paths.external_systems_path().read_bytes()
    except FileNotFoundError:
        return b""


def status_inputs(org: str, repo: str, reg_bytes: bytes) -> tuple[str | None, str | None]:
    """(current extract version, ledger generated_at) from meta.json, for ``status``. A done
    extract whose gaps.json is missing reports a version that cannot match (-> stale)."""
    out = paths.runs_dir(org, repo)
    meta = paths.read_json(out / "meta.json", None)
    if not meta:
        return None, None
    ver = current_version(meta, reg_bytes)
    if meta.get("extract") and not (out / "gaps.json").exists():
        ver += "+gaps-missing"
    return ver, (meta.get("ledger") or {}).get("generated_at")


# ---- merge (rule 6) ------------------------------------------------------------------------
def _key(v) -> str:
    return json.dumps(v, sort_keys=True, ensure_ascii=False, default=str)


def _empty(v) -> bool:
    return v is None or v == [] or v == {}


def _merge_values(vals: list) -> tuple[object, bool]:
    vals = [v for v in vals if not _empty(v)]
    if not vals:
        return None, False
    distinct = []
    for v in vals:
        if _key(v) not in {_key(d) for d in distinct}:
            distinct.append(v)
    if len(distinct) == 1:
        return distinct[0], False
    if all(isinstance(v, list) for v in distinct):
        seen, out = set(), []
        for v in distinct:
            for x in v:
                k = _key(x)
                if k not in seen:
                    seen.add(k)
                    out.append(x)
        return sorted(out, key=_key), False
    if all(isinstance(v, dict) for v in distinct):
        out, conflict = {}, False
        for k in sorted({k for v in distinct for k in v}):
            mv, c = _merge_values([v.get(k) for v in distinct])
            out[k] = mv
            conflict |= c
        return out, conflict
    return sorted(distinct, key=_key), True


def _dedupe_responses(rows: list) -> list:
    """One ``responses`` entry per status: the code entry wins, empty fields are filled from the
    others (contract ``when`` text, schema)."""
    by: dict = {}
    for r in rows:
        if not isinstance(r, dict):
            return rows
        by.setdefault(_key(r.get("status")), []).append(r)
    out = []
    for k in sorted(by):
        rs = sorted(by[k], key=lambda r: (r.get("from") == "contract", _key(r)))
        m = dict(rs[0])
        for r in rs[1:]:
            for f, v in r.items():
                if _empty(m.get(f)) and not _empty(v):
                    m[f] = v
        out.append(m)
    return out


def merge_items(items: list[InventoryItem]) -> list[InventoryItem]:
    """Rule 6: one item per id. Code beats contract: when a code and a contract item disagree
    on a scalar, the code value is kept (contract fills only empty attributes) and the code
    extractor is credited. ``role``: runtime beats tests_target. Other scalar conflicts keep
    both values as a sorted list and drop confidence to medium."""
    groups: dict[str, list[InventoryItem]] = {}
    for it in items:
        groups.setdefault(it.id, []).append(it)
    out = []
    for iid in sorted(groups):
        g = groups[iid]
        first = g[0]
        if len(g) == 1:
            out.append(first)
            continue
        code = [x for x in g if x.source == "code"]
        primary = code or g
        runtime = [x for x in primary if x.attributes.get("role") == "runtime"]
        if runtime and len(runtime) < len(primary):
            primary = runtime          # a runtime call also mocked in a test stays runtime
        lead = next((x for x in primary if not x.extractor_id.startswith("shared.")), primary[0])
        attrs, conflict = {}, False
        for k in first.attributes:
            dflt = first.attributes[k]
            mv, c = _merge_values([x.attributes.get(k) for x in g])
            if c and len(primary) < len(g):
                pm, pc = _merge_values([x.attributes.get(k) for x in primary])
                if pm is not None:
                    mv, c = pm, pc
            if k == "responses" and isinstance(mv, list):
                mv = _dedupe_responses(mv)
            attrs[k] = mv if mv is not None else ([] if isinstance(dflt, list) else
                                                  {} if isinstance(dflt, dict) else None)
            conflict |= c
        ev = sorted({e for x in g for e in x.evidence}, key=lambda e: (e.file, e.line, e.snippet))
        out.append(InventoryItem(
            id=iid, kind=first.kind, subproject=first.subproject, attributes=attrs, evidence=ev,
            source="code" if code else first.source,
            extractor_id=lead.extractor_id, extractor_version=lead.extractor_version,
            confidence="medium" if conflict or any(x.confidence == "medium" for x in g)
            else "high"))
    return out


NON_RUNTIME_DIRS = frozenset({"script", "scripts", "tools"})


def _non_runtime(path: str) -> bool:
    """True for files under a ``script/``, ``scripts/`` or ``tools/`` directory (one-off
    loaders and utilities, not part of the deployed service)."""
    return any(seg in NON_RUNTIME_DIRS for seg in path.split("/")[:-1])


# ---- core ----------------------------------------------------------------------------------
def build_context(org: OrgConfig, repo: str, ledger: dict, meta: dict,
                  systems: list[dict]) -> RepoContext:
    return RepoContext(org.name, repo, paths.clone_dir(org.name, repo), ledger, meta, systems,
                       org.internal_package_patterns)


def run(ctx: RepoContext) -> dict:
    """Run extractors + post-processing on a context. Returns items, touches, errors, repo_type.
    Raises on extractor exceptions (the caller fails the repo)."""
    items: list[InventoryItem] = []
    touches: dict[str, list[tuple[str, str, FileTouch, int]]] = {}
    for ex, sub in reg.applicable(ctx.meta):
        res = ex.extract(ctx, sub)
        per_file: dict[str, set] = {}
        for it in res.items:
            for e in it.evidence:
                per_file.setdefault(e.file, set()).add(it.id)
        for path, t in sorted(res.touched.items()):
            touches.setdefault(path, []).append((ex.id, ex.extractor_version, t,
                                                 len(per_file.get(path, ()))))
        items.extend(res.items)
    items = merge_items(items)
    rt = classify_repo(ctx, items)
    for it in items:
        if rt["value"] == "test-suite" and it.kind == "outbound_http":
            it.attributes["role"] = "tests_target"
        if it.kind == "messaging":
            it.attributes["role"] = "script" if all(
                _non_runtime(e.file) for e in it.evidence) else "runtime"
        if rt["value"] == "db-migration" and it.kind == "data_access" and \
                it.extractor_id == "shared.sql":
            it.attributes["owns_schema"] = True
    items = merge_items(items + external_systems.match(ctx, items))
    errors = []
    for path in sorted(touches):
        for ex_id, _v, t, _n in sorted(touches[path], key=lambda x: x[0]):
            if t.error:
                errors.append({"level": "file", "file": path, "extractor": ex_id,
                               "reason": redact(t.error, SecretFilter.secrets())[:500]})
    return {"items": sorted(items, key=lambda i: (i.kind, i.id)), "touches": touches,
            "errors": errors, "repo_type": rt}


def validate(ctx: RepoContext, items: list[InventoryItem]) -> list[str]:
    problems: list[str] = []
    for it in items:
        problems += validate_item(it, ctx.ledger_index, ctx.line)
    return problems


def recompute_ledger(ctx: RepoContext, ledger: dict, touches: dict) -> dict:
    new = copy.deepcopy(ledger)
    for f in new["files"]:
        st = f.get("status") or ""
        if st.startswith("skipped:"):
            continue
        tl = touches.get(f["path"])
        if tl:
            ents = []
            for ex_id, ver, t, n in sorted(tl, key=lambda x: x[0]):
                e = {"id": ex_id, "version": ver, "parse": t.parse, "items": n}
                if t.error:
                    e["error"] = redact(t.error, SecretFilter.secrets())[:500]
                ents.append(e)
            f["extractors"] = ents
        else:
            f.pop("extractors", None)
        if st.startswith("failed:"):
            continue
        llm = f.get("llm")
        data = ctx.read_bytes(f["path"]) if llm else None
        if llm and data is not None and llm.get("content_sha1") == hashlib.sha1(data).hexdigest():
            f["status"] = "scanned"
        elif any(e["parse"] == "full" for e in f.get("extractors") or []):
            f["status"] = "extracted"
        else:
            f["status"] = "pending"
    if [f["path"] for f in new["files"]] != [f["path"] for f in ledger["files"]]:
        raise ExtractError("ledger path set changed during extract")
    return new


def _counts(ledger: dict, items: list[InventoryItem], touches: dict) -> dict:
    files = [f for f in ledger["files"] if not (f.get("status") or "").startswith("skipped:")]
    by_kind: dict[str, int] = {}
    for it in items:
        by_kind[it.kind] = by_kind.get(it.kind, 0) + 1
    extracted = sum(1 for f in files if f["status"] == "extracted")
    touched = [f for f in files if f["path"] in touches]
    return {
        "items": len(items), "by_kind": dict(sorted(by_kind.items())),
        "files_extracted": extracted,
        "files_partial": sum(1 for f in touched if f["status"] != "extracted"
                             and not f["status"].startswith("failed:")),
        "files_untouched": sum(1 for f in files if f["path"] not in touches
                               and not f["status"].startswith("failed:")),
        "file_errors": sum(1 for p, tl in touches.items() if any(t.error for _, _, t, _ in tl)),
        "files_failed": len(coverage.ledger_gate(ledger)["failed"]),
    }


def extract_one(org: OrgConfig, store: StateStore, repo: str, force: bool = False,
                systems: list[dict] | None = None, reg_bytes: bytes | None = None) -> str:
    cur = store.phase(org.name, repo, "extract")
    store.set_phase(org.name, repo, "extract", status="running", started_at=paths.utcnow(),
                    attempts=int(cur.get("attempts") or 0) + 1, error=None)
    try:
        if reg_bytes is None or systems is None:
            systems, _h, reg_bytes = external_systems.load_registry()
        rhash = hashlib.sha1(reg_bytes).hexdigest()
        rec = store.repo(org.name, repo) or {}
        if StateStore.effective_from(rec, "ledger", p1.PHASE_VERSION) != "done":
            raise ExtractError("ledger not done or stale; run ledger first")
        dest = paths.clone_dir(org.name, repo)
        head = gitops.head_sha(dest)
        if head != rec.get("head_sha"):
            raise ExtractError(f"clone HEAD {head[:12]} != state head_sha; re-run clone")
        out_dir = paths.runs_dir(org.name, repo)
        ledger = paths.read_json(out_dir / "ledger.json", None)
        meta = paths.read_json(out_dir / "meta.json", None) or {}
        if not ledger or ledger.get("head_sha") != head:
            raise ExtractError("ledger.json missing or for another head_sha; run ledger")
        ctx = build_context(org, repo, ledger, meta, systems)
        res = run(ctx)
        problems = validate(ctx, res["items"])
        if problems:
            more = f" (+{len(problems) - 5} more)" if len(problems) > 5 else ""
            raise ExtractError(f"{len(problems)} invalid item(s): " + "; ".join(problems[:5]) + more)
        version = current_version(meta, reg_bytes)
        vers = dict(sorted(extractor_versions(meta).items()))
        new_ledger = recompute_ledger(ctx, ledger, res["touches"])
        counts = _counts(new_ledger, res["items"], res["touches"])
        missing = reg.missing_extractors(meta)
        inventory = {
            "schema_version": 1, "org": org.name, "repo": repo,
            "service_id": rec.get("service_id"), "head_sha": head,
            "phase_version": PHASE_VERSION, "version": version, "extractor_versions": vers,
            "registry_hash": rhash, "repo_type": res["repo_type"]["value"],
            "items": [it.to_dict() for it in res["items"]], "errors": res["errors"],
            "stats": {"by_kind": counts["by_kind"]},
        }
        gap_doc = gaps.build(ctx, res["items"], new_ledger, res["touches"],
                             res["repo_type"]["value"], head, version)
        blob = json.dumps(inventory, ensure_ascii=False)
        gblob = json.dumps(gap_doc, ensure_ascii=False)
        if any(s and (s in blob or s in gblob) for s in SecretFilter.secrets()):
            raise ExtractError("inventory/gaps would contain a registered secret")
        paths.atomic_write_json(out_dir / "inventory.json", inventory, sort_keys=True)
        paths.atomic_write_json(out_dir / "gaps.json", gap_doc, sort_keys=True)
        paths.atomic_write_json(out_dir / "ledger.json", new_ledger)
        meta = paths.read_json(out_dir / "meta.json", None) or meta
        meta["repo_type"] = res["repo_type"]
        meta["extract"] = {"phase_version": PHASE_VERSION, "version": version,
                           "items": counts["items"], "files_extracted": counts["files_extracted"],
                           "files_partial": counts["files_partial"],
                           "files_untouched": counts["files_untouched"],
                           "gaps": gap_doc["summary"]["total"]}
        paths.atomic_write_json(out_dir / "meta.json", meta)
    except Exception as e:
        msg = redact(f"{type(e).__name__}: {e}", SecretFilter.secrets())
        log.error("%s: extract failed: %s", repo, msg)
        store.set_phase(org.name, repo, "extract", status="failed", error=msg,
                        finished_at=paths.utcnow())
        return "failed"
    store.set_phase(org.name, repo, "extract", status="done", version=version, input_sha=head,
                    ledger_generated_at=ledger.get("generated_at"), extractor_versions=vers,
                    registry_hash=rhash, counts=counts, missing_extractors=missing,
                    gaps=gap_doc["summary"]["by_type"],
                    finished_at=paths.utcnow(), error=None, skip_reason=None)
    return "done"


def extract_all(org: OrgConfig, store: StateStore, repos: list[str] | None = None,
                force: bool = False, workers: int | None = None) -> dict:
    systems, _h, rbytes = external_systems.load_registry()
    all_repos = store.repos(org.name)
    candidates = repos if repos is not None else sorted(all_repos)
    todo, results = [], {}
    for n in candidates:
        r = all_repos.get(n) or {}
        ledger = (r.get("phases") or {}).get("ledger") or {}
        if ledger.get("status") == "skipped":
            if ((r.get("phases") or {}).get("extract") or {}).get("status") != "skipped":
                store.set_phase(org.name, n, "extract", status="skipped", version=PHASE_VERSION,
                                skip_reason=ledger.get("skip_reason") or "ledger-skipped",
                                finished_at=paths.utcnow())
            results[n] = "skipped"
            continue
        if StateStore.effective_from(r, "ledger", p1.PHASE_VERSION) != "done":
            results[n] = "no-ledger"
            continue
        ver, lga = status_inputs(org.name, n, rbytes)
        st = StateStore.effective_from(r, "extract", ver, ledger_generated_at=lga)
        if force or st in ("pending", "failed", "stale", "running", "skipped"):
            todo.append(n)
        else:
            results[n] = "fresh"
    with ThreadPoolExecutor(max_workers=workers or org.workers) as ex:
        futs = {ex.submit(extract_one, org, store, n, force, systems, rbytes): n for n in todo}
        for f in as_completed(futs):
            results[futs[f]] = f.result()
            log.info("extract %s: %s", futs[f], results[futs[f]])
    counts: dict[str, int] = {}
    for v in results.values():
        counts[v] = counts.get(v, 0) + 1
    return {"results": results, "counts": counts,
            "failed": sorted(n for n, v in results.items() if v == "failed")}
