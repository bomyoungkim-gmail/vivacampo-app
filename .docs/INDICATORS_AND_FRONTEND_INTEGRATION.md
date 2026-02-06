# Gerenciamento de Indicadores e Integração com Frontend

## Visão Geral

Este documento responde duas perguntas críticas sobre a arquitetura hexagonal:

1. **Gerenciamento de Indicadores**: Como adicionar, remover ou substituir indicadores (NDVI, NDWI, NDRE, SAVI, EVI, etc.) de forma fácil?
2. **Integração Frontend**: Como o frontend (React/Next.js) se integra com as novas camadas (Presentation, Application, Domain)?

---

## 1. Gerenciamento de Indicadores com Arquitetura Hexagonal

### 1.1 Por Que É Fácil?

Com a arquitetura hexagonal, **adicionar um novo indicador requer mudanças em apenas 2 lugares**:

1. **Configuração do Domínio** (1 linha) → Adicionar ao enum de indicadores disponíveis
2. **Lógica de Cálculo** (1 método) → Implementar fórmula matemática

**NÃO é necessário mudar**:
- ❌ Infraestrutura (adaptadores satellite, storage)
- ❌ Repositórios (PostgreSQL, queries)
- ❌ Banco de dados (schema, migrações)
- ❌ Presentation layer (routers FastAPI)
- ❌ Application layer (use cases)

### 1.2 Estrutura Atual de Indicadores

```python
# services/api/app/domain/entities/vegetation_index.py

from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any

class IndexType(str, Enum):
    """Indicadores disponíveis no sistema"""
    NDVI = "ndvi"
    NDWI = "ndwi"
    NDRE = "ndre"
    MSAVI = "msavi"
    # FÁCIL: Adicionar novo indicador aqui!
    # SAVI = "savi"
    # EVI = "evi"
    # GNDVI = "gndvi"

class VegetationIndex(BaseModel):
    """Value Object - Índice de vegetação calculado"""
    index_type: IndexType
    value: float = Field(ge=-1.0, le=1.0)  # Validação automática
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        validate_assignment=True,
        frozen=True  # Imutável após criação
    )
```

### 1.3 Como Adicionar um Novo Indicador (Exemplo: SAVI)

**PASSO 1**: Adicionar ao enum (1 linha)

```python
# services/api/app/domain/entities/vegetation_index.py

class IndexType(str, Enum):
    NDVI = "ndvi"
    NDWI = "ndwi"
    NDRE = "ndre"
    MSAVI = "msavi"
    SAVI = "savi"  # ← NOVO INDICADOR
```

**PASSO 2**: Implementar cálculo no Domain Service (1 método)

