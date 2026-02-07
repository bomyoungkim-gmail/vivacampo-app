"""SQLAlchemy adapter for quota repository (domain port)."""
from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.quota_repository import IQuotaRepository
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemyQuotaRepository(IQuotaRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        BaseSQLAlchemyRepository.__init__(self, db)

    def get_tenant_tier(self, tenant_id: str) -> str:
        sql = text(
            """
            SELECT type, plan FROM tenants
            WHERE id = :tenant_id
            """
        )
        result = self._execute_query(sql, {"tenant_id": tenant_id}, fetch_one=True)

        if not result:
            return "PERSONAL"

        if result["type"] == "PERSONAL":
            return "PERSONAL"

        tier = f"{result['type']}_{result['plan']}".upper()
        return tier

    def count_aois(self, tenant_id: str) -> int:
        sql = text(
            """
            SELECT COUNT(*) as count
            FROM aois
            WHERE tenant_id = :tenant_id AND status = 'ACTIVE'
            """
        )
        result = self._execute_query(sql, {"tenant_id": tenant_id}, fetch_one=True)
        return result["count"] if result else 0

    def count_farms(self, tenant_id: str) -> int:
        sql = text(
            """
            SELECT COUNT(*) as count
            FROM farms
            WHERE tenant_id = :tenant_id
            """
        )
        result = self._execute_query(sql, {"tenant_id": tenant_id}, fetch_one=True)
        return result["count"] if result else 0

    def count_backfills_on_date(self, tenant_id: str, on_date: date) -> int:
        sql = text(
            """
            SELECT COUNT(*) as count
            FROM jobs
            WHERE tenant_id = :tenant_id
              AND job_type = 'BACKFILL'
              AND DATE(created_at) = :today
            """
        )
        result = self._execute_query(sql, {"tenant_id": tenant_id, "today": on_date}, fetch_one=True)
        return result["count"] if result else 0

    def count_members(self, tenant_id: str) -> int:
        sql = text(
            """
            SELECT COUNT(*) as count
            FROM memberships
            WHERE tenant_id = :tenant_id AND status = 'ACTIVE'
            """
        )
        result = self._execute_query(sql, {"tenant_id": tenant_id}, fetch_one=True)
        return result["count"] if result else 0

    def count_ai_threads_on_date(self, tenant_id: str, on_date: date) -> int:
        sql = text(
            """
            SELECT COUNT(*) as count
            FROM ai_assistant_threads
            WHERE tenant_id = :tenant_id
              AND DATE(created_at) = :today
            """
        )
        result = self._execute_query(sql, {"tenant_id": tenant_id, "today": on_date}, fetch_one=True)
        return result["count"] if result else 0
