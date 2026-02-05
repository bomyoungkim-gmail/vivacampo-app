# Admin UI - Design System Documentation

**Version:** 1.3 (Phase 3)
**Created:** 2026-02-04
**Last Updated:** 2026-02-05
**Product:** VivaCampo Admin Panel

---

## Overview

The Admin UI design system provides a consistent, accessible, and maintainable component library for the VivaCampo admin panel. Built with **Tailwind CSS**, **Next.js 14**, and **TypeScript**, it follows **WCAG AAA** accessibility standards.

---

## Design Principles

1. **Consistency** - Same visual language across all pages
2. **Accessibility** - WCAG AAA compliance (4.5:1 contrast, 44px touch targets)
3. **Dark Mode First** - Full support for light and dark themes
4. **Data-Focused** - Optimized for admin dashboards and monitoring
5. **Mobile-First** - Responsive from 375px to 1440px+

---

## Design Tokens

All design tokens are defined as CSS custom properties in [src/app/globals.css](src/app/globals.css).

### Color Palette

#### Light Mode
```css
--foreground: 222.2 84% 4.9%       /* Dark text */
--background: 0 0% 100%            /* White background */
--primary: 142.1 76.2% 36.3%       /* Emerald/Teal green */
--destructive: 0 84.2% 60.2%       /* Red */
--muted: 210 40% 96.1%             /* Light gray */
--border: 214.3 31.8% 91.4%        /* Border gray */
```

#### Dark Mode
```css
--foreground: 210 40% 98%          /* Light text */
--background: 222.2 84% 4.9%       /* Very dark */
--primary: 142.1 70.6% 45.3%       /* Lighter green */
--destructive: 0 62.8% 30.6%       /* Darker red */
--muted: 217.2 32.6% 17.5%         /* Dark gray */
--border: 217.2 32.6% 17.5%        /* Border dark */
```

#### Chart Colors
```css
--chart-1: 142 76% 36%    /* Green - Primary */
--chart-2: 221 83% 53%    /* Blue - Secondary */
--chart-3: 38 92% 50%     /* Orange - Warning */
--chart-4: 262 83% 58%    /* Purple - Info */
--chart-5: 0 84% 60%      /* Red - Danger */
```

### Usage in Components

**DO:**
```tsx
<div className="bg-background text-foreground border-border">
```

**DON'T:**
```tsx
<div className="bg-white text-gray-800 border-gray-200">
```

---

## Typography

### Font Families

The design system uses two carefully selected Google Fonts:

**Primary (UI):** Fira Sans
- Weights: 300 (Light), 400 (Regular), 500 (Medium), 600 (SemiBold), 700 (Bold)
- Usage: All UI text, headings, body copy, labels
- CSS Variable: `--font-sans`

**Monospace (Code):** Fira Code
- Weights: 400 (Regular), 500 (Medium), 600 (SemiBold)
- Usage: Code blocks, IDs, JSON, API responses, technical data
- CSS Variable: `--font-mono`
- Features: Programming ligatures for better code readability

### Type Scale (Modular Scale 1.250 - Major Third)

| Element | Class | Size | Variable | Weight |
|---------|-------|------|----------|--------|
| H1 / Page Title | `text-4xl font-semibold` | 2.25rem (36px) | `--font-size-4xl` | 600 |
| H2 / Section | `text-3xl font-semibold` | 1.875rem (30px) | `--font-size-3xl` | 600 |
| H3 / Subsection | `text-2xl font-semibold` | 1.5rem (24px) | `--font-size-2xl` | 600 |
| H4 / Card Title | `text-xl font-semibold` | 1.25rem (20px) | `--font-size-xl` | 600 |
| H5 / Small Header | `text-lg font-medium` | 1.125rem (18px) | `--font-size-lg` | 500 |
| Body Large | `text-lg` | 1.125rem (18px) | `--font-size-lg` | 400 |
| Body Base | `text-base` | 1rem (16px) | `--font-size-base` | 400 |
| Body Small | `text-sm` | 0.875rem (14px) | `--font-size-sm` | 400 |
| Caption / Meta | `text-xs` | 0.75rem (12px) | `--font-size-xs` | 400 |

### Utility Classes

```tsx
/* Semantic typography classes */
<h1 className="heading-1">Page Title</h1>
<h2 className="heading-2">Section Header</h2>
<h3 className="heading-3">Subsection</h3>
<p className="body-lg">Large body text for emphasis</p>
<p className="body-base">Regular body text</p>
<p className="body-sm">Small body text or captions</p>

/* Monospace for technical content */
<code className="text-mono text-sm">user_id: "abc-123"</code>
<pre className="text-mono text-xs">{JSON.stringify(data, null, 2)}</pre>
```

