"""Weather DTOs."""
from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class WeatherHistoryCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = Field(default=365, ge=1, le=2000)


class WeatherSyncCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID


class WeatherSyncResult(ImmutableDTO):
    job_id: UUID
    status: str
    message: str
