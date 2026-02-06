"""DTOs for worker backfill jobs."""
from __future__ import annotations

from datetime import date
from typing import Dict

from pydantic import Field, model_validator

from worker.domain.base import ImmutableDTO


class BackfillCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    aoi_id: str = Field(min_length=1)
    from_date: date
    to_date: date
    pipeline_version: str = Field(min_length=1)
    signals_enabled: bool = False

    @model_validator(mode="after")
    def validate_date_range(self) -> "BackfillCommand":
        if self.from_date > self.to_date:
            raise ValueError("from_date must be on or before to_date")
        return self


class BackfillResult(ImmutableDTO):
    weeks_processed: int
    jobs_created: Dict[str, int]
    total_jobs: int
