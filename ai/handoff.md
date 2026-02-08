# Handoff — 2026-02-07 15:16

## Current Objective
Fase 3 (Post-Map First) em andamento: remover sidebar e preparar cards espaciais + hardening de performance/a11y.

## Session Note
- TASK-MOBILE sprint encerrado. Documentação e handoff atualizados.

---

## Progress Log

- 2026-02-08: **Landing v2 — Base scaffold**
  - Criada rota paralela `/landing-v2` copiando `page.tsx` para preservar a home atual.
  - Adicionado `Experience.tsx` (skeleton) com `useScroll`/`useFrame` e ranges de camera.
  - Observacao: `ai/tasks.md` foi relido (arquivo gitignored) e contem backlog atualizado.
  - Proxima acao: integrar `ScrollControls` no `Hero3DCanvas` e wire `Experience` na v2.
  - Backlog atualizado: adicionadas tasks `TASK-LANDING-V2-0001` e `TASK-LANDING-V2-0002` em `ai/tasks.md`.
  - Implementacao iniciada: criados `Hero3DCanvasV2.tsx` e `Hero3DV2.tsx` usando `ScrollControls` e `Experience`.
  - `/landing-v2` agora usa `Hero3DV2` e nao importa `LandingDesktopEffects` para evitar GSAP no v2.
  - Conteudo principal migrado para `<Scroll html>` via `LandingScrollContentV2`.
  - Ajuste: `ScrollControls` agora com `pages=6`.
  - Fallback: `Hero3DV2` renderiza conteudo diretamente quando `prefersReducedMotion`.
  - Ajustes visuais no hero v2: overlay de contraste, vignette e alinhamento para esquerda no desktop.
  - `ScrollControls` agora calcula `pages` dinamicamente usando `scrollHeight` com ajuste (`-0.95`) para remover espaco extra.
  - `Experience` agora inclui planos 3D basicos (farm/micro) com fade por scroll para coreografia inicial.
  - Parallax leve adicionado: planos duplos para farm/micro com offsets e fade independente.
  - Wow pass 1: camera snap + focus lock por secoes e fog leve para profundidade.
  - TASK-LANDING-V2-0002 concluida; logger de metricas removido.
  - Landing v2 promovida para `/` (page.tsx). Componentes v2 mesclados em Hero3D/Hero3DCanvas e LandingScrollContent.
  - Rota `/landing-v2` removida e arquivos v2 deletados para manter estrutura.
  - CSP ajustado para permitir `worker-src 'self' blob:` (evita bloqueio de Web Worker no `useCompressedTexture`).
  - Coreografia inicial de camera por secoes (hero -> transicao -> farm -> micro) em `Experience.tsx`.
  - Proxima acao: validar ranges e ajustar posicoes de camera conforme feedback.

- 2026-02-08: **ADMIN UI — Plano de implementação criado**
  - Documento de plano baseado em `ai/ADMIN_UI_PROPOSAL.md`.
  - Arquivo: `ai/ADMIN_UI_IMPLEMENTATION_PLAN.md`.
  - Atualizado com stack, design system, metas, checklist e matriz de conciliacao para cobrir 100% da proposta.
  - Adicionado bloco de endpoints sugeridos e contratos detalhados por fase.
  - Contratos ajustados para refletir o backend atual e stack alinhada ao `services/admin-ui/package.json`.
  - Stubs OpenAPI criados em `docs/openapi/admin-ui-stubs.yaml`.
  - Stubs futuros separados em `docs/openapi/admin-ui-stubs-future.yaml`.
  - Proxima acao: validar escopo MVP e confirmar endpoints backend.

- 2026-02-08: **ADMIN UI — Seção de tasks atualizada**
  - Seção "Admin UI — Execution Order" detalhada em `ai/tasks.md` e alinhada ao plano de implementação.
  - Proxima acao: escolher o próximo task P0 para execução.

- 2026-02-08: **ADMIN UI — Tasks de execução priorizadas**
  - Repriorizadas e quebradas em subtasks as entregas do Admin UI.
  - Seção "Admin UI — Execution Order (Suggested)" criada em `ai/tasks.md` com P0/P1/P2.
  - Novas tasks: `TASK-ADMIN-0001` a `TASK-ADMIN-0012`.
  - Proxima acao: aprovar prioridades sugeridas e escolher a primeira task P0 para implementação.

- 2026-02-08: **ADMIN UI — TASK-ADMIN-0001 (Auth guard base + redirects)**
  - Criado `AdminAuthGate` para centralizar verificação de token/role e redirects.
  - Aplicado o guard nas páginas: dashboard, audit, jobs, tenants, missing-weeks.
  - Páginas agora recebem token via gate para chamadas API.
  - Arquivos: `services/admin-ui/src/components/AdminAuthGate.tsx`,
    `services/admin-ui/src/app/dashboard/page.tsx`,
    `services/admin-ui/src/app/audit/page.tsx`,
    `services/admin-ui/src/app/jobs/page.tsx`,
    `services/admin-ui/src/app/tenants/page.tsx`,
    `services/admin-ui/src/app/missing-weeks/page.tsx`.
  - Proxima acao: validar redirects no browser e seguir para `TASK-ADMIN-0002` (layout shell).

- 2026-02-08: **ADMIN UI — Tailwind/PostCSS fix (login sem estilos)**
  - Adicionado `postcss.config.js` em `services/admin-ui` para habilitar Tailwind.
  - Proxima acao: reiniciar `npm run dev --prefix services/admin-ui` e recarregar `/admin/login`.

