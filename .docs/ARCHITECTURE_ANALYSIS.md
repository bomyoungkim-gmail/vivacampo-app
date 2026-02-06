# Análise Arquitetural - VivaCampo

## Resumo Executivo

Esta análise identifica **riscos críticos de manutenibilidade** na aplicação VivaCampo e propõe uma arquitetura em camadas com padrões de adaptadores para melhorar modularidade, testabilidade e escalabilidade.

### Principais Preocupações Identificadas ✅

1. **Acoplamento Direto entre Camadas** - Lógica de negócio misturada com infraestrutura
2. **Lógica de Fallback Espalhada** - Resiliência implementada em múltiplos locais ao invés de adaptadores centralizados
3. **Ausência de Portas e Adaptadores** - Dificulta troca de bibliotecas e serviços externos
4. **Violação do Princípio de Inversão de Dependência** - Camadas de alto nível dependem de detalhes de implementação

---

## 1. Análise da Arquitetura Atual

### 1.1 Estrutura Atual

```
services/api/app/
├── presentation/          # Routers (FastAPI)
├── application/          # Use Cases (thin layer)
├── domain/              # Business logic (minimal)
├── infrastructure/      # DB, S3, SQS, resilience
└── config.py

services/worker/worker/
├── jobs/                # Job handlers
├── pipeline/            # STAC client
├── shared/              # AWS clients
└── signals/             # Change detection
```

### 1.2 Problemas Identificados

#### ❌ **Problema 1: Acoplamento Direto entre Camadas**

**Evidência no código:**

```python
# weather_router.py (Presentation Layer)
from app.infrastructure.sqs_client import get_sqs_client  # ❌ Direct infra dependency

@router.post("/aois/{aoi_id}/weather/sync")
async def sync_weather_data(...):
    # Business logic mixed with infrastructure
    sqs = get_sqs_client()  # ❌ Direct coupling
    sqs.send_message(settings.sqs_queue_name, json.dumps(msg))
```

**Impacto:**
- Impossível trocar SQS por RabbitMQ, Kafka ou Redis sem modificar routers
- Testes requerem mock de infraestrutura real
- Violação do princípio de inversão de dependência

---

#### ❌ **Problema 2: Lógica de Fallback Espalhada**

**Evidência no código:**

```python
# process_week.py (Worker Job)
# Fallback logic embedded in business logic
if not valid_scenes:
    logger.info("weekly_search_empty_trying_fallback")
    fallback_start = start_date - timedelta(days=15)  # ❌ Hardcoded fallback
    fallback_scenes = await client.search_scenes(...)  # ❌ Direct retry logic
    
    if valid_scenes:
        is_fallback = True
```

**Impacto:**
- Lógica de resiliência duplicada em múltiplos jobs
- Difícil alterar estratégia de fallback globalmente
- Não há separação entre "o que fazer" e "como lidar com falhas"

---

#### ❌ **Problema 3: Ausência de Adaptadores**

**Evidência:**

```python
# stac_client.py - Direct implementation without interface
class STACClient:
    async def search_scenes(self, ...):
        # Direct Planetary Computer API calls
        # No abstraction layer
```

**Impacto:**
- Impossível trocar Planetary Computer por Google Earth Engine, AWS Open Data, ou Sentinel Hub
- Testes requerem acesso real à API externa
- Vendor lock-in

---

#### ❌ **Problema 4: Infraestrutura Vazando para Camadas Superiores**

**Evidência:**

```python
# farms.py (Application Layer)
from app.infrastructure.repositories import FarmRepository  # ❌ Direct infra import
from app.infrastructure.models import Farm  # ❌ SQLAlchemy model in use case

class CreateFarmUseCase:
    def __init__(self, db: Session):  # ❌ SQLAlchemy Session
        self.farm_repo = FarmRepository(db)
```

**Impacto:**
- Use cases acoplados ao SQLAlchemy
- Impossível trocar ORM (ex: para Prisma, TypeORM, ou raw SQL)
- Modelos de domínio poluídos com anotações de framework

---

## 2. Arquitetura Proposta: Hexagonal (Ports & Adapters)

