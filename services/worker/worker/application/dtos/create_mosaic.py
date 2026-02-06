"""DTOs for CREATE_MOSAIC job."""
from __future__ import annotations

from pydantic import Field

from worker.domain.base import ImmutableDTO


class CreateMosaicCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    year: int
    week: int
    collection: str = "sentinel-2-l2a"
    max_cloud_cover: float = 30


class CreateMosaicResult(ImmutableDTO):
    status: str
    mosaic_url: str | None
    scene_count: int
    tile_count: int | None = None
