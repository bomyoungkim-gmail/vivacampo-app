"""AI assistant DTOs."""
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class CreateThreadCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: Optional[UUID] = None
    signal_id: Optional[UUID] = None
    membership_id: UUID
    provider: str
    model: str


class ListThreadsCommand(ImmutableDTO):
    tenant_id: TenantId
    limit: int = Field(default=50, ge=1, le=50)


class GetMessagesCommand(ImmutableDTO):
    tenant_id: TenantId
    thread_id: UUID


class ListApprovalsCommand(ImmutableDTO):
    tenant_id: TenantId
    pending_only: bool = True


class GetApprovalThreadCommand(ImmutableDTO):
    tenant_id: TenantId
    approval_id: UUID
