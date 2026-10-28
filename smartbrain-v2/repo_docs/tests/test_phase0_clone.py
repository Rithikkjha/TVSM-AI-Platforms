from __future__ import annotations

import json
import logging
import subprocess
import urllib.error

import pytest

from conftest import git, make_bare_remote, make_work_repo, push_commit
from repo_docs import gitops, paths, phase0_discover_clone as p0, phase1_ledger as p1
from repo_docs.github_client import GitHubClient
from repo_docs.secrets import basic_auth_b64
from repo_docs.selfcheck import scan_for_secret
from repo_docs.state import StateStore


def api_repo(name, size=10, lang="C#"):
    return {"name": name, "full_name": f"TEST-ORG/{name}", "default_branch": "main",
            "language": lang, "size": size, "archived": False, "pushed_at": "2025-01-01T00:00:00Z",
            "html_url": f"https://github.com/TEST-ORG/{name}"}


class FakeClient:
    def __init__(self, repos):
        self.repos = repos

    def list_org_repos(self, org):
        from repo_docs.github_client import normalize_repo
        return [normalize_repo(r) for r in self.repos]


@pytest.fixture
def setup(root, remotes, org_cfg):
    make_bare_remote(remotes, "TEST-ORG", "alpha", {
        "Api/Api.csproj": "<Project/>", "Api/Controllers/X.cs": "class X {}\n",
        "README.md": "# alpha\n"})
    make_bare_remote(remotes, "TEST-ORG", "beta", {
        "package.json": json.dumps({"dependencies": {"express": "4"}}), "index.js": "x\n"})
    make_bare_remote(remotes, "TEST-ORG", "empty-one", None)
    store = StateStore()
    client = FakeClient([api_repo("alpha"), api_repo("beta", lang="JavaScript"),
                         api_repo("empty-one", size=0), api_repo("gamma")])
    return org_cfg, store, client


def nosleep(_):
    pass


def test_discover_allowlist_and_empty(setup):
    org, store, client = setup
    res = p0.discover(org, store, client)
    assert res["api_repo_count"] == 4 and res["registered"] == 3
    assert res["allowlist_missing"] == []
    snap = paths.read_json(paths.runs_dir("TEST-ORG") / "repos.json")
    assert snap["count"] == 4
    assert {r["name"]: r["allowlisted"] for r in snap["repos"]}["gamma"] is False
    assert set(store.repos("TEST-ORG")) == {"alpha", "beta", "empty-one"}
    assert store.phase("TEST-ORG", "empty-one", "clone")["status"] == "skipped"
    assert store.phase("TEST-ORG", "empty-one", "clone")["skip_reason"] == "empty"


def test_discover_missing_allowlist_name(setup, caplog):
    org, store, client = setup
    org.allowlist = org.allowlist + ["ghost"]
    res = p0.discover(org, store, client)
    assert res["allowlist_missing"] == ["ghost"]
    assert store.get()["orgs"]["TEST-ORG"]["allowlist_missing"] == ["ghost"]
    assert "ghost" in caplog.text


def test_clone_rerun_refresh_and_stale(setup, remotes, fake_token, monkeypatch):
    org, store, client = setup
    p0.discover(org, store, client)
    res = p0.clone_all(org, store, fake_token, sleep=nosleep)
    assert res["counts"] == {"cloned": 2, "skipped": 1}
    rec = store.repo("TEST-ORG", "alpha")
    dest = paths.clone_dir("TEST-ORG", "alpha")
    assert rec["head_sha"] == gitops.head_sha(dest)
    assert rec["phases"]["clone"]["status"] == "done"
    meta = paths.read_json(paths.runs_dir("TEST-ORG", "alpha") / "meta.json")
    assert meta["stack_ids"] == ["dotnet"] and meta["head_sha"] == rec["head_sha"]
    assert store.repo("TEST-ORG", "beta")["stacks"] == ["express", "node"]
    assert not dest.with_name("alpha.partial").exists()

    calls = []
    real = gitops.shallow_clone
    monkeypatch.setattr(gitops, "shallow_clone", lambda *a, **k: calls.append(a) or real(*a, **k))
    res = p0.clone_all(org, store, fake_token, sleep=nosleep)
    assert res["counts"] == {"unchanged": 2, "skipped": 1} and calls == []

    p1.ledger_all(org, store)
    assert store.effective_status("TEST-ORG", "alpha", "ledger", p1.PHASE_VERSION) == "done"
    push_commit(remotes, "TEST-ORG", "alpha", "Api/Controllers/Y.cs", "class Y {}\n")
    res = p0.clone_all(org, store, fake_token, sleep=nosleep)
    assert res["results"]["alpha"] == "refreshed" and calls == []
    assert store.repo("TEST-ORG", "alpha")["head_sha"] == gitops.head_sha(dest)
    assert (dest / "Api/Controllers/Y.cs").exists()
    assert store.effective_status("TEST-ORG", "alpha", "ledger", p1.PHASE_VERSION) == "stale"


def test_empty_repo_ledger_skipped_then_built(setup, remotes, fake_token):
    """Empty repo -> ledger skipped(empty); after it gets commits, clone + ledger run."""
    org, store, client = setup
    p0.discover(org, store, client)
    p0.clone_all(org, store, fake_token, sleep=nosleep)
    assert p1.ledger_all(org, store)["results"]["empty-one"] == "skipped"
    ph = store.phase("TEST-ORG", "empty-one", "ledger")
    assert ph["status"] == "skipped" and ph["skip_reason"] == "empty"
    work = make_work_repo(remotes / "_work" / "TEST-ORG" / "empty-one", {"a.py": "x\n"})
    git("push", "-q", str(remotes / "TEST-ORG" / "empty-one.git"), "main", cwd=work)
    store.set_phase("TEST-ORG", "empty-one", "clone", status="pending")
    store.upsert_repo("TEST-ORG", "empty-one", {"empty": False})
    assert p0.clone_all(org, store, fake_token, ["empty-one"], sleep=nosleep)["results"] == {
        "empty-one": "cloned"}
    assert p1.ledger_all(org, store, ["empty-one"])["results"]["empty-one"] == "done"


