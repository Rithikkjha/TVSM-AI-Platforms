"""Loads config/orgs.yaml into typed dataclasses (defaults merged per org)."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import paths


class ConfigError(ValueError):
    pass


@dataclass
class Defaults:
    workers: int = 5
    max_retries: int = 4
    max_file_bytes: int = 1_000_000
    clone_depth: int = 1


@dataclass
class OrgConfig:
    name: str
    token_env_file: Path
    token_key: str
    enabled: bool = True
    api_base: str = "https://api.github.com"
    git_base: str = "https://github.com"
    include: list[str] = field(default_factory=lambda: ["*"])
    exclude: list[str] = field(default_factory=list)
    include_archived: bool = True
    allowlist_path: Path | None = None
    allowlist: list[str] | None = None
    service_id_overrides: dict[str, str] = field(default_factory=dict)
    self_repos: list[str] = field(default_factory=list)
    internal_package_patterns: list[str] = field(default_factory=list)
    workers: int = 5
    max_retries: int = 4
    max_file_bytes: int = 1_000_000
    clone_depth: int = 1

    def in_allowlist(self, repo: str) -> bool:
        return self.allowlist is None or repo in self.allowlist

    def matches(self, repo: str) -> bool:
        return (
            self.in_allowlist(repo)
            and any(fnmatch.fnmatchcase(repo, p) for p in self.include)
            and not any(fnmatch.fnmatchcase(repo, p) for p in self.exclude)
        )

    def clone_url(self, repo: str) -> str:
        return f"{self.git_base.rstrip('/')}/{self.name}/{repo}.git"


@dataclass
class Config:
    schema_version: int
    defaults: Defaults
    orgs: list[OrgConfig]

    def org(self, name: str) -> OrgConfig:
        for o in self.orgs:
            if o.name == name:
                return o
        raise ConfigError(f"unknown org {name!r} (known: {[o.name for o in self.orgs]})")

    def enabled_orgs(self) -> list[OrgConfig]:
        return [o for o in self.orgs if o.enabled]


def load_allowlist(path: Path) -> list[str]:
    if not path.is_file():
        raise ConfigError(f"allowlist file not found: {path}")
    names: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line and line not in names:
            names.append(line)
    return names


def _int(d: dict, key: str, default: int, where: str) -> int:
    v = d.get(key, default)
    if not isinstance(v, int) or isinstance(v, bool) or v < 0:
        raise ConfigError(f"{where}.{key} must be a non-negative integer")
    return v


def _strlist(d: dict, key: str, default: list[str], where: str) -> list[str]:
    v = d.get(key, default)
    if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
        raise ConfigError(f"{where}.{key} must be a list of strings")
    return list(v)


def load_config(path: Path | None = None) -> Config:
    path = path or paths.config_path()
    if not path.is_file():
        raise ConfigError(f"config not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"invalid YAML in {path}: {e}") from e
    if not isinstance(data, dict):
        raise ConfigError("config root must be a mapping")
    sv = data.get("schema_version")
    if sv != 1:
        raise ConfigError("schema_version must be 1")
    dd = data.get("defaults") or {}
    if not isinstance(dd, dict):
        raise ConfigError("defaults must be a mapping")
    defaults = Defaults(
        workers=_int(dd, "workers", 5, "defaults"),
        max_retries=_int(dd, "max_retries", 4, "defaults"),
        max_file_bytes=_int(dd, "max_file_bytes", 1_000_000, "defaults"),
        clone_depth=_int(dd, "clone_depth", 1, "defaults"),
    )
    raw_orgs = data.get("orgs")
    if not isinstance(raw_orgs, list) or not raw_orgs:
        raise ConfigError("orgs must be a non-empty list")
    orgs: list[OrgConfig] = []
    for i, o in enumerate(raw_orgs):
        where = f"orgs[{i}]"
        if not isinstance(o, dict):
            raise ConfigError(f"{where} must be a mapping")
        for req in ("name", "token_env_file", "token_key"):
            if not isinstance(o.get(req), str) or not o.get(req):
                raise ConfigError(f"{where}.{req} is required (string)")
        overrides = o.get("service_id_overrides") or {}
        if not isinstance(overrides, dict):
            raise ConfigError(f"{where}.service_id_overrides must be a mapping")
        allow_path = paths.resolve(o["allowlist"]) if o.get("allowlist") else None
        org = OrgConfig(
            name=o["name"],
            token_env_file=paths.resolve(o["token_env_file"]),
            token_key=o["token_key"],
            enabled=bool(o.get("enabled", True)),
            api_base=str(o.get("api_base", "https://api.github.com")),
            git_base=str(o.get("git_base", "https://github.com")),
            include=_strlist(o, "include", ["*"], where),
            exclude=_strlist(o, "exclude", [], where),
            include_archived=bool(o.get("include_archived", True)),
            allowlist_path=allow_path,
            allowlist=load_allowlist(allow_path) if allow_path else None,
            service_id_overrides={str(k): str(v) for k, v in overrides.items()},
            self_repos=_strlist(o, "self_repos", [], where),
            internal_package_patterns=_strlist(o, "internal_package_patterns", [], where),
            workers=_int(o, "workers", defaults.workers, where),
            max_retries=_int(o, "max_retries", defaults.max_retries, where),
            max_file_bytes=_int(o, "max_file_bytes", defaults.max_file_bytes, where),
            clone_depth=_int(o, "clone_depth", defaults.clone_depth, where),
        )
        if org.workers < 1:
            raise ConfigError(f"{where}.workers must be >= 1")
        if any(x.name == org.name for x in orgs):
            raise ConfigError(f"{where}.name duplicate org {org.name!r}")
        orgs.append(org)
    return Config(schema_version=sv, defaults=defaults, orgs=orgs)