- 2026-02-08: **ADMIN UI — TASK-ADMIN-0002 (Layout shell: header + sidebar)**
  - Criado `AdminShell` com header fixo + sidebar existente.
  - Agrupadas rotas admin em `src/app/(admin)` para aplicar layout a dashboard, audit, jobs, tenants, missing-weeks e `/admin`.
  - Novo layout: `services/admin-ui/src/app/(admin)/layout.tsx`.
  - Arquivos: `services/admin-ui/src/components/AdminShell.tsx`.
  - Proxima acao: validar visual e spacing das páginas dentro do shell.

- 2026-02-08: **ADMIN UI — TASK-ADMIN-0003 (Audit log page refinada)**
  - Removido header duplicado e alinhado a pagina de auditoria ao `AdminShell`.
  - Conteudo agora usa container `max-w-7xl` e cabecalho interno simples.
  - Arquivo: `services/admin-ui/src/app/(admin)/audit/page.tsx`.
  - Proxima acao: validar visual do Audit Log dentro do shell.

- 2026-02-08: **ADMIN UI — TASK-ADMIN-0004 (Tenants list + status update)**
  - Ajustado status para `ACTIVE|SUSPENDED` conforme backend.
  - Adicionada edicao de status via PATCH `/v1/admin/tenants/{id}` com feedback de erro.
  - Header duplicado removido; pagina alinhada ao `AdminShell`.
  - Arquivo: `services/admin-ui/src/app/(admin)/tenants/page.tsx`.
  - Proxima acao: validar UI/fluxo de update no browser.

- 2026-02-08: **ADMIN UI — TASK-ADMIN-0005 (Jobs list + filters)**
  - Adicionados filtros de `job_type` e `limit` na lista de jobs.
  - Header duplicado removido; pagina alinhada ao `AdminShell`.
  - Arquivo: `services/admin-ui/src/app/(admin)/jobs/page.tsx`.
  - Proxima acao: validar filtros e limite com token.

- 2026-02-08: **ADMIN UI — TASK-ADMIN-0006 (Missing weeks + reprocess)**
  - Header duplicado removido; pagina alinhada ao `AdminShell`.
  - Controles de busca e reprocessamento mantidos com layout unificado.
  - Arquivo: `services/admin-ui/src/app/(admin)/missing-weeks/page.tsx`.
  - Proxima acao: validar reprocessamento com token.

- 2026-02-08: **ADMIN UI — TASK-ADMIN-0010 (Status HUD)**
  - Dashboard agora faz polling a cada 5s para health + queues.
  - Adicionado bloco de Status HUD por job_type/status.
  - Header duplicado removido; pagina alinhada ao `AdminShell`.
  - Arquivo: `services/admin-ui/src/app/(admin)/dashboard/page.tsx`.
  - Proxima acao: validar HUD com token.

- 2026-02-08: **ADMIN UI — TASK-ADMIN-0011 (Providers status widget)**
  - Dashboard agora carrega `/v1/admin/providers/status` e renderiza cards por provider.
  - Exibe cache info quando presente e tolera valores nulos.
  - Arquivo: `services/admin-ui/src/app/(admin)/dashboard/page.tsx`.
  - Proxima acao: validar providers widget com token.

- 2026-02-08: **ADMIN UI — TASK-ADMIN-0012 (Tenant members admin)**
  - Criada pagina `/admin/tenant/members` com lista, convite, update de role/status e settings.
  - Endpoints: `/v1/app/admin/tenant/members`, `/invite`, `/role`, `/status`, `/settings`.
  - Arquivo: `services/admin-ui/src/app/(admin)/tenant/members/page.tsx`.
  - Proxima acao: validar fluxos com token.

- 2026-02-08: **ADMIN UI — TASK-ADMIN-0020 (Command Palette)**
  - Adicionado Command Palette com Ctrl/⌘+K e lista de atalhos.
  - Trigger incluido no header do AdminShell.
  - Arquivos: `services/admin-ui/src/components/CommandPalette.tsx`,
    `services/admin-ui/src/components/AdminShell.tsx`.
  - Proxima acao: validar navegação pelo palette.

- 2026-02-08: **ADMIN UI — Design System Plan (tasks detalhadas)**
  - Plano detalhado criado em `ai/ADMIN_DESIGN_SYSTEM_IMPLEMENTATION_PLAN.md`.
  - Tasks de design system adicionadas ao `ai/tasks.md` (TASK-DS-0001..0203).
  - Proxima acao: iniciar Fase 0 (mobile-first urgente).

- 2026-02-07: **NAVBAR — Implementation plan drafted**
  - Criado plano de implementação baseado no `ai/NAV_AUDIT_REPORT.md`.
  - Arquivo: `ai/NAVBAR_IMPLEMENTATION_PLAN.md`.
  - Proxima acao: usuario revisar o plano e aprovar execução.

- 2026-02-07: **NAVBAR — Implementação aplicada**
  - Ajustado contraste do header para `bg-black/80`.
  - Links desktop receberam `min-h-[44px]`/`min-w-[44px]`, padding e `aria-label`.
  - Link Login e CTA “Começar grátis” com min height explícito.
  - Menu mobile recebeu `aria-labelledby` e título sr-only.
  - Links do menu mobile com `min-h-[44px]` + `aria-label`.
  - MobileNav: `gap-2`, `min-h-[44px]`, `aria-current`, `aria-label` e indicador visual de ativo.
  - Arquivos: `services/app-ui/src/components/landing/LandingHeader.tsx`, `services/app-ui/src/components/MobileNav.tsx`.
  - Proxima acao: validar visual e a11y em mobile/desktop (touch targets, contraste, screen reader).

