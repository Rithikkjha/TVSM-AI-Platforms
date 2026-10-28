"""node.backend (FEAT-004). Fixtures under tests/fixtures/node/ are trimmed reproductions of
TVS-CS clones (source repo + file cited per test); values in .env fixtures are fake."""
from __future__ import annotations

import json
from pathlib import Path

from repo_docs.extractors.base import RepoContext
from repo_docs.extractors.node_backend import NodeBackendExtractor
from repo_docs.extractors.node_frontend import NodeFrontendExtractor
from repo_docs.extractors.shared_config import SharedConfig
from repo_docs.extractors.shared_infra import SharedInfra
from repo_docs.inventory_schema import validate_item
from repo_docs.phase2_extract import merge_items

FIX = Path(__file__).parent / "fixtures" / "node"


def load(name: str) -> dict[str, str]:
    base = FIX / name
    return {p.relative_to(base).as_posix(): p.read_text() for p in sorted(base.rglob("*"))
            if p.is_file()}


def run(files: dict, stacks: list, extractors=(NodeBackendExtractor, NodeFrontendExtractor)):
    ctx = RepoContext.for_test(files, stacks)
    # shared extractors run first in the real orchestrator (config index + config_key defs);
    # their config_key items are merged with the node read items like phase2_extract does
    items = [it for it in SharedConfig().extract(ctx, None).items]
    SharedInfra().extract(ctx, None)
    touched = {}
    for cls in extractors:
        ex = cls()
        for sub in ctx.subprojects:
            if ex.applies_to(ctx.meta, sub):
                r = ex.extract(ctx, sub)
                items += r.items
                for k, v in r.touched.items():
                    touched[(ex.id, k)] = v
    items = merge_items(items)
    problems = [p for it in items for p in validate_item(it, ctx.ledger_index, ctx.line)]
    assert problems == []
    return ctx, {it.id: it for it in items}, touched


def blob(items) -> str:
    return json.dumps([it.to_dict() for it in items.values()], sort_keys=True)


EXPRESS = [("express", "."), ("node", ".")]


def test_applies_to_dp6():
    ex = NodeBackendExtractor()
    meta = {"stacks": [{"stack": "node", "subproject": "."},
                       {"stack": "react", "subproject": "web"},
                       {"stack": "node", "subproject": "web"},
                       {"stack": "nest", "subproject": "api"}]}
    assert ex.applies_to(meta, ".")          # plain node (Catalog-Scheduler)
    assert not ex.applies_to(meta, "web")    # node + react -> frontend only
    assert ex.applies_to(meta, "api")
    assert NodeFrontendExtractor().applies_to(meta, "web")
    assert not NodeFrontendExtractor().applies_to(meta, ".")
    assert "+ts" in ex.extractor_version and ".tsg" in ex.extractor_version


def test_express_mount_prefix_and_wrapper_outbound():
    # Price-Microservice-Backend-for-Frontend-Layer: src/routes/routes.ts app.use('/regions',
    # regionRoute) + src/routes/api/region-routes.ts, src/rest/http/http.ts (class Http,
    # export default new Http()), src/rest/API-directories/region-api.ts URL builders,
    # src/rest/implementers/region-implementer.ts call sites
    ctx, items, touched = run(load("price-bff"), EXPRESS)
    inb = items["inbound_http:.:GET:/regions/{}/states"]
    a = inb.attributes
    assert a["path"] == "/regions/{country}/states" and a["framework"] == "express"
    assert a["params"][0] == {"name": "country", "in": "path", "type": "string", "required": True}
    assert a["handler"] == "regionHandler.getAllStates"
    ev = {(e.file, e.line) for e in inb.evidence}
    assert ("src/routes/api/region-routes.ts", 5) in ev and ("src/routes/routes.ts", 12) in ev
    cities = items["inbound_http:.:GET:/regions/cities"].attributes
    assert {"name": "state", "in": "query", "type": "string", "required": False} in cities["params"]

    out = items["outbound_http:.:GET:env:PRICE_MICROSERVICE_BASE_URL:/regions/{}/states"]
    o = out.attributes
    assert o["client"] == "axios" and o["method"] == "GET"
    assert o["path_template"] == "/regions/{}/states"
    assert o["via_wrapper"] == "src/rest/http/http.ts:7"
    assert o["base_url_values"] == {"default": "http://price-svc.example.internal:8080"}
    assert out.confidence == "medium"
    assert out.evidence[0].file == "src/rest/implementers/region-implementer.ts"
    assert out.evidence[0].line == 7
    city = items["outbound_http:.:GET:env:PRICE_MICROSERVICE_BASE_URL:/regions/cities"]
    assert city.attributes["query_params"] == []
    # wrapper file is generic -> partial; route file fully understood -> full
    assert touched[("node.backend", "src/rest/http/http.ts")].parse == "partial"
    assert touched[("node.backend", "src/routes/api/region-routes.ts")].parse == "full"


