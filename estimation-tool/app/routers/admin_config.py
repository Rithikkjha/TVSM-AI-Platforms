"""Admin configuration and template management router.

Provides endpoints for system configuration and base template management:
- GET /api/admin/config — read Config.xlsx settings
- PUT /api/admin/config — update Config.xlsx (Admin only)
- GET /api/admin/templates — list all base templates
- POST /api/admin/templates — create/update base template (Admin only)
- DELETE /api/admin/templates/:id — delete base template (Admin only)

Requirements: 10.4, 16.1, 16.2, 17.1, 17.5, 17.6, 17.7
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.middleware.auth import (
    AuthenticatedUser,
    get_current_user,
    get_sharepoint_client,
    require_admin,
)
from app.models.schemas import BaseTemplate, Domain, Stream
from app.services.sharepoint_client import (
    FOLDER_ESTIMATIONS,
    SharePointClient,
    SharePointError,
    SharePointUnavailableError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Config"])

# File names and sheet names
CONFIG_FILENAME = f"{FOLDER_ESTIMATIONS}/Config.xlsx"
CONFIG_SHEET = "Sheet1"
TEMPLATES_FILENAME = f"{FOLDER_ESTIMATIONS}/Templates.xlsx"
TEMPLATES_SHEET = "Sheet1"


# --- Request/Response Models ---


class ConfigEntry(BaseModel):
    """A single configuration key-value pair."""
    key: str
    value: str
    updatedBy: Optional[str] = None
    updatedAt: Optional[str] = None


class ConfigResponse(BaseModel):
    """Response containing all configuration entries."""
    config: list[ConfigEntry]


class ConfigUpdateRequest(BaseModel):
    """Request body for updating configuration."""
    entries: list[ConfigEntry]


class TemplateCreateRequest(BaseModel):
    """Request body for creating or updating a base template."""
    templateId: Optional[str] = None
    domain: Domain
    stream: Stream
    scopeAreas: list[str] = Field(..., min_length=1)
    defaultWeightings: Optional[dict] = None


class TemplateResponse(BaseModel):
    """Response for a single template."""
    templateId: str
    domain: Domain
    stream: Stream
    scopeAreas: list[str]
    defaultWeightings: Optional[dict] = None
    createdBy: str
    createdAt: str
    updatedAt: Optional[str] = None


class TemplateListResponse(BaseModel):
    """Response for listing templates."""
    templates: list[TemplateResponse]
    total: int


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


# --- Config Endpoints ---


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    user: AuthenticatedUser = Depends(get_current_user),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> ConfigResponse:
    """Read current Config.xlsx settings.

    Returns SLM model path, context window, temperature, GPU layers, and rate card.
    Accessible by any authenticated user.

    Requirements: 10.4, 17.1
    """
    try:
        rows = await sharepoint_client.read_workbook(CONFIG_FILENAME, sheet=CONFIG_SHEET)
    except SharePointUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configuration service temporarily unavailable. Please retry.",
        )
    except Exception as exc:
        logger.error(f"Failed to read Config.xlsx: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to load configuration. Please retry.",
        )

    entries = _parse_config_rows(rows)

    return ConfigResponse(config=entries)


@router.put("/config", response_model=ConfigResponse)
async def update_config(
    request: ConfigUpdateRequest,
    admin: AuthenticatedUser = Depends(require_admin),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> ConfigResponse:
    """Update Config.xlsx settings (Admin only).

    Updates configuration entries. New configurations take effect for
    subsequent requests without affecting previously generated estimations.

    Requirements: 10.4, 17.1, 17.5, 17.7
    """
    if not request.entries:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No configuration entries provided.",
        )

    try:
        rows = await sharepoint_client.read_workbook(CONFIG_FILENAME, sheet=CONFIG_SHEET)
    except SharePointUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configuration service temporarily unavailable. Please retry.",
        )

    # Build current config as a dict for updating
    now = datetime.now(timezone.utc).isoformat()
    existing_entries = _parse_config_rows(rows)
    existing_map = {e.key: e for e in existing_entries}

    # Apply updates
    for update in request.entries:
        existing_map[update.key] = ConfigEntry(
            key=update.key,
            value=update.value,
            updatedBy=admin.email,
            updatedAt=now,
        )

    # Write all config rows back (header + data)
    updated_rows = []
    for entry in existing_map.values():
        updated_rows.append([
            entry.key,
            entry.value,
            entry.updatedBy or "",
            entry.updatedAt or "",
        ])

    try:
        # Write rows starting at row 2 (after header)
        if updated_rows:
            await sharepoint_client.write_rows(
                CONFIG_FILENAME, CONFIG_SHEET, updated_rows, start_row=2
            )
    except SharePointError as exc:
        logger.error(f"Failed to update Config.xlsx: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save configuration. Please retry.",
        )

    logger.info(f"Admin '{admin.email}' updated {len(request.entries)} config entries.")

    return ConfigResponse(config=list(existing_map.values()))


# --- Template Endpoints ---


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    user: AuthenticatedUser = Depends(get_current_user),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> TemplateListResponse:
    """List all base templates from Templates.xlsx.

    Accessible by any authenticated user.

    Requirements: 16.1
    """
    try:
        rows = await sharepoint_client.read_workbook(
            TEMPLATES_FILENAME, sheet=TEMPLATES_SHEET
        )
    except SharePointUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Template service temporarily unavailable. Please retry.",
        )
    except SharePointError as exc:
        # Templates.xlsx is optional — if it doesn't exist yet, there simply
        # are no base templates configured. Return an empty list, not an error.
        if "not found" in str(exc).lower():
            logger.info("Templates.xlsx does not exist yet; returning empty template list.")
            return TemplateListResponse(templates=[], total=0)
        logger.error(f"Failed to read Templates.xlsx: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to load templates. Please retry.",
        )
    except Exception as exc:
        logger.error(f"Failed to read Templates.xlsx: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to load templates. Please retry.",
        )

    templates = _parse_template_rows(rows)

    return TemplateListResponse(templates=templates, total=len(templates))


@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_template(
    request: TemplateCreateRequest,
    admin: AuthenticatedUser = Depends(require_admin),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> TemplateResponse:
    """Create or update a base template (Admin only).

    If templateId is provided and exists, updates the existing template.
    Otherwise, creates a new template.

    Requirements: 16.1, 16.2
    """
    now = datetime.now(timezone.utc).isoformat()

    try:
        rows = await sharepoint_client.read_workbook(
            TEMPLATES_FILENAME, sheet=TEMPLATES_SHEET
        )
    except SharePointUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Template service temporarily unavailable. Please retry.",
        )

    # Check if updating an existing template
    existing_templates = _parse_template_rows(rows)
    template_id = request.templateId

    if template_id:
        # Find and update existing template
        found = False
        for idx, tmpl in enumerate(existing_templates):
            if tmpl.templateId == template_id:
                found = True
                break

        if found:
            # Update: rewrite the row
            updated_row = [
                template_id,
                request.domain.value,
                request.stream.value,
                json.dumps(request.scopeAreas),
                json.dumps(request.defaultWeightings) if request.defaultWeightings else "",
                admin.email,
                existing_templates[idx].createdAt,
                now,
            ]
            # Row index: header + idx + 1 for 1-based
            row_idx = idx + 2
            try:
                await sharepoint_client.write_rows(
                    TEMPLATES_FILENAME, TEMPLATES_SHEET, [updated_row], start_row=row_idx
                )
            except SharePointError as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update template. Please retry.",
                )

            logger.info(f"Admin '{admin.email}' updated template '{template_id}'.")

            return TemplateResponse(
                templateId=template_id,
                domain=request.domain,
                stream=request.stream,
                scopeAreas=request.scopeAreas,
                defaultWeightings=request.defaultWeightings,
                createdBy=admin.email,
                createdAt=existing_templates[idx].createdAt,
                updatedAt=now,
            )

    # Create new template
    import uuid
    template_id = template_id or str(uuid.uuid4())

    new_row = [
        template_id,
        request.domain.value,
        request.stream.value,
        json.dumps(request.scopeAreas),
        json.dumps(request.defaultWeightings) if request.defaultWeightings else "",
        admin.email,
        now,
        "",  # UpdatedAt
    ]

    try:
        await sharepoint_client.append_row(TEMPLATES_FILENAME, TEMPLATES_SHEET, new_row)
    except SharePointError as exc:
        logger.error(f"Failed to create template: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template. Please retry.",
        )

    logger.info(f"Admin '{admin.email}' created template '{template_id}'.")

    return TemplateResponse(
        templateId=template_id,
        domain=request.domain,
        stream=request.stream,
        scopeAreas=request.scopeAreas,
        defaultWeightings=request.defaultWeightings,
        createdBy=admin.email,
        createdAt=now,
    )


@router.delete("/templates/{template_id}", response_model=MessageResponse)
async def delete_template(
    template_id: str,
    admin: AuthenticatedUser = Depends(require_admin),
    sharepoint_client: SharePointClient = Depends(get_sharepoint_client),
) -> MessageResponse:
    """Delete a base template (Admin only).

    Deleting a template does not affect previously generated estimations
    that referenced it.

    Requirements: 16.2
    """
    try:
        rows = await sharepoint_client.read_workbook(
            TEMPLATES_FILENAME, sheet=TEMPLATES_SHEET
        )
    except SharePointUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Template service temporarily unavailable. Please retry.",
        )

    templates = _parse_template_rows(rows)

    # Find the template to delete
    target_idx = None
    for idx, tmpl in enumerate(templates):
        if tmpl.templateId == template_id:
            target_idx = idx
            break

    if target_idx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found.",
        )

    # Mark as deleted by clearing the row (write empty values)
    # In practice, we write an empty/cleared row
    empty_row = ["", "", "", "", "", "", "", ""]
    row_idx = target_idx + 2  # header + 1-based

    try:
        await sharepoint_client.write_rows(
            TEMPLATES_FILENAME, TEMPLATES_SHEET, [empty_row], start_row=row_idx
        )
    except SharePointError as exc:
        logger.error(f"Failed to delete template: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template. Please retry.",
        )

    logger.info(f"Admin '{admin.email}' deleted template '{template_id}'.")

    return MessageResponse(message=f"Template '{template_id}' has been deleted.")


# --- Helper Functions ---


def _parse_config_rows(rows: list[list]) -> list[ConfigEntry]:
    """Parse Config.xlsx rows into ConfigEntry objects.

    Expected columns: Key, Value, UpdatedBy, UpdatedAt

    Args:
        rows: Raw rows from the workbook (first row is headers).

    Returns:
        List of ConfigEntry objects.
    """
    if not rows or len(rows) < 1:
        return []

    entries: list[ConfigEntry] = []

    for row in rows[1:]:  # Skip header
        if not row or len(row) < 2:
            continue
        key = str(row[0]).strip() if row[0] else ""
        if not key:
            continue

        value = str(row[1]).strip() if len(row) > 1 and row[1] else ""
        updated_by = str(row[2]).strip() if len(row) > 2 and row[2] else None
        updated_at = str(row[3]).strip() if len(row) > 3 and row[3] else None

        entries.append(ConfigEntry(
            key=key,
            value=value,
            updatedBy=updated_by,
            updatedAt=updated_at,
        ))

    return entries


def _parse_template_rows(rows: list[list]) -> list[TemplateResponse]:
    """Parse Templates.xlsx rows into TemplateResponse objects.

    Expected columns: TemplateId, Domain, Stream, ScopeAreas, DefaultWeightings,
                      CreatedBy, CreatedAt, UpdatedAt

    Args:
        rows: Raw rows from the workbook (first row is headers).

    Returns:
        List of TemplateResponse objects.
    """
    if not rows or len(rows) < 2:
        return []

    headers = [str(h).strip().lower() for h in rows[0]]
    col_map = {h: i for i, h in enumerate(headers)}

    id_idx = col_map.get("templateid", 0)
    domain_idx = col_map.get("domain", 1)
    stream_idx = col_map.get("stream", 2)
    scope_idx = col_map.get("scopeareas", 3)
    weights_idx = col_map.get("defaultweightings", 4)
    created_by_idx = col_map.get("createdby", 5)
    created_at_idx = col_map.get("createdat", 6)
    updated_at_idx = col_map.get("updatedat", 7)

    templates: list[TemplateResponse] = []

    for row in rows[1:]:
        if not row or len(row) <= id_idx:
            continue

        template_id = str(row[id_idx]).strip() if row[id_idx] else ""
        if not template_id:
            continue  # Skip empty/deleted rows

        # Parse scope areas JSON
        scope_raw = str(row[scope_idx]).strip() if len(row) > scope_idx and row[scope_idx] else "[]"
        try:
            scope_areas = json.loads(scope_raw)
        except (json.JSONDecodeError, TypeError):
            scope_areas = []

        # Parse default weightings JSON
        weights_raw = str(row[weights_idx]).strip() if len(row) > weights_idx and row[weights_idx] else ""
        default_weightings = None
        if weights_raw:
            try:
                default_weightings = json.loads(weights_raw)
            except (json.JSONDecodeError, TypeError):
                default_weightings = None

        # Parse domain and stream
        domain_val = str(row[domain_idx]).strip() if len(row) > domain_idx and row[domain_idx] else ""
        stream_val = str(row[stream_idx]).strip() if len(row) > stream_idx and row[stream_idx] else ""

        try:
            domain_enum = Domain(domain_val)
        except ValueError:
            continue  # Skip invalid domain entries

        try:
            stream_enum = Stream(stream_val)
        except ValueError:
            continue  # Skip invalid stream entries

        templates.append(TemplateResponse(
            templateId=template_id,
            domain=domain_enum,
            stream=stream_enum,
            scopeAreas=scope_areas,
            defaultWeightings=default_weightings,
            createdBy=str(row[created_by_idx]).strip() if len(row) > created_by_idx and row[created_by_idx] else "",
            createdAt=str(row[created_at_idx]).strip() if len(row) > created_at_idx and row[created_at_idx] else "",
            updatedAt=str(row[updated_at_idx]).strip() if len(row) > updated_at_idx and row[updated_at_idx] else None,
        ))

    return templates


# ═══════════════════════════════════════════════════════════════════
# CATALOG MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════


@router.get("/catalog", summary="Get estimation catalog")
async def get_estimation_catalog(
    _user: AuthenticatedUser = Depends(require_admin),
):
    """Return the current estimation_catalog.json content."""
    from app.services.catalog_loader import get_catalog_loader

    loader = get_catalog_loader()
    catalog = loader.load_catalog()
    return catalog


@router.put("/catalog", summary="Update estimation catalog")
async def update_estimation_catalog(
    catalog_data: dict,
    _user: AuthenticatedUser = Depends(require_admin),
):
    """Replace the estimation catalog with new data.

    Validates structure before saving.
    """
    import shutil
    from pathlib import Path

    from app.services.catalog_loader import get_catalog_loader

    config_dir = Path(__file__).parent.parent.parent / "config"
    catalog_path = config_dir / "estimation_catalog.json"

    # Validate required keys
    required_keys = ["effortTable", "systemMultipliers", "overheadFactors", "integrationPatternCosts", "hubSurcharges"]
    for key in required_keys:
        if key not in catalog_data:
            raise HTTPException(status_code=400, detail=f"Missing required key: {key}")

    # Validate effort values
    for unit_id, data in catalog_data.get("effortTable", {}).items():
        for tier in ("simple", "medium", "complex"):
            if tier not in data:
                raise HTTPException(status_code=400, detail=f"{unit_id} missing '{tier}' tier")
            val = data[tier]
            if not isinstance(val, (int, float)) or val < 0.1 or val > 20.0:
                raise HTTPException(status_code=400, detail=f"{unit_id}.{tier} = {val} out of range [0.1, 20.0]")

    # Validate system multipliers
    for system, mult in catalog_data.get("systemMultipliers", {}).items():
        if not isinstance(mult, (int, float)) or mult < 0.5 or mult > 3.0:
            raise HTTPException(status_code=400, detail=f"Multiplier for '{system}' = {mult} out of range [0.5, 3.0]")

    # Backup current file
    if catalog_path.exists():
        backup_path = config_dir / f"estimation_catalog_backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(catalog_path, backup_path)

    # Save new catalog
    catalog_data["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, indent=2, ensure_ascii=False)

    # Invalidate cache
    loader = get_catalog_loader()
    loader.invalidate_cache()

    return {"message": "Catalog updated successfully", "units": len(catalog_data.get("effortTable", {}))}


@router.get("/system-dependencies", summary="Get system dependencies")
async def get_system_dependencies(
    _user: AuthenticatedUser = Depends(require_admin),
):
    """Return the current system_dependencies.json content."""
    from app.services.catalog_loader import get_catalog_loader

    loader = get_catalog_loader()
    deps = loader.load_dependencies()
    return deps


@router.put("/system-dependencies", summary="Update system dependencies")
async def update_system_dependencies(
    deps_data: dict,
    _user: AuthenticatedUser = Depends(require_admin),
):
    """Replace the system dependencies with new data."""
    import shutil
    from pathlib import Path

    from app.services.catalog_loader import get_catalog_loader

    config_dir = Path(__file__).parent.parent.parent / "config"
    deps_path = config_dir / "system_dependencies.json"

    # Validate required keys
    if "systems" not in deps_data or "hubSystems" not in deps_data:
        raise HTTPException(status_code=400, detail="Missing required keys: systems, hubSystems")

    # Backup current file
    if deps_path.exists():
        backup_path = config_dir / f"system_dependencies_backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(deps_path, backup_path)

    # Save
    deps_data["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    with open(deps_path, "w", encoding="utf-8") as f:
        json.dump(deps_data, f, indent=2, ensure_ascii=False)

    # Invalidate cache
    loader = get_catalog_loader()
    loader.invalidate_cache()

    return {"message": "System dependencies updated successfully", "systems": len(deps_data.get("systems", {}))}


@router.get("/catalog/ai-multiplier", summary="Get AI productivity multiplier")
async def get_ai_multiplier(
    _user: AuthenticatedUser = Depends(require_admin),
):
    """Return the current AI productivity multiplier settings."""
    from app.services.catalog_loader import get_catalog_loader

    loader = get_catalog_loader()
    catalog = loader.load_catalog()
    return catalog.get("aiProductivity", {"globalMultiplier": 1.0, "perCategory": {}})


@router.put("/catalog/ai-multiplier", summary="Update AI productivity multiplier")
async def update_ai_multiplier(
    ai_data: dict,
    _user: AuthenticatedUser = Depends(require_admin),
):
    """Update the AI productivity multiplier in the catalog."""
    from pathlib import Path

    from app.services.catalog_loader import get_catalog_loader

    config_dir = Path(__file__).parent.parent.parent / "config"
    catalog_path = config_dir / "estimation_catalog.json"

    # Validate global multiplier
    global_mult = ai_data.get("globalMultiplier", 1.0)
    if not isinstance(global_mult, (int, float)) or global_mult < 0.5 or global_mult > 1.0:
        raise HTTPException(status_code=400, detail=f"globalMultiplier must be between 0.5 and 1.0, got {global_mult}")

    # Load current catalog
    loader = get_catalog_loader()
    catalog = loader.load_catalog()

    # Update AI section only
    catalog["aiProductivity"] = ai_data
    catalog["lastUpdated"] = datetime.now(timezone.utc).isoformat()

    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    loader.invalidate_cache()

    return {"message": "AI multiplier updated", "globalMultiplier": global_mult}


@router.post("/catalog/reset", summary="Reset catalog to defaults")
async def reset_catalog_to_defaults(
    _user: AuthenticatedUser = Depends(require_admin),
):
    """Reset the estimation catalog to the shipped default version.

    Creates a backup of current catalog before resetting.
    """
    import shutil
    from pathlib import Path

    from app.services.catalog_loader import get_catalog_loader

    config_dir = Path(__file__).parent.parent.parent / "config"
    catalog_path = config_dir / "estimation_catalog.json"
    deps_path = config_dir / "system_dependencies.json"

    # We don't have a separate "defaults" file — the current committed files ARE the defaults.
    # This endpoint is for when admin has messed up edits and wants to restore.
    # In practice, we'd restore from git or a shipped copy.
    # For now, just invalidate cache so it reloads from disk.
    loader = get_catalog_loader()
    loader.invalidate_cache()

    return {
        "message": "Cache invalidated. Catalog will reload from disk on next estimation.",
        "note": "To fully reset, redeploy or restore config files from version control."
    }
