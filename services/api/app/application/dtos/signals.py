"""Signal DTOs for application layer."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class ListSignalsCommand(ImmutableDTO):
    tenant_id: TenantId
    status: Optional[str] = None
    signal_type: Optional[str] = None
    aoi_id: Optional[UUID] = None
    farm_id: Optional[UUID] = None
    cursor: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)


class GetSignalCommand(ImmutableDTO):
    tenant_id: TenantId
    signal_id: UUID


class AckSignalCommand(ImmutableDTO):
    tenant_id: TenantId
    signal_id: UUID


class SignalResult(ImmutableDTO):
    id: UUID
    aoi_id: UUID
    aoi_name: Optional[str] = None
    year: int
    week: int
    signal_type: str
    status: str
    severity: str
    confidence: str
    score: float
    model_version: str
    change_method: str
    evidence_json: dict
    recommended_actions: List[str]
    created_at: datetime


class ListSignalsResult(ImmutableDTO):
    items: List[SignalResult]
    next_cursor: Optional[str] = None
