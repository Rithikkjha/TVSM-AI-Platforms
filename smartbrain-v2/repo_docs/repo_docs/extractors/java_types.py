"""Java type normalization + ``schema`` items for java.spring (docs/EXTRACTORS.md#schema).

Wrappers (``ResponseEntity<T>``, ``Mono<T>``, ``Optional<T>``, ``CompletableFuture<T>`` ...) are
unwrapped, collections become ``T[]``, maps ``map<K,V>``, primitives the template names, in-repo
enums ``enum[A,B]``; domain generics stay instantiated (``APIResponse<BookingDto>``) and their
schema gets the type arguments substituted into its fields. Out-of-repo types -> ``resolved: false``.
"""
from __future__ import annotations

import re

from ..inventory_schema import make_item
from . import java_symbols as js
from . import syntax as sx

PRIM = {
    "String": "string", "char": "string", "Character": "string", "CharSequence": "string",
    "int": "integer", "Integer": "integer", "long": "integer", "Long": "integer",
    "short": "integer", "Short": "integer", "byte": "integer", "Byte": "integer",
    "BigInteger": "integer", "AtomicInteger": "integer", "AtomicLong": "integer",
    "double": "number", "Double": "number", "float": "number", "Float": "number",
    "BigDecimal": "number", "Number": "number",
    "boolean": "boolean", "Boolean": "boolean",
    "LocalDate": "date", "LocalDateTime": "datetime", "OffsetDateTime": "datetime",
    "ZonedDateTime": "datetime", "Instant": "datetime", "Date": "datetime",
    "Timestamp": "datetime", "LocalTime": "string", "Duration": "string",
    "UUID": "uuid", "MultipartFile": "binary", "Resource": "binary", "InputStream": "binary",
    "InputStreamResource": "binary", "File": "binary",
    "Object": "object", "JsonNode": "object", "ObjectNode": "object", "Map": "object",
    "HttpServletRequest": None, "HttpServletResponse": None,
}
WRAPPERS = {"ResponseEntity", "Mono", "Optional", "CompletableFuture", "HttpEntity", "Callable",
            "DeferredResult", "Future", "CompletionStage", "ListenableFuture", "WebAsyncTask",
            "RequestEntity", "EntityModel"}
COLLECTIONS = {"List", "Set", "Collection", "Iterable", "Flux", "ArrayList", "LinkedList",
               "HashSet", "LinkedHashSet", "TreeSet", "SortedSet", "Stream", "Queue", "Deque",
               "CollectionModel"}
MAPS = {"Map", "HashMap", "LinkedHashMap", "TreeMap", "ConcurrentHashMap", "MultiValueMap",
        "SortedMap", "LinkedMultiValueMap"}
REQUIRED_ANN = {"NotNull", "NotBlank", "NotEmpty", "NonNull"}
VALID_ANN = {"Size", "Min", "Max", "Pattern", "Email", "Positive", "PositiveOrZero", "Negative",
             "NegativeOrZero", "Past", "PastOrPresent", "Future", "FutureOrPresent", "Valid",
             "DecimalMin", "DecimalMax", "Digits", "NotBlank", "NotEmpty", "NotNull"}


def parse_type(s: str | None):
    """``A<B<C>, D>[]`` -> (name, [args], dims)."""
    s = re.sub(r"@[\w.]+(\([^)]*\))?\s*", "", s or "").replace("final ", "").strip()
    dims = 0
    while s.endswith("[]"):
        s, dims = s[:-2].strip(), dims + 1
    if s.endswith("..."):
        s, dims = s[:-3].strip(), dims + 1
    if s.startswith("?"):
        s = re.sub(r"^\?\s*(extends|super)?\s*", "", s).strip() or "?"
    if "<" not in s or not s.endswith(">"):
        return (s, [], dims)
    i = s.index("<")
    inner = s[i + 1:-1]
    args, depth, cur = [], 0, ""
    for c in inner:
        if c == "<":
            depth += 1
        elif c == ">":
            depth -= 1
        if c == "," and depth == 0:
            args.append(cur)
            cur = ""
        else:
            cur += c
    if cur.strip():
        args.append(cur)
    return (s[:i].strip(), [parse_type(a) for a in args], dims)


def _simple(name: str) -> str:
    return name.rsplit(".", 1)[-1]


