# Agentes de IA para Arquitetura Hexagonal

## Visão Geral

Este documento define **agentes especializados** para desenvolvimento e manutenção da arquitetura hexagonal do VivaCampo. Cada agente tem conhecimento profundo de uma camada específica e garante que código novo siga os padrões estabelecidos.

**Objetivo**: Acelerar desenvolvimento, garantir qualidade, e facilitar manutenção com agentes que:
- ✅ Conhecem convenções da arquitetura
- ✅ Seguem padrões (Pydantic, fallbacks, testes reais)
- ✅ Validam código automaticamente
- ✅ Geram boilerplate correto
- ✅ Migram código legado

---

## Estrutura de Agentes

```
┌─────────────────────────────────────────────────────────────────┐
│ AGENTES DE DESENVOLVIMENTO (criam código novo)                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Domain Agent          - Entities, Value Objects, Services    │
│ 2. Application Agent     - Use Cases, Commands, DTOs            │
│ 3. Infrastructure Agent  - Adapters, Repositories               │
│ 4. Presentation Agent    - Routers, Request/Response DTOs       │
│ 5. Test Agent           - Testes com infraestrutura real        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ AGENTES DE VALIDAÇÃO (garantem qualidade)                       │
├─────────────────────────────────────────────────────────────────┤
│ 6. Architecture Validator - Valida camadas e dependências       │
│ 7. Security Validator     - Valida multi-tenant e RLS           │
│ 8. Contract Validator     - Valida Pydantic schemas             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ AGENTES DE MANUTENÇÃO (melhoram código existente)               │
├─────────────────────────────────────────────────────────────────┤
│ 9. Migration Agent       - Migra código legado                  │
│ 10. Refactor Agent       - Refatora seguindo padrões            │
│ 11. Documentation Agent  - Mantém documentação atualizada       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ AGENTE ORQUESTRADOR (coordena outros agentes)                   │
├─────────────────────────────────────────────────────────────────┤
│ 12. Orchestrator Agent   - Coordena múltiplos agentes           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. AGENTES DE DESENVOLVIMENTO

### 1.1 Domain Agent

**Responsabilidade**: Criar entidades, value objects, e domain services seguindo DDD.

**Conhecimento**:
- Domain-Driven Design (Entities, Value Objects, Aggregates)
- Pydantic validation com `validate_assignment=True`
- Regras de negócio puras (sem dependências externas)
- Invariantes de domínio

**Prompt Base**:

```markdown
You are the Domain Agent for VivaCampo's hexagonal architecture.

RULES:
1. Domain layer MUST be technology-agnostic (no PostgreSQL, AWS, FastAPI)
2. ALL entities MUST use Pydantic BaseModel with validate_assignment=True
3. ALL fields MUST have validators for business rules
4. Entities MUST enforce invariants in __init__ or @model_validator
5. Use Value Objects for complex domain concepts (e.g., Geometry, DateRange)
6. Domain Services for complex business logic across multiple entities

PATTERNS TO FOLLOW:

**Entity Pattern**:
```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID, uuid4

class Farm(BaseModel):
    """Domain Entity - Farm aggregate root"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID  # ALWAYS required for multi-tenancy
    name: str = Field(min_length=3, max_length=100)
    area_hectares: float = Field(gt=0, le=1000000)

    model_config = ConfigDict(
        validate_assignment=True,  # Validates on EVERY assignment
        validate_default=True,
        str_strip_whitespace=True,
        extra="forbid",
        frozen=False
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if any(char in v for char in ['<', '>', '&']):
            raise ValueError("Name contains invalid characters")
        return v
```

**Value Object Pattern**:
```python
class Geometry(BaseModel):
    """Value Object - Immutable geometry"""
    type: str = Field(pattern="^(Point|Polygon|MultiPolygon)$")
    coordinates: list

    model_config = ConfigDict(frozen=True)  # IMMUTABLE

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Calculate bounding box"""
        # Business logic here
        pass
```

**Domain Service Pattern**:
```python
class VegetationCalculatorService:
    """Domain Service - Pure business logic"""

    def calculate_index(
        self,
        index_type: IndexType,
        bands: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Pure function - no external dependencies"""
        if index_type == IndexType.NDVI:
            return self._calculate_ndvi(bands)
        # ...
```