```python
# services/api/app/domain/services/vegetation_calculator.py

from typing import Dict
import numpy as np

class VegetationCalculatorService:
    """Domain Service - Cálculos de índices de vegetação"""

    # Constantes específicas de cada índice
    SAVI_L_FACTOR = 0.5  # Fator de ajuste de solo

    def calculate_index(
        self,
        index_type: IndexType,
        bands: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """
        Calcula índice de vegetação baseado no tipo.

        Args:
            index_type: Tipo de índice (NDVI, NDWI, SAVI, etc.)
            bands: Dicionário com arrays das bandas espectrais
                   {"red": array, "nir": array, "green": array, ...}

        Returns:
            Array NumPy com valores do índice calculado
        """
        if index_type == IndexType.NDVI:
            return self._calculate_ndvi(bands)
        elif index_type == IndexType.NDWI:
            return self._calculate_ndwi(bands)
        elif index_type == IndexType.NDRE:
            return self._calculate_ndre(bands)
        elif index_type == IndexType.MSAVI:
            return self._calculate_msavi(bands)
        elif index_type == IndexType.SAVI:
            return self._calculate_savi(bands)  # ← NOVO MÉTODO
        else:
            raise ValueError(f"Índice não suportado: {index_type}")

    def _calculate_ndvi(self, bands: Dict[str, np.ndarray]) -> np.ndarray:
        """NDVI = (NIR - Red) / (NIR + Red)"""
        nir = bands["nir"].astype(float)
        red = bands["red"].astype(float)

        denominator = nir + red
        denominator[denominator == 0] = np.nan

        ndvi = (nir - red) / denominator
        return np.clip(ndvi, -1.0, 1.0)

    def _calculate_ndwi(self, bands: Dict[str, np.ndarray]) -> np.ndarray:
        """NDWI = (Green - NIR) / (Green + NIR)"""
        green = bands["green"].astype(float)
        nir = bands["nir"].astype(float)

        denominator = green + nir
        denominator[denominator == 0] = np.nan

        ndwi = (green - nir) / denominator
        return np.clip(ndwi, -1.0, 1.0)

    def _calculate_ndre(self, bands: Dict[str, np.ndarray]) -> np.ndarray:
        """NDRE = (NIR - Red Edge) / (NIR + Red Edge)"""
        nir = bands["nir"].astype(float)
        red_edge = bands["red_edge"].astype(float)

        denominator = nir + red_edge
        denominator[denominator == 0] = np.nan

        ndre = (nir - red_edge) / denominator
        return np.clip(ndre, -1.0, 1.0)

    def _calculate_msavi(self, bands: Dict[str, np.ndarray]) -> np.ndarray:
        """
        MSAVI = (2*NIR + 1 - sqrt((2*NIR + 1)^2 - 8*(NIR - Red))) / 2
        Modified Soil Adjusted Vegetation Index
        """
        nir = bands["nir"].astype(float)
        red = bands["red"].astype(float)

        term = 2 * nir + 1
        msavi = (term - np.sqrt(term**2 - 8 * (nir - red))) / 2
        return np.clip(msavi, -1.0, 1.0)

    # ← NOVO MÉTODO PARA SAVI
    def _calculate_savi(self, bands: Dict[str, np.ndarray]) -> np.ndarray:
        """
        SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)
        Soil Adjusted Vegetation Index
        L = 0.5 (fator de ajuste de solo)
        """
        nir = bands["nir"].astype(float)
        red = bands["red"].astype(float)
        L = self.SAVI_L_FACTOR

        denominator = nir + red + L
        denominator[denominator == 0] = np.nan

        savi = ((nir - red) / denominator) * (1 + L)
        return np.clip(savi, -1.0, 1.0)

    def get_required_bands(self, index_type: IndexType) -> set[str]:
        """
        Retorna quais bandas espectrais são necessárias para cada índice.
        Útil para validação antes de calcular.
        """
        requirements = {
            IndexType.NDVI: {"red", "nir"},
            IndexType.NDWI: {"green", "nir"},
            IndexType.NDRE: {"red_edge", "nir"},
            IndexType.MSAVI: {"red", "nir"},
            IndexType.SAVI: {"red", "nir"},  # ← NOVO REQUISITO
        }
        return requirements.get(index_type, set())
```

**PRONTO!** O novo indicador SAVI agora funciona em todo o sistema:
- ✅ API aceita `"savi"` como parâmetro
- ✅ Domain Service calcula corretamente
- ✅ Validação Pydantic garante valores entre -1.0 e 1.0
- ✅ Frontend pode solicitar SAVI via API

### 1.4 Remover ou Substituir Indicadores

**Remover** um indicador (exemplo: remover MSAVI):

```python
# PASSO 1: Remover do enum
class IndexType(str, Enum):
    NDVI = "ndvi"
    NDWI = "ndwi"
    NDRE = "ndre"
    # MSAVI = "msavi"  # ← COMENTADO ou REMOVIDO

# PASSO 2: Remover método de cálculo (opcional, para limpeza)
# def _calculate_msavi(self, bands): ...  # ← REMOVIDO
```

**Substituir** um indicador (exemplo: trocar MSAVI por SAVI):

```python
# Simplesmente remova o antigo e adicione o novo seguindo passos acima
class IndexType(str, Enum):
    NDVI = "ndvi"
    NDWI = "ndwi"
    NDRE = "ndre"
    # MSAVI = "msavi"  # ← REMOVIDO
    SAVI = "savi"      # ← ADICIONADO
```

### 1.5 Por Que Arquitetura Hexagonal Facilita?

**Separação de Responsabilidades**:
- **Domínio**: Contém lógica de negócio (cálculos matemáticos)
- **Infraestrutura**: Busca dados de satélite (bandas espectrais)
- **Application**: Orquestra o fluxo (buscar bandas → calcular índice → salvar)

