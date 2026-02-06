"""DTOs for FORECAST_WEEK job."""
from __future__ import annotations

from pydantic import Field

from worker.domain.base import ImmutableDTO


class ForecastWeekCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    aoi_id: str = Field(min_length=1)
    year: int
    week: int


class ForecastWeekResult(ImmutableDTO):
    status: str
    estimated_yield_kg_ha: float | None = None
    confidence: str | None = None
    ndvi_index: float | None = None
    observations_count: int | None = None
    reason: str | None = None
