"""Ports for topography processing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class TopographySceneProvider(ABC):
    @abstractmethod
    async def search_scenes(
        self,
        aoi_geometry: dict,
        start_date: datetime,
        end_date: datetime,
        *,
        collections: list[str],
    ) -> list[dict]:
        """Search DEM scenes."""
        raise NotImplementedError

    @abstractmethod
    async def download_and_clip_band(self, href: str, geometry: dict, output_path: str) -> None:
        """Download and clip DEM."""
        raise NotImplementedError


class TopographyRepository(ABC):
    @abstractmethod
    def ensure_table(self) -> None:
        """Ensure topography table exists."""
        raise NotImplementedError

    @abstractmethod
    def save_assets(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        dem_uri: str,
        slope_uri: str,
        aspect_uri: str | None,
        stats: dict,
    ) -> None:
        """Persist topography assets and stats."""
        raise NotImplementedError
