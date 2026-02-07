"""Provider registry for satellite and weather data."""
from __future__ import annotations

from typing import Optional

from worker.config import settings
from worker.pipeline.providers.base import SatelliteDataProvider, WeatherDataProvider
from worker.pipeline.providers.fallback_chain import FallbackChainProvider
from worker.pipeline.providers.cached_provider import CachedSatelliteProvider
from worker.pipeline.providers.metrics import ProviderMetrics
from worker.pipeline.providers.planetary_computer import PlanetaryComputerProvider
from worker.pipeline.providers.open_meteo import OpenMeteoProvider

_satellite_provider: Optional[SatelliteDataProvider] = None
_weather_provider: Optional[WeatherDataProvider] = None


def get_satellite_provider() -> SatelliteDataProvider:
    global _satellite_provider
    if _satellite_provider is None:
        providers: list[SatelliteDataProvider] = []
        provider_name = getattr(settings, "satellite_provider", "planetary_computer")
        if provider_name == "planetary_computer":
            providers.append(PlanetaryComputerProvider())
        else:
            raise ValueError(f"Unknown satellite provider: {provider_name}")

        fallback_names = [
            n.strip()
            for n in getattr(settings, "satellite_fallback_providers", "").split(",")
            if n.strip()
        ]
        for name in fallback_names:
            if name == "aws_earth":
                try:
                    from worker.pipeline.providers.aws_earth import AWSEarthSearchProvider
                except Exception:
                    continue
                providers.append(AWSEarthSearchProvider())
            elif name == "cdse":
                try:
                    from worker.pipeline.providers.cdse import CDSEProvider
                except Exception:
                    continue
                if settings.cdse_client_id and settings.cdse_client_secret:
                    providers.append(CDSEProvider(settings.cdse_client_id, settings.cdse_client_secret))

        if len(providers) > 1:
            base_provider = FallbackChainProvider(
                providers,
                metrics=ProviderMetrics(),
            )
        else:
            base_provider = providers[0]

        from worker.database import SessionLocal
        _satellite_provider = CachedSatelliteProvider(base_provider, lambda: SessionLocal())
    return _satellite_provider


def get_weather_provider() -> WeatherDataProvider:
    global _weather_provider
    if _weather_provider is None:
        provider_name = getattr(settings, "weather_provider", "open_meteo")
        if provider_name == "open_meteo":
            _weather_provider = OpenMeteoProvider()
        else:
            raise ValueError(f"Unknown weather provider: {provider_name}")
    return _weather_provider
