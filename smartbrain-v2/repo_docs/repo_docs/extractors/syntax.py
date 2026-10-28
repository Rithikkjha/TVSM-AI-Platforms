"""Source parsing with tree-sitter (decision D-P1, docs/EXTRACTORS.md) + language-neutral helpers.

Languages: ``java``, ``csharp``, ``ts``, ``tsx``, ``js``. ``.js/.jsx/.mjs/.cjs`` use the javascript
grammar; when that tree has errors the file is re-parsed with tsx and the tree with fewer error
nodes is kept. Trees with errors are still usable: ``walk`` skips ``ERROR``/``MISSING`` subtrees and
callers mark such files ``parse: partial``.

Line numbers are 1-based (``node.start_point.row + 1``), matching ledger ``lines``.
``GRAMMAR_TAG`` / ``grammar_tag(*langs)`` go into every source extractor's ``extractor_version`` so a
grammar bump makes extract output stale.
"""
from __future__ import annotations

import hashlib
import posixpath
import re
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from importlib.metadata import version as _pkg_version

import tree_sitter_c_sharp
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_typescript
from tree_sitter import Language, Node, Parser

LANGS = ("java", "csharp", "ts", "tsx", "js")
LANG_OF_EXT = {".java": "java", ".cs": "csharp", ".ts": "ts", ".mts": "ts", ".cts": "ts",
               ".tsx": "tsx", ".js": "js", ".jsx": "js", ".mjs": "js", ".cjs": "js"}
_PKG = {"java": "tree-sitter-java", "csharp": "tree-sitter-c-sharp",
        "ts": "tree-sitter-typescript", "tsx": "tree-sitter-typescript",
        "js": "tree-sitter-javascript"}
_SHORT = {"java": "java", "csharp": "cs", "ts": "tsg", "tsx": "tsg", "js": "js"}


def grammar_tag(*langs: str) -> str:
    """``ts<core>`` + ``.<lang><grammar version>`` for each distinct grammar package."""
    parts = [f"ts{_pkg_version('tree-sitter')}"]
    seen = set()
    for lang in langs or LANGS:
        pkg = _PKG[lang]
        if pkg in seen:
            continue
        seen.add(pkg)
        parts.append(f"{_SHORT[lang]}{_pkg_version(pkg)}")
    return ".".join(parts)


GRAMMAR_TAG = grammar_tag(*LANGS)


def versioned(base: str, *langs: str) -> str:
    """Extractor version with the grammar versions appended, e.g. ``0.1.0+ts0.26.0.java0.23.5``."""
    return f"{base}+{grammar_tag(*langs)}"


_LANGUAGES = {
    "java": Language(tree_sitter_java.language()),
    "csharp": Language(tree_sitter_c_sharp.language()),
    "ts": Language(tree_sitter_typescript.language_typescript()),
    "tsx": Language(tree_sitter_typescript.language_tsx()),
    "js": Language(tree_sitter_javascript.language()),
}
_tls = threading.local()


def _parser(lang: str) -> Parser:
    ps = getattr(_tls, "parsers", None)
    if ps is None:
        ps = _tls.parsers = {}
    if lang not in ps:
        ps[lang] = Parser(_LANGUAGES[lang])
    return ps[lang]


def lang_for_path(path: str) -> str | None:
    name = posixpath.basename(path)
    if name.endswith(".d.ts"):
        return None
    ext = posixpath.splitext(name)[1].lower()
    return LANG_OF_EXT.get(ext)


@dataclass
class Parsed:
    tree: object
    lang: str          # grammar actually used (js files may end up "tsx")
    requested: str
    errors: int        # number of ERROR + MISSING nodes

    @property
    def root(self) -> Node:
        return self.tree.root_node

    @property
    def has_error(self) -> bool:
        return self.errors > 0

    @property
    def family(self) -> str:
        return "java" if self.lang == "java" else "csharp" if self.lang == "csharp" else "ts"


_CACHE: "OrderedDict[tuple[str, str], Parsed]" = OrderedDict()
_CACHE_LOCK = threading.Lock()
_CACHE_MAX = 128


def parse(text: str, lang: str) -> Parsed:
    """Parse ``text`` with the grammar of ``lang`` (cached by content hash)."""
    if lang not in LANGS:
        raise ValueError(f"unsupported language {lang!r}")
    key = (lang, hashlib.sha1(text.encode("utf-8", "surrogatepass")).hexdigest())
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
        if hit is not None:
            _CACHE.move_to_end(key)
            return hit
    src = text.encode("utf-8", "replace")
    tree = _parser(lang).parse(src)
    res = Parsed(tree, lang, lang, error_count(tree.root_node))
    if lang == "js" and res.errors:
        t2 = _parser("tsx").parse(src)
        e2 = error_count(t2.root_node)
        if e2 < res.errors:
            res = Parsed(t2, "tsx", lang, e2)
    with _CACHE_LOCK:
        _CACHE[key] = res
        while len(_CACHE) > _CACHE_MAX:
            _CACHE.popitem(last=False)
    return res