- 2026-02-07: **NAVBAR — A11y/foco refinados**
  - Adicionadas utilidades `.min-h-touch` e `.min-w-touch` em `globals.css`.
  - Links e CTAs do header receberam foco visível com ring (desktop e mobile menu).
  - MobileNav recebeu foco visível com ring verde.
  - Arquivos: `services/app-ui/src/app/globals.css`, `services/app-ui/src/components/landing/LandingHeader.tsx`, `services/app-ui/src/components/MobileNav.tsx`.
  - Proxima acao: validação visual/a11y em device real ou DevTools (contraste + foco).

- 2026-02-07: **NAVBAR — Validação A11y (Lighthouse)**
  - Lighthouse A11y (mobile) em `http://localhost:3002`: score 1.00 (sem falhas).
  - Relatório: `ai/lighthouse-a11y.json`.
  - Lighthouse desktop não concluiu (timeout); precisa re-run se necessário.
  - Proxima acao: validação visual manual (contraste/foco) e re-tentar Lighthouse desktop se desejado.

- 2026-02-08: **NAVBAR — Contraste ajustado e Lighthouse desktop**
  - Corrigido contraste em `services/app-ui/src/app/page.tsx` (`text-gray-500` -> `text-gray-400`).
  - Lighthouse A11y (desktop) em `http://localhost:3002`: score 1.00 (sem falhas).
  - Relatório: `ai/lighthouse-a11y-desktop.json`.
  - Proxima acao: validação visual manual se necessário.

- 2026-02-07: **TASK-MOBILE-001 — Browser validation attempt**
  - Tried `npm run dev` for app-ui; server responded with Next.js error "Cannot find the middleware module".
  - Could not fetch page HTML from localhost to confirm `<head>` meta.
  - Proxima acao: investigar middleware setup for app-ui dev server and retry validation.

- 2026-02-07: **TASK-MOBILE-001 — Browser validation (port 3002)**
  - Dev server iniciado em `http://localhost:3002`.
  - `<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">` presente.
  - `<meta name="theme-color" content="#050505">` presente.
  - Apple web app meta tags presentes (`apple-mobile-web-app-*`).
  - Body com `overflow-x-hidden` confirmado.
  - Proxima acao: seguir para `TASK-MOBILE-002`.

- 2026-02-07: **TASK-MOBILE-002 — Touch targets baseline (in progress)**
  - Applied `min-h-[44px]` to inputs/selects/textarea in `services/app-ui/src/app/globals.css`.
  - Added `min-height/width: 44px` for `input[type='checkbox']` and `input[type='radio']`.
  - Enforced 44px min touch size for all `button` and `a` elements in `services/app-ui/src/app/globals.css`.
  - Updated action icon buttons in AOI list to real `<button>` elements with 44px min size.
  - Ensured nav links and CTAs in `LandingHeader` and `ClientLayout` are 44px touch targets.
  - Added 44px min height to toggle labels in `MapControlCluster`.
  - Validated landing page output in dev server on port 3002.
  - Updated landing footer links and analytics filters/refresh buttons to meet 44px touch size.
  - Updated AI Assistant sidebar link/button touch targets.
  - Updated auth pages (login/signup/forgot/reset) and legal/contact links to meet 44px touch size.
  - Updated farms detail page buttons/links to ensure 44px touch targets in header, actions, and modals.
  - Updated signals details page links and acknowledge button.
  - Updated vision pages back links and offline CTA button.
  - Updated settings preference switch to meet 44px touch target.
  - Added 44px touch targets to AOI list header, filter chips, and “Limpar busca”.
  - Ran final dev-server visual validation on port 3002 (landing page rendered as expected).
  - Added `inputMode`/`autoComplete` to auth/contact/invite forms and search inputs.
  - Added numeric input keyboard hints for split controls.
  - Marked `TASK-MOBILE-003` as completed in `ai/tasks.md`.
  - Added focus trap, ESC close, and backdrop click for landing mobile menu.
  - Proxima acao: validar UX em device real e revisar event-specific interactions (map overlays).

- 2026-02-07: **TASK-MOBILE-007 — Mobile menu validation (Playwright)**
  - Dev server iniciado em `http://localhost:3002` (port 3002).
  - Validado via Playwright (viewport 375x812): `aria-expanded` muda para `true` ao abrir.
  - `aria-hidden` alterna `false` (aberto) e `true` (fechado).
  - Focus trap confirmado (focus permanece dentro do menu após `Tab`).
  - ESC fecha o menu.
  - `TASK-MOBILE-007` marcado como concluida em `ai/tasks.md`.

- 2026-02-07: **TASK-MOBILE-004 — Breakpoint testing suite (in progress)**
  - Criado teste Playwright `tests/e2e/mobile-responsiveness.spec.ts`.
  - Cobertura de breakpoints: 320, 375, 414, 768, 1024, 1440.
  - Valida ausencia de scroll horizontal, tamanho base de fonte >= 16px, e touch targets >= 44x44.
  - Executado `npx playwright test tests/e2e/mobile-responsiveness.spec.ts --project "Mobile Chrome" --project "Mobile Safari"` com app-ui em `http://localhost:3002`.
  - Resultado: 2 testes passaram (Mobile Chrome + Mobile Safari).
  - `TASK-MOBILE-004` marcado como concluida em `ai/tasks.md`.

