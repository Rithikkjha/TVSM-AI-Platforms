"""Confidence calculator service for the Project Estimation Tool.

Computes a 5-factor composite confidence score with configurable weights:
- Input completeness (0.30): derived from input tier
- Document detail (0.25): from SLM analysis of document quality
- Requirement clarity (0.20): from SLM analysis of requirement precision
- Domain history (0.15): from historical estimation lookup
- Scope coverage (0.10): from scope analysis results

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 15.1-15.9
"""

import logging
import random
from typing import Optional

from app.models.schemas import (
    CompositeConfidenceScore,
    ConfidenceFactor,
    ConfidenceFactors,
    InputTier,
)

logger = logging.getLogger(__name__)

# Factor weights (must sum to 1.0)
WEIGHT_INPUT_COMPLETENESS = 0.30
WEIGHT_DOCUMENT_DETAIL = 0.25
WEIGHT_REQUIREMENT_CLARITY = 0.20
WEIGHT_DOMAIN_HISTORY = 0.15
WEIGHT_SCOPE_COVERAGE = 0.10

# Tier-based input completeness ranges
TIER_RANGES: dict[int, tuple[int, int]] = {
    0: (15, 35),
    1: (30, 60),
    2: (50, 75),
    3: (65, 90),
}


def compute_input_completeness_score(input_tier: InputTier) -> float:
    """Compute the input completeness sub-score based on the input tier.

    Tier 1 → [30, 60], Tier 2 → [50, 75], Tier 3 → [65, 90].
    Returns the midpoint of the tier range as a deterministic baseline.

    Args:
        input_tier: The classified input tier (1, 2, or 3).

    Returns:
        Input completeness score in the appropriate tier range.

    Requirements: 3.2, 3.3, 3.4
    """
    low, high = TIER_RANGES[input_tier]
    # Use the midpoint as the deterministic score for the tier
    return (low + high) / 2.0


def calculate_confidence(factors: ConfidenceFactors) -> CompositeConfidenceScore:
    """Calculate the composite confidence score from 5 input factors.

    Formula: overall = 0.30 × inputCompleteness + 0.25 × documentDetail
             + 0.20 × requirementClarity + 0.15 × domainHistory
             + 0.10 × scopeCoverage

    Each factor sub-score is in [0, 100]. The result is in [0, 100].

    Args:
        factors: ConfidenceFactors containing input tier and four sub-scores.

    Returns:
        CompositeConfidenceScore with overall score, factor breakdown,
        recommendations, and textual explanation.

    Requirements: 3.1, 15.1, 15.9
    """
    # Derive input completeness from tier
    input_completeness_score = compute_input_completeness_score(factors.inputTier)

    # Clamp all scores to [0, 100]
    input_completeness = max(0.0, min(100.0, input_completeness_score))
    document_detail = max(0.0, min(100.0, factors.documentDetailScore))
    requirement_clarity = max(0.0, min(100.0, factors.requirementClarityScore))
    domain_history = max(0.0, min(100.0, factors.domainHistoryScore))
    scope_coverage = max(0.0, min(100.0, factors.scopeCoverageScore))

    # Calculate weighted composite score
    overall = (
        WEIGHT_INPUT_COMPLETENESS * input_completeness
        + WEIGHT_DOCUMENT_DETAIL * document_detail
        + WEIGHT_REQUIREMENT_CLARITY * requirement_clarity
        + WEIGHT_DOMAIN_HISTORY * domain_history
        + WEIGHT_SCOPE_COVERAGE * scope_coverage
    )

    # Clamp overall to [0, 100]
    overall = max(0.0, min(100.0, overall))

    # Build factor breakdown
    factor_details = {
        "inputCompleteness": ConfidenceFactor(
            score=input_completeness, weight=WEIGHT_INPUT_COMPLETENESS
        ),
        "documentDetail": ConfidenceFactor(
            score=document_detail, weight=WEIGHT_DOCUMENT_DETAIL
        ),
        "requirementClarity": ConfidenceFactor(
            score=requirement_clarity, weight=WEIGHT_REQUIREMENT_CLARITY
        ),
        "domainHistory": ConfidenceFactor(
            score=domain_history, weight=WEIGHT_DOMAIN_HISTORY
        ),
        "scopeCoverage": ConfidenceFactor(
            score=scope_coverage, weight=WEIGHT_SCOPE_COVERAGE
        ),
    }

    # Generate recommendations
    recommendations = _generate_recommendations(
        factors.inputTier,
        input_completeness,
        document_detail,
        requirement_clarity,
        domain_history,
        scope_coverage,
    )

    # Generate explanation
    explanation = _generate_explanation(
        overall,
        input_completeness,
        document_detail,
        requirement_clarity,
        domain_history,
        scope_coverage,
    )

    return CompositeConfidenceScore(
        overall=round(overall, 2),
        factors=factor_details,
        recommendations=recommendations,
        explanation=explanation,
    )