# ---- generic node helpers -----------------------------------------------------------------
def text(node: Node | None) -> str:
    return node.text.decode("utf-8", "replace") if node is not None else ""


def line(node: Node) -> int:
    return node.start_point[0] + 1


def end_line(node: Node) -> int:
    return node.end_point[0] + 1


def _is_err(n: Node) -> bool:
    return n.type == "ERROR" or n.is_missing


def error_count(node: Node) -> int:
    n = 0
    stack = [node]
    while stack:
        cur = stack.pop()
        if cur.type == "ERROR" or cur.is_missing:
            n += 1
        if cur.has_error or cur.type == "ERROR":
            stack.extend(cur.children)
    return n


def walk(node: Node, skip_errors: bool = True):
    """Pre-order DFS; with ``skip_errors`` ERROR/MISSING nodes and their subtrees are skipped."""
    stack = [node]
    while stack:
        cur = stack.pop()
        if skip_errors and _is_err(cur):
            continue
        yield cur
        stack.extend(reversed(cur.children))


def find_all(node: Node, types, skip_errors: bool = True) -> list[Node]:
    types = {types} if isinstance(types, str) else set(types)
    return [n for n in walk(node, skip_errors) if n.type in types]


def named_children(node: Node) -> list[Node]:
    return [c for c in node.children if c.is_named and c.type not in ("comment", "line_comment",
                                                                      "block_comment")]


# ---- values -------------------------------------------------------------------------------
@dataclass(frozen=True)
class Ref:
    """Identifier / member reference ``A.B.C`` (resolved later through a symbol index)."""
    name: str


@dataclass(frozen=True)
class TypeRef:
    """``X.class`` / ``typeof(X)``."""
    name: str


@dataclass(frozen=True)
class Hole:
    """Interpolation hole inside a template/interpolated string."""
    expr: str


@dataclass(frozen=True)
class Template:
    parts: tuple  # str | Hole


@dataclass(frozen=True)
class Concat:
    """``a + b + c`` string concatenation (parts are values)."""
    parts: tuple


@dataclass(frozen=True)
class Expr:
    """Any other expression (raw text)."""
    text: str


@dataclass
class Args:
    positional: list = field(default_factory=list)
    named: dict = field(default_factory=dict)

    def get(self, *names, pos: int | None = None, default=None):
        for n in names:
            if n in self.named:
                return self.named[n]
        if pos is not None and pos < len(self.positional):
            return self.positional[pos]
        return default


@dataclass
class Annotation:
    """Java annotation / C# attribute / TS decorator."""
    name: str          # simple name (C# ``Attribute`` suffix stripped)
    full_name: str
    line: int
    node: Node
    args: Args


_ESC = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v", "0": "\0",
        "\\": "\\", '"': '"', "'": "'", "`": "`", "$": "$", "a": "\a", "{": "{", "}": "}",
        "/": "/"}


def unescape(s: str, lang: str = "java") -> str:
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c != "\\" or i + 1 >= n:
            out.append(c)
            i += 1
            continue
        nx = s[i + 1]
        if nx == "u" and i + 2 < n and s[i + 2] == "{":
            j = s.find("}", i + 3)
            if j > 0:
                try:
                    out.append(chr(int(s[i + 3:j], 16)))
                    i = j + 1
                    continue
                except ValueError:
                    pass
        if nx == "u" and re.fullmatch(r"[0-9a-fA-F]{4}", s[i + 2:i + 6]):
            out.append(chr(int(s[i + 2:i + 6], 16)))
            i += 6
            continue
        if nx == "x" and re.fullmatch(r"[0-9a-fA-F]{2}", s[i + 2:i + 4]):
            out.append(chr(int(s[i + 2:i + 4], 16)))
            i += 4
            continue
        if nx == "s" and lang == "java":
            out.append(" ")
            i += 2
            continue
        if nx == "\n":  # line continuation (JS / Java text block)
            i += 2
            continue
        out.append(_ESC.get(nx, nx))
        i += 2
    return "".join(out)


