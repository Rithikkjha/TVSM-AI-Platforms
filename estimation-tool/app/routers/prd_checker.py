"""PRD/BRD Completeness Checker API."""
import json
import logging
import os
import re
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from app.middleware.auth import AuthenticatedUser, get_current_user
from app.services.document_readiness import assess_document_readiness, DocumentReadinessResult
from app.services.document_processor import extract_text, extract_text_markdown
from app.services.sharepoint_client import SharePointClient, FOLDER_PRD_CHECK, FOLDER_PRD_CHECK_AUDIT
from app.services.slm_engine import SLMEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prd-check", tags=["PRD Checker"])

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "config", "templates"
)

# Placeholder patterns for quality checking
PLACEHOLDER_PATTERNS = [
    r'\bTBD\b', r'\bTBC\b', r'\bN/A\b', r'\bXX\b', r'\bYY\b',
    r'<\s*Name\s*>', r'<\s*Yes/No\s*>', r'<\s*\w+\s*>',
    r'\bTo be decided\b', r'\bTo be confirmed\b', r'\bPending\b',
    r'\bPlaceholder\b', r'\[.*?\]',
]


def check_section_quality(section_text: str) -> dict:
    """Check a section's content quality.

    Returns:
        dict with keys:
            status: 'filled', 'placeholder', 'insufficient', or 'missing'
            issues: list of specific problems found
    """
    if not section_text or not section_text.strip():
        return {"status": "missing", "issues": ["Section is empty"]}

    issues = []

    # Check for placeholder patterns
    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, section_text, re.IGNORECASE)
        if matches:
            issues.append(f"Contains placeholder: {matches[0]}")

    # Check minimum content length
    if len(section_text.strip()) < 20:
        issues.append("Insufficient detail (less than 20 characters)")

    if issues and any('placeholder' in i.lower() for i in issues):
        return {"status": "placeholder", "issues": issues}
    elif issues:
        return {"status": "insufficient", "issues": issues}

    return {"status": "filled", "issues": []}


async def _ensure_local_template(doc_type: str) -> bool:
    """Ensure the local template cache is populated.

    If local cache is missing, attempts to download from SharePoint.

    Returns:
        True if local sections JSON exists (either already or after download).
    """
    json_path = os.path.join(TEMPLATES_DIR, f"{doc_type}_sections.json")
    if os.path.exists(json_path):
        return True

    # Try to pull from SharePoint
    try:
        sp = SharePointClient()
        content = await sp.download_template_sections(doc_type)
        if content:
            os.makedirs(TEMPLATES_DIR, exist_ok=True)
            with open(json_path, "wb") as f:
                f.write(content)
            logger.info(f"Cached template sections from SharePoint: {doc_type}")
            return True
    except Exception as e:
        logger.warning(f"Could not fetch template from SharePoint for {doc_type}: {e}")

    return False


