"""tree-sitter layer (extractors/syntax.py)."""
from __future__ import annotations

from importlib.metadata import version

from repo_docs.extractors import syntax as sx


def _anns(parsed, type_name):
    return [d for d in sx.type_decls(parsed) if d.name == type_name][0]


def test_grammars_pinned_and_tag():
    assert version("tree-sitter") == "0.26.0"
    assert version("tree-sitter-java") == "0.23.5"
    assert version("tree-sitter-c-sharp") == "0.23.5"
    assert version("tree-sitter-typescript") == "0.23.2"
    assert version("tree-sitter-javascript") == "0.25.0"
    assert sx.GRAMMAR_TAG.startswith("ts0.26.0.")
    assert sx.versioned("0.1.0", "java") == "0.1.0+ts0.26.0.java0.23.5"


def test_lang_for_path():
    assert sx.lang_for_path("a/B.java") == "java"
    assert sx.lang_for_path("a/b.cs") == "csharp"
    assert sx.lang_for_path("a/b.tsx") == "tsx"
    assert sx.lang_for_path("a/b.d.ts") is None
    assert sx.lang_for_path("a/b.mjs") == "js"


JAVA = '''package x;
@RestController
@RequestMapping(value = {"/a", "/b"}, method = RequestMethod.GET)
public class C {
    static final String BASE = Endpoints.BASE + "/v1";
    String tb = """
        hello
          world\\
         end""";
    @GetMapping(path = AppConstants.X.LOCATION_URI + "/state", produces = MediaType.APPLICATION_JSON_VALUE)
    @ApiResponse(responseCode = "404", content = @Content(schema = @Schema(implementation = Err.class)))
    public ResponseEntity<List<Out>> get(@PathVariable("id") final String id, @RequestParam(required = false) int q) {
        return null;
    }
    static class Inner { enum E { A, B } }
}
'''


def test_java_annotations_and_methods():
    p = sx.parse(JAVA, "java")
    assert not p.has_error
    c = _anns(p, "C")
    names = [a.name for a in c.annotations]
    assert names == ["RestController", "RequestMapping"]
    rm = c.annotations[1].args
    assert rm.get("value") == ["/a", "/b"] and rm.get("method") == sx.Ref("RequestMethod.GET")
    assert c.annotations[1].line == 3
    m = sx.methods(c, "java")[0]
    assert m.name == "get" and m.line == 10 and m.return_type == "ResponseEntity<List<Out>>"
    ga = m.annotations[0].args.get("path")
    assert isinstance(ga, sx.Concat) and ga.parts == (sx.Ref("AppConstants.X.LOCATION_URI"),
                                                      "/state")
    nested = m.annotations[1].args.get("content")
    assert isinstance(nested, sx.Annotation) and nested.name == "Content"
    assert nested.args.get("schema").args.get("implementation") == sx.TypeRef("Err")
    assert [(pp.name, pp.type) for pp in m.params] == [("id", "String"), ("q", "int")]
    assert m.params[0].annotations[0].args.positional == ["id"]
    assert m.params[1].annotations[0].args.get("required") is False
    flds = {f.name: f for f in sx.fields(c, "java")}
    assert sx.value_of(flds["tb"].value, "java") == "hello\n  world end"
    base = sx.value_of(flds["BASE"].value, "java")
    folded, unresolved = sx.resolve_value(base, {"Endpoints.BASE": "/api"}.get)
    assert folded == "/api/v1" and unresolved == []
    assert [d.qualified for d in sx.type_decls(p)] == ["C", "C.Inner", "C.Inner.E"]
    e = [d for d in sx.type_decls(p) if d.name == "E"][0]
    assert [n for n, _, _ in sx.enum_members(e, "java")] == ["A", "B"]


CS = '''namespace N;
[ApiController]
[Route("api/service/appointment-request")]
public class AppointmentController(IService svc) : ControllerBase
{
    private const string Verb = @"a""b";
    [HttpPost]
    [Route("create")]
    [SwaggerResponse(statusCode: 200, type: typeof(Output))]
    [ProducesResponseType(typeof(Out), StatusCodes.Status201Created)]
    public async Task<ActionResult<Out>> Create([FromBody] Req r, string? q = null, int limit = 5)
    {
        var s = $"x{r.Id}y{{z}}";
        var raw = """
            raw "text"
            """;
        return Ok();
    }
    public string? Name { get; set; }
}
public record R(int A, string? B);
'''


