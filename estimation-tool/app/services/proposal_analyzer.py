"""SLM-powered vendor proposal analysis for Build vs Buy evaluations.

Extracts structured data from vendor proposals using the SLM engine and
suggests dimension scores for evaluation.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from app.services.document_processor import extract_text_markdown
from app.services.slm_engine import SLMEngine, SLMOptions

logger = logging.getLogger(__name__)


@dataclass
class ProposalExtractionResult:
    """Result of SLM-powered vendor proposal analysis."""

    proposed_costs: dict[str, float] = field(default_factory=dict)
    timeline_months: Optional[int] = None
    team_size: Optional[int] = None
    technology_stack: list[str] = field(default_factory=list)
    support_model: Optional[str] = None
    sla_commitments: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    suggested_scores: dict[str, int] = field(default_factory=dict)
    confidence: float = 0.0
    error: Optional[str] = None


ANALYSIS_PROMPT_TEMPLATE = """You are analyzing a vendor proposal for a Build vs Buy evaluation.
Extract the following structured data from the document:

1. Proposed cost breakdown (license, implementation, support, etc.) as key-value pairs with numeric amounts
2. Implementation timeline in months
3. Team size (number of people proposed)
4. Technology stack (list of technologies mentioned)
5. Support model description
6. SLA commitments (list of specific SLA terms)
7. Risk indicators: look for vendor lock-in, hidden costs, unclear SLA terms, deprecation risks

Additionally, suggest scores (1-5) for these evaluation dimensions:
- technology_fit: How well does the proposed technology align with requirements? (1=poor, 5=excellent)
- functional_fit: How well does it meet functional requirements? (1=poor, 5=excellent)
- operational_sustainability: How maintainable is the solution long-term? (1=poor, 5=excellent)
- vendor_risk: Rate the vendor risk level (1=highest risk, 5=lowest risk)
- ai_readiness: How AI-ready is the proposed solution? (1=not ready, 5=fully ready)

Respond ONLY with valid JSON in this exact format (no markdown, no explanation):
{{
  "proposed_costs": {{"license": 0.0, "implementation": 0.0, "support": 0.0}},
  "timeline_months": null,
  "team_size": null,
  "technology_stack": [],
  "support_model": null,
  "sla_commitments": [],
  "risk_flags": [],
  "suggested_scores": {{
    "technology_fit": 3,
    "functional_fit": 3,
    "operational_sustainability": 3,
    "vendor_risk": 3,
    "ai_readiness": 3
  }},
  "confidence": 0.5
}}

Document content:
{document_text}
"""


async def analyze_proposal(
    file_content: bytes,
    filename: str,
    slm_engine: SLMEngine,
) -> ProposalExtractionResult:
    """Extract data and suggest scores from a vendor proposal document.

    Supports PDF, DOCX, and MD formats. Uses the SLM engine to parse and
    analyze the document content.

    Falls back gracefully if SLM fails (returns empty result with error flag).

    Args:
        file_content: Raw file bytes.
        filename: Original filename (determines format).
        slm_engine: The SLM engine instance for inference.

    Returns:
        ProposalExtractionResult with extracted data and suggested scores.
    """
    # Extract text from document
    try:
        document_text = extract_text_markdown(file_content, filename)
    except ValueError as exc:
        return ProposalExtractionResult(
            error=f"Unsupported file format: {exc}",
        )
    except Exception as exc:
        logger.error(f"Failed to extract text from '{filename}': {exc}")
        return ProposalExtractionResult(
            error=f"Failed to extract text from document: {exc}",
        )

    # Truncate to max 15000 characters to stay within context window
    if len(document_text) > 15000:
        document_text = document_text[:15000]

    # Build prompt
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(document_text=document_text)

    # Call SLM
    try:
        response = await slm_engine.inference(
            prompt,
            options=SLMOptions(temperature=0.1, maxTokens=2048),
        )
    except Exception as exc:
        logger.error(f"SLM inference failed for proposal '{filename}': {exc}")
        return ProposalExtractionResult(
            error=f"SLM analysis failed: {exc}",
        )

    # Parse JSON response
    try:
        content = response.content.strip()
        # Try to extract JSON from the response (handle potential markdown wrapping)
        if content.startswith("```"):
            # Strip markdown code block
            lines = content.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            content = "\n".join(json_lines)

        data = json.loads(content)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning(f"Failed to parse SLM JSON response for '{filename}': {exc}")
        return ProposalExtractionResult(
            error=f"Failed to parse SLM response as JSON: {exc}",
        )

    # Build result from parsed data
    result = ProposalExtractionResult(
        proposed_costs=data.get("proposed_costs", {}),
        timeline_months=data.get("timeline_months"),
        team_size=data.get("team_size"),
        technology_stack=data.get("technology_stack", []),
        support_model=data.get("support_model"),
        sla_commitments=data.get("sla_commitments", []),
        risk_flags=data.get("risk_flags", []),
        suggested_scores=data.get("suggested_scores", {}),
        confidence=data.get("confidence", 0.0),
    )

    # Validate suggested scores are in 1-5 range
    validated_scores: dict[str, int] = {}
    for dimension, score in result.suggested_scores.items():
        try:
            score_int = int(score)
            if 1 <= score_int <= 5:
                validated_scores[dimension] = score_int
            else:
                logger.warning(
                    f"Score {score_int} for '{dimension}' out of range 1-5, skipping"
                )
        except (TypeError, ValueError):
            logger.warning(f"Invalid score value for '{dimension}': {score}, skipping")
    result.suggested_scores = validated_scores

    # Validate confidence is in 0-1 range
    try:
        conf = float(result.confidence)
        result.confidence = max(0.0, min(1.0, conf))
    except (TypeError, ValueError):
        result.confidence = 0.0

    # Ensure proposed_costs values are floats
    validated_costs: dict[str, float] = {}
    for key, value in result.proposed_costs.items():
        try:
            validated_costs[str(key)] = float(value)
        except (TypeError, ValueError):
            pass
    result.proposed_costs = validated_costs

    return result
