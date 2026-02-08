# WCAG 2.1 Level AA Compliance Checklist

**Projeto:** VivaCampo Spatial AI OS
**Versão:** 2.0.0
**Data:** 2026-02-07
**Nível Alvo:** WCAG 2.1 Level AA

---

## 📋 Visão Geral

Este documento serve como checklist de conformidade com as **Web Content Accessibility Guidelines (WCAG) 2.1 Level AA**. Todos os componentes do VivaCampo Spatial AI OS devem passar por esta auditoria antes de serem lançados.

### Estatísticas Atuais

- **Total de Critérios:** 50 (Level A + AA)
- **Implementados:** 0
- **Pendentes:** 50
- **Score Atual:** 0% → **Meta: 100%**

---

## 1. Perceptível (Perceivable)

Informação e componentes da interface devem ser apresentados aos usuários de forma que eles possam perceber.

### 1.1 Alternativas de Texto

#### 1.1.1 Conteúdo Não-Textual (Level A)

- [ ] **Imagens de Satélite:** Todas as imagens têm `alt` descritivo
  - Exemplo: `alt="Imagem de satélite do Talhão 4B em 15/01/2026 mostrando NDVI de 0.62"`
- [ ] **Ícones SVG:** Todos os ícones têm `aria-label` quando não há texto
  - Exemplo: `<svg aria-label="Fechar painel">...</svg>`
- [ ] **Imagens Decorativas:** Marcadas com `alt=""` ou `aria-hidden="true"`
- [ ] **Gráficos de NDVI:** Descrição alternativa em texto
  - Exemplo: "Gráfico mostrando evolução do NDVI de 0.45 em janeiro para 0.72 em março"

**Componentes Afetados:**
- Command Center (ícones de resultados)
- Field Dock (ícones de ferramentas)
- Bottom Sheets (gráficos e visualizações)
- Dynamic Island (ícones de status)

---

### 1.2 Mídias Baseadas em Tempo

#### 1.2.1 Apenas Áudio e Apenas Vídeo (Pré-gravado) (Level A)

- [ ] **Vídeos do Onboarding:** Legendas descritivas
- [ ] **Comandos de Voz:** Alternativa em texto sempre disponível

**Componentes Afetados:**
- Tour de Onboarding (se usar vídeos)
- Command Center (comandos de voz)

---

### 1.3 Adaptável

#### 1.3.1 Informação e Relações (Level A)

- [ ] **HTML Semântico:** Usar `<nav>`, `<main>`, `<section>`, `<article>`
  - Breadcrumb usa `<nav aria-label="Navegação estrutural">`
  - Command Center usa `<div role="search">`
  - Bottom Sheet usa `<div role="dialog">`
- [ ] **Estrutura de Headings:** Hierarquia lógica (h1 → h2 → h3)
- [ ] **Listas:** Usar `<ul>`, `<ol>` para listas
  - Resultados do Command Center usam `<ul role="listbox">`
- [ ] **Formulários:** Labels associados com `for`/`id`

**Componentes Afetados:**
- Todos os componentes espaciais

#### 1.3.2 Sequência Significativa (Level A)

- [ ] **Ordem de Leitura:** Ordem DOM = ordem visual
- [ ] **Tab Order:** Navegação por Tab segue fluxo lógico
  - Command Center → Field Dock → Bottom Sheet → Breadcrumb

#### 1.3.3 Características Sensoriais (Level A)

- [ ] **Não Apenas Cor:** Alertas críticos usam ícone + cor
  - ❌ Errado: "Clique no botão vermelho"
  - ✅ Certo: "Clique no botão 'Criar Alerta' (vermelho com ícone de sino)"
- [ ] **Não Apenas Posição:** "Clique no botão abaixo" → "Clique em 'Próximo'"

#### 1.3.4 Orientação (Level AA)

- [ ] **Rotação de Tela:** Mapa funciona em portrait e landscape
- [ ] **Sem Bloqueio:** Não bloquear orientação específica

#### 1.3.5 Identificar Propósito de Input (Level AA)

- [ ] **Autocomplete:** Usar atributos `autocomplete` corretos
  - Command Center: `<input autocomplete="off">`
  - Login: `<input type="email" autocomplete="email">`

---

### 1.4 Distinguível

#### 1.4.1 Uso de Cor (Level A)

- [ ] **Não Apenas Cor:** NDVI baixo = cor vermelha + ícone de alerta
- [ ] **Links:** Sublinhados ou outra distinção além de cor

#### 1.4.2 Controle de Áudio (Level A)

