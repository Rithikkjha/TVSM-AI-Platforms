"""Vendor comparator service for the Project Estimation Tool.

Implements vendor proposal analysis and comparison against internal estimations:
- Vendor proposal analysis via SLM
- Quality assessment: compare vendor scope coverage against PRD
- Cost comparison: variance |V-I|/I×100, flag if >25%
- Delivery comparison: vendor timeline vs Calendar_Duration
- Multi-vendor consolidation and ranking

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9
"""

import json
import logging
from typing import Optional

from app.models.schemas import (
    ConsolidatedVendorView,
    EstimationResult,
    SLMOptions,
    VendorComparison,
    VendorCostComparison,
    VendorDeliveryComparison,
    VendorProposalInput,
    VendorQualityAssessment,
)
from app.services.slm_engine import SLMEngine

logger = logging.getLogger(__name__)

# Cost variance threshold for flagging
COST_VARIANCE_THRESHOLD = 25.0  # percent


class VendorComparatorError(Exception):
    """Base exception for vendor comparator errors."""
    pass


async def analyze_proposal(
    proposal: VendorProposalInput,
    internal_estimation: EstimationResult,
    slm_engine: SLMEngine,
) -> VendorComparison:
    """Analyze a vendor proposal and compare against the internal estimation.

    Performs multi-dimensional comparison across quality, cost, and delivery.

    Args:
        proposal: The vendor proposal input with document, cost, and timeline.
        internal_estimation: The internal estimation result to compare against.
        slm_engine: SLM engine for document analysis.

    Returns:
        VendorComparison with quality, cost, and delivery assessments.

    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.8
    """
    # Step 1: Analyze vendor proposal via SLM
    vendor_analysis = await _analyze_vendor_document(
        proposal, internal_estimation, slm_engine
    )

    # Step 2: Quality assessment - scope coverage comparison
    quality_assessment = _assess_quality(vendor_analysis, internal_estimation)

    # Step 3: Cost comparison with variance calculation
    cost_comparison = _compare_cost(
        vendor_cost=proposal.quotedCost,
        internal_cost=internal_estimation.costProjection.total,
    )

    # Step 4: Delivery comparison
    delivery_comparison = _compare_delivery(
        vendor_timeline=proposal.quotedTimeline,
        internal_timeline=internal_estimation.calendarDuration,
        vendor_team_size=proposal.vendorTeamSize,
        internal_team_size=sum(t.count for t in internal_estimation.teamComposition),
    )

    # Step 5: Extract vendor name from analysis or use generic
    vendor_name = vendor_analysis.get("vendorName", f"Vendor ({proposal.document.filename})")

    return VendorComparison(
        vendorName=vendor_name,
        qualityAssessment=quality_assessment,
        costComparison=cost_comparison,
        deliveryComparison=delivery_comparison,
        assumptions=vendor_analysis.get("assumptions", []),
    )


def consolidate_comparisons(
    comparisons: list[VendorComparison],
) -> ConsolidatedVendorView:
    """Consolidate multiple vendor comparisons and produce rankings.

    Ranks vendors by overall proximity to the internal estimate across
    all three comparison dimensions (quality, cost, delivery).

    Args:
        comparisons: List of individual vendor comparisons.

    Returns:
        ConsolidatedVendorView with comparisons and rankings.

    Requirements: 5.6, 5.7
    """
    if not comparisons:
        return ConsolidatedVendorView(comparisons=[], rankings=[])

    # Calculate a composite score for each vendor
    scored_vendors: list[dict] = []

    for comp in comparisons:
        # Quality score: higher scope coverage is better (0-1 scale → 0-100)
        quality_score = comp.qualityAssessment.scopeCoverage * 100

        # Cost score: lower variance is better (invert)
        cost_variance = comp.costComparison.variancePercent
        cost_score = max(0, 100 - cost_variance)

        # Delivery score: closer to internal timeline is better
        if comp.deliveryComparison.internalTimeline > 0:
            timeline_variance = (
                abs(comp.deliveryComparison.vendorTimeline - comp.deliveryComparison.internalTimeline)
                / comp.deliveryComparison.internalTimeline
                * 100
            )
        else:
            timeline_variance = 0
        delivery_score = max(0, 100 - timeline_variance)

        # Composite: weighted average (quality 40%, cost 35%, delivery 25%)
        composite = quality_score * 0.40 + cost_score * 0.35 + delivery_score * 0.25

        scored_vendors.append({
            "vendorName": comp.vendorName,
            "qualityScore": round(quality_score, 1),
            "costScore": round(cost_score, 1),
            "deliveryScore": round(delivery_score, 1),
            "compositeScore": round(composite, 1),
        })

    # Sort by composite score (descending - higher is better)
    scored_vendors.sort(key=lambda v: v["compositeScore"], reverse=True)

    # Assign ranks
    rankings: list[dict] = []
    for rank, vendor in enumerate(scored_vendors, 1):
        vendor["rank"] = rank
        rankings.append(vendor)

    # Update comparisons with ranks
    rank_map = {v["vendorName"]: v["rank"] for v in rankings}
    for comp in comparisons:
        comp.overallRank = rank_map.get(comp.vendorName)

    return ConsolidatedVendorView(
        comparisons=comparisons,
        rankings=rankings,
    )


