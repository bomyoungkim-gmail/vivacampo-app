from worker.application.dtos.forecast_week import ForecastWeekCommand
from worker.application.use_cases.forecast_week import ForecastWeekUseCase
from worker.domain.ports.forecast_provider import (
    ForecastObservationsRepository,
    SeasonRepository,
    YieldForecastRepository,
)
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


class FakeSeasonRepository(SeasonRepository):
    def __init__(self, season: dict | None):
        self._season = season

    def get_active_season(self, *, tenant_id: str, aoi_id: str) -> dict | None:
        return self._season


class FakeObservationsRepository(ForecastObservationsRepository):
    def __init__(self, observations: list[dict]):
        self._observations = observations

    def list_observations(self, *, tenant_id: str, aoi_id: str) -> list[dict]:
        return self._observations


class FakeYieldForecastRepository(YieldForecastRepository):
    def __init__(self, yields: list[float]):
        self._yields = yields
        self.saved = []

    def list_historical_yields(self, *, tenant_id: str, aoi_id: str, limit: int) -> list[float]:
        return self._yields[:limit]

    def save_forecast(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        season_id: str,
        year: int,
        week: int,
        estimated_yield: float,
        confidence: str,
        evidence: dict,
        method: str,
        model_version: str,
    ) -> None:
        self.saved.append((estimated_yield, confidence, evidence, method, model_version))


def test_forecast_week_no_season():
    use_case = ForecastWeekUseCase(
        job_repo=FakeJobRepository(),
        season_repo=FakeSeasonRepository(None),
        observations_repo=FakeObservationsRepository([]),
        forecast_repo=FakeYieldForecastRepository([]),
    )

    command = ForecastWeekCommand(job_id="job-1", tenant_id="tenant", aoi_id="aoi", year=2025, week=1)
    result = use_case.execute(command)

    assert result.status == "NO_DATA"
    assert result.reason == "no_active_season"


def test_forecast_week_insufficient_history():
    use_case = ForecastWeekUseCase(
        job_repo=FakeJobRepository(),
        season_repo=FakeSeasonRepository({"id": "season", "crop_type": "CORN"}),
        observations_repo=FakeObservationsRepository([{ "year": 2025, "week": 1, "ndvi_mean": 0.5 }]),
        forecast_repo=FakeYieldForecastRepository([]),
    )

    command = ForecastWeekCommand(job_id="job-2", tenant_id="tenant", aoi_id="aoi", year=2025, week=1)
    result = use_case.execute(command)

    assert result.status == "NO_DATA"
    assert result.reason == "insufficient_history"


def test_forecast_week_success():
    observations = [
        {"year": 2025, "week": 1, "ndvi_mean": 0.5},
        {"year": 2025, "week": 2, "ndvi_mean": 0.6},
        {"year": 2025, "week": 3, "ndvi_mean": 0.7},
        {"year": 2025, "week": 4, "ndvi_mean": 0.6},
    ]
    forecast_repo = FakeYieldForecastRepository([8000, 8200])
    use_case = ForecastWeekUseCase(
        job_repo=FakeJobRepository(),
        season_repo=FakeSeasonRepository({"id": "season", "crop_type": "CORN"}),
        observations_repo=FakeObservationsRepository(observations),
        forecast_repo=forecast_repo,
    )

    command = ForecastWeekCommand(job_id="job-3", tenant_id="tenant", aoi_id="aoi", year=2025, week=4)
    result = use_case.execute(command)

    assert result.status == "OK"
    assert result.estimated_yield_kg_ha is not None
    assert forecast_repo.saved
