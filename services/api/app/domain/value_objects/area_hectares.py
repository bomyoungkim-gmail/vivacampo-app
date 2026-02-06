"""AreaHectares value object."""
import math
from pydantic import field_validator

from app.domain.base import ValueObject


class AreaHectares(ValueObject):
    value: float

    @field_validator("value")
    @classmethod
    def validate_area(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("Area must be finite")
        if v <= 0:
            raise ValueError("Area must be positive")
        if v > 10000:
            raise ValueError("Area exceeds max allowed (10000 ha)")
        return v
