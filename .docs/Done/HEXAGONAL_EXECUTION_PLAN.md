# Plano de Execucao: Arquitetura Hexagonal (Conciliado com o Plano Original)

Data: 2026-02-05
Status: Plano encerrado (pendencias migradas para `ai/tasks.md`)

## Objetivo
Executar a migracao para arquitetura hexagonal (Ports & Adapters) com:
- Validacao Pydantic em 5 camadas (HTTP -> Presentation -> Application -> Domain -> Infrastructure)
- Fallbacks automaticos e circuit breaker para resiliencia
- Testes com infraestrutura real (LocalStack)
- Isolamento multi-tenant garantido em todas as camadas

---

## Plano por Fase (Entregaveis, Contratos, Testes, Riscos)

### Fase 1 — Domain Layer (Ports & Entities)
Objetivo: criar camada de dominio pura com entidades/VOs e ports, validacao Pydantic e base comum.

Detalhes de implementacao (granular):
- Criar `services/api/app/domain/base.py` com `DomainEntity` e `ImmutableDTO`
- Criar estrutura de diretorios e `__init__.py`
- Criar entidades iniciais (ex: `farm.py`, `aoi.py`) com validators
- Criar ports iniciais (ex: message queue, object storage, repositories)
- Espelhar estrutura equivalente no worker (domain + ports)

Entregaveis:
- `services/api/app/domain/base.py` com `DomainEntity` e `ImmutableDTO` (Pydantic)
- Estrutura de diretorios `services/api/app/domain/*` e `services/worker/worker/domain/*` com `__init__.py`
- Entidades iniciais em `services/api/app/domain/entities/` (ex: `farm.py`, `aoi.py`) com validacoes
- Ports iniciais (ex: `message_queue.py`, `object_storage.py`) e ports do worker (ex: `satellite_provider.py`)
- Configuracao Pydantic global (strict, validate_assignment, extra=forbid)

Contratos afetados:
- Domain (novos tipos e validacao)

Testes:
- Unitarios em `tests/unit/domain/` cobrindo criacao e update com validacao

Riscos:
- Divergencia entre validacoes do domain e schemas atuais. Precisa alinhar regras para evitar quebra

Checklist de implementacao:
- [x] Criar `services/api/app/domain/base.py`
- [x] Criar diretorios + `__init__.py` em API e Worker
- [x] Implementar `Farm` com validators e `update_*` methods
- [x] Implementar `AOI` com validators (WKT, area_ha)
- [x] Criar ports iniciais (queue, storage, farm repo)
- [x] Criar ports iniciais do worker (satellite provider)
- [x] Testes unitarios de validacao (criacao e update)
- [x] Validar imports sem framework (domain puro)

---

### Fase 2 — Infrastructure Layer (Adapters)
Objetivo: implementar adapters concretos e resilientes, com validacao Pydantic de dados externos.

Detalhes de implementacao (granular):
- Criar adapters SQS/S3 com retry/backoff
- Criar adapter resiliente de satelite com fallback chain
- Implementar validacao Pydantic para payloads de APIs externas
- Adicionar circuit breaker nos adapters criticos

Entregaveis:
- Adapters concretos para SQS, storage e satellite provider resiliente
- Validacao Pydantic de payloads externos
- Retry e circuit breaker configurados
- Fallback chain: Primary -> Fallback -> Cache -> Degraded

Contratos afetados:
- Infra adapters (sem mudanca direta na API)

Testes:
- Integracao com LocalStack (SQS/S3/DB)

Riscos:
- Timeouts e efeitos colaterais em ambiente local. Usar flags para ativar fallback

Checklist de implementacao:
- [x] Adapter SQS com retry (tenacity) e logs estruturados
- [x] Adapter S3 com presigned URLs (se aplicavel) e fallback local
- [x] Adapter satelite resiliente (primary + fallback + cache)
- [x] Circuit breaker nos providers externos
- [x] Schemas Pydantic para respostas externas (STAC, weather, etc.)
- [x] Tests de integracao LocalStack (SQS/S3)
- [x] Flags/env para ativar fallback e ajustar timeouts

