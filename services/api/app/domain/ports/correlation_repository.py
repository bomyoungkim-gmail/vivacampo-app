"""Correlation repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from app.domain.value_objects.tenant_id import TenantId


class ICorrelationRepository(ABC):
    @abstractmethod
    def fetch_correlation_data(
        self,
        aoi_id: str,
        tenant_id: TenantId,
        start_date: datetime,
    ) -> List[dict]:
        raise NotImplementedError

    @abstractmethod
    def fetch_year_over_year(self, aoi_id: str, tenant_id: TenantId) -> dict:
        raise NotImplementedError
