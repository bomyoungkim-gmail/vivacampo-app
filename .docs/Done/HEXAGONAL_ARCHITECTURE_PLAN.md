# Plano de Implementação: Arquitetura Hexagonal Completa - VivaCampo

**Objetivo:** Migrar VivaCampo para arquitetura hexagonal (Ports & Adapters) com separação completa de camadas, dependency injection, abstrações para todos os serviços externos, **validação Pydantic em todas as camadas**, **fallbacks automáticos para resiliência**, e **testes com infraestrutura real**.

**Prioridade:** P0 (Fundação para escalabilidade e resiliência)
**Estimativa:** 8-10 semanas
**Data:** 2026-02-05

**Melhorias Integradas:**
- ✅ **Pydantic para Contratos:** Validação automática em runtime em 5 camadas (HTTP → Presentation → Application → Domain → Infrastructure)
- ✅ **Fallbacks Automáticos:** Resiliência em cada camada (ex: Planetary Computer → CDSE → Cache)
- ✅ **Testes Reais:** LocalStack + Testcontainers em vez de mocks (garante integração funciona)

---

## Índice

1. [Visão Geral da Arquitetura](#visao-geral)
2. [Fase 1: Domain Layer - Ports & Entities](#fase-1)
3. [Fase 2: Infrastructure Layer - Adapters](#fase-2)
4. [Fase 3: Application Layer - Use Cases](#fase-3)
5. [Fase 4: Dependency Injection Container](#fase-4)
6. [Fase 5: Presentation Layer - Refatoração](#fase-5)
7. [Fase 6: Worker Jobs - Refatoração](#fase-6)
8. [Fase 7: Testes e Validação](#fase-7)
9. [Fase 8: Limpeza de Código Legado](#fase-8)
10. [Segurança Multi-Tenant](#seguranca-multi-tenant)
11. [Plano de Verificação](#plano-verificacao)

---

## Visão Geral da Arquitetura {#visao-geral}

### Estrutura Final de Diretórios

```
services/
├── api/
│   └── app/
│       ├── domain/                    # ⭐ NOVA - Camada de Domínio
│       │   ├── entities/              # Entidades de negócio
│       │   ├── value_objects/         # Value Objects
│       │   ├── ports/                 # Interfaces (Ports)
│       │   └── services/              # Domain Services
│       ├── application/               # ⭐ REFATORADA - Use Cases
│       │   ├── use_cases/
│       │   ├── dtos/                  # Data Transfer Objects
│       │   └── services/
│       ├── infrastructure/            # ⭐ REFATORADA - Adapters
│       │   ├── adapters/
│       │   │   ├── message_queue/
│       │   │   ├── storage/
│       │   │   └── cache/
│       │   ├── persistence/
│       │   │   └── sqlalchemy/
│       │   └── di_container.py        # ⭐ NOVO - DI Container
│       └── presentation/              # Controllers (thin)
│
└── worker/
    └── worker/
        ├── domain/                    # ⭐ NOVA - Camada de Domínio
        │   ├── entities/
        │   ├── ports/
        │   └── services/
        ├── application/               # ⭐ NOVA - Use Cases
        │   └── use_cases/
        ├── infrastructure/            # ⭐ REFATORADA
        │   ├── adapters/
        │   │   ├── satellite/
        │   │   ├── weather/
        │   │   └── storage/
        │   └── di_container.py
        └── jobs/                      # ⭐ REFATORADA - Thin handlers
```

### Princípios Fundamentais

1. **Dependency Rule:** Dependências apontam SEMPRE para dentro (Infrastructure → Application → Domain)
2. **Domain Purity:** Domain layer NÃO tem dependências externas (zero imports de frameworks)
3. **Interface Segregation:** Ports pequenos e específicos
4. **Dependency Injection:** Todas as dependências injetadas via constructor
5. **Validation Everywhere (Pydantic):** Validação automática em runtime em todas as camadas
6. **Fail Gracefully:** Fallbacks automáticos - sistema nunca para completamente
7. **Test with Real Infrastructure:** Testes de integração com LocalStack/Testcontainers (não só mocks)
8. **Multi-Tenant Security First:** Isolamento garantido de dados entre tenants em TODAS as camadas

---

## FASE 1: Domain Layer - Ports & Entities {#fase-1}

**Duração:** 2 semanas
**Objetivo:** Criar camada de domínio pura com entidades (Pydantic), value objects e ports (interfaces)

**Melhorias desta fase:**
- ✅ Usar **Pydantic BaseModel** em vez de dataclass (validação automática em runtime)
- ✅ Field validators para regras de negócio complexas
- ✅ Configuração global de validação (strict mode)

### Etapa 1.0: Instalar Pydantic

**Executar:**
```bash
pip install pydantic==2.5.0
pip install pydantic-settings==2.1.0
```

**Criar configuração global:**

**Arquivo:** `services/api/app/domain/base.py`

```python
"""
Base classes para domain entities com Pydantic.
"""
from pydantic import BaseModel, ConfigDict


class DomainEntity(BaseModel):
    """
    Base class para todas as domain entities.
    Configuração rigorosa com validação automática.
    """

    model_config = ConfigDict(
        # Validação
        validate_assignment=True,      # Valida em TODA atribuição
        validate_default=True,         # Valida valores default
        str_strip_whitespace=True,     # Remove espaços

        # Segurança
        extra="forbid",                # Rejeita campos extras
        frozen=False,                  # Permite mutação

        # Performance
        arbitrary_types_allowed=False, # Só tipos nativos Python
    )


class ImmutableDTO(BaseModel):
    """Base class para DTOs imutáveis (Commands, Responses)"""

    model_config = ConfigDict(
        frozen=True,                   # Imutável
        validate_assignment=True,
        extra="forbid"
    )
```

---

### Etapa 1.1: Criar Estrutura de Diretórios

**Executar comandos:**

```bash
# API Domain Layer
mkdir -p services/api/app/domain/entities
mkdir -p services/api/app/domain/value_objects
mkdir -p services/api/app/domain/ports
mkdir -p services/api/app/domain/services

# Worker Domain Layer
mkdir -p services/worker/worker/domain/entities
mkdir -p services/worker/worker/domain/value_objects
mkdir -p services/worker/worker/domain/ports
mkdir -p services/worker/worker/domain/services

# Criar __init__.py em todos os diretórios
find services/api/app/domain -type d -exec touch {}/__init__.py \;
find services/worker/worker/domain -type d -exec touch {}/__init__.py \;
```

**Critérios de Aceite:**
- [ ] Estrutura de diretórios criada
- [ ] Todos os `__init__.py` criados
- [ ] Imports funcionando: `from app.domain.entities import Farm`
- [ ] Pydantic instalado e configuração global criada

---

### Etapa 1.2: Domain Entities (API)

**Arquivo:** `services/api/app/domain/entities/farm.py`

```python
"""
Farm domain entity com Pydantic.
Pure Python - NO framework dependencies (exceto Pydantic).
"""
from pydantic import Field, field_validator
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from app.domain.base import DomainEntity


class Farm(DomainEntity):
    """
    Fazenda - Agregado raiz para gestão de propriedades rurais.

    Regras de Negócio (validadas automaticamente por Pydantic):
    - Nome: 3-100 caracteres
    - Timezone: deve estar em pytz.all_timezones
    - Tenant ID: obrigatório (multi-tenancy)
    """

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
            raise ValueError(f"Invalid timezone: {v}")
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
        Atualiza nome da fazenda.
        Validação automática via validate_assignment=True.
        """
        self.name = new_name  # Pydantic valida automaticamente!
        self.updated_at = datetime.utcnow()
```

**Benefícios do Pydantic:**
- ✅ Validação automática em criação: `Farm(name="AB")` → ValidationError
- ✅ Validação em atualização: `farm.name = "X"` → ValidationError
- ✅ Mensagens de erro estruturadas em JSON
- ✅ Type safety em runtime (não só mypy)

**Arquivo:** `services/api/app/domain/entities/aoi.py`

```python
"""
Area of Interest (AOI) domain entity com Pydantic.
"""
from pydantic import Field, field_validator
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from app.domain.base import DomainEntity


class AOI(DomainEntity):
    """
    Área de Interesse - Polígono geográfico para monitoramento.

    Regras de Negócio (validadas automaticamente):
    - Geometria: MultiPolygon válido (WKT)
    - Área: 1-10,000 hectares
    - Deve pertencer a Farm e Tenant
    """

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    farm_id: UUID
    name: str = Field(min_length=3, max_length=200)
    geometry_wkt: str = Field(min_length=10)
    area_hectares: float = Field(ge=1.0, le=10000.0)  # >= 1, <= 10000
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    crop_type: Optional[str] = Field(None, max_length=50)
    planting_date: Optional[datetime] = None

    @field_validator('geometry_wkt')
    @classmethod
    def validate_geometry(cls, v: str) -> str:
        """Valida formato WKT básico"""
        if not v.startswith(('POLYGON', 'MULTIPOLYGON')):
            raise ValueError("Geometry must be POLYGON or MULTIPOLYGON")
        return v

    def update_geometry(self, new_geometry_wkt: str, new_area_hectares: float) -> None:
        """
        Atualiza geometria da AOI.
        Pydantic valida automaticamente os constraints (1-10000 ha).
        """
        self.geometry_wkt = new_geometry_wkt
        self.area_hectares = new_area_hectares
        self.updated_at = datetime.utcnow()
```

**Critérios de Aceite:**
- [ ] Entidades criadas com validação Pydantic
- [ ] Zero imports de frameworks ORM/Web (apenas Pydantic permitido)
- [ ] Testes unitários passando (testam validação automática)
- [ ] Validação funciona em criação E atualização

**Teste de validação:**
```python
# tests/unit/domain/test_farm_entity.py
import pytest
from pydantic import ValidationError
from app.domain.entities.farm import Farm

def test_farm_validates_name_length():
    with pytest.raises(ValidationError) as exc:
        Farm(tenant_id=uuid4(), name="AB")  # < 3 chars

    errors = exc.value.errors()
    assert errors[0]['loc'] == ('name',)
    assert 'at least 3 characters' in errors[0]['msg']

def test_farm_validates_on_update():
    farm = Farm(tenant_id=uuid4(), name="Valid Name")

    with pytest.raises(ValidationError):
        farm.name = "X"  # Validação automática!
```

---

### Etapa 1.3: Domain Ports (Interfaces)

**Arquivo:** `services/api/app/domain/ports/message_queue.py`

```python
"""
Message Queue port (interface).
Define contrato para filas de mensagens.
"""
from abc import ABC, abstractmethod
from typing import Callable, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """Mensagem genérica para fila"""
    id: str
    body: dict
    attributes: Optional[dict] = None


class IMessageQueue(ABC):
    """
    Port para operações de fila de mensagens.
    
    Implementações:
    - SQSAdapter (AWS)
    - RabbitMQAdapter
    - RedisAdapter
    """
    
    @abstractmethod
    async def publish(
        self,
        queue_name: str,
        message: dict,
        delay_seconds: int = 0
    ) -> str:
        """
        Publica mensagem na fila.
        
        Args:
            queue_name: Nome da fila
            message: Payload da mensagem (será serializado para JSON)
            delay_seconds: Delay antes de processar (0 = imediato)
        
        Returns:
            message_id: ID da mensagem publicada
        """
        pass
    
    @abstractmethod
    async def consume(
        self,
        queue_name: str,
        handler: Callable[[Message], None],
        max_messages: int = 10,
        wait_time_seconds: int = 20
    ) -> None:
        """Consome mensagens da fila"""
        pass
```

**Arquivo:** `services/api/app/domain/ports/object_storage.py`

```python
"""
Object Storage port (interface).
Abstração para S3, GCS, Azure Blob, etc.
"""
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from datetime import timedelta


class IObjectStorage(ABC):
    """
    Port para operações de object storage.
    
    Implementações:
    - S3Adapter (AWS)
    - GCSAdapter (Google Cloud)
    - LocalFileSystemAdapter (dev/testing)
    """
    
    @abstractmethod
    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload de objeto.
        
        Returns:
            uri: URI do objeto (ex: s3://bucket/key)
        """
        pass
    
    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download de objeto"""
        pass
    
    @abstractmethod
    async def generate_presigned_url(
        self,
        key: str,
        expires_in: timedelta = timedelta(hours=1)
    ) -> str:
        """Gera URL assinada para acesso temporário"""
        pass
```

**Arquivo:** `services/worker/worker/domain/ports/satellite_provider.py`

```python
"""
Satellite Data Provider port.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class SatelliteScene:
    """Cena de satélite - Domain entity"""
    id: str
    datetime: datetime
    cloud_cover: float
    platform: str
    collection: str
    bbox: List[float]
    geometry: Dict[str, Any]
    assets: Dict[str, Optional[str]]


class ISatelliteProvider(ABC):
    """
    Port para provedores de dados de satélite.
    
    Implementações:
    - PlanetaryComputerAdapter
    - CDSEAdapter
    - EarthEngineAdapter
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
    
    @abstractmethod
    async def search_scenes(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        collections: Optional[List[str]] = None,
        max_cloud_cover: float = 60.0
    ) -> List[SatelliteScene]:
        """Busca cenas de satélite"""
        pass
    
    @abstractmethod
    async def download_band(
        self,
        asset_href: str,
        geometry: Dict[str, Any],
        output_path: str
    ) -> str:
        """Baixa banda e recorta pela geometria"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Verifica se provider está acessível"""
        pass
```

---

## FASE 2: Infrastructure Layer - Adapters {#fase-2}

**Duração:** 3 semanas
**Objetivo:** Implementar adapters concretos com **fallbacks automáticos** e **validação Pydantic de dados externos**

**Melhorias desta fase:**
- ✅ **Resilient Adapters:** Cada adapter tem fallback chain (Primary → Fallback → Cache → Degraded)
- ✅ **Validação de Dados Externos:** Pydantic valida respostas de APIs externas antes de usar
- ✅ **Circuit Breaker:** Detecta falhas repetidas e desvia para fallback
- ✅ **Testes com LocalStack:** Testar com S3/SQS REAL (não mocks)

### Etapa 2.1: Instalar Dependências para Resiliência

```bash
pip install tenacity==8.2.3        # Retry com backoff exponencial
pip install circuitbreaker==1.4.0  # Circuit breaker pattern
```

---

### Etapa 2.2: SQS Adapter com Retry e Fallback

**Arquivo:** `services/api/app/infrastructure/adapters/message_queue/sqs_adapter.py`

```python
"""AWS SQS adapter com retry automático"""
import json
import structlog
import boto3
from typing import Callable, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from app.domain.ports.message_queue import IMessageQueue, Message

logger = structlog.get_logger()


class SQSAdapter(IMessageQueue):
    """AWS SQS implementation com retry automático"""

    def __init__(
        self,
        region: str,
        endpoint_url: Optional[str] = None
    ):
        self.client = boto3.client(
            'sqs',
            region_name=region,
            endpoint_url=endpoint_url
        )
        self._queue_urls = {}
        logger.info("sqs_adapter_initialized", region=region)

    def _get_queue_url(self, queue_name: str) -> str:
        if queue_name not in self._queue_urls:
            response = self.client.get_queue_url(QueueName=queue_name)
            self._queue_urls[queue_name] = response['QueueUrl']
        return self._queue_urls[queue_name]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def publish(
        self,
        queue_name: str,
        message: dict,
        delay_seconds: int = 0
    ) -> str:
        """
        Publica com retry automático (3 tentativas, backoff exponencial).
        """
        queue_url = self._get_queue_url(queue_name)

        response = self.client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, default=str),
            DelaySeconds=delay_seconds
        )

        message_id = response['MessageId']
        logger.info("message_published", queue=queue_name, message_id=message_id)
        return message_id

    async def consume(
        self,
        queue_name: str,
        handler: Callable[[Message], None],
        max_messages: int = 10,
        wait_time_seconds: int = 20
    ) -> None:
        queue_url = self._get_queue_url(queue_name)

        response = self.client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_time_seconds
        )

        for msg in response.get('Messages', []):
            try:
                body = json.loads(msg['Body'])
                message = Message(
                    id=msg['MessageId'],
                    body=body,
                    attributes=msg.get('Attributes', {})
                )
                await handler(message)

                # Sucesso → deletar mensagem
                self.client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg['ReceiptHandle']
                )

            except Exception as e:
                logger.error("message_processing_failed", error=str(e))
                # Mensagem volta para fila (visibility timeout)
```

---

### Etapa 2.3: Satellite Provider com Fallback Chain

**Arquivo:** `services/worker/worker/infrastructure/adapters/satellite/resilient_satellite_adapter.py`

```python
"""
Satellite adapter com fallback automático:
1. Planetary Computer (preferido)
2. CDSE (fallback)
3. Cache (última opção)
"""
import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime
from circuitbreaker import circuit

from app.domain.ports.satellite_provider import ISatelliteProvider, SatelliteScene

logger = structlog.get_logger()


class ResilientSatelliteAdapter(ISatelliteProvider):
    """Provider com fallback chain"""

    def __init__(
        self,
        primary: ISatelliteProvider,    # PlanetaryComputerAdapter
        fallback: ISatelliteProvider,   # CDSEAdapter
        cache: Optional['SatelliteCache'] = None
    ):
        self.primary = primary
        self.fallback = fallback
        self.cache = cache
        self._primary_failures = 0

    @property
    def provider_name(self) -> str:
        return f"Resilient({self.primary.provider_name})"

    @circuit(failure_threshold=3, recovery_timeout=300)  # 3 falhas → abrir por 5min
    async def _try_primary(self, *args, **kwargs) -> List[SatelliteScene]:
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
        Busca com fallback automático:
        1. Primary (Planetary Computer)
        2. Fallback (CDSE)
        3. Cache (dados históricos)
        4. Empty list (degradação graciosa)
        """

        # TENTATIVA 1: Primary
        try:
            scenes = await self._try_primary(
                geometry, start_date, end_date, collections, max_cloud_cover
            )

            # Cachear sucesso
            if self.cache:
                await self.cache.store(geometry, start_date, end_date, scenes)

            logger.info("satellite_search_success", provider="primary", count=len(scenes))
            return scenes

        except Exception as e:
            logger.warning("primary_failed", error=str(e), fallback="cdse")
            self._primary_failures += 1

        # TENTATIVA 2: Fallback
        try:
            scenes = await self.fallback.search_scenes(
                geometry, start_date, end_date, collections, max_cloud_cover
            )

            if self.cache:
                await self.cache.store(geometry, start_date, end_date, scenes)

            logger.info("satellite_search_success", provider="fallback", count=len(scenes))
            return scenes

        except Exception as e:
            logger.warning("fallback_failed", error=str(e), fallback="cache")

        # TENTATIVA 3: Cache
        if self.cache:
            try:
                scenes = await self.cache.retrieve(geometry, start_date, end_date)
                if scenes:
                    logger.warning("using_cached_data", count=len(scenes))
                    return scenes
            except Exception as e:
                logger.error("cache_failed", error=str(e))

        # DEGRADAÇÃO GRACIOSA: Lista vazia
        logger.error("all_providers_failed", primary_failures=self._primary_failures)
        return []  # Sistema continua funcionando!

    async def health_check(self) -> bool:
        """Healthy se PELO MENOS UM provider funciona"""
        primary_ok = await self.primary.health_check()
        fallback_ok = await self.fallback.health_check()
        return primary_ok or fallback_ok
```

**Configurar no DI Container:**
```python
# di_container.py
satellite_provider = providers.Singleton(
    ResilientSatelliteAdapter,
    primary=providers.Singleton(PlanetaryComputerAdapter),
    fallback=providers.Singleton(CDSEAdapter),
    cache=providers.Singleton(SatelliteCache)
)
```

---

### Etapa 2.4: Testes de Integração com LocalStack

**Instalar testcontainers:**
```bash
pip install testcontainers==3.7.1
```

**Arquivo:** `tests/integration/adapters/test_sqs_adapter.py`

```python
"""
Testes do SQSAdapter com LocalStack REAL (não mocks!).
"""
import pytest
from testcontainers.localstack import LocalStackContainer

from app.infrastructure.adapters.message_queue.sqs_adapter import SQSAdapter


@pytest.fixture(scope="module")
def localstack():
    """LocalStack container - S3, SQS, etc."""
    with LocalStackContainer(image="localstack/localstack:latest") as container:
        container.with_services("sqs")
        yield container.get_url()


@pytest.mark.integration
async def test_sqs_publish_and_consume_with_real_localstack(localstack):
    """
    Testa com SQS REAL - garante integração funciona!
    """
    # Arrange
    adapter = SQSAdapter(region="us-east-1", endpoint_url=localstack)

    # Act: Publish
    message_id = await adapter.publish("test-queue", {"job": "PROCESS_WEEK"})

    # Consume
    messages = []
    await adapter.consume("test-queue", lambda m: messages.append(m), max_messages=1)

    # Assert: Integração funcionou
    assert len(messages) == 1
    assert messages[0].body["job"] == "PROCESS_WEEK"
```

**Rodar testes de integração:**
```bash
pytest tests/integration/ -v -m integration
```

---

## FASE 3: Application Layer - Use Cases {#fase-3}

**Duração:** 2 semanas
**Objetivo:** Criar use cases com **Commands/DTOs Pydantic** e dependency injection

**Melhorias desta fase:**
- ✅ **Commands como Pydantic models** (imutáveis, validados)
- ✅ **Response DTOs validados** (contratos fortes)
- ✅ **Testes unitários SEM infraestrutura** (mocks dos ports)

### Etapa 3.1: Use Case Example

**Arquivo:** `services/api/app/application/use_cases/farms/create_farm.py`

```python
"""
Create Farm use case com Pydantic Commands e DTOs.
"""
from pydantic import Field
from uuid import UUID
from datetime import datetime

from app.domain.base import ImmutableDTO
from app.domain.entities.farm import Farm
from app.domain.ports.farm_repository import IFarmRepository


class CreateFarmCommand(ImmutableDTO):
    """
    Input DTO - validado por Pydantic.
    Imutável (frozen=True).
    """
    tenant_id: UUID
    name: str = Field(min_length=3, max_length=100)
    timezone: str = Field(default="America/Sao_Paulo")


class CreateFarmResponse(ImmutableDTO):
    """
    Output DTO - contrato de resposta garantido.
    """
    farm_id: UUID
    name: str
    timezone: str
    created_at: datetime

    @classmethod
    def from_entity(cls, farm: Farm) -> "CreateFarmResponse":
        """Converte entity → DTO"""
        return cls(
            farm_id=farm.id,
            name=farm.name,
            timezone=farm.timezone,
            created_at=farm.created_at
        )


class CreateFarmUseCase:
    """
    Use case com contratos Pydantic fortes.

    Dependency Injection:
    - farm_repository: IFarmRepository (porta, não adapter)
    """

    def __init__(self, farm_repository: IFarmRepository):
        self.farm_repository = farm_repository

    async def execute(self, command: CreateFarmCommand) -> CreateFarmResponse:
        """
        Executa criação de farm.

        Args:
            command: CreateFarmCommand (já validado por Pydantic)

        Returns:
            CreateFarmResponse (contrato garantido)

        Raises:
            ValidationError: Se entity inválida (capturado por Pydantic)
            RepositoryError: Se falha ao persistir
        """
        # 1. Criar entity (validação automática de negócio)
        farm = Farm(
            tenant_id=command.tenant_id,
            name=command.name,
            timezone=command.timezone
        )

        # 2. Persistir via repository (porta)
        farm = await self.farm_repository.create(farm)

        # 3. Retornar DTO validado
        return CreateFarmResponse.from_entity(farm)
```

**Teste unitário (SEM infraestrutura):**

```python
# tests/unit/application/test_create_farm_use_case.py
import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from app.application.use_cases.farms.create_farm import (
    CreateFarmUseCase,
    CreateFarmCommand
)


@pytest.mark.asyncio
async def test_create_farm_use_case_success():
    """Testa use case SEM banco - usa mock do repository"""
    # Arrange: Mock repository
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value=Farm(
        id=uuid4(),
        tenant_id=uuid4(),
        name="Test Farm",
        timezone="UTC"
    ))

    use_case = CreateFarmUseCase(farm_repository=mock_repo)

    # Act
    command = CreateFarmCommand(
        tenant_id=uuid4(),
        name="Test Farm",
        timezone="UTC"
    )
    response = await use_case.execute(command)

    # Assert
    assert response.name == "Test Farm"
    assert response.timezone == "UTC"
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_farm_validates_command():
    """Pydantic valida command automaticamente"""
    with pytest.raises(ValidationError):
        CreateFarmCommand(tenant_id=uuid4(), name="AB")  # < 3 chars
```

---

## FASE 4: Dependency Injection Container {#fase-4}

**Duração:** 1 semana  
**Objetivo:** Configurar DI container com dependency-injector

### Etapa 4.1: Instalar Biblioteca

```bash
pip install dependency-injector==4.41.0
```

### Etapa 4.2: Criar Container

**Arquivo:** `services/api/app/infrastructure/di_container.py`

```python
"""
Dependency Injection Container.
Centraliza configuração de todas as dependências.
"""
from dependency_injector import containers, providers
from app.config import settings

# Adapters
from app.infrastructure.adapters.message_queue.sqs_adapter import SQSAdapter
from app.infrastructure.adapters.storage.s3_adapter import S3Adapter
from app.infrastructure.persistence.sqlalchemy.farm_repository import SQLAlchemyFarmRepository

# Use Cases
from app.application.use_cases.farms.create_farm import CreateFarmUseCase


class Container(containers.DeclarativeContainer):
    """Application DI Container"""
    
    config = providers.Configuration()
    
    # Database
    db_session = providers.Singleton(
        # Database session factory
    )
    
    # Message Queue Adapter (configurável via env)
    message_queue = providers.Selector(
        config.message_queue_type,
        sqs=providers.Singleton(
            SQSAdapter,
            region=config.aws_region,
            endpoint_url=config.aws_endpoint_url
        ),
        # rabbitmq=providers.Singleton(RabbitMQAdapter, ...),
    )
    
    # Object Storage Adapter
    object_storage = providers.Singleton(
        S3Adapter,
        bucket=config.s3_bucket,
        region=config.aws_region,
        endpoint_url=config.aws_endpoint_url
    )
    
    # Repositories
    farm_repository = providers.Factory(
        SQLAlchemyFarmRepository,
        session=db_session
    )
    
    # Use Cases
    create_farm_use_case = providers.Factory(
        CreateFarmUseCase,
        farm_repository=farm_repository
    )
```

### Etapa 4.3: Configurar FastAPI

**Arquivo:** `services/api/app/main.py`

```python
from fastapi import FastAPI
from app.infrastructure.di_container import Container

# Criar container
container = Container()
container.config.from_pydantic(settings)

# Criar app
app = FastAPI()
app.container = container

# Registrar routers
from app.presentation import farms_router
app.include_router(farms_router.router)
```

### Etapa 4.4: Injetar em Router

**Arquivo:** `services/api/app/presentation/farms_router.py`

```python
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from app.infrastructure.di_container import Container
from app.application.use_cases.farms.create_farm import (
    CreateFarmUseCase,
    CreateFarmCommand
)

router = APIRouter()


@router.post("/farms")
@inject
async def create_farm(
    name: str,
    timezone: str,
    use_case: CreateFarmUseCase = Depends(Provide[Container.create_farm_use_case])
):
    """
    Thin controller - delega para use case.
    Use case é injetado automaticamente pelo DI container.
    """
    command = CreateFarmCommand(
        tenant_id=get_current_tenant_id(),  # From auth
        name=name,
        timezone=timezone
    )
    
    farm = await use_case.execute(command)
    
    return {"id": str(farm.id), "name": farm.name}
```

---

## FASE 7: Plano de Verificação e Testes {#plano-verificacao}

**Estratégia:** Pirâmide de testes com infraestrutura REAL (não só mocks)

```
        E2E (Stack Completa)          ← 5-10 min
       /                      \
    Integração (LocalStack)    ← 30s-2min
   /                          \
Unitários (Mocks)              ← < 5s
```

---

### Etapa 7.1: Setup de Testes

**Instalar dependências:**
```bash
pip install pytest==7.4.3
pip install pytest-asyncio==0.21.1
pip install pytest-cov==4.1.0
pip install testcontainers==3.7.1
pip install httpx==0.25.2  # Para testes E2E
```

**Arquivo:** `tests/conftest.py`

```python
"""
Fixtures compartilhadas - LocalStack + Testcontainers.
"""
import pytest
from testcontainers.localstack import LocalStackContainer
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.models import Base


@pytest.fixture(scope="session")
def localstack():
    """LocalStack para S3, SQS (roda UMA VEZ por sessão)"""
    with LocalStackContainer(image="localstack/localstack:latest") as container:
        container.with_services("s3", "sqs")
        yield {
            "endpoint_url": container.get_url(),
            "region": "us-east-1"
        }


@pytest.fixture(scope="session")
def postgres():
    """PostgreSQL com PostGIS (roda UMA VEZ por sessão)"""
    with PostgresContainer(
        image="postgis/postgis:15-3.3",
        username="test",
        password="test",
        dbname="vivacampo_test"
    ) as container:
        yield container.get_connection_url()


@pytest.fixture(scope="function")
def db_session(postgres):
    """
    Database session para cada teste.
    Cria schema → Roda teste → ROLLBACK.
    """
    engine = create_engine(postgres)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.rollback()
    session.close()
    Base.metadata.drop_all(engine)
```

---

### Etapa 7.2: Testes Unitários (Domain + Application)

**Objetivo:** Testar lógica de negócio SEM infraestrutura

```bash
# Executar testes unitários
pytest tests/unit/ -v --cov=app.domain --cov=app.application

# Expectativa:
# - Execução: < 5 segundos
# - Cobertura: > 85%
# - Zero dependências externas
```

**Exemplo:**

```python
# tests/unit/domain/test_farm_entity.py
import pytest
from pydantic import ValidationError
from app.domain.entities.farm import Farm


def test_farm_validates_name_on_creation():
    """Pydantic valida automaticamente na criação"""
    with pytest.raises(ValidationError) as exc:
        Farm(tenant_id=uuid4(), name="AB")  # < 3 chars

    assert 'at least 3 characters' in str(exc.value)


def test_farm_validates_name_on_update():
    """Pydantic valida em atribuição (validate_assignment=True)"""
    farm = Farm(tenant_id=uuid4(), name="Valid Name")

    with pytest.raises(ValidationError):
        farm.name = "X"  # Validação automática!


def test_farm_validates_timezone():
    """Field validator customizado funciona"""
    with pytest.raises(ValidationError) as exc:
        Farm(tenant_id=uuid4(), name="Farm", timezone="Invalid/Timezone")

    assert 'Invalid timezone' in str(exc.value)
```

---

### Etapa 7.3: Testes de Integração (Adapters + LocalStack)

**Objetivo:** Testar integração com infraestrutura REAL (LocalStack, PostgreSQL)

```bash
# Executar testes de integração
pytest tests/integration/ -v -m integration

# Expectativa:
# - Execução: 30s - 2min
# - LocalStack S3/SQS REAL
# - PostgreSQL com testcontainers
```

**Exemplo: S3Adapter com LocalStack REAL**

```python
# tests/integration/adapters/test_s3_adapter.py
import pytest
from app.infrastructure.adapters.storage.s3_adapter import S3Adapter


@pytest.mark.integration
async def test_s3_upload_and_download_with_real_localstack(localstack):
    """
    Testa com S3 REAL - não mock!
    Garante: boto3, serialização, network, tudo funciona.
    """
    # Arrange
    adapter = S3Adapter(
        bucket="vivacampo-test",
        region=localstack["region"],
        endpoint_url=localstack["endpoint_url"]
    )

    # Act: Upload
    data = b"Test satellite data"
    uri = await adapter.upload("test/scene.tif", data)

    # Assert: URI correto
    assert uri.startswith("s3://vivacampo-test/test/scene.tif")

    # Act: Download
    downloaded = await adapter.download("test/scene.tif")

    # Assert: Dados idênticos
    assert downloaded == data
```

**Exemplo: FarmRepository com PostgreSQL REAL**

```python
# tests/integration/persistence/test_farm_repository.py
import pytest
from app.infrastructure.persistence.sqlalchemy.farm_repository import SQLAlchemyFarmRepository


@pytest.mark.integration
async def test_farm_repository_crud_with_real_postgres(db_session):
    """
    Testa com PostgreSQL REAL (testcontainer).
    Garante: SQLAlchemy, tipos PostGIS, constraints funcionam.
    """
    # Arrange
    repo = SQLAlchemyFarmRepository(db_session)

    farm = Farm(tenant_id=uuid4(), name="Test Farm", timezone="UTC")

    # Act: Create
    created = await repo.create(farm)

    # Assert: ID gerado pelo banco
    assert created.id is not None

    # Act: Find by ID
    found = await repo.find_by_id(created.id)

    # Assert: Dados persistidos corretamente
    assert found.name == "Test Farm"
    assert found.timezone == "UTC"
```

---

### Etapa 7.4: Testes de Contrato (Ports ↔ Adapters)

**Objetivo:** Garantir que TODOS os adapters implementam os ports corretamente

```python
# tests/integration/contracts/test_object_storage_contract.py
import pytest


@pytest.mark.parametrize("adapter_factory", [
    lambda: S3Adapter(bucket="test", endpoint_url=localstack),
    lambda: LocalFileSystemAdapter(base_path="/tmp/test"),
])
async def test_object_storage_contract(adapter_factory):
    """
    Testa contrato IObjectStorage.
    Todos os adapters devem passar.
    """
    adapter = adapter_factory()

    # Upload
    uri = await adapter.upload("test.txt", b"data")
    assert uri is not None

    # Download
    data = await adapter.download("test.txt")
    assert data == b"data"

    # Presigned URL
    url = await adapter.generate_presigned_url("test.txt")
    assert url.startswith("http")
```

---

### Etapa 7.5: Testes End-to-End (Stack Completa)

**Objetivo:** Testar fluxos críticos do usuário com TODA a stack rodando

**Setup:**
```bash
# Subir stack completa
docker-compose -f docker-compose.test.yml up -d

# Aguardar serviços prontos
./scripts/wait-for-services.sh

# Rodar E2E
pytest tests/e2e/ -v -m e2e --timeout=300
```

**Exemplo: Fluxo completo de criação de AOI**

```python
# tests/e2e/test_aoi_creation_flow.py
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
async def test_full_aoi_creation_and_processing_flow():
    """
    Fluxo E2E completo:
    1. Register → Login → Create Farm → Create AOI
    2. Verificar backfill jobs criados
    3. Aguardar worker processar
    4. Verificar tiles disponíveis
    """
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Register
        response = await client.post("/auth/register", json={
            "email": "e2e@vivacampo.com",
            "password": "Test123!",
            "plan": "COMPANY_BASIC"
        })
        assert response.status_code == 201

        # 2. Login
        response = await client.post("/auth/login", json={
            "email": "e2e@vivacampo.com",
            "password": "Test123!"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create Farm
        response = await client.post("/farms", headers=headers, json={
            "name": "E2E Test Farm",
            "timezone": "America/Sao_Paulo"
        })
        farm_id = response.json()["id"]

        # 4. Create AOI
        response = await client.post("/aois", headers=headers, json={
            "farm_id": farm_id,
            "name": "E2E AOI",
            "geometry": {"type": "MultiPolygon", "coordinates": [...]}
        })
        aoi_id = response.json()["id"]

        # 5. Verificar jobs criados
        response = await client.get(f"/jobs?aoi_id={aoi_id}", headers=headers)
        jobs = response.json()
        assert len(jobs) == 8  # 8 semanas backfill

        # 6. Aguardar processamento (max 2 min)
        import asyncio
        for _ in range(24):
            await asyncio.sleep(5)
            response = await client.get(f"/jobs?aoi_id={aoi_id}", headers=headers)
            jobs = response.json()
            if all(j["status"] == "COMPLETED" for j in jobs):
                break

        # 7. Verificar tiles disponíveis
        response = await client.get(
            f"/tiles/ndvi/14/8431/6234?aoi_id={aoi_id}",
            headers=headers
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
```

---

### Etapa 7.6: Validação de Resiliência (Fallbacks)

**Objetivo:** Validar que fallbacks funcionam quando serviços falham

```python
# tests/integration/resilience/test_satellite_fallback.py
import pytest
from unittest.mock import AsyncMock


@pytest.mark.integration
async def test_satellite_fallback_when_primary_fails():
    """
    Testa fallback: Primary falha → usa CDSE.
    """
    # Arrange: Primary configurado para falhar
    primary = Mock()
    primary.search_scenes = AsyncMock(side_effect=TimeoutError("PC down"))

    fallback = Mock()
    fallback.search_scenes = AsyncMock(return_value=[
        SatelliteScene(id="cdse-123", ...)
    ])

    adapter = ResilientSatelliteAdapter(primary=primary, fallback=fallback)

    # Act
    scenes = await adapter.search_scenes(geometry={...}, ...)

    # Assert: Usou fallback
    assert len(scenes) == 1
    assert scenes[0].id == "cdse-123"
    fallback.search_scenes.assert_called_once()


@pytest.mark.integration
async def test_satellite_returns_empty_when_all_fail():
    """
    Testa degradação graciosa: Todos falham → retorna []
    """
    # Arrange: Todos configurados para falhar
    primary = Mock()
    primary.search_scenes = AsyncMock(side_effect=TimeoutError())

    fallback = Mock()
    fallback.search_scenes = AsyncMock(side_effect=ConnectionError())

    adapter = ResilientSatelliteAdapter(primary=primary, fallback=fallback)

    # Act
    scenes = await adapter.search_scenes(geometry={...}, ...)

    # Assert: Degradação graciosa - sistema continua
    assert scenes == []  # Lista vazia, não erro!
```

---

### Etapa 7.7: Validação Manual

1. **Trocar provider via config:**
   ```bash
   # .env
   SATELLITE_PROVIDER=cdse  # Muda de Planetary Computer para CDSE
   ```
   - Worker deve buscar cenas do novo provider sem mudanças de código

2. **Simular falha do Planetary Computer:**
   - Desligar Planetary Computer (ou block no firewall)
   - Worker deve automaticamente usar CDSE
   - Logs devem mostrar fallback

3. **Trocar message queue:**
   ```bash
   MESSAGE_QUEUE_TYPE=rabbitmq  # Muda de SQS para RabbitMQ
   ```
   - API deve publicar jobs no RabbitMQ sem recompilação

---

## FASE 8: Limpeza de Código Legado {#fase-8}

**Duração:** 1 semana
**Objetivo:** Remover código obsoleto, feature flags temporários e arquivos legados pós-migração

**Pré-requisitos:**
- ✅ Fase 5, 6 e 7 concluídas
- ✅ Sistema rodando 100% com nova arquitetura em produção por pelo menos 1 semana
- ✅ Zero incidentes relacionados à migração
- ✅ Métricas de performance estáveis

---

### Etapa 8.1: Identificar Código Obsoleto

**Criar inventário de arquivos legados:**

**Arquivo:** `ai/LEGACY_CODE_INVENTORY.md`

```markdown
# Inventário de Código Legado para Remoção

## Services/API

### Infrastructure (DELETAR após migração)
- [ ] `services/api/app/infrastructure/sqs_client.py` → Substituído por `SQSAdapter`
- [ ] `services/api/app/infrastructure/s3_client.py` → Substituído por `S3Adapter`
- [ ] `services/api/app/infrastructure/repositories.py` → Substituído por ports + SQLAlchemy implementations
- [ ] `services/api/app/infrastructure/redis_client.py` → Substituído por `RedisAdapter`

### Application (REFATORAR/DELETAR)
- [ ] `services/api/app/application/farms.py` (se legado não-DI) → Substituído por use cases
- [ ] `services/api/app/application/nitrogen.py` (se legado) → Substituído por use cases

### Domain (MIGRAR LÓGICA, depois DELETAR)
- [ ] `services/api/app/domain/audit.py` (se usa SQLAlchemy direto) → Mover para infrastructure
- [ ] `services/api/app/domain/quotas.py` (se faz queries diretas) → Extrair regras para entities

## Services/Worker

### Pipeline (DELETAR)
- [ ] `services/worker/worker/pipeline/stac_client.py` → Substituído por `PlanetaryComputerAdapter`

### Shared/Utils (DELETAR)
- [ ] `services/worker/worker/shared/aws_clients.py` → Substituído por adapters individuais

### Jobs (REFATORAR - manter arquivo, trocar conteúdo)
- [ ] `services/worker/worker/jobs/process_week.py` → Delegar para `ProcessWeekUseCase`
- [ ] `services/worker/worker/jobs/process_radar.py` → Delegar para use case
- [ ] etc.

## Feature Flags Temporários (REMOVER)
- [ ] `USE_HEXAGONAL_ARCHITECTURE` (config)
- [ ] `ARCHITECTURE_VERSION` (job payloads)
- [ ] Dual code paths em routers (if/else baseado em flag)

## Testes Obsoletos (DELETAR ou ATUALIZAR)
- [ ] Testes que mockam implementações antigas
- [ ] Testes fortemente acoplados a código legado
```

**Executar:**
```bash
# Encontrar TODOs e FIXMEs deixados durante migração
grep -r "TODO.*legacy" services/ --include="*.py"
grep -r "FIXME.*migration" services/ --include="*.py"

# Encontrar imports não utilizados
pylint services/ --disable=all --enable=unused-import

# Encontrar código morto (não referenciado)
vulture services/api/app/
vulture services/worker/worker/
```

---

### Etapa 8.2: Remover Arquivos Legados (Infraestrutura)

**IMPORTANTE:** Fazer em PR separado, após validação em produção

**Arquivos a deletar (API):**

```bash
# 1. Clients legados (substituídos por adapters)
git rm services/api/app/infrastructure/sqs_client.py
git rm services/api/app/infrastructure/s3_client.py
git rm services/api/app/infrastructure/redis_client.py

# 2. Repositories antigos (movidos para persistence/sqlalchemy/)
git rm services/api/app/infrastructure/repositories.py

# 3. Helpers globais (movidos para adapters)
git rm services/api/app/infrastructure/aws_helpers.py
```

**Arquivos a deletar (Worker):**

```bash
# 1. STAC client legado
git rm services/worker/worker/pipeline/stac_client.py

# 2. AWS clients compartilhados
git rm services/worker/worker/shared/aws_clients.py

# 3. Utils obsoletos
git rm services/worker/worker/shared/s3_utils.py
git rm services/worker/worker/shared/sqs_utils.py
```

**Validação antes de deletar:**
```bash
# Verificar se arquivo ainda é importado em algum lugar
grep -r "from.*sqs_client import" services/ --include="*.py"
grep -r "from.*s3_client import" services/ --include="*.py"
grep -r "from.*stac_client import" services/ --include="*.py"

# Se retornar algo → NÃO deletar ainda, migrar imports primeiro
```

---

### Etapa 8.3: Remover Feature Flags Temporários

**1. Remover flag USE_HEXAGONAL_ARCHITECTURE**

**Arquivo:** `services/api/app/config.py`

```python
# ANTES
class Settings(BaseSettings):
    use_hexagonal_architecture: bool = False  # ← DELETAR
    ...

# DEPOIS
class Settings(BaseSettings):
    # Flag removida - sempre usa hexagonal architecture
    ...
```

**2. Remover dual code paths em routers**

**Arquivo:** `services/api/app/presentation/farms_router.py`

```python
# ANTES (dual path com feature flag)
@router.post("/farms")
async def create_farm(name: str, timezone: str, db: Session = Depends(get_db)):
    if settings.use_hexagonal_architecture:
        # Novo caminho
        use_case = Depends(Provide[Container.create_farm_use_case])
        ...
    else:
        # Caminho legado
        use_case = CreateFarmUseCase(db)
        ...

# DEPOIS (apenas novo caminho)
@router.post("/farms")
@inject
async def create_farm(
    name: str,
    timezone: str,
    use_case: CreateFarmUseCase = Depends(Provide[Container.create_farm_use_case])
):
    command = CreateFarmCommand(...)
    return await use_case.execute(command)
```

**3. Remover versão de arquitetura em jobs**

**Arquivo:** `services/worker/worker/jobs/process_week.py`

```python
# ANTES (suporta ambas versões)
async def process_week_job(payload: dict):
    version = payload.get("architecture_version", "legacy")

    if version == "hexagonal":
        # Nova arquitetura
        use_case = container.process_week_use_case()
        ...
    else:
        # Legado
        await legacy_process_week(payload)

# DEPOIS (apenas nova arquitetura)
async def process_week_job(payload: dict):
    """Processa semana usando hexagonal architecture"""
    use_case = container.process_week_use_case()
    command = ProcessWeekCommand(**payload)
    await use_case.execute(command)
```

---

### Etapa 8.4: Limpar Imports e Código Morto

**Instalar ferramentas:**
```bash
pip install autoflake==2.2.1   # Remove imports não usados
pip install isort==5.12.0      # Organiza imports
pip install black==23.12.1     # Formata código
```

**Executar limpeza automatizada:**

```bash
# 1. Remover imports não utilizados
autoflake --in-place --remove-all-unused-imports --recursive services/

# 2. Organizar imports (PEP 8)
isort services/api/app/ services/worker/worker/

# 3. Formatar código
black services/api/app/ services/worker/worker/

# 4. Verificar com linter
pylint services/api/app/ --fail-under=8.0
pylint services/worker/worker/ --fail-under=8.0
```

**Revisão manual:**
```bash
# Encontrar funções/classes não referenciadas
vulture services/api/app/ --min-confidence 80

# Output exemplo:
# services/api/app/utils/legacy_helper.py:42: unused function 'old_compute' (100% confidence)
# → Deletar manualmente
```

---

### Etapa 8.5: Limpar Testes Obsoletos

**Identificar testes quebrados/obsoletos:**

```bash
# Rodar todos os testes
pytest tests/ -v

# Identificar testes que falharam
# → Se testam código legado deletado → DELETAR teste
# → Se testam lógica ainda válida → ATUALIZAR teste
```

**Deletar testes de código legado:**

```bash
# Testes de clients antigos (substituídos por testes de adapters)
git rm tests/unit/infrastructure/test_sqs_client.py
git rm tests/unit/infrastructure/test_s3_client.py

# Testes de implementações antigas
git rm tests/unit/application/test_legacy_farms_service.py
```

**Atualizar testes que ainda são relevantes:**

```python
# ANTES (testa implementação antiga)
def test_create_farm_old():
    service = FarmService(db)  # Classe antiga
    farm = service.create_farm(name="Test")
    assert farm.name == "Test"

# DEPOIS (testa use case novo)
async def test_create_farm_use_case():
    mock_repo = Mock(spec=IFarmRepository)
    use_case = CreateFarmUseCase(farm_repository=mock_repo)

    command = CreateFarmCommand(tenant_id=uuid4(), name="Test")
    response = await use_case.execute(command)

    assert response.name == "Test"
```

---

### Etapa 8.6: Atualizar Documentação

**1. Atualizar CONTEXT.md**

```markdown
# DELETAR seção antiga:
## ~~Arquitetura Atual (Pré-Migração)~~

# ADICIONAR nova seção:
## Arquitetura Hexagonal (Ports & Adapters)

### Camadas
- **Domain:** Entidades Pydantic, value objects, ports (interfaces)
- **Application:** Use cases com dependency injection
- **Infrastructure:** Adapters (SQS, S3, Satellite providers)
- **Presentation:** Routers thin (FastAPI)

### Princípios
1. Dependency Rule: Dependências apontam para dentro
2. Validação Pydantic em 5 camadas
3. Fallbacks automáticos para resiliência
4. Testes com LocalStack (infraestrutura real)
```

**2. Criar ADR (Architecture Decision Record)**

**Arquivo:** `docs/adrs/ADR-0008-hexagonal-architecture-migration.md`

```markdown
# ADR-0008: Migração para Arquitetura Hexagonal

## Status
✅ ACCEPTED (Implementado em 2026-02-05 a 2026-04-15)

## Contexto
Sistema monolítico com acoplamento alto entre camadas, dificultando:
- Testes sem infraestrutura
- Troca de provedores externos (Satellite, Message Queue)
- Validação de dados em runtime

## Decisão
Migrar para arquitetura hexagonal (Ports & Adapters) com:
1. Pydantic para validação em 5 camadas
2. Fallbacks automáticos (resiliência)
3. Testes com LocalStack/Testcontainers

## Consequências

### Positivas
- ✅ Use cases testáveis sem DB/network
- ✅ Trocar satellite provider via config (Planetary Computer ↔ CDSE)
- ✅ Sistema nunca para (degradação graciosa com fallbacks)
- ✅ Dados sempre validados (HTTP → DB)

### Negativas
- ⚠️ Mais código (entities, DTOs, adapters)
- ⚠️ Curva de aprendizado (DI, ports/adapters)

## Código Removido
- infrastructure/sqs_client.py → SQSAdapter
- infrastructure/s3_client.py → S3Adapter
- pipeline/stac_client.py → PlanetaryComputerAdapter
- Feature flags: USE_HEXAGONAL_ARCHITECTURE, ARCHITECTURE_VERSION
```

**3. Atualizar README de desenvolvimento**

```markdown
# ADICIONAR seção:
## Arquitetura

Este projeto usa **Arquitetura Hexagonal (Ports & Adapters)**:

- 📦 **Domain Layer:** Entidades Pydantic puras (sem frameworks)
- 🎯 **Application Layer:** Use cases com DI
- 🔌 **Infrastructure Layer:** Adapters para serviços externos
- 🌐 **Presentation Layer:** Routers FastAPI (thin)

Ver [HEXAGONAL_ARCHITECTURE_PLAN.md](ai/HEXAGONAL_ARCHITECTURE_PLAN.md)
```

---

### Etapa 8.7: Validação Final Pós-Limpeza

**Checklist antes de mergear PR de limpeza:**

```bash
# 1. Todos os testes passam
pytest tests/ -v --cov=services --cov-report=term-missing

# 2. Linter passa
pylint services/api/app/ --fail-under=8.0
pylint services/worker/worker/ --fail-under=8.0
mypy services/api/app/ --strict

# 3. Import-linter valida dependency rule
lint-imports --config .import-linter.toml

# 4. Nenhum import quebrado
python -m compileall services/

# 5. Build Docker funciona
docker-compose build api worker

# 6. E2E passam
pytest tests/e2e/ -v -m e2e
```

**Monitoramento pós-deploy:**

```bash
# Após deploy em produção, monitorar por 24h:
# - Error rate < 0.01%
# - P95 latency inalterado
# - Nenhum log de "module not found" (imports quebrados)
# - Worker job success rate > 99.5%
```

---

### Etapa 8.8: Commit e PR

**Criar PR de limpeza:**

```bash
git checkout -b cleanup/remove-legacy-code

# Stage deletions
git add -A

# Commit com mensagem descritiva
git commit -m "$(cat <<'EOF'
chore: Remove código legado pós-migração hexagonal

Remove arquivos obsoletos após migração completa para
arquitetura hexagonal (Ports & Adapters).

Arquivos removidos:
- infrastructure/sqs_client.py (→ SQSAdapter)
- infrastructure/s3_client.py (→ S3Adapter)
- pipeline/stac_client.py (→ PlanetaryComputerAdapter)
- infrastructure/repositories.py (→ SQLAlchemyRepositories)

Feature flags removidos:
- USE_HEXAGONAL_ARCHITECTURE
- ARCHITECTURE_VERSION (worker jobs)

Dual code paths removidos:
- Routers (apenas DI path mantido)
- Worker jobs (apenas use cases mantidos)

Testes atualizados:
- Removidos testes de código deletado
- Atualizados testes para use cases

Documentação atualizada:
- CONTEXT.md (nova arquitetura)
- ADR-0008 (migration decision)
- README (desenvolvimento)

BREAKING: Código legado removido. Rollback requer
revert deste commit + redeploy versão anterior.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

# Push
git push origin cleanup/remove-legacy-code

# Criar PR
gh pr create --title "chore: Remove código legado pós-migração" \
  --body "Remove código obsoleto após migração para arquitetura hexagonal concluída e validada em produção por 1 semana."
```

---

### Critérios de Aceite (Fase 8)

**Antes de iniciar limpeza:**
- [ ] Sistema rodando com nova arquitetura em produção por ≥ 1 semana
- [ ] Zero incidentes relacionados à migração
- [ ] Feature flags testados (liga/desliga sem problemas)

**Durante limpeza:**
- [ ] Inventário completo de código legado criado
- [ ] Cada arquivo deletado validado (não importado em outro lugar)
- [ ] Todos os feature flags removidos
- [ ] Dual code paths eliminados
- [ ] Imports organizados e limpos
- [ ] Testes obsoletos removidos
- [ ] Documentação atualizada

**Após limpeza:**
- [ ] Todos os testes passam (unit + integration + E2E)
- [ ] Linters passam (pylint, mypy, import-linter)
- [ ] Build Docker funciona
- [ ] Deploy em staging bem-sucedido
- [ ] Monitoramento 24h pós-deploy OK

**Rollback plan:**
- Se problemas após limpeza → `git revert <commit-cleanup>`
- Feature flags já removidos → requer redeploy versão anterior

---

## Segurança Multi-Tenant {#seguranca-multi-tenant}

**CRÍTICO:** Sistema multi-tenant DEVE garantir isolamento total entre tenants em TODAS as camadas.

### Princípio: Defense in Depth (Segurança em Camadas)

```
┌─────────────────────────────────────────────┐
│ 1. PRESENTATION: Extrai tenant do JWT      │ ✅ Valida token
│    → Injeta tenant_id em TODA requisição   │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ 2. APPLICATION: Valida tenant_id no Command │ ✅ Pydantic valida UUID
│    → Use case recebe tenant SEMPRE          │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ 3. DOMAIN: Entity valida tenant obrigatório │ ✅ Farm.tenant_id required
│    → Nunca permite entity sem tenant        │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ 4. REPOSITORY: SEMPRE filtra por tenant_id  │ ✅ WHERE tenant_id = ?
│    → SQL nunca retorna dados de outro tenant│
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ 5. DATABASE: Row Level Security (RLS)       │ ✅ PostgreSQL policy
│    → Último nível de proteção              │
└─────────────────────────────────────────────┘
```

---

### 1. Garantia em PRESENTATION Layer

**Arquivo:** `services/api/app/presentation/dependencies.py`

```python
"""
Dependency para extrair tenant do JWT e garantir em toda requisição.
"""
from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError
from uuid import UUID

from app.config import settings


async def get_current_tenant_id(
    authorization: str = Header(...)
) -> UUID:
    """
    Extrai tenant_id do JWT.

    CRÍTICO: Todo endpoint DEVE usar este dependency.
    Garante que NUNCA processamos requisição sem tenant.

    Raises:
        HTTPException(401): Token inválido ou expirado
        HTTPException(403): Token sem tenant_id
    """
    try:
        # Extrair token
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(401, "Invalid authentication scheme")

        # Decodificar JWT
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        # Extrair tenant_id
        tenant_id_str = payload.get("tenant_id")
        if not tenant_id_str:
            raise HTTPException(403, "Token missing tenant_id")

        # Validar UUID
        tenant_id = UUID(tenant_id_str)

        return tenant_id

    except JWTError as e:
        raise HTTPException(401, f"Invalid token: {str(e)}")
    except ValueError:
        raise HTTPException(403, "Invalid tenant_id format")


async def get_current_user_id(
    authorization: str = Header(...)
) -> UUID:
    """Extrai user_id do JWT (similar ao tenant)"""
    # Similar implementation
    pass
```

**Uso em TODOS os routers:**

```python
# services/api/app/presentation/farms_router.py
from app.presentation.dependencies import get_current_tenant_id

@router.post("/farms")
@inject
async def create_farm(
    request: CreateFarmRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),  # ⬅️ SEMPRE presente
    use_case: CreateFarmUseCase = Depends(Provide[Container.create_farm_use_case])
):
    """
    Cria farm - tenant_id extraído do JWT automaticamente.
    IMPOSSÍVEL criar farm para outro tenant.
    """
    command = CreateFarmCommand(
        tenant_id=tenant_id,  # ⬅️ Tenant do JWT
        name=request.name,
        timezone=request.timezone
    )

    response = await use_case.execute(command)
    return response


@router.get("/farms/{farm_id}")
@inject
async def get_farm(
    farm_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),  # ⬅️ SEMPRE valida
    use_case: GetFarmUseCase = Depends(Provide[Container.get_farm_use_case])
):
    """
    Busca farm - VALIDA se farm pertence ao tenant.
    Retorna 404 se tentar acessar farm de outro tenant.
    """
    command = GetFarmCommand(
        tenant_id=tenant_id,
        farm_id=farm_id
    )

    farm = await use_case.execute(command)

    if not farm:
        raise HTTPException(404, "Farm not found")  # ⬅️ Nunca expõe se existe

    return farm
```

---

### 2. Garantia em APPLICATION Layer

**Arquivo:** `services/api/app/application/use_cases/farms/get_farm.py`

```python
"""
Get Farm use case com validação de tenant.
"""
from pydantic import Field
from uuid import UUID
from typing import Optional

from app.domain.base import ImmutableDTO
from app.domain.entities.farm import Farm
from app.domain.ports.farm_repository import IFarmRepository


class GetFarmCommand(ImmutableDTO):
    """
    Command SEMPRE inclui tenant_id.
    Pydantic garante que é UUID válido.
    """
    tenant_id: UUID
    farm_id: UUID


class GetFarmUseCase:
    """Use case que VALIDA tenant ownership"""

    def __init__(self, farm_repository: IFarmRepository):
        self.farm_repository = farm_repository

    async def execute(self, command: GetFarmCommand) -> Optional[Farm]:
        """
        Busca farm SOMENTE se pertence ao tenant.

        SEGURANÇA: Nunca retorna farm de outro tenant.
        Retorna None se não encontrar ou se pertencer a outro tenant.
        """
        # Repository SEMPRE filtra por tenant_id
        farm = await self.farm_repository.find_by_id_and_tenant(
            farm_id=command.farm_id,
            tenant_id=command.tenant_id  # ⬅️ CRÍTICO
        )

        return farm
```

---

### 3. Garantia em DOMAIN Layer

**Arquivo:** `services/api/app/domain/entities/farm.py`

```python
"""
Farm entity com validação obrigatória de tenant.
"""
from pydantic import Field, field_validator
from uuid import UUID

from app.domain.base import DomainEntity


class Farm(DomainEntity):
    """
    Farm SEMPRE pertence a um tenant.
    Pydantic garante que tenant_id NUNCA é None.
    """

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID  # ⬅️ SEM default, OBRIGATÓRIO
    name: str = Field(min_length=3, max_length=100)
    # ...

    @field_validator('tenant_id')
    @classmethod
    def validate_tenant_id(cls, v: UUID) -> UUID:
        """
        Valida que tenant_id nunca é nulo.
        Adicional: poderia validar contra lista de tenants ativos.
        """
        if not v:
            raise ValueError("tenant_id is required")
        return v
```

**Impossível criar entity sem tenant:**

```python
# ❌ ERRO - Pydantic rejeita
farm = Farm(name="Test Farm")
# ValidationError: field required (type=value_error.missing)

# ✅ OK - Tenant obrigatório
farm = Farm(tenant_id=uuid4(), name="Test Farm")
```

---

### 4. Garantia em REPOSITORY Layer

**Arquivo:** `services/api/app/domain/ports/farm_repository.py`

```python
"""
Farm repository port - SEMPRE exige tenant_id.
"""
from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional

from app.domain.entities.farm import Farm


class IFarmRepository(ABC):
    """
    Repository port com isolamento de tenant OBRIGATÓRIO.
    TODOS os métodos recebem tenant_id.
    """

    @abstractmethod
    async def find_by_id_and_tenant(
        self,
        farm_id: UUID,
        tenant_id: UUID  # ⬅️ OBRIGATÓRIO
    ) -> Optional[Farm]:
        """
        Busca farm POR ID E TENANT.
        Retorna None se não pertencer ao tenant.
        """
        pass

    @abstractmethod
    async def find_all_by_tenant(
        self,
        tenant_id: UUID  # ⬅️ OBRIGATÓRIO
    ) -> List[Farm]:
        """Lista SOMENTE farms do tenant"""
        pass

    @abstractmethod
    async def create(self, farm: Farm) -> Farm:
        """
        Cria farm - tenant_id já está na entity.
        Repository valida que não é None.
        """
        pass
```

**Implementação com SQLAlchemy:**

**Arquivo:** `services/api/app/infrastructure/persistence/sqlalchemy/farm_repository.py`

```python
"""
Farm repository implementation com filtro SEMPRE por tenant.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from typing import List, Optional

from app.domain.ports.farm_repository import IFarmRepository
from app.domain.entities.farm import Farm
from app.infrastructure.models import FarmModel


class SQLAlchemyFarmRepository(IFarmRepository):
    """Repository com isolamento de tenant garantido"""

    def __init__(self, session: Session):
        self.session = session

    async def find_by_id_and_tenant(
        self,
        farm_id: UUID,
        tenant_id: UUID
    ) -> Optional[Farm]:
        """
        SEMPRE filtra por tenant_id no WHERE.
        SQL injection impossível (parametrizado).
        """
        model = self.session.query(FarmModel).filter(
            and_(
                FarmModel.id == farm_id,
                FarmModel.tenant_id == tenant_id  # ⬅️ CRÍTICO
            )
        ).first()

        if not model:
            return None

        # Converter SQLAlchemy model → Domain entity
        return Farm(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            timezone=model.timezone,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def find_all_by_tenant(self, tenant_id: UUID) -> List[Farm]:
        """Lista SOMENTE farms do tenant"""
        models = self.session.query(FarmModel).filter(
            FarmModel.tenant_id == tenant_id  # ⬅️ SEMPRE filtra
        ).all()

        return [
            Farm(
                id=m.id,
                tenant_id=m.tenant_id,
                name=m.name,
                timezone=m.timezone,
                created_at=m.created_at,
                updated_at=m.updated_at
            )
            for m in models
        ]

    async def create(self, farm: Farm) -> Farm:
        """
        Cria farm - valida tenant_id presente.
        """
        if not farm.tenant_id:
            raise ValueError("Cannot create farm without tenant_id")

        model = FarmModel(
            id=farm.id,
            tenant_id=farm.tenant_id,  # ⬅️ Sempre presente (Pydantic garante)
            name=farm.name,
            timezone=farm.timezone,
            created_at=farm.created_at
        )

        self.session.add(model)
        self.session.flush()

        return farm
```

---

### 5. Garantia em DATABASE Layer (Row Level Security)

**Migração:** `infra/migrations/sql/006_enable_row_level_security.sql`

```sql
-- Habilitar Row Level Security (RLS) no PostgreSQL
-- ÚLTIMO nível de defesa - mesmo se código falhar, DB protege

-- 1. Habilitar RLS na tabela farms
ALTER TABLE farms ENABLE ROW LEVEL SECURITY;

-- 2. Criar policy: usuário só vê farms do próprio tenant
CREATE POLICY farms_tenant_isolation ON farms
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 3. Aplicar em TODAS as tabelas multi-tenant
ALTER TABLE aois ENABLE ROW LEVEL SECURITY;
CREATE POLICY aois_tenant_isolation ON aois
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

ALTER TABLE observations ENABLE ROW LEVEL SECURITY;
CREATE POLICY observations_tenant_isolation ON observations
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY jobs_tenant_isolation ON jobs
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
CREATE POLICY signals_tenant_isolation ON signals
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 4. Admin pode ver tudo (bypass RLS)
CREATE POLICY admin_bypass ON farms
    FOR ALL
    TO admin_user  -- Role específico para admin
    USING (true);
```

**Configurar tenant_id na session:**

```python
# services/api/app/infrastructure/persistence/sqlalchemy/session.py
from sqlalchemy.orm import Session
from uuid import UUID


async def set_tenant_context(session: Session, tenant_id: UUID):
    """
    Configura tenant_id no contexto da session PostgreSQL.
    RLS usa este valor para filtrar automaticamente.
    """
    session.execute(
        "SET LOCAL app.current_tenant_id = :tenant_id",
        {"tenant_id": str(tenant_id)}
    )
```

**Uso no repository:**

```python
class SQLAlchemyFarmRepository(IFarmRepository):
    def __init__(self, session: Session):
        self.session = session

    async def find_all_by_tenant(self, tenant_id: UUID) -> List[Farm]:
        # Configurar tenant no contexto (para RLS)
        await set_tenant_context(self.session, tenant_id)

        # Query SEM WHERE tenant_id - RLS adiciona automaticamente!
        models = self.session.query(FarmModel).all()

        # RLS garante que só retorna farms do tenant
        return [self._to_entity(m) for m in models]
```

---

### 6. Auditoria de Acesso

**Arquivo:** `services/api/app/infrastructure/audit/access_logger.py`

```python
"""
Logger de auditoria para acesso a dados sensíveis.
"""
import structlog
from uuid import UUID
from datetime import datetime

from app.infrastructure.models import AuditLog

logger = structlog.get_logger()


class AccessAuditor:
    """
    Audita TODOS os acessos a entidades multi-tenant.
    """

    def __init__(self, session):
        self.session = session

    async def log_access(
        self,
        user_id: UUID,
        tenant_id: UUID,
        resource_type: str,
        resource_id: UUID,
        action: str,  # "READ", "WRITE", "DELETE"
        ip_address: str
    ):
        """
        Registra acesso para auditoria.

        Use cases:
        - Investigar vazamento de dados
        - Compliance (LGPD, GDPR)
        - Detectar acessos suspeitos
        """
        audit_log = AuditLog(
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )

        self.session.add(audit_log)

        logger.info(
            "data_access_audit",
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            resource=f"{resource_type}:{resource_id}",
            action=action,
            ip=ip_address
        )
```

**Uso em use cases:**

```python
class GetFarmUseCase:
    def __init__(
        self,
        farm_repository: IFarmRepository,
        access_auditor: AccessAuditor  # ⬅️ Injetar auditor
    ):
        self.farm_repository = farm_repository
        self.access_auditor = access_auditor

    async def execute(self, command: GetFarmCommand) -> Optional[Farm]:
        farm = await self.farm_repository.find_by_id_and_tenant(
            farm_id=command.farm_id,
            tenant_id=command.tenant_id
        )

        if farm:
            # Auditar acesso
            await self.access_auditor.log_access(
                user_id=command.user_id,
                tenant_id=command.tenant_id,
                resource_type="Farm",
                resource_id=farm.id,
                action="READ",
                ip_address=command.ip_address
            )

        return farm
```

---

### 7. Testes de Segurança Multi-Tenant

**Arquivo:** `tests/security/test_tenant_isolation.py`

```python
"""
Testes de isolamento de tenant - CRÍTICOS para segurança.
"""
import pytest
from uuid import uuid4

from app.domain.entities.farm import Farm
from app.infrastructure.persistence.sqlalchemy.farm_repository import SQLAlchemyFarmRepository


@pytest.mark.security
async def test_cannot_access_farm_from_different_tenant(db_session):
    """
    SEGURANÇA: Garante que tenant A não acessa dados do tenant B.
    """
    # Arrange: 2 tenants
    tenant_a = uuid4()
    tenant_b = uuid4()

    repo = SQLAlchemyFarmRepository(db_session)

    # Criar farm para tenant A
    farm_a = await repo.create(Farm(
        tenant_id=tenant_a,
        name="Farm Tenant A"
    ))

    # Act: Tenant B tenta acessar farm do Tenant A
    farm = await repo.find_by_id_and_tenant(
        farm_id=farm_a.id,
        tenant_id=tenant_b  # ⬅️ Tenant ERRADO
    )

    # Assert: NÃO deve retornar farm
    assert farm is None


@pytest.mark.security
async def test_list_farms_only_returns_own_tenant(db_session):
    """
    SEGURANÇA: Listar farms só retorna do próprio tenant.
    """
    # Arrange: 2 tenants com farms
    tenant_a = uuid4()
    tenant_b = uuid4()

    repo = SQLAlchemyFarmRepository(db_session)

    # Tenant A: 2 farms
    await repo.create(Farm(tenant_id=tenant_a, name="Farm A1"))
    await repo.create(Farm(tenant_id=tenant_a, name="Farm A2"))

    # Tenant B: 3 farms
    await repo.create(Farm(tenant_id=tenant_b, name="Farm B1"))
    await repo.create(Farm(tenant_id=tenant_b, name="Farm B2"))
    await repo.create(Farm(tenant_id=tenant_b, name="Farm B3"))

    # Act: Listar farms do tenant A
    farms_a = await repo.find_all_by_tenant(tenant_a)

    # Assert: Só farms do tenant A
    assert len(farms_a) == 2
    assert all(f.tenant_id == tenant_a for f in farms_a)


@pytest.mark.security
async def test_cannot_create_farm_for_another_tenant_via_jwt(api_client):
    """
    E2E: Não pode criar farm para outro tenant via API.
    """
    # Arrange: Login como tenant A
    response = await api_client.post("/auth/login", json={
        "email": "tenantA@example.com",
        "password": "pass"
    })
    token_a = response.json()["access_token"]
    tenant_a_id = response.json()["tenant_id"]

    # Act: Tentar criar farm com tenant_id diferente no payload
    tenant_b_id = uuid4()
    response = await api_client.post(
        "/farms",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "tenant_id": str(tenant_b_id),  # ⬅️ Tenant ERRADO no payload
            "name": "Malicious Farm"
        }
    )

    # Assert: Deve falhar (403 ou ignorar tenant_id do payload)
    # Router SEMPRE usa tenant do JWT, não do payload
    assert response.status_code in [403, 201]

    if response.status_code == 201:
        farm = response.json()
        # Se criou, deve ter usado tenant do JWT (não do payload)
        assert farm["tenant_id"] == str(tenant_a_id)


@pytest.mark.security
async def test_sql_injection_cannot_bypass_tenant_filter(db_session):
    """
    SEGURANÇA: SQL injection não pode burlar filtro de tenant.
    """
    # Arrange
    tenant_a = uuid4()
    repo = SQLAlchemyFarmRepository(db_session)

    await repo.create(Farm(tenant_id=tenant_a, name="Legit Farm"))

    # Act: Tentar SQL injection no farm_id
    malicious_id = "' OR '1'='1"
    farm = await repo.find_by_id_and_tenant(
        farm_id=malicious_id,  # ⬅️ SQL injection attempt
        tenant_id=tenant_a
    )

    # Assert: SQLAlchemy parametriza query, injection falha
    assert farm is None  # Não deve encontrar
```

**Rodar testes de segurança:**

```bash
# Sempre rodar antes de deploy
pytest tests/security/ -v -m security

# CI/CD deve BLOQUEAR deploy se falhar
```

---

### 8. Checklist de Segurança Multi-Tenant

**Antes de deploy:**

- [ ] **PRESENTATION:** Todo endpoint usa `Depends(get_current_tenant_id)`
- [ ] **APPLICATION:** Todos os Commands têm `tenant_id: UUID` obrigatório
- [ ] **DOMAIN:** Entities validam `tenant_id` obrigatório (Pydantic)
- [ ] **REPOSITORY:** Todos os métodos filtram por `tenant_id` no SQL
- [ ] **DATABASE:** Row Level Security (RLS) habilitado em todas as tabelas
- [ ] **AUDIT:** AccessAuditor registra acessos a dados sensíveis
- [ ] **TESTS:** Testes de isolamento de tenant passam (100% cobertura)

**Code review:**

```bash
# Verificar que NUNCA há query sem filtro de tenant
grep -r "query(FarmModel)" services/ --include="*.py" | grep -v "tenant_id"
# Output vazio = OK

# Verificar que Commands sempre têm tenant_id
grep -r "class.*Command" services/ --include="*.py" -A 5 | grep "tenant_id: UUID"
# Deve aparecer em TODOS os commands
```

---

### 9. Exemplo Completo: Fluxo Seguro

```python
# 1. PRESENTATION: Extrai tenant do JWT
@router.get("/farms/{farm_id}")
async def get_farm(
    farm_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),  # ⬅️ Do JWT
    use_case: GetFarmUseCase = Depends(...)
):
    command = GetFarmCommand(
        tenant_id=tenant_id,  # ⬅️ Tenant autenticado
        farm_id=farm_id
    )
    farm = await use_case.execute(command)
    return farm


# 2. APPLICATION: Valida comando
class GetFarmCommand(ImmutableDTO):
    tenant_id: UUID  # ⬅️ Pydantic valida
    farm_id: UUID


# 3. DOMAIN: Entity valida tenant obrigatório
class Farm(DomainEntity):
    tenant_id: UUID  # ⬅️ Nunca None


# 4. REPOSITORY: Filtra no SQL
async def find_by_id_and_tenant(farm_id, tenant_id):
    return session.query(FarmModel).filter(
        and_(
            FarmModel.id == farm_id,
            FarmModel.tenant_id == tenant_id  # ⬅️ WHERE crítico
        )
    ).first()


# 5. DATABASE: RLS garante (última camada)
-- Policy no PostgreSQL filtra automaticamente
```

**Resultado:** 5 camadas de proteção garantem isolamento!

---

## Critérios de Sucesso

### Arquitetura

- [ ] **Zero imports de frameworks ORM/Web no domain layer** (apenas Pydantic permitido)
- [ ] **Todos os use cases testáveis sem infraestrutura** (mocks dos ports)
- [ ] **Trocar adapters via configuração** (sem mudanças de código)
- [ ] **Dependency Rule validada** (import-linter passa)

### Validação e Resiliência

- [ ] **Pydantic valida em 5 camadas** (HTTP → Presentation → Application → Domain → Infrastructure)
- [ ] **Validação automática em criação E atualização** (validate_assignment=True)
- [ ] **Fallbacks configurados em todas as camadas críticas**:
  - [ ] Satellite Provider: Planetary Computer → CDSE → Cache
  - [ ] Object Storage: S3 → Local filesystem
  - [ ] Message Queue: SQS com retry (3x backoff exponencial)
- [ ] **Sistema nunca para completamente** (degradação graciosa)
- [ ] **Circuit breakers detectam falhas repetidas** (3 falhas → fallback por 5 min)

### Testes

- [ ] **Cobertura de testes > 85%** (domain + application + infrastructure)
- [ ] **Testes unitários < 5 segundos** (sem DB/rede)
- [ ] **Testes de integração com LocalStack** (S3, SQS real)
- [ ] **Testes de integração com Testcontainers** (PostgreSQL, Redis real)
- [ ] **Testes de contrato** (todos adapters implementam ports corretamente)
- [ ] **Testes E2E passando** (< 10 min com stack completa)
- [ ] **CI roda testes unitários + integração** (sempre)
- [ ] **CI roda testes E2E** (pré-deploy apenas)

### Performance e Observabilidade

- [ ] **P95 latency < 200ms** (API endpoints)
- [ ] **Worker job duration < 60s** (média)
- [ ] **Logs estruturados** (structlog JSON)
- [ ] **Métricas de fallback** (quantas vezes fallback foi usado)
- [ ] **Health checks** (todos adapters reportam saúde)

### Documentação

- [ ] **CONTEXT.md atualizado** (arquitetura hexagonal)
- [ ] **ADR criado** (decisão de migração)
- [ ] **Runbooks atualizados** (deployment, rollback)
- [ ] **Developer guide** (como adicionar novo adapter)

---

## Referência Rápida: Melhorias Integradas

### 🛡️ 1. Pydantic para Contratos (Defense in Depth)

**Problema resolvido:** Type hints não validam em runtime → dados inválidos passam despercebidos

**Solução:**
```python
# Domain Entity
class Farm(DomainEntity):  # BaseModel do Pydantic
    name: str = Field(min_length=3, max_length=100)
    timezone: str

    @field_validator('timezone')
    def validate_timezone(cls, v):
        if v not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone: {v}")

# Application Command
class CreateFarmCommand(ImmutableDTO):  # frozen=True
    tenant_id: UUID
    name: str = Field(min_length=3)

# Infrastructure - valida dados externos
class STACItemResponse(BaseModel):
    id: str
    bbox: List[float] = Field(min_length=4, max_length=4)

    @field_validator('bbox')
    def validate_bbox(cls, v):
        if not (-180 <= v[0] <= 180):
            raise ValueError("Invalid longitude")
```

**Benefícios:**
- ✅ Validação automática em criação: `Farm(name="AB")` → ValidationError
- ✅ Validação em atribuição: `farm.name = "X"` → ValidationError (validate_assignment=True)
- ✅ Proteção contra dados externos corrompidos (STAC API, S3 metadata)
- ✅ Mensagens de erro estruturadas (JSON)

**Onde usar:**
- Domain Entities: `DomainEntity` (BaseModel com validate_assignment=True)
- Application DTOs: `ImmutableDTO` (frozen=True para Commands/Responses)
- Infrastructure: Validar respostas de APIs externas

---

### 🔄 2. Fallbacks Automáticos (Resiliência)

**Problema resolvido:** Serviço externo cai → sistema para completamente

**Solução:**
```python
class ResilientSatelliteAdapter(ISatelliteProvider):
    def __init__(self, primary, fallback, cache):
        self.primary = primary      # Planetary Computer
        self.fallback = fallback    # CDSE
        self.cache = cache          # Dados históricos

    async def search_scenes(self, ...):
        # TENTATIVA 1: Primary
        try:
            return await self.primary.search_scenes(...)
        except Exception:
            logger.warning("primary_failed", fallback="cdse")

        # TENTATIVA 2: Fallback
        try:
            return await self.fallback.search_scenes(...)
        except Exception:
            logger.warning("fallback_failed", fallback="cache")

        # TENTATIVA 3: Cache
        if self.cache:
            return await self.cache.retrieve(...)

        # DEGRADAÇÃO GRACIOSA: Lista vazia
        return []  # Sistema continua funcionando!
```

**Fallbacks implementados:**
| Camada | Primary | Fallback 1 | Fallback 2 | Degradação |
|--------|---------|------------|------------|------------|
| Satellite | Planetary Computer | CDSE | Cache | [] (empty) |
| Storage | S3 | Local filesystem | - | Exception |
| Message Queue | SQS (3 retries) | Local queue | Background sync | - |
| Database | Primary (R/W) | Read replica (R) | - | Exception |

**Benefícios:**
- ✅ Sistema NUNCA para completamente
- ✅ Degradação graciosa (funcionalidade reduzida, não erro)
- ✅ Circuit breaker detecta falhas repetidas (3 falhas → fallback por 5 min)
- ✅ Logs estruturados para debugging

**Configuração:**
```python
# DI Container
satellite_provider = providers.Singleton(
    ResilientSatelliteAdapter,
    primary=providers.Singleton(PlanetaryComputerAdapter),
    fallback=providers.Singleton(CDSEAdapter),
    cache=providers.Singleton(SatelliteCache)
)
```

---

### 🧪 3. Testes com Infraestrutura Real (Não Só Mocks)

**Problema resolvido:** Testes com mocks passam, mas produção quebra (serialização, network, etc.)

**Solução:**
```python
# LocalStack para AWS services (S3, SQS)
@pytest.fixture(scope="session")
def localstack():
    with LocalStackContainer() as container:
        container.with_services("s3", "sqs")
        yield container.get_url()

# Testcontainers para PostgreSQL
@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer(image="postgis/postgis:15-3.3") as container:
        yield container.get_connection_url()

# Teste com S3 REAL
@pytest.mark.integration
async def test_s3_upload_with_real_localstack(localstack):
    adapter = S3Adapter(endpoint_url=localstack)

    # Upload para S3 REAL (LocalStack)
    uri = await adapter.upload("test.tif", b"data")

    # Download do S3 REAL
    data = await adapter.download("test.tif")

    # GARANTE: boto3, serialização, network funcionam
    assert data == b"data"
```

**Estratégia de Testes:**
```
        E2E (Docker Compose)           ← 5-10 min | CI: pré-deploy
       /                      \
  Integração (LocalStack)      ← 30s-2min | CI: sempre
 /                            \
Unitários (Mocks)              ← < 5s | CI: sempre
```

**Benefícios:**
- ✅ Detecta bugs de integração ANTES de produção
- ✅ Testa boto3, SQLAlchemy, serialização JSON REAL
- ✅ CI roda LocalStack automaticamente (sem AWS real)
- ✅ Confiança: testes passam = integração funciona

**Setup CI:**
```yaml
# .github/workflows/test.yml
jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests with LocalStack
        run: pytest tests/integration/ -v -m integration
```

---

## Resumo Executivo

**Antes (Plano Original):**
- ✓ Arquitetura hexagonal (Ports & Adapters)
- ✓ Dependency injection
- ✓ Domain purity
- ✗ Validação fraca (type hints apenas)
- ✗ Sem fallbacks (fail fast)
- ✗ Testes com mocks (falsa segurança)

**Depois (Com Melhorias):**
- ✓ Arquitetura hexagonal (Ports & Adapters)
- ✓ Dependency injection
- ✓ Domain purity
- ✅ **Pydantic valida em 5 camadas** (runtime safety)
- ✅ **Fallbacks em cada camada** (nunca para completamente)
- ✅ **LocalStack + Testcontainers** (garante integração funciona)

**Impacto:**
- 🛡️ **Segurança:** Dados sempre validados (HTTP → DB)
- 🔄 **Resiliência:** Sistema degrada graciosamente (não falha catastroficamente)
- ✅ **Confiança:** Testes com infra real detectam bugs antes de produção

**Próximos Passos:**
1. Revisar plano integrado
2. Aprovar abordagem
3. Iniciar Fase 1 (Domain Layer com Pydantic)
