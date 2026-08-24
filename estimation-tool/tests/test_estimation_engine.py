"""Unit tests for the estimation engine service.

Tests: validation, prompt construction, response parsing, and full pipeline.
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.schemas import (
    DocumentSet,
    Domain,
    DisciplineEffort,
    EstimationRequest,
    EstimationResult,
    ExtractedDocument,
    InputTier,
    SLMResponse,
    Stream,
)
from app.services.estimation_engine import (
    EstimationError,
    ValidationError,
    _build_estimation_prompt,
    _parse_estimation_response,
    clear_config_cache,
    generate_estimation,
    load_base_template,
    load_config,
    validate_request,
)


# --- Fixtures ---


def _make_extracted_doc(filename="test.pdf", text="Test content", pages=5):
    return ExtractedDocument(
        filename=filename,
        format="pdf",
        pageCount=pages,
        textContent=text,
    )


def _make_request(
    project_name="Test Project",
    domain=Domain.SHOP,
    stream=Stream.D2C,
    description="A test project",
):
    return EstimationRequest(
        projectName=project_name,
        projectDescription=description,
        domain=domain,
        stream=stream,
        documents=DocumentSet(
            brd=_make_extracted_doc("brd.pdf", "BRD content"),
            prd=_make_extracted_doc("prd.pdf", "PRD content"),
        ),
        userId="user123",
    )


# --- validate_request tests ---


class TestValidateRequest:
    @pytest.mark.asyncio
    async def test_valid_request_passes(self):
        request = _make_request()
        await validate_request(request)  # Should not raise

    @pytest.mark.asyncio
    async def test_empty_project_name_raises(self):
        request = _make_request(project_name="   ")
        with pytest.raises(ValidationError, match="Project name is mandatory"):
            await validate_request(request)

    @pytest.mark.asyncio
    async def test_missing_domain_raises(self):
        """Domain is enforced by Pydantic enum, but test the validation logic."""
        request = _make_request()
        # Manually set domain to None to simulate invalid state
        object.__setattr__(request, "domain", None)
        with pytest.raises(ValidationError, match="Domain selection is mandatory"):
            await validate_request(request)

    @pytest.mark.asyncio
    async def test_missing_stream_raises(self):
        request = _make_request()
        object.__setattr__(request, "stream", None)
        with pytest.raises(ValidationError, match="Stream selection is mandatory"):
            await validate_request(request)


# --- _parse_estimation_response tests ---


class TestParseEstimationResponse:
    def test_valid_json_response(self):
        response = json.dumps({
            "effortBreakdown": [
                {"discipline": "Backend", "personDays": 44, "personMonths": 2.0},
                {"discipline": "Frontend", "personDays": 22, "personMonths": 1.0},
            ],
            "assumptions": ["Standard team", "No legacy code"],
            "documentDetailScore": 70,
            "requirementClarityScore": 80,
        })
        result = _parse_estimation_response(response)
        assert result is not None
        assert len(result["effortBreakdown"]) == 2
        assert result["effortBreakdown"][0]["discipline"] == "Backend"
        assert result["documentDetailScore"] == 70

    def test_json_in_code_block(self):
        response = '```json\n{"effortBreakdown": [{"discipline": "QA", "personDays": 10, "personMonths": 0.45}]}\n```'
        result = _parse_estimation_response(response)
        assert result is not None
        assert result["effortBreakdown"][0]["discipline"] == "QA"

    def test_auto_calculates_person_months(self):
        response = json.dumps({
            "effortBreakdown": [
                {"discipline": "Backend", "personDays": 44},
            ],
        })
        result = _parse_estimation_response(response)
        assert result is not None
        assert abs(result["effortBreakdown"][0]["personMonths"] - 2.0) < 0.01

    def test_invalid_json_returns_none(self):
        result = _parse_estimation_response("not valid json at all")
        assert result is None

    def test_missing_effort_breakdown_returns_none(self):
        response = json.dumps({"assumptions": ["something"]})
        result = _parse_estimation_response(response)
        assert result is None

    def test_zero_person_days_returns_none(self):
        response = json.dumps({
            "effortBreakdown": [
                {"discipline": "Backend", "personDays": 0},
            ],
        })
        result = _parse_estimation_response(response)
        assert result is None

    def test_empty_breakdown_returns_none(self):
        response = json.dumps({"effortBreakdown": []})
        result = _parse_estimation_response(response)
        assert result is None


# --- _build_estimation_prompt tests ---


class TestBuildEstimationPrompt:
    def test_tier1_prompt_includes_metadata(self):
        request = _make_request()
        prompt = _build_estimation_prompt(request, 1, {})
        assert "Test Project" in prompt
        assert "Shop" in prompt
        assert "D2C" in prompt
        assert "Input Tier: 1" in prompt
        assert "High-level estimation" in prompt.lower() or "high-level" in prompt.lower()

    def test_tier2_includes_hld(self):
        request = _make_request()
        request.documents.hld = _make_extracted_doc("hld.pdf", "HLD architecture content")
        prompt = _build_estimation_prompt(request, 2, {})
        assert "HLD Content" in prompt
        assert "architectural complexity" in prompt.lower()

    def test_tier3_includes_dependent_docs(self):
        request = _make_request()
        request.documents.hld = _make_extracted_doc("hld.pdf", "HLD content")
        request.documents.dependentServiceDocs = [
            _make_extracted_doc("dep1.md", "Service A docs")
        ]
        prompt = _build_estimation_prompt(request, 3, {})
        assert "Dependent Service Doc" in prompt
        assert "integration effort" in prompt.lower()


# --- load_config tests ---


class TestLoadConfig:
    def setup_method(self):
        clear_config_cache()

    @pytest.mark.asyncio
    async def test_load_config_from_sharepoint(self):
        mock_sp = AsyncMock()
        mock_sp.read_workbook.return_value = [
            ["Key", "Value", "UpdatedBy", "UpdatedAt"],
            ["slm_temperature", "0.5", "admin", "2024-01-01"],
            ["rate_per_person_month", "400000", "admin", "2024-01-01"],
        ]
        config = await load_config(mock_sp)
        assert config["slm_temperature"] == "0.5"
        assert config["rate_per_person_month"] == "400000"

    @pytest.mark.asyncio
    async def test_load_config_returns_empty_on_failure(self):
        mock_sp = AsyncMock()
        mock_sp.read_workbook.side_effect = Exception("Network error")
        config = await load_config(mock_sp)
        assert config == {}


# --- load_base_template tests ---


class TestLoadBaseTemplate:
    def setup_method(self):
        clear_config_cache()

    @pytest.mark.asyncio
    async def test_loads_matching_template(self):
        mock_sp = AsyncMock()
        mock_sp.read_workbook.return_value = [
            ["TemplateId", "Domain", "Stream", "ScopeAreas", "CreatedBy", "CreatedAt"],
            ["T1", "Shop", "D2C", '["Auth", "Cart", "Payment"]', "admin", "2024-01-01"],
        ]
        template = await load_base_template(mock_sp, Domain.SHOP, Stream.D2C)
        assert template is not None
        assert template.templateId == "T1"
        assert "Auth" in template.scopeAreas

    @pytest.mark.asyncio
    async def test_returns_none_when_no_match(self):
        mock_sp = AsyncMock()
        mock_sp.read_workbook.return_value = [
            ["TemplateId", "Domain", "Stream", "ScopeAreas", "CreatedBy", "CreatedAt"],
            ["T1", "Buy", "D2C", '["Checkout"]', "admin", "2024-01-01"],
        ]
        template = await load_base_template(mock_sp, Domain.SHOP, Stream.D2C)
        assert template is None

    @pytest.mark.asyncio
    async def test_returns_none_on_error(self):
        mock_sp = AsyncMock()
        mock_sp.read_workbook.side_effect = Exception("Unavailable")
        template = await load_base_template(mock_sp, Domain.SHOP, Stream.D2C)
        assert template is None


# --- generate_estimation integration test ---


class TestGenerateEstimation:
    def setup_method(self):
        clear_config_cache()

    @pytest.mark.asyncio
    async def test_full_pipeline_produces_result(self):
        request = _make_request()

        slm_response_content = json.dumps({
            "effortBreakdown": [
                {"discipline": "Backend", "personDays": 44, "personMonths": 2.0},
                {"discipline": "Frontend", "personDays": 22, "personMonths": 1.0},
                {"discipline": "QA", "personDays": 11, "personMonths": 0.5},
            ],
            "assumptions": ["Standard team productivity", "No legacy code migration"],
            "documentDetailScore": 65,
            "requirementClarityScore": 70,
        })

        scope_response = json.dumps({
            "items": [
                {"id": "SCOPE-001", "name": "User Authentication", "type": "feature"},
                {"id": "SCOPE-002", "name": "Product Listing", "type": "feature"},
            ]
        })

        team_response = json.dumps({
            "team": [
                {"discipline": "Backend", "count": 2, "rationale": "Complex logic"},
                {"discipline": "Frontend", "count": 1, "rationale": "Standard UI"},
                {"discipline": "QA", "count": 1, "rationale": "Testing"},
            ]
        })

        readiness_response = json.dumps({
            "sections": [
                {"name": "Executive Summary", "present": True, "confidence": 0.9},
                {"name": "Business Objectives", "present": True, "confidence": 0.85},
            ],
            "overallScore": 75
        })

        # Mock SLM engine
        mock_slm = AsyncMock()
        mock_slm.inference = AsyncMock(
            side_effect=[
                SLMResponse(content=slm_response_content, model="qwen3:4b", usage={"promptTokens": 100, "completionTokens": 200}, inferenceTimeMs=500),
                SLMResponse(content=scope_response, model="qwen3:4b", usage={"promptTokens": 50, "completionTokens": 100}, inferenceTimeMs=300),
                SLMResponse(content=team_response, model="qwen3:4b", usage={"promptTokens": 50, "completionTokens": 100}, inferenceTimeMs=200),
                SLMResponse(content=readiness_response, model="qwen3:4b", usage={"promptTokens": 50, "completionTokens": 100}, inferenceTimeMs=200),
            ]
        )
        model_info = MagicMock(modelName="qwen3:4b")
        mock_slm.get_model_info = MagicMock(return_value=model_info)

        # Mock SharePoint client
        mock_sp = AsyncMock()
        mock_sp.read_workbook.side_effect = [
            # Config.xlsx
            [
                ["Key", "Value"],
                ["slm_temperature", "0.3"],
                ["rate_per_person_month", "350000"],
            ],
            # Templates.xlsx
            [
                ["TemplateId", "Domain", "Stream", "ScopeAreas", "CreatedBy", "CreatedAt"],
            ],
            # Config.xlsx again for rate_card
            [
                ["Key", "Value"],
                ["rate_per_person_month", "350000"],
                ["working_days_per_month", "22"],
            ],
            # EstimationIndex.xlsx for domain history
            [
                ["EstimationId", "Domain", "Stream"],
            ],
        ]

        result = await generate_estimation(request, 1, mock_slm, mock_sp)

        assert isinstance(result, EstimationResult)
        assert result.projectName == "Test Project"
        assert result.domain == Domain.SHOP
        assert result.stream == Stream.D2C
        assert result.inputTier == 1
        assert len(result.effortBreakdown) == 3
        assert result.totalEffortPersonDays == 77.0
        assert result.totalEffortPersonMonths == 3.5
        assert result.calendarDuration > 0
        assert len(result.teamComposition) >= 1
        assert result.compositeConfidence.overall > 0
        assert result.costProjection.total > 0
        assert len(result.assumptions) >= 1
        assert result.slmModelName == "qwen3:4b"
        assert result.timestamp is not None

    @pytest.mark.asyncio
    async def test_invalid_request_raises_validation_error(self):
        request = _make_request(project_name="  ")
        mock_slm = AsyncMock()
        mock_sp = AsyncMock()

        with pytest.raises(ValidationError):
            await generate_estimation(request, 1, mock_slm, mock_sp)
