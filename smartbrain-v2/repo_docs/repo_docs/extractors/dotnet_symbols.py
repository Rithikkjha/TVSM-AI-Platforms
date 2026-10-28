"""Repo-wide C# symbol index + value resolution for ``dotnet.aspnet`` (decisions D-P2/D-P3).

Indexes every non-skipped ``*.cs`` file of the repo (all subprojects: DTOs/entities live in
``*.Application`` / ``*.Domain`` projects while controllers live in ``*.API``):
types (nested, records, enums, primary-constructor classes), constants (``const`` and
``static readonly`` fields / static properties with an initializer), named/typed HttpClient
registrations, Refit clients, ``Configure<T>(GetSection("A"))`` option bindings, DbContexts and
entity -> table mappings (``[Table]``, ``ToTable`` in ``OnModelCreating`` / ``IEntityTypeConfiguration``).

``Resolver.resolve(node, scope)`` folds an expression into a ``Val`` made of segments: literals,
interpolation holes, ``IConfiguration["A:B"]`` / ``GetSection("A")["B"]`` / ``GetValue<T>`` /
``GetConnectionString`` (-> config key), ``Environment.GetEnvironmentVariable`` (-> env var),
method parameters, constants, one assignment hop through locals / fields / constructor assignments.
Depth 8, cycles -> unresolved. Nothing is executed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import syntax as sx
from .base import RepoContext

MAX_DEPTH = 8
LANG = "csharp"
_CFG_RECV = re.compile(r"(?i)(?:^|[._])(configuration|config|cfg|configurationroot|appconfig|"
                       r"configurationmanager)$")
_CFG_TYPES = ("IConfiguration", "IConfigurationRoot", "IConfigurationSection",
              "ConfigurationManager", "IConfigurationBuilder")
_STRINGISH = {"string_literal", "verbatim_string_literal", "raw_string_literal",
              "interpolated_string_expression"}


# ---- value model ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Seg:
    kind: str          # lit | hole | config | env | param | section | unknown
    text: str = ""     # literal text / config key / env var / param name / expr text


@dataclass
class Val:
    segs: tuple = ()
    lines: tuple = ()  # extra evidence lines followed (file, line)

    @property
    def kinds(self) -> list[str]:
        return [s.kind for s in self.segs]

    @property
    def is_literal(self) -> bool:
        return bool(self.segs) and all(s.kind in ("lit", "hole") for s in self.segs)

    @property
    def text(self) -> str | None:
        """Literal text with holes as ``{}`` (None unless literal)."""
        if not self.is_literal:
            return None
        return "".join(s.text if s.kind == "lit" else "{}" for s in self.segs)

    @property
    def single(self) -> Seg | None:
        """The only non-literal segment when the value is exactly one config/env/param."""
        segs = [s for s in self.segs if not (s.kind == "lit" and s.text == "")]
        return segs[0] if len(segs) == 1 and segs[0].kind != "lit" else None

    def source(self) -> tuple[str, str | None, str]:
        """(kind, key, rest) where kind = literal | config | env | param | unknown; ``rest`` is
        the text after the first non-literal segment (holes -> ``{}``)."""
        if not self.segs:
            return "unknown", None, ""
        if self.is_literal:
            return "literal", None, self.text or ""
        first = self.segs[0]
        if first.kind == "lit" and first.text:
            # literal prefix: later non-literal parts are holes (``"/api/x/" + id``)
            return "literal", None, "".join(s.text if s.kind == "lit" else "{}"
                                            for s in self.segs)
        if first.kind in ("config", "env", "section"):
            rest = "".join(s.text if s.kind == "lit" else "{}" for s in self.segs[1:])
            return ("config" if first.kind == "section" else first.kind), first.text, rest
        if first.kind == "param":
            rest = "".join(s.text if s.kind == "lit" else "{}" for s in self.segs[1:])
            return "param", first.text, rest
        return "unknown", None, ""

    @property
    def unresolved(self) -> list[str]:
        return [s.text for s in self.segs if s.kind in ("unknown", "param")]


def _lit(s: str) -> Val:
    return Val((Seg("lit", s),))


def _unknown(text: str) -> Val:
    return Val((Seg("unknown", text[:120]),))


def _concat(vals: list[Val]) -> Val:
    segs: list[Seg] = []
    lines: list = []
    for v in vals:
        lines += list(v.lines)
        for s in v.segs:
            if s.kind == "lit" and segs and segs[-1].kind == "lit":
                segs[-1] = Seg("lit", segs[-1].text + s.text)
            else:
                segs.append(s)
    return Val(tuple(segs), tuple(lines))


# ---- index ---------------------------------------------------------------------------------
@dataclass
class CsFile:
    path: str
    parsed: sx.Parsed
    types: list
    text: str
    is_test: bool


@dataclass
class Scope:
    path: str
    td: object | None            # TypeDecl
    body: object | None          # node searched for locals (method/ctor/lambda/compilation unit)
    params: dict = field(default_factory=dict)   # name -> type text
    line: int = 10 ** 9          # use-site line (locals declared after it are ignored)


@dataclass
class HttpReg:
    base: Val | None
    path: str
    line: int
    name: str | None


class CsIndex:
    def __init__(self) -> None:
        self.files: dict[str, CsFile] = {}
        self.consts: dict[str, tuple] = {}          # qualified / Class.NAME -> (node, path, td)
        self.types: dict[str, list[tuple]] = {}     # simple name -> [(path, TypeDecl)]
        self.named_clients: dict[str, HttpReg] = {}
        self.typed_clients: dict[str, HttpReg] = {}
        self.refit_bases: dict[str, HttpReg] = {}
        self.options_sections: dict[str, str] = {}  # options type -> config section
        self.dbcontexts: dict[str, tuple] = {}      # name -> (path, TypeDecl)
        self.entity_tables: dict[str, tuple] = {}   # entity type -> (table, schema, path, line)
        self.auth_default: str | None = None
        self.auth_evidence: tuple | None = None

    def type_decl(self, name: str | None, prefer_sub: str | None = None, ctx=None):
        if not name:
            return None
        cands = self.types.get(name.split(".")[-1]) or []
        if not cands:
            return None
        if prefer_sub is not None and ctx is not None:
            same = [c for c in cands if ctx.subproject_of(c[0]) == prefer_sub]
            if same:
                return same[0]
        return cands[0]

    def const(self, name: str, td=None):
        """Look a constant up by (partially) qualified name, from the scope of ``td``."""
        name = name.replace("this.", "").replace("global::", "")
        cands = []
        if td is not None:
            q = td.qualified
            while q:
                cands.append(f"{q}.{name}")
                q = q.rpartition(".")[0]
        cands.append(name)
        parts = name.split(".")
        for i in range(1, len(parts) - 1):
            cands.append(".".join(parts[i:]))
        for c in cands:
            if c in self.consts:
                return self.consts[c]
        return None


def get_index(ctx: RepoContext) -> CsIndex:
    """Build (once per repo context) the C# index over every non-skipped ``.cs`` file."""
    cached = ctx.symbols.get("csharp")
    if cached is not None:
        return cached
    idx = CsIndex()
    for e in ctx.files(None, lambda e: e["path"].endswith(".cs")):
        p = ctx.syntax(e["path"])
        if p is None:
            continue
        tds = sx.type_decls(p)
        idx.files[e["path"]] = CsFile(e["path"], p, tds, ctx.read_text(e["path"]) or "",
                                      e.get("class") == "test")
    for path, cf in idx.files.items():
        for td in cf.types:
            idx.types.setdefault(td.name, []).append((path, td))
            for f in sx.fields(td, LANG):
                mods = set(f.modifiers)
                if f.value is not None and ("const" in mods or ("static" in mods and
                                                                ("readonly" in mods or
                                                                 f.node.type == "property_declaration"))):
                    for key in (f"{td.qualified}.{f.name}", f"{td.name}.{f.name}"):
                        idx.consts.setdefault(key, (f.value, path, td))
            if td.kind == "class" and (any(re.search(r"\bDbContext\b|DbContext<", x)
                                           for x in td.extends)
                                       or any((f.type or "").startswith("DbSet<")
                                              for f in sx.fields(td, LANG))):
                idx.dbcontexts.setdefault(td.name, (path, td))
            for a in td.annotations:
                if a.name == "Table":
                    t = a.args.get("Name", pos=0)
                    s = a.args.get("Schema")
                    if isinstance(t, str):
                        idx.entity_tables.setdefault(td.name, (t, s if isinstance(s, str) else None,
                                                               path, a.line))
    res = Resolver(idx, ctx)
    for path, cf in idx.files.items():
        _scan_registrations(idx, res, cf)
    ctx.symbols["csharp"] = idx
    return idx