### 2.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│              (FastAPI Routers, GraphQL, gRPC)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│         (Use Cases, Application Services, DTOs)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
│    (Entities, Value Objects, Domain Services, Interfaces)    │
│                    ⚠️ NO DEPENDENCIES                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                       │
│         (Adapters: DB, S3, SQS, STAC, Weather APIs)          │
│              Implements Domain Interfaces                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Princípios Fundamentais

1. **Dependency Inversion Principle (DIP)**
   - Camadas superiores definem interfaces (Ports)
   - Camadas inferiores implementam interfaces (Adapters)
   - Fluxo de dependência: Infrastructure → Domain ← Application

2. **Separation of Concerns**
   - Domain: Regras de negócio puras
   - Application: Orquestração de casos de uso
   - Infrastructure: Detalhes técnicos

3. **Testability**
   - Domain testável sem infraestrutura
   - Adapters intercambiáveis via injeção de dependência

---

## 3. Refatoração Proposta por Camada

### 3.1 Domain Layer (Core)

**Estrutura:**

```
services/api/app/domain/
├── entities/
│   ├── farm.py              # Domain entity (pure Python)
│   ├── aoi.py
│   └── observation.py
├── value_objects/
│   ├── coordinates.py
│   └── ndvi_stats.py
├── repositories/            # ⚠️ INTERFACES (not implementations)
│   ├── farm_repository.py
│   └── aoi_repository.py
├── services/                # Domain services
│   ├── satellite_data_service.py
│   └── weather_service.py
└── ports/                   # External service interfaces
    ├── message_queue.py     # Abstract message queue
    ├── object_storage.py    # Abstract S3
    └── stac_provider.py     # Abstract STAC API
```

**Exemplo - Port (Interface):**

```python
# domain/ports/message_queue.py
from abc import ABC, abstractmethod
from typing import Any

class IMessageQueue(ABC):
    """Port for message queue operations"""
    
    @abstractmethod
    async def publish(self, queue_name: str, message: dict) -> str:
        """Publish message to queue. Returns message ID."""
        pass
    
    @abstractmethod
    async def consume(self, queue_name: str, handler: callable) -> None:
        """Consume messages from queue"""
        pass
```

**Exemplo - Domain Entity:**

```python
# domain/entities/farm.py
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

@dataclass
class Farm:
    """Pure domain entity - no framework dependencies"""
    id: UUID
    tenant_id: UUID
    name: str
    timezone: str
    created_at: datetime
    
    def validate(self) -> None:
        if not self.name or len(self.name) < 3:
            raise ValueError("Farm name must be at least 3 characters")
        
        # Domain validation logic here
```

---

### 3.2 Infrastructure Layer (Adapters)

**Estrutura:**

```
services/api/app/infrastructure/
├── adapters/
│   ├── message_queue/
│   │   ├── sqs_adapter.py          # SQS implementation
│   │   ├── rabbitmq_adapter.py     # Alternative implementation
│   │   └── redis_adapter.py        # Alternative implementation
│   ├── storage/
│   │   ├── s3_adapter.py
│   │   └── gcs_adapter.py          # Google Cloud Storage
│   ├── stac/
│   │   ├── planetary_computer_adapter.py
│   │   ├── earth_engine_adapter.py
│   │   └── sentinel_hub_adapter.py
│   └── weather/
│       ├── open_meteo_adapter.py
│       └── weather_api_adapter.py
├── persistence/
│   ├── sqlalchemy/
│   │   ├── models.py               # ORM models
│   │   ├── farm_repository.py      # Implements domain interface
│   │   └── aoi_repository.py
│   └── migrations/
└── resilience/
    ├── circuit_breaker.py
    ├── retry_policy.py
    └── fallback_decorator.py       # ✅ Centralized fallback logic
```

**Exemplo - Adapter com Fallback Centralizado:**

