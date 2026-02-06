# Scripts de Validação - Arquitetura Hexagonal

Este diretório contém **agentes validadores** que garantem que o código segue os padrões da arquitetura hexagonal.

## Validadores Disponíveis

### 1. Architecture Validator

Valida que código respeita a arquitetura hexagonal (camadas e dependências).

```bash
python scripts/validate_architecture.py
```

**Verifica:**
- ✅ Domain layer não importa Infrastructure/Application/Presentation
- ✅ Application layer não importa Presentation
- ✅ Pydantic entities têm `validate_assignment=True`
- ✅ Pydantic DTOs têm `frozen=True` (imutáveis)
- ✅ Direção de dependências correta

**Exemplo de Output:**
```
🔍 Validando arquitetura hexagonal...

❌ ERRORS (2):

  services/api/app/domain/entities/farm.py:15
    Layer: domain
    Forbidden import: domain layer cannot import 'sqlalchemy'

  services/api/app/domain/entities/farm.py:23
    Layer: domain
    Domain entity 'Farm' missing validate_assignment=True

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 2 errors, 0 warnings
```

---

### 2. Security Validator

Valida segurança multi-tenant e prevenção de SQL injection.

```bash
python scripts/validate_security.py
```

**Verifica:**
- ✅ Repositories filtram por `tenant_id`
- ✅ Use Cases validam `tenant_id` do command
- ✅ Presentation layer extrai `tenant_id` do JWT
- ✅ Queries SQL usam parameterização (previne SQL injection)
- ✅ Nenhum string concatenation em queries

**Exemplo de Output:**
```
🔐 Validando segurança multi-tenant...

🚨 CRITICAL (1):

  services/api/app/infrastructure/repositories/farm_repository.py:42
    Category: multi-tenant
    Repository method 'find_by_id' has WHERE clause but doesn't filter by tenant_id

❌ HIGH (1):

  services/api/app/application/use_cases/create_farm.py:28
    Category: multi-tenant
    Use case 'CreateFarmUseCase' doesn't use tenant_id from command

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 1 critical, 1 high, 0 medium, 0 low
```

---

### 3. Master Validator (Todos Juntos)

Executa **todos os validadores** em sequência.

```bash
# Executar todos
python scripts/validate_all.py

# Com output verbose
python scripts/validate_all.py --verbose

# Modo strict (falha em warnings)
python scripts/validate_all.py --strict
```

**Exemplo de Output:**
```
============================================================
VivaCampo - Master Validator
============================================================

────────────────────────────────────────────────────────────
Running Architecture Validator...

✅ Architecture Validator PASSED (1.23s)

────────────────────────────────────────────────────────────
Running Security Validator...

✅ Security Validator PASSED (0.87s)

============================================================
SUMMARY
============================================================

  Architecture         ✅ PASSED            (1.23s)
  Security             ✅ PASSED            (0.87s)

Total: 2 validators
Passed: 2
Failed: 0
Duration: 2.10s

============================================================
✅ ALL VALIDATIONS PASSED!
============================================================
```

---

## Integração com CI/CD

### GitHub Actions

O arquivo [`.github/workflows/validate-architecture.yml`](../.github/workflows/validate-architecture.yml) executa os validadores automaticamente em cada push/PR.

**Workflow inclui:**
1. Architecture Validator
2. Security Validator
3. Master Validator (todos juntos)
4. Upload de artefatos (resultados)

**Status do Workflow:**

Para adicionar badge ao README principal:

```markdown
[![Architecture Validation](https://github.com/seu-usuario/vivacampo-app/actions/workflows/validate-architecture.yml/badge.svg)](https://github.com/seu-usuario/vivacampo-app/actions/workflows/validate-architecture.yml)
```

---

## Pre-commit Hook (Opcional)

Adicionar validação antes de cada commit:

**Criar arquivo `.git/hooks/pre-commit`:**

```bash
#!/bin/bash

echo "Running architecture validators..."

# Executar validadores
python scripts/validate_all.py

# Se falhar, bloquear commit
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Commit blocked: Fix architecture violations first"
    exit 1
fi

echo "✅ Validations passed, proceeding with commit"
exit 0
```