- 2026-02-07: **TASK-MOBILE-005 — Touch optimization (completed)**
  - Adicionado `scroll-behavior: smooth` em `html` e `touch-action: manipulation` + `overscroll-behavior-y: contain` no `body` em `services/app-ui/src/app/globals.css`.
  - Atualizado `tests/e2e/mobile-responsiveness.spec.ts` para validar scroll-behavior/touch-action e tolerar `overscroll-behavior-y` ausente em WebKit.
  - Playwright executado (`Mobile Chrome`, `Mobile Safari`) com app-ui em `http://localhost:3002`: 2 testes passaram.
  - `TASK-MOBILE-005` marcado como concluida em `ai/tasks.md`.

- 2026-02-07: **TASK-MOBILE-006 — Responsive images (completed)**
  - `Hero3D` fallback agora usa `next/image` com `fill`, `sizes` e `priority`.
  - Imagens da landing (`farm-zoom`, `micro-analysis`, `devices-mockup`) agora definem `sizes` para servir variantes responsivas.
  - `TASK-MOBILE-006` marcado como concluida em `ai/tasks.md`.

- 2026-02-07: **TASK-MOBILE-008 — Lighthouse mobile audit (in progress)**
  - Rodado Lighthouse mobile em dev server (`http://localhost:3002`): Performance 47, A11y 96, Best Practices 92, SEO 100.
  - Métricas (dev): LCP 14.1s, CLS 0.106, TBT 1230ms.
  - Otimizações aplicadas para reduzir JS em mobile: cenas 3D/efeitos agora lazy + desktop-only via dynamic imports (`Hero3DCanvas`, `LandingDesktopEffects`, `FarmSceneLazy`, `MicroSceneLazy`) e fallback hero estático com `next/image`.
  - Ajustes de types para liberar build: `Charts.tsx` (dot), `VideoTracker.tsx` (querySelectorAll tipado), `MapLeaflet.tsx` (originalEvent), `VectorTileLayer.tsx` (rendererFactory).
  - Build production liberado após excluir `src/stories` e `vitest.config.ts` no `services/app-ui/tsconfig.json` e corrigir `/map-embed` (client-only).
  - Lighthouse mobile em build (next start, `http://localhost:3002`): Performance 91, LCP 2.8s, TBT 30ms.
  - LCP element identificado via PerformanceObserver (Playwright): `section#hero > div.relative.z-20 > h1.text-balance.text-3xl` (heading principal).
  - Otimizacoes que ajudaram: `content-visibility: auto` nas seções abaixo do hero.
  - Tentativas sem ganho (revertidas): override de fonte do h1 no mobile.
  - Decisão: LCP 2.8s aceito como baseline (sem reduzir o “wow”).
  - `TASK-MOBILE-008` marcado como concluida em `ai/tasks.md`.

- 2026-02-07: **TASK-MOBILE-010 — A11y + WCAG 2.1 AA (automated)**
  - Corrigidos landmarks com `<main>` e contraste/links em: `login`, `signup`, `contact`, `terms`, `privacy`.
  - Ajustes de contraste: textos cinza para `gray-700`, links com `underline` e botão contato `bg-green-700`.
  - aXe (Playwright, viewport 375x812) em `/`, `/login`, `/signup`, `/contact`, `/terms`, `/privacy`: 0 violations.
  - Pendências manuais: WAVE extension e teste com screen reader (VoiceOver/TalkBack).

- 2026-02-07: **TASK-MOBILE-009 — Mobile-first docs (completed)**
  - Criado `docs/MOBILE_FIRST_GUIDELINES.md` com checklist, anti-patterns, targets e guia de validação.
  - README principal atualizado com link para o guia.
  - `TASK-MOBILE-009` marcado como concluida em `ai/tasks.md`.

- 2026-02-07: **TASK-MOBILE-001 — Mobile-first base setup (in progress)**
  - Added mobile-first breakpoints and spacing helper `touch: 44px` in `services/app-ui/tailwind.config.js`.
  - Added `overflow-x-hidden` on app body to prevent horizontal scroll.
  - Viewport/themeColor/appleWebApp metadata already present in `services/app-ui/src/app/layout.tsx`.
  - Proxima acao: validar visual no browser e confirmar meta viewport no `<head>`.

- 2026-02-07: **Session closeout**
  - Pytest (API) passou com `.env` local (`pytest -q`).
  - Dashboard de analytics ajustado com ordenacao/filtro por fase; eventos/labels refinados.
  - Task criada: `TASK-SPATIAL-0039` (filtros reais por data via API + UI).
  - Proxima acao: implementar `TASK-SPATIAL-0039`.

