"""Farm DTOs for application layer."""
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class CreateFarmCommand(ImmutableDTO):
    tenant_id: TenantId
    name: str = Field(min_length=3, max_length=100)
    timezone: str


class ListFarmsCommand(ImmutableDTO):
    tenant_id: TenantId


class FarmResult(ImmutableDTO):
    id: UUID
    tenant_id: UUID
    name: str
    timezone: str
    aoi_count: int = 0
    created_at: datetime