- [ ] **Auto-play > 3s:** Botão para pausar/parar
- [ ] **Comandos de Voz:** Botão mute sempre visível

#### 1.4.3 Contraste Mínimo (Level AA) — **CRÍTICO**

- [ ] **Texto Normal:** Contraste 4.5:1 mínimo
  - Testar: `--text-primary` (#0F172A) vs `white` = 17.9:1 ✅
  - Testar: `--text-secondary` (#475569) vs `white` = 7.5:1 ✅
  - Testar: `--text-muted` (#94A3B8) vs `white` = 3.4:1 ❌ **FALHA**
- [ ] **Texto Grande (18pt+):** Contraste 3:1 mínimo
- [ ] **Componentes de UI:** Contraste 3:1 mínimo
  - Testar: Bordas de inputs, ícones, estados de foco

**Ação Necessária:**
```css
/* Ajustar text-muted para AA compliance */
--text-muted: #64748B; /* Gray-500: 4.6:1 ✅ */
```

#### 1.4.4 Redimensionar Texto (Level AA)

- [ ] **Zoom 200%:** Interface funcional em 200% zoom
- [ ] **Sem Overflow:** Texto não sai do container

#### 1.4.5 Imagens de Texto (Level AA)

- [ ] **Evitar:** Usar texto real, não imagens de texto
- [ ] **Exceção:** Logos podem ser imagens

#### 1.4.10 Reflow (Level AA)

- [ ] **320px Width:** Conteúdo legível em 320px sem scroll horizontal
- [ ] **Mobile:** Bottom Sheets funcionam em telas pequenas

#### 1.4.11 Contraste Não-Textual (Level AA)

- [ ] **Componentes de UI:** Bordas de inputs, ícones = 3:1
- [ ] **Gráficos:** Linhas do gráfico de NDVI = 3:1

#### 1.4.12 Espaçamento de Texto (Level AA)

- [ ] **Line Height:** Mínimo 1.5x (body usa 1.5 ✅)
- [ ] **Espaço entre Parágrafos:** 2x font size
- [ ] **Letter Spacing:** Mínimo 0.12x
- [ ] **Word Spacing:** Mínimo 0.16x

#### 1.4.13 Conteúdo em Hover ou Foco (Level AA)

- [ ] **Tooltips:**
  - Podem ser dispensados (tecla Esc)
  - Podem ser hoverados (não desaparecem ao mover mouse)
  - Persistem até usuário dismissar ou informação deixar de ser válida

---

## 2. Operável (Operable)

Componentes da interface e navegação devem ser operáveis.

### 2.1 Acessível por Teclado

#### 2.1.1 Teclado (Level A) — **CRÍTICO**

- [ ] **Command Center:**
  - `⌘K` / `Ctrl+K` abre
  - `↑↓` navega resultados
  - `Enter` executa comando
  - `Esc` fecha
- [ ] **Field Dock:**
  - `Tab` para navegar ferramentas
  - `Enter` / `Space` ativa ferramenta
- [ ] **Bottom Sheet:**
  - `Tab` navega dentro do sheet
  - `Esc` fecha
- [ ] **Zoom Semântico:**
  - `1`, `2`, `3` muda nível
  - `+` / `-` zoom in/out
  - `↑↓←→` pan no mapa

#### 2.1.2 Sem Trap de Teclado (Level A)

- [ ] **Modais:** Focus trap funcional (Tab circula dentro do modal)
- [ ] **Bottom Sheet:** `Esc` ou `Shift+Tab` permite sair

#### 2.1.4 Atalhos de Caractere (Level A)

- [ ] **Atalhos Únicos:** Podem ser desativados ou remapeados
- [ ] **Atalhos com Modificador:** Preferir `⌘K` a apenas `K`

---

### 2.2 Tempo Suficiente

#### 2.2.1 Ajuste de Tempo (Level A)

- [ ] **Auto-refresh:** Pode ser pausado/parado
  - Dados do mapa não auto-refresh sem controle do usuário

#### 2.2.2 Pausar, Parar, Esconder (Level A)

- [ ] **Animações > 5s:** Podem ser pausadas
  - Animação de Loading do mapa

---

### 2.3 Convulsões e Reações Físicas

#### 2.3.1 Três Flashes ou Abaixo do Limite (Level A)

- [ ] **Sem Flashes:** Nenhum componente pisca > 3x por segundo
- [ ] **Alertas Críticos:** Não usar flash vermelho

---

### 2.4 Navegável

#### 2.4.1 Pular Blocos (Level A)

- [ ] **Skip Links:** "Pular para mapa principal", "Pular para comandos"
```html
<a href="#map-container" class="sr-only focus:not-sr-only">
  Pular para mapa principal
</a>
```

#### 2.4.2 Título da Página (Level A)

- [ ] **Títulos Únicos:** Cada página tem título descritivo
  - `/map` → "Mapa Espacial | VivaCampo"
  - `/map/farms/[id]` → "Fazenda Santa Maria | VivaCampo"

#### 2.4.3 Ordem de Foco (Level A)

- [ ] **Tab Order:** Segue ordem visual
  - Dynamic Island → Breadcrumb → Mapa → Field Dock → Bottom Sheet

#### 2.4.4 Propósito do Link (Em Contexto) (Level A)

- [ ] **Links Descritivos:** Evitar "clique aqui"
  - ❌ "Para mais detalhes, clique aqui"
  - ✅ "Ver detalhes do Talhão 4B"

#### 2.4.5 Múltiplas Formas (Level AA)

- [ ] **Navegação Diversa:**
  - Breadcrumb (navegação estrutural)
  - Command Center (busca/comandos)
  - Mini-Mapa (navegação espacial)
  - Field Dock (ferramentas contextuais)

#### 2.4.6 Headings e Labels (Level AA)

- [ ] **Headings Descritivos:** "Detalhes do Talhão 4B" não "Detalhes"
- [ ] **Labels Descritivos:** "Buscar fazendas" não "Buscar"

#### 2.4.7 Foco Visível (Level AA) — **CRÍTICO**

- [ ] **Outline de Foco:** 2px sólido, contraste 3:1
```css
*:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
```

---

### 2.5 Modalidades de Input

#### 2.5.1 Gestos de Ponteiro (Level A)

- [ ] **Gestos Simples:** Todas as funções usam single tap/click
- [ ] **Bottom Sheet:** Swipe down + botão "Fechar"

#### 2.5.2 Cancelamento de Ponteiro (Level A)

- [ ] **Down Event:** Não usar `mousedown` para ações críticas
- [ ] **Up Event:** Usar `click` (permite cancelar arrastando fora)

#### 2.5.3 Label em Nome (Level A)

- [ ] **Texto Visível = Nome Acessível:**
  - Se botão mostra "Criar Alerta", `aria-label` deve incluir "Criar Alerta"

#### 2.5.4 Ativação por Movimento (Level A)

- [ ] **Alternativa:** Gestos de shake/inclinação têm alternativa por botão
- [ ] **Desabilitar:** Pode desabilitar ativação por movimento

---

## 3. Compreensível (Understandable)

Informação e operação da interface devem ser compreensíveis.

### 3.1 Legível

#### 3.1.1 Linguagem da Página (Level A)

- [ ] **HTML Lang:** `<html lang="pt-BR">`
- [ ] **Mudanças de Idioma:** Marcar com `lang` se houver

#### 3.1.2 Linguagem de Partes (Level AA)

- [ ] **Termos Técnicos:** Se usar termos em inglês, marcar
  - "NDVI" → `<abbr title="Normalized Difference Vegetation Index">NDVI</abbr>`

---

### 3.2 Previsível

#### 3.2.1 Em Foco (Level A)

- [ ] **Foco Não Muda Contexto:** Focus em input não submete form
- [ ] **Command Center:** Focus em input não executa comando

#### 3.2.2 Em Input (Level A)

- [ ] **Input Não Muda Contexto:** Digitar não muda página
- [ ] **Seleção de Camada:** Mudar camada não redireciona

#### 3.2.3 Navegação Consistente (Level AA)

- [ ] **Componentes Fixos:** Field Dock sempre no mesmo lugar
- [ ] **Breadcrumb:** Sempre no topo-esquerdo

#### 3.2.4 Identificação Consistente (Level AA)

- [ ] **Ícones Consistentes:** Ícone de "Fechar" sempre o mesmo
- [ ] **Terminologia:** "Talhão" sempre "Talhão", não misturar com "Field"

---

### 3.3 Assistência de Input

#### 3.3.1 Identificação de Erro (Level A)

- [ ] **Erros Descritivos:** "Campo obrigatório: Nome da Fazenda"
- [ ] **Localização:** Erro próximo ao campo com problema

#### 3.3.2 Labels ou Instruções (Level A)

- [ ] **Labels Sempre:** Todos os inputs têm `<label>`
- [ ] **Placeholders Não Bastam:** Usar label + placeholder

#### 3.3.3 Sugestão de Erro (Level AA)

- [ ] **Sugestões:** "Email inválido. Formato correto: nome@exemplo.com"

#### 3.3.4 Prevenção de Erro (Legal, Financeiro, Dados) (Level AA)

- [ ] **Confirmação:** Deletar fazenda exige confirmação
- [ ] **Reversível:** Ações críticas podem ser desfeitas (undo)

---

## 4. Robusto (Robust)

Conteúdo deve ser robusto o suficiente para ser interpretado por uma variedade de user agents, incluindo tecnologias assistivas.

### 4.1 Compatível

#### 4.1.1 Parsing (Level A) — **OBSOLETO EM WCAG 2.2**

- [ ] **HTML Válido:** Validar com W3C Validator
- [ ] **IDs Únicos:** Sem IDs duplicados

#### 4.1.2 Nome, Função, Valor (Level A)

- [ ] **Componentes Customizados:** Têm roles ARIA apropriados
  - Command Center: `role="search"`
  - Bottom Sheet: `role="dialog"`
  - Resultados: `role="listbox"` + `role="option"`
- [ ] **Estados:** Comunicados via ARIA
  - `aria-selected="true"`
  - `aria-expanded="false"`
  - `aria-hidden="true"`

#### 4.1.3 Mensagens de Status (Level AA)

- [ ] **ARIA Live:** Mudanças dinâmicas anunciadas
```html
<div role="status" aria-live="polite" aria-atomic="true">
  Processando nova imagem... 30%
</div>

<div role="alert" aria-live="assertive">
  Erro crítico: Falha ao carregar dados do talhão
</div>
```

**Componentes Afetados:**
- Dynamic Island (`aria-live="polite"`)
- Loading States (`aria-live="polite"`)
- Erros Críticos (`aria-live="assertive"`)

---

## 🛠️ Ferramentas de Auditoria

### Automatizadas

1. **axe DevTools** (Chrome/Firefox Extension)
   - Detecta ~57% dos problemas de acessibilidade
   - Gratuito e rápido

2. **Lighthouse** (Chrome DevTools)
   - Score de 0-100
   - **Meta: > 90**

3. **WAVE** (WebAIM)
   - Visualização de erros inline
   - Bom para contraste de cor

### Manuais

1. **Navegação por Teclado:**
   - Desconectar mouse
   - Navegar apenas com Tab, Enter, Esc, setas

2. **Screen Reader:**
   - **Windows:** NVDA (gratuito)
   - **Mac:** VoiceOver (built-in)
   - **Chrome:** ChromeVox

3. **Contraste de Cor:**
   - [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

---

## 📊 Relatório de Auditoria (Template)

### Componente: [Nome do Componente]

**Data:** YYYY-MM-DD
**Auditor:** [Nome]
**Ferramentas:** axe DevTools, NVDA, Lighthouse

#### Resultados

| Critério | Status | Notas |
|----------|--------|-------|
| 1.4.3 Contraste | ❌ Falha | `text-muted` tem apenas 3.4:1 |
| 2.1.1 Teclado | ✅ Passa | Todos os controles acessíveis |
| 2.4.7 Foco Visível | ✅ Passa | Outline verde 2px |

#### Lighthouse Score

- **Acessibilidade:** 87/100
- **Performance:** 92/100
- **Best Practices:** 95/100

#### Ações Necessárias

1. Ajustar `--text-muted` para `#64748B` (contraste 4.6:1)
2. Adicionar `aria-live` na Dynamic Island
3. Testar com NVDA em navegação completa

---

## ✅ Checklist Resumido (Pré-Deploy)

Antes de lançar qualquer componente:

### Automatizado
- [ ] Lighthouse Accessibility > 90
- [ ] axe DevTools: 0 erros críticos
- [ ] WAVE: 0 erros

### Manual
- [ ] Navegação completa apenas com teclado
- [ ] Teste com NVDA/VoiceOver (5 min mínimo)
- [ ] Contraste validado (WebAIM)
- [ ] Zoom 200% sem quebra de layout
- [ ] Teste em 320px width (mobile)

### Documentação
- [ ] ARIA roles documentados
- [ ] Atalhos de teclado documentados
- [ ] Relatório de auditoria preenchido

---

## 📚 Recursos

- [WCAG 2.1 Guia Completo (PT-BR)](https://guia-wcag.com/)
- [WebAIM Checklist](https://webaim.org/standards/wcag/checklist)
- [A11y Project](https://www.a11yproject.com/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)

---

**Próxima Revisão:** Mensal
**Responsável:** Equipe Frontend + QA