```python
# infrastructure/adapters/stac/planetary_computer_adapter.py
from app.domain.ports.stac_provider import ISTACProvider
from app.infrastructure.resilience.fallback_decorator import with_fallback
from app.infrastructure.resilience.circuit_breaker import circuit

class PlanetaryComputerAdapter(ISTACProvider):
    """STAC adapter with built-in resilience"""
    
    @circuit(failure_threshold=5, recovery_timeout=60)
    @with_fallback(
        fallback_strategy="expand_time_window",
        max_expansion_days=30
    )
    async def search_scenes(
        self, 
        geometry: dict, 
        start_date: datetime, 
        end_date: datetime,
        max_cloud_cover: float
    ) -> list[dict]:
        """
        Search for satellite scenes with automatic fallback.
        
        Fallback strategy:
        1. Try exact time window
        2. If no results, expand to ±15 days
        3. If still no results, expand to ±30 days
        4. Circuit breaker opens after 5 failures
        """
        # Implementation here
        pass
```

**Exemplo - Adapter de Message Queue:**

```python
# infrastructure/adapters/message_queue/sqs_adapter.py
from app.domain.ports.message_queue import IMessageQueue
import boto3
import json

class SQSAdapter(IMessageQueue):
    """SQS implementation of message queue port"""
    
    def __init__(self, region: str, endpoint_url: str = None):
        self.client = boto3.client('sqs', region_name=region, endpoint_url=endpoint_url)
    
    async def publish(self, queue_name: str, message: dict) -> str:
        response = self.client.send_message(
            QueueUrl=self._get_queue_url(queue_name),
            MessageBody=json.dumps(message)
        )
        return response['MessageId']
    
    async def consume(self, queue_name: str, handler: callable) -> None:
        # Implementation
        pass
```

**Exemplo - Adapter Alternativo (RabbitMQ):**

```python
# infrastructure/adapters/message_queue/rabbitmq_adapter.py
from app.domain.ports.message_queue import IMessageQueue
import aio_pika

class RabbitMQAdapter(IMessageQueue):
    """RabbitMQ implementation - drop-in replacement for SQS"""
    
    def __init__(self, host: str, port: int):
        self.connection = None
        self.host = host
        self.port = port
    
    async def publish(self, queue_name: str, message: dict) -> str:
        # RabbitMQ implementation
        pass
```

---

### 3.3 Application Layer (Use Cases)

**Estrutura:**

```
services/api/app/application/
├── use_cases/
│   ├── farms/
│   │   ├── create_farm.py
│   │   ├── list_farms.py
│   │   └── delete_farm.py
│   ├── aois/
│   │   ├── create_aoi.py
│   │   └── trigger_processing.py
│   └── weather/
│       └── sync_weather_data.py
├── dtos/                    # Data Transfer Objects
│   ├── farm_dto.py
│   └── aoi_dto.py
└── services/                # Application services (orchestration)
    └── job_dispatcher.py
```

**Exemplo - Use Case com Dependency Injection:**

```python
# application/use_cases/weather/sync_weather_data.py
from app.domain.ports.message_queue import IMessageQueue
from app.domain.repositories.aoi_repository import IAOIRepository
from dataclasses import dataclass
from uuid import UUID

@dataclass
class SyncWeatherDataCommand:
    tenant_id: UUID
    aoi_id: UUID

class SyncWeatherDataUseCase:
    """
    Use case for triggering weather data synchronization.
    
    Dependencies injected via constructor (Dependency Inversion).
    """
    
    def __init__(
        self,
        message_queue: IMessageQueue,  # ✅ Interface, not implementation
        aoi_repository: IAOIRepository  # ✅ Interface, not implementation
    ):
        self.message_queue = message_queue
        self.aoi_repository = aoi_repository
    
    async def execute(self, command: SyncWeatherDataCommand) -> str:
        # 1. Validate AOI exists
        aoi = await self.aoi_repository.get_by_id(command.aoi_id, command.tenant_id)
        if not aoi:
            raise ValueError(f"AOI {command.aoi_id} not found")
        
        # 2. Create job
        job_id = await self._create_job(command)
        
        # 3. Dispatch to queue
        message = {
            "job_id": str(job_id),
            "job_type": "PROCESS_WEATHER",
            "payload": {
                "tenant_id": str(command.tenant_id),
                "aoi_id": str(command.aoi_id)
            }
        }
        
        await self.message_queue.publish("jobs-queue", message)
        
        return job_id
```

---