async def _analyze_vendor_document(
    proposal: VendorProposalInput,
    internal_estimation: EstimationResult,
    slm_engine: SLMEngine,
) -> dict:
    """Analyze a vendor proposal document using the SLM.

    Extracts vendor approach, assumptions, team composition, and scope coverage.

    Args:
        proposal: The vendor proposal with document content.
        internal_estimation: Internal estimation for context.
        slm_engine: SLM engine for inference.

    Returns:
        Parsed analysis dictionary.

    Requirements: 5.1, 5.8
    """
    # Build scope items list from internal estimation
    scope_items = []
    if internal_estimation.scopeCoverage and internal_estimation.scopeCoverage.items:
        scope_items = [item.name for item in internal_estimation.scopeCoverage.items]

    scope_list = "\n".join(f"- {item}" for item in scope_items) if scope_items else "No scope items available"

    prompt = f"""Analyze the following vendor proposal document and extract key information.
Compare the vendor's scope coverage against the internal PRD scope items listed below.

VENDOR PROPOSAL (from {proposal.document.filename}):
{proposal.document.textContent[:4000]}

INTERNAL PRD SCOPE ITEMS:
{scope_list}

Respond in JSON format only:
{{
  "vendorName": "<vendor company name if mentioned>",
  "approach": "<brief summary of vendor's approach/methodology>",
  "assumptions": ["<vendor assumption 1>", "<vendor assumption 2>", ...],
  "teamComposition": "<vendor's stated team composition if any>",
  "scopeItemsAddressed": ["<PRD item addressed by vendor>", ...],
  "scopeGaps": ["<PRD item NOT addressed by vendor>", ...],
  "coverageRatio": <0.0 to 1.0 estimate of PRD coverage>
}}
"""

    try:
        response = await slm_engine.inference(
            prompt,
            options=SLMOptions(temperature=0.2, maxTokens=2048),
        )
        return _parse_vendor_analysis(response.content)
    except Exception as exc:
        logger.warning(f"SLM vendor analysis failed: {exc}. Using basic analysis.")
        return _basic_vendor_analysis(proposal)


def _parse_vendor_analysis(content: str) -> dict:
    """Parse the SLM response for vendor analysis.

    Args:
        content: Raw SLM response text.

    Returns:
        Parsed dictionary with vendor analysis data.
    """
    try:
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()

        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = json_str[start:end]

        data = json.loads(json_str)
        return data
    except (json.JSONDecodeError, IndexError, ValueError) as exc:
        logger.warning(f"Failed to parse vendor analysis: {exc}")
        return {
            "vendorName": "Unknown Vendor",
            "approach": "",
            "assumptions": [],
            "teamComposition": "",
            "scopeItemsAddressed": [],
            "scopeGaps": [],
            "coverageRatio": 0.5,
        }


