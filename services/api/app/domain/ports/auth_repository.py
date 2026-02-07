from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID


class IAuthRepository:
    async def get_identity_by_email(self, email: str) -> Optional[dict]:
        raise NotImplementedError

    async def get_identity_by_email_provider(self, email: str, provider: str) -> Optional[dict]:
        raise NotImplementedError

    async def get_identity_by_reset_token(self, token: str) -> Optional[dict]:
        raise NotImplementedError

    async def create_identity_local(self, email: str, name: str, password_hash: str) -> dict:
        raise NotImplementedError

    async def update_identity_password(self, identity_id: UUID, password_hash: str) -> None:
        raise NotImplementedError

    async def set_password_reset(self, identity_id: UUID, token: str, expires_at: datetime) -> None:
        raise NotImplementedError

    async def clear_password_reset(self, identity_id: UUID) -> None:
        raise NotImplementedError

    async def create_tenant(self, tenant_type: str, name: str, plan: str, quotas: dict) -> dict:
        raise NotImplementedError

    async def create_membership(self, tenant_id: UUID, identity_id: UUID, role: str, status: str) -> dict:
        raise NotImplementedError

    async def list_workspaces(self, identity_id: UUID) -> list[dict]:
        raise NotImplementedError
