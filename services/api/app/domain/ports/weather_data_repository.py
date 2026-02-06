"""Weather data repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class IWeatherDataRepository(ABC):
    @abstractmethod
    async def get_history(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 365,
    ) -> list[dict]:
        raise NotImplementedError
