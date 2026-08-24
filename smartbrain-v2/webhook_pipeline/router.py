"""FastAPI router for the steering webhook endpoint.

Receives GitHub PR webhook events, validates HMAC-SHA256 signatures,
orchestrates the diff extraction → LLM analysis → file write → re-ingest
pipeline.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse

from config.settings import get_settings
from shared.reingest import trigger_reingest
from webhook_pipeline.diff_extractor import extract_pr_diff
from webhook_pipeline.llm_analyzer import analyze_diff
from webhook_pipeline.steering_writer import write_steering_files

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["steering-webhook"])


def verify_signature(body: bytes, header: str | None, secret: str) -> bool:
    """Validate HMAC-SHA256 signature from the X-Hub-Signature-256 header.

    Args:
        body: Raw request body bytes.
        header: Value of the ``X-Hub-Signature-256`` header (e.g.
            ``"sha256=abc123..."``).
        secret: The shared webhook secret.

    Returns:
        ``True`` if the signature is valid, ``False`` otherwise.
    """
    if not secret:
        # No secret configured — skip validation (dev mode)
        return True
    if not header:
        return False

    # Header format: "sha256=<hex_digest>"
    if not header.startswith("sha256="):
        return False

    expected_sig = header[7:]
    computed_sig = hmac.HMAC(
        key=secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed_sig, expected_sig)


@router.post("/steering")
async def steering_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
) -> JSONResponse:
    """Steering webhook handler: validate → extract → analyze → write → re-ingest."""
    settings = get_settings()
    raw_body = await request.body()

    # Step 1: HMAC-SHA256 signature validation
    if not verify_signature(raw_body, x_hub_signature_256, settings.steering_webhook_secret):
        logger.warning(
            "Steering webhook: invalid signature from %s",
            request.client.host if request.client else "unknown",
        )
        return JSONResponse(
            {"error": "invalid_signature"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Step 2: Parse JSON payload
    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, ValueError):
        return JSONResponse(
            {"error": "malformed_payload"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Step 3: Extract repo name
    repo = payload.get("repository", {})
    repo_name = repo.get("name", "")
    if not repo_name:
        return JSONResponse(
            {"error": "missing_repository"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Step 4: Extract diff
    diff_result = await extract_pr_diff(payload, settings.github_token)
    if diff_result.error:
        logger.error("Diff extraction failed for %s: %s", repo_name, diff_result.error)
        return JSONResponse(
            {"error": diff_result.error},
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    # Step 5: LLM analysis
    analysis = await analyze_diff(diff_result, repo_name)
    if analysis.error:
        logger.error("LLM analysis failed for %s: %s", repo_name, analysis.error)
        return JSONResponse(
            {"error": analysis.error},
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    # Step 6: Check if changes needed
    if not analysis.has_changes:
        return JSONResponse({
            "status": "no_changes",
            "reasoning": analysis.reasoning,
        })

    # Step 7: Write steering files
    write_steering_files(repo_name, analysis.updates)

    # Step 8: Trigger re-ingestion
    ingest_result = await trigger_reingest(repo_name, analysis.updated_file_types)

    # Step 9: Return success
    return JSONResponse({
        "status": "updated",
        "repo": repo_name,
        "updated_files": analysis.updated_file_types,
        "reasoning": analysis.reasoning,
        "ingestion": {
            "files_processed": ingest_result.files_processed,
            "files_skipped": ingest_result.files_skipped,
            "chunks_created": ingest_result.chunks_created,
            "error": ingest_result.error,
        },
    })


__all__ = [
    "router",
    "verify_signature",
]
