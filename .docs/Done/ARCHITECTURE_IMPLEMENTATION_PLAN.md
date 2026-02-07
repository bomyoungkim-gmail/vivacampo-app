# Plano de Implementação — Correções Arquiteturais

**Data**: 2026-02-06  
**Objetivo**: Corrigir 19 violações hexagonais e implementar Intelligence Features

---

## User Review Required

> [!IMPORTANT]
> **Breaking Changes**: Refatoração move lógica de Domain para Infrastructure, afetando testes que mockam `Session` diretamente.
>
> **Decisão Necessária**:
> - **Opção A (Recomendada)**: Refatorar tudo em 1 PR (22h)
> - **Opção B**: Refatorar incrementalmente em 3 PRs (30h total)

> [!WARNING]
> **Impacto em Testes**: ~15 testes unitários precisarão ser atualizados para usar Ports ao invés de mockar `Session`.

---

## Proposed Changes

### Phase 1: Domain Layer — Remove SQLAlchemy (14h)

#### [MODIFY] [quotas.py](file:///c:/projects/vivacampo-app/services/api/app/domain/quotas.py)

**Problema**: Importa `sqlalchemy.orm.Session`, `text`, `func`

**Solução**:
1. Criar `IQuotaRepository` port
2. Converter funções em `QuotaService` class
3. Manter apenas lógica de negócio (QUOTAS dict)

**Código**:
```python
# domain/quotas.py (DEPOIS)
from domain.ports.quota_repository import IQuotaRepository

class QuotaService:
    def __init__(self, quota_repo: IQuotaRepository):
        self.quota_repo = quota_repo
    
    def check_aoi_quota(self, tenant_id: str) -> None:
        tier = self.quota_repo.get_tenant_tier(tenant_id)
        limits = QUOTAS[tier]
        current = self.quota_repo.count_aois(tenant_id)
        
        if current >= limits["max_aois"]:
            raise QuotaExceededError(...)
```

**Esforço**: 8h

---

#### [NEW] [domain/ports/quota_repository.py](file:///c:/projects/vivacampo-app/services/api/app/domain/ports/quota_repository.py)

```python
from typing import Protocol

class IQuotaRepository(Protocol):
    """Port for quota data access."""
    
    def get_tenant_tier(self, tenant_id: str) -> str: ...
    def count_aois(self, tenant_id: str) -> int: ...
    def count_farms(self, tenant_id: str) -> int: ...
    def count_backfills_today(self, tenant_id: str) -> int: ...
    def count_members(self, tenant_id: str) -> int: ...
    def count_ai_threads_today(self, tenant_id: str) -> int: ...
```

---

#### [NEW] [infrastructure/adapters/persistence/sqlalchemy/quota_repository.py](file:///c:/projects/vivacampo-app/services/api/app/infrastructure/adapters/persistence/sqlalchemy/quota_repository.py)

```python
from sqlalchemy.orm import Session
from sqlalchemy import text
from domain.ports.quota_repository import IQuotaRepository

class SQLAlchemyQuotaRepository(IQuotaRepository):
    def __init__(self, db: Session):
        self.db = db
    
    def get_tenant_tier(self, tenant_id: str) -> str:
        sql = text("SELECT type, plan FROM tenants WHERE id = :tenant_id")
        result = self.db.execute(sql, {"tenant_id": tenant_id}).fetchone()
        
        if not result:
            return "PERSONAL"
        
        tier = f"{result.type}_{result.plan}".upper()
        return tier if tier in QUOTAS else "COMPANY_BASIC"
    
    def count_aois(self, tenant_id: str) -> int:
        sql = text("SELECT COUNT(*) as count FROM aois WHERE tenant_id = :tenant_id AND status = 'ACTIVE'")
        result = self.db.execute(sql, {"tenant_id": tenant_id}).fetchone()
        return result.count if result else 0
    
    # ... implementar outros métodos
```

---

#### [MODIFY] [audit.py](file:///c:/projects/vivacampo-app/services/api/app/domain/audit.py)

**Problema**: Importa `sqlalchemy.orm.Session`, `text`

**Solução**: Criar `IAuditRepository` port

**Código**:
```python
# domain/audit.py (DEPOIS)
from domain.ports.audit_repository import IAuditRepository

class AuditLogger:
    def __init__(self, audit_repo: IAuditRepository):
        self.audit_repo = audit_repo
    
    def log(self, tenant_id: str, actor_id: str, action: str, **kwargs):
        event = {
            "tenant_id": tenant_id,
            "actor_id": actor_id,
            "action": action,
            **kwargs
        }
        self.audit_repo.save_event(event)
```

**Esforço**: 6h

---

### Phase 2: Presentation Layer — Remove Session (4h)

#### [MODIFY] 13 Routers

**Arquivos**:
- `ai_assistant_router.py`, `aois_router.py`, `auth_router.py`
- `correlation_router.py`, `farms_router.py`, `jobs_router.py`
- `nitrogen_router.py`, `radar_router.py`, `signals_router.py`
- `system_admin_router.py`, `tenant_admin_router.py`
- `tiles_router.py`, `weather_router.py`

