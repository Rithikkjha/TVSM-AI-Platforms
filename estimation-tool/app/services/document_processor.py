"""Document processor service for the Project Estimation Tool.

Handles document validation, text extraction, and tier classification:
- File format validation: accepts PDF, DOCX, MD; rejects unsupported formats
- Page count validation: rejects documents exceeding 20 pages (30 for vendor proposals)
- Text extraction: PyPDF2 for PDF, python-docx for DOCX, direct read for MD
- Tier classification: BRD+PRD → Tier 1, +HLD → Tier 2, +DependentDocs → Tier 3
- Document set validation: rejects submissions missing both BRD and PRD

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
"""

import io
import logging
from typing import Optional

from app.models.schemas import (
    DocumentSet,
    ExtractedDocument,
    InputTier,
    ValidationResult,
)

logger = logging.getLogger(__name__)

# Supported file formats
SUPPORTED_FORMATS = {"pdf", "docx", "md"}

# Page limits
STANDARD_PAGE_LIMIT = 20
VENDOR_PAGE_LIMIT = 30


def _get_file_extension(filename: str) -> str:
    """Extract the file extension (lowercase, without dot).

    Args:
        filename: The filename to extract extension from.

    Returns:
        Lowercase extension string (e.g., 'pdf', 'docx', 'md').
    """
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def validate(filename: str, file_bytes: bytes, is_vendor: bool = False) -> ValidationResult:
    """Validate a document's format and page count.

    Checks:
    1. File format is one of PDF, DOCX, or MD
    2. Page count does not exceed the applicable limit (20 standard, 30 vendor)

    Args:
        filename: Original filename (used to determine format).
        file_bytes: Raw file content as bytes.
        is_vendor: If True, applies the 30-page vendor proposal limit.

    Returns:
        ValidationResult with valid=True if acceptable, or valid=False with error message.

    Requirements: 1.5, 1.6, 1.7
    """
    # Check file format
    extension = _get_file_extension(filename)
    if extension not in SUPPORTED_FORMATS:
        return ValidationResult(
            valid=False,
            error=(
                f"Unsupported file format: '.{extension}'. "
                f"Accepted formats are PDF, DOCX, and Markdown (.md)."
            ),
        )

    # Check page count
    page_limit = VENDOR_PAGE_LIMIT if is_vendor else STANDARD_PAGE_LIMIT
    try:
        page_count = _count_pages(file_bytes, extension)
    except Exception as exc:
        logger.warning(f"Failed to count pages for '{filename}': {exc}")
        return ValidationResult(
            valid=False,
            error=f"Unable to read document '{filename}'. The file may be corrupted or unreadable.",
        )

    if page_count > page_limit:
        return ValidationResult(
            valid=False,
            error=(
                f"Document '{filename}' exceeds {page_limit} pages "
                f"(found {page_count} pages). "
                f"Please provide a condensed version."
            ),
        )

    return ValidationResult(valid=True)


def _count_pages(file_bytes: bytes, extension: str) -> int:
    """Count the number of pages in a document.

    Args:
        file_bytes: Raw file content.
        extension: File extension (pdf, docx, md).

    Returns:
        Number of pages.
    """
    if extension == "pdf":
        return _count_pdf_pages(file_bytes)
    elif extension == "docx":
        return _count_docx_pages(file_bytes)
    elif extension == "md":
        return _count_md_pages(file_bytes)
    return 0


def _count_pdf_pages(file_bytes: bytes) -> int:
    """Count pages in a PDF file using PyPDF2.

    Args:
        file_bytes: PDF file content.

    Returns:
        Number of pages in the PDF.
    """
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    return len(reader.pages)