def _generate_recommendations(
    input_tier: InputTier,
    input_completeness: float,
    document_detail: float,
    requirement_clarity: float,
    domain_history: float,
    scope_coverage: float,
) -> list[str]:
    """Generate actionable recommendations for each factor.

    Suggests improvements for factors that score below threshold.

    Args:
        input_tier: Current input tier.
        input_completeness: Input completeness sub-score.
        document_detail: Document detail sub-score.
        requirement_clarity: Requirement clarity sub-score.
        domain_history: Domain history sub-score.
        scope_coverage: Scope coverage sub-score.

    Returns:
        List of actionable recommendation strings.

    Requirements: 15.8
    """
    recommendations: list[str] = []

    # Input completeness recommendations
    if input_tier == 0:
        potential_gain = TIER_RANGES[1][1] - TIER_RANGES[0][1]
        recommendations.append(
            f"⚠️ This is a Tier 0 (ballpark) estimate based on BRD only. "
            f"Upload a PRD to advance to Tier 1 and gain +{potential_gain} points "
            f"on input completeness. Estimates at Tier 0 have ±40-50% uncertainty."
        )
    elif input_tier == 1:
        potential_gain = TIER_RANGES[2][1] - TIER_RANGES[1][1]
        recommendations.append(
            f"Upload an HLD document to advance to Tier 2 and potentially gain "
            f"+{potential_gain} points on input completeness."
        )
    elif input_tier == 2:
        potential_gain = TIER_RANGES[3][1] - TIER_RANGES[2][1]
        recommendations.append(
            f"Upload dependent service documentation to advance to Tier 3 and "
            f"potentially gain +{potential_gain} points on input completeness."
        )

    # Document detail recommendations
    if document_detail < 50:
        recommendations.append(
            "Improve document detail: add more structured sections, diagrams, "
            "and granular specifications to increase the document detail score."
        )
    elif document_detail < 75:
        recommendations.append(
            "Consider adding more specific technical details, acceptance criteria, "
            "and architecture diagrams to strengthen document quality."
        )

    # Requirement clarity recommendations
    if requirement_clarity < 50:
        recommendations.append(
            "Several requirements appear ambiguous or contradictory. "
            "Clarifying undefined terms and resolving contradictions could "
            "significantly improve estimation reliability."
        )
    elif requirement_clarity < 75:
        recommendations.append(
            "Some requirements could be more specific. Adding concrete acceptance "
            "criteria and removing ambiguous language would improve clarity."
        )

    # Domain history recommendations
    if domain_history < 30:
        recommendations.append(
            "No historical estimation data found for this Domain/Stream combination. "
            "As more estimations are generated, confidence in future estimates will increase."
        )
    elif domain_history < 60:
        recommendations.append(
            "Limited historical data available. Additional estimations in this "
            "Domain/Stream will improve baseline comparisons."
        )

    # Scope coverage recommendations
    if scope_coverage < 50:
        recommendations.append(
            "Scope coverage is low. Clarifying partially estimated and "
            "not-estimable scope items could significantly improve coverage."
        )
    elif scope_coverage < 75:
        recommendations.append(
            "Moderate scope coverage. Addressing the partially estimated items "
            "with more detailed requirements would improve estimation completeness."
        )

    return recommendations


def _generate_explanation(
    overall: float,
    input_completeness: float,
    document_detail: float,
    requirement_clarity: float,
    domain_history: float,
    scope_coverage: float,
) -> str:
    """Generate a textual explanation of factor contributions.

    Describes how each factor contributed to the overall score.

    Args:
        overall: The computed overall confidence score.
        input_completeness: Input completeness sub-score.
        document_detail: Document detail sub-score.
        requirement_clarity: Requirement clarity sub-score.
        domain_history: Domain history sub-score.
        scope_coverage: Scope coverage sub-score.

    Returns:
        Human-readable explanation string.

    Requirements: 3.5, 15.7
    """
    contributions = [
        (
            "Input Completeness",
            input_completeness,
            WEIGHT_INPUT_COMPLETENESS,
            input_completeness * WEIGHT_INPUT_COMPLETENESS,
        ),
        (
            "Document Detail",
            document_detail,
            WEIGHT_DOCUMENT_DETAIL,
            document_detail * WEIGHT_DOCUMENT_DETAIL,
        ),
        (
            "Requirement Clarity",
            requirement_clarity,
            WEIGHT_REQUIREMENT_CLARITY,
            requirement_clarity * WEIGHT_REQUIREMENT_CLARITY,
        ),
        (
            "Domain History",
            domain_history,
            WEIGHT_DOMAIN_HISTORY,
            domain_history * WEIGHT_DOMAIN_HISTORY,
        ),
        (
            "Scope Coverage",
            scope_coverage,
            WEIGHT_SCOPE_COVERAGE,
            scope_coverage * WEIGHT_SCOPE_COVERAGE,
        ),
    ]

    lines = [f"Composite Confidence Score: {overall:.1f}/100"]
    lines.append("")
    lines.append("Factor contributions:")

    for name, score, weight, contribution in contributions:
        lines.append(
            f"  - {name}: {score:.1f}/100 × {weight:.0%} weight = "
            f"{contribution:.1f} points"
        )

    # Identify strongest and weakest factors
    sorted_contributions = sorted(contributions, key=lambda x: x[1], reverse=True)
    strongest = sorted_contributions[0]
    weakest = sorted_contributions[-1]

    lines.append("")
    lines.append(
        f"Strongest factor: {strongest[0]} ({strongest[1]:.1f}/100). "
        f"Weakest factor: {weakest[0]} ({weakest[1]:.1f}/100)."
    )

    return "\n".join(lines)
