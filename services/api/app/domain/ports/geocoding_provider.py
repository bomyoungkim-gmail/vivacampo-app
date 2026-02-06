"""Geocoding provider port."""
from __future__ import annotations

from abc import ABC, abstractmethod


class IGeocodingProvider(ABC):
    @abstractmethod
    async def geocode(self, query: str, limit: int = 5) -> list[dict]:
        raise NotImplementedError
