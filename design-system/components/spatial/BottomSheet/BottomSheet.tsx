import * as React from 'react'
import { createPortal } from 'react-dom'
import { cn } from '../../utils/cn'

export type BottomSheetLevel = 'peek' | 'half' | 'full'

export type BottomSheetProps = {
  isOpen: boolean
  onClose: () => void
  initialLevel?: BottomSheetLevel
  title: string
  children: React.ReactNode
  className?: string
}

const levelRatios: Record<BottomSheetLevel, number> = {
  peek: 0.5,
  half: 0.75,
  full: 1,
}

const getTranslateForLevel = (height: number, level: BottomSheetLevel) => {
  const ratio = levelRatios[level]
  return Math.max(0, height * (1 - ratio))
}

const getNearestLevel = (height: number, translate: number): BottomSheetLevel => {
  const candidates = Object.keys(levelRatios) as BottomSheetLevel[]
  return candidates.reduce((closest, level) => {
    const currentDistance = Math.abs(translate - getTranslateForLevel(height, level))
    const closestDistance = Math.abs(translate - getTranslateForLevel(height, closest))
    return currentDistance < closestDistance ? level : closest
  }, 'half')
}

export const BottomSheet = React.forwardRef<HTMLDivElement, BottomSheetProps>(
  ({ isOpen, onClose, initialLevel = 'peek', title, children, className }, ref) => {
    const [level, setLevel] = React.useState<BottomSheetLevel>(initialLevel)
    const [viewportHeight, setViewportHeight] = React.useState(0)
    const [translateY, setTranslateY] = React.useState(0)
    const [isDragging, setIsDragging] = React.useState(false)
    const titleId = React.useId()
    const contentRef = React.useRef<HTMLDivElement | null>(null)
    const dragState = React.useRef({ startY: 0, startTranslate: 0 })

    React.useEffect(() => {
      if (typeof window === 'undefined') return
      const updateHeight = () => setViewportHeight(window.innerHeight)
      updateHeight()
      window.addEventListener('resize', updateHeight)
      return () => window.removeEventListener('resize', updateHeight)
    }, [])

    React.useEffect(() => {
      if (!isOpen || viewportHeight === 0) return
      setLevel(initialLevel)
      setTranslateY(getTranslateForLevel(viewportHeight, initialLevel))
    }, [initialLevel, isOpen, viewportHeight])

    React.useEffect(() => {
      if (!isOpen || viewportHeight === 0) return
      if (isDragging) return
      setTranslateY(getTranslateForLevel(viewportHeight, level))
    }, [isOpen, isDragging, level, viewportHeight])

    const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
      if (!isOpen) return
      if (typeof event.currentTarget.setPointerCapture === 'function') {
        event.currentTarget.setPointerCapture(event.pointerId)
      }
      dragState.current = { startY: event.clientY, startTranslate: translateY }
      setIsDragging(true)
    }

    const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
      if (!isDragging) return
      const delta = event.clientY - dragState.current.startY
      const nextTranslate = Math.min(
        Math.max(dragState.current.startTranslate + delta, 0),
        viewportHeight
      )
      setTranslateY(nextTranslate)
    }

    const handlePointerEnd = () => {
      if (!isDragging) return
      setIsDragging(false)
      if (viewportHeight === 0) return

      if (translateY > viewportHeight * 0.88) {
        onClose()
        return
      }

      const nearest = getNearestLevel(viewportHeight, translateY)
      setLevel(nearest)
      setTranslateY(getTranslateForLevel(viewportHeight, nearest))
    }

    React.useEffect(() => {
      if (!isOpen) return
      const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === 'Escape') {
          event.stopPropagation()
          onClose()
          return
        }

        if (event.key !== 'Tab') return

        const root = contentRef.current
        if (!root) return
        const focusable = Array.from(
          root.querySelectorAll<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex=\"-1\"])'
          )
        ).filter((el) => !el.hasAttribute('disabled'))

        if (focusable.length === 0) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault()
          last.focus()
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault()
          first.focus()
        }
      }

      document.addEventListener('keydown', handleKeyDown)
      return () => document.removeEventListener('keydown', handleKeyDown)
    }, [isOpen, onClose])

    React.useEffect(() => {
      if (!isOpen) return
      const root = contentRef.current
      if (!root) return
      const focusable = root.querySelector<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex=\"-1\"])'
      )
      focusable?.focus()
    }, [isOpen])

    if (!isOpen) return null

    const content = (
      <>
        <div
          className={cn(
            'bottom-sheet-overlay fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity',
            isOpen ? 'opacity-100' : 'opacity-0'
          )}
          onClick={onClose}
        />
        <div
          ref={(node) => {
            contentRef.current = node
            if (typeof ref === 'function') {
              ref(node)
            } else if (ref) {
              ref.current = node
            }
          }}
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          className={cn(
            'bottom-sheet glass-morphism fixed inset-x-0 bottom-0 z-[var(--z-overlay)] w-full rounded-t-3xl border border-border/40 bg-background/90 shadow-floating outline-none',
            isDragging ? 'transition-none' : 'transition-transform duration-200 ease-out',
            className
          )}
          style={{
            height: viewportHeight ? `${viewportHeight}px` : '100vh',
            transform: `translateY(${translateY}px)`,
            paddingBottom: 'calc(16px + env(safe-area-inset-bottom))',
            contain: 'layout',
            willChange: isDragging ? 'transform' : 'auto',
          }}
        >
          <div
            className="px-4 pb-4 pt-3"
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerEnd}
            onPointerCancel={handlePointerEnd}
          >
            <div className="bottom-sheet-drag-indicator mx-auto mb-3 h-1.5 w-12 rounded-full bg-border" />
            <div className="flex items-center justify-between">
              <h2 id={titleId} className="text-sm font-semibold text-foreground">
                {title}
              </h2>
              <button
                type="button"
                className="min-h-[44px] min-w-[44px] rounded-full border border-border/40 px-3 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
                aria-label="Fechar"
                onClick={onClose}
              >
                Fechar
              </button>
            </div>
          </div>
          <div className="max-h-[calc(100%-96px)] overflow-y-auto px-4 pb-6">
            {children}
          </div>
        </div>
      </>
    )

    return createPortal(content, document.body)
  }
)

BottomSheet.displayName = 'BottomSheet'
