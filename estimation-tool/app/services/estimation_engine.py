"""Estimation engine service for the Project Estimation Tool.

Orchestrates the full estimation pipeline:
1. Validates mandatory fields (project name, domain, stream)
2. Loads configuration (Config.xlsx) and templates (Templates.xlsx)
3. Constructs prompts for the SLM with project context
4. Parses structured output (per-discipline effort breakdown)
5. Calls confidence_calculator, scope_analyzer, cost_calculator, timeline_calculator
6. Produces complete EstimationResult

Supports tiered analysis depth:
- Tier 1: High-level estimation from BRD + PRD
- Tier 2: Architectural complexity from +HLD
- Tier 3: Integration effort from +DependentDocs

Requirements: 2.1, 2.2, 2.3, 2.4, 4.1, 4.2, 4.3, 11.3, 12.3
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.models.schemas import (
    BaseTemplate,
    CatalogBreakdown,
    CompositeConfidenceScore,
    ConfidenceFactor,
    ConfidenceFactors,
    CostProjection,
    DisciplineEffort,
    DocumentSet,
    Domain,
    DurationResult,
    EstimationRequest,
    EstimationResult,
    InputTier,
    PhaseEstimation,
    RateCard,
    ScopeAnalysis,
    SLMOptions,
    Stream,
    TeamMember,
)
from app.services.confidence_calculator import (
    calculate_confidence,
    compute_input_completeness_score,
)
from app.services.cost_calculator import calculate_cost, load_rate_card
from app.services.phase_detector import (
    PhaseDetectionResult,
    detect_phases,
    normalize_discipline,
)
from app.services.scope_analyzer import analyze_scope
from app.services.sharepoint_client import SharePointClient, FOLDER_ESTIMATIONS
from app.services.slm_engine import SLMEngine
from app.services.timeline_calculator import (
    calculate_duration,
    infer_team_composition,
)

logger = logging.getLogger(__name__)

# Default SLM parameters
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 4096

# Simple TTL cache for config and templates
_config_cache: dict[str, Any] = {}
_config_cache_time: float = 0
_template_cache: dict[str, Any] = {}
_template_cache_time: float = 0
CONFIG_CACHE_TTL = 3600  # 1 hour


def clear_config_cache() -> None:
    """Clear the in-memory config and template caches. Useful for testing."""
    global _config_cache, _config_cache_time, _template_cache, _template_cache_time
    _config_cache = {}
    _config_cache_time = 0
    _template_cache = {}
    _template_cache_time = 0


class EstimationError(Exception):
    """Base exception for estimation engine errors."""

    pass


class ValidationError(EstimationError):
    """Raised when mandatory fields are missing or invalid."""

    pass


async def validate_request(request: EstimationRequest) -> None:
    """Validate mandatory fields before processing.

    Checks that project name, domain, and stream are present and valid.

    Args:
        request: The estimation request to validate.

    Raises:
        ValidationError: If any mandatory field is missing.

    Requirements: 11.3, 12.3
    """
    errors: list[str] = []

    # Validate project name
    if not request.projectName or not request.projectName.strip():
        errors.append("Project name is mandatory and cannot be empty.")

    # Validate domain
    if not request.domain:
        errors.append("Domain selection is mandatory.")

    # Validate stream
    if not request.stream:
        errors.append("Stream selection is mandatory.")

    if errors:
        raise ValidationError(" ".join(errors))


async def load_config(
    sharepoint_client: SharePointClient,
) -> dict[str, str]:
    """Load SLM parameters and configuration from Config.xlsx.

    Uses an in-memory TTL cache to avoid re-downloading on every estimation.

    Args:
        sharepoint_client: SharePoint client for reading files.

    Returns:
        Dictionary of configuration key-value pairs.
    """
    global _config_cache, _config_cache_time

    now = time.time()
    if _config_cache and (now - _config_cache_time) < CONFIG_CACHE_TTL:
        return _config_cache

    try:
        rows = await sharepoint_client.read_workbook(f"{FOLDER_ESTIMATIONS}/Config.xlsx", sheet="Sheet1")
        config: dict[str, str] = {}
        for row in rows[1:]:  # Skip header
            if len(row) >= 2:
                config[str(row[0]).strip()] = str(row[1]).strip()
        _config_cache = config
        _config_cache_time = now
        return config
    except Exception as exc:
        logger.warning(f"Failed to load Config.xlsx: {exc}. Using defaults.")
        return {}


async def load_base_template(
    sharepoint_client: SharePointClient,
    domain: Domain,
    stream: Stream,
) -> Optional[BaseTemplate]:
    """Load the base template for the given domain/stream combination.

    Uses an in-memory TTL cache to avoid re-downloading on every estimation.

    Args:
        sharepoint_client: SharePoint client for reading Templates.xlsx.
        domain: The selected domain.
        stream: The selected stream.

    Returns:
        BaseTemplate if found, None otherwise.

    Requirements: 16.3
    """
    global _template_cache, _template_cache_time

    now = time.time()
    cache_key = f"{domain.value}:{stream.value}"

    if _template_cache and (now - _template_cache_time) < CONFIG_CACHE_TTL:
        if cache_key in _template_cache:
            return _template_cache[cache_key]

    try:
        rows = await sharepoint_client.read_workbook("Templates.xlsx", sheet="Sheet1")
        if len(rows) < 2:
            return None

        headers = [str(h).strip() for h in rows[0]]

        # Rebuild the entire template cache
        new_cache: dict[str, Any] = {}
        for row in rows[1:]:
            row_dict = dict(zip(headers, row))
            row_domain = str(row_dict.get("Domain", "")).strip()
            row_stream = str(row_dict.get("Stream", "")).strip()
            row_key = f"{row_domain}:{row_stream}"

            scope_areas_raw = row_dict.get("ScopeAreas", "[]")
            try:
                scope_areas = json.loads(scope_areas_raw)
            except (json.JSONDecodeError, TypeError):
                scope_areas = []

            new_cache[row_key] = BaseTemplate(
                templateId=str(row_dict.get("TemplateId", "")),
                domain=Domain(row_domain) if row_domain else domain,
                stream=Stream(row_stream) if row_stream else stream,
                scopeAreas=scope_areas,
                createdBy=str(row_dict.get("CreatedBy", "")),
                createdAt=str(row_dict.get("CreatedAt", "")),
            )

        _template_cache = new_cache
        _template_cache_time = now
        return _template_cache.get(cache_key)

    except Exception as exc:
        logger.warning(f"Failed to load template for {domain}/{stream}: {exc}")
        return None


def _build_estimation_prompt(
    request: EstimationRequest,
    input_tier: InputTier,
    config: dict[str, str],
) -> str:
    """Construct the SLM prompt for effort estimation.

    Includes project metadata, FULL document content, domain/stream context,
    and detailed analysis instructions for thorough estimation.

    Args:
        request: The estimation request with documents and metadata.
        input_tier: The classified input tier.
        config: Configuration parameters.

    Returns:
        Formatted prompt string for SLM inference.

    Requirements: 2.1, 4.1, 4.2, 4.3
    """
    # Build document context — use FULL text (up to 15000 chars per doc for large context models)
    max_chars = 15000
    doc_context = f"=== BRD Content ===\n{request.documents.brd.textContent[:max_chars]}\n\n"
    doc_context += f"=== PRD Content ===\n{request.documents.prd.textContent[:max_chars]}\n\n"

    if request.documents.hld:
        doc_context += f"=== HLD Content ===\n{request.documents.hld.textContent[:max_chars]}\n\n"

    if request.documents.dependentServiceDocs:
        for i, doc in enumerate(request.documents.dependentServiceDocs):
            doc_context += (
                f"=== Dependent Service Doc {i+1} ({doc.filename}) ===\n"
                f"{doc.textContent[:max_chars]}\n\n"
            )

    # Tier-specific instructions
    tier_instructions = _get_tier_instructions(input_tier)

    prompt = f"""You are a senior engineering estimation expert with 15+ years of experience estimating enterprise software projects. 

