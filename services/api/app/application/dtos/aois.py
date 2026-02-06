"""AOI DTOs for application layer."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class CreateAoiCommand(ImmutableDTO):
    tenant_id: TenantId
    farm_id: UUID
    name: str = Field(min_length=1, max_length=200)
    use_type: str
    geometry_wkt: str


class ListAoisCommand(ImmutableDTO):
    tenant_id: TenantId
    farm_id: Optional[UUID] = None
    status: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=500)


class AoiResult(ImmutableDTO):
    id: UUID
    tenant_id: UUID
    farm_id: UUID
    name: str
    use_type: str
    status: str
    area_ha: float
    geometry: str
    created_at: datetime
