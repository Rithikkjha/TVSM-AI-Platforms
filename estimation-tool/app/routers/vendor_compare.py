"""Standalone Vendor Comparison API router.

Compares vendor proposals against each other (no estimation dependency).
Stores results in the Vendors/ SharePoint folder.

Endpoints:
- POST /api/vendors/compare — upload proposals and run comparison
- GET /api/vendors/comparisons — list past comparisons
"""

import io
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from typing import Optional

from app.middleware.auth import AuthenticatedUser, get_current_user
from app.services.document_processor import extract_text_markdown
from app.services.sharepoint_client import SharePointClient, FOLDER_VENDORS, FOLDER_VENDORS_RESULTS, SharePointError
from app.services.slm_engine import SLMEngine, SLMOptions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vendors", tags=["Vendor Compare"])

COMPARISON_INDEX = f"{FOLDER_VENDORS}/ComparisonIndex.xlsx"
INDEX_HEADERS = ["ComparisonId", "Name", "VendorCount", "Winner", "OwnerName", "CreatedAt"]


# --- Response Models ---

class VendorResult(BaseModel):
    vendor_name: str
    cost: float
    timeline: float
    team_size: Optional[int] = None
    strengths: list[str] = []
    risks: list[str] = []
    scope_coverage: str = ""
    tech_stack: list[str] = []
    support_warranty: str = ""
    score: float = 0.0
    score_reasoning: str = ""


class ComparisonResult(BaseModel):
    comparison_id: str
    name: str
    vendors: list[VendorResult]
    recommendation: str
    created_at: str


class ComparisonListItem(BaseModel):
    comparison_id: str
    name: str
    vendor_count: int
    winner: str
    owner: str
    created_at: str


class ComparisonListResponse(BaseModel):
    comparisons: list[ComparisonListItem]
    total: int


# --- Endpoints ---

@router.post("/compare")
async def compare_vendors(
    comparison_name: str = Form(...),
    vendor_names: str = Form(...),  # comma-separated
    vendor_costs: str = Form(...),  # comma-separated
    vendor_timelines: str = Form(...),  # comma-separated
    vendor_teams: str = Form(""),  # comma-separated, optional
    vendor_files: list[UploadFile] = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
) -> ComparisonResult:
    """Compare vendor proposals side by side.

    Uploads vendor docs, extracts key info via SLM, and produces a ranked comparison.
    """
    names = [n.strip() for n in vendor_names.split(",") if n.strip()]
    costs = [float(c.strip()) for c in vendor_costs.split(",") if c.strip()]
    timelines = [float(t.strip()) for t in vendor_timelines.split(",") if t.strip()]
    teams_raw = [t.strip() for t in vendor_teams.split(",")]
    teams = [int(t) if t and t.isdigit() else None for t in teams_raw]

    if len(names) < 2:
        raise HTTPException(status_code=400, detail="At least 2 vendors required")
    if len(vendor_files) < 2:
        raise HTTPException(status_code=400, detail="Upload at least 2 vendor documents")
    if len(names) != len(costs) or len(names) != len(timelines):
        raise HTTPException(status_code=400, detail="Vendor names, costs, and timelines must have same count")

    # Extract text from each vendor doc
    vendor_texts = []
    for f in vendor_files:
        content = await f.read()
        try:
            text = extract_text_markdown(content, f.filename or "doc.pdf")
            vendor_texts.append(text[:12000])  # Cap for context window
        except Exception as e:
            vendor_texts.append(f"[Could not extract: {e}]")

    # SLM analysis for each vendor
    slm = SLMEngine()
    await slm.load_model()

    vendor_results: list[VendorResult] = []

    for i, (name, cost, timeline) in enumerate(zip(names, costs, timelines)):
        team = teams[i] if i < len(teams) else None
        doc_text = vendor_texts[i] if i < len(vendor_texts) else ""

        prompt = f"""Analyze this vendor proposal for "{name}" and extract key insights.

VENDOR PROPOSAL:
{doc_text}

Extract in JSON format:
{{
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "risks": ["risk 1", "risk 2"],
  "scope_coverage": "brief summary of what the vendor covers",
  "tech_stack": ["tech 1", "tech 2"],
  "support_warranty": "summary of support model, warranty terms, SLA commitments, maintenance included",
  "overall_score": <1-10 integer based on quality of proposal>,
  "score_reasoning": "1-2 sentence explanation of why this score was given, referencing specific proposal strengths or weaknesses including support/warranty terms"
}}

Scoring guide (consider ALL these factors):
- Scope coverage and functional fit
- Technical approach and architecture
- Team composition and experience
- Timeline feasibility
- Support model, warranty period, SLA commitments, post-go-live support
- Risk mitigation and escalation process
- 9-10: Comprehensive proposal with clear scope, strong support/warranty, proven references
- 7-8: Good proposal covering most areas but missing some detail
- 5-6: Average proposal with significant gaps
- 3-4: Weak proposal lacking detail or support commitments
- 1-2: Inadequate proposal

Respond ONLY with valid JSON."""

        try:
            resp = await slm.inference(prompt, options=SLMOptions(temperature=0.1, maxTokens=1024))
            # Parse JSON
            content = resp.content.strip()
            if "```" in content:
                content = content.split("```")[1].split("```")[0]
                if content.startswith("json"):
                    content = content[4:]
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
            else:
                data = {}
        except Exception as e:
            logger.warning(f"SLM analysis failed for vendor {name}: {e}")
            data = {}

        vendor_results.append(VendorResult(
            vendor_name=name,
            cost=cost,
            timeline=timeline,
            team_size=team,
            strengths=data.get("strengths", [])[:5],
            risks=data.get("risks", [])[:5],
            scope_coverage=data.get("scope_coverage", ""),
            tech_stack=data.get("tech_stack", [])[:8],
            support_warranty=str(data.get("support_warranty", "")),
            score=float(data.get("overall_score", 5)),
            score_reasoning=str(data.get("score_reasoning", "")),
        ))

    # Rank by score (highest first), with cost as tiebreaker (lower is better)
    vendor_results.sort(key=lambda v: (-v.score, v.cost))
    winner = vendor_results[0].vendor_name if vendor_results else "N/A"

    comparison_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Persist to SharePoint
    try:
        sp = SharePointClient()
        # Ensure index exists
        if not await sp.file_exists(COMPARISON_INDEX):
            await sp._create_excel_file(COMPARISON_INDEX, INDEX_HEADERS)

        await sp.append_row(COMPARISON_INDEX, "Sheet1", [
            comparison_id, comparison_name, len(names), winner,
            user.identity.displayName, now
        ])

        # Save full result as JSON for later viewing
        result_data = {
            "comparison_id": comparison_id,
            "name": comparison_name,
            "recommendation": "",  # Will be set below
            "created_at": now,
            "vendors": [v.__dict__ if hasattr(v, '__dict__') else v.model_dump() for v in vendor_results],
        }
    except Exception as e:
        logger.warning(f"Failed to persist vendor comparison: {e}")
        result_data = None

    # Build recommendation with reasoning
    if len(vendor_results) >= 2 and vendor_results[0].score == vendor_results[1].score:
        recommendation = (
            f"Recommended: {winner} (Score: {vendor_results[0].score}/10 — tied with "
            f"{vendor_results[1].vendor_name}, selected on lower cost: "
            f"\u20b9{vendor_results[0].cost:,.0f} vs \u20b9{vendor_results[1].cost:,.0f})"
        )
    else:
        recommendation = (
            f"Recommended: {winner} (Score: {vendor_results[0].score}/10, "
            f"Cost: \u20b9{vendor_results[0].cost:,.0f}, Timeline: {vendor_results[0].timeline} months)"
        )

    # Persist full result JSON for history viewing
    if result_data:
        try:
            result_data["recommendation"] = recommendation
            result_json = json.dumps(result_data).encode("utf-8")
            result_path = f"{FOLDER_VENDORS_RESULTS}/{comparison_id}.json"
            await sp._ensure_authenticated()
            client = await sp._get_http_client()
            url = f"{sp.GRAPH_API_BASE}/drives/{sp.drive_id}/root:/{result_path}:/content"
            headers = {"Authorization": f"Bearer {sp._access_token}", "Content-Type": "application/json"}
            await client.put(url, headers=headers, content=result_json)
        except Exception as e:
            logger.warning(f"Failed to save comparison result JSON: {e}")

    return ComparisonResult(
        comparison_id=comparison_id,
        name=comparison_name,
        vendors=vendor_results,
        recommendation=recommendation,
        created_at=now,
    )


