"""
CALCULATE_STATS Job

Calculates vegetation index statistics for an AOI using TiTiler's
statistics endpoint. This replaces the old approach of downloading
COGs and calculating stats locally.

The job:
1. Verifies MosaicJSON exists for the week
2. Calls TiTiler /mosaic/statistics with AOI geometry
3. Saves stats to observations_weekly table
4. Does NOT create or upload any COGs
"""

import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import text
from shapely import wkt
from shapely.geometry import mapping

from worker.config import settings
from worker.jobs.create_mosaic import ensure_mosaic_exists

logger = structlog.get_logger()

# TiTiler URL (internal service URL)
TILER_URL = settings.tiler_url

# Vegetation indices to calculate
INDICES = {
    "ndvi": "(B08-B04)/(B08+B04)",
    "ndwi": "(B03-B08)/(B03+B08)",
    "ndmi": "(B08-B11)/(B08+B11)",
    "evi": "2.5*(B08-B04)/(B08+6*B04-7.5*B02+1)",
    "savi": "1.5*(B08-B04)/(B08+B04+0.5)",
    "ndre": "(B08-B05)/(B08+B05)",
    "gndvi": "(B08-B03)/(B08+B03)",
}

# HTTP client timeout
HTTP_TIMEOUT = 120.0  # 2 minutes for stats calculation


async def fetch_stats_from_tiler(
    mosaic_url: str,
    expression: str,
    geometry: Dict[str, Any],
) -> Optional[Dict[str, float]]:
    """
    Fetch statistics from TiTiler mosaic statistics endpoint.

    Args:
        mosaic_url: S3 URL to MosaicJSON file
        expression: Band math expression (e.g., "(B08-B04)/(B08+B04)")
        geometry: GeoJSON geometry to calculate stats for

    Returns:
        Dictionary with statistics or None if failed
    """
    url = f"{TILER_URL}/mosaic/statistics"
    params = {
        "url": mosaic_url,
        "expression": expression,
    }

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(url, params=params, json=geometry)

            if response.status_code == 200:
                data = response.json()
                # TiTiler returns stats in format: {"statistics": {"b1": {...}}}
                if "statistics" in data and "b1" in data["statistics"]:
                    stats = data["statistics"]["b1"]
                    return {
                        "mean": stats.get("mean"),
                        "min": stats.get("min"),
                        "max": stats.get("max"),
                        "std": stats.get("std"),
                        "p10": stats.get("percentile_10"),
                        "p50": stats.get("percentile_50"),
                        "p90": stats.get("percentile_90"),
                        "valid_pixels": stats.get("count"),
                    }
            else:
                logger.warning(
                    "tiler_stats_failed",
                    status_code=response.status_code,
                    response=response.text[:500],
                )
                return None

    except httpx.TimeoutException:
        logger.error("tiler_stats_timeout", url=url)
        return None
    except Exception as e:
        logger.error("tiler_stats_error", error=str(e))
        return None


