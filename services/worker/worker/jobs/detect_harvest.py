"""
Harvest detection via VH backscatter proxy (RVI drop).
Scientific basis: VH drops > 3dB when crops are harvested.
"""
import json
import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = structlog.get_logger()


def get_rvi_mean(tenant_id: str, aoi_id: str, year: int, week: int, db: Session) -> float | None:
    """Get RVI mean from derived_radar_assets for a specific week."""
    sql = text("""
        SELECT rvi_mean
        FROM derived_radar_assets
        WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id AND year = :year AND week = :week
        LIMIT 1
    """)
    result = db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "year": year,
        "week": week,
    }).first()
    return result.rvi_mean if result else None


def create_harvest_signal(
    tenant_id: str,
    aoi_id: str,
    year: int,
    week: int,
    rvi_current: float,
    rvi_previous: float,
    db: Session,
):
    """Create HARVEST_DETECTED signal in opportunity_signals table."""
    sql = text("""
        INSERT INTO opportunity_signals
        (id, tenant_id, aoi_id, year, week, signal_type, status, severity,
         confidence, score, model_version, evidence_json, recommended_actions, created_at)
        VALUES
        (gen_random_uuid(), :tenant_id, :aoi_id, :year, :week, 'HARVEST_DETECTED',
         'NEW', 'INFO', 0.85, :score, 'harvest_v1', :evidence, :actions, NOW())
        ON CONFLICT DO NOTHING
    """)

    rvi_drop = rvi_previous - rvi_current
    evidence = json.dumps({
        "rvi_current": rvi_current,
        "rvi_previous": rvi_previous,
        "rvi_drop": rvi_drop,
        "detection_method": "radar_rvi_drop",
    })
    actions = json.dumps([
        "Verificar colheita em campo",
        "Atualizar registro de produtividade",
        "Notificar equipe de logística",
    ])

    db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "year": year,
        "week": week,
        "score": min(rvi_drop, 1.0),
        "evidence": evidence,
        "actions": actions,
    })
    db.commit()
    logger.info("harvest_signal_created", aoi_id=aoi_id, year=year, week=week, rvi_drop=rvi_drop)


def update_job_status(job_id: str, status: str, db: Session, error: str | None = None):
    """Update job status in jobs table."""
    sql = text("UPDATE jobs SET status = :status, error_message = :error_message, updated_at = now() WHERE id = :job_id")
    db.execute(sql, {"job_id": job_id, "status": status, "error_message": error})
    db.commit()


def detect_harvest_handler(job_id: str, payload: dict, db: Session):
    """
    DETECT_HARVEST job handler.
    Compares RVI (current week vs previous week).
    If drop > 0.3 (correlates with ~3dB VH drop), creates HARVEST_DETECTED signal.
    """
    logger.info("detect_harvest_start", job_id=job_id, payload=payload)
    update_job_status(job_id, "RUNNING", db)

    try:
        tenant_id = payload["tenant_id"]
        aoi_id = payload["aoi_id"]
        year = payload["year"]
        week = payload["week"]

        current_rvi = get_rvi_mean(tenant_id, aoi_id, year, week, db)

        # Calculate previous week
        prev_week = week - 1
        prev_year = year
        if prev_week < 1:
            prev_week = 52
            prev_year = year - 1

        previous_rvi = get_rvi_mean(tenant_id, aoi_id, prev_year, prev_week, db)

        if current_rvi is None or previous_rvi is None:
            logger.info("detect_harvest_skip_no_data", aoi_id=aoi_id)
            update_job_status(job_id, "DONE", db)
            return

        rvi_drop = previous_rvi - current_rvi
        harvest_threshold = 0.3

        if rvi_drop > harvest_threshold:
            logger.info("harvest_detected", aoi_id=aoi_id, rvi_drop=rvi_drop)
            create_harvest_signal(tenant_id, aoi_id, year, week, current_rvi, previous_rvi, db)
        else:
            logger.info("no_harvest_detected", aoi_id=aoi_id, rvi_drop=rvi_drop)

        update_job_status(job_id, "DONE", db)

    except Exception as exc:
        logger.error("detect_harvest_failed", job_id=job_id, exc_info=exc)
        update_job_status(job_id, "FAILED", db, error=str(exc))
