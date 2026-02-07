"""Field calibration repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class IFieldCalibrationRepository(ABC):
    @abstractmethod
    async def create(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        observed_date: date,
        metric_type: str,
        value: float,
        unit: str,
        source: str,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def list_by_aoi_metric(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        metric_type: str,
    ) -> list[dict]:
        raise NotImplementedError
