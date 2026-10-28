"""Master tracker state/state.json.

Every mutation runs inside ``transaction()``: process-level threading lock + cross-process
``fcntl.flock`` on state/state.lock, re-read file, mutate, atomic write (tmp + fsync + rename).
Re-reading inside the lock means racing processes never lose each other's updates.

Stored statuses: pending | running | done | failed | skipped.
``stale`` is DERIVED (never stored): a done phase whose input_sha != repo head_sha or whose
version != the current phase version (extract: also when ledger.json was regenerated after it).
"""

from __future__ import annotations

import copy
import fcntl
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from . import paths

SCHEMA_VERSION = 1
STATUSES = ("pending", "running", "done", "failed", "skipped")
EFFECTIVE_STATUSES = STATUSES + ("stale",)
PHASES = ("clone", "ledger", "extract", "llm_scan", "resolve", "generate", "verify", "review",
          "ingest")
MAX_ERROR = 2000

_thread_lock = threading.RLock()


def _empty() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "updated_at": None, "orgs": {}}


def new_phase() -> dict[str, Any]:
    return {
        "status": "pending",
        "version": None,
        "input_sha": None,
        "started_at": None,
        "finished_at": None,
        "attempts": 0,
        "error": None,
        "skip_reason": None,
    }


class StateStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else paths.state_path()
        self.lock_path = self.path.with_name(self.path.stem + ".lock")

    # ---- low level -------------------------------------------------------------------------
    def get(self) -> dict[str, Any]:
        """Snapshot read (no lock needed: writes are atomic renames)."""
        return paths.read_json(self.path, None) or _empty()

    @contextmanager
    def transaction(self) -> Iterator[dict[str, Any]]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _thread_lock:
            with open(self.lock_path, "a+") as lf:
                fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
                try:
                    data = self.get()
                    yield data
                    data["updated_at"] = paths.utcnow()
                    paths.atomic_write_json(self.path, data)
                finally:
                    fcntl.flock(lf.fileno(), fcntl.LOCK_UN)

    # ---- helpers ---------------------------------------------------------------------------
    @staticmethod
    def _org(data: dict, org: str) -> dict:
        return data["orgs"].setdefault(org, {"repos": {}})

    def update_org(self, org: str, fields: dict[str, Any]) -> None:
        with self.transaction() as d:
            self._org(d, org).update(copy.deepcopy(fields))

    def upsert_repo(self, org: str, name: str, fields: dict[str, Any]) -> None:
        with self.transaction() as d:
            repo = self._org(d, org)["repos"].setdefault(name, {"phases": {}})
            repo.update(copy.deepcopy(fields))

    def repo(self, org: str, name: str) -> dict[str, Any] | None:
        return self.get()["orgs"].get(org, {}).get("repos", {}).get(name)

    def repos(self, org: str) -> dict[str, dict[str, Any]]:
        return self.get()["orgs"].get(org, {}).get("repos", {})

    def set_phase(self, org: str, repo: str, phase: str, **fields: Any) -> None:
        if phase not in PHASES:
            raise ValueError(f"unknown phase {phase}")
        if "status" in fields and fields["status"] not in STATUSES:
            raise ValueError(f"invalid stored status {fields['status']}")
        if fields.get("error"):
            fields["error"] = str(fields["error"])[:MAX_ERROR]
        with self.transaction() as d:
            r = self._org(d, org)["repos"].setdefault(repo, {"phases": {}})
            ph = r.setdefault("phases", {}).setdefault(phase, new_phase())
            ph.update(fields)

    def phase(self, org: str, repo: str, phase: str) -> dict[str, Any]:
        r = self.repo(org, repo) or {}
        return r.get("phases", {}).get(phase) or new_phase()

    # ---- derived status --------------------------------------------------------------------
    @staticmethod
    def effective_from(repo: dict[str, Any], phase: str, current_version: str | None,
                       ledger_generated_at: str | None = None) -> str:
        """``ledger_generated_at`` (extract only): the current ledger.json ``generated_at``; a
        different value than the one recorded by the extract run means the ledger was rebuilt."""
        ph = (repo.get("phases") or {}).get(phase)
        if not ph:
            return "pending"
        st = ph.get("status", "pending")
        if st != "done":
            return st
        if current_version is not None and ph.get("version") != current_version:
            return "stale"
        if phase != "clone" and ph.get("input_sha") != repo.get("head_sha"):
            return "stale"
        if (phase == "extract" and ledger_generated_at is not None
                and ph.get("ledger_generated_at") != ledger_generated_at):
            return "stale"
        return "done"

    def effective_status(
        self, org: str, repo: str, phase: str, current_version: str | None = None
    ) -> str:
        r = self.repo(org, repo)
        return self.effective_from(r, phase, current_version) if r else "pending"

    def repos_needing(
        self, org: str, phase: str, current_version: str | None, force: bool = False
    ) -> list[str]:
        """Repos whose phase is pending/failed/stale/running (crash leftover); all non-skipped if force."""
        out = []
        for name, r in sorted(self.repos(org).items()):
            st = self.effective_from(r, phase, current_version)
            if st == "skipped":
                continue
            if force or st in ("pending", "failed", "stale", "running"):
                out.append(name)
        return out

    def summary(
        self, org: str | None = None, versions: dict[str, str] | None = None
    ) -> dict[str, dict[str, dict[str, int]]]:
        """{org: {phase: {effective_status: count}}} for phases that have any record."""
        versions = versions or {}
        data = self.get()
        out: dict[str, dict[str, dict[str, int]]] = {}
        for oname, o in data["orgs"].items():
            if org and oname != org:
                continue
            per: dict[str, dict[str, int]] = {}
            for r in o.get("repos", {}).values():
                for ph in PHASES:
                    if ph not in (r.get("phases") or {}) and ph not in versions:
                        continue
                    st = self.effective_from(r, ph, versions.get(ph))
                    per.setdefault(ph, {}).setdefault(st, 0)
                    per[ph][st] += 1
            out[oname] = per
        return out
