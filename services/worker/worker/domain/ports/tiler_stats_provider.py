"""Ports for TiTiler stats and observations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional


class TilerStatsProvider(ABC):
    @abstractmethod
    async def fetch_stats(self, *, mosaic_url: str, expression: str, geometry: dict) -> Optional[Dict[str, float]]:
        """Fetch stats from TiTiler."""
        raise NotImplementedError


class ObservationsRepository(ABC):
    @abstractmethod
    def save_observations(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        stats: Dict[str, Dict[str, float]],
        status: str,
    ) -> None:
        """Persist observations."""
        raise NotImplementedError
