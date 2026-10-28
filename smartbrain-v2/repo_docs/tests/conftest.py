from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import pytest

from repo_docs import paths
from repo_docs.config import load_config

FAKE_TOKEN = "ghp_FAKEtoken1234567890abcdef"


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True).stdout


def make_work_repo(path: Path, files: dict[str, bytes | str]) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git("init", "-q", "-b", "main", cwd=path)
    git("config", "user.email", "t@example.com", cwd=path)
    git("config", "user.name", "t", cwd=path)
    for rel, content in files.items():
        p = path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            content = content.encode()
        p.write_bytes(content)
    git("add", "-A", cwd=path)
    git("commit", "-q", "-m", "init", cwd=path)
    return path


def make_bare_remote(base: Path, org: str, name: str, files: dict | None) -> Path:
    """Bare repo at base/org/name.git; files=None -> empty repo (no commits)."""
    bare = base / org / f"{name}.git"
    bare.parent.mkdir(parents=True, exist_ok=True)
    git("init", "-q", "--bare", "-b", "main", str(bare))
    if files is not None:
        work = base / "_work" / org / name
        make_work_repo(work, files)
        git("push", "-q", str(bare), "main", cwd=work)
    return bare


def push_commit(base: Path, org: str, name: str, rel: str, content: str) -> None:
    work = base / "_work" / org / name
    (work / rel).parent.mkdir(parents=True, exist_ok=True)
    (work / rel).write_text(content)
    git("add", "-A", cwd=work)
    git("commit", "-q", "-m", "more", cwd=work)
    git("push", "-q", str(base / org / f"{name}.git"), "main", cwd=work)


@pytest.fixture(autouse=True)
def _restore_root_logging():
    """cli.main() installs root handlers bound to the (captured) stderr; remove them after."""
    root_logger = logging.getLogger()
    before = list(root_logger.handlers)
    yield
    for h in list(root_logger.handlers):
        if h not in before:
            root_logger.removeHandler(h)
            h.close()


@pytest.fixture
def fake_token() -> str:
    return FAKE_TOKEN


@pytest.fixture
def root(tmp_path, monkeypatch):
    """Isolated repo_docs ROOT with a config for org TEST-ORG and a tmp token file."""
    r = tmp_path / "root"
    (r / "config" / "repos").mkdir(parents=True)
    (tmp_path / "secret.env").write_text(f"# comment\nOTHER=1\nGITHUB_TOKEN={FAKE_TOKEN}\n")
    remotes = tmp_path / "remotes"
    remotes.mkdir()
    (r / "config" / "orgs.yaml").write_text(f"""
schema_version: 1
defaults: {{workers: 3, max_retries: 0, max_file_bytes: 1000000, clone_depth: 1}}
orgs:
  - name: TEST-ORG
    token_env_file: {tmp_path / 'secret.env'}
    token_key: GITHUB_TOKEN
    git_base: file://{remotes}
    allowlist: config/repos/TEST-ORG.txt
    self_repos: [tvsm-brain]
""")
    (r / "config" / "repos" / "TEST-ORG.txt").write_text("alpha\nbeta  # comment\nempty-one\n")
    old = paths.root()
    paths.set_root(r)
    yield r
    paths.set_root(old)


@pytest.fixture
def remotes(root) -> Path:
    return root.parent / "remotes"


@pytest.fixture
def org_cfg(root):
    return load_config().org("TEST-ORG")