### 3.4 Presentation Layer (Controllers)

**Exemplo - Router Refatorado:**

```python
# presentation/weather_router.py
from fastapi import APIRouter, Depends
from app.application.use_cases.weather.sync_weather_data import (
    SyncWeatherDataUseCase,
    SyncWeatherDataCommand
)
from app.auth.dependencies import get_current_membership

router = APIRouter()

@router.post("/aois/{aoi_id}/weather/sync")
async def sync_weather_data(
    aoi_id: UUID,
    membership: CurrentMembership = Depends(get_current_membership),
    use_case: SyncWeatherDataUseCase = Depends()  # ✅ Injected via DI container
):
    """
    Thin controller - delegates to use case.
    No business logic, no infrastructure dependencies.
    """
    command = SyncWeatherDataCommand(
        tenant_id=membership.tenant_id,
        aoi_id=aoi_id
    )
    
    job_id = await use_case.execute(command)
    
    return {"message": "Weather sync started", "job_id": job_id}
```

---

## 4. Dependency Injection Container

**Configuração Centralizada:**

```python
# infrastructure/di_container.py
from dependency_injector import containers, providers
from app.domain.ports.message_queue import IMessageQueue
from app.infrastructure.adapters.message_queue.sqs_adapter import SQSAdapter
from app.infrastructure.adapters.message_queue.rabbitmq_adapter import RabbitMQAdapter
from app.config import settings

class Container(containers.DeclarativeContainer):
    """Dependency Injection container"""
    
    config = providers.Configuration()
    
    # Message Queue Adapter (configurable)
    message_queue = providers.Selector(
        config.message_queue_type,
        sqs=providers.Singleton(
            SQSAdapter,
            region=config.aws_region,
            endpoint_url=config.aws_endpoint_url
        ),
        rabbitmq=providers.Singleton(
            RabbitMQAdapter,
            host=config.rabbitmq_host,
            port=config.rabbitmq_port
        )
    )
    
    # STAC Provider Adapter (configurable)
    stac_provider = providers.Selector(
        config.stac_provider,
        planetary_computer=providers.Singleton(PlanetaryComputerAdapter),
        earth_engine=providers.Singleton(EarthEngineAdapter),
        sentinel_hub=providers.Singleton(SentinelHubAdapter)
    )
    
    # Use Cases
    sync_weather_use_case = providers.Factory(
        SyncWeatherDataUseCase,
        message_queue=message_queue,
        aoi_repository=aoi_repository
    )
```

**Configuração via Environment Variables:**

```bash
# .env
MESSAGE_QUEUE_TYPE=sqs          # ou rabbitmq, redis
STAC_PROVIDER=planetary_computer # ou earth_engine, sentinel_hub
OBJECT_STORAGE=s3               # ou gcs, azure_blob
```

---

## 5. Resiliência Centralizada

### 5.1 Decorator de Fallback Genérico

```python
# infrastructure/resilience/fallback_decorator.py
from functools import wraps
from typing import Callable, Any
import structlog

logger = structlog.get_logger()

def with_fallback(
    fallback_strategy: str,
    max_expansion_days: int = 30,
    fallback_collections: list = None
):
    """
    Centralized fallback decorator.
    
    Strategies:
    - expand_time_window: Expand search window incrementally
    - alternative_collection: Try alternative data sources
    - degraded_quality: Accept lower quality data
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                # Try primary strategy
                result = await func(*args, **kwargs)
                
                if result:
                    return result
                
                # Apply fallback strategy
                if fallback_strategy == "expand_time_window":
                    return await _expand_time_window_fallback(
                        func, args, kwargs, max_expansion_days
                    )
                elif fallback_strategy == "alternative_collection":
                    return await _alternative_collection_fallback(
                        func, args, kwargs, fallback_collections
                    )
                
                return result
                
            except Exception as e:
                logger.error("fallback_failed", error=str(e), exc_info=True)
                raise
        
        return wrapper
    return decorator

async def _expand_time_window_fallback(func, args, kwargs, max_days):
    """Expand time window incrementally"""
    from datetime import timedelta
    
    original_start = kwargs.get('start_date')
    original_end = kwargs.get('end_date')
    
    for expansion in [15, 30]:
        if expansion > max_days:
            break
        
        kwargs['start_date'] = original_start - timedelta(days=expansion)
        kwargs['end_date'] = original_end + timedelta(days=expansion)
        
        logger.info("fallback_expanding_window", expansion_days=expansion)
        
        result = await func(*args, **kwargs)
        if result:
            logger.info("fallback_success", strategy="expand_time_window")
            return result
    
    return []
```

