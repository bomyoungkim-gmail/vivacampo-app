# Guia: Protótipo Figma — VivaCampo Spatial AI OS

**Versão:** 2.0.0
**Data:** 2026-02-07
**Objetivo:** Criar protótipo interativo de alta fidelidade para validação com usuários

---

## 🎯 Visão Geral

Este guia orienta a criação do protótipo Figma do VivaCampo Spatial AI OS, incluindo:
1. Configuração de design tokens
2. Componentes principais
3. Interações e gestos
4. Fluxos de navegação
5. Exportação para desenvolvimento

---

## 📦 Setup Inicial

### 1. Criar Novo Arquivo Figma

1. Novo arquivo: `VivaCampo Spatial AI OS - Prototype`
2. Criar páginas:
   - **Design System** (tokens, componentes)
   - **Screens** (telas completas)
   - **Flows** (fluxos de navegação)
   - **Handoff** (especificações para dev)

### 2. Importar Design Tokens

#### Criar Variáveis (Figma Variables)

**Cores (Terra Viva Palette):**
```
Collections:
├── Colors
│   ├── Primary (Forest)
│   │   ├── primary-50: #F0FDF4
│   │   ├── ...
│   │   ├── primary-500: #22C55E (Main)
│   │   └── primary-900: #14532D
│   ├── Accent (Harvest)
│   │   ├── accent-50: #FFFBEB
│   │   ├── ...
│   │   ├── accent-500: #F59E0B (Highlight)
│   │   └── accent-900: #78350F
│   ├── Earth (Neutral/Base)
│   │   ├── earth-50: #FAF5F0
│   │   ├── ...
│   │   ├── earth-500: #8B6F47
│   │   └── earth-900: #1A1510
│   ├── Sky (Info/Tech)
│   │   ├── sky-50: #F0F9FF
│   │   ├── ...
│   │   ├── sky-500: #0EA5E9
│   │   └── sky-900: #0C4A6E
│   ├── Semantic
│   │   ├── success: {primary-500}
│   │   ├── warning: {accent-500}
│   │   ├── error: #DC2626
│   │   └── info: {sky-500}
│   └── Glassmorphism
│       ├── glass-bg: rgba(255,255,255,0.85)
│       └── glass-border: rgba(255,255,255,0.2)
```

**Espaçamento:**
```
Collections:
├── Spacing
│   ├── space-1: 4px
│   ├── space-2: 8px
│   ├── space-3: 12px
│   ├── ... (todos)
│   └── space-20: 80px
```

**Tipografia:**
```
Collections:
├── Typography
│   ├── Font Size
│   │   ├── text-xs: 12
│   │   ├── text-sm: 14
│   │   ├── ... (todos)
│   │   └── text-4xl: 36
│   ├── Font Weight
│   │   ├── font-light: 300
│   │   ├── ... (todos)
│   │   └── font-bold: 700
│   └── Line Height
│       ├── leading-tight: 1.25
│       └── ... (todos)
```

---

## 🎨 Componentes Base

### 1. Botões

**Criar Component Set:**

```
Component: Button
Variants:
├── Variant: primary, secondary, ghost
├── Size: sm, md, lg
├── State: default, hover, active, disabled
└── Loading: false, true
```

**Propriedades Auto Layout:**

| Variant | Padding | Gap | Border Radius |
|---------|---------|-----|---------------|
| sm | 8px 12px | 8px | 6px |
| md | 12px 24px | 8px | 8px |
| lg | 16px 32px | 8px | 12px |

**Estilos:**

```
Primary:
- Fill: {primary-500}
- Text: white
- Shadow: shadow-sm (0 1px 2px rgba(0,0,0,0.05))

Primary Hover:
- Fill: {primary-600}
- Shadow: shadow-md (0 4px 6px rgba(0,0,0,0.07))

Primary Active:
- Fill: {primary-600}
- Transform: scale(0.98)
```

---

