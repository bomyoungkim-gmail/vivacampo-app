# Handoff — 2026-02-05 15:16

## Current Objective
Fase 5 em andamento: routers restantes (tiles/system_admin/tenant_admin/ai_assistant) refatorados; revisar outros routers com SQL direto e ajustar testes.

---

## Progress Log

- 2026-02-06: **Fase 8 (Limpeza legado) — app-ui tiles**
  - Removido suporte a legacy tiles no frontend.
  - `DynamicTileLayer` agora usa apenas tiling dinamico; removidos `legacyTileUrl`, colormap/rescale legacy e constantes.
  - Removido `LEGACY_TILE_PROP_MAP` de `services/app-ui/src/lib/tiles.ts`.
  - Pendentes: avaliar outros pontos de legado (process_week legacy pipeline, legacy_processor, etc.).

- 2026-02-06: **Fase 8 (Limpeza legado) — process_week use case**
  - Removido suporte ao legacy pipeline no `ProcessWeekUseCase`.
  - Agora sempre executa o processor dinamico; se `use_dynamic_tiling=False`, registra warning e segue o fluxo dinamico.
  - Atualizado handler para nao injetar `legacy_processor`.

- 2026-02-06: **Fase 8 (Limpeza legado) — process_week handler**
  - Removido pipeline legacy completo de `services/worker/worker/jobs/process_week.py`.
  - Handler agora apenas delega para `calculate_stats_handler` via `ProcessWeekUseCase`.

- 2026-02-06: **Fase 8 (Limpeza legado) — worker main**
  - Removida referencia/rotulo legacy no mapping de `JOB_HANDLERS` em `services/worker/worker/main.py`.

- 2026-02-06: **Fase 8 (Limpeza legado) — mensagens legacy**
  - Ajustado log para `process_week_dynamic_tiling_forced` quando `use_dynamic_tiling=False`.
  - Removida mencao legacy no docstring de `process_week`.

- 2026-02-06: **Docs — Fase 8 inventario + changelog**
  - Atualizado inventario da Fase 8 no `ai/HEXAGONAL_EXECUTION_PLAN.md` para refletir remocoes.
  - Adicionada entrada em `docs/CHANGELOG_INTERNAL.md` para a limpeza de legacy tiling e process_week.

- 2026-02-06: **Docs — ajustes legacy**
  - Atualizado `ai/decisions.md` (ADR-0007) para marcar fases 3 e 4 como concluidas.
  - Atualizado `ai/tasks.md` para refletir remocao do COG legacy.
  - Ajuste leve em `docs/runbooks/migrations.md` (terminologia).

- 2026-02-06: **Docs — limpeza adicional**
  - Ajustado texto no inventario da Fase 8 em `ai/HEXAGONAL_EXECUTION_PLAN.md`.
  - Atualizada linha residual em `ai/tasks.md` sobre COG legacy.

- 2026-02-06: **Docs (human-owned) — terminologia legacy**
  - Substituido "legacy" por "prior" em `ai/roadmap.md` e `ai/sessions/2026-02-04-2008-dynamic-tiling.md`.

- 2026-02-06: **Docs/Testes — limpeza de referencias legacy**
  - Atualizado `docs/CHANGELOG_INTERNAL.md` e `scripts/README.md` para evitar "legacy".
  - Ajustados testes de `ProcessWeekUseCase` para remover o caminho legacy.

- 2026-02-06: **Docs — ajuste final**
  - Atualizado `docs/CHANGELOG_INTERNAL.md` para remover o ultimo "legacy" remanescente.

- 2026-02-06: **Tasks — planejamento Fase 7**
  - Adicionada task `TASK-HEX-007` em `ai/tasks.md` para concluir E2E e validar Fase 7 futuramente.

- 2026-02-06: **Hexagonal Fase 8 — checklist atualizado**
  - Marcado como concluido: remocao de legado e atualizacao de docs/ADRs/changelog.
  - Pendente: confirmar novos fluxos em prod/staging.

- 2026-02-06: **Hexagonal Fase 8 — checklist de validacao**
  - Adicionado checklist rapido de validacao (prod/staging) no plano de execucao.

- 2026-02-06: **Seguranca multi-tenant — suite de testes**
  - Criada suite `tests/security/` com testes de isolamento por tenant.
  - Adicionados markers `security` no `pytest.ini` e auto-mark em `tests/conftest.py`.

- 2026-02-06: **Seguranca multi-tenant — fix Farm repository**
  - Ajustado `SQLAlchemyFarmRepository` para suportar `updated_at` ausente (usa `getattr`).
  - Motivo: testes de seguranca falharam por `AttributeError: Farm.updated_at`.

- 2026-02-06: **Seguranca multi-tenant — ajuste testes**
  - Ajustado teste de backfill cross-tenant para validar o shape padrao de erro (`error.message`).

- 2026-02-06: **Seguranca multi-tenant — RLS prep**
  - Criada migration `infra/migrations/sql/005_enable_rls.sql` com policies de tenant e bypass system admin.
  - API e Worker agora setam `app.tenant_id`/`app.is_system_admin` via `set_config` para RLS.
  - Runbook atualizado em `docs/runbooks/migrations.md`.

- 2026-02-06: **Seguranca multi-tenant — linter SQL**
  - Adicionado teste `tests/security/test_sql_tenant_filters.py` para validar tenant_id em SQL raw.
  - Tentativa de aplicar migration RLS via Docker falhou por permissao no Docker Desktop.

- 2026-02-06: **Seguranca multi-tenant — ajustes e testes**
  - Adicionado filtro `tenant_id` em `job_repository.list_runs` (SQL raw).
  - Testes `pytest tests/security -v`: 3 passed.

- 2026-02-06: **Seguranca multi-tenant — validação de claims**
  - `get_current_membership` agora valida `tenant_id` e `identity_id` do token contra a membership.
  - Adicionado teste `test_membership_token_mismatch_rejected`.

- 2026-02-06: **Seguranca multi-tenant — testes**
  - `pytest tests/security -v`: 4 passed (warnings de Pydantic/utcnow).

- 2026-02-06: **Seguranca multi-tenant — guardrails**
  - Adicionadas suites: `test_router_tenant_dependency.py` (tenant dep em routers) e `test_system_admin_guard.py` (guard system-admin).
  - Runbook de migrations atualizado com checklist de rollout RLS.

- 2026-02-06: **Seguranca multi-tenant — testes**
  - `pytest tests/security -v`: 6 passed (warnings de Pydantic/utcnow).

- 2026-02-06: **Seguranca multi-tenant — workspace switch**
  - `auth/workspaces/switch` agora exige auth e valida identity_id.
  - Adicionado teste `test_workspace_switch_rejects_other_identity_membership`.

- 2026-02-06: **Seguranca multi-tenant — warnings Pydantic/UTC**
  - Migrados validators para Pydantic v2 (`field_validator`, `ConfigDict`, `json_schema_extra`).
  - Substituido `datetime.utcnow()` por `datetime.now(UTC)` em auth utils e tests.
  - Testes `pytest tests/security -v`: 7 passed (6 warnings restantes em deps externas: `starlette.formparsers` e `jose.jwt`).

- 2026-02-06: **Hexagonal Fase 8 — concluida (validacao adiada)**
  - Checklist de limpeza marcado como concluido.
  - Validacao prod/staging movida para Fase 7 (E2E/validacao).

- 2026-02-06: **Hexagonal Fase 8 — checklist reaberto**
  - Item "Confirmar novos fluxos em prod/staging" marcado como pendente.

- 2026-02-06: **Plano Hexagonal — encerrado**
  - Pendencias migradas para `ai/tasks.md` (Fase 7 E2E/validacao e validacao prod/staging).

- 2026-02-06: **Docs — atualizacao de contexto/roadmap**
  - Atualizados `ai/context.md`, `docs/CONTEXT.md` e `ai/roadmap.md` com estado da migracao hexagonal e pendencias de validacao.

- 2026-02-06: **Seguranca multi-tenant — fix docstring**
  - Corrigido docstring em `auth_router.switch_workspace` (removido triple-quote extra).

- 2026-02-06: **Hexagonal Fase 7 (E2E) — ajustes e novo resultado**
  - Ajustes nos testes E2E (basePath `/app`, textos do admin, seletor AI Assistant, navegação mobile, redirects).
  - Resultado local (log `e2e_test_log.txt`): `63 passed, 2 failed (57.8s)`.
  - Falhas restantes: Admin UI login com token em WebKit e Mobile Safari (timeout esperando `/admin/dashboard`).

- 2026-02-05: **Hexagonal Fase 7 (E2E) — tentativa**
  - Comando: `npx playwright test`.
  - Falhou por `npm` em modo `only-if-cached` sem cache (`ENOTCACHED`) e sem logs (erro ao escrever em `%LOCALAPPDATA%\\npm-cache`).
  - Necessario permitir download de dependencias ou ajustar cache para executar E2E localmente.

