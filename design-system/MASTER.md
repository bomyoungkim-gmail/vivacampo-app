# VivaCampo Design System — Master

**Versão:** 2.0.0 (Spatial AI OS)
**Data:** 2026-02-07
**Status:** Draft para validação
**Baseado em:** RADICAL_PROPOSAL.md + Avaliação UI/UX Pro Max

---

## 🎯 Visão Geral

O VivaCampo Design System foi criado para suportar a transformação de um SaaS tradicional para um **Spatial AI OS** — uma interface imersiva onde o mapa é o sistema.

### Princípios de Design

1. **Spatial-First:** Mapa sempre visível, UI flutua sobre ele
2. **Progressive Disclosure:** Complexidade revelada gradualmente via Zoom Semântico
3. **Glassmorphism:** Profundidade visual sem poluir o mapa
4. **Accessibility-First:** WCAG 2.1 Level AA em todas as interfaces
5. **Mobile-Native:** Bottom Sheets e gestos nativos
6. **Agriculture-Centric:** Cores e metáforas alinhadas ao domínio

---

## 🎨 Design Tokens

### Cores

#### Cores Primárias — Natureza

```css
:root {
  /* Verde - Saúde das Plantas */
  --primary: #16A34A;           /* Green-600 */
  --primary-dark: #15803D;      /* Green-700 */
  --primary-light: #4ADE80;     /* Green-400 */

  /* Uso: Botões principais, ícones de status saudável, NDVI alto */
}
```

#### Cores Secundárias — Alertas e Status

```css
:root {
  /* Alertas */
  --warning: #F59E0B;           /* Amber-500 */
  --critical: #DC2626;          /* Red-600 */
  --healthy: #10B981;           /* Emerald-500 */
  --info: #3B82F6;              /* Blue-500 */

  /* Status de NDVI */
  --ndvi-critical: #DC2626;     /* < 0.3 */
  --ndvi-low: #F59E0B;          /* 0.3 - 0.5 */
  --ndvi-medium: #F59E0B;       /* 0.5 - 0.7 */
  --ndvi-good: #10B981;         /* 0.7 - 0.85 */
  --ndvi-excellent: #16A34A;    /* > 0.85 */
}
```

#### Cores Neutras — Fundação

```css
:root {
  /* Escala de Cinza (Slate) */
  --gray-50: #F8FAFC;
  --gray-100: #F1F5F9;
  --gray-200: #E2E8F0;
  --gray-300: #CBD5E1;
  --gray-400: #94A3B8;
  --gray-500: #64748B;
  --gray-600: #475569;
  --gray-700: #334155;
  --gray-800: #1E293B;
  --gray-900: #0F172A;

  /* Textos */
  --text-primary: var(--gray-900);
  --text-secondary: var(--gray-600);
  --text-muted: var(--gray-400);
  --text-on-primary: #FFFFFF;
}
```

#### Glassmorphism — Profundidade Espacial

```css
:root {
  /* Backgrounds com Blur */
  --glass-bg: rgba(255, 255, 255, 0.85);
  --glass-bg-dark: rgba(15, 23, 42, 0.85);
  --glass-bg-subtle: rgba(255, 255, 255, 0.60);

  /* Bordas */
  --glass-border: rgba(255, 255, 255, 0.2);
  --glass-border-dark: rgba(255, 255, 255, 0.1);

  /* Blur Amount */
  --blur-sm: blur(8px) saturate(150%);
  --blur-md: blur(16px) saturate(160%);
  --blur-lg: blur(24px) saturate(180%);
}

/* Classe Utilitária */
.glass-morphism {
  background: var(--glass-bg);
  backdrop-filter: var(--blur-lg);
  border: 1px solid var(--glass-border);
}

.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: var(--blur-md);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-md);
}

.glass-panel-subtle {
  background: var(--glass-bg-subtle);
  backdrop-filter: var(--blur-sm);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-sm);
}

.glass-border {
  border: 1px solid var(--glass-border);
}
```

