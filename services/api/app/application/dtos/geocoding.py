"""Geocoding DTOs."""
from pydantic import Field

from app.domain.base import ImmutableDTO


class GeocodeCommand(ImmutableDTO):
    query: str = Field(min_length=1, max_length=200)
    limit: int = Field(default=5, ge=1, le=10)
