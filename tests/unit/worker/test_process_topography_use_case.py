import asyncio
import numpy as np
import rasterio

from worker.application.dtos.process_topography import ProcessTopographyCommand
from worker.application.use_cases.process_topography import ProcessTopographyUseCase
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.radar_provider import ObjectStorage
from worker.domain.ports.topography_provider import TopographyRepository, TopographySceneProvider
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


class FakeTopographyProvider(TopographySceneProvider):
    def __init__(self, scenes):
        self._scenes = scenes

    async def search_scenes(self, aoi_geometry, start_date, end_date, *, collections):
        return self._scenes

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


class FakeTopographyRepository(TopographyRepository):
    def __init__(self):
        self.saved = []
        self.ensure_called = False

    def ensure_table(self) -> None:
        self.ensure_called = True

    def save_assets(self, *, tenant_id: str, aoi_id: str, dem_uri: str, slope_uri: str, aspect_uri: str | None, stats: dict):
        self.saved.append((tenant_id, aoi_id, dem_uri, slope_uri, aspect_uri, stats))


def test_process_topography_use_case_success():
    repo = FakeJobRepository()
    topo_repo = FakeTopographyRepository()
    use_case = ProcessTopographyUseCase(
        job_repo=repo,
        aoi_repo=FakeAoiGeometryRepository(),
        topo_provider=FakeTopographyProvider([
            {"id": "dem-1", "assets": {"data": "dem"}},
        ]),
        storage=FakeStorage(),
        topo_repo=topo_repo,
    )

    command = ProcessTopographyCommand(job_id="job-1", tenant_id="tenant", aoi_id="aoi")
    result = asyncio.run(use_case.execute(command))

    assert result.status == "DONE"
    assert result.scene_found is True
    assert topo_repo.ensure_called is True
    assert topo_repo.saved
    assert repo.status[0][1] == "RUNNING"
    assert repo.status[-1][1] == "DONE"


def test_process_topography_use_case_no_scene():
    repo = FakeJobRepository()
    topo_repo = FakeTopographyRepository()
    use_case = ProcessTopographyUseCase(
        job_repo=repo,
        aoi_repo=FakeAoiGeometryRepository(),
        topo_provider=FakeTopographyProvider([]),
        storage=FakeStorage(),
        topo_repo=topo_repo,
    )

    command = ProcessTopographyCommand(job_id="job-2", tenant_id="tenant", aoi_id="aoi")
    result = asyncio.run(use_case.execute(command))

    assert result.status == "NO_DATA"
    assert result.scene_found is False
    assert repo.status[-1][1] == "DONE"
