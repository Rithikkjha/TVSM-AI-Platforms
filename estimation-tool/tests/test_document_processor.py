"""Unit tests for document processor service (app/services/document_processor.py).

Tests file validation, text extraction, tier classification, and document set
validation including:
- Format validation (PDF, DOCX, MD accepted; others rejected)
- Page count validation (20 pages standard, 30 for vendor proposals)
- Text extraction for each format
- Tier classification logic (BRD+PRD → Tier 1, +HLD → Tier 2, +DependentDocs → Tier 3)
- Rejection of submissions missing BRD and/or PRD

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
"""

import io

import pytest

from app.models.schemas import ExtractedDocument
from app.services.document_processor import (
    STANDARD_PAGE_LIMIT,
    VENDOR_PAGE_LIMIT,
    classify_tier,
    extract_text,
    validate,
    validate_document_set,
    _count_md_pages,
    _count_pdf_pages,
    _count_docx_pages,
    _get_file_extension,
)


# --- Helper Functions ---


def _make_pdf_bytes(num_pages: int = 1, chars_per_page: int = 500) -> bytes:
    """Create a valid PDF with a given number of pages using PyPDF2/reportlab.

    Uses PyPDF2's PdfWriter to create a minimal multi-page PDF.
    """
    from PyPDF2 import PdfWriter
    from PyPDF2.generic import (
        ArrayObject,
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
        NumberObject,
    )

    writer = PdfWriter()
    for i in range(num_pages):
        # Add a blank page with dimensions (letter size)
        writer.add_blank_page(width=612, height=792)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.getvalue()


def _make_docx_bytes(num_paragraphs: int = 10, chars_per_para: int = 300) -> bytes:
    """Create a valid DOCX with a given number of paragraphs."""
    from docx import Document

    doc = Document()
    for i in range(num_paragraphs):
        doc.add_paragraph("A" * chars_per_para)

    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output.getvalue()


def _make_md_bytes(num_chars: int = 1000) -> bytes:
    """Create markdown content with a given character count."""
    content = "# Test Document\n\n" + "x" * (num_chars - 20) + "\n"
    return content.encode("utf-8")


def _make_extracted_doc(
    filename: str = "test.pdf",
    fmt: str = "pdf",
    page_count: int = 5,
    text: str = "Sample content",
) -> ExtractedDocument:
    """Create an ExtractedDocument for testing."""
    return ExtractedDocument(
        filename=filename,
        format=fmt,
        pageCount=page_count,
        textContent=text,
    )


# --- File Extension Tests ---


class TestGetFileExtension:
    """Tests for _get_file_extension helper."""

    def test_pdf_extension(self):
        assert _get_file_extension("document.pdf") == "pdf"

    def test_docx_extension(self):
        assert _get_file_extension("document.docx") == "docx"

    def test_md_extension(self):
        assert _get_file_extension("readme.md") == "md"

    def test_uppercase_extension(self):
        assert _get_file_extension("DOCUMENT.PDF") == "pdf"

    def test_no_extension(self):
        assert _get_file_extension("noextension") == ""

    def test_multiple_dots(self):
        assert _get_file_extension("my.file.name.pdf") == "pdf"


# --- Format Validation Tests ---


