"""Radar use cases."""
from __future__ import annotations

from app.application.dtos.radar import RadarHistoryCommand
from app.domain.ports.radar_data_repository import IRadarDataRepository


class GetRadarHistoryUseCase:
    def __init__(self, repo: IRadarDataRepository):
        self.repo = repo

    async def execute(self, command: RadarHistoryCommand) -> list[dict]:
        return await self.repo.get_history(
            tenant_id=command.tenant_id,
            aoi_id=command.aoi_id,
            year=command.year,
            limit=command.limit,
        )
