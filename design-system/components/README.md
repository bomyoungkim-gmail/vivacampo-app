# VivaCampo Component Library

**Versão:** 2.0.0 (Spatial AI OS)
**Framework:** React + Next.js + Tailwind CSS
**Documentação:** Storybook

---

## 📚 Visão Geral

Este diretório contém todos os componentes reutilizáveis do VivaCampo Spatial AI OS. Cada componente é documentado no Storybook e segue os padrões do Design System definido em `design-system/MASTER.md`.

---

## 🗂️ Estrutura de Pastas

```
design-system/components/
├── README.md                    # Este arquivo
├── .storybook/                  # Configuração do Storybook
│   ├── main.ts
│   ├── preview.ts
│   └── preview-head.html
├── base/                        # Componentes base (botões, inputs, cards)
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.stories.tsx
│   │   ├── Button.test.tsx
│   │   └── index.ts
│   ├── Input/
│   ├── Card/
│   └── index.ts
├── spatial/                     # Componentes espaciais (específicos do Spatial AI OS)
│   ├── CommandCenter/
│   │   ├── CommandCenter.tsx
│   │   ├── CommandCenter.stories.tsx
│   │   ├── CommandCenter.test.tsx
│   │   ├── useCommandCenter.ts  # Hook customizado
│   │   └── index.ts
│   ├── DynamicIsland/
│   ├── FieldDock/
│   ├── BottomSheet/
│   ├── BreadcrumbFloating/
│   ├── MiniMap/
│   └── index.ts
├── layouts/                     # Layouts e containers
│   ├── MapLayout/
│   └── index.ts
└── utils/                       # Utilitários compartilhados
    ├── cn.ts                    # Merge de classes Tailwind
    ├── a11y.ts                  # Helpers de acessibilidade
    └── index.ts
```

---

## 🚀 Setup do Storybook

### 1. Instalação

```bash
# Instalar Storybook
npx storybook@latest init

# Instalar addons essenciais
npm install --save-dev @storybook/addon-a11y @storybook/addon-interactions
```

### 2. Configuração (`.storybook/main.ts`)

```typescript
import type { StorybookConfig } from '@storybook/nextjs';

const config: StorybookConfig = {
  stories: [
    '../design-system/components/**/*.stories.@(js|jsx|ts|tsx)',
    '../design-system/components/**/*.mdx',
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y', // ✅ Auditoria de acessibilidade
  ],
  framework: {
    name: '@storybook/nextjs',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
};

export default config;
```

### 3. Preview Global (`.storybook/preview.ts`)

```typescript
import type { Preview } from '@storybook/react';
import '../design-system/tokens.css'; // ✅ Importar tokens

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#FFFFFF' },
        { name: 'dark', value: '#0F172A' },
        { name: 'map', value: '#E5E7EB' }, // Simular fundo de mapa
      ],
    },
  },
};

export default preview;
```

### 4. Rodar Storybook

```bash
npm run storybook
```

Abrir em: `http://localhost:6006`

---

## 📝 Padrão de Componente

Cada componente segue esta estrutura:

### Exemplo: Button

#### `Button.tsx`

```typescript
import * as React from 'react';
import { cn } from '../utils/cn';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Variante visual do botão */
  variant?: 'primary' | 'secondary' | 'ghost';

  /** Tamanho do botão */
  size?: 'sm' | 'md' | 'lg';

  /** Se verdadeiro, mostra estado de loading */
  isLoading?: boolean;

  /** Ícone à esquerda do texto */
  leftIcon?: React.ReactNode;

  /** Ícone à direita do texto */
  rightIcon?: React.ReactNode;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles = 'inline-flex items-center justify-center gap-2 font-medium transition-fast touch-target';

    const variants = {
      primary: 'bg-primary text-white hover:bg-primary-dark',
      secondary: 'bg-transparent border border-gray-300 text-gray-900 hover:bg-gray-100',
      ghost: 'bg-transparent text-gray-600 hover:bg-gray-100 hover:text-gray-900',
    };

    const sizes = {
      sm: 'px-3 py-2 text-sm rounded-md',
      md: 'px-6 py-3 text-base rounded-lg',
      lg: 'px-8 py-4 text-lg rounded-xl',
    };

    return (
      <button
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          (disabled || isLoading) && 'opacity-50 cursor-not-allowed',
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <svg className="animate-spin h-5 w-5" aria-hidden="true">
            {/* Spinner SVG */}
          </svg>
        ) : (
          <>
            {leftIcon && <span aria-hidden="true">{leftIcon}</span>}
            {children}
            {rightIcon && <span aria-hidden="true">{rightIcon}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button };
```