class TestValidateFormat:
    """Tests for file format validation.

    Requirements: 1.5, 1.6
    """

    def test_accepts_pdf(self):
        """PDF format is accepted."""
        pdf_bytes = _make_pdf_bytes(num_pages=1)
        result = validate("document.pdf", pdf_bytes)
        assert result.valid is True
        assert result.error is None

    def test_accepts_docx(self):
        """DOCX format is accepted."""
        docx_bytes = _make_docx_bytes(num_paragraphs=5, chars_per_para=100)
        result = validate("document.docx", docx_bytes)
        assert result.valid is True
        assert result.error is None

    def test_accepts_md(self):
        """Markdown format is accepted."""
        md_bytes = _make_md_bytes(num_chars=500)
        result = validate("readme.md", md_bytes)
        assert result.valid is True
        assert result.error is None

    def test_rejects_txt(self):
        """TXT format is rejected."""
        result = validate("document.txt", b"some text")
        assert result.valid is False
        assert "Unsupported file format" in result.error

    def test_rejects_xlsx(self):
        """XLSX format is rejected."""
        result = validate("spreadsheet.xlsx", b"fake data")
        assert result.valid is False
        assert "Unsupported file format" in result.error

    def test_rejects_pptx(self):
        """PPTX format is rejected."""
        result = validate("presentation.pptx", b"fake data")
        assert result.valid is False
        assert "Unsupported file format" in result.error

    def test_rejects_no_extension(self):
        """Files without extension are rejected."""
        result = validate("noextension", b"data")
        assert result.valid is False
        assert "Unsupported file format" in result.error


# --- Page Count Validation Tests ---


class TestValidatePageCount:
    """Tests for page count validation.

    Requirements: 1.7
    """

    def test_accepts_pdf_within_limit(self):
        """PDF within 20 pages is accepted."""
        pdf_bytes = _make_pdf_bytes(num_pages=10)
        result = validate("doc.pdf", pdf_bytes)
        assert result.valid is True

    def test_accepts_pdf_at_limit(self):
        """PDF at exactly 20 pages is accepted."""
        pdf_bytes = _make_pdf_bytes(num_pages=20)
        result = validate("doc.pdf", pdf_bytes)
        assert result.valid is True

    def test_rejects_pdf_over_limit(self):
        """PDF exceeding 20 pages is rejected."""
        pdf_bytes = _make_pdf_bytes(num_pages=21)
        result = validate("doc.pdf", pdf_bytes)
        assert result.valid is False
        assert "exceeds" in result.error
        assert "20" in result.error

    def test_vendor_accepts_up_to_30_pages(self):
        """Vendor proposals up to 30 pages are accepted."""
        pdf_bytes = _make_pdf_bytes(num_pages=25)
        result = validate("proposal.pdf", pdf_bytes, is_vendor=True)
        assert result.valid is True

    def test_vendor_rejects_over_30_pages(self):
        """Vendor proposals exceeding 30 pages are rejected."""
        pdf_bytes = _make_pdf_bytes(num_pages=31)
        result = validate("proposal.pdf", pdf_bytes, is_vendor=True)
        assert result.valid is False
        assert "exceeds" in result.error
        assert "30" in result.error

    def test_md_page_count_by_character_count(self):
        """Markdown page count is estimated by character count (~3000 chars/page)."""
        # 6000 chars should be ~2 pages
        md_bytes = _make_md_bytes(num_chars=6000)
        result = validate("doc.md", md_bytes)
        assert result.valid is True

    def test_md_exceeding_limit(self):
        """Markdown file exceeding the page limit is rejected."""
        # 21 * 3000 chars = 63000 chars -> 21 pages
        md_bytes = _make_md_bytes(num_chars=63000)
        result = validate("doc.md", md_bytes)
        assert result.valid is False
        assert "exceeds" in result.error

    def test_docx_page_count_by_paragraph_density(self):
        """DOCX page count is estimated by character density."""
        # 10 paragraphs * 300 chars = 3000 chars -> ~1 page
        docx_bytes = _make_docx_bytes(num_paragraphs=10, chars_per_para=300)
        result = validate("doc.docx", docx_bytes)
        assert result.valid is True


# --- Text Extraction Tests ---


