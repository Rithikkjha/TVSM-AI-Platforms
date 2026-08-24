"""Unit tests for the scope analyzer service.

Tests: scope extraction, classification, coverage formula, template comparison, recommendations.
"""

import json
import pytest
from unittest.mock import AsyncMock

from app.models.schemas import (
    BaseTemplate,
    ClassifiedScopeItem,
    Domain,
    SLMOptions,
    SLMResponse,
    ScopeAnalysis,
    ScopeItem,
    Stream,
    TemplateComparison,
)
from app.services.scope_analyzer import (
    _determine_item_status,
    _parse_scope_items_response,
    analyze_scope,
    calculate_coverage,
    classify_scope_items,
    compare_with_template,
    extract_scope_items,
    generate_recommendations,
)


class TestCalculateCoverage:
    def test_all_fully_estimated(self):
        items = [
            ClassifiedScopeItem(id="1", name="A", type="feature", status="fully_estimated"),
            ClassifiedScopeItem(id="2", name="B", type="feature", status="fully_estimated"),
        ]
        assert calculate_coverage(items) == 1.0

    def test_all_not_estimable(self):
        items = [
            ClassifiedScopeItem(id="1", name="A", type="feature", status="not_estimable"),
            ClassifiedScopeItem(id="2", name="B", type="feature", status="not_estimable"),
        ]
        assert calculate_coverage(items) == 0.0

    def test_mixed_coverage(self):
        items = [
            ClassifiedScopeItem(id="1", name="A", type="feature", status="fully_estimated"),
            ClassifiedScopeItem(id="2", name="B", type="feature", status="partially_estimated"),
            ClassifiedScopeItem(id="3", name="C", type="feature", status="not_estimable"),
        ]
        # (1 + 0.5*1) / 3 = 1.5/3 = 0.5
        assert calculate_coverage(items) == 0.5

    def test_empty_list_returns_zero(self):
        assert calculate_coverage([]) == 0.0

    def test_all_partially_estimated(self):
        items = [
            ClassifiedScopeItem(id="1", name="A", type="feature", status="partially_estimated"),
            ClassifiedScopeItem(id="2", name="B", type="feature", status="partially_estimated"),
        ]
        # (0 + 0.5*2) / 2 = 1/2 = 0.5
        assert calculate_coverage(items) == 0.5

    def test_coverage_between_0_and_1(self):
        items = [
            ClassifiedScopeItem(id="1", name="A", type="feature", status="fully_estimated"),
            ClassifiedScopeItem(id="2", name="B", type="feature", status="partially_estimated"),
            ClassifiedScopeItem(id="3", name="C", type="feature", status="not_estimable"),
            ClassifiedScopeItem(id="4", name="D", type="feature", status="fully_estimated"),
        ]
        # (2 + 0.5*1) / 4 = 2.5/4 = 0.625
        coverage = calculate_coverage(items)
        assert 0 <= coverage <= 1
        assert abs(coverage - 0.625) < 0.001


class TestClassifyScopeItems:
    def test_classifies_items_based_on_effort_text(self):
        items = [
            ScopeItem(id="1", name="User Authentication Login", type="feature"),
            ScopeItem(id="2", name="Unknown Widget XYZ", type="feature"),
        ]
        effort_json = '{"backend": "user authentication login flow implemented"}'
        classified = classify_scope_items(items, effort_json)
        assert len(classified) == 2
        # First item should be found (keywords match)
        assert classified[0].status in ("fully_estimated", "partially_estimated")
        # Second item likely not found
        assert classified[1].status in ("partially_estimated", "not_estimable")

    def test_empty_items_returns_empty(self):
        assert classify_scope_items([], "some effort") == []


class TestCompareWithTemplate:
    def test_returns_none_without_template(self):
        items = [ClassifiedScopeItem(id="1", name="Auth", type="feature", status="fully_estimated")]
        result = compare_with_template(items, None)
        assert result is None

    def test_matches_template_areas(self):
        items = [
            ClassifiedScopeItem(id="1", name="User Authentication", type="feature", status="fully_estimated"),
            ClassifiedScopeItem(id="2", name="Payment Gateway", type="integration", status="fully_estimated"),
        ]
        template = BaseTemplate(
            templateId="T1",
            domain=Domain.SHOP,
            stream=Stream.D2C,
            scopeAreas=["Authentication", "Payment", "Cart"],
            createdBy="admin",
            createdAt="2024-01-01",
        )
        result = compare_with_template(items, template)
        assert result is not None
        assert isinstance(result, TemplateComparison)
        # Cart should be unmatched since no item covers it
        assert "Cart" in result.unmatchedTemplateAreas

    def test_empty_template_scope_areas(self):
        items = [ClassifiedScopeItem(id="1", name="Auth", type="feature", status="fully_estimated")]
        template = BaseTemplate(
            templateId="T1",
            domain=Domain.SHOP,
            stream=Stream.D2C,
            scopeAreas=[],
            createdBy="admin",
            createdAt="2024-01-01",
        )
        result = compare_with_template(items, template)
        assert result is not None
        assert result.matchedItems == []
        assert result.unmatchedTemplateAreas == []