def _java_text_block(raw: str) -> str:
    """Java text block content (between the delimiters) -> value (JLS 3.10.6)."""
    body = raw.split("\n", 1)[1] if "\n" in raw else ""
    lines = body.split("\n")
    closing_own_line = lines and lines[-1].strip() == ""
    sig = [ln for ln in lines[:-1] if ln.strip()] + ([lines[-1]] if lines else [])
    indent = min((len(ln) - len(ln.lstrip(" \t")) for ln in sig), default=0)
    out = [ln[indent:].rstrip(" \t") for ln in lines]
    s = "\n".join(out)
    if closing_own_line:
        s = s[: len(s) - len(out[-1])] if out[-1] == "" else s
    return unescape(s, "java")


def _strip_raw_indent(content: str) -> str:
    """C# multi-line raw string: drop first/last line and the closing line's indentation."""
    if "\n" not in content:
        return content
    lines = content.split("\n")
    if lines[0].strip() == "":
        lines = lines[1:]
    last = lines[-1] if lines else ""
    indent = len(last) if last.strip() == "" else 0
    if last.strip() == "":
        lines = lines[:-1]
    return "\n".join(ln[indent:] if ln[:indent].strip() == "" else ln for ln in lines)


_CONTENT = {"string_fragment", "string_literal_content", "string_content",
            "multiline_string_fragment", "raw_string_content"}
_STRING_TYPES = {"string_literal", "string", "template_string", "verbatim_string_literal",
                 "raw_string_literal", "interpolated_string_expression", "character_literal"}


def decode_string(node: Node, lang: str):
    """String literal node -> ``str`` (or ``Template`` when it has interpolation holes);
    ``None`` when the node is not a string literal."""
    t = node.type
    if t not in _STRING_TYPES:
        return None
    if t == "character_literal":
        return unescape(text(node)[1:-1], lang)
    if t == "verbatim_string_literal":
        return text(node)[2:-1].replace('""', '"')
    if lang == "java" and node.children and node.children[0].type == '"""':
        raw = text(node)[3:-3]
        return _java_text_block(raw)
    verbatim = False
    raw_interp = False
    if t == "interpolated_string_expression":
        start = node.children[0] if node.children else None
        st = text(start) if start is not None else ""
        verbatim = "@" in st
        raw_interp = '"""' in text(node)[:8]
    if t == "raw_string_literal":
        content = "".join(text(c) for c in node.children if c.type == "raw_string_content")
        return _strip_raw_indent(content)
    parts: list = []
    for c in node.children:
        ct = c.type
        if ct in _CONTENT:
            s = text(c)
            if verbatim:
                s = s.replace('""', '"')
            if t == "interpolated_string_expression":
                s = s.replace("{{", "{").replace("}}", "}")
            parts.append(s)
        elif ct == "escape_sequence":
            s = text(c)
            if t == "interpolated_string_expression" and s in ("{{", "}}"):
                parts.append(s[0])
            else:
                parts.append(unescape(s, lang))
        elif ct in ("interpolation", "template_substitution"):
            inner = [x for x in c.children if x.type not in ("interpolation_brace", "${", "}", "{",
                                                              "interpolation_format_clause",
                                                              "interpolation_alignment_clause")]
            parts.append(Hole("".join(text(x) for x in inner).strip()))
    if raw_interp and parts and isinstance(parts[0], str):
        parts[0] = parts[0].lstrip("\n")
    merged: list = []
    for p in parts:
        if isinstance(p, str) and merged and isinstance(merged[-1], str):
            merged[-1] += p
        else:
            merged.append(p)
    if any(isinstance(p, Hole) for p in merged):
        return Template(tuple(merged))
    return "".join(merged)


def _flatten_concat(node: Node, lang: str, out: list) -> None:
    if node.type == "binary_expression":
        op = node.child_by_field_name("operator")
        if op is None:
            kids = node.children
            op = kids[1] if len(kids) == 3 else None
        if op is not None and text(op) == "+":
            left = node.child_by_field_name("left") or node.children[0]
            right = node.child_by_field_name("right") or node.children[-1]
            _flatten_concat(left, lang, out)
            _flatten_concat(right, lang, out)
            return
        out.append(Expr(text(node)))  # other operators: never recurse into value_of again
        return
    out.append(value_of(node, lang))


_REF_TYPES = {"identifier", "field_access", "scoped_identifier", "member_access_expression",
              "member_expression", "qualified_name", "this", "property_identifier",
              "type_identifier", "shorthand_property_identifier"}


def _ref_text(node: Node) -> str:
    return re.sub(r"\s+", "", text(node)).replace("?.", ".")


