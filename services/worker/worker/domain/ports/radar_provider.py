"""Ports for radar processing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


class RadarSceneProvider(ABC):
    @abstractmethod
    async def search_scenes(
        self,
        aoi_geometry: dict,
        start_date,
        end_date,
        *,
        collections: list[str],
        max_cloud_cover: float,
    ) -> list[dict]:
        """Search radar scenes."""
        raise NotImplementedError

    @abstractmethod
    async def download_and_clip_band(self, href: str, geometry: dict, output_path: str) -> None:
        """Download and clip a band for a geometry."""
        raise NotImplementedError


class RadarRepository(ABC):
    @abstractmethod
    def ensure_table(self) -> None:
        """Ensure radar table exists."""
        raise NotImplementedError

    @abstractmethod
    def save_assets(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        rvi_uri: str,
        ratio_uri: str,
        vh_uri: str,
        vv_uri: str,
        stats: dict,
    ) -> None:
        """Persist radar assets and stats."""
        raise NotImplementedError


class ObjectStorage(ABC):
    @abstractmethod
    def upload_file(self, local_path: str, key: str) -> str:
        """Upload a file and return the URI."""
        raise NotImplementedError
