"""Azure AD (Entra ID) SSO login for the SmartBrain web app + REST API.

Browser users sign in with their org account using the OIDC
authorization-code flow (via MSAL ``ConfidentialClientApplication``). A minimal
user dict is stored in a signed session cookie (Starlette ``SessionMiddleware``).

Enforcement is secure-by-default: ``settings.require_login`` is True unless the
operator explicitly sets ``REQUIRE_LOGIN=false``. The MCP server and
``/v1/health`` are intentionally NOT protected by this module.

Deployment note (nginx + ``--root-path /brain``)
------------------------------------------------
In production the app runs as::

    uvicorn api.app:app --host 0.0.0.0 --port 8000 --root-path /brain

behind nginx, which strips the ``/brain`` prefix before forwarding. So the app
sees request paths WITHOUT ``/brain``, but any absolute URL we hand to Azure
(the ``redirect_uri``) must include ``/brain`` to match what IT registered:

    https://smartbrain.tvsmotor.net/brain/auth/callback

We therefore build the redirect URI from the forwarded scheme/host
(``X-Forwarded-Proto`` / ``X-Forwarded-Host``, set by nginx) plus the
configured ``azure_redirect_path`` (which already includes ``/brain``), rather
than from ``request.url`` (which would be missing the prefix / show http).
"""

from __future__ import annotations

import logging
from typing import Any

import msal
from config.settings import get_settings
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# OIDC scopes — keep minimal. MSAL always adds the reserved scopes
# (openid/profile/offline_access) itself and rejects them if passed explicitly,
# so we request no extra resource scopes: an empty list yields an id token with
# the standard profile claims (name/preferred_username/oid), which is all we
# need to identify the user.
LOGIN_SCOPES: list[str] = []

# Session keys.
_SESSION_USER_KEY = "user"
_SESSION_FLOW_KEY = "auth_flow"

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# MSAL client + URL helpers
# ---------------------------------------------------------------------------


def _authority(settings: Any) -> str:
    """Single-tenant authority URL for the configured tenant."""
    return f"https://login.microsoftonline.com/{settings.azure_tenant_id}"


def _build_msal_app(settings: Any) -> msal.ConfidentialClientApplication:
    """Construct a confidential-client MSAL app from settings."""
    return msal.ConfidentialClientApplication(
        client_id=settings.azure_client_id,
        client_credential=settings.azure_client_secret,
        authority=_authority(settings),
    )


def _forwarded_base(request: Request) -> str:
    """Return the public ``scheme://host`` as seen by the browser.

    Honors nginx's ``X-Forwarded-Proto`` / ``X-Forwarded-Host`` headers so we
    reconstruct ``https://smartbrain.tvsmotor.net`` even though the app itself
    is reached over plain http on :8000 behind the proxy. Falls back to the
    request URL components when the headers are absent (local dev).
    """
    proto = request.headers.get("x-forwarded-proto")
    if not proto:
        proto = request.url.scheme
    # X-Forwarded-Host may contain a comma-separated list; take the first.
    fwd_host = request.headers.get("x-forwarded-host")
    if fwd_host:
        host = fwd_host.split(",")[0].strip()
    else:
        host = request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}"


def _redirect_uri(request: Request, settings: Any) -> str:
    """Full public redirect URI that must match the Azure app registration.

    Built as ``<forwarded-base><azure_redirect_path>`` so it includes the
    ``/brain`` prefix and uses https in production.
    """
    return _forwarded_base(request) + settings.azure_redirect_path


def _absolute_path(request: Request, path: str) -> str:
    """Turn a public path (e.g. ``/brain/chatbot/``) into an absolute URL."""
    return _forwarded_base(request) + path


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """Start the OIDC auth-code flow and redirect to Microsoft (302)."""
    settings = get_settings()
    msal_app = _build_msal_app(settings)
    redirect_uri = _redirect_uri(request, settings)

    # initiate_auth_code_flow generates state + PKCE and returns a dict we must
    # stash in the session to validate the callback.
    flow = msal_app.initiate_auth_code_flow(
        scopes=LOGIN_SCOPES,
        redirect_uri=redirect_uri,
    )
    request.session[_SESSION_FLOW_KEY] = flow
    return RedirectResponse(url=flow["auth_uri"], status_code=302)