### 2. Glassmorphism (Efeito de Vidro)

**Criar Estilo de Efeito:**

1. Layer > Effects > Background Blur
   - Blur: 24px
   - Saturation: 180%

2. Fill:
   - Color: white
   - Opacity: 85%

3. Stroke:
   - Color: white
   - Opacity: 20%
   - Width: 1px
   - Position: Inside

4. Shadow:
   - X: 0, Y: 8
   - Blur: 32
   - Color: rgba(0,0,0,0.12)

**Salvar como Estilo:** `glass-morphism`

---

## 📱 Componentes Espaciais

### 1. Command Center

**Frame:**
- Width: 640px (max-width)
- Height: Auto
- Auto Layout: Vertical
- Padding: 0px
- Gap: 0px
- Corner Radius: 16px
- Effects: `glass-morphism`

**Estrutura:**

```
Frame: CommandCenter
├── Frame: Input Container
│   ├── Auto Layout: Horizontal
│   ├── Padding: 16px 24px
│   ├── Gap: 12px
│   ├── TextInput: "Digite um comando..."
│   └── Icon: Search (16x16)
└── Frame: Results Container
    ├── Auto Layout: Vertical
    ├── Padding: 0px
    ├── Gap: 0px
    ├── Max Height: 320px
    ├── Overflow: Scroll
    └── Frame: Result Item (repeat)
        ├── Auto Layout: Horizontal
        ├── Padding: 12px 24px
        ├── Gap: 12px
        ├── Icon: Tool (20x20)
        ├── Text: "Mostrar NDVI abaixo de 0.4"
        └── Interaction: Hover → bg-primary-500/10
```

**Criar Interactive Component:**

1. Variants:
   - State: closed, open-empty, open-with-results
2. Prototyping:
   - closed → open-with-results: Smart Animate (300ms ease-out)

---

### 2. Dynamic Island

**Frame:**
- Width: Auto (fit content)
- Height: 44px
- Auto Layout: Horizontal
- Padding: 12px 24px
- Gap: 12px
- Corner Radius: 9999px (pill shape)
- Effects: `glass-morphism`

**Variants:**

```
Variant: neutral
- Text: "Boa tarde, João. 3 alertas críticos hoje."
- Icon: None

Variant: selection
- Icon: Warning (20x20) color:accent-500
- Text: "Talhão 4B • Soja • 120ha"
- Badge: "⚠️ Risco de Praga" (bg-error/10, text-error)

Variant: action
- Icon: Spinner (animated)
- Text: "Processando nova imagem... 30%"
- Progress Bar (inside)
```

**Animação:**

1. neutral → selection: Smart Animate (300ms)
2. Auto Animate quando texto muda

---

### 3. Field Dock

**Frame:**
- Auto Layout: Vertical
- Gap: 8px
- Position: Fixed (bottom-right)

**Tool Button:**

```
Frame: ToolButton
- Width: 56px
- Height: 56px
- Corner Radius: 12px
- Effects: glass-morphism
- Icon: 24x24 (centered)

States:
- default: bg-glass-bg
- hover: bg-white/95 + scale(1.05)
- active: bg-primary-500 + text-white
```

**Component Set:**

```
Component: ToolButton
Variants:
├── Tool: ndvi, weather, alerts, draw, compare
├── State: default, hover, active
└── Tooltip: visible, hidden
```

---

### 4. Bottom Sheet (Mobile)

**Frame (iPhone 14 Pro Max: 430x932):**

```
Frame: BottomSheet
├── Position: Fixed Bottom
├── Width: 430px (full width)
├── Height: Variable
├── Corner Radius: 24px 24px 0px 0px
├── Effects: glass-morphism + shadow-depth

Levels:
├── Peek: Height 466px (50vh)
├── Half: Height 699px (75vh)
└── Full: Height 932px (100vh)
```

**Estrutura:**