Notas de execucao (Fase 2):
- Testes de integracao API com LocalStack:
  - `pytest tests/test_api_aws_integration.py -v`
  - Resultado: `2 passed, 9 warnings` (warnings do botocore sobre `datetime.utcnow` deprecado).

---

### Fase 3 — Application Layer (Use Cases)
Objetivo: mover regras de negocio para use cases e DTOs imutaveis.

Detalhes de implementacao (granular):
- Criar comandos/respostas Pydantic (ImmutableDTO)
- Criar use cases com portas injetadas
- Remover logica de negocio de routers

Entregaveis:
- Use cases refatorados em `services/api/app/application/use_cases`
- DTOs imutaveis com Pydantic
- Services de aplicacao isolando regras de negocio

Contratos afetados:
- Domain/Application (novo fluxo de validacao)

Testes:
- Unitarios dos use cases com ports em memoria

Riscos:
- Mudancas no fluxo de exceptions. Alinhar com `ai/contracts.md`

Checklist de implementacao:
- [x] Criar `use_cases/` por dominio (farms, aois, signals, etc.)
- [x] Criar `dtos/` (Commands/Responses) imutaveis
- [x] Garantir tenant_id obrigatorio nos commands
- [x] Remover logica de negocio de routers (delegar 100%)
- [x] Tests unitarios por use case com ports em memoria

---

### Fase 4 — Dependency Injection Container
Objetivo: wiring centralizado de ports/adapters por ambiente.

Detalhes de implementacao (granular):
- Criar container (API/Worker) com providers
- Mapear adapters por ambiente (dev/staging/prod)
- Garantir override para testes

Entregaveis:
- `di_container.py` em API e Worker
- Configuracao para trocar adapters por ambiente
- Wiring de ports/adapters com providers

Contratos afetados:
- Infra/config

Testes:
- Smoke tests de container e wiring

Riscos:
- Ciclos de import. Manter dependency rule

Checklist de implementacao:
- [x] Criar `di_container.py` no API
- [x] Criar `di_container.py` no Worker
- [x] Providers para repos, adapters externos e use cases
- [x] Override facil para testes (fake adapters)
- [x] Smoke test do container (resolve todos providers)

---

### Fase 5 — Presentation Layer
Objetivo: routers finos e validacao Pydantic no boundary HTTP.

Detalhes de implementacao (granular):
- Refatorar routers para usar use cases
- Extrair tenant_id do JWT em todos endpoints
- Padronizar erros conforme contrato

Entregaveis:
- Routers thin (delegam para use cases)
- Remocao de logica em controllers
- Validacao Pydantic no boundary HTTP

Contratos afetados:
- API behavior (se mudar, atualizar OpenAPI)

Testes:
- Testes de API (happy path + tenant isolation)

Riscos:
- Mudancas visiveis ao cliente. Validar com contratos

Checklist de implementacao:
- [x] Cada endpoint cria Command e chama use case
- [x] `Depends(get_current_tenant_id)` em todos endpoints multi-tenant
- [x] Validar inputs via Pydantic
- [x] Ajustar respostas para shape padrao de erro
- [x] Atualizar OpenAPI se houver mudanca de behavior

---

### Fase 6 — Worker Jobs
Objetivo: jobs finos chamando use cases com ports injetados.

Detalhes de implementacao (granular):
- Refatorar jobs para chamar use cases
- Injetar adapters no DI do worker
- Adicionar health checks nos adapters

Entregaveis:
- Jobs finos chamando use cases
- Ports/adapters de infraestrutura do worker
- Health checks dos adapters do worker

Contratos afetados:
- Worker + infraestrutura

Testes:
- Integracao com LocalStack e DB real

Riscos:
- Execucao assincrona e idempotencia. Confirmar com `ai/contracts.md`

