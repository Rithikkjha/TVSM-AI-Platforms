"""Rate limiter middleware for the Project Estimation Tool.

Implements per-user rate limiting: max 10 requests/minute.
Returns 429 with "system busy" message if exceeded.

Requirements: 21.1, 21.2
"""

import logging
import time
from collections import defaultdict
from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_MAX_REQUESTS = 10
DEFAULT_WINDOW_SECONDS = 60


class RateLimitState:
    """Tracks request counts per user within a sliding window."""

    def __init__(self, max_requests: int = DEFAULT_MAX_REQUESTS, window_seconds: int = DEFAULT_WINDOW_SECONDS):
        """Initialize rate limit state.

        Args:
            max_requests: Maximum number of requests allowed per window.
            window_seconds: Time window in seconds.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # user_id -> list of request timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(self, user_id: str) -> bool:
        """Check if a user has exceeded the rate limit.

        Args:
            user_id: Identifier for the user (email, IP, or token).

        Returns:
            True if rate limit exceeded, False otherwise.
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Clean up old entries
        self._requests[user_id] = [
            ts for ts in self._requests[user_id] if ts > window_start
        ]

        # Check limit
        if len(self._requests[user_id]) >= self.max_requests:
            return True

        # Record this request
        self._requests[user_id].append(now)
        return False

    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests for a user in the current window.

        Args:
            user_id: The user identifier.

        Returns:
            Number of remaining requests allowed.
        """
        now = time.time()
        window_start = now - self.window_seconds
        current = [ts for ts in self._requests[user_id] if ts > window_start]
        return max(0, self.max_requests - len(current))

    def get_retry_after(self, user_id: str) -> int:
        """Get seconds until the user can make another request.

        Args:
            user_id: The user identifier.

        Returns:
            Seconds to wait before retrying.
        """
        if not self._requests[user_id]:
            return 0
        oldest_in_window = min(self._requests[user_id])
        retry_after = int(self.window_seconds - (time.time() - oldest_in_window)) + 1
        return max(1, retry_after)


# Global rate limit state (shared across requests)
_rate_limit_state = RateLimitState()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces per-user rate limiting.

    Limits each user to max 10 requests per minute. Users are identified
    by their Authorization token or IP address.

    When rate limited, returns HTTP 429 with a structured JSON response
    including a "system busy" message and Retry-After header.
    """

    def __init__(self, app, max_requests: int = DEFAULT_MAX_REQUESTS, window_seconds: int = DEFAULT_WINDOW_SECONDS):
        """Initialize the rate limiter middleware.

        Args:
            app: The ASGI application.
            max_requests: Maximum requests per window per user.
            window_seconds: Window duration in seconds.
        """
        super().__init__(app)
        self.state = RateLimitState(max_requests, window_seconds)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        """Check rate limit before processing the request.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/endpoint in the chain.

        Returns:
            Normal response or 429 rate limit response.
        """
        # Skip rate limiting for health checks, static files, and export endpoints
        path = request.url.path
        if path == "/health" or path.startswith("/static") or not path.startswith("/api"):
            return await call_next(request)
        if "/export/" in path:
            return await call_next(request)
        # Skip polling endpoints (jobs status, enrichment) — they're called frequently by frontend
        if "/jobs" in path or "/enrichment" in path:
            return await call_next(request)

        # Identify user by Authorization header or client IP
        user_id = _extract_user_id(request)

        if self.state.is_rate_limited(user_id):
            retry_after = self.state.get_retry_after(user_id)
            logger.warning(
                f"Rate limit exceeded for user '{user_id}' on {request.method} {path}"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "type": "rate_limit_exceeded",
                        "message": "System busy — please retry shortly.",
                        "statusCode": 429,
                        "correctiveAction": (
                            f"You have exceeded the maximum request rate. "
                            f"Please wait {retry_after} seconds before retrying."
                        ),
                        "retryAfter": retry_after,
                    }
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Add rate limit headers to response
        response = await call_next(request)
        remaining = self.state.get_remaining(user_id)
        response.headers["X-RateLimit-Limit"] = str(self.state.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.state.window_seconds)
        return response


def _extract_user_id(request: Request) -> str:
    """Extract a user identifier from the request.

    Uses the Authorization token if available, otherwise falls back to
    the client IP address.

    Args:
        request: The incoming request.

    Returns:
        A string identifying the user for rate limiting purposes.
    """
    # Try Authorization header first
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        # Use a hash/truncation of the token as the user ID
        return f"token:{token[:32]}"

    # Fall back to client IP
    client = request.client
    if client:
        return f"ip:{client.host}"

    return "unknown"
