"""Estimation API router for the Project Estimation Tool.

Provides endpoints for the full estimation lifecycle:
- POST /api/estimations — generate new estimation (full pipeline)
- GET /api/estimations — query EstimationIndex.xlsx for dashboard listing
- GET /api/estimations/:id — load full estimation detail from monthly file
- GET /api/estimations/:id/audit — return project audit history
- GET /api/estimations/:id/export/pdf — PDF export
- GET /api/estimations/:id/export/json — JSON export

Requirements: 2.1, 2.4, 2.5, 6.1, 6.2, 6.3, 7.2, 18.8, 18.9
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.middleware.auth import (
    AuthenticatedUser,
    get_current_user,
    get_sharepoint_client,
)
from app.models.schemas import (
    AuditEntry,
    AuditGenerationEntry,
    AuditRevisionEntry,
    ConsolidatedVendorView,
    DashboardFilters,
    Domain,
    DocumentSet,
    EstimationIndexEntry,
    EstimationRequest,
    EstimationResult,
    ExtractedDocument,
    InputTier,
    ReEstimationResult,
    ScenarioResult,
    Stream,
    TeamMember,
    VendorComparison,
    VendorProposalInput,
)
from app.services.audit_service import (
    get_project_history,
    get_project_history_all_months,
    record_generation_with_estimation_id,
    record_revision,
)
from app.services.vendor_comparator import (
    analyze_proposal,
    consolidate_comparisons,
)
from app.services.document_processor import (
    classify_tier,
    extract_text,
    extract_text_markdown,
    validate,
    validate_document_set,
)
from app.services.estimation_engine import (
    EstimationError,
    ValidationError,
    generate_estimation,
)
from app.services.sharepoint_client import SharePointClient, FOLDER_ESTIMATIONS, FOLDER_ESTIMATIONS_DATA

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/estimations", tags=["Estimations"])

# --- Estimation Result Cache (LRU, max 50 entries) ---
from collections import OrderedDict

_estimation_cache: OrderedDict[str, "EstimationResult"] = OrderedDict()
_CACHE_MAX_SIZE = 50


def _cache_put(estimation_id: str, result: "EstimationResult") -> None:
    """Store estimation in cache, evicting oldest if full."""
    _estimation_cache[estimation_id] = result
    _estimation_cache.move_to_end(estimation_id)
    while len(_estimation_cache) > _CACHE_MAX_SIZE:
        _estimation_cache.popitem(last=False)


def _cache_get(estimation_id: str) -> Optional["EstimationResult"]:
    """Get estimation from cache, or None if not cached."""
    result = _estimation_cache.get(estimation_id)
    if result:
        _estimation_cache.move_to_end(estimation_id)
    return result


# --- Background Job Store ---

# In-memory store: {job_id: {"status": "processing"|"complete"|"failed", "result": ..., "error": ..., "created_at": datetime}}
_job_store: dict[str, dict[str, Any]] = {}
_JOB_TTL_SECONDS = 30 * 60  # 30 minutes


def _cleanup_expired_jobs() -> None:
    """Remove jobs older than 30 minutes from memory."""
    now = datetime.now(timezone.utc)
    expired = [
        jid for jid, job in _job_store.items()
        if (now - job["created_at"]).total_seconds() > _JOB_TTL_SECONDS
    ]
    for jid in expired:
        del _job_store[jid]


# --- Request/Response Models ---


class EstimationListResponse(BaseModel):
    """Response for listing estimations on the dashboard."""
    estimations: list[EstimationIndexEntry]
    total: int


class EstimationCreateRequest(BaseModel):
    """Request body for creating a new estimation via JSON."""
    projectName: str = Field(..., min_length=1)
    projectDescription: Optional[str] = None
    domain: Domain
    stream: Stream
    brd: ExtractedDocument
    prd: ExtractedDocument
    hld: Optional[ExtractedDocument] = None
    dependentServiceDocs: Optional[list[ExtractedDocument]] = None
    userId: Optional[str] = None


class AuditHistoryResponse(BaseModel):
    """Response for audit history queries."""
    entries: list[AuditEntry]
    total: int


class JobResponse(BaseModel):
    """Response returned immediately when an estimation job is submitted."""
    jobId: str
    status: str = "processing"


class JobStatusResponse(BaseModel):
    """Response for polling a job's status."""
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None


# --- Endpoints ---