Analyze the following project documents THOROUGHLY and produce a detailed effort estimation.

Project: {request.projectName}
Description: {request.projectDescription or 'Not provided'}
Domain: {request.domain.value}
Stream: {request.stream.value}
Input Tier: {input_tier} ({tier_instructions})

{doc_context}

ANALYSIS INSTRUCTIONS:
Before estimating, carefully identify and count:
1. Total number of functional requirements / use cases
2. Total number of systems that need integration
3. Total number of UI changes across platforms (web, mobile, admin, etc.)
4. Edge cases and exception handling scenarios
5. Non-functional requirements (performance, security, monitoring)
6. Cross-team dependencies

ESTIMATION GUIDELINES:
- Break down effort by THESE specific disciplines ONLY (use these exact names):
  1. Digital Engineering (backend, frontend, android, iOS, middleware, APIs, web — all software dev)
  2. Data Engineering (data pipelines, BI reports, ETL, data warehouse)
  3. Data Science (ML models, analytics algorithms, recommendation engines)
  4. DevOps (CI/CD pipeline setup, build/deploy automation, monitoring)
  5. QA/Testing (test automation, quality assurance, manual testing, performance testing)
  6. Tech COE (Azure/AWS cloud infra, architecture, security, platform setup)
  7. Product/Design (UX/UI design, product management, user research)
- Use ONLY these discipline names exactly as written: Digital Engineering, Data Engineering, Data Science, DevOps, QA/Testing, Tech COE, Product/Design
- NOT all disciplines are needed for every project — only include those relevant to the scope
- For each discipline, consider: new development, enhancement, integration work, testing, and deployment
- Integration-heavy projects need significant Digital Engineering effort
- Multi-system projects need more testing effort within Digital Engineering
- personMonths = personDays / 22
- Be thorough — underestimation is worse than overestimation
- Consider the FULL scope: every system mentioned, every use case, every edge case

SCORING GUIDELINES:
- documentDetailScore: Rate 0-100 based on: structured sections, clear acceptance criteria, defined edge cases, system interaction details, NFRs present
- requirementClarityScore: Rate 0-100 based on: unambiguous language, specific acceptance criteria, no TBD/pending items, complete API specifications

Produce a JSON response with this EXACT structure:
{{
  "effortBreakdown": [
    {{"discipline": "<name>", "personDays": <number>, "personMonths": <number>}}
  ],
  "infraCost": {{
    "monthlyTotal": <number in INR>,
    "breakdown": [
      {{"service": "<cloud service name>", "monthlyCost": <number in INR>, "reason": "<why needed>"}}
    ]
  }},
  "assumptions": ["<assumption 1>", "<assumption 2>", "<assumption 3>", "<assumption 4>", "<assumption 5>"],
  "documentDetailScore": <0-100>,
  "requirementClarityScore": <0-100>
}}

IMPORTANT:
- Use ONLY these discipline names exactly as written: Digital Engineering, Data Engineering, Data Science, DevOps, QA/Testing, Tech COE, Product/Design
- Not all disciplines are needed — only include those relevant to the project scope
- Estimates should reflect REAL enterprise project complexity (not trivial amounts)
- A project with 10+ integrations typically needs 200+ total person-days minimum
- For infraCost: estimate monthly Azure/AWS cloud costs based on the architecture you infer (compute, databases, messaging, storage, API gateways, monitoring, etc.)
- Use realistic Azure/AWS India region pricing
- List 5+ key assumptions
- documentDetailScore and requirementClarityScore MUST be non-zero positive integers

Respond ONLY with valid JSON, no additional text or explanation.
"""
    return prompt


def _get_tier_instructions(input_tier: InputTier) -> str:
    """Get tier-specific analysis instructions.

    Args:
        input_tier: The input tier level.

    Returns:
        Instruction text for the SLM prompt.

    Requirements: 4.1, 4.2, 4.3
    """
    if input_tier == 1:
        return (
            "High-level estimation. Focus on major functional areas "
            "identified in the PRD. Provide broad estimates per discipline."
        )
    elif input_tier == 2:
        return (
            "Refined estimation with architectural complexity. Account for "
            "system design patterns, component interactions, and technical "
            "complexity described in the HLD."
        )
    else:  # Tier 3
        return (
            "Detailed estimation including integration effort. Account for "
            "each dependent service integration, API contract alignment, "
            "data migration, and cross-service testing needs."
        )


def _parse_estimation_response(content: str) -> Optional[dict[str, Any]]:
    """Parse the SLM structured JSON response.

    Extracts effort breakdown, assumptions, and quality scores from the
    SLM's JSON output.

    Args:
        content: Raw SLM response text.

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

        # Validate required fields
        if "effortBreakdown" not in data:
            return None

        breakdown = data["effortBreakdown"]
        if not isinstance(breakdown, list) or len(breakdown) < 1:
            return None

        # Validate each discipline entry
        for entry in breakdown:
            if "discipline" not in entry or "personDays" not in entry:
                return None
            if not isinstance(entry["personDays"], (int, float)) or entry["personDays"] <= 0:
                return None
            # Auto-calculate personMonths if missing
            if "personMonths" not in entry:
                entry["personMonths"] = entry["personDays"] / 22.0

        return data

    except (json.JSONDecodeError, KeyError, ValueError, IndexError) as exc:
        logger.warning(f"Failed to parse estimation response: {exc}")
        return None


