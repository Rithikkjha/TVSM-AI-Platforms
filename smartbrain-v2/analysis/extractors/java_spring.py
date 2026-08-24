"""Extractor for Java (Spring Boot / Spring MVC) repositories.

Handles:
- Spring MVC endpoints: @GetMapping, @PostMapping, @RequestMapping, etc.
- HTTP clients: RestTemplate, WebClient, FeignClient, HttpClient
- Azure Service Bus: @ServiceBusListener, ServiceBusSender, JMS listeners
- Build files: pom.xml (dependencies, parent version, Java version)
- Config: application.properties, application.yml
- Database: spring.datasource.*, spring.data.mongodb.*, etc.

Learnings from Node extractor applied:
- Resolve constants/enums where possible
- Detect variable-based URLs (not just string literals)
- Infer topics from class names (e.g., BookingEventPublisher)
- Detect DB type from dependencies (not just config)
- Handle env var references (${VAR_NAME})
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


class JavaSpringExtractor(BaseExtractor):
    """Extracts structured facts from Java / Spring Boot repos."""

    # --- Endpoint patterns ---
    _ENDPOINT_PATTERNS = [
        # @GetMapping("/path"), @PostMapping("/path"), etc.
        r"@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:value\s*=\s*)?[\"']([^\"']+)[\"']",
        # @GetMapping without path (method-level, inherits class path)
        r"@(Get|Post|Put|Delete|Patch)Mapping\s*$",
        r"@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*\)",
        # @RequestMapping(value = "/path", method = RequestMethod.GET)
        r"@RequestMapping\s*\([^)]*value\s*=\s*[\"']([^\"']+)[\"'][^)]*method\s*=\s*RequestMethod\.(\w+)",
        r"@RequestMapping\s*\([^)]*method\s*=\s*RequestMethod\.(\w+)[^)]*value\s*=\s*[\"']([^\"']+)[\"']",
        # @RequestMapping("/path") — class-level base path
        r"@RequestMapping\s*\(\s*[\"']([^\"']+)[\"']\s*\)",
    ]

    _CLASS_REQUEST_MAPPING = r"@RequestMapping\s*\(\s*(?:value\s*=\s*)?[\"']([^\"']+)[\"']"

    # --- HTTP client patterns ---
    _HTTP_CALL_PATTERNS = [
        # RestTemplate: restTemplate.getForObject("url", ...), restTemplate.postForEntity(url, ...)
        r"restTemplate\.(getForObject|getForEntity|postForObject|postForEntity|exchange|put|delete)\s*\(\s*[\"']([^\"']+)",
        # RestTemplate with variable URL
        r"restTemplate\.(getForObject|getForEntity|postForObject|postForEntity|exchange|put|delete)\s*\(\s*(\w+[\w.]*)",
        # WebClient: webClient.get().uri("url"), webClient.post().uri(url)
        r"webClient\.(get|post|put|delete|patch)\s*\(\s*\)\s*\.uri\s*\(\s*[\"']([^\"']+)",
        r"webClient\.(get|post|put|delete|patch)\s*\(\s*\)\s*\.uri\s*\(\s*(\w+[\w.]*)",
        # FeignClient: @FeignClient(name = "service", url = "${URL}")
        r"@FeignClient\s*\([^)]*(?:url|value)\s*=\s*[\"'\$\{]([^\"'}]+)",
        r"@FeignClient\s*\([^)]*name\s*=\s*[\"']([^\"']+)",
        # HttpClient (Java 11+): HttpClient...uri("url")
        r"HttpRequest\.newBuilder\s*\(\s*\)\s*\.uri\s*\(\s*URI\.create\s*\(\s*[\"']([^\"']+)",
        # Variable-based URLs: String url = config.get("SERVICE_URL")
        r"(?:String|var)\s+(\w*[Uu]rl|\w*URL|\w*[Ee]ndpoint|\w*URI)\s*=",
        # @Value("${property}") for URL injection
        r"@Value\s*\(\s*[\"']\$\{([^}]*(?:url|uri|endpoint|host|base)[^}]*)\}[\"']\s*\)",
        # Environment/config property references
        r"environment\.getProperty\s*\(\s*[\"']([^\"']*(?:url|uri|endpoint|host)[^\"']*)[\"']",
        r"getProperty\s*\(\s*[\"']([^\"']*(?:url|uri|endpoint|host|service)[^\"']*)[\"']",
    ]

    # --- Service bus patterns ---
    _SERVICE_BUS_PUBLISH_PATTERNS = [
        # ServiceBusSenderClient / ServiceBusTemplate with literal topic
        r"ServiceBusSender\w*\s*.*?[\"']([^\"']+)[\"']",
        r"serviceBusTemplate\.send\w*\s*\(\s*[\"']([^\"']+)",
        # .topicName("literal") in builder
        r"\.topicName\s*\(\s*[\"']([^\"']+)[\"']\s*\)",
        # .topicName(variable) — capture variable name
        r"\.topicName\s*\(\s*(\w+)\s*\)",
        # JmsTemplate: jmsTemplate.convertAndSend("topic", ...)
        r"jmsTemplate\.(?:convertAndSend|send)\s*\(\s*[\"']([^\"']+)",
        # @Value for topic names (Spring property injection)
        r"@Value\s*\(\s*\"\$\{spring\.jms\.servicebus\.topic\.([^}\"]+)\}\"",
        r"@Value\s*\(\s*\"\$\{.*?topic[.-]?name[^}]*\}\"[^;]*;\s*private\s+String\s+(\w*[Tt]opic\w*)",
        # topicName / queueName assignment with literal
        r"(?:topicName|destination|queueName)\s*=\s*[\"']([^\"']+)",
        # @SendTo("topic")
        r"@SendTo\s*\(\s*[\"']([^\"']+)",
        # sendMessage on a sender (indicates this class publishes)
        r"(\w*[Ss]ender\w*)\.sendMessage",
        # Publisher/Producer class names
        r"class\s+(\w*[Pp]ublisher\w*)",
        r"class\s+(\w*[Pp]roducer\w*)",
        r"class\s+(\w*[Nn]otifier\w*)",
        # Bean names that indicate sender creation
        r"@Bean.*?\"(\w*[Ss]ender\w*)\"",
        # Queue names from @Value
        r"@Value\s*\(\s*\"\$\{spring\.jms\.servicebus\.queue\.([^}\"]+)\}\"",
    ]

    _SERVICE_BUS_SUBSCRIBE_PATTERNS = [
        # @JmsListener(destination = "topic")
        r"@JmsListener\s*\([^)]*destination\s*=\s*[\"']([^\"']+)",
        # @ServiceBusTopicListener / @ServiceBusQueueListener
        r"@ServiceBus(?:Topic|Queue)Listener\s*\([^)]*(?:topicName|value)\s*=\s*[\"']([^\"']+)",
        # @Value for subscription names (indicates this service subscribes)
        r"@Value\s*\(\s*\"\$\{spring\.jms\.servicebus\.subscription\.([^}\"]+)\}\"",
        # ServiceBusProcessorClient bean creation for specific channel
        r"ServiceBusProcessorClient\s+create\w*For(\w+)",
        # @RabbitListener(queues = "queue")
        r"@RabbitListener\s*\([^)]*queues?\s*=\s*[\"']([^\"']+)",
        # @KafkaListener(topics = "topic")
        r"@KafkaListener\s*\([^)]*topics?\s*=\s*[\"']([^\"']+)",
        # Receiver/Listener/Consumer class names
        r"class\s+(\w*[Rr]eceiver\w*)",
        r"class\s+(\w*[Ll]istener\w*)",
        r"class\s+(\w*[Cc]onsumer\w*)",
        r"class\s+(\w*[Ss]ubscriber\w*)",
    ]

    # --- Database patterns (from application.properties/yml) ---
    _DB_CONFIG_PATTERNS = [
        (r"spring\.datasource\.url\s*=\s*jdbc:(\w+)://([^\s/]+)/(\w+)", "jdbc"),
        (r"spring\.datasource\.driver-class-name\s*=.*?(\w+)Driver", "driver"),
        (r"spring\.data\.mongodb\.uri\s*=\s*mongodb://([^\s]+)", "mongodb"),
        (r"spring\.data\.mongodb\.database\s*=\s*(\w+)", "mongodb_name"),
        (r"spring\.redis\.host\s*=\s*(\S+)", "redis"),
        (r"spring\.datasource\.url\s*=.*?\$\{([^}]+)\}", "env_ref"),
    ]

    async def extract_endpoints(self, files: dict[str, str]) -> list[Endpoint]:
        """Extract API endpoints from Spring MVC annotations."""
        endpoints: list[Endpoint] = []
        seen: set[str] = set()

        for file_path, content in files.items():
            if not self._is_java_source(file_path):
                continue

            # Detect class-level @RequestMapping base path
            class_base = ""
            class_mapping = re.search(self._CLASS_REQUEST_MAPPING, content)
            if class_mapping:
                class_base = class_mapping.group(1)

            # Method-level mappings
            for pattern in self._ENDPOINT_PATTERNS[:3]:  # Get/Post/Put/Delete/PatchMapping
                for match_info in self._find_in_file(content, pattern, file_path):
                    groups = match_info["match"].groups()
                    if len(groups) >= 2:
                        method = groups[0].upper()
                        path = groups[1]
                    elif len(groups) == 1:
                        method = groups[0].upper()
                        path = ""
                    else:
                        continue

                    full_path = f"{class_base}/{path}".replace("//", "/")
                    if not full_path.startswith("/"):
                        full_path = "/" + full_path

                    key = f"{method}:{full_path}"
                    if key not in seen:
                        seen.add(key)
                        endpoints.append(Endpoint(
                            method=method,
                            path=full_path.rstrip("/") or "/",
                            description=self._extract_api_description(content, match_info["line"]),
                            file=match_info["file"],
                        ))

            # @RequestMapping with method specified
            for pattern in self._ENDPOINT_PATTERNS[3:5]:
                for match_info in self._find_in_file(content, pattern, file_path):
                    groups = match_info["match"].groups()
                    # Groups order depends on which pattern matched
                    if "value" in match_info["line_content"].split("method")[0]:
                        path, method = groups[0], groups[1]
                    else:
                        method, path = groups[0], groups[1]

                    full_path = f"{class_base}/{path}".replace("//", "/")
                    if not full_path.startswith("/"):
                        full_path = "/" + full_path

                    key = f"{method.upper()}:{full_path}"
                    if key not in seen:
                        seen.add(key)
                        endpoints.append(Endpoint(
                            method=method.upper(),
                            path=full_path.rstrip("/") or "/",
                            description="",
                            file=match_info["file"],
                        ))

        return endpoints

    async def extract_http_calls(self, files: dict[str, str]) -> list[HttpDependency]:
        """Extract outbound HTTP calls to other services."""
        deps: list[HttpDependency] = []
        seen_targets: set[str] = set()

        for file_path, content in files.items():
            if not self._is_java_source(file_path) and not self._is_config_file(file_path):
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
                    # Skip common false positives
                    if url_or_var in ("url", "uri", "body", "request", "response",
                                      "entity", "result", "null", "void", "String"):
                        continue

                    target, confidence = self.match_to_service(url_or_var)
                    if target in seen_targets:
                        continue
                    seen_targets.add(target)

                    deps.append(HttpDependency(
                        target_service=target,
                        purpose=self._infer_purpose_java(file_path, match_info["line_content"]),
                        evidence=f"{match_info['file']} — {match_info['line_content'][:100]}",
                        confidence=confidence,
                    ))

        return deps

    async def extract_service_bus(
        self, files: dict[str, str]
    ) -> tuple[list[ServiceBusPublish], list[ServiceBusSubscribe]]:
        """Extract service bus publish/subscribe patterns."""
        publishes: list[ServiceBusPublish] = []
        subscribes: list[ServiceBusSubscribe] = []
        seen_pub: set[str] = set()
        seen_sub: set[str] = set()

        for file_path, content in files.items():
            if not self._is_java_source(file_path) and not self._is_config_file(file_path):
                continue

            # Publishers
            for pattern in self._SERVICE_BUS_PUBLISH_PATTERNS:
                for match_info in self._find_in_file(content, pattern, file_path):
                    try:
                        topic = match_info["match"].group(1)
                    except (IndexError, AttributeError):
                        continue
                    if not topic or len(topic) < 2:
                        continue

                    # For class names (Publisher/Producer/Notifier), convert to topic format
                    if re.match(r"^[A-Z]", topic) and any(k in match_info["line_content"] for k in ["class ", "Bean"]):
                        topic = self._class_name_to_topic(topic)
                    # For sender variable names, skip entirely (not a topic)
                    elif "sendMessage" in match_info["line_content"]:
                        continue

                    if not topic or topic in seen_pub:
                        continue
                    if not self._is_valid_topic(topic):
                        continue

                    seen_pub.add(topic)
                    confidence = "high" if not topic.startswith("$") else "medium"
                    publishes.append(ServiceBusPublish(
                        topic=topic,
                        evidence=match_info["file"],
                        confidence=confidence,
                    ))

            # Subscribers
            for pattern in self._SERVICE_BUS_SUBSCRIBE_PATTERNS:
                for match_info in self._find_in_file(content, pattern, file_path):
                    try:
                        topic = match_info["match"].group(1)
                    except (IndexError, AttributeError):
                        continue
                    if not topic or len(topic) < 2:
                        continue

                    # For class names, convert
                    if re.match(r"^[A-Z]", topic) and "class " in match_info["line_content"]:
                        topic = self._class_name_to_topic(topic)
                    # For ProcessorClient bean names like "HighPriorityNotifications"
                    elif re.match(r"^[A-Z]", topic) and "create" in match_info["line_content"]:
                        topic = f"subscription:{self._class_name_to_topic(topic)}"

                    if not topic or topic in seen_sub:
                        continue

                    seen_sub.add(topic)
                    confidence = "high" if not topic.startswith("$") else "medium"
                    subscribes.append(ServiceBusSubscribe(
                        topic=topic,
                        source_service="unknown",
                        evidence=match_info["file"],
                        confidence=confidence,
                    ))

        return publishes, subscribes

    async def extract_build_deps(self, files: dict[str, str]) -> list[BuildDependency]:
        """Extract dependencies from pom.xml or build.gradle."""
        deps: list[BuildDependency] = []

        pom = files.get("pom.xml", "")
        if pom:
            # Extract <dependency> blocks
            dep_pattern = r"<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>(?:\s*<version>([^<]+)</version>)?"
            for match in re.finditer(dep_pattern, pom, re.DOTALL):
                group_id = match.group(1).strip()
                artifact_id = match.group(2).strip()
                version = (match.group(3) or "").strip()
                deps.append(BuildDependency(
                    name=f"{group_id}:{artifact_id}",
                    version=version,
                    type="maven",
                ))

        gradle = files.get("build.gradle", "")
        if gradle:
            # implementation 'group:artifact:version'
            gradle_pattern = r"(?:implementation|api|compile)\s+['\"]([^:]+):([^:]+):?([^'\"]*)['\"]"
            for match in re.finditer(gradle_pattern, gradle):
                deps.append(BuildDependency(
                    name=f"{match.group(1)}:{match.group(2)}",
                    version=match.group(3) or "",
                    type="gradle",
                ))

        return deps

    async def extract_databases(self, files: dict[str, str]) -> list[DatabaseConnection]:
        """Extract database connections from config and dependencies."""
        databases: list[DatabaseConnection] = []
        seen_types: set[str] = set()

        # From pom.xml dependencies
        pom = files.get("pom.xml", "")
        if pom:
            if "mysql-connector" in pom or "mysql" in pom.lower():
                if "mysql" not in seen_types:
                    seen_types.add("mysql")
                    databases.append(DatabaseConnection(type="mysql", name="", evidence="pom.xml — mysql dependency"))
            if "postgresql" in pom or "postgres" in pom:
                if "postgres" not in seen_types:
                    seen_types.add("postgres")
                    databases.append(DatabaseConnection(type="postgres", name="", evidence="pom.xml — postgresql dependency"))
            if "mssql" in pom or "sqlserver" in pom:
                if "mssql" not in seen_types:
                    seen_types.add("mssql")
                    databases.append(DatabaseConnection(type="mssql", name="", evidence="pom.xml — mssql dependency"))
            if "mongodb" in pom or "mongo" in pom:
                if "mongodb" not in seen_types:
                    seen_types.add("mongodb")
                    databases.append(DatabaseConnection(type="mongodb", name="", evidence="pom.xml — mongodb dependency"))
            if "redis" in pom or "jedis" in pom or "lettuce" in pom:
                if "redis" not in seen_types:
                    seen_types.add("redis")
                    databases.append(DatabaseConnection(type="redis", name="", evidence="pom.xml — redis dependency"))

        # From application.properties / application.yml
        for file_path, content in files.items():
            if "application" not in file_path.lower():
                continue
            for pattern, db_type in self._DB_CONFIG_PATTERNS:
                for match_info in self._find_in_file(content, pattern, file_path):
                    groups = match_info["match"].groups()
                    if db_type == "jdbc":
                        actual_type = groups[0]  # mysql, postgresql, sqlserver
                        db_name = groups[2] if len(groups) > 2 else ""
                        if actual_type not in seen_types:
                            seen_types.add(actual_type)
                            databases.append(DatabaseConnection(
                                type=actual_type, name=db_name, evidence=match_info["file"]
                            ))
                    elif db_type == "mongodb":
                        if "mongodb" not in seen_types:
                            seen_types.add("mongodb")
                            databases.append(DatabaseConnection(
                                type="mongodb", name="", evidence=match_info["file"]
                            ))
                    elif db_type == "mongodb_name":
                        # Update existing mongodb entry with name
                        for db in databases:
                            if db.type == "mongodb" and not db.name:
                                db.name = groups[0]
                                break
                    elif db_type == "redis":
                        if "redis" not in seen_types:
                            seen_types.add("redis")
                            databases.append(DatabaseConnection(
                                type="redis", name="", evidence=match_info["file"]
                            ))

        return databases

    # --- Helpers ---

    def _is_java_source(self, path: str) -> bool:
        """Check if file is a Java/Kotlin source file."""
        return (path.endswith((".java", ".kt"))
                and "test" not in path.lower()
                and "Test" not in path.split("/")[-1])

    def _is_config_file(self, path: str) -> bool:
        """Check if file is a config file."""
        return any(k in path.lower() for k in [
            "application.properties", "application.yml", "application.yaml",
            "bootstrap.properties", "bootstrap.yml", "pom.xml", "build.gradle",
        ])

    def _extract_api_description(self, content: str, line_num: int) -> str:
        """Try to extract API description from nearby annotations or comments."""
        lines = content.split("\n")
        # Look at lines above for @ApiOperation or comments
        for i in range(max(0, line_num - 4), line_num - 1):
            if i < len(lines):
                line = lines[i].strip()
                # @ApiOperation("description")
                api_op = re.search(r'@ApiOperation\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)', line)
                if api_op:
                    return api_op.group(1)
                # @Operation(summary = "description")
                op_match = re.search(r'@Operation\s*\([^)]*summary\s*=\s*["\']([^"\']+)', line)
                if op_match:
                    return op_match.group(1)
                # Javadoc or // comment
                if line.startswith("//"):
                    return line[2:].strip()[:100]
                if line.startswith("*") and not line.startswith("*/"):
                    cleaned = line.lstrip("* ").strip()
                    if cleaned and not cleaned.startswith("@"):
                        return cleaned[:100]
        return ""

    def _infer_purpose_java(self, file_path: str, line: str) -> str:
        """Infer purpose from file path and context."""
        parts = file_path.lower().replace("\\", "/").split("/")
        for part in reversed(parts):
            name = part.replace(".java", "").replace(".kt", "")
            name = re.sub(r"(Service|Client|Controller|Handler|Adapter)$", "", name)
            if name and name not in ("src", "main", "java", "com", "service", "impl"):
                return f"{name} integration"
        return ""

    def _is_valid_topic(self, topic: str) -> bool:
        """Check if extracted value looks like a valid topic name."""
        if len(topic) < 3 or len(topic) > 80:
            return False
        # Skip Java keywords and common types
        skip = {"String", "void", "null", "true", "false", "Object", "class",
                "public", "private", "static", "final", "return", "import"}
        if topic in skip:
            return False
        # Skip variable names (camelCase ending with common suffixes)
        variable_suffixes = ("Name", "Client", "String", "Builder", "Sender",
                             "Receiver", "Processor", "Connection", "Config",
                             "Factory", "Template", "Handler", "Manager")
        if any(topic.endswith(s) for s in variable_suffixes):
            return False
        # Skip bean/variable names that are clearly camelCase identifiers
        # (start lowercase, contain uppercase) unless they look like topic paths
        if topic[0].islower() and any(c.isupper() for c in topic[1:]):
            # Allow if it contains dots or hyphens (looks like a topic path)
            if "." not in topic and "-" not in topic:
                return False
        # Skip generic names
        generic = {"topicName", "queueName", "connectionString", "subscriptionName",
                   "topic", "queue", "sender", "receiver", "processor", "this",
                   "message", "context", "config", "service"}
        if topic in generic:
            return False
        if not re.search(r"[a-zA-Z]", topic):
            return False
        return True

    def _class_name_to_topic(self, class_name: str) -> str:
        """Convert class name to topic: BookingEventPublisher → booking-event.

        Handles acronyms: SMSNotifications → sms-notifications
        """
        name = class_name
        for suffix in ("Publisher", "Producer", "Sender", "Listener", "Consumer",
                       "Subscriber", "Handler", "Service", "Processor", "Notifier",
                       "Receiver", "Notifications"):
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        if not name:
            return ""
        # Handle acronyms: "SMSNotification" → "SMS-Notification"
        result = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", name)
        result = re.sub(r"([a-z])([A-Z])", r"\1-\2", result)
        result = result.lower()
        result = re.sub(r"-+", "-", result).strip("-")
        return result
