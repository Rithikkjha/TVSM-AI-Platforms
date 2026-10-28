"""shared.manifests: build manifests -> ``dependency`` / ``artifact`` items.

pom.xml, *.csproj, Directory.Packages.props, packages.config, package.json, libs.versions.toml
(real parsers -> ``full``); build.gradle(.kts) (regex -> ``partial``). Lock files are skipped in the
ledger and never read. Generated OpenAPI specs (Swashbuckle / springdoc / @nestjs/swagger
packages) are reported as ``api_contract`` items with ``generated: true``.
"""
from __future__ import annotations

import fnmatch
import posixpath
import re
import tomllib

from ..inventory_schema import make_item
from . import configfmt
from .base import ExtractResult, Extractor, RepoContext

NPM_SCOPES = (("dependencies", "runtime"), ("devDependencies", "dev"),
              ("peerDependencies", "peer"), ("optionalDependencies", "optional"))
_GRADLE = re.compile(
    r"""^\s*(implementation|api|compileOnly|runtimeOnly|testImplementation|testCompileOnly|"""
    r"""testRuntimeOnly|annotationProcessor|kapt|developmentOnly|compile|testCompile)\s*\(?\s*"""
    r"""(platform\(\s*)?['"]([^'":\s]+):([^'":\s]+)(?::([^'"\s]+))?['"]""")
_GRADLE_SCOPE = {"testImplementation": "test", "testCompileOnly": "test", "testRuntimeOnly": "test",
                 "testCompile": "test", "compileOnly": "provided", "runtimeOnly": "runtime",
                 "annotationProcessor": "provided", "kapt": "provided",
                 "developmentOnly": "runtime"}
GENERATORS = {
    "swashbuckle": ("Swashbuckle.AspNetCore*", "/swagger/v1/swagger.json"),
    "springdoc": ("org.springdoc:springdoc-openapi*", "/v3/api-docs"),
    "nestjs-swagger": ("@nestjs/swagger", None),
}


def scope(path: str) -> str | None:
    name = posixpath.basename(path)
    if name == "pom.xml":
        return "pom"
    if name.endswith(".csproj"):
        return "csproj"
    if name == "Directory.Packages.props":
        return "props"
    if name == "packages.config":
        return "packages.config"
    if name == "package.json":
        return "npm"
    if name == "libs.versions.toml":
        return "toml"
    if name in ("build.gradle", "build.gradle.kts"):
        return "gradle"
    return None


def _is_internal(ctx: RepoContext, name: str) -> bool:
    low = name.lower()
    return any(fnmatch.fnmatchcase(low, p.lower()) for p in ctx.internal_patterns)


