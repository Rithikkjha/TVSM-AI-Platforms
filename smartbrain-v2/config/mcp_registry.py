"""MCP server registry loader.

Parses `mcp_servers.yaml` into validated Pydantic models. Used by the
MCP_Orchestrator at startup to enumerate the data sources (GitHub, Jira,
Confluence, ...) it should connect to.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError


class MCPServerConfig(BaseModel):
    """One registered MCP server.

    `config` is intentionally a free-form dict — each server type
    (GitHub vs mcp-atlassian vs ...) has its own keys, and interpretation
    is deferred to the orchestrator/adapter for that server. Validation
    here only covers the envelope.
    """

    name: str = Field(..., min_length=1, description="Unique logical name, e.g. 'github'.")
    type: str = Field(
        ...,
        min_length=1,
        description="MCP server implementation id, e.g. '@modelcontextprotocol/server-github'.",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Server-specific configuration (repos, projects, token env vars, ...).",
    )


class MCPRegistry(BaseModel):
    """Top-level registry document: a list of registered servers."""

    servers: list[MCPServerConfig] = Field(default_factory=list)


class MCPRegistryError(ValueError):
    """Raised when the MCP registry YAML is missing or structurally invalid."""


def load_mcp_registry(path: str | Path) -> MCPRegistry:
    """Load and validate the MCP server registry from a YAML file.

    Args:
        path: Filesystem path to the MCP registry YAML document.

    Returns:
        A validated `MCPRegistry` instance.

    Raises:
        MCPRegistryError: If the file does not exist, is not valid YAML,
            does not contain a top-level mapping, or fails Pydantic
            validation (e.g. missing `name`/`type`).
    """

    registry_path = Path(path)
    if not registry_path.is_file():
        raise MCPRegistryError(f"MCP registry file not found: {registry_path}")

    try:
        raw = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise MCPRegistryError(f"Invalid YAML in MCP registry {registry_path}: {exc}") from exc

    if raw is None:
        # Empty file → empty registry. Harmless but explicit.
        raw = {"servers": []}

    if not isinstance(raw, dict):
        raise MCPRegistryError(
            f"MCP registry {registry_path} must be a YAML mapping at top level, "
            f"got {type(raw).__name__}."
        )

    try:
        return MCPRegistry.model_validate(raw)
    except ValidationError as exc:
        raise MCPRegistryError(
            f"MCP registry {registry_path} failed schema validation: {exc}"
        ) from exc
