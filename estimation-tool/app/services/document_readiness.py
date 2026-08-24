"""Document Readiness Assessment Service.

Checks uploaded BRD/PRD documents against admin-configured document templates
to produce a completeness percentage. Uses the SLM to identify which expected
sections are present or missing in the document text.

This module provides:
- Default BRD and PRD template definitions (expected sections with weights)
- assess_document_readiness() function for scoring documents
- DocumentReadinessResult model for structured output
"""

import json
import logging
from typing import Optional

from pydantic import BaseModel, Field

from app.models.schemas import SLMOptions
from app.services.slm_engine import SLMEngine

logger = logging.getLogger(__name__)


# --- Document Template Definitions ---

DEFAULT_PRD_TEMPLATE = {
    "name": "Standard PRD Template",
    "sections": [
        {"name": "Product Objective", "required": True, "weight": 10},
        {"name": "Problem Definition", "required": True, "weight": 10},
        {"name": "User Personas", "required": True, "weight": 8},
        {"name": "Functional Requirements", "required": True, "weight": 15},
        {"name": "Non-Functional Requirements", "required": True, "weight": 10},
        {"name": "Edge Cases / Exception Handling", "required": True, "weight": 10},
        {"name": "System Interactions / Architecture", "required": True, "weight": 10},
        {"name": "API Specifications", "required": False, "weight": 8},
        {"name": "UI/UX Changes", "required": False, "weight": 7},
        {"name": "Dependencies", "required": True, "weight": 7},
        {"name": "Success Criteria / KPIs", "required": False, "weight": 5},
    ],
}

DEFAULT_BRD_TEMPLATE = {
    "name": "Standard BRD Template",
    "sections": [
        {"name": "Executive Summary", "required": True, "weight": 10},
        {"name": "Business Objectives", "required": True, "weight": 15},
        {"name": "Problem Statement", "required": True, "weight": 10},
        {"name": "Scope (In/Out)", "required": True, "weight": 12},
        {"name": "Functional Requirements / User Journeys", "required": True, "weight": 15},
        {"name": "Success Metrics / KPIs", "required": True, "weight": 10},
        {"name": "Assumptions", "required": True, "weight": 8},
        {"name": "Timeline", "required": False, "weight": 8},
        {"name": "Dependencies", "required": False, "weight": 7},
        {"name": "Open Questions", "required": False, "weight": 5},
    ],
}


# --- Result Model ---


class SectionStatus(BaseModel):
    """Status of a single section in the document."""
    name: str = Field(..., description="Section name from template")
    status: str = Field(..., description="One of: filled, placeholder, insufficient, missing")
    issues: list[str] = Field(default_factory=list, description="Specific problems found")


class FeatureAssessment(BaseModel):
    """Assessment of a single feature/use case for completeness."""
    uc_id: str = Field(default="", description="Use case ID")
    feature: str = Field(..., description="Feature name")
    ac_quality: str = Field(..., description="good, weak, or missing")
    ac_issues: list[str] = Field(default_factory=list, description="What's wrong with the AC")
    has_error_handling: bool = Field(default=False, description="Whether error/failure cases are defined")
    has_ui_reference: bool = Field(default=False, description="Whether UI/design artifacts are referenced")
    channels: list[str] = Field(default_factory=list, description="Channels mentioned (Web, App, etc.)")


class FeatureCompletenessResult(BaseModel):
    """Result of feature-level completeness assessment."""
    total_features: int = Field(default=0)
    testable_features: int = Field(default=0)
    weak_ac_features: int = Field(default=0)
    missing_ac_features: int = Field(default=0)
    features_without_error_handling: int = Field(default=0)
    features_without_ui_reference: int = Field(default=0)
    implied_screen_count: int = Field(default=0, description="Estimated screen count from channels")
    testability_score: float = Field(default=0.0, description="0-100 score")
    assessments: list[FeatureAssessment] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class DocumentReadinessResult(BaseModel):
    """Result of assessing document readiness against a template."""

    docType: str = Field(..., description="Document type: 'brd' or 'prd'")
    readinessPercent: float = Field(..., ge=0, le=100, description="Completeness percentage 0-100")
    sections: list[SectionStatus] = Field(default_factory=list, description="Per-section status details")
    presentSections: list[str] = Field(default_factory=list, description="Sections found in document")
    missingSections: list[str] = Field(default_factory=list, description="Sections not found in document")
    placeholderSections: list[str] = Field(default_factory=list, description="Sections with placeholder content")
    recommendations: list[str] = Field(default_factory=list, description="Suggestions for improving the document")
    featureCompleteness: Optional[FeatureCompletenessResult] = Field(None, description="Feature-level completeness (PRD only)")


# --- Assessment Function ---