### Line Height

- **Tight (Headings):** 1.25 (`leading-tight` or `--leading-tight`)
- **Normal (Body):** 1.5 (`leading-normal` or `--leading-normal`)
- **Relaxed (Long-form):** 1.75 (`leading-relaxed` or `--leading-relaxed`)

### Font Weights

| Name | Value | Variable | Usage |
|------|-------|----------|-------|
| Light | 300 | `--font-light` | De-emphasized text |
| Regular | 400 | `--font-normal` | Body text |
| Medium | 500 | `--font-medium` | Labels, emphasis |
| SemiBold | 600 | `--font-semibold` | Headings, buttons |
| Bold | 700 | `--font-bold` | Strong emphasis |

### Best Practices

1. **Use semantic HTML**: `<h1>`, `<h2>`, `<p>`, etc. for proper accessibility
2. **Limit line length**: Max 65-75 characters for readability (use `max-w-prose`)
3. **Consistent hierarchy**: Don't skip heading levels (h1 → h2 → h3)
4. **Monospace for data**: Use `text-mono` for IDs, codes, JSON, technical values
5. **Weight variation**: Use Medium (500) for labels, SemiBold (600) for headings

---

## Spacing Scale

Follow Tailwind's spacing scale (based on 0.25rem = 4px):

| Name | Class | Value |
|------|-------|-------|
| XS | `2` | 0.5rem (8px) |
| SM | `4` | 1rem (16px) |
| MD | `6` | 1.5rem (24px) |
| LG | `8` | 2rem (32px) |
| XL | `12` | 3rem (48px) |

### Common Patterns

```tsx
// Card padding
<Card className="p-6">

// Section spacing
<div className="space-y-4">

// Header padding
<header className="px-4 py-4 sm:px-6 lg:px-8">

// Responsive padding
<main className="px-4 py-8 sm:px-6 lg:px-8">
```

---

## Z-Index Scale

Defined in [globals.css](src/app/globals.css):

```css
--z-base: 10
--z-dropdown: 20
--z-modal: 30
--z-toast: 50
```

**Usage:**
```tsx
<div className="z-[var(--z-modal)]">
```

---

## Components

### Button

**Location:** [src/components/ui/Button.tsx](src/components/ui/Button.tsx)

**Variants:**
- `primary` - Main actions (green)
- `secondary` - Secondary actions (gray)
- `destructive` - Dangerous actions (red)
- `outline` - Less prominent actions
- `ghost` - Minimal styling

**Sizes:**
- `sm` - 36px height
- `md` - 40px height (default)
- `lg` - 44px height

**States:**
- `loading` - Shows spinner, disables interaction
- `disabled` - Reduces opacity, prevents clicks

**Example:**
```tsx
import { Button } from '@/components/ui'

<Button variant="primary" size="md">
    Salvar
</Button>

<Button variant="destructive" loading={isDeleting}>
    Deletar
</Button>
```

---

### Card

**Location:** [src/components/ui/Card.tsx](src/components/ui/Card.tsx)

**Subcomponents:**
- `Card` - Container
- `CardHeader` - Header section
- `CardTitle` - Title
- `CardDescription` - Subtitle
- `CardContent` - Main content
- `CardFooter` - Footer section

**Variants:**
- `default` - Static card
- `interactive` - Hover effects (uses `.interactive-card` from globals.css)

**Example:**
```tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui'

<Card>
    <CardHeader>
        <CardTitle>Estatísticas</CardTitle>
    </CardHeader>
    <CardContent>
        <p>Conteúdo aqui</p>
    </CardContent>
</Card>
```

---

### Badge

**Location:** [src/components/ui/Badge.tsx](src/components/ui/Badge.tsx)

**Variants:**
- `default` - Primary color (green)
- `success` - Green
- `warning` - Orange
- `error` - Red
- `info` - Blue
- `secondary` - Gray

**Example:**
```tsx
import { Badge } from '@/components/ui'

<Badge variant="success">DONE</Badge>
<Badge variant="error">FAILED</Badge>
<Badge variant="warning">PENDING</Badge>
```

---

### LoadingSpinner

**Location:** [src/components/ui/LoadingSpinner.tsx](src/components/ui/LoadingSpinner.tsx)

**Sizes:**
- `sm` - 16px
- `md` - 32px (default)
- `lg` - 48px