- 2026-02-07: **TASK-SPATIAL-0038 — Analytics dashboard (backend + eventos)**
  - TrackGoal agora envia eventos para API (`/v1/app/analytics/events`) com fase (F1/F2/F3).
  - Endpoint `/v1/app/analytics/adoption` agregado a partir do audit_log; dashboard agora consome backend.
  - Novos eventos mapeados: `aoi_selected`, `aoi_created`, `aoi_batch_created` (alem de onboarding/zoom/bottom sheet).
  - Teste unitario app-ui atualizado (rodado: `npm run test:unit --prefix services/app-ui`).
  - Testes API adicionados; pytest falhou por falta de env vars (jwt/sqs/db/etc).
  - Ajustado painel para exibir fase por evento (F1/F2/F3) e refinar labels/ordem.
  - Adicionadas opcoes de ordenacao (volume/alfabetica) e filtro por fase.
  - Proxima acao: validar eventos em ambiente real e garantir que o volume do audit_log esta aceitavel.

- 2026-02-07: **TASK-SPATIAL-0039 — Filtros reais de analytics (criado)**
  - Task criada para adicionar filtros reais por data no dashboard (API + UI).
  - Proxima acao: implementar query params em `/v1/app/analytics/adoption` e conectar no frontend.

- 2026-02-07: **TASK-SPATIAL-0038 — Analytics dashboard (concluida)**
  - Criada pagina `/analytics` com painel de adocao (eventos chave + metricas por fase F1/F2/F3).
  - `trackGoal` agora guarda snapshot local (localStorage) para contagens e ultimo evento.
  - Adicionado item de navegacao Analytics para tenant/system admin.
  - Proxima acao: validar eventos reais no fluxo (onboarding, bottom sheet, zoom) e ajustar mapeamento se necessario.

- 2026-02-07: **TASK-SPATIAL-0037 — Perf + A11y hardening (concluida)**
  - Lighthouse mobile em `/farms`: LCP 2.3s, Perf 0.75, A11y 0.93 (dev server local).
  - Acceptance finalizada; status atualizado para concluida.
  - Proxima acao: iniciar `TASK-SPATIAL-0038` (Analytics dashboard).

- 2026-02-07: **TASK-SPATIAL-0037 — Perf + A11y hardening (parcial)**
  - Adicionado foco visivel global e reducao de blur/animacoes para usuarios com preferencia de reduced motion/transparency.
  - LCP target ainda nao validado.
  - Proxima acao: rodar Lighthouse mobile e ajustar LCP (<2.5s) conforme necessario.

- 2026-02-07: **TASK-SPATIAL-0036 — Full spatial cards**
  - ClientLayout agora renderiza paginas de gestao como cards flutuantes sobre o mapa (MapLayout + MapComponent).
  - Header/nav compactos migrados para overlays; mapa permanece visivel.
  - Proxima acao: iniciar `TASK-SPATIAL-0037` (Perf + A11y hardening).

- 2026-02-07: **Sprint 4 encerrado**
  - Concluido Sprint 4 (Fase 2): `TASK-SPATIAL-0023`, `0030`, `0031`, `0032`.
  - Proxima acao: iniciar Fase 3 com `TASK-SPATIAL-0035` (sidebar removal) e seguir para `0036`.

- 2026-02-07: **TASK-SPATIAL-0035 — Sidebar removal**
  - Sidebar persistente removida no mapa da fazenda; menu compacto agora abre painel overlay.
  - Menu acessivel no topo com toggle e backdrop para fechar.
  - Proxima acao: iniciar `TASK-SPATIAL-0036` (Full spatial cards).

- 2026-02-07: **TASK-SPATIAL-0032 — Service Worker cache de geometrias**
  - Configurado runtime caching no PWA: geometrias (AOIs) com cache-first (24h) e dados dinamicos com network-first.
  - Cache invalidado por deploy via `cacheId` com build/commit.
  - Proxima acao: revisar Sprint 4 concluido e decidir Fase 3 (Post-Map First).

- 2026-02-07: **TASK-SPATIAL-0031 — Bottom Sheet GPU + containment**
  - Aplicado `contain: layout` e `will-change` condicional durante drag no BottomSheet.
  - Animacao continua via `transform` para reduzir reflow.
  - Proxima acao: executar `TASK-SPATIAL-0032` (Service Worker cache).

- 2026-02-07: **TASK-SPATIAL-0030 — Network-aware tile loading**
  - Auto-selecao do mapa base por tipo de conexao (4G+ usa vector; 2G/3G cai para raster).
  - Override manual preservado quando usuario escolhe outro base layer.
  - Indicador de modo economico mantido quando vector nao esta permitido.
  - Proxima acao: executar `TASK-SPATIAL-0031` (Bottom Sheet containment) ou `TASK-SPATIAL-0032` (Service Worker cache).

- 2026-02-07: **TASK-SPATIAL-0023 — Leaflet Vector Tiles (POC)**
  - Adicionado `leaflet.vectorgrid` e camada vetorial com tiles Protomaps no app-ui.
  - Fallback automatico para raster em conexoes lentas (2G/3G) com aviso discreto.
  - Plano atualizado com estrategia de vector tiles e fallback.
  - Proxima acao: executar `TASK-SPATIAL-0030` (network-aware loading refinado) ou `TASK-SPATIAL-0031` (Bottom Sheet containment).

- 2026-02-07: **Sprint 4 iniciado + Post-Map First alinhado**
  - Sprint 4 (Fase 2) iniciado com foco em: `TASK-SPATIAL-0023`, `0030`, `0031`, `0032`.
  - Post-Map First (Fase 3) alinhado como proxima etapa: `TASK-SPATIAL-0035`–`0038`.
  - Proxima acao: escolher a primeira task de Sprint 4 para implementacao (recomendado: `TASK-SPATIAL-0023`).

