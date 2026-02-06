# Plano de Implementacao: Data Provider Resilience

**Objetivo:** Implementar 4 camadas de resiliencia para data providers do VivaCampo.
**Prioridade:** P0 (pre-requisito para producao confiavel)
**Data:** 2026-02-05

---

## Indice

1. [FASE 1: Interface `SatelliteDataProvider` + Adapter Pattern](#fase-1)
2. [FASE 2: Implementacao de Providers Alternativos](#fase-2)
3. [FASE 3: Cache de Metadados STAC + Reprocessamento](#fase-3)
4. [FASE 4: Fallback Chain com Circuit Breaker](#fase-4)

---

## FASE 1: Interface `SatelliteDataProvider` + Adapter Pattern {#fase-1}

### Contexto

Hoje existe uma unica classe `STACClient` em `services/worker/worker/pipeline/stac_client.py` (~452 linhas) que mistura:
- Busca STAC (search_scenes)
- Download de assets (download_and_clip_band, _download_asset)
- URL signing (planetary_computer.sign)
- Calculo de indices (calculate_ndvi, calculate_ndwi, etc.)
- Fetch de weather (fetch_weather_history)
- Mascara de nuvens (mask_clouds)

O objetivo e separar responsabilidades e criar uma interface que permita trocar providers sem alterar os jobs.

### Etapa 1.1: Criar o Protocol/ABC `SatelliteDataProvider`

**Arquivo:** `services/worker/worker/pipeline/providers/base.py` (NOVO)

```python
"""
Abstract base for satellite data providers.
All providers must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np


class SatelliteDataProvider(ABC):
    """
    Interface que todo data provider de satelite deve implementar.

    Responsabilidades:
    - Buscar cenas de satelite (search_scenes)
    - Assinar URLs para download (sign_url)
    - Baixar e recortar bandas (download_and_clip_band)

    NAO inclui:
    - Calculo de indices (responsabilidade de IndexCalculator)
    - Weather data (responsabilidade de WeatherProvider)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nome unico do provider (ex: 'planetary_computer', 'cdse', 'aws_sentinel')"""
        ...

    @property
    @abstractmethod
    def supported_collections(self) -> List[str]:
        """Colecoes suportadas por este provider (ex: ['sentinel-2-l2a', 'sentinel-1-rtc'])"""
        ...

    @abstractmethod
    async def search_scenes(
        self,
        aoi_geom: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Buscar cenas de satelite que cobrem a AOI.

        Retorno padronizado:
        [
            {
                "id": str,
                "datetime": str (ISO),
                "cloud_cover": float,
                "platform": str,
                "assets": {
                    "red": str | None,    # href para B04
                    "green": str | None,  # href para B03
                    "blue": str | None,   # href para B02
                    "nir": str | None,    # href para B08
                    "swir": str | None,   # href para B11
                    "swir2": str | None,  # href para B12
                    "rededge": str | None,# href para B05
                    "scl": str | None,    # href para SCL
                    "vv": str | None,     # Sentinel-1
                    "vh": str | None,     # Sentinel-1
                    "dem": str | None,    # DEM
                },
                "bbox": List[float],
                "geometry": Dict[str, Any],  # GeoJSON
            }
        ]
        """
        ...

    @abstractmethod
    async def download_and_clip_band(
        self,
        asset_href: str,
        aoi_geom: Dict[str, Any],
        output_path: str
    ) -> np.ndarray:
        """
        Baixar asset, recortar pela AOI e salvar como GeoTIFF.

        - Deve assinar URL internamente (se necessario)
        - Deve reprojetar AOI para CRS do raster
        - Retorna array da primeira banda
        """
        ...

    @abstractmethod
    def sign_url(self, href: str) -> str:
        """
        Assinar URL para acesso direto (SAS token, presigned, etc).
        Se provider nao exige assinatura, retorna href original.
        """
        ...

    @abstractmethod
    async def search_raw_items(
        self,
        bbox: List[float],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None,
        max_items: int = 2000,
    ):
        """
        Buscar STAC items crus (pystac.Item) para uso em MosaicJSON builder.
        Diferente de search_scenes() que retorna dicts simplificados,
        este metodo retorna os objetos pystac.Item com links e assets originais.

        Necessario para create_mosaic.py que precisa de:
        - item.links (self link)
        - item.assets (nomes originais do provider)
        - item.bbox
        - item.id

        Args:
            bbox: Bounding box [minx, miny, maxx, maxy]
            start_date, end_date: Range temporal
            max_cloud_cover: Filtro de nuvens
            collections: Colecoes STAC
            max_items: Limite de items

        Returns:
            Lista de pystac.Item (objetos crus, nao dicts)
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verificar se o provider esta acessivel.
        Usado pelo circuit breaker para testar half-open state.
        Deve ter timeout curto (5s max).
        """
        ...


class WeatherDataProvider(ABC):
    """
    Interface para providers de dados meteorologicos.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    async def fetch_history(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        timezone: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        Buscar historico meteorologico.

        Retorno padronizado:
        [
            {
                "date": str (YYYY-MM-DD),
                "temp_max": float,
                "temp_min": float,
                "precip_sum": float,
                "et0_fao": float,
            }
        ]
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
```

**Criterios de aceite:**
- [ ] Arquivo criado em `services/worker/worker/pipeline/providers/base.py`
- [ ] `__init__.py` criado em `services/worker/worker/pipeline/providers/`
- [ ] Imports funcionando: `from worker.pipeline.providers.base import SatelliteDataProvider, WeatherDataProvider`

### Etapa 1.2: Extrair `IndexCalculator` do STACClient

Os metodos de calculo de indices NAO pertencem ao data provider. Devem ser extraidos para uma classe utilitaria independente.

**Arquivo:** `services/worker/worker/pipeline/index_calculator.py` (NOVO)

```python
"""
Calculo de indices de vegetacao e radar.
Independente de provider - opera sobre numpy arrays.
"""
import numpy as np


class IndexCalculator:
    """Calcula indices de vegetacao e radar a partir de arrays numpy."""

    @staticmethod
    def ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """NDVI = (NIR - Red) / (NIR + Red)"""
        denom = nir + red
        denom = np.where(denom == 0, 0.0001, denom)
        return np.clip((nir - red) / denom, -1, 1)

    @staticmethod
    def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """NDWI = (Green - NIR) / (Green + NIR)"""
        denom = green + nir
        denom = np.where(denom == 0, 0.0001, denom)
        return np.clip((green - nir) / denom, -1, 1)

    @staticmethod
    def ndmi(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """NDMI = (NIR - SWIR) / (NIR + SWIR)"""
        denom = nir + swir
        denom = np.where(denom == 0, 0.0001, denom)
        return np.clip((nir - swir) / denom, -1, 1)

    @staticmethod
    def savi(red: np.ndarray, nir: np.ndarray, L: float = 0.5) -> np.ndarray:
        """SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)"""
        denom = nir + red + L
        denom = np.where(denom == 0, 0.0001, denom)
        return np.clip(((nir - red) / denom) * (1 + L), -1, 1)

    @staticmethod
    def rvi(vv: np.ndarray, vh: np.ndarray) -> np.ndarray:
        """RVI = 4 * VH / (VV + VH). Range: 0-1."""
        denominator = vv + vh
        denominator = np.where(denominator == 0, 0.0001, denominator)
        return np.clip(4 * vh / denominator, 0, 1)

    @staticmethod
    def radar_ratio(vv: np.ndarray, vh: np.ndarray) -> np.ndarray:
        """VH/VV Ratio"""
        vv = np.where(vv == 0, 0.0001, vv)
        return vh / vv

    @staticmethod
    def mask_clouds(data_array: np.ndarray, scl_array: np.ndarray) -> np.ndarray:
        """
        Mascara de nuvens usando SCL (Scene Classification Layer).
        Invalida pixels: 0=NoData, 1=Saturated, 3=CloudShadow, 8=CloudMedium, 9=CloudHigh, 10=Cirrus.
        """
        # Resize SCL se resolucao diferente (20m vs 10m)
        if data_array.shape[-2:] != scl_array.shape[-2:]:
            target_h, target_w = data_array.shape[-2:]
            scl_h, scl_w = scl_array.shape[-2:]
            scale_h = target_h / scl_h
            scale_w = target_w / scl_w
            y_coords = np.arange(target_h) / scale_h
            x_coords = np.arange(target_w) / scale_w
            y_indices = np.clip(np.round(y_coords).astype(int), 0, scl_h - 1)
            x_indices = np.clip(np.round(x_coords).astype(int), 0, scl_w - 1)
            scl_array = scl_array[y_indices[:, None], x_indices]

        invalid_pixels = np.isin(scl_array, [0, 1, 3, 8, 9, 10])
        return np.where(invalid_pixels, np.nan, data_array)
```

**Criterios de aceite:**
- [ ] `IndexCalculator` criado com todos os metodos estaticos
- [ ] Testes unitarios em `tests/test_index_calculator.py` cobrindo cada indice
- [ ] `mask_clouds` inclui logica de resize SCL (copiada do STACClient atual)

### Etapa 1.3: Refatorar STACClient atual como `PlanetaryComputerProvider`

**Arquivo:** `services/worker/worker/pipeline/providers/planetary_computer.py` (NOVO)

Mover o STACClient atual para implementar a interface `SatelliteDataProvider`:

```python
"""
Planetary Computer STAC provider.
Implementa SatelliteDataProvider usando Microsoft Planetary Computer.
"""
import structlog
import asyncio
import os
import time
import socket
import tempfile
import urllib.request
from typing import List, Dict, Any, Optional
from datetime import datetime

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom
from shapely.geometry import shape, mapping
from pystac_client import Client
from pystac_client.stac_api_io import StacApiIO
from pystac_client.exceptions import APIError
from urllib3 import Retry
from requests.exceptions import RequestException, Timeout as RequestsTimeout
from tenacity import Retrying, stop_after_attempt, wait_exponential, retry_if_exception_type
import planetary_computer

from worker.pipeline.providers.base import SatelliteDataProvider

logger = structlog.get_logger()


class PlanetaryComputerProvider(SatelliteDataProvider):
    """
    Microsoft Planetary Computer STAC provider.

    Catalogo: https://planetarycomputer.microsoft.com/api/stac/v1
    Colecoes: sentinel-2-l2a, sentinel-1-rtc, copernicus-dem-glo-30
    Autenticacao: SAS tokens via planetary_computer.sign()
    """

    CATALOG_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

    # Mapeamento de bandas por colecao (padrao da interface -> nome do asset PC)
    BAND_MAPPING = {
        "sentinel-2-l2a": {
            "red": "B04", "green": "B03", "blue": "B02",
            "nir": "B08", "swir": "B11", "swir2": "B12",
            "rededge": "B05", "scl": "SCL",
        },
        "sentinel-1-rtc": {
            "vv": "vv", "vh": "vh",
        },
        "copernicus-dem-glo-30": {
            "dem": "data",
        },
    }

    def __init__(self, catalog_url: str | None = None):
        self._catalog_url = catalog_url or self.CATALOG_URL
        self._client = None
        self.search_limit = 50
        self.search_max_items = 100
        self.search_timeout = (5, 60)
        self.search_max_retries = 5

    @property
    def provider_name(self) -> str:
        return "planetary_computer"

    @property
    def supported_collections(self) -> List[str]:
        return ["sentinel-2-l2a", "sentinel-1-rtc", "copernicus-dem-glo-30"]

    def _get_client(self):
        """Lazy initialization do STAC client."""
        if self._client is None:
            retry = Retry(
                total=self.search_max_retries,
                backoff_factor=1,
                status_forcelist=[502, 503, 504],
                allowed_methods=None,
                respect_retry_after_header=True,
                raise_on_status=False,
            )
            stac_io = StacApiIO(max_retries=retry, timeout=self.search_timeout)
            self._client = Client.open(self._catalog_url, stac_io=stac_io)
            logger.info("provider_initialized", provider=self.provider_name, catalog=self._catalog_url)
        return self._client

    async def search_scenes(
        self,
        aoi_geom: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Buscar cenas no Planetary Computer STAC."""
        if collections is None:
            collections = ["sentinel-2-l2a"]

        client = self._get_client()

        try:
            bounds = shape(aoi_geom).bounds
        except Exception:
            bounds = None

        logger.info("stac_search_start", provider=self.provider_name,
                     start_date=str(start_date), end_date=str(end_date),
                     collections=collections, max_cloud_cover=max_cloud_cover)

        query = {}
        if "sentinel-2-l2a" in collections:
            query["eo:cloud_cover"] = {"lt": max_cloud_cover}

        search_kwargs = {
            "collections": collections,
            "datetime": f"{start_date.isoformat()}/{end_date.isoformat()}",
            "query": query,
            "limit": self.search_limit,
            "max_items": self.search_max_items,
        }
        if bounds:
            search_kwargs["bbox"] = list(bounds)
        else:
            search_kwargs["intersects"] = aoi_geom

        retryer = Retrying(
            stop=stop_after_attempt(4),
            wait=wait_exponential(multiplier=1, min=1, max=15),
            retry=retry_if_exception_type((APIError, RequestException, RequestsTimeout)),
            reraise=True,
        )
        for attempt in retryer:
            with attempt:
                search = client.search(**search_kwargs)
                items = list(search.items())

        logger.info("stac_search_completed", provider=self.provider_name,
                     scenes_found=len(items), collections=collections)

        # Converter para formato padronizado
        scenes = []
        for item in items:
            collection_id = item.collection_id
            band_map = self.BAND_MAPPING.get(collection_id, {})

            assets = {}
            for standard_name, pc_name in band_map.items():
                asset = item.assets.get(pc_name)
                assets[standard_name] = asset.href if asset else None

            scenes.append({
                "id": item.id,
                "datetime": item.datetime.isoformat(),
                "cloud_cover": item.properties.get("eo:cloud_cover", 0),
                "platform": item.properties.get("platform", "unknown"),
                "assets": assets,
                "bbox": item.bbox,
                "geometry": mapping(shape(item.geometry)),
            })

        return scenes

    async def search_raw_items(
        self,
        bbox,
        start_date,
        end_date,
        max_cloud_cover=60.0,
        collections=None,
        max_items=2000,
    ):
        """Retorna pystac.Item crus para MosaicJSON builder."""
        if collections is None:
            collections = ["sentinel-2-l2a"]

        client = self._get_client()

        query = {}
        if "sentinel-2-l2a" in collections:
            query["eo:cloud_cover"] = {"lt": max_cloud_cover}

        search = client.search(
            collections=collections,
            bbox=bbox,
            datetime=f"{start_date}/{end_date}",
            query=query if query else None,
            max_items=max_items,
        )

        return list(search.items())

    def sign_url(self, href: str) -> str:
        """Assinar URL com SAS token do Planetary Computer."""
        try:
            signed = planetary_computer.sign(href)
            return signed
        except Exception as e:
            logger.warning("pc_signing_failed_fallback", error=str(e))
            return href

    async def download_and_clip_band(
        self,
        asset_href: str,
        aoi_geom: Dict[str, Any],
        output_path: str
    ) -> np.ndarray:
        """Baixar e recortar banda usando urllib (mais estavel em containers)."""
        local_path = None
        try:
            local_path = await asyncio.to_thread(self._download_asset, asset_href)

            with rasterio.open(local_path) as src:
                aoi_projected = transform_geom("EPSG:4326", src.crs, aoi_geom)
                geom = [shape(aoi_projected)]
                out_image, out_transform = mask(src, geom, crop=True)
                out_meta = src.meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                })
                with rasterio.open(output_path, "w", **out_meta) as dest:
                    dest.write(out_image)
                return out_image[0]
        finally:
            if local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except Exception:
                    pass

    def _download_asset(self, href: str) -> str:
        """Download com retry e SAS token signing."""
        signed_href = self.sign_url(href)
        max_attempts = 5

        for attempt in range(max_attempts):
            try:
                socket.setdefaulttimeout(30)
                fd, temp_path = tempfile.mkstemp(suffix=".tif")
                os.close(fd)

                with urllib.request.urlopen(signed_href) as response:
                    with open(temp_path, 'wb') as f:
                        while True:
                            chunk = response.read(16 * 1024)
                            if not chunk:
                                break
                            f.write(chunk)

                return temp_path
            except Exception as e:
                logger.error("download_error", provider=self.provider_name,
                           error=str(e), attempt=attempt + 1)
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise

    async def health_check(self) -> bool:
        """Verificar se Planetary Computer STAC esta acessivel."""
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._catalog_url}/",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False
```

**Criterios de aceite:**
- [ ] `PlanetaryComputerProvider` implementa todos os metodos de `SatelliteDataProvider`
- [ ] Toda logica de `stac_client.py` migrada (search, download, sign)
- [ ] Formato de retorno de `search_scenes` identico ao atual (nao quebrar jobs)
- [ ] `health_check` funcional (GET no endpoint root do catalogo)

### Etapa 1.4: Criar `OpenMeteoProvider` implementando `WeatherDataProvider`

**Arquivo:** `services/worker/worker/pipeline/providers/open_meteo.py` (NOVO)

```python
"""
Open-Meteo weather data provider.
"""
import aiohttp
import structlog
from typing import List, Dict, Any

from worker.pipeline.providers.base import WeatherDataProvider

logger = structlog.get_logger()


class OpenMeteoProvider(WeatherDataProvider):

    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    @property
    def provider_name(self) -> str:
        return "open_meteo"

    async def fetch_history(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        timezone: str = "auto"
    ) -> List[Dict[str, Any]]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration",
            "timezone": timezone,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL, params=params) as resp:
                if resp.status != 200:
                    logger.error("open_meteo_failed", status=resp.status)
                    return []
                data = await resp.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        results = []
        for i, d in enumerate(dates):
            results.append({
                "date": d,
                "temp_max": daily.get("temperature_2m_max", [None])[i],
                "temp_min": daily.get("temperature_2m_min", [None])[i],
                "precip_sum": daily.get("precipitation_sum", [None])[i],
                "et0_fao": daily.get("et0_fao_evapotranspiration", [None])[i],
            })

        return results

    async def health_check(self) -> bool:
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                # Minimal request to verify API responds
                async with session.get(
                    self.BASE_URL,
                    params={"latitude": 0, "longitude": 0, "start_date": "2024-01-01",
                            "end_date": "2024-01-01", "daily": "temperature_2m_max"},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False
```

### Etapa 1.5: Criar `ProviderRegistry` (Service Locator)

**Arquivo:** `services/worker/worker/pipeline/providers/registry.py` (NOVO)

```python
"""
Registry de providers. Ponto central para obter providers configurados.
Substitui o padrao global _stac_client singleton.
"""
import structlog
from typing import Optional
from worker.pipeline.providers.base import SatelliteDataProvider, WeatherDataProvider
from worker.pipeline.providers.planetary_computer import PlanetaryComputerProvider
from worker.pipeline.providers.open_meteo import OpenMeteoProvider

logger = structlog.get_logger()

# Singletons (lazy)
_satellite_provider: Optional[SatelliteDataProvider] = None
_weather_provider: Optional[WeatherDataProvider] = None


def get_satellite_provider() -> SatelliteDataProvider:
    """
    Retorna o satellite data provider configurado.
    Por enquanto retorna PlanetaryComputerProvider.
    Futuramente lera config para decidir (ou retornar FallbackChainProvider).
    """
    global _satellite_provider
    if _satellite_provider is None:
        _satellite_provider = PlanetaryComputerProvider()
    return _satellite_provider


def get_weather_provider() -> WeatherDataProvider:
    """Retorna o weather provider configurado."""
    global _weather_provider
    if _weather_provider is None:
        _weather_provider = OpenMeteoProvider()
    return _weather_provider


def reset_providers():
    """Reset singletons (usado em testes)."""
    global _satellite_provider, _weather_provider
    _satellite_provider = None
    _weather_provider = None
```

### Etapa 1.6: Migrar TODOS os jobs e DELETAR `stac_client.py`

**Nao existe wrapper de retrocompatibilidade.** O `stac_client.py` sera deletado ao final desta etapa.
Todos os jobs passam a usar diretamente `get_satellite_provider()` e `IndexCalculator`.

Abaixo estao os diffs exatos para cada arquivo. Aplicar um a um, testando entre cada.

---

#### 1.6.1 — `process_topography.py` (mais simples — DEM estatico)

**Localizacao:** `services/worker/worker/jobs/process_topography.py`

Linha 114-128 atual:
```python
async def process_topography_async(job_id: str, payload: dict, db: Session):
    from worker.pipeline.stac_client import get_stac_client
    from worker.shared.utils import get_week_date_range, get_aoi_geometry
    ...
    client = get_stac_client()

    scenes = await client.search_scenes(
        aoi_geom,
        start_date=datetime(2010, 1, 1),
        end_date=datetime.now(),
        collections=["copernicus-dem-glo-30"]
    )
```

**Substituir por:**
```python
async def process_topography_async(job_id: str, payload: dict, db: Session):
    from worker.pipeline.providers.registry import get_satellite_provider
    from worker.shared.utils import get_week_date_range, get_aoi_geometry
    ...
    provider = get_satellite_provider()

    scenes = await provider.search_scenes(
        aoi_geom,
        start_date=datetime(2010, 1, 1),
        end_date=datetime.now(),
        collections=["copernicus-dem-glo-30"]
    )
```

E na linha 167:
```python
# ANTES
await client.download_and_clip_band(href, aoi_geom, path)

# DEPOIS
await provider.download_and_clip_band(href, aoi_geom, path)
```

**Nenhum `calculate_*` e usado neste job** (faz calculo de slope manualmente com numpy).

- [ ] Substituir import + todas as chamadas `client.` -> `provider.`
- [ ] Testar: `python -c "from worker.jobs.process_topography import process_topography_handler"`

---

#### 1.6.2 — `process_radar.py` (Sentinel-1, sem cloud cover)

**Localizacao:** `services/worker/worker/jobs/process_radar.py`

Linha 103-120 atual:
```python
async def process_radar_week_async(job_id: str, payload: dict, db: Session):
    from worker.pipeline.stac_client import get_stac_client
    from worker.shared.utils import get_week_date_range, get_aoi_geometry
    ...
    client = get_stac_client()

    scenes = await client.search_scenes(
        aoi_geom, start_date, end_date,
        max_cloud_cover=100,
        collections=["sentinel-1-rtc"]
    )
```

**Substituir por:**
```python
async def process_radar_week_async(job_id: str, payload: dict, db: Session):
    from worker.pipeline.providers.registry import get_satellite_provider
    from worker.pipeline.index_calculator import IndexCalculator
    from worker.shared.utils import get_week_date_range, get_aoi_geometry
    ...
    provider = get_satellite_provider()

    scenes = await provider.search_scenes(
        aoi_geom, start_date, end_date,
        max_cloud_cover=100,
        collections=["sentinel-1-rtc"]
    )
```

Substituir todas as chamadas `client.` neste arquivo:
```python
# ANTES (linhas 150-151)
await client.download_and_clip_band(href, aoi_geom, p)

# DEPOIS
await provider.download_and_clip_band(href, aoi_geom, p)
```

**ATENCAO — calculo de indices neste job e inline (nao usa client.calculate_rvi).**
O job calcula RVI e ratio diretamente com numpy (linhas 170-181). Nao precisa mudar.

- [ ] Substituir import + todas as chamadas `client.` -> `provider.`
- [ ] Testar: `python -c "from worker.jobs.process_radar import process_radar_week_handler"`

---

#### 1.6.3 — `process_weather.py` (Weather provider separado)

**Localizacao:** `services/worker/worker/jobs/process_weather.py`

Este job ja NAO importa stac_client. Usa `requests.get()` diretamente na linha 99.
Mas deve ser migrado para usar `WeatherDataProvider`:

Linha 83-101 atual:
```python
async def fetch_open_meteo_history(lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = { ... }
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: requests.get(url, params=params))
    response.raise_for_status()
    return response.json()
```

**Substituir por:**
```python
async def fetch_open_meteo_history(lat, lon, start_date, end_date):
    from worker.pipeline.providers.registry import get_weather_provider
    weather = get_weather_provider()
    return await weather.fetch_history(lat, lon, start_date, end_date)
```

E ajustar `process_weather_history_async` (linha 166) para usar o retorno padronizado:
```python
# ANTES (linhas 169-190)
data = await fetch_open_meteo_history(lat, lon, start_str, end_str)
daily = data.get('daily', {})
dates = daily.get('time', [])
...

# DEPOIS — fetch_history ja retorna lista de dicts padronizada
records = await fetch_open_meteo_history(lat, lon, start_str, end_str)
# records ja e: [{"date": ..., "temp_max": ..., "temp_min": ..., "precip_sum": ..., "et0_fao": ...}]
# Tratar None values
for r in records:
    r["temp_max"] = r["temp_max"] if r["temp_max"] is not None else 0
    r["temp_min"] = r["temp_min"] if r["temp_min"] is not None else 0
    r["precip_sum"] = r["precip_sum"] if r["precip_sum"] is not None else 0
    r["et0_fao"] = r["et0_fao"] if r["et0_fao"] is not None else 0
```

- [ ] Substituir `fetch_open_meteo_history` para usar `get_weather_provider()`
- [ ] Simplificar transformacao de dados (provider ja retorna formato padrao)
- [ ] Remover `import requests` (nao mais necessario)
- [ ] Testar: `python -c "from worker.jobs.process_weather import process_weather_history_handler"`

---

#### 1.6.4 — `process_week.py` (Sentinel-2, mais complexo)

**Localizacao:** `services/worker/worker/jobs/process_week.py`

Este e o job mais complexo. Usa `client` para:
- `client.search_scenes()` (linhas 284, 296, 308)
- `client.download_and_clip_band()` (linha 410)
- `client.fetch_weather_history()` (linha 269)
- `client.calculate_ndvi()` (linha 478)
- `client.calculate_savi()` (linha 492)
- `client.calculate_ndwi()` (linha 500)
- `client.calculate_ndmi()` (linha 507)
- `client.calculate_rvi()` (linha 351)
- `client.calculate_radar_ratio()` (linha 356)

**Diff:**

```python
# ANTES (linha 244-257)
async def process_week_async(job_id: str, payload: dict, db: Session):
    from worker.pipeline.stac_client import get_stac_client
    from worker.shared.utils import get_week_date_range, get_aoi_geometry
    ...
    client = get_stac_client()

# DEPOIS
async def process_week_async(job_id: str, payload: dict, db: Session):
    from worker.pipeline.providers.registry import get_satellite_provider, get_weather_provider
    from worker.pipeline.index_calculator import IndexCalculator
    from worker.shared.utils import get_week_date_range, get_aoi_geometry
    ...
    provider = get_satellite_provider()
    weather = get_weather_provider()
```

Substituir TODAS as chamadas:
```python
# search_scenes (3 ocorrencias)
client.search_scenes(...)  ->  provider.search_scenes(...)

# download_and_clip_band
client.download_and_clip_band(...)  ->  provider.download_and_clip_band(...)

# weather (linha 269)
# ANTES
weather_data = await client.fetch_weather_history(centroid_lat, centroid_lon, ...)
# DEPOIS
weather_data = await weather.fetch_history(centroid_lat, centroid_lon, ...)

# INDICES — remover await (IndexCalculator e sync)
# ANTES
ndvi = await client.calculate_ndvi(red, nir)
savi = await client.calculate_savi(red, nir)
ndwi = await client.calculate_ndwi(green, nir)
ndmi = await client.calculate_ndmi(nir, swir)
rvi = await client.calculate_rvi(vv, vh)
ratio = await client.calculate_radar_ratio(vv, vh)

# DEPOIS
ndvi = IndexCalculator.ndvi(red, nir)
savi = IndexCalculator.savi(red, nir)
ndwi = IndexCalculator.ndwi(green, nir)
ndmi = IndexCalculator.ndmi(nir, swir)
rvi = IndexCalculator.rvi(vv, vh)
ratio = IndexCalculator.radar_ratio(vv, vh)
```

**ATENCAO:** Os metodos `IndexCalculator.*` sao **sync** (retornam `np.ndarray` direto).
Remover o `await` de cada chamada. Se esquecer, Python levantara `TypeError: object ndarray can't be used in 'await' expression` — facil de pegar.

- [ ] Trocar import
- [ ] Substituir `client.search_scenes` -> `provider.search_scenes` (3 ocorrencias)
- [ ] Substituir `client.download_and_clip_band` -> `provider.download_and_clip_band`
- [ ] Substituir `client.fetch_weather_history` -> `weather.fetch_history`
- [ ] Substituir 6x `await client.calculate_*` -> `IndexCalculator.*` (sem await)
- [ ] Testar: `python -c "from worker.jobs.process_week import process_week_handler"`

---

#### 1.6.5 — `create_mosaic.py` (caso especial — usa STAC items crus)

**Localizacao:** `services/worker/worker/jobs/create_mosaic.py`

Este job **nao usa `get_stac_client()`**. Ele cria sua propria conexao:

```python
# ANTES (linhas 18-19, 31, 184-187)
import planetary_computer
from pystac_client import Client

PC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

catalog = Client.open(PC_STAC_URL, modifier=planetary_computer.sign_inplace)
search = catalog.search(collections=[collection], bbox=BRAZIL_BBOX, ...)
items = list(search.items())
```

**Substituir por:**
```python
# DEPOIS
from worker.pipeline.providers.registry import get_satellite_provider

provider = get_satellite_provider()
items = await provider.search_raw_items(
    bbox=BRAZIL_BBOX,
    start_date=start_date,
    end_date=end_date,
    max_cloud_cover=max_cloud_cover,
    collections=[collection],
    max_items=2000,
)
```

**NOTA:** `create_mosaic_handler` e sync. Como `search_raw_items` e async no provider,
converter o handler para usar asyncio:

```python
def create_mosaic_handler(job_id: str, payload: dict, db: Session) -> dict:
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_create_mosaic_async(job_id, payload, db))
    finally:
        loop.close()

async def _create_mosaic_async(job_id: str, payload: dict, db: Session) -> dict:
    from worker.pipeline.providers.registry import get_satellite_provider
    provider = get_satellite_provider()

    items = await provider.search_raw_items(
        bbox=BRAZIL_BBOX,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        collections=[collection],
        max_items=2000,
    )
    # ... resto do handler usando items (mesma logica de create_mosaic_json)
```

Remover imports que nao serao mais usados:
```python
# REMOVER
import planetary_computer
from pystac_client import Client
PC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
```

- [ ] Remover `import planetary_computer`, `from pystac_client import Client`, `PC_STAC_URL`
- [ ] Substituir `Client.open()` + `catalog.search()` por `provider.search_raw_items()`
- [ ] Converter handler para async wrapper
- [ ] Verificar que `create_mosaic_json()` recebe os mesmos `pystac.Item` objects
- [ ] Testar: `python -c "from worker.jobs.create_mosaic import create_mosaic_handler"`

---

#### 1.6.6 — DELETAR `stac_client.py`

Apos todos os jobs migrarem com sucesso:

```bash
# Verificar que nenhum arquivo importa stac_client
grep -r "stac_client" services/worker/worker/ --include="*.py"
# Deve retornar ZERO resultados

# Deletar
rm services/worker/worker/pipeline/stac_client.py
```

- [ ] Grep confirma zero imports de `stac_client`
- [ ] Arquivo deletado
- [ ] Todos os testes passam sem ele

---

**Criterios de aceite gerais da Fase 1:**
- [ ] `stac_client.py` **deletado** (nao existe mais no repositorio)
- [ ] Nenhum arquivo no worker importa `stac_client` ou `get_stac_client`
- [ ] Nenhum arquivo importa `pystac_client.Client` diretamente (exceto dentro dos providers)
- [ ] Nenhum arquivo importa `planetary_computer` diretamente (exceto dentro dos providers)
- [ ] Todos os jobs usam `get_satellite_provider()` do registry
- [ ] `process_weather.py` usa `get_weather_provider()` do registry
- [ ] Todos os calculos de indices usam `IndexCalculator` (sync, sem await)
- [ ] Todos os testes existentes passam
- [ ] `IndexCalculator` tem 100% de cobertura por testes unitarios

---

## FASE 2: Implementacao de Providers Alternativos {#fase-2}

### Contexto

Com a interface `SatelliteDataProvider` em vigor, podemos implementar providers alternativos. Os prioritarios para o Brasil sao:

1. **CDSE (Copernicus Data Space Ecosystem)** — Provider oficial europeu, gratuito
2. **AWS Earth Search** — Sentinel-2 COGs no S3 da AWS, sem necessidade de signing
3. **(Futuro) Brasil Data Cube** — INPE, dados nacionais

### Etapa 2.1: Implementar `CDSEProvider`

**Arquivo:** `services/worker/worker/pipeline/providers/cdse.py` (NOVO)

O CDSE usa STAC API com OAuth2 para autenticacao.

```python
"""
Copernicus Data Space Ecosystem (CDSE) provider.
URL: https://dataspace.copernicus.eu/
STAC: https://catalogue.dataspace.copernicus.eu/stac
Auth: OAuth2 client credentials -> Bearer token
"""
import aiohttp
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime

import numpy as np
from pystac_client import Client
from shapely.geometry import shape, mapping

from worker.pipeline.providers.base import SatelliteDataProvider

logger = structlog.get_logger()


class CDSEProvider(SatelliteDataProvider):

    CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/stac"
    TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    # Mapeamento CDSE -> padrao interface
    BAND_MAPPING = {
        "sentinel-2-l2a": {
            "red": "B04_10m", "green": "B03_10m", "blue": "B02_10m",
            "nir": "B08_10m", "swir": "B11_20m", "swir2": "B12_20m",
            "rededge": "B05_20m", "scl": "SCL_20m",
        },
    }

    def __init__(self, client_id: str, client_secret: str):
        """
        Args:
            client_id: CDSE OAuth2 client ID (env: CDSE_CLIENT_ID)
            client_secret: CDSE OAuth2 client secret (env: CDSE_CLIENT_SECRET)
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    @property
    def provider_name(self) -> str:
        return "cdse"

    @property
    def supported_collections(self) -> List[str]:
        return ["sentinel-2-l2a"]

    async def _ensure_token(self):
        """Obter/renovar OAuth2 token."""
        import time
        if self._access_token and time.time() < self._token_expires_at - 60:
            return

        async with aiohttp.ClientSession() as session:
            async with session.post(self.TOKEN_URL, data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }) as resp:
                data = await resp.json()
                self._access_token = data["access_token"]
                self._token_expires_at = time.time() + data.get("expires_in", 600)

        logger.info("cdse_token_refreshed")

    async def search_scenes(self, aoi_geom, start_date, end_date,
                           max_cloud_cover=60.0, collections=None):
        """Buscar cenas no CDSE STAC."""
        # ... (implementacao similar ao PlanetaryComputerProvider
        #      mas usando CDSE catalog URL e band mapping)
        # NOTA: O assistente que implementar deve:
        # 1. Abrir Client com CDSE CATALOG_URL
        # 2. Nao usar planetary_computer.sign (CDSE usa Bearer token)
        # 3. Mapear bandas conforme BAND_MAPPING acima
        # 4. Retornar no formato padrao da interface
        raise NotImplementedError("Implementar: CDSE STAC search")

    def sign_url(self, href: str) -> str:
        """CDSE usa Bearer token, nao SAS. Retorna URL com token no header."""
        # CDSE precisa de Authorization header, nao query param.
        # O download_and_clip_band deve usar aiohttp com header.
        return href

    async def download_and_clip_band(self, asset_href, aoi_geom, output_path):
        """Download com Bearer token no header (diferente de PC que usa SAS query param)."""
        await self._ensure_token()
        # ... implementar download com Authorization: Bearer header
        raise NotImplementedError("Implementar: CDSE download com Bearer token")

    async def health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.CATALOG_URL,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False
```

**Config necessaria em `worker/config.py`:**
```python
# CDSE (Copernicus Data Space Ecosystem) - Fallback provider
cdse_client_id: str | None = None
cdse_client_secret: str | None = None
```

**Criterios de aceite:**
- [ ] `CDSEProvider` implementa `SatelliteDataProvider`
- [ ] OAuth2 token refresh automatico
- [ ] Band mapping correto para CDSE (nomes de assets diferentes do PC)
- [ ] Health check funcional
- [ ] Testes com mock do CDSE API

### Etapa 2.2: Implementar `AWSEarthSearchProvider`

**Arquivo:** `services/worker/worker/pipeline/providers/aws_earth.py` (NOVO)

```python
"""
AWS Earth Search provider.
Sentinel-2 COGs hospedados no S3 da AWS (requester-pays).
URL: https://earth-search.aws.element84.com/v1
Sem necessidade de signing (S3 publico / requester-pays).
"""
from worker.pipeline.providers.base import SatelliteDataProvider

class AWSEarthSearchProvider(SatelliteDataProvider):

    CATALOG_URL = "https://earth-search.aws.element84.com/v1"

    # AWS Earth Search usa nomes de band diferentes
    BAND_MAPPING = {
        "sentinel-2-l2a": {
            "red": "red", "green": "green", "blue": "blue",
            "nir": "nir", "swir": "swir16", "swir2": "swir22",
            "rededge": "rededge1", "scl": "scl",
        },
    }

    @property
    def provider_name(self) -> str:
        return "aws_earth_search"

    @property
    def supported_collections(self) -> List[str]:
        return ["sentinel-2-l2a"]

    def sign_url(self, href: str) -> str:
        """AWS Earth Search COGs sao publicos. Nenhuma assinatura necessaria."""
        return href

    # ... (implementar search_scenes, download_and_clip_band, health_check
    #      seguindo mesmo padrao do PlanetaryComputerProvider mas sem signing)
```

**Criterios de aceite:**
- [ ] `AWSEarthSearchProvider` implementa `SatelliteDataProvider`
- [ ] Sem dependencia de `planetary_computer` lib
- [ ] Download direto (sem SAS token)
- [ ] Band mapping correto para AWS Earth Search

### Etapa 2.3: Adicionar settings de providers no config

**Arquivo:** `services/worker/worker/config.py` — EDITAR

Adicionar ao `Settings`:

```python
# Data Provider Configuration
satellite_provider: str = "planetary_computer"  # planetary_computer | cdse | aws_earth
satellite_fallback_providers: str = ""  # comma-separated: "aws_earth,cdse"

# CDSE credentials (optional, for fallback)
cdse_client_id: str | None = None
cdse_client_secret: str | None = None

# Weather Provider
weather_provider: str = "open_meteo"  # open_meteo (unico por enquanto)
```

**Criterios de aceite da Fase 2:**
- [ ] Pelo menos 1 provider alternativo (CDSEProvider ou AWSEarthSearchProvider) implementado e testavel
- [ ] Config de provider em `worker/config.py`
- [ ] Testes com mock para cada provider

---

## FASE 3: Cache de Metadados STAC + Reprocessamento {#fase-3}

### Contexto

Atualmente o sistema nao armazena metadados STAC. Se Planetary Computer ficar fora, nao ha como saber quais cenas existem para uma semana. Alem disso, nao ha mecanismo formal de reprocessamento.

### Etapa 3.1: Tabela `stac_scene_cache` no PostgreSQL

**Arquivo:** `infra/migrations/sql/006_add_stac_scene_cache.sql` (NOVO)

```sql
-- Cache de metadados STAC para resiliencia
-- Permite reprocessamento sem depender do catalogo STAC em tempo real

CREATE TABLE IF NOT EXISTS stac_scene_cache (
    id TEXT NOT NULL,                          -- STAC item ID (ex: S2A_MSIL2A_20260205T...)
    collection TEXT NOT NULL,                  -- sentinel-2-l2a, sentinel-1-rtc, etc.
    provider TEXT NOT NULL,                    -- planetary_computer, cdse, aws_earth

    datetime TIMESTAMPTZ NOT NULL,             -- Data da cena
    cloud_cover FLOAT,                         -- eo:cloud_cover (null para radar)
    platform TEXT,                             -- S2A, S2B, S1A, etc.

    bbox FLOAT[] NOT NULL,                     -- Bounding box [minx, miny, maxx, maxy]
    geometry GEOMETRY(POLYGON, 4326),          -- Footprint da cena

    -- Assets como JSONB (flexivel para diferentes providers)
    assets JSONB NOT NULL,                     -- {"red": "https://...", "nir": "https://...", ...}

    -- Metadados extras
    properties JSONB,                          -- Outras propriedades STAC uteis

    -- Tracking
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,                    -- Quando os URLs assinados expiram (NULL = nao expira)

    PRIMARY KEY (id, provider)
);

-- Indices para busca rapida
CREATE INDEX IF NOT EXISTS idx_scene_cache_collection_datetime
    ON stac_scene_cache (collection, datetime);

CREATE INDEX IF NOT EXISTS idx_scene_cache_geometry
    ON stac_scene_cache USING GIST (geometry);

CREATE INDEX IF NOT EXISTS idx_scene_cache_bbox
    ON stac_scene_cache USING GIST (
        ST_MakeEnvelope(bbox[1], bbox[2], bbox[3], bbox[4], 4326)
    );

-- Expirar cache antigo (90 dias)
-- Rodar via cron ou job periodico:
-- DELETE FROM stac_scene_cache WHERE fetched_at < NOW() - INTERVAL '90 days';
```

### Etapa 3.2: `SceneCacheRepository`

**Arquivo:** `services/worker/worker/pipeline/scene_cache.py` (NOVO)

```python
"""
Cache local de metadados STAC.
Permite operacao offline quando catalogo STAC esta indisponivel.
"""
import json
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = structlog.get_logger()


class SceneCacheRepository:
    """
    Repositorio de cache de cenas STAC.

    Fluxo:
    1. Provider busca cenas no STAC -> retorna lista
    2. SceneCacheRepository.save_scenes() persiste no DB
    3. Se STAC falhar, SceneCacheRepository.get_cached_scenes() serve dados locais
    """

    def save_scenes(
        self,
        scenes: List[Dict[str, Any]],
        collection: str,
        provider: str,
        db: Session
    ):
        """
        Persistir cenas no cache.
        Upsert: se cena ja existe (mesmo id+provider), atualiza.
        """
        if not scenes:
            return

        sql = text("""
            INSERT INTO stac_scene_cache
                (id, collection, provider, datetime, cloud_cover, platform,
                 bbox, assets, fetched_at)
            VALUES
                (:id, :collection, :provider, :datetime, :cloud_cover, :platform,
                 :bbox, :assets::jsonb, NOW())
            ON CONFLICT (id, provider) DO UPDATE SET
                assets = EXCLUDED.assets,
                fetched_at = NOW()
        """)

        for scene in scenes:
            db.execute(sql, {
                "id": scene["id"],
                "collection": collection,
                "provider": provider,
                "datetime": scene["datetime"],
                "cloud_cover": scene.get("cloud_cover"),
                "platform": scene.get("platform"),
                "bbox": scene.get("bbox"),
                "assets": json.dumps(scene.get("assets", {})),
            })

        db.commit()
        logger.info("scene_cache_saved", count=len(scenes), collection=collection, provider=provider)

    def get_cached_scenes(
        self,
        collection: str,
        start_date: datetime,
        end_date: datetime,
        bbox: Optional[List[float]] = None,
        max_cloud_cover: float = 100.0,
        db: Session = None,
    ) -> List[Dict[str, Any]]:
        """
        Buscar cenas do cache local.
        Usado quando o STAC catalog esta indisponivel.
        """
        conditions = [
            "collection = :collection",
            "datetime >= :start_date",
            "datetime <= :end_date",
        ]
        params = {
            "collection": collection,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        if max_cloud_cover < 100:
            conditions.append("(cloud_cover IS NULL OR cloud_cover < :max_cloud_cover)")
            params["max_cloud_cover"] = max_cloud_cover

        if bbox:
            conditions.append("""
                bbox[1] <= :maxx AND bbox[3] >= :minx
                AND bbox[2] <= :maxy AND bbox[4] >= :miny
            """)
            params.update({
                "minx": bbox[0], "miny": bbox[1],
                "maxx": bbox[2], "maxy": bbox[3],
            })

        where_clause = " AND ".join(conditions)
        sql = text(f"""
            SELECT id, collection, provider, datetime, cloud_cover, platform,
                   bbox, assets, fetched_at
            FROM stac_scene_cache
            WHERE {where_clause}
            ORDER BY datetime DESC
            LIMIT 200
        """)

        rows = db.execute(sql, params).fetchall()

        scenes = []
        for row in rows:
            assets = json.loads(row.assets) if isinstance(row.assets, str) else row.assets
            scenes.append({
                "id": row.id,
                "datetime": row.datetime.isoformat() if hasattr(row.datetime, 'isoformat') else row.datetime,
                "cloud_cover": row.cloud_cover or 0,
                "platform": row.platform or "unknown",
                "assets": assets,
                "bbox": list(row.bbox) if row.bbox else [],
                "geometry": {},  # Nao armazenamos geometry completo no cache
                "_cached": True,
                "_cached_at": str(row.fetched_at),
                "_provider": row.provider,
            })

        if scenes:
            logger.info("scene_cache_hit", count=len(scenes), collection=collection)
        else:
            logger.warning("scene_cache_miss", collection=collection,
                          start_date=str(start_date), end_date=str(end_date))

        return scenes

    def cleanup_expired(self, db: Session, max_age_days: int = 90):
        """Limpar cache antigo."""
        sql = text("""
            DELETE FROM stac_scene_cache
            WHERE fetched_at < NOW() - INTERVAL ':days days'
        """)
        result = db.execute(sql, {"days": max_age_days})
        db.commit()
        logger.info("scene_cache_cleanup", deleted=result.rowcount)
```

### Etapa 3.3: Integrar cache no provider (CachedProviderWrapper)

**Arquivo:** `services/worker/worker/pipeline/providers/cached_provider.py` (NOVO)

```python
"""
Wrapper que adiciona cache a qualquer SatelliteDataProvider.
Padrao Decorator: CachedProvider(PlanetaryComputerProvider()).
"""
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from sqlalchemy.orm import Session

from worker.pipeline.providers.base import SatelliteDataProvider
from worker.pipeline.scene_cache import SceneCacheRepository

logger = structlog.get_logger()


class CachedSatelliteProvider(SatelliteDataProvider):
    """
    Decorator que adiciona cache write-through a qualquer SatelliteDataProvider.

    Fluxo:
    1. search_scenes() -> tenta provider real
    2. Se sucesso -> salva no cache + retorna
    3. Se falha -> busca no cache local
    """

    def __init__(self, inner: SatelliteDataProvider, db_session_factory):
        """
        Args:
            inner: Provider real (ex: PlanetaryComputerProvider)
            db_session_factory: Callable que retorna Session (ex: get_db)
        """
        self._inner = inner
        self._cache = SceneCacheRepository()
        self._db_factory = db_session_factory

    @property
    def provider_name(self) -> str:
        return f"cached_{self._inner.provider_name}"

    @property
    def supported_collections(self) -> List[str]:
        return self._inner.supported_collections

    async def search_scenes(
        self,
        aoi_geom: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search com write-through cache."""
        db = self._db_factory()
        try:
            # 1. Tentar provider real
            scenes = await self._inner.search_scenes(
                aoi_geom, start_date, end_date, max_cloud_cover, collections
            )

            # 2. Salvar no cache (write-through)
            for coll in (collections or ["sentinel-2-l2a"]):
                coll_scenes = [s for s in scenes]  # Todos sao da mesma busca
                self._cache.save_scenes(coll_scenes, coll, self._inner.provider_name, db)

            return scenes

        except Exception as e:
            # 3. Fallback para cache local
            logger.warning("provider_failed_using_cache",
                          provider=self._inner.provider_name, error=str(e))

            from shapely.geometry import shape
            try:
                bbox = list(shape(aoi_geom).bounds)
            except Exception:
                bbox = None

            cached = self._cache.get_cached_scenes(
                collection=(collections or ["sentinel-2-l2a"])[0],
                start_date=start_date,
                end_date=end_date,
                bbox=bbox,
                max_cloud_cover=max_cloud_cover,
                db=db,
            )

            if cached:
                logger.info("serving_from_cache", count=len(cached))
                return cached

            # Se cache tambem vazio, re-raise
            raise
        finally:
            db.close()

    async def download_and_clip_band(self, asset_href, aoi_geom, output_path):
        return await self._inner.download_and_clip_band(asset_href, aoi_geom, output_path)

    def sign_url(self, href: str) -> str:
        return self._inner.sign_url(href)

    async def health_check(self) -> bool:
        return await self._inner.health_check()
```

### Etapa 3.4: Endpoint de reprocessamento no Admin UI

**Arquivo:** `services/api/app/presentation/admin_router.py` — EDITAR (ou criar se nao existir)

Adicionar endpoint:

```python
@router.post("/v1/admin/jobs/reprocess")
async def reprocess_jobs(
    request: ReprocessRequest,  # { aoi_id?, tenant_id?, year, week, job_types: list[str] }
    db: Session = Depends(get_db),
    admin = Depends(require_system_admin)
):
    """
    Reprocessar jobs para uma semana especifica.
    Cria novos jobs na fila SQS.
    """
    # Valida parametros
    # Para cada job_type em request.job_types:
    #   Criar mensagem SQS com payload {tenant_id, aoi_id, year, week}
    #   Enviar para fila de alta prioridade
    # Retornar lista de job_ids criados
```

**Admin UI — Botao de reprocessar:**

Ja existe parcialmente em `services/admin-ui/src/app/missing-weeks/page.tsx`. Verificar se funciona end-to-end e conectar com o novo endpoint.

**Criterios de aceite da Fase 3:**
- [ ] Migration `006_add_stac_scene_cache.sql` criada e aplicada
- [ ] `SceneCacheRepository` com save/get/cleanup
- [ ] `CachedSatelliteProvider` wrapper funcional
- [ ] Cache write-through: toda busca STAC grava no cache
- [ ] Cache read-on-failure: se STAC falhar, serve do cache
- [ ] Endpoint `/v1/admin/jobs/reprocess` funcional
- [ ] Admin UI permite reprocessar semanas com falha

---

## FASE 4: Fallback Chain com Circuit Breaker {#fase-4}

### Contexto

Com multiplos providers (Fase 2) e cache (Fase 3), podemos implementar fallback automatico:
`PlanetaryComputer -> AWSEarthSearch -> CDSE -> Cache Local`

### Etapa 4.1: `FallbackChainProvider`

**Arquivo:** `services/worker/worker/pipeline/providers/fallback_chain.py` (NOVO)

```python
"""
Fallback chain: tenta providers em sequencia ate um funcionar.
Integra com CircuitBreaker para evitar tentativas desnecessarias.
"""
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from worker.pipeline.providers.base import SatelliteDataProvider

logger = structlog.get_logger()


class ProviderCircuitBreaker:
    """
    Circuit breaker por provider.
    Previne tentativas repetidas em providers com falha.
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout_seconds: int = 300):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_seconds
        self._failures: Dict[str, int] = {}           # provider_name -> failure_count
        self._last_failure: Dict[str, float] = {}     # provider_name -> timestamp
        self._state: Dict[str, str] = {}              # provider_name -> CLOSED|OPEN|HALF_OPEN

    def is_available(self, provider_name: str) -> bool:
        """Verificar se provider esta disponivel (circuit nao aberto)."""
        import time
        state = self._state.get(provider_name, "CLOSED")

        if state == "CLOSED":
            return True

        if state == "OPEN":
            last = self._last_failure.get(provider_name, 0)
            if time.time() - last > self._recovery_timeout:
                self._state[provider_name] = "HALF_OPEN"
                logger.info("circuit_half_open", provider=provider_name)
                return True
            return False

        # HALF_OPEN: permitir uma tentativa
        return True

    def record_success(self, provider_name: str):
        """Registrar sucesso -> fechar circuit."""
        self._failures[provider_name] = 0
        self._state[provider_name] = "CLOSED"
        logger.debug("circuit_closed", provider=provider_name)

    def record_failure(self, provider_name: str):
        """Registrar falha -> potencialmente abrir circuit."""
        import time
        count = self._failures.get(provider_name, 0) + 1
        self._failures[provider_name] = count
        self._last_failure[provider_name] = time.time()

        if count >= self._failure_threshold:
            self._state[provider_name] = "OPEN"
            logger.warning("circuit_opened", provider=provider_name, failures=count)


class FallbackChainProvider(SatelliteDataProvider):
    """
    Tenta providers em sequencia com circuit breaker.

    Exemplo:
        chain = FallbackChainProvider([
            PlanetaryComputerProvider(),
            AWSEarthSearchProvider(),
            CDSEProvider(client_id, client_secret),
        ])
    """

    def __init__(
        self,
        providers: List[SatelliteDataProvider],
        circuit_breaker: Optional[ProviderCircuitBreaker] = None,
    ):
        if not providers:
            raise ValueError("At least one provider is required")

        self._providers = providers
        self._circuit = circuit_breaker or ProviderCircuitBreaker()

    @property
    def provider_name(self) -> str:
        names = [p.provider_name for p in self._providers]
        return f"fallback_chain({','.join(names)})"

    @property
    def supported_collections(self) -> List[str]:
        """Uniao de colecoes de todos os providers."""
        all_collections = set()
        for p in self._providers:
            all_collections.update(p.supported_collections)
        return list(all_collections)

    async def search_scenes(
        self,
        aoi_geom: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Tentar cada provider em sequencia.
        Pula providers com circuit aberto.
        """
        last_error = None

        for provider in self._providers:
            # Verificar se colecao e suportada
            if collections:
                if not any(c in provider.supported_collections for c in collections):
                    continue

            # Verificar circuit breaker
            if not self._circuit.is_available(provider.provider_name):
                logger.info("provider_skipped_circuit_open", provider=provider.provider_name)
                continue

            try:
                logger.info("fallback_trying_provider", provider=provider.provider_name)
                scenes = await provider.search_scenes(
                    aoi_geom, start_date, end_date, max_cloud_cover, collections
                )
                self._circuit.record_success(provider.provider_name)

                # Anotar qual provider retornou os dados
                for scene in scenes:
                    scene["_provider"] = provider.provider_name

                return scenes

            except Exception as e:
                logger.warning("provider_failed",
                             provider=provider.provider_name, error=str(e))
                self._circuit.record_failure(provider.provider_name)
                last_error = e
                continue

        # Nenhum provider funcionou
        raise RuntimeError(
            f"All providers failed. Last error: {last_error}"
        ) from last_error

    async def download_and_clip_band(self, asset_href, aoi_geom, output_path):
        """
        Download usa o provider que retornou a cena.
        Precisa saber qual provider assinou a URL.

        NOTA: Para simplificar, tenta o provider primario.
        Se falhar, tenta os outros (URL pode ser generica).
        """
        last_error = None
        for provider in self._providers:
            if not self._circuit.is_available(provider.provider_name):
                continue
            try:
                result = await provider.download_and_clip_band(
                    asset_href, aoi_geom, output_path
                )
                self._circuit.record_success(provider.provider_name)
                return result
            except Exception as e:
                self._circuit.record_failure(provider.provider_name)
                last_error = e
                continue

        raise RuntimeError(f"All providers failed for download. Last: {last_error}") from last_error

    def sign_url(self, href: str) -> str:
        """Tenta assinar com o primeiro provider disponivel."""
        for provider in self._providers:
            if self._circuit.is_available(provider.provider_name):
                return provider.sign_url(href)
        return href

    async def health_check(self) -> bool:
        """True se pelo menos um provider esta saudavel."""
        for provider in self._providers:
            try:
                if await provider.health_check():
                    return True
            except Exception:
                continue
        return False
```

### Etapa 4.2: Atualizar `ProviderRegistry` para construir a chain

**Arquivo:** `services/worker/worker/pipeline/providers/registry.py` — EDITAR

```python
def get_satellite_provider() -> SatelliteDataProvider:
    """Constroi o provider com fallback chain e cache."""
    global _satellite_provider
    if _satellite_provider is not None:
        return _satellite_provider

    from worker.config import settings
    from worker.pipeline.providers.planetary_computer import PlanetaryComputerProvider
    from worker.pipeline.providers.fallback_chain import FallbackChainProvider
    from worker.pipeline.providers.cached_provider import CachedSatelliteProvider
    from worker.database import get_db

    # 1. Montar lista de providers
    providers = [PlanetaryComputerProvider()]

    # Adicionar fallbacks se configurados
    fallback_names = [n.strip() for n in settings.satellite_fallback_providers.split(",") if n.strip()]

    for name in fallback_names:
        if name == "aws_earth":
            from worker.pipeline.providers.aws_earth import AWSEarthSearchProvider
            providers.append(AWSEarthSearchProvider())
        elif name == "cdse" and settings.cdse_client_id:
            from worker.pipeline.providers.cdse import CDSEProvider
            providers.append(CDSEProvider(settings.cdse_client_id, settings.cdse_client_secret))

    # 2. Se mais de 1 provider, usar FallbackChain
    if len(providers) > 1:
        base_provider = FallbackChainProvider(providers)
    else:
        base_provider = providers[0]

    # 3. Envolver com cache
    _satellite_provider = CachedSatelliteProvider(base_provider, get_db)

    return _satellite_provider
```

### Etapa 4.3: Adicionar metricas de observabilidade

**Arquivo:** `services/worker/worker/pipeline/providers/metrics.py` (NOVO)

```python
"""
Metricas de uso dos providers.
Salva no Redis para visualizacao no Admin UI.
"""
import time
import structlog
from typing import Optional

logger = structlog.get_logger()


class ProviderMetrics:
    """
    Registra metricas de cada provider:
    - Total de chamadas
    - Total de falhas
    - Latencia media
    - Circuit breaker state
    """

    def __init__(self, redis_client=None):
        self._redis = redis_client

    def record_call(self, provider_name: str, operation: str,
                    duration_ms: float, success: bool, error: Optional[str] = None):
        """Registrar uma chamada ao provider."""
        logger.info("provider_metric",
                    provider=provider_name,
                    operation=operation,
                    duration_ms=round(duration_ms, 1),
                    success=success,
                    error=error)

        if self._redis:
            try:
                key = f"provider_metrics:{provider_name}"
                pipe = self._redis.pipeline()
                pipe.hincrby(key, f"{operation}_total", 1)
                if not success:
                    pipe.hincrby(key, f"{operation}_errors", 1)
                pipe.expire(key, 86400)  # 24h TTL
                pipe.execute()
            except Exception:
                pass  # Metricas nao devem afetar fluxo principal
```

### Etapa 4.4: Endpoint de status dos providers no Admin

**Arquivo:** Adicionar endpoint em `services/api/` para o Admin UI:

```python
@router.get("/v1/admin/providers/status")
async def get_provider_status():
    """
    Retorna status de cada data provider.
    Usado pelo Admin UI para monitorar saude dos providers.
    """
    return {
        "providers": [
            {
                "name": "planetary_computer",
                "status": "healthy",  # healthy | degraded | down
                "circuit_state": "CLOSED",
                "calls_24h": 1234,
                "errors_24h": 5,
                "avg_latency_ms": 1725,
            },
            # ...
        ],
        "cache": {
            "scenes_cached": 15000,
            "oldest_scene": "2026-01-01",
            "newest_scene": "2026-02-05",
        }
    }
```

**Criterios de aceite da Fase 4:**
- [ ] `FallbackChainProvider` implementado e testado
- [ ] `ProviderCircuitBreaker` abre apos 3 falhas consecutivas
- [ ] Circuit breaker reabre (HALF_OPEN) apos 300s de recovery
- [ ] Registry monta chain conforme `satellite_fallback_providers` config
- [ ] Metricas de provider logadas via structlog
- [ ] Endpoint `/v1/admin/providers/status` funcional
- [ ] Teste end-to-end: simular falha do provider primario e verificar fallback

---

## Estrutura Final de Arquivos

```
services/worker/worker/pipeline/
├── __init__.py
├── index_calculator.py             # NOVO: Calculo de indices (extraido de STACClient)
├── scene_cache.py                  # NOVO: Cache de metadados STAC
├── providers/
│   ├── __init__.py                 # NOVO
│   ├── base.py                     # NOVO: SatelliteDataProvider + WeatherDataProvider ABCs
│   ├── registry.py                 # NOVO: get_satellite_provider(), get_weather_provider()
│   ├── planetary_computer.py       # NOVO: PlanetaryComputerProvider
│   ├── cdse.py                     # NOVO: CDSEProvider (Fase 2)
│   ├── aws_earth.py                # NOVO: AWSEarthSearchProvider (Fase 2)
│   ├── open_meteo.py               # NOVO: OpenMeteoProvider
│   ├── cached_provider.py          # NOVO: CachedSatelliteProvider decorator
│   ├── fallback_chain.py           # NOVO: FallbackChainProvider + ProviderCircuitBreaker
│   └── metrics.py                  # NOVO: ProviderMetrics
│
│   stac_client.py                  # DELETADO (Etapa 1.6.6)

infra/migrations/sql/
└── 006_add_stac_scene_cache.sql    # NOVO

tests/
├── test_index_calculator.py        # NOVO
├── test_satellite_providers.py     # NOVO
├── test_scene_cache.py             # NOVO
├── test_fallback_chain.py          # NOVO
└── test_provider_integration.py    # NOVO (com mocks)
```

## Configuracao Final (.env)

```env
# Data Provider (Fase 1)
SATELLITE_PROVIDER=planetary_computer
WEATHER_PROVIDER=open_meteo

# Fallback Chain (Fase 4)
SATELLITE_FALLBACK_PROVIDERS=aws_earth,cdse

# CDSE Credentials (Fase 2, opcional)
CDSE_CLIENT_ID=
CDSE_CLIENT_SECRET=
```

---

## Ordem de Implementacao Recomendada

| # | Etapa | Deps | Risco |
|---|-------|------|-------|
| 1 | 1.1 Base interfaces (SatelliteDataProvider, WeatherDataProvider) | Nenhuma | Baixo |
| 2 | 1.2 IndexCalculator + testes unitarios | 1.1 | Baixo |
| 3 | 1.3 PlanetaryComputerProvider (incl. search_raw_items) | 1.1 | Medio |
| 4 | 1.4 OpenMeteoProvider | 1.1 | Baixo |
| 5 | 1.5 ProviderRegistry | 1.3, 1.4 | Baixo |
| 6 | 1.6.1 Migrar process_topography.py | 1.5 | Baixo |
| 7 | 1.6.2 Migrar process_radar.py | 1.5 | Baixo |
| 8 | 1.6.3 Migrar process_weather.py | 1.5 | Baixo |
| 9 | 1.6.4 Migrar process_week.py | 1.5 | **Alto** |
| 10 | 1.6.5 Migrar create_mosaic.py | 1.5 | **Alto** |
| 11 | 1.6.6 **Deletar stac_client.py** + validar grep zero imports | 1.6.1-5 | Medio |
| 12 | 3.1 Migration stac_scene_cache | Nenhuma | Baixo |
| 13 | 3.2 SceneCacheRepository | 3.1 | Medio |
| 14 | 3.3 CachedSatelliteProvider | 3.2, 1.3 | Medio |
| 15 | 2.1 CDSEProvider | 1.1 | Medio |
| 16 | 2.2 AWSEarthSearchProvider | 1.1 | Medio |
| 17 | 4.1 FallbackChainProvider | 1.3, 2.x | Medio |
| 18 | 4.2 Registry com chain | 4.1 | Baixo |
| 19 | 3.4 Endpoint reprocessamento | 3.2 | Baixo |
| 20 | 4.3 Metricas | 4.1 | Baixo |
| 21 | 4.4 Admin status endpoint | 4.3 | Baixo |

## Testes Criticos

1. **Unitario**: IndexCalculator — todos os indices retornam valores no range esperado
2. **Unitario**: PlanetaryComputerProvider.search_scenes — mock de pystac_client, verificar formato de retorno
3. **Unitario**: FallbackChainProvider — simular falha do provider 1, verificar que tenta provider 2
4. **Unitario**: ProviderCircuitBreaker — verificar transicoes CLOSED -> OPEN -> HALF_OPEN -> CLOSED
5. **Unitario**: CachedSatelliteProvider — simular falha do provider real, verificar que serve do cache
6. **Integracao**: Migrar um job (process_topography) e verificar que funciona identico ao original
7. **Integracao**: Reprocessamento via Admin endpoint cria job na fila SQS

---

## Notas para o Assistente Implementador

1. **NAO migrar todos os jobs de uma vez.** Migrar UM job (etapa 1.6.x), rodar testes, commitar, depois o proximo. Se um job quebrar, os demais continuam funcionando com o stac_client original ate serem migrados.
2. **stac_client.py so e deletado na Etapa 1.6.6** — APOS todos os 5 jobs terem sido migrados e testados. Antes disso ele ainda existe no disco (apenas ninguem o importa mais).
3. **create_mosaic.py usa `search_raw_items()`** — metodo novo que retorna `pystac.Item` crus (com links e assets originais). Diferente de `search_scenes()` que retorna dicts simplificados. A funcao `create_mosaic_json()` recebe esses items e precisa de `item.links`, `item.bbox`, `item.id`, `item.assets`.
4. **`IndexCalculator` e 100% sync.** Ao migrar `process_week.py`, trocar `await client.calculate_ndvi(red, nir)` por `IndexCalculator.ndvi(red, nir)` (sem await). Caso esqueca o await, Python levanta `TypeError` imediatamente — facil de detectar.
5. **`fetch_weather_history` muda de interface.** O metodo antigo retornava o JSON cru do Open-Meteo (`{"daily": {"time": [...], ...}}`). O novo `WeatherDataProvider.fetch_history()` retorna lista padronizada `[{"date": ..., "temp_max": ...}]`. O job `process_weather.py` deve ser ajustado para consumir esse formato (menos parsing necessario).
6. **Testes primeiro**: Para cada etapa, escrever o teste ANTES da implementacao (TDD).
7. **Nao instalar libs novas** a menos que listadas aqui. Todas as dependencias necessarias (pystac_client, planetary_computer, tenacity, aiohttp, rasterio) ja estao no requirements.txt do worker.
8. **Validacao final da Etapa 1.6.6**: Rodar `grep -r "stac_client\|get_stac_client" services/worker/ --include="*.py"` e confirmar ZERO resultados antes de deletar o arquivo.
9. **Nao existe camada de delegacao/wrapper.** `stac_client.py` nao e reescrito como proxy. Ele simplesmente deixa de ser importado e e deletado.
