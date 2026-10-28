"""git subprocess wrappers. argv lists only (never a shell); output redacted.

Auth is passed through ``env`` (see secrets.git_auth_env), never through argv or URLs.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .secrets import redact


class GitError(RuntimeError):
    pass


def _env(extra: dict[str, str] | None) -> dict[str, str]:
    env = dict(os.environ)
    # never let ambient config inject other credentials/headers into our env-scoped config
    for k in list(env):
        if k.startswith("GIT_CONFIG_KEY_") or k.startswith("GIT_CONFIG_VALUE_"):
            env.pop(k)
    env.pop("GIT_CONFIG_COUNT", None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["LC_ALL"] = "C"
    if extra:
        env.update(extra)
    return env


def run_git(args: list[str], cwd: Path | None = None, env: dict[str, str] | None = None,
            timeout: int = 1800, secrets: list[str] | None = None) -> str:
    try:
        p = subprocess.run(["git", *args], cwd=cwd, env=_env(env), capture_output=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        raise GitError(f"git {args[0]} timed out after {timeout}s") from None
    if p.returncode != 0:
        msg = p.stderr.decode("utf-8", "replace").strip() or p.stdout.decode("utf-8", "replace")
        raise GitError(redact(f"git {args[0]} exit {p.returncode}: {msg}", secrets or []))
    return p.stdout.decode("utf-8", "surrogateescape")


def ls_remote_sha(url: str, branch: str, env: dict[str, str] | None = None,
                  secrets: list[str] | None = None) -> str | None:
    """SHA of refs/heads/<branch>; None if the remote has no refs at all (empty repo)."""
    out = run_git(["ls-remote", "--heads", url], env=env, secrets=secrets, timeout=300)
    refs = {}
    for line in out.splitlines():
        sha, _, ref = line.partition("\t")
        refs[ref.strip()] = sha.strip()
    if not refs:
        return None
    sha = refs.get(f"refs/heads/{branch}")
    if not sha:
        raise GitError(f"branch {branch!r} not found on remote")
    return sha


def shallow_clone(url: str, branch: str, dest: Path, env: dict[str, str] | None = None,
                  depth: int = 1, secrets: list[str] | None = None) -> None:
    partial = dest.with_name(dest.name + ".partial")
    if partial.exists():
        shutil.rmtree(partial)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        run_git(["clone", "--quiet", "--depth", str(depth), "--single-branch", "--branch", branch,
                 "--no-tags", url, str(partial)], env=env, secrets=secrets)
        if dest.exists():
            shutil.rmtree(dest)
        os.replace(partial, dest)
    finally:
        if partial.exists():
            shutil.rmtree(partial, ignore_errors=True)


def refresh(dest: Path, branch: str, env: dict[str, str] | None = None, depth: int = 1,
            secrets: list[str] | None = None) -> None:
    run_git(["fetch", "--quiet", "--depth", str(depth), "--no-tags", "origin", branch], cwd=dest,
            env=env, secrets=secrets)
    run_git(["reset", "--quiet", "--hard", "FETCH_HEAD"], cwd=dest)
    run_git(["clean", "-fdxq"], cwd=dest)


def head_sha(dest: Path) -> str:
    return run_git(["rev-parse", "HEAD"], cwd=dest).strip()


def is_clone(dest: Path) -> bool:
    return (dest / ".git").is_dir()


def ls_files(dest: Path) -> list[tuple[str, str]]:
    """[(mode, path)] for every tracked entry (``git ls-files -s -z``)."""
    out = run_git(["ls-files", "-s", "-z"], cwd=dest)
    res = []
    for rec in out.split("\0"):
        if not rec:
            continue
        meta, _, path = rec.partition("\t")
        res.append((meta.split(" ", 1)[0], path))
    return res


def assert_no_credentials(dest: Path, secrets: list[str] | None = None) -> None:
    cfg = (dest / ".git" / "config").read_text(encoding="utf-8", errors="replace")
    if "extraheader" in cfg.lower():
        raise GitError("credential header persisted in .git/config")
    for s in secrets or []:
        if s and s in cfg:
            raise GitError("token persisted in .git/config")
    url = run_git(["remote", "get-url", "origin"], cwd=dest).strip()
    if "@" in url.split("://", 1)[-1].split("/", 1)[0]:
        raise GitError("remote URL contains credentials")