**Indicadores são Conceitos de Domínio**:
- Não dependem de tecnologia (PostgreSQL, AWS, etc.)
- Não dependem de fornecedor (Planetary Computer, CDSE)
- São apenas **fórmulas matemáticas puras**

**Exemplo de Fluxo Completo** (adicionar SAVI):

```
1. Frontend solicita: GET /api/aois/123/indices?type=savi&date=2025-01-15
2. Presentation Router valida request
3. Application Use Case orquestra:
   a. Busca cena de satélite via ISatelliteProvider (infraestrutura)
   b. Extrai bandas Red e NIR
   c. Chama VegetationCalculatorService.calculate_index(SAVI, bands)
   d. Domain Service retorna array com valores SAVI
   e. Salva resultado via IIndexRepository (infraestrutura)
4. Presentation Router retorna DTO para frontend
```

**Mudança isolada**: Apenas o Domain Service (passo 3c) mudou!

---

## 2. Integração Frontend com Arquitetura Hexagonal

### 2.1 Visão Geral do Fluxo

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (React/Next.js)                                        │
│ - Componentes React                                             │
│ - API Client (fetch/axios)                                      │
│ - TypeScript Types (gerados de Pydantic)                        │
└─────────────────────────────────────────────────────────────────┘
                              ▼
                     HTTP Request (JSON)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER (FastAPI Routers)                            │
│ - Recebe HTTP Request                                           │
│ - Valida com Pydantic Request DTO                               │
│ - Extrai tenant_id do JWT                                       │
│ - Chama Application Use Case                                    │
│ - Converte Domain Entity → Response DTO                         │
│ - Retorna HTTP Response (JSON)                                  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ APPLICATION LAYER (Use Cases)                                   │
│ - Recebe Command DTO (validado)                                 │
│ - Orquestra Domain Services e Repositories                      │
│ - Coordena transações                                           │
│ - Retorna Domain Entity                                         │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ DOMAIN LAYER (Entities, Services, Value Objects)                │
│ - Executa lógica de negócio                                     │
│ - Valida regras de domínio                                      │
│ - Garante invariantes                                           │
│ - Independente de tecnologia                                    │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER (Adapters, Repositories)                   │
│ - PostgreSQL Repository                                         │
│ - S3 Adapter                                                    │
│ - Satellite Provider Adapter                                    │
│ - External APIs                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Exemplo Completo: Solicitar Índice NDVI

#### Frontend (React Component)

```typescript
// services/app-ui/src/components/VegetationIndexChart.tsx

import { useState, useEffect } from 'react';
import { getVegetationIndex } from '@/lib/api';
import type { VegetationIndexResponse } from '@/lib/types';

interface VegetationIndexChartProps {
  aoiId: string;
  indexType: 'ndvi' | 'ndwi' | 'ndre' | 'savi';
  dateRange: { start: string; end: string };
}

export function VegetationIndexChart({
  aoiId,
  indexType,
  dateRange
}: VegetationIndexChartProps) {
  const [data, setData] = useState<VegetationIndexResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);

      try {
        const response = await getVegetationIndex({
          aoiId,
          indexType,
          startDate: dateRange.start,
          endDate: dateRange.end
        });

        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro ao buscar dados');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [aoiId, indexType, dateRange]);

  if (loading) return <div>Carregando...</div>;
  if (error) return <div>Erro: {error}</div>;
  if (!data) return null;

  return (
    <div>
      <h2>Índice {indexType.toUpperCase()}</h2>
      <p>Média: {data.statistics.mean.toFixed(3)}</p>
      <p>Desvio Padrão: {data.statistics.std.toFixed(3)}</p>
      {/* Renderizar gráfico com data.timeSeries */}
    </div>
  );
}
```

#### Frontend (API Client)

