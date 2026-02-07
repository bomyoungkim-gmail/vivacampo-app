import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.application.dtos.jobs import (
    CancelJobCommand,
    GetJobCommand,
    ListJobRunsCommand,
    ListJobsCommand,
    RetryJobCommand,
)
from app.application.use_cases.jobs import (
    CancelJobUseCase,
    GetJobUseCase,
    ListJobRunsUseCase,
    ListJobsUseCase,
    RetryJobUseCase,
)
from app.domain.ports.job_repository import IJobRepository
from app.domain.value_objects.tenant_id import TenantId


class _StubJobRepo(IJobRepository):
    def __init__(self):
        self.jobs = []

    async def list_jobs(self, tenant_id, aoi_id=None, job_type=None, status=None, limit=50):
        return self.jobs

    async def get_job(self, tenant_id, job_id):
        for job in self.jobs:
            if job["id"] == job_id:
                return job
        return None

    async def list_runs(self, tenant_id, job_id, limit=10):
        if not any(job["id"] == job_id for job in self.jobs):
            return [], False
        return [
            {
                "id": uuid4(),
                "job_id": job_id,
                "attempt": 1,
                "status": "DONE",
                "metrics": None,
                "error": None,
                "started_at": datetime.now(timezone.utc),
                "finished_at": datetime.now(timezone.utc),
            }
        ], True

    async def update_status(self, tenant_id, job_id, status):
        for job in self.jobs:
            if job["id"] == job_id:
                job["status"] = status
                return True
        return False

    async def create_backfill_job(self, tenant_id, aoi_id, job_key, payload_json):
        job_id = uuid4()
        self.jobs.append(
            {
                "id": job_id,
                "aoi_id": aoi_id,
                "job_type": "BACKFILL",
                "status": "PENDING",
                "payload": payload_json,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        return job_id

    async def create_weather_sync_job(self, tenant_id, aoi_id, job_key, payload_json):
        job_id = uuid4()
        self.jobs.append(
            {
                "id": job_id,
                "aoi_id": aoi_id,
                "job_type": "PROCESS_WEATHER",
                "status": "PENDING",
                "payload": payload_json,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        return job_id

    async def latest_status_by_aois(self, tenant_id, aoi_ids):
        return []

    async def create_job(self, tenant_id, aoi_id, job_type, job_key, payload_json):
        job_id = uuid4()
        self.jobs.append(
            {
                "id": job_id,
                "aoi_id": aoi_id,
                "job_type": job_type,
                "status": "PENDING",
                "payload": payload_json,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )
        return job_id


def _job(job_id, status="FAILED"):
    return {
        "id": job_id,
        "aoi_id": uuid4(),
        "job_type": "BACKFILL",
        "status": status,
        "payload": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def test_list_jobs_use_case():
    repo = _StubJobRepo()
    job_id = uuid4()
    repo.jobs.append(_job(job_id))
    use_case = ListJobsUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(ListJobsCommand(tenant_id=tenant_id))

    results = asyncio.run(run())
    assert len(results) == 1
    assert results[0].id == job_id


def test_get_job_use_case():
    repo = _StubJobRepo()
    job_id = uuid4()
    repo.jobs.append(_job(job_id))
    use_case = GetJobUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(GetJobCommand(tenant_id=tenant_id, job_id=job_id))

    result = asyncio.run(run())
    assert result is not None
    assert result.id == job_id


def test_list_job_runs_use_case():
    repo = _StubJobRepo()
    job_id = uuid4()
    repo.jobs.append(_job(job_id))
    use_case = ListJobRunsUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(ListJobRunsCommand(tenant_id=tenant_id, job_id=job_id))

    runs, job_exists = asyncio.run(run())
    assert job_exists is True
    assert len(runs) == 1


def test_retry_job_use_case():
    repo = _StubJobRepo()
    job_id = uuid4()
    repo.jobs.append(_job(job_id, status="FAILED"))
    use_case = RetryJobUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(RetryJobCommand(tenant_id=tenant_id, job_id=job_id))

    ok = asyncio.run(run())
    assert ok is True
    assert repo.jobs[0]["status"] == "PENDING"


def test_cancel_job_use_case():
    repo = _StubJobRepo()
    job_id = uuid4()
    repo.jobs.append(_job(job_id, status="RUNNING"))
    use_case = CancelJobUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(CancelJobCommand(tenant_id=tenant_id, job_id=job_id))

    ok = asyncio.run(run())
    assert ok is True
    assert repo.jobs[0]["status"] == "CANCELLED"
