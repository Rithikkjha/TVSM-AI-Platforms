"""Repo-wide Java symbol index (decisions D-P2/D-P3) on top of tree-sitter trees (syntax.py).

Indexes every non-skipped ``*.java`` file of the repo (all subprojects: constants are shared across
Maven modules, e.g. TVS-CPS-BACKEND bff-service importing lead-allocation's ``ApiConstants``):
package, imports (incl. ``import static a.b.C.*`` / ``import static a.b.C.NAME``), types (nested
classes, records, enums), fields (``static final String`` constants, ``@Value("${k[:d]}")`` fields,
constructor-injected final fields incl. ``@Qualifier`` bean names), ``@ConfigurationProperties``
prefixes and ``@Bean`` factory methods.

``resolve_expr(node, scope)`` / ``resolve_value(value, scope)`` fold an expression into a
``ValueSource`` (``literal | config | env | param | unknown``) made of segments: literals,
``${...}`` placeholders (-> config key), ``System.getenv`` (-> env var), ``@Value`` fields/params,
other constants (``Outer.Inner.NAME``, static imports, inherited constants), one assignment hop
through a local variable assigned exactly once, ``String.format`` and ``UriComponentsBuilder``
chains. Depth 8, cycles -> unresolved. Nothing is executed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import syntax as sx
from .base import RepoContext

MAX_DEPTH = 8
_PLACEHOLDER = re.compile(r"\$\{([^{}:]+)(?::([^{}]*))?\}")
_FMT = re.compile(r"%(?:\d+\$)?[-#+ 0,(]*\d*(?:\.\d+)?[sdfxXobBcneEgGaAhHtT%]")
LOMBOK_PROPS = {"Data", "Value", "Getter", "Builder", "AllArgsConstructor", "SuperBuilder"}
BODY_TYPES = {"method_invocation", "object_creation_expression", "local_variable_declaration",
              "assignment_expression", "enhanced_for_statement", "lambda_expression",
              "return_statement"}


# ---- value model ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Seg:
    kind: str                 # lit | hole | config | env | param | unknown
    text: str = ""            # literal text / config key / env var / param index / expr text
    default: str | None = None


@dataclass
class ValueSource:
    kind: str                 # literal | config | env | param | unknown
    value: str | None         # literal: full text (holes "{}"); else the text after the key segment
    key: str | None = None    # config key / env var / param index
    default: str | None = None
    prefix: str = ""          # literal text before the key segment
    holes: int = 0
    unresolved: list = field(default_factory=list)
    segs: tuple = ()
    query: list = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        return self.kind in ("literal", "config", "env") and not self.unresolved


def _merge(segs: list[Seg]) -> list[Seg]:
    out: list[Seg] = []
    for s in segs:
        if s.kind == "lit" and out and out[-1].kind == "lit":
            out[-1] = Seg("lit", out[-1].text + s.text)
        elif s.kind == "lit" and not s.text:
            continue
        else:
            out.append(s)
    # A placeholder assembled by concatenation ("${" + PREFIX + ".topic}") only exists after
    # folding: split it again so it becomes a config/env key, not literal text.
    if any(s.kind == "lit" and _PLACEHOLDER.search(s.text) for s in out):
        out = [p for s in out
               for p in (split_placeholders(s.text) if s.kind == "lit" else [s])]
    return out


def _text_of(segs) -> str:
    return "".join(s.text if s.kind == "lit" else "{}" for s in segs)


def source_of(segs: list[Seg], query: list | None = None) -> ValueSource:
    segs = _merge(list(segs))
    unresolved = [s.text for s in segs if s.kind == "unknown"]
    holes = sum(1 for s in segs if s.kind in ("hole", "unknown", "param"))
    if not segs:
        return ValueSource("unknown", None, segs=(), query=list(query or []))
    idx = next((i for i, s in enumerate(segs) if s.kind in ("config", "env", "param", "unknown")),
               None)
    if idx is not None and idx > 0 and segs[idx].kind in ("param", "unknown"):
        idx = None  # "http://host/" + id -> literal with a hole
    if idx is None:
        return ValueSource("literal", _text_of(segs), holes=holes, segs=tuple(segs),
                           query=list(query or []))
    head = segs[idx]
    rest = segs[idx + 1:]
    kind = {"config": "config", "env": "env", "param": "param"}.get(head.kind, "unknown")
    return ValueSource(kind, _text_of(rest), None if kind == "unknown" else head.text,
                       head.default, _text_of(segs[:idx]), holes, unresolved, tuple(segs),
                       list(query or []))


def split_placeholders(s: str) -> list[Seg]:
    """``"${a.b:/x}/y"`` -> [config a.b (default /x), lit /y]."""
    out, pos = [], 0
    for m in _PLACEHOLDER.finditer(s):
        if m.start() > pos:
            out.append(Seg("lit", s[pos:m.start()]))
        name = m.group(1).strip()
        if re.fullmatch(r"[A-Z_][A-Z0-9_]*", name):
            out.append(Seg("env", name, m.group(2)))
        else:
            out.append(Seg("config", name, m.group(2)))
        pos = m.end()
    if pos < len(s):
        out.append(Seg("lit", s[pos:]))
    return out


def placeholder_keys(s) -> list[tuple[str, str | None]]:
    if not isinstance(s, str):
        return []
    return [(m.group(1).strip(), m.group(2)) for m in _PLACEHOLDER.finditer(s)]


# ---- index ---------------------------------------------------------------------------------
@dataclass
class JFile:
    path: str
    parsed: sx.Parsed
    package: str
    imports: dict           # simple name -> fqn
    wildcards: list         # package or class fqns (import a.b.*)
    static_imports: dict    # member name -> "a.b.C.NAME"
    static_wildcards: list  # class fqns (import static a.b.C.*)
    import_lines: dict      # fqn -> line
    types: list = field(default_factory=list)


@dataclass
class JType:
    fqn: str
    decl: sx.TypeDecl
    jfile: JFile
    fields: dict            # name -> FieldDecl
    methods: list           # MethodDecl
    value_keys: dict        # field -> (key, default, line)   (@Value field / ctor param)
    qualifiers: dict        # field -> bean name (@Qualifier on field or ctor param)
    ctor_values: dict       # field -> value node assigned in a constructor (once)
    props_prefix: str | None
    outer_fqn: str | None


@dataclass
class Scope:
    jfile: JFile
    jtype: JType | None = None
    method: sx.MethodDecl | None = None
    locals: dict = field(default_factory=dict)       # name -> [value nodes]
    local_types: dict = field(default_factory=dict)  # name -> type text
    params: dict = field(default_factory=dict)       # name -> (index, Param)


def _scoped_name(node) -> str:
    return re.sub(r"\s+", "", sx.text(node))


def _imports(root) -> tuple[str, dict, list, dict, list, dict]:
    package, imports, wild, simports, swild, lines = "", {}, [], {}, [], {}
    for c in root.children:
        if c.type == "package_declaration":
            nm = next((x for x in c.children if x.type in ("scoped_identifier", "identifier")), None)
            package = _scoped_name(nm) if nm is not None else ""
        elif c.type == "import_declaration":
            is_static = any(x.type == "static" for x in c.children)
            nm = next((x for x in c.children if x.type in ("scoped_identifier", "identifier")), None)
            if nm is None:
                continue
            name = _scoped_name(nm)
            star = any(x.type == "asterisk" for x in c.children)
            lines[name] = sx.line(c)
            if is_static and star:
                swild.append(name)
            elif is_static:
                simports[name.rsplit(".", 1)[-1]] = name
            elif star:
                wild.append(name)
            else:
                imports[name.rsplit(".", 1)[-1]] = name
    return package, imports, wild, simports, swild, lines


def strip_generics(t: str | None) -> str:
    if not t:
        return ""
    t = re.sub(r"@\w+(\([^)]*\))?\s*", "", t).strip()
    return re.sub(r"<.*$", "", t).replace("[]", "").replace("...", "").strip()


def simple_type(t: str | None) -> str:
    return strip_generics(t).rsplit(".", 1)[-1]


class JavaIndex:
    def __init__(self, ctx: RepoContext):
        self.ctx = ctx
        self.files: dict[str, JFile] = {}
        self.types: dict[str, JType] = {}
        self.beans: dict[str, tuple] = {}       # bean name -> (MethodDecl, JType)
        self._memo: dict = {}
        for e in ctx.files(None, lambda e: e.get("language") == "java"
                           or e["path"].endswith(".java")):
            path = e["path"]
            if not path.endswith(".java"):
                continue
            parsed = ctx.syntax(path)
            if parsed is None:
                continue
            pkg, imps, wild, simps, swild, ilines = _imports(parsed.root)
            jf = JFile(path, parsed, pkg, imps, wild, simps, swild, ilines)
            self.files[path] = jf
            for td in sx.type_decls(parsed):
                fqn = f"{pkg}.{td.qualified}" if pkg else td.qualified
                outer = (f"{pkg}.{td.outer}" if pkg else td.outer) if td.outer else None
                jt = JType(fqn, td, jf, {f.name: f for f in sx.fields(td, "java")},
                           sx.methods(td, "java"), {}, {}, {}, None, outer)
                if td.kind == "interface" and not td.extends:
                    ext = next((x for x in td.node.children if x.type == "extends_interfaces"),
                               None)
                    tl = next((x for x in ext.children if x.type == "type_list"), None) \
                        if ext is not None else None
                    if tl is not None:
                        td.extends = [sx.text(x) for x in sx.named_children(tl)]
                if td.kind == "record":
                    for p in td.params:
                        jt.fields.setdefault(p.name, sx.FieldDecl(p.name, p.type, None,
                                                                  p.annotations, ["final"],
                                                                  p.line, p.node))
                self._bind_fields(jt)
                jf.types.append(jt)
                self.types.setdefault(fqn, jt)
        for jt in self.types.values():
            for m in jt.methods:
                if any(a.name == "Bean" for a in m.annotations):
                    ann = next(a for a in m.annotations if a.name == "Bean")
                    names = ann.args.get("name", "value", pos=0)
                    names = names if isinstance(names, list) else [names]
                    for n in [x for x in names if isinstance(x, str)] or [m.name]:
                        self.beans.setdefault(n, (m, jt))

    # ---- field bindings ------------------------------------------------------------------
    def _bind_fields(self, jt: JType) -> None:
        cp = next((a for a in jt.decl.annotations if a.name == "ConfigurationProperties"), None)
        if cp is not None:
            pre = cp.args.get("prefix", "value", pos=0)
            jt.props_prefix = pre if isinstance(pre, str) else ""
        for f in jt.fields.values():
            for a in f.annotations:
                if a.name == "Value":
                    keys = placeholder_keys(a.args.get("value", pos=0))
                    if len(keys) == 1:
                        jt.value_keys[f.name] = (keys[0][0], keys[0][1], a.line)
                elif a.name == "Qualifier":
                    q = a.args.get("value", pos=0)
                    if isinstance(q, str):
                        jt.qualifiers[f.name] = q
        assigned: dict[str, list] = {}
        for m in jt.methods:
            if m.kind != "constructor" or m.body is None:
                continue
            pmap = {p.name: p for p in m.params}
            for n in sx.walk(m.body):
                if n.type != "assignment_expression":
                    continue
                left = n.child_by_field_name("left")
                right = n.child_by_field_name("right")
                lt = sx.text(left)
                fname = lt[5:] if lt.startswith("this.") else lt
                if fname not in jt.fields:
                    continue
                assigned.setdefault(fname, []).append(right)
                if right is not None and right.type == "identifier" and sx.text(right) in pmap:
                    p = pmap[sx.text(right)]
                    for a in p.annotations:
                        if a.name == "Value":
                            keys = placeholder_keys(a.args.get("value", pos=0))
                            if len(keys) == 1:
                                jt.value_keys.setdefault(fname, (keys[0][0], keys[0][1], a.line))
                        elif a.name == "Qualifier":
                            q = a.args.get("value", pos=0)
                            if isinstance(q, str):
                                jt.qualifiers.setdefault(fname, q)
        for fname, nodes in assigned.items():
            if len(nodes) == 1 and nodes[0] is not None:
                jt.ctor_values[fname] = nodes[0]

    def beans_of_type(self, simple: str) -> list:
        """[(MethodDecl, JType)] of every @Bean method returning ``simple`` (source order)."""
        key = ("beans_of_type", simple)
        got = self._memo.get(key)
        if got is None:
            got = [(m, jt) for jt in self.types.values() for m in jt.methods
                   if any(a.name == "Bean" for a in m.annotations)
                   and simple_type(m.return_type) == simple]
            self._memo[key] = got
        return got

    def lombok_binding(self, jt: JType, fname: str):
        """(argument node, bean-method Scope) for a field set by a Lombok-generated constructor
        (``@RequiredArgsConstructor``: final non-initialised non-static fields;
        ``@AllArgsConstructor``: all non-static fields, declaration order) when exactly one
        ``@Bean`` method in the repo calls ``new <Type>(...)`` with that arity. Else None."""
        key = ("lombok", jt.fqn)
        if key not in self._memo:
            self._memo[key] = None
            anns = {a.name for a in jt.decl.annotations}
            if not any(m.kind == "constructor" for m in jt.methods) and \
                    anns & {"RequiredArgsConstructor", "AllArgsConstructor"}:
                if "AllArgsConstructor" in anns:
                    order = [f.name for f in jt.fields.values() if "static" not in f.modifiers]
                else:
                    order = [f.name for f in jt.fields.values() if "static" not in f.modifiers
                             and "final" in f.modifiers and f.value is None]
                sites = []
                for bjt in self.types.values():
                    for m in bjt.methods:
                        if not any(a.name == "Bean" for a in m.annotations):
                            continue
                        for n in self.nodes(m, "object_creation_expression"):
                            ty = sx.text(n.child_by_field_name("type"))
                            al = n.child_by_field_name("arguments")
                            args = sx.named_children(al) if al is not None else []
                            if simple_type(ty) == jt.decl.name and len(args) == len(order):
                                t = self.resolve_type(ty, bjt.jfile, bjt)
                                if t is not None and t.fqn == jt.fqn:
                                    sites.append((args, bjt, m))
                if len(sites) == 1 and order:
                    args, bjt, m = sites[0]
                    self._memo[key] = (dict(zip(order, args)), self.method_scope(bjt, m))
        got = self._memo[key]
        if got is None or fname not in got[0]:
            return None
        return got[0][fname], got[1]

    # ---- types ---------------------------------------------------------------------------
    def outer_chain(self, jt: JType | None):
        seen = set()
        while jt is not None and jt.fqn not in seen:
            seen.add(jt.fqn)
            yield jt
            jt = self.types.get(jt.outer_fqn) if jt.outer_fqn else None

    def resolve_type(self, name: str, jfile: JFile, jtype: JType | None = None) -> JType | None:
        """Simple or dotted type name -> in-repo JType (nested, imports, package, wildcards)."""
        name = strip_generics(name)
        if not name:
            return None
        parts = name.split(".")
        first = self._resolve_simple(parts[0], jfile, jtype)
        if first is None:
            for j in range(len(parts), 0, -1):  # fully-qualified prefix
                cand = ".".join(parts[:j])
                if cand in self.types:
                    first, parts = self.types[cand], [cand] + parts[j:]
                    break
            if first is None:
                return None
        cur = first
        for p in parts[1:]:
            nxt = self.types.get(f"{cur.fqn}.{p}")
            if nxt is None:
                return None
            cur = nxt
        return cur

    def _resolve_simple(self, name: str, jfile: JFile, jtype: JType | None) -> JType | None:
        for t in self.outer_chain(jtype):
            hit = self.types.get(f"{t.fqn}.{name}")
            if hit is not None:
                return hit
            if t.decl.name == name:
                return t
        pkg = jfile.package
        for t in jfile.types:
            if t.decl.qualified == name:
                return t
        cands = []
        if name in jfile.imports:
            cands.append(jfile.imports[name])
        cands.append(f"{pkg}.{name}" if pkg else name)
        cands += [f"{w}.{name}" for w in jfile.wildcards]
        for c in cands:
            if c in self.types:
                return self.types[c]
        return None

    def supertypes(self, jt: JType) -> list[JType]:
        out = []
        for s in jt.decl.extends:
            t = self.resolve_type(s, jt.jfile, self.types.get(jt.outer_fqn) if jt.outer_fqn
                                  else None)
            if t is not None and t.fqn != jt.fqn:
                out.append(t)
        return out

    def find_field(self, jt: JType | None, name: str, depth: int = 0):
        """(JType, FieldDecl) for ``name`` visible in ``jt`` (outer classes, supertypes)."""
        if jt is None or depth > MAX_DEPTH:
            return None
        for t in self.outer_chain(jt):
            if name in t.fields:
                return t, t.fields[name]
        for s in self.supertypes(jt):
            hit = self.find_field(s, name, depth + 1)
            if hit:
                return hit
        return None

    def find_member(self, dotted: str, scope: Scope):
        """``A.B.NAME`` / static-import ``NAME`` -> (JType, FieldDecl) or None."""
        parts = dotted.split(".")
        if len(parts) == 1:
            nm = parts[0]
            fqn = scope.jfile.static_imports.get(nm)
            if fqn:
                t = self.types.get(fqn.rsplit(".", 1)[0])
                if t is not None:
                    return self.find_field(t, nm)
            for cls in scope.jfile.static_wildcards:
                t = self.types.get(cls)
                if t is not None:
                    hit = self.find_field(t, nm)
                    if hit:
                        return hit
            return None
        t = self.resolve_type(".".join(parts[:-1]), scope.jfile, scope.jtype)
        if t is None:
            return None
        return self.find_field(t, parts[-1])

    # ---- type of a name in scope ---------------------------------------------------------
    def type_of(self, node, scope: Scope) -> str | None:
        if node is None:
            return None
        t = node.type
        if t == "identifier":
            nm = sx.text(node)
            if nm in scope.local_types:
                return scope.local_types[nm]
            if nm in scope.params:
                return scope.params[nm][1].type
            hit = self.find_field(scope.jtype, nm)
            return hit[1].type if hit else None
        if t == "field_access":
            obj = node.child_by_field_name("object")
            if obj is not None and obj.type == "this":
                hit = self.find_field(scope.jtype, sx.text(node.child_by_field_name("field")))
                return hit[1].type if hit else None
            return None
        if t == "object_creation_expression":
            return sx.text(node.child_by_field_name("type"))
        if t in ("parenthesized_expression", "cast_expression"):
            kids = sx.named_children(node)
            if t == "cast_expression" and kids:
                return sx.text(kids[0])
            return self.type_of(kids[0], scope) if kids else None
        return None

    def qualifier_of(self, node, scope: Scope) -> str | None:
        """Bean name for a field reference (``@Qualifier`` or field name)."""
        if node is None:
            return None
        nm = sx.text(node)
        nm = nm[5:] if nm.startswith("this.") else nm
        if scope.params and nm in scope.params:
            for a in scope.params[nm][1].annotations:
                if a.name == "Qualifier" and isinstance(a.args.get("value", pos=0), str):
                    return a.args.get("value", pos=0)
            return nm
        for t in self.outer_chain(scope.jtype):
            if nm in t.qualifiers:
                return t.qualifiers[nm]
            if nm in t.fields:
                return nm
        return None

    # ---- per-method node cache (one walk per method body) --------------------------------
    def nodes(self, m: sx.MethodDecl, typ: str) -> list:
        key = ("nodes", id(m))
        got = self._memo.get(key)
        if got is None:
            got = {}
            if m.body is not None:
                for n in sx.walk(m.body):
                    if n.type in BODY_TYPES:
                        got.setdefault(n.type, []).append(n)
                        got.setdefault("*", []).append(n)
            self._memo[key] = (m, got)  # keep m alive so id(m) stays unique
        else:
            got = got[1]
        return got.get(typ, [])

    # ---- scopes --------------------------------------------------------------------------
    def method_scope(self, jt: JType, m: sx.MethodDecl) -> Scope:
        key = ("scope", jt.fqn, m.line, m.name)
        if key in self._memo:
            return self._memo[key]
        sc = Scope(jt.jfile, jt, m, {}, {}, {p.name: (i, p) for i, p in enumerate(m.params)})
        if m.body is not None:
            collect_locals(self.nodes(m, "*"), sc)
        self._memo[key] = sc
        return sc

    def type_scope(self, jt: JType) -> Scope:
        return Scope(jt.jfile, jt)

    # ---- resolution ----------------------------------------------------------------------
    def resolve_expr(self, node, scope: Scope) -> ValueSource:
        segs, query = self._node(node, scope, MAX_DEPTH, frozenset())
        return source_of(segs, query)

    def resolve_value(self, v, scope: Scope) -> ValueSource:
        segs, query = self._val(v, scope, MAX_DEPTH, frozenset())
        return source_of(segs, query)

    def _val(self, v, scope, depth, seen):
        if isinstance(v, str):
            return split_placeholders(v), []
        if isinstance(v, bool) or v is None:
            return [Seg("unknown", repr(v))], []
        if isinstance(v, (int, float)):
            return [Seg("lit", str(v))], []
        if isinstance(v, sx.Ref):
            return self._name(v.name, scope, depth, seen), []
        if isinstance(v, sx.Concat):
            out, q = [], []
            for p in v.parts:
                s, qq = self._val(p, scope, depth, seen)
                out += s
                q += qq
            return out, q
        if isinstance(v, sx.Template):
            return [Seg("lit", p) if isinstance(p, str) else Seg("hole") for p in v.parts], []
        return [Seg("unknown", getattr(v, "text", repr(v))[:80])], []

    def _name(self, name: str, scope: Scope, depth: int, seen: frozenset) -> list[Seg]:
        if depth <= 0:
            return [Seg("unknown", name)]
        if name.startswith("this."):
            name = name[5:]
            if "." in name:
                return [Seg("unknown", "this." + name)]
            return self._field(name, scope, depth, seen, local_ok=False)
        if "." not in name:
            if name in scope.locals:
                key = ("local", id(scope), name)
                vals = scope.locals[name]
                if key in seen or len(vals) != 1 or vals[0] is None:
                    return [Seg("unknown", name)]
                s, _ = self._node(vals[0], scope, depth - 1, seen | {key})
                return s
            if name in scope.params:
                idx, p = scope.params[name]
                for a in p.annotations:
                    if a.name == "Value":
                        keys = placeholder_keys(a.args.get("value", pos=0))
                        if len(keys) == 1:
                            k, d = keys[0]
                            return [Seg("env" if re.fullmatch(r"[A-Z_][A-Z0-9_]*", k)
                                        else "config", k, d)]
                return [Seg("param", str(idx))]
            return self._field(name, scope, depth, seen)
        hit = self.find_member(name, scope)
        if hit is None:
            return [Seg("unknown", name)]
        return self._field_value(hit[0], hit[1], depth, seen)

    def _field(self, name, scope, depth, seen, local_ok=True) -> list[Seg]:
        hit = self.find_field(scope.jtype, name) if scope.jtype is not None else None
        if hit is None:
            hit = self.find_member(name, scope)
        if hit is None:
            return [Seg("unknown", name)]
        return self._field_value(hit[0], hit[1], depth, seen)

    def _field_value(self, jt: JType, f: sx.FieldDecl, depth: int, seen: frozenset) -> list[Seg]:
        key = ("field", jt.fqn, f.name)
        if key in seen:
            return [Seg("unknown", f.name)]
        if f.name in jt.value_keys:
            k, d, _ = jt.value_keys[f.name]
            return [Seg("env" if re.fullmatch(r"[A-Z_][A-Z0-9_]*", k) else "config", k, d)]
        # @Value(Constants.PROP) - the placeholder text lives in a constant (TVS-CPS-BACKEND
        # OrderProducerService); constants are only resolvable once the index is complete
        va = next((a for a in f.annotations if a.name == "Value"), None)
        if va is not None:
            v = va.args.get("value", pos=0)
            if v is not None and not isinstance(v, str):
                s, _ = self._val(v, Scope(jt.jfile, jt), depth - 1, seen | {key})
                return _merge(s)
        node = f.value if f.value is not None else jt.ctor_values.get(f.name)
        if node is None:
            return [Seg("unknown", f.name)]
        sc = Scope(jt.jfile, jt)
        if f.value is None:  # assigned in a constructor: resolve in that constructor's scope
            ctor = next((m for m in jt.methods if m.kind == "constructor" and m.body is not None
                         and m.node.start_byte <= node.start_byte < m.node.end_byte), None)
            if ctor is not None:
                sc = self.method_scope(jt, ctor)
        s, _ = self._node(node, sc, depth - 1, seen | {key})
        return s

    def _node(self, node, scope: Scope, depth: int, seen: frozenset):
        if node is None:
            return [Seg("unknown", "")], []
        if depth <= 0:
            return [Seg("unknown", sx.text(node)[:80])], []
        t = node.type
        s = sx.decode_string(node, "java") if t in ("string_literal",) else None
        if isinstance(s, str):
            return split_placeholders(s), []
        if t in ("decimal_integer_literal", "hex_integer_literal"):
            return [Seg("lit", sx.text(node))], []
        if t == "parenthesized_expression":
            kids = sx.named_children(node)
            return self._node(kids[0], scope, depth, seen) if kids else ([Seg("unknown")], [])
        if t == "cast_expression":
            kids = sx.named_children(node)
            return self._node(kids[-1], scope, depth, seen) if kids else ([Seg("unknown")], [])
        if t == "binary_expression":
            op = node.child_by_field_name("operator")
            if op is not None and sx.text(op) == "+":
                a, qa = self._node(node.child_by_field_name("left"), scope, depth, seen)
                b, qb = self._node(node.child_by_field_name("right"), scope, depth, seen)
                return a + b, qa + qb
            return [Seg("unknown", sx.text(node)[:80])], []
        if t in ("identifier", "field_access", "scoped_identifier"):
            nm = _scoped_name(node)
            if t == "field_access":
                obj = node.child_by_field_name("object")
                if obj is not None and obj.type not in ("identifier", "field_access", "this",
                                                        "scoped_identifier"):
                    return [Seg("unknown", nm[:80])], []
            return self._name(nm, scope, depth, seen), []
        if t == "method_invocation":
            return self._invocation(node, scope, depth, seen)
        if t == "object_creation_expression":
            ty = simple_type(sx.text(node.child_by_field_name("type")))
            args = sx.named_children(node.child_by_field_name("arguments")) \
                if node.child_by_field_name("arguments") is not None else []
            if ty in ("URI", "URL", "StringBuilder", "String") and len(args) == 1:
                return self._node(args[0], scope, depth, seen)
        if t == "ternary_expression":
            return [Seg("unknown", "?:")], []
        return [Seg("unknown", sx.text(node)[:80])], []

    def _invocation(self, node, scope: Scope, depth: int, seen: frozenset):
        name = sx.text(node.child_by_field_name("name"))
        obj = node.child_by_field_name("object")
        al = node.child_by_field_name("arguments")
        args = sx.named_children(al) if al is not None else []
        ot = _scoped_name(obj) if obj is not None else ""
        if ot == "String" and name == "format" and args:
            return self._format(args[0], args[1:], scope, depth, seen)
        if name == "formatted" and obj is not None:
            return self._format(obj, args, scope, depth, seen)
        if ot == "System" and name == "getenv" and len(args) == 1:
            v = sx.decode_string(args[0], "java")
            if isinstance(v, str):
                return [Seg("env", v)], []
        if name in ("getProperty", "getRequiredProperty") and args and obj is not None and \
                "env" in ot.lower():
            v = sx.decode_string(args[0], "java")
            if isinstance(v, str):
                d = sx.decode_string(args[1], "java") if len(args) > 1 else None
                return [Seg("config", v, d if isinstance(d, str) else None)], []
        if name == "concat" and obj is not None and len(args) == 1:
            a, qa = self._node(obj, scope, depth, seen)
            b, qb = self._node(args[0], scope, depth, seen)
            return a + b, qa + qb
        if ot == "URI" and name == "create" and len(args) == 1:
            return self._node(args[0], scope, depth, seen)
        chain = invocation_chain(node)
        if chain and chain[0][0] is not None and simple_type(_scoped_name(chain[0][0])) \
                == "UriComponentsBuilder":
            return self._uri_builder(chain, scope, depth, seen)
        if len(chain) > 1 and chain[0][0] is not None and chain[0][0].type == "identifier" \
                and self._is_uri_builder(chain[0][0], scope):
            # builder.path(x).build().toUriString() on a UriComponentsBuilder local / param
            rs, rq = self._node(chain[0][0], scope, depth - 1, seen)
            return self._uri_builder(chain, scope, depth, seen, rs, rq)
        if name in ("toString", "trim", "strip") and obj is not None and not args:
            return self._node(obj, scope, depth, seen)
        if obj is not None and obj.type in ("identifier", "field_access") and not args and \
                re.match(r"(get|is)[A-Z]", name):
            ty = self.type_of(obj, scope)
            jt = self.resolve_type(ty, scope.jfile, scope.jtype) if ty else None
            if jt is None or jt.props_prefix is None:
                jt = self._bound_type(obj, scope) or jt
            if jt is not None and jt.props_prefix is not None:
                prop = name[3:] if name.startswith("get") else name[2:]
                prop = prop[:1].lower() + prop[1:]
                key = f"{jt.props_prefix}.{prop}" if jt.props_prefix else prop
                return [Seg("config", key)], []
        if (obj is None or obj.type == "this") and scope.jtype is not None:
            # one hop into a same-class helper returning an expression (e.g. getBaseUrl(),
            # buildSafeUrl(baseUrl, endpoint)): the return expression is resolved in the
            # helper's scope, then each of its parameter segments is replaced by the caller-side
            # segments of the matching argument
            m = next((m for t in self.outer_chain(scope.jtype) for m in t.methods
                      if m.name == name and len(m.params) == len(args)), None)
            key = ("call", scope.jtype.fqn, name, len(args))
            if m is not None and m.body is not None and key not in seen:
                ret = [n for n in sx.walk(m.body) if n.type == "return_statement"]
                if len(ret) == 1 and sx.named_children(ret[0]):
                    owner = next(t for t in self.outer_chain(scope.jtype) if m in t.methods)
                    s, q = self._node(sx.named_children(ret[0])[0],
                                      self.method_scope(owner, m), depth - 1, seen | {key})
                    if not args:
                        return s, q
                    return self._subst(s, q, args, scope, depth - 1, seen | {key})
        return [Seg("unknown", sx.text(node)[:80])], []

    def _subst(self, segs, query, args, scope, depth, seen):
        """Replace ``Seg("param", i)`` by the segments of ``args[i]`` resolved in ``scope``."""
        out, q = [], list(query)
        for x in segs:
            if x.kind == "param" and x.text.isdigit() and int(x.text) < len(args):
                a, aq = self._node(args[int(x.text)], scope, depth, seen)
                out += a
                q += [v for v in aq if v not in q]
            else:
                out.append(x)
        return out, q

    def _bound_type(self, node, scope: Scope) -> JType | None:
        """Declared type of the bean argument a Lombok-constructor field is bound to (an
        abstract ``CatalogueApiProperties`` field fed ``NortonCatalogueApiProperties``)."""
        nm = sx.text(node)
        nm = nm[5:] if nm.startswith("this.") else nm
        if "." in nm or nm in scope.locals or nm in scope.params or scope.jtype is None:
            return None
        hit = self.find_field(scope.jtype, nm)
        if hit is None or hit[1].value is not None or nm in hit[0].ctor_values:
            return None
        b = self.lombok_binding(hit[0], nm)
        if b is None:
            return None
        ty = self.type_of(b[0], b[1])
        return self.resolve_type(ty, b[1].jfile, b[1].jtype) if ty else None

    def _is_uri_builder(self, node, scope: Scope) -> bool:
        if simple_type(self.type_of(node, scope)) in ("UriComponentsBuilder", "UriComponents"):
            return True
        vals = scope.locals.get(sx.text(node)) or []
        if len(vals) == 1 and vals[0] is not None and vals[0].type == "method_invocation":
            root = invocation_chain(vals[0])[0][0]
            return root is not None and simple_type(_scoped_name(root)) == "UriComponentsBuilder"
        return False

    def _format(self, fmt_node, args, scope, depth, seen):
        fmt, q = self._node(fmt_node, scope, depth, seen)
        if any(s.kind != "lit" for s in fmt):
            return fmt, q
        text = "".join(s.text for s in fmt)
        out, pos, i = [], 0, 0
        for m in _FMT.finditer(text):
            out.append(Seg("lit", text[pos:m.start()]))
            pos = m.end()
            if m.group(0) == "%%":
                out.append(Seg("lit", "%"))
                continue
            if i < len(args):
                s, qq = self._node(args[i], scope, depth, seen)
                q += qq
                out += [x if x.kind != "unknown" else Seg("hole") for x in s] \
                    if not all(x.kind == "unknown" for x in s) else [Seg("hole")]
            else:
                out.append(Seg("hole"))
            i += 1
        out.append(Seg("lit", text[pos:]))
        return out, q

    def _uri_builder(self, chain, scope, depth, seen, segs=None, query=None):
        segs = list(segs or [])
        query = list(query or [])
        for _obj, name, args in chain[1:]:
            if name in ("fromHttpUrl", "fromUriString", "fromPath", "path", "uri") and args:
                s, q = self._node(args[0], scope, depth, seen)
                if name == "path" and segs and s and s[0].kind == "lit" and \
                        not s[0].text.startswith("/") and not _text_of(segs).endswith("/"):
                    segs.append(Seg("lit", "/"))
                elif name == "path" and segs and s and s[0].kind != "lit":
                    # path(param): UriComponentsBuilder inserts the separator; "//" collapses
                    segs.append(Seg("lit", "/"))
                segs += s
                query += q
            elif name == "pathSegment":
                for a in args:
                    s, _ = self._node(a, scope, depth, seen)
                    segs.append(Seg("lit", "/"))
                    segs += [x if x.kind == "lit" else Seg("hole") for x in s]
            elif name in ("queryParam", "queryParamIfPresent") and args:
                v = sx.decode_string(args[0], "java")
                if not isinstance(v, str):
                    r = self.resolve_expr(args[0], scope)
                    v = r.value if r.kind == "literal" and not r.holes else None
                if isinstance(v, str) and v not in query:
                    query.append(v)
        return segs or [Seg("unknown", "UriComponentsBuilder")], query


def invocation_chain(node) -> list:
    """``a.b(x).c(y)`` outermost invocation -> [(root node, None, []), (_, 'b', [x]), (_, 'c', [y])].
    The root is the innermost receiver (identifier / object creation / ``None`` for bare calls)."""
    calls = []
    cur = node
    while cur is not None and cur.type == "method_invocation":
        al = cur.child_by_field_name("arguments")
        calls.append((cur, sx.text(cur.child_by_field_name("name")),
                      sx.named_children(al) if al is not None else []))
        cur = cur.child_by_field_name("object")
    calls.reverse()
    return [(cur, None, [])] + calls


def outermost(node):
    """Climb from an invocation/creation to the outermost call of its fluent chain."""
    cur = node
    while cur.parent is not None and cur.parent.type == "method_invocation" and \
            cur.parent.child_by_field_name("object") == cur:
        cur = cur.parent
    return cur


def collect_locals(body_nodes, scope: Scope) -> None:
    """Local variable declarations + plain assignments in a method body (lambdas included);
    ``body_nodes`` = the body's nodes in pre-order (``JavaIndex.nodes(m, "*")``)."""
    for n in body_nodes:
        if n.type == "local_variable_declaration":
            ty = sx.text(n.child_by_field_name("type"))
            for vd in n.children:
                if vd.type != "variable_declarator":
                    continue
                nm = sx.text(vd.child_by_field_name("name"))
                val = vd.child_by_field_name("value")
                scope.locals.setdefault(nm, [])
                if val is not None:
                    scope.locals[nm].append(val)
                if ty and ty != "var":
                    scope.local_types[nm] = ty
                elif val is not None and val.type == "object_creation_expression":
                    scope.local_types[nm] = sx.text(val.child_by_field_name("type"))
        elif n.type == "assignment_expression":
            left = n.child_by_field_name("left")
            if left is not None and left.type == "identifier":
                nm = sx.text(left)
                op = sx.text(n.child_by_field_name("operator"))
                if nm in scope.locals:
                    scope.locals[nm].append(
                        n.child_by_field_name("right") if op == "=" else None)
        elif n.type == "enhanced_for_statement":
            nm = n.child_by_field_name("name")
            if nm is not None:
                scope.locals.setdefault(sx.text(nm), []).append(None)
        elif n.type == "lambda_expression":
            ps = n.child_by_field_name("parameters")
            if ps is None:
                continue
            ids = [ps] if ps.type == "identifier" else [
                x for x in sx.walk(ps) if x.type == "identifier"
                and (x.parent is ps or x.parent.type in ("formal_parameter",
                                                         "inferred_parameters"))]
            for x in ids:
                scope.locals.setdefault(sx.text(x), []).append(None)


def index(ctx: RepoContext) -> JavaIndex:
    """Repo-wide index, built once per RepoContext (``ctx.symbols['java']``)."""
    idx = ctx.symbols.get("java")
    if idx is None:
        idx = ctx.symbols["java"] = JavaIndex(ctx)
    return idx