```typescript
// services/app-ui/src/lib/api.ts

import { API_BASE_URL } from './constants';

// TypeScript types gerados de Pydantic schemas
export interface VegetationIndexRequest {
  aoiId: string;
  indexType: 'ndvi' | 'ndwi' | 'ndre' | 'savi';
  startDate: string;  // ISO 8601
  endDate: string;    // ISO 8601
}

export interface VegetationIndexResponse {
  aoiId: string;
  indexType: string;
  dateRange: {
    start: string;
    end: string;
  };
  statistics: {
    mean: number;
    median: number;
    std: number;
    min: number;
    max: number;
  };
  timeSeries: Array<{
    date: string;
    value: number;
    confidence: number;
  }>;
  metadata: {
    scenes_processed: number;
    cloud_coverage_avg: number;
  };
}

export async function getVegetationIndex(
  request: VegetationIndexRequest
): Promise<VegetationIndexResponse> {
  const { aoiId, indexType, startDate, endDate } = request;

  // Construir query params
  const params = new URLSearchParams({
    index_type: indexType,
    start_date: startDate,
    end_date: endDate
  });

  const url = `${API_BASE_URL}/aois/${aoiId}/vegetation-indices?${params}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Erro ao buscar índice de vegetação');
  }

  return response.json();
}

function getAuthToken(): string {
  // Recuperar token JWT do localStorage, cookie, etc.
  return localStorage.getItem('auth_token') || '';
}
```

#### Backend: Presentation Layer (FastAPI Router)

```python
# services/api/app/presentation/routers/vegetation_indices_router.py

from fastapi import APIRouter, Depends, Query
from uuid import UUID
from datetime import date
from typing import Annotated

from app.presentation.dependencies import (
    get_current_tenant_id,
    get_vegetation_index_use_case
)
from app.presentation.dtos.vegetation_index_dtos import (
    VegetationIndexResponseDTO
)
from app.application.use_cases.get_vegetation_index import (
    GetVegetationIndexUseCase,
    GetVegetationIndexCommand
)
from app.domain.entities.vegetation_index import IndexType

router = APIRouter(prefix="/aois", tags=["vegetation-indices"])

@router.get(
    "/{aoi_id}/vegetation-indices",
    response_model=VegetationIndexResponseDTO,
    summary="Get vegetation index time series for AOI"
)
async def get_vegetation_index(
    aoi_id: UUID,
    index_type: IndexType = Query(..., description="Type of vegetation index"),
    start_date: date = Query(..., description="Start date (ISO 8601)"),
    end_date: date = Query(..., description="End date (ISO 8601)"),
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)],
    use_case: Annotated[GetVegetationIndexUseCase, Depends(get_vegetation_index_use_case)]
):
    """
    Retrieve vegetation index time series for an Area of Interest.

    Supports: NDVI, NDWI, NDRE, MSAVI, SAVI

    Security: Multi-tenant isolation via JWT tenant_id
    """
    # 1. Criar Command (validado por Pydantic)
    command = GetVegetationIndexCommand(
        tenant_id=tenant_id,
        aoi_id=aoi_id,
        index_type=index_type,
        start_date=start_date,
        end_date=end_date
    )

    # 2. Executar Use Case (Application Layer)
    result = await use_case.execute(command)

    # 3. Converter Domain Entity → Response DTO
    response_dto = VegetationIndexResponseDTO.from_domain(result)

    return response_dto
```

#### Backend: Presentation DTOs

```python
# services/api/app/presentation/dtos/vegetation_index_dtos.py

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date
from typing import List

class DateRangeDTO(BaseModel):
    """DTO para período de datas"""
    start: date
    end: date

class VegetationIndexStatisticsDTO(BaseModel):
    """DTO para estatísticas do índice"""
    mean: float = Field(..., ge=-1.0, le=1.0)
    median: float = Field(..., ge=-1.0, le=1.0)
    std: float = Field(..., ge=0.0)
    min: float = Field(..., ge=-1.0, le=1.0)
    max: float = Field(..., ge=-1.0, le=1.0)

class VegetationIndexTimeSeriesPointDTO(BaseModel):
    """DTO para ponto na série temporal"""
    date: date
    value: float = Field(..., ge=-1.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)

class VegetationIndexMetadataDTO(BaseModel):
    """DTO para metadados do processamento"""
    scenes_processed: int = Field(..., ge=0)
    cloud_coverage_avg: float = Field(..., ge=0.0, le=100.0)