@router.get("/comparisons")
async def list_comparisons(
    user: AuthenticatedUser = Depends(get_current_user),
) -> ComparisonListResponse:
    """List past vendor comparisons."""
    sp = SharePointClient()
    try:
        if not await sp.file_exists(COMPARISON_INDEX):
            return ComparisonListResponse(comparisons=[], total=0)

        rows = await sp.read_workbook(COMPARISON_INDEX, "Sheet1")
        if not rows or len(rows) < 2:
            return ComparisonListResponse(comparisons=[], total=0)

        items = []
        for row in rows[1:]:
            if not row or not row[0]:
                continue
            items.append(ComparisonListItem(
                comparison_id=str(row[0]),
                name=str(row[1]) if len(row) > 1 and row[1] else "",
                vendor_count=int(row[2]) if len(row) > 2 and row[2] else 0,
                winner=str(row[3]) if len(row) > 3 and row[3] else "",
                owner=str(row[4]) if len(row) > 4 and row[4] else "",
                created_at=str(row[5]) if len(row) > 5 and row[5] else "",
            ))

        items.reverse()  # Most recent first
        return ComparisonListResponse(comparisons=items, total=len(items))
    except SharePointError:
        return ComparisonListResponse(comparisons=[], total=0)


@router.get("/comparisons/{comparison_id}")
async def get_comparison(
    comparison_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ComparisonResult:
    """Get full comparison result by ID."""
    sp = SharePointClient()
    result_path = f"{FOLDER_VENDORS_RESULTS}/{comparison_id}.json"

    try:
        await sp._ensure_authenticated()
        client = await sp._get_http_client()
        url = f"{sp.GRAPH_API_BASE}/drives/{sp.drive_id}/root:/{result_path}:/content"
        headers = {"Authorization": f"Bearer {sp._access_token}"}
        resp = await client.get(url, headers=headers, follow_redirects=True)

        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Comparison result not found")
        if resp.status_code >= 400:
            raise HTTPException(status_code=503, detail="Failed to load comparison")

        data = json.loads(resp.content)

        vendors = [VendorResult(**v) for v in data.get("vendors", [])]
        return ComparisonResult(
            comparison_id=data.get("comparison_id", comparison_id),
            name=data.get("name", ""),
            vendors=vendors,
            recommendation=data.get("recommendation", ""),
            created_at=data.get("created_at", ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load comparison {comparison_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load comparison result")
