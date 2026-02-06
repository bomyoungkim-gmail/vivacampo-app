"""Nominatim geocoding adapter."""
from __future__ import annotations

import httpx
import structlog

from app.domain.ports.geocoding_provider import IGeocodingProvider

logger = structlog.get_logger()


class NominatimAdapter(IGeocodingProvider):
    def __init__(self, base_url: str = "https://nominatim.openstreetmap.org"):
        self.base_url = base_url

    async def geocode(self, query: str, limit: int = 5) -> list[dict]:
        if not query:
            return []

        url = f"{self.base_url}/search"
        params = {
            "format": "json",
            "q": query,
            "limit": limit,
            "addressdetails": 1,
        }
        headers = {"User-Agent": "VivaCampo/1.0 (contact@vivacampo.com)"}

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params, headers=headers, timeout=10.0)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.error("geocode_failed", error=str(exc))
                raise
