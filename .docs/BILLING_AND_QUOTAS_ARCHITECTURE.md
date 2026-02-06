# Planos de Cobrança e Quotas - Arquitetura Hexagonal

**RESPOSTA DIRETA:** ❌ A arquitetura **NÃO será prejudicada** por planos de cobrança!
**Na verdade:** ✅ Arquitetura hexagonal **FACILITA MUITO** a implementação de billing e quotas!

---

## Por Que Hexagonal é Perfeita para Billing?

```
✅ Domain Service gerencia quotas (lógica de negócio pura)
✅ Billing Adapter abstrai provider (Stripe ↔ Paddle via config)
✅ Feature flags no Domain (plan type é parte do Tenant entity)
✅ Fácil testar quotas SEM billing real (mock do adapter)
✅ Trocar provider de pagamento SEM refatorar código
```

---

## Arquitetura de Planos e Quotas

```
┌──────────────────────────────────────────────────────┐
│ DOMAIN LAYER                                         │
│                                                      │
│ ┌─────────────────┐      ┌────────────────────┐    │
│ │ Tenant Entity   │      │ QuotaService       │    │
│ │                 │      │ (Domain Service)   │    │
│ │ - plan: PlanType│─────▶│                    │    │
│ │ - trial_ends_at │      │ check_quota()      │    │
│ │                 │      │ get_limits()       │    │
│ └─────────────────┘      └────────────────────┘    │
│         │                                           │
│         │                                           │
│ ┌───────▼──────────────────────────────────┐       │
│ │ PlanType (Value Object/Enum)             │       │
│ │ - PERSONAL (Free)                        │       │
│ │ - COMPANY_BASIC (R$ 99/mês)              │       │
│ │ - COMPANY_PRO (R$ 499/mês)               │       │
│ │ - ENTERPRISE (Custom)                    │       │
│ └──────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────┐
│ APPLICATION LAYER                                    │
│                                                      │
│ ┌──────────────────────────────────────────┐        │
│ │ CreateAOIUseCase                         │        │
│ │                                          │        │
│ │ 1. Check quota (QuotaService)            │        │
│ │ 2. If exceeded → QuotaExceededError      │        │
│ │ 3. Create AOI                            │        │
│ │ 4. Update usage count                    │        │
│ └──────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER                                 │
│                                                      │
│ ┌────────────────────┐   ┌──────────────────────┐  │
│ │ IBillingProvider   │   │ IPaymentGateway      │  │
│ │ (Port/Interface)   │   │ (Port/Interface)     │  │
│ └────────┬───────────┘   └─────────┬────────────┘  │
│          │                          │               │
│  ┌───────▼────────┐        ┌────────▼──────────┐   │
│  │ StripeAdapter  │        │ PaddleAdapter     │   │
│  │                │        │                   │   │
│  │ - webhooks     │        │ - subscriptions   │   │
│  │ - subscriptions│        │ - invoices        │   │
│  └────────────────┘        └───────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## 1. Domain Layer: Plan Types e Quotas

**Arquivo:** `services/api/app/domain/value_objects/plan_type.py`

```python
"""
Plan Type - Value Object com quotas configuradas.
"""
from enum import Enum
from dataclasses import dataclass


class PlanType(str, Enum):
    """Tipos de plano disponíveis"""
    PERSONAL = "PERSONAL"
    COMPANY_BASIC = "COMPANY_BASIC"
    COMPANY_PRO = "COMPANY_PRO"
    ENTERPRISE = "ENTERPRISE"


@dataclass(frozen=True)
class PlanQuotas:
    """Quotas e limites por plano (configuração de negócio)"""
    max_farms: int
    max_aois_per_farm: int
    max_total_aois: int
    max_hectares_per_aoi: int
    max_total_hectares: int
    max_backfill_weeks: int
    features: frozenset[str]
    price_monthly_cents: int
    price_yearly_cents: int