def value_of(node: Node | None, lang: str):
    """Evaluate a literal-ish expression into a python value / Ref / TypeRef / Concat / Template /
    list / dict / Annotation / Expr. Never executes anything."""
    if node is None:
        return None
    t = node.type
    s = decode_string(node, lang)
    if s is not None:
        return s
    if t in ("parenthesized_expression", "as_expression", "satisfies_expression",
             "non_null_expression", "type_assertion", "cast_expression") and named_children(node):
        kids = named_children(node)
        inner = kids[-1] if t == "cast_expression" else kids[0]
        return value_of(inner, lang)
    if t in ("decimal_integer_literal", "hex_integer_literal", "octal_integer_literal",
             "binary_integer_literal", "integer_literal"):
        raw = text(node).rstrip("lLuU").replace("_", "")
        try:
            return int(raw, 0) if not re.fullmatch(r"0\d+", raw) else int(raw, 8)
        except ValueError:
            return Expr(text(node))
    if t in ("decimal_floating_point_literal", "real_literal", "number"):
        raw = text(node).rstrip("fFdDmM").replace("_", "")
        try:
            return int(raw, 0) if re.fullmatch(r"-?(0[xXoObB])?[0-9a-fA-F]+", raw) and "." not in raw \
                else float(raw)
        except ValueError:
            return Expr(text(node))
    if t in ("true", "false"):
        return t == "true"
    if t == "boolean_literal":
        return text(node) == "true"
    if t in ("null_literal", "null", "undefined"):
        return None
    if t == "unary_expression" and text(node).startswith("-"):
        v = value_of(named_children(node)[0], lang) if named_children(node) else None
        return -v if isinstance(v, (int, float)) else Expr(text(node))
    if t == "class_literal":
        kids = named_children(node)
        return TypeRef(text(kids[0]) if kids else text(node)[:-6])
    if t == "typeof_expression":
        kids = named_children(node)
        return TypeRef(text(kids[0]) if kids else "")
    if t in _REF_TYPES:
        return Ref(_ref_text(node))
    if t == "binary_expression":
        parts: list = []
        _flatten_concat(node, lang, parts)
        if len(parts) > 1:
            if all(isinstance(p, str) for p in parts):
                return "".join(parts)
            return Concat(tuple(parts))
        return Expr(text(node))
    if t in ("element_value_array_initializer", "array_initializer", "array",
             "initializer_expression", "collection_expression"):
        return [value_of(c, lang) for c in named_children(node)]
    if t in ("array_creation_expression", "implicit_array_creation_expression"):
        init = [c for c in node.children if c.type == "initializer_expression"]
        return [value_of(c, lang) for c in named_children(init[0])] if init else Expr(text(node))
    if t in ("annotation", "marker_annotation"):
        return _java_annotation(node)
    if t == "object":
        d = {}
        for c in named_children(node):
            if c.type == "pair":
                k = c.child_by_field_name("key")
                kv = decode_string(k, lang) if k is not None else None
                d[kv if isinstance(kv, str) else text(k)] = value_of(c.child_by_field_name("value"),
                                                                     lang)
            elif c.type == "shorthand_property_identifier":
                d[text(c)] = Ref(text(c))
        return d
    if t == "invocation_expression":
        fn = node.child_by_field_name("function")
        if fn is not None and text(fn) == "nameof":
            args = node.child_by_field_name("arguments")
            kids = named_children(args) if args is not None else []
            if kids:
                return text(kids[0]).split(".")[-1]
    if t == "attribute_argument":
        kids = named_children(node)
        return value_of(kids[-1], lang) if kids else None
    return Expr(text(node))


def resolve_value(v, lookup, depth: int = 8, _seen: frozenset = frozenset()):
    """Fold a value into a string using ``lookup(ref_name) -> value | None`` for ``Ref`` parts.
    Returns ``(str | None, unresolved: list[str])``; ``Template`` holes become ``{}``."""
    if isinstance(v, str):
        return v, []
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v), []
    if isinstance(v, Ref):
        if depth <= 0 or v.name in _seen:
            return None, [v.name]
        target = lookup(v.name)
        if target is None:
            return None, [v.name]
        return resolve_value(target, lookup, depth - 1, _seen | {v.name})
    if isinstance(v, Concat):
        out, unresolved = [], []
        for p in v.parts:
            s, u = resolve_value(p, lookup, depth, _seen)
            unresolved += u
            out.append(s if s is not None else "{}")
        return "".join(out), unresolved
    if isinstance(v, Template):
        return "".join(p if isinstance(p, str) else "{}" for p in v.parts), []
    return None, [getattr(v, "text", repr(v))]