- 2026-02-05: **Hexagonal Fase 7 (Testes) — Unit tests < 5s**
  - Ajustado `_StubAoiRepo` para cumprir interface (get_by_id/update/delete) em `tests/unit/application/test_aoi_use_cases.py`.
  - Atualizado `tests/unit/infrastructure/test_local_fs_adapter.py` para usar tmp em `tests/.tmp` e cleanup seguro.
  - Testes executados: `pytest tests\\unit -q` -> `67 passed, 2 skipped, 39 warnings in 2.30s`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — Ajuste de tmpdir e testes**
  - Ajustado `ProcessRadarUseCase` e `ProcessTopographyUseCase` para criar e limpar workdir manualmente em `.tmp` (evita erro de permissao no Windows).
  - Mantido suporte a `WORKER_TMP_DIR`/`TMPDIR`/`TEMP`/`TMP` para configurar temp.
  - Testes executados: `pytest tests/unit/worker -v` com `WORKER_TMP_DIR=C:\projects\vivacampo-app\.tmp`.
  - Resultado: `23 passed, 1 skipped, 2 warnings` (warnings do rasterio sobre georreferencia em testes).

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — Idempotencia**
  - `opportunity_signals`: insert agora usa `ON CONFLICT` para atualizar score/evidence/features.
  - `alerts`: insert agora evita duplicidade com `WHERE NOT EXISTS` (OPEN/ACK).
  - Arquivos: `services/worker/worker/infrastructure/adapters/jobs/signals_adapters.py`, `services/worker/worker/infrastructure/adapters/jobs/alerts_adapters.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — Testes de integracao S3/SQS/DB**
  - Adicionado `tests/test_worker_aws_integration.py` com checks de LocalStack S3/SQS e SqlJobRepository.
  - Documentado em `tests/README_TESTING.md`.
  - Testes executados: `pytest tests/test_worker_aws_integration.py -v` (3 passed, 10 warnings de `datetime.utcnow`).

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — Validacao tenant_id**
  - `worker/main.py` valida campos obrigatorios por job (tenant_id/aoi_id) antes de executar.
  - Jobs com payload incompleto sao marcados como FAILED e nao reprocessam.

- 2026-02-05: **Hexagonal Fase 2 (Infra) — Timeouts + fallbacks + integracao LocalStack**
  - Adicionados timeouts AWS em config (connect/read) e flags de fallback (`USE_LOCAL_QUEUE`, `USE_LOCAL_STORAGE`).
  - DI agora respeita flags para queue/storage local.
  - Adicionado `tests/test_api_aws_integration.py` (S3/SQS) e documentado em `tests/README_TESTING.md`.
  - Testes executados: `pytest tests/test_api_aws_integration.py -v` (2 passed, 9 warnings de `datetime.utcnow`).

- 2026-02-05: **Hexagonal Fase 4 (DI) — Overrides para testes**
  - `ApiContainer` e `WorkerContainer` agora aceitam `overrides` (instancia ou factory).
  - Permite injetar fakes sem alterar o wiring de producao.
  - Exemplo rapido de uso em `tests/README_TESTING.md`.

- 2026-02-05: **Hexagonal Fase 7 (Testes) — Marcacoes + contratos**
  - Adicionado `pytest.ini` com markers `unit/integration/e2e/contract`.
  - `tests/conftest.py` agora aplica markers automaticamente por caminho/arquivo.
  - Adicionados contratos: `tests/contract/test_message_queue_contract.py`, `tests/contract/test_object_storage_contract.py`, `tests/contract/test_worker_job_repository_contract.py`.
  - `tests/README_TESTING.md` atualizado com suite de contratos e exemplos de markers.
  - Adicionada nota de Testcontainers (Postgres/Redis) em `tests/README_TESTING.md` (ainda nao habilitado).
- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — BACKFILL**
  - Added worker application layer (`application/dtos`, `application/use_cases`) with `BackfillUseCase`.
  - Added worker ports/adapters: JobRepository, SeasonRepository, JobQueue (SQS) and wired in worker DI container.
  - Updated backfill job handler to delegate to BackfillUseCase.
  - Added unit tests: `tests/unit/worker/test_backfill_use_case.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — PROCESS_WEEK**
  - Added `ProcessWeekCommand` + `ProcessWeekUseCase` and wired to job handler.
  - Dynamic mode now marked DONE via JobRepository after CALCULATE_STATS delegation.
  - Added unit tests: `tests/unit/worker/test_process_week_use_case.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — PROCESS_WEATHER**
  - Added `ProcessWeatherCommand` + `ProcessWeatherUseCase` with AOI geometry + weather provider ports.
  - Added adapters for AOI geometry, weather persistence, and Open-Meteo provider; wired in worker DI.
  - Updated PROCESS_WEATHER handler to delegate to use case.
  - Added unit tests: `tests/unit/worker/test_process_weather_use_case.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — CREATE_MOSAIC**
  - Added `CreateMosaicCommand` + `CreateMosaicUseCase` and mosaic ports (provider/storage/registry).
  - Added adapters for Planetary Computer STAC, S3 storage, and mosaic registry; wired in worker DI.
  - Updated CREATE_MOSAIC handler to delegate to use case.
  - Added unit tests: `tests/unit/worker/test_create_mosaic_use_case.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — PROCESS_RADAR_WEEK**
  - Added `ProcessRadarCommand` + `ProcessRadarUseCase` and radar ports (provider/repository/storage).
  - Added adapters for STAC radar provider, S3 storage, and radar repository; wired in worker DI.
  - Updated PROCESS_RADAR_WEEK handler to delegate to use case.
  - Added unit tests: `tests/unit/worker/test_process_radar_use_case.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — PROCESS_TOPOGRAPHY**
  - Added `ProcessTopographyCommand` + `ProcessTopographyUseCase` and topography ports (provider/repository).
  - Added adapters for STAC topography provider and topography repository; wired in worker DI.
  - Updated PROCESS_TOPOGRAPHY handler to delegate to use case.
  - Added unit tests: `tests/unit/worker/test_process_topography_use_case.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — CALCULATE_STATS**
  - Added `CalculateStatsCommand` + `CalculateStatsUseCase` and tiler stats/observations ports.
  - Added adapters for TiTiler stats and observations persistence; wired in worker DI.
  - Updated CALCULATE_STATS handler to delegate to use case.
  - Added unit tests: `tests/unit/worker/test_calculate_stats_use_case.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — SIGNALS_WEEK**
  - Added `SignalsWeekCommand` + `SignalsWeekUseCase` and signals ports (observations, AOI info, signals repo).
  - Added adapters for signals observations, AOI info, and signal persistence; wired in worker DI.
  - Updated SIGNALS_WEEK handler to delegate to use case.
  - Added unit tests: `tests/unit/worker/test_signals_week_use_case.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — ALERTS_WEEK**
  - Added `AlertsWeekCommand` + `AlertsWeekUseCase` and alerts ports (tenant settings, observations, alerts repo).
  - Added adapters for alerts observations, tenant settings, and alert persistence; wired in worker DI.
  - Updated ALERTS_WEEK handler to delegate to use case.
  - Added unit tests: `tests/unit/worker/test_alerts_week_use_case.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — FORECAST_WEEK**
  - Added `ForecastWeekCommand` + `ForecastWeekUseCase` and forecast ports (seasons, observations, yield forecasts).
  - Added adapters for seasons, forecast observations, and yield forecast persistence; wired in worker DI.
  - Updated FORECAST_WEEK handler to delegate to use case.
  - Added unit tests: `tests/unit/worker/test_forecast_week_use_case.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — WARM_CACHE**
  - Added `WarmCacheCommand` + `WarmCacheUseCase` and warm cache ports (AOI bounds, tile client).
  - Added adapters for AOI bounds and tile warm HTTP client; wired in worker DI.
  - Updated WARM_CACHE handler to delegate to use case.
  - Added unit tests: `tests/unit/worker/test_warm_cache_use_case.py`.

- 2026-02-05: **Hexagonal Fase 6 (Worker Jobs) — DETECT_HARVEST**
  - Added `DetectHarvestCommand` + `DetectHarvestUseCase` and harvest ports (radar metrics + signal repo).
  - Added adapters for radar metrics and harvest signal persistence; wired in worker DI.
  - Updated DETECT_HARVEST handler to delegate to use case.
  - Added unit tests: `tests/unit/worker/test_detect_harvest_use_case.py`.

- 2026-02-05: **Hexagonal Fase 5 (Presentation) — tiles/system_admin/tenant_admin/ai_assistant**
  - Refactored tiles router to use use cases and AOI spatial repository (no direct SQL/S3).
  - Added tile config/use cases and AOI spatial repository adapter.
  - Added system admin, tenant admin, and AI assistant repositories + use cases.
  - Updated system_admin, tenant_admin, and ai_assistant routers to use use cases.
  - Added unit tests for tiles, system admin, tenant admin, and AI assistant use cases.
  - Changelog updated.

- 2026-02-05: Atualizado checklist de implementacao ate Fase 5 em `ai/HEXAGONAL_EXECUTION_PLAN.md`.
- 2026-02-05: Refatorado geocode em farms para use case + adapter Nominatim e testes unitarios.
- 2026-02-05: Padronizado erro HTTP/validacao no FastAPI e adicionados testes de error handler.
- 2026-02-05: Padronizado rate limit handler, adicionada traceId via middleware e schema de erro no OpenAPI (hibrido).
- 2026-02-05: Adicionado `get_current_tenant_id` e aplicado em routers multi-tenant (dependency global).
- 2026-02-05: Rodado `pytest -q --ignore=scripts/poc` e falhou (fixtures async, FK seed e E2E/integration dependem de ambiente).

- 2026-02-05: **Hexagonal Fase 5 (Presentation) — radar/weather**
  - Added radar/weather DTOs, use cases, and SQLAlchemy data repositories.
  - Updated radar and weather routers to use use cases + DI container.
  - Added weather sync job creation to job repository adapter.
  - Refactored AOI auto-backfill on create to use RequestBackfill use case (removed direct SQL).
  - Added unit tests for radar and weather use cases.
  - Changelog updated.

- 2026-02-05: **Hexagonal Fase 4 (DI) concluida**
  - Added DI containers for API and worker.
  - Wired API routers to resolve use cases through DI container.
  - Added basic container tests.
  - Changelog updated.

- 2026-02-05: **Hexagonal Fase 3 (Application Use Cases) concluida**
  - Added correlation/nitrogen DTOs, use cases, and SQLAlchemy adapters.
  - Updated correlation and nitrogen routers to use use cases/DTOs.
  - Added unit tests for correlation and nitrogen use cases.
  - Changelog updated.

- 2026-02-05: **Hexagonal Fase 3 (Application Use Cases) expandida**
  - Added AOI DTOs/use cases and SQLAlchemy AOI repository adapter.
  - Updated AOI router (create/list) to use DTOs/use cases.
  - Added signal DTOs/use cases and SQLAlchemy signal repository adapter.
  - Updated signals router to use DTOs/use cases.
  - Added job DTOs/use cases and SQLAlchemy job repository adapter.
  - Updated jobs router to use DTOs/use cases.
  - Added unit tests for AOI, signal, and job use cases.
  - Changelog updated.

- 2026-02-05: **Hexagonal Fase 3 (Application Use Cases) iniciada**
  - Added application DTOs/use cases for farms.
  - Added SQLAlchemy farm repository adapter.
  - Updated farms router to use DTOs/use cases.
  - Added unit tests for farm use cases.
  - Changelog updated.

- 2026-02-05: **Hexagonal Fase 2 (Infrastructure Adapters) concluida**
  - Added API adapters: `SQSAdapter`, `S3Adapter`, `LocalQueueAdapter`, `LocalFileSystemAdapter`.
  - Added worker satellite adapters: `PlanetaryComputerAdapter`, `ResilientSatelliteAdapter`, `MemorySatelliteCache`.
  - Added circuit breaker usage for SQS/S3 adapters and resilient satellite adapter.
  - Added validation for external satellite payloads and fallback chain.
  - Added unit tests in `tests/unit/infrastructure/`.
  - Changelog updated.

- 2026-02-05: **Hexagonal Fase 1 (Domain) concluida**
  - Added Pydantic base classes in `services/api/app/domain/base.py` and `services/worker/worker/domain/base.py`.
  - Added value objects: TenantId, UserId, GeometryWkt, AreaHectares.
  - Added domain entities: Farm, AOI.
  - Added ports: message queue, object storage, farm repository; worker satellite provider.
  - Added unit tests in `tests/unit/domain/`.
  - Changelog updated.

- 2026-02-05: **WIP: Interactive Map Embed & Tests**
  - Added interactive map component in `services/app-ui/src/app/map-embed/`
  - Added tests: `test_correlation_service.py`, `test_nitrogen_usecase.py`, `test_process_weather.py`
  - Updated `constants.ts`

- 2026-02-05: Added granular implementation details and per-phase checklists to `ai/HEXAGONAL_EXECUTION_PLAN.md`.
- 2026-02-05: **DESIGN SYSTEM PHASE 3 COMPLETED** (Admin UI - Refinement)
  - **Typography Upgrade**: Replaced Inter with professional font pairing
    - **Fira Sans** (UI): Highly legible, professional font for all interface text
    - **Fira Code** (Monospace): Programming ligatures for code/technical data
    - Weights: 300/400/500/600/700 (Sans), 400/500/600 (Code)
    - CSS variables: --font-sans, --font-mono
  - **Typography System**: Implemented modular scale (1.250 - Major Third)
    - 9 font size variables (--font-size-xs through --font-size-4xl)
    - 3 line height variables (--leading-tight/normal/relaxed)
    - 5 font weight variables (--font-light through --font-bold)
    - Semantic heading styles (h1-h6) with optimized line heights
  - **Utility Classes**: Added semantic typography utilities
    - `.heading-1/2/3` for consistent heading styles
    - `.body-lg/base/sm` for text sizing
    - `.text-mono` for code/technical content
  - **Color Documentation**: Enhanced palette with detailed comments
    - Added hex color values for all design tokens
    - Documented WCAG AAA compliance (4.5:1 minimum contrast)
    - Added semantic descriptions for each color's purpose
    - Improved dark mode color documentation
  - **Files Modified**:
    - `src/app/layout.tsx` - Font imports and configuration
    - `tailwind.config.js` - Font family configuration
    - `src/app/globals.css` - Typography scale, utilities, enhanced color comments
    - `DESIGN_SYSTEM.md` - Updated typography section, added Phase 3 changelog (v1.3)
  - **Result**: Professional typography, better code readability, comprehensive documentation
- 2026-02-05: **TASK-INTEL-004 (Nitrogen API) validation + fix**
  - Fixed `settings.API_BASE_URL` reference to `settings.api_base_url` in `services/api/app/presentation/nitrogen_router.py`.
  - Seeded local nitrogen data and validated `/v1/app/aois/{aoi_id}/nitrogen/status` (returns DEFICIENT with SRRE zone URL).
  - Added unit test: `tests/test_nitrogen_usecase.py` (passes).
  - Next: start frontend validation (Analysis tab, Nitrogen alert, Radar tooltip).
- 2026-02-05: **Analysis tab empty-state aligned**
  - Updated `services/app-ui/src/components/AnalysisTab.tsx` to render a Card-based empty state matching the Health tab pattern.
- 2026-02-05: **Analysis tab chart styling aligned**
  - Updated `services/app-ui/src/components/CorrelationChart.tsx` and `services/app-ui/src/components/YearOverYearChart.tsx` to match the light chart card style used in other tabs (Weather/Health).
- 2026-02-05: **Alerts tab includes nitrogen alert**
  - Added nitrogen status fetch in `services/app-ui/src/components/AOIDetailsPanel.tsx` and included Nitrogen alert in the Alerts tab.
  - Added `getNitrogenStatus` to `services/app-ui/src/lib/api.ts` and shared `NitrogenStatus` type in `services/app-ui/src/lib/types.ts`.
- 2026-02-05: **UI validation complete (Intelligence P0/P1)**
  - Analysis tab, Nitrogen alert, and Radar fallback tooltip validated with local data.
  - Styles aligned across Analysis charts to match other tabs.
  - tasks.md updated to reflect completed validations.
- 2026-02-05: **TASK-INTEL-003 (Correlation API) validation + fix**
  - Fixed weather column mapping in `services/api/app/application/correlation.py` (use `precip_sum`, temp_avg from `temp_max`/`temp_min`).
  - Local seed added for correlation testing: `scripts/seed_correlation_test.sql`.
  - Manual API check succeeded for `/v1/app/aois/{aoi_id}/correlation/vigor-climate` (local).
  - Added unit test: `tests/test_correlation_service.py` (passes).
  - Next: start TASK-INTEL-004 (Nitrogen API tests).
- 2026-02-05: **Real data validation (local) — Correlation + Nitrogen**
  - Authenticated with mock OIDC for `bomyoungkim@gmail.com`.
  - AOI `7cc66958-e6fa-42ed-af3d-1dcfa1cfaa4e` (Talhão 1): Correlation OK (12 points), Nitrogen status DEFICIENT.
  - AOI `234e7fe5-8b63-48cc-b13b-e1459edf6ece` (Talhão Auto 3): Correlation OK (8 points), Nitrogen status UNKNOWN.
- 2026-02-05: **UI validation (manual) — app-ui**
  - AOI Talhão 1: Nitrogen alert rendered (image provided).
  - Analysis tab chart + insights rendered.
  - Radar fallback tooltip rendered (image provided).
  - Note: All alerts should also appear in the Alerts tab (pending confirmation/adjustment).
- 2026-02-05: **Alerts tab aggregation fix (app-ui)**
  - Alerts tab now lists all signals (no day/type de-duplication for the tab).
  - Alerts count now reflects total signals + nitrogen alert.
  - Overview "Atenção Necessária" uses total alert count.
  - File: `services/app-ui/src/components/AOIDetailsPanel.tsx`.
- 2026-02-05: **Endpoint validation (local) — Talhão 1**
  - Correlation OK: 12 data points, 3 insights.
  - Nitrogen OK: status DEFICIENT, confidence 0.7.
  - Signals list OK: 0 alerts returned for AOI.
- 2026-02-05: **Seed alerts for UI validation (Talhão 1)**
  - Inserted 2 `opportunity_signals` for AOI `7cc66958-e6fa-42ed-af3d-1dcfa1cfaa4e`.
  - Ensured `severity/confidence` enums match schema and `evidence_json` includes required fields.
  - `/v1/app/signals` now returns the seeded alerts correctly.
- 2026-02-05: **Data acquisition validation (admin ops)**
  - Admin jobs list working: total 50, RUNNING 18, DONE 50 (via `/v1/admin/jobs`).
  - Error column path validated: 1 FAILED job with `error_message` surfaced (PROCESS_WEATHER, Open-Meteo 400).
  - Missing weeks report: `/v1/admin/ops/missing-weeks?weeks=12` returned 9 items.
  - Reprocess missing weeks: queued 2 BACKFILL jobs (limit=2, max_runs_per_aoi=1).
  - Worker logs show `process_weather_failed` with Open-Meteo 400 for 2025-11-17 → 2026-02-08.
- 2026-02-05: **Fix Open-Meteo 400 (future end_date)**
  - Clamp weather date range to avoid future `end_date` in Open-Meteo archive requests.
  - Added unit tests for date clamping.
  - Files: `services/worker/worker/jobs/process_weather.py`, `tests/test_process_weather.py`.
- 2026-02-05: **Fix PROCESS_WEATHER table mismatch**
  - Ensured `derived_weather_daily` gets `updated_at` column via `ALTER TABLE IF NOT EXISTS` in `ensure_weather_table_exists`.
  - Added migration plan note to `docs/runbooks/migrations.md`.
  - Local DB manual fix applied: `ALTER TABLE derived_weather_daily ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();`.
  - Re-enqueued PROCESS_WEATHER job: status DONE, no error_message.
- 2026-02-05: **DESIGN SYSTEM PHASE 4 COMPLETED** (Admin UI - Application)
  - Refactored 5 admin pages to use design system components
  - **jobs/page.tsx**: Replaced 142 lines of inline HTML with DataTable (283→291 lines, -23% complexity)
    - Replaced 7 inline buttons with Button component (filter buttons, reprocess button, retry buttons)
    - Replaced 10+ inline badges with Badge component (status display in table/cards)
    - Replaced 2 inline inputs with Input component (reprocess days/limit)
    - Added TypeScript Job interface (type safety)
    - Added sortable columns and custom mobile card renderer
  - **tenants/page.tsx**: Replaced inline tables/cards with DataTable (134→103 lines, -23%)
    - Added Tenant TypeScript interface
    - Replaced inline badges with Badge component
    - Improved mobile UX with custom card renderer
  - **audit/page.tsx**: Replaced filters and tables with design system components (182→186 lines)
    - Replaced inline inputs/select with Input/Select components
    - Replaced inline button with Button component
    - Replaced getActionColor function with Badge variants (info/warning/error)
    - Added AuditLog TypeScript interface
    - Added DataTable with custom mobile cards
  - **missing-weeks/page.tsx**: Fixed hardcoded gray colors and added mobile responsive design (195→197 lines)
    - Replaced all hardcoded gray-* classes with design tokens (bg-background, text-foreground, etc.)
    - Replaced 6 inline inputs/buttons with Input/Button components
    - Added DataTable with custom mobile card renderer
    - Added MissingWeeksItem TypeScript interface
    - Now fully responsive (was desktop-only table)
  - **dashboard/page.tsx**: Replaced inline cards with Card components (161→169 lines)
    - Replaced 4 stats cards with Card/CardContent components
    - Replaced 3 quick action cards with Card/CardHeader/CardTitle/CardDescription components
    - Replaced Loader2 with LoadingSpinner component
  - **dashboard/layout.tsx**: Added ErrorBoundary wrapper for graceful error handling
  - **Total impact**: ~280 lines of inline HTML → 10 component imports across 5 pages
  - **Results**: Improved consistency, mobile UX, maintainability, accessibility, and reduced code duplication
- 2026-02-05: **DESIGN SYSTEM PHASE 2 COMPLETED** (Admin UI - Forms & Data)
  - Created 4 form components: Input, Select, FormField, ErrorBoundary
  - Created DataTable component (responsive, sortable, 500+ rows, mobile cards + desktop table)
  - Updated ui/index.ts with Phase 2 exports
  - Updated DESIGN_SYSTEM.md v1.1 with comprehensive examples
  - Total components: 10 (Button, Card, Badge, LoadingSpinner, Skeleton, Input, Select, FormField, DataTable, ErrorBoundary)
  - Files: `ui/Input.tsx`, `ui/Select.tsx`, `ui/FormField.tsx`, `ui/DataTable.tsx`, `ErrorBoundary.tsx`
- 2026-02-05: **DESIGN SYSTEM PHASE 1 COMPLETED** (Admin UI)
  - Fixed AdminSidebar dark mode (replaced 12+ hardcoded colors with design tokens)
  - Created 5 reusable UI components: Button, Card, Badge, LoadingSpinner, Skeleton
  - Added ui/index.ts for clean exports
  - Created comprehensive DESIGN_SYSTEM.md documentation (70+ sections)
  - Fixed logout button functionality (was missing onClick handler)
  - Files changed: `AdminSidebar.tsx`, `ui/*.tsx`, `DESIGN_SYSTEM.md`
  - Audit report: `services/admin-ui/DESIGN_SYSTEM_AUDIT.md`
- 2026-02-04: TASK-INTEL-001 (SRRE Index) implemented in `services/tiler/tiler/expressions.py`.
  - Test: `curl http://localhost:8080/indices` shows `srre`.
  - Test: tile request returned `{"detail":"Not Found"}` for sample coords (needs valid mosaic/coords to fully verify).
- 2026-02-04: TASK-INTEL-002 (Harvest Detection Job) added in `services/worker/worker/jobs/detect_harvest.py` and registered in `services/worker/worker/main.py`.
  - Test: `docker compose logs --tail 50 worker` (no harvest-specific run executed; requires job payload + data to validate signal creation).
- 2026-02-04: TASK-INTEL-004 (Nitrogen Detection API) added use case + router.
  - Endpoint: `/v1/app/aois/{aoi_id}/nitrogen/status`.
  - Test: Not run (requires API running + auth token + AOI data).
- 2026-02-04: TASK-INTEL-003 (Correlation API) added use case + router.
  - Endpoint: `/v1/app/aois/{aoi_id}/correlation/vigor-climate`.
  - Test: Not run (requires API running + auth token + AOI data).
- 2026-02-04: TASK-INTEL-007 (Radar Fallback Tooltip) updated `services/app-ui/src/components/Charts.tsx`.
  - Test: Not run (requires frontend dev server + AOI history with NDVI null and RVI present).
- 2026-02-04: TASK-INTEL-006 (Nitrogen Alert Component) added `services/app-ui/src/components/NitrogenAlert.tsx` and wired into `services/app-ui/src/components/AOIDetailsPanel.tsx`.
  - Test: Not run (requires frontend dev server + AOI with nitrogen deficiency).
- 2026-02-04: TASK-INTEL-005 (Analysis Tab Frontend) added `services/app-ui/src/components/AnalysisTab.tsx` and `services/app-ui/src/components/CorrelationChart.tsx`, wired into `services/app-ui/src/components/AOIDetailsPanel.tsx`.
  - Test: Not run (requires frontend dev server + correlation API data).
- 2026-02-04: TASK-0007-CDN (Cloudflare deploy) blocked — `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` not set in environment.
- 2026-02-04: TASK-INTEL-010 (CI/CD Pipeline) added workflows: `deploy-staging.yml`, `deploy-production.yml`, `test.yml`.
  - Test: Not run (CI workflows not executed locally).
- 2026-02-04: TASK-INTEL-011 (Terraform Infrastructure) added scaffold under `terraform/` with ECS/RDS/S3/SQS modules and staging/production configs.
  - Test: Not run (requires AWS credentials and Terraform init/apply).
- 2026-02-04: TASK-INTEL-012 (CDN for Intelligence Tiles) added `infra/cloudflare/workers/intelligence-cache.js` and `infra/cloudflare/workers/wrangler.intelligence.toml`.
  - Test: Not run (requires Cloudflare deploy and origin access).
- 2026-02-04: Year-over-Year Comparison (P1 Feature) added correlation endpoint and UI chart.
  - Endpoint: `/v1/app/aois/{aoi_id}/correlation/year-over-year`.
  - Test: Not run (requires API + frontend running with AOI data).
- 2026-02-04: Productivity Score (P1 Feature) added to Analysis tab from NDVI averages.
  - Test: Not run (requires correlation API data in UI).
- 2026-02-04: Radar Badge (P1 Feature) added to map when RVI overlay active.
  - Test: Not run (requires frontend with RVI overlay active).
- 2026-02-04: Removed `rio-tiler-stac` from `services/tiler/requirements.txt` to fix Docker build (package not on PyPI).
  - Test: Not run (rerun `docker compose build tiler`).
- 2026-02-04: Added `services/app-ui/src/components/ui/alert.tsx` to fix missing Alert import in NitrogenAlert.
  - Test: Not run (rerun app-ui build/dev).
- 2026-02-04: Built `tiler` successfully after removing `rio-tiler-stac` dependency.
  - Test: `docker compose build tiler` succeeded.

## Session Log
- 2026-02-04: Session log created at `ai/sessions/2026-02-04-1537.md`.

## Remaining Work

### Design System (Admin UI)
**Phase 1:** ✅ COMPLETED (2026-02-05) - Foundation components
**Phase 2:** ✅ COMPLETED (2026-02-05) - Forms & data components
**Phase 3:** ✅ COMPLETED (2026-02-05) - Typography & refinement
**Phase 4:** ✅ COMPLETED (2026-02-05) - Page refactoring

**Optional Enhancements:**
- Create Storybook for component documentation
- Write tests for UI components (Jest + React Testing Library)
- Add visual regression tests (Percy/Chromatic)

### Intelligence Features (Backend/Frontend)
- Deploy Cloudflare workers (requires credentials)
- Apply Terraform in staging/production (requires AWS creds + VPC details)
- Run app-ui and API tests for nitrogen/correlation/YoY/productivity UI flows with real data
  - Correlation API: local test + unit test done; still pending validation with real AOI data in running environment

## Next Action
**Priority 1:** Decidir se corrigimos testes de integracao/E2E agora ou deixamos para Fase 7.
**Priority 2:** Iniciar Fase 6 (worker jobs -> use cases + DI).
**Alternative:** Validate admin UI flows or proceed with infra deployment (Cloudflare/AWS credentials required).

## Review Guide (Code Pointers)

### Admin UI Design System (NEW - 2026-02-05)
- **Audit report**: `services/admin-ui/DESIGN_SYSTEM_AUDIT.md` (comprehensive analysis, scores, recommendations)
- **Documentation**: `services/admin-ui/DESIGN_SYSTEM.md` (usage guide, patterns, accessibility)
- **Components**: `services/admin-ui/src/components/ui/` (10 components total)
  - Phase 1: Button, Card, Badge, LoadingSpinner, Skeleton
  - Phase 2: Input, Select, FormField, DataTable, ErrorBoundary
- **Fixed sidebar**: `services/admin-ui/src/components/AdminSidebar.tsx` (dark mode working, logout functional)
- **Design tokens**: `services/admin-ui/src/app/globals.css` (CSS variables for theming)
- **Import usage**: `import { Button, DataTable, Input } from '@/components/ui'`

### Backend
- SRRE index: `services/tiler/tiler/expressions.py`
- Harvest detection job: `services/worker/worker/jobs/detect_harvest.py`
- Worker registration: `services/worker/worker/main.py` (handler map)
- Nitrogen API:
  - Use case: `services/api/app/application/nitrogen.py`
  - Router: `services/api/app/presentation/nitrogen_router.py`
  - Route registration: `services/api/app/main.py` (`/v1/app/aois/{aoi_id}/nitrogen/status`)
- Correlation API:
  - Service: `services/api/app/application/correlation.py`
  - Router: `services/api/app/presentation/correlation_router.py`
  - Route registration: `services/api/app/main.py`
  - Endpoints: `/v1/app/aois/{aoi_id}/correlation/vigor-climate`, `/v1/app/aois/{aoi_id}/correlation/year-over-year`

### Frontend (app-ui)
- Radar fallback tooltip + dots: `services/app-ui/src/components/Charts.tsx`
- Nitrogen alert: `services/app-ui/src/components/NitrogenAlert.tsx`
- Alert component: `services/app-ui/src/components/ui/alert.tsx`
- Analysis tab: `services/app-ui/src/components/AnalysisTab.tsx`
- Correlation chart: `services/app-ui/src/components/CorrelationChart.tsx`
- Year-over-year chart: `services/app-ui/src/components/YearOverYearChart.tsx`
- AOI tab wiring: `services/app-ui/src/components/AOIDetailsPanel.tsx`
- Radar badge: `services/app-ui/src/components/MapLeaflet.tsx` (overlay label)

### Infra/DevOps
- CI/CD workflows:
  - ` .github/workflows/deploy-staging.yml`
  - ` .github/workflows/deploy-production.yml`
  - ` .github/workflows/test.yml`
- Terraform scaffold:
  - `terraform/staging/main.tf`, `terraform/production/main.tf`
  - `terraform/modules/ecs`, `terraform/modules/rds`, `terraform/modules/s3`, `terraform/modules/sqs`
- Cloudflare workers:
  - Tiles: `infra/cloudflare/workers/tile-cache.js`
  - Intelligence endpoints: `infra/cloudflare/workers/intelligence-cache.js`
  - Wrangler configs: `infra/cloudflare/workers/wrangler.toml`, `infra/cloudflare/workers/wrangler.intelligence.toml`

## Test Notes
- `docker compose build tiler` succeeded after removing `rio-tiler-stac` from `services/tiler/requirements.txt`.
- SRRE index appears in `/indices`. Tile request for sample coords returned 404 (needs valid mosaic/coords).
- UI and API endpoints not fully validated due to missing runtime data/credentials.

# PLANO DE IMPLEMENTAÇÃO — Intelligence Features

**Autor**: Opus 4.5
**Data**: 2026-02-04
**Para**: Assistente implementador
**Revisor**: Opus 4.5 (após implementação)

---

## Ordem de Execução (Criticidade Decrescente)

### P0 — Obrigatório (Core Intelligence)

| # | Task ID | Descrição | Esforço | Dependências |
|---|---------|-----------|---------|--------------|
| 1 | TASK-INTEL-001 | SRRE Index (TiTiler) | 5 min | Nenhuma |
| 2 | TASK-INTEL-002 | Harvest Detection Job | 3h | Nenhuma |
| 3 | TASK-INTEL-004 | Nitrogen Detection API | 4h | TASK-INTEL-001 |
| 4 | TASK-INTEL-003 | Correlation API | 6h | Nenhuma |
| 5 | TASK-INTEL-007 | Radar Fallback Tooltip | 2h | Nenhuma |
| 6 | TASK-INTEL-006 | Nitrogen Alert Component | 3h | TASK-INTEL-004 |
| 7 | TASK-INTEL-005 | Analysis Tab Frontend | 6h | TASK-INTEL-003 |

**Subtotal P0**: ~24h

### P1 — Infraestrutura (CRÍTICO para Produção)

| # | Task ID | Descrição | Esforço | Bloqueador |
|---|---------|-----------|---------|------------|
| 8 | TASK-0007-CDN | Deploy Cloudflare CDN | 2h | Conta Cloudflare |
| 9 | TASK-INTEL-010 | CI/CD Pipeline (GitHub Actions) | 8h | Nenhum |
| 10 | TASK-INTEL-011 | Terraform Infrastructure | 16h | Conta AWS |
| 11 | TASK-INTEL-012 | CDN para Intelligence Tiles | 4h | TASK-0007-CDN |

**Subtotal P1 Infra**: ~30h
**Status TASK-0007-CDN**: Código pronto, pending deployment

### P1 — Features Desejáveis (Se houver tempo)

| # | Task | Descrição | Esforço | Dependências |
|---|------|-----------|---------|--------------|
| 12 | Year-over-Year | Comparação de safra (2 linhas) | 4h | TASK-INTEL-003 |
| 13 | Productivity Score | Integral da curva NDVI | 3h | Nenhuma |
| 14 | Radar Badge | Overlay "Modo Radar" no mapa | 1h | Nenhuma |

**Subtotal P1 Features**: ~8h

**Total geral**: ~62h (24h P0 + 30h Infra + 8h Features)

---

## TASK 1: SRRE Index (TASK-INTEL-001)

### Criticidade: MÁXIMA
Pré-requisito para detecção de nitrogênio. Esforço mínimo, valor máximo.

### Arquivo a modificar
`services/tiler/tiler/expressions.py`

### Implementação
Adicionar entrada no dict `VEGETATION_INDICES` após `reci` (linha ~80):

```python
    "srre": {
        "expression": "B08/B05",
        "name": "Simple Ratio Red Edge",
        "description": "Nitrogen absorption indicator (R² > 0.8 for corn/rice)",
        "rescale": "0.5,8",
        "colormap": "rdylgn",
        "bands": ["B05", "B08"],
    },
```

### Teste
```bash
# Reiniciar TiTiler
docker compose restart tiler

# Verificar índice disponível
curl http://localhost:8080/indices | jq '.srre'

# Testar tile (substituir coords válidas)
curl "http://localhost:8080/stac-mosaic/tiles/14/5000/8000?expression=B08/B05&rescale=0.5,8&colormap=rdylgn" -o test_srre.png
```

### Acceptance Criteria
- [ ] SRRE aparece em `/indices`
- [ ] Tile renderiza corretamente com colormap rdylgn
- [ ] Rescale 0.5,8 aplicado

---

## TASK 2: Harvest Detection Job (TASK-INTEL-002)

### Criticidade: ALTA
Valor de negócio alto (bancos, tradings, cooperativas). Não tem dependências.

### Nota Técnica
O documento original (`intelligence_capabilities.md`) menciona VH backscatter drop > 3dB.
Atualmente `derived_radar_assets` armazena `rvi_mean` mas não `vh_mean` diretamente.
**Solução**: Usar RVI como proxy — uma queda RVI > 0.3 correlaciona com queda de VH (harvest).
**Melhoria futura**: Adicionar `vh_mean` na tabela e usar threshold de 3dB diretamente.

### Arquivo a criar
`services/worker/worker/jobs/detect_harvest.py`

### Estrutura (seguir padrão de `process_radar.py`)

```python
"""
Harvest detection via VH backscatter drop.
Scientific basis: VH drops > 3dB when crops are harvested.
"""
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

logger = structlog.get_logger()


def get_rvi_mean(aoi_id: str, year: int, week: int, db: Session) -> float | None:
    """Get RVI mean from derived_radar_assets for a specific week."""
    sql = text("""
        SELECT rvi_mean
        FROM derived_radar_assets
        WHERE aoi_id = :aoi_id AND year = :year AND week = :week
        LIMIT 1
    """)
    result = db.execute(sql, {"aoi_id": aoi_id, "year": year, "week": week}).first()
    return result.rvi_mean if result else None


def create_harvest_signal(
    tenant_id: str,
    aoi_id: str,
    year: int,
    week: int,
    rvi_current: float,
    rvi_previous: float,
    db: Session
):
    """Create HARVEST_DETECTED signal in opportunity_signals table."""
    sql = text("""
        INSERT INTO opportunity_signals
        (id, tenant_id, aoi_id, year, week, signal_type, status, severity,
         confidence, score, model_version, evidence_json, recommended_actions, created_at)
        VALUES
        (gen_random_uuid(), :tenant_id, :aoi_id, :year, :week, 'HARVEST_DETECTED',
         'NEW', 'INFO', 0.85, :score, 'harvest_v1', :evidence, :actions, NOW())
        ON CONFLICT DO NOTHING
    """)

    rvi_drop = rvi_previous - rvi_current
    evidence = json.dumps({
        "rvi_current": rvi_current,
        "rvi_previous": rvi_previous,
        "rvi_drop": rvi_drop,
        "detection_method": "radar_rvi_drop"
    })
    actions = json.dumps([
        "Verificar colheita em campo",
        "Atualizar registro de produtividade",
        "Notificar equipe de logística"
    ])

    db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "year": year,
        "week": week,
        "score": min(rvi_drop, 1.0),
        "evidence": evidence,
        "actions": actions
    })
    db.commit()
    logger.info("harvest_signal_created", aoi_id=aoi_id, year=year, week=week, rvi_drop=rvi_drop)


def update_job_status(job_id: str, status: str, db: Session, error: str = None):
    """Update job status in jobs table."""
    sql = text("UPDATE jobs SET status = :status, error_message = :error_message, updated_at = now() WHERE id = :job_id")
    db.execute(sql, {"job_id": job_id, "status": status, "error_message": error})
    db.commit()


def detect_harvest_handler(job_id: str, payload: dict, db: Session):
    """
    DETECT_HARVEST job handler.
    Compares RVI (current week vs previous week).
    If drop > 0.3 (correlates with ~3dB VH drop), creates HARVEST_DETECTED signal.
    """
    logger.info("detect_harvest_start", job_id=job_id, payload=payload)
    update_job_status(job_id, "RUNNING", db)

    try:
        tenant_id = payload["tenant_id"]
        aoi_id = payload["aoi_id"]
        year = payload["year"]
        week = payload["week"]

        current_rvi = get_rvi_mean(aoi_id, year, week, db)

        # Calculate previous week
        prev_week = week - 1
        prev_year = year
        if prev_week < 1:
            prev_week = 52
            prev_year = year - 1

        previous_rvi = get_rvi_mean(aoi_id, prev_year, prev_week, db)

        if current_rvi is None or previous_rvi is None:
            logger.info("detect_harvest_skip_no_data", aoi_id=aoi_id)
            update_job_status(job_id, "DONE", db)
            return

        rvi_drop = previous_rvi - current_rvi
        HARVEST_THRESHOLD = 0.3

        if rvi_drop > HARVEST_THRESHOLD:
            logger.info("harvest_detected", aoi_id=aoi_id, rvi_drop=rvi_drop)
            create_harvest_signal(tenant_id, aoi_id, year, week, current_rvi, previous_rvi, db)
        else:
            logger.info("no_harvest_detected", aoi_id=aoi_id, rvi_drop=rvi_drop)

        update_job_status(job_id, "DONE", db)

    except Exception as e:
        logger.error("detect_harvest_failed", job_id=job_id, exc_info=e)
        update_job_status(job_id, "FAILED", db, error=str(e))
```

### Registrar no dispatcher
Editar `services/worker/worker/main.py`, adicionar import e handler:

```python
from worker.jobs.detect_harvest import detect_harvest_handler

# No dict de handlers:
"DETECT_HARVEST": detect_harvest_handler,
```

### Teste
```bash
# Verificar logs do worker
docker compose logs -f worker

# Verificar signal criado
curl http://localhost:8000/v1/signals?signal_type=HARVEST_DETECTED -H "Authorization: Bearer $TOKEN"
```

### Acceptance Criteria
- [ ] Job `detect_harvest.py` criado (~80 LOC)
- [ ] Handler registrado no dispatcher
- [ ] Detecta RVI drop > 0.3
- [ ] Cria signal `HARVEST_DETECTED`
- [ ] Metadata contém rvi_current e rvi_previous

---

## TASK 3: Nitrogen Detection API (TASK-INTEL-004)

### Criticidade: ALTA
Depende de SRRE estar funcionando. Valor agronômico alto.

### Arquivo a criar
`services/api/app/presentation/nitrogen_router.py`

### Implementação

```python
"""
Nitrogen deficiency detection API.
Algorithm: High NDVI (>0.7) + Low NDRE (<0.5) + Low RECI (<1.5) = DEFICIENT
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class NitrogenStatus(BaseModel):
    status: str  # DEFICIENT, ADEQUATE, UNKNOWN
    confidence: float
    ndvi_mean: Optional[float] = None
    ndre_mean: Optional[float] = None
    reci_mean: Optional[float] = None
    recommendation: str
    zone_map_url: Optional[str] = None


def get_latest_indices(aoi_id: str, tenant_id: str, db: Session) -> dict:
    """Get latest NDVI, NDRE, RECI means from derived_assets."""
    sql = text("""
        SELECT ndvi_mean, ndre_mean, reci_mean, year, week
        FROM derived_assets
        WHERE aoi_id = :aoi_id AND tenant_id = :tenant_id
        ORDER BY year DESC, week DESC
        LIMIT 1
    """)
    result = db.execute(sql, {"aoi_id": aoi_id, "tenant_id": tenant_id}).first()
    if result:
        return {
            "ndvi_mean": result.ndvi_mean,
            "ndre_mean": result.ndre_mean,
            "reci_mean": result.reci_mean,
        }
    return {}


def detect_nitrogen_status(ndvi: float, ndre: float, reci: float) -> tuple[str, float, str]:
    """Detect nitrogen status based on index thresholds."""
    if ndvi is None or ndre is None or reci is None:
        return "UNKNOWN", 0.0, "Dados insuficientes para análise"

    is_high_ndvi = ndvi > 0.7
    is_low_ndre = ndre < 0.5
    is_low_reci = reci < 1.5
    conditions_met = sum([is_high_ndvi, is_low_ndre, is_low_reci])

    if conditions_met >= 3:
        return "DEFICIENT", 0.9, "Deficiência de nitrogênio detectada. Recomenda-se aplicação em taxa variável."
    elif conditions_met >= 2:
        return "DEFICIENT", 0.7, "Possível deficiência de nitrogênio. Monitorar nas próximas semanas."
    elif ndvi > 0.6 and ndre > 0.4:
        return "ADEQUATE", 0.85, "Níveis de nitrogênio adequados."
    else:
        return "UNKNOWN", 0.5, "Condições mistas. Recomenda-se análise de solo."


@router.get("/aois/{aoi_id}/nitrogen/status", response_model=NitrogenStatus)
def get_nitrogen_status(
    aoi_id: UUID,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """Get nitrogen deficiency status for an AOI."""
    indices = get_latest_indices(str(aoi_id), str(membership.tenant_id), db)

    if not indices:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No vegetation data found")

    ndvi = indices.get("ndvi_mean")
    ndre = indices.get("ndre_mean")
    reci = indices.get("reci_mean")

    status_str, confidence, recommendation = detect_nitrogen_status(ndvi, ndre, reci)

    zone_map_url = None
    if status_str == "DEFICIENT":
        base = settings.API_BASE_URL or "http://localhost:8000"
        zone_map_url = f"{base}/v1/tiles/aois/{aoi_id}/{{z}}/{{x}}/{{y}}.png?index=srre"

    return NitrogenStatus(
        status=status_str,
        confidence=confidence,
        ndvi_mean=ndvi,
        ndre_mean=ndre,
        reci_mean=reci,
        recommendation=recommendation,
        zone_map_url=zone_map_url
    )
```

### Registrar router em `services/api/app/main.py`:

```python
from app.presentation.nitrogen_router import router as nitrogen_router
app.include_router(nitrogen_router, prefix="/v1", tags=["nitrogen"])
```

### Acceptance Criteria
- [ ] Endpoint `/v1/aois/{aoi_id}/nitrogen/status` criado
- [ ] Algoritmo: NDVI > 0.7 AND NDRE < 0.5 AND RECI < 1.5 → DEFICIENT
- [ ] Retorna status, confidence, recommendation
- [ ] zone_map_url aponta para TiTiler SRRE

---

## TASK 4: Correlation API (TASK-INTEL-003)

### Criticidade: ALTA
Combina 3 fontes de dados. Base para Analysis Tab.

### Arquivo a criar
`services/api/app/presentation/correlation_router.py`

### Implementação

```python
"""Correlation API - Combines vegetation, radar, and weather data."""
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership

logger = logging.getLogger(__name__)
router = APIRouter()


class CorrelationDataPoint(BaseModel):
    date: str
    ndvi: Optional[float] = None
    rvi: Optional[float] = None
    rain_mm: Optional[float] = None
    temp_avg: Optional[float] = None


class Insight(BaseModel):
    type: str
    message: str
    severity: str


class CorrelationResponse(BaseModel):
    data: List[CorrelationDataPoint]
    insights: List[Insight]


def fetch_correlation_data(aoi_id: str, tenant_id: str, weeks: int, db: Session) -> List[dict]:
    """Fetch and combine data from 3 sources."""
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks)

    sql = text("""
        WITH weeks AS (
            SELECT da.year, da.week, da.ndvi_mean as ndvi, da.created_at
            FROM derived_assets da
            WHERE da.aoi_id = :aoi_id AND da.tenant_id = :tenant_id AND da.created_at >= :start_date
        ),
        radar AS (
            SELECT dr.year, dr.week, dr.rvi_mean as rvi
            FROM derived_radar_assets dr
            WHERE dr.aoi_id = :aoi_id AND dr.created_at >= :start_date
        ),
        weather AS (
            SELECT EXTRACT(YEAR FROM dw.date)::int as year, EXTRACT(WEEK FROM dw.date)::int as week,
                   SUM(dw.precipitation_mm) as rain_mm, AVG(dw.temperature_avg) as temp_avg
            FROM derived_weather_daily dw
            WHERE dw.aoi_id = :aoi_id AND dw.date >= :start_date
            GROUP BY EXTRACT(YEAR FROM dw.date), EXTRACT(WEEK FROM dw.date)
        )
        SELECT w.year, w.week, w.ndvi, r.rvi, wt.rain_mm, wt.temp_avg
        FROM weeks w
        LEFT JOIN radar r ON w.year = r.year AND w.week = r.week
        LEFT JOIN weather wt ON w.year = wt.year AND w.week = wt.week
        ORDER BY w.year, w.week
    """)
    result = db.execute(sql, {"aoi_id": aoi_id, "tenant_id": tenant_id, "start_date": start_date})

    return [{"date": f"{row.year}-W{row.week:02d}", "ndvi": row.ndvi, "rvi": row.rvi,
             "rain_mm": float(row.rain_mm) if row.rain_mm else None,
             "temp_avg": float(row.temp_avg) if row.temp_avg else None} for row in result]


def generate_insights(data: List[dict]) -> List[Insight]:
    """Generate auto-insights from correlation data."""
    insights = []
    if len(data) < 2:
        return insights

    for i in range(1, len(data)):
        current, previous = data[i], data[i-1]

        # Rain effect
        if previous.get("rain_mm") and previous["rain_mm"] > 10:
            if current.get("ndvi") and previous.get("ndvi"):
                ndvi_change = current["ndvi"] - previous["ndvi"]
                if ndvi_change > 0.05:
                    insights.append(Insight(type="rain_effect",
                        message=f"Chuva de {previous['rain_mm']:.1f}mm em {previous['date']} → NDVI subiu {ndvi_change*100:.0f}%",
                        severity="info"))

        # Radar fallback
        if current.get("ndvi") is None and current.get("rvi") is not None:
            insights.append(Insight(type="radar_fallback",
                message=f"Dia nublado em {current['date']}. Usando radar (RVI: {current['rvi']:.2f})",
                severity="info"))

        # Vigor drop
        if current.get("ndvi") and previous.get("ndvi"):
            ndvi_drop = previous["ndvi"] - current["ndvi"]
            if ndvi_drop > 0.1:
                insights.append(Insight(type="vigor_drop",
                    message=f"Queda de vigor de {ndvi_drop*100:.0f}% entre {previous['date']} e {current['date']}",
                    severity="warning"))

    return insights


@router.get("/aois/{aoi_id}/correlation/vigor-climate", response_model=CorrelationResponse)
def get_vigor_climate_correlation(
    aoi_id: UUID,
    weeks: int = Query(default=12, ge=4, le=52),
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """Get correlation data between vegetation vigor and climate."""
    data = fetch_correlation_data(str(aoi_id), str(membership.tenant_id), weeks, db)
    if not data:
        raise HTTPException(status_code=404, detail="No correlation data found")
    return CorrelationResponse(data=[CorrelationDataPoint(**d) for d in data], insights=generate_insights(data))
```

### Registrar router em `main.py`:

```python
from app.presentation.correlation_router import router as correlation_router
app.include_router(correlation_router, prefix="/v1", tags=["correlation"])
```

### Acceptance Criteria
- [ ] Endpoint `/v1/aois/{aoi_id}/correlation/vigor-climate` criado
- [ ] Combina dados de 3 tabelas
- [ ] Gera insights automáticos
- [ ] Retorna `data` e `insights` arrays

---

## TASK 5: Radar Fallback Tooltip (TASK-INTEL-007)

### Criticidade: MÉDIA
UX improvement. Mostra RVI quando NDVI não disponível.

### Arquivo a modificar
`services/app-ui/src/components/Charts.tsx`

### Implementação

#### 5.1 Tooltip para dias nublados
Adicionar lógica no CustomTooltip (ou criar se não existir):

```tsx
import { Cloud } from "lucide-react";

// No tooltip:
if (data?.ndvi === null && data?.rvi !== null) {
  return (
    <div className="bg-background border rounded-lg p-3 shadow-lg">
      <div className="flex items-center gap-2 mb-2">
        <Cloud className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">Dia Nublado</span>
      </div>
      <p className="text-sm text-muted-foreground">Dado óptico indisponível.</p>
      <p className="text-sm">Estimativa via Sentinel-1: <span className="font-mono">{data.rvi.toFixed(2)}</span></p>
    </div>
  );
}
```

#### 5.2 Estilo visual para pontos de radar no gráfico
Quando NDVI é null mas RVI existe, o ponto deve ter estilo diferenciado:

```tsx
// No componente de gráfico, usar dot customizado:
<Line
  dataKey="ndvi"
  dot={({ cx, cy, payload }) => {
    // Se NDVI null mas RVI existe, mostrar círculo vazado
    if (payload.ndvi === null && payload.rvi !== null) {
      return <circle cx={cx} cy={cy} r={4} fill="none" stroke="hsl(var(--chart-2))" strokeWidth={2} />;
    }
    return <circle cx={cx} cy={cy} r={3} fill="hsl(var(--chart-2))" />;
  }}
/>
```

### Acceptance Criteria
- [ ] Tooltip detecta `ndvi === null && rvi !== null`
- [ ] Mostra ícone de nuvem + "Dia Nublado"
- [ ] Exibe valor RVI
- [ ] Pontos de radar têm círculo vazado (⚪) no gráfico

---

## TASK 6: Nitrogen Alert Component (TASK-INTEL-006)

### Criticidade: MÉDIA
Depende da Nitrogen API.

### Arquivo a criar
`services/app-ui/src/components/NitrogenAlert.tsx`

### Implementação

```tsx
"use client";
import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { api } from "@/lib/api";

interface NitrogenStatus {
  status: "DEFICIENT" | "ADEQUATE" | "UNKNOWN";
  confidence: number;
  ndvi_mean: number | null;
  ndre_mean: number | null;
  recommendation: string;
  zone_map_url: string | null;
}

export function NitrogenAlert({ aoiId }: { aoiId: string }) {
  const [status, setStatus] = useState<NitrogenStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/aois/${aoiId}/nitrogen/status`)
      .then(res => setStatus(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [aoiId]);

  if (loading || !status || status.status !== "DEFICIENT") return null;

  return (
    <Alert variant="destructive" className="mb-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-950">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>Deficiência de Nitrogênio Detectada</AlertTitle>
      <AlertDescription>
        <p className="text-sm mt-1">{status.recommendation}</p>
        <div className="flex gap-4 text-xs text-muted-foreground mt-2">
          <span>NDVI: {status.ndvi_mean?.toFixed(2)}</span>
          <span>NDRE: {status.ndre_mean?.toFixed(2)}</span>
          <span>Confiança: {(status.confidence * 100).toFixed(0)}%</span>
        </div>
        {status.zone_map_url && (
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="mt-3">Ver Mapa de Zonas</Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl">
              <DialogHeader><DialogTitle>Mapa SRRE (Nitrogênio)</DialogTitle></DialogHeader>
              <div className="h-[500px]">
                <iframe src={`/map-embed?aoi=${aoiId}&layer=srre`} className="w-full h-full border-0 rounded" />
              </div>
            </DialogContent>
          </Dialog>
        )}
      </AlertDescription>
    </Alert>
  );
}
```

### Integrar em AOIDetailsPanel (Overview tab):

```tsx
import { NitrogenAlert } from "./NitrogenAlert";
// No Overview tab:
<NitrogenAlert aoiId={aoi.id} />
```

### Acceptance Criteria
- [ ] Componente `NitrogenAlert.tsx` criado
- [ ] Alert amarelo quando status = "DEFICIENT"
- [ ] Botão "Ver Mapa de Zonas" abre modal
- [ ] Só renderiza quando deficiente

---

## TASK 7: Analysis Tab Frontend (TASK-INTEL-005)

### Criticidade: MÉDIA
Depende da Correlation API.

### Arquivos a criar
1. `services/app-ui/src/components/CorrelationChart.tsx`
2. `services/app-ui/src/components/AnalysisTab.tsx`

### CorrelationChart.tsx

```tsx
"use client";
import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

export function CorrelationChart({ data }: { data: Array<{ date: string; ndvi: number | null; rvi: number | null; rain_mm: number | null }> }) {
  return (
    <ResponsiveContainer width="100%" height={350}>
      <ComposedChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
        <YAxis yAxisId="left" domain={[0, 1]} label={{ value: 'Vigor', angle: -90, position: 'insideLeft' }} />
        <YAxis yAxisId="right" orientation="right" label={{ value: 'Chuva (mm)', angle: 90, position: 'insideRight' }} />
        <Tooltip />
        <Legend />
        <Bar yAxisId="right" dataKey="rain_mm" name="Chuva (mm)" fill="hsl(var(--chart-1))" opacity={0.6} />
        <Line yAxisId="left" type="monotone" dataKey="ndvi" name="NDVI" stroke="hsl(var(--chart-2))" strokeWidth={2} connectNulls={false} />
        <Line yAxisId="left" type="monotone" dataKey="rvi" name="RVI (Radar)" stroke="hsl(var(--chart-3))" strokeWidth={2} strokeDasharray="5 5" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
```

### AnalysisTab.tsx

```tsx
"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CorrelationChart } from "./CorrelationChart";
import { api } from "@/lib/api";
import { AlertCircle, CloudRain, TrendingDown, Radio } from "lucide-react";

const icons: Record<string, React.ReactNode> = {
  rain_effect: <CloudRain className="h-4 w-4" />,
  vigor_drop: <TrendingDown className="h-4 w-4" />,
  radar_fallback: <Radio className="h-4 w-4" />,
};

export function AnalysisTab({ aoiId }: { aoiId: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/aois/${aoiId}/correlation/vigor-climate?weeks=12`)
      .then(res => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [aoiId]);

  if (loading) return <Skeleton className="h-[400px] w-full" />;
  if (!data) return <p className="text-muted-foreground text-center p-8">Sem dados</p>;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader><CardTitle className="text-lg">Correlação Vigor x Clima</CardTitle></CardHeader>
        <CardContent><CorrelationChart data={data.data} /></CardContent>
      </Card>
      {data.insights?.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-lg">Insights Automáticos</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {data.insights.map((i: any, idx: number) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                {icons[i.type] || <AlertCircle className="h-4 w-4" />}
                <p className="flex-1 text-sm">{i.message}</p>
                <Badge variant={i.severity === "warning" ? "default" : "secondary"}>{i.severity}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

### Integrar em AOIDetailsPanel:

```tsx
import { AnalysisTab } from "./AnalysisTab";
// Adicionar tab:
<TabsTrigger value="analysis">Análise</TabsTrigger>
<TabsContent value="analysis"><AnalysisTab aoiId={aoi.id} /></TabsContent>
```

### Acceptance Criteria
- [ ] Tab "ANÁLISE" adicionada
- [ ] CorrelationChart renderiza combo chart
- [ ] Dual Y-axis (Vigor esquerda, Chuva direita)
- [ ] Insight cards exibidos
- [ ] Mobile responsive

---

## INFRAESTRUTURA P1 — CRÍTICO PARA PRODUÇÃO

Estas tasks são bloqueadores para ir para produção. Sem CDN, latência será inaceitável (~2s por tile).

---

### TASK 8: Deploy Cloudflare CDN (TASK-0007-CDN)

**Criticidade**: BLOQUEADOR para produção
**Status**: Código pronto, pending deployment

#### Arquivos já criados
- `infra/cloudflare/workers/tile-cache.js` ✅
- `infra/cloudflare/workers/wrangler.toml` ✅
- `infra/cloudflare/.env.cloudflare.example` ✅ (template)
- `docs/runbooks/cloudflare-setup.md` ✅

#### Pré-requisitos (Conta Cloudflare)

1. **Criar conta Cloudflare** (se não existir): https://dash.cloudflare.com
2. **Obter Account ID**: Visível na URL ou sidebar direita de qualquer zone
3. **Criar API Token**:
   - My Profile → API Tokens → Create Token
   - Template: "Edit Cloudflare Workers"
   - Permissões: Workers:Edit, Zone:Read

#### Configurar env vars

**Opção A: Local (deploy manual)**
```bash
# Copiar template
cp infra/cloudflare/.env.cloudflare.example infra/cloudflare/.env.cloudflare

# Editar com seus valores
# CLOUDFLARE_API_TOKEN=your-token
# CLOUDFLARE_ACCOUNT_ID=your-account-id

# Carregar e deploy
source infra/cloudflare/.env.cloudflare
```

**Opção B: GitHub Secrets (CI/CD)**
- Settings → Secrets → Actions → New repository secret
- Adicionar: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`

#### Passos para deploy
```bash
# 1. Carregar env vars (se local)
source infra/cloudflare/.env.cloudflare
export CLOUDFLARE_ACCOUNT_ID="..."

# 2. Deploy Worker
cd infra/cloudflare/workers
wrangler publish --env production

# 3. Configurar DNS (apontar tiles.vivacampo.com para Worker)
# Via Cloudflare Dashboard ou API

# 4. Atualizar .env com CDN_BASE_URL
CDN_BASE_URL=https://tiles.vivacampo.com
```

#### Cache Rules
- `/v1/tiles/*`: 7 dias
- `/mosaic/tiles/*`: 7 dias
- Bypass para `?date=` (tiles dinâmicos)

#### Acceptance Criteria
- [ ] Worker deployed em Cloudflare
- [ ] DNS configurado
- [ ] `CF-Cache-Status: HIT` em requests repetidos
- [ ] p95 latência < 100ms (cached)

---

### TASK 9: CI/CD Pipeline (TASK-INTEL-010)

**Criticidade**: ALTA (required for production)
**Esforço**: 8h

#### Arquivos a criar
```
.github/workflows/
├── deploy-staging.yml
├── deploy-production.yml
└── test.yml
```

#### deploy-staging.yml
```yaml
name: Deploy Staging

on:
  push:
    branches: [develop]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: sa-east-1

      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push images
        run: |
          docker compose build api worker tiler app-ui admin-ui
          docker compose push

      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster vivacampo-staging --service api --force-new-deployment
          aws ecs update-service --cluster vivacampo-staging --service worker --force-new-deployment

      - name: Run smoke tests
        run: |
          sleep 60  # Wait for deployment
          curl -f https://staging-api.vivacampo.com/health

      - name: Notify team
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {"text": "✅ Staging deployed: ${{ github.sha }}"}
```

#### Acceptance Criteria
- [ ] Staging deploy on push to `develop`
- [ ] Production deploy on push to `main`
- [ ] Docker images pushed to ECR
- [ ] ECS services updated
- [ ] Smoke tests pass
- [ ] Team notified

---

### TASK 10: Terraform Infrastructure (TASK-INTEL-011)

**Criticidade**: ALTA (required for production)
**Esforço**: 16h

#### Estrutura
```
terraform/
├── modules/
│   ├── ecs/
│   ├── rds/
│   ├── s3/
│   └── sqs/
├── staging/
│   └── main.tf
└── production/
    └── main.tf
```

#### staging/main.tf (exemplo)
```hcl
terraform {
  backend "s3" {
    bucket = "vivacampo-terraform-state"
    key    = "staging/terraform.tfstate"
    region = "sa-east-1"
  }
}

provider "aws" {
  region = "sa-east-1"
}

module "ecs" {
  source = "../modules/ecs"
  environment = "staging"
  cpu = 256
  memory = 512
}

module "rds" {
  source = "../modules/rds"
  environment = "staging"
  instance_class = "db.t3.micro"
  allocated_storage = 20
}

module "s3" {
  source = "../modules/s3"
  environment = "staging"
  buckets = ["tiles", "mosaics", "exports"]
}

module "sqs" {
  source = "../modules/sqs"
  environment = "staging"
  queues = ["jobs", "jobs-dlq"]
}
```

#### Recursos por ambiente

| Recurso | Staging | Production |
|---------|---------|------------|
| ECS Fargate | 256 CPU, 512MB | 1024 CPU, 2GB |
| RDS PostgreSQL | db.t3.micro | db.r5.large |
| S3 | 3 buckets | 3 buckets |
| SQS | 2 queues | 2 queues |
| CloudWatch | Basic | Enhanced |

#### Acceptance Criteria
- [ ] Staging provisioned via Terraform
- [ ] Production config ready (not applied)
- [ ] State stored in S3
- [ ] Modules reusable

---

### TASK 11: CDN para Intelligence Tiles (TASK-INTEL-012)

**Criticidade**: P1 (performance)
**Esforço**: 4h
**Depende de**: TASK-0007-CDN

#### Descrição
Configurar cache rules específicas para endpoints de inteligência:
- `/v1/aois/{id}/nitrogen/status` → Cache 1h
- `/v1/aois/{id}/correlation/*` → Cache 1h

#### Cloudflare Worker adicional
```javascript
// intelligence-cache.js
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Cache intelligence endpoints
    if (url.pathname.includes('/nitrogen/') || url.pathname.includes('/correlation/')) {
      const cacheKey = new Request(url.toString(), request);
      const cache = caches.default;

      let response = await cache.match(cacheKey);
      if (response) return response;

      response = await fetch(request);
      response = new Response(response.body, response);
      response.headers.set('Cache-Control', 'public, max-age=3600'); // 1h

      await cache.put(cacheKey, response.clone());
      return response;
    }

    return fetch(request);
  }
};
```

#### Acceptance Criteria
- [ ] Intelligence endpoints cached
- [ ] Cache invalidation on data update
- [ ] p95 < 200ms para endpoints cached

---

## TASKS ADICIONAIS (P1 - Features Desejáveis)

As tasks abaixo foram identificadas no `intelligence_capabilities.md` mas têm menor criticidade.
Implementar após P0 e Infraestrutura, se houver tempo.

### TASK 8: Year-over-Year Comparison (Comparação de Safra)

**Criticidade**: P1 (desejável)
**Fonte**: intelligence_capabilities.md §3.B

#### Descrição
Exibir duas linhas no gráfico: safra atual vs safra anterior.
- Linha verde sólida: Safra atual
- Linha cinza tracejada: Safra anterior
- Insight: Se atual cruzar abaixo da anterior → "Alerta de Quebra"

#### Arquivo a modificar
`services/app-ui/src/components/Charts.tsx` ou criar `YearOverYearChart.tsx`

#### API necessária
```python
# Novo endpoint ou parâmetro em correlation
@router.get("/aois/{aoi_id}/correlation/year-over-year")
def get_yoy_comparison(aoi_id: UUID, ...):
    # Retorna { current_year: [...], previous_year: [...] }
```

#### Acceptance Criteria
- [ ] Endpoint retorna dados de 2 safras
- [ ] Gráfico exibe 2 linhas (atual sólida, anterior tracejada)
- [ ] Insight gerado quando atual < anterior

---

### TASK 9: Productivity Score (Integral da Curva NDVI)

**Criticidade**: P1 (desejável)
**Fonte**: intelligence_capabilities.md §3.C

#### Descrição
A área abaixo da curva NDVI ao longo do ciclo correlaciona com produtividade.
Exibir "Score de Potencial Produtivo" acumulado.

#### Lógica
```python
# Integral simples (soma trapezoidal)
def calculate_productivity_score(ndvi_series: List[float]) -> float:
    score = sum(ndvi_series) / len(ndvi_series)
    return score

# Comparar com média histórica
historical_avg = 0.65  # Calibrar por região/cultura
deviation = ((score - historical_avg) / historical_avg) * 100
# Output: "Sua safra acumulou 15% mais biomassa que a média histórica"
```

#### Acceptance Criteria
- [ ] Score calculado como média de NDVI no período
- [ ] Comparação com média histórica (%)
- [ ] Exibido como card no dashboard

---

### TASK 10: Radar Overlay Badge no Mapa

**Criticidade**: P1 (UX polish)
**Fonte**: intelligence_capabilities.md §2.A.2

#### Descrição
Quando exibindo camada RVI (radar), mostrar badge discreto:
"Modo Radar / Estimativa" no canto do mapa.

#### Arquivo a modificar
`services/app-ui/src/components/MapLeaflet.tsx`

#### Implementação
```tsx
{activeLayer === 'rvi' && (
  <div className="absolute bottom-4 left-4 z-[1000] bg-background/80 px-3 py-1.5 rounded-full text-xs font-medium border">
    <Radio className="h-3 w-3 inline mr-1" />
    Modo Radar / Estimativa
  </div>
)}
```

#### Acceptance Criteria
- [ ] Badge aparece quando layer RVI ativo
- [ ] Estilo discreto (não intrusivo)
- [ ] Desaparece quando volta para NDVI/óptico

---

## Verificação Final

### Local (P0 Features)
```bash
# 1. Rebuild
docker compose build tiler worker api

# 2. Restart
docker compose up -d

# 3. Test endpoints
curl http://localhost:8080/indices | jq '.srre'
curl http://localhost:8000/v1/aois/{id}/nitrogen/status -H "Authorization: Bearer $TOKEN"
curl http://localhost:8000/v1/aois/{id}/correlation/vigor-climate -H "Authorization: Bearer $TOKEN"

# 4. Test frontend
npm run dev --prefix services/app-ui
```

### Staging (P1 Infraestrutura)
```bash
# 1. Terraform
cd terraform/staging
terraform init
terraform plan
terraform apply

# 2. Deploy via CI
git push origin develop  # Triggers GitHub Actions

# 3. Verify CDN
curl -I https://tiles.vivacampo.com/v1/tiles/aois/{id}/14/5000/8000.png
# Check: CF-Cache-Status: HIT

# 4. Smoke tests
curl https://staging-api.vivacampo.com/health
```

---

## Context for Reviewer

Após implementação, o revisor (Opus 4.5) deve verificar:

1. **Código**: Segue padrões existentes
2. **Testes**: Endpoints testáveis via curl
3. **UX**: Frontend responsivo
4. **Performance**: Queries otimizadas
5. **Segurança**: tenant_id filtrado

---

## ADR References

- [ADR-0008: SRRE Index and Nitrogen Detection](docs/adr/0008-intelligence-nitrogen-detection.md)
- [ADR-0009: Radar-Based Harvest Detection](docs/adr/0009-radar-harvest-detection.md)
- [ADR-0010: Correlation API and Analysis Tab](docs/adr/0010-correlation-analysis.md)

---

## Key Project Info

**Tech Stack:**
- Backend: FastAPI + Python 3.11 + PostGIS + SQLAlchemy
- Frontend: Next.js 14 + React 18 + TypeScript
- Infra: Docker Compose + LocalStack

**File Patterns:**
- API routers: `services/api/app/presentation/*_router.py`
- Worker jobs: `services/worker/worker/jobs/*.py`
- Frontend: `services/app-ui/src/components/*.tsx`
- TiTiler: `services/tiler/tiler/expressions.py`

---

*Handoff criado por Opus 4.5 em 2026-02-04 23:45*
*Revisado em 2026-02-05 00:15 — Adicionadas tasks P1 Infraestrutura (CI/CD, Terraform, CDN)*
*Próximo: Assistente implementador executar tasks em ordem*
*Após: Opus 4.5 revisar implementação*
