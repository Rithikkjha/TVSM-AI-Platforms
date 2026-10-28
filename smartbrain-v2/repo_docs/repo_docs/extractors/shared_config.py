"""shared.config: config files of every stack -> ``config_key`` items + the repo config index.

Values are recorded only when ``config_classify`` allows them (rule 5); secrets are name-only.
The index (``ctx.config``) keeps raw values in memory for placeholder resolution by later
extractors (never written).
"""
from __future__ import annotations

import fnmatch
import posixpath
import re

from .. import config_classify as cc
from ..inventory_schema import make_item
from . import configfmt, syntax
from .base import ExtractResult, Extractor, RepoContext
from .config_index import ConfigDef

SAMPLE_ENV = (".env.example", ".env.sample", ".env.template", ".env.dist")


def scope(path: str) -> str | None:
    """Parser kind for a file in shared.config scope, else None."""
    name = posixpath.basename(path)
    low = name.lower()
    parts = path.split("/")[:-1]
    if fnmatch.fnmatch(name, "appsettings*.json") or name in ("local.settings.json", "host.json"):
        return "json"
    if low in ("web.config", "app.config"):
        return "xml"
    if re.fullmatch(r"(application|bootstrap)([-.].*)?\.(ya?ml)", name):
        return "yaml"
    if re.fullmatch(r"(application|bootstrap)([-.].*)?\.properties", name):
        return "properties"
    if name == ".env" or name.startswith(".env."):
        return "dotenv"
    if re.fullmatch(r"environment(\..+)?\.ts", name):
        return "script"
    if name == "config.js":
        return "script"
    if name == "config.json" and ("runtime-assets" in parts or "public" in parts):
        return "json"
    return None


def _flat_json(path: str, entries: list) -> list[tuple[str, object, int]]:
    """Leaves of a JSON doc as ("A:B:0:C", value, line)."""
    name = posixpath.basename(path)
    out = []
    for p, v, ln in entries:
        if isinstance(v, (dict, list)):
            continue
        keys = [str(x) for x in p]
        if name == "local.settings.json" and keys and keys[0] == "Values" and len(keys) > 1:
            keys = keys[1:]
        out.append((":".join(keys), v, ln))
    return out


def _flat_yaml(entries: list) -> list[tuple[str, object, int]]:
    out = []
    for p, v, ln in entries:
        if isinstance(v, (dict, list)):
            continue
        key = ""
        for x in p:
            key += f"[{x}]" if isinstance(x, int) else (("." if key else "") + str(x))
        out.append((key, v, ln))
    return out


def _script_entries(ctx: RepoContext, path: str) -> tuple[list, bool]:
    """``const env = {a: 'x'}`` / ``window.X = {...}`` / ``export default {...}`` literal members."""
    parsed = ctx.syntax(path)
    if parsed is None:
        return [], False
    out = []
    for n in syntax.walk(parsed.root):
        prefix = None
        obj = None
        if n.type == "variable_declarator":
            val = n.child_by_field_name("value")
            if val is not None and val.type == "object":
                prefix, obj = syntax.text(n.child_by_field_name("name")), val
        elif n.type == "assignment_expression":
            right = n.child_by_field_name("right")
            if right is not None and right.type == "object":
                left = syntax.text(n.child_by_field_name("left"))
                prefix, obj = re.sub(r"^(window|globalThis|self)\.", "", left), right
        elif n.type == "export_statement":
            val = n.child_by_field_name("value")
            if val is not None and val.type == "object":
                prefix, obj = "", val
        if obj is None:
            continue
        stack = [(obj, prefix)]
        while stack:
            o, pre = stack.pop()
            for pair in syntax.named_children(o):
                if pair.type != "pair":
                    continue
                k = pair.child_by_field_name("key")
                kv = syntax.decode_string(k, parsed.lang) if k is not None else None
                kname = kv if isinstance(kv, str) else syntax.text(k)
                full = f"{pre}.{kname}" if pre else kname
                v = pair.child_by_field_name("value")
                if v is None:
                    continue
                if v.type == "object":
                    stack.append((v, full))
                    continue
                val = syntax.value_of(v, parsed.lang)
                if isinstance(val, syntax.Ref) and val.name.startswith("process.env."):
                    val = "${" + val.name[len("process.env."):] + "}"
                elif not isinstance(val, (str, int, float, bool)) or isinstance(val, syntax.Template):
                    continue
                out.append((full, val, syntax.line(pair)))
    return sorted(out, key=lambda e: e[2]), parsed.has_error


