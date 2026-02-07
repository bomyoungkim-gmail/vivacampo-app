"""AI assistant use cases."""
from __future__ import annotations

from app.application.decorators import require_tenant
from app.application.dtos.ai_assistant import (
    CreateThreadCommand,
    GetApprovalThreadCommand,
    GetMessagesCommand,
    ListApprovalsCommand,
    ListThreadsCommand,
)
from app.domain.ports.ai_assistant_repository import IAiAssistantRepository


class CreateThreadUseCase:
    def __init__(self, repo: IAiAssistantRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: CreateThreadCommand) -> dict:
        return await self.repo.create_thread(
            tenant_id=command.tenant_id,
            aoi_id=command.aoi_id,
            signal_id=command.signal_id,
            membership_id=command.membership_id,
            provider=command.provider,
            model=command.model,
        )


class ListThreadsUseCase:
    def __init__(self, repo: IAiAssistantRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: ListThreadsCommand) -> list[dict]:
        return await self.repo.list_threads(command.tenant_id, command.limit)


class GetMessagesUseCase:
    def __init__(self, repo: IAiAssistantRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: GetMessagesCommand) -> list[dict]:
        state_json = await self.repo.get_latest_state(command.tenant_id, command.thread_id)
        if not state_json:
            return []
        import json

        state = json.loads(state_json)
        messages = state.get("messages", [])
        return [m for m in messages if m.get("role") != "system"]


class ListApprovalsUseCase:
    def __init__(self, repo: IAiAssistantRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: ListApprovalsCommand) -> list[dict]:
        return await self.repo.list_approvals(command.tenant_id, command.pending_only)


class GetApprovalThreadUseCase:
    def __init__(self, repo: IAiAssistantRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: GetApprovalThreadCommand):
        return await self.repo.get_approval_thread_id(command.tenant_id, command.approval_id)