- 2026-02-07: **Encerramento — Sprint 1 e Sprint 3**  
  - Sprint 1 concluido (0010, 0011, 0021, 0033, 0024).  
  - Sprint 3 concluido (0012, 0022, 0034, 0013).  
  - Testes: `npm run test:unit` (14 arquivos, 26 testes OK) e `npm run test:storybook` (9 arquivos, 3 testes OK).  
  - Documentos atualizados: `ai/tasks.md` (status), `ai/sessions/2026-02-07-1737.md` (log).  
  - Proxima acao: iniciar Sprint 2 (hardening a11y/perf) ou Sprint 4 (vector tiles, network-aware loading, SW cache).

- 2026-02-07: **TASK-SPATIAL-0013 — Bottom Sheet (audit)**  
  - Nao ha implementacao encontrada em `design-system/components/spatial/BottomSheet/` (pasta inexistente).  
  - Apenas referencias de design/spec em `design-system/components/README.md` e `design-system/FIGMA_GUIDE.md`.  
  - Proxima acao: implementar Bottom Sheet MVP conforme `ai/tasks.md` (gestos, focus trap, ESC, safe area) + stories/tests.

- 2026-02-07: **TASK-SPATIAL-0013 — Bottom Sheet (implementado)**  
  - Criado `design-system/components/spatial/BottomSheet` com gestos up/down, foco via Radix Dialog, ESC para fechar e safe area iOS.  
  - Adicionadas stories (Peek/Half/Full/Gestures) e testes unitarios basicos.  
  - Export atualizado em `design-system/components/index.ts`.  
  - Removido Radix Dialog por implementacao local (portal + focus trap) para evitar dependencia ausente em testes.  
  - Testes executados: `npm run test:unit` (14 arquivos, 26 testes OK) e `npm run test:storybook` (9 arquivos, 3 testes OK).  
  - Nota: Vitest/Storybook avisou sobre `optimizeDeps` (reload do Vite ao otimizar `react-dom`).  
  - Proxima acao: opcional — adicionar `react-dom` em `optimizeDeps.include` se quiser eliminar o warning.

- 2026-02-07: **TASK-SPATIAL-0010 — Command Center (audit + fixes)**  
  - Ajustado `CommandCenter` com `aria-activedescendant` e ids por opção para listbox acessível.  
  - Botão de abertura agora tem `aria-label` + `aria-controls`.  
  - Corrigido edge case de lista vazia nas setas (evita `activeIndex = -1`).  
  - Testes executados: `npm run test:unit` (10 arquivos, 17 testes OK) e `npm run test:storybook` (8 arquivos, 3 testes OK).  
  - Proxima acao: nenhuma.

- 2026-02-07: **TASK-SPATIAL-0011 — Field Dock (audit + fixes)**  
  - Adicionado Tooltip real (Radix) para acoes do FieldDock, substituindo `title`.  
  - Acoes agora incluem `aria-label` e `aria-disabled` para melhor a11y.  
  - Adicionado `cursor-pointer` nos botoes habilitados.  
  - Testes executados: `npm run test:unit` (10 arquivos, 17 testes OK) e `npm run test:storybook` (8 arquivos, 3 testes OK).  
  - Proxima acao: nenhuma.

- 2026-02-07: **Testes app-ui (rerun)**  
  - `npm run test:unit` inicialmente falhou com timeout/EPIPE; re-run com timeout maior passou (10 arquivos, 17 testes OK).  
  - `npm run test:storybook` passou (8 arquivos, 3 testes OK).  
  - Proxima acao: nenhuma.

- 2026-02-07: **TASK-SPATIAL-0021 — Landing no mapa (implementado)**  
  - Preferencia por usuario via localStorage (`landing-preference:{userId}`) com default dashboard.  
  - Toggle em Settings para escolher dashboard vs mapa.  
  - Login/Signup agora redirecionam para rota conforme preferencia.  
  - Testes: `npm run test:unit` (11 arquivos, 19 testes OK).  
  - Testes: `npm run test:storybook` (8 arquivos, 3 testes OK).  
  - Proxima acao: nenhuma.

- 2026-02-07: **TASK-SPATIAL-0033 — Onboarding tour MVP (implementado)**  
  - Criado `OnboardingTour` com 2 passos (Command Center + Field Dock), opcao de pular e persistencia `tour-completed:{userId}`.  
  - Onboarding renderizado no mapa (`/farms/[id]`) para primeira visita.  
  - Testes: `npm run test:unit` (12 arquivos, 20 testes OK).  
  - Testes: `npm run test:storybook` (8 arquivos, 3 testes OK).  
  - Proxima acao: nenhuma.

- 2026-02-07: **TASK-SPATIAL-0024 — Analytics eventos (implementado)**  
  - `command_center_used` emitido no Command Center com query/result_count/time_to_result/metodo.  
  - `zoom_semantic_transition` emitido no mapa com thresholds macro/meso/micro.  
  - `bottom_sheet_interaction` emitido em sheets `side="bottom"` (open/close).  
  - Onboarding agora emite `onboarding_step` (started/completed/skipped).  
  - Testes: `npm run test:unit` (12 arquivos, 20 testes OK).  
  - Testes: `npm run test:storybook` (8 arquivos, 3 testes OK).  
  - Proxima acao: nenhuma.