def _generic_args(node) -> list[str]:
    """Type arguments of a ``generic_name`` (``AddHttpClient<IFoo, Foo>`` -> [IFoo, Foo])."""
    tal = next((c for c in node.children if c.type == "type_argument_list"), None)
    if tal is None:
        return []
    return [sx.text(c) for c in sx.named_children(tal)]


def call_parts(inv):
    """invocation_expression -> (receiver node | None, method name, generic args, arg nodes)."""
    fn = inv.child_by_field_name("function")
    recv, name_node = None, fn
    if fn is not None and fn.type in ("member_access_expression", "conditional_access_expression"):
        recv = fn.child_by_field_name("expression")
        name_node = fn.child_by_field_name("name")
    if fn is not None and fn.type == "member_binding_expression":
        name_node = fn.child_by_field_name("name")
    gargs: list[str] = []
    name = ""
    if name_node is not None:
        if name_node.type == "generic_name":
            gargs = _generic_args(name_node)
            ident = next((c for c in name_node.children if c.type == "identifier"), None)
            name = sx.text(ident)
        else:
            name = sx.text(name_node)
    al = inv.child_by_field_name("arguments")
    args = [a for a in sx.named_children(al)] if al is not None else []
    return recv, name, gargs, args


def arg_expr(arg):
    """``argument`` node -> its expression node."""
    if arg is None:
        return None
    if arg.type != "argument":
        return arg
    kids = sx.named_children(arg)
    return kids[-1] if kids else None