# ---- annotations / attributes / decorators -------------------------------------------------
def _java_annotation(node: Node) -> Annotation:
    name_node = node.child_by_field_name("name")
    full = text(name_node) if name_node is not None else text(node).lstrip("@").split("(")[0]
    args = Args()
    al = node.child_by_field_name("arguments")
    if al is not None:
        for c in named_children(al):
            if c.type == "element_value_pair":
                k = c.child_by_field_name("key")
                args.named[text(k)] = value_of(c.child_by_field_name("value"), "java")
            else:
                args.positional.append(value_of(c, "java"))
    return Annotation(full.split(".")[-1], full, line(node), node, args)


def _cs_attribute(node: Node) -> Annotation:
    name_node = node.child_by_field_name("name")
    full = text(name_node) if name_node is not None else text(node).split("(")[0]
    simple = re.sub(r"<.*$", "", full.split(".")[-1])
    if simple.endswith("Attribute") and len(simple) > len("Attribute"):
        simple = simple[: -len("Attribute")]
    args = Args()
    al = [c for c in node.children if c.type == "attribute_argument_list"]
    if al:
        for c in named_children(al[0]):
            if c.type != "attribute_argument":
                continue
            kids = c.children
            if len(kids) >= 3 and kids[0].type == "identifier" and kids[1].type in ("=", ":"):
                args.named[text(kids[0])] = value_of(kids[2], "csharp")
            else:
                nk = named_children(c)
                args.positional.append(value_of(nk[0], "csharp") if nk else None)
    return Annotation(simple, full, line(node), node, args)


def _ts_decorator(node: Node, lang: str) -> Annotation:
    kids = named_children(node)
    target = kids[0] if kids else node
    args = Args()
    if target.type == "call_expression":
        fn = target.child_by_field_name("function")
        full = text(fn)
        al = target.child_by_field_name("arguments")
        if al is not None:
            args.positional = [value_of(c, lang) for c in named_children(al)]
    else:
        full = text(target)
    return Annotation(full.split(".")[-1], full, line(node), node, args)


def parse_args(node: Node, lang: str) -> Args:
    """Arguments of one annotation / attribute / decorator node."""
    return annotation_of(node, lang).args


def annotation_of(node: Node, lang: str) -> Annotation:
    fam = _family(lang)
    if fam == "java":
        return _java_annotation(node)
    if fam == "csharp":
        return _cs_attribute(node)
    return _ts_decorator(node, lang)


def _family(lang: str) -> str:
    return "java" if lang == "java" else "csharp" if lang == "csharp" else "ts"


def annotations(node: Node, lang: str) -> list[Annotation]:
    """Annotations attached to a declaration node (class/method/field/parameter)."""
    fam = _family(lang)
    out: list[Annotation] = []
    if fam == "java":
        for c in node.children:
            if c.type == "modifiers":
                out += [_java_annotation(a) for a in c.children
                        if a.type in ("annotation", "marker_annotation")]
            elif c.type in ("annotation", "marker_annotation"):
                out.append(_java_annotation(c))
        return out
    if fam == "csharp":
        for c in node.children:
            if c.type == "attribute_list":
                out += [_cs_attribute(a) for a in c.children if a.type == "attribute"]
        return out
    # ts / js: decorator children, decorators on the wrapping export statement, and decorators
    # that precede the member as siblings inside a class body
    decs = [c for c in node.children if c.type == "decorator"]
    parent = node.parent
    if parent is not None and parent.type == "export_statement":
        decs = [c for c in parent.children if c.type == "decorator"] + decs
    if parent is not None and parent.type == "class_body":
        prev = node.prev_named_sibling
        pre = []
        while prev is not None and prev.type == "decorator":
            pre.append(prev)
            prev = prev.prev_named_sibling
        decs = list(reversed(pre)) + decs
    return [_ts_decorator(d, lang) for d in decs]


def modifiers(node: Node, lang: str) -> list[str]:
    fam = _family(lang)
    out: list[str] = []
    for c in node.children:
        if fam == "java" and c.type == "modifiers":
            out += [text(m) for m in c.children if m.type not in ("annotation",
                                                                    "marker_annotation")]
        elif fam == "csharp" and c.type == "modifier":
            out.append(text(c))
        elif fam == "ts" and c.type in ("accessibility_modifier", "static", "readonly", "async",
                                        "abstract", "override", "declare"):
            out.append(text(c))
    return out


