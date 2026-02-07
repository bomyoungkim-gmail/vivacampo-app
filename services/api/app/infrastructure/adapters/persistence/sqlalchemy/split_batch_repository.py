"""SQLAlchemy adapter for split batch idempotency."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.split_batch_repository import ISplitBatchRepository
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemySplitBatchRepository(ISplitBatchRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    async def get_by_key(self, tenant_id: TenantId, idempotency_key: str) -> list[UUID] | None:
        sql = """
            SELECT created_ids
            FROM split_batches
            WHERE tenant_id = :tenant_id AND idempotency_key = :idempotency_key
        """
        row = self._execute_query(
            sql,
            {"tenant_id": str(tenant_id.value), "idempotency_key": idempotency_key},
            fetch_one=True,
        )
        if not row:
            return None
        return [UUID(value) for value in row["created_ids"]]

    async def create(
        self,
        tenant_id: TenantId,
        parent_aoi_id: UUID,
        idempotency_key: str,
        created_ids: list[UUID],
    ) -> None:
        sql = """
            INSERT INTO split_batches (tenant_id, parent_aoi_id, idempotency_key, created_ids)
            VALUES (:tenant_id, :parent_aoi_id, :idempotency_key, :created_ids)
            ON CONFLICT (tenant_id, idempotency_key) DO NOTHING
        """
        self.db.execute(
            text(sql),
            {
                "tenant_id": str(tenant_id.value),
                "parent_aoi_id": str(parent_aoi_id),
                "idempotency_key": idempotency_key,
                "created_ids": [str(value) for value in created_ids],
            },
        )
        self.db.commit()