def test_api_empty_but_remote_has_refs_is_cloned(setup, fake_token, caplog):
    """API size=0 is only a hint: ls-remote finds refs -> clone, empty flag cleared, WARNING."""
    org, store, client = setup
    client.repos[0] = api_repo("alpha", size=0)
    p0.discover(org, store, client)
    assert store.repo("TEST-ORG", "alpha")["empty"] is True
    assert store.phase("TEST-ORG", "alpha", "clone")["status"] == "skipped"
    caplog.set_level(logging.WARNING)
    res = p0.clone_all(org, store, fake_token, ["alpha"], sleep=nosleep)
    assert res["results"] == {"alpha": "cloned"}
    assert store.repo("TEST-ORG", "alpha")["empty"] is False
    assert store.phase("TEST-ORG", "alpha", "clone")["status"] == "done"
    assert "reported size 0" in caplog.text


def test_api_empty_confirmed_by_ls_remote(setup, fake_token, monkeypatch):
    org, store, client = setup
    p0.discover(org, store, client)
    calls = []
    real = gitops.ls_remote_sha
    monkeypatch.setattr(gitops, "ls_remote_sha",
                        lambda *a, **k: calls.append(a) or real(*a, **k))
    res = p0.clone_all(org, store, fake_token, ["empty-one"], sleep=nosleep)
    assert res["results"] == {"empty-one": "skipped"} and len(calls) == 1
    ph = store.phase("TEST-ORG", "empty-one", "clone")
    assert ph["status"] == "skipped" and ph["skip_reason"] == "empty"


def test_clone_failure_not_fatal(setup, fake_token):
    org, store, client = setup
    client.repos.append(api_repo("broken"))
    org.allowlist = org.allowlist + ["broken"]
    p0.discover(org, store, client)
    res = p0.clone_all(org, store, fake_token, sleep=nosleep)
    assert res["failed"] == ["broken"]
    assert res["counts"]["cloned"] == 2
    ph = store.phase("TEST-ORG", "broken", "clone")
    assert ph["status"] == "failed" and ph["error"]
    assert not paths.clone_dir("TEST-ORG", "broken").exists()
    assert not paths.clone_dir("TEST-ORG", "broken").with_name("broken.partial").exists()


def test_running_leftover_is_retried(setup, fake_token):
    org, store, client = setup
    p0.discover(org, store, client)
    store.set_phase("TEST-ORG", "alpha", "clone", status="running")
    res = p0.clone_all(org, store, fake_token, ["alpha"], sleep=nosleep)
    assert res["results"]["alpha"] == "cloned"


class _Resp:
    def __init__(self, body, headers=None):
        self._b = json.dumps(body).encode()
        self.headers = headers or {}

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_pagination_161(monkeypatch, fake_token):
    pages = {1: [api_repo(f"r{i}") for i in range(100)],
             2: [api_repo(f"r{i}") for i in range(100, 161)]}
    seen = []

    def fake_urlopen(req, timeout=None):
        assert req.headers["Authorization"] == f"Bearer {fake_token}"
        page = int(req.full_url.rsplit("page=", 1)[1])
        seen.append(page)
        return _Resp(pages[page])

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    repos = GitHubClient(fake_token, sleep=nosleep).list_org_repos("TEST-ORG")
    assert len(repos) == 161 and seen == [1, 2]


def test_retry_on_429(monkeypatch, fake_token):
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append(1)
        if len(calls) == 1:
            raise urllib.error.HTTPError(req.full_url, 429, "rate", {"Retry-After": "1"}, None)
        return _Resp([api_repo("a")])

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert len(GitHubClient(fake_token, sleep=nosleep).list_org_repos("O")) == 1
    assert len(calls) == 2


def test_token_never_written(setup, fake_token, monkeypatch, caplog):
    """End-to-end discover+clone+ledger: token absent from argv, logs, files, .git/config."""
    org, store, client = setup
    argvs = []
    real_run = subprocess.run

    def spy(cmd, *a, **k):
        argvs.append(list(cmd))
        return real_run(cmd, *a, **k)

    monkeypatch.setattr(subprocess, "run", spy)
    caplog.set_level(logging.DEBUG)
    p0.discover(org, store, client)
    p0.clone_all(org, store, fake_token, sleep=nosleep)
    p1.ledger_all(org, store)
    forms = [fake_token, basic_auth_b64(fake_token)]
    assert argvs
    for argv in argvs:
        assert not any(f in " ".join(argv) for f in forms)
    assert not any(f in caplog.text for f in forms)
    root = paths.root()
    for p in root.rglob("*"):
        if p.is_file() and (p.name == "config" or "repos" not in p.parts or ".git" not in p.parts):
            data = p.read_bytes()
            assert not any(f.encode() in data for f in forms), p
    for cfg in (root / "repos").glob("*/*/.git/config"):
        assert "extraheader" not in cfg.read_text().lower()
    assert scan_for_secret(fake_token) == []
    # and the scanner does detect a leak
    (root / "runs" / "leak.txt").write_text(f"x {fake_token}")
    assert scan_for_secret(fake_token) == [root / "runs" / "leak.txt"]
