"""shared.infra: Dockerfile, compose, k8s/helm, Azure pipelines, GitHub workflows, bicep/terraform
-> ``infra`` items (+ ``scheduled_job`` for k8s CronJobs). Env vars defined here are registered in
the config index (placeholder resolution) and emitted as ``config_key`` items; every value goes
through the classifier. Service Bus entities from IaC are also left in ``ctx.hints`` for messaging.
"""
from __future__ import annotations

import fnmatch
import posixpath
import re

from .. import config_classify as cc
from ..inventory_schema import make_item
from . import configfmt
from .base import ExtractResult, Extractor, RepoContext
from .shared_config import config_key_item

PIPELINE_KEYS = {"trigger", "stages", "jobs", "steps", "pool", "variables"}
K8S_WORKLOADS = {"Deployment": "k8s-deployment", "StatefulSet": "k8s-deployment",
                 "DaemonSet": "k8s-deployment", "Service": "k8s-service",
                 "Ingress": "k8s-ingress", "ConfigMap": "k8s-configmap",
                 "Secret": "k8s-secret-ref", "CronJob": "k8s-cronjob"}
DEPLOY_INPUTS = ("kubernetesServiceConnection", "azureSubscription", "appName", "WebAppName",
                 "functionAppName", "azureResourceGroup", "resourceGroupName", "clusterName",
                 "aksClusterName", "containerRegistry", "dockerRegistryServiceConnection",
                 "connectedServiceNameARM", "ConnectedServiceName")


def _yaml_like(path: str) -> bool:
    return path.endswith((".yml", ".yaml"))


def scope(path: str) -> str | None:
    name = posixpath.basename(path)
    dirs = [d.lower() for d in path.split("/")[:-1]]
    if name.startswith("Dockerfile") or name.endswith((".Dockerfile", ".dockerfile")):
        return "dockerfile"
    if fnmatch.fnmatch(name, "docker-compose*.y*ml") or fnmatch.fnmatch(name, "compose*.y*ml"):
        return "compose"
    if path.startswith(".github/workflows/") and _yaml_like(path):
        return "github"
    if name.endswith(".bicep"):
        return "bicep"
    if name.endswith(".tf"):
        return "terraform"
    if _yaml_like(path):
        if re.fullmatch(r"values(-.+)?\.ya?ml", name) and ("helm" in dirs or "charts" in dirs
                                                          or "chart" in dirs):
            return "helm"
        return "yaml?"  # content-sniffed: k8s manifest or azure pipeline
    return None


def _env_list(spec) -> list[tuple[str, object]]:
    """compose/k8s/workflow env: dict or list of ``K=V`` / ``{name, value}``."""
    out = []
    if isinstance(spec, dict):
        out = [(str(k), v) for k, v in spec.items()]
    elif isinstance(spec, list):
        for e in spec:
            if isinstance(e, str):
                k, _, v = e.partition("=")
                out.append((k.strip(), v if _ else None))
            elif isinstance(e, dict) and "name" in e:
                out.append((str(e["name"]), e.get("value")))
    return out


def _lines_by_path(doc) -> dict:
    return {p: ln for p, _, ln in doc.entries}


def _near(lines: dict, path: tuple, default: int) -> int:
    while path:
        if path in lines:
            return lines[path]
        path = path[:-1]
    return default


