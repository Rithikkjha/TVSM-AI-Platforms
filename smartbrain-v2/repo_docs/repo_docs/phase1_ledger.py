"""Phase 1: file ledger. One entry per `git ls-files` entry, classified, with a count self-check."""

from __future__ import annotations

import fnmatch
import logging
import posixpath
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import gitops, paths
from .classify import classify, status_for
from .config import OrgConfig
from .secrets import SecretFilter, redact
from .state import StateStore

PHASE_VERSION = "0.1.0"
HEAD_BYTES = 8192
log = logging.getLogger(__name__)
SECRET_RISK_GLOBS = (".env", ".env.*", "*.env", "*.pfx", "*.p12", "*.jks", "*.keystore",
                     "*.pem", "*.key", "secrets*.json", "credentials*.json")
SECRET_RISK_SAFE = (".env.example", ".env.sample", ".env.template", ".env.dist")


class LedgerError(RuntimeError):
    pass


def _count_lines(fp) -> int:
    n = 0
    last = b""
    while True:
        chunk = fp.read(1 << 20)
        if not chunk:
            break
        n += chunk.count(b"\n")
        last = chunk[-1:]
    if last and last != b"\n":
        n += 1
    return n


def ledger_entry(dest, mode: str, path: str, max_file_bytes: int) -> dict:
    full = dest / path
    size: int | None = None
    head = b""
    missing = False
    if mode != "160000":
        try:
            st = full.lstat()
            size = st.st_size
            if mode != "120000":
                with open(full, "rb") as fh:
                    head = fh.read(HEAD_BYTES)
        except FileNotFoundError:
            missing = True
    if missing:
        cls, lang = "other", "unknown"
        return {"path": path, "class": cls, "language": lang, "size": None, "lines": None,
                "status": "failed:missing"}
    cls, lang = classify(path, mode, size, head, max_file_bytes)
    status = status_for(cls)
    lines = None
    if status == "pending" and mode not in ("160000", "120000"):
        with open(full, "rb") as fh:
            lines = _count_lines(fh)
    return {"path": path, "class": cls, "language": lang, "size": size, "lines": lines,
            "status": status}


def _secret_risk(path: str) -> bool:
    name = posixpath.basename(path)
    if name in SECRET_RISK_SAFE:
        return False
    return any(fnmatch.fnmatchcase(name, g) for g in SECRET_RISK_GLOBS)


def build_ledger(org: OrgConfig, store: StateStore, repo: str) -> dict:
    rec = store.repo(org.name, repo) or {}
    clone = (rec.get("phases") or {}).get("clone") or {}
    if clone.get("status") != "done":
        raise LedgerError(f"clone not done for {repo}")
    dest = paths.clone_dir(org.name, repo)
    head = gitops.head_sha(dest)
    if head != rec.get("head_sha"):
        raise LedgerError(f"clone HEAD {head[:12]} != state head_sha; re-run clone")
    entries = gitops.ls_files(dest)
    files = sorted((ledger_entry(dest, m, p, org.max_file_bytes) for m, p in entries),
                   key=lambda f: f["path"])
    ls_paths = {p for _, p in entries}
    led_paths = {f["path"] for f in files}
    ok = len(files) == len(entries) and ls_paths == led_paths
    by_class: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_lang: dict[str, int] = {}
    for f in files:
        by_class[f["class"]] = by_class.get(f["class"], 0) + 1
        by_status[f["status"]] = by_status.get(f["status"], 0) + 1
        by_lang[f["language"]] = by_lang.get(f["language"], 0) + 1
    if sum(by_class.values()) != len(files) or sum(by_status.values()) != len(files):
        ok = False
    now = paths.utcnow()
    out_dir = paths.runs_dir(org.name, repo)
    paths.atomic_write_json(out_dir / "ledger.json", {
        "schema_version": 1, "org": org.name, "repo": repo, "head_sha": head,
        "phase_version": PHASE_VERSION, "generated_at": now,
        "max_file_bytes": org.max_file_bytes, "files": files,
    })
    meta_path = out_dir / "meta.json"
    meta = paths.read_json(meta_path, {}) or {}
    meta["ledger"] = {
        "phase_version": PHASE_VERSION, "generated_at": now,
        "git_ls_files_count": len(entries), "ledger_count": len(files),
        "self_check": "pass" if ok else "fail",
        "by_class": dict(sorted(by_class.items())), "by_status": dict(sorted(by_status.items())),
        "by_language": dict(sorted(by_lang.items(), key=lambda kv: (-kv[1], kv[0]))),
        "secret_risk_files": sorted(f["path"] for f in files if _secret_risk(f["path"])),
    }
    paths.atomic_write_json(meta_path, meta)
    counts = {
        "total": len(files),
        "pending": by_status.get("pending", 0),
        "skipped": sum(v for k, v in by_status.items() if k.startswith("skipped:")),
        "failed": sum(v for k, v in by_status.items() if k.startswith("failed:")),
    }
    if not ok:
        raise LedgerError(f"self-check failed: ls-files={len(entries)} ledger={len(files)}")
    return {"head_sha": head, "counts": counts, "finished_at": now}


