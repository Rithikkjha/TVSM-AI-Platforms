"""Scope analyzer service for the Project Estimation Tool.

Extracts scope items from PRD via SLM, classifies estimation status,
calculates scope coverage, and compares against base templates.

Requirements: 14.1-14.6, 16.3-16.9
"""

import json
import logging
from typing import Optional

from app.models.schemas import (
    BaseTemplate,
    ClassifiedScopeItem,
    ScopeAnalysis,
    ScopeItem,
    SLMOptions,
    TemplateComparison,
)
from app.services.slm_engine import SLMEngine

logger = logging.getLogger(__name__)


async def extract_scope_items(
    prd_text: str,
    slm_engine: SLMEngine,
) -> list[ScopeItem]:
    """Extract discrete scope items from PRD text via SLM.

    Asks the SLM to identify features, user stories, integrations,
    screens, and API endpoints from the PRD content.

    Args:
        prd_text: Full text content of the PRD document.
        slm_engine: SLM engine for inference.

    Returns:
        List of ScopeItem objects extracted from the PRD.

    Requirements: 14.1
    """
    prompt = f"""Analyze the following PRD (Product Requirements Document) and extract all discrete
scope items. Identify:
- Features (major functional capabilities)
- User stories (specific user-facing behaviors)
- Integrations (connections to external/internal services)
- Screens (UI pages or views)
- API endpoints (backend service endpoints)

PRD Content:
---
{prd_text[:6000]}
---

Respond in JSON format only:
{{
  "items": [
    {{"id": "SCOPE-001", "name": "<item name>", "type": "<feature|user_story|integration|screen|api_endpoint>"}}
  ]
}}
"""

    try:
        response = await slm_engine.inference(
            prompt,
            options=SLMOptions(temperature=0.2, maxTokens=2048),
        )
        items = _parse_scope_items_response(response.content)
        if items:
            return items
    except Exception as exc:
        logger.warning(f"SLM scope extraction failed: {exc}. Returning empty scope.")

    return []


def _parse_scope_items_response(content: str) -> list[ScopeItem]:
    """Parse the SLM response for scope items.

    Args:
        content: Raw SLM response text containing JSON.

    Returns:
        List of ScopeItem objects parsed from the response.
    """
    try:
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()

        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = json_str[start:end]

        data = json.loads(json_str)
        raw_items = data.get("items", [])

        items: list[ScopeItem] = []
        valid_types = {"feature", "user_story", "integration", "screen", "api_endpoint"}

        for i, raw in enumerate(raw_items):
            item_id = raw.get("id", f"SCOPE-{i+1:03d}")
            name = raw.get("name", "")
            item_type = raw.get("type", "feature")

            if item_type not in valid_types:
                item_type = "feature"

            if name:
                items.append(ScopeItem(id=item_id, name=name, type=item_type))

        return items

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning(f"Failed to parse scope items response: {exc}")
        return []


def classify_scope_items(
    items: list[ScopeItem],
    effort_breakdown_json: str,
) -> list[ClassifiedScopeItem]:
    """Classify scope items by estimation status.

    Determines whether each scope item is fully_estimated,
    partially_estimated, or not_estimable based on the estimation output.

    Args:
        items: List of extracted scope items.
        effort_breakdown_json: JSON string of the effort analysis to check coverage.

    Returns:
        List of ClassifiedScopeItem with status and reason.

    Requirements: 14.2
    """
    if not items:
        return []

    # Parse effort data for coverage matching
    effort_text = effort_breakdown_json.lower()

    classified: list[ClassifiedScopeItem] = []

    for item in items:
        status, reason = _determine_item_status(item, effort_text)
        classified.append(
            ClassifiedScopeItem(
                id=item.id,
                name=item.name,
                type=item.type,
                status=status,
                reason=reason,
            )
        )

    return classified


