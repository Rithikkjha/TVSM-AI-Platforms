"""Scoring Matrix Calculator for Build vs Buy evaluations.

Implements a Gartner-style weighted scoring matrix with 8 dimensions.
Calculates weighted totals, validates inputs, and ranks options.
"""

from dataclasses import dataclass
from typing import Optional


# Default Gartner-style dimension weights (must sum to 1.0)
DEFAULT_WEIGHTS: dict[str, float] = {
    "business_value": 0.20,
    "technology_fit": 0.15,
    "functional_fit": 0.15,
    "financial": 0.20,
    "operational_sustainability": 0.15,
    "business_agility": 0.05,
    "vendor_risk": 0.05,
    "ai_readiness": 0.05,
}

DIMENSIONS = list(DEFAULT_WEIGHTS.keys())
SCORE_MIN = 1
SCORE_MAX = 5


@dataclass
class DimensionScore:
    """A score for a single dimension of an option."""

    dimension: str
    score: int  # 1-5
    source: str  # "manual" or "slm_suggested"
    confidence: Optional[float] = None  # SLM confidence 0-1


@dataclass
class WeightedResult:
    """Aggregated scoring result for one option."""

    option_id: str
    dimension_scores: list[DimensionScore]
    weighted_total: float  # 1.00 - 5.00
    scored_dimensions: int
    total_dimensions: int
    is_complete: bool


def validate_weights(weights: dict[str, float]) -> bool:
    """Validate weights sum to 1.0 (100%) within floating-point tolerance (±0.001)."""
    return abs(sum(weights.values()) - 1.0) <= 0.001


def validate_score(score: int) -> bool:
    """Validate score is between 1 and 5 inclusive."""
    return SCORE_MIN <= score <= SCORE_MAX


def calculate_weighted_total(
    scores: dict[str, int],
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> float:
    """Calculate weighted total from dimension scores and weights.

    Only includes dimensions that are both in scores dict AND in weights dict.
    Returns value in range [1.0, 5.0].
    """
    total = 0.0
    for dimension, score in scores.items():
        if dimension in weights:
            total += score * weights[dimension]
    return total


def get_unscored_dimensions(
    scores: dict[str, int],
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> list[str]:
    """Return list of dimension keys present in weights but not in scores."""
    return [dim for dim in weights if dim not in scores]


def rank_options(results: list[WeightedResult]) -> list[WeightedResult]:
    """Rank options by weighted total, descending. Only ranks complete options."""
    complete = [r for r in results if r.is_complete]
    return sorted(complete, key=lambda r: r.weighted_total, reverse=True)
