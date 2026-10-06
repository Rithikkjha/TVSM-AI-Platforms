"""Global exception handler middleware for the Project Estimation Tool.

Returns structured error JSON with corrective action suggestions.
Implements session preservation logic for error recovery.

Requirements: 2.5, 7.3, 21.5, 21.6, 21.7, 21.8
"""

import logging
import traceback
from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Structured error response builder."""

    @staticmethod
    def build(
        status_code: int,
        error_type: str,
        message: str,
        corrective_action: Optional[str] = None,
        details: Optional[dict] = None,
        session_preserved: bool = False,
    ) -> dict:
        """Build a structured error response.

        Args:
            status_code: HTTP status code.
            error_type: Category of error (e.g., 'validation', 'service_unavailable').
            message: User-facing error message.
            corrective_action: Suggested action the user can take.
            details: Additional error details (optional).
            session_preserved: Whether session state was preserved for resume.

        Returns:
            Dictionary suitable for JSON response.
        """
        response = {
            "error": {
                "type": error_type,
                "message": message,
                "statusCode": status_code,
            }
        }
        if corrective_action:
            response["error"]["correctiveAction"] = corrective_action
        if details:
            response["error"]["details"] = details
        if session_preserved:
            response["error"]["sessionPreserved"] = True
            response["error"]["resumeHint"] = (
                "Your progress has been saved. You can resume after re-authentication."
            )
        return response


# Map of known exception types to structured responses
ERROR_MAP = {
    "ValidationError": {
        "status": status.HTTP_400_BAD_REQUEST,
        "type": "validation_error",
        "action": "Please check the input fields and correct any invalid values.",
    },
    "AuthenticationError": {
        "status": status.HTTP_401_UNAUTHORIZED,
        "type": "authentication_error",
        "action": "Please re-authenticate with your corporate SSO.",
    },
    "PermissionError": {
        "status": status.HTTP_403_FORBIDDEN,
        "type": "authorization_error",
        "action": "Contact your admin to request appropriate access.",
    },
    "FileNotFoundError": {
        "status": status.HTTP_404_NOT_FOUND,
        "type": "not_found",
        "action": "The requested resource could not be found. Please verify the ID.",
    },
    "SharePointUnavailableError": {
        "status": status.HTTP_503_SERVICE_UNAVAILABLE,
        "type": "service_unavailable",
        "action": "Data source temporarily unavailable. Please retry shortly.",
    },
    "SharePointWriteError": {
        "status": status.HTTP_503_SERVICE_UNAVAILABLE,
        "type": "service_unavailable",
        "action": "Your change could not be saved to storage. Please retry — no partial data was committed to the row you edited.",
    },
    "SharePointError": {
        # Base class for all SharePoint failures (e.g. the persist guard
        # refusing to overwrite from an unverified load). Treated as a
        # retryable service error rather than a generic 500 so the user is told
        # to retry instead of assuming their edit was saved.
        "status": status.HTTP_503_SERVICE_UNAVAILABLE,
        "type": "service_unavailable",
        "action": "Your change could not be saved right now. Please retry in a few moments.",
    },
    "FileLockError": {
        "status": 423,  # HTTP 423 Locked
        "type": "file_locked",
        "action": "File currently in use. Please try again later.",
    },
    "SLMEngineError": {
        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "type": "slm_engine_error",
        "action": "Estimation service encountered an error. Please retry or contact admin.",
    },
    "TimeoutError": {
        "status": status.HTTP_504_GATEWAY_TIMEOUT,
        "type": "timeout",
        "action": "The operation timed out. Please retry in a few moments.",
    },
}


class GlobalExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware that catches all unhandled exceptions and returns structured JSON.

    Provides:
    - Structured error responses with corrective actions
    - Session preservation hints on certain errors
    - Consistent error format across all endpoints
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        """Process the request and catch any unhandled exceptions.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/endpoint in the chain.

        Returns:
            The response (normal or error JSON).
        """
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            exc_name = type(exc).__name__
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}: "
                f"{exc_name}: {exc}",
                exc_info=True,
            )

            # Check if this is a known exception type
            error_info = ERROR_MAP.get(exc_name)

            if error_info:
                body = ErrorResponse.build(
                    status_code=error_info["status"],
                    error_type=error_info["type"],
                    message=str(exc),
                    corrective_action=error_info["action"],
                )
                return JSONResponse(
                    status_code=error_info["status"],
                    content=body,
                )

            # Default: Internal Server Error
            # Determine if session state should be preserved
            session_preserved = _should_preserve_session(request)

            body = ErrorResponse.build(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_type="internal_error",
                message="An unexpected error occurred. Please retry or contact support.",
                corrective_action=(
                    "If this persists, try refreshing the page. "
                    "Your estimation progress may be recoverable."
                ),
                session_preserved=session_preserved,
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=body,
            )


def _should_preserve_session(request: Request) -> bool:
    """Determine if session state should be preserved for this request.

    Session preservation is relevant for long-running operations like
    estimation generation where partial progress exists.

    Args:
        request: The incoming request.

    Returns:
        True if session should be preserved.
    """
    # Preserve session for POST requests to estimation endpoints
    path = request.url.path
    if request.method == "POST" and "/api/estimations" in path:
        return True
    return False
