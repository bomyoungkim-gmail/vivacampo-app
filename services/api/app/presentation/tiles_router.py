"""
Tiles Router - Dynamic Tiling API

Provides authenticated tile endpoints for AOIs using TiTiler + MosaicJSON.
Part of ADR-0007: Dynamic Tiling with MosaicJSON.

Endpoints:
- GET /tiles/aois/{aoi_id}/{z}/{x}/{y}.png - Tile for AOI
- GET /tiles/aois/{aoi_id}/tilejson.json - TileJSON metadata
- POST /tiles/aois/{aoi_id}/export - Export COG on-demand
"""

from datetime import date, datetime
from typing import Optional
from urllib.parse import quote
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
import structlog

from app.config import settings
from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership

logger = structlog.get_logger()
router = APIRouter()

# TiTiler internal URL
TILER_URL = getattr(settings, 'tiler_url', 'http://tiler:8080')

# Vegetation index expressions (must match TiTiler expressions.py)
# NOTE: Current MosaicJSON uses "visual" composite (RGB) which only supports
# true_color display. For vegetation indices, implement TiTiler-STAC endpoint
# that can resolve individual band COGs.
EXPRESSIONS = {
    "ndvi": "(B08-B04)/(B08+B04)",
    "ndwi": "(B03-B08)/(B03+B08)",
    "ndmi": "(B08-B11)/(B08+B11)",
    "evi": "2.5*(B08-B04)/(B08+6*B04-7.5*B02+1)",
    "savi": "1.5*(B08-B04)/(B08+B04+0.5)",
    "ndre": "(B08-B05)/(B08+B05)",
    "gndvi": "(B08-B03)/(B08+B03)",
    "true_color": None,  # No expression, use RGB directly
}

COLORMAPS = {
    "ndvi": "rdylgn",
    "ndwi": "blues",
    "ndmi": "blues",
    "evi": "rdylgn",
    "savi": "rdylgn",
    "ndre": "rdylgn",
    "gndvi": "rdylgn",
    "true_color": None,  # No colormap for RGB
}

RESCALES = {
    "ndvi": "-0.2,0.8",
    "ndwi": "-0.5,0.5",
    "ndmi": "-0.5,0.5",
    "evi": "-0.2,0.8",
    "savi": "-0.2,0.8",
    "ndre": "-0.2,0.8",
    "gndvi": "-0.2,0.8",
    "true_color": None,  # No rescale for RGB
}


def get_current_iso_week() -> tuple[int, int]:
    """Get current ISO year and week number."""
    today = date.today()
    iso_cal = today.isocalendar()
    return iso_cal.year, iso_cal.week


