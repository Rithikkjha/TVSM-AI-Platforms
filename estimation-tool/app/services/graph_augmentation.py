"""Graph Augmentation Layer — post-SLM classification enhancement using system dependency graph.

This module runs AFTER the SLM classifier produces its initial classification.
It uses the deterministic system dependency graph (config/system_dependencies.json)
to correct and enrich the classification:

1. Cross-domain detection — auto-detect from graph topology (not SLM guess)
2. Missing integration work items — auto-add based on known integration links
3. Dependent system flagging — flag systems the SLM missed but graph says are always involved
4. Cross-domain overhead — apply deterministically from graph data
5. Better scope detection for new apps — based on graph connectivity

Design principle: The graph NEVER removes SLM output — it only ADDS what's missing.
This ensures the SLM's domain understanding is preserved while graph data fills gaps.

Requirements: Graph-augmented classification spec.
"""

import logging
from typing import Any

from app.models.schemas import (
    CatalogClassificationResult,
    CatalogOverheadFlags,
    CatalogWorkItem,
)

logger = logging.getLogger(__name__)

# Integration pattern to catalog unit mapping
PATTERN_TO_UNIT = {
    "REST_API": "INT-01",
    "REST_API_IDP": "INT-03",  # Goes through IDP → needs IDP publisher
    "SERVICE_BUS": "INT-05",
    "SERVICE_BUS_BATCH": "INT-05",
    "IDP": "INT-03",
    "IDP_DIRECT_API": "INT-03",
    "SSO_JWT": "INT-12",
    "WEBHOOK": "INT-09",
    "GRAPHQL_WEBSOCKET": "INT-18",
    "DATA_FEED": "INT-11",
    "SHARED_DB_API": "INT-01",
    "SHARED_APP": "INT-01",
    "BLE": "INT-16",
    "BLE_CLOUD": "INT-16",
    "MQTT": "INT-16",
    "TIMER_BATCH": "BE-04",
    "WIDGET_EMBED": "INT-01",
    "REST_API_BATCH": "INT-01",
}

# Minimum systems that MUST be involved when certain systems are touched
# Based on TVS architecture invariants
ALWAYS_INVOLVED_RULES = {
    # If you touch DMS, IDP is always involved for message brokering
    "DMS": ["IDP", "UMS"],
    # If you touch Booking Service, CPG (payments) and CNS (notifications) are always involved
    "Booking Service": ["CPG", "CNS", "MDP"],
    # If you touch tvsmotor.com, Catalog Service and Lead Service are usually involved
    "tvsmotor.com": ["Catalog Service", "Lead Service"],
    # If you touch TVS Connect, UMS and P360 are always involved
    "TVS Connect": ["UMS", "P360", "CNS"],
    # If you touch CPS, UMS and MDP are always involved
    "CPS": ["UMS", "MDP", "IDP"],
    # If you touch DigiApp, DMS and UMS are always involved
    "DigiApp": ["DMS", "UMS"],
    # If you touch POMS, IDP and SAP are always involved
    "POMS": ["IDP"],
    # If you touch Subscription Platform, P360 and Vehicle Systems are involved
    "Subscription Platform": ["P360", "Vehicle Systems"],
    # If you touch EMS, Lead Service is involved
    "EMS": ["Lead Service"],
}


class GraphAugmentationResult:
    """Result of graph augmentation applied to a classification."""

    def __init__(self):
        self.added_systems: list[str] = []
        self.added_work_items: list[CatalogWorkItem] = []
        self.added_integration_patterns: list[str] = []
        self.cross_domain_detected: bool = False
        self.cross_domain_systems: list[str] = []
        self.cross_domain_overhead_factor: float = 0.0
        self.warnings: list[str] = []
        self.assumptions_added: list[str] = []


