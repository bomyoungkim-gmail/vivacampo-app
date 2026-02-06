import pytest

pytest.importorskip("mercantile")

from worker.application.dtos.create_mosaic import CreateMosaicCommand
from worker.application.use_cases.create_mosaic import CreateMosaicUseCase
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.mosaic_provider import MosaicProvider, MosaicRegistry, MosaicStorage


class FakeJobRepository(JobRepository):
    def __init__(self) -> None:
        self.status = []

    def mark_status(self, job_id: str, status: str, error_message: str | None = None) -> None:
        self.status.append((job_id, status, error_message))

    def upsert_job(self, *, tenant_id: str, aoi_id: str, job_type: str, job_key: str, payload: dict):
        return None

    def commit(self) -> None:
        return None


class FakeProvider(MosaicProvider):
    def __init__(self, scenes):
        self._scenes = scenes

    def search_scenes(
        self,
        *,
        collection: str,
        start_date: str,
        end_date: str,
        bbox: list[float],
        max_cloud_cover: float,
        max_items: int,
    ):
        return self._scenes


class FakeStorage(MosaicStorage):
    def __init__(self):
        self.saved = []

    def save_json(self, *, key: str, payload: dict) -> str:
        self.saved.append((key, payload))
        return f"s3://bucket/{key}"

    def exists(self, *, key: str) -> bool:
        return False


class FakeRegistry(MosaicRegistry):
    def __init__(self):
        self.saved = []

    def save_record(self, *, collection: str, year: int, week: int, url: str, scene_count: int) -> None:
        self.saved.append((collection, year, week, url, scene_count))


class FakeLink:
    def __init__(self, href: str):
        self.rel = "self"
        self.href = href


class FakeItem:
    def __init__(self, item_id: str, bbox: list[float]):
        self.id = item_id
        self.bbox = bbox
        self.links = [FakeLink(f"https://example.com/{item_id}")]


def test_create_mosaic_no_scenes():
    repo = FakeJobRepository()
    storage = FakeStorage()
    registry = FakeRegistry()
    use_case = CreateMosaicUseCase(repo, FakeProvider([]), storage, registry)

    command = CreateMosaicCommand(job_id="job-1", year=2025, week=1)
    result = use_case.execute(command)

    assert result.status == "NO_DATA"
    assert result.scene_count == 0
    assert storage.saved
    assert registry.saved == []


def test_create_mosaic_with_scene():
    repo = FakeJobRepository()
    storage = FakeStorage()
    registry = FakeRegistry()
    scenes = [FakeItem("scene-1", [-10.0, -10.0, -9.0, -9.0])]
    use_case = CreateMosaicUseCase(repo, FakeProvider(scenes), storage, registry)

    command = CreateMosaicCommand(job_id="job-2", year=2025, week=1)
    result = use_case.execute(command)

    assert result.status == "OK"
    assert result.scene_count == 1
    assert result.tile_count is not None
    assert storage.saved
    assert registry.saved