```
Frame: BottomSheet
├── Frame: Drag Indicator
│   ├── Width: 48px
│   ├── Height: 6px
│   ├── Corner Radius: 9999px
│   ├── Fill: gray-300
│   ├── Align: Center Horizontal
│   └── Margin Top: 12px
├── Button: Close
│   ├── Position: Absolute top-right
│   ├── Icon: X
│   └── Size: 44x44px (touch target)
└── Frame: Content
    ├── Auto Layout: Vertical
    ├── Padding: 24px
    ├── Gap: 16px
    ├── Overflow: Scroll
    └── ... (conteúdo dinâmico)
```

**Interação de Gestos (Protopie ou Figma Mirror):**

1. Drag Up: Peek → Half → Full
2. Drag Down: Full → Half → Peek → Closed
3. Tap Close: → Closed
4. Tap Overlay: → Closed

**Criar Protótipo no Figma:**

1. Criar 4 frames:
   - BottomSheet-Closed
   - BottomSheet-Peek
   - BottomSheet-Half
   - BottomSheet-Full

2. Adicionar interações:
   - Drag: Use Drag Trigger (vertical)
   - Threshold: 100px
   - Animation: Smart Animate (300ms ease-out)

---

### 5. Breadcrumb Flutuante

**Frame:**
- Width: Auto (fit content)
- Height: 36px
- Auto Layout: Horizontal
- Padding: 8px 16px
- Gap: 8px
- Corner Radius: 9999px
- Effects: glass-morphism

**Estrutura:**

```
Frame: Breadcrumb
├── Icon: Home (16x16)
├── Text: "Início"
├── Text: "›" (separator, color-muted)
├── Text: "Fazenda Santa Maria" (clickable)
├── Text: "›"
└── Text: "Talhão 4B" (current, font-medium)
```

**Mobile Variant:**

- Mostrar apenas item atual + botão voltar
- Width: Auto
- Icon: ChevronLeft + Text: "Talhão 4B"

---

### 6. Mini-Mapa

**Frame:**
- Width: 192px
- Height: 192px
- Corner Radius: 12px
- Effects: glass-morphism

**Conteúdo:**

```
Frame: MiniMap
├── Image: Simplified map view
├── Frame: Indicator (Você está aqui)
│   ├── Width: 12px
│   ├── Height: 12px
│   ├── Corner Radius: 9999px
│   ├── Fill: primary-500
│   ├── Stroke: white (2px)
│   └── Position: Center (absolute)
│   └── Animation: Pulse (2s infinite)
```

**Animação de Pulse:**

1. Duplicar Indicator
2. Criar Variant: scale-100, scale-110
3. After Delay 1000ms → scale-110 (ease-in-out)
4. After Delay 1000ms → scale-100 (ease-in-out)

---

## 🖼️ Telas Completas

### 1. Landing no Mapa (Estado Inicial)

**Frame: Desktop (1440x900)**

```
Layers:
├── Background: Map Image (full screen)
├── DynamicIsland (top-center)
├── BreadcrumbFloating (top-left)
├── FieldDock (bottom-right)
├── MiniMap (bottom-left)
└── CommandCenter (bottom-center, inicialmente hidden)
```

**Interações:**

- Press `⌘K`: Show CommandCenter (Smart Animate)
- Click MiniMap: Zoom to region (change map image)
- Click FieldDock Tool: Toggle active state

---

### 2. Zoom Semântico (3 Níveis)

**Criar 3 Frames:**

1. **Macro (Global View)**
   - Map: Clusters de fazendas
   - DynamicIsland: "Boa tarde, João. 3 alertas críticos"
   - FieldDock Tools: Search, Filter

2. **Meso (Farm View)**
   - Map: Fazenda inteira com talhões
   - DynamicIsland: "Fazenda Santa Maria • 1200ha"
   - FieldDock Tools: NewHarvest, Planning, Team

