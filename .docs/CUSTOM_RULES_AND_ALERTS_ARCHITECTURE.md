# Arquitetura de Regras Customizáveis e Alertas

## Visão Geral

Este documento define a arquitetura para separar **indicadores brutos** de **regras/alertas personalizados**, permitindo que admins criem regras customizadas via frontend sem escrever código.

---

## 1. Separação Conceitual

### 1.1 Indicadores Brutos (Raw Indices) - Camada de Domínio

**O que são:**
- Cálculos matemáticos puros baseados em bandas espectrais
- Definições científicas fixas (NDVI, NDWI, SAVI, EVI, etc.)
- **NÃO mudam** (são fórmulas matemáticas estabelecidas)

**Responsável:**
- `VegetationCalculatorService` (Domain Service)

**Exemplo:**
```python
# Indicador bruto - Fórmula científica fixa
NDVI = (NIR - Red) / (NIR + Red)
SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)
```

**Características:**
- ✅ Sem estado (stateless)
- ✅ Sem regras de negócio
- ✅ Apenas matemática pura
- ✅ Iguais para todos os tenants

---

### 1.2 Regras/Alertas Personalizados - Camada de Aplicação/Domínio

**O que são:**
- Inteligência de negócio aplicada sobre indicadores brutos
- Regras configuráveis por tenant/usuário
- Condições lógicas complexas
- **PODEM mudar** (criadas/editadas por admins)

**Responsável:**
- `RuleEngine` (Domain Service)
- `CustomRule` (Domain Entity)
- `Alert` (Domain Entity)

**Exemplo:**
```python
# Regra personalizada - Configurável
IF NDVI < 0.3 AND days_consecutive >= 7 THEN
  CREATE ALERT "Risco de Seca - Irrigação Recomendada"

IF NDVI > 0.7 AND crop.status == "growing" AND days_until_harvest <= 14 THEN
  CREATE ALERT "Ponto Ótimo de Colheita em 2 Semanas"

IF correlation(NDVI, precipitation) < 0.3 AND nitrogen_applied == False THEN
  CREATE ALERT "Aplicar Nitrogênio - Baixa Correlação com Chuva"
```

**Características:**
- ✅ Com estado (stateful) - depende de histórico
- ✅ Regras de negócio complexas
- ✅ Configuráveis por tenant
- ✅ Armazenadas no banco de dados

---

## 2. Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (Admin Panel)                                          │
│ - UI para criar/editar regras customizadas                      │
│ - Drag-and-drop rule builder                                    │
│ - Preview de alertas                                            │
└─────────────────────────────────────────────────────────────────┘
                              ▼
                     HTTP Request (JSON)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER (FastAPI Routers)                            │
│ /api/indices         → Retorna indicadores brutos (NDVI, etc.)  │
│ /api/alerts          → Retorna alertas calculados               │
│ /api/admin/rules     → CRUD de regras customizadas              │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ APPLICATION LAYER (Use Cases)                                   │
│ CalculateIndicesUseCase    → Calcula NDVI, SAVI, etc.           │
│ EvaluateRulesUseCase       → Aplica regras e gera alertas       │
│ CreateCustomRuleUseCase    → Admin cria nova regra              │
│ UpdateCustomRuleUseCase    → Admin edita regra                  │
│ DeleteCustomRuleUseCase    → Admin remove regra                 │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ DOMAIN LAYER (Entities, Services)                               │
│                                                                  │
│ VegetationCalculatorService                                     │
│ ├── calculate_ndvi()       → Cálculo puro                       │
│ ├── calculate_savi()       → Cálculo puro                       │
│ └── calculate_evi()        → Cálculo puro                       │
│                                                                  │
│ RuleEngine (Domain Service)                                     │
│ ├── evaluate_rule()        → Avalia regra customizada           │
│ ├── check_condition()      → Verifica condições                 │
│ └── create_alert()         → Cria alerta se regra ativada       │
│                                                                  │
│ CustomRule (Entity - Configurável)                              │
│ ├── id, tenant_id, name                                         │
│ ├── conditions (JSON)      → Lógica da regra                    │
│ ├── alert_template         → Template do alerta                 │
│ └── is_active              → Habilitado/Desabilitado            │
│                                                                  │
│ Alert (Entity - Gerado)                                         │
│ ├── id, tenant_id, rule_id                                      │
│ ├── severity               → info/warning/critical              │
│ ├── message                → Mensagem do alerta                 │
│ └── triggered_at           → Quando foi gerado                  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER (Repositories)                             │
│ CustomRuleRepository       → Persiste regras no PostgreSQL      │
│ AlertRepository            → Persiste alertas no PostgreSQL     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementação Detalhada

