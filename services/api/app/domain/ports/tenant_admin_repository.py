"""Tenant admin repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class ITenantAdminRepository(ABC):
    @abstractmethod
    async def list_members(self, tenant_id: TenantId) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def get_identity_by_email(self, email: str) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    async def membership_exists(self, tenant_id: TenantId, identity_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def create_identity(self, email: str, name: str) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def create_membership(self, tenant_id: TenantId, identity_id: UUID, role: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def get_membership_role(self, tenant_id: TenantId, membership_id: UUID) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    async def count_active_admins(self, tenant_id: TenantId) -> int:
        raise NotImplementedError

    @abstractmethod
    async def update_membership_role(self, tenant_id: TenantId, membership_id: UUID, role: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_membership_role_status(self, tenant_id: TenantId, membership_id: UUID) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    async def update_membership_status(self, tenant_id: TenantId, membership_id: UUID, status: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_tenant_settings(self, tenant_id: TenantId) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    async def upsert_tenant_settings(
        self,
        tenant_id: TenantId,
        min_valid_pixel_ratio: Optional[float],
        alert_thresholds_json: Optional[str],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_audit_logs(self, tenant_id: TenantId, limit: int) -> list[dict]:
        raise NotImplementedError
