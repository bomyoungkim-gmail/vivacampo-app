"""In-memory cache for satellite scenes (dev/test)."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from worker.domain.ports.satellite_provider import SatelliteScene


class MemorySatelliteCache:
    def __init__(self):
        self._store: dict[str, List[SatelliteScene]] = {}

    def _key(self, geometry: Dict[str, Any], start_date: datetime, end_date: datetime) -> str:
        payload = {
            "geometry": geometry,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }
        return json.dumps(payload, sort_keys=True)

    async def store(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        scenes: List[SatelliteScene],
    ) -> None:
        self._store[self._key(geometry, start_date, end_date)] = scenes

    async def retrieve(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> List[SatelliteScene]:
        return self._store.get(self._key(geometry, start_date, end_date), [])
