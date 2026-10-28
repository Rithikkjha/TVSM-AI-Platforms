"""Multi-stack / monorepo-aware stack detection over the tracked file list."""

from __future__ import annotations

import fnmatch
import json
import posixpath
import re
from dataclasses import asdict, dataclass, field
from typing import Callable

IGNORE_DIRS = {"node_modules", "vendor", "bower_components", "Pods", ".git", "dist", "build",
               "bin", "obj", "target", "packages", ".next", "out", "coverage"}

ReadFn = Callable[[str], "str | None"]


@dataclass
class StackHit:
    stack: str
    subproject: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _dir(p: str) -> str:
    d = posixpath.dirname(p)
    return d if d else "."


def _ignored(p: str) -> bool:
    parts = p.split("/")[:-1]
    if any(x in IGNORE_DIRS for x in parts):
        return True
    return False


def _json(text: str | None) -> dict:
    if not text:
        return {}
    try:
        v = json.loads(text)
        return v if isinstance(v, dict) else {}
    except ValueError:
        return {}


def detect_stacks(paths: list[str], read_file: ReadFn) -> list[StackHit]:
    hits: dict[tuple[str, str], set[str]] = {}

    def add(stack: str, sub: str, ev: str) -> None:
        hits.setdefault((stack, sub), set()).add(ev)

    files = [p for p in paths if not _ignored(p)]
    names = {p: posixpath.basename(p) for p in files}

    # .NET
    proj = [p for p in files if fnmatch.fnmatch(names[p], "*.[cfv][sb]proj")
            and names[p].rsplit(".", 1)[-1] in ("csproj", "fsproj", "vbproj")]
    for p in proj:
        add("dotnet", _dir(p), p)
    if not proj:
        for p in files:
            if names[p].endswith(".sln"):
                add("dotnet", _dir(p), p)
    # Classic ASP.NET without project files (web.config + .aspx/.cs)
    # is still covered by csproj in practice; not inferred here.

    # Java / Android
    android_manifests = [p for p in files if names[p] == "AndroidManifest.xml"]
    for p in files:
        if names[p] in ("pom.xml", "build.gradle", "build.gradle.kts"):
            sub = _dir(p)
            add("java", sub, p)
            txt = read_file(p) if names[p] != "pom.xml" else None
            is_android = bool(txt and "com.android" in txt)
            for m in android_manifests:
                if sub == "." or m.startswith(sub + "/"):
                    is_android = True
                    add("android", sub, m)
            if is_android:
                add("android", sub, p)

    # Node family
    for p in files:
        if names[p] != "package.json":
            continue
        sub = _dir(p)
        add("node", sub, p)
        pkg = _json(read_file(p))
        deps: dict = {}
        for k in ("dependencies", "devDependencies", "peerDependencies"):
            if isinstance(pkg.get(k), dict):
                deps.update(pkg[k])
        prefix = "" if sub == "." else sub + "/"
        if "@angular/core" in deps or (prefix + "angular.json") in names:
            add("angular", sub, (prefix + "angular.json") if (prefix + "angular.json") in names else p)
        if "next" in deps:
            add("nextjs", sub, p)
        if "react-native" in deps:
            add("react-native", sub, p)
        elif "react" in deps and "next" not in deps:
            add("react", sub, p)
        if "@nestjs/core" in deps:
            add("nest", sub, p)
        if "express" in deps:
            add("express", sub, p)
        if "vue" in deps or "nuxt" in deps:
            add("vue", sub, p)

    # Dart / Flutter
    for p in files:
        if names[p] == "pubspec.yaml":
            sub = _dir(p)
            add("dart", sub, p)
            txt = read_file(p) or ""
            if re.search(r"^\s*flutter\s*:", txt, re.M) or "sdk: flutter" in txt:
                add("flutter", sub, p)

    # iOS
    for p in paths:
        if any(x in IGNORE_DIRS for x in p.split("/")[:-1]) and "Pods" in p.split("/"):
            continue
        parts = p.split("/")
        for i, seg in enumerate(parts[:-1]):
            if seg.endswith(".xcodeproj") or seg.endswith(".xcworkspace"):
                add("ios", "/".join(parts[:i]) or ".", "/".join(parts[: i + 1]))
                break
    for p in files:
        if names[p] in ("Podfile", "Package.swift"):
            add("ios", _dir(p), p)

    # Python
    for p in files:
        n = names[p]
        if fnmatch.fnmatch(n, "requirements*.txt") or n in ("pyproject.toml", "setup.py", "Pipfile"):
            add("python", _dir(p), p)

    # PHP
    for p in files:
        if names[p] == "composer.json":
            add("php", _dir(p), p)

    return sorted(
        (StackHit(s, sub, sorted(ev)) for (s, sub), ev in hits.items()),
        key=lambda h: (h.stack, h.subproject),
    )


def stack_ids(hits: list[StackHit]) -> list[str]:
    return sorted({h.stack for h in hits})
