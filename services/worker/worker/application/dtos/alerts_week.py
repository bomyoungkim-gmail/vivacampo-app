"""DTOs for ALERTS_WEEK job."""
from __future__ import annotations

from pydantic import Field

from worker.domain.base import ImmutableDTO


class AlertsWeekCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    aoi_id: str = Field(min_length=1)
    year: int
    week: int


class AlertsWeekResult(ImmutableDTO):
    status: str
    alerts_created: int = 0
    alert_types: list[str] | None = None
    reason: str | None = None
