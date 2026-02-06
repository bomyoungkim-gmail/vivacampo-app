import asyncio
from datetime import datetime

from worker.infrastructure.adapters.satellite.memory_cache import MemorySatelliteCache
from worker.domain.ports.satellite_provider import SatelliteScene


def _scene():
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


def test_memory_cache_store_retrieve():
    cache = MemorySatelliteCache()
    scene = _scene()
    geom = {"type": "Point", "coordinates": [0, 0]}
    start = datetime.utcnow()
    end = datetime.utcnow()

    async def run():
        await cache.store(geom, start, end, [scene])
        return await cache.retrieve(geom, start, end)

    scenes = asyncio.run(run())
    assert len(scenes) == 1
    assert scenes[0].id == "scene-1"
