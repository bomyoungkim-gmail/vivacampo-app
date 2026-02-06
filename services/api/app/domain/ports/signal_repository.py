"""Signal repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class ISignalRepository(ABC):
    @abstractmethod
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
        """Return (signals, has_more)."""
        raise NotImplementedError

    @abstractmethod
    async def get_signal(self, tenant_id: TenantId, signal_id: UUID) -> Optional[dict]:
        raise NotImplementedError

    @abstractmethod
    async def acknowledge(self, tenant_id: TenantId, signal_id: UUID) -> bool:
        raise NotImplementedError
