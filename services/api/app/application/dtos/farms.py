"""Farm DTOs for application layer."""
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId
from app.domain.entities.user import UserRole


class CreateFarmCommand(ImmutableDTO):
    tenant_id: TenantId
    user_id: UUID
    user_role: UserRole
    name: str = Field(min_length=3, max_length=100)
    timezone: str


class ListFarmsCommand(ImmutableDTO):
    tenant_id: TenantId


class UpdateFarmCommand(ImmutableDTO):
    farm_id: UUID
    tenant_id: TenantId
    user_id: UUID
    user_role: UserRole
    name: str | None = Field(default=None, min_length=3, max_length=100)
    timezone: str | None = None


class DeleteFarmCommand(ImmutableDTO):
    farm_id: UUID
    tenant_id: TenantId
    user_id: UUID
    user_role: UserRole


class FarmResult(ImmutableDTO):
    id: UUID
    tenant_id: UUID
    created_by_user_id: UUID | None = None
    name: str
    timezone: str
    aoi_count: int = 0
    created_at: datetime
