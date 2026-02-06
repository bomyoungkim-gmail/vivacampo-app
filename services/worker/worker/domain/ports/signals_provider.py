"""Ports for SIGNALS_WEEK processing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class SignalsObservationsRepository(ABC):
    @abstractmethod
    def list_recent(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        limit: int,
    ) -> List[dict]:
        """Return recent observations in chronological order."""
        raise NotImplementedError


class AoiInfoRepository(ABC):
    @abstractmethod
    def get_use_type(self, *, tenant_id: str, aoi_id: str) -> str:
        """Return AOI use_type."""
        raise NotImplementedError


class SignalRepository(ABC):
    @abstractmethod
    def get_existing(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        signal_type: str,
        pipeline_version: str,
    ) -> Optional[dict]:
        """Return existing signal row if present."""
        raise NotImplementedError

    @abstractmethod
    def update_signal(self, *, signal_id: str, score: float, evidence: dict, features: dict) -> None:
        """Update signal score and evidence."""
        raise NotImplementedError

    @abstractmethod
    def create_signal(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        signal_type: str,
        severity: str,
        confidence: str,
        score: float,
        evidence: dict,
        features: dict,
        recommended_actions: list,
        created_at,
        pipeline_version: str,
        model_version: str,
        change_method: str,
    ) -> None:
        """Create a new signal row."""
        raise NotImplementedError