class TypeNorm:
    """Normalizes type text in the scope of a file/type (enum lookup through the index)."""

    def __init__(self, idx: js.JavaIndex):
        self.idx = idx

    def enum_values(self, name: str, jfile, jtype) -> list | None:
        jt = self.idx.resolve_type(name, jfile, jtype)
        if jt is None or jt.decl.kind != "enum":
            return None
        return [n for n, _v, _l in sx.enum_members(jt.decl, "java")]

    def norm_tree(self, tree, jfile, jtype, subst: dict | None = None) -> str | None:
        name, args, dims = tree
        if subst and name in subst and not args:
            base = subst[name]
            return None if base is None else base + "[]" * dims
        simple = _simple(name)
        if dims:
            if simple in ("byte", "Byte") and dims == 1:
                return "binary"
            inner = self.norm_tree((name, args, 0), jfile, jtype, subst)
            return (inner or "any") + "[]" * dims
        if name in ("?", ""):
            return "any"
        if simple in ("void", "Void"):
            return None
        if simple in WRAPPERS:
            return self.norm_tree(args[0], jfile, jtype, subst) if args else "any"
        if simple in COLLECTIONS:
            inner = self.norm_tree(args[0], jfile, jtype, subst) if args else "any"
            return (inner or "any") + "[]"
        if simple in MAPS:
            if len(args) == 2:
                k = self.norm_tree(args[0], jfile, jtype, subst) or "any"
                v = self.norm_tree(args[1], jfile, jtype, subst) or "any"
                return f"map<{k},{v}>"
            return "object"
        if simple in PRIM and not args:
            return PRIM[simple]
        ev = self.enum_values(name, jfile, jtype) if not args else None
        if ev is not None:
            return "enum[" + ",".join(ev) + "]"
        if args:
            inner = [self.norm_tree(a, jfile, jtype, subst) or "any" for a in args]
            return f"{simple}<{','.join(inner)}>"
        return simple

    def norm(self, text: str | None, jfile, jtype, subst: dict | None = None) -> str | None:
        if not text:
            return None
        return self.norm_tree(parse_type(text), jfile, jtype, subst)

    def domain_refs(self, tree, jfile, jtype, subst=None) -> list:
        """Domain (non-primitive, non-wrapper) type sub-trees of ``tree``, outermost first."""
        name, args, _dims = tree
        simple = _simple(name)
        if subst and name in subst:
            return []
        out = []
        if simple in WRAPPERS or simple in COLLECTIONS or simple in MAPS:
            pass
        elif simple in PRIM or simple in ("void", "Void", "?", "") or \
                re.fullmatch(r"[A-Z]", simple):
            return []
        else:
            out.append((name, args, 0))
        for a in args:
            out += self.domain_refs(a, jfile, jtype, subst)
        return out


def _fmt(v) -> str:
    if isinstance(v, sx.Expr):
        return v.text
    if isinstance(v, sx.Ref):
        return v.name
    return str(v)


def _validation(anns) -> str | None:
    parts = []
    for a in anns:
        def g(*names, pos=None):
            v = a.args.get(*names, pos=pos)
            return None if v is None else _fmt(v)
        if a.name == "Size":
            if g("min") is not None:
                parts.append(f"minLength={g('min')}")
            if g("max") is not None:
                parts.append(f"maxLength={g('max')}")
        elif a.name in ("Min", "DecimalMin"):
            parts.append(f"minimum={g('value', pos=0)}")
        elif a.name in ("Max", "DecimalMax"):
            parts.append(f"maximum={g('value', pos=0)}")
        elif a.name == "Pattern":
            rx = g("regexp", pos=0)
            if isinstance(rx, str):
                parts.append(f"pattern={rx}")
        elif a.name == "Digits":
            parts.append(f"digits={g('integer')},{g('fraction')}")
        elif a.name in ("Email", "Positive", "PositiveOrZero", "Negative", "NegativeOrZero",
                        "Past", "PastOrPresent", "Future", "FutureOrPresent", "Valid"):
            parts.append(a.name[0].lower() + a.name[1:])
    return ";".join(parts) or None


def _default(node) -> object:
    if node is None:
        return None
    v = sx.value_of(node, "java")
    return v if isinstance(v, (str, int, float, bool)) else None


