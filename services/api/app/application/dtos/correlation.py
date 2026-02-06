"""Correlation DTOs for application layer."""
from datetime import datetime
from typing import List, Optional

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class CorrelationCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: str
    weeks: int = Field(default=12, ge=4, le=52)


class YearOverYearCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: str


class CorrelationDataPoint(ImmutableDTO):
    date: str
    ndvi: Optional[float] = None
    rvi: Optional[float] = None
    rain_mm: Optional[float] = None
    temp_avg: Optional[float] = None


class Insight(ImmutableDTO):
    type: str
    message: str
    severity: str


class CorrelationResult(ImmutableDTO):
    data: List[CorrelationDataPoint]
    insights: List[Insight]


class YearOverYearPoint(ImmutableDTO):
    week: int
    ndvi: Optional[float] = None


class YearOverYearResult(ImmutableDTO):
    current_year: int
    previous_year: int
    current_series: List[YearOverYearPoint]
    previous_series: List[YearOverYearPoint]