async def calculate_stats_handler(job: dict, db: Session) -> dict:
    """
    Async job handler for CALCULATE_STATS.

    Job payload:
        aoi_id: UUID - Area of Interest ID
        tenant_id: UUID - Tenant ID
        year: int - ISO year
        week: int - ISO week number
        indices: list[str] - Optional list of indices to calculate (default: all)

    Returns:
        dict with status and calculated indices
    """
    payload = job.get("payload", {})
    aoi_id = payload.get("aoi_id")
    tenant_id = payload.get("tenant_id")
    year = payload.get("year")
    week = payload.get("week")
    indices_to_calc = payload.get("indices", list(INDICES.keys()))

    if not all([aoi_id, tenant_id, year, week]):
        raise ValueError("aoi_id, tenant_id, year, and week are required")

    logger.info(
        "calculate_stats_start",
        job_id=job.get("id"),
        aoi_id=aoi_id,
        year=year,
        week=week,
    )

    # 1. Get AOI geometry from database
    aoi_result = db.execute(
        text("SELECT geom FROM aois WHERE id = :aoi_id AND tenant_id = :tenant_id"),
        {"aoi_id": aoi_id, "tenant_id": tenant_id},
    ).fetchone()

    if not aoi_result:
        raise ValueError(f"AOI {aoi_id} not found for tenant {tenant_id}")

    # Convert geometry to GeoJSON
    geom_wkt = aoi_result[0]
    if isinstance(geom_wkt, str):
        geom = wkt.loads(geom_wkt)
    else:
        # Assume it's already a shapely geometry or WKB
        from shapely import wkb
        geom = wkb.loads(bytes(geom_wkt.data)) if hasattr(geom_wkt, 'data') else geom_wkt

    geometry_geojson = mapping(geom)

    # 2. Verify mosaic exists
    mosaic_url = ensure_mosaic_exists(year, week, "sentinel-2-l2a")
    if not mosaic_url:
        logger.warning(
            "mosaic_not_found",
            year=year,
            week=week,
        )
        # Mark as NO_DATA in observations
        _save_observations(db, tenant_id, aoi_id, year, week, {}, status="NO_DATA")
        return {"status": "NO_DATA", "reason": "mosaic_not_found"}

    # 3. Calculate stats for each index
    all_stats = {}
    for index_name in indices_to_calc:
        if index_name not in INDICES:
            logger.warning("unknown_index", index=index_name)
            continue

        expression = INDICES[index_name]
        stats = await fetch_stats_from_tiler(mosaic_url, expression, geometry_geojson)

        if stats:
            all_stats[index_name] = stats
            logger.debug(
                "index_stats_calculated",
                index=index_name,
                mean=stats.get("mean"),
            )
        else:
            logger.warning("index_stats_failed", index=index_name)

    # 4. Save to database
    if all_stats:
        _save_observations(db, tenant_id, aoi_id, year, week, all_stats, status="OK")
        logger.info(
            "calculate_stats_complete",
            aoi_id=aoi_id,
            year=year,
            week=week,
            indices=list(all_stats.keys()),
        )
        return {"status": "OK", "indices": list(all_stats.keys())}
    else:
        _save_observations(db, tenant_id, aoi_id, year, week, {}, status="NO_DATA")
        return {"status": "NO_DATA", "reason": "no_stats_calculated"}


def _save_observations(
    db: Session,
    tenant_id: str,
    aoi_id: str,
    year: int,
    week: int,
    stats: Dict[str, Dict[str, float]],
    status: str = "OK",
):
    """Save calculated stats to observations_weekly table."""

    # Build dynamic columns based on available stats
    columns = ["tenant_id", "aoi_id", "year", "week", "pipeline_version", "status"]
    values = {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "year": year,
        "week": week,
        "pipeline_version": "v2-dynamic",
        "status": status,
    }

    # Add stats for each index
    stat_mappings = [
        ("ndvi", ["mean", "p10", "p50", "p90", "std"]),
        ("ndwi", ["mean", "std"]),
        ("ndmi", ["mean", "std"]),
        ("evi", ["mean", "std"]),
        ("savi", ["mean", "std"]),
        ("ndre", ["mean", "std"]),
        ("gndvi", ["mean", "std"]),
    ]

    for index_name, stat_fields in stat_mappings:
        if index_name in stats:
            index_stats = stats[index_name]
            for field in stat_fields:
                col_name = f"{index_name}_{field}"
                columns.append(col_name)
                values[col_name] = index_stats.get(field)

    # Build SQL dynamically
    columns_str = ", ".join(columns)
    placeholders = ", ".join(f":{col}" for col in columns)

    # Build ON CONFLICT update clause
    update_cols = [c for c in columns if c not in ["tenant_id", "aoi_id", "year", "week", "pipeline_version"]]
    update_str = ", ".join(f"{c} = :{c}" for c in update_cols)

    sql = text(f"""
        INSERT INTO observations_weekly ({columns_str})
        VALUES ({placeholders})
        ON CONFLICT (tenant_id, aoi_id, year, week, pipeline_version)
        DO UPDATE SET {update_str}, updated_at = NOW()
    """)

    try:
        db.execute(sql, values)
        db.commit()
        logger.debug("observations_saved", aoi_id=aoi_id, year=year, week=week)
    except Exception as e:
        logger.error("observations_save_failed", error=str(e))
        db.rollback()
        raise