def test_csharp_attributes_strings_lines():
    p = sx.parse(CS, "csharp")
    assert not p.has_error
    c = _anns(p, "AppointmentController")
    assert [a.name for a in c.annotations] == ["ApiController", "Route"]
    assert c.annotations[1].args.positional == ["api/service/appointment-request"]
    assert c.annotations[1].line == 3
    assert [x.name for x in c.params] == ["svc"]  # primary constructor
    m = sx.methods(c, "csharp")[0]
    assert [(a.name, a.line) for a in m.annotations][:2] == [("HttpPost", 7), ("Route", 8)]
    sw = m.annotations[2].args
    assert sw.get("statusCode") == 200 and sw.get("type") == sx.TypeRef("Output")
    assert m.annotations[3].args.positional == [sx.TypeRef("Out"),
                                                sx.Ref("StatusCodes.Status201Created")]
    assert m.return_type == "Task<ActionResult<Out>>"
    ps = m.params
    assert [(x.name, x.type, x.optional) for x in ps] == [("r", "Req", False),
                                                          ("q", "string?", True),
                                                          ("limit", "int", True)]
    assert ps[0].annotations[0].name == "FromBody"
    flds = {f.name: f for f in sx.fields(c, "csharp")}
    assert sx.value_of(flds["Verb"].value, "csharp") == 'a"b'
    assert flds["Name"].optional
    strs = [sx.decode_string(n, "csharp") for n in sx.find_all(
        p.root, ("interpolated_string_expression", "raw_string_literal"))]
    assert strs[0] == sx.Template(("x", sx.Hole("r.Id"), "y{z}"))
    assert strs[1] == 'raw "text"'
    rec = _anns(p, "R")
    assert rec.kind == "record" and [x.name for x in rec.params] == ["A", "B"]


TS = '''@Controller('bookings')
export class BookingsController {
  constructor(private readonly http: HttpService) {}
  @Get(':id')
  @ApiResponse({ status: 200, type: [Out] })
  async get(@Param('id') id: string, q?: number): Promise<Out> {
    const u = `${base}/a/${id}`;
    return 'it\\'s';
  }
}
export enum API_ROUTE { BOOKINGS = 'bookings', X }
export const fn = async (a: string): Promise<void> => {};
'''


def test_typescript_decorators_templates():
    p = sx.parse(TS, "ts")
    assert not p.has_error
    c = _anns(p, "BookingsController")
    assert [(a.name, a.args.positional) for a in c.annotations] == [("Controller", ["bookings"])]
    ms = {m.name: m for m in sx.methods(c, "ts")}
    g = ms["get"]
    assert [(a.name, a.line) for a in g.annotations] == [("Get", 4), ("ApiResponse", 5)]
    assert g.annotations[1].args.positional == [{"status": 200, "type": [sx.Ref("Out")]}]
    assert [(x.name, x.type, x.optional) for x in g.params] == [("id", "string", False),
                                                                ("q", "number", True)]
    assert g.params[0].annotations[0].args.positional == ["id"]
    assert g.return_type == "Promise<Out>"
    tmpl = [sx.decode_string(n, "ts") for n in sx.find_all(p.root, "template_string")][0]
    assert tmpl == sx.Template((sx.Hole("base"), "/a/", sx.Hole("id")))
    assert sx.resolve_value(tmpl, lambda n: None)[0] == "{}/a/{}"
    strs = [sx.decode_string(n, "ts") for n in sx.find_all(p.root, "string")]
    assert "it's" in strs
    e = _anns(p, "API_ROUTE")
    assert sx.enum_members(e, "ts")[0][:2] == ("BOOKINGS", "bookings")
    assert [f.name for f in sx.functions(p)] == ["fn"]


def test_jsx_in_js_falls_back_to_tsx():
    # cbs-admin-portal src/pages/*.js contain JSX plus TS-only syntax in places
    src = "const A = (p) => <div>{p.x as any}</div>;\nexport default A;\n"
    p = sx.parse(src, "js")
    assert p.requested == "js" and p.lang == "tsx" and not p.has_error
    plain = sx.parse("const B = () => <div className='x'>{y}</div>;\n", "js")
    assert plain.lang == "js" and not plain.has_error


def test_error_tree_still_yields_clean_subtrees():
    src = ("@RestController\nclass Good {\n  @GetMapping(\"/ok\")\n  void ok() {}\n}\n"
           "class Broken {\n  void x( {\n}\n")
    p = sx.parse(src, "java")
    assert p.has_error and p.errors >= 1
    good = [d for d in sx.type_decls(p) if d.name == "Good"]
    assert good and sx.methods(good[0], "java")[0].annotations[0].args.positional == ["/ok"]
    assert all(n.type != "ERROR" for n in sx.walk(p.root))


def test_parse_is_cached():
    assert sx.parse("class Z {}", "java") is sx.parse("class Z {}", "java")
