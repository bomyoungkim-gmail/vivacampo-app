import * as React from 'react'
import { cn } from '../../utils/cn'

export type DynamicIslandVariant = 'neutral' | 'selection' | 'action'

export type DynamicIslandProps = {
  title: string
  description?: string
  status?: string
  variant?: DynamicIslandVariant
  actions?: React.ReactNode
  ariaLive?: 'polite' | 'assertive'
  className?: string
}

const variantStyles: Record<DynamicIslandVariant, string> = {
  neutral: 'bg-background/70 text-foreground',
  selection: 'bg-primary/15 text-foreground',
  action: 'bg-amber-500/20 text-foreground',
}

const DynamicIsland = React.forwardRef<HTMLDivElement, DynamicIslandProps>(
  ({ title, description, status, variant = 'neutral', actions, ariaLive = 'polite', className }, ref) => {
    return (
      <div
        ref={ref}
        role="status"
        aria-live={ariaLive}
        aria-atomic="true"
        className={cn(
          'glass-morphism inline-flex max-w-[420px] flex-col gap-2 rounded-full border border-border/50 px-5 py-3 shadow-floating',
          variantStyles[variant],
          className
        )}
      >
        <div className="flex items-center gap-3">
          <div className="flex flex-1 flex-col">
            <span className="text-sm font-semibold leading-none text-foreground/90">{title}</span>
            {description ? (
              <span className="text-xs text-muted-foreground">{description}</span>
            ) : null}
          </div>
          {status ? (
            <span className="rounded-full border border-border/50 px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
              {status}
            </span>
          ) : null}
        </div>
        {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
      </div>
    )
  }
)

DynamicIsland.displayName = 'DynamicIsland'

export { DynamicIsland }
