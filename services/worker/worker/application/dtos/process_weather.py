"""DTOs for PROCESS_WEATHER job."""
from __future__ import annotations

from datetime import date

from pydantic import Field, model_validator

from worker.domain.base import ImmutableDTO


class ProcessWeatherCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    aoi_id: str = Field(min_length=1)
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_range(self) -> "ProcessWeatherCommand":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        return self


class ProcessWeatherResult(ImmutableDTO):
    status: str
    records_saved: int
    clamped: bool
