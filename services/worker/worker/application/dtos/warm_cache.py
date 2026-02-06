"""DTOs for WARM_CACHE job."""
from __future__ import annotations

from pydantic import Field

from worker.domain.base import ImmutableDTO


class WarmCacheCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    aoi_id: str = Field(min_length=1)
    indices: list[str] | None = None
    zoom_levels: list[int] | None = None


class WarmCacheResult(ImmutableDTO):
    status: str
    aoi_id: str
    stats: dict
    reason: str | None = None
