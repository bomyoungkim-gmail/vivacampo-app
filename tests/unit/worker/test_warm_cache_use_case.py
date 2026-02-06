import asyncio

from worker.application.dtos.warm_cache import WarmCacheCommand
from worker.application.use_cases.warm_cache import WarmCacheUseCase
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.warm_cache_provider import AoiBoundsRepository, TileWarmClient


class FakeJobRepository(JobRepository):
    def __init__(self) -> None:
        self.status = []

    def mark_status(self, job_id: str, status: str, error_message: str | None = None) -> None:
        self.status.append((job_id, status, error_message))

    def upsert_job(self, *, tenant_id: str, aoi_id: str, job_type: str, job_key: str, payload: dict):
        return None

    def commit(self) -> None:
        return None


class FakeBoundsRepository(AoiBoundsRepository):
    def __init__(self, bounds):
        self._bounds = bounds

    def get_bounds(self, *, tenant_id: str, aoi_id: str):
        return self._bounds


class FakeTileWarmClient(TileWarmClient):
    async def fetch_tile(self, *, aoi_id: str, z: int, x: int, y: int, index: str) -> bool:
        return True


def test_warm_cache_not_found():
    use_case = WarmCacheUseCase(
        job_repo=FakeJobRepository(),
        bounds_repo=FakeBoundsRepository(None),
        tile_client=FakeTileWarmClient(),
    )

    command = WarmCacheCommand(job_id="job-1", tenant_id="tenant", aoi_id="aoi")
    result = asyncio.run(use_case.execute(command))

    assert result.status == "NOT_FOUND"
    assert result.reason == "aoi_not_found"


def test_warm_cache_success():
    use_case = WarmCacheUseCase(
        job_repo=FakeJobRepository(),
        bounds_repo=FakeBoundsRepository((-50.0, -10.0, -49.0, -9.0)),
        tile_client=FakeTileWarmClient(),
    )

    command = WarmCacheCommand(job_id="job-2", tenant_id="tenant", aoi_id="aoi", indices=["ndvi"], zoom_levels=[10])
    result = asyncio.run(use_case.execute(command))

    assert result.status == "OK"
    assert result.stats["total_tiles"] >= 1