async def _chunked_estimation(
    request: EstimationRequest,
    input_tier: InputTier,
    config: dict[str, str],
    slm_engine: SLMEngine,
) -> Optional[dict[str, Any]]:
    """Run estimation using multiple focused SLM calls (chunked approach).

    Instead of one massive prompt that overwhelms small models, this does:
    1. Scope Analysis: count use cases, systems, integrations
    2. Per-discipline estimation: focused call per relevant discipline
    3. Quality scoring + assumptions

    Returns the same dict format as _parse_estimation_response for compatibility.
    """
    max_chars = 12000
    doc_text = f"{request.documents.brd.textContent[:max_chars]}\n\n{request.documents.prd.textContent[:max_chars]}"
    if request.documents.hld:
        doc_text += f"\n\n{request.documents.hld.textContent[:6000]}"

    slm_options = SLMOptions(
        temperature=float(config.get("slm_temperature", str(DEFAULT_TEMPERATURE))),
        maxTokens=2048,
    )

    # --- STEP 1: Scope Analysis ---
    scope_prompt = f"""Analyze this project document and count the scope elements.

PROJECT: {request.projectName}
DOMAIN: {request.domain.value}

DOCUMENT:
{doc_text[:10000]}

Count and list:
1. Number of functional requirements / user stories
2. Number of systems to integrate with (list them)
3. Number of platforms (web, mobile app, admin, vehicle, etc.)
4. Does this project need data pipelines/ETL/BI? (yes/no)
5. Does this project need ML/AI models? (yes/no)
6. Complexity level: simple (1-3 integrations), medium (4-7), complex (8+)

Respond ONLY with JSON:
{{"use_case_count": <int>, "systems": ["system1", "system2"], "platforms": ["web", "mobile"], "needs_data_engineering": <bool>, "needs_data_science": <bool>, "complexity": "simple|medium|complex"}}
"""

    try:
        resp = await slm_engine.inference(scope_prompt, options=slm_options)
        scope_content = resp.content.strip()
        # Parse scope JSON
        if "```" in scope_content:
            scope_content = scope_content.split("```")[1].split("```")[0]
            if scope_content.startswith("json"):
                scope_content = scope_content[4:]
        start = scope_content.find("{")
        end = scope_content.rfind("}") + 1
        scope_data = json.loads(scope_content[start:end]) if start >= 0 and end > start else {}
    except Exception as e:
        logger.warning(f"Scope analysis failed: {e}")
        scope_data = {"use_case_count": 10, "systems": [], "platforms": ["web"], "needs_data_engineering": False, "needs_data_science": False, "complexity": "medium"}

    uc_count = scope_data.get("use_case_count", 10)
    systems = scope_data.get("systems", [])
    platforms = scope_data.get("platforms", ["web"])
    complexity = scope_data.get("complexity", "medium")
    needs_de = scope_data.get("needs_data_engineering", False)
    needs_ds = scope_data.get("needs_data_science", False)

    logger.info(f"Chunked estimation scope: {uc_count} UCs, {len(systems)} systems, complexity={complexity}")

    # --- STEP 2: Per-discipline estimation ---
    # Calibration ranges based on complexity
    calibration = {
        "simple": {"de_range": "80-200", "qa_ratio": "30-40%", "devops_range": "15-40", "design_range": "20-50"},
        "medium": {"de_range": "150-400", "qa_ratio": "30-40%", "devops_range": "30-70", "design_range": "40-100"},
        "complex": {"de_range": "300-700", "qa_ratio": "30-40%", "devops_range": "50-120", "design_range": "60-150"},
    }
    cal = calibration.get(complexity, calibration["medium"])

    estimation_prompt = f"""You are estimating effort for an enterprise software project.

PROJECT SCOPE (already analyzed):
- {uc_count} functional requirements / user stories
- {len(systems)} systems to integrate: {', '.join(systems[:8])}
- Platforms: {', '.join(platforms)}
- Complexity: {complexity}
- Needs Data Engineering: {needs_de}
- Needs Data Science: {needs_ds}

CALIBRATION GUIDELINES (realistic ranges for {complexity} projects):
- Digital Engineering (all software dev): {cal['de_range']} person-days for this complexity
- QA/Testing: typically {cal['qa_ratio']} of Digital Engineering effort
- DevOps: {cal['devops_range']} person-days
- Product/Design: {cal['design_range']} person-days
- Tech COE (cloud infra): 10-40 person-days (only if new infra setup needed)
- Data Engineering: ONLY if project needs data pipelines/ETL. If not needed, DO NOT include.
- Data Science: ONLY if project needs ML models. If not needed, DO NOT include.

IMPORTANT RULES:
- Stay WITHIN the calibration ranges. Do not exceed the upper bound unless you have a very specific reason.
- SKIP disciplines that aren't relevant. Not every project needs all 7.
- personMonths = personDays / 22

Produce JSON with effort for ONLY the relevant disciplines:
{{"effortBreakdown": [{{"discipline": "<name>", "personDays": <number>, "personMonths": <number>}}], "assumptions": ["assumption 1", "assumption 2", "assumption 3", "assumption 4", "assumption 5"], "documentDetailScore": <0-100>, "requirementClarityScore": <0-100>}}

Respond ONLY with valid JSON.
"""

    try:
        resp = await slm_engine.inference(estimation_prompt, options=slm_options)
        parsed = _parse_estimation_response(resp.content)
        if parsed:
            return parsed
    except Exception as e:
        logger.warning(f"Chunked estimation main call failed: {e}")

    # Fallback: if chunked approach fails, try the old single-shot prompt
    logger.warning("Chunked estimation failed, falling back to single-shot prompt")
    return None


def _build_phase_estimation_prompt(
    request: EstimationRequest,
    input_tier: InputTier,
    config: dict[str, str],
    phase_result: PhaseDetectionResult,
) -> str:
    """Construct the SLM prompt for per-phase effort estimation.

    Includes phase names, use case assignments, and instructions for
    the SLM to produce a separate effortBreakdown per phase using ONLY
    the 7 fixed Discipline names.

    Args:
        request: The estimation request with documents and metadata.
        input_tier: The classified input tier.
        config: Configuration parameters.
        phase_result: Detected phases with use case assignments.

    Returns:
        Formatted prompt string for SLM inference.

    Requirements: 2.1, 2.3, 2.4, 3.3
    """
    # Build document context
    max_chars = 15000
    doc_context = f"=== BRD Content ===\n{request.documents.brd.textContent[:max_chars]}\n\n"
    doc_context += f"=== PRD Content ===\n{request.documents.prd.textContent[:max_chars]}\n\n"

    if request.documents.hld:
        doc_context += f"=== HLD Content ===\n{request.documents.hld.textContent[:max_chars]}\n\n"

    if request.documents.dependentServiceDocs:
        for i, doc in enumerate(request.documents.dependentServiceDocs):
            doc_context += (
                f"=== Dependent Service Doc {i+1} ({doc.filename}) ===\n"
                f"{doc.textContent[:max_chars]}\n\n"
            )

    # Build phase context
    phase_context = "=== DETECTED PHASES ===\n"
    for phase in phase_result.phases:
        phase_context += f"\n### {phase.name}\n"
        if phase.use_cases:
            phase_context += "Assigned use cases / requirements:\n"
            for uc in phase.use_cases:
                phase_context += f"  - {uc}\n"
        else:
            phase_context += "No specific use cases listed (estimate based on document context).\n"

    tier_instructions = _get_tier_instructions(input_tier)

    prompt = f"""You are a senior engineering estimation expert with 15+ years of experience estimating enterprise software projects.

Analyze the following project documents THOROUGHLY and produce a detailed effort estimation broken down BY PHASE.

Project: {request.projectName}
Description: {request.projectDescription or 'Not provided'}
Domain: {request.domain.value}
Stream: {request.stream.value}
Input Tier: {input_tier} ({tier_instructions})

{doc_context}

{phase_context}

ANALYSIS INSTRUCTIONS:
For EACH phase listed above, carefully analyze:
1. The use cases / requirements assigned to that phase
2. The complexity and integration needs of those use cases
3. The team required to deliver that phase
4. The estimated calendar duration for that phase

ESTIMATION GUIDELINES:
- Use ONLY these discipline names exactly as written: Digital Engineering, Data Engineering, Data Science, DevOps, QA/Testing, Tech COE, Product/Design
- NOT all disciplines are needed for every phase — only include those relevant to the phase's scope
- For each discipline in each phase, consider: new development, enhancement, integration work, testing, and deployment
- personMonths = personDays / 22
- Be thorough — underestimation is worse than overestimation
- Provide per-phase timeline (calendar months) and recommended team composition
- Each phase should have its own team composition recommendation

SCORING GUIDELINES:
- documentDetailScore: Rate 0-100 based on: structured sections, clear acceptance criteria, defined edge cases, system interaction details, NFRs present
- requirementClarityScore: Rate 0-100 based on: unambiguous language, specific acceptance criteria, no TBD/pending items, complete API specifications

Produce a JSON response with this EXACT structure:
{{
  "phases": [
    {{
      "phaseName": "<Phase name exactly as listed above>",
      "effortBreakdown": [
        {{"discipline": "<discipline name>", "personDays": <number>, "personMonths": <number>}}
      ],
      "totalPersonDays": <sum of personDays for this phase>,
      "teamComposition": [
        {{"discipline": "<discipline name>", "count": <number of people>}}
      ],
      "calendarDuration": <calendar months for this phase>,
      "assumptions": ["<assumption 1>", "<assumption 2>"]
    }}
  ],
  "documentDetailScore": <0-100>,
  "requirementClarityScore": <0-100>
}}

IMPORTANT:
- Use ONLY these discipline names exactly as written: Digital Engineering, Data Engineering, Data Science, DevOps, QA/Testing, Tech COE, Product/Design
- Produce one entry in the "phases" array for EACH phase listed above
- Not all disciplines are needed in every phase — only include those relevant
- Estimates should reflect REAL enterprise project complexity
- documentDetailScore and requirementClarityScore MUST be non-zero positive integers

Respond ONLY with valid JSON, no additional text or explanation.
"""
    return prompt


