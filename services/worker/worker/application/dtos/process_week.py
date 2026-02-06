"""DTOs for PROCESS_WEEK job."""
from __future__ import annotations

from typing import Any, Dict

from pydantic import Field

from worker.domain.base import ImmutableDTO


class ProcessWeekCommand(ImmutableDTO):
    job_id: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    aoi_id: str = Field(min_length=1)
    year: int
    week: int
    payload: Dict[str, Any]
    use_dynamic_tiling: bool = True


class ProcessWeekResult(ImmutableDTO):
    status: str
    details: Dict[str, Any] | None = None