# ---- declarations -------------------------------------------------------------------------
_TYPE_KINDS = {
    "java": {"class_declaration": "class", "interface_declaration": "interface",
             "enum_declaration": "enum", "record_declaration": "record",
             "annotation_type_declaration": "annotation"},
    "csharp": {"class_declaration": "class", "interface_declaration": "interface",
               "struct_declaration": "struct", "record_declaration": "record",
               "record_struct_declaration": "record", "enum_declaration": "enum"},
    "ts": {"class_declaration": "class", "abstract_class_declaration": "class", "class": "class",
           "interface_declaration": "interface", "enum_declaration": "enum",
           "type_alias_declaration": "type"},
}


@dataclass
class Param:
    name: str
    type: str | None
    annotations: list[Annotation]
    optional: bool
    default: str | None
    line: int
    node: Node
    modifiers: list[str] = field(default_factory=list)


@dataclass
class TypeDecl:
    name: str
    qualified: str
    kind: str
    node: Node
    body: Node | None
    line: int
    end_line: int
    annotations: list[Annotation]
    modifiers: list[str]
    extends: list[str]
    type_params: list[str]
    params: list[Param]     # record / primary-constructor parameters
    outer: str | None


@dataclass
class MethodDecl:
    name: str
    kind: str               # method | constructor | function | arrow
    node: Node
    line: int
    end_line: int
    params: list[Param]
    return_type: str | None
    annotations: list[Annotation]
    modifiers: list[str]
    body: Node | None
    owner: str | None


@dataclass
class FieldDecl:
    name: str
    type: str | None
    value: Node | None
    annotations: list[Annotation]
    modifiers: list[str]
    line: int
    node: Node
    optional: bool = False


def _type_text(node: Node | None) -> str | None:
    if node is None:
        return None
    s = text(node).strip()
    if node.type == "type_annotation" or s.startswith(":"):
        s = s.lstrip(":").strip()
    return re.sub(r"\s+", " ", s) or None


def _heritage(node: Node, fam: str) -> list[str]:
    out: list[str] = []
    if fam == "java":
        for f in ("superclass", "interfaces"):
            c = node.child_by_field_name(f)
            if c is not None:
                out += [text(x) for x in walk(c) if x.type in ("type_identifier", "generic_type",
                                                               "scoped_type_identifier")
                        and x.parent is not None and x.parent.type in ("superclass", "type_list")]
    elif fam == "csharp":
        for c in node.children:
            if c.type == "base_list":
                out += [text(x) for x in named_children(c)]
    else:
        for c in node.children:
            if c.type in ("class_heritage", "extends_type_clause"):
                for cl in walk(c):
                    if cl.type in ("extends_clause", "implements_clause", "extends_type_clause"):
                        out += [text(x) for x in named_children(cl)]
    return out


def _type_params(node: Node) -> list[str]:
    tp = node.child_by_field_name("type_parameters")
    if tp is None:
        tp = next((c for c in node.children if c.type in ("type_parameter_list", "type_parameters")),
                  None)
    if tp is None:
        return []
    out = []
    for c in named_children(tp):
        if c.type == "type_parameter":
            n = c.child_by_field_name("name")
            out.append(text(n) if n is not None else text(named_children(c)[0]))
    return out


