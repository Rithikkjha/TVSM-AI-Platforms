"""Unit tests for the timeline calculator service.

Tests: duration formula, team inference, scenario modeling, rationale generation.
"""

import json
import pytest
from unittest.mock import AsyncMock

from app.models.schemas import (
    DisciplineEffort,
    DurationResult,
    ScenarioResult,
    SLMResponse,
    TeamMember,
)
from app.services.timeline_calculator import (
    _generate_duration_rationale,
    _heuristic_team_composition,
    _parse_team_composition_response,
    calculate_duration,
    infer_team_composition,
    model_scenarios,
)


class TestCalculateDuration:
    def test_single_discipline(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0),
        ]
        team = [TeamMember(discipline="Backend", count=2)]
        result = calculate_duration(effort, team)

        # 2.0 / 2 = 1.0 months
        assert result.totalCalendarMonths == 1.0
        assert len(result.perDiscipline) == 1
        assert result.perDiscipline[0]["discipline"] == "Backend"
        assert result.perDiscipline[0]["calendarMonths"] == 1.0

    def test_overall_is_max_of_disciplines(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=66, personMonths=3.0),
            DisciplineEffort(discipline="Frontend", personDays=44, personMonths=2.0),
            DisciplineEffort(discipline="QA", personDays=22, personMonths=1.0),
        ]
        team = [
            TeamMember(discipline="Backend", count=1),
            TeamMember(discipline="Frontend", count=1),
            TeamMember(discipline="QA", count=1),
        ]
        result = calculate_duration(effort, team)

        # Backend: 3.0/1 = 3.0, Frontend: 2.0/1 = 2.0, QA: 1.0/1 = 1.0
        # Max = 3.0
        assert result.totalCalendarMonths == 3.0

    def test_larger_team_reduces_duration(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=88, personMonths=4.0),
        ]
        team_small = [TeamMember(discipline="Backend", count=1)]
        team_large = [TeamMember(discipline="Backend", count=4)]

        result_small = calculate_duration(effort, team_small)
        result_large = calculate_duration(effort, team_large)

        assert result_small.totalCalendarMonths == 4.0
        assert result_large.totalCalendarMonths == 1.0
        assert result_large.totalCalendarMonths < result_small.totalCalendarMonths

    def test_missing_team_discipline_defaults_to_1(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0),
        ]
        team = []  # No team members for Backend
        result = calculate_duration(effort, team)
        # Defaults to team size 1: 2.0/1 = 2.0
        assert result.totalCalendarMonths == 2.0

    def test_minimum_duration(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=1, personMonths=0.045),
        ]
        team = [TeamMember(discipline="Backend", count=10)]
        result = calculate_duration(effort, team)
        # 0.045/10 = 0.0045 → clamped to 0.1
        assert result.totalCalendarMonths >= 0.1

    def test_rationale_generated(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0),
        ]
        team = [TeamMember(discipline="Backend", count=2)]
        result = calculate_duration(effort, team)
        assert "Backend" in result.rationale
        assert "critical path" in result.rationale.lower() or "Critical path" in result.rationale


class TestModelScenarios:
    def test_multiple_team_variants(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0),
            DisciplineEffort(discipline="Frontend", personDays=22, personMonths=1.0),
        ]
        variants = [
            [TeamMember(discipline="Backend", count=1), TeamMember(discipline="Frontend", count=1)],
            [TeamMember(discipline="Backend", count=2), TeamMember(discipline="Frontend", count=1)],
            [TeamMember(discipline="Backend", count=2), TeamMember(discipline="Frontend", count=2)],
        ]
        results = model_scenarios(effort, variants)
        assert len(results) == 3
        assert all(isinstance(r, ScenarioResult) for r in results)

        # Larger teams should have shorter durations
        assert results[0].duration.totalCalendarMonths >= results[1].duration.totalCalendarMonths
        assert results[1].duration.totalCalendarMonths >= results[2].duration.totalCalendarMonths

    def test_empty_variants(self):
        effort = [DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0)]
        results = model_scenarios(effort, [])
        assert results == []


class TestHeuristicTeamComposition:
    def test_targets_4_months(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=176, personMonths=8.0),
        ]
        team = _heuristic_team_composition(effort)
        assert len(team) == 1
        assert team[0].discipline == "Backend"
        # 8.0 / 4.0 = 2.0 → round to 2
        assert team[0].count == 2

    def test_minimum_one_member(self):
        effort = [
            DisciplineEffort(discipline="QA", personDays=5, personMonths=0.23),
        ]
        team = _heuristic_team_composition(effort)
        assert team[0].count >= 1


class TestParseTeamCompositionResponse:
    def test_valid_response(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0),
            DisciplineEffort(discipline="Frontend", personDays=22, personMonths=1.0),
        ]
        content = json.dumps({
            "team": [
                {"discipline": "Backend", "count": 2, "rationale": "Complex"},
                {"discipline": "Frontend", "count": 1, "rationale": "Simple"},
            ]
        })
        team = _parse_team_composition_response(content, effort)
        assert team is not None
        assert len(team) == 2

    def test_invalid_json_returns_none(self):
        effort = [DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0)]
        team = _parse_team_composition_response("invalid", effort)
        assert team is None

    def test_missing_discipline_gets_added(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0),
            DisciplineEffort(discipline="Frontend", personDays=22, personMonths=1.0),
        ]
        content = json.dumps({
            "team": [
                {"discipline": "Backend", "count": 2, "rationale": "Complex"},
            ]
        })
        team = _parse_team_composition_response(content, effort)
        assert team is not None
        disciplines = {t.discipline for t in team}
        assert "Backend" in disciplines
        assert "Frontend" in disciplines


class TestInferTeamComposition:
    @pytest.mark.asyncio
    async def test_uses_slm_response(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0),
            DisciplineEffort(discipline="Frontend", personDays=22, personMonths=1.0),
        ]
        mock_slm = AsyncMock()
        mock_slm.inference.return_value = SLMResponse(
            content=json.dumps({
                "team": [
                    {"discipline": "Backend", "count": 2, "rationale": "Complex"},
                    {"discipline": "Frontend", "count": 1, "rationale": "Simple"},
                ]
            }),
            model="qwen3:4b",
            usage={"promptTokens": 50, "completionTokens": 50},
            inferenceTimeMs=200,
        )
        team = await infer_team_composition(effort, mock_slm)
        assert len(team) == 2

    @pytest.mark.asyncio
    async def test_falls_back_to_heuristic_on_failure(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0),
        ]
        mock_slm = AsyncMock()
        mock_slm.inference.side_effect = Exception("SLM error")
        team = await infer_team_composition(effort, mock_slm)
        assert len(team) == 1
        assert team[0].discipline == "Backend"
        assert team[0].count >= 1
