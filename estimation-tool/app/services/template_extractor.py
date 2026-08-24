"""Extract sections from uploaded template documents.

Captures not just heading names but the *expected content* under each heading
(guidance text and table column headers). This forms the rubric used for
section-by-section completeness evaluation.
"""
import io
import re
from dataclasses import dataclass, field
from typing import Optional

from docx import Document


@dataclass
class TemplateSection:
    """A section extracted from a template document."""
    name: str
    level: int = 1  # heading level (1=H1, 2=H2)
    has_table: bool = False  # whether template shows a table in this section
    has_placeholder: bool = False  # whether template has placeholder text like <Name>, XX
    expected_content: str = ""  # guidance/example text shown under this heading in the template
    table_columns: list[str] = field(default_factory=list)  # column headers if section has a table


@dataclass
class ExtractedTemplate:
    """Complete template extracted from a document."""
    doc_type: str  # 'prd', 'brd', 'hld'
    filename: str
    sections: list[TemplateSection] = field(default_factory=list)


def extract_template_sections(file_bytes: bytes, filename: str) -> list[TemplateSection]:
    """Extract section headings, structure, and expected content from a template file.

    Args:
        file_bytes: Raw bytes of a .docx or .pdf template file.
        filename: Original filename for reference.

    Returns:
        List of TemplateSection objects representing the document structure.
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if ext == 'pdf':
        return _extract_sections_from_pdf(file_bytes)
    else:
        return _extract_sections_from_docx(file_bytes)


def _is_heading_para(para) -> tuple[bool, int]:
    """Determine if a paragraph is a heading and its level.

    Returns:
        (is_heading, level)
    """
    text = para.text.strip()
    if not text:
        return False, 1

    # Method 1: Heading style (most reliable)
    if para.style and para.style.name and 'Heading' in para.style.name:
        try:
            level = int(para.style.name.replace('Heading ', ''))
        except (ValueError, AttributeError):
            level = 1
        return True, level

    # Method 2: Bold paragraph — only if short, no punctuation at end, not a sentence
    if para.runs and all(run.bold for run in para.runs if run.text.strip()):
        if (len(text) < 80
            and len(text.split()) <= 8
            and not text.endswith(('.', ',', ':', ';'))
            and not text.startswith(('Ex ', 'Example', 'Check ', 'Add ', 'Mention ', 'Describe ', 'Explain ', 'Capture '))
            and '<' not in text  # Skip placeholder text like <Name>
            and 'XX' not in text
        ):
            return True, 2

    # Method 3: Numbered section pattern (1.1, 2.3, etc.)
    if re.match(r'^\d+(\.\d+)?\s+\w', text) and len(text) < 120:
        # Skip if it looks like a table row (has too many numbers or pipe chars)
        if text.count('|') > 0 or re.match(r'^\d+\s+[A-Z]\s', text):
            return False, 1
        level = 2 if '.' in text.split()[0] else 1
        return True, level

    return False, 1


def _extract_sections_from_docx(file_bytes: bytes) -> list[TemplateSection]:
    """Extract sections + expected content from a .docx template file.

    Walks the document body in order. Heading paragraphs start new sections;
    non-heading paragraphs are collected as the section's expected content.
    Tables are associated with the most recent heading and their column headers
    are captured.
    """
    doc = Document(io.BytesIO(file_bytes))
    sections: list[TemplateSection] = []
    current: Optional[TemplateSection] = None
    content_buffer: list[str] = []

    def _flush_content():
        """Attach buffered content to the current section."""
        if current is not None and content_buffer:
            text = " ".join(content_buffer).strip()
            # Limit guidance text length
            current.expected_content = text[:600]
        content_buffer.clear()

    # Build an ordered list of body elements (paragraphs + tables interleaved)
    body_items = _iter_body_items(doc)

    for kind, item in body_items:
        if kind == "para":
            para = item
            text = para.text.strip()
            if not text:
                continue

            is_heading, level = _is_heading_para(para)

            if is_heading:
                # Close out previous section
                _flush_content()
                has_placeholder = bool(re.search(r'<\s*\w+\s*>|XX|YY|\bTBD\b', text))
                current = TemplateSection(
                    name=text,
                    level=level,
                    has_placeholder=has_placeholder,
                )
                sections.append(current)
            else:
                # Body content under the current heading
                if current is not None:
                    content_buffer.append(text)

        elif kind == "table":
            table = item
            # Capture column headers from the first row
            if table.rows:
                cols = [c.text.strip() for c in table.rows[0].cells if c.text.strip()]
                if current is not None and cols:
                    current.has_table = True
                    # Merge unique columns
                    for c in cols:
                        if c not in current.table_columns:
                            current.table_columns.append(c)
                    # Also fold a few example rows into expected content for richer rubric
                    sample_rows = []
                    for row in table.rows[1:3]:
                        cells = [c.text.strip() for c in row.cells if c.text.strip()]
                        if cells:
                            sample_rows.append(" | ".join(cells))
                    if sample_rows:
                        content_buffer.append("Table columns: " + ", ".join(cols))
                        content_buffer.append("Examples: " + " ; ".join(sample_rows))

    _flush_content()

    return sections


def _iter_body_items(doc):
    """Yield ('para', paragraph) and ('table', table) in document order."""
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    from docx.text.paragraph import Paragraph
    from docx.table import Table

    parent_elm = doc.element.body
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield "para", Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield "table", Table(child, doc)


def _extract_sections_from_pdf(file_bytes: bytes) -> list[TemplateSection]:
    """Extract sections from a PDF template.

    PDF text extraction is unreliable (PyPDF2 often merges or loses text).
    Instead of trying to parse headings from mangled PDF text, we use the
    canonical section list from doc_templates.json as the authoritative source.
    The PDF upload serves as confirmation that the admin wants this template active.

    We still try to extract what we can, but fall back to the full canonical list.
    """
    from PyPDF2 import PdfReader
    import json
    import os

    # Try to extract text and match known sections
    reader = PdfReader(io.BytesIO(file_bytes))
    all_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            all_text += page_text + "\n"

    text_lower = all_text.lower()

    # Load canonical sections from doc_templates.json
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "doc_templates.json")
    canonical_names = []
    try:
        with open(config_path, "r") as f:
            templates = json.load(f)
        prd_template = templates.get("prd", {})
        canonical_names = [s["name"] for s in prd_template.get("sections", [])]
    except Exception:
        pass

    if not canonical_names:
        # Hardcoded fallback
        canonical_names = [
            "Document Metadata", "Problem Definition", "Business Impact",
            "Product Objective", "User Personas", "Customer Journey Summary",
            "Assumptions Made", "Platform Capability Check", "System Interaction Overview",
            "Functional Requirements", "Edge Cases and Exception Handling",
            "Out of Scope", "Non-Functional Requirements", "Dependencies",
            "Release Scope / Rollout Plan", "Success Criteria",
            "Metrics/Dashboard Required", "Next Phases Planned",
            "UI/UX Design", "Open Questions", "Appendix / Glossary",
        ]

    # Try text matching first — if we find at least 10, use those
    matched = []
    for name in canonical_names:
        # Check if any significant part of the name appears in text
        key_words = [w.lower() for w in name.split() if len(w) > 3]
        if key_words and any(kw in text_lower for kw in key_words[:2]):
            matched.append(name)

    # If PDF text extraction found a reasonable number, use those
    if len(matched) >= 10:
        return [TemplateSection(name=n, level=1) for n in matched]

    # Otherwise, use the full canonical list (PDF text was unreadable)
    return [TemplateSection(name=n, level=1) for n in canonical_names]
