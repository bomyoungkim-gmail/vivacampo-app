import asyncio
from datetime import datetime
from typing import Any, Dict, List

from worker.domain.ports.satellite_provider import ISatelliteProvider, SatelliteScene
from worker.infrastructure.adapters.satellite.resilient_satellite_adapter import ResilientSatelliteAdapter


class _StubProvider(ISatelliteProvider):
    def __init__(self, name: str, scenes: List[SatelliteScene], fail: bool = False):
        self._name = name
        self._scenes = scenes
        self._fail = fail
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return self._name

    async def search_scenes(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        collections=None,
        max_cloud_cover: float = 60.0,
    ) -> List[SatelliteScene]:
        self.calls += 1
        if self._fail:
            raise RuntimeError("fail")
        return self._scenes

    async def download_band(self, asset_href: str, geometry: Dict[str, Any], output_path: str) -> str:
        self.calls += 1
        if self._fail:
            raise RuntimeError("fail")
        return output_path

    async def health_check(self) -> bool:
        return not self._fail


def _scene() -> SatelliteScene:
    return SatelliteScene(
        id="scene-1",
        datetime=datetime.utcnow(),
        cloud_cover=0.0,
        platform="sentinel",
        collection="sentinel-2-l2a",
        bbox=[0, 0, 1, 1],
        geometry={"type": "Point", "coordinates": [0, 0]},
        assets={},
    )


def test_resilient_adapter_uses_fallback_when_primary_fails():
    primary = _StubProvider("primary", scenes=[], fail=True)
    fallback = _StubProvider("fallback", scenes=[_scene()], fail=False)
    adapter = ResilientSatelliteAdapter(primary=primary, fallback=fallback, circuit_failure_threshold=1)

    scenes = asyncio.run(adapter.search_scenes({}, datetime.utcnow(), datetime.utcnow()))
    assert len(scenes) == 1
    assert primary.calls == 1
    assert fallback.calls == 1


def test_resilient_adapter_skips_primary_when_circuit_open():
    primary = _StubProvider("primary", scenes=[], fail=True)
    fallback = _StubProvider("fallback", scenes=[_scene()], fail=False)
    adapter = ResilientSatelliteAdapter(
        primary=primary,
        fallback=fallback,
        circuit_failure_threshold=1,
        circuit_recovery_timeout_seconds=9999,
    )

    asyncio.run(adapter.search_scenes({}, datetime.utcnow(), datetime.utcnow()))
    asyncio.run(adapter.search_scenes({}, datetime.utcnow(), datetime.utcnow()))

    assert primary.calls == 1
    assert fallback.calls == 2
