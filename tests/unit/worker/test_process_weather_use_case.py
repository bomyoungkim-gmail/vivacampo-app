import asyncio
from datetime import date

from worker.application.dtos.process_weather import ProcessWeatherCommand
from worker.application.use_cases.process_weather import ProcessWeatherUseCase
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.weather_provider import AoiGeometryRepository, WeatherProvider, WeatherRepository


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


class FakeWeatherRepository(WeatherRepository):
    def __init__(self) -> None:
        self.saved = []

    def save_batch(self, *, tenant_id: str, aoi_id: str, records):
        self.saved = list(records)


class FakeWeatherProvider(WeatherProvider):
    async def fetch_history(self, *, lat: float, lon: float, start_date: date, end_date: date) -> list[dict]:
        return [
            {
                "date": "2025-01-01",
                "temp_max": 30,
                "temp_min": 20,
                "precip_sum": 1.5,
                "et0_fao": 2.0,
            },
            {
                "date": "2025-01-02",
                "temp_max": 0,
                "temp_min": 18,
                "precip_sum": 0,
                "et0_fao": 1.9,
            },
        ]


def _run(command: ProcessWeatherCommand):
    repo = FakeJobRepository()
    weather_repo = FakeWeatherRepository()
    use_case = ProcessWeatherUseCase(
        job_repo=repo,
        aoi_repo=FakeAoiGeometryRepository(),
        weather_repo=weather_repo,
        weather_provider=FakeWeatherProvider(),
    )
    result = asyncio.run(use_case.execute(command))
    return result, repo, weather_repo


def test_process_weather_use_case_saves_records():
    command = ProcessWeatherCommand(
        job_id="job-1",
        tenant_id="tenant",
        aoi_id="aoi",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
    )

    result, repo, weather_repo = _run(command)

    assert result.status == "DONE"
    assert result.records_saved == 2
    assert len(weather_repo.saved) == 2
    assert repo.status[0][1] == "RUNNING"
    assert repo.status[-1][1] == "DONE"


def test_process_weather_use_case_clamps_future_range():
    command = ProcessWeatherCommand(
        job_id="job-2",
        tenant_id="tenant",
        aoi_id="aoi",
        start_date=date(2099, 1, 1),
        end_date=date(2099, 1, 2),
    )

    result, repo, _ = _run(command)

    assert result.status == "DONE"
    assert result.clamped is True
    assert repo.status[-1][1] == "DONE"