- 2026-02-07: **TASK-SPATIAL-0012 — Dynamic Island (a11y hardening)**  
  - Adicionado `aria-atomic="true"` e prop `ariaLive` para ajustar `aria-live` quando necessario.  
  - Story `Action` ajustada para `ariaLive="assertive"`.  
  - Testes: `npm run test:unit` (12 arquivos, 20 testes OK).  
  - Testes: `npm run test:storybook` (8 arquivos, 3 testes OK).  
  - Proxima acao: nenhuma.

- 2026-02-07: **TASK-SPATIAL-0022 — Zoom Semantico MVP (implementado)**  
  - Nivel semantico macro/meso/micro com thresholds + badge no mapa.  
  - Atalhos 1/2/3 ajustam o zoom para macro/meso/micro.  
  - Helper `zoomSemantic` extraido com testes.  
  - Testes: `npm run test:unit` (13 arquivos, 23 testes OK).  
  - Testes: `npm run test:storybook` (8 arquivos, 3 testes OK).  
  - Proxima acao: nenhuma.

- 2026-02-07: **TASK-SPATIAL-0034 — Overlay details (implementado)**  
  - Detalhes do talhao agora abrem como overlay flutuante sobre o mapa.  
  - Botao "Ver detalhes" alterna visibilidade; fechar retorna ao mapa.  
  - Overlay aparece automaticamente quando painel esta colapsado ou foco no mapa.  
  - Testes: `npm run test:unit` (13 arquivos, 23 testes OK).  
  - Proxima acao: nenhuma.

- 2026-02-07: **Landing Page — "The Portal" implementation**
  - Rebuilt app-ui landing page with cinematic "Portal" layout, narrative sections, and dark immersive styling.
  - Added Hero3D (R3F) with fallback, GSAP scroll animation, mobile overlay menu, JSON-LD + Plausible script.
  - Added farm/micro 3D scenes with scroll-jacking animations, SVG line draw, particles + shader scan.
  - Added robots/sitemap routes, CSP header, reduced-motion guardrails, real Earth textures, atmosphere lighting.
  - Added CTA + scroll analytics, A/B CTA via Edge Config, Signup Completed tracking, Video play tracker, Sentry + Vercel Analytics.
  - Added Lighthouse CI workflow + budget.json and OG/Twitter assets.
  - Wired KTX2 globe textures from public/textures/compressed with JPG/PNG fallback, including mobile LOD.
  - Proxima acao: validar visual em `/` e confirmar carregamento KTX2 no DevTools.

- 2026-02-07: **Spatial AI OS — Implementation Plan (draft)**
  - Novo plano criado em `ai/IMPLEMENTATION_PLAN_SPATIAL_AI_OS.md` consolidando `ai/RADICAL_PROPOSAL.md` + docs de `design-system/`.
  - Atualizado com decisoes aprovadas: Design System Spatial Glass, Leaflet nas Fases 0-2, e cronograma 2/4/4 semanas.
  - Proxima acao: usuario revisar a versao atualizada do plano.

- 2026-02-07: **Spatial AI OS — Tasks detalhadas**
  - Detalhadas tasks em `ai/tasks.md` (Fases 0-2) para tokens, Storybook, componentes Spatial, layout e Leaflet vector tiles.
  - Adicionadas tasks faltantes (a11y baseline, Lighthouse CI, utilities/tokens docs, Badge/Tooltip, Storybook a11y gate, performance mobile, SW cache, onboarding, overlays, Phase 3 e analytics dashboard).
  - Adicionado Sprint Plan proposto (Sprint 0–4 + Fase 3) em `ai/tasks.md`.
  - Marcadas as tasks com `Sprint` (0–4/Fase 3) em `ai/tasks.md`.
  - Proxima acao: priorizar quais tasks iniciar primeiro.

- 2026-02-07: **TASK-SPATIAL-0001 — Tokens no app-ui (em progresso)**
  - Importado `design-system/tokens.css` em `services/app-ui/src/app/globals.css`.
  - Atualizado `--primary-foreground` para usar `--text-on-primary` dos tokens.
  - Ajustado Tailwind `primary` para usar `var(--primary)` e `var(--primary-foreground)` sem `hsl()`.
  - Proxima acao: validar visual no app-ui e ajustar tokens/vars se necessario.

- 2026-02-07: **TASK-SPATIAL-0001 — Tokens no app-ui (concluido)**
  - `globals.css` agora usa tokens (`--gray-*`, `--text-*`, `--primary`, `--critical`) para light/dark.
  - Tailwind config ajustado para usar vars diretas (sem `hsl()`) em background/foreground/secondary/etc.
  - Proxima acao: validar visual no app-ui (mapa e cards) e ajustar contraste se necessario.

- 2026-02-07: **TASK-SPATIAL-0002 — Storybook (concluido)**
  - Storybook roda com framework `@storybook/react-webpack5` (para estabilidade no Windows).
  - `.storybook` aponta apenas para stories do `design-system/components`.
  - Preview carrega `design-system/tokens.css` e backgrounds base (sem `import type`).
  - Addons habilitados: essentials, interactions, a11y, links (v8.6.15).
  - Proxima acao: adicionar as primeiras stories no design-system para remover o warning de “No story files found”.

- 2026-02-07: **TASK-SPATIAL-0003 — Base components (em progresso)**
  - Criados componentes base: Button, Input, Card em `design-system/components/base`.
  - Criadas stories para Button/Input/Card e exports em `design-system/components/index.ts`.
  - Proxima acao: configurar test runner para componentes e adicionar testes basicos.

