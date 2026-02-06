"""Use case for PROCESS_RADAR_WEEK job."""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
import structlog

from worker.application.dtos.process_radar import ProcessRadarCommand, ProcessRadarResult
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.radar_provider import ObjectStorage, RadarRepository, RadarSceneProvider
from worker.domain.ports.weather_provider import AoiGeometryRepository
from worker.shared.utils import get_week_date_range

logger = structlog.get_logger()


class ProcessRadarUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        aoi_repo: AoiGeometryRepository,
        radar_provider: RadarSceneProvider,
        storage: ObjectStorage,
        radar_repo: RadarRepository,
    ) -> None:
        self._job_repo = job_repo
        self._aoi_repo = aoi_repo
        self._radar_provider = radar_provider
        self._storage = storage
        self._radar_repo = radar_repo

    async def execute(self, command: ProcessRadarCommand) -> ProcessRadarResult:
        logger.info("process_radar_start", job_id=command.job_id)
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        try:
            self._radar_repo.ensure_table()
            aoi_geom = self._aoi_repo.get_geometry(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
            )
            if not aoi_geom:
                raise ValueError("AOI Geometry not found")

            start_date, end_date = get_week_date_range(command.year, command.week)

            scenes = await self._radar_provider.search_scenes(
                aoi_geom,
                start_date,
                end_date,
                collections=["sentinel-1-rtc"],
                max_cloud_cover=100,
            )

            valid_scenes = [s for s in scenes if s.get("assets", {}).get("vv") and s.get("assets", {}).get("vh")]
            if not valid_scenes:
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return ProcessRadarResult(status="NO_DATA", scene_found=False)

            best_scene = valid_scenes[0]
            logger.info("selected_best_radar_scene", scene_id=best_scene.get("id"))

            tmpdir = _create_workdir()
            try:
                vv_path, vh_path, profile = await _download_bands(
                    self._radar_provider,
                    aoi_geom,
                    best_scene,
                    str(tmpdir),
                )

                with rasterio.open(vv_path) as src:
                    vv = src.read(1)
                with rasterio.open(vh_path) as src:
                    vh = src.read(1)

                rvi, ratio, stats = _calculate_indices(vv, vh)

                prefix = f"tenant={command.tenant_id}/aoi={command.aoi_id}/year={command.year}/week={command.week}/radar/"
                rvi_uri = _upload_band(self._storage, rvi, profile, str(tmpdir), prefix, "rvi")
                ratio_uri = _upload_band(self._storage, ratio, profile, str(tmpdir), prefix, "ratio")
                vh_uri = self._storage.upload_file(vh_path, prefix + "vh.tif")
                vv_uri = self._storage.upload_file(vv_path, prefix + "vv.tif")

                self._radar_repo.save_assets(
                    tenant_id=command.tenant_id,
                    aoi_id=command.aoi_id,
                    year=command.year,
                    week=command.week,
                    rvi_uri=rvi_uri,
                    ratio_uri=ratio_uri,
                    vh_uri=vh_uri,
                    vv_uri=vv_uri,
                    stats=stats,
                )
            finally:
                _cleanup_workdir(tmpdir)

            self._job_repo.mark_status(command.job_id, "DONE")
            self._job_repo.commit()
            return ProcessRadarResult(status="DONE", scene_found=True)
        except Exception as exc:
            logger.error("process_radar_failed", job_id=command.job_id, error=str(exc), exc_info=True)
            self._job_repo.mark_status(command.job_id, "FAILED", error_message=str(exc))
            self._job_repo.commit()
            raise


def _calculate_indices(vv: np.ndarray, vh: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    if np.nanmean(vv) < 0:
        logger.info("detect_db_scale_converting_to_linear")
        vv = 10 ** (vv / 10.0)
        vh = 10 ** (vh / 10.0)

    numerator = 4 * vh
    denominator = vv + vh
    denominator = np.where(denominator == 0, 0.0001, denominator)
    rvi = np.clip(numerator / denominator, 0, 1)

    vv_safe = np.where(vv == 0, 0.0001, vv)
    ratio = vh / vv_safe

    stats = {}

    def calc_stats(arr: np.ndarray, name: str) -> dict:
        v = arr[~np.isnan(arr)]
        if v.size == 0:
            return {f"{name}_mean": 0.0, f"{name}_std": 0.0}
        return {f"{name}_mean": float(np.mean(v)), f"{name}_std": float(np.std(v))}

    stats.update(calc_stats(rvi, "rvi"))
    stats.update(calc_stats(ratio, "ratio"))
    return rvi, ratio, stats


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


async def _download_bands(provider: RadarSceneProvider, geometry: dict, scene: dict, tmpdir: str):
    vv_href = scene["assets"]["vv"]
    vh_href = scene["assets"]["vh"]

    tmp_path = Path(tmpdir)
    vv_path = tmp_path / "vv.tif"
    vh_path = tmp_path / "vh.tif"

    await provider.download_and_clip_band(vv_href, geometry, str(vv_path))
    await provider.download_and_clip_band(vh_href, geometry, str(vh_path))

    profile = None
    with rasterio.open(str(vv_path)) as src:
        profile = src.profile

    return str(vv_path), str(vh_path), profile


def _upload_band(storage: ObjectStorage, data: np.ndarray, profile: dict, tmpdir: str, prefix: str, name: str) -> str:
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