### 3.1 Domain Entities

#### CustomRule Entity (Regra Configurável)

```python
# services/api/app/domain/entities/custom_rule.py

from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID, uuid4
from enum import Enum
from typing import Dict, Any, List

class RuleConditionOperator(str, Enum):
    """Operadores de comparação"""
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    EQUAL = "eq"
    NOT_EQUAL = "ne"

class AlertSeverity(str, Enum):
    """Severidade do alerta"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class RuleCondition(BaseModel):
    """
    Condição individual de uma regra.

    Exemplo:
    {
        "metric": "ndvi",
        "operator": "lt",
        "value": 0.3,
        "aggregation": "mean",  # mean, min, max, last
        "time_window_days": 7
    }
    """
    metric: str = Field(..., description="Nome do indicador (ndvi, ndwi, savi)")
    operator: RuleConditionOperator
    value: float = Field(..., description="Valor de comparação")
    aggregation: str = Field(default="mean", pattern="^(mean|min|max|last)$")
    time_window_days: int = Field(default=1, ge=1, le=365)

    model_config = ConfigDict(frozen=True)

class CustomRule(BaseModel):
    """
    Domain Entity - Regra customizável criada pelo admin.

    Regras são avaliadas pelo RuleEngine e geram Alertas quando ativadas.
    """
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(max_length=500)

    # Condições da regra (AND lógico entre condições)
    conditions: List[RuleCondition] = Field(min_length=1)

    # Template do alerta gerado
    alert_severity: AlertSeverity
    alert_template: str = Field(
        max_length=500,
        description="Template com variáveis: {field_name}, {ndvi_value}, etc."
    )

    # Configurações
    is_active: bool = Field(default=True)
    apply_to_all_fields: bool = Field(
        default=False,
        description="Se True, aplica a todos os campos do tenant"
    )
    field_ids: List[UUID] = Field(
        default_factory=list,
        description="Se apply_to_all_fields=False, lista de field_ids específicos"
    )

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid"
    )

    @field_validator('conditions')
    @classmethod
    def validate_conditions(cls, v: List[RuleCondition]) -> List[RuleCondition]:
        """Validar que há pelo menos uma condição"""
        if not v:
            raise ValueError("Regra deve ter pelo menos uma condição")
        return v

    @field_validator('field_ids')
    @classmethod
    def validate_field_ids(cls, v: List[UUID], info) -> List[UUID]:
        """Se não aplica a todos, deve ter field_ids"""
        if 'apply_to_all_fields' in info.data:
            apply_to_all = info.data['apply_to_all_fields']
            if not apply_to_all and not v:
                raise ValueError(
                    "Deve especificar field_ids ou apply_to_all_fields=True"
                )
        return v
```

#### Alert Entity (Alerta Gerado)

```python
# services/api/app/domain/entities/alert.py

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

class AlertStatus(str, Enum):
    """Status do alerta"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class Alert(BaseModel):
    """
    Domain Entity - Alerta gerado por uma regra customizada.

    Alertas são criados pelo RuleEngine quando condições são satisfeitas.
    """
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    rule_id: UUID
    field_id: UUID

    # Conteúdo do alerta
    severity: AlertSeverity
    message: str = Field(max_length=500)

    # Metadados
    metric_values: dict = Field(
        default_factory=dict,
        description="Valores dos indicadores que ativaram a regra"
    )

    # Status
    status: AlertStatus = Field(default=AlertStatus.ACTIVE)
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        extra="forbid"
    )

    def acknowledge(self) -> None:
        """Marcar alerta como reconhecido"""
        if self.status != AlertStatus.ACTIVE:
            raise ValueError(f"Cannot acknowledge alert in status: {self.status}")
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()

    def resolve(self) -> None:
        """Marcar alerta como resolvido"""
        if self.status == AlertStatus.RESOLVED:
            raise ValueError("Alert already resolved")
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
```

---

### 3.2 Domain Service: RuleEngine

