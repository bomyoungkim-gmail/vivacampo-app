"""
ALERTS_WEEK handler - Generate risk alerts based on observations.
Detects conditions that require immediate attention.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
import structlog
from typing import Dict, Any
import json

logger = structlog.get_logger()


async def handle_alerts_week(job: Dict[str, Any], db: Session):
    """
    Generate alerts for a specific week based on observations.
    
    Alert types:
    - LOW_NDVI: NDVI below critical threshold
    - RAPID_DECLINE: Sudden drop in vegetation
    - PERSISTENT_ANOMALY: Negative anomaly for multiple weeks
    - NO_DATA: Insufficient valid pixels
    """
    logger.info("alerts_week_started", job_id=job["id"])
    
    tenant_id = job["tenant_id"]
    aoi_id = job["aoi_id"]
    year = job["payload"]["year"]
    week = job["payload"]["week"]
    
    # Get tenant settings
    sql = text("SELECT min_valid_pixel_ratio FROM tenant_settings WHERE tenant_id = :tenant_id")
    settings_result = db.execute(sql, {"tenant_id": tenant_id}).fetchone()
    min_valid_ratio = settings_result.min_valid_pixel_ratio if settings_result else 0.15
    
    # Get current observation
    sql = text("""
        SELECT status, valid_pixel_ratio, ndvi_mean, ndvi_p10, anomaly
        FROM observations_weekly
        WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id 
          AND year = :year AND week = :week
    """)
    
    obs = db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "year": year,
        "week": week
    }).fetchone()
    
    if not obs:
        logger.warning("no_observation_found", aoi_id=aoi_id, year=year, week=week)
        return
    
    alerts_to_create = []
    
    # Alert 1: NO_DATA
    if obs.status == "NO_DATA" or obs.valid_pixel_ratio < min_valid_ratio:
        alerts_to_create.append({
            "alert_type": "NO_DATA",
            "severity": "LOW",
            "confidence": "HIGH",
            "evidence": {
                "valid_pixel_ratio": obs.valid_pixel_ratio,
                "threshold": min_valid_ratio,
                "status": obs.status
            }
        })
    
    # Alert 2: LOW_NDVI (critical threshold)
    if obs.ndvi_mean and obs.ndvi_mean < 0.3:
        severity = "HIGH" if obs.ndvi_mean < 0.2 else "MEDIUM"
        alerts_to_create.append({
            "alert_type": "LOW_NDVI",
            "severity": severity,
            "confidence": "HIGH",
            "evidence": {
                "ndvi_mean": obs.ndvi_mean,
                "ndvi_p10": obs.ndvi_p10,
                "threshold": 0.3
            }
        })
    
    # Alert 3: RAPID_DECLINE (compare with previous week)
    sql = text("""
        SELECT ndvi_mean
        FROM observations_weekly
        WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
          AND (year = :year AND week < :week) OR (year = :prev_year AND week > :week)
        ORDER BY year DESC, week DESC
        LIMIT 1
    """)
    
    prev_obs = db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "year": year,
        "week": week,
        "prev_year": year - 1
    }).fetchone()
    
    if prev_obs and prev_obs.ndvi_mean and obs.ndvi_mean:
        decline = prev_obs.ndvi_mean - obs.ndvi_mean
        if decline > 0.15:  # 15% drop
            alerts_to_create.append({
                "alert_type": "RAPID_DECLINE",
                "severity": "HIGH",
                "confidence": "MEDIUM",
                "evidence": {
                    "current_ndvi": obs.ndvi_mean,
                    "previous_ndvi": prev_obs.ndvi_mean,
                    "decline": decline
                }
            })
    
    # Alert 4: PERSISTENT_ANOMALY (negative for 3+ weeks)
    sql = text("""
        SELECT COUNT(*) as count
        FROM observations_weekly
        WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
          AND year = :year AND week <= :week AND week > :week - 3
          AND anomaly < -0.05
    """)
    
    persistent = db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "year": year,
        "week": week
    }).fetchone()
    
    if persistent and persistent.count >= 3:
        alerts_to_create.append({
            "alert_type": "PERSISTENT_ANOMALY",
            "severity": "MEDIUM",
            "confidence": "HIGH",
            "evidence": {
                "weeks_count": persistent.count,
                "current_anomaly": obs.anomaly
            }
        })
    
    # Create alerts
    for alert_data in alerts_to_create:
        # Check for duplicates
        sql = text("""
            SELECT id FROM alerts
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
              AND year = :year AND week = :week
              AND alert_type = :alert_type
              AND status IN ('OPEN', 'ACK')
        """)
        
        existing = db.execute(sql, {
            "tenant_id": tenant_id,
            "aoi_id": aoi_id,
            "year": year,
            "week": week,
            "alert_type": alert_data["alert_type"]
        }).fetchone()
        
        if existing:
            # Update existing
            sql = text("""
                UPDATE alerts
                SET severity = :severity, confidence = :confidence,
                    evidence_json = :evidence, updated_at = now()
                WHERE id = :alert_id
            """)
            db.execute(sql, {
                "severity": alert_data["severity"],
                "confidence": alert_data["confidence"],
                "evidence": json.dumps(alert_data["evidence"]),
                "alert_id": existing.id
            })
        else:
            # Create new
            sql = text("""
                INSERT INTO alerts
                (tenant_id, aoi_id, year, week, alert_type, status, severity, confidence, evidence_json)
                VALUES (:tenant_id, :aoi_id, :year, :week, :alert_type, 'OPEN', :severity, :confidence, :evidence)
            """)
            db.execute(sql, {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "year": year,
                "week": week,
                "alert_type": alert_data["alert_type"],
                "severity": alert_data["severity"],
                "confidence": alert_data["confidence"],
                "evidence": json.dumps(alert_data["evidence"])
            })
    
    db.commit()
    
    logger.info("alerts_week_completed", 
                job_id=job["id"], 
                alerts_created=len(alerts_to_create))
    
    return {
        "alerts_created": len(alerts_to_create),
        "alert_types": [a["alert_type"] for a in alerts_to_create]
    }