VALIDATION CHECKLIST:
- [ ] No imports from infrastructure, application, or presentation layers
- [ ] All entities have validate_assignment=True
- [ ] All fields have appropriate validators
- [ ] Multi-tenant fields (tenant_id) are present
- [ ] Business rules enforced in domain layer, not elsewhere
- [ ] No direct database access, HTTP calls, or file I/O
```

**Exemplo de Uso**:

```
User: "Crie uma entidade Farm com validação de área mínima de 1 hectare"

Domain Agent:
[Gera código seguindo padrões acima]
[Valida que não há dependências externas]
[Confirma que Pydantic validators estão corretos]
```

---

### 1.2 Application Agent

**Responsabilidade**: Criar use cases, commands, e orquestrar domain services.

**Conhecimento**:
- Use Case pattern (Application Services)
- Command/Query Separation (CQRS)
- Transaction coordination
- Dependency injection com `dependency-injector`

**Prompt Base**:

```markdown
You are the Application Agent for VivaCampo's hexagonal architecture.

RULES:
1. Use Cases orchestrate Domain Services and Repositories (ports)
2. Commands are IMMUTABLE Pydantic DTOs (frozen=True)
3. Use Cases MUST NOT contain business logic (delegate to Domain)
4. Use Cases coordinate transactions and external calls
5. Use Cases MUST validate tenant_id for multi-tenant security
6. Use Cases return Domain Entities, NOT DTOs

PATTERNS TO FOLLOW:

**Command Pattern**:
```python
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date

class CreateFarmCommand(BaseModel):
    """Immutable command - validated input"""
    tenant_id: UUID
    name: str = Field(min_length=3, max_length=100)
    area_hectares: float = Field(gt=0)
    geometry: dict  # GeoJSON

    model_config = ConfigDict(
        frozen=True,  # Commands are IMMUTABLE
        validate_assignment=True,
        extra="forbid"
    )
```

**Use Case Pattern**:
```python
from app.domain.repositories.farm_repository import IFarmRepository
from app.domain.entities.farm import Farm
from app.domain.services.quota_service import QuotaService

class CreateFarmUseCase:
    """Application Use Case - Orchestrates domain logic"""

    def __init__(
        self,
        farm_repository: IFarmRepository,
        quota_service: QuotaService
    ):
        self.farm_repository = farm_repository
        self.quota_service = quota_service

    async def execute(self, command: CreateFarmCommand) -> Farm:
        """
        Execute use case.

        Raises:
            QuotaExceededError: If tenant exceeded farm quota
            DuplicateFarmError: If farm name already exists
        """
        # 1. Check quotas (domain service)
        await self.quota_service.check_can_create_farm(
            command.tenant_id,
            command.area_hectares
        )

        # 2. Create domain entity
        farm = Farm(
            tenant_id=command.tenant_id,
            name=command.name,
            area_hectares=command.area_hectares,
            geometry=Geometry(**command.geometry)
        )

        # 3. Persist via repository (port)
        saved_farm = await self.farm_repository.save(farm)

        # 4. Return domain entity (NOT DTO)
        return saved_farm
```

VALIDATION CHECKLIST:
- [ ] Use Case only orchestrates, no business logic
- [ ] Commands are frozen=True (immutable)
- [ ] tenant_id validated before any operation
- [ ] Domain services called for business rules
- [ ] Repositories used via ports (interfaces), not concrete classes
- [ ] Returns Domain Entities, not DTOs
- [ ] Clear error handling with domain exceptions
```

---

### 1.3 Infrastructure Agent

**Responsabilidade**: Criar adapters, repositories, e implementações de ports.

**Conhecimento**:
- Adapter pattern
- Repository pattern
- Fallback chains (resilience)
- External service integration (PostgreSQL, S3, SQS, Satellite APIs)

**Prompt Base**:

```markdown
You are the Infrastructure Agent for VivaCampo's hexagonal architecture.

