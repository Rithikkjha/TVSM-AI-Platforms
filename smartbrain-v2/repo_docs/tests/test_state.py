from __future__ import annotations

import json
import multiprocessing as mp
import os
import threading

import pytest

from repo_docs.state import StateStore


def _worker(path, org, n):
    s = StateStore(path)
    for i in range(n):
        with s.transaction() as d:
            r = d["orgs"].setdefault(org, {"repos": {}})["repos"].setdefault("counter", {"n": 0})
            r["n"] = r.get("n", 0) + 1


def test_atomic_write_no_tmp(tmp_path):
    s = StateStore(tmp_path / "state" / "state.json")
    s.upsert_repo("O", "r", {"head_sha": "a"})
    files = os.listdir(tmp_path / "state")
    assert not [f for f in files if ".tmp" in f]
    json.loads((tmp_path / "state" / "state.json").read_text())


def test_crash_during_replace_keeps_previous(tmp_path, monkeypatch):
    s = StateStore(tmp_path / "state.json")
    s.upsert_repo("O", "r", {"head_sha": "a"})
    def boom(*a, **k):
        raise OSError("crash")
    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        s.upsert_repo("O", "r", {"head_sha": "b"})
    monkeypatch.undo()
    assert s.repo("O", "r")["head_sha"] == "a"
    assert not [f for f in os.listdir(tmp_path) if ".tmp" in f]


def test_concurrent_processes_and_threads(tmp_path):
    """2 processes x 50 + 8 threads x 100 increments -> 900, no lost update."""
    path = tmp_path / "state.json"
    ctx = mp.get_context("spawn")
    procs = [ctx.Process(target=_worker, args=(str(path), "O", 50)) for _ in range(2)]
    threads = [threading.Thread(target=_worker, args=(path, "O", 100)) for _ in range(8)]
    for p in procs:
        p.start()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    for p in procs:
        p.join()
        assert p.exitcode == 0
    assert StateStore(path).repo("O", "counter")["n"] == 900


def test_effective_status_and_needing(tmp_path):
    s = StateStore(tmp_path / "state.json")
    for name in ("fresh", "moved", "oldver", "failed", "crashed", "new", "empty"):
        s.upsert_repo("O", name, {"head_sha": "h1"})
    for name in ("fresh", "moved", "oldver"):
        s.set_phase("O", name, "ledger", status="done", version="1", input_sha="h1")
    s.upsert_repo("O", "moved", {"head_sha": "h2"})
    s.set_phase("O", "oldver", "ledger", version="0")
    s.set_phase("O", "failed", "ledger", status="failed", error="x" * 5000)
    s.set_phase("O", "crashed", "ledger", status="running")
    s.set_phase("O", "empty", "ledger", status="skipped", skip_reason="empty")
    assert s.effective_status("O", "fresh", "ledger", "1") == "done"
    assert s.effective_status("O", "moved", "ledger", "1") == "stale"
    assert s.effective_status("O", "oldver", "ledger", "1") == "stale"
    assert s.effective_status("O", "new", "ledger", "1") == "pending"
    assert len(s.phase("O", "failed", "ledger")["error"]) == 2000
    need = s.repos_needing("O", "ledger", "1")
    assert need == ["crashed", "failed", "moved", "new", "oldver"]
    assert "fresh" in s.repos_needing("O", "ledger", "1", force=True)
    assert "empty" not in s.repos_needing("O", "ledger", "1", force=True)
    summ = s.summary("O", {"ledger": "1"})["O"]["ledger"]
    assert summ == {"done": 1, "stale": 2, "failed": 1, "running": 1, "pending": 1, "skipped": 1}
    with pytest.raises(ValueError):
        s.set_phase("O", "fresh", "ledger", status="stale")