**Naming conventions:**
- `glass-morphism`: floating overlays (Command Center, Dynamic Island)
- `glass-panel`: inline panels/cards
- `glass-panel-subtle`: soft surfaces on map
- `glass-border`: apply glass border on custom elements

#### Sombras — Profundidade

```css
:root {
  /* Elevação */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  --shadow-floating: 0 8px 32px rgba(0, 0, 0, 0.12);
  --shadow-depth: 0 20px 60px rgba(0, 0, 0, 0.2);

  /* Uso */
  /* sm: Botões, cards simples */
  /* md: Dropdowns, popovers */
  /* floating: Command Center, Field Dock */
  /* depth: Bottom Sheets, modais */
}
```

### Dark Mode

```css
@media (prefers-color-scheme: dark) {
  :root {
    /* Cores Base */
    --text-primary: var(--gray-50);
    --text-secondary: var(--gray-400);
    --text-muted: var(--gray-500);

    /* Glassmorphism */
    --glass-bg: var(--glass-bg-dark);
    --glass-border: var(--glass-border-dark);

    /* Sombras mais sutis */
    --shadow-floating: 0 8px 32px rgba(0, 0, 0, 0.3);
    --shadow-depth: 0 20px 60px rgba(0, 0, 0, 0.5);
  }
}
```

---

## 📐 Espaçamento e Layout

### Escala de Espaçamento

Baseada em múltiplos de 4px (Tailwind padrão):

```css
:root {
  --space-0: 0;
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
  --space-20: 5rem;     /* 80px */
}
```

### Grid e Containers

```css
.container {
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  padding-left: var(--space-4);
  padding-right: var(--space-4);
}

/* Breakpoints */
@media (min-width: 640px) {  /* sm */
  .container { max-width: 640px; }
}
@media (min-width: 768px) {  /* md */
  .container { max-width: 768px; }
}
@media (min-width: 1024px) { /* lg */
  .container { max-width: 1024px; }
}
@media (min-width: 1280px) { /* xl */
  .container { max-width: 1280px; }
}
@media (min-width: 1536px) { /* 2xl */
  .container { max-width: 1536px; }
}
```

### Z-Index Scale

```css
:root {
  --z-base: 0;
  --z-dropdown: 10;
  --z-sticky: 20;
  --z-fixed: 30;
  --z-overlay: 40;
  --z-modal: 50;
  --z-popover: 60;
  --z-tooltip: 70;
}

/* Componentes Específicos */
.map-container { z-index: var(--z-base); }
.field-dock { z-index: var(--z-fixed); }
.bottom-sheet { z-index: var(--z-overlay); }
.command-center { z-index: var(--z-modal); }
.dynamic-island { z-index: var(--z-modal); }
.tooltip { z-index: var(--z-tooltip); }
```

---

## 🔤 Tipografia

### Família de Fontes

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --font-family-base: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-family-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;
}

