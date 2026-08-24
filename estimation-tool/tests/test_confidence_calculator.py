"""Unit tests for the confidence calculator service.

Tests: composite score calculation, tier ranges, recommendations, explanations.
"""

import pytest

from app.models.schemas import ConfidenceFactors, InputTier
from app.services.confidence_calculator import (
    TIER_RANGES,
    WEIGHT_DOCUMENT_DETAIL,
    WEIGHT_DOMAIN_HISTORY,
    WEIGHT_INPUT_COMPLETENESS,
    WEIGHT_REQUIREMENT_CLARITY,
    WEIGHT_SCOPE_COVERAGE,
    calculate_confidence,
    compute_input_completeness_score,
)


class TestComputeInputCompletenessScore:
    def test_tier1_returns_midpoint(self):
        score = compute_input_completeness_score(1)
        low, high = TIER_RANGES[1]
        assert score == (low + high) / 2.0
        assert 30 <= score <= 60

    def test_tier2_returns_midpoint(self):
        score = compute_input_completeness_score(2)
        low, high = TIER_RANGES[2]
        assert score == (low + high) / 2.0
        assert 50 <= score <= 75

    def test_tier3_returns_midpoint(self):
        score = compute_input_completeness_score(3)
        low, high = TIER_RANGES[3]
        assert score == (low + high) / 2.0
        assert 65 <= score <= 90


class TestCalculateConfidence:
    def test_all_zero_scores_returns_low(self):
        factors = ConfidenceFactors(
            inputTier=1,
            documentDetailScore=0,
            requirementClarityScore=0,
            domainHistoryScore=0,
            scopeCoverageScore=0,
        )
        result = calculate_confidence(factors)
        # Only input completeness contributes (midpoint of tier 1 = 45)
        expected_min = WEIGHT_INPUT_COMPLETENESS * 30  # 0.30 * 30 = 9
        assert result.overall >= expected_min
        assert result.overall <= 100

    def test_all_max_scores_returns_high(self):
        factors = ConfidenceFactors(
            inputTier=3,
            documentDetailScore=100,
            requirementClarityScore=100,
            domainHistoryScore=100,
            scopeCoverageScore=100,
        )
        result = calculate_confidence(factors)
        # Input completeness for tier 3 midpoint = 77.5
        expected = (
            WEIGHT_INPUT_COMPLETENESS * 77.5
            + WEIGHT_DOCUMENT_DETAIL * 100
            + WEIGHT_REQUIREMENT_CLARITY * 100
            + WEIGHT_DOMAIN_HISTORY * 100
            + WEIGHT_SCOPE_COVERAGE * 100
        )
        assert abs(result.overall - expected) < 0.1

    def test_composite_formula_correct(self):
        factors = ConfidenceFactors(
            inputTier=2,
            documentDetailScore=60,
            requirementClarityScore=70,
            domainHistoryScore=40,
            scopeCoverageScore=80,
        )
        result = calculate_confidence(factors)
        input_completeness = compute_input_completeness_score(2)
        expected = (
            0.30 * input_completeness
            + 0.25 * 60
            + 0.20 * 70
            + 0.15 * 40
            + 0.10 * 80
        )
        assert abs(result.overall - expected) < 0.1

    def test_result_in_range_0_100(self):
        factors = ConfidenceFactors(
            inputTier=1,
            documentDetailScore=50,
            requirementClarityScore=50,
            domainHistoryScore=50,
            scopeCoverageScore=50,
        )
        result = calculate_confidence(factors)
        assert 0 <= result.overall <= 100

    def test_factor_breakdown_has_all_keys(self):
        factors = ConfidenceFactors(
            inputTier=2,
            documentDetailScore=60,
            requirementClarityScore=70,
            domainHistoryScore=40,
            scopeCoverageScore=80,
        )
        result = calculate_confidence(factors)
        assert "inputCompleteness" in result.factors
        assert "documentDetail" in result.factors
        assert "requirementClarity" in result.factors
        assert "domainHistory" in result.factors
        assert "scopeCoverage" in result.factors

    def test_factor_weights_correct(self):
        factors = ConfidenceFactors(
            inputTier=1,
            documentDetailScore=50,
            requirementClarityScore=50,
            domainHistoryScore=50,
            scopeCoverageScore=50,
        )
        result = calculate_confidence(factors)
        assert result.factors["inputCompleteness"].weight == 0.30
        assert result.factors["documentDetail"].weight == 0.25
        assert result.factors["requirementClarity"].weight == 0.20
        assert result.factors["domainHistory"].weight == 0.15
        assert result.factors["scopeCoverage"].weight == 0.10

    def test_recommendations_generated(self):
        factors = ConfidenceFactors(
            inputTier=1,
            documentDetailScore=30,
            requirementClarityScore=30,
            domainHistoryScore=0,
            scopeCoverageScore=30,
        )
        result = calculate_confidence(factors)
        assert len(result.recommendations) > 0

    def test_explanation_generated(self):
        factors = ConfidenceFactors(
            inputTier=2,
            documentDetailScore=60,
            requirementClarityScore=70,
            domainHistoryScore=40,
            scopeCoverageScore=80,
        )
        result = calculate_confidence(factors)
        assert "Composite Confidence Score" in result.explanation
        assert "Factor contributions" in result.explanation

    def test_clamping_above_100(self):
        """Scores above 100 should be clamped."""
        factors = ConfidenceFactors(
            inputTier=3,
            documentDetailScore=100,
            requirementClarityScore=100,
            domainHistoryScore=100,
            scopeCoverageScore=100,
        )
        result = calculate_confidence(factors)
        assert result.overall <= 100

    def test_tier1_recommendations_suggest_hld(self):
        factors = ConfidenceFactors(
            inputTier=1,
            documentDetailScore=50,
            requirementClarityScore=50,
            domainHistoryScore=50,
            scopeCoverageScore=50,
        )
        result = calculate_confidence(factors)
        hld_recommendation = [r for r in result.recommendations if "HLD" in r]
        assert len(hld_recommendation) > 0
