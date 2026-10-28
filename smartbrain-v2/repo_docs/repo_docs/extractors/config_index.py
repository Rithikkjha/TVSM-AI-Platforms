"""Repo-wide config index built by ``shared.config`` (+ env vars registered by ``shared.infra``).

Raw values live in memory only; anything written must go through ``config_classify`` first
(``public_values`` does that). Placeholder chains (``${a}`` -> property ``a`` -> ``${A_ENV}`` -> env var
defined in ``.env`` / Dockerfile ``ENV`` / compose ``environment`` / pipeline variables / k8s env) are
resolved up to depth 5, cycle-safe.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..config_classify import canonical_key, classify, key_is_secret, value_is_secret

MAX_DEPTH = 5
_PH = re.compile(r"\$\{([^{}:]+?)(?::([^{}]*))?\}|#\{([^{}]+)\}#|\$\(([A-Za-z0-9_.\-]+)\)"
                 r"|%([A-Za-z0-9_.:\-]+)%")
_ENV_NAME = re.compile(r"^[A-Z_][A-Z0-9_]*$")


@dataclass
class ConfigDef:
    name: str            # key as written (flattened: "A:B:C", "spring.x.y", "ENV_NAME")
    canonical: str
    env: str
    value: object        # RAW value (never written)
    file: str
    line: int
    subproject: str
    provided_by: str
    source: str = "property"   # property | env


@dataclass
class Resolution:
    value: str | None              # fully resolved value (None if unresolved)
    chain: list = field(default_factory=list)       # keys / env names followed
    unresolved: list = field(default_factory=list)  # placeholder names without a definition


class ConfigIndex:
    def __init__(self) -> None:
        self._by_key: dict[str, list[ConfigDef]] = {}
        self._env_exact: dict[str, list[ConfigDef]] = {}

    # ---- building ------------------------------------------------------------------------
    def add(self, d: ConfigDef) -> None:
        self._by_key.setdefault(d.canonical, []).append(d)
        if d.source == "env":
            self._env_exact.setdefault(d.name, []).append(d)

    def add_env(self, name: str, value, env: str, file: str, line: int, subproject: str,
                provided_by: str) -> ConfigDef:
        d = ConfigDef(name, canonical_key(name)[0], env, value, file, line, subproject,
                      provided_by, "env")
        self.add(d)
        return d

    # ---- lookup --------------------------------------------------------------------------
    @staticmethod
    def _pick(defs: list[ConfigDef], subproject: str | None) -> list[ConfigDef]:
        if subproject is not None:
            same = [d for d in defs if d.subproject == subproject]
            if same:
                defs = same
        return sorted(defs, key=lambda d: (d.source != "property", d.file, d.line))

    def keys(self) -> list[str]:
        return sorted(self._by_key)

    def defs(self, key: str, subproject: str | None = None) -> list[ConfigDef]:
        """Definitions of ``key`` (any spelling; canonical match), same subproject preferred."""
        return self._pick(self._by_key.get(canonical_key(key)[0], []), subproject)

    def env_defs(self, name: str, subproject: str | None = None) -> list[ConfigDef]:
        return self._pick(self._env_exact.get(name, []), subproject)

    def envs(self, key: str, subproject: str | None = None) -> list[str]:
        return sorted({d.env for d in self.defs(key, subproject)})

    @staticmethod
    def _for_env(defs: list[ConfigDef], env: str) -> ConfigDef | None:
        for want in (env, "default"):
            for d in defs:
                if d.env == want:
                    return d
        return None

    def raw(self, key: str, env: str = "default", subproject: str | None = None):
        d = self._for_env(self.defs(key, subproject), env)
        return d.value if d else None

    def _lookup_name(self, name: str, env: str, subproject: str | None) -> ConfigDef | None:
        if _ENV_NAME.match(name):
            d = self._for_env(self.env_defs(name, subproject), env)
            if d:
                return d
        return self._for_env(self.defs(name, subproject), env)

    # ---- resolution ----------------------------------------------------------------------
    def resolve(self, value, env: str = "default", subproject: str | None = None,
                depth: int = MAX_DEPTH, _seen: frozenset = frozenset()) -> Resolution:
        """Resolve placeholders inside ``value``."""
        if value is None:
            return Resolution(None)
        s = str(value)
        res = Resolution(None)
        out, pos = [], 0
        for m in _PH.finditer(s):
            out.append(s[pos:m.start()])
            pos = m.end()
            name = next(g for g in (m.group(1), m.group(3), m.group(4), m.group(5)) if g)
            name = name.strip()
            default = m.group(2)
            res.chain.append(name)
            d = None if (depth <= 0 or name in _seen) else self._lookup_name(name, env, subproject)
            if d is None:
                if default is not None:
                    inner = self.resolve(default, env, subproject, depth - 1, _seen | {name})
                    res.chain += inner.chain
                    res.unresolved += inner.unresolved
                    out.append(inner.value if inner.value is not None else "")
                    if inner.value is None:
                        res.unresolved.append(name)
                else:
                    res.unresolved.append(name)
                    out.append("")
                continue
            inner = self.resolve(d.value, env, subproject, depth - 1, _seen | {name})
            res.chain += inner.chain
            res.unresolved += inner.unresolved
            out.append(inner.value if inner.value is not None else "")
        out.append(s[pos:])
        res.value = None if res.unresolved else "".join(out)
        return res

    def resolve_key(self, key: str, env: str = "default",
                    subproject: str | None = None) -> Resolution:
        d = self._for_env(self.defs(key, subproject), env)
        if d is None:
            return Resolution(None, [], [key])
        r = self.resolve(d.value, env, subproject, MAX_DEPTH, frozenset({canonical_key(key)[0]}))
        r.chain.insert(0, key)
        return r

    def resolved_envs(self, key: str, subproject: str | None = None) -> list[str]:
        """Envs in which ``key`` (or anything its default chain references) is defined."""
        envs = set(self.envs(key, subproject))
        r = self.resolve_key(key, "default", subproject)
        for name in r.chain[1:]:
            envs |= {d.env for d in self.defs(name, subproject)}
            envs |= {d.env for d in self.env_defs(name, subproject)}
        return sorted(envs)

    def public_values(self, key: str, subproject: str | None = None) -> dict[str, str]:
        """{env: resolved value} for values the classifier allows (rule 5) only."""
        out: dict[str, str] = {}
        for env in self.resolved_envs(key, subproject):
            r = self.resolve_key(key, env, subproject)
            if r.value is None or not r.value:
                continue
            if any(key_is_secret(k) for k in r.chain) or value_is_secret(r.value):
                continue
            for k in r.chain:
                c = classify(k, r.value)
                if c.record_value is not None and not c.secret:
                    out[env] = c.record_value
                    break
        return out
