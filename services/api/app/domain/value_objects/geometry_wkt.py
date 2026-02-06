"""GeometryWkt value object."""
from pydantic import field_validator

from app.domain.base import ValueObject


class GeometryWkt(ValueObject):
    value: str

    @field_validator("value")
    @classmethod
    def validate_wkt(cls, v: str) -> str:
        if not (v.startswith("POLYGON") or v.startswith("MULTIPOLYGON")):
            raise ValueError("Geometry must start with POLYGON or MULTIPOLYGON")
        if "(" not in v or ")" not in v:
            raise ValueError("Geometry must contain parentheses")
        return v
