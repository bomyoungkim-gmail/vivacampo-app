# 📘 Guia de Componentes UI/UX - VivaCampo

Guia prático para desenvolvedores sobre como usar os novos componentes e padrões.

## 🎯 Quick Start

### 1. Criar Nova Página

```tsx
'use client'

import ClientLayout from '@/components/ClientLayout'
import { DashboardSkeleton } from '@/components/LoadingSkeleton'

export default function MinhaPage() {
    const [loading, setLoading] = useState(true)

    if (loading) {
        return (
            <ClientLayout>
                <DashboardSkeleton />
            </ClientLayout>
        )
    }

    return (
        <ClientLayout>
            <div className="mb-4 sm:mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                    Meu Título
                </h2>
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    Descrição
                </p>
            </div>

            {/* Seu conteúdo aqui */}
        </ClientLayout>
    )
}
```

---

## 🧩 Componentes Disponíveis

### ClientLayout

**Uso**: Wrapper padrão para todas as páginas autenticadas.

```tsx
import ClientLayout from '@/components/ClientLayout'

<ClientLayout>
    {/* Seu conteúdo */}
</ClientLayout>
```

**Fornece**:
- Header com logo e logout
- Desktop navigation
- Mobile navigation (bottom bar)
- Dark mode toggle
- Padding consistente

---

### MobileNav

**Uso**: Já incluído no ClientLayout, não precisa importar separadamente.

**Customizar rotas**:
```tsx
// Em MobileNav.tsx
const navItems = [
    { href: routes.dashboard, label: 'Dashboard', icon: DashboardIcon },
    { href: routes.farms, label: 'Fazendas', icon: FarmIcon },
    // ... adicione mais
]
```

---

### Loading Skeletons

**Quando usar**: No lugar de spinners para melhor UX.

#### Dashboard Skeleton
```tsx
import { DashboardSkeleton } from '@/components/LoadingSkeleton'

if (loading) {
    return <DashboardSkeleton />
}
```

#### Card Skeleton
```tsx
import { CardSkeleton } from '@/components/LoadingSkeleton'

<div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
    {loading ? (
        <>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
        </>
    ) : (
        // Seus cards reais
    )}
</div>
```

#### List Skeleton
```tsx
import { TableSkeleton } from '@/components/LoadingSkeleton'

{loading ? (
    <TableSkeleton rows={5} />
) : (
    <YourTable data={data} />
)}
```

---

### Empty States

**Quando usar**: Quando uma lista/grid está vazio.

#### Empty Farms
```tsx
import { EmptyFarms } from '@/components/EmptyState'

{farms.length === 0 ? (
    <EmptyFarms onCreate={() => setShowModal(true)} />
) : (
    <FarmsGrid farms={farms} />
)}
```

#### Empty Signals
```tsx
import { EmptySignals } from '@/components/EmptyState'

{signals.length === 0 ? (
    <EmptySignals />
) : (
    <SignalsList signals={signals} />
)}
```

#### Empty State Customizado
```tsx
import { EmptyState } from '@/components/EmptyState'

<EmptyState
    icon={<YourIcon />}
    title="Nenhum item encontrado"
    description="Adicione seu primeiro item para começar."
    action={{
        label: "Adicionar item",
        onClick: handleAdd
    }}
/>
```

---

### Theme Toggle

**Uso**: Já incluído no ClientLayout.

**Uso standalone**:
```tsx
import ThemeToggle from '@/components/ThemeToggle'

<ThemeToggle />
```

**Acessar tema atual**:
```tsx
import { useTheme } from '@/contexts/ThemeContext'

function MyComponent() {
    const { theme, effectiveTheme, setTheme } = useTheme()

    // theme: 'light' | 'dark' | 'system'
    // effectiveTheme: 'light' | 'dark' (resolvido)

    return <div>Current theme: {effectiveTheme}</div>
}
```

---

## 🎨 Padrões de Estilo

### Cards Responsivos

```tsx
<div className="rounded-lg bg-white dark:bg-gray-800
                p-4 sm:p-6
                shadow dark:shadow-gray-700/50
                hover:shadow-md
                transition-colors">
    {/* Conteúdo */}
</div>
```

