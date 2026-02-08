export type Shortcut = {
  combo: string
  description: string
}

export const A11Y_SHORTCUTS: Shortcut[] = [
  { combo: 'Ctrl+K / ⌘K', description: 'Abrir Command Center' },
  { combo: '1', description: 'Macro view (zoom semantico)' },
  { combo: '2', description: 'Meso view (zoom semantico)' },
  { combo: '3', description: 'Micro view (zoom semantico)' },
  { combo: 'Esc', description: 'Fechar overlays e menus' },
]

export const isCommandShortcut = (event: KeyboardEvent) =>
  (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k'

export const isEscapeKey = (event: KeyboardEvent | React.KeyboardEvent) =>
  event.key === 'Escape'

export const isActivationKey = (event: KeyboardEvent | React.KeyboardEvent) =>
  event.key === 'Enter' || event.key === ' '

export const isArrowDown = (event: KeyboardEvent | React.KeyboardEvent) =>
  event.key === 'ArrowDown'

export const isArrowUp = (event: KeyboardEvent | React.KeyboardEvent) =>
  event.key === 'ArrowUp'