def arg_name(arg) -> str | None:
    """Named argument label (``commandType: X`` -> ``commandType``)."""
    if arg is None or arg.type != "argument":
        return None
    nm = arg.child_by_field_name("name")
    if nm is not None:
        return sx.text(nm)
    kids = arg.children
    if len(kids) >= 2 and kids[0].type == "identifier" and kids[1].type == ":":
        return sx.text(kids[0])
    return None


def enclosing(node, types) -> object | None:
    cur = node.parent
    while cur is not None:
        if cur.type in types:
            return cur
        cur = cur.parent
    return None


_BODY_TYPES = ("method_declaration", "constructor_declaration", "local_function_statement",
               "lambda_expression", "anonymous_method_expression", "accessor_declaration",
               "property_declaration", "compilation_unit")


def scope_for(cf: CsFile, node) -> Scope:
    """Scope of ``node``: its type declaration, enclosing method body and parameters."""
    td = None
    best = -1
    for t in cf.types:
        if t.node.start_byte <= node.start_byte and node.end_byte <= t.node.end_byte:
            if t.node.start_byte > best:
                td, best = t, t.node.start_byte
    params: dict = {}
    body = None
    cur = node
    while cur is not None:
        if cur.type in ("method_declaration", "constructor_declaration", "local_function_statement",
                        "lambda_expression", "anonymous_method_expression"):
            for p in sx.params_of(cur, LANG):
                params.setdefault(p.name, p.type)
            if body is None and cur.type in ("method_declaration", "constructor_declaration",
                                             "local_function_statement"):
                body = cur
        if cur.type == "compilation_unit" and body is None:
            body = cur
        cur = cur.parent
    if body is None:
        body = cf.parsed.root
    if td is not None and body.type == "compilation_unit":
        body = None   # field initializer / attribute: no locals in scope
    if td is not None:
        for p in td.params:
            params.setdefault(p.name, p.type)
    return Scope(cf.path, td, body, params, sx.line(node))


