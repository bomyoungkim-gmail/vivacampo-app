"""Ports for ALERTS_WEEK processing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TenantSettingsRepository(ABC):
    @abstractmethod
    def get_min_valid_pixel_ratio(self, *, tenant_id: str) -> float:
        """Return min valid pixel ratio for tenant."""
        raise NotImplementedError


class AlertsObservationsRepository(ABC):
    @abstractmethod
    def get_observation(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
    ) -> Optional[dict]:
        """Return observation for week."""
        raise NotImplementedError

    @abstractmethod
    def get_previous_observation(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
    ) -> Optional[dict]:
        """Return previous observation (prior week).
        """
        raise NotImplementedError

    @abstractmethod
    def count_persistent_anomalies(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
    ) -> int:
        """Count recent anomalies over last 3 weeks."""
        raise NotImplementedError


class AlertRepository(ABC):
    @abstractmethod
    def get_existing(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        alert_type: str,
    ) -> Optional[dict]:
        """Return existing alert if present."""
        raise NotImplementedError

    @abstractmethod
    def update_alert(self, *, alert_id: str, severity: str, confidence: str, evidence: dict) -> None:
        """Update existing alert."""
        raise NotImplementedError

    @abstractmethod
    def create_alert(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        alert_type: str,
        severity: str,
        confidence: str,
        evidence: dict,
    ) -> None:
        """Create new alert."""
        raise NotImplementedError