def params_of(node: Node | None, lang: str) -> list[Param]:
    """Parameters of a method/constructor/function/record (the parameter-list node or its owner)."""
    if node is None:
        return []
    fam = _family(lang)
    plist = node
    if node.type not in ("formal_parameters", "parameter_list"):
        plist = node.child_by_field_name("parameters")
        if plist is None:
            plist = next((c for c in node.children if c.type in ("formal_parameters",
                                                                 "parameter_list")), None)
        if plist is None:
            p = node.child_by_field_name("parameter")
            if p is not None:  # JS arrow fn with a single bare parameter
                return [Param(text(p), None, [], False, None, line(p), p)]
            return []
    out: list[Param] = []
    if fam == "java":
        for c in named_children(plist):
            if c.type not in ("formal_parameter", "spread_parameter"):
                continue
            nm = c.child_by_field_name("name")
            if nm is None:
                vd = next((x for x in c.children if x.type == "variable_declarator"), None)
                nm = vd.child_by_field_name("name") if vd is not None else None
            ty = c.child_by_field_name("type")
            if ty is None:
                ty = next((x for x in named_children(c) if x.type.endswith("type")
                           or x.type == "type_identifier"), None)
            out.append(Param(text(nm), _type_text(ty), annotations(c, lang), False, None, line(c),
                             c, modifiers(c, lang)))
        return out
    if fam == "csharp":
        group: list[Node] = []

        def flush(nodes: list[Node]) -> None:
            if not nodes:
                return
            if len(nodes) == 1 and nodes[0].type == "parameter":
                c = nodes[0]
                nm = c.child_by_field_name("name")
                ty = c.child_by_field_name("type")
                kids = c.children
                default = None
                for i, k in enumerate(kids):
                    if k.type == "=" and i + 1 < len(kids):
                        default = text(kids[i + 1])
                tyt = _type_text(ty)
                out.append(Param(text(nm), tyt, annotations(c, lang),
                                 bool(default is not None or (tyt or "").endswith("?")), default,
                                 line(c), c, modifiers(c, lang)))
                return
            names = [n for n in nodes if n.type == "identifier"]
            types = [n for n in nodes if n.type not in ("identifier", "params", "attribute_list",
                                                        "modifier")]
            nm = names[-1] if names else nodes[-1]
            out.append(Param(text(nm), _type_text(types[0]) if types else None, [], True, None,
                             line(nodes[0]), nodes[0], ["params"] if any(
                                 n.type == "params" for n in nodes) else []))

        for c in plist.children:
            if c.type in ("(", ")"):
                continue
            if c.type == ",":
                flush(group)
                group = []
                continue
            if c.is_named and c.type != "comment":
                group.append(c)
            elif c.type == "params":
                group.append(c)
        flush(group)
        return out
    # ts / js
    for c in named_children(plist):
        t = c.type
        if t in ("required_parameter", "optional_parameter"):
            pat = c.child_by_field_name("pattern")
            ty = c.child_by_field_name("type")
            val = c.child_by_field_name("value")
            out.append(Param(text(pat), _type_text(ty), annotations(c, lang),
                             t == "optional_parameter" or val is not None,
                             text(val) if val is not None else None, line(c), c,
                             modifiers(c, lang)))
        elif t == "assignment_pattern":
            left = c.child_by_field_name("left")
            right = c.child_by_field_name("right")
            out.append(Param(text(left), None, [], True, text(right), line(c), c))
        elif t in ("identifier", "object_pattern", "array_pattern", "rest_pattern"):
            out.append(Param(text(c), None, [], t == "rest_pattern", None, line(c), c))
    return out


def type_decls(parsed: Parsed) -> list[TypeDecl]:
    """Every type declaration (nested included, pre-order), skipping error subtrees."""
    fam = parsed.family
    kinds = _TYPE_KINDS[fam]
    out: list[TypeDecl] = []

    def visit(node: Node, outer: str | None) -> None:
        for c in node.children:
            if _is_err(c):
                continue
            if c.type in kinds:
                nm = c.child_by_field_name("name")
                name = text(nm) if nm is not None else ""
                q = f"{outer}.{name}" if outer else name
                body = c.child_by_field_name("body")
                if fam == "csharp" and c.type == "record_declaration" and body is None:
                    body = next((x for x in c.children if x.type == "declaration_list"), None)
                rec_params = params_of(c, parsed.lang) if (
                    c.type in ("record_declaration", "record_struct_declaration")
                    or (fam == "csharp" and any(x.type == "parameter_list" for x in c.children))
                ) else []
                out.append(TypeDecl(name, q, kinds[c.type], c, body, line(c), end_line(c),
                                    annotations(c, parsed.lang), modifiers(c, parsed.lang),
                                    _heritage(c, fam), _type_params(c), rec_params, outer))
                visit(body if body is not None else c, q)
            else:
                visit(c, outer)

    visit(parsed.root, None)
    return out


_METHOD_TYPES = {
    "java": {"method_declaration": "method", "constructor_declaration": "constructor",
             "compact_constructor_declaration": "constructor"},
    "csharp": {"method_declaration": "method", "constructor_declaration": "constructor",
               "local_function_statement": "function"},
    "ts": {"method_definition": "method", "method_signature": "method",
           "abstract_method_signature": "method"},
}


def _members(td: TypeDecl) -> list[Node]:
    if td.body is None:
        return []
    out = []
    for c in td.body.children:
        if _is_err(c):
            continue
        if c.type == "enum_body_declarations":  # java enum members
            out += [x for x in c.children if not _is_err(x)]
        else:
            out.append(c)
    return out


def methods(td: TypeDecl, lang: str) -> list[MethodDecl]:
    """Methods/constructors declared directly in ``td``."""
    fam = _family(lang)
    kinds = _METHOD_TYPES[fam]
    out = []
    for c in _members(td):
        if c.type not in kinds:
            continue
        nm = c.child_by_field_name("name")
        name = text(nm)
        kind = kinds[c.type]
        if fam == "ts" and name == "constructor":
            kind = "constructor"
        if fam == "java":
            rt = c.child_by_field_name("type")
        elif fam == "csharp":
            rt = c.child_by_field_name("returns") or c.child_by_field_name("type")
        else:
            rt = c.child_by_field_name("return_type")
        out.append(MethodDecl(name, kind, c, line(c), end_line(c), params_of(c, lang),
                              _type_text(rt) if kind != "constructor" else None,
                              annotations(c, lang), modifiers(c, lang),
                              c.child_by_field_name("body"), td.qualified))
    return out