class TestParseResponse:
    def test_valid_json_response(self):
        content = json.dumps({
            "items": [
                {"id": "SCOPE-001", "name": "User Login", "type": "feature"},
                {"id": "SCOPE-002", "name": "Payment API", "type": "api_endpoint"},
            ]
        })
        items = _parse_scope_items_response(content)
        assert len(items) == 2
        assert items[0].name == "User Login"
        assert items[1].type == "api_endpoint"

    def test_invalid_json_returns_empty(self):
        items = _parse_scope_items_response("not json")
        assert items == []

    def test_invalid_type_defaults_to_feature(self):
        content = json.dumps({
            "items": [{"id": "1", "name": "Test", "type": "invalid_type"}]
        })
        items = _parse_scope_items_response(content)
        assert len(items) == 1
        assert items[0].type == "feature"


class TestExtractScopeItems:
    @pytest.mark.asyncio
    async def test_extracts_items_from_slm(self):
        mock_slm = AsyncMock()
        mock_slm.inference.return_value = SLMResponse(
            content=json.dumps({
                "items": [
                    {"id": "SCOPE-001", "name": "Dashboard", "type": "screen"},
                    {"id": "SCOPE-002", "name": "Auth Service", "type": "integration"},
                ]
            }),
            model="qwen3:4b",
            usage={"promptTokens": 100, "completionTokens": 50},
            inferenceTimeMs=200,
        )
        items = await extract_scope_items("Some PRD content", mock_slm)
        assert len(items) == 2
        assert items[0].name == "Dashboard"

    @pytest.mark.asyncio
    async def test_returns_empty_on_slm_failure(self):
        mock_slm = AsyncMock()
        mock_slm.inference.side_effect = Exception("SLM failed")
        items = await extract_scope_items("PRD content", mock_slm)
        assert items == []


class TestGenerateRecommendations:
    def test_recommendations_for_partial_items(self):
        items = [
            ClassifiedScopeItem(id="1", name="Auth", type="feature", status="fully_estimated"),
            ClassifiedScopeItem(id="2", name="Cart", type="feature", status="partially_estimated"),
            ClassifiedScopeItem(id="3", name="API", type="feature", status="not_estimable"),
        ]
        recommendations = generate_recommendations(items, 0.5)
        assert len(recommendations) > 0
        # Should mention improving coverage
        combined = " ".join(recommendations)
        assert "coverage" in combined.lower() or "clarify" in combined.lower()

    def test_high_coverage_positive_recommendation(self):
        items = [
            ClassifiedScopeItem(id="1", name="A", type="feature", status="fully_estimated"),
            ClassifiedScopeItem(id="2", name="B", type="feature", status="fully_estimated"),
        ]
        recommendations = generate_recommendations(items, 1.0)
        combined = " ".join(recommendations)
        assert "excellent" in combined.lower() or "good" in combined.lower()

    def test_empty_items_recommendation(self):
        recommendations = generate_recommendations([], 0.0)
        assert len(recommendations) > 0


class TestAnalyzeScope:
    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self):
        mock_slm = AsyncMock()
        mock_slm.inference.return_value = SLMResponse(
            content=json.dumps({
                "items": [
                    {"id": "SCOPE-001", "name": "User Login Feature", "type": "feature"},
                ]
            }),
            model="qwen3:4b",
            usage={"promptTokens": 100, "completionTokens": 50},
            inferenceTimeMs=200,
        )

        result = await analyze_scope(
            prd_text="User login feature requirement",
            effort_breakdown_json='{"backend": "user login feature"}',
            slm_engine=mock_slm,
            template=None,
        )

        assert isinstance(result, ScopeAnalysis)
        assert len(result.items) == 1
        assert 0 <= result.coverage <= 1
        assert result.templateComparison is None
