# Plano de Implementação: Data Provider Resilience (REVISADO)

**Objetivo:** Implementar 4 camadas de resiliência para data providers do VivaCampo  
**Prioridade:** P0 (pré-requisito para produção confiável)  
**Data Criação:** 2026-02-05  
**Última Revisão:** 2026-02-06

---

## 📊 Status de Implementação

| Fase | Status | Progresso | Esforço Restante |
|------|--------|-----------|------------------|
| FASE 1 | 🟡 Em Andamento | 80% | 14h |
| FASE 4 | ⏳ Não Iniciado | 0% | 8h |
| FASE 3 | ⏳ Não Iniciado | 0% | 6h |
| FASE 2 | ⏳ Não Iniciado | 0% | 12h |

**Total Restante**: 40h (~5 dias)

---

## 🎯 Ordem de Execução Revisada

> [!IMPORTANT]
> **Mudança de Ordem**: Executar FASE 4 antes de FASE 2/3 para aproveitar circuit breakers já implementados.

**Ordem Original**: FASE 1 → 2 → 3 → 4  
**Ordem Revisada**: **FASE 1 → 4 → 3 → 2** ✅

**Justificativa**:
- Circuit breakers já existem em `infrastructure/resilience.py`
- Fallback chain pode usar PC + Cache inicialmente
- CDSE (FASE 2) pode ser adicionado incrementalmente

---

## FASE 1: Interface + Adapter Pattern (80% COMPLETO)

### ✅ Já Implementado

**Ports Criados**:
- ✅ `worker/domain/ports/satellite_provider.py` — `ISatelliteProvider` (ABC)
- ✅ `worker/domain/ports/weather_provider.py` — `WeatherProvider` (ABC)
- ✅ Dataclass `SatelliteScene` para padronização

**Adapters Criados**:
- ✅ `worker/infrastructure/adapters/jobs/open_meteo_provider.py` — `OpenMeteoProvider`

**Compliance Hexagonal**:
- ✅ Ports em `domain/ports/` (correto)
- ✅ Adapters em `infrastructure/adapters/` (correto)
- ✅ Naming: Prefixo `I` para interfaces, sufixo `Provider`

---

### ⏳ Pendente (20%)

#### Task 1.1: Extrair IndexCalculator (4h)

**Problema**: Cálculos de índices (NDVI, NDWI, etc.) estão no `STACClient`

**Solução**: Criar serviço de domínio

**Arquivo**: `worker/domain/services/index_calculator.py` (NOVO)

```python
"""Cálculo de índices de vegetação e radar."""
import numpy as np

class IndexCalculator:
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
        """RVI = 4 * VH / (VV + VH)"""
        denom = vv + vh
        denom = np.where(denom == 0, 0.0001, denom)
        return np.clip(4 * vh / denom, 0, 1)
    
    @staticmethod
    def mask_clouds(data: np.ndarray, scl: np.ndarray) -> np.ndarray:
        """Máscara de nuvens usando SCL (Scene Classification Layer)."""
        # Resize SCL se necessário
        if data.shape[-2:] != scl.shape[-2:]:
            target_h, target_w = data.shape[-2:]
            scl_h, scl_w = scl.shape[-2:]
            scale_h = target_h / scl_h
            scale_w = target_w / scl_w
            y_coords = np.arange(target_h) / scale_h
            x_coords = np.arange(target_w) / scale_w
            y_indices = np.clip(np.round(y_coords).astype(int), 0, scl_h - 1)
            x_indices = np.clip(np.round(x_coords).astype(int), 0, scl_w - 1)
            scl = scl[y_indices[:, None], x_indices]
        
        # Pixels inválidos: 0=NoData, 1=Saturated, 3=CloudShadow, 8/9/10=Clouds
        invalid = np.isin(scl, [0, 1, 3, 8, 9, 10])
        return np.where(invalid, np.nan, data)
```

**Testes**: `tests/unit/domain/test_index_calculator.py`

---

#### Task 1.2: Refatorar STACClient → PlanetaryComputerProvider (6h)

**Arquivo**: `worker/infrastructure/adapters/satellite/planetary_computer_provider.py` (NOVO)

