"""DTOs for DETECT_HARVEST job."""
from __future__ import annotations

from pydantic import Field

from worker.domain.base import ImmutableDTO


class DetectHarvestCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    aoi_id: str = Field(min_length=1)
    year: int
    week: int


class DetectHarvestResult(ImmutableDTO):
    status: str
    detected: bool
    reason: str | None = None