#### `Button.stories.tsx`

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta = {
  title: 'Base/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'ghost'],
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Criar Alerta',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Cancelar',
  },
};

export const WithIcon: Story = {
  args: {
    variant: 'primary',
    children: 'Adicionar Fazenda',
    leftIcon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
    ),
  },
};

export const Loading: Story = {
  args: {
    variant: 'primary',
    children: 'Processando...',
    isLoading: true,
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex gap-4">
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="ghost">Ghost</Button>
    </div>
  ),
};
```

#### `Button.test.tsx`

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button', () => {
  it('renderiza o texto corretamente', () => {
    render(<Button>Clique aqui</Button>);
    expect(screen.getByText('Clique aqui')).toBeInTheDocument();
  });

  it('chama onClick quando clicado', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Clique</Button>);

    await userEvent.click(screen.getByText('Clique'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('não chama onClick quando disabled', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick} disabled>Clique</Button>);

    await userEvent.click(screen.getByText('Clique'));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('mostra loading spinner quando isLoading', () => {
    render(<Button isLoading>Processando</Button>);
    expect(screen.getByRole('button')).toHaveClass('opacity-50');
  });
});
```

---

## 🧩 Tokens e Utilitários (Glassmorphism)

Os tokens vivem em `design-system/tokens.css`. Use as classes abaixo para manter consistência visual:

- `glass-morphism`: overlays flutuantes (Command Center, Dynamic Island)
- `glass-panel`: cards/painéis inline
- `glass-panel-subtle`: painéis discretos no mapa
- `glass-border`: borda de vidro isolada

Sempre preferir tokens CSS (`var(--*)`) em vez de valores hardcoded.

---

## 🎨 Componentes por Prioridade

### Fase 0-1 (ALTA PRIORIDADE)

#### 1. Command Center

**Localização:** `spatial/CommandCenter/`

**Props:**
```typescript
interface CommandCenterProps {
  /** Se verdadeiro, o Command Center está aberto */
  isOpen: boolean;

  /** Callback ao fechar */
  onClose: () => void;

  /** Placeholder do input */
  placeholder?: string;

  /** Comandos disponíveis */
  commands: Command[];

  /** Callback ao executar comando */
  onExecuteCommand: (command: Command) => void;
}

interface Command {
  id: string;
  label: string;
  icon?: React.ReactNode;
  keywords: string[];
  action: () => void;
}
```

**Stories:**
- Default (aberto)
- Com resultados de busca
- Vazio (sem resultados)
- Loading

**Acessibilidade:**
- `role="search"`
- `aria-label="Centro de Comandos IA"`
- Navegação por setas ↑↓
- Esc fecha

---

#### 2. Dynamic Island

**Localização:** `spatial/DynamicIsland/`

**Props:**
```typescript
interface DynamicIslandProps {
  /** Conteúdo a ser exibido */
  children: React.ReactNode;

  /** Estado atual (neutral, selection, action) */
  state?: 'neutral' | 'selection' | 'action';
}
```

**Stories:**
- Neutral ("Boa tarde, João")
- Selection ("Talhão 4B • Soja")
- Action ("Processando... 30%")

**Acessibilidade:**
- `role="status"`
- `aria-live="polite"`

---

#### 3. Field Dock

**Localização:** `spatial/FieldDock/`

**Props:**
```typescript
interface FieldDockProps {
  /** Ferramentas disponíveis */
  tools: Tool[];

  /** Ferramenta ativa */
  activeTool?: string;

  /** Callback ao selecionar ferramenta */
  onSelectTool: (toolId: string) => void;
}

interface Tool {
  id: string;
  icon: React.ReactNode;
  label: string;
  tooltip: string;
}
```

