"""TenantId value object."""
from uuid import UUID

from app.domain.base import ValueObject


class TenantId(ValueObject):
    value: UUID