class GraphAugmenter:
    """Post-SLM graph augmentation layer.

    Uses the system dependency graph to deterministically correct
    and enrich the SLM's classification output.
    """

    def __init__(self, dependencies: dict[str, Any], catalog: dict[str, Any]):
        """Initialize with loaded dependency graph and catalog.

        Args:
            dependencies: Parsed system_dependencies.json
            catalog: Parsed estimation_catalog.json (for effort table lookups)
        """
        self.systems = dependencies.get("systems", {})
        self.hub_systems = set(dependencies.get("hubSystems", []))
        self.integration_links = dependencies.get("integrationLinks", [])
        self.cross_domain_overhead = dependencies.get("crossDomainOverhead", {})
        self.critical_path_chains = dependencies.get("criticalPathChains", [])
        self.effort_table = catalog.get("effortTable", {})

        # Build adjacency index for fast lookups
        self._adjacency: dict[str, list[dict[str, Any]]] = {}
        for link in self.integration_links:
            src = link.get("source", "")
            tgt = link.get("target", "")
            if src not in self._adjacency:
                self._adjacency[src] = []
            self._adjacency[src].append(link)
            # Also index reverse direction for neighbor lookups
            if tgt not in self._adjacency:
                self._adjacency[tgt] = []
            self._adjacency[tgt].append(link)

    def augment(
        self, classification: CatalogClassificationResult
    ) -> tuple[CatalogClassificationResult, GraphAugmentationResult]:
        """Apply graph augmentation to an SLM classification result.

        Steps:
        1. Detect missing dependent systems from graph topology
        2. Auto-detect cross-domain from system domains (not SLM guess)
        3. Add missing integration work items for known links
        4. Calculate cross-domain overhead from graph data
        5. Enrich assumptions and warnings

        Args:
            classification: The SLM's raw classification output.

        Returns:
            Tuple of (augmented_classification, augmentation_details).
        """
        result = GraphAugmentationResult()

        # Work with mutable copies
        target_systems = list(classification.targetSystems)
        work_items = list(classification.workItems)
        integration_patterns = list(classification.integrationPatterns)
        assumptions = list(classification.assumptions)
        risks = list(classification.risks)

        # Step 1: Detect and add missing dependent systems
        target_systems, result = self._add_missing_systems(
            target_systems, result
        )

        # Step 2: Auto-detect cross-domain from graph topology
        cross_domain, cross_domain_systems = self._detect_cross_domain(target_systems)
        result.cross_domain_detected = cross_domain
        result.cross_domain_systems = cross_domain_systems

        # Step 3: Add missing integration work items
        work_items, result = self._add_missing_integration_items(
            target_systems, work_items, result
        )

        # Step 4: Calculate cross-domain overhead
        if cross_domain:
            overhead_factor = self._calculate_cross_domain_overhead(target_systems)
            result.cross_domain_overhead_factor = overhead_factor

        # Step 5: Enrich assumptions
        if result.added_systems:
            assumptions.append(
                f"Graph analysis: added {', '.join(result.added_systems)} as "
                f"dependent systems based on known integration topology."
            )
        if cross_domain and not classification.overheadFlags.crossDomain:
            assumptions.append(
                f"Cross-domain scope detected from graph: "
                f"{', '.join(cross_domain_systems)} span CP↔D2C boundary."
            )
        augmented_flags = CatalogOverheadFlags(
            teamSize=classification.overheadFlags.teamSize,
            crossDomain=cross_domain,  # Override with graph-detected value
            crossDomainSystems=cross_domain_systems,
            techFamiliarityRisk=classification.overheadFlags.techFamiliarityRisk,
            dataVolumeEstimate=classification.overheadFlags.dataVolumeEstimate,
            multiRegion=classification.overheadFlags.multiRegion,
            regionCount=classification.overheadFlags.regionCount,
            securityCritical=classification.overheadFlags.securityCritical,
            legacyTechDebt=classification.overheadFlags.legacyTechDebt,
        )

        # Build augmented classification
        augmented = CatalogClassificationResult(
            requirementTitle=classification.requirementTitle,
            targetSystems=target_systems,
            scopeType=classification.scopeType,
            workItems=work_items,
            integrationPatterns=integration_patterns + result.added_integration_patterns,
            overheadFlags=augmented_flags,
            assumptions=assumptions + result.assumptions_added,
            risks=risks,
        )

        logger.info(
            f"Graph augmentation: +{len(result.added_systems)} systems, "
            f"+{len(result.added_work_items)} work items, "
            f"cross_domain={cross_domain}"
        )

        return augmented, result

    def _add_missing_systems(
        self,
        target_systems: list[str],
        result: GraphAugmentationResult,
    ) -> tuple[list[str], GraphAugmentationResult]:
        """Detect systems that should be involved based on graph topology.

        Uses two strategies:
        1. ALWAYS_INVOLVED_RULES — hard-coded architectural invariants (only for multi-system or feature+ scope)
        2. Hub system detection — if touching >2 systems, hub systems in the path are needed

        Never removes systems the SLM identified.
        Skips rules for simple Enhancement/Bug Fix with single-system scope.
        """
        current_set = set(target_systems)
        additions = set()

        # Skip aggressive augmentation for single-system simple changes
        is_simple_scope = len(current_set) == 1

        # Strategy 1: Apply always-involved rules (skip for single-system simple scope)
        if not is_simple_scope:
            for system in list(current_set):
                required = ALWAYS_INVOLVED_RULES.get(system, [])
                for dep in required:
                    if dep not in current_set and dep in self.systems:
                        additions.add(dep)
                        result.warnings.append(
                            f"Graph: '{system}' always involves '{dep}' — auto-added."
                        )

        # Strategy 2: Hub system detection
        # If we have 3+ systems and they communicate through a hub, add the hub
        if len(current_set) >= 3:
            for hub in self.hub_systems:
                if hub in current_set:
                    continue  # Already there
                # Check if hub connects to ≥2 of our target systems
                hub_neighbors = self._get_neighbors(hub)
                overlap = hub_neighbors & current_set
                if len(overlap) >= 2:
                    additions.add(hub)
                    result.warnings.append(
                        f"Graph: Hub '{hub}' connects to {len(overlap)} of your "
                        f"target systems ({', '.join(sorted(overlap))}) — auto-added."
                    )

        # Strategy 3: Critical path chain detection
        # If 3+ systems in a chain are present, add the intermediate ones
        for chain in self.critical_path_chains:
            chain_systems = chain.get("systems", [])
            present = [s for s in chain_systems if s in current_set]
            if len(present) >= 3:
                # Add intermediate systems in the chain
                first_idx = chain_systems.index(present[0])
                last_idx = chain_systems.index(present[-1])
                for s in chain_systems[first_idx:last_idx + 1]:
                    if s not in current_set and s in self.systems:
                        additions.add(s)
                        result.warnings.append(
                            f"Graph: '{s}' is on critical path '{chain['name']}' "
                            f"between your systems — auto-added."
                        )

        result.added_systems = sorted(additions)
        return target_systems + sorted(additions), result

    def _detect_cross_domain(
        self, target_systems: list[str]
    ) -> tuple[bool, list[str]]:
        """Deterministically detect cross-domain scope from system domain tags.

        Cross-domain = systems from BOTH CP and D2C domains are involved.
        Uses the graph's domain field, not the SLM's guess.

        Returns:
            (is_cross_domain, list_of_cross_domain_systems)
        """
        cp_systems = []
        d2c_systems = []

        for sys_name in target_systems:
            sys_info = self.systems.get(sys_name, {})
            domain = sys_info.get("domain", "")
            if domain == "CP":
                cp_systems.append(sys_name)
            elif domain == "D2C":
                d2c_systems.append(sys_name)

        is_cross_domain = len(cp_systems) > 0 and len(d2c_systems) > 0

        # Return the systems that create the cross-domain boundary
        cross_systems = []
        if is_cross_domain:
            # Find the actual cross-domain links between our systems
            for link in self.integration_links:
                src = link.get("source", "")
                tgt = link.get("target", "")
                link_domain = link.get("domain", "")
                if (
                    "to" in link_domain
                    and src in target_systems
                    and tgt in target_systems
                ):
                    if src not in cross_systems:
                        cross_systems.append(src)
                    if tgt not in cross_systems:
                        cross_systems.append(tgt)

            # If no specific links found, just list all systems
            if not cross_systems:
                cross_systems = cp_systems[:2] + d2c_systems[:2]

        return is_cross_domain, cross_systems

    def _add_missing_integration_items(
        self,
        target_systems: list[str],
        work_items: list[CatalogWorkItem],
        result: GraphAugmentationResult,
    ) -> tuple[list[CatalogWorkItem], GraphAugmentationResult]:
        """Add integration work items for known links between target systems.

        For each known integration link between target systems:
        - Check if a matching INT-* work item already exists
        - If not, add one with medium complexity and quantity=1

        Only adds items for links where BOTH source and target are in our scope.
        """
        target_set = set(target_systems)

        # Collect existing integration items (by system pair)
        existing_pairs: set[tuple[str, str]] = set()
        for item in work_items:
            if item.unitId.startswith("INT-") or item.unitId in ("BE-17", "BE-04"):
                # Track that this system has integration coverage
                existing_pairs.add((item.system, item.unitId))

        # Find links between our target systems that lack work items
        added_items: list[CatalogWorkItem] = []

        for link in self.integration_links:
            src = link.get("source", "")
            tgt = link.get("target", "")
            pattern = link.get("pattern", "")
            criticality = link.get("criticality", "medium")

            # Only process links where both ends are in scope
            if src not in target_set or tgt not in target_set:
                continue

            # Skip SAP links (SAP is external, handled differently)
            if src == "SAP" or tgt == "SAP":
                continue

            # Map pattern to catalog unit
            unit_id = PATTERN_TO_UNIT.get(pattern, "INT-01")

            # Check if we already have an integration item for this pair
            has_coverage = (
                (src, unit_id) in existing_pairs
                or (tgt, unit_id) in existing_pairs
            )
            if has_coverage:
                continue

            # Determine complexity from criticality
            complexity_map = {
                "critical": "complex",
                "high": "medium",
                "medium": "simple",
                "low": "simple",
            }
            complexity = complexity_map.get(criticality, "medium")

            # Create the work item
            new_item = CatalogWorkItem(
                unitId=unit_id,
                complexity=complexity,
                quantity=1,
                system=src,
                reason=f"Graph: {src} → {tgt} ({pattern}, {criticality})",
                calculatedEffort=None,  # Will be calculated by CatalogCalculator
            )
            added_items.append(new_item)
            existing_pairs.add((src, unit_id))  # Prevent duplicates

            result.added_integration_patterns.append(pattern)
            # Note: These are NOT added to assumptions_added because they're deterministic
            # facts from the graph (not uncertain assumptions). They show in the UI
            # via graphAugmentation.warnings instead.

        # Limit to avoid explosion — cap at 8 auto-added integration items
        if len(added_items) > 8:
            # Keep the most critical ones (complex first)
            added_items.sort(
                key=lambda x: {"complex": 0, "medium": 1, "simple": 2}.get(x.complexity, 1)
            )
            added_items = added_items[:8]
            result.warnings.append(
                f"Graph augmentation capped at 8 integration items "
                f"(total links found: {len(added_items) + len(added_items)}). "
                f"Review for completeness."
            )

        result.added_work_items = added_items
        return work_items + added_items, result

    def _calculate_cross_domain_overhead(self, target_systems: list[str]) -> float:
        """Calculate the total cross-domain overhead factor from graph data.

        Uses crossDomainOverhead table in system_dependencies.json:
        - D2C_to_CP: 0.2 (20% overhead per cross-domain link)
        - any_to_SAP: 0.3
        - any_to_MDP: 0.25
        - any_to_UMS: 0.15
        - any_to_IDP: 0.2
        - any_to_thirdParty: 0.25

        Sums unique applicable overheads (each type counted once, not per-link).
        Caps at 0.6 to prevent runaway.
        """
        target_set = set(target_systems)
        applicable_overheads: dict[str, float] = {}

        # Check D2C_to_CP or CP_to_D2C
        cp_present = any(
            self.systems.get(s, {}).get("domain") == "CP" for s in target_set
        )
        d2c_present = any(
            self.systems.get(s, {}).get("domain") == "D2C" for s in target_set
        )
        if cp_present and d2c_present:
            applicable_overheads["D2C_to_CP"] = self.cross_domain_overhead.get(
                "D2C_to_CP", 0.2
            )

        # Check specific hub/external overheads
        if "MDP" in target_set:
            applicable_overheads["any_to_MDP"] = self.cross_domain_overhead.get(
                "any_to_MDP", 0.25
            )
        if "UMS" in target_set:
            applicable_overheads["any_to_UMS"] = self.cross_domain_overhead.get(
                "any_to_UMS", 0.15
            )
        if "IDP" in target_set:
            applicable_overheads["any_to_IDP"] = self.cross_domain_overhead.get(
                "any_to_IDP", 0.2
            )
        if "CNS" in target_set:
            applicable_overheads["any_to_notification"] = self.cross_domain_overhead.get(
                "any_to_notification", 0.1
            )

        # Check SAP involvement (from integration links)
        has_sap_link = any(
            link.get("target") == "SAP" or link.get("source") == "SAP"
            for link in self.integration_links
            if link.get("source") in target_set or link.get("target") in target_set
        )
        if has_sap_link:
            applicable_overheads["any_to_SAP"] = self.cross_domain_overhead.get(
                "any_to_SAP", 0.3
            )

        total = sum(applicable_overheads.values())
        # Cap at 0.6 to prevent runaway
        capped = min(total, 0.6)

        if applicable_overheads:
            logger.info(
                f"Cross-domain overhead: {applicable_overheads} → "
                f"total={total:.2f}, capped={capped:.2f}"
            )

        return capped

    def _get_neighbors(self, system: str) -> set[str]:
        """Get all systems that have a direct integration link with the given system."""
        neighbors = set()
        for link in self._adjacency.get(system, []):
            src = link.get("source", "")
            tgt = link.get("target", "")
            if src == system:
                neighbors.add(tgt)
            else:
                neighbors.add(src)
        return neighbors