```python
"""Planetary Computer STAC provider."""
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import planetary_computer
from pystac_client import Client

from worker.domain.ports.satellite_provider import ISatelliteProvider, SatelliteScene

logger = structlog.get_logger()

class PlanetaryComputerProvider(ISatelliteProvider):
    CATALOG_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
    
    BAND_MAPPING = {
        "sentinel-2-l2a": {
            "red": "B04", "green": "B03", "blue": "B02",
            "nir": "B08", "swir": "B11", "swir2": "B12",
            "rededge": "B05", "scl": "SCL",
        },
        "sentinel-1-rtc": {"vv": "vv", "vh": "vh"},
        "copernicus-dem-glo-30": {"dem": "data"},
    }
    
    def __init__(self, catalog_url: str | None = None):
        self._catalog_url = catalog_url or self.CATALOG_URL
        self._client = None
    
    @property
    def provider_name(self) -> str:
        return "planetary_computer"
    
    async def search_scenes(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        collections: Optional[List[str]] = None,
        max_cloud_cover: float = 60.0,
    ) -> List[SatelliteScene]:
        # Implementação completa...
        pass
    
    async def download_band(
        self,
        asset_href: str,
        geometry: Dict[str, Any],
        output_path: str,
    ) -> str:
        # Implementação completa...
        pass
    
    async def health_check(self) -> bool:
        # Implementação completa...
        pass
```

---

#### Task 1.3: Criar ProviderRegistry (2h)

**Arquivo**: `worker/infrastructure/providers/registry.py` (NOVO)

```python
"""Registry de providers."""
from worker.domain.ports.satellite_provider import ISatelliteProvider
from worker.domain.ports.weather_provider import WeatherProvider
from worker.infrastructure.adapters.satellite.planetary_computer_provider import PlanetaryComputerProvider
from worker.infrastructure.adapters.jobs.open_meteo_provider import OpenMeteoProvider

_satellite_provider: ISatelliteProvider | None = None
_weather_provider: WeatherProvider | None = None

def get_satellite_provider() -> ISatelliteProvider:
    global _satellite_provider
    if _satellite_provider is None:
        _satellite_provider = PlanetaryComputerProvider()
    return _satellite_provider

def get_weather_provider() -> WeatherProvider:
    global _weather_provider
    if _weather_provider is None:
        _weather_provider = OpenMeteoProvider()
    return _weather_provider

def reset_providers():
    """Reset singletons (para testes)."""
    global _satellite_provider, _weather_provider
    _satellite_provider = None
    _weather_provider = None
```

---

#### Task 1.4: Migrar Jobs (2h)

**Arquivos**:
- `worker/jobs/process_topography.py`
- `worker/jobs/process_radar.py`
- `worker/jobs/process_satellite.py`

**Mudança**:
```python
# ANTES
from worker.pipeline.stac_client import get_stac_client
client = get_stac_client()
scenes = await client.search_scenes(...)

# DEPOIS
from worker.infrastructure.providers.registry import get_satellite_provider
from worker.domain.services.index_calculator import IndexCalculator

provider = get_satellite_provider()
scenes = await provider.search_scenes(...)
ndvi = IndexCalculator.ndvi(red, nir)
```

---

#### Task 1.5: Deletar stac_client.py (0.5h)

```bash
git rm services/worker/worker/pipeline/stac_client.py
```

**Validação**: `grep -r "stac_client" services/worker/` → 0 resultados

---

## FASE 4: Fallback Chain + Circuit Breaker (8h)

> [!NOTE]
> **Executar antes de FASE 2/3**: Aproveita circuit breakers já implementados em `infrastructure/resilience.py`

### Task 4.1: Criar FallbackChainProvider (4h)

**Arquivo**: `worker/infrastructure/adapters/satellite/fallback_chain_provider.py` (NOVO)

```python
"""Fallback chain provider com circuit breakers."""
import structlog
from typing import List
from worker.domain.ports.satellite_provider import ISatelliteProvider, SatelliteScene
from worker.infrastructure.resilience import circuit, retry_with_backoff

logger = structlog.get_logger()

class FallbackChainProvider(ISatelliteProvider):
    def __init__(self, providers: List[ISatelliteProvider]):
        self.providers = providers
    
    @property
    def provider_name(self) -> str:
        return "fallback_chain"
    
    @circuit(failure_threshold=3, recovery_timeout=120)
    @retry_with_backoff(max_attempts=2, initial_delay=1.0)
    async def search_scenes(self, geometry, start_date, end_date, collections=None, max_cloud_cover=60.0):
        last_error = None
        
        for provider in self.providers:
            try:
                logger.info("trying_provider", provider=provider.provider_name)
                scenes = await provider.search_scenes(
                    geometry, start_date, end_date, collections, max_cloud_cover
                )
                logger.info("provider_success", provider=provider.provider_name, scenes=len(scenes))
                return scenes
            except Exception as e:
                logger.warning("provider_failed", provider=provider.provider_name, error=str(e))
                last_error = e
                continue
        
        raise Exception(f"All providers failed. Last error: {last_error}")
    
    async def download_band(self, asset_href, geometry, output_path):
        # Similar fallback logic
        pass
    
    async def health_check(self) -> bool:
        # Check if at least one provider is healthy
        for provider in self.providers:
            if await provider.health_check():
                return True
        return False
```