@router.get("/callback")
async def callback(request: Request):
    """Handle the redirect from Microsoft and complete the token exchange."""
    settings = get_settings()
    flow = request.session.pop(_SESSION_FLOW_KEY, None)
    if not flow:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_state", "message": "No auth flow in session; start at /auth/login"},
        )

    msal_app = _build_msal_app(settings)
    try:
        # MSAL validates the state and exchanges the code. It reads the auth
        # response params (code/state/error) from the query dict we pass.
        result = msal_app.acquire_token_by_auth_code_flow(
            flow, dict(request.query_params)
        )
    except ValueError as exc:
        # Raised on state mismatch / malformed response.
        logger.warning("Auth callback state validation failed: %s", exc)
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_state", "message": "Authentication state mismatch"},
        )

    if "error" in result:
        logger.warning(
            "Token exchange error: %s / %s",
            result.get("error"),
            result.get("error_description"),
        )
        return JSONResponse(
            status_code=401,
            content={
                "error": result.get("error", "token_error"),
                "message": result.get("error_description", "Token exchange failed"),
            },
        )

    claims = result.get("id_token_claims") or {}
    user = {
        "oid": claims.get("oid"),
        "name": claims.get("name"),
        "preferred_username": claims.get("preferred_username"),
        "email": claims.get("email") or claims.get("preferred_username"),
    }
    request.session[_SESSION_USER_KEY] = user

    # Land on the chatbot UI (absolute, so it survives the /brain prefix).
    return RedirectResponse(
        url=_absolute_path(request, settings.azure_post_login_path),
        status_code=302,
    )


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """Clear the local session and return to the app's own sign-in screen.

    We intentionally do NOT bounce through the Microsoft federated logout
    endpoint: that would land the user on Microsoft's "signed out" page. The
    desired UX is to drop the local session and come straight back to the
    chatbot, where the UI shows the in-app "Sign in" card (driven by
    /auth/me). The user's Microsoft SSO session is left intact, so the next
    sign-in is one click.
    """
    settings = get_settings()
    request.session.clear()
    home = _absolute_path(request, settings.azure_post_login_path)
    return RedirectResponse(url=home, status_code=302)


@router.get("/me")
async def me(request: Request):
    """Return the current user JSON, or 401 if not signed in."""
    user = request.session.get(_SESSION_USER_KEY)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "message": "Not signed in"},
        )
    return user


# ---------------------------------------------------------------------------
# Enforcement dependency
# ---------------------------------------------------------------------------


def _wants_html(request: Request) -> bool:
    """Heuristic: does this look like a browser navigation (vs an API client)?"""
    accept = request.headers.get("accept", "")
    return "text/html" in accept


class ChatbotLoginGateMiddleware(BaseHTTPMiddleware):
    """Redirect unauthenticated browsers hitting the chatbot UI to /auth/login.

    The chatbot UI is a ``StaticFiles`` mount, which cannot take a FastAPI
    dependency, so it is gated here instead. Only ``/chatbot`` paths are
    guarded — the /v1 API is gated by the ``require_login`` dependency, and
    /auth/*, /mcp, and /v1/health stay open. No-ops when login is disabled.

    MUST be installed so that SessionMiddleware wraps it (i.e. added to the app
    BEFORE SessionMiddleware), otherwise ``request.session`` is unavailable.
    """

    async def dispatch(self, request: Request, call_next):
        # The chatbot UI shell (static HTML/CSS/JS) is always allowed to load.
        # It is a public shell with no data in it; when the user has no session
        # the UI shows a "Sign in" screen (driven by /auth/me) and the user
        # clicks through to Microsoft via /auth/login. The actual data API
        # (/v1/*) stays gated by the ``require_login`` dependency, so nothing
        # sensitive is served to an unauthenticated client. This middleware is
        # kept as a passthrough so the login experience is a visible sign-in
        # page rather than an immediate browser redirect.
        return await call_next(request)


async def require_login(request: Request) -> dict[str, Any] | None:
    """FastAPI dependency enforcing SSO login.

    - If ``settings.require_login`` is False, allow unauthenticated access.
    - Otherwise require a user in the session. On miss:
        * browser (HTML Accept)  -> 302 redirect to /auth/login
        * API / JSON client      -> 401 JSON
    """
    settings = get_settings()
    if not settings.require_login:
        return None

    user = request.session.get(_SESSION_USER_KEY)
    if user:
        return user

    if _wants_html(request):
        # Build the login URL honoring the /brain prefix.
        login_url = _absolute_path(request, "/brain/auth/login")
        raise HTTPException(
            status_code=302,
            headers={"Location": login_url},
            detail="redirect_to_login",
        )
    raise HTTPException(
        status_code=401,
        detail={"error": "unauthorized", "message": "Login required"},
    )
