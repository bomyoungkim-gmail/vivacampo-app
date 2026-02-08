# Mobile-First Guidelines

Status: Draft
Last Updated: 2026-02-07

## Purpose
Provide a consistent, mobile-first checklist for UI/UX, performance, and accessibility across VivaCampo.

## Quick Checklist (10)
1. Viewport meta set to `width=device-width, initial-scale=1, maximum-scale=5`.
2. No horizontal scroll at 320, 375, 414, 768, 1024, 1440 widths.
3. Touch targets >= 44x44px for all interactive elements.
4. Base font size >= 16px on mobile.
5. Correct `inputMode` + `autoComplete` for all inputs.
6. Links in text blocks are distinguishable (underline or non-color cue).
7. Focus visible for keyboard navigation.
8. Images use responsive `sizes`/`srcset` and `loading=lazy` below the fold.
9. Reduced motion respected (no critical motion for essential content).
10. Mobile Lighthouse targets: Perf > 90, A11y > 95, LCP < 2.5s, CLS < 0.1.

## Touch Targets (44x44px)
- Buttons: `min-h-[44px] min-w-[44px]`.
- Icon buttons: wrap icon in a 44x44 container.
- Links in lists: vertical padding to reach 44px.
- Inputs, checkboxes, radios: min 44px.

## Breakpoint Testing Guide
- Test widths: 320, 375, 414, 768, 1024, 1440.
- Validate:
  - No horizontal scroll.
  - Text readable (>= 16px).
  - Touch targets >= 44px.

## InputMode Reference
| Field type | inputMode | autoComplete |
| --- | --- | --- |
| Email | `email` | `email` |
| Phone | `tel` | `tel` |
| Numeric (hectares/qty) | `numeric` + `pattern="[0-9]*"` | `off` or domain-specific |
| Name | `text` | `name` |
| Company | `text` | `organization` |
| Password (signup) | `text` | `new-password` |
| Password (login) | `text` | `current-password` |

## Anti-patterns
- Text links with color-only distinction.
- 12–14px body text on mobile.
- Tap targets smaller than 44px.
- Fixed elements causing horizontal scroll.
- Heavy hero animations blocking initial render.

## Performance Targets (Mobile)
- Lighthouse Performance > 90
- Lighthouse Accessibility > 95
- LCP < 2.5s
- TBT < 200ms
- CLS < 0.1

## How To Validate
- Playwright: `tests/e2e/mobile-responsiveness.spec.ts`
- Lighthouse: `npx lighthouse http://localhost:3002 --form-factor=mobile`
- aXe DevTools: 0 critical violations
- WAVE extension: 0 errors
- Screen reader: VoiceOver (iOS) or TalkBack (Android)
