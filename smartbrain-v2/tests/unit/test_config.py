"""Unit tests for `src.config` — Settings and MCP registry loader.

These are setup-task tests only; no property-based tests for configuration.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from config.mcp_registry import (
    MCPRegistry,
    MCPRegistryError,
    MCPServerConfig,
    load_mcp_registry,
)
from config.settings import Settings, get_settings

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def test_get_settings_returns_settings_instance_with_defaults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`get_settings()` returns a `Settings` populated from defaults when no
    env vars (and no `.env` file) are present."""

    # Isolate from the real process env and any .env file on disk by
    # pointing CWD at an empty tmp dir and clearing all fields we care about.
    monkeypatch.chdir(tmp_path)
    for var in [
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT_GPT4O",
        "AZURE_OPENAI_DEPLOYMENT_EMBEDDING",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_KEY",
        "QDRANT_URL",
        "GITHUB_TOKEN",
        "JIRA_TOKEN",
        "JIRA_EMAIL",
        "JIRA_URL",
        "CONFLUENCE_TOKEN",
        "CONFLUENCE_URL",
        "API_KEY",
        "API_VERSION_PREFIX",
        "MCP_SERVERS_CONFIG_PATH",
        "STALENESS_THRESHOLD_HOURS",
        "FULL_SYNC_INTERVAL_HOURS",
        "LLM_CONTEXT_TOKEN_BUDGET",
        "VECTOR_SEARCH_TOP_K",
        "GRAPH_EXPANSION_HOPS",
        "LOG_LEVEL",
    ]:
        monkeypatch.delenv(var, raising=False)

    get_settings.cache_clear()
    settings = get_settings()

    assert isinstance(settings, Settings)
    assert settings.neo4j_uri == "bolt://neo4j:7687"
    assert settings.neo4j_user == "neo4j"
    assert settings.azure_openai_deployment_gpt4o == "gpt-4o"
    assert settings.azure_openai_deployment_embedding == "text-embedding-3-large"
    assert settings.azure_openai_api_version == "2024-06-01"
    assert settings.api_key == "dev-api-key"
    assert settings.api_version_prefix == "/v1"
    assert settings.mcp_servers_config_path == "src/config/mcp_servers.yaml"
    assert settings.staleness_threshold_hours == 24
    assert settings.full_sync_interval_hours == 6
    assert settings.llm_context_token_budget == 8000
    assert settings.vector_search_top_k == 10
    assert settings.graph_expansion_hops == 2
    assert settings.log_level == "INFO"
    # Optional Azure Search fields default to None
    assert settings.azure_search_endpoint is None
    assert settings.azure_search_key is None


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Consecutive calls return the same instance (lru_cache singleton)."""

    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second


def test_settings_reads_env_overrides(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Environment variables override defaults (case-insensitive matching)."""

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NEO4J_URI", "bolt://custom:7687")
    monkeypatch.setenv("API_KEY", "override-key")
    monkeypatch.setenv("STALENESS_THRESHOLD_HOURS", "48")

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.neo4j_uri == "bolt://custom:7687"
    assert settings.api_key == "override-key"
    assert settings.staleness_threshold_hours == 48


# ---------------------------------------------------------------------------
# MCP registry loader
# ---------------------------------------------------------------------------


EXAMPLE_YAML_PATH = Path("src/config/mcp_servers.yaml")


def test_load_mcp_registry_parses_example_yaml() -> None:
    """The committed `mcp_servers.yaml` parses into a valid `MCPRegistry`."""

    registry = load_mcp_registry(EXAMPLE_YAML_PATH)

    assert isinstance(registry, MCPRegistry)
    names = [s.name for s in registry.servers]
    assert names == ["github", "jira", "confluence"]

    github = registry.servers[0]
    assert isinstance(github, MCPServerConfig)
    assert github.type == "@modelcontextprotocol/server-github"
    assert github.config["org"] == "example-org"
    assert github.config["repos"] == ["example-service-a", "example-service-b"]
    assert github.config["token_env"] == "GITHUB_TOKEN"

    jira = registry.servers[1]
    assert jira.type == "mcp-atlassian"
    assert jira.config["projects"] == ["ENG", "PLATFORM"]
    assert jira.config["email_env"] == "JIRA_EMAIL"


def test_load_mcp_registry_accepts_string_path() -> None:
    """Passing a `str` path works identically to passing a `Path`."""

    registry = load_mcp_registry(str(EXAMPLE_YAML_PATH))
    assert len(registry.servers) == 3


def test_load_mcp_registry_missing_file_raises(tmp_path: Path) -> None:
    """Missing files raise a clear `MCPRegistryError`."""

    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(MCPRegistryError, match="not found"):
        load_mcp_registry(missing)


def test_load_mcp_registry_invalid_yaml_raises(tmp_path: Path) -> None:
    """Malformed YAML surfaces as `MCPRegistryError`."""

    bad = tmp_path / "bad.yaml"
    bad.write_text("servers: [unclosed\n", encoding="utf-8")
    with pytest.raises(MCPRegistryError, match="Invalid YAML"):
        load_mcp_registry(bad)


def test_load_mcp_registry_non_mapping_top_level_raises(tmp_path: Path) -> None:
    """A YAML list at the top level is rejected with a clear error."""

    wrong = tmp_path / "wrong.yaml"
    wrong.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(MCPRegistryError, match="mapping at top level"):
        load_mcp_registry(wrong)


def test_load_mcp_registry_validation_error_raises(tmp_path: Path) -> None:
    """Entries missing required `name`/`type` fields fail validation."""

    bad_schema = tmp_path / "bad_schema.yaml"
    bad_schema.write_text("servers:\n  - config: {}\n", encoding="utf-8")
    with pytest.raises(MCPRegistryError, match="schema validation"):
        load_mcp_registry(bad_schema)


def test_load_mcp_registry_empty_file_returns_empty_registry(tmp_path: Path) -> None:
    """An empty YAML file yields a registry with zero servers."""

    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    registry = load_mcp_registry(empty)
    assert registry.servers == []
