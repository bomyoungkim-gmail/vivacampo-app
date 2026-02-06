"""Ports for mosaic creation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable


class MosaicProvider(ABC):
    @abstractmethod
    def search_scenes(
        self,
        *,
        collection: str,
        start_date: str,
        end_date: str,
        bbox: list[float],
        max_cloud_cover: float,
        max_items: int,
    ) -> Iterable[Any]:
        """Search STAC for scenes."""
        raise NotImplementedError


class MosaicStorage(ABC):
    @abstractmethod
    def save_json(self, *, key: str, payload: dict) -> str:
        """Persist MosaicJSON and return URL."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, *, key: str) -> bool:
        """Check if mosaic exists."""
        raise NotImplementedError


class MosaicRegistry(ABC):
    @abstractmethod
    def save_record(self, *, collection: str, year: int, week: int, url: str, scene_count: int) -> None:
        """Persist mosaic metadata for tracking."""
        raise NotImplementedError
