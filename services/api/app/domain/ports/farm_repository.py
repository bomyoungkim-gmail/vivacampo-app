"""Farm repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.farm import Farm
from app.domain.value_objects.tenant_id import TenantId


class IFarmRepository(ABC):
    @abstractmethod
    async def find_by_id_and_tenant(self, farm_id: UUID, tenant_id: TenantId) -> Optional[Farm]:
        raise NotImplementedError

    @abstractmethod
    async def find_all_by_tenant(self, tenant_id: TenantId) -> List[Farm]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, farm: Farm) -> Farm:
        raise NotImplementedError
