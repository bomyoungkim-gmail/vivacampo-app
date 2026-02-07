# Review: PLAN-DATA-PROVIDER-RESILIENCE.md

**Data**: 2026-02-06  
**Status**: ✅ Parcialmente Implementado

---

## 📊 Status de Implementação

### ✅ FASE 1: Interface + Adapter Pattern — **80% COMPLETO**

**Implementado**:
- ✅ Port `ISatelliteProvider` em `worker/domain/ports/satellite_provider.py`
- ✅ Port `WeatherProvider` em `worker/domain/ports/weather_provider.py`
- ✅ Adapter `OpenMeteoProvider` em `worker/infrastructure/adapters/jobs/open_meteo_provider.py`
- ✅ Dataclass `SatelliteScene` para padronização

**Diferenças do Plano Original**:
| Plano | Implementado | Status |
|-------|--------------|--------|
| `SatelliteDataProvider` (ABC) | `ISatelliteProvider` (ABC) | ✅ Equivalente |
| `WeatherDataProvider` (ABC) | `WeatherProvider` (ABC) | ✅ Equivalente |
| `providers/base.py` | `domain/ports/*.py` | ✅ Melhor (hexagonal) |
| `IndexCalculator` separado | Não encontrado | ⚠️  Pendente |
| `PlanetaryComputerProvider` | Não encontrado | ⚠️  Pendente |
| `ProviderRegistry` | Não encontrado | ⚠️  Pendente |

**Pendente**:
- ⏳ Extrair `IndexCalculator` do `STACClient`
- ⏳ Refatorar `STACClient` → `PlanetaryComputerProvider`
- ⏳ Criar `ProviderRegistry` (service locator)
- ⏳ Migrar jobs para usar providers
- ⏳ Deletar `stac_client.py`

---

### ⏳ FASE 2: Providers Alternativos — **NÃO INICIADO**

**Objetivo**: Implementar CDSE (Copernicus Data Space Ecosystem) como fallback

**Pendente**:
- [ ] Criar `CDSEProvider` implementando `ISatelliteProvider`
- [ ] Configurar autenticação OAuth2
- [ ] Mapear bandas Sentinel-2/1
- [ ] Testes de integração

---

### ⏳ FASE 3: Cache de Metadados STAC — **NÃO INICIADO**

**Objetivo**: Cache Redis para metadados STAC

**Pendente**:
- [ ] Criar `STACMetadataCache` usando Redis
- [ ] Implementar TTL (24h para metadados)
- [ ] Cache de `search_scenes` results
- [ ] Invalidação em caso de fallback

---

### ⏳ FASE 4: Fallback Chain + Circuit Breaker — **NÃO INICIADO**

**Objetivo**: Cadeia de fallback com circuit breakers

**Pendente**:
- [ ] Criar `FallbackChainProvider`
- [ ] Integrar circuit breakers existentes (`resilience.py`)
- [ ] Configurar ordem: PC → CDSE → Cache
- [ ] Métricas de failover

---

## 🎯 Alinhamento com Hexagonal Architecture

### ✅ Pontos Positivos

1. **Ports Corretos**: `ISatelliteProvider` está em `domain/ports/` ✅
2. **Adapters Corretos**: `OpenMeteoProvider` está em `infrastructure/adapters/` ✅
3. **Naming Consistente**: Prefixo `I` para interfaces, sufixo `Provider` ✅
4. **Dataclass para DTOs**: `SatelliteScene` é um DTO imutável ✅

### ⚠️  Problemas Identificados

1. **STACClient ainda existe**: Viola hexagonal architecture
   - Localização: `worker/pipeline/stac_client.py`
   - Problema: Mistura responsabilidades (search + download + cálculo)
   - Solução: Seguir Fase 1 do plano

2. **IndexCalculator não extraído**: Cálculos ainda no STACClient
   - Problema: Lógica de negócio (NDVI, NDWI) acoplada ao provider
   - Solução: Criar `worker/domain/services/index_calculator.py`

3. **Falta DI Container para Providers**: Jobs instanciam providers diretamente
   - Problema: Dificulta testes e troca de providers
   - Solução: Criar `ProviderRegistry` ou usar DI Container

---

## 📝 Recomendações

### Prioridade 1: Completar FASE 1 (14h)

**Justificativa**: Necessário para corrigir violações hexagonais

**Tasks**:
1. **Extrair IndexCalculator** (4h)
   ```python
   # worker/domain/services/index_calculator.py
   class IndexCalculator:
       @staticmethod
       def ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
           ...
   ```

