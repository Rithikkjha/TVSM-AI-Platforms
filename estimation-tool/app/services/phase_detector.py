"""Phase Detector module for identifying phased delivery plans in PRD/BRD documents.

Detects phase structures using multiple strategies:
1. Numbered headings (## Phase 1: ..., ### Release 2 - ...)
2. Tabular assignments (rows with Phase/Release column)
3. Inline annotations (UC#1 [Phase 1], [Sprint 1-3])
4. Milestone groupings (Milestone 1 - MVP)
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from app.models.schemas import Discipline


@dataclass
class PhaseInfo:
    """A detected phase with its name and assigned use cases."""

    name: str
    use_cases: list[str] = field(default_factory=list)


@dataclass
class PhaseDetectionResult:
    """Result of phase detection on document text."""

    phases: list[PhaseInfo] = field(default_factory=list)
    detection_method: Optional[str] = None
    warning: Optional[str] = None


# --- Discipline Aliases and Normalization (Task 2.6) ---

DISCIPLINE_ALIASES: dict[str, Discipline] = {
    "backend": Discipline.DIGITAL_ENGINEERING,
    "frontend": Discipline.DIGITAL_ENGINEERING,
    "fullstack": Discipline.DIGITAL_ENGINEERING,
    "software engineering": Discipline.DIGITAL_ENGINEERING,
    "ml": Discipline.DATA_SCIENCE,
    "machine learning": Discipline.DATA_SCIENCE,
    "analytics": Discipline.DATA_SCIENCE,
    "data pipeline": Discipline.DATA_ENGINEERING,
    "etl": Discipline.DATA_ENGINEERING,
    "bi": Discipline.DATA_ENGINEERING,
    "ci/cd": Discipline.DEVOPS,
    "infrastructure": Discipline.DEVOPS,
    "testing": Discipline.QA_TESTING,
    "qa": Discipline.QA_TESTING,
    "quality assurance": Discipline.QA_TESTING,
    "cloud": Discipline.TECH_COE,
    "architecture": Discipline.TECH_COE,
    "security": Discipline.TECH_COE,
    "design": Discipline.PRODUCT_DESIGN,
    "ux": Discipline.PRODUCT_DESIGN,
    "product": Discipline.PRODUCT_DESIGN,
    "product management": Discipline.PRODUCT_DESIGN,
}


def normalize_discipline(raw_name: str) -> Optional[Discipline]:
    """Map a raw discipline string to the fixed Discipline enum.

    Resolution order:
    1. Exact match (case-insensitive) against enum values.
    2. Alias lookup from DISCIPLINE_ALIASES.
    3. Substring match against alias keys.
    4. Returns None if no match found.
    """
    if not raw_name or not raw_name.strip():
        return None

    cleaned = raw_name.strip()

    # 1. Exact match against enum values (case-insensitive)
    for member in Discipline:
        if member.value.lower() == cleaned.lower():
            return member

    # 2. Alias lookup (case-insensitive)
    lower_cleaned = cleaned.lower()
    if lower_cleaned in DISCIPLINE_ALIASES:
        return DISCIPLINE_ALIASES[lower_cleaned]

    # 3. Substring match against alias keys
    for alias_key, discipline in DISCIPLINE_ALIASES.items():
        if alias_key in lower_cleaned or lower_cleaned in alias_key:
            return discipline

    return None


# --- Phase Detection Strategies ---


def _detect_heading_phases(text: str) -> list[PhaseInfo]:
    """Detect phases from numbered headings.

    Matches patterns like:
    - ## Phase 1: Identity & Rides
    - ### Release 2 - Payments
    - Phase-1
    - Phase 1
    - # Phase 1: ...
    """
    # Pattern matches markdown headings or standalone phase/release lines
    heading_pattern = re.compile(
        r"^(?:#{1,6}\s+)?"  # Optional markdown heading prefix
        r"(?:Phase|Release)\s*[-–—]?\s*(\d+)"  # Phase/Release + number
        r"(?:\s*[-–—:]\s*(.+?))?$",  # Optional separator + title
        re.MULTILINE | re.IGNORECASE,
    )

    matches = list(heading_pattern.finditer(text))
    if not matches:
        return []

    phases: list[PhaseInfo] = []
    lines = text.split("\n")

    for i, match in enumerate(matches):
        phase_num = match.group(1)
        phase_title = match.group(2).strip() if match.group(2) else ""
        phase_name = f"Phase {phase_num}"
        if phase_title:
            phase_name = f"Phase {phase_num}: {phase_title}"

        # Determine the text block under this heading (until next phase heading)
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)

        block = text[start_pos:end_pos]

        # Extract use cases from the block
        use_cases = _extract_use_cases_from_block(block)
        phases.append(PhaseInfo(name=phase_name, use_cases=use_cases))

    return phases


def _detect_table_phases(text: str) -> list[PhaseInfo]:
    """Detect phases from tabular use case assignments.

    Handles tables with columns like:
    UC# | Change | Type | Feature Requirement | Description | Channel | Acceptance Criteria | Priority | Phase

    Where the Phase column has values like:
    - "Phase -1", "Phase - 1", "Phase - 2"
    - "Phase 1", "Phase 2"
    - "Release 1", "Release 2"

    Lines can be tab, pipe, or multi-space separated.
    Also handles PDF-extracted text where "Phase N" appears at end of lines.
    """
    lines = text.split("\n")

    # Find the header row that contains a "Phase" or "Release" column
    header_idx = -1
    phase_col_idx = -1
    uc_col_idx = -1
    feature_col_idx = -1
    separator = None

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Determine separator: pipe, tab, or multi-space (3+)
        if "|" in stripped:
            cols = [c.strip() for c in stripped.split("|")]
            sep = "|"
        elif "\t" in stripped:
            cols = [c.strip() for c in stripped.split("\t")]
            sep = "\t"
        elif "  " in stripped:
            # Multi-space separator (common in PDF extraction)
            cols = [c.strip() for c in re.split(r"\s{2,}", stripped)]
            sep = "  "
        else:
            continue

        # Filter out empty columns from leading/trailing pipes
        cols_clean = [c for c in cols if c]

        # Check if this row contains a phase-related header
        for ci, col in enumerate(cols_clean):
            col_lower = col.lower().strip()
            if col_lower in ("phase", "release", "phase/release", "delivery phase"):
                phase_col_idx = ci
                header_idx = idx
                separator = sep
                break

        if phase_col_idx >= 0:
            # Also find use case / feature column
            for ci, col in enumerate(cols_clean):
                col_lower = col.lower().strip()
                if col_lower in ("uc#", "uc", "use case", "use case id", "id", "uc id"):
                    uc_col_idx = ci
                if col_lower in (
                    "feature requirement",
                    "feature",
                    "requirement",
                    "description",
                    "name",
                    "change",
                ):
                    feature_col_idx = ci
            break

    if header_idx < 0 or phase_col_idx < 0:
        return []

    # Parse data rows after the header
    phase_map: dict[str, list[str]] = {}

    for idx in range(header_idx + 1, len(lines)):
        line = lines[idx].strip()
        if not line:
            continue

        # Skip markdown table separator lines (e.g., |---|---|---|)
        if re.match(r"^[\s|:-]+$", line):
            continue

        # Split using the same separator
        if separator == "|":
            cols = [c.strip() for c in line.split("|")]
        else:
            cols = [c.strip() for c in line.split("\t")]

        cols_clean = [c for c in cols if c != ""]

        if len(cols_clean) <= phase_col_idx:
            continue

        phase_value = cols_clean[phase_col_idx].strip()

        # Normalize phase value - handle "Phase -1", "Phase - 1", "Phase-1", "Phase 1"
        phase_normalized = _normalize_phase_name(phase_value)
        if not phase_normalized:
            continue

        # Get use case identifier
        uc_id = ""
        if uc_col_idx >= 0 and uc_col_idx < len(cols_clean):
            uc_id = cols_clean[uc_col_idx].strip()

        # Get feature/description as fallback
        feature_desc = ""
        if feature_col_idx >= 0 and feature_col_idx < len(cols_clean):
            feature_desc = cols_clean[feature_col_idx].strip()

        use_case_entry = uc_id if uc_id else feature_desc
        if not use_case_entry:
            # Use any non-phase column content as identifier
            for ci, col in enumerate(cols_clean):
                if ci != phase_col_idx and col.strip():
                    use_case_entry = col.strip()
                    break

        if phase_normalized not in phase_map:
            phase_map[phase_normalized] = []
        if use_case_entry:
            phase_map[phase_normalized].append(use_case_entry)

    # Convert to PhaseInfo list, sorted by phase number
    phases = []
    for phase_name in sorted(phase_map.keys(), key=_phase_sort_key):
        phases.append(PhaseInfo(name=phase_name, use_cases=phase_map[phase_name]))

    return phases


def _detect_lineend_phases(text: str) -> list[PhaseInfo]:
    """Detect phases from 'Phase N' patterns at end of lines.

    Common in PDF-extracted tables where cell content runs together and
    the Phase column value appears at the end of each row.

    Matches lines ending with: Phase 1, Phase -1, Phase - 2, Release 1, etc.
    """
    # Pattern: line content followed by Phase/Release N at end
    pattern = re.compile(
        r"^(.+?)\s+(?:Phase|Release)\s*[-–—]?\s*[-–—]?\s*(\d+)\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    matches = list(pattern.finditer(text))
    if len(matches) < 3:  # Need at least 3 rows to be meaningful
        return []

    phase_map: dict[str, list[str]] = {}
    for match in matches:
        line_content = match.group(1).strip()
        phase_num = match.group(2)
        phase_name = f"Phase {phase_num}"

        # Try to extract a UC# from the line content
        uc_match = re.search(r"UC#?\s*(\d+)", line_content, re.IGNORECASE)
        if uc_match:
            use_case = f"UC#{uc_match.group(1)}"
        else:
            # Use first meaningful chunk of the line
            use_case = line_content[:60].strip()

        if phase_name not in phase_map:
            phase_map[phase_name] = []
        phase_map[phase_name].append(use_case)

    phases = []
    for phase_name in sorted(phase_map.keys(), key=_phase_sort_key):
        phases.append(PhaseInfo(name=phase_name, use_cases=phase_map[phase_name]))

    return phases


def _detect_inline_phases(text: str) -> list[PhaseInfo]:
    """Detect phases from inline annotations.

    Matches patterns like:
    - UC#1 [Phase 1]
    - UC#12 [Phase 2]
    - Feature X [Sprint 1-3]
    - Requirement Y [Release 2]
    """
    # Pattern: text followed by [Phase N] or [Sprint N] or [Release N]
    inline_pattern = re.compile(
        r"((?:UC#?\d+|[A-Za-z][A-Za-z0-9_ ]*?))\s*"  # Use case ID or name
        r"\[\s*(?:Phase|Sprint|Release)\s*[-–—]?\s*(\d+(?:\s*[-–—]\s*\d+)?)\s*\]",
        re.IGNORECASE,
    )

    matches = list(inline_pattern.finditer(text))
    if not matches:
        return []

    phase_map: dict[str, list[str]] = {}
    for match in matches:
        uc_name = match.group(1).strip()
        phase_ref = match.group(2).strip()
        # Normalize sprint ranges like "1-3" to just use the first number for grouping
        phase_num = re.match(r"(\d+)", phase_ref)
        if phase_num:
            phase_name = f"Phase {phase_num.group(1)}"
        else:
            phase_name = f"Phase {phase_ref}"

        if phase_name not in phase_map:
            phase_map[phase_name] = []
        phase_map[phase_name].append(uc_name)

    phases = []
    for phase_name in sorted(phase_map.keys(), key=_phase_sort_key):
        phases.append(PhaseInfo(name=phase_name, use_cases=phase_map[phase_name]))

    return phases


def _detect_milestone_phases(text: str) -> list[PhaseInfo]:
    """Detect phases from milestone-based groupings.

    Matches patterns like:
    - Milestone 1 - MVP
    - Milestone 2: Enhanced Features
    - ## Milestone 1 - Core
    """
    milestone_pattern = re.compile(
        r"^(?:#{1,6}\s+)?"  # Optional markdown heading
        r"Milestone\s+(\d+)\s*[-–—:]\s*(.+?)$",
        re.MULTILINE | re.IGNORECASE,
    )

    matches = list(milestone_pattern.finditer(text))
    if not matches:
        return []

    phases: list[PhaseInfo] = []

    for i, match in enumerate(matches):
        milestone_num = match.group(1)
        milestone_title = match.group(2).strip()
        phase_name = f"Milestone {milestone_num} - {milestone_title}"

        # Get block of text under this milestone
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)

        block = text[start_pos:end_pos]
        use_cases = _extract_use_cases_from_block(block)
        phases.append(PhaseInfo(name=phase_name, use_cases=use_cases))

    return phases


# --- Main Entry Point (Task 2.1) ---


def detect_phases(text: str) -> PhaseDetectionResult:
    """Scan document text for phase indicators and extract phase structure.

    Detection strategies (in priority order):
    1. Numbered headings: "## Phase 1: ...", "### Release 2 - ..."
    2. Tabular assignments: rows with Phase/Release column
    3. Inline annotations: "UC#1 [Phase 1]", "[Sprint 1-3]"
    4. Milestone groupings: "Milestone 1 - MVP"

    Returns PhaseDetectionResult with empty phases list if no phases found.
    Returns single-phase documents as non-phased (empty list + no warning).
    If multiple strategies detect phases (ambiguity), returns empty with warning.
    """
    if not text or not text.strip():
        return PhaseDetectionResult()

    # Run all detection strategies
    results: list[tuple[str, list[PhaseInfo]]] = []

    heading_phases = _detect_heading_phases(text)
    if heading_phases:
        results.append(("heading", heading_phases))

    table_phases = _detect_table_phases(text)
    if table_phases:
        results.append(("table", table_phases))

    # Fallback: detect "Phase N" at end of lines (common in PDF-extracted tables)
    if not results:
        lineend_phases = _detect_lineend_phases(text)
        if lineend_phases:
            results.append(("lineend", lineend_phases))

    inline_phases = _detect_inline_phases(text)
    if inline_phases:
        results.append(("inline", inline_phases))

    milestone_phases = _detect_milestone_phases(text)
    if milestone_phases:
        results.append(("milestone", milestone_phases))

    # No phases detected
    if not results:
        return PhaseDetectionResult()

    # Ambiguity check: if multiple strategies detect different phase counts,
    # it may be conflicting structure
    if len(results) > 1:
        phase_counts = [len(phases) for _, phases in results]
        # If strategies disagree on the number of phases, that's ambiguous
        if len(set(phase_counts)) > 1:
            return PhaseDetectionResult(
                warning="Conflicting phase structures detected across different formats. "
                "Falling back to non-phased estimation."
            )

    # Use the first (highest priority) result
    method, phases = results[0]

    # Single-phase collapsing: if only one phase detected, treat as non-phased
    if len(phases) <= 1:
        return PhaseDetectionResult()

    return PhaseDetectionResult(phases=phases, detection_method=method)


# --- Helper Functions ---


def _normalize_phase_name(raw: str) -> Optional[str]:
    """Normalize a raw phase value like 'Phase -1', 'Phase - 2', 'Phase 1' to 'Phase N'."""
    if not raw or not raw.strip():
        return None

    # Match various phase formats: "Phase -1", "Phase - 1", "Phase-1", "Phase 1",
    # "Release 1", "Release - 2", etc.
    pattern = re.compile(
        r"^\s*(?:Phase|Release)\s*[-–—]?\s*[-–—]?\s*(\d+)\s*$",
        re.IGNORECASE,
    )
    match = pattern.match(raw.strip())
    if match:
        num = match.group(1)
        return f"Phase {num}"

    return None


def _phase_sort_key(phase_name: str) -> int:
    """Extract numeric portion of phase name for sorting."""
    match = re.search(r"(\d+)", phase_name)
    if match:
        return int(match.group(1))
    return 0


def _extract_use_cases_from_block(block: str) -> list[str]:
    """Extract use case identifiers or bullet items from a text block."""
    use_cases: list[str] = []

    # Match UC# patterns
    uc_pattern = re.compile(r"UC#?\s*(\d+)", re.IGNORECASE)
    uc_matches = uc_pattern.findall(block)
    for uc_num in uc_matches:
        use_cases.append(f"UC#{uc_num}")

    # Match bullet points or numbered list items (if no UC# found)
    if not use_cases:
        bullet_pattern = re.compile(
            r"^\s*(?:[-*•]|\d+[.)]\s)\s*(.+?)$", re.MULTILINE
        )
        bullets = bullet_pattern.findall(block)
        for bullet in bullets:
            cleaned = bullet.strip()
            if cleaned and len(cleaned) > 2:
                use_cases.append(cleaned)

    return use_cases
