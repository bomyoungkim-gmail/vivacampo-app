import asyncio

from worker.application.dtos.calculate_stats import CalculateStatsCommand
from worker.application.use_cases.calculate_stats import CalculateStatsUseCase
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.mosaic_provider import MosaicStorage
from worker.domain.ports.tiler_stats_provider import ObservationsRepository, TilerStatsProvider
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
        return {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}


class FakeMosaicStorage(MosaicStorage):
    def __init__(self, exists: bool):
        self._exists = exists

    def save_json(self, *, key: str, payload: dict) -> str:
        return f"s3://bucket/{key}"

    def exists(self, *, key: str) -> bool:
        return self._exists


class FakeTilerStatsProvider(TilerStatsProvider):
    async def fetch_stats(self, *, mosaic_url: str, expression: str, geometry: dict):
        return {"mean": 0.5, "std": 0.1, "p10": 0.2, "p50": 0.5, "p90": 0.8}


class FakeObservationsRepository(ObservationsRepository):
    def __init__(self):
        self.saved = []

    def save_observations(self, *, tenant_id: str, aoi_id: str, year: int, week: int, stats: dict, status: str) -> None:
        self.saved.append((tenant_id, aoi_id, year, week, stats, status))


def test_calculate_stats_no_mosaic():
    use_case = CalculateStatsUseCase(
        job_repo=FakeJobRepository(),
        aoi_repo=FakeAoiGeometryRepository(),
        mosaic_storage=FakeMosaicStorage(False),
        tiler_provider=FakeTilerStatsProvider(),
        observations_repo=FakeObservationsRepository(),
    )

    command = CalculateStatsCommand(job_id="job-1", tenant_id="tenant", aoi_id="aoi", year=2025, week=1)
    result = asyncio.run(use_case.execute(command))

    assert result.status == "NO_DATA"
    assert result.reason == "mosaic_not_found"


def test_calculate_stats_success():
    obs_repo = FakeObservationsRepository()
    use_case = CalculateStatsUseCase(
        job_repo=FakeJobRepository(),
        aoi_repo=FakeAoiGeometryRepository(),
        mosaic_storage=FakeMosaicStorage(True),
        tiler_provider=FakeTilerStatsProvider(),
        observations_repo=obs_repo,
    )

    command = CalculateStatsCommand(job_id="job-2", tenant_id="tenant", aoi_id="aoi", year=2025, week=1, indices=["ndvi"])
    result = asyncio.run(use_case.execute(command))

    assert result.status == "OK"
    assert result.indices == ["ndvi"]
    assert obs_repo.saved
