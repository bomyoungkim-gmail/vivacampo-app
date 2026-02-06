"""AOI repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.aoi import AOI
from app.domain.value_objects.tenant_id import TenantId


class IAOIRepository(ABC):
    @abstractmethod
    async def create(self, aoi: AOI) -> AOI:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, tenant_id: TenantId, aoi_id: UUID) -> Optional[AOI]:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        name: Optional[str] = None,
        use_type: Optional[str] = None,
        status: Optional[str] = None,
        geometry_wkt: Optional[str] = None,
    ) -> Optional[AOI]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, tenant_id: TenantId, aoi_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: TenantId,
        farm_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[AOI]:
        raise NotImplementedError
