"""
CREATE_MOSAIC Job

Creates MosaicJSON files for a specific week/collection.
MosaicJSONs are virtual aggregations of Sentinel scenes that allow
TiTiler to serve tiles dynamically without storing COGs per-AOI.

This job runs once per week (globally, not per-AOI) and creates
a MosaicJSON that references all available Sentinel-2 scenes for Brazil.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import text
import planetary_computer
from pystac_client import Client
from shapely.geometry import box

from worker.config import settings
from worker.shared.aws_clients import S3Client

logger = structlog.get_logger()

# Brazil bounding box (approximate)
BRAZIL_BBOX = [-74.0, -34.0, -34.0, 6.0]  # [minx, miny, maxx, maxy]

# Planetary Computer STAC URL
PC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

# Sentinel-2 bands to include in mosaic
SENTINEL2_BANDS = [
    "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12", "SCL"
]

# Sentinel-1 bands
SENTINEL1_BANDS = ["VV", "VH"]


def iso_week_to_dates(year: int, week: int) -> tuple[str, str]:
    """Convert ISO year/week to start/end date strings."""
    # First day of ISO week
    jan4 = datetime(year, 1, 4)
    start_of_year = jan4 - timedelta(days=jan4.isoweekday() - 1)
    start_date = start_of_year + timedelta(weeks=week - 1)
    end_date = start_date + timedelta(days=6)
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def create_mosaic_json(
    scenes: List[Dict[str, Any]],
    collection: str,
    year: int,
    week: int,
    bands: List[str],
) -> Dict[str, Any]:
    """
    Create MosaicJSON structure from STAC items.

    The MosaicJSON format for cogeo-mosaic requires tiles to be a dict
    mapping quadkey/tile_id to a list of COG URLs.

    For multi-band imagery like Sentinel-2, we reference the STAC item
    href and let TiTiler/rio-tiler handle band selection via expressions.

    Args:
        scenes: List of STAC items
        collection: Collection name (e.g., "sentinel-2-l2a")
        year: ISO year
        week: ISO week number
        bands: List of bands to include

    Returns:
        MosaicJSON dictionary compatible with cogeo-mosaic
    """
    import mercantile

    # Calculate min/max zoom based on collection
    minzoom = 8
    maxzoom = 14

    # Build tiles dict mapping quadkey to list of scene URLs
    # cogeo-mosaic expects: {"quadkey": ["url1", "url2"], ...}
    tiles_dict = {}

    for item in scenes:
        # Store STAC item self-link URLs in the MosaicJSON
        # This allows TiTiler-STAC endpoint to resolve individual band assets
        # for computing vegetation indices (NDVI, EVI, etc.) that need multiple bands.
        #
        # The /stac-mosaic/tiles endpoint will:
        # 1. Look up the STAC item URL from MosaicJSON
        # 2. Use STACReader to access individual band COGs
        # 3. Compute the band math expression (e.g., (B08-B04)/(B08+B04))

        # Get STAC item self-link
        self_link = None
        if hasattr(item, 'links'):
            for link in item.links:
                if link.rel == 'self':
                    self_link = link.href
                    break

        if not self_link:
            # Fallback: construct URL from item ID (Planetary Computer format)
            self_link = f"https://planetarycomputer.microsoft.com/api/stac/v1/collections/{collection}/items/{item.id}"

        # Store UNSIGNED URL - signing will happen at request time
        # Planetary Computer signed URLs expire, so we don't sign at mosaic creation
        signed_href = self_link

        # Get quadkeys covered by this scene
        if item.bbox:
            # Calculate quadkeys at maxzoom that intersect this scene
            tiles = list(mercantile.tiles(*item.bbox, zooms=maxzoom))
            for tile in tiles:
                qk = mercantile.quadkey(tile)
                if qk not in tiles_dict:
                    tiles_dict[qk] = []
                # Only add if not already present (avoid duplicates)
                if signed_href not in tiles_dict[qk]:
                    tiles_dict[qk].append(signed_href)

    mosaic = {
        "mosaicjson": "0.0.3",
        "name": f"{collection}-{year}-w{week:02d}",
        "description": f"Weekly mosaic for {collection}, {year} week {week}",
        "version": "1.0.0",
        "minzoom": minzoom,
        "maxzoom": maxzoom,
        "quadkey_zoom": maxzoom,
        "center": [-55.0, -15.0, 10],  # Center of Brazil
        "bounds": BRAZIL_BBOX,
        "tiles": tiles_dict,
    }

    return mosaic


def create_mosaic_handler(job_id: str, payload: dict, db: Session) -> dict:
    """
    Job handler for CREATE_MOSAIC.

    Payload:
        year: int - ISO year
        week: int - ISO week number
        collection: str - STAC collection (default: "sentinel-2-l2a")
        max_cloud_cover: float - Maximum cloud cover % (default: 30)

    Returns:
        dict with status, mosaic_url, and scene count
    """
    year = payload.get("year")
    week = payload.get("week")
    collection = payload.get("collection", "sentinel-2-l2a")
    max_cloud_cover = payload.get("max_cloud_cover", 30)

    if not year or not week:
        raise ValueError("year and week are required in payload")

    logger.info(
        "create_mosaic_start",
        job_id=job_id,
        year=year,
        week=week,
        collection=collection,
    )

    # Calculate date range for the week
    start_date, end_date = iso_week_to_dates(year, week)

    # Determine bands based on collection
    if collection == "sentinel-2-l2a":
        bands = SENTINEL2_BANDS
    elif collection == "sentinel-1-rtc":
        bands = SENTINEL1_BANDS
    else:
        bands = SENTINEL2_BANDS

    try:
        # Connect to Planetary Computer STAC
        catalog = Client.open(
            PC_STAC_URL,
            modifier=planetary_computer.sign_inplace,
        )

        # Build query
        query = {}
        if collection == "sentinel-2-l2a":
            query["eo:cloud_cover"] = {"lt": max_cloud_cover}

        # Search for scenes
        logger.info(
            "stac_search_start",
            collection=collection,
            start_date=start_date,
            end_date=end_date,
            bbox=BRAZIL_BBOX,
        )

        search = catalog.search(
            collections=[collection],
            bbox=BRAZIL_BBOX,
            datetime=f"{start_date}/{end_date}",
            query=query if query else None,
            max_items=2000,  # Increased to capture more of Brazil
        )

        items = list(search.items())
        logger.info("stac_search_complete", scene_count=len(items))

        if not items:
            logger.warning(
                "no_scenes_found",
                year=year,
                week=week,
                collection=collection,
            )
            # Save empty mosaic marker
            s3_key = f"mosaics/{collection}/{year}/w{week:02d}.json"
            empty_mosaic = {
                "mosaicjson": "0.0.3",
                "name": f"{collection}-{year}-w{week:02d}",
                "tiles": {},
                "metadata": {
                    "status": "NO_DATA",
                    "created_at": datetime.utcnow().isoformat(),
                },
            }
            S3Client().upload_json(s3_key, empty_mosaic)

            return {
                "status": "NO_DATA",
                "mosaic_url": f"s3://{settings.s3_bucket}/{s3_key}",
                "scene_count": 0,
            }

        # Create MosaicJSON
        mosaic = create_mosaic_json(items, collection, year, week, bands)

        # Upload to S3
        s3_key = f"mosaics/{collection}/{year}/w{week:02d}.json"
        S3Client().upload_json(s3_key, mosaic)

        mosaic_url = f"s3://{settings.s3_bucket}/{s3_key}"

        logger.info(
            "create_mosaic_complete",
            job_id=job_id,
            mosaic_url=mosaic_url,
            scene_count=len(items),
            tile_count=len(mosaic["tiles"]),
        )

        # Record in database (optional, for tracking)
        _save_mosaic_record(db, collection, year, week, mosaic_url, len(items))

        return {
            "status": "OK",
            "mosaic_url": mosaic_url,
            "scene_count": len(items),
            "tile_count": len(mosaic["tiles"]),
        }

    except Exception as e:
        logger.error(
            "create_mosaic_failed",
            job_id=job_id,
            error=str(e),
            exc_info=True,
        )
        raise


def _save_mosaic_record(
    db: Session,
    collection: str,
    year: int,
    week: int,
    mosaic_url: str,
    scene_count: int,
):
    """Save mosaic metadata to database for tracking."""
    try:
        sql = text("""
            INSERT INTO mosaic_registry (collection, year, week, s3_url, scene_count, created_at)
            VALUES (:collection, :year, :week, :s3_url, :scene_count, NOW())
            ON CONFLICT (collection, year, week)
            DO UPDATE SET s3_url = :s3_url, scene_count = :scene_count, updated_at = NOW()
        """)
        db.execute(
            sql,
            {
                "collection": collection,
                "year": year,
                "week": week,
                "s3_url": mosaic_url,
                "scene_count": scene_count,
            },
        )
        db.commit()
    except Exception as e:
        # Table may not exist yet, log and continue
        logger.warning("mosaic_registry_save_failed", error=str(e))
        db.rollback()


def ensure_mosaic_exists(year: int, week: int, collection: str = "sentinel-2-l2a") -> str:
    """
    Check if mosaic exists in S3, return URL if it does.
    Used by other jobs to ensure mosaic is available before calculating stats.
    """
    s3_key = f"mosaics/{collection}/{year}/w{week:02d}.json"
    s3_client = S3Client()

    if s3_client.object_exists(s3_key):
        return f"s3://{settings.s3_bucket}/{s3_key}"

    return None