def _determine_item_status(
    item: ScopeItem,
    effort_text: str,
) -> tuple[str, Optional[str]]:
    """Determine the estimation status of a single scope item.

    Uses keyword matching to determine if the item was covered in the
    effort analysis.

    Args:
        item: The scope item to classify.
        effort_text: Lowercased effort analysis text for matching.

    Returns:
        Tuple of (status, reason) where status is one of:
        fully_estimated, partially_estimated, not_estimable.
    """
    item_name_lower = item.name.lower()
    keywords = item_name_lower.split()

    # Count how many keywords from the item name appear in the effort text
    matches = sum(1 for kw in keywords if len(kw) > 3 and kw in effort_text)
    match_ratio = matches / max(len(keywords), 1)

    if match_ratio >= 0.5:
        return "fully_estimated", None
    elif match_ratio >= 0.2:
        return "partially_estimated", (
            f"Only partial coverage found for '{item.name}'. "
            "Consider adding more detail about this item."
        )
    else:
        return "not_estimable", (
            f"Insufficient information to estimate '{item.name}'. "
            "Please provide specific requirements or specifications for this item."
        )


def calculate_coverage(classified_items: list[ClassifiedScopeItem]) -> float:
    """Calculate scope coverage from classified items.

    Formula: (fully_estimated + 0.5 × partially_estimated) / total.

    Args:
        classified_items: List of scope items with classification status.

    Returns:
        Coverage ratio between 0.0 and 1.0. Returns 0.0 if no items.

    Requirements: 14.3
    """
    if not classified_items:
        return 0.0

    total = len(classified_items)
    fully = sum(1 for item in classified_items if item.status == "fully_estimated")
    partially = sum(1 for item in classified_items if item.status == "partially_estimated")

    coverage = (fully + 0.5 * partially) / total
    return min(1.0, max(0.0, coverage))


def compare_with_template(
    classified_items: list[ClassifiedScopeItem],
    template: Optional[BaseTemplate],
) -> Optional[TemplateComparison]:
    """Compare PRD scope items against a base template.

    Maps extracted items against template scope areas, identifying:
    - Matched template areas covered by PRD items
    - Unmatched template areas not found in PRD
    - Additional PRD items beyond template scope

    Args:
        classified_items: Classified scope items from PRD.
        template: Base template for the domain/stream combination, or None.

    Returns:
        TemplateComparison if template is provided, None otherwise.

    Requirements: 16.4, 16.5, 16.6, 16.8
    """
    if template is None:
        return None

    template_areas = template.scopeAreas
    if not template_areas:
        return TemplateComparison(
            matchedItems=[],
            unmatchedTemplateAreas=[],
            additionalPrdScope=[],
        )

    # Normalize template areas for comparison
    normalized_template = {area.lower().strip(): area for area in template_areas}

    matched_items: list[str] = []
    matched_template_keys: set[str] = set()
    additional_prd_scope: list[str] = []

    # Match PRD items against template areas
    for item in classified_items:
        item_lower = item.name.lower().strip()
        found_match = False

        for template_key, template_area in normalized_template.items():
            # Check if the item name matches a template area (substring match)
            if (
                template_key in item_lower
                or item_lower in template_key
                or _fuzzy_match(item_lower, template_key)
            ):
                matched_items.append(template_area)
                matched_template_keys.add(template_key)
                found_match = True
                break

        if not found_match:
            additional_prd_scope.append(item.name)

    # Find unmatched template areas
    unmatched_template_areas = [
        area
        for key, area in normalized_template.items()
        if key not in matched_template_keys
    ]

    return TemplateComparison(
        matchedItems=matched_items,
        unmatchedTemplateAreas=unmatched_template_areas,
        additionalPrdScope=additional_prd_scope,
    )


