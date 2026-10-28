from __future__ import annotations

import pytest

from repo_docs import paths
from repo_docs.config import ConfigError, load_allowlist, load_config


def test_allowlist_parsing(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("# header\n\n  alpha  \nbeta   # empty\n# gamma\nalpha\nCase-Name\n")
    assert load_allowlist(f) == ["alpha", "beta", "Case-Name"]
    with pytest.raises(ConfigError):
        load_allowlist(tmp_path / "missing.txt")


def test_load_config_defaults_and_matching(root):
    cfg = load_config()
    org = cfg.org("TEST-ORG")
    assert org.workers == 3 and org.max_retries == 0 and org.clone_depth == 1
    assert org.allowlist == ["alpha", "beta", "empty-one"]
    assert org.matches("alpha") and not org.matches("gamma") and not org.matches("Alpha")
    org.exclude = ["be*"]
    assert not org.matches("beta")
    assert org.token_env_file.is_absolute()
    with pytest.raises(ConfigError):
        cfg.org("NOPE")


def test_relative_token_path(root):
    (root / "config" / "orgs.yaml").write_text(
        "schema_version: 1\norgs:\n  - {name: X, token_env_file: ../.env, token_key: K}\n")
    org = load_config().org("X")
    assert org.token_env_file == (paths.root() / "../.env").resolve()
    assert org.allowlist is None and org.matches("anything")


@pytest.mark.parametrize("body", [
    "schema_version: 2\norgs: [{name: X, token_env_file: a, token_key: K}]\n",
    "schema_version: 1\norgs: []\n",
    "schema_version: 1\norgs: [{name: X, token_key: K}]\n",
    "schema_version: 1\ndefaults: {workers: -1}\norgs: [{name: X, token_env_file: a, token_key: K}]\n",
    "schema_version: 1\norgs: [{name: X, token_env_file: a, token_key: K, include: x}]\n",
    "schema_version: 1\norgs: [{name: X, token_env_file: a, token_key: K, allowlist: nope.txt}]\n",
    ": : :\n",
])
def test_invalid_config(root, body):
    (root / "config" / "orgs.yaml").write_text(body)
    with pytest.raises(ConfigError):
        load_config()