```python
# services/api/app/domain/services/rule_engine.py

from typing import List, Dict
import numpy as np
from datetime import datetime, timedelta

from app.domain.entities.custom_rule import (
    CustomRule,
    RuleCondition,
    RuleConditionOperator
)
from app.domain.entities.alert import Alert, AlertSeverity

class RuleEngine:
    """
    Domain Service - Avalia regras customizadas e gera alertas.

    Puro: Sem dependências externas, apenas lógica de domínio.
    """

    def evaluate_rule(
        self,
        rule: CustomRule,
        field_id: UUID,
        time_series_data: Dict[str, List[tuple[datetime, float]]]
    ) -> Alert | None:
        """
        Avalia uma regra customizada para um campo específico.

        Args:
            rule: Regra a avaliar
            field_id: ID do campo
            time_series_data: Dados de séries temporais por métrica
                              {"ndvi": [(date1, 0.5), (date2, 0.6), ...], ...}

        Returns:
            Alert se regra ativada, None caso contrário
        """
        # Verificar se regra está ativa
        if not rule.is_active:
            return None

        # Verificar se aplica a este campo
        if not rule.apply_to_all_fields:
            if field_id not in rule.field_ids:
                return None

        # Avaliar todas as condições (AND lógico)
        metric_values = {}
        all_conditions_met = True

        for condition in rule.conditions:
            condition_met, value = self._evaluate_condition(
                condition,
                time_series_data
            )

            metric_values[condition.metric] = value

            if not condition_met:
                all_conditions_met = False
                break

        # Se todas as condições satisfeitas, criar alerta
        if all_conditions_met:
            message = self._render_alert_message(
                rule.alert_template,
                field_id,
                metric_values
            )

            return Alert(
                tenant_id=rule.tenant_id,
                rule_id=rule.id,
                field_id=field_id,
                severity=rule.alert_severity,
                message=message,
                metric_values=metric_values
            )

        return None

    def _evaluate_condition(
        self,
        condition: RuleCondition,
        time_series_data: Dict[str, List[tuple[datetime, float]]]
    ) -> tuple[bool, float]:
        """
        Avalia uma condição individual.

        Returns:
            (condition_met, aggregated_value)
        """
        # Obter dados da métrica
        if condition.metric not in time_series_data:
            return False, 0.0

        metric_data = time_series_data[condition.metric]

        # Filtrar por janela de tempo
        cutoff_date = datetime.utcnow() - timedelta(days=condition.time_window_days)
        recent_data = [
            value for date, value in metric_data
            if date >= cutoff_date
        ]

        if not recent_data:
            return False, 0.0

        # Agregar dados
        if condition.aggregation == "mean":
            aggregated_value = float(np.mean(recent_data))
        elif condition.aggregation == "min":
            aggregated_value = float(np.min(recent_data))
        elif condition.aggregation == "max":
            aggregated_value = float(np.max(recent_data))
        elif condition.aggregation == "last":
            aggregated_value = recent_data[-1]
        else:
            aggregated_value = float(np.mean(recent_data))

        # Comparar com threshold
        condition_met = self._compare(
            aggregated_value,
            condition.operator,
            condition.value
        )

        return condition_met, aggregated_value

    def _compare(
        self,
        value: float,
        operator: RuleConditionOperator,
        threshold: float
    ) -> bool:
        """Compara valor com threshold usando operador"""
        if operator == RuleConditionOperator.LESS_THAN:
            return value < threshold
        elif operator == RuleConditionOperator.LESS_THAN_OR_EQUAL:
            return value <= threshold
        elif operator == RuleConditionOperator.GREATER_THAN:
            return value > threshold
        elif operator == RuleConditionOperator.GREATER_THAN_OR_EQUAL:
            return value >= threshold
        elif operator == RuleConditionOperator.EQUAL:
            return abs(value - threshold) < 1e-6
        elif operator == RuleConditionOperator.NOT_EQUAL:
            return abs(value - threshold) >= 1e-6
        else:
            return False

    def _render_alert_message(
        self,
        template: str,
        field_id: UUID,
        metric_values: Dict[str, float]
    ) -> str:
        """
        Renderiza template do alerta com valores reais.

        Template: "NDVI médio ({ndvi}) abaixo de 0.3 por 7 dias"
        Resultado: "NDVI médio (0.25) abaixo de 0.3 por 7 dias"
        """
        message = template
        message = message.replace("{field_id}", str(field_id))

        for metric, value in metric_values.items():
            message = message.replace(f"{{{metric}}}", f"{value:.2f}")

        return message
```

---

### 3.3 Application Layer: Use Cases

