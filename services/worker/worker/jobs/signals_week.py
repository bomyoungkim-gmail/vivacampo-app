import structlog
from sqlalchemy.orm import Session
from sqlalchemy import text
from worker.config import settings
from datetime import datetime
from worker.signals.features import (
    extract_features,
    calculate_rule_score,
    calculate_ml_score,
    calculate_final_score,
    determine_severity,
    determine_confidence
)
from worker.signals.change_detection import (
    detect_change_bfast_like,
    detect_change_simple,
    calculate_change_score
)
from worker.signals.signal_types import (
    determine_signal_type,
    get_recommended_actions
)

logger = structlog.get_logger()


def signals_week_handler(job_id: str, payload: dict, db: Session):
    """
    SIGNALS_WEEK job handler.
    Generates opportunity signals using change detection and scoring.
    
    Steps:
    1. Query observations_weekly (last N weeks)
    2. Extract features
    3. Run change detection (BFastLike or Simple)
    4. Calculate scores (rule + change + ml)
    5. Determine signal_type based on use_type
    6. Generate recommended_actions
    7. Check for existing signals (dedupe)
    8. Save opportunity_signals
    """
    logger.info("signals_week_start", job_id=job_id, payload=payload)
    
    tenant_id = payload['tenant_id']
    aoi_id = payload['aoi_id']
    year = payload['year']
    week = payload['week']
    
    try:
        # Step 1: Query observations (last N weeks)
        logger.info("step_1_query_observations")
        observations = query_observations(tenant_id, aoi_id, year, week, db)
        
        if len(observations) < settings.signals_min_history_weeks:
            logger.warning("insufficient_history", count=len(observations), required=settings.signals_min_history_weeks)
            update_job_status(job_id, "DONE", db)
            return
        
        # Get AOI info for use_type
        aoi_info = get_aoi_info(aoi_id, db)
        use_type = aoi_info['use_type']
        
        # Step 2: Extract features
        logger.info("step_2_extract_features")
        features = extract_features(observations)
        
        if not features:
            logger.warning("no_features_extracted")
            update_job_status(job_id, "DONE", db)
            return
        
        # Step 3: Change detection
        logger.info("step_3_change_detection", method=settings.signals_change_detection)
        
        if settings.signals_change_detection == "BFastLike":
            change_detection = detect_change_bfast_like(
                observations,
                persistence_weeks=settings.signals_persistence_weeks
            )
        else:
            change_detection = detect_change_simple(observations)
        
        # Step 4: Calculate scores
        logger.info("step_4_calculate_scores")
        
        rule_score = calculate_rule_score(features, use_type)
        change_score = calculate_change_score(change_detection)
        ml_score = calculate_ml_score(features)
        
        final_score = calculate_final_score(rule_score, change_score, ml_score)
        
        logger.info("scores_calculated", 
                   rule=rule_score, 
                   change=change_score, 
                   ml=ml_score, 
                   final=final_score)
        
        # Check threshold
        if final_score < settings.signals_score_threshold:
            logger.info("score_below_threshold", score=final_score, threshold=settings.signals_score_threshold)
            update_job_status(job_id, "DONE", db)
            return
        
        # Step 5: Determine signal_type
        logger.info("step_5_determine_signal_type")
        signal_type = determine_signal_type(use_type, features, change_detection or {})
        
        # Step 6: Generate recommended_actions
        logger.info("step_6_generate_actions")
        recommended_actions = get_recommended_actions(signal_type)
        
        # Calculate severity and confidence
        avg_valid_pixel_ratio = sum(o.get('valid_pixel_ratio', 0) for o in observations) / len(observations)
        severity = determine_severity(final_score)
        confidence = determine_confidence(final_score, avg_valid_pixel_ratio, len(observations))
        
        # Prepare evidence
        evidence = {
            'window_weeks': len(observations),
            'baseline_ref': observations[0].get('baseline', 0),
            'valid_pixel_ratio_summary': {
                'mean': avg_valid_pixel_ratio,
                'min': min(o.get('valid_pixel_ratio', 0) for o in observations)
            },
            'change_detection': change_detection or {}
        }
        
        # Step 7: Check for existing signals (dedupe)
        logger.info("step_7_check_dedupe")
        existing_signal = check_existing_signal(tenant_id, aoi_id, year, week, signal_type, db)
        
        if existing_signal:
            logger.info("updating_existing_signal", signal_id=existing_signal['id'])
            update_signal(existing_signal['id'], final_score, evidence, features, db)
        else:
            # Step 8: Save new signal
            logger.info("step_8_save_signal")
            
            # Use end of week as "detection/creation" date for correct timeline sorting
            from worker.shared.utils import get_week_date_range
            _, end_date = get_week_date_range(year, week)
            
            save_signal(
                tenant_id=tenant_id,
                aoi_id=aoi_id,
                year=year,
                week=week,
                signal_type=signal_type,
                severity=severity,
                confidence=confidence,
                score=final_score,
                evidence=evidence,
                features=features,
                recommended_actions=recommended_actions,
                db=db,
                created_at=end_date
            )
        
        update_job_status(job_id, "DONE", db)
        logger.info("signals_week_complete", job_id=job_id, signal_type=signal_type, score=final_score)
        
    except Exception as e:
        logger.error("signals_week_failed", job_id=job_id, exc_info=e)
        update_job_status(job_id, "FAILED", db, error=str(e))
        raise