def test_nest_enum_controller_swagger_and_schema():
    # booking-crud-services: src/shared/constants/constants.ts enum API_ROUTE,
    # src/bookings/controllers/bookings.controller.ts @Controller(API_ROUTE.BOOKINGS) @Post(),
    # src/main.ts SwaggerModule.setup('api-doc', ...)
    ctx, items, _ = run(load("booking"), [("nest", "."), ("node", ".")])
    post = items["inbound_http:.:POST:/bookings"].attributes
    assert post["framework"] == "nest" and post["handler"] == "BookingsController.createBooking"
    assert post["request"] == "CreateBookingRequestDto"
    assert post["responses"] == [{"status": 202, "schema": "BookingCreationResponseDto",
                                  "when": "Booking accepted", "from": "annotation"}]
    cancel = items["inbound_http:.:PUT:/bookings/cancel"].attributes
    assert cancel["responses"][0]["status"] == 200
    assert cancel["responses"][0]["from"] == "return-type"
    contract = items["api_contract:.:nestjs-swagger"].attributes
    assert contract["generated"] is True and contract["docs_path"] == "/api-doc"
    dto = items["schema:.:CreateBookingRequestDto"].attributes
    f = {x["name"]: x for x in dto["fields"]}
    assert f["mobileNumber"]["required"] is True and "Length(10, 10)" in f["mobileNumber"]["validation"]
    assert f["remarks"]["required"] is False
    assert f["vehicle"]["type"] == "VehicleDto"
    veh = items["schema:.:VehicleDto"].attributes      # nested interface collected transitively
    assert veh["schema_kind"] == "interface"
    assert {x["name"]: x["required"] for x in veh["fields"]} == {"modelId": True, "color": False,
                                                                 "price": True}
    resp = items["schema:.:BookingCreationResponseDto"].attributes
    assert resp["fields"][1]["type"] == "enum[ACCEPTED,REJECTED]"


def test_service_bus_base_listener_subclass_hint_and_secret_json_publisher():
    # booking-crud-services: cloud-conductor/services/listener/base-topic-listener.service.ts
    # acceptNextSession(this.topicName, this.subscriptionName) set in initialize(...);
    # mdp-dealer-topic-listener.service.ts destructures DEALER_TOPIC_NAME from a JSON secret;
    # publisher/topic-publisher.service.ts createSender(this.topic) with TOPIC_NAME
    ctx, items, touched = run(load("booking"), [("nest", "."), ("node", ".")])
    sub = items["messaging:.:subscribe:azure-service-bus:unknown:DEALER_TOPIC_NAME"]
    a = sub.attributes
    assert a["entity"] is None and a["name_from"] == "unknown"
    assert a["name_key"] == "DEALER_TOPIC_NAME"
    assert a["subscription"] == "unknown:DEALER_TOPIC_SUBSCRIPTION_NAME"
    assert a["entity_type"] == "topic" and a["trigger"] == "processor"
    assert sub.confidence == "medium"
    files = {e.file for e in sub.evidence}
    assert files == {"src/cloud-conductor/services/listener/base-topic-listener.service.ts",
                     "src/cloud-conductor/services/listener/mdp-dealer-topic-listener.service.ts"}
    pub = items["messaging:.:publish:azure-service-bus:unknown:TOPIC_NAME"].attributes
    assert pub["published_by"] == \
        "src/cloud-conductor/services/publisher/topic-publisher.service.ts:16"


def test_service_bus_publisher_env_topic_and_no_secret_values():
    # Price-Engine-MicroService-Backend src/services/price-engine-price-publisher.ts:
    # private readonly topicName = process.env.TOPIC_NAME_MARKETPLACE || ''
    ctx, items, _ = run(load("price-engine"), EXPRESS)
    pub = items["messaging:.:publish:azure-service-bus:env:TOPIC_NAME_MARKETPLACE"]
    a = pub.attributes
    assert a["entity"] == "local.ccp.marketplace.price"
    assert a["resolved_values"] == {"default": "local.ccp.marketplace.price"}
    assert a["name_key"] == "TOPIC_NAME_MARKETPLACE" and a["entity_type"] == "topic"
    assert a["published_by"] == "src/services/price-engine-price-publisher.ts:9"
    assert "FAKEsecretKEY0123456789abcdefFAKE" not in blob(items)
    cs = items["config_key:.:connection.string.marketplace"].attributes
    assert cs["secret"] is True and cs["values"] == {}
    assert cs["reads"] == [{"file": "src/services/price-engine-price-publisher.ts", "line": 4,
                            "api": "process.env"}]