**Tornar executável:**

```bash
chmod +x .git/hooks/pre-commit
```

---

## Roadmap de Validadores Futuros

### 3. Contract Validator (Planejado)

Valida contratos Pydantic (DTOs, Commands, Responses).

```bash
python scripts/validate_contracts.py
```

**Verificará:**
- ✅ Request DTOs têm `frozen=True`
- ✅ Response DTOs têm método `from_domain()`
- ✅ Commands têm `frozen=True`
- ✅ Campos têm validators apropriados
- ✅ DTOs seguem convenção de nomes (`*RequestDTO`, `*ResponseDTO`, `*Command`)

---

### 4. Test Coverage Validator (Planejado)

Valida cobertura de testes.

```bash
python scripts/validate_test_coverage.py
```

**Verificará:**
- ✅ Domain Services têm 100% cobertura
- ✅ Use Cases têm testes de integração
- ✅ Repositories têm testes com DB real (Testcontainers)
- ✅ Adapters têm testes com fallback mechanisms
- ✅ Presentation routers têm testes E2E

---

### 5. Documentation Validator (Planejado)

Valida que documentação está atualizada.

```bash
python scripts/validate_documentation.py
```

**Verificará:**
- ✅ Novos indicadores documentados em `INDICATORS_AND_FRONTEND_INTEGRATION.md`
- ✅ Novos use cases listados em `HEXAGONAL_ARCHITECTURE_PLAN.md`
- ✅ Docstrings presentes em domain services
- ✅ OpenAPI schemas atualizados (FastAPI)

---

## Uso Durante Desenvolvimento

### Ao Adicionar Nova Feature

```bash
# 1. Implementar feature seguindo padrões
# 2. Antes de commitar, validar
python scripts/validate_all.py

# 3. Se falhar, corrigir violações
# 4. Validar novamente
python scripts/validate_all.py

# 5. Commit quando tudo passar
git commit -m "Add new feature"
```

### Ao Migrar Código Anterior

```bash
# 1. Migrar código para arquitetura hexagonal
# 2. Validar arquitetura
python scripts/validate_architecture.py

# 3. Validar segurança multi-tenant
python scripts/validate_security.py

# 4. Se tudo passar, remover código anterior
# 5. Commit
git commit -m "Migrate prior code to hexagonal architecture"
```

---

## Troubleshooting

### Erro: "Module not found"

Instalar dependências:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Falsos Positivos

Se validador reportar falso positivo, abrir issue:

```bash
# Reportar problema
echo "File: path/to/file.py
Line: 42
Validator: Architecture
Issue: False positive for ..." > validation-issue.txt
```

### Desabilitar Validação Temporária

Para desenvolvimento local (não recomendado):

```bash
# Pular validação (NÃO FAZER NO CI/CD)
git commit --no-verify -m "WIP: temporary commit"
```

---

## Contribuindo com Novos Validadores

Para adicionar novo validador:

1. Criar script `validate_<nome>.py`
2. Seguir estrutura:
   ```python
   class <Nome>Validator:
       def __init__(self, project_root: Path):
           ...

       def validate(self) -> bool:
           ...

       def _report_results(self) -> bool:
           ...
   ```
3. Adicionar ao `validate_all.py`
4. Adicionar ao workflow GitHub Actions
5. Documentar neste README

---

## Referências

- [AI_AGENTS_ARCHITECTURE.md](../ai/AI_AGENTS_ARCHITECTURE.md) - Arquitetura completa de agentes
- [HEXAGONAL_ARCHITECTURE_PLAN.md](../ai/HEXAGONAL_ARCHITECTURE_PLAN.md) - Plano de migração
- [INDICATORS_AND_FRONTEND_INTEGRATION.md](../ai/INDICATORS_AND_FRONTEND_INTEGRATION.md) - Integração frontend

---

## Suporte

Para problemas com validadores, abrir issue no GitHub ou contatar time de arquitetura.
