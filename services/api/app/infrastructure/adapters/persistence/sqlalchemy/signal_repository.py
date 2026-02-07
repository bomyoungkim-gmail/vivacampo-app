"""SQLAlchemy adapter for signal repository (domain port)."""
from __future__ import annotations

import json
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.signal_repository import ISignalRepository
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemySignalRepository(ISignalRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    async def list_signals(
        self,
        tenant_id: TenantId,
        status: Optional[str] = None,
        signal_type: Optional[str] = None,
        aoi_id: Optional[UUID] = None,
        farm_id: Optional[UUID] = None,
        cursor_id: Optional[str] = None,
        cursor_created: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[list[dict], bool]:
        conditions = ["s.tenant_id = :tenant_id"]
        params = {
            "tenant_id": str(tenant_id.value),
            "limit": min(limit, 100),
        }

        if cursor_id and cursor_created:
            conditions.append("(s.created_at, s.id) < (:cursor_created, :cursor_id)")
            params["cursor_created"] = cursor_created
            params["cursor_id"] = cursor_id

        if status:
            conditions.append("s.status = :status")
            params["status"] = status

        if signal_type:
            conditions.append("s.signal_type = :signal_type")
            params["signal_type"] = signal_type

        if aoi_id:
            conditions.append("s.aoi_id = :aoi_id")
            params["aoi_id"] = str(aoi_id)

        if farm_id:
            conditions.append("a.farm_id = :farm_id")
            params["farm_id"] = str(farm_id)

        sql = f"""
            SELECT s.id, s.aoi_id, a.name as aoi_name, s.year, s.week, s.signal_type, s.status, s.severity,
                   s.confidence, s.score, s.model_version, s.change_method,
                   s.evidence_json, s.recommended_actions, s.created_at
            FROM opportunity_signals s
            JOIN aois a ON s.aoi_id = a.id
            WHERE {' AND '.join(conditions)}
            ORDER BY s.created_at DESC, s.id DESC
            LIMIT :limit + 1
            """

        result = self._execute_query(sql, params)
        rows = list(result)
        has_more = len(rows) > limit
        rows = rows[:limit]

        signals = []
        for row in rows:
            evidence = row["evidence_json"]
            actions = row["recommended_actions"]
            signals.append(
                {
                    "id": row["id"],
                    "aoi_id": row["aoi_id"],
                    "aoi_name": row["aoi_name"],
                    "year": row["year"],
                    "week": row["week"],
                    "signal_type": row["signal_type"],
                    "status": row["status"],
                    "severity": row["severity"],
                    "confidence": row["confidence"],
                    "score": row["score"],
                    "model_version": row["model_version"],
                    "change_method": row["change_method"],
                    "evidence_json": json.loads(evidence) if isinstance(evidence, str) else (evidence or {}),
                    "recommended_actions": json.loads(actions) if isinstance(actions, str) else (actions or []),
                    "created_at": row["created_at"],
                }
            )

        return signals, has_more

    async def get_signal(self, tenant_id: TenantId, signal_id: UUID) -> Optional[dict]:
        sql = """
            SELECT s.id, s.aoi_id, a.name as aoi_name, s.year, s.week, s.signal_type, s.status, s.severity,
                   s.confidence, s.score, s.model_version, s.change_method,
                   s.evidence_json, s.recommended_actions, s.created_at
            FROM opportunity_signals s
            JOIN aois a ON s.aoi_id = a.id
            WHERE s.id = :signal_id AND s.tenant_id = :tenant_id
            """

        result = self._execute_query(
            sql,
            {"signal_id": str(signal_id), "tenant_id": str(tenant_id.value)},
            fetch_one=True,
        )

        if not result:
            return None

        evidence = result["evidence_json"]
        actions = result["recommended_actions"]
        return {
            "id": result["id"],
            "aoi_id": result["aoi_id"],
            "aoi_name": result["aoi_name"],
            "year": result["year"],
            "week": result["week"],
            "signal_type": result["signal_type"],
            "status": result["status"],
            "severity": result["severity"],
            "confidence": result["confidence"],
            "score": result["score"],
            "model_version": result["model_version"],
            "change_method": result["change_method"],
            "evidence_json": json.loads(evidence) if isinstance(evidence, str) else (evidence or {}),
            "recommended_actions": json.loads(actions) if isinstance(actions, str) else (actions or []),
            "created_at": result["created_at"],
        }

    async def acknowledge(self, tenant_id: TenantId, signal_id: UUID) -> bool:
        sql = text(
            """
            UPDATE opportunity_signals
            SET status = 'ACK'
            WHERE id = :signal_id AND tenant_id = :tenant_id
            """
        )
        result = self.db.execute(
            text(sql),
            {"signal_id": str(signal_id), "tenant_id": str(tenant_id.value)},
        )
        self.db.commit()
        return result.rowcount > 0