### Headers de Seção

```tsx
<div className="mb-4 sm:mb-6">
    <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
        Título
    </h2>
    <p className="mt-1 text-xs sm:text-sm text-gray-600 dark:text-gray-400">
        Descrição
    </p>
</div>
```

### Grids Responsivos

```tsx
{/* 1 coluna mobile, 2 tablet, 3 desktop */}
<div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
    {items.map(item => (
        <Card key={item.id} />
    ))}
</div>
```

### Botões

```tsx
{/* Botão primário */}
<button className="rounded-lg bg-green-600 px-4 py-2
                   text-sm font-semibold text-white
                   hover:bg-green-700
                   disabled:opacity-50
                   min-h-touch
                   transition-colors">
    Ação Principal
</button>

{/* Botão secundário */}
<button className="rounded-lg border border-gray-300 dark:border-gray-600
                   bg-white dark:bg-gray-800
                   px-4 py-2 text-sm font-medium
                   text-gray-700 dark:text-gray-200
                   hover:bg-gray-50 dark:hover:bg-gray-700
                   min-h-touch
                   transition-colors">
    Ação Secundária
</button>
```

### Inputs

```tsx
<input
    type="text"
    className="flex-1 rounded-lg
               border border-gray-300 dark:border-gray-600
               bg-white dark:bg-gray-800
               text-gray-900 dark:text-white
               px-3 sm:px-4 py-2
               text-sm
               focus:border-green-500 dark:focus:border-green-400
               focus:outline-none
               focus:ring-1 focus:ring-green-500
               min-h-touch
               transition-colors"
    placeholder="Digite aqui..."
/>
```

### Modais Responsivos

```tsx
<div className="fixed inset-0 z-50 flex items-center justify-center
                bg-black bg-opacity-50 p-4">
    <div className="w-full max-w-md rounded-lg
                    bg-white dark:bg-gray-800
                    p-4 sm:p-6
                    shadow-xl dark:shadow-gray-700/50">
        <h2 className="text-lg sm:text-xl font-bold
                       text-gray-900 dark:text-white">
            Título do Modal
        </h2>
        {/* Conteúdo */}
    </div>
</div>
```

---

## 📏 Espaçamento Padrão

### Padding

| Uso | Mobile | Desktop |
|-----|--------|---------|
| Cards | `p-4` | `sm:p-6` |
| Containers | `px-4 py-4` | `sm:px-6 sm:py-8` |
| Modais | `p-4` | `sm:p-6` |

### Gap

| Uso | Mobile | Desktop |
|-----|--------|---------|
| Grid | `gap-4` | `sm:gap-6` |
| Flex | `gap-2` | `sm:gap-3` |
| Stack | `space-y-3` | `sm:space-y-4` |

### Margin

| Uso | Mobile | Desktop |
|-----|--------|---------|
| Seções | `mb-4` | `sm:mb-6` |
| Entre elementos | `mt-2` | `sm:mt-3` |

---

## 🎨 Cores por Contexto

### Backgrounds

```tsx
// Page background
className="bg-gray-50 dark:bg-gray-900"

// Card background
className="bg-white dark:bg-gray-800"

// Hover background
className="hover:bg-gray-50 dark:hover:bg-gray-700/50"
```

### Texto

```tsx
// Título principal
className="text-gray-900 dark:text-white"

// Texto secundário
className="text-gray-600 dark:text-gray-400"

// Texto desabilitado
className="text-gray-500 dark:text-gray-500"
```

### Bordas

```tsx
// Borda padrão
className="border-gray-200 dark:border-gray-700"

// Borda de foco
className="focus:border-green-500 dark:focus:border-green-400"
```

### Sombras

```tsx
// Sombra padrão
className="shadow dark:shadow-gray-700/50"

// Sombra hover
className="hover:shadow-md dark:hover:shadow-gray-600/50"
```

---

## ✅ Checklist para Nova Página

- [ ] Usa `ClientLayout` wrapper
- [ ] Implementa loading skeleton
- [ ] Implementa empty state
- [ ] Typography responsiva (`text-xs sm:text-sm`)
- [ ] Spacing responsivo (`p-4 sm:p-6`)
- [ ] Dark mode classes (`dark:`)
- [ ] Touch targets (`min-h-touch`)
- [ ] Transitions (`transition-colors`)
- [ ] Hover states
- [ ] Grid/Flex responsivo

