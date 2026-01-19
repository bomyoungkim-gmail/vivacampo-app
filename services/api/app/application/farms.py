from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.infrastructure.repositories import FarmRepository
from app.infrastructure.models import Farm


class CreateFarmUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repo = FarmRepository(db)
    
    def execute(self, tenant_id: UUID, name: str, timezone: str) -> Farm:
        """
        Create a new farm for the tenant.
        """
        farm = self.farm_repo.create(
            tenant_id=tenant_id,
            name=name,
            timezone=timezone
        )
        return farm


class ListFarmsUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.farm_repo = FarmRepository(db)
    
    def execute(self, tenant_id: UUID) -> List[Farm]:
        """
        List all farms for the tenant.
        """
        return self.farm_repo.list_by_tenant(tenant_id)