@router.post("/template-upload")
async def upload_template(
    template_file: UploadFile = File(...),
    doc_type: str = Form("prd"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Upload a template document for completeness checking.

    Accepts a .docx or .pdf template file and extracts section headings from it.
    The extracted sections are saved locally (cache) and persisted to SharePoint.
    """
    if not template_file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided."
        )

    allowed_exts = ('.docx', '.pdf')
    if not any(template_file.filename.lower().endswith(ext) for ext in allowed_exts):
        raise HTTPException(
            status_code=400,
            detail="Only .docx and .pdf template files are supported."
        )

    if doc_type not in ('prd', 'brd', 'hld', 'lld'):
        raise HTTPException(
            status_code=400,
            detail="doc_type must be one of: prd, brd, hld, lld"
        )

    os.makedirs(TEMPLATES_DIR, exist_ok=True)

    file_bytes = await template_file.read()

    # Extract sections from the template
    from app.services.template_extractor import extract_template_sections
    sections = extract_template_sections(file_bytes, template_file.filename)

    if not sections:
        raise HTTPException(
            status_code=400,
            detail="Could not extract any sections from the template. "
                   "Ensure it has headings or bold section titles."
        )

    # Save locally (cache)
    file_ext = template_file.filename.rsplit('.', 1)[-1].lower()
    filepath = os.path.join(TEMPLATES_DIR, f"{doc_type}_template.{file_ext}")
    with open(filepath, "wb") as f:
        f.write(file_bytes)

    sections_data = [
        {
            "name": s.name,
            "level": s.level,
            "has_table": s.has_table,
            "expected_content": s.expected_content,
            "table_columns": s.table_columns,
        }
        for s in sections
    ]
    json_path = os.path.join(TEMPLATES_DIR, f"{doc_type}_sections.json")
    with open(json_path, "w") as f:
        json.dump(sections_data, f, indent=2)

    # Persist to SharePoint (non-blocking — don't fail the request if SP is down)
    try:
        sp = SharePointClient()
        await sp.upload_template(doc_type, file_bytes, file_ext)
        sections_json_bytes = json.dumps(sections_data, indent=2).encode("utf-8")
        await sp.upload_template_sections(doc_type, sections_json_bytes)
        logger.info(f"Template persisted to SharePoint: {doc_type}")
    except Exception as e:
        logger.warning(f"Could not persist template to SharePoint (saved locally): {e}")

    return {
        "message": f"Template uploaded successfully for {doc_type.upper()}",
        "sections_found": len(sections),
        "sections": [s.name for s in sections]
    }


@router.delete("/template/{doc_type}")
async def delete_template(
    doc_type: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Remove an uploaded template for a document type.

    Deletes local cache and attempts to remove from SharePoint.
    Falls back to doc_templates.json after deletion.
    """
    if doc_type not in ('prd', 'brd', 'hld', 'lld'):
        raise HTTPException(
            status_code=400,
            detail="doc_type must be one of: prd, brd, hld, lld"
        )

    # Remove local files
    removed = False
    for ext in ('docx', 'pdf'):
        filepath = os.path.join(TEMPLATES_DIR, f"{doc_type}_template.{ext}")
        if os.path.exists(filepath):
            os.remove(filepath)
            removed = True

    json_path = os.path.join(TEMPLATES_DIR, f"{doc_type}_sections.json")
    if os.path.exists(json_path):
        os.remove(json_path)
        removed = True

    # Try to remove from SharePoint as well
    try:
        sp = SharePointClient()
        await sp.delete_template(doc_type)
        logger.info(f"Template removed from SharePoint: {doc_type}")
    except Exception as e:
        logger.warning(f"Could not remove template from SharePoint: {e}")

    if not removed:
        return {"message": f"No uploaded template found for {doc_type.upper()}"}

    return {"message": f"Template removed for {doc_type.upper()}. Will fall back to default config."}


@router.get("/template/{doc_type}")
async def get_template_info(
    doc_type: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get the current template sections for a document type.

    Checks local cache first; if missing, pulls from SharePoint.
    """
    if doc_type not in ('prd', 'brd', 'hld', 'lld'):
        raise HTTPException(
            status_code=400,
            detail="doc_type must be one of: prd, brd, hld, lld"
        )

    # Ensure local cache is populated (pulls from SharePoint if needed)
    await _ensure_local_template(doc_type)

    json_path = os.path.join(TEMPLATES_DIR, f"{doc_type}_sections.json")
    if not os.path.exists(json_path):
        return {"doc_type": doc_type, "has_template": False, "sections": []}

    with open(json_path, "r") as f:
        sections = json.load(f)

    return {"doc_type": doc_type, "has_template": True, "sections": sections}


@router.post("/analyze")
async def analyze_document(
    doc_file: UploadFile = File(...),
    doc_type: str = Form("prd"),  # 'prd', 'brd', 'hld', or 'lld'
    user: AuthenticatedUser = Depends(get_current_user),
) -> DocumentReadinessResult:
    """Analyze a document for completeness against the standard template.

    Uses uploaded template if available, otherwise falls back to
    config/doc_templates.json. Ensures local template cache is fresh.
    Validates that the document matches the selected type before analysis.
    """
    # Ensure we have the latest template cached locally
    await _ensure_local_template(doc_type)

    file_bytes = await doc_file.read()
    # Markdown-formatted tables help the SLM recognize populated vs empty tables
    text = extract_text_markdown(file_bytes, doc_file.filename)

    # Validate document type matches what was selected
    doc_type_mismatch = _check_doc_type_match(text, doc_type)
    if doc_type_mismatch:
        raise HTTPException(
            status_code=400,
            detail=doc_type_mismatch
        )

    slm_engine = SLMEngine()
    await slm_engine.load_model()

    result = await assess_document_readiness(text, doc_type, slm_engine)

    # Record audit log to dedicated PRD check audit file
    try:
        await _record_prd_check_audit(
            user=user,
            doc_type=doc_type,
            filename=doc_file.filename or "unknown",
            result=result,
        )
    except Exception as e:
        logger.warning(f"Failed to record PRD check audit: {e}")

    return result


async def _record_prd_check_audit(
    user: AuthenticatedUser,
    doc_type: str,
    filename: str,
    result: DocumentReadinessResult,
) -> None:
    """Record a PRD/BRD/HLD completeness check in a dedicated audit file.

    Writes to PrdCheckAudit_YYYY-MM.xlsx (separate from estimation audit).
    """
    import uuid
    from datetime import datetime, timezone

    sp = SharePointClient()
    timestamp = datetime.now(timezone.utc).isoformat()
    month = timestamp[:7]  # YYYY-MM

    audit_filename = f"{FOLDER_PRD_CHECK_AUDIT}/PrdCheckAudit_{month}.xlsx"

    # Ensure the file exists (create if not)
    if not await sp.file_exists(audit_filename):
        await _create_prd_audit_file(sp, audit_filename)

    audit_id = str(uuid.uuid4())
    filename_safe = filename[:80]

    filled = len([s for s in result.sections if s.status == "filled"])
    placeholder = len([s for s in result.sections if s.status == "placeholder"])
    missing_count = len([s for s in result.sections if s.status == "missing"])
    total = len(result.sections)

    row = [
        audit_id,
        timestamp,
        user.identity.email,
        user.identity.displayName,
        doc_type.upper(),
        filename_safe,
        result.readinessPercent,
        filled,
        placeholder,
        missing_count,
        total,
        json.dumps([s.name for s in result.sections if s.status == "missing"][:10]),
        json.dumps(result.model_dump()),
    ]

    await sp.append_row(audit_filename, "Sheet1", row)
    logger.info(f"Recorded PRD check audit: {audit_id} for {filename_safe} ({doc_type})")


async def _create_prd_audit_file(sp: SharePointClient, filename: str) -> None:
    """Create the PRD check audit Excel file with headers."""
    import openpyxl
    import io

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append([
        "AuditId", "Timestamp", "UserEmail", "UserName", "DocType",
        "Filename", "ReadinessPercent", "FilledSections", "PlaceholderSections",
        "MissingSections", "TotalSections", "MissingSectionNames", "ResultJSON"
    ])
    buffer = io.BytesIO()
    wb.save(buffer)
    await sp._upload_file(filename, buffer.getvalue())


@router.get("/audit")
async def get_prd_check_audit(
    month: Optional[str] = Query(None, description="Month filter in YYYY-MM format"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get PRD completeness check audit history for a given month."""
    from datetime import datetime, timezone

    sp = SharePointClient()
    target_month = month or datetime.now(timezone.utc).strftime("%Y-%m")
    audit_filename = f"{FOLDER_PRD_CHECK_AUDIT}/PrdCheckAudit_{target_month}.xlsx"

    try:
        if not await sp.file_exists(audit_filename):
            return {"entries": [], "month": target_month}

        rows = await sp.read_workbook(audit_filename, "Sheet1")
        if not rows or len(rows) <= 1:
            return {"entries": [], "month": target_month}

        # Skip header row
        headers = rows[0]
        entries = []
        for row in rows[1:]:
            if len(row) >= 11:
                entries.append({
                    "auditId": row[0],
                    "timestamp": row[1],
                    "userEmail": row[2],
                    "userName": row[3],
                    "docType": row[4],
                    "filename": row[5],
                    "readinessPercent": row[6],
                    "filledSections": row[7],
                    "placeholderSections": row[8],
                    "missingSections": row[9],
                    "totalSections": row[10],
                    "missingSectionNames": row[11] if len(row) > 11 else "[]",
                    "resultJSON": row[12] if len(row) > 12 else None,
                })

        # Reverse to show most recent first
        entries.reverse()
        return {"entries": entries, "month": target_month}

    except Exception as e:
        logger.warning(f"Failed to read PRD check audit: {e}")
        return {"entries": []}


def _check_doc_type_match(text: str, expected_type: str) -> Optional[str]:
    """Quick heuristic check to verify document matches the selected type.

    Looks for strong indicators of document type in the first portion of text.
    Returns an error message if mismatch detected, None if OK.
    """
    # Only check the first 3000 chars for type indicators
    sample = text[:3000].lower()

    type_indicators = {
        "prd": {
            "positive": ["product requirement", "prd", "functional requirement", "user persona",
                         "acceptance criteria", "user story", "use case", "product objective"],
            "negative_if_only": ["architecture", "hld", "high-level design", "low-level design",
                                 "class diagram", "sequence diagram", "er diagram"]
        },
        "brd": {
            "positive": ["business requirement", "brd", "business objective", "executive summary",
                         "business impact", "roi", "business case"],
            "negative_if_only": ["architecture", "hld", "lld", "class diagram", "api contract"]
        },
        "hld": {
            "positive": ["high-level design", "hld", "architecture", "system design",
                         "proposed architecture", "current architecture", "deployment"],
            "negative_if_only": ["prd", "product requirement", "user story", "acceptance criteria",
                                 "class diagram", "er diagram", "low-level"]
        },
        "lld": {
            "positive": ["low-level design", "lld", "class diagram", "sequence diagram",
                         "er diagram", "api contract", "database schema", "module design"],
            "negative_if_only": ["prd", "product requirement", "user story", "business requirement",
                                 "high-level design", "proposed architecture"]
        },
    }

    indicators = type_indicators.get(expected_type)
    if not indicators:
        return None

    # Count positive signals for expected type
    positive_hits = sum(1 for kw in indicators["positive"] if kw in sample)

    # Count signals that suggest it's a different type
    negative_hits = sum(1 for kw in indicators["negative_if_only"] if kw in sample)

    # If strong negative signals and no positive signals, likely wrong type
    if negative_hits >= 2 and positive_hits == 0:
        type_labels = {"prd": "PRD", "brd": "BRD", "hld": "HLD", "lld": "LLD"}
        expected_label = type_labels.get(expected_type, expected_type.upper())

        # Try to guess what it actually is
        detected_type = None
        for dtype, ind in type_indicators.items():
            if dtype == expected_type:
                continue
            hits = sum(1 for kw in ind["positive"] if kw in sample)
            if hits >= 2:
                detected_type = type_labels.get(dtype, dtype.upper())
                break

        if detected_type:
            return (
                f"Document mismatch: You selected '{expected_label}' but the uploaded document "
                f"appears to be a {detected_type}. Please select the correct document type."
            )
        else:
            return (
                f"Document mismatch: The uploaded document doesn't appear to be a {expected_label}. "
                f"Please verify you've selected the correct document type."
            )

    return None
