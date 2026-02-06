"""Radar data repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class IRadarDataRepository(ABC):
    @abstractmethod
    async def get_history(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        year: Optional[int] = None,
        limit: int = 52,
    ) -> list[dict]:
        raise NotImplementedError