# Configuração de quotas (Domain knowledge)
PLAN_QUOTAS = {
    PlanType.PERSONAL: PlanQuotas(
        max_farms=1,
        max_aois_per_farm=3,
        max_total_aois=3,
        max_hectares_per_aoi=50,
        max_total_hectares=50,
        max_backfill_weeks=8,
        features=frozenset([
            "ndvi_analysis",
            "basic_weather",
            "weekly_processing"
        ]),
        price_monthly_cents=0,  # Free
        price_yearly_cents=0
    ),

    PlanType.COMPANY_BASIC: PlanQuotas(
        max_farms=5,
        max_aois_per_farm=10,
        max_total_aois=30,
        max_hectares_per_aoi=500,
        max_total_hectares=2000,
        max_backfill_weeks=52,
        features=frozenset([
            "ndvi_analysis",
            "ndwi_analysis",
            "advanced_weather",
            "weekly_processing",
            "nitrogen_detection",
            "harvest_detection"
        ]),
        price_monthly_cents=9900,  # R$ 99/mês
        price_yearly_cents=99000   # R$ 990/ano (2 meses grátis)
    ),

    PlanType.COMPANY_PRO: PlanQuotas(
        max_farms=50,
        max_aois_per_farm=100,
        max_total_aois=500,
        max_hectares_per_aoi=10000,
        max_total_hectares=50000,
        max_backfill_weeks=104,  # 2 anos
        features=frozenset([
            "ndvi_analysis",
            "ndwi_analysis",
            "advanced_weather",
            "daily_processing",
            "nitrogen_detection",
            "harvest_detection",
            "yield_prediction",
            "correlation_analysis",
            "custom_alerts",
            "api_access",
            "bulk_export"
        ]),
        price_monthly_cents=49900,  # R$ 499/mês
        price_yearly_cents=499000
    ),

    PlanType.ENTERPRISE: PlanQuotas(
        max_farms=-1,  # Unlimited
        max_aois_per_farm=-1,
        max_total_aois=-1,
        max_hectares_per_aoi=-1,
        max_total_hectares=-1,
        max_backfill_weeks=520,  # 10 anos
        features=frozenset(["*"]),  # All features
        price_monthly_cents=-1,  # Custom pricing
        price_yearly_cents=-1
    )
}
```

---

## 2. Domain Service: Quota Validation

**Arquivo:** `services/api/app/domain/services/quota_service.py`

```python
"""
Quota Service - Domain Service para validação de quotas.
NÃO depende de billing provider!
"""
from uuid import UUID
from app.domain.value_objects.plan_type import get_quotas


class QuotaExceededError(Exception):
    """Erro quando quota é excedida"""
    def __init__(self, resource: str, limit: int, current: int, plan: str):
        self.resource = resource
        self.limit = limit
        self.current = current
        self.plan = plan
        super().__init__(
            f"Quota exceeded for {resource}: {current}/{limit} (plan: {plan})"
        )


class QuotaService:
    """
    Domain Service - validação de quotas.
    Usa ports (interfaces), NÃO implementações.
    """

    def __init__(
        self,
        tenant_repository: ITenantRepository,  # Port
        usage_repository: IUsageRepository     # Port
    ):
        self.tenant_repository = tenant_repository
        self.usage_repository = usage_repository

    async def check_can_create_aoi(
        self,
        tenant_id: UUID,
        area_hectares: float
    ) -> None:
        """
        Valida se pode criar nova AOI.

        Raises:
            QuotaExceededError: Se exceder limite do plano
        """
        # 1. Buscar tenant e quotas do plano
        tenant = await self.tenant_repository.find_by_id(tenant_id)
        quotas = get_quotas(tenant.plan)

        # 2. Verificar total de AOIs
        if quotas.max_total_aois != -1:  # -1 = unlimited
            current_aois = await self.usage_repository.count_aois(tenant_id)

            if current_aois >= quotas.max_total_aois:
                raise QuotaExceededError(
                    resource="aois",
                    limit=quotas.max_total_aois,
                    current=current_aois,
                    plan=tenant.plan.value
                )

        # 3. Verificar área total
        if quotas.max_total_hectares != -1:
            current_hectares = await self.usage_repository.sum_total_hectares(tenant_id)

            if current_hectares + area_hectares > quotas.max_total_hectares:
                raise QuotaExceededError(
                    resource="total_hectares",
                    limit=quotas.max_total_hectares,
                    current=int(current_hectares),
                    plan=tenant.plan.value
                )
