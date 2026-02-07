import asyncio
from datetime import datetime, timezone

from worker.infrastructure.adapters.satellite.planetary_computer_adapter import PlanetaryComputerAdapter


class _StubSatelliteProvider:
    async def search_scenes(self, aoi_geom, start_date, end_date, max_cloud_cover=60.0, collections=None):
        return [
            {
                "id": "ok-1",
                "datetime": datetime.now(timezone.utc).isoformat(),
                "cloud_cover": 10.0,
                "platform": "sentinel",
                "assets": {},
                "bbox": [0, 0, 1, 1],
                "geometry": {"type": "Point", "coordinates": [0, 0]},
            },
            {
                "id": "bad-1",
                "datetime": "invalid",
                "cloud_cover": 10.0,
                "platform": "sentinel",
                "assets": {},
                "bbox": [0, 0, 1, 1],
                "geometry": {"type": "Point", "coordinates": [0, 0]},
            },
        ]

    async def download_and_clip_band(self, asset_href, geometry, output_path):
        return output_path

    async def health_check(self):
        return True


def test_planetary_adapter_filters_invalid_items(monkeypatch):
    from worker.infrastructure.adapters.satellite import planetary_computer_adapter as module

    monkeypatch.setattr(module, "get_satellite_provider", lambda: _StubSatelliteProvider())

    adapter = PlanetaryComputerAdapter()
    scenes = asyncio.run(adapter.search_scenes({}, datetime.now(timezone.utc), datetime.now(timezone.utc)))

    assert len(scenes) == 1
    assert scenes[0].id == "ok-1"