**Mudança**:
```python
# ANTES
from sqlalchemy.orm import Session
from app.database import get_db

@router.get("/farms")
async def list_farms(
    db: Session = Depends(get_db),  # ❌ REMOVER
    container: ApiContainer = Depends(get_container)
):
    ...

# DEPOIS
@router.get("/farms")
async def list_farms(
    container: ApiContainer = Depends(get_container)
):
    ...
```

**Esforço**: 4h (13 arquivos × ~20min cada)

---

### Phase 3: Infrastructure — DI Wiring (4h)

#### [MODIFY] [di_container.py](file:///c:/projects/vivacampo-app/services/api/app/infrastructure/di_container.py)

**Adicionar**:
```python
class ApiContainer:
    def __init__(self, db: Session, overrides: dict = None):
        self.db = db
        self.overrides = overrides or {}
    
    # NEW
    def quota_repository(self) -> IQuotaRepository:
        if "quota_repository" in self.overrides:
            return self.overrides["quota_repository"]
        return SQLAlchemyQuotaRepository(self.db)
    
    # NEW
    def audit_repository(self) -> IAuditRepository:
        if "audit_repository" in self.overrides:
            return self.overrides["audit_repository"]
        return SQLAlchemyAuditRepository(self.db)
    
    # NEW
    def quota_service(self) -> QuotaService:
        return QuotaService(self.quota_repository())
    
    # NEW
    def audit_logger(self) -> AuditLogger:
        return AuditLogger(self.audit_repository())
```

**Esforço**: 2h

---

#### [MODIFY] Use Cases que usam quotas

**Exemplo**: `application/use_cases/farms.py`

```python
# ANTES
from domain.quotas import check_farm_quota

class CreateFarmUseCase:
    async def execute(self, command: CreateFarmCommand):
        check_farm_quota(command.tenant_id, self.db)  # ❌
        ...

# DEPOIS
class CreateFarmUseCase:
    def __init__(self, farm_repo: IFarmRepository, quota_service: QuotaService):
        self.farm_repo = farm_repo
        self.quota_service = quota_service
    
    async def execute(self, command: CreateFarmCommand):
        self.quota_service.check_farm_quota(command.tenant_id)  # ✅
        ...
```

**Esforço**: 2h (~8 use cases)

---

## Verification Plan

### 1. Architecture Validation

**Command**:
```bash
python scripts/validate_architecture.py
```

**Expected**: `✅ 0 errors, 0 warnings`

---

### 2. Unit Tests — Domain Layer

**Criar**:
```python
# tests/unit/domain/test_quota_service.py
import pytest
from domain.quotas import QuotaService, QuotaExceededError

class FakeQuotaRepository:
    def __init__(self, tier: str, aoi_count: int):
        self.tier = tier
        self.aoi_count = aoi_count
    
    def get_tenant_tier(self, tenant_id: str) -> str:
        return self.tier
    
    def count_aois(self, tenant_id: str) -> int:
        return self.aoi_count

def test_check_aoi_quota_passes():
    repo = FakeQuotaRepository(tier="PERSONAL", aoi_count=2)
    service = QuotaService(repo)
    service.check_aoi_quota("tenant-123")  # Should not raise

def test_check_aoi_quota_fails():
    repo = FakeQuotaRepository(tier="PERSONAL", aoi_count=3)
    service = QuotaService(repo)
    
    with pytest.raises(QuotaExceededError):
        service.check_aoi_quota("tenant-123")
```

**Command**: `pytest tests/unit/domain/test_quota_service.py -v`

---

### 3. Integration Tests

```python
# tests/integration/test_quota_repository.py
@pytest.mark.integration
def test_get_tenant_tier(db_session, seed_tenant):
    repo = SQLAlchemyQuotaRepository(db_session)
    tier = repo.get_tenant_tier(seed_tenant.id)
    assert tier == "PERSONAL"
```

**Command**: `pytest tests/integration/ -v -m integration`

---

### 4. Existing Tests

**Command**: `pytest tests/unit -q`

**Expected**: Todos passam (pode haver ~15 testes para atualizar)

---

## Rollback Plan

1. **Revert PR**: `git revert <commit-hash>`
2. **Rollback DB**: Não há migrations
3. **Redeploy**: `docker compose up --build`

---

## Estimated Effort

| Phase | Tasks | Effort |
|-------|-------|--------|
| Phase 1: Domain refactoring | 6 files | 14h |
| Phase 2: Presentation cleanup | 13 files | 4h |
| Phase 3: DI wiring | 2 files | 4h |
| **Testing & Validation** | Write tests, fix regressions | 8h |
| **TOTAL** | | **30h** (~4 dias) |

---

## Success Metrics

| Metric | Before | After | Validation |
|--------|--------|-------|------------|
| Architecture violations | 19 | 0 | `validate_architecture.py` |
| Domain purity | 40% | 100% | No SQLAlchemy in domain/ |
| Test coverage (Domain) | 65% | 85% | `pytest --cov=app.domain` |

---

## Next Steps

1. ✅ Review this plan
2. ⏳ Get user approval
3. ⏳ Create branch: `git checkout -b fix/architecture-violations`
4. ⏳ Execute Phase 1-3
5. ⏳ Run verification plan
6. ⏳ Create PR
