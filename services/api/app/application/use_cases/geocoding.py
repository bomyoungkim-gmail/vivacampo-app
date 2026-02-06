"""Geocoding use cases."""
from __future__ import annotations

from app.application.dtos.geocoding import GeocodeCommand
from app.domain.ports.geocoding_provider import IGeocodingProvider


class GeocodeUseCase:
    def __init__(self, provider: IGeocodingProvider):
        self.provider = provider

    async def execute(self, command: GeocodeCommand) -> list[dict]:
        return await self.provider.geocode(command.query, limit=command.limit)
