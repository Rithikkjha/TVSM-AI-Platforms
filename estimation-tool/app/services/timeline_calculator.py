"""Timeline calculator service for the Project Estimation Tool.

Infers team composition from SLM analysis, calculates calendar duration
using the formula: person-months / team_size per discipline, overall = max
of all disciplines. Supports scenario modeling with multiple team variants.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7
"""

import json
import logging
from typing import Optional

from app.models.schemas import (
    DisciplineEffort,
    DurationResult,
    ScenarioResult,
    SLMOptions,
    TeamMember,
)
from app.services.slm_engine import SLMEngine

logger = logging.getLogger(__name__)

# Default working days per month for person-months conversion
WORKING_DAYS_PER_MONTH = 22


async def infer_team_composition(
    effort_breakdown: list[DisciplineEffort],
    slm_engine: SLMEngine,
) -> list[TeamMember]:
    """Infer recommended team composition from SLM analysis.

    Asks the SLM to suggest team sizes per discipline based on the effort
    breakdown and produces a team allocation recommendation.

    Args:
        effort_breakdown: Per-discipline effort estimates.
        slm_engine: SLM engine for inference.

    Returns:
        List of TeamMember recommendations with discipline and count.

    Requirements: 13.1, 13.6
    """
    # Build a prompt for the SLM to suggest team composition
    effort_summary = "\n".join(
        f"- {e.discipline}: {e.personDays} person-days ({e.personMonths:.1f} person-months)"
        for e in effort_breakdown
    )

    prompt = f"""Analyze the following effort breakdown and recommend the optimal team composition.
For each discipline, recommend the number of team members that would result in a reasonable
project timeline (ideally 3-6 months calendar duration).

Effort Breakdown:
{effort_summary}

Respond in JSON format only:
{{
  "team": [
    {{"discipline": "<name>", "count": <number>, "rationale": "<brief reason>"}}
  ]
}}
"""

    try:
        response = await slm_engine.inference(
            prompt,
            options=SLMOptions(temperature=0.2, maxTokens=1024),
        )

        team = _parse_team_composition_response(response.content, effort_breakdown)
        if team:
            return team

    except Exception as exc:
        logger.warning(f"SLM team composition inference failed: {exc}. Using heuristic.")

    # Fallback: heuristic-based team composition
    return _heuristic_team_composition(effort_breakdown)


def _parse_team_composition_response(
    content: str, effort_breakdown: list[DisciplineEffort]
) -> Optional[list[TeamMember]]:
    """Parse the SLM response for team composition.

    Extracts the JSON team array from the SLM response content.

    Args:
        content: Raw SLM response text.
        effort_breakdown: Original effort breakdown for validation.

    Returns:
        List of TeamMember if parsing succeeds, None otherwise.
    """
    try:
        # Try to extract JSON from the response
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()

        # Find JSON object in text
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = json_str[start:end]

        data = json.loads(json_str)
        team_data = data.get("team", [])

        team: list[TeamMember] = []
        for item in team_data:
            discipline = item.get("discipline", "")
            count = int(item.get("count", 1))
            if discipline and count > 0:
                team.append(TeamMember(discipline=discipline, count=count))

        # Validate we have at least one member for each discipline
        discipline_names = {e.discipline for e in effort_breakdown}
        covered = {t.discipline for t in team}

        # Add missing disciplines with count 1
        for d in discipline_names - covered:
            team.append(TeamMember(discipline=d, count=1))

        # Sanity-correct team sizes to be proportional to effort share.
        # The LLM often returns uniform counts (e.g., 5/5/5) which is unrealistic —
        # a discipline with 1/10th the effort shouldn't have the same headcount.
        team = _normalize_team_to_effort(team, effort_breakdown)

        return team if team else None

    except (json.JSONDecodeError, KeyError, ValueError, IndexError) as exc:
        logger.warning(f"Failed to parse team composition response: {exc}")
        return None


def _normalize_team_to_effort(
    team: list[TeamMember],
    effort_breakdown: list[DisciplineEffort],
) -> list[TeamMember]:
    """Correct team sizes so headcount is proportional to each discipline's effort.

    Anchors on the largest-effort discipline (usually Digital Engineering) and its
    LLM-suggested count, then scales other disciplines' headcount by their effort ratio.
    This prevents unrealistic uniform staffing (e.g., 5 devs + 5 QA + 5 DevOps when
    QA effort is 1/10th of Dev effort).
    """
    effort_map = {e.discipline: e.personMonths for e in effort_breakdown}
    if not effort_map:
        return team

    # Find the anchor: discipline with the most effort
    anchor_disc = max(effort_map, key=effort_map.get)
    anchor_effort = effort_map[anchor_disc]
    if anchor_effort <= 0:
        return team

    # Anchor's headcount (from LLM, capped to a sane range 1-10)
    anchor_count = next((t.count for t in team if t.discipline == anchor_disc), 5)
    anchor_count = max(1, min(anchor_count, 10))

    corrected: list[TeamMember] = []
    for t in team:
        eff = effort_map.get(t.discipline, 0)
        if t.discipline == anchor_disc:
            corrected.append(TeamMember(discipline=t.discipline, count=anchor_count))
        else:
            # Scale headcount by effort ratio, always at least 1
            ratio = eff / anchor_effort
            scaled = max(1, round(anchor_count * ratio))
            corrected.append(TeamMember(discipline=t.discipline, count=scaled))
    return corrected