class VegetationIndexResponseDTO(BaseModel):
    """
    Response DTO enviado para frontend.

    Imutável (frozen=True) para garantir que não seja modificado
    após serialização.
    """
    aoi_id: UUID
    index_type: str
    date_range: DateRangeDTO
    statistics: VegetationIndexStatisticsDTO
    time_series: List[VegetationIndexTimeSeriesPointDTO]
    metadata: VegetationIndexMetadataDTO

    model_config = ConfigDict(
        frozen=True,  # Imutável
        validate_assignment=True,
        extra="forbid"
    )

    @classmethod
    def from_domain(cls, domain_result: 'VegetationIndexTimeSeries') -> 'VegetationIndexResponseDTO':
        """
        Converte Domain Entity → Response DTO.

        Essa transformação acontece na Presentation Layer.
        """
        return cls(
            aoi_id=domain_result.aoi_id,
            index_type=domain_result.index_type.value,
            date_range=DateRangeDTO(
                start=domain_result.date_range.start,
                end=domain_result.date_range.end
            ),
            statistics=VegetationIndexStatisticsDTO(
                mean=domain_result.statistics.mean,
                median=domain_result.statistics.median,
                std=domain_result.statistics.std,
                min=domain_result.statistics.min,
                max=domain_result.statistics.max
            ),
            time_series=[
                VegetationIndexTimeSeriesPointDTO(
                    date=point.date,
                    value=point.value,
                    confidence=point.confidence
                )
                for point in domain_result.time_series
            ],
            metadata=VegetationIndexMetadataDTO(
                scenes_processed=domain_result.metadata.scenes_processed,
                cloud_coverage_avg=domain_result.metadata.cloud_coverage_avg
            )
        )
```

#### Backend: Application Layer (Use Case)

```python
# services/api/app/application/use_cases/get_vegetation_index.py

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date

from app.domain.entities.vegetation_index import IndexType
from app.domain.services.vegetation_calculator import VegetationCalculatorService
from app.domain.repositories.aoi_repository import IAOIRepository
from app.infrastructure.adapters.satellite.satellite_adapter import ISatelliteProvider

class GetVegetationIndexCommand(BaseModel):
    """
    Command DTO - Entrada para o Use Case.

    Validado por Pydantic na Presentation Layer.
    """
    tenant_id: UUID
    aoi_id: UUID
    index_type: IndexType
    start_date: date
    end_date: date

    model_config = ConfigDict(
        frozen=True,  # Imutável
        validate_assignment=True
    )

class GetVegetationIndexUseCase:
    """
    Application Use Case - Orquestra busca de índice de vegetação.

    Coordena:
    1. Verificar permissões (tenant_id)
    2. Buscar AOI do repositório
    3. Buscar cenas de satélite via adapter
    4. Calcular índice via domain service
    5. Retornar resultado
    """

    def __init__(
        self,
        aoi_repository: IAOIRepository,
        satellite_provider: ISatelliteProvider,
        vegetation_calculator: VegetationCalculatorService
    ):
        self.aoi_repository = aoi_repository
        self.satellite_provider = satellite_provider
        self.vegetation_calculator = vegetation_calculator

    async def execute(self, command: GetVegetationIndexCommand) -> 'VegetationIndexTimeSeries':
        """
        Executa o caso de uso.

        Raises:
            AOINotFoundError: Se AOI não existir
            TenantMismatchError: Se AOI pertencer a outro tenant
            NoScenesFoundError: Se não houver cenas disponíveis
        """
        # 1. Buscar AOI e validar tenant
        aoi = await self.aoi_repository.find_by_id(
            command.aoi_id,
            tenant_id=command.tenant_id
        )
        if not aoi:
            raise AOINotFoundError(f"AOI {command.aoi_id} não encontrada")

        # 2. Buscar cenas de satélite
        scenes = await self.satellite_provider.search_scenes(
            bbox=aoi.geometry.bounds,
            date_range=(command.start_date, command.end_date),
            max_cloud_coverage=20.0
        )

        if not scenes:
            raise NoScenesFoundError("Nenhuma cena encontrada para período")

        # 3. Processar cada cena
        time_series_points = []

        for scene in scenes:
            # Baixar bandas necessárias
            bands = await self.satellite_provider.download_bands(
                scene_id=scene.id,
                bands=self.vegetation_calculator.get_required_bands(command.index_type)
            )

            # Calcular índice
            index_array = self.vegetation_calculator.calculate_index(
                command.index_type,
                bands
            )

            # Agregar estatísticas (média da AOI)
            mean_value = float(np.nanmean(index_array))

            time_series_points.append(
                VegetationIndexTimeSeriesPoint(
                    date=scene.acquisition_date,
                    value=mean_value,
                    confidence=1.0 - (scene.cloud_coverage / 100.0)
                )
            )

        # 4. Calcular estatísticas gerais
        values = [p.value for p in time_series_points]
        statistics = VegetationIndexStatistics(
            mean=float(np.mean(values)),
            median=float(np.median(values)),
            std=float(np.std(values)),
            min=float(np.min(values)),
            max=float(np.max(values))
        )

        # 5. Retornar Domain Entity
        return VegetationIndexTimeSeries(
            aoi_id=aoi.id,
            index_type=command.index_type,
            date_range=DateRange(start=command.start_date, end=command.end_date),
            statistics=statistics,
            time_series=time_series_points,
            metadata=VegetationIndexMetadata(
                scenes_processed=len(scenes),
                cloud_coverage_avg=float(np.mean([s.cloud_coverage for s in scenes]))
            )
        )