#### CreateCustomRuleUseCase

```python
# services/api/app/application/use_cases/create_custom_rule.py

from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import List

from app.domain.entities.custom_rule import (
    CustomRule,
    RuleCondition,
    AlertSeverity
)
from app.domain.repositories.custom_rule_repository import ICustomRuleRepository

class CreateCustomRuleCommand(BaseModel):
    """Command para criar regra customizada"""
    tenant_id: UUID
    name: str
    description: str
    conditions: List[RuleCondition]
    alert_severity: AlertSeverity
    alert_template: str
    apply_to_all_fields: bool = False
    field_ids: List[UUID] = []

    model_config = ConfigDict(frozen=True)

class CreateCustomRuleUseCase:
    """Use Case - Admin cria nova regra customizada"""

    def __init__(self, rule_repository: ICustomRuleRepository):
        self.rule_repository = rule_repository

    async def execute(self, command: CreateCustomRuleCommand) -> CustomRule:
        """
        Cria nova regra customizada.

        Raises:
            DuplicateRuleNameError: Se já existe regra com mesmo nome
        """
        # Verificar se já existe regra com mesmo nome
        existing = await self.rule_repository.find_by_name(
            command.name,
            command.tenant_id
        )

        if existing:
            raise DuplicateRuleNameError(
                f"Rule '{command.name}' already exists for this tenant"
            )

        # Criar domain entity
        rule = CustomRule(
            tenant_id=command.tenant_id,
            name=command.name,
            description=command.description,
            conditions=command.conditions,
            alert_severity=command.alert_severity,
            alert_template=command.alert_template,
            is_active=True,
            apply_to_all_fields=command.apply_to_all_fields,
            field_ids=command.field_ids
        )

        # Persistir
        saved_rule = await self.rule_repository.save(rule)

        return saved_rule
```

#### EvaluateRulesUseCase

```python
# services/api/app/application/use_cases/evaluate_rules.py

from typing import List
from uuid import UUID

from app.domain.entities.custom_rule import CustomRule
from app.domain.entities.alert import Alert
from app.domain.services.rule_engine import RuleEngine
from app.domain.repositories.custom_rule_repository import ICustomRuleRepository
from app.domain.repositories.alert_repository import IAlertRepository
from app.domain.repositories.field_repository import IFieldRepository
from app.infrastructure.adapters.time_series.time_series_provider import ITimeSeriesProvider

class EvaluateRulesUseCase:
    """
    Use Case - Avalia todas as regras ativas e gera alertas.

    Executado periodicamente (ex: daily cron job).
    """

    def __init__(
        self,
        rule_repository: ICustomRuleRepository,
        alert_repository: IAlertRepository,
        field_repository: IFieldRepository,
        time_series_provider: ITimeSeriesProvider,
        rule_engine: RuleEngine
    ):
        self.rule_repository = rule_repository
        self.alert_repository = alert_repository
        self.field_repository = field_repository
        self.time_series_provider = time_series_provider
        self.rule_engine = rule_engine

    async def execute(self, tenant_id: UUID) -> List[Alert]:
        """
        Avalia todas as regras para um tenant.

        Returns:
            Lista de alertas gerados
        """
        # 1. Buscar todas as regras ativas do tenant
        active_rules = await self.rule_repository.list_active(tenant_id)

        if not active_rules:
            return []

        # 2. Buscar todos os campos do tenant
        fields = await self.field_repository.list_by_tenant(tenant_id)

        # 3. Avaliar cada regra para cada campo
        new_alerts = []

        for rule in active_rules:
            for field in fields:
                # Buscar dados de séries temporais para este campo
                time_series_data = await self.time_series_provider.get_time_series(
                    field_id=field.id,
                    metrics=self._extract_metrics_from_rule(rule),
                    days=self._get_max_time_window(rule)
                )

                # Avaliar regra
                alert = self.rule_engine.evaluate_rule(
                    rule=rule,
                    field_id=field.id,
                    time_series_data=time_series_data
                )

                # Se alerta gerado, salvar
                if alert:
                    # Verificar se já não existe alerta ativo para esta regra+campo
                    existing_alert = await self.alert_repository.find_active(
                        rule_id=rule.id,
                        field_id=field.id
                    )

                    if not existing_alert:
                        saved_alert = await self.alert_repository.save(alert)
                        new_alerts.append(saved_alert)

        return new_alerts

    def _extract_metrics_from_rule(self, rule: CustomRule) -> List[str]:
        """Extrai nomes das métricas usadas na regra"""
        return list(set(c.metric for c in rule.conditions))

    def _get_max_time_window(self, rule: CustomRule) -> int:
        """Retorna maior janela de tempo usada na regra"""
        return max(c.time_window_days for c in rule.conditions)
```

