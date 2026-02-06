"""Correlation API - Combines vegetation, radar, and weather data."""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.dtos.correlation import CorrelationCommand, YearOverYearCommand
from app.application.use_cases.correlation import CorrelationUseCase, YearOverYearUseCase
from app.auth.dependencies import CurrentMembership, get_current_membership, get_current_tenant_id
from app.database import get_db
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.di_container import ApiContainer

logger = logging.getLogger(__name__)
router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])


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
    container = ApiContainer()
    use_case = container.correlation_use_case(db)
    result = use_case.execute(
        CorrelationCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_id=str(aoi_id),
            weeks=weeks,
        )
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="No correlation data found")
    return CorrelationResponse(
        data=[CorrelationDataPoint(**d.model_dump()) for d in result.data],
        insights=[Insight(**i.model_dump()) for i in result.insights],
    )


@router.get("/aois/{aoi_id}/correlation/year-over-year", response_model=YearOverYearResponse)
def get_year_over_year(
    aoi_id: UUID,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
):
    """Get year-over-year NDVI comparison for an AOI."""
    container = ApiContainer()
    use_case = container.year_over_year_use_case(db)
    result = use_case.execute(
        YearOverYearCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_id=str(aoi_id),
        )
    )
    if not result:
        raise HTTPException(status_code=404, detail="No year-over-year data found")
    return YearOverYearResponse(
        current_year=result.current_year,
        previous_year=result.previous_year,
        current_series=[YearOverYearPoint(**p.model_dump()) for p in result.current_series],
        previous_series=[YearOverYearPoint(**p.model_dump()) for p in result.previous_series],
    )