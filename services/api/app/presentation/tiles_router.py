"""
Tiles Router - Dynamic Tiling API

Provides authenticated tile endpoints for AOIs using TiTiler + MosaicJSON.
Part of ADR-0007: Dynamic Tiling with MosaicJSON.

Endpoints:
- GET /tiles/aois/{aoi_id}/{z}/{x}/{y}.png - Tile for AOI
- GET /tiles/aois/{aoi_id}/tilejson.json - TileJSON metadata
- POST /tiles/aois/{aoi_id}/export - Export COG on-demand
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import RedirectResponse
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from sqlalchemy.orm import Session
import structlog

from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership, get_current_tenant_id
from app.config import settings
from app.application.dtos.tiles import (
    TileExportCommand,
    TileExportStatusCommand,
    TileJsonCommand,
    TileRequestCommand,
)
from app.application.tiles_config import EXPRESSIONS
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.di_container import ApiContainer

logger = structlog.get_logger()
router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])


@router.get("/tiles/aois/{aoi_id}/{z}/{x}/{y}.png")
async def get_aoi_tile(
    aoi_id: UUID,
    z: int,
    x: int,
    y: int,
    index: str = Query("ndvi", description="Vegetation index to render"),
    year: Optional[int] = Query(None, description="ISO year (default: current)"),
    week: Optional[int] = Query(None, description="ISO week (default: current)"),
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
):
    """
    Get a map tile for an AOI with the specified vegetation index.

    The tile is dynamically rendered by TiTiler using MosaicJSON.
    Results are cached by CDN for 7 days.

    - **aoi_id**: Area of Interest UUID
    - **z/x/y**: Tile coordinates (Web Mercator)
    - **index**: Vegetation index (ndvi, ndwi, ndmi, evi, savi, ndre, gndvi)
    - **year/week**: ISO year and week number (default: current week)
    """
    container = ApiContainer()
    use_case = container.tile_use_case(db)
    try:
        result = await use_case.execute(
            TileRequestCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                aoi_id=aoi_id,
                z=z,
                x=x,
                y=y,
                index=index,
                year=year,
                week=week,
            )
        )
    except ValueError as exc:
        if str(exc) == "AOI_NOT_FOUND":
            raise HTTPException(status_code=404, detail="AOI not found")
        if str(exc) == "INVALID_INDEX":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid index '{index}'. Valid options: {', '.join(EXPRESSIONS.keys())}",
            )
        raise

    logger.debug(
        "tile_request",
        aoi_id=str(aoi_id),
        z=z, x=x, y=y,
        index=result.index,
        year=result.year,
        week=result.week,
    )

    # Redirect to TiTiler (CDN will cache the response)
    response = RedirectResponse(url=result.url, status_code=307)
    response.headers["Cache-Control"] = "public, max-age=604800, immutable"  # 7 days
    response.headers["X-VivaCampo-Index"] = result.index
    response.headers["X-VivaCampo-Week"] = f"{result.year}-W{result.week:02d}"
    return response


@router.get("/tiles/aois/{aoi_id}/tilejson.json")
async def get_aoi_tilejson(
    aoi_id: UUID,
    index: str = Query("ndvi", description="Vegetation index"),
    year: Optional[int] = Query(None, description="ISO year"),
    week: Optional[int] = Query(None, description="ISO week"),
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
):
    """
    Get TileJSON metadata for an AOI.

    Used by GIS tools (QGIS, ArcGIS, Mapbox) for layer configuration.
    Returns tile URL template, bounds, center, and zoom levels.
    """
    container = ApiContainer()
    use_case = container.tilejson_use_case(db)
    try:
        return await use_case.execute(
            TileJsonCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                aoi_id=aoi_id,
                index=index,
                year=year,
                week=week,
            )
        )
    except ValueError as exc:
        if str(exc) == "AOI_NOT_FOUND":
            raise HTTPException(status_code=404, detail="AOI not found")
        raise


@router.get("/tiles/config")
async def get_tiles_config():
    """
    Get tile serving configuration for frontend.

    Returns CDN URL if enabled, otherwise returns API base URL.
    Used by frontend to determine which URL to use for tile requests.
    """
    cdn_enabled = getattr(settings, 'cdn_enabled', False)
    cdn_url = getattr(settings, 'cdn_tiles_url', None)

    if cdn_enabled and cdn_url:
        tiles_base_url = cdn_url
    else:
        tiles_base_url = getattr(settings, 'api_base_url', 'http://localhost:8000')

    return {
        "tiles_base_url": tiles_base_url,
        "cdn_enabled": cdn_enabled,
        "cache_ttl": getattr(settings, 'cdn_cache_ttl', 604800),
        "available_indices": list(EXPRESSIONS.keys()),
    }


@router.get("/tiles/indices")
async def list_available_indices():
    """
    List all available vegetation indices.

    Returns index names, descriptions, and valid value ranges.
    """
    return {
        "indices": [
            {
                "id": "ndvi",
                "name": "Normalized Difference Vegetation Index",
                "description": "Measures vegetation health and density",
                "range": [-1, 1],
                "typical_range": [-0.2, 0.8],
            },
            {
                "id": "ndwi",
                "name": "Normalized Difference Water Index",
                "description": "Detects water content in vegetation",
                "range": [-1, 1],
                "typical_range": [-0.5, 0.5],
            },
            {
                "id": "ndmi",
                "name": "Normalized Difference Moisture Index",
                "description": "Measures vegetation water content",
                "range": [-1, 1],
                "typical_range": [-0.5, 0.5],
            },
            {
                "id": "evi",
                "name": "Enhanced Vegetation Index",
                "description": "Enhanced vegetation monitoring, reduces atmospheric effects",
                "range": [-1, 1],
                "typical_range": [-0.2, 0.8],
            },
            {
                "id": "savi",
                "name": "Soil Adjusted Vegetation Index",
                "description": "Minimizes soil brightness influences",
                "range": [-1, 1],
                "typical_range": [-0.2, 0.8],
            },
            {
                "id": "ndre",
                "name": "Normalized Difference Red Edge",
                "description": "Sensitive to chlorophyll content, good for crop monitoring",
                "range": [-1, 1],
                "typical_range": [-0.2, 0.8],
            },
            {
                "id": "gndvi",
                "name": "Green Normalized Difference Vegetation Index",
                "description": "More sensitive to chlorophyll concentration",
                "range": [-1, 1],
                "typical_range": [-0.2, 0.8],
            },
        ]
    }


@router.post("/tiles/aois/{aoi_id}/export")
async def export_aoi_cog(
    aoi_id: UUID,
    background_tasks: BackgroundTasks,
    index: str = Query("ndvi", description="Vegetation index to export"),
    year: Optional[int] = Query(None, description="ISO year"),
    week: Optional[int] = Query(None, description="ISO week"),
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
):
    """
    Export a Cloud Optimized GeoTIFF (COG) for an AOI.

    Generates a COG file on-demand and returns a presigned download URL.
    The file is cached in S3 for 24 hours.

    Use this endpoint when you need to download the raster for local analysis
    in QGIS, ArcGIS, or other GIS software.
    """
    container = ApiContainer()
    use_case = container.tile_export_use_case(db)
    try:
        result = await use_case.execute(
            TileExportCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                aoi_id=aoi_id,
                index=index,
                year=year,
                week=week,
            )
        )
    except ValueError as exc:
        if str(exc) == "AOI_NOT_FOUND":
            raise HTTPException(status_code=404, detail="AOI not found")
        if str(exc) == "INVALID_INDEX":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid index '{index}'. Valid options: {', '.join(EXPRESSIONS.keys())}",
            )
        raise

    if result.status == "processing" and result.export_key:
        if not year or not week:
            year, week = datetime.utcnow().isocalendar().year, datetime.utcnow().isocalendar().week
        background_tasks.add_task(
            generate_cog_export,
            tenant_id=str(membership.tenant_id),
            aoi_id=str(aoi_id),
            index=index.lower(),
            year=year,
            week=week,
            export_key=result.export_key,
        )

    return result.model_dump()


async def generate_cog_export(
    tenant_id: str,
    aoi_id: str,
    index: str,
    year: int,
    week: int,
    export_key: str,
):
    """
    Background task to generate COG export via TiTiler.
    """
    from app.database import SessionLocal

    logger.info(
        "cog_export_start",
        tenant_id=tenant_id,
        aoi_id=aoi_id,
        index=index,
        year=year,
        week=week,
    )

    try:
        db = SessionLocal()
        container = ApiContainer()
        use_case = container.tile_export_generate_use_case(db)
        await use_case.execute(
            tenant_id=TenantId(value=UUID(tenant_id)),
            aoi_id=UUID(aoi_id),
            index=index,
            year=year,
            week=week,
            export_key=export_key,
        )

    except Exception as e:
        logger.error("cog_export_failed", error=str(e), exc_info=True)
    finally:
        db.close()


@router.get("/tiles/aois/{aoi_id}/export/status")
async def get_export_status(
    aoi_id: UUID,
    index: str = Query("ndvi"),
    year: Optional[int] = Query(None),
    week: Optional[int] = Query(None),
    membership: CurrentMembership = Depends(get_current_membership),
):
    """
    Check the status of a COG export request.
    """
    container = ApiContainer()
    use_case = container.tile_export_status_use_case()
    result = await use_case.execute(
        TileExportStatusCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_id=aoi_id,
            index=index,
            year=year,
            week=week,
        )
    )
    return result.model_dump()