---

### 3.4 Presentation Layer: Admin API

```python
# services/api/app/presentation/routers/admin/custom_rules_router.py

from fastapi import APIRouter, Depends, status
from uuid import UUID
from typing import List, Annotated

from app.presentation.dependencies import (
    get_current_tenant_id,
    get_create_custom_rule_use_case,
    get_update_custom_rule_use_case,
    get_delete_custom_rule_use_case
)
from app.presentation.dtos.custom_rule_dtos import (
    CreateCustomRuleRequestDTO,
    UpdateCustomRuleRequestDTO,
    CustomRuleResponseDTO
)
from app.application.use_cases.create_custom_rule import (
    CreateCustomRuleUseCase,
    CreateCustomRuleCommand
)

router = APIRouter(prefix="/admin/rules", tags=["admin-rules"])

@router.post(
    "/",
    response_model=CustomRuleResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom rule (Admin only)"
)
async def create_custom_rule(
    request: CreateCustomRuleRequestDTO,
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)],
    use_case: Annotated[CreateCustomRuleUseCase, Depends(get_create_custom_rule_use_case)]
):
    """
    Create a custom alerting rule.

    Admins can create rules with custom conditions and alert templates.

    Example rule:
    - Name: "Drought Risk Alert"
    - Condition: NDVI < 0.3 for 7 days (mean)
    - Alert: "Irrigation recommended - NDVI ({ndvi}) below threshold"
    """
    command = CreateCustomRuleCommand(
        tenant_id=tenant_id,
        name=request.name,
        description=request.description,
        conditions=request.conditions,
        alert_severity=request.alert_severity,
        alert_template=request.alert_template,
        apply_to_all_fields=request.apply_to_all_fields,
        field_ids=request.field_ids
    )

    rule = await use_case.execute(command)

    return CustomRuleResponseDTO.from_domain(rule)

@router.get(
    "/",
    response_model=List[CustomRuleResponseDTO],
    summary="List all custom rules"
)
async def list_custom_rules(
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)],
    is_active: bool | None = None
):
    """List all custom rules for tenant"""
    # Implementation...
    pass

@router.get(
    "/{rule_id}",
    response_model=CustomRuleResponseDTO,
    summary="Get custom rule by ID"
)
async def get_custom_rule(
    rule_id: UUID,
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)]
):
    """Get specific custom rule"""
    # Implementation...
    pass

@router.put(
    "/{rule_id}",
    response_model=CustomRuleResponseDTO,
    summary="Update custom rule"
)
async def update_custom_rule(
    rule_id: UUID,
    request: UpdateCustomRuleRequestDTO,
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)]
):
    """Update custom rule"""
    # Implementation...
    pass

@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete custom rule"
)
async def delete_custom_rule(
    rule_id: UUID,
    tenant_id: Annotated[UUID, Depends(get_current_tenant_id)]
):
    """Delete custom rule"""
    # Implementation...
    pass
```

---

## 4. Frontend: Admin Rule Builder

### 4.1 Componente React para Criar Regras

