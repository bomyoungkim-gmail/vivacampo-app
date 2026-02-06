"""AI assistant repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class IAiAssistantRepository(ABC):
    @abstractmethod
    async def create_thread(
        self,
        tenant_id: TenantId,
        aoi_id: Optional[UUID],
        signal_id: Optional[UUID],
        membership_id: UUID,
        provider: str,
        model: str,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def list_threads(self, tenant_id: TenantId, limit: int = 50) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_state(self, tenant_id: TenantId, thread_id: UUID) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    async def list_approvals(self, tenant_id: TenantId, pending_only: bool) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def get_approval_thread_id(self, tenant_id: TenantId, approval_id: UUID) -> Optional[UUID]:
        raise NotImplementedError
