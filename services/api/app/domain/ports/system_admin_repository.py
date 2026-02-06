"""System admin repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID


class ISystemAdminRepository(ABC):
    @abstractmethod
    async def list_tenants(self, tenant_type: Optional[str], limit: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def create_tenant(self, name: str, tenant_type: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def get_tenant_status(self, tenant_id: UUID) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    async def update_tenant_status(self, tenant_id: UUID, status: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_jobs(self, status: Optional[str], job_type: Optional[str], limit: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def retry_job(self, job_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_missing_aois(self, limit: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def list_active_aois(self, limit: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def list_observation_weeks(self, tenant_id: UUID, aoi_id: UUID) -> list[tuple[int, int]]:
        raise NotImplementedError

    @abstractmethod
    async def get_job_stats_24h(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def get_queue_stats(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def list_audit_logs(self, limit: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def check_db(self) -> tuple[bool, str | None]:
        """Return (is_healthy, error_message)."""
        raise NotImplementedError
