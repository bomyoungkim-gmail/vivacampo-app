from worker.application.dtos.detect_harvest import DetectHarvestCommand
from worker.application.use_cases.detect_harvest import DetectHarvestUseCase
from worker.domain.ports.harvest_provider import HarvestSignalRepository, RadarMetricsRepository
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


class FakeRadarMetricsRepository(RadarMetricsRepository):
    def __init__(self, current=None, previous=None):
        self._current = current
        self._previous = previous

    def get_rvi_mean(self, *, tenant_id: str, aoi_id: str, year: int, week: int):
        if (year, week) == (2025, 1):
            return self._current
        return self._previous


class FakeHarvestSignalRepository(HarvestSignalRepository):
    def __init__(self):
        self.created = 0

    def create_signal(self, *, tenant_id: str, aoi_id: str, year: int, week: int, rvi_current: float, rvi_previous: float) -> None:
        self.created += 1


def test_detect_harvest_no_data():
    use_case = DetectHarvestUseCase(
        job_repo=FakeJobRepository(),
        radar_repo=FakeRadarMetricsRepository(current=None, previous=None),
        signal_repo=FakeHarvestSignalRepository(),
    )

    command = DetectHarvestCommand(job_id="job-1", tenant_id="tenant", aoi_id="aoi", year=2025, week=1)
    result = use_case.execute(command)

    assert result.status == "NO_DATA"
    assert result.detected is False


def test_detect_harvest_detected():
    signal_repo = FakeHarvestSignalRepository()
    use_case = DetectHarvestUseCase(
        job_repo=FakeJobRepository(),
        radar_repo=FakeRadarMetricsRepository(current=0.1, previous=0.6),
        signal_repo=signal_repo,
    )

    command = DetectHarvestCommand(job_id="job-2", tenant_id="tenant", aoi_id="aoi", year=2025, week=1)
    result = use_case.execute(command)

    assert result.status == "OK"
    assert result.detected is True
    assert signal_repo.created == 1