3. **Micro (Field View)**
   - Map: Talhão com NDVI heatmap
   - DynamicIsland: "Talhão 4B • Soja • 120ha • ⚠️"
   - FieldDock Tools: CreateAlert, Annotation, Compare

**Interações:**

- Scroll Zoom (simulado): Macro → Meso → Micro
- Press `1`, `2`, `3`: Jump to level
- Animation: Smart Animate (300ms) + map fade

---

### 3. Mobile com Bottom Sheet

**Frame: iPhone 14 Pro Max (430x932)**

```
Layers:
├── Background: Map (full screen)
├── DynamicIsland (top, safe area)
├── BottomSheet-Peek (bottom)
│   └── Content Preview: NDVI 0.62 | Área 120ha
└── Overlay (dim, behind sheet)
```

**Interações:**

- Drag Sheet Up: Peek → Half → Full
- Tap Overlay: Dismiss sheet
- Swipe Sheet Down: Full → Half → Peek

---

## 🎬 Protótipo de Fluxos

### Fluxo 1: Usar Command Center

```
Frames:
1. Map (Command Center closed)
   → Press ⌘K
2. Map (Command Center open, empty)
   → Type "mostrar ndvi"
3. Map (Command Center with results)
   → Click result
4. Map (NDVI layer visible, Command Center closed)
```

**Criar Protótipo:**

1. Frame 1 → 2:
   - Trigger: Key press `K` (with ⌘)
   - Action: Change to Frame 2
   - Animation: Smart Animate (150ms)

2. Frame 2 → 3:
   - Trigger: After delay 500ms
   - Action: Change to Frame 3
   - Animation: Instant

3. Frame 3 → 4:
   - Trigger: Click on result
   - Action: Change to Frame 4
   - Animation: Smart Animate (300ms)

---

### Fluxo 2: Navegar por Zoom Semântico

```
Frames:
1. Macro View
   → Click on farm cluster
2. Meso View (farm focused)
   → Click on field
3. Micro View (field detailed)
   → Press 1
4. Back to Macro View
```

---

### Fluxo 3: Mobile Bottom Sheet

```
Frames:
1. Map with BottomSheet-Peek
   → Drag up
2. Map with BottomSheet-Half
   → Drag up
3. Map with BottomSheet-Full
   → Swipe down
4. Back to Peek
```

---

## 📐 Especificações para Handoff

### Página "Handoff" no Figma

Criar frames com especificações técnicas:

#### 1. Espaçamento Interno

```
Frame: Spacing Spec
- Mostrar componente com linhas de medida
- Anotar: padding, gap, margin
- Usar plugin: Measure (Figma plugin)
```

#### 2. Cores e Sombras

```
Frame: Color Spec
- Criar swatches de todas as cores
- Anotar código hex + variável CSS
- Exemplo:
  ┌─────────┐
  │ #16A34A │ → var(--primary)
  └─────────┘
```

#### 3. Tipografia

```
Frame: Typography Spec
- H1, H2, H3, Body, Label
- Anotar: font-family, size, weight, line-height
```

#### 4. Componentes com Estados

```
Frame: Button States
- Default, Hover, Active, Disabled, Loading
- Anotar transições: "150ms ease-out"
```

---

## 🔌 Plugins Úteis

### Design Tokens

1. **Tokens Studio** (Design Tokens)
   - Exporta tokens para JSON
   - Integração com código

2. **Style Dictionary** (Build system)
   - Transforma JSON → CSS/JS/iOS/Android

### Acessibilidade

1. **Stark** (Contrast Checker)
   - Verifica contraste WCAG AA
   - Simula daltonismo

2. **A11y - Focus Orderer**
   - Define ordem de foco
   - Exporta para dev

### Handoff

1. **Measure** (Redlines)
   - Adiciona medidas automaticamente

2. **Zeplin** ou **Figma Dev Mode**
   - Especificações para desenvolvedores

---

## 🧪 Testes com Usuários

### Preparar Protótipo para Teste

