"""SQLAlchemy adapter for farm repository (domain port)."""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.domain.entities.farm import Farm
from app.domain.ports.farm_repository import IFarmRepository
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.models import Farm as FarmModel, AOI


class SQLAlchemyFarmRepository(IFarmRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: FarmModel, aoi_count: int = 0) -> Farm:
        return Farm(
            id=model.id,
            tenant_id=TenantId(value=model.tenant_id),
            name=model.name,
            timezone=model.timezone,
            created_at=model.created_at,
            updated_at=getattr(model, "updated_at", None),
            aoi_count=aoi_count,
        )

    async def find_by_id_and_tenant(self, farm_id: UUID, tenant_id: TenantId) -> Optional[Farm]:
        result = (
            self.db.query(FarmModel, func.count(AOI.id).label("aoi_count"))
            .outerjoin(AOI, (AOI.farm_id == FarmModel.id) & (AOI.status == "ACTIVE"))
            .filter(FarmModel.id == farm_id, FarmModel.tenant_id == tenant_id.value)
            .group_by(FarmModel.id)
            .first()
        )
        if not result:
            return None
        model, count = result
        return self._to_entity(model, aoi_count=count)

    async def find_all_by_tenant(self, tenant_id: TenantId) -> List[Farm]:
        result = (
            self.db.query(FarmModel, func.count(AOI.id).label("aoi_count"))
            .outerjoin(AOI, (AOI.farm_id == FarmModel.id) & (AOI.status == "ACTIVE"))
            .filter(FarmModel.tenant_id == tenant_id.value)
            .group_by(FarmModel.id)
            .order_by(FarmModel.created_at.desc())
            .all()
        )

        farms: List[Farm] = []
        for model, count in result:
            farms.append(self._to_entity(model, aoi_count=count))
        return farms

    async def create(self, farm: Farm) -> Farm:
        model = FarmModel(
            id=farm.id,
            tenant_id=farm.tenant_id.value,
            name=farm.name,
            timezone=farm.timezone,
            created_at=farm.created_at,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model, aoi_count=getattr(farm, "aoi_count", 0))