---

## 6. Outros Riscos Identificados e Soluções

### 6.1 **Risco: Vendor Lock-in (AWS)**

**Problema:**
- Código acoplado a boto3, S3, SQS
- Difícil migrar para GCP, Azure, ou on-premise

**Solução:**

```python
# domain/ports/object_storage.py
class IObjectStorage(ABC):
    @abstractmethod
    async def upload(self, key: str, data: bytes) -> str:
        pass
    
    @abstractmethod
    async def download(self, key: str) -> bytes:
        pass
    
    @abstractmethod
    async def generate_presigned_url(self, key: str, expires_in: int) -> str:
        pass

# infrastructure/adapters/storage/s3_adapter.py
class S3Adapter(IObjectStorage):
    # AWS S3 implementation

# infrastructure/adapters/storage/gcs_adapter.py
class GCSAdapter(IObjectStorage):
    # Google Cloud Storage implementation
```

---

### 6.2 **Risco: Falta de Observabilidade**

**Problema:**
- Logs espalhados
- Métricas não padronizadas
- Difícil rastrear requests entre serviços

**Solução:**

```python
# infrastructure/observability/tracing.py
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

tracer = trace.get_tracer(__name__)

# Decorator para rastreamento automático
def traced(operation_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(operation_name) as span:
                span.set_attribute("function", func.__name__)
                result = await func(*args, **kwargs)
                return result
        return wrapper
    return decorator

# Uso
@traced("stac.search_scenes")
async def search_scenes(self, ...):
    pass
```

---

### 6.3 **Risco: Testes Acoplados à Infraestrutura**

**Problema Atual:**
- Testes requerem LocalStack, banco de dados real
- Lentos e frágeis

**Solução:**

```python
# tests/unit/application/test_sync_weather_use_case.py
import pytest
from unittest.mock import AsyncMock
from app.application.use_cases.weather.sync_weather_data import SyncWeatherDataUseCase

@pytest.mark.asyncio
async def test_sync_weather_creates_job():
    # Arrange
    mock_queue = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = {"id": "aoi-123"}
    
    use_case = SyncWeatherDataUseCase(
        message_queue=mock_queue,
        aoi_repository=mock_repo
    )
    
    # Act
    job_id = await use_case.execute(command)
    
    # Assert
    mock_queue.publish.assert_called_once()
    assert job_id is not None
```

---

### 6.4 **Risco: Escalabilidade Horizontal**

**Problema:**
- Workers compartilham estado global
- Circuit breakers não sincronizados entre instâncias

**Solução:**

```python
# infrastructure/resilience/distributed_circuit_breaker.py
import redis.asyncio as redis

class DistributedCircuitBreaker:
    """Circuit breaker using Redis for state sharing"""
    
    def __init__(self, redis_client: redis.Redis, service_name: str):
        self.redis = redis_client
        self.key_prefix = f"circuit_breaker:{service_name}"
    
    async def is_open(self) -> bool:
        state = await self.redis.get(f"{self.key_prefix}:state")
        return state == b"OPEN"
    
    async def record_failure(self):
        failures = await self.redis.incr(f"{self.key_prefix}:failures")
        
        if failures >= self.threshold:
            await self.redis.set(f"{self.key_prefix}:state", "OPEN")
            await self.redis.expire(f"{self.key_prefix}:state", self.recovery_timeout)
```

---

## 7. Plano de Migração Incremental

### Fase 1: Criar Interfaces (Ports) - **2 semanas**

1. Definir interfaces em `domain/ports/`
2. Documentar contratos
3. Sem quebrar código existente

### Fase 2: Implementar Adapters - **3 semanas**

