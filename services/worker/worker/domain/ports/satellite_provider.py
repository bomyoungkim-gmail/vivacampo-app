"""Satellite data provider port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SatelliteScene:
    id: str
    datetime: datetime
    cloud_cover: float
    platform: str
    collection: str
    bbox: List[float]
    geometry: Dict[str, Any]
    assets: Dict[str, Optional[str]]


class ISatelliteProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def search_scenes(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        collections: Optional[List[str]] = None,
        max_cloud_cover: float = 60.0,
    ) -> List[SatelliteScene]:
        raise NotImplementedError

    @abstractmethod
    async def download_band(
        self,
        asset_href: str,
        geometry: Dict[str, Any],
        output_path: str,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError
