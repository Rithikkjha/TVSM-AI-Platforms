"""Unit tests for the cost calculator service.

Tests: cost derivation formula, per-discipline breakdown, rate card loading.
"""

import pytest
from unittest.mock import AsyncMock

from app.models.schemas import CostProjection, DisciplineEffort, RateCard
from app.services.cost_calculator import (
    DEFAULT_RATE_PER_PERSON_MONTH,
    DEFAULT_WORKING_DAYS_PER_MONTH,
    calculate_cost,
    load_rate_card,
)


class TestCalculateCost:
    def test_single_discipline(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0),
        ]
        rate_card = RateCard(ratePerPersonMonth=350000, workingDaysPerMonth=22)
        result = calculate_cost(effort, rate_card)

        # 44 / 22 * 350000 = 2 * 350000 = 700000
        assert result.total == 700000.0
        assert len(result.perDiscipline) == 1
        assert result.perDiscipline[0]["discipline"] == "Backend"
        assert result.perDiscipline[0]["cost"] == 700000.0
        assert result.rateApplied == 350000

    def test_multiple_disciplines(self):
        effort = [
            DisciplineEffort(discipline="Backend", personDays=44, personMonths=2.0),
            DisciplineEffort(discipline="Frontend", personDays=22, personMonths=1.0),
            DisciplineEffort(discipline="QA", personDays=11, personMonths=0.5),
        ]
        rate_card = RateCard(ratePerPersonMonth=350000, workingDaysPerMonth=22)
        result = calculate_cost(effort, rate_card)

        # Backend: 44/22 * 350000 = 700000
        # Frontend: 22/22 * 350000 = 350000
        # QA: 11/22 * 350000 = 175000
        # Total: 1225000
        assert result.total == 1225000.0
        assert len(result.perDiscipline) == 3

        # Total should equal sum of per-discipline costs
        per_disc_total = sum(d["cost"] for d in result.perDiscipline)
        assert abs(result.total - per_disc_total) < 0.01

    def test_custom_rate_card(self):
        effort = [
            DisciplineEffort(discipline="DevOps", personDays=10, personMonths=0.45),
        ]
        rate_card = RateCard(ratePerPersonMonth=500000, workingDaysPerMonth=22)
        result = calculate_cost(effort, rate_card)

        # 10/22 * 500000 = 227272.73
        expected = (10 / 22) * 500000
        assert abs(result.total - round(expected, 2)) < 0.01
        assert result.rateApplied == 500000

    def test_cost_formula_precision(self):
        """Ensure the formula: personDays / 22 × ratePerPersonMonth."""
        effort = [
            DisciplineEffort(discipline="Backend", personDays=33, personMonths=1.5),
        ]
        rate_card = RateCard(ratePerPersonMonth=350000, workingDaysPerMonth=22)
        result = calculate_cost(effort, rate_card)

        expected = (33 / 22) * 350000
        assert abs(result.total - round(expected, 2)) < 0.01

    def test_empty_effort_breakdown(self):
        effort = []
        rate_card = RateCard(ratePerPersonMonth=350000, workingDaysPerMonth=22)
        result = calculate_cost(effort, rate_card)
        assert result.total == 0.0
        assert result.perDiscipline == []


class TestLoadRateCard:
    @pytest.mark.asyncio
    async def test_loads_from_sharepoint(self):
        mock_sp = AsyncMock()
        mock_sp.read_workbook.return_value = [
            ["Key", "Value"],
            ["rate_per_person_month", "400000"],
            ["working_days_per_month", "20"],
        ]
        rate_card = await load_rate_card(mock_sp)
        assert rate_card.ratePerPersonMonth == 400000
        assert rate_card.workingDaysPerMonth == 20

    @pytest.mark.asyncio
    async def test_falls_back_to_defaults_on_error(self):
        mock_sp = AsyncMock()
        mock_sp.read_workbook.side_effect = Exception("Network error")
        rate_card = await load_rate_card(mock_sp)
        assert rate_card.ratePerPersonMonth == DEFAULT_RATE_PER_PERSON_MONTH
        assert rate_card.workingDaysPerMonth == DEFAULT_WORKING_DAYS_PER_MONTH

    @pytest.mark.asyncio
    async def test_defaults_when_keys_missing(self):
        mock_sp = AsyncMock()
        mock_sp.read_workbook.return_value = [
            ["Key", "Value"],
            ["some_other_key", "value"],
        ]
        rate_card = await load_rate_card(mock_sp)
        assert rate_card.ratePerPersonMonth == DEFAULT_RATE_PER_PERSON_MONTH
        assert rate_card.workingDaysPerMonth == DEFAULT_WORKING_DAYS_PER_MONTH
