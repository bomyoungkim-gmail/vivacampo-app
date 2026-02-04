"""Correlation API - Combines vegetation, radar, and weather data."""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.correlation import CorrelationService
from app.auth.dependencies import CurrentMembership, get_current_membership
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class CorrelationDataPoint(BaseModel):
    date: str
    ndvi: Optional[float] = None
    rvi: Optional[float] = None
    rain_mm: Optional[float] = None
    temp_avg: Optional[float] = None


class Insight(BaseModel):
    type: str
    message: str
    severity: str


class CorrelationResponse(BaseModel):
    data: List[CorrelationDataPoint]
    insights: List[Insight]


class YearOverYearPoint(BaseModel):
    week: int
    ndvi: Optional[float] = None


class YearOverYearResponse(BaseModel):
    current_year: int
    previous_year: int
    current_series: List[YearOverYearPoint]
    previous_series: List[YearOverYearPoint]


@router.get("/aois/{aoi_id}/correlation/vigor-climate", response_model=CorrelationResponse)
def get_vigor_climate_correlation(
    aoi_id: UUID,
    weeks: int = Query(default=12, ge=4, le=52),
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
):
    """Get correlation data between vegetation vigor and climate."""
    service = CorrelationService(db)
    data = service.fetch_correlation_data(str(aoi_id), str(membership.tenant_id), weeks)
    if not data:
        raise HTTPException(status_code=404, detail="No correlation data found")
    insights = service.generate_insights(data)
    return CorrelationResponse(
        data=[CorrelationDataPoint(**d) for d in data],
        insights=[Insight(**i) for i in insights],
    )


@router.get("/aois/{aoi_id}/correlation/year-over-year", response_model=YearOverYearResponse)
def get_year_over_year(
    aoi_id: UUID,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
):
    """Get year-over-year NDVI comparison for an AOI."""
    service = CorrelationService(db)
    result = service.fetch_year_over_year(str(aoi_id), str(membership.tenant_id))
    if not result:
        raise HTTPException(status_code=404, detail="No year-over-year data found")
    return YearOverYearResponse(
        current_year=result["current_year"],
        previous_year=result["previous_year"],
        current_series=[YearOverYearPoint(**d) for d in result["current_series"]],
        previous_series=[YearOverYearPoint(**d) for d in result["previous_series"]],
    )