class TestExtractText:
    """Tests for text extraction.

    Requirements: 1.5
    """

    def test_extract_pdf_text(self):
        """PDF text extraction returns content from pages."""
        # Create a PDF with actual text content using reportlab-like approach
        # PyPDF2's blank pages don't have text, so we test the function exists
        # and handles empty content gracefully
        pdf_bytes = _make_pdf_bytes(num_pages=1)
        text = extract_text(pdf_bytes, "test.pdf")
        # Blank pages produce empty text
        assert isinstance(text, str)

    def test_extract_docx_text(self):
        """DOCX text extraction returns paragraph content."""
        docx_bytes = _make_docx_bytes(num_paragraphs=3, chars_per_para=50)
        text = extract_text(docx_bytes, "test.docx")
        assert isinstance(text, str)
        assert len(text) > 0
        # Each paragraph has 50 'A' chars
        assert "A" * 50 in text

    def test_extract_md_text(self):
        """Markdown text extraction returns raw content."""
        content = "# Header\n\nSome paragraph text here.\n"
        md_bytes = content.encode("utf-8")
        text = extract_text(md_bytes, "readme.md")
        assert text == content

    def test_extract_unsupported_format_raises(self):
        """Unsupported format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported file format"):
            extract_text(b"data", "file.txt")


# --- Tier Classification Tests ---


class TestClassifyTier:
    """Tests for tier classification logic.

    Requirements: 1.1, 1.2, 1.3
    """

    def test_brd_prd_only_is_tier_1(self):
        """BRD + PRD → Tier 1.

        Requirements: 1.1
        """
        docs = {
            "brd": _make_extracted_doc("brd.pdf", "pdf"),
            "prd": _make_extracted_doc("prd.pdf", "pdf"),
            "hld": None,
            "dependent_docs": None,
        }
        assert classify_tier(docs) == 1

    def test_brd_prd_hld_is_tier_2(self):
        """BRD + PRD + HLD → Tier 2.

        Requirements: 1.2
        """
        docs = {
            "brd": _make_extracted_doc("brd.pdf", "pdf"),
            "prd": _make_extracted_doc("prd.pdf", "pdf"),
            "hld": _make_extracted_doc("hld.pdf", "pdf"),
            "dependent_docs": None,
        }
        assert classify_tier(docs) == 2

    def test_brd_prd_hld_dependent_is_tier_3(self):
        """BRD + PRD + HLD + DependentDocs → Tier 3.

        Requirements: 1.3
        """
        docs = {
            "brd": _make_extracted_doc("brd.pdf", "pdf"),
            "prd": _make_extracted_doc("prd.pdf", "pdf"),
            "hld": _make_extracted_doc("hld.pdf", "pdf"),
            "dependent_docs": [_make_extracted_doc("dep.md", "md")],
        }
        assert classify_tier(docs) == 3

    def test_empty_dependent_docs_list_is_tier_2(self):
        """BRD + PRD + HLD + empty DependentDocs list → Tier 2."""
        docs = {
            "brd": _make_extracted_doc("brd.pdf", "pdf"),
            "prd": _make_extracted_doc("prd.pdf", "pdf"),
            "hld": _make_extracted_doc("hld.pdf", "pdf"),
            "dependent_docs": [],
        }
        assert classify_tier(docs) == 2

    def test_tier_independent_of_format(self):
        """Tier is determined by document types, not format."""
        # Using different formats for documents
        docs_pdf = {
            "brd": _make_extracted_doc("brd.pdf", "pdf"),
            "prd": _make_extracted_doc("prd.pdf", "pdf"),
            "hld": None,
            "dependent_docs": None,
        }
        docs_md = {
            "brd": _make_extracted_doc("brd.md", "md"),
            "prd": _make_extracted_doc("prd.md", "md"),
            "hld": None,
            "dependent_docs": None,
        }
        assert classify_tier(docs_pdf) == classify_tier(docs_md)

    def test_tier_independent_of_page_count(self):
        """Tier is determined by document types, not page count."""
        docs_small = {
            "brd": _make_extracted_doc("brd.pdf", "pdf", page_count=1),
            "prd": _make_extracted_doc("prd.pdf", "pdf", page_count=1),
            "hld": _make_extracted_doc("hld.pdf", "pdf", page_count=1),
            "dependent_docs": None,
        }
        docs_large = {
            "brd": _make_extracted_doc("brd.pdf", "pdf", page_count=20),
            "prd": _make_extracted_doc("prd.pdf", "pdf", page_count=20),
            "hld": _make_extracted_doc("hld.pdf", "pdf", page_count=20),
            "dependent_docs": None,
        }
        assert classify_tier(docs_small) == classify_tier(docs_large) == 2

    def test_multiple_dependent_docs_is_tier_3(self):
        """Multiple dependent docs still classify as Tier 3."""
        docs = {
            "brd": _make_extracted_doc("brd.pdf", "pdf"),
            "prd": _make_extracted_doc("prd.docx", "docx"),
            "hld": _make_extracted_doc("hld.md", "md"),
            "dependent_docs": [
                _make_extracted_doc("dep1.pdf", "pdf"),
                _make_extracted_doc("dep2.md", "md"),
                _make_extracted_doc("dep3.docx", "docx"),
            ],
        }
        assert classify_tier(docs) == 3


# --- Document Set Validation Tests ---


class TestValidateDocumentSet:
    """Tests for document set validation (mandatory BRD + PRD check).

    Requirements: 1.4
    """

    def test_accepts_brd_and_prd(self):
        """Accepts document set with both BRD and PRD."""
        docs = {
            "brd": _make_extracted_doc("brd.pdf", "pdf"),
            "prd": _make_extracted_doc("prd.pdf", "pdf"),
        }
        result = validate_document_set(docs)
        assert result.valid is True
        assert result.error is None

    def test_rejects_missing_both_brd_and_prd(self):
        """Rejects document set missing both BRD and PRD."""
        docs = {"brd": None, "prd": None}
        result = validate_document_set(docs)
        assert result.valid is False
        assert "BRD" in result.error
        assert "PRD" in result.error

    def test_rejects_missing_brd(self):
        """Rejects document set missing BRD only."""
        docs = {
            "brd": None,
            "prd": _make_extracted_doc("prd.pdf", "pdf"),
        }
        result = validate_document_set(docs)
        assert result.valid is False
        assert "BRD" in result.error

    def test_rejects_missing_prd(self):
        """Rejects document set missing PRD only."""
        docs = {
            "brd": _make_extracted_doc("brd.pdf", "pdf"),
            "prd": None,
        }
        result = validate_document_set(docs)
        assert result.valid is False
        assert "PRD" in result.error

    def test_accepts_with_optional_hld(self):
        """Accepts when BRD, PRD, and HLD are present."""
        docs = {
            "brd": _make_extracted_doc("brd.pdf", "pdf"),
            "prd": _make_extracted_doc("prd.pdf", "pdf"),
            "hld": _make_extracted_doc("hld.pdf", "pdf"),
        }
        result = validate_document_set(docs)
        assert result.valid is True


# --- Page Count Helper Tests ---


class TestPageCounting:
    """Tests for page count estimation helpers."""

    def test_pdf_page_count(self):
        """PDF page count matches actual number of pages."""
        pdf_bytes = _make_pdf_bytes(num_pages=5)
        count = _count_pdf_pages(pdf_bytes)
        assert count == 5

    def test_md_page_count_minimum_one(self):
        """Markdown always has at least 1 page."""
        md_bytes = b"x"  # Very short content
        count = _count_md_pages(md_bytes)
        assert count == 1

    def test_md_page_count_scales_with_content(self):
        """Markdown page count increases with content length."""
        # 9000 chars → 3 pages (at 3000 chars/page)
        md_bytes = ("x" * 9000).encode("utf-8")
        count = _count_md_pages(md_bytes)
        assert count == 3

    def test_docx_page_count_minimum_one(self):
        """DOCX always has at least 1 page."""
        docx_bytes = _make_docx_bytes(num_paragraphs=1, chars_per_para=10)
        count = _count_docx_pages(docx_bytes)
        assert count == 1

    def test_docx_page_count_scales_with_content(self):
        """DOCX page count increases with paragraph density."""
        # 30 paragraphs * 300 chars = 9000 chars → ~3 pages
        docx_bytes = _make_docx_bytes(num_paragraphs=30, chars_per_para=300)
        count = _count_docx_pages(docx_bytes)
        assert count == 3
