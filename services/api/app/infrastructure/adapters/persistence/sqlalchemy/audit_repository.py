"""SQLAlchemy adapter for audit repository (domain port)."""
from __future__ import annotations

import json
from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.audit_repository import IAuditRepository
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemyAuditRepository(IAuditRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        BaseSQLAlchemyRepository.__init__(self, db)

    def save_event(self, event: Dict[str, Any]) -> None:
        sql = text(
            """
            INSERT INTO audit_log
            (tenant_id, actor_id, actor_type, action, resource_type, resource_id, diff_json, metadata_json)
            VALUES (:tenant_id, :actor_id, :actor_type, :action, :resource_type, :resource_id, :diff_json, :metadata)
            """
        )

        try:
            self.db.execute(
                sql,
                {
                    "tenant_id": event["tenant_id"],
                    "actor_id": event.get("actor_id"),
                    "actor_type": event.get("actor_type", "SYSTEM"),
                    "action": event["action"],
                    "resource_type": event.get("resource_type"),
                    "resource_id": event.get("resource_id"),
                    "diff_json": json.dumps(event.get("changes")) if event.get("changes") else None,
                    "metadata": json.dumps(event.get("metadata")) if event.get("metadata") else None,
                },
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