```

### 2.3 Geração Automática de TypeScript Types

**Ferramenta**: Usar `datamodel-code-generator` para gerar types TypeScript a partir de Pydantic schemas.

```bash
# Instalar ferramenta
pip install datamodel-code-generator

# Gerar types TypeScript
datamodel-codegen \
  --input services/api/app/presentation/dtos \
  --input-file-type python \
  --output services/app-ui/src/lib/generated-types.ts \
  --output-model-type typescript
```

**Resultado**:

```typescript
// services/app-ui/src/lib/generated-types.ts (GERADO AUTOMATICAMENTE)

export interface DateRangeDTO {
  start: string;  // date (ISO 8601)
  end: string;    // date (ISO 8601)
}

export interface VegetationIndexStatisticsDTO {
  mean: number;   // -1.0 to 1.0
  median: number; // -1.0 to 1.0
  std: number;    // >= 0.0
  min: number;    // -1.0 to 1.0
  max: number;    // -1.0 to 1.0
}

export interface VegetationIndexTimeSeriesPointDTO {
  date: string;      // date (ISO 8601)
  value: number;     // -1.0 to 1.0
  confidence: number; // 0.0 to 1.0
}

export interface VegetationIndexMetadataDTO {
  scenes_processed: number;  // >= 0
  cloud_coverage_avg: number; // 0.0 to 100.0
}

export interface VegetationIndexResponseDTO {
  aoi_id: string;  // UUID
  index_type: string;
  date_range: DateRangeDTO;
  statistics: VegetationIndexStatisticsDTO;
  time_series: VegetationIndexTimeSeriesPointDTO[];
  metadata: VegetationIndexMetadataDTO;
}
```

**Uso no Frontend**:

```typescript
// services/app-ui/src/lib/api.ts

import type {
  VegetationIndexResponseDTO
} from './generated-types';

// Agora VegetationIndexResponseDTO é importado, não definido manualmente!
export async function getVegetationIndex(...): Promise<VegetationIndexResponseDTO> {
  // ...
}
```

### 2.4 Fluxo de Dados Completo

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. Frontend Component (React)                                    │
│    const data = await getVegetationIndex(params)                 │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. API Client (fetch)                                            │
│    GET /aois/{id}/vegetation-indices?index_type=ndvi&...         │
│    Headers: { Authorization: "Bearer <JWT>" }                    │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. FastAPI Router (Presentation Layer)                           │
│    - Extrai tenant_id do JWT                                     │
│    - Valida params com Pydantic                                  │
│    - Cria GetVegetationIndexCommand                              │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. Use Case (Application Layer)                                  │
│    - Busca AOI via IAOIRepository                                │
│    - Busca cenas via ISatelliteProvider                          │
│    - Calcula índice via VegetationCalculatorService              │
│    - Retorna VegetationIndexTimeSeries (Domain Entity)           │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. FastAPI Router (Presentation Layer)                           │
│    - Converte Domain Entity → VegetationIndexResponseDTO         │
│    - Serializa para JSON                                         │
│    - Retorna HTTP 200 + JSON                                     │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 6. API Client (fetch)                                            │
│    - Recebe JSON response                                        │
│    - Parseia para VegetationIndexResponseDTO (TypeScript)        │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ 7. Frontend Component (React)                                    │
│    - Renderiza gráfico com data.time_series                      │
│    - Exibe estatísticas com data.statistics                      │
└──────────────────────────────────────────────────────────────────┘
```