def ledger_one(org: OrgConfig, store: StateStore, repo: str) -> str:
    cur = store.phase(org.name, repo, "ledger")
    store.set_phase(org.name, repo, "ledger", status="running", started_at=paths.utcnow(),
                    attempts=int(cur.get("attempts") or 0) + 1, error=None)
    try:
        res = build_ledger(org, store, repo)
    except Exception as e:
        msg = redact(f"{type(e).__name__}: {e}", SecretFilter.secrets())
        log.error("%s: ledger failed: %s", repo, msg)
        store.set_phase(org.name, repo, "ledger", status="failed",
                        error=msg, finished_at=paths.utcnow())
        return "failed"
    store.set_phase(org.name, repo, "ledger", status="done", version=PHASE_VERSION,
                    input_sha=res["head_sha"], counts=res["counts"],
                    finished_at=res["finished_at"], error=None, skip_reason=None)
    return "done"


def ledger_all(org: OrgConfig, store: StateStore, repos: list[str] | None = None,
               force: bool = False, workers: int | None = None) -> dict:
    all_repos = store.repos(org.name)
    candidates = repos if repos is not None else sorted(all_repos)
    todo, results = [], {}
    for n in candidates:
        r = all_repos.get(n) or {}
        clone = (r.get("phases") or {}).get("clone") or {}
        if clone.get("status") == "skipped":
            # nothing to ledger (e.g. empty repo): mirror the clone skip so status is explicit
            if ((r.get("phases") or {}).get("ledger") or {}).get("status") != "skipped":
                store.set_phase(org.name, n, "ledger", status="skipped", version=PHASE_VERSION,
                                skip_reason=clone.get("skip_reason") or "clone-skipped",
                                finished_at=paths.utcnow())
            results[n] = "skipped"
            continue
        if clone.get("status") != "done":
            results[n] = "no-clone"
            continue
        st = StateStore.effective_from(r, "ledger", PHASE_VERSION)
        # "skipped" here means the repo was empty earlier but now has a clone -> build it
        if force or st in ("pending", "failed", "stale", "running", "skipped"):
            todo.append(n)
        else:
            results[n] = "fresh"
    with ThreadPoolExecutor(max_workers=workers or org.workers) as ex:
        futs = {ex.submit(ledger_one, org, store, n): n for n in todo}
        for f in as_completed(futs):
            results[futs[f]] = f.result()
            log.info("ledger %s: %s", futs[f], results[futs[f]])
    counts: dict[str, int] = {}
    for v in results.values():
        counts[v] = counts.get(v, 0) + 1
    return {"results": results, "counts": counts,
            "failed": sorted(n for n, v in results.items() if v == "failed")}
