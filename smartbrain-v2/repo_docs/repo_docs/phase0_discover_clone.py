"""Phase 0: discover org repos via the GitHub API, shallow clone/refresh, detect stacks."""

from __future__ import annotations

import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from . import gitops, naming, paths
from .config import OrgConfig
from .github_client import GitHubClient
from .secrets import git_auth_env, redact, secret_forms
from .stack_detect import detect_stacks, stack_ids
from .state import StateStore

PHASE_VERSION = "0.1.0"
log = logging.getLogger(__name__)
STACK_READ_LIMIT = 512_000


def discover(org: OrgConfig, store: StateStore, client: GitHubClient) -> dict:
    """List all org repos, write runs/<org>/repos.json, register in-scope repos in state."""
    api_repos = client.list_org_repos(org.name)
    by_name = {r["name"]: r for r in api_repos}
    missing = [n for n in (org.allowlist or []) if n not in by_name]
    for n in missing:
        log.error("allowlist repo %r not found in GitHub org %s", n, org.name)

    selected = [
        r for r in api_repos
        if org.matches(r["name"]) and (org.include_archived or not r["archived"])
    ]
    ids, collided = naming.assign_service_ids(
        [r["name"] for r in selected], org.service_id_overrides
    )
    for n in sorted(collided):
        log.warning("service_id collision: %s -> %s", n, ids[n])

    now = paths.utcnow()
    snapshot = []
    for r in sorted(api_repos, key=lambda x: x["name"].lower()):
        snapshot.append({
            **r,
            "self": r["name"] in org.self_repos,
            "allowlisted": org.in_allowlist(r["name"]),
            "registered": r["name"] in ids,
            "service_id": ids.get(r["name"]),
        })
    paths.atomic_write_json(paths.runs_dir(org.name) / "repos.json", {
        "schema_version": 1, "org": org.name, "fetched_at": now, "count": len(api_repos),
        "allowlist_missing": missing, "repos": snapshot,
    })

    with store.transaction() as d:
        o = d["orgs"].setdefault(org.name, {"repos": {}})
        o.update({
            "discovered_at": now, "api_repo_count": len(api_repos), "repo_count": len(selected),
            "allowlist_missing": missing, "service_id_collisions": sorted(collided),
        })
        for r in selected:
            rec = o["repos"].setdefault(r["name"], {"phases": {}})
            rec.update({
                "service_id": ids[r["name"]],
                "service_id_collision": r["name"] in collided,
                "default_branch": r["default_branch"], "language": r["language"],
                "size_kb": r["size_kb"], "archived": r["archived"], "empty": r["empty"],
                "self": r["name"] in org.self_repos, "pushed_at": r["pushed_at"],
                "html_url": r["html_url"],
            })
            rec.setdefault("remote_sha", None)
            rec.setdefault("head_sha", None)
            rec.setdefault("stacks", [])
            ph = rec.setdefault("phases", {})
            if r["empty"] and (ph.get("clone") or {}).get("status") != "done":
                ph["clone"] = _phase_record("skipped", skip_reason="empty", finished_at=now)
    return {
        "api_repo_count": len(api_repos), "registered": len(selected),
        "empty": sum(1 for r in selected if r["empty"]),
        "allowlist_missing": missing, "collisions": sorted(collided),
    }


def _phase_record(status: str, **kw) -> dict:
    rec = {"status": status, "version": PHASE_VERSION, "input_sha": None, "output_sha": None,
           "started_at": None, "finished_at": None, "attempts": 0, "error": None,
           "skip_reason": None}
    rec.update(kw)
    return rec


def _with_retries(fn: Callable, retries: int, sleep: Callable[[float], None], what: str):
    attempt = 0
    while True:
        try:
            return fn()
        except gitops.GitError as e:
            attempt += 1
            if attempt > retries:
                raise
            wait = 2 ** attempt + random.uniform(0, 1)
            log.warning("%s failed (%s); retry %d/%d in %.0fs", what, e, attempt, retries, wait)
            sleep(wait)


def _read_for_detect(dest: Path) -> Callable[[str], str | None]:
    def read(rel: str) -> str | None:
        p = dest / rel
        try:
            if p.is_symlink() or not p.is_file() or p.stat().st_size > STACK_READ_LIMIT:
                return None
            return p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
    return read