class SharedConfig(Extractor):
    id = "shared.config"
    stacks = ()
    extractor_version = "0.1.0"

    def extract(self, ctx: RepoContext, subproject: str | None) -> ExtractResult:
        res = ExtractResult()
        # canonical key per subproject -> list of (ConfigDef, Classified, sample)
        groups: dict[tuple[str, str], list] = {}
        for path in ctx.paths(subproject, lambda e: scope(e["path"]) is not None):
            kind = scope(path)
            text = ctx.read_text(path)
            if text is None:
                res.touch(path, "partial", "unreadable")
                continue
            env = cc.env_from_filename(path)
            parse, error = "full", None
            entries: list[tuple[str, object, int]] = []
            profiles: list[str | None] = []
            if kind == "json":
                r = configfmt.parse_jsonc(text)
                if not r.ok:
                    parse, error = "partial", r.error
                entries = _flat_json(path, r.entries)
                profiles = [None] * len(entries)
            elif kind == "yaml":
                docs, ok, err = configfmt.yaml_with_lines(text)
                if not ok:
                    parse, error = "partial", err
                for d in docs:
                    flat = _flat_yaml(d.entries)
                    entries += flat
                    profiles += [d.profile] * len(flat)
            elif kind == "properties":
                r = configfmt.parse_properties(text)
                entries = r.entries
                profiles = [None] * len(entries)
            elif kind == "dotenv":
                r = configfmt.parse_dotenv(text)
                if not r.ok:
                    parse, error = "partial", r.error
                entries = r.entries
                profiles = [None] * len(entries)
            elif kind == "xml":
                doc = configfmt.xml_with_lines(text)
                if not doc.ok:
                    parse, error = "partial", doc.error
                if doc.root is not None:
                    for el in doc.root.iter("add"):
                        if el.get("key") is not None:
                            entries.append((el.get("key"), el.get("value"), doc.line(el)))
                        elif el.get("name") is not None:  # connectionStrings: name only
                            entries.append(("ConnectionStrings:" + el.get("name"), None,
                                            doc.line(el)))
                profiles = [None] * len(entries)
            else:  # script (.ts/.js): literal members only -> always partial
                entries, _err = _script_entries(ctx, path)
                profiles = [None] * len(entries)
                parse = "partial"
                if _err:
                    error = "tree-sitter: error nodes"
            sub = ctx.subproject_of(path)
            sample = posixpath.basename(path) in SAMPLE_ENV
            for (name, value, ln), prof in zip(entries, profiles):
                if not name:
                    continue
                e = prof or env
                canon, env_rule = cc.canonical_key(name)
                if not canon:
                    continue
                c = cc.classify(name, value, file=path)
                if kind == "dotenv":
                    pb = "env-file"
                else:
                    pb = cc.provided_by_for_file(path)
                if c.provided_by == "key-vault":
                    pb = "key-vault"
                d = ConfigDef(name, canon, e, None if sample else value, path, ln, sub, pb,
                              "env" if kind == "dotenv" or (
                                  posixpath.basename(path) == "local.settings.json"
                                  and ":" not in name) else "property")
                if not sample:
                    ctx.config.add(d)
                groups.setdefault((sub, canon), []).append((d, c, sample, env_rule, value))
            res.touch(path, parse, error)
        for (sub, canon), defs in sorted(groups.items()):
            res.items.append(self._item(ctx, sub, canon, defs))
        return res

    def _item(self, ctx: RepoContext, sub: str, canon: str, defs: list):
        defs = sorted(defs, key=lambda x: (x[0].file, x[0].line))
        first_d, first_c = defs[0][0], defs[0][1]
        values: dict[str, str] = {}
        secret = any(c.secret for _, c, *_ in defs)
        for d, c, sample, *_ in defs:
            if (not secret and not sample and c.record_value is not None
                    and d.env not in values):
                values[d.env] = c.record_value
        kinds = [c.value_kind for d, c, s, *_ in defs if not s]
        default_kind = next((c.value_kind for d, c, s, *_ in defs
                             if d.env == "default" and not s), kinds[0] if kinds else "hidden")
        if secret and default_kind != "reference":
            default_kind = "hidden"
        env_rule_mix = len({x[3] for x in defs}) > 1
        attrs = {
            "name": first_d.name, "canonical": canon, "reads": [],
            "defined_in": sorted({(d.file, d.env) for d, *_ in defs}),
            "values": values, "value_kind": default_kind,
            "secret": secret,
            "kv_ref": next((c.kv_ref for _, c, *_ in defs if c.kv_ref), None),
            "ref": next((c.ref for _, c, *_ in defs if c.ref), None),
            "provided_by": first_d.provided_by,
            "required": True if any(x[2] for x in defs) else None,
        }
        attrs["defined_in"] = [{"file": f, "env": e} for f, e in attrs["defined_in"]]
        ev = [ctx.evidence_masked(d.file, d.line, raw) if c.secret or s
              else ctx.evidence(d.file, d.line) for d, c, s, _r, raw in defs]
        return make_item("config_key", sub, canon, attrs, ev, self,
                         "medium" if env_rule_mix else "high")


def config_key_item(ctx: RepoContext, extractor, name: str, value, file: str, line: int,
                    env: str, provided_by: str):
    """config_key item for an env var defined outside config files (Dockerfile, compose, k8s,
    pipelines). The value goes through the classifier."""
    canon, _ = cc.canonical_key(name)
    c = cc.classify(name, value, file=file)
    attrs = {"name": name, "canonical": canon, "reads": [],
             "defined_in": [{"file": file, "env": env}],
             "values": {env: c.record_value} if c.record_value is not None else {},
             "value_kind": c.value_kind, "secret": c.secret, "kv_ref": c.kv_ref, "ref": c.ref,
             "provided_by": provided_by, "required": None}
    return make_item("config_key", ctx.subproject_of(file), canon, attrs,
                     [ctx.evidence_masked(file, line, value) if c.secret
                      else ctx.evidence(file, line)], extractor)
