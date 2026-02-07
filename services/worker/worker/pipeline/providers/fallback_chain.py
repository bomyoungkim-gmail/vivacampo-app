"""
Fallback chain provider with circuit breaker.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import time

import structlog

from worker.pipeline.providers.base import SatelliteDataProvider
from worker.pipeline.providers.metrics import ProviderMetrics

logger = structlog.get_logger()


class ProviderCircuitBreaker:
    """Circuit breaker per provider name."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout_seconds: int = 300):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_seconds
        self._failures: Dict[str, int] = {}
        self._last_failure: Dict[str, float] = {}
        self._state: Dict[str, str] = {}

    def is_available(self, provider_name: str) -> bool:
        state = self._state.get(provider_name, "CLOSED")
        if state == "CLOSED":
            return True
        if state == "OPEN":
            last = self._last_failure.get(provider_name, 0)
            if time.time() - last > self._recovery_timeout:
                self._state[provider_name] = "HALF_OPEN"
                logger.info("circuit_half_open", provider=provider_name)
                return True
            return False
        return True

    def record_success(self, provider_name: str) -> None:
        self._failures[provider_name] = 0
        self._state[provider_name] = "CLOSED"
        logger.debug("circuit_closed", provider=provider_name)

    def record_failure(self, provider_name: str) -> None:
        count = self._failures.get(provider_name, 0) + 1
        self._failures[provider_name] = count
        self._last_failure[provider_name] = time.time()
        if count >= self._failure_threshold:
            self._state[provider_name] = "OPEN"
            logger.warning("circuit_opened", provider=provider_name, failures=count)


class FallbackChainProvider(SatelliteDataProvider):
    """Try providers in sequence with circuit breaker."""

    def __init__(
        self,
        providers: List[SatelliteDataProvider],
        circuit_breaker: Optional[ProviderCircuitBreaker] = None,
        metrics: Optional[ProviderMetrics] = None,
    ) -> None:
        if not providers:
            raise ValueError("At least one provider is required")
        self._providers = providers
        self._circuit = circuit_breaker or ProviderCircuitBreaker()
        self._metrics = metrics

    @property
    def provider_name(self) -> str:
        names = [p.provider_name for p in self._providers]
        return f"fallback_chain({','.join(names)})"

    @property
    def supported_collections(self) -> List[str]:
        all_collections = set()
        for p in self._providers:
            all_collections.update(p.supported_collections)
        return list(all_collections)

    async def search_scenes(
        self,
        aoi_geom: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        last_error: Optional[Exception] = None

        for provider in self._providers:
            if collections:
                if not any(c in provider.supported_collections for c in collections):
                    continue

            if not self._circuit.is_available(provider.provider_name):
                logger.info("provider_skipped_circuit_open", provider=provider.provider_name)
                continue

            try:
                start = time.time()
                logger.info("fallback_trying_provider", provider=provider.provider_name)
                scenes = await provider.search_scenes(
                    aoi_geom, start_date, end_date, max_cloud_cover, collections
                )
                self._circuit.record_success(provider.provider_name)
                if self._metrics:
                    self._metrics.record_call(
                        provider.provider_name,
                        "search_scenes",
                        (time.time() - start) * 1000,
                        True,
                    )
                for scene in scenes:
                    if isinstance(scene, dict):
                        scene["_provider"] = provider.provider_name
                return scenes
            except Exception as exc:
                logger.warning("provider_failed", provider=provider.provider_name, error=str(exc))
                self._circuit.record_failure(provider.provider_name)
                if self._metrics:
                    self._metrics.record_call(
                        provider.provider_name,
                        "search_scenes",
                        (time.time() - start) * 1000,
                        False,
                        error=str(exc),
                    )
                last_error = exc
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}") from last_error

    async def download_and_clip_band(self, asset_href, aoi_geom, output_path):
        last_error: Optional[Exception] = None
        for provider in self._providers:
            if not self._circuit.is_available(provider.provider_name):
                continue
            try:
                start = time.time()
                result = await provider.download_and_clip_band(asset_href, aoi_geom, output_path)
                self._circuit.record_success(provider.provider_name)
                if self._metrics:
                    self._metrics.record_call(
                        provider.provider_name,
                        "download_and_clip_band",
                        (time.time() - start) * 1000,
                        True,
                    )
                return result
            except Exception as exc:
                self._circuit.record_failure(provider.provider_name)
                if self._metrics:
                    self._metrics.record_call(
                        provider.provider_name,
                        "download_and_clip_band",
                        (time.time() - start) * 1000,
                        False,
                        error=str(exc),
                    )
                last_error = exc
                continue
        raise RuntimeError(f"All providers failed for download. Last: {last_error}") from last_error

    def sign_url(self, href: str) -> str:
        for provider in self._providers:
            if self._circuit.is_available(provider.provider_name):
                return provider.sign_url(href)
        return href

    async def search_raw_items(
        self,
        bbox: List[float],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None,
        max_items: int = 2000,
    ):
        last_error: Optional[Exception] = None
        for provider in self._providers:
            if collections:
                if not any(c in provider.supported_collections for c in collections):
                    continue
            if not self._circuit.is_available(provider.provider_name):
                continue
            try:
                start = time.time()
                items = await provider.search_raw_items(
                    bbox=bbox,
                    start_date=start_date,
                    end_date=end_date,
                    max_cloud_cover=max_cloud_cover,
                    collections=collections,
                    max_items=max_items,
                )
                self._circuit.record_success(provider.provider_name)
                if self._metrics:
                    self._metrics.record_call(
                        provider.provider_name,
                        "search_raw_items",
                        (time.time() - start) * 1000,
                        True,
                    )
                return items
            except Exception as exc:
                self._circuit.record_failure(provider.provider_name)
                if self._metrics:
                    self._metrics.record_call(
                        provider.provider_name,
                        "search_raw_items",
                        (time.time() - start) * 1000,
                        False,
                        error=str(exc),
                    )
                last_error = exc
                continue
        raise RuntimeError(f"All providers failed for raw items. Last: {last_error}") from last_error

    async def health_check(self) -> bool:
        for provider in self._providers:
            try:
                if await provider.health_check():
                    return True
            except Exception:
                continue
        return False