**Example:**
```tsx
import { LoadingSpinner } from '@/components/ui'

<LoadingSpinner size="md" label="Carregando dados..." />

{loading && <LoadingSpinner />}
```

---

### Skeleton

**Location:** [src/components/ui/Skeleton.tsx](src/components/ui/Skeleton.tsx)

**Variants:**
- `default` - Rounded rectangle
- `text` - Text line (4px height)
- `circular` - Circle
- `rectangular` - Sharp corners

**Presets:**
- `SkeletonCard` - Skeleton for card layout
- `SkeletonTable` - Skeleton for table rows

**Example:**
```tsx
import { Skeleton, SkeletonCard, SkeletonTable } from '@/components/ui'

{loading ? (
    <SkeletonTable />
) : (
    <Table data={data} />
)}

<Skeleton className="h-10 w-full" />
<Skeleton variant="circular" className="h-12 w-12" />
```

---

### Input

**Location:** [src/components/ui/Input.tsx](src/components/ui/Input.tsx)

**Features:**
- Error states with visual feedback
- Helper text support
- Optional label
- Auto-generated IDs for accessibility
- ARIA attributes for screen readers

**Example:**
```tsx
import { Input } from '@/components/ui'

<Input
    label="Email"
    type="email"
    placeholder="seu@email.com"
    helperText="Digite seu email de cadastro"
/>

<Input
    label="Senha"
    type="password"
    error="Senha deve ter no mínimo 8 caracteres"
/>
```

---

### Select

**Location:** [src/components/ui/Select.tsx](src/components/ui/Select.tsx)

**Features:**
- Error states with visual feedback
- Helper text support
- Optional label
- Placeholder support
- Chevron icon indicator
- Disabled options support

**Example:**
```tsx
import { Select } from '@/components/ui'

<Select
    label="Status"
    placeholder="Selecione um status"
    options={[
        { value: 'active', label: 'Ativo' },
        { value: 'inactive', label: 'Inativo' },
        { value: 'pending', label: 'Pendente', disabled: true },
    ]}
    helperText="Escolha o status do item"
/>

<Select
    label="Prioridade"
    error="Campo obrigatório"
    options={[
        { value: 'high', label: 'Alta' },
        { value: 'medium', label: 'Média' },
        { value: 'low', label: 'Baixa' },
    ]}
/>
```

---

### FormField

**Location:** [src/components/ui/FormField.tsx](src/components/ui/FormField.tsx)

**Features:**
- Wrapper component for consistent form layouts
- Label with optional required indicator (*)
- Error display
- Helper text
- Works with any input component

**Example:**
```tsx
import { FormField, Input, Select } from '@/components/ui'

<FormField label="Nome" required error={errors.name}>
    <Input placeholder="Digite seu nome" {...register('name')} />
</FormField>

<FormField label="Categoria" helperText="Escolha a categoria principal">
    <Select options={categories} {...register('category')} />
</FormField>
```

---

### DataTable

**Location:** [src/components/ui/DataTable.tsx](src/components/ui/DataTable.tsx)

**Features:**
- Responsive (cards on mobile, table on desktop)
- Sortable columns (asc/desc/none cycle)
- Loading states with skeleton
- Empty state handling
- Custom mobile card renderer
- Row click handler
- TypeScript generics for type safety

**Example:**
```tsx
import { DataTable, Badge } from '@/components/ui'

const columns = [
    {
        key: 'name',
        header: 'Nome',
        sortable: true,
        mobileLabel: 'Nome',
    },
    {
        key: 'status',
        header: 'Status',
        accessor: (row) => <Badge variant={row.status === 'DONE' ? 'success' : 'warning'}>{row.status}</Badge>,
        sortable: true,
    },
    {
        key: 'created_at',
        header: 'Criado em',
        accessor: (row) => new Date(row.created_at).toLocaleDateString('pt-BR'),
        sortable: true,
    },
]

<DataTable
    data={jobs}
    columns={columns}
    rowKey={(row) => row.id}
    loading={loading}
    emptyMessage="Nenhum job encontrado"
    onRowClick={(row) => console.log('Clicked:', row)}
/>
```

---

### ErrorBoundary

**Location:** [src/components/ErrorBoundary.tsx](src/components/ErrorBoundary.tsx)

**Features:**
- Catches React errors in component tree
- Graceful fallback UI
- Retry functionality
- Shows stack trace in development
- Custom fallback renderer support

