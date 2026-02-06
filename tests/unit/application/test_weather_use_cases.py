import asyncio
from uuid import uuid4

from app.application.dtos.weather import WeatherHistoryCommand, WeatherSyncCommand
from app.application.use_cases.weather import GetWeatherHistoryUseCase, RequestWeatherSyncUseCase
from app.domain.value_objects.tenant_id import TenantId


class _StubWeatherRepo:
    def __init__(self, rows):
        self.rows = rows

    async def get_history(self, tenant_id, aoi_id, start_date=None, end_date=None, limit=365):
        return self.rows


class _StubJobRepo:
    def __init__(self):
        self.created = []

    async def create_weather_sync_job(self, tenant_id, aoi_id, job_key, payload_json):
        job_id = uuid4()
        self.created.append({"job_id": job_id, "job_key": job_key, "payload": payload_json})
        return job_id


class _StubQueue:
    def __init__(self):
        self.published = []

    async def publish(self, queue_name, message):
        self.published.append({"queue_name": queue_name, "message": message})


def test_get_weather_history_use_case():
    tenant_id = TenantId(value=uuid4())
    aoi_id = uuid4()
    rows = [{"date": "2025-01-01", "precip_sum": 10.0}]
    repo = _StubWeatherRepo(rows)
    use_case = GetWeatherHistoryUseCase(repo)

    async def run():
        return await use_case.execute(
            WeatherHistoryCommand(tenant_id=tenant_id, aoi_id=aoi_id, limit=10)
        )

    result = asyncio.run(run())
    assert result == rows


def test_request_weather_sync_use_case():
    tenant_id = TenantId(value=uuid4())
    aoi_id = uuid4()
    job_repo = _StubJobRepo()
    queue = _StubQueue()
    use_case = RequestWeatherSyncUseCase(job_repo=job_repo, queue=queue, queue_name="jobs")

    async def run():
        return await use_case.execute(WeatherSyncCommand(tenant_id=tenant_id, aoi_id=aoi_id))

    result = asyncio.run(run())
    assert result.status == "PENDING"
    assert len(job_repo.created) == 1
    assert len(queue.published) == 1
    assert queue.published[0]["queue_name"] == "jobs"
