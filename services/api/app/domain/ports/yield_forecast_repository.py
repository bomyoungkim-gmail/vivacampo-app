"""Yield forecast repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class IYieldForecastRepository(ABC):
    @abstractmethod
    async def get_latest_by_aoi(self, tenant_id: TenantId, aoi_id: UUID) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    async def get_tenant_summary(self, tenant_id: TenantId) -> dict | None:
        raise NotImplementedError
