"""AOI data (assets/history) repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class IAoiDataRepository(ABC):
    @abstractmethod
    async def get_latest_assets(self, tenant_id: TenantId, aoi_id: UUID) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def get_history(self, tenant_id: TenantId, aoi_id: UUID, limit: int = 52) -> List[dict]:
        raise NotImplementedError
