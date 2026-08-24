"""TCO (Total Cost of Ownership) Calculator for Build vs Buy evaluations.

Computes 3-Year TCO, 5-Year TCO, Annual Run Cost, and Cost per User
from structured cost inputs.
"""

from dataclasses import dataclass, field, fields
from typing import Optional


@dataclass
class Year0Costs:
    """Initial (Year 0) cost breakdown."""
    license: float = 0.0
    implementation: float = 0.0
    migration: float = 0.0
    infrastructure: float = 0.0
    training: float = 0.0
    professional_services: float = 0.0

    @property
    def total(self) -> float:
        return sum([
            self.license, self.implementation, self.migration,
            self.infrastructure, self.training, self.professional_services
        ])


@dataclass
class RecurringCosts:
    """Annual recurring costs (Year 1-5)."""
    license_renewal: float = 0.0
    cloud: float = 0.0
    infrastructure: float = 0.0
    storage: float = 0.0
    ktlo_people: float = 0.0
    vendor_amc: float = 0.0
    change_requests: float = 0.0
    upgrades: float = 0.0
    support: float = 0.0

    @property
    def total(self) -> float:
        return sum([
            self.license_renewal, self.cloud, self.infrastructure,
            self.storage, self.ktlo_people, self.vendor_amc,
            self.change_requests, self.upgrades, self.support
        ])


@dataclass
class TCOInput:
    """Complete TCO input for one option."""
    option_id: str
    year_0: Year0Costs = field(default_factory=Year0Costs)
    yearly_costs: list[RecurringCosts] = field(default_factory=list)
    user_count: Optional[int] = None


@dataclass
class TCOResult:
    """Computed TCO metrics for one option."""
    option_id: str
    year_0_total: float
    three_year_tco: float
    five_year_tco: float
    annual_run_cost: float
    cost_per_user: Optional[float]
    yearly_totals: list[float]


def validate_costs(costs: "Year0Costs | RecurringCosts") -> list[str]:
    """Validate all cost values are non-negative.

    Returns list of field names with negative values.
    """
    invalid_fields = []
    for f in fields(costs):
        value = getattr(costs, f.name)
        if isinstance(value, (int, float)) and value < 0:
            invalid_fields.append(f.name)
    return invalid_fields


def get_year_costs(tco_input: TCOInput, year: int) -> RecurringCosts:
    """Get costs for a specific year (1-based), defaulting to last specified if not present.

    If yearly_costs is empty, returns a default RecurringCosts().
    If the year index is out of range, returns the last available entry.
    """
    if not tco_input.yearly_costs:
        return RecurringCosts()
    index = year - 1
    if index < len(tco_input.yearly_costs):
        return tco_input.yearly_costs[index]
    return tco_input.yearly_costs[-1]


def calculate_tco(tco_input: TCOInput) -> TCOResult:
    """Calculate 3-Year TCO, 5-Year TCO, Annual Run Cost, and Cost per User.

    - Unspecified years default to last-specified year's values.
    - Annual Run Cost = average of Year 1-5 recurring costs.
    - Cost per User = 5-Year TCO / user_count (if provided).
    """
    year_0_total = tco_input.year_0.total

    # Get costs for years 1 through 5
    year_costs = [get_year_costs(tco_input, y) for y in range(1, 6)]
    year_totals = [yc.total for yc in year_costs]

    three_year_tco = year_0_total + sum(year_totals[:3])
    five_year_tco = year_0_total + sum(year_totals)
    annual_run_cost = sum(year_totals) / 5.0

    cost_per_user: Optional[float] = None
    if tco_input.user_count is not None and tco_input.user_count > 0:
        cost_per_user = five_year_tco / tco_input.user_count

    yearly_totals = [year_0_total] + year_totals

    return TCOResult(
        option_id=tco_input.option_id,
        year_0_total=year_0_total,
        three_year_tco=three_year_tco,
        five_year_tco=five_year_tco,
        annual_run_cost=annual_run_cost,
        cost_per_user=cost_per_user,
        yearly_totals=yearly_totals,
    )
