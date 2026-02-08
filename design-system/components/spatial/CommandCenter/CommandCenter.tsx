import * as React from 'react'
import { cn } from '../../utils/cn'
import { isArrowDown, isArrowUp, isCommandShortcut, isEscapeKey } from '../../utils/a11y'
import { trackSpatialEvent } from '../../utils/analytics'

export type CommandCenterItem = {
  id: string
  label: string
  description?: string
  shortcut?: string
}

export type CommandCenterProps = {
  items: CommandCenterItem[]
  isOpen?: boolean
  placeholder?: string
  emptyLabel?: string
  onOpenChange?: (open: boolean) => void
  onQueryChange?: (value: string) => void
  onSelect?: (item: CommandCenterItem) => void
  className?: string
}

const CommandCenter = React.forwardRef<HTMLDivElement, CommandCenterProps>(
  (
    {
      items,
      isOpen,
      placeholder = 'Pesquisar comandos, lugares ou camadas…',
      emptyLabel = 'Sem resultados',
      onOpenChange,
      onQueryChange,
      onSelect,
      className,
    },
    ref
  ) => {
    const [open, setOpen] = React.useState(isOpen ?? false)
    const [query, setQuery] = React.useState('')
    const [activeIndex, setActiveIndex] = React.useState(0)
    const inputRef = React.useRef<HTMLInputElement>(null)
    const openStartedAtRef = React.useRef<number | null>(null)
    const openMethodRef = React.useRef<'keyboard_shortcut' | 'button_click'>('button_click')

    const isControlled = typeof isOpen === 'boolean'
    const resolvedOpen = isControlled ? isOpen : open

    const filteredItems = React.useMemo(() => {
      if (!query.trim()) return items
      const normalized = query.toLowerCase()
      return items.filter((item) => item.label.toLowerCase().includes(normalized))
    }, [items, query])

    React.useEffect(() => {
      if (!resolvedOpen) return
      setActiveIndex(0)
      requestAnimationFrame(() => inputRef.current?.focus())
    }, [resolvedOpen])

    React.useEffect(() => {
      const handler = (event: KeyboardEvent) => {
        if (!isCommandShortcut(event)) return
        event.preventDefault()
        openMethodRef.current = 'keyboard_shortcut'
        const nextOpen = !resolvedOpen
        if (isControlled) {
          onOpenChange?.(nextOpen)
        } else {
          setOpen(nextOpen)
          onOpenChange?.(nextOpen)
        }
      }
      window.addEventListener('keydown', handler)
      return () => window.removeEventListener('keydown', handler)
    }, [resolvedOpen, isControlled, onOpenChange])

    const handleOpenChange = (value: boolean) => {
      if (value) {
        openStartedAtRef.current = performance.now()
      }
      if (isControlled) {
        onOpenChange?.(value)
      } else {
        setOpen(value)
        onOpenChange?.(value)
      }
    }

    const handleQueryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      const value = event.target.value
      setQuery(value)
      onQueryChange?.(value)
      setActiveIndex(0)
    }

    const activeItemId =
      filteredItems.length > 0 ? `command-center-option-${filteredItems[activeIndex].id}` : undefined

    const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (isArrowDown(event)) {
        event.preventDefault()
        if (filteredItems.length === 0) return
        setActiveIndex((prev) => Math.min(prev + 1, filteredItems.length - 1))
      }
      if (isArrowUp(event)) {
        event.preventDefault()
        if (filteredItems.length === 0) return
        setActiveIndex((prev) => Math.max(prev - 1, 0))
      }
      if (event.key === 'Enter') {
        event.preventDefault()
        const item = filteredItems[activeIndex]
        if (item) {
          onSelect?.(item)
          trackSpatialEvent('command_center_used', {
            query: query.trim() || 'empty',
            result_count: filteredItems.length,
            time_to_result: openStartedAtRef.current
              ? Number(((performance.now() - openStartedAtRef.current) / 1000).toFixed(2))
              : 0,
            method: openMethodRef.current,
          })
          handleOpenChange(false)
        }
      }
      if (isEscapeKey(event)) {
        event.preventDefault()
        handleOpenChange(false)
      }
    }

    return (
      <div ref={ref} className={cn('relative w-full max-w-[520px]', className)}>
        <div className="flex items-center gap-3 rounded-full border border-border/60 bg-background/80 px-4 py-2 shadow-md backdrop-blur">
          <span className="text-xs font-medium text-muted-foreground">⌘K</span>
          <button
            type="button"
            className="text-left text-sm text-muted-foreground transition-colors hover:text-foreground"
            onClick={() => handleOpenChange(true)}
            onMouseDown={() => {
              openMethodRef.current = 'button_click'
            }}
            aria-label="Abrir Command Center"
            aria-controls="command-center-listbox"
          >
            {placeholder}
          </button>
        </div>

        {resolvedOpen ? (
          <div className="absolute left-0 right-0 top-14 z-[var(--z-modal)]">
            <div className="glass-morphism rounded-2xl border border-border/40 bg-background/80 p-4 shadow-floating">
              <div role="search" className="flex items-center gap-2 rounded-xl border border-border/60 bg-background/70 px-3 py-2">
                <span className="text-xs font-semibold text-muted-foreground">CMD</span>
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={handleQueryChange}
                  onKeyDown={handleKeyDown}
                  placeholder={placeholder}
                  className="w-full bg-transparent text-sm text-foreground outline-none"
                  aria-controls="command-center-listbox"
                  aria-expanded={resolvedOpen}
                  aria-autocomplete="list"
                  aria-activedescendant={activeItemId}
                />
              </div>

              <ul
                id="command-center-listbox"
                role="listbox"
                className="mt-3 max-h-64 space-y-1 overflow-y-auto pr-1 text-sm"
              >
                {filteredItems.length === 0 ? (
                  <li className="rounded-lg px-3 py-2 text-muted-foreground">{emptyLabel}</li>
                ) : (
                  filteredItems.map((item, index) => (
                    <li
                      key={item.id}
                      id={`command-center-option-${item.id}`}
                      role="option"
                      aria-selected={index === activeIndex}
                      className={cn(
                        'flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 transition-colors',
                        index === activeIndex
                          ? 'bg-primary/10 text-foreground'
                          : 'text-muted-foreground hover:text-foreground'
                      )}
                      onMouseEnter={() => setActiveIndex(index)}
                      onClick={() => {
                        onSelect?.(item)
                        handleOpenChange(false)
                      }}
                    >
                      <div className="space-y-0.5">
                        <div className="font-medium text-foreground/90">{item.label}</div>
                        {item.description ? (
                          <div className="text-xs text-muted-foreground">{item.description}</div>
                        ) : null}
                      </div>
                      {item.shortcut ? (
                        <span className="rounded-full border border-border/60 px-2 py-0.5 text-[10px] text-muted-foreground">
                          {item.shortcut}
                        </span>
                      ) : null}
                    </li>
                  ))
                )}
              </ul>
            </div>
          </div>
        ) : null}
      </div>
    )
  }
)

CommandCenter.displayName = 'CommandCenter'

export { CommandCenter }
