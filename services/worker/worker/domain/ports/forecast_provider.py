"""Ports for FORECAST_WEEK processing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class SeasonRepository(ABC):
    @abstractmethod
    def get_active_season(self, *, tenant_id: str, aoi_id: str) -> Optional[dict]:
        """Return active season info."""
        raise NotImplementedError


class ForecastObservationsRepository(ABC):
    @abstractmethod
    def list_observations(self, *, tenant_id: str, aoi_id: str) -> List[dict]:
        """Return observations ordered by year/week."""
        raise NotImplementedError


class YieldForecastRepository(ABC):
    @abstractmethod
    def list_historical_yields(self, *, tenant_id: str, aoi_id: str, limit: int) -> List[float]:
        """Return historical yield values."""
        raise NotImplementedError

    @abstractmethod
    def save_forecast(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        season_id: str,
        year: int,
        week: int,
        estimated_yield: float,
        confidence: str,
        evidence: dict,
        method: str,
        model_version: str,
    ) -> None:
        """Persist forecast values."""
        raise NotImplementedError
