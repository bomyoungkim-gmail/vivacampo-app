"""Field feedback repository port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class IFieldFeedbackRepository(ABC):
    @abstractmethod
    async def create(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        feedback_type: str,
        message: str,
        created_by_membership_id: UUID | None,
    ) -> UUID:
        raise NotImplementedError