def _lambda_body_assign(lam, prop: str) -> object | None:
    """``c => c.BaseAddress = new Uri(x)`` / block lambdas: the assigned expression node."""
    for n in sx.walk(lam):
        if n.type == "assignment_expression":
            left = n.child_by_field_name("left")
            if left is not None and sx.text(left).split(".")[-1] == prop:
                return n.child_by_field_name("right")
    return None


def _scan_registrations(idx: CsIndex, res: "Resolver", cf: CsFile) -> None:
    root = cf.parsed.root
    for inv in sx.find_all(root, "invocation_expression"):
        recv, name, gargs, args = call_parts(inv)
        if name in ("AddHttpClient", "AddRefitClient"):
            lam_nodes = [arg_expr(a) for a in args if arg_expr(a) is not None
                         and arg_expr(a).type == "lambda_expression"]
            # chained .ConfigureHttpClient(c => ...)
            par = inv.parent
            if par is not None and par.type == "member_access_expression":
                gp = par.parent
                nm = par.child_by_field_name("name")
                if gp is not None and gp.type == "invocation_expression" and \
                        sx.text(nm) == "ConfigureHttpClient":
                    _, _, _, cargs = call_parts(gp)
                    lam_nodes += [arg_expr(a) for a in cargs if arg_expr(a) is not None
                                  and arg_expr(a).type == "lambda_expression"]
            base = None
            for lam in lam_nodes:
                rhs = _lambda_body_assign(lam, "BaseAddress")
                if rhs is not None:
                    base = res.resolve(rhs, scope_for(cf, rhs))
                    break
            reg = HttpReg(base, cf.path, sx.line(inv), None)
            first = arg_expr(args[0]) if args else None
            if name == "AddRefitClient":
                for g in gargs[:1]:
                    idx.refit_bases.setdefault(g, reg)
                continue
            if first is not None and first.type in _STRINGISH | {"invocation_expression",
                                                                  "member_access_expression",
                                                                  "identifier"} \
                    and first.type != "lambda_expression":
                nv = res.resolve(first, scope_for(cf, first))
                if nv.is_literal:
                    reg.name = nv.text
                    idx.named_clients.setdefault(nv.text, reg)
            for g in gargs:
                idx.typed_clients.setdefault(g.split(".")[-1], HttpReg(base, cf.path,
                                                                        sx.line(inv), g))
        elif name == "Configure" and gargs and args:
            ex = arg_expr(args[-1])
            v = res.resolve(ex, scope_for(cf, ex)) if ex is not None else None
            if v is not None and v.single is not None and v.single.kind in ("section", "config"):
                idx.options_sections.setdefault(gargs[0].split(".")[-1], v.single.text)
        elif name == "ToTable" and args:
            t = res.resolve(arg_expr(args[0]), scope_for(cf, inv))
            sch = None
            if len(args) > 1:
                sv = res.resolve(arg_expr(args[1]), scope_for(cf, inv))
                sch = sv.text if sv.is_literal else None
            ent = _entity_type_for(cf, inv)
            if ent and t.is_literal:
                idx.entity_tables.setdefault(ent, (t.text, sch, cf.path, sx.line(inv)))
        elif name in ("AddJwtBearer",) or (name == "AddAuthentication" and args and
                                           "JwtBearer" in sx.text(inv)):
            if idx.auth_default is None:
                idx.auth_default = "bearer-jwt"
                idx.auth_evidence = (cf.path, sx.line(inv))
        elif name == "AddScheme" and re.search(r"(?i)bearer", sx.text(inv)):
            if idx.auth_default is None:
                idx.auth_default = "bearer-jwt"
                idx.auth_evidence = (cf.path, sx.line(inv))
        elif name == "AddScheme" and re.search(r"(?i)basic", sx.text(inv)):
            if idx.auth_default is None:
                idx.auth_default = "basic"
                idx.auth_evidence = (cf.path, sx.line(inv))


