"""DTOs for SIGNALS_WEEK job."""
from __future__ import annotations

from pydantic import Field

from worker.domain.base import ImmutableDTO


class SignalsWeekCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    aoi_id: str = Field(min_length=1)
    year: int
    week: int


class SignalsWeekResult(ImmutableDTO):
    status: str
    signal_type: str | None = None
    score: float | None = None
    reason: str | None = None
