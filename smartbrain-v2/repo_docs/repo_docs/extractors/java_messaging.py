"""Messaging detection for java.spring (docs/EXTRACTORS.md#messaging).

azure-messaging-servicebus ``new ServiceBusClientBuilder()...sender()|processor()|sessionProcessor()|
receiver()|sessionReceiver()`` chains with ``topicName/queueName/subscriptionName``; spring-cloud-azure
``ServiceBusTemplate.send`` / ``@ServiceBusListener``; JMS; Kafka (incl. the tvsm-be-core
``KafkaProducerUtil.send*`` wrapper); Rabbit; Spring Cloud Stream.
Produces neutral ``Msg`` records; java_spring turns them into ``messaging`` items.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

from . import java_symbols as js
from . import syntax as sx

SB_KINDS = {"sender": ("publish", None), "processor": ("subscribe", "processor"),
            "sessionProcessor": ("subscribe", "processor"),
            "receiver": ("subscribe", "poll"), "sessionReceiver": ("subscribe", "poll")}
SENDER_TYPES = ("ServiceBusSenderClient", "ServiceBusSenderAsyncClient")
SEND_METHODS = ("sendMessage", "sendMessages", "scheduleMessage", "scheduleMessages")
KAFKA_UTIL_SEND = re.compile(r"send(String|Json|Bytes)(Sync|Async)?")
# payload resolution: serializer calls are unwrapped to their argument, whose declared type is the
# payload; transport/envelope types never count as a payload
SERIALIZERS = ("toJson", "writeValueAsString", "writeValueAsBytes", "fromObject", "serialize",
               "toJSONString", "withPayload")
DESERIALIZERS = ("readValue", "fromJson", "toObject", "convertValue", "parseObject")
ENVELOPE_TYPES = frozenset({
    "String", "Object", "byte[]", "char[]", "Message", "ServiceBusReceivedMessage",
    "ServiceBusReceivedMessageContext", "ServiceBusMessage", "ServiceBusMessageBatch",
    "BinaryData", "ConsumerRecord", "ConsumerRecords", "Acknowledgment", "Session", "Channel",
    "TextMessage", "BytesMessage", "MessageHeaders", "Map", "HashMap", "JsonNode", "ObjectNode",
    "MessageProperties", "Headers", "List", "void"})


@dataclass
class Msg:
    direction: str
    broker: str
    entity_type: str | None
    name: js.ValueSource | None          # entity expression
    line: int
    lines: list = field(default_factory=list)
    subscription: js.ValueSource | None = None
    namespace: str | None = None
    trigger: str | None = None
    handler_line: int | None = None
    properties: dict = field(default_factory=dict)
    error_handling: dict = field(default_factory=dict)
    library: str | None = None
    beans: list = field(default_factory=list)     # bean names producing this client
    payload: str | None = None                    # declared payload type text (normalized later)
    conn_param: int | None = None                 # helper param holding the connection string


def _args(node) -> list:
    al = node.child_by_field_name("arguments")
    return sx.named_children(al) if al is not None else []


def _nline(node) -> int:
    n = node.child_by_field_name("name")
    return sx.line(n if n is not None else node)


class MessagingScanner:
    def __init__(self, ctx, idx: js.JavaIndex):
        self.ctx, self.idx = ctx, idx

    def _namespace(self, node, scope, sub) -> str | None:
        """Service Bus namespace from a connection string expression (host only, never the key)."""
        from ..config_classify import parse_store_identity
        vs = self.idx.resolve_expr(node, scope)
        raw = None
        if vs.kind in ("config", "env") and vs.key:
            raw = self.ctx.config.resolve("${" + vs.key + "}", "default", sub).value
        elif vs.kind == "literal":
            raw = vs.value
        ident = parse_store_identity(raw) if raw else None
        return ident.get("namespace") if ident else None

    def method_msgs(self, jt: js.JType, m: sx.MethodDecl, sub: str, servicebus_jms: bool
                    ) -> list[Msg]:
        if m.body is None:
            return []
        scope = self.idx.method_scope(jt, m)
        out: list[Msg] = []
        done = set()
        bean_names = []
        bean = next((a for a in m.annotations if a.name == "Bean"), None)
        if bean is not None:
            nm = bean.args.get("name", "value", pos=0)
            nm = nm if isinstance(nm, list) else [nm]
            bean_names = [x for x in nm if isinstance(x, str)] or [m.name]
        for n in self.idx.nodes(m, "*"):
            if n.type == "object_creation_expression" and \
                    js.simple_type(sx.text(n.child_by_field_name("type"))) == \
                    "ServiceBusClientBuilder":
                top = js.outermost(n)
                if top.id in done:
                    continue
                done.add(top.id)
                msg = self._sb_chain(js.invocation_chain(top), scope, sub, sx.line(n))
                if msg is not None:
                    msg.beans = list(bean_names)
                    out.append(msg)
            elif n.type == "method_invocation":
                msg = self._template_send(n, scope, servicebus_jms)
                if msg is not None:
                    out.append(msg)
        return out

    def _sb_chain(self, chain, scope, sub, line) -> Msg | None:
        kind = next((c for c in chain[1:] if c[1] in SB_KINDS), None)
        if kind is None:
            return None
        direction, trigger = SB_KINDS[kind[1]]
        msg = Msg(direction, "azure-service-bus", None, None, line, [line, _nline(kind[0])],
                  trigger=trigger, library="azure-messaging-servicebus")
        if kind[1].startswith("session"):
            msg.properties["session_id"] = True
        for cn, nm, args in chain[1:]:
            if nm in ("topicName", "queueName") and args:
                msg.entity_type = "topic" if nm == "topicName" else "queue"
                msg.name = self.idx.resolve_expr(args[0], scope)
                msg.lines.append(_nline(cn))
                msg.lines += self._value_lines(args[0], scope)
            elif nm == "subscriptionName" and args:
                msg.subscription = self.idx.resolve_expr(args[0], scope)
                msg.lines.append(_nline(cn))
            elif nm == "connectionString" and args:
                msg.namespace = self._namespace(args[0], scope, sub) or msg.namespace
                if args[0].type == "identifier" and sx.text(args[0]) in scope.params:
                    msg.conn_param = scope.params[sx.text(args[0])][0]
            elif nm == "fullyQualifiedNamespace" and args:
                vs = self.idx.resolve_expr(args[0], scope)
                if vs.kind == "literal" and not vs.holes:
                    msg.namespace = vs.value.split(".")[0]
            elif nm == "disableAutoComplete":
                msg.properties["auto_complete"] = False
            elif nm == "maxAutoLockRenewDuration" and args:
                msg.properties["max_auto_lock_renew"] = sx.text(args[0])[:80]
            elif nm == "receiveMode" and args:
                msg.properties["receive_mode"] = sx.text(args[0]).rsplit(".", 1)[-1]
            elif nm in ("maxConcurrentCalls", "maxConcurrentSessions") and args:
                v = sx.value_of(args[0], "java")
                if isinstance(v, int):
                    msg.properties["max_concurrent_" + nm[13:].lower()] = v
            elif nm == "retryOptions":
                msg.error_handling["retry"] = True
            elif nm == "processMessage" and args:
                msg.handler_line = self._handler_line(args[0], scope) or _nline(cn)
            elif nm == "processError" and args:
                msg.error_handling["error_handler"] = True
        return msg

    def expand_param_msgs(self, jt: js.JType, m: sx.MethodDecl, msgs: list[Msg], sub: str
                          ) -> list[Msg]:
        """A Service Bus client built in a helper from its parameters (``topicName(topic)``)
        is re-emitted once per same-class call site (same arity, bare / ``this.`` receiver,
        source order) with the entity / subscription / namespace resolved in the caller's
        scope (``@Value`` parameters of the ``@Bean`` methods). One hop; no call site -> the
        original, unresolved message."""
        def is_param(vs):
            return vs is not None and any(s.kind == "param" for s in vs.segs)
        if not any(is_param(x.name) or is_param(x.subscription) for x in msgs):
            return msgs
        sites = []
        for t in self.idx.outer_chain(jt):
            for cm in t.methods:
                if cm is m or cm.body is None:
                    continue
                for n in self.idx.nodes(cm, "method_invocation"):
                    obj = n.child_by_field_name("object")
                    if sx.text(n.child_by_field_name("name")) != m.name or \
                            (obj is not None and obj.type != "this") or \
                            len(_args(n)) != len(m.params):
                        continue
                    sites.append((t, cm, n))
        if not sites:
            return msgs
        out = []
        for msg in msgs:
            if not (is_param(msg.name) or is_param(msg.subscription)):
                out.append(msg)
                continue
            for t, cm, n in sites:
                cs = self.idx.method_scope(t, cm)
                args = _args(n)
                lines = list(msg.lines) + [_nline(n)]

                def sub_vs(vs):
                    if not is_param(vs):
                        return vs
                    segs, q = [], list(vs.query)
                    for s in vs.segs:
                        if s.kind == "param" and s.text.isdigit() and int(s.text) < len(args):
                            a = args[int(s.text)]
                            r = self.idx.resolve_expr(a, cs)
                            segs += list(r.segs)
                            q += r.query
                            lines.extend(self._value_lines(a, cs))
                        else:
                            segs.append(s)
                    return js.source_of(segs, q)
                bean = next((a for a in cm.annotations if a.name == "Bean"), None)
                beans = msg.beans
                if bean is not None:
                    nm = bean.args.get("name", "value", pos=0)
                    nm = nm if isinstance(nm, list) else [nm]
                    beans = [x for x in nm if isinstance(x, str)] or [cm.name]
                ns = msg.namespace
                if msg.conn_param is not None and msg.conn_param < len(args):
                    ns = self._namespace(args[msg.conn_param], cs, sub) or ns
                clone = replace(msg, name=sub_vs(msg.name), subscription=sub_vs(msg.subscription),
                                namespace=ns, beans=list(beans),
                                properties=dict(msg.properties),
                                error_handling=dict(msg.error_handling))
                clone.lines = sorted(set(lines))
                out.append(clone)
        return out

    def _value_lines(self, node, scope) -> list:
        """@Value lines of a parameter / field used as an entity name."""
        if node.type != "identifier":
            return []
        nm = sx.text(node)
        if nm in scope.params:
            return [a.line for a in scope.params[nm][1].annotations if a.name == "Value"]
        hit = self.idx.find_field(scope.jtype, nm) if scope.jtype is not None else None
        if hit is not None and nm in hit[0].value_keys:
            return [hit[0].value_keys[nm][2]]
        return []

    def _handler_line(self, node, scope) -> int | None:
        if node.type == "identifier":
            vals = scope.locals.get(sx.text(node)) or []
            if len(vals) == 1 and vals[0] is not None:
                return sx.line(vals[0])
        if node.type == "method_reference":
            nm = sx.text(node).split("::")[-1]
            m = next((mm for mm in (scope.jtype.methods if scope.jtype else [])
                      if mm.name == nm), None)
            if m is not None:
                return m.line
        return sx.line(node)

    def payload_of(self, node, scope) -> str | None:
        """Declared type of the object a message is built from: ``x`` in ``toJson(x)``,
        ``BinaryData.fromObject(x)``, ``MessageBuilder.withPayload(x).build()`` or plain ``x``.
        None for envelope types / untyped expressions."""
        for _ in range(4):
            if node is None or node.type != "method_invocation":
                break
            nm = sx.text(node.child_by_field_name("name"))
            args = _args(node)
            if nm in SERIALIZERS and args:
                node = args[0]
            elif nm in ("build", "toString", "getBytes"):
                node = node.child_by_field_name("object")
            else:
                break
        ty = self.idx.type_of(node, scope) if node is not None else None
        return ty if ty and js.simple_type(ty) not in ENVELOPE_TYPES else None

    def handler_payload(self, jt: js.JType, m: sx.MethodDecl) -> str | None:
        """Payload of a subscribe handler: the ``T.class`` of a deserializer call in the method
        (``readValue(body, T.class)``), else the first non-envelope parameter type."""
        if m.body is not None:
            for n in self.idx.nodes(m, "method_invocation"):
                if sx.text(n.child_by_field_name("name")) not in DESERIALIZERS:
                    continue
                args = _args(n)
                if len(args) >= 2 and args[-1].type == "class_literal":
                    kids = sx.named_children(args[-1])
                    ty = sx.text(kids[0]) if kids else None
                    if ty and js.simple_type(ty) not in ENVELOPE_TYPES:
                        return ty
        for p in m.params:
            if p.type and js.simple_type(p.type) not in ENVELOPE_TYPES and \
                    not any(a.name in ("Header", "Headers") for a in p.annotations):
                return p.type
        return None

    def _template_send(self, n, scope, servicebus_jms) -> Msg | None:
        msg = self._template_send_msg(n, scope, servicebus_jms)
        if msg is not None:
            args = _args(n)
            if len(args) >= 2:
                msg.payload = self.payload_of(args[-1], scope)
        return msg

    def _template_send_msg(self, n, scope, servicebus_jms) -> Msg | None:
        name = sx.text(n.child_by_field_name("name"))
        obj = n.child_by_field_name("object")
        if obj is None:
            return None
        ty = js.simple_type(self.idx.type_of(obj, scope) or "")
        low = sx.text(obj).lower()
        args = _args(n)
        if not args:
            return None
        line = _nline(n)
        if (ty == "KafkaTemplate" or "kafkatemplate" in low) and name == "send":
            return Msg("publish", "kafka", "kafka-topic", self.idx.resolve_expr(args[0], scope),
                       line, [line], library="spring-kafka")
        # tvsm-be-core (TVS-CPS-BE-BASE-FRAMEWORK) wrapper: KafkaProducerUtil.send{String,Json,
        # Bytes}[Sync|Async](topic, ...)
        if ty == "KafkaProducerUtil" and KAFKA_UTIL_SEND.fullmatch(name):
            return Msg("publish", "kafka", "kafka-topic", self.idx.resolve_expr(args[0], scope),
                       line, [line], library="tvsm-be-core")
        if (ty == "ServiceBusTemplate" or "servicebustemplate" in low) and name in (
                "send", "sendAsync"):
            return Msg("publish", "azure-service-bus", None, self.idx.resolve_expr(args[0], scope),
                       line, [line], library="spring-cloud-azure")
        if (ty in ("JmsTemplate", "JmsMessagingTemplate") or "jmstemplate" in low) and name in (
                "convertAndSend", "send") and len(args) >= 2:
            return Msg("publish", "azure-service-bus" if servicebus_jms else "other", None,
                       self.idx.resolve_expr(args[0], scope), line, [line], library="spring-jms")
        if (ty in ("RabbitTemplate", "AmqpTemplate") or "rabbittemplate" in low) and name in (
                "convertAndSend", "send"):
            if len(args) >= 3:
                return Msg("publish", "rabbitmq", "exchange",
                           self.idx.resolve_expr(args[0], scope), line, [line],
                           library="spring-amqp")
            return Msg("publish", "rabbitmq", "queue", self.idx.resolve_expr(args[0], scope),
                       line, [line], library="spring-amqp")
        if (ty == "StreamBridge" or "streambridge" in low) and name == "send":
            b = self.idx.resolve_expr(args[0], scope)
            if b.kind == "literal" and not b.holes:
                key = f"spring.cloud.stream.bindings.{b.value}.destination"
                return Msg("publish", "stream", None,
                           js.source_of([js.Seg("config", key)]), line, [line],
                           trigger="stream-binding", library="spring-cloud-stream")
            return Msg("publish", "stream", None, js.source_of([js.Seg("unknown", "binding")]),
                       line, [line], library="spring-cloud-stream")
        return None

    def listener_msgs(self, jt: js.JType, m: sx.MethodDecl, servicebus_jms: bool) -> list[Msg]:
        scope = self.idx.method_scope(jt, m)
        out = []
        for a in m.annotations:
            if a.name == "KafkaListener":
                topics = a.args.get("topics", "value", pos=0)
                for t in (topics if isinstance(topics, list) else [topics]):
                    if t is None:
                        continue
                    msg = Msg("subscribe", "kafka", "kafka-topic",
                              self.idx.resolve_value(t, scope), a.line, [a.line],
                              trigger="listener-annotation", handler_line=a.line,
                              library="spring-kafka")
                    g = a.args.get("groupId")
                    if g is not None:
                        msg.subscription = self.idx.resolve_value(g, scope)
                    msg.payload = self.handler_payload(jt, m)
                    out.append(msg)
            elif a.name in ("ServiceBusListener", "JmsListener", "RabbitListener"):
                if a.name == "RabbitListener":
                    dest = a.args.get("queues", "value", pos=0)
                    broker, et, lib, trig = "rabbitmq", "queue", "spring-amqp", \
                        "listener-annotation"
                else:
                    dest = a.args.get("destination", "value", pos=0)
                    broker = "azure-service-bus" if a.name == "ServiceBusListener" or \
                        servicebus_jms else "other"
                    et, lib = None, ("spring-cloud-azure" if a.name == "ServiceBusListener"
                                     else "spring-jms")
                    trig = "jms-listener" if a.name == "JmsListener" else "listener-annotation"
                for d in (dest if isinstance(dest, list) else [dest]):
                    if d is None:
                        continue
                    msg = Msg("subscribe", broker, et, self.idx.resolve_value(d, scope), a.line,
                              [a.line], trigger=trig, handler_line=a.line, library=lib)
                    g = a.args.get("group", "subscription")
                    if g is not None:
                        msg.subscription = self.idx.resolve_value(g, scope)
                        msg.entity_type = msg.entity_type or "topic"
                    msg.payload = self.handler_payload(jt, m)
                    out.append(msg)
        return out

    # ---- send sites ----------------------------------------------------------------------
    def send_sites(self, jt: js.JType, m: sx.MethodDecl) -> list[tuple[str | None, int]]:
        """(bean name or None, line) of ServiceBusSenderClient.sendMessage(s) calls."""
        if m.body is None:
            return []
        scope = self.idx.method_scope(jt, m)
        out = []
        for n in self.idx.nodes(m, "method_invocation"):
            if sx.text(n.child_by_field_name("name")) not in SEND_METHODS:
                continue
            obj = n.child_by_field_name("object")
            if obj is None:
                continue
            ty = js.simple_type(self.idx.type_of(obj, scope) or "")
            if ty not in SENDER_TYPES:
                continue
            out.append((self.idx.qualifier_of(obj, scope), _nline(n)))
        return out

    def message_details(self, jt: js.JType) -> tuple[list, dict, list, list]:
        """(message_types, properties, evidence lines, payloads) from ServiceBusMessage
        construction and setters in a class. ``payloads``: (type text, line) of
        ``new ServiceBusMessage(<serializer>(typed))``."""
        types, props, lines, payloads = [], {}, [], []
        app = []
        for m in jt.methods:
            if m.body is None:
                continue
            scope = None
            for n in self.idx.nodes(m, "object_creation_expression"):
                if js.simple_type(sx.text(n.child_by_field_name("type"))) != "ServiceBusMessage":
                    continue
                args = _args(n)
                if not args:
                    continue
                scope = scope or self.idx.method_scope(jt, m)
                ty = self.payload_of(args[0], scope)
                if ty:
                    payloads.append((ty, sx.line(n)))
            for n in self.idx.nodes(m, "method_invocation"):
                nm = sx.text(n.child_by_field_name("name"))
                args = _args(n)
                if nm == "setSubject" and args:
                    v = sx.decode_string(args[0], "java")
                    if isinstance(v, str):
                        types.append(v)
                        lines.append(_nline(n))
                elif nm == "setSessionId":
                    props["session_id"] = True
                    lines.append(_nline(n))
                elif nm == "setCorrelationId":
                    props["correlation_id"] = True
                elif nm == "setPartitionKey":
                    props["partition_key"] = True
                elif nm == "put" and len(args) == 2:
                    obj = sx.text(n.child_by_field_name("object"))
                    if "getApplicationProperties" in obj or "propert" in obj.lower():
                        k = sx.decode_string(args[0], "java")
                        if isinstance(k, str):
                            v = sx.decode_string(args[1], "java")
                            if k in ("type", "eventType", "messageType") and isinstance(v, str):
                                types.append(v)
                            elif k not in app:
                                app.append(k)
                            lines.append(_nline(n))
        if app:
            props["app_properties"] = sorted(app)
        return sorted(set(types)), props, lines, payloads
