"""Build vs Buy Evaluation API router.

Provides endpoints for the Build vs Buy evaluation lifecycle:
- POST /api/build-vs-buy/evaluations — create new evaluation
- GET /api/build-vs-buy/evaluations — list evaluations
- GET /api/build-vs-buy/evaluations/{id} — get full evaluation detail
- POST /api/build-vs-buy/evaluations/{id}/options — add option
- PUT /api/build-vs-buy/evaluations/{id}/options/{opt_id} — update option
- DELETE /api/build-vs-buy/evaluations/{id}/options/{opt_id} — remove option
- PUT /api/build-vs-buy/evaluations/{id}/options/{opt_id}/scores — submit scores
- PUT /api/build-vs-buy/evaluations/{id}/options/{opt_id}/tco — submit TCO
- PATCH /api/build-vs-buy/evaluations/{id}/status — update lifecycle status

Requirements: 1.1, 1.3, 2.1, 2.2, 2.3, 2.5, 2.6, 4.1, 4.4, 5.1, 5.2,
             10.4, 10.5, 12.5, 14.1, 14.2, 14.3, 14.4, 14.5
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.middleware.auth import AuthenticatedUser, get_current_user
from app.models.schemas import (
    BvBEvaluationDetailResponse,
    BvBEvaluationListResponse,
    BvBEvaluationResponse,
    DimensionScoreResponse,
    EvaluationCreateRequest,
    OptionCreateRequest,
    OptionResponse,
    OptionUpdateRequest,
    ProposalAnalysisResponse,
    ScoreResponse,
    ScoreSubmitRequest,
    StatusUpdateRequest,
    TCOResultResponse,
    TCOSubmitRequest,
)
from app.services.sharepoint_client import SharePointClient, SharePointError
from app.services import bvb_evaluation_service
from app.services.proposal_analyzer import analyze_proposal
from app.services.slm_engine import SLMEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/build-vs-buy", tags=["Build vs Buy"])


# ---------------------------------------------------------------------------
# Evaluation CRUD
# ---------------------------------------------------------------------------


@router.post("/evaluations", status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    request: EvaluationCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> BvBEvaluationResponse:
    """Create a new Build vs Buy evaluation."""
    sp = SharePointClient()
    try:
        result = await bvb_evaluation_service.create_evaluation(
            request=request,
            user_display_name=user.identity.displayName,
            user_email=user.identity.email,
            sp=sp,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except SharePointError as exc:
        logger.error(f"SharePoint error creating evaluation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later.",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error creating evaluation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.get("/evaluations")
async def list_evaluations(
    user: AuthenticatedUser = Depends(get_current_user),
) -> BvBEvaluationListResponse:
    """List all Build vs Buy evaluations."""
    sp = SharePointClient()
    try:
        evaluations = await bvb_evaluation_service.list_evaluations(sp)
        return BvBEvaluationListResponse(
            evaluations=evaluations,
            total=len(evaluations),
        )
    except SharePointError as exc:
        logger.error(f"SharePoint error listing evaluations: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later.",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error listing evaluations: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.get("/evaluations/{evaluation_id}")
async def get_evaluation(
    evaluation_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> BvBEvaluationDetailResponse:
    """Get full evaluation detail by ID."""
    sp = SharePointClient()
    try:
        data = await bvb_evaluation_service.load_evaluation(evaluation_id, sp)
        metadata = data.get("metadata", {})
        options_raw = data.get("options", [])
        scores_raw = data.get("scores", [])
        tco_raw = data.get("tco", [])

        # Build evaluation response from metadata
        evaluation = BvBEvaluationResponse(
            id=metadata.get("evaluation_id", evaluation_id),
            opportunity_name=metadata.get("opportunity_name", ""),
            problem_statement=metadata.get("problem_statement", ""),
            business_unit=metadata.get("business_unit", ""),
            budget_min=float(metadata.get("budget_min", 0)),
            budget_max=float(metadata.get("budget_max", 0)),
            target_decision_date=metadata.get("target_decision_date", ""),
            owner_display_name=metadata.get("owner_display_name", ""),
            status=metadata.get("status", "Draft"),
            created_at=metadata.get("created_at", ""),
            updated_at=metadata.get("updated_at", ""),
        )

        # Build options list
        options = [
            OptionResponse(
                id=opt.get("OptionId", ""),
                evaluation_id=evaluation_id,
                name=opt.get("Name", ""),
                type=opt.get("Type", "Build"),
                vendor_name=opt.get("VendorName") or None,
                description=opt.get("Description") or None,
            )
            for opt in options_raw
        ]

        # Build scores dict: option_id -> list of DimensionScoreResponse
        scores: dict[str, list[DimensionScoreResponse]] = {}
        for score_row in scores_raw:
            opt_id = score_row.get("OptionId", "")
            if opt_id not in scores:
                scores[opt_id] = []
            scores[opt_id].append(
                DimensionScoreResponse(
                    dimension=score_row.get("Dimension", ""),
                    score=int(score_row.get("Score", 0)),
                    source=score_row.get("Source", "manual"),
                    confidence=None,
                )
            )

        # Build TCO results dict: option_id -> TCOResultResponse
        tco_results: dict[str, TCOResultResponse] = {}
        for tco_row in tco_raw:
            opt_id = tco_row.get("OptionId", "")
            category = tco_row.get("Category", "")
            amount = float(tco_row.get("Amount", 0))
            if opt_id not in tco_results:
                tco_results[opt_id] = TCOResultResponse(
                    option_id=opt_id,
                    year_0_total=0.0,
                    three_year_tco=0.0,
                    five_year_tco=0.0,
                    annual_run_cost=0.0,
                    cost_per_user=None,
                )
            if category == "year_0_total":
                tco_results[opt_id].year_0_total = amount
            elif category == "three_year_tco":
                tco_results[opt_id].three_year_tco = amount
            elif category == "five_year_tco":
                tco_results[opt_id].five_year_tco = amount
            elif category == "annual_run_cost":
                tco_results[opt_id].annual_run_cost = amount
            elif category == "cost_per_user":
                tco_results[opt_id].cost_per_user = amount

        return BvBEvaluationDetailResponse(
            evaluation=evaluation,
            options=options,
            scores=scores,
            tco_results=tco_results,
            recommendation=None,
        )
    except SharePointError as exc:
        logger.error(f"SharePoint error loading evaluation {evaluation_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later.",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error loading evaluation {evaluation_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


# ---------------------------------------------------------------------------
# Option Management
# ---------------------------------------------------------------------------


@router.post("/evaluations/{evaluation_id}/options", status_code=status.HTTP_201_CREATED)
async def add_option(
    evaluation_id: str,
    request: OptionCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> OptionResponse:
    """Add an option to an evaluation."""
    sp = SharePointClient()
    try:
        result = await bvb_evaluation_service.add_option(evaluation_id, request, sp)
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except SharePointError as exc:
        logger.error(f"SharePoint error adding option to {evaluation_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later.",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error adding option to {evaluation_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.put("/evaluations/{evaluation_id}/options/{option_id}")
async def update_option(
    evaluation_id: str,
    option_id: str,
    request: OptionUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> OptionResponse:
    """Update an existing option's metadata."""
    sp = SharePointClient()
    try:
        # Load current option data to merge updates
        data = await bvb_evaluation_service.load_evaluation(evaluation_id, sp)
        options_raw = data.get("options", [])
        target_option = None
        for opt in options_raw:
            if opt.get("OptionId") == option_id:
                target_option = opt
                break

        if not target_option:
            raise ValueError(f"Option {option_id} not found in evaluation {evaluation_id}")

        # Apply updates (only non-None fields)
        name = request.name if request.name is not None else target_option.get("Name", "")
        vendor_name = request.vendor_name if request.vendor_name is not None else target_option.get("VendorName", "")
        description = request.description if request.description is not None else target_option.get("Description", "")

        return OptionResponse(
            id=option_id,
            evaluation_id=evaluation_id,
            name=name,
            type=target_option.get("Type", "Build"),
            vendor_name=vendor_name or None,
            description=description or None,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except SharePointError as exc:
        logger.error(f"SharePoint error updating option {option_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later.",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error updating option {option_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.delete("/evaluations/{evaluation_id}/options/{option_id}")
async def remove_option(
    evaluation_id: str,
    option_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Remove an option and all associated scores/TCO data."""
    sp = SharePointClient()
    try:
        await bvb_evaluation_service.remove_option(evaluation_id, option_id, sp)
        return {"message": f"Option {option_id} removed successfully"}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except SharePointError as exc:
        logger.error(f"SharePoint error removing option {option_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later.",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error removing option {option_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


@router.put("/evaluations/{evaluation_id}/options/{option_id}/scores")
async def submit_scores(
    evaluation_id: str,
    option_id: str,
    request: ScoreSubmitRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ScoreResponse:
    """Submit dimension scores for an option."""
    sp = SharePointClient()
    try:
        result = await bvb_evaluation_service.submit_scores(
            evaluation_id=evaluation_id,
            option_id=option_id,
            scores=request.scores,
            source="manual",
            sp=sp,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except SharePointError as exc:
        logger.error(f"SharePoint error submitting scores for {option_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later.",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error submitting scores for {option_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


# ---------------------------------------------------------------------------
# TCO
# ---------------------------------------------------------------------------


@router.put("/evaluations/{evaluation_id}/options/{option_id}/tco")
async def submit_tco(
    evaluation_id: str,
    option_id: str,
    request: TCOSubmitRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> TCOResultResponse:
    """Submit TCO data for an option."""
    sp = SharePointClient()
    try:
        result = await bvb_evaluation_service.submit_tco(
            evaluation_id=evaluation_id,
            option_id=option_id,
            tco_input=request,
            sp=sp,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except SharePointError as exc:
        logger.error(f"SharePoint error submitting TCO for {option_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later.",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error submitting TCO for {option_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


# ---------------------------------------------------------------------------
# SLM Proposal Analysis
# ---------------------------------------------------------------------------


@router.post("/evaluations/{evaluation_id}/options/{option_id}/analyze-proposal")
async def analyze_vendor_proposal(
    evaluation_id: str,
    option_id: str,
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
) -> ProposalAnalysisResponse:
    """Analyze a vendor proposal using the SLM engine.

    Extracts structured data and suggests dimension scores from an uploaded
    vendor proposal document (PDF, DOCX, or MD).
    """
    sp = SharePointClient()
    try:
        # Read file content
        file_bytes = await file.read()
        filename = file.filename or "proposal.pdf"

        # Initialize SLM engine and run analysis
        slm_engine = SLMEngine()
        await slm_engine.load_model()
        result = await analyze_proposal(file_bytes, filename, slm_engine)

        # If SLM suggested scores, store them with source="slm_suggested"
        if result.suggested_scores and not result.error:
            try:
                await bvb_evaluation_service.submit_scores(
                    evaluation_id=evaluation_id,
                    option_id=option_id,
                    scores=result.suggested_scores,
                    source="slm_suggested",
                    sp=sp,
                )
            except Exception as exc:
                logger.warning(
                    f"Failed to store SLM-suggested scores for option {option_id}: {exc}"
                )

        # Build extracted_data dict for response
        extracted_data = {
            "proposed_costs": result.proposed_costs,
            "timeline_months": result.timeline_months,
            "team_size": result.team_size,
            "technology_stack": result.technology_stack,
            "support_model": result.support_model,
            "sla_commitments": result.sla_commitments,
        }

        return ProposalAnalysisResponse(
            extracted_data=extracted_data,
            suggested_scores=result.suggested_scores,
            risk_flags=result.risk_flags,
            confidence=result.confidence,
            error=result.error,
        )
    except SharePointError as exc:
        logger.error(f"SharePoint error analyzing proposal for {option_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later.",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error analyzing proposal for {option_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during proposal analysis.",
        )


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


@router.patch("/evaluations/{evaluation_id}/status")
async def update_status(
    evaluation_id: str,
    request: StatusUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> BvBEvaluationResponse:
    """Update the lifecycle status of an evaluation."""
    sp = SharePointClient()
    try:
        # Load evaluation and update status in metadata
        data = await bvb_evaluation_service.load_evaluation(evaluation_id, sp)
        metadata = data.get("metadata", {})

        metadata["status"] = request.status.value
        metadata["updated_at"] = bvb_evaluation_service._now_iso()

        await bvb_evaluation_service.save_evaluation_metadata(evaluation_id, metadata, sp)
        await bvb_evaluation_service.update_index_status(evaluation_id, request.status.value, sp)

        return BvBEvaluationResponse(
            id=metadata.get("evaluation_id", evaluation_id),
            opportunity_name=metadata.get("opportunity_name", ""),
            problem_statement=metadata.get("problem_statement", ""),
            business_unit=metadata.get("business_unit", ""),
            budget_min=float(metadata.get("budget_min", 0)),
            budget_max=float(metadata.get("budget_max", 0)),
            target_decision_date=metadata.get("target_decision_date", ""),
            owner_display_name=metadata.get("owner_display_name", ""),
            status=request.status,
            created_at=metadata.get("created_at", ""),
            updated_at=metadata.get("updated_at", ""),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except SharePointError as exc:
        logger.error(f"SharePoint error updating status for {evaluation_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable. Please try again later.",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error updating status for {evaluation_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