def query_observations(tenant_id: str, aoi_id: str, year: int, week: int, db: Session):
    """Query last N observations for AOI"""
    sql = text("""
        SELECT year, week, ndvi_mean, ndvi_p10, ndvi_p50, ndvi_p90, ndvi_std, 
               baseline, anomaly, valid_pixel_ratio, status
        FROM observations_weekly
        WHERE tenant_id = :tenant_id 
          AND aoi_id = :aoi_id
          AND status = 'OK'
        ORDER BY year DESC, week DESC
        LIMIT :limit
    """)
    
    result = db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "limit": settings.signals_min_history_weeks + 10
    })
    
    observations = []
    for row in result:
        observations.append({
            'year': row.year,
            'week': row.week,
            'ndvi_mean': row.ndvi_mean,
            'ndvi_p10': row.ndvi_p10,
            'ndvi_p50': row.ndvi_p50,
            'ndvi_p90': row.ndvi_p90,
            'ndvi_std': row.ndvi_std,
            'baseline': row.baseline,
            'anomaly': row.anomaly,
            'valid_pixel_ratio': row.valid_pixel_ratio
        })
    
    # Reverse to chronological order
    return list(reversed(observations))


def get_aoi_info(aoi_id: str, db: Session):
    """Get AOI information"""
    sql = text("SELECT use_type FROM aois WHERE id = :aoi_id")
    result = db.execute(sql, {"aoi_id": aoi_id}).fetchone()
    return {"use_type": result.use_type if result else "PASTURE"}


def check_existing_signal(tenant_id: str, aoi_id: str, year: int, week: int, signal_type: str, db: Session):
    """Check for existing signal (dedupe)"""
    sql = text("""
        SELECT id, status
        FROM opportunity_signals
        WHERE tenant_id = :tenant_id
          AND aoi_id = :aoi_id
          AND year = :year
          AND week = :week
          AND signal_type = :signal_type
          AND pipeline_version = :pipeline_version
    """)
    
    result = db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "year": year,
        "week": week,
        "signal_type": signal_type,
        "pipeline_version": settings.pipeline_version
    }).fetchone()
    
    if result:
        return {"id": result.id, "status": result.status}
    return None


def update_signal(signal_id: str, score: float, evidence: dict, features: dict, db: Session):
    """Update existing signal"""
    import json
    
    sql = text("""
        UPDATE opportunity_signals
        SET score = :score,
            evidence_json = :evidence,
            features_json = :features,
            updated_at = now()
        WHERE id = :signal_id
    """)
    
    db.execute(sql, {
        "signal_id": signal_id,
        "score": score,
        "evidence": json.dumps(evidence),
        "features": json.dumps(features)
    })
    db.commit()


def save_signal(
    tenant_id: str,
    aoi_id: str,
    year: int,
    week: int,
    signal_type: str,
    severity: str,
    confidence: str,
    score: float,
    evidence: dict,
    features: dict,
    recommended_actions: list,
    db: Session,
    created_at: datetime = None
):
    """Save new opportunity signal"""
    import json
    
    sql = text("""
        INSERT INTO opportunity_signals
        (tenant_id, aoi_id, year, week, pipeline_version, signal_type, status,
         severity, confidence, score, model_version, change_method, 
         evidence_json, features_json, recommended_actions, created_at)
        VALUES
        (:tenant_id, :aoi_id, :year, :week, :pipeline_version, :signal_type, 'OPEN',
         :severity, :confidence, :score, :model_version, :change_method,
         :evidence, :features, :actions, :created_at)
    """)
    
    db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "year": year,
        "week": week,
        "pipeline_version": settings.pipeline_version,
        "signal_type": signal_type,
        "severity": severity,
        "confidence": confidence,
        "score": score,
        "model_version": settings.signals_model_version,
        "change_method": settings.signals_change_detection,
        "evidence": json.dumps(evidence),
        "features": json.dumps(features),
        "actions": json.dumps(recommended_actions),
        "created_at": created_at or datetime.now()
    })
    db.commit()


def update_job_status(job_id: str, status: str, db: Session, error: str = None):
    """Update job status"""
    sql = text("UPDATE jobs SET status = :status, updated_at = now() WHERE id = :job_id")
    db.execute(sql, {"job_id": job_id, "status": status})
    db.commit()

