"""Use case for CALCULATE_STATS job."""
from __future__ import annotations

import structlog

from worker.application.dtos.calculate_stats import CalculateStatsCommand, CalculateStatsResult
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.mosaic_provider import MosaicStorage
from worker.domain.ports.tiler_stats_provider import ObservationsRepository, TilerStatsProvider
from worker.domain.ports.weather_provider import AoiGeometryRepository
from worker.config import settings

logger = structlog.get_logger()

INDICES = {
    "ndvi": "(B08-B04)/(B08+B04)",
    "ndwi": "(B03-B08)/(B03+B08)",
    "ndmi": "(B08-B11)/(B08+B11)",
    "evi": "2.5*(B08-B04)/(B08+6*B04-7.5*B02+1)",
    "savi": "1.5*(B08-B04)/(B08+B04+0.5)",
    "ndre": "(B08-B05)/(B08+B05)",
    "gndvi": "(B08-B03)/(B08+B03)",
}


class CalculateStatsUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        aoi_repo: AoiGeometryRepository,
        mosaic_storage: MosaicStorage,
        tiler_provider: TilerStatsProvider,
        observations_repo: ObservationsRepository,
    ) -> None:
        self._job_repo = job_repo
        self._aoi_repo = aoi_repo
        self._mosaic_storage = mosaic_storage
        self._tiler_provider = tiler_provider
        self._observations_repo = observations_repo

    async def execute(self, command: CalculateStatsCommand) -> CalculateStatsResult:
        logger.info("calculate_stats_start", job_id=command.job_id)
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        try:
            geometry = self._aoi_repo.get_geometry(tenant_id=command.tenant_id, aoi_id=command.aoi_id)
            if not geometry:
                raise ValueError("AOI Geometry not found")

            key = _mosaic_key(command.year, command.week)
            if not self._mosaic_storage.exists(key=key):
                self._observations_repo.save_observations(
                    tenant_id=command.tenant_id,
                    aoi_id=command.aoi_id,
                    year=command.year,
                    week=command.week,
                    stats={},
                    status="NO_DATA",
                )
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return CalculateStatsResult(status="NO_DATA", reason="mosaic_not_found")

            mosaic_url = f"s3://{settings.s3_bucket}/{key}"
            indices = command.indices or list(INDICES.keys())
            all_stats = {}

            for index_name in indices:
                if index_name not in INDICES:
                    logger.warning("unknown_index", index=index_name)
                    continue

                expression = INDICES[index_name]
                stats = await self._tiler_provider.fetch_stats(
                    mosaic_url=mosaic_url,
                    expression=expression,
                    geometry=geometry,
                )

                if stats:
                    all_stats[index_name] = stats
                else:
                    logger.warning("index_stats_failed", index=index_name)

            if all_stats:
                self._observations_repo.save_observations(
                    tenant_id=command.tenant_id,
                    aoi_id=command.aoi_id,
                    year=command.year,
                    week=command.week,
                    stats=all_stats,
                    status="OK",
                )
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return CalculateStatsResult(status="OK", indices=list(all_stats.keys()))

            self._observations_repo.save_observations(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                year=command.year,
                week=command.week,
                stats={},
                status="NO_DATA",
            )
            self._job_repo.mark_status(command.job_id, "DONE")
            self._job_repo.commit()
            return CalculateStatsResult(status="NO_DATA", reason="no_stats_calculated")
        except Exception as exc:
            logger.error("calculate_stats_failed", job_id=command.job_id, error=str(exc), exc_info=True)
            self._job_repo.mark_status(command.job_id, "FAILED", error_message=str(exc))
            self._job_repo.commit()
            raise


def _mosaic_key(year: int, week: int, collection: str = "sentinel-2-l2a") -> str:
    return f"mosaics/{collection}/{year}/w{week:02d}.json"
