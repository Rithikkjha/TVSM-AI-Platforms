"""Filesystem layout of the repo_docs subsystem + atomic JSON helpers.

All paths are resolved from ROOT (the repo_docs/ directory), never from the cwd.
Tests may redirect everything with ``set_root(tmp_path)``.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
_root: Path = Path(os.environ.get("REPO_DOCS_ROOT", DEFAULT_ROOT)).resolve()


def set_root(path: Path | str) -> None:
    global _root
    _root = Path(path).resolve()


def root() -> Path:
    return _root


def config_path() -> Path:
    return _root / "config" / "orgs.yaml"


def state_path() -> Path:
    return _root / "state" / "state.json"


def runs_dir(org: str, repo: str | None = None) -> Path:
    base = _root / "runs" / org
    return base / repo if repo else base


def repos_root() -> Path:
    return _root / "repos"


def clone_dir(org: str, repo: str) -> Path:
    return _root / "repos" / org / repo


def logs_dir(org: str) -> Path:
    return _root / "logs" / org


def output_dir(org: str, service_id: str) -> Path:
    """Planned (phase 5) destination of generated docs."""
    return _root / "output" / org / service_id


def resolve(p: str | Path) -> Path:
    """Resolve a config-supplied path relative to ROOT (absolute paths pass through)."""
    p = Path(p).expanduser()
    return p if p.is_absolute() else (_root / p).resolve()


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def registry_dir() -> Path:
    return _root / "registry"


def external_systems_path() -> Path:
    return registry_dir() / "external_systems.yaml"


def atomic_write_json(path: Path, obj: Any, sort_keys: bool = False) -> None:
    """Write JSON via temp file + fsync + os.replace (readers never see a partial file).
    ``sort_keys=True`` is used for deterministic phase-2 outputs (inventory.json)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}.{threading.get_ident()}")
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, sort_keys=sort_keys, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def read_json(path: Path, default: Any = None) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default