def fields(td: TypeDecl, lang: str) -> list[FieldDecl]:
    """Fields / properties declared directly in ``td`` (one entry per declarator)."""
    fam = _family(lang)
    out = []
    for c in _members(td):
        t = c.type
        if fam in ("java", "csharp") and t == "field_declaration":
            holder = c if fam == "java" else next(
                (x for x in c.children if x.type == "variable_declaration"), c)
            ty = holder.child_by_field_name("type")
            for vd in holder.children:
                if vd.type != "variable_declarator":
                    continue
                nm = vd.child_by_field_name("name")
                if nm is None:
                    nm = next((x for x in vd.children if x.type == "identifier"), None)
                val = vd.child_by_field_name("value")
                if val is None and fam == "csharp":
                    kids = vd.children
                    for i, k in enumerate(kids):
                        if k.type == "=" and i + 1 < len(kids):
                            val = kids[i + 1]
                        elif k.type == "equals_value_clause":
                            val = named_children(k)[0] if named_children(k) else None
                out.append(FieldDecl(text(nm), _type_text(ty), val, annotations(c, lang),
                                     modifiers(c, lang), line(vd), c))
        elif fam == "csharp" and t == "property_declaration":
            out.append(FieldDecl(text(c.child_by_field_name("name")),
                                 _type_text(c.child_by_field_name("type")),
                                 c.child_by_field_name("value"), annotations(c, lang),
                                 modifiers(c, lang), line(c), c,
                                 (_type_text(c.child_by_field_name("type")) or "").endswith("?")))
        elif fam == "java" and t == "constant_declaration":
            ty = c.child_by_field_name("type")
            for vd in c.children:
                if vd.type == "variable_declarator":
                    out.append(FieldDecl(text(vd.child_by_field_name("name")), _type_text(ty),
                                         vd.child_by_field_name("value"), annotations(c, lang),
                                         modifiers(c, lang), line(vd), c))
        elif fam == "ts" and t in ("public_field_definition", "property_signature",
                                   "field_definition"):
            nm = c.child_by_field_name("name") or c.child_by_field_name("property")
            out.append(FieldDecl(text(nm), _type_text(c.child_by_field_name("type")),
                                 c.child_by_field_name("value"), annotations(c, lang),
                                 modifiers(c, lang), line(c), c,
                                 any(x.type == "?" for x in c.children)))
    return out


def enum_members(td: TypeDecl, lang: str) -> list[tuple[str, object, int]]:
    """(name, value or None, line) for an enum declaration."""
    out = []
    if td.body is None:
        return out
    for c in td.body.children:
        if c.type in ("enum_constant", "enum_member_declaration"):
            nm = c.child_by_field_name("name") or next(
                (x for x in c.children if x.type == "identifier"), None)
            val = c.child_by_field_name("value")
            out.append((text(nm), value_of(val, lang) if val is not None else None, line(c)))
        elif c.type == "enum_assignment":
            out.append((text(c.child_by_field_name("name")),
                        value_of(c.child_by_field_name("value"), lang), line(c)))
        elif c.type == "property_identifier":
            out.append((text(c), None, line(c)))
    return out


def functions(parsed: Parsed) -> list[MethodDecl]:
    """TS/JS functions: declarations and ``const f = (…) => …`` / ``function`` expressions,
    at module level or nested (class methods excluded)."""
    if parsed.family != "ts":
        return []
    lang = parsed.lang
    out = []
    for n in walk(parsed.root):
        if n.type in ("function_declaration", "generator_function_declaration"):
            out.append(MethodDecl(text(n.child_by_field_name("name")), "function", n, line(n),
                                  end_line(n), params_of(n, lang),
                                  _type_text(n.child_by_field_name("return_type")), [], [],
                                  n.child_by_field_name("body"), None))
        elif n.type == "variable_declarator":
            val = n.child_by_field_name("value")
            if val is not None and val.type in ("arrow_function", "function_expression",
                                                "function"):
                out.append(MethodDecl(text(n.child_by_field_name("name")),
                                      "arrow" if val.type == "arrow_function" else "function",
                                      val, line(n), end_line(val), params_of(val, lang),
                                      _type_text(val.child_by_field_name("return_type")), [],
                                      modifiers(val, lang), val.child_by_field_name("body"),
                                      None))
    return out
