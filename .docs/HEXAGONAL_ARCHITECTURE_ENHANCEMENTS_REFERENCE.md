# Melhorias Críticas - Arquitetura Hexagonal VivaCampo

**Data:** 2026-02-05
**Complemento ao:** [HEXAGONAL_ARCHITECTURE_PLAN.md](HEXAGONAL_ARCHITECTURE_PLAN.md)

---

## Índice

1. [Pydantic para Reforçar Contratos](#pydantic-contratos)
2. [Fallbacks em Cada Camada](#fallbacks-resiliencia)
3. [Testes Locais Sem Mockup](#testes-reais)

---

## 1. Pydantic para Reforçar Contratos {#pydantic-contratos}

### Problema Atual

O plano original usa:
- Type hints + `@dataclass` para entities
- Abstract Base Classes (ABC) para ports
- **Problema:** Validação em runtime fraca, fácil passar dados inválidos entre camadas

### Solução: Pydantic em Todas as Camadas

**Princípio:** Cada camada valida dados na entrada/saída usando Pydantic

```
┌─────────────────────────────────────────┐
│ Presentation Layer                      │
│ ├─ FastAPI (Pydantic models nativos)    │ ← HTTP Request
│ └─ PydanticCommand → Use Case           │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Application Layer                       │
│ ├─ Command (Pydantic BaseModel)         │ ← Valida entrada
│ ├─ Use Case executa lógica              │
│ └─ DTO Response (Pydantic)              │ ← Valida saída
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Domain Layer                            │
│ ├─ Entity (Pydantic BaseModel)          │ ← Validação de negócio
│ └─ Port retorna Entity                  │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Infrastructure Layer                    │
│ ├─ Adapter recebe Entity (Pydantic)     │
│ ├─ Converte para SQLAlchemy/boto3       │
│ └─ Converte resposta → Entity (valida)  │ ← Valida dados externos
└─────────────────────────────────────────┘
```

---

### Implementação por Camada

#### Domain Layer - Entities com Pydantic

**Arquivo:** `services/api/app/domain/entities/farm.py`

```python
"""
Farm domain entity com Pydantic.
Validação de negócio automática.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional


class Farm(BaseModel):
    """
    Fazenda - Agregado raiz com validação Pydantic.

    Regras de Negócio (validadas automaticamente):
    - Nome: 3-100 caracteres
    - Timezone: deve estar em pytz.all_timezones
    - Tenant ID: obrigatório (multi-tenancy)
    """

    model_config = ConfigDict(
        frozen=False,  # Permite atualizações
        validate_assignment=True,  # Valida em toda atribuição
        str_strip_whitespace=True,  # Remove espaços
    )

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str = Field(min_length=3, max_length=100)
    timezone: str = Field(default="America/Sao_Paulo")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Valida timezone usando pytz"""
        import pytz
        if v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}. Must be in pytz.all_timezones")
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validação customizada de nome"""
        if v.lower() in ['test', 'admin', 'system']:
            raise ValueError("Reserved farm name")
        return v

    def update_name(self, new_name: str) -> None:
        """
        Atualiza nome (validação automática via validate_assignment).
        Raises ValidationError se inválido.
        """
        self.name = new_name  # Pydantic valida automaticamente
        self.updated_at = datetime.utcnow()


# Exemplo de uso
try:
    farm = Farm(tenant_id=uuid4(), name="AB")  # ERRO: nome < 3 chars
except ValidationError as e:
    print(e.json())
    # {
    #   "name": ["String should have at least 3 characters"]
    # }
```

**Benefícios:**
- ✅ Validação automática em criação e atualização
- ✅ Mensagens de erro estruturadas (JSON)
- ✅ Type safety em runtime (não só em mypy)
- ✅ Serialização/deserialização automática

---

#### Application Layer - Commands e DTOs com Pydantic

**Arquivo:** `services/api/app/application/use_cases/farms/create_farm.py`

```python
"""
Create Farm use case com Pydantic Commands/DTOs.
"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from typing import Optional

from app.domain.entities.farm import Farm
from app.domain.ports.farm_repository import IFarmRepository


class CreateFarmCommand(BaseModel):
    """
    Input DTO - valida dados da apresentação.
    Garante que use case recebe dados válidos.
    """

    model_config = ConfigDict(frozen=True)  # Imutável (command pattern)

    tenant_id: UUID
    name: str = Field(min_length=3, max_length=100)
    timezone: str = Field(default="America/Sao_Paulo")


class CreateFarmResponse(BaseModel):
    """
    Output DTO - contrato de resposta.
    Garante que use case retorna estrutura esperada.
    """

    model_config = ConfigDict(frozen=True)

    farm_id: UUID
    name: str
    timezone: str
    created_at: datetime

    @classmethod
    def from_entity(cls, farm: Farm) -> "CreateFarmResponse":
        """Converte entity para DTO"""
        return cls(
            farm_id=farm.id,
            name=farm.name,
            timezone=farm.timezone,
            created_at=farm.created_at
        )


class CreateFarmUseCase:
    """Use case com contratos Pydantic fortes"""

    def __init__(self, farm_repository: IFarmRepository):
        self.farm_repository = farm_repository

    async def execute(self, command: CreateFarmCommand) -> CreateFarmResponse:
        """
        Executa criação de farm.

        Args:
            command: CreateFarmCommand (já validado)

        Returns:
            CreateFarmResponse (contrato garantido)

        Raises:
            ValidationError: Se entity inválida (nunca deve ocorrer)
            RepositoryError: Se falha ao persistir
        """
        # 1. Criar entity (validação automática de negócio)
        farm = Farm(
            tenant_id=command.tenant_id,
            name=command.name,
            timezone=command.timezone
        )

        # 2. Persistir via repository
        farm = await self.farm_repository.create(farm)

        # 3. Retornar DTO (contrato garantido)
        return CreateFarmResponse.from_entity(farm)
```

---

#### Infrastructure Layer - Adapters com Validação

**Arquivo:** `services/api/app/infrastructure/adapters/satellite/planetary_computer_adapter.py`

```python
"""
Planetary Computer adapter com validação Pydantic de dados externos.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.domain.ports.satellite_provider import ISatelliteProvider
from app.domain.entities.satellite_scene import SatelliteScene


class STACItemResponse(BaseModel):
    """
    Schema de resposta da STAC API.
    CRÍTICO: Valida dados externos antes de usar internamente.
    """

    model_config = ConfigDict(extra="ignore")  # Ignora campos desconhecidos

    id: str
    type: str = Field(pattern="^Feature$")
    geometry: Dict[str, Any]
    bbox: List[float] = Field(min_length=4, max_length=4)
    properties: Dict[str, Any]
    assets: Dict[str, Any]

    @field_validator('properties')
    @classmethod
    def validate_datetime(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Garante datetime existe"""
        if 'datetime' not in v:
            raise ValueError("STAC item missing 'datetime' in properties")
        return v

    @field_validator('bbox')
    @classmethod
    def validate_bbox(cls, v: List[float]) -> List[float]:
        """Valida bbox [minx, miny, maxx, maxy]"""
        if not (-180 <= v[0] <= 180 and -180 <= v[2] <= 180):
            raise ValueError(f"Invalid longitude in bbox: {v}")
        if not (-90 <= v[1] <= 90 and -90 <= v[3] <= 90):
            raise ValueError(f"Invalid latitude in bbox: {v}")
        return v


class PlanetaryComputerAdapter(ISatelliteProvider):
    """Adapter com validação de dados externos"""

    async def search_scenes(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        collections: Optional[List[str]] = None,
        max_cloud_cover: float = 60.0
    ) -> List[SatelliteScene]:
        """
        Busca cenas - VALIDA resposta da API antes de retornar.
        """
        # 1. Buscar dados da STAC API
        items = await self._fetch_stac_items(geometry, start_date, end_date)

        # 2. VALIDAR cada item com Pydantic
        validated_items = []
        for item_dict in items:
            try:
                validated = STACItemResponse(**item_dict)
                validated_items.append(validated)
            except ValidationError as e:
                logger.warning(
                    "stac_item_validation_failed",
                    item_id=item_dict.get('id'),
                    error=e.json()
                )
                # Continua processando outros itens
                continue

        # 3. Converter para domain entities
        scenes = []
        for item in validated_items:
            scene = SatelliteScene(
                id=item.id,
                datetime=datetime.fromisoformat(item.properties['datetime']),
                cloud_cover=item.properties.get('eo:cloud_cover', 100.0),
                platform=item.properties.get('platform', 'unknown'),
                collection=item.properties.get('collection', ''),
                bbox=item.bbox,
                geometry=item.geometry,
                assets=item.assets
            )
            scenes.append(scene)

        return scenes
```

**Benefícios:**
- ✅ Protege contra mudanças na API externa
- ✅ Detecta dados corrompidos/inválidos na origem
- ✅ Logs estruturados de falhas de validação
- ✅ Domain layer recebe sempre dados válidos

---

#### Presentation Layer - FastAPI com Pydantic Nativo

**Arquivo:** `services/api/app/presentation/farms_router.py`

```python
"""
Router com Pydantic request/response models.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from dependency_injector.wiring import inject, Provide

from app.infrastructure.di_container import Container
from app.application.use_cases.farms.create_farm import (
    CreateFarmUseCase,
    CreateFarmCommand,
    CreateFarmResponse
)


# Request model (input do usuário)
class CreateFarmRequest(BaseModel):
    """Schema de request HTTP"""
    name: str = Field(min_length=3, max_length=100, example="Fazenda Santa Rita")
    timezone: str = Field(default="America/Sao_Paulo", example="America/Sao_Paulo")


# Response model (output HTTP)
class CreateFarmHTTPResponse(BaseModel):
    """Schema de response HTTP"""
    id: str  # UUID como string para JSON
    name: str
    timezone: str
    created_at: str  # datetime como ISO string


router = APIRouter()


@router.post("/farms", response_model=CreateFarmHTTPResponse, status_code=201)
@inject
async def create_farm(
    request: CreateFarmRequest,  # FastAPI valida automaticamente
    use_case: CreateFarmUseCase = Depends(Provide[Container.create_farm_use_case]),
    tenant_id: UUID = Depends(get_current_tenant_id)
) -> CreateFarmHTTPResponse:
    """
    Cria nova farm.

    Fluxo de validação:
    1. FastAPI valida CreateFarmRequest (Pydantic)
    2. Converte para CreateFarmCommand (Pydantic)
    3. Use case valida comando novamente
    4. Domain entity valida regras de negócio (Pydantic)
    5. Resposta convertida para HTTP response (Pydantic)
    """
    try:
        # Converte HTTP request → Application command
        command = CreateFarmCommand(
            tenant_id=tenant_id,
            name=request.name,
            timezone=request.timezone
        )

        # Executa use case
        response = await use_case.execute(command)

        # Converte Application DTO → HTTP response
        return CreateFarmHTTPResponse(
            id=str(response.farm_id),
            name=response.name,
            timezone=response.timezone,
            created_at=response.created_at.isoformat()
        )

    except ValidationError as e:
        # Erro de validação Pydantic
        raise HTTPException(status_code=422, detail=e.errors())
    except RepositoryError as e:
        # Erro de infraestrutura
        raise HTTPException(status_code=500, detail="Failed to create farm")
```

---

### Validação em Múltiplas Camadas (Defense in Depth)

```
HTTP Request → Presentation → Application → Domain → Infrastructure
      ↓              ↓              ↓          ↓            ↓
  Pydantic      Pydantic       Pydantic   Pydantic     Pydantic
  (HTTP)        (Command)      (Entity)   (Port)       (External)
      ✓              ✓              ✓          ✓            ✓
```

**Exemplo de fluxo:**

1. **User envia:** `{"name": "AB", "timezone": "Invalid"}`
2. **Presentation:** FastAPI valida → ERRO 422 (nome < 3 chars)
3. **User corrige:** `{"name": "Fazenda", "timezone": "Invalid"}`
4. **Application:** CreateFarmCommand valida → OK
5. **Domain:** Farm entity valida timezone → ERRO (timezone inválido)
6. **User corrige:** `{"name": "Fazenda", "timezone": "America/Sao_Paulo"}`
7. **Infrastructure:** Repository salva → SQLAlchemy converte
8. **Response:** CreateFarmResponse → HTTP 201 Created

---

### Configuração Global do Pydantic

**Arquivo:** `services/api/app/config.py`

```python
"""
Configuração global do Pydantic para toda aplicação.
"""
from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    """
    Base class para todos os models da aplicação.
    Configuração rigorosa.
    """

    model_config = ConfigDict(
        # Validação
        validate_assignment=True,  # Valida em toda atribuição
        validate_default=True,     # Valida valores default
        str_strip_whitespace=True, # Remove espaços
        str_min_length=0,          # Não aceita strings vazias por padrão

        # Segurança
        extra="forbid",            # Rejeita campos extras
        frozen=False,              # Permite mutação (alterar para True em DTOs)

        # Serialização
        use_enum_values=True,      # Serializa enums como valores
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        },

        # Performance
        arbitrary_types_allowed=False,  # Só tipos nativos
    )


# Usar em todas as camadas
class Farm(StrictBaseModel):
    # ...

class CreateFarmCommand(StrictBaseModel):
    model_config = ConfigDict(frozen=True)  # Commands são imutáveis
    # ...
```

---

## 2. Fallbacks em Cada Camada {#fallbacks-resiliencia}

### Problema

Sistema atual **falha completamente** se um serviço externo está indisponível:
- Planetary Computer fora → NENHUMA cena processada
- S3 indisponível → NENHUM tile renderizado
- Open-Meteo fora → NENHUM dado de clima

### Solução: Resiliência em Camadas

```
┌──────────────────────────────────────────────────┐
│ Adapter Principal (ex: PlanetaryComputer)        │
│   ↓ FALHA (timeout, HTTP 503, etc)               │
│ Circuit Breaker detecta                          │
│   ↓ ABRE circuito                                │
│ Adapter Fallback (ex: CDSE)                      │
│   ↓ FALHA também                                 │
│ Degraded Mode (cache, dados históricos)         │
│   ↓ SEMPRE sucede                                │
│ ✅ Sistema continua funcionando (degradado)      │
└──────────────────────────────────────────────────┘
```

---

### Padrão 1: Satellite Provider com Fallback

**Arquivo:** `services/worker/worker/infrastructure/adapters/satellite/resilient_satellite_adapter.py`

```python
"""
Satellite adapter com fallback automático.
"""
import structlog
from typing import List, Optional
from datetime import datetime
from circuitbreaker import circuit

from app.domain.ports.satellite_provider import ISatelliteProvider
from app.domain.entities.satellite_scene import SatelliteScene

logger = structlog.get_logger()


class ResilientSatelliteAdapter(ISatelliteProvider):
    """
    Satellite provider com fallback chain:
    1. Planetary Computer (preferido)
    2. CDSE (fallback)
    3. Cache (última opção)
    """

    def __init__(
        self,
        primary: ISatelliteProvider,  # PlanetaryComputerAdapter
        fallback: ISatelliteProvider,  # CDSEAdapter
        cache: Optional[ISatelliteCache] = None
    ):
        self.primary = primary
        self.fallback = fallback
        self.cache = cache
        self._primary_failures = 0

    @property
    def provider_name(self) -> str:
        return f"Resilient({self.primary.provider_name}+{self.fallback.provider_name})"

    @circuit(failure_threshold=3, recovery_timeout=300)  # 5 min
    async def _try_primary(self, *args, **kwargs) -> List[SatelliteScene]:
        """Tenta provider primário com circuit breaker"""
        return await self.primary.search_scenes(*args, **kwargs)

    async def search_scenes(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        collections: Optional[List[str]] = None,
        max_cloud_cover: float = 60.0
    ) -> List[SatelliteScene]:
        """
        Busca cenas com fallback automático.

        Strategy:
        1. Tentar primary (Planetary Computer)
        2. Se falhar → tentar fallback (CDSE)
        3. Se falhar → buscar cache
        4. Se falhar → retornar lista vazia (graceful degradation)
        """

        # TENTATIVA 1: Primary provider
        try:
            logger.info("satellite_search_attempt", provider="primary")
            scenes = await self._try_primary(
                geometry, start_date, end_date, collections, max_cloud_cover
            )

            # Sucesso! Cachear resultado
            if self.cache:
                await self.cache.store(geometry, start_date, end_date, scenes)

            logger.info(
                "satellite_search_success",
                provider="primary",
                scenes_found=len(scenes)
            )
            return scenes

        except Exception as e:
            logger.warning(
                "satellite_search_failed",
                provider="primary",
                error=str(e),
                fallback="cdse"
            )
            self._primary_failures += 1

        # TENTATIVA 2: Fallback provider
        try:
            logger.info("satellite_search_attempt", provider="fallback")
            scenes = await self.fallback.search_scenes(
                geometry, start_date, end_date, collections, max_cloud_cover
            )

            # Sucesso! Cachear resultado
            if self.cache:
                await self.cache.store(geometry, start_date, end_date, scenes)

            logger.info(
                "satellite_search_success",
                provider="fallback",
                scenes_found=len(scenes)
            )
            return scenes

        except Exception as e:
            logger.warning(
                "satellite_search_failed",
                provider="fallback",
                error=str(e),
                fallback="cache"
            )

        # TENTATIVA 3: Cache (se disponível)
        if self.cache:
            try:
                logger.info("satellite_search_attempt", provider="cache")
                scenes = await self.cache.retrieve(geometry, start_date, end_date)

                if scenes:
                    logger.info(
                        "satellite_search_success",
                        provider="cache",
                        scenes_found=len(scenes),
                        warning="Using stale cached data"
                    )
                    return scenes

            except Exception as e:
                logger.error("satellite_cache_failed", error=str(e))

        # ÚLTIMO RECURSO: Degradação graciosa
        logger.error(
            "satellite_search_exhausted",
            message="All providers failed, returning empty list",
            primary_failures=self._primary_failures
        )

        # Retorna lista vazia - permite sistema continuar
        # Use case decide como lidar (pode reprocessar depois)
        return []

    async def health_check(self) -> bool:
        """Health check testa ambos providers"""
        primary_ok = await self.primary.health_check()
        fallback_ok = await self.fallback.health_check()

        # Sistema healthy se PELO MENOS UM provider funciona
        return primary_ok or fallback_ok
```

---

### Padrão 2: Object Storage com Fallback Local

**Arquivo:** `services/api/app/infrastructure/adapters/storage/resilient_storage_adapter.py`

```python
"""
Object storage com fallback para filesystem local.
"""
import structlog
from pathlib import Path
from typing import Optional

from app.domain.ports.object_storage import IObjectStorage

logger = structlog.get_logger()


class ResilientStorageAdapter(IObjectStorage):
    """
    Storage adapter com fallback:
    1. S3 (produção)
    2. Local filesystem (fallback)
    """

    def __init__(
        self,
        primary: IObjectStorage,     # S3Adapter
        fallback_path: Path = Path("/tmp/vivacampo-storage-fallback")
    ):
        self.primary = primary
        self.fallback_path = fallback_path
        self.fallback_path.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload com fallback automático.

        Strategy:
        1. Tentar S3
        2. Se falhar → salvar localmente
        3. Background job tenta sync depois
        """

        # TENTATIVA 1: S3
        try:
            uri = await self.primary.upload(key, data, content_type, metadata)
            logger.info("storage_upload_success", key=key, storage="s3")
            return uri

        except Exception as e:
            logger.warning(
                "storage_upload_failed",
                key=key,
                storage="s3",
                error=str(e),
                fallback="local"
            )

        # TENTATIVA 2: Local filesystem
        try:
            local_path = self.fallback_path / key
            local_path.parent.mkdir(parents=True, exist_ok=True)

            with open(local_path, 'wb') as f:
                f.write(data)

            # Criar marker para sync job
            await self._mark_for_sync(key, local_path)

            logger.warning(
                "storage_upload_degraded",
                key=key,
                storage="local",
                path=str(local_path),
                message="S3 unavailable, using local storage"
            )

            return f"file://{local_path}"

        except Exception as e:
            logger.error(
                "storage_upload_catastrophic_failure",
                key=key,
                error=str(e)
            )
            raise  # Não há mais fallback

    async def download(self, key: str) -> bytes:
        """
        Download com fallback.

        Strategy:
        1. Tentar S3
        2. Se falhar → tentar local
        3. Se falhar → erro (não há cache)
        """

        # TENTATIVA 1: S3
        try:
            data = await self.primary.download(key)
            return data

        except Exception as e:
            logger.warning(
                "storage_download_failed",
                key=key,
                storage="s3",
                error=str(e),
                fallback="local"
            )

        # TENTATIVA 2: Local filesystem
        local_path = self.fallback_path / key
        if local_path.exists():
            with open(local_path, 'rb') as f:
                data = f.read()

            logger.warning(
                "storage_download_degraded",
                key=key,
                storage="local",
                message="S3 unavailable, using local storage"
            )
            return data

        # Não encontrado em nenhum storage
        raise FileNotFoundError(f"Object not found: {key}")

    async def _mark_for_sync(self, key: str, local_path: Path) -> None:
        """Marca arquivo para sync futuro com S3"""
        sync_marker = Path("/tmp/vivacampo-sync-queue.txt")
        with open(sync_marker, 'a') as f:
            f.write(f"{key}|{local_path}\n")
```

---

### Padrão 3: Message Queue com Retry e DLQ

**Arquivo:** `services/api/app/infrastructure/adapters/message_queue/resilient_sqs_adapter.py`

```python
"""
Message queue com retry automático e Dead Letter Queue.
"""
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.domain.ports.message_queue import IMessageQueue

logger = structlog.get_logger()


class ResilientSQSAdapter(IMessageQueue):
    """SQS adapter com retry e DLQ"""

    def __init__(self, sqs_client, dlq_client=None):
        self.sqs = sqs_client
        self.dlq = dlq_client
        self._local_queue = []  # Fallback local

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ConnectionError)
    )
    async def publish(
        self,
        queue_name: str,
        message: dict,
        delay_seconds: int = 0
    ) -> str:
        """
        Publica com retry automático.

        Strategy:
        1. Tentar publicar 3x com backoff exponencial
        2. Se falhar → salvar em fila local
        3. Background job tenta reenviar depois
        """

        try:
            # Tentar SQS (com retry automático)
            message_id = await self.sqs.send_message(
                queue_name, message, delay_seconds
            )
            logger.info("message_published", queue=queue_name, id=message_id)
            return message_id

        except Exception as e:
            logger.error(
                "message_publish_failed_all_retries",
                queue=queue_name,
                error=str(e),
                fallback="local_queue"
            )

            # Fallback: fila local em memória
            local_id = f"local-{len(self._local_queue)}"
            self._local_queue.append({
                "id": local_id,
                "queue": queue_name,
                "message": message,
                "delay": delay_seconds
            })

            logger.warning(
                "message_queued_locally",
                queue=queue_name,
                id=local_id,
                pending_count=len(self._local_queue)
            )

            return local_id

    async def consume(
        self,
        queue_name: str,
        handler: Callable,
        max_messages: int = 10,
        wait_time_seconds: int = 20
    ) -> None:
        """
        Consome com retry e DLQ para mensagens problemáticas.
        """
        messages = await self.sqs.receive_messages(
            queue_name, max_messages, wait_time_seconds
        )

        for msg in messages:
            try:
                # Processar mensagem
                await handler(msg)

                # Sucesso → deletar da fila
                await self.sqs.delete_message(queue_name, msg.receipt_handle)

            except Exception as e:
                # Falha → verificar tentativas
                receive_count = int(msg.attributes.get('ApproximateReceiveCount', 0))

                if receive_count >= 3:
                    # Muitas tentativas → mover para DLQ
                    logger.error(
                        "message_processing_failed_max_retries",
                        queue=queue_name,
                        message_id=msg.id,
                        receive_count=receive_count,
                        error=str(e),
                        action="moving_to_dlq"
                    )

                    if self.dlq:
                        await self.dlq.send_message("dlq-" + queue_name, msg.body)

                    # Deletar da fila principal
                    await self.sqs.delete_message(queue_name, msg.receipt_handle)
                else:
                    # Retry → deixar voltar para fila
                    logger.warning(
                        "message_processing_failed_will_retry",
                        queue=queue_name,
                        message_id=msg.id,
                        receive_count=receive_count,
                        error=str(e)
                    )
```

---

### Padrão 4: Database com Read Replica Fallback

**Arquivo:** `services/api/app/infrastructure/persistence/resilient_database.py`

```python
"""
Database session com fallback para read replica.
"""
import structlog
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

logger = structlog.get_logger()


class ResilientDatabaseSession:
    """
    Database session com fallback:
    1. Primary (read/write)
    2. Read replica (somente leitura)
    """

    def __init__(self, primary: Session, replica: Session = None):
        self.primary = primary
        self.replica = replica
        self._primary_down = False

    async def execute_read(self, query):
        """
        Read query com fallback para replica.
        """

        # TENTATIVA 1: Primary
        if not self._primary_down:
            try:
                result = await self.primary.execute(query)
                return result
            except OperationalError as e:
                logger.warning(
                    "database_primary_failed",
                    error=str(e),
                    fallback="replica"
                )
                self._primary_down = True

        # TENTATIVA 2: Read replica
        if self.replica:
            try:
                result = await self.replica.execute(query)
                logger.info("database_read_from_replica")
                return result
            except OperationalError as e:
                logger.error("database_replica_failed", error=str(e))
                raise

        raise Exception("All database connections failed")

    async def execute_write(self, query):
        """
        Write query (sem fallback - deve usar primary).
        """
        try:
            result = await self.primary.execute(query)
            self._primary_down = False  # Recuperou!
            return result
        except OperationalError as e:
            logger.error("database_write_failed", error=str(e))
            raise  # Write DEVE falhar se primary down
```

---

### Configuração de Fallbacks no DI Container

**Arquivo:** `services/api/app/infrastructure/di_container.py`

```python
"""
DI Container com fallbacks configurados.
"""
from dependency_injector import containers, providers

from app.infrastructure.adapters.satellite import (
    PlanetaryComputerAdapter,
    CDSEAdapter,
    ResilientSatelliteAdapter
)


class Container(containers.DeclarativeContainer):
    """Container com fallback chain"""

    config = providers.Configuration()

    # Satellite Providers
    planetary_computer = providers.Singleton(
        PlanetaryComputerAdapter,
        catalog_url=config.planetary_computer_url
    )

    cdse = providers.Singleton(
        CDSEAdapter,
        catalog_url=config.cdse_url
    )

    # Satellite provider com fallback automático
    satellite_provider = providers.Singleton(
        ResilientSatelliteAdapter,
        primary=planetary_computer,
        fallback=cdse,
        cache=providers.Singleton(SatelliteCache)
    )

    # Storage com fallback
    s3_storage = providers.Singleton(
        S3Adapter,
        bucket=config.s3_bucket
    )

    storage = providers.Singleton(
        ResilientStorageAdapter,
        primary=s3_storage,
        fallback_path="/tmp/vivacampo-storage"
    )
```

---

## 3. Testes Locais Sem Mockup {#testes-reais}

### Problema

Testes com mocks:
- ✅ Rápidos (< 1s)
- ❌ Não garantem integração funciona
- ❌ Não pegam bugs de serialização/validação
- ❌ Falsa sensação de segurança

### Solução: Testes com Infraestrutura Real (LocalStack + Testcontainers)

```
┌──────────────────────────────────────────┐
│ Testes Unitários (Mocks)                 │
│ - Domain entities                        │
│ - Use cases (ports mockados)             │
│ - Rápidos (< 5s total)                   │
│ - CI: Sempre roda                        │
└──────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────┐
│ Testes de Integração (Infraestrutura)    │
│ - LocalStack (S3, SQS)                   │
│ - PostgreSQL (testcontainers)            │
│ - Redis (testcontainers)                 │
│ - Lentos (30s-2min)                      │
│ - CI: Sempre roda                        │
└──────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────┐
│ Testes E2E (Sistema Completo)            │
│ - Docker Compose (todos serviços)        │
│ - APIs externas mockadas (mock server)   │
│ - Muito lentos (5-10min)                 │
│ - CI: Pré-deploy apenas                  │
└──────────────────────────────────────────┘
```

---

### Setup: LocalStack + Testcontainers

**Arquivo:** `tests/conftest.py`

```python
"""
Fixtures compartilhadas para testes com infraestrutura real.
"""
import pytest
import boto3
from testcontainers.localstack import LocalStackContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.models import Base


@pytest.fixture(scope="session")
def localstack():
    """
    LocalStack container para S3, SQS, etc.
    Roda UMA VEZ por sessão de testes.
    """
    with LocalStackContainer(image="localstack/localstack:latest") as localstack:
        # Configurar services
        localstack.with_services("s3", "sqs", "secretsmanager")

        # Esperar estar pronto
        localstack.start()

        yield {
            "endpoint_url": localstack.get_url(),
            "region": "us-east-1",
            "access_key": "test",
            "secret_key": "test"
        }


@pytest.fixture(scope="session")
def postgres():
    """
    PostgreSQL container com PostGIS.
    Roda UMA VEZ por sessão de testes.
    """
    with PostgresContainer(
        image="postgis/postgis:15-3.3",
        username="test",
        password="test",
        dbname="vivacampo_test"
    ) as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="session")
def redis():
    """Redis container para cache"""
    with RedisContainer(image="redis:7-alpine") as redis:
        yield redis.get_connection_url()


@pytest.fixture(scope="function")
def db_session(postgres):
    """
    Database session para cada teste.
    Cria schema, roda teste, faz ROLLBACK.
    """
    engine = create_engine(postgres)

    # Criar schema
    Base.metadata.create_all(engine)

    # Session factory
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Rollback e cleanup
    session.rollback()
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def s3_client(localstack):
    """Cliente S3 configurado para LocalStack"""
    client = boto3.client(
        's3',
        endpoint_url=localstack["endpoint_url"],
        aws_access_key_id=localstack["access_key"],
        aws_secret_access_key=localstack["secret_key"],
        region_name=localstack["region"]
    )

    # Criar bucket de teste
    client.create_bucket(Bucket="vivacampo-test")

    yield client


@pytest.fixture(scope="function")
def sqs_client(localstack):
    """Cliente SQS configurado para LocalStack"""
    client = boto3.client(
        'sqs',
        endpoint_url=localstack["endpoint_url"],
        aws_access_key_id=localstack["access_key"],
        aws_secret_access_key=localstack["secret_key"],
        region_name=localstack["region"]
    )

    # Criar fila de teste
    queue_url = client.create_queue(QueueName="test-queue")["QueueUrl"]

    yield client
```

---

### Teste de Integração: S3 Adapter

**Arquivo:** `tests/integration/adapters/test_s3_adapter.py`

```python
"""
Testes de integração do S3Adapter com LocalStack REAL.
NÃO usa mocks - testa integração real.
"""
import pytest
from app.infrastructure.adapters.storage.s3_adapter import S3Adapter


@pytest.mark.integration
class TestS3AdapterIntegration:
    """Testes com LocalStack (infraestrutura real)"""

    @pytest.fixture
    def adapter(self, localstack):
        """Cria adapter configurado para LocalStack"""
        return S3Adapter(
            bucket="vivacampo-test",
            region=localstack["region"],
            endpoint_url=localstack["endpoint_url"],
            access_key=localstack["access_key"],
            secret_key=localstack["secret_key"]
        )

    async def test_upload_and_download(self, adapter):
        """
        Testa upload e download com S3 REAL (LocalStack).
        Garante serialização/deserialização funciona.
        """
        # Arrange
        key = "test/file.txt"
        data = b"Hello, VivaCampo!"

        # Act: Upload
        uri = await adapter.upload(key, data, content_type="text/plain")

        # Assert: URI retornado
        assert uri.startswith("s3://vivacampo-test/test/file.txt")

        # Act: Download
        downloaded = await adapter.download(key)

        # Assert: Dados idênticos
        assert downloaded == data

    async def test_upload_with_metadata(self, adapter):
        """Testa upload com metadados customizados"""
        # Arrange
        key = "test/with-metadata.txt"
        data = b"Test data"
        metadata = {"aoi_id": "123", "processed_at": "2026-02-05"}

        # Act
        await adapter.upload(key, data, metadata=metadata)

        # Assert: Recuperar metadados (via boto3 direto)
        s3 = adapter._client
        response = s3.head_object(Bucket="vivacampo-test", Key=key)

        assert response["Metadata"]["aoi_id"] == "123"
        assert response["Metadata"]["processed_at"] == "2026-02-05"

    async def test_presigned_url(self, adapter):
        """Testa geração de URL assinada"""
        # Arrange
        key = "test/presigned.txt"
        data = b"Secret data"
        await adapter.upload(key, data)

        # Act
        url = await adapter.generate_presigned_url(key, expires_in=timedelta(hours=1))

        # Assert: URL é acessível
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                downloaded = await response.read()
                assert downloaded == data

    async def test_upload_large_file(self, adapter):
        """Testa multipart upload com arquivo grande"""
        # Arrange: 10 MB
        key = "test/large-file.bin"
        data = b"x" * (10 * 1024 * 1024)

        # Act
        uri = await adapter.upload(key, data)

        # Assert: Download funciona
        downloaded = await adapter.download(key)
        assert len(downloaded) == 10 * 1024 * 1024

    async def test_download_nonexistent_raises_error(self, adapter):
        """Testa erro ao baixar arquivo inexistente"""
        with pytest.raises(FileNotFoundError):
            await adapter.download("nao-existe.txt")
```

**Executar:**
```bash
# Roda apenas testes de integração
pytest tests/integration/adapters/test_s3_adapter.py -v -m integration

# Output:
# test_upload_and_download PASSED (2.3s)
# test_upload_with_metadata PASSED (1.8s)
# test_presigned_url PASSED (3.1s)
# test_upload_large_file PASSED (4.5s)
# test_download_nonexistent_raises_error PASSED (0.8s)
```

---

### Teste de Integração: Farm Repository

**Arquivo:** `tests/integration/persistence/test_farm_repository.py`

```python
"""
Testes do FarmRepository com PostgreSQL REAL (testcontainers).
"""
import pytest
from uuid import uuid4

from app.domain.entities.farm import Farm
from app.infrastructure.persistence.sqlalchemy.farm_repository import SQLAlchemyFarmRepository


@pytest.mark.integration
class TestFarmRepositoryIntegration:
    """Testes com PostgreSQL real (testcontainers)"""

    @pytest.fixture
    def repository(self, db_session):
        """Cria repository com session real"""
        return SQLAlchemyFarmRepository(db_session)

    async def test_create_and_find_by_id(self, repository):
        """
        Testa CRUD completo com banco REAL.
        Garante serialização ORM funciona.
        """
        # Arrange
        tenant_id = uuid4()
        farm = Farm(
            tenant_id=tenant_id,
            name="Fazenda Teste",
            timezone="America/Sao_Paulo"
        )

        # Act: Create
        created = await repository.create(farm)

        # Assert: ID gerado
        assert created.id is not None
        assert created.created_at is not None

        # Act: Find by ID
        found = await repository.find_by_id(created.id)

        # Assert: Dados idênticos
        assert found.id == created.id
        assert found.name == "Fazenda Teste"
        assert found.timezone == "America/Sao_Paulo"
        assert found.tenant_id == tenant_id

    async def test_find_by_tenant_filters_correctly(self, repository):
        """Testa filtro por tenant (multi-tenancy)"""
        # Arrange: 2 tenants
        tenant1 = uuid4()
        tenant2 = uuid4()

        await repository.create(Farm(tenant_id=tenant1, name="Farm 1", timezone="UTC"))
        await repository.create(Farm(tenant_id=tenant1, name="Farm 2", timezone="UTC"))
        await repository.create(Farm(tenant_id=tenant2, name="Farm 3", timezone="UTC"))

        # Act
        tenant1_farms = await repository.find_by_tenant(tenant1)
        tenant2_farms = await repository.find_by_tenant(tenant2)

        # Assert: Isolamento por tenant
        assert len(tenant1_farms) == 2
        assert len(tenant2_farms) == 1
        assert all(f.tenant_id == tenant1 for f in tenant1_farms)
        assert all(f.tenant_id == tenant2 for f in tenant2_farms)

    async def test_update_farm(self, repository):
        """Testa atualização de farm"""
        # Arrange
        farm = await repository.create(Farm(
            tenant_id=uuid4(),
            name="Original Name",
            timezone="UTC"
        ))

        # Act: Update via domain method
        farm.update_name("New Name")
        updated = await repository.update(farm)

        # Assert: Atualização persistida
        found = await repository.find_by_id(farm.id)
        assert found.name == "New Name"
        assert found.updated_at is not None

    async def test_delete_farm(self, repository):
        """Testa deleção de farm"""
        # Arrange
        farm = await repository.create(Farm(
            tenant_id=uuid4(),
            name="To Delete",
            timezone="UTC"
        ))

        # Act
        await repository.delete(farm.id)

        # Assert: Não existe mais
        found = await repository.find_by_id(farm.id)
        assert found is None

    async def test_concurrent_updates_with_optimistic_locking(self, repository):
        """
        Testa atualizações concorrentes (se implementado).
        Garante que ORM lida com race conditions.
        """
        # Arrange
        farm = await repository.create(Farm(
            tenant_id=uuid4(),
            name="Concurrent Test",
            timezone="UTC"
        ))

        # Act: 2 sessões tentam atualizar simultaneamente
        farm1 = await repository.find_by_id(farm.id)
        farm2 = await repository.find_by_id(farm.id)

        farm1.update_name("Update 1")
        farm2.update_name("Update 2")

        await repository.update(farm1)  # Sucesso

        # Assert: Segunda atualização detecta conflito
        with pytest.raises(OptimisticLockError):
            await repository.update(farm2)
```

---

### Teste de Integração: SQS Adapter

**Arquivo:** `tests/integration/adapters/test_sqs_adapter.py`

```python
"""
Testes do SQSAdapter com LocalStack REAL.
"""
import pytest
import asyncio

from app.infrastructure.adapters.message_queue.sqs_adapter import SQSAdapter


@pytest.mark.integration
class TestSQSAdapterIntegration:
    """Testes com SQS real (LocalStack)"""

    @pytest.fixture
    def adapter(self, sqs_client, localstack):
        """Cria adapter configurado para LocalStack"""
        return SQSAdapter(
            region=localstack["region"],
            endpoint_url=localstack["endpoint_url"]
        )

    async def test_publish_and_consume(self, adapter, sqs_client):
        """
        Testa publicar e consumir mensagem com SQS REAL.
        Garante serialização JSON funciona.
        """
        # Arrange
        queue_name = "test-queue"
        message = {
            "job_type": "PROCESS_WEEK",
            "aoi_id": "123",
            "start_date": "2026-01-01"
        }

        # Act: Publish
        message_id = await adapter.publish(queue_name, message)

        # Assert: Message ID retornado
        assert message_id is not None

        # Act: Consume
        consumed_messages = []

        async def handler(msg):
            consumed_messages.append(msg)

        await adapter.consume(queue_name, handler, max_messages=1, wait_time_seconds=5)

        # Assert: Mensagem consumida
        assert len(consumed_messages) == 1
        assert consumed_messages[0].body["job_type"] == "PROCESS_WEEK"
        assert consumed_messages[0].body["aoi_id"] == "123"

    async def test_delayed_message(self, adapter):
        """Testa delay de mensagem"""
        # Arrange
        queue_name = "test-queue"
        message = {"test": "delayed"}

        # Act: Publish com delay de 5 segundos
        await adapter.publish(queue_name, message, delay_seconds=5)

        # Assert: Não disponível imediatamente
        consumed = []
        await adapter.consume(queue_name, lambda m: consumed.append(m), wait_time_seconds=2)
        assert len(consumed) == 0

        # Wait delay passar
        await asyncio.sleep(4)

        # Assert: Agora disponível
        await adapter.consume(queue_name, lambda m: consumed.append(m), wait_time_seconds=2)
        assert len(consumed) == 1

    async def test_message_attributes(self, adapter):
        """Testa attributes customizados"""
        # Arrange
        queue_name = "test-queue"
        message = {"data": "test"}

        # Act: Publish com attributes
        await adapter.publish(
            queue_name,
            message,
            attributes={"priority": "high", "source": "api"}
        )

        # Consume
        consumed = []
        await adapter.consume(queue_name, lambda m: consumed.append(m))

        # Assert: Attributes preservados
        assert consumed[0].attributes["priority"] == "high"
        assert consumed[0].attributes["source"] == "api"

    async def test_batch_publish(self, adapter):
        """Testa publicação em lote (se suportado)"""
        # Arrange
        messages = [{"id": i} for i in range(10)]

        # Act
        for msg in messages:
            await adapter.publish("test-queue", msg)

        # Consume all
        consumed = []
        await adapter.consume(
            "test-queue",
            lambda m: consumed.append(m),
            max_messages=10,
            wait_time_seconds=5
        )

        # Assert: Todos consumidos
        assert len(consumed) == 10
        assert sorted([m.body["id"] for m in consumed]) == list(range(10))
```

---

### Teste E2E: Fluxo Completo de Criação de AOI

**Arquivo:** `tests/e2e/test_aoi_creation_flow.py`

```python
"""
Teste E2E do fluxo completo de criação de AOI.
Usa TODA a stack (API + Worker + Infraestrutura).
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.e2e
class TestAOICreationFlow:
    """
    Teste end-to-end com stack completa.

    Stack (Docker Compose):
    - API (FastAPI)
    - Worker (background jobs)
    - PostgreSQL
    - LocalStack (S3, SQS)
    - Redis
    """

    @pytest.fixture
    async def api_client(self):
        """Cliente HTTP para API"""
        async with AsyncClient(base_url="http://localhost:8000") as client:
            yield client

    @pytest.fixture
    async def authenticated_user(self, api_client):
        """Cria usuário e retorna token"""
        # Register
        response = await api_client.post("/auth/register", json={
            "email": "test@vivacampo.com",
            "password": "SecurePass123!",
            "plan": "COMPANY_BASIC"
        })
        assert response.status_code == 201

        # Login
        response = await api_client.post("/auth/login", json={
            "email": "test@vivacampo.com",
            "password": "SecurePass123!"
        })
        token = response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    async def test_full_aoi_creation_flow(self, api_client, authenticated_user):
        """
        Fluxo completo:
        1. Criar tenant (via registro)
        2. Criar farm
        3. Criar AOI
        4. Verificar backfill jobs criados
        5. Aguardar processamento
        6. Verificar tiles disponíveis
        """

        # ETAPA 1: Criar farm
        response = await api_client.post(
            "/farms",
            headers=authenticated_user,
            json={
                "name": "Fazenda E2E Test",
                "timezone": "America/Sao_Paulo"
            }
        )
        assert response.status_code == 201
        farm = response.json()
        farm_id = farm["id"]

        # ETAPA 2: Criar AOI
        response = await api_client.post(
            "/aois",
            headers=authenticated_user,
            json={
                "farm_id": farm_id,
                "name": "Talhão 1",
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [[
                        [[-47.5, -15.5], [-47.5, -15.6], [-47.6, -15.6], [-47.6, -15.5], [-47.5, -15.5]]
                    ]]
                }
            }
        )
        assert response.status_code == 201
        aoi = response.json()
        aoi_id = aoi["id"]

        # ETAPA 3: Verificar jobs criados
        response = await api_client.get(
            f"/jobs?aoi_id={aoi_id}",
            headers=authenticated_user
        )
        jobs = response.json()

        # Assert: 8 semanas de backfill
        assert len(jobs) == 8
        assert all(job["status"] == "PENDING" for job in jobs)
        assert all(job["job_type"] == "BACKFILL" for job in jobs)

        # ETAPA 4: Aguardar worker processar (timeout 2 min)
        import asyncio
        for _ in range(24):  # 24 * 5s = 2 min
            await asyncio.sleep(5)

            response = await api_client.get(
                f"/jobs?aoi_id={aoi_id}",
                headers=authenticated_user
            )
            jobs = response.json()

            completed = [j for j in jobs if j["status"] == "COMPLETED"]
            if len(completed) >= 8:
                break

        # Assert: Todos jobs completados
        assert len(completed) == 8

        # ETAPA 5: Verificar tiles disponíveis
        response = await api_client.get(
            f"/tiles/ndvi/14/8431/6234?aoi_id={aoi_id}",
            headers=authenticated_user
        )

        # Assert: Tile gerado
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert len(response.content) > 0

        # ETAPA 6: Verificar observações criadas
        response = await api_client.get(
            f"/observations?aoi_id={aoi_id}",
            headers=authenticated_user
        )
        observations = response.json()

        # Assert: Pelo menos 8 observações (1 por semana)
        assert len(observations) >= 8
        assert all("ndvi_mean" in obs for obs in observations)
        assert all("ndwi_mean" in obs for obs in observations)
```

**Executar E2E:**
```bash
# Subir stack completa
docker-compose -f docker-compose.test.yml up -d

# Aguardar serviços prontos
./scripts/wait-for-services.sh

# Rodar testes E2E
pytest tests/e2e/ -v -m e2e --timeout=300

# Teardown
docker-compose -f docker-compose.test.yml down -v
```

---

### Estratégia de Testes Completa

| Tipo | Infraestrutura | Velocidade | Quando Rodar | Cobertura |
|------|----------------|------------|--------------|-----------|
| **Unitário** | Mocks | < 5s | Sempre (pre-commit, CI) | Domain + Use Cases |
| **Integração** | LocalStack + Testcontainers | 30s-2min | CI (todas branches) | Adapters + Repositories |
| **Contrato** | LocalStack + Testcontainers | 1-3min | CI (todas branches) | Ports ↔ Adapters |
| **E2E** | Docker Compose completo | 5-10min | CI (pre-deploy) + Nightly | Fluxos críticos |

---

### CI Configuration (.github/workflows/test.yml)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run integration tests (LocalStack + Testcontainers)
        run: pytest tests/integration/ -v -m integration

  e2e-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'  # Só na main
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose -f docker-compose.test.yml up -d
      - name: Wait for services
        run: ./scripts/wait-for-services.sh
      - name: Run E2E tests
        run: pytest tests/e2e/ -v -m e2e --timeout=300
      - name: Cleanup
        run: docker-compose -f docker-compose.test.yml down -v
```

---

## Resumo das Melhorias

### 1. Pydantic para Contratos

✅ **Validação em runtime** em todas as camadas
✅ **Mensagens de erro estruturadas** (JSON)
✅ **Proteção contra dados externos inválidos**
✅ **Serialização/deserialização automática**

### 2. Fallbacks em Cada Camada

✅ **Satellite Provider:** Planetary Computer → CDSE → Cache
✅ **Object Storage:** S3 → Local filesystem → Sync job
✅ **Message Queue:** SQS retry → Local queue → Background sync
✅ **Database:** Primary → Read replica (somente leitura)

### 3. Testes Sem Mockup

✅ **LocalStack** para S3, SQS (infraestrutura AWS real)
✅ **Testcontainers** para PostgreSQL, Redis
✅ **Docker Compose** para testes E2E completos
✅ **CI rodando testes de integração** sempre

---

## Próximos Passos

1. **Aprovar este plano complementar**
2. **Adicionar Pydantic ao HEXAGONAL_ARCHITECTURE_PLAN.md** (Fase 1)
3. **Implementar fallbacks** (Fase 2 do plano original)
4. **Configurar testcontainers** (durante Fase 2-3)
5. **Adicionar testes de integração** conforme adapters são criados

Quer que eu elabore alguma seção específica ou comece a implementação?
