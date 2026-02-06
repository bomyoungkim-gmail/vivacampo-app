"""UserId value object."""
from uuid import UUID

from app.domain.base import ValueObject


class UserId(ValueObject):
    value: UUID