---

### Task 4.2: Integrar com Registry (2h)

**Atualizar**: `worker/infrastructure/providers/registry.py`

```python
from worker.infrastructure.adapters.satellite.fallback_chain_provider import FallbackChainProvider
from worker.infrastructure.adapters.satellite.planetary_computer_provider import PlanetaryComputerProvider

def get_satellite_provider() -> ISatelliteProvider:
    global _satellite_provider
    if _satellite_provider is None:
        pc_provider = PlanetaryComputerProvider()
        # Futuramente: adicionar CDSE e Cache
        _satellite_provider = FallbackChainProvider([pc_provider])
    return _satellite_provider
```

---

### Task 4.3: Testes de Resiliência (2h)

**Arquivo**: `tests/integration/test_fallback_chain.py`

```python
import pytest
from worker.infrastructure.adapters.satellite.fallback_chain_provider import FallbackChainProvider

class FakeProvider:
    def __init__(self, name, should_fail=False):
        self.name = name
        self.should_fail = should_fail
    
    @property
    def provider_name(self):
        return self.name
    
    async def search_scenes(self, *args, **kwargs):
        if self.should_fail:
            raise Exception(f"{self.name} failed")
        return [{"id": f"scene-{self.name}"}]

@pytest.mark.asyncio
async def test_fallback_to_second_provider():
    provider1 = FakeProvider("provider1", should_fail=True)
    provider2 = FakeProvider("provider2", should_fail=False)
    
    chain = FallbackChainProvider([provider1, provider2])
    scenes = await chain.search_scenes({}, None, None)
    
    assert len(scenes) == 1
    assert scenes[0]["id"] == "scene-provider2"
```

---

## FASE 3: Cache de Metadados STAC (6h)

### Task 3.1: Criar STACMetadataCache (4h)

**Arquivo**: `worker/infrastructure/adapters/satellite/stac_cache_provider.py` (NOVO)

```python
"""STAC metadata cache usando Redis."""
import json
import hashlib
import structlog
from typing import List
from datetime import datetime, timedelta
from worker.domain.ports.satellite_provider import ISatelliteProvider, SatelliteScene

logger = structlog.get_logger()

class STACCacheProvider(ISatelliteProvider):
    def __init__(self, redis_client, upstream_provider: ISatelliteProvider, ttl_hours: int = 24):
        self.redis = redis_client
        self.upstream = upstream_provider
        self.ttl = timedelta(hours=ttl_hours)
    
    @property
    def provider_name(self) -> str:
        return f"cache_{self.upstream.provider_name}"
    
    def _cache_key(self, geometry, start_date, end_date, collections, max_cloud_cover):
        key_data = f"{geometry}_{start_date}_{end_date}_{collections}_{max_cloud_cover}"
        return f"stac:scenes:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def search_scenes(self, geometry, start_date, end_date, collections=None, max_cloud_cover=60.0):
        cache_key = self._cache_key(geometry, start_date, end_date, collections, max_cloud_cover)
        
        # Try cache
        cached = self.redis.get(cache_key)
        if cached:
            logger.info("cache_hit", key=cache_key)
            return [SatelliteScene(**s) for s in json.loads(cached)]
        
        # Fetch from upstream
        logger.info("cache_miss", key=cache_key)
        scenes = await self.upstream.search_scenes(geometry, start_date, end_date, collections, max_cloud_cover)
        
        # Cache result
        self.redis.setex(cache_key, int(self.ttl.total_seconds()), json.dumps([s.__dict__ for s in scenes]))
        return scenes
    
    async def download_band(self, asset_href, geometry, output_path):
        # Delegate to upstream (não cachear downloads)
        return await self.upstream.download_band(asset_href, geometry, output_path)
    
    async def health_check(self) -> bool:
        return await self.upstream.health_check()
```

