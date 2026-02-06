"""Use case for PROCESS_TOPOGRAPHY job."""
from __future__ import annotations

import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np
import rasterio
import structlog

from worker.application.dtos.process_topography import ProcessTopographyCommand, ProcessTopographyResult
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.radar_provider import ObjectStorage
from worker.domain.ports.topography_provider import TopographyRepository, TopographySceneProvider
from worker.domain.ports.weather_provider import AoiGeometryRepository

logger = structlog.get_logger()


class ProcessTopographyUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        aoi_repo: AoiGeometryRepository,
        topo_provider: TopographySceneProvider,
        storage: ObjectStorage,
        topo_repo: TopographyRepository,
    ) -> None:
        self._job_repo = job_repo
        self._aoi_repo = aoi_repo
        self._topo_provider = topo_provider
        self._storage = storage
        self._topo_repo = topo_repo

    async def execute(self, command: ProcessTopographyCommand) -> ProcessTopographyResult:
        logger.info("process_topography_start", job_id=command.job_id)
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        try:
            self._topo_repo.ensure_table()
            aoi_geom = self._aoi_repo.get_geometry(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
            )
            if not aoi_geom:
                raise ValueError("AOI Geometry not found")

            scenes = await self._topo_provider.search_scenes(
                aoi_geom,
                datetime(2010, 1, 1),
                datetime.now(),
                collections=["copernicus-dem-glo-30"],
            )

            if not scenes:
                logger.warning("no_dem_found", aoi_id=command.aoi_id)
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return ProcessTopographyResult(status="NO_DATA", scene_found=False)

            best_scene = scenes[0]

            tmpdir = _create_workdir()
            try:
                href = best_scene.get("assets", {}).get("data") or best_scene.get("assets", {}).get("dem")
                if not href:
                    raise ValueError("DEM asset not found")

                dem_path = tmpdir / "dem.tif"
                await self._topo_provider.download_and_clip_band(href, aoi_geom, str(dem_path))

                with rasterio.open(str(dem_path)) as src:
                    dem = src.read(1)
                    profile = src.profile
                    lat_mean = profile["transform"][5]
                    scale_x = 111320 * np.cos(np.deg2rad(lat_mean))
                    scale_y = 111320

                    dy, dx = np.gradient(dem)
                    res_x_deg = profile["transform"][0]
                    res_y_deg = -profile["transform"][4]

                    slope_rad = np.arctan(
                        np.sqrt((dx / res_x_deg / scale_x) ** 2 + (dy / res_y_deg / scale_y) ** 2)
                    )
                    slope_deg = np.degrees(slope_rad)

                    stats = {
                        "ele_min": float(np.nanmin(dem)),
                        "ele_max": float(np.nanmax(dem)),
                        "ele_mean": float(np.nanmean(dem)),
                        "slope_mean": float(np.nanmean(slope_deg)),
                    }

                prefix = f"tenant={command.tenant_id}/aoi={command.aoi_id}/static/topo/"
                dem_uri = self._storage.upload_file(str(dem_path), prefix + "dem.tif")
                slope_uri = _export_and_upload(self._storage, slope_deg, profile, str(tmpdir), prefix, "slope")

                self._topo_repo.save_assets(
                    tenant_id=command.tenant_id,
                    aoi_id=command.aoi_id,
                    dem_uri=dem_uri,
                    slope_uri=slope_uri,
                    aspect_uri=None,
                    stats=stats,
                )
            finally:
                _cleanup_workdir(tmpdir)

            self._job_repo.mark_status(command.job_id, "DONE")
            self._job_repo.commit()
            return ProcessTopographyResult(status="DONE", scene_found=True)
        except Exception as exc:
            logger.error("process_topography_failed", job_id=command.job_id, error=str(exc), exc_info=True)
            self._job_repo.mark_status(command.job_id, "FAILED", error_message=str(exc))
            self._job_repo.commit()
            raise


def _get_temp_dir() -> Path:
    configured = (
        os.getenv("WORKER_TMP_DIR")
        or os.getenv("TMPDIR")
        or os.getenv("TEMP")
        or os.getenv("TMP")
    )
    base = Path(configured) if configured else Path(".tmp")
    base.mkdir(parents=True, exist_ok=True)
    return base


def _create_workdir() -> Path:
    base = _get_temp_dir()
    workdir = base / f"worker-{uuid.uuid4().hex}"
    workdir.mkdir(parents=True, exist_ok=False)
    return workdir


def _cleanup_workdir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def _export_and_upload(storage: ObjectStorage, data: np.ndarray, profile: dict, tmpdir: str, prefix: str, name: str) -> str:
    profile = profile.copy()
    profile.update(
        {
            "driver": "GTiff",
            "dtype": "float32",
            "count": 1,
            "compress": "deflate",
            "predictor": 2,
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
        }
    )
    path = Path(tmpdir) / f"{name}.tif"
    with rasterio.open(str(path), "w", **profile) as dst:
        dst.write(data.astype("float32"), 1)
    return storage.upload_file(str(path), prefix + f"{name}.tif")
