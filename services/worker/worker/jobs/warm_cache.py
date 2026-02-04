"""
WARM_CACHE Job

Pre-warms CDN cache for AOI tiles after backfill completes.
This ensures users experience fast tile loading on first access.

The job:
1. Calculates visible tiles for the AOI at common zoom levels
2. Requests each tile to populate CDN cache
3. Reports cache warming statistics

Part of ADR-0007: Dynamic Tiling with MosaicJSON
"""

import asyncio
import math
from typing import List, Tuple
from uuid import UUID
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
from shapely import wkt
from shapely.geometry import shape

from worker.config import settings

logger = structlog.get_logger()

# API URL for tile requests (goes through CDN)
API_URL = getattr(settings, 'api_url', 'http://api:8000')

# Zoom levels to pre-warm (typical agricultural viewing)
WARM_ZOOM_LEVELS = [10, 11, 12, 13, 14]

# Maximum tiles to warm per AOI (prevent excessive requests)
MAX_TILES_PER_AOI = 200

# Concurrent requests limit
CONCURRENT_REQUESTS = 10

# Request timeout
REQUEST_TIMEOUT = 30.0


def lng_lat_to_tile(lng: float, lat: float, zoom: int) -> Tuple[int, int]:
    """Convert longitude/latitude to tile coordinates."""
    n = 2 ** zoom
    x = int((lng + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (x, y)


def get_tiles_for_bounds(
    minx: float, miny: float, maxx: float, maxy: float, zoom: int
) -> List[Tuple[int, int, int]]:
    """Get all tiles that cover the given bounds at a zoom level."""
    min_tile = lng_lat_to_tile(minx, maxy, zoom)  # Note: y is inverted
    max_tile = lng_lat_to_tile(maxx, miny, zoom)

    tiles = []
    for x in range(min_tile[0], max_tile[0] + 1):
        for y in range(min_tile[1], max_tile[1] + 1):
            tiles.append((zoom, x, y))

    return tiles


async def fetch_tile(
    client: httpx.AsyncClient,
    aoi_id: str,
    z: int,
    x: int,
    y: int,
    index: str = "ndvi",
) -> bool:
    """Fetch a single tile to warm the cache."""
    try:
        url = f"{API_URL}/v1/tiles/aois/{aoi_id}/{z}/{x}/{y}.png"
        params = {"index": index}

        response = await client.get(url, params=params, follow_redirects=True)
        return response.status_code in [200, 307]

    except Exception as e:
        logger.debug("tile_fetch_error", z=z, x=x, y=y, error=str(e))
        return False


async def warm_cache_handler(job: dict, db: Session) -> dict:
    """
    Async job handler for WARM_CACHE.

    Job payload:
        aoi_id: UUID - Area of Interest ID
        tenant_id: UUID - Tenant ID
        indices: list[str] - Indices to warm (default: ["ndvi"])
        zoom_levels: list[int] - Zoom levels to warm (default: [10-14])

    Returns:
        dict with status and statistics
    """
    payload = job.get("payload", {})
    aoi_id = payload.get("aoi_id")
    tenant_id = payload.get("tenant_id")
    indices = payload.get("indices", ["ndvi"])
    zoom_levels = payload.get("zoom_levels", WARM_ZOOM_LEVELS)

    if not aoi_id or not tenant_id:
        raise ValueError("aoi_id and tenant_id are required")

    logger.info(
        "warm_cache_start",
        job_id=job.get("id"),
        aoi_id=aoi_id,
        indices=indices,
        zoom_levels=zoom_levels,
    )

    # 1. Get AOI bounds from database
    result = db.execute(
        text("""
            SELECT
                ST_XMin(geom) as minx, ST_YMin(geom) as miny,
                ST_XMax(geom) as maxx, ST_YMax(geom) as maxy
            FROM aois
            WHERE id = :aoi_id AND tenant_id = :tenant_id
        """),
        {"aoi_id": aoi_id, "tenant_id": tenant_id},
    ).fetchone()

    if not result:
        logger.warning("warm_cache_aoi_not_found", aoi_id=aoi_id)
        return {"status": "NOT_FOUND", "aoi_id": aoi_id}

    bounds = (result.minx, result.miny, result.maxx, result.maxy)

    # 2. Calculate tiles to warm
    all_tiles = []
    for zoom in zoom_levels:
        tiles = get_tiles_for_bounds(*bounds, zoom)
        all_tiles.extend(tiles)

    # Limit total tiles
    if len(all_tiles) > MAX_TILES_PER_AOI:
        logger.warning(
            "warm_cache_tiles_limited",
            total_tiles=len(all_tiles),
            limit=MAX_TILES_PER_AOI,
        )
        all_tiles = all_tiles[:MAX_TILES_PER_AOI]

    logger.info("warm_cache_tiles_calculated", tile_count=len(all_tiles))

    # 3. Warm cache for each index
    stats = {
        "total_tiles": len(all_tiles) * len(indices),
        "success": 0,
        "failed": 0,
    }

    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    async def fetch_with_semaphore(client, aoi_id, z, x, y, index):
        async with semaphore:
            return await fetch_tile(client, aoi_id, z, x, y, index)

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for index in indices:
            tasks = [
                fetch_with_semaphore(client, aoi_id, z, x, y, index)
                for z, x, y in all_tiles
            ]

            results = await asyncio.gather(*tasks)

            for success in results:
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1

    logger.info(
        "warm_cache_complete",
        aoi_id=aoi_id,
        stats=stats,
    )

    return {
        "status": "OK",
        "aoi_id": aoi_id,
        "stats": stats,
    }


# Sync wrapper for job system compatibility
def warm_cache_sync_handler(job_id: str, payload: dict, db: Session) -> dict:
    """Sync wrapper for warm_cache_handler."""
    job = {"id": job_id, "payload": payload}
    return asyncio.run(warm_cache_handler(job, db))
