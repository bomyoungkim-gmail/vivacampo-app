"""AOI management DTOs (update/delete/backfill/assets/history)."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class UpdateAoiCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    use_type: Optional[str] = None
    status: Optional[str] = None
    geometry_wkt: Optional[str] = None


class DeleteAoiCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID


class RequestBackfillCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    from_date: str
    to_date: str
    cadence: str


class AoiAssetsCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID


class AoiHistoryCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    limit: int = Field(default=52, ge=1, le=200)


class BackfillResult(ImmutableDTO):
    job_id: UUID
    status: str
    weeks_count: int
    message: str


class UpdateAoiResult(ImmutableDTO):
    id: UUID
    farm_id: UUID
    name: str
    use_type: str
    status: str
    area_ha: float
    geometry: str
    created_at: datetime
    geometry_changed: bool = False