class SharedInfra(Extractor):
    id = "shared.infra"
    stacks = ()
    extractor_version = "0.1.0"

    def extract(self, ctx: RepoContext, subproject: str | None) -> ExtractResult:
        res = ExtractResult()
        for path in ctx.paths(subproject, lambda e: scope(e["path"]) is not None):
            kind = scope(path)
            text = ctx.read_text(path)
            if text is None:
                continue
            if kind == "yaml?":
                head = text[:20000]
                if not (re.search(r"^apiVersion\s*:", head, re.M) and re.search(r"^kind\s*:", head,
                                                                                 re.M)) and \
                        not any(re.search(rf"^{k}\s*:", head, re.M) for k in PIPELINE_KEYS):
                    continue  # not infra: not opened
            getattr(self, "_" + kind.rstrip("?").replace("yaml", "yaml_sniffed"))(ctx, path, text,
                                                                                  res)
        return res

    # ---- helpers ---------------------------------------------------------------------------
    def _env_entries(self, ctx, res, path, pairs, provided_by, frm, env="default"):
        """[(name, value, line)] -> infra env list; registers + emits config_key items."""
        out = []
        for name, value, ln in pairs:
            if not name:
                continue
            c = cc.classify(name, value, file=path)
            entry = {"name": name, "from": frm}
            if c.record_value is not None:
                entry["value"] = c.record_value
            out.append(entry)
            if value is not None and not isinstance(value, (dict, list)):
                ctx.config.add_env(name, value, env, path, ln, ctx.subproject_of(path),
                                   provided_by)
            res.items.append(config_key_item(ctx, self, name, value, path, ln, env, provided_by))
        return sorted(out, key=lambda e: e["name"])

    def _infra(self, ctx, res, path, lines, infra_kind, name, **attrs):
        attrs.update({"infra_kind": infra_kind, "name": name})
        ev = [ctx.evidence(path, ln) for ln in sorted(set(lines))] or [ctx.evidence(path, 1)]
        res.items.append(make_item("infra", ctx.subproject_of(path), None, attrs, ev, self))

    # ---- Dockerfile ------------------------------------------------------------------------
    def _dockerfile(self, ctx, path, text, res):
        r = configfmt.parse_dockerfile(text)
        stages, bases, ports, env_pairs, lines = set(), [], [], [], []
        for instr, args, ln in r.entries:
            if instr == "FROM":
                m = re.match(r"(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?", args, re.I)
                if m:
                    img = m.group(1)
                    if img.lower() not in stages and img not in bases:
                        bases.append(img)
                    if m.group(2):
                        stages.add(m.group(2).lower())
                lines.append(ln)
            elif instr == "EXPOSE":
                ports += [p for p in args.split() if p not in ports]
                lines.append(ln)
            elif instr == "ENV":
                env_pairs += [(k, v, ln) for k, v in configfmt.docker_kv(args)]
                lines.append(ln)
        env = self._env_entries(ctx, res, path, env_pairs, "unknown", "dockerfile")
        self._infra(ctx, res, path, lines, "dockerfile", path, image=None, base_images=bases,
                    ports=ports, env=env)
        res.touch(path, "full" if r.ok else "partial", r.error)

    # ---- compose ---------------------------------------------------------------------------
    def _compose(self, ctx, path, text, res):
        docs, ok, err = configfmt.yaml_with_lines(text)
        for doc in docs:
            lines = _lines_by_path(doc)
            services = doc.data.get("services") if isinstance(doc.data, dict) else None
            if not isinstance(services, dict):
                continue
            for sname in sorted(services):
                svc = services[sname] if isinstance(services[sname], dict) else {}
                base = ("services", sname)
                pairs = []
                env_spec = svc.get("environment")
                for i, (k, v) in enumerate(_env_list(env_spec)):
                    ln = lines.get(base + ("environment", k)) or lines.get(
                        base + ("environment", i)) or lines.get(base, 1)
                    pairs.append((k, v, ln))
                env = self._env_entries(ctx, res, path, pairs, "unknown", "compose")
                ports = [str(p) for p in svc.get("ports") or [] if isinstance(p, (str, int))]
                img = svc.get("image") if isinstance(svc.get("image"), str) else None
                self._infra(ctx, res, path, [lines.get(base, 1)], "compose-service", str(sname),
                            image=img, ports=ports, env=env)
        res.touch(path, "full" if ok else "partial", err)

    # ---- k8s / pipelines (content-sniffed YAML) --------------------------------------------
    def _yaml_sniffed(self, ctx, path, text, res):
        docs, ok, err = configfmt.yaml_with_lines(text)
        partial = not ok
        for doc in docs:
            d = doc.data
            if not isinstance(d, dict):
                continue
            if "apiVersion" in d and "kind" in d:
                partial |= not self._k8s(ctx, path, doc, res)
            elif PIPELINE_KEYS & set(d):
                self._pipeline(ctx, path, doc, res)
        if not docs and ok:
            partial = True
        res.touch(path, "partial" if partial else "full", err)

    def _k8s(self, ctx, path, doc, res) -> bool:
        d = doc.data
        lines = _lines_by_path(doc)
        kind = str(d.get("kind"))
        ik = K8S_WORKLOADS.get(kind)
        meta = d.get("metadata") if isinstance(d.get("metadata"), dict) else {}
        name = str(meta.get("name") or posixpath.basename(path))
        ns = meta.get("namespace") if isinstance(meta.get("namespace"), str) else None
        ln = lines.get(("metadata", "name"), doc.start_line)
        if ik is None:
            return True
        spec = d.get("spec") if isinstance(d.get("spec"), dict) else {}
        attrs = {"namespace": ns}
        if kind in ("Deployment", "StatefulSet", "DaemonSet", "CronJob"):
            pod_path = ("spec", "template", "spec")
            pod = (spec.get("template") or {}).get("spec") if kind != "CronJob" else (
                ((spec.get("jobTemplate") or {}).get("spec") or {}).get("template") or {}).get(
                "spec")
            if kind == "CronJob":
                pod_path = ("spec", "jobTemplate", "spec", "template", "spec")
            pod = pod if isinstance(pod, dict) else {}
            cms, secs, ports, pairs = set(), set(), [], []
            image = None
            for ci, c in enumerate(pod.get("containers") or []):
                if not isinstance(c, dict):
                    continue
                image = image or c.get("image")
                for p in c.get("ports") or []:
                    if isinstance(p, dict) and p.get("containerPort") is not None:
                        ports.append(str(p["containerPort"]))
                for ei, e in enumerate(c.get("env") or []):
                    if not isinstance(e, dict) or "name" not in e:
                        continue
                    vf = e.get("valueFrom") or {}
                    if isinstance(vf, dict) and isinstance(vf.get("secretKeyRef"), dict):
                        secs.add(str(vf["secretKeyRef"].get("name")))
                        continue  # secret: name only, no config value
                    if isinstance(vf, dict) and isinstance(vf.get("configMapKeyRef"), dict):
                        cms.add(str(vf["configMapKeyRef"].get("name")))
                    pairs.append((str(e["name"]), e.get("value"),
                                  lines.get(pod_path + ("containers", ci, "env", ei, "name"), ln)))
                for ef in c.get("envFrom") or []:
                    if isinstance(ef, dict):
                        if isinstance(ef.get("configMapRef"), dict):
                            cms.add(str(ef["configMapRef"].get("name")))
                        if isinstance(ef.get("secretRef"), dict):
                            secs.add(str(ef["secretRef"].get("name")))
            attrs.update(image=image, ports=ports, configmap_refs=sorted(cms),
                         secret_refs=sorted(secs),
                         env=self._env_entries(ctx, res, path, pairs, "k8s-configmap", "k8s"))
            if kind == "CronJob" and spec.get("schedule"):
                sline = lines.get(("spec", "schedule"), ln)
                res.items.append(make_item(
                    "scheduled_job", ctx.subproject_of(path), f"{path}:{sline}",
                    {"trigger_type": "k8s-cronjob", "expression": str(spec["schedule"]),
                     "expression_from": "literal", "timezone": spec.get("timeZone"),
                     "handler": f"{path}:{sline}", "name": name},
                    [ctx.evidence(path, sline)], self))
        elif kind == "Service":
            attrs["ports"] = [str(p.get("port")) for p in spec.get("ports") or []
                              if isinstance(p, dict) and p.get("port") is not None]
        elif kind == "Ingress":
            hosts, paths_ = [], []
            for rule in spec.get("rules") or []:
                if not isinstance(rule, dict):
                    continue
                if rule.get("host"):
                    hosts.append(str(rule["host"]))
                for p in ((rule.get("http") or {}).get("paths") or []):
                    if not isinstance(p, dict):
                        continue
                    be = p.get("backend") or {}
                    svc = be.get("service") or {}
                    port = (svc.get("port") or {}).get("number") or (svc.get("port") or {}).get(
                        "name") or be.get("servicePort")
                    paths_.append({"path": p.get("path"),
                                   "backend_service": svc.get("name") or be.get("serviceName"),
                                   "port": str(port) if port is not None else None})
            attrs.update(hosts=sorted(set(hosts)), paths=paths_)
        elif kind == "ConfigMap":
            data = d.get("data") if isinstance(d.get("data"), dict) else {}
            pairs = [(str(k), v, lines.get(("data", k), ln)) for k, v in sorted(data.items())]
            attrs["env"] = self._env_entries(ctx, res, path, pairs, "k8s-configmap", "k8s")
        elif kind == "Secret":
            data = {**(d.get("data") or {}), **(d.get("stringData") or {})} if isinstance(
                d.get("data") or {}, dict) else {}
            attrs["secret_refs"] = sorted(str(k) for k in data)  # key names only
        self._infra(ctx, res, path, [ln], ik, name, **attrs)
        return True

    def _pipeline(self, ctx, path, doc, res):
        d = doc.data
        lines = _lines_by_path(doc)
        variables, groups, envs, targets = [], set(), set(), set()
        pairs = []

        def collect_vars(spec, base):
            if isinstance(spec, dict):
                for k, v in spec.items():
                    pairs.append((str(k), v, lines.get(base + (k,), doc.start_line)))
            elif isinstance(spec, list):
                for i, v in enumerate(spec):
                    if isinstance(v, dict) and "group" in v:
                        groups.add(str(v["group"]))
                    elif isinstance(v, dict) and "name" in v:
                        pairs.append((str(v["name"]), v.get("value"),
                                      lines.get(base + (i, "name"), doc.start_line)))

        def visit(node, p):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k == "variables" and p != ():
                        collect_vars(v, p + (k,))
                    elif k == "environment":
                        if isinstance(v, str):
                            envs.add(v)
                        elif isinstance(v, dict) and v.get("name"):
                            envs.add(str(v["name"]))
                    elif k == "inputs" and isinstance(v, dict):
                        for ik in DEPLOY_INPUTS:
                            if isinstance(v.get(ik), str):
                                targets.add(f"{ik}={v[ik]}")
                    visit(v, p + (k,))
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    visit(v, p + (i,))

        collect_vars(d.get("variables"), ("variables",))
        visit(d, ())
        for prm in d.get("parameters") or []:
            if isinstance(prm, dict) and str(prm.get("name", "")).lower() == "environments":
                for e in prm.get("default") or []:
                    if isinstance(e, dict) and e.get("name"):
                        envs.add(str(e["name"]))
                    elif isinstance(e, str):
                        envs.add(e)
        for name, value, ln in pairs:
            c = cc.classify(name, value, file=path)
            v = {"name": name, "secret": c.secret}
            if c.record_value is not None:
                v["value"] = c.record_value
            variables.append(v)
            if value is not None and not isinstance(value, (dict, list)):
                ctx.config.add_env(name, value, "default", path, ln, ctx.subproject_of(path),
                                   "pipeline")
        variables.sort(key=lambda v: v["name"])
        ln = lines.get(("trigger",)) or lines.get(("stages",)) or lines.get(("jobs",)) or \
            doc.start_line
        self._infra(ctx, res, path, [ln], "azure-pipeline", path, variables=variables,
                    variable_groups=sorted(groups), environments=sorted(envs),
                    deploy_targets=sorted(targets))

    # ---- helm values -----------------------------------------------------------------------
    def _helm(self, ctx, path, text, res):
        docs, ok, err = configfmt.yaml_with_lines(text)
        for doc in docs:
            d = doc.data if isinstance(doc.data, dict) else {}
            lines = _lines_by_path(doc)
            img = d.get("image")
            image = None
            if isinstance(img, dict) and img.get("repository"):
                image = f"{img['repository']}:{img.get('tag')}" if img.get("tag") else str(
                    img["repository"])
            hosts = []
            ing = d.get("ingress") if isinstance(d.get("ingress"), dict) else {}
            for h in ing.get("hosts") or []:
                if isinstance(h, dict) and h.get("host"):
                    hosts.append(str(h["host"]))
                elif isinstance(h, str):
                    hosts.append(h)
            pairs = [(k, v, lines.get(("env", k)) or lines.get(("env", i, "name"), 1))
                     for i, (k, v) in enumerate(_env_list(d.get("env")))]
            env = self._env_entries(ctx, res, path, pairs, "k8s-configmap", "helm",
                                    cc.env_from_filename(path))
            ln = lines.get(("image",)) or lines.get(("ingress",)) or doc.start_line
            self._infra(ctx, res, path, [ln], "helm-values", path, image=image,
                        hosts=sorted(set(hosts)), env=env)
        res.touch(path, "full" if ok else "partial", err)

    # ---- GitHub workflows ------------------------------------------------------------------
    def _github(self, ctx, path, text, res):
        docs, ok, err = configfmt.yaml_with_lines(text)
        for doc in docs:
            d = doc.data if isinstance(doc.data, dict) else {}
            lines = _lines_by_path(doc)
            pairs, envs = [], set()

            def visit(node, p):
                if isinstance(node, dict):
                    for k, v in node.items():
                        if k == "env" and isinstance(v, dict):
                            pairs.extend((str(n), val, lines.get(p + (k, n), doc.start_line))
                                         for n, val in v.items())
                        elif k == "environment":
                            if isinstance(v, str):
                                envs.add(v)
                            elif isinstance(v, dict) and v.get("name"):
                                envs.add(str(v["name"]))
                        visit(v, p + (k,))
                elif isinstance(node, list):
                    for i, v in enumerate(node):
                        visit(v, p + (i,))

            visit(d, ())
            secrets = sorted(set(re.findall(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}", text)))
            variables = []
            for name, value, _ln in pairs:
                c = cc.classify(name, value, file=path)
                v = {"name": name, "secret": c.secret}
                if c.record_value is not None:
                    v["value"] = c.record_value
                variables.append(v)
            ln = lines.get(("name",)) or lines.get(("on",)) or lines.get(("True",)) or doc.start_line
            self._infra(ctx, res, path, [ln], "github-workflow", str(d.get("name") or path),
                        variables=sorted(variables, key=lambda v: v["name"]),
                        environments=sorted(envs), secret_refs=secrets)
        res.touch(path, "full" if ok else "partial", err)

    # ---- IaC (regex -> partial) ------------------------------------------------------------
    _BICEP_RES = re.compile(r"""resource\s+\w+\s+'Microsoft\.ServiceBus/namespaces(/(topics|queues|"""
                            r"""topics/subscriptions))?@[^']*'""")
    _TF_RES = re.compile(r'resource\s+"azurerm_servicebus_(namespace|topic|queue|subscription)"\s+'
                         r'"[^"]+"\s*\{')

    def _iac(self, ctx, path, text, res, infra_kind, rx, type_of):
        lines = ctx.lines(path)
        entities, ev_lines = [], []
        i = 0
        while i < len(lines):
            m = rx.search(lines[i])
            if not m:
                i += 1
                continue
            etype = type_of(m)
            block, depth, j = [], 0, i
            while j < len(lines):
                block.append(lines[j])
                depth += lines[j].count("{") - lines[j].count("}")
                j += 1
                if depth <= 0 and "{" in "".join(block):
                    break
            body = "\n".join(block)
            nm = re.search(r"""^\s*name\s*[:=]\s*['"]([^'"]+)['"]""", body, re.M)
            md = re.search(r"max_?[Dd]elivery_?[Cc]ount\s*[:=]\s*(\d+)", body)
            dl = re.search(r"dead_?[Ll]ettering_?[Oo]n_?[Mm]essage_?[Ee]xpiration\s*[:=]\s*(\w+)",
                           body)
            if etype != "namespace":
                entities.append({"name": nm.group(1) if nm else None, "type": etype,
                                 "max_delivery": int(md.group(1)) if md else None,
                                 "dead_letter": (dl.group(1).lower() == "true") if dl else None})
                ev_lines.append(i + 1)
            i = j
        if entities:
            ctx.hints.setdefault("servicebus_entities", []).extend(
                dict(e, file=path) for e in entities)
            self._infra(ctx, res, path, ev_lines, infra_kind, path,
                        servicebus_entities=entities)
        res.touch(path, "partial")

    def _bicep(self, ctx, path, text, res):
        self._iac(ctx, path, text, res, "bicep", self._BICEP_RES,
                  lambda m: {"topics": "topic", "queues": "queue",
                             "topics/subscriptions": "subscription"}.get(m.group(2) or "",
                                                                         "namespace"))

    def _terraform(self, ctx, path, text, res):
        self._iac(ctx, path, text, res, "terraform", self._TF_RES, lambda m: m.group(1))