Checklist de implementacao:
- [x] Refatorar handler BACKFILL para delegar a BackfillUseCase
- [x] Criar ports/adapters: JobRepository, SeasonRepository, JobQueue (SQS)
- [x] Adicionar unit tests para BackfillUseCase
- [x] Refatorar handler PROCESS_WEEK para delegar a ProcessWeekUseCase
- [x] Refatorar handler PROCESS_WEATHER para delegar a ProcessWeatherUseCase
- [x] Refatorar handler CREATE_MOSAIC para delegar a CreateMosaicUseCase
- [x] Refatorar handler PROCESS_RADAR_WEEK para delegar a ProcessRadarUseCase
- [x] Refatorar handler PROCESS_TOPOGRAPHY para delegar a ProcessTopographyUseCase
- [x] Refatorar handler CALCULATE_STATS para delegar a CalculateStatsUseCase
- [x] Refatorar handler SIGNALS_WEEK para delegar a SignalsWeekUseCase
- [x] Refatorar handler ALERTS_WEEK para delegar a AlertsWeekUseCase
- [x] Refatorar handler FORECAST_WEEK para delegar a ForecastWeekUseCase
- [x] Refatorar handler WARM_CACHE para delegar a WarmCacheUseCase
- [x] Refatorar handler DETECT_HARVEST para delegar a DetectHarvestUseCase
- [x] Refatorar handlers restantes para delegar a use cases
- [x] Garantir idempotencia (ON CONFLICT / checks) nos demais jobs
- [x] Validar tenant_id nos flows do worker
- [x] Tests de integracao com SQS/S3/DB

Notas de execucao (Fase 6):
- Testes unitarios do worker executados com `WORKER_TMP_DIR=C:\projects\vivacampo-app\.tmp`:
  - Resultado: `23 passed, 1 skipped, 2 warnings` (warnings do rasterio sobre georeferencia em testes)
- Ajuste feito para evitar erros de permissao no Windows:
  - Use cases `process_radar` e `process_topography` agora criam e limpam workdir manualmente em `.tmp`.
- Testes de integracao adicionados (nao executados):
  - `tests/test_worker_aws_integration.py` cobre S3/SQS/DB via LocalStack.
- Testes de integracao executados:
  - `pytest tests/test_worker_aws_integration.py -v`
  - Resultado: `3 passed, 10 warnings` (warnings do botocore sobre `datetime.utcnow` deprecado).
- Validacao de payload no worker:
  - `worker/main.py` agora valida campos obrigatorios por job e marca FAILED se faltarem.

---

### Fase 7 — Testes e Validacao
Objetivo: consolidar estrategia de testes e validar resiliencia.

Detalhes de implementacao (granular):
- Separar unit/integration/e2e com marcacoes
- Adicionar testes de contrato ports/adapters
- Rodar LocalStack no CI

Entregaveis:
- Suite de testes unitarios, integracao e E2E conforme estrategia
- Metricas basicas de fallback e health checks
- Testes de contrato para adapters (ports)

Contratos afetados:
- Nenhum direto

Testes:
- Execucao no CI e local

Riscos:
- Tempo de execucao. Ajustar marcacoes `@integration`

Checklist de implementacao:
- [x] Unitarios < 5s (sem DB/rede)
- [x] Integracao com LocalStack (S3/SQS)
- [x] Testes de contrato ports/adapters
- [ ] E2E com stack completa (pre-deploy)

Notas de execucao (Fase 7):
- Unit tests executados: `pytest tests\\unit -q` -> `67 passed, 2 skipped, 39 warnings in 2.30s`.
- E2E (Playwright) bloqueado por npm/proxy/cache no ambiente: `npx playwright install` falhou com `EPERM` no cache; requer ajuste de proxy/antivirus ou execucao local.
- E2E executado localmente (log em `e2e_test_log.txt`): `63 passed, 2 failed (57.8s)`.
  - Falhas: `Admin UI should login with admin token` em WebKit e Mobile Safari (timeout aguardando `/admin/dashboard`).

---

### Fase 8 — Limpeza de Codigo Legado
Objetivo: remover caminhos duplicados e consolidar arquitetura.

Detalhes de implementacao (granular):
- Mapear modulos antigos e equivalentes novos
- Remover codigo obsoleto apos validacao
- Atualizar docs/ADRs

Entregaveis:
- Remocao de caminhos antigos e duplicados
- Atualizacao de docs e ADRs
- Remocao de adapters/servicos obsoletos

Contratos afetados:
- Depende das remocoes

Testes:
- Regressao completa

Riscos:
- Remocao prematura. Precisa checklist de migracao

