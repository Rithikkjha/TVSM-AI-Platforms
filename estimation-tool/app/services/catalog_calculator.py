"""Catalog Calculator — deterministic effort calculation from classification.

This module performs ALL math for the catalog-based estimation engine.
It takes a ClassificationResult (from the SLM classifier) and produces
a CalculationResult using only data from the estimation catalog JSON.

Key property: same input → same output ALWAYS (no randomness, no SLM, no async).

Requirements: 3.1–3.8 from catalog-based-estimation spec.
"""

import logging
from typing import Any

from app.models.schemas import (
    CatalogBreakdown,
    CatalogCalculationResult,
    CatalogClassificationResult,
    CatalogOverheadFlags,
    CatalogWorkItem,
    DisciplineEffort,
)

logger = logging.getLogger(__name__)


class CatalogCalculator:
    """Deterministic effort calculation from SLM classification + catalog data.

    All methods are synchronous. No external calls.
    Given identical inputs, always produces identical outputs.
    """

    def __init__(self, catalog: dict[str, Any], dependencies: dict[str, Any]):
        """Initialize with loaded catalog and dependency data.

        Args:
            catalog: Parsed estimation_catalog.json
            dependencies: Parsed system_dependencies.json
        """
        self.catalog = catalog
        self.dependencies = dependencies
        self.effort_table = catalog.get("effortTable", {})
        self.system_multipliers = catalog.get("systemMultipliers", {})
        self.overhead_factors = catalog.get("overheadFactors", {})
        self.pattern_costs = catalog.get("integrationPatternCosts", {})
        self.hub_surcharges = catalog.get("hubSurcharges", {})
        self.ai_config = catalog.get("aiProductivity", {"globalMultiplier": 1.0, "perCategory": {}})
        self.doc_overhead = catalog.get("documentationOverhead", 0.05)
        self.sanity_config = catalog.get("sanityChecks", {"minEffort": {}, "maxEffort": {}})
        self.discipline_mapping = catalog.get("disciplineMapping", {})
        self.scope_factors = catalog.get("scopeFactors", {})
        self.hub_systems = dependencies.get("hubSystems", [])

    def calculate(self, classification: CatalogClassificationResult) -> CatalogCalculationResult:
        """Run the full calculation pipeline.

        Steps:
        1. Calculate base effort (unit efforts × quantities × system multipliers)
        2. Add integration pattern surcharges
        3. Add hub system surcharges
        4. Compound overhead multipliers
        4.5. Apply scope factor (with auto-detection for new apps)
        5. Add documentation overhead (+5%)
        6. Apply AI productivity multiplier
        7. Calculate confidence band
        8. Run sanity checks

        Args:
            classification: SLM classification output.

        Returns:
            Complete calculation result with point estimate, range, and breakdown.
        """
        # Step 0: Auto-detect "New Application" if most systems are unknown
        effective_scope = self._detect_effective_scope(classification)

        # Step 1: Base effort
        work_items_with_effort = self._calculate_base_effort(classification.workItems)
        base_effort = sum(item.calculatedEffort or 0 for item in work_items_with_effort)

        # Step 2: Pattern surcharges
        pattern_surcharge = self._calculate_pattern_surcharges(classification.integrationPatterns)

        # Step 3: Hub surcharges
        hub_surcharge = self._calculate_hub_surcharges(classification.targetSystems)

        # Step 4: Overhead multiplier
        overhead_mult = self._calculate_overhead_multiplier(classification.overheadFlags)

        # Step 4.5: Scope factor (New Application = ×2.5, New Module = ×1.8, etc.)
        scope_factor = self.scope_factors.get(effective_scope, 1.0)

        # Step 5: Subtotal with documentation overhead
        subtotal = (base_effort + pattern_surcharge + hub_surcharge) * overhead_mult * scope_factor
        subtotal_with_docs = subtotal * (1 + self.doc_overhead)

        # Step 6: AI productivity multiplier
        ai_mult = self._get_ai_multiplier(work_items_with_effort)
        final_effort = subtotal_with_docs * ai_mult

        # Ensure minimum of 0.5 person-days
        final_effort = max(final_effort, 0.5)

        # Step 7: Confidence band
        confidence_level, range_low, range_high = self._calculate_confidence_band(
            final_effort, classification.assumptions, classification.risks
        )

        # Step 8: Sanity checks
        sanity_warnings = self._run_sanity_checks(
            final_effort, classification.scopeType, classification
        )

        # Map to disciplines
        discipline_breakdown = self._map_to_disciplines(work_items_with_effort)

        # Step 9: Distribution validation + auto-correction
        distribution_warnings = self._check_distribution(
            final_effort, classification.scopeType, discipline_breakdown
        )
        sanity_warnings.extend(distribution_warnings)

        # Recalculate total after distribution corrections
        adjusted_total = sum(d.personDays for d in discipline_breakdown)
        if adjusted_total > final_effort:
            final_effort = adjusted_total
            # Recalculate range based on adjusted total
            confidence_level, range_low, range_high = self._calculate_confidence_band(
                final_effort, classification.assumptions, classification.risks
            )
        discipline_breakdown = self._map_to_disciplines(work_items_with_effort)

        return CatalogCalculationResult(
            pointEstimate=round(final_effort, 1),
            confidenceLevel=confidence_level,
            rangeLow=round(range_low, 1),
            rangeHigh=round(range_high, 1),
            baseEffort=round(base_effort, 1),
            patternSurcharge=round(pattern_surcharge, 1),
            hubSurcharge=round(hub_surcharge, 1),
            overheadMultiplier=round(overhead_mult, 3),
            aiMultiplier=round(ai_mult, 2),
            workItems=work_items_with_effort,
            disciplineBreakdown=discipline_breakdown,
            sanityWarnings=sanity_warnings,
            assumptions=classification.assumptions,
            risks=classification.risks,
        )

    def build_catalog_breakdown(self, result: CatalogCalculationResult, flags: CatalogOverheadFlags) -> CatalogBreakdown:
        """Build the UI-friendly breakdown from a calculation result.

        Args:
            result: The calculation result.
            flags: Overhead flags used.

        Returns:
            CatalogBreakdown for embedding in EstimationResult.
        """
        # Build overhead detail
        overhead_detail = {}
        overhead_detail["teamSize"] = self._get_team_size_multiplier(flags.teamSize)
        if flags.crossDomain:
            overhead_detail["crossDomain"] = self.overhead_factors.get("crossDomain", 1.2)
        overhead_detail["techFamiliarity"] = self.overhead_factors.get("techFamiliarity", {}).get(
            flags.techFamiliarityRisk, 1.0
        )
        overhead_detail["dataVolume"] = self.overhead_factors.get("dataVolume", {}).get(
            flags.dataVolumeEstimate, 1.0
        )
        if flags.securityCritical:
            overhead_detail["security"] = self.overhead_factors.get("security", {}).get("payment", 1.2)
        if flags.legacyTechDebt:
            overhead_detail["legacyDebt"] = self.overhead_factors.get("legacyDebt", {}).get("heavy", 1.3)

        # Hub surcharges detail
        hub_detail = {}
        for system in [s for s in (result.assumptions if hasattr(result, '_target_systems') else [])]:
            pass  # Will be populated from targetSystems
        # Re-calculate from work items
        seen_hubs = set()
        for item in result.workItems:
            if item.system in self.hub_surcharges and item.system not in seen_hubs:
                hub_detail[item.system] = self.hub_surcharges[item.system]
                seen_hubs.add(item.system)

        return CatalogBreakdown(
            workItems=result.workItems,
            overheadDetail=overhead_detail,
            integrationPatterns=[],  # Filled by caller
            hubSurcharges=hub_detail,
            aiMultiplierApplied=result.aiMultiplier,
            sanityWarnings=result.sanityWarnings,
            confidenceLevel=result.confidenceLevel,
            rangeLow=result.rangeLow,
            rangeHigh=result.rangeHigh,
        )

    def _detect_effective_scope(self, classification: CatalogClassificationResult) -> str:
        """Auto-detect if this is a New Application based on registry coverage.

        Rule: If the PRD's target systems are mostly NOT in our dependency graph,
        it means we're building something new — not enhancing existing systems.

        - >50% unknown systems → "New Application" (×2.5)
        - >30% unknown systems → "New Module" (×1.8)
        - Otherwise → use LLM's scopeType as-is

        Also checks: if LLM already said "New Application", respect that.
        """
        # If LLM already classified as New Application or New Module, trust it
        if classification.scopeType in ("New Application", "New Module"):
            logger.info(f"Scope: LLM classified as '{classification.scopeType}' — using directly")
            return classification.scopeType

        # Check how many target systems are unknown (not in our registry)
        known_systems = set(self.system_multipliers.keys())
        target_systems = set(classification.targetSystems)

        if not target_systems:
            return classification.scopeType

        unknown_systems = target_systems - known_systems
        unknown_ratio = len(unknown_systems) / len(target_systems)

        # Also check work items — if systems in work items are mostly unknown
        work_item_systems = set(item.system for item in classification.workItems)
        unknown_work_systems = work_item_systems - known_systems
        work_unknown_ratio = len(unknown_work_systems) / max(len(work_item_systems), 1)

        # Use the higher ratio
        effective_ratio = max(unknown_ratio, work_unknown_ratio)

        if effective_ratio > 0.5:
            logger.info(
                f"Scope auto-upgrade: {effective_ratio:.0%} of systems unknown "
                f"({unknown_systems | unknown_work_systems}). "
                f"Upgrading '{classification.scopeType}' → 'New Application' (×{self.scope_factors.get('New Application', 2.5)})"
            )
            return "New Application"
        elif effective_ratio > 0.3:
            logger.info(
                f"Scope auto-upgrade: {effective_ratio:.0%} of systems unknown. "
                f"Upgrading '{classification.scopeType}' → 'New Module' (×{self.scope_factors.get('New Module', 1.8)})"
            )
            return "New Module"
        else:
            logger.info(f"Scope: '{classification.scopeType}' — {effective_ratio:.0%} unknown systems, no upgrade needed")
            return classification.scopeType

    def _calculate_base_effort(self, work_items: list[CatalogWorkItem]) -> list[CatalogWorkItem]:
        """Calculate effort per work item: effort[unitId][complexity] × quantity × systemMultiplier.

        Returns work items with calculatedEffort filled.
        Unknown unitIds get 0 effort (logged as warning).
        Unknown systems get default multiplier of 1.2.
        """
        result_items = []

        for item in work_items:
            unit_data = self.effort_table.get(item.unitId)
            if not unit_data:
                logger.warning(f"Unknown unitId '{item.unitId}' — skipping (0 effort)")
                result_items.append(item.model_copy(update={"calculatedEffort": 0}))
                continue

            # Get base effort for complexity tier
            base_effort = unit_data.get(item.complexity, unit_data.get("medium", 2.0))

            # Get system multiplier (default 1.2 for unknown systems)
            sys_mult = self.system_multipliers.get(item.system, 1.2)

            # Calculate: base × quantity × system multiplier
            calculated = base_effort * item.quantity * sys_mult

            result_items.append(item.model_copy(update={"calculatedEffort": round(calculated, 2)}))

        return result_items

    def _calculate_pattern_surcharges(self, patterns: list[str]) -> float:
        """Sum integration pattern cost surcharges.

        Each unique pattern adds its cost once.
        Unknown patterns add 0 (logged).
        """
        total = 0.0
        for pattern in patterns:
            cost = self.pattern_costs.get(pattern)
            if cost is None:
                logger.warning(f"Unknown integration pattern '{pattern}' — 0 surcharge")
                continue
            total += cost
        return total

    def _calculate_hub_surcharges(self, target_systems: list[str]) -> float:
        """Sum hub surcharges for hub systems in targetSystems list.

        Each hub system adds a flat person-day surcharge.
        """
        total = 0.0
        for system in target_systems:
            if system in self.hub_surcharges:
                total += self.hub_surcharges[system]
        return total

    def _calculate_overhead_multiplier(self, flags: CatalogOverheadFlags) -> float:
        """Compound all overhead factors into a single multiplier.

        Compounds: teamSize × crossDomain × techFamiliarity × dataVolume
                   × deployment × security × legacy
        """
        mult = 1.0

        # Team size
        mult *= self._get_team_size_multiplier(flags.teamSize)

        # Cross-domain
        if flags.crossDomain:
            mult *= self.overhead_factors.get("crossDomain", 1.2)

        # Tech familiarity
        tech_mult = self.overhead_factors.get("techFamiliarity", {}).get(
            flags.techFamiliarityRisk, 1.0
        )
        mult *= tech_mult

        # Data volume
        volume_mult = self.overhead_factors.get("dataVolume", {}).get(
            flags.dataVolumeEstimate, 1.0
        )
        mult *= volume_mult

        # Deployment topology
        if flags.multiRegion and flags.regionCount > 0:
            deploy_table = self.overhead_factors.get("deploymentTopology", {})
            if flags.regionCount <= 3:
                mult *= deploy_table.get("multi_region_2_3", 1.2)
            elif flags.regionCount <= 10:
                mult *= deploy_table.get("multi_country_4_10", 1.35)
            else:
                mult *= deploy_table.get("multi_country_10+", 1.5)

        # Security
        if flags.securityCritical:
            security_table = self.overhead_factors.get("security", {})
            mult *= security_table.get("payment", 1.2)

        # Legacy tech debt
        if flags.legacyTechDebt:
            legacy_table = self.overhead_factors.get("legacyDebt", {})
            mult *= legacy_table.get("heavy", 1.3)

        return mult

    def _get_team_size_multiplier(self, team_size: int) -> float:
        """Map team size to multiplier from overhead factors."""
        team_table = self.overhead_factors.get("teamSize", {})
        if team_size <= 2:
            return team_table.get("1-2", 1.0)
        elif team_size <= 5:
            return team_table.get("3-5", 1.1)
        elif team_size <= 10:
            return team_table.get("6-10", 1.2)
        else:
            return team_table.get("11+", 1.35)

    def _get_ai_multiplier(self, work_items: list[CatalogWorkItem]) -> float:
        """Get the AI productivity multiplier.

        Uses global multiplier by default. If per-category multipliers are set,
        computes a weighted average based on work item effort distribution.
        """
        global_mult = self.ai_config.get("globalMultiplier", 1.0)
        per_category = self.ai_config.get("perCategory", {})

        # Check if any per-category overrides are set
        has_overrides = any(v is not None for v in per_category.values())
        if not has_overrides:
            return global_mult

        # Weighted average by effort
        total_effort = 0.0
        weighted_sum = 0.0

        for item in work_items:
            effort = item.calculatedEffort or 0
            if effort <= 0:
                continue

            unit_data = self.effort_table.get(item.unitId, {})
            category = unit_data.get("category", "backendLogic")
            cat_mult = per_category.get(category)

            if cat_mult is not None:
                weighted_sum += effort * cat_mult
            else:
                weighted_sum += effort * global_mult

            total_effort += effort

        if total_effort <= 0:
            return global_mult

        return weighted_sum / total_effort

    def _calculate_confidence_band(
        self, effort: float, assumptions: list[str], risks: list[str]
    ) -> tuple[str, float, float]:
        """Determine confidence level and calculate range.

        HIGH (±10%): ≤2 assumptions AND ≤1 risk
        MEDIUM (±25%): ≤4 assumptions AND ≤3 risks
        LOW (±40%): everything else

        Returns: (level, range_low, range_high)
        """
        n_assumptions = len(assumptions)
        n_risks = len(risks)

        if n_assumptions <= 2 and n_risks <= 1:
            level = "HIGH"
            return level, effort * 0.9, effort * 1.1
        elif n_assumptions <= 4 and n_risks <= 3:
            level = "MEDIUM"
            return level, effort * 0.75, effort * 1.25
        else:
            level = "LOW"
            return level, effort * 0.6, effort * 1.4

    def _run_sanity_checks(
        self,
        effort: float,
        scope_type: str,
        classification: CatalogClassificationResult,
    ) -> list[str]:
        """Run post-calculation sanity checks. Return warning messages."""
        warnings = []

        # Min/max effort guards
        min_guards = self.sanity_config.get("minEffort", {})
        max_guards = self.sanity_config.get("maxEffort", {})

        min_val = min_guards.get(scope_type)
        if min_val is not None and effort < min_val:
            warnings.append(
                f"Estimate ({effort:.1f} pd) below minimum for '{scope_type}' ({min_val} pd). "
                f"May indicate missing work items."
            )

        max_val = max_guards.get(scope_type)
        if max_val is not None and effort > max_val:
            warnings.append(
                f"Estimate ({effort:.1f} pd) exceeds maximum for '{scope_type}' ({max_val} pd). "
                f"Consider splitting into phases."
            )

        # Consistency checks
        target_systems = set(classification.targetSystems)
        work_unit_ids = {item.unitId for item in classification.workItems}
        work_unit_systems = {item.system for item in classification.workItems}
        has_int_units = any(uid.startswith("INT-") for uid in work_unit_ids)
        has_qa02 = "QA-02" in work_unit_ids
        has_qa06 = "QA-06" in work_unit_ids
        has_be17 = "BE-17" in work_unit_ids

        # Hub system touched but no integration unit
        for hub in self.hub_systems:
            if hub in target_systems and not has_int_units:
                warnings.append(
                    f"Hub system '{hub}' in targetSystems but no INT-* work items. "
                    f"Integration effort likely missing."
                )
                break  # One warning is enough

        # Payment mentioned but no integration test
        payment_units = {"BE-08", "BE-09", "INT-13"}
        if payment_units & work_unit_ids and not has_qa02:
            warnings.append(
                "Payment flow identified but no integration test (QA-02). "
                "Consider adding integration testing."
            )

        # Multi-system but no integration test
        if len(target_systems) >= 3 and not has_qa02:
            warnings.append(
                f"{len(target_systems)} systems involved but no integration test (QA-02). "
                f"Multi-system scope typically needs integration testing."
            )

        # SAP in targets but no BE-17
        sap_related = {"BE-17", "INT-07", "INT-08"}
        if "SAP" in str(target_systems) and not (sap_related & work_unit_ids):
            warnings.append(
                "SAP referenced in targetSystems but no SAP integration unit (BE-17/INT-07/INT-08)."
            )

        # Security critical but no QA-06
        if classification.overheadFlags.securityCritical and not has_qa06:
            warnings.append(
                "Security-critical scope without SAST/DAST scan (QA-06). "
                "Security testing is mandatory for PII/payment flows."
            )

        # Large scope without performance test
        if effort > 50 and "QA-05" not in work_unit_ids:
            warnings.append(
                f"Large scope ({effort:.0f} pd) without performance test (QA-05). "
                f"Consider adding load testing for >50 pd projects."
            )

        return warnings

    def _check_distribution(
        self,
        total_effort: float,
        scope_type: str,
        discipline_breakdown: list[DisciplineEffort],
    ) -> list[str]:
        """Validate discipline distribution and auto-correct if below minimum.

        Modifies discipline_breakdown in-place to add missing effort.
        Returns warnings describing any corrections applied.
        """
        distribution_rules = self.catalog.get("distributionRules", {})
        rules = distribution_rules.get(scope_type)
        if not rules or total_effort < 20:
            return []

        warnings = []
        present = {d.discipline: d for d in discipline_breakdown}
        adjustments: list[str] = []

        for discipline_name, rule in rules.items():
            min_pct = rule.get("min", 0)
            expected_pct = rule.get("expected", min_pct)

            current = present.get(discipline_name)
            current_effort = current.personDays if current else 0
            current_pct = current_effort / total_effort if total_effort > 0 else 0

            if current_pct < min_pct and min_pct > 0:
                target_effort = round(total_effort * expected_pct, 1)
                gap = round(target_effort - current_effort, 1)

                if gap > 0:
                    adjustments.append(
                        f"{discipline_name}: +{gap:.0f}pd ({current_pct:.0%}→{expected_pct:.0%})"
                    )
                    if current:
                        current.personDays = round(current.personDays + gap, 2)
                        current.personMonths = round(current.personDays / 22.0, 2)
                    else:
                        discipline_breakdown.append(DisciplineEffort(
                            discipline=discipline_name,
                            personDays=target_effort,
                            personMonths=round(target_effort / 22.0, 2),
                        ))

        if adjustments:
            total_gap = sum(
                d.personDays for d in discipline_breakdown
            ) - total_effort
            warnings.append(
                f"Distribution auto-correction: +{total_gap:.0f} pd added. "
                f"[{', '.join(adjustments)}]"
            )

        return warnings

    def _map_to_disciplines(self, work_items: list[CatalogWorkItem]) -> list[DisciplineEffort]:
        """Map work item categories to discipline-level breakdown.

        Uses disciplineMapping from catalog for default mapping:
        - frontend, backendCrud, backendLogic, integration, sap → Digital Engineering
        - qa → QA/Testing
        - devops → DevOps

        Also applies systemDisciplineOverrides: work items targeting specific systems
        (e.g., TVS Connect, P360, MDP) get mapped to their specialized discipline
        (e.g., P360 Telematics, Data Engineering) for accurate rate card application.
        Note: QA and DevOps work items always stay in QA/Testing and DevOps respectively,
        regardless of which system they target.
        """
        discipline_totals: dict[str, float] = {}
        system_overrides = self.catalog.get("systemDisciplineOverrides", {})

        # Categories that should NOT be overridden by system (keep their own discipline)
        non_overridable_categories = {"qa", "devops"}

        for item in work_items:
            effort = item.calculatedEffort or 0
            if effort <= 0:
                continue

            # Get category from effort table
            unit_data = self.effort_table.get(item.unitId, {})
            category = unit_data.get("category", "backendLogic")

            # QA and DevOps always map to their own discipline
            if category in non_overridable_categories:
                discipline = self.discipline_mapping.get(category, "Digital Engineering")
            else:
                # Check if this system has a discipline override
                override_discipline = system_overrides.get(item.system)
                if override_discipline:
                    discipline = override_discipline
                else:
                    discipline = self.discipline_mapping.get(category, "Digital Engineering")

            discipline_totals[discipline] = discipline_totals.get(discipline, 0) + effort

        # Convert to DisciplineEffort list
        return [
            DisciplineEffort(
                discipline=name,
                personDays=round(days, 2),
                personMonths=round(days / 22.0, 2),
            )
            for name, days in sorted(discipline_totals.items(), key=lambda x: -x[1])
        ]