class SharedManifests(Extractor):
    id = "shared.manifests"
    stacks = ()
    extractor_version = "0.1.0"

    def extract(self, ctx: RepoContext, subproject: str | None) -> ExtractResult:
        res = ExtractResult()
        files = ctx.paths(subproject, lambda e: scope(e["path"]) is not None)
        central: dict[str, str] = {}
        own: set[str] = set()
        poms: dict[str, configfmt.XmlDoc] = {}
        # pass 1: central versions + own artifacts (so module deps are internal)
        for path in files:
            kind = scope(path)
            text = ctx.read_text(path) or ""
            if kind == "props":
                doc = configfmt.xml_with_lines(text)
                if doc.root is not None:
                    for el in doc.root.iter("PackageVersion"):
                        if el.get("Include") and el.get("Version"):
                            central[el.get("Include")] = el.get("Version")
            elif kind == "pom":
                doc = configfmt.xml_with_lines(text)
                poms[path] = doc
                if doc.root is not None:
                    g = configfmt.xml_text(doc.root, "groupId") or configfmt.xml_text(
                        doc.root.find("parent"), "groupId")
                    a = configfmt.xml_text(doc.root, "artifactId")
                    if g and a:
                        own.add(f"{g}:{a}")
        ctx.hints.setdefault("own_artifacts", set()).update(own)
        for path in files:
            kind = scope(path)
            text = ctx.read_text(path)
            if text is None:
                res.touch(path, "partial", "unreadable")
                continue
            if kind == "pom":
                self._pom(ctx, path, text, res, own, poms.get(path))
            elif kind == "csproj":
                self._csproj(ctx, path, text, res, central)
            else:
                getattr(self, "_" + kind.replace(".", "_"))(ctx, path, text, res)
        return res

    # ---- helpers ---------------------------------------------------------------------------
    def _dep(self, ctx, res, path, line, eco, name, version, version_from, scope_, kind,
             internal=None, confidence="high"):
        internal = _is_internal(ctx, name) if internal is None else internal
        attrs = {"ecosystem": eco, "name": name, "version": version, "version_from": version_from,
                 "scope": scope_, "manifest": path, "internal": internal,
                 "internal_repo": ctx.repo if internal and name in ctx.hints.get(
                     "own_artifacts", set()) else None, "kind": kind}
        res.items.append(make_item("dependency", ctx.subproject_of(path), None, attrs,
                                   [ctx.evidence(path, line)], self, confidence))
        for gen, (pat, docs) in GENERATORS.items():
            if fnmatch.fnmatchcase(name, pat) and kind == "package":
                res.items.append(generated_contract_item(ctx, self, gen, docs, path, line))

    def _artifact(self, ctx, res, path, line, eco, name, version, packaging):
        res.items.append(make_item("artifact", ctx.subproject_of(path), None,
                                   {"ecosystem": eco, "name": name, "version": version,
                                    "packaging": packaging},
                                   [ctx.evidence(path, line)], self))

    # ---- maven -----------------------------------------------------------------------------
    def _pom(self, ctx, path, text, res, own, doc):
        doc = doc or configfmt.xml_with_lines(text)
        parse = "full" if doc.ok else "partial"
        root = doc.root
        if root is None:
            res.touch(path, "partial", doc.error)
            return
        props = {}
        pe = root.find("properties")
        if pe is not None:
            for c in pe:
                props[c.tag] = (c.text or "").strip()
        parent = root.find("parent")
        pg, pa, pv = (configfmt.xml_text(parent, "groupId"), configfmt.xml_text(parent, "artifactId"),
                      configfmt.xml_text(parent, "version")) if parent is not None else (None,) * 3
        g = configfmt.xml_text(root, "groupId") or pg
        a = configfmt.xml_text(root, "artifactId")
        v = configfmt.xml_text(root, "version") or pv
        props.update({"project.version": v or "", "project.groupId": g or "",
                      "project.parent.version": pv or "", "project.artifactId": a or ""})
        unresolved = False

        def resolve(s):
            nonlocal unresolved
            if s is None:
                return None, None
            out, frm = s, "literal"
            for _ in range(5):
                m = re.search(r"\$\{([^}]+)\}", out)
                if not m:
                    break
                val = props.get(m.group(1))
                if not val:
                    unresolved = True
                    return s, f"property:{m.group(1)}"
                out = out.replace(m.group(0), val)
                frm = f"property:{m.group(1)}"
            return out, frm

        if parent is not None and pa:
            pver, pfrom = resolve(pv)
            self._dep(ctx, res, path, doc.line(parent), "maven", f"{pg}:{pa}", pver, pfrom,
                      None, "parent")
        mods = root.find("modules")
        if mods is not None:
            for m in mods.findall("module"):
                if m.text and m.text.strip():
                    self._dep(ctx, res, path, doc.line(m), "maven", m.text.strip(), None, None,
                              None, "module", internal=True)
        dm = root.find("dependencyManagement")
        if dm is not None:
            for d in dm.iter("dependency"):
                if configfmt.xml_text(d, "scope") == "import":
                    name = f"{configfmt.xml_text(d, 'groupId')}:{configfmt.xml_text(d, 'artifactId')}"
                    ver, vfrom = resolve(configfmt.xml_text(d, "version"))
                    self._dep(ctx, res, path, doc.line(d), "maven", name, ver, vfrom, None,
                              "bom")
        deps = root.find("dependencies")
        if deps is not None:
            for d in deps.findall("dependency"):
                name = f"{configfmt.xml_text(d, 'groupId')}:{configfmt.xml_text(d, 'artifactId')}"
                ver, vfrom = resolve(configfmt.xml_text(d, "version"))
                if ver is None:
                    vfrom = "managed"
                self._dep(ctx, res, path, doc.line(d), "maven", name, ver, vfrom,
                          configfmt.xml_text(d, "scope") or "compile", "package",
                          internal=True if name in own else None)
        if g and a:
            packaging = configfmt.xml_text(root, "packaging") or "jar"
            plugins = root.find("build/plugins")  # pluginManagement alone does not repackage
            boot = plugins is not None and any(
                configfmt.xml_text(p, "artifactId") == "spring-boot-maven-plugin"
                for p in plugins.findall("plugin"))
            if boot:
                ctx.hints.setdefault("boot_repackage", set()).add(path)
            aline = doc.line(root.find("artifactId")) if root.find("artifactId") is not None \
                else doc.line(root)
            self._artifact(ctx, res, path, aline, "maven", f"{g}:{a}", resolve(v)[0], packaging)
        res.touch(path, "partial" if unresolved else parse, doc.error)

    # ---- nuget -----------------------------------------------------------------------------
    def _csproj(self, ctx, path, text, res, central):
        doc = configfmt.xml_with_lines(text)
        root = doc.root
        if root is None:
            res.touch(path, "partial", doc.error)
            return
        test = ("Microsoft.NET.Test.Sdk" in text or "<IsTestProject>true" in text)
        for el in root.iter("PackageReference"):
            name = el.get("Include") or el.get("Update")
            if not name:
                continue
            ver = el.get("Version") or configfmt.xml_text(el, "Version")
            vfrom = "literal" if ver else None
            if ver is None and name in central:
                ver, vfrom = central[name], "central"
            self._dep(ctx, res, path, doc.line(el), "nuget", name, ver, vfrom,
                      "test" if test else "compile", "package")
        for el in root.iter("ProjectReference"):
            inc = (el.get("Include") or "").replace("\\", "/")
            if inc:
                name = posixpath.splitext(posixpath.basename(inc))[0]
                self._dep(ctx, res, path, doc.line(el), "nuget", name, None, None,
                          "test" if test else "compile", "project-reference", internal=True)
        packable = (configfmt.xml_text(root.find("PropertyGroup"), "IsPackable") or "").lower()
        pid = None
        for pg in root.iter("PropertyGroup"):
            pid = pid or configfmt.xml_text(pg, "PackageId")
            packable = packable or (configfmt.xml_text(pg, "IsPackable") or "").lower()
        if pid or packable == "true":
            name = pid or posixpath.splitext(posixpath.basename(path))[0]
            ver = None
            for pg in root.iter("PropertyGroup"):
                ver = ver or configfmt.xml_text(pg, "Version") or configfmt.xml_text(
                    pg, "PackageVersion")
            ln = next((doc.line(e) for e in root.iter() if e.tag in ("PackageId", "IsPackable")),
                      doc.line(root))
            self._artifact(ctx, res, path, ln, "nuget", name, ver, "nupkg")
        res.touch(path, "full" if doc.ok else "partial", doc.error)

    def _props(self, ctx, path, text, res):
        doc = configfmt.xml_with_lines(text)
        res.touch(path, "full" if doc.ok else "partial", doc.error)

    def _packages_config(self, ctx, path, text, res):
        doc = configfmt.xml_with_lines(text)
        if doc.root is not None:
            for el in doc.root.iter("package"):
                if el.get("id"):
                    self._dep(ctx, res, path, doc.line(el), "nuget", el.get("id"),
                              el.get("version"), "literal" if el.get("version") else None,
                              "compile", "package")
        res.touch(path, "full" if doc.ok else "partial", doc.error)

    # ---- npm -------------------------------------------------------------------------------
    def _npm(self, ctx, path, text, res):
        r = configfmt.parse_jsonc(text)
        if not r.ok or not isinstance(r.data, dict):
            res.touch(path, "partial", r.error or "package.json root is not an object")
            return
        lines = {p: ln for p, _, ln in r.entries}
        data = r.data
        for section, scope_ in NPM_SCOPES:
            deps = data.get(section)
            if not isinstance(deps, dict):
                continue
            for name in sorted(deps):
                ver = deps[name]
                ver = ver if isinstance(ver, str) else None
                self._dep(ctx, res, path, lines.get((section, name), 1), "npm", name, ver,
                          "literal" if ver else None, scope_, "package")
        ws = data.get("workspaces")
        if isinstance(ws, dict):
            ws = ws.get("packages")
        if isinstance(ws, list):
            for i, w in enumerate(ws):
                if isinstance(w, str):
                    ln = lines.get(("workspaces", i)) or lines.get(("workspaces", "packages", i), 1)
                    self._dep(ctx, res, path, ln, "npm", w, None, None, None, "module",
                              internal=True)
        name = data.get("name")
        if isinstance(name, str) and name and (
                any(k in data for k in ("main", "exports", "module", "types"))
                or data.get("private") is not True):
            ver = data.get("version") if isinstance(data.get("version"), str) else None
            self._artifact(ctx, res, path, lines.get(("name",), 1), "npm", name, ver, "npm")
            ctx.hints.setdefault("own_artifacts", set()).add(name)
        res.touch(path, "full")

    # ---- gradle ----------------------------------------------------------------------------
    def _toml(self, ctx, path, text, res):
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError as e:
            res.touch(path, "partial", f"TOMLDecodeError: {e}")
            return
        versions = data.get("versions") or {}
        lines = ctx.lines(path)

        def line_of(alias: str) -> int:
            rx = re.compile(r"^\s*" + re.escape(alias) + r"\s*=")
            for i, ln in enumerate(lines, 1):
                if rx.match(ln):
                    return i
            return 1

        unresolved = False
        for alias, spec in sorted((data.get("libraries") or {}).items()):
            ver, vfrom, mod = None, None, None
            if isinstance(spec, str):
                parts = spec.split(":")
                mod = ":".join(parts[:2])
                if len(parts) > 2:
                    ver, vfrom = parts[2], "literal"
            elif isinstance(spec, dict):
                mod = spec.get("module") or (f"{spec.get('group')}:{spec.get('name')}"
                                             if spec.get("group") else None)
                v = spec.get("version")
                if isinstance(v, str):
                    ver, vfrom = v, "literal"
                elif isinstance(v, dict) and v.get("ref"):
                    ver, vfrom = versions.get(v["ref"]), f"catalog:{v['ref']}"
                    if ver is None:
                        unresolved = True
            if mod:
                self._dep(ctx, res, path, line_of(alias), "gradle", mod, ver, vfrom, None,
                          "package")
        res.touch(path, "partial" if unresolved else "full")

    def _gradle(self, ctx, path, text, res):
        for i, ln in enumerate(ctx.lines(path), 1):
            m = _GRADLE.match(ln)
            if not m:
                continue
            name = f"{m.group(3)}:{m.group(4)}"
            self._dep(ctx, res, path, i, "gradle", name, m.group(5),
                      "literal" if m.group(5) else None,
                      _GRADLE_SCOPE.get(m.group(1), "compile"),
                      "bom" if m.group(2) else "package", confidence="medium")
        res.touch(path, "partial")


def generated_contract_item(ctx: RepoContext, extractor, generator: str, docs_path: str | None,
                            file: str, line: int):
    """``api_contract`` for a spec generated at runtime (hook used by manifests + stack extractors).
    springdoc's path comes from ``springdoc.api-docs.path`` when configured."""
    if generator == "springdoc":
        configured = ctx.config.public_values("springdoc.api-docs.path")
        docs_path = configured.get("default") or docs_path
    attrs = {"format": "openapi-3", "file": None, "generator": generator, "generated": True,
             "docs_path": docs_path, "operations": None, "title": None, "version": None}
    return make_item("api_contract", ctx.subproject_of(file), generator, attrs,
                     [ctx.evidence(file, line)], extractor, "medium")
