"""C# type-name normalization for ``dotnet.aspnet`` (docs/EXTRACTORS.md#schema).

``norm_type("Task<ActionResult<List<FooDto>>>")`` -> ``"FooDto[]"``; primitives map to
``string | integer | number | boolean | date | datetime | uuid | binary | object``;
``schema_refs`` returns the domain type names a type text references (for schema collection).
"""
from __future__ import annotations

import re

WRAPPERS = {"Task", "ValueTask", "ActionResult", "Nullable", "Ok", "Created",
            "CreatedAtRoute", "Accepted", "ApiResponse", "IApiResponse", "Response"}
NO_BODY = {"IActionResult", "ActionResult", "IResult", "void", "Task", "ValueTask",
           "HttpResponseData", "HttpResponseMessage", "IHttpActionResult", "Results",
           "NoContent", "NotFound", "BadRequest", "RestResponse", "IRestResponse"}
COLLECTIONS = {"List", "IList", "IEnumerable", "ICollection", "IReadOnlyList",
               "IReadOnlyCollection", "HashSet", "ISet", "IAsyncEnumerable", "Collection",
               "ObservableCollection", "IQueryable", "ImmutableList", "ImmutableArray"}
MAPS = {"Dictionary", "IDictionary", "IReadOnlyDictionary", "ConcurrentDictionary",
        "SortedDictionary", "ImmutableDictionary"}
PRIMITIVES = {
    "string": "string", "String": "string", "char": "string", "Char": "string",
    "int": "integer", "Int32": "integer", "long": "integer", "Int64": "integer",
    "short": "integer", "Int16": "integer", "byte": "integer", "Byte": "integer",
    "uint": "integer", "ulong": "integer", "ushort": "integer", "sbyte": "integer",
    "UInt32": "integer", "UInt64": "integer", "nint": "integer",
    "decimal": "number", "Decimal": "number", "double": "number", "Double": "number",
    "float": "number", "Single": "number",
    "bool": "boolean", "Boolean": "boolean",
    "DateTime": "datetime", "DateTimeOffset": "datetime", "DateOnly": "date",
    "TimeOnly": "string", "TimeSpan": "string",
    "Guid": "uuid",
    "object": "object", "Object": "object", "dynamic": "object", "JObject": "object",
    "JToken": "object", "JsonElement": "object", "JsonNode": "object", "JsonDocument": "object",
    "ExpandoObject": "object", "JArray": "object[]",
    "IFormFile": "binary", "IFormFileCollection": "binary[]", "Stream": "binary",
    "byte[]": "binary", "Byte[]": "binary",
}
VALUE_TYPES = {"int", "Int32", "long", "Int64", "short", "Int16", "byte", "Byte", "uint", "ulong",
               "ushort", "sbyte", "decimal", "Decimal", "double", "Double", "float", "Single",
               "bool", "Boolean", "DateTime", "DateTimeOffset", "DateOnly", "TimeOnly",
               "TimeSpan", "Guid", "char", "Char"}
SIMPLE = set(PRIMITIVES) - {"object", "Object", "dynamic", "JObject", "JToken", "JsonElement",
                            "JsonNode", "JsonDocument", "ExpandoObject", "JArray", "IFormFile",
                            "IFormFileCollection", "Stream"}


def split_generic(t: str) -> tuple[str, list[str]]:
    """``A<B, C<D>>`` -> (``A``, [``B``, ``C<D>``]); namespaces stripped from the name."""
    t = t.strip()
    if "<" not in t or not t.endswith(">"):
        return t.split(".")[-1] if not t.endswith("]") else t, []
    i = t.index("<")
    name = t[:i].strip().split(".")[-1]
    inner = t[i + 1:-1]
    args, depth, cur = [], 0, ""
    for ch in inner:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            args.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        args.append(cur.strip())
    return name, args


def clean(t: str | None) -> str:
    t = re.sub(r"\s+", " ", (t or "").replace("global::", "")).strip()
    return t


def is_nullable(t: str | None) -> bool:
    t = clean(t)
    return t.endswith("?") or t.startswith("Nullable<")


def norm_type(t: str | None) -> str | None:
    """Normalized type text, or None for no body / unknown."""
    t = clean(t)
    if not t:
        return None
    if t.endswith("?"):
        t = t[:-1]
    if t.startswith("(") and t.endswith(")"):  # tuples
        return "object"
    if t.endswith("[]"):
        if t in PRIMITIVES:
            return PRIMITIVES[t]
        inner = norm_type(t[:-2])
        return f"{inner}[]" if inner else None
    name, args = split_generic(t)
    if name in NO_BODY and not args:
        return None
    if name in WRAPPERS and args:
        return norm_type(args[0])
    if name in COLLECTIONS and args:
        inner = norm_type(args[0])
        return f"{inner}[]" if inner else None
    if name in MAPS and len(args) == 2:
        return f"map<{norm_type(args[0]) or 'any'},{norm_type(args[1]) or 'any'}>"
    if name in PRIMITIVES:
        return PRIMITIVES[name]
    if args:
        return f"{name}<{','.join(norm_type(a) or 'any' for a in args)}>"
    return name


def schema_refs(t: str | None) -> list[str]:
    """Domain type names referenced by a type text (wrappers/collections unwrapped)."""
    t = clean(t)
    if not t:
        return []
    if t.endswith("?"):
        t = t[:-1]
    if t.endswith("[]"):
        return schema_refs(t[:-2])
    if t.startswith("("):
        return []
    name, args = split_generic(t)
    out: list[str] = []
    if name in WRAPPERS or name in COLLECTIONS or name in MAPS:
        for a in args:
            out += schema_refs(a)
        return out
    if name in PRIMITIVES or name in NO_BODY or not re.match(r"^[A-Za-z_]\w*$", name):
        return out
    out.append(name)
    for a in args:
        out += schema_refs(a)
    return out


def is_simple(t: str | None, enums: set[str] = frozenset()) -> bool:
    t = clean(t).rstrip("?")
    if t.endswith("[]"):
        return is_simple(t[:-2], enums)
    name, args = split_generic(t)
    if name in COLLECTIONS and args:
        return is_simple(args[0], enums)
    if name == "Nullable" and args:
        return is_simple(args[0], enums)
    return name in SIMPLE or name in enums


def is_value_type(t: str | None, enums: set[str] = frozenset()) -> bool:
    t = clean(t)
    if t.endswith("?") or t.startswith("Nullable<"):
        return False
    return t in VALUE_TYPES or t in enums