1. **Modo de Apresentação:**
   - Figma > Present
   - Ou Figma Mirror (mobile)

2. **Criar Tasks:**

```markdown
# Tarefas para Teste de Usuário

## Tarefa 1: Encontrar Talhão com NDVI Baixo
"Use o Command Center para encontrar todos os talhões com NDVI abaixo de 0.4"

Sucesso: ✅ Abriu Command Center e digitou comando
Tempo esperado: < 30s

## Tarefa 2: Navegar para Fazenda Específica
"Navegue até a Fazenda Santa Maria e veja o talhão 4B"

Sucesso: ✅ Usou breadcrumb ou Command Center
Tempo esperado: < 45s

## Tarefa 3: Ver Detalhes do Talhão (Mobile)
"No celular, abra os detalhes completos do Talhão 4B"

Sucesso: ✅ Arrastou Bottom Sheet até Full
Tempo esperado: < 20s
```

3. **Observar e Anotar:**
   - Hesitações
   - Erros
   - Comentários espontâneos
   - Métricas: tempo, taxa de sucesso

---

## 📤 Exportação para Desenvolvimento

### 1. Exportar Assets

```
Assets a exportar:
├── Icons/ (SVG)
│   ├── icon-search.svg
│   ├── icon-alert.svg
│   └── ... (todos os ícones)
├── Images/
│   └── map-placeholder.png
└── Logos/
    └── vivacampo-logo.svg
```

**Configurações de Exportação:**

- SVG: Remove IDs, Outline Strokes
- PNG: 1x, 2x, 3x (retina)

### 2. Exportar Design Tokens

**Usar Tokens Studio:**

1. Plugin > Tokens Studio > Export
2. Formato: JSON
3. Arquivo: `design-tokens.json`

**Exemplo de saída:**

```json
{
  "color": {
    "primary": {
      "value": "#16A34A",
      "type": "color"
    }
  },
  "spacing": {
    "4": {
      "value": "16px",
      "type": "spacing"
    }
  }
}
```

### 3. Integrar com Código

**Build com Style Dictionary:**

```javascript
// build-tokens.js
const StyleDictionary = require('style-dictionary');

const sd = StyleDictionary.extend({
  source: ['design-tokens.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      buildPath: 'design-system/',
      files: [{
        destination: 'tokens.css',
        format: 'css/variables'
      }]
    }
  }
});

sd.buildAllPlatforms();
```

---

## ✅ Checklist de Prototipação

Antes de validar com usuários:

### Design System
- [ ] Todos os design tokens criados como variáveis
- [ ] Componentes base criados (botão, input, card)
- [ ] Componentes espaciais criados (Command Center, etc.)
- [ ] Estilos salvos (glassmorphism, sombras)

### Interações
- [ ] Command Center abre/fecha com ⌘K
- [ ] Bottom Sheet com gestos de drag
- [ ] Zoom Semântico com animações
- [ ] Hover states em todos os botões
- [ ] Feedback visual em cliques

### Acessibilidade
- [ ] Contraste validado (Stark plugin)
- [ ] Ordem de foco definida
- [ ] Touch targets mínimos 44x44px
- [ ] Labels descritivos em ícones

### Handoff
- [ ] Especificações de espaçamento
- [ ] Cores anotadas com variáveis CSS
- [ ] Assets exportados (SVG, PNG)
- [ ] Design tokens exportados (JSON)

---

## 📚 Recursos

- [Figma Best Practices](https://www.figma.com/best-practices/)
- [ProtoPie](https://www.protopie.io/) — Gestos avançados
- [Tokens Studio](https://tokens.studio/) — Design tokens
- [Style Dictionary](https://amzn.github.io/style-dictionary/) — Build tokens

---

**Responsável:** Designer UX/UI + Product Owner
**Timeline Estimado:** 2-3 semanas
**Próximo Passo:** Validar com 5-10 usuários beta
