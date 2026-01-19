"""
FORECAST_WEEK handler - Generate yield forecasts using index-relative method.
Estimates harvest based on historical NDVI patterns.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
import structlog
from typing import Dict, Any
import json
from datetime import datetime

logger = structlog.get_logger()


async def handle_forecast_week(job: Dict[str, Any], db: Session):
    """
    Generate yield forecast for a specific week.
    
    Uses index-relative method (MVP):
    - Compare current NDVI trajectory with historical patterns
    - Estimate yield based on correlation with past seasons
    """
    logger.info("forecast_week_started", job_id=job["id"])
    
    tenant_id = job["tenant_id"]
    aoi_id = job["aoi_id"]
    year = job["payload"]["year"]
    week = job["payload"]["week"]
    
    # Get active season for this AOI
    sql = text("""
        SELECT id, crop_type, planted_date, expected_harvest_date
        FROM seasons
        WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
          AND status = 'ACTIVE'
        ORDER BY planted_date DESC
        LIMIT 1
    """)
    
    season = db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id
    }).fetchone()
    
    if not season:
        logger.info("no_active_season", aoi_id=aoi_id)
        return {"message": "No active season"}
    
    # Get current season observations
    sql = text("""
        SELECT year, week, ndvi_mean, ndvi_p90
        FROM observations_weekly
        WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
          AND status = 'OK'
        ORDER BY year, week
    """)
    
    observations = db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id
    }).fetchall()
    
    if len(observations) < 4:
        logger.info("insufficient_history", aoi_id=aoi_id, count=len(observations))
        return {"message": "Insufficient history for forecast"}
    
    # Calculate cumulative NDVI (simple index-relative method)
    current_season_ndvi = []
    for obs in observations:
        if obs.year == year and obs.week <= week:
            current_season_ndvi.append(obs.ndvi_mean)
    
    if not current_season_ndvi:
        return {"message": "No observations for current season"}
    
    # Calculate index: cumulative NDVI / weeks
    ndvi_index = sum(current_season_ndvi) / len(current_season_ndvi)
    
    # Get historical yield data for comparison
    sql = text("""
        SELECT actual_yield_kg_ha
        FROM yield_forecasts
        WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
          AND actual_yield_kg_ha IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 3
    """)
    
    historical_yields = db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id
    }).fetchall()
    
    # Simple forecast: scale historical average by current NDVI index
    if historical_yields:
        avg_historical_yield = sum(y.actual_yield_kg_ha for y in historical_yields) / len(historical_yields)
        # Assume NDVI index of 0.6 = 100% of historical yield
        baseline_ndvi = 0.6
        yield_factor = ndvi_index / baseline_ndvi
        estimated_yield = avg_historical_yield * yield_factor
        confidence = "MEDIUM" if len(historical_yields) >= 2 else "LOW"
    else:
        # No historical data - use crop type defaults
        crop_defaults = {
            "CORN": 8000,
            "SOYBEAN": 3500,
            "WHEAT": 4000,
            "RICE": 6000
        }
        base_yield = crop_defaults.get(season.crop_type, 5000)
        yield_factor = ndvi_index / 0.6
        estimated_yield = base_yield * yield_factor
        confidence = "LOW"
    
    # Calculate confidence based on data quality
    weeks_to_harvest = 12  # Simplified
    progress = len(current_season_ndvi) / weeks_to_harvest
    
    if progress < 0.3:
        confidence = "LOW"
    elif progress < 0.7:
        confidence = "MEDIUM"
    else:
        confidence = "HIGH"
    
    # Store forecast
    sql = text("""
        INSERT INTO yield_forecasts
        (tenant_id, aoi_id, season_id, year, week, method, estimated_yield_kg_ha, 
         confidence, model_version, evidence_json)
        VALUES (:tenant_id, :aoi_id, :season_id, :year, :week, 'INDEX_RELATIVE',
                :estimated_yield, :confidence, 'forecast-v1', :evidence)
        ON CONFLICT (tenant_id, aoi_id, season_id, year, week) DO UPDATE
        SET estimated_yield_kg_ha = :estimated_yield,
            confidence = :confidence,
            evidence_json = :evidence,
            updated_at = now()
    """)
    
    evidence = {
        "ndvi_index": ndvi_index,
        "observations_count": len(current_season_ndvi),
        "yield_factor": yield_factor,
        "historical_yields_count": len(historical_yields) if historical_yields else 0
    }
    
    db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "season_id": str(season.id),
        "year": year,
        "week": week,
        "estimated_yield": round(estimated_yield, 2),
        "confidence": confidence,
        "evidence": json.dumps(evidence)
    })
    db.commit()
    
    logger.info("forecast_week_completed",
                job_id=job["id"],
                estimated_yield=round(estimated_yield, 2),
                confidence=confidence)
    
    return {
        "estimated_yield_kg_ha": round(estimated_yield, 2),
        "confidence": confidence,
        "ndvi_index": round(ndvi_index, 3),
        "observations_count": len(current_season_ndvi)
    }
