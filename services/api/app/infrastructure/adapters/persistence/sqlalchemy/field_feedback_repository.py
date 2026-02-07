"""SQLAlchemy adapter for field feedback."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.field_feedback_repository import IFieldFeedbackRepository
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemyFieldFeedbackRepository(IFieldFeedbackRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    async def create(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        feedback_type: str,
        message: str,
        created_by_membership_id: UUID | None,
    ) -> UUID:
        sql = text(
            """
            INSERT INTO field_feedback (
                tenant_id, aoi_id, feedback_type, message, created_by_membership_id
            )
            VALUES (:tenant_id, :aoi_id, :feedback_type, :message, :created_by_membership_id)
            RETURNING id
            """
        )
        result = self.db.execute(
            sql,
            {
                "tenant_id": str(tenant_id.value),
                "aoi_id": str(aoi_id),
                "feedback_type": feedback_type,
                "message": message,
                "created_by_membership_id": str(created_by_membership_id) if created_by_membership_id else None,
            },
        )
        self.db.commit()
        return result.fetchone()[0]