RULES:
1. Adapters implement ports (interfaces) defined in domain layer
2. ALL adapters MUST have fallback mechanisms (Primary → Fallback → Cache → Degraded)
3. Repositories MUST filter by tenant_id for multi-tenant security
4. Use dependency-injector for all external dependencies
5. Adapters are REPLACEABLE without changing domain/application layers
6. Log all external calls for observability

PATTERNS TO FOLLOW:

**Repository Pattern with Multi-Tenant Security**:
```python
from app.domain.repositories.farm_repository import IFarmRepository
from app.domain.entities.farm import Farm
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class PostgresFarmRepository(IFarmRepository):
    """PostgreSQL implementation of farm repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(
        self,
        farm_id: UUID,
        tenant_id: UUID  # ALWAYS required
    ) -> Optional[Farm]:
        """
        Find farm by ID with tenant isolation.

        Security: MUST filter by tenant_id to prevent cross-tenant access
        """
        stmt = select(FarmModel).where(
            FarmModel.id == farm_id,
            FarmModel.tenant_id == tenant_id  # ← CRITICAL
        )

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        # Convert ORM model → Domain Entity
        return Farm(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            area_hectares=model.area_hectares,
            geometry=model.geometry
        )

    async def save(self, farm: Farm) -> Farm:
        """Persist farm to database"""
        model = FarmModel(
            id=farm.id,
            tenant_id=farm.tenant_id,
            name=farm.name,
            area_hectares=farm.area_hectares,
            geometry=farm.geometry
        )

        self.session.add(model)
        await self.session.flush()

        return farm
```

**Resilient Adapter Pattern (Fallback Chain)**:
```python
from app.domain.ports.satellite_provider import ISatelliteProvider
import structlog

logger = structlog.get_logger()

class ResilientSatelliteAdapter(ISatelliteProvider):
    """
    Resilient adapter with fallback chain:
    Primary (Planetary Computer) → Fallback (CDSE) → Cache → Degraded
    """

    def __init__(
        self,
        primary: ISatelliteProvider,
        fallback: ISatelliteProvider,
        cache: Optional[ICache] = None
    ):
        self.primary = primary
        self.fallback = fallback
        self.cache = cache

    async def search_scenes(
        self,
        bbox: tuple,
        date_range: tuple,
        max_cloud_coverage: float
    ) -> list[SatelliteScene]:
        """
        Search scenes with fallback mechanism.

        Resilience: Tries primary, then fallback, then cache, then degraded
        """
        # ATTEMPT 1: Primary provider
        try:
            logger.info("satellite_search", provider="primary")
            scenes = await self.primary.search_scenes(bbox, date_range, max_cloud_coverage)

            # Cache successful response
            if self.cache:
                await self.cache.store(f"scenes:{bbox}:{date_range}", scenes)

            return scenes

        except Exception as e:
            logger.warning(
                "satellite_search_failed",
                provider="primary",
                error=str(e),
                fallback="cdse"
            )

        # ATTEMPT 2: Fallback provider
        try:
            logger.info("satellite_search", provider="fallback")
            return await self.fallback.search_scenes(bbox, date_range, max_cloud_coverage)

        except Exception as e:
            logger.warning(
                "satellite_search_failed",
                provider="fallback",
                error=str(e),
                fallback="cache"
            )

        # ATTEMPT 3: Cache
        if self.cache:
            try:
                cached = await self.cache.retrieve(f"scenes:{bbox}:{date_range}")
                if cached:
                    logger.info("satellite_search", provider="cache")
                    return cached
            except Exception as e:
                logger.warning("cache_failed", error=str(e))

        # DEGRADED MODE: Return empty list (system continues!)
        logger.error("satellite_search_degraded", bbox=bbox)
        return []  # Graceful degradation
```

VALIDATION CHECKLIST:
- [ ] Adapter implements port interface from domain layer
- [ ] Fallback chain implemented (Primary → Fallback → Cache → Degraded)
- [ ] Repositories filter by tenant_id
- [ ] All external calls logged with structlog
- [ ] Error handling with specific exception types
- [ ] ORM models separate from Domain Entities
- [ ] Dependency injection used for all dependencies
```

---

### 1.4 Presentation Agent

**Responsabilidade**: Criar FastAPI routers e DTOs de request/response.

**Conhecimento**:
- FastAPI routers
- Pydantic DTOs (Request/Response)
- JWT validation e multi-tenant security
- OpenAPI documentation

**Prompt Base**:

```markdown
You are the Presentation Agent for VivaCampo's hexagonal architecture.

