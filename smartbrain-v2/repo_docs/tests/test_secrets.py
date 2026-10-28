from __future__ import annotations

import base64
import logging
import subprocess

import pytest

from repo_docs import gitops
from repo_docs.secrets import (SecretFilter, TokenError, basic_auth_b64, git_auth_env,
                               load_token, redact, secret_forms)


def test_load_token_variants(tmp_path, fake_token):
    """Quoted, unquoted, export-prefixed and commented lines are parsed."""
    f = tmp_path / "e.env"
    for line in (f"GITHUB_TOKEN={fake_token}", f'GITHUB_TOKEN="{fake_token}"',
                 f"export GITHUB_TOKEN='{fake_token}'", f"GITHUB_TOKEN={fake_token} # c"):
        f.write_text(f"# GITHUB_TOKEN=wrong\nA=1\n{line}\n")
        assert load_token(f, "GITHUB_TOKEN") == fake_token


def test_missing_key_message_has_no_value(tmp_path, fake_token):
    """Errors name the file and key but never the value."""
    f = tmp_path / "e.env"
    f.write_text(f"OTHER={fake_token}\n")
    with pytest.raises(TokenError) as e:
        load_token(f, "GITHUB_TOKEN")
    assert fake_token not in str(e.value) and "GITHUB_TOKEN" in str(e.value)
    with pytest.raises(TokenError):
        load_token(tmp_path / "nope.env", "GITHUB_TOKEN")


def test_redact_raw_and_b64(fake_token):
    b64 = basic_auth_b64(fake_token)
    assert base64.b64decode(b64).decode().endswith(fake_token)
    out = redact(f"x {fake_token} y {b64}", secret_forms(fake_token))
    assert fake_token not in out and b64 not in out and out.count("***") == 2


def test_git_auth_env_only_in_header_value(fake_token):
    env = git_auth_env(fake_token, "https://github.com")
    assert env["GIT_CONFIG_KEY_0"] == "http.https://github.com/.extraheader"
    for k, v in env.items():
        assert fake_token not in v and fake_token not in k
    assert basic_auth_b64(fake_token) in env["GIT_CONFIG_VALUE_0"]
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GIT_CONFIG_COUNT"] == "2"
    assert env["GIT_CONFIG_KEY_1"] == "credential.helper" and env["GIT_CONFIG_VALUE_1"] == ""


def _credential_fill(env_extra):
    return subprocess.run(["git", "credential", "fill"], env=gitops._env(env_extra),
                          input=b"protocol=https\nhost=example.invalid\n\n",
                          capture_output=True, timeout=30)


def test_git_auth_env_disables_ambient_helpers(tmp_path, monkeypatch, fake_token):
    """A helper in the global gitconfig must not run under git_auth_env."""
    marker = tmp_path / "helper-ran"
    cfg = tmp_path / "gitconfig"
    cfg.write_text(f'[credential]\n\thelper = "!f() {{ touch {marker}; }}; f"\n')
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(cfg))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    p = _credential_fill(git_auth_env(fake_token, "https://example.invalid"))
    assert p.returncode != 0
    assert not marker.exists()
    # control: without the auth env the ambient helper does run
    _credential_fill({"GIT_ASKPASS": "/usr/bin/false"})
    assert marker.exists()


def test_secret_filter_redacts(fake_token, caplog):
    SecretFilter.register(fake_token)
    logger = logging.getLogger("t-secret")
    handler = logging.Handler()
    handler.addFilter(SecretFilter())
    records = []
    handler.emit = records.append
    logger.addHandler(handler)
    try:
        logger.warning("token=%s", fake_token)
    finally:
        logger.removeHandler(handler)
    assert fake_token not in records[0].getMessage()