def _get_template(doc_type: str) -> dict:
    """Get the template definition for the given document type.

    Priority order:
    1. Admin-configured JSON (config/doc_templates.json) — curated, always correct
    2. Uploaded template sections (config/templates/{doc_type}_sections.json) — fallback
    3. Hardcoded defaults

    Args:
        doc_type: Either 'brd', 'prd', or 'hld'.

    Returns:
        Template dictionary with name and sections.
    """
    import os

    # Priority 1: Admin-configured JSON (curated sections)
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config",
        "doc_templates.json",
    )

    try:
        with open(config_path, "r") as f:
            templates = json.load(f)
        if doc_type.lower() in templates:
            return templates[doc_type.lower()]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load doc_templates.json: {e}. Trying uploaded template.")

    # Priority 2: Check for uploaded template
    templates_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config",
        "templates",
    )
    uploaded_path = os.path.join(templates_dir, f"{doc_type.lower()}_sections.json")

    if os.path.exists(uploaded_path):
        try:
            with open(uploaded_path, "r") as f:
                sections_data = json.load(f)
            if sections_data:
                # Convert uploaded template format to internal format,
                # preserving expected content and table columns for the rubric.
                sections = [
                    {
                        "name": s["name"],
                        "required": True,
                        "weight": 10 if s.get("level", 1) == 1 else 7,
                        "expected_content": s.get("expected_content", ""),
                        "table_columns": s.get("table_columns", []),
                    }
                    for s in sections_data
                ]
                return {
                    "name": f"Uploaded {doc_type.upper()} Template",
                    "sections": sections,
                    "from_upload": True,
                }
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not load uploaded template for {doc_type}: {e}")

    # Priority 2: Admin-configured JSON
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config",
        "doc_templates.json",
    )

    try:
        with open(config_path, "r") as f:
            templates = json.load(f)
        if doc_type.lower() in templates:
            return templates[doc_type.lower()]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load doc_templates.json: {e}. Using defaults.")

    # Priority 3: Fallback defaults
    if doc_type.lower() == "prd":
        return DEFAULT_PRD_TEMPLATE
    elif doc_type.lower() == "hld":
        return {"name": "HLD Template", "sections": [
            {"name": "Overview", "required": True, "weight": 10},
            {"name": "Architecture Diagram", "required": True, "weight": 15},
            {"name": "Data Flow", "required": True, "weight": 12},
        ]}
    elif doc_type.lower() == "lld":
        return {"name": "LLD Template", "sections": [
            {"name": "Module/Component Overview", "required": True, "weight": 10},
            {"name": "Class/Sequence Diagrams", "required": True, "weight": 15},
            {"name": "Database Schema / ER Diagram", "required": True, "weight": 12},
            {"name": "API Contracts (Request/Response)", "required": True, "weight": 12},
            {"name": "Error Handling & Edge Cases", "required": True, "weight": 10},
            {"name": "Data Validation Rules", "required": True, "weight": 8},
            {"name": "Caching Strategy", "required": False, "weight": 6},
            {"name": "Security Considerations", "required": True, "weight": 8},
            {"name": "Unit Test Plan", "required": False, "weight": 7},
            {"name": "Dependencies & Libraries", "required": True, "weight": 7},
            {"name": "Configuration & Environment Variables", "required": False, "weight": 5},
        ]}
    return DEFAULT_BRD_TEMPLATE


def _build_readiness_prompt(doc_text: str, doc_type: str, template: dict) -> str:
    """Build the SLM prompt for document readiness assessment.

    Args:
        doc_text: The full document text content.
        doc_type: 'brd' or 'prd'.
        template: The template definition with expected sections.

    Returns:
        Formatted prompt string.
    """
    section_list = "\n".join(
        f"  - {s['name']} (Required: {s['required']}, Weight: {s['weight']})"
        for s in template["sections"]
    )

    max_doc_chars = 12000
    truncated_text = doc_text[:max_doc_chars]

    prompt = f"""You are a STRICT document quality assessor for enterprise engineering documents. Analyze the following {doc_type.upper()} document and determine which expected template sections are ACTUALLY present with proper content.

EXPECTED SECTIONS for a {template['name']}:
{section_list}

DOCUMENT CONTENT:
{truncated_text}

STRICT ASSESSMENT RULES:
1. A section is "present" ONLY if the document contains DEDICATED, SUBSTANTIVE content specifically addressing that topic. A brief mention or passing reference does NOT count.
2. A section is "missing" if:
   - There is no content addressing that topic at all
   - The topic is only mentioned in passing (1-2 sentences) without proper detail
   - The content exists but in a completely different context/meaning
   - The section requires a specific FORMAT (table, diagram, list) and it's not in that format
3. Be STRICT about metadata sections: "Document Metadata", "MP/CP", "Dependencies tables", "Platform Capability Check tables" — these need explicit structured content, not just mentions.
4. Do NOT conflate similar-sounding sections. For example:
   - "System Architecture (High-Level)" is NOT the same as "System Interaction Overview" (which requires a table of system interactions)
   - "Edge Cases" as a simple list is NOT the same as "Edge Cases and Exception Handling" with a structured UC# table
   - "Non-Functional Requirements" as a few bullet points is NOT the same as the full NFR section with Scale/Performance/Reliability/Security subsections with target metrics
5. "Release Scope / Rollout Plan" requires explicit phased release plan, not just a product roadmap mention.
6. "Success Criteria" requires quantifiable metrics with target values, not just feature descriptions.
7. "Dependencies" requires a table of upstream/downstream services with PO alignment and budget info.
8. Provide 2-4 actionable recommendations for improving the document.

Respond with ONLY valid JSON in this exact format:
{{
  "presentSections": ["Section Name 1", "Section Name 2"],
  "missingSections": ["Section Name 3", "Section Name 4"],
  "recommendations": ["Add a dedicated section for...", "Expand the existing..."]
}}

Use the EXACT section names from the expected sections list above. Every section must appear in either presentSections or missingSections.
When in doubt, mark as MISSING. Be strict — it's better to flag a gap than to miss one.
Respond ONLY with valid JSON, no additional text.
"""
    return prompt


