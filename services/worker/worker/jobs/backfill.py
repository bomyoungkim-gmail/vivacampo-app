"""
BACKFILL handler - Orchestrate processing of historical data.
Creates PROCESS_WEEK, ALERTS_WEEK, SIGNALS_WEEK, and FORECAST_WEEK jobs for each week.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
import structlog
from typing import Dict, Any
import json
from datetime import datetime, timedelta
import hashlib

logger = structlog.get_logger()


async def handle_backfill(job: Dict[str, Any], db: Session):
    """
    Orchestrate backfill processing for a date range.
    
    Creates jobs in sequence:
    1. PROCESS_WEEK (generate observations)
    2. ALERTS_WEEK (generate alerts)
    3. SIGNALS_WEEK (generate signals)
    4. FORECAST_WEEK (generate forecasts)
    """
    logger.info("backfill_started", job_id=job["id"])
    db.execute(text("UPDATE jobs SET status = 'RUNNING', updated_at = now() WHERE id = :job_id"), {"job_id": job["id"]})
    db.commit()
    
    tenant_id = job["tenant_id"]
    aoi_id = job["aoi_id"]
    from_date = datetime.strptime(job["payload"]["from_date"], "%Y-%m-%d")
    to_date = datetime.strptime(job["payload"]["to_date"], "%Y-%m-%d")
    
    # Calculate weeks to process
    weeks_to_process = []
    current_date = from_date
    
    while current_date <= to_date:
        year = current_date.isocalendar()[0]
        week = current_date.isocalendar()[1]
        weeks_to_process.append((year, week))
        current_date += timedelta(days=7)
    
    logger.info("backfill_weeks_calculated", 
                total_weeks=len(weeks_to_process),
                from_date=str(from_date),
                to_date=str(to_date))
    
    # Get pipeline version
    from worker.config import settings
    pipeline_version = settings.pipeline_version
    
    jobs_created = {
        "PROCESS_WEEK": 0,
        "PROCESS_RADAR_WEEK": 0,
        "PROCESS_WEATHER": 0,
        "PROCESS_TOPOGRAPHY": 0,
        "ALERTS_WEEK": 0,
        "SIGNALS_WEEK": 0,
        "FORECAST_WEEK": 0
    }
    
    # Create jobs for each week
    from worker.shared.aws_clients import SQSClient
    sqs = SQSClient()

    # Create PROCESS_WEATHER (range-based) once per backfill
    weather_job_key = hashlib.sha256(
        f"{tenant_id}{aoi_id}{from_date.date().isoformat()}{to_date.date().isoformat()}PROCESS_WEATHER{pipeline_version}".encode()
    ).hexdigest()

    weather_payload = {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "start_date": from_date.date().isoformat(),
        "end_date": to_date.date().isoformat()
    }

    sql_weather = text("""
        INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
        VALUES (:tenant_id, :aoi_id, 'PROCESS_WEATHER', :job_key, 'PENDING', :payload)
        ON CONFLICT (tenant_id, job_key) DO UPDATE 
        SET status = 'PENDING', updated_at = now()
        RETURNING id
    """)

    result = db.execute(sql_weather, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "job_key": weather_job_key,
        "payload": json.dumps(weather_payload)
    })

    row = result.fetchone()
    if row:
        jobs_created["PROCESS_WEATHER"] += 1
        sqs.send_message({
            "job_id": str(row[0]),
            "job_type": "PROCESS_WEATHER",
            "payload": weather_payload
        })

    # Create PROCESS_TOPOGRAPHY once per backfill
    topo_job_key = hashlib.sha256(
        f"{tenant_id}{aoi_id}PROCESS_TOPOGRAPHY{pipeline_version}".encode()
    ).hexdigest()

    topo_payload = {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id
    }

    sql_topo = text("""
        INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
        VALUES (:tenant_id, :aoi_id, 'PROCESS_TOPOGRAPHY', :job_key, 'PENDING', :payload)
        ON CONFLICT (tenant_id, job_key) DO UPDATE 
        SET status = 'PENDING', updated_at = now()
        RETURNING id
    """)

    result = db.execute(sql_topo, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "job_key": topo_job_key,
        "payload": json.dumps(topo_payload)
    })

    row = result.fetchone()
    if row:
        jobs_created["PROCESS_TOPOGRAPHY"] += 1
        sqs.send_message({
            "job_id": str(row[0]),
            "job_type": "PROCESS_TOPOGRAPHY",
            "payload": topo_payload
        })

    for year, week in weeks_to_process:
        # 1. PROCESS_WEEK
        job_key = hashlib.sha256(
            f"{tenant_id}{aoi_id}{year}{week}PROCESS_WEEK{pipeline_version}".encode()
        ).hexdigest()
        
        payload_dict = {
            "tenant_id": tenant_id,
            "aoi_id": aoi_id,
            "year": year,
            "week": week
        }

        sql = text("""
            INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
            VALUES (:tenant_id, :aoi_id, 'PROCESS_WEEK', :job_key, 'PENDING', :payload)
            ON CONFLICT (tenant_id, job_key) DO UPDATE 
            SET status = 'PENDING', updated_at = now()
            RETURNING id
        """)
        
        result = db.execute(sql, {
            "tenant_id": tenant_id,
            "aoi_id": aoi_id,
            "job_key": job_key,
            "payload": json.dumps(payload_dict)
        })
        
        row = result.fetchone()
        if row:
            jobs_created["PROCESS_WEEK"] += 1
            sqs.send_message({
                "job_id": str(row[0]),
                "job_type": "PROCESS_WEEK",
                "payload": payload_dict
            })

        # 1b. PROCESS_RADAR_WEEK
        job_key = hashlib.sha256(
            f"{tenant_id}{aoi_id}{year}{week}PROCESS_RADAR_WEEK{pipeline_version}".encode()
        ).hexdigest()

        sql = text("""
            INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
            VALUES (:tenant_id, :aoi_id, 'PROCESS_RADAR_WEEK', :job_key, 'PENDING', :payload)
            ON CONFLICT (tenant_id, job_key) DO UPDATE 
            SET status = 'PENDING', updated_at = now()
            RETURNING id
        """)

        result = db.execute(sql, {
            "tenant_id": tenant_id,
            "aoi_id": aoi_id,
            "job_key": job_key,
            "payload": json.dumps(payload_dict)
        })

        row = result.fetchone()
        if row:
            jobs_created["PROCESS_RADAR_WEEK"] += 1
            sqs.send_message({
                "job_id": str(row[0]),
                "job_type": "PROCESS_RADAR_WEEK",
                "payload": payload_dict
            })
        
        # 2. ALERTS_WEEK
        job_key = hashlib.sha256(
            f"{tenant_id}{aoi_id}{year}{week}ALERTS_WEEK{pipeline_version}".encode()
        ).hexdigest()
        
        sql = text("""
            INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
            VALUES (:tenant_id, :aoi_id, 'ALERTS_WEEK', :job_key, 'PENDING', :payload)
            ON CONFLICT (tenant_id, job_key) DO UPDATE 
            SET status = 'PENDING', updated_at = now()
            RETURNING id
        """)

        result = db.execute(sql, {
            "tenant_id": tenant_id,
            "aoi_id": aoi_id,
            "job_key": job_key,
            "payload": json.dumps(payload_dict)
        })
        
        row = result.fetchone()
        if row:
            jobs_created["ALERTS_WEEK"] += 1
            sqs.send_message({
                "job_id": str(row[0]),
                "job_type": "ALERTS_WEEK",
                "payload": payload_dict
            })
        
        # 3. SIGNALS_WEEK (only if signals enabled)
        if settings.signals_enabled:
            job_key = hashlib.sha256(
                f"{tenant_id}{aoi_id}{year}{week}SIGNALS_WEEK{pipeline_version}".encode()
            ).hexdigest()
            
            sql_signals = text("""
                INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
                VALUES (:tenant_id, :aoi_id, 'SIGNALS_WEEK', :job_key, 'PENDING', :payload)
                ON CONFLICT (tenant_id, job_key) DO UPDATE 
                SET status = 'PENDING', updated_at = now()
                RETURNING id
            """)
            
            result = db.execute(sql_signals, {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "job_key": job_key,
                "payload": json.dumps(payload_dict)
            })
            
            row = result.fetchone()
            if row:
                jobs_created["SIGNALS_WEEK"] += 1
                sqs.send_message({
                    "job_id": str(row[0]),
                    "job_type": "SIGNALS_WEEK",
                    "payload": payload_dict
                })
        
        # 4. FORECAST_WEEK (only for crop AOIs with active season)
        sql_check_season = text("""
            SELECT id FROM seasons
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
        """)
        
        has_season = db.execute(sql_check_season, {
            "tenant_id": tenant_id,
            "aoi_id": aoi_id
        }).fetchone()
        
        if has_season:
            job_key = hashlib.sha256(
                f"{tenant_id}{aoi_id}{year}{week}FORECAST_WEEK{pipeline_version}".encode()
            ).hexdigest()
            
            sql_forecast = text("""
                INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
                VALUES (:tenant_id, :aoi_id, 'FORECAST_WEEK', :job_key, 'PENDING', :payload)
                ON CONFLICT (tenant_id, job_key) DO UPDATE 
                SET status = 'PENDING', updated_at = now()
                RETURNING id
            """)
            
            result = db.execute(sql_forecast, {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "job_key": job_key,
                "payload": json.dumps(payload_dict)
            })
            
            row = result.fetchone()
            if row:
                jobs_created["FORECAST_WEEK"] += 1
                sqs.send_message({
                    "job_id": str(row[0]),
                    "job_type": "FORECAST_WEEK",
                    "payload": payload_dict
                })
    
    db.commit()
    
    # Update status of THIS job (the backfill job)
    # Update status of THIS job (the backfill job)
    sql_update = text("UPDATE jobs SET status = 'DONE', updated_at = now() WHERE id = :job_id")
    db.execute(sql_update, {"job_id": job["id"]})
    db.commit()
    
    logger.info("backfill_completed",
                job_id=job["id"],
                weeks_processed=len(weeks_to_process),
                jobs_created=jobs_created)
    
    return {
        "weeks_processed": len(weeks_to_process),
        "jobs_created": jobs_created,
        "total_jobs": sum(jobs_created.values())
    }
