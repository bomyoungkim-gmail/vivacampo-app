"""Use case for CREATE_MOSAIC job."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable

import structlog

from worker.application.dtos.create_mosaic import CreateMosaicCommand, CreateMosaicResult
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.mosaic_provider import MosaicProvider, MosaicRegistry, MosaicStorage

logger = structlog.get_logger()

BRAZIL_BBOX = [-74.0, -34.0, -34.0, 6.0]
SENTINEL2_BANDS = [
    "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12", "SCL"
]
SENTINEL1_BANDS = ["VV", "VH"]


class CreateMosaicUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        provider: MosaicProvider,
        storage: MosaicStorage,
        registry: MosaicRegistry,
    ) -> None:
        self._job_repo = job_repo
        self._provider = provider
        self._storage = storage
        self._registry = registry

    def execute(self, command: CreateMosaicCommand) -> CreateMosaicResult:
        logger.info(
            "create_mosaic_start",
            job_id=command.job_id,
            year=command.year,
            week=command.week,
            collection=command.collection,
        )
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        start_date, end_date = iso_week_to_dates(command.year, command.week)
        bands = _bands_for_collection(command.collection)

        try:
            scenes = list(
                self._provider.search_scenes(
                    collection=command.collection,
                    start_date=start_date,
                    end_date=end_date,
                    bbox=BRAZIL_BBOX,
                    max_cloud_cover=command.max_cloud_cover,
                    max_items=2000,
                )
            )

            if not scenes:
                empty_mosaic = {
                    "mosaicjson": "0.0.3",
                    "name": f"{command.collection}-{command.year}-w{command.week:02d}",
                    "tiles": {},
                    "metadata": {
                        "status": "NO_DATA",
                        "created_at": datetime.utcnow().isoformat(),
                    },
                }
                key = _mosaic_key(command.collection, command.year, command.week)
                url = self._storage.save_json(key=key, payload=empty_mosaic)
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return CreateMosaicResult(status="NO_DATA", mosaic_url=url, scene_count=0, tile_count=0)

            mosaic = create_mosaic_json(scenes, command.collection, command.year, command.week, bands)
            key = _mosaic_key(command.collection, command.year, command.week)
            url = self._storage.save_json(key=key, payload=mosaic)

            self._registry.save_record(
                collection=command.collection,
                year=command.year,
                week=command.week,
                url=url,
                scene_count=len(scenes),
            )

            self._job_repo.mark_status(command.job_id, "DONE")
            self._job_repo.commit()

            return CreateMosaicResult(
                status="OK",
                mosaic_url=url,
                scene_count=len(scenes),
                tile_count=len(mosaic.get("tiles", {})),
            )
        except Exception as exc:
            logger.error("create_mosaic_failed", job_id=command.job_id, error=str(exc), exc_info=True)
            self._job_repo.mark_status(command.job_id, "FAILED", error_message=str(exc))
            self._job_repo.commit()
            raise


def iso_week_to_dates(year: int, week: int) -> tuple[str, str]:
    jan4 = datetime(year, 1, 4)
    start_of_year = jan4 - timedelta(days=jan4.isoweekday() - 1)
    start_date = start_of_year + timedelta(weeks=week - 1)
    end_date = start_date + timedelta(days=6)
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def create_mosaic_json(
    scenes: Iterable[Any],
    collection: str,
    year: int,
    week: int,
    bands: list[str],
) -> Dict[str, Any]:
    _ = bands
    import mercantile

    minzoom = 8
    maxzoom = 14
    tiles_dict: Dict[str, list[str]] = {}

    for item in scenes:
        self_link = None
        if hasattr(item, "links"):
            for link in item.links:
                if link.rel == "self":
                    self_link = link.href
                    break

        if not self_link:
            self_link = f"https://planetarycomputer.microsoft.com/api/stac/v1/collections/{collection}/items/{item.id}"

        if item.bbox:
            tiles = list(mercantile.tiles(*item.bbox, zooms=maxzoom))
            for tile in tiles:
                qk = mercantile.quadkey(tile)
                tiles_dict.setdefault(qk, [])
                if self_link not in tiles_dict[qk]:
                    tiles_dict[qk].append(self_link)

    return {
        "mosaicjson": "0.0.3",
        "name": f"{collection}-{year}-w{week:02d}",
        "description": f"Weekly mosaic for {collection}, {year} week {week}",
        "version": "1.0.0",
        "minzoom": minzoom,
        "maxzoom": maxzoom,
        "quadkey_zoom": maxzoom,
        "center": [-55.0, -15.0, 10],
        "bounds": BRAZIL_BBOX,
        "tiles": tiles_dict,
    }


def _mosaic_key(collection: str, year: int, week: int) -> str:
    return f"mosaics/{collection}/{year}/w{week:02d}.json"


def _bands_for_collection(collection: str) -> list[str]:
    if collection == "sentinel-2-l2a":
        return SENTINEL2_BANDS
    if collection == "sentinel-1-rtc":
        return SENTINEL1_BANDS
    return SENTINEL2_BANDS