def write_meta(org: OrgConfig, repo: str, rec: dict, head: str, hits, cloned_at: str) -> None:
    mpath = paths.runs_dir(org.name, repo) / "meta.json"
    old = paths.read_json(mpath, {}) or {}
    meta = {
        "schema_version": 1, "org": org.name, "repo": repo,
        "service_id": rec.get("service_id"),
        "service_id_collision": bool(rec.get("service_id_collision")),
        "self": bool(rec.get("self")), "default_branch": rec.get("default_branch"),
        "head_sha": head, "html_url": rec.get("html_url"), "language": rec.get("language"),
        "archived": bool(rec.get("archived")),
        "clone": {"path": f"repos/{org.name}/{repo}", "depth": org.clone_depth,
                  "cloned_at": cloned_at, "phase_version": PHASE_VERSION},
        "stacks": [h.to_dict() for h in hits],
        "stack_ids": stack_ids(hits),
    }
    if old.get("head_sha") == head and "ledger" in old:
        meta["ledger"] = old["ledger"]
    paths.atomic_write_json(mpath, meta)


def clone_one(org: OrgConfig, store: StateStore, repo: str, token: str, force: bool = False,
              sleep: Callable[[float], None] = time.sleep) -> str:
    """Clone/refresh one repo. Returns outcome: cloned|refreshed|unchanged|skipped|failed."""
    secrets = secret_forms(token)
    rec = store.repo(org.name, repo) or {}
    cur = (rec.get("phases") or {}).get("clone") or {}
    dest = paths.clone_dir(org.name, repo)
    url = org.clone_url(repo)
    env = git_auth_env(token, org.git_base)
    branch = rec.get("default_branch") or "main"
    started = paths.utcnow()
    try:
        remote = _with_retries(lambda: gitops.ls_remote_sha(url, branch, env, secrets),
                               org.max_retries, sleep, f"{repo}: ls-remote")
        if remote is None:
            store.set_phase(org.name, repo, "clone", status="skipped", skip_reason="empty",
                            version=PHASE_VERSION, finished_at=paths.utcnow(), error=None)
            store.upsert_repo(org.name, repo, {"empty": True, "remote_sha": None})
            return "skipped"
        if rec.get("empty"):
            # the API's size=0 is only a hint; ls-remote is authoritative
            log.warning("%s: GitHub API reported size 0 but remote has refs; cloning", repo)
            store.upsert_repo(org.name, repo, {"empty": False})
        if (not force and cur.get("status") == "done" and cur.get("version") == PHASE_VERSION
                and rec.get("head_sha") == remote and gitops.is_clone(dest)
                and gitops.head_sha(dest) == remote
                and (paths.runs_dir(org.name, repo) / "meta.json").is_file()):
            store.upsert_repo(org.name, repo, {"remote_sha": remote})
            return "unchanged"
        store.set_phase(org.name, repo, "clone", status="running", started_at=started,
                        attempts=int(cur.get("attempts") or 0) + 1, error=None)
        existed = gitops.is_clone(dest)
        if existed:
            try:
                _with_retries(lambda: gitops.refresh(dest, branch, env, org.clone_depth, secrets),
                              org.max_retries, sleep, f"{repo}: refresh")
            except gitops.GitError:
                existed = False  # broken clone -> fresh clone
        if not existed:
            _with_retries(
                lambda: gitops.shallow_clone(url, branch, dest, env, org.clone_depth, secrets),
                org.max_retries, sleep, f"{repo}: clone")
        head = gitops.head_sha(dest)
        gitops.assert_no_credentials(dest, secrets)
        files = [p for mode, p in gitops.ls_files(dest) if mode != "160000"]
        hits = detect_stacks(files, _read_for_detect(dest))
        now = paths.utcnow()
        write_meta(org, repo, rec, head, hits, now)
        store.upsert_repo(org.name, repo, {"remote_sha": remote, "head_sha": head,
                                           "stacks": stack_ids(hits)})
        store.set_phase(org.name, repo, "clone", status="done", version=PHASE_VERSION,
                        output_sha=head, finished_at=now, error=None, skip_reason=None)
        return "refreshed" if existed else "cloned"
    except Exception as e:  # per-repo failure is never fatal
        msg = redact(f"{type(e).__name__}: {e}", secrets)
        log.error("%s: clone failed: %s", repo, msg)
        store.set_phase(org.name, repo, "clone", status="failed", error=msg,
                        finished_at=paths.utcnow())
        return "failed"


def clone_all(org: OrgConfig, store: StateStore, token: str, repos: list[str] | None = None,
              force: bool = False, workers: int | None = None,
              sleep: Callable[[float], None] = time.sleep) -> dict:
    names = repos if repos is not None else sorted(store.repos(org.name))
    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=workers or org.workers) as ex:
        futs = {ex.submit(clone_one, org, store, n, token, force, sleep): n for n in names}
        for f in as_completed(futs):
            n = futs[f]
            results[n] = f.result()
            log.info("clone %s: %s", n, results[n])
    counts: dict[str, int] = {}
    for v in results.values():
        counts[v] = counts.get(v, 0) + 1
    return {"results": results, "counts": counts,
            "failed": sorted(n for n, v in results.items() if v == "failed")}
