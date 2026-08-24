"""Extractor for Node.js (Express / NestJS / generic) repositories.

Handles:
- Express routes: app.get(), router.post(), etc.
- NestJS decorators: @Get(), @Post(), @Controller()
- HTTP clients: axios, fetch, httpService, got
- Azure Service Bus: @azure/service-bus patterns
- package.json parsing
- .env.example parsing
- Config file scanning
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


class NodeNestJSExtractor(BaseExtractor):
    """Extracts structured facts from Node.js / NestJS repos."""

    def __init__(self, known_services: list[str]) -> None:
        super().__init__(known_services)
        self._constants: dict[str, str] = {}  # e.g., {"API_ROUTE.SEARCH": "search"}

    def _resolve_constants(self, files: dict[str, str]) -> None:
        """Parse enum/const files to build a lookup table for constant resolution."""
        for file_path, content in files.items():
            if "constant" not in file_path.lower() and "enum" not in file_path.lower():
                continue

            # Parse TypeScript enums: export enum NAME { KEY = 'value', ... }
            current_enum = ""
            for line in content.split("\n"):
                # Detect enum start
                enum_match = re.match(r"\s*export\s+enum\s+(\w+)\s*\{", line)
                if enum_match:
                    current_enum = enum_match.group(1)
                    continue
                if current_enum and "}" in line and "=" not in line:
                    current_enum = ""
                    continue
                if current_enum:
                    # Parse: KEY = 'value' or KEY = "value"
                    val_match = re.match(r"\s*(\w+)\s*=\s*['\"]([^'\"]+)['\"]", line)
                    if val_match:
                        key = f"{current_enum}.{val_match.group(1)}"
                        self._constants[key] = val_match.group(2)

            # Also parse: const X = 'value'
            for line in content.split("\n"):
                const_match = re.match(r"\s*(?:export\s+)?const\s+(\w+)\s*=\s*['\"]([^'\"]+)['\"]", line)
                if const_match:
                    self._constants[const_match.group(1)] = const_match.group(2)

    def _resolve(self, value: str) -> str:
        """Resolve a constant reference to its actual value."""
        if value in self._constants:
            return self._constants[value]
        # Try without enum prefix
        for key, val in self._constants.items():
            if key.endswith(f".{value}"):
                return val
        return value

    # --- Endpoint patterns ---
    _EXPRESS_ROUTE_PATTERNS = [
        # app.get('/path', handler) or router.post('/path', ...)
        r"(?:app|router|this\.router)\.(get|post|put|delete|patch)\s*\(\s*['\"`]([^'\"`]+)",
        # Express Router with path prefix
        r"Router\(\)\s*.*?\.(get|post|put|delete|patch)\s*\(\s*['\"`]([^'\"`]+)",
    ]

    _NESTJS_ROUTE_PATTERNS = [
        # @Get(':id'), @Post(), @Put('status'), etc.
        r"@(Get|Post|Put|Delete|Patch)\s*\(\s*['\"`]([^'\"`]*)['\"`]\s*\)",
        # @Get() with no path
        r"@(Get|Post|Put|Delete|Patch)\s*\(\s*\)",
        # @Post(API_ROUTE.SEARCH) — constant reference
        r"@(Get|Post|Put|Delete|Patch)\s*\(\s*([A-Z_]+\.\w+)\s*\)",
    ]

    _NESTJS_CONTROLLER_PATTERN = r"@Controller\s*\(\s*['\"`]([^'\"`]*)['\"`]\s*\)"

    # --- HTTP client patterns ---
    _HTTP_CALL_PATTERNS = [
        # axios.get('url'), axios.post('url')
        r"axios\.(get|post|put|delete|patch)\s*\(\s*[`'\"]([^`'\"]+)",
        # axios.post(this.variable) or axios.post(VARIABLE) — any variable after axios call
        r"await\s+axios\.(get|post|put|delete|patch)\s*\(\s*(?:this\.)?([A-Za-z_]\w*[Uu]rl\w*)",
        r"await\s+axios\.(get|post|put|delete|patch)\s*\(\s*(?:this\.)?([A-Z][A-Z_]*URL[A-Z_]*)",
        # Catch-all: axios.post(variable, ...) where variable is not a common keyword
        r"axios\.(get|post|put|delete|patch)\s*\(\s*(?:this\.)?([a-zA-Z]\w*(?:[Uu]rl|URL|[Aa]pi|API|[Ee]ndpoint))",
        # fetch('url')
        r"fetch\s*\(\s*[`'\"]([^`'\"]+)",
        # this.httpService calls
        r"(?:this\.)?httpService\.(get|post|put|delete|patch)\s*\(\s*[`'\"]([^`'\"]+)",
        r"(?:this\.)?httpService\.(get|post|put|delete|patch)\s*\(\s*(?:this\.)?([a-zA-Z]\w*)",
        # Template literals: axios.post(`${VAR}/path`)
        r"axios\.\w+\s*\(\s*`\$\{([^}]+)\}([^`]*)`",
        # process.env references that look like service URLs
        r"process\.env\.([\w]*(?:URL|API_URL|ENDPOINT|SERVICE_URL)[\w]*)",
    ]

    # --- Service bus patterns ---
    _SERVICE_BUS_PUBLISH_PATTERNS = [
        # createSender('topic-name')
        r"createSender\s*\(\s*['\"`]([^'\"`]+)",
        # createSender(this.topic) or createSender(topicName)
        r"createSender\s*\(\s*(?:this\.)?(\w+)",
        # sendMessages.*topic
        r"(?:sender|producer|publisher).*?['\"`]([a-zA-Z][\w-]+)['\"`]",
        # topicName: 'booking-created' or this.topic = TOPIC_NAME
        r"(?:topicName|this\.topic)\s*[:=]\s*['\"`]([^'\"`]+)",
        # TOPIC_NAME from config/constants
        r"(?:TOPIC_NAME|topicName|TOPIC)\s*[:=]\s*['\"`]([^'\"`]+)",
        # PublisherService class names (infer topic from class name)
        r"class\s+(\w+Publisher\w*Service)",
        # processPublish method calls (indicates this service publishes)
        r"(?:this\.\w+[Pp]ublisher\w*)\.(processPublish|publish|send)\s*\(",
    ]

    _SERVICE_BUS_SUBSCRIBE_PATTERNS = [
        # createReceiver('topic', 'subscription') or subscribe('topic')
        r"(?:createReceiver|subscribe|createProcessor)\s*\(\s*['\"`]([^'\"`]+)",
        # createReceiver(this.topic) or createReceiver(topicName)
        r"(?:createReceiver|subscribe|createProcessor)\s*\(\s*(?:this\.)?(\w+)",
        # acceptNextSession(topicName, subscriptionName) — Azure Service Bus session listener
        r"acceptNextSession\s*\(\s*(?:this\.)?(\w+)",
        # ServiceBusClient listener initialization
        r"ServiceBusClient\s*\(\s*(?:this\.)?(\w+)",
        # @ServiceBusListener or similar decorator
        r"(?:ServiceBus|EventBus|MessageHandler).*?['\"`]([a-zA-Z][\w-]+)['\"`]",
        # subscriptionName assignment
        r"(?:this\.)?subscriptionName\s*=\s*['\"`]?([^'\"`;\s,]+)",
        # Listener/Consumer/Subscriber class names
        r"class\s+(\w+(?:Listener|Consumer|Subscriber)\w*Service)",
    ]

    # --- Database patterns ---
    _DB_PATTERNS = [
        # mongoose.connect('mongodb://...')
        (r"mongoose\.connect\s*\(\s*[`'\"]([^`'\"]+)", "mongodb"),
        (r"MongoClient\s*\(\s*[`'\"]([^`'\"]+)", "mongodb"),
        # TypeORM / createConnection with type
        (r"type\s*:\s*['\"](\w+)['\"]", "typeorm"),
        # mysql/pg createConnection
        (r"(?:mysql|pg|postgres).*?(?:createConnection|createPool|connect)\s*\(", "sql"),
        # Redis
        (r"(?:Redis|createClient|ioredis)\s*\(", "redis"),
        # process.env with DB in name
        (r"process\.env\.(\w*(?:DB|DATABASE|MONGO|REDIS|MYSQL|PG)\w*)", "env_ref"),
    ]

    async def extract_endpoints(self, files: dict[str, str]) -> list[Endpoint]:
        """Extract API endpoints from Express routes and NestJS decorators."""
        # First, resolve constants from enum files
        self._resolve_constants(files)

        endpoints: list[Endpoint] = []
        seen: set[str] = set()

        for file_path, content in files.items():
            if not self._is_route_file(file_path):
                continue

            # Detect NestJS controller base path
            controller_base = ""
            ctrl_matches = re.findall(self._NESTJS_CONTROLLER_PATTERN, content)
            if ctrl_matches:
                controller_base = ctrl_matches[0]
            # Also check for @Controller(CONSTANT) pattern
            ctrl_const_match = re.search(r"@Controller\s*\(\s*([A-Z_]+\.\w+)\s*\)", content)
            if ctrl_const_match:
                controller_base = self._resolve(ctrl_const_match.group(1))

            # NestJS decorators
            for pattern in self._NESTJS_ROUTE_PATTERNS:
                for match_info in self._find_in_file(content, pattern, file_path):
                    match = match_info["match"]
                    groups = match.groups()
                    method = groups[0].upper() if groups[0] else "GET"
                    raw_path = groups[1] if len(groups) > 1 else ""

                    # Resolve constant references like API_ROUTE.SEARCH → "search"
                    if raw_path and re.match(r"[A-Z_]+\.\w+", raw_path):
                        resolved = self._resolve(raw_path)
                        path = resolved
                    else:
                        path = raw_path

                    # Build full path: /controller_base/path
                    if controller_base and path:
                        full_path = f"/{controller_base}/{path}"
                    elif controller_base:
                        full_path = f"/{controller_base}"
                    elif path:
                        full_path = f"/{path}"
                    else:
                        full_path = "/"

                    # Clean up double slashes
                    full_path = re.sub(r"/+", "/", full_path)

                    key = f"{method}:{full_path}"
                    if key not in seen:
                        seen.add(key)
                        # Try to get description from nearby annotations
                        desc = self._get_endpoint_description(content, match_info["line"])
                        if not desc:
                            desc = self._guess_description(match_info["line_content"])
                        endpoints.append(Endpoint(
                            method=method,
                            path=full_path,
                            description=desc,
                            file=match_info["file"],
                        ))

            # Express routes
            for pattern in self._EXPRESS_ROUTE_PATTERNS:
                for match_info in self._find_in_file(content, pattern, file_path):
                    match = match_info["match"]
                    groups = match.groups()
                    method = groups[0].upper()
                    path = groups[1]
                    key = f"{method}:{path}"
                    if key not in seen:
                        seen.add(key)
                        endpoints.append(Endpoint(
                            method=method,
                            path=path,
                            description=self._guess_description(match_info["line_content"]),
                            file=match_info["file"],
                        ))

        return endpoints

    async def extract_http_calls(self, files: dict[str, str]) -> list[HttpDependency]:
        """Extract outbound HTTP calls to other services."""
        deps: list[HttpDependency] = []
        seen_urls: set[str] = set()

        # Skip patterns — these are NOT HTTP calls
        skip_line_patterns = [
            "getSecret",        # Key Vault reads
            "secretService",    # Key Vault reads
            "configService",    # Config reads (not HTTP)
            "getProperty",      # Config reads
            "JSON.parse",       # Parsing, not calling
            "import ",          # Import statements
            "require(",         # Require statements
        ]

        for file_path, content in files.items():
            if not self._is_source_file(file_path):
                continue

            for pattern in self._HTTP_CALL_PATTERNS:
                for match_info in self._find_in_file(content, pattern, file_path):
                    line_content = match_info["line_content"]

                    # Skip lines that are config/secret reads, not HTTP calls
                    if any(skip in line_content for skip in skip_line_patterns):
                        continue

                    match = match_info["match"]
                    groups = match.groups()
                    url_or_var = ""
                    for g in reversed(groups):
                        if g and len(g) > 2:
                            url_or_var = g
                            break
                    if not url_or_var:
                        continue

                    # Skip common false positives
                    if url_or_var.lower() in ("data", "body", "payload", "request", "response",
                                              "config", "options", "headers", "params", "error",
                                              "result", "null", "content", "message", "tostring",
                                              "json", "string", "undefined"):
                        continue

                    # Deduplicate by URL/variable name
                    if url_or_var in seen_urls:
                        continue
                    seen_urls.add(url_or_var)

                    target, confidence = self.match_to_service(url_or_var)

                    deps.append(HttpDependency(
                        target_service=target,
                        purpose=self._infer_purpose(file_path, line_content),
                        evidence=f"{match_info['file']} — {url_or_var} — {line_content[:80]}",
                        confidence=confidence,
                    ))

        return deps

    async def extract_service_bus(
        self, files: dict[str, str]
    ) -> tuple[list[ServiceBusPublish], list[ServiceBusSubscribe]]:
        """Extract Azure Service Bus publish/subscribe patterns."""
        # Resolve constants first
        self._resolve_constants(files)

        publishes: list[ServiceBusPublish] = []
        subscribes: list[ServiceBusSubscribe] = []
        seen_pub_topics: set[str] = set()
        seen_sub_topics: set[str] = set()

        for file_path, content in files.items():
            if not self._is_source_file(file_path):
                continue

            # Detect publisher service classes (indicates this service publishes)
            pub_class_pattern = r"class\s+(\w*[Pp]ublisher\w*)"
            for match_info in self._find_in_file(content, pub_class_pattern, file_path):
                class_name = match_info["match"].group(1)
                # Infer topic from class name: BookingCreationPublisherService → booking-creation
                topic = self._class_name_to_topic(class_name)
                if topic and topic not in seen_pub_topics:
                    seen_pub_topics.add(topic)
                    publishes.append(ServiceBusPublish(
                        topic=topic,
                        evidence=match_info["file"],
                        confidence="medium",
                    ))

            # Detect literal topic names in createSender / config
            for pattern in self._SERVICE_BUS_PUBLISH_PATTERNS[:4]:  # literal patterns only
                for match_info in self._find_in_file(content, pattern, file_path):
                    topic = match_info["match"].group(1)
                    # Skip method names and common false positives
                    if topic in ("processPublish", "publish", "send", "sendMessage",
                                 "topic", "sender", "this"):
                        continue
                    if not self._looks_like_topic_name(topic):
                        continue
                    if topic not in seen_pub_topics:
                        seen_pub_topics.add(topic)
                        confidence = "high" if not topic.startswith("$") and not topic.startswith("this.") else "low"
                        publishes.append(ServiceBusPublish(
                            topic=topic,
                            evidence=match_info["file"],
                            confidence=confidence,
                        ))

            # Detect subscriber patterns
            for pattern in self._SERVICE_BUS_SUBSCRIBE_PATTERNS[:3]:
                for match_info in self._find_in_file(content, pattern, file_path):
                    topic = match_info["match"].group(1)
                    if not self._looks_like_topic_name(topic):
                        continue
                    if topic in seen_sub_topics:
                        continue
                    seen_sub_topics.add(topic)
                    confidence = "high" if not topic.startswith("$") else "low"
                    subscribes.append(ServiceBusSubscribe(
                        topic=topic,
                        source_service="unknown",
                        evidence=match_info["file"],
                        confidence=confidence,
                    ))

        # Also extract EVENT_TYPE values as published events (from constants)
        event_types = [v for k, v in self._constants.items() if "EVENT_TYPE" in k]
        if event_types and not publishes:
            # If we found event types but no explicit publishers, the service likely
            # publishes these events to a topic
            for evt in event_types[:15]:  # show more events
                if evt not in seen_pub_topics:
                    seen_pub_topics.add(evt)
                    publishes.append(ServiceBusPublish(
                        topic=f"event:{evt}",
                        evidence="src/shared/constants/constants.ts (EVENT_TYPE enum)",
                        confidence="medium",
                    ))

        return publishes, subscribes

    def _class_name_to_topic(self, class_name: str) -> str:
        """Convert a publisher class name to a likely topic name.

        BookingCreationPublisherService → booking-creation
        BookingModificationPublisherService → booking-modification
        ATPHandlerPublisherService → atp-handler
        BookingRefundStatusUpdatePublisherService → booking-refund-status-update
        """
        # Remove common suffixes
        name = class_name
        for suffix in ("PublisherService", "Publisher", "Service"):
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        if not name:
            return ""
        # CamelCase to kebab-case
        result = re.sub(r"([A-Z])", r"-\1", name).lower().lstrip("-")
        # Clean up double hyphens
        result = re.sub(r"-+", "-", result)
        return result

    async def extract_build_deps(self, files: dict[str, str]) -> list[BuildDependency]:
        """Extract dependencies from package.json."""
        deps: list[BuildDependency] = []

        pkg_content = files.get("package.json")
        if not pkg_content:
            return deps

        try:
            pkg = json.loads(pkg_content)
        except json.JSONDecodeError:
            return deps

        for section in ("dependencies", "devDependencies"):
            for name, version in (pkg.get(section) or {}).items():
                deps.append(BuildDependency(
                    name=name,
                    version=str(version).lstrip("^~"),
                    type="npm",
                ))

        return deps

    async def extract_databases(self, files: dict[str, str]) -> list[DatabaseConnection]:
        """Extract database connections from config and source files."""
        databases: list[DatabaseConnection] = []
        seen_types: set[str] = set()

        # First, infer DB type from package.json dependencies
        pkg_content = files.get("package.json")
        if pkg_content:
            try:
                pkg = json.loads(pkg_content)
                all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                if "mssql" in all_deps or "tedious" in all_deps:
                    if "mssql" not in seen_types:
                        seen_types.add("mssql")
                        databases.append(DatabaseConnection(
                            type="mssql",
                            name="",
                            evidence="package.json — mssql/tedious dependency",
                        ))
                if "mysql2" in all_deps or "mysql" in all_deps:
                    if "mysql" not in seen_types:
                        seen_types.add("mysql")
                        databases.append(DatabaseConnection(
                            type="mysql",
                            name="",
                            evidence="package.json — mysql dependency",
                        ))
                if "pg" in all_deps or "postgres" in all_deps:
                    if "postgres" not in seen_types:
                        seen_types.add("postgres")
                        databases.append(DatabaseConnection(
                            type="postgres",
                            name="",
                            evidence="package.json — pg dependency",
                        ))
                if "mongoose" in all_deps or "mongodb" in all_deps:
                    if "mongodb" not in seen_types:
                        seen_types.add("mongodb")
                        databases.append(DatabaseConnection(
                            type="mongodb",
                            name="",
                            evidence="package.json — mongoose/mongodb dependency",
                        ))
                if "ioredis" in all_deps or "redis" in all_deps:
                    if "redis" not in seen_types:
                        seen_types.add("redis")
                        databases.append(DatabaseConnection(
                            type="redis",
                            name="",
                            evidence="package.json — ioredis/redis dependency",
                        ))
            except json.JSONDecodeError:
                pass

        # Then scan config files for connection details (DB name, host)
        for file_path, content in files.items():
            if not (self._is_config_file(file_path) or file_path.endswith(("database.ts", "database.js", "ormconfig.ts", "ormconfig.js"))):
                continue

            # Look for database name in TypeORM config or connection strings
            db_name_patterns = [
                (r"database\s*[:=]\s*['\"]([^'\"]+)", "name"),
                (r"DB_NAME\s*[:=]\s*['\"]([^'\"]+)", "name"),
                (r"dbName\s*[:=]\s*['\"]([^'\"]+)", "name"),
            ]
            for pattern, _ in db_name_patterns:
                for match_info in self._find_in_file(content, pattern, file_path):
                    db_name = match_info["match"].group(1)
                    if db_name and len(db_name) > 2 and db_name not in ("test", "true", "false"):
                        # Update existing DB entry with name
                        for db in databases:
                            if not db.name:
                                db.name = db_name
                                db.evidence += f" | {match_info['file']}"
                                break

        return databases

    # --- Helper methods ---

    def _is_route_file(self, path: str) -> bool:
        """Check if a file is likely to contain route definitions."""
        keywords = ["route", "controller", "handler", "endpoint", "api", "app."]
        return (
            self._is_source_file(path)
            and any(k in path.lower() for k in keywords)
        ) or path.endswith("main.ts") or path.endswith("app.ts")

    def _is_source_file(self, path: str) -> bool:
        """Check if a file is a TypeScript/JavaScript source file."""
        return path.endswith((".ts", ".js", ".mjs")) and "node_modules" not in path and "dist" not in path

    def _is_config_file(self, path: str) -> bool:
        """Check if a file is a config file."""
        config_names = (".env", "config", "ormconfig", "database", "typeorm")
        return any(n in path.lower() for n in config_names) or path.endswith(".json")

    def _guess_description(self, line: str) -> str:
        """Try to extract a description from comments or annotations near the route."""
        # Look for inline comments
        comment_match = re.search(r"//\s*(.+)$", line)
        if comment_match:
            return comment_match.group(1).strip()
        # Look for @ApiOperation or @ApiBody summary in the same line context
        api_op = re.search(r"summary\s*[:=]\s*['\"]([^'\"]+)", line)
        if api_op:
            return api_op.group(1).strip()
        return ""

    def _get_endpoint_description(self, content: str, line_num: int) -> str:
        """Look at lines above the endpoint decorator for @ApiOperation or comments."""
        lines = content.split("\n")
        # Check 5 lines above for @ApiOperation, @ApiBody, or comments
        for i in range(max(0, line_num - 6), line_num - 1):
            if i < len(lines):
                line = lines[i].strip()
                # @ApiOperation({ summary: 'description' })
                api_match = re.search(r"summary\s*[:=]\s*['\"]([^'\"]+)", line)
                if api_match:
                    return api_match.group(1)
                # @ApiBody({ description: '...' })
                body_match = re.search(r"description\s*[:=]\s*['\"]([^'\"]+)", line)
                if body_match:
                    return body_match.group(1)
                # // comment
                if line.startswith("//"):
                    comment = line[2:].strip()
                    if len(comment) > 5:
                        return comment[:100]
        return ""

    def _infer_purpose(self, file_path: str, line: str) -> str:
        """Infer the purpose of an HTTP call from context."""
        # Use file name as hint
        parts = file_path.lower().replace("\\", "/").split("/")
        for part in reversed(parts):
            name = part.replace(".ts", "").replace(".js", "").replace(".service", "")
            if name and name not in ("index", "src", "services", "lib"):
                return f"{name} integration"
        return ""

    def _looks_like_topic_name(self, value: str) -> bool:
        """Check if a string looks like a service bus topic/queue name."""
        # Topic names are typically kebab-case or snake_case, 3-50 chars
        if len(value) < 3 or len(value) > 60:
            return False
        # Skip things that are clearly not topics
        skip = ["http", "https", "localhost", "true", "false", "null", "undefined",
                "TOPIC_PUBLISH", "TOPIC_SUBSCRIBE", "TOPIC_LISTENER", "TOPIC_PUBLISHER",
                "processPublish", "publish", "send", "sendMessage", "subscribe",
                "topic", "queue", "sender", "receiver", "processor", "this",
                "message", "context", "config", "service", "error", "success"]
        if value in skip or value.upper() in [s.upper() for s in skip]:
            return False
        # Skip ALL_CAPS that look like log event types (e.g., TOPIC_PUBLISH)
        if re.match(r"^[A-Z_]+$", value) and "_" in value:
            return False
        # Should contain letters
        if not re.search(r"[a-zA-Z]", value):
            return False
        return True

    def _extract_db_name(self, value: str, db_type: str) -> str:
        """Try to extract database name from a connection string or config value."""
        if db_type == "mongodb":
            # mongodb://host:port/dbname
            match = re.search(r"/([a-zA-Z][\w-]+)(?:\?|$)", value)
            if match:
                return match.group(1)
        return ""

    def _infer_db_type(self, env_var: str) -> str:
        """Infer database type from environment variable name."""
        var = env_var.upper()
        if "MONGO" in var:
            return "mongodb"
        if "REDIS" in var:
            return "redis"
        if "MYSQL" in var:
            return "mysql"
        if "PG" in var or "POSTGRES" in var:
            return "postgres"
        return "unknown"