def get_mosaic_url(year: int, week: int, collection: str = "sentinel-2-l2a") -> str:
    """Build S3 URL for MosaicJSON file."""
    return f"s3://{settings.s3_bucket}/mosaics/{collection}/{year}/w{week:02d}.json"


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
    # Verify AOI belongs to tenant
    result = db.execute(
        text("SELECT id FROM aois WHERE id = :aoi_id AND tenant_id = :tenant_id"),
        {"aoi_id": str(aoi_id), "tenant_id": str(membership.tenant_id)},
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="AOI not found")

    # Validate index
    if index.lower() not in EXPRESSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid index '{index}'. Valid options: {', '.join(EXPRESSIONS.keys())}",
        )

    index = index.lower()

    # Default to current week
    if not year or not week:
        year, week = get_current_iso_week()

    # Build mosaic URL
    mosaic_url = get_mosaic_url(year, week)

    # Get index configuration
    expression = EXPRESSIONS.get(index)
    colormap = COLORMAPS.get(index)
    rescale = RESCALES.get(index)

    # Route to appropriate TiTiler endpoint based on index type
    if expression:
        # Vegetation indices need multi-band access via STAC-mosaic endpoint
        # This endpoint reads STAC item URLs from MosaicJSON and uses STACReader
        # to access individual band COGs for expression computation
        tiler_url = (
            f"{TILER_URL}/stac-mosaic/tiles/{z}/{x}/{y}.png"
            f"?url={quote(mosaic_url, safe='')}"
            f"&expression={quote(expression, safe='')}"
        )
        if colormap:
            tiler_url += f"&colormap_name={colormap}"
        if rescale:
            tiler_url += f"&rescale={rescale}"
    else:
        # true_color uses visual composite COG via standard mosaic endpoint
        # For backwards compatibility with visual-based MosaicJSON
        tiler_url = (
            f"{TILER_URL}/mosaic/tiles/WebMercatorQuad/{z}/{x}/{y}.png"
            f"?url={quote(mosaic_url, safe='')}"
        )

    logger.debug(
        "tile_request",
        aoi_id=str(aoi_id),
        z=z, x=x, y=y,
        index=index,
        year=year,
        week=week,
    )

    # Redirect to TiTiler (CDN will cache the response)
    response = RedirectResponse(url=tiler_url, status_code=307)
    response.headers["Cache-Control"] = "public, max-age=604800, immutable"  # 7 days
    response.headers["X-VivaCampo-Index"] = index
    response.headers["X-VivaCampo-Week"] = f"{year}-W{week:02d}"
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
    # Verify AOI belongs to tenant
    result = db.execute(
        text("""
            SELECT id, name,
                   ST_XMin(geom) as minx, ST_YMin(geom) as miny,
                   ST_XMax(geom) as maxx, ST_YMax(geom) as maxy,
                   ST_X(ST_Centroid(geom)) as cx, ST_Y(ST_Centroid(geom)) as cy
            FROM aois
            WHERE id = :aoi_id AND tenant_id = :tenant_id
        """),
        {"aoi_id": str(aoi_id), "tenant_id": str(membership.tenant_id)},
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="AOI not found")

    # Default to current week
    if not year or not week:
        year, week = get_current_iso_week()

    index = index.lower()
    if index not in EXPRESSIONS:
        index = "ndvi"

    # Build tile URL template
    # Note: Using {z}/{x}/{y} placeholders for GIS tools
    # Use CDN URL if enabled, otherwise use API base URL
    if getattr(settings, 'cdn_enabled', False) and getattr(settings, 'cdn_tiles_url', None):
        base_url = settings.cdn_tiles_url
    else:
        base_url = getattr(settings, 'api_base_url', 'http://localhost:8000')

    tile_url = (
        f"{base_url}/v1/tiles/aois/{aoi_id}/{{z}}/{{x}}/{{y}}.png"
        f"?index={index}&year={year}&week={week}"
    )

    return {
        "tilejson": "3.0.0",
        "name": f"{result.name} - {index.upper()}",
        "description": f"Vegetation index {index.upper()} for {result.name}, {year} week {week}",
        "version": "1.0.0",
        "attribution": "VivaCampo - Sentinel-2 via Planetary Computer",
        "tiles": [tile_url],
        "minzoom": 8,
        "maxzoom": 16,
        "bounds": [result.minx, result.miny, result.maxx, result.maxy],
        "center": [result.cx, result.cy, 12],
    }


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
    # Verify AOI belongs to tenant
    result = db.execute(
        text("SELECT id, name FROM aois WHERE id = :aoi_id AND tenant_id = :tenant_id"),
        {"aoi_id": str(aoi_id), "tenant_id": str(membership.tenant_id)},
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="AOI not found")

    # Default to current week
    if not year or not week:
        year, week = get_current_iso_week()

    index = index.lower()
    if index not in EXPRESSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid index '{index}'. Valid options: {', '.join(EXPRESSIONS.keys())}",
        )

    # Generate export key
    export_key = f"exports/{membership.tenant_id}/{aoi_id}/{index}-{year}-w{week:02d}.tif"

    # Check if already exists in S3
    from app.infrastructure.s3_client import S3Client
    s3 = S3Client()

    if s3.object_exists(export_key):
        # Return existing file
        presigned_url = s3.generate_presigned_url(export_key, expires_in=86400)
        return {
            "status": "ready",
            "download_url": presigned_url,
            "filename": f"{result.name}-{index}-{year}-w{week:02d}.tif",
            "expires_in": 86400,
            "cached": True,
        }

    # Queue background task to generate COG
    background_tasks.add_task(
        generate_cog_export,
        tenant_id=str(membership.tenant_id),
        aoi_id=str(aoi_id),
        index=index,
        year=year,
        week=week,
        export_key=export_key,
    )

    # Return processing status
    return {
        "status": "processing",
        "message": "COG export is being generated. Check back in 1-2 minutes.",
        "export_key": export_key,
        "filename": f"{result.name}-{index}-{year}-w{week:02d}.tif",
    }


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
    from app.infrastructure.s3_client import S3Client
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

        # Get AOI geometry
        result = db.execute(
            text("SELECT ST_AsGeoJSON(geom) as geojson FROM aois WHERE id = :aoi_id"),
            {"aoi_id": aoi_id},
        ).fetchone()

        if not result:
            logger.error("cog_export_aoi_not_found", aoi_id=aoi_id)
            return

        import json
        geometry = json.loads(result.geojson)

        # Build mosaic URL
        mosaic_url = get_mosaic_url(year, week)
        expression = EXPRESSIONS[index]

        # Call TiTiler to generate COG
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Use TiTiler's crop endpoint to generate clipped COG
            response = await client.post(
                f"{TILER_URL}/mosaic/crop",
                params={
                    "url": mosaic_url,
                    "expression": expression,
                    "format": "tif",
                },
                json=geometry,
            )

            if response.status_code != 200:
                logger.error(
                    "cog_export_tiler_error",
                    status_code=response.status_code,
                    response=response.text[:500],
                )
                return

            # Upload to S3
            s3 = S3Client()
            s3.upload_bytes(export_key, response.content, content_type="image/tiff")

            logger.info(
                "cog_export_complete",
                aoi_id=aoi_id,
                export_key=export_key,
                size_bytes=len(response.content),
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
    if not year or not week:
        year, week = get_current_iso_week()

    index = index.lower()
    export_key = f"exports/{membership.tenant_id}/{aoi_id}/{index}-{year}-w{week:02d}.tif"

    from app.infrastructure.s3_client import S3Client
    s3 = S3Client()

    if s3.object_exists(export_key):
        presigned_url = s3.generate_presigned_url(export_key, expires_in=86400)
        return {
            "status": "ready",
            "download_url": presigned_url,
            "expires_in": 86400,
        }
    else:
        return {
            "status": "processing",
            "message": "Export is still being generated or has not been requested.",
        }
