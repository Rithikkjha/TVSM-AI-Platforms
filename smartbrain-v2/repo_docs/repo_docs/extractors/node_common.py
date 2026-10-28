"""Shared TS/JS analysis for ``node.backend`` and ``node.frontend`` (FEAT-004, plan item 5).

(The plan calls this module ``ts_common.py``; it is ``node_common.py`` so every node module shares
one prefix.)

Pieces:
- ``Project``: repo-wide module graph over non-skipped ``ts/tsx/js/jsx/mjs/cjs`` files (``.d.ts``
  excluded): ES imports (default/named/namespace), ``require`` (+ destructuring), re-exports
  (``export * from``, ``export {x} from``), CommonJS ``module.exports``/``exports.x``; resolution of
  relative specifiers, ``tsconfig*.json``/``jsconfig.json`` ``baseUrl``/``paths`` (``@/*`` ->
  ``src/*``), index files and extensions.
- ``Evaluator``: a small, side-effect free abstract interpreter over tree-sitter nodes. String
  values are ``SV`` part tuples (literal text, ``Env(VAR)``, ``Cfg(key)``, ``Param`` of an
  enclosing function, ``Key`` destructured from a runtime object, ``Dyn`` runtime holes). It
  follows identifiers, imports, object-literal members, enums, class fields/static getters,
  ``this.x`` assignments, URL-builder functions (``return `${base}/x/${id}```) and factory
  functions (one call hop each, depth-limited, cycle-safe). Nothing is executed.
- HTTP model (``HttpModel``): direct axios/fetch/got/Nest HttpService calls, ``axios.create``
  instances (also returned by a factory), one-level wrappers (object-literal methods, class
  methods/arrow fields, exported functions) resolved at their call sites.
- Config reads, TS schemas (class-validator, interfaces, type aliases, enums) and item helpers.
"""
from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass, field

from .. import config_classify as cc
from .. import pathnorm
from ..inventory_schema import make_item
from . import configfmt, syntax
from .base import ExtractResult, RepoContext

BASE_VERSION = "0.1.1"
VERSION = syntax.versioned(BASE_VERSION, "ts", "js")
SOURCE_LANGS = ("ts", "tsx", "js")
EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts")
HTTP_VERBS = ("get", "post", "put", "patch", "delete", "head", "options")
FN_TYPES = ("function_declaration", "function_expression", "arrow_function", "method_definition",
            "generator_function_declaration", "function", "generator_function")
MAX_DEPTH = 24
_TEST_RE = re.compile(r"(^|/)(__tests__|__mocks__|__test__|tests?|e2e|cypress|mocks?)/"
                      r"|\.(spec|test|e2e-spec|stories)\.[cm]?[jt]sx?$|(^|/)(jest|vitest)\."
                      r"|(^|/)setupTests\.")
_ENV_LIKE = re.compile(r"^(NEXT_PUBLIC_|REACT_APP_|VITE_|NEXT_)[A-Z0-9_]+$")
_UPPER = re.compile(r"^[A-Z][A-Z0-9_]*[A-Z0-9]$")
_CONFIGISH_OBJ = re.compile(r"(config|env|__ENV__|runtimeConfig|settings)\??$", re.I)


def is_source(path: str) -> bool:
    return syntax.lang_for_path(path) in SOURCE_LANGS


def is_test(entry_or_path) -> bool:
    if isinstance(entry_or_path, dict):
        if entry_or_path.get("class") == "test":
            return True
        path = entry_or_path["path"]
    else:
        path = entry_or_path
    return bool(_TEST_RE.search(path))


def key_of(node) -> tuple:
    return (node.start_byte, node.end_byte, node.type)


def unwrap(node):
    """Strip parentheses / ``as`` / ``!`` / ``satisfies`` / ``await`` / type assertions."""
    while node is not None and node.type in ("parenthesized_expression", "as_expression",
                                             "non_null_expression", "satisfies_expression",
                                             "await_expression", "type_assertion"):
        kids = syntax.named_children(node)
        if not kids:
            break
        node = kids[0] if node.type != "type_assertion" else kids[-1]
    return node


def args_of(call) -> list:
    a = call.child_by_field_name("arguments")
    return [c for c in syntax.named_children(a)] if a is not None else []


def callee_name(call) -> str:
    fn = unwrap(call.child_by_field_name("function") or call.child_by_field_name("constructor"))
    if fn is None:
        return ""
    if fn.type == "member_expression":
        return syntax.text(fn.child_by_field_name("property"))
    return syntax.text(fn)


# ---- abstract values ----------------------------------------------------------------------
@dataclass(frozen=True)
class Env:
    name: str
    default: str | None = None


@dataclass(frozen=True)
class Cfg:
    key: str


@dataclass(frozen=True)
class Param:
    name: str
    owner: tuple      # (module path, fn node key)


@dataclass(frozen=True)
class OptsParam:
    """HTTP method taken from a wrapper's request-options parameter (``fetch(url, init)``)."""
    name: str
    owner: tuple


@dataclass(frozen=True)
class Dyn:
    text: str


@dataclass(frozen=True)
class Key:
    """Property destructured / read from a runtime object (e.g. a JSON secret)."""
    name: str


@dataclass(frozen=True)
class SV:
    """String value: tuple of parts (str | Env | Cfg | Param | Dyn | Key)."""
    parts: tuple
    heuristic: bool = False

    def literal(self) -> str | None:
        return "".join(self.parts) if all(isinstance(p, str) for p in self.parts) else None

    def render(self) -> str:
        return "".join(p if isinstance(p, str) else "{}" for p in self.parts)


@dataclass(eq=False)
class Obj:
    mod: "Module"
    node: object
    scope: "Scope | None" = None


@dataclass(eq=False)
class Ns:
    mod: "Module"


@dataclass(eq=False)
class Fn:
    mod: "Module"
    node: object
    cls: "Cls | None" = None
    scope: "Scope | None" = None     # closure (factory parameters bound at creation)

    @property
    def key(self) -> tuple:
        return (self.mod.path, key_of(self.node))


@dataclass(eq=False)
class Cls:
    mod: "Module"
    node: object

    @property
    def name(self) -> str:
        return syntax.text(self.node.child_by_field_name("name"))


@dataclass(eq=False)
class Inst:
    cls: Cls


@dataclass(eq=False)
class EnumV:
    mod: "Module"
    node: object


@dataclass(frozen=True)
class Lib:
    pkg: str
    path: tuple = ()


@dataclass(eq=False)
class AxInst:
    base: SV | None
    mod: "Module"
    node: object
    name: str | None = None


@dataclass(frozen=True)
class Typed:
    """Constructor-injected / declared field whose only known fact is its type."""
    type: str


@dataclass(frozen=True)
class Router:
    """``express()`` app (``app=True``) or ``express.Router()``; identity = creating call."""
    mod: str
    key: tuple
    line: int
    app: bool = False


@dataclass(frozen=True)
class Global:
    name: str


@dataclass(frozen=True)
class Unknown:
    text: str = ""


UNKNOWN = Unknown()


def sv(*parts, heuristic=False) -> SV:
    out: list = []
    for p in parts:
        if isinstance(p, str) and out and isinstance(out[-1], str):
            out[-1] += p
        elif p != "":
            out.append(p)
    return SV(tuple(out), heuristic)


def concat(*vals) -> SV:
    parts, heur = [], False
    for v in vals:
        if isinstance(v, SV):
            parts += list(v.parts)
            heur |= v.heuristic
        elif isinstance(v, Param):
            parts.append(v)
        else:
            parts.append(Dyn(getattr(v, "text", "") or type(v).__name__))
    return sv(*parts, heuristic=heur)


def as_sv(v) -> SV | None:
    if isinstance(v, SV):
        return v
    if isinstance(v, Param):
        return SV((v,))
    return None