---

### Task 3.2: Integrar com FallbackChain (2h)

**Atualizar**: `worker/infrastructure/providers/registry.py`

```python
from worker.infrastructure.adapters.satellite.stac_cache_provider import STACCacheProvider
import redis

def get_satellite_provider() -> ISatelliteProvider:
    global _satellite_provider
    if _satellite_provider is None:
        redis_client = redis.Redis(host='redis', port=6379, db=0)
        pc_provider = PlanetaryComputerProvider()
        cached_pc = STACCacheProvider(redis_client, pc_provider)
        
        _satellite_provider = FallbackChainProvider([cached_pc])
    return _satellite_provider
```

---

## FASE 2: Providers Alternativos (CDSE) (12h)

### Task 2.1: Implementar CDSEProvider (8h)

**Arquivo**: `worker/infrastructure/adapters/satellite/cdse_provider.py` (NOVO)

```python
"""Copernicus Data Space Ecosystem provider."""
import structlog
from worker.domain.ports.satellite_provider import ISatelliteProvider

logger = structlog.get_logger()

class CDSEProvider(ISatelliteProvider):
    CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/stac"
    
    @property
    def provider_name(self) -> str:
        return "cdse"
    
    # Implementação similar a PlanetaryComputerProvider
    # Diferenças: OAuth2 auth, diferentes asset names
```

---

### Task 2.2: Configurar OAuth2 (2h)

**Arquivo**: `worker/infrastructure/adapters/satellite/cdse_auth.py` (NOVO)

```python
"""CDSE OAuth2 authentication."""
import requests

class CDSEAuth:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
    
    def get_token(self) -> str:
        if self._token:
            return self._token
        
        # OAuth2 token request
        response = requests.post(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        )
        self._token = response.json()["access_token"]
        return self._token
```

---

### Task 2.3: Adicionar ao Fallback Chain (2h)

**Atualizar**: `worker/infrastructure/providers/registry.py`

```python
def get_satellite_provider() -> ISatelliteProvider:
    global _satellite_provider
    if _satellite_provider is None:
        redis_client = redis.Redis(host='redis', port=6379, db=0)
        
        pc_provider = PlanetaryComputerProvider()
        cdse_provider = CDSEProvider()
        
        cached_pc = STACCacheProvider(redis_client, pc_provider)
        cached_cdse = STACCacheProvider(redis_client, cdse_provider)
        
        _satellite_provider = FallbackChainProvider([cached_pc, cached_cdse])
    return _satellite_provider
```

---

## 🎯 Métricas de Sucesso

| Métrica | Antes | Meta | Validação |
|---------|-------|------|-----------|
| `stac_client.py` deletado | ❌ | ✅ | `git log --diff-filter=D` |
| Providers implementados | 1 (PC) | 3 (PC, CDSE, Cache) | Código |
| Circuit breakers ativos | 2 (SQS/S3) | 5 (+ PC, CDSE, Cache) | Logs |
| Failover automático | ❌ | ✅ | Teste resiliência |
| Cache hit rate | 0% | >60% | Redis metrics |

---

## ✅ Critérios de Aceite

**FASE 1**:
- [ ] `IndexCalculator` criado e testado
- [ ] `PlanetaryComputerProvider` implementa `ISatelliteProvider`
- [ ] `ProviderRegistry` funcional
- [ ] Todos jobs migrados
- [ ] `stac_client.py` deletado
- [ ] 0 imports de `stac_client` no código

**FASE 4**:
- [ ] `FallbackChainProvider` funcional
- [ ] Circuit breakers integrados
- [ ] Testes de failover passando

**FASE 3**:
- [ ] Cache Redis implementado
- [ ] TTL de 24h configurado
- [ ] Cache hit rate >60% em produção

**FASE 2**:
- [ ] `CDSEProvider` funcional
- [ ] OAuth2 configurado
- [ ] Fallback PC → CDSE funcionando

---

## 📋 Next Steps

1. ✅ Aprovar plano revisado
2. ⏳ Criar branch: `feat/data-provider-resilience`
3. ⏳ Executar FASE 1 (14h)
4. ⏳ Executar FASE 4 (8h)
5. ⏳ Executar FASE 3 (6h)
6. ⏳ Executar FASE 2 (12h)
7. ⏳ Validar métricas de sucesso