@router.post("/upload", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_estimation_upload(
    project_name: str = Form(...),
    project_description: Optional[str] = Form(None),
    domain: str = Form(...),
    stream: str = Form(...),
    additional_context: Optional[str] = Form(None),
    brd_file: UploadFile = File(...),
    prd_file: Optional[UploadFile] = File(None),
    hld_file: Optional[UploadFile] = File(None),
    dep_files: Optional[list[UploadFile]] = File(None),
    user: AuthenticatedUser = Depends(get_current_user),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> JobResponse:
    """Generate estimation from uploaded files (multipart form data).
    
    PRD is optional — if only BRD is provided, produces a Tier 0 (ballpark) estimate.

    Extracts text from DOCX/PDF/MD files server-side using python-docx/PyPDF2.
    This is the preferred endpoint for file uploads from the frontend.
    Launches estimation as a background job and returns immediately with a jobId.
    """

    # Step 1: Read and extract text from uploaded files
    brd_bytes = await brd_file.read()
    brd_text = extract_text(brd_bytes, brd_file.filename)
    brd_readiness_text = extract_text_markdown(brd_bytes, brd_file.filename)
    brd_validation = validate(brd_file.filename, brd_bytes)
    if not brd_validation.valid:
        raise HTTPException(status_code=400, detail=f"BRD: {brd_validation.error}")

    prd_doc = None
    prd_text = ""
    if prd_file and prd_file.filename:
        prd_bytes = await prd_file.read()
        prd_text = extract_text(prd_bytes, prd_file.filename)
        prd_readiness_text = extract_text_markdown(prd_bytes, prd_file.filename)
        prd_validation = validate(prd_file.filename, prd_bytes)
        if not prd_validation.valid:
            raise HTTPException(status_code=400, detail=f"PRD: {prd_validation.error}")
        prd_doc = ExtractedDocument(
            filename=prd_file.filename,
            format=prd_file.filename.rsplit('.', 1)[-1].lower() if '.' in prd_file.filename else 'md',
            pageCount=max(1, len(prd_text) // 3000),
            textContent=prd_text,
            readinessText=prd_readiness_text,
        )

    hld_doc = None
    if hld_file and hld_file.filename:
        hld_bytes = await hld_file.read()
        hld_text = extract_text(hld_bytes, hld_file.filename)
        hld_doc = ExtractedDocument(
            filename=hld_file.filename,
            format=hld_file.filename.rsplit('.', 1)[-1].lower() if '.' in hld_file.filename else 'md',
            pageCount=max(1, len(hld_text) // 3000),
            textContent=hld_text,
        )

    # Process dependent service docs (multiple files)
    dep_docs = None
    if dep_files:
        dep_docs = []
        for dep_file in dep_files:
            if dep_file and dep_file.filename:
                dep_bytes = await dep_file.read()
                dep_text = extract_text(dep_bytes, dep_file.filename)
                dep_docs.append(ExtractedDocument(
                    filename=dep_file.filename,
                    format=dep_file.filename.rsplit('.', 1)[-1].lower() if '.' in dep_file.filename else 'md',
                    pageCount=max(1, len(dep_text) // 3000),
                    textContent=dep_text,
                ))
        if not dep_docs:
            dep_docs = None

    # Build extracted documents
    brd_doc = ExtractedDocument(
        filename=brd_file.filename,
        format=brd_file.filename.rsplit('.', 1)[-1].lower() if '.' in brd_file.filename else 'md',
        pageCount=max(1, len(brd_text) // 3000),
        textContent=brd_text,
        readinessText=brd_readiness_text,
    )

    # Append tribal knowledge / additional context to BRD if provided
    if additional_context:
        brd_doc.textContent += (
            f"\n\n---\n## Additional Context (Tribal Knowledge)\n{additional_context}\n"
        )
    # prd_doc is already built above (or None if no PRD uploaded)

    # Step 2: Classify tier (0 = BRD only, 1 = BRD+PRD, 2 = +HLD, 3 = +Deps)
    documents_dict = {
        "brd": brd_doc,
        "prd": prd_doc,
        "hld": hld_doc,
        "dependent_docs": dep_docs,
    }
    input_tier: InputTier = classify_tier(documents_dict)

    # For BRD-only (no PRD), create a placeholder PRD with BRD content for the estimation engine
    if prd_doc is None:
        prd_doc = ExtractedDocument(
            filename="(no PRD - using BRD content)",
            format="md",
            pageCount=1,
            textContent=f"[No PRD provided. Estimation based on BRD only.]\n\n{brd_text[:5000]}",
        )

    # Step 3: Build request
    document_set = DocumentSet(brd=brd_doc, prd=prd_doc, hld=hld_doc, dependentServiceDocs=dep_docs)

    # Map string domain/stream to enums
    try:
        domain_enum = Domain(domain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")
    try:
        stream_enum = Stream(stream)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stream: {stream}")

    estimation_request = EstimationRequest(
        projectName=project_name,
        projectDescription=project_description,
        domain=domain_enum,
        stream=stream_enum,
        documents=document_set,
        userId=user.corporate_id or user.email,
    )

    # Step 4: Launch estimation as a background job (avoids browser timeout)
    job_id = str(uuid.uuid4())
    _cleanup_expired_jobs()
    _job_store[job_id] = {
        "status": "processing",
        "result": None,
        "error": None,
        "created_at": datetime.now(timezone.utc),
        "project_name": project_name,
    }

    # Collect uploaded document filenames for persistence
    _doc_names: list[str] = []
    if brd_file and brd_file.filename and not brd_file.filename.startswith("no-brd"):
        _doc_names.append(brd_file.filename)
    if prd_file and prd_file.filename:
        _doc_names.append(prd_file.filename)
    if hld_file and hld_file.filename:
        _doc_names.append(hld_file.filename)
    if dep_files:
        for df in dep_files:
            if df and df.filename:
                _doc_names.append(df.filename)

    async def _run_estimation_job():
        """Background coroutine that runs the estimation and updates the job store."""
        from app.services.slm_engine import SLMEngine

        try:
            slm_engine = SLMEngine()
            await slm_engine.load_model()

            result = await generate_estimation(
                request=estimation_request,
                input_tier=input_tier,
                slm_engine=slm_engine,
                sharepoint_client=sharepoint_client,
            )

            # Best-effort: Write to SharePoint
            try:
                await _write_estimation_to_sharepoint(result, user, sharepoint_client, document_names=_doc_names)
            except Exception as exc:
                logger.error(f"Failed to write estimation to SharePoint: {exc}")

            # Best-effort: Audit
            try:
                audit_entry = AuditGenerationEntry(
                    userId=user.corporate_id or user.email,
                    projectName=result.projectName,
                    domain=result.domain,
                    stream=result.stream,
                    inputTier=result.inputTier,
                    estimationValues={
                        "totalEffortPersonDays": result.totalEffortPersonDays,
                        "calendarDuration": result.calendarDuration,
                        "confidenceScore": result.compositeConfidence.overall,
                        "costTotal": result.costProjection.total,
                    },
                    slmModelName=result.slmModelName,
                    timestamp=result.timestamp,
                )
                await record_generation_with_estimation_id(audit_entry, result.id, sharepoint_client)
            except Exception as exc:
                logger.error(f"Failed to record audit entry: {exc}")

            _job_store[job_id]["status"] = "complete"
            _job_store[job_id]["result"] = result.model_dump(mode="json")
            _cache_put(result.id, result)

        except Exception as exc:
            logger.error(f"Background estimation job {job_id} failed: {exc}")
            _job_store[job_id]["status"] = "failed"
            _job_store[job_id]["error"] = str(exc)

    asyncio.create_task(_run_estimation_job())

    return JobResponse(jobId=job_id, status="processing")



class ActiveJobEntry(BaseModel):
    """A single active/recent job entry for dashboard display."""
    jobId: str
    status: str
    projectName: Optional[str] = None
    createdAt: str
    elapsedSeconds: float


class ActiveJobsResponse(BaseModel):
    """Response for listing active/recent jobs."""
    jobs: list[ActiveJobEntry]


@router.get("/jobs", response_model=ActiveJobsResponse)
async def list_active_jobs() -> ActiveJobsResponse:
    """List all active and recent estimation jobs.

    Returns all in-progress, recently completed, and recently failed jobs.
    Used by the dashboard to show real-time job status.
    Automatically cleans up expired jobs (>30 min).
    """
    _cleanup_expired_jobs()
    now = datetime.now(timezone.utc)

    jobs = []
    for job_id, job in _job_store.items():
        elapsed = (now - job["created_at"]).total_seconds()

        # Extract project name from result if available
        project_name = None
        if job.get("result") and isinstance(job["result"], dict):
            project_name = job["result"].get("projectName")
        elif job.get("project_name"):
            project_name = job["project_name"]

        jobs.append(ActiveJobEntry(
            jobId=job_id,
            status=job["status"],
            projectName=project_name,
            createdAt=job["created_at"].isoformat(),
            elapsedSeconds=round(elapsed, 1),
        ))

    # Sort: processing first, then by creation time (newest first)
    jobs.sort(key=lambda j: (0 if j.status == "processing" else 1, -j.elapsedSeconds))

    return ActiveJobsResponse(jobs=jobs)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Poll the status of a background estimation job.

    Returns:
    - {"status": "processing"} while the job is still running
    - {"status": "complete", "result": <EstimationResult>} when finished
    - {"status": "failed", "error": "message"} on failure
    """
    job = _job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found or expired")

    if job["status"] == "processing":
        return JobStatusResponse(status="processing")
    elif job["status"] == "complete":
        return JobStatusResponse(status="complete", result=job["result"])
    else:
        return JobStatusResponse(status="failed", error=job["error"])


@router.post("", response_model=EstimationResult, status_code=status.HTTP_201_CREATED)
async def create_estimation(
    request: EstimationCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> EstimationResult:
    """Generate a new estimation through the full pipeline.

    Pipeline: validate → document processing → estimation → write to SharePoint → audit → return JSON.

    Requirements: 2.1, 2.4, 6.1, 6.2, 6.3, 7.2, 18.8, 18.9
    """
    from app.services.slm_engine import SLMEngine

    # Step 1: Build document set and validate
    documents_dict = {
        "brd": request.brd,
        "prd": request.prd,
        "hld": request.hld,
        "dependent_docs": request.dependentServiceDocs,
    }

    doc_validation = validate_document_set(documents_dict)
    if not doc_validation.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=doc_validation.error,
        )

    # Step 2: Classify input tier
    input_tier: InputTier = classify_tier(documents_dict)

    # Step 3: Build EstimationRequest
    document_set = DocumentSet(
        brd=request.brd,
        prd=request.prd,
        hld=request.hld,
        dependentServiceDocs=request.dependentServiceDocs,
    )

    estimation_request = EstimationRequest(
        projectName=request.projectName,
        projectDescription=request.projectDescription,
        domain=request.domain,
        stream=request.stream,
        documents=document_set,
        userId=user.corporate_id or user.email,
    )

    # Step 4: Run estimation engine
    slm_engine = SLMEngine()
    try:
        await slm_engine.load_model()
    except Exception as exc:
        logger.error(f"SLM engine failed to load: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Estimation service temporarily unavailable. The SLM engine could not be loaded. Please retry or contact admin.",
        )

    try:
        result = await generate_estimation(
            request=estimation_request,
            input_tier=input_tier,
            slm_engine=slm_engine,
            sharepoint_client=sharepoint_client,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except EstimationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    # Step 5: Write results to SharePoint
    _doc_names_api: list[str] = []
    if request.brd and request.brd.filename:
        _doc_names_api.append(request.brd.filename)
    if request.prd and request.prd.filename:
        _doc_names_api.append(request.prd.filename)
    if request.hld and request.hld.filename:
        _doc_names_api.append(request.hld.filename)
    if request.dependentServiceDocs:
        for dep in request.dependentServiceDocs:
            if dep and dep.filename:
                _doc_names_api.append(dep.filename)
    try:
        await _write_estimation_to_sharepoint(result, user, sharepoint_client, document_names=_doc_names_api)
    except Exception as exc:
        logger.error(f"Failed to write estimation to SharePoint: {exc}")
        # Continue — estimation was generated successfully

    # Step 6: Record audit log entry
    try:
        audit_entry = AuditGenerationEntry(
            userId=user.corporate_id or user.email,
            projectName=result.projectName,
            domain=result.domain,
            stream=result.stream,
            inputTier=result.inputTier,
            estimationValues={
                "totalEffortPersonDays": result.totalEffortPersonDays,
                "totalEffortPersonMonths": result.totalEffortPersonMonths,
                "calendarDuration": result.calendarDuration,
                "confidenceScore": result.compositeConfidence.overall,
                "costTotal": result.costProjection.total,
                "scopeCoverage": result.scopeCoverage.coverage,
            },
            slmModelName=result.slmModelName,
            timestamp=result.timestamp,
        )
        await record_generation_with_estimation_id(
            audit_entry, result.id, sharepoint_client
        )
    except Exception as exc:
        logger.error(f"Failed to record audit entry: {exc}")
        # Continue — estimation was generated successfully

    return result


@router.get("", response_model=EstimationListResponse)
async def list_estimations(
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    domain: Optional[Domain] = Query(None, description="Filter by domain"),
    stream: Optional[Stream] = Query(None, description="Filter by stream"),
    month: Optional[str] = Query(None, description="Filter by month (YYYY-MM format, loads from monthly sheet)"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO)"),
    user: AuthenticatedUser = Depends(get_current_user),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> EstimationListResponse:
    """Query EstimationIndex.xlsx for dashboard listing.

    Supports filtering by project name, domain, stream, month, and date range.
    When month is provided, filters by the MonthlyFileRef column to ensure
    accurate per-sheet results. All filters are applied with AND logic.

    Requirements: 18.9, 20.1-20.9
    """
    # Ensure the index file exists (auto-create with headers if missing)
    try:
        await sharepoint_client.ensure_estimation_index()
    except Exception:
        pass  # Best-effort; read below will fail with 503 if truly unavailable

    try:
        rows = await sharepoint_client.read_workbook(
            f"{FOLDER_ESTIMATIONS}/EstimationIndex.xlsx", sheet="Sheet1"
        )
    except Exception as exc:
        logger.error(f"Failed to read EstimationIndex.xlsx: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Data source temporarily unavailable. Please retry shortly.",
        )

    estimations = _parse_estimation_index(rows)

    # Apply filters (AND logic)
    if month:
        # Filter by MonthlyFileRef containing the month string (e.g., "2026-07")
        estimations = [
            e for e in estimations
            if month in (e.monthlyFileRef or "")
        ]

    if project_name:
        search_lower = project_name.lower()
        estimations = [
            e for e in estimations
            if search_lower in e.projectName.lower()
        ]

    if domain:
        estimations = [e for e in estimations if e.domain == domain]

    if stream:
        estimations = [e for e in estimations if e.stream == stream]

    if date_from:
        estimations = [e for e in estimations if e.generatedAt >= date_from]

    if date_to:
        estimations = [e for e in estimations if e.generatedAt <= date_to]

    return EstimationListResponse(estimations=estimations, total=len(estimations))


@router.get("/{estimation_id}", response_model=EstimationResult)
async def get_estimation(
    estimation_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> EstimationResult:
    """Load full estimation detail from the monthly file.

    First looks up the EstimationIndex to find the monthly file reference,
    then loads the full detail from that file.

    Requirements: 18.9
    """
    # Check cache first
    cached = _cache_get(estimation_id)
    if cached:
        return cached

    # Look up the estimation in the index to find the monthly file
    index_entry = await _find_estimation_in_index(estimation_id, sharepoint_client)
    if not index_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimation '{estimation_id}' not found.",
        )

    # Load from monthly file
    monthly_file = index_entry.get("monthly_file_ref", "")
    if not monthly_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monthly file reference not found for estimation '{estimation_id}'.",
        )

    try:
        result = await _load_estimation_from_monthly_file(
            estimation_id, monthly_file, sharepoint_client
        )
    except Exception as exc:
        logger.error(f"Failed to load estimation from {monthly_file}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load estimation details. Please retry.",
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimation '{estimation_id}' not found in {monthly_file}.",
        )

    _cache_put(estimation_id, result)
    return result


@router.get("/{estimation_id}/enrichment")
async def get_estimation_enrichment(estimation_id: str) -> JSONResponse:
    """Get async enrichment data (scope coverage, doc readiness) for an estimation.

    Returns:
    - {"status": "processing"} if still computing
    - {"status": "complete", "scopeCoverage": {...}, "documentReadiness": {...}} when done
    - {"status": "not_found"} if no enrichment was triggered for this ID
    """
    from app.services.estimation_engine import _enrichment_store

    data = _enrichment_store.get(estimation_id)
    if data is None:
        return JSONResponse({"status": "not_found"})
    return JSONResponse(data)


@router.get("/{estimation_id}/audit", response_model=AuditHistoryResponse)
async def get_estimation_audit(
    estimation_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> AuditHistoryResponse:
    """Return project audit history for a specific estimation.

    Requirements: 9.4
    """
    # First get the project name from the index
    index_entry = await _find_estimation_in_index(estimation_id, sharepoint_client)
    if not index_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimation '{estimation_id}' not found.",
        )

    project_name = index_entry.get("project_name", "")

    entries = await get_project_history_all_months(
        project_name=project_name,
        sharepoint_client=sharepoint_client,
        estimation_id=estimation_id,
    )

    return AuditHistoryResponse(entries=entries, total=len(entries))


@router.get("/{estimation_id}/export/pdf")
async def export_estimation_pdf(estimation_id: str):
    """PDF export is now handled client-side via browser print.

    This endpoint is kept for backward compatibility but returns guidance.
    """
    return JSONResponse(
        {"message": "PDF export is now available via the 'Download PDF' button in the UI (uses browser print-to-PDF)."},
        status_code=200,
    )


@router.post("/export/pdf")
async def export_estimation_pdf_from_body(request: dict = Body(...)):
    """PDF export is now handled client-side via browser print.

    This endpoint is kept for backward compatibility but returns guidance.
    """
    return JSONResponse(
        {"message": "PDF export is now available via the 'Download PDF' button in the UI (uses browser print-to-PDF)."},
        status_code=200,
    )


@router.get("/{estimation_id}/export/json")
async def export_estimation_json(
    estimation_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
):
    """Export estimation as structured JSON.

    Requirements: 6.1
    """
    index_entry = await _find_estimation_in_index(estimation_id, sharepoint_client)
    if not index_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimation '{estimation_id}' not found.",
        )

    monthly_file = index_entry.get("monthly_file_ref", "")
    result = await _load_estimation_from_monthly_file(
        estimation_id, monthly_file, sharepoint_client
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimation '{estimation_id}' not found.",
        )

    return JSONResponse(
        content=result.model_dump(mode="json"),
        headers={
            "Content-Disposition": f"attachment; filename=estimation_{estimation_id}.json"
        },
    )


# --- Vendor Comparison and Re-Estimation Endpoints ---


class VendorCompareRequest(BaseModel):
    """Request body for vendor comparison."""
    document: ExtractedDocument
    quotedCost: float = Field(..., gt=0)
    quotedTimeline: float = Field(..., gt=0, description="Months")
    vendorTeamSize: Optional[int] = None


class MultiVendorCompareRequest(BaseModel):
    """Request body for comparing multiple vendors."""
    vendors: list[VendorCompareRequest]


class ReEstimateRequest(BaseModel):
    """Request body for re-estimation."""
    projectName: Optional[str] = None
    projectDescription: Optional[str] = None
    domain: Optional[Domain] = None
    stream: Optional[Stream] = None
    brd: Optional[ExtractedDocument] = None
    prd: Optional[ExtractedDocument] = None
    hld: Optional[ExtractedDocument] = None
    dependentServiceDocs: Optional[list[ExtractedDocument]] = None


class ScenarioRequest(BaseModel):
    """Request body for team scenario modeling."""
    teamVariants: list[list[TeamMember]]


@router.post("/{estimation_id}/vendor-compare", response_model=ConsolidatedVendorView)
async def compare_vendors(
    estimation_id: str,
    request: MultiVendorCompareRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> ConsolidatedVendorView:
    """Upload vendor proposals and run comparison against internal estimation.

    Accepts one or more vendor proposals and produces a consolidated comparison
    across quality, cost, and delivery dimensions.

    Requirements: 5.1, 5.6
    """
    from app.services.slm_engine import SLMEngine

    # Load the internal estimation
    index_entry = await _find_estimation_in_index(estimation_id, sharepoint_client)
    if not index_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimation '{estimation_id}' not found.",
        )

    monthly_file = index_entry.get("monthly_file_ref", "")
    internal_estimation = await _load_estimation_from_monthly_file(
        estimation_id, monthly_file, sharepoint_client
    )

    if not internal_estimation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimation '{estimation_id}' not found in monthly file.",
        )

    # Initialize SLM
    slm_engine = SLMEngine()
    try:
        await slm_engine.load_model()
    except Exception as exc:
        logger.error(f"SLM engine failed to load for vendor comparison: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Estimation service temporarily unavailable. Please retry.",
        )

    # Analyze each vendor proposal
    comparisons: list[VendorComparison] = []
    for vendor_req in request.vendors:
        proposal = VendorProposalInput(
            document=vendor_req.document,
            quotedCost=vendor_req.quotedCost,
            quotedTimeline=vendor_req.quotedTimeline,
            vendorTeamSize=vendor_req.vendorTeamSize,
        )

        comparison = await analyze_proposal(
            proposal=proposal,
            internal_estimation=internal_estimation,
            slm_engine=slm_engine,
        )
        comparisons.append(comparison)

    # Consolidate and rank
    consolidated = consolidate_comparisons(comparisons)

    return consolidated


@router.post("/{estimation_id}/re-estimate", response_model=ReEstimationResult)
async def re_estimate(
    estimation_id: str,
    request: ReEstimateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> ReEstimationResult:
    """Re-estimate an existing project with updated documents.

    Links the new estimation to the same project, produces a before/after
    comparison, and records an audit revision entry.

    Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7
    """
    from app.services.slm_engine import SLMEngine

    # Load the previous estimation
    index_entry = await _find_estimation_in_index(estimation_id, sharepoint_client)
    if not index_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimation '{estimation_id}' not found.",
        )

    monthly_file = index_entry.get("monthly_file_ref", "")
    previous_estimation = await _load_estimation_from_monthly_file(
        estimation_id, monthly_file, sharepoint_client
    )

    if not previous_estimation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimation '{estimation_id}' not found in monthly file.",
        )

    # Build new estimation request using previous data + updates
    brd = request.brd or ExtractedDocument(
        filename="previous_brd.md", format="md", pageCount=1,
        textContent="Previously submitted BRD content"
    )
    prd = request.prd or ExtractedDocument(
        filename="previous_prd.md", format="md", pageCount=1,
        textContent="Previously submitted PRD content"
    )

    documents_dict = {
        "brd": brd,
        "prd": prd,
        "hld": request.hld,
        "dependent_docs": request.dependentServiceDocs,
    }

    input_tier: InputTier = classify_tier(documents_dict)

    document_set = DocumentSet(
        brd=brd,
        prd=prd,
        hld=request.hld,
        dependentServiceDocs=request.dependentServiceDocs,
    )

    estimation_request = EstimationRequest(
        projectName=request.projectName or previous_estimation.projectName,
        projectDescription=request.projectDescription or previous_estimation.projectDescription,
        domain=request.domain or previous_estimation.domain,
        stream=request.stream or previous_estimation.stream,
        documents=document_set,
        userId=user.corporate_id or user.email,
    )

    # Run new estimation
    slm_engine = SLMEngine()
    try:
        await slm_engine.load_model()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Estimation service temporarily unavailable. Please retry.",
        )

    try:
        new_estimation = await generate_estimation(
            request=estimation_request,
            input_tier=input_tier,
            slm_engine=slm_engine,
            sharepoint_client=sharepoint_client,
        )
    except (ValidationError, EstimationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # Write new estimation to SharePoint
    _reest_doc_names: list[str] = []
    if document_set.brd and document_set.brd.filename and not document_set.brd.filename.startswith("previous_"):
        _reest_doc_names.append(document_set.brd.filename)
    if document_set.prd and document_set.prd.filename and not document_set.prd.filename.startswith("previous_"):
        _reest_doc_names.append(document_set.prd.filename)
    if document_set.hld and document_set.hld.filename:
        _reest_doc_names.append(document_set.hld.filename)
    if document_set.dependentServiceDocs:
        for dep in document_set.dependentServiceDocs:
            if dep and dep.filename:
                _reest_doc_names.append(dep.filename)
    try:
        await _write_estimation_to_sharepoint(new_estimation, user, sharepoint_client, document_names=_reest_doc_names)
    except Exception as exc:
        logger.error(f"Failed to write re-estimation to SharePoint: {exc}")

    # Record audit revision
    try:
        previous_values = {
            "totalEffortPersonDays": previous_estimation.totalEffortPersonDays,
            "totalEffortPersonMonths": previous_estimation.totalEffortPersonMonths,
            "calendarDuration": previous_estimation.calendarDuration,
            "confidenceScore": previous_estimation.compositeConfidence.overall,
            "costTotal": previous_estimation.costProjection.total,
            "inputTier": previous_estimation.inputTier,
        }
        new_values = {
            "totalEffortPersonDays": new_estimation.totalEffortPersonDays,
            "totalEffortPersonMonths": new_estimation.totalEffortPersonMonths,
            "calendarDuration": new_estimation.calendarDuration,
            "confidenceScore": new_estimation.compositeConfidence.overall,
            "costTotal": new_estimation.costProjection.total,
            "inputTier": new_estimation.inputTier,
        }

        revision_entry = AuditRevisionEntry(
            userId=user.corporate_id or user.email,
            projectName=new_estimation.projectName,
            domain=new_estimation.domain,
            stream=new_estimation.stream,
            inputTier=new_estimation.inputTier,
            previousValues=previous_values,
            newValues=new_values,
            slmModelName=new_estimation.slmModelName,
            timestamp=new_estimation.timestamp,
            estimationId=new_estimation.id,
        )
        await record_revision(revision_entry, sharepoint_client)
    except Exception as exc:
        logger.error(f"Failed to record revision audit: {exc}")

    # Build changes summary
    changes = _compute_changes(previous_estimation, new_estimation)

    return ReEstimationResult(
        currentEstimation=new_estimation,
        previousEstimation=previous_estimation,
        changes=changes,
    )


@router.post("/{estimation_id}/scenarios", response_model=list[ScenarioResult])
async def model_scenarios_endpoint(
    estimation_id: str,
    request: ScenarioRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> list[ScenarioResult]:
    """Model multiple team composition scenarios for an estimation.

    Accepts team variants and returns side-by-side duration comparisons.

    Requirements: 13.4, 13.5
    """
    from app.services.timeline_calculator import model_scenarios

    # Load the estimation
    index_entry = await _find_estimation_in_index(estimation_id, sharepoint_client)
    if not index_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimation '{estimation_id}' not found.",
        )

    monthly_file = index_entry.get("monthly_file_ref", "")
    estimation = await _load_estimation_from_monthly_file(
        estimation_id, monthly_file, sharepoint_client
    )

    if not estimation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimation '{estimation_id}' not found.",
        )

    # Run scenario modeling
    results = model_scenarios(estimation.effortBreakdown, request.teamVariants)

    return results


def _compute_changes(
    previous: EstimationResult,
    current: EstimationResult,
) -> dict:
    """Compute a summary of differences between previous and current estimations.

    Args:
        previous: The previous estimation result.
        current: The current/new estimation result.

    Returns:
        Dictionary summarizing the key changes.
    """
    changes = {}

    if previous.totalEffortPersonDays != current.totalEffortPersonDays:
        diff = current.totalEffortPersonDays - previous.totalEffortPersonDays
        changes["totalEffortPersonDays"] = {
            "previous": previous.totalEffortPersonDays,
            "current": current.totalEffortPersonDays,
            "delta": round(diff, 2),
            "direction": "increased" if diff > 0 else "decreased",
        }

    if previous.calendarDuration != current.calendarDuration:
        diff = current.calendarDuration - previous.calendarDuration
        changes["calendarDuration"] = {
            "previous": previous.calendarDuration,
            "current": current.calendarDuration,
            "delta": round(diff, 2),
            "direction": "increased" if diff > 0 else "decreased",
        }

    if previous.costProjection.total != current.costProjection.total:
        diff = current.costProjection.total - previous.costProjection.total
        changes["costTotal"] = {
            "previous": previous.costProjection.total,
            "current": current.costProjection.total,
            "delta": round(diff, 2),
            "direction": "increased" if diff > 0 else "decreased",
        }

    if previous.compositeConfidence.overall != current.compositeConfidence.overall:
        diff = current.compositeConfidence.overall - previous.compositeConfidence.overall
        changes["confidenceScore"] = {
            "previous": previous.compositeConfidence.overall,
            "current": current.compositeConfidence.overall,
            "delta": round(diff, 2),
            "direction": "increased" if diff > 0 else "decreased",
        }

    if previous.inputTier != current.inputTier:
        changes["inputTier"] = {
            "previous": previous.inputTier,
            "current": current.inputTier,
            "direction": "upgraded" if current.inputTier > previous.inputTier else "downgraded",
        }

    if previous.scopeCoverage.coverage != current.scopeCoverage.coverage:
        diff = current.scopeCoverage.coverage - previous.scopeCoverage.coverage
        changes["scopeCoverage"] = {
            "previous": previous.scopeCoverage.coverage,
            "current": current.scopeCoverage.coverage,
            "delta": round(diff, 4),
            "direction": "increased" if diff > 0 else "decreased",
        }

    return changes


# --- Helper Functions ---


async def _write_estimation_to_sharepoint(
    result: EstimationResult,
    user: AuthenticatedUser,
    sharepoint_client: SharePointClient,
    document_names: Optional[list[str]] = None,
) -> None:
    """Write estimation results to SharePoint (monthly file + index).

    Writes:
    1. Full estimation data to Estimations_YYYY-MM.xlsx
    2. Lightweight summary to EstimationIndex.xlsx

    Requirements: 18.8
    """
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    monthly_file = f"{FOLDER_ESTIMATIONS_DATA}/Estimations_{month}.xlsx"

    # Ensure monthly files exist
    await sharepoint_client.ensure_monthly_files(month)

    # Write to monthly estimation file
    phases_json = ""
    if result.phases:
        phases_json = json.dumps([p.model_dump() for p in result.phases])

    estimation_row = [
        result.id,
        result.projectName,
        result.projectDescription or "",
        result.domain.value,
        result.stream.value,
        result.inputTier,
        json.dumps([e.model_dump() for e in result.effortBreakdown]),
        result.totalEffortPersonDays,
        result.totalEffortPersonMonths,
        result.calendarDuration,
        json.dumps([t.model_dump() for t in result.teamComposition]),
        json.dumps(result.scopeCoverage.model_dump()),
        json.dumps(result.compositeConfidence.model_dump()),
        json.dumps(result.costProjection.model_dump()),
        json.dumps(result.assumptions),
        result.slmModelName,
        user.corporate_id or user.email,
        result.timestamp,
        1,  # Version
        "",  # PreviousVersionId
        "",  # VendorComparisonJSON
        phases_json,  # PhasesJSON
        json.dumps(result.catalogBreakdown.model_dump()) if result.catalogBreakdown else "",  # CatalogBreakdownJSON
        json.dumps(result.infraCost) if result.infraCost else "",  # InfraCostJSON
        json.dumps(result.documentReadiness) if result.documentReadiness else "",  # DocumentReadinessJSON
    ]

    await sharepoint_client.append_row(monthly_file, "Sheet1", estimation_row)

    # Write to index
    index_row = [
        result.id,                              # EstimationId
        result.projectName,                     # ProjectName
        result.domain.value,                    # Domain
        result.stream.value,                    # Stream
        result.inputTier,                       # InputTier
        result.totalEffortPersonDays,           # TotalEffortDays
        result.calendarDuration,                # CalendarDuration
        result.compositeConfidence.overall,     # ConfidenceLevel
        result.costProjection.total,            # TotalCost
        user.corporate_id or user.email,        # GeneratedBy
        result.timestamp,                       # GeneratedAt
        monthly_file,                           # MonthlyFileRef
        1,                                      # Version
        "Active",                               # Status
        ",".join(document_names) if document_names else "",  # DocumentNames
    ]

    await sharepoint_client.ensure_estimation_index()
    await sharepoint_client.append_row(f"{FOLDER_ESTIMATIONS}/EstimationIndex.xlsx", "Sheet1", index_row)


async def _find_estimation_in_index(
    estimation_id: str,
    sharepoint_client: SharePointClient,
) -> Optional[dict]:
    """Find an estimation entry in the EstimationIndex.xlsx.

    Args:
        estimation_id: The estimation ID to search for.
        sharepoint_client: SharePoint client for reading.

    Returns:
        Dictionary with index entry data, or None if not found.
    """
    try:
        rows = await sharepoint_client.read_workbook(
            f"{FOLDER_ESTIMATIONS}/EstimationIndex.xlsx", sheet="Sheet1"
        )
    except Exception:
        return None

    if not rows or len(rows) < 2:
        return None

    headers = [str(h).strip().lower() for h in rows[0]]
    col_map = {h: i for i, h in enumerate(headers)}

    id_idx = col_map.get("estimationid", 0)
    name_idx = col_map.get("projectname", 1)
    monthly_ref_idx = col_map.get("monthlyfileref", 11)

    for row in rows[1:]:
        if not row or len(row) <= id_idx:
            continue
        row_id = str(row[id_idx]).strip()
        if row_id == estimation_id:
            return {
                "estimation_id": row_id,
                "project_name": str(row[name_idx]).strip() if len(row) > name_idx else "",
                "monthly_file_ref": str(row[monthly_ref_idx]).strip() if len(row) > monthly_ref_idx else "",
            }

    return None


async def _load_estimation_from_monthly_file(
    estimation_id: str,
    monthly_file: str,
    sharepoint_client: SharePointClient,
) -> Optional[EstimationResult]:
    """Load a full estimation from its monthly file.

    Args:
        estimation_id: The estimation ID to find.
        monthly_file: The monthly file name (e.g., 'Estimations_2026-01.xlsx').
        sharepoint_client: SharePoint client for reading.

    Returns:
        EstimationResult if found, None otherwise.
    """
    from app.models.schemas import (
        ClassifiedScopeItem,
        CompositeConfidenceScore,
        CostProjection,
        DisciplineEffort,
        DurationResult,
        ScopeAnalysis,
        TeamMember,
    )

    # Backward compatibility: old index entries stored bare filenames before folder migration
    if monthly_file and not monthly_file.startswith(FOLDER_ESTIMATIONS):
        monthly_file = f"{FOLDER_ESTIMATIONS_DATA}/{monthly_file}"

    rows = await sharepoint_client.read_workbook(monthly_file, sheet="Sheet1")
    if not rows or len(rows) < 2:
        return None

    headers = [str(h).strip().lower() for h in rows[0]]
    col_map = {h: i for i, h in enumerate(headers)}

    id_idx = col_map.get("estimationid", 0)

    for row in rows[1:]:
        if not row or len(row) <= id_idx:
            continue
        if str(row[id_idx]).strip() != estimation_id:
            continue

        # Parse the row into an EstimationResult
        try:
            project_name = str(row[col_map.get("projectname", 1)]).strip()
            project_desc = str(row[col_map.get("projectdescription", 2)]).strip() or None
            domain_val = str(row[col_map.get("domain", 3)]).strip()
            stream_val = str(row[col_map.get("stream", 4)]).strip()
            input_tier = int(row[col_map.get("inputtier", 5)])

            effort_json = str(row[col_map.get("effortbreakdownjson", 6)]).strip()
            effort_data = json.loads(effort_json) if effort_json else []
            effort_breakdown = [DisciplineEffort(**e) for e in effort_data]

            total_days = float(row[col_map.get("totaleffortdays", 7)])
            total_months = float(row[col_map.get("totaleffortmonths", 8)])
            calendar_duration = float(row[col_map.get("calendarduration", 9)])

            team_json = str(row[col_map.get("teamcompositionjson", 10)]).strip()
            team_data = json.loads(team_json) if team_json else []
            team_composition = [TeamMember(**t) for t in team_data]

            scope_json = str(row[col_map.get("scopecoveragejson", 11)]).strip()
            scope_data = json.loads(scope_json) if scope_json else {}
            scope_coverage = ScopeAnalysis(**scope_data)

            confidence_json = str(row[col_map.get("confidencejson", 12)]).strip()
            confidence_data = json.loads(confidence_json) if confidence_json else {}
            composite_confidence = CompositeConfidenceScore(**confidence_data)

            cost_json = str(row[col_map.get("costprojectionjson", 13)]).strip()
            cost_data = json.loads(cost_json) if cost_json else {}
            cost_projection = CostProjection(**cost_data)

            assumptions_json = str(row[col_map.get("assumptionsjson", 14)]).strip()
            assumptions = json.loads(assumptions_json) if assumptions_json else []

            slm_model = str(row[col_map.get("slmmodelname", 15)]).strip()
            generated_at = str(row[col_map.get("generatedat", 17)]).strip()

            # Load phases if present
            phases = None
            phases_idx = col_map.get("phasesjson")
            if phases_idx is not None and len(row) > phases_idx:
                phases_json_str = str(row[phases_idx]).strip()
                if phases_json_str:
                    try:
                        phases_data = json.loads(phases_json_str)
                        if phases_data:
                            from app.models.schemas import PhaseEstimation
                            phases = [PhaseEstimation(**p) for p in phases_data]
                    except (json.JSONDecodeError, TypeError):
                        phases = None

            # Load catalog breakdown if present
            catalog_breakdown = None
            cb_idx = col_map.get("catalogbreakdownjson", 22)  # Position 22 (after PhasesJSON)
            if len(row) > cb_idx:
                cb_str = str(row[cb_idx]).strip()
                if cb_str:
                    try:
                        from app.models.schemas import CatalogBreakdown
                        catalog_breakdown = CatalogBreakdown(**json.loads(cb_str))
                    except (json.JSONDecodeError, TypeError, Exception):
                        catalog_breakdown = None

            # Load infra cost if present
            infra_cost = None
            ic_idx = col_map.get("infracostjson", 23)  # Position 23
            if len(row) > ic_idx:
                ic_str = str(row[ic_idx]).strip()
                if ic_str:
                    try:
                        infra_cost = json.loads(ic_str)
                    except (json.JSONDecodeError, TypeError):
                        infra_cost = None

            # Load document readiness if present
            doc_readiness = None
            dr_idx = col_map.get("documentreadinessjson", 24)  # Position 24
            if len(row) > dr_idx:
                dr_str = str(row[dr_idx]).strip()
                if dr_str:
                    try:
                        doc_readiness = json.loads(dr_str)
                    except (json.JSONDecodeError, TypeError):
                        doc_readiness = None

            return EstimationResult(
                id=estimation_id,
                projectName=project_name,
                projectDescription=project_desc,
                domain=domain_val,
                stream=stream_val,
                inputTier=input_tier,
                effortBreakdown=effort_breakdown,
                totalEffortPersonDays=total_days,
                totalEffortPersonMonths=total_months,
                calendarDuration=calendar_duration,
                teamComposition=team_composition,
                scopeCoverage=scope_coverage,
                compositeConfidence=composite_confidence,
                costProjection=cost_projection,
                infraCost=infra_cost,
                documentReadiness=doc_readiness,
                catalogBreakdown=catalog_breakdown,
                phases=phases,
                assumptions=assumptions,
                slmModelName=slm_model,
                timestamp=generated_at,
            )
        except Exception as exc:
            logger.error(f"Failed to parse estimation row: {exc}")
            return None

    return None


def _parse_estimation_index(rows: list[list]) -> list[EstimationIndexEntry]:
    """Parse EstimationIndex.xlsx rows into EstimationIndexEntry objects.

    Args:
        rows: Raw rows from the workbook (first row is headers).

    Returns:
        List of EstimationIndexEntry objects.
    """
    if not rows or len(rows) < 2:
        return []

    headers = [str(h).strip().lower() for h in rows[0]]
    col_map = {h: i for i, h in enumerate(headers)}

    id_idx = col_map.get("estimationid", 0)
    name_idx = col_map.get("projectname", 1)
    domain_idx = col_map.get("domain", 2)
    stream_idx = col_map.get("stream", 3)
    tier_idx = col_map.get("inputtier", 4)
    effort_idx = col_map.get("totaleffortdays", 5)
    duration_idx = col_map.get("calendarduration", 6)
    confidence_idx = col_map.get("confidencelevel", 7)
    cost_idx = col_map.get("totalcost", 8)
    generated_by_idx = col_map.get("generatedby", 9)
    generated_at_idx = col_map.get("generatedat", 10)
    file_ref_idx = col_map.get("monthlyfileref", 11)
    version_idx = col_map.get("version", 12)
    doc_names_idx = col_map.get("documentnames", None)

    entries: list[EstimationIndexEntry] = []

    for row in rows[1:]:
        if not row or len(row) <= id_idx:
            continue
        # Skip empty rows (from table placeholder)
        row_id = str(row[id_idx]).strip()
        if not row_id or row_id == "":
            continue

        try:
            # Parse documentNames from comma-separated string
            raw_doc_names = ""
            if doc_names_idx is not None and len(row) > doc_names_idx and row[doc_names_idx]:
                raw_doc_names = str(row[doc_names_idx]).strip()
            doc_names_list = [n.strip() for n in raw_doc_names.split(",") if n.strip()] if raw_doc_names else []

            entry = EstimationIndexEntry(
                estimationId=row_id,
                projectName=str(row[name_idx]).strip() if len(row) > name_idx else "",
                domain=str(row[domain_idx]).strip() if len(row) > domain_idx else "Others",
                stream=str(row[stream_idx]).strip() if len(row) > stream_idx else "D2C",
                inputTier=int(float(str(row[tier_idx]))) if len(row) > tier_idx and row[tier_idx] else 1,
                totalEffortDays=float(row[effort_idx]) if len(row) > effort_idx and row[effort_idx] else 0,
                confidenceScore=float(row[confidence_idx]) if len(row) > confidence_idx and row[confidence_idx] else 0,
                totalCost=float(row[cost_idx]) if len(row) > cost_idx and row[cost_idx] else 0,
                generatedBy=str(row[generated_by_idx]).strip() if len(row) > generated_by_idx else "",
                generatedAt=str(row[generated_at_idx]).strip() if len(row) > generated_at_idx else "",
                monthlyFileRef=str(row[file_ref_idx]).strip() if len(row) > file_ref_idx else "",
                version=int(float(str(row[version_idx]))) if len(row) > version_idx and row[version_idx] else 1,
                documentNames=doc_names_list,
            )
            entries.append(entry)
        except Exception as exc:
            logger.warning(f"Failed to parse estimation index row: {exc}")
            continue

    return entries
