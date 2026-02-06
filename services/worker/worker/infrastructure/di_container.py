"""Dependency injection container for worker layer."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from worker.config import settings
from worker.infrastructure.adapters.satellite.memory_cache import MemorySatelliteCache
from worker.infrastructure.adapters.satellite.planetary_computer_adapter import PlanetaryComputerAdapter
from worker.infrastructure.adapters.satellite.resilient_satellite_adapter import ResilientSatelliteAdapter
from worker.infrastructure.adapters.jobs.sql_job_repository import SqlJobRepository, SqlSeasonRepository
from worker.infrastructure.adapters.jobs.sql_weather_repository import SqlAoiGeometryRepository, SqlWeatherRepository
from worker.infrastructure.adapters.jobs.open_meteo_provider import OpenMeteoProvider
from worker.infrastructure.adapters.jobs.sqs_job_queue import SqsJobQueue
from worker.infrastructure.adapters.jobs.mosaic_adapters import (
    PlanetaryComputerMosaicProvider,
    S3MosaicStorage,
    SqlMosaicRegistry,
)
from worker.infrastructure.adapters.jobs.radar_adapters import S3ObjectStorage, SqlRadarRepository, StacRadarProvider
from worker.infrastructure.adapters.jobs.signals_adapters import (
    SqlAoiInfoRepository,
    SqlSignalRepository,
    SqlSignalsObservationsRepository,
)
from worker.infrastructure.adapters.jobs.topography_adapters import SqlTopographyRepository, StacTopographyProvider
from worker.infrastructure.adapters.jobs.tiler_stats_adapters import HttpTilerStatsProvider, SqlObservationsRepository
from worker.infrastructure.adapters.jobs.alerts_adapters import (
    SqlAlertRepository,
    SqlAlertsObservationsRepository,
    SqlTenantSettingsRepository,
)
from worker.infrastructure.adapters.jobs.forecast_adapters import (
    SqlForecastObservationsRepository,
    SqlSeasonRepository,
    SqlYieldForecastRepository,
)
from worker.infrastructure.adapters.jobs.warm_cache_adapters import HttpTileWarmClient, SqlAoiBoundsRepository
from worker.infrastructure.adapters.jobs.harvest_adapters import SqlHarvestSignalRepository, SqlRadarMetricsRepository


class WorkerContainer:
    """Lightweight DI container for worker adapters."""

    def __init__(
        self,
        env: Optional[str] = None,
        use_memory_cache: Optional[bool] = None,
        overrides: Optional[dict[str, object]] = None,
    ):
        self.env = env or settings.env
        self.use_memory_cache = use_memory_cache if use_memory_cache is not None else self.env == "local"
        self.overrides = overrides or {}

    def _resolve(self, name: str, factory, *args, **kwargs):
        override = self.overrides.get(name)
        if override is None:
            return factory(*args, **kwargs)
        if callable(override):
            return override(*args, **kwargs)
        return override

    def satellite_cache(self) -> Optional[MemorySatelliteCache]:
        return self._resolve(
            "satellite_cache",
            lambda: MemorySatelliteCache() if self.use_memory_cache else None,
        )

    def satellite_primary(self) -> PlanetaryComputerAdapter:
        return self._resolve("satellite_primary", PlanetaryComputerAdapter)

    def satellite_fallback(self) -> PlanetaryComputerAdapter:
        # Placeholder fallback (same provider) until a second provider is implemented.
        return self._resolve("satellite_fallback", PlanetaryComputerAdapter)

    def satellite_provider(self) -> ResilientSatelliteAdapter:
        return self._resolve(
            "satellite_provider",
            ResilientSatelliteAdapter,
            primary=self.satellite_primary(),
            fallback=self.satellite_fallback(),
            cache=self.satellite_cache(),
        )

    def job_repository(self, db: Session) -> SqlJobRepository:
        return self._resolve("job_repository", SqlJobRepository, db)

    def season_repository(self, db: Session) -> SqlSeasonRepository:
        return self._resolve("season_repository", SqlSeasonRepository, db)

    def job_queue(self) -> SqsJobQueue:
        return self._resolve("job_queue", SqsJobQueue)

    def aoi_geometry_repository(self, db: Session) -> SqlAoiGeometryRepository:
        return self._resolve("aoi_geometry_repository", SqlAoiGeometryRepository, db)

    def weather_repository(self, db: Session) -> SqlWeatherRepository:
        return self._resolve("weather_repository", SqlWeatherRepository, db)

    def weather_provider(self) -> OpenMeteoProvider:
        return self._resolve("weather_provider", OpenMeteoProvider)

    def mosaic_provider(self) -> PlanetaryComputerMosaicProvider:
        return self._resolve("mosaic_provider", PlanetaryComputerMosaicProvider)

    def mosaic_storage(self) -> S3MosaicStorage:
        return self._resolve("mosaic_storage", S3MosaicStorage)

    def mosaic_registry(self, db: Session) -> SqlMosaicRegistry:
        return self._resolve("mosaic_registry", SqlMosaicRegistry, db)

    def radar_provider(self) -> StacRadarProvider:
        return self._resolve("radar_provider", StacRadarProvider)

    def radar_repository(self, db: Session) -> SqlRadarRepository:
        return self._resolve("radar_repository", SqlRadarRepository, db)

    def object_storage(self) -> S3ObjectStorage:
        return self._resolve("object_storage", S3ObjectStorage)

    def topography_provider(self) -> StacTopographyProvider:
        return self._resolve("topography_provider", StacTopographyProvider)

    def topography_repository(self, db: Session) -> SqlTopographyRepository:
        return self._resolve("topography_repository", SqlTopographyRepository, db)

    def tiler_stats_provider(self) -> HttpTilerStatsProvider:
        return self._resolve("tiler_stats_provider", HttpTilerStatsProvider)

    def observations_repository(self, db: Session) -> SqlObservationsRepository:
        return self._resolve("observations_repository", SqlObservationsRepository, db)

    def signals_observations_repository(self, db: Session) -> SqlSignalsObservationsRepository:
        return self._resolve("signals_observations_repository", SqlSignalsObservationsRepository, db)

    def aoi_info_repository(self, db: Session) -> SqlAoiInfoRepository:
        return self._resolve("aoi_info_repository", SqlAoiInfoRepository, db)

    def signal_repository(self, db: Session) -> SqlSignalRepository:
        return self._resolve("signal_repository", SqlSignalRepository, db)

    def alerts_observations_repository(self, db: Session) -> SqlAlertsObservationsRepository:
        return self._resolve("alerts_observations_repository", SqlAlertsObservationsRepository, db)

    def tenant_settings_repository(self, db: Session) -> SqlTenantSettingsRepository:
        return self._resolve("tenant_settings_repository", SqlTenantSettingsRepository, db)

    def alert_repository(self, db: Session) -> SqlAlertRepository:
        return self._resolve("alert_repository", SqlAlertRepository, db)

    def forecast_observations_repository(self, db: Session) -> SqlForecastObservationsRepository:
        return self._resolve("forecast_observations_repository", SqlForecastObservationsRepository, db)

    def yield_forecast_repository(self, db: Session) -> SqlYieldForecastRepository:
        return self._resolve("yield_forecast_repository", SqlYieldForecastRepository, db)

    def aoi_bounds_repository(self, db: Session) -> SqlAoiBoundsRepository:
        return self._resolve("aoi_bounds_repository", SqlAoiBoundsRepository, db)

    def tile_warm_client(self) -> HttpTileWarmClient:
        return self._resolve("tile_warm_client", HttpTileWarmClient)

    def radar_metrics_repository(self, db: Session) -> SqlRadarMetricsRepository:
        return self._resolve("radar_metrics_repository", SqlRadarMetricsRepository, db)

    def harvest_signal_repository(self, db: Session) -> SqlHarvestSignalRepository:
        return self._resolve("harvest_signal_repository", SqlHarvestSignalRepository, db)