class SchemaCollector:
    """Collects ``schema`` items for referenced types, transitively and cycle-safe."""

    def __init__(self, ctx, idx: js.JavaIndex, tn: TypeNorm, extractor, sub: str):
        self.ctx, self.idx, self.tn, self.ex, self.sub = ctx, idx, tn, extractor, sub
        self.seen: set[str] = set()
        self.items: list = []
        self.queue: list = []

    def add(self, type_text: str | None, jfile, jtype, evidence) -> None:
        if not type_text:
            return
        for ref in self.tn.domain_refs(js_parse(type_text), jfile, jtype):
            self.queue.append((ref, jfile, jtype, evidence, None))

    def run(self) -> list:
        while self.queue:
            ref, jfile, jtype, ev, subst = self.queue.pop(0)
            self._one(ref, jfile, jtype, ev, subst)
        return self.items

    def _one(self, ref, jfile, jtype, ev, subst) -> None:
        name = self.tn.norm_tree(ref, jfile, jtype, subst)
        if not name or name in self.seen or name.startswith("enum[") and ref[1]:
            return
        jt = self.idx.resolve_type(ref[0], jfile, jtype)
        if name.startswith("enum["):
            name = _simple(ref[0])
            if name in self.seen:
                return
        self.seen.add(name)
        if jt is None:
            attrs = {"name": name, "defined_in": None, "language": "java", "schema_kind": None,
                     "fields": [], "enum_values": [], "type_params": [], "extends": None,
                     "resolved": False}
            self.items.append(make_item("schema", self.sub, name, attrs, [ev], self.ex))
            for a in ref[1]:
                for r in self.tn.domain_refs(a, jfile, jtype, subst):
                    self.queue.append((r, jfile, jtype, ev, subst))
            return
        d = jt.decl
        tparams = list(d.type_params)
        args = [self.tn.norm_tree(a, jfile, jtype, subst) for a in ref[1]]
        tsub = dict(zip(tparams, args)) if args and len(args) == len(tparams) else {}
        arg_trees = dict(zip(tparams, ref[1])) if tsub else {}
        dev = self.ctx.evidence(jt.jfile.path, d.line)
        fields = []
        enum_values = []
        if d.kind == "enum":
            enum_values = [n for n, _v, _l in sx.enum_members(d, "java")]
        else:
            for f in schema_fields(jt):
                anns = f.annotations
                if any(a.name == "JsonIgnore" for a in anns):
                    continue
                jp = next((a for a in anns if a.name == "JsonProperty"), None)
                jname = jp.args.get("value", pos=0) if jp is not None else None
                tree = parse_type(f.type)
                ftype = self.tn.norm_tree(tree, jt.jfile, jt, tsub)
                simple = _simple(tree[0])
                nullable = True if simple == "Optional" else (
                    False if simple in ("int", "long", "short", "byte", "double", "float",
                                        "boolean", "char") and not tree[2] else None)
                fields.append({
                    "name": f.name, "json_name": jname if isinstance(jname, str) else None,
                    "type": ftype,
                    "required": any(a.name in REQUIRED_ANN for a in anns),
                    "nullable": nullable, "validation": _validation(anns),
                    "default": _default(f.value)})
                for r in self.tn.domain_refs(tree, jt.jfile, jt, tsub):
                    self.queue.append((r, jt.jfile, jt, dev, tsub))
                for tp, at in arg_trees.items():
                    if re.search(rf"\b{re.escape(tp)}\b", f.type or ""):
                        for r in self.tn.domain_refs(at, jfile, jtype, subst):
                            self.queue.append((r, jfile, jtype, ev, subst))
        for s in d.extends:
            for r in self.tn.domain_refs(parse_type(s), jt.jfile, jt):
                self.queue.append((r, jt.jfile, jt, dev, None))
        attrs = {"name": name, "defined_in": f"{jt.jfile.path}:{d.line}", "language": "java",
                 "schema_kind": d.kind if d.kind in ("class", "record", "interface", "enum")
                 else "class",
                 "fields": fields, "enum_values": enum_values, "type_params": tparams,
                 "extends": js.simple_type(d.extends[0]) if d.extends and d.kind != "interface"
                 else None,
                 "resolved": True}
        self.items.append(make_item("schema", self.sub, name, attrs, [dev], self.ex))


def js_parse(text: str):
    return parse_type(text)


def schema_fields(jt: js.JType) -> list:
    """Properties of a type: record components; Lombok classes -> non-static fields; otherwise
    getters (field annotations attached when a backing field exists), else non-static fields."""
    d = jt.decl
    inst = [f for f in jt.fields.values() if "static" not in f.modifiers]
    inst.sort(key=lambda f: f.line)
    if d.kind == "record":
        return [jt.fields[p.name] for p in d.params if p.name in jt.fields]
    lombok = any(a.name in js.LOMBOK_PROPS for a in d.annotations)
    if lombok or any(any(a.name == "Getter" for a in f.annotations) for f in inst):
        return inst
    getters = []
    for m in jt.methods:
        if m.kind != "method" or m.params or "static" in m.modifiers:
            continue
        mm = re.fullmatch(r"(get|is)([A-Z]\w*)", m.name)
        if not mm or m.name == "getClass":
            continue
        prop = mm.group(2)[:1].lower() + mm.group(2)[1:]
        backing = jt.fields.get(prop)
        getters.append(sx.FieldDecl(prop, m.return_type,
                                    backing.value if backing is not None else None,
                                    (backing.annotations if backing is not None else [])
                                    + m.annotations, [], m.line, m.node))
    return getters or inst
