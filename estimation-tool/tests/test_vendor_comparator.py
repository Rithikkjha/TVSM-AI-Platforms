"""Tests for the vendor comparator service."""

import pytest

from app.models.schemas import (
    ClassifiedScopeItem,
    CompositeConfidenceScore,
    ConfidenceFactor,
    CostProjection,
    DisciplineEffort,
    DurationResult,
    EstimationResult,
    ScopeAnalysis,
    TeamMember,
    VendorComparison,
    VendorCostComparison,
    VendorDeliveryComparison,
    VendorQualityAssessment,
)
from app.services.vendor_comparator import (
    COST_VARIANCE_THRESHOLD,
    _compare_cost,
    _compare_delivery,
    consolidate_comparisons,
)


class TestCompareCost:
    """Tests for cost comparison logic."""

    def test_equal_costs_not_flagged(self):
        result = _compare_cost(vendor_cost=100000, internal_cost=100000)
        assert result.variancePercent == 0.0
        assert result.flagged is False

    def test_vendor_25_percent_higher_flagged(self):
        # Variance = |125000 - 100000| / 100000 * 100 = 25.0
        # >25% threshold → but it's exactly 25, not exceeding
        result = _compare_cost(vendor_cost=125000, internal_cost=100000)
        assert result.variancePercent == 25.0
        assert result.flagged is False  # Not >25%, exactly 25%

    def test_vendor_26_percent_higher_flagged(self):
        # Variance = |126000 - 100000| / 100000 * 100 = 26.0
        result = _compare_cost(vendor_cost=126000, internal_cost=100000)
        assert result.variancePercent == 26.0
        assert result.flagged is True

    def test_vendor_lower_by_30_percent_flagged(self):
        # Variance = |70000 - 100000| / 100000 * 100 = 30.0
        result = _compare_cost(vendor_cost=70000, internal_cost=100000)
        assert result.variancePercent == 30.0
        assert result.flagged is True

    def test_zero_internal_cost(self):
        result = _compare_cost(vendor_cost=50000, internal_cost=0)
        assert result.variancePercent == 0.0
        assert result.flagged is False

    def test_variance_formula_correct(self):
        # |V - I| / I * 100
        result = _compare_cost(vendor_cost=150000, internal_cost=200000)
        expected = abs(150000 - 200000) / 200000 * 100
        assert result.variancePercent == expected


class TestCompareDelivery:
    """Tests for delivery comparison logic."""

    def test_matching_timelines_not_flagged(self):
        result = _compare_delivery(
            vendor_timeline=6.0,
            internal_timeline=6.0,
            vendor_team_size=5,
            internal_team_size=5,
        )
        assert result.flagged is False

    def test_vendor_much_shorter_flagged(self):
        # ratio = 2/6 = 0.33 < 0.7 → flagged
        result = _compare_delivery(
            vendor_timeline=2.0,
            internal_timeline=6.0,
            vendor_team_size=10,
            internal_team_size=5,
        )
        assert result.flagged is True

    def test_vendor_much_longer_flagged(self):
        # ratio = 10/6 = 1.67 > 1.5 → flagged
        result = _compare_delivery(
            vendor_timeline=10.0,
            internal_timeline=6.0,
            vendor_team_size=3,
            internal_team_size=5,
        )
        assert result.flagged is True

    def test_vendor_within_range_not_flagged(self):
        # ratio = 5/6 = 0.83 → within [0.7, 1.5]
        result = _compare_delivery(
            vendor_timeline=5.0,
            internal_timeline=6.0,
            vendor_team_size=5,
            internal_team_size=5,
        )
        assert result.flagged is False

    def test_team_size_comparison_larger(self):
        result = _compare_delivery(
            vendor_timeline=5.0,
            internal_timeline=5.0,
            vendor_team_size=10,
            internal_team_size=5,
        )
        assert "larger team" in result.teamSizeComparison

    def test_team_size_comparison_smaller(self):
        result = _compare_delivery(
            vendor_timeline=5.0,
            internal_timeline=5.0,
            vendor_team_size=3,
            internal_team_size=5,
        )
        assert "smaller team" in result.teamSizeComparison

    def test_team_size_not_specified(self):
        result = _compare_delivery(
            vendor_timeline=5.0,
            internal_timeline=5.0,
            vendor_team_size=None,
            internal_team_size=5,
        )
        assert "not specified" in result.teamSizeComparison


class TestConsolidateComparisons:
    """Tests for multi-vendor consolidation."""

    def _make_comparison(
        self, name: str, coverage: float, cost_var: float, timeline_ratio: float
    ) -> VendorComparison:
        return VendorComparison(
            vendorName=name,
            qualityAssessment=VendorQualityAssessment(
                scopeCoverage=coverage, gaps=[], addressed=[]
            ),
            costComparison=VendorCostComparison(
                vendorCost=100000 * (1 + cost_var / 100),
                internalCost=100000,
                variancePercent=abs(cost_var),
                flagged=abs(cost_var) > 25,
            ),
            deliveryComparison=VendorDeliveryComparison(
                vendorTimeline=6 * timeline_ratio,
                internalTimeline=6.0,
                teamSizeComparison="Same",
                flagged=False,
            ),
            assumptions=[],
        )

    def test_empty_comparisons(self):
        result = consolidate_comparisons([])
        assert result.comparisons == []
        assert result.rankings == []

    def test_single_vendor_ranked_first(self):
        comp = self._make_comparison("Vendor A", 0.9, 10, 1.0)
        result = consolidate_comparisons([comp])
        assert len(result.rankings) == 1
        assert result.rankings[0]["rank"] == 1
        assert result.rankings[0]["vendorName"] == "Vendor A"

    def test_multiple_vendors_ranked_by_composite(self):
        # Vendor A: high quality, low cost variance, matching timeline
        comp_a = self._make_comparison("Vendor A", 0.95, 5, 1.0)
        # Vendor B: lower quality, higher cost variance
        comp_b = self._make_comparison("Vendor B", 0.6, 30, 1.2)

        result = consolidate_comparisons([comp_a, comp_b])

        assert len(result.rankings) == 2
        assert result.rankings[0]["vendorName"] == "Vendor A"
        assert result.rankings[1]["vendorName"] == "Vendor B"
        # Vendor A should be ranked 1
        assert result.comparisons[0].overallRank == 1

    def test_rankings_have_scores(self):
        comp = self._make_comparison("Vendor A", 0.8, 15, 1.1)
        result = consolidate_comparisons([comp])

        ranking = result.rankings[0]
        assert "qualityScore" in ranking
        assert "costScore" in ranking
        assert "deliveryScore" in ranking
        assert "compositeScore" in ranking
