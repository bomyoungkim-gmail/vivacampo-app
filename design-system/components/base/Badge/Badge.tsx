import * as React from 'react'
import { cn } from '../../utils/cn'

export type BadgeVariant = 'neutral' | 'success' | 'warning' | 'critical' | 'info'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
}

const variantStyles: Record<BadgeVariant, string> = {
  neutral: 'bg-muted text-muted-foreground',
  success: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
  warning: 'bg-amber-500/15 text-amber-700 dark:text-amber-300',
  critical: 'bg-red-500/15 text-red-700 dark:text-red-300',
  info: 'bg-blue-500/15 text-blue-700 dark:text-blue-300',
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'neutral', ...props }, ref) => (
    <span
      ref={ref}
      className={cn(
        'inline-flex items-center rounded-full border border-border/40 px-2.5 py-0.5 text-xs font-medium',
        variantStyles[variant],
        className
      )}
      {...props}
    />
  )
)

Badge.displayName = 'Badge'

export { Badge }
