"""Fixture helpers for phase-2 tests: a real git repo at paths.clone_dir with clone + ledger done."""
from __future__ import annotations

from conftest import make_work_repo
from repo_docs import gitops, paths, phase0_discover_clone as p0, phase1_ledger as p1
from repo_docs.stack_detect import detect_stacks


def make_ledgered_repo(root, org_cfg, store, name: str, files: dict) -> str:
    """Create repos/<org>/<name> as a git repo, mark clone done, write meta, build the ledger.
    Returns head sha."""
    dest = paths.clone_dir(org_cfg.name, name)
    make_work_repo(dest, files)
    head = gitops.head_sha(dest)
    store.upsert_repo(org_cfg.name, name, {"head_sha": head, "remote_sha": head,
                                           "service_id": name.lower(), "default_branch": "main"})
    store.set_phase(org_cfg.name, name, "clone", status="done", version=p0.PHASE_VERSION,
                    output_sha=head, finished_at=paths.utcnow())
    tracked = [p for _, p in gitops.ls_files(dest)]
    hits = detect_stacks(tracked, p0._read_for_detect(dest))
    p0.write_meta(org_cfg, name, store.repo(org_cfg.name, name), head, hits, paths.utcnow())
    assert p1.ledger_one(org_cfg, store, name) == "done"
    return head
