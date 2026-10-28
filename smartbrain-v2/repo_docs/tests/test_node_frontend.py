"""node.frontend (FEAT-004). Fixtures under tests/fixtures/node/ are trimmed reproductions of
TVS-CS clones (source repo + file cited per test); env values are fake."""
from __future__ import annotations

from repo_docs.extractors.node_frontend import NodeFrontendExtractor

from test_node_backend import blob, load, run

REACT = [("node", "."), ("react", ".")]
NEXT = [("nextjs", "channel-partner-system"), ("node", "channel-partner-system")]


def test_object_literal_wrapper_with_per_env_dotenv_values():
    # location-frontend: src/rest/httpDealer.ts (`get: async (url) => axios.get(`${baseURL}${url}`)`),
    # src/services/DealerDetailsService.ts, .env.dev/.env.uat/.env.prod
    ctx, items, _ = run(load("location-frontend"), REACT)
    it = items["frontend_api_call:.:GET:env:REACT_APP_DEALER_BASE_URL:/api/v1/user-x/{}/countries"]
    a = it.attributes
    assert a["method"] == "GET" and a["client"] == "axios"
    assert a["path_template"] == "/api/v1/user-x/{}/countries"
    assert a["base_url_values"] == {"dev": "https://dev-api.example.com/location-master",
                                    "prod": "https://api.example.com/location-master",
                                    "uat": "https://uat-api.example.com/location-master"}
    assert a["ui_framework"] == "react" and a["runtime"] == "browser"
    assert a["base_url_kind"] == "dotenv"
    assert a["via_wrapper"] == "src/rest/httpDealer.ts:7"
    assert it.confidence == "medium"
    assert (it.evidence[0].file, it.evidence[0].line) == ("src/services/DealerDetailsService.ts", 6)
    post = items["frontend_api_call:.:POST:env:REACT_APP_DEALER_BASE_URL:/v1/dealer-location/submit"]
    assert post.attributes["method"] == "POST"
    # factory-made wrapper: createHttpService(process.env.REACT_APP_ADMIN_BASE_URL)
    adm = items["frontend_api_call:.:GET:env:REACT_APP_ADMIN_BASE_URL:/summary"].attributes
    assert adm["base_url_values"]["dev"] == \
        "https://dev-api.example.com/location-master/api/v1/admin-flow"
    assert adm["via_wrapper"] == "src/rest/httpCommon.ts:12"
    # secret key read: name only, never the value; no query string values leak
    key = items["config_key:.:react.app.google.maps.api.key"].attributes
    assert key["secret"] is True and key["values"] == {}
    assert "AIzaFAKE" not in blob(items)
    # query strings of base URLs are stripped from node items (shared.config evidence snippets
    # of the .env line itself are shared.config's business)
    own = {k: v for k, v in items.items() if v.extractor_id.startswith("node.")}
    assert "abc123" not in blob(own)


def test_next_portal_alias_static_getter_cast_call_site_and_route_handlers():
    # TVS-CPS-PORTAL channel-partner-system: tsconfig paths '@/*' -> src/*, src/utils/api.ts
    # (createApiInstance/getApiInstance + get/post inside withLoading), EnvironmentConstants
    # static getter, `(post as any)('/v1/inventory/list')`, app/api route handlers, next.config
    # basePath: BASE_PATH
    files = {f"channel-partner-system/{k}" if not k.startswith("channel-partner-system/") else k: v
             for k, v in load("cps-portal").items()}
    ctx, items, touched = run(files, NEXT)
    sub = "channel-partner-system"
    inv = items[f"frontend_api_call:{sub}:POST:env:NEXT_PUBLIC_API_BASE_URL:/v1/inventory/list"]
    a = inv.attributes
    assert a["ui_framework"] == "nextjs" and a["runtime"] == "browser"
    assert a["via_wrapper"] == f"{sub}/src/utils/api.ts:39"
    get = items[f"frontend_api_call:{sub}:GET:env:NEXT_PUBLIC_API_BASE_URL:/v1/inventory/{{}}"]
    assert get.attributes["response"] == "StockQuery"
    assert items[f"schema:{sub}:StockQuery"].attributes["schema_kind"] == "interface"
    # the runtime-config loader calls the app's own API (relative, base unknown)
    cfg = items[f"frontend_api_call:{sub}:GET:_:/thenortonhub/api/getEnvConfig"].attributes
    assert cfg["base_url_source"] == "unknown"
    # Next route handlers -> inbound next-api with basePath
    claim = items[f"inbound_http:{sub}:GET:/thenortonhub/api/claim/claim-details/{{}}"]
    assert claim.attributes["framework"] == "next-api"
    assert claim.attributes["path"] == "/thenortonhub/api/claim/claim-details/{claimId}"
    assert f"inbound_http:{sub}:GET:/thenortonhub/api/getEnvConfig" in items
    # server-side fetch inside the route handler
    srv = items[f"frontend_api_call:{sub}:GET:env:NEXT_PUBLIC_API_BASE_URL_INTERNAL:/v1/claims/{{}}"]
    assert srv.attributes["runtime"] == "server" and srv.attributes["client"] == "fetch"
    fb = items[f"config_key:{sub}:next.public.firebase.api.key"].attributes
    assert fb["secret"] is True and fb["values"] == {}
    assert fb["reads"][0]["file"] == f"{sub}/src/app/api/getEnvConfig/route.ts"
    assert touched[("node.frontend", f"{sub}/tsconfig.json")].parse == "partial"


def test_jsx_in_js_falls_back_to_tsx_and_code_default_base():
    # cbs-admin-portal: src/services/dataService.js (`process.env.REACT_APP_BOOKING_API_URL ||
    # 'http://...'`), JSX page in a .js file
    ctx, items, touched = run(load("cbs-admin-portal"), REACT)
    page = items["frontend_api_call:.:GET:env:REACT_APP_API_URL:/lms/lead-flow/all"].attributes
    assert page["client"] == "fetch" and page["method"] == "GET"
    assert ctx.syntax("src/pages/LeadFlowPage.js").lang == "tsx"
    vm = items["frontend_api_call:.:POST:env:REACT_APP_BOOKING_API_URL:/dms-vehicle-master"]
    assert vm.attributes["base_url_values"] == {"code-default": "http://uat-bookings.example.net/bookings"}
    assert vm.confidence == "high"
    assert "frontend_api_call:.:GET:env:REACT_APP_API_URL:/dealers/{}" in items
    assert touched[("node.frontend", "src/services/dataService.js")].parse == "full"


def test_env_sample_names_only():
    # Price-Engine-Frontend .env.sample: sample values -> name + required only
    ctx, items, _ = run(load("price-engine-frontend"), REACT)
    k = items["config_key:.:react.app.price.engine.bff.base.url"].attributes
    assert k["required"] is True and k["values"] == {}
    call = items["frontend_api_call:.:GET:env:REACT_APP_PRICE_ENGINE_BFF_BASE_URL:/regions/{}/states"]
    assert call.attributes["base_url_values"] == {}
    assert "sample-not-a-real-secret-value" not in blob(items)


def test_frontend_extractor_ignores_test_files():
    files = load("location-frontend")
    files["src/services/__tests__/DealerDetailsService.test.ts"] = (
        "import axios from 'axios';\n"
        "it('x', async () => { await axios.get('https://mock.example.com/never'); });\n")
    ctx, items, touched = run(files, REACT, extractors=(NodeFrontendExtractor,))
    assert not any("mock.example.com" in i for i in items)
    assert ("node.frontend", "src/services/__tests__/DealerDetailsService.test.ts") not in touched