1. Criar adapters para serviços existentes (SQS, S3, STAC)
2. Manter código legado funcionando
3. Testes paralelos

### Fase 3: Refatorar Use Cases - **4 semanas**

1. Migrar use cases para usar interfaces
2. Implementar DI container
3. Testes de integração

### Fase 4: Centralizar Resiliência - **2 semanas**

1. Mover lógica de fallback para decorators
2. Implementar circuit breakers distribuídos
3. Remover código duplicado

### Fase 5: Remover Código Legado - **1 semana**

1. Deletar implementações antigas
2. Atualizar documentação
3. Treinamento da equipe

---

## 8. Métricas de Sucesso

| Métrica | Antes | Meta |
|---------|-------|------|
| **Cobertura de Testes Unitários** | ~30% | >80% |
| **Tempo de Build** | ~5min | <2min |
| **Acoplamento entre Camadas** | Alto | Baixo (interfaces) |
| **Tempo para Trocar Provedor** | ~2 semanas | ~2 dias |
| **Duplicação de Código (Fallbacks)** | ~5 locais | 1 local (decorator) |

---

## 9. Referências e Práticas de Mercado

### Arquiteturas Similares em Produção

1. **Uber** - Hexagonal Architecture para microserviços
   - [Engineering Blog](https://eng.uber.com/microservice-architecture/)

2. **Netflix** - Resilience4j para circuit breakers
   - [Hystrix → Resilience4j migration](https://netflixtechblog.com/)

3. **Spotify** - Domain-Driven Design
   - [DDD at Spotify](https://engineering.atspotify.com/)

### Bibliotecas Recomendadas

```python
# Dependency Injection
dependency-injector==4.41.0

# Circuit Breaker / Resilience
resilience4py==0.1.0  # Port of Resilience4j

# Observability
opentelemetry-api==1.20.0
opentelemetry-sdk==1.20.0
opentelemetry-instrumentation-fastapi==0.41b0

# Testing
pytest-asyncio==0.21.0
pytest-mock==3.11.1
```

---

## 10. Conclusão

### Benefícios da Refatoração

✅ **Manutenibilidade**: Código modular e desacoplado  
✅ **Testabilidade**: Testes rápidos sem infraestrutura  
✅ **Escalabilidade**: Fácil adicionar novos provedores  
✅ **Resiliência**: Fallbacks centralizados e consistentes  
✅ **Flexibilidade**: Trocar bibliotecas sem impacto  

### Próximos Passos

1. **Revisar este documento** com a equipe técnica
2. **Priorizar Fase 1** (criar interfaces)
3. **Definir ADR** (Architecture Decision Record) para mudanças
4. **Criar POC** com um adapter (ex: SQS → RabbitMQ)
5. **Executar migração incremental** sem parar desenvolvimento

---

## Apêndice: Exemplo Completo de Fluxo

### Antes (Acoplado)

```python
# weather_router.py
@router.post("/sync")
async def sync(aoi_id: UUID, db: Session = Depends(get_db)):
    sqs = get_sqs_client()  # ❌ Direct coupling
    sqs.send_message("queue", json.dumps(msg))
```

### Depois (Desacoplado)

```python
# weather_router.py
@router.post("/sync")
async def sync(
    aoi_id: UUID,
    use_case: SyncWeatherUseCase = Depends()  # ✅ DI
):
    await use_case.execute(SyncWeatherCommand(aoi_id=aoi_id))

# application/use_cases/weather/sync_weather_data.py
class SyncWeatherUseCase:
    def __init__(self, queue: IMessageQueue):  # ✅ Interface
        self.queue = queue
    
    async def execute(self, cmd: SyncWeatherCommand):
        await self.queue.publish("jobs", {...})

# infrastructure/di_container.py
Container.message_queue = providers.Selector(
    config.queue_type,
    sqs=providers.Singleton(SQSAdapter),      # ✅ Swappable
    rabbitmq=providers.Singleton(RabbitMQAdapter)
)
```

**Resultado:**
- Trocar SQS → RabbitMQ: **1 linha de configuração**
- Testar use case: **sem infraestrutura**
- Adicionar Kafka: **novo adapter, zero mudanças no core**