```typescript
// services/admin-ui/src/components/RuleBuilder.tsx

import { useState } from 'react';
import type { CustomRule, RuleCondition } from '@/lib/types';

interface RuleBuilderProps {
  onSave: (rule: CustomRule) => Promise<void>;
}

export function RuleBuilder({ onSave }: RuleBuilderProps) {
  const [ruleName, setRuleName] = useState('');
  const [description, setDescription] = useState('');
  const [conditions, setConditions] = useState<RuleCondition[]>([]);
  const [alertSeverity, setAlertSeverity] = useState<'info' | 'warning' | 'critical'>('warning');
  const [alertTemplate, setAlertTemplate] = useState('');

  const addCondition = () => {
    setConditions([
      ...conditions,
      {
        metric: 'ndvi',
        operator: 'lt',
        value: 0.3,
        aggregation: 'mean',
        time_window_days: 7
      }
    ]);
  };

  const handleSubmit = async () => {
    const rule: CustomRule = {
      name: ruleName,
      description,
      conditions,
      alert_severity: alertSeverity,
      alert_template: alertTemplate,
      apply_to_all_fields: true,
      field_ids: []
    };

    await onSave(rule);
  };

  return (
    <div className="rule-builder">
      <h2>Create Custom Alert Rule</h2>

      {/* Rule Name */}
      <div>
        <label>Rule Name</label>
        <input
          type="text"
          value={ruleName}
          onChange={(e) => setRuleName(e.target.value)}
          placeholder="Drought Risk Alert"
        />
      </div>

      {/* Description */}
      <div>
        <label>Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Alert when NDVI indicates drought risk"
        />
      </div>

      {/* Conditions */}
      <div className="conditions">
        <h3>Conditions (AND logic)</h3>

        {conditions.map((condition, index) => (
          <div key={index} className="condition">
            {/* Metric Select */}
            <select
              value={condition.metric}
              onChange={(e) => {
                const updated = [...conditions];
                updated[index].metric = e.target.value;
                setConditions(updated);
              }}
            >
              <option value="ndvi">NDVI</option>
              <option value="ndwi">NDWI</option>
              <option value="savi">SAVI</option>
              <option value="evi">EVI</option>
            </select>

            {/* Operator Select */}
            <select
              value={condition.operator}
              onChange={(e) => {
                const updated = [...conditions];
                updated[index].operator = e.target.value as any;
                setConditions(updated);
              }}
            >
              <option value="lt">&lt; (less than)</option>
              <option value="lte">&lt;= (less than or equal)</option>
              <option value="gt">&gt; (greater than)</option>
              <option value="gte">&gt;= (greater than or equal)</option>
              <option value="eq">= (equal)</option>
            </select>

            {/* Value Input */}
            <input
              type="number"
              step="0.01"
              value={condition.value}
              onChange={(e) => {
                const updated = [...conditions];
                updated[index].value = parseFloat(e.target.value);
                setConditions(updated);
              }}
            />

            {/* Aggregation */}
            <select
              value={condition.aggregation}
              onChange={(e) => {
                const updated = [...conditions];
                updated[index].aggregation = e.target.value;
                setConditions(updated);
              }}
            >
              <option value="mean">Mean</option>
              <option value="min">Min</option>
              <option value="max">Max</option>
              <option value="last">Last</option>
            </select>

            {/* Time Window */}
            <input
              type="number"
              min="1"
              max="365"
              value={condition.time_window_days}
              onChange={(e) => {
                const updated = [...conditions];
                updated[index].time_window_days = parseInt(e.target.value);
                setConditions(updated);
              }}
            />
            <span>days</span>

            {/* Remove Button */}
            <button
              onClick={() => setConditions(conditions.filter((_, i) => i !== index))}
            >
              Remove
            </button>
          </div>
        ))}

        <button onClick={addCondition}>+ Add Condition</button>
      </div>

      {/* Alert Configuration */}
      <div>
        <label>Alert Severity</label>
        <select
          value={alertSeverity}
          onChange={(e) => setAlertSeverity(e.target.value as any)}
        >
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      <div>
        <label>Alert Message Template</label>
        <textarea
          value={alertTemplate}
          onChange={(e) => setAlertTemplate(e.target.value)}
          placeholder="NDVI ({ndvi}) below 0.3 for 7 days - Irrigation recommended"
        />
        <small>Use {'{metric_name}'} for variable substitution</small>
      </div>

      {/* Preview */}
      <div className="preview">
        <h3>Preview</h3>
        <pre>{JSON.stringify({ ruleName, conditions, alertTemplate }, null, 2)}</pre>
      </div>

      {/* Submit */}
      <button onClick={handleSubmit}>Create Rule</button>
    </div>
  );
}
```

---

## 5. Exemplos de Regras Customizadas

### Exemplo 1: Alerta de Seca

```json
{
  "name": "Drought Risk Alert",
  "description": "Alert when NDVI indicates prolonged drought",
  "conditions": [
    {
      "metric": "ndvi",
      "operator": "lt",
      "value": 0.3,
      "aggregation": "mean",
      "time_window_days": 7
    }
  ],
  "alert_severity": "critical",
  "alert_template": "Drought risk detected - NDVI ({ndvi}) below 0.3 for 7 days. Irrigation strongly recommended.",
  "apply_to_all_fields": true
}
```

### Exemplo 2: Ponto Ótimo de Colheita

