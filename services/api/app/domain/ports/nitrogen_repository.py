"""Nitrogen repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.value_objects.tenant_id import TenantId


class INitrogenRepository(ABC):
    @abstractmethod
    def get_latest_indices(self, tenant_id: TenantId, aoi_id: str) -> dict:
        raise NotImplementedError
