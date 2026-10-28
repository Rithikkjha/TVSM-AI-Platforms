from __future__ import annotations

import os

import pytest

from conftest import git, make_work_repo
from repo_docs import gitops, paths, phase1_ledger as p1
from repo_docs.secrets import SecretFilter
from repo_docs.state import StateStore


@pytest.fixture
def cloned(root, org_cfg):
    """A 'clone' placed directly at repos/TEST-ORG/alpha with every file class."""
    dest = paths.clone_dir("TEST-ORG", "alpha")
    make_work_repo(dest, {
        "src/Api/Controllers/X.cs": "a\nb\nc",  # 3 lines, no trailing newline
        "src/Api/appsettings.json": "{}\n",
        "Dockerfile": "FROM x\n",
        "openapi.yaml": "openapi: 3\n",
        "README.md": "# r\n",
        "tests/test_a.py": "x\n",
        "src/Api/Api.csproj": "<Project/>\n",
        "node_modules/x/index.js": "x\n",
        "package-lock.json": "{}\n",
        "bin.dat2": b"ab\x00cd",
        "app.min.js": "x",
        "big.cs": "x" * 200,
        ".env": "SECRET=1\n",
        "empty.txt": "",
    })
    os.symlink("README.md", dest / "link.md")
    git("add", "link.md", cwd=dest)
    git("update-index", "--add", "--cacheinfo",
        "160000,1111111111111111111111111111111111111111,sub", cwd=dest)
    git("commit", "-q", "-m", "more", cwd=dest)
    org_cfg.max_file_bytes = 100
    store = StateStore()
    head = gitops.head_sha(dest)
    store.upsert_repo("TEST-ORG", "alpha", {"head_sha": head})
    store.set_phase("TEST-ORG", "alpha", "clone", status="done", version="0.1.0", output_sha=head)
    paths.atomic_write_json(paths.runs_dir("TEST-ORG", "alpha") / "meta.json", {"repo": "alpha"})
    return org_cfg, store, dest


def test_ledger_full_accounting(cloned):
    org, store, dest = cloned
    res = p1.ledger_all(org, store)
    assert res["results"]["alpha"] == "done"
    led = paths.read_json(paths.runs_dir("TEST-ORG", "alpha") / "ledger.json")
    meta = paths.read_json(paths.runs_dir("TEST-ORG", "alpha") / "meta.json")
    ls = gitops.ls_files(dest)
    assert len(led["files"]) == len(ls) == meta["ledger"]["git_ls_files_count"]
    assert meta["ledger"]["self_check"] == "pass"
    assert [f["path"] for f in led["files"]] == sorted(f["path"] for f in led["files"])
    by = {f["path"]: f for f in led["files"]}
    assert by["src/Api/Controllers/X.cs"]["lines"] == 3
    assert by["empty.txt"]["lines"] == 0
    expect = {
        "src/Api/Controllers/X.cs": "pending", "src/Api/appsettings.json": "pending",
        "Dockerfile": "pending", "openapi.yaml": "pending", "README.md": "pending",
        "tests/test_a.py": "pending", "src/Api/Api.csproj": "pending",
        "node_modules/x/index.js": "skipped:vendor", "package-lock.json": "skipped:lockfile",
        "bin.dat2": "skipped:binary", "app.min.js": "skipped:minified", "big.cs": "skipped:large",
        "link.md": "skipped:symlink", "sub": "skipped:submodule", ".env": "pending",
    }
    for p, st in expect.items():
        assert by[p]["status"] == st, p
    assert by["node_modules/x/index.js"]["lines"] is None
    assert meta["ledger"]["secret_risk_files"] == [".env"]
    assert sum(meta["ledger"]["by_class"].values()) == len(ls)
    assert sum(meta["ledger"]["by_status"].values()) == len(ls)
    ph = store.phase("TEST-ORG", "alpha", "ledger")
    assert ph["status"] == "done" and ph["input_sha"] == gitops.head_sha(dest)
    assert ph["counts"]["total"] == len(ls)


def test_ledger_resume_stale_force(cloned):
    org, store, dest = cloned
    p1.ledger_all(org, store)
    assert p1.ledger_all(org, store)["results"]["alpha"] == "fresh"
    assert p1.ledger_all(org, store, ["alpha"], force=True)["results"]["alpha"] == "done"
    (dest / "new.cs").write_text("x\n")
    git("add", "new.cs", cwd=dest)
    git("commit", "-q", "-m", "n", cwd=dest)
    store.upsert_repo("TEST-ORG", "alpha", {"head_sha": gitops.head_sha(dest)})
    assert store.effective_status("TEST-ORG", "alpha", "ledger", p1.PHASE_VERSION) == "stale"
    assert p1.ledger_all(org, store)["results"]["alpha"] == "done"
    led = paths.read_json(paths.runs_dir("TEST-ORG", "alpha") / "ledger.json")
    assert "new.cs" in {f["path"] for f in led["files"]}


def test_ledger_error_is_redacted(cloned, fake_token, monkeypatch, caplog):
    org, store, dest = cloned
    saved = list(SecretFilter._secrets)
    SecretFilter.register(fake_token)
    try:
        def boom(*a, **k):
            raise RuntimeError(f"boom {fake_token}")

        monkeypatch.setattr(p1, "build_ledger", boom)
        assert p1.ledger_one(org, store, "alpha") == "failed"
        err = store.phase("TEST-ORG", "alpha", "ledger")["error"]
        assert "***" in err and fake_token not in err
        assert fake_token not in caplog.text
    finally:
        SecretFilter._secrets[:] = saved


def test_ledger_head_mismatch_fails(cloned):
    org, store, dest = cloned
    store.upsert_repo("TEST-ORG", "alpha", {"head_sha": "0" * 40})
    res = p1.ledger_all(org, store)
    assert res["failed"] == ["alpha"]
    assert store.phase("TEST-ORG", "alpha", "ledger")["status"] == "failed"
