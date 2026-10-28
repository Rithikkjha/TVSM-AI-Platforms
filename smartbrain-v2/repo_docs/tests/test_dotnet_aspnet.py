"""dotnet.aspnet extractor over trimmed reproductions of TVS-CS .NET repos (sources cited in each
fixture file under tests/fixtures/dotnet/) plus small synthetic snippets for constructs the clones
do not use (RestSharp, Refit, Flurl, minimal APIs, IOptions). Every secret value is fake; tests
assert they never reach the items."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from repo_docs.extractors.base import RepoContext
from repo_docs.extractors.dotnet_aspnet import DotnetAspnetExtractor
from repo_docs.extractors.registry import SHARED
from repo_docs.inventory_schema import KINDS, validate_item
from repo_docs.phase2_extract import merge_items
from repo_docs.repo_type import classify_repo

FIX = Path(__file__).parent / "fixtures" / "dotnet"
RD = Path(__file__).resolve().parents[1]
CLONES = RD / "repos" / "TVS-CS"
FAKE_SECRETS = ("fakePaySbKey0123456789abcdef=", "fakeBs2SbKey0123456789abcdef=",
                "fakeBs2DbPassw0rd")


def fx(rel: str) -> str:
    return (FIX / rel).read_text()


def run(files: dict, stacks=(("dotnet", "."),), shared=True):
    ctx = RepoContext.for_test(files, list(stacks))
    shared_items = []
    if shared:
        for cls in SHARED:
            shared_items += cls().extract(ctx, None).items
    ex = DotnetAspnetExtractor()
    items, touched = [], {}
    for _stack, sub in stacks:
        res = ex.extract(ctx, sub)
        items += res.items
        touched.update(res.touched)
    merged = merge_items(items)
    for it in merged:
        assert validate_item(it, ctx.ledger_index, ctx.line) == [], it.id
        assert set(it.attributes) == set(KINDS[it.kind])
    return ctx, merged, touched, shared_items


def by_id(items):
    return {i.id: i for i in items}


def lines(it):
    return sorted({e.line for e in it.evidence})


def no_secrets(items):
    blob = json.dumps([i.to_dict() for i in items])
    for s in FAKE_SECRETS:
        assert s not in blob


# ---- appointment-booking-service AppointmentController (acceptance) ------------------------
APPT = {
    "src/Appointment.API/Controllers/AppointmentController.cs": fx(
        "appointment/AppointmentController.cs"),
    "src/Appointment.Application/Appointment/Dtos/AppointmentSlotRequestDto.cs": fx(
        "appointment/AppointmentSlotRequestDto.cs"),
}
APPT_STACKS = (("dotnet", "src/Appointment.API"), ("dotnet", "src/Appointment.Application"))
SUB = "src/Appointment.API"


def _check_appointment(items, path):
    ids = by_id(items)
    want = {
        f"inbound_http:{SUB}:POST:/api/service/appointment-request/create": [32, 40, 41],
        f"inbound_http:{SUB}:GET:/api/service/appointment-request/fetch/{{}}": [32, 80],
        f"inbound_http:{SUB}:GET:/api/service/health/{{}}": [121, 122],
        f"inbound_http:{SUB}:POST:/api/service/appointment/fetch/slot": [155],
        f"inbound_http:{SUB}:POST:/api/service/appointment/create": [190, 191],
        f"inbound_http:{SUB}:PUT:/api/service/appointment/{{}}/update": [224, 225],
        f"inbound_http:{SUB}:POST:/api/service/appointment/fetch": [272, 273],
    }
    inbound = {i.id for i in items if i.kind == "inbound_http"}
    assert set(want) <= inbound
    for iid, ls in want.items():
        assert lines(ids[iid]) == ls, iid
        assert {e.file for e in ids[iid].evidence} == {path}
    create = ids[f"inbound_http:{SUB}:POST:/api/service/appointment-request/create"].attributes
    assert create["path"] == "/api/service/appointment-request/create"
    assert create["handler"] == "AppointmentController.CreateAppointment"
    assert create["framework"] == "aspnet-core"
    ann = {r["status"]: r for r in create["responses"] if r["from"] == "annotation"}
    assert sorted(ann) == [200, 400, 409, 500]
    assert ann[200]["schema"] == "Output"
    fetch = ids[f"inbound_http:{SUB}:GET:/api/service/appointment-request/fetch/{{}}"].attributes
    assert fetch["path"] == "/api/service/appointment-request/fetch/{frameNo}"
    params = {p["name"]: p for p in fetch["params"]}
    assert params["frameNo"] == {"name": "frameNo", "in": "path", "type": "string",
                                 "required": True}
    for n, t in (("referenceNo", "string"), ("fromDate", "datetime"), ("toDate", "datetime"),
                 ("dealerId", "integer"), ("branchId", "integer"), ("limit", "integer")):
        assert params[n] == {"name": n, "in": "query", "type": t, "required": False}
    health = ids[f"inbound_http:{SUB}:GET:/api/service/health/{{}}"].attributes
    assert health["path"] == "/api/service/health/{dealerId}"
    assert health["params"] == [{"name": "dealerId", "in": "path", "type": "integer",
                                 "required": True}]
    slot = ids[f"inbound_http:{SUB}:POST:/api/service/appointment/fetch/slot"].attributes
    assert slot["path"] == "/api/service/appointment/fetch/slot"
    assert slot["request"] == "AppointmentSlotRequestDto"
    upd = ids[f"inbound_http:{SUB}:PUT:/api/service/appointment/{{}}/update"].attributes
    assert [r["status"] for r in upd["responses"]] == [200, 400, 404]


def test_appointment_controller_fixture_routes():
    path = "src/Appointment.API/Controllers/AppointmentController.cs"
    _ctx, items, touched, _ = run(APPT, APPT_STACKS)
    _check_appointment(items, path)
    assert touched[path].parse == "full"


def test_appointment_schema_dataannotations_record_enum():
    _ctx, items, _t, _ = run(APPT, APPT_STACKS)
    ids = by_id(items)
    dto = ids["schema:src/Appointment.Application:AppointmentSlotRequestDto"].attributes
    f = {x["name"]: x for x in dto["fields"]}
    assert dto["schema_kind"] == "class" and dto["resolved"] is True
    assert dto["defined_in"].endswith("AppointmentSlotRequestDto.cs:8")
    assert f["dealerId"]["required"] is True and f["dealerId"]["type"] == "integer"
    assert f["fromDate"]["json_name"] == "from_date" and f["fromDate"]["nullable"] is True
    assert f["fromDate"]["required"] is False
    assert f["channel"]["validation"] == {"max_length": 20, "min_length": 2}
    assert "Internal" not in f
    assert f["Kind"]["type"] == "SlotKind"
    kind = ids["schema:src/Appointment.Application:SlotKind"].attributes
    assert kind["enum_values"] == ["Morning=1", "Evening=2"]
    out = ids["schema:src/Appointment.Application:Output"].attributes
    assert [x["name"] for x in out["fields"]] == ["statusCode", "message"]
    rec = ids["schema:src/Appointment.Application:Success"].attributes
    assert rec["schema_kind"] == "record"
    assert [x["name"] for x in rec["fields"]] == ["appointmentId", "appointmentDateTime"]


@pytest.mark.skipif(not (CLONES / "appointment-booking-service").is_dir(),
                    reason="appointment-booking-service clone absent")
def test_appointment_controller_real_clone():
    """Read-only: the actual clone file, same assertions as the fixture."""
    path = "src/Appointment.API/Controllers/AppointmentController.cs"
    real = (CLONES / "appointment-booking-service" / path).read_text(encoding="utf-8-sig")
    _ctx, items, _t, _ = run({path: real}, (("dotnet", SUB),), shared=False)
    for it in items:
        if it.kind == "inbound_http":
            assert it.subproject == SUB
    ids = by_id(items)
    assert lines(ids[f"inbound_http:{SUB}:POST:/api/service/appointment-request/create"]) == \
        [32, 40, 41]
    assert lines(ids[f"inbound_http:{SUB}:GET:/api/service/appointment-request/fetch/{{}}"]) == \
        [32, 80]
    assert lines(ids[f"inbound_http:{SUB}:GET:/api/service/health/{{}}"]) == [121, 122]
    assert lines(ids[f"inbound_http:{SUB}:POST:/api/service/appointment/fetch/slot"]) == [155]
    assert lines(ids[f"inbound_http:{SUB}:POST:/api/service/appointment/create"]) == [190, 191]
    assert lines(ids[f"inbound_http:{SUB}:PUT:/api/service/appointment/{{}}/update"]) == \
        [224, 225]
    assert lines(ids[f"inbound_http:{SUB}:POST:/api/service/appointment/fetch"]) == [272, 273]


# ---- tokens, auth, ActionResult<T>, ProducesResponseType, UsePathBase ----------------------
TOKENS = {
    "Program.cs": ('var builder = WebApplication.CreateBuilder(args);\n'
                   'builder.Services.AddAuthentication().AddJwtBearer();\n'
                   'var app = builder.Build();\n'
                   'app.UsePathBase("/svc");\n'
                   'var api = app.MapGroup("/api/v2").RequireAuthorization("Admin");\n'
                   'api.MapGet("/items/{id:int}", (int id, IItemService svc) => svc.Get(id));\n'
                   'app.MapPost("/public/ping", ([FromBody] PingDto dto) => Results.Ok())'
                   '.AllowAnonymous();\n'
                   'app.Run();\n'),
    "Controllers/OrdersController.cs": (
        "[ApiController]\n"
        '[Route("api/[controller]")]\n'
        "[Authorize]\n"
        "public class OrdersController : ControllerBase\n"
        "{\n"
        '    private const string Base = "by-dealer";\n'
        '    [HttpGet(Base + "/{dealerId}/[action]")]\n'
        "    [ProducesResponseType(typeof(OrderDto), StatusCodes.Status200OK)]\n"
        "    [ProducesResponseType(StatusCodes.Status404NotFound)]\n"
        "    public async Task<ActionResult<List<OrderDto>>> ListAsync(int dealerId,"
        " [FromHeader(Name = \"X-Tenant\")] string tenant, CancellationToken ct) { return Ok(); }\n"
        '    [HttpPost, AllowAnonymous]\n'
        "    public ActionResult<OrderDto> Create(OrderDto order) => Created(\"\", order);\n"
        '    [HttpDelete("{id:guid}")]\n'
        '    [Authorize(Roles = "Admin, Ops")]\n'
        "    [Obsolete]\n"
        "    public IActionResult Delete(Guid id) { return NoContent(); }\n"
        "}\n"
        "public class OrderDto { public required string Code { get; init; } "
        "public decimal Amount { get; set; } }\n"),
}


def test_controller_tokens_auth_responses_minimal_apis():
    _ctx, items, touched, _ = run(TOKENS)
    ids = by_id(items)
    lst = ids["inbound_http:.:GET:/svc/api/Orders/by-dealer/{}/List"].attributes
    assert lst["path"] == "/svc/api/Orders/by-dealer/{dealerId}/List"
    assert lst["auth"] == "bearer-jwt"
    assert {r["status"]: (r["schema"], r["from"]) for r in lst["responses"]} == {
        200: ("OrderDto", "annotation"), 404: (None, "annotation")}
    assert lst["params"] == [
        {"name": "dealerId", "in": "path", "type": "integer", "required": True},
        {"name": "X-Tenant", "in": "header", "type": "string", "required": True}]
    create = ids["inbound_http:.:POST:/svc/api/Orders"].attributes
    assert create["auth"] == "none" and create["allow_anonymous"] is True
    assert create["request"] == "OrderDto"
    assert create["responses"][0] == {"status": 200, "schema": "OrderDto", "when": None,
                                      "from": "return-type"}
    assert {r["status"] for r in create["responses"]} == {200, 201}
    dele = ids["inbound_http:.:DELETE:/svc/api/Orders/{}"].attributes
    assert dele["auth"] == "roles:Admin,Ops" and dele["deprecated"] is True
    assert dele["params"] == [{"name": "id", "in": "path", "type": "uuid", "required": True}]
    mg = ids["inbound_http:.:GET:/svc/api/v2/items/{}"].attributes
    assert mg["framework"] == "aspnet-minimal" and mg["auth"] == "policy:Admin"
    assert mg["params"] == [{"name": "id", "in": "path", "type": "integer", "required": True}]
    ping = ids["inbound_http:.:POST:/svc/public/ping"].attributes
    assert ping["auth"] == "none" and ping["request"] == "PingDto"
    od = ids["schema:.:OrderDto"].attributes
    assert {f["name"]: f["required"] for f in od["fields"]} == {"Code": True, "Amount": True}
    assert touched["Controllers/OrdersController.cs"].parse == "full"


# ---- PaymentService: Functions, host.json routePrefix, %X% bindings, repo_type ------------
PAY = {"Functions/JusPayWebhooks.cs": fx("payment/Functions/JusPayWebhooks.cs"),
       "Constants/General.cs": fx("payment/Constants/General.cs"),
       "host.json": fx("payment/host.json"),
       "local.settings.json": fx("payment/local.settings.json"),
       "PaymentService.csproj": fx("payment/PaymentService.csproj")}


def test_payment_service_functions():
    ctx, items, _t, shared = run(PAY)
    ids = by_id(items)
    sb = ids["messaging:.:subscribe:azure-service-bus:cpg-juspay"].attributes
    assert sb["entity"] == "cpg-juspay" and sb["name_from"] == "literal"
    assert sb["entity_type"] == "queue" and sb["trigger"] == "function-trigger"
    assert sb["handler"] == "Functions/JusPayWebhooks.cs:13"
    assert sb["error_handling"] == {"dead_letter": True}
    assert lines(ids["messaging:.:subscribe:azure-service-bus:cpg-juspay"]) == [11, 13]
    ref = ids["messaging:.:subscribe:azure-service-bus:config:RefundTopic"].attributes
    assert ref["entity"] == "local.refunds" and ref["resolved_values"] == {"local":
                                                                           "local.refunds"}
    assert ref["subscription"] == "refund-sub" and ref["entity_type"] == "topic"
    http = ids["inbound_http:.:GET:/api/payments/{}/status"].attributes
    assert http["framework"] == "azure-functions" and http["auth"] == "api-key"
    assert http["params"] == [{"name": "orderId", "in": "path", "type": "integer",
                               "required": True}]
    job = ids["scheduled_job:.:Functions/JusPayWebhooks.cs:38"].attributes
    assert job["trigger_type"] == "timer-trigger" and job["expression"] == "0 */5 * * * *"
    assert job["expression_from"] == "config:ReconcileSchedule"
    out = [i for i in items if i.kind == "outbound_http"]
    assert [o.id for o in out] == ["outbound_http:.:POST:env:TokenUrl:/"]
    assert out[0].attributes["client"] == "httpclient"
    # key name contains "token" -> classifier rule 2: the value is never recorded
    assert out[0].attributes["base_url_values"] == {}
    rt = classify_repo(ctx, merge_items(shared + items))
    assert rt["value"] == "function-app"
    no_secrets(items)


def test_host_json_route_prefix():
    files = dict(PAY)
    files["host.json"] = '{ // c\n "version": "2.0", "extensions": {"http": {"routePrefix": ""}}}\n'
    _ctx, items, _t, _ = run(files)
    assert "inbound_http:.:GET:/payments/{}/status" in by_id(items)


# ---- BS2.0Backend_Integration: config-resolved topic listener + dynamic sender -------------
BS2 = {"TopicListener/BookingServiceTopicListener.cs": fx(
           "bs2/TopicListener/BookingServiceTopicListener.cs"),
       "QueueDispatcher/Dispatcher.cs": fx("bs2/QueueDispatcher/Dispatcher.cs"),
       "appsettings.json": fx("bs2/appsettings.json"),
       "appsettings.Development.json": fx("bs2/appsettings.Development.json")}


def test_bs2_topic_listener_config_entity_per_env():
    _ctx, items, touched, _ = run(BS2)
    ids = by_id(items)
    it = ids["messaging:.:subscribe:azure-service-bus:config:ServiceBusSettings:TopicName"]
    a = it.attributes
    assert a["name_from"] == "config:ServiceBusSettings:TopicName"
    assert a["name_key"] == "ServiceBusSettings:TopicName"
    assert a["resolved_values"] == {"default": "prod.booking", "Development": "dev.booking"}
    assert a["entity"] == "prod.booking" and a["entity_type"] == "topic"
    assert a["subscription"] == "reimbursement-booking-subscription"
    assert a["trigger"] == "processor" and a["namespace"] == "fake-bs2-ns"
    assert a["handler"] == "TopicListener/BookingServiceTopicListener.cs:36"
    assert a["error_handling"] == {"dead_letter": True}
    assert lines(it) == [16, 17, 31]
    reads = {i.attributes["name"] for i in items if i.kind == "config_key"}
    assert {"ServiceBusSettings:TopicName", "ServiceBusSettings:Subscription",
            "ServiceBusSettings:ServiceBusEndpoint"} <= reads
    # dynamic sender: entity null, name_from unknown, medium, file partial
    pub = ids["messaging:.:publish:azure-service-bus:unknown"]
    assert pub.attributes["entity"] is None and pub.attributes["name_from"] == "unknown"
    assert pub.confidence == "medium" and pub.attributes["entity_type"] == "queue"
    assert pub.attributes["message_types"] == ["booking-export"]
    assert pub.attributes["namespace"] == "fake-bs2-ns"
    assert touched["QueueDispatcher/Dispatcher.cs"].parse == "partial"
    assert touched["TopicListener/BookingServiceTopicListener.cs"].parse == "full"
    no_secrets(items)


# ---- job-card-service: EF Core + Dapper -----------------------------------------------------
def test_jobcard_ef_core_and_dapper():
    files = {"src/Jobcard.Infrastructure/Extensions/ServiceCollectionExtensions.cs":
             fx("jobcard/ServiceCollectionExtensions.cs"),
             "src/Jobcard.API/appsettings.json": (
                 '{"ConnectionStrings": {"JobcardDb": "Server=fake-jc-sql,1433;Database=jobcard;'
                 'User Id=x;Password=fakeJcPassw0rd;"}}\n')}
    stacks = (("dotnet", "src/Jobcard.API"), ("dotnet", "src/Jobcard.Infrastructure"))
    _ctx, items, _t, _ = run(files, stacks)
    ids = by_id(items)
    ef = ids["data_access:src/Jobcard.Infrastructure:mssql:env:JOBCARD_DB_CONNECTION"]
    a = ef.attributes
    assert a["orm"] == "ef-core" and a["name_from"] == "env:JOBCARD_DB_CONNECTION"
    assert {(e["name"], e["table"], e["schema"]) for e in a["entities"]} == {
        ("JobCard", "MDMS_JOBCARD", "dbo"), ("Dealer", "MDMS_DEALER", None)}
    assert lines(ef) == [15, 16]
    dp = ids["data_access:src/Jobcard.Infrastructure:mssql:config:ConnectionStrings:JobcardDb"]
    assert dp.attributes["orm"] == "dapper"
    assert dp.attributes["host"] == "fake-jc-sql" and dp.attributes["database"] == "jobcard"
    assert [s["name"] for s in dp.attributes["stored_procedures"]] == ["usp_issue_labour"]
    blob = json.dumps([i.to_dict() for i in items])
    assert "fakeJcPassw0rd" not in blob and "Server=" not in blob


# ---- outbound clients -----------------------------------------------------------------------
CLIENTS = {
    "Program.cs": (
        'builder.Services.AddHttpClient("crm", c => c.BaseAddress = '
        'new Uri(builder.Configuration["Crm:BaseUrl"]));\n'
        'builder.Services.AddHttpClient<IPricing, PricingClient>(c => '
        'c.BaseAddress = new Uri("https://pricing.example.test/"));\n'
        'builder.Services.AddRefitClient<ILeadApi>().ConfigureHttpClient(c => '
        'c.BaseAddress = new Uri(builder.Configuration["Lead:Url"]));\n'
        'builder.Services.Configure<CrmOptions>(builder.Configuration.GetSection("Crm"));\n'),
    "appsettings.json": ('{"Crm": {"BaseUrl": "https://crm.example.test", "TimeoutSeconds": 5},'
                         ' "Lead": {"Url": "https://lead.example.test"}}\n'),
    "Clients/CrmClient.cs": (
        "using System.Net.Http.Json;\n"
        "public class CrmClient\n{\n"
        "    private readonly IHttpClientFactory _factory;\n"
        "    private readonly IOptions<CrmOptions> _opts;\n"
        "    public CrmClient(IHttpClientFactory factory, IOptions<CrmOptions> opts)"
        " { _factory = factory; _opts = opts; }\n"
        "    public async Task<CustomerDto?> Get(string id)\n    {\n"
        '        var client = _factory.CreateClient("crm");\n'
        '        client.DefaultRequestHeaders.Add("X-Api-Version", "2");\n'
        "        var t = _opts.Value.TimeoutSeconds;\n"
        '        return await client.GetFromJsonAsync<CustomerDto>($"/api/customers/{id}?expand=all");\n'
        "    }\n}\n"),
    "Clients/PricingClient.cs": (
        "public class PricingClient : IPricing\n{\n"
        "    private readonly HttpClient _http;\n"
        "    public PricingClient(HttpClient http) { _http = http; }\n"
        "    public Task<HttpResponseMessage> Quote(QuoteDto q) =>"
        ' _http.PostAsJsonAsync("v1/quotes", q);\n}\n'),
    "Clients/ILeadApi.cs": (
        "using Refit;\npublic interface ILeadApi\n{\n"
        '    [Get("/leads/{id}")]\n    Task<LeadDto> GetLead(int id);\n}\n'),
    "Clients/SmsClient.cs": (
        "using RestSharp;\npublic class SmsClient\n{\n"
        '    private readonly RestClient _client = new RestClient("https://sms.example.test");\n'
        "    public async Task Send()\n    {\n"
        '        var request = new RestRequest("api/v1/send", Method.Post);\n'
        "        await _client.ExecuteAsync<SmsResult>(request);\n    }\n}\n"),
    "Clients/GeoClient.cs": (
        "using Flurl.Http;\npublic class GeoClient\n{\n"
        '    public Task<GeoDto> Find(string pin) => "https://geo.example.test"'
        '.AppendPathSegment("pincode").AppendPathSegment(pin).GetJsonAsync<GeoDto>();\n}\n'),
}


def test_outbound_clients():
    _ctx, items, _t, _ = run(CLIENTS)
    ids = by_id(items)
    crm = ids["outbound_http:.:GET:config:Crm:BaseUrl:/api/customers/{}"].attributes
    assert crm["client"] == "ihttpclientfactory" and crm["client_name"] == "crm"
    assert crm["base_url_values"] == {"default": "https://crm.example.test"}
    assert crm["query_params"] == ["expand"] and crm["headers"] == ["X-Api-Version"]
    assert crm["response"] == "CustomerDto"
    pr = ids["outbound_http:.:POST:pricing.example.test:/v1/quotes"].attributes
    assert pr["client"] == "ihttpclientfactory" and pr["request"] == "QuoteDto"
    assert pr["target_hint"] == "pricing.example.test"
    lead = ids["outbound_http:.:GET:config:Lead:Url:/leads/{}"].attributes
    assert lead["client"] == "refit" and lead["response"] == "LeadDto"
    sms = ids["outbound_http:.:POST:sms.example.test:/api/v1/send"].attributes
    assert sms["client"] == "restsharp" and sms["response"] == "SmsResult"
    geo = ids["outbound_http:.:GET:geo.example.test:/pincode/{}"].attributes
    assert geo["client"] == "flurl"
    reads = by_id([i for i in items if i.kind == "config_key"])
    assert "config_key:.:crm.timeoutseconds" in reads
    assert reads["config_key:.:crm.timeoutseconds"].attributes["reads"][0]["api"] == "IOptions"
    assert "config_key:.:crm.baseurl" in reads


def test_wrapper_one_level_and_tests_target():
    files = {
        "Services/Notifier.cs": (
            "public class Notifier\n{\n"
            "    public async Task Notify() { await Post(Environment.GetEnvironmentVariable("
            '"HOOK_URL"), "x"); }\n'
            "    private async Task<bool> Post(string url, object data)\n    {\n"
            "        using (var client = new HttpClient())\n        {\n"
            "            var r = await client.PostAsJsonAsync(url, data);\n"
            "            return r.IsSuccessStatusCode;\n        }\n    }\n}\n"),
        "Notifier.Tests/NotifierTests.cs": (
            "public class NotifierTests\n{\n    [Fact]\n    public async Task T()\n    {\n"
            "        var c = new HttpClient();\n"
            '        await c.GetAsync("https://svc.example.test/health");\n    }\n}\n'),
    }
    _ctx, items, touched, _ = run(files, (("dotnet", "."), ("dotnet", "Notifier.Tests")))
    ids = by_id(items)
    w = ids["outbound_http:.:POST:env:HOOK_URL:/"]
    assert w.confidence == "medium"
    assert w.attributes["via_wrapper"] == "Services/Notifier.cs:8"
    t = ids["outbound_http:Notifier.Tests:GET:svc.example.test:/health"].attributes
    assert t["role"] == "tests_target"
    assert not [i for i in items if i.subproject == "Notifier.Tests" and i.kind != "outbound_http"]
    assert touched["Notifier.Tests/NotifierTests.cs"].parse == "partial"


def test_scheduled_and_swashbuckle():
    files = {
        "Program.cs": ("builder.Services.AddSwaggerGen();\napp.UseSwagger();\n"
                       'RecurringJob.AddOrUpdate("cleanup", () => Jobs.Cleanup(), Cron.Daily);\n'),
        "Workers/Poller.cs": (
            "public class Poller : BackgroundService\n{\n"
            "    protected override async Task ExecuteAsync(CancellationToken ct)\n    {\n"
            "        while (!ct.IsCancellationRequested)"
            " { await Task.Delay(TimeSpan.FromMinutes(5), ct); }\n    }\n}\n"),
    }
    _ctx, items, _t, _ = run(files)
    ids = by_id(items)
    assert ids["api_contract:.:swashbuckle"].attributes["docs_path"] == "/swagger/v1/swagger.json"
    hs = ids["scheduled_job:.:Workers/Poller.cs:3"]
    assert hs.attributes["trigger_type"] == "hosted-service" and hs.confidence == "medium"
    assert hs.attributes["expression"] == "TimeSpan.FromMinutes(5)"
    hf = ids["scheduled_job:.:Program.cs:3"].attributes
    assert hf["trigger_type"] == "hangfire" and hf["expression"] == "Cron.Daily"
    assert hf["name"] == "cleanup"


def test_parse_errors_mark_partial():
    files = {"Broken.cs": "public class A { void M( { int x = ; }\n"}
    _ctx, _items, touched, _ = run(files)
    assert touched["Broken.cs"].parse == "partial"
    assert touched["Broken.cs"].error.startswith("tree-sitter:")


def test_deterministic_output():
    files = {**APPT, **{f"pay/{k}": v for k, v in PAY.items()}}
    stacks = APPT_STACKS + (("dotnet", "pay"),)
    dumps = []
    for _ in range(2):
        _ctx, items, touched, _ = run(files, stacks)
        dumps.append(json.dumps([i.to_dict() for i in sorted(items, key=lambda i: i.id)],
                                sort_keys=True)
                     + json.dumps({k: (v.parse, v.error) for k, v in sorted(touched.items())}))
    assert dumps[0] == dumps[1]


def test_extractor_contract():
    ex = DotnetAspnetExtractor()
    assert ex.id == "dotnet.aspnet" and ex.stacks == ("dotnet",)
    assert ex.extractor_version.startswith("0.1.1+ts") and ".cs" in ex.extractor_version
    assert ex.applies_to({"stacks": [{"stack": "dotnet", "subproject": "."}]}, ".")
    assert not ex.applies_to({"stacks": [{"stack": "java", "subproject": "."}]}, ".")


def test_declared_type_names_feed_external_systems_sdk_symbols():
    from repo_docs import phase2_extract as p2
    reg = [{"name": "juspay", "category": "payments", "hosts": [], "packages": [],
            "sdk_symbols": ["JusPay*"]}]
    ctx = RepoContext.for_test(PAY, [("dotnet", ".")], registry=reg)
    res = p2.run(ctx)
    ext = [i for i in res["items"] if i.kind == "external_system"]
    assert [i.id for i in ext] == ["external_system:.:juspay"]
    assert ext[0].attributes["matched_by"] == "sdk-symbol"
    assert ext[0].attributes["match"].startswith("JusPay")
    assert p2.validate(ctx, res["items"]) == []
