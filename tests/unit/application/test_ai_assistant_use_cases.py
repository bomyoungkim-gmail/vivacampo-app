import asyncio
from uuid import uuid4

from app.application.dtos.ai_assistant import GetMessagesCommand, ListThreadsCommand
from app.application.use_cases.ai_assistant import GetMessagesUseCase, ListThreadsUseCase
from app.domain.value_objects.tenant_id import TenantId


class _StubAiRepo:
    def __init__(self):
        self.threads = [{"id": uuid4(), "provider": "openai", "model": "gpt", "status": "OPEN", "created_at": "now", "aoi_id": None, "signal_id": None}]

    async def list_threads(self, tenant_id, limit=50):
        return self.threads

    async def get_latest_state(self, tenant_id, thread_id):
        return '{"messages": [{"role": "user", "content": "hi"}, {"role": "system", "content": "ignore"}]}'


def test_list_threads_use_case():
    repo = _StubAiRepo()
    use_case = ListThreadsUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(ListThreadsCommand(tenant_id=tenant_id))

    result = asyncio.run(run())
    assert len(result) == 1


def test_get_messages_use_case():
    repo = _StubAiRepo()
    use_case = GetMessagesUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(GetMessagesCommand(tenant_id=tenant_id, thread_id=uuid4()))

    result = asyncio.run(run())
    assert len(result) == 1
    assert result[0]["role"] == "user"
