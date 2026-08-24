"""Catalog Loader — loads and caches estimation config files.

Handles:
- config/estimation_catalog.json (effort values, multipliers, overheads)
- config/system_dependencies.json (system graph, hubs, integration links)
- config/estimation_blueprint.md (LLM prompt context, parsed by section)

Uses TTL-based in-memory cache (5 minutes) so edits take effect without restart.
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Cache TTL in seconds
CACHE_TTL = 300  # 5 minutes

# Base config directory
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"

# Default catalog (hardcoded fallback if file missing/corrupt)
_DEFAULT_CATALOG = {
    "version": "fallback",
    "engine": "catalog",
    "effortTable": {},
    "systemMultipliers": {},
    "overheadFactors": {
        "teamSize": {"1-2": 1.0, "3-5": 1.1, "6-10": 1.2, "11+": 1.35},
        "crossDomain": 1.2,
        "techFamiliarity": {"proficient": 1.0, "learning": 1.25, "unfamiliar": 1.5},
        "dataVolume": {"<1K": 1.0, "1K-10K": 1.05, "10K-100K": 1.15, "100K-1M": 1.3, ">1M": 1.5},
        "deploymentTopology": {"single_region": 1.0, "multi_region_2_3": 1.2, "multi_country_4_10": 1.35, "multi_country_10+": 1.5, "hybrid": 1.3, "on_prem": 1.15},
        "security": {"standard": 1.0, "pii": 1.15, "payment": 1.2, "pii_and_payment": 1.3},
        "legacyDebt": {"modern": 1.0, "moderate": 1.15, "heavy": 1.3},
    },
    "integrationPatternCosts": {},
    "hubSurcharges": {},
    "documentationOverhead": 0.05,
    "aiProductivity": {"globalMultiplier": 1.0, "perCategory": {}},
    "sanityChecks": {"minEffort": {}, "maxEffort": {}},
    "disciplineMapping": {
        "frontend": "Digital Engineering",
        "backendCrud": "Digital Engineering",
        "backendLogic": "Digital Engineering",
        "integration": "Digital Engineering",
        "sap": "Digital Engineering",
        "qa": "QA/Testing",
        "devops": "DevOps",
    },
}

_DEFAULT_DEPENDENCIES = {
    "version": "fallback",
    "systems": {},
    "hubSystems": [],
    "integrationLinks": [],
    "crossDomainOverhead": {},
    "criticalPathChains": [],
}


class CatalogLoader:
    """Loads and caches estimation catalog and system dependencies with TTL."""

    def __init__(self):
        self._catalog_cache: Optional[dict[str, Any]] = None
        self._catalog_cache_time: float = 0
        self._deps_cache: Optional[dict[str, Any]] = None
        self._deps_cache_time: float = 0
        self._blueprint_cache: Optional[str] = None
        self._blueprint_cache_time: float = 0

    def load_catalog(self) -> dict[str, Any]:
        """Load config/estimation_catalog.json with TTL cache.

        Returns:
            Parsed catalog dict with effort tables, multipliers, etc.
            Falls back to hardcoded defaults if file missing/corrupt.
        """
        now = time.time()
        if self._catalog_cache and (now - self._catalog_cache_time) < CACHE_TTL:
            return self._catalog_cache

        catalog_path = CONFIG_DIR / "estimation_catalog.json"
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)

            # Structural validation
            self._validate_catalog(catalog)

            self._catalog_cache = catalog
            self._catalog_cache_time = now
            logger.info(
                f"Loaded estimation catalog v{catalog.get('version', '?')} "
                f"({len(catalog.get('effortTable', {}))} units)"
            )
            return catalog

        except FileNotFoundError:
            logger.warning(f"Catalog file not found at {catalog_path}. Using defaults.")
            self._catalog_cache = _DEFAULT_CATALOG
            self._catalog_cache_time = now
            return _DEFAULT_CATALOG

        except (json.JSONDecodeError, ValueError) as exc:
            logger.error(f"Failed to parse catalog: {exc}. Using defaults.")
            self._catalog_cache = _DEFAULT_CATALOG
            self._catalog_cache_time = now
            return _DEFAULT_CATALOG

    def load_dependencies(self) -> dict[str, Any]:
        """Load config/system_dependencies.json with TTL cache.

        Returns:
            Parsed dependencies dict with systems, links, hubs.
            Falls back to hardcoded defaults if file missing/corrupt.
        """
        now = time.time()
        if self._deps_cache and (now - self._deps_cache_time) < CACHE_TTL:
            return self._deps_cache

        deps_path = CONFIG_DIR / "system_dependencies.json"
        try:
            with open(deps_path, "r", encoding="utf-8") as f:
                deps = json.load(f)

            # Basic validation
            if "systems" not in deps or "hubSystems" not in deps:
                raise ValueError("Missing required keys: systems, hubSystems")

            self._deps_cache = deps
            self._deps_cache_time = now
            logger.info(
                f"Loaded system dependencies v{deps.get('version', '?')} "
                f"({len(deps.get('systems', {}))} systems, "
                f"{len(deps.get('integrationLinks', []))} links)"
            )
            return deps

        except FileNotFoundError:
            logger.warning(f"Dependencies file not found at {deps_path}. Using defaults.")
            self._deps_cache = _DEFAULT_DEPENDENCIES
            self._deps_cache_time = now
            return _DEFAULT_DEPENDENCIES

        except (json.JSONDecodeError, ValueError) as exc:
            logger.error(f"Failed to parse dependencies: {exc}. Using defaults.")
            self._deps_cache = _DEFAULT_DEPENDENCIES
            self._deps_cache_time = now
            return _DEFAULT_DEPENDENCIES

    def load_blueprint(self) -> str:
        """Load the full estimation_blueprint.md content.

        Returns:
            Full markdown content of the blueprint file.
        """
        now = time.time()
        if self._blueprint_cache and (now - self._blueprint_cache_time) < CACHE_TTL:
            return self._blueprint_cache

        blueprint_path = CONFIG_DIR / "estimation_blueprint.md"
        try:
            with open(blueprint_path, "r", encoding="utf-8") as f:
                content = f.read()

            self._blueprint_cache = content
            self._blueprint_cache_time = now
            logger.info(f"Loaded estimation blueprint ({len(content)} chars)")
            return content

        except FileNotFoundError:
            logger.warning(f"Blueprint file not found at {blueprint_path}.")
            return ""

    def load_blueprint_section(self, section: str) -> str:
        """Load a specific section from the blueprint markdown.

        Args:
            section: Section identifier (e.g., "§1", "§2", "§3", "§4", "§5")

        Returns:
            Content of the requested section, or empty string if not found.
        """
        full_content = self.load_blueprint()
        if not full_content:
            return ""

        # Parse sections by ## headings containing the section number
        pattern = rf"## {re.escape(section)}\."
        matches = list(re.finditer(pattern, full_content))

        if not matches:
            # Try alternate pattern (e.g., "§1. " or "§1 ")
            pattern = rf"## {re.escape(section)}[\.\s]"
            matches = list(re.finditer(pattern, full_content))

        if not matches:
            logger.warning(f"Section '{section}' not found in blueprint.")
            return ""

        start = matches[0].start()

        # Find the next ## heading after this one
        next_section = re.search(r"\n## §\d+\.", full_content[start + 10:])
        if next_section:
            end = start + 10 + next_section.start()
        else:
            # Check for major separator
            separator = full_content.find("═══", start + 10)
            if separator > 0:
                end = separator
            else:
                end = len(full_content)

        return full_content[start:end].strip()

    def get_engine_mode(self) -> str:
        """Check if catalog engine or legacy engine should be used.

        Returns:
            'catalog' or 'legacy'
        """
        catalog = self.load_catalog()
        return catalog.get("engine", "catalog")

    def get_unit_ids(self) -> set[str]:
        """Get the set of valid unit IDs from the catalog.

        Returns:
            Set of valid unit ID strings (e.g., {'FE-01', 'BE-05', ...})
        """
        catalog = self.load_catalog()
        return set(catalog.get("effortTable", {}).keys())

    def get_system_names(self) -> set[str]:
        """Get the set of valid system names from dependencies.

        Returns:
            Set of system name strings.
        """
        deps = self.load_dependencies()
        return set(deps.get("systems", {}).keys())

    def get_hub_systems(self) -> list[str]:
        """Get the list of hub system names.

        Returns:
            List of hub system names.
        """
        deps = self.load_dependencies()
        return deps.get("hubSystems", [])

    def invalidate_cache(self) -> None:
        """Force reload on next access. Call after admin edits config files."""
        self._catalog_cache = None
        self._catalog_cache_time = 0
        self._deps_cache = None
        self._deps_cache_time = 0
        self._blueprint_cache = None
        self._blueprint_cache_time = 0
        logger.info("Catalog loader cache invalidated.")

    def _validate_catalog(self, catalog: dict[str, Any]) -> None:
        """Validate catalog structure. Raises ValueError on issues.

        Checks:
        - Required top-level keys present
        - Effort values within valid ranges (0.1 - 20.0)
        - Multipliers within valid ranges (0.5 - 3.0)
        - Each effort entry has simple ≤ medium ≤ complex
        """
        required_keys = [
            "effortTable",
            "systemMultipliers",
            "overheadFactors",
            "integrationPatternCosts",
            "hubSurcharges",
        ]
        for key in required_keys:
            if key not in catalog:
                raise ValueError(f"Missing required catalog key: {key}")

        # Validate effort table entries
        for unit_id, data in catalog["effortTable"].items():
            for tier in ("simple", "medium", "complex"):
                if tier not in data:
                    raise ValueError(f"{unit_id} missing '{tier}' effort value")
                val = data[tier]
                if not isinstance(val, (int, float)) or val < 0.1 or val > 20.0:
                    raise ValueError(
                        f"{unit_id}.{tier} = {val} out of valid range [0.1, 20.0]"
                    )
            if data["simple"] > data["medium"]:
                raise ValueError(f"{unit_id}: simple ({data['simple']}) > medium ({data['medium']})")
            if data["medium"] > data["complex"]:
                raise ValueError(f"{unit_id}: medium ({data['medium']}) > complex ({data['complex']})")

        # Validate system multipliers
        for system, mult in catalog["systemMultipliers"].items():
            if not isinstance(mult, (int, float)) or mult < 0.5 or mult > 3.0:
                raise ValueError(
                    f"System multiplier for '{system}' = {mult} out of range [0.5, 3.0]"
                )


# Module-level singleton for convenience
_loader_instance: Optional[CatalogLoader] = None


def get_catalog_loader() -> CatalogLoader:
    """Get or create the module-level CatalogLoader singleton."""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = CatalogLoader()
    return _loader_instance
