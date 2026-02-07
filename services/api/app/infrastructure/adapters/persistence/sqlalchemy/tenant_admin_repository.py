"""SQLAlchemy adapter for tenant admin operations."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.tenant_admin_repository import ITenantAdminRepository
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemyTenantAdminRepository(ITenantAdminRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    async def list_members(self, tenant_id: TenantId) -> list[dict]:
        sql = """
            SELECT m.id, m.identity_id, i.email, i.name, m.role, m.status, m.created_at
            FROM memberships m
            JOIN identities i ON m.identity_id = i.id
            WHERE m.tenant_id = :tenant_id
            ORDER BY m.created_at DESC
            """
        return self._execute_query(sql, {"tenant_id": str(tenant_id.value)})

    async def get_identity_by_email(self, email: str) -> Optional[dict]:
        sql = "SELECT id FROM identities WHERE email = :email"
        row = self._execute_query(sql, {"email": email}, fetch_one=True)
        return dict(row) if row else None

    async def membership_exists(self, tenant_id: TenantId, identity_id: UUID) -> bool:
        sql = """
            SELECT id FROM memberships
            WHERE tenant_id = :tenant_id AND identity_id = :identity_id
            """
        row = self._execute_query(
            sql,
            {"tenant_id": str(tenant_id.value), "identity_id": str(identity_id)},
            fetch_one=True,
        )
        return row is not None

    async def create_identity(self, email: str, name: str) -> UUID:
        sql = text(
            """
            INSERT INTO identities (provider, subject, email, name, status)
            VALUES ('local', :email, :email, :name, 'PENDING')
            RETURNING id
            """
        )
        result = self.db.execute(text(sql), {"email": email, "name": name})
        return result.fetchone()[0]

    async def create_membership(self, tenant_id: TenantId, identity_id: UUID, role: str) -> dict:
        sql = text(
            """
            INSERT INTO memberships (tenant_id, identity_id, role, status)
            VALUES (:tenant_id, :identity_id, :role, 'INVITED')
            RETURNING id, created_at
            """
        )
        result = self.db.execute(
            text(sql),
            {
                "tenant_id": str(tenant_id.value),
                "identity_id": str(identity_id),
                "role": role,
            },
        )
        self.db.commit()
        row = result.fetchone()
        return dict(row._mapping)

    async def get_membership_role(self, tenant_id: TenantId, membership_id: UUID) -> Optional[str]:
        sql = """
            SELECT role FROM memberships
            WHERE id = :membership_id AND tenant_id = :tenant_id
            """
        row = self._execute_query(
            sql,
            {"membership_id": str(membership_id), "tenant_id": str(tenant_id.value)},
            fetch_one=True,
        )
        return row["role"] if row else None

    async def count_active_admins(self, tenant_id: TenantId) -> int:
        sql = """
            SELECT COUNT(*) as count FROM memberships
            WHERE tenant_id = :tenant_id AND role = 'TENANT_ADMIN' AND status = 'ACTIVE'
            """
        row = self._execute_query(sql, {"tenant_id": str(tenant_id.value)}, fetch_one=True)
        return int(row["count"]) if row else 0

    async def update_membership_role(self, tenant_id: TenantId, membership_id: UUID, role: str) -> bool:
        sql = text(
            """
            UPDATE memberships
            SET role = :role
            WHERE id = :membership_id AND tenant_id = :tenant_id
            """
        )
        result = self.db.execute(
            text(sql),
            {"role": role, "membership_id": str(membership_id), "tenant_id": str(tenant_id.value)},
        )
        self.db.commit()
        return result.rowcount > 0

    async def get_membership_role_status(self, tenant_id: TenantId, membership_id: UUID) -> Optional[dict]:
        sql = """
            SELECT role, status FROM memberships
            WHERE id = :membership_id AND tenant_id = :tenant_id
            """
        row = self._execute_query(
            sql,
            {"membership_id": str(membership_id), "tenant_id": str(tenant_id.value)},
            fetch_one=True,
        )
        return dict(row) if row else None

    async def update_membership_status(self, tenant_id: TenantId, membership_id: UUID, status: str) -> bool:
        sql = text(
            """
            UPDATE memberships
            SET status = :status
            WHERE id = :membership_id AND tenant_id = :tenant_id
            """
        )
        result = self.db.execute(
            text(sql),
            {"status": status, "membership_id": str(membership_id), "tenant_id": str(tenant_id.value)},
        )
        self.db.commit()
        return result.rowcount > 0

    async def get_tenant_settings(self, tenant_id: TenantId) -> Optional[dict]:
        sql = """
            SELECT
                CASE
                    WHEN t.type = 'PERSONAL' THEN 'PERSONAL'
                    ELSE UPPER(t.type || '_' || t.plan)
                END AS tier,
                COALESCE(ts.min_valid_pixel_ratio, 0.15) as min_valid_pixel_ratio,
                COALESCE(ts.alert_thresholds, '{}'::jsonb)::text AS alert_thresholds_json
            FROM tenants t
            LEFT JOIN tenant_settings ts ON ts.tenant_id = t.id
            WHERE t.id = :tenant_id
            """
        row = self._execute_query(sql, {"tenant_id": str(tenant_id.value)}, fetch_one=True)
        return dict(row) if row else None

    async def upsert_tenant_settings(
        self,
        tenant_id: TenantId,
        min_valid_pixel_ratio: Optional[float],
        alert_thresholds_json: Optional[str],
    ) -> None:
        sql = """
            INSERT INTO tenant_settings (tenant_id, min_valid_pixel_ratio, alert_thresholds)
            VALUES (:tenant_id, :min_valid, COALESCE(CAST(:thresholds AS jsonb), '{}'::jsonb))
            ON CONFLICT (tenant_id) DO UPDATE
            SET min_valid_pixel_ratio = COALESCE(:min_valid, tenant_settings.min_valid_pixel_ratio),
                alert_thresholds = COALESCE(CAST(:thresholds AS jsonb), tenant_settings.alert_thresholds),
                updated_at = now()
            """
        self.db.execute(
            text(sql),
            {
                "tenant_id": str(tenant_id.value),
                "min_valid": min_valid_pixel_ratio,
                "thresholds": alert_thresholds_json,
            },
        )
        self.db.commit()

    async def list_audit_logs(self, tenant_id: TenantId, limit: int) -> list[dict]:
        sql = """
            SELECT id, action, resource_type, resource_id,
                   diff_json::text as changes_json,
                   metadata_json::text as metadata_json,
                   created_at
            FROM audit_log
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT :limit
            """
        return self._execute_query(
            sql,
            {"tenant_id": str(tenant_id.value), "limit": min(limit, 100)},
        )