**Example:**
```tsx
import { ErrorBoundary } from '@/components/ErrorBoundary'

// Wrap entire page
<ErrorBoundary>
    <YourPage />
</ErrorBoundary>

// Wrap specific component with custom fallback
<ErrorBoundary
    fallback={(error, resetError) => (
        <div>
            <p>Erro ao carregar dados: {error.message}</p>
            <button onClick={resetError}>Tentar novamente</button>
        </div>
    )}
>
    <ComplexComponent />
</ErrorBoundary>

// In layout.tsx (recommended)
export default function RootLayout({ children }) {
    return (
        <html>
            <body>
                <ErrorBoundary>
                    {children}
                </ErrorBoundary>
            </body>
        </html>
    )
}
```

---

## Layout Patterns

### Container

```tsx
<div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    {/* Content */}
</div>
```

### Page Header

```tsx
<header className="border-b border-border bg-card shadow-sm">
    <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">Page Title</h1>
        <Button>Action</Button>
    </div>
</header>
```

### Grid Layout

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <Card>...</Card>
    <Card>...</Card>
    <Card>...</Card>
</div>
```

### Responsive Table → Cards

```tsx
{/* Mobile: Cards */}
<div className="block lg:hidden space-y-4">
    {items.map(item => (
        <Card key={item.id}>...</Card>
    ))}
</div>

{/* Desktop: Table */}
<div className="hidden lg:block">
    <table>...</table>
</div>
```

---

## Accessibility Guidelines

### Touch Targets

**Minimum 44x44px** for all interactive elements (WCAG AAA):

```css
button, a {
  min-height: 44px;
  min-width: 44px;
}
```

### Color Contrast

**Minimum 4.5:1** for normal text (WCAG AA):

```css
/* Light mode */
--foreground: 222.2 84% 4.9%       /* #0F172A on white = 13.5:1 ✅ */
--muted-foreground: 215.4 16.3% 46.9%  /* #64748B on white = 4.6:1 ✅ */

/* Dark mode */
--foreground: 210 40% 98%          /* #F8FAFC on dark = 14.2:1 ✅ */
```

### Focus States

All interactive elements have visible focus rings:

```tsx
focus-visible:outline-none
focus-visible:ring-2
focus-visible:ring-ring
focus-visible:ring-offset-2
```

### ARIA Labels

```tsx
<button aria-label="Logout">
    <LogOut className="w-4 h-4" />
</button>

<div role="status" aria-label="Loading">
    <Loader2 className="animate-spin" />
</div>
```

### Reduced Motion

Respects `prefers-reduced-motion` globally:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Responsive Breakpoints

Following Tailwind defaults:

| Breakpoint | Min Width | Device |
|------------|-----------|--------|
| `sm` | 640px | Mobile landscape |
| `md` | 768px | Tablet portrait |
| `lg` | 1024px | Tablet landscape / Desktop |
| `xl` | 1280px | Desktop |
| `2xl` | 1536px | Large desktop |

### Mobile-First Approach

```tsx
{/* Default: Mobile */}
<div className="px-4 text-sm">

{/* Tablet: Medium */}
<div className="px-4 md:px-6 text-sm md:text-base">

{/* Desktop: Large */}
<div className="px-4 md:px-6 lg:px-8 text-sm md:text-base lg:text-lg">
```

---

## Anti-Patterns

### ❌ DON'T

```tsx
// Hardcoded colors
<div className="bg-white text-gray-800 border-gray-200">

// Inconsistent spacing
<div className="p-5 mb-7">

// Emojis as icons
<button>🔍 Buscar</button>

// Missing cursor pointer
<div onClick={handleClick}>Clickable</div>

// Scale transforms on hover (causes layout shift)
<button className="hover:scale-105">

// Missing dark mode support
<div className="bg-white dark:bg-white">
```

### ✅ DO

```tsx
// Design tokens
<div className="bg-background text-foreground border-border">

// Consistent spacing scale
<div className="p-6 space-y-4">

// SVG icons
<button><Search className="w-4 h-4" /> Buscar</button>

// Cursor pointer
<div onClick={handleClick} className="cursor-pointer">Clickable</div>

// Color/opacity transitions
<button className="hover:bg-primary/90">

