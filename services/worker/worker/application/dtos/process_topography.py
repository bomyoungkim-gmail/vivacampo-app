"""DTOs for PROCESS_TOPOGRAPHY job."""
from __future__ import annotations

from pydantic import Field

from worker.domain.base import ImmutableDTO


class ProcessTopographyCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    aoi_id: str = Field(min_length=1)


class ProcessTopographyResult(ImmutableDTO):
    status: str
    scene_found: bool