body {
  font-family: var(--font-family-base);
  font-feature-settings: 'tnum' 1; /* Números tabulares */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### Escala Tipográfica

```css
:root {
  /* Tamanhos */
  --text-xs: 0.75rem;     /* 12px */
  --text-sm: 0.875rem;    /* 14px */
  --text-base: 1rem;      /* 16px */
  --text-lg: 1.125rem;    /* 18px */
  --text-xl: 1.25rem;     /* 20px */
  --text-2xl: 1.5rem;     /* 24px */
  --text-3xl: 1.875rem;   /* 30px */
  --text-4xl: 2.25rem;    /* 36px */

  /* Pesos */
  --font-light: 300;
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;

  /* Line Heights */
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;
}
```

### Hierarquia de Texto

```css
/* Headings */
.h1 {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: -0.02em;
}

.h2 {
  font-size: var(--text-3xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  letter-spacing: -0.01em;
}

.h3 {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-snug);
}

/* Body */
.body-lg {
  font-size: var(--text-lg);
  line-height: var(--leading-relaxed);
}

.body {
  font-size: var(--text-base);
  line-height: var(--leading-normal);
}

.body-sm {
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
}

/* Labels */
.label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  letter-spacing: 0.01em;
}

/* Código */
.code {
  font-family: var(--font-family-mono);
  font-size: var(--text-sm);
  background: var(--gray-100);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
}
```

---

## 🎬 Animações e Transições

### Durações

```css
:root {
  --transition-instant: 0ms;
  --transition-fast: 150ms;
  --transition-medium: 300ms;
  --transition-slow: 500ms;
}
```

### Easing Functions

```css
:root {
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);      /* ease-in-out */
  --ease-in: cubic-bezier(0.4, 0, 1, 1);             /* ease-in */
  --ease-out: cubic-bezier(0, 0, 0.2, 1);            /* ease-out */
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55); /* bounce */
}
```

### Classes Utilitárias

```css
.transition-fast {
  transition: all var(--transition-fast) var(--ease-default);
}

.transition-medium {
  transition: all var(--transition-medium) var(--ease-default);
}

.transition-colors {
  transition: color var(--transition-fast) var(--ease-default),
              background-color var(--transition-fast) var(--ease-default),
              border-color var(--transition-fast) var(--ease-default);
}

.transition-transform {
  transition: transform var(--transition-medium) var(--ease-default);
}
```

### Respeitar Preferências do Usuário

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 🧩 Componentes Base

### Botões

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  border-radius: 0.5rem;
  transition: all var(--transition-fast) var(--ease-default);
  cursor: pointer;

  /* Touch Target */
  min-width: 44px;
  min-height: 44px;

  /* Disable text selection */
  user-select: none;
}

.btn-primary {
  background: var(--primary);
  color: var(--text-on-primary);
  border: 1px solid transparent;
}

.btn-primary:hover {
  background: var(--primary-dark);
  box-shadow: var(--shadow-md);
}

.btn-primary:active {
  transform: scale(0.98);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--gray-300);
}

.btn-secondary:hover {
  background: var(--gray-100);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid transparent;
}

.btn-ghost:hover {
  background: var(--gray-100);
  color: var(--text-primary);
}
```

### Cards

```css
.card {
  background: white;
  border-radius: 1rem;
  box-shadow: var(--shadow-sm);
  padding: var(--space-6);
  transition: all var(--transition-fast) var(--ease-default);
}

.card-glass {
  background: var(--glass-bg);
  backdrop-filter: var(--blur-lg);
  border: 1px solid var(--glass-border);
  border-radius: 1rem;
  padding: var(--space-6);
  box-shadow: var(--shadow-floating);
}

.card-interactive {
  cursor: pointer;
}

.card-interactive:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### Inputs

```css
.input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-base);
  border: 1px solid var(--gray-300);
  border-radius: 0.5rem;
  transition: all var(--transition-fast) var(--ease-default);

  /* Touch Target */
  min-height: 44px;
}

.input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.1);
}

.input::placeholder {
  color: var(--text-muted);
}

.input:disabled {
  background: var(--gray-100);
  cursor: not-allowed;
}
```

---

## 📱 Componentes Espaciais

### Command Center

```css
.command-center {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--z-modal);

  /* Glassmorphism */
  background: var(--glass-bg);
  backdrop-filter: var(--blur-lg);
  border: 1px solid var(--glass-border);
  border-radius: 1rem;
  box-shadow: var(--shadow-depth);

  /* Sizing */
  width: 90%;
  max-width: 640px;

  /* Animação de entrada */
  animation: slideUp var(--transition-medium) var(--ease-out);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translate(-50%, 20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

.command-center-input {
  width: 100%;
  padding: var(--space-4) var(--space-6);
  font-size: var(--text-lg);
  background: transparent;
  border: none;
  outline: none;
}

.command-center-results {
  max-height: 320px;
  overflow-y: auto;
  border-top: 1px solid var(--glass-border);
}

.command-center-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-6);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.command-center-item:hover,
.command-center-item[aria-selected="true"] {
  background: rgba(22, 163, 74, 0.1);
}
```

