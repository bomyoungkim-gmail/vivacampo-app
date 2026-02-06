"""Use case for WARM_CACHE job."""
from __future__ import annotations

import asyncio
import math
from typing import List, Tuple

import structlog

from worker.application.dtos.warm_cache import WarmCacheCommand, WarmCacheResult
from worker.config import settings
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.warm_cache_provider import AoiBoundsRepository, TileWarmClient

logger = structlog.get_logger()

WARM_ZOOM_LEVELS = [10, 11, 12, 13, 14]
MAX_TILES_PER_AOI = 200
CONCURRENT_REQUESTS = 10


class WarmCacheUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        bounds_repo: AoiBoundsRepository,
        tile_client: TileWarmClient,
    ) -> None:
        self._job_repo = job_repo
        self._bounds_repo = bounds_repo
        self._tile_client = tile_client

    async def execute(self, command: WarmCacheCommand) -> WarmCacheResult:
        logger.info("warm_cache_start", job_id=command.job_id, aoi_id=command.aoi_id)
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        try:
            indices = command.indices or ["ndvi"]
            zoom_levels = command.zoom_levels or WARM_ZOOM_LEVELS
            bounds = self._bounds_repo.get_bounds(tenant_id=command.tenant_id, aoi_id=command.aoi_id)
            if not bounds:
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return WarmCacheResult(status="NOT_FOUND", aoi_id=command.aoi_id, stats={}, reason="aoi_not_found")

            all_tiles = []
            for zoom in zoom_levels:
                all_tiles.extend(get_tiles_for_bounds(*bounds, zoom))

            if len(all_tiles) > MAX_TILES_PER_AOI:
                all_tiles = all_tiles[:MAX_TILES_PER_AOI]

            stats = {"total_tiles": len(all_tiles) * len(indices), "success": 0, "failed": 0}

            semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

            async def fetch_with_semaphore(aoi_id, z, x, y, index):
                async with semaphore:
                    return await self._tile_client.fetch_tile(aoi_id=aoi_id, z=z, x=x, y=y, index=index)

            for index in indices:
                tasks = [fetch_with_semaphore(command.aoi_id, z, x, y, index) for z, x, y in all_tiles]
                results = await asyncio.gather(*tasks)
                for success in results:
                    if success:
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1

            self._job_repo.mark_status(command.job_id, "DONE")
            self._job_repo.commit()
            return WarmCacheResult(status="OK", aoi_id=command.aoi_id, stats=stats)
        except Exception as exc:
            logger.error("warm_cache_failed", job_id=command.job_id, error=str(exc), exc_info=True)
            self._job_repo.mark_status(command.job_id, "FAILED", error_message=str(exc))
            self._job_repo.commit()
            raise


def lng_lat_to_tile(lng: float, lat: float, zoom: int) -> Tuple[int, int]:
    n = 2 ** zoom
    x = int((lng + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def get_tiles_for_bounds(minx: float, miny: float, maxx: float, maxy: float, zoom: int) -> List[Tuple[int, int, int]]:
    min_tile = lng_lat_to_tile(minx, maxy, zoom)
    max_tile = lng_lat_to_tile(maxx, miny, zoom)

    tiles = []
    for x in range(min_tile[0], max_tile[0] + 1):
        for y in range(min_tile[1], max_tile[1] + 1):
            tiles.append((zoom, x, y))
    return tiles
