"""Resilient satellite adapter with fallback chain and circuit breaker."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol
import time

import structlog

from worker.domain.ports.satellite_provider import ISatelliteProvider, SatelliteScene

logger = structlog.get_logger()


class SatelliteCache(Protocol):
    async def store(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        scenes: List[SatelliteScene],
    ) -> None:
        ...

    async def retrieve(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> List[SatelliteScene]:
        ...


class _CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout_seconds: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.failure_count = 0
        self.last_failure_ts: float | None = None

    def _is_open(self) -> bool:
        if self.failure_count < self.failure_threshold:
            return False
        if self.last_failure_ts is None:
            return True
        return (time.time() - self.last_failure_ts) < self.recovery_timeout_seconds

    def allow(self) -> bool:
        return not self._is_open()

    def record_success(self) -> None:
        self.failure_count = 0
        self.last_failure_ts = None

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_ts = time.time()


class ResilientSatelliteAdapter(ISatelliteProvider):
    """Provider with fallback chain: primary -> fallback -> cache -> empty."""

    def __init__(
        self,
        primary: ISatelliteProvider,
        fallback: ISatelliteProvider,
        cache: Optional[SatelliteCache] = None,
        circuit_failure_threshold: int = 3,
        circuit_recovery_timeout_seconds: int = 300,
    ):
        self.primary = primary
        self.fallback = fallback
        self.cache = cache
        self._circuit = _CircuitBreaker(
            failure_threshold=circuit_failure_threshold,
            recovery_timeout_seconds=circuit_recovery_timeout_seconds,
        )

    @property
    def provider_name(self) -> str:
        return f"resilient({self.primary.provider_name})"

    async def search_scenes(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        collections: Optional[List[str]] = None,
        max_cloud_cover: float = 60.0,
    ) -> List[SatelliteScene]:
        if self._circuit.allow():
            try:
                scenes = await self.primary.search_scenes(
                    geometry=geometry,
                    start_date=start_date,
                    end_date=end_date,
                    collections=collections,
                    max_cloud_cover=max_cloud_cover,
                )
                self._circuit.record_success()
                if self.cache:
                    await self.cache.store(geometry, start_date, end_date, scenes)
                logger.info("satellite_search_primary_ok", count=len(scenes))
                return scenes
            except Exception as exc:
                self._circuit.record_failure()
                logger.warning("satellite_primary_failed", exc_info=exc)
        else:
            logger.warning("satellite_primary_circuit_open")

        try:
            scenes = await self.fallback.search_scenes(
                geometry=geometry,
                start_date=start_date,
                end_date=end_date,
                collections=collections,
                max_cloud_cover=max_cloud_cover,
            )
            if self.cache:
                await self.cache.store(geometry, start_date, end_date, scenes)
            logger.info("satellite_search_fallback_ok", count=len(scenes))
            return scenes
        except Exception as exc:
            logger.warning("satellite_fallback_failed", exc_info=exc)

        if self.cache:
            try:
                cached = await self.cache.retrieve(geometry, start_date, end_date)
                logger.info("satellite_search_cache_used", count=len(cached))
                return cached
            except Exception as exc:
                logger.warning("satellite_cache_failed", exc_info=exc)

        logger.info("satellite_search_degraded", count=0)
        return []

    async def download_band(self, asset_href: str, geometry: Dict[str, Any], output_path: str) -> str:
        if self._circuit.allow():
            try:
                result = await self.primary.download_band(asset_href, geometry, output_path)
                self._circuit.record_success()
                return result
            except Exception as exc:
                self._circuit.record_failure()
                logger.warning("satellite_download_primary_failed", exc_info=exc)
        else:
            logger.warning("satellite_download_primary_circuit_open")

        return await self.fallback.download_band(asset_href, geometry, output_path)

    async def health_check(self) -> bool:
        primary_ok = await self.primary.health_check()
        fallback_ok = await self.fallback.health_check()
        return primary_ok or fallback_ok
