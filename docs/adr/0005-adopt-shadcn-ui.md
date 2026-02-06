# ADR-0005 — Adopt shadcn/ui Design System

Date: 2026-02-04
Status: Accepted
Owners: Frontend Team

## Context
The VivaCampo frontend (Next.js + React) had grown organically without a consistent component library. Issues identified:
- Inconsistent styling across components
- Difficult to maintain dark mode (hardcoded classes)
- No standardized component patterns (buttons, cards, dialogs)
- Charts and data panels were too small for agricultural data visualization
- Custom implementations for common UI patterns (modals, dropdowns, tabs)

**Requirements:**
- Must work with Next.js 14 (App Router, RSC)
- Must support dark mode via Tailwind CSS
- Must be customizable (agricultural-specific color palette)
- Must not add heavy runtime dependencies
- Should improve developer productivity

## Decision
**Adopt shadcn/ui as the design system** for all frontend components.

## Options considered

### 1) Material UI (MUI)
**Pros:**
- Mature, comprehensive component library
- Large community and ecosystem
- Well-documented

**Cons:**
- Heavy runtime bundle (~100kb+ gzipped)
- Opinionated styling (Material Design)
- Complex theming system (Emotion/styled-components)
- Not ideal for Tailwind CSS projects

### 2) Chakra UI
**Pros:**
- Good accessibility defaults
- Reasonable bundle size
- Nice API

**Cons:**
- Still adds runtime overhead
- Styling system conflicts with Tailwind
- Theme customization less flexible than Tailwind

### 3) shadcn/ui ✅
**Pros:**
- Zero runtime - components are copied into your codebase
- Built on Radix UI (excellent accessibility)
- Native Tailwind CSS integration
- CSS variables for theming (perfect for dark mode)
- Copy/paste ownership - full control over components
- Excellent Next.js 14 support (RSC-compatible)

**Cons:**
- Must maintain components yourself (no package updates)
- Fewer pre-built complex components
- Requires Tailwind CSS (already using)

### 4) Build from scratch
**Pros:**
- Full control
- No dependencies

**Cons:**
- Massive development effort
- Accessibility is hard to get right
- Reinventing solved problems

## Consequences
**What changes:**
- New directory: `src/components/ui/` for shadcn components
- New utility: `src/lib/utils.ts` with `cn()` helper
- Updated `globals.css` with CSS variables for theming
- Components refactored to use shadcn patterns

**Components installed:**
- Layout: button, card, dialog, sheet, sidebar, separator
- Forms: input, label, select, checkbox
- Data display: badge, table, skeleton
- Feedback: tooltip, popover, sonner (toast)
- Navigation: tabs, dropdown-menu
- Charts: chart (Recharts wrapper)

**Theming:**
```css
:root {
  --primary: 142.1 76.2% 36.3%;  /* Green - agricultural theme */
  --chart-1: 142 76% 36%;         /* Vegetation green */
  --chart-2: 221 83% 53%;         /* Water blue */
  --chart-3: 38 92% 50%;          /* Warning orange */
}
```

**Migration strategy:**
- Gradual adoption (new features use shadcn)
- Existing components migrated incrementally
- No big-bang rewrite

**Trade-offs accepted:**
- Must maintain components ourselves - **mitigated by:**
  - Components rarely change after initial setup
  - Can cherry-pick updates from shadcn repo
  - Full control is actually an advantage for customization
- Fewer pre-built components - **mitigated by:**
  - Core components cover 90% of needs
  - Complex components (charts) use dedicated libraries (Recharts)

## Follow-ups
- [x] Install shadcn/ui CLI and core components
- [x] Configure CSS variables for agricultural color palette
- [x] Refactor AOIDetailsPanel to use Tabs, Card, Badge
- [x] Implement split-view layout with new components
- [ ] Migrate remaining pages to shadcn components (TASK-0300)
- [ ] Document component usage patterns in Storybook (TASK-0301)
