"""Extractor for .NET (ASP.NET Core + .NET Framework) repositories.

Handles both:
- ASP.NET Core: [HttpGet], [Route], IHttpClientFactory, etc.
- .NET Framework: ApiController, RoutePrefix, HttpClient, web.config

Endpoints:
- [HttpGet("path")], [HttpPost("path")], [Route("path")]
- [RoutePrefix("api/v1")] (Framework)
- MapGet/MapPost (minimal APIs in .NET 6+)

HTTP Clients:
- IHttpClientFactory / HttpClient usage
- RestSharp
- Refit interfaces
- WebClient (legacy)

Service Bus:
- Azure.Messaging.ServiceBus (Core)
- Microsoft.Azure.ServiceBus (older)
- NServiceBus
- MassTransit

Config:
- appsettings.json / appsettings.Development.json
- web.config (Framework)
- .csproj (PackageReference, TargetFramework)
- launchSettings.json
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from analysis.extractors.base import BaseExtractor
from analysis.models.manifest import (
    BuildDependency,
    DatabaseConnection,
    Endpoint,
    HttpDependency,
    ServiceBusPublish,
    ServiceBusSubscribe,
)

logger = logging.getLogger(__name__)


class DotNetExtractor(BaseExtractor):
    """Extracts structured facts from .NET / ASP.NET repos."""

    # --- Endpoint patterns ---
    _ENDPOINT_PATTERNS = [
        # [HttpGet("path")], [HttpPost("path")], etc.
        r"\[(Http(?:Get|Post|Put|Delete|Patch))\s*\(\s*\"([^\"]+)\"\s*\)\]",
        # [HttpGet] without path
        r"\[(Http(?:Get|Post|Put|Delete|Patch))\s*\]",
        # [Route("path")]
        r"\[Route\s*\(\s*\"([^\"]+)\"\s*\)\]",
        # Minimal API: app.MapGet("/path", ...)
        r"app\.Map(Get|Post|Put|Delete|Patch)\s*\(\s*\"([^\"]+)\"",
        # [RoutePrefix("api/v1/controller")] — .NET Framework
        r"\[RoutePrefix\s*\(\s*\"([^\"]+)\"\s*\)\]",
    ]

    _CONTROLLER_ROUTE_PATTERN = r"\[Route\s*\(\s*\"([^\"]+)\"\s*\)\]"
    _API_CONTROLLER_PATTERN = r":\s*(?:Controller|ControllerBase|ApiController)"

    # --- HTTP client patterns ---
    _HTTP_CALL_PATTERNS = [
        # HttpClient: _httpClient.GetAsync("url"), PostAsync("url"), etc.
        r"(?:_httpClient|httpClient|client)\.(Get|Post|Put|Delete|Patch)Async\s*\(\s*\"([^\"]+)\"",
        r"(?:_httpClient|httpClient|client)\.(Get|Post|Put|Delete|Patch)Async\s*\(\s*(\w+[\w.]*)",
        # HttpClient with string interpolation: $"{baseUrl}/path"
        r"(?:_httpClient|httpClient|client)\.\w+Async\s*\(\s*\$\"([^\"]+)\"",
        # IHttpClientFactory named clients
        r"CreateClient\s*\(\s*\"([^\"]+)\"",
        # RestSharp: client.Execute(new RestRequest("url"))
        r"RestRequest\s*\(\s*\"([^\"]+)\"",
        # Refit: [Get("/path")], [Post("/path")]
        r"\[(Get|Post|Put|Delete|Patch)\s*\(\s*\"([^\"]+)\"\s*\)\]",
        # Configuration URL references
        r"Configuration\s*\[\s*\"([^\"]*(?:Url|Uri|Endpoint|BaseAddress|Host|Service)[^\"]*)\"\s*\]",
        r"GetValue<string>\s*\(\s*\"([^\"]*(?:Url|Uri|Endpoint|BaseAddress|Host|Service)[^\"]*)\"\s*\)",
        # appsettings references
        r"\"((?:ServiceUrls|ExternalServices|ApiEndpoints)[^\"]*)\"\s*:",
    ]

    # --- Service bus patterns ---
    _SERVICE_BUS_PUBLISH_PATTERNS = [
        # ServiceBusSender: sender.SendMessageAsync(...)
        r"ServiceBusSender\s*.*?\"([^\"]+)\"",
        r"CreateSender\s*\(\s*\"([^\"]+)\"",
        # TopicClient (older SDK)
        r"TopicClient\s*\(\s*[^,]+,\s*\"([^\"]+)\"",
        # NServiceBus: await endpoint.Publish(new Event())
        r"\.Publish\s*\(\s*new\s+(\w+Event\w*)",
        r"\.Send\s*\(\s*new\s+(\w+Command\w*)",
        # MassTransit: await publishEndpoint.Publish<IEvent>(...)
        r"\.Publish<(\w+)>",
        # Topic name in config
        r"\"TopicName\"\s*:\s*\"([^\"]+)\"",
        r"\"QueueName\"\s*:\s*\"([^\"]+)\"",
        # Publisher class names
        r"class\s+(\w*[Pp]ublisher\w*)",
        r"class\s+(\w*[Pp]roducer\w*)",
    ]

    _SERVICE_BUS_SUBSCRIBE_PATTERNS = [
        # ServiceBusProcessor
        r"CreateProcessor\s*\(\s*\"([^\"]+)\"",
        # SubscriptionClient (older SDK)
        r"SubscriptionClient\s*\(\s*[^,]+,\s*\"([^\"]+)\"",
        # NServiceBus: IHandleMessages<Event>
        r"IHandleMessages<(\w+)>",
        # MassTransit: IConsumer<Event>
        r"IConsumer<(\w+)>",
        # Azure Functions ServiceBusTrigger
        r"\[ServiceBusTrigger\s*\(\s*\"([^\"]+)\"",
        # Subscription name in config
        r"\"SubscriptionName\"\s*:\s*\"([^\"]+)\"",
        # Listener/Consumer class names
        r"class\s+(\w*[Ll]istener\w*)",
        r"class\s+(\w*[Cc]onsumer\w*)",
        r"class\s+(\w*[Hh]andler\w*(?:Event|Message|Command))",
    ]

    async def extract_endpoints(self, files: dict[str, str]) -> list[Endpoint]:
        """Extract API endpoints from ASP.NET attributes."""
        endpoints: list[Endpoint] = []
        seen: set[str] = set()

        for file_path, content in files.items():
            if not self._is_cs_source(file_path):
                continue
            # Only look at controller files
            if not self._is_controller(content, file_path):
                continue

            # Detect class-level [Route("api/[controller]")]
            class_route = ""
            route_matches = re.findall(self._CONTROLLER_ROUTE_PATTERN, content)
            if route_matches:
                # First Route attribute is usually the class-level one
                class_route = route_matches[0]
                # Replace [controller] placeholder with inferred name
                if "[controller]" in class_route:
                    ctrl_name = self._infer_controller_name(file_path)
                    class_route = class_route.replace("[controller]", ctrl_name)

            # [HttpGet("path")], [HttpPost("path")]
            for match_info in self._find_in_file(content, self._ENDPOINT_PATTERNS[0], file_path):
                groups = match_info["match"].groups()
                method = groups[0].replace("Http", "").upper()
                path = groups[1]
                full_path = f"{class_route}/{path}".replace("//", "/")
                if not full_path.startswith("/"):
                    full_path = "/" + full_path
                key = f"{method}:{full_path}"
                if key not in seen:
                    seen.add(key)
                    endpoints.append(Endpoint(
                        method=method, path=full_path, description="", file=match_info["file"]
                    ))

            # [HttpGet] without path
            for match_info in self._find_in_file(content, self._ENDPOINT_PATTERNS[1], file_path):
                method = match_info["match"].group(1).replace("Http", "").upper()
                full_path = f"/{class_route}".replace("//", "/") if class_route else "/"
                key = f"{method}:{full_path}"
                if key not in seen:
                    seen.add(key)
                    endpoints.append(Endpoint(
                        method=method, path=full_path, description="", file=match_info["file"]
                    ))

            # Minimal API: app.MapGet("/path", ...)
            for match_info in self._find_in_file(content, self._ENDPOINT_PATTERNS[3], file_path):
                groups = match_info["match"].groups()
                method = groups[0].upper()
                path = groups[1]
                key = f"{method}:{path}"
                if key not in seen:
                    seen.add(key)
                    endpoints.append(Endpoint(
                        method=method, path=path, description="", file=match_info["file"]
                    ))

        return endpoints

    async def extract_http_calls(self, files: dict[str, str]) -> list[HttpDependency]:
        """Extract outbound HTTP calls."""
        deps: list[HttpDependency] = []
        seen_targets: set[str] = set()

        for file_path, content in files.items():
            if not (self._is_cs_source(file_path) or self._is_config_file(file_path)):
                continue

            for pattern in self._HTTP_CALL_PATTERNS:
                for match_info in self._find_in_file(content, pattern, file_path):
                    groups = match_info["match"].groups()
                    url_or_var = ""
                    for g in reversed(groups):
                        if g and len(g) > 2:
                            url_or_var = g
                            break
                    if not url_or_var:
                        continue
                    if url_or_var in ("string", "var", "null", "true", "false", "content"):
                        continue

                    target, confidence = self.match_to_service(url_or_var)
                    if target in seen_targets:
                        continue
                    seen_targets.add(target)

                    deps.append(HttpDependency(
                        target_service=target,
                        purpose=self._infer_purpose_dotnet(file_path),
                        evidence=f"{match_info['file']} — {match_info['line_content'][:100]}",
                        confidence=confidence,
                    ))

        return deps

    async def extract_service_bus(
        self, files: dict[str, str]
    ) -> tuple[list[ServiceBusPublish], list[ServiceBusSubscribe]]:
        """Extract service bus patterns."""
        publishes: list[ServiceBusPublish] = []
        subscribes: list[ServiceBusSubscribe] = []
        seen_pub: set[str] = set()
        seen_sub: set[str] = set()

        for file_path, content in files.items():
            if not (self._is_cs_source(file_path) or self._is_config_file(file_path)):
                continue

            for pattern in self._SERVICE_BUS_PUBLISH_PATTERNS:
                for match_info in self._find_in_file(content, pattern, file_path):
                    topic = match_info["match"].group(1)
                    if not self._is_valid_topic(topic):
                        continue
                    if re.match(r"^[A-Z]", topic) and "class" in match_info["line_content"]:
                        topic = self._class_name_to_topic(topic)
                    if topic and topic not in seen_pub:
                        seen_pub.add(topic)
                        publishes.append(ServiceBusPublish(
                            topic=topic, evidence=match_info["file"], confidence="high"
                        ))

            for pattern in self._SERVICE_BUS_SUBSCRIBE_PATTERNS:
                for match_info in self._find_in_file(content, pattern, file_path):
                    topic = match_info["match"].group(1)
                    if not self._is_valid_topic(topic):
                        continue
                    if re.match(r"^[A-Z]", topic) and "class" in match_info["line_content"]:
                        topic = self._class_name_to_topic(topic)
                    if topic and topic not in seen_sub:
                        seen_sub.add(topic)
                        subscribes.append(ServiceBusSubscribe(
                            topic=topic, source_service="unknown",
                            evidence=match_info["file"], confidence="high"
                        ))

        return publishes, subscribes

    async def extract_build_deps(self, files: dict[str, str]) -> list[BuildDependency]:
        """Extract dependencies from .csproj files."""
        deps: list[BuildDependency] = []

        for file_path, content in files.items():
            if not file_path.endswith(".csproj"):
                continue
            # <PackageReference Include="Package.Name" Version="1.0.0" />
            pattern = r"<PackageReference\s+Include=\"([^\"]+)\"\s+Version=\"([^\"]+)\""
            for match in re.finditer(pattern, content):
                deps.append(BuildDependency(
                    name=match.group(1),
                    version=match.group(2),
                    type="nuget",
                ))

            # Detect target framework
            fw_match = re.search(r"<TargetFramework>([^<]+)</TargetFramework>", content)
            if fw_match:
                deps.append(BuildDependency(
                    name="TargetFramework",
                    version=fw_match.group(1),
                    type="framework",
                ))

        return deps

    async def extract_databases(self, files: dict[str, str]) -> list[DatabaseConnection]:
        """Extract database connections from config and dependencies."""
        databases: list[DatabaseConnection] = []
        seen_types: set[str] = set()

        # From .csproj dependencies
        for file_path, content in files.items():
            if not file_path.endswith(".csproj"):
                continue
            if "Microsoft.EntityFrameworkCore.SqlServer" in content or "System.Data.SqlClient" in content:
                if "sqlserver" not in seen_types:
                    seen_types.add("sqlserver")
                    databases.append(DatabaseConnection(type="sqlserver", name="", evidence=f"{file_path} — SqlServer dependency"))
            if "Npgsql" in content or "PostgreSQL" in content:
                if "postgres" not in seen_types:
                    seen_types.add("postgres")
                    databases.append(DatabaseConnection(type="postgres", name="", evidence=f"{file_path} — Npgsql dependency"))
            if "MongoDB.Driver" in content:
                if "mongodb" not in seen_types:
                    seen_types.add("mongodb")
                    databases.append(DatabaseConnection(type="mongodb", name="", evidence=f"{file_path} — MongoDB.Driver dependency"))
            if "StackExchange.Redis" in content:
                if "redis" not in seen_types:
                    seen_types.add("redis")
                    databases.append(DatabaseConnection(type="redis", name="", evidence=f"{file_path} — StackExchange.Redis dependency"))
            if "MySql.Data" in content or "MySqlConnector" in content:
                if "mysql" not in seen_types:
                    seen_types.add("mysql")
                    databases.append(DatabaseConnection(type="mysql", name="", evidence=f"{file_path} — MySQL dependency"))

        # From appsettings.json — ConnectionStrings section
        for file_path, content in files.items():
            if "appsettings" not in file_path.lower():
                continue
            try:
                config = json.loads(content)
                conn_strings = config.get("ConnectionStrings", {})
                for name, conn_str in conn_strings.items():
                    db_type = self._infer_db_from_connection_string(conn_str)
                    if db_type and db_type not in seen_types:
                        seen_types.add(db_type)
                        databases.append(DatabaseConnection(
                            type=db_type, name=name, evidence=f"{file_path} — ConnectionStrings.{name}"
                        ))
            except (json.JSONDecodeError, AttributeError):
                pass

        # From web.config — connectionStrings section
        for file_path, content in files.items():
            if "web.config" not in file_path.lower():
                continue
            conn_pattern = r"<add\s+name=\"([^\"]+)\"\s+connectionString=\"([^\"]+)\""
            for match in re.finditer(conn_pattern, content):
                name = match.group(1)
                conn_str = match.group(2)
                db_type = self._infer_db_from_connection_string(conn_str)
                if db_type and db_type not in seen_types:
                    seen_types.add(db_type)
                    databases.append(DatabaseConnection(
                        type=db_type, name=name, evidence=f"{file_path} — {name}"
                    ))

        return databases

    # --- Helpers ---

    def _is_cs_source(self, path: str) -> bool:
        """Check if file is a C# source file."""
        return (path.endswith(".cs")
                and "test" not in path.lower()
                and "Test" not in path.split("/")[-1]
                and "obj/" not in path
                and "bin/" not in path)

    def _is_config_file(self, path: str) -> bool:
        """Check if file is a config file."""
        return any(k in path.lower() for k in [
            "appsettings", "web.config", ".csproj", "launchsettings",
            "startup.cs", "program.cs",
        ])

    def _is_controller(self, content: str, file_path: str) -> bool:
        """Check if a file is a controller."""
        if "controller" in file_path.lower():
            return True
        if re.search(self._API_CONTROLLER_PATTERN, content):
            return True
        if "[ApiController]" in content:
            return True
        return False

    def _infer_controller_name(self, file_path: str) -> str:
        """Infer controller name from file path: UsersController.cs → users."""
        filename = file_path.split("/")[-1].replace(".cs", "")
        name = filename.replace("Controller", "")
        return name.lower()

    def _infer_purpose_dotnet(self, file_path: str) -> str:
        """Infer purpose from file path."""
        parts = file_path.replace("\\", "/").split("/")
        for part in reversed(parts):
            name = part.replace(".cs", "")
            name = re.sub(r"(Service|Client|Controller|Handler|Repository)$", "", name)
            if name and name.lower() not in ("src", "services", "clients", "handlers"):
                return f"{name} integration"
        return ""

    def _is_valid_topic(self, topic: str) -> bool:
        """Check if value looks like a valid topic/event name."""
        if len(topic) < 3 or len(topic) > 80:
            return False
        skip = {"string", "void", "null", "true", "false", "object", "var",
                "Task", "async", "await", "return", "class", "public", "private"}
        if topic in skip:
            return False
        return bool(re.search(r"[a-zA-Z]", topic))

    def _class_name_to_topic(self, class_name: str) -> str:
        """Convert class name to topic format."""
        name = class_name
        for suffix in ("Publisher", "Producer", "Sender", "Listener", "Consumer",
                       "Subscriber", "Handler", "Service", "Processor"):
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        if not name:
            return ""
        result = re.sub(r"([A-Z])", r"-\1", name).lower().lstrip("-")
        return re.sub(r"-+", "-", result)

    def _infer_db_from_connection_string(self, conn_str: str) -> str:
        """Infer database type from a connection string."""
        lower = conn_str.lower()
        if "server=" in lower or "data source=" in lower or "sqlserver" in lower:
            return "sqlserver"
        if "host=" in lower and "port=5432" in lower:
            return "postgres"
        if "host=" in lower and "port=3306" in lower:
            return "mysql"
        if "mongodb://" in lower or "mongodb+srv://" in lower:
            return "mongodb"
        if "redis" in lower:
            return "redis"
        # Default for generic ADO.NET connection strings
        if "server=" in lower or "data source=" in lower:
            return "sqlserver"
        return ""