---

## 🚫 Evitar

### ❌ NÃO Fazer

```tsx
// Tamanhos fixos
className="text-sm"  // Sempre adicione variantes responsivas

// Sem dark mode
className="bg-white text-gray-900"  // Adicione dark:

// Botões pequenos
<button className="px-2 py-1">  // Use min-h-touch

// Spinners simples
{loading && <Spinner />}  // Use Skeletons

// Empty state vazio
{items.length === 0 && <p>Vazio</p>}  // Use EmptyState component
```

### ✅ Fazer

```tsx
// Responsivo
className="text-xs sm:text-sm"

// Com dark mode
className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white"

// Touch friendly
<button className="px-4 py-2 min-h-touch">

// UX melhorada
{loading ? <CardSkeleton /> : <Card />}

// Guiar o usuário
{items.length === 0 ? <EmptyState /> : <List />}
```

---

## 🎯 Exemplos Completos

### Página de Lista

```tsx
'use client'

import { useState, useEffect } from 'react'
import ClientLayout from '@/components/ClientLayout'
import { TableSkeleton } from '@/components/LoadingSkeleton'
import { EmptyState } from '@/components/EmptyState'

export default function MyListPage() {
    const [items, setItems] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        loadItems()
    }, [])

    const loadItems = async () => {
        setLoading(true)
        try {
            const data = await fetchItems()
            setItems(data)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <ClientLayout>
                <TableSkeleton rows={5} />
            </ClientLayout>
        )
    }

    return (
        <ClientLayout>
            <div className="mb-4 sm:mb-6">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                    Minha Lista
                </h2>
                <p className="mt-1 text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                    Gerencie seus itens
                </p>
            </div>

            {items.length === 0 ? (
                <EmptyState
                    icon={<YourIcon />}
                    title="Nenhum item ainda"
                    description="Comece adicionando seu primeiro item"
                    action={{
                        label: "Adicionar item",
                        onClick: () => setShowModal(true)
                    }}
                />
            ) : (
                <div className="rounded-lg bg-white dark:bg-gray-800 shadow dark:shadow-gray-700/50">
                    {items.map(item => (
                        <ItemRow key={item.id} item={item} />
                    ))}
                </div>
            )}
        </ClientLayout>
    )
}
```

### Página com Grid

```tsx
'use client'

import ClientLayout from '@/components/ClientLayout'
import { GridCardSkeleton } from '@/components/LoadingSkeleton'

export default function MyGridPage() {
    const [items, setItems] = useState([])
    const [loading, setLoading] = useState(true)

    if (loading) {
        return (
            <ClientLayout>
                <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                    <GridCardSkeleton />
                    <GridCardSkeleton />
                    <GridCardSkeleton />
                </div>
            </ClientLayout>
        )
    }

    return (
        <ClientLayout>
            <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                {items.map(item => (
                    <div
                        key={item.id}
                        className="rounded-lg bg-white dark:bg-gray-800
                                   p-4 sm:p-6 shadow dark:shadow-gray-700/50
                                   hover:shadow-md transition-all cursor-pointer"
                        onClick={() => handleClick(item)}
                    >
                        {/* Card content */}
                    </div>
                ))}
            </div>
        </ClientLayout>
    )
}
```

---

## 🔧 Utilitários Úteis

### Scrollbar Hide

```tsx
<div className="overflow-x-auto scrollbar-hide">
    {/* Conteúdo com scroll horizontal sem scrollbar */}
</div>
```

### Safe Area

```tsx
<div className="pb-16 lg:pb-0">
    {/* Padding bottom para bottom nav em mobile */}
</div>
```

### Truncate

```tsx
<p className="truncate max-w-[200px]">
    Texto muito longo que será cortado...
</p>
```

---

## 📚 Recursos Adicionais

- [Tailwind CSS Docs](https://tailwindcss.com)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Material Design](https://material.io/design)

---

**Última atualização**: Janeiro 2026
