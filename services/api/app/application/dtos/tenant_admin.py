"""Tenant admin DTOs."""
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class ListMembersCommand(ImmutableDTO):
    tenant_id: TenantId


class InviteMemberCommand(ImmutableDTO):
    tenant_id: TenantId
    email: str
    name: Optional[str] = None
    role: str


class UpdateMemberRoleCommand(ImmutableDTO):
    tenant_id: TenantId
    membership_id: UUID
    role: str


class UpdateMemberStatusCommand(ImmutableDTO):
    tenant_id: TenantId
    membership_id: UUID
    status: str


class GetTenantSettingsCommand(ImmutableDTO):
    tenant_id: TenantId


class UpdateTenantSettingsCommand(ImmutableDTO):
    tenant_id: TenantId
    min_valid_pixel_ratio: Optional[float] = None
    alert_thresholds: Optional[dict] = None


class GetTenantAuditLogCommand(ImmutableDTO):
    tenant_id: TenantId
    limit: int = Field(default=50, ge=1, le=100)