def _count_docx_pages(file_bytes: bytes) -> int:
    """Estimate page count for a DOCX file.

    DOCX files don't have a fixed page count without rendering.
    We estimate based on paragraph count and content length.
    A typical page contains approximately 3000 characters.

    Args:
        file_bytes: DOCX file content.

    Returns:
        Estimated number of pages.
    """
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    total_chars = sum(len(para.text) for para in doc.paragraphs)
    # Approximate: ~3000 characters per page
    page_count = max(1, (total_chars + 2999) // 3000)
    return page_count


def _count_md_pages(file_bytes: bytes) -> int:
    """Estimate page count for a Markdown file.

    Uses character count to estimate pages (~3000 chars per page).

    Args:
        file_bytes: Markdown file content.

    Returns:
        Estimated number of pages.
    """
    text = file_bytes.decode("utf-8", errors="replace")
    page_count = max(1, (len(text) + 2999) // 3000)
    return page_count


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text content from a document file.

    Uses the appropriate extraction method based on file format:
    - PDF: PyPDF2
    - DOCX: python-docx
    - MD: direct UTF-8 read

    Args:
        file_bytes: Raw file content as bytes.
        filename: Original filename (used to determine format).

    Returns:
        Extracted text content as a string.

    Raises:
        ValueError: If the file format is unsupported.

    Requirements: 1.5
    """
    extension = _get_file_extension(filename)

    if extension == "pdf":
        return _extract_pdf_text(file_bytes)
    elif extension == "docx":
        return _extract_docx_text(file_bytes)
    elif extension == "md":
        return _extract_md_text(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file format: '.{extension}'. "
            f"Accepted formats are PDF, DOCX, and Markdown (.md)."
        )


def _extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from a PDF file using PyPDF2.

    Args:
        file_bytes: PDF file content.

    Returns:
        Concatenated text from all PDF pages.
    """
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_docx_text(file_bytes: bytes) -> str:
    """Extract text from a DOCX file using python-docx.

    Args:
        file_bytes: DOCX file content.

    Returns:
        Concatenated text from all paragraphs and tables.
    """
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    text_parts = []

    # Extract paragraphs
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)

    # Extract tables (critical for phase detection and structured data)
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            # Join cells with tab separator to preserve table structure
            row_text = "\t".join(cells)
            if row_text.strip():
                text_parts.append(row_text)

    return "\n".join(text_parts)


def _extract_md_text(file_bytes: bytes) -> str:
    """Extract text from a Markdown file by direct UTF-8 read.

    Args:
        file_bytes: Markdown file content.

    Returns:
        The raw text content of the Markdown file.
    """
    return file_bytes.decode("utf-8", errors="replace")


def classify_tier(documents: dict[str, Optional[ExtractedDocument]]) -> InputTier:
    """Determine the InputTier based on which document types are present.

    Classification rules:
    - BRD only (no PRD) → Tier 0 (ballpark)
    - BRD + PRD → Tier 1
    - BRD + PRD + HLD → Tier 2
    - BRD + PRD + HLD + DependentDocs → Tier 3

    The classification is independent of document content, size, or format.

    Args:
        documents: Dictionary with keys 'brd', 'prd', 'hld', 'dependent_docs'.
            Values are ExtractedDocument or None. 'dependent_docs' can be
            a list of ExtractedDocument or None.

    Returns:
        InputTier (0, 1, 2, or 3).

    Requirements: 1.1, 1.2, 1.3
    """
    has_prd = documents.get("prd") is not None
    has_hld = documents.get("hld") is not None
    has_dependent_docs = documents.get("dependent_docs") is not None

    # If dependent_docs is a list, check if it's non-empty
    dependent_docs = documents.get("dependent_docs")
    if isinstance(dependent_docs, list):
        has_dependent_docs = len(dependent_docs) > 0

    if not has_prd:
        return 0
    elif has_hld and has_dependent_docs:
        return 3
    elif has_hld:
        return 2
    else:
        return 1


def validate_document_set(
    documents: dict[str, Optional[ExtractedDocument]],
) -> ValidationResult:
    """Validate that a document set contains the mandatory BRD and PRD.

    Rejects submissions that are missing either or both of BRD and PRD.

    Args:
        documents: Dictionary with keys 'brd', 'prd' (and optionally 'hld',
            'dependent_docs'). Values are ExtractedDocument or None.

    Returns:
        ValidationResult with valid=True if BRD and PRD are present,
        or valid=False with a descriptive error message.

    Requirements: 1.4
    """
    has_brd = documents.get("brd") is not None
    has_prd = documents.get("prd") is not None

    if not has_brd and not has_prd:
        return ValidationResult(
            valid=False,
            error="Both BRD and PRD are mandatory. Please upload both documents to proceed.",
        )
    elif not has_brd:
        return ValidationResult(
            valid=False,
            error="BRD (Business Requirements Document) is mandatory. Please upload a BRD to proceed.",
        )
    elif not has_prd:
        return ValidationResult(
            valid=False,
            error="PRD (Product Requirements Document) is mandatory. Please upload a PRD to proceed.",
        )

    return ValidationResult(valid=True)


# --- Markdown-aware extraction (used by PRD/BRD/HLD completeness checker) ---


def extract_text_markdown(file_bytes: bytes, filename: str) -> str:
    """Extract document text with tables rendered as Markdown pipe tables.

    Unlike extract_text() (which joins table cells with tabs for phase
    detection), this renders tables in Markdown pipe format so small LLMs can
    clearly recognize populated vs empty tables. Used by the completeness
    checker only — does NOT affect the estimation/phase-detection pipeline.

    Args:
        file_bytes: Raw file content.
        filename: Original filename (determines format).

    Returns:
        Extracted text with Markdown-formatted tables.
    """
    extension = _get_file_extension(filename)

    if extension == "docx":
        return _extract_docx_text_markdown(file_bytes)
    elif extension == "pdf":
        # PDFs have no reliable table structure; reuse standard extraction
        return _extract_pdf_text(file_bytes)
    elif extension == "md":
        return _extract_md_text(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file format: '.{extension}'. "
            f"Accepted formats are PDF, DOCX, and Markdown (.md)."
        )


def _render_markdown_table(table) -> str:
    """Render a python-docx table as a Markdown pipe table.

    Empty cells are rendered as a visible marker so the model can tell a
    populated table from a blank template table.

    Args:
        table: A python-docx Table object.

    Returns:
        Markdown table string (with header separator), or empty string if no rows.
    """
    rows = table.rows
    if not rows:
        return ""

    def _clean(cell_text: str) -> str:
        # Collapse newlines/pipes inside cells so the table stays one row per line
        t = cell_text.strip().replace("\n", " ").replace("|", "/")
        return t if t else "—"  # visible marker for empty cell

    md_lines: list[str] = []

    # Header row
    header_cells = [_clean(c.text) for c in rows[0].cells]
    md_lines.append("| " + " | ".join(header_cells) + " |")
    md_lines.append("| " + " | ".join("---" for _ in header_cells) + " |")

    # Body rows
    for row in rows[1:]:
        body_cells = [_clean(c.text) for c in row.cells]
        md_lines.append("| " + " | ".join(body_cells) + " |")

    return "\n".join(md_lines)


def _extract_docx_text_markdown(file_bytes: bytes) -> str:
    """Extract DOCX text in document order with tables as Markdown.

    Walks paragraphs and tables in their actual document order so that each
    table appears right after its section heading.

    Args:
        file_bytes: DOCX file content.

    Returns:
        Concatenated text with Markdown-formatted tables.
    """
    from docx import Document
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    from docx.text.paragraph import Paragraph
    from docx.table import Table

    doc = Document(io.BytesIO(file_bytes))
    parts: list[str] = []

    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            para = Paragraph(child, doc)
            if para.text.strip():
                parts.append(para.text.strip())
        elif isinstance(child, CT_Tbl):
            table = Table(child, doc)
            md = _render_markdown_table(table)
            if md:
                parts.append(md)

    return "\n".join(parts)
