
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
from datetime import date
import hashlib
import json

from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership, require_role
from app.config import settings
from app.infrastructure.sqs_client import get_sqs_client
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/aois/{aoi_id}/weather/history", response_model=List[dict])
async def get_weather_history(
    aoi_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 365,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Get historical weather data (Precipitation, Temperature, ET0).
    """
    conditions = ["tenant_id = :tenant_id", "aoi_id = :aoi_id"]
    params = {
        "tenant_id": str(membership.tenant_id),
        "aoi_id": str(aoi_id),
        "limit": limit
    }
    
    if start_date:
        conditions.append("date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("date <= :end_date")
        params["end_date"] = end_date
        
    where_clause = " AND ".join(conditions)
    
    sql = text(f"""
        SELECT date, temp_max, temp_min, precip_sum, et0_fao
        FROM derived_weather_daily
        WHERE {where_clause}
        ORDER BY date DESC
        LIMIT :limit
    """)
    
    # Check if table exists first preventing 500 if migration didn't run
    # Actually, worker creates table. If not exists, return empty.
    try:
        result = db.execute(sql, params)
        return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.warning("weather_table_query_failed", exc_info=e)
        return []

@router.post("/aois/{aoi_id}/weather/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_weather_data(
    aoi_id: UUID,
    membership: CurrentMembership = Depends(require_role("OPERATOR")),
    db: Session = Depends(get_db)
):
    """
    Trigger a job to fetch/update weather data from Open-Meteo.
    """
    tenant_id = str(membership.tenant_id)
    s_aoi_id = str(aoi_id)
    job_key = hashlib.sha256(f"{tenant_id}{s_aoi_id}WEATHER_SYNC".encode()).hexdigest()
    
    # Insert Job
    sql = text("""
        INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
        VALUES (:tenant_id, :aoi_id, 'PROCESS_WEATHER', :job_key, 'PENDING', :payload)
        ON CONFLICT (tenant_id, job_key) DO UPDATE
        SET status = 'PENDING', updated_at = now()
        RETURNING id
    """)
    
    payload = {
        "tenant_id": tenant_id,
        "aoi_id": s_aoi_id,
        # Default: Full history backfill logic in worker handle this
    }
    
    result = db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": s_aoi_id,
        "job_key": job_key,
        "payload": json.dumps(payload)
    })
    db.commit()
    
    job_id = result.fetchone()[0]
    
    # Dispatch SQS
    sqs = get_sqs_client()
    msg = {
        "job_id": str(job_id),
        "job_type": "PROCESS_WEATHER",
        "payload": payload
    }
    sqs.send_message(settings.sqs_queue_name, json.dumps(msg))
    
    return {"message": "Weather sync started", "job_id": job_id}
