from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
from datetime import date
import json

from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership
from app.config import settings
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/aois/{aoi_id}/radar/history", response_model=List[dict])
async def get_radar_history(
    aoi_id: UUID,
    year: Optional[int] = None,
    limit: int = 52,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Get historical Radar (Sentinel-1) data (RVI, Ratio).
    """
    conditions = ["tenant_id = :tenant_id", "aoi_id = :aoi_id"]
    params = {
        "tenant_id": str(membership.tenant_id),
        "aoi_id": str(aoi_id),
        "limit": limit
    }
    
    if year:
        conditions.append("year = :year")
        params["year"] = year
        
    where_clause = " AND ".join(conditions)
    
    sql = text(f"""
        SELECT year, week, rvi_mean, rvi_std, ratio_mean, ratio_std, rvi_s3_uri, ratio_s3_uri
        FROM derived_radar_assets
        WHERE {where_clause}
        ORDER BY year DESC, week DESC
        LIMIT :limit
    """)
    
    try:
        result = db.execute(sql, params)
        return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.warning("radar_table_query_failed", exc_info=e)
        return []
