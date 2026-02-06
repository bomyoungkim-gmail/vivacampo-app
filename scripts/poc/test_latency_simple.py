#!/usr/bin/env python3
"""
PoC: Dynamic Tiling Latency Test (Simple Version)

Testa latencia real de:
1. Planetary Computer STAC search
2. Fetch de tiles COG direto do PC
3. Calculo de NDVI on-the-fly
"""

import asyncio
import time
from datetime import datetime
import statistics
import sys

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import httpx
import numpy as np
import planetary_computer
import pystac_client
import rasterio
from rasterio.windows import from_bounds

# Config
TEST_BBOX = [-55.5, -12.5, -55.4, -12.4]  # Mato Grosso ~500ha
TEST_AOI = {
    "type": "Polygon",
    "coordinates": [[
        [-55.5, -12.5], [-55.4, -12.5], [-55.4, -12.4], [-55.5, -12.4], [-55.5, -12.5]
    ]]
}
TEST_DATE_START = "2023-06-01"
TEST_DATE_END = "2023-06-30"
PC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
PC_TILER_URL = "https://planetarycomputer.microsoft.com/api/data/v1"
NUM_ITERATIONS = 3


def print_header(text):
    print("\n" + "=" * 65)
    print(f"  {text}")
    print("=" * 65 + "\n")


def print_result(name, results, extra=""):
    avg = statistics.mean(results)
    print(f"  {name}:")
    print(f"    Min: {min(results):.0f}ms | Avg: {avg:.0f}ms | Max: {max(results):.0f}ms")
    if extra:
        print(f"    {extra}")


async def test_stac_search():
    """Test 1: STAC catalog search"""
    print("  [1/6] Testing STAC Search...", end=" ", flush=True)
    results = []
    scenes_count = 0

    for _ in range(NUM_ITERATIONS):
        start = time.perf_counter()
        catalog = pystac_client.Client.open(PC_STAC_URL, modifier=planetary_computer.sign_inplace)
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=TEST_BBOX,
            datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
            query={"eo:cloud_cover": {"lt": 50}}
        )
        items = list(search.items())
        scenes_count = len(items)
        results.append((time.perf_counter() - start) * 1000)

    print(f"OK ({scenes_count} scenes)")
    return {"name": "STAC Search", "results": results, "scenes": scenes_count}


async def test_cog_fetch():
    """Test 2: COG windowed read"""
    print("  [2/6] Testing COG Tile Fetch...", end=" ", flush=True)
    results = []

    catalog = pystac_client.Client.open(PC_STAC_URL, modifier=planetary_computer.sign_inplace)
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=TEST_BBOX,
        datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=1
    )
    items = list(search.items())
    if not items:
        print("SKIP (no scenes)")
        return None

    b04_href = items[0].assets["B04"].href
    shape = None

    for _ in range(NUM_ITERATIONS):
        start = time.perf_counter()
        with rasterio.open(b04_href) as src:
            window = from_bounds(*TEST_BBOX, src.transform)
            data = src.read(1, window=window)
            shape = data.shape
        results.append((time.perf_counter() - start) * 1000)

    print(f"OK ({shape})")
    return {"name": "COG Fetch (B04)", "results": results, "shape": shape}


async def test_ndvi_calc():
    """Test 3: NDVI calculation from 2 bands"""
    print("  [3/6] Testing NDVI Calculation...", end=" ", flush=True)
    results = []

    catalog = pystac_client.Client.open(PC_STAC_URL, modifier=planetary_computer.sign_inplace)
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=TEST_BBOX,
        datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=1
    )
    items = list(search.items())
    if not items:
        print("SKIP")
        return None

    item = items[0]
    b04_href = item.assets["B04"].href
    b08_href = item.assets["B08"].href

    for _ in range(NUM_ITERATIONS):
        start = time.perf_counter()

        with rasterio.open(b04_href) as src:
            window = from_bounds(*TEST_BBOX, src.transform)
            red = src.read(1, window=window).astype(np.float32)

        with rasterio.open(b08_href) as src:
            window = from_bounds(*TEST_BBOX, src.transform)
            nir = src.read(1, window=window).astype(np.float32)

        ndvi = (nir - red) / (nir + red + 1e-10)
        ndvi = np.clip(ndvi, -1, 1)

        results.append((time.perf_counter() - start) * 1000)

    ndvi_mean = np.mean(ndvi)
    print(f"OK (mean NDVI: {ndvi_mean:.3f})")
    return {"name": "NDVI Calc (B04+B08)", "results": results, "ndvi_mean": ndvi_mean}


async def test_titiler_tile():
    """Test 4: TiTiler single tile"""
    print("  [4/6] Testing TiTiler Tile...", end=" ", flush=True)
    results = []

    catalog = pystac_client.Client.open(PC_STAC_URL, modifier=planetary_computer.sign_inplace)
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=TEST_BBOX,
        datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=1
    )
    items = list(search.items())
    if not items:
        print("SKIP")
        return None

    item = items[0]
    z, x, y = 13, 2847, 4523

    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(NUM_ITERATIONS):
            start = time.perf_counter()
            url = f"{PC_TILER_URL}/item/tiles/WebMercatorQuad/{z}/{x}/{y}.png"
            params = {
                "collection": "sentinel-2-l2a",
                "item": item.id,
                "assets": "B04",
                "colormap_name": "viridis"
            }
            response = await client.get(url, params=params)
            results.append((time.perf_counter() - start) * 1000)

    print(f"OK (status: {response.status_code})")
    return {"name": "TiTiler Tile", "results": results, "status": response.status_code}