```

---

## 3. Application Layer: Use Cases com Quotas

**Arquivo:** `services/api/app/application/use_cases/aois/create_aoi.py`

```python
"""
Create AOI use case com validação de quota.
"""
from app.domain.services.quota_service import QuotaService


class CreateAOIUseCase:
    """Use case com validação de quota ANTES de criar"""

    def __init__(
        self,
        aoi_repository: IAOIRepository,
        quota_service: QuotaService  # ⬅️ Domain Service injetado!
    ):
        self.aoi_repository = aoi_repository
        self.quota_service = quota_service

    async def execute(self, command: CreateAOICommand) -> AOI:
        """
        1. VALIDA quota
        2. Cria AOI (se passar validação)
        """
        # 1. VALIDAR QUOTA (pode lançar QuotaExceededError)
        await self.quota_service.check_can_create_aoi(
            tenant_id=command.tenant_id,
            area_hectares=command.area_hectares
        )

        # 2. Criar AOI (passou validação)
        aoi = AOI(
            tenant_id=command.tenant_id,
            farm_id=command.farm_id,
            name=command.name,
            geometry_wkt=command.geometry_wkt,
            area_hectares=command.area_hectares
        )

        # 3. Persistir
        return await self.aoi_repository.create(aoi)
```

---

## 4. Infrastructure: Billing Adapter

**Arquivo:** `services/api/app/domain/ports/billing_provider.py`

```python
"""
Billing Provider port - abstrai Stripe, Paddle, etc.
"""
from abc import ABC, abstractmethod
from uuid import UUID
from app.domain.value_objects.plan_type import PlanType


class IBillingProvider(ABC):
    """
    Port para provedores de billing.

    Implementações:
    - StripeAdapter
    - PaddleAdapter
    - ManualBillingAdapter (Enterprise)
    """

    @abstractmethod
    async def create_customer(
        self,
        tenant_id: UUID,
        email: str
    ) -> str:
        """Cria customer. Returns: customer_id"""
        pass

    @abstractmethod
    async def create_subscription(
        self,
        customer_id: str,
        plan: PlanType,
        billing_interval: str = "monthly"
    ) -> str:
        """Cria subscription. Returns: subscription_id"""
        pass

    @abstractmethod
    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> dict:
        """Processa webhook. Returns: event data"""
        pass
```

**Implementação Stripe:**

```python
# services/api/app/infrastructure/adapters/billing/stripe_adapter.py
import stripe


class StripeAdapter(IBillingProvider):
    """Stripe implementation"""

    def __init__(self, api_key: str, webhook_secret: str):
        stripe.api_key = api_key
        self.webhook_secret = webhook_secret

    async def create_customer(self, tenant_id: UUID, email: str) -> str:
        customer = stripe.Customer.create(
            email=email,
            metadata={"tenant_id": str(tenant_id)}
        )
        return customer.id

    async def create_subscription(
        self,
        customer_id: str,
        plan: PlanType,
        billing_interval: str
    ) -> str:
        price_id = self._get_price_id(plan, billing_interval)

        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            trial_period_days=14
        )
        return subscription.id
```

---

## 5. Trocar Billing Provider via Config

**ZERO mudanças de código!**

```bash
# .env - Produção (Stripe)
BILLING_PROVIDER_TYPE=stripe
STRIPE_API_KEY=sk_live_...