def test_plain_node_local_env_topic_timer_and_mongo():
    # Catalog-Scheduler: price-updates.js `const topicName = process.env.SERVICE_BUS_TOPIC_NAME`
    # + createSender(topicName); src/functions/*.js app.timer(... schedule: process.env.X);
    # local.settings.json Values
    ctx, items, _ = run(load("catalog-scheduler"), [("node", ".")])
    pub = items["messaging:.:publish:azure-service-bus:env:SERVICE_BUS_TOPIC_NAME"].attributes
    assert pub["entity"] == "local.catalog.price-updates"
    job = items["scheduled_job:.:src/functions/product-price-ingestion-job.js:4"].attributes
    assert job["trigger_type"] == "timer-trigger" and job["name"] == "product-price-ingestion-job"
    assert job["expression_from"] == "env:CRON_EXPRESSION_FOR_PRODUCT_PRICE_INGESTION_JOB"
    assert job["expression"] == "0 */30 * * * *"
    mongo = [it for it in items.values() if it.kind == "data_access"]
    assert len(mongo) == 1
    m = mongo[0].attributes
    assert m["store_type"] == "mongo" and m["name_from"] == "env:MONGO_DB_HOST"
    assert m["collections"] == ["icePrices"]


def test_nest_global_prefix_versioning_guards_httpservice_typeorm_cron():
    # synthetic (no setGlobalPrefix / RouterModule in the allowlisted clones)
    files = load("nest-synthetic")
    files[".env"] = "INVENTORY_URL=https://inventory.example.com\nDB_HOST=db.example.com\n"
    ctx, items, _ = run(files, [("nest", "."), ("node", ".")])
    order = items["inbound_http:.:GET:/api/v1/orders/{}"]
    a = order.attributes
    assert a["path"] == "/api/v1/orders/{id}"
    assert a["auth"] == "guard:JwtAuthGuard"
    assert {"name": "id", "in": "path", "type": "string", "required": True} in a["params"]
    assert {"name": "limit", "in": "query", "type": "number", "required": False} in a["params"]
    assert [r["status"] for r in a["responses"]] == [200, 404]
    assert a["responses"][0]["schema"] == "OrderDto"
    assert ("src/main.ts", 7) in {(e.file, e.line) for e in order.evidence}
    assert "inbound_http:.:GET:/health" in items            # excluded from the global prefix
    stock = items["outbound_http:.:GET:env:INVENTORY_URL:/stock/{}"].attributes
    assert stock["client"] == "nest-httpservice"
    assert stock["base_url_values"] == {"default": "https://inventory.example.com"}
    pay = items["outbound_http:.:POST:config:PAYMENT_URL:/payments"].attributes
    assert pay["client"] == "axios"
    db = items["data_access:.:postgres:env:DB_HOST"].attributes
    assert db["orm"] == "typeorm" and db["entities"][0]["table"] == "orders"
    cron = [it for it in items.values() if it.kind == "scheduled_job"][0].attributes
    assert cron["expression"] == "0 */5 * * * *" and cron["name"] == "OrdersService.reconcile"
    schema = items["schema:.:OrderDto"].attributes
    assert {f["name"]: f["type"] for f in schema["fields"]} == {
        "id": "string", "status": "OrderStatus", "lines": "string[]"}
    assert items["schema:.:OrderStatus"].attributes["enum_values"] == ["OPEN", "CLOSED"]


def test_deterministic_output():
    def once():
        _, items, touched = run(load("booking"), [("nest", "."), ("node", ".")])
        return blob(items), sorted((k, v.parse) for k, v in touched.items())
    assert once() == once()


def test_clean_file_without_constructs_is_full_unsupported_client_partial():
    files = {"package.json": '{"name": "svc", "dependencies": {"express": "4"}}\n',
             "src/util.ts": "export const trim = (s: string) => s.trim();\n",
             "src/queue.ts": "import { Kafka } from 'kafkajs';\n"
                             "export const kafka = new Kafka({ clientId: 'svc' });\n"}
    _ctx, _items, touched = run(files, [("node", ".")], extractors=(NodeBackendExtractor,))
    assert touched[("node.backend", "src/util.ts")].parse == "full"
    assert touched[("node.backend", "src/queue.ts")].parse == "partial"
