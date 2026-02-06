"""Ports for WARM_CACHE processing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class AoiBoundsRepository(ABC):
    @abstractmethod
    def get_bounds(self, *, tenant_id: str, aoi_id: str) -> Optional[Tuple[float, float, float, float]]:
        """Return AOI bounds (minx, miny, maxx, maxy)."""
        raise NotImplementedError


class TileWarmClient(ABC):
    @abstractmethod
    async def fetch_tile(self, *, aoi_id: str, z: int, x: int, y: int, index: str) -> bool:
        """Fetch a tile and return success flag."""
        raise NotImplementedError
