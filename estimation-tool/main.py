"""Project Estimation Tool - FastAPI Application."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.middleware.error_handler import GlobalExceptionHandlerMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.routers.admin_users import router as admin_users_router
from app.routers.estimations import router as estimations_router
from app.routers.admin_config import router as admin_config_router
from app.routers.prd_checker import router as prd_checker_router
from app.routers.build_vs_buy import router as build_vs_buy_router
from app.routers.vendor_compare import router as vendor_compare_router
from app.routers.mpcp_tracker import router as mpcp_tracker_router
from app.routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup: Ensure all required SharePoint files exist
    try:
        from app.services.sharepoint_client import SharePointClient
        sp = SharePointClient()
        await sp.initialize_sharepoint_structure()
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            f"SharePoint initialization skipped (will retry on first use): {exc}"
        )
    yield
    # Shutdown: cleanup resources


app = FastAPI(
    title="Project Estimation Tool",
    description=(
        "A self-service web application that leverages an embedded SLM "
        "to generate effort estimations from business and technical documents."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware stack (order matters: last added = outermost = first to process)
# 1. CORS - restricted in production, open in dev
_cors_origins = ["*"] if os.getenv("DEV_MODE", "false").lower() in ("true", "1") else [
    os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:8000"),
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Global exception handler - catches unhandled errors from all downstream
app.add_middleware(GlobalExceptionHandlerMiddleware)

# 3. Rate limiter - applied per-user before request reaches routers
app.add_middleware(RateLimiterMiddleware, max_requests=100, window_seconds=60)

# 4. GZip compression - reduces HTML/JSON transfer size (228KB HTML → ~40KB compressed)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Register routers
app.include_router(admin_users_router)
app.include_router(estimations_router)
app.include_router(admin_config_router)
app.include_router(prd_checker_router)
app.include_router(build_vs_buy_router)
app.include_router(vendor_compare_router)
app.include_router(mpcp_tracker_router)
app.include_router(auth_router)


# ---- DEV MODE: Skip auth when DEV_MODE=true ----
if os.getenv("DEV_MODE", "false").lower() in ("true", "1", "yes"):
    from app.middleware.auth import (
        AuthenticatedUser,
        get_current_user,
        get_sharepoint_client,
        require_admin,
    )
    from app.models.schemas import UserIdentity, UserRole
    from app.services.sharepoint_client import SharePointClient

    # Mock user for dev mode
    _dev_user = AuthenticatedUser(
        identity=UserIdentity(
            corporateId="DEV001",
            email="suraj.ray@tvsmotor.com",
            displayName="Suraj Ray",
        ),
        role=UserRole.ADMIN,
    )

    async def _dev_get_current_user():
        return _dev_user

    async def _dev_require_admin():
        return _dev_user

    def _dev_get_sharepoint_client():
        return SharePointClient()

    app.dependency_overrides[get_current_user] = _dev_get_current_user
    app.dependency_overrides[require_admin] = _dev_require_admin
# ---- END DEV MODE ----


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "devMode": os.getenv("DEV_MODE", "false")}


@app.get("/health/detailed")
async def health_check_detailed():
    """Detailed health check with component status."""
    return {
        "status": "healthy",
        "components": {
            "api": "up",
            "slm": "unknown",
            "sharepoint": "unknown",
        },
    }


@app.post("/api/admin/migrate-folders")
async def migrate_sharepoint_folders():
    """One-time migration: move files from root to module-based folders.

    Copies existing files at root into the new folder structure:
    - Config.xlsx, Templates.xlsx, EstimationIndex.xlsx, Estimations_*.xlsx, AuditLog_*.xlsx → Estimations/
    - Users.xlsx → Admin/
    - Templates/ → PrdCheck/Templates/

    Safe to run multiple times (skips if destination already exists).
    """
    from app.services.sharepoint_client import (
        SharePointClient, FOLDER_ESTIMATIONS, FOLDER_ADMIN, FOLDER_PRD_CHECK
    )

    sp = SharePointClient()
    results = []

    # Files to move to Estimations/
    estimation_files = ["Config.xlsx", "Templates.xlsx", "EstimationIndex.xlsx"]

    # Also find monthly files
    from datetime import datetime, timezone
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    estimation_files.append(f"Estimations_{current_month}.xlsx")
    estimation_files.append(f"AuditLog_{current_month}.xlsx")

    for filename in estimation_files:
        try:
            if await sp.file_exists(filename):
                content = await sp._download_file(filename)
                dest = f"{FOLDER_ESTIMATIONS}/{filename}"
                if not await sp.file_exists(dest):
                    await sp._upload_file(dest, content)
                    results.append(f"✓ {filename} → {dest}")
                else:
                    results.append(f"⊘ {dest} already exists, skipped")
            else:
                results.append(f"⊘ {filename} not found at root, skipped")
        except Exception as e:
            results.append(f"✗ {filename}: {str(e)[:100]}")

    # Users.xlsx → Admin/
    try:
        if await sp.file_exists("Users.xlsx"):
            content = await sp._download_file("Users.xlsx")
            dest = f"{FOLDER_ADMIN}/Users.xlsx"
            if not await sp.file_exists(dest):
                await sp._upload_file(dest, content)
                results.append(f"✓ Users.xlsx → {dest}")
            else:
                results.append(f"⊘ {dest} already exists, skipped")
        else:
            results.append(f"⊘ Users.xlsx not found at root, skipped")
    except Exception as e:
        results.append(f"✗ Users.xlsx: {str(e)[:100]}")

    # Templates/ → PrdCheck/Templates/
    for doc_type in ["prd", "brd", "hld", "lld"]:
        for ext in ["sections.json", "template.docx", "template.pdf"]:
            src = f"Templates/{doc_type}_{ext}"
            dest = f"{FOLDER_PRD_CHECK}/Templates/{doc_type}_{ext}"
            try:
                src_content = await sp.download_template_sections(doc_type) if ext == "sections.json" else None
                if ext == "sections.json" and src_content:
                    if not await sp.file_exists(dest):
                        await sp.upload_template_sections(doc_type, src_content)
                        results.append(f"✓ {src} → {dest}")
                    else:
                        results.append(f"⊘ {dest} already exists, skipped")
            except Exception:
                pass  # Skip missing template files silently

    return {"message": "Migration complete", "results": results}


# Mount static files for frontend SPA
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


# Add no-cache headers for HTML and JS to ensure latest code is served
from starlette.middleware.base import BaseHTTPMiddleware

class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path == "/" or path.endswith(".html") or path.endswith(".js"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheStaticMiddleware)