# ---- modules / project --------------------------------------------------------------------
class Module:
    def __init__(self, path: str, parsed):
        self.path = path
        self.parsed = parsed
        self.lang = parsed.lang
        self.root = parsed.root
        self.imports: dict[str, tuple] = {}   # local -> (kind, spec, name)
        self.exports: dict[str, tuple] = {}   # name -> ('local', n) | ('from', spec, n) | ('ns', spec) | ('node', node)
        self.stars: list[str] = []
        self.decls: dict[str, object] = {}    # top-level name -> declaring node
        self.default = None                   # node (expression / declaration)
        self.pkgs: dict[str, int] = {}        # external import spec -> first line
        self._index()

    def _add_import(self, spec: str, line: int) -> None:
        if not spec.startswith(".") and spec not in self.pkgs:
            self.pkgs[spec] = line

    def _decl(self, node) -> None:
        t = node.type
        if t in ("lexical_declaration", "variable_declaration"):
            for d in node.children:
                if d.type == "variable_declarator":
                    nm = d.child_by_field_name("name")
                    if nm is not None and nm.type == "identifier":
                        self.decls.setdefault(syntax.text(nm), d)
                    elif nm is not None and nm.type == "object_pattern":
                        val = unwrap(d.child_by_field_name("value"))
                        spec = _require_spec(val)
                        for nmn, alias in _pattern_names(nm):
                            if spec is not None:
                                self.imports[alias] = ("named", spec, nmn)
                            else:
                                self.decls.setdefault(alias, d)
                    if nm is not None and nm.type == "identifier":
                        spec = _require_spec(unwrap(d.child_by_field_name("value")))
                        if spec is not None:
                            self.imports[syntax.text(nm)] = ("require", spec, None)
                            self._add_import(spec, syntax.line(d))
                    elif nm is not None and nm.type == "object_pattern":
                        spec = _require_spec(unwrap(d.child_by_field_name("value")))
                        if spec is not None:
                            self._add_import(spec, syntax.line(d))
        elif t in ("function_declaration", "generator_function_declaration", "class_declaration",
                   "abstract_class_declaration", "enum_declaration", "interface_declaration",
                   "type_alias_declaration"):
            nm = node.child_by_field_name("name")
            if nm is not None:
                self.decls.setdefault(syntax.text(nm), node)

    def _index(self) -> None:
        for c in self.root.children:
            t = c.type
            if t == "import_statement":
                src = c.child_by_field_name("source")
                spec = syntax.decode_string(src, "ts") if src is not None else None
                if not isinstance(spec, str):
                    continue
                self._add_import(spec, syntax.line(c))
                for cl in c.children:
                    if cl.type != "import_clause":
                        continue
                    for x in cl.children:
                        if x.type == "identifier":
                            self.imports[syntax.text(x)] = ("default", spec, None)
                        elif x.type == "namespace_import":
                            ids = [y for y in x.children if y.type == "identifier"]
                            if ids:
                                self.imports[syntax.text(ids[0])] = ("namespace", spec, None)
                        elif x.type == "named_imports":
                            for s in x.children:
                                if s.type != "import_specifier":
                                    continue
                                nm = syntax.text(s.child_by_field_name("name"))
                                al = s.child_by_field_name("alias")
                                self.imports[syntax.text(al) if al is not None else nm] = \
                                    ("named", spec, nm)
            elif t == "export_statement":
                src = c.child_by_field_name("source")
                spec = syntax.decode_string(src, "ts") if src is not None else None
                decl = c.child_by_field_name("declaration")
                val = c.child_by_field_name("value")
                is_default = any(x.type == "default" for x in c.children)
                if isinstance(spec, str):
                    self._add_import(spec, syntax.line(c))
                    clause = next((x for x in c.children if x.type == "export_clause"), None)
                    nsx = next((x for x in c.children if x.type == "namespace_export"), None)
                    if clause is not None:
                        for s in clause.children:
                            if s.type == "export_specifier":
                                nm = syntax.text(s.child_by_field_name("name"))
                                al = s.child_by_field_name("alias")
                                self.exports[syntax.text(al) if al is not None else nm] = \
                                    ("from", spec, nm)
                    elif nsx is not None:
                        ids = [y for y in nsx.children if y.type == "identifier"]
                        if ids:
                            self.exports[syntax.text(ids[0])] = ("ns", spec)
                    else:
                        self.stars.append(spec)
                    continue
                if decl is not None:
                    self._decl(decl)
                    if is_default:
                        self.default = decl
                    for nm in _declared_names(decl):
                        self.exports.setdefault(nm, ("local", nm))
                    continue
                if val is not None and is_default:
                    self.default = val
                    continue
                clause = next((x for x in c.children if x.type == "export_clause"), None)
                if clause is not None:
                    for s in clause.children:
                        if s.type == "export_specifier":
                            nm = syntax.text(s.child_by_field_name("name"))
                            al = s.child_by_field_name("alias")
                            alias = syntax.text(al) if al is not None else nm
                            if alias == "default":
                                self.default = s.child_by_field_name("name")
                            else:
                                self.exports[alias] = ("local", nm)
            elif t == "expression_statement":
                e = syntax.named_children(c)
                e = e[0] if e else None
                if e is not None and e.type == "assignment_expression":
                    left = syntax.text(e.child_by_field_name("left"))
                    right = e.child_by_field_name("right")
                    if left == "module.exports":
                        self.default = right
                        if right is not None and right.type == "object":
                            for p in syntax.named_children(right):
                                if p.type == "shorthand_property_identifier":
                                    self.exports.setdefault(syntax.text(p), ("local", syntax.text(p)))
                                elif p.type == "pair":
                                    k = syntax.text(p.child_by_field_name("key")).strip("'\"")
                                    self.exports.setdefault(k, ("node", p.child_by_field_name("value")))
                    else:
                        m = re.fullmatch(r"(?:module\.)?exports\.([A-Za-z_$][\w$]*)", left)
                        if m:
                            self.exports[m.group(1)] = ("node", right)
                # require('x') side-effect imports
                for n in syntax.walk(c):
                    if n.type == "call_expression":
                        s = _require_spec(n)
                        if s:
                            self._add_import(s, syntax.line(n))
            else:
                self._decl(c)
                if t in ("lexical_declaration", "variable_declaration"):
                    for n in syntax.walk(c):
                        if n.type == "call_expression":
                            s = _require_spec(n)
                            if s:
                                self._add_import(s, syntax.line(n))

    def imports_pkg(self, *prefixes: str) -> int | None:
        """First line importing any package equal to / under one of ``prefixes``."""
        lines = [ln for spec, ln in self.pkgs.items()
                 if any(spec == p or spec.startswith(p + "/") for p in prefixes)]
        return min(lines) if lines else None


def _require_spec(node) -> str | None:
    if node is None or node.type != "call_expression":
        return None
    fn = node.child_by_field_name("function")
    if fn is None or syntax.text(fn) != "require":
        return None
    a = args_of(node)
    if not a:
        return None
    s = syntax.decode_string(a[0], "ts")
    return s if isinstance(s, str) else None


def _pattern_names(pat) -> list[tuple[str, str]]:
    """``{a, b: c, d = 1}`` -> [(a, a), (b, c), (d, d)]."""
    out = []
    for p in syntax.named_children(pat):
        if p.type == "shorthand_property_identifier_pattern":
            out.append((syntax.text(p), syntax.text(p)))
        elif p.type == "pair_pattern":
            k = syntax.text(p.child_by_field_name("key")).strip("'\"")
            v = p.child_by_field_name("value")
            if v is not None and v.type == "identifier":
                out.append((k, syntax.text(v)))
            elif v is not None and v.type == "assignment_pattern":
                left = v.child_by_field_name("left")
                out.append((k, syntax.text(left)))
        elif p.type == "object_assignment_pattern":
            left = p.child_by_field_name("left")
            out.append((syntax.text(left), syntax.text(left)))
    return out


def _declared_names(decl) -> list[str]:
    if decl.type in ("lexical_declaration", "variable_declaration"):
        out = []
        for d in decl.children:
            if d.type == "variable_declarator":
                nm = d.child_by_field_name("name")
                if nm is not None and nm.type == "identifier":
                    out.append(syntax.text(nm))
                elif nm is not None and nm.type == "object_pattern":
                    out += [a for _, a in _pattern_names(nm)]
        return out
    nm = decl.child_by_field_name("name")
    return [syntax.text(nm)] if nm is not None else []