# Sync wrapper for compatibility with existing job system
def calculate_stats_sync_handler(job_id: str, payload: dict, db: Session) -> dict:
    """Sync wrapper for calculate_stats_handler."""
    import asyncio

    job = {
        "id": job_id,
        "payload": payload,
    }
    return asyncio.run(calculate_stats_handler(job, db))


def calculate_stats_handler(job_id: str, payload: dict, db: Session) -> dict:
    """
    Main entry point for CALCULATE_STATS job.

    This is the sync handler that matches the signature expected by the job system
    and by process_week.py when in dynamic tiling mode.

    Args:
        job_id: Job UUID
        payload: Job payload with aoi_id, tenant_id, year, week
        db: Database session

    Returns:
        dict with status and results
    """
    import asyncio

    job = {
        "id": job_id,
        "payload": payload,
    }

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(calculate_stats_async_handler(job, db))
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error("calculate_stats_failed", job_id=job_id, error=str(e), exc_info=True)
        raise


# Rename the async handler to avoid confusion
async def calculate_stats_async_handler(job: dict, db: Session) -> dict:
    """Async implementation of CALCULATE_STATS."""
    payload = job.get("payload", {})
    aoi_id = payload.get("aoi_id")
    tenant_id = payload.get("tenant_id")
    year = payload.get("year")
    week = payload.get("week")
    indices_to_calc = payload.get("indices", list(INDICES.keys()))

    if not all([aoi_id, tenant_id, year, week]):
        raise ValueError("aoi_id, tenant_id, year, and week are required")

    logger.info(
        "calculate_stats_start",
        job_id=job.get("id"),
        aoi_id=aoi_id,
        year=year,
        week=week,
    )

    # 1. Get AOI geometry from database
    aoi_result = db.execute(
        text("SELECT ST_AsText(geom) as geom_wkt FROM aois WHERE id = :aoi_id AND tenant_id = :tenant_id"),
        {"aoi_id": aoi_id, "tenant_id": tenant_id},
    ).fetchone()

    if not aoi_result:
        raise ValueError(f"AOI {aoi_id} not found for tenant {tenant_id}")

    # Convert geometry to GeoJSON
    geom = wkt.loads(aoi_result.geom_wkt)
    geometry_geojson = mapping(geom)

    # 2. Verify mosaic exists
    mosaic_url = ensure_mosaic_exists(year, week, "sentinel-2-l2a")
    if not mosaic_url:
        logger.warning(
            "mosaic_not_found",
            year=year,
            week=week,
        )
        # Mark as NO_DATA in observations
        _save_observations(db, tenant_id, aoi_id, year, week, {}, status="NO_DATA")
        return {"status": "NO_DATA", "reason": "mosaic_not_found"}

    # 3. Calculate stats for each index
    all_stats = {}
    for index_name in indices_to_calc:
        if index_name not in INDICES:
            logger.warning("unknown_index", index=index_name)
            continue

        expression = INDICES[index_name]
        stats = await fetch_stats_from_tiler(mosaic_url, expression, geometry_geojson)

        if stats:
            all_stats[index_name] = stats
            logger.debug(
                "index_stats_calculated",
                index=index_name,
                mean=stats.get("mean"),
            )
        else:
            logger.warning("index_stats_failed", index=index_name)

    # 4. Save to database
    if all_stats:
        _save_observations(db, tenant_id, aoi_id, year, week, all_stats, status="OK")
        logger.info(
            "calculate_stats_complete",
            aoi_id=aoi_id,
            year=year,
            week=week,
            indices=list(all_stats.keys()),
        )
        return {"status": "OK", "indices": list(all_stats.keys())}
    else:
        _save_observations(db, tenant_id, aoi_id, year, week, {}, status="NO_DATA")
        return {"status": "NO_DATA", "reason": "no_stats_calculated"}