- 2026-02-07: **TASK-SPATIAL-0003 — Testes base components (concluido)**
  - Configurados scripts `test:unit` e setup do Vitest para ler `design-system/components`.
  - Instalados Testing Library + jsdom e ajustado `vitest.setup.ts` para jest-dom/vitest.
  - Ajustado Vitest para resolver deps do app-ui e permitir fs fora do root.
  - Testes rodando: `npm run test:unit` -> 3 arquivos, 6 testes OK.
  - Proxima acao: opcional — avaliar habilitar suite `test:storybook` quando addon-vitest estiver definido.

- 2026-02-07: **Storybook test runner (bloqueado por versão)**
  - Tentativa de habilitar `test:storybook` via `@storybook/addon-vitest` falhou.
  - Motivo: addon-vitest atual exige Storybook `^10.2.7` e nossa stack está em `8.6.15`.
  - Proxima acao: decidir se fazemos upgrade major para Storybook 10 (destravar `test:storybook`) ou mantemos apenas `test:unit`.

- 2026-02-07: **test:storybook habilitado sem upgrade**
  - Ajustado `vitest.config.ts` para executar stories no browser sem addon-vitest.
  - Corrigido `.storybook/vitest.setup.ts` para `@storybook/nextjs`.
  - Ajustado `design-system/tokens.css` para mover `@import` ao topo (PostCSS).
  - `npm run test:storybook` passa (stories carregam; 0 testes, passWithNoTests).

- 2026-02-07: **Storybook interaction tests adicionados**
  - Adicionados `play` e testes diretos nos stories de Button/Input/Card.
  - Instalado `@storybook/test` e resolvido alias para carregar no Vitest.
  - `npm run test:storybook` passa com 3 testes (1 por story).

- 2026-02-07: **A11y checks nos stories**
  - Adicionados checks com `axe-core` em Button/Input/Card.
  - `npm run test:storybook` passa com interacoes + a11y.

- 2026-02-07: **TASK-SPATIAL-0010 — Command Center (concluido)**
  - Componente `CommandCenter` criado com role `search`, listbox acessivel e atalhos ⌘K/Ctrl+K.
  - Navegacao por setas + Enter implementada; stories e testes adicionados.
  - Testes: `npm run test:unit` e `npm run test:storybook` OK.

- 2026-02-07: **TASK-SPATIAL-0011 — Field Dock (concluido)**
  - Componente `FieldDock` criado com variantes macro/meso/micro e touch targets >= 44px.
  - Acoes suportam estado ativo/disabled e tooltip via atributo `title`.
  - Stories e testes adicionados; `npm run test:unit` e `npm run test:storybook` OK.

- 2026-02-07: **TASK-SPATIAL-0027 — Glassmorphism utilities (concluido)**
  - Adicionadas classes utilitarias (`glass-panel`, `glass-panel-subtle`, `glass-border`) em `design-system/tokens.css`.
  - Naming conventions documentadas em `design-system/MASTER.md` e `design-system/components/README.md`.

- 2026-02-07: **TASK-SPATIAL-0025 — A11y baseline + contratos de teclado (concluido)**
  - Criado `design-system/components/utils/a11y.ts` com helpers e lista de atalhos globais.
  - Atalhos documentados em `design-system/MASTER.md` e `design-system/components/README.md`.
  - Command Center passou a usar helpers de teclado.
  - Testes: `npm run test:unit` OK.

- 2026-02-07: **TASK-SPATIAL-0026 — Lighthouse CI + thresholds (concluido)**
  - Adicionado `services/app-ui/lighthouserc.json` com thresholds (Perf >= 0.85, A11y >= 0.90).
  - Workflow `lighthouse.yml` atualizado para usar `configPath`.
  - Script `lighthouse:ci` e dependency `@lhci/cli` adicionados.
  - Nota: LHCI não foi executado localmente (depende de URL preview).

- 2026-02-07: **TASK-SPATIAL-0029 — Storybook a11y gate (concluido)**
  - `test:a11y` adicionado como alias para `test:storybook`.
  - Documentado gate de a11y em `design-system/components/README.md`.

- 2026-02-07: **TASK-SPATIAL-0028 — Badge + Tooltip (concluido)**
  - Badge e Tooltip criados com tokens e glassmorphism (Radix Tooltip).
  - Stories e testes adicionados; `npm run test:unit` e `npm run test:storybook` OK.
  - Nota: warnings de atributos `jsx/global` no teste `landing-page` persistem (preexistente).

- 2026-02-07: **TASK-SPATIAL-0020 — Map layout (concluido)**
  - Criado `MapLayout` com slots de overlay (top/bottom/center) e container map full-size.
  - `farms/[id]` agora usa MapLayout para overlay + mapa 100% tela.
  - Testes: `npm run test:unit` OK.

- 2026-02-07: **Sprint 0 — Encerramento**
  - Sprint 0 finalizado (tokens, Storybook/tests, base components, Command Center, Field Dock, MapLayout, LHCI).
  - Session log: `ai/sessions/2026-02-07-1609.md`.

- 2026-02-07: **npm EPERM + ENOTCACHED — Resolvido**
  - Erro `spawn EPERM` em `npm rebuild esbuild` resolvido com limpeza de cache e reinstalacao seletiva.
  - Erro `EPERM` ao remover `package.jso…22986 tokens truncated… wt ON w.year = wt.year AND w.week = wt.week
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
            ))
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