// Proper dark mode
<div className="bg-background">
```

---

## Pre-Delivery Checklist

Before merging any UI changes, verify:

### Visual Quality
- [ ] No emojis as icons (use Lucide icons)
- [ ] All icons from consistent set
- [ ] Hover states don't cause layout shift
- [ ] Use design tokens (no hardcoded colors)

### Interaction
- [ ] All clickable elements have `cursor-pointer`
- [ ] Hover states provide visual feedback
- [ ] Transitions are smooth (150-300ms)
- [ ] Focus states visible for keyboard nav

### Light/Dark Mode
- [ ] Text has sufficient contrast (4.5:1 minimum)
- [ ] Borders visible in both modes
- [ ] Test both modes before delivery

### Layout
- [ ] Responsive at 375px, 768px, 1024px, 1440px
- [ ] No horizontal scroll on mobile
- [ ] Proper spacing from edges

### Accessibility
- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Color is not the only indicator
- [ ] `prefers-reduced-motion` respected

---

## Contributing

### Adding a New Component

1. **Create component file** in `src/components/ui/ComponentName.tsx`
2. **Export from index** in `src/components/ui/index.ts`
3. **Document usage** in this file (DESIGN_SYSTEM.md)
4. **Test in both themes** (light and dark mode)
5. **Verify accessibility** (WCAG AAA compliance)

### Updating Design Tokens

1. **Edit globals.css** only (never hardcode)
2. **Update both light and dark** mode values
3. **Test across all pages** to ensure no regressions
4. **Document changes** in this file

---

## Resources

### Internal
- Design Tokens: [src/app/globals.css](src/app/globals.css)
- Components: [src/components/ui/](src/components/ui/)
- Tailwind Config: [tailwind.config.js](tailwind.config.js)

### External
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Lucide Icons](https://lucide.dev/)

---

## Changelog

### 2026-02-05 - Phase 3 Refinement (v1.3)
- **Typography Upgrade**: Replaced Inter with Fira Sans (UI) and Fira Code (monospace)
  - Fira Sans: Professional, highly legible font optimized for UI
  - Fira Code: Monospace font with programming ligatures for better code display
  - Added font weights: 300, 400, 500, 600, 700 (Sans) and 400, 500, 600 (Code)
  - Configured as CSS variables (--font-sans, --font-mono)
- **Typography System**: Implemented modular scale (1.250 - Major Third)
  - Added 9 font size variables (--font-size-xs through --font-size-4xl)
  - Added 3 line height variables (--leading-tight, --leading-normal, --leading-relaxed)
  - Added 5 font weight variables (--font-light through --font-bold)
  - Semantic heading styles (h1-h6) with optimized line heights
- **Utility Classes**: Added typography utilities
  - `.heading-1`, `.heading-2`, `.heading-3` for semantic headings
  - `.body-lg`, `.body-base`, `.body-sm` for text sizes
  - `.text-mono` for monospace code/technical content
- **Color Documentation**: Enhanced color palette documentation
  - Added detailed comments with hex values for all colors
  - Documented WCAG AAA compliance (4.5:1 contrast minimum)
  - Added semantic descriptions for each color's purpose
  - Improved dark mode color comments
- **Impact**: More professional typography, better code readability, enhanced documentation

### 2026-02-05 - Phase 4 Application (v1.2)
- Refactored 4 admin pages to use design system components
- **jobs/page.tsx**: Replaced 142 lines of inline HTML with DataTable (291 lines total, -23% complexity)
- **tenants/page.tsx**: Replaced inline tables/cards with DataTable (134→103 lines, -23%)
- **audit/page.tsx**: Replaced filters and tables with Input, Select, Badge, DataTable (182→186 lines, +modularity)
- **missing-weeks/page.tsx**: Fixed hardcoded gray colors, added mobile responsive design (195→197 lines, +modularity)
- **dashboard/page.tsx**: Replaced inline cards with Card/CardHeader/CardContent components (161→169 lines, +modularity)
- Added ErrorBoundary to dashboard/layout.tsx for better error handling
- **Total refactored**: 5 pages, ~280 lines of inline HTML → 10 component imports
- **Impact**: Improved consistency, mobile UX, maintainability, and accessibility

### 2026-02-05 - Phase 2 Release (v1.1)
- Added 4 form components (Input, Select, FormField, ErrorBoundary)
- Added DataTable component (responsive, sortable, 500+ rows support)
- Updated component exports in ui/index.ts
- Documented all new components with examples
- Total components: 10 (up from 5)

### 2026-02-04 - Initial Release (v1.0)
- Created design system documentation
- Added 5 core components (Button, Card, Badge, LoadingSpinner, Skeleton)
- Fixed AdminSidebar dark mode issues
- Documented all design tokens and patterns
- Established accessibility standards (WCAG AAA)

---

**Last Updated:** 2026-02-05 (Phase 3)
**Maintained By:** VivaCampo Engineering Team
**Current Version:** 1.3
