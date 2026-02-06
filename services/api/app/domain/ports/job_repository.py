"""Job repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class IJobRepository(ABC):
    @abstractmethod
    async def list_jobs(
        self,
        tenant_id: TenantId,
        aoi_id: Optional[UUID] = None,
        job_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        raise NotImplementedError

    @abstractmethod
    async def get_job(self, tenant_id: TenantId, job_id: UUID) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    async def list_runs(self, tenant_id: TenantId, job_id: UUID, limit: int = 10) -> tuple[List[dict], bool]:
        raise NotImplementedError

    @abstractmethod
    async def update_status(self, tenant_id: TenantId, job_id: UUID, status: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def create_backfill_job(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        job_key: str,
        payload_json: str,
    ) -> UUID:
        raise NotImplementedError

    @abstractmethod
    async def create_weather_sync_job(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        job_key: str,
        payload_json: str,
    ) -> UUID:
        raise NotImplementedError
