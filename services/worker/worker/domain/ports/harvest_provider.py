"""Ports for DETECT_HARVEST processing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class RadarMetricsRepository(ABC):
    @abstractmethod
    def get_rvi_mean(self, *, tenant_id: str, aoi_id: str, year: int, week: int) -> Optional[float]:
        """Return RVI mean for week."""
        raise NotImplementedError


class HarvestSignalRepository(ABC):
    @abstractmethod
    def create_signal(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        rvi_current: float,
        rvi_previous: float,
    ) -> None:
        """Create harvest detected signal."""
        raise NotImplementedError
