from worker.application.dtos.alerts_week import AlertsWeekCommand
from worker.application.use_cases.alerts_week import AlertsWeekUseCase
from worker.domain.ports.alerts_provider import AlertRepository, AlertsObservationsRepository, TenantSettingsRepository
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


class FakeSettingsRepository(TenantSettingsRepository):
    def get_min_valid_pixel_ratio(self, *, tenant_id: str) -> float:
        return 0.15


class FakeObservationsRepository(AlertsObservationsRepository):
    def __init__(self, obs=None, prev=None, persistent=0):
        self._obs = obs
        self._prev = prev
        self._persistent = persistent

    def get_observation(self, *, tenant_id: str, aoi_id: str, year: int, week: int):
        return self._obs

    def get_previous_observation(self, *, tenant_id: str, aoi_id: str, year: int, week: int):
        return self._prev

    def count_persistent_anomalies(self, *, tenant_id: str, aoi_id: str, year: int, week: int) -> int:
        return self._persistent


class FakeAlertRepository(AlertRepository):
    def __init__(self):
        self.created = []

    def get_existing(self, *, tenant_id: str, aoi_id: str, year: int, week: int, alert_type: str):
        return None

    def update_alert(self, *, alert_id: str, severity: str, confidence: str, evidence: dict) -> None:
        return None

    def create_alert(self, *, tenant_id: str, aoi_id: str, year: int, week: int, alert_type: str, severity: str, confidence: str, evidence: dict) -> None:
        self.created.append(alert_type)


def test_alerts_week_no_observation():
    use_case = AlertsWeekUseCase(
        job_repo=FakeJobRepository(),
        settings_repo=FakeSettingsRepository(),
        observations_repo=FakeObservationsRepository(obs=None),
        alert_repo=FakeAlertRepository(),
    )

    command = AlertsWeekCommand(job_id="job-1", tenant_id="tenant", aoi_id="aoi", year=2025, week=1)
    result = use_case.execute(command)

    assert result.status == "NO_DATA"
    assert result.reason == "no_observation"


def test_alerts_week_creates_alerts():
    obs = {
        "status": "OK",
        "valid_pixel_ratio": 0.1,
        "ndvi_mean": 0.25,
        "ndvi_p10": 0.2,
        "anomaly": -0.1,
    }
    prev = {"ndvi_mean": 0.5}

    alert_repo = FakeAlertRepository()
    use_case = AlertsWeekUseCase(
        job_repo=FakeJobRepository(),
        settings_repo=FakeSettingsRepository(),
        observations_repo=FakeObservationsRepository(obs=obs, prev=prev, persistent=3),
        alert_repo=alert_repo,
    )

    command = AlertsWeekCommand(job_id="job-2", tenant_id="tenant", aoi_id="aoi", year=2025, week=1)
    result = use_case.execute(command)

    assert result.status == "OK"
    assert result.alerts_created >= 1
    assert "NO_DATA" in alert_repo.created
    assert "LOW_NDVI" in alert_repo.created
    assert "RAPID_DECLINE" in alert_repo.created
    assert "PERSISTENT_ANOMALY" in alert_repo.created
