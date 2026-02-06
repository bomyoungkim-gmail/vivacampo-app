"""AOI use cases using domain ports and DTOs."""
from __future__ import annotations

from typing import List

from app.application.dtos.aois import CreateAoiCommand, ListAoisCommand, AoiResult
from app.domain.entities.aoi import AOI
from app.domain.ports.aoi_repository import IAOIRepository
from app.domain.value_objects.area_hectares import AreaHectares
from app.domain.value_objects.geometry_wkt import GeometryWkt


class CreateAoiUseCase:
    def __init__(self, aoi_repo: IAOIRepository):
        self.aoi_repo = aoi_repo

    async def execute(self, command: CreateAoiCommand) -> AoiResult:
        aoi = AOI(
            tenant_id=command.tenant_id,
            farm_id=command.farm_id,
            name=command.name,
            use_type=command.use_type,
            geometry_wkt=GeometryWkt(value=command.geometry_wkt),
            area_hectares=AreaHectares(value=1.0),
        )
        created = await self.aoi_repo.create(aoi)
        return AoiResult(
            id=created.id,
            tenant_id=created.tenant_id.value,
            farm_id=created.farm_id,
            name=created.name,
            use_type=created.use_type,
            status=created.status,
            area_ha=created.area_hectares.value,
            geometry=created.geometry_wkt.value,
            created_at=created.created_at,
        )


class ListAoisUseCase:
    def __init__(self, aoi_repo: IAOIRepository):
        self.aoi_repo = aoi_repo

    async def execute(self, command: ListAoisCommand) -> List[AoiResult]:
        aois = await self.aoi_repo.list_by_tenant(
            tenant_id=command.tenant_id,
            farm_id=command.farm_id,
            status=command.status,
            limit=command.limit,
        )
        return [
            AoiResult(
                id=aoi.id,
                tenant_id=aoi.tenant_id.value,
                farm_id=aoi.farm_id,
                name=aoi.name,
                use_type=aoi.use_type,
                status=aoi.status,
                area_ha=aoi.area_hectares.value,
                geometry=aoi.geometry_wkt.value,
                created_at=aoi.created_at,
            )
            for aoi in aois
        ]
