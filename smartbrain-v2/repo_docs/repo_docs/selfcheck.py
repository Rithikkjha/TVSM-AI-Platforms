"""Secret-leak scan: reports which files contain the token (raw or base64 header form).

Never prints the token or any matched content — only paths and counts.
"""

from __future__ import annotations

from pathlib import Path

from . import paths
from .secrets import secret_forms

SKIP_DIRS = {".venv", "repos", "__pycache__", ".pytest_cache", ".git"}


def _iter_files(root: Path):
    if root.is_file():
        yield root
        return
    if not root.is_dir():
        return
    for p in root.rglob("*"):
        if p.is_file() and not (set(p.relative_to(root).parts[:-1]) & SKIP_DIRS):
            yield p


def scan_for_secret(token: str, roots: list[Path] | None = None) -> list[Path]:
    """Scan repo_docs (excluding .venv and clone worktrees) + every clone's .git/config."""
    needles = [s.encode() for s in secret_forms(token)]
    if not needles:
        return []
    base = paths.root()
    roots = roots if roots is not None else [base]
    targets: list[Path] = []
    for r in roots:
        targets.extend(_iter_files(r))
    repos = paths.repos_root()
    if repos.is_dir():
        targets.extend(sorted(repos.glob("*/*/.git/config")))
    hits = []
    for p in targets:
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if any(n in data for n in needles):
            hits.append(p)
    return hits
