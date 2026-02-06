"""Signal use cases using ports and DTOs."""
from __future__ import annotations

import base64
from typing import Optional

from app.application.dtos.signals import (
    AckSignalCommand,
    GetSignalCommand,
    ListSignalsCommand,
    ListSignalsResult,
    SignalResult,
)
from app.domain.ports.signal_repository import ISignalRepository


def _encode_cursor(signal_id, created_at) -> str:
    cursor_str = f"{signal_id}:{created_at}"
    return base64.b64encode(cursor_str.encode()).decode()


def _decode_cursor(cursor: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not cursor:
        return None, None
    decoded = base64.b64decode(cursor).decode()
    cursor_id, cursor_created = decoded.split(":")
    return cursor_id, cursor_created


class ListSignalsUseCase:
    def __init__(self, repo: ISignalRepository):
        self.repo = repo

    async def execute(self, command: ListSignalsCommand) -> ListSignalsResult:
        cursor_id, cursor_created = _decode_cursor(command.cursor)
        signals, has_more = await self.repo.list_signals(
            tenant_id=command.tenant_id,
            status=command.status,
            signal_type=command.signal_type,
            aoi_id=command.aoi_id,
            farm_id=command.farm_id,
            cursor_id=cursor_id,
            cursor_created=cursor_created,
            limit=command.limit,
        )

        items = [SignalResult(**signal) for signal in signals]
        next_cursor = _encode_cursor(items[-1].id, items[-1].created_at) if has_more and items else None
        return ListSignalsResult(items=items, next_cursor=next_cursor)


class GetSignalUseCase:
    def __init__(self, repo: ISignalRepository):
        self.repo = repo

    async def execute(self, command: GetSignalCommand) -> SignalResult | None:
        signal = await self.repo.get_signal(command.tenant_id, command.signal_id)
        if not signal:
            return None
        return SignalResult(**signal)


class AckSignalUseCase:
    def __init__(self, repo: ISignalRepository):
        self.repo = repo

    async def execute(self, command: AckSignalCommand) -> bool:
        return await self.repo.acknowledge(command.tenant_id, command.signal_id)
