"""DTOs for PROCESS_RADAR_WEEK job."""
from __future__ import annotations

from pydantic import Field

from worker.domain.base import ImmutableDTO


class ProcessRadarCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    aoi_id: str = Field(min_length=1)
    year: int
    week: int


class ProcessRadarResult(ImmutableDTO):
    status: str
    scene_found: bool