### Dynamic Island

```css
.dynamic-island {
  position: fixed;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--z-modal);

  /* Glassmorphism */
  background: var(--glass-bg);
  backdrop-filter: var(--blur-lg);
  border: 1px solid var(--glass-border);
  border-radius: 9999px;
  box-shadow: var(--shadow-lg);

  /* Sizing */
  padding: var(--space-3) var(--space-6);

  /* Transição suave de altura */
  transition: all var(--transition-medium) var(--ease-default);
}

.dynamic-island-content {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}
```

### Field Dock (Menu Inferior Direito)

```css
.field-dock {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: var(--z-fixed);

  /* Layout */
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field-dock-tool {
  /* Glassmorphism */
  background: var(--glass-bg);
  backdrop-filter: var(--blur-lg);
  border: 1px solid var(--glass-border);
  border-radius: 0.75rem;
  box-shadow: var(--shadow-floating);

  /* Sizing */
  width: 56px;
  height: 56px;

  /* Flexbox */
  display: flex;
  align-items: center;
  justify-content: center;

  /* Interação */
  cursor: pointer;
  transition: all var(--transition-fast) var(--ease-default);
}

.field-dock-tool:hover {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: var(--shadow-lg);
  transform: scale(1.05);
}

.field-dock-tool.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}
```

### Bottom Sheet (Mobile)

```css
.bottom-sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: var(--z-overlay);

  /* Glassmorphism */
  background: var(--glass-bg);
  backdrop-filter: var(--blur-lg);
  border-top-left-radius: 1.5rem;
  border-top-right-radius: 1.5rem;
  box-shadow: var(--shadow-depth);

  /* Padding */
  padding: var(--space-6);
  padding-bottom: max(var(--space-6), env(safe-area-inset-bottom));

  /* Performance */
  transform: translateZ(0);
  will-change: transform;
  contain: layout style paint;

  /* Touch */
  touch-action: pan-y;
  -webkit-overflow-scrolling: touch;

  /* Transição */
  transition: transform var(--transition-medium) var(--ease-default);
}

.bottom-sheet-drag-indicator {
  width: 48px;
  height: 6px;
  background: var(--gray-300);
  border-radius: 9999px;
  margin: 0 auto var(--space-4);
}

.bottom-sheet-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: calc(var(--z-overlay) - 1);
  backdrop-filter: blur(4px);
  transition: opacity var(--transition-medium);
}
```

### Breadcrumb Flutuante

```css
.breadcrumb-floating {
  position: fixed;
  top: 5rem;
  left: 1rem;
  z-index: var(--z-fixed);

  /* Glassmorphism */
  background: var(--glass-bg);
  backdrop-filter: var(--blur-lg);
  border: 1px solid var(--glass-border);
  border-radius: 9999px;
  box-shadow: var(--shadow-floating);

  /* Padding */
  padding: var(--space-2) var(--space-4);
}

.breadcrumb-list {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  list-style: none;
}

.breadcrumb-separator {
  color: var(--text-muted);
}

.breadcrumb-link {
  color: var(--text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.breadcrumb-link:hover {
  color: var(--primary);
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: var(--font-medium);
}
```

### Mini-Mapa

```css
.mini-map {
  position: fixed;
  bottom: 6rem;
  left: 1rem;
  z-index: var(--z-fixed);

  /* Glassmorphism */
  background: var(--glass-bg);
  backdrop-filter: var(--blur-lg);
  border: 1px solid var(--glass-border);
  border-radius: 0.75rem;
  box-shadow: var(--shadow-floating);

  /* Sizing */
  width: 192px;
  height: 192px;

  /* Overflow */
  overflow: hidden;
}

.mini-map-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  background: var(--primary);
  border: 2px solid white;
  border-radius: 9999px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
```

---

## ♿ Acessibilidade

### Classes Utilitárias

```css
/* Screen Reader Only */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

### Estados de Foco

```css
/* Foco visível para navegação por teclado */
*:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