def _condense_document(doc_text: str, budget_chars: int = 11000) -> str:
    """Condense a long document so the FULL structure fits within budget.

    Instead of naive truncation (which drops tail sections entirely), this
    splits the document into heading-delimited chunks and allocates the char
    budget proportionally — keeping EVERY section's heading plus a snippet of
    its content. This ensures sections at the end of the document (Dependencies,
    Release Plan, Success Criteria, Glossary, etc.) are still seen by the model.

    Args:
        doc_text: Full extracted document text.
        budget_chars: Max characters to produce.

    Returns:
        Condensed text preserving all section headings.
    """
    if len(doc_text) <= budget_chars:
        return doc_text

    import re

    lines = doc_text.split("\n")

    # Identify heading-like lines to use as chunk boundaries.
    # Be STRICT: table rows, list items, and key:value lines must NOT count,
    # otherwise the doc over-segments and each section loses its content budget.
    def _is_heading(line: str) -> bool:
        s = line.strip()
        if not s or len(s) > 80:
            return False
        # Tab characters → it's a table row, not a heading
        if "\t" in s:
            return False
        # Contains a colon with text after → key:value or label line, not a heading
        if re.search(r':\s*\S', s):
            return False
        # Ends with sentence punctuation → prose, not a heading
        if s.endswith(('.', ',', ';')):
            return False
        # Numbered headings: "1.", "1.1", "12.4 Security" — strongest signal
        if re.match(r'^\d+(\.\d+)*\.?\s+[A-Za-z]', s):
            return True
        # Pure ALL-CAPS section titles (e.g., "FUNCTIONAL REQUIREMENTS")
        if s.isupper() and 6 <= len(s) <= 50 and len(s.split()) <= 6:
            return True
        return False

    # Group lines into chunks by heading boundaries
    chunks: list[list[str]] = []
    current_chunk: list[str] = []
    for line in lines:
        if _is_heading(line) and current_chunk:
            chunks.append(current_chunk)
            current_chunk = [line]
        else:
            current_chunk.append(line)
    if current_chunk:
        chunks.append(current_chunk)

    if not chunks:
        return doc_text[:budget_chars]

    # Reserve space for separators between chunks
    separator_overhead = len(chunks) * 4
    usable_budget = max(budget_chars - separator_overhead, len(chunks) * 120)

    # Allocate budget per chunk so the TOTAL stays within budget (tail sections
    # must survive). Guarantee a minimum so each heading + snippet is kept.
    per_chunk = max(120, usable_budget // len(chunks))

    condensed_parts: list[str] = []
    for chunk in chunks:
        chunk_text = "\n".join(chunk).strip()
        if len(chunk_text) <= per_chunk:
            condensed_parts.append(chunk_text)
        else:
            # Keep the heading (first line) + as much content as the budget allows
            head = chunk[0].strip()
            body = "\n".join(chunk[1:])
            remaining = per_chunk - len(head) - 6
            if remaining > 20:
                snippet = body[:remaining]
                condensed_parts.append(f"{head}\n{snippet} [...]")
            else:
                condensed_parts.append(head)

    result = "\n\n".join(condensed_parts)
    return result


def _parse_readiness_response(content: str, template: dict) -> Optional[dict]:
    """Parse the SLM response for readiness assessment.

    Args:
        content: Raw SLM response text.
        template: Template definition for validation.

    Returns:
        Parsed dictionary if successful, None otherwise.
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

        if "presentSections" not in data or "missingSections" not in data:
            return None

        return data

    except (json.JSONDecodeError, KeyError, ValueError, IndexError) as exc:
        logger.warning(f"Failed to parse readiness response: {exc}")
        return None


def _calculate_readiness_percent(present_sections: list[str], template: dict) -> float:
    """Calculate readiness percentage based on weighted sections.

    Uses fuzzy matching — a section is considered present if either:
    - The template section name appears in any present section (substring)
    - Any present section appears in the template section name (substring)
    - The first significant words match (ignoring parenthetical descriptions)

    Args:
        present_sections: List of section names identified as present.
        template: Template with section definitions and weights.

    Returns:
        Readiness percentage (0-100).
    """
    import re

    total_weight = sum(s["weight"] for s in template["sections"])
    if total_weight == 0:
        return 0.0

    present_lower = [s.lower().strip() for s in present_sections]

    def _matches(template_name: str) -> bool:
        tmpl = template_name.lower().strip()
        # Strip parenthetical descriptions for matching
        tmpl_base = re.sub(r"\s*\(.*?\)", "", tmpl).strip()

        for present in present_lower:
            present_base = re.sub(r"\s*\(.*?\)", "", present).strip()
            # Exact match
            if tmpl == present:
                return True
            # Base name match (without parenthetical)
            if tmpl_base == present_base:
                return True
            # Substring match (either direction)
            if tmpl_base in present or present_base in tmpl:
                return True
            # First 3 words match
            tmpl_words = tmpl_base.split()[:3]
            present_words = present_base.split()[:3]
            if tmpl_words and tmpl_words == present_words:
                return True
        return False

    present_weight = 0.0
    for section in template["sections"]:
        if _matches(section["name"]):
            present_weight += section["weight"]

    return round((present_weight / total_weight) * 100, 1)


def _check_section_in_doc(section_name: str, doc_text: str) -> dict:
    """Check quality of a section's content within the document text.

    Searches for the section heading in the document and analyzes
    the content that follows it for placeholder patterns.

    Args:
        section_name: Name of the section to find.
        doc_text: Full document text.

    Returns:
        dict with 'status' and 'issues' keys.
    """
    import re
    from app.routers.prd_checker import PLACEHOLDER_PATTERNS

    # Try to find the section in the document text
    # Use a simplified version of the section name for matching
    base_name = re.sub(r'\s*\(.*?\)', '', section_name).strip()
    pattern = re.escape(base_name[:40])  # Use first 40 chars to avoid over-matching

    match = re.search(pattern, doc_text, re.IGNORECASE)
    if not match:
        # Section was reported present by SLM but we can't locate it exactly
        # Trust the SLM and mark as filled
        return {"status": "filled", "issues": []}

    # Extract text after the heading (up to next heading or 2000 chars)
    start_pos = match.end()
    # Look for the next section-like boundary
    next_heading = re.search(
        r'\n(?=[A-Z0-9][\w\s]{2,50}(?:\n|$))',
        doc_text[start_pos:start_pos + 2000]
    )
    if next_heading:
        section_text = doc_text[start_pos:start_pos + next_heading.start()]
    else:
        section_text = doc_text[start_pos:start_pos + 2000]

    # Check for quality issues
    if not section_text.strip():
        return {"status": "missing", "issues": ["Section heading found but no content follows"]}

    issues = []
    for p in PLACEHOLDER_PATTERNS:
        matches = re.findall(p, section_text, re.IGNORECASE)
        if matches:
            issues.append(f"Contains placeholder: {matches[0]}")

    if len(section_text.strip()) < 20:
        issues.append("Insufficient detail (less than 20 characters)")

    if issues and any('placeholder' in i.lower() for i in issues):
        return {"status": "placeholder", "issues": issues}
    elif issues:
        return {"status": "insufficient", "issues": issues}

    return {"status": "filled", "issues": []}


def _build_section_eval_prompt(
    doc_text: str,
    doc_type: str,
    template: dict,
    sections_subset: Optional[list] = None,
    doc_budget_chars: int = 24000,
) -> str:
    """Build a section-by-section evaluation prompt.

    For each template section (or a subset/batch), includes its name and what
    content the template expects (guidance text + table columns). The LLM
    evaluates the submitted document against EACH section and returns a verdict.

    Args:
        doc_text: Full document text.
        doc_type: 'prd', 'brd', 'hld', 'lld'.
        template: Template definition.
        sections_subset: If provided, only evaluate these sections (a batch).
            Otherwise evaluates all template sections.
        doc_budget_chars: Char budget for the document portion of the prompt.
    """
    sections_to_eval = sections_subset if sections_subset is not None else template["sections"]

    section_blocks = []
    for i, s in enumerate(sections_to_eval, 1):
        expected = s.get("expected_content", "").strip()
        cols = s.get("table_columns", [])
        rubric_parts = []
        if expected:
            rubric_parts.append(f"this section should cover: {expected[:200]}")
        if cols:
            rubric_parts.append(f"it usually contains a table with columns like: {', '.join(cols)}")
        rubric = "; ".join(rubric_parts) if rubric_parts else "judge whether the document contains real content for this topic."
        section_blocks.append(f"{i}. \"{s['name']}\" ({rubric})")

    sections_text = "\n".join(section_blocks)

    doc_for_prompt = _condense_document(doc_text, budget_chars=doc_budget_chars)

    prompt = f"""You are a fair but rigorous enterprise document reviewer. Below is a list of TEMPLATE SECTIONS a {doc_type.upper()} should contain, and a submitted document. Evaluate the document against ONLY the sections listed.

TEMPLATE SECTIONS TO EVALUATE:
{sections_text}

SUBMITTED DOCUMENT:
\"\"\"
{doc_for_prompt}
\"\"\"

For EACH numbered section, decide a status based STRICTLY on the SUBMITTED DOCUMENT content above (never on the section descriptions themselves):
- "filled": The document genuinely covers this topic with real, specific content. If a table is expected and the document provides a populated table (rows with real values, not just "—" empty markers), that counts as filled.
- "insufficient": The topic is addressed but thin — only 1-2 generic sentences, or major expected detail absent.
- "placeholder": A table or section EXISTS in the document but its values are placeholders/blanks — TBD, TBC, <Name>, XX, "to be decided", or cells shown as "—". This is DIFFERENT from missing: the structure is there, just not filled in.
- "missing": The topic is genuinely absent from the document entirely.

CRITICAL RULES:
- Judge ONLY by what appears in the SUBMITTED DOCUMENT between the triple quotes. NEVER treat the section descriptions/purpose text as if it were document content.
- A table whose cells contain real values = "filled". A table whose cells are mostly "—" or TBD = "placeholder". No such table or topic anywhere = "missing".
- If a heading for the topic exists and has ANY real content below it, it is NOT "missing" — choose filled / insufficient / placeholder instead.
- Tables are shown in Markdown (| col | col |). Read their cell values to judge filled vs placeholder.
- Column names and "Ex -" example values in section descriptions are ILLUSTRATIONS — do not require the document to contain those exact examples.

Respond with ONLY a valid JSON array, one object per section IN ORDER. Use the EXACT section name (no leading number):
[
  {{"section": "<section name>", "status": "filled|insufficient|placeholder|missing", "issue": "<one short sentence on the gap, or empty string if filled>"}}
]
Do NOT add extra objects beyond the {len(sections_to_eval)} sections listed. Respond ONLY with the JSON array.
"""
    return prompt


def _parse_section_eval_response(content: str, template: dict) -> Optional[list[dict]]:
    """Parse the section-by-section evaluation JSON array response."""
    try:
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()

        start = json_str.find("[")
        end = json_str.rfind("]") + 1
        if start >= 0 and end > start:
            json_str = json_str[start:end]

        data = json.loads(json_str)
        if not isinstance(data, list):
            return None
        return data
    except (json.JSONDecodeError, ValueError, IndexError) as exc:
        logger.warning(f"Failed to parse section eval response: {exc}")
        return None


def _normalize_section_name(s: str) -> str:
    """Normalize a section name for matching (strip numbering, prefixes, quotes)."""
    import re as _re
    s = str(s).strip().lower()
    s = s.replace("section:", "")
    s = _re.sub(r'^\d+\.\s*', '', s)  # leading "1. "
    s = s.strip().strip('"').strip("'").strip()
    return s


async def _evaluate_section_batch(
    doc_text: str,
    doc_type: str,
    template: dict,
    batch: list,
    slm_engine: SLMEngine,
) -> dict:
    """Evaluate one batch of template sections against the document.

    Returns a dict mapping normalized section name -> verdict item.
    """
    prompt = _build_section_eval_prompt(
        doc_text, doc_type, template, sections_subset=batch
    )
    options = SLMOptions(temperature=0.1, maxTokens=2048)

    try:
        response = await slm_engine.inference(prompt, options=options)
        parsed = _parse_section_eval_response(response.content, template)
    except Exception as exc:
        logger.warning(f"Batch evaluation failed ({len(batch)} sections): {exc}")
        parsed = None

    verdicts: dict = {}
    if parsed:
        for i, item in enumerate(parsed):
            if not isinstance(item, dict):
                continue
            # Prefer the name the model returned; fall back to positional batch name
            name = item.get("section")
            if name:
                verdicts[_normalize_section_name(name)] = item
            if i < len(batch):
                # Also index by the batch section name positionally as a safety net
                verdicts.setdefault(_normalize_section_name(batch[i]["name"]), item)
    return verdicts


async def assess_document_readiness(
    doc_text: str, doc_type: str, slm_engine: SLMEngine
) -> DocumentReadinessResult:
    """Assess document readiness via batched section-by-section evaluation.

    Splits the template's sections into small batches and evaluates each batch
    against the full document in parallel. This avoids output-token truncation
    (which dropped tail-section verdicts) and works for templates of any size.
    Verdicts are stitched together and the score computed directly from them.

    Args:
        doc_text: The full text content of the document.
        doc_type: Document type - 'brd', 'prd', 'hld', or 'lld'.
        slm_engine: The SLM engine instance for inference.

    Returns:
        DocumentReadinessResult with percentage, per-section status, and recommendations.
    """
    template = _get_template(doc_type)
    tmpl_sections = template["sections"]

    # Split sections into batches to keep each LLM response small & complete.
    BATCH_SIZE = 8
    batches = [
        tmpl_sections[i:i + BATCH_SIZE]
        for i in range(0, len(tmpl_sections), BATCH_SIZE)
    ]

    # Evaluate batches. Local Ollama serves one model serially, so run batches
    # sequentially to avoid request contention; cloud models could parallelize.
    batch_results = []
    for batch in batches:
        try:
            result = await _evaluate_section_batch(
                doc_text, doc_type, template, batch, slm_engine
            )
            batch_results.append(result)
        except Exception as exc:
            logger.warning(f"Batch evaluation failed for {doc_type}: {exc}")
            batch_results.append({})

    # Merge all batch verdicts
    verdict_by_name: dict = {}
    for result in batch_results:
        verdict_by_name.update(result)

    # If we got nothing at all, return a graceful fallback
    if not verdict_by_name:
        all_sections = [s["name"] for s in tmpl_sections]
        return DocumentReadinessResult(
            docType=doc_type,
            readinessPercent=0.0,
            sections=[SectionStatus(name=s, status="missing", issues=["Could not assess"]) for s in all_sections],
            presentSections=[],
            missingSections=all_sections,
            placeholderSections=[],
            recommendations=[
                f"Could not assess {doc_type.upper()} readiness. Please retry or ensure the document has readable content."
            ],
        )

    section_statuses: list[SectionStatus] = []
    present_sections: list[str] = []
    missing_sections: list[str] = []
    placeholder_sections: list[str] = []

    valid_statuses = {"filled", "insufficient", "placeholder", "missing"}

    for tmpl_section in tmpl_sections:
        name = tmpl_section["name"]
        item = verdict_by_name.get(_normalize_section_name(name))

        status = "missing"
        issue = "Section not found in document"
        if item:
            raw_status = str(item.get("status", "missing")).strip().lower()
            status = raw_status if raw_status in valid_statuses else "missing"
            issue = str(item.get("issue", "")).strip()

        issues = [issue] if issue else []
        section_statuses.append(SectionStatus(name=name, status=status, issues=issues))

        if status == "filled":
            present_sections.append(name)
        elif status == "placeholder":
            placeholder_sections.append(name)
            present_sections.append(name)
        elif status == "missing":
            missing_sections.append(name)

    # Score directly from verdicts
    total_weight = sum(s["weight"] for s in tmpl_sections)
    achieved_weight = 0.0
    for tmpl_section, status_obj in zip(tmpl_sections, section_statuses):
        if status_obj.status == "filled":
            achieved_weight += tmpl_section["weight"]
        elif status_obj.status == "insufficient":
            achieved_weight += tmpl_section["weight"] * 0.5
        elif status_obj.status == "placeholder":
            achieved_weight += tmpl_section["weight"] * 0.3

    readiness_percent = round((achieved_weight / total_weight) * 100, 1) if total_weight > 0 else 0.0

    recommendations = _build_recommendations(section_statuses, tmpl_sections)

    # Feature completeness evaluation (PRD only)
    feature_completeness = None
    if doc_type == "prd":
        try:
            feature_completeness = await assess_feature_completeness(doc_text, slm_engine)
            # Add feature-level recommendations to main recommendations
            if feature_completeness and feature_completeness.recommendations:
                recommendations.extend(feature_completeness.recommendations[:3])
        except Exception as e:
            logger.warning(f"Feature completeness evaluation failed: {e}")

    return DocumentReadinessResult(
        docType=doc_type,
        readinessPercent=readiness_percent,
        sections=section_statuses,
        presentSections=present_sections,
        missingSections=missing_sections,
        placeholderSections=placeholder_sections,
        recommendations=recommendations,
        featureCompleteness=feature_completeness,
    )


def _build_recommendations(
    section_statuses: list, tmpl_sections: list
) -> list[str]:
    """Generate actionable recommendations from the section verdicts.

    Prioritizes the highest-weight missing/insufficient sections.
    """
    weight_by_name = {s["name"]: s["weight"] for s in tmpl_sections}

    gaps = []
    for st in section_statuses:
        if st.status in ("missing", "insufficient", "placeholder"):
            gaps.append((weight_by_name.get(st.name, 5), st))

    # Sort by weight descending (most important gaps first)
    gaps.sort(key=lambda x: x[0], reverse=True)

    recs = []
    for _, st in gaps[:5]:
        if st.status == "missing":
            recs.append(f"Add the missing section: '{st.name}'.")
        elif st.status == "placeholder":
            detail = st.issues[0] if st.issues else "contains placeholders/blanks"
            recs.append(f"Complete '{st.name}' — {detail}.")
        elif st.status == "insufficient":
            detail = st.issues[0] if st.issues else "needs more detail/structure"
            recs.append(f"Expand '{st.name}' — {detail}.")

    if not recs:
        recs.append("Document covers all template sections well. Ready for estimation.")

    return recs


# =============================================================================
# FEATURE COMPLETENESS EVALUATION (PRD only)
# =============================================================================

FEATURE_EVAL_PROMPT = """You are a QA engineering expert evaluating a PRD's functional requirements for testability and completeness.

Analyze the following functional requirements section from a PRD. For each use case/feature, assess:
1. Can a QA engineer write test cases from the acceptance criteria? (good/weak/missing)
2. Are error/failure scenarios covered?
3. Are UI channels (Web/App) mentioned?

Respond in JSON format:
```json
{
  "features": [
    {
      "uc_id": "1",
      "feature": "OTP Login",
      "ac_quality": "weak",
      "ac_issues": ["No error case for wrong OTP", "No rate limiting mentioned", "No session timeout defined"],
      "has_error_handling": false,
      "channels": ["Web", "App"]
    }
  ],
  "ui_design_referenced": false,
  "overall_issues": ["Most ACs are one-liners without failure scenarios", "No wireframe/mockup references"]
}
```

Rules:
- ac_quality: "good" = QA can write 3+ test cases directly. "weak" = AC is vague/one-liner. "missing" = no AC at all.
- has_error_handling: true only if failure/error/edge case is explicitly mentioned for that feature
- channels: extract from the Channel column or description
- Be strict: "Login successful" alone is WEAK. Good AC = specific, measurable, testable.
- IMPORTANT: Always provide at least one issue in ac_issues, even for "missing" — explain WHY it's missing or what's needed (e.g., "No testable acceptance criteria defined", "AC is just a description, not testable conditions")

FUNCTIONAL REQUIREMENTS SECTION:
---
{content}
---

Return ONLY the JSON, no explanation."""


async def assess_feature_completeness(
    doc_text: str, slm_engine: SLMEngine
) -> Optional[FeatureCompletenessResult]:
    """Evaluate feature-level completeness of a PRD's functional requirements.

    Extracts use cases, evaluates AC quality for testability, flags missing
    error handling and UI/UX gaps.
    """
    import re

    # Extract the functional requirements section
    fr_patterns = [
        # Match "Functional Requirements" heading and everything until next non-FR major section
        r"(?i)(?:\d+\.?\s*)?functional\s+requirements?\s*\n([\s\S]*?)(?=\n\d+\.?\s*(?:edge\s+cases?|out\s+of\s+scope|non[\-\s]?functional|success\s+criteria|dependencies|budget|timeline))",
        # Match everything from first UC# table to last, including multiple tables across sections
        r"(?i)((?:\|[^\n]*UC#[^\n]*\|[\s\S]*?)(?=\n\d+\.?\s*(?:edge\s+cases?|out\s+of\s+scope|non[\-\s]?functional|success\s+criteria|dependencies\b)))",
        # Broader: find all markdown tables that contain UC# anywhere in the doc
        r"(?i)(\|[^\n]*UC#[^\n]*\|[\s\S]*?)(?=\n\d+\.?\s*(?:edge\s+cases?|non[\-\s]?functional|success\s+criteria|$))",
    ]

    fr_content = ""
    for pattern in fr_patterns:
        match = re.search(pattern, doc_text)
        if match:
            fr_content = match.group(0)[:8000]  # Cap to avoid token overflow
            break

    # Fallback: collect ALL markdown pipe-tables that have UC# or Feature/Acceptance columns
    if not fr_content or len(fr_content) < 100:
        lines = doc_text.split('\n')
        table_blocks = []
        in_table = False
        current_block = []
        is_fr_table = False

        for line in lines:
            if line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    current_block = []
                    is_fr_table = False
                current_block.append(line)
                # Check if this table has UC#, Feature, or Acceptance Criteria columns
                if 'UC#' in line or 'Acceptance' in line.lower() or 'Feature' in line:
                    is_fr_table = True
            else:
                if in_table and current_block:
                    if is_fr_table and len(current_block) > 2:
                        table_blocks.append('\n'.join(current_block))
                    in_table = False
                    current_block = []

        # Handle last block
        if in_table and current_block and is_fr_table and len(current_block) > 2:
            table_blocks.append('\n'.join(current_block))

        if table_blocks:
            fr_content = '\n\n'.join(table_blocks)[:8000]

    # Fallback: if regex didn't work, look for UC# patterns anywhere in the doc
    if not fr_content or len(fr_content) < 100:
        uc_lines = [l for l in doc_text.split('\n') if re.match(r'^\s*\d+\s*[\|│]', l) or 'UC#' in l or 'As a ' in l or 'Acceptance' in l.lower()]
        if len(uc_lines) >= 3:
            fr_content = '\n'.join(uc_lines[:50])

    # Last resort: just send the middle chunk of the doc (likely has requirements)
    if not fr_content or len(fr_content) < 100:
        doc_lines = doc_text.split('\n')
        total = len(doc_lines)
        if total > 30:
            # Take the middle 40% of the document (most likely has functional requirements)
            start = int(total * 0.25)
            end = int(total * 0.65)
            fr_content = '\n'.join(doc_lines[start:end])[:8000]

    if not fr_content or len(fr_content) < 50:
        logger.info("No functional requirements content found for feature completeness evaluation")
        return None

    prompt = FEATURE_EVAL_PROMPT.replace("{content}", fr_content)

    try:
        response = await slm_engine.inference(
            prompt,
            SLMOptions(temperature=0.1, maxTokens=3000),
        )
        content = response.content.strip()

        # Parse JSON from response
        json_match = re.search(r"\{[\s\S]*\}", content)
        if not json_match:
            logger.warning("Feature completeness: no JSON found in SLM response")
            return None

        data = json.loads(json_match.group(0))
        features = data.get("features", [])
        ui_referenced = data.get("ui_design_referenced", False)

        assessments = []
        testable = 0
        weak = 0
        missing_ac = 0
        no_error = 0
        no_ui = 0
        all_channels = set()

        for f in features:
            ac_q = f.get("ac_quality", "missing")
            channels = f.get("channels", [])
            all_channels.update(channels)

            assessment = FeatureAssessment(
                uc_id=str(f.get("uc_id", "")),
                feature=f.get("feature", "Unknown"),
                ac_quality=ac_q,
                ac_issues=f.get("ac_issues", []),
                has_error_handling=f.get("has_error_handling", False),
                has_ui_reference=ui_referenced,
                channels=channels,
            )
            assessments.append(assessment)

            if ac_q == "good":
                testable += 1
            elif ac_q == "weak":
                weak += 1
            else:
                missing_ac += 1

            if not f.get("has_error_handling", False):
                no_error += 1
            if channels and not ui_referenced:
                no_ui += 1

        total = len(assessments)
        testability_score = round((testable / total) * 100, 1) if total > 0 else 0.0

        # Estimate implied screen count: unique channels × features with UI
        platform_count = len([c for c in all_channels if c.lower() in ("web", "app", "mobile", "android", "ios")])
        implied_screens = max(total * platform_count, 0)

        # Build recommendations
        recs = []
        if weak > 0:
            recs.append(f"{weak} features have weak acceptance criteria — QA cannot write comprehensive tests. Add specific, measurable ACs with success AND failure conditions.")
        if no_error > total * 0.5:
            recs.append(f"{no_error}/{total} features lack error/failure handling — add what happens when things go wrong (timeouts, invalid input, network failure).")
        if no_ui > 0 and not ui_referenced:
            recs.append(f"{no_ui} features target Web/App but no UI/UX design artifacts are referenced — add wireframes or Figma links.")
        if implied_screens > 20:
            recs.append(f"Estimated {implied_screens}+ screens implied across {platform_count} platforms — add a screen inventory per platform.")
        if missing_ac > 0:
            recs.append(f"{missing_ac} features have no acceptance criteria at all.")
        overall_issues = data.get("overall_issues", [])
        recs.extend(overall_issues[:3])

        return FeatureCompletenessResult(
            total_features=total,
            testable_features=testable,
            weak_ac_features=weak,
            missing_ac_features=missing_ac,
            features_without_error_handling=no_error,
            features_without_ui_reference=no_ui,
            implied_screen_count=implied_screens,
            testability_score=testability_score,
            assessments=assessments,
            recommendations=recs,
        )

    except Exception as e:
        logger.warning(f"Feature completeness evaluation failed: {e}")
        return None