```json
{
  "name": "Optimal Harvest Point",
  "description": "Alert when NDVI indicates optimal harvest point",
  "conditions": [
    {
      "metric": "ndvi",
      "operator": "gte",
      "value": 0.7,
      "aggregation": "mean",
      "time_window_days": 3
    },
    {
      "metric": "ndvi",
      "operator": "lt",
      "value": 0.75,
      "aggregation": "max",
      "time_window_days": 3
    }
  ],
  "alert_severity": "info",
  "alert_template": "Optimal harvest point detected - NDVI stable at {ndvi}. Consider harvesting within 2 weeks.",
  "apply_to_all_fields": false,
  "field_ids": ["uuid-field-1", "uuid-field-2"]
}
```

### Exemplo 3: Déficit de Nitrogênio

```json
{
  "name": "Nitrogen Deficiency Alert",
  "description": "Alert when low NDVI suggests nitrogen deficiency",
  "conditions": [
    {
      "metric": "ndvi",
      "operator": "lt",
      "value": 0.5,
      "aggregation": "mean",
      "time_window_days": 14
    },
    {
      "metric": "ndwi",
      "operator": "gt",
      "value": 0.1,
      "aggregation": "mean",
      "time_window_days": 14
    }
  ],
  "alert_severity": "warning",
  "alert_template": "Potential nitrogen deficiency - NDVI ({ndvi}) low while water availability adequate (NDWI {ndwi}). Consider nitrogen application.",
  "apply_to_all_fields": true
}
```

---

## 6. Benefícios da Separação

### 6.1 Para o Sistema

✅ **Escalabilidade**: Regras armazenadas no DB, não em código
✅ **Flexibilidade**: Admins criam regras sem deploy
✅ **Manutenibilidade**: Indicadores brutos (científicos) separados de regras (negócio)
✅ **Testabilidade**: Domain Services testáveis independentemente

### 6.2 Para o Negócio

✅ **Personalização**: Cada tenant pode ter regras diferentes
✅ **Agilidade**: Criar nova regra em minutos, não semanas
✅ **Experimentação**: Testar regras sem afetar código
✅ **Evolução**: Aprender com dados e ajustar regras

### 6.3 Para os Usuários

✅ **Relevância**: Alertas personalizados para suas necessidades
✅ **Controle**: Admin define o que é importante
✅ **Clareza**: Mensagens customizadas, não genéricas

---

## 7. Roadmap de Implementação

### Fase 1: Fundação (2-3 semanas)
- [ ] Criar domain entities (CustomRule, Alert)
- [ ] Criar RuleEngine (Domain Service)
- [ ] Criar repositories (CustomRuleRepository, AlertRepository)
- [ ] Testes unitários

### Fase 2: Application Layer (1-2 semanas)
- [ ] CreateCustomRuleUseCase
- [ ] EvaluateRulesUseCase
- [ ] UpdateCustomRuleUseCase
- [ ] DeleteCustomRuleUseCase

### Fase 3: Presentation Layer (1-2 semanas)
- [ ] Admin API endpoints (/admin/rules)
- [ ] User API endpoints (/alerts)
- [ ] DTOs de request/response

### Fase 4: Frontend (2-3 semanas)
- [ ] Admin Rule Builder UI
- [ ] Alert Dashboard
- [ ] Rule preview/testing

### Fase 5: Automação (1 semana)
- [ ] Cron job para avaliar regras (daily)
- [ ] Notificações (email, push, webhook)

---

## 8. Resumo Executivo

**Separação recomendada:**

| Tipo | Responsável | Onde | Configurável |
|------|------------|------|--------------|
| **Indicadores Brutos** | VegetationCalculatorService | Domain Layer | ❌ Fixo (científico) |
| **Regras Customizadas** | RuleEngine + CustomRule | Domain/Application | ✅ Admin via UI |
| **Alertas Gerados** | Alert | Domain Layer | ✅ Template customizável |

**Admin pode:**
- ✅ Criar regras via UI (drag-and-drop)
- ✅ Definir condições (NDVI < 0.3 por 7 dias)
- ✅ Customizar mensagens de alerta
- ✅ Ativar/desativar regras
- ✅ Aplicar a campos específicos ou todos

**Sistema faz:**
- ✅ Calcula indicadores brutos (NDVI, SAVI, etc.)
- ✅ Avalia regras periodicamente (cron job)
- ✅ Gera alertas automaticamente
- ✅ Notifica usuários

**Resultado**: Sistema flexível, escalável e personalizável! 🎯