### 2.5 Benefícios da Separação de Camadas para o Frontend

**1. Contratos Claros via Pydantic DTOs**:
- Frontend sabe exatamente o formato de request/response
- Validação automática de tipos no backend
- TypeScript types gerados automaticamente

**2. Frontend Desacoplado da Lógica de Negócio**:
- Frontend não sabe (e não precisa saber):
  - Como dados são calculados (VegetationCalculatorService)
  - Onde dados são armazenados (PostgreSQL, S3)
  - Qual fornecedor de satélite é usado (Planetary Computer vs CDSE)
- Frontend só conhece a **API REST** (contrato público)

**3. Mudanças Internas Não Afetam Frontend**:
- Trocar PostgreSQL por MongoDB → Frontend não muda
- Trocar Planetary Computer por CDSE → Frontend não muda
- Adicionar cache Redis → Frontend não muda
- Adicionar novo indicador SAVI → Frontend adiciona apenas opção no dropdown

**4. Testabilidade**:
- Frontend pode mockar API responses usando DTOs
- Backend pode testar use cases sem rodar frontend
- Cada camada testada independentemente

**5. Versionamento de API**:
- Apresentação layer pode ter múltiplas versões:
  - `/v1/aois/{id}/vegetation-indices` (DTOs antigos)
  - `/v2/aois/{id}/vegetation-indices` (DTOs novos)
- Domain layer permanece único e estável
- Migrations graduais sem quebrar frontend legado

---

## 3. Resumo Executivo

### 3.1 Gerenciamento de Indicadores

**Sim, é extremamente fácil!**

| Operação | Passos Necessários | Arquivos Afetados |
|----------|-------------------|-------------------|
| **Adicionar novo indicador** | 1. Adicionar ao enum<br>2. Implementar cálculo | 2 arquivos |
| **Remover indicador** | 1. Remover do enum | 1 arquivo |
| **Substituir indicador** | 1. Remover antigo do enum<br>2. Adicionar novo ao enum<br>3. Implementar cálculo | 2 arquivos |

**NÃO requer**:
- ❌ Mudanças no banco de dados
- ❌ Mudanças na infraestrutura
- ❌ Mudanças nos repositórios
- ❌ Mudanças nos routers
- ❌ Reescrever testes de integração

### 3.2 Integração Frontend

**Fluxo Completo**:

```
Frontend (React)
  → API Client (fetch)
    → Presentation Router (FastAPI)
      → Application Use Case
        → Domain Service (cálculo NDVI)
          → Infrastructure Adapter (Planetary Computer)
```

**Frontend só conhece**:
- ✅ URL do endpoint
- ✅ Request params (DTOs)
- ✅ Response format (DTOs)

**Frontend NÃO conhece**:
- ❌ Lógica de negócio (cálculos)
- ❌ Banco de dados (PostgreSQL)
- ❌ Fornecedores externos (Planetary Computer)
- ❌ Infraestrutura (S3, SQS)

**Vantagens**:
- Frontend evolui independentemente do backend
- Backend pode mudar implementação sem afetar frontend
- Contratos garantidos por Pydantic + TypeScript
- Testes isolados em cada camada

---

## 4. Próximos Passos

1. **Implementar Domain Service de Indicadores** (Fase 3 do plano)
2. **Criar DTOs de Request/Response** (Fase 4)
3. **Implementar Presentation Router** (Fase 4)
4. **Gerar TypeScript Types** com `datamodel-code-generator`
5. **Atualizar Frontend Components** para usar nova API

Essa estrutura garante:
- ✅ **Indicadores fáceis de adicionar/remover**
- ✅ **Frontend desacoplado da lógica interna**
- ✅ **Contratos validados automaticamente**
- ✅ **Testes isolados em cada camada**
- ✅ **Evolução independente de frontend e backend**
