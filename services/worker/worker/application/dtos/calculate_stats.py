"""DTOs for CALCULATE_STATS job."""
from __future__ import annotations

from pydantic import Field

from worker.domain.base import ImmutableDTO


class CalculateStatsCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    aoi_id: str = Field(min_length=1)
    year: int
    week: int
    indices: list[str] | None = None


class CalculateStatsResult(ImmutableDTO):
    status: str
    indices: list[str] | None = None
    reason: str | None = None
