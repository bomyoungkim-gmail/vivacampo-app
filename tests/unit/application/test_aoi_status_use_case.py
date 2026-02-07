import asyncio
from uuid import uuid4

from app.application.dtos.aois import AoiStatusCommand
from app.application.use_cases.aois import AoiStatusUseCase
from app.domain.ports.job_repository import IJobRepository
from app.domain.value_objects.tenant_id import TenantId


class _StubJobRepo(IJobRepository):
    async def list_jobs(self, tenant_id, aoi_id=None, job_type=None, status=None, limit=50):
        raise NotImplementedError

    async def get_job(self, tenant_id, job_id):
        raise NotImplementedError

    async def list_runs(self, tenant_id, job_id, limit=10):
        raise NotImplementedError

    async def update_status(self, tenant_id, job_id, status):
        raise NotImplementedError

    async def create_backfill_job(self, tenant_id, aoi_id, job_key, payload_json):
        raise NotImplementedError

    async def create_weather_sync_job(self, tenant_id, aoi_id, job_key, payload_json):
        raise NotImplementedError

    async def create_job(self, tenant_id, aoi_id, job_type, job_key, payload_json):
        raise NotImplementedError

    async def latest_status_by_aois(self, tenant_id, aoi_ids):
        return [
            {"aoi_id": aoi_ids[0], "status": "RUNNING", "job_type": "BACKFILL", "updated_at": None},
        ]


def test_aoi_status_use_case_returns_processing():
    repo = _StubJobRepo()
    use_case = AoiStatusUseCase(repo)
    tenant_id = TenantId(value=uuid4())
    aoi_ids = [uuid4(), uuid4()]

    async def run():
        return await use_case.execute(AoiStatusCommand(tenant_id=tenant_id, aoi_ids=aoi_ids))

    result = asyncio.run(run())
    assert len(result.items) == 2
    assert result.items[0].is_processing is True
    assert result.items[1].is_processing is False