Checklist de implementacao:
- [x] Inventario de modulos antigos
- [ ] Confirmar novos fluxos em prod/staging (pendente; ver `TASK-HEX-008` em `ai/tasks.md`)
- [x] Remover codigo legado com diff pequeno
- [x] Atualizar docs/ADRs e changelog

Inventario inicial (Fase 8) — removidos:
- `services/worker/worker/jobs/process_week.py` (COG pipeline antigo)
- `services/worker/worker/application/use_cases/process_week.py` (legacy_processor)
- `services/worker/worker/main.py` (rotulo legacy)
- `services/app-ui/src/components/DynamicTileLayer.tsx` (legacyTileUrl)
- `services/app-ui/src/lib/tiles.ts` (`LEGACY_TILE_PROP_MAP`)

Checklist rapido de validacao (prod/staging) — pendente (ver `TASK-HEX-008` em `ai/tasks.md`):
1. Tiles (app-ui): alternar indices (NDVI/NDRE/RVI) sem erros de tile.
2. PROCESS_WEEK (worker): job executa e marca DONE no Admin Jobs.
3. Admin Jobs UI: filtros RUNNING/DONE e erro/traceId exibidos corretamente.
4. Missing Weeks: reprocess cria jobs sem regressao.
5. Worker logs: sem mensagens de pipeline antigo; `process_week_dynamic_tiling_forced` apenas se flag desligada.

---

## Seguranca Multi-Tenant (Transversal)
Entregaveis:
- RLS migration (se aprovado), access audit, checagem de tenant em todas as camadas
- Checklist de tenant_id em Presentation/Application/Domain/Repository
- Testes de isolamento multi-tenant

Contratos afetados:
- DB e API

Testes:
- Suite `tests/security/`

Riscos:
- Alto risco. Precisa aprovacao explicita antes de migracoes

---

## Sequencia e Checkpoints
1. Fase 1 inteira
2. Fase 2 parcial (adapters criticos)
3. Fase 3
4. Fase 4
5. Fase 5
6. Fase 6
7. Fase 7
8. Fase 8

Checkpoint de revisao apos cada fase: confirmar criterios de aceite e atualizar `ai/handoff.md`.

## Criterios de Sucesso (do plano original)

Arquitetura:
- Zero imports de frameworks ORM/Web no domain layer (apenas Pydantic permitido)
- Use cases testaveis sem infraestrutura (ports mockaveis)
- Trocar adapters via configuracao (sem mudanca de codigo)
- Dependency rule validada (import-linter ou equivalente)

Validacao e Resiliencia:
- Pydantic valida em 5 camadas (HTTP -> Presentation -> Application -> Domain -> Infrastructure)
- Validacao automatica em criacao e atualizacao (validate_assignment)
- Fallbacks configurados nas camadas criticas (satellite, storage, queue)
- Circuit breaker para falhas repetidas (threshold 3, recovery 5 min)

Testes:
- Cobertura > 85% (domain + application + infrastructure)
- Unitarios < 5s
- Integracao com LocalStack/Testcontainers
- Testes de contrato (ports/adapters)
- E2E < 10 min (stack completa)

Performance e Observabilidade:
- p95 API < 200ms
- Jobs < 60s (media)
- Logs estruturados (structlog JSON)
- Metricas de fallback
- Health checks para adapters

Documentacao:
- ADR de migracao (se nao existir)
- Runbooks atualizados (deploy/rollback)
- Guia de como adicionar novo adapter

## Checklist Rapido de Multi-Tenant (do plano original)
- PRESENTATION: endpoints usam tenant do JWT
- APPLICATION: Commands incluem tenant_id obrigatorio
- DOMAIN: Entities validam tenant_id nao-nulo
- REPOSITORY: Sempre filtra por tenant_id ou RLS
- DATABASE: RLS habilitado nas tabelas multi-tenant (se aprovado)
- AUDIT: AccessAuditor registra acessos
- TESTS: suite `tests/security/` passa

---

## Decisoes Pendentes (para iniciar a Fase 1)
1. Quais entidades iniciais sao prioridade alem de `Farm` e `AOI`?
2. Nivel de validacao Pydantic no domain: minima (non-breaking) ou espelhada aos schemas atuais?
3. RLS: iniciar agora ou deixar para aprovacao posterior?