2. **Refatorar STACClient → PlanetaryComputerProvider** (6h)
   ```python
   # worker/infrastructure/adapters/satellite/planetary_computer_provider.py
   class PlanetaryComputerProvider(ISatelliteProvider):
       ...
   ```

3. **Criar ProviderRegistry** (2h)
   ```python
   # worker/infrastructure/providers/registry.py
   def get_satellite_provider() -> ISatelliteProvider:
       return PlanetaryComputerProvider()
   ```

4. **Migrar Jobs** (2h)
   - `process_topography.py`
   - `process_radar.py`
   - `process_satellite.py`

**Critério de Sucesso**: `stac_client.py` deletado, 0 imports dele

---

### Prioridade 2: FASE 4 antes de FASE 2 (8h)

**Justificativa**: Circuit breakers já implementados, aproveitar

**Mudança de Ordem**:
- ~~FASE 2 → FASE 3 → FASE 4~~
- **FASE 4 → FASE 2 → FASE 3** ✅

**Razão**: 
- Circuit breakers já existem em `infrastructure/resilience.py`
- Fallback chain pode usar apenas PC + Cache inicialmente
- CDSE (FASE 2) pode ser adicionado depois

**Tasks**:
1. Criar `FallbackChainProvider` (4h)
2. Integrar com circuit breakers existentes (2h)
3. Configurar fallback: PC → Cache (2h)

---

### Prioridade 3: FASE 3 (Cache) (6h)

**Tasks**:
1. Criar `STACMetadataCache` usando Redis (4h)
2. Integrar com `FallbackChainProvider` (2h)

---

### Prioridade 4: FASE 2 (CDSE) (12h)

**Tasks**:
1. Implementar `CDSEProvider` (8h)
2. Configurar OAuth2 (2h)
3. Adicionar ao fallback chain (2h)

---

## 🔄 Plano Revisado

### Ordem Recomendada

| Fase | Descrição | Esforço | Prioridade |
|------|-----------|---------|------------|
| **1A** | Completar FASE 1 (IndexCalculator + PC Provider) | 14h | P0 |
| **4** | FASE 4 (Fallback Chain + Circuit Breaker) | 8h | P0 |
| **3** | FASE 3 (Cache Redis) | 6h | P1 |
| **2** | FASE 2 (CDSE Provider) | 12h | P2 |

**Total**: 40h (~5 dias)

---

## ✅ Validação com Audit Report

### Compliance com ARCHITECTURE_AUDIT_REPORT.md

**✅ Alinhado**:
- Resilience patterns implementados (circuit breakers)
- Hexagonal architecture seguida (ports + adapters)
- Naming conventions PEP 8

**⚠️  Conflitos**:
- `STACClient` ainda existe (viola Domain purity)
- Falta DI Container para providers

**Solução**: Completar FASE 1 resolve ambos

---

## 🎯 Next Steps

1. ✅ Aprovar plano revisado
2. ⏳ Criar branch: `feat/data-provider-resilience`
3. ⏳ Executar FASE 1A (14h)
4. ⏳ Executar FASE 4 (8h)
5. ⏳ Validar com testes de integração
6. ⏳ Executar FASE 3 e 2 (opcional)

---

## 📊 Métricas de Sucesso

| Métrica | Antes | Meta | Validação |
|---------|-------|------|-----------|
| Providers implementados | 1 (PC) | 3 (PC, CDSE, Cache) | Código |
| STACClient deletado | ❌ | ✅ | `git rm stac_client.py` |
| Circuit breakers ativos | 2 (SQS/S3) | 5 (+ PC, CDSE, Cache) | Logs |
| Failover automático | ❌ | ✅ | Teste de resiliência |
| Cache hit rate | 0% | >60% | Redis metrics |

---

## 🔗 Documentos Relacionados

- [ARCHITECTURE_AUDIT_REPORT.md](file:///c:/projects/vivacampo-app/ai/ARCHITECTURE_AUDIT_REPORT.md)
- [ARCHITECTURE_IMPLEMENTATION_PLAN.md](file:///c:/projects/vivacampo-app/ai/ARCHITECTURE_IMPLEMENTATION_PLAN.md)
- [PLAN-DATA-PROVIDER-RESILIENCE.md](file:///c:/projects/vivacampo-app/ai/PLAN-DATA-PROVIDER-RESILIENCE.md)
