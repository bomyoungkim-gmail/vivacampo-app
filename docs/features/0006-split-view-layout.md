# FEAT-0006 — Split-View Layout for Data Visualization

Date: 2026-02-04
Owner: Frontend Team
Status: Done

## Goal
Provide a flexible, resizable panel layout optimized for agricultural data visualization, allowing users to focus on either map or data as needed.

**User value:** Users can view charts and data at comfortable sizes without sacrificing map context, improving analysis efficiency.

## Scope
**In scope:**
- Expandable/collapsible data panel (3 sizes: collapsed, normal, expanded)
- Focus modes: map-focused, data-focused, split view
- Responsive design (mobile: full-screen sheets, desktop: side panel)
- Keyboard shortcuts for quick mode switching
- Larger chart heights (288px vs previous 160px)
- shadcn/ui component integration

**Out of scope:**
- Drag-to-resize panel (future enhancement)
- Multiple panels side-by-side
- Custom user layout persistence

## User Stories
- **As a farmer**, I want larger charts so I can easily read NDVI trends.
- **As an agronomist**, I want to expand the data panel to see detailed analysis while keeping the map visible.
- **As a user on mobile**, I want full-screen data views that don't feel cramped.

## UX Notes
**Panel Sizes:**
- Collapsed: 0px (panel hidden, map full-screen)
- Normal: 560px (desktop), full width (mobile)
- Expanded: 640px or 50vw (whichever is larger)

**Focus Modes:**
- Map focus: Panel at 420px, map dominant
- Data focus: Panel at 70vw, charts dominant
- Split: Balanced 50/50 view

**Controls:**
- Panel header with collapse/expand buttons
- Focus mode toggle (map/data/split icons)
- Mobile: Bottom sheet with swipe gestures

**Design System:**
- shadcn/ui components (Button, Tabs, Card, Badge, etc.)
- Tailwind CSS with CSS variables for theming
- Dark mode support via semantic color classes

## Contract Changes
**API:** None - frontend-only feature

**Domain:** None

**Data:** None

## Acceptance Criteria
- [x] User can collapse/expand data panel
- [x] User can switch between focus modes (map/data/split)
- [x] Charts display at 288px height (h-72)
- [x] Panel respects responsive breakpoints
- [x] Dark mode works correctly with CSS variables
- [x] Mobile uses full-screen sheets for data views
- [x] All existing functionality preserved

## Components Created/Modified
**New shadcn/ui components installed:**
- button, card, dialog, sheet, skeleton, badge, separator
- dropdown-menu, tabs, tooltip, select, input, label
- sidebar, chart, popover, scroll-area, sonner, table, alert-dialog

**Modified files:**
- `services/app-ui/src/app/farms/[id]/page.tsx` - Split-view layout
- `services/app-ui/src/components/AOIDetailsPanel.tsx` - Tabs, larger charts
- `services/app-ui/src/app/globals.css` - CSS variables for theming

## Observability
**Logs:** N/A (frontend-only)

**Analytics (future):**
- Panel size changes
- Focus mode usage
- Time spent in each mode

## Testing
**Manual tests:**
- Resize panel in all sizes
- Switch focus modes
- Verify charts are readable at new sizes
- Test on mobile devices (iOS Safari, Android Chrome)
- Test dark mode toggle
- Verify no regression in existing features

## Status
Done - Deployed 2026-02-04
