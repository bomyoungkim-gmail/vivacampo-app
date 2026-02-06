"""
Farm domain entity.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from zoneinfo import available_timezones

from pydantic import Field, field_validator

from app.domain.base import DomainEntity
from app.domain.value_objects.tenant_id import TenantId


class Farm(DomainEntity):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: TenantId
    name: str = Field(min_length=3, max_length=100)
    timezone: str = Field(default="America/Sao_Paulo")
    aoi_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        if v not in available_timezones():
            raise ValueError(f"Invalid timezone: {v}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v.lower() in {"test", "admin", "system"}:
            raise ValueError("Reserved farm name")
        return v

    def update_name(self, new_name: str) -> None:
        self.name = new_name
        self.updated_at = datetime.utcnow()
