import asyncio

from worker.application.dtos.process_week import ProcessWeekCommand
from worker.application.use_cases.process_week import ProcessWeekUseCase
from worker.domain.ports.job_repository import JobRepository


class FakeJobRepository(JobRepository):
    def __init__(self) -> None:
        self.status = []

    def mark_status(self, job_id: str, status: str, error_message: str | None = None) -> None:
        self.status.append((job_id, status, error_message))

    def upsert_job(self, *, tenant_id: str, aoi_id: str, job_type: str, job_key: str, payload: dict):
        return None

    def commit(self) -> None:
        return None


class FakeDB:
    pass


def test_process_week_dynamic_marks_done():
    repo = FakeJobRepository()
    called = {}

    def dynamic(job_id: str, payload: dict, db):
        called["dynamic"] = True
        return {"status": "OK"}

    command = ProcessWeekCommand(
        job_id="job-1",
        tenant_id="tenant",
        aoi_id="aoi",
        year=2025,
        week=1,
        payload={"tenant_id": "tenant", "aoi_id": "aoi", "year": 2025, "week": 1},
        use_dynamic_tiling=True,
    )

    use_case = ProcessWeekUseCase(repo, dynamic)
    result = asyncio.run(use_case.execute(command, FakeDB()))

    assert called.get("dynamic") is True
    assert repo.status[0][1] == "RUNNING"
    assert repo.status[-1][1] == "DONE"
    assert result.status == "DONE"


def test_process_week_forces_dynamic_when_disabled():
    repo = FakeJobRepository()
    called = {}

    def dynamic(job_id: str, payload: dict, db):
        called["dynamic"] = True
        return {"status": "OK"}

    command = ProcessWeekCommand(
        job_id="job-2",
        tenant_id="tenant",
        aoi_id="aoi",
        year=2025,
        week=2,
        payload={"tenant_id": "tenant", "aoi_id": "aoi", "year": 2025, "week": 2},
        use_dynamic_tiling=False,
    )

    use_case = ProcessWeekUseCase(repo, dynamic)
    result = asyncio.run(use_case.execute(command, FakeDB()))

    assert called.get("dynamic") is True
    assert repo.status[0][1] == "RUNNING"
    assert result.status == "DONE"