def _parse_phase_estimation_response(content: str) -> Optional[dict[str, Any]]:
    """Parse SLM response for phase-wise estimation.

    Expected structure:
    {
        "phases": [
            {
                "phaseName": "Phase 1: ...",
                "effortBreakdown": [{"discipline": "...", "personDays": N, ...}],
                "totalPersonDays": N,
                "teamComposition": [...],
                "calendarDuration": N,
                "assumptions": [...]
            },
            ...
        ],
        "documentDetailScore": 70,
        "requirementClarityScore": 80
    }

    Args:
        content: Raw SLM response text.

    Returns:
        Parsed dictionary if valid, None otherwise.
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

        # Validate required top-level fields
        if "phases" not in data:
            return None

        phases = data["phases"]
        if not isinstance(phases, list) or len(phases) < 1:
            return None

        # Validate each phase entry
        for phase in phases:
            if not isinstance(phase, dict):
                return None
            if "phaseName" not in phase or "effortBreakdown" not in phase:
                return None

            breakdown = phase["effortBreakdown"]
            if not isinstance(breakdown, list) or len(breakdown) < 1:
                return None

            for entry in breakdown:
                if "discipline" not in entry or "personDays" not in entry:
                    return None
                if not isinstance(entry["personDays"], (int, float)) or entry["personDays"] <= 0:
                    return None
                # Auto-calculate personMonths if missing
                if "personMonths" not in entry:
                    entry["personMonths"] = entry["personDays"] / 22.0

            # Auto-calculate totalPersonDays if missing
            if "totalPersonDays" not in phase:
                phase["totalPersonDays"] = sum(e["personDays"] for e in breakdown)

        return data

    except (json.JSONDecodeError, KeyError, ValueError, IndexError) as exc:
        logger.warning(f"Failed to parse phase estimation response: {exc}")
        return None


def _validate_disciplines(effort_breakdown: list[dict]) -> list[DisciplineEffort]:
    """Validate and normalize discipline names in parsed SLM output.

    Maps recognized names to the Discipline enum using normalize_discipline.
    Discards entries with unmappable discipline names (logs warning).
    Merges duplicate disciplines by summing person-days.

    Args:
        effort_breakdown: List of dicts with 'discipline', 'personDays', 'personMonths'.

    Returns:
        List of validated DisciplineEffort objects with canonical discipline names.

    Requirements: 3.2, 3.4
    """
    merged: dict[str, float] = {}

    for entry in effort_breakdown:
        raw_name = entry.get("discipline", "")
        person_days = float(entry.get("personDays", 0))

        if person_days <= 0:
            continue

        discipline = normalize_discipline(raw_name)
        if discipline is None:
            logger.warning(
                f"Discarding unmappable discipline name: '{raw_name}' "
                f"({person_days} person-days)"
            )
            continue

        canonical_name = discipline.value
        if canonical_name in merged:
            merged[canonical_name] += person_days
        else:
            merged[canonical_name] = person_days

    return [
        DisciplineEffort(
            discipline=name,
            personDays=round(days, 2),
            personMonths=round(days / 22.0, 2),
        )
        for name, days in merged.items()
    ]


async def _generate_estimation_catalog(
    request: EstimationRequest,
    input_tier: InputTier,
    slm_engine: SLMEngine,
    sharepoint_client: SharePointClient,
) -> Optional[EstimationResult]:
    """Generate estimation using the catalog-based engine (primary path).

    The SLM only classifies work items from the catalog. The app does all math.
    Returns None if catalog engine fails (caller falls back to legacy).

    Requirements: catalog-based-estimation spec.
    """
    from app.models.schemas import (
        CatalogBreakdown,
        CatalogClassificationResult,
    )
    from app.services.catalog_calculator import CatalogCalculator
    from app.services.catalog_classifier import CatalogClassifier
    from app.services.catalog_loader import get_catalog_loader

    loader = get_catalog_loader()
    catalog = loader.load_catalog()
    deps = loader.load_dependencies()

    # Check if catalog engine is enabled
    if catalog.get("engine") == "legacy":
        logger.info("Catalog engine disabled (engine=legacy). Skipping.")
        return None

    logger.info("Using catalog-based estimation engine.")
    start_time = time.time()

    try:
        # Build full PRD text
        prd_text = ""
        if request.documents.brd:
            prd_text += request.documents.brd.textContent + "\n\n"
        prd_text += request.documents.prd.textContent
        if request.documents.hld:
            prd_text += "\n\n" + request.documents.hld.textContent

        # Phase detection
        phase_result = detect_phases(request.documents.prd.textContent)
        if not phase_result.phases and request.documents.brd:
            phase_result = detect_phases(request.documents.brd.textContent)

        # Classify via catalog + graph augmentation
        from app.services.graph_augmentation import GraphAugmenter

        classifier = CatalogClassifier(slm_engine, loader)
        calculator = CatalogCalculator(catalog, deps)
        graph_augmenter = GraphAugmenter(deps, catalog)

        phases_list: Optional[list[PhaseEstimation]] = None

        if phase_result.phases:
            # Per-phase classification
            logger.info(f"Catalog engine: phase-wise estimation ({len(phase_result.phases)} phases)")
            phases_list = []
            all_work_items = []

            for phase in phase_result.phases:
                # Extract phase-specific text
                phase_text = _extract_phase_text_for_catalog(request, phase)
                classification = await classifier.classify(phase_text, f"{request.projectName} - {phase.name}")

                # Graph augmentation: enrich classification with dependency graph knowledge
                classification, _graph_result = graph_augmenter.augment(classification)

                result = calculator.calculate(classification)

                # Build PhaseEstimation
                phase_estimation = PhaseEstimation(
                    phaseName=phase.name,
                    effortBreakdown=result.disciplineBreakdown,
                    totalPersonDays=result.pointEstimate,
                    totalPersonMonths=round(result.pointEstimate / 22.0, 2),
                    teamComposition=[
                        TeamMember(discipline=d.discipline, count=max(1, int(d.personDays / 22)))
                        for d in result.disciplineBreakdown
                    ],
                    calendarDuration=round(result.pointEstimate / (len(result.disciplineBreakdown) * 22) * 1.5, 1) if result.disciplineBreakdown else 1.0,
                    assumptions=result.assumptions,
                )
                phases_list.append(phase_estimation)
                all_work_items.extend(result.workItems)

            # Aggregate top-level from phases
            total_effort_days = sum(p.totalPersonDays for p in phases_list)
            total_effort_months = round(total_effort_days / 22.0, 2)

            # Build aggregated discipline breakdown
            discipline_totals: dict[str, float] = {}
            for phase in phases_list:
                for d in phase.effortBreakdown:
                    discipline_totals[d.discipline] = discipline_totals.get(d.discipline, 0) + d.personDays

            # Scale discipline breakdown to match total (includes overhead, surcharges, scope factor)
            raw_sum = sum(discipline_totals.values())
            if raw_sum > 0 and abs(raw_sum - total_effort_days) > 1:
                scale_factor = total_effort_days / raw_sum
                discipline_totals = {k: v * scale_factor for k, v in discipline_totals.items()}

            effort_breakdown = [
                DisciplineEffort(discipline=name, personDays=round(days, 2), personMonths=round(days / 22.0, 2))
                for name, days in sorted(discipline_totals.items(), key=lambda x: -x[1])
            ]

            # Use the last classification for assumptions/risks/breakdown
            catalog_breakdown = CatalogBreakdown(
                workItems=all_work_items,
                overheadDetail={},
                integrationPatterns=[],
                hubSurcharges={},
                aiMultiplierApplied=catalog.get("aiProductivity", {}).get("globalMultiplier", 1.0),
                sanityWarnings=[],
                confidenceLevel="MEDIUM",
                rangeLow=round(total_effort_days * 0.75, 1),
                rangeHigh=round(total_effort_days * 1.25, 1),
            )
            assumptions = []
            for p in phases_list:
                assumptions.extend(p.assumptions)
            if not assumptions:
                assumptions = ["Standard team productivity assumed."]

        else:
            # Single consolidated classification
            logger.info("Catalog engine: consolidated estimation (no phases)")
            classification = await classifier.classify(prd_text, request.projectName)

            # Graph augmentation: enrich classification with dependency graph knowledge
            classification, graph_result = graph_augmenter.augment(classification)

            result = calculator.calculate(classification)

            effort_breakdown = result.disciplineBreakdown
            total_effort_days = result.pointEstimate
            total_effort_months = round(total_effort_days / 22.0, 2)

            # Scale discipline breakdown to match pointEstimate (which includes all multipliers)
            raw_sum = sum(d.personDays for d in effort_breakdown)
            if raw_sum > 0 and abs(raw_sum - total_effort_days) > 1:
                scale_factor = total_effort_days / raw_sum
                effort_breakdown = [
                    DisciplineEffort(
                        discipline=d.discipline,
                        personDays=round(d.personDays * scale_factor, 2),
                        personMonths=round(d.personDays * scale_factor / 22.0, 2),
                    )
                    for d in effort_breakdown
                ]
            assumptions = result.assumptions if result.assumptions else ["Standard team productivity assumed."]

            catalog_breakdown = CatalogBreakdown(
                workItems=result.workItems,
                overheadDetail={
                    "overheadMultiplier": result.overheadMultiplier,
                    "aiMultiplier": result.aiMultiplier,
                },
                integrationPatterns=classification.integrationPatterns,
                hubSurcharges={
                    s: catalog.get("hubSurcharges", {}).get(s, 0)
                    for s in classification.targetSystems
                    if s in catalog.get("hubSurcharges", {})
                },
                aiMultiplierApplied=result.aiMultiplier,
                sanityWarnings=result.sanityWarnings,
                confidenceLevel=result.confidenceLevel,
                rangeLow=result.rangeLow,
                rangeHigh=result.rangeHigh,
                graphAugmentation={
                    "addedSystems": graph_result.added_systems,
                    "addedWorkItems": len(graph_result.added_work_items),
                    "crossDomainDetected": graph_result.cross_domain_detected,
                    "crossDomainSystems": graph_result.cross_domain_systems,
                    "crossDomainOverhead": graph_result.cross_domain_overhead_factor,
                    "warnings": graph_result.warnings,
                } if graph_result.added_systems or graph_result.cross_domain_detected else None,
            )

        # Team composition from discipline breakdown
        # Reasonable team size: 1 person per ~40 person-days of effort in that discipline
        team_composition = [
            TeamMember(discipline=d.discipline, count=max(1, min(5, round(d.personDays / 40))))
            for d in effort_breakdown
        ]

        # Cost calculation (reuse existing)
        rate_card = await load_rate_card(sharepoint_client)
        cost_projection = calculate_cost(effort_breakdown, rate_card)

        # Timeline calculation (reuse existing)
        duration_result = calculate_duration(effort_breakdown, team_composition)

        # Confidence — use catalog's band mapping
        confidence_level = catalog_breakdown.confidenceLevel
        # Map to composite confidence format
        confidence_score = {"HIGH": 85.0, "MEDIUM": 65.0, "LOW": 45.0}.get(confidence_level, 65.0)
        composite_confidence = CompositeConfidenceScore(
            overall=confidence_score,
            factors={
                "catalogClassification": ConfidenceFactor(score=confidence_score, weight=1.0),
            },
            recommendations=[],
            explanation=f"Catalog-based estimation with {confidence_level} confidence ({len(classification.assumptions)} assumptions, {len(classification.risks)} risks).",
        )

        # Scope coverage + Document readiness — run asynchronously after returning results
        # These are backfilled in the background to avoid delaying the main estimation
        scope_analysis = ScopeAnalysis(items=[], coverage=0.5)
        doc_readiness = None

        estimation_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Fire background task to compute scope + doc readiness
        # Skip BRD readiness if BRD is a placeholder (only PRD was uploaded)
        _has_real_brd = (
            request.documents.brd
            and request.documents.brd.filename
            and not request.documents.brd.filename.startswith("no-brd")
            and "[No BRD provided]" not in (request.documents.brd.textContent or "")[:50]
        )
        asyncio.create_task(_backfill_scope_and_readiness(
            estimation_id=estimation_id,
            prd_text=prd_text,
            brd_text=(request.documents.brd.readinessText or request.documents.brd.textContent) if _has_real_brd else "",
            prd_readiness_text=request.documents.prd.readinessText or request.documents.prd.textContent if (request.documents.prd and request.documents.prd.filename != "(no PRD - using BRD content)") else (request.documents.brd.readinessText or request.documents.brd.textContent if request.documents.brd else ""),
            work_items=result.workItems,
            classification=classification,
            assumptions=assumptions,
            slm_engine=slm_engine,
            sharepoint_client=sharepoint_client,
        ))

        elapsed = time.time() - start_time
        logger.info(
            f"Catalog estimation complete: {total_effort_days:.1f} pd, "
            f"confidence={confidence_level}, {elapsed:.1f}s elapsed (scope/doc readiness backfilling async)"
        )

        return EstimationResult(
            id=estimation_id,
            projectName=request.projectName,
            projectDescription=request.projectDescription,
            domain=request.domain,
            stream=request.stream,
            inputTier=input_tier,
            effortBreakdown=effort_breakdown,
            totalEffortPersonDays=round(total_effort_days, 2),
            totalEffortPersonMonths=total_effort_months,
            calendarDuration=duration_result.totalCalendarMonths,
            teamComposition=team_composition,
            scopeCoverage=scope_analysis,
            compositeConfidence=composite_confidence,
            costProjection=cost_projection,
            infraCost=_calculate_infra_cost(result.workItems, classification.targetSystems, deps, catalog),
            documentReadiness=doc_readiness,
            phases=phases_list,
            catalogBreakdown=catalog_breakdown,
            assumptions=assumptions,
            slmModelName=slm_engine.get_model_info().modelName,
            timestamp=timestamp,
        )

    except Exception as exc:
        elapsed = time.time() - start_time
        logger.error(
            f"Catalog estimation failed after {elapsed:.1f}s: {exc}. "
            f"Falling back to legacy engine."
        )
        return None


async def _backfill_scope_and_readiness(
    estimation_id: str,
    prd_text: str,
    brd_text: str,
    prd_readiness_text: str,
    work_items: list,
    classification: Any,
    assumptions: list[str],
    slm_engine: Any,
    sharepoint_client: Any,
) -> None:
    """Background task: compute scope analysis and document readiness.

    Stores results in the global _enrichment_store so the frontend can poll for them.
    Also updates SharePoint monthly file with the enrichment data.
    """
    from app.services.estimation_engine import _enrichment_store

    try:
        from app.services.document_readiness import assess_document_readiness

        logger.info(f"Background enrichment [{estimation_id[:8]}]: starting...")
        _enrichment_store[estimation_id] = {"status": "processing"}

        # Build effort context
        effort_context = json.dumps(
            [{"unitId": w.unitId, "system": w.system, "reason": w.reason} for w in work_items[:20]],
            indent=None
        ) + " " + " ".join(classification.targetSystems)

        # Run all in parallel (they'll serialize at Ollama level but that's fine)
        tasks = []
        labels = []

        tasks.append(analyze_scope(prd_text, effort_context, slm_engine))
        labels.append("scope")

        if brd_text:
            tasks.append(assess_document_readiness(brd_text, "brd", slm_engine))
            labels.append("brd")
        if prd_readiness_text:
            tasks.append(assess_document_readiness(prd_readiness_text, "prd", slm_engine))
            labels.append("prd")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        scope_data = None
        doc_readiness = {}

        for i, label in enumerate(labels):
            if isinstance(results[i], Exception):
                logger.warning(f"Background {label} failed: {results[i]}")
                continue
            if label == "scope":
                scope_data = results[i].model_dump()
                logger.info(f"Background scope: {len(results[i].items)} items, {results[i].coverage:.0%}")
            elif label in ("brd", "prd"):
                doc_readiness[label] = results[i].model_dump()

        # Store in enrichment store for frontend polling
        _enrichment_store[estimation_id] = {
            "status": "complete",
            "scopeCoverage": scope_data,
            "documentReadiness": doc_readiness if doc_readiness else None,
        }

        # Persist enrichment data back to SharePoint monthly file
        try:
            month = datetime.now(timezone.utc).strftime("%Y-%m")
            monthly_file = f"Estimations/Estimations/Estimations_{month}.xlsx"
            updates = {}
            if scope_data:
                updates[12] = json.dumps(scope_data)  # Column 12: ScopeCoverageJSON
            if doc_readiness:
                updates[25] = json.dumps(doc_readiness)  # Column 25: DocumentReadinessJSON
            if updates:
                await sharepoint_client.update_row_cells(
                    filename=monthly_file,
                    sheet="Sheet1",
                    match_column=1,  # Column 1: EstimationId
                    match_value=estimation_id,
                    updates=updates,
                )
                logger.info(f"Background enrichment [{estimation_id[:8]}]: persisted to SharePoint")
        except Exception as sp_exc:
            logger.warning(f"Background enrichment [{estimation_id[:8]}]: SharePoint persist failed: {sp_exc}")

        logger.info(f"Background enrichment [{estimation_id[:8]}]: complete")

    except Exception as exc:
        logger.error(f"Background enrichment [{estimation_id[:8]}] failed: {exc}")
        _enrichment_store[estimation_id] = {"status": "failed", "error": str(exc)}


# In-memory store for async enrichment results (scope + doc readiness)
_enrichment_store: dict[str, dict] = {}


def _calculate_infra_cost(
    work_items: list,
    target_systems: list[str],
    dependencies: dict,
    catalog: dict,
) -> dict | None:
    """Calculate cloud infrastructure cost. Returns None on failure."""
    try:
        from app.services.cloud_cost_calculator import estimate_cloud_cost
        return estimate_cloud_cost(work_items, target_systems, dependencies, catalog)
    except Exception as exc:
        logger.warning(f"Cloud cost calculation failed: {exc}")
        return None


def _extract_phase_text_for_catalog(request: EstimationRequest, phase) -> str:
    """Extract text content relevant to a specific phase for catalog classification.

    Combines BRD/PRD text with phase-specific use cases for focused classification.
    """
    base_text = ""
    if request.documents.brd:
        base_text += request.documents.brd.textContent[:3000] + "\n\n"

    # Add phase-specific context
    base_text += f"=== Phase: {phase.name} ===\n"
    if phase.use_cases:
        base_text += "Requirements/Use Cases for this phase:\n"
        for uc in phase.use_cases:
            base_text += f"- {uc}\n"
        base_text += "\n"

    # Add relevant PRD sections (full text — classifier will focus on phase use cases)
    base_text += request.documents.prd.textContent[:8000]

    return base_text


async def generate_estimation(
    request: EstimationRequest,
    input_tier: InputTier,
    slm_engine: SLMEngine,
    sharepoint_client: SharePointClient,
) -> EstimationResult:
    """Generate a complete estimation from the request.

    Primary path: Catalog-based engine (SLM classifies, app calculates).
    Fallback: Legacy engine (SLM generates numbers directly).

    Orchestrates the full pipeline:
    1. Validate mandatory fields
    2. Try catalog-based estimation (3-call chunked SLM + deterministic math)
    3. If catalog fails, fall back to legacy estimation
    4. Calculate confidence, scope coverage, cost, timeline
    5. Assemble and return the EstimationResult

    Args:
        request: Validated estimation request.
        input_tier: Classified input tier from document processor.
        slm_engine: SLM engine for inference.
        sharepoint_client: SharePoint client for config/template loading.

    Returns:
        Complete EstimationResult.

    Raises:
        ValidationError: If mandatory fields are missing.
        EstimationError: If the estimation pipeline fails.

    Requirements: 2.1, 2.2, 2.3, 2.4, 4.1, 4.2, 4.3, 11.3, 12.3
    """
    # Step 0: Validate mandatory fields (shared by both engines)
    await validate_request(request)

    # Step 1: Run catalog-based estimation (the ONLY estimation path)
    catalog_result = await _generate_estimation_catalog(
        request, input_tier, slm_engine, sharepoint_client
    )
    if catalog_result is not None:
        return catalog_result

    # If catalog engine is set to "legacy" mode, use the old estimation path
    from app.services.catalog_loader import get_catalog_loader
    loader = get_catalog_loader()
    if loader.get_engine_mode() == "legacy":
        logger.info("Legacy engine mode enabled — using old estimation path.")
    else:
        # Catalog engine failed and we're not in legacy mode — error out
        raise EstimationError(
            "Catalog-based estimation failed. The SLM could not classify work items from the PRD. "
            "Please check that Ollama is running and retry. If the issue persists, check the PRD content quality."
        )

    # Step 2: Load configuration and template
    config = await load_config(sharepoint_client)
    template = await load_base_template(sharepoint_client, request.domain, request.stream)

    # Step 2.5: Phase detection — check PRD first, then BRD
    phase_result = detect_phases(request.documents.prd.textContent)
    if not phase_result.phases and request.documents.brd:
        phase_result = detect_phases(request.documents.brd.textContent)

    if phase_result.phases:
        logger.info(
            f"Phase detection: Found {len(phase_result.phases)} phases "
            f"via '{phase_result.detection_method}': "
            f"{[p.name for p in phase_result.phases]}"
        )
    else:
        logger.info(
            f"Phase detection: No phases detected. "
            f"Warning: {phase_result.warning or 'None'}"
        )

    # Step 3: Build prompt and run SLM inference (phase-aware or chunked)
    is_phased = bool(phase_result.phases)

    slm_options = SLMOptions(
        temperature=float(config.get("slm_temperature", str(DEFAULT_TEMPERATURE))),
        maxTokens=int(config.get("slm_max_tokens", str(DEFAULT_MAX_TOKENS))),
    )

    # Step 4: Parse response and build effort breakdown
    phases_list: Optional[list[PhaseEstimation]] = None
    parsed: Optional[dict[str, Any]] = None

    if is_phased:
        prompt = _build_phase_estimation_prompt(request, input_tier, config, phase_result)
        response = await slm_engine.inference(prompt, options=slm_options)
        parsed = _parse_phase_estimation_response(response.content)
        if parsed is None:
            # Fallback: retry with consolidated prompt if phase parsing fails
            logger.warning(
                "Phase-wise SLM response parsing failed. "
                "Falling back to chunked estimation."
            )
            parsed = await _chunked_estimation(request, input_tier, config, slm_engine)
            if parsed is None:
                prompt = _build_estimation_prompt(request, input_tier, config)
                response = await slm_engine.inference(prompt, options=slm_options)
                parsed = _parse_estimation_response(response.content)
            is_phased = False
            response = await slm_engine.inference(prompt, options=slm_options)
            parsed = _parse_estimation_response(response.content)
            is_phased = False
        else:
            # Assemble PhaseEstimation objects
            phases_list = []
            all_effort_entries: list[dict] = []

            for phase_data in parsed["phases"]:
                validated_breakdown = _validate_disciplines(phase_data["effortBreakdown"])
                if not validated_breakdown:
                    logger.warning(
                        f"Phase '{phase_data.get('phaseName', 'Unknown')}' "
                        f"has no valid discipline entries — skipping."
                    )
                    continue

                phase_total_days = sum(e.personDays for e in validated_breakdown)
                phase_total_months = sum(e.personMonths for e in validated_breakdown)

                # Team composition from SLM response
                phase_team: list[TeamMember] = []
                for tc in phase_data.get("teamComposition", []):
                    if "discipline" in tc and "count" in tc:
                        phase_team.append(
                            TeamMember(discipline=tc["discipline"], count=int(tc["count"]))
                        )

                phase_estimation = PhaseEstimation(
                    phaseName=phase_data["phaseName"],
                    effortBreakdown=validated_breakdown,
                    totalPersonDays=round(phase_total_days, 2),
                    totalPersonMonths=round(phase_total_months, 2),
                    teamComposition=phase_team,
                    calendarDuration=phase_data.get("calendarDuration"),
                    assumptions=phase_data.get("assumptions", []),
                )
                phases_list.append(phase_estimation)

                # Accumulate effort entries for top-level aggregation
                all_effort_entries.extend(phase_data["effortBreakdown"])

            if not phases_list:
                # All phases had invalid data — fall back to consolidated
                logger.warning("No valid phases after validation. Falling back to consolidated.")
                prompt = _build_estimation_prompt(request, input_tier, config)
                response = await slm_engine.inference(prompt, options=slm_options)
                parsed = _parse_estimation_response(response.content)
                is_phased = False
                phases_list = None
            else:
                # Build aggregated top-level effort from all phases
                effort_breakdown = _validate_disciplines(all_effort_entries)
                total_effort_days = sum(e.personDays for e in effort_breakdown)
                total_effort_months = sum(e.personMonths for e in effort_breakdown)
                # Construct a parsed dict with the fields expected downstream
                parsed = {
                    "effortBreakdown": [
                        {"discipline": e.discipline, "personDays": e.personDays, "personMonths": e.personMonths}
                        for e in effort_breakdown
                    ],
                    "assumptions": [],
                    "documentDetailScore": parsed.get("documentDetailScore"),
                    "requirementClarityScore": parsed.get("requirementClarityScore"),
                }
                # Gather all assumptions from phases
                for pe in phases_list:
                    parsed["assumptions"].extend(pe.assumptions)
                if not parsed["assumptions"]:
                    parsed["assumptions"] = ["Standard team productivity assumed."]

    if not is_phased:
        if parsed is None:
            # Try chunked estimation (focused multi-call approach)
            parsed = await _chunked_estimation(request, input_tier, config, slm_engine)

        if parsed is None:
            # Final fallback: single-shot prompt
            logger.warning("Chunked estimation returned None, trying single-shot fallback")
            prompt = _build_estimation_prompt(request, input_tier, config)
            response = await slm_engine.inference(prompt, options=slm_options)
            parsed = _parse_estimation_response(response.content)

        if parsed is None:
            raise EstimationError(
                "Failed to parse SLM estimation response. "
                "The model produced an invalid output format. Please retry."
            )

        # Build effort breakdown from consolidated response
        effort_breakdown = [
            DisciplineEffort(
                discipline=entry["discipline"],
                personDays=float(entry["personDays"]),
                personMonths=float(entry["personMonths"]),
            )
            for entry in parsed["effortBreakdown"]
        ]

        total_effort_days = sum(e.personDays for e in effort_breakdown)
        total_effort_months = sum(e.personMonths for e in effort_breakdown)

    # Step 5: Parallel SLM-dependent analysis (scope, team, document readiness)
    effort_json = json.dumps(parsed["effortBreakdown"])

    from app.services.document_readiness import assess_document_readiness

    # Build the async tasks for parallel execution
    scope_task = analyze_scope(
        prd_text=request.documents.prd.textContent,
        effort_breakdown_json=effort_json,
        slm_engine=slm_engine,
        template=template,
    )
    team_task = infer_team_composition(effort_breakdown, slm_engine)

    readiness_tasks = []
    readiness_labels = []

    # Only assess BRD readiness if a real BRD was uploaded (not a placeholder)
    _has_real_brd_legacy = (
        request.documents.brd
        and request.documents.brd.filename
        and not request.documents.brd.filename.startswith("no-brd")
        and "[No BRD provided]" not in (request.documents.brd.textContent or "")[:50]
    )
    if _has_real_brd_legacy:
        readiness_tasks.append(
            assess_document_readiness(
                request.documents.brd.readinessText or request.documents.brd.textContent,
                "brd", slm_engine
            )
        )
        readiness_labels.append("brd")

    has_prd = request.documents.prd and "(no PRD" not in request.documents.prd.filename
    if has_prd:
        readiness_tasks.append(
            assess_document_readiness(
                request.documents.prd.readinessText or request.documents.prd.textContent,
                "prd", slm_engine
            )
        )
        readiness_labels.append("prd")

    # Run all SLM-dependent calls in parallel
    results = await asyncio.gather(
        scope_task, team_task, *readiness_tasks, return_exceptions=True
    )

    # Unpack results with graceful error handling
    # results[0] = scope_analysis
    if isinstance(results[0], Exception):
        logger.warning(f"Scope analysis failed: {results[0]}. Using defaults.")
        scope_analysis = ScopeAnalysis(items=[], coverage=0.0)
    else:
        scope_analysis = results[0]

    # results[1] = team_composition
    if isinstance(results[1], Exception):
        logger.warning(f"Team composition inference failed: {results[1]}. Using defaults.")
        team_composition = [
            TeamMember(discipline=e.discipline, count=1) for e in effort_breakdown
        ]
    else:
        team_composition = results[1]

    # results[2:] = readiness results (dynamic based on what was requested)
    readiness_results = {}
    readiness_offset = 2
    for i, label in enumerate(readiness_labels):
        idx = readiness_offset + i
        if idx < len(results) and not isinstance(results[idx], Exception):
            readiness_results[label] = results[idx].model_dump()
        elif idx < len(results):
            logger.warning(f"{label.upper()} readiness assessment failed: {results[idx]}")

    # Step 6: Confidence calculation
    # Extract quality scores from LLM response; default to 50 if missing/zero
    # (0 usually means the LLM didn't return these fields, not that quality is actually 0)
    raw_detail_score = parsed.get("documentDetailScore")
    raw_clarity_score = parsed.get("requirementClarityScore")
    
    document_detail_score = float(raw_detail_score) if raw_detail_score and float(raw_detail_score) > 0 else 50.0
    requirement_clarity_score = float(raw_clarity_score) if raw_clarity_score and float(raw_clarity_score) > 0 else 50.0

    # Domain history lookup (check if prior estimations exist)
    domain_history_score = await _get_domain_history_score(
        sharepoint_client, request.domain, request.stream
    )

    # Convert scope coverage (0-1) to 0-100 scale for confidence input
    # If scope analysis returned 0 items (LLM didn't extract any), default to 50
    scope_coverage_score = scope_analysis.coverage * 100.0
    if scope_coverage_score == 0.0 and not scope_analysis.items:
        scope_coverage_score = 50.0  # No scope data available, use neutral default

    confidence_factors = ConfidenceFactors(
        inputTier=input_tier,
        documentDetailScore=document_detail_score,
        requirementClarityScore=requirement_clarity_score,
        domainHistoryScore=domain_history_score,
        scopeCoverageScore=scope_coverage_score,
    )
    composite_confidence = calculate_confidence(confidence_factors)

    # Step 7: Cost calculation
    rate_card = await load_rate_card(sharepoint_client)
    cost_projection = calculate_cost(effort_breakdown, rate_card)

    # Step 8: Timeline calculation (duration uses team_composition from parallel gather)
    duration_result = calculate_duration(effort_breakdown, team_composition)

    # Step 10: Assemble result
    assumptions = parsed.get("assumptions", ["Standard team productivity assumed."])
    if not assumptions:
        assumptions = ["Standard team productivity assumed."]

    estimation_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    return EstimationResult(
        id=estimation_id,
        projectName=request.projectName,
        projectDescription=request.projectDescription,
        domain=request.domain,
        stream=request.stream,
        inputTier=input_tier,
        effortBreakdown=effort_breakdown,
        totalEffortPersonDays=round(total_effort_days, 2),
        totalEffortPersonMonths=round(total_effort_months, 2),
        calendarDuration=duration_result.totalCalendarMonths,
        teamComposition=team_composition,
        scopeCoverage=scope_analysis,
        compositeConfidence=composite_confidence,
        costProjection=cost_projection,
        infraCost=parsed.get("infraCost"),
        documentReadiness=readiness_results if readiness_results else None,
        phases=phases_list,
        assumptions=assumptions,
        slmModelName=slm_engine.get_model_info().modelName,
        timestamp=timestamp,
    )


async def _get_domain_history_score(
    sharepoint_client: SharePointClient,
    domain: Domain,
    stream: Stream,
) -> float:
    """Check for historical estimations with matching domain/stream.

    Looks up EstimationIndex.xlsx for prior estimations with the same
    domain and stream to derive a domain history confidence factor.

    Args:
        sharepoint_client: SharePoint client for reading index.
        domain: The domain to check.
        stream: The stream to check.

    Returns:
        Domain history score (0-100). 0 if no history, higher with more history.
    """
    try:
        rows = await sharepoint_client.read_workbook(f"{FOLDER_ESTIMATIONS}/EstimationIndex.xlsx", sheet="Sheet1")
        if len(rows) < 2:
            return 0.0

        headers = [str(h).strip() for h in rows[0]]
        domain_col = headers.index("Domain") if "Domain" in headers else -1
        stream_col = headers.index("Stream") if "Stream" in headers else -1

        if domain_col < 0 or stream_col < 0:
            return 0.0

        match_count = 0
        for row in rows[1:]:
            if len(row) > max(domain_col, stream_col):
                if (
                    str(row[domain_col]).strip() == domain.value
                    and str(row[stream_col]).strip() == stream.value
                ):
                    match_count += 1

        # Scale: 0 matches = 0, 1 match = 30, 3+ matches = 60, 5+ = 80, 10+ = 95
        if match_count == 0:
            return 0.0
        elif match_count == 1:
            return 30.0
        elif match_count <= 3:
            return 60.0
        elif match_count <= 5:
            return 80.0
        else:
            return 95.0

    except Exception as exc:
        logger.warning(f"Failed to check domain history: {exc}")
        return 0.0