**Stories:**
- Com todas as ferramentas
- Com ferramenta ativa
- Context-aware (muda por zoom)

**Acessibilidade:**
- `aria-label` em cada ferramenta
- `aria-pressed="true"` para ativa
- Touch target 44x44px

---

#### 4. Bottom Sheet

**Localização:** `spatial/BottomSheet/`

**Props:**
```typescript
interface BottomSheetProps {
  /** Se verdadeiro, o sheet está aberto */
  isOpen: boolean;

  /** Callback ao fechar */
  onClose: () => void;

  /** Nível inicial (peek, half, full) */
  initialLevel?: 'peek' | 'half' | 'full';

  /** Conteúdo do sheet */
  children: React.ReactNode;

  /** Título do sheet */
  title: string;
}
```

**Stories:**
- Peek (50vh)
- Half (75vh)
- Full (100vh)
- Com gestos (demo)

**Acessibilidade:**
- `role="dialog"`
- `aria-modal="true"`
- Focus trap
- Esc fecha

---

#### 5. Breadcrumb Floating

**Localização:** `spatial/BreadcrumbFloating/`

**Props:**
```typescript
interface BreadcrumbFloatingProps {
  /** Itens do breadcrumb */
  items: BreadcrumbItem[];
}

interface BreadcrumbItem {
  label: string;
  href?: string;
  isCurrent?: boolean;
}
```

**Stories:**
- Com 2 níveis
- Com 3+ níveis
- Mobile (colapsa)

**Acessibilidade:**
- `<nav aria-label="Navegação estrutural">`
- `aria-current="page"` no item atual

---

### Fase 2 (MÉDIA PRIORIDADE)

- Mini-Mapa
- Toast/Notifications
- Loading States (skeleton screens)
- Zoom Controls

---

### Fase 3 (BAIXA PRIORIDADE)

- Tour de Onboarding
- Split View (comparação)
- Crop Feed

---

## 🧪 Testes

### Rodar Testes

```bash
# Testes unitários
npm test

# Coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

### Padrão de Teste

Cada componente deve ter:

1. **Renderização básica**
2. **Interações (click, hover, keyboard)**
3. **Acessibilidade (roles, labels)**
4. **Estados (loading, error, disabled)**

---

## 📊 Auditoria de Acessibilidade

### No Storybook

1. Abrir componente no Storybook
2. Abrir aba "Accessibility"
3. Verificar 0 violations

### Via Linha de Comando

```bash
# Instalar axe-core
npm install --save-dev @axe-core/cli

# Rodar auditoria
npx axe http://localhost:6006/iframe.html?id=base-button--primary
```

### Gate automatizado (Storybook + a11y)

```bash
# Executa stories com interacoes e checagens de acessibilidade
npm run test:a11y
```

---

## 📚 Recursos

- [Storybook Docs](https://storybook.js.org/docs/react/get-started/introduction)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Radix UI](https://www.radix-ui.com/) — Primitives para componentes acessíveis
- [Headless UI](https://headlessui.com/) — Componentes acessíveis unstyled

---

## ✅ Checklist de Novo Componente

Antes de criar um PR com novo componente:

- [ ] Componente criado em `base/` ou `spatial/`
- [ ] TypeScript com tipos exportados
- [ ] Stories do Storybook (mínimo 3)
- [ ] Testes unitários (mínimo 4)
- [ ] Acessibilidade auditada (0 violations)
- [ ] Documentação JSDoc
- [ ] Exportado em `index.ts`
- [ ] Design tokens usados (não valores hardcoded)
- [ ] Responsivo (testado em 375px, 768px, 1024px)
- [ ] Dark mode funcional

---

## ⌨️ Atalhos Globais (Spatial OS)

| Atalho | Ação |
| --- | --- |
| Ctrl+K / ⌘K | Abrir Command Center |
| Esc | Fechar overlays e menus |
| 1 | Macro view (zoom semantico) |
| 2 | Meso view (zoom semantico) |
| 3 | Micro view (zoom semantico) |

Fonte: `design-system/components/utils/a11y.ts`

---

**Responsável:** Equipe Frontend
**Próxima Revisão:** Após cada sprint
