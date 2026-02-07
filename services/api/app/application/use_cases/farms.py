"""Farm use cases using domain ports and DTOs."""
from __future__ import annotations

from typing import List

from app.application.decorators import require_tenant
from app.application.dtos.farms import (
    CreateFarmCommand,
    DeleteFarmCommand,
    ListFarmsCommand,
    UpdateFarmCommand,
    FarmResult,
)
from app.domain.entities.farm import Farm
from app.domain.entities.user import UserRole
from app.domain.ports.farm_repository import IFarmRepository


class CreateFarmUseCase:
    def __init__(self, farm_repo: IFarmRepository):
        self.farm_repo = farm_repo

    @require_tenant
    async def execute(self, command: CreateFarmCommand) -> FarmResult:
        if command.user_role == UserRole.VIEWER:
            raise ValueError("FORBIDDEN")
        farm = Farm(
            tenant_id=command.tenant_id,
            created_by_user_id=command.user_id,
            name=command.name,
            timezone=command.timezone,
        )
        created = await self.farm_repo.create(farm)
        return FarmResult(
            id=created.id,
            tenant_id=created.tenant_id.value,
            created_by_user_id=created.created_by_user_id,
            name=created.name,
            timezone=created.timezone,
            aoi_count=created.aoi_count,
            created_at=created.created_at,
        )


class ListFarmsUseCase:
    def __init__(self, farm_repo: IFarmRepository):
        self.farm_repo = farm_repo

    @require_tenant
    async def execute(self, command: ListFarmsCommand) -> List[FarmResult]:
        farms = await self.farm_repo.find_all_by_tenant(command.tenant_id)
        return [
            FarmResult(
                id=farm.id,
                tenant_id=farm.tenant_id.value,
                created_by_user_id=farm.created_by_user_id,
                name=farm.name,
                timezone=farm.timezone,
                aoi_count=farm.aoi_count,
                created_at=farm.created_at,
            )
            for farm in farms
        ]


class UpdateFarmUseCase:
    def __init__(self, farm_repo: IFarmRepository):
        self.farm_repo = farm_repo

    @require_tenant
    async def execute(self, command: UpdateFarmCommand) -> FarmResult:
        farm = await self.farm_repo.find_by_id_and_tenant(command.farm_id, command.tenant_id)
        if not farm:
            raise ValueError("FARM_NOT_FOUND")
        if not farm.can_edit(command.user_id, command.user_role):
            raise ValueError("FORBIDDEN")

        if command.name:
            farm.update_name(command.name)
        if command.timezone:
            farm.timezone = command.timezone

        updated = await self.farm_repo.update(farm)
        return FarmResult(
            id=updated.id,
            tenant_id=updated.tenant_id.value,
            created_by_user_id=updated.created_by_user_id,
            name=updated.name,
            timezone=updated.timezone,
            aoi_count=updated.aoi_count,
            created_at=updated.created_at,
        )


class DeleteFarmUseCase:
    def __init__(self, farm_repo: IFarmRepository):
        self.farm_repo = farm_repo

    @require_tenant
    async def execute(self, command: DeleteFarmCommand) -> None:
        farm = await self.farm_repo.find_by_id_and_tenant(command.farm_id, command.tenant_id)
        if not farm:
            raise ValueError("FARM_NOT_FOUND")
        if not farm.can_edit(command.user_id, command.user_role):
            raise ValueError("FORBIDDEN")
        await self.farm_repo.delete(command.farm_id, command.tenant_id)
