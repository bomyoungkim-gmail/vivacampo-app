"""Cached satellite provider wrapper."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional

from worker.pipeline.providers.base import SatelliteDataProvider
from worker.pipeline.scene_cache import SceneCacheRepository


class CachedSatelliteProvider(SatelliteDataProvider):
    def __init__(
        self,
        provider: SatelliteDataProvider,
        db_factory: Callable[[], Any],
        max_age_days: int = 14,
    ) -> None:
        self._provider = provider
        self._db_factory = db_factory
        self._max_age_days = max_age_days

    @property
    def provider_name(self) -> str:
        return f"cached({self._provider.provider_name})"

    @property
    def supported_collections(self) -> List[str]:
        return self._provider.supported_collections

    async def search_scenes(
        self,
        aoi_geom: Dict[str, Any],
        start_date: datetime | date,
        end_date: datetime | date,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        collections = collections or []
        cache_key = SceneCacheRepository.build_cache_key(
            provider_name=self._provider.provider_name,
            collections=collections,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=max_cloud_cover,
            geometry=aoi_geom,
        )

        try:
            scenes = await self._provider.search_scenes(
                aoi_geom, start_date, end_date, max_cloud_cover, collections
            )
            db = self._db_factory()
            try:
                repo = SceneCacheRepository(db)
                repo.save(
                    cache_key=cache_key,
                    provider_name=self._provider.provider_name,
                    collections=collections,
                    start_date=start_date,
                    end_date=end_date,
                    max_cloud_cover=max_cloud_cover,
                    bbox=None,
                    geometry=aoi_geom,
                    scenes=scenes,
                )
                repo.cleanup(max_age_days=self._max_age_days)
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            return scenes
        except Exception:
            db = self._db_factory()
            try:
                repo = SceneCacheRepository(db)
                cached = repo.get(cache_key)
                if cached is not None:
                    return cached
            finally:
                try:
                    db.close()
                except Exception:
                    pass
            raise

    async def download_and_clip_band(self, asset_href, aoi_geom, output_path):
        return await self._provider.download_and_clip_band(asset_href, aoi_geom, output_path)

    def sign_url(self, href: str) -> str:
        return self._provider.sign_url(href)

    async def search_raw_items(
        self,
        bbox: List[float],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None,
        max_items: int = 2000,
    ):
        return await self._provider.search_raw_items(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=max_cloud_cover,
            collections=collections,
            max_items=max_items,
        )

    async def health_check(self) -> bool:
        return await self._provider.health_check()