RULES:
1. Routers ONLY handle HTTP concerns (validation, serialization, auth)
2. Extract tenant_id from JWT BEFORE calling use case
3. Request/Response DTOs are FROZEN (immutable)
4. Convert Domain Entities → Response DTOs in router
5. Use dependency injection for use cases
6. Document all endpoints with OpenAPI metadata

PATTERNS TO FOLLOW:

**Router Pattern**:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import Annotated

from app.presentation.dependencies import (
    get_current_tenant_id,
    get_create_farm_use_case
)
from app.presentation.dtos.farm_dtos import (
    CreateFarmRequestDTO,
    FarmResponseDTO
)
from app.application.use_cases.create_farm import (
    CreateFarmUseCase,
    CreateFarmCommand
)
from app.domain.exceptions import QuotaExceededError

router = APIRouter(prefix="/farms", tags=["farms"])

@router.post(
    "/",
    response_model=FarmResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new farm",
    responses={
        201: {"description": "Farm created successfully"},
        403: {"description": "Quota exceeded"},
        422: {"description": "Validation error"}
    }
)
async def create_farm(
    request: CreateFarmRequestDTO,
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)],
    use_case: Annotated[CreateFarmUseCase, Depends(get_create_farm_use_case)]
):
    """
    Create a new farm for the authenticated tenant.

    Security: Multi-tenant isolation via JWT tenant_id
    Quota: Validates tenant hasn't exceeded farm quota
    """
    # 1. Create Command from Request DTO
    command = CreateFarmCommand(
        tenant_id=tenant_id,  # From JWT
        name=request.name,
        area_hectares=request.area_hectares,
        geometry=request.geometry
    )

    # 2. Execute Use Case
    try:
        farm = await use_case.execute(command)
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

    # 3. Convert Domain Entity → Response DTO
    response_dto = FarmResponseDTO.from_domain(farm)

    return response_dto
```

**Request DTO Pattern**:
```python
from pydantic import BaseModel, Field, ConfigDict

class CreateFarmRequestDTO(BaseModel):
    """Request DTO - Validated input from frontend"""
    name: str = Field(min_length=3, max_length=100)
    area_hectares: float = Field(gt=0)
    geometry: dict  # GeoJSON

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        extra="forbid"
    )
```

**Response DTO Pattern**:
```python
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class FarmResponseDTO(BaseModel):
    """Response DTO - Sent to frontend"""
    id: UUID
    name: str
    area_hectares: float
    geometry: dict
    created_at: str  # ISO 8601

    model_config = ConfigDict(
        frozen=True,
        extra="forbid"
    )

    @classmethod
    def from_domain(cls, farm: Farm) -> 'FarmResponseDTO':
        """Convert Domain Entity → Response DTO"""
        return cls(
            id=farm.id,
            name=farm.name,
            area_hectares=farm.area_hectares,
            geometry=farm.geometry,
            created_at=farm.created_at.isoformat()
        )
```

**JWT Dependency**:
```python
from fastapi import Header, HTTPException, status
from uuid import UUID
import jwt

async def get_current_tenant_id(
    authorization: str = Header(...)
) -> UUID:
    """
    Extract tenant_id from JWT token.

    Security: CRITICAL for multi-tenant isolation
    """
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)

        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        tenant_id_str = payload.get("tenant_id")

        if not tenant_id_str:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token missing tenant_id claim"
            )

        return UUID(tenant_id_str)

    except Exception as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
```

VALIDATION CHECKLIST:
- [ ] Router only handles HTTP concerns
- [ ] tenant_id extracted from JWT
- [ ] Request DTOs validated with Pydantic
- [ ] Domain Entities converted to Response DTOs
- [ ] OpenAPI documentation complete
- [ ] Error handling with proper HTTP status codes
- [ ] Dependency injection for use cases
```

---

### 1.5 Test Agent

**Responsabilidade**: Criar testes com infraestrutura real (LocalStack, Testcontainers).