def _entity_type_for(cf: CsFile, inv) -> str | None:
    """Entity of a ``ToTable`` call: ``modelBuilder.Entity<T>(e => e.ToTable(..))``,
    ``builder.Entity<T>().ToTable(..)`` or an ``IEntityTypeConfiguration<T>`` class."""
    cur = inv
    while cur is not None:
        if cur.type == "invocation_expression":
            _, nm, g, _ = call_parts(cur)
            if nm == "Entity" and g:
                return g[0].split(".")[-1]
        cur = cur.parent
    # receiver chain: modelBuilder.Entity<T>().ToTable(...)
    recv, _, _, _ = call_parts(inv)
    while recv is not None and recv.type == "invocation_expression":
        r2, nm, g, _ = call_parts(recv)
        if nm == "Entity" and g:
            return g[0].split(".")[-1]
        recv = r2
    td = None
    for t in cf.types:
        if t.node.start_byte <= inv.start_byte and inv.end_byte <= t.node.end_byte:
            td = t
    if td is not None:
        for b in td.extends:
            m = re.match(r"IEntityTypeConfiguration<\s*([\w.]+)\s*>", b)
            if m:
                return m.group(1).split(".")[-1]
    return None


# ---- resolution ----------------------------------------------------------------------------
def is_config_receiver(node, scope: Scope | None) -> bool:
    if node is None:
        return False
    t = re.sub(r"\s+", "", sx.text(node)).rstrip("!")
    if node.type in ("identifier", "member_access_expression", "postfix_unary_expression") and \
            _CFG_RECV.search(t):
        return True
    if node.type == "identifier" and scope is not None:
        ty = scope.params.get(t)
        if ty and ty.rstrip("?") in _CFG_TYPES:
            return True
        if scope.td is not None:
            for f in sx.fields(scope.td, LANG):
                if f.name == t and (f.type or "").rstrip("?") in _CFG_TYPES:
                    return True
    return False


