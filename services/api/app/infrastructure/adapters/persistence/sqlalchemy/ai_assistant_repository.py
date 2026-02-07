"""SQLAlchemy adapter for AI assistant operations."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.ai_assistant_repository import IAiAssistantRepository
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemyAiAssistantRepository(IAiAssistantRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    async def create_thread(
        self,
        tenant_id: TenantId,
        aoi_id: Optional[UUID],
        signal_id: Optional[UUID],
        membership_id: UUID,
        provider: str,
        model: str,
    ) -> dict:
        sql = """
            INSERT INTO ai_assistant_threads
            (tenant_id, aoi_id, signal_id, created_by_membership_id, provider, model, status)
            VALUES (:tenant_id, :aoi_id, :signal_id, :membership_id, :provider, :model, 'OPEN')
            RETURNING id, created_at
            """
        result = self.db.execute(
            text(sql),
            {
                "tenant_id": str(tenant_id.value),
                "aoi_id": str(aoi_id) if aoi_id else None,
                "signal_id": str(signal_id) if signal_id else None,
                "membership_id": str(membership_id),
                "provider": provider,
                "model": model,
            },
        )
        self.db.commit()
        row = result.fetchone()
        return {"id": row.id, "created_at": row.created_at}

    async def list_threads(self, tenant_id: TenantId, limit: int = 50) -> list[dict]:
        sql = """
            SELECT id, aoi_id, signal_id, provider, model, status, created_at
            FROM ai_assistant_threads
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT :limit
            """
        return self._execute_query(
            sql,
            {"tenant_id": str(tenant_id.value), "limit": limit},
        )

    async def get_latest_state(self, tenant_id: TenantId, thread_id: UUID) -> Optional[str]:
        sql = """
            SELECT state_json
            FROM ai_assistant_checkpoints
            WHERE thread_id = :thread_id AND tenant_id = :tenant_id
            ORDER BY step DESC
            LIMIT 1
            """
        row = self._execute_query(
            sql,
            {"thread_id": str(thread_id), "tenant_id": str(tenant_id.value)},
            fetch_one=True,
        )
        return row["state_json"] if row else None

    async def list_approvals(self, tenant_id: TenantId, pending_only: bool) -> list[dict]:
        sql = """
            SELECT id, tool_name, tool_payload, decision, created_at
            FROM ai_assistant_approvals
            WHERE tenant_id = :tenant_id
            AND (:pending_only = false OR decision = 'PENDING')
            ORDER BY created_at DESC
            LIMIT 50
            """
        return self._execute_query(
            sql,
            {"tenant_id": str(tenant_id.value), "pending_only": pending_only},
        )

    async def get_approval_thread_id(self, tenant_id: TenantId, approval_id: UUID) -> Optional[UUID]:
        sql = """
            SELECT thread_id
            FROM ai_assistant_approvals
            WHERE id = :approval_id AND tenant_id = :tenant_id
            """
        row = self._execute_query(
            sql,
            {"approval_id": str(approval_id), "tenant_id": str(tenant_id.value)},
            fetch_one=True,
        )
        return row["thread_id"] if row else None
