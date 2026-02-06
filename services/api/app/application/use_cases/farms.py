"""Farm use cases using domain ports and DTOs."""
from __future__ import annotations

from typing import List

from app.application.dtos.farms import CreateFarmCommand, ListFarmsCommand, FarmResult
from app.domain.entities.farm import Farm
from app.domain.ports.farm_repository import IFarmRepository


class CreateFarmUseCase:
    def __init__(self, farm_repo: IFarmRepository):
        self.farm_repo = farm_repo

    async def execute(self, command: CreateFarmCommand) -> FarmResult:
        farm = Farm(
            tenant_id=command.tenant_id,
            name=command.name,
            timezone=command.timezone,
        )
        created = await self.farm_repo.create(farm)
        return FarmResult(
            id=created.id,
            tenant_id=created.tenant_id.value,
            name=created.name,
            timezone=created.timezone,
            aoi_count=created.aoi_count,
            created_at=created.created_at,
        )


class ListFarmsUseCase:
    def __init__(self, farm_repo: IFarmRepository):
        self.farm_repo = farm_repo

    async def execute(self, command: ListFarmsCommand) -> List[FarmResult]:
        farms = await self.farm_repo.find_all_by_tenant(command.tenant_id)
        return [
            FarmResult(
                id=farm.id,
                tenant_id=farm.tenant_id.value,
                name=farm.name,
                timezone=farm.timezone,
                aoi_count=farm.aoi_count,
                created_at=farm.created_at,
            )
            for farm in farms
        ]