class Project:
    """Repo-wide module graph (cached on ``ctx.symbols['node']``)."""

    def __init__(self, ctx: RepoContext):
        self.ctx = ctx
        self.entries = {e["path"]: e for e in ctx.files(None, lambda e: is_source(e["path"]))}
        self.all_paths = set(ctx.ledger_index)
        self._mods: dict[str, Module | None] = {}
        self._tsconfigs = self._load_tsconfigs()
        self.evaluator = Evaluator(self)
        self._types: dict[str, list] | None = None

    # ---- tsconfig ------------------------------------------------------------------------
    def _load_tsconfigs(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for p in sorted(self.ctx.paths(None, lambda e: re.fullmatch(
                r"(tsconfig[^/]*|jsconfig)\.json", posixpath.basename(e["path"])) is not None)):
            text = self.ctx.read_text(p)
            if text is None:
                continue
            r = configfmt.parse_jsonc(text)
            data = r.data if isinstance(r.data, dict) else {}
            out[p] = data
        return out

    def tsconfig_paths(self) -> list[str]:
        return sorted(self._tsconfigs)

    def _aliases(self, from_path: str) -> tuple[str | None, dict]:
        d = posixpath.dirname(from_path)
        while True:
            for name in ("tsconfig.json", "jsconfig.json"):
                cand = posixpath.join(d, name) if d else name
                if cand in self._tsconfigs:
                    data = self._tsconfigs[cand]
                    opts = dict(data.get("compilerOptions") or {})
                    ext = data.get("extends")
                    if isinstance(ext, str) and ext.startswith("."):
                        parent = posixpath.normpath(posixpath.join(d, ext))
                        pdata = self._tsconfigs.get(parent) or self._tsconfigs.get(parent + ".json")
                        if pdata:
                            popts = pdata.get("compilerOptions") or {}
                            for k in ("baseUrl", "paths"):
                                opts.setdefault(k, popts.get(k))
                    base = opts.get("baseUrl")
                    base_dir = posixpath.normpath(posixpath.join(d, base)) if isinstance(base, str) \
                        else (d or ".")
                    return base_dir, opts.get("paths") if isinstance(opts.get("paths"), dict) else {}
            if not d:
                return None, {}
            d = posixpath.dirname(d)

    def _candidates(self, base: str) -> str | None:
        base = posixpath.normpath(base)
        if base.startswith("./"):
            base = base[2:]
        cands = [base] + [base + e for e in EXTS] + [posixpath.join(base, "index" + e) for e in EXTS]
        stem, ext = posixpath.splitext(base)
        if ext in (".js", ".jsx", ".mjs", ".cjs"):
            cands += [stem + e for e in (".ts", ".tsx", ".mts", ".cts")]
        for c in cands:
            if c in self.entries:
                return c
        return None

    def resolve_spec(self, from_path: str, spec: str) -> str | None:
        if spec.startswith("."):
            return self._candidates(posixpath.join(posixpath.dirname(from_path), spec))
        base_dir, paths = self._aliases(from_path)
        for pat, targets in sorted((paths or {}).items(), key=lambda kv: -len(kv[0])):
            if not isinstance(targets, list):
                continue
            if pat.endswith("*"):
                if not spec.startswith(pat[:-1]):
                    continue
                rest = spec[len(pat) - 1:]
            elif spec != pat:
                continue
            else:
                rest = ""
            for t in targets:
                if not isinstance(t, str):
                    continue
                tgt = t[:-1] + rest if t.endswith("*") else t
                r = self._candidates(posixpath.join(base_dir or ".", tgt))
                if r:
                    return r
        if base_dir is not None:
            r = self._candidates(posixpath.join(base_dir, spec))
            if r:
                return r
        return None

    # ---- modules -------------------------------------------------------------------------
    def module(self, path: str) -> Module | None:
        if path not in self._mods:
            parsed = self.ctx.syntax(path) if path in self.entries else None
            self._mods[path] = Module(path, parsed) if parsed is not None else None
        return self._mods[path]

    def module_for_spec(self, from_path: str, spec: str) -> Module | None:
        p = self.resolve_spec(from_path, spec)
        return self.module(p) if p else None

    def paths_in(self, subproject: str | None, tests: bool = False) -> list[str]:
        return [e["path"] for e in self.ctx.files(subproject, lambda e: is_source(e["path"]))
                if tests or not is_test(e)]

    # ---- type index (schemas) ------------------------------------------------------------
    def types(self) -> dict[str, list]:
        if self._types is None:
            self._types = {}
            for p in sorted(self.entries):
                if is_test(self.entries[p]):
                    continue
                m = self.module(p)
                if m is None:
                    continue
                for td in syntax.type_decls(m.parsed):
                    if td.name:
                        self._types.setdefault(td.name, []).append((m, td))
        return self._types


def project(ctx: RepoContext) -> Project:
    p = ctx.symbols.get("node")
    if p is None:
        p = ctx.symbols["node"] = Project(ctx)
    return p


# ---- evaluator ----------------------------------------------------------------------------
@dataclass
class Scope:
    frames: dict = field(default_factory=dict)   # fn key -> {param name: value}
    this: object = None                          # Inst | Cls for ``this``


def fn_params(node, lang: str) -> list[str]:
    out = []
    for p in syntax.params_of(node, lang):
        nm = p.name
        if p.node is not None and p.node.type in ("required_parameter", "optional_parameter"):
            pat = p.node.child_by_field_name("pattern")
            if pat is not None and pat.type == "identifier":
                nm = syntax.text(pat)
        out.append(nm)
    return out


def enclosing_class(node):
    a = node.parent
    while a is not None:
        if a.type in ("class_declaration", "abstract_class_declaration", "class"):
            return a
        a = a.parent
    return None


def enclosing_fn(node):
    a = node.parent
    while a is not None:
        if a.type in FN_TYPES:
            return a
        a = a.parent
    return None


def _is_static(member) -> bool:
    return any(c.type == "static" for c in member.children)


def _class_members(cls_node):
    body = cls_node.child_by_field_name("body")
    return [c for c in body.children if c.is_named] if body is not None else []


def _member_name(m) -> str:
    nm = m.child_by_field_name("name") or m.child_by_field_name("property")
    return syntax.text(nm) if nm is not None else ""


class Evaluator:
    def __init__(self, proj: Project):
        self.p = proj
        self._cache: dict = {}
        self._active: set = set()
        self.depth = 0

    # ---- entry ---------------------------------------------------------------------------
    def eval(self, mod: Module, node, scope: Scope | None = None):
        if node is None:
            return UNKNOWN
        if self.depth > MAX_DEPTH:
            return Unknown(syntax.text(node)[:60])
        ck = (mod.path, key_of(node)) if not scope or (not scope.frames and scope.this is None) \
            else None
        if ck is not None and ck in self._cache:
            return self._cache[ck]
        act = (mod.path, key_of(node), id(scope) if scope else 0)
        if act in self._active:
            return Unknown(syntax.text(node)[:60])
        self._active.add(act)
        self.depth += 1
        try:
            v = self._eval(mod, node, scope or Scope())
        finally:
            self.depth -= 1
            self._active.discard(act)
        if ck is not None:
            self._cache[ck] = v
        return v

    def _eval(self, mod: Module, node, scope: Scope):
        t = node.type
        if t in ("parenthesized_expression", "as_expression", "non_null_expression",
                 "satisfies_expression", "await_expression", "type_assertion"):
            return self.eval(mod, unwrap(node), scope)
        if t in ("string", "template_string"):
            return self._string(mod, node, scope)
        if t == "number":
            return sv(syntax.text(node))
        if t in ("true", "false", "null", "undefined"):
            return Unknown(t)
        if t in ("identifier", "shorthand_property_identifier"):
            return self.lookup(mod, node, syntax.text(node), scope)
        if t == "this":
            return self._this(mod, node, scope)
        if t == "member_expression":
            return self._member_expr(mod, node, scope)
        if t == "subscript_expression":
            obj = node.child_by_field_name("object")
            idx = node.child_by_field_name("index")
            if syntax.text(obj).replace("?.", ".") in ("process.env", "import.meta.env"):
                s = syntax.decode_string(idx, "ts") if idx is not None else None
                return sv(Env(s)) if isinstance(s, str) else Unknown(syntax.text(node))
            iv = self.eval(mod, idx, scope)
            lit = iv.literal() if isinstance(iv, SV) else None
            if lit is not None:
                return self.member(self.eval(mod, obj, scope), lit, mod, node)
            return Unknown(syntax.text(node)[:60])
        if t == "binary_expression":
            op = syntax.text(node.child_by_field_name("operator"))
            left = node.child_by_field_name("left")
            right = node.child_by_field_name("right")
            if op == "+":
                return concat(self.eval(mod, left, scope), self.eval(mod, right, scope))
            if op in ("||", "??"):
                lv = self.eval(mod, left, scope)
                rv = self.eval(mod, right, scope)
                if isinstance(lv, SV) and lv.parts and not all(isinstance(p, Dyn) for p in lv.parts):
                    lit = rv.literal() if isinstance(rv, SV) else None
                    if lit and len(lv.parts) == 1 and isinstance(lv.parts[0], Env) \
                            and lv.parts[0].default is None:
                        return SV((Env(lv.parts[0].name, lit),), lv.heuristic)
                    return lv
                if isinstance(lv, (AxInst, Obj, Fn, Inst, Cls, Ns, EnumV, Router)):
                    return lv
                return rv
            return Unknown(syntax.text(node)[:60])
        if t in ("arrow_function", "function_expression", "function", "generator_function"):
            return Fn(mod, node, self._cls_of(mod, node), scope if scope.frames else None)
        if t == "object":
            return Obj(mod, node, scope)
        if t in ("class", "class_declaration", "abstract_class_declaration"):
            return Cls(mod, node)
        if t == "call_expression":
            return self._call(mod, node, scope)
        if t == "new_expression":
            ctor = self.eval(mod, node.child_by_field_name("constructor"), scope)
            if isinstance(ctor, Cls):
                return Inst(ctor)
            if isinstance(ctor, Lib):
                return Lib(ctor.pkg, ctor.path + ("new",))
            return Unknown(syntax.text(node)[:60])
        if t == "ternary_expression":
            a = self.eval(mod, node.child_by_field_name("consequence"), scope)
            b = self.eval(mod, node.child_by_field_name("alternative"), scope)
            if isinstance(a, SV) and isinstance(b, SV) and a.parts == b.parts:
                return a
            for v in (a, b):
                if isinstance(v, (AxInst, Router)):
                    return v
            return Unknown(syntax.text(node)[:60])
        return Unknown(syntax.text(node)[:60])

    def _string(self, mod, node, scope) -> SV:
        if node.type == "string":
            s = syntax.decode_string(node, "ts")
            return sv(s if isinstance(s, str) else "")
        parts = []
        for c in node.children:
            if c.type in ("string_fragment", "template_chars"):
                parts.append(syntax.text(c))
            elif c.type == "escape_sequence":
                parts.append(syntax.unescape(syntax.text(c), "ts"))
            elif c.type == "template_substitution":
                inner = syntax.named_children(c)
                v = self.eval(mod, inner[0], scope) if inner else UNKNOWN
                if isinstance(v, SV):
                    parts += list(v.parts)
                elif isinstance(v, Param):
                    parts.append(v)
                else:
                    parts.append(Dyn(syntax.text(inner[0]) if inner else ""))
        return sv(*parts)

    # ---- identifiers ---------------------------------------------------------------------
    def lookup(self, mod: Module, node, name: str, scope: Scope):
        a = node.parent
        pos = node.start_byte
        while a is not None:
            if a.type in FN_TYPES:
                fk = (mod.path, key_of(a))
                params = fn_params(a, mod.lang)
                if name in params:
                    frame = scope.frames.get(fk)
                    if frame is not None and name in frame:
                        return frame[name]
                    return Param(name, fk)
                for p in syntax.params_of(a, mod.lang):
                    pn = p.node
                    pat = pn.child_by_field_name("pattern") if pn is not None and pn.type in (
                        "required_parameter", "optional_parameter") else pn
                    if pat is not None and pat.type == "object_pattern" and \
                            name in [al for _, al in _pattern_names(pat)]:
                        return Dyn(name)
            if a.type in ("statement_block", "program", "class_body", "switch_body"):
                v = self._block_decl(mod, a, name, pos, scope)
                if v is not None:
                    return v
            a = a.parent
        if name in mod.imports:
            return self._import(mod, name)
        if name in mod.decls:
            return self._decl_value(mod, mod.decls[name], name, Scope())
        if name in ("process", "window", "globalThis", "self", "document", "console", "JSON",
                    "fetch", "require", "module", "exports", "Promise", "Object", "Math"):
            return Global(name)
        return Unknown(name)

    def _block_decl(self, mod, block, name, pos, scope):
        best = None
        for st in block.children:
            t = st.type
            if t == "export_statement":
                st = st.child_by_field_name("declaration") or st
                t = st.type
            if t in ("lexical_declaration", "variable_declaration"):
                for d in st.children:
                    if d.type != "variable_declarator":
                        continue
                    nm = d.child_by_field_name("name")
                    if nm is None:
                        continue
                    if nm.type == "identifier" and syntax.text(nm) == name:
                        if d.start_byte <= pos or best is None:
                            best = d
                    elif nm.type in ("object_pattern",) and \
                            name in [al for _, al in _pattern_names(nm)]:
                        if d.start_byte <= pos or best is None:
                            best = d
            elif t in ("function_declaration", "generator_function_declaration",
                       "class_declaration", "abstract_class_declaration", "enum_declaration"):
                nm = st.child_by_field_name("name")
                if nm is not None and syntax.text(nm) == name:
                    return self._decl_value(mod, st, name, scope)
        if best is None:
            return None
        return self._decl_value(mod, best, name, scope, block)

    def _decl_value(self, mod, d, name, scope, block=None):
        t = d.type
        if t in ("function_declaration", "generator_function_declaration"):
            return Fn(mod, d, self._cls_of(mod, d))
        if t in ("class_declaration", "abstract_class_declaration"):
            return Cls(mod, d)
        if t == "enum_declaration":
            return EnumV(mod, d)
        if t != "variable_declarator":
            return Unknown(name)
        nm = d.child_by_field_name("name")
        val = d.child_by_field_name("value")
        if nm is not None and nm.type == "object_pattern":
            src = None
            for k, al in _pattern_names(nm):
                if al == name:
                    src = k
            spec = _require_spec(unwrap(val))
            if spec is not None:
                return self._import_named(mod, spec, src or name)
            base = self.eval(mod, val, scope) if val is not None else UNKNOWN
            if isinstance(base, Global) and base.name == "process":
                return UNKNOWN
            if syntax.text(val).replace("?.", ".") in ("process.env", "import.meta.env"):
                return sv(Env(src or name))
            m = self.member(base, src or name, mod, d)
            if isinstance(m, Unknown):
                return sv(Key(src or name))
            return m
        if val is None:
            # ``let x;`` + later ``x = expr`` in the same block
            blk = block if block is not None else d.parent.parent if d.parent is not None else None
            if blk is not None:
                for n in syntax.walk(blk):
                    if n.type == "assignment_expression" and \
                            syntax.text(n.child_by_field_name("left")) == name:
                        return self.eval(mod, n.child_by_field_name("right"), scope)
            ty = d.child_by_field_name("type")
            return Typed(syntax.text(ty).lstrip(": ").strip()) if ty is not None else Unknown(name)
        v = self.eval(mod, val, scope)
        if isinstance(v, Unknown) or (isinstance(v, Unknown) and v.text in ("null",)):
            blk = block if block is not None else None
            if blk is not None:
                for n in syntax.walk(blk):
                    if n.type == "assignment_expression" and \
                            syntax.text(n.child_by_field_name("left")) == name:
                        v2 = self.eval(mod, n.child_by_field_name("right"), scope)
                        if not isinstance(v2, Unknown):
                            return v2
        if isinstance(v, AxInst) and v.name is None:
            v.name = name
        return v

    # ---- imports -------------------------------------------------------------------------
    def _import(self, mod: Module, local: str):
        kind, spec, name = mod.imports[local]
        target = self.p.module_for_spec(mod.path, spec)
        if target is None:
            if spec.startswith("."):
                return Unknown(local)
            if kind in ("default", "require"):
                return Lib(spec)
            if kind == "namespace":
                return Lib(spec)
            return Lib(spec, (name,))
        if kind == "namespace":
            return Ns(target)
        if kind == "require":
            return self._require_value(target)
        if kind == "default":
            return self.default_of(target)
        return self.export_of(target, name)

    def _import_named(self, mod, spec, name):
        target = self.p.module_for_spec(mod.path, spec)
        if target is None:
            return Lib(spec, (name,)) if not spec.startswith(".") else Unknown(name)
        return self.export_of(target, name)

    def _require_value(self, target: Module):
        if target.default is not None:
            return self.eval(target, target.default)
        return Ns(target)

    def default_of(self, target: Module, depth: int = 0):
        if target.default is None:
            if "default" in target.exports:
                return self.export_of(target, "default", depth + 1)
            return Ns(target)
        d = target.default
        if d.type in ("function_declaration", "class_declaration", "abstract_class_declaration",
                      "generator_function_declaration"):
            return self._decl_value(target, d, "", Scope())
        if d.type in ("lexical_declaration", "variable_declaration"):
            return Unknown("default")
        return self.eval(target, d)

    def export_of(self, target: Module, name: str, depth: int = 0):
        if depth > 8:
            return Unknown(name)
        ex = target.exports.get(name)
        if ex is not None:
            if ex[0] == "local":
                if ex[1] in target.decls:
                    return self._decl_value(target, target.decls[ex[1]], ex[1], Scope())
                if ex[1] in target.imports:
                    return self._import(target, ex[1])
                return Unknown(name)
            if ex[0] == "from":
                t2 = self.p.module_for_spec(target.path, ex[1])
                if t2 is None:
                    return Lib(ex[1], (ex[2],)) if not ex[1].startswith(".") else Unknown(name)
                if ex[2] == "default":
                    return self.default_of(t2, depth + 1)
                return self.export_of(t2, ex[2], depth + 1)
            if ex[0] == "ns":
                t2 = self.p.module_for_spec(target.path, ex[1])
                return Ns(t2) if t2 is not None else Unknown(name)
            if ex[0] == "node":
                return self.eval(target, ex[1])
        for spec in target.stars:
            t2 = self.p.module_for_spec(target.path, spec)
            if t2 is not None and (name in t2.exports or t2.stars):
                v = self.export_of(t2, name, depth + 1)
                if not isinstance(v, Unknown):
                    return v
        if name in target.decls and target.default is None and not target.exports:
            return self._decl_value(target, target.decls[name], name, Scope())
        if target.default is not None and target.default.type == "object":
            return self.member(self.eval(target, target.default), name, target, target.default)
        return Unknown(name)

    # ---- members -------------------------------------------------------------------------
    def _cls_of(self, mod, node):
        c = enclosing_class(node)
        return Cls(mod, c) if c is not None else None

    def _this(self, mod, node, scope):
        if scope.this is not None:
            return scope.this
        c = enclosing_class(node)
        if c is None:
            return Unknown("this")
        fn = enclosing_fn(node)
        while fn is not None and fn.type == "arrow_function":
            fn = enclosing_fn(fn)
        if fn is not None and fn.type == "method_definition" and _is_static(fn):
            return Cls(mod, c)
        return Inst(Cls(mod, c))

    def _member_expr(self, mod, node, scope):
        obj = node.child_by_field_name("object")
        prop = syntax.text(node.child_by_field_name("property"))
        otext = syntax.text(obj).replace("?.", ".").replace(" ", "")
        if otext in ("process.env", "import.meta.env"):
            return sv(Env(prop))
        if otext == "import.meta":
            return Unknown("import.meta." + prop)
        ov = self.eval(mod, obj, scope)
        v = self.member(ov, prop, mod, node, scope)
        if isinstance(v, (Unknown, Typed)) and _UPPER.match(prop):
            if _ENV_LIKE.match(prop) or _CONFIGISH_OBJ.search(otext):
                return SV((Env(prop),), heuristic=True)
            if isinstance(ov, (SV, Dyn, Key, Unknown, Typed)) and not isinstance(ov, Global):
                return sv(Key(prop))
        return v

    def member(self, ov, prop: str, mod=None, node=None, scope: Scope | None = None):
        if isinstance(ov, Ns):
            return self.export_of(ov.mod, prop)
        if isinstance(ov, Obj):
            return self._obj_member(ov, prop)
        if isinstance(ov, Inst):
            return self._inst_member(ov.cls, prop, set())
        if isinstance(ov, Cls):
            return self._static_member(ov, prop)
        if isinstance(ov, EnumV):
            body = ov.node.child_by_field_name("body")
            for c in syntax.named_children(body) if body is not None else []:
                if c.type == "enum_assignment" and syntax.text(c.child_by_field_name("name")) == prop:
                    return self.eval(ov.mod, c.child_by_field_name("value"))
                if c.type == "property_identifier" and syntax.text(c) == prop:
                    return sv(prop)
            return Unknown(prop)
        if isinstance(ov, Lib):
            return Lib(ov.pkg, ov.path + (prop,))
        if isinstance(ov, Global):
            if ov.name in ("window", "globalThis", "self"):
                return Global(ov.name + "." + prop)
            return Unknown(ov.name + "." + prop)
        return Unknown(prop)

    def _obj_member(self, ov: Obj, prop: str):
        for c in syntax.named_children(ov.node):
            if c.type == "pair":
                k = c.child_by_field_name("key")
                kv = syntax.decode_string(k, "ts") if k is not None and k.type == "string" \
                    else syntax.text(k)
                if kv == prop:
                    return self.eval(ov.mod, c.child_by_field_name("value"), ov.scope)
            elif c.type == "shorthand_property_identifier" and syntax.text(c) == prop:
                return self.lookup(ov.mod, c, prop, ov.scope or Scope())
            elif c.type == "method_definition" and _member_name(c) == prop:
                return Fn(ov.mod, c, None, ov.scope if ov.scope and ov.scope.frames else None)
        return Unknown(prop)

    def _base_class(self, cls: Cls):
        for c in cls.node.children:
            if c.type == "class_heritage":
                for ext in syntax.walk(c):
                    if ext.type == "extends_clause":
                        val = ext.child_by_field_name("value") or next(
                            iter(syntax.named_children(ext)), None)
                        if val is not None:
                            v = self.eval(cls.mod, val)
                            if isinstance(v, Cls):
                                return v
        return None

    def _inst_member(self, cls: Cls, prop: str, seen: set):
        if cls.name in seen or len(seen) > 5:
            return Unknown(prop)
        seen = seen | {cls.name}
        typed = None
        for m in _class_members(cls.node):
            if _member_name(m) != prop or _is_static(m):
                continue
            if m.type in ("public_field_definition", "field_definition"):
                val = m.child_by_field_name("value")
                if val is not None:
                    return self.eval(cls.mod, val, Scope(this=Inst(cls)))
                ty = m.child_by_field_name("type")
                typed = Typed(syntax.text(ty).lstrip(": ").strip()) if ty is not None else None
            elif m.type == "method_definition":
                return Fn(cls.mod, m, cls)
        # constructor parameter properties (``private readonly http: HttpService``)
        for m in _class_members(cls.node):
            if m.type == "method_definition" and _member_name(m) == "constructor":
                for p in syntax.params_of(m, cls.mod.lang):
                    if p.name == prop or (p.node is not None and syntax.text(
                            p.node.child_by_field_name("pattern")) == prop):
                        if p.modifiers or any(c.type in ("accessibility_modifier", "readonly")
                                              for c in p.node.children):
                            return Typed(p.type or "")
        # ``this.prop = expr`` assignments in methods (constructor first)
        assigns = []
        for m in _class_members(cls.node):
            if m.type != "method_definition":
                continue
            body = m.child_by_field_name("body")
            if body is None:
                continue
            for n in syntax.walk(body):
                if n.type == "assignment_expression":
                    left = syntax.text(n.child_by_field_name("left")).replace("?.", ".")
                    if left == "this." + prop:
                        assigns.append((0 if _member_name(m) == "constructor" else 1, n))
        for _, n in sorted(assigns, key=lambda x: (x[0], x[1].start_byte)):
            v = self.eval(cls.mod, n.child_by_field_name("right"), Scope(this=Inst(cls)))
            if not isinstance(v, Unknown):
                return v
        base = self._base_class(cls)
        if base is not None:
            v = self._inst_member(base, prop, seen)
            if not isinstance(v, Unknown):
                return v
        return typed or Unknown(prop)

    def _static_member(self, cls: Cls, prop: str):
        for m in _class_members(cls.node):
            if _member_name(m) != prop:
                continue
            if m.type in ("public_field_definition", "field_definition"):
                val = m.child_by_field_name("value")
                if val is not None:
                    return self.eval(cls.mod, val, Scope(this=cls))
            elif m.type == "method_definition":
                if any(c.type == "get" for c in m.children):
                    return self.call_fn(Fn(cls.mod, m, cls), [], cls.mod, Scope(), this=cls)
                return Fn(cls.mod, m, cls)
        base = self._base_class(cls)
        return self._static_member(base, prop) if base is not None else Unknown(prop)

    # ---- calls ---------------------------------------------------------------------------
    def _call(self, mod, node, scope):
        fn = unwrap(node.child_by_field_name("function"))
        args = args_of(node)
        spec = _require_spec(node)
        if spec is not None:
            target = self.p.module_for_spec(mod.path, spec)
            if target is None:
                return Lib(spec) if not spec.startswith(".") else Unknown(spec)
            return self._require_value(target)
        if fn is not None and fn.type == "member_expression":
            prop = syntax.text(fn.child_by_field_name("property"))
            obj = fn.child_by_field_name("object")
            if prop in ("get", "getOrThrow") and args and re.search(
                    r"config(Service)?$", syntax.text(obj).replace("?.", "."), re.I):
                k = syntax.decode_string(args[0], "ts")
                if isinstance(k, str):
                    return sv(Cfg(k))
            if prop == "bind":
                return self.eval(mod, obj, scope)
            if prop in ("replace", "replaceAll", "trim", "trimEnd", "trimStart", "toString"):
                ov = self.eval(mod, obj, scope)   # trailing-slash cleanup keeps the value's identity
                if isinstance(ov, (SV, Param)):
                    return ov
        cv = self.eval(mod, fn, scope)
        if isinstance(cv, Lib):
            if cv.pkg == "axios" and cv.path in (("create",), ("default", "create")):
                base = None
                if args:
                    cfg = self.eval(mod, args[0], scope)
                    if isinstance(cfg, Obj):
                        base = as_sv(self._obj_member(cfg, "baseURL"))
                return AxInst(base, mod, node)
            if cv.pkg == "express" and cv.path == ():
                return Router(mod.path, key_of(node), syntax.line(node), app=True)
            if cv.pkg == "express" and cv.path == ("Router",):
                return Router(mod.path, key_of(node), syntax.line(node))
            return Lib(cv.pkg, cv.path + ("()",))
        if isinstance(cv, Fn):
            return self.call_fn(cv, args, mod, scope)
        if isinstance(cv, Unknown) and fn is not None and fn.type == "member_expression" and \
                syntax.text(fn.child_by_field_name("property")) == "Router":
            # require('express').Router()
            o = self.eval(mod, fn.child_by_field_name("object"), scope)
            if isinstance(o, Lib) and o.pkg == "express":
                return Router(mod.path, key_of(node), syntax.line(node))
        return Unknown(syntax.text(node)[:60])

    def call_fn(self, fnv: Fn, arg_nodes: list, caller_mod, caller_scope: Scope, this=None):
        node = fnv.node
        params = fn_params(node, fnv.mod.lang)
        frame = {}
        for i, pn in enumerate(params):
            if i < len(arg_nodes):
                frame[pn] = self.eval(caller_mod, arg_nodes[i], caller_scope)
        fk = (fnv.mod.path, key_of(node))
        outer = fnv.scope.frames if fnv.scope is not None else (
            caller_scope.frames if caller_scope else {})
        sc = Scope(frames={**outer, fk: frame},
                   this=this if this is not None else (caller_scope.this if fnv.cls is None else None))
        body = node.child_by_field_name("body")
        if body is None:
            return UNKNOWN
        if body.type != "statement_block":
            return self.eval(fnv.mod, body, sc)
        first = UNKNOWN
        for st in _returns(body):
            kids = syntax.named_children(st)
            if not kids:
                continue
            v = self.eval(fnv.mod, kids[0], sc)
            if isinstance(v, (AxInst, SV, Router)) and not (isinstance(v, SV) and all(
                    isinstance(p, Dyn) for p in v.parts)):
                return v
            if isinstance(first, Unknown):
                first = v
        return first


def _returns(body) -> list:
    """Return statements of a function body (nested functions excluded)."""
    out, stack = [], [body]
    while stack:
        n = stack.pop()
        for c in reversed(n.children):
            if c.type in FN_TYPES or c.type == "class_declaration":
                continue
            if c.type == "return_statement":
                out.append(c)
            elif c.child_count:
                stack.append(c)
    return sorted(out, key=lambda n: n.start_byte)


# ---- URL values -> call attributes --------------------------------------------------------
def url_attrs(ctx: RepoContext, value: SV, subproject: str | None) -> dict | None:
    """``base_url_source``/``base_url_values``/``path_template``/``query_params`` from a URL value.
    None when nothing useful is known (unknown base and no literal path segment)."""
    parts = list(value.parts)
    source, values, hint = "unknown", {}, None
    if parts and isinstance(parts[0], (Env, Cfg)):
        p0 = parts.pop(0)
        if isinstance(p0, Env):
            source = f"env:{p0.name}"
            values = dict(ctx.config.public_values(p0.name, subproject))
            if p0.default and "code-default" not in values:
                c = cc.classify(p0.name, p0.default)
                if c.record_value is not None and not c.secret and re.match(r"https?://",
                                                                            c.record_value):
                    values["code-default"] = c.record_value
        else:
            source = f"config:{p0.key}"
            values = dict(ctx.config.public_values(p0.key, subproject))
    rest = "".join(p if isinstance(p, str) else "{}" for p in parts)
    if source == "unknown":
        m = re.match(r"^([a-z][a-z0-9+.\-]*://[^/?#{}]+)", rest, re.I)
        if m:
            base = m.group(1)
            c = cc.classify("url", base)
            if c.secret or c.record_value is None:
                return None
            source, values = "literal", {"default": c.record_value}
            rest = rest[m.end():]
            hint = base.split("://", 1)[1]
    base, path, query = pathnorm.split_url(rest if rest else "/")
    if base and base.startswith("{"):
        path = base + path    # a leading runtime hole stays part of the path
    norm = pathnorm.normalize(path or "/")
    has_literal = any(s.replace("{}", "") for s in norm.split("/"))
    if not has_literal and not (source != "unknown" and norm == "/"):
        return None     # only runtime holes: phase 3 territory
    return {"base_url_source": source, "base_url_values": values, "path_template": norm,
            "query_params": [q for q in query if re.fullmatch(r"[\w.\-\[\]]+", q)],
            "target_hint": hint}


# ---- HTTP model ---------------------------------------------------------------------------
@dataclass
class Prim:
    mod: Module
    node: object              # call node
    client: str
    client_name: str | None
    method: object            # str | Param | None
    url: object               # value
    type_node: object = None


@dataclass
class Wrapper:
    fn_key: tuple
    mod: Module
    fn_node: object
    params: list
    prim: Prim
    url: SV
    name: str


@dataclass
class Call:
    """One resolved HTTP call (direct or through a wrapper)."""
    mod: Module
    node: object
    client: str
    client_name: str | None
    method: str | None
    url: SV
    raw: str
    response: str | None
    request: str | None
    via: str | None           # "file:line" of the wrapper
    heuristic: bool


class HttpModel:
    def __init__(self, proj: Project):
        self.p = proj
        self.ev = proj.evaluator
        self._prims: dict[str, list[Prim]] = {}
        self.wrappers: dict[tuple, Wrapper] | None = None
        self.wrapper_names: set[str] = set()
        self.nest_base: SV | None = None

    def prims(self, mod: Module) -> list[Prim]:
        if mod.path in self._prims:
            return self._prims[mod.path]
        out = []
        txt = self.p.ctx.read_text(mod.path) or ""
        if not re.search(r"axios|fetch|got|http|Http|request|\.get\(|\.post\(", txt):
            self._prims[mod.path] = out
            return out
        for n in syntax.walk(mod.root):
            if n.type != "call_expression":
                continue
            pr = self._prim(mod, n)
            if pr is not None:
                out.append(pr)
        self._prims[mod.path] = out
        return out

    def _prim(self, mod, n) -> Prim | None:
        fn = unwrap(n.child_by_field_name("function"))
        if fn is None:
            return None
        args = args_of(n)
        targs = n.child_by_field_name("type_arguments")
        ev = self.ev
        if fn.type == "member_expression":
            prop = syntax.text(fn.child_by_field_name("property"))
            if prop not in HTTP_VERBS + ("request",):
                return None
            ov = ev.eval(mod, fn.child_by_field_name("object"))
            client, cname, base = None, None, None
            if isinstance(ov, Lib) and ov.pkg in ("axios",) and ov.path in ((), ("default",)):
                client = "axios"
            elif isinstance(ov, AxInst):
                client, cname, base = "axios", ov.name, ov.base
            elif isinstance(ov, Lib) and ov.pkg == "got" and ov.path == ():
                client = "got"
            elif isinstance(ov, Typed) and "HttpService" in ov.type:
                client, base = "nest-httpservice", self.nest_base
            elif isinstance(ov, Typed) and re.search(r"\bHttpClient\b", ov.type):
                client = "httpclient"     # Angular HttpClient
            elif isinstance(ov, Lib) and ov.pkg == "@nestjs/axios":
                client = "nest-httpservice"
            if client is None:
                return None
            if prop == "request":
                if not args:
                    return None
                cfg = ev.eval(mod, args[0])
                if not isinstance(cfg, Obj):
                    return None
                url = ev._obj_member(cfg, "url")
                b2 = as_sv(ev._obj_member(cfg, "baseURL"))
                mv = ev._obj_member(cfg, "method")
                method = mv.literal().upper() if isinstance(mv, SV) and mv.literal() else None
                url = _join_base(b2 or base, url)
                return Prim(mod, n, client, cname, method, url, targs)
            if not args:
                return None
            url = _join_base(base, ev.eval(mod, args[0]))
            return Prim(mod, n, client, cname, prop.upper(), url, targs)
        cv = ev.eval(mod, fn)
        if isinstance(cv, Global) and cv.name == "fetch" or (
                isinstance(cv, Lib) and cv.pkg in ("node-fetch", "cross-fetch", "isomorphic-fetch")
                and cv.path in ((), ("default",))):
            if not args:
                return None
            return Prim(mod, n, "fetch", None, self._opts_method(mod, args[1:2]),
                        ev.eval(mod, args[0]), targs)
        if (isinstance(cv, Lib) and cv.pkg in ("axios", "got") and cv.path in ((), ("default",))) \
                or isinstance(cv, AxInst):
            if not args:
                return None
            client = "got" if isinstance(cv, Lib) and cv.pkg == "got" else "axios"
            base = cv.base if isinstance(cv, AxInst) else None
            first = ev.eval(mod, args[0])
            if isinstance(first, Obj):
                url = ev._obj_member(first, "url")
                mv = ev._obj_member(first, "method")
                b2 = as_sv(ev._obj_member(first, "baseURL"))
                method = mv.literal().upper() if isinstance(mv, SV) and mv.literal() else None
                return Prim(mod, n, client, getattr(cv, "name", None), method,
                            _join_base(b2 or base, url), targs)
            return Prim(mod, n, client, getattr(cv, "name", None),
                        self._opts_method(mod, args[1:2]), _join_base(base, first), targs)
        return None

    def _opts_method(self, mod, opts_nodes):
        """HTTP method of a fetch/axios(url, opts) call: literal ``method``, GET when no options
        or no ``method`` key, ``Param`` when the options are a wrapper parameter (or spread one),
        None when dynamic."""
        if not opts_nodes:
            return "GET"
        o = self.ev.eval(mod, opts_nodes[0])
        if isinstance(o, Param):
            return OptsParam(o.name, o.owner)
        if not isinstance(o, Obj):
            return None
        mv = self.ev._obj_member(o, "method")
        lit = mv.literal() if isinstance(mv, SV) else None
        if lit:
            return lit.upper()
        if not (isinstance(mv, Unknown) and mv.text == "method"):
            return None
        for c in syntax.named_children(o.node):
            if c.type == "spread_element":
                kids = syntax.named_children(c)
                sv_ = self.ev.eval(mod, kids[0], o.scope) if kids else UNKNOWN
                if isinstance(sv_, Param):
                    return OptsParam(sv_.name, sv_.owner)
                return None
        return "GET"

    # ---- wrappers ------------------------------------------------------------------------
    def build(self, paths: list[str]) -> None:
        """Find wrappers over the given (repo-wide, non-test) files."""
        if self.wrappers is not None:
            return
        self._nest_base(paths)
        self.wrappers = {}
        for p in paths:
            m = self.p.module(p)
            if m is None:
                continue
            for pr in self.prims(m):
                w = self._wrapper_of(pr)
                if w is not None and w.fn_key not in self.wrappers:
                    self.wrappers[w.fn_key] = w
                    self.wrapper_names.add(w.name)

    def _nest_base(self, paths):
        for p in paths:
            txt = self.p.ctx.read_text(p) or ""
            if "HttpModule.register" not in txt:
                continue
            m = self.p.module(p)
            if m is None:
                continue
            for n in syntax.walk(m.root):
                if n.type == "call_expression" and syntax.text(
                        n.child_by_field_name("function")).replace(" ", "") in (
                        "HttpModule.register",):
                    a = args_of(n)
                    o = self.ev.eval(m, a[0]) if a else None
                    if isinstance(o, Obj):
                        b = as_sv(self.ev._obj_member(o, "baseURL"))
                        if b is not None:
                            self.nest_base = b
                            return

    def _wrapper_of(self, pr: Prim) -> Wrapper | None:
        url = as_sv(pr.url)
        if url is None:
            return None
        parts = list(url.parts)
        owners = {p.owner for p in parts if isinstance(p, Param)}
        if not owners:
            return None
        # innermost enclosing function that owns a URL parameter = the wrapper; parameters of
        # outer functions (factory ``createHttpService(baseURL)``) are bound through the
        # closure at the call site
        fn = pr.node.parent
        while fn is not None and not (fn.type in FN_TYPES and (pr.mod.path, key_of(fn)) in owners):
            fn = fn.parent
        if fn is None:
            return None
        owner = (pr.mod.path, key_of(fn))
        i = 0
        while i < len(parts) and (isinstance(parts[i], (Env, Cfg, Key)) or (
                isinstance(parts[i], Param) and parts[i].owner != owner)):
            i += 1
        if i < len(parts) and isinstance(parts[i], str) and re.match(r"https?://[^/]*$", parts[i]) \
                and all(not isinstance(x, str) for x in parts[:i]):
            i += 1
        if i >= len(parts) or not isinstance(parts[i], Param) or parts[i].owner != owner:
            return None
        name = self._fn_name(fn)
        if not name:
            return None
        return Wrapper(owner, pr.mod, fn, fn_params(fn, pr.mod.lang), pr, url, name)

    @staticmethod
    def _fn_name(fn) -> str:
        if fn.type in ("function_declaration", "generator_function_declaration",
                       "method_definition"):
            return _member_name(fn) if fn.type == "method_definition" else \
                syntax.text(fn.child_by_field_name("name"))
        par = fn.parent
        if par is None:
            return ""
        if par.type == "variable_declarator":
            return syntax.text(par.child_by_field_name("name"))
        if par.type == "pair":
            return syntax.text(par.child_by_field_name("key")).strip("'\"")
        if par.type in ("public_field_definition", "field_definition"):
            return _member_name(par)
        if par.type == "assignment_expression":
            return syntax.text(par.child_by_field_name("left")).split(".")[-1]
        return ""

    def calls(self, paths: list[str]) -> tuple[list[Call], set[str]]:
        """Resolved calls in ``paths`` (direct primitives not inside wrappers + wrapper call
        sites) and the set of files with unresolved HTTP constructs."""
        assert self.wrappers is not None, "build() first"
        out: list[Call] = []
        unresolved: set[str] = set()
        wrapped_prims = {(w.prim.mod.path, key_of(w.prim.node)) for w in self.wrappers.values()}
        for p in paths:
            m = self.p.module(p)
            if m is None:
                continue
            for pr in self.prims(m):
                if (m.path, key_of(pr.node)) in wrapped_prims:
                    continue
                url = as_sv(pr.url)
                if url is None:
                    unresolved.add(p)
                    continue
                url = _params_to_holes(url)
                out.append(Call(m, pr.node, pr.client, pr.client_name,
                                pr.method if isinstance(pr.method, str) else None, url,
                                _raw(pr), _type_arg(pr.type_node), None, None, url.heuristic))
            if not self.wrapper_names:
                continue
            txt = self.p.ctx.read_text(p) or ""
            if not any(nm in txt for nm in self.wrapper_names):
                continue
            for n in syntax.walk(m.root):
                if n.type != "call_expression" or callee_name(n) not in self.wrapper_names:
                    continue
                cv = self.ev.eval(m, unwrap(n.child_by_field_name("function")))
                if not isinstance(cv, Fn):
                    continue
                w = self.wrappers.get(cv.key)
                if w is None:
                    continue
                c = self._site(m, n, w, cv)
                if c is None:
                    unresolved.add(p)
                else:
                    out.append(c)
        for w in self.wrappers.values():
            if w.mod.path in paths:
                unresolved.add(w.mod.path)  # the wrapper itself is generic
        return out, unresolved

    def _site(self, m: Module, n, w: Wrapper, fnv: Fn) -> Call | None:
        args = args_of(n)
        frame = {}
        for i, pn in enumerate(w.params):
            if i < len(args):
                frame[pn] = self.ev.eval(m, args[i])
        closure = fnv.scope.frames if fnv.scope is not None else {}
        parts: list = []
        heur = w.url.heuristic
        for part in w.url.parts:
            if isinstance(part, Param) and (part.owner == w.fn_key or part.owner in closure):
                v = frame.get(part.name) if part.owner == w.fn_key else \
                    closure[part.owner].get(part.name)
                if isinstance(v, SV):
                    parts += list(v.parts)
                    heur |= v.heuristic
                elif isinstance(v, Param):
                    parts.append(v)
                else:
                    parts.append(Dyn(part.name))
            else:
                parts.append(part)
        url = _params_to_holes(sv(*parts, heuristic=heur))
        method = w.prim.method
        if isinstance(method, Param):
            mv = frame.get(method.name)
            method = mv.literal().upper() if isinstance(mv, SV) and mv.literal() else None
        elif isinstance(method, OptsParam):
            if method.owner != w.fn_key:
                method = None
            elif method.name not in frame:
                method = "GET"          # options omitted at the call site
            else:
                o = frame[method.name]
                method = None
                if isinstance(o, Obj):
                    mv = self.ev._obj_member(o, "method")
                    lit = mv.literal() if isinstance(mv, SV) else None
                    method = lit.upper() if lit else (
                        "GET" if isinstance(mv, Unknown) and mv.text == "method" and not any(
                            c.type == "spread_element" for c in syntax.named_children(o.node))
                        else None)
        resp = _type_arg(n.child_by_field_name("type_arguments")) or None
        raw = syntax.text(args[0])[:200] if args else ""
        return Call(m, n, w.prim.client, w.prim.client_name, method, url, raw, resp, None,
                    f"{w.mod.path}:{syntax.line(w.fn_node)}", heur)


def _join_base(base: SV | None, url):
    if base is None:
        return url
    u = as_sv(url)
    if u is None:
        return url
    if u.parts and isinstance(u.parts[0], str) and re.match(r"[a-z][a-z0-9+.\-]*://", u.parts[0],
                                                             re.I):
        return u
    return concat(base, u)


def _params_to_holes(v: SV) -> SV:
    return SV(tuple(Dyn(p.name) if isinstance(p, Param) else p for p in v.parts), v.heuristic)


def _raw(pr: Prim) -> str:
    a = args_of(pr.node)
    return syntax.text(a[0])[:200] if a else ""


def _type_arg(targs) -> str | None:
    if targs is None:
        return None
    kids = syntax.named_children(targs)
    return unwrap_type(syntax.text(kids[0])) if kids else None


_WRAPPERS = ("Promise", "Observable", "AxiosResponse", "Readonly")
_PRIM = {"string": "string", "number": "number", "boolean": "boolean", "Date": "datetime",
         "any": "any", "unknown": "any", "object": "object", "Object": "object",
         "bigint": "integer", "Buffer": "binary", "Blob": "binary", "File": "binary",
         "void": None, "never": None, "undefined": None, "null": None}


def unwrap_type(t: str | None) -> str | None:
    """``Promise<X>``/``Observable<X>``/``AxiosResponse<X>`` -> X; ``Array<X>`` -> ``X[]``."""
    if not t:
        return None
    t = re.sub(r"\s+", " ", t.strip().lstrip(":").strip())
    for _ in range(4):
        m = re.fullmatch(r"(\w+)\s*<(.*)>", t)
        if m and m.group(1) in _WRAPPERS:
            t = m.group(2).strip()
            continue
        break
    m = re.fullmatch(r"Array\s*<(.*)>", t)
    if m:
        inner = unwrap_type(m.group(1))
        return f"{inner}[]" if inner else None
    t = re.sub(r"\s*\|\s*(null|undefined)\b", "", t).strip()
    if t in _PRIM:
        return _PRIM[t]
    return t or None


def norm_type(t: str | None) -> str | None:
    t = unwrap_type(t)
    if t is None:
        return None
    if t.endswith("[]"):
        inner = norm_type(t[:-2])
        return f"{inner or 'any'}[]"
    if re.fullmatch(r"Record\s*<.*>|\{.*\}", t, re.S):
        return "object"
    if re.fullmatch(r"('[^']*'|\"[^\"]*\")(\s*\|\s*('[^']*'|\"[^\"]*\"))+", t):
        vals = re.findall(r"['\"]([^'\"]*)['\"]", t)
        return f"enum[{','.join(vals)}]"
    return t


def type_names(t: str | None) -> list[str]:
    """Candidate user type names referenced by a type expression."""
    if not t:
        return []
    out = []
    for w in re.findall(r"[A-Za-z_$][\w$]*", t):
        if w in _PRIM or w in _WRAPPERS or w in ("Array", "Record", "Partial", "Pick", "Omit",
                                                 "Map", "Set", "Required", "keyof", "typeof"):
            continue
        if w[0].isupper() and w not in out:
            out.append(w)
    return out


# ---- config reads -------------------------------------------------------------------------
def config_reads(ctx: RepoContext, proj: Project, paths: list[str], extractor) -> list:
    """``process.env.X``, ``process.env['X']``, ``import.meta.env.X``, ``const {X} = process.env``,
    ``configService.get('X')`` -> config_key items (names only; values come from config files)."""
    found: dict[str, list] = {}
    for p in paths:
        txt = ctx.read_text(p) or ""
        if "env" not in txt and ".get(" not in txt:
            continue
        m = proj.module(p)
        if m is None:
            continue
        for n in syntax.walk(m.root):
            name, api = None, None
            if n.type == "member_expression":
                o = syntax.text(n.child_by_field_name("object")).replace("?.", ".").replace(" ", "")
                if o in ("process.env", "import.meta.env"):
                    name = syntax.text(n.child_by_field_name("property"))
                    api = o
            elif n.type == "subscript_expression":
                o = syntax.text(n.child_by_field_name("object")).replace("?.", ".").replace(" ", "")
                if o in ("process.env", "import.meta.env"):
                    s = syntax.decode_string(n.child_by_field_name("index"), "ts")
                    if isinstance(s, str):
                        name, api = s, o
            elif n.type == "variable_declarator":
                nm = n.child_by_field_name("name")
                val = n.child_by_field_name("value")
                if nm is not None and nm.type == "object_pattern" and val is not None and \
                        syntax.text(val).replace("?.", ".") in ("process.env", "import.meta.env"):
                    for k, _al in _pattern_names(nm):
                        found.setdefault(k, []).append((p, syntax.line(n), syntax.text(val)))
            elif n.type == "call_expression":
                fn = n.child_by_field_name("function")
                if fn is not None and fn.type == "member_expression" and syntax.text(
                        fn.child_by_field_name("property")) in ("get", "getOrThrow") and re.search(
                        r"config(Service)?$", syntax.text(fn.child_by_field_name("object")), re.I):
                    a = args_of(n)
                    s = syntax.decode_string(a[0], "ts") if a else None
                    if isinstance(s, str):
                        name, api = s, "ConfigService.get"
            if name and re.fullmatch(r"[A-Za-z_][\w.\-:]*", name):
                found.setdefault(name, []).append((p, syntax.line(n), api))
    items = []
    for name in sorted(found):
        reads = found[name]
        canon, _ = cc.canonical_key(name)
        if not canon:
            continue
        c = cc.classify(name, None)
        by_sub: dict[str, list] = {}
        for f, ln, api in reads:
            by_sub.setdefault(ctx.subproject_of(f), []).append((f, ln, api))
        for sub, rs in sorted(by_sub.items()):
            rs = sorted(set(rs))
            attrs = {"name": name, "canonical": canon,
                     "reads": [{"file": f, "line": ln, "api": api} for f, ln, api in rs],
                     "secret": True if c.secret else None,
                     "value_kind": "hidden" if c.secret else None}
            items.append(make_item("config_key", sub, canon, attrs,
                                   [ctx.evidence(f, ln) for f, ln, _ in rs], extractor))
    return items


# ---- schemas ------------------------------------------------------------------------------
_VALIDATORS = re.compile(r"^(Is[A-Z]\w*|Min|Max|MinLength|MaxLength|Length|Matches|Contains|"
                         r"ArrayMinSize|ArrayMaxSize|ArrayNotEmpty|ValidateNested|Equals|"
                         r"NotEquals|Allow|Type)$")


def _field_info(f: syntax.FieldDecl, lang: str) -> dict:
    decos = f.annotations
    names = [a.name for a in decos]
    optional = f.optional or "IsOptional" in names
    for a in decos:
        if a.name in ("ApiProperty", "ApiPropertyOptional"):
            if a.name == "ApiPropertyOptional":
                optional = True
            arg = a.args.positional[0] if a.args.positional else None
            if isinstance(arg, dict) and arg.get("required") is False:
                optional = True
    validation = [syntax.text(a.node).lstrip("@")[:120] for a in decos
                  if _VALIDATORS.match(a.name) and a.name not in ("IsOptional", "Type")]
    ty = f.type
    nullable = bool(ty and re.search(r"\|\s*null\b", ty))
    if ty is None and f.value is not None:
        ty = {"string": "string", "number": "number", "true": "boolean",
              "false": "boolean"}.get(f.value.type)
    default = syntax.text(f.value)[:80] if f.value is not None else None
    return {"name": f.name, "json_name": None, "type": norm_type(ty),
            "required": not optional, "nullable": nullable,
            "validation": "; ".join(validation) if validation else None, "default": default}


def schema_items(ctx: RepoContext, proj: Project, names: list[str], subproject: str,
                 extractor, max_items: int = 200) -> list:
    """schema items for ``names`` and the user types their fields reference (transitive)."""
    types = proj.types()
    out, seen = [], set()
    todo = [n for n in names if n]
    while todo and len(out) < max_items:
        name = todo.pop(0)
        if name in seen:
            continue
        seen.add(name)
        cands = types.get(name)
        if not cands:
            continue
        cands = sorted(cands, key=lambda x: (ctx.subproject_of(x[0].path) != subproject,
                                             x[0].path, x[1].line))
        mod, td = cands[0]
        attrs = {"name": name, "defined_in": f"{mod.path}:{td.line}", "language": "typescript"
                 if mod.lang in ("ts", "tsx") else "javascript",
                 "type_params": list(td.type_params),
                 "extends": td.extends[0] if td.extends else None, "resolved": True,
                 "fields": [], "enum_values": []}
        if td.kind == "enum":
            attrs["schema_kind"] = "enum"
            attrs["enum_values"] = [m[0] for m in syntax.enum_members(td, mod.lang)]
        elif td.kind == "type":
            attrs["schema_kind"] = "type"
            val = td.node.child_by_field_name("value")
            if val is not None and val.type == "object_type":
                attrs["fields"] = [_field_info(f, mod.lang) for f in _object_type_fields(val)]
            elif val is not None:
                nt = norm_type(syntax.text(val))
                if nt and nt.startswith("enum["):
                    attrs["enum_values"] = nt[5:-1].split(",")
                    attrs["schema_kind"] = "enum"
        else:
            attrs["schema_kind"] = "class" if td.kind == "class" else "interface"
            attrs["fields"] = [_field_info(f, mod.lang) for f in syntax.fields(td, mod.lang)
                               if "static" not in f.modifiers]
        for f in attrs["fields"]:
            for tn in type_names(f["type"]):
                if tn not in seen:
                    todo.append(tn)
        if td.extends:
            for tn in type_names(td.extends[0]):
                if tn not in seen:
                    todo.append(tn)
        out.append(make_item("schema", subproject, name, attrs, [ctx.evidence(mod.path, td.line)],
                             extractor))
    return out


def _object_type_fields(node) -> list:
    out = []
    for c in node.children:
        if c.type == "property_signature":
            nm = c.child_by_field_name("name")
            out.append(syntax.FieldDecl(syntax.text(nm), syntax._type_text(
                c.child_by_field_name("type")), None, [], [], syntax.line(c), c,
                any(x.type == "?" for x in c.children)))
    return out


# ---- items --------------------------------------------------------------------------------
def call_item(ctx: RepoContext, extractor, call: Call, kind: str, extra: dict | None = None):
    sub = ctx.subproject_of(call.mod.path)
    ua = url_attrs(ctx, call.url, sub)
    if ua is None:
        return None
    attrs = {"method": call.method, "client": call.client, "client_name": call.client_name,
             "path_raw": call.raw or None, "headers": [], "request": call.request,
             "response": call.response, "via_wrapper": call.via, "role": "runtime", **ua}
    if extra:
        attrs.update(extra)
    medium = bool(call.via or call.heuristic or call.method is None)
    return make_item(kind, sub, None, attrs, [ctx.evidence(call.mod.path, syntax.line(call.node))],
                     extractor, "medium" if medium else "high")


# client / driver packages no node rule covers: importing one leaves the file partial (phase 3)
UNSUPPORTED_PKGS = ("kafkajs", "amqplib", "amqp-connection-manager", "bull", "bullmq",
                    "@reduxjs/toolkit/query", "swr", "@tanstack/react-query", "react-query",
                    "@opensearch-project/opensearch", "@elastic/elasticsearch", "@azure/cosmos",
                    "@azure/storage-blob", "@azure/storage-queue", "@azure/event-hubs",
                    "@azure/eventgrid", "aws-sdk", "@aws-sdk", "@google-cloud", "@grpc/grpc-js",
                    "grpc", "socket.io-client", "socket.io", "ws", "graphql-request",
                    "@apollo/client", "apollo-client", "superagent", "request", "needle",
                    "undici", "ky", "cassandra-driver", "neo4j-driver", "oracledb", "nats",
                    "mqtt")


def note_sdk_symbols(ctx: RepoContext, proj: Project, paths: list[str]) -> None:
    """Imported names (from packages) and declared classes for the external-systems matcher."""
    if not any(s.get("sdk_symbols") for s in ctx.registry):
        return
    for p in paths:
        m = proj.module(p)
        if m is None:
            continue
        for local, (_kind, spec, name) in sorted(m.imports.items()):
            line = m.pkgs.get(spec)
            if line is not None:
                ctx.note_sdk_symbol(name or local, p, line)
        for n in syntax.find_all(m.parsed.root, "class_declaration"):
            nm = n.child_by_field_name("name")
            if nm is not None:
                ctx.note_sdk_symbol(syntax.text(nm), p, syntax.line(n))


def touch_files(ctx: RepoContext, res: ExtractResult, proj: Project, paths: list[str],
                unresolved: set[str], extra: list[str] = ()) -> None:
    """Touch every opened file: ``full`` for clean trees with every construct resolved (also
    when the file has no construct of interest, same rule as java.spring / dotnet.aspnet);
    error trees -> ``partial`` + error; unresolved constructs / ``extra`` -> ``partial``."""
    for p in paths:
        m = proj.module(p)
        if m is None:
            res.touch(p, "partial", "unreadable or unparsable")
            continue
        if m.parsed.has_error:
            res.touch(p, "partial", f"tree-sitter: {m.parsed.errors} error nodes")
        elif p not in unresolved and m.imports_pkg(*UNSUPPORTED_PKGS) is None:
            res.touch(p, "full")
        else:
            res.touch(p, "partial")
    for p in extra:
        res.touch(p, "partial")


def decorator_args(ann: syntax.Annotation) -> list:
    """Argument nodes of a TS decorator ``@X(a, b)``."""
    kids = syntax.named_children(ann.node)
    tgt = kids[0] if kids else None
    if tgt is not None and tgt.type == "call_expression":
        return args_of(tgt)
    return []


def literal_of(v) -> str | None:
    return v.literal() if isinstance(v, SV) else None