def _fuzzy_match(item: str, template_area: str) -> bool:
    """Simple fuzzy matching between item name and template area.

    Checks if significant words from the item appear in the template area
    or vice versa.

    Args:
        item: Normalized item name.
        template_area: Normalized template area name.

    Returns:
        True if a reasonable match is found.
    """
    item_words = set(w for w in item.split() if len(w) > 3)
    template_words = set(w for w in template_area.split() if len(w) > 3)

    if not item_words or not template_words:
        return False

    # If more than half the words match, consider it a fuzzy match
    common = item_words & template_words
    return len(common) >= min(len(item_words), len(template_words)) * 0.5


def generate_recommendations(
    classified_items: list[ClassifiedScopeItem],
    coverage: float,
) -> list[str]:
    """Generate actionable recommendations for improving scope coverage.

    Suggests specific items to clarify and the projected improvement.

    Args:
        classified_items: List of classified scope items.
        coverage: Current scope coverage ratio.

    Returns:
        List of recommendation strings.

    Requirements: 14.5
    """
    recommendations: list[str] = []

    not_estimable = [
        item for item in classified_items if item.status == "not_estimable"
    ]
    partially_estimated = [
        item for item in classified_items if item.status == "partially_estimated"
    ]

    total = len(classified_items)
    if total == 0:
        return ["No scope items identified. Ensure the PRD contains clear features and requirements."]

    # Calculate projected improvement if partially estimated items are resolved
    if partially_estimated:
        additional_coverage = (0.5 * len(partially_estimated)) / total
        projected = min(1.0, coverage + additional_coverage)
        item_names = ", ".join(item.name for item in partially_estimated[:3])
        recommendations.append(
            f"Clarify {len(partially_estimated)} partially estimated item(s) "
            f"(e.g., {item_names}) to improve coverage from "
            f"{coverage*100:.0f}% to {projected*100:.0f}%."
        )

    # Recommendations for not-estimable items
    if not_estimable:
        additional_coverage = len(not_estimable) / total
        projected = min(1.0, coverage + additional_coverage)
        item_names = ", ".join(item.name for item in not_estimable[:3])
        recommendations.append(
            f"Provide detailed requirements for {len(not_estimable)} not-estimable item(s) "
            f"(e.g., {item_names}) to potentially improve coverage to "
            f"{projected*100:.0f}%."
        )

    if coverage >= 0.9:
        recommendations.append(
            "Scope coverage is excellent (90%+). The estimation captures most PRD items."
        )
    elif coverage >= 0.7:
        recommendations.append(
            "Scope coverage is good but could be improved by addressing "
            "the items listed above."
        )

    return recommendations


async def analyze_scope(
    prd_text: str,
    effort_breakdown_json: str,
    slm_engine: SLMEngine,
    template: Optional[BaseTemplate] = None,
) -> ScopeAnalysis:
    """Perform full scope analysis on PRD content.

    Orchestrates the complete scope analysis pipeline:
    1. Extract scope items from PRD via SLM
    2. Classify items based on estimation coverage
    3. Calculate scope coverage
    4. Compare with template (if available)
    5. Generate recommendations

    Args:
        prd_text: Full text content of the PRD document.
        effort_breakdown_json: JSON string of the effort analysis.
        slm_engine: SLM engine for inference.
        template: Optional base template for comparison.

    Returns:
        ScopeAnalysis with items, coverage, recommendations, and template comparison.

    Requirements: 14.1-14.6, 16.3-16.9
    """
    # Step 1: Extract scope items
    raw_items = await extract_scope_items(prd_text, slm_engine)

    # Step 2: Classify items
    classified = classify_scope_items(raw_items, effort_breakdown_json)

    # Step 3: Calculate coverage
    coverage = calculate_coverage(classified)

    # Step 4: Template comparison
    template_comparison = compare_with_template(classified, template)

    # Step 5: Generate recommendations
    recommendations = generate_recommendations(classified, coverage)

    return ScopeAnalysis(
        items=classified,
        coverage=round(coverage, 4),
        recommendations=recommendations,
        templateComparison=template_comparison,
    )