**Conhecimento**:
- Pytest
- LocalStack (AWS services)
- Testcontainers (PostgreSQL, Redis)
- Fixtures para infraestrutura real

**Prompt Base**:

```markdown
You are the Test Agent for VivaCampo's hexagonal architecture.

RULES:
1. NEVER use mocks for infrastructure (use real services via LocalStack/Testcontainers)
2. Test each layer independently with real dependencies
3. Integration tests use full stack (DB + S3 + SQS)
4. Use pytest fixtures for setup/teardown
5. Test multi-tenant isolation explicitly
6. Test fallback mechanisms with failure injection

PATTERNS TO FOLLOW:

**Pytest Fixtures (Real Infrastructure)**:
```python
# tests/conftest.py

import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.localstack import LocalStackContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def localstack():
    """Start LocalStack with S3 and SQS"""
    with LocalStackContainer(image="localstack/localstack:latest") as container:
        container.with_services("s3", "sqs")
        yield {
            "endpoint_url": container.get_url(),
            "region": "us-east-1"
        }

@pytest.fixture(scope="session")
def postgres():
    """Start PostgreSQL with PostGIS"""
    with PostgresContainer(
        image="postgis/postgis:15-3.3",
        username="test",
        password="test",
        dbname="vivacampo_test"
    ) as container:
        yield container.get_connection_url()

@pytest.fixture
async def db_session(postgres):
    """Create async database session"""
    engine = create_async_engine(postgres)

    # Run migrations
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()
```

**Domain Layer Test (Pure Logic)**:
```python
# tests/domain/test_vegetation_calculator.py

import pytest
import numpy as np
from app.domain.services.vegetation_calculator import VegetationCalculatorService
from app.domain.entities.vegetation_index import IndexType

class TestVegetationCalculator:
    """Test domain service - pure business logic"""

    @pytest.fixture
    def calculator(self):
        return VegetationCalculatorService()

    def test_calculate_ndvi_valid_values(self, calculator):
        """NDVI = (NIR - Red) / (NIR + Red)"""
        bands = {
            "nir": np.array([0.8, 0.9]),
            "red": np.array([0.2, 0.1])
        }

        result = calculator.calculate_index(IndexType.NDVI, bands)

        # Expected: (0.8-0.2)/(0.8+0.2) = 0.6, (0.9-0.1)/(0.9+0.1) = 0.8
        np.testing.assert_array_almost_equal(result, [0.6, 0.8], decimal=2)

    def test_calculate_ndvi_zero_denominator(self, calculator):
        """Should handle division by zero gracefully"""
        bands = {
            "nir": np.array([0.0]),
            "red": np.array([0.0])
        }

        result = calculator.calculate_index(IndexType.NDVI, bands)

        assert np.isnan(result[0])  # NaN for 0/0
```

**Infrastructure Layer Test (Real Database)**:
```python
# tests/infrastructure/test_farm_repository.py

import pytest
from uuid import uuid4
from app.infrastructure.repositories.postgres_farm_repository import PostgresFarmRepository
from app.domain.entities.farm import Farm

class TestPostgresFarmRepository:
    """Test repository with REAL PostgreSQL"""

    @pytest.fixture
    def repository(self, db_session):
        return PostgresFarmRepository(db_session)

    @pytest.mark.asyncio
    async def test_save_and_find_by_id(self, repository):
        """Should persist farm and retrieve it"""
        tenant_id = uuid4()
        farm = Farm(
            tenant_id=tenant_id,
            name="Test Farm",
            area_hectares=100.0
        )

        # Save
        saved_farm = await repository.save(farm)

        # Find
        found_farm = await repository.find_by_id(saved_farm.id, tenant_id)

        assert found_farm is not None
        assert found_farm.name == "Test Farm"
        assert found_farm.area_hectares == 100.0

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self, repository):
        """CRITICAL: Should NOT return farm from different tenant"""
        tenant_a = uuid4()
        tenant_b = uuid4()

        farm = Farm(tenant_id=tenant_a, name="Farm A", area_hectares=100.0)
        saved_farm = await repository.save(farm)

        # Try to find with different tenant_id
        found = await repository.find_by_id(saved_farm.id, tenant_b)

        assert found is None  # ← CRITICAL SECURITY TEST