def _basic_vendor_analysis(proposal: VendorProposalInput) -> dict:
    """Provide a basic vendor analysis when SLM is unavailable.

    Args:
        proposal: The vendor proposal input.

    Returns:
        Basic analysis dictionary.
    """
    return {
        "vendorName": f"Vendor ({proposal.document.filename})",
        "approach": "Analysis unavailable - SLM inference failed.",
        "assumptions": [],
        "teamComposition": "",
        "scopeItemsAddressed": [],
        "scopeGaps": [],
        "coverageRatio": 0.5,
    }


def _assess_quality(
    vendor_analysis: dict,
    internal_estimation: EstimationResult,
) -> VendorQualityAssessment:
    """Assess vendor quality by comparing scope coverage against PRD.

    Args:
        vendor_analysis: Parsed vendor analysis from SLM.
        internal_estimation: Internal estimation for scope reference.

    Returns:
        VendorQualityAssessment with coverage, gaps, and addressed items.

    Requirements: 5.2
    """
    addressed = vendor_analysis.get("scopeItemsAddressed", [])
    gaps = vendor_analysis.get("scopeGaps", [])
    coverage_ratio = vendor_analysis.get("coverageRatio", 0.5)

    # If we have actual scope items from the internal estimation, calculate coverage
    if internal_estimation.scopeCoverage and internal_estimation.scopeCoverage.items:
        total_items = len(internal_estimation.scopeCoverage.items)
        if total_items > 0 and addressed:
            coverage_ratio = len(addressed) / total_items
        elif total_items > 0 and not addressed:
            coverage_ratio = vendor_analysis.get("coverageRatio", 0.5)

    return VendorQualityAssessment(
        scopeCoverage=min(1.0, max(0.0, coverage_ratio)),
        gaps=gaps,
        addressed=addressed,
    )


def _compare_cost(
    vendor_cost: float,
    internal_cost: float,
) -> VendorCostComparison:
    """Compare vendor cost against internal cost projection.

    Calculates variance: |V - I| / I × 100
    Flags if variance > 25%.

    Args:
        vendor_cost: Vendor's quoted cost.
        internal_cost: Internal estimated cost.

    Returns:
        VendorCostComparison with variance and flag.

    Requirements: 5.3, 5.5
    """
    if internal_cost > 0:
        variance_percent = abs(vendor_cost - internal_cost) / internal_cost * 100
    else:
        variance_percent = 0.0

    flagged = variance_percent > COST_VARIANCE_THRESHOLD

    return VendorCostComparison(
        vendorCost=vendor_cost,
        internalCost=internal_cost,
        variancePercent=round(variance_percent, 2),
        flagged=flagged,
    )


def _compare_delivery(
    vendor_timeline: float,
    internal_timeline: float,
    vendor_team_size: Optional[int],
    internal_team_size: int,
) -> VendorDeliveryComparison:
    """Compare vendor delivery timeline against internal calculation.

    Args:
        vendor_timeline: Vendor's quoted timeline in months.
        internal_timeline: Internal Calendar_Duration in months.
        vendor_team_size: Vendor's stated team size (optional).
        internal_team_size: Total internal team size.

    Returns:
        VendorDeliveryComparison with timeline and team comparison.

    Requirements: 5.4
    """
    # Determine if delivery timeline is flagged
    # Flag if vendor timeline differs significantly (>30% shorter or >50% longer)
    flagged = False
    if internal_timeline > 0:
        ratio = vendor_timeline / internal_timeline
        if ratio < 0.7 or ratio > 1.5:
            flagged = True

    # Team size comparison
    if vendor_team_size is not None:
        if vendor_team_size > internal_team_size:
            team_comparison = (
                f"Vendor proposes {vendor_team_size} team members vs "
                f"internal recommendation of {internal_team_size} (larger team)"
            )
        elif vendor_team_size < internal_team_size:
            team_comparison = (
                f"Vendor proposes {vendor_team_size} team members vs "
                f"internal recommendation of {internal_team_size} (smaller team)"
            )
        else:
            team_comparison = (
                f"Vendor proposes {vendor_team_size} team members, "
                f"matching internal recommendation"
            )
    else:
        team_comparison = "Vendor team size not specified"

    return VendorDeliveryComparison(
        vendorTimeline=vendor_timeline,
        internalTimeline=internal_timeline,
        teamSizeComparison=team_comparison,
        flagged=flagged,
    )
