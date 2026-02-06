import asyncio

import numpy as np
import rasterio

from worker.application.dtos.process_radar import ProcessRadarCommand
from worker.application.use_cases.process_radar import ProcessRadarUseCase
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.radar_provider import ObjectStorage, RadarRepository, RadarSceneProvider
from worker.domain.ports.weather_provider import AoiGeometryRepository


class FakeJobRepository(JobRepository):
    def __init__(self) -> None:
        self.status = []

    def mark_status(self, job_id: str, status: str, error_message: str | None = None) -> None:
        self.status.append((job_id, status, error_message))

    def upsert_job(self, *, tenant_id: str, aoi_id: str, job_type: str, job_key: str, payload: dict):
        return None

    def commit(self) -> None:
        return None


class FakeAoiGeometryRepository(AoiGeometryRepository):
    def get_geometry(self, *, tenant_id: str, aoi_id: str) -> dict | None:
        return {
            "type": "Polygon",
            "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
        }


class FakeRadarProvider(RadarSceneProvider):
    def __init__(self):
        self.scenes = [
            {"id": "scene-1", "assets": {"vv": "vv", "vh": "vh"}},
        ]

    async def search_scenes(self, aoi_geometry, start_date, end_date, *, collections, max_cloud_cover):
        return self.scenes

    async def download_and_clip_band(self, href: str, geometry: dict, output_path: str) -> None:
        data = np.array([[1.0, 2.0], [3.0, 4.0]], dtype="float32")
        profile = {
            "driver": "GTiff",
            "height": data.shape[0],
            "width": data.shape[1],
            "count": 1,
            "dtype": "float32",
            "crs": "EPSG:4326",
            "transform": rasterio.transform.from_origin(0, 0, 1, 1),
        }
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data, 1)


class FakeStorage(ObjectStorage):
    def __init__(self):
        self.uploads = []

    def upload_file(self, local_path: str, key: str) -> str:
        self.uploads.append((local_path, key))
        return f"s3://bucket/{key}"


class FakeRadarRepository(RadarRepository):
    def __init__(self):
        self.saved = []
        self.ensure_called = False

    def ensure_table(self) -> None:
        self.ensure_called = True

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
        self.saved.append((tenant_id, aoi_id, year, week, rvi_uri, ratio_uri, vh_uri, vv_uri, stats))


def test_process_radar_use_case_success():
    repo = FakeJobRepository()
    radar_repo = FakeRadarRepository()
    use_case = ProcessRadarUseCase(
        job_repo=repo,
        aoi_repo=FakeAoiGeometryRepository(),
        radar_provider=FakeRadarProvider(),
        storage=FakeStorage(),
        radar_repo=radar_repo,
    )

    command = ProcessRadarCommand(
        job_id="job-1",
        tenant_id="tenant",
        aoi_id="aoi",
        year=2025,
        week=1,
    )

    result = asyncio.run(use_case.execute(command))

    assert result.status == "DONE"
    assert result.scene_found is True
    assert radar_repo.ensure_called is True
    assert radar_repo.saved
    assert repo.status[0][1] == "RUNNING"
    assert repo.status[-1][1] == "DONE"


def test_process_radar_use_case_no_scene():
    class EmptyProvider(FakeRadarProvider):
        def __init__(self):
            self.scenes = []

    repo = FakeJobRepository()
    radar_repo = FakeRadarRepository()
    use_case = ProcessRadarUseCase(
        job_repo=repo,
        aoi_repo=FakeAoiGeometryRepository(),
        radar_provider=EmptyProvider(),
        storage=FakeStorage(),
        radar_repo=radar_repo,
    )

    command = ProcessRadarCommand(
        job_id="job-2",
        tenant_id="tenant",
        aoi_id="aoi",
        year=2025,
        week=1,
    )

    result = asyncio.run(use_case.execute(command))

    assert result.status == "NO_DATA"
    assert result.scene_found is False
    assert repo.status[-1][1] == "DONE"
