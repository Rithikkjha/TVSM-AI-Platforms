"""Base class for language-specific extractors."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

from analysis.models.manifest import (
    BuildDependency,
    DatabaseConnection,
    Endpoint,
    HttpDependency,
    ServiceBusPublish,
    ServiceBusSubscribe,
)


class BaseExtractor(ABC):
    """Abstract base for language-specific extractors.

    Each extractor receives the full file tree and a file-fetching function,
    then extracts endpoints, HTTP calls, service bus patterns, etc.
    """

    def __init__(self, known_services: list[str]) -> None:
        """Initialize with the list of known service names for matching."""
        self._known_services = known_services
        # Build lookup for matching URLs/env vars to service names
        self._service_lookup: dict[str, str] = {}
        for svc in known_services:
            # Exact lowercase match
            self._service_lookup[svc.lower()] = svc
            # Normalized (hyphens → underscores)
            self._service_lookup[svc.lower().replace("-", "_")] = svc
            # Without common prefixes
            for prefix in ("tvsm-", "tvs-", "tvsmbe-"):
                if svc.lower().startswith(prefix):
                    self._service_lookup[svc.lower()[len(prefix):]] = svc

    @abstractmethod
    async def extract_endpoints(self, files: dict[str, str]) -> list[Endpoint]:
        """Extract API endpoints from source files."""
        ...

    @abstractmethod
    async def extract_http_calls(self, files: dict[str, str]) -> list[HttpDependency]:
        """Extract outbound HTTP calls to other services."""
        ...

    @abstractmethod
    async def extract_service_bus(
        self, files: dict[str, str]
    ) -> tuple[list[ServiceBusPublish], list[ServiceBusSubscribe]]:
        """Extract service bus publish/subscribe patterns."""
        ...

    @abstractmethod
    async def extract_build_deps(self, files: dict[str, str]) -> list[BuildDependency]:
        """Extract build dependencies from package manager files."""
        ...

    @abstractmethod
    async def extract_databases(self, files: dict[str, str]) -> list[DatabaseConnection]:
        """Extract database connection info from config files."""
        ...

    def match_to_service(self, url_or_var: str) -> tuple[str, str]:
        """Try to match a URL or env var name to a known service.

        Returns (service_name, confidence).
        """
        text = url_or_var.lower()

        # Rule 1: Direct service name in URL/string (full name match)
        for svc in self._known_services:
            if svc.lower() in text:
                return svc, "high"

        # Rule 2: Normalized name match (underscores → hyphens)
        for key, svc in self._service_lookup.items():
            if len(key) > 4 and key in text:
                return svc, "high"

        # Rule 3: Partial keyword match — specific words only
        for svc in self._known_services:
            parts = re.split(r"[-_.]", svc.lower())
            significant_parts = [p for p in parts if len(p) > 4 and p not in
                                 ("service", "backend", "frontend", "testing", "platform",
                                  "common", "shared", "base", "framework", "engine",
                                  "micro", "layer")]
            for part in significant_parts:
                if part in text:
                    return svc, "medium"

        return "unknown", "low"

    def _find_in_file(
        self, content: str, pattern: str, file_path: str
    ) -> list[dict[str, Any]]:
        """Run a regex pattern against file content, returning matches with line numbers."""
        results = []
        for i, line in enumerate(content.split("\n"), 1):
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                results.append({
                    "match": match,
                    "line": i,
                    "line_content": line.strip(),
                    "file": f"{file_path}:{i}",
                })
        return results
