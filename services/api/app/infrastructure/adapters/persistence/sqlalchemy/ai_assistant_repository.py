"""SQLAlchemy adapter for AI assistant operations."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.ai_assistant_repository import IAiAssistantRepository
from app.domain.value_objects.tenant_id import TenantId


class SQLAlchemyAiAssistantRepository(IAiAssistantRepository):
    def __init__(self, db: Session):
        self.db = db

    async def create_thread(
        self,
        tenant_id: TenantId,
        aoi_id: Optional[UUID],
        signal_id: Optional[UUID],
        membership_id: UUID,
        provider: str,
        model: str,
    ) -> dict:
        sql = text(
            """
            INSERT INTO ai_assistant_threads
            (tenant_id, aoi_id, signal_id, created_by_membership_id, provider, model, status)
            VALUES (:tenant_id, :aoi_id, :signal_id, :membership_id, :provider, :model, 'OPEN')
            RETURNING id, created_at
            """
        )
        result = self.db.execute(
            sql,
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
        sql = text(
            """
            SELECT id, aoi_id, signal_id, provider, model, status, created_at
            FROM ai_assistant_threads
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT :limit
            """
        )
        result = self.db.execute(sql, {"tenant_id": str(tenant_id.value), "limit": limit})
        return [dict(row._mapping) for row in result]

    async def get_latest_state(self, tenant_id: TenantId, thread_id: UUID) -> Optional[str]:
        sql = text(
            """
            SELECT state_json
            FROM ai_assistant_checkpoints
            WHERE thread_id = :thread_id AND tenant_id = :tenant_id
            ORDER BY step DESC
            LIMIT 1
            """
        )
        row = self.db.execute(
            sql,
            {"thread_id": str(thread_id), "tenant_id": str(tenant_id.value)},
        ).fetchone()
        return row.state_json if row else None

    async def list_approvals(self, tenant_id: TenantId, pending_only: bool) -> list[dict]:
        sql = text(
            """
            SELECT id, tool_name, tool_payload, decision, created_at
            FROM ai_assistant_approvals
            WHERE tenant_id = :tenant_id
            AND (:pending_only = false OR decision = 'PENDING')
            ORDER BY created_at DESC
            LIMIT 50
            """
        )
        result = self.db.execute(
            sql,
            {"tenant_id": str(tenant_id.value), "pending_only": pending_only},
        )
        return [dict(row._mapping) for row in result]

    async def get_approval_thread_id(self, tenant_id: TenantId, approval_id: UUID) -> Optional[UUID]:
        sql = text(
            """
            SELECT thread_id
            FROM ai_assistant_approvals
            WHERE id = :approval_id AND tenant_id = :tenant_id
            """
        )
        row = self.db.execute(
            sql,
            {"approval_id": str(approval_id), "tenant_id": str(tenant_id.value)},
        ).fetchone()
        return row.thread_id if row else None
