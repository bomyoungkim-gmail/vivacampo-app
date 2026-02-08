import * as React from 'react'
import { cn } from '../../utils/cn'
import { TooltipContent, TooltipProvider, TooltipRoot, TooltipTrigger } from '../../base/Tooltip'

export type FieldDockContext = 'macro' | 'meso' | 'micro'

export type FieldDockAction = {
  id: string
  label: string
  icon?: React.ReactNode
  active?: boolean
  disabled?: boolean
  tooltip?: string
  onSelect?: () => void
}

export type FieldDockProps = {
  title?: string
  context?: FieldDockContext
  actions: FieldDockAction[]
  className?: string
}

const contextLabels: Record<FieldDockContext, string> = {
  macro: 'Macro',
  meso: 'Meso',
  micro: 'Micro',
}

const FieldDock = React.forwardRef<HTMLDivElement, FieldDockProps>(
  ({ title = 'Ferramentas de Campo', context = 'macro', actions, className }, ref) => {
    return (
      <div ref={ref} className={cn('w-full max-w-[420px] rounded-2xl p-4', className)}>
        <div className="glass-morphism flex flex-col gap-3 rounded-2xl border border-border/50 bg-background/80 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{title}</p>
              <p className="text-sm font-semibold text-foreground">Contexto {contextLabels[context]}</p>
            </div>
            <span className="rounded-full border border-border/50 px-2 py-1 text-[10px] text-muted-foreground">
              {contextLabels[context]}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {actions.map((action) => {
              const tooltip = action.tooltip ?? action.label
              const ariaLabel = action.label || action.tooltip || 'Acao do dock'

              return (
                <TooltipProvider key={action.id}>
                  <TooltipRoot>
                    <TooltipTrigger asChild>
                      <button
                        type="button"
                        onClick={action.onSelect}
                        disabled={action.disabled}
                        className={cn(
                          'flex min-h-[44px] items-center gap-2 rounded-xl border border-border/40 px-3 py-2 text-left text-sm font-medium transition-colors',
                          action.active ? 'bg-primary/15 text-foreground' : 'bg-background/70 text-muted-foreground',
                          action.disabled
                            ? 'cursor-not-allowed opacity-50'
                            : 'cursor-pointer hover:text-foreground hover:shadow-sm'
                        )}
                        aria-pressed={action.active}
                        aria-disabled={action.disabled}
                        aria-label={ariaLabel}
                      >
                        <span className="text-base">{action.icon}</span>
                        <span className="flex-1">{action.label}</span>
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="top">{tooltip}</TooltipContent>
                  </TooltipRoot>
                </TooltipProvider>
              )
            })}
          </div>
        </div>
      </div>
    )
  }
)

FieldDock.displayName = 'FieldDock'

export { FieldDock }
