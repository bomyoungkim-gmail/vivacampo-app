"""SQLAlchemy adapter for auth operations."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.auth_repository import IAuthRepository
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemyAuthRepository(IAuthRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    async def get_identity_by_email(self, email: str) -> Optional[dict]:
        sql = """
            SELECT id, provider, subject, email, name, status, password_hash,
                   password_reset_token, password_reset_expires_at
            FROM identities
            WHERE email = :email
            """
        return self._execute_query(sql, {"email": email}, fetch_one=True)

    async def get_identity_by_email_provider(self, email: str, provider: str) -> Optional[dict]:
        sql = """
            SELECT id, provider, subject, email, name, status, password_hash,
                   password_reset_token, password_reset_expires_at
            FROM identities
            WHERE email = :email AND provider = :provider
            """
        return self._execute_query(sql, {"email": email, "provider": provider}, fetch_one=True)

    async def get_identity_by_reset_token(self, token: str) -> Optional[dict]:
        sql = """
            SELECT id, provider, subject, email, name, status, password_hash,
                   password_reset_token, password_reset_expires_at
            FROM identities
            WHERE password_reset_token = :token
            """
        return self._execute_query(sql, {"token": token}, fetch_one=True)

    async def create_identity_local(self, email: str, name: str, password_hash: str) -> dict:
        sql = text(
            """
            INSERT INTO identities (provider, subject, email, name, password_hash, status)
            VALUES ('local', :email, :email, :name, :password_hash, 'ACTIVE')
            RETURNING id, provider, subject, email, name, status
            """
        )
        result = self.db.execute(
            sql,
            {"email": email, "name": name, "password_hash": password_hash},
        )
        row = result.fetchone()
        self.db.commit()
        return dict(row._mapping)

    async def update_identity_password(self, identity_id: UUID, password_hash: str) -> None:
        sql = text(
            """
            UPDATE identities
            SET password_hash = :password_hash
            WHERE id = :identity_id
            """
        )
        self.db.execute(sql, {"password_hash": password_hash, "identity_id": str(identity_id)})
        self.db.commit()

    async def set_password_reset(self, identity_id: UUID, token: str, expires_at: datetime) -> None:
        sql = text(
            """
            UPDATE identities
            SET password_reset_token = :token,
                password_reset_expires_at = :expires_at
            WHERE id = :identity_id
            """
        )
        self.db.execute(
            sql,
            {"token": token, "expires_at": expires_at, "identity_id": str(identity_id)},
        )
        self.db.commit()

    async def clear_password_reset(self, identity_id: UUID) -> None:
        sql = text(
            """
            UPDATE identities
            SET password_reset_token = NULL,
                password_reset_expires_at = NULL
            WHERE id = :identity_id
            """
        )
        self.db.execute(sql, {"identity_id": str(identity_id)})
        self.db.commit()

    async def create_tenant(self, tenant_type: str, name: str, plan: str, quotas: dict) -> dict:
        import json
        sql = text(
            """
            INSERT INTO tenants (type, name, status, plan, quotas)
            VALUES (:tenant_type, :name, 'ACTIVE', :plan, :quotas)
            RETURNING id, type, name, status, plan
            """
        )
        result = self.db.execute(
            sql,
            {"tenant_type": tenant_type, "name": name, "plan": plan, "quotas": json.dumps(quotas)},
        )
        row = result.fetchone()
        self.db.commit()
        return dict(row._mapping)

    async def create_membership(self, tenant_id: UUID, identity_id: UUID, role: str, status: str) -> dict:
        sql = text(
            """
            INSERT INTO memberships (tenant_id, identity_id, role, status)
            VALUES (:tenant_id, :identity_id, :role, :status)
            RETURNING id, tenant_id, identity_id, role, status, created_at
            """
        )
        result = self.db.execute(
            sql,
            {
                "tenant_id": str(tenant_id),
                "identity_id": str(identity_id),
                "role": role,
                "status": status,
            },
        )
        row = result.fetchone()
        self.db.commit()
        return dict(row._mapping)

    async def list_workspaces(self, identity_id: UUID) -> list[dict]:
        sql = """
            SELECT m.id AS membership_id,
                   m.tenant_id AS tenant_id,
                   m.role AS role,
                   m.status AS status,
                   t.type AS tenant_type,
                   t.name AS tenant_name
            FROM memberships m
            JOIN tenants t ON t.id = m.tenant_id
            WHERE m.identity_id = :identity_id
            ORDER BY m.created_at ASC
            """
        return self._execute_query(sql, {"identity_id": str(identity_id)})