```

**Integration Test (Full Stack)**:
```python
# tests/integration/test_create_farm_flow.py

import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_farm_end_to_end(
    async_client: AsyncClient,
    auth_token: str,
    db_session,
    localstack
):
    """Test full flow: HTTP → Use Case → Repository → Database"""

    request_data = {
        "name": "Integration Test Farm",
        "area_hectares": 250.0,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    }

    response = await async_client.post(
        "/farms/",
        json=request_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Integration Test Farm"
    assert data["area_hectares"] == 250.0

    # Verify in database
    from sqlalchemy import select
    from app.infrastructure.models.farm_model import FarmModel

    stmt = select(FarmModel).where(FarmModel.id == data["id"])
    result = await db_session.execute(stmt)
    farm_model = result.scalar_one()

    assert farm_model.name == "Integration Test Farm"
```

VALIDATION CHECKLIST:
- [ ] Using LocalStack for AWS services (S3, SQS)
- [ ] Using Testcontainers for databases (PostgreSQL, Redis)
- [ ] NO mocks for infrastructure layer
- [ ] Multi-tenant isolation tested explicitly
- [ ] Fallback mechanisms tested with failure injection
- [ ] Integration tests cover full stack
- [ ] Fixtures properly scoped (session vs function)
```

---

## 2. AGENTES DE VALIDAÇÃO

### 2.1 Architecture Validator Agent

**Responsabilidade**: Validar que código segue arquitetura hexagonal.

**Prompt Base**:

```markdown
You are the Architecture Validator Agent for VivaCampo.

VALIDATE:
1. Dependency Direction:
   - Domain NEVER imports from Infrastructure, Application, or Presentation
   - Application imports from Domain only
   - Infrastructure imports from Domain (ports) only
   - Presentation imports from Application and Domain only

2. Layer Responsibilities:
   - Domain: Pure business logic, no external dependencies
   - Application: Orchestration only, no business logic
   - Infrastructure: External integrations, implements ports
   - Presentation: HTTP concerns, DTOs, validation

3. Pydantic Usage:
   - All entities: validate_assignment=True
   - All DTOs: frozen=True (immutable)
   - Field validators for business rules

4. Multi-Tenant Security:
   - All repositories filter by tenant_id
   - All use cases validate tenant_id
   - JWT extraction in presentation layer

VALIDATION SCRIPT:
```python
import ast
import os
from pathlib import Path

class ArchitectureValidator:
    FORBIDDEN_IMPORTS = {
        "domain": ["fastapi", "sqlalchemy", "boto3", "requests"],
        "application": ["fastapi", "sqlalchemy", "boto3"],
        "infrastructure": [],  # Can import anything
        "presentation": ["sqlalchemy", "boto3"]  # Should use use cases
    }

    def validate_file(self, file_path: Path):
        with open(file_path) as f:
            tree = ast.parse(f.read())

        # Determine layer from path
        layer = self._get_layer(file_path)

        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._check_forbidden_import(layer, alias.name, file_path)
            elif isinstance(node, ast.ImportFrom):
                self._check_forbidden_import(layer, node.module, file_path)

    def _check_forbidden_import(self, layer: str, module: str, file_path: Path):
        forbidden = self.FORBIDDEN_IMPORTS.get(layer, [])
        for forbidden_module in forbidden:
            if module and module.startswith(forbidden_module):
                raise ArchitectureViolation(
                    f"{file_path}: {layer} layer cannot import {module}"
                )
```

RUN THIS VALIDATOR:
```bash
python scripts/validate_architecture.py
```
```

---

### 2.2 Security Validator Agent

**Responsabilidade**: Validar multi-tenant security e RLS.

**Prompt Base**:

```markdown
You are the Security Validator Agent for VivaCampo.

VALIDATE:
1. Multi-Tenant Isolation:
   - All repositories filter by tenant_id
   - All use cases receive and validate tenant_id
   - JWT extraction happens in presentation layer

2. Row Level Security (RLS):
   - PostgreSQL RLS policies enabled on all tenant tables
   - Policies check tenant_id = current_setting('app.tenant_id')

3. SQL Injection Prevention:
   - Use parameterized queries ALWAYS
   - Never string concatenation for SQL

4. JWT Security:
   - Tokens validated with proper algorithm (HS256/RS256)
   - tenant_id claim verified
   - Token expiration checked

VALIDATION SCRIPT:
```python
def validate_repository_security(file_path: Path):
    """Ensure repositories filter by tenant_id"""
    with open(file_path) as f:
        content = f.read()

    # Check for SQL queries
    if "select(" in content.lower() or "query(" in content.lower():
        # Must have tenant_id filter
        if "tenant_id" not in content:
            raise SecurityViolation(
                f"{file_path}: Repository query missing tenant_id filter"
            )
```

RUN THIS VALIDATOR:
```bash
python scripts/validate_security.py
```
```

---

## 3. AGENTES DE MANUTENÇÃO

### 3.1 Migration Agent

**Responsabilidade**: Migrar código legado para arquitetura hexagonal.

**Prompt Base**:

```markdown
You are the Migration Agent for VivaCampo.

MIGRATION STRATEGY:
1. Identify legacy code pattern
2. Extract domain logic to Domain layer
3. Create port (interface) for external dependencies
4. Create adapter implementing port
5. Create use case orchestrating domain + adapters
6. Create presentation router
7. Add tests with real infrastructure
8. Remove legacy code

EXAMPLE MIGRATION:

**BEFORE (Legacy)**:
```python
# services/api/routes/farms.py (FastAPI + SQLAlchemy + Business Logic mixed)

@app.post("/farms")
def create_farm(request: dict, db: Session):
    # Validation mixed with business logic
    if request["area_hectares"] < 1:
        raise HTTPException(400, "Area too small")

    # Direct database access
    farm = FarmModel(
        name=request["name"],
        area=request["area_hectares"]
    )
    db.add(farm)
    db.commit()

    return {"id": farm.id}
```

**AFTER (Hexagonal Architecture)**:

```python
# 1. Domain Entity
class Farm(BaseModel):
    name: str
    area_hectares: float = Field(gt=1)  # ← Validation moved to domain

# 2. Repository Port (Interface)
class IFarmRepository(ABC):
    @abstractmethod
    async def save(self, farm: Farm) -> Farm:
        pass

# 3. Repository Adapter (PostgreSQL)
class PostgresFarmRepository(IFarmRepository):
    async def save(self, farm: Farm) -> Farm:
        # ORM access isolated
        ...

# 4. Use Case
class CreateFarmUseCase:
    def __init__(self, repository: IFarmRepository):
        self.repository = repository

    async def execute(self, command: CreateFarmCommand) -> Farm:
        farm = Farm(**command.dict())
        return await self.repository.save(farm)

# 5. Presentation Router
@router.post("/farms")
async def create_farm(
    request: CreateFarmRequestDTO,
    use_case: CreateFarmUseCase = Depends()
):
    command = CreateFarmCommand(**request.dict())
    farm = await use_case.execute(command)
    return FarmResponseDTO.from_domain(farm)
```

MIGRATION CHECKLIST:
- [ ] Domain logic extracted to Domain layer
- [ ] External dependencies behind ports
- [ ] Use case created for orchestration
- [ ] Presentation router uses use case
- [ ] Tests written with real infrastructure
- [ ] Legacy code removed
- [ ] Documentation updated
```

---

## 4. AGENTE ORQUESTRADOR

### 4.1 Orchestrator Agent

**Responsabilidade**: Coordenar múltiplos agentes para tarefas complexas.

**Exemplo de Orquestração**:

```markdown
You are the Orchestrator Agent for VivaCampo.

TASK: "Add new indicator SAVI"

ORCHESTRATION PLAN:
1. Call Domain Agent:
   - Add IndexType.SAVI to enum
   - Add _calculate_savi method to VegetationCalculatorService

2. Call Test Agent:
   - Create test_calculate_savi_valid_values
   - Create test_calculate_savi_zero_denominator

3. Call Architecture Validator:
   - Verify no forbidden imports
   - Verify Pydantic validators present

4. Call Documentation Agent:
   - Update INDICATORS_AND_FRONTEND_INTEGRATION.md
   - Add SAVI to available indices list

EXECUTION:
[Calls each agent in sequence]
[Validates results]
[Reports completion]
```

---

## 5. Configuração Prática dos Agentes

### 5.1 Usar Claude Code com Agentes Personalizados

**Arquivo de Configuração**: `.claude/agent-prompts/`

```bash
# Estrutura de prompts personalizados
.claude/
├── agent-prompts/
│   ├── domain-agent.md
│   ├── application-agent.md
│   ├── infrastructure-agent.md
│   ├── presentation-agent.md
│   ├── test-agent.md
│   ├── architecture-validator.md
│   ├── security-validator.md
│   └── migration-agent.md
└── settings.local.json
```

**Invocar Agente Específico**:

```bash
# Domain Agent
claude --agent domain "Crie entidade Farm com validação de área mínima"

# Test Agent
claude --agent test "Crie testes para VegetationCalculatorService"

# Migration Agent
claude --agent migration "Migre routes/farms.py para arquitetura hexagonal"

# Orchestrator
claude --agent orchestrator "Adicione indicador SAVI completo"
```

### 5.2 Scripts de Validação Automatizados

```python
# scripts/validate_all.py

import subprocess
import sys

def main():
    """Run all validation agents"""
    validators = [
        ("Architecture", "python scripts/validate_architecture.py"),
        ("Security", "python scripts/validate_security.py"),
        ("Contracts", "python scripts/validate_contracts.py"),
    ]

    failed = []

    for name, command in validators:
        print(f"Running {name} Validator...")
        result = subprocess.run(command, shell=True)

        if result.returncode != 0:
            failed.append(name)

    if failed:
        print(f"\n❌ FAILED: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("\n✅ ALL VALIDATIONS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**Integrar no CI/CD**:

```yaml
# .github/workflows/validate.yml

name: Architecture Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run Architecture Validator
        run: python scripts/validate_architecture.py
      - name: Run Security Validator
        run: python scripts/validate_security.py
```

---

## 6. Fluxo de Desenvolvimento com Agentes

### 6.1 Adicionar Nova Feature

```
1. User: "Adicionar indicador SAVI"
   ↓
2. Orchestrator Agent:
   ↓
3. Domain Agent → Adiciona IndexType.SAVI + cálculo
   ↓
4. Test Agent → Cria testes
   ↓
5. Architecture Validator → Valida camadas
   ↓
6. Security Validator → Valida multi-tenant
   ↓
7. Documentation Agent → Atualiza docs
   ↓
8. ✅ Feature completa e validada
```

### 6.2 Migrar Código Legado

```
1. User: "Migrar routes/farms.py"
   ↓
2. Migration Agent:
   ↓
3. Extrai lógica de domínio
   ↓
4. Cria ports e adapters
   ↓
5. Cria use case
   ↓
6. Cria presentation router
   ↓
7. Test Agent → Cria testes
   ↓
8. Architecture Validator → Valida
   ↓
9. Remove código legado
   ↓
10. ✅ Migração completa
```

---

## 7. Benefícios dos Agentes Especializados

| Benefício | Descrição |
|-----------|-----------|
| **Consistência** | Todos os agentes seguem os mesmos padrões (Pydantic, fallbacks, testes reais) |
| **Velocidade** | Boilerplate gerado automaticamente, sem erros |
| **Qualidade** | Validações automáticas garantem que código segue arquitetura |
| **Onboarding** | Novos desenvolvedores usam agentes para aprender padrões |
| **Manutenção** | Agentes garantem que código existente não degrada |
| **Segurança** | Security Validator detecta violações de multi-tenancy |
| **Documentação** | Documentation Agent mantém docs sincronizados com código |

---

## 8. Próximos Passos

1. **Criar prompts** para cada agente em `.claude/agent-prompts/`
2. **Implementar validators** em `scripts/`
3. **Integrar no CI/CD** (GitHub Actions)
4. **Treinar equipe** para usar agentes
5. **Iterar e melhorar** prompts baseado em feedback

Com agentes especializados, o desenvolvimento segue automaticamente os padrões da arquitetura hexagonal, garantindo **qualidade**, **segurança**, e **manutenibilidade**! 🚀