class Resolver:
    def __init__(self, idx: CsIndex, ctx: RepoContext):
        self.idx, self.ctx = idx, ctx

    # -- helpers --
    def _local(self, name: str, scope: Scope):
        """Latest declaration/assignment of local ``name`` before the use site (one hop)."""
        if scope.body is None:
            return None
        best = None
        for n in sx.walk(scope.body):
            if sx.line(n) > scope.line:
                continue
            if n.type == "variable_declarator":
                nm = n.child_by_field_name("name") or next(
                    (x for x in n.children if x.type == "identifier"), None)
                if nm is not None and sx.text(nm) == name:
                    val = None
                    kids = n.children
                    for i, k in enumerate(kids):
                        if k.type == "=" and i + 1 < len(kids):
                            val = kids[i + 1]
                        elif k.type == "equals_value_clause":
                            val = sx.named_children(k)[0] if sx.named_children(k) else None
                    if val is not None:
                        best = val
            elif n.type == "assignment_expression":
                left = n.child_by_field_name("left")
                op = n.child_by_field_name("operator")
                if left is not None and sx.text(left) == name and sx.text(op) == "=":
                    best = n.child_by_field_name("right")
        return best

    def member_value(self, name: str, td):
        """Initializer of field/property ``name`` of ``td`` or its single constructor
        assignment (``this.X = ...`` / ``X = ...``)."""
        if td is None:
            return None
        for f in sx.fields(td, LANG):
            if f.name == name and f.value is not None:
                return f.value
        found = []
        for m in sx.methods(td, LANG):
            if m.kind != "constructor" or m.body is None:
                continue
            for n in sx.walk(m.body):
                if n.type == "assignment_expression" and sx.text(
                        n.child_by_field_name("operator")) == "=":
                    left = sx.text(n.child_by_field_name("left")).replace("this.", "")
                    if left == name:
                        found.append(n.child_by_field_name("right"))
        if len({sx.text(x) for x in found}) == 1:
            return found[0]
        return None

    def member_type(self, name: str, scope: Scope) -> str | None:
        name = name.replace("this.", "")
        if name in scope.params:
            return scope.params[name]
        if scope.td is not None:
            for f in sx.fields(scope.td, LANG):
                if f.name == name:
                    return f.type
        return None

    def local_type(self, name: str, scope: Scope) -> tuple[str | None, object | None]:
        """Declared type text and initializer of a local / field / param ``name``."""
        if scope.body is not None:
            for n in sx.walk(scope.body):
                if n.type == "variable_declaration":
                    ty = n.child_by_field_name("type")
                    for vd in n.children:
                        if vd.type != "variable_declarator":
                            continue
                        nm = vd.child_by_field_name("name") or next(
                            (x for x in vd.children if x.type == "identifier"), None)
                        if nm is not None and sx.text(nm) == name and sx.line(vd) <= scope.line:
                            init = None
                            for i, k in enumerate(vd.children):
                                if k.type == "=" and i + 1 < len(vd.children):
                                    init = vd.children[i + 1]
                            tt = sx.text(ty) if ty is not None else None
                            return (None if tt == "var" else tt), init
        nm = name.replace("this.", "")
        if scope.td is not None:
            for f in sx.fields(scope.td, LANG):
                if f.name == nm:
                    return f.type, f.value
        if nm in scope.params:
            return scope.params[nm], None
        return None, None

    # -- main --
    def resolve(self, node, scope: Scope, depth: int = MAX_DEPTH, _seen: frozenset = frozenset()
                ) -> Val:
        if node is None:
            return _unknown("")
        if depth <= 0:
            return _unknown(sx.text(node))
        t = node.type
        if t == "argument":
            return self.resolve(arg_expr(node), scope, depth, _seen)
        if t == "interpolated_string_expression":
            return self._interp(node, scope, depth, _seen)
        if t in _STRINGISH:
            s = sx.decode_string(node, LANG)
            if isinstance(s, str):
                return _lit(s)
            if isinstance(s, sx.Template):
                return Val(tuple(Seg("lit", p) if isinstance(p, str) else Seg("hole", p.expr)
                                 for p in s.parts))
        if t in ("parenthesized_expression", "cast_expression", "postfix_unary_expression",
                 "checked_expression"):
            kids = sx.named_children(node)
            if kids:
                return self.resolve(kids[-1] if t == "cast_expression" else kids[0], scope, depth,
                                    _seen)
        if t in ("integer_literal", "real_literal"):
            return _lit(sx.text(node))
        if t == "binary_expression":
            op = sx.text(node.child_by_field_name("operator"))
            left = node.child_by_field_name("left")
            right = node.child_by_field_name("right")
            if op == "+":
                return _concat([self.resolve(left, scope, depth - 1, _seen),
                                self.resolve(right, scope, depth - 1, _seen)])
            if op == "??":
                lv = self.resolve(left, scope, depth - 1, _seen)
                if lv.unresolved and not lv.is_literal:
                    rv = self.resolve(right, scope, depth - 1, _seen)
                    if not rv.unresolved:
                        return rv
                return lv
            return _unknown(sx.text(node))
        if t in ("identifier", "member_access_expression", "this_expression"):
            return self._ref(node, scope, depth, _seen)
        if t == "element_access_expression":
            return self._element(node, scope, depth, _seen)
        if t == "invocation_expression":
            return self._invocation(node, scope, depth, _seen)
        if t in ("object_creation_expression", "implicit_object_creation_expression"):
            ty = sx.text(node.child_by_field_name("type"))
            al = node.child_by_field_name("arguments")
            args = sx.named_children(al) if al is not None else []
            if ty in ("Uri", "System.Uri") and args:
                parts = [self.resolve(arg_expr(a), scope, depth - 1, _seen) for a in args
                         if arg_expr(a) is not None and not sx.text(arg_expr(a)).startswith(
                             "UriKind")]
                if len(parts) == 2:
                    return _concat([parts[0], _lit("/"), parts[1]])
                if parts:
                    return parts[0]
            return _unknown(sx.text(node))
        return _unknown(sx.text(node))

    def _interp(self, node, scope, depth, _seen) -> Val:
        verbatim = "@" in sx.text(node.children[0]) if node.children else False
        vals: list[Val] = []
        for c in node.children:
            ct = c.type
            if ct in ("string_content", "string_literal_content", "raw_string_content"):
                s = sx.text(c)
                if verbatim:
                    s = s.replace('""', '"')
                vals.append(_lit(s.replace("{{", "{").replace("}}", "}")))
            elif ct == "escape_sequence":
                s = sx.text(c)
                vals.append(_lit(s[0] if s in ("{{", "}}") else sx.unescape(s, LANG)))
            elif ct == "interpolation":
                inner = [x for x in c.children if x.is_named and x.type not in (
                    "interpolation_brace", "interpolation_format_clause",
                    "interpolation_alignment_clause")]
                if not inner:
                    continue
                v = self.resolve(inner[0], scope, depth - 1, _seen)
                lead = not any(x.segs and any(s.text for s in x.segs) for x in vals)
                if v.is_literal or (lead and v.segs and v.segs[0].kind in ("config", "env")):
                    vals.append(v)
                elif lead and v.segs and v.segs[0].kind == "param" and len(v.segs) == 1:
                    vals.append(v)
                else:
                    vals.append(Val((Seg("hole", sx.text(inner[0])),)))
        return _concat(vals)

    def _ref(self, node, scope, depth, _seen) -> Val:
        name = re.sub(r"\s+", "", sx.text(node))
        if name in _seen:
            return _unknown(name)
        seen = _seen | {name}
        bare = name[5:] if name.startswith("this.") else name
        if node.type == "member_access_expression":
            expr = node.child_by_field_name("expression")
            nm = sx.text(node.child_by_field_name("name"))
            # IOptions<T>.Value.Prop
            if expr is not None and expr.type == "member_access_expression" and \
                    sx.text(expr.child_by_field_name("name")) in ("Value", "CurrentValue"):
                holder = sx.text(expr.child_by_field_name("expression")).replace("this.", "")
                ty = self.member_type(holder, scope) or ""
                m = re.match(r"I?Options(?:Snapshot|Monitor)?<\s*([\w.]+)\s*>", ty)
                if m and m.group(1).split(".")[-1] in self.idx.options_sections:
                    sec = self.idx.options_sections[m.group(1).split(".")[-1]]
                    return Val((Seg("config", f"{sec}:{nm}"),))
            # GetSection("A").Value
            if nm == "Value" and expr is not None:
                v = self.resolve(expr, scope, depth - 1, seen)
                if v.single is not None and v.single.kind == "section":
                    return Val((Seg("config", v.single.text),), v.lines)
            if "." in bare:
                c = self.idx.const(bare, scope.td)
                if c is not None:
                    return self._from_decl(c[0], c[1], c[2], depth, seen)
                return _unknown(name)
        if "." not in bare:
            if bare in scope.params and scope.body is not None:
                loc = self._local(bare, scope)
                if loc is not None:
                    return self.resolve(loc, Scope(scope.path, scope.td, scope.body, scope.params,
                                                   sx.line(loc)), depth - 1, seen)
                return Val((Seg("param", bare),))
            loc = self._local(bare, scope) if not name.startswith("this.") else None
            if loc is not None:
                v = self.resolve(loc, Scope(scope.path, scope.td, scope.body, scope.params,
                                            sx.line(loc)), depth - 1, seen)
                return Val(v.segs, v.lines + ((scope.path, sx.line(loc)),))
            mv = self.member_value(bare, scope.td)
            if mv is not None:
                cf = self.idx.files.get(scope.path)
                sc = scope_for(cf, mv) if cf is not None else scope
                v = self.resolve(mv, sc, depth - 1, seen)
                return Val(v.segs, v.lines + ((scope.path, sx.line(mv)),))
            c = self.idx.const(bare, scope.td)
            if c is not None:
                return self._from_decl(c[0], c[1], c[2], depth, seen)
        return _unknown(name)

    def _from_decl(self, vnode, path, td, depth, seen) -> Val:
        cf = self.idx.files.get(path)
        sc = scope_for(cf, vnode) if cf is not None else Scope(path, td, None)
        v = self.resolve(vnode, sc, depth - 1, seen)
        return Val(v.segs, v.lines + ((path, sx.line(vnode)),))

    def _element(self, node, scope, depth, _seen) -> Val:
        expr = node.child_by_field_name("expression")
        sub = node.child_by_field_name("subscript")
        keys = [arg_expr(a) for a in sx.named_children(sub)] if sub is not None else []
        if len(keys) != 1:
            return _unknown(sx.text(node))
        kv = self.resolve(keys[0], scope, depth - 1, _seen)
        if not kv.is_literal:
            return _unknown(sx.text(node))
        if is_config_receiver(expr, scope):
            return Val((Seg("config", kv.text),), kv.lines)
        ev = self.resolve(expr, scope, depth - 1, _seen) if expr is not None else None
        if ev is not None and ev.single is not None and ev.single.kind == "section":
            return Val((Seg("config", f"{ev.single.text}:{kv.text}"),), ev.lines)
        return _unknown(sx.text(node))

    def _invocation(self, node, scope, depth, _seen) -> Val:
        recv, name, gargs, args = call_parts(node)
        a0 = arg_expr(args[0]) if args else None
        if name == "nameof" and a0 is not None:
            return _lit(sx.text(a0).split(".")[-1])
        if name in ("GetSection", "GetValue", "GetConnectionString", "GetRequiredSection") and a0:
            kv = self.resolve(a0, scope, depth - 1, _seen)
            if not kv.is_literal:
                return _unknown(sx.text(node))
            key = kv.text
            if name == "GetConnectionString":
                key = f"ConnectionStrings:{key}"
            prefix = None
            if recv is None:
                return _unknown(sx.text(node))
            if not is_config_receiver(recv, scope):
                rv = self.resolve(recv, scope, depth - 1, _seen)
                if rv.single is not None and rv.single.kind == "section":
                    prefix = rv.single.text
                elif name == "GetValue" or recv.type not in ("identifier",
                                                             "member_access_expression",
                                                             "postfix_unary_expression"):
                    # GetValue on a non-configuration receiver (JObject, DataReader, ...)
                    return _unknown(sx.text(node))
            full = f"{prefix}:{key}" if prefix else key
            kind = "section" if name in ("GetSection", "GetRequiredSection") else "config"
            return Val((Seg(kind, full),), kv.lines)
        if name == "GetEnvironmentVariable" and a0 is not None:
            kv = self.resolve(a0, scope, depth - 1, _seen)
            if kv.is_literal and "{}" not in (kv.text or ""):
                return Val((Seg("env", kv.text),), kv.lines)
            return _unknown(sx.text(node))
        if name in ("ToString", "Trim", "TrimEnd", "TrimStart", "ToLower", "ToLowerInvariant")\
                and recv is not None:
            v = self.resolve(recv, scope, depth - 1, _seen)
            if name == "TrimEnd" and v.is_literal:
                return _lit((v.text or "").rstrip("/"))
            return v
        if name in ("Format",) and recv is not None and sx.text(recv) in ("string", "String") \
                and a0 is not None:
            fv = self.resolve(a0, scope, depth - 1, _seen)
            if fv.is_literal:
                return Val(tuple(Seg("lit", p) if i % 2 == 0 else Seg("hole", p)
                                 for i, p in enumerate(re.split(r"\{(\d+)(?::[^}]*)?\}",
                                                                fv.text or ""))))
        if name == "Combine" and recv is not None and sx.text(recv) in ("Path", "System.IO.Path"):
            return _unknown(sx.text(node))
        return _unknown(sx.text(node))
