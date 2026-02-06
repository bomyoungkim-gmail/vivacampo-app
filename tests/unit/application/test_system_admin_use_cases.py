import asyncio
from uuid import uuid4

from app.application.dtos.system_admin import ListTenantsCommand, ReprocessMissingAoisCommand
from app.application.use_cases.system_admin import ListTenantsUseCase, ReprocessMissingAoisUseCase
from app.domain.value_objects.tenant_id import TenantId


class _StubSystemRepo:
    def __init__(self):
        self.tenants = [{"id": uuid4(), "name": "T1", "type": "PERSONAL", "status": "ACTIVE", "created_at": "now"}]
        self.missing = [{"id": uuid4(), "tenant_id": uuid4()}]

    async def list_tenants(self, tenant_type, limit):
        return self.tenants

    async def list_missing_aois(self, limit):
        return self.missing


class _StubJobRepo:
    def __init__(self):
        self.created = []

    async def create_backfill_job(self, tenant_id, aoi_id, job_key, payload_json):
        self.created.append((tenant_id, aoi_id))
        return uuid4()


class _StubQueue:
    def __init__(self):
        self.published = []

    async def publish(self, queue_name, message):
        self.published.append((queue_name, message))


def test_list_tenants_use_case():
    repo = _StubSystemRepo()
    use_case = ListTenantsUseCase(repo)

    async def run():
        return await use_case.execute(ListTenantsCommand())

    result = asyncio.run(run())
    assert len(result) == 1


def test_reprocess_missing_aois_use_case():
    repo = _StubSystemRepo()
    job_repo = _StubJobRepo()
    queue = _StubQueue()
    use_case = ReprocessMissingAoisUseCase(
        repo=repo,
        job_repo=job_repo,
        queue=queue,
        queue_name="jobs",
        pipeline_version="v1",
    )

    async def run():
        return await use_case.execute(ReprocessMissingAoisCommand(days=7, limit=10))

    result = asyncio.run(run())
    assert result["queued"] == 1
    assert len(queue.published) == 1
