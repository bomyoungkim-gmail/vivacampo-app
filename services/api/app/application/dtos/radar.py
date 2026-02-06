"""Radar DTOs."""
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class RadarHistoryCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    year: Optional[int] = None
    limit: int = Field(default=52, ge=1, le=520)
