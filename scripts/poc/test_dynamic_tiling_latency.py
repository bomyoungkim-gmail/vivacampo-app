#!/usr/bin/env python3
"""
PoC: Dynamic Tiling + MosaicJSON Latency Test

Testa latência real de:
1. Planetary Computer STAC search
2. Fetch de tiles COG direto do PC
3. Cálculo de NDVI on-the-fly
4. Comparação com/sem cache

Requisitos:
    pip install planetary-computer pystac-client rasterio httpx rich numpy

Uso:
    python test_dynamic_tiling_latency.py
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional
import statistics

# Core
import httpx
import numpy as np

# STAC
import planetary_computer
import pystac_client

# Raster
import rasterio
from rasterio.windows import from_bounds

# Pretty output
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# AOI de teste (fazenda real no Mato Grosso - ~500 hectares)
TEST_AOI = {
    "type": "Polygon",
    "coordinates": [[
        [-55.5, -12.5],
        [-55.4, -12.5],
        [-55.4, -12.4],
        [-55.5, -12.4],
        [-55.5, -12.5]
    ]]
}

TEST_BBOX = [-55.5, -12.5, -55.4, -12.4]  # minx, miny, maxx, maxy

# Período de teste
TEST_DATE_START = "2024-01-01"
TEST_DATE_END = "2024-01-15"

# Planetary Computer STAC
PC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

# TiTiler público do Planetary Computer
PC_TILER_URL = "https://planetarycomputer.microsoft.com/api/data/v1"

# Número de repetições para média
NUM_ITERATIONS = 3


# ============================================================================
# TESTES DE LATÊNCIA
# ============================================================================

async def test_stac_search() -> dict:
    """Teste 1: Busca no STAC catalog."""
    results = []
    scenes_found = 0

    for i in range(NUM_ITERATIONS):
        start = time.perf_counter()

        catalog = pystac_client.Client.open(
            PC_STAC_URL,
            modifier=planetary_computer.sign_inplace
        )

        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=TEST_BBOX,
            datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
            query={"eo:cloud_cover": {"lt": 30}}
        )

        items = list(search.items())
        scenes_found = len(items)

        elapsed = (time.perf_counter() - start) * 1000
        results.append(elapsed)

    return {
        "name": "STAC Search",
        "description": f"Buscar cenas Sentinel-2 ({scenes_found} encontradas)",
        "min_ms": min(results),
        "max_ms": max(results),
        "avg_ms": statistics.mean(results),
        "p95_ms": sorted(results)[int(len(results) * 0.95)] if len(results) > 1 else results[0]
    }


async def test_cog_tile_fetch() -> dict:
    """Teste 2: Fetch de tile COG direto do Planetary Computer."""
    results = []

    # Primeiro, buscar uma cena
    catalog = pystac_client.Client.open(
        PC_STAC_URL,
        modifier=planetary_computer.sign_inplace
    )

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=TEST_BBOX,
        datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=1
    )

    items = list(search.items())
    if not items:
        return {"name": "COG Tile Fetch", "error": "No scenes found"}

    item = items[0]
    b04_href = item.assets["B04"].href  # Red band

    for i in range(NUM_ITERATIONS):
        start = time.perf_counter()

        # Ler apenas a região do AOI (windowed read)
        with rasterio.open(b04_href) as src:
            # Converter bbox para window
            window = from_bounds(*TEST_BBOX, src.transform)
            data = src.read(1, window=window)

        elapsed = (time.perf_counter() - start) * 1000
        results.append(elapsed)

    return {
        "name": "COG Tile Fetch",
        "description": f"Ler banda B04 clipped ({data.shape})",
        "min_ms": min(results),
        "max_ms": max(results),
        "avg_ms": statistics.mean(results),
        "p95_ms": sorted(results)[int(len(results) * 0.95)] if len(results) > 1 else results[0]
    }


async def test_ndvi_calculation() -> dict:
    """Teste 3: Cálculo NDVI on-the-fly (2 bandas + math)."""
    results = []

    # Buscar cena
    catalog = pystac_client.Client.open(
        PC_STAC_URL,
        modifier=planetary_computer.sign_inplace
    )

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=TEST_BBOX,
        datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=1
    )

    items = list(search.items())
    if not items:
        return {"name": "NDVI Calculation", "error": "No scenes found"}

    item = items[0]
    b04_href = item.assets["B04"].href  # Red
    b08_href = item.assets["B08"].href  # NIR

    for i in range(NUM_ITERATIONS):
        start = time.perf_counter()

        # Ler ambas as bandas
        with rasterio.open(b04_href) as src:
            window = from_bounds(*TEST_BBOX, src.transform)
            red = src.read(1, window=window).astype(np.float32)

        with rasterio.open(b08_href) as src:
            window = from_bounds(*TEST_BBOX, src.transform)
            nir = src.read(1, window=window).astype(np.float32)

        # Calcular NDVI
        ndvi = (nir - red) / (nir + red + 1e-10)
        ndvi = np.clip(ndvi, -1, 1)

        elapsed = (time.perf_counter() - start) * 1000
        results.append(elapsed)

    return {
        "name": "NDVI Calculation",
        "description": f"B04 + B08 + calc ({red.shape})",
        "min_ms": min(results),
        "max_ms": max(results),
        "avg_ms": statistics.mean(results),
        "p95_ms": sorted(results)[int(len(results) * 0.95)] if len(results) > 1 else results[0]
    }


async def test_titiler_tile() -> dict:
    """Teste 4: Request para TiTiler do Planetary Computer (XYZ tile)."""
    results = []

    # Buscar cena para obter URL assinada
    catalog = pystac_client.Client.open(
        PC_STAC_URL,
        modifier=planetary_computer.sign_inplace
    )

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=TEST_BBOX,
        datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=1
    )

    items = list(search.items())
    if not items:
        return {"name": "TiTiler Tile", "error": "No scenes found"}

    item = items[0]

    # URL do TiTiler para tile específico
    # Zoom 13 é típico para visualização de fazendas
    z, x, y = 13, 2847, 4523  # Tile que cobre nossa área de teste

    # Construir URL do TiTiler com expressão NDVI
    cog_url = item.assets["B04"].href

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(NUM_ITERATIONS):
            start = time.perf_counter()

            # Request simples de tile PNG
            url = f"{PC_TILER_URL}/item/tiles/WebMercatorQuad/{z}/{x}/{y}.png"
            params = {
                "collection": "sentinel-2-l2a",
                "item": item.id,
                "assets": "B04",
                "colormap_name": "viridis"
            }

            response = await client.get(url, params=params)

            elapsed = (time.perf_counter() - start) * 1000
            results.append(elapsed)

    return {
        "name": "TiTiler Tile (PNG)",
        "description": f"Tile z={z} via PC TiTiler",
        "min_ms": min(results),
        "max_ms": max(results),
        "avg_ms": statistics.mean(results),
        "p95_ms": sorted(results)[int(len(results) * 0.95)] if len(results) > 1 else results[0],
        "status_code": response.status_code
    }


async def test_titiler_ndvi_expression() -> dict:
    """Teste 5: TiTiler com expressão NDVI (mais realista)."""
    results = []

    catalog = pystac_client.Client.open(
        PC_STAC_URL,
        modifier=planetary_computer.sign_inplace
    )

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=TEST_BBOX,
        datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=1
    )

    items = list(search.items())
    if not items:
        return {"name": "TiTiler NDVI Expression", "error": "No scenes found"}

    item = items[0]
    z, x, y = 13, 2847, 4523

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i in range(NUM_ITERATIONS):
            start = time.perf_counter()

            # Request com expressão NDVI
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

            elapsed = (time.perf_counter() - start) * 1000
            results.append(elapsed)

    return {
        "name": "TiTiler NDVI Expression",
        "description": f"Tile z={z} com expression NDVI",
        "min_ms": min(results),
        "max_ms": max(results),
        "avg_ms": statistics.mean(results),
        "p95_ms": sorted(results)[int(len(results) * 0.95)] if len(results) > 1 else results[0],
        "status_code": response.status_code
    }


async def test_multiple_tiles_parallel() -> dict:
    """Teste 6: Múltiplos tiles em paralelo (simula pan/zoom)."""
    results = []

    catalog = pystac_client.Client.open(
        PC_STAC_URL,
        modifier=planetary_computer.sign_inplace
    )

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=TEST_BBOX,
        datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=1
    )

    items = list(search.items())
    if not items:
        return {"name": "Parallel Tiles", "error": "No scenes found"}

    item = items[0]

    # 9 tiles (grid 3x3) - típico de uma viewport
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
        for i in range(NUM_ITERATIONS):
            start = time.perf_counter()

            # Fetch all tiles in parallel
            tasks = [fetch_tile(client, z, x, y) for z, x, y in tiles]
            responses = await asyncio.gather(*tasks)

            elapsed = (time.perf_counter() - start) * 1000
            results.append(elapsed)

    return {
        "name": "9 Tiles Parallel",
        "description": f"Grid 3x3 NDVI em paralelo",
        "min_ms": min(results),
        "max_ms": max(results),
        "avg_ms": statistics.mean(results),
        "p95_ms": sorted(results)[int(len(results) * 0.95)] if len(results) > 1 else results[0],
        "tiles_fetched": len(tiles),
        "all_success": all(r.status_code == 200 for r in responses)
    }


async def test_statistics_endpoint() -> dict:
    """Teste 7: Endpoint de estatísticas (para gráficos)."""
    results = []

    catalog = pystac_client.Client.open(
        PC_STAC_URL,
        modifier=planetary_computer.sign_inplace
    )

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=TEST_BBOX,
        datetime=f"{TEST_DATE_START}/{TEST_DATE_END}",
        query={"eo:cloud_cover": {"lt": 30}},
        limit=1
    )

    items = list(search.items())
    if not items:
        return {"name": "Statistics Endpoint", "error": "No scenes found"}

    item = items[0]

    async with httpx.AsyncClient(timeout=60.0) as client:
        for i in range(NUM_ITERATIONS):
            start = time.perf_counter()

            # Request stats para o AOI
            url = f"{PC_TILER_URL}/item/statistics"
            params = {
                "collection": "sentinel-2-l2a",
                "item": item.id,
                "assets": ["B04", "B08"],
                "expression": "(B08-B04)/(B08+B04)",
            }

            # POST com geometry
            response = await client.post(
                url,
                params=params,
                json=TEST_AOI
            )

            elapsed = (time.perf_counter() - start) * 1000
            results.append(elapsed)

    stats_data = response.json() if response.status_code == 200 else None

    return {
        "name": "Statistics (NDVI)",
        "description": f"Stats para AOI polygon",
        "min_ms": min(results),
        "max_ms": max(results),
        "avg_ms": statistics.mean(results),
        "p95_ms": sorted(results)[int(len(results) * 0.95)] if len(results) > 1 else results[0],
        "status_code": response.status_code,
        "has_stats": stats_data is not None
    }


# ============================================================================
# MAIN
# ============================================================================

async def main():
    console.print("\n[bold blue]═══════════════════════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]  PoC: Dynamic Tiling + MosaicJSON - Teste de Latência[/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════════════════════[/bold blue]\n")

    console.print(f"[dim]AOI de teste: Mato Grosso, ~500 hectares[/dim]")
    console.print(f"[dim]Período: {TEST_DATE_START} a {TEST_DATE_END}[/dim]")
    console.print(f"[dim]Iterações por teste: {NUM_ITERATIONS}[/dim]\n")

    tests = [
        ("STAC Search", test_stac_search),
        ("COG Tile Fetch", test_cog_tile_fetch),
        ("NDVI Calculation", test_ndvi_calculation),
        ("TiTiler Tile", test_titiler_tile),
        ("TiTiler NDVI", test_titiler_ndvi_expression),
        ("Parallel Tiles", test_multiple_tiles_parallel),
        ("Statistics", test_statistics_endpoint),
    ]

    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for name, test_func in tests:
            task = progress.add_task(f"Testando {name}...", total=None)
            try:
                result = await test_func()
                results.append(result)
                progress.update(task, completed=True)
            except Exception as e:
                results.append({"name": name, "error": str(e)})
                progress.update(task, completed=True)

    # Exibir resultados
    console.print("\n[bold green]═══════════════════════════════════════════════════════════════[/bold green]")
    console.print("[bold green]  RESULTADOS[/bold green]")
    console.print("[bold green]═══════════════════════════════════════════════════════════════[/bold green]\n")

    table = Table(title="Latência por Operação")
    table.add_column("Operação", style="cyan")
    table.add_column("Descrição", style="dim")
    table.add_column("Min", justify="right")
    table.add_column("Avg", justify="right", style="bold")
    table.add_column("Max", justify="right")
    table.add_column("p95", justify="right")

    for r in results:
        if "error" in r:
            table.add_row(r["name"], f"[red]ERROR: {r['error']}[/red]", "-", "-", "-", "-")
        else:
            table.add_row(
                r["name"],
                r.get("description", ""),
                f"{r['min_ms']:.0f}ms",
                f"{r['avg_ms']:.0f}ms",
                f"{r['max_ms']:.0f}ms",
                f"{r['p95_ms']:.0f}ms"
            )

    console.print(table)

    # Análise
    console.print("\n[bold yellow]═══════════════════════════════════════════════════════════════[/bold yellow]")
    console.print("[bold yellow]  ANÁLISE[/bold yellow]")
    console.print("[bold yellow]═══════════════════════════════════════════════════════════════[/bold yellow]\n")

    # Calcular latência total típica
    stac_result = next((r for r in results if r["name"] == "STAC Search"), None)
    ndvi_result = next((r for r in results if r["name"] == "TiTiler NDVI Expression"), None)
    parallel_result = next((r for r in results if r["name"] == "9 Tiles Parallel"), None)
    stats_result = next((r for r in results if r["name"] == "Statistics (NDVI)"), None)

    if all([stac_result, ndvi_result, parallel_result]):
        console.print("[bold]Cenário: Usuário abre mapa de AOI (sem cache)[/bold]")
        console.print(f"  • STAC search: ~{stac_result.get('avg_ms', 0):.0f}ms")
        console.print(f"  • 9 tiles NDVI: ~{parallel_result.get('avg_ms', 0):.0f}ms")
        total = stac_result.get('avg_ms', 0) + parallel_result.get('avg_ms', 0)
        console.print(f"  • [bold]TOTAL: ~{total:.0f}ms ({total/1000:.1f}s)[/bold]")

        console.print(f"\n[bold]Cenário: Usuário navega (cache hit esperado com CDN)[/bold]")
        console.print(f"  • CDN edge cache: ~50ms")

        console.print(f"\n[bold]Cenário: Carregar gráfico de estatísticas[/bold]")
        if stats_result and "error" not in stats_result:
            console.print(f"  • Stats endpoint: ~{stats_result.get('avg_ms', 0):.0f}ms")

    # Veredicto
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  VEREDICTO[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]\n")

    if parallel_result and "error" not in parallel_result:
        avg_ms = parallel_result.get("avg_ms", 9999)
        if avg_ms < 2000:
            console.print("[bold green]✅ VIÁVEL[/bold green] - Latência aceitável para UX")
            console.print(f"   Grid 3x3 em {avg_ms:.0f}ms (< 2s threshold)")
        elif avg_ms < 5000:
            console.print("[bold yellow]⚠️  VIÁVEL COM RESSALVAS[/bold yellow] - Precisa de cache warming")
            console.print(f"   Grid 3x3 em {avg_ms:.0f}ms (2-5s, OK com loading state)")
        else:
            console.print("[bold red]❌ PROBLEMÁTICO[/bold red] - Latência muito alta")
            console.print(f"   Grid 3x3 em {avg_ms:.0f}ms (> 5s, UX ruim)")

    console.print("\n[dim]Nota: Estes testes são sem CDN cache. Com Cloudflare, espera-se ~50ms para cache hits.[/dim]")
    console.print("[dim]      Em produção, 80-90% dos requests serão cache hits após warm-up.[/dim]\n")


if __name__ == "__main__":
    asyncio.run(main())