# .env - Teste (Paddle)
BILLING_PROVIDER_TYPE=paddle
PADDLE_VENDOR_ID=...

# .env - Development (sem billing real)
BILLING_PROVIDER_TYPE=manual
```

**DI Container:**

```python
# di_container.py
billing_provider = providers.Selector(
    config.billing_provider_type,
    stripe=providers.Singleton(StripeAdapter, ...),
    paddle=providers.Singleton(PaddleAdapter, ...),
    manual=providers.Singleton(ManualBillingAdapter, ...)
)
```

---

## 6. Mensagens de Erro Amigáveis

**Arquivo:** `services/api/app/presentation/aois_router.py`

```python
@router.post("/aois")
async def create_aoi(...):
    try:
        aoi = await use_case.execute(command)
        return {"id": str(aoi.id)}

    except QuotaExceededError as e:
        # Mensagem amigável com link para upgrade
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                "error": "quota_exceeded",
                "resource": e.resource,
                "limit": e.limit,
                "current": e.current,
                "plan": e.plan,
                "message": f"Você atingiu o limite de {e.limit} {e.resource}",
                "upgrade_url": "/billing/upgrade",
                "plans_url": "/billing/plans"
            }
        )
```

---

## 7. Testes SEM Billing Real

```python
# tests/unit/domain/services/test_quota_service.py
@pytest.mark.asyncio
async def test_personal_plan_limited_to_3_aois():
    """Plano PERSONAL limitado a 3 AOIs"""
    # Mock repositories (SEM Stripe!)
    tenant_repo = AsyncMock()
    tenant_repo.find_by_id.return_value = Tenant(
        email="test@example.com",
        plan=PlanType.PERSONAL  # ⬅️ Plano free
    )

    usage_repo = AsyncMock()
    usage_repo.count_aois.return_value = 3  # Já tem 3

    service = QuotaService(tenant_repo, usage_repo)

    # Act & Assert: Deve falhar (limite 3)
    with pytest.raises(QuotaExceededError) as exc:
        await service.check_can_create_aoi(uuid4(), 10)

    assert exc.value.limit == 3
```

---

## Benefícios da Arquitetura Hexagonal

| Benefício | Como Hexagonal Ajuda |
|-----------|---------------------|
| **Trocar Stripe por Paddle** | Só criar `PaddleAdapter`, configurar no DI |
| **Testar quotas SEM billing** | Mock do port, testa lógica pura |
| **Mudar quotas facilmente** | Configuração centralizada (`PLAN_QUOTAS`) |
| **Feature flags por plano** | `tenant.can_use_feature()` no Domain |
| **Custom pricing (Enterprise)** | `ManualBillingAdapter` para contratos customizados |
| **Múltiplos providers** | Usar Stripe no BR, Paddle na EU (simultaneamente) |

---

## Garantias Fornecidas

1. ✅ **Sem Acoplamento:** Billing provider é adapter, fácil trocar
2. ✅ **Testável:** Quotas testáveis SEM Stripe/Paddle real
3. ✅ **Centralizado:** Configuração de quotas em um só lugar
4. ✅ **Extensível:** Novo plano = adicionar em `PLAN_QUOTAS`
5. ✅ **Flexível:** Múltiplos providers simultaneamente

---

## Resumo: Por Que Hexagonal é Perfeita?

```
Sem Hexagonal:
├─ Código de quota misturado com Stripe
├─ Difícil testar sem billing real
├─ Trocar provider = refatorar tudo
└─ Feature flags espalhados pelo código

Com Hexagonal:
├─ QuotaService (Domain) - lógica pura
├─ IBillingProvider (Port) - abstração
├─ StripeAdapter (Infrastructure) - implementação
└─ Trocar provider = mudar config .env
```

**Conclusão:** Arquitetura hexagonal **FACILITA** billing, não prejudica! 🎉