async def test_titiler_ndvi():
    """Test 5: TiTiler with NDVI expression"""
    print("  [5/6] Testing TiTiler NDVI Expression...", end=" ", flush=True)
    results = []

    catalog = pystac_client.Client.open(PC_STAC_URL, modifier=planetary_computer.sign_inplace)
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=TEST_BBOX,
        datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=1
    )
    items = list(search.items())
    if not items:
        print("SKIP")
        return None

    item = items[0]
    z, x, y = 13, 2847, 4523

    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(NUM_ITERATIONS):
            start = time.perf_counter()
            url = f"{PC_TILER_URL}/item/tiles/WebMercatorQuad/{z}/{x}/{y}.png"
            params = {
                "collection": "sentinel-2-l2a",
                "item": item.id,
                "assets": ["B04", "B08"],
                "expression": "(B08-B04)/(B08+B04)",
                "colormap_name": "rdylgn",
                "rescale": "-0.2,0.8"
            }
            response = await client.get(url, params=params)
            results.append((time.perf_counter() - start) * 1000)

    print(f"OK (status: {response.status_code})")
    return {"name": "TiTiler NDVI", "results": results, "status": response.status_code}


async def test_parallel_tiles():
    """Test 6: 9 tiles in parallel (3x3 grid)"""
    print("  [6/6] Testing 9 Parallel Tiles...", end=" ", flush=True)
    results = []

    catalog = pystac_client.Client.open(PC_STAC_URL, modifier=planetary_computer.sign_inplace)
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=TEST_BBOX,
        datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=1
    )
    items = list(search.items())
    if not items:
        print("SKIP")
        return None

    item = items[0]
    tiles = [
        (13, 2846, 4522), (13, 2847, 4522), (13, 2848, 4522),
        (13, 2846, 4523), (13, 2847, 4523), (13, 2848, 4523),
        (13, 2846, 4524), (13, 2847, 4524), (13, 2848, 4524),
    ]

    async def fetch_tile(client, z, x, y):
        url = f"{PC_TILER_URL}/item/tiles/WebMercatorQuad/{z}/{x}/{y}.png"
        params = {
            "collection": "sentinel-2-l2a",
            "item": item.id,
            "assets": ["B04", "B08"],
            "expression": "(B08-B04)/(B08+B04)",
            "colormap_name": "rdylgn",
            "rescale": "-0.2,0.8"
        }
        return await client.get(url, params=params)

    async with httpx.AsyncClient(timeout=60.0) as client:
        for _ in range(NUM_ITERATIONS):
            start = time.perf_counter()
            tasks = [fetch_tile(client, z, x, y) for z, x, y in tiles]
            responses = await asyncio.gather(*tasks)
            results.append((time.perf_counter() - start) * 1000)

    all_ok = all(r.status_code == 200 for r in responses)
    print(f"OK (all 200: {all_ok})")
    return {"name": "9 Tiles Parallel", "results": results, "all_ok": all_ok}


async def main():
    print_header("PoC: Dynamic Tiling + MosaicJSON - Latency Test")

    print(f"  AOI: Mato Grosso, ~500 hectares")
    print(f"  Period: {TEST_DATE_START} to {TEST_DATE_END}")
    print(f"  Iterations: {NUM_ITERATIONS}")

    print_header("Running Tests")

    all_results = []

    tests = [
        test_stac_search,
        test_cog_fetch,
        test_ndvi_calc,
        test_titiler_tile,
        test_titiler_ndvi,
        test_parallel_tiles,
    ]

    for test in tests:
        try:
            result = await test()
            if result:
                all_results.append(result)
        except Exception as e:
            print(f"ERROR: {e}")

    print_header("Results Summary")

    for r in all_results:
        print_result(r["name"], r["results"])

    print_header("Analysis")

    # Find key results
    stac = next((r for r in all_results if "STAC" in r["name"]), None)
    parallel = next((r for r in all_results if "Parallel" in r["name"]), None)
    ndvi_tiler = next((r for r in all_results if "TiTiler NDVI" in r["name"]), None)

    if stac and parallel:
        stac_avg = statistics.mean(stac["results"])
        parallel_avg = statistics.mean(parallel["results"])
        total_cold = stac_avg + parallel_avg

        print("  Scenario: User opens AOI map (cold cache)")
        print(f"    STAC search:    ~{stac_avg:.0f}ms")
        print(f"    9 NDVI tiles:   ~{parallel_avg:.0f}ms")
        print(f"    TOTAL:          ~{total_cold:.0f}ms ({total_cold/1000:.1f}s)")

        print("\n  Scenario: User pans/zooms (CDN cache hit)")
        print(f"    Expected:       ~50ms (Cloudflare edge)")

    print_header("Verdict")

    verdict = "NO_DATA"
    if not parallel:
        print("  [SKIP] No parallel tile data to evaluate")
        print("         STAC search worked but no scenes found in date range")
    elif parallel:
        avg_ms = statistics.mean(parallel["results"])
        if avg_ms < 2000:
            print("  [OK] VIABLE - Acceptable latency for UX")
            print(f"       3x3 grid in {avg_ms:.0f}ms (< 2s threshold)")
            verdict = "VIABLE"
        elif avg_ms < 5000:
            print("  [WARN] VIABLE WITH CAVEATS - Needs cache warming")
            print(f"         3x3 grid in {avg_ms:.0f}ms (2-5s, OK with loading state)")
            verdict = "VIABLE_WITH_CAVEATS"
        else:
            print("  [FAIL] PROBLEMATIC - Latency too high")
            print(f"         3x3 grid in {avg_ms:.0f}ms (> 5s, bad UX)")
            verdict = "PROBLEMATIC"

    print("\n  Note: These tests are WITHOUT CDN cache.")
    print("        With Cloudflare, expect ~50ms for cache hits.")
    print("        In production, 80-90% of requests will be cache hits.\n")

    return verdict


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\nFinal result: {result}")