def _heuristic_team_composition(
    effort_breakdown: list[DisciplineEffort],
) -> list[TeamMember]:
    """Generate heuristic-based team composition.

    Uses a simple heuristic: for each discipline, allocate enough team members
    to target approximately 4 months calendar duration.

    Args:
        effort_breakdown: Per-discipline effort estimates.

    Returns:
        List of TeamMember with heuristic allocations.
    """
    target_months = 4.0
    team: list[TeamMember] = []

    for effort in effort_breakdown:
        # Calculate team size to achieve target duration
        count = max(1, round(effort.personMonths / target_months))
        team.append(TeamMember(discipline=effort.discipline, count=count))

    return team


def calculate_duration(
    effort_breakdown: list[DisciplineEffort],
    team: list[TeamMember],
) -> DurationResult:
    """Calculate calendar duration from effort and team composition.

    Formula per discipline: calendar_months = person_months / team_size.
    Overall duration = max of all per-discipline durations.

    Args:
        effort_breakdown: Per-discipline effort in person-days/months.
        team: Team composition with count per discipline.

    Returns:
        DurationResult with total and per-discipline calendar months.

    Requirements: 13.2, 13.3, 13.7
    """
    # Build team size lookup
    team_size_map: dict[str, int] = {t.discipline: t.count for t in team}

    per_discipline: list[dict] = []
    max_duration = 0.0

    for effort in effort_breakdown:
        team_size = team_size_map.get(effort.discipline, 1)
        # Calendar months = person-months / team size
        calendar_months = effort.personMonths / team_size
        per_discipline.append({
            "discipline": effort.discipline,
            "calendarMonths": round(calendar_months, 2),
        })
        max_duration = max(max_duration, calendar_months)

    # Ensure minimum duration of 0.1 months
    total_calendar_months = max(0.1, max_duration)

    # Generate rationale
    rationale = _generate_duration_rationale(effort_breakdown, team, per_discipline)

    return DurationResult(
        totalCalendarMonths=round(total_calendar_months, 2),
        perDiscipline=per_discipline,
        rationale=rationale,
    )


def model_scenarios(
    effort_breakdown: list[DisciplineEffort],
    team_variants: list[list[TeamMember]],
) -> list[ScenarioResult]:
    """Model multiple team composition scenarios.

    Calculates calendar duration for each team variant to enable
    side-by-side comparison of staffing options.

    Args:
        effort_breakdown: Per-discipline effort estimates.
        team_variants: List of alternative team compositions to model.

    Returns:
        List of ScenarioResult with duration for each variant.

    Requirements: 13.4, 13.5
    """
    results: list[ScenarioResult] = []

    for variant in team_variants:
        duration = calculate_duration(effort_breakdown, variant)
        results.append(ScenarioResult(teamVariant=variant, duration=duration))

    return results


def _generate_duration_rationale(
    effort_breakdown: list[DisciplineEffort],
    team: list[TeamMember],
    per_discipline: list[dict],
) -> str:
    """Generate textual rationale for team allocation and duration.

    Explains how the team was allocated and what drives the overall timeline.

    Args:
        effort_breakdown: Original effort breakdown.
        team: Team composition used.
        per_discipline: Calculated per-discipline durations.

    Returns:
        Human-readable rationale string.

    Requirements: 13.6
    """
    lines: list[str] = []
    lines.append("Team allocation rationale:")
    lines.append("")

    team_map = {t.discipline: t.count for t in team}

    for effort in effort_breakdown:
        count = team_map.get(effort.discipline, 1)
        lines.append(
            f"- {effort.discipline}: {count} member(s) for "
            f"{effort.personMonths:.1f} person-months of work"
        )

    # Identify the critical path (longest discipline)
    if per_discipline:
        longest = max(per_discipline, key=lambda d: d["calendarMonths"])
        lines.append("")
        lines.append(
            f"Critical path: {longest['discipline']} at "
            f"{longest['calendarMonths']:.1f} calendar months determines "
            f"the overall project timeline."
        )

    return "\n".join(lines)
