import asyncio
from datetime import date

from worker.application.dtos.backfill import BackfillCommand
from worker.application.use_cases.backfill import BackfillUseCase
from worker.domain.ports.job_repository import JobQueue, JobRepository, SeasonRepository


class FakeJobRepository(JobRepository):
    def __init__(self) -> None:
        self.jobs = {}
        self.status_updates = []

    def mark_status(self, job_id: str, status: str, error_message: str | None = None) -> None:
        self.status_updates.append((job_id, status, error_message))

    def upsert_job(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        job_type: str,
        job_key: str,
        payload: dict,
    ) -> str | None:
        if job_key in self.jobs:
            return self.jobs[job_key]
        job_id = str(len(self.jobs) + 1)
        self.jobs[job_key] = job_id
        return job_id

    def commit(self) -> None:
        return None


class FakeSeasonRepository(SeasonRepository):
    def __init__(self, has_season: bool) -> None:
        self._has_season = has_season

    def has_season(self, tenant_id: str, aoi_id: str) -> bool:
        return self._has_season


class FakeJobQueue(JobQueue):
    def __init__(self) -> None:
        self.messages = []

    def enqueue(self, *, job_id: str, job_type: str, payload: dict) -> None:
        self.messages.append((job_id, job_type, payload))


def _run(command: BackfillCommand, has_season: bool) -> tuple[dict, list]:
    repo = FakeJobRepository()
    queue = FakeJobQueue()
    use_case = BackfillUseCase(repo, FakeSeasonRepository(has_season), queue)
    result = asyncio.run(use_case.execute(command))
    return result.model_dump(), queue.messages


def test_backfill_use_case_without_signals():
    command = BackfillCommand(
        job_id="job-1",
        tenant_id="tenant",
        aoi_id="aoi",
        from_date=date(2025, 1, 1),
        to_date=date(2025, 1, 15),
        pipeline_version="v1",
        signals_enabled=False,
    )

    result, messages = _run(command, has_season=True)

    assert result["weeks_processed"] == 3
    assert result["jobs_created"]["PROCESS_WEEK"] == 3
    assert result["jobs_created"]["PROCESS_RADAR_WEEK"] == 3
    assert result["jobs_created"]["ALERTS_WEEK"] == 3
    assert result["jobs_created"]["FORECAST_WEEK"] == 3
    assert result["jobs_created"]["PROCESS_WEATHER"] == 1
    assert result["jobs_created"]["PROCESS_TOPOGRAPHY"] == 1
    assert result["jobs_created"]["SIGNALS_WEEK"] == 0
    assert result["total_jobs"] == 14
    assert len(messages) == 14


def test_backfill_use_case_with_signals():
    command = BackfillCommand(
        job_id="job-2",
        tenant_id="tenant",
        aoi_id="aoi",
        from_date=date(2025, 1, 1),
        to_date=date(2025, 1, 15),
        pipeline_version="v1",
        signals_enabled=True,
    )

    result, messages = _run(command, has_season=False)

    assert result["weeks_processed"] == 3
    assert result["jobs_created"]["SIGNALS_WEEK"] == 3
    assert result["jobs_created"]["FORECAST_WEEK"] == 0
    assert result["total_jobs"] == 14
    assert len(messages) == 14
