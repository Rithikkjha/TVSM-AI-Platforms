"""Cost calculator service for the Project Estimation Tool.

Derives cost projections from effort breakdowns using the configured rate card.
Formula: personDays / 22 × ratePerPersonMonth per discipline.

Requirements: 10.1, 10.2, 10.3, 10.4
"""

import logging
from typing import Any, Optional

from app.models.schemas import CostProjection, DisciplineEffort, RateCard
from app.services.sharepoint_client import SharePointClient, FOLDER_ESTIMATIONS

logger = logging.getLogger(__name__)

# Default rate card values
DEFAULT_RATE_PER_PERSON_MONTH = 350000  # ₹3.5L per person per month
DEFAULT_WORKING_DAYS_PER_MONTH = 22


async def load_rate_card(sharepoint_client: SharePointClient) -> RateCard:
    """Load the rate card configuration from Config.xlsx.

    Reads both the default rate and per-discipline rates from Config.xlsx.
    Per-discipline rates are stored as keys like "rate_Digital Engineering",
    "rate_QA/Testing", etc.

    Args:
        sharepoint_client: SharePoint client for reading Config.xlsx.

    Returns:
        RateCard with configured or default values.
    """
    try:
        rows = await sharepoint_client.read_workbook(f"{FOLDER_ESTIMATIONS}/Config.xlsx", sheet="Sheet1")
        config_map: dict[str, str] = {}
        for row in rows[1:]:  # Skip header row
            if len(row) >= 2:
                config_map[str(row[0]).strip()] = str(row[1]).strip()

        rate = float(config_map.get("rate_per_person_month", str(DEFAULT_RATE_PER_PERSON_MONTH)))
        working_days = int(config_map.get("working_days_per_month", str(DEFAULT_WORKING_DAYS_PER_MONTH)))

        # Load per-discipline rates (keys like "rate_digital_engineering", "rate_devops", etc.)
        # The UI saves as lowercase with underscores, we need to map back to discipline names
        discipline_key_map = {
            "rate_digital_engineering": "Digital Engineering",
            "rate_data_science": "Data Science",
            "rate_data_engineering": "Data Engineering",
            "rate_p360_telematics___connected_features": "P360 Telematics + Connected Features",
            "rate_p360_telematics_connected_features": "P360 Telematics + Connected Features",
            "rate_devops": "DevOps",
            "rate_tech_coe": "Tech COE",
            "rate_qa_testing": "QA/Testing",
            "rate_product_design": "Product/Design",
        }
        per_discipline_rates: dict[str, float] = {}
        for key, value in config_map.items():
            if key.startswith("rate_") and key != "rate_per_person_month":
                # Try mapped name first, then use raw key stripped of "rate_"
                discipline_name = discipline_key_map.get(key)
                if not discipline_name:
                    # Fallback: strip prefix, title case
                    discipline_name = key[5:].replace("_", " ").title()
                try:
                    per_discipline_rates[discipline_name] = float(value)
                except (ValueError, TypeError):
                    pass

        return RateCard(
            ratePerPersonMonth=rate,
            workingDaysPerMonth=working_days,
            perDisciplineRates=per_discipline_rates,
        )

    except Exception as exc:
        logger.warning(f"Failed to load rate card from Config.xlsx, using defaults: {exc}")
        return RateCard(
            ratePerPersonMonth=DEFAULT_RATE_PER_PERSON_MONTH,
            workingDaysPerMonth=DEFAULT_WORKING_DAYS_PER_MONTH,
        )


def calculate_cost(
    effort_breakdown: list[DisciplineEffort],
    rate_card: RateCard,
) -> CostProjection:
    """Calculate cost projection from effort breakdown and rate card.

    Uses per-discipline rates when available, falls back to default rate.
    Formula per discipline: (personDays / workingDaysPerMonth) × disciplineRate

    Args:
        effort_breakdown: List of per-discipline effort estimates.
        rate_card: Rate card with default and per-discipline rates.

    Returns:
        CostProjection with total cost and per-discipline breakdown.

    Requirements: 10.1, 10.2, 10.3
    """
    working_days = rate_card.workingDaysPerMonth
    default_rate = rate_card.ratePerPersonMonth
    per_discipline_rates = rate_card.perDisciplineRates

    per_discipline: list[dict] = []
    total_cost = 0.0

    for effort in effort_breakdown:
        # Use per-discipline rate if available, otherwise default
        rate = per_discipline_rates.get(effort.discipline, default_rate)

        # Convert person-days to person-months, then multiply by rate
        person_months = effort.personDays / working_days
        discipline_cost = person_months * rate

        per_discipline.append({
            "discipline": effort.discipline,
            "cost": round(discipline_cost, 2),
        })
        total_cost += discipline_cost

    return CostProjection(
        total=round(total_cost, 2),
        perDiscipline=per_discipline,
        rateApplied=default_rate,
    )