/* Remover outline padrão do navegador */
*:focus:not(:focus-visible) {
  outline: none;
}
```

### Touch Targets

```css
/* Garantir tamanho mínimo de toque (WCAG 2.5.5) */
.touch-target {
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
```

### Contratos de Teclado (Spatial OS)

| Atalho | Comportamento |
| --- | --- |
| Ctrl+K / ⌘K | Abrir Command Center |
| Esc | Fechar overlays e menus |
| 1 | Macro view (zoom semantico) |
| 2 | Meso view (zoom semantico) |
| 3 | Micro view (zoom semantico) |

**Observações:**
- Todos os overlays devem fechar com `Esc`.
- A lista acima é a referência de atalhos globais (também exportada em `utils/a11y.ts`).

---

## 📏 Breakpoints e Responsividade

### Breakpoints

```css
:root {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;
}
```

### Mobile-First Media Queries

```css
/* Mobile (default) */
/* Estilo base já é mobile */

/* Tablet */
@media (min-width: 768px) {
  .breadcrumb-floating {
    /* Mostrar breadcrumb completo */
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .field-dock {
    /* Aumentar tamanho das ferramentas */
  }
}
```

---

## 🎓 Uso e Boas Práticas

### ✅ Do's

1. **Use design tokens:** Sempre use variáveis CSS em vez de valores hardcoded
2. **Glassmorphism sobre mapa:** Todos os componentes flutuantes devem usar `.glass-morphism`
3. **Touch targets:** Mínimo 44x44px para todos os elementos interativos
4. **ARIA labels:** Sempre em ícones sem texto
5. **Dark mode:** Testar todos os componentes em ambos os modos
6. **Performance:** Use `transform` e `opacity` para animações

### ❌ Don'ts

1. **Emojis como ícones:** Use SVG (Heroicons/Lucide)
2. **Animações excessivas:** Respeite `prefers-reduced-motion`
3. **Cores hardcoded:** Sempre use variáveis CSS
4. **Layout shifts:** Evite hover com `scale()` em elementos inline
5. **Z-index arbitrários:** Use a escala definida
6. **Blur excessivo:** Pode causar lag em mobile

---

## 📦 Componentes a Implementar

### Prioridade Alta (Fase 0-1)

- [ ] Command Center
- [ ] Dynamic Island
- [ ] Field Dock
- [ ] Bottom Sheet (mobile)
- [ ] Breadcrumb Flutuante

### Prioridade Média (Fase 2)

- [ ] Mini-Mapa
- [ ] Toast/Notifications
- [ ] Loading States (skeleton screens)
- [ ] Zoom Controls

### Prioridade Baixa (Fase 3)

- [ ] Tour de Onboarding
- [ ] Split View (comparação)
- [ ] Crop Feed

---

## 🔗 Recursos

### Documentação
- [Tailwind CSS](https://tailwindcss.com/docs)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Mapbox GL JS](https://docs.mapbox.com/mapbox-gl-js/)

### Ferramentas
- [Figma](https://figma.com) — Prototipagem
- [Storybook](https://storybook.js.org) — Documentação de componentes
- [axe DevTools](https://www.deque.com/axe/devtools/) — Auditoria de acessibilidade

### Ícones
- [Heroicons](https://heroicons.com)
- [Lucide Icons](https://lucide.dev)
- [Simple Icons](https://simpleicons.org) — Logos de marcas

---

## 📝 Changelog

### v2.0.0 — 2026-02-07
- ✨ Criação do design system para Spatial AI OS
- 🎨 Definição de cores agricultura-centric
- 🧩 Componentes espaciais (Command Center, Dynamic Island, Field Dock)
- ♿ Guidelines de acessibilidade WCAG 2.1 AA
- 📱 Mobile-first com Bottom Sheets

---

**Próxima Revisão:** Após validação de protótipo com usuários
**Responsável:** Equipe de Design + Desenvolvimento Frontend
