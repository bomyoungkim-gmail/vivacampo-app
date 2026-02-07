"""Split batch repository port for idempotency."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class ISplitBatchRepository(ABC):
    @abstractmethod
    async def get_by_key(self, tenant_id: TenantId, idempotency_key: str) -> list[UUID] | None:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        tenant_id: TenantId,
        parent_aoi_id: UUID,
        idempotency_key: str,
        created_ids: list[UUID],
    ) -> None:
        raise NotImplementedError
