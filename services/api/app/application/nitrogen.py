"""Backward-compatible nitrogen use case wrapper."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.dtos.nitrogen import GetNitrogenStatusCommand
from app.application.use_cases.nitrogen import GetNitrogenStatusUseCase as _UseCase
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.nitrogen_repository import SQLAlchemyNitrogenRepository


class GetNitrogenStatusUseCase:
    def __init__(self, db: Session):
        self.repo = SQLAlchemyNitrogenRepository(db)

    def execute(self, tenant_id: str, aoi_id: str, base_url: str) -> dict:
        use_case = _UseCase(self.repo)
        result = use_case.execute(
            GetNitrogenStatusCommand(
                tenant_id=TenantId(value=UUID(tenant_id)),
                aoi_id=aoi_id,
                base_url=base_url,
            )
        )
        if not result:
            return {}

        return {
            "status": result.status,
            "confidence": result.confidence,
            "ndvi_mean": result.ndvi_mean,
            "ndre_mean": result.ndre_mean,
            "reci_mean": result.reci_mean,
            "recommendation": result.recommendation,
            "zone_map_url": result.zone_map_url,
        }
