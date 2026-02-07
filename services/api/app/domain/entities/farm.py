"""
Farm domain entity.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from zoneinfo import available_timezones

from pydantic import Field, field_validator

from app.domain.base import DomainEntity
from app.domain.value_objects.tenant_id import TenantId
from app.domain.entities.user import UserRole


class Farm(DomainEntity):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: TenantId
    created_by_user_id: Optional[UUID] = None
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
        self.updated_at = datetime.now(timezone.utc)

    def can_edit(self, user_id: UUID, user_role: UserRole) -> bool:
        if user_role == UserRole.SYSTEM_ADMIN:
            return True
        if user_role == UserRole.TENANT_ADMIN:
            return True
        if user_role == UserRole.EDITOR:
            return self.created_by_user_id == user_id
        return False